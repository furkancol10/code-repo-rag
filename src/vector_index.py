"""Vektör indeksi: NumpyIndex (kosinüs = matris çarpımı), CodeChunk için."""
import fcntl
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import config
from .chunk import CodeChunk


def repo_hash(repo) -> str:
    return hashlib.sha1(str(Path(repo).resolve()).encode("utf-8")).hexdigest()[:8]


def _git(repo, *args) -> str | None:
    try:
        r = subprocess.run(["git", "-c", "core.fsmonitor=", "-C", str(repo), *args],
                           capture_output=True, check=True, text=True)
        return r.stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def commit_short(repo) -> str:
    """Repo HEAD kısa hash'i; git yoksa 'nogit'."""
    out = _git(repo, "rev-parse", "--short=8", "HEAD")
    return (out or "").strip() or "nogit"


def content_hash(repo) -> str:
    """Taranan dosyaların (yol, boyut, mtime_ns) özetinden 8 haneli hash."""
    from .scanner import scan_repo
    root = Path(repo)
    h = hashlib.sha1()
    for rel in scan_repo(root):
        try:
            st = (root / rel).stat()
        except OSError:
            continue
        h.update(f"{rel}\0{st.st_size}\0{st.st_mtime_ns}\n".encode("utf-8", "replace"))
    return h.hexdigest()[:8]


def _dirty(repo) -> bool:
    """Git repoda commit'lenmemiş değişiklik var mı; git yoksa True (güvenilmez)."""
    out = _git(repo, "status", "--porcelain")
    return out is None or bool(out.strip())


def index_name(model: str, repo) -> str:
    """model + repo yolu hash'i + commit kısa hash'i (+ kirli/git dışıysa içerik hash'i)."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", model).strip("_")[:36]
    name = f"{slug}_{repo_hash(repo)}_{commit_short(repo)}"
    if commit_short(repo) == "nogit" or _dirty(repo):
        name += f"_{content_hash(repo)}"
    return name


def prune_indexes(repo, keep: int = 1) -> list[str]:
    """Aynı repo hash'ine ait indekslerden en yeni `keep` dışındakileri siler; silinen adlar."""
    rh = f"_{repo_hash(repo)}_"
    removed = []
    for kind in ("numpy", "bm25"):
        base = config.INDEX_DIR / kind
        if not base.is_dir():
            continue
        dirs = [d for d in base.iterdir() if d.is_dir() and rh in d.name
                and ".tmp." not in d.name and ".old." not in d.name]
        dirs.sort(key=lambda d: d.stat().st_mtime_ns, reverse=True)
        for d in dirs[max(keep, 0):]:
            shutil.rmtree(d, ignore_errors=True)
            removed.append(f"{kind}/{d.name}")
    return removed


def atomic_write_dir(final: Path, write) -> None:
    """Benzersiz tmp dizinine write(tmp) yap, flock altında final ile değiştir."""
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=final.parent, prefix=final.name + ".tmp."))
    old = final.with_name(f"{final.name}.old.{uuid.uuid4().hex[:8]}")
    try:
        write(tmp)
        with open(final.parent / f".{final.name}.lock", "w") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            moved = False
            try:
                if final.exists():
                    final.rename(old)
                    moved = True
                tmp.rename(final)
            except BaseException:
                if moved and not final.exists():
                    old.rename(final)
                raise
            finally:
                shutil.rmtree(old, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def read_retry(fn, tries: int = 20, delay: float = 0.01):
    """Swap penceresinde dizin yoksa kısa süre yeniden dener."""
    for i in range(tries):
        try:
            return fn()
        except FileNotFoundError:
            if i == tries - 1:
                raise
            time.sleep(delay)


class NumpyIndex:
    def __init__(self, name: str):
        self.dir = config.INDEX_DIR / "numpy" / name
        self._vecs: np.ndarray | None = None
        self._chunks: list[CodeChunk] | None = None
        self._stamp: tuple | None = None

    def _disk_stamp(self) -> tuple | None:
        try:
            return tuple((st.st_mtime_ns, st.st_ino, st.st_size) for st in
                         (( self.dir / f).stat() for f in ("vecs.npy", "chunks.json")))
        except OSError:
            return None

    def exists(self) -> bool:
        return (self.dir / "vecs.npy").exists() and (self.dir / "chunks.json").exists()

    def build(self, chunks: list[CodeChunk], vecs: np.ndarray) -> None:
        def write(tmp):
            np.save(tmp / "vecs.npy", vecs)
            (tmp / "chunks.json").write_text(
                json.dumps([asdict(c) for c in chunks], ensure_ascii=False), encoding="utf-8")
        atomic_write_dir(self.dir, write)
        self._vecs, self._chunks = vecs, list(chunks)  # önbelleği yenile
        self._stamp = self._disk_stamp()

    def _load(self) -> None:
        read_retry(self._load_once)

    def _load_once(self) -> None:
        stamp = self._disk_stamp()
        if self._vecs is None or self._chunks is None or stamp != self._stamp:
            vecs = np.load(self.dir / "vecs.npy")
            chunks = [CodeChunk(**c) for c in
                      json.loads((self.dir / "chunks.json").read_text("utf-8"))]
            self._vecs, self._chunks = vecs, chunks
            self._stamp = stamp

    def chunks(self) -> list[CodeChunk]:
        self._load()
        return self._chunks

    def search(self, qvec: np.ndarray, k: int) -> list[tuple[CodeChunk, float]]:
        self._load()
        scores = self._vecs @ qvec  # normalize vektörler: nokta çarpımı = kosinüs
        k = min(k, len(scores))
        if k <= 0:
            return []
        top = np.argpartition(-scores, k - 1)[:k] if k < len(scores) else np.arange(len(scores))
        top = top[np.argsort(-scores[top], kind="stable")]
        return [(self._chunks[i], float(scores[i])) for i in top]

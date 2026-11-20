"""Vektör indeksi: NumpyIndex (kosinüs = matris çarpımı), CodeChunk için."""
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import config
from .chunk import CodeChunk


def repo_hash(repo) -> str:
    return hashlib.sha1(str(Path(repo).resolve()).encode("utf-8")).hexdigest()[:8]


def commit_short(repo) -> str:
    """Repo HEAD kısa hash'i; git yoksa 'nogit'."""
    try:
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short=8", "HEAD"],
                           capture_output=True, check=True, text=True)
        return r.stdout.strip() or "nogit"
    except (OSError, subprocess.CalledProcessError):
        return "nogit"


def index_name(model: str, repo) -> str:
    """model + repo yolu hash'i + commit kısa hash'i."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", model).strip("_")[:36]
    return f"{slug}_{repo_hash(repo)}_{commit_short(repo)}"


class NumpyIndex:
    def __init__(self, name: str):
        self.dir = config.INDEX_DIR / "numpy" / name

    def exists(self) -> bool:
        return (self.dir / "vecs.npy").exists() and (self.dir / "chunks.json").exists()

    def build(self, chunks: list[CodeChunk], vecs: np.ndarray) -> None:
        # Geçici dizine yaz, başarılıysa değiştir: hata eski indeksi bozmaz
        tmp = self.dir.with_name(self.dir.name + ".tmp")
        old = self.dir.with_name(self.dir.name + ".old")
        for d in (tmp, old):
            shutil.rmtree(d, ignore_errors=True)
        tmp.mkdir(parents=True)
        try:
            np.save(tmp / "vecs.npy", vecs)
            (tmp / "chunks.json").write_text(
                json.dumps([asdict(c) for c in chunks], ensure_ascii=False), encoding="utf-8")
            if self.dir.exists():
                self.dir.rename(old)
            tmp.rename(self.dir)
        except BaseException:
            if old.exists() and not self.dir.exists():
                old.rename(self.dir)
            shutil.rmtree(tmp, ignore_errors=True)
            raise
        shutil.rmtree(old, ignore_errors=True)

    def chunks(self) -> list[CodeChunk]:
        return [CodeChunk(**c) for c in json.loads((self.dir / "chunks.json").read_text("utf-8"))]

    def search(self, qvec: np.ndarray, k: int) -> list[tuple[CodeChunk, float]]:
        vecs = np.load(self.dir / "vecs.npy")
        chunks = self.chunks()
        scores = vecs @ qvec  # normalize vektörler: nokta çarpımı = kosinüs
        top = np.argsort(-scores)[:k]
        return [(chunks[i], float(scores[i])) for i in top]

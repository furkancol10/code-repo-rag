"""İndeksleme hattı: tara -> parçala -> embed -> iki indeksi aynı isimle kur."""
import logging
from collections import Counter
from pathlib import Path

from . import config
from .bm25_index import BM25Index
from .chunk import chunk_file, make_embed_text
from .embedder import embed_passages, release_gpu
from .scanner import scan_repo
from .vector_index import NumpyIndex, index_name

log = logging.getLogger(__name__)


class RepoError(ValueError):
    """Repo yolu geçersiz ya da indeksleme sınırları aşıldı (kullanıcı hatası)."""


def validate_repo(repo) -> Path:
    """Var olan, dizin olan, aşırı geniş olmayan (/ , $HOME ve üstleri) repo yolunu döner."""
    p = Path(repo).expanduser()
    if not p.exists():
        raise RepoError(f"repo yolu yok: {p}")
    if not p.is_dir():
        raise RepoError(f"repo yolu bir dizin değil: {p}")
    p = p.resolve()
    home = Path.home().resolve()
    if p == home or p in home.parents:
        raise RepoError(f"repo yolu çok geniş (kök ya da ev dizini): {p}; bir proje dizini verin")
    return p


def known_error_message(exc: BaseException) -> str | None:
    """Bilinen hatalar için kullanıcıya dönük kısa mesaj; bilinmiyorsa None."""
    if isinstance(exc, RepoError):
        return str(exc)
    if isinstance(exc, FileNotFoundError):
        return f"{exc} (önce 'index' komutu / 'İndeksle' düğmesi ile indeksleyin)"
    import httpx
    import ollama
    if isinstance(exc, (ConnectionError, httpx.ConnectError, httpx.TimeoutException)):
        return (f"Ollama'ya bağlanılamadı ({config.LLM} için 'ollama serve' çalışıyor mu?): "
                f"{exc}")
    if isinstance(exc, ollama.ResponseError):
        return f"Ollama hatası (model '{config.LLM}' kurulu mu? 'ollama pull'): {exc}"
    return None


def _names(repo):
    repo = Path(repo).resolve()
    return repo, index_name(config.EMBED_MODEL, repo)


def indexes_exist(repo) -> bool:
    _, name = _names(repo)
    return NumpyIndex(name).exists() and BM25Index(name).exists()


def build_index(repo) -> dict:
    """Repoyu indeksler; {files, chunks, kinds, index_name} döner."""
    repo = validate_repo(repo)
    repo, name = _names(repo)
    files = scan_repo(repo)
    total = sum((repo / rel).stat().st_size for rel in files)
    if total > config.MAX_TOTAL_BYTES:
        raise RepoError(f"indekslenecek dosyalar toplam {total} bayt; sınır "
                        f"{config.MAX_TOTAL_BYTES} bayt (config.MAX_TOTAL_BYTES)")
    chunks = []
    unreadable = decode_errors = 0
    for rel in files:
        try:
            raw = (repo / rel).read_bytes()
        except OSError as e:
            unreadable += 1
            log.warning("okunamadı, atlandı: %s (%s)", rel, e)
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            decode_errors += 1
            log.warning("UTF-8 değil, bozuk karakterler değiştirilerek indeksleniyor: %s", rel)
            text = raw.decode("utf-8", errors="replace")
        chunks += chunk_file(repo / rel, rel, text)
    if not chunks:
        raise ValueError(f"indekslenecek parça yok: {repo}")
    try:
        vecs = embed_passages([make_embed_text(c) for c in chunks])
    finally:
        release_gpu()
    NumpyIndex(name).build(chunks, vecs)
    BM25Index(name).build(chunks)
    st = {"files": len(files) - unreadable, "chunks": len(chunks),
          "kinds": dict(Counter(c.kind for c in chunks)), "index_name": name,
          "unreadable": unreadable, "decode_errors": decode_errors}
    log.info("indekslendi: %d dosya, %d parça (okunamayan %d, bozuk kodlama %d)",
             st["files"], st["chunks"], unreadable, decode_errors)
    return st


def load_indexes(repo):
    """(NumpyIndex, BM25Index) döner; indeks yoksa FileNotFoundError."""
    repo, name = _names(repo)
    vec, bm = NumpyIndex(name), BM25Index(name)
    if not (vec.exists() and bm.exists()):
        raise FileNotFoundError(f"indeks yok, önce indeksleyin: {repo}")
    bm.load()
    return vec, bm

"""İndeksleme hattı: tara -> parçala -> embed -> iki indeksi aynı isimle kur."""
from collections import Counter
from pathlib import Path

from . import config
from .bm25_index import BM25Index
from .chunk import chunk_file, make_embed_text
from .embedder import embed_passages, release_gpu
from .scanner import scan_repo
from .vector_index import NumpyIndex, index_name


def _names(repo):
    repo = Path(repo).resolve()
    return repo, index_name(config.EMBED_MODEL, repo)


def indexes_exist(repo) -> bool:
    _, name = _names(repo)
    return NumpyIndex(name).exists() and BM25Index(name).exists()


def build_index(repo) -> dict:
    """Repoyu indeksler; {files, chunks, kinds, index_name} döner."""
    repo, name = _names(repo)
    files = scan_repo(repo)
    chunks = []
    for rel in files:
        text = (repo / rel).read_text(encoding="utf-8", errors="replace")
        chunks += chunk_file(repo / rel, rel, text)
    if not chunks:
        raise ValueError(f"indekslenecek parça yok: {repo}")
    try:
        vecs = embed_passages([make_embed_text(c) for c in chunks])
    finally:
        release_gpu()
    NumpyIndex(name).build(chunks, vecs)
    BM25Index(name).build(chunks)
    return {"files": len(files), "chunks": len(chunks),
            "kinds": dict(Counter(c.kind for c in chunks)), "index_name": name}


def load_indexes(repo):
    """(NumpyIndex, BM25Index) döner; indeks yoksa FileNotFoundError."""
    repo, name = _names(repo)
    vec, bm = NumpyIndex(name), BM25Index(name)
    if not (vec.exists() and bm.exists()):
        raise FileNotFoundError(f"indeks yok, önce indeksleyin: {repo}")
    bm.load()
    return vec, bm

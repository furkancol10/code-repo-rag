"""Hibrit arama: BM25 + vektör sonuçlarını Reciprocal Rank Fusion (RRF) ile birleştirir."""
from . import config
from .chunk import CodeChunk
from .embedder import embed_query

MODES = ("hybrid", "bm25", "vector")


def rrf(rankings: list[list[str]], k: int = config.RRF_K) -> list[tuple[str, float]]:
    """score(id) = Σ 1/(k + rank), rank 1-tabanlı. Bir listede tekrar eden id yalnız ilk
    sırasıyla sayılır. Eşit skorda ilk görülen önce gelir."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        seen = set()
        for rank, cid in enumerate(ranking, start=1):
            if cid in seen:
                continue
            seen.add(cid)
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    order = {cid: i for i, cid in enumerate(scores)}
    return sorted(scores.items(), key=lambda kv: (-kv[1], order[kv[0]]))


def hybrid_search(query: str, vec_index, bm25_index, mode: str = "hybrid",
                  top_k: int = config.TOP_K, candidates: int = config.CANDIDATES,
                  k: int = config.RRF_K) -> list[tuple[CodeChunk, float]]:
    """mode=bm25|vector: o yöntemin kendi skoru; hybrid: RRF skoru."""
    if mode not in MODES:
        raise ValueError(f"bilinmeyen mod: {mode!r} (seçenekler: {', '.join(MODES)})")
    if mode == "bm25":
        return bm25_index.search(query, top_k)
    if mode == "vector":
        return vec_index.search(embed_query(query), top_k)
    lex = bm25_index.search(query, candidates)
    sem = vec_index.search(embed_query(query), candidates)
    by_id = {c.id: c for c, _ in lex + sem}
    fused = rrf([[c.id for c, _ in sem], [c.id for c, _ in lex]], k=k)
    return [(by_id[cid], score) for cid, score in fused[:top_k]]

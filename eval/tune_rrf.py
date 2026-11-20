"""Ağırlıklı RRF parametre taraması — YALNIZ eval/tuning.json üzerinde.

Embedding ve aday listeleri (BM25 + vektör, en çok 50) soru başına bir kez hesaplanır;
her kombinasyon önbellekten, gerçek `hybrid_search` ile skorlanır.
Seçim: tuning setinde (name MRR + conceptual MRR) / 2. Eşitlikte varsayılana yakın olan.
En iyi ile varsayılan farkı <= 0.01 ise varsayılan korunur.

Kullanım: uv run python eval/tune_rrf.py
"""
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval"))

from run_eval import REPO_PATHS, metrics, rank_of  # noqa: E402

W_BM25 = (0.3, 0.5, 0.7, 1.0)  # w_vec = 1
KS = (10, 30, 60)
CANDS = (20, 30, 50)
MAX_CAND = max(CANDS)
MARGIN = 0.01


class _Cached:
    """Önceden hesaplanmış sıralı sonucu `search(q, k)` arayüzüyle verir (ön ek = ilk k)."""

    def __init__(self, hits):
        self.hits = hits

    def search(self, _q, k):
        return self.hits[:k]


def distance(p, default):
    """Varsayılana yakınlık (eşitlik bozucu): değişen parametre sayısı, sonra ağırlık farkı."""
    return (sum(a != b for a, b in zip(p, default)), abs(p[0] - default[0]))


def main():
    from src import config, hybrid
    from src.embedder import embed_query
    from src.pipeline import load_indexes

    default = (config.RRF_W_BM25, config.RRF_K, config.CANDIDATES)
    questions = json.loads((ROOT / "eval" / "tuning.json").read_text("utf-8"))
    idx = {r: load_indexes(REPO_PATHS[r]) for r in sorted({q["repo"] for q in questions})}

    cache = []  # (soru, vektör adayları, bm25 adayları)
    for q in questions:
        vec, bm = idx[q["repo"]]
        cache.append((q, vec.search(embed_query(q["question"]), MAX_CAND),
                      bm.search(q["question"], MAX_CAND)))

    def evaluate(mode, w=1.0, k=60, c=MAX_CAND):
        ranks = {"name": [], "conceptual": []}
        for q, sem, lex in cache:
            hybrid.embed_query = lambda _q: None
            hits = hybrid.hybrid_search(q["question"], _Cached(sem), _Cached(lex), mode=mode,
                                        top_k=30, candidates=c, k=k, w_bm25=w, w_vec=1.0)
            ranks[q["type"]].append(rank_of(hits, q["expected"]))
        m = {t: metrics(r) for t, r in ranks.items()}
        return m, (m["name"]["mrr"] + m["conceptual"]["mrr"]) / 2

    rows = {}
    for p in itertools.product(W_BM25, KS, CANDS):
        rows[p] = evaluate("hybrid", *p)
    if default not in rows:
        rows[default] = evaluate("hybrid", *default)
    vec_m, vec_s = evaluate("vector")

    best = max(rows, key=lambda p: (round(rows[p][1], 6), [-x for x in distance(p, default)]))
    gain = rows[best][1] - rows[default][1]
    chosen = best if gain > MARGIN else default

    lines = ["# Ağırlıklı RRF tuning (eval/tuning.json, %d soru)" % len(questions), "",
             "Skor = (name MRR@10 + conceptual MRR@10) / 2. w_vec = 1. "
             "Ana set (questions.json) bu taramada kullanılmadı.", "",
             "| w_bm25 | k | candidates | name hit@5 | name MRR | conc. hit@5 | conc. MRR | skor |",
             "|---|---|---|---|---|---|---|---|"]
    for p in sorted(rows, key=lambda p: -rows[p][1]):
        m, s = rows[p]
        tag = (" (varsayılan)" if p == default else "") + (" **seçilen**" if p == chosen else "")
        lines.append(f"| {p[0]} | {p[1]} | {p[2]} | {m['name']['hit5']:.2f} | "
                     f"{m['name']['mrr']:.3f} | {m['conceptual']['hit5']:.2f} | "
                     f"{m['conceptual']['mrr']:.3f} | {s:.4f}{tag} |")
    lines += ["", f"Referans, yalnız vektör: name MRR {vec_m['name']['mrr']:.3f}, conceptual MRR "
              f"{vec_m['conceptual']['mrr']:.3f}, skor {vec_s:.4f}.", "",
              f"En iyi: w_bm25={best[0]}, k={best[1]}, candidates={best[2]} "
              f"(skor {rows[best][1]:.4f}); varsayılan w_bm25={default[0]}, k={default[1]}, "
              f"candidates={default[2]} (skor {rows[default][1]:.4f}); fark {gain:+.4f}.",
              (f"Fark > {MARGIN}: en iyi kombinasyon seçildi." if chosen == best and best != default
               else f"Fark <= {MARGIN}: aşırı uydurmayı önlemek için varsayılan korundu.")]
    text = "\n".join(lines)
    print(text)
    (ROOT / "eval" / "tuning_results.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

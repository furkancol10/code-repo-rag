"""Retrieval değerlendirmesi (LLM yok): hit@1, hit@5, MRR@10; mod x repo x tür.

Kullanım: uv run python eval/run_eval.py [--set main|tuning]
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODES = ("bm25", "vector", "hybrid")
REPO_PATHS = {"kisiselnotarama": ROOT.parent / "KisiselNotArama",
              "httpx": ROOT / "data" / "repos" / "httpx"}
SUFFIX = re.compile(r"[#~]\d+$")


def base_symbol(symbol: str) -> str:
    """Bölünmüş parça (`#n`) / yinelenen (`~n`) ekini atar."""
    return SUFFIX.sub("", symbol)


def symbol_matches(chunk_symbol: str, expected: str) -> bool:
    """Eşleşme kuralları (hepsi base_symbol sonrası):
    1. chunk symbol'ü == expected
    2. markdown başlık yolu "A > B": son öğe == expected
    3. expected sınıf adı ("Sinif", noktasız): chunk "Sinif" ya da "Sinif.metot" olabilir
       (sınıf soruları, sınıfın metot parçasıyla da doğru sayılır)
    """
    sym = base_symbol(chunk_symbol)
    if sym == expected:
        return True
    if " > " in sym and sym.rsplit(" > ", 1)[-1].strip() == expected:
        return True
    if "." not in expected and " > " not in sym and sym.startswith(expected + "."):
        return True
    return False


def is_match(chunk, expected: list[dict]) -> bool:
    return any(chunk.path == e["path"] and symbol_matches(chunk.symbol, e["symbol"])
               for e in expected)


def dedupe(hits) -> list:
    """Aynı (path, base symbol) parçalarını tek hit say; ilk görülen sırayı korur."""
    seen, out = set(), []
    for chunk, score in hits:
        key = (chunk.path, base_symbol(chunk.symbol))
        if key not in seen:
            seen.add(key)
            out.append((chunk, score))
    return out


def rank_of(hits, expected, limit=10):
    """İlk doğru hit'in 1-tabanlı sırası (dedupe sonrası), yoksa None."""
    for i, (chunk, _) in enumerate(dedupe(hits)[:limit], 1):
        if is_match(chunk, expected):
            return i
    return None


def metrics(ranks: list) -> dict:
    n = len(ranks)
    if not n:
        return {"n": 0, "hit1": 0.0, "hit5": 0.0, "mrr": 0.0}
    return {"n": n,
            "hit1": sum(r == 1 for r in ranks) / n,
            "hit5": sum(r is not None and r <= 5 for r in ranks) / n,
            "mrr": sum(1 / r for r in ranks if r) / n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="main", choices=["main", "tuning"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from src import hybrid
    from src.embedder import embed_query
    from src.pipeline import build_index, indexes_exist, load_indexes

    hybrid.embed_query = lru_cache(maxsize=None)(embed_query)  # sorgu embedding'i tek sefer

    fname = "questions.json" if args.set == "main" else "tuning.json"
    questions = json.loads((ROOT / "eval" / fname).read_text("utf-8"))

    idx = {}
    for repo in sorted({q["repo"] for q in questions}):
        path = REPO_PATHS[repo]
        if not indexes_exist(path):
            print(f"[{repo}] indeksleniyor...", flush=True)
            print(build_index(path))
        idx[repo] = load_indexes(path)

    ranks = defaultdict(list)  # (mode, repo, type) -> [rank]
    misses = []
    for q in questions:
        vec, bm = idx[q["repo"]]
        for mode in MODES:
            hits = hybrid.hybrid_search(q["question"], vec, bm, mode=mode,
                                        top_k=30, candidates=50)
            r = rank_of(hits, q["expected"])
            for t in (q["type"], "all"):
                ranks[(mode, q["repo"], t)].append(r)
            ranks[(mode, "all", q["type"])].append(r)
            ranks[(mode, "all", "all")].append(r)
            if mode == "hybrid" and r is None:
                misses.append(q["id"])

    lines = [f"# Eval sonuçları ({args.set}, {len(questions)} soru)", "",
             "| mod | repo | tür | n | hit@1 | hit@5 | MRR@10 |", "|---|---|---|---|---|---|---|"]
    for mode in MODES:
        for repo in sorted({q["repo"] for q in questions}) + ["all"]:
            for t in ("name", "conceptual", "all"):
                m = metrics(ranks.get((mode, repo, t), []))
                if m["n"]:
                    lines.append(f"| {mode} | {repo} | {t} | {m['n']} | {m['hit1']:.2f} | "
                                 f"{m['hit5']:.2f} | {m['mrr']:.3f} |")
    lines += ["", f"Hybrid ilk 10'da bulamadığı sorular: {', '.join(misses) or '-'}"]
    text = "\n".join(lines)
    print(text)
    out = Path(args.out) if args.out else ROOT / "eval" / (
        "results.md" if args.set == "main" else "results_tuning.md")
    out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

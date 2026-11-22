"""Üretim kalitesi eval'i (Ollama gerekir): atıf geçerliliği, atıfsızlık, doğru dosyaya atıf, red.

Kullanım: uv run python eval/gen_eval.py [--n 12] [--seed 0]
Çıktı: eval/gen_results.md
"""
import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval"))

from run_eval import REPO_PATHS  # noqa: E402
from src.generator import CITATION  # noqa: E402

REFUSAL = "Bu bilgi repoda yok."


def pick_subset(questions: list[dict], n: int, seed: int = 0) -> list[dict]:
    """name/conceptual dengeli, sabit seed'li alt küme (n >= len ise hepsi)."""
    rng = random.Random(seed)
    groups = {t: [q for q in questions if q["type"] == t] for t in ("name", "conceptual")}
    for g in groups.values():
        rng.shuffle(g)
    out, i = [], 0
    while len(out) < n and any(groups.values()):
        t = ("name", "conceptual")[i % 2]
        if groups[t]:
            out.append(groups[t].pop())
        i += 1
    return out


def gen_metrics(rows: list[dict]) -> dict:
    """Saf metrik. rows: {answer, bad (geçersiz atıf listesi), expected_paths, trap}.
    Normal satırlar: atıfsız oranı, geçersiz atıf oranı (atıf bazında), beklenen dosyaya atıf oranı.
    Tuzak satırlar: tam red oranı."""
    normal = [r for r in rows if not r.get("trap")]
    traps = [r for r in rows if r.get("trap")]
    total = invalid = uncited = to_expected = 0
    for r in normal:
        cites = CITATION.findall(r["answer"])
        total += len(cites)
        invalid += len(r["bad"])
        if not cites:
            uncited += 1
        if any(p in set(r["expected_paths"]) for p, _, _ in cites):
            to_expected += 1
    n = len(normal)
    return {"n": n, "citations": total, "invalid": invalid,
            "invalid_rate": invalid / total if total else 0.0,
            "uncited_rate": uncited / n if n else 0.0,
            "expected_cite_rate": to_expected / n if n else 0.0,
            "n_traps": len(traps),
            "refusal_rate": (sum(r["answer"].strip() == REFUSAL for r in traps) / len(traps)
                             if traps else 0.0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    from src.generator import answer, check_citations
    from src.hybrid import hybrid_search
    from src.pipeline import indexes_exist, load_indexes

    questions = json.loads((ROOT / "eval" / "questions.json").read_text("utf-8"))
    traps = json.loads((ROOT / "eval" / "gen_traps.json").read_text("utf-8"))
    items = [dict(q, trap=False) for q in pick_subset(questions, args.n, args.seed)]
    items += [dict(t, trap=True, expected=[]) for t in traps]

    idx = {}
    for repo in sorted({q["repo"] for q in items}):
        if not indexes_exist(REPO_PATHS[repo]):
            sys.exit(f"[{repo}] indeks yok; önce eval/run_eval.py çalıştırın")
        idx[repo] = load_indexes(REPO_PATHS[repo])

    rows = []
    for q in items:
        vec, bm = idx[q["repo"]]
        hits = hybrid_search(q["question"], vec, bm)
        ans = answer(q["question"], hits)
        rows.append({"id": q["id"], "answer": ans, "bad": check_citations(ans, hits),
                     "expected_paths": [e["path"] for e in q["expected"]], "trap": q["trap"]})
        print(f"{q['id']}: {len(ans)} kar, geçersiz={len(rows[-1]['bad'])}", flush=True)

    m = gen_metrics(rows)
    lines = [f"# Üretim eval sonuçları (n={m['n']} soru, seed={args.seed}, {m['n_traps']} tuzak)", "",
             "| metrik | değer |", "|---|---|",
             f"| geçersiz atıf oranı | {m['invalid_rate']:.2f} ({m['invalid']}/{m['citations']}) |",
             f"| atıfsız cevap oranı | {m['uncited_rate']:.2f} |",
             f"| beklenen dosyaya atıf oranı | {m['expected_cite_rate']:.2f} |",
             f"| tuzakta \"{REFUSAL}\" oranı | {m['refusal_rate']:.2f} |", "",
             "Geçersiz atıflı sorular: " + (", ".join(r["id"] for r in rows if r["bad"]) or "-")]
    text = "\n".join(lines)
    print(text)
    (ROOT / "eval" / "gen_results.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""CLI: python -m src.cli {index,search,ask,eval}"""
import argparse
import subprocess
import sys

from . import config
from .hybrid import MODES, hybrid_search
from .pipeline import build_index, load_indexes


def cmd_index(a):
    st = build_index(a.repo)
    print(f"dosya: {st['files']}  parça: {st['chunks']}  türler: {st['kinds']}")
    print(f"indeks: {st['index_name']}")


def cmd_search(a):
    vec, bm = load_indexes(a.repo)
    hits = hybrid_search(a.query, vec, bm, mode=a.mode, top_k=a.k)
    print(f"{'#':>2}  {'path:satır':<48} {'symbol':<36} skor")
    for i, (c, s) in enumerate(hits, 1):
        print(f"{i:>2}  {f'{c.path}:{c.start_line}-{c.end_line}':<48} {c.symbol[:36]:<36} {s:.4f}")


def cmd_ask(a):
    from .generator import answer, sources
    vec, bm = load_indexes(a.repo)
    hits = hybrid_search(a.query, vec, bm, mode=a.mode, top_k=a.k)
    print(answer(a.query, hits))
    print("\nKaynaklar:")
    for s in sources(hits):
        print(f"  - {s}")


def cmd_eval(a):
    sys.exit(subprocess.call([sys.executable, str(config.ROOT / "eval" / "run_eval.py"),
                              "--set", a.set]))


def main():
    p = argparse.ArgumentParser(prog="src.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("index"); s.add_argument("--repo", required=True); s.set_defaults(f=cmd_index)
    for name, f in (("search", cmd_search), ("ask", cmd_ask)):
        s = sub.add_parser(name)
        s.add_argument("query"); s.add_argument("--repo", required=True)
        s.add_argument("--mode", default="hybrid", choices=MODES)
        s.add_argument("--k", type=int, default=config.TOP_K)
        s.set_defaults(f=f)
    s = sub.add_parser("eval"); s.add_argument("--set", default="main", choices=["main", "tuning"])
    s.set_defaults(f=cmd_eval)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()

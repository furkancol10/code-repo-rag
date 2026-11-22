"""CLI: python -m src.cli {index,search,ask,eval}"""
import argparse
import logging
import subprocess
import sys

from . import config
from .hybrid import MODES, hybrid_search
from .pipeline import RepoError, build_index, known_error_message, load_indexes, validate_repo

log = logging.getLogger(__name__)


def cmd_index(a):
    st = build_index(a.repo)
    print(f"dosya: {st['files']}  parça: {st['chunks']}  türler: {st['kinds']}")
    if st["unreadable"] or st["decode_errors"]:
        print(f"uyarı: okunamayan {st['unreadable']}, UTF-8 olmayan {st['decode_errors']} dosya")
    print(f"indeks: {st['index_name']}")


def cmd_search(a):
    validate_repo(a.repo)
    vec, bm = load_indexes(a.repo)
    hits = hybrid_search(a.query, vec, bm, mode=a.mode, top_k=a.k)
    print(f"{'#':>2}  {'path:satır':<48} {'symbol':<36} skor")
    for i, (c, s) in enumerate(hits, 1):
        print(f"{i:>2}  {f'{c.path}:{c.start_line}-{c.end_line}':<48} {c.symbol[:36]:<36} {s:.4f}")


def cmd_ask(a):
    from .generator import answer, check_citations, sources
    validate_repo(a.repo)
    vec, bm = load_indexes(a.repo)
    hits = hybrid_search(a.query, vec, bm, mode=a.mode, top_k=a.k)
    text = answer(a.query, hits)
    print(text)
    bad = check_citations(text, hits)
    if bad:
        print(f"\nUyarı: bağlamda olmayan atıflar: {', '.join(bad)}")
    print("\nKaynaklar:")
    for s in sources(hits):
        print(f"  - {s}")


def cmd_eval(a):
    sys.exit(subprocess.call([sys.executable, str(config.ROOT / "eval" / "run_eval.py"),
                              "--set", a.set]))


def main(argv=None) -> int:
    """Çıkış kodu: 0 başarı, 1 çalışma hatası (indeks yok, Ollama...), 2 geçersiz girdi."""
    p = argparse.ArgumentParser(prog="src.cli")
    p.add_argument("--verbose", "-v", action="store_true", help="ayrıntılı (DEBUG) log")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("index")
    s.add_argument("--repo", required=True)
    s.set_defaults(f=cmd_index)
    for name, f in (("search", cmd_search), ("ask", cmd_ask)):
        s = sub.add_parser(name)
        s.add_argument("query")
        s.add_argument("--repo", required=True)
        s.add_argument("--mode", default="hybrid", choices=MODES)
        s.add_argument("--k", type=int, default=config.TOP_K)
        s.set_defaults(f=f)
    s = sub.add_parser("eval")
    s.add_argument("--set", default="main", choices=["main", "tuning"])
    s.set_defaults(f=cmd_eval)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s", stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG if a.verbose else logging.INFO)
    try:
        a.f(a)
    except RepoError as e:
        print(f"hata: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 - kullanıcıya traceback yerine mesaj
        msg = known_error_message(e)
        if msg is None:
            log.debug("beklenmeyen hata", exc_info=True)
            msg = f"beklenmeyen hata ({type(e).__name__}): {e} (ayrıntı için --verbose)"
        print(f"hata: {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

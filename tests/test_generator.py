from types import SimpleNamespace as C

from src.generator import build_context, check_citations

HITS = [(C(path="src/a.py", start_line=10, end_line=40, symbol="f", text="x"), 1.0),
        (C(path="b/c.py", start_line=5, end_line=9, symbol="g", text="y"), 0.5)]


def test_valid_citations():
    assert check_citations("Bak [src/a.py:10-40] ve [src/a.py:12-20], [b/c.py:7].", HITS) == []


def test_invalid_citations():
    ans = "[src/a.py:30-60] [src/zzz.py:10-40] [b/c.py:1-3] [src/a.py:10-40]"
    assert check_citations(ans, HITS) == ["[src/a.py:30-60]", "[src/zzz.py:10-40]", "[b/c.py:1-3]"]


def test_context_numbered():
    ctx = build_context(HITS)
    assert ctx.startswith("[1] ### src/a.py:10-40 (f)")
    assert "[2] ### b/c.py:5-9 (g)" in ctx

from src.chunk_md import chunk_md
from src.chunk import chunk_file, make_embed_text

MD = """intro line

# Title
text
## Sub
a
b
```
# not heading
```
# Other
z
"""


def test_line_ranges():
    cs = chunk_md("README.md", MD)
    got = [(c.symbol, c.start_line, c.end_line) for c in cs]
    assert got == [("(giriş)", 1, 1), ("Title", 3, 4), ("Title > Sub", 5, 10), ("Other", 11, 12)]
    lines = MD.splitlines()
    for c in cs:
        assert c.text == "\n".join(lines[c.start_line - 1:c.end_line])
        assert c.kind == "section" and c.lang == "markdown"


def test_route_and_embed_text():
    cs = chunk_file(None, "d.md", "# A\nx\n")
    assert cs[0].id == "d.md::A"
    assert make_embed_text(cs[0]).startswith("# d.md :: A\n# # A\n")
    assert chunk_file(None, "x.txt", "hi") == []


def test_long_section_split(monkeypatch):
    from src import config
    monkeypatch.setattr(config, "MAX_CHUNK_LINES", 3)
    cs = chunk_md("r.md", "# T\n" + "l\n" * 6)
    assert [(c.start_line, c.end_line) for c in cs] == [(1, 3), (4, 6), (7, 7)]
    assert len({c.id for c in cs}) == 3


def test_form_feed_keeps_line_numbers():
    # \x0c ve \x85 editörlerde satır sonu değildir; satır numarası kaymamalı
    text = "# A\nbir\x0ciki\n\x85uc\n# B\nson\n"
    chunks = chunk_md("doc.md", text)
    b = next(c for c in chunks if c.symbol == "B")
    assert (b.start_line, b.end_line) == (4, 5)

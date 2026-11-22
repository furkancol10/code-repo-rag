from src import config
from src.chunk import chunk_file
from src.chunk_py import chunk_python

SRC = '''"""Modül docstring."""
import os

X = 1


@decorator
@other(arg=1)
def decorated(a, b=2) -> int:
    def inner():
        return a
    return inner() + b


class Short:
    """Kısa sınıf."""
    y = 2

    def m(self):
        return self.y


class Long(Base):
    """Uzun sınıf."""
    field = 1

    @property
    def a(self):
        return 1

    async def b(self, x):
        return x

    z = 3


def long_func(n):
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    j = 10
    k = 11
    return n


if __name__ == "__main__":
    long_func(1)
'''


def _chunks(monkeypatch, src=SRC, n=10):
    monkeypatch.setattr(config, "MAX_CHUNK_LINES", n)
    return chunk_python("f.py", src)


def test_spans_exact(monkeypatch):
    got = [(c.id, c.kind, c.symbol, c.start_line, c.end_line) for c in _chunks(monkeypatch)]
    assert got == [
        ("f.py::<module>", "module", "<module>", 1, 4),
        ("f.py::decorated", "function", "decorated", 7, 12),
        ("f.py::Short", "class", "Short", 15, 20),
        ("f.py::Long", "class", "Long", 23, 25),
        ("f.py::Long.a", "method", "Long.a", 27, 29),
        ("f.py::Long.b", "method", "Long.b", 31, 32),
        ("f.py::Long~2", "class", "Long", 34, 34),
        ("f.py::long_func", "function", "long_func", 37, 46),
        ("f.py::long_func#2", "function", "long_func", 47, 49),
        ("f.py::<module>~2", "module", "<module>", 52, 53),
    ]


def test_signatures_and_decorators(monkeypatch):
    cs = {c.id: c for c in _chunks(monkeypatch)}
    d = cs["f.py::decorated"]
    assert d.signature == "def decorated(a, b=2) -> int"
    assert d.text.startswith("@decorator\n@other(arg=1)\ndef decorated")
    assert "def inner():" in d.text  # iç fonksiyon üstte kalır
    assert not any(c.symbol.endswith("inner") for c in cs.values())
    assert cs["f.py::Long"].signature == "class Long(Base)"
    assert cs["f.py::Long.a"].text.startswith("    @property\n    def a(self):")
    assert cs["f.py::Long.b"].signature == "async def b(self, x)"
    assert "def m(self)" in cs["f.py::Short"].text  # kısa sınıf bölünmez
    assert "def a" not in cs["f.py::Long"].text


def test_text_matches_lines_and_header(monkeypatch):
    lines = SRC.splitlines()
    for c in _chunks(monkeypatch):
        orig = "\n".join(lines[c.start_line - 1:c.end_line])
        if c.id.endswith("#2"):
            assert c.text == f"{c.signature}\n{orig}"
        else:
            assert c.text == orig
        assert c.lang == "python"
    part2 = next(c for c in _chunks(monkeypatch) if c.id == "f.py::long_func#2")
    assert part2.text == "def long_func(n)\n    j = 10\n    k = 11\n    return n"


def test_split_parts_respect_limit(monkeypatch):
    body = "\n".join(f"    v{i} = {i}" for i in range(200))
    cs = _chunks(monkeypatch, f"def big():\n{body}\n", n=80)
    assert [(c.start_line, c.end_line) for c in cs] == [(1, 80), (81, 159), (160, 201)]
    assert all(len(c.text.splitlines()) <= 80 for c in cs)
    assert len({c.id for c in cs}) == 3


def test_default_max_keeps_long_class_whole():
    cs = chunk_python("f.py", SRC)
    assert [c.id for c in cs if c.symbol.startswith("Long")] == ["f.py::Long"]
    assert [c.id for c in cs if c.symbol == "long_func"] == ["f.py::long_func"]


def test_syntax_error_falls_back_to_lines(monkeypatch):
    src = "def broken(:\n    pass\n\nx = 1\n"
    cs = _chunks(monkeypatch, src)
    assert [(c.kind, c.symbol, c.start_line, c.end_line) for c in cs] == [
        ("module", "<module>", 1, 4)]
    long_src = "\n".join(["x = ("] + [f"  {i}," for i in range(7)] + ["", "y = 2", "z = 3"])
    cs = _chunks(monkeypatch, long_src)  # 11 satır, boş satır 9 → 10'dan bölünür
    assert [(c.start_line, c.end_line) for c in cs] == [(1, 8), (10, 11)]
    assert cs[1].text == "y = 2\nz = 3" and cs[1].id == "f.py::<module>#2"


def test_empty_and_comment_only():
    assert chunk_python("e.py", "") == []
    assert chunk_python("e.py", "\n   \n") == []
    assert chunk_python("e.py", "# sadece yorum\n") == []


def test_route():
    assert chunk_file(None, "a/b.py", "def f():\n    pass\n")[0].id == "a/b.py::f"


def test_form_feed_and_unicode_separators_keep_line_numbers():
    for sep in ("\x0c", "\x1c", "\x85", "\u2028"):
        # sep, kod içinde (form feed: boşluk, diğerleri: yorum içinde) ast'nin satırını bölmez
        line2 = sep if sep == "\x0c" else f"# a{sep}b"
        text = f"import os\n{line2}\ndef a():\n    return 1\n"
        fn = [c for c in chunk_python("m.py", text) if c.symbol == "a"]
        assert len(fn) == 1, repr(sep)
        assert (fn[0].start_line, fn[0].end_line) == (3, 4), repr(sep)
        assert fn[0].text == "def a():\n    return 1", repr(sep)
        mod = [c for c in chunk_python("m.py", text) if c.symbol != "a"]
        if sep != "\x0c":  # form feed tek başına boşluk satırı, parçada korunmaz
            assert any(line2 in c.text for c in mod), repr(sep)

from types import SimpleNamespace as C

from eval.run_eval import base_symbol, dedupe, is_match, rank_of, symbol_matches


def ch(path, symbol):
    return C(path=path, symbol=symbol)


def test_exact_and_suffix():
    assert symbol_matches("NumpyIndex.search", "NumpyIndex.search")
    assert symbol_matches("NumpyIndex.search#2", "NumpyIndex.search")
    assert symbol_matches("detect~2", "detect")
    assert base_symbol("a#12") == "a"


def test_markdown_last_heading():
    assert symbol_matches("Kurulum > GPU", "GPU")
    assert symbol_matches("Kurulum > GPU#2", "GPU")
    assert not symbol_matches("Kurulum > GPU", "Kurulum > CPU")


def test_class_expected():
    assert symbol_matches("Sinif", "Sinif")
    assert symbol_matches("Sinif.metot", "Sinif")
    assert not symbol_matches("SinifB.metot", "Sinif")
    assert not symbol_matches("Sinif", "Sinif.metot")
    assert not symbol_matches("<module>", "Sinif")


def test_path_must_match():
    exp = [{"path": "a.py", "symbol": "f"}]
    assert is_match(ch("a.py", "f"), exp)
    assert not is_match(ch("b.py", "f"), exp)


def test_dedupe_and_rank():
    hits = [(ch("a.py", "f"), 3), (ch("a.py", "f#2"), 2), (ch("a.py", "g"), 1),
            (ch("b.py", "h"), 0.5)]
    assert [c.symbol for c, _ in dedupe(hits)] == ["f", "g", "h"]
    assert rank_of(hits, [{"path": "b.py", "symbol": "h"}]) == 3
    assert rank_of(hits, [{"path": "z.py", "symbol": "h"}]) is None

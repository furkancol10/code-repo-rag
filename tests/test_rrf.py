import pytest

from src import hybrid
from src.chunk import CodeChunk
from src.hybrid import hybrid_search, rrf


def test_rrf_hand_computed():
    got = rrf([["a", "b", "c"], ["b", "c", "d"]], k=60)
    # a=1/61, b=1/62+1/61, c=1/63+1/62, d=1/63
    assert [i for i, _ in got] == ["b", "c", "a", "d"]
    s = dict(got)
    assert s["b"] == pytest.approx(1 / 61 + 1 / 62)
    assert s["c"] == pytest.approx(1 / 62 + 1 / 63)
    assert s["a"] == pytest.approx(1 / 61)
    assert s["d"] == pytest.approx(1 / 63)


def test_rrf_small_k_and_ties():
    assert rrf([["x", "y"], ["y"]], k=0) == [("y", 1.5), ("x", 1.0)]  # y=1/2+1/1
    assert rrf([["p"], ["q"]], k=1) == [("p", 0.5), ("q", 0.5)]  # eşitlikte ilk görülen
    assert rrf([["a", "a", "b"]], k=0) == [("a", 1.0), ("b", 1 / 3)]  # tekrar sayılmaz
    assert rrf([]) == []


def _c(name):
    return CodeChunk(f"m.py::{name}", "m.py", "python", "function", name, "", 1, 1, "")


class _Fake:
    def __init__(self, names):
        self.res = [(_c(n), 1.0 / (i + 1)) for i, n in enumerate(names)]
        self.calls = []

    def search(self, q, k):
        self.calls.append((q, k))
        return self.res[:k]


def test_hybrid_search_modes(monkeypatch):
    monkeypatch.setattr(hybrid, "embed_query", lambda q: "VEC")
    vec, bm = _Fake(["a", "b", "c"]), _Fake(["b", "c", "d"])
    out = hybrid_search("q", vec, bm, mode="hybrid", top_k=2, candidates=30,
                        k=60, w_bm25=1.0, w_vec=1.0)
    assert [c.symbol for c, _ in out] == ["b", "c"]
    assert out[0][1] == pytest.approx(1 / 61 + 1 / 62)
    assert vec.calls == [("VEC", 30)] and bm.calls == [("q", 30)]
    assert [c.symbol for c, _ in hybrid_search("q", vec, bm, mode="bm25", top_k=1)] == ["b"]
    assert [c.symbol for c, _ in hybrid_search("q", vec, bm, mode="vector", top_k=1)] == ["a"]
    with pytest.raises(ValueError):
        hybrid_search("q", vec, bm, mode="xxx")


def test_rrf_weighted_hand_computed():
    got = rrf([["a", "b"], ["b", "c"]], k=0, weights=[1.0, 0.5])
    # a=1/1, b=1/2+0.5/1=1.0, c=0.5/2=0.25; a ile b eşit → ilk görülen a
    assert got == [("a", 1.0), ("b", 1.0), ("c", 0.25)]
    got = rrf([["a", "b", "c"], ["b", "c", "d"]], k=60, weights=[2.0, 0.3])
    s = dict(got)
    assert s["b"] == pytest.approx(2 / 62 + 0.3 / 61)
    assert s["d"] == pytest.approx(0.3 / 63)
    assert [i for i, _ in got] == ["b", "c", "a", "d"]
    with pytest.raises(ValueError):
        rrf([["a"]], weights=[1.0, 1.0])


def test_rrf_weights_none_equals_unweighted():
    cases = [[["a", "b", "c"], ["b", "c", "d"]], [["x", "y"], ["y"]], [["a", "a", "b"]], []]
    for rk in cases:
        for k in (0, 1, 60):
            assert rrf(rk, k=k) == rrf(rk, k=k, weights=None)
            assert rrf(rk, k=k) == rrf(rk, k=k, weights=[1.0] * len(rk))


def test_hybrid_search_weights(monkeypatch):
    monkeypatch.setattr(hybrid, "embed_query", lambda q: "VEC")
    vec, bm = _Fake(["a", "b", "c"]), _Fake(["d", "c", "b"])
    out = hybrid_search("q", vec, bm, top_k=1, candidates=30, k=0, w_bm25=0.1, w_vec=1.0)
    assert [c.symbol for c, _ in out] == ["a"]
    out = hybrid_search("q", vec, bm, top_k=1, candidates=30, k=0, w_bm25=1.0, w_vec=1.0)
    assert out[0][1] == pytest.approx(1.0)  # a=1, d=1 → ilk görülen (vektör) a

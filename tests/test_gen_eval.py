import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
from gen_eval import gen_metrics, pick_subset  # noqa: E402


def _r(answer, bad=(), exp=("a.py",), trap=False):
    return {"answer": answer, "bad": list(bad), "expected_paths": list(exp), "trap": trap}


def test_gen_metrics_hand_computed():
    rows = [
        _r("x [a.py:1-3] y [b.py:5]", bad=["[b.py:5]"]),   # 2 atıf, 1 geçersiz, doğru dosya
        _r("atıfsız cevap"),                               # atıfsız
        _r("z [c.py:2]"),                                  # yanlış dosya
        _r("Bu bilgi repoda yok.", trap=True),
        _r("uydurma [a.py:1]", trap=True),
    ]
    m = gen_metrics(rows)
    assert m["n"] == 3 and m["citations"] == 3 and m["invalid"] == 1
    assert m["invalid_rate"] == pytest.approx(1 / 3)
    assert m["uncited_rate"] == pytest.approx(1 / 3)
    assert m["expected_cite_rate"] == pytest.approx(1 / 3)
    assert m["n_traps"] == 2 and m["refusal_rate"] == 0.5


def test_gen_metrics_empty():
    m = gen_metrics([])
    assert m["invalid_rate"] == m["uncited_rate"] == m["refusal_rate"] == 0.0


def test_pick_subset_balanced_deterministic():
    qs = [{"id": f"n{i}", "type": "name"} for i in range(10)] + \
         [{"id": f"c{i}", "type": "conceptual"} for i in range(10)]
    a, b = pick_subset(qs, 6, 0), pick_subset(qs, 6, 0)
    assert a == b and len(a) == 6
    assert sum(q["type"] == "name" for q in a) == 3

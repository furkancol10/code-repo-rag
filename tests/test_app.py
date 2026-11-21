from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import src.generator
import src.hybrid
import src.pipeline
import src.vector_index

APP = str(Path(__file__).resolve().parent.parent / "app.py")
CHUNK = SimpleNamespace(path="a.py", start_line=1, end_line=3, symbol="f", text="x=1", lang="python")


@pytest.fixture
def mocks(monkeypatch):
    st.cache_resource.clear()
    ans = MagicMock(return_value="LLM CEVABI")
    load = MagicMock(return_value=(object(), object()))
    monkeypatch.setattr(src.generator, "answer", ans)
    monkeypatch.setattr(src.hybrid, "hybrid_search", lambda *a, **kw: [(CHUNK, 0.5)])
    monkeypatch.setattr(src.pipeline, "indexes_exist", lambda repo: True)
    monkeypatch.setattr(src.pipeline, "load_indexes", load)
    return ans, load


def run(use_llm):
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.checkbox[0].set_value(use_llm)
    at.text_input[0].set_value("soru?").run()
    return at


def test_llm_off_no_answer_call(mocks):
    ans, _ = mocks
    at = run(False)
    assert not at.exception
    ans.assert_not_called()
    assert len(at.expander) == 1
    assert [h.value for h in at.header] == ["Kaynaklar"]


def test_llm_on_calls_answer(mocks):
    ans, _ = mocks
    at = run(True)
    assert not at.exception
    ans.assert_called_once()
    assert "LLM CEVABI" in at.markdown[0].value
    assert len(at.expander) == 1


def test_load_indexes_cached(mocks):
    _, load = mocks
    at = run(False)
    at.text_input[0].set_value("soru 2").run()
    assert load.call_count == 1


def test_index_button_clears_cache(mocks, monkeypatch):
    _, load = mocks
    monkeypatch.setattr(src.pipeline, "build_index", lambda repo: {"chunks": 1, "files": 1, "kinds": {}})
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.text_input[0].set_value("soru?").run()
    at.text_input[0].set_value("soru??").run()
    assert load.call_count == 1  # önbellekten
    at.sidebar.button[0].click().run()
    at.text_input[0].set_value("soru???").run()
    assert load.call_count == 2


def test_cache_key_includes_index_name(mocks, monkeypatch):
    _, load = mocks
    names = iter(["n1", "n2"])
    monkeypatch.setattr(src.vector_index, "index_name", lambda m, r: next(names))
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.text_input[0].set_value("a").run()
    at.text_input[0].set_value("b").run()
    assert load.call_count == 2

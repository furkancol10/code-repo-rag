from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import src.config
import src.generator
import src.hybrid
import src.pipeline
import src.vector_index

APP = str(Path(__file__).resolve().parent.parent / "app.py")
CHUNK = SimpleNamespace(path="a.py", start_line=1, end_line=3, symbol="f", text="x=1", lang="python")


@pytest.fixture
def mocks(monkeypatch, tmp_path):
    st.cache_resource.clear()
    monkeypatch.setattr(src.config, "DEFAULT_REPO", tmp_path)
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


def test_default_repo_from_config(mocks, tmp_path):
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert at.sidebar.text_input[0].value == str(tmp_path)


def test_source_label_readable_and_score_separate(mocks):
    at = run(False)
    assert at.expander[0].label == "a.py:1-3 · f"
    assert "skor 0.5000" in [c.value for c in at.expander[0].caption]


def test_missing_repo_message(mocks, tmp_path):
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.text_input[0].set_value(str(tmp_path / "yok")).run()
    at.text_input[0].set_value("soru?").run()
    assert not at.exception
    assert any("yok" in e.value for e in at.error)
    assert len(at.expander) == 0


def test_ollama_down_specific_message(mocks):
    ans, _ = mocks
    ans.side_effect = ConnectionError("refused")
    at = run(True)
    assert not at.exception
    assert any("Ollama'ya bağlanılamadı" in e.value for e in at.error)


def test_unknown_llm_error_short_and_logged(mocks, caplog):
    ans, _ = mocks
    ans.side_effect = KeyError("gizli-ayrinti")
    with caplog.at_level("ERROR", logger="kra.app"):
        at = run(True)
    assert not at.exception
    assert any("KeyError" in e.value and "log" in e.value for e in at.error)
    assert "gizli-ayrinti" not in " ".join(e.value for e in at.error)
    assert "KeyError" in caplog.text


def test_index_button_known_error(mocks, monkeypatch):
    def bad(repo):
        raise src.pipeline.RepoError("repo yolu çok geniş")
    monkeypatch.setattr(src.pipeline, "build_index", bad)
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.button[0].click().run()
    assert not at.exception
    assert any("çok geniş" in e.value for e in at.sidebar.error)


def test_index_button_reports_skipped_files(mocks, monkeypatch):
    monkeypatch.setattr(src.pipeline, "build_index", lambda repo: {
        "chunks": 1, "files": 1, "kinds": {}, "unreadable": 2, "decode_errors": 1})
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.button[0].click().run()
    assert any("Okunamayan 2" in w.value for w in at.sidebar.warning)

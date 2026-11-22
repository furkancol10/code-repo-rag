"""Uçtan uca entegrasyon: tara -> parçala -> embed (sahte) -> indeksle -> ara."""
import hashlib
import logging
import re

import numpy as np
import pytest

import src.hybrid
import src.pipeline
from src import config
from src.hybrid import hybrid_search
from src.pipeline import (RepoError, build_index, indexes_exist, known_error_message,
                          load_indexes, validate_repo)

DIM = 64


def fake_embed(texts):
    """Kelime torbası -> sabit boyutlu, normalize vektör (GPU/model gerekmez)."""
    out = np.zeros((len(texts), DIM), dtype=np.float32)
    for i, t in enumerate(texts):
        for w in re.findall(r"[a-z]+", t.lower()):
            out[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % DIM] += 1.0
        n = np.linalg.norm(out[i])
        if n:
            out[i] /= n
    return out


@pytest.fixture
def fakes(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path / "idx")
    monkeypatch.setattr(src.pipeline, "embed_passages", fake_embed)
    monkeypatch.setattr(src.pipeline, "release_gpu", lambda: None)
    monkeypatch.setattr(src.hybrid, "embed_query", lambda q: fake_embed([q])[0])


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    (r / "notes.py").write_text(
        "def save_note(text):\n    '''Persist the note text to disk.'''\n    return text\n", "utf-8")
    (r / "net.py").write_text(
        "def send_request(url):\n    '''Send an http request to the url.'''\n    return url\n", "utf-8")
    (r / "README.md").write_text("# Installation\n\nRun pip install to setup the package.\n", "utf-8")
    return r


def test_build_load_search_end_to_end(fakes, repo):
    assert not indexes_exist(repo)
    st = build_index(repo)
    assert st["files"] == 3
    assert st["kinds"].get("function") == 2 and st["kinds"].get("section") == 1
    assert st["chunks"] == sum(st["kinds"].values())
    assert st["unreadable"] == 0 and st["decode_errors"] == 0
    assert indexes_exist(repo)
    vec, bm = load_indexes(repo)
    for mode in ("hybrid", "vector", "bm25"):
        top = hybrid_search("save the note text to disk", vec, bm, mode=mode, top_k=3)[0][0]
        assert top.symbol == "save_note", mode
    top = hybrid_search("send http request", vec, bm, top_k=3)[0][0]
    assert top.symbol == "send_request"
    top = hybrid_search("pip install setup package", vec, bm, top_k=3)[0][0]
    assert top.path == "README.md"


def test_load_indexes_missing_raises(fakes, repo):
    with pytest.raises(FileNotFoundError):
        load_indexes(repo)


def test_undecodable_file_counted_and_logged(fakes, repo, caplog):
    (repo / "bad.py").write_bytes(b"def ok():\n    return '\xff\xfe'\n")
    with caplog.at_level(logging.WARNING, logger="src.pipeline"):
        st = build_index(repo)
    assert st["decode_errors"] == 1 and st["unreadable"] == 0
    assert "bad.py" in caplog.text


def test_unreadable_file_counted(fakes, repo, monkeypatch, caplog):
    real = type(repo).read_bytes

    def rb(self):
        if self.name == "net.py":
            raise PermissionError("izin yok")
        return real(self)
    monkeypatch.setattr(type(repo), "read_bytes", rb)
    with caplog.at_level(logging.WARNING, logger="src.pipeline"):
        st = build_index(repo)
    assert st["unreadable"] == 1 and st["files"] == 2
    assert "net.py" in caplog.text


def test_validate_repo_rejects_missing_file_and_broad_roots(tmp_path, monkeypatch):
    with pytest.raises(RepoError, match="yok"):
        validate_repo(tmp_path / "nope")
    f = tmp_path / "f.txt"
    f.write_text("x")
    with pytest.raises(RepoError, match="dizin"):
        validate_repo(f)
    with pytest.raises(RepoError, match="geniş"):
        validate_repo("/")
    home = tmp_path / "home" / "u"
    home.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    with pytest.raises(RepoError, match="geniş"):
        validate_repo(home)
    with pytest.raises(RepoError, match="geniş"):
        validate_repo(home.parent)
    sub = home / "proj"
    sub.mkdir()
    assert validate_repo(sub) == sub.resolve()


def test_total_size_limit(fakes, repo, monkeypatch):
    monkeypatch.setattr(config, "MAX_TOTAL_BYTES", 50)
    with pytest.raises(RepoError, match="sınır"):
        build_index(repo)
    assert not indexes_exist(repo)


def test_build_index_rejects_missing_repo(fakes, tmp_path):
    with pytest.raises(RepoError):
        build_index(tmp_path / "nope")


def test_known_error_message():
    import httpx
    import ollama
    assert "Ollama" in known_error_message(ConnectionError("refused"))
    assert "Ollama" in known_error_message(httpx.ConnectError("x"))
    assert "Ollama" in known_error_message(ollama.ResponseError("model yok", 404))
    assert "İndeksle" in known_error_message(FileNotFoundError("indeks yok"))
    assert known_error_message(RepoError("kötü yol")) == "kötü yol"
    assert known_error_message(KeyError("x")) is None


def test_default_repo_env(monkeypatch):
    import importlib
    monkeypatch.setenv("KRA_DEFAULT_REPO", "/tmp/benim_repom")
    try:
        importlib.reload(config)
        assert str(config.DEFAULT_REPO) == "/tmp/benim_repom"
    finally:
        monkeypatch.delenv("KRA_DEFAULT_REPO")
        importlib.reload(config)

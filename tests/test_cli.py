"""CLI: index/search/ask alt komutları ve hata yolları (sahte embedder, GPU/Ollama yok)."""
import logging

import pytest

import src.generator
from src import cli
from tests.test_pipeline import fakes, repo  # noqa: F401  (fixture'lar)


def run(argv, capsys):
    code = cli.main(argv)
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_index_then_search(fakes, repo, capsys):
    code, out, _ = run(["index", "--repo", str(repo)], capsys)
    assert code == 0 and "dosya: 3" in out
    code, out, _ = run(["search", "save note text to disk", "--repo", str(repo), "--k", "2"], capsys)
    assert code == 0
    first = [ln for ln in out.splitlines() if ln.strip().startswith("1 ")][0]
    assert "notes.py" in first and "save_note" in first


def test_missing_repo(fakes, tmp_path, capsys):
    for cmd in (["index"], ["search", "q"], ["ask", "q"]):
        code, out, err = run(cmd + ["--repo", str(tmp_path / "yok")], capsys)
        assert code == 2, cmd
        assert "Traceback" not in err and "yok" in err


def test_broad_root_rejected(fakes, tmp_path, monkeypatch, capsys):
    home = tmp_path / "h"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    code, _, err = run(["index", "--repo", str(home)], capsys)
    assert code == 2 and "geniş" in err


def test_search_without_index(fakes, repo, capsys):
    code, out, err = run(["search", "q", "--repo", str(repo)], capsys)
    assert code == 1 and "index" in err and "Traceback" not in err


def test_size_limit(fakes, repo, monkeypatch, capsys):
    from src import config
    monkeypatch.setattr(config, "MAX_TOTAL_BYTES", 10)
    code, _, err = run(["index", "--repo", str(repo)], capsys)
    assert code == 2 and "sınır" in err


def test_ask_ollama_down(fakes, repo, monkeypatch, capsys):
    run(["index", "--repo", str(repo)], capsys)

    def boom(*a, **k):
        raise ConnectionError("Failed to connect to Ollama")
    monkeypatch.setattr(src.generator.ollama, "chat", boom)
    code, out, err = run(["ask", "save note", "--repo", str(repo)], capsys)
    assert code == 1 and "Ollama" in err and "Traceback" not in err


def test_ask_ok(fakes, repo, monkeypatch, capsys):
    run(["index", "--repo", str(repo)], capsys)
    monkeypatch.setattr(src.generator.ollama, "chat",
                        lambda **k: {"message": {"content": "Cevap."}})
    code, out, _ = run(["ask", "save note", "--repo", str(repo)], capsys)
    assert code == 0 and "Cevap." in out and "Kaynaklar" in out


def test_unexpected_error_short_message(fakes, repo, monkeypatch, capsys):
    run(["index", "--repo", str(repo)], capsys)
    monkeypatch.setattr(cli, "hybrid_search", lambda *a, **k: 1 / 0)
    code, _, err = run(["search", "q", "--repo", str(repo)], capsys)
    assert code == 1 and "ZeroDivisionError" in err and "Traceback" not in err


def test_verbose_sets_debug(fakes, repo, capsys):
    root = logging.getLogger()
    old = (root.level, list(root.handlers))
    try:
        run(["--verbose", "index", "--repo", str(repo)], capsys)
        assert root.level == logging.DEBUG
        run(["index", "--repo", str(repo)], capsys)
        assert root.level == logging.INFO
    finally:
        root.setLevel(old[0])
        root.handlers[:] = old[1]

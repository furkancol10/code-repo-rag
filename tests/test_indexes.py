import pickle

import numpy as np

from src import bm25_index, config, vector_index
from src.bm25_index import BM25Index
from src.chunk import CodeChunk
from src.vector_index import NumpyIndex


def _mk(i, sym, text):
    return CodeChunk(f"a{i}.py::{sym}", f"a{i}.py", "python", "function", sym, "", 1, 2, text)


CH = [_mk(0, "save_note", "write note to disk"), _mk(1, "load_note", "read note file"),
      _mk(2, "http_client", "send request")]


def test_bm25_json_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path)
    a = BM25Index("r")
    a.build(CH)
    b = BM25Index("r")
    assert b.search("save note", 3) == a.search("save note", 3)
    assert b.search("save note", 1)[0][0] == CH[0]


def test_bm25_never_unpickles(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path)
    BM25Index("p").build(CH)
    (tmp_path / "bm25" / "p" / "evil.pkl").write_bytes(pickle.dumps([1]))

    def boom(*a, **k):
        raise AssertionError("pickle.load çağrıldı")
    monkeypatch.setattr(pickle, "load", boom)
    monkeypatch.setattr(pickle, "loads", boom)
    assert BM25Index("p").search("http client", 1)[0][0] == CH[2]


def test_bm25_old_pkl_only_dir_not_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path)
    d = tmp_path / "bm25" / "old"
    d.mkdir(parents=True)
    (d / "bm25.pkl").write_bytes(b"not a pickle")
    assert not BM25Index("old").exists()


def _vecs(rows):
    v = np.array(rows, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_vector_search_cached_and_refreshed(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path)
    NumpyIndex("v").build(CH, _vecs([[1, 0], [0, 1], [1, 1]]))
    idx = NumpyIndex("v")  # yeni nesne: önbellek boş
    calls = []
    real = np.load
    monkeypatch.setattr(vector_index.np, "load", lambda *a, **k: (calls.append(a), real(*a, **k))[1])
    q = np.array([1, 0], dtype=np.float32)
    r1 = idx.search(q, 2)
    r2 = idx.search(q, 2)
    assert r1 == r2 and r1[0][0] == CH[0] and r1[1][0] == CH[2]
    assert len(calls) == 1  # ikinci arama diskten okumadı
    idx.build(CH[:2], _vecs([[0, 1], [1, 0]]))  # build sonrası yeni veri
    r3 = idx.search(q, 5)
    assert [c for c, _ in r3] == [CH[1], CH[0]]
    assert len(calls) == 1

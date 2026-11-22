import pickle

import numpy as np

from src import config, vector_index
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


def test_numpy_cache_sees_rebuild_by_other_instance(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path)
    a = NumpyIndex("stale")
    a.build(CH, _vecs([[1, 0], [0, 1], [1, 1]]))
    q = np.array([1.0, 0.0], dtype=np.float32)
    first = a.search(q, 1)[0][0].id
    b = NumpyIndex("stale")
    b.build(CH, _vecs([[0, 1], [1, 0], [0, 1]]))  # farklı veri
    assert a.search(q, 1)[0][0].id != first
    assert a.search(q, 1)[0][0].id == CH[1].id


def _git_repo(tmp_path):
    import subprocess
    r = tmp_path / "repo"
    r.mkdir()
    (r / "a.py").write_text("def a():\n    return 1\n")
    env = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "init", "-q"], cwd=r, check=True)
    subprocess.run(["git", "add", "."], cwd=r, check=True)
    subprocess.run([*env, "commit", "-qm", "x"], cwd=r, check=True)
    return r


def test_index_name_clean_git_has_no_content_hash(tmp_path):
    r = _git_repo(tmp_path)
    n = vector_index.index_name("m", r)
    assert n == f"m_{vector_index.repo_hash(r)}_{vector_index.commit_short(r)}"


def test_index_name_changes_when_dirty(tmp_path):
    r = _git_repo(tmp_path)
    clean = vector_index.index_name("m", r)
    (r / "a.py").write_text("def a():\n    return 2222\n")
    d1 = vector_index.index_name("m", r)
    assert d1 != clean and d1.startswith(clean)
    (r / "a.py").write_text("def a():\n    return 3\n")
    assert vector_index.index_name("m", r) != d1


def test_index_name_nogit_tracks_changes(tmp_path):
    r = tmp_path / "plain"
    r.mkdir()
    (r / "a.py").write_text("x = 1\n")
    n1 = vector_index.index_name("m", r)
    assert "_nogit_" in n1
    (r / "a.py").write_text("x = 22\n")
    assert vector_index.index_name("m", r) != n1


def test_prune_indexes(tmp_path, monkeypatch):
    import os
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path / "idx")
    r = tmp_path / "r"
    r.mkdir()
    rh = vector_index.repo_hash(r)
    for _i, kind in enumerate(("numpy", "bm25")):
        for j in range(3):
            d = config.INDEX_DIR / kind / f"m_{rh}_c{j}"
            d.mkdir(parents=True)
            os.utime(d, ns=(10**9 * (j + 1),) * 2)
    other = config.INDEX_DIR / "numpy" / "m_deadbeef_c0"
    other.mkdir()
    vector_index.prune_indexes(r, keep=1)
    for kind in ("numpy", "bm25"):
        left = sorted(p.name for p in (config.INDEX_DIR / kind).iterdir())
        assert [n for n in left if rh in n] == [f"m_{rh}_c2"]
    assert other.exists()


def test_concurrent_build_same_name(tmp_path, monkeypatch):
    import threading
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path)
    errs = []

    def work(k):
        try:
            for _ in range(5):
                v = np.full((3, 2), k, dtype=np.float32)
                NumpyIndex("c").build(CH, v)
                BM25Index("c").build(CH)
                NumpyIndex("c").search(np.ones(2, dtype=np.float32), 2)
                BM25Index("c").search("note", 2)
        except BaseException as e:  # noqa
            errs.append(e)

    ts = [threading.Thread(target=work, args=(k,)) for k in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errs
    idx = NumpyIndex("c")
    assert len(idx.chunks()) == 3 and len(set(idx._vecs.ravel().tolist())) == 1
    assert BM25Index("c").search("save note", 1)[0][0] == CH[0]
    left = [p.name for k in ("numpy", "bm25") for p in (tmp_path / k).iterdir()]
    assert sorted(n for n in left if not n.startswith(".")) == ["c", "c"]
    assert not [n for n in left if ".tmp" in n or ".old" in n]

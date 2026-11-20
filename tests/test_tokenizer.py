from src.bm25_index import BM25Index, tokenize_code
from src.chunk import CodeChunk
from src import config


def test_camel_case():
    assert tokenize_code("getUserById") == ["get", "user", "by", "id", "getuserbyid"]


def test_snake_case():
    assert tokenize_code("chunk_by_heading") == ["chunk", "by", "heading", "chunkbyheading"]


def test_dotted_and_acronym():
    assert tokenize_code("NumpyIndex.search") == [
        "numpy", "index", "numpyindex", "search", "numpyindex.search"]
    assert tokenize_code("HTTPServer") == ["http", "server", "httpserver"]
    assert tokenize_code("Base64Coder") == ["base64", "coder", "base64coder"]


def test_turkish_and_filtering():
    assert tokenize_code("ağaçYapısı İndeks") == ["ağaç", "yapısı", "ağaçyapısı", "indeks"]
    assert tokenize_code("a = self.x + 1 if 42 else None") == []
    assert tokenize_code("self.dir.rename") == ["dir", "rename", "dir.rename"]


def _c(i, symbol, text, path="src/m.py"):
    return CodeChunk(f"{path}::{symbol}", path, "python", "function", symbol, "", 1, 1, text)


CHUNKS = [
    _c(1, "get_user_by_id", "def get_user_by_id(uid):\n    return db[uid]"),
    _c(2, "save_note", "def save_note(n):\n    write(n)"),
    _c(3, "NumpyIndex.search", "def search(self, qvec, k):\n    return top", path="src/index.py"),
    _c(4, "helper", "x = 1"),
]


def test_bm25_search_ranks_name():
    idx = BM25Index()
    idx.build(CHUNKS)
    assert idx.search("getUserById", 3)[0][0].symbol == "get_user_by_id"
    assert idx.search("NumpyIndex.search", 3)[0][0].symbol == "NumpyIndex.search"
    assert idx.search("zzz_yok", 3) == []
    assert idx.search("", 3) == []


def test_bm25_save_load(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INDEX_DIR", tmp_path)
    BM25Index("t").build(CHUNKS)
    assert (tmp_path / "bm25" / "t" / "bm25.pkl").exists()
    idx = BM25Index("t")
    assert idx.exists()
    assert idx.search("save note", 1)[0][0] == CHUNKS[1]


def test_bm25_empty():
    idx = BM25Index()
    idx.build([])
    assert idx.search("x y", 5) == []

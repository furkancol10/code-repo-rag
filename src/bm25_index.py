"""BM25 indeksi: kod tokenizer'ı (camelCase/snake_case/dotted) + rank-bm25 BM25Okapi."""
import json
import re
import shutil
from dataclasses import asdict

import numpy as np
from rank_bm25 import BM25Okapi

from . import config
from .chunk import CodeChunk

_NAME = re.compile(r"[^\W\d]\w*(?:\.[^\W\d]\w*)*")  # rakamla başlamayan adlar
# Python anahtar kelimeleri + sık geçen anlamsız kelimeler (EN/TR)
_STOP = {
    "self", "cls", "def", "class", "return", "import", "from", "as", "in", "is", "if",
    "elif", "else", "for", "while", "not", "and", "or", "none", "true", "false", "pass",
    "with", "try", "except", "finally", "raise", "lambda", "yield", "async", "await",
    "the", "an", "of", "to", "ve", "ile", "bu", "bir", "için", "da", "de", "mi", "mı",
    "mu", "mü", "ne", "nerede", "nasıl", "hangi", "neden",
}
SYMBOL_WEIGHT = 3
PATH_WEIGHT = 3


def _lower(s: str) -> str:
    return s.replace("İ", "i").lower()


def _split_case(word: str) -> list[str]:
    """getUserById -> get,User,By,Id; HTTPServer -> HTTP,Server; Base64Coder -> Base64,Coder."""
    parts, cur = [], ""
    for i, ch in enumerate(word):
        if cur and ch.isupper():
            prev = word[i - 1]
            nxt = word[i + 1] if i + 1 < len(word) else ""
            if prev.islower() or prev.isdigit() or (prev.isupper() and nxt.islower()):
                parts.append(cur)
                cur = ""
        cur += ch
    if cur:
        parts.append(cur)
    return parts


def _keep(tok: str) -> bool:
    return len(tok) >= 2 and not tok.isdigit() and tok not in _STOP


def tokenize_code(text: str) -> list[str]:
    out: list[str] = []
    for m in _NAME.finditer(text):
        name = m.group(0)
        idents = [p for p in name.split(".") if p]
        for ident in idents:
            pieces = [_lower(p) for chunk in ident.split("_") if chunk
                      for p in _split_case(chunk)]
            out += [p for p in pieces if _keep(p)]
            if len(pieces) > 1:  # birleşik hal: getuserbyid, chunkbyheading
                joined = "".join(pieces)
                if _keep(joined):
                    out.append(joined)
        while idents and idents[0] in ("self", "cls"):
            idents = idents[1:]
        if len(idents) > 1:  # numpyindex.search
            out.append(".".join("".join(_lower(p) for p in i.split("_")) for i in idents))
    return out


def _doc_tokens(c: CodeChunk) -> list[str]:
    return (tokenize_code(c.symbol) * SYMBOL_WEIGHT + tokenize_code(c.path) * PATH_WEIGHT
            + tokenize_code(c.signature) + tokenize_code(c.text))


class BM25Index:
    """name verilirse config.INDEX_DIR/bm25/<name>/bm25.json altına kaydeder/yükler."""

    def __init__(self, name: str | None = None):
        self.dir = config.INDEX_DIR / "bm25" / name if name else None
        self._chunks: list[CodeChunk] | None = None
        self._bm25: BM25Okapi | None = None

    @property
    def path(self):
        return self.dir / "bm25.json" if self.dir else None

    def exists(self) -> bool:
        return bool(self.path and self.path.exists())

    def _set(self, chunks: list[CodeChunk], corpus: list[list[str]]) -> None:
        self._chunks = chunks
        self._bm25 = BM25Okapi(corpus) if chunks else None

    def build(self, chunks: list[CodeChunk]) -> None:
        corpus = [_doc_tokens(c) for c in chunks]
        self._set(list(chunks), corpus)
        if self.dir is None:
            return
        # Geçici dizine yaz, başarılıysa değiştir (vector_index ile aynı mantık)
        tmp = self.dir.with_name(self.dir.name + ".tmp")
        old = self.dir.with_name(self.dir.name + ".old")
        for d in (tmp, old):
            shutil.rmtree(d, ignore_errors=True)
        tmp.mkdir(parents=True)
        try:
            (tmp / "bm25.json").write_text(
                json.dumps({"version": 2, "chunks": [asdict(c) for c in chunks],
                            "corpus": corpus}, ensure_ascii=False), encoding="utf-8")
            if self.dir.exists():
                self.dir.rename(old)
            tmp.rename(self.dir)
        except BaseException:
            if old.exists() and not self.dir.exists():
                old.rename(self.dir)
            shutil.rmtree(tmp, ignore_errors=True)
            raise
        shutil.rmtree(old, ignore_errors=True)

    def load(self) -> None:
        data = json.loads(self.path.read_text("utf-8"))
        self._set([CodeChunk(**c) for c in data["chunks"]], data["corpus"])

    def chunks(self) -> list[CodeChunk]:
        if self._chunks is None:
            self.load()
        return self._chunks

    def search(self, query: str, k: int) -> list[tuple[CodeChunk, float]]:
        chunks = self.chunks()
        q = tokenize_code(query)
        if not chunks or not q:
            return []
        scores = self._bm25.get_scores(q)
        top = np.argsort(-scores, kind="stable")[:k]
        return [(chunks[i], float(scores[i])) for i in top if scores[i] > 0]

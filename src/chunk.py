"""CodeChunk veri modeli + dile göre yönlendirme."""
from dataclasses import dataclass


@dataclass
class CodeChunk:
    id: str            # "src/index.py::NumpyIndex.search"
    path: str          # repo köküne göre
    lang: str          # "python" | "markdown"
    kind: str          # module | class | method | function | section
    symbol: str        # "NumpyIndex.search"
    signature: str     # "def search(self, qvec, k, sources=None)"
    start_line: int    # 1-tabanlı, dahil
    end_line: int      # 1-tabanlı, dahil
    text: str          # chunk'ın ham metni (kod / bölüm)


def chunk_file(path, rel: str, text: str) -> list[CodeChunk]:
    """Dosyayı uzantısına göre parçalar. rel: repo köküne göre yol."""
    suffix = str(rel).lower().rsplit(".", 1)[-1] if "." in str(rel) else ""
    if suffix == "md":
        from .chunk_md import chunk_md
        return chunk_md(rel, text)
    if suffix == "py":
        from .chunk_py import chunk_python
        return chunk_python(rel, text)
    return []


def make_embed_text(chunk: CodeChunk) -> str:
    """Embedding'e giden metin: '# path :: symbol\\n# signature\\n<text>'."""
    return f"# {chunk.path} :: {chunk.symbol}\n# {chunk.signature}\n{chunk.text}"

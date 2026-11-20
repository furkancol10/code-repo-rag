"""Ayarlar: yollar, modeller, arama parametreleri, dışlama kalıpları."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
INDEX_DIR = DATA_DIR / "indexes"
REPOS_DIR = DATA_DIR / "repos"

EMBED_MODEL = "BAAI/bge-m3"
EMBED_DEVICE_INDEX = "auto"
EMBED_DEVICE_QUERY = "auto"
EMBED_INDEX_DTYPE = "float16"
EMBED_BATCH_SIZE = 16
PASSAGE_PREFIX: dict[str, str] = {}
QUERY_PREFIX: dict[str, str] = {}

LLM = "qwen3.5:4b"

TOP_K = 5
CANDIDATES = 30
RRF_K = 60
MAX_CHUNK_LINES = 80

EXTENSIONS = (".py", ".md")
MAX_FILE_BYTES = 300_000
EXCLUDE_DIRS = {"tests", "test", "build", "dist", ".venv", "venv", "__pycache__",
                "node_modules", ".git", ".tox", ".mypy_cache", ".pytest_cache"}
EXCLUDE_FILE_PATTERNS = ("test_*.py", "*_test.py", "*.lock", "conftest.py")

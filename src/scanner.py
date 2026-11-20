"""Repo tarayıcı: git ls-files (yoksa os.walk); yalnız .py/.md, dışlamalar uygulanır."""
import fnmatch
import os
import subprocess
from pathlib import Path

from . import config


def _git_files(root: Path) -> list[str] | None:
    if not (root / ".git").exists():
        return None
    try:
        r = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                           capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [p for p in r.stdout.decode("utf-8", "replace").split("\0") if p]


def _walk_files(root: Path) -> list[str]:
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in config.EXCLUDE_DIRS]
        for f in fns:
            out.append(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/"))
    return out


def _excluded(rel: str) -> bool:
    parts = rel.split("/")
    if any(p in config.EXCLUDE_DIRS for p in parts[:-1]):
        return True
    name = parts[-1]
    if any(fnmatch.fnmatch(name, pat) for pat in config.EXCLUDE_FILE_PATTERNS):
        return True
    return not name.lower().endswith(config.EXTENSIONS)


def _is_text(p: Path) -> bool:
    try:
        size = p.stat().st_size
        if size > config.MAX_FILE_BYTES:
            return False
        with open(p, "rb") as f:
            return b"\0" not in f.read(8192)
    except OSError:
        return False


def scan_repo(root) -> list[str]:
    """Repo köküne göre sıralı göreli yolları döner (yalnız indekslenecek .py/.md)."""
    root = Path(root)
    files = _git_files(root)
    if files is None:
        files = _walk_files(root)
    return sorted(rel for rel in files
                  if not _excluded(rel) and (root / rel).is_file() and _is_text(root / rel))

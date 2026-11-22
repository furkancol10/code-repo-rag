"""Markdown: başlıklara göre bölme (kod çitleri içindeki # başlık sayılmaz)."""
import re

from . import config
from .chunk import CodeChunk

_H = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")


def chunk_md(rel: str, text: str) -> list[CodeChunk]:
    # yalnız \r\n, \r, \n satır sonudur (splitlines \x0c, \x85 vb. de böler, satırlar kayar)
    lines = re.split(r"\r\n|\r|\n", text)
    if lines and lines[-1] == "":
        lines.pop()
    # (start_idx, level, title)
    heads, fence = [], None  # fence: (karakter, uzunluk) ya da None
    for i, ln in enumerate(lines):
        fm = _FENCE.match(ln)
        if fm:
            mark = fm.group(1)
            if fence is None:
                fence = (mark[0], len(mark))
            elif mark[0] == fence[0] and len(mark) >= fence[1] and not fm.group(2).strip():
                fence = None
            continue
        m = None if fence else _H.match(ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    bounds = [(0, 0, "")] if not heads or heads[0][0] > 0 else []
    bounds += heads
    chunks, stack, seen = [], [], {}
    for n, (s, level, title) in enumerate(bounds):
        e = bounds[n + 1][0] if n + 1 < len(bounds) else len(lines)
        if level:
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            symbol = " > ".join(t for _, t in stack)
            sig = lines[s].strip()
        else:
            symbol, sig = "(giriş)", ""
        body = lines[s:e]
        while body and not body[-1].strip():
            body.pop()
        if not any(b.strip() for b in body):
            continue
        # uzun bölümleri MAX_CHUNK_LINES'tan böl
        for part, off in enumerate(range(0, len(body), config.MAX_CHUNK_LINES)):
            seg = body[off:off + config.MAX_CHUNK_LINES]
            if not any(b.strip() for b in seg):
                continue
            base = f"{rel}::{symbol}" + (f"#{part + 1}" if part else "")
            seen[base] = seen.get(base, 0) + 1
            cid = base if seen[base] == 1 else f"{base}~{seen[base]}"
            chunks.append(CodeChunk(cid, rel, "markdown", "section", symbol, sig,
                                    s + off + 1, s + off + len(seg), "\n".join(seg)))
    return chunks

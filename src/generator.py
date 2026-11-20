"""Bağlam bloklarından Ollama ile atıflı Türkçe cevap üretir."""
import re

import ollama

from . import config

SYSTEM = (
    "Sen bir kod deposu asistanısın. Yalnızca verilen numaralı bağlam bloklarına dayanarak "
    "Türkçe cevap ver. Yalnızca bağlamda görünen ad, parametre ve davranışı kullan. "
    "Her cümleyi bağlamdaki konumla `[path:satır]` biçiminde atıfla (örn. [src/index.py:10-40]); "
    "atıfsız cümle yazma. Kod örneği uydurma. Bilgi bağlamda yoksa tam olarak "
    "\"Bu bilgi repoda yok.\" yaz, tahmin yürütme, bağlam dışı bilgi ekleme."
)

CITATION = re.compile(r"\[([^\[\]:\s]+(?:/[^\[\]:\s]+)*):(\d+)(?:-(\d+))?\]")


def build_context(hits) -> str:
    blocks = []
    for i, (chunk, _) in enumerate(hits, 1):
        blocks.append(f"[{i}] ### {chunk.path}:{chunk.start_line}-{chunk.end_line} ({chunk.symbol})\n"
                      f"```\n{chunk.text}\n```")
    return "\n\n".join(blocks)


def sources(hits) -> list[str]:
    return [f"{c.path}:{c.start_line}-{c.end_line} ({c.symbol})" for c, _ in hits]


def check_citations(answer: str, hits) -> list[str]:
    """Cevaptaki `[path:satır]` atıflarından bağlam aralıklarına uymayanları döndürür."""
    bad = []
    for m in CITATION.finditer(answer):
        path, start = m.group(1), int(m.group(2))
        end = int(m.group(3)) if m.group(3) else start
        ok = any(c.path == path and start >= c.start_line and end <= c.end_line
                 for c, _ in hits)
        if not ok and m.group(0) not in bad:
            bad.append(m.group(0))
    return bad


def answer(question: str, hits) -> str:
    if not hits:
        return "Bu bilgi repoda yok."
    user = f"Bağlam:\n\n{build_context(hits)}\n\nSoru: {question}"
    resp = ollama.chat(model=config.LLM, think=False, options={"temperature": 0},
                       messages=[{"role": "system", "content": SYSTEM},
                                 {"role": "user", "content": user}])
    return resp["message"]["content"].strip()

"""Bağlam bloklarından Ollama ile atıflı Türkçe cevap üretir."""
import ollama

from . import config

SYSTEM = (
    "Sen bir kod deposu asistanısın. Yalnızca verilen bağlam bloklarına dayanarak "
    "Türkçe cevap ver. Her iddiayı bağlamdaki konumla `[path:satır]` biçiminde atıfla "
    "(örn. [src/index.py:10-40]). Cevap bağlamda yoksa aynen \"Bu bilgi repoda yok\" de; "
    "tahmin yürütme, bağlam dışı bilgi ekleme."
)


def build_context(hits) -> str:
    blocks = []
    for chunk, _ in hits:
        blocks.append(f"### {chunk.path}:{chunk.start_line}-{chunk.end_line} ({chunk.symbol})\n"
                      f"```\n{chunk.text}\n```")
    return "\n\n".join(blocks)


def sources(hits) -> list[str]:
    return [f"{c.path}:{c.start_line}-{c.end_line} ({c.symbol})" for c, _ in hits]


def answer(question: str, hits) -> str:
    if not hits:
        return "Bu bilgi repoda yok."
    user = f"Bağlam:\n\n{build_context(hits)}\n\nSoru: {question}"
    resp = ollama.chat(model=config.LLM, think=False,
                       messages=[{"role": "system", "content": SYSTEM},
                                 {"role": "user", "content": user}])
    return resp["message"]["content"].strip()

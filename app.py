"""Streamlit arayüzü: streamlit run app.py"""
import logging
from pathlib import Path

import streamlit as st

from src import config, vector_index
from src.generator import answer
from src.hybrid import MODES, hybrid_search
from src.pipeline import (
    RepoError,
    build_index,
    indexes_exist,
    known_error_message,
    load_indexes,
    validate_repo,
)

log = logging.getLogger("kra.app")


def show_error(e: Exception, where, context: str):
    """Bilinen hata -> özel mesaj; bilinmeyen -> log + kısa uyarı."""
    msg = known_error_message(e)
    if msg is None:
        log.exception("%s: beklenmeyen hata", context)
        msg = f"{context}: beklenmeyen hata ({type(e).__name__}); ayrıntı log'da."
    where.error(msg)


@st.cache_resource(show_spinner=False)
def _get_indexes(resolved: str, index_name: str):
    return load_indexes(resolved)


def get_indexes(repo_path: str):
    resolved = str(Path(repo_path).expanduser().resolve())
    return _get_indexes(resolved, vector_index.index_name(config.EMBED_MODEL, resolved))


get_indexes.clear = _get_indexes.clear


st.set_page_config(page_title="Kod Repo Asistanı", layout="wide")
st.title("Kod Repo Asistanı")

repo = st.sidebar.text_input("Repo yolu", value=str(config.DEFAULT_REPO))
mode = st.sidebar.selectbox("Arama modu", MODES, index=MODES.index("hybrid"))
k = st.sidebar.slider("Parça sayısı", 1, 10, config.TOP_K)
use_llm = st.sidebar.checkbox("LLM cevabı üret", value=True)

if st.sidebar.button("İndeksle"):
    with st.spinner("İndeksleniyor..."):
        try:
            stats = build_index(repo)
            get_indexes.clear()
            st.sidebar.success(f"{stats['chunks']} parça, {stats['files']} dosya")
            st.sidebar.json(stats["kinds"])
            if stats.get("unreadable") or stats.get("decode_errors"):
                st.sidebar.warning(f"Okunamayan {stats['unreadable']}, UTF-8 olmayan "
                                   f"{stats['decode_errors']} dosya (ayrıntı log'da).")
        except Exception as e:
            show_error(e, st.sidebar, "İndeksleme hatası")

question = st.text_input("Soru")
repo_ok = True
if question:
    try:
        validate_repo(repo)
    except RepoError as e:
        repo_ok = False
        st.error(str(e))
if question and repo_ok:
    if not indexes_exist(repo):
        st.warning("Bu repo için indeks yok; önce 'İndeksle'ye basın.")
    else:
        vec, bm = get_indexes(repo)
        hits = hybrid_search(question, vec, bm, mode=mode, top_k=k)
        if use_llm:
            with st.spinner("Cevap üretiliyor..."):
                try:
                    st.markdown(answer(question, hits))
                except Exception as e:
                    show_error(e, st, "LLM hatası")
        st.header("Kaynaklar")
        for c, score in hits:
            label = f"{c.path}:{c.start_line}-{c.end_line}" + (f" · {c.symbol}" if c.symbol else "")
            with st.expander(label):
                st.caption(f"skor {score:.4f}")
                st.code(c.text, language=c.lang)

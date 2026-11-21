"""Streamlit arayüzü: streamlit run app.py"""
from pathlib import Path

import streamlit as st

from src import config
from src.generator import answer
from src.hybrid import MODES, hybrid_search
from src import vector_index
from src.pipeline import build_index, indexes_exist, load_indexes



@st.cache_resource(show_spinner=False)
def _get_indexes(resolved: str, index_name: str):
    return load_indexes(resolved)


def get_indexes(repo_path: str):
    resolved = str(Path(repo_path).expanduser().resolve())
    return _get_indexes(resolved, vector_index.index_name(config.EMBED_MODEL, resolved))


get_indexes.clear = _get_indexes.clear


st.set_page_config(page_title="Kod Repo Asistanı", layout="wide")
st.title("Kod Repo Asistanı")

repo = st.sidebar.text_input("Repo yolu", value=str(config.ROOT.parent / "KisiselNotArama"))
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
        except Exception as e:
            st.sidebar.error(str(e))

question = st.text_input("Soru")
if question:
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
                    st.error(f"LLM hatası (Ollama çalışıyor mu?): {e}")
        st.header("Kaynaklar")
        for c, score in hits:
            with st.expander(f"{c.path}:{c.start_line}-{c.end_line} ({c.symbol})  skor={score:.4f}"):
                st.code(c.text, language=c.lang)

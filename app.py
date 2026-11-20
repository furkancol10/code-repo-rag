"""Streamlit arayüzü: streamlit run app.py"""
import streamlit as st

from src import config
from src.generator import answer
from src.hybrid import MODES, hybrid_search
from src.pipeline import build_index, indexes_exist, load_indexes

st.set_page_config(page_title="Kod Repo Asistanı", layout="wide")
st.title("Kod Repo Asistanı")

repo = st.sidebar.text_input("Repo yolu", value=str(config.ROOT.parent / "KisiselNotArama"))
mode = st.sidebar.selectbox("Arama modu", MODES, index=MODES.index("hybrid"))
k = st.sidebar.slider("Parça sayısı", 1, 10, config.TOP_K)

if st.sidebar.button("İndeksle"):
    with st.spinner("İndeksleniyor..."):
        try:
            stats = build_index(repo)
            st.sidebar.success(f"{stats['chunks']} parça, {stats['files']} dosya")
            st.sidebar.json(stats["kinds"])
        except Exception as e:
            st.sidebar.error(str(e))

question = st.text_input("Soru")
if question:
    if not indexes_exist(repo):
        st.warning("Bu repo için indeks yok; önce 'İndeksle'ye basın.")
    else:
        vec, bm = load_indexes(repo)
        hits = hybrid_search(question, vec, bm, mode=mode, top_k=k)
        with st.spinner("Cevap üretiliyor..."):
            try:
                st.markdown(answer(question, hits))
            except Exception as e:
                st.error(f"LLM hatası (Ollama çalışıyor mu?): {e}")
        st.subheader("Kaynaklar")
        for c, score in hits:
            with st.expander(f"{c.path}:{c.start_line}-{c.end_line} ({c.symbol})  skor={score:.4f}"):
                st.code(c.text, language=c.lang)

"""Entrada local isolada: .venv/Scripts/python.exe -m streamlit run lce_modulo02.py.

Etapa 2: somente A individual. Não modifica a entrada publicada app.py.
"""

import streamlit as st
from modulo_02.interface_individual import renderizar_individual

st.set_page_config(page_title="LCE | Decisão de produção da firma", page_icon="📈", layout="wide")
with st.container(key="m02_a_root"):
    renderizar_individual()

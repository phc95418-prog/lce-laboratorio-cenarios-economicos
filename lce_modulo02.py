"""Entrada local isolada: .venv/Scripts/python.exe -m streamlit run lce_modulo02.py.

Experimento A: investigação individual e comparação. Não modifica app.py.
"""

import streamlit as st
from modulo_02.interface_individual import renderizar_individual

st.set_page_config(page_title="LCE | Decisão de produção da firma", page_icon="📈",
                   layout="wide", initial_sidebar_state="collapsed")
with st.container(key="m02_a_root"):
    renderizar_individual()

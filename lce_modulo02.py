"""Entrada local isolada: .venv/Scripts/python.exe -m streamlit run lce_modulo02.py.

Experimentos A e B. Navegação local sem modificar app.py ou o Módulo 01.
"""

import streamlit as st
from modulo_02.interface_individual import renderizar_individual

st.set_page_config(page_title="LCE | Módulo 02", page_icon="📈",
                   layout="wide", initial_sidebar_state="collapsed")
experimento=st.radio("Experimento",("Experimento A","Experimento B"),horizontal=True,key="m02_experimento")
# O Streamlit descarta widgets não renderizados. Preservar apenas o namespace
# inativo mantém preferências/buffers na navegação, sem persistência externa.
prefixo="m02_a_" if experimento=="Experimento B" else "m02_b_"
for chave in list(st.session_state):
    if chave.startswith(prefixo): st.session_state[chave]=st.session_state[chave]
with st.container(key="m02_a_root"):
    if experimento=="Experimento A": renderizar_individual()
    else:
        from modulo_02.interface_b import renderizar_b
        renderizar_b()

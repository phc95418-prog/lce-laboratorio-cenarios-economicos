"""Entrada local isolada: .venv/Scripts/python.exe -m streamlit run lce_modulo02.py.

Experimentos A e B. Navegação local sem modificar app.py ou o Módulo 01.
"""

import streamlit as st
from modulo_02.interface_individual import renderizar_individual
from modulo_02.estrutura_visual import topo, estilo_local

st.set_page_config(page_title="LCE | Módulo 02", page_icon="📈",
                   layout="wide", initial_sidebar_state="collapsed")
# Reduz comandos de desenvolvimento pela API oficial. O menu permanece para
# os temas nativos usados pela engrenagem; não se modifica config.toml.
if not st.session_state.get("_lce_integrado", False):
    st.set_option("client.toolbarMode", "viewer")
with st.container(key="m02_a_root"):
    estilo_local()
    acoes=topo()
    experimento=st.segmented_control("Experimento",("Experimento A","Experimento B"),
        default="Experimento A",required=True,key="m02_experimento",label_visibility="collapsed",
        persist_state="session" if st.session_state.get("_lce_integrado", False) else None)
    # O Streamlit descarta widgets não renderizados. Preservar apenas o namespace
    # inativo mantém preferências/buffers na navegação, sem persistência externa.
    prefixo="m02_a_" if experimento=="Experimento B" else "m02_b_"
    for chave in list(st.session_state):
        if chave.startswith(prefixo): st.session_state[chave]=st.session_state[chave]
    if experimento=="Experimento A": renderizar_individual(acoes_cabecalho=acoes)
    else:
        from modulo_02.interface_b import renderizar_b
        renderizar_b(acoes_cabecalho=acoes)

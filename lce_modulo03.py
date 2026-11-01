"""Entrypoint experimental independente do Módulo 03 e seus quatro ambientes."""

import streamlit as st

from modulo_03.interface_livre import render as render_livre
from modulo_03.interface_individual import render as render_individual
from modulo_03.interface_comparacao_consumidores import render as render_comparacao
from modulo_03.interface_experimento_b import render as render_experimento_b


PAGES = ("Exploração livre", "Experimento A · Escolha individual",
         "Experimento A · Comparação entre consumidores",
         "Experimento B · Mudanças na escolha ótima")
PREFIXES = ("m03_livre_", "m03_ai_", "m03_ac_", "m03_eb_")
RENDERERS = (render_livre, render_individual, render_comparacao,
             render_experimento_b)


def _switch_page() -> None:
    previous = st.session_state["m03_active_page"]
    new = st.session_state["m03_page"]
    old_prefix = PREFIXES[PAGES.index(previous)]
    st.session_state["m03_saved_" + previous] = {
        key: value for key, value in st.session_state.items()
        if key.startswith(old_prefix) and not key.endswith(("_graph", "_hint_button"))
    }
    for key, value in st.session_state.get("m03_saved_" + new, {}).items():
        st.session_state[key] = value
    st.session_state["m03_active_page"] = new


st.set_page_config(page_title="LCE · Módulo 03 — desenvolvimento isolado", layout="wide")
st.session_state.setdefault("m03_active_page", PAGES[0])
st.session_state.setdefault("m03_page", st.session_state["m03_active_page"])
st.radio("Ambiente do Módulo 03", PAGES, horizontal=True, key="m03_page",
         on_change=_switch_page)
RENDERERS[PAGES.index(st.session_state["m03_page"])]()

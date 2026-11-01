"""Entrypoint experimental independente do Módulo 03 (livre e A individual)."""

import streamlit as st

from modulo_03.interface_livre import render as render_livre
from modulo_03.interface_individual import render as render_individual


PAGES = ("Exploração livre", "Experimento A · Escolha individual")


def _switch_page() -> None:
    previous = st.session_state["m03_active_page"]
    new = st.session_state["m03_page"]
    old_prefix = "m03_livre_" if previous == PAGES[0] else "m03_ai_"
    new_prefix = "m03_livre_" if new == PAGES[0] else "m03_ai_"
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
if st.session_state["m03_page"] == PAGES[0]:
    render_livre()
else:
    render_individual()

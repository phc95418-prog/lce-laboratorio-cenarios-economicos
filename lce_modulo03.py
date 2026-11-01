"""Entrypoint independente e experimental da Exploração livre do Módulo 03."""

import streamlit as st

from modulo_03.interface_livre import render


st.set_page_config(page_title="LCE · Módulo 03 — Exploração livre", layout="wide")
render()

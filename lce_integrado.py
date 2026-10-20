"""Validação local conjunta: python -m streamlit run lce_integrado.py.

Os entrypoints individuais continuam executáveis sem este roteador.
"""
import streamlit as st

st.set_page_config(page_title="LCE", page_icon="📈", layout="wide")
st.session_state["_lce_integrado"] = True

modulo01 = st.Page("app.py", title="Módulo 01 — Incidência Tributária, Elasticidades e Bem-Estar", default=True)
modulo02 = st.Page("lce_modulo02.py", title="Módulo 02 — Decisões da Firma e Estruturas de Mercado")
pagina = st.navigation([modulo01, modulo02], position="hidden")
with st.container(gap="small", key="lce_navegacao_modulos"):
    st.caption("MÓDULOS DO LCE · Em uso: " + ("Módulo 01" if pagina.url_path == modulo01.url_path else "Módulo 02"))
    st.page_link(modulo01, label=modulo01.title, width="stretch")
    st.page_link(modulo02, label=modulo02.title, width="stretch")

# Escopo exclusivo do integrador. Os módulos independentes não recebem estilos
# nem navegação adicionais. A área continua acessível durante a rolagem.
st.html("""<style>
div:has(> .st-key-lce_navegacao_modulos) {
  position:sticky;top:4rem;z-index:20;
}
.st-key-lce_navegacao_modulos {
  background:var(--background-color);border:1px solid #8290a0;
  border-radius:10px;padding:.5rem .75rem;
}
.st-key-lce_navegacao_modulos a {white-space:normal;}
</style>""")

# Escolhas usam persist_state; objetos econômicos já vivem na Session State.
# Não copiar resultados de componentes V2: são buffers de eventos, não escolhas.
modulo01_ativo = pagina.url_path == modulo01.url_path
if modulo01_ativo:
    # Expanders e abas não oferecem persist_state. Guardar apenas escolhas
    # visuais atuais; nunca eventos V2, resultados ou controles econômicos.
    for chave, aberto in st.session_state.get("_lce_paineis_modulo01", {}).items():
        if chave not in st.session_state:
            st.session_state[chave] = aberto
pagina.run()
if modulo01_ativo:
    st.session_state["_lce_paineis_modulo01"] = {
        chave: st.session_state[chave] for chave in
        ("lce_abas_investigacao", "lce_analise_individual", "lce_analise_individual_dimensao",
         "lce_analise_comparativa_a", "lce_analise_comparativa_a_dimensao",
         "lce_analise_comparativa_b", "lce_analise_comparativa_b_dimensao",
         "lce_m01_sobre_modelo")
        if chave in st.session_state
    }

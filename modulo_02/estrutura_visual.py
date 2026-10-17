"""Estrutura visual compartilhável, sem estado ou cálculos econômicos."""

from contextlib import contextmanager
from pathlib import Path
import streamlit as st

ACIONADOR = st.components.v2.component(
    "lce_m02_acoes", isolate_styles=False,
    js=Path(__file__).with_name("acionador_lateral.js").read_text(encoding="utf-8"),
)

def cabecalho(modo):
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        with st.container():
            st.caption("LCE · LABORATÓRIO DE CENÁRIOS ECONÔMICOS")
            st.subheader("Módulo 02 · Decisões da Firma", anchor=False)
            st.caption("Experimento A · "+modo)
        with st.popover("Configurações", icon=":material/settings:", key="m02_configuracoes"):
            st.markdown("**Tema claro ou escuro**")
            st.write("Use o menu ⋮ no canto superior direito → Theme → Light (claro) ou Dark (escuro). O seletor nativo aplica o tema à interface inteira.")
            st.caption("Os marcadores usam forma e contorno, além da cor, nos dois temas.")
            st.caption("Aba Ações na borda esquerda. Enter abre ferramentas; Escape fecha os painéis flutuantes.")


def lateral(estado, acoes, *, complemento=None, resumo=None):
    """Ações recebidas da interface; pronta para receber as da comparação."""
    with st.sidebar:
        st.subheader("Ações do experimento", anchor=False)
        st.caption("Feche pela seta no topo para liberar a área do gráfico.")
        for rotulo, funcao, ajuda in acoes:
            st.button(rotulo, on_click=funcao, help=ajuda, width="stretch")
        if complemento:
            complemento()
        st.divider()
        st.markdown("**Estado atual**")
        if resumo:
            resumo()
        else:
            p = estado.escolha.parametros
            st.write(f"Q individual: {str(estado.escolha.q).replace('.',',')} unidades")
            st.caption(" · ".join(f"{k}={str(getattr(p,k)).replace('.',',')}" for k in ("a","b","c","s","cf")))
            st.caption(estado.perspectiva+" · "+estado.foco)


@contextmanager
def ferramenta(rotulo, icone, chave, *, variaveis=False):
    """Popover nativo: mantém abertura nos reruns e fecha por fora/Escape.

    Não usar renderização condicional pelo estado aberto: controles mantêm
    suas chaves e rascunhos mesmo quando o painel está recolhido.
    """
    with st.popover(rotulo, icon=icone, key=chave):
        with st.container(width=380, height=340 if variaveis else "content", border=False):
            yield


def estilo_local():
    ACIONADOR(key="m02_acionador_lateral", data={})
    st.html("""<style>
    body:has(.st-key-m02_a_root) [data-testid="stExpandSidebarButton"] {
      position:fixed;left:0;top:10px;width:auto;padding:0.4rem 0.6rem;
      border:1px solid currentColor;border-radius:0 8px 8px 0;gap:0.25rem;
      background:var(--background-color);font-size:0.875rem;}
    body:has(.st-key-m02_a_root) [data-testid="stSidebarCollapseButton"] {visibility:visible;}
    body:has(.st-key-m02_a_root) [data-testid="stExpandSidebarButton"]:focus-visible {
      outline:3px solid #3578c8;outline-offset:2px;}
    .st-key-m02_a_root [data-testid="stCaptionContainer"] {opacity:1;}
    .st-key-m02_a_indicadores [data-testid="stMetric"] {
      max-width:100%;border:1px solid #8290a0;
      border-radius:10px;padding:0.75rem;}
    .st-key-m02_a_indicadores [data-testid="stMetricLabel"] p {white-space:normal;}
    .st-key-m02_a_indicadores [data-testid="stMetricLabel"] {min-height:2.8rem;}
    .st-key-m02_a_indicadores [data-testid="stMetricValue"] {font-size:1.5rem;white-space:normal;}
    </style>""")

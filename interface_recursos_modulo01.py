"""Ações transversais do M01, independentes do M02 e dos cálculos econômicos."""
from pathlib import Path
import streamlit as st
from interface_analise_modulo01 import _equacao, _texto
from recursos_modulo01 import perguntas_frequentes, SOBRE_MODELO
from interface_exportacao_modulo01 import renderizar_exportacao


def renderizar_acoes(resultado, ambiente, catalogo):
    with st.container(horizontal=True, horizontal_alignment="right", gap="small", key="lce_m01_acoes"):
        with st.popover("?", help="Ajuda e dúvidas frequentes", key="lce_m01_ajuda"):
            with st.container(width=480, height=480, border=False):
                st.subheader("Ajuda · " + ambiente, anchor=False)
                for pergunta,resposta in perguntas_frequentes(ambiente):
                    with st.expander(pergunta):
                        st.markdown(_texto(resposta))
        with st.popover("Configurações", icon=":material/settings:", key="lce_m01_configuracoes"):
            with st.container(width=640, height=560, border=False):
                st.subheader("Aparência", anchor=False)
                # Registro idempotente no Runtime atual: funciona em reruns e em
                # sessões AppTest novas sem cache de componentes de outro Runtime.
                aparencia = st.components.v2.component(
                    "lce_m01_aparencia",
                    js=Path(__file__).with_name("aparencia_modulo01.js").read_text(encoding="utf-8"),
                    css=""".lce-m01-aparencia{font:inherit;color:var(--st-text-color)}
                    .lce-m01-aparencia [role=group]{display:flex;gap:.5rem;flex-wrap:wrap}
                    .lce-m01-aparencia button{font:inherit;color:inherit;background:var(--st-background-color);
                    border:1px solid currentColor;border-radius:8px;padding:.5rem .75rem;cursor:pointer}
                    .lce-m01-aparencia button:focus-visible{outline:3px solid var(--st-primary-color);outline-offset:2px}
                    .lce-m01-aparencia [role=status]{font-size:.875rem}""")
                aparencia(key="lce_m01_aparencia_controle", data={})
                st.caption("Aparência usa o tema nativo. Imposto, curvas e cenários permanecem na lateral Configurar simulação.")
                st.divider()
                renderizar_exportacao(catalogo)
                st.divider()
                with st.expander("Sobre o modelo", key="lce_m01_sobre_modelo"):
                    for titulo,textos,formulas in SOBRE_MODELO:
                        with st.expander(titulo):
                            for texto in textos:
                                st.markdown(_texto(texto))
                            for formula in formulas:
                                st.latex(_equacao(formula))
                    with st.expander("Parâmetros do mercado selecionado (consulta somente leitura)"):
                        st.caption("Valores internos do cenário vigente; esta consulta não modifica controles ou cálculos. As substituições estão na Análise econômica e matemática.")
                        st.json({k:resultado[k] for k in ("a","b","c","d","t")})
                        st.json({"Elasticidade da demanda inicial (módulo)":abs(resultado["elasticidade_demanda_0"]),
                                 "Elasticidade da oferta inicial":resultado["elasticidade_oferta_0"]})

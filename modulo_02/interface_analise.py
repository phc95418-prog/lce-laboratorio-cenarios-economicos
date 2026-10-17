"""Instrumentos opcionais de leitura; nenhuma transição econômica."""
import streamlit as st
from .analise_experimento_a import DIMENSOES, analise_individual, analise_comparativa
from .explicacoes_individual import TEXTO_PRECISAO, FORMULA_IGUALDADE, FORMULA_PROXIMIDADE


def renderizar_analise(estado, chave):
    dados = analise_comparativa(estado) if estado.comparacao is not None else analise_individual(estado)
    with st.expander("Análise econômica e matemática",key=chave("analise")):
        st.caption("Análises consolidadas ao concluir a interação; cálculos usam valores internos completos. As três dimensões são independentes e opcionais.")
        for aba, campo in zip(st.tabs(DIMENSOES),("leitura","formulas","propriedades")):
            with aba:
                for titulo,conteudo in dados:
                    if len(dados)>1:
                        st.markdown("**"+titulo+"**")
                    for item in conteudo[campo]:
                        if campo=="formulas":
                            st.markdown("**"+item[0]+"**")
                            st.latex(item[1])
                        else:
                            st.write(item)
                if campo=="propriedades":
                    with st.expander("Precisão numérica e proximidade"):
                        st.write(TEXTO_PRECISAO)
                        st.latex(FORMULA_IGUALDADE)
                        st.latex(FORMULA_PROXIMIDADE)

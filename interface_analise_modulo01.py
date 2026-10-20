"""Apresentação da análise M01; não calcula nem modifica estado econômico."""

import streamlit as st
from analise_modulo01 import Analise, DIMENSOES


def _texto(conteudo):
    # R$ pertence ao texto, não a um delimitador de matemática Markdown.
    return conteudo.replace("$", r"\$")


def _equacao(expressao):
    """Reorganiza apenas separadores existentes, sem alterar a matemática.

    Evita uma única linha larga com todas as equações e substituições.
    Não abrevia nem arredonda a representação recebida da camada analítica.
    """
    linhas = [parte.strip().rstrip(",") for parte in expressao.split(r"\quad")]
    return r"\begin{aligned}&" + r"\\&".join(linhas) + r"\end{aligned}"


def _organizar_comparacao(analise):
    """Agrupa só relações literalmente iguais, incluindo a interpretação.

    Mantém cada substituição original e o escopo de validade por mercado.
    Não recalcula resultados nem altera o contrato da camada analítica.
    """
    relacoes = {}
    mercados = {c.nome: [] for c in analise.cenarios}
    for formula in analise.estrutura:
        chave = (formula.titulo, formula.expressao, formula.interpretacao)
        if chave not in relacoes:
            relacoes[chave] = (len(relacoes) + 1, [])
        numero, nomes = relacoes[chave]
        if formula.cenario not in nomes:
            nomes.append(formula.cenario)
        mercados[formula.cenario].append((numero, formula))
    return relacoes, mercados


def _substituicoes_numeradas(formulas):
    """Uma expressão alinhada por mercado; números remetem às relações acima."""
    linhas = []
    for numero, formula in formulas:
        partes = [p.strip().rstrip(",") for p in formula.substituicao.split(r"\quad")]
        linhas.append(r"\text{[" + str(numero) + r"]}\quad " + partes[0])
        linhas.extend(partes[1:])
        # Separação visual entre relações, sem repetir títulos e explicações.
        linhas[-1] += r"\rule{0pt}{1.5em}"
    return r"\begin{aligned}&" + r"\\&".join(linhas) + r"\end{aligned}"


def _matematica_comparativa(analise):
    relacoes, mercados = _organizar_comparacao(analise)
    st.markdown(_texto(analise.propriedades[0]))
    st.subheader("Relações e condições de validade", anchor=False)
    for (titulo, expressao, interpretacao), (numero, nomes) in relacoes.items():
        st.markdown(f"**[{numero}] {titulo}**")
        if len(nomes) != len(analise.cenarios):
            st.caption("Aplicável a: " + "; ".join(nomes))
        st.latex(_equacao(expressao))
        st.markdown(_texto(interpretacao))
    st.subheader("Substituições por mercado", anchor=False)
    st.caption(_texto("Os números entre colchetes identificam as relações acima. Valores internos do cenário; preços e imposto em R$/unidade, quantidades em unidades/período e bem-estar em R$/período."))
    regimes = {
        "sem_imposto": "Imposto zero: preços válidos, sem carga tributária efetiva.",
        "interior": "Equilíbrio interior: transações e preços efetivamente negociados.",
        "proibitivo": "Sem transações: preços negociados e carga efetiva não se aplicam.",
    }
    for cenario in analise.cenarios:
        st.markdown("**" + cenario.nome + "**")
        st.caption(regimes[cenario.regime])
        st.latex(_substituicoes_numeradas(mercados[cenario.nome]))


def renderizar_analise(analise: Analise, *, chave: str):
    """Síntese visível seguida do aprofundamento inicialmente recolhido.

    Chaves separam análise individual e comparações A/B. O único estado
    escrito pelos controles é visual (abertura e dimensão selecionada).
    """
    st.subheader("Síntese econômica", anchor=False)
    st.markdown(_texto(analise.sintese))
    with st.expander("Análise econômica e matemática", expanded=False,
                     key=chave, on_change="rerun"):
        st.caption(_texto("Base da análise: " + analise.base))
        leitura, matematica, propriedades = st.tabs(DIMENSOES, key=chave + "_dimensao",
            on_change="rerun" if st.session_state.get("_lce_integrado", False) else "ignore")
        with leitura:
            for paragrafo in analise.leitura:
                st.markdown(_texto(paragrafo))
        with matematica:
            if len(analise.cenarios) > 1:
                _matematica_comparativa(analise)
            else:
                for formula in analise.estrutura:
                    if formula == analise.estrutura[0]:
                        st.subheader(formula.cenario, anchor=False)
                    st.markdown("**" + formula.titulo + "**")
                    st.latex(_equacao(formula.expressao))
                    st.caption("Substituição com os valores internos do cenário:")
                    st.latex(_equacao(formula.substituicao))
                    st.markdown(_texto(formula.interpretacao))
        with propriedades:
            for paragrafo in analise.propriedades:
                st.markdown(_texto(paragrafo))

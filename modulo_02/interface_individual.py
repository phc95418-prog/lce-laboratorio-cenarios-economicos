"""Renderização de A individual. Executar pelo ponto de entrada lce_modulo02.py."""

from pathlib import Path
import streamlit as st

from .estado_individual import (
    EstadoIndividual, FOCOS, LIMITES, PERSPECTIVAS, aplicar_evento_sessao, selecionar_otimo,
    selecionar_vista, revalidar_sessao, restaurar_experimento, alterar_zoom, chave_visualizacao,
)
from .explicacoes_individual import (
    numero, resumo_economico,
)
from .estrutura_visual import cabecalho, lateral, ferramenta, barra_ferramentas
from .graficos_individual import grafico_individual
from .modelo_firma import avaliar_firma

PASTA = Path(__file__).parent
# Registro único durante a importação, sem redefinir componente a cada rerun.
CONTROLE = st.components.v2.component(
    "lce_m02_numero",
    js=PASTA.joinpath("controles_individual.js").read_text(encoding="utf-8"),
    css=PASTA.joinpath("controles_individual.css").read_text(encoding="utf-8"),
)


def controle(estado, campo, rotulo):
    p = estado.escolha.parametros
    minimo, maximo, passo = (0, p.q_max, 0.1) if campo == "q" else LIMITES[campo]
    geracao = st.session_state.get("m02_a_geracao", 0)
    chave = f"m02_a_controle_{campo}_g{geracao}"

    def receber():
        retorno = st.session_state.get(chave)
        aplicar_evento_sessao(st.session_state, geracao, campo, retorno.get("evento") if retorno else None)

    CONTROLE(
        key=chave, on_evento_change=receber,
        data={"campo":campo, "rotulo":rotulo, "minimo":minimo, "maximo":maximo,
              "passo":passo, "valor":estado.escolha.q if campo == "q" else getattr(p,campo),
              "seq":estado.sequencias.get(campo,0), "erro":estado.erros.get(campo,"")},
    )


def renderizar_individual(*, acoes_cabecalho=None):
    if "m02_a_individual" not in st.session_state:
        st.session_state.m02_a_individual = EstadoIndividual()
    estado = revalidar_sessao(st.session_state.m02_a_individual)
    if estado.comparacao is not None:
        from .estado_comparacao import revalidar_comparacao
        estado.comparacao = revalidar_comparacao(estado.comparacao)
    st.session_state.m02_a_individual = estado
    geracao = st.session_state.get("m02_a_geracao", 0)
    def chave(nome):
        return f"m02_a_{nome}_g{geracao}"
    cabecalho("Comparação controlada" if estado.comparacao else "Investigação individual", acoes=acoes_cabecalho)
    def restaurar():
        restaurar_experimento(st.session_state)
    def fixar():
        from .estado_comparacao import fixar_referencia
        fixar_referencia(st.session_state.m02_a_individual)
    acoes = [] if estado.comparacao else [
        ("Restaurar experimento",restaurar,"Reinicia parâmetros, Q, perspectivas, ótimos e aprofundamentos."),
        ("Fixar cenário de referência",fixar,"Congela os parâmetros atuais e inicia uma comparação controlada."),
    ]

    def parametros():
        with st.expander("Parâmetros de demanda", key=chave("demanda"), on_change="rerun"):
            controle(estado,"a","a · intercepto da demanda (u.m./unidade)")
            controle(estado,"b","b · inclinação da demanda")
        with st.expander("Parâmetros de custos", key=chave("custos"), on_change="rerun"):
            controle(estado,"c","c · custo marginal inicial (u.m./unidade)")
            controle(estado,"s","s · inclinação do custo marginal")
            controle(estado,"cf","CF · custo fixo inevitável (u.m.)")

    if estado.comparacao is not None:
        from .interface_comparacao import renderizar_comparacao
        renderizar_comparacao(estado, CONTROLE, parametros)
        return

    lateral(estado,acoes)

    def mudar_vista():
        if geracao == st.session_state.get("m02_a_geracao", 0):
            selecionar_vista(st.session_state.m02_a_individual, st.session_state[chave("perspectiva")])
    def mudar_foco():
        if geracao == st.session_state.get("m02_a_geracao",0):
            atual = st.session_state.m02_a_individual
            selecionar_vista(atual,atual.perspectiva,st.session_state[chave("foco")])
    def zoom():
        alterar_zoom(st.session_state.m02_a_individual,"restaurar")

    with barra_ferramentas():
        with ferramenta("Perspectivas",":material/view_carousel:",chave("ferramenta_perspectivas")):
            st.radio("Perspectiva",PERSPECTIVAS,key=chave("perspectiva"),
                     index=PERSPECTIVAS.index(estado.perspectiva),on_change=mudar_vista)
        with ferramenta("Alterar variáveis",":material/tune:",chave("ferramenta_variaveis"),variaveis=True):
            controle(estado,"q","Quantidade produzida Q (unidades)")
            st.caption(f"Domínio atual: 0 ≤ Q ≤ {numero(estado.escolha.parametros.q_max)}. Enter ou perda de foco confirma o campo; a precisão digitada é preservada.")
            parametros()
        with ferramenta("Visualização",":material/visibility:",chave("ferramenta_visualizacao")):
            if estado.perspectiva == PERSPECTIVAS[0]:
                st.radio("Foco do gráfico",FOCOS,key=chave("foco"),on_change=mudar_foco,
                         index=FOCOS.index(estado.foco))
            else:
                st.caption("Análise Marginal apresenta RMg e CMg conjuntamente, sem seletor de foco.")
            st.button("Restaurar visualização",on_click=zoom,
                      help="Recupera a escala original desta perspectiva e foco, sem alterar a simulação.")
            st.checkbox("Ativar zoom pela roda no gráfico",key=chave("roda"),
                        help="Desativado inicialmente para preservar a rolagem da página.")
            st.caption("Arraste uma região para ampliar; Pan move. A roda, quando ativada, amplia no gráfico e continua rolando a página fora dele.")

    st.caption("Modelo teórico linear-quadrático de uma firma monopolista. Valores monetários em unidades hipotéticas (u.m.).")
    vista = chave_visualizacao(estado)
    st.plotly_chart(grafico_individual(estado),
                    key=chave(f"grafico_{vista}_{estado.escolha.parametros}_{estado.zoom.get(vista,0)}"),
                    width="stretch", config={"displayModeBar":True,"displaylogo":False,
                    "responsive":True,"locale":"pt-BR","scrollZoom":st.session_state.get(chave("roda"),False),
                    "toImageButtonOptions":{"filename":"lce-experimento-a-individual"},
                    "modeBarButtonsToRemove":["select2d","lasso2d","autoScale2d","zoomIn2d","zoomOut2d"]})
    st.caption("Arraste para ampliar; Pan desloca. Escala e roda em Visualização. Linhas por nomes e estilos; círculos indicam Q. Alterar a simulação ou a vista reinicia o enquadramento.")
    with st.container(horizontal=True):
        def mudar_otimos():
            if geracao == st.session_state.get("m02_a_geracao", 0):
                st.session_state.m02_a_individual.mostrar_otimos = st.session_state[chave("otimos")]
        def ir_ao_otimo():
            selecionar_otimo(st.session_state.m02_a_individual)
        st.checkbox("Mostrar pontos ótimos",key=chave("otimos"),value=estado.mostrar_otimos,
                    on_change=mudar_otimos)
        st.button("Ir para lucro máximo",on_click=ir_ao_otimo)
    if estado.mostrar_otimos:
        r = avaliar_firma(estado.escolha.q, estado.escolha.parametros)
        st.caption(f"Q_R={numero(r.otimos.q_receita)} · Q_M={numero(r.otimos.q_lucro)}. Receita máxima e lucro máximo são critérios distintos. Guias de quantidade não representam ótimos de custo.")

    if estado.aviso_dominio:
        st.warning("Atenção: " + estado.aviso_dominio, icon="⚠️")
        def dispensar_aviso():
            st.session_state.m02_a_individual.aviso_dominio = ""
        st.button("Dispensar aviso de ajuste", on_click=dispensar_aviso)
    r = avaliar_firma(estado.escolha.q, estado.escolha.parametros)
    c = r.curvas
    indicadores = [("Quantidade (unidades)",c.q),("Preço da demanda (u.m./unidade)",c.preco_demanda)]
    if estado.perspectiva == "Resultados Totais":
        indicadores += [("Receita total (u.m.)",c.receita_total),("Custo total (u.m.)",r.custo_total),("Lucro (u.m.)",r.lucro)]
    else:
        indicadores += [("Receita marginal (u.m./unidade)",c.receita_marginal),("Custo marginal (u.m./unidade)",c.custo_marginal),("RMg − CMg (u.m./unidade)",r.diferenca_marginal)]
    with st.container(key="m02_a_indicadores", horizontal=True):
        for rotulo, valor in indicadores:
            st.metric(rotulo, numero(valor), width=200)
    with st.container(key="m02_a_sintese"):
        st.info("Informação econômica: " + resumo_economico(estado), icon="ℹ️")
    if estado.em_interacao:
        st.html('<p role="status" aria-live="polite">Atualizando gráfico e indicadores; síntese ao terminar.</p>')
    from .interface_analise import renderizar_analise
    renderizar_analise(estado,chave)

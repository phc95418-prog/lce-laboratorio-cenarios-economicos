"""Renderização de A individual. Executar pelo ponto de entrada lce_modulo02.py."""

from pathlib import Path
import streamlit as st

from .estado_individual import (
    EstadoIndividual, FOCOS, LIMITES, PERSPECTIVAS, aplicar_evento_sessao, selecionar_otimo,
    selecionar_vista, revalidar_sessao, restaurar_experimento, alterar_zoom, chave_visualizacao,
)
from .explicacoes_individual import (
    IDEIAS, condicoes_excepcionais, explicacao, numero, sintese, resumo_economico,
    GRUPOS_MATEMATICOS, FORMULA_IGUALDADE, FORMULA_PROXIMIDADE, TEXTO_PRECISAO,
)
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


def renderizar_individual():
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
    st.caption("LABORATÓRIO DE CENÁRIOS ECONÔMICOS · MÓDULO 02")
    st.title("Decisão de produção da firma")
    st.write("Experimento A · "+("Comparação controlada" if estado.comparacao else "Investigação individual"))
    st.caption("Modelo teórico linear-quadrático de uma firma monopolista. Valores monetários em unidades hipotéticas (u.m.).")
    if estado.comparacao is None:
        st.button("Restaurar experimento", key="m02_restaurar_a",
                  on_click=restaurar_experimento, args=(st.session_state,),
                  help="Reinicia parâmetros, quantidade, perspectivas, zoom e aprofundamentos.")
        def fixar():
            from .estado_comparacao import fixar_referencia
            fixar_referencia(st.session_state.m02_a_individual)
        st.button("Fixar cenário de referência",on_click=fixar)

    # Escopo local deste ponto de entrada, sem alterar o Módulo 01.
    st.html("""<style>
    .st-key-m02_a_root [data-testid="stCaptionContainer"] {opacity:1;}
    .st-key-m02_a_indicadores [data-testid="stMetric"] {
      max-width:100%;border:1px solid #8290a0;
      border-radius:10px;padding:0.75rem;}
    .st-key-m02_a_indicadores [data-testid="stMetricLabel"] p {white-space:normal;}
    .st-key-m02_a_indicadores [data-testid="stMetricLabel"] {min-height:2.8rem;}
    .st-key-m02_a_indicadores [data-testid="stMetricValue"] {font-size:1.5rem;white-space:normal;}
    </style>""")

    with st.expander("Parâmetros de demanda", key=chave("demanda"), on_change="rerun"):
        controle(estado,"a","a · intercepto da demanda (u.m./unidade)")
        controle(estado,"b","b · inclinação da demanda")
    with st.expander("Parâmetros de custos", key=chave("custos"), on_change="rerun"):
        controle(estado,"c","c · custo marginal inicial (u.m./unidade)")
        controle(estado,"s","s · inclinação do custo marginal")
        controle(estado,"cf","CF · custo fixo inevitável (u.m.)")

    if estado.comparacao is not None:
        from .interface_comparacao import renderizar_comparacao
        renderizar_comparacao(estado, CONTROLE)
        return

    def mudar_vista():
        if geracao == st.session_state.get("m02_a_geracao", 0):
            selecionar_vista(st.session_state.m02_a_individual, st.session_state[chave("perspectiva")])

    st.radio("Perspectiva", PERSPECTIVAS, horizontal=True, key=chave("perspectiva"),
             index=PERSPECTIVAS.index(estado.perspectiva), on_change=mudar_vista)
    if estado.perspectiva == PERSPECTIVAS[0]:
        def mudar_foco():
            if geracao != st.session_state.get("m02_a_geracao", 0):
                return
            atual = st.session_state.m02_a_individual
            selecionar_vista(atual, atual.perspectiva, st.session_state[chave("foco")])
        st.radio("Foco do gráfico", FOCOS, horizontal=True, key=chave("foco"), on_change=mudar_foco,
                 index=FOCOS.index(estado.foco))

    def zoom(acao):
        alterar_zoom(st.session_state.m02_a_individual, acao)

    st.button("Restaurar visualização", on_click=zoom, args=("restaurar",),
              help="Recupera a escala original desta perspectiva e foco, sem alterar a simulação.")
    roda = st.checkbox("Ativar zoom pela roda no gráfico", key=chave("roda"),
                       help="Desativado inicialmente para preservar a rolagem da página. Fora do gráfico, a roda continua rolando a página.")
    st.caption("Arraste uma região para ampliá-la. Na barra do gráfico, use Pan para mover e Zoom para selecionar outra região. Restaurar visualização também funciona por teclado. Esses gestos não alteram Q.")
    # Streamlit 1.65 identifica a figura também pelo conteúdo/configuração.
    # Cada vista começa com sua escala; dados novos remontam o gráfico. A
    # revisão permite restaurar mesmo quando os dados não mudaram.
    vista = chave_visualizacao(estado)
    st.plotly_chart(grafico_individual(estado),
                    key=chave(f"grafico_{vista}_{estado.escolha.parametros}_{estado.zoom.get(vista,0)}"),
                    width="stretch", config={"displayModeBar":True,"displaylogo":False,
                    "responsive":True,"locale":"pt-BR","scrollZoom":roda,
                    "modeBarButtonsToRemove":["select2d","lasso2d","autoScale2d","zoomIn2d","zoomOut2d"]})
    st.caption("Linhas identificadas por nomes e estilos; os círculos indicam a quantidade escolhida. Os valores correspondentes estão abaixo, sem depender de hover. Alterar a simulação, a perspectiva ou o foco reinicia o enquadramento próprio da vista.")
    controle(estado,"q","Quantidade produzida Q (unidades)")
    st.caption(f"Domínio atual: 0 ≤ Q ≤ {numero(estado.escolha.parametros.q_max)}. Enter ou perda de foco confirma o campo; a precisão digitada é preservada.")
    with st.container(horizontal=True):
        def mudar_otimos():
            if geracao == st.session_state.get("m02_a_geracao", 0):
                st.session_state.m02_a_individual.mostrar_otimos = st.session_state[chave("otimos")]
        def ir_ao_otimo():
            selecionar_otimo(st.session_state.m02_a_individual)
        st.checkbox("Mostrar pontos ótimos", key=chave("otimos"), value=estado.mostrar_otimos,
                    on_change=mudar_otimos)
        st.button("Ir para lucro máximo", on_click=ir_ao_otimo)
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
    with st.expander("Compreenda o mecanismo · opcional", key=chave("explicacao"), on_change="rerun"):
        avisos = condicoes_excepcionais(estado.escolha)
        if avisos:
            st.markdown("**Condições econômicas atuais**")
            for aviso in avisos:
                st.write("• " + aviso)
        if estado.aviso_dominio:
            st.write("A ampliação posterior do domínio não restaura uma quantidade descartada pelo ajuste.")
        st.markdown("**Leitura da última interação concluída**")
        st.write(sintese(estado))
        nivel = st.radio("Nível de explicação", ("Essencial","Econômica","Matemática"), horizontal=True, key=chave("nivel"))
        st.write(explicacao(estado.confirmado, nivel))
        if nivel == "Matemática":
            for titulo, formula in GRUPOS_MATEMATICOS:
                st.markdown(f"**{titulo}**")
                st.latex(formula)
            st.caption("A igualdade marginal na origem é uma condição de fronteira, não um ótimo interior.")
            with st.expander("Precisão numérica e proximidade · detalhes", key=chave("precisao"), on_change="rerun"):
                st.write(TEXTO_PRECISAO)
                st.latex(FORMULA_IGUALDADE)
                st.latex(FORMULA_PROXIMIDADE)
    with st.expander("Ideias para investigar · opcional", key=chave("ideias"), on_change="rerun"):
        for ideia in IDEIAS:
            st.write("• " + ideia)

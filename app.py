"""Interface do Laboratorio de Cenarios Economicos (LCE), modulo 01.

Inicie com: python -m streamlit run app.py
Todos os resultados economicos sao calculados por modelo_mercado.py.
"""

import streamlit as st

# A execução individual mantém a política original de descarte dos widgets.
_PERSISTENCIA_MODULOS = "session" if st.session_state.get("_lce_integrado", False) else None

from modelo_mercado import simular_mercado, parametros_por_elasticidades
from experimentos import (
    cenarios_experimento_a, cenarios_experimento_b, resultados_cenarios,
)
from visualizacoes import (
    grafico_mercado, grafico_composicao_excedente,
    grafico_reparticao, grafico_distorcao,
)
from analise_modulo01 import (
    analisar_exploracao, analisar_experimento_a, analisar_experimento_b,
)
from interface_analise_modulo01 import renderizar_analise
from interface_recursos_modulo01 import renderizar_acoes
from exportacao_modulo01 import catalogo_exportacao


st.set_page_config(
    page_title="LCE | Laboratório de Cenários Econômicos",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.container(key="lce_m01_root"):
    st.markdown("""
    <style>
      body:has(.st-key-lce_m01_root) .block-container {padding-top: 3.5rem; padding-bottom: 3rem; max-width: 1380px;}
      .st-key-lce_m01_root .lce-eyebrow {font-size:0.80rem;font-weight:700;letter-spacing:0.12em;color:var(--text-color);}
      .st-key-lce_m01_root .lce-subtitle {max-width:960px; color:var(--text-color); font-size:1.02rem; line-height:1.55;}
      .st-key-lce_m01_root .lce-note {background:rgba(100,116,139,0.065);padding:1rem 1.15rem;
         border-left:3px solid #7692B7;border-radius:0.4rem;line-height:1.55;}
      .st-key-lce_m01_root .lce-caption {font-size:0.88rem;color:var(--text-color);}
      .st-key-lce_m01_root div[data-testid="stMetric"] {border:1px solid rgba(128,145,167,0.22);
         border-radius:12px; padding:0.8rem 0.85rem; background:rgba(140,156,177,0.035);}
      .st-key-lce_m01_root div[data-testid="stMetricValue"] {font-size:1.55rem;}
      /* Rótulos dos pontos seguem o tema, sem alterar dados ou geometria. */
      .st-key-lce_m01_root .textpoint text {fill:var(--text-color);}
      /* Os cartões devem caber na área disponível, inclusive com a lateral aberta. */
      .st-key-lce_indicadores [data-testid="stColumn"] {
         min-width:min(100%, 9.5rem);}
      .st-key-lce_bem_estar [data-testid="stColumn"] {
         min-width:min(100%, 12rem);}
      :is(.st-key-lce_indicadores, .st-key-lce_bem_estar)
         [data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"],
      :is(.st-key-lce_indicadores, .st-key-lce_bem_estar)
         [data-testid="stMetricLabel"] p {white-space:normal;}
      .st-key-lce_m01_root div[data-testid="stTabs"] {margin-top:0.4rem;}
    </style>
    """, unsafe_allow_html=True)


    def numero(valor, casas=2):
        """Formata um valor para leitura em portugues (sem alterar os calculos)."""
        if valor is None:
            return "—"
        return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


    def moeda(valor):
        return "—" if valor is None else f"R$ {numero(valor)}"


    def percentual(fracao):
        return "—" if fracao is None else f"{numero(100 * fracao, 1)}%"


    def entradas_livres():
        modo = st.radio(
            "Forma de entrada",
            ["Exploratório · elasticidades", "Avançado · equações"],
            help="Os dois modos utilizam exatamente o mesmo modelo econômico.",
            key="lce_forma_entrada", persist_state=_PERSISTENCIA_MODULOS,
        )
        if modo.startswith("Exploratório"):
            st.caption("Elasticidades avaliadas no equilíbrio inicial.")
            p0 = st.number_input("Preço inicial (R$/un.)", min_value=0.01, value=60.0, step=5.0, key="lce_preco_inicial", persist_state=_PERSISTENCIA_MODULOS)
            q0 = st.number_input("Quantidade inicial (un./período)", min_value=0.01, value=40.0, step=5.0, key="lce_quantidade_inicial", persist_state=_PERSISTENCIA_MODULOS)
            ed = st.number_input("Elasticidade da demanda · módulo", min_value=0.01,
                                 value=1.5, step=0.1, format="%.2f", key="lce_elasticidade_demanda", persist_state=_PERSISTENCIA_MODULOS)
            es = st.number_input("Elasticidade da oferta", min_value=1.0,
                                 value=1.5, step=0.1, format="%.2f", key="lce_elasticidade_oferta", persist_state=_PERSISTENCIA_MODULOS)
            t = st.number_input("Imposto (R$/un.)", min_value=0.0, value=20.0, step=1.0, key="lce_imposto_livre", persist_state=_PERSISTENCIA_MODULOS)
            parametros = parametros_por_elasticidades(p0, q0, ed, es, t)
        else:
            st.caption("Curvas inversas: Pᴰ=a−bQ e Pˢ=c+dQ.")
            a = st.number_input("a · intercepto da demanda", min_value=0.0, value=100.0, step=5.0, key="lce_demanda_a", persist_state=_PERSISTENCIA_MODULOS)
            b = st.number_input("b · inclinação da demanda", min_value=0.01, value=1.0, step=0.1, key="lce_demanda_b", persist_state=_PERSISTENCIA_MODULOS)
            c = st.number_input("c · intercepto da oferta", min_value=0.0, value=20.0, step=5.0, key="lce_oferta_c", persist_state=_PERSISTENCIA_MODULOS)
            d = st.number_input("d · inclinação da oferta", min_value=0.01, value=1.0, step=0.1, key="lce_oferta_d", persist_state=_PERSISTENCIA_MODULOS)
            t = st.number_input("Imposto (R$/un.)", min_value=0.0, value=20.0, step=1.0, key="lce_imposto_livre", persist_state=_PERSISTENCIA_MODULOS)
            parametros = dict(a=a, b=b, c=c, d=d, t=t)
        return parametros


    st.markdown('<div class="lce-eyebrow">LCE / LABORATÓRIO DE CENÁRIOS ECONÔMICOS</div>',
                unsafe_allow_html=True)
    st.title("Quem realmente paga um imposto?")
    st.markdown(
        '<div class="lce-subtitle">Modifique as características do mercado, compare cenários e investigue '
        'como um imposto específico altera os preços, a quantidade, a arrecadação e o bem-estar. '
        '<strong>Simulação teórica — não é previsão econômica.</strong></div>',
        unsafe_allow_html=True,
    )

    acoes_aplicacao = st.container(key="lce_m01_acoes_aplicacao")

    with st.sidebar:
        st.markdown("## Configurar simulação")
        experiencia = st.radio(
            "Investigar",
            ["Exploração livre", "Experimento A", "Experimento B"],
            format_func=lambda s: {
                "Exploração livre": "Exploração livre",
                "Experimento A": "A · Quem suporta o imposto?",
                "Experimento B": "B · Quanto o imposto distorce?",
            }[s],
            key="lce_ambiente", persist_state=_PERSISTENCIA_MODULOS,
        )
        st.divider()
        try:
            if experiencia == "Exploração livre":
                parametros = entradas_livres()
                cenarios = None
                destaque = None
            else:
                st.caption("Cenários hipotéticos de ensino.")
                if experiencia == "Experimento A":
                    st.info(
                        "Mesmo equilíbrio inicial e mesmo imposto; comparamos "
                        "como a carga tributária se distribui entre consumidores e produtores."
                    )
                    limite_imposto = 80.0
                    funcao_cenarios = cenarios_experimento_a
                else:
                    st.info(
                        "Mesmo equilíbrio inicial e mesmo imposto; comparamos "
                        "como a sensibilidade ao preço altera as trocas."
                    )
                    limite_imposto = 40.0
                    funcao_cenarios = cenarios_experimento_b
                imposto = st.slider(
                    "Imposto comum a todos os cenários (R$/un.)",
                    min_value=0.0, max_value=limite_imposto,
                    value=20.0, step=1.0,
                    help="O mesmo imposto é aplicado a todos, para permitir comparação.",
                    key="lce_imposto_comum_a" if experiencia == "Experimento A" else "lce_imposto_comum_b",
                    persist_state=_PERSISTENCIA_MODULOS,
                )
                cenarios = resultados_cenarios(funcao_cenarios(imposto))
                destaque = st.selectbox(
                    "Cenário em destaque", [nome for nome, _ in cenarios],
                    key="lce_cenario_destaque_a" if experiencia == "Experimento A" else "lce_cenario_destaque_b",
                    persist_state=_PERSISTENCIA_MODULOS,
                )
                parametros = next(dict(a=r["a"], b=r["b"], c=r["c"], d=r["d"], t=r["t"])
                                  for nome, r in cenarios if nome == destaque)
            resultado = simular_mercado(**parametros)
        except (ValueError, OverflowError, ZeroDivisionError) as erro:
            st.error(f"Não foi possível calcular essa configuração: {erro}")
            st.stop()

        st.divider()
        st.caption("Modelo: equilíbrio parcial competitivo; curvas lineares; ausência de externalidades; imposto por unidade.")
        st.caption("Projeto independente de Economia · interface v1.2 · arquitetura matemática v1.1")

    # Uma construção por figura: tela e exportação recebem os mesmos dados.
    figuras = {"E1":grafico_mercado(resultado, cenarios),
               "E2":grafico_composicao_excedente(resultado)}
    if experiencia == "Experimento A":
        figuras["E3"] = grafico_reparticao(cenarios)
    elif experiencia == "Experimento B":
        figuras["E4"] = grafico_distorcao(cenarios)
    catalogo = catalogo_exportacao(resultado, experiencia, destaque, cenarios, figuras)
    with acoes_aplicacao:
        renderizar_acoes(resultado, experiencia, catalogo)

    st.markdown("\n")
    aba_simulacao, aba_comparacao = st.tabs(["Simulação", "Comparar cenários"],
        key="lce_abas_investigacao" if _PERSISTENCIA_MODULOS else None,
        on_change="rerun" if _PERSISTENCIA_MODULOS else "ignore")

    with aba_simulacao:
        coluna_grafico, coluna_indicadores = st.columns([1.65, 1], gap="large")
        with coluna_grafico:
            st.subheader("Equilíbrio de mercado")
            with st.container(key="lce_m01_export_e1"):
                st.plotly_chart(figuras["E1"], use_container_width=True,
                                config={"displaylogo": False, "responsive": True})
            if resultado["t"] == 0:
                st.caption("Sem imposto: o gráfico mostra somente o equilíbrio inicial, sem áreas tributárias.")
            elif resultado["ha_transacoes"]:
                st.caption("A área lilás representa a arrecadação; a área laranja, o peso morto. Q₀ e Qₜ indicam as quantidades antes e depois do imposto.")
            else:
                st.caption("Sem transações: não há arrecadação nem preços efetivamente negociados. A área laranja representa toda a perda de excedente.")
        with coluna_indicadores:
            st.subheader("Indicadores")
            with st.container(key="lce_indicadores"):
                c1, c2 = st.columns(2)
                c1.metric("Quantidade antes", numero(resultado["q0"]))
                c2.metric("Quantidade depois", numero(resultado["qt"]),
                          delta=f"{numero(-resultado['reducao_quantidade'])} un.", delta_color="off")
                c3, c4 = st.columns(2)
                c3.metric("Preço inicial", moeda(resultado["p0"]))
                c4.metric("Preço consumidor", moeda(resultado["pc"]))
                c5, c6 = st.columns(2)
                c5.metric("Preço produtor", moeda(resultado["pp"]))
                c6.metric("Imposto/unidade", moeda(resultado["t"]))
            if resultado["t"] == 0:
                st.caption("Sem tributação efetiva: não existe carga de imposto a distribuir.")
            elif not resultado["ha_transacoes"]:
                st.warning("Sem transações. Os preços pós-imposto não são preços efetivamente negociados.")
            else:
                st.caption(
                    "Parcela por unidade do imposto: consumidor "
                    f"**{percentual(resultado['fracao_consumidor_efetiva'])}** · produtor "
                    f"**{percentual(resultado['fracao_produtor_efetiva'])}**."
                )

        st.markdown("### Arrecadação e bem-estar")
        with st.container(key="lce_bem_estar"):
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Arrecadação", moeda(resultado["arrecadacao"]))
            m2.metric("Peso morto", moeda(resultado["peso_morto"]))
            m3.metric("Excedente do consumidor", moeda(resultado["ec"]))
            m4.metric("Excedente do produtor", moeda(resultado["ep"]))

        with st.container(key="lce_m01_export_e2"):
            st.plotly_chart(figuras["E2"], use_container_width=True,
                            config={"displaylogo": False})
        st.caption("O excedente total com imposto soma excedentes privados e arrecadação pública, uma única vez.")
        renderizar_analise(
            analisar_exploracao(resultado, nome=destaque or "Mercado vigente"),
            chave="lce_analise_individual",
        )

    with aba_comparacao:
        if cenarios is None:
            st.info(
                "Selecione **Experimento A** ou **Experimento B** no painel lateral para "
                "comparar cenários mantendo hipóteses de controle explícitas."
            )
        else:
            if experiencia == "Experimento A":
                st.subheader("Experimento A · Quem suporta o imposto?")
                st.markdown(
                    "Três mercados partem do **mesmo equilíbrio inicial** e recebem "
                    "o **mesmo imposto**. A comparação mantém a soma das inclinações "
                    "das curvas inversas constante."
                )
                # Legenda ocupa a mesma posição em todos os regimes tributários.
                if resultado["t"] == 0:
                    aviso_tributo = (
                        "Imposto zero: as barras representam repasses potenciais; "
                        "não há carga tributária efetivamente paga."
                    )
                elif not resultado["ha_transacoes"]:
                    aviso_tributo = (
                        "Sem transações: as barras representam repasses potenciais, "
                        "não pagamentos realizados."
                    )
                else:
                    aviso_tributo = (
                        "Com imposto positivo e transações, as barras mostram "
                        "as parcelas do imposto suportadas por cada lado do mercado."
                    )
                st.caption(aviso_tributo)
                with st.container(key="lce_m01_export_e3"):
                    st.plotly_chart(figuras["E3"], use_container_width=True,
                                    config={"displaylogo": False})
            else:
                st.subheader("Experimento B · Quanto o imposto distorce o mercado?")
                st.markdown(
                    "Três mercados partem do **mesmo equilíbrio inicial** e recebem "
                    "o **mesmo imposto**. As inclinações são iguais entre oferta e demanda "
                    "dentro de cada mercado, mas sua magnitude varia entre os cenários."
                )
                if any(not r["ha_transacoes"] for _, r in cenarios):
                    st.warning("Pelo menos um cenário chegou ao imposto proibitivo: nele não existem preços de transação nem repartição efetiva do tributo.")
                with st.container(key="lce_m01_export_e4"):
                    st.plotly_chart(figuras["E4"], use_container_width=True,
                                    config={"displaylogo": False})
            tabela = []
            for nome, r in cenarios:
                tabela.append({
                    "Cenário": nome,
                    "Q₀": numero(r["q0"]),
                    "Q após imposto": numero(r["qt"]),
                    "|ε demanda| (inicial)": numero(abs(r["elasticidade_demanda_0"]), 2),
                    "ε oferta (inicial)": numero(r["elasticidade_oferta_0"], 2),
                    "P consumidor": moeda(r["pc"]),
                    "P produtor": moeda(r["pp"]),
                    "Consumidor (repasse)*": percentual(r["fracao_consumidor_efetiva"]),
                    "Arrecadação": moeda(r["arrecadacao"]),
                    "Peso morto": moeda(r["peso_morto"]),
                })
            st.dataframe(tabela, use_container_width=True, hide_index=True)
            st.caption("Elasticidades pontuais avaliadas no equilíbrio inicial (não constantes ao longo das curvas lineares). * Parcela efetiva por unidade somente com imposto positivo e transações; traço = não aplicável.")
            st.caption("Alterações nas curvas são experimentos teóricos controlados; não equivalem a estimativas empíricas de efeitos causais.")
            analise_comparativa = (
                analisar_experimento_a(cenarios) if experiencia == "Experimento A"
                else analisar_experimento_b(cenarios)
            )
            renderizar_analise(
                analise_comparativa,
                chave="lce_analise_comparativa_a" if experiencia == "Experimento A" else "lce_analise_comparativa_b",
            )

    st.divider()
    st.caption("LCE · Laboratório de Cenários Econômicos — projeto acadêmico independente · Módulo 01, interface v1.2")

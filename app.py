"""Interface do Laboratorio de Cenarios Economicos (LCE), modulo 01.

Inicie com: python -m streamlit run app.py
Todos os resultados economicos sao calculados por modelo_mercado.py.
"""

import streamlit as st

from modelo_mercado import simular_mercado, parametros_por_elasticidades
from experimentos import (
    cenarios_experimento_a, cenarios_experimento_b, resultados_cenarios,
)
from visualizacoes import (
    grafico_mercado, grafico_composicao_excedente,
    grafico_reparticao, grafico_distorcao,
)
from investigacao_a import QUESTOES, NIVEIS, sugestao, explicacao as explicar_questao, formula, sintese


st.set_page_config(
    page_title="LCE | Laboratório de Cenários Econômicos",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1380px;}
  .lce-eyebrow {font-size:0.80rem;font-weight:700;letter-spacing:0.12em;color:#68809B;}
  .lce-subtitle {max-width:960px; color:#64748B; font-size:1.02rem; line-height:1.55;}
  .lce-note {background:rgba(100,116,139,0.065);padding:1rem 1.15rem;
     border-left:3px solid #7692B7;border-radius:0.4rem;line-height:1.55;}
  .lce-caption {font-size:0.88rem;color:#687587;}
  div[data-testid="stMetric"] {border:1px solid rgba(128,145,167,0.22);
     border-radius:12px; padding:0.8rem 0.85rem; background:rgba(140,156,177,0.035);}
  div[data-testid="stMetricValue"] {font-size:1.55rem;}
  div[data-testid="stTabs"] {margin-top:0.4rem;}
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


def explicacao(resultado, experimento):
    """Interpreta somente resultados do nucleo, segundo as hipoteses do modelo."""
    t, q0, qt = resultado["t"], resultado["q0"], resultado["qt"]
    if t == 0:
        return (
            "O imposto é zero. A quantidade permanece no equilíbrio inicial e "
            "não há arrecadação nem perda de eficiência. Os percentuais de "
            "repasse representam somente como um pequeno imposto *poderia* "
            "ser distribuído neste modelo; não há carga efetivamente paga."
        )
    if not resultado["ha_transacoes"]:
        return (
            f"Com imposto de {moeda(t)} por unidade, o mercado deixa de "
            f"transacionar: a quantidade cai de {numero(q0)} para zero. "
            "Não existe arrecadação e não há preços efetivos de compra ou venda. "
            f"O peso morto corresponde ao excedente inicial ({moeda(resultado['et0'])})."
        )

    parte_consumidor = 100 * resultado["fracao_consumidor_efetiva"]
    lado = ("os consumidores" if parte_consumidor > 50 else
            "os produtores" if parte_consumidor < 50 else "os dois lados igualmente")
    mudanca = f"A quantidade cai de {numero(q0)} para {numero(qt)} unidades."
    incidencia = (
        f" O consumidor passa a pagar {moeda(resultado['pc'])} e o produtor "
        f"recebe {moeda(resultado['pp'])} por unidade. "
        f"Nesta configuração, {lado} suportam a maior parte da cunha "
        f"tributária por unidade (consumidores: {percentual(resultado['fracao_consumidor_efetiva'])}; "
        f"produtores: {percentual(resultado['fracao_produtor_efetiva'])})."
    )
    # Evitar erro de concordancia no caso de partilha igual.
    if parte_consumidor == 50:
        incidencia = (
            f" O consumidor paga {moeda(resultado['pc'])} e o produtor recebe "
            f"{moeda(resultado['pp'])} por unidade. A cunha é dividida igualmente "
            "entre os dois lados (50% para cada um)."
        )
    welfare = (
        f" A arrecadação é {moeda(resultado['arrecadacao'])} e a perda de "
        f"eficiência é {moeda(resultado['peso_morto'])}; são medidas diferentes."
    )
    if experimento == "Experimento A":
        if parte_consumidor == 50:
            mecanismo = (
                "Como a oferta e a demanda têm a mesma elasticidade inicial, "
                "os dois lados dividem igualmente o imposto."
            )
        elif parte_consumidor > 50:
            mecanismo = (
                "A demanda é relativamente menos elástica, então os consumidores "
                "suportam uma parcela maior do imposto."
            )
        else:
            mecanismo = (
                "A oferta é relativamente menos elástica, então os produtores "
                "suportam uma parcela maior do imposto."
            )
        finalidade = (
            f" {mecanismo} Nos três cenários A, a soma das inclinações das "
            "curvas inversas é mantida constante: a redução da quantidade "
            "e o peso morto são iguais."
        )
    elif experimento == "Experimento B":
        finalidade = (
            " Ao comparar os cenários B, vemos que elasticidades iniciais "
            "maiores tornam a quantidade mais sensível ao mesmo imposto, "
            "aumentando a redução das trocas e o peso morto."
        )
    else:
        finalidade = " Os resultados decorrem das curvas e hipóteses que você definiu."
    return mudanca + incidencia + welfare + finalidade


def entradas_livres():
    modo = st.radio(
        "Forma de entrada",
        ["Exploratório · elasticidades", "Avançado · equações"],
        help="Os dois modos utilizam exatamente o mesmo modelo econômico.",
    )
    if modo.startswith("Exploratório"):
        st.caption("Elasticidades avaliadas no equilíbrio inicial.")
        p0 = st.number_input("Preço inicial (R$/un.)", min_value=0.01, value=60.0, step=5.0)
        q0 = st.number_input("Quantidade inicial (un./período)", min_value=0.01, value=40.0, step=5.0)
        ed = st.number_input("Elasticidade da demanda · módulo", min_value=0.01,
                             value=1.5, step=0.1, format="%.2f")
        es = st.number_input("Elasticidade da oferta", min_value=1.0,
                             value=1.5, step=0.1, format="%.2f")
        t = st.number_input("Imposto (R$/un.)", min_value=0.0, value=20.0, step=1.0)
        parametros = parametros_por_elasticidades(p0, q0, ed, es, t)
    else:
        st.caption("Curvas inversas: Pᴰ=a−bQ e Pˢ=c+dQ.")
        a = st.number_input("a · intercepto da demanda", min_value=0.0, value=100.0, step=5.0)
        b = st.number_input("b · inclinação da demanda", min_value=0.01, value=1.0, step=0.1)
        c = st.number_input("c · intercepto da oferta", min_value=0.0, value=20.0, step=5.0)
        d = st.number_input("d · inclinação da oferta", min_value=0.01, value=1.0, step=0.1)
        t = st.number_input("Imposto (R$/un.)", min_value=0.0, value=20.0, step=1.0)
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
            )
            cenarios = resultados_cenarios(funcao_cenarios(imposto))
            destaque = st.selectbox(
                "Cenário em destaque", [nome for nome, _ in cenarios],
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

st.markdown("\n")
aba_simulacao, aba_comparacao, aba_metodo = st.tabs(
    ["Simulação", "Comparar cenários", "Modelo e hipóteses"]
)

with aba_simulacao:
    coluna_grafico, coluna_indicadores = st.columns([1.65, 1], gap="large")
    with coluna_grafico:
        st.subheader("Equilíbrio de mercado")
        st.plotly_chart(grafico_mercado(resultado, cenarios), use_container_width=True,
                        config={"displaylogo": False, "responsive": True})
        if resultado["t"] == 0:
            st.caption("Sem imposto: o gráfico mostra somente o equilíbrio inicial, sem áreas tributárias.")
        elif resultado["ha_transacoes"]:
            st.caption("A área lilás representa a arrecadação; a área laranja, o peso morto. Q₀ e Qₜ indicam as quantidades antes e depois do imposto.")
        else:
            st.caption("Sem transações: não há arrecadação nem preços efetivamente negociados. A área laranja representa toda a perda de excedente.")
    with coluna_indicadores:
        st.subheader("Indicadores")
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
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Arrecadação", moeda(resultado["arrecadacao"]))
    m2.metric("Peso morto", moeda(resultado["peso_morto"]))
    m3.metric("Excedente do consumidor", moeda(resultado["ec"]))
    m4.metric("Excedente do produtor", moeda(resultado["ep"]))

    cw1, cw2 = st.columns([1, 1.15], gap="large")
    with cw1:
        st.plotly_chart(grafico_composicao_excedente(resultado), use_container_width=True,
                        config={"displaylogo": False})
        st.caption("O excedente total com imposto soma excedentes privados e arrecadação pública, uma única vez.")
    with cw2:
        st.markdown("#### O que aconteceu neste mercado?")
        # O cifrão deve ser escapado apenas no Markdown: sem isso,
        # valores R$ podem ser interpretados como delimitadores de matemática.
        st.markdown(explicacao(resultado, experiencia).replace("$", r"\$"))
        st.markdown(
            '<div class="lce-note">Estas conclusões dependem de concorrência perfeita, equilíbrio parcial, '
            'curvas lineares e das hipóteses monetárias usadas para interpretar o bem-estar. '
            'Elas não são estimativas de incidência tributária observada no Brasil.</div>',
            unsafe_allow_html=True,
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
            # Não antecipar a descoberta antes da exploração.
            st.markdown(
                "Três mercados partem do **mesmo equilíbrio inicial** e recebem "
                "o **mesmo imposto**. Explore como seus resultados se relacionam. "
                "Você pode seguir uma questão sugerida ou comparar livremente."
            )
            # Sempre renderizar UMA legenda neste ponto. Antes, ela era
            # criada somente para imposto zero/proibitivo: sua inserção ou
            # remoção deslocava os painéis seguintes e podia recolhê-los.
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
            # Roteiro opcional: nenhuma pergunta é obrigatória ou bloqueia a comparação.
            with st.expander(
                "💡 Questões para investigar · opcional", expanded=False,
                key="lce_a_painel_questoes", on_change="rerun",
            ):
                st.caption("Escolha uma curiosidade para explorar. Não há respostas obrigatórias nem pontuação.")
                questao_a = st.radio(
                    "O que você quer investigar?",
                    options=list(QUESTOES),
                    format_func=lambda chave: QUESTOES[chave],
                    key="lce_a_questao",
                )
                st.markdown("**Experimente observar**")
                st.markdown(sugestao(questao_a, cenarios))

            st.plotly_chart(grafico_reparticao(cenarios), use_container_width=True,
                            config={"displaylogo": False})
        else:
            st.subheader("Experimento B · Quanto o imposto distorce o mercado?")
            if resultado["t"] == 0:
                st.markdown(
                    "**O que observar:** sem imposto, não há perda de eficiência. "
                    "As elasticidades dos três mercados são diferentes, "
                    "mas nenhum deles sofre uma redução de transações."
                )
            else:
                st.markdown(
                    "**O que observar:** com o mesmo imposto, mercados mais "
                    "sensíveis ao preço deixam de realizar mais transações e "
                    "apresentam maior peso morto, **mesmo quando a divisão "
                    "potencial do imposto é de 50% para cada lado**."
                )
            with st.expander("Por que isso acontece? · Detalhes do experimento B"):
                st.markdown(
                    "Mantemos **P₀ = 60**, **Q₀ = 40** e o mesmo imposto. "
                    "Nas curvas inversas, fazemos **b = d**: isso garante "
                    "uma divisão potencial de 50% para cada lado. Alteramos "
                    "as duas inclinações conjuntamente, mudando a resposta da "
                    "quantidade ao imposto. As elasticidades apresentadas na "
                    "tabela são **pontuais no equilíbrio inicial** e não "
                    "permanecem constantes ao longo das curvas."
                )
            if any(not r["ha_transacoes"] for _, r in cenarios):
                st.warning("Pelo menos um cenário chegou ao imposto proibitivo: nele não existem preços de transação nem repartição efetiva do tributo.")
            st.plotly_chart(grafico_distorcao(cenarios), use_container_width=True,
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
        if experiencia == "Experimento A":
            with st.expander(
                "📖 Compreenda o mecanismo · opcional", expanded=False,
                key="lce_a_painel_mecanismo", on_change="rerun",
            ):
                # A questão é a mesma selecionada acima; se o primeiro painel estiver
                # fechado, a primeira questão serve somente como padrão navegável.
                questao_a = st.session_state.get("lce_a_questao", "incidencia")
                st.markdown(f"**{QUESTOES[questao_a]}**")
                nivel_a = st.radio(
                    "Nível de aprofundamento",
                    NIVEIS,
                    horizontal=True,
                    key="lce_a_nivel",
                )
                st.markdown(explicar_questao(questao_a, nivel_a, cenarios).replace("$", r"\$"))
                notacao = formula(questao_a, nivel_a)
                if notacao:
                    st.latex(notacao)
                st.caption("As explicações descrevem o experimento teórico; não são previsões para um mercado real.")
            with st.expander(
                "Síntese econômica · após a comparação", expanded=False,
                key="lce_a_painel_sintese", on_change="rerun",
            ):
                questao_a = st.session_state.get("lce_a_questao", "incidencia")
                st.markdown(sintese(questao_a, cenarios).replace("$", r"\$"))
                st.caption("Síntese do modelo hipotético; consulte as hipóteses na aba Modelo e hipóteses.")

with aba_metodo:
    st.subheader("O modelo por trás da simulação")
    st.markdown("As curvas inversas de demanda e oferta são lineares:")
    st.latex(r"P_D(Q)=a-bQ \qquad P_S(Q)=c+dQ")
    st.markdown("Antes do imposto, a quantidade e o preço são determinados pelo equilíbrio:")
    st.latex(r"Q_0=\frac{a-c}{b+d}, \qquad P_0=a-bQ_0=c+dQ_0")
    st.markdown("Depois do imposto específico, a quantidade não pode ficar negativa:")
    st.latex(r"Q_t=\max\left(0,\frac{a-c-t}{b+d}\right)")
    st.markdown("Se há transações, a diferença entre preços é exatamente o imposto:")
    st.latex(r"P_C=a-bQ_t,\quad P_P=c+dQ_t,\quad P_C-P_P=t")
    st.markdown("Excedente total e perda de eficiência:")
    st.latex(r"ET(Q)=\int_0^Q [P_D(q)-P_S(q)]\,dq")
    st.latex(r"PM=ET(Q_0)-ET(Q_t)=\frac{b+d}{2}(Q_0-Q_t)^2")
    with st.expander("Parâmetros calculados para esta simulação"):
        st.write({chave: round(resultado[chave], 6) for chave in ("a", "b", "c", "d", "t")})
        st.write({
            "Elasticidade da demanda inicial (módulo)": round(abs(resultado["elasticidade_demanda_0"]), 6),
            "Elasticidade da oferta inicial": round(resultado["elasticidade_oferta_0"], 6),
        })
    st.markdown("#### Hipóteses e limitações")
    st.markdown(
        "O modelo assume um único mercado competitivo, equilíbrio parcial estático, "
        "oferta associada ao custo marginal relevante, demanda como disposição marginal "
        "a pagar e ausência de externalidades. Para interpretar excedentes como "
        "medidas monetárias de bem-estar, são necessárias condições adicionais, "
        "como efeitos-renda desprezíveis. Ao somar a arrecadação pública ao "
        "excedente privado, atribui-se igual peso marginal a essas unidades "
        "monetárias, sem modelar custos de arrecadação, efeitos distributivos "
        "ou uso da receita pública."
    )
    st.markdown(
        "**Limitação matemática:** com Pˢ(Q)=c+dQ, c≥0 e d>0, a elasticidade "
        "pontual da oferta não pode ser inferior a 1. Elasticidades mudam ao "
        "longo de curvas lineares; os valores configurados referem-se ao "
        "equilíbrio inicial. Se o imposto eliminar as transações, não há "
        "preços efetivos de negociação nem arrecadação."
    )
    st.markdown(
        "**Fontes para estudo:** Varian & Melitz, *Intermediate Microeconomics*; "
        "OpenStax, *Principles of Economics*; Benzarti, *Tax Incidence Anomalies* (2025). "
        "O documento técnico completo está no Google Drive do projeto."
    )

st.divider()
st.caption("LCE · Laboratório de Cenários Econômicos — projeto acadêmico independente · Módulo 01, interface v1.2")

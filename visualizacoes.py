"""Figuras do LCE. O equilibrio e os excedentes vem de modelo_mercado.

As formulas P_D(Q), P_S(Q) aqui sao usadas apenas para desenhar curvas,
nao para recalcular o equilibrio nem os indicadores economicos.
"""

import plotly.graph_objects as go

COR_DEMANDA = "#3268BB"
COR_OFERTA = "#10977D"
COR_CONSUMIDOR = "#4774CC"
COR_PRODUTOR = "#19A48B"
COR_RECEITA = "#7C72D8"
COR_PESO_MORTO = "#E7A33B"
COR_INICIAL = "#434D60"
COR_TEXTO = "#344054"


def _base(fig, altura=435):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial, sans-serif", color=COR_TEXTO, size=12),
        margin=dict(l=24, r=18, t=22, b=46),
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#ECF0F4", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#ECF0F4", zeroline=False)
    return fig


def _limites_mercado(resultado):
    """Limites comparaveis sem desenhar demanda com preco negativo."""
    a, b, c, d = (resultado[x] for x in ("a", "b", "c", "d"))
    qmax = min(a / b, 1.45 * resultado["q0"])
    y_candidatos = [a, c + d * qmax, resultado["pc"] or 0]
    if resultado["t"] > 0 and resultado["ha_transacoes"]:
        y_candidatos.append(c + d * qmax + resultado["t"])
    return qmax * 1.03, max(y_candidatos) * 1.07


def grafico_mercado(resultado, cenarios=None):
    """Curvas, equilibrio e areas; cenarios permite usar escalas comuns."""
    a, b, c, d = (resultado[x] for x in ("a", "b", "c", "d"))
    t = resultado["t"]
    q0, qt, p0 = resultado["q0"], resultado["qt"], resultado["p0"]
    pc, pp = resultado["pc"], resultado["pp"]

    # Nao desenhar a demanda onde a disposicao a pagar e negativa.
    q_max = min(a / b, 1.45 * q0)
    qs = [q_max * k / 120 for k in range(121)]
    pd = [a - b * q for q in qs]
    ps = [c + d * q for q in qs]
    fig = go.Figure()

    # A receita e um retangulo; o peso morto e a regiao de trocas perdidas.
    if t > 0 and resultado["ha_transacoes"]:
        fig.add_trace(go.Scatter(
            x=[0, qt, qt, 0, 0], y=[pp, pp, pc, pc, pp],
            fill="toself", fillcolor="rgba(124,114,216,0.17)",
            line=dict(color="rgba(124,114,216,0)", width=0),
            name="Arrecadação", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=[qt, qt, q0, qt], y=[pp, pc, p0, pp],
            fill="toself", fillcolor="rgba(231,163,59,0.28)",
            line=dict(color="rgba(231,163,59,0.6)", width=1),
            name="Peso morto", hoverinfo="skip",
        ))
    elif t > 0 and not resultado["ha_transacoes"]:
        fig.add_trace(go.Scatter(
            x=[0, 0, q0, 0], y=[c, a, p0, c],
            fill="toself", fillcolor="rgba(231,163,59,0.27)",
            line=dict(color="rgba(231,163,59,0.7)", width=1),
            name="Peso morto", hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter(
        x=qs, y=pd, mode="lines", name="Demanda",
        line=dict(color=COR_DEMANDA, width=3),
        hovertemplate="Q = %{x:.2f}<br>Disposição marginal a pagar = %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=qs, y=ps, mode="lines", name="Oferta",
        line=dict(color=COR_OFERTA, width=3),
        hovertemplate="Q = %{x:.2f}<br>Custo marginal = %{y:.2f}<extra></extra>",
    ))

    # A oferta mais o imposto representa precos ao consumidor (sem troca na tecnologia).
    if t > 0 and resultado["ha_transacoes"]:
        fig.add_trace(go.Scatter(
            x=qs, y=[s + t for s in ps], mode="lines", name="Oferta + imposto",
            line=dict(color=COR_OFERTA, dash="dash", width=1.7),
            hovertemplate="Q = %{x:.2f}<br>Oferta + imposto = %{y:.2f}<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x=[q0], y=[p0], mode="markers+text", name="Equilíbrio inicial",
        text=["E₀"], textposition="top right",
        marker=dict(size=11, color=COR_INICIAL, line=dict(color="white", width=2)),
        hovertemplate="Equilíbrio inicial<br>Q₀ = %{x:.2f}<br>P₀ = %{y:.2f}<extra></extra>",
    ))
    if resultado["ha_transacoes"] and t > 0:
        fig.add_trace(go.Scatter(
            x=[qt, qt], y=[pp, pc], mode="lines+markers", name="Cunha tributária",
            line=dict(color="#805DAD", width=3.5),
            marker=dict(size=10, color=[COR_PRODUTOR, COR_CONSUMIDOR]),
            hovertemplate="Q = %{x:.2f}<br>Preço = %{y:.2f}<extra></extra>",
        ))
        fig.add_vline(x=qt, line=dict(color="#AAB2BC", dash="dot", width=1))
    elif not resultado["ha_transacoes"]:
        fig.add_annotation(
            x=q0 * 0.28, y=p0, text="Sem transações",
            showarrow=False, bgcolor="rgba(255,255,255,0.88)",
            font=dict(color="#B66B19", size=13),
        )

    escala = [resultado] if cenarios is None else [r for _, r in cenarios]
    limites = [_limites_mercado(r) for r in escala]
    max_q = max(limite[0] for limite in limites)
    max_p = max(limite[1] for limite in limites)
    # Guias pontilhadas ajudam a localizar as quantidades de equilibrio.
    fig.add_vline(x=q0, line=dict(color="#B8C0CD", dash="dot", width=1))
    _base(fig, 440)
    fig.update_xaxes(title="Quantidade (unidades por período)", range=[0, max_q])
    fig.update_yaxes(title="Preço por unidade (R$/un.)", range=[0, max_p])
    return fig


def grafico_composicao_excedente(resultado):
    """Decomposicao do excedente, sem duplicar os calculos economicos."""
    fig = go.Figure()
    for rotulo, key_inicial, key_final, cor in [
        ("Consumidor", "ec0", "ec", COR_CONSUMIDOR),
        ("Produtor", "ep0", "ep", COR_PRODUTOR),
        ("Governo", None, "arrecadacao", COR_RECEITA),
    ]:
        fig.add_bar(
            x=["Sem imposto", "Com imposto"],
            y=[resultado[key_inicial] if key_inicial else 0, resultado[key_final]],
            name=rotulo, marker_color=cor,
            hovertemplate="%{x}<br>" + rotulo + ": %{y:,.2f}<extra></extra>",
        )
    _base(fig, 305)
    fig.update_layout(barmode="stack", margin=dict(l=20, r=15, t=10, b=30))
    fig.update_yaxes(title="Excedente e arrecadação (unidades monetárias)")
    return fig


def grafico_reparticao(resultados):
    """Comparacao das parcelas teoricas/efetivas da cunha tributaria."""
    nomes = [nome for nome, _ in resultados]
    consumidores = [100 * r["fracao_consumidor_potencial"] for _, r in resultados]
    produtores = [100 * r["fracao_produtor_potencial"] for _, r in resultados]
    fig = go.Figure()
    fig.add_bar(x=nomes, y=consumidores, name="Consumidor", marker_color=COR_CONSUMIDOR,
                text=[f"{v:.0f}%" for v in consumidores], textposition="inside")
    fig.add_bar(x=nomes, y=produtores, name="Produtor", marker_color=COR_PRODUTOR,
                text=[f"{v:.0f}%" for v in produtores], textposition="inside")
    _base(fig, 350)
    fig.update_layout(barmode="stack", margin=dict(l=18, r=12, t=10, b=64))
    fig.update_yaxes(title="Parcela da cunha (%)", range=[0, 100])
    return fig


def grafico_distorcao(resultados):
    """Receita e peso morto em cada cenario (escala monetaria comum)."""
    nomes = [nome for nome, _ in resultados]
    fig = go.Figure()
    receitas = [r["arrecadacao"] for _, r in resultados]
    perdas = [r["peso_morto"] for _, r in resultados]
    # Rotulos dentro das barras: contraste legivel em temas claro e escuro.
    # Valores nulos permanecem visiveis na tabela abaixo do grafico.
    fig.add_bar(x=nomes, y=receitas, name="Arrecadação", marker_color=COR_RECEITA,
                text=[f"{v:.0f}" if v > 0 else "" for v in receitas],
                textposition="inside", insidetextanchor="middle",
                textfont=dict(color="#FFFFFF", size=13))
    fig.add_bar(x=nomes, y=perdas, name="Peso morto", marker_color=COR_PESO_MORTO,
                text=[f"{v:.0f}" if v > 0 else "" for v in perdas],
                textposition="inside", insidetextanchor="middle",
                textfont=dict(color="#FFFFFF", size=13))
    _base(fig, 350)
    fig.update_layout(barmode="group", margin=dict(l=18, r=12, t=18, b=64),
                      uniformtext_minsize=12, uniformtext_mode="hide")
    fig.update_yaxes(title="Unidades monetárias / período")
    if not any(receitas) and not any(perdas):
        fig.add_annotation(
            x=0.5, y=0.5, xref="paper", yref="paper",
            text="Sem arrecadação nem peso morto",
            showarrow=False, font=dict(color="#8997AC", size=14),
        )
    return fig

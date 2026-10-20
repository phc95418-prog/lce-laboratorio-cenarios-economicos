"""Preparação Plotly: toda ordenada vem do motor aprovado, sem fórmulas locais."""

import plotly.graph_objects as go

from .estado_individual import EstadoIndividual, chave_visualizacao
from .modelo_firma import avaliar_firma

TOTAIS = {
    "Receita total": ("receita_total", "#145da0", "solid"),
    "Custo total": ("custo_total", "#a84b0a", "dash"),
    "Lucro": ("lucro", "#087858", "dot"),
}
MARGINAIS = {
    "Receita marginal": ("receita_marginal", "#145da0", "solid"),
    "Custo marginal": ("custo_marginal", "#a84b0a", "dash"),
}


def _valor(resultado, atributo):
    return getattr(resultado, atributo) if hasattr(resultado, atributo) else getattr(resultado.curvas, atributo)


def _guia_otimo(fig, x, texto):
    # Contorno duplo legível em fundo claro ou escuro, sem depender de detectar
    # o tema Python durante a mudança de tema nativa do Streamlit.
    fig.add_vline(x=x, line_width=4, line_color="#ffffff")
    fig.add_vline(x=x, line_width=2, line_dash="dot", line_color="#0f172a",
                  annotation_text=texto, annotation_position="top right")


def grafico_individual(estado: EstadoIndividual) -> go.Figure:
    escolha = estado.escolha
    p, q = escolha.parametros, escolha.q
    marginal = estado.perspectiva == "Análise Marginal"
    series = MARGINAIS if marginal else TOTAIS if estado.foco == "Geral" else {estado.foco: TOTAIS[estado.foco]}
    # Incluir Q escolhido e ótimos na malha evita marcadores fora da curva amostrada.
    escolhido = avaliar_firma(q, p)
    dominio = sorted(set([p.q_max*(i/160) for i in range(161)] + [q, escolhido.otimos.q_receita, escolhido.otimos.q_lucro]))
    resultados = [avaliar_firma(x, p) for x in dominio]
    fig = go.Figure()
    valores = [0.0]
    for nome, (atributo, cor, estilo) in series.items():
        y = [_valor(r, atributo) for r in resultados]
        valores.extend(y)
        fig.add_trace(go.Scatter(x=dominio, y=y, mode="lines", name=nome,
                                 line={"color":cor, "dash":estilo, "width":3},
                                 hovertemplate="Q=%{x:.4f}<br>%{y:.4f}<extra>%{fullData.name}</extra>"))
        fig.add_trace(go.Scatter(x=[q], y=[_valor(escolhido, atributo)], mode="markers",
                                 name=f"Q escolhido · {nome}", showlegend=False,
                                 marker={"color":cor,"size":9,"symbol":"circle"},
                                 meta={"papel":"escolha", "funcao":atributo}))
    fig.add_vline(x=q, line_width=1, line_dash="dash", line_color="#64748b")
    fig.add_hline(y=0, line_width=1, line_color="#64748b")
    if estado.mostrar_otimos:
        # Na vista de CT, guias de quantidade evitam atribuir um ótimo de outra função.
        pontos = [("Q_R · receita máxima", escolhido.otimos.q_receita, "receita_total", "diamond")]
        pontos.append(("Q_M · lucro máximo", escolhido.otimos.q_lucro, "lucro", "x"))
        for nome, x, atributo, simbolo in pontos:
            if marginal and atributo == "receita_total":
                continue
            if marginal:
                # Em a<c, Q_M é fronteira, não um encontro de marginais.
                if p.a < p.c:
                    _guia_otimo(fig,0,"Q_M · fronteira")
                    continue
                atributo = "receita_marginal"
            elif estado.foco not in ("Geral", "Receita total" if atributo == "receita_total" else "Lucro"):
                _guia_otimo(fig,x,"Q_R · referência" if atributo == "receita_total" else "Q_M · referência")
                continue
            r = avaliar_firma(x, p)
            fig.add_trace(go.Scatter(x=[x], y=[_valor(r, atributo)], mode="markers",
                                     name=nome + (" · fronteira" if x == 0 else ""),
                                     marker={"color":"#ffffff", "symbol":simbolo,"size":15,
                                             "line":{"color":"#0f172a","width":2}},
                                     meta={"papel":"otimo", "funcao":atributo}))
    minimo, maximo = min(valores), max(valores)
    folga = max(1.0, (maximo-minimo)*0.08)
    fig.update_layout(
        height=420, margin={"l":15,"r":15,"t":10,"b":20},
        xaxis={"title":"Quantidade (unidades)", "range":[0,p.q_max],
               "minallowed":0, "maxallowed":p.q_max, "fixedrange":False},
        yaxis={"title":"u.m./unidade" if marginal else "u.m.",
               "range":[minimo-folga,maximo+folga], "fixedrange":False},
        legend={"orientation":"h","y":1.02,"yanchor":"bottom","x":0},
        font={"size":14}, template="plotly_white", separators=",.",
        dragmode="zoom", transition={"duration":0},
        uirevision=f"{chave_visualizacao(estado)}:{p}:{estado.zoom.get(chave_visualizacao(estado),0)}",
    )
    return fig

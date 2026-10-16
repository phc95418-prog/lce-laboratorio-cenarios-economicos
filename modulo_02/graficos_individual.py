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
                    fig.add_vline(x=0, line_dash="dot", line_color="#334155",
                                  annotation_text="Q_M · fronteira", annotation_position="top right")
                    continue
                atributo = "receita_marginal"
            elif estado.foco not in ("Geral", "Receita total" if atributo == "receita_total" else "Lucro"):
                fig.add_vline(x=x, line_dash="dot", line_color="#334155",
                              annotation_text="Q_R · referência" if atributo == "receita_total" else "Q_M · referência",
                              annotation_position="top right")
                continue
            r = avaliar_firma(x, p)
            fig.add_trace(go.Scatter(x=[x], y=[_valor(r, atributo)], mode="markers",
                                     name=nome + (" · fronteira" if x == 0 else ""),
                                     marker={"color":"#334155", "symbol":simbolo,"size":12},
                                     meta={"papel":"otimo", "funcao":atributo}))
    minimo, maximo = min(valores), max(valores)
    folga = max(1.0, (maximo-minimo)*0.08)
    nivel = estado.zoom.get(chave_visualizacao(estado), 0)
    fator = 1.5 ** nivel
    largura = p.q_max / fator
    x0 = max(0.0, min(q-largura/2, p.q_max-largura)) if nivel else 0.0
    ys = [_valor(escolhido, atributo) for atributo, _, _ in series.values()]
    centro_y = (min(ys)+max(ys))/2
    y_base = (minimo-folga, maximo+folga)
    altura = (y_base[1]-y_base[0])/fator
    y_range = [centro_y-altura/2, centro_y+altura/2] if nivel else list(y_base)
    fig.update_layout(
        height=420, margin={"l":15,"r":15,"t":10,"b":20},
        xaxis={"title":"Quantidade (unidades)", "range":[x0,min(p.q_max,x0+largura)], "fixedrange":True},
        yaxis={"title":"u.m./unidade" if marginal else "u.m.", "range":y_range, "fixedrange":True},
        legend={"orientation":"h","y":1.02,"yanchor":"bottom","x":0},
        font={"size":14}, template="plotly_white", separators=",.",
        transition={"duration":0}, uirevision=f"{chave_visualizacao(estado)}:{nivel}",
    )
    return fig

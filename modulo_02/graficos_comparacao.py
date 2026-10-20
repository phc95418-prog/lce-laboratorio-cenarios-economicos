"""Dois gráficos separados, com limites comuns e curvas no domínio próprio."""

from .estado_individual import EstadoIndividual, Escolha
from .estado_comparacao import resultados_comparacao
from .graficos_individual import grafico_individual


def graficos_comparacao(estado):
    r, a, _ = resultados_comparacao(estado)
    figuras = [grafico_individual(EstadoIndividual(escolha=Escolha(x.parametros,x.curvas.q),
                foco=estado.comparacao.foco)) for x in (r,a)]
    xmax = max(r.parametros.q_max,a.parametros.q_max)
    ymin = min(f.layout.yaxis.range[0] for f in figuras)
    ymax = max(f.layout.yaxis.range[1] for f in figuras)
    contexto = repr((r.parametros,a.parametros,estado.comparacao.foco,estado.comparacao.revisao))
    for f in figuras:
        f.update_layout(xaxis={"range":[0,xmax],"maxallowed":xmax},
                        yaxis={"range":[ymin,ymax]}, uirevision=contexto,
                        legend={"itemclick":False,"itemdoubleclick":False},
                        # Margens idênticas também preservam unidades por pixel.
                        margin={"l":80,"r":20,"t":35,"b":60}, height=420)
    return figuras, contexto

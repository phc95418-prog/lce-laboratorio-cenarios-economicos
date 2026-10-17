"""Um gráfico por modo B, coordenadas e domínios do motor aprovado."""
import plotly.graph_objects as go
from .estruturas_mercado import avaliar_mercados
from .modelo_firma import avaliar_curvas
from .geometria_b import poligono_b
from .estado_b import MODOS, regiao_ativa

NOMES={"EC":"Excedente do consumidor","EP":"Excedente do produtor","DWL":"Perda de eficiência", "T":"Transferência", "L_C":"Perda do consumidor nas unidades não vendidas", "L_P":"Perda do produtor nas unidades não vendidas"}


def grafico_b(e):
    p=e.parametros
    r=avaliar_mercados(p)
    qc,qm=r.concorrencia.curvas.q,r.monopolio.curvas.q
    grid=sorted(set([p.q_max*i/160 for i in range(161)]+[qc,qm]))
    curvas=[avaliar_curvas(q,p) for q in grid]
    fig=go.Figure()
    if e.modo==MODOS[2]:
        regiao=regiao_ativa(e)
        vertices=poligono_b(p,regiao,e.regime)
        if vertices:
            x,y=zip(*(vertices+vertices[:1]))
            fig.add_trace(go.Scatter(x=x,y=y,fill="toself",mode="lines",name="Área "+regiao,
                fillcolor="rgba(70,130,180,0.28)",line={"color":"#4088bd","width":1.5},
                meta={"papel":"regiao","regiao":regiao},hoverinfo="skip"))
    series=[("Demanda inversa P_D","preco_demanda","#2f82c7","solid"),
            ("Custo marginal agregado CMg","custo_marginal","#ce7427","dash")]
    if e.modo==MODOS[1]: series.insert(1,("Receita marginal RMg","receita_marginal","#1f987a","dot"))
    for nome,atributo,cor,traco in series:
        fig.add_trace(go.Scatter(x=grid,y=[getattr(c,atributo) for c in curvas],mode="lines",name=nome,
            line={"color":cor,"width":3,"dash":traco},meta={"papel":"curva","funcao":atributo},
            hovertemplate="Q=%{x:.4f}<br>%{y:.4f} u.m./unidade<extra>%{fullData.name}</extra>"))
    if qc>0:
        for nome,resultado,simbolo in (("C · Concorrência",r.concorrencia,"diamond"),("M · Monopólio",r.monopolio,"circle")):
            q,preco=resultado.curvas.q,resultado.preco_transacao
            fig.add_trace(go.Scatter(x=[q],y=[preco],mode="markers",name=nome,
                marker={"symbol":simbolo,"size":13,"color":"#ffffff","line":{"color":"#0f172a","width":2}},
                meta={"papel":"equilibrio","regime":nome},hovertemplate="Q=%{x:.4f}<br>P=%{y:.4f}<extra>%{fullData.name}</extra>"))
            fig.add_shape(type="line",x0=q,x1=q,y0=0,y1=preco,line={"color":"#8290a0","dash":"dot","width":1})
        if e.modo==MODOS[1]:
            marginal=r.monopolio.curvas.custo_marginal
            fig.add_trace(go.Scatter(x=[qm],y=[marginal],mode="markers",name="RMg=CMg em Q_M · não é P_M",
                marker={"symbol":"triangle-up","color":"#ffffff","size":12,"line":{"color":"#0f172a","width":2}},meta={"papel":"condicao_marginal"}))
            fig.add_shape(type="line",x0=qm,x1=qm,y0=marginal,y1=r.monopolio.preco_transacao,line={"color":"#8290a0","dash":"dash"})
    else:
        texto="a=c: igualdade marginal na fronteira, sem comércio" if p.a==p.c else "a<c: RMg(0)<CMg(0), sem comércio"
        fig.add_annotation(text=texto,xref="paper",yref="paper",x=0,y=.97,showarrow=False,xanchor="left",yanchor="top")
    inferior=-p.a if e.modo==MODOS[1] else 0
    superior=max(p.a,curvas[-1].custo_marginal)
    margem=(superior-inferior)*.08
    fig.update_layout(height=480,margin={"l":20,"r":20,"t":100,"b":20},template="plotly_white",separators=",.",
        xaxis={"title":"Quantidade (unidades)","range":[0,p.q_max],"minallowed":0,"maxallowed":p.q_max},
        yaxis={"title":"u.m./unidade","range":[inferior-margem,superior+margem]},
        legend={"orientation":"h","y":1,"yanchor":"bottom"},font={"size":14},dragmode="zoom",transition={"duration":0},
        uirevision=f"B:{p}:{e.modo}:{e.zoom.get(e.modo,0)}")
    fig.add_hline(y=0,line_color="#8290a0",line_width=1)
    return fig

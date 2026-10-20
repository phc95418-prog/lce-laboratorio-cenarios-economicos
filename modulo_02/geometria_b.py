"""Vértices G-03/G-04 derivados exclusivamente dos resultados do motor.

Não há coordenadas ilustrativas. EP é trapezoidal no monopólio e triangular
na concorrência; DWL usa o contorno da união L_C∪L_P, preenchido uma só vez.
"""
from .estruturas_mercado import avaliar_mercados


def poligono_b(parametros,regiao,regime="Concorrência"):
    if regiao not in ("EC","EP","DWL","T","L_C","L_P") or regime not in ("Concorrência","Monopólio"):
        raise ValueError("Região ou regime inválido.")
    r=avaliar_mercados(parametros)
    if r.concorrencia.curvas.q==0: return []
    qc,qm=r.concorrencia.curvas.q,r.monopolio.curvas.q
    pc,pm=r.concorrencia.preco_transacao,r.monopolio.preco_transacao
    cm=r.monopolio.curvas.custo_marginal
    escolhido=r.concorrencia if regime=="Concorrência" else r.monopolio
    q,preco=escolhido.curvas.q,escolhido.preco_transacao
    return {
        "EC":[(0,parametros.a),(q,preco),(0,preco)],
        "EP":[(0,preco),(q,preco),(q,escolhido.curvas.custo_marginal),(0,parametros.c)],
        "DWL":[(qm,pm),(qc,pc),(qm,cm)],
        "T":[(0,pc),(qm,pc),(qm,pm),(0,pm)],
        "L_C":[(qm,pm),(qm,pc),(qc,pc)],
        "L_P":[(qm,pc),(qm,cm),(qc,pc)],
    }[regiao]


def area_poligono(vertices):
    if len(vertices)<3: return 0.0
    return abs(sum(x*y2-x2*y for (x,y),(x2,y2) in zip(vertices,vertices[1:]+vertices[:1])))/2

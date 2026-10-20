"""Catálogo explícito de figuras já calculadas; nenhuma equação econômica nova."""
from hashlib import sha256
import json
import re
import unicodedata

TITULOS = {
    "E1":"Equilíbrio de mercado — oferta, demanda e imposto",
    "E2":"Composição dos excedentes e arrecadação",
    "E3":"Experimento A — repartição tributária",
    "E4":"Experimento B — distorções e perda de eficiência",
}


def _slug(texto):
    ascii_ = unicodedata.normalize("NFKD",texto).encode("ascii","ignore").decode()
    return re.sub(r"[^a-z0-9]+","-",ascii_.lower()).strip("-")


def catalogo_exportacao(resultado, ambiente, destaque, cenarios, figuras):
    """Recebe as MESMAS figuras usadas por st.plotly_chart no rerun corrente.

    E1/E2: mercado selecionado. E3/E4: três mercados, sem reduzir ao destaque.
    O hash inclui dados completos e contexto; nunca números arredondados.
    """
    if ambiente not in ("Exploração livre","Experimento A","Experimento B"):
        raise ValueError("Ambiente de exportação desconhecido.")
    ids=("E1","E2") + (("E3",) if ambiente=="Experimento A" else ("E4",) if ambiente=="Experimento B" else ())
    if set(figuras)!=set(ids):
        raise ValueError("Figuras incompatíveis com o contexto de exportação.")
    if len(ids)==3 and (cenarios is None or len(cenarios)!=3):
        raise ValueError("Exportação comparativa exige os três mercados.")
    alvos=[]
    t=resultado["t"]
    imposto=format(t,".15g").replace(".",",")
    for id_ in ids:
        comparativo=id_ in ("E3","E4")
        mercado="Comparação dos três mercados" if comparativo else destaque or "Mercado vigente"
        base=cenarios if comparativo else [(mercado,resultado)]
        if t==0:
            nota="Imposto zero: preços de equilíbrio válidos; sem carga tributária efetiva, arrecadação ou peso morto. Parcelas apenas potenciais."
        else:
            sem=[nome for nome,r in base if not r["ha_transacoes"]]
            nota=("Sem transações, preços negociados ou carga efetiva: "+"; ".join(sem)+". Coeficientes de repasse apenas potenciais nesses mercados.") if sem else "Imposto positivo e transações: repasse efetivo por unidade; arrecadação não é perda de eficiência."
        if id_=="E4" and t>0:
            ativos=[nome for nome,r in base if r["ha_transacoes"]]
            if ativos: nota+=" Com transações: "+"; ".join(ativos)+"."
        alvos.append(dict(id=id_,titulo=TITULOS[id_],
            seletor=".st-key-lce_m01_export_"+id_.lower(),
            contexto=f"Módulo 01 · {ambiente} · {mercado} · imposto R$ {imposto}/unidade",
            nota=nota,
            arquivo="lce-m01-"+_slug(ambiente)+"-"+_slug(mercado)+"-"+id_.lower()+"-t-"+_slug(format(t,".15g")),
            figura=json.loads(figuras[id_].to_json())))
    contexto=sha256(json.dumps(alvos,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    return {"contexto":contexto,"alvos":alvos}

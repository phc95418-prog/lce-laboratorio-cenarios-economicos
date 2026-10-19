"""Janela modeless com DOM próprio; reutiliza o editor numérico aprovado."""
from pathlib import Path
import streamlit as st

PASTA=Path(__file__).parent
_controle=PASTA.joinpath("controles_individual.js").read_text(encoding="utf-8")
JANELA=st.components.v2.component(
    "lce_m02_janela_variaveis",
    js=_controle.replace("export default renderizarControle;","")+"\n"+PASTA.joinpath("janela_variaveis.js").read_text(encoding="utf-8"),
    css=PASTA.joinpath("controles_individual.css").read_text(encoding="utf-8")+"\n"+PASTA.joinpath("janela_variaveis.css").read_text(encoding="utf-8"),
)


def campo(nome,rotulo,valor,limites,seq=0,erro="",grupo=""):
    minimo,maximo,passo=limites
    return dict(campo=nome,rotulo=rotulo,valor=valor,minimo=minimo,maximo=maximo,
                passo=passo,seq=seq,erro=erro,grupo=grupo)


def janela(chave,campos,receber,*,descricao=""):
    return JANELA(key=chave,on_evento_change=receber,width=200,
                  data={"campos":campos,"descricao":descricao})


def eventos(retorno):
    """Um lote mantém confirmações de campos distintos durante reruns rápidos."""
    evento=(retorno or {}).get("evento")
    if not isinstance(evento,dict): return []
    lote=evento.get("lote")
    return [e for e in lote if isinstance(e,dict)][:8] if isinstance(lote,list) else [evento]

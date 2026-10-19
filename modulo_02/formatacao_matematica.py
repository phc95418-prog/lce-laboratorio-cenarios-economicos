"""Apresentação de notação existente, sem cálculo ou interpretação nova."""
import re

_TOKENS={
    "RMg−CMg":r"\mathrm{RMg}-\mathrm{CMg}",
    "RMg=CMg":r"\mathrm{RMg}=\mathrm{CMg}",
    "Qmax":r"Q_{\max}","QF":r"Q_F",
    "π":r"\pi","Π":r"\Pi",
}
for _s in ("RMg","CMg","RT","CT","CV","CF","EC","EP","ET","DWL"):
    _TOKENS[_s]=rf"\mathrm{{{_s}}}"
for _s in ("Q_R","Q_M","Q_C","P_D","P_M","P_C","L_C","L_P","Q","T"):
    _TOKENS[_s]=_s
for _s in ("Π_M","Π_C","EP_M","EP_C"):
    _TOKENS[_s]=(r"\Pi" if _s.startswith("Π") else r"\mathrm{EP}")+"_"+_s[-1]
for _s in ("RT","CT","CF","EC","EP","ET","Q","P","π"):
    _TOKENS["Δ"+_s]=r"\Delta "+_TOKENS.get(_s,_s)
for _s in ("a","b","c","s"):
    _TOKENS["∂Q_M/∂"+_s]=rf"\frac{{\partial Q_M}}{{\partial {_s}}}"
_TOKENS.update({
    "RMg(0)=CMg(0)":r"\mathrm{RMg}(0)=\mathrm{CMg}(0)",
    "RMg(0)<CMg(0)":r"\mathrm{RMg}(0)<\mathrm{CMg}(0)",
    "Π_M−Π_C=EP_M−EP_C":r"\Pi_M-\Pi_C=\mathrm{EP}_M-\mathrm{EP}_C",
})
_PADRAO=re.compile(r"(?<![\w\\])("+"|".join(re.escape(k) for k in sorted(_TOKENS,key=len,reverse=True))+r")(?!\w)")


def texto_matematico(texto):
    partes=re.split(r"(\$[^$]+\$)",texto)
    return "".join(p if p.startswith("$") else _PADRAO.sub(lambda m:"$"+_TOKENS[m[0]]+"$",p) for p in partes)


def latex_operadores(formula):
    formula=re.sub(r"(?<=\d)\.(?=\d)", "{,}", formula)
    return re.sub(r"(?<!\\mathrm\{)(?<![a-zA-Z])(?:RMg|CMg|RT|CT|CV|CF|EC|EP|ET|DWL)(?![a-zA-Z])",
                  lambda m:rf"\mathrm{{{m[0]}}}",formula)


def paragrafo(texto):
    import streamlit as st
    for base in ("Base: última edição confirmada. ",
                 "Base: Referência congelada → Atual; Δ=Atual−Referência, calculado antes da formatação. "):
        if texto.startswith(base):
            st.caption(texto_matematico(base));st.markdown(texto_matematico(texto[len(base):]));return
    if texto.startswith(("Perspectiva:","Última confirmação:")):
        st.caption(texto_matematico(texto))
    else: st.markdown(texto_matematico(texto))

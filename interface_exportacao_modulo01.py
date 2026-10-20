"""Exportação na engrenagem; seleção visual não altera controles econômicos."""
from pathlib import Path
from plotly.offline import get_plotlyjs
import streamlit as st
from modulo_02.exportacao_pdf import gerar_pdf, navegador_pdf


def preparar_pdf(pedido, catalogo):
    """Aceita somente um alvo do catálogo vigente; não recebe caminhos locais."""
    if not isinstance(pedido, dict) or pedido.get("contexto") != catalogo["contexto"]:
        raise ValueError("O cenário mudou. Solicite a exportação novamente.")
    alvo = next((a for a in catalogo["alvos"] if a["id"] == pedido.get("id")), None)
    if alvo is None or pedido.get("arquivo") != alvo["arquivo"]:
        raise ValueError("Gráfico de exportação inválido.")
    return dict(contexto=catalogo["contexto"], id=alvo["id"],
                arquivo=alvo["arquivo"] + ".pdf", dados=gerar_pdf(pedido.get("svg")))


def renderizar_exportacao(catalogo):
    st.subheader("Exportar gráfico", anchor=False)
    componente=st.components.v2.component("lce_m01_exportacao",
        js=get_plotlyjs()+"\n"+Path(__file__).with_name("exportacao_modulo01.js").read_text(encoding="utf-8"),
        css=""".lce-m01-exportacao{font:inherit;color:var(--st-text-color)}
        .lce-m01-exportacao label{display:block;margin:.5rem 0}
        .lce-m01-exportacao select{display:block;width:100%;font:inherit;color:inherit;
        background:var(--st-background-color);padding:.5rem;border:1px solid currentColor;border-radius:6px}
        .lce-m01-exportacao button{font:inherit;color:inherit;background:var(--st-background-color);
        padding:.5rem .75rem;border:1px solid currentColor;border-radius:8px;cursor:pointer}
        .lce-m01-exportacao :is(button,select):focus-visible{outline:3px solid var(--st-primary-color);outline-offset:2px}
        .lce-m01-exportacao [role=status]{font-size:.875rem}""")
    def receber_pdf():
        estado = st.session_state.get("lce_m01_exportacao_controle", {})
        try:
            st.session_state["lce_m01_pdf_preparado"] = preparar_pdf(estado.get("pedido_pdf"), catalogo)
            st.session_state.pop("lce_m01_pdf_erro", None)
        except (ValueError, RuntimeError) as erro:
            st.session_state.pop("lce_m01_pdf_preparado", None)
            st.session_state["lce_m01_pdf_erro"] = (catalogo["contexto"], str(erro))

    formatos = ["PNG", "SVG"]
    if navegador_pdf():
        formatos.append("PDF")
    else:
        st.caption("PDF indisponível neste ambiente: Chrome/Chromium não encontrado. PNG e SVG permanecem disponíveis.")
    componente(key="lce_m01_exportacao_controle",data={**catalogo,"formatos":formatos},
               on_pedido_pdf_change=receber_pdf)
    erro = st.session_state.get("lce_m01_pdf_erro")
    if erro and erro[0] == catalogo["contexto"]:
        st.warning("PDF não gerado: " + erro[1])
    pronto = st.session_state.get("lce_m01_pdf_preparado")
    if pronto and pronto["contexto"] == catalogo["contexto"]:
        alvo = next(a for a in catalogo["alvos"] if a["id"] == pronto["id"])
        st.caption("PDF preparado: " + alvo["id"] + " · " + alvo["titulo"] + ". " + alvo["contexto"])
        st.download_button("Baixar PDF preparado", pronto["dados"], pronto["arquivo"],
                           mime="application/pdf", on_click="ignore", key="lce_m01_pdf_download")

"""Estrutura visual compartilhável, sem estado ou cálculos econômicos."""

from contextlib import contextmanager
from pathlib import Path
from hashlib import sha256
import streamlit as st
from plotly.offline import get_plotlyjs
from .exportacao_pdf import navegador_pdf, gerar_pdf
from .textos_interface import EXPERIMENTOS, perguntas_frequentes
from .formatacao_matematica import texto_matematico

ACIONADOR = st.components.v2.component(
    "lce_m02_acoes", isolate_styles=False,
    js=Path(__file__).with_name("acionador_lateral.js").read_text(encoding="utf-8"),
)
CONFIGURACOES = st.components.v2.component(
    "lce_m02_configuracoes",
    js=get_plotlyjs()+"\n"+Path(__file__).with_name("configuracoes.js").read_text(encoding="utf-8"),
    css=Path(__file__).with_name("configuracoes.css").read_text(encoding="utf-8"),
)


def contexto_exportacao(experimento):
    if experimento=="A":
        e=st.session_state.m02_a_individual;c=e.comparacao
        valores=(e.escolha,e.perspectiva,e.foco,e.mostrar_otimos,e.zoom,
                 None if c is None else (c.referencia,c.q_fixa,c.perspectiva,c.foco,c.revisao))
    else:
        e=st.session_state.m02_b_estado
        valores=(e.parametros,e.modo,e.regiao,e.regime,e.parcela,e.decomposicao,e.zoom)
    return sha256(repr(valores).encode()).hexdigest(),e.em_interacao

def topo():
    """Reserva ações antes do seletor, sem consultar ou regravar a economia."""
    with st.container(horizontal=True, vertical_alignment="center", gap="small", key="m02_cabecalho"):
        with st.container(key="m02_titulo"):
            st.title("Módulo 02 · Decisões da Firma", anchor=False)
            st.caption("LCE · LABORATÓRIO DE CENÁRIOS ECONÔMICOS")
        acoes = st.container(horizontal=True, width="content", gap="small", key="m02_acoes_cabecalho")
    return acoes


def cabecalho(modo, *, experimento="A", acoes=None):
    contexto,interacao=contexto_exportacao(experimento)
    def preparar_pdf():
        pedido=(st.session_state.get("m02_configuracoes_reais") or {}).get("exportacao")
        if not isinstance(pedido,dict): return
        permitidos=("lce-experimento-b",) if experimento=="B" else ("lce-experimento-a-individual","lce-experimento-a-referencia","lce-experimento-a-atual")
        try:
            atual,interagindo=contexto_exportacao(experimento)
            if pedido.get("arquivo") not in permitidos or pedido.get("contexto")!=atual or interagindo:
                raise ValueError("A investigação mudou durante a exportação. Prepare novamente após concluir a interação.")
            pdf=gerar_pdf(pedido.get("svg"))
            st.session_state.m02_pdf_preparado=dict(pdf=pdf,arquivo=pedido["arquivo"],contexto=atual)
            st.session_state.m02_pdf_erro=""
        except (ValueError,RuntimeError) as erro:
            st.session_state.m02_pdf_preparado=None;st.session_state.m02_pdf_erro=str(erro)
    with st.container(key="m02_contexto"):
        st.markdown(f"**Experimento {experimento} · {EXPERIMENTOS[experimento]}**")
        st.caption(modo)
    with acoes if acoes is not None else st.container(horizontal=True):
        with st.popover("Configurações", icon=":material/settings:", key="m02_configuracoes"):
            with st.container(width=380,height=420,border=False):
                pronto=st.session_state.get("m02_pdf_preparado")
                arquivo_pronto=pronto["arquivo"] if pronto and pronto["contexto"]==contexto else ""
                CONFIGURACOES(key="m02_configuracoes_reais",on_exportacao_change=preparar_pdf,
                    data={"comparacao":modo=="Comparação controlada","experimento":experimento,
                          "pdf_disponivel":bool(navegador_pdf()),"pdf_pronto":arquivo_pronto,
                          "contexto":contexto,"interacao":interacao})
                if pronto and pronto["contexto"]==contexto:
                    st.download_button("Baixar PDF preparado · "+pronto["arquivo"],pronto["pdf"],
                        file_name=pronto["arquivo"]+".pdf",mime="application/pdf",on_click="ignore")
                    st.caption("Imagem capturada ao preparar. Para outra vista ou tema, prepare novamente.")
                if st.session_state.get("m02_pdf_erro"): st.warning(st.session_state.m02_pdf_erro)
                st.caption("Sobre o modelo está na lateral Ações. Enter aciona controles; Escape fecha os painéis.")
        with st.popover("Ajuda", icon=":material/help_outline:", key="m02_ajuda"):
            with st.container(width=440, height=460, border=False, key="m02_ajuda_corpo"):
                st.subheader("Ajuda · Experimento "+experimento, anchor=False)
                st.caption("Para dúvidas sobre o Experimento "+("B" if experimento=="A" else "A")+", selecione-o no cabeçalho.")
                for pergunta, resposta in perguntas_frequentes(experimento):
                    with st.expander(pergunta):
                        st.markdown(texto_matematico(resposta))


def lateral(estado, acoes, *, complemento=None, resumo=None, experimento="A"):
    """Ações recebidas da interface; pronta para receber as da comparação."""
    with st.sidebar:
        st.subheader("Ações do experimento", anchor=False)
        st.caption("Feche pela seta no topo para liberar a área do gráfico.")
        for rotulo, funcao, ajuda in acoes:
            st.button(rotulo, on_click=funcao, help=ajuda, width="stretch")
        if complemento:
            complemento()
        st.divider()
        st.markdown("**Estado atual**")
        if resumo:
            resumo()
        else:
            p = estado.escolha.parametros
            st.write(f"Q individual: {str(estado.escolha.q).replace('.',',')} unidades")
            st.caption(" · ".join(f"{k}={str(getattr(p,k)).replace('.',',')}" for k in ("a","b","c","s","cf")))
            st.caption(estado.perspectiva+" · "+estado.foco)
        with st.expander("Sobre o modelo"):
            if experimento=="A":
                st.write("Firma monopolista teórica com demanda inversa linear e preço uniforme. Custo variável quadrático; CF é encargo fixo comprometido, inevitável no horizonte corrente. Não há entrada, saída ou decisão endógena de fechamento.")
                st.latex(r"0\leq Q\leq a/b,\quad a,b,s>0,\quad c,\mathrm{CF}\geq0")
            else:
                st.write("Concorrência perfeita e monopólio sob a mesma demanda e custos agregados equivalentes. Tecnologia, unidades produtivas e preços de insumos invariantes; custos variáveis separáveis. Concorrência pressupõe tomada de preço. Não há oligopólio, entrada, saída ou custos de reorganização. B tem somente a, b, c e s, sem CF.")
                st.latex(r"0\leq Q\leq a/b,\quad a,b,s>0,\quad c\geq0")
            st.write("Q em unidades; preços e marginais em u.m./unidade; totais em u.m. hipotéticas. As simulações são condicionais às hipóteses, não previsões empíricas. A análise detalha a interpretação do custo de oportunidade.")
            st.caption(f"Streamlit {st.__version__} · Plotly · motor econômico local com precisão interna não arredondada.")


@contextmanager
def barra_ferramentas():
    with st.container(horizontal=True, horizontal_alignment="center", gap="small", key="m02_ferramentas"):
        yield


@contextmanager
def ferramenta(rotulo, icone, chave, *, variaveis=False):
    """Popover nativo: mantém abertura nos reruns e fecha por fora/Escape.

    Não usar renderização condicional pelo estado aberto: controles mantêm
    suas chaves e rascunhos mesmo quando o painel está recolhido.
    """
    with st.popover(rotulo, icon=icone, key=chave, width=200):
        with st.container(width=380, height=340 if variaveis else "content", border=False):
            yield


def estilo_local():
    ACIONADOR(key="m02_acionador_lateral", data={})
    st.html("<style>"+Path(__file__).with_name("interface.css").read_text(encoding="utf-8")+"</style>")
    st.html("""<style>
    body:has(.st-key-m02_a_root) [data-testid="stExpandSidebarButton"] {
      position:fixed;left:0;top:10px;width:auto;padding:0.4rem 0.6rem;
      border:1px solid currentColor;border-radius:0 8px 8px 0;gap:0.25rem;
      background:var(--background-color);font-size:0.875rem;}
    body:has(.st-key-m02_a_root) [data-testid="stSidebarCollapseButton"] {visibility:visible;}
    body:has(.st-key-m02_a_root) [data-testid="stExpandSidebarButton"]:focus-visible {
      outline:3px solid #3578c8;outline-offset:2px;}
    .st-key-m02_a_root [data-testid="stCaptionContainer"] {opacity:1;}
    :is(.st-key-m02_a_indicadores,.st-key-m02_b_indicadores) [data-testid="stMetric"] {
      max-width:100%;border:1px solid #8290a0;
      border-radius:10px;padding:0.75rem;}
    :is(.st-key-m02_a_indicadores,.st-key-m02_b_indicadores) [data-testid="stMetricLabel"] p {white-space:normal;}
    :is(.st-key-m02_a_indicadores,.st-key-m02_b_indicadores) [data-testid="stMetricLabel"] {min-height:2.8rem;}
    :is(.st-key-m02_a_indicadores,.st-key-m02_b_indicadores) [data-testid="stMetricValue"] {font-size:1.5rem;white-space:normal;}
    </style>""")

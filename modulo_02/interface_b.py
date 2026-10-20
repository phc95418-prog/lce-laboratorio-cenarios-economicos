"""Experimento B local, com quatro parâmetros comuns aos dois regimes."""
import streamlit as st
from .estado_b import (
    EstadoB, MODOS, REGIOES, REGIMES, PARCELAS, CAMPOS, revalidar_b,
    aplicar_evento_b, importar_de_a, abrir_decomposicao, fechar_decomposicao,
    reiniciar_controles, restaurar_parametros_b, regiao_ativa,
)
from .estado_individual import LIMITES
from .janela_variaveis import janela, campo as descritor, eventos
from .estrutura_visual import cabecalho, ferramenta, lateral, barra_ferramentas
from .textos_interface import REGIOES as ROTULOS_REGIOES, DESCRICOES
from .estruturas_mercado import avaliar_mercados
from .graficos_b import grafico_b
from .analise_b import renderizar_analise_b, valor_regiao
from .explicacoes_individual import numero
from .analise_experimento_a import assinado

ROTULOS={"a":"a · intercepto da demanda (u.m./unidade)","b":"b · inclinação da demanda",
         "c":"c · custo marginal inicial (u.m./unidade)","s":"s · inclinação do custo marginal"}


def renderizar_b(*, acoes_cabecalho=None):
    if "m02_b_estado" not in st.session_state: st.session_state.m02_b_estado=EstadoB()
    def atual():
        st.session_state.m02_b_estado=revalidar_b(st.session_state.m02_b_estado)
        return st.session_state.m02_b_estado
    e=atual()
    geracao=st.session_state.get("m02_b_geracao",0)
    def chave(nome): return "m02_b_"+nome
    def selecionar(atributo,widget): setattr(atual(),atributo,st.session_state[widget])
    def importar():
        if importar_de_a(atual(),st.session_state.get("m02_a_individual")):
            reiniciar_controles(st.session_state)
    def restaurar():
        restaurar_parametros_b(atual());reiniciar_controles(st.session_state)
    def resetar_zoom():
        estado=atual();estado.zoom[estado.modo]=estado.zoom.get(estado.modo,0)+1
    def decompor():
        (abrir_decomposicao if st.session_state[chave("decompor")] else fechar_decomposicao)(atual())
    def resumo():
        st.caption(" · ".join(f"{k}={numero(getattr(e.parametros,k))}" for k in CAMPOS))
        st.write(e.modo)
        if e.modo==MODOS[2]:
            st.caption("Região ativa: "+ROTULOS_REGIOES[regiao_ativa(e)]+( " · decomposição" if e.decomposicao else " · "+e.regime))
        st.caption("Um único conjunto de parâmetros para os dois regimes. Importação de A não cria vínculo.")
    cabecalho(e.modo,experimento="B",acoes=acoes_cabecalho)
    lateral(e,[
        ("Utilizar parâmetros do Experimento A",importar,"Copia a, b, c e s do cenário Atual de A, sem CF ou sincronização."),
        ("Restaurar parâmetros do B",restaurar,"Recupera (100,1,20,1) e preserva modos e seleções."),
    ],resumo=resumo,experimento="B")
    def variaveis():
        k=chave(f"janela_variaveis_g{geracao}")
        def receber():
            if geracao!=st.session_state.get("m02_b_geracao",0): return
            retorno=st.session_state.get(k)
            for evento in eventos(retorno):
                nome=evento.get("campo","")
                aplicar_evento_b(atual(),nome.removeprefix("b_"),evento)
        campos=[descritor("b_"+nome,ROTULOS[nome],getattr(e.parametros,nome),LIMITES[nome],
            e.sequencias.get(nome,0),e.erros.get(nome,""),
            "Parâmetros de demanda" if nome in ("a","b") else "Parâmetros de custos") for nome in CAMPOS]
        janela(k,campos,receber,descricao="Os parâmetros afetam concorrência e monopólio simultaneamente. Enter ou perda de foco confirma o campo.")
    with barra_ferramentas():
        with ferramenta("Perspectivas",":material/view_carousel:",chave("ferramenta_perspectivas")):
            st.radio("Modo do Experimento B",MODOS,index=MODOS.index(e.modo),key=chave("modo"),
                on_change=selecionar,args=("modo",chave("modo")))
        variaveis()
        with ferramenta("Visualização",":material/visibility:",chave("ferramenta_visualizacao")):
            st.button("Restaurar visualização",on_click=resetar_zoom,key=chave("restaurar_vista"))
            st.checkbox("Ativar zoom pela roda no gráfico",value=e.roda,key=chave("roda"),
                on_change=selecionar,args=("roda",chave("roda")))
            st.caption("Zoom por arraste e Pan modificam só os eixos. Regime e área mantêm o enquadramento com parâmetros fixos.")
    if e.modo==MODOS[2]:
        st.checkbox("Examinar origem da perda de eficiência",value=e.decomposicao,key=chave("decompor"),on_change=decompor,
            help="Guarda a região principal e o regime; inicia em DWL e mostra uma única região por vez. Ao fechar, restaura as seleções anteriores.")
        if e.decomposicao:
            st.radio("Região da decomposição",PARCELAS,index=PARCELAS.index(e.parcela),horizontal=True,
                format_func=ROTULOS_REGIOES.__getitem__,key=chave("parcela"),on_change=selecionar,args=("parcela",chave("parcela")))
        else:
            st.radio("Região principal",REGIOES,index=REGIOES.index(e.regiao),horizontal=True,
                format_func=ROTULOS_REGIOES.__getitem__,key=chave("regiao"),on_change=selecionar,args=("regiao",chave("regiao")))
            if e.regiao!="DWL":
                st.radio("Regime para a região",REGIMES,index=REGIMES.index(e.regime),horizontal=True,
                    key=chave("regime"),on_change=selecionar,args=("regime",chave("regime")))
            else: st.caption("DWL compara os regimes. O último regime permanece guardado para EC/EP.")
    if e.aviso:
        st.info(e.aviso,icon="ℹ️")
    r=avaliar_mercados(e.parametros)
    if r.concorrencia.curvas.q==0:
        st.info("Sem comércio de equilíbrio: Q_C=Q_M=0; preços transacionados não aplicáveis. Excedentes, DWL e decomposição são zero. Interceptos são valores das funções.",icon="ℹ️")
    if e.modo==MODOS[2]:
        area=regiao_ativa(e)
        st.caption(DESCRICOES[area] if r.concorrencia.curvas.q>0 else "Sem comércio de equilíbrio: a região selecionada tem área zero.")
    fig=grafico_b(e)
    st.plotly_chart(fig,key=chave(f"grafico_{e.modo}_{e.parametros}_{e.zoom.get(e.modo,0)}"),width="stretch",
        config={"displaylogo":False,"displayModeBar":True,"scrollZoom":e.roda,"responsive":True,
                "toImageButtonOptions":{"filename":"lce-experimento-b"},
                "modeBarButtonsToRemove":["select2d","lasso2d","autoScale2d","zoomIn2d","zoomOut2d"]})
    st.caption("C e M, quando presentes, estão na demanda. Curvas limitadas a 0≤Q≤a/b; apenas uma região preenchida no bem-estar. Valores em unidades hipotéticas.")
    def preco(v): return "não aplicável" if v is None else numero(v)
    with st.container(key=chave("indicadores"),horizontal=True):
        if e.modo==MODOS[0]:
            metricas=[("Quantidade competitiva (Q_C) · unidades",numero(r.concorrencia.curvas.q)),("Preço competitivo (P_C) · u.m./unidade",preco(r.concorrencia.preco_transacao)),
                      ("Quantidade monopolista (Q_M) · unidades",numero(r.monopolio.curvas.q)),("Preço monopolista (P_M) · u.m./unidade",preco(r.monopolio.preco_transacao))]
        elif e.modo==MODOS[1]:
            metricas=[("Preço competitivo (P_C) · u.m./unidade",preco(r.concorrencia.preco_transacao)),("Receita marginal em Q_M (RMg) · u.m./unidade",numero(r.monopolio.curvas.receita_marginal)),
                      ("Custo marginal em Q_M (CMg) · u.m./unidade",numero(r.monopolio.curvas.custo_marginal)),("Preço monopolista (P_M) · u.m./unidade",preco(r.monopolio.preco_transacao))]
        else:
            area=regiao_ativa(e)
            metricas=[(ROTULOS_REGIOES[area]+" · u.m.",numero(valor_regiao(e,r)))]
            if area!="DWL": metricas.append(("Perda de eficiência (DWL) · u.m.",numero(r.decomposicao.peso_morto)))
        for rotulo,valor in metricas: st.metric(rotulo,valor,width=320 if e.modo==MODOS[2] else 220)
    if e.modo==MODOS[0]:
        variacoes=(r.diferencas.quantidade,r.diferencas.preco)
        st.table({"Grandeza":["Quantidade (unidades)","Preço (u.m./unidade)"],
            "Δ Monopólio − Concorrência":["não aplicável" if v.absoluta is None else assinado(v.absoluta) for v in variacoes],
            "Δ / base competitiva (%)":["não aplicável" if v.percentual is None else assinado(v.percentual)+"%" for v in variacoes]})
    elif e.modo==MODOS[1] and e.parametros.a>e.parametros.c:
        st.caption("P_C=CMg(Q_C); RMg(Q_M)=CMg(Q_M). P_M é o preço sobre a demanda, não a ordenada marginal do monopólio.")
    elif e.modo==MODOS[2]:
        with st.expander("Excedentes dos dois regimes e balanço"):
            st.caption("Valores em u.m.; Δ=Monopólio−Concorrência. Sinais não representam julgamento distributivo.")
            st.table({"Grandeza":[ROTULOS_REGIOES["EC"],ROTULOS_REGIOES["EP"],"Excedente total (ET)"],
                "Concorrência":[numero(getattr(r.concorrencia.curvas,k)) for k in ("excedente_consumidor","excedente_produtor","excedente_total")],
                "Monopólio":[numero(getattr(r.monopolio.curvas,k)) for k in ("excedente_consumidor","excedente_produtor","excedente_total")],
                "Δ M−C":[assinado(getattr(r.diferencas,k).absoluta) for k in ("excedente_consumidor","excedente_produtor","excedente_total")]})
    if e.em_interacao: st.caption("Atualizando gráfico e indicadores; análise consolidada ao concluir a interação.")
    renderizar_analise_b(e,chave)

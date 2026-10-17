"""Comparação controlada do Experimento A. Não implementa estruturas de mercado."""

from pathlib import Path
import streamlit as st
from plotly.offline import get_plotlyjs

from .estado_comparacao import (
    PERSPECTIVAS, aplicar_quantidade, dominio_comum, encerrar_comparacao,
    restaurar_parametros, resultados_comparacao, substituir_referencia,
)
from .explicacoes_comparacao import resumo_comparacao
from .estado_individual import FOCOS
from .explicacoes_individual import numero
from .graficos_comparacao import graficos_comparacao
from .estrutura_visual import lateral, ferramenta

PASTA = Path(__file__).parent
# Usa o bundle da dependência Plotly instalada: sem CDN, downloads ou biblioteca
# adicional. Registrado uma vez; apenas dados das figuras mudam a cada rerun.
GRAFICOS = st.components.v2.component(
    "lce_m02_par_comparativo", isolate_styles=False,
    js=get_plotlyjs()+"\n"+PASTA.joinpath("graficos_comparacao.js").read_text(encoding="utf-8"),
    css=PASTA.joinpath("graficos_comparacao.css").read_text(encoding="utf-8"),
)


def renderizar_comparacao(estado, componente_numero, parametros):
    c = estado.comparacao
    ciclo = estado.ciclo_comparacao
    geracao = st.session_state.get("m02_a_geracao",0)
    def chave(nome):
        return f"m02_a_comparacao_{nome}_g{geracao}_c{ciclo}"

    def agir(funcao,*args):
        atual = st.session_state.m02_a_individual
        if (geracao == st.session_state.get("m02_a_geracao",0)
                and atual.comparacao is not None and atual.ciclo_comparacao == ciclo):
            funcao(atual,*args)

    def pedir_substituicao(e):
        e.comparacao.substituindo = True
    def confirmar():
        if c.substituindo:
            st.info("Substituir os cinco parâmetros da referência pelos atuais? Quantidades serão preservadas, salvo restrição do domínio comum.",icon="ℹ️")
            st.button("Confirmar substituição",on_click=agir,args=(substituir_referencia,True))
            st.button("Cancelar substituição",on_click=agir,args=(substituir_referencia,False))
    def resumo():
        for titulo,p in (("Referência congelada",c.referencia),("Atual",estado.escolha.parametros)):
            st.markdown("**"+titulo+"**")
            st.caption(" · ".join(f"{k.upper() if k=='cf' else k}={numero(getattr(p,k))}" for k in ("a","b","c","s","cf")))
        r,a,_ = resultados_comparacao(estado)
        st.caption(f"{c.perspectiva} · {c.foco}")
        st.write(f"Q Referência: {numero(r.curvas.q)} · Q Atual: {numero(a.curvas.q)}")
        st.caption(f"Q fixa armazenada: {numero(c.q_fixa)}. Q individual preservada: {numero(estado.escolha.q)}.")
    lateral(estado,[
        ("Substituir referência",lambda: agir(pedir_substituicao),"Solicita confirmação antes de substituir os parâmetros congelados."),
        ("Restaurar parâmetros do Atual",lambda: agir(restaurar_parametros),"Restaura somente os parâmetros do cenário Atual."),
        ("Encerrar comparação",lambda: agir(encerrar_comparacao),"Retorna à investigação individual, preservando sua quantidade."),
    ],complemento=confirmar,resumo=resumo)

    def perspectiva():
        agir(lambda e: setattr(e.comparacao,"perspectiva",st.session_state[chave("perspectiva")]))
    def foco():
        agir(lambda e: setattr(e.comparacao,"foco",st.session_state[chave("foco")]))
    def restaurar(e):
        e.comparacao.revisao += 1
    with st.container(horizontal=True,gap="small"):
        with ferramenta("Perspectivas",":material/view_carousel:",chave("ferramenta_perspectivas")):
            st.radio("Perspectiva comparativa",PERSPECTIVAS,key=chave("perspectiva"),
                     index=PERSPECTIVAS.index(c.perspectiva),on_change=perspectiva)
            st.caption("Quantidade fixa e Decisões ótimas preservam Q individual e Q fixa armazenada.")
        with ferramenta("Alterar variáveis",":material/tune:",chave("ferramenta_variaveis"),variaveis=True):
            st.caption("Somente o cenário Atual é editável. A Referência permanece congelada.")
            if c.perspectiva == PERSPECTIVAS[0]:
                chave_q = chave("quantidade")
                def receber():
                    atual = st.session_state.m02_a_individual
                    if (geracao == st.session_state.get("m02_a_geracao",0)
                            and atual.comparacao is not None and atual.ciclo_comparacao == ciclo):
                        retorno = st.session_state.get(chave_q)
                        aplicar_quantidade(atual,retorno.get("evento") if retorno else None)
                componente_numero(key=chave_q,on_evento_change=receber,
                    data={"campo":"q_comparacao","rotulo":"Quantidade comum Q da comparação (unidades)",
                          "minimo":0,"maximo":dominio_comum(estado),"passo":0.1,"valor":c.q_fixa,
                          "seq":c.sequencia,"erro":c.erro})
                st.caption(f"Domínio comum: 0 ≤ Q ≤ {numero(dominio_comum(estado))}. Esta escolha não altera Q individual.")
            else:
                st.info("Decisões ótimas: cada cenário é avaliado em sua própria quantidade de lucro máximo. As quantidades podem ser diferentes; nenhuma escolha armazenada é substituída.",icon="ℹ️")
            parametros()
        with ferramenta("Visualização",":material/visibility:",chave("ferramenta_visualizacao")):
            st.radio("Foco dos dois gráficos",FOCOS,key=chave("foco"),
                     index=FOCOS.index(c.foco),on_change=foco)
            st.button("Restaurar visualização comparativa",on_click=agir,args=(restaurar,))
            modo_zoom = st.radio("Zoom comparativo",("Sincronizado","Independente"),key=chave("modo_zoom"))
            st.caption("Independente permite enquadramentos diferentes. Voltar a Sincronizado restaura a escala comum original.")
            roda = st.checkbox("Ativar zoom pela roda nos gráficos",key=chave("roda"))
            st.caption("Arraste para ampliar; Pan move. Sincronizado mantém o mesmo enquadramento; Independente permite vistas distintas. A roda é opcional para preservar a rolagem da página.")
    st.caption("Zoom "+modo_zoom.lower()+" · "+("mesmas escalas" if modo_zoom=="Sincronizado" else "atenção: os enquadramentos podem diferir; comparação visual direta de escalas limitada")+" · curvas nos domínios próprios.")
    figuras, contexto = graficos_comparacao(estado)
    GRAFICOS(key=chave("graficos"),data={"figuras":[f.to_json() for f in figuras],
                                     "contexto":contexto,"roda":roda,"sincronizado":modo_zoom=="Sincronizado"})

    for mensagem in (estado.aviso_dominio,c.aviso):
        if mensagem:
            st.warning("Atenção: "+mensagem,icon="⚠️")
    if estado.aviso_dominio or c.aviso:
        def dispensar(e):
            e.aviso_dominio = ""
            e.comparacao.aviso = ""
        st.button("Dispensar avisos de ajuste",on_click=agir,args=(dispensar,))
    r,a,deltas = resultados_comparacao(estado)
    dados = [("Quantidade (unidades)",r.curvas.q,a.curvas.q,deltas["Quantidade"]),
             ("Receita total (u.m.)",r.curvas.receita_total,a.curvas.receita_total,deltas["Receita total"]),
             ("Custo total (u.m.)",r.custo_total,a.custo_total,deltas["Custo total"]),
             ("Lucro (u.m.)",r.lucro,a.lucro,deltas["Lucro"])]
    def sinal(v):
        return ("+" if v>0 else "−" if v<0 else "")+numero(abs(v))
    st.caption("Δ = Atual − Referência. Sinais indicam direção matemática, sem julgamento de ganho ou perda.")
    st.table({"Grandeza":[v[0] for v in dados],"Referência":[numero(v[1]) for v in dados],
              "Atual":[numero(v[2]) for v in dados],"Δ Atual − Referência":[sinal(v[3]) for v in dados]})
    st.caption(f"Q individual preservada: {numero(estado.escolha.q)} unidades. Q fixa armazenada: {numero(c.q_fixa)} unidades.")
    st.info("Informação econômica: "+resumo_comparacao(estado),icon="ℹ️")
    from .interface_analise import renderizar_analise
    renderizar_analise(estado,chave)

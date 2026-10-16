"""Comparação controlada do Experimento A. Não implementa estruturas de mercado."""

from pathlib import Path
import streamlit as st
from plotly.offline import get_plotlyjs

from .estado_comparacao import (
    PERSPECTIVAS, aplicar_quantidade, dominio_comum, encerrar_comparacao,
    restaurar_parametros, resultados_comparacao, substituir_referencia,
)
from .explicacoes_comparacao import sintese_comparacao, resumo_comparacao
from .estado_individual import FOCOS, Escolha
from .explicacoes_individual import (
    numero, condicoes_excepcionais, GRUPOS_MATEMATICOS, IDEIAS,
)
from .graficos_comparacao import graficos_comparacao

PASTA = Path(__file__).parent
# Usa o bundle da dependência Plotly instalada: sem CDN, downloads ou biblioteca
# adicional. Registrado uma vez; apenas dados das figuras mudam a cada rerun.
GRAFICOS = st.components.v2.component(
    "lce_m02_par_comparativo", isolate_styles=False,
    js=get_plotlyjs()+"\n"+PASTA.joinpath("graficos_comparacao.js").read_text(encoding="utf-8"),
    css=PASTA.joinpath("graficos_comparacao.css").read_text(encoding="utf-8"),
)


def renderizar_comparacao(estado, componente_numero):
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

    st.subheader("Comparação controlada de cenários")
    st.caption("Os parâmetros acima pertencem somente ao cenário Atual. A referência permanece congelada.")
    with st.expander("Parâmetros da referência congelada"):
        p = c.referencia
        st.write(f"a={numero(p.a)} · b={numero(p.b)} · c={numero(p.c)} · s={numero(p.s)} · CF={numero(p.cf)} u.m.")
    with st.container(horizontal=True):
        def pedir_substituicao(e):
            e.comparacao.substituindo = True
        st.button("Substituir referência", on_click=agir,args=(pedir_substituicao,))
        st.button("Restaurar parâmetros padrão",on_click=agir,args=(restaurar_parametros,))
        st.button("Encerrar comparação",on_click=agir,args=(encerrar_comparacao,))
    if c.substituindo:
        st.info("Confirmar a substituição dos cinco parâmetros da referência pelos atuais? Quantidades escolhidas serão preservadas, salvo restrição do domínio comum.",icon="ℹ️")
        with st.container(horizontal=True):
            st.button("Confirmar substituição",on_click=agir,args=(substituir_referencia,True))
            st.button("Cancelar substituição",on_click=agir,args=(substituir_referencia,False))

    def perspectiva():
        st.session_state.m02_a_individual.comparacao.perspectiva = st.session_state[chave("perspectiva")]
    def foco():
        st.session_state.m02_a_individual.comparacao.foco = st.session_state[chave("foco")]
    st.radio("Perspectiva comparativa",PERSPECTIVAS,key=chave("perspectiva"),horizontal=True,
             index=PERSPECTIVAS.index(c.perspectiva),on_change=perspectiva)
    st.radio("Foco dos dois gráficos",FOCOS,key=chave("foco"),horizontal=True,
             index=FOCOS.index(c.foco),on_change=foco)
    def restaurar(e):
        e.comparacao.revisao += 1
    st.button("Restaurar visualização comparativa",on_click=agir,args=(restaurar,))
    roda = st.checkbox("Ativar zoom pela roda nos gráficos",key=chave("roda"))
    st.caption("Arraste uma região para ampliar. Pan move a visualização; Zoom volta à seleção. Qualquer gesto enquadra os dois gráficos igualmente, sem alterar as escolhas econômicas.")
    figuras, contexto = graficos_comparacao(estado)
    GRAFICOS(key=chave("graficos"),data={"figuras":[f.to_json() for f in figuras],
                                     "contexto":contexto,"roda":roda})

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
    with st.expander("Compreenda a comparação · opcional"):
        for titulo, resultado in (("Referência",r),("Atual",a)):
            for aviso in condicoes_excepcionais(Escolha(resultado.parametros,resultado.curvas.q)):
                st.write(f"{titulo}: {aviso}")
        nivel = st.radio("Nível de explicação da comparação",("Essencial","Econômica","Matemática"),
                         key=chave("nivel"),horizontal=True)
        st.write(sintese_comparacao(estado))
        if nivel != "Essencial":
            st.write("Quantidade fixa isola a avaliação na mesma produção. Decisões ótimas compara cada cenário em seu próprio máximo de lucro, dadas as hipóteses linear-quadráticas e o custo fixo inevitável. Alterações conjuntas não permitem atribuir toda a diferença a um único parâmetro.")
        if nivel == "Matemática":
            for titulo, formula in GRUPOS_MATEMATICOS:
                st.markdown(f"**{titulo}**")
                st.latex(formula)
            st.latex(r"\Delta X=X_{atual}-X_{ref},\quad Q_F\leq\min(a_{ref}/b_{ref},a_{atual}/b_{atual})")
    with st.expander("Ideias para investigar · opcional"):
        for ideia in IDEIAS:
            st.write("• "+ideia)

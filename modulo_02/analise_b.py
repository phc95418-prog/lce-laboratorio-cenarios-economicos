"""Análises próprias dos três modos, sempre sobre parâmetros confirmados."""
from .estruturas_mercado import avaliar_mercados
from .estado_b import MODOS, regiao_ativa
from .explicacoes_individual import numero
from .analise_experimento_a import assinado, DIMENSOES, _latex
from .graficos_b import NOMES
from .formatacao_matematica import paragrafo, latex_operadores


def valor_regiao(e,r):
    area=regiao_ativa(e)
    escolhido=r.concorrencia if e.regime=="Concorrência" else r.monopolio
    return {"EC":escolhido.curvas.excedente_consumidor,"EP":escolhido.curvas.excedente_produtor,
            "DWL":r.decomposicao.peso_morto,"T":r.decomposicao.transferencia,
            "L_C":r.decomposicao.perda_consumidor,"L_P":r.decomposicao.perda_produtor}[area]


def analise_b(e):
    p=e.confirmado
    r=avaliar_mercados(p)
    c,m=r.concorrencia,r.monopolio
    d=r.decomposicao
    preco=lambda x:"não aplicável" if x is None else numero(x)+" u.m./unidade"
    leitura=[f"Concorrência: Q_C={numero(c.curvas.q)} unidades e P_C={preco(c.preco_transacao)}. Monopólio: Q_M={numero(m.curvas.q)} unidades e P_M={preco(m.preco_transacao)}."]
    propriedades=[
        f"Domínio gráfico confirmado: 0 ≤ Q ≤ {numero(p.q_max)} unidades; b>0, s>0. Os dois regimes usam a mesma demanda e os mesmos custos agregados.",
        "Custos agregados comparáveis pressupõem unidades produtivas equivalentes, tecnologia e preços de insumos invariantes, custos separáveis e ausência de custos de reorganização. Concorrência impõe tomada de preço; não há oligopólio, entrada/saída ou dinâmica.",
        "Os resultados são contrafactuais teóricos de equilíbrio parcial. Não são previsões de fusões reais, de justiça distributiva ou de eficiência dinâmica.",
    ]
    a,b,c0,s=(_latex(getattr(p,k)) for k in ("a","b","c","s"))
    formulas=[("Funções comuns — coeficientes confirmados",rf"\begin{{aligned}}P_D(Q)&={a}-({b})Q\\CMg(Q)&={c0}+({s})Q\\RMg(Q)&={a}-2({b})Q\end{{aligned}}")]
    if e.modo==MODOS[0]:
        leitura.append("A diferença entre C e M decorre da regra de decisão, mantendo condições produtivas e demanda equivalentes. C e M são mostrados simultaneamente sobre a demanda quando há comércio.")
        for nome,v in (("Q",r.diferencas.quantidade),("P",r.diferencas.preco)):
            leitura.append(f"Δ{nome}=Monopólio−Concorrência: "+("não aplicável" if v.absoluta is None else assinado(v.absoluta))+"; percentual sobre a base competitiva: "+("não aplicável" if v.percentual is None else assinado(v.percentual)+"%")+".")
        formulas.append(("Equilíbrios restritos e diferenças",rf"\begin{{aligned}}Q_C&=\max(0,\frac{{{a}-{c0}}}{{{b}+{s}}})\\Q_M&=\max(0,\frac{{{a}-{c0}}}{{2({b})+{s}}})\\P_r&=P_D(Q_r)\quad(Q_r>0)\\\Delta Q&=Q_M-Q_C,\quad\Delta P=P_M-P_C\end{{aligned}}"))
    elif e.modo==MODOS[1]:
        leitura.append("O monopolista internaliza a redução do preço uniforme sobre as unidades vendidas: RMg(Q)=P_D(Q)−bQ. No equilíbrio competitivo, a condição preço-custo marginal decorre da tomada de preços e do equilíbrio de mercado.")
        if p.a>p.c:
            leitura.append(f"Em Q_M={numero(m.curvas.q)}, RMg={numero(m.curvas.receita_marginal)} e CMg={numero(m.curvas.custo_marginal)} u.m./unidade. P_M={numero(m.preco_transacao)} está na demanda, acima dessa ordenada marginal. A diferença P_M−CMg(Q_M)=bQ_M={numero(p.b*m.curvas.q)} u.m./unidade.")
        formulas.append(("Condições interiores — somente a>c",r"\begin{aligned}P_C&=CMg(Q_C)\\RMg(Q_M)&=CMg(Q_M)\\P_M&=P_D(Q_M)>CMg(Q_M)\\P_D(Q)-RMg(Q)&=bQ\end{aligned}"))
    else:
        area=regiao_ativa(e)
        leitura.append(f"Região ativa: {area} · {NOMES[area]} = {numero(valor_regiao(e,r))} u.m. "+("Comparação entre regimes." if area not in ("EC","EP") else "Regime: "+e.regime+"."))
        leitura.append(f"ΔEC={assinado(r.diferencas.excedente_consumidor.absoluta)}, ΔEP={assinado(r.diferencas.excedente_produtor.absoluta)} e ΔET={assinado(r.diferencas.excedente_total.absoluta)} u.m., sempre Monopólio−Concorrência.")
        leitura.append(f"T={numero(d.transferencia)}, L_C={numero(d.perda_consumidor)}, L_P={numero(d.perda_produtor)} e DWL={numero(d.peso_morto)} u.m. T redistribui excedente sobre as unidades ainda vendidas; não é perda líquida de eficiência. L_C e L_P representam perdas nas unidades não comercializadas.")
        if p.b!=p.s and c.curvas.q>0:
            leitura.append("b≠s: L_C e L_P são diferentes. Não há divisão meio a meio presumida.")
        formulas += [("Excedentes — r∈{C,M}",r"\begin{aligned}EC_r&=\int_0^{Q_r}[P_D(x)-P_r]dx=\frac b2 Q_r^2\\EP_r&=\int_0^{Q_r}[P_r-CMg(x)]dx\\&=(a-c)Q_r-(b+s/2)Q_r^2\\ET_r&=EC_r+EP_r\end{aligned}"),
                     ("Perda e decomposição",r"\begin{aligned}\Delta Q_+&=Q_C-Q_M\\DWL&=\int_{Q_M}^{Q_C}[P_D(x)-CMg(x)]dx\\&=\frac{b+s}{2}(\Delta Q_+)^2=L_C+L_P\\T&=(P_M-P_C)Q_M\quad(a>c)\\L_C&=\frac b2(\Delta Q_+)^2,\quad L_P=\frac s2(\Delta Q_+)^2\\\Delta EC&=-T-L_C,\quad\Delta EP=T-L_P\\\Delta ET&=-DWL\end{aligned}")]
        propriedades += [
            "EC mede excedente dos consumidores ao preço uniforme; EP é receita menos custo variável, não automaticamente lucro líquido de encargos fixos. B não contém controle de CF.",
            f"Sob custos fixos agregados idênticos nos dois regimes, a diferença de lucro econômico líquido coincide com a de excedente do produtor: Π_M−Π_C=EP_M−EP_C={assinado(r.diferencas.excedente_produtor.absoluta)} u.m. Isso não iguala seus níveis nem é previsão sobre mercados reais.",
            "ET é excedente monetário agregado, com igual peso por unidade monetária. Sua interpretação como bem-estar requer hipóteses como preferências quase lineares, ausência de efeitos-renda relevantes e custos de oportunidade pertinentes. Não mede equidade.",
            "O gráfico destaca uma única região; o balanço numérico não implica sobreposição das áreas. Ao alternar regime com parâmetros fixos, os eixos são preservados.",
        ]
        formulas.append(("Lucro e excedente — somente sob encargos fixos agregados idênticos",
            r"\Pi_M-\Pi_C=EP_M-EP_C\quad(F_M=F_C)"))
    if p.a>p.c:
        propriedades.append("a>c: 0<Q_M<Q_C, P_M>P_C. A quantidade competitiva maximiza o excedente monetário neste modelo; isso não é uma conclusão distributiva universal.")
    else:
        leitura.insert(0,"Sem comércio de equilíbrio: Q_C=Q_M=0; preços transacionados e percentuais com base zero não se aplicam. EC=EP=ET=DWL=T=L_C=L_P=0.")
        propriedades.append("a=c: RMg(0)=CMg(0) é igualdade na fronteira, não ótimo interior nem transação." if p.a==p.c else "a<c: RMg(0)<CMg(0); não há interseção ótima admissível. Preço competitivo referencial pode não ser único; não há preço realizado.")
        propriedades.append("DWL=0 na ausência de comércio não demonstra equivalência econômica geral entre as estruturas.")
    mudaram=[k for k in ("a","b","c","s") if getattr(e.anterior,k)!=getattr(p,k)]
    if len(mudaram)>1:
        leitura.append("Última confirmação: mudanças simultâneas em "+", ".join(mudaram)+". Não há decomposição causal por parâmetro; os dois regimes foram recalculados sob as mesmas condições.")
    return {"leitura":leitura,"formulas":formulas,"propriedades":propriedades}


def renderizar_analise_b(e,chave):
    import streamlit as st
    with st.expander("Análise econômica e matemática",key=chave("analise")):
        if e.em_interacao:
            st.info("Gráficos e indicadores acompanham a interação. A análise será consolidada ao concluir; o texto anterior fica suspenso.",icon="ℹ️")
            return
        dados=analise_b(e)
        st.caption("Três dimensões opcionais. Conteúdo consolidado ao término da interação, sobre valores internos confirmados.")
        for aba,campo in zip(st.tabs(DIMENSOES),("leitura","formulas","propriedades")):
            with aba:
                for item in dados[campo]:
                    if campo=="formulas":
                        st.markdown("**"+item[0]+"**");st.latex(latex_operadores(item[1]))
                    else: paragrafo(item)

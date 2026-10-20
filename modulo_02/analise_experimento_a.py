"""Análises determinísticas do adendo ANA-01–12, sem alterar o motor.

Valores completos entram no motor; formatação ocorre somente na saída.
As duas bases temporais vêm dos contratos existentes de estado confirmado.
"""

from .modelo_firma import avaliar_firma, calcular_otimos
from .estado_comparacao import resultados_comparacao
from .explicacoes_individual import (
    numero, mensagem_quantidade, mensagem_marginal, condicoes_excepcionais,
)
from .estado_individual import Escolha

DIMENSOES = ("Leitura econômica", "Estrutura matemática", "Propriedades e limites")

def assinado(valor):
    return ("+" if valor>0 else "−" if valor<0 else "")+numero(abs(valor))


def variacao(parametros_antes, parametros_agora):
    campos = ("a", "b", "c", "s", "cf")
    alterados = [k for k in campos if getattr(parametros_antes,k) != getattr(parametros_agora,k)]
    if not alterados:
        return "Os parâmetros coincidem com a base de comparação. Uma diferença de quantidade não é uma mudança das funções econômicas."
    if len(alterados) > 1:
        return ("Mudanças simultâneas em "+", ".join(k.upper() if k=="cf" else k for k in alterados)+
                ": os resultados refletem efeitos conjuntos. Não há decomposição que atribua a diferença a uma variável isolada.")
    k = alterados[0]
    if k == "cf":
        delta = parametros_agora.cf-parametros_antes.cf
        return (f"Variação isolada de CF: ΔCF={assinado(delta)} u.m. Para qualquer Q comum, ΔCT=ΔCF e Δπ=−ΔCF. "
                "RT, CMg e Q_M permanecem invariantes. Isso compara as funções na mesma quantidade, não uma decisão de fechamento.")
    qr_antes = calcular_otimos(parametros_antes).q_lucro
    qr_agora = calcular_otimos(parametros_agora).q_lucro
    efeito = {
        "a":"Um a maior desloca a demanda inversa e a receita marginal para cima; no interior, ∂Q_M/∂a=1/(2b+s)>0.",
        "b":"Um b maior torna a demanda mais inclinada; no interior, ∂Q_M/∂b=−2(a−c)/(2b+s)²<0. b não é uma elasticidade constante.",
        "c":"Um c maior desloca CMg para cima; no interior, ∂Q_M/∂c=−1/(2b+s)<0. Quando c alcança ou supera a, o máximo fica em Q=0.",
        "s":"Um s maior eleva a inclinação de CMg; no interior, ∂Q_M/∂s=−(a−c)/(2b+s)²<0.",
    }[k]
    return (f"Variação isolada de {k}: {numero(getattr(parametros_antes,k))} → {numero(getattr(parametros_agora,k))}. "
            f"Q_M: {numero(qr_antes)} → {numero(qr_agora)} unidades. "+efeito+
            " Essas relações mantêm os demais parâmetros constantes; a fronteira exige a solução restrita.")


def _latex(v):
    texto = str(int(v)) if v == int(v) else repr(float(v))
    if "e" in texto:
        mantissa,expoente = texto.split("e")
        return mantissa+ r"\times10^{"+str(int(expoente))+"}"
    return texto


def analisar_resultado(r):
    p, c = r.parametros, r.curvas
    escolha = Escolha(p,c.q)
    leitura = [
        f"Q avaliada={numero(c.q)} unidades; RT={numero(c.receita_total)}, CT={numero(r.custo_total)} e π={numero(r.lucro)} u.m.",
        mensagem_quantidade(escolha),
        f"Q_R={numero(r.otimos.q_receita)} e Q_M={numero(r.otimos.q_lucro)} unidades: máximos de receita e lucro são critérios distintos.",
        f"RMg={numero(c.receita_marginal)}, CMg={numero(c.custo_marginal)} e RMg−CMg={numero(r.diferenca_marginal)} u.m./unidade. "+mensagem_marginal(escolha),
    ]
    if r.classificacao == "muito_proxima":
        leitura.append("Muito próximo é a faixa relativa de até 1% de Q_M>0; não significa igualdade computacional nem RMg−CMg=0.")
    elif r.classificacao == "otima":
        leitura.append("A classificação de Q usa equivalência computacional relativa; o sinal da diferença marginal é calculado independentemente, sem arredondar a escolha.")
    if c.q == 0:
        leitura.append("Q=0: só há variações admissíveis para a direita; P_D(0) é intercepto, sem preço realizado ou transação.")
    elif c.q == p.q_max:
        leitura.append("Q=Qmax: só há variações admissíveis para a esquerda. A curva de demanda tem preço zero neste limite; nenhuma curva é extrapolada além dele.")
    else:
        leitura.append("No interior admissível, RMg−CMg é a derivada do lucro: sinal positivo/negativo descreve aumento/redução local, sem prescrever a quantidade escolhida.")
    propriedades = condicoes_excepcionais(escolha)
    propriedades += [
        f"Domínio atual: 0 ≤ Q ≤ {numero(p.q_max)} unidades; a e c em u.m./unidade; b e s em u.m./unidade²; CF em u.m.",
        "Demanda inversa linear, preço uniforme, custo variável quadrático e custo fixo comprometido e inevitável no horizonte corrente. Não há escolha endógena de operar, entrada, saída ou custos de ativação.",
        "CF é o encargo fixo imputado ao período. Lucro econômico requer custos de oportunidade relevantes; gasto histórico irrecuperável sem oportunidade atual não integra o lucro incremental da decisão corrente.",
        "RT é estritamente côncava (−2b<0) e π é estritamente côncava (−(2b+s)<0). Seus máximos restritos são globais e únicos neste domínio. São propriedades do modelo, não previsões empíricas universais.",
    ]
    if p.a > p.c:
        propriedades.append("a>c: Q_M é interior e satisfaz RMg=CMg. Como s>0 e c≥0, Q_M<Q_R; maximizar receita não maximiza lucro.")
    elif p.a == p.c:
        propriedades.append("a=c: Q_M=0, RMg(0)=CMg(0). É máximo de fronteira; a igualdade na origem não é ótimo interior. π(0)=−CF.")
    else:
        propriedades.append("a<c: Q_M=0 e RMg(0)<CMg(0), sem interseção marginal admissível. Uma produção positiva continua sendo exploração hipotética legítima, não uma decisão maximizadora.")
    a,b,c0,s,cf = (_latex(getattr(p,k)) for k in ("a","b","c","s","cf"))
    formulas = [
        ("Demanda e receita — parâmetros do cenário",rf"\begin{{aligned}}P_D(Q)&={a}-({b})Q\\RT(Q)&=({a})Q-({b})Q^2\\RMg(Q)&={a}-2({b})Q\end{{aligned}}"),
        ("Custos e lucro",rf"\begin{{aligned}}CV(Q)&=({c0})Q+\frac{{{s}}}{{2}}Q^2\\CT(Q)&={cf}+CV(Q)\\CMg(Q)&={c0}+({s})Q\\\pi(Q)&=RT(Q)-CT(Q)\end{{aligned}}"),
        ("Soluções restritas e concavidade",rf"\begin{{aligned}}Q_R&=\frac{{{a}}}{{2({b})}}\\Q_M&=\max\!\left(0,\frac{{{a}-{c0}}}{{2({b})+{s}}}\right)\\\pi'(Q)&=RMg(Q)-CMg(Q)\\\pi''(Q)&=-[2({b})+{s}]<0\\0&\leq Q\leq\frac{{{a}}}{{{b}}}\end{{aligned}}"),
    ]
    return {"leitura":leitura,"formulas":formulas,"propriedades":propriedades}


def analise_individual(estado):
    r = avaliar_firma(estado.confirmado.q,estado.confirmado.parametros)
    dados = analisar_resultado(r)
    dados["leitura"].append("Base: última edição confirmada. "+variacao(estado.anterior.parametros,r.parametros))
    dados["leitura"].append("Perspectiva: "+estado.perspectiva+". Q não ótimo é uma escolha legítima de investigação.")
    return [("Cenário individual",dados)]


def analise_comparativa(estado):
    r,a,delta = resultados_comparacao(estado,consolidada=True)
    resultados = [("Referência congelada",analisar_resultado(r)),("Atual",analisar_resultado(a))]
    texto = ("Base: Referência congelada → Atual; Δ=Atual−Referência, calculado antes da formatação. "
             +variacao(r.parametros,a.parametros))
    perspectiva = estado.comparacao.perspectiva
    if perspectiva == "Quantidade fixa":
        texto += f" Quantidade fixa: ambos avaliados em QF={numero(a.curvas.q)} unidades, no domínio comum."
    else:
        texto += (f" Decisões ótimas: Q_M da Referência={numero(r.curvas.q)} e do Atual={numero(a.curvas.q)} unidades. "
                  "Cada cenário é avaliado em seu próprio ótimo; diferenças de resultados combinam condições econômicas e, quando distintas, quantidades avaliadas. Não são efeitos a Q constante.")
    texto += f" ΔRT={assinado(delta['Receita total'])}, ΔCT={assinado(delta['Custo total'])} e Δπ={assinado(delta['Lucro'])} u.m.; ΔQ={assinado(delta['Quantidade'])} unidades."
    resultados[1][1]["leitura"].append(texto)
    resultados[1][1]["propriedades"].append(f"Domínio comum de QF: 0 ≤ QF ≤ {numero(min(r.parametros.q_max,a.parametros.q_max))} unidades. A perspectiva consulta os resultados sem regravar Q individual ou Q fixa; cada curva termina em seu próprio Qmax.")
    return resultados

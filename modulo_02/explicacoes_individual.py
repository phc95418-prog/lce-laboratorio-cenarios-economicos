"""Catálogo determinístico de A individual (TXT/MSG da v0.4)."""

from .estado_individual import Escolha, EstadoIndividual
from .modelo_firma import avaliar_firma


def numero(valor: float) -> str:
    # Não transformar um valor não nulo em um zero aparente.
    if valor != 0 and abs(valor) < 0.005:
        return f"{valor:.6g}".replace(".", ",").replace("e-", "e−")
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mensagem_quantidade(escolha: Escolha) -> str:
    r = avaliar_firma(escolha.q, escolha.parametros)
    if r.otimos.q_lucro == 0:
        return (
            "Neste cenário, não produzir é a quantidade que maximiza o lucro."
            if escolha.q == 0 else
            "A produção escolhida é admissível para investigação, mas não maximiza o lucro neste cenário."
        )
    return {
        "otima": "Esta quantidade maximiza o lucro nas condições do modelo.",
        "muito_proxima": "A quantidade escolhida está muito próxima daquela que maximiza o lucro.",
        "abaixo": "A quantidade escolhida está abaixo da que maximiza o lucro.",
        "acima": "A quantidade escolhida está acima da que maximiza o lucro.",
    }[r.classificacao]


def mensagem_marginal(escolha: Escolha) -> str:
    r = avaliar_firma(escolha.q, escolha.parametros)
    p = escolha.parametros
    if escolha.q == p.q_max:
        return "A quantidade está no limite superior do domínio; uma expansão além dele não é admissível."
    if escolha.q == 0 and p.a == p.c:
        return "RMg(0)=CMg(0): igualdade na fronteira, sem ótimo interior ou transação."
    if escolha.q == 0 and p.a < p.c:
        return "Na origem, RMg(0)<CMg(0); o máximo de lucro está na fronteira Q=0."
    if escolha.q == r.otimos.q_lucro and r.otimos.tipo_lucro == "interior":
        return (
            "No ótimo interior do modelo, receita marginal e custo marginal se igualam. "
            "A diferença numérica pode conter um resíduo de ponto flutuante."
        )
    if r.diferenca_marginal == 0:
        return "Neste ponto, receita marginal e custo marginal se igualam."
    if r.diferenca_marginal > 0:
        return "Neste ponto, um pequeno aumento da produção tende a elevar o lucro."
    return "Neste ponto, um pequeno aumento da produção tende a reduzir o lucro."


def sintese(estado: EstadoIndividual) -> str:
    if not estado.interagiu:
        return "Explore a quantidade produzida e os parâmetros para investigar receitas, custos e lucro."
    escolha = estado.confirmado
    principal = mensagem_marginal(escolha) if estado.perspectiva == "Análise Marginal" else mensagem_quantidade(escolha)
    anterior, atual = estado.anterior.parametros, escolha.parametros
    alterados = [nome for nome in ("a", "b", "c", "s", "cf") if getattr(anterior, nome) != getattr(atual, nome)]
    if alterados == ["cf"]:
        direcao = "aumentou e reduziu" if atual.cf > anterior.cf else "diminuiu e elevou"
        principal += f" O custo fixo {direcao} o lucro, sem alterar a quantidade ótima, as receitas ou as grandezas marginais."
    elif len(alterados) > 1:
        principal += " As diferenças refletem alterações simultâneas na demanda e/ou nos custos."
    return principal


def condicoes_excepcionais(escolha: Escolha) -> list[str]:
    r = avaliar_firma(escolha.q, escolha.parametros)
    avisos = []
    if escolha.q == 0:
        avisos.append("P_D(0) é o intercepto da curva de demanda; não existe preço efetivamente transacionado em Q=0.")
    if r.otimos.q_lucro == 0 and escolha.q > 0:
        avisos.append("Esta produção é uma exploração hipotética, não um equilíbrio nem uma decisão maximizadora de lucro.")
    if r.lucro < 0:
        avisos.append("Nesta quantidade, a receita total é inferior ao custo total. O custo fixo é inevitável; o modelo não decide o fechamento da firma.")
    if escolha.q == escolha.parametros.q_max:
        avisos.append("Q está no limite superior do domínio; não é possível ampliar a produção além dele.")
    return avisos


def resumo_economico(estado: EstadoIndividual) -> str:
    """Uma síntese principal; o catálogo completo permanece no aprofundamento."""
    escolha = estado.escolha
    r = avaliar_firma(escolha.q, escolha.parametros)
    if escolha.q == 0:
        if r.otimos.q_lucro == 0:
            return "Não produzir maximiza o lucro neste cenário; não há transação e o custo fixo comprometido permanece."
        return "Em Q=0, o preço indicado é o intercepto da demanda, sem transação efetiva."
    if r.otimos.q_lucro == 0:
        return "Esta produção hipotética é admissível para investigação, mas não maximiza o lucro."
    if escolha.q == escolha.parametros.q_max:
        return "A produção está no limite do domínio; uma expansão adicional não é admissível."
    if r.lucro < 0:
        return "A receita é inferior ao custo total. Isso não implica fechamento automático da firma."
    if not estado.interagiu:
        return sintese(estado)
    anterior, atual = estado.anterior.parametros, estado.confirmado.parametros
    alterados = [nome for nome in ("a", "b", "c", "s", "cf") if getattr(anterior,nome) != getattr(atual,nome)]
    if alterados == ["cf"]:
        direcao = "aumentou e reduziu" if atual.cf > anterior.cf else "diminuiu e elevou"
        return f"O custo fixo {direcao} o lucro, sem mudar a quantidade ótima."
    if len(alterados) > 1:
        return "As diferenças refletem alterações simultâneas na demanda e/ou nos custos."
    return mensagem_marginal(estado.confirmado) if estado.perspectiva == "Análise Marginal" else mensagem_quantidade(estado.confirmado)


def explicacao(escolha: Escolha, nivel: str) -> str:
    if nivel == "Essencial":
        return mensagem_quantidade(escolha) + " " + mensagem_marginal(escolha)
    if nivel == "Econômica":
        return (
            "A receita depende do preço uniforme indicado pela demanda inversa e da quantidade. "
            "Produzir mais reduz esse preço. O custo marginal cresce com a produção; "
            "o custo fixo comprometido desloca o custo total e o lucro, sem mudar a decisão marginal. "
            "A quantidade que maximiza a receita não é necessariamente a que maximiza o lucro. "
            "São propriedades deste modelo linear-quadrático, não previsões sobre firmas reais."
        )
    if nivel == "Matemática":
        return (
            "As expressões estão agrupadas abaixo. CF é um encargo comprometido: "
            "altera o lucro, mas não a quantidade que o maximiza. Em Q=0, "
            "o intercepto da demanda não é um preço efetivamente transacionado."
        )
    raise ValueError("Nível desconhecido.")


GRUPOS_MATEMATICOS = (
    ("Demanda e receita", r"\begin{aligned}P_D(Q)&=a-bQ\\RT(Q)&=aQ-bQ^2\\RMg(Q)&=a-2bQ\end{aligned}"),
    ("Custos e lucro", r"\begin{aligned}CV(Q)&=cQ+\frac{s}{2}Q^2\\CT(Q)&=CF+CV(Q)\\CMg(Q)&=c+sQ\\\pi(Q)&=RT(Q)-CT(Q)\end{aligned}"),
    ("Condições de maximização", r"\begin{aligned}Q_R&=\frac{a}{2b}\\Q_M&=\max\!\left(0,\frac{a-c}{2b+s}\right)\\a>c&\implies RMg(Q_M)=CMg(Q_M),\quad Q_M>0\end{aligned}"),
    ("Domínio e casos de fronteira", r"\begin{gathered}0\leq Q\leq\frac{a}{b}\\a=c\implies Q_M=0,\quad RMg(0)=CMg(0)\\a<c\implies Q_M=0,\quad RMg(0)<CMg(0)\end{gathered}"),
)
FORMULA_IGUALDADE = r"|Q-Q_M|\leq10^{-12}\max(|Q|,|Q_M|)"
FORMULA_PROXIMIDADE = r"Q_M>0,\quad\frac{|Q-Q_M|}{Q_M}\leq0{,}01"
TEXTO_PRECISAO = (
    "A igualdade computacional usa os valores internos finitos, sem piso absoluto. "
    "Se ambos são zero, a regra é satisfeita; Q=0 e Q_M>0 minúsculo não são equivalentes. "
    "Somente quando não há equivalência computacional se aplica a proximidade pedagógica de até 1%. "
    "Nenhuma regra arredonda Q nem transforma uma diferença marginal não nula em igualdade."
)


IDEIAS = (
    "O que acontece com receita e lucro quando a quantidade aumenta?",
    "Como uma mudança isolada do custo fixo afeta as curvas?",
    "A quantidade de receita máxima coincide com a de lucro máximo?",
    "Como demanda e custo marginal modificam a decisão de produção?",
)

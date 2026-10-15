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
            "P_D(Q)=a−bQ; RT(Q)=aQ−bQ²; CT(Q)=CF+cQ+(s/2)Q²; π(Q)=RT(Q)−CT(Q). "
            "RMg(Q)=a−2bQ; CMg(Q)=c+sQ. Domínio: 0≤Q≤a/b. "
            "Q_R=a/(2b); Q_M=max(0,(a−c)/(2b+s)). Em a=c, a igualdade marginal ocorre "
            "na fronteira; em a<c, não existe interseção ótima em Q≥0. "
            "Igualdade computacional usa |Q−Q_M|≤10⁻¹²·max(|Q|,|Q_M|); proximidade "
            "pedagógica de até 1% é distinta e só se aplica quando Q_M>0."
        )
    raise ValueError("Nível desconhecido.")


IDEIAS = (
    "O que acontece com receita e lucro quando a quantidade aumenta?",
    "Como uma mudança isolada do custo fixo afeta as curvas?",
    "A quantidade de receita máxima coincide com a de lucro máximo?",
    "Como demanda e custo marginal modificam a decisão de produção?",
)

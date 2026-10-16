"""Interpretações determinísticas: base congelada e prioridade de exceções."""

from .estado_individual import LIMITES, Escolha
from .estado_comparacao import resultados_comparacao
from .explicacoes_individual import condicoes_excepcionais


def sintese_comparacao(estado):
    r, a, _ = resultados_comparacao(estado, consolidada=True)
    alterados = [k for k in LIMITES if getattr(a.parametros,k) != getattr(r.parametros,k)]
    if len(alterados) > 1:
        return "As diferenças observadas refletem alterações simultâneas na demanda e/ou nos custos, em relação à referência congelada."
    if alterados == ["cf"]:
        direcao = "aumentou e reduziu" if a.parametros.cf > r.parametros.cf else "diminuiu e elevou"
        return f"Em relação à referência, o custo fixo {direcao} o lucro, sem alterar a quantidade ótima ou as receitas."
    if alterados:
        return f"A comparação usa a referência congelada; o parâmetro alterado é {alterados[0]}. Os resultados são condicionais às hipóteses do modelo."
    return "Os parâmetros atuais coincidem com a referência congelada; os cenários são avaliados pela mesma regra."


def resumo_comparacao(estado):
    referencia, atual, _ = resultados_comparacao(estado)
    # Apenas uma síntese principal. O catálogo e a explicação da variação
    # continuam disponíveis no aprofundamento, mesmo com uma exceção ativa.
    for titulo, resultado in (("Atual",atual),("Referência",referencia)):
        avisos = condicoes_excepcionais(Escolha(resultado.parametros,resultado.curvas.q))
        if avisos:
            return titulo+": "+avisos[0]
    return sintese_comparacao(estado)

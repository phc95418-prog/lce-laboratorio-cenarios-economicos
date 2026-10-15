"""EC-09/MSG-04: aceite analítico, igualdade e proximidade são distintos."""

from numbers import Real

from .contratos import ClasseQuantidade, Variacao
from .validacao import numero_finito


def atende_aceite_analitico(calculado: Real, esperado: Real) -> bool:
    calculado = numero_finito(calculado, "calculado")
    esperado = numero_finito(esperado, "esperado")
    return abs(calculado - esperado) <= 1e-9 + 1e-9 * abs(esperado)


def _quantidades(q: Real, q_otimo: Real) -> tuple[float, float]:
    q = numero_finito(q, "Q")
    q_otimo = numero_finito(q_otimo, "Q_M")
    if q < 0 or q_otimo < 0:
        raise ValueError("Q e Q_M devem ser não negativas.")
    return q, q_otimo


def quantidade_equivalente(q: Real, q_otimo: Real) -> bool:
    """Sem piso absoluto, sem alterar qualquer das quantidades."""
    q, q_otimo = _quantidades(q, q_otimo)
    return abs(q - q_otimo) <= 1e-12 * max(abs(q), abs(q_otimo))


def classificar_quantidade(q: Real, q_otimo: Real) -> ClasseQuantidade:
    q, q_otimo = _quantidades(q, q_otimo)
    if quantidade_equivalente(q, q_otimo):
        return "otima"
    if q_otimo > 0 and abs(q - q_otimo) / q_otimo <= 0.01:
        return "muito_proxima"
    return "abaixo" if q < q_otimo else "acima"


def calcular_variacao(
    atual: Real | None, referencia: Real | None, unidade: str
) -> Variacao:
    """Diferença matemática sem arredondar nem atribuir juízo ao sinal.

    Use None para base economicamente indefinida. Base negativa definida
    (por exemplo, lucro em A) não é confundida com uma base nula.
    """
    atual = None if atual is None else numero_finito(atual, "atual")
    referencia = None if referencia is None else numero_finito(referencia, "referência")
    if atual is None or referencia is None:
        return Variacao(None, None, unidade)
    delta = atual - referencia
    percentual = None if referencia == 0 else 100 * (delta / referencia)
    return Variacao(delta, percentual, unidade)

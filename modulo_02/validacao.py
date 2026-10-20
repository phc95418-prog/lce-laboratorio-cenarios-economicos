"""Domínios EC-01/02 da v0.4, independentes dos passos dos controles."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real


def numero_finito(valor: Real, nome: str) -> float:
    """Aceita números reais finitos; rejeita booleanos e texto numérico."""
    if isinstance(valor, bool) or not isinstance(valor, Real):
        raise ValueError(f"{nome} deve ser um número real finito.")
    try:
        convertido = float(valor)
    except (ValueError, OverflowError) as erro:
        raise ValueError(f"{nome} deve ser um número real finito.") from erro
    if not isfinite(convertido):
        raise ValueError(f"{nome} deve ser um número real finito.")
    return convertido


def _na_faixa(valor: Real, nome: str, minimo: float, maximo: float) -> float:
    convertido = numero_finito(valor, nome)
    if not minimo <= convertido <= maximo:
        raise ValueError(f"{nome} deve estar entre {minimo} e {maximo}.")
    return convertido


@dataclass(frozen=True)
class ParametrosMercado:
    """B: demanda (a,b), tecnologia agregada (c,s); sem custo fixo."""

    a: float = 100.0
    b: float = 1.0
    c: float = 20.0
    s: float = 1.0

    def __post_init__(self) -> None:
        for nome, minimo, maximo in (
            ("a", 60, 140), ("b", 0.5, 2), ("c", 0, 160), ("s", 0.25, 3)
        ):
            object.__setattr__(self, nome, _na_faixa(getattr(self, nome), nome, minimo, maximo))

    @property
    def q_max(self) -> float:
        """Limite econômico da exploração, em unidades."""
        return self.a / self.b


@dataclass(frozen=True)
class ParametrosFirma(ParametrosMercado):
    """A: acrescenta CF comprometido/inevitável, em u.m."""

    cf: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "cf", _na_faixa(self.cf, "CF", 0, 1600))


def validar_parametros(parametros: ParametrosMercado) -> None:
    if not isinstance(parametros, ParametrosMercado):
        raise TypeError("Use ParametrosMercado ou ParametrosFirma validados.")


def validar_quantidade(q: Real, parametros: ParametrosMercado) -> float:
    validar_parametros(parametros)
    return _na_faixa(q, "Q", 0, parametros.q_max)


def limitar_quantidade(q: Real, parametros: ParametrosMercado) -> float:
    """Clamp explícito ao novo domínio (A-03/C5), sem guardar estado anterior.

    Não é utilizado silenciosamente pelos cálculos: avaliar quantidade fora
    do domínio gera erro. A interface futura decidirá quando aplicar e avisar.
    """
    validar_parametros(parametros)
    q = numero_finito(q, "Q")
    if q < 0:
        raise ValueError("Q deve ser não negativa.")
    return min(q, parametros.q_max)

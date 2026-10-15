"""Resultados imutáveis. Metadado 'unidade' acompanha cada grandeza numérica.

Nenhum resultado é arredondado. None representa grandeza economicamente
indefinida; zero representa uma grandeza definida de valor zero.
"""

from dataclasses import dataclass, field
from typing import Literal

from .validacao import ParametrosFirma, ParametrosMercado


def grandeza(unidade: str):
    return field(metadata={"unidade": unidade})


TipoOtimo = Literal["interior", "fronteira_igualdade", "fronteira_sem_intersecao"]
ClasseQuantidade = Literal["otima", "muito_proxima", "abaixo", "acima"]


@dataclass(frozen=True)
class CurvasFirma:
    """Valores das funções em Q, não uma declaração de equilíbrio."""

    q: float = grandeza("unidades")
    preco_demanda: float = grandeza("u.m./unidade")
    receita_total: float = grandeza("u.m.")
    receita_marginal: float = grandeza("u.m./unidade")
    custo_variavel: float = grandeza("u.m.")
    custo_marginal: float = grandeza("u.m./unidade")
    excedente_consumidor: float = grandeza("u.m.")
    excedente_produtor: float = grandeza("u.m.")
    excedente_total: float = grandeza("u.m.")


@dataclass(frozen=True)
class OtimosFirma:
    q_receita: float = grandeza("unidades")
    q_lucro: float = grandeza("unidades")
    tipo_lucro: TipoOtimo


@dataclass(frozen=True)
class ResultadoFirma:
    parametros: ParametrosFirma
    curvas: CurvasFirma
    custo_total: float = grandeza("u.m.")
    lucro: float = grandeza("u.m.")
    preco_transacao: float | None = grandeza("u.m./unidade")
    otimos: OtimosFirma
    classificacao: ClasseQuantidade
    # Calculada das marginais, independentemente da classe da quantidade.
    diferenca_marginal: float = grandeza("u.m./unidade")


@dataclass(frozen=True)
class Variacao:
    """Atual−referência; percentual=100*absoluta/referência (não fração).

    Percentual é None se a base for zero ou uma grandeza não estiver definida.
    A unidade de 'absoluta' é explicitada em 'unidade_absoluta'.
    """

    absoluta: float | None
    percentual: float | None = grandeza("%")
    unidade_absoluta: str


@dataclass(frozen=True)
class ResultadoRegime:
    curvas: CurvasFirma
    preco_transacao: float | None = grandeza("u.m./unidade")


@dataclass(frozen=True)
class DecomposicaoBemEstar:
    reducao_quantidade: float = grandeza("unidades")
    transferencia: float = grandeza("u.m.")
    perda_consumidor: float = grandeza("u.m.")
    perda_produtor: float = grandeza("u.m.")
    peso_morto: float = grandeza("u.m.")


@dataclass(frozen=True)
class DiferencasMercados:
    """Todas as diferenças seguem monopólio−concorrência (EC-08)."""

    quantidade: Variacao
    preco: Variacao
    excedente_consumidor: Variacao
    excedente_produtor: Variacao
    excedente_total: Variacao


@dataclass(frozen=True)
class ResultadoMercados:
    parametros: ParametrosMercado
    concorrencia: ResultadoRegime
    monopolio: ResultadoRegime
    tipo_otimo_monopolio: TipoOtimo
    decomposicao: DecomposicaoBemEstar
    diferencas: DiferencasMercados

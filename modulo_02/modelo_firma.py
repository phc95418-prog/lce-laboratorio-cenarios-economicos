"""Motor puro da firma linear-quadrática (EC-02/04/06; Experimento A).

Cada chamada avalia o domínio e devolve valores internos sem formatação.
EP é calculado diretamente pela expressão econômica, evitando subtração
de RT e CV quase iguais próximo à fronteira a=c; lucro segue RT−CT.
"""

from numbers import Real

from .classificacao import classificar_quantidade
from .contratos import CurvasFirma, OtimosFirma, ResultadoFirma
from .validacao import (
    ParametrosFirma, ParametrosMercado, validar_parametros, validar_quantidade,
)


def calcular_otimos(parametros: ParametrosMercado) -> OtimosFirma:
    """Ótimos independem de CF; fronteiras não são soluções interiores."""
    validar_parametros(parametros)
    a, b, c, s = parametros.a, parametros.b, parametros.c, parametros.s
    tipo = (
        "interior" if a > c else
        "fronteira_igualdade" if a == c else "fronteira_sem_intersecao"
    )
    return OtimosFirma(a / (2 * b), max(0.0, (a - c) / (2 * b + s)), tipo)


def avaliar_curvas(q: Real, parametros: ParametrosMercado) -> CurvasFirma:
    """Funções comuns de A/B, inclusive marginais negativas e Q=0.

    P_D(0)=a é intercepto. Excedentes pressupõem preço uniforme P_D(Q);
    os resultados em uma escolha de A não são rotulados como equilíbrio.
    """
    q = validar_quantidade(q, parametros)
    a, b, c, s = parametros.a, parametros.b, parametros.c, parametros.s
    preco = a - b * q
    rt = a * q - b * q**2
    rmg = a - 2 * b * q
    cv = c * q + (s / 2) * q**2
    cmg = c + s * q
    ec = b * q**2 / 2
    ep = (a - c) * q - (b + s / 2) * q**2
    return CurvasFirma(q, preco, rt, rmg, cv, cmg, ec, ep, ec + ep)


def avaliar_firma(q: Real, parametros: ParametrosFirma) -> ResultadoFirma:
    """A: avalia Q escolhido, sem fechamento endógeno por lucro negativo.

    preco_transacao=None em Q=0; com Q>0 é o preço da produção hipotética
    escolhida, não necessariamente de uma decisão ótima.
    """
    if not isinstance(parametros, ParametrosFirma):
        raise TypeError("A exige ParametrosFirma, com CF explícito ou padrão zero.")
    curvas = avaliar_curvas(q, parametros)
    otimos = calcular_otimos(parametros)
    ct = parametros.cf + curvas.custo_variavel
    return ResultadoFirma(
        parametros, curvas, ct, curvas.receita_total - ct,
        curvas.preco_demanda if curvas.q > 0 else None,
        otimos, classificar_quantidade(curvas.q, otimos.q_lucro),
        curvas.receita_marginal - curvas.custo_marginal,
    )

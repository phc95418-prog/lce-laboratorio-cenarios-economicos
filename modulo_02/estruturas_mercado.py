"""B: regimes sob a mesma demanda e tecnologia; nenhuma dependência de CF."""

from .classificacao import calcular_variacao
from .contratos import (
    DecomposicaoBemEstar, DiferencasMercados, ResultadoMercados, ResultadoRegime,
)
from .modelo_firma import avaliar_curvas, calcular_otimos
from .validacao import ParametrosMercado


def avaliar_mercados(parametros: ParametrosMercado) -> ResultadoMercados:
    """Concorrência, monopólio, decomposição e diferenças M−C (EC-05/08).

    B aceita apenas seu contrato de quatro parâmetros. Importação pontual de
    A deve construir ParametrosMercado(a,b,c,s), sem carregar CF ou estado.
    """
    if type(parametros) is not ParametrosMercado:
        raise TypeError("B exige ParametrosMercado(a,b,c,s), sem CF.")
    otimos = calcular_otimos(parametros)
    qc = max(0.0, (parametros.a - parametros.c) / (parametros.b + parametros.s))
    qm = otimos.q_lucro
    c = avaliar_curvas(qc, parametros)
    m = avaliar_curvas(qm, parametros)
    concorrencia = ResultadoRegime(c, c.preco_demanda if qc > 0 else None)
    monopolio = ResultadoRegime(m, m.preco_demanda if qm > 0 else None)
    dq = qc - qm
    transferencia = parametros.b * dq * qm
    lc = parametros.b * dq**2 / 2
    lp = parametros.s * dq**2 / 2
    decomposicao = DecomposicaoBemEstar(dq, transferencia, lc, lp, lc + lp)
    diferencas = DiferencasMercados(
        calcular_variacao(qm, qc, "unidades"),
        calcular_variacao(monopolio.preco_transacao, concorrencia.preco_transacao, "u.m./unidade"),
        calcular_variacao(m.excedente_consumidor, c.excedente_consumidor, "u.m."),
        calcular_variacao(m.excedente_produtor, c.excedente_produtor, "u.m."),
        calcular_variacao(m.excedente_total, c.excedente_total, "u.m."),
    )
    return ResultadoMercados(
        parametros, concorrencia, monopolio, otimos.tipo_lucro, decomposicao, diferencas
    )

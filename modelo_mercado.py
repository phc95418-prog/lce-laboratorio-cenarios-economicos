"""LCE - Modulo 01: incidencia tributaria em equilibrio parcial.

O modelo utiliza as funcoes inversas lineares:
    P_demanda(Q) = a - b*Q
    P_oferta(Q)  = c + d*Q

Hipoteses principais: mercado competitivo, equilibrio parcial, curvas agregadas
estaticas e imposto especifico sobre cada unidade transacionada.

Os valores sao simulacoes teoricas, nao estimativas de mercados reais.
Referencia: Arquitetura Funcional e Matematica do LCE, versao 1.1.
"""

import math


def _numero_finito(valor, nome):
    """Verifica se uma entrada e um numero real finito."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{nome} deve ser um numero real.")
    try:
        numero = float(valor)
    except (OverflowError, ValueError):
        raise ValueError(f"{nome} deve ser um numero real finito.") from None
    if not math.isfinite(numero):
        raise ValueError(f"{nome} deve ser finito.")
    return numero


def validar_parametros(a, b, c, d, t):
    """Aplica as restricoes economicas da versao inicial do LCE."""
    a = _numero_finito(a, "a")
    b = _numero_finito(b, "b")
    c = _numero_finito(c, "c")
    d = _numero_finito(d, "d")
    t = _numero_finito(t, "t")

    if not a > c >= 0:
        raise ValueError("E necessario que a > c >= 0.")
    if b <= 0 or d <= 0:
        raise ValueError("As inclinacoes b e d devem ser positivas.")
    if t < 0:
        raise ValueError("O imposto t nao pode ser negativo.")
    return a, b, c, d, t


def parametros_por_elasticidades(p0, q0, elasticidade_demanda,
                                  elasticidade_oferta, t):
    """Converte a entrada exploratoria para os coeficientes lineares.

    elasticidade_demanda: valor absoluto da elasticidade no equilibrio inicial.
    elasticidade_oferta: elasticidade pontual no equilibrio inicial (>= 1).
    """
    p0 = _numero_finito(p0, "p0")
    q0 = _numero_finito(q0, "q0")
    ed = _numero_finito(elasticidade_demanda, "elasticidade_demanda")
    es = _numero_finito(elasticidade_oferta, "elasticidade_oferta")
    t = _numero_finito(t, "t")

    if p0 <= 0 or q0 <= 0:
        raise ValueError("Preco e quantidade iniciais devem ser positivos.")
    if ed <= 0:
        raise ValueError("A elasticidade da demanda (em modulo) deve ser positiva.")
    if es < 1:
        raise ValueError("Este modelo linear, com c >= 0, exige elasticidade da oferta >= 1.")

    b = p0 / (ed * q0)
    d = p0 / (es * q0)
    a = p0 + b * q0
    c = p0 - d * q0

    # A fronteira es=1 implica c=0; removemos residuo do arredondamento.
    if es == 1:
        c = 0.0
    elif c < 0 and math.isclose(c, 0.0, abs_tol=1e-12):
        c = 0.0

    return dict(zip(("a", "b", "c", "d", "t"), validar_parametros(a, b, c, d, t)))


def excedente_total_em_quantidade(a, b, c, d, quantidade):
    """Integral da diferenca entre demanda e custo marginal ate a quantidade Q.

    A expressao pode ser usada no intervalo economico 0 <= Q <= Q0.
    """
    a, b, c, d, _ = validar_parametros(a, b, c, d, 0)
    quantidade = _numero_finito(quantidade, "quantidade")
    q0 = (a - c) / (b + d)
    if quantidade < 0 or quantidade > q0:
        raise ValueError("A quantidade deve pertencer ao intervalo [0, Q0].")
    return (a - c) * quantidade - 0.5 * (b + d) * quantidade ** 2


def simular_mercado(a, b, c, d, t):
    """Calcula o equilibrio sem imposto e o equilibrio tributado.

    Retorna um dicionario que pode ser usado pelos graficos e pelos testes.
    Valores None indicam resultados sem interpretacao economica no caso dado.
    """
    a, b, c, d, t = validar_parametros(a, b, c, d, t)

    # 1. Equilibrio competitivo sem tributacao.
    q0 = (a - c) / (b + d)
    p0 = c + d * q0
    if q0 <= 0 or not math.isfinite(p0):
        raise ValueError("Parametros numericamente extremos: nao ha equilibrio calculavel.")

    ec0 = b * q0 ** 2 / 2
    ep0 = d * q0 ** 2 / 2
    et0 = ec0 + ep0

    # 2. Equilibrio com imposto e limite de encerramento do comercio.
    imposto_proibitivo = t >= (a - c)
    qt = 0.0 if imposto_proibitivo else (a - c - t) / (b + d)
    qt = max(0.0, qt)
    ha_transacoes = qt > 0

    if ha_transacoes:
        pc = a - b * qt
        pp = c + d * qt
        aumento_preco_consumidor = pc - p0
        queda_preco_produtor = p0 - pp
    else:
        pc = None
        pp = None
        aumento_preco_consumidor = None
        queda_preco_produtor = None

    # 3. Elasticidades iniciais e coeficientes teoricos de repasse.
    elasticidade_demanda = -p0 / (b * q0)
    elasticidade_oferta = p0 / (d * q0)
    fracao_consumidor_potencial = b / (b + d)
    fracao_produtor_potencial = d / (b + d)

    # Com imposto zero nao existe carga tributaria realizada.
    fracao_consumidor_efetiva = (
        fracao_consumidor_potencial if t > 0 and ha_transacoes else None
    )
    fracao_produtor_efetiva = (
        fracao_produtor_potencial if t > 0 and ha_transacoes else None
    )

    # 4. Bem-estar do mercado e arrecadacao.
    ec = b * qt ** 2 / 2
    ep = d * qt ** 2 / 2
    arrecadacao = t * qt
    et = ec + ep + arrecadacao
    # A expressao abaixo permanece valida com t acima do limite proibitivo.
    peso_morto = (b + d) * (q0 - qt) ** 2 / 2

    # Erros por transbordamento nao devem chegar silenciosamente a interface.
    resultados = (q0, p0, qt, ec0, ep0, et0, ec, ep, arrecadacao,
                  et, peso_morto, elasticidade_demanda, elasticidade_oferta)
    if not all(math.isfinite(valor) for valor in resultados):
        raise ValueError("Parametros muito extremos para os calculos em ponto flutuante.")

    return {
        "a": a, "b": b, "c": c, "d": d, "t": t,
        "q0": q0, "p0": p0,
        "qt": qt, "pc": pc, "pp": pp,
        "ha_transacoes": ha_transacoes,
        "reducao_quantidade": q0 - qt,
        "aumento_preco_consumidor": aumento_preco_consumidor,
        "queda_preco_produtor": queda_preco_produtor,
        "elasticidade_demanda_0": elasticidade_demanda,
        "elasticidade_oferta_0": elasticidade_oferta,
        "fracao_consumidor_potencial": fracao_consumidor_potencial,
        "fracao_produtor_potencial": fracao_produtor_potencial,
        "fracao_consumidor_efetiva": fracao_consumidor_efetiva,
        "fracao_produtor_efetiva": fracao_produtor_efetiva,
        "ec0": ec0, "ep0": ep0, "et0": et0,
        "ec": ec, "ep": ep,
        "arrecadacao": arrecadacao,
        "et": et, "peso_morto": peso_morto,
        "perda_ec": ec0 - ec,
        "perda_ep": ep0 - ep,
    }

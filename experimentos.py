"""Cenarios didaticos documentados na arquitetura v1.1 do LCE.

Os cenarios A isolam a distribuicao da incidencia tributaria.
Os cenarios B isolam a resposta da quantidade e do peso morto.
Os valores sao hipoteticos e os resultados sao calculados no modelo_mercado.
"""

from modelo_mercado import parametros_por_elasticidades, simular_mercado


def cenarios_experimento_a(imposto=20.0):
    """P0=60, Q0=40 e b+d=2 em todos os cenarios."""
    return [
        ("A · Simétrico", dict(a=100, b=1, c=20, d=1, t=imposto)),
        ("B · Demanda menos elástica", dict(a=120, b=1.5, c=40, d=0.5, t=imposto)),
        ("C · Oferta menos elástica", dict(a=80, b=0.5, c=0, d=1.5, t=imposto)),
    ]


def cenarios_experimento_b(imposto=20.0):
    """P0=60, Q0=40 e b=d; elasticidades iguais dentro de cada cenario."""
    return [
        (f"B1 · Elasticidade 3,0", parametros_por_elasticidades(60, 40, 3, 3, imposto)),
        (f"B2 · Elasticidade 1,5", parametros_por_elasticidades(60, 40, 1.5, 1.5, imposto)),
        (f"B3 · Elasticidade 1,2", parametros_por_elasticidades(60, 40, 1.2, 1.2, imposto)),
    ]


def resultados_cenarios(cenarios):
    """Retorna pares (nome, resultado), sem implementar novas equacoes."""
    return [(nome, simular_mercado(**parametros)) for nome, parametros in cenarios]

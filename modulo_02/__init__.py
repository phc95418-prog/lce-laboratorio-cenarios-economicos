"""API matemática do Módulo 02, conforme especificação funcional v0.4.

Unidades hipotéticas: quantidades em unidades, preços/marginais em
u.m./unidade e totais em u.m. Percentuais retornados em %, não frações.
Sem interface, estado de sessão, gráficos ou dependências externas.
"""

from .classificacao import (
    atende_aceite_analitico, calcular_variacao, classificar_quantidade,
    quantidade_equivalente,
)
from .estruturas_mercado import avaliar_mercados
from .modelo_firma import avaliar_curvas, avaliar_firma, calcular_otimos
from .validacao import ParametrosFirma, ParametrosMercado, limitar_quantidade, validar_quantidade

__all__ = [
    "ParametrosFirma", "ParametrosMercado", "avaliar_curvas", "avaliar_firma",
    "calcular_otimos", "avaliar_mercados", "validar_quantidade", "limitar_quantidade",
    "atende_aceite_analitico", "quantidade_equivalente", "classificar_quantidade",
    "calcular_variacao",
]

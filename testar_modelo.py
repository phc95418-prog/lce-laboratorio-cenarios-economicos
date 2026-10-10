"""Testes verificaveis do Modulo 01 do LCE. Execute: python testar_modelo.py"""

import math
import random
import unittest

from modelo_mercado import (
    simular_mercado, parametros_por_elasticidades,
    excedente_total_em_quantidade,
)


class TestesModeloMercado(unittest.TestCase):

    def assert_igual(self, encontrado, esperado):
        self.assertTrue(math.isclose(encontrado, esperado, rel_tol=1e-10, abs_tol=1e-10),
                        f"Encontrado: {encontrado}, esperado: {esperado}")

    def test_referencia_sem_imposto(self):
        r = simular_mercado(100, 1, 20, 1, 0)
        self.assert_igual(r["q0"], 40)
        self.assert_igual(r["qt"], 40)
        self.assert_igual(r["pc"], 60)
        self.assert_igual(r["pp"], 60)
        self.assert_igual(r["arrecadacao"], 0)
        self.assert_igual(r["peso_morto"], 0)
        self.assertIsNone(r["fracao_consumidor_efetiva"])
        self.assert_igual(r["fracao_consumidor_potencial"], 0.5)

    def test_referencia_com_imposto(self):
        r = simular_mercado(100, 1, 20, 1, 20)
        valores = dict(q0=40, p0=60, qt=30, pc=70, pp=50,
                       ec0=800, ep0=800, et0=1600,
                       ec=450, ep=450, arrecadacao=600,
                       et=1500, peso_morto=100)
        for campo, valor in valores.items():
            self.assert_igual(r[campo], valor)
        self.assert_igual(r["fracao_consumidor_efetiva"], 0.5)
        self.assert_igual(r["fracao_produtor_efetiva"], 0.5)

    def test_sem_transacoes_no_limiar(self):
        r = simular_mercado(100, 1, 20, 1, 80)
        self.assertFalse(r["ha_transacoes"])
        self.assert_igual(r["qt"], 0)
        self.assertIsNone(r["pc"])
        self.assertIsNone(r["pp"])
        self.assertIsNone(r["fracao_consumidor_efetiva"])
        self.assert_igual(r["arrecadacao"], 0)
        self.assert_igual(r["peso_morto"], 1600)

    def test_imposto_acima_do_limiar(self):
        r = simular_mercado(100, 1, 20, 1, 90)
        self.assert_igual(r["qt"], 0)
        self.assert_igual(r["peso_morto"], 1600)
        self.assert_igual(r["et"], 0)
        self.assertIsNone(r["pc"])

    def test_experimento_a(self):
        cenarios = [
            (100, 1, 20, 1, 0.50, 70, 50),
            (120, 1.5, 40, 0.5, 0.75, 75, 55),
            (80, 0.5, 0, 1.5, 0.25, 65, 45),
        ]
        for a, b, c, d, fracao, pc, pp in cenarios:
            r = simular_mercado(a, b, c, d, 20)
            for campo, valor in dict(q0=40, p0=60, qt=30,
                                     arrecadacao=600, peso_morto=100).items():
                self.assert_igual(r[campo], valor)
            self.assert_igual(r["fracao_consumidor_efetiva"], fracao)
            self.assert_igual(r["pc"], pc)
            self.assert_igual(r["pp"], pp)

    def test_experimento_b(self):
        for elasticidade, qt, receita, peso_morto in (
            (3, 20, 400, 200), (1.5, 30, 600, 100), (1.2, 32, 640, 80)
        ):
            parametros = parametros_por_elasticidades(60, 40, elasticidade, elasticidade, 20)
            r = simular_mercado(**parametros)
            self.assert_igual(r["p0"], 60)
            self.assert_igual(r["q0"], 40)
            self.assert_igual(r["qt"], qt)
            self.assert_igual(r["arrecadacao"], receita)
            self.assert_igual(r["peso_morto"], peso_morto)
            self.assert_igual(r["elasticidade_oferta_0"], elasticidade)
            self.assert_igual(abs(r["elasticidade_demanda_0"]), elasticidade)

    def test_conversao_exploratoria(self):
        p = parametros_por_elasticidades(60, 40, 1.5, 1.5, 20)
        for chave, esperado in dict(a=100, b=1, c=20, d=1, t=20).items():
            self.assert_igual(p[chave], esperado)
        p = parametros_por_elasticidades(60, 40, 3, 1, 20)
        self.assert_igual(p["c"], 0)

    def test_integral_de_bem_estar(self):
        r = simular_mercado(100, 1, 20, 1, 20)
        self.assert_igual(excedente_total_em_quantidade(100, 1, 20, 1, 40), 1600)
        self.assert_igual(excedente_total_em_quantidade(100, 1, 20, 1, 30), 1500)
        self.assert_igual(r["et0"] - r["et"], r["peso_morto"])

    def test_entradas_invalidas(self):
        entradas = [
            (100, 0, 20, 1, 20), (100, 1, 20, 0, 20),
            (20, 1, 20, 1, 20), (100, 1, -1, 1, 20),
            (100, 1, 20, 1, -1), (100, float("nan"), 20, 1, 20),
            (100, 1, 20, float("inf"), 20),
            (100, True, 20, 1, 20), (100, "1", 20, 1, 20),
        ]
        for entrada in entradas:
            with self.assertRaises(ValueError):
                simular_mercado(*entrada)
        with self.assertRaises(ValueError):
            parametros_por_elasticidades(60, 40, 1.5, 0.9, 20)
        with self.assertRaises(ValueError):
            parametros_por_elasticidades(60, 40, 0, 1, 20)

    def test_identidades_para_muitos_cenarios(self):
        # Uma semente fixa torna o teste reproduzivel.
        sorteio = random.Random(20261009)
        for _ in range(2000):
            a = sorteio.uniform(50, 200)
            c = sorteio.uniform(0, a * 0.5)
            b = sorteio.uniform(0.2, 3)
            d = sorteio.uniform(0.2, 3)
            t = sorteio.uniform(0, 1.5 * (a - c))
            r = simular_mercado(a, b, c, d, t)

            self.assertGreaterEqual(r["qt"], 0)
            self.assertLessEqual(r["qt"], r["q0"])
            self.assert_igual(r["et0"] - r["et"], r["peso_morto"])
            self.assert_igual(r["perda_ec"] + r["perda_ep"],
                              r["arrecadacao"] + r["peso_morto"])
            self.assert_igual(excedente_total_em_quantidade(a, b, c, d, r["qt"]), r["et"])
            self.assert_igual(r["peso_morto"],
                              0.5 * (b + d) * (r["q0"] - r["qt"])**2)
            if r["ha_transacoes"]:
                self.assert_igual(r["pc"] - r["pp"], t)
                self.assert_igual(r["a"] - b * r["qt"], r["pc"])
                self.assert_igual(r["c"] + d * r["qt"], r["pp"])
                self.assert_igual(r["q0"] - r["qt"], t / (b + d))
            else:
                self.assertIsNone(r["pc"])
                self.assertIsNone(r["pp"])
                self.assert_igual(r["arrecadacao"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Testes simples dos graficos e cenarios da interface do LCE.

Execute apos instalar requirements.txt: python testar_interface.py
"""

import math
import unittest

from experimentos import (
    cenarios_experimento_a, cenarios_experimento_b, resultados_cenarios,
)
from modelo_mercado import simular_mercado
from visualizacoes import (
    grafico_mercado, grafico_composicao_excedente,
    grafico_reparticao, grafico_distorcao,
)


class TestesInterface(unittest.TestCase):
    def assert_quase_igual(self, encontrado, esperado):
        self.assertTrue(math.isclose(encontrado, esperado, rel_tol=1e-11, abs_tol=1e-11),
                        f"Encontrado {encontrado}; esperado {esperado}")

    def test_cenarios_a_preservam_quantidade_e_bem_estar(self):
        resultados = resultados_cenarios(cenarios_experimento_a(20))
        self.assertEqual(len(resultados), 3)
        parcelas = []
        for _, r in resultados:
            for chave, esperado in [("q0", 40), ("qt", 30),
                                    ("arrecadacao", 600), ("peso_morto", 100)]:
                self.assert_quase_igual(r[chave], esperado)
            parcelas.append(r["fracao_consumidor_efetiva"])
        self.assertEqual(parcelas, [0.5, 0.75, 0.25])

    def test_cenarios_b_reproduzem_a_arquitetura(self):
        resultados = resultados_cenarios(cenarios_experimento_b(20))
        for (_, r), valores in zip(resultados,
                                   [(20, 400, 200), (30, 600, 100), (32, 640, 80)]):
            self.assert_quase_igual(r["p0"], 60)
            self.assert_quase_igual(r["q0"], 40)
            for chave, esperado in zip(["qt", "arrecadacao", "peso_morto"], valores):
                self.assert_quase_igual(r[chave], esperado)

    def test_curvas_nao_incluem_disposicao_a_pagar_negativa(self):
        r = simular_mercado(100, 1, 20, 1, 20)
        fig = grafico_mercado(r)
        demanda = next(tr for tr in fig.data if tr.name == "Demanda")
        self.assertTrue(all(q >= 0 for q in demanda.x))
        self.assertTrue(all(p >= -1e-12 for p in demanda.y))
        self.assertGreaterEqual(max(demanda.x), r["q0"])

    def test_grafico_arrecadacao_nao_duplica_excedentes(self):
        r = simular_mercado(100, 1, 20, 1, 20)
        fig = grafico_composicao_excedente(r)
        self.assertEqual(len(fig.data), 3)
        antes = sum(trace.y[0] for trace in fig.data)
        depois = sum(trace.y[1] for trace in fig.data)
        self.assert_quase_igual(antes, r["et0"])
        self.assert_quase_igual(depois, r["et"])

    def test_imposto_proibitivo_nao_exibe_cunha_de_transacoes(self):
        r = simular_mercado(100, 1, 20, 1, 90)
        fig = grafico_mercado(r)
        nomes = {tr.name for tr in fig.data}
        self.assertNotIn("Cunha tributária", nomes)
        self.assertNotIn("Arrecadação", nomes)
        self.assertNotIn("Oferta + imposto", nomes)
        self.assertIn("Peso morto", nomes)
        self.assert_quase_igual(r["qt"], 0)

    def test_sem_imposto_nao_exibe_areas_ficticias(self):
        r = simular_mercado(100, 1, 20, 1, 0)
        fig = grafico_mercado(r)
        nomes = {tr.name for tr in fig.data}
        self.assertNotIn("Arrecadação", nomes)
        self.assertNotIn("Peso morto", nomes)
        self.assert_quase_igual(r["et0"], r["et"])

    def test_graficos_comparativos(self):
        a = resultados_cenarios(cenarios_experimento_a(20))
        b = resultados_cenarios(cenarios_experimento_b(20))
        self.assertEqual(len(grafico_reparticao(a).data), 2)
        self.assertEqual(len(grafico_distorcao(b).data), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

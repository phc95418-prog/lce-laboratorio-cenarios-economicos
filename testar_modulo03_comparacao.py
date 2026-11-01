"""Critérios AC-01 a AC-12: comparação de consumidores do Experimento A."""

from decimal import Decimal
import unittest

from modulo_03.comparacao_consumidores import (
    INITIAL, automatic_view, calculate, interpretation, plot_data, shares,
    share_differences,
)


class ComparacaoConsumidoresTests(unittest.TestCase):
    def setUp(self):
        self.base = INITIAL.copy()

    def result(self, **changes):
        return calculate({**self.base, **changes})

    def graph(self, result, *, curve_a=False, curve_b=False):
        return plot_data(result, curve_a=curve_a, curve_b=curve_b,
                         view=automatic_view(result))

    def test_ac01_inicializacao_e_consulta_somente_a_otimos(self):
        c = self.result()
        self.assertEqual(INITIAL, {"R": "120", "PX": "10", "PY": "20",
                                   "AA": "0.25", "AB": "0.75"})
        self.assertEqual((c.consumer_a.basket.x, c.consumer_a.basket.y),
                         (Decimal("3"), Decimal("4.5")))
        self.assertEqual((c.consumer_b.basket.x, c.consumer_b.basket.y),
                         (Decimal("9"), Decimal("1.5")))
        traces, _, targets = self.graph(c)
        self.assertEqual([t["name"] for t in traces],
                         ["Restrição orçamentária comum", "Consumidor A", "Consumidor B"])
        self.assertEqual(targets, {"1": "A", "2": "B"})

    def test_ac02_alterar_somente_alfa_a(self):
        c = self.result(AA="0.5")
        self.assertEqual((c.consumer_a.basket.x, c.consumer_a.basket.y),
                         (Decimal("6"), Decimal("3")))
        self.assertEqual((c.consumer_b.alpha, c.consumer_b.basket.x,
                          c.consumer_b.basket.y),
                         (Decimal("0.75"), Decimal("9"), Decimal("1.5")))

    def test_ac03_alterar_somente_alfa_b(self):
        c = self.result(AB="0.5")
        self.assertEqual((c.consumer_b.basket.x, c.consumer_b.basket.y),
                         (Decimal("6"), Decimal("3")))
        self.assertEqual((c.consumer_a.alpha, c.consumer_a.basket.x,
                          c.consumer_a.basket.y),
                         (Decimal("0.25"), Decimal("3"), Decimal("4.5")))

    def test_ac04_renda_comum_recalcula_ambos(self):
        c = self.result(R="180")
        self.assertEqual((c.consumer_a.basket.x, c.consumer_a.basket.y),
                         (Decimal("4.5"), Decimal("6.75")))
        self.assertEqual((c.consumer_b.basket.x, c.consumer_b.basket.y),
                         (Decimal("13.5"), Decimal("2.25")))
        self.assertEqual(self.graph(c)[0][0]["x"], [0.0, 18.0])
        self.assertEqual(c.consumer_a.budget, c.consumer_b.budget)

    def test_ac05_preco_comum_recalcula_ambos(self):
        c = self.result(PX="20")
        self.assertEqual((c.consumer_a.basket.x, c.consumer_a.basket.y),
                         (Decimal("1.5"), Decimal("4.5")))
        self.assertEqual((c.consumer_b.basket.x, c.consumer_b.basket.y),
                         (Decimal("4.5"), Decimal("1.5")))
        self.assertEqual(self.graph(c)[0][0]["x"], [0.0, 6.0])
        self.assertEqual(c.consumer_a.budget.price_x, c.consumer_b.budget.price_x)

    def test_ac06_alfa_igual_marcador_unico_sem_deslocamento(self):
        c = self.result(AA="0.5", AB="0.5")
        traces, _, targets = self.graph(c)
        markers = [t for t in traces if "markers" in t["mode"]]
        self.assertEqual(len(markers), 1)
        self.assertEqual((markers[0]["x"], markers[0]["y"]), ([6.0], [3.0]))
        self.assertIn("A = B", markers[0]["name"])
        self.assertEqual(targets, {"1": "A=B"})
        self.assertEqual((c.difference_x, c.difference_y), (0, 0))
        self.assertEqual(share_differences(c), (Decimal(0), Decimal(0)))

    def test_ac07_quantidades_e_diferencas_b_menos_a(self):
        c = self.result()
        self.assertEqual((c.difference_x, c.difference_y),
                         (Decimal("6"), Decimal("-3")))

    def test_ac08_despesas_participacoes_e_total(self):
        c = self.result()
        self.assertEqual(c.spending_a, (Decimal("30"), Decimal("90")))
        self.assertEqual(c.spending_b, (Decimal("90"), Decimal("30")))
        self.assertEqual(shares(c), ((Decimal("25"), Decimal("75")),
                                     (Decimal("75"), Decimal("25"))))
        self.assertEqual(share_differences(c), (Decimal("50"), Decimal("-50")))
        self.assertEqual(sum(c.spending_a), Decimal("120"))
        self.assertEqual(sum(c.spending_b), Decimal("120"))

    def test_ac09_interpretacao_sem_ranking_de_bem_estar(self):
        message = interpretation(self.result())
        self.assertIn("mesma renda", message)
        self.assertIn("não permitem comparar o bem-estar", message)
        self.assertNotIn("A é superior", message)

    def test_ac10_curvas_opcionais_independentes(self):
        c = self.result()
        names_a = [t["name"] for t in self.graph(c, curve_a=True)[0]]
        names_b = [t["name"] for t in self.graph(c, curve_b=True)[0]]
        self.assertIn("Indiferença ótima de A", names_a)
        self.assertNotIn("Indiferença ótima de B", names_a)
        self.assertIn("Indiferença ótima de B", names_b)
        self.assertNotIn("Indiferença ótima de A", names_b)
        self.assertIn("Consumidor A", names_a)
        self.assertIn("Consumidor B", names_b)

    def test_ac11_sem_referencia_historica(self):
        old, new = self.result(), self.result(R="180")
        self.assertNotIn("reference", vars(new))
        self.assertNotEqual(old.consumer_a.basket, new.consumer_a.basket)
        self.assertEqual(new.consumer_a.budget.income, Decimal("180"))
        self.assertEqual(len([t for t in self.graph(new)[0]
                              if t["name"].startswith("Restrição")]), 1)

    def test_ac12_perfis_nao_mutam_estado_de_outro_modo(self):
        values = self.base.copy()
        c = calculate(values)
        from modulo_03.individual import INITIAL as INDIVIDUAL_INITIAL, calculate as individual
        individual_values = INDIVIDUAL_INITIAL.copy()
        before = individual("cobb_douglas", individual_values, None)
        values["AA"] = "0.6"
        after = calculate(values)
        self.assertEqual(individual_values, INDIVIDUAL_INITIAL)
        self.assertEqual(before, individual("cobb_douglas", individual_values, None))
        self.assertEqual(c.consumer_b, after.consumer_b)

    def test_precos_decimais_proximos_sem_perder_entrada(self):
        c = self.result(AA="0.5", AB="0.500000000000000001")
        self.assertNotEqual(c.consumer_a.alpha, c.consumer_b.alpha)
        self.assertNotEqual(c.consumer_a.exact_basket, c.consumer_b.exact_basket)
        self.assertEqual(share_differences(c)[0], Decimal("1e-16"))
        traces, warnings, targets = self.graph(c)
        self.assertNotIn("A = B", [t["name"] for t in traces])
        self.assertEqual(targets, {"1": "A", "2": "B"})
        self.assertEqual([t["marker"]["size"] for t in traces[1:]], [18, 10])
        self.assertTrue(any("economicamente distintas" in text for text in warnings))


if __name__ == "__main__":
    unittest.main()

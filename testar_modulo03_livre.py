"""Verificações focais da projeção visual da Exploração livre."""

import unittest
from decimal import Decimal

from modulo_03.livre import (automatic_view, focus_view, objects_outside,
                             plot_data, slider_spec)
from modulo_03.nucleo import assess_basket, make_basket, make_cobb_case, solve_cobb


class ExploracaoLivreTests(unittest.TestCase):
    def setUp(self):
        self.case = make_cobb_case("120", "10", "20", "0.5")
        self.solution = solve_cobb(self.case)

    def test_estado_inicial_e_projecao_somente_orcamento(self):
        view = automatic_view(self.case, self.solution, None, show_optimum=False)
        traces, warnings = plot_data(self.case, self.solution, None,
                                     manual_curve=False, optimum=False,
                                     optimum_curve=False, view=view)
        self.assertEqual([t["name"] for t in traces], ["Restrição orçamentária"])
        self.assertEqual(traces[0]["x"], [0, 12.0])
        self.assertEqual(traces[0]["y"], [6.0, 0])
        self.assertEqual(warnings, [])

    def test_cesta_inacessivel_preservada_apos_preco(self):
        basket = make_basket("4", "2")
        changed = solve_cobb(make_cobb_case("120", "25", "20", "0.5"))
        result = assess_basket(changed, basket)
        self.assertEqual((basket.x, basket.y), (Decimal(4), Decimal(2)))
        self.assertEqual((result.cost, result.balance), (Decimal(140), Decimal(-20)))
        self.assertEqual(result.budget_status, "inacessivel")

    def test_cesta_na_fronteira_e_outra_fora(self):
        self.assertEqual(assess_basket(self.solution, make_basket("6", "3")).budget_status, "fronteira")
        self.assertEqual(assess_basket(self.solution, make_basket("10", "3")).budget_status, "inacessivel")

    def test_otimo_e_curva_podem_ser_revelados_independentemente(self):
        view = automatic_view(self.case, self.solution, None, show_optimum=False)
        traces, _ = plot_data(self.case, self.solution, None, manual_curve=False,
                              optimum=False, optimum_curve=True, view=view)
        self.assertIn("Indiferença ótima", [t["name"] for t in traces])
        self.assertNotIn("Solução ótima", [t["name"] for t in traces])
        self.assertEqual((self.solution.basket.x, self.solution.basket.y), (Decimal(6), Decimal(3)))

    def test_curva_nivel_zero_sao_eixos(self):
        basket = make_basket("0", "2")
        view = automatic_view(self.case, self.solution, basket, show_optimum=False)
        traces, _ = plot_data(self.case, self.solution, basket,
                              manual_curve=True, optimum=False,
                              optimum_curve=False, view=view)
        curve = next(t for t in traces if t["name"] == "Indiferença da cesta manual")
        self.assertEqual(curve["x"][2], None)
        self.assertEqual(curve["y"][0], 0)
        self.assertEqual(curve["x"][3:], [0.0, 0.0])

    def test_slider_expandido_na_borda_inferior_sem_mudar_decimal(self):
        px = Decimal("0.000001")
        spec = slider_spec("PX", px)
        self.assertEqual(spec.minimum, 1e-6)
        self.assertEqual(spec.position, spec.minimum)
        self.assertTrue(spec.expanded)
        self.assertEqual(px, Decimal("0.000001"))

    def test_slider_alfa_extremo_e_valor_decimal_distinto(self):
        spec = slider_spec("A", Decimal("0.000000000001"))
        self.assertEqual(spec.position, 1e-12)
        self.assertEqual(spec.minimum, 1e-12)
        precise = slider_spec("PX", Decimal("1.00000000000000001"))
        self.assertTrue(precise.approximate)

    def test_foco_local_recupera_objeto_com_escala_assimetrica(self):
        case = make_cobb_case("1000000", "0.000001", "1000000", "0.5")
        solution = solve_cobb(case)
        full = automatic_view(case, solution, None, show_optimum=True)
        focus = focus_view(solution.basket)
        self.assertGreater(full["x"][1] / (focus["x"][1] - focus["x"][0]), 1)
        self.assertTrue(objects_outside(focus, None, make_basket("999999999999", "0")))
        self.assertEqual(solution.basket.x, Decimal("500000000000.0"))


if __name__ == "__main__":
    unittest.main()

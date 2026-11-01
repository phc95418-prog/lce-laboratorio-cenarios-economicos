"""Critérios focais AI-01 a AI-13 do Experimento A individual."""

import unittest
from decimal import Decimal

from modulo_03.individual import (INITIAL, MODELS, automatic_view, calculate,
                                  diagnosis, explanation, hint, plot_data)
from modulo_03.nucleo import make_basket


class EscolhaIndividualTests(unittest.TestCase):
    def setUp(self):
        self.base = dict(INITIAL)

    def result(self, model="cobb_douglas", x=None, y=None, values=None):
        manual = make_basket(x, y) if x is not None else None
        return calculate(model, values or self.base, manual)

    def traces(self, result, manual=None, **visibility):
        flags = dict(manual_curve=False, optimum=False, optimum_curve=False)
        flags.update(visibility)
        view = automatic_view(result.solution, manual,
                              show_optimum=flags["optimum"],
                              show_optimum_curve=flags["optimum_curve"])
        traces, warnings = plot_data(result.solution, manual, view=view, **flags)
        return traces, warnings

    def test_ai01_inicial_sem_cesta_ou_otimo_visual(self):
        self.assertEqual(INITIAL, {"R": "120", "PX": "10", "PY": "20", "A": "0.5"})
        self.assertEqual(MODELS["Cobb–Douglas"], "cobb_douglas")
        result = self.result()
        self.assertIsNone(result.assessment)
        self.assertEqual([t["name"] for t in self.traces(result)[0]], ["Restrição orçamentária"])

    def test_ai02_selecao_frac_fora_sem_ajuste(self):
        result = self.result(x="3.5", y="9.25")
        a = result.assessment
        self.assertEqual((a.basket.x, a.basket.y), (Decimal("3.5"), Decimal("9.25")))
        self.assertEqual(a.cost, Decimal("220.0"))
        self.assertEqual(a.budget_status, "inacessivel")

    def test_ai03_ai07_avaliacao_e_otimo_independentes(self):
        manual = make_basket("4", "4")
        result = calculate("cobb_douglas", self.base, manual)
        self.assertEqual(result.assessment.optimality, "nao_otima")
        self.assertNotIn("Solução ótima", [t["name"] for t in self.traces(result, manual)[0]])
        self.assertIn("Solução ótima", [t["name"] for t in self.traces(result, manual, optimum=True)[0]])
        self.assertEqual((manual.x, manual.y), (Decimal(4), Decimal(4)))

    def test_ai04_tangencia_sem_esgotamento(self):
        result = self.result(x="3", y="1.5")
        a = result.assessment
        self.assertEqual((a.cost, a.balance, a.budget_status, a.optimality),
                         (Decimal(60), Decimal(60), "sobra", "nao_otima"))
        self.assertIn("tangência isolada não basta", explanation(result.solution, a))

    def test_ai05_fronteira_sem_otimalidade(self):
        result = self.result(x="4", y="4")
        a = result.assessment
        self.assertEqual((a.cost, a.budget_status, a.optimality),
                         (Decimal(120), "fronteira", "nao_otima"))
        self.assertIn("isoladamente não garante", explanation(result.solution, a))

    def test_ai06_inacessibilidade_antes_da_utilidade(self):
        result = self.result(x="10", y="3")
        a = result.assessment
        self.assertEqual((a.cost, a.budget_status, a.optimality),
                         (Decimal(160), "inacessivel", "nao_otima"))
        self.assertIn("inacessível", diagnosis(a))

    def test_ai08_pistas_sem_coordenadas(self):
        for model, basket, values in (
            ("cobb_douglas", ("4", "4"), self.base),
            ("substitutes", ("2", "3"), {**self.base, "PX": "20"}),
            ("complements", ("3", "3"), self.base),
        ):
            result = self.result(model, *basket, values=values)
            self.assertIsNotNone(hint(result.solution, result.assessment))
            self.assertNotIn("(6;3)", hint(result.solution, result.assessment))
        equal = self.result("substitutes", "2", "3", {**self.base, "PX": "20"})
        self.assertIn("renda", hint(equal.solution, equal.assessment))
        self.assertNotIn("bem X", hint(equal.solution, equal.assessment))

    def test_ai09_canto_substitutos(self):
        result = self.result("substitutes", "4", "4")
        self.assertEqual((result.solution.basket.x, result.solution.basket.y),
                         (Decimal(12), Decimal(0)))
        self.assertEqual(result.assessment.optimality, "nao_otima")

    def test_ai10_segmento_inteiro_e_pertencimento(self):
        values = {**self.base, "PX": "20"}
        result = self.result("substitutes", "2", "4", values)
        self.assertEqual(result.solution.kind, "segment")
        self.assertIsNone(result.solution.basket)
        self.assertEqual(result.assessment.optimality, "otima")
        self.assertEqual(self.result("substitutes", "3", "3", values).assessment.optimality, "otima")
        self.assertEqual(self.result("substitutes", "2", "3", values).assessment.optimality, "nao_otima")
        traces, _ = self.traces(result, optimum=True)
        segment = next(t for t in traces if t["name"] == "Conjunto ótimo completo")
        self.assertEqual(segment["x"], [6.0, 0.0])
        self.assertEqual(segment["y"], [0.0, 6.0])

    def test_ai10_precos_decimais_distintos_nao_sao_empate(self):
        result = self.result("substitutes", values={**self.base, "PX": "20", "PY": "20.000000000000000001"})
        self.assertEqual(result.solution.kind, "unique")
        self.assertEqual(result.solution.basket.y, Decimal(0))

    def test_ai11_quina_e_ambos_os_bens(self):
        result = self.result("complements", "4", "4")
        self.assertEqual(result.assessment.optimality, "otima")
        self.assertEqual(result.solution.basket, make_basket("4", "4"))
        other = self.result("complements", "3", "3")
        self.assertEqual(other.assessment.optimality, "nao_otima")
        self.assertIn("ambos os bens", explanation(other.solution, other.assessment))

    def test_ai12_troca_de_modelo_preserva_cesta_e_alfa(self):
        manual = make_basket("4", "4")
        outcomes = [calculate(model, self.base, manual).assessment.optimality
                    for model in ("cobb_douglas", "substitutes", "complements", "cobb_douglas")]
        self.assertEqual(outcomes, ["nao_otima", "nao_otima", "otima", "nao_otima"])
        self.assertEqual(self.base["A"], "0.5")
        self.assertEqual(manual, make_basket("4", "4"))

    def test_ai13_recalculo_de_diagnostico_ativo(self):
        manual = make_basket("4", "4")
        before = calculate("complements", self.base, manual)
        after = calculate("complements", {**self.base, "R": "90"}, manual)
        self.assertEqual(before.assessment.optimality, "otima")
        self.assertEqual(after.assessment.budget_status, "inacessivel")
        self.assertEqual(after.assessment.basket, manual)

    def test_curvas_especificas_e_nivel_zero(self):
        for model in ("cobb_douglas", "substitutes", "complements"):
            manual = make_basket("0", "0")
            result = calculate(model, self.base, manual)
            traces, _ = self.traces(result, manual, manual_curve=True)
            curve = next(t for t in traces if t["name"] == "Indiferença da cesta manual")
            if model == "substitutes":
                self.assertEqual((curve["x"], curve["y"]), ([0.0], [0.0]))
            else:
                self.assertIn(None, curve["x"])
        comp = self.result("complements", "3", "3")
        traces, _ = self.traces(comp, make_basket("3", "3"), manual_curve=True)
        curve = next(t for t in traces if t["name"] == "Indiferença da cesta manual")
        self.assertIn(None, curve["x"])
        self.assertEqual(curve["x"][0], 3.0)

        # O Pan pode deixar a quina fora da janela. O traçado não pode
        # voltar em direção a quantidades inferiores ao nível de utilidade.
        outside = {"x": [0.0, 2.0], "y": [0.0, 2.0]}
        traces, warnings = plot_data(comp.solution, make_basket("3", "3"),
                                     manual_curve=True, optimum=False,
                                     optimum_curve=False, view=outside)
        curve = next(t for t in traces if t["name"] == "Indiferença da cesta manual")
        self.assertEqual((curve["x"], curve["y"]), ([], []))
        self.assertTrue(warnings)

    def test_classificacao_inconclusiva_e_explicita(self):
        result = self.result(x="1e-1100", y="0")
        self.assertEqual(result.assessment.budget_status, "inconclusivo")
        self.assertEqual(result.assessment.optimality, "inconclusiva")
        self.assertIn("inconclusiva", diagnosis(result.assessment))

    def test_marcador_coincidente_nao_e_duplicado(self):
        manual = make_basket("6", "3")
        result = calculate("cobb_douglas", self.base, manual)
        traces, _ = self.traces(result, manual, optimum=True)
        self.assertIn("Cesta manual = solução ótima", [t["name"] for t in traces])
        self.assertNotIn("Solução ótima", [t["name"] for t in traces])


if __name__ == "__main__":
    unittest.main()

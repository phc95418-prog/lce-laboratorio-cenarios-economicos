"""Critérios EH-01 a EH-10 do aprofundamento experimental de Hicks."""

from __future__ import annotations

import unittest
from decimal import Decimal, localcontext
from unittest.mock import patch

from modulo_03 import interface_experimento_b as ui
from modulo_03.experimento_b import (INITIAL, automatic_view, case_from, compare,
                                     effect_annotation, fix_reference, hicks,
                                     plot_data, reference_values)
from modulo_03.nucleo import Basket, HicksResult


class HicksExperimentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reference = fix_reference(dict(INITIAL))

    def scenario(self, **changes: str):
        values = dict(INITIAL)
        values.update(changes)
        comparison = compare(self.reference, values)
        return comparison, hicks(self.reference, comparison.current)

    def graph(self, comparison, result, *, curve_c=False):
        view = automatic_view(comparison.current, comparison, result)
        return plot_data(comparison.current, comparison, curve_a=False,
                         curve_c=curve_c, view=view, hicks_result=result)

    def test_eh01_exact_eligibility_and_primary_comparison(self):
        same, result = self.scenario()
        self.assertEqual(result.status, "inaplicavel")
        self.assertEqual(result.reason, "preços inalterados")
        self.assertEqual(same.current_solution.basket, self.reference.solution.basket)
        changed, result = self.scenario(PX="20")
        self.assertEqual(result.status, "calculado")
        self.assertEqual(changed.current_solution.basket, Basket(Decimal(3), Decimal(3)))
        jointly, result = self.scenario(R="180", PX="20")
        self.assertEqual(result.reason, "renda nominal diferente")
        self.assertEqual(jointly.change_kind, "conjunto")
        self.assertEqual(jointly.current_solution.basket, Basket(Decimal("4.5"), Decimal("4.5")))
        _, near = self.scenario(PX="10.000000000000001")
        self.assertEqual(near.status, "calculado")
        self.assertNotEqual(near.substitution, Basket(Decimal(0), Decimal(0)))

    def test_eh02_independent_canonical_oracle_and_duality(self):
        comparison, result = self.scenario(PX="20")
        self.assertEqual(result.status, "calculado")
        with localcontext() as ctx:
            ctx.prec = 125
            root = Decimal(18).sqrt()
            self.assertLess(abs(result.compensated.x - root), Decimal("1e-100"))
            self.assertLess(abs(result.compensated.y - root), Decimal("1e-100"))
            self.assertLess(abs(result.expenditure - 40 * root), Decimal("1e-100"))
            self.assertLess(abs(result.compensated.x * result.compensated.y - 18),
                            Decimal("1e-100"))
            self.assertLess(abs(20 * result.compensated.x + 20 * result.compensated.y -
                                result.expenditure), Decimal("1e-100"))
        self.assertEqual(comparison.reference.solution.basket, Basket(Decimal(6), Decimal(3)))

    def test_eh03_finite_identity_both_goods(self):
        _, result = self.scenario(PX="20")
        with localcontext() as ctx:
            ctx.prec = 125
            for component in ("x", "y"):
                left = getattr(result.substitution, component) + getattr(result.income_effect, component)
                self.assertLess(abs(left - getattr(result.total, component)), Decimal("1e-100"))
        self.assertEqual(result.total, Basket(Decimal(-3), Decimal(0)))

    def test_eh04_highlight_arrows_and_exact_zero(self):
        comparison, result = self.scenario(PX="20")
        for effect in ("Substituição", "Renda", "Total"):
            annotation, warning = effect_annotation(comparison, result, effect)
            self.assertIsNone(warning)
            self.assertTrue(annotation["showarrow"])
            self.assertEqual(annotation["axref"], "x")
            self.assertEqual(annotation["ayref"], "y")
        proportional, zero = self.scenario(PX="20", PY="40")
        annotation, warning = effect_annotation(proportional, zero, "Substituição")
        self.assertIsNone(annotation)
        self.assertIn("exatamente nulo", warning)
        self.assertIsNotNone(effect_annotation(proportional, zero, "Renda")[0])

    def test_eh05_price_updates_and_removes_old_compensation(self):
        before, first = self.scenario(PX="20")
        after, second = self.scenario(PX="30")
        self.assertNotEqual(first.compensated, second.compensated)
        self.assertNotEqual(first.expenditure, second.expenditure)
        self.assertEqual(after.reference, before.reference)
        _, returned = self.scenario()
        self.assertEqual(returned.status, "inaplicavel")

    def test_eh06_and_eh07_deactivation_then_voluntary_reactivation(self):
        state = {}
        with patch.object(ui.st, "session_state", state):
            ui._initial_state()
            state[ui._key("reference")] = self.reference
            state[ui._key("hicks_on")] = True
            income_case = case_from(dict(INITIAL, R="180", PX="20"))
            candidate, message = ui._hicks_candidate(self.reference, income_case)
            self.assertIsNone(candidate)
            self.assertFalse(state[ui._key("hicks_on")])
            self.assertIn("renda nominal", message)
            eligible = case_from(dict(INITIAL, PX="20"))
            candidate, message = ui._hicks_candidate(self.reference, eligible)
            self.assertEqual(candidate.status, "calculado")
            self.assertIsNone(message)
            self.assertFalse(state[ui._key("hicks_on")])

    def test_eh08_zero_total_y_has_opposing_components(self):
        _, result = self.scenario(PX="20")
        self.assertGreater(result.substitution.y, 0)
        self.assertLess(result.income_effect.y, 0)
        self.assertEqual(result.total.y, 0)
        with localcontext() as ctx:
            ctx.prec = 125
            self.assertEqual(result.substitution.y + result.income_effect.y, 0)
        self.assertIn("substituição positiva e renda negativa",
                      ui._zero_total_y_explanation(result))
        _, cheaper = self.scenario(PX="5")
        self.assertEqual(cheaper.total.y, 0)
        self.assertIn("substituição negativa e renda positiva",
                      ui._zero_total_y_explanation(cheaper))

    def test_eh09_proportional_prices_merge_A_H_and_skip_arrow(self):
        comparison, result = self.scenario(PX="20", PY="40")
        self.assertEqual(result.status, "calculado")
        self.assertEqual(result.compensated, Basket(Decimal(6), Decimal(3)))
        self.assertEqual(result.substitution, Basket(Decimal(0), Decimal(0)))
        self.assertEqual(result.income_effect, Basket(Decimal(-3), Decimal("-1.5")))
        self.assertEqual(result.income_effect, result.total)
        traces, warnings, targets = self.graph(comparison, result)
        self.assertEqual(warnings, [])
        self.assertTrue(any("referência e compensada coincidentes" in t["name"] for t in traces))
        self.assertEqual(set(targets.values()), {"A=H", "C"})
        self.assertFalse(any(t["name"] == "Restrição compensada" for t in traces))

    def test_eh10_replace_reference_invalidates_hicks(self):
        state = {}
        with patch.object(ui.st, "session_state", state):
            ui._initial_state()
            state[ui._key("reference")] = self.reference
            state[ui._key("value_PX")] = "20"
            state[ui._key("hicks_on")] = True
            state[ui._key("replace_pending")] = True
            ui._apply_pending()
            self.assertEqual(state[ui._key("reference")].case.budget.price_x, Decimal(20))
            self.assertFalse(state[ui._key("hicks_on")])
            current = case_from(ui._values(), alpha=state[ui._key("reference")].case.alpha)
            self.assertEqual(hicks(state[ui._key("reference")], current).status, "inaplicavel")

    def test_restore_and_reset_clear_hicks_without_other_environment_changes(self):
        state = {"m03_livre_value_R": "777", "m03_ai_value_R": "888"}
        with patch.object(ui.st, "session_state", state):
            ui._initial_state()
            state[ui._key("reference")] = self.reference
            state[ui._key("value_PX")] = "20"
            state[ui._key("hicks_on")] = True
            state[ui._key("restore_pending")] = True
            ui._apply_pending()
            self.assertIs(state[ui._key("reference")], self.reference)
            self.assertFalse(state[ui._key("hicks_on")])
            self.assertEqual(ui._values(), reference_values(self.reference))
            state[ui._key("reset_pending")] = True
            ui._apply_pending()
            self.assertIsNone(state[ui._key("reference")])
            self.assertFalse(state[ui._key("hicks_on")])
            self.assertEqual(state["m03_livre_value_R"], "777")
            self.assertEqual(state["m03_ai_value_R"], "888")

    def test_navigation_snapshot_keeps_hicks_but_new_session_starts_off(self):
        state = {}
        with patch.object(ui.st, "session_state", state):
            ui._initial_state()
            state[ui._key("reference")] = self.reference
            state[ui._key("value_PX")] = "20"
            state[ui._key("hicks_on")] = True
            state[ui._key("hicks_effect")] = "Renda"
            state[ui._key("curve_C")] = True
            state[ui._key("view")] = {"x": [1.0, 8.0], "y": [1.0, 6.0]}
            saved = dict(state)
            state.clear()
            state.update(saved)
            ui._initial_state()
            self.assertTrue(state[ui._key("hicks_on")])
            self.assertEqual(state[ui._key("hicks_effect")], "Renda")
            self.assertTrue(state[ui._key("curve_C")])
            self.assertEqual(state[ui._key("view")]["x"], [1.0, 8.0])
            state.clear()
            ui._initial_state()
            self.assertIsNone(state[ui._key("reference")])
            self.assertFalse(state[ui._key("hicks_on")])

    def test_inconclusive_hicks_clears_layer_without_losing_primary_reference(self):
        state = {}
        with patch.object(ui.st, "session_state", state):
            ui._initial_state()
            state[ui._key("reference")] = self.reference
            state[ui._key("hicks_on")] = True
            current = case_from(dict(INITIAL, PX="20"))
            uncertain = HicksResult("inconclusivo", "precisão derivada insuficiente",
                                    self.reference, current)
            with patch.object(ui, "hicks", return_value=uncertain):
                candidate, message = ui._hicks_candidate(self.reference, current)
            self.assertIsNone(candidate)
            self.assertFalse(state[ui._key("hicks_on")])
            self.assertIn("precisão derivada insuficiente", message)
            self.assertIs(state[ui._key("reference")], self.reference)
            self.assertEqual(compare(self.reference, dict(INITIAL, PX="20")).change_kind,
                             "precos")

    def test_graph_compensation_curve_markers_and_joint_H_C(self):
        comparison, result = self.scenario(PX="20")
        traces, warnings, targets = self.graph(comparison, result, curve_c=True)
        self.assertEqual(warnings, [])
        self.assertEqual(set(targets.values()), {"A", "H", "C"})
        self.assertEqual(next(t for t in traces if t["name"] == "Restrição compensada")["line"]["dash"],
                         "dashdot")
        self.assertEqual(next(t for t in traces if t["name"] == "Cesta H")["marker"]["symbol"],
                         "diamond")
        self.assertEqual(len([t for t in traces if t["name"].startswith("Indiferença")]), 2)
        initial_curve = next(t for t in traces if t["name"] == "Indiferença inicial de A e H")
        self.assertIn((6.0, 3.0), zip(initial_curve["x"], initial_curve["y"]))
        self.assertIn((float(result.compensated.x), float(result.compensated.y)),
                      zip(initial_curve["x"], initial_curve["y"]))
        comparison, result = self.scenario(PX="20", PY="10")
        self.assertEqual(comparison.utility_order, "igual")
        traces, _, targets = self.graph(comparison, result)
        self.assertEqual(set(targets.values()), {"A", "H=C"})
        self.assertTrue(any("atual e compensada coincidentes" in t["name"] for t in traces))

    def test_tiny_effects_do_not_become_economic_zero(self):
        comparison, result = self.scenario(PX="10.000000000000001")
        self.assertEqual(result.status, "calculado")
        self.assertNotEqual(result.substitution.x, 0)
        self.assertNotEqual(result.income_effect.x, 0)
        self.assertEqual(result.total.y, 0)
        annotation, warning = effect_annotation(comparison, result, "Substituição")
        self.assertFalse(warning and "exatamente nulo" in warning)
        if annotation is None:
            self.assertIn("resolução do gráfico", warning)


if __name__ == "__main__":
    unittest.main()

"""Contratos econômicos, gráficos e estados do Experimento B experimental."""

from __future__ import annotations

import unittest
from dataclasses import replace
from decimal import Decimal
from unittest.mock import patch

from modulo_03 import interface_experimento_b as ui
from modulo_03.experimento_b import (INITIAL, automatic_view, budgets_coincide,
                                     case_from, compare, fix_reference,
                                     interpretation, plot_data, reference_values)
from modulo_03.nucleo import DomainError


class ExperimentBTests(unittest.TestCase):
    def setUp(self) -> None:
        self.initial = dict(INITIAL)
        self.reference = fix_reference(self.initial)

    def current(self, **changes: str) -> dict[str, str]:
        values = dict(self.initial)
        values.update(changes)
        return values

    def graph(self, comparison, *, curves=False):
        current = comparison.current
        return plot_data(current, comparison, curve_a=curves, curve_c=curves,
                         view=automatic_view(current, comparison))

    def test_eb01_initial_without_historical_comparison(self):
        case = case_from(self.initial)
        self.assertEqual(case.budget.income, Decimal("120"))
        self.assertEqual(case.alpha, Decimal("0.5"))
        traces, _, targets = plot_data(case, None, curve_a=False, curve_c=False,
                                      view=automatic_view(case, None))
        self.assertEqual(len(traces), 1)
        self.assertEqual(targets, {})
        self.assertEqual(traces[0]["name"], "Restrição atual")

    def test_eb02_reference_base(self):
        a = self.reference.solution.basket
        self.assertEqual((a.x, a.y), (Decimal("6"), Decimal("3")))
        self.assertEqual(self.reference.solution.utility *
                         self.reference.solution.utility, Decimal("18"))
        self.assertEqual(reference_values(self.reference), self.initial)
        self.assertEqual(compare(self.reference, self.initial).change_kind, "identico")

    def test_eb03_income_only(self):
        comparison = compare(self.reference, self.current(R="180"))
        c = comparison.current_solution.basket
        self.assertEqual((c.x, c.y), (Decimal("9"), Decimal("4.5")))
        self.assertEqual(comparison.change_kind, "renda")
        self.assertEqual(comparison.utility_order, "maior")
        self.assertEqual(comparison.reference.case.budget.income, Decimal("120"))
        traces, _, _ = self.graph(comparison)
        self.assertEqual(traces[0]["line"]["dash"], "dash")
        self.assertEqual(traces[1]["line"]["dash"], "solid")
        self.assertEqual(traces[0]["x"][-1], traces[1]["x"][-1] / 1.5)

    def test_eb04_price_only_and_repurchase(self):
        comparison = compare(self.reference, self.current(PX="20"))
        c = comparison.current_solution.basket
        self.assertEqual((c.x, c.y), (Decimal("3"), Decimal("3")))
        self.assertEqual(comparison.change_kind, "precos")
        self.assertEqual(comparison.reference_repurchase_cost, Decimal("180"))
        self.assertEqual(comparison.reference_repurchase_balance, Decimal("-60"))
        self.assertEqual(comparison.reference_affordability, "inacessivel")
        self.assertEqual(comparison.utility_order, "menor")
        self.assertLess(abs(comparison.current_solution.utility - Decimal("3")),
                        Decimal("1e-70"))
        self.assertGreater(self.reference.solution.utility, Decimal("4"))
        self.assertEqual(comparison.reference.solution.basket.x, Decimal("6"))

    def test_eb05_joint_change_has_no_single_cause(self):
        comparison = compare(self.reference, self.current(R="180", PX="20"))
        c = comparison.current_solution.basket
        self.assertEqual((c.x, c.y), (Decimal("4.5"), Decimal("4.5")))
        self.assertEqual(comparison.change_kind, "conjunto")
        summary = interpretation(comparison)
        self.assertIn("conjuntamente", summary)
        self.assertIn("não pode ser atribuída a um único fator", summary)

    def test_eb06_graph_and_curves(self):
        comparison = compare(self.reference, self.current(PX="20"))
        traces, warnings, targets = self.graph(comparison, curves=True)
        self.assertEqual(warnings, [])
        self.assertEqual(traces[0]["name"], "Restrição de referência")
        self.assertEqual(traces[1]["name"], "Restrição atual")
        self.assertEqual(traces[0]["line"]["dash"], "dash")
        self.assertEqual(traces[1]["line"]["dash"], "solid")
        curves = [t for t in traces if t["name"].startswith("Indiferença")]
        self.assertEqual(len(curves), 2)
        self.assertTrue(all(t["line"]["dash"] == "dot" for t in curves))
        self.assertEqual({"A", "C"}, set(targets.values()))
        self.assertEqual(traces[-2]["marker"]["symbol"], "circle")
        self.assertEqual(traces[-1]["marker"]["symbol"], "square")

    def test_eb07_repurchase_is_distinct_from_optimal_spending(self):
        comparison = compare(self.reference, self.current(PX="20"))
        self.assertEqual(comparison.reference_repurchase_cost, Decimal("180"))
        self.assertEqual(comparison.current.budget.income, Decimal("120"))
        self.assertNotEqual(comparison.reference_repurchase_cost,
                            comparison.current.budget.income)

    def test_eb08_ordinal_only_and_inconclusive(self):
        comparison = compare(self.reference, self.current(PX="20"))
        self.assertEqual(comparison.utility_order, "menor")
        self.assertIn("U(C) < U(A)", interpretation(comparison))
        inconclusive = replace(comparison, utility_order="inconclusiva")
        self.assertIn("inconclusiva", interpretation(inconclusive))
        self.assertNotIn("U(C) = U(A)", interpretation(inconclusive))

    def test_eb09_restore_current_preserves_reference(self):
        modified = compare(self.reference, self.current(R="180", PX="20"))
        restored = compare(modified.reference, reference_values(modified.reference))
        self.assertIs(restored.reference, self.reference)
        self.assertEqual(restored.change_kind, "identico")
        self.assertEqual(restored.current_solution.exact_basket,
                         self.reference.solution.exact_basket)

    def test_eb10_replace_reference_recalculates(self):
        old = self.reference
        new = fix_reference(self.current(R="180", PX="20"))
        self.assertEqual((new.solution.basket.x, new.solution.basket.y),
                         (Decimal("4.5"), Decimal("4.5")))
        self.assertNotEqual(new.solution.exact_basket, old.solution.exact_basket)
        self.assertEqual(compare(new, reference_values(new)).change_kind, "identico")
        self.assertEqual(old.case.budget.income, Decimal("120"))

    def test_eb11_homogeneity_joint_marker_and_budget(self):
        comparison = compare(self.reference, self.current(R="240", PX="20", PY="40"))
        self.assertEqual(comparison.change_kind, "conjunto")
        self.assertEqual(comparison.utility_order, "igual")
        self.assertEqual(comparison.current_solution.exact_basket,
                         self.reference.solution.exact_basket)
        self.assertTrue(budgets_coincide(self.reference, comparison.current))
        traces, _, targets = self.graph(comparison)
        self.assertEqual(len(traces), 2)
        self.assertIn("coincidentes", traces[0]["name"])
        self.assertEqual(traces[1]["name"], "A = C · referência e atual")
        self.assertEqual(traces[1]["marker"]["symbol"], "diamond")
        self.assertEqual(list(targets.values()), ["A=C"])
        self.assertIn("valores nominais diferem", interpretation(comparison))

    def test_eb12_reference_and_view_survive_state_snapshot(self):
        state = {}
        with patch.object(ui.st, "session_state", state):
            ui._initial_state()
            state[ui._key("reference")] = self.reference
            state[ui._key("value_R")] = "180"
            state[ui._key("field_R")] = "180"
            state[ui._key("view")] = {"x": [2.0, 10.0], "y": [1.0, 7.0]}
            saved = {k: v for k, v in state.items() if k.startswith(ui.PREFIX)}
            state.clear()
            state.update(saved)
            self.assertIs(state[ui._key("reference")], self.reference)
            self.assertEqual(state[ui._key("value_R")], "180")
            self.assertEqual(state[ui._key("view")]["x"], [2.0, 10.0])

    def test_state_operations_do_not_modify_other_environments(self):
        state = {"m03_livre_value_R": "777", "m03_ai_value_R": "888",
                 "m03_ac_value_R": "999"}
        with patch.object(ui.st, "session_state", state):
            ui._initial_state()
            state[ui._key("reference")] = self.reference
            state[ui._key("value_R")] = "180"
            state[ui._key("restore_pending")] = True
            ui._apply_pending()
            self.assertEqual(state[ui._key("value_R")], "120")
            self.assertIs(state[ui._key("reference")], self.reference)
            state[ui._key("value_PX")] = "20"
            state[ui._key("replace_pending")] = True
            ui._apply_pending()
            self.assertEqual(state[ui._key("reference")].case.budget.price_x,
                             Decimal("20"))
            state[ui._key("reset_pending")] = True
            ui._apply_pending()
            self.assertIsNone(state[ui._key("reference")])
            self.assertEqual(state[ui._key("value_PX")], "10")
            self.assertEqual(tuple(state[f"m03_{p}_value_R"] for p in
                                   ("livre", "ai", "ac")), ("777", "888", "999"))

    def test_decimal_distinct_prices_and_fixed_alpha(self):
        values = self.current(PX="10.000000000000001")
        comparison = compare(self.reference, values)
        self.assertEqual(comparison.change_kind, "precos")
        self.assertFalse(budgets_coincide(self.reference, comparison.current))
        _, warnings, targets = self.graph(comparison)
        self.assertTrue(any("diferem economicamente" in item for item in warnings))
        self.assertEqual(set(targets.values()), {"A", "C"})
        values["A"] = "0.7"
        self.assertEqual(compare(self.reference, values).current.alpha, Decimal("0.5"))
        with self.assertRaises(DomainError):
            case_from(values, alpha=Decimal("1"))


if __name__ == "__main__":
    unittest.main()

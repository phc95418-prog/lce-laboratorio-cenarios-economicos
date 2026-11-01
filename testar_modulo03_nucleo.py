"""Contratos matemáticos permanentes do núcleo do Módulo 03."""

import ast
import unittest
from decimal import Decimal as D, localcontext
from fractions import Fraction
from pathlib import Path

from modulo_03 import (
    DomainError, NumericalPolicy, assess_basket, compare_consumers,
    compare_scenarios, compensate, freeze_reference, hicks_decomposition,
    make_basket, make_budget, make_cobb_case, solve_cobb,
    solve_complements, solve_substitutes,
)


def base():
    return make_cobb_case("120", "10", "20", "0.5")


class ConsumerEngineTests(unittest.TestCase):
    def test_cobb_reference_and_budget(self):
        solution = solve_cobb(base())
        self.assertEqual(solution.basket, make_basket("6", "3"))
        self.assertEqual(solution.exact_basket, (Fraction(6), Fraction(3)))
        self.assertEqual(Fraction(10) * solution.exact_basket[0] +
                         Fraction(20) * solution.exact_basket[1], Fraction(120))
        with localcontext() as ctx:
            ctx.prec = 80
            self.assertLess(abs(solution.utility - D(18).sqrt()), D("1e-70"))

    def test_cobb_shares_and_homogeneity_multiple_cases(self):
        for r, px, py, a, scale in [
            ("120", "10", "20", "0.5", "2"),
            ("1e-6", "1e6", "1e-6", "1e-12", "0.5"),
            ("1e6", "1e-6", "1e6", "0.999999999999", "1e-6"),
        ]:
            with self.subTest(r=r, px=px, py=py, a=a):
                case = make_cobb_case(r, px, py, a)
                x, y = solve_cobb(case).exact_basket
                rf, pxf, pyf, af = map(lambda z: Fraction(D(z)), (r, px, py, a))
                self.assertEqual(pxf * x, af * rf)
                self.assertEqual(pyf * y, (1 - af) * rf)
                scaled = make_cobb_case(str(D(r) * D(scale)),
                                        str(D(px) * D(scale)), str(D(py) * D(scale)), a,
                                        envelope=None)
                self.assertEqual(solve_cobb(scaled).exact_basket, (x, y))

    def test_manual_budget_and_no_tangency_shortcut(self):
        solution = solve_cobb(base())
        self.assertEqual(assess_basket(solution, make_basket("4", "2")).cost, D(80))
        self.assertEqual(assess_basket(solution, make_basket("3", "1.5")).optimality,
                         "nao_otima")  # TMS igual ao preço relativo, mas há sobra
        self.assertEqual(assess_basket(solution, make_basket("4", "4")).budget_status,
                         "fronteira")
        self.assertEqual(assess_basket(solution, make_basket("4", "4")).optimality,
                         "nao_otima")
        self.assertEqual(assess_basket(solution, make_basket("10", "3")).budget_status,
                         "inacessivel")

    def test_immediately_outside_budget_not_rounded_to_frontier(self):
        solution = solve_cobb(base())
        x = "4." + "0" * 60 + "1"
        result = assess_basket(solution, make_basket(x, "4"))
        self.assertEqual(result.budget_status, "inacessivel")
        self.assertEqual(result.balance, D("-1e-60"))
        self.assertEqual(result.optimality, "nao_otima")
        self.assertEqual(assess_basket(solution, make_basket("4", "4")).balance, 0)

    def test_exact_optimality_ignores_display_rounding(self):
        solution = solve_cobb(base())
        self.assertEqual(assess_basket(solution, make_basket("6", "3")).optimality,
                         "otima")
        almost = "6." + "0" * 60 + "1"
        self.assertEqual(assess_basket(solution, make_basket(almost, "3")).optimality,
                         "nao_otima")

    def test_zero_utility_on_cobb_axes(self):
        solution = solve_cobb(base())
        for x, y in [("0", "3"), ("6", "0"), ("0", "0")]:
            self.assertEqual(assess_basket(solution, make_basket(x, y)).utility, 0)

    def test_substitutes_corner_and_full_segment(self):
        first = solve_substitutes(make_budget("120", "10", "20"))
        self.assertEqual(first.kind, "unique")
        self.assertEqual(first.basket, make_basket("12", "0"))
        second = solve_substitutes(make_budget("120", "20", "10"))
        self.assertEqual(second.basket, make_basket("0", "12"))
        tied = solve_substitutes(make_budget("120", "20", "20"))
        self.assertEqual(tied.kind, "segment")
        self.assertIsNone(tied.basket)
        self.assertEqual(tied.segment, (make_basket("6", "0"), make_basket("0", "6")))
        self.assertEqual(assess_basket(tied, make_basket("2", "4")).optimality, "otima")
        self.assertEqual(assess_basket(tied, make_basket("2", "3")).optimality, "nao_otima")

    def test_decimal_prices_that_float_collapses_are_not_tied(self):
        close = "10." + "0" * 60 + "1"
        self.assertEqual(float(D(close)), float(D(10)))
        solution = solve_substitutes(make_budget("120", "10", close))
        self.assertEqual(solution.kind, "unique")
        self.assertEqual(solution.basket, make_basket("12", "0"))

    def test_complements_kink(self):
        solution = solve_complements(make_budget("120", "10", "20"))
        self.assertEqual(solution.kind, "unique")
        self.assertEqual(solution.basket, make_basket("4", "4"))
        self.assertEqual(assess_basket(solution, make_basket("4", "4")).optimality, "otima")
        self.assertEqual(assess_basket(solution, make_basket("3", "3")).optimality,
                         "nao_otima")
        self.assertEqual(assess_basket(solution, make_basket("5", "3")).utility, 3)

    def test_consumer_comparison_uses_common_budget(self):
        got = compare_consumers(make_budget("120", "10", "20"), "0.25", "0.75")
        self.assertEqual(got.consumer_a.basket, make_basket("3", "4.5"))
        self.assertEqual(got.consumer_b.basket, make_basket("9", "1.5"))
        self.assertEqual((got.difference_x, got.difference_y), (D(6), D(-3)))
        self.assertEqual(got.spending_a, (D(30), D(90)))
        self.assertEqual(got.spending_b, (D(90), D(30)))
        self.assertFalse(hasattr(got, "utility_difference"))

    def test_change_reference_and_repurchase(self):
        ref = freeze_reference(base())
        current = make_cobb_case("120", "20", "20", "0.5")
        got = compare_scenarios(ref, current)
        self.assertEqual(ref.solution.basket, make_basket("6", "3"))
        self.assertEqual(got.current_solution.basket, make_basket("3", "3"))
        self.assertEqual(got.reference_repurchase_cost, D(180))
        self.assertEqual(got.reference_affordability, "inacessivel")
        self.assertEqual(got.change_kind, "precos")
        self.assertEqual(got.utility_order, "menor")

    def test_change_income_joint_and_homothetic(self):
        ref = freeze_reference(base())
        income = compare_scenarios(ref, make_cobb_case("180", "10", "20", "0.5"))
        self.assertEqual(income.change_kind, "renda")
        self.assertEqual(income.current_solution.basket, make_basket("9", "4.5"))
        self.assertEqual(income.utility_order, "maior")
        joint = compare_scenarios(ref, make_cobb_case("180", "20", "20", "0.5"))
        self.assertEqual(joint.change_kind, "conjunto")
        self.assertEqual(joint.current_solution.basket, make_basket("4.5", "4.5"))
        double = compare_scenarios(ref, make_cobb_case("240", "20", "40", "0.5"))
        self.assertEqual(double.utility_order, "igual")
        self.assertEqual(double.current_solution.exact_basket, ref.solution.exact_basket)
        self.assertNotEqual(double.change_kind, "identico")

    def test_tiny_price_change_preserves_ordinal_order(self):
        px = "10." + "0" * 99 + "1"
        result = compare_scenarios(freeze_reference(base()),
                                   make_cobb_case("120", px, "20", "0.5"))
        self.assertEqual(result.utility_order, "menor")
        self.assertEqual(result.reference_affordability, "inacessivel")
        self.assertEqual(result.reference_repurchase_balance, D("-6e-100"))

    def test_equal_utility_with_different_budget_and_basket(self):
        result = compare_scenarios(freeze_reference(base()),
                                   make_cobb_case("120", "5", "40", "0.5"))
        self.assertEqual(result.utility_order, "igual")
        self.assertEqual(result.current_solution.basket, make_basket("12", "1.5"))
        self.assertNotEqual(result.current_solution.basket, result.reference.solution.basket)

    def test_comparison_requires_fixed_preference(self):
        with self.assertRaises(DomainError):
            compare_scenarios(freeze_reference(base()),
                              make_cobb_case("120", "10", "20", "0.6"))

    def test_compensation_duality_at_original_prices(self):
        case = base()
        original = solve_cobb(case)
        result = compensate(case.budget, case.alpha, original.utility)
        self.assertEqual(result.status, "calculado")
        self.assertLess(abs(result.expenditure - D(120)), D("1e-70"))
        self.assertLess(abs(result.basket.x - D(6)), D("1e-70"))
        self.assertLess(abs(result.basket.y - D(3)), D("1e-70"))
        dual = solve_cobb(make_cobb_case(result.expenditure, "10", "20", "0.5"))
        self.assertLess(abs(dual.utility - original.utility), D("1e-70"))

    def test_hicks_canonical_independent_sqrt_oracle(self):
        result = hicks_decomposition(freeze_reference(base()),
                                     make_cobb_case("120", "20", "20", "0.5"))
        self.assertEqual(result.status, "calculado")
        with localcontext() as ctx:
            ctx.prec = 100
            root = D(18).sqrt()
            self.assertLess(abs(result.compensated.x - root), D("1e-90"))
            self.assertLess(abs(result.compensated.y - root), D("1e-90"))
            self.assertLess(abs(result.expenditure - 40 * root), D("1e-88"))
            self.assertLess(abs(result.substitution.x - (root - 6)), D("1e-90"))
            self.assertLess(abs(result.income_effect.x - (3 - root)), D("1e-90"))
        self.assertEqual((result.total.x, result.total.y), (D(-3), D(0)))

    def test_hicks_identity_and_duality_residuals(self):
        result = hicks_decomposition(freeze_reference(base()),
                                     make_cobb_case("120", "20", "20", "0.5"))
        with localcontext() as ctx:
            ctx.prec = 100
            self.assertLess(abs(result.substitution.x + result.income_effect.x -
                                result.total.x), D("1e-90"))
            self.assertLess(abs(result.substitution.y + result.income_effect.y -
                                result.total.y), D("1e-90"))
            self.assertLess(abs(result.utility_residual), D("1e-100"))
            self.assertLess(abs(result.expenditure_residual), D("1e-100"))

    def test_hicks_proportional_price_structural_zero(self):
        result = hicks_decomposition(freeze_reference(base()),
                                     make_cobb_case("120", "20", "40", "0.5"))
        self.assertEqual(result.status, "calculado")
        self.assertEqual((result.substitution.x, result.substitution.y), (D(0), D(0)))
        self.assertEqual((result.compensated.x, result.compensated.y), (D(6), D(3)))
        self.assertEqual(result.income_effect, result.total)
        self.assertEqual((result.utility_residual, result.expenditure_residual), (D(0), D(0)))
        other = freeze_reference(make_cobb_case("120", "10", "20", "0.25"))
        proportional = hicks_decomposition(other, make_cobb_case("120", "20", "40", "0.25"))
        self.assertEqual(proportional.compensated, make_basket("3", "4.5"))
        self.assertEqual(proportional.substitution, make_basket("0", "0"))

    def test_hicks_tiny_nonzero_raises_precision(self):
        px = "10." + "0" * 99 + "1"
        result = hicks_decomposition(freeze_reference(base()),
                                     make_cobb_case("120", px, "20", "0.5"))
        self.assertEqual(result.status, "calculado")
        self.assertGreaterEqual(result.precision, 134)
        self.assertLess(result.substitution.x, 0)
        self.assertNotEqual(result.substitution.x, 0)
        self.assertLess(abs(result.substitution.x + D("3e-101")), D("1e-120"))

    def test_hicks_eligibility(self):
        ref = freeze_reference(base())
        cases = [make_cobb_case("120", "10", "20", "0.5"),
                 make_cobb_case("121", "20", "20", "0.5"),
                 make_cobb_case("120", "20", "20", "0.6")]
        for case in cases:
            self.assertEqual(hicks_decomposition(ref, case).status, "inaplicavel")

    def test_inconclusive_when_guard_precision_unavailable(self):
        policy = NumericalPolicy(max_derived_precision=80)
        result = hicks_decomposition(freeze_reference(base()),
                                     make_cobb_case("120", "20", "20", "0.5"),
                                     policy=policy)
        self.assertEqual(result.status, "inconclusivo")
        self.assertIsNone(result.compensated)
        self.assertEqual(compensate(base().budget, D("0.5"), D("4"),
                                    policy=policy).status, "inconclusivo")
        tiny = "10." + "0" * 499 + "1"
        difficult = hicks_decomposition(freeze_reference(base()),
                                         make_cobb_case("120", tiny, "20", "0.5"))
        self.assertEqual(difficult.status, "inconclusivo")
        self.assertIsNone(difficult.substitution)

    def test_manual_basket_no_economic_upper_bound(self):
        huge = make_basket("1e2000", "2")
        result = assess_basket(solve_cobb(base()), huge)
        self.assertEqual(result.optimality, "inconclusiva")
        self.assertIn("proteção", result.reason)

    def test_candidate_envelope_and_invalid_inputs(self):
        make_cobb_case("1e-6", "1e6", "1e-6", "1e-12")
        make_cobb_case("1e6", "1e-6", "1e6", "0.999999999999")
        for args in [("0", "10", "20", "0.5"), ("120", "0", "20", "0.5"),
                     ("120", "10", "20", "1"), ("120", "10", "20", "NaN"),
                     ("1.000001e6", "10", "20", "0.5"),
                     ("120", "10", "20", "0.999999999999000001")]:
            with self.subTest(args=args), self.assertRaises(DomainError):
                make_cobb_case(*args)
        with self.assertRaises(DomainError):
            make_basket("-1", "2")
        with self.assertRaises(DomainError):
            make_basket("Infinity", "2")
        with self.assertRaises(DomainError):
            make_budget(120.0, "10", "20")

    def test_core_has_no_visual_or_legacy_imports(self):
        tree = ast.parse((Path(__file__).parent / "modulo_03" / "nucleo.py").read_text(encoding="utf-8"))
        modules = [node.module or "" for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom)]
        modules += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names]
        self.assertFalse(any(name.startswith(("streamlit", "plotly", "modelo_mercado",
                                              "experimentos", "modulo_02")) for name in modules))


if __name__ == "__main__":
    unittest.main()

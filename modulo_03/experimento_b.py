"""Projeção determinística do Experimento B, independente da interface.

O núcleo calcula escolhas, recompra e ordem ordinal. ``float`` é usado
exclusivamente nos objetos enviados ao gráfico.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from .livre import _curve, safe_float
from .nucleo import (CobbCase, Reference, ScenarioComparison,
                     compare_scenarios, freeze_reference, make_cobb_case)


INITIAL = {"R": "120", "PX": "10", "PY": "20", "A": "0.5"}


def case_from(values: dict[str, str], *, alpha: Decimal | None = None) -> CobbCase:
    return make_cobb_case(values["R"], values["PX"], values["PY"],
                          values["A"] if alpha is None else alpha)


def fix_reference(values: dict[str, str]) -> Reference:
    return freeze_reference(case_from(values))


def compare(reference: Reference, values: dict[str, str]) -> ScenarioComparison:
    return compare_scenarios(reference, case_from(values, alpha=reference.case.alpha))


def reference_values(reference: Reference) -> dict[str, str]:
    b = reference.case.budget
    return {"R": str(b.income), "PX": str(b.price_x), "PY": str(b.price_y),
            "A": str(reference.case.alpha)}


def budgets_coincide(reference: Reference, current: CobbCase) -> bool:
    """Compara interceptos como frações exatas, inclusive sob homogeneidade."""
    old, new = reference.case.budget, current.budget
    return (Fraction(old.income) / Fraction(old.price_x) ==
            Fraction(new.income) / Fraction(new.price_x) and
            Fraction(old.income) / Fraction(old.price_y) ==
            Fraction(new.income) / Fraction(new.price_y))


def automatic_view(current: CobbCase,
                   comparison: ScenarioComparison | None) -> dict[str, list[float]]:
    budgets = [current.budget]
    if comparison:
        budgets.append(comparison.reference.case.budget)
    xs = [safe_float(b.income / b.price_x) for b in budgets]
    ys = [safe_float(b.income / b.price_y) for b in budgets]
    if comparison:
        for basket in (comparison.reference.solution.basket,
                       comparison.current_solution.basket):
            xs.append(safe_float(basket.x))
            ys.append(safe_float(basket.y))
    xmax = max((x for x in xs if x is not None), default=1.0)
    ymax = max((y for y in ys if y is not None), default=1.0)
    return {"x": [0.0, max(xmax * 1.12, 1e-24)],
            "y": [0.0, max(ymax * 1.12, 1e-24)]}


def interpretation(comparison: ScenarioComparison) -> str:
    kind = comparison.change_kind
    if kind == "identico":
        summary = "Os parâmetros atuais coincidem com a referência."
    elif kind == "renda":
        summary = "Somente a renda mudou; os preços e as preferências permanecem constantes."
    elif kind == "precos":
        summary = "Um ou ambos os preços mudaram; renda e preferências permanecem constantes."
    else:
        summary = ("Renda e preço(s) mudaram conjuntamente; a variação total da cesta "
                   "não pode ser atribuída a um único fator sem comparação adicional.")
    if kind != "identico" and budgets_coincide(comparison.reference, comparison.current):
        summary += " Os valores nominais diferem, mas a restrição real e a cesta ótima coincidem."
    order = {"maior": "U(C) > U(A)", "igual": "U(C) = U(A)",
             "menor": "U(C) < U(A)", "inconclusiva": "ordem de utilidade inconclusiva"}
    return summary + " Sob as mesmas preferências, " + order[comparison.utility_order] + "."


def plot_data(current: CobbCase, comparison: ScenarioComparison | None,
              *, curve_a: bool, curve_c: bool,
              view: dict[str, list[float]]) -> tuple[list[dict], list[str], dict[str, str]]:
    warnings: list[str] = []
    targets: dict[str, str] = {}

    def budget_trace(case: CobbCase, name: str, dash: str, color: str) -> dict:
        b = case.budget
        return {"x": [0.0, safe_float(b.income / b.price_x)],
                "y": [safe_float(b.income / b.price_y), 0.0],
                "mode": "lines", "name": name, "hoverinfo": "skip",
                "line": {"color": color, "width": 2.5, "dash": dash}}

    if comparison is None:
        return [budget_trace(current, "Restrição atual", "solid", "#2878B5")], warnings, targets

    reference = comparison.reference
    if budgets_coincide(reference, current):
        traces = [budget_trace(current, "Restrições de referência e atual coincidentes",
                               "solid", "#2878B5")]
    else:
        traces = [budget_trace(reference.case, "Restrição de referência", "dash", "#867A9B"),
                  budget_trace(current, "Restrição atual", "solid", "#2878B5")]

    if curve_a or curve_c:
        same_level = comparison.utility_order == "igual"
        curve_specs = []
        if curve_a and curve_c and same_level:
            curve_specs.append((reference.solution, "Indiferença de A = C", "#7353A6"))
        else:
            if curve_a:
                curve_specs.append((reference.solution, "Indiferença de A", "#AD4561"))
            if curve_c:
                curve_specs.append((comparison.current_solution, "Indiferença de C", "#177E70"))
        for solution, name, color in curve_specs:
            if solution.utility is None:
                warnings.append(f"{name} indisponível: utilidade inconclusiva.")
                continue
            xs, ys = _curve(solution.utility, reference.case.alpha, view)
            if not any(x is not None for x in xs):
                warnings.append(f"{name} fora da escala representável.")
            traces.append({"x": xs, "y": ys, "mode": "lines", "name": name,
                           "hoverinfo": "skip",
                           "line": {"color": color, "width": 1.8, "dash": "dot"}})

    a, c = reference.solution.basket, comparison.current_solution.basket
    if reference.solution.exact_basket == comparison.current_solution.exact_basket:
        traces.append({"x": [safe_float(a.x)], "y": [safe_float(a.y)],
                       "mode": "markers+text", "name": "A = C · referência e atual",
                       "text": ["A = C"], "textposition": "top center",
                       "marker": {"symbol": "diamond", "size": 15, "color": "#7353A6"}})
        targets[str(len(traces) - 1)] = "A=C"
    else:
        # A decisão econômica usa as frações exatas acima; esta distância serve
        # somente para reconhecer marcadores indistinguíveis na tela.
        ax, ay, cx, cy = (safe_float(v) for v in (a.x, a.y, c.x, c.y))
        overlap = (all(v is not None for v in (ax, ay, cx, cy)) and
                   abs(ax - cx) < abs(view["x"][1] - view["x"][0]) / 500 and
                   abs(ay - cy) < abs(view["y"][1] - view["y"][0]) / 500)
        if overlap:
            warnings.append("A e C diferem economicamente, mas coincidem na resolução do gráfico. Consulte os indicadores.")
        for name, basket, symbol, color in (
            ("A", a, "circle", "#AD4561"),
            ("C", c, "square", "#177E70"),
        ):
            traces.append({"x": [safe_float(basket.x)], "y": [safe_float(basket.y)],
                           "mode": "markers+text", "name": f"Cesta {name}",
                           "text": [name], "textposition": "top center",
                           "marker": {"symbol": symbol,
                                      "size": (18 if name == "A" else 10) if overlap else 14,
                                      "color": color}})
            targets[str(len(traces) - 1)] = name
    return traces, warnings, targets

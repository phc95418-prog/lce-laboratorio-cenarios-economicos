"""Projeção determinística do Experimento B, independente da interface.

O núcleo calcula escolhas, recompra e ordem ordinal. ``float`` é usado
exclusivamente nos objetos enviados ao gráfico.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from .livre import _curve, safe_float
from .nucleo import (Basket, CobbCase, HicksResult, Reference, ScenarioComparison,
                     compare_scenarios, freeze_reference, hicks_decomposition,
                     make_cobb_case)


INITIAL = {"R": "120", "PX": "10", "PY": "20", "A": "0.5"}


def case_from(values: dict[str, str], *, alpha: Decimal | None = None) -> CobbCase:
    return make_cobb_case(values["R"], values["PX"], values["PY"],
                          values["A"] if alpha is None else alpha)


def fix_reference(values: dict[str, str]) -> Reference:
    return freeze_reference(case_from(values))


def compare(reference: Reference, values: dict[str, str]) -> ScenarioComparison:
    return compare_scenarios(reference, case_from(values, alpha=reference.case.alpha))


def hicks(reference: Reference, current: CobbCase) -> HicksResult:
    """Delega elegibilidade, cálculo e classificação numérica ao núcleo."""
    return hicks_decomposition(reference, current)


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
                   comparison: ScenarioComparison | None,
                   hicks_result: HicksResult | None = None) -> dict[str, list[float]]:
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
    if hicks_result is not None and hicks_result.status == "calculado":
        xs.extend((safe_float(hicks_result.compensated.x),
                   safe_float(hicks_result.expenditure / current.budget.price_x)))
        ys.extend((safe_float(hicks_result.compensated.y),
                   safe_float(hicks_result.expenditure / current.budget.price_y)))
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
              view: dict[str, list[float]],
              hicks_result: HicksResult | None = None) -> tuple[list[dict], list[str], dict[str, str]]:
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
    active = hicks_result is not None and hicks_result.status == "calculado"
    sub_zero = active and hicks_result.substitution == Basket(Decimal(0), Decimal(0))
    income_zero = active and comparison.utility_order == "igual"
    if budgets_coincide(reference, current):
        traces = [budget_trace(current, "Restrições de referência e atual coincidentes",
                               "solid", "#2878B5")]
    else:
        reference_name = ("Restrições de referência e compensada coincidentes" if sub_zero
                          else "Restrição de referência")
        current_name = ("Restrições atual e compensada coincidentes" if income_zero
                        else "Restrição atual")
        traces = [budget_trace(reference.case, reference_name, "dash", "#867A9B"),
                  budget_trace(current, current_name, "solid", "#2878B5")]

    if active and not sub_zero and not income_zero:
        compensated_budget = CobbCase(
            type(current.budget)(hicks_result.expenditure,
                                 current.budget.price_x, current.budget.price_y),
            current.alpha)
        traces.append(budget_trace(compensated_budget, "Restrição compensada",
                                   "dashdot", "#A36A1B"))

    if curve_a or curve_c or active:
        same_level = comparison.utility_order == "igual"
        curve_specs = []
        if (curve_a or active) and curve_c and same_level:
            curve_specs.append((reference.solution, "Indiferença inicial e final coincidentes", "#7353A6"))
        else:
            if curve_a or active:
                curve_specs.append((reference.solution,
                                    "Indiferença inicial de A e H" if active else "Indiferença de A",
                                    "#AD4561"))
            if curve_c:
                curve_specs.append((comparison.current_solution, "Indiferença de C", "#177E70"))
        for solution, name, color in curve_specs:
            if solution.utility is None:
                warnings.append(f"{name} indisponível: utilidade inconclusiva.")
                continue
            xs, ys = _curve(solution.utility, reference.case.alpha, view)
            if not any(x is not None for x in xs):
                warnings.append(f"{name} fora da escala representável.")
            elif active:
                # A curva desenhada passa pelos marcadores econômicos, além da
                # amostragem visual feita por _curve. Nenhum ponto volta ao motor.
                points = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
                anchors = ((reference.solution.basket, hicks_result.compensated)
                           if solution is reference.solution else
                           (comparison.current_solution.basket,))
                for basket in anchors:
                    x, y = safe_float(basket.x), safe_float(basket.y)
                    if x is not None and y is not None:
                        points.append((x, y))
                points.sort(key=lambda point: point[0])
                xs, ys = ([point[0] for point in points],
                          [point[1] for point in points])
            traces.append({"x": xs, "y": ys, "mode": "lines", "name": name,
                           "hoverinfo": "skip",
                           "line": {"color": color, "width": 1.8, "dash": "dot"}})

    a, c = reference.solution.basket, comparison.current_solution.basket
    if active and sub_zero:
        marker_specs = (("A = H", a, "diamond", "#AD4561", "A=H"),
                        ("C", c, "square", "#177E70", "C"))
    elif active and income_zero:
        marker_specs = (("A", a, "circle", "#AD4561", "A"),
                        ("H = C", c, "diamond", "#A36A1B", "H=C"))
    elif active:
        marker_specs = (("A", a, "circle", "#AD4561", "A"),
                        ("H", hicks_result.compensated, "diamond", "#A36A1B", "H"),
                        ("C", c, "square", "#177E70", "C"))
    else:
        marker_specs = ()
    if active:
        for label, basket, symbol, color, target in marker_specs:
            traces.append({"x": [safe_float(basket.x)], "y": [safe_float(basket.y)],
                           "mode": "markers+text", "name": f"Cesta {label}",
                           "text": [label], "textposition": "top center",
                           "marker": {"symbol": symbol, "size": 15, "color": color}})
            targets[str(len(traces) - 1)] = target
    elif reference.solution.exact_basket == comparison.current_solution.exact_basket:
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


def effect_annotation(comparison: ScenarioComparison, hicks_result: HicksResult,
                      effect: str) -> tuple[dict | None, str | None]:
    """Projeta uma relação analítica no gráfico, sem decidir a economia por float."""
    if hicks_result.status != "calculado":
        return None, None
    a = comparison.reference.solution.basket
    h = hicks_result.compensated
    c = comparison.current_solution.basket
    start, end, difference = {
        "Substituição": (a, h, hicks_result.substitution),
        "Renda": (h, c, hicks_result.income_effect),
        "Total": (a, c, hicks_result.total),
    }[effect]
    if difference == Basket(Decimal(0), Decimal(0)):
        return None, f"Efeito {effect.lower()} exatamente nulo; nenhuma seta é desenhada."
    sx, sy, ex, ey = (safe_float(v) for v in (start.x, start.y, end.x, end.y))
    if None in (sx, sy, ex, ey) or (sx == ex and sy == ey):
        return None, (f"Efeito {effect.lower()} não representável na resolução do gráfico; "
                      "os valores econômicos continuam disponíveis nos indicadores.")
    return {"x": ex, "y": ey, "ax": sx, "ay": sy,
            "xref": "x", "yref": "y", "axref": "x", "ayref": "y",
            "showarrow": True, "arrowhead": 3, "arrowsize": 1.2,
            "arrowwidth": 2.5, "arrowcolor": "#C15525", "text": ""}, None

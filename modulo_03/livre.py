"""Estado e projeção gráfica da Exploração livre, sem Streamlit.

O cálculo econômico permanece em ``nucleo``. Os floats produzidos aqui servem
somente ao desenho e aos controles de navegação visual.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import exp, isfinite, log

from .nucleo import Basket, CobbCase, Solution


INITIAL = {"R": "120", "PX": "10", "PY": "20", "A": "0.5"}
SLIDER_RANGES = {"R": (Decimal("20"), Decimal("1000"), Decimal("1")),
                 "PX": (Decimal("1"), Decimal("100"), Decimal("1")),
                 "PY": (Decimal("1"), Decimal("100"), Decimal("1")),
                 "A": (Decimal("0.05"), Decimal("0.95"), Decimal("0.01"))}


@dataclass(frozen=True)
class SliderSpec:
    minimum: float
    maximum: float
    step: float
    position: float
    approximate: bool
    expanded: bool


def slider_spec(name: str, exact: Decimal) -> SliderSpec:
    """Expande a faixa sem converter o valor econômico armazenado em float."""
    low, high, step = SLIDER_RANGES[name]
    expanded = exact < low or exact > high
    lower = exact if exact < low else low
    upper = exact if exact > high else high
    position = float(exact)
    return SliderSpec(float(lower), float(upper), float(step), position,
                      Decimal(str(position)) != exact, expanded)


def safe_float(value: Decimal) -> float | None:
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    return number if isfinite(number) else None


def automatic_view(case: CobbCase, solution: Solution, manual: Basket | None,
                   *, show_optimum: bool) -> dict[str, list[float]]:
    """Inclui os objetos visíveis; assimetrias podem exigir foco local posterior."""
    b = case.budget
    x_values = [safe_float(b.income / b.price_x)]
    y_values = [safe_float(b.income / b.price_y)]
    if manual:
        x_values.append(safe_float(manual.x))
        y_values.append(safe_float(manual.y))
    if show_optimum and solution.basket:
        x_values.append(safe_float(solution.basket.x))
        y_values.append(safe_float(solution.basket.y))
    mx = max((v for v in x_values if v is not None), default=1.0)
    my = max((v for v in y_values if v is not None), default=1.0)
    return {"x": [0.0, max(mx * 1.12, 1e-24)],
            "y": [0.0, max(my * 1.12, 1e-24)]}


def focus_view(target: Basket) -> dict[str, list[float]] | None:
    """Enquadra localmente um objeto, preservando o comando de visão completa."""
    x, y = safe_float(target.x), safe_float(target.y)
    if x is None or y is None:
        return None
    span_x = max(abs(x) * 0.35, 1e-24)
    span_y = max(abs(y) * 0.35, 1e-24)
    return {"x": [max(0.0, x - span_x), x + span_x],
            "y": [max(0.0, y - span_y), y + span_y]}


def _curve(level: Decimal, alpha: Decimal, view: dict[str, list[float]]) -> tuple[list[float | None], list[float | None]]:
    xmax, ymax = view["x"][1], view["y"][1]
    if level == 0:
        return [0.0, xmax, None, 0.0, 0.0], [0.0, 0.0, None, 0.0, ymax]
    u = safe_float(level)
    if u is None or u <= 0 or xmax <= 0:
        return [], []
    a = float(alpha)
    beta = 1.0 - a
    if beta <= 0:
        return [], []
    lo = max(xmax * 1e-8, 1e-300)
    xs: list[float | None] = []
    ys: list[float | None] = []
    for i in range(161):
        x = exp(log(lo) + (log(xmax) - log(lo)) * i / 160)
        try:
            y = exp((log(u) - a * log(x)) / beta)
        except OverflowError:
            y = float("inf")
        xs.append(x if isfinite(y) and 0 <= y <= ymax * 5 else None)
        ys.append(y if isfinite(y) and 0 <= y <= ymax * 5 else None)
    return xs, ys


def plot_data(case: CobbCase, solution: Solution, manual: Basket | None,
              *, manual_curve: bool, optimum: bool, optimum_curve: bool,
              view: dict[str, list[float]]) -> tuple[list[dict], list[str]]:
    b = case.budget
    warnings: list[str] = []
    xmax = safe_float(b.income / b.price_x)
    ymax = safe_float(b.income / b.price_y)
    if xmax is None or ymax is None:
        return [], ["Escala da restrição não representável no gráfico."]
    traces = [{"x": [0, xmax], "y": [ymax, 0], "mode": "lines",
               "name": "Restrição orçamentária", "line": {"color": "#2878B5", "width": 3}}]
    if manual_curve and manual:
        # A curva é visual; a utilidade vem do núcleo, nunca dos pontos desenhados.
        from .nucleo import assess_basket
        assessment = assess_basket(solution, manual)
        if assessment.utility is not None:
            xs, ys = _curve(assessment.utility, case.alpha, view)
            if not any(x is not None for x in xs):
                warnings.append("Curva manual não representável nesta escala; a utilidade econômica permanece preservada.")
            traces.append({"x": xs, "y": ys, "mode": "lines", "name": "Indiferença da cesta manual",
                           "line": {"color": "#AE4561", "width": 1.8, "dash": "dot"}})
        else:
            warnings.append("Curva manual indisponível: utilidade inconclusiva.")
    if optimum_curve:
        if solution.utility is not None:
            xs, ys = _curve(solution.utility, case.alpha, view)
            if not any(x is not None for x in xs):
                warnings.append("Curva ótima não representável nesta escala; a solução econômica permanece preservada.")
            traces.append({"x": xs, "y": ys, "mode": "lines", "name": "Indiferença ótima",
                           "line": {"color": "#21805C", "width": 1.8, "dash": "dot"}})
        else:
            warnings.append("Curva ótima indisponível: utilidade inconclusiva.")
    if manual:
        x, y = safe_float(manual.x), safe_float(manual.y)
        if x is None or y is None:
            warnings.append("Cesta manual fora da escala representável; os campos econômicos permanecem preservados.")
        else:
            traces.append({"x": [x], "y": [y], "mode": "markers+text",
                           "name": "Cesta manual", "text": ["Manual"], "textposition": "top center",
                           "marker": {"symbol": "circle", "size": 13, "color": "#AE4561"}})
    if optimum and solution.basket:
        x, y = safe_float(solution.basket.x), safe_float(solution.basket.y)
        if x is not None and y is not None:
            traces.append({"x": [x], "y": [y], "mode": "markers+text",
                           "name": "Solução ótima", "text": ["Ótimo"], "textposition": "top center",
                           "marker": {"symbol": "square", "size": 13, "color": "#21805C"}})
    return traces, warnings


def objects_outside(view: dict[str, list[float]], manual: Basket | None,
                    optimum: Basket | None) -> bool:
    for basket in (manual, optimum):
        if not basket:
            continue
        x, y = safe_float(basket.x), safe_float(basket.y)
        if x is None or y is None or not (view["x"][0] <= x <= view["x"][1]
                                        and view["y"][0] <= y <= view["y"][1]):
            return True
    return False

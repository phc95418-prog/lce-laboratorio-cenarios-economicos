"""Projeções determinísticas da comparação de dois consumidores Cobb–Douglas.

O cálculo econômico pertence a ``nucleo``. Valores float aparecem somente nos
dados destinados ao gráfico.
"""

from __future__ import annotations

from decimal import Decimal, localcontext

from .livre import _curve, safe_float
from .nucleo import ConsumerComparison, make_budget, compare_consumers


INITIAL = {"R": "120", "PX": "10", "PY": "20", "AA": "0.25", "AB": "0.75"}


def calculate(values: dict[str, str]) -> ConsumerComparison:
    budget = make_budget(values["R"], values["PX"], values["PY"])
    return compare_consumers(budget, values["AA"], values["AB"])


def shares(comparison: ConsumerComparison) -> tuple[tuple[Decimal, Decimal],
                                                       tuple[Decimal, Decimal]]:
    """Parcelas exatas derivadas dos parâmetros já validados pelo núcleo."""
    alphas = (comparison.consumer_a.alpha, comparison.consumer_b.alpha)
    with localcontext() as ctx:
        ctx.prec = max(80, *(len(a.as_tuple().digits) + 4 for a in alphas))
        return tuple((a * 100, (Decimal(1) - a) * 100) for a in alphas)


def share_differences(comparison: ConsumerComparison) -> tuple[Decimal, Decimal]:
    (ax, ay), (bx, by) = shares(comparison)
    with localcontext() as ctx:
        ctx.prec = max(80, *(len(v.as_tuple().digits) + 4 for v in (ax, ay, bx, by)))
        return bx - ax, by - ay


def interpretation(comparison: ConsumerComparison) -> str:
    if comparison.consumer_a.alpha == comparison.consumer_b.alpha:
        return ("Com as mesmas preferências e o mesmo orçamento, A e B escolhem "
                "a mesma cesta ótima. Os perfis continuam identificados separadamente.")
    return ("A e B enfrentam a mesma renda e os mesmos preços. As diferenças "
            "entre suas cestas ótimas decorrem das preferências distintas e das "
            "participações orçamentárias correspondentes. Os números de utilidade "
            "não permitem comparar o bem-estar entre consumidores.")


def automatic_view(comparison: ConsumerComparison) -> dict[str, list[float]]:
    b = comparison.consumer_a.budget
    x, y = safe_float(b.income / b.price_x), safe_float(b.income / b.price_y)
    if x is None or y is None:
        return {"x": [0.0, 1.0], "y": [0.0, 1.0]}
    return {"x": [0.0, max(x * 1.12, 1e-24)],
            "y": [0.0, max(y * 1.12, 1e-24)]}


def plot_data(comparison: ConsumerComparison, *, curve_a: bool, curve_b: bool,
              view: dict[str, list[float]]) -> tuple[list[dict], list[str], dict[str, str]]:
    b = comparison.consumer_a.budget
    x_max, y_max = safe_float(b.income / b.price_x), safe_float(b.income / b.price_y)
    if x_max is None or y_max is None:
        return [], ["Restrição fora da escala gráfica; cálculos econômicos preservados."], {}
    traces: list[dict] = [{"x": [0.0, x_max], "y": [y_max, 0.0], "mode": "lines",
                           "name": "Restrição orçamentária comum",
                           "hoverinfo": "skip",
                           "line": {"color": "#2878B5", "width": 3}}]
    warnings: list[str] = []
    click_targets: dict[str, str] = {}
    for profile, solution, enabled, color in (
        ("A", comparison.consumer_a, curve_a, "#AD4561"),
        ("B", comparison.consumer_b, curve_b, "#177E70"),
    ):
        if not enabled:
            continue
        if solution.utility is None:
            warnings.append(f"Curva de {profile} indisponível: utilidade inconclusiva.")
            continue
        xs, ys = _curve(solution.utility, solution.alpha, view)
        if not xs:
            warnings.append(f"Curva de {profile} fora da escala gráfica representável.")
        traces.append({"x": xs, "y": ys, "mode": "lines",
                       "name": f"Indiferença ótima de {profile}",
                       "hoverinfo": "skip",
                       "line": {"color": color, "width": 2, "dash": "dot"}})

    a, z = comparison.consumer_a.basket, comparison.consumer_b.basket
    if comparison.consumer_a.exact_basket == comparison.consumer_b.exact_basket:
        x, y = safe_float(a.x), safe_float(a.y)
        traces.append({"x": [x], "y": [y], "mode": "markers+text",
                       "name": "A = B · consumidores A e B", "text": ["A = B"],
                       "textposition": "top center",
                       "marker": {"symbol": "diamond", "size": 15, "color": "#7353A6"}})
        click_targets[str(len(traces) - 1)] = "A=B"
    else:
        projected_overlap = ((safe_float(a.x), safe_float(a.y)) ==
                             (safe_float(z.x), safe_float(z.y)))
        if projected_overlap:
            warnings.append("As cestas são economicamente distintas, mas coincidem na resolução do gráfico. Consulte as diferenças nos indicadores.")
        for profile, basket, symbol, color in (
            ("A", a, "circle", "#AD4561"),
            ("B", z, "square", "#177E70"),
        ):
            traces.append({"x": [safe_float(basket.x)], "y": [safe_float(basket.y)],
                           "mode": "markers+text", "name": f"Consumidor {profile}",
                           "text": [profile], "textposition": "top center",
                           "marker": {"symbol": symbol,
                                      "size": (18 if profile == "A" else 10)
                                      if projected_overlap else 14, "color": color}})
            click_targets[str(len(traces) - 1)] = profile
    return traces, warnings, click_targets

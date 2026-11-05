"""Projeção e leitura determinística do Experimento A individual.

As decisões econômicas são delegadas integralmente a ``nucleo``. Os floats
produzidos aqui são somente coordenadas para o desenho Plotly.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .livre import _curve as cobb_curve, safe_float
from .nucleo import (Basket, BasketAssessment, Budget, Model, Solution,
                     assess_basket, make_budget, make_cobb_case, solve_cobb,
                     solve_complements, solve_substitutes)


INITIAL = {"R": "120", "PX": "10", "PY": "20", "A": "0.5"}
MODELS: dict[str, Model] = {
    "Cobb–Douglas": "cobb_douglas",
    "Substitutos perfeitos": "substitutes",
    "Complementares perfeitos": "complements",
}


@dataclass(frozen=True)
class IndividualResult:
    solution: Solution
    assessment: BasketAssessment | None


def calculate(model: Model, values: dict[str, str], manual: Basket | None) -> IndividualResult:
    """Único ponto de ligação da interface às funções aprovadas do núcleo."""
    if model == "cobb_douglas":
        solution = solve_cobb(make_cobb_case(values["R"], values["PX"],
                                             values["PY"], values["A"]))
    else:
        budget = make_budget(values["R"], values["PX"], values["PY"])
        solution = (solve_substitutes(budget) if model == "substitutes"
                    else solve_complements(budget))
    return IndividualResult(solution, assess_basket(solution, manual) if manual else None)


def diagnosis(assessment: BasketAssessment | None) -> str | None:
    if assessment is None:
        return None
    if assessment.budget_status == "inconclusivo" or assessment.optimality == "inconclusiva":
        return "A classificação ficou inconclusiva sob a proteção numérica experimental."
    if assessment.budget_status == "inacessivel":
        return "Cesta inacessível: o gasto excede a renda; ela não é uma escolha ótima viável."
    if assessment.optimality == "otima":
        return "Cesta acessível e ótima para as preferências e o orçamento atuais."
    return "Cesta acessível, mas não ótima nas condições atuais."


def explanation(solution: Solution, assessment: BasketAssessment | None) -> str:
    if assessment is None:
        return "Selecione uma cesta e ative a avaliação para examinar sua escolha."
    if assessment.budget_status == "inconclusivo" or assessment.optimality == "inconclusiva":
        return assessment.reason or "A precisão disponível não sustenta uma conclusão."
    if assessment.budget_status == "inacessivel":
        return "O custo supera a renda. A utilidade de uma cesta inacessível não a transforma em ótimo viável."
    if assessment.budget_status == "sobra":
        if solution.model == "complements":
            return "Há renda não utilizada. É possível melhorar a escolha ampliando ambos os bens; aumentar somente um deles pode não elevar a utilidade."
        return "Há renda não utilizada. Uma tangência isolada não basta: a escolha ótima também esgota o orçamento."
    if assessment.optimality == "otima":
        if solution.kind == "segment":
            return "Com preços iguais, toda a fronteira orçamentária pertence ao conjunto ótimo; não há cesta privilegiada."
        if solution.model == "complements":
            return "A cesta está na quina ótima. Uma TMS diferencial não é exigida nessa quina."
        if solution.model == "substitutes":
            return "A escolha de canto aloca a renda ao bem de menor preço por unidade."
        return "A cesta interior esgota o orçamento e satisfaz as condições de ótimo Cobb–Douglas."
    if solution.model == "cobb_douglas":
        return "O orçamento está esgotado, mas isso isoladamente não garante o ótimo: a composição dos bens difere da solução Cobb–Douglas."
    if solution.model == "substitutes":
        return "Com preços diferentes, gastar toda a renda não basta: o bem de menor preço oferece mais unidades por real."
    return "O orçamento está esgotado, mas a cesta não está na quina que iguala as quantidades dos bens."


def hint(solution: Solution, assessment: BasketAssessment | None) -> str | None:
    if assessment is None or assessment.optimality != "nao_otima":
        return None
    if assessment.budget_status == "inacessivel":
        return "Compare o custo da cesta com a renda antes de avaliar sua composição."
    if assessment.budget_status == "sobra":
        if solution.model == "complements":
            return "Examine se a sobra permite ampliar os dois bens em conjunto."
        return "Investigue o que ocorre ao utilizar a renda ainda disponível."
    if solution.model == "cobb_douglas":
        return "Com o orçamento esgotado, compare a composição da cesta com a razão entre os preços."
    if solution.model == "substitutes":
        return "Compare quantas unidades de cada bem um real pode comprar."
    return "Observe o que ocorre ao trocar parte do bem em excesso pelo bem em falta."


def automatic_view(solution: Solution, manual: Basket | None,
                   *, show_optimum: bool, show_optimum_curve: bool = False) -> dict[str, list[float]]:
    b = solution.budget
    xs = [safe_float(b.income / b.price_x)]
    ys = [safe_float(b.income / b.price_y)]
    if manual:
        xs.append(safe_float(manual.x))
        ys.append(safe_float(manual.y))
    if show_optimum or show_optimum_curve:
        baskets = solution.segment or ((solution.basket,) if solution.basket else ())
        for basket in baskets:
            xs.append(safe_float(basket.x))
            ys.append(safe_float(basket.y))
    mx = max((x for x in xs if x is not None), default=1.0)
    my = max((y for y in ys if y is not None), default=1.0)
    return {"x": [0.0, max(mx * 1.12, 1e-24)],
            "y": [0.0, max(my * 1.12, 1e-24)]}


def _indifference(model: Model, level: Decimal, alpha: Decimal | None,
                  view: dict[str, list[float]]) -> tuple[list[float | None], list[float | None]]:
    xmin, xmax = view["x"]
    ymin, ymax = view["y"]
    if model == "cobb_douglas":
        return cobb_curve(level, alpha, view)
    if level == 0:
        if model == "substitutes":
            return [0.0], [0.0]
    u = safe_float(level)
    if u is None:
        return [], []
    if model == "substitutes":
        return [0.0, u], [u, 0.0]
    xs: list[float | None] = []
    ys: list[float | None] = []
    if ymin <= u <= ymax and xmax >= u:
        xs.extend((max(u, xmin), xmax))
        ys.extend((u, u))
    if xmin <= u <= xmax and ymax >= u:
        if xs:
            xs.append(None)
            ys.append(None)
        xs.extend((u, u))
        ys.extend((max(u, ymin), ymax))
    return xs, ys


def plot_data(solution: Solution, manual: Basket | None, *, manual_curve: bool,
              optimum: bool, optimum_curve: bool,
              view: dict[str, list[float]]) -> tuple[list[dict], list[str]]:
    b = solution.budget
    xmax, ymax = safe_float(b.income / b.price_x), safe_float(b.income / b.price_y)
    if xmax is None or ymax is None:
        return [], ["Restrição fora da escala gráfica representável; cálculo econômico preservado."]
    traces = [{"x": [0, xmax], "y": [ymax, 0], "mode": "lines",
               "name": "Restrição orçamentária", "line": {"color": "#2878B5", "width": 3}}]
    warnings: list[str] = []
    assessment = assess_basket(solution, manual) if manual and manual_curve else None
    for enabled, level, name, color in (
        (manual_curve and manual, assessment.utility if assessment else None,
         "Indiferença da cesta manual", "#AE4561"),
        (optimum_curve, solution.utility, "Indiferença ótima", "#21805C"),
    ):
        if not enabled:
            continue
        if level is None:
            warnings.append(f"{name} indisponível: utilidade inconclusiva.")
            continue
        xs, ys = _indifference(solution.model, level, solution.alpha, view)
        if not xs:
            warnings.append(f"{name} fora da escala representável.")
        traces.append({"x": xs, "y": ys, "mode": "lines", "name": name,
                       "line": {"color": color, "width": 1.8, "dash": "dot"}})
    coincident = (manual is not None and solution.kind == "unique" and
                  solution.exact_basket is not None and
                  assess_basket(solution, manual).optimality == "otima")
    if manual:
        x, y = safe_float(manual.x), safe_float(manual.y)
        if x is not None and y is not None:
            joint = optimum and coincident
            traces.append({"x": [x], "y": [y], "mode": "markers+text",
                           "name": "Cesta manual = solução ótima" if joint else "Cesta manual",
                           "text": ["Manual = ótimo" if joint else "Manual"],
                           "textposition": "top center",
                           "marker": {"symbol": "circle", "size": 13, "color": "#AE4561"}})
        else:
            warnings.append("Cesta manual fora da escala gráfica representável.")
    if optimum:
        if solution.kind == "segment":
            a, z = solution.segment
            traces.append({"x": [safe_float(a.x), safe_float(z.x)],
                           "y": [safe_float(a.y), safe_float(z.y)], "mode": "lines",
                           "name": "Conjunto ótimo completo", "line": {"color": "#21805C", "width": 5}})
        elif solution.basket and not coincident:
            x, y = safe_float(solution.basket.x), safe_float(solution.basket.y)
            if x is not None and y is not None:
                traces.append({"x": [x], "y": [y], "mode": "markers+text",
                               "name": "Solução ótima", "text": ["Ótimo"],
                               "textposition": "top center",
                               "marker": {"symbol": "square", "size": 13, "color": "#21805C"}})
    return traces, warnings

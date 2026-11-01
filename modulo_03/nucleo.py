"""Escolha do consumidor: contratos matemáticos sem Streamlit, Plotly ou float.

O envelope e as proteções de recursos abaixo são candidatos técnicos revisáveis;
não ampliam nem restringem o domínio econômico definido na especificação.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from typing import Literal


NumberInput = str | int | Decimal
Model = Literal["cobb_douglas", "substitutes", "complements"]
Decision = Literal["otima", "nao_otima", "inconclusiva"]


class DomainError(ValueError):
    """Entrada fora do domínio econômico ou do envelope experimental escolhido."""


class NumericalLimit(Exception):
    """Proteção computacional atingida; não é uma classificação econômica."""


@dataclass(frozen=True)
class Envelope:
    money_min: Decimal
    money_max: Decimal
    alpha_min: Decimal
    alpha_max: Decimal


CANDIDATE_ENVELOPE = Envelope(
    Decimal("1e-6"), Decimal("1e6"), Decimal("1e-12"), Decimal("0.999999999999")
)


@dataclass(frozen=True)
class NumericalPolicy:
    initial_precision: int = 80
    guard_digits: int = 32
    max_derived_precision: int = 512
    max_exact_expanded_digits: int = 1024
    comparison_digits: int = 12
    max_exact_utility_power: int = 64


DEFAULT_POLICY = NumericalPolicy()


@dataclass(frozen=True)
class Budget:
    income: Decimal
    price_x: Decimal
    price_y: Decimal


@dataclass(frozen=True)
class Basket:
    x: Decimal
    y: Decimal


@dataclass(frozen=True)
class CobbCase:
    budget: Budget
    alpha: Decimal


@dataclass(frozen=True)
class Solution:
    model: Model
    budget: Budget
    alpha: Decimal | None
    kind: Literal["unique", "segment"]
    basket: Basket | None
    segment: tuple[Basket, Basket] | None
    exact_basket: tuple[Fraction, Fraction] | None
    utility: Decimal | None
    precision: int | None
    numerical_status: Literal["calculado", "inconclusivo"]


@dataclass(frozen=True)
class BasketAssessment:
    basket: Basket
    cost: Decimal | None
    balance: Decimal | None
    budget_status: Literal["sobra", "fronteira", "inacessivel", "inconclusivo"]
    optimality: Decision
    utility: Decimal | None
    numerical_status: Literal["calculado", "inconclusivo"]
    reason: str | None = None


@dataclass(frozen=True)
class ConsumerComparison:
    consumer_a: Solution
    consumer_b: Solution
    difference_x: Decimal
    difference_y: Decimal
    spending_a: tuple[Decimal, Decimal]
    spending_b: tuple[Decimal, Decimal]


@dataclass(frozen=True)
class Reference:
    case: CobbCase
    solution: Solution


@dataclass(frozen=True)
class ScenarioComparison:
    reference: Reference
    current: CobbCase
    current_solution: Solution
    reference_repurchase_cost: Decimal
    reference_repurchase_balance: Decimal
    reference_affordability: Literal["sobra", "fronteira", "inacessivel"]
    change_kind: Literal["identico", "renda", "precos", "conjunto"]
    utility_order: Literal["maior", "igual", "menor", "inconclusiva"]
    precision: int | None


@dataclass(frozen=True)
class Compensation:
    status: Literal["calculado", "inconclusivo"]
    expenditure: Decimal | None
    basket: Basket | None
    precision: int | None
    reason: str | None = None


@dataclass(frozen=True)
class HicksResult:
    status: Literal["calculado", "inaplicavel", "inconclusivo"]
    reason: str | None
    reference: Reference
    current: CobbCase
    compensated: Basket | None = None
    expenditure: Decimal | None = None
    substitution: Basket | None = None
    income_effect: Basket | None = None
    total: Basket | None = None
    utility_residual: Decimal | None = None
    expenditure_residual: Decimal | None = None
    precision: int | None = None


def _decimal(value: NumberInput) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise DomainError("use texto decimal, Decimal ou inteiro exato; float não é aceito")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise DomainError("entrada numérica inválida") from exc
    if not result.is_finite():
        raise DomainError("NaN e infinito não pertencem ao domínio")
    return result


def make_budget(income: NumberInput, price_x: NumberInput, price_y: NumberInput,
                *, envelope: Envelope | None = CANDIDATE_ENVELOPE) -> Budget:
    values = tuple(_decimal(v) for v in (income, price_x, price_y))
    if any(v <= 0 for v in values):
        raise DomainError("renda e preços devem ser positivos")
    if envelope and any(not envelope.money_min <= v <= envelope.money_max for v in values):
        raise DomainError("renda ou preço fora do envelope computacional candidato")
    return Budget(*values)


def make_basket(x: NumberInput, y: NumberInput) -> Basket:
    values = (_decimal(x), _decimal(y))
    if any(v < 0 for v in values):
        raise DomainError("quantidades manuais devem ser não negativas")
    return Basket(*values)


def make_cobb_case(income: NumberInput, price_x: NumberInput, price_y: NumberInput,
                   alpha: NumberInput, *, envelope: Envelope | None = CANDIDATE_ENVELOPE) -> CobbCase:
    budget = make_budget(income, price_x, price_y, envelope=envelope)
    a = _decimal(alpha)
    if not 0 < a < 1:
        raise DomainError("Cobb–Douglas exige 0 < α < 1")
    if envelope and not envelope.alpha_min <= a <= envelope.alpha_max:
        raise DomainError("α fora do envelope computacional candidato")
    return CobbCase(budget, a)


def _precision(values: tuple[Decimal, ...], policy: NumericalPolicy) -> int:
    return max(policy.initial_precision,
               max(len(v.as_tuple().digits) for v in values) + policy.guard_digits)


def _fraction(value: Decimal, policy: NumericalPolicy) -> Fraction:
    sign, digits, exponent = value.as_tuple()
    if len(digits) + abs(exponent) > policy.max_exact_expanded_digits:
        raise NumericalLimit("conversão exata excede a proteção de recursos experimental")
    return Fraction(value)


def _decimal_fraction(value: Fraction, precision: int) -> Decimal:
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        twos += 1
        denominator //= 2
    while denominator % 5 == 0:
        fives += 1
        denominator //= 5
    if denominator == 1:
        scale = max(twos, fives)
        integer = value.numerator * 2 ** (scale - twos) * 5 ** (scale - fives)
        return Decimal(f"{integer}e-{scale}")  # representação decimal exata
    with localcontext() as ctx:
        ctx.prec = precision
        return +(Decimal(value.numerator) / Decimal(value.denominator))


def _utility(x: Decimal, y: Decimal, alpha: Decimal, precision: int) -> Decimal:
    if x == 0 or y == 0:
        return Decimal(0)
    with localcontext() as ctx:
        ctx.prec = precision
        return +(alpha * x.ln() + (1 - alpha) * y.ln()).exp()


def solve_cobb(case: CobbCase, *, policy: NumericalPolicy = DEFAULT_POLICY) -> Solution:
    b, a = case.budget, case.alpha
    r, px, py, af = (_fraction(v, policy) for v in (b.income, b.price_x, b.price_y, a))
    exact = (af * r / px, (1 - af) * r / py)
    precision = _precision((b.income, b.price_x, b.price_y, a), policy)
    work = min(precision, policy.max_derived_precision)
    chosen = Basket(*(_decimal_fraction(v, work) for v in exact))
    confident = precision <= policy.max_derived_precision
    return Solution("cobb_douglas", b, a, "unique", chosen, None, exact,
                    _utility(chosen.x, chosen.y, a, work) if confident else None,
                    work, "calculado" if confident else "inconclusivo")


def solve_substitutes(budget: Budget, *, policy: NumericalPolicy = DEFAULT_POLICY) -> Solution:
    r, px, py = (_fraction(v, policy) for v in (budget.income, budget.price_x, budget.price_y))
    precision = _precision((budget.income, budget.price_x, budget.price_y), policy)
    work = min(precision, policy.max_derived_precision)
    confident = precision <= policy.max_derived_precision
    if px == py:
        endpoints = (Basket(_decimal_fraction(r / px, work), Decimal(0)),
                     Basket(Decimal(0), _decimal_fraction(r / py, work)))
        return Solution("substitutes", budget, None, "segment", None, endpoints,
                        None, _decimal_fraction(r / px, work) if confident else None,
                        work, "calculado" if confident else "inconclusivo")
    exact = (r / px, Fraction(0)) if px < py else (Fraction(0), r / py)
    chosen = Basket(*(_decimal_fraction(v, work) for v in exact))
    return Solution("substitutes", budget, None, "unique", chosen, None, exact,
                    chosen.x + chosen.y if confident else None, work,
                    "calculado" if confident else "inconclusivo")


def solve_complements(budget: Budget, *, policy: NumericalPolicy = DEFAULT_POLICY) -> Solution:
    r, px, py = (_fraction(v, policy) for v in (budget.income, budget.price_x, budget.price_y))
    z = r / (px + py)
    precision = _precision((budget.income, budget.price_x, budget.price_y), policy)
    work = min(precision, policy.max_derived_precision)
    confident = precision <= policy.max_derived_precision
    chosen = Basket(_decimal_fraction(z, work), _decimal_fraction(z, work))
    return Solution("complements", budget, None, "unique", chosen, None, (z, z),
                    chosen.x if confident else None, work,
                    "calculado" if confident else "inconclusivo")


def _cost(budget: Budget, basket: Basket, policy: NumericalPolicy) -> tuple[Fraction, Fraction]:
    r, px, py, x, y = (_fraction(v, policy) for v in
                        (budget.income, budget.price_x, budget.price_y, basket.x, basket.y))
    cost = px * x + py * y
    return cost, r - cost


def assess_basket(solution: Solution, basket: Basket,
                  *, policy: NumericalPolicy = DEFAULT_POLICY) -> BasketAssessment:
    try:
        cost, balance = _cost(solution.budget, basket, policy)
        x, y = _fraction(basket.x, policy), _fraction(basket.y, policy)
    except NumericalLimit as exc:
        return BasketAssessment(basket, None, None, "inconclusivo", "inconclusiva",
                                None, "inconclusivo", str(exc))
    status = "fronteira" if balance == 0 else "sobra" if balance > 0 else "inacessivel"
    if solution.kind == "segment":
        is_optimal = balance == 0  # preços iguais: toda a fronteira, sem representante
    else:
        is_optimal = balance == 0 and (x, y) == solution.exact_basket
    precision = _precision((basket.x, basket.y, solution.budget.income,
                            solution.budget.price_x, solution.budget.price_y), policy)
    work = min(precision, policy.max_derived_precision)
    if solution.model == "cobb_douglas" and precision <= policy.max_derived_precision:
        util = _utility(basket.x, basket.y, solution.alpha, work)
    elif solution.model == "substitutes":
        util = _decimal_fraction(x + y, work)
    elif solution.model == "complements":
        util = min(basket.x, basket.y)
    else:
        util = None
    return BasketAssessment(basket, _decimal_fraction(cost, work),
                            _decimal_fraction(balance, work), status,
                            "otima" if is_optimal else "nao_otima", util,
                            "calculado" if util is not None else "inconclusivo",
                            None if util is not None else "precisão derivada acima da proteção experimental")


def compare_consumers(budget: Budget, alpha_a: NumberInput, alpha_b: NumberInput,
                      *, envelope: Envelope | None = CANDIDATE_ENVELOPE,
                      policy: NumericalPolicy = DEFAULT_POLICY) -> ConsumerComparison:
    a, b = _decimal(alpha_a), _decimal(alpha_b)
    for value in (a, b):
        if not 0 < value < 1 or (envelope and not envelope.alpha_min <= value <= envelope.alpha_max):
            raise DomainError("α de consumidor fora do domínio/envelope selecionado")
    sa, sb = (solve_cobb(CobbCase(budget, v), policy=policy) for v in (a, b))
    work = max(sa.precision, sb.precision)
    dx = _decimal_fraction(sb.exact_basket[0] - sa.exact_basket[0], work)
    dy = _decimal_fraction(sb.exact_basket[1] - sa.exact_basket[1], work)
    ra = _fraction(budget.income, policy)
    spending_a = (_decimal_fraction(_fraction(a, policy) * ra, work),
                  _decimal_fraction((1 - _fraction(a, policy)) * ra, work))
    spending_b = (_decimal_fraction(_fraction(b, policy) * ra, work),
                  _decimal_fraction((1 - _fraction(b, policy)) * ra, work))
    return ConsumerComparison(sa, sb, dx, dy, spending_a, spending_b)


def freeze_reference(case: CobbCase, *, policy: NumericalPolicy = DEFAULT_POLICY) -> Reference:
    return Reference(case, solve_cobb(case, policy=policy))


def _significant_agreement(a: Decimal, b: Decimal, digits: int) -> bool:
    if a == 0 or b == 0:
        return a == b
    if (a > 0) != (b > 0):
        return False
    with localcontext() as ctx:
        ctx.prec = digits
        return +a == +b


def _utility_difference(reference: Reference, current: CobbCase, precision: int,
                        policy: NumericalPolicy) -> Decimal:
    a = reference.case.alpha
    r0, px0, py0 = (_fraction(v, policy) for v in
                     (reference.case.budget.income, reference.case.budget.price_x,
                      reference.case.budget.price_y))
    r1, px1, py1 = (_fraction(v, policy) for v in
                     (current.budget.income, current.budget.price_x, current.budget.price_y))
    with localcontext() as ctx:
        ctx.prec = precision
        rx = _decimal_fraction(r1 / r0, precision)
        px = _decimal_fraction(px1 / px0, precision)
        py = _decimal_fraction(py1 / py0, precision)
        return +(rx.ln() - a * px.ln() - (1 - a) * py.ln())


def compare_scenarios(reference: Reference, current: CobbCase,
                      *, policy: NumericalPolicy = DEFAULT_POLICY) -> ScenarioComparison:
    if current.alpha != reference.case.alpha:
        raise DomainError("comparação exige preferências constantes")
    solution = solve_cobb(current, policy=policy)
    old, new = reference.case.budget, current.budget
    income_changed = old.income != new.income
    prices_changed = (old.price_x, old.price_y) != (new.price_x, new.price_y)
    kind = ("conjunto" if income_changed and prices_changed else "renda" if income_changed
            else "precos" if prices_changed else "identico")
    old_x, old_y = reference.solution.exact_basket
    px1, py1, r1 = (_fraction(v, policy) for v in (new.price_x, new.price_y, new.income))
    cost = px1 * old_x + py1 * old_y
    balance = r1 - cost
    affordability = "fronteira" if balance == 0 else "sobra" if balance > 0 else "inacessivel"
    work = _precision((old.income, old.price_x, old.price_y, new.income,
                       new.price_x, new.price_y, current.alpha), policy)
    same_real_budget = (r1 / px1 == _fraction(old.income, policy) / _fraction(old.price_x, policy)
                        and r1 / py1 == _fraction(old.income, policy) / _fraction(old.price_y, policy))
    af = _fraction(current.alpha, policy)
    utility_exactly_equal = False
    if af.denominator <= policy.max_exact_utility_power:
        r0 = _fraction(old.income, policy)
        px0, py0 = _fraction(old.price_x, policy), _fraction(old.price_y, policy)
        utility_exactly_equal = ((r1 / r0) ** af.denominator ==
                                 (px1 / px0) ** af.numerator *
                                 (py1 / py0) ** (af.denominator - af.numerator))
    if same_real_budget or utility_exactly_equal:
        order = "igual"
    else:
        order = "inconclusiva"
        precision = work
        while precision + policy.guard_digits <= policy.max_derived_precision:
            low = _utility_difference(reference, current, precision, policy)
            high = _utility_difference(reference, current, precision + policy.guard_digits, policy)
            if low != 0 and high != 0 and _significant_agreement(low, high, policy.comparison_digits):
                order = "maior" if high > 0 else "menor"
                work = precision + policy.guard_digits
                break
            precision += policy.guard_digits
        if order == "inconclusiva":
            work = min(precision, policy.max_derived_precision)
    return ScenarioComparison(reference, current, solution,
                              _decimal_fraction(cost, min(work, policy.max_derived_precision)),
                              _decimal_fraction(balance, min(work, policy.max_derived_precision)),
                              affordability, kind, order, min(work, policy.max_derived_precision))


def _compensation_at(budget: Budget, alpha: Decimal, utility_target: Decimal,
                     precision: int) -> tuple[Decimal, Basket]:
    with localcontext() as ctx:
        ctx.prec = precision
        beta = 1 - alpha
        e = (utility_target.ln() + alpha * (budget.price_x / alpha).ln()
             + beta * (budget.price_y / beta).ln()).exp()
        return +e, Basket(+(alpha * e / budget.price_x), +(beta * e / budget.price_y))


def compensate(budget: Budget, alpha: NumberInput, utility_target: NumberInput,
               *, policy: NumericalPolicy = DEFAULT_POLICY) -> Compensation:
    a, u = _decimal(alpha), _decimal(utility_target)
    if not 0 < a < 1 or u <= 0:
        raise DomainError("compensação Cobb–Douglas exige 0 < α < 1 e utilidade positiva")
    precision = _precision((budget.income, budget.price_x, budget.price_y, a, u), policy)
    if precision + policy.guard_digits > policy.max_derived_precision:
        return Compensation("inconclusivo", None, None, None, "proteção de precisão derivada")
    while precision + policy.guard_digits <= policy.max_derived_precision:
        low = _compensation_at(budget, a, u, precision)
        high = _compensation_at(budget, a, u, precision + policy.guard_digits)
        if all(_significant_agreement(v, w, policy.comparison_digits)
               for v, w in zip((low[0], low[1].x, low[1].y),
                               (high[0], high[1].x, high[1].y))):
            return Compensation("calculado", high[0], high[1], precision + policy.guard_digits)
        precision += policy.guard_digits
    return Compensation("inconclusivo", None, None, None, "convergência não demonstrada")


def _hicks_at(reference: Reference, current: CobbCase, precision: int,
              policy: NumericalPolicy) -> dict[str, Decimal]:
    a = reference.case.alpha
    old_x, old_y = reference.solution.exact_basket
    new = current.budget
    new_x = _fraction(a, policy) * _fraction(new.income, policy) / _fraction(new.price_x, policy)
    new_y = (1 - _fraction(a, policy)) * _fraction(new.income, policy) / _fraction(new.price_y, policy)
    with localcontext() as ctx:
        ctx.prec = precision
        x0, y0 = _decimal_fraction(old_x, precision), _decimal_fraction(old_y, precision)
        x1, y1 = _decimal_fraction(new_x, precision), _decimal_fraction(new_y, precision)
        u0 = _utility(x0, y0, a, precision)
        e, basket = _compensation_at(new, a, u0, precision)
        return {"e": e, "hx": basket.x, "hy": basket.y,
                "esx": +(basket.x - x0), "esy": +(basket.y - y0),
                "erx": +(x1 - basket.x), "ery": +(y1 - basket.y),
                "etx": +(x1 - x0), "ety": +(y1 - y0),
                "utility_residual": +(_utility(basket.x, basket.y, a, precision) - u0),
                "expenditure_residual": +(new.price_x * basket.x + new.price_y * basket.y - e)}


def hicks_decomposition(reference: Reference, current: CobbCase,
                        *, policy: NumericalPolicy = DEFAULT_POLICY) -> HicksResult:
    if current.alpha != reference.case.alpha:
        return HicksResult("inaplicavel", "preferências diferentes", reference, current)
    if current.budget.income != reference.case.budget.income:
        return HicksResult("inaplicavel", "renda nominal diferente", reference, current)
    old, new = reference.case.budget, current.budget
    if (old.price_x, old.price_y) == (new.price_x, new.price_y):
        return HicksResult("inaplicavel", "preços inalterados", reference, current)
    precision = _precision((old.income, old.price_x, old.price_y,
                            new.price_x, new.price_y, current.alpha), policy)
    px0, py0, px1, py1 = (_fraction(v, policy) for v in
                           (old.price_x, old.price_y, new.price_x, new.price_y))
    structural_sub_zero = px0 * py1 == py0 * px1
    old_x, old_y = reference.solution.exact_basket
    a = _fraction(current.alpha, policy)
    new_x, new_y = a * _fraction(new.income, policy) / px1, (1 - a) * _fraction(new.income, policy) / py1
    if structural_sub_zero:
        # Preços proporcionais preservam exatamente H=A; dispensam subtração numérica.
        work = min(max(precision, policy.initial_precision), policy.max_derived_precision)
        total = Basket(_decimal_fraction(new_x - old_x, work),
                       _decimal_fraction(new_y - old_y, work))
        return HicksResult("calculado", None, reference, current,
                           Basket(_decimal_fraction(old_x, work), _decimal_fraction(old_y, work)),
                           _decimal_fraction((px1 / px0) * _fraction(old.income, policy), work),
                           Basket(Decimal(0), Decimal(0)), total, total,
                           Decimal(0), Decimal(0), work)
    exact_total_zero = {"etx": new_x == old_x, "ety": new_y == old_y}
    structural = exact_total_zero
    while precision + policy.guard_digits <= policy.max_derived_precision:
        low = _hicks_at(reference, current, precision, policy)
        high = _hicks_at(reference, current, precision + policy.guard_digits, policy)
        for key, is_zero in structural.items():
            if is_zero:
                low[key] = high[key] = Decimal(0)
        keys = ("e", "hx", "hy", "esx", "esy", "erx", "ery", "etx", "ety")
        stable = all((structural.get(k, False) or
                      (low[k] != 0 and high[k] != 0 and
                       _significant_agreement(low[k], high[k], policy.comparison_digits)))
                     for k in keys)
        if stable:
            return HicksResult("calculado", None, reference, current,
                               Basket(high["hx"], high["hy"]), high["e"],
                               Basket(high["esx"], high["esy"]),
                               Basket(high["erx"], high["ery"]),
                               Basket(high["etx"], high["ety"]),
                               high["utility_residual"], high["expenditure_residual"],
                               precision + policy.guard_digits)
        precision += policy.guard_digits
    return HicksResult("inconclusivo", "efeitos derivados não estabilizaram na precisão disponível",
                       reference, current, precision=min(precision, policy.max_derived_precision))

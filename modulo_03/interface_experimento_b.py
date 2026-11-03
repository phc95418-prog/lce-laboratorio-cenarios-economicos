"""Interface experimental do B: referência congelada e cenário atual Cobb–Douglas."""

from __future__ import annotations

from decimal import Decimal, localcontext

import streamlit as st

from .experimento_b import (INITIAL, automatic_view, case_from, compare,
                           effect_annotation, fix_reference, hicks, interpretation,
                           plot_data, reference_values)
from .interface_livre import _component, _number
from .livre import focus_view, objects_outside, slider_spec
from .nucleo import (DomainError, HicksResult, NumericalLimit, Reference,
                     ScenarioComparison)


PREFIX = "m03_eb_"
LABELS = {"R": "Renda atual (R$)", "PX": "Preço atual de X (R$ por unidade)",
          "PY": "Preço atual de Y (R$ por unidade)", "A": "Preferência (α)"}


def _key(name: str) -> str:
    return PREFIX + name


def _initial_state() -> None:
    for name, value in INITIAL.items():
        st.session_state.setdefault(_key("value_" + name), value)
        st.session_state.setdefault(_key("field_" + name), value)
    st.session_state.setdefault(_key("reference"), None)
    st.session_state.setdefault(_key("curve_A"), False)
    st.session_state.setdefault(_key("curve_C"), False)
    st.session_state.setdefault(_key("hicks_on"), False)
    st.session_state.setdefault(_key("hicks_effect"), "Substituição")
    st.session_state.setdefault(_key("drag"), "Mover (Pan)")
    st.session_state.setdefault(_key("view"), None)
    st.session_state.setdefault(_key("query"), None)
    st.session_state.setdefault(_key("notice"), None)
    st.session_state.setdefault(_key("slider_epoch"), 0)


def _values() -> dict[str, str]:
    return {name: st.session_state[_key("value_" + name)] for name in INITIAL}


def _set_values(values: dict[str, str]) -> None:
    for name, value in values.items():
        st.session_state[_key("value_" + name)] = value
        st.session_state[_key("field_" + name)] = value


def _reset() -> None:
    _set_values(INITIAL)
    # Widgets da referência anterior podem reenviar a posição antiga após o reset.
    st.session_state[_key("slider_epoch")] += 1
    st.session_state[_key("reference")] = None
    st.session_state[_key("curve_A")] = False
    st.session_state[_key("curve_C")] = False
    _drop_hicks()
    st.session_state[_key("drag")] = "Mover (Pan)"
    st.session_state[_key("view")] = None
    st.session_state[_key("query")] = None
    st.session_state[_key("notice")] = None


def _drop_hicks() -> None:
    st.session_state[_key("hicks_on")] = False
    st.session_state[_key("hicks_effect")] = "Substituição"
    if "H" in (st.session_state.get(_key("query")) or ""):
        st.session_state[_key("query")] = None


def _apply_pending() -> None:
    if st.session_state.pop(_key("reset_pending"), False):
        _reset()
    elif st.session_state.pop(_key("restore_pending"), False):
        reference = st.session_state[_key("reference")]
        if reference is not None:
            _set_values(reference_values(reference))
            _drop_hicks()
            st.session_state[_key("query")] = None
            st.session_state[_key("notice")] = None
    elif st.session_state.pop(_key("replace_pending"), False):
        reference = st.session_state[_key("reference")]
        if reference is not None:
            st.session_state[_key("reference")] = fix_reference(_values())
            _drop_hicks()
            st.session_state[_key("view")] = None
            st.session_state[_key("query")] = None
            st.session_state[_key("notice")] = None


def _validate(values: dict[str, str]) -> None:
    reference = st.session_state[_key("reference")]
    if reference is None:
        case_from(values)
    else:
        compare(reference, values)


def _commit_field(name: str) -> None:
    proposed = _values()
    proposed[name] = st.session_state[_key("field_" + name)]
    try:
        _validate(proposed)
    except (DomainError, NumericalLimit, ValueError, ArithmeticError) as exc:
        st.session_state[_key("field_" + name)] = st.session_state[_key("value_" + name)]
        st.session_state[_key("notice")] = f"{LABELS[name]}: {exc}. Último valor válido preservado."
        return
    exact = str(Decimal(proposed[name]))
    st.session_state[_key("value_" + name)] = exact
    st.session_state[_key("field_" + name)] = exact
    st.session_state[_key("notice")] = None
    st.session_state[_key("query")] = None


def _commit_slider(name: str, slider_key: str) -> None:
    proposed = _values()
    proposed[name] = str(st.session_state[slider_key])
    try:
        _validate(proposed)
    except (DomainError, NumericalLimit, ValueError, ArithmeticError) as exc:
        st.session_state[_key("notice")] = f"{LABELS[name]}: {exc}. Último valor válido preservado."
        return
    st.session_state[_key("value_" + name)] = proposed[name]
    st.session_state[_key("field_" + name)] = proposed[name]
    st.session_state[_key("notice")] = None
    st.session_state[_key("query")] = None


def _control(name: str, *, disabled: bool = False) -> None:
    st.text_input(LABELS[name], key=_key("field_" + name), disabled=disabled,
                  on_change=_commit_field, args=(name,))
    exact = Decimal(st.session_state[_key("value_" + name)])
    if disabled:
        st.caption("Preferência congelada com a referência.")
        return
    spec = slider_spec(name, exact)
    epoch = st.session_state[_key("slider_epoch")]
    slider_key = _key(f"slider_{name}_{spec.minimum}_{spec.maximum}_{epoch}")
    initial_position = spec.position if slider_key not in st.session_state else None
    if initial_position is None and st.session_state[slider_key] != spec.position:
        st.session_state[slider_key] = spec.position
    st.slider(f"Ajuste visual de {LABELS[name]}", min_value=spec.minimum,
              max_value=spec.maximum, value=initial_position, step=spec.step, format="%.9g",
              key=slider_key, on_change=_commit_slider, args=(name, slider_key))
    if spec.expanded or spec.approximate:
        st.caption(f"Valor econômico confirmado: {exact}. O slider é uma aproximação visual.")


def _controls(reference: Reference | None) -> None:
    st.subheader("Condições do cenário atual")
    for name in ("R", "PX", "PY"):
        _control(name)
    _control("A", disabled=reference is not None)
    if reference is None:
        if st.button("Fixar referência", type="primary"):
            st.session_state[_key("reference")] = fix_reference(_values())
            _drop_hicks()
            st.session_state[_key("view")] = None
            st.session_state[_key("query")] = None
            st.rerun()
    else:
        if st.button("Restaurar cenário atual"):
            st.session_state[_key("restore_pending")] = True
            st.rerun()
        with st.popover("Substituir referência"):
            st.write("O cenário atual será a nova referência. A referência anterior e seus resultados derivados serão descartados.")
            if st.button("Confirmar substituição da referência"):
                st.session_state[_key("replace_pending")] = True
                st.rerun()
    with st.popover("Reiniciar experimento"):
        st.write("Apagar a referência e a comparação deste experimento e voltar ao cenário inicial?")
        if st.button("Confirmar reinício do Experimento B"):
            st.session_state[_key("reset_pending")] = True
            st.rerun()


def _difference(current: Decimal, old: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = max(80, len(current.as_tuple().digits) + len(old.as_tuple().digits) + 4)
        return current - old


def _table(comparison: ScenarioComparison) -> None:
    old, new = comparison.reference.case.budget, comparison.current.budget
    a, c = comparison.reference.solution.basket, comparison.current_solution.basket

    def row(label: str, before: Decimal, after: Decimal,
            *, exact: bool = False) -> dict[str, str]:
        return {"Indicador": label, "Referência": _number(before, exact=exact),
                "Atual": _number(after, exact=exact), "Variação atual − referência":
                    _number(_difference(after, before), exact=exact)}

    st.table([
        row("Renda (R$)", old.income, new.income, exact=True),
        row("Preço de X (R$ por unidade)", old.price_x, new.price_x, exact=True),
        row("Preço de Y (R$ por unidade)", old.price_y, new.price_y, exact=True),
        row("Quantidade ótima de X", a.x, c.x),
        row("Quantidade ótima de Y", a.y, c.y),
        row("Despesa total ótima (R$)", old.income, new.income),
    ])


def _query(comparison: ScenarioComparison, target: str | None,
           hicks_result: HicksResult | None = None) -> None:
    if target is None:
        st.caption("Clique em A, C ou H (quando visível) para consultar as cestas calculadas.")
        return
    names = target.split("=")
    for name in names:
        basket = (comparison.reference.solution.basket if name == "A" else
                  comparison.current_solution.basket if name == "C" else
                  hicks_result.compensated if hicks_result is not None else None)
        if basket is not None:
            st.info(f"Consulta · Cesta {name}: X ≈ {_number(basket.x)}, "
                    f"Y ≈ {_number(basket.y)}. O clique não modifica a escolha.")


def _analysis(comparison: ScenarioComparison) -> None:
    old, new = comparison.reference.case.budget, comparison.current.budget
    a = comparison.reference.case.alpha
    st.subheader("Síntese econômica")
    st.write(interpretation(comparison))
    with st.expander("Análise econômica e matemática", expanded=False):
        tabs = st.tabs(("Leitura econômica", "Estrutura matemática",
                        "Propriedades e limites"))
        with tabs[0]:
            st.write("A é a escolha ótima da referência congelada; C é a escolha ótima nas condições atuais. O custo de recompra mostra se A ainda cabe no orçamento atual. A ordenação de utilidade é válida porque as preferências permanecem constantes; diferenças numéricas de utilidade não são valores monetários de bem-estar.")
        with tabs[1]:
            st.latex(r"X_i^*=\frac{\alpha R_i}{P_{X,i}},\qquad Y_i^*=\frac{(1-\alpha)R_i}{P_{Y,i}},\quad i\in\{0,1\}")
            st.latex(r"G_1(A)=P_{X,1}X_0^*+P_{Y,1}Y_0^*,\qquad S_1(A)=R_1-G_1(A)")
            st.write(f"α = {a}; referência: R₀ = {_number(old.income, exact=True)}, P_X₀ = {_number(old.price_x, exact=True)}, P_Y₀ = {_number(old.price_y, exact=True)}; atual: R₁ = {_number(new.income, exact=True)}, P_X₁ = {_number(new.price_x, exact=True)}, P_Y₁ = {_number(new.price_y, exact=True)}.")
            st.write(f"Substituição atual: G₁(A) = {_number(new.price_x, exact=True)} × {_number(comparison.reference.solution.basket.x)} + {_number(new.price_y, exact=True)} × {_number(comparison.reference.solution.basket.y)} ≈ R\\$ {_number(comparison.reference_repurchase_cost)}.")
        with tabs[2]:
            st.write("Cobb–Douglas pressupõe renda e preços positivos, 0 < α < 1 e dois bens divisíveis. Mudanças conjuntas não isolam efeitos causais de cada parâmetro. Preços e renda proporcionais preservam o orçamento real e a cesta ótima, embora os valores nominais mudem.")
            st.write("Entradas e decisões permanecem em Decimal; o gráfico usa coordenadas float aproximadas. Hicks, quando elegível, é um aprofundamento opcional de uma mudança de preços com renda nominal constante.")


def _hicks_candidate(reference: Reference | None, current) -> tuple[HicksResult | None, str | None]:
    """Desativa a camada quando o núcleo não confirma a elegibilidade/cálculo."""
    if reference is None:
        _drop_hicks()
        return None, "Fixe uma referência para investigar Hicks."
    result = hicks(reference, current)
    if result.status == "calculado":
        return result, None
    was_active = st.session_state[_key("hicks_on")]
    _drop_hicks()
    reason = {"renda nominal diferente": "a renda nominal atual difere da referência",
              "preços inalterados": "os preços atuais coincidem com a referência",
              "preferências diferentes": "as preferências não são constantes"}.get(
                  result.reason, result.reason or "cálculo inconclusivo")
    prefix = "Hicks foi desativado: " if was_active else "Hicks indisponível: "
    return None, prefix + reason + "."


def _hicks_indicators(result: HicksResult) -> None:
    h = result.compensated
    st.subheader("Decomposição finita de Hicks")
    st.write("H é a cesta compensada contrafactual aos preços atuais para conservar U₀; "
             "não representa uma transferência monetária efetivamente recebida.")
    st.write(f"H ≈ ({_number(h.x)}; {_number(h.y)}) · despesa mínima compensada "
             f"e ≈ R\\$ {_number(result.expenditure)}.")
    st.table([
        {"Efeito": name, "Bem X": _number(basket.x), "Bem Y": _number(basket.y)}
        for name, basket in (("Substituição (H − A)", result.substitution),
                             ("Renda (C − H)", result.income_effect),
                             ("Total (C − A)", result.total))
    ])
    note = _zero_total_y_explanation(result)
    if note:
        st.info(note)
    with st.expander("Entender a decomposição de Hicks", expanded=False):
        st.write("A → H, H → C e A → C são relações analíticas entre cestas, não "
                 "etapas temporais observadas. A compensação conserva a utilidade "
                 "inicial apenas como construção teórica.")
        st.latex(r"e(p^1,U_0)=\frac{U_0(P_X^1)^\alpha(P_Y^1)^{1-\alpha}}{\alpha^\alpha(1-\alpha)^{1-\alpha}}")
        st.latex(r"H=\left(\frac{\alpha e}{P_X^1},\frac{(1-\alpha)e}{P_Y^1}\right)")
        st.latex(r"ES=H-A,\qquad ER=C-H,\qquad ET=C-A=ES+ER")
        st.write("A decomposição finita de Hicks é distinta da equação diferencial "
                 "de Slutsky. Valores apresentados são aproximados; o cálculo "
                 "interno usa Decimal com precisão adaptativa.")


def _zero_total_y_explanation(result: HicksResult) -> str | None:
    if (result.total.y != 0 or result.substitution.y == 0 or
            result.income_effect.y == 0):
        return None
    substitution_sign = "positiva" if result.substitution.y > 0 else "negativa"
    income_sign = "positiva" if result.income_effect.y > 0 else "negativa"
    return (f"Em Y, o efeito total exatamente nulo reúne substituição {substitution_sign} "
            f"e renda {income_sign} de mesma magnitude neste cenário. "
            "Isso não significa ausência de mecanismos.")


def render() -> None:
    _initial_state()
    _apply_pending()
    reference = st.session_state[_key("reference")]
    st.title("Módulo 03 · Decisões do Consumidor")
    st.caption("Experimento B · Mudanças na escolha ótima · ambiente independente em desenvolvimento")
    st.write("Como renda e preços modificam uma escolha sob preferências constantes?")
    left, right = st.columns([1, 2.1], gap="large")
    with left:
        _controls(reference)
    values = _values()
    current = case_from(values, alpha=reference.case.alpha if reference else None)
    comparison = compare(reference, values) if reference else None
    candidate, hicks_message = _hicks_candidate(reference, current)
    with right:
        if st.session_state[_key("notice")]:
            st.error(st.session_state[_key("notice")])
        if reference is None:
            st.info("Configure renda, preços e α; depois use ‘Fixar referência’ para iniciar a comparação.")
        else:
            a, u0 = reference.solution.basket, reference.solution.utility
            st.caption(f"Referência congelada · R₀ = R\\$ {_number(reference.case.budget.income, exact=True)} · "
                       f"P_X₀ = R\\$ {_number(reference.case.budget.price_x, exact=True)} · "
                       f"P_Y₀ = R\\$ {_number(reference.case.budget.price_y, exact=True)} · α = {_number(reference.case.alpha, exact=True)}")
            st.write(f"A = ({_number(a.x)}; {_number(a.y)}); U₀ ≈ {_number(u0)}.")
        st.selectbox("Arraste no gráfico", ("Mover (Pan)", "Ampliar região"),
                     key=_key("drag"))
        if comparison is not None:
            st.checkbox("Investigar efeitos de Hicks", key=_key("hicks_on"),
                        disabled=candidate is None,
                        help="Disponível com referência fixada, renda nominal constante e preços modificados.")
            if hicks_message:
                st.caption(hicks_message)
            hicks_result = candidate if st.session_state[_key("hicks_on")] else None
            if hicks_result is not None:
                st.selectbox("Destacar efeito", ("Substituição", "Renda", "Total"),
                             key=_key("hicks_effect"))
                st.caption("A curva de indiferença inicial de A e H está visível.")
            ca, cc = st.columns(2)
            if hicks_result is None:
                ca.checkbox("Curva de A", key=_key("curve_A"))
            cc.checkbox("Curva final de C" if hicks_result is not None else "Curva de C",
                        key=_key("curve_C"))
        else:
            hicks_result = None
            st.checkbox("Investigar efeitos de Hicks", key=_key("hicks_on"), disabled=True)
            if hicks_message:
                st.caption(hicks_message)
        auto = automatic_view(current, comparison, hicks_result)
        view = st.session_state[_key("view")] or auto
        traces, warnings, targets = plot_data(current, comparison,
                                              curve_a=st.session_state[_key("curve_A")],
                                              curve_c=st.session_state[_key("curve_C")],
                                              view=view, hicks_result=hicks_result)
        layout = {"height": 500, "margin": {"l": 65, "r": 25, "t": 25,
                                            "b": 55, "autoexpand": False},
                  "dragmode": "pan" if st.session_state[_key("drag")] == "Mover (Pan)" else "zoom",
                  "clickmode": "event", "clickanywhere": True, "hovermode": "closest",
                  "xaxis": {"title": "Quantidade de X", "range": auto["x"]},
                  "yaxis": {"title": "Quantidade de Y", "range": auto["y"]},
                  "legend": {"orientation": "h", "y": -0.23}}
        if hicks_result is not None:
            annotation, warning = effect_annotation(
                comparison, hicks_result, st.session_state[_key("hicks_effect")])
            if annotation is not None:
                layout["annotations"] = [annotation]
            if warning:
                warnings.append(warning)
        graph = _component()(key=_key("graph"),
                             data={"traces": traces, "layout": layout,
                                   "view": st.session_state[_key("view")],
                                   "clickTargets": targets},
                             height=530, on_clicked_change=lambda: None,
                             on_view_event_change=lambda: None)
        if graph.view_event and graph.view_event.get("id") != st.session_state.get(_key("last_view_id")):
            st.session_state[_key("last_view_id")] = graph.view_event["id"]
            st.session_state[_key("view")] = graph.view_event["view"]
        if graph.clicked and graph.clicked.get("id") != st.session_state.get(_key("last_click_id")):
            st.session_state[_key("last_click_id")] = graph.clicked["id"]
            st.session_state[_key("query")] = graph.clicked["target"]
            st.rerun()
        if comparison is not None:
            if hicks_result is not None:
                c1, c2 = st.columns(2)
                c3, c4 = st.columns(2)
            else:
                c1, c2, c3 = st.columns(3)
                c4 = None
            if c1.button("Enquadrar todos"):
                st.session_state[_key("view")] = None
                st.rerun()
            if c2.button("Focar A"):
                st.session_state[_key("view")] = focus_view(comparison.reference.solution.basket)
                st.rerun()
            if c3.button("Focar C"):
                st.session_state[_key("view")] = focus_view(comparison.current_solution.basket)
                st.rerun()
            if c4 is not None and c4.button("Focar H"):
                st.session_state[_key("view")] = focus_view(hicks_result.compensated)
                st.rerun()
            baskets = [comparison.reference.solution.basket,
                       comparison.current_solution.basket]
            if hicks_result is not None:
                baskets.append(hicks_result.compensated)
            if any(objects_outside(view, basket, None) for basket in baskets):
                st.caption("Há cestas fora da vista. Use ‘Enquadrar todos’ para localizá-las.")
        else:
            if st.button("Enquadrar todos"):
                st.session_state[_key("view")] = None
                st.rerun()
        for warning in warnings:
            st.warning(warning)
        if comparison is not None:
            _query(comparison, st.session_state[_key("query")], hicks_result)
            st.subheader("Indicadores comparativos")
            _table(comparison)
            status = {"sobra": "acessível, com sobra", "fronteira": "acessível, na fronteira",
                      "inacessivel": "inacessível"}[comparison.reference_affordability]
            st.write(f"Recompra de A aos preços atuais: R\\$ {_number(comparison.reference_repurchase_cost)} · "
                     f"saldo: R\\$ {_number(comparison.reference_repurchase_balance)} · "
                     f"cesta A {status}.")
            if comparison.utility_order == "inconclusiva":
                st.warning("A precisão disponível não permite ordenar U(A) e U(C) com segurança.")
            if hicks_result is not None:
                _hicks_indicators(hicks_result)
            _analysis(comparison)
        with st.expander("Sobre o modelo", expanded=False):
            st.write("Comparação teórica de escolhas ótimas Cobb–Douglas sob preferências constantes. A referência permanece congelada até sua substituição explícita; este modelo não prevê escolhas empíricas.")

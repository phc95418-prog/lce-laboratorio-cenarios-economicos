"""Interface independente da Exploração livre do Módulo 03 (Fase 2)."""

from __future__ import annotations

from decimal import Decimal, localcontext
from pathlib import Path

import streamlit as st

from .livre import (INITIAL, automatic_view, focus_view, objects_outside,
                    plot_data, slider_spec)
from .nucleo import DomainError, assess_basket, make_basket, make_cobb_case, solve_cobb


PREFIX = "m03_livre_"
LABELS = {"R": "Renda (R$)", "PX": "Preço de X (R$ por unidade)",
          "PY": "Preço de Y (R$ por unidade)", "A": "Preferência (α)"}
CORE_KEYS = ("R", "PX", "PY", "A")


def _key(name: str) -> str:
    return PREFIX + name


def _initial_state() -> None:
    for name, value in INITIAL.items():
        st.session_state.setdefault(_key("value_" + name), value)
        st.session_state.setdefault(_key("field_" + name), value)
    st.session_state.setdefault(_key("manual"), None)
    for name in ("field_X", "field_Y"):
        st.session_state.setdefault(_key(name), "")
    for name in ("manual_curve", "optimum", "optimum_curve"):
        st.session_state.setdefault(_key(name), False)
    st.session_state.setdefault(_key("drag"), "Mover (Pan)")
    st.session_state.setdefault(_key("view"), None)
    st.session_state.setdefault(_key("notice"), None)


def _reset() -> None:
    for name, value in INITIAL.items():
        st.session_state[_key("value_" + name)] = value
        st.session_state[_key("field_" + name)] = value
    st.session_state[_key("manual")] = None
    st.session_state[_key("field_X")] = ""
    st.session_state[_key("field_Y")] = ""
    for name in ("manual_curve", "optimum", "optimum_curve"):
        st.session_state[_key(name)] = False
    st.session_state[_key("drag")] = "Mover (Pan)"
    st.session_state[_key("view")] = None
    st.session_state[_key("notice")] = None


def _values() -> dict[str, str]:
    return {name: st.session_state[_key("value_" + name)] for name in CORE_KEYS}


def _case(values: dict[str, str] | None = None):
    values = values or _values()
    return make_cobb_case(values["R"], values["PX"], values["PY"], values["A"])


def _notice(kind: str, message: str) -> None:
    st.session_state[_key("notice")] = (kind, message)


def _commit_field(name: str) -> None:
    raw = st.session_state[_key("field_" + name)]
    proposed = _values()
    proposed[name] = raw
    try:
        case = _case(proposed)
    except (DomainError, ValueError, ArithmeticError) as exc:
        st.session_state[_key("field_" + name)] = st.session_state[_key("value_" + name)]
        _notice("error", f"{LABELS[name]}: {exc}. Último valor válido preservado.")
        return
    exact = case.alpha if name == "A" else getattr(case.budget, {"R": "income", "PX": "price_x", "PY": "price_y"}[name])
    st.session_state[_key("value_" + name)] = str(exact)
    st.session_state[_key("field_" + name)] = str(exact)
    st.session_state[_key("notice")] = None


def _commit_slider(name: str, slider_key: str) -> None:
    proposed = _values()
    proposed[name] = str(st.session_state[slider_key])
    try:
        case = _case(proposed)
    except (DomainError, ValueError, ArithmeticError) as exc:
        _notice("error", f"{LABELS[name]}: {exc}. Último valor válido preservado.")
        return
    exact = case.alpha if name == "A" else getattr(case.budget, {"R": "income", "PX": "price_x", "PY": "price_y"}[name])
    st.session_state[_key("value_" + name)] = str(exact)
    st.session_state[_key("field_" + name)] = str(exact)
    st.session_state[_key("notice")] = None


def _commit_basket() -> None:
    x = st.session_state[_key("field_X")].strip()
    y = st.session_state[_key("field_Y")].strip()
    if not x or not y:
        previous = st.session_state[_key("manual")]
        if previous:
            st.session_state[_key("field_X")] = str(previous.x)
            st.session_state[_key("field_Y")] = str(previous.y)
            _notice("info", "Edição incompleta; última cesta confirmada preservada.")
        return  # sem cesta inicial, aguarda os dois campos
    try:
        basket = make_basket(x, y)
    except (DomainError, ValueError, ArithmeticError) as exc:
        previous = st.session_state[_key("manual")]
        st.session_state[_key("field_X")] = str(previous.x) if previous else ""
        st.session_state[_key("field_Y")] = str(previous.y) if previous else ""
        _notice("error", f"Cesta rejeitada: {exc}. Última cesta válida preservada.")
        return
    st.session_state[_key("manual")] = basket
    st.session_state[_key("field_X")] = str(basket.x)
    st.session_state[_key("field_Y")] = str(basket.y)
    st.session_state[_key("notice")] = None


def _clear_basket() -> None:
    st.session_state[_key("manual")] = None
    st.session_state[_key("field_X")] = ""
    st.session_state[_key("field_Y")] = ""
    st.session_state[_key("notice")] = None


def _set_basket_from_click(payload: dict) -> None:
    try:
        basket = make_basket(payload["x"], payload["y"])
    except (KeyError, DomainError, ValueError, ArithmeticError) as exc:
        _notice("error", f"Clique rejeitado: {exc}. Última cesta válida preservada.")
        return
    st.session_state[_key("manual")] = basket
    st.session_state[_key("field_X")] = str(basket.x)
    st.session_state[_key("field_Y")] = str(basket.y)
    st.session_state[_key("notice")] = None


@st.cache_resource
def _component():
    js = Path(__file__).with_name("grafico_livre.js").read_text(encoding="utf-8")
    return st.components.v2.component(
        "lce_modulo03_livre", html='<div class="m03-plot" style="width:100%;height:510px"></div>',
        js=js, isolate_styles=False)


def _number(value: Decimal | None, *, exact: bool = False) -> str:
    if value is None:
        return "inconclusivo"
    return str(value) if exact else format(value, ".9g")


def _controls() -> None:
    st.subheader("Condições econômicas")
    for name in CORE_KEYS:
        st.text_input(LABELS[name], key=_key("field_" + name),
                      on_change=_commit_field, args=(name,))
        exact = Decimal(st.session_state[_key("value_" + name)])
        spec = slider_spec(name, exact)
        slider_key = _key(f"slider_{name}_{spec.minimum}_{spec.maximum}")
        if slider_key not in st.session_state or st.session_state[slider_key] != spec.position:
            st.session_state[slider_key] = spec.position
        st.slider(f"Ajuste visual de {LABELS[name]}", min_value=spec.minimum,
                  max_value=spec.maximum, step=spec.step, format="%.9g",
                  key=slider_key, on_change=_commit_slider, args=(name, slider_key))
        if spec.expanded or spec.approximate:
            st.caption(f"Valor econômico confirmado: {exact}. O slider é uma aproximação visual.")
    st.subheader("Cesta manual")
    st.caption("Informe X e Y ou clique no gráfico. A cesta pode ficar fora do orçamento.")
    col_x, col_y = st.columns(2)
    with col_x:
        st.text_input("Quantidade de X", key=_key("field_X"),
                      on_change=_commit_basket)
    with col_y:
        st.text_input("Quantidade de Y", key=_key("field_Y"),
                      on_change=_commit_basket)
    manual = st.session_state[_key("manual")]
    if manual is not None and max(len(str(manual.x)), len(str(manual.y))) > 12:
        st.caption(f"Coordenadas confirmadas: X = {manual.x}; Y = {manual.y}.")
    st.button("Limpar cesta manual", on_click=_clear_basket,
              disabled=st.session_state[_key("manual")] is None)
    with st.popover("Restaurar exploração"):
        st.write("Restaurar os valores, a cesta e a visualização iniciais?")
        if st.button("Confirmar restauração"):
            st.session_state[_key("reset_pending")] = True
            st.rerun()


def _analysis(case, solution, manual, assessment) -> None:
    b = case.budget
    st.subheader("Síntese econômica")
    if manual is None:
        st.write("A restrição orçamentária mostra as combinações possíveis. Selecione uma cesta para observar seu custo e sua utilidade.")
    elif assessment.budget_status == "inconclusivo":
        st.info("A avaliação desta cesta excedeu uma proteção numérica experimental; a classificação permanece inconclusiva.")
    elif assessment.budget_status == "inacessivel":
        st.write("A cesta selecionada excede a renda disponível e permanece visível para comparação com o orçamento.")
    elif assessment.budget_status == "fronteira":
        st.write("A cesta utiliza integralmente a renda disponível.")
    else:
        st.write("A cesta é acessível e deixa parte da renda sem gastar.")
    with st.expander("Entender este cenário", expanded=False):
        tabs = st.tabs(("Leitura econômica", "Estrutura matemática",
                        "Desenvolvimento matemático", "Propriedades e limites"))
        with tabs[0]:
            if manual is None:
                st.write("Os interceptos mostram o máximo de cada bem quando toda a renda é dedicada a ele. A cesta ótima permanece oculta até ser solicitada.")
            else:
                st.write(rf"A cesta ({_number(manual.x, exact=True)}; {_number(manual.y, exact=True)}) tem custo de R\$ {_number(assessment.cost)} e saldo de R\$ {_number(assessment.balance)}. Sua condição orçamentária é {assessment.budget_status}.")
                if assessment.utility is not None:
                    st.write(f"Sua utilidade modelada é {_number(assessment.utility)}; esse número não é uma medida monetária de bem-estar.")
        with tabs[1]:
            with localcontext() as ctx:
                ctx.prec = max(80, len(case.alpha.as_tuple().digits) + 4)
                beta = Decimal(1) - case.alpha
            st.latex(r"P_X X + P_Y Y \leq R")
            st.latex(rf"{b.price_x}X + {b.price_y}Y \leq {b.income}")
            st.latex(r"U(X,Y)=X^{\alpha}Y^{1-\alpha}")
            st.latex(rf"U(X,Y)=X^{{{case.alpha}}}Y^{{{beta}}}")
        with tabs[2]:
            st.latex(r"X^*=\frac{\alpha R}{P_X},\qquad Y^*=\frac{(1-\alpha)R}{P_Y}")
            st.latex(rf"X^*=\frac{{{case.alpha}\cdot {b.income}}}{{{b.price_x}}},\qquad Y^*=\frac{{(1-{case.alpha})\cdot {b.income}}}{{{b.price_y}}}")
            if solution.basket:
                st.write(f"Resultado calculado: X* ≈ {_number(solution.basket.x)}, Y* ≈ {_number(solution.basket.y)}.")
        with tabs[3]:
            st.write("Renda e preços são positivos; 0 < α < 1. Para Cobb–Douglas, a solução ótima é interior e esgota o orçamento. A tangência e as participações constantes não são propriedades universais de toda preferência.")
            st.write("As coordenadas gráficas são aproximações em ponto flutuante. Valores econômicos e decisões de domínio usam Decimal no núcleo; resultados inconclusivos não são classificados por tolerância visual.")
    with st.expander("Sobre o modelo", expanded=False):
        st.write("Cobb–Douglas representa preferências teóricas entre dois bens não negativos, com renda e preços dados. O laboratório não é uma previsão empírica do comportamento de consumidores.")


def render() -> None:
    _initial_state()
    if st.session_state.pop(_key("reset_pending"), False):
        _reset()
    click = st.session_state.pop(_key("pending_click"), None)
    if click:
        st.session_state[_key("last_click_id")] = click["id"]
        _set_basket_from_click(click)
    st.title("Módulo 03 · Decisões do Consumidor")
    st.caption("Exploração livre · interface independente em desenvolvimento")
    st.write("Como renda, preços e preferências delimitam as cestas possíveis?")
    left, right = st.columns([1, 2.1], gap="large")
    with left:
        _controls()
    case = _case()
    solution = solve_cobb(case)
    manual = st.session_state[_key("manual")]
    assessment = assess_basket(solution, manual) if manual else None
    with right:
        notice = st.session_state[_key("notice")]
        if notice:
            getattr(st, notice[0])(notice[1])
        b = case.budget
        st.caption(rf"Orçamento: R\$ {_number(b.income, exact=True)} · X a R\$ {_number(b.price_x, exact=True)} · Y a R\$ {_number(b.price_y, exact=True)}")
        st.selectbox("Arraste no gráfico", ("Mover (Pan)", "Ampliar região"), key=_key("drag"))
        v1, v2, v3 = st.columns(3)
        with v1:
            st.checkbox("Curva da cesta manual", key=_key("manual_curve"))
        with v2:
            st.checkbox("Mostrar solução ótima", key=_key("optimum"))
        with v3:
            st.checkbox("Curva da solução ótima", key=_key("optimum_curve"))
        auto = automatic_view(case, solution, manual, show_optimum=st.session_state[_key("optimum")])
        view = st.session_state[_key("view")] or auto
        traces, warnings = plot_data(case, solution, manual,
                                     manual_curve=st.session_state[_key("manual_curve")],
                                     optimum=st.session_state[_key("optimum")],
                                     optimum_curve=st.session_state[_key("optimum_curve")], view=view)
        layout = {"height": 500, "margin": {"l": 65, "r": 25, "t": 25, "b": 55, "autoexpand": False},
                  "dragmode": "pan" if st.session_state[_key("drag")] == "Mover (Pan)" else "zoom",
                  "clickmode": "event", "clickanywhere": True, "hovermode": "closest",
                  "xaxis": {"title": "Quantidade de X", "range": auto["x"]},
                  "yaxis": {"title": "Quantidade de Y", "range": auto["y"]},
                  "legend": {"orientation": "h", "y": -0.23}}
        graph = _component()(key=_key("graph"), data={"traces": traces, "layout": layout,
                             "view": st.session_state[_key("view")]}, height=530,
                             on_clicked_change=lambda: None, on_view_event_change=lambda: None)
        if graph.view_event and graph.view_event.get("id") != st.session_state.get(_key("last_view_id")):
            st.session_state[_key("last_view_id")] = graph.view_event["id"]
            st.session_state[_key("view")] = graph.view_event["view"]
        if graph.clicked and graph.clicked.get("id") != st.session_state.get(_key("last_click_id")):
            st.session_state[_key("pending_click")] = graph.clicked
            st.rerun()
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Enquadrar todos"):
                st.session_state[_key("view")] = None
                st.rerun()
        with c2:
            if st.button("Focar cesta", disabled=manual is None):
                st.session_state[_key("view")] = focus_view(manual)
                st.rerun()
        with c3:
            if st.button("Focar ótimo", disabled=not st.session_state[_key("optimum")]):
                st.session_state[_key("view")] = focus_view(solution.basket)
                st.rerun()
        if objects_outside(view, manual, solution.basket if st.session_state[_key("optimum")] else None):
            st.caption("Há objetos fora do enquadramento. Use ‘Enquadrar todos’ ou um foco local.")
        for warning in warnings:
            st.warning(warning)
        if assessment:
            st.subheader("Cesta selecionada")
            top = st.columns(2)
            top[0].metric("Custo (R$)", _number(assessment.cost))
            top[1].metric("Saldo (R$)", _number(assessment.balance))
            bottom = st.columns(2)
            bottom[0].metric("Utilidade", _number(assessment.utility))
            bottom[1].metric("Orçamento", {"sobra": "Sobra", "fronteira": "Fronteira",
                                                "inacessivel": "Inacessível", "inconclusivo": "Inconclusivo"}[assessment.budget_status])
        if st.session_state[_key("optimum")] and solution.basket:
            st.caption(f"Solução ótima: X ≈ {_number(solution.basket.x)}, Y ≈ {_number(solution.basket.y)}; utilidade ≈ {_number(solution.utility)}.")
        _analysis(case, solution, manual, assessment)

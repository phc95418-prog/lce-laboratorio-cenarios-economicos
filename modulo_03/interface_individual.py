"""Interface isolada do Experimento A — Escolha individual (Módulo 03)."""

from __future__ import annotations

from decimal import Decimal

import streamlit as st

from .individual import (INITIAL, MODELS, automatic_view, calculate, diagnosis,
                         explanation, hint, plot_data)
from .livre import focus_view, objects_outside, slider_spec
from .nucleo import DomainError, make_basket, make_budget, make_cobb_case
from .interface_livre import _component, _number


PREFIX = "m03_ai_"
LABELS = {"R": "Renda (R$)", "PX": "Preço de X (R$ por unidade)",
          "PY": "Preço de Y (R$ por unidade)", "A": "Preferência (α)"}


def _key(name: str) -> str:
    return PREFIX + name


def _initial_state() -> None:
    for name, value in INITIAL.items():
        st.session_state.setdefault(_key("value_" + name), value)
        st.session_state.setdefault(_key("field_" + name), value)
    st.session_state.setdefault(_key("model"), "Cobb–Douglas")
    st.session_state.setdefault(_key("manual"), None)
    for name in ("field_X", "field_Y"):
        st.session_state.setdefault(_key(name), "")
    for name in ("evaluate", "optimum", "manual_curve", "optimum_curve", "show_hint"):
        st.session_state.setdefault(_key(name), False)
    st.session_state.setdefault(_key("drag"), "Mover (Pan)")
    st.session_state.setdefault(_key("view"), None)
    st.session_state.setdefault(_key("notice"), None)


def _reset() -> None:
    for name, value in INITIAL.items():
        st.session_state[_key("value_" + name)] = value
        st.session_state[_key("field_" + name)] = value
    st.session_state[_key("model")] = "Cobb–Douglas"
    st.session_state[_key("manual")] = None
    for name in ("field_X", "field_Y"):
        st.session_state[_key(name)] = ""
    for name in ("evaluate", "optimum", "manual_curve", "optimum_curve", "show_hint"):
        st.session_state[_key(name)] = False
    st.session_state[_key("drag")] = "Mover (Pan)"
    st.session_state[_key("view")] = None
    st.session_state[_key("notice")] = None


def _values() -> dict[str, str]:
    return {name: st.session_state[_key("value_" + name)] for name in INITIAL}


def _valid_values(values: dict[str, str]) -> None:
    make_budget(values["R"], values["PX"], values["PY"])
    # O α continua guardado mesmo enquanto um modelo de contraste está ativo.
    make_cobb_case(values["R"], values["PX"], values["PY"], values["A"])


def _notice(kind: str, message: str) -> None:
    st.session_state[_key("notice")] = (kind, message)


def _commit_field(name: str) -> None:
    proposed = _values()
    proposed[name] = st.session_state[_key("field_" + name)]
    try:
        _valid_values(proposed)
    except (DomainError, ValueError, ArithmeticError) as exc:
        st.session_state[_key("field_" + name)] = st.session_state[_key("value_" + name)]
        _notice("error", f"{LABELS[name]}: {exc}. Último valor válido preservado.")
        return
    exact = Decimal(proposed[name])
    st.session_state[_key("value_" + name)] = str(exact)
    st.session_state[_key("field_" + name)] = str(exact)
    st.session_state[_key("show_hint")] = False
    st.session_state[_key("notice")] = None


def _commit_slider(name: str, slider_key: str) -> None:
    proposed = _values()
    proposed[name] = str(st.session_state[slider_key])
    try:
        _valid_values(proposed)
    except (DomainError, ValueError, ArithmeticError) as exc:
        _notice("error", f"{LABELS[name]}: {exc}. Último valor válido preservado.")
        return
    st.session_state[_key("value_" + name)] = proposed[name]
    st.session_state[_key("field_" + name)] = proposed[name]
    st.session_state[_key("show_hint")] = False
    st.session_state[_key("notice")] = None


def _commit_basket() -> None:
    x = st.session_state[_key("field_X")].strip()
    y = st.session_state[_key("field_Y")].strip()
    previous = st.session_state[_key("manual")]
    if not x or not y:
        if previous:
            st.session_state[_key("field_X")] = str(previous.x)
            st.session_state[_key("field_Y")] = str(previous.y)
            _notice("info", "Edição incompleta; última cesta confirmada preservada.")
        return
    try:
        basket = make_basket(x, y)
    except (DomainError, ValueError, ArithmeticError) as exc:
        st.session_state[_key("field_X")] = str(previous.x) if previous else ""
        st.session_state[_key("field_Y")] = str(previous.y) if previous else ""
        _notice("error", f"Cesta rejeitada: {exc}. Última cesta válida preservada.")
        return
    st.session_state[_key("manual")] = basket
    st.session_state[_key("field_X")] = str(basket.x)
    st.session_state[_key("field_Y")] = str(basket.y)
    st.session_state[_key("show_hint")] = False
    st.session_state[_key("notice")] = None


def _click_basket(payload: dict) -> None:
    try:
        basket = make_basket(payload["x"], payload["y"])
    except (KeyError, DomainError, ValueError, ArithmeticError) as exc:
        _notice("error", f"Clique rejeitado: {exc}. Última cesta válida preservada.")
        return
    st.session_state[_key("manual")] = basket
    st.session_state[_key("field_X")] = str(basket.x)
    st.session_state[_key("field_Y")] = str(basket.y)
    st.session_state[_key("show_hint")] = False
    st.session_state[_key("notice")] = None


def _clear_basket() -> None:
    st.session_state[_key("manual")] = None
    st.session_state[_key("field_X")] = ""
    st.session_state[_key("field_Y")] = ""
    st.session_state[_key("evaluate")] = False
    st.session_state[_key("show_hint")] = False
    st.session_state[_key("notice")] = None


def _change_model() -> None:
    if MODELS[st.session_state[_key("model")]] == "cobb_douglas":
        st.session_state[_key("field_A")] = st.session_state[_key("value_A")]
    st.session_state[_key("show_hint")] = False
    st.session_state[_key("notice")] = None


def _controls() -> None:
    st.subheader("Condições econômicas")
    st.selectbox("Modelo de preferências", tuple(MODELS), key=_key("model"),
                 on_change=_change_model)
    names = ("R", "PX", "PY", "A") if MODELS[st.session_state[_key("model")]] == "cobb_douglas" else ("R", "PX", "PY")
    for name in names:
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
    st.subheader("Minha cesta")
    st.caption("Informe X e Y ou clique no gráfico; cestas fora do orçamento são mantidas.")
    col_x, col_y = st.columns(2)
    with col_x:
        st.text_input("Quantidade de X", key=_key("field_X"), on_change=_commit_basket)
    with col_y:
        st.text_input("Quantidade de Y", key=_key("field_Y"), on_change=_commit_basket)
    manual = st.session_state[_key("manual")]
    if manual is not None and max(len(str(manual.x)), len(str(manual.y))) > 12:
        st.caption(f"Coordenadas confirmadas: X = {manual.x}; Y = {manual.y}.")
    st.button("Limpar cesta manual", on_click=_clear_basket,
              disabled=st.session_state[_key("manual")] is None)
    with st.popover("Reiniciar escolha individual"):
        st.write("Apagar a investigação individual e restaurar o estado inicial?")
        if st.button("Confirmar reinício individual"):
            st.session_state[_key("reset_pending")] = True
            st.rerun()


def _analysis(result, manual, evaluate: bool) -> None:
    solution, assessment = result.solution, result.assessment
    st.subheader("Síntese econômica")
    if manual is None:
        st.write("Construa uma cesta para observar custo e utilidade. Avaliação e ótimo permanecem ocultos até sua escolha.")
    elif not evaluate:
        st.write("A cesta foi registrada. O custo e a acessibilidade aparecem acima; use ‘Avaliar minha escolha’ para obter o diagnóstico.")
    else:
        message = diagnosis(assessment)
        if assessment.budget_status == "inconclusivo":
            st.info(message)
        else:
            st.write(message)
    with st.expander("Entender o resultado", expanded=False):
        tabs = st.tabs(("Leitura econômica", "Estrutura matemática",
                        "Desenvolvimento matemático", "Propriedades e limites"))
        b = solution.budget
        with tabs[0]:
            if not evaluate:
                st.write("A avaliação é opcional e independente da exibição do ótimo. A seleção manual não é ajustada.")
            else:
                st.write(explanation(solution, assessment))
        with tabs[1]:
            st.latex(r"P_X X+P_Y Y\leq R")
            st.latex(rf"{b.price_x}X+{b.price_y}Y\leq {b.income}")
            if solution.model == "cobb_douglas":
                st.latex(r"U(X,Y)=X^{\alpha}Y^{1-\alpha}")
                st.write(f"Parâmetro atual: α = {solution.alpha}.")
            elif solution.model == "substitutes":
                st.latex(r"U(X,Y)=X+Y")
            else:
                st.latex(r"U(X,Y)=\min(X,Y)")
            if assessment:
                st.write(f"Custo da cesta: R$ {_number(assessment.cost)}; saldo: R$ {_number(assessment.balance)}.")
        with tabs[2]:
            if solution.model == "cobb_douglas":
                st.latex(r"X^*=\frac{\alpha R}{P_X},\qquad Y^*=\frac{(1-\alpha)R}{P_Y}")
                st.write("A solução interior exige também o esgotamento do orçamento.")
            elif solution.model == "substitutes":
                st.write("Preços diferentes produzem escolha de canto no bem mais barato. Preços exatamente iguais tornam ótima toda a fronteira.")
            else:
                st.latex(r"X^*=Y^*=\frac{R}{P_X+P_Y}")
                st.write("A solução está na quina da curva de indiferença.")
        with tabs[3]:
            st.write("A utilidade é ordinal, não monetária. O diagnóstico exige viabilidade antes de otimalidade. Não existe categoria formal de ‘quase ótima’.")
            st.write("Cestas, preços e renda são avaliados pelo núcleo em Decimal; o gráfico utiliza aproximações float apenas para desenhar.")
    with st.expander("Sobre o modelo", expanded=False):
        st.write("Modelos teóricos de dois bens divisíveis, com renda e preços positivos. Cobb–Douglas exige 0 < α < 1; substitutos e complementares têm cantos ou quinas que não seguem a condição interior de tangência.")


def render() -> None:
    _initial_state()
    if st.session_state.pop(_key("reset_pending"), False):
        _reset()
    click = st.session_state.pop(_key("pending_click"), None)
    if click:
        st.session_state[_key("last_click_id")] = click["id"]
        _click_basket(click)
    st.title("Módulo 03 · Decisões do Consumidor")
    st.caption("Experimento A · Escolha individual · Módulo 03 — Decisões do Consumidor")
    st.write("Como a cesta escolhida se relaciona com o orçamento e as preferências?")
    left, right = st.columns([1, 2.1], gap="large")
    with left:
        _controls()
    model = MODELS[st.session_state[_key("model")]]
    result = calculate(model, _values(), st.session_state[_key("manual")])
    solution, assessment = result.solution, result.assessment
    manual = st.session_state[_key("manual")]
    with right:
        notice = st.session_state[_key("notice")]
        if notice:
            getattr(st, notice[0])(notice[1])
        b = solution.budget
        st.caption(rf"Orçamento: R\$ {_number(b.income, exact=True)} · X a R\$ {_number(b.price_x, exact=True)} · Y a R\$ {_number(b.price_y, exact=True)}")
        st.selectbox("Arraste no gráfico", ("Mover (Pan)", "Ampliar região"), key=_key("drag"))
        v1, v2, v3 = st.columns(3)
        with v1:
            st.checkbox("Curva da cesta manual", key=_key("manual_curve"))
        with v2:
            st.checkbox("Mostrar solução ótima", key=_key("optimum"))
        with v3:
            st.checkbox("Curva da solução ótima", key=_key("optimum_curve"))
        auto = automatic_view(solution, manual,
                              show_optimum=st.session_state[_key("optimum")],
                              show_optimum_curve=st.session_state[_key("optimum_curve")])
        view = st.session_state[_key("view")] or auto
        traces, warnings = plot_data(solution, manual,
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
            if st.button("Focar ótimo", disabled=not st.session_state[_key("optimum")] or solution.basket is None):
                st.session_state[_key("view")] = focus_view(solution.basket)
                st.rerun()
        if objects_outside(view, manual, solution.basket if st.session_state[_key("optimum")] else None):
            st.caption("Há objetos fora do enquadramento. Use ‘Enquadrar todos’ para localizá-los.")
        for warning in warnings:
            st.warning(warning)
        if assessment:
            st.subheader("Cesta selecionada")
            top = st.columns(2)
            top[0].metric("Custo (R$)", _number(assessment.cost))
            top[1].metric("Saldo (R$)", _number(assessment.balance))
            bottom = st.columns(2)
            bottom[0].metric("Utilidade modelada", _number(assessment.utility))
            bottom[1].metric("Orçamento", {"sobra": "Sobra", "fronteira": "Fronteira",
                                               "inacessivel": "Inacessível", "inconclusivo": "Inconclusivo"}[assessment.budget_status])
        st.toggle("Avaliar minha escolha", key=_key("evaluate"), disabled=manual is None)
        if st.session_state[_key("evaluate")] and assessment:
            st.button("Receber uma pista", key=_key("hint_button"),
                      disabled=hint(solution, assessment) is None,
                      on_click=lambda: st.session_state.__setitem__(_key("show_hint"), True))
            if st.session_state[_key("show_hint")]:
                clue = hint(solution, assessment)
                if clue:
                    st.info(clue)
        if st.session_state[_key("optimum")]:
            if solution.kind == "segment":
                st.caption("Solução ótima: todo o segmento da fronteira orçamentária; nenhum ponto é privilegiado.")
            elif solution.basket:
                st.caption(f"Solução ótima: X ≈ {_number(solution.basket.x)}, Y ≈ {_number(solution.basket.y)}.")
        _analysis(result, manual, st.session_state[_key("evaluate")])

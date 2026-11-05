"""Interface isolada do Experimento A — Comparação entre consumidores."""

from __future__ import annotations

from decimal import Decimal

import streamlit as st

from .comparacao_consumidores import (INITIAL, automatic_view, calculate,
                                      interpretation, plot_data, shares,
                                      share_differences)
from .interface_livre import _component, _number
from .livre import focus_view, objects_outside, slider_spec
from .nucleo import DomainError, make_budget


PREFIX = "m03_ac_"
LABELS = {"R": "Renda comum (R$)", "PX": "Preço comum de X (R$ por unidade)",
          "PY": "Preço comum de Y (R$ por unidade)",
          "AA": "Preferência do consumidor A (α_A)",
          "AB": "Preferência do consumidor B (α_B)"}


def _key(name: str) -> str:
    return PREFIX + name


def _initial_state() -> None:
    for name, value in INITIAL.items():
        st.session_state.setdefault(_key("value_" + name), value)
        st.session_state.setdefault(_key("field_" + name), value)
    for name in ("curve_A", "curve_B"):
        st.session_state.setdefault(_key(name), False)
    st.session_state.setdefault(_key("drag"), "Mover (Pan)")
    st.session_state.setdefault(_key("view"), None)
    st.session_state.setdefault(_key("query"), None)
    st.session_state.setdefault(_key("notice"), None)


def _reset() -> None:
    for name, value in INITIAL.items():
        st.session_state[_key("value_" + name)] = value
        st.session_state[_key("field_" + name)] = value
    for name in ("curve_A", "curve_B"):
        st.session_state[_key(name)] = False
    st.session_state[_key("drag")] = "Mover (Pan)"
    st.session_state[_key("view")] = None
    st.session_state[_key("query")] = None
    st.session_state[_key("notice")] = None


def _values() -> dict[str, str]:
    return {name: st.session_state[_key("value_" + name)] for name in INITIAL}


def _validate(values: dict[str, str]) -> None:
    budget = make_budget(values["R"], values["PX"], values["PY"])
    # Usa a validação de domínio e precisão do núcleo para os dois perfis.
    from .nucleo import compare_consumers
    compare_consumers(budget, values["AA"], values["AB"])


def _commit_field(name: str) -> None:
    proposed = _values()
    proposed[name] = st.session_state[_key("field_" + name)]
    try:
        _validate(proposed)
    except (DomainError, ValueError, ArithmeticError) as exc:
        st.session_state[_key("field_" + name)] = st.session_state[_key("value_" + name)]
        st.session_state[_key("notice")] = f"{LABELS[name]}: {exc}. Último valor válido preservado."
        return
    exact = str(Decimal(proposed[name]))
    st.session_state[_key("value_" + name)] = exact
    st.session_state[_key("field_" + name)] = exact
    st.session_state[_key("notice")] = None


def _commit_slider(name: str, slider_key: str) -> None:
    proposed = _values()
    proposed[name] = str(st.session_state[slider_key])
    try:
        _validate(proposed)
    except (DomainError, ValueError, ArithmeticError) as exc:
        st.session_state[_key("notice")] = f"{LABELS[name]}: {exc}. Último valor válido preservado."
        return
    st.session_state[_key("value_" + name)] = proposed[name]
    st.session_state[_key("field_" + name)] = proposed[name]
    st.session_state[_key("notice")] = None


def _control(name: str) -> None:
    st.text_input(LABELS[name], key=_key("field_" + name),
                  on_change=_commit_field, args=(name,))
    exact = Decimal(st.session_state[_key("value_" + name)])
    spec = slider_spec("A" if name in ("AA", "AB") else name, exact)
    slider_key = _key(f"slider_{name}_{spec.minimum}_{spec.maximum}")
    if slider_key not in st.session_state or st.session_state[slider_key] != spec.position:
        st.session_state[slider_key] = spec.position
    st.slider(f"Ajuste visual de {LABELS[name]}", min_value=spec.minimum,
              max_value=spec.maximum, step=spec.step, format="%.9g",
              key=slider_key, on_change=_commit_slider, args=(name, slider_key))
    if spec.expanded or spec.approximate:
        st.caption(f"Valor econômico confirmado: {exact}. O slider é uma aproximação visual.")


def _controls() -> None:
    st.subheader("Condições econômicas comuns")
    for name in ("R", "PX", "PY"):
        _control(name)
    st.subheader("Preferências individuais")
    _control("AA")
    _control("AB")
    with st.popover("Restaurar comparação"):
        st.write("Restaurar somente este modo aos valores e à visualização iniciais?")
        if st.button("Confirmar restauração da comparação"):
            st.session_state[_key("reset_pending")] = True
            st.rerun()


def _table(comparison) -> None:
    a, b = comparison.consumer_a.basket, comparison.consumer_b.basket
    sa, sb = comparison.spending_a, comparison.spending_b
    pa, pb = shares(comparison)
    dx_share, dy_share = share_differences(comparison)
    def row(label, va, vb, difference=None, unit=""):
        return {"Indicador": label,
                "Consumidor A": f"{_number(va)}{unit}",
                "Consumidor B": f"{_number(vb)}{unit}",
                "Diferença B−A": f"{_number(difference)}{unit}" if difference is not None else "—"}
    st.table([
        row("Quantidade ótima de X", a.x, b.x, comparison.difference_x),
        row("Quantidade ótima de Y", a.y, b.y, comparison.difference_y),
        row("Despesa em X (R$)", sa[0], sb[0]),
        row("Despesa em Y (R$)", sa[1], sb[1]),
        row("Participação de X", pa[0], pb[0], dx_share, "%"),
        row("Participação de Y", pa[1], pb[1], dy_share, "%"),
        row("Despesa total (R$)", comparison.consumer_a.budget.income,
            comparison.consumer_b.budget.income),
    ])


def _query(comparison, target: str | None) -> None:
    if not target:
        st.caption("Clique nos marcadores A ou B para consultar suas cestas calculadas.")
        return
    profiles = ("A", "B") if target == "A=B" else (target,)
    for profile in profiles:
        solution = comparison.consumer_a if profile == "A" else comparison.consumer_b
        basket = solution.basket
        st.info(f"Consulta · Consumidor {profile}: X ≈ {_number(basket.x)}, "
                f"Y ≈ {_number(basket.y)}. A escolha permanece calculada pelo núcleo.")


def _analysis(comparison) -> None:
    st.subheader("Síntese econômica")
    st.write(interpretation(comparison))
    with st.expander("Análise econômica e matemática", expanded=False):
        tabs = st.tabs(("Leitura econômica", "Estrutura matemática",
                        "Desenvolvimento matemático", "Propriedades e limites"))
        b = comparison.consumer_a.budget
        a, z = comparison.consumer_a.alpha, comparison.consumer_b.alpha
        with tabs[0]:
            st.write("As condições orçamentárias são idênticas. Cada perfil distribui a mesma renda entre X e Y segundo sua preferência. Despesas e parcelas podem ser comparadas; números de utilidade de pessoas distintas não medem diferenças de bem-estar.")
        with tabs[1]:
            st.latex(r"P_X X+P_Y Y\leq R")
            st.latex(rf"{b.price_x}X+{b.price_y}Y\leq {b.income}")
            st.latex(r"X_i^*=\frac{\alpha_iR}{P_X},\qquad Y_i^*=\frac{(1-\alpha_i)R}{P_Y},\quad i\in\{A,B\}")
            st.write(f"Parâmetros efetivos: α_A = {a}; α_B = {z}.")
        with tabs[2]:
            st.write("As duas soluções são calculadas separadamente sob a mesma restrição. Para cada perfil, a despesa em X corresponde à sua parcela α da renda e a despesa em Y à parcela restante.")
            st.write(f"No cenário atual, A gasta R$ {_number(comparison.spending_a[0])} em X e R$ {_number(comparison.spending_a[1])} em Y; B gasta R$ {_number(comparison.spending_b[0])} em X e R$ {_number(comparison.spending_b[1])} em Y.")
        with tabs[3]:
            st.write("Cobb–Douglas pressupõe renda e preços positivos e 0 < α < 1. Os dois ótimos são interiores e esgotam o orçamento. Igualdade de α implica coincidência das escolhas sob estas condições comuns.")
            st.write("O gráfico usa coordenadas float aproximadas; entradas e decisões econômicas permanecem em Decimal. Não há comparação cardinal de utilidade nem referência histórica neste modo.")
    with st.expander("Sobre o modelo", expanded=False):
        st.write("Comparação teórica entre dois perfis Cobb–Douglas sob renda e preços idênticos. Ela não mede diferenças interpessoais de bem-estar nem prevê escolhas empíricas.")


def render() -> None:
    _initial_state()
    if st.session_state.pop(_key("reset_pending"), False):
        _reset()
    st.title("Módulo 03 · Decisões do Consumidor")
    st.caption("Experimento A · Comparação entre consumidores · Módulo 03 — Decisões do Consumidor")
    st.write("Como preferências diferentes afetam as escolhas sob o mesmo orçamento?")
    left, right = st.columns([1, 2.1], gap="large")
    with left:
        _controls()
    comparison = calculate(_values())
    with right:
        notice = st.session_state[_key("notice")]
        if notice:
            st.error(notice)
        budget = comparison.consumer_a.budget
        st.caption(rf"Orçamento comum: R\$ {_number(budget.income, exact=True)} · "
                   rf"X a R\$ {_number(budget.price_x, exact=True)} · "
                   rf"Y a R\$ {_number(budget.price_y, exact=True)}")
        st.selectbox("Arraste no gráfico", ("Mover (Pan)", "Ampliar região"),
                     key=_key("drag"))
        ca, cb = st.columns(2)
        ca.checkbox("Curva ótima de A", key=_key("curve_A"))
        cb.checkbox("Curva ótima de B", key=_key("curve_B"))
        auto = automatic_view(comparison)
        view = st.session_state[_key("view")] or auto
        traces, warnings, targets = plot_data(comparison,
                                              curve_a=st.session_state[_key("curve_A")],
                                              curve_b=st.session_state[_key("curve_B")],
                                              view=view)
        layout = {"height": 500, "margin": {"l": 65, "r": 25, "t": 25,
                                            "b": 55, "autoexpand": False},
                  "dragmode": "pan" if st.session_state[_key("drag")] == "Mover (Pan)" else "zoom",
                  "clickmode": "event", "clickanywhere": True, "hovermode": "closest",
                  "xaxis": {"title": "Quantidade de X", "range": auto["x"]},
                  "yaxis": {"title": "Quantidade de Y", "range": auto["y"]},
                  "legend": {"orientation": "h", "y": -0.23}}
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
        c1, c2, c3 = st.columns(3)
        if c1.button("Enquadrar todos"):
            st.session_state[_key("view")] = None
            st.rerun()
        if c2.button("Focar A"):
            st.session_state[_key("view")] = focus_view(comparison.consumer_a.basket)
            st.rerun()
        if c3.button("Focar B"):
            st.session_state[_key("view")] = focus_view(comparison.consumer_b.basket)
            st.rerun()
        if objects_outside(view, comparison.consumer_a.basket, comparison.consumer_b.basket):
            st.caption("Há ótimos fora do enquadramento. Use ‘Enquadrar todos’ para localizá-los.")
        for warning in warnings:
            st.warning(warning)
        _query(comparison, st.session_state[_key("query")])
        st.subheader("Indicadores comparativos")
        _table(comparison)
        _analysis(comparison)

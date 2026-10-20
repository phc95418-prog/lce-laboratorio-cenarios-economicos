"""Camada analítica determinística do M01, sem Streamlit, Plotly ou M02.

Contratos: analisar_exploracao recebe UM resultado de simular_mercado (também
serve ao cenário destacado na aba Simulação); analisar_experimento_a/b recebem
os TRÊS pares (nome, resultado) de resultados_cenarios. Não há seleção implícita
de destaque nem memória de edições anteriores. A base individual é sempre o
equilíbrio sem imposto NAS MESMAS CURVAS, nunca uma edição anterior.

Saída imutável: síntese, base, três dimensões e snapshots numéricos completos.
Fórmulas separam expressão, substituição LaTeX e interpretação. Textos monetários
são texto simples (R$), a escapar na futura interface Markdown. Nenhum cálculo
usa os números formatados; o motor continua sendo a fonte dos resultados.
Comparações aceitam somente os presets e as faixas atuais: A [0,80], B [0,40].
Referências: Convergência M01 v0.1, §§3–5/AC-03–05; Arquitetura v1.1, §§4–8.
"""

from collections.abc import Mapping
from dataclasses import dataclass
import math

from experimentos import cenarios_experimento_a, cenarios_experimento_b
from modelo_mercado import validar_parametros


DIMENSOES = ("Leitura econômica", "Estrutura matemática", "Propriedades e limites")
_NUMERICOS = (
    "a", "b", "c", "d", "t", "q0", "p0", "qt", "reducao_quantidade",
    "elasticidade_demanda_0", "elasticidade_oferta_0",
    "fracao_consumidor_potencial", "fracao_produtor_potencial",
    "ec0", "ep0", "et0", "ec", "ep", "arrecadacao", "et", "peso_morto",
    "perda_ec", "perda_ep",
)
_PRECOS = ("pc", "pp", "aumento_preco_consumidor", "queda_preco_produtor")
_FRACOES = ("fracao_consumidor_efetiva", "fracao_produtor_efetiva")
_HIPOTESES = (
    "Modelo estático de equilíbrio parcial competitivo, bem homogêneo e curvas lineares; "
    "a oferta representa custo marginal, sem externalidades. São simulações teóricas, não previsões empíricas.",
    "Bem-estar monetário pressupõe ausência de efeitos-renda relevantes, por exemplo preferências quase lineares. "
    "O excedente do produtor não equivale automaticamente ao lucro líquido ou contábil: não deduz custos fixos.",
    "A arrecadação entra uma única vez no excedente total, como transferência com o mesmo peso monetário "
    "dos excedentes privados. Não se avaliam gasto público, distribuição, custos de arrecadação, evasão, "
    "dinâmica ou efeitos em outros mercados; peso morto não é avaliação completa de uma política real.",
    "Elasticidades são pontuais no equilíbrio inicial; inclinação não é elasticidade constante. "
    "Com c≥0, P>0 e Q>0, ε_S=1+c/(dQ)≥1; relativamente menos elástica não significa necessariamente inelástica.",
    "A irrelevância da obrigação legal de recolhimento para a incidência depende das hipóteses competitivas "
    "e da ausência de fricções; não constitui lei empírica universal.",
    "Preços e imposto em R$/unidade; quantidades em unidades por período; excedentes, arrecadação e "
    "peso morto em R$/período. Arredondamento somente para leitura, sem alterar valores internos.",
)


@dataclass(frozen=True)
class Formula:
    cenario: str
    titulo: str
    expressao: str
    substituicao: str
    interpretacao: str


@dataclass(frozen=True)
class Cenario:
    nome: str
    regime: str
    valores: tuple[tuple[str, float | bool | None], ...]


@dataclass(frozen=True)
class Analise:
    ambiente: str
    base: str
    sintese: str
    leitura: tuple[str, ...]
    estrutura: tuple[Formula, ...]
    propriedades: tuple[str, ...]
    cenarios: tuple[Cenario, ...]


def _numero(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _moeda(v):
    return "R$ " + _numero(v)


def _latex(v):
    """Representação round-trip; não arredonda valores antes da substituição."""
    v = float(v)
    texto = str(int(v)) if v.is_integer() else repr(v)
    if "e" in texto:
        mantissa, expoente = texto.split("e")
        texto = mantissa + r"\times10^{" + str(int(expoente)) + "}"
    return texto.replace(".", "{,}")


def _finito(v):
    try:
        return type(v) in (int, float) and math.isfinite(v)
    except OverflowError:
        return False


def _validar_resultado(resultado):
    """Valida o contrato recebido, sem recalcular equilíbrios ou corrigir dados."""
    if not isinstance(resultado, Mapping):
        raise ValueError("Esperado um resultado completo do núcleo econômico.")
    r = dict(resultado)
    obrigatorios = (*_NUMERICOS, *_PRECOS, *_FRACOES, "ha_transacoes")
    if any(k not in r for k in obrigatorios):
        raise ValueError("Resultado incompleto do núcleo econômico.")
    if any(not _finito(r[k]) for k in _NUMERICOS):
        raise ValueError("Resultados numéricos devem ser reais finitos, sem arredondamento prévio.")
    validar_parametros(*(r[k] for k in ("a", "b", "c", "d", "t")))
    if (type(r["ha_transacoes"]) is not bool or r["q0"] <= 0 or r["p0"] <= 0
            or not 0 <= r["qt"] <= r["q0"]):
        raise ValueError("Quantidade, preço inicial ou estado de transações inválido.")
    ha = r["ha_transacoes"]
    if ha != (r["qt"] > 0) or ha != (r["t"] < r["a"] - r["c"]):
        raise ValueError("Regime tributário inconsistente com as transações.")
    for k in _PRECOS:
        if (ha and not _finito(r[k])) or (not ha and r[k] is not None):
            raise ValueError("Preços e variações transacionados só se aplicam com comércio.")
    for k in _FRACOES:
        efetiva = ha and r["t"] > 0
        if (efetiva and (not _finito(r[k]) or not 0 <= r[k] <= 1)) or (not efetiva and r[k] is not None):
            raise ValueError("Incidência efetiva só se aplica com imposto positivo e comércio.")
    if any(r[k] < 0 for k in ("ec0", "ep0", "et0", "ec", "ep", "arrecadacao", "et", "peso_morto")):
        raise ValueError("Excedentes, arrecadação e perda devem ser não negativos.")
    return r


def _regime(r):
    return "sem_imposto" if r["t"] == 0 else "interior" if r["ha_transacoes"] else "proibitivo"


def _cenario(nome, r):
    return Cenario(nome, _regime(r), tuple((k, r[k]) for k in (*_NUMERICOS, *_PRECOS, *_FRACOES, "ha_transacoes")))


def _conteudo(nome, r):
    n = {k: _latex(r[k]) for k in _NUMERICOS}
    a, b, c, d, t = (n[k] for k in ("a", "b", "c", "d", "t"))
    q0, qt = n["q0"], n["qt"]
    formulas = []

    def formula(titulo, expressao, substituicao, interpretacao):
        formulas.append(Formula(nome, titulo, expressao, substituicao, interpretacao))

    formula("Curvas vigentes", r"P_D(Q)=a-bQ,\quad P_S(Q)=c+dQ",
            rf"P_D(Q)={a}-({b})Q,\quad P_S(Q)={c}+({d})Q",
            "Demanda é disposição marginal a pagar; oferta é custo marginal. O imposto não altera a tecnologia.")
    formula("Equilíbrios e quantidade", r"Q_0=\frac{a-c}{b+d},\quad P_0=c+dQ_0,\quad Q_t=\max\left(0,\frac{a-c-t}{b+d}\right)",
            rf"Q_0=\frac{{{a}-{c}}}{{{b}+{d}}}\approx {q0},\quad P_0={c}+({d})({q0})\approx {n['p0']},\quad Q_t=\max\left(0,\frac{{{a}-{c}-{t}}}{{{b}+{d}}}\right)\approx {qt}",
            "Mesmas curvas antes/depois do imposto; a quantidade não pode ser negativa.")
    formula("Elasticidades iniciais e coeficientes potenciais",
            r"|\varepsilon_{D,0}|=\frac{P_0}{bQ_0},\quad\varepsilon_{S,0}=\frac{P_0}{dQ_0},\quad s_C=\frac{b}{b+d}=\frac{\varepsilon_{S,0}}{\varepsilon_{S,0}+|\varepsilon_{D,0}|},\quad s_P=\frac{d}{b+d}=\frac{|\varepsilon_{D,0}|}{\varepsilon_{S,0}+|\varepsilon_{D,0}|}",
            rf"|\varepsilon_{{D,0}}|=\frac{{{n['p0']}}}{{({b})({q0})}}\approx {_latex(abs(r['elasticidade_demanda_0']))},\quad\varepsilon_{{S,0}}=\frac{{{n['p0']}}}{{({d})({q0})}}\approx {n['elasticidade_oferta_0']},\quad s_C=\frac{{{b}}}{{{b}+{d}}}\approx {n['fracao_consumidor_potencial']},\quad s_P=\frac{{{d}}}{{{b}+{d}}}\approx {n['fracao_produtor_potencial']}",
            "Coeficientes potenciais; só representam carga efetiva por unidade se 0<t<a−c. Elasticidades avaliadas em P₀,Q₀.")
    leitura = []
    propriedades = [f"{nome}: domínio a>c≥0, b,d>0, t≥0; limiar proibitivo a−c={_moeda(r['a']-r['c'])}/unidade. Demanda econômica: Q≥0 e P_D(Q)≥0."]
    if r["t"] == 0:
        sintese = f"{nome}: imposto zero; Q={_numero(r['qt'])}, preços iguais a {_moeda(r['p0'])}/unidade; arrecadação e peso morto nulos."
        leitura.append(f"{nome}: sem imposto, há transações e preços válidos: P_C=P_P=P₀={_moeda(r['p0'])}/unidade. Não há carga tributária efetiva; as parcelas são apenas potenciais.")
        formula("Preços sem imposto", r"t=0:\quad P_C=P_P=P_0,\quad Q_t=Q_0",
                rf"P_C=P_P={n['p0']},\quad Q_t=Q_0={q0}",
                "Preços válidos, nenhuma incidência efetiva nem divisão por imposto zero.")
    elif r["ha_transacoes"]:
        sintese = f"{nome}: Q {_numero(r['q0'])} → {_numero(r['qt'])}; arrecadação {_moeda(r['arrecadacao'])} e peso morto {_moeda(r['peso_morto'])} por período."
        sc, sp = r["fracao_consumidor_efetiva"], r["fracao_produtor_efetiva"]
        lado = "igualmente entre os dois lados" if sc == sp else "em maior parcela pelos consumidores" if sc > sp else "em maior parcela pelos produtores"
        leitura.append(f"{nome}: o imposto é suportado {lado}, segundo as sensibilidades relativas no equilíbrio inicial. "
                       f"Consumidores: {_numero(100*sc)}%; produtores: {_numero(100*sp)}% por unidade. "
                       f"P_C={_moeda(r['pc'])} e P_P={_moeda(r['pp'])}/unidade; aumento ao consumidor {_moeda(r['aumento_preco_consumidor'])} "
                       f"e redução ao produtor {_moeda(r['queda_preco_produtor'])}/unidade.")
        formula("Preços e repasse efetivo — 0<t<a−c",
                r"P_C=a-bQ_t,\quad P_P=c+dQ_t,\quad P_C-P_P=t,\quad\Delta Q=\frac{t}{b+d}",
                rf"P_C={a}-({b})({qt})\approx {_latex(r['pc'])},\quad P_P={c}+({d})({qt})\approx {_latex(r['pp'])},\quad {_latex(r['pc'])}-{_latex(r['pp'])}\approx {t},\quad\Delta Q=\frac{{{t}}}{{{b}+{d}}}\approx {n['reducao_quantidade']}",
                "Cunha e repasse por unidade transacionada; não são a perda total dos excedentes privados.")
        formula("Peso morto no interior", r"0<t<a-c:\quad PM=\frac{t^2}{2(b+d)}",
                rf"PM=\frac{{({t})^2}}{{2({b}+{d})}}\approx {n['peso_morto']}",
                "Expressão interior; coincide no limiar, mas não deve ser extrapolada acima dele.")
    else:
        sintese = f"{nome}: imposto proibitivo; Q=0, sem preços transacionados nem carga efetiva; arrecadação zero e peso morto {_moeda(r['peso_morto'])} por período."
        leitura.append(f"{nome}: não há transações, preços efetivamente negociados ou incidência efetiva. Os coeficientes de repasse são apenas potenciais. "
                       f"A arrecadação é zero; a perda de eficiência atinge todo o excedente inicial, {_moeda(r['et0'])} por período.")
        formula("Encerramento das transações", r"t\geq a-c:\quad Q_t=0,\quad EC_t=EP_t=R_t=ET_t=0,\quad PM=ET_0",
                rf"{t}\geq {a}-{c},\quad Q_t=0,\quad PM=ET_0={n['et0']}",
                "P_C e P_P não se aplicam. Não se impõem a cunha nem a redução linear de quantidade a transações inexistentes.")
        if r["t"] == r["a"] - r["c"]:
            propriedades.append(f"{nome}: no limiar, a e c são preços de reserva no limite, não preços transacionados.")
        else:
            propriedades.append(f"{nome}: acima do limiar, a quantidade permanece zero e PM=ET₀; a expressão quadrática interior em t superestimaria a perda.")
    leitura.append(f"{nome}: quantidade {_numero(r['q0'])} → {_numero(r['qt'])}, redução de {_numero(r['reducao_quantidade'])} unidades por período. "
                   f"EC {_moeda(r['ec0'])} → {_moeda(r['ec'])}; EP {_moeda(r['ep0'])} → {_moeda(r['ep'])}; "
                   f"arrecadação {_moeda(r['arrecadacao'])}; peso morto {_moeda(r['peso_morto'])} por período.")
    perda_privada = r["perda_ec"] + r["perda_ep"]
    leitura.append(f"{nome}: a perda total de excedentes privados é {_moeda(perda_privada)} por período "
                   f"(consumidores {_moeda(r['perda_ec'])}; produtores {_moeda(r['perda_ep'])}). "
                   f"Dela, {_moeda(r['arrecadacao'])} corresponde à transferência ao governo e {_moeda(r['peso_morto'])} à perda líquida de eficiência. "
                   "Isso difere da repartição da cunha por unidade; arrecadação não é peso morto.")
    if r["ha_transacoes"] and r["t"] > 0:
        contribuicao_c = r["aumento_preco_consumidor"] * r["qt"]
        contribuicao_p = r["queda_preco_produtor"] * r["qt"]
        leitura.append(f"{nome}: sobre as unidades ainda vendidas, a contribuição associada ao aumento do preço ao consumidor "
                       f"é {_moeda(contribuicao_c)} e ao menor preço recebido pelo produtor é {_moeda(contribuicao_p)} por período; "
                       "juntas compõem a arrecadação, não as perdas totais de excedente, que incluem as trocas eliminadas.")
    formula("Excedentes iniciais", r"EC_0=\frac{bQ_0^2}{2},\quad EP_0=\frac{dQ_0^2}{2},\quad ET_0=EC_0+EP_0",
            rf"EC_0=\frac{{({b})({q0})^2}}{{2}}\approx {n['ec0']},\quad EP_0=\frac{{({d})({q0})^2}}{{2}}\approx {n['ep0']},\quad ET_0={n['ec0']}+{n['ep0']}\approx {n['et0']}",
            "Base sem imposto nas mesmas curvas, em R$/período.")
    formula("Excedentes privados", r"EC_t=\frac{bQ_t^2}{2},\quad EP_t=\frac{dQ_t^2}{2}",
            rf"EC_t=\frac{{({b})({qt})^2}}{{2}}\approx {n['ec']},\quad EP_t=\frac{{({d})({qt})^2}}{{2}}\approx {n['ep']}",
            "Expressões em quantidade: valem também para Q_t=0, sem inventar preços.")
    formula("Arrecadação e excedente total", r"R_t=tQ_t,\quad ET_t=EC_t+EP_t+R_t",
            rf"R_t=({t})({qt})\approx {n['arrecadacao']},\quad ET_t={n['ec']}+{n['ep']}+{n['arrecadacao']}\approx {n['et']}",
            "Arrecadação contabilizada uma única vez, em R$/período.")
    formula("Perda de eficiência — expressão geral", r"PM=ET_0-ET_t=\frac{b+d}{2}(Q_0-Q_t)^2",
            rf"PM={n['et0']}-{n['et']}\approx\frac{{{b}+{d}}}{{2}}({q0}-{qt})^2\approx {n['peso_morto']}",
            "Válida em todo t≥0, inclusive acima do imposto proibitivo; queda limitada a Q₀.")
    formula("Perdas privadas e transferência", r"(EC_0-EC_t)+(EP_0-EP_t)=R_t+PM",
            rf"({n['ec0']}-{n['ec']})+({n['ep0']}-{n['ep']})\approx {n['arrecadacao']}+{n['peso_morto']}",
            "Perda privada não é toda perda de eficiência: parte é transferência ao governo.")
    return sintese, tuple(leitura), tuple(formulas), tuple(propriedades)


def analisar_exploracao(resultado, *, nome="Mercado vigente"):
    """Análise individual nas curvas vigentes, inclusive de um destaque de A/B."""
    if not isinstance(nome, str) or not nome.strip():
        raise ValueError("Identifique o cenário individual.")
    r = _validar_resultado(resultado)
    sintese, leitura, estrutura, propriedades = _conteudo(nome, r)
    base = f"{nome}: equilíbrio sem imposto → equilíbrio tributado nas mesmas curvas vigentes; não compara edições anteriores nem outros mercados."
    return Analise("Individual", base, sintese, leitura, estrutura,
                   propriedades + _HIPOTESES, (_cenario(nome, r),))


def _comparar(cenarios, experimento):
    try:
        pares = list(cenarios)
        if len(pares) != 3 or any(len(p) != 2 for p in pares):
            raise ValueError
        nomes = [p[0] for p in pares]
        if any(not isinstance(n, str) or not n.strip() for n in nomes) or len(set(nomes)) != 3:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("A comparação requer três pares (nome único, resultado).") from None
    dados = [(nome, _validar_resultado(r)) for nome, r in pares]
    t = dados[0][1]["t"]
    limite = 80 if experimento == "A" else 40
    if t > limite or any(r["t"] != t for _, r in dados):
        raise ValueError(f"Experimento {experimento}: imposto comum na faixa [0,{limite}].")
    fabrica = cenarios_experimento_a if experimento == "A" else cenarios_experimento_b
    esperados = [p for _, p in fabrica(t)]
    # Validar a coleção completa impede atribuir invariâncias dos presets a
    # mercados arbitrários. Ordem e rótulos podem mudar, mas não os parâmetros.
    for _, r in dados:
        indice = next((i for i, p in enumerate(esperados)
                       if all(r[k] == p[k] for k in ("a", "b", "c", "d", "t"))), None)
        if indice is None:
            raise ValueError(f"Os três mercados devem corresponder aos presets do Experimento {experimento}.")
        esperados.pop(indice)
    conteudos = [_conteudo(nome, r) for nome, r in dados]
    if experimento == "A":
        base = "Comparação conjunta dos três mercados de A: P₀=60, Q₀=40, mesmo imposto e b+d=2; variam as inclinações relativas e os interceptos compatíveis."
        leitura = ("Para o mesmo imposto, Qₜ, arrecadação e peso morto coincidem ENTRE os três cenários. "
                   "As parcelas do consumidor são 50%, 75% e 25% nos respectivos presets; efetivas somente com imposto positivo e transações. "
                   "A divisão muda com as sensibilidades relativas, sem mudar a redução da quantidade neste desenho.",)
        propriedades = ("As invariâncias decorrem de Q₀, b+d e imposto comuns: não são leis universais. "
                        "Quantidade, arrecadação e peso morto podem mudar quando o imposto comum muda; não se atribui o efeito a uma variável isolada fora desse controle.",)
    else:
        base = "Comparação conjunta dos três mercados de B: P₀=60, Q₀=40 e mesmo imposto; b=d em cada mercado, mas variam a magnitude das inclinações e os interceptos compatíveis."
        leitura = ("Nos equilíbrios interiores, inclinações menores e elasticidades iniciais maiores implicam maior queda de quantidade, "
                   "menor base tributada e arrecadação e maior peso morto para o mesmo imposto positivo, apesar do repasse simétrico de 50% por lado. "
                   "Com imposto zero, não há distorção nem incidência efetiva em nenhum mercado.",
                   "Os excedentes totais iniciais diferem entre os mercados: " + "; ".join(f"{nome}: ET₀={_moeda(r['et0'])} por período" for nome, r in dados) + ". "
                   "A comparação é condicional ao desenho controlado; não é ranking distributivo ou normativo.")
        propriedades = ("B1 tem limiar proibitivo t=40; B2, t=80; B3, t=100. Na faixa atual [0,40], "
                        "só B1 pode atingir a fronteira: nele não há preços transacionados nem carga efetiva em t=40, enquanto B2 e B3 continuam transacionando. "
                        "Os limiares maiores são propriedades do modelo, não novos controles de imposto.",)
    if experimento == "A":
        r = dados[0][1]
        qualificacao = "efetivas" if _regime(r) == "interior" else "apenas potenciais, sem carga efetiva"
        parcelas = "; ".join(f"{nome}: {_numero(100*r['fracao_consumidor_potencial'])}%" for nome, r in dados)
        estado = "Imposto zero. " if r["t"] == 0 else "Sem transações. " if not r["ha_transacoes"] else ""
        sintese = (estado + f"Parcelas do consumidor {qualificacao} — {parcelas}. Entre os mercados: "
                   f"Qₜ={_numero(r['qt'])}, arrecadação {_moeda(r['arrecadacao'])} e peso morto {_moeda(r['peso_morto'])} por período, iguais.")
    else:
        sintese = " | ".join(f"{nome}: Qₜ={_numero(r['qt'])}; R={_moeda(r['arrecadacao'])}; PM={_moeda(r['peso_morto'])} por período"
                             + ("; sem transações ou carga efetiva" if not r['ha_transacoes'] else "")
                             for nome, r in dados)
    return Analise("Experimento " + experimento, base, sintese,
                   leitura + tuple(texto for item in conteudos for texto in item[1]),
                   tuple(f for item in conteudos for f in item[2]),
                   propriedades + tuple(texto for item in conteudos for texto in item[3]) + _HIPOTESES,
                   tuple(_cenario(nome, r) for nome, r in dados))


def analisar_experimento_a(cenarios):
    """Comparação conjunta dos três presets A; imposto comum entre 0 e 80."""
    return _comparar(cenarios, "A")


def analisar_experimento_b(cenarios):
    """Comparação conjunta dos três presets B; imposto comum entre 0 e 40."""
    return _comparar(cenarios, "B")

"""Investigação opcional do Experimento A do LCE.

Textos derivados dos cenários de modelo_mercado, sem refazer os cálculos.
As três etapas (observação, explicação, síntese) não bloqueiam a simulação.
"""

QUESTOES = {
    "incidencia": "Por que consumidores e produtores suportam parcelas diferentes do imposto?",
    "quantidade": "A quantidade comercializada acompanha as mudanças na incidência?",
    "imposto": "O que acontece quando aumentamos o imposto?",
}
NIVEIS = ("Intuição", "Leitura dos gráficos", "Matemática")


def _numero(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _moeda(valor):
    return f"R$ {_numero(valor)}"


def _estado(cenarios):
    """Identifica situação efetiva do conjunto do Experimento A."""
    resultados = [r for _, r in cenarios]
    if not resultados:
        raise ValueError("O experimento A precisa de cenários para investigar.")
    if resultados[0]["t"] == 0:
        return "sem_imposto"
    if all(not r["ha_transacoes"] for r in resultados):
        return "sem_transacoes"
    return "interior"


def _validar(questao, nivel=None):
    if questao not in QUESTOES:
        raise ValueError("Questão desconhecida.")
    if nivel is not None and nivel not in NIVEIS:
        raise ValueError("Nível desconhecido.")


def sugestao(questao, cenarios):
    """Oferece orientação sem entregar a conclusão antecipadamente."""
    _validar(questao)
    estado = _estado(cenarios)
    if questao == "incidencia":
        if estado == "sem_imposto":
            return ("Com imposto zero, não há carga tributária efetiva. "
                    "Compare os repasses *potenciais* das barras; depois aumente o imposto.")
        if estado == "sem_transacoes":
            return ("Não há transações no ponto atual. Reduza o imposto e "
                    "compare as diferenças de preços nos três cenários.")
        return ("Compare os preços pagos por consumidores e recebidos por produtores "
                "nos três cenários. Quem tem a maior variação em relação ao preço inicial?")
    if questao == "quantidade":
        if estado == "sem_imposto":
            return ("Com imposto zero, Q após imposto coincide com Q₀. "
                    "Aumente um pouco o imposto e compare as quedas entre os cenários.")
        if estado == "sem_transacoes":
            return ("Com a quantidade tributada zerada, reduza o imposto e "
                    "observe se os três mercados recuperam transações na mesma proporção.")
        return ("Compare Q₀ e Q após imposto nos três cenários e observe "
                "os percentuais de repasse. As duas comparações variam da mesma maneira?")
    if estado == "sem_transacoes":
        return ("Sem transações, a arrecadação é zero. Reduza gradualmente o "
                "imposto e procure o ponto em que a receita foi maior.")
    return ("Mova o imposto na lateral e acompanhe a quantidade, a arrecadação "
            "e o peso morto na tabela. O efeito do imposto é sempre proporcional?")


def explicacao(questao, nivel, cenarios):
    """Explica os resultados atuais no nível escolhido, com números dinâmicos."""
    _validar(questao, nivel)
    estado = _estado(cenarios)
    r = cenarios[0][1]
    t, q0, qt = r["t"], r["q0"], r["qt"]
    soma = r["b"] + r["d"]
    reducao = q0 - qt

    if questao == "incidencia":
        if nivel == "Intuição":
            if estado == "sem_imposto":
                return ("Sem imposto, não há custo tributário a distribuir. "
                        "A sensibilidade de demanda e oferta indica como um pequeno "
                        "imposto *poderia* ser dividido, mas ainda não houve repasse efetivo.")
            if estado == "sem_transacoes":
                return ("Sem trocas, não há pagamentos de imposto nem repartição efetiva. "
                        "As parcelas exibidas são apenas coeficientes *potenciais* "
                        "do modelo, não valores efetivamente pagos.")
            return ("O lado menos sensível a variações de preço tem menor capacidade "
                    "de ajustar a quantidade e tende a suportar uma parcela maior da "
                    "cunha tributária. Na situação simétrica, o encargo é dividido "
                    "igualmente; quando as sensibilidades diferem, a divisão muda.")
        if nivel == "Leitura dos gráficos":
            if estado == "sem_imposto":
                return (
                    "Com **imposto zero**, os mercados continuam realizando transações "
                    f"em Q₀ = {_numero(q0)} ao preço de equilíbrio P₀ = {_moeda(r['p0'])}. "
                    "Os preços pagos e recebidos são válidos e iguais ao preço inicial. "
                    "O que não existe é carga tributária efetivamente suportada; "
                    "as barras indicam somente parcelas *potenciais* de repasse "
                    "para um imposto positivo."
                )
            if estado == "sem_transacoes":
                return (
                    "Com **imposto proibitivo**, nenhuma unidade é comercializada. "
                    "Não existem preços efetivos de compra e venda, nem arrecadação "
                    "ou incidência tributária realizada. As barras representam "
                    "apenas parcelas *potenciais* de repasse, não pagamentos observados."
                )
            linhas = []
            for nome, cenario in cenarios:
                subiu = cenario["pc"] - cenario["p0"]
                caiu = cenario["p0"] - cenario["pp"]
                linhas.append(
                    f"- **{nome}:** o preço ao consumidor sobe {_moeda(subiu)} "
                    f"e o preço ao produtor cai {_moeda(caiu)}."
                )
            return (
                "No gráfico, compare a altura das parcelas de consumidores e "
                "produtores. Na tabela, a diferença entre os preços e P₀ mostra "
                "o mesmo fenômeno em valores monetários, para o imposto "
                f"**atual de {_moeda(t)} por unidade**:\n\n"
                + "\n".join(linhas)
                + "\n\nEm cada cenário, essas duas variações de preço somam "
                f"{_moeda(t)}, exatamente o imposto por unidade."
            )
        exemplo_nome, exemplo = cenarios[1]
        parcela_consumidor = exemplo["b"] / (exemplo["b"] + exemplo["d"])
        parcela_produtor = 1 - parcela_consumidor
        texto = (
            "As curvas inversas possuem inclinações b e d. No equilíbrio "
            "interior, as parcelas do imposto são b/(b+d) para consumidores "
            "e d/(b+d) para produtores. Por exemplo, em **"
            f"{exemplo_nome}**, b = {_numero(exemplo['b'])} e "
            f"d = {_numero(exemplo['d'])}: consumidor "
            f"{_numero(100*parcela_consumidor, 0)}% e produtor "
            f"{_numero(100*parcela_produtor, 0)}%."
        )
        if estado == "interior":
            texto += (
                f" Com o imposto atual de {_moeda(t)}, essas parcelas "
                f"correspondem a {_moeda(t*parcela_consumidor)} de aumento "
                f"no preço ao consumidor e {_moeda(t*parcela_produtor)} "
                "de redução no preço ao produtor."
            )
        else:
            texto += (" Neste ponto são apenas coeficientes *potenciais*: "
                      "não há incidência efetivamente paga, pois o imposto é "
                      "nulo ou não há transações.")
        return texto

    if questao == "quantidade":
        if nivel == "Intuição":
            if estado == "sem_imposto":
                return ("Com imposto zero, os três mercados estão no equilíbrio inicial. "
                        "Não existe redução de transações nem perda de eficiência "
                        "associada ao tributo.")
            if estado == "sem_transacoes":
                return ("O imposto atingiu o limite em que deixam de existir "
                        "transações. O modelo fixa a quantidade em zero, em vez "
                        "de permitir quantidades economicamente negativas.")
            return ("Os três mercados podem dividir o imposto de maneiras "
                    "diferentes e ainda perder o mesmo número de transações. "
                    "A repartição da carga e a resposta da quantidade são "
                    "mecanismos relacionados, mas não idênticos.")
        if nivel == "Leitura dos gráficos":
            pct = ", ".join(
                f"{_numero(100*cenario['fracao_consumidor_potencial'], 0)}%"
                for _, cenario in cenarios
            )
            qualificador = (
                "São divisões potenciais, não imposto efetivamente pago."
                if estado != "interior" else
                "Essas divisões correspondem ao imposto efetivamente repartido."
            )
            return (
                f"Na tabela, Q₀ = {_numero(q0)} e Q após imposto = {_numero(qt)} "
                f"nos três mercados: a queda é de {_numero(reducao)} unidades "
                "em cada um. Já as parcelas dos consumidores nas barras são "
                f"{pct}, respectivamente. {qualificador} "
                "Observe que a altura total de cada barra continua 100%, "
                "apesar das divisões diferentes."
            )
        return (
            f"Os três mercados possuem Q₀ = {_numero(q0)}, "
            f"b+d = {_numero(soma)} e imposto atual t = {_numero(t)}. "
            "Pela equação Qₜ = máx(0, Q₀ − t/(b+d)), obtemos "
            f"Qₜ = {_numero(qt)} e ΔQ = {_numero(reducao)}. "
            "As parcelas b/(b+d) e d/(b+d) podem mudar sem "
            "modificar sua soma. O mesmo denominador determina a "
            "redução da quantidade, respeitado o limite Qₜ ≥ 0."
        )

    if nivel == "Intuição":
        if estado == "sem_imposto":
            return ("Com imposto zero, não há transações perdidas, arrecadação "
                    "ou peso morto. Aumente o imposto para comparar a quantidade "
                    "comercializada e a receita obtida.")
        if estado == "sem_transacoes":
            return ("O imposto eliminou todas as transações. Não há arrecadação, "
                    "mas a perda de eficiência corresponde a todo o excedente inicial. "
                    "Um imposto ainda maior não pode eliminar mais transações.")
        return ("Aumentar o imposto reduz as transações e eleva o peso morto, "
                "mas a arrecadação não cresce indefinidamente. A taxa por "
                "unidade sobe ao mesmo tempo que a base tributada diminui.")
    if nivel == "Leitura dos gráficos":
        return (
            "As barras acima mostram a **repartição percentual**, não o total "
            "arrecadado. Para investigar a arrecadação e o peso morto, acompanhe "
            "as colunas da **tabela** e altere o imposto na lateral. "
            f"Com o imposto atual de {_moeda(t)}, a quantidade é "
            f"{_numero(qt)}, a arrecadação {_moeda(r['arrecadacao'])} "
            f"e o peso morto {_moeda(r['peso_morto'])}. "
            "Neste desenho do Experimento A, a receita é máxima quando "
            "t = 40 e vai a zero quando t = 80, pois as transações cessam."
        )
    return (
        "Neste Experimento A, Qₜ = máx(0, 40 − t/2) e R(t) = t·Qₜ. "
        "Para 0 ≤ t ≤ 80, a receita é R(t) = 40t − t²/2, "
        "com máximo em t = 40. "
        f"No imposto atual t = {_numero(t)}, calculamos "
        f"Qₜ = {_numero(qt)}, R = {_moeda(r['arrecadacao'])} "
        f"e PM = {_moeda(r['peso_morto'])}. "
        "Para t ≥ 80, Qₜ e arrecadação são zero, enquanto o "
        "peso morto atinge todo o excedente inicial."
    )


def sintese(questao, cenarios):
    """Conclusão opcional após explorar; nunca antes do gráfico."""
    _validar(questao)
    estado = _estado(cenarios)
    r = cenarios[0][1]
    if questao == "incidencia":
        percentuais = ", ".join(
            f"{_numero(100*c['fracao_consumidor_potencial'], 0)}%"
            for _, c in cenarios
        )
        if estado != "interior":
            return (
                "As barras indicam parcelas **potenciais** do consumidor "
                f"({percentuais}), mas neste ponto não há repartição efetiva "
                "de imposto. Reduza ou aumente o tributo até haver transações "
                "com imposto positivo para observar a incidência realizada."
            )
        return (
            "A parcela percentual do imposto suportada pelos consumidores varia "
            f"entre os três mercados ({percentuais}). Quando a demanda é "
            "relativamente menos elástica, o consumidor absorve uma parcela maior; "
            "quando a oferta é relativamente menos elástica, o produtor absorve "
            "uma parcela maior. Esse resultado depende das curvas do modelo."
        )
    if questao == "quantidade":
        inicio = (
            "Apesar das parcelas **efetivas** de incidência diferentes, "
            if estado == "interior" else
            "Apesar dos coeficientes **potenciais** de repasse diferentes, "
        )
        return (
            inicio + "os três mercados "
            f"apresentam Qₜ = {_numero(r['qt'])} e peso morto de "
            f"{_moeda(r['peso_morto'])}, para o imposto atual de "
            f"{_moeda(r['t'])}. Isso acontece porque Q₀ e b+d "
            "foram mantidos constantes, não porque a incidência e "
            "a perda de eficiência sejam sempre independentes."
        )
    return (
        f"Com o imposto atual de {_moeda(r['t'])} por unidade, a quantidade "
        f"comercializada é {_numero(r['qt'])}, a arrecadação é "
        f"{_moeda(r['arrecadacao'])} e o peso morto é "
        f"{_moeda(r['peso_morto'])}. "
        "Neste experimento controlado, a arrecadação máxima é R$ 800,00 "
        "com imposto de R$ 40,00 por unidade. Acima desse valor, "
        "a arrecadação diminui porque a quantidade tributada cai, "
        "enquanto o peso morto continua aumentando até o imposto proibitivo "
        "de R$ 80,00. Nesse limite, não há transações nem arrecadação."
    )


def formula(questao, nivel):
    """Notação matemática opcional, válida com as condições declaradas."""
    if nivel != "Matemática":
        return None
    if questao == "incidencia":
        return (r"\frac{P_C-P_0}{t}=\frac{b}{b+d},\qquad"
                r"\frac{P_0-P_P}{t}=\frac{d}{b+d}\quad (0<t<a-c)")
    if questao == "quantidade":
        return r"Q_t=\max\!\left(0,Q_0-\frac{t}{b+d}\right)"
    if questao == "imposto":
        return r"R(t)=tQ_t,\qquad PM=\frac{b+d}{2}(Q_0-Q_t)^2"
    raise ValueError("Questão desconhecida.")

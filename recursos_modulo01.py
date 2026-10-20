"""Conteúdo permanente e ajuda operacional do M01, sem estado ou cálculos.

Inventário de migração da antiga aba Modelo e hipóteses:
curvas/equilíbrios/cunha → curvas, equilíbrio e incidência;
integral/PM → bem-estar; hipóteses/limitação da oferta → hipóteses e domínios;
parâmetros calculados → consulta somente leitura em Sobre o modelo;
bibliografia → referências. A análise contextual da Etapa 1 permanece intacta.
"""

REFERENCIA = "https://docs.google.com/document/d/1-1l1HtqIrwz6G9piHSg244UXDW0aAUzhfTf9vQIf07A/edit"


def perguntas_frequentes(ambiente):
    contexto = {
        "Exploração livre": "Na Exploração livre, os dois equilíbrios usam as mesmas curvas vigentes. Não há comparação predefinida de três mercados.",
        "Experimento A": "Em A, os três mercados têm o mesmo equilíbrio inicial, imposto e soma das inclinações; diferem as inclinações relativas.",
        "Experimento B": "Em B, os três mercados têm o mesmo equilíbrio inicial e imposto; as inclinações são simétricas em cada mercado, com magnitudes diferentes.",
    }[ambiente]
    return (
        ("Como alternar entre os ambientes?", "O seletor Investigar fica em Configurar simulação, na lateral retrátil. Os três ambientes permanecem disponíveis. " + contexto),
        ("Onde altero os parâmetros econômicos?", "Na lateral Configurar simulação. A Exploração livre oferece entradas por elasticidades iniciais ou por equações; A/B têm imposto comum e cenário em destaque. A engrenagem contém somente opções da aplicação e documentação."),
        ("O que mostram os gráficos e indicadores?", "O gráfico de mercado mostra curvas, equilíbrio inicial e efeito do imposto; o gráfico de composição distingue excedentes e arrecadação. Quantidades, preços e bem-estar aparecem nos indicadores. Sem transações, os preços negociados não se aplicam."),
        ("Qual a diferença entre Simulação e Comparar cenários?", "Simulação interpreta apenas o mercado selecionado, comparando sem/com imposto nas mesmas curvas. Comparar cenários interpreta conjuntamente os três mercados de A ou B; mudar o destaque não reduz essa comparação."),
        ("Como acessar a análise econômica e matemática?", "A síntese fica visível abaixo dos resultados. A seção Análise econômica e matemática oferece Leitura econômica, Estrutura matemática e Propriedades e limites, acessíveis diretamente. Abrir as dimensões não altera o mercado."),
        ("Onde estão as hipóteses e a documentação?", "Em Configurações (engrenagem) → Sobre o modelo: descrição, equações gerais, domínios, parâmetros, unidades, limitações e referências. A análise contextual contém as substituições numéricas do mercado vigente."),
        ("Como exportar um gráfico?", "Em Configurações (engrenagem) → Exportar gráfico, selecione o gráfico disponível e escolha PNG, SVG ou PDF. Acione Exportar gráfico; no PDF, aguarde e use Baixar PDF preparado. O arquivo corresponde ao cenário vigente no momento da solicitação."),
    )


# Cada seção separa texto e LaTeX; não depende dos contratos do Módulo 02.
SOBRE_MODELO = (
    ("Descrição e hipóteses", (
        "Modelo de um único mercado competitivo, estático e de equilíbrio parcial, com bem homogêneo, curvas agregadas lineares e imposto específico por unidade vendida. Consumidores e produtores são tomadores de preços.",
        "A demanda representa disposição marginal a pagar e a oferta representa custo marginal relevante, com tecnologia mantida constante e ausência de externalidades. Bem-estar monetário requer hipóteses adicionais, como efeitos-renda desprezíveis ou preferências quase lineares.",
        "O excedente do produtor não equivale automaticamente ao lucro líquido ou contábil: não deduz custos fixos. Ao somar arrecadação e excedentes privados, atribui-se o mesmo peso marginal a cada unidade monetária, sem modelar custos de arrecadação, distribuição ou uso da receita pública.",
    ), ()),
    ("Curvas, equilíbrio e incidência", (
        "P_D é demanda inversa e P_S é oferta inversa. Q₀ e P₀ são o equilíbrio sem imposto. Com transações, P_C é o preço pago pelo consumidor e P_P, o preço líquido recebido pelo produtor.",
        "A oferta acrescida do imposto representa preço ao consumidor, não mudança tecnológica. A incidência econômica distingue-se da obrigação legal de recolhimento; sua invariância à incidência legal depende das hipóteses competitivas, sem fricções.",
        "As parcelas abaixo descrevem repasse por unidade, não perda total de excedentes. Com imposto zero, são somente coeficientes potenciais; sem transações, não há incidência efetiva.",
    ), (
        r"P_D(Q)=a-bQ,\quad P_S(Q)=c+dQ",
        r"Q_0=\frac{a-c}{b+d},\quad P_0=a-bQ_0=c+dQ_0",
        r"Q_t=\max\left(0,\frac{a-c-t}{b+d}\right)",
        r"0\leq t<a-c:\quad P_C=a-bQ_t,\quad P_P=c+dQ_t,\quad P_C-P_P=t",
        r"0<t<a-c:\quad s_C=\frac{b}{b+d},\quad s_P=\frac{d}{b+d},\quad s_C+s_P=1",
    )),
    ("Excedentes, arrecadação e perda de eficiência", (
        "EC é excedente do consumidor; EP, excedente do produtor; R, arrecadação; ET, excedente total; PM, peso morto ou perda de eficiência. A arrecadação entra uma única vez em ET e não equivale à perda de eficiência.",
        "A integral mede o excedente no intervalo 0≤Q≤Q₀. A fórmula geral de PM continua válida quando o imposto elimina as transações. A expressão quadrática em t abaixo é interior; no limiar coincide, mas acima dele superestima a perda.",
    ), (
        r"EC_t=\frac{bQ_t^2}{2},\quad EP_t=\frac{dQ_t^2}{2},\quad R_t=tQ_t",
        r"ET_t=EC_t+EP_t+R_t,\quad ET_0=EC_0+EP_0",
        r"ET(Q)=\int_0^Q[P_D(q)-P_S(q)]\,dq=(a-c)Q-\frac{b+d}{2}Q^2",
        r"PM=ET(Q_0)-ET(Q_t)=\frac{b+d}{2}(Q_0-Q_t)^2",
        r"0<t<a-c:\quad PM=\frac{t^2}{2(b+d)}",
    )),
    ("Domínios, elasticidades e casos-limite", (
        "Todos os parâmetros devem ser finitos, com a>c≥0, b,d>0 e t≥0. Quantidades são não negativas e a demanda econômica não se estende a preços negativos. No modo exploratório, P₀,Q₀>0, |ε_D,0|>0 e ε_S,0≥1.",
        "Elasticidades são pontuais no equilíbrio inicial, não constantes ao longo das curvas lineares. Inclinação não é elasticidade. Com c≥0 e P,Q positivos, a oferta não pode ter elasticidade inferior a 1; relativamente menos elástica não significa necessariamente inelástica.",
        "Imposto zero: Qₜ=Q₀ e preços válidos iguais a P₀, sem arrecadação, peso morto ou carga efetiva. Para 0<t<a−c há transações e cunha tributária efetiva.",
        "Em t≥a−c, Qₜ=0, ECₜ=EPₜ=Rₜ=ETₜ=0 e PM=ET₀; preços transacionados e incidência efetiva não se aplicam. No limiar, a e c são preços de reserva no limite, não preços negociados; acima dele, não se extrapolam identidades interiores.",
    ), (
        r"|\varepsilon_{D,0}|=\frac{P_0}{bQ_0},\quad\varepsilon_{S,0}=\frac{P_0}{dQ_0}=1+\frac{c}{dQ_0}\geq1",
        r"s_C=\frac{\varepsilon_{S,0}}{\varepsilon_{S,0}+|\varepsilon_{D,0}|},\quad s_P=\frac{|\varepsilon_{D,0}|}{\varepsilon_{S,0}+|\varepsilon_{D,0}|}",
    )),
    ("Parâmetros, unidades e convenções", (
        "a: intercepto da demanda inversa; c: intercepto da oferta inversa; ambos em R$/unidade. b: módulo da inclinação da demanda inversa; d: inclinação da oferta inversa; ambos em (R$/unidade)/(unidade por período). t: imposto específico em R$/unidade.",
        "Q em unidades por período; P, P_C e P_P em R$/unidade; excedentes, arrecadação e peso morto em R$/período. P₀ e Q₀ identificam o equilíbrio inicial. Elasticidades e parcelas são adimensionais; parcelas podem ser exibidas em porcentagem.",
        "Os números monetários são hipotéticos, sem calibração empírica. O arredondamento é só de apresentação; cálculos usam valores internos completos. Ausência de preço transacionado é não aplicável, nunca preço zero.",
    ), ()),
    ("Limitações interpretativas", (
        "Não são modelados comércio internacional, evasão, externalidades, dinâmica, poder de mercado, custos administrativos ou efeitos em outros mercados. O modelo não avalia o valor do gasto público nem consequências de financiamento.",
        "Os resultados descrevem propriedades e comparações controladas do modelo. Não são previsões nem estimativas causais de incidência tributária observada no Brasil, nem avaliação normativa completa de políticas reais.",
    ), ()),
    ("Referências e documentação", (
        "Varian & Melitz — Intermediate Microeconomics: A Modern Approach; OpenStax — Principles of Economics; Benzarti — Tax Incidence Anomalies (2025). Essas referências da antiga aba permanecem preservadas.",
        "[Arquitetura Funcional e Matemática do Módulo 01 v1.1](" + REFERENCIA + ") — referência completa das equações, hipóteses, domínios, exemplos e bibliografia do projeto.",
    ), ()),
)

MIGRACAO = (
    ("Curvas inversas", "Curvas, equilíbrio e incidência"),
    ("Equilíbrio sem imposto", "Curvas, equilíbrio e incidência"),
    ("Quantidade com imposto e cunha", "Curvas, equilíbrio e incidência"),
    ("Integral do excedente e peso morto", "Excedentes, arrecadação e perda de eficiência"),
    ("Parâmetros calculados e elasticidades", "Parâmetros do mercado selecionado (consulta somente leitura)"),
    ("Hipóteses e limitações", "Descrição e hipóteses / Limitações interpretativas"),
    ("Limitação matemática da oferta", "Domínios, elasticidades e casos-limite"),
    ("Fontes bibliográficas", "Referências e documentação"),
)

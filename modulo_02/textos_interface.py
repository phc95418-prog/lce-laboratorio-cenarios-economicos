"""Textos de navegação e apresentação; sem estado ou cálculo econômico."""

EXPERIMENTOS = {
    "A": "Decisão de produção da firma monopolista",
    "B": "Concorrência Perfeita versus Monopólio",
}

REGIOES = {
    "EC": "Excedente do consumidor (EC)",
    "EP": "Excedente do produtor (EP)",
    "DWL": "Perda de eficiência (DWL)",
    "T": "Transferência entre consumidores e produtores (T)",
    "L_C": "Parcela da perda associada aos consumidores (L_C)",
    "L_P": "Parcela da perda associada aos produtores (L_P)",
}

DESCRICOES = {
    "EC": "Excedente dos consumidores entre a demanda e o preço pago, no regime selecionado.",
    "EP": "Receita além do custo variável no regime selecionado. Não equivale necessariamente ao lucro líquido.",
    "DWL": "Excedente total não realizado no monopólio em relação à concorrência, dadas as hipóteses do modelo.",
    "T": "Excedente transferido dos consumidores aos produtores nas unidades ainda vendidas. É transferência, não perda de eficiência.",
    "L_C": "Parcela da perda de excedente dos consumidores nas unidades que deixam de ser comercializadas em monopólio.",
    "L_P": "Parcela da perda de excedente dos produtores nas unidades que deixam de ser comercializadas em monopólio.",
}

FAQ = (
    ("Como alternar entre os experimentos?",
     "Use o seletor Experimento A / Experimento B abaixo do título. Parâmetros e seleções são preservados nessa navegação; recarregar a página inicia uma nova experiência."),
    ("O que cada experimento representa?",
     "A investiga produção, receitas, custos e lucro de uma firma monopolista. B compara concorrência perfeita e monopólio sob a mesma demanda e condições produtivas agregadas equivalentes. São modelos teóricos, não previsões empíricas."),
    ("Como alterar parâmetros e quantidades?",
     "Abra Alterar variáveis. O slider atualiza gráficos e valores durante a interação; o campo numérico confirma por Enter ou perda de foco. Valores válidos entre passos são aceitos; entradas inválidas preservam o último valor válido. B ajusta apenas a, b, c e s; a importação de A é pontual e exclui CF."),
    ("Como funcionam as perspectivas?",
     "Perspectivas muda a representação da investigação. A oferece resultados totais e análise marginal; na comparação, quantidade fixa ou decisões ótimas. B oferece Comparar resultados, Entender o mecanismo e Investigar o bem-estar. A troca preserva as escolhas armazenadas."),
    ("Como ampliar ou mover um gráfico?",
     "Arraste uma região para ampliar e use Pan na barra do gráfico para deslocar a vista. Visualização oferece restauração da escala e zoom opcional pela roda. Essas ações mudam só os eixos; curvas e cálculos conservam seus domínios econômicos."),
    ("Como funciona a comparação do Experimento A?",
     "Em Ações, Fixar cenário de referência congela os parâmetros atuais. Só o cenário Atual é editável. Quantidade fixa usa a mesma Q nos dois cenários; Decisões ótimas usa o máximo de lucro próprio de cada um. O zoom começa sincronizado; Independente permite enquadramentos distintos."),
    ("O que significam as regiões de bem-estar?",
     "EC é excedente do consumidor; EP é excedente do produtor, sem equivaler automaticamente ao lucro líquido. DWL é perda de eficiência. T é transferência, não perda líquida; L_C e L_P são as parcelas da perda associadas aos consumidores e produtores. Uma única região é preenchida por vez."),
    ("Como interpretar indicadores e encontrar mais detalhes?",
     "Valores monetários são hipotéticos, em u.m. Os indicadores são resumidos; os cálculos usam precisão interna. Diferenças mostram a base de comparação, sem julgamento de ganho ou perda. Análise econômica e matemática detalha o cenário em três dimensões opcionais. Sem comércio, preços transacionados não se aplicam."),
    ("Como mudar a aparência ou exportar uma imagem?",
     "Abra Configurações para Sistema, Claro ou Escuro e para exportar PNG. Na comparação de A, escolha Referência ou Atual. A imagem é salva nos downloads do navegador. Aparência, Ajuda e exportação não alteram resultados ou referência."),
)


def perguntas_frequentes(experimento):
    """Nove dúvidas de funcionamento, com conteúdo próprio do experimento ativo."""
    graficos=FAQ[4]
    indicadores=FAQ[7]
    exportacao=(FAQ[8][0],"Abra Configurações para Sistema, Claro ou Escuro e para exportar PNG, SVG ou preparar PDF quando disponível. Na comparação de A, escolha Referência ou Atual. PDF é baixado após sua preparação; a imagem corresponde à vista capturada no pedido. Sobre o modelo está em Ações. Essas operações não alteram a investigação.")
    controles=(FAQ[2][0],"Abra Alterar variáveis: a janela pode ser movida pela barra de título ou pelas setas com a barra em foco, sem fechar para acompanhar o gráfico. O campo confirma por Enter ou perda de foco; valores entre passos são aceitos e inválidos preservam o último válido. "+("A controla Q e cinco parâmetros; a comparação edita só o Atual." if experimento=="A" else "B ajusta a, b, c e s nos dois regimes; importar de A exclui CF e não cria sincronização."))
    if experimento=="A":
        especificas=(
            ("Quais perspectivas estão disponíveis em A?","Na investigação individual: Resultados Totais e Análise Marginal. Na comparação: Quantidade fixa e Decisões ótimas. A mudança consulta os resultados sem substituir as quantidades armazenadas."),
            ("Receita máxima e lucro máximo são a mesma coisa?","Não. $Q_R$ maximiza receita; $Q_M$ maximiza lucro. Mostrar pontos ótimos apenas os revela. Ir para lucro máximo altera explicitamente Q na investigação individual, com precisão interna completa."),
            FAQ[5],
            ("Como o custo fixo afeta o lucro?","O encargo fixo inevitável desloca custo total e lucro, sem mudar custo marginal ou quantidade ótima. Lucro negativo não implica fechamento automático; A não modela entrada, saída ou ativação."),
        )
    else:
        especificas=(
            ("Quais modos estão disponíveis em B?","Comparar resultados mostra concorrência e monopólio juntos. Entender o mecanismo distingue preço e condição marginal. Investigar o bem-estar destaca uma região econômica por vez, sob os mesmos quatro parâmetros."),
            FAQ[6],
            ("Excedente do produtor é o mesmo que lucro líquido?","Não: EP desconta os custos variáveis. Sob encargos fixos agregados idênticos, a diferença de lucros entre regimes coincide com a diferença de EP, sem igualar seus níveis. B não contém controle de custo fixo nem curva de lucro."),
            ("O que significa ausência de comércio?","Quando a≤c, as quantidades de equilíbrio são zero e não há preços transacionados. Excedentes e perdas variáveis são zero; percentuais com base zero não se aplicam. Isso não prova equivalência geral entre as estruturas."),
        )
    return (FAQ[0],controles,*especificas,graficos,indicadores,exportacao)

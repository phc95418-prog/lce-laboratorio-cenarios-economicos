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

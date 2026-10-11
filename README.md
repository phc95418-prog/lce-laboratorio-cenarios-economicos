# LCE — Laboratório de Cenários Econômicos

**Módulo 01 — Incidência tributária, elasticidades e bem-estar**  
Interface v1.2 — **candidata à publicação, com investigação opcional no Experimento A**, construída sobre a Arquitetura Funcional e Matemática v1.1. A versão pública permanece na v1.1.

Projeto acadêmico independente de Pedro Henrique de Carvalho Almeida (Economia — IDP).

## O que é o LCE?

Uma plataforma interativa para explorar o efeito de um **imposto específico por unidade** em um mercado competitivo, utilizando funções inversas lineares de oferta e demanda. Exibe preços, quantidades, distribuição do imposto, arrecadação, excedentes e perda de eficiência.

Inclui três ambientes de simulação e comparação:

- **Simulação livre:** controles de parâmetros e de elasticidades, com resultados atualizados.
- **Experimento A — Quem suporta o imposto?:** variação da incidência econômica mantendo fixos o equilíbrio inicial e a distorção em quantidade.
- **Experimento B — Quanto o imposto distorce o mercado?:** comparação controlada da reação da quantidade e do peso morto às elasticidades.

Os resultados são **simulações teóricas condicionadas às hipóteses do modelo**, não estimativas empíricas nem previsões tributárias para mercados reais.

## Acessar a aplicação

https://lce-laboratorio-cenarios-economicos-kisqpqyg4huaz9os7vuplv.streamlit.app/

## Rodar localmente

Utilize preferencialmente **Python 3.13**:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

O navegador poderá abrir automaticamente em `http://localhost:8501`.

No Windows, crie um ambiente virtual exclusivo para o projeto, quando necessário:

```bat
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Não envie a pasta `.venv` para o GitHub. Ela contém arquivos específicos do computador local e não é necessária na nuvem.

## Testes

```bash
python testar_modelo.py
python testar_interface.py
python testar_investigacao.py
```

Os testes cobrem os exemplos de referência, cenários comparativos, identidades econômicas e casos-limite. Os novos testes verificam o comportamento e os textos do piloto de investigação no Experimento A.

## Arquivos principais

| Arquivo | Função |
|---|---|
| `app.py` | Interface Streamlit. Ponto de entrada da aplicação. |
| `modelo_mercado.py` | Equações, validação econômica e métricas de bem-estar. |
| `experimentos.py` | Parâmetros dos experimentos A e B. |
| `visualizacoes.py` | Gráficos em Plotly. |
| `requirements.txt` | Versões das bibliotecas necessárias. |
| `investigacao_a.py` | Perguntas, orientações e explicações progressivas do piloto A. |
| `testar_investigacao.py` | Testes de conteúdos e casos-limite do piloto A. |
| `testar_modelo.py` | Testes da matemática. |
| `testar_interface.py` | Testes dos dados dos gráficos e dos cenários. |
| `INICIAR_LCE.bat` | Atalho opcional de execução no Windows. |

## Consolidação técnica da v1.2 (após inspeção visual)

Esta candidata v1.2 foi consolidada após os testes locais do piloto. Recomenda-se fazer uma conferência rápida do pacote definitivo antes da atualização do GitHub. O núcleo matemático, os experimentos e os gráficos continuam idênticos ao piloto já testado.

- A comparação do Experimento A inicia com um convite neutro, sem antecipar a resposta.
- O painel de questões aparece antes do gráfico; a interpretação e a síntese aparecem depois da tabela e são opcionais.
- A leitura gráfica relaciona as barras às variações **atuais** de preço dos três cenários.
- A matemática avalia os coeficientes efetivos/potenciais, com exemplo numérico derivado dos parâmetros e imposto vigentes.
- O conteúdo de quantidade e arrecadação acompanha a alteração do imposto, inclusive nos casos t=0 e t=80.

Se você já executa o piloto anterior, pode simplesmente substituir **app.py**, **investigacao_a.py** e **testar_investigacao.py** na mesma pasta, sem reinstalar o Python nem as bibliotecas. Encerre primeiro o Streamlit com Ctrl+C, copie os três arquivos e execute novamente `python -m streamlit run app.py`.

## Recursos pedagógicos opcionais da v1.2

**Antes do envio ao GitHub:** confirme no Streamlit local a síntese revisada das questões 1 e 3. A versão pública v1.1 permanece preservada até a atualização do repositório.

Na aba **Comparar cenários** do **Experimento A**:

1. Abra o painel discreto **“Questões para investigar · opcional”** acima do gráfico. Escolha uma das três questões e leia o convite para explorar.
2. Altere o imposto na lateral e observe os mesmos gráficos e a tabela da v1.1. Nada fica bloqueado e não há pontuação.
3. Abaixo da tabela, abra **“Compreenda o mecanismo · opcional”** e escolha entre **Intuição**, **Leitura dos gráficos** ou **Matemática**. O texto acompanha a questão selecionada e a situação tributária.
4. Confira imposto **R$ 0**, **R$ 20** e **R$ 80** (limite proibitivo no Experimento A). A explicação não deve atribuir carga tributária efetiva quando não há imposto ou transações.
5. Confira **Experimento B** e **Exploração livre**; esses percursos não devem ter novo painel nem mudanças nos cálculos.

O núcleo econômico (`modelo_mercado.py`), os cenários (`experimentos.py`) e os gráficos (`visualizacoes.py`, incluindo a correção para pandas/Plotly) foram preservados. O piloto acrescenta apenas uma camada opcional à comparação A.

**Status dos testes neste pacote:** 10 testes de modelo, 11 testes de interface/figuras e 13 testes pedagógicos, total de **34 testes aprovados** no ambiente de preparação. A nova revisão ainda precisa de inspeção visual local no Streamlit.

## Atualizações da interface v1.1

- Formatação monetária legível nos textos explicativos em Markdown.
- Rótulos compactos nos cartões, legendas condicionais para imposto zero e sem transações.
- Explicações econômicas mais próximas dos resultados e elasticidades iniciais nas tabelas comparativas.
- Escalas comuns dos gráficos de mercado entre os cenários de um experimento, indicação de equilíbrio e valores nas barras de comparação B.
- Narrativa pedagógica em duas camadas nas comparações: conclusão econômica visível e justificativa técnica opcional.
- Contraste dos valores no gráfico do Experimento B corrigido para os temas claro e escuro.
- Texto do Experimento A ajustado para diferenciar o cenário simétrico dos casos de maior incidência em um dos lados.
- Modelo e definição dos cenários preservados; testes originais e testes de regressão ampliados.

## Publicar no Streamlit Community Cloud (após validação do piloto)

1. Criar no GitHub um repositório público, por exemplo `lce-laboratorio-cenarios-economicos`.
2. Fazer upload dos **arquivos extraídos**, mantendo `app.py`, `modelo_mercado.py`, `experimentos.py`, `visualizacoes.py` e `requirements.txt` no nível principal do repositório. Não envie o arquivo ZIP como único conteúdo, nem a pasta `.venv`.
3. Entrar em https://share.streamlit.io/ com sua conta GitHub e autorizar o acesso necessário.
4. Selecionar **Create app** > **Yup, I have an app**. Informar o repositório, a branch `main` e o ponto de entrada `app.py`.
5. Em **Advanced settings**, selecionar **Python 3.13** e salvar. Essa é a versão usada localmente pelo projeto.
6. Escolher, se disponível, o endereço desejado e clicar em **Deploy**. Aguardar a instalação automática das bibliotecas.
7. Abrir o endereço `*.streamlit.app` gerado e conferir simulação livre e experimentos A e B.
8. Conferir a aplicação após o deploy e comparar os cenários A e B.

O Streamlit Community Cloud acompanha o repositório e republica novas versões quando os arquivos são atualizados no GitHub.

Documentação oficial: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Notas metodológicas

Modelo estático de equilíbrio parcial competitivo, bem homogêneo, curvas lineares, preços tomados como dados por agentes e imposto por unidade comercializada. As métricas de bem-estar dependem de pressupostos adicionais, descritos na especificação acadêmica do Módulo 01. A incidência econômica é distinta da obrigação legal de recolhimento. O modelo não contempla efeitos-renda relevantes, externalidades, dinâmica, evasão, mercados com poder de mercado nem uso da receita pelo governo.


## Ajustes da candidata final

- A síntese de incidência utiliza **parcela percentual do imposto**, evitando confundir percentuais com valores monetários por unidade.
- A síntese sobre aumento do imposto informa o valor atual da arrecadação e do peso morto e os relaciona à receita máxima no desenho controlado do Experimento A.
- Foram acrescentados testes de regressão das sínteses (inclusive com imposto de R$ 60,00 e limite proibitivo).
- A v1.2 continua restrita à comparação do Experimento A; sem alterações no núcleo econômico ou no Experimento B.

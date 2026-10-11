# LCE — Laboratório de Cenários Econômicos

**Módulo 01 — Incidência tributária, elasticidades e bem-estar**  
Interface v1.1, construída sobre a Arquitetura Funcional e Matemática v1.1.

Projeto acadêmico independente de Pedro Henrique de Carvalho Almeida (Economia — IDP).

## O que é o LCE?

Uma plataforma interativa para explorar o efeito de um **imposto específico por unidade** em um mercado competitivo, utilizando funções inversas lineares de oferta e demanda. Exibe preços, quantidades, distribuição do imposto, arrecadação, excedentes e perda de eficiência.

Inclui três ambientes de investigação:

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
```

Os testes cobrem os exemplos de referência, cenários comparativos, identidades econômicas e casos-limite.

## Arquivos principais

| Arquivo | Função |
|---|---|
| `app.py` | Interface Streamlit. Ponto de entrada da aplicação. |
| `modelo_mercado.py` | Equações, validação econômica e métricas de bem-estar. |
| `experimentos.py` | Parâmetros dos experimentos A e B. |
| `visualizacoes.py` | Gráficos em Plotly. |
| `requirements.txt` | Versões das bibliotecas necessárias. |
| `testar_modelo.py` | Testes da matemática. |
| `testar_interface.py` | Testes dos dados dos gráficos e dos cenários. |
| `INICIAR_LCE.bat` | Atalho opcional de execução no Windows. |

## Atualizações da interface v1.1

- Formatação monetária legível nos textos explicativos em Markdown.
- Rótulos compactos nos cartões, legendas condicionais para imposto zero e sem transações.
- Explicações econômicas mais próximas dos resultados e elasticidades iniciais nas tabelas comparativas.
- Escalas comuns dos gráficos de mercado entre os cenários de um experimento, indicação de equilíbrio e valores nas barras de comparação B.
- Narrativa pedagógica em duas camadas nas comparações: conclusão econômica visível e justificativa técnica opcional.
- Contraste dos valores no gráfico do Experimento B corrigido para os temas claro e escuro.
- Texto do Experimento A ajustado para diferenciar o cenário simétrico dos casos de maior incidência em um dos lados.
- Modelo e definição dos cenários preservados; testes originais e testes de regressão ampliados.

## Publicar no Streamlit Community Cloud

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

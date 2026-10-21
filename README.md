# LCE — Laboratório de Cenários Econômicos

O **Laboratório de Cenários Econômicos (LCE)** é uma plataforma acadêmica interativa voltada ao estudo da Economia por meio da experimentação.

Seu propósito é transformar modelos econômicos tradicionalmente apresentados por equações e gráficos estáticos em ambientes nos quais o usuário pode modificar parâmetros, observar o comportamento das curvas e dos indicadores e investigar relações de causa e efeito.

Organizado em módulos temáticos, o LCE busca facilitar a compreensão não apenas de **o que acontece** quando determinadas condições econômicas mudam, mas também de **por que essas mudanças ocorrem**.

A plataforma utiliza modelos teóricos com hipóteses explícitas, permitindo explorar diferentes cenários e relacionar seus resultados às estruturas matemáticas e aos conceitos econômicos correspondentes.

**Acesse a aplicação:**

[**Abrir o Laboratório de Cenários Econômicos — LCE**](https://lce-laboratorio-cenarios-economicos-kisqpqyg4huaz9os7vuplv.streamlit.app/)

**Versão estável atual:** [LCE v2.0.0 — Módulos 01 e 02 integrados](https://github.com/phc95418-prog/lce-laboratorio-cenarios-economicos/releases/tag/v2.0.0)

Projeto acadêmico independente de Pedro Henrique de Carvalho Almeida (Economia — IDP).

---

## 1. Organização do laboratório

O LCE está organizado em módulos dedicados a diferentes problemas econômicos. Cada módulo combina modelos matemáticos, representações gráficas interativas, indicadores econômicos e ambientes de investigação.

A aplicação integrada permite navegar entre os módulos, preservar parâmetros de investigação e explorar diferentes situações sem precisar reiniciar a plataforma.

Atualmente, o laboratório conta com dois módulos.

### Módulo 01 — Incidência Tributária, Elasticidades e Bem-Estar

Investiga os efeitos de um imposto específico por unidade em mercados competitivos, utilizando modelos de oferta e demanda lineares.

O módulo permite observar como a tributação modifica os preços pagos pelos consumidores, os preços recebidos pelos produtores, as quantidades transacionadas, a arrecadação governamental e os excedentes econômicos.

Está organizado em três ambientes:

- **Exploração livre:** permite modificar parâmetros das curvas ou elasticidades e observar os equilíbrios de mercado antes e depois da introdução do imposto.
- **Experimento A — Quem suporta o imposto?:** investiga como diferentes condições de oferta e demanda afetam a distribuição do ônus tributário entre consumidores e produtores.
- **Experimento B — Quanto o imposto distorce o mercado?:** compara mercados com diferentes sensibilidades da quantidade e analisa os efeitos da tributação sobre transações, arrecadação e perda de eficiência.

O objetivo é compreender como as características do mercado influenciam tanto a distribuição do imposto quanto suas consequências para o bem-estar econômico.

### Módulo 02 — Decisões da Firma e Estruturas de Mercado

Investiga decisões de produção e suas consequências econômicas, considerando relações entre demanda, receita, custos, lucro e organização dos mercados.

O módulo contém dois experimentos:

- **Experimento A — Decisões da firma:** permite analisar receita, custos, lucro e decisões de produção. O usuário pode modificar parâmetros, examinar diferentes objetivos e comparar os resultados obtidos.
- **Experimento B — Concorrência e monopólio:** compara resultados de mercados competitivos e monopolistas, destacando diferenças de preços, quantidades, excedentes econômicos e eficiência.

O objetivo é compreender como as decisões econômicas dependem das condições de demanda, da estrutura de custos e da organização do mercado.

---

## 2. Como funciona a investigação

A proposta do LCE é permitir que o usuário participe ativamente da construção e da interpretação dos cenários econômicos.

Em vez de apresentar apenas o resultado de um modelo, a plataforma permite explorar o processo pelo qual esse resultado é determinado.

As principais possibilidades são:

1. **Modificar parâmetros:** alterar características econômicas e observar como essas mudanças afetam o comportamento do modelo.
2. **Visualizar resultados:** acompanhar curvas, equilíbrios, indicadores e outras representações gráficas.
3. **Comparar cenários:** identificar diferenças entre situações econômicas e investigar suas causas.
4. **Relacionar matemática e economia:** consultar expressões, propriedades e interpretações dos resultados.
5. **Investigar hipóteses e limites:** compreender as condições sob as quais as conclusões do modelo são válidas.

### Análise econômica e matemática

Os experimentos disponibilizam recursos de interpretação organizados em três perspectivas complementares:

- **Leitura econômica:** interpretação dos resultados e dos mecanismos envolvidos.
- **Estrutura matemática:** apresentação das relações e expressões que sustentam o modelo.
- **Propriedades e limites:** discussão das hipóteses, condições de validade e limitações das conclusões.

A plataforma também oferece recursos de ajuda contextual e informações sobre os modelos utilizados.

### Exportação de gráficos

Os gráficos podem ser exportados nos formatos **PNG, SVG e PDF**, permitindo sua utilização em estudos, apresentações e materiais acadêmicos.

Os três formatos foram validados na aplicação de homologação hospedada, e o funcionamento dos downloads foi confirmado preliminarmente na aplicação oficial.

A geração de PDF utiliza Chromium no servidor.

---

## 3. Acesso à aplicação

A versão pública do LCE está disponível no Streamlit Community Cloud:

**[Acessar o LCE](https://lce-laboratorio-cenarios-economicos-kisqpqyg4huaz9os7vuplv.streamlit.app/)**

A aplicação utiliza:

- **Repositório:** `phc95418-prog/lce-laboratorio-cenarios-economicos`
- **Branch:** `main`
- **Arquivo principal:** `lce_integrado.py`
- **Python:** 3.13
- **Versão estável:** `v2.0.0`

Não é necessário instalar o projeto para utilizar a versão hospedada. Basta acessar o endereço pelo navegador.

---

## 4. Execução local

Para executar o LCE localmente, utilize Python 3.13 e execute os comandos a partir da pasta raiz do repositório.

### Windows

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run lce_integrado.py
```

### Linux ou macOS

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run lce_integrado.py
```

O endereço local padrão é:

`http://localhost:8501`

Os módulos também podem ser executados separadamente durante o desenvolvimento:

- `app.py` — Módulo 01.
- `lce_modulo02.py` — Módulo 02.
- `lce_integrado.py` — Aplicação integrada.

A pasta `.venv` contém o ambiente virtual local e não é versionada no Git.

---

## 5. Organização técnica

O projeto foi desenvolvido em Python, utilizando Streamlit para a interface e Plotly para as visualizações gráficas interativas.

Seus principais arquivos e componentes são:

| Caminho | Função |
|---|---|
| `lce_integrado.py` | Entrada da aplicação integrada e navegação entre os módulos. |
| `app.py` | Entrada independente do Módulo 01. |
| `modelo_mercado.py`, `experimentos.py` e `visualizacoes.py` | Modelos, experimentos e representações gráficas do Módulo 01. |
| `analise_modulo01.py` e arquivos auxiliares do Módulo 01 | Análises e recursos de interface. |
| `lce_modulo02.py` | Entrada independente do Módulo 02. |
| `modulo_02/` | Componentes econômicos, matemáticos e de interface do Módulo 02. |
| `requirements.txt` | Dependências Python do projeto. |
| `packages.txt` | Provisionamento do Chromium para exportações em PDF na hospedagem Linux. |

Os recursos JavaScript e CSS utilizados pela interface estão incluídos no próprio repositório.

O projeto também contém testes automatizados e materiais de validação utilizados durante o desenvolvimento dos módulos e de sua integração.

### Implantação

A aplicação oficial é executada no Streamlit Community Cloud a partir da branch `main`, utilizando `lce_integrado.py` como arquivo principal.

As dependências Python são declaradas em `requirements.txt`, enquanto `packages.txt` solicita a instalação de Chromium no ambiente hospedado.

Para informações adicionais sobre a plataforma, consulte a [documentação do Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

---

## 6. Alcance e limitações dos modelos

O LCE utiliza modelos teóricos de Economia com hipóteses explícitas. Seus resultados representam consequências matemáticas e econômicas dessas hipóteses e dos parâmetros definidos pelo usuário.

**As simulações não constituem previsões de mercados reais nem estimativas empíricas.**

O Módulo 01 utiliza modelos estáticos de equilíbrio parcial, com curvas lineares de oferta e demanda, bem homogêneo e tributação específica por unidade.

A interpretação dos excedentes econômicos como medidas de bem-estar depende de condições teóricas que devem ser consideradas na análise dos resultados.

O Módulo 02 utiliza funções de demanda e custos especificadas para investigar decisões da firma e comparar estruturas de mercado.

Os modelos não incorporam necessariamente elementos como dinâmica intertemporal, heterogeneidade ampla entre agentes, externalidades ou calibração com dados observados.

Essas simplificações permitem isolar mecanismos econômicos e facilitar sua compreensão, mas também delimitam o alcance das conclusões.

Para aprofundamento das hipóteses e dos fundamentos matemáticos do Módulo 01, consulte a [Arquitetura Funcional e Matemática v1.1](https://docs.google.com/document/d/1-1l1HtqIrwz6G9piHSg244UXDW0aAUzhfTf9vQIf07A/edit).

---

## 7. Versões do projeto

### v2.0.0 — Módulos 01 e 02 integrados

Primeira versão oficial com os dois módulos reunidos em uma única aplicação.

Inclui a modernização do Módulo 01, a implementação do Módulo 02, a integração da navegação, os recursos de análise econômica e matemática e a exportação de gráficos.

[Consultar a release v2.0.0](https://github.com/phc95418-prog/lce-laboratorio-cenarios-economicos/releases/tag/v2.0.0)

### v1.2.1 — Módulo 01

Versão histórica anterior à integração, preservada para consulta e recuperação do código.

[Consultar a release v1.2.1](https://github.com/phc95418-prog/lce-laboratorio-cenarios-economicos/releases/tag/v1.2.1)

---

## 8. Perspectiva de desenvolvimento

O LCE é um projeto acadêmico em evolução.

O desenvolvimento de novos módulos e o aprimoramento dos existentes poderão ampliar os problemas econômicos investigados, aprofundar as possibilidades de comparação e incorporar novas formas de exploração dos modelos.

A orientação central do projeto permanece a mesma: **utilizar a experimentação para transformar relações matemáticas em mecanismos econômicos que possam ser observados, investigados e compreendidos.**

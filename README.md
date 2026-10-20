# LCE — Laboratório de Cenários Econômicos

O LCE é um laboratório acadêmico interativo para investigar mecanismos econômicos com modelos teóricos e cenários controlados. A aplicação integrada reúne dois módulos, com navegação visível entre eles e estados de investigação próprios.

**Estado das versões:** esta branch contém a aplicação integrada em desenvolvimento, validada localmente e ainda não publicada. A [aplicação pública atual](https://lce-laboratorio-cenarios-economicos-kisqpqyg4huaz9os7vuplv.streamlit.app/) corresponde à versão estável anterior do Módulo 01 (v1.2.1); seu endereço não é uma demonstração da integração.

Projeto acadêmico independente de Pedro Henrique de Carvalho Almeida (Economia — IDP).

## Módulos e investigação

**Módulo 01 — Incidência Tributária, Elasticidades e Bem-Estar.** Explora um imposto específico por unidade em mercados competitivos com oferta e demanda inversas lineares. Apresenta preços, quantidades, elasticidades iniciais, arrecadação, excedentes e perda de eficiência. Seus três ambientes são:

- **Exploração livre:** altera parâmetros das curvas ou elasticidades e compara o equilíbrio sem e com imposto no mercado selecionado.
- **Experimento A — Quem suporta o imposto?:** compara três mercados com repartições tributárias diferentes sob condições controladas.
- **Experimento B — Quanto o imposto distorce o mercado?:** compara três sensibilidades da quantidade e as respectivas distorções.

**Módulo 02 — Decisões da Firma e Estruturas de Mercado.** O Experimento A permite investigar individualmente receita, custos, lucro, decisões de produção e comparação de cenários. O Experimento B compara concorrência e monopólio, incluindo excedentes, transferência e perda de eficiência. Ambos preservam seus controles e perspectivas próprios.

O seletor da aplicação integrada alterna entre os módulos; os seletores de ambiente e experimento permanecem dentro de cada módulo. Os resultados são acompanhados por uma síntese econômica visível e pela seção opcional **Análise econômica e matemática**, com Leitura econômica, Estrutura matemática e Propriedades e limites. Ajuda, aparência e informações sobre os modelos ficam nos controles da interface.

Os gráficos disponíveis no contexto vigente podem ser exportados em **PNG, SVG ou PDF**. A geração de PDF depende de Chrome/Chromium no servidor. Ela foi validada localmente, mas ainda precisa ser confirmada no Streamlit Community Cloud; se o navegador não estiver disponível, PNG e SVG continuam acessíveis.

## Execução local

Use Python 3.13 e execute os comandos a partir da raiz do repositório. No Windows:

~~~powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run lce_integrado.py
~~~

Em Linux ou macOS, com Python 3.13 disponível:

~~~sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run lce_integrado.py
~~~

O endereço local padrão é http://localhost:8501. Para executar os módulos separadamente durante o desenvolvimento, use <code>app.py</code> para o Módulo 01 ou <code>lce_modulo02.py</code> para o Módulo 02 no lugar de <code>lce_integrado.py</code>. A pasta <code>.venv</code> é local e está excluída do Git.

## Organização e dependências

| Caminho | Papel |
|---|---|
| <code>lce_integrado.py</code> | Ponto de entrada da aplicação integrada e seleção dos módulos. |
| <code>app.py</code>, <code>modelo_mercado.py</code>, <code>experimentos.py</code>, <code>visualizacoes.py</code> | Interface, motor, cenários e gráficos do Módulo 01. |
| <code>analise_modulo01.py</code> e arquivos <code>*modulo01*</code> | Análises, recursos de interface e exportação do Módulo 01. |
| <code>lce_modulo02.py</code> e <code>modulo_02/</code> | Entrada independente, motor, estados, gráficos e interface do Módulo 02. |
| <code>requirements.txt</code> | Dependências Python: Streamlit, Plotly e pandas. |
| <code>packages.txt</code> | Solicitação de instalação de Chromium para PDF na hospedagem Linux. |

Os componentes JavaScript e CSS usados pela interface estão no próprio repositório. A aplicação não requer um servidor auxiliar iniciado manualmente. Os testes versionados estão nos arquivos <code>testar_*.py</code> e <code>testar_*.mjs</code>; a regressão integrada foi executada localmente em etapa anterior.

## Preparação para publicação futura

Ao criar ou configurar **uma futura aplicação integrada** no Streamlit Community Cloud, selecionar explicitamente o repositório e a branch aprovados, <code>lce_integrado.py</code> como arquivo principal e Python 3.13. O serviço lê <code>requirements.txt</code> e <code>packages.txt</code> da raiz. Essa configuração não altera por si só a aplicação pública anterior; qualquer integração à branch pública ou troca de entrypoint exige decisão própria.

Após a implantação, conferir abertura dos dois módulos, navegação e estados, gráficos, temas, exportações PNG/SVG e uma geração real de PDF. Para PDF, verificar também os logs de instalação do Chromium e a presença de um arquivo baixado e legível. A preparação local não comprova o funcionamento em Linux hospedado. Consulte a [documentação de implantação do Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Alcance dos modelos

Os resultados são simulações teóricas condicionadas a hipóteses explícitas, não estimativas empíricas nem previsões de mercados reais. O Módulo 01 usa equilíbrio parcial estático, curvas lineares, bem homogêneo e imposto por unidade; a leitura dos excedentes requer as condições de bem-estar descritas na [Arquitetura Funcional e Matemática v1.1](https://docs.google.com/document/d/1-1l1HtqIrwz6G9piHSg244UXDW0aAUzhfTf9vQIf07A/edit). O Módulo 02 trabalha com demanda inversa linear e custos especificados para comparar decisões da firma e estruturas de mercado. Os modelos não incorporam, por exemplo, dinâmica, heterogeneidade ampla, externalidades ou calibração com dados observados.

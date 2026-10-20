// Adaptador isolado para os dois controles nativos do Streamlit 1.65.
// Preserva os handlers e a navegação por teclado do framework, sem estado React.
export default function() {
  const alterados = new Map();
  function identificar(selector, rotulo, texto) {
    const botao = document.querySelector(selector);
    if (!botao) return;
    if (!alterados.has(botao)) alterados.set(botao, {
      aria:botao.getAttribute('aria-label'), title:botao.getAttribute('title'),
    });
    if (botao.getAttribute('aria-label') !== rotulo) botao.setAttribute('aria-label',rotulo);
    if (botao.getAttribute('title') !== rotulo) botao.setAttribute('title',rotulo);
    if (texto && !botao.querySelector('[data-lce-acoes]')) {
      const legenda = document.createElement('span');
      legenda.dataset.lceAcoes = ''; legenda.textContent = 'Ações';
      botao.appendChild(legenda);
    }
  }
  function atualizar() {
    identificar('[data-testid="stExpandSidebarButton"]','Abrir ações do experimento',true);
    identificar('[data-testid="stSidebarCollapseButton"] button','Fechar ações do experimento',false);
  }
  atualizar();
  const observador = new MutationObserver(atualizar);
  observador.observe(document.body,{childList:true,subtree:true});
  return () => {
    observador.disconnect();
    for (const [botao, anterior] of alterados) {
      for (const [atributo, valor] of [['aria-label',anterior.aria],['title',anterior.title]]) {
        if (valor === null) botao.removeAttribute(atributo); else botao.setAttribute(atributo,valor);
      }
      botao.querySelector('[data-lce-acoes]')?.remove();
    }
  };
}

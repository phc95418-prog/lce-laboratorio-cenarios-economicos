// Adaptador de UI do Streamlit 1.65/Plotly: usa apenas cliques em controles
// nativos existentes. Não acessa React, armazenamento ou estado econômico.
export function opcaoAparencia(elementos, modo) {
  const nomes = {sistema:['System','Sistema'],claro:['Light','Claro'],escuro:['Dark','Escuro']};
  return [...elementos].find(el=>nomes[modo]?.some(nome=>el.textContent.trim().endsWith(nome)));
}

export default function({parentElement,data}) {
  let root = parentElement.querySelector('.lce-configuracoes');
  if (!root) {
    root = document.createElement('section');root.className='lce-configuracoes';
    parentElement.appendChild(root);
  }
  root.innerHTML='<p><strong>Aparência</strong></p><div class="botoes" role="group" aria-label="Aparência">'+
    '<button type="button" data-tema="sistema">Sistema</button><button type="button" data-tema="claro">Claro</button>'+
    '<button type="button" data-tema="escuro">Escuro</button></div>'+
    '<p><strong>Exportar gráfico como imagem</strong></p><div class="botoes exportar"></div>'+
    '<p role="status" aria-live="polite" class="status"></p>';
  const status=root.querySelector('.status');
  let observador, prazo;
  function encerrarEspera() {observador?.disconnect();clearTimeout(prazo);}
  function aplicar(modo,rotulo) {
    encerrarEspera();
    const menu=document.querySelector('button[aria-label="Main menu"]');
    if (!menu) {status.textContent='Aparência indisponível: menu nativo não encontrado.';return;}
    function escolher() {
      const opcao=opcaoAparencia(document.querySelectorAll('[role="menuitemradio"]'),modo);
      if (!opcao) return false;
      encerrarEspera();opcao.click();
      if(menu.getAttribute('aria-expanded')==='true') menu.click();
      status.textContent='Aparência aplicada: '+rotulo+'.';return true;
    }
    observador=new MutationObserver(escolher);
    observador.observe(document.body,{childList:true,subtree:true});
    if(menu.getAttribute('aria-expanded')!=='true') menu.click();
    if (!escolher()) prazo=setTimeout(()=>{
      encerrarEspera();status.textContent='Não foi possível acessar as opções nativas de aparência. Nenhum tema foi aplicado por este controle.';
    },2500);
  }
  for(const b of root.querySelectorAll('[data-tema]')) b.onclick=()=>aplicar(b.dataset.tema,b.textContent);
  const alvos=data.comparacao ? [
    ['Referência','.lce-pares .referencia'],['Atual','.lce-pares .atual'],
  ] : [['Individual','[data-testid="stPlotlyChart"]']];
  for(const [nome,seletor] of alvos) {
    const b=document.createElement('button');b.type='button';b.textContent='Exportar '+nome+' · PNG';
    b.onclick=()=>{
      const grafico=document.querySelector(seletor);
      const comando=grafico?.querySelector('[aria-label="Download plot as a PNG"], [data-title="Download plot as a PNG"]');
      if(!comando) {status.textContent='Exportação indisponível: aguarde o gráfico terminar de renderizar.';return;}
      comando.click();status.textContent='Exportação de '+nome+' solicitada ao Plotly. Verifique o arquivo nos downloads do navegador.';
    };
    root.querySelector('.exportar').appendChild(b);
  }
  return encerrarEspera;
}

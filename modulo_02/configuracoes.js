// Adaptador de UI do Streamlit 1.65/Plotly: usa apenas cliques em controles
// nativos existentes. Não acessa React, armazenamento ou estado econômico.
export function opcaoAparencia(elementos, modo) {
  const nomes = {sistema:['System','Sistema'],claro:['Light','Claro'],escuro:['Dark','Escuro']};
  return [...elementos].find(el=>nomes[modo]?.some(nome=>el.textContent.trim().endsWith(nome)));
}

export function svgDoDataURL(uri) {
  if(!uri.startsWith('data:image/svg+xml')) throw new Error('O Plotly não retornou SVG.');
  const [cabecalho,...partes]=uri.split(',');const conteudo=partes.join(',');
  return cabecalho.includes(';base64')?new TextDecoder().decode(Uint8Array.from(atob(conteudo),c=>c.charCodeAt(0))):decodeURIComponent(conteudo);
}

export default function({parentElement,data,setStateValue}) {
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
    ['Referência','.lce-pares .referencia','lce-experimento-a-referencia'],['Atual','.lce-pares .atual','lce-experimento-a-atual'],
  ] : [[data.experimento==='B'?'Experimento B':'Individual','[data-testid="stPlotlyChart"]',data.experimento==='B'?'lce-experimento-b':'lce-experimento-a-individual']];
  for(const [nome,seletor,arquivo] of alvos) {
    const b=document.createElement('button');b.type='button';b.textContent='Exportar '+nome+' · PNG';
    b.onclick=()=>{
      const grafico=document.querySelector(seletor);
      const comando=grafico?.querySelector('[aria-label="Download plot as a PNG"], [data-title="Download plot as a PNG"]');
      if(!comando) {status.textContent='Exportação indisponível: aguarde o gráfico terminar de renderizar.';return;}
      comando.click();status.textContent='Exportação de '+nome+' solicitada ao Plotly. Verifique o arquivo nos downloads do navegador.';
    };
    root.querySelector('.exportar').appendChild(b);
    for(const formato of ['SVG','PDF']) {
      const botao=document.createElement('button');botao.type='button';
      botao.textContent=(formato==='PDF'?'Preparar ':'Exportar ')+nome+' · '+formato;
      botao.disabled=data.interacao || (formato==='PDF'&&!data.pdf_disponivel);
      botao.onclick=async()=>{
        botao.disabled=true;
        try {
          const container=document.querySelector(seletor);
          const plot=container?.matches('.js-plotly-plot')?container:container?.querySelector('.js-plotly-plot');
          if(!plot) throw new Error('Aguarde o gráfico terminar de renderizar.');
          const svg=svgDoDataURL(await window.Plotly.toImage(plot,{format:'svg'}));
          if(formato==='SVG') {
            const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml;charset=utf-8'}));
            const link=document.createElement('a');link.href=url;link.download=arquivo+'.svg';link.click();
            setTimeout(()=>URL.revokeObjectURL(url),1000);
            status.textContent='Download SVG de '+nome+' solicitado. Verifique os downloads do navegador.';
          } else {
            root.seq=(root.seq||0)+1;
            status.textContent='Preparando PDF de '+nome+'. Aguarde o botão Baixar PDF preparado.';
            setStateValue('exportacao',{seq:root.seq,svg,arquivo,contexto:data.contexto});
          }
        } catch(erro) {status.textContent='Exportação não concluída: '+erro.message;}
        finally {botao.disabled=false;}
      };
      root.querySelector('.exportar').appendChild(botao);
    }
  }
  if(data.pdf_pronto) status.textContent='PDF pronto: '+data.pdf_pronto+'. Use Baixar PDF preparado abaixo.';
  if(!data.pdf_disponivel) status.textContent='PDF indisponível neste ambiente: requer Chrome/Chromium instalado no servidor. PNG e SVG permanecem disponíveis.';
  return encerrarEspera;
}

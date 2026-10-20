// Adaptador visual do M01 para as opções NATIVAS do Streamlit 1.65.
// Não lê/grava estado econômico, armazenamento, React nem configurações globais.
// O menu original permanece disponível. Falhas são anunciadas, nunca simuladas.
export function opcaoAparencia(elementos, modo) {
  const nomes={sistema:['System','Sistema'],claro:['Light','Claro'],escuro:['Dark','Escuro']};
  return [...elementos].find(el=>nomes[modo]?.some(n=>el.textContent.trim().endsWith(n)));
}

export default function({parentElement}) {
  // Preservar os nós de estilo que o Streamlit injeta no parentElement.
  let root=parentElement.querySelector('.lce-m01-aparencia');
  if(!root){root=document.createElement('section');root.className='lce-m01-aparencia';parentElement.appendChild(root);}
  root.innerHTML='<div role="group" aria-label="Aparência">'+
    '<button type="button" data-tema="sistema">Sistema</button>'+
    '<button type="button" data-tema="claro">Claro</button>'+
    '<button type="button" data-tema="escuro">Escuro</button></div>'+
    '<p role="status" aria-live="polite"></p>';
  const status=root.querySelector('[role="status"]');
  let observador,prazo;
  function limpar(){observador?.disconnect();clearTimeout(prazo);}
  function aplicar(modo,rotulo){
    limpar();
    const menu=document.querySelector('button[aria-label="Main menu"]');
    if(!menu){status.textContent='Aparência indisponível: menu nativo não encontrado. Nenhum tema aplicado.';return;}
    function escolher(){
      const opcao=opcaoAparencia(document.querySelectorAll('[role="menuitemradio"]'),modo);
      if(!opcao)return false;
      limpar();opcao.click();
      if(menu.getAttribute('aria-expanded')==='true')menu.click();
      status.textContent='Aparência solicitada ao Streamlit: '+rotulo+'.';return true;
    }
    observador=new MutationObserver(escolher);
    observador.observe(document.body,{childList:true,subtree:true});
    if(menu.getAttribute('aria-expanded')!=='true')menu.click();
    if(!escolher())prazo=setTimeout(()=>{
      limpar();status.textContent='Não foi possível acessar a aparência nativa. Nenhum tema aplicado por este controle; utilize o menu original do Streamlit.';
    },2500);
  }
  for(const b of root.querySelectorAll('[data-tema]'))b.onclick=()=>aplicar(b.dataset.tema,b.textContent);
  return limpar;
}

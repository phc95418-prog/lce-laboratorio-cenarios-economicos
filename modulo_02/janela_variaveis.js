export function limitarJanela(x,y,w,h,vw,vh) {
  return {x:Math.max(8,Math.min(x,Math.max(8,vw-w-8))),
          y:Math.max(8,Math.min(y,Math.max(8,vh-h-8)))};
}

export function posicaoArraste(inicio,e) {
  return !inicio||inicio.id!==e.pointerId?null:
    {x:inicio.base.x+e.clientX-inicio.x,y:inicio.base.y+e.clientY-inicio.y};
}

export function registrarEvento(pendentes,evento) {
  pendentes.set(evento.campo,evento);
  return [...pendentes.values()].sort((a,b)=>a.ordem-b.ordem);
}

export default function({parentElement,data,setStateValue}) {
  let root=parentElement.querySelector('.lce-janela-raiz');
  if (!root) {
    root=document.createElement('section');root.className='lce-janela-raiz';
    root.innerHTML=`<button class="abrir" type="button" aria-expanded="false"><span aria-hidden="true">☷</span> Alterar variáveis</button>
      <section class="janela" role="dialog" aria-modal="false" aria-label="Alterar variáveis" hidden>
      <header><button class="mover" type="button" aria-label="Mover janela Alterar variáveis — use as setas">⠿ Alterar variáveis</button>
      <button class="fechar" type="button" aria-label="Fechar janela Alterar variáveis">×</button></header>
      <div class="corpo"><p class="instrucoes">Arraste a barra de título ou use as setas quando ela estiver em foco. Escape fecha.</p>
      <p class="descricao"></p><div class="campos"></div></div></section>`;
    parentElement.appendChild(root);
  }
  const painel=root.querySelector('.janela'),abrir=root.querySelector('.abrir');
  const mover=root.querySelector('.mover'),fechar=root.querySelector('.fechar');
  const campos=root.querySelector('.campos');
  root.querySelector('.descricao').textContent=data.descricao||'';
  const posicionar=()=>{
    if(painel.hidden) return;
    const r=painel.getBoundingClientRect();
    const p=limitarJanela(root.pos?.x??innerWidth-r.width-24,root.pos?.y??180,
      r.width,r.height,innerWidth,innerHeight);
    root.pos=p;painel.style.left=p.x+'px';painel.style.top=p.y+'px';
    painel.dataset.x=String(p.x);painel.dataset.y=String(p.y);
  };
  const fecharJanela=()=>{painel.hidden=true;abrir.setAttribute('aria-expanded','false');abrir.focus();};
  abrir.onclick=()=>{
    if(!painel.hidden) {fecharJanela();return;}
    painel.hidden=false;abrir.setAttribute('aria-expanded','true');posicionar();mover.focus();
  };
  fechar.onclick=fecharJanela;
  const limpezas=[];
  const grupos=new Map();
  root.pendentes??=new Map();root.ordem??=0;
  for(const item of data.campos) {
    if((root.pendentes.get(item.campo)?.seq??Infinity)<=item.seq) root.pendentes.delete(item.campo);
    let destino=campos;
    if(item.grupo) {
      let grupo=grupos.get(item.grupo)||[...campos.querySelectorAll('details')].find(e=>e.dataset.grupo===item.grupo);
      if(!grupo) {
        grupo=document.createElement('details');grupo.dataset.grupo=item.grupo;
        const titulo=document.createElement('summary');titulo.textContent=item.grupo;grupo.appendChild(titulo);campos.appendChild(grupo);
      }
      grupos.set(item.grupo,grupo);destino=grupo;grupo.ontoggle=posicionar;
    }
    let slot=[...destino.children].find(e=>e.dataset?.campo===item.campo);
    if(!slot) {slot=document.createElement('div');slot.dataset.campo=item.campo;destino.appendChild(slot);}
    limpezas.push(renderizarControle({parentElement:slot,data:item,
      setStateValue:(_,evento)=>{
        const atual={...evento,campo:item.campo,ordem:++root.ordem};
        setStateValue('evento',{...atual,lote:registrarEvento(root.pendentes,atual)});
      }}));
  }
  // Campos podem desaparecer ao alternar Quantidade fixa/Decisões ótimas.
  const ativos=new Set(data.campos.map(c=>c.campo));
  for(const slot of campos.querySelectorAll('[data-campo]')) if(!ativos.has(slot.dataset.campo)) slot.remove();
  const down=e=>{
    if(e.button!==0) return;
    e.preventDefault();posicionar();root.gesto={id:e.pointerId,x:e.clientX,y:e.clientY,base:{...root.pos}};
    mover.setPointerCapture(e.pointerId);
  };
  const move=e=>{
    const nova=posicaoArraste(root.gesto,e);
    if(!nova) return;
    root.pos=nova;posicionar();
  };
  const fim=()=>{root.gesto=null;};
  const tecla=e=>{
    const passos={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
    if(e.key==='Home') {e.preventDefault();root.pos=null;posicionar();return;}
    if(!passos[e.key]) return;
    e.preventDefault();const passo=e.shiftKey?48:16;posicionar();
    root.pos={x:root.pos.x+passos[e.key][0]*passo,y:root.pos.y+passos[e.key][1]*passo};posicionar();
  };
  const escape=e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();fecharJanela();}};
  const handlers=[[mover,'pointerdown',down],[mover,'pointermove',move],[mover,'pointerup',fim],
    [mover,'pointercancel',fim],[mover,'lostpointercapture',fim],[mover,'keydown',tecla],[painel,'keydown',escape]];
  handlers.forEach(([el,n,f])=>el.addEventListener(n,f));
  window.addEventListener('resize',posicionar);
  posicionar();
  return ()=>{handlers.forEach(([el,n,f])=>el.removeEventListener(n,f));
    window.removeEventListener('resize',posicionar);limpezas.forEach(f=>f?.());};
}

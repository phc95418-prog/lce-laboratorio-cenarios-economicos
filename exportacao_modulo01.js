// Plotly.toImage + download de Blob, adaptados do mecanismo existente no M02.
// Seletores e figuras vêm do catálogo explícito do M01. Nenhuma busca pelo
// primeiro gráfico da página; a figura exibida nunca é alterada.
export function svgDoDataURL(uri) {
  if(!uri.startsWith('data:image/svg+xml'))throw Error('O Plotly não retornou SVG.');
  const [cabecalho,...partes]=uri.split(',');const conteudo=partes.join(',');
  return cabecalho.includes(';base64')?new TextDecoder().decode(Uint8Array.from(atob(conteudo),c=>c.charCodeAt(0))):decodeURIComponent(conteudo);
}
export function escapar(texto){return texto.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');}
export function linhas(texto,limite=95){
  const saida=[''];
  for(const palavra of texto.split(' ')){
    const i=saida.length-1;
    if(saida[i].length && saida[i].length+1+palavra.length>limite)saida.push(palavra);
    else saida[i]+=(saida[i]?' ':'')+palavra;
  }
  return saida;
}
export default function({parentElement,data,setStateValue}){
  let root=parentElement.querySelector('.lce-m01-exportacao');
  if(!root){root=document.createElement('section');root.className='lce-m01-exportacao';parentElement.appendChild(root);}
  const anterior=root.querySelector('select[data-campo=alvo]')?.value;
  const formatoAnterior=root.querySelector('select[data-campo=formato]')?.value;
  root.contexto=data.contexto;
  root.innerHTML='<label>Gráfico a exportar<select data-campo="alvo" aria-label="Gráfico a exportar"></select></label>'+
    '<label>Formato<select data-campo="formato" aria-label="Formato de exportação"></select></label>'+
    '<button type="button">Exportar gráfico</button><p role="status" aria-live="polite"></p>';
  const alvo=root.querySelector('[data-campo=alvo]'),formato=root.querySelector('[data-campo=formato]');
  const status=root.querySelector('[role=status]'),botao=root.querySelector('button');
  for(const item of data.alvos){const opt=document.createElement('option');opt.value=item.id;opt.textContent=item.id+' · '+item.titulo;alvo.appendChild(opt);}
  for(const nome of data.formatos){const opt=document.createElement('option');opt.value=nome;opt.textContent=nome;formato.appendChild(opt);}
  if(data.alvos.some(a=>a.id===anterior))alvo.value=anterior;
  if(data.formatos.includes(formatoAnterior))formato.value=formatoAnterior;
  botao.onclick=async()=>{
    const item=data.alvos.find(a=>a.id===alvo.value),tipo=formato.value,contexto=data.contexto;
    if(!item||!data.formatos.includes(tipo)){status.textContent='Seleção de exportação inválida.';return;}
    botao.disabled=true;let copia;
    try{
      // Dados, anotações e curvas vêm sempre do rerun corrente. Do gráfico
      // montado aproveitamos somente o enquadramento; nunca dados possivelmente
      // antigos durante uma atualização. Abas ainda não visitadas também funcionam.
      const container=document.querySelector(item.seletor);
      const vivo=container?.querySelector('.js-plotly-plot');
      const figura=JSON.parse(JSON.stringify(item.figura));
      for(const eixo of ['xaxis','yaxis']){
        if(vivo?.layout?.[eixo]?.range && vivo.layout[eixo].autorange===false){
          figura.layout[eixo]={...figura.layout[eixo],range:[...vivo.layout[eixo].range],autorange:false};
        }
      }
      const fundo=getComputedStyle(document.querySelector('.stApp')).backgroundColor;
      const cor=getComputedStyle(document.querySelector('.st-key-lce_m01_root')).color;
      const cabecalho=[item.titulo,...linhas(item.contexto),...linhas(item.nota)];
      const extra=24*cabecalho.length+24;
      const layout={...figura.layout,
        width:1100,height:(figura.layout.height||440)+extra,
        paper_bgcolor:fundo,plot_bgcolor:fundo,
        font:{...figura.layout.font,color:cor},
        margin:{...figura.layout.margin,t:(figura.layout.margin?.t||22)+extra},
        title:{text:cabecalho.map(escapar).join('<br>'),x:.02,xanchor:'left',y:1,yanchor:'top',pad:{t:24},font:{size:14,color:cor}},
      };
      for(const traco of figura.data)if(traco.mode?.includes('text'))traco.textfont={...traco.textfont,color:cor};
      copia=document.createElement('div');
      copia.style.cssText='position:fixed;left:-100000px;top:0;width:1100px;pointer-events:none';
      document.body.appendChild(copia);
      await window.Plotly.newPlot(copia,figura.data,layout,{staticPlot:true,displayModeBar:false});
      const uri=await window.Plotly.toImage(copia,{format:tipo==='PDF'?'svg':tipo.toLowerCase(),width:layout.width,height:layout.height,scale:tipo==='PNG'?2:1});
      if(!root.isConnected||root.contexto!==contexto)throw Error('O cenário mudou. Solicite a exportação novamente.');
      if(tipo==='PDF'){
        setStateValue('pedido_pdf',{seq:Date.now(),contexto,id:item.id,arquivo:item.arquivo,svg:svgDoDataURL(uri)});
        status.textContent='PDF solicitado. Aguarde o botão Baixar PDF preparado.';
        return;
      }
      let blob;
      if(tipo==='SVG')blob=new Blob([svgDoDataURL(uri)],{type:'image/svg+xml;charset=utf-8'});
      else {const bytes=Uint8Array.from(atob(uri.split(',')[1]),c=>c.charCodeAt(0));blob=new Blob([bytes],{type:'image/png'});}
      const url=URL.createObjectURL(blob),link=document.createElement('a');
      link.href=url;link.download=item.arquivo+'.'+tipo.toLowerCase();link.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
      status.textContent='Download '+tipo+' solicitado: '+link.download+'. Verifique os downloads do navegador.';
    }catch(erro){status.textContent='Exportação não concluída: '+erro.message;}
    finally{if(copia){window.Plotly.purge(copia);copia.remove();}botao.disabled=false;}
  };
}

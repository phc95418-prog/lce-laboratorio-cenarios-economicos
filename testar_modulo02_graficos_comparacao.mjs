// Transformações de visualização: independentes do motor e sem dependências.
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
const source = await readFile(new URL('./modulo_02/graficos_comparacao.js',import.meta.url),'utf8');
const {limitesRelayout,aparenciaTema,vistasPreservadas,renderizarVista} = await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const base={xaxis:{range:[0,100]},yaxis:{range:[-8000,8000]}};
const zoom={xaxis:{range:[70,90]},yaxis:{range:[2000,6000]}};
test('arraste transfere exatamente ambos os eixos e não autorange',()=>{
  const r=limitesRelayout({'xaxis.range[0]':70},zoom,base);
  assert.deepEqual(r,{'xaxis.range':[70,90],'yaxis.range':[2000,6000],
    'xaxis.autorange':false,'yaxis.autorange':false});
});
test('deslocamento transfere limites Y mesmo sem mudança de X',()=>{
  assert.deepEqual(limitesRelayout({'yaxis.range':[2000,6000]},zoom,base)['yaxis.range'],[2000,6000]);
});
test('restauração nativa restaura a escala comum original',()=>{
  const r=limitesRelayout({'xaxis.autorange':true},zoom,base);
  assert.deepEqual(r['xaxis.range'],[0,100]);assert.deepEqual(r['yaxis.range'],[-8000,8000]);
});
test('resize e mudança de ferramenta não alteram escalas',()=>{
  for(const event of [{autosize:true},{dragmode:'pan'},{width:800}])
    assert.equal(limitesRelayout(event,zoom,base),null);
});
test('limites são copiados sem mutar a figura ou a base',()=>{
  const r=limitesRelayout({'xaxis.range':[70,90]},zoom,base);
  r['xaxis.range'][0]=0;
  assert.equal(zoom.xaxis.range[0],70);assert.equal(base.xaxis.range[0],0);
});
test('tema usa cores reais sem incluir alterações de escala ou domínio',()=>{
  for (const [fundo,texto,escuro] of [
    ['rgb(255, 255, 255)','rgb(49, 51, 63)',false],
    ['rgb(14, 17, 23)','rgb(250, 250, 250)',true],
  ]) {
    const t=aparenciaTema(fundo,texto);
    assert.equal(t.escuro,escuro);
    assert.equal(t.paper_bgcolor,fundo);assert.equal(t.plot_bgcolor,fundo);
    assert.equal(t['font.color'],texto);
    assert.ok(Object.keys(t).every(k=>!/range|autorange|minallowed|maxallowed/.test(k)));
  }
});
test('sincronizado conserva a mesma vista ao renderizar novos resultados',()=>{
  assert.deepEqual(vistasPreservadas('base','base',true,true,zoom,[null,null]),[zoom,zoom]);
});
test('entrada em independente parte do enquadramento compartilhado',()=>{
  assert.deepEqual(vistasPreservadas('base','base',true,false,zoom,[null,null]),[zoom,zoom]);
});
test('independente preserva separadamente ambos os eixos de cada gráfico',()=>{
  const a={xaxis:{range:[0,10]},yaxis:{range:[-20,20]}};
  const b={xaxis:{range:[70,80]},yaxis:{range:[1000,2000]}};
  assert.deepEqual(vistasPreservadas('base','base',false,false,null,[a,b]),[a,b]);
});
test('retorno ao sincronizado recupera a base comum original',()=>{
  assert.deepEqual(vistasPreservadas('base','base',false,true,null,[zoom,base]),[null,null]);
});
test('mudança de domínio, foco ou restauração invalida enquadramentos antigos',()=>{
  for(const modo of [true,false])
    assert.deepEqual(vistasPreservadas('antiga','nova',modo,modo,zoom,[zoom,base]),[null,null]);
});
test('primeiro enquadramento é comum e sem resíduos de comparação anterior',()=>{
  assert.deepEqual(vistasPreservadas(undefined,'nova',undefined,true,null,null),[null,null]);
});
test('restauração mantém snapshot de eixos quando Plotly.react muta layout',async()=>{
  const layout={xaxis:{range:[0,100]},yaxis:{range:[-8000,8000]}};
  let aplicado;
  const plotly={
    react:async(plot,dados,l)=>{l.xaxis.range[0]=20;l.xaxis.range[1]=50;l.yaxis.range=[0,1000];},
    relayout:async(plot,limites)=>{aplicado=limites;},
  };
  await renderizarVista(plotly,{},[],layout,{});
  assert.deepEqual(aplicado['xaxis.range'],[0,100]);
  assert.deepEqual(aplicado['yaxis.range'],[-8000,8000]);
});

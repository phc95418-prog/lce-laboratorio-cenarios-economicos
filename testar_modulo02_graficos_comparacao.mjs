// Transformações de visualização: independentes do motor e sem dependências.
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
const source = await readFile(new URL('./modulo_02/graficos_comparacao.js',import.meta.url),'utf8');
const {limitesRelayout} = await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
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

import {readFile} from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
async function modulo(nome){const s=await readFile(new URL('./modulo_02/'+nome,import.meta.url),'utf8');return import('data:text/javascript;base64,'+Buffer.from(s).toString('base64'));}
const {limitarJanela,posicaoArraste,registrarEvento}=await modulo('janela_variaveis.js');
const {criarFilaLive}=await modulo('controles_individual.js');
const {svgDoDataURL}=await modulo('configuracoes.js');

test('janela permanece integralmente no viewport',()=>{
  assert.deepEqual(limitarJanela(-200,2000,400,600,1440,1000),{x:8,y:392});
  assert.deepEqual(limitarJanela(900,900,400,600,460,700),{x:52,y:92});
});
test('arraste usa deslocamento sem modificar o objeto de origem',()=>{
  const inicio={id:7,x:100,y:200,base:{x:630,y:180}};
  assert.deepEqual(posicaoArraste(inicio,{pointerId:7,clientX:150,clientY:120}),{x:680,y:100});
  assert.deepEqual(inicio.base,{x:630,y:180});
});
test('ponteiro diferente ou gesto encerrado não move a janela',()=>{
  assert.equal(posicaoArraste(null,{pointerId:7}),null);
  assert.equal(posicaoArraste({id:8},{pointerId:7}),null);
});
test('lote preserva campos distintos e ordem da última edição',()=>{
  const mapa=new Map();registrarEvento(mapa,{campo:'a',seq:1,ordem:1,valor:120});
  registrarEvento(mapa,{campo:'b',seq:1,ordem:2,valor:1.1537});
  const lote=registrarEvento(mapa,{campo:'a',seq:2,ordem:3,valor:130});
  assert.deepEqual(lote.map(e=>[e.campo,e.valor]),[['b',1.1537],['a',130]]);
});
function fila(){let tempo=0,id=0;const frames=new Map(),eventos=[];
  const f=criarFilaLive(v=>eventos.push(v),cb=>{frames.set(++id,cb);return id;},i=>frames.delete(i),()=>tempo);
  return {f,eventos,passo(t){tempo=t;const callbacks=[...frames.values()];frames.clear();callbacks.forEach(cb=>cb());}};
}
test('primeiro live é imediato e intermediários são agrupados',()=>{
  const s=fila();s.f.live(10);s.f.live(20);s.f.live(30);
  assert.deepEqual(s.eventos,[10]);s.passo(49);assert.deepEqual(s.eventos,[10]);
  s.passo(50);assert.deepEqual(s.eventos,[10,30]);
});
test('fim descarta intermediário pendente sem emissão tardia',()=>{
  const s=fila();s.f.live(10);s.f.live(30);s.f.descartar();s.passo(100);
  assert.deepEqual(s.eventos,[10]);s.f.live(40);assert.deepEqual(s.eventos,[10,40]);
});
test('rajada de cem valores conserva o último sem cem envios',()=>{
  const s=fila();for(let n=0;n<100;n++)s.f.live(n);
  s.passo(100);assert.deepEqual(s.eventos,[0,99]);
});
test('SVG URI e base64 preservam conteúdo e rejeitam outro formato',()=>{
  const svg='<svg width="700" height="420"><text>Preço, quantidade</text></svg>';
  assert.equal(svgDoDataURL('data:image/svg+xml,'+encodeURIComponent(svg)),svg);
  assert.equal(svgDoDataURL('data:image/svg+xml;base64,'+Buffer.from(svg).toString('base64')),svg);
  assert.throws(()=>svgDoDataURL('data:image/png;base64,xyz'));
});

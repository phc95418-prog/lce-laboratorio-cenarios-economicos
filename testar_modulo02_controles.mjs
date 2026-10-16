// Contratos de eventos da integração de produção; sem dependências externas.
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
const source = await readFile(new URL('./modulo_02/controles_individual.js',import.meta.url),'utf8');
const {default:render} = await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));

class Element extends EventTarget {
  constructor(){super();this.dataset={};this.nodes=new Map();this.attrs=new Map();this.value='';this.textContent='';}
  querySelector(s){if(!this.nodes.has(s))this.nodes.set(s,new Element());return this.nodes.get(s);}
  setAttribute(k,v){this.attrs.set(k,String(v));}
  appendChild(node){this.root=node;}
}
function setup(){
  const parent=new Element();parent.querySelector=()=>parent.root??null;
  globalThis.document={createElement:()=>new Element()};
  const events=[];
  const c={parentElement:parent,data:{seq:0,valor:25,minimo:0,maximo:100,passo:.1,campo:'q',rotulo:'Q',erro:''},setStateValue:(k,v)=>events.push(v)};
  render(c);
  const node=s=>parent.root.querySelector(s);
  const fire=(s,type,key)=>{const e=new Event(type);if(key)Object.defineProperty(e,'key',{value:key});node(s).dispatchEvent(e);};
  return {c,parent,events,node,fire};
}

test('rerender e ótimo programático não quantizam nem emitem eventos',()=>{
  const s=setup();s.c.data.valor=80/3;
  for(let i=0;i<10;i++)render(s.c);
  assert.equal(Number(s.node('.campo').value.replace(',','.')),80/3);
  assert.equal(s.events.length,0);
});
test('não duplica assinaturas de eventos depois de rerenders',()=>{
  const s=setup();for(let i=0;i<12;i++)render(s.c);
  s.fire('.slider','pointerdown');s.node('.slider').value='60';s.fire('.slider','input');s.fire('.slider','pointerup');
  assert.deepEqual(s.events.map(e=>e.fase),['live','fim']);
});
test('rascunho permanece separado até Enter',()=>{
  const s=setup();s.fire('.campo','focus');s.node('.campo').value='26,67';s.fire('.campo','input');
  assert.equal(s.events.length,0);assert.equal(s.parent.root.value,25);
  s.fire('.campo','keydown','Enter');assert.equal(s.parent.root.value,26.67);
  assert.equal(s.events[0].fase,'campo');s.fire('.campo','blur');assert.equal(s.events.length,1);
});
test('perda de foco aceita precisão fora da grade',()=>{
  const s=setup();s.c.data={...s.c.data,campo:'b',minimo:.5,maximo:2,valor:1};render(s.c);
  s.fire('.campo','focus');s.node('.campo').value='1,1537';s.fire('.campo','input');s.fire('.campo','blur');
  assert.equal(s.parent.root.value,1.1537);assert.equal(s.events[0].texto,'1,1537');
});
test('inválidos mantêm valor e emitem aviso acessível',()=>{
  const s=setup();
  for(const text of ['', '26,', 'abc', '101']){
    s.fire('.campo','focus');s.node('.campo').value=text;s.fire('.campo','input');s.fire('.campo','keydown','Enter');
    assert.equal(s.parent.root.value,25);assert.match(s.node('.aviso').textContent,/rejeitada/);
    assert.match(s.node('.aviso').textContent,/Erro:.*Último valor válido preservado/);
    assert.equal(s.node('.campo').attrs.get('aria-invalid'),'true');
  }
});
test('erro confirmado pelo servidor mantém contexto e some após correção válida',()=>{
  const s=setup();s.c.data.erro='Valor fora da faixa permitida.';render(s.c);
  assert.match(s.node('.aviso').textContent,/Erro:.*fora da faixa.*Último valor válido preservado/);
  assert.equal(s.parent.root.value,25);
  s.fire('.campo','focus');s.node('.campo').value='26,67';s.fire('.campo','input');s.fire('.campo','keydown','Enter');
  assert.equal(s.node('.aviso').textContent,'');
  assert.equal(s.node('.campo').attrs.get('aria-invalid'),'false');
  assert.equal(s.parent.root.value,26.67);
});
test('rerender preserva rascunho e ignora confirmação atrasada',()=>{
  const s=setup();s.fire('.campo','focus');s.node('.campo').value='26,';s.fire('.campo','input');render(s.c);
  assert.equal(s.node('.campo').value,'26,');
  s.fire('.campo','blur');s.fire('.slider','pointerdown');s.node('.slider').value='40';s.fire('.slider','input');
  render(s.c);assert.equal(s.parent.root.value,40);assert.equal(s.node('.campo').value,'40');
});
test('gesto envia vários live e um único fim mesmo com perda de captura',()=>{
  const s=setup();s.fire('.slider','pointerdown');
  for(const v of [30,40,50]){s.node('.slider').value=String(v);s.fire('.slider','input');}
  s.fire('.slider','pointerup');s.fire('.slider','lostpointercapture');
  assert.deepEqual(s.events.map(e=>e.fase),['live','live','live','fim']);
  assert.equal(s.events.at(-1).valor,50);
});
test('teclado altera explicitamente e consolida no keyup',()=>{
  const s=setup();s.fire('.slider','keydown','ArrowRight');s.fire('.slider','keyup');
  assert.equal(s.parent.root.value,25.1);assert.deepEqual(s.events.map(e=>e.fase),['live','fim']);
  s.fire('.slider','keydown','End');s.fire('.slider','keyup');assert.equal(s.parent.root.value,100);
});

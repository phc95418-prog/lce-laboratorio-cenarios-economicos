import {readFile} from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
const source=await readFile(new URL('./aparencia_modulo01.js',import.meta.url),'utf8');
const {default:montar,opcaoAparencia}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('três opções nativas em inglês',()=>{
  const elementos=['contrast System','light_mode Light','dark_mode Dark'].map(textContent=>({textContent}));
  for(const [i,modo] of ['sistema','claro','escuro'].entries())assert.equal(opcaoAparencia(elementos,modo),elementos[i]);
});
test('opções nativas em português',()=>{
  for(const [modo,textContent] of [['sistema','Sistema'],['claro','Claro'],['escuro','Escuro']]){
    const el={textContent};assert.equal(opcaoAparencia([el],modo),el);
  }
});
test('ausência ou opção inválida não simula sucesso',()=>{
  assert.equal(opcaoAparencia([],'claro'),undefined);
  assert.equal(opcaoAparencia([{textContent:'Clear cache'}],'claro'),undefined);
  assert.equal(opcaoAparencia([{textContent:'Dark'}],'invalido'),undefined);
});
test('montagem preserva estilos fornecidos pelo framework',()=>{
  const estilo={tagName:'STYLE'};
  const parentElement={children:[estilo],querySelector:()=>null,
    appendChild(el){this.children.push(el);},replaceChildren(){throw Error('Estilo removido');}};
  const root={querySelector:()=>({textContent:''}),querySelectorAll:()=>[]};
  const anterior=globalThis.document;
  try{
    globalThis.document={createElement:()=>root};
    const limpar=montar({parentElement});
    assert.equal(parentElement.children[0],estilo);
    assert.equal(parentElement.children[1],root);
    limpar();
  }finally{if(anterior===undefined)delete globalThis.document;else globalThis.document=anterior;}
});

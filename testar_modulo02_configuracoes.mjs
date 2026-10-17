import {readFile} from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
const source=await readFile(new URL('./modulo_02/configuracoes.js',import.meta.url),'utf8');
const {opcaoAparencia}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('seleciona opção de tema nativo pelo nome, sem confundir ícone e texto',()=>{
  const opcoes=['contrast System','light_mode Light','dark_mode Dark'].map(textContent=>({textContent}));
  assert.equal(opcaoAparencia(opcoes,'sistema'),opcoes[0]);
  assert.equal(opcaoAparencia(opcoes,'claro'),opcoes[1]);
  assert.equal(opcaoAparencia(opcoes,'escuro'),opcoes[2]);
});
test('menu ausente ou desconhecido não simula aplicação de aparência',()=>{
  assert.equal(opcaoAparencia([],'claro'),undefined);
  assert.equal(opcaoAparencia([{textContent:'Clear cache'}],'claro'),undefined);
  assert.equal(opcaoAparencia([{textContent:'Dark'}],'invalido'),undefined);
});
test('nomes em português também são reconhecidos',()=>{
  for(const [modo,textContent] of [['sistema','Sistema'],['claro','Claro'],['escuro','Escuro']]) {
    const opcao={textContent};assert.equal(opcaoAparencia([opcao],modo),opcao);
  }
});

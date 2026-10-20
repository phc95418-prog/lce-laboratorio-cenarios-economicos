import {readFile} from 'node:fs/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
const source=await readFile(new URL('./exportacao_modulo01.js',import.meta.url),'utf8');
const {svgDoDataURL,escapar,linhas}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('SVG UTF-8 em URI e base64 preserva unidades e acentos',()=>{
  const svg='<svg><text>Arrecadação · R$ 600</text></svg>';
  assert.equal(svgDoDataURL('data:image/svg+xml,'+encodeURIComponent(svg)),svg);
  assert.equal(svgDoDataURL('data:image/svg+xml;base64,'+Buffer.from(svg).toString('base64')),svg);
});
test('não aceita imagem de outro formato como SVG',()=>assert.throws(()=>svgDoDataURL('data:image/png;base64,AAA')));
test('cabeçalho escapa marcação e preserva texto econômico',()=>assert.equal(escapar('0<t & Q>0'),'0&lt;t &amp; Q&gt;0'));
test('quebra de linha preserva palavras e conteúdo integral',()=>{
  const texto='Sem transações, preços negociados ou carga efetiva: B1. Com transações: B2 e B3.';
  const partes=linhas(texto,35);
  assert.equal(partes.join(' '),texto);
  assert.ok(partes.every(p=>p.length<=35));
});

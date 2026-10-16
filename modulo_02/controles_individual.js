// Componente de produção: edição com buffer e eventos; cálculos só no Python.
export default function(component) {
  const {parentElement, data, setStateValue} = component;
  let root = parentElement.querySelector('.lce-controle');
  if (!root) {
    root = document.createElement('section');
    root.className = 'lce-controle';
    root.innerHTML = `<label class="rotulo"></label><div class="entradas">
      <input class="slider" type="range" step="any">
      <input class="campo" type="text" inputmode="decimal" autocomplete="off" spellcheck="false">
      </div><p class="aviso" role="alert" aria-live="assertive"></p>`;
    parentElement.appendChild(root);
    root.seq = 0;
    root.active = false;
    root.editing = false;
    root.dirty = false;
    root.trace = [];
  }
  if (root.detachHandlers) root.detachHandlers();
  const range = root.querySelector('.slider');
  const input = root.querySelector('.campo');
  const notice = root.querySelector('.aviso');
  const apresentarErro = texto => {
    notice.textContent = texto ? `⚠ Erro: ${texto} Último valor válido preservado.` : '';
  };
  const label = root.querySelector('.rotulo');
  const represent = v => String(v).replace('.', ',');
  label.textContent = data.rotulo;
  input.id = 'lce-campo-' + data.campo;
  label.htmlFor = input.id;
  range.setAttribute('aria-label', data.rotulo + ' — slider');
  input.setAttribute('aria-label', data.rotulo + ' — campo');
  input.setAttribute('aria-describedby', 'lce-aviso-' + data.campo);
  notice.id = 'lce-aviso-' + data.campo;
  range.min = String(data.minimo);
  range.max = String(data.maximo);
  const trace = (fase, valor) => {
    root.trace.push({fase, valor, pressionado:root.active, seq:root.seq});
    if (root.trace.length > 60) root.trace.shift();
    root.dataset.eventos = JSON.stringify(root.trace);
  };
  const present = v => {
    root.value = v;
    root.dataset.value = String(v);
    range.setAttribute('aria-valuetext', represent(v));
  };
  // Acknowledgements podem chegar enquanto o ponteiro permanece pressionado.
  // Não reescrever rascunho, gesto atual ou sequência mais nova do navegador.
  if (data.seq >= root.seq) {
    root.seq = data.seq;
    root.dataset.confirmadoServidor = String(data.valor);
    trace('servidor', data.valor);
    if (!root.active && !root.keyboard) {
      present(data.valor);
      range.value = String(data.valor);
      if (!root.editing || !root.dirty) input.value = represent(data.valor);
    }
    apresentarErro(data.erro);
    input.setAttribute('aria-invalid', data.erro ? 'true' : 'false');
  }
  if (root.value === undefined) {
    present(data.valor);
    range.value = String(data.valor);
    input.value = represent(data.valor);
  }
  const send = payload => {
    root.seq += 1;
    setStateValue('evento', {...payload, seq:root.seq});
  };
  const live = () => {
    const valor = Math.min(data.maximo, Math.max(data.minimo,
      Number((Math.round(Number(range.value)/data.passo)*data.passo).toPrecision(15))));
    present(valor);
    range.value = String(valor);
    input.value = represent(valor);
    root.dirty = false;
    notice.textContent = '';
    input.setAttribute('aria-invalid','false');
    trace('live',valor);
    send({fase:'live',valor});
  };
  const finish = () => {
    if (!root.active && !root.keyboard) return;
    root.active = false;
    root.keyboard = false;
    trace('fim',root.value);
    send({fase:'fim',valor:root.value});
  };
  const commit = () => {
    if (!root.dirty) return;
    root.dirty = false;
    const texto = input.value.trim();
    const completo = /^[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)(?:[eE][+-]?\d+)?$/.test(texto);
    const valor = completo ? Number(texto.replace(',', '.')) : NaN;
    if (!Number.isFinite(valor) || valor < data.minimo || valor > data.maximo) {
      apresentarErro(`Entrada rejeitada. Use um número completo entre ${represent(data.minimo)} e ${represent(data.maximo)}.`);
      input.setAttribute('aria-invalid','true');
      trace('invalido',root.value);
      send({fase:'invalido',texto});
      return;
    }
    present(valor);
    range.value = String(valor);
    input.value = represent(valor);
    notice.textContent = '';
    input.setAttribute('aria-invalid','false');
    trace('campo',valor);
    send({fase:'campo',texto});
  };
  const down = e => {root.active = true; range.setPointerCapture?.(e.pointerId);};
  const keydown = e => {
    if (!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End','PageUp','PageDown'].includes(e.key)) return;
    e.preventDefault();
    root.keyboard = true;
    const direction = ['ArrowRight','ArrowUp','PageUp'].includes(e.key) ? 1 : -1;
    let v = root.value + direction*data.passo*(e.key.startsWith('Page') ? 10 : 1);
    if (e.key === 'Home') v = data.minimo;
    if (e.key === 'End') v = data.maximo;
    range.value = String(Math.min(data.maximo,Math.max(data.minimo,v)));
    live();
  };
  const focus = () => {root.editing = true;};
  const edit = () => {root.dirty = true;};
  const blur = () => {root.editing = false;commit();};
  const enter = e => {if(e.key === 'Enter'){e.preventDefault();commit();}};
  const handlers = [[range,'input',live],[range,'pointerdown',down],
    [range,'pointerup',finish],[range,'pointercancel',finish],[range,'lostpointercapture',finish],
    [range,'keydown',keydown],[range,'keyup',finish],[range,'blur',finish],
    [input,'focus',focus],[input,'input',edit],[input,'blur',blur],[input,'keydown',enter]];
  handlers.forEach(([el,event,fn])=>el.addEventListener(event,fn));
  const detach = () => handlers.forEach(([el,event,fn])=>el.removeEventListener(event,fn));
  root.detachHandlers = detach;
  return () => {detach(); if(root.detachHandlers === detach) root.detachHandlers = null;};
}

// Componente experimental P-04: somente eventos públicos do Plotly.js.
const EXPECTED = '3.7.0';
const loadPlotly = () => {
  if (window.Plotly?.version === EXPECTED) return Promise.resolve(window.Plotly);
  if (!window.__m03_plotly_load) {
    window.__m03_plotly_load = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'app/static/m03_plotly_3_7_0.min.js';
      script.onload = () => window.Plotly?.version === EXPECTED
        ? resolve(window.Plotly) : reject(new Error('Versão inesperada de Plotly.js: ' + window.Plotly?.version));
      script.onerror = () => reject(new Error('Plotly.js local indisponível; inicie com --server.enableStaticServing true'));
      document.head.appendChild(script);
    });
  }
  return window.__m03_plotly_load;
};

export default function(component) {
  const {parentElement, data, setTriggerValue} = component;
  const root = parentElement.querySelector('.m03-plot');
  let disposed = false;
  loadPlotly().then(async Plotly => {
    if (disposed) return;
    const layout = structuredClone(data.layout);
    const view = data.view || {x: layout.xaxis.range.slice(), y: layout.yaxis.range.slice()};
    layout.xaxis.range = view.x.slice();
    layout.yaxis.range = view.y.slice();
    Plotly.purge(root);
    root.replaceChildren();
    await Plotly.newPlot(root, data.traces, layout,
      {responsive: true, scrollZoom: true, displayModeBar: true, displaylogo: false});
    if (disposed) return;
    root.dataset.plotlyVersion = Plotly.version;
    let current = view;
    root.on('plotly_click', event => {
      if (data.clickTargets) {
        const point = event.points?.find(p => data.clickTargets[String(p.curveNumber)]);
        const target = point && data.clickTargets[String(point.curveNumber)];
        if (target) setTriggerValue('clicked', {target, id: Date.now()});
        return;
      }
      const x = Number(event.xvals?.[0]);
      const y = Number(event.yvals?.[0]);
      if (Number.isFinite(x) && Number.isFinite(y)) {
        const payload = {x: String(x), y: String(y), id: Date.now()};
        root.dataset.lastClick = JSON.stringify(payload);
        setTriggerValue('clicked', payload);
      }
    });
    root.on('plotly_relayout', event => {
      if (event['xaxis.autorange'] || event['yaxis.autorange']) {
        setTriggerValue('view_event', {view: null, id: Date.now()});
        return;
      }
      const next = {x: current.x.slice(), y: current.y.slice()};
      for (const axis of ['xaxis', 'yaxis']) {
        const target = axis === 'xaxis' ? next.x : next.y;
        if (Array.isArray(event[axis + '.range'])) {
          target[0] = event[axis + '.range'][0];
          target[1] = event[axis + '.range'][1];
        }
        for (const i of [0, 1]) {
          const value = event[axis + '.range[' + i + ']'];
          if (value !== undefined) target[i] = value;
        }
      }
      if (JSON.stringify(next) !== JSON.stringify(current)) {
        current = next;
        root.dataset.lastView = JSON.stringify(next);
        setTriggerValue('view_event', {view: next, id: Date.now()});
      }
    });
  }).catch(error => { root.textContent = error.message; });
  return () => {
    disposed = true;
    if (window.Plotly?.version === EXPECTED) window.Plotly.purge(root);
  };
}

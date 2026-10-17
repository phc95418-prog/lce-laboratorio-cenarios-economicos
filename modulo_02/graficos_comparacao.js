// Apenas apresentação: nenhum parâmetro, quantidade ou resultado é emitido.
export function limitesRelayout(evento, layout, base) {
  if (!Object.keys(evento).some(k => /^(xaxis|yaxis)\.(range|autorange)/.test(k))) return null;
  const restaurar = evento['xaxis.autorange'] === true || evento['yaxis.autorange'] === true;
  return {
    'xaxis.range': [...(restaurar ? base.xaxis.range : layout.xaxis.range)],
    'yaxis.range': [...(restaurar ? base.yaxis.range : layout.yaxis.range)],
    'xaxis.autorange': false, 'yaxis.autorange': false,
  };
}

export function aparenciaTema(fundo, texto) {
  const rgb = (fundo.match(/[\d.]+/g) || []).slice(0,3).map(Number);
  const escuro = rgb.length === 3 && rgb.reduce((a,b)=>a+b,0)/3 < 128;
  return {paper_bgcolor:fundo,plot_bgcolor:fundo,'font.color':texto,
    'xaxis.color':texto,'yaxis.color':texto,
    'xaxis.gridcolor':escuro?'#475569':'#dce2eb',
    'yaxis.gridcolor':escuro?'#475569':'#dce2eb',
    'legend.bgcolor':fundo,escuro};
}

const CORES_ESCURAS = {'#145da0':'#70b7ff','#a84b0a':'#ffba75','#087858':'#65d9af'};

export function vistasPreservadas(contextoAntes, contextoAgora, antesSincrono, agoraSincrono, comum, individuais) {
  // Retornar a Sincronizado ou restaurar/foco/parâmetros recupera a base comum.
  if (contextoAntes !== contextoAgora || (!antesSincrono && agoraSincrono)) return [null,null];
  return agoraSincrono || antesSincrono ? [comum,comum] : (individuais || [null,null]);
}

export async function renderizarVista(Plotly, plot, dados, layout, config) {
  // react pode mutar seu argumento ao preservar uma vista pela uirevision.
  // Snapshot anterior evita transformar a vista do usuário na base restaurada.
  const limites = limitesRelayout({'xaxis.autorange':true},layout,layout);
  await Plotly.react(plot,dados,layout,config);
  await Plotly.relayout(plot,limites);
}

export default function({parentElement, data}) {
  let root = parentElement.querySelector('.lce-pares');
  if (!root) {
    root = document.createElement('section');
    root.className = 'lce-pares';
    root.setAttribute('aria-label','Gráficos comparativos com escalas sincronizadas');
    root.innerHTML = '<div class="painel"><h3>Referência</h3><div class="grafico referencia"></div></div>' +
      '<div class="painel"><h3>Atual</h3><div class="grafico atual"></div></div>' +
      '<p class="situacao" role="status" aria-live="polite"></p>';
    parentElement.appendChild(root);
  }
  const token = {};
  root.token = token;
  const sincronizado = data.sincronizado !== false;
  root.setAttribute('aria-label',sincronizado ? 'Gráficos comparativos com escalas sincronizadas' :
    'Gráficos comparativos com enquadramentos independentes');
  const plots = [root.querySelector('.referencia'),root.querySelector('.atual')];
  const status = root.querySelector('.situacao');
  const figures = data.figuras.map(f => JSON.parse(f));
  let observer;
  let temaObserver;
  const handlers = [];
  const Plotly = window.Plotly;
  const app = parentElement.closest('[data-testid="stApp"]') || document.body;
  function temaAtual() {
    const estilo = getComputedStyle(app);
    return aparenciaTema(estilo.backgroundColor,estilo.color);
  }
  let tema = temaAtual();
  function cores(t) {
    return figures.map(f=>f.data.map(traco=>{
      const cor = traco.line?.color || traco.marker?.color;
      return t.escuro ? (CORES_ESCURAS[cor] || cor) : cor;
    }));
  }
  const colorir = async t => {
    const paletas = cores(t);
    await Promise.all(plots.map(async (plot,i)=>{
      const {escuro,...layout} = t;
      await Plotly.relayout(plot,layout);
      await Plotly.restyle(plot,{'line.color':paletas[i],'marker.color':paletas[i],
        'marker.line.color':t['font.color'],'marker.line.width':1.5});
    }));
  };
  root.work = (root.work || Promise.resolve()).then(async () => {
    if (root.token !== token) return;
    root.syncing = true;
    const preservar = vistasPreservadas(root.contexto,data.contexto,root.sincronizado,
      sincronizado,root.limites,root.individuais);
    const config = {displaylogo:false, responsive:true, scrollZoom:data.roda,
      displayModeBar:true, doubleClick:'reset',
      modeBarButtonsToRemove:['select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d']};
    for (let i=0;i<2;i++) {
      const layout = {...figures[i].layout, autosize:true,
        uirevision:String(figures[i].layout.uirevision)+':'+sincronizado};
      if (preservar[i]) {
        layout.xaxis = {...layout.xaxis,range:[...preservar[i]['xaxis.range']],autorange:false};
        layout.yaxis = {...layout.yaxis,range:[...preservar[i]['yaxis.range']],autorange:false};
      }
      await renderizarVista(Plotly,plots[i],figures[i].data,layout,{...config,
        toImageButtonOptions:{filename:i===0?'lce-experimento-a-referencia':'lce-experimento-a-atual'}});
    }
    if (root.token !== token) return;
    root.limites = sincronizado ? preservar[0] : null;
    root.individuais = [...preservar];
    root.sincronizado = sincronizado;
    root.contexto = data.contexto;
    await colorir(tema);
    root.syncing = false;
    plots.forEach((plot,indice) => {
      const handler = async evento => {
        if (root.syncing || root.token !== token) return;
        const limites = limitesRelayout(evento,plot.layout,figures[indice].layout);
        if (!limites) return;
        root.syncing = true;
        if (sincronizado) {
          root.limites = limites;
          root.individuais = [limites,limites];
        } else root.individuais[indice] = limites;
        try {
          await Promise.all((sincronizado ? plots : [plot]).map(p => Plotly.relayout(p,limites)));
          status.textContent = sincronizado ? 'Visualização sincronizada nos dois cenários.' :
            'Zoom independente: enquadramentos podem diferir. As escalas visuais não são diretamente comparáveis.';
        } catch (_) {
          status.textContent = 'Não foi possível sincronizar. Use Restaurar visualização comparativa.';
        } finally {root.syncing = false;}
      };
      plot.on('plotly_relayout',handler);
      handlers.push([plot,handler]);
    });
    observer = new ResizeObserver(entries => {
      const largura = entries[0].contentRect.width;
      root.dataset.disposicao = largura >= 1100 ? 'lado-a-lado' : 'empilhada';
      // Ambos recebem a mesma largura útil, inclusive quando empilhados.
      for (const p of plots) Plotly.Plots.resize(p);
    });
    observer.observe(root);
    // O tema nativo muda sem rerun Python. Ler apenas cores calculadas do DOM;
    // nenhum limite de eixo ou estado econômico é escrito nesta atualização.
    temaObserver = new MutationObserver(() => {
      const novo = temaAtual();
      if (root.token !== token || JSON.stringify(novo) === JSON.stringify(tema)) return;
      tema = novo;
      root.work = root.work.then(()=>root.token===token ? colorir(novo) : undefined);
    });
    temaObserver.observe(app,{attributes:true,attributeFilter:['class','style']});
    status.textContent = sincronizado ? 'Mesmas escalas; zoom e deslocamento sincronizados. As curvas respeitam seus domínios próprios.' :
      'Zoom independente: enquadramentos podem diferir. As escalas visuais não são diretamente comparáveis.';
  }).catch(() => {
    status.textContent = 'Não foi possível renderizar os gráficos comparativos. Recarregue a página.';
    root.syncing = false;
  });
  return () => {
    observer?.disconnect();
    temaObserver?.disconnect();
    handlers.forEach(([plot,handler]) => plot.removeListener('plotly_relayout',handler));
    if (root.token === token) root.token = null;
    // Rerenders reutilizam o DOM; no encerramento, liberar também os listeners
    // de resize que o próprio Plotly registra fora do componente.
    root.work.finally(() => {
      if (!root.isConnected) plots.forEach(plot => Plotly.purge(plot));
    });
  };
}

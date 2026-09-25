(function (root, factory) {
  const api = factory(root);
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.VAPPlotlyRenderer = Object.freeze(api);
})(typeof globalThis !== 'undefined' ? globalThis : this, function (root) {
  'use strict';

  // def 01 PARAMETERS
  const VERSION = 'v025';
  const SCHEMA = 'VIA-VAP-PLOTLY-RENDERER/1.1';
  const OBSERVATION_SCHEMA = 'VIA-VAP-OBSERVATION-SPEC/1.0';
  const TICK_COUNT = 5;
  const INTERVAL_COUNT = 4;
  const TOKENS = Object.freeze({
    paper: '#ffffff', plot: '#ffffff', ink: '#1b1a17', muted: '#6b6860', grid: '#e8e6df', line: '#d8d5cd',
    left: '#4c72b0', right: '#dd8452', positive: '#c93030', negative: '#2e8b57', font: 'Microsoft JhengHei, Segoe UI, sans-serif'
  });

  // def 02 OBSERVATION ENGINE
  function def_number(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }
  function def_date(value) {
    const text = String(value ?? '').trim();
    const normalized = /^\d{4}-\d{2}$/.test(text) ? text + '-01T00:00:00Z' : text;
    const date = new Date(normalized);
    return Number.isFinite(date.getTime()) ? date : null;
  }
  function def_frequency_bucket(value, frequency) {
    const date = def_date(value);
    if (!date || ['native', 'daily'].includes(frequency)) return String(value);
    const year = date.getUTCFullYear(), month = date.getUTCMonth();
    if (frequency === 'weekly') {
      const start = new Date(Date.UTC(year, month, date.getUTCDate()));
      start.setUTCDate(start.getUTCDate() - ((start.getUTCDay() + 6) % 7));
      return start.toISOString().slice(0, 10);
    }
    if (frequency === 'monthly') return year + '-' + String(month + 1).padStart(2, '0');
    if (frequency === 'quarterly') return year + '-Q' + (Math.floor(month / 3) + 1);
    if (frequency === 'yearly') return String(year);
    return String(value);
  }
  function def_resample_series(series, frequency) {
    const selected = String(frequency || 'native').toLowerCase();
    if (!series || !Array.isArray(series.x) || !Array.isArray(series.y) || series.x.length !== series.y.length) throw new Error('SERIES_X_Y_LENGTH_MISMATCH');
    if (['native', 'daily'].includes(selected)) return { ...series, x: [...series.x], y: [...series.y], customdata: Array.isArray(series.customdata) ? [...series.customdata] : undefined };
    const buckets = new Map();
    series.x.forEach((x, index) => buckets.set(def_frequency_bucket(x, selected), { x, y: series.y[index], customdata: Array.isArray(series.customdata) ? series.customdata[index] : undefined }));
    const rows = [...buckets.values()];
    return { ...series, x: rows.map(row => row.x), y: rows.map(row => row.y), customdata: Array.isArray(series.customdata) ? rows.map(row => row.customdata) : undefined };
  }
  function def_yoy_lag(x, frequency) {
    const selected = String(frequency || 'native').toLowerCase();
    if (selected === 'daily') return 252;
    if (selected === 'weekly') return 52;
    if (selected === 'monthly') return 12;
    if (selected === 'quarterly') return 4;
    if (selected === 'yearly') return 1;
    if (x.every(value => /^\d{4}-\d{2}$/.test(String(value)))) return 12;
    const dates = x.map(def_date).filter(Boolean);
    if (dates.length < 2) return 1;
    const days = Math.abs(dates.at(-1) - dates[0]) / 86400000 / Math.max(1, dates.length - 1);
    return days <= 3 ? 252 : days <= 10 ? 52 : days <= 45 ? 12 : days <= 120 ? 4 : 1;
  }
  function def_transform_series(series, mode, frequency) {
    const selected = String(mode || 'level').toLowerCase(), values = series.y.map(def_number);
    if (selected === 'level') return { ...series, y: values };
    const base = values.find(value => value !== null && value !== 0);
    const lag = selected === 'yoy_pct' ? def_yoy_lag(series.x, frequency) : 1;
    const transformed = values.map((value, index) => {
      if (value === null) return null;
      if (selected === 'rebase_100') return base === undefined ? null : value / base * 100;
      const previous = values[index - lag];
      if (previous === undefined || previous === null || previous === 0) return null;
      if (selected === 'change_pct' || selected === 'yoy_pct') return (value / previous - 1) * 100;
      throw new Error('OBSERVATION_MODE_UNSUPPORTED');
    });
    return { ...series, y: transformed };
  }
  function def_apply_time_window(series, range) {
    const selected = String(range || 'ALL').toUpperCase();
    if (selected === 'ALL' || !series.x.length) return { ...series, x: [...series.x], y: [...series.y], customdata: Array.isArray(series.customdata) ? [...series.customdata] : undefined };
    const years = Number(selected.replace('Y', ''));
    const end = def_date(series.x.at(-1));
    if (!Number.isFinite(years) || !end) return { ...series };
    const start = new Date(end.getTime());
    start.setUTCFullYear(start.getUTCFullYear() - years);
    const keep = series.x.map((value, index) => ({ value, index, date: def_date(value) })).filter(row => row.date && row.date >= start);
    return { ...series, x: keep.map(row => row.value), y: keep.map(row => series.y[row.index]), customdata: Array.isArray(series.customdata) ? keep.map(row => series.customdata[row.index]) : undefined };
  }
  function def_prepare_observation_series(series, observation) {
    const spec = { schema: OBSERVATION_SCHEMA, timeRange: 'ALL', frequency: 'native', valueMode: 'level', ...(observation || {}) };
    let prepared = def_resample_series(series, spec.frequency);
    prepared = def_transform_series(prepared, spec.valueMode, spec.frequency);
    prepared = def_apply_time_window(prepared, spec.timeRange);
    const rows = prepared.x.map((x, index) => ({ x, y: prepared.y[index], customdata: Array.isArray(prepared.customdata) ? prepared.customdata[index] : undefined })).filter(row => Number.isFinite(row.y));
    return { ...prepared, x: rows.map(row => row.x), y: rows.map(row => row.y), customdata: Array.isArray(prepared.customdata) ? rows.map(row => row.customdata) : undefined, observation: spec };
  }

  // def 03 AXIS CONTRACT
  function def_axis_contract(values, includeZero) {
    const finite = values.map(def_number).filter(value => value !== null);
    if (!finite.length) return { lo: 0, hi: 4, step: 1, ticks: [0, 1, 2, 3, 4], decimals: 0 };
    let minimum = Math.min(...finite), maximum = Math.max(...finite);
    if (includeZero) { minimum = Math.min(0, minimum); maximum = Math.max(0, maximum); }
    if (minimum === maximum) { const padding = Math.abs(minimum || 1) * 0.1; minimum -= padding; maximum += padding; }
    const raw = (maximum - minimum) / INTERVAL_COUNT, exponent = Math.floor(Math.log10(Math.max(raw, Number.MIN_VALUE))), scale = 10 ** exponent;
    const normalized = raw / scale, family = [2, 2.5, 5, 10], selected = normalized <= 1 ? 10 : family.find(value => value >= normalized) || 10;
    const step = selected === 10 && normalized <= 1 ? scale : selected * scale;
    let lo = Math.floor(minimum / step) * step, hi = lo + INTERVAL_COUNT * step;
    if (hi < maximum - step * 1e-9) { hi = Math.ceil(maximum / step) * step; lo = hi - INTERVAL_COUNT * step; }
    if (includeZero && lo > 0) { lo = 0; hi = INTERVAL_COUNT * step; }
    if (includeZero && hi < 0) { hi = 0; lo = -INTERVAL_COUNT * step; }
    const decimals = step >= 1 ? 0 : Math.min(8, Math.max(0, Math.ceil(-Math.log10(step)) + (selected === 2.5 ? 1 : 0)));
    return { lo, hi, step, ticks: Array.from({ length: TICK_COUNT }, (_, index) => +(lo + index * step).toFixed(decimals + 2)), decimals };
  }

  // def 04 FIGURE CONTRACT
  function def_layout(options) {
    const config = options || {}, left = config.leftAxis || def_axis_contract([0, 1], false), right = config.rightAxis || null;
    return {
      paper_bgcolor: TOKENS.paper, plot_bgcolor: TOKENS.plot,
      font: { family: TOKENS.font, color: TOKENS.ink, size: 12 },
      title: { text: config.title || '', x: 0.01, xanchor: 'left' },
      margin: { l: 70, r: config.dualAxis ? 70 : 28, t: 72, b: 52 },
      hovermode: 'x unified', dragmode: 'zoom',
      xaxis: {
        showgrid: false, rangeslider: { visible: Boolean(config.rangeSlider) }, zeroline: false,
        rangeselector: config.rangeSelector === false ? undefined : { buttons: [{ count: 1, label: '1Y', step: 'year', stepmode: 'backward' }, { count: 3, label: '3Y', step: 'year', stepmode: 'backward' }, { count: 5, label: '5Y', step: 'year', stepmode: 'backward' }, { step: 'all', label: 'All' }] }
      },
      yaxis: { title: { text: config.leftUnit || '' }, showgrid: true, gridcolor: TOKENS.grid, zeroline: false, fixedrange: false, range: [left.lo, left.hi], tickvals: left.ticks, tickformat: left.decimals ? '.' + left.decimals + 'f' : undefined },
      yaxis2: config.dualAxis ? { title: { text: config.rightUnit || '' }, overlaying: 'y', side: 'right', showgrid: false, zeroline: false, fixedrange: false, range: [right.lo, right.hi], tickvals: right.ticks, tickformat: right.decimals ? '.' + right.decimals + 'f' : undefined } : undefined,
      legend: { orientation: 'h', x: 0, y: 1.12, bgcolor: 'rgba(255,255,255,.88)' },
      annotations: config.annotations || [],
      meta: { observation: config.observation || null, axisContract: { intervalCount: INTERVAL_COUNT, tickCount: TICK_COUNT, left, right }, evidence: config.evidence || null },
      uirevision: config.uirevision || 'VAP-v025'
    };
  }
  function def_trace(series, index) {
    if (!series || !Array.isArray(series.x) || !Array.isArray(series.y) || series.x.length !== series.y.length) throw new Error('TRACE_X_Y_LENGTH_MISMATCH');
    const form = String(series.form || 'line').toLowerCase();
    const color = series.color || (series.axis === 'right' ? TOKENS.right : TOKENS.left);
    const evidence = [series.unit || '', series.source || '', series.asOf || '', series.dataStatus || ''];
    const customdata = Array.isArray(series.customdata) && series.customdata.length === series.x.length ? series.customdata : series.x.map(() => evidence);
    const trace = {
      name: series.name || 'Series ' + (index + 1), x: series.x, y: series.y,
      yaxis: series.axis === 'right' ? 'y2' : 'y', opacity: Number.isFinite(Number(series.opacity)) ? Number(series.opacity) : 0.9,
      customdata,
      hovertemplate: '<b>%{fullData.name}</b><br>%{x}<br>%{y} %{customdata[0]}<br>Source: %{customdata[1]}<br>As Of: %{customdata[2]}<br>%{customdata[3]}<extra></extra>'
    };
    if (form === 'bar') return { ...trace, type: 'bar', marker: { color, line: { color, width: 0 } } };
    if (form === 'scatter') return { ...trace, type: 'scatter', mode: 'markers', marker: { color, size: series.size || 7 } };
    return { ...trace, type: 'scatter', mode: 'lines', fill: form === 'area' ? 'tozeroy' : undefined, line: { color, width: Number(series.width || 2), dash: series.dash || (series.axis === 'right' ? 'dash' : 'solid') } };
  }
  function def_last_annotation(series) {
    if (!series.x.length) return null;
    const value = series.y.at(-1);
    return { x: series.x.at(-1), y: value, xref: 'x', yref: series.axis === 'right' ? 'y2' : 'y', text: (series.name || 'Series') + ' ' + Number(value).toLocaleString(undefined, { maximumFractionDigits: 3 }) + (series.unit ? ' ' + series.unit : ''), showarrow: false, xanchor: 'left', xshift: 6, font: { color: series.color || (series.axis === 'right' ? TOKENS.right : TOKENS.left), size: 11 }, bgcolor: 'rgba(255,255,255,.82)' };
  }
  function def_build_figure(contract) {
    if (!contract || !Array.isArray(contract.series) || !contract.series.length) throw new Error('FIGURE_SERIES_REQUIRED');
    const observation = { schema: OBSERVATION_SCHEMA, timeRange: 'ALL', frequency: 'native', valueMode: 'level', ...(contract.observation || {}) };
    const prepared = contract.series.map(series => def_prepare_observation_series(series, observation));
    const dualAxis = prepared.some(item => item.axis === 'right');
    const leftSeries = prepared.filter(item => item.axis !== 'right'), rightSeries = prepared.filter(item => item.axis === 'right');
    const leftAxis = def_axis_contract(leftSeries.flatMap(item => item.y), leftSeries.some(item => String(item.form).toLowerCase() === 'bar'));
    const rightAxis = dualAxis ? def_axis_contract(rightSeries.flatMap(item => item.y), rightSeries.some(item => String(item.form).toLowerCase() === 'bar')) : null;
    const annotations = contract.showLastValue === false ? [] : prepared.map(def_last_annotation).filter(Boolean);
    return {
      schema: SCHEMA, version: VERSION,
      data: prepared.map(def_trace),
      layout: def_layout({ title: contract.title, dualAxis, rangeSlider: contract.rangeSlider, rangeSelector: contract.rangeSelector, uirevision: contract.id, leftAxis, rightAxis, leftUnit: leftSeries[0]?.unit, rightUnit: rightSeries[0]?.unit, annotations, observation, evidence: contract.evidence }),
      config: { responsive: true, displaylogo: false, scrollZoom: true, modeBarButtonsToRemove: ['lasso2d'], toImageButtonOptions: { format: 'png', scale: 3 } }
    };
  }
  async function def_render(target, contract) {
    if (!root.Plotly || typeof root.Plotly.react !== 'function') throw new Error('PLOTLY_RUNTIME_NOT_AVAILABLE');
    const element = typeof target === 'string' ? root.document.querySelector(target) : target;
    if (!element) throw new Error('RENDER_TARGET_NOT_FOUND');
    const figure = def_build_figure(contract);
    await root.Plotly.react(element, figure.data, figure.layout, figure.config);
    return figure;
  }

  // def 05 SELF TEST
  function def_self_test() {
    const figure = def_build_figure({ title: 'Test', observation: { timeRange: 'ALL', frequency: 'monthly', valueMode: 'rebase_100' }, series: [{ name: 'A', x: ['2025-01', '2025-02'], y: [10, 12], axis: 'left', unit: 'Index' }, { name: 'B', x: ['2025-01', '2025-02'], y: [20, 18], axis: 'right', form: 'bar', unit: '%' }] });
    const checks = {
      schema: figure.schema === SCHEMA,
      traces: figure.data.length === 2,
      dualAxis: figure.layout.yaxis2.side === 'right',
      ticks: figure.layout.yaxis.tickvals.length === TICK_COUNT && figure.layout.yaxis2.tickvals.length === TICK_COUNT,
      observation: figure.layout.meta.observation.valueMode === 'rebase_100' && figure.data[0].y[0] === 100,
      evidenceHover: figure.data[0].hovertemplate.includes('Source:'),
      noCdnClaim: !JSON.stringify(figure).includes('cdn')
    };
    return { schema: SCHEMA, version: VERSION, status: Object.values(checks).every(Boolean) ? 'PASS' : 'FAIL', checks };
  }
  return {
    VERSION, SCHEMA, OBSERVATION_SCHEMA, TOKENS, TICK_COUNT, INTERVAL_COUNT,
    resampleSeries: def_resample_series, transformSeries: def_transform_series, applyTimeWindow: def_apply_time_window,
    prepareObservationSeries: def_prepare_observation_series, axisContract: def_axis_contract,
    buildLayout: def_layout, buildTrace: def_trace, buildFigure: def_build_figure, render: def_render, selfTest: def_self_test
  };
});

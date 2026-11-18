'use strict';
const MODEL = JSON.parse(document.getElementById('model').textContent);
const $ = (selector) => document.querySelector(selector);
const all = (selector) => Array.from(document.querySelectorAll(selector));
const LIMIT = 50;
const PANEL_PREF_KEY = 'via-governance-panels-v0105';
const COMMON = ['status', 'id', 'ssot_name'];
const ICONS = {
  search: [['circle', {cx:'10', cy:'10', r:'6'}], ['path', {d:'m15 15 5 5'}]],
  sliders: [['path', {d:'M4 6h16M4 12h16M4 18h16'}], ['circle', {cx:'8', cy:'6', r:'2'}], ['circle', {cx:'16', cy:'12', r:'2'}], ['circle', {cx:'10', cy:'18', r:'2'}]],
  layers: [['path', {d:'m12 3 10 6-10 6L2 9zM2 13l10 6 10-6M2 17l10 6 10-6'}]],
  reset: [['path', {d:'M4 9a8 8 0 1 1 0 7M4 4v5h5'}]],
  download: [['path', {d:'M12 3v13m-5-5 5 5 5-5M4 16v5h16v-5'}]],
  grid: [['path', {d:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z'}]],
};
function icon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  for (const [tag, attrs] of (ICONS[name] || ICONS.grid)) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    svg.append(node);
  }
  return svg;
}
function el(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}
function display(value) {
  if (value === undefined) return 'NOT_OBSERVED';
  if (value === null) return 'NULL (explicit)';
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}
function statusInfo(value) {
  const raw = display(value).trim() || 'PENDING';
  const upper = raw.toUpperCase();
  let code = 'YELLOW';
  if (/\bRED\b/.test(upper)) code = 'RED';
  else if (/\bGREEN\b/.test(upper)) code = 'GREEN';
  const pending = !/\b(?:RED|YELLOW|GREEN)\b/.test(upper) || /PENDING|UNKNOWN|NOT_OBSERVED|NOT RUN|UPLOADED/.test(upper);
  const label = /\b(?:RED|YELLOW|GREEN)\b/.test(upper) ? raw : 'YELLOW · ' + raw;
  return {code, label, pending};
}
function rowStatus(row) { return statusInfo(row.status); }
function rowField(row, key) { return key === 'status' ? row.status : row[key]; }
function matrixRows(tab) {
  const rows = MODEL.matrices && Array.isArray(MODEL.matrices[tab]) ? MODEL.matrices[tab] : [];
  return rows;
}
const TAB_META = {
  systems: {title:'系統治理矩陣', note:'VCGC、VDF、VRN、VQG、VAP 與相關 peer 的候選狀態；source 名稱不代表 owner 正式 SSOT。'},
  io: {title:'參數 I/O 矩陣', note:'參數、輸入、輸出與契約欄位只列 inventory 可證實內容；未知欄位顯示 NOT_OBSERVED。'},
  commands: {title:'指令 CLS-FNC-LIB 定位矩陣', note:'Python AST 僅產生 candidate locator；JS / PS static text 不等同 AST，也不表示 runtime coverage。'},
  files: {title:'全部文件與來源成員', note:'大量文件採 50 列分頁 lazy render；SHA、ZIP member 與 duplicate alias 只作追溯，不自動註冊。'},
  environment: {title:'環境 / 工具矩陣', note:'環境存在、工具版本與依賴證據分開呈現；未觀測與未跑不可推論為 GREEN。'},
  conflicts: {title:'衝突與治理阻礙', note:'衝突保持 RED / YELLOW 邊界；此頁沒有解除按鈕，ACTUAL 仍維持 RED / BLOCKED。'},
  policy: {title:'SSOT · REGEX · 同義字政策', note:'政策條款、SSOT 邊界、regex 與 synonym 只作候選治理證據，不取代正式 owner 決策。'},
  tests: {title:'測試輸出 / 驗證矩陣', note:'uploaded PASS ≠ this-round execution；Sandbox UI 驗證與 peer integration 需分開核對。'},
  requirements: {title:'VAP 需求與差異矩陣', note:'需求文字與 v027 觀測實作逐列揭露；VAP 純展示與 VQG 計算邊界不可互換。'},
};
const state = {tab:'systems', page:0, selected:null, panels:{leftHidden:false, rightHidden:false}};
try {
  const saved = JSON.parse(localStorage.getItem(PANEL_PREF_KEY) || '{}');
  state.panels.leftHidden = saved.leftHidden === true;
  state.panels.rightHidden = saved.rightHidden === true;
} catch (_) {}
function allRows() { return Object.values(MODEL.matrices || {}).flatMap((rows) => Array.isArray(rows) ? rows : []); }
function addOptions() {
  const systems = new Set();
  for (const row of allRows()) {
    const value = display(row.system);
    if (value !== 'NOT_OBSERVED') systems.add(value);
  }
  for (const value of Array.from(systems).sort()) {
    const option = el('option', '', value);
    option.value = value;
    $('#system-filter').append(option);
  }
}
function matches(row) {
  const query = $('#query').value.trim().toLocaleLowerCase();
  const system = $('#system-filter').value;
  const filter = $('#status-filter').value;
  if (system && display(row.system) !== system) return false;
  const info = rowStatus(row);
  if (filter === 'RED' || filter === 'GREEN' || filter === 'YELLOW') {
    if (info.code !== filter) return false;
  }
  if (filter === 'PENDING' && !info.pending) return false;
  return !query || JSON.stringify(row).toLocaleLowerCase().includes(query);
}
function columnsFor(rows) {
  const columns = [...COMMON];
  const seen = new Set(columns);
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (key === 'error_detail' || key.startsWith('_') || seen.has(key)) continue;
      seen.add(key);
      columns.push(key);
    }
  }
  columns.push('error_detail');
  return columns;
}
const COLUMN_LABELS = {
  status:'燈號', id:'編號', ssot_name:'SSOT名稱', system:'系統', source:'來源', source_sha256:'來源 SHA-256',
  version:'版本', kind:'種類', scope:'範圍', evidence:'證據', error_detail:'錯誤詳細說明'
};
function columnLabel(key) { return COLUMN_LABELS[key] || key; }
function statusCell(value) {
  const info = statusInfo(value);
  const box = el('div', 'status-cell');
  const dot = el('span', 'status-dot ' + info.code.toLowerCase());
  dot.setAttribute('aria-label', info.code);
  const label = el('span', 'status-label', info.label);
  box.append(dot, label);
  return box;
}
function inspect(row, matrixName) {
  state.selected = row;
  $('#inspect-title').textContent = display(row.id || row.ssot_name || 'NOT_ASSIGNED');
  $('#inspect-note').textContent = 'READ-ONLY EVIDENCE · ' + matrixName + ' · source 名稱不代表 owner 正式 SSOT；選取不變更 actual release。';
  const fields = $('#inspect-fields');
  fields.replaceChildren();
  const dl = el('dl');
  for (const [key, value] of Object.entries(row)) {
    if (key.startsWith('_')) continue;
    dl.append(el('dt', '', columnLabel(key)));
    const dd = el('dd');
    if (value !== null && typeof value === 'object') dd.append(el('pre', '', display(value)));
    else dd.textContent = display(value);
    dl.append(dd);
  }
  fields.append(dl);
  if (matchMedia('(max-width:720px)').matches) $('#inspector').scrollIntoView({behavior:'auto', block:'start'});
}
function matrixTable(rows, matrixName) {
  const wrap = el('div', 'table-wrap ' + matrixName);
  const table = el('table');
  const columns = columnsFor(rows);
  table.style.width = (440 + Math.max(0, columns.length - 3) * 220) + 'px';
  const head = el('thead');
  const headerRow = el('tr');
  for (const key of columns) headerRow.append(el('th', '', columnLabel(key)));
  head.append(headerRow);
  table.append(head);
  const body = el('tbody');
  const start = state.page * LIMIT;
  const slice = rows.slice(start, start + LIMIT);
  for (const row of slice) {
    const tr = el('tr', 'matrix-row');
    tr.tabIndex = 0;
    tr.dataset.rowId = display(row.id);
    tr.addEventListener('click', () => inspect(row, matrixName));
    tr.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); inspect(row, matrixName); }
    });
    for (const key of columns) {
      const td = el('td', key === 'status' ? '' : (['id','source_sha256','version','kind'].includes(key) ? 'code' : ''));
      if (key === 'status') td.append(statusCell(rowField(row, key)));
      else {
        const value = display(rowField(row, key));
        td.textContent = value.length > 220 ? value.slice(0, 220) + '…' : value;
        td.title = value;
      }
      tr.append(td);
    }
    body.append(tr);
  }
  table.append(body);
  wrap.append(table);
  if (!slice.length) wrap.append(el('p', 'empty', '目前篩選無符合列；缺資料顯示 PENDING，不推論為 GREEN。'));
  return wrap;
}
function renderKpis() {
  const rows = allRows();
  const red = rows.filter((row) => rowStatus(row).code === 'RED').length;
  const errors = Array.isArray(MODEL.errors) ? MODEL.errors.length : 0;
  const values = [
    [String(Object.keys(MODEL.matrices || {}).length), '治理矩陣頁籤', 'grid'],
    [String(rows.length), 'inventory 候選列', 'layers'],
    [String(red), 'RED / BLOCKED 列', 'grid'],
    [String(errors), '解析錯誤（不含治理阻礙）', 'search'],
  ];
  const box = $('#kpis');
  box.replaceChildren();
  for (const [number, label, symbol] of values) {
    const card = el('div', 'kpi');
    const iconBox = el('span', 'icon');
    iconBox.append(icon(symbol));
    card.append(iconBox, el('strong', '', number), el('span', '', label));
    box.append(card);
  }
}
function render() {
  const tab = TAB_META[state.tab] ? state.tab : 'systems';
  state.tab = tab;
  const allForTab = matrixRows(tab);
  const rows = allForTab.filter(matches);
  const pages = Math.max(1, Math.ceil(rows.length / LIMIT));
  state.page = Math.min(Math.max(0, state.page), pages - 1);
  const index = Object.keys(TAB_META).indexOf(tab) + 1;
  $('#view-index').textContent = 'MATRIX / ' + String(index).padStart(2, '0');
  $('#view-title').textContent = TAB_META[tab].title;
  $('#view-subtitle').textContent = TAB_META[tab].note;
  const view = $('#view');
  view.replaceChildren();
  if (!allForTab.length) {
    const notice = el('div', 'notice', 'PENDING · 此矩陣目前沒有可呈現列；等待正式 inventory/evidence，不以空白假設 GREEN。');
    view.append(notice);
  }
  view.append(matrixTable(rows, tab));
  $('#row-count').textContent = rows.length + ' / ' + allForTab.length + ' 列';
  $('#page-label').textContent = (state.page + 1) + ' / ' + pages;
  $('#prev-page').disabled = state.page === 0;
  $('#next-page').disabled = state.page >= pages - 1;
  all('[data-tab]').forEach((button) => {
    const active = button.dataset.tab === tab;
    button.setAttribute('aria-selected', String(active));
    button.tabIndex = active ? 0 : -1;
  });
}
function download(content, name, type) {
  const url = URL.createObjectURL(new Blob([content], {type}));
  const anchor = el('a');
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function csvCell(value) {
  let string = display(value);
  if (/^\s*[=+@-]/.test(string)) string = "'" + string;
  return '"' + string.replaceAll('"', '""') + '"';
}
function filteredRows() { return matrixRows(state.tab).filter(matches); }
function exportCsv() {
  const rows = filteredRows();
  const columns = columnsFor(matrixRows(state.tab));
  const output = [columns.map((key) => csvCell(columnLabel(key))).join(',')];
  for (const row of rows) output.push(columns.map((key) => csvCell(rowField(row, key))).join(','));
  download('\uFEFF' + output.join('\r\n'), 'VIA_governance_' + state.tab + '_v0105.csv', 'text/csv;charset=utf-8');
}
function exportJson() {
  const payload = {version: MODEL.version, matrix: state.tab, rows: filteredRows(), meta: MODEL.meta, scope: 'filtered current matrix; preview-only; no registration'};
  download(JSON.stringify(payload, null, 2), 'VIA_governance_' + state.tab + '_v0105.json', 'application/json');
}
function updateToggle(button, hidden, label) {
  button.textContent = (hidden ? '＋ ' : '− ') + label;
  button.setAttribute('aria-expanded', String(!hidden));
  button.setAttribute('aria-label', (hidden ? '顯示' : '隱藏') + label);
  button.title = (hidden ? '顯示' : '隱藏') + label;
}

function setLayoutPixel(name, value) {
  const next = Math.round(value) + 'px';
  const style = document.documentElement.style;
  if (style.getPropertyValue(name) !== next) style.setProperty(name, next);
}
function frameScheduler(work) {
  let pendingFrame = 0;
  return function scheduledLayout() {
    if (pendingFrame) return;
    pendingFrame = requestAnimationFrame(() => { pendingFrame = 0; work(); });
  };
}
function syncStickyOffsets() {
  const mast = $('#masthead'); const centerHead = $('#center-panel-head'); const tabs = $('.tabs'); const copy = $('.brand-copy');
  const sizes = {logo: copy ? copy.getBoundingClientRect().height * 1.08 : null,
    head: mast ? mast.getBoundingClientRect().height : null,
    center: centerHead ? centerHead.getBoundingClientRect().height : null,
    tabs: tabs ? tabs.getBoundingClientRect().height : null};
  if (sizes.logo !== null) setLayoutPixel('--brand-logo-height', Math.min(140, Math.max(48, sizes.logo)));
  if (sizes.head !== null) setLayoutPixel('--head', Math.ceil(sizes.head));
  if (sizes.center !== null) setLayoutPixel('--center-head', Math.ceil(sizes.center));
  if (sizes.tabs !== null) setLayoutPixel('--tabs-height', Math.ceil(sizes.tabs));
}
const scheduleStickyLayout = frameScheduler(syncStickyOffsets);
function applyPanelLayout(persist) {
  const left = state.panels.leftHidden;
  const right = state.panels.rightHidden;
  $('#input-rail').hidden = left;
  $('#inspector').hidden = right;
  $('.workspace').classList.toggle('hide-input', left);
  $('.workspace').classList.toggle('hide-evidence', right);
  updateToggle($('#toggle-input'), left, '輸入面板');
  updateToggle($('#toggle-evidence'), right, '證據面板');
  if (persist) {
    try { localStorage.setItem(PANEL_PREF_KEY, JSON.stringify(state.panels)); } catch (_) {}
  }
  requestAnimationFrame(syncStickyOffsets);
}
function switchTab(tab) { state.tab = tab; state.page = 0; render(); }
all('[data-icon]').forEach((node) => node.append(icon(node.dataset.icon)));
addOptions();
renderKpis();
const pending = MODEL.meta && Array.isArray(MODEL.meta.pending_warnings) ? MODEL.meta.pending_warnings : [];
const warning = $('#inventory-warning');
if (pending.length) warning.textContent += ' ' + pending.join(' ');
$('#generated-at').textContent = 'GOVERNANCE ' + display(MODEL.version) + ' · evidence ' + display(MODEL.meta && MODEL.meta.evidence_status);
for (const [index, button] of all('[data-tab]').entries()) {
  button.id = 'tab-' + button.dataset.tab;
  button.setAttribute('aria-controls', 'view');
  button.addEventListener('click', () => switchTab(button.dataset.tab));
  button.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const tabs = all('[data-tab]');
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    switchTab(tabs[next].dataset.tab);
    tabs[next].focus();
  });
}
for (const selector of ['#query', '#system-filter', '#status-filter']) {
  $(selector).addEventListener(selector === '#query' ? 'input' : 'change', () => { state.page = 0; render(); });
}
$('#reset-view').addEventListener('click', () => {
  $('#query').value = '';
  $('#system-filter').value = '';
  $('#status-filter').value = '';
  state.page = 0;
  render();
});
$('#prev-page').addEventListener('click', () => { state.page -= 1; render(); });
$('#next-page').addEventListener('click', () => { state.page += 1; render(); });
$('#export-csv').addEventListener('click', exportCsv);
$('#export-json').addEventListener('click', exportJson);
$('#toggle-input').addEventListener('click', () => { state.panels.leftHidden = !state.panels.leftHidden; applyPanelLayout(true); });
$('#toggle-evidence').addEventListener('click', () => { state.panels.rightHidden = !state.panels.rightHidden; applyPanelLayout(true); });
all('[data-hide-panel]').forEach((button) => button.addEventListener('click', () => {
  state.panels[button.dataset.hidePanel + 'Hidden'] = true;
  applyPanelLayout(true);
}));
applyPanelLayout(false);
if (typeof ResizeObserver !== 'undefined') {
  const observer = new ResizeObserver(scheduleStickyLayout);
  ['#masthead', '.brand-copy', '#center-panel-head', '.tabs'].forEach((selector) => observer.observe($(selector)));
}
scheduleStickyLayout();
window.VIA_GOVERNANCE = {actualRelease:'RED/BLOCKED', registration:false, model:MODEL, viewState:state, limit:LIMIT};

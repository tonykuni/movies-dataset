// board_qa_runner.mjs v0100 — 指揮板 unit + integration 兩層(node vm;零安裝依賴)
// 用法:node board_qa_runner.mjs <extracted_board_js> <fixture_json>
// unit:vm context 直呼純函數;integration:render 後 DOM 側效斷言(shim 慣例)。
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const [, , jsPath, fxPath] = process.argv;
const js = readFileSync(jsPath, 'utf8');
const fixture = readFileSync(fxPath, 'utf8');

const byId = {}, bySel = {};
function nFor(s) { if (s === '.tab') return 12; if (s === '.tab .tx') return 11; if (s === '.page') return 11; return 8; }
function mkEl() {
  const el = {
    textContent: '', innerHTML: '', value: '', checked: false, disabled: false,
    style: {}, dataset: {}, _cls: {},
    classList: { add: c => { el._cls[c] = 1; }, remove: c => { delete el._cls[c]; }, contains: c => !!el._cls[c] },
    addEventListener: (ev, fn) => { (el._ev = el._ev || {})[ev] = fn; },
    querySelectorAll: s => { if (!bySel[s]) bySel[s] = Array.from({ length: nFor(s) }, () => mkEl()); return bySel[s]; },
    querySelector: () => mkEl(),
    insertAdjacentHTML: (pos, h) => { el.innerHTML = pos === 'afterbegin' ? h + el.innerHTML : el.innerHTML + h; },
    click: () => { if (el._ev && el._ev.click) el._ev.click(); },
    blur: () => {}, focus: () => {},
  };
  return el;
}
const ctx = {
  document: {
    getElementById: id => { if (!byId[id]) byId[id] = mkEl(); return byId[id]; },
    querySelectorAll: s => { if (!bySel[s]) bySel[s] = Array.from({ length: nFor(s) }, () => mkEl()); return bySel[s]; },
    querySelector: () => mkEl(), createElement: () => mkEl(),
    addEventListener: () => {}, activeElement: null,
    body: { classList: { add: () => {}, remove: () => {} } },
  },
  window: { prompt: () => {} }, navigator: {},
  localStorage: { getItem: () => null, setItem: () => {} },
  URL: { createObjectURL: () => 'b' }, Blob: function () {},
  console, parseInt, parseFloat, JSON, Math, Object, Array, String, Number, RegExp, Date,
};
vm.createContext(ctx);
vm.runInContext(js.replace('var DATA = __VIA_DATA__;', 'var DATA = ' + fixture + ';'), ctx);

let nOK = 0, nFAIL = 0;
function A(cond, msg) {
  if (cond) { nOK++; console.log('ok  U/I - ' + msg); }
  else { nFAIL++; console.error('FAIL U/I - ' + msg); }
}

// ---- TIER 1 unit(vm 直呼純函數)----
A(ctx.esc('<a> & <b>') === '&lt;a&gt; &amp; &lt;b&gt;', 'unit esc() HTML 逃逸(板契約:& < > 三字元)');
A(JSON.stringify(ctx.arr(null)) === '[]' && JSON.stringify(ctx.arr([1])) === '[1]' && JSON.stringify(ctx.arr(1)) === '[1]', 'unit arr() 正規化');
A(ctx.fmt('{n} 件 · {d} 天', { n: 3, d: 7 }) === '3 件 · 7 天', 'unit fmt() 佔位替換');
A(ctx.t('ttl').indexOf('指揮板') >= 0, 'unit t() zh 詞條');
A(typeof ctx.gsBuild === 'function' && ctx.gsBuild().length > 0, 'unit gsBuild() 索引非空');
A(ctx.pfStrip('p2').indexOf('pfstrip') >= 0 && ctx.pfStrip('p2').indexOf('→') >= 0, 'unit pfStrip() 步驟+箭頭');
A(ctx.pfStrip('nosuch') === '', 'unit pfStrip() 未知頁誠實空字串');

// ---- TIER 2 integration(render 後 DOM 側效)----
const pages = ['pT', 'pO', 'p0', 'p1', 'p2', 'pB', 'pC', 'p3', 'p4', 'p5', 'p6'];
A(pages.every(p => (byId[p] && byId[p].innerHTML.length > 0)), 'integration 十一頁全渲染');
A(pages.every(p => byId[p].innerHTML.indexOf('pfstrip') >= 0), 'integration 流程帶 11/11');
A(byId.pO.innerHTML.indexOf('出信掛號稽核') >= 0, 'integration Σ M7 出信稽核');
A(byId.pO.innerHTML.indexOf('WOP-001') >= 0, 'integration Σ 專案卡(fixture WOP)');
byId.gsq.value = 'thr-00005'; byId.gsq._ev.input();
A(byId.gsd._cls.on && byId.gsd.innerHTML.indexOf('THR-00005') >= 0, 'integration 全域搜尋命中');
byId.gsq._ev.keydown({ key: 'Escape' });
A(!byId.gsd._cls.on, 'integration Esc 收合');
A(byId.smet.innerHTML.indexOf('<b>') >= 0, 'integration 側欄即時指標');

console.log('----------------------------------------');
console.log(`TIER1+2 result: ${nOK} ok / ${nFAIL} fail`);
process.exit(nFAIL ? 1 : 0);

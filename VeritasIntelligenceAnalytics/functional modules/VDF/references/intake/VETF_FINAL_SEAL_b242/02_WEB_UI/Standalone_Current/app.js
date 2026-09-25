"use strict";

/* ========================================================================== */
/* 0. 全域參數                                                               */
/* ========================================================================== */

const PARAMS = Object.freeze({
  asof: "2026/06/22",
  providerGapReviewPct: 30,
  portfolioPeHorizon: "n1",
  exportJsonName: "vetf_consensus_filtered.json",
  exportCsvName: "vetf_consensus_filtered.csv",
  targetStats: ["low", "mean", "median", "high"],
  returnLabels: ["1D", "5D", "10D", "20D", "60D", "120D", "240D", "YTD"],
});

const ETF_DATA = [
  {code:"00981A",name:"主動統一台股增長",issuer:"統一投信",manager:"林哲緯",style:"成長",aum:285,nav:38.12,flow:20.2,expense:.85,since:18.4,returns:[1,.4,2.3,5.6,6.8,11.3,16,14.2]},
  {code:"00982A",name:"主動野村臺灣優選",issuer:"野村投信",manager:"陳柏宇",style:"優選",aum:246,nav:38.13,flow:-5.2,expense:.89,since:15.2,returns:[.5,1.1,2.4,4.7,7.2,10.8,15.4,13.7]},
  {code:"00980A",name:"主動安聯台灣高息",issuer:"安聯投信",manager:"黃詩涵",style:"高息",aum:198,nav:38.1,flow:-19.3,expense:.9,since:9.6,returns:[.2,-.3,1.6,2.7,5.4,8.9,12.4,9.8]},
  {code:"00983A",name:"主動群益台灣強棒",issuer:"群益投信",manager:"張凱程",style:"成長",aum:164,nav:38.15,flow:2.8,expense:.88,since:16.8,returns:[.7,1.4,2.6,4.9,7.5,11.7,16.8,15]},
  {code:"00984A",name:"主動野村台灣50",issuer:"野村投信",manager:"吳承翰",style:"優選",aum:142,nav:38.17,flow:7.8,expense:.85,since:12.1,returns:[.4,.8,1.9,3.8,6.1,9.5,13.6,11.9]},
  {code:"00985A",name:"主動富邦台灣成長",issuer:"富邦投信",manager:"李宗翰",style:"成長",aum:128,nav:38.18,flow:11.9,expense:.87,since:14.3,returns:[.8,1.3,2.8,4.5,7.1,10.9,15.8,13.6]},
  {code:"00986A",name:"主動元大台灣價值",issuer:"元大投信",manager:"周明哲",style:"價值",aum:116,nav:38.21,flow:4.4,expense:.86,since:11.8,returns:[.3,.7,1.5,3.1,5.8,8.7,12.9,10.7]},
  {code:"00987A",name:"主動中信台灣科技",issuer:"中信投信",manager:"鄭宇晴",style:"科技",aum:88,nav:38.25,flow:8.1,expense:.92,since:21.5,returns:[1.2,2.8,3.1,3.2,7.9,15.3,21.2,17.8]},
  {code:"009A01",name:"主動富邦台灣科技",issuer:"富邦投信",manager:"邱柏睿",style:"科技",aum:22,nav:15.08,flow:-2.6,expense:.91,since:15.6,returns:[-.4,-.2,4,2.1,7.6,12.3,16.4,15.6]},
];

const HOLDING_DATA = [
  {ticker:"2330.TW",name:"台積電",sector:"半導體",price:560,cost:519.5,action:"超額配置",quality:"PASS",flags:[],weights:{"00981A":28,"00982A":25,"00980A":21,"00983A":27,"00984A":32,"00985A":24,"00986A":18,"00987A":31,"009A01":29},fs:{low:590,mean:696.2,median:611.9,high:760},yf:{low:580,mean:664.2,median:598.1,high:740},eps:{n:25.4,n1:31.2,n2:36.8}},
  {ticker:"2454.TW",name:"聯發科",sector:"半導體",price:684,cost:652.7,action:"順勢加碼",quality:"PASS",flags:[],weights:{"00981A":7.2,"00982A":5.1,"00983A":7.8,"00985A":6.6,"00987A":9.4,"009A01":8.1},fs:{low:720,mean:794.3,median:839.5,high:930},yf:{low:700,mean:848.5,median:717.3,high:910},eps:{n:58.5,n1:69.4,n2:78.1}},
  {ticker:"2317.TW",name:"鴻海",sector:"AI伺服器",price:547,cost:485.8,action:"強勢重壓",quality:"REVIEW",flags:["PROVIDER_DIVERGENCE"],weights:{"00981A":5.8,"00982A":7,"00983A":5.4,"00984A":6.1,"00985A":8.2,"00986A":4.1},fs:{low:560,mean:627.4,median:636.2,high:720},yf:{low:530,mean:627.2,median:595,high:700},eps:{n:27.8,n1:33.5,n2:39.2}},
  {ticker:"6669.TW",name:"緯穎",sector:"AI伺服器",price:399,cost:358.2,action:"強勢重壓",quality:"PASS",flags:[],weights:{"00981A":4.3,"00983A":5,"00985A":3.7,"00987A":6.8,"009A01":5.9},fs:{low:408,mean:465.2,median:418.9,high:520},yf:{low:405,mean:434.9,median:422.1,high:500},eps:{n:19.5,n1:24.8,n2:29.9}},
  {ticker:"2382.TW",name:"廣達",sector:"AI伺服器",price:612,cost:564.6,action:"順勢加碼",quality:"REVIEW",flags:["TARGET_DATE_AGE_97D"],weights:{"00981A":3.1,"00982A":3.5,"00983A":4,"00984A":3.2,"00985A":4.8,"00987A":5.1},fs:{low:650,mean:751.6,median:753,high:840},yf:{low:640,mean:687.7,median:727.6,high:810},eps:{n:36.1,n1:43.8,n2:49.7}},
  {ticker:"1519.TW",name:"華城",sector:"重電",price:649,cost:582.6,action:"強勢重壓",quality:"PASS",flags:[],weights:{"00981A":2.8,"00983A":2.1,"00985A":3.6,"00986A":4.2},fs:{low:690,mean:804.2,median:776.7,high:890},yf:{low:680,mean:689.7,median:784.2,high:850},eps:{n:28.8,n1:35.4,n2:41.1}},
  {ticker:"2603.TW",name:"長榮",sector:"航運",price:833,cost:777.1,action:"順勢加碼",quality:"PASS",flags:[],weights:{"00980A":3.8,"00982A":2.4,"00984A":2.1,"00986A":3.7},fs:{low:820,mean:886.6,median:900.6,high:970},yf:{low:790,mean:944.4,median:877.2,high:960},eps:{n:92,n1:85.5,n2:79.2}},
  {ticker:"2308.TW",name:"台達電",sector:"電源管理",price:538,cost:516.3,action:"逢低承接",quality:"PASS",flags:[],weights:{"00981A":2.1,"00982A":1.8,"00983A":2,"00984A":2.5,"00985A":2.3,"00986A":1.9,"00987A":2.9,"009A01":3.1},fs:{low:560,mean:581.2,median:626,high:690},yf:{low:550,mean:638.6,median:567.7,high:680},eps:{n:21.5,n1:25.9,n2:30.4}},
  {ticker:"2881.TW",name:"富邦金",sector:"金融",price:211,cost:206.1,action:"逢低承接",quality:"REVIEW",flags:["MISSING_EPS_N2"],weights:{"00980A":2.5,"00982A":1.8,"00984A":2.2,"00986A":3.1},fs:{low:220,mean:236.8,median:240.4,high:270},yf:{low:218,mean:249.2,median:236.9,high:275},eps:{n:14.2,n1:16.8,n2:null}},
];

const REQUEST = {
  request: "tw_active_etf_consensus_enriched",
  asof: "latest",
  universe: {type: "active_etf", exchange: ["TWSE", "TPEX"]},
  fields: ["holdings:weight,manager_action", "price_adj", "target_yf:low,mean,median,high", "target_fs:low,mean,median,high", "eps_fs:N,N+1,N+2", "forward_pe:N,N+1,N+2"],
  verify: ["double_identity", "asof_no_lookahead", "currency_match"],
  write_mode: "candidate",
};

const state = {
  etfs: structuredClone(ETF_DATA),
  holdings: structuredClone(HOLDING_DATA),
  selected: new Set(ETF_DATA.map((item) => item.code)),
  provider: "both",
  search: "",
  sector: "all",
  quality: "all",
  sortKey: "weight",
  sortDirection: "desc",
};

/* ========================================================================== */
/* 1. 通用工具                                                               */
/* ========================================================================== */

function byId(id) { return document.getElementById(id); }
function all(selector) { return [...document.querySelectorAll(selector)]; }
function safeNumber(value) { const parsed = Number(value); return value === null || value === "" || !Number.isFinite(parsed) ? null : parsed; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[char])); }
function number(value, digits = 1) { return value === null || !Number.isFinite(value) ? "—" : value.toLocaleString("zh-TW", {minimumFractionDigits:digits, maximumFractionDigits:digits}); }
function pct(value, digits = 1) { return value === null || !Number.isFinite(value) ? "—" : `${value > 0 ? "+" : ""}${number(value, digits)}%`; }
function pe(price, eps) { return eps !== null && eps > 0 && price > 0 ? price / eps : null; }
function upside(target, price) { return target !== null && price > 0 ? (target / price - 1) * 100 : null; }
function gap(left, right) { return left !== null && right !== null && right !== 0 ? (left - right) / Math.abs(right) * 100 : null; }
function download(name, content, mime) { const url = URL.createObjectURL(new Blob([content], {type:mime})); const anchor = document.createElement("a"); anchor.href = url; anchor.download = name; anchor.click(); URL.revokeObjectURL(url); }
function heat(value) { return value >= 10 ? "heat-strong" : value > 0 ? "heat-up" : value < 0 ? "heat-down" : ""; }

/* ========================================================================== */
/* 2. 聚合計算                                                               */
/* ========================================================================== */

function aggregateHoldings() {
  const aum = Object.fromEntries(state.etfs.map((item) => [item.code, item.aum || 1]));
  const denominator = [...state.selected].reduce((sum, code) => sum + (aum[code] || 1), 0);
  return state.holdings.map((holding) => {
    const entries = Object.entries(holding.weights).filter(([code]) => state.selected.has(code));
    const weight = denominator ? entries.reduce((sum, [code, value]) => sum + (aum[code] || 1) * value, 0) / denominator : 0;
    const breadth = state.selected.size ? entries.length / state.selected.size * 100 : 0;
    return {...holding, weight, breadth, count: entries.length, peN:pe(holding.price, holding.eps.n), peN1:pe(holding.price, holding.eps.n1), peN2:pe(holding.price, holding.eps.n2), fsUpside:upside(holding.fs.median, holding.price), yfUpside:upside(holding.yf.median, holding.price), providerGap:gap(holding.yf.median, holding.fs.median)};
  }).filter((item) => item.count > 0);
}

function filteredHoldings() {
  const term = state.search.toLowerCase();
  const rows = aggregateHoldings().filter((item) => (!term || `${item.ticker} ${item.name} ${item.sector}`.toLowerCase().includes(term)) && (state.sector === "all" || item.sector === state.sector) && (state.quality === "all" || item.quality === state.quality));
  const key = state.sortKey;
  rows.sort((left, right) => ((left[key] ?? -Infinity) - (right[key] ?? -Infinity)) * (state.sortDirection === "asc" ? 1 : -1));
  return rows;
}

function calculateStats(rows) {
  const totalWeight = rows.reduce((sum, item) => sum + item.weight, 0);
  const covered = rows.filter((item) => item.fs.median !== null && item.eps.n1 !== null);
  const coveredWeight = covered.reduce((sum, item) => sum + item.weight, 0);
  const earningsYield = covered.reduce((sum, item) => sum + item.weight / Math.max(coveredWeight, .0001) * item.eps.n1 / item.price, 0);
  return {
    aum: state.etfs.filter((item) => state.selected.has(item.code)).reduce((sum, item) => sum + item.aum, 0),
    coverage: totalWeight ? coveredWeight / totalWeight * 100 : 0,
    portfolioPe: earningsYield > 0 ? 1 / earningsYield : null,
    upside: covered.reduce((sum, item) => sum + item.weight * (item.fsUpside || 0), 0) / Math.max(coveredWeight, .0001),
    review: rows.filter((item) => item.quality !== "PASS").length,
  };
}

/* ========================================================================== */
/* 3. 畫面產生                                                               */
/* ========================================================================== */

function renderMetrics(rows) {
  const stats = calculateStats(rows);
  const data = [
    ["已選 ETF", state.selected.size, `全部 ${state.etfs.length} 檔`, "coral"],
    ["所選總規模", `$${number(stats.aum,0)}億`, "AUM · TWD", "blue"],
    ["Consensus 涵蓋", `${number(stats.coverage,1)}%`, "FactSet Target + EPS N+1", "teal"],
    ["組合 Forward P/E", `${number(stats.portfolioPe,1)}×`, "N+1 · Earnings Yield", "gold"],
    ["FS Median 空間", pct(stats.upside,1), "持股權重加權", "green"],
    ["待覆核", stats.review, "Review / Fail 個股", "coral"],
  ];
  byId("metrics").innerHTML = data.map(([label,value,note,tone]) => `<article class="metric" data-tone="${tone}"><header><span>${label}</span><i>◆</i></header><strong>${value}</strong><small>${note}</small></article>`).join("");
  byId("coverageSide").textContent = `${number(stats.coverage,1)}%`;
  byId("coverageBar").style.width = `${Math.min(stats.coverage,100)}%`;
}

function renderPerformance() {
  const rows = [...state.etfs].sort((a,b) => b.returns[7] - a.returns[7]);
  byId("performanceTable").innerHTML = `<thead><tr><th>#</th><th>代碼</th><th>ETF 名稱</th><th>風格</th><th>經理人</th>${PARAMS.returnLabels.map((label) => `<th class="num">${label}</th>`).join("")}<th class="num">規模(億)</th><th class="num">YTD流</th></tr></thead><tbody>${rows.map((item,index) => `<tr><td class="ticker">${index+1}</td><td class="ticker">${escapeHtml(item.code)}</td><td>${escapeHtml(item.name)}</td><td><span class="chip">${escapeHtml(item.style)}</span></td><td>${escapeHtml(item.manager)}</td>${item.returns.map((value) => `<td class="num ${heat(value)}">${pct(value)}</td>`).join("")}<td class="num"><b>${number(item.aum,0)}</b></td><td class="num ${item.flow>=0?"up":"down"}">${pct(item.flow)}</td></tr>`).join("")}</tbody>`;
}

function renderEtfs() {
  byId("etfTable").innerHTML = `<thead><tr><th>選</th><th>代碼</th><th>ETF 名稱</th><th>投信</th><th>經理人</th><th>風格</th><th class="num">規模(億)</th><th class="num">淨值</th><th class="num">YTD流</th><th class="num">費用率</th><th class="num">上市來</th></tr></thead><tbody>${state.etfs.map((item) => `<tr><td><input type="checkbox" data-etf-check="${escapeHtml(item.code)}" ${state.selected.has(item.code)?"checked":""}></td><td class="ticker">${escapeHtml(item.code)}</td><td>${escapeHtml(item.name)}</td><td>${escapeHtml(item.issuer)}</td><td>${escapeHtml(item.manager)}</td><td><span class="chip">${escapeHtml(item.style)}</span></td><td class="num"><b>${number(item.aum,0)}</b></td><td class="num">${number(item.nav,2)}</td><td class="num ${item.flow>=0?"up":"down"}">${pct(item.flow)}</td><td class="num">${pct(item.expense,2)}</td><td class="num up">${pct(item.since)}</td></tr>`).join("")}</tbody>`;
  all("[data-etf-check]").forEach((checkbox) => checkbox.addEventListener("change", () => toggleEtf(checkbox.dataset.etfCheck, checkbox.checked)));
}

function renderFunds() {
  byId("selectedCount").textContent = `${state.selected.size} / ${state.etfs.length}`;
  byId("fundList").innerHTML = state.etfs.map((item) => `<label class="${state.selected.has(item.code)?"selected":""}"><input type="checkbox" data-fund-check="${escapeHtml(item.code)}" ${state.selected.has(item.code)?"checked":""}><span><b>${escapeHtml(item.code)}</b>${escapeHtml(item.name)}</span></label>`).join("");
  all("[data-fund-check]").forEach((checkbox) => checkbox.addEventListener("change", () => toggleEtf(checkbox.dataset.fundCheck, checkbox.checked)));
}

function targetCells(item, provider) {
  const data = item[provider];
  const css = provider === "fs" ? "fs-cell" : "yf-cell";
  const targetUpside = provider === "fs" ? item.fsUpside : item.yfUpside;
  return `${PARAMS.targetStats.map((stat) => `<td class="${css}">${number(data[stat],1)}</td>`).join("")}<td class="${css} ${targetUpside>=0?"up":"down"}">${pct(targetUpside)}</td>`;
}

function renderHoldings() {
  const rows = filteredHoldings();
  renderMetrics(aggregateHoldings());
  const fsShown = state.provider !== "yf";
  const yfShown = state.provider !== "fs";
  byId("resultCount").textContent = `${rows.length} 檔`;
  byId("emptyState").hidden = rows.length > 0;
  const sortButton = (label,key) => `<button class="sort" data-sort="${key}">${label}${state.sortKey===key?(state.sortDirection==="desc"?" ↓":" ↑"):""}</button>`;
  byId("holdingsTable").innerHTML = `<thead><tr class="group-row"><th colspan="5">持股聚合</th><th colspan="3">價格與動作</th>${fsShown?'<th colspan="5" class="fs-group">FactSet Target</th>':""}${yfShown?'<th colspan="5" class="yf-group">YFinance Target</th>':""}<th colspan="3" class="eps-group">Consensus EPS</th><th colspan="3" class="pe-group">Forward P/E</th><th colspan="2">驗證</th></tr><tr><th>#</th><th class="company">個股</th><th>族群</th><th>${sortButton("權重","weight")}</th><th>${sortButton("廣度","breadth")}</th><th>動作</th><th>估均價</th><th>${sortButton("Adj Close","price")}</th>${fsShown?'<th class="fs-head">Low</th><th class="fs-head">Mean</th><th class="fs-head">Median</th><th class="fs-head">High</th><th class="fs-head">空間</th>':""}${yfShown?'<th class="yf-head">Low</th><th class="yf-head">Mean</th><th class="yf-head">Median</th><th class="yf-head">High</th><th class="yf-head">空間</th>':""}<th class="eps-head">N</th><th class="eps-head">N+1</th><th class="eps-head">N+2</th><th class="pe-head">${sortButton("N","peN")}</th><th class="pe-head">${sortButton("N+1","peN1")}</th><th class="pe-head">${sortButton("N+2","peN2")}</th><th>品質</th><th>差異</th></tr></thead><tbody>${rows.map((item,index) => `<tr><td class="ticker">${index+1}</td><td class="company"><b>${escapeHtml(item.name)}</b><small>${escapeHtml(item.ticker)}</small></td><td>${escapeHtml(item.sector)}</td><td><span class="bar"><b>${pct(item.weight)}</b><i><span style="width:${Math.min(item.weight/32*100,100)}%"></span></i></span></td><td>${number(item.breadth,0)}%<small> · ${item.count}/${state.selected.size}</small></td><td><span class="action">${escapeHtml(item.action)}</span></td><td>${number(item.cost,1)}</td><td><b>${number(item.price,1)}</b></td>${fsShown?targetCells(item,"fs"):""}${yfShown?targetCells(item,"yf"):""}<td class="eps-cell">${number(item.eps.n,2)}</td><td class="eps-cell">${number(item.eps.n1,2)}</td><td class="eps-cell">${number(item.eps.n2,2)}</td><td class="pe-cell">${number(item.peN,1)}×</td><td class="pe-cell"><b>${number(item.peN1,1)}×</b></td><td class="pe-cell">${item.peN2===null?"—":`${number(item.peN2,1)}×`}</td><td><span class="quality ${item.quality}">${item.quality}</span></td><td class="${Math.abs(item.providerGap||0)>PARAMS.providerGapReviewPct?"down":""}">${pct(item.providerGap)}</td></tr>`).join("")}</tbody>`;
  all("[data-sort]").forEach((button) => button.addEventListener("click", () => { if(state.sortKey===button.dataset.sort) state.sortDirection=state.sortDirection==="desc"?"asc":"desc"; else {state.sortKey=button.dataset.sort;state.sortDirection="desc";} renderHoldings(); }));
}

function renderSectorOptions() {
  const current = state.sector;
  byId("sectorSelect").innerHTML = `<option value="all">全部族群</option>${[...new Set(state.holdings.map((item)=>item.sector))].sort().map((value)=>`<option>${escapeHtml(value)}</option>`).join("")}`;
  byId("sectorSelect").value = current;
}

function renderAll() {
  renderPerformance();
  renderEtfs();
  renderFunds();
  renderSectorOptions();
  renderHoldings();
}

/* ========================================================================== */
/* 4. Adapter JSON 與事件                                                     */
/* ========================================================================== */

function normalizeFlags(value) { if(Array.isArray(value)) return value; if(typeof value==="string") { try { const parsed=JSON.parse(value); return Array.isArray(parsed)?parsed:[value]; } catch { return value?[value]:[]; } } return []; }

function loadAdapterRecords(records) {
  const grouped = new Map();
  const codes = new Set();
  records.forEach((record) => {
    const ticker = String(record.ticker ?? record.holding_ticker ?? "").trim();
    const code = String(record.etf_code ?? "UNKNOWN").trim();
    if(!ticker) return;
    codes.add(code);
    const item = grouped.get(ticker) ?? {ticker,name:String(record.company_name??record.name??ticker),sector:String(record.sector??record.industry??"未分類"),price:safeNumber(record.price_adj_close)||0,cost:safeNumber(record.estimated_cost),action:String(record.manager_action??"待分類"),quality:["PASS","FAIL"].includes(String(record.record_status))?String(record.record_status):"REVIEW",flags:normalizeFlags(record.quality_flags),weights:{},fs:{low:safeNumber(record.fs_target_low),mean:safeNumber(record.fs_target_mean),median:safeNumber(record.fs_target_median),high:safeNumber(record.fs_target_high)},yf:{low:safeNumber(record.yf_target_low),mean:safeNumber(record.yf_target_mean),median:safeNumber(record.yf_target_median),high:safeNumber(record.yf_target_high)},eps:{n:safeNumber(record.fs_eps_n_mean),n1:safeNumber(record.fs_eps_n1_mean),n2:safeNumber(record.fs_eps_n2_mean)}};
    item.weights[code] = safeNumber(record.holding_weight) || 0;
    grouped.set(ticker,item);
  });
  if(!grouped.size) throw new Error("沒有可辨識的持股欄位");
  state.holdings = [...grouped.values()];
  state.etfs = [...codes].map((code) => ETF_DATA.find((item)=>item.code===code) ?? {code,name:`主動式 ETF ${code}`,issuer:"資料來源",manager:"—",style:"未分類",aum:1,nav:0,flow:0,expense:0,since:0,returns:[0,0,0,0,0,0,0,0]});
  state.selected = new Set(codes);
}

function toggleEtf(code, checked) { if(checked) state.selected.add(code); else state.selected.delete(code); renderEtfs(); renderFunds(); renderHoldings(); }
function setAllEtfs(enabled) { state.selected = new Set(enabled ? state.etfs.map((item)=>item.code) : []); renderEtfs(); renderFunds(); renderHoldings(); }

function bindEvents() {
  all("[data-tab]").forEach((button) => button.addEventListener("click", () => {
    all("[data-tab]").forEach((item)=>item.setAttribute("aria-selected",String(item===button)));
    all("[data-panel]").forEach((panel)=>panel.hidden=panel.dataset.panel!==button.dataset.tab);
  }));
  all("[data-provider]").forEach((button) => button.addEventListener("click", () => { state.provider=button.dataset.provider; all("[data-provider]").forEach((item)=>item.classList.toggle("active",item===button)); renderHoldings(); }));
  byId("searchInput").addEventListener("input", (event)=>{state.search=event.target.value.trim();renderHoldings();});
  byId("sectorSelect").addEventListener("change",(event)=>{state.sector=event.target.value;renderHoldings();});
  byId("qualitySelect").addEventListener("change",(event)=>{state.quality=event.target.value;renderHoldings();});
  byId("loadButton").addEventListener("click",()=>byId("fileInput").click());
  byId("fileInput").addEventListener("change",async(event)=>{const file=event.target.files?.[0];if(!file)return;try{const parsed=JSON.parse(await file.text());const records=Array.isArray(parsed)?parsed:parsed.records??parsed.data??[];if(!Array.isArray(records)||!records.length)throw new Error("JSON 找不到 records");loadAdapterRecords(records);byId("dataLabel").textContent="LOADED CANDIDATE";byId("loadMessage").textContent=`${file.name} · ${records.length} 筆`;state.sector="all";renderAll();}catch(error){byId("loadMessage").textContent=`載入失敗：${error.message}`;}finally{event.target.value="";}});
  byId("resetButton").addEventListener("click",()=>{state.etfs=structuredClone(ETF_DATA);state.holdings=structuredClone(HOLDING_DATA);state.selected=new Set(ETF_DATA.map((item)=>item.code));state.search="";state.sector="all";state.quality="all";byId("searchInput").value="";byId("qualitySelect").value="all";byId("dataLabel").textContent="DEMO SNAPSHOT";byId("loadMessage").textContent="已還原示範資料";renderAll();});
  byId("selectAllButton").addEventListener("click",()=>setAllEtfs(true));
  byId("clearAllButton").addEventListener("click",()=>setAllEtfs(false));
  byId("fundAll").addEventListener("click",()=>setAllEtfs(true));
  byId("fundClear").addEventListener("click",()=>setAllEtfs(false));
  byId("jsonButton").addEventListener("click",()=>download(PARAMS.exportJsonName,JSON.stringify(filteredHoldings(),null,2),"application/json;charset=utf-8"));
  byId("csvButton").addEventListener("click",()=>{const cols=["ticker","name","sector","weight","breadth","price","fs_target_median","yf_target_median","eps_n","eps_n1","eps_n2","forward_pe_n","forward_pe_n1","forward_pe_n2","quality"];const rows=filteredHoldings().map((item)=>[item.ticker,item.name,item.sector,item.weight,item.breadth,item.price,item.fs.median,item.yf.median,item.eps.n,item.eps.n1,item.eps.n2,item.peN,item.peN1,item.peN2,item.quality]);const csv=[cols,...rows].map((row)=>row.map((value)=>`"${String(value??"").replaceAll('"','""')}"`).join(",")).join("\n");download(PARAMS.exportCsvName,`\ufeff${csv}`,"text/csv;charset=utf-8");});
}

function initialize() {
  byId("requestJson").textContent = JSON.stringify(REQUEST,null,2);
  renderAll();
  bindEvents();
}

document.addEventListener("DOMContentLoaded", initialize);

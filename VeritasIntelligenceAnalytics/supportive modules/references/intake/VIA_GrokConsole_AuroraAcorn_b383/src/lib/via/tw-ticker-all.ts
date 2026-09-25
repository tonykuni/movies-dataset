/**
 * TW_Ticker_All SSOT v0100。附件 VIA_TWTickerRegex.py 為準。
 * 只增不減：SECTION A 原定義保留（缺陷者 DORMANT），SECTION B v2 補碼，
 * SECTION C 13 類註冊表互斥分類。VRN 檔名層仍用 tw-ticker lookaround（STOCK 四碼）。
 */
export const TW_TICKER_ALL_DESC =
  "台灣 ETF 代碼具有『前置數字相同但尾碼不同』的特性，例如 00980A、00980B、00980D。使用者若僅輸入前置數字（如 00980），系統會依照 ETF 類型規則與 TWSE metadata 自動補尾碼，並轉換成正確的 TW / YF / Bloomberg 格式。主動式台股 ETF 的正式定義為：代碼以 A 結尾、管理方式為 Active、投資區域為 Domestic、每日揭露持股，且代碼區間為 00400A～00499A 或 00980A～00999A。";

export const TW_TICKER_RX_VER = "v0100";

/** SECTION A 原樣保留。^(00\\d{3})$ 只吃 5 碼，0050／006208／009800 皆 miss。 */
export const TW_TICKER_DORMANT = {
  PassiveEquityETF: /^(00\d{3})$/,
  YFinance_PassiveEquityETF: /^(00\d{3})\.(TW|TWO)$/,
  BBG_PassiveEquityETF: /^(00\d{3})\sTT$/,
} as const;

export const TW_TICKER = {
  Stock: /^([1-9]\d{3})$/,
  Preferred: /^([1-9]\d{3}[A-Z])$/,
  PassiveEquityETF4: /^(00\d{2})$/,
  PassiveEquityETF: /^(00\d{3})$/,
  PassiveEquityETFv2: /^(00\d{2,4})$/,
  ActiveEquityETF: /^(00\d{3}A)$/,
  ActiveBondETF: /^(00\d{3}D)$/,
  PassiveBondETF: /^(00\d{3}B)$/,
  BondFxETF: /^(00\d{3}C)$/,
  LeverageETF: /^(00\d{3}L)$/,
  LeverageFxETF: /^(00\d{3}M)$/,
  ReverseETF: /^(00\d{3}R)$/,
  ReverseFxETF: /^(00\d{3}S)$/,
  FuturesETF: /^(00\d{3}[UV])$/,
  BalancedETF: /^(00\d{3}T)$/,
  PassiveFxETF: /^(00\d{3}K)$/,
} as const;

export const TW_YF_TICKER = {
  Stock: /^([1-9]\d{3})\.(TW|TWO)$/i,
  Preferred: /^([1-9]\d{3}[A-Z])\.(TW|TWO)$/i,
  PassiveEquityETF4: /^(00\d{2})\.(TW|TWO)$/i,
  PassiveEquityETF: /^(00\d{3})\.(TW|TWO)$/i,
  PassiveEquityETFv2: /^(00\d{2,4})\.(TW|TWO)$/i,
  ActiveEquityETF: /^(00\d{3}A)\.(TW|TWO)$/i,
  ActiveBondETF: /^(00\d{3}D)\.(TW|TWO)$/i,
  PassiveBondETF: /^(00\d{3}B)\.(TW|TWO)$/i,
  BondFxETF: /^(00\d{3}C)\.(TW|TWO)$/i,
  LeverageETF: /^(00\d{3}L)\.(TW|TWO)$/i,
  LeverageFxETF: /^(00\d{3}M)\.(TW|TWO)$/i,
  ReverseETF: /^(00\d{3}R)\.(TW|TWO)$/i,
  ReverseFxETF: /^(00\d{3}S)\.(TW|TWO)$/i,
  FuturesETF: /^(00\d{3}[UV])\.(TW|TWO)$/i,
  BalancedETF: /^(00\d{3}T)\.(TW|TWO)$/i,
  PassiveFxETF: /^(00\d{3}K)\.(TW|TWO)$/i,
} as const;

export const TW_BB_TICKER = {
  Stock: /^([1-9]\d{3})\sTT$/,
  Preferred: /^([1-9]\d{3}[A-Z])\sTT$/,
  PassiveEquityETF4: /^(00\d{2})\sTT$/,
  PassiveEquityETF: /^(00\d{3})\sTT$/,
  PassiveEquityETFv2: /^(00\d{2,4})\sTT$/,
  ActiveEquityETF: /^(00\d{3}A)\sTT$/,
  ActiveBondETF: /^(00\d{3}D)\sTT$/,
  PassiveBondETF: /^(00\d{3}B)\sTT$/,
  BondFxETF: /^(00\d{3}C)\sTT$/,
  LeverageETF: /^(00\d{3}L)\sTT$/,
  LeverageFxETF: /^(00\d{3}M)\sTT$/,
  ReverseETF: /^(00\d{3}R)\sTT$/,
  ReverseFxETF: /^(00\d{3}S)\sTT$/,
  FuturesETF: /^(00\d{3}[UV])\sTT$/,
  BalancedETF: /^(00\d{3}T)\sTT$/,
  PassiveFxETF: /^(00\d{3}K)\sTT$/,
} as const;

/** Bloomberg 寬鬆：2330 TT Equity。不進 LOCKED 圈。 */
export const TW_BBG_LOOSE_RE =
  /^(00\d{2,4}|00\d{3}[A-DKLMRSTUV]|[1-9]\d{3}[A-Z]?)\s+TT(?:\s+Equity)?$/i;

export type TwAllKind = keyof typeof TW_TICKER;
export type TwAllForm = "TW_TICKER" | "TW_YF_TICKER" | "TW_BB_TICKER";
export type TwRxCls =
  | "STOCK"
  | "PREFERRED"
  | "ETF_ACTIVE"
  | "ETF_BOND"
  | "ETF_BOND_FX"
  | "ETF_LEVERAGE"
  | "ETF_LEVERAGE_FX"
  | "ETF_REVERSE"
  | "ETF_REVERSE_FX"
  | "ETF_FUTURES"
  | "ETF_BALANCED"
  | "ETF_PASSIVE_FX"
  | "ETF_PASSIVE";
export type TwRxFmt = "PLAIN" | "YF" | "BBG";

export type TwRxRow = {
  cls: TwRxCls;
  zh: string;
  sfx: string;
  plain: RegExp;
  yf: RegExp;
  bbg: RegExp;
  sample: string;
};

/** 附件 REGISTRY 優先序上→下。YF/BBG 此處大小寫嚴格（與 py 自測一致）。 */
export const TW_RX_REGISTRY: TwRxRow[] = [
  { cls: "STOCK", zh: "一般上市櫃公司", sfx: "-", plain: /^([1-9]\d{3})$/, yf: /^([1-9]\d{3})\.(TW|TWO)$/, bbg: /^([1-9]\d{3})\sTT$/, sample: "2330" },
  { cls: "PREFERRED", zh: "特別股", sfx: "A-Z", plain: /^([1-9]\d{3}[A-Z])$/, yf: /^([1-9]\d{3}[A-Z])\.(TW|TWO)$/, bbg: /^([1-9]\d{3}[A-Z])\sTT$/, sample: "2881A" },
  { cls: "ETF_ACTIVE", zh: "主動式 ETF", sfx: "A/D", plain: /^(00\d{3}[AD])$/, yf: /^(00\d{3}[AD])\.(TW|TWO)$/, bbg: /^(00\d{3}[AD])\sTT$/, sample: "00981A" },
  { cls: "ETF_BOND", zh: "債券型 ETF", sfx: "B", plain: /^(00\d{3}B)$/, yf: /^(00\d{3}B)\.(TW|TWO)$/, bbg: /^(00\d{3}B)\sTT$/, sample: "00679B" },
  { cls: "ETF_BOND_FX", zh: "債券型 ETF (外幣)", sfx: "C", plain: /^(00\d{3}C)$/, yf: /^(00\d{3}C)\.(TW|TWO)$/, bbg: /^(00\d{3}C)\sTT$/, sample: "00679C" },
  { cls: "ETF_LEVERAGE", zh: "槓桿型 ETF", sfx: "L", plain: /^(00\d{3}L)$/, yf: /^(00\d{3}L)\.(TW|TWO)$/, bbg: /^(00\d{3}L)\sTT$/, sample: "00631L" },
  { cls: "ETF_LEVERAGE_FX", zh: "槓桿型 ETF (外幣)", sfx: "M", plain: /^(00\d{3}M)$/, yf: /^(00\d{3}M)\.(TW|TWO)$/, bbg: /^(00\d{3}M)\sTT$/, sample: "00663M" },
  { cls: "ETF_REVERSE", zh: "反向型 ETF", sfx: "R", plain: /^(00\d{3}R)$/, yf: /^(00\d{3}R)\.(TW|TWO)$/, bbg: /^(00\d{3}R)\sTT$/, sample: "00632R" },
  { cls: "ETF_REVERSE_FX", zh: "反向型 ETF (外幣)", sfx: "S", plain: /^(00\d{3}S)$/, yf: /^(00\d{3}S)\.(TW|TWO)$/, bbg: /^(00\d{3}S)\sTT$/, sample: "00664S" },
  { cls: "ETF_FUTURES", zh: "期貨型 ETF (台幣U/外幣V)", sfx: "U/V", plain: /^(00\d{3}[UV])$/, yf: /^(00\d{3}[UV])\.(TW|TWO)$/, bbg: /^(00\d{3}[UV])\sTT$/, sample: "00635U" },
  { cls: "ETF_BALANCED", zh: "平衡型 ETF", sfx: "T", plain: /^(00\d{3}T)$/, yf: /^(00\d{3}T)\.(TW|TWO)$/, bbg: /^(00\d{3}T)\sTT$/, sample: "00980T" },
  { cls: "ETF_PASSIVE_FX", zh: "被動股票 ETF (外幣)", sfx: "K", plain: /^(00\d{3}K)$/, yf: /^(00\d{3}K)\.(TW|TWO)$/, bbg: /^(00\d{3}K)\sTT$/, sample: "00643K" },
  { cls: "ETF_PASSIVE", zh: "被動股票 ETF (v2)", sfx: "數字", plain: /^(00\d{2,4})$/, yf: /^(00\d{2,4})\.(TW|TWO)$/, bbg: /^(00\d{2,4})\sTT$/, sample: "0050" },
];

const KIND_ORDER: TwAllKind[] = [
  "Preferred",
  "ActiveEquityETF",
  "ActiveBondETF",
  "BondFxETF",
  "PassiveBondETF",
  "LeverageFxETF",
  "LeverageETF",
  "ReverseFxETF",
  "ReverseETF",
  "FuturesETF",
  "BalancedETF",
  "PassiveFxETF",
  "PassiveEquityETF4",
  "PassiveEquityETF",
  "PassiveEquityETFv2",
  "Stock",
];

const SUFFIX: Record<
  Exclude<TwAllKind, "Stock" | "Preferred" | "PassiveEquityETF" | "PassiveEquityETF4" | "PassiveEquityETFv2">,
  string
> = {
  ActiveEquityETF: "A",
  ActiveBondETF: "D",
  PassiveBondETF: "B",
  BondFxETF: "C",
  LeverageETF: "L",
  LeverageFxETF: "M",
  ReverseETF: "R",
  ReverseFxETF: "S",
  FuturesETF: "U",
  BalancedETF: "T",
  PassiveFxETF: "K",
};

export type TwAllHit = {
  kind: TwAllKind;
  form: TwAllForm;
  native: string;
  yfinance: string;
  bloomberg: string;
  board: "TW" | "TWO";
};

export type TwRxHit = {
  cls: TwRxCls;
  code: string;
  venue: "TW" | "TWO" | null;
  fmt: TwRxFmt;
};

export function stripTwWrap(raw: string): { core: string; board: "TW" | "TWO"; form: TwAllForm } {
  const s = String(raw).trim().toUpperCase().replace(/\s+/g, " ");
  const yf = s.match(/^([0-9]{4,6}[A-Z]?)\.(TW|TWO)$/);
  if (yf) return { core: yf[1]!, board: yf[2] as "TW" | "TWO", form: "TW_YF_TICKER" };
  const bb = s.match(/^([0-9]{4,6}[A-Z]?)\sTT(?:\sEQUITY)?$/);
  if (bb) return { core: bb[1]!, board: "TW", form: "TW_BB_TICKER" };
  return { core: s.replace(/\sTT$/, "").replace(/\.(TW|TWO)$/, ""), board: "TW", form: "TW_TICKER" };
}

export function classifyNative(core: string): TwAllKind | null {
  const c = core.toUpperCase();
  for (const k of KIND_ORDER) {
    if (TW_TICKER[k].test(c)) return k;
  }
  return null;
}

/** 00400A–00499A 或 00980A–00999A。 */
export function inActiveEquityRange(code: string): boolean {
  const m = code.toUpperCase().match(/^00(\d{3})A$/);
  if (!m) return false;
  const n = Number(m[1]);
  return (n >= 400 && n <= 499) || (n >= 980 && n <= 999);
}

/**
 * 主動式台股 ETF 五條件：A 結尾 · Active · Domestic · 日持股 · 區間。
 * 本台無 TWSE metadata 時：A＋區間可判定；Domestic／日持股要 LIVE。
 */
export function isActiveDomesticEquityEtf(code: string, meta?: { region?: string; style?: string; dailyHold?: boolean }): boolean {
  if (!inActiveEquityRange(code)) return false;
  if (meta) {
    if (meta.region && meta.region !== "Domestic") return false;
    if (meta.style && meta.style !== "Active") return false;
    if (meta.dailyHold === false) return false;
  }
  return true;
}

export function expandAll(native: string, board: "TW" | "TWO" = "TW"): { native: string; yfinance: string; bloomberg: string } {
  const n = native.toUpperCase();
  return {
    native: n,
    yfinance: `${n}.${board}`,
    bloomberg: `${n} TT`,
  };
}

export function classifyTwAll(raw: string): TwAllHit | null {
  const w = stripTwWrap(raw);
  const kind = classifyNative(w.core);
  if (!kind) return null;
  const board = kind === "Stock" || kind === "Preferred" ? w.board : "TW";
  const ex = expandAll(w.core, board);
  return { kind, form: w.form, native: ex.native, yfinance: ex.yfinance, bloomberg: ex.bloomberg, board };
}

/** 附件 classify()：strip 後大小寫嚴格、互斥第一命中。 */
export function classifyTwRx(ticker: string): TwRxHit | null {
  const s = String(ticker).trim();
  for (const r of TW_RX_REGISTRY) {
    const p = r.plain.exec(s);
    if (p) return { cls: r.cls, code: p[1]!, venue: null, fmt: "PLAIN" };
    const y = r.yf.exec(s);
    if (y) return { cls: r.cls, code: y[1]!, venue: y[2] as "TW" | "TWO", fmt: "YF" };
    const b = r.bbg.exec(s);
    if (b) return { cls: r.cls, code: b[1]!, venue: null, fmt: "BBG" };
  }
  return null;
}

export function deriveTw(code: string, venue: "TW" | "TWO" = "TW"): { plain: string; yfinance: string; bloomberg: string } {
  return { plain: code, yfinance: `${code}.${venue}`, bloomberg: `${code} TT` };
}

export function rxHits(raw: string): TwRxCls[] {
  const s = String(raw).trim();
  return TW_RX_REGISTRY.filter((r) => r.plain.test(s) || r.yf.test(s) || r.bbg.test(s)).map((r) => r.cls);
}

export type SuffixPlan = {
  prefix: string;
  completed: string | null;
  kind: TwAllKind | null;
  candidates: string[];
  note: string;
};

/** 僅前置數字（00980）→ 依尾碼規則補。主動股分析預設 A（若在區間）。多尾碼不猜。 */
export function completeEtfSuffix(raw: string, prefer: "A" | "all" = "A"): SuffixPlan {
  const w = stripTwWrap(raw);
  const core = w.core;
  if (TW_TICKER.Stock.test(core) || TW_TICKER.Preferred.test(core) || /[A-Z]$/.test(core)) {
    const hit = classifyTwAll(core);
    return {
      prefix: core.replace(/[A-Z]$/, ""),
      completed: hit?.native ?? core,
      kind: hit?.kind ?? null,
      candidates: [core],
      note: "已有尾碼或為股票",
    };
  }
  const prefix = core;
  if (/^00\d{4}$/.test(prefix)) {
    return { prefix, completed: prefix, kind: "PassiveEquityETFv2", candidates: [prefix], note: "六碼被動股 ETF 無尾碼 · v2" };
  }
  if (!/^00\d{3}$/.test(prefix) && !/^00\d{2}$/.test(prefix)) {
    return { prefix, completed: null, kind: null, candidates: [], note: "非 ETF 前置" };
  }
  if (/^00\d{2}$/.test(prefix) && prefix.length === 4) {
    return { prefix, completed: prefix, kind: "PassiveEquityETF4", candidates: [prefix], note: "四碼被動股 ETF 無尾碼" };
  }
  const candidates = [
    `${prefix}A`,
    `${prefix}B`,
    `${prefix}C`,
    `${prefix}D`,
    `${prefix}K`,
    `${prefix}L`,
    `${prefix}M`,
    `${prefix}R`,
    `${prefix}S`,
    `${prefix}U`,
    `${prefix}V`,
    `${prefix}T`,
    prefix,
  ];
  if (prefer === "A" && inActiveEquityRange(`${prefix}A`)) {
    return {
      prefix,
      completed: `${prefix}A`,
      kind: "ActiveEquityETF",
      candidates,
      note: "前置數字在主動股區間 · 補 A · 其餘尾碼仍列候選",
    };
  }
  return {
    prefix,
    completed: null,
    kind: null,
    candidates,
    note: "多尾碼 · 需 TWSE metadata 才能唯一補碼",
  };
}

type RxCase = { inp: string; exp: TwRxCls | null; note: string };

const RX_CASES: RxCase[] = [
  { inp: "2330", exp: "STOCK", note: "台積電 plain" },
  { inp: "2330.TW", exp: "STOCK", note: "yfinance 上市" },
  { inp: "6488.TWO", exp: "STOCK", note: "yfinance 上櫃" },
  { inp: "2330 TT", exp: "STOCK", note: "Bloomberg" },
  { inp: "2881A", exp: "PREFERRED", note: "富邦特" },
  { inp: "2882B.TW", exp: "PREFERRED", note: "國泰特乙 yfinance" },
  { inp: "00981A", exp: "ETF_ACTIVE", note: "主動統一台股增長" },
  { inp: "00981A.TW", exp: "ETF_ACTIVE", note: "主動 yfinance" },
  { inp: "00981A TT", exp: "ETF_ACTIVE", note: "主動 Bloomberg" },
  { inp: "00980D", exp: "ETF_ACTIVE", note: "主動債券型 D" },
  { inp: "00679B", exp: "ETF_BOND", note: "元大美債20年" },
  { inp: "00687B.TW", exp: "ETF_BOND", note: "國泰20年美債" },
  { inp: "00679C", exp: "ETF_BOND_FX", note: "債券外幣 C" },
  { inp: "00631L", exp: "ETF_LEVERAGE", note: "0050正2" },
  { inp: "00663M", exp: "ETF_LEVERAGE_FX", note: "槓桿外幣 M" },
  { inp: "00632R", exp: "ETF_REVERSE", note: "0050反1" },
  { inp: "00664S", exp: "ETF_REVERSE_FX", note: "反向外幣 S" },
  { inp: "00635U", exp: "ETF_FUTURES", note: "期元大S&P黃金" },
  { inp: "00682V", exp: "ETF_FUTURES", note: "期貨外幣 V" },
  { inp: "00980T", exp: "ETF_BALANCED", note: "凱基美國Top股債平衡" },
  { inp: "00643K", exp: "ETF_PASSIVE_FX", note: "深證中小 外幣" },
  { inp: "0050", exp: "ETF_PASSIVE", note: "4碼 (原regex miss)" },
  { inp: "00878", exp: "ETF_PASSIVE", note: "5碼" },
  { inp: "006208", exp: "ETF_PASSIVE", note: "6碼舊制" },
  { inp: "009800", exp: "ETF_PASSIVE", note: "6碼新制" },
  { inp: "004001", exp: "ETF_PASSIVE", note: "6碼新制第二階段" },
  { inp: "0050.TW", exp: "ETF_PASSIVE", note: "4碼 yfinance" },
  { inp: "009800 TT", exp: "ETF_PASSIVE", note: "6碼 Bloomberg" },
  { inp: "0330", exp: null, note: "首位0 非ETF前綴" },
  { inp: "233", exp: null, note: "3碼" },
  { inp: "23300", exp: null, note: "5碼純數字非00開頭" },
  { inp: "2330.TWX", exp: null, note: "錯後綴" },
  { inp: "00981a", exp: null, note: "小寫字母" },
  { inp: "2330TT", exp: null, note: "BBG 無空白" },
  { inp: "00981AB", exp: null, note: "雙字母" },
  { inp: "0098000", exp: null, note: "7碼" },
  { inp: "00980X", exp: null, note: "未定義第六碼 X" },
  { inp: "2330.TW ", exp: "STOCK", note: "尾端空白 strip" },
  { inp: "", exp: null, note: "空字串" },
];

export type TwRxSelfRow = {
  kind: "TEST" | "EXCLUSIVE" | "DERIVE" | "DIAG";
  input: string;
  expected: string;
  got: string;
  pass: boolean;
  note: string;
};

export function runTwRxSelftest(): { ok: boolean; pass: number; all: number; rows: TwRxSelfRow[] } {
  const rows: TwRxSelfRow[] = [];
  let ok = true;
  for (const c of RX_CASES) {
    const r = classifyTwRx(c.inp);
    const got = r?.cls ?? null;
    const passed = got === c.exp;
    ok = ok && passed;
    rows.push({
      kind: "TEST",
      input: c.inp,
      expected: String(c.exp),
      got: String(got),
      pass: passed,
      note: c.note,
    });
  }
  for (const c of RX_CASES) {
    if (c.exp == null) continue;
    const hits = rxHits(c.inp.trim());
    const passed = hits.length === 1;
    ok = ok && passed;
    rows.push({
      kind: "EXCLUSIVE",
      input: c.inp,
      expected: "1 hit",
      got: `${hits.length} hit(s): ${hits.join(",")}`,
      pass: passed,
      note: "互斥性",
    });
  }
  for (const [code, venue] of [
    ["2330", "TW"],
    ["6488", "TWO"],
    ["0050", "TW"],
    ["00981A", "TW"],
  ] as const) {
    const d = deriveTw(code, venue);
    const back = [classifyTwRx(d.plain), classifyTwRx(d.yfinance), classifyTwRx(d.bloomberg)];
    const passed = back.every((b) => b && b.code === code) && back[1]?.venue === venue;
    ok = ok && passed;
    rows.push({
      kind: "DERIVE",
      input: code,
      expected: "3/3 往返",
      got: JSON.stringify(d),
      pass: passed,
      note: "三態推導",
    });
  }
  for (const inp of ["0050", "006208", "009800"] as const) {
    const hit = Boolean(TW_TICKER_DORMANT.PassiveEquityETF.test(inp));
    rows.push({
      kind: "DIAG",
      input: inp,
      expected: "miss (已知缺陷)",
      got: hit ? "hit" : "miss",
      pass: true,
      note: "原 TW_PassiveEquityETFRegex ^(00\\d{3})$ → DORMANT",
    });
  }
  for (const [inp, exp] of [
    ["2330 TT Equity", true],
    ["00981A  tt equity", true],
    ["2330 TT Corp", false],
  ] as const) {
    const got = TW_BBG_LOOSE_RE.test(inp);
    const passed = got === exp;
    ok = ok && passed;
    rows.push({
      kind: "TEST",
      input: inp,
      expected: String(exp),
      got: String(got),
      pass: passed,
      note: "Bloomberg 寬鬆",
    });
  }
  const scored = rows.filter((r) => r.kind !== "DIAG");
  const pass = scored.filter((r) => r.pass).length;
  return { ok, pass, all: scored.length, rows };
}

export function twRxQc(): { id: string; metric: string; value: string; light: "ok" | "warn" | "bad"; note: string }[] {
  const st = runTwRxSelftest();
  const six = classifyTwRx("009800");
  const four = classifyTwRx("0050");
  const pref = classifyTwRx("2881A");
  const low = classifyTwRx("00981a");
  const aetf = classifyTwRx("00981A");
  return [
    { id: "RX_N", metric: "註冊表", value: `${TW_RX_REGISTRY.length} 類`, light: TW_RX_REGISTRY.length === 13 ? "ok" : "bad", note: "STOCK→ETF_PASSIVE 優先序" },
    { id: "RX_SELF", metric: "自測", value: `${st.pass}/${st.all}`, light: st.ok && st.all === 75 ? "ok" : "bad", note: "附件 75/75 · DIAG 不計 FAIL" },
    { id: "RX_V2", metric: "被動 v2", value: `${four?.cls}/${six?.cls}`, light: four?.cls === "ETF_PASSIVE" && six?.cls === "ETF_PASSIVE" ? "ok" : "bad", note: "0050／009800 · 原 5 碼 DORMANT" },
    { id: "RX_PREF", metric: "特別股", value: pref?.code ?? "—", light: pref?.cls === "PREFERRED" ? "ok" : "bad", note: "2881A 不切成 2881" },
    { id: "RX_CASE", metric: "大小寫", value: low ? "漏收" : "拒小寫", light: !low && aetf?.cls === "ETF_ACTIVE" ? "ok" : "bad", note: "00981a 拒 · 00981A 收" },
  ];
}

export { SUFFIX, KIND_ORDER };

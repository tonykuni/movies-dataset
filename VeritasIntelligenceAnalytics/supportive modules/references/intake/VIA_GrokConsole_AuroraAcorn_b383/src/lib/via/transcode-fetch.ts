/** 自動轉碼擷取：三種代碼互轉，擷取只走救回後的 YF，禁網。 */
import type { Light } from "./types.ts";
import { lookupTw } from "./vdf-mother.ts";
import { resolveTwTicker, type TwMarket } from "./tw-ticker.ts";

export type XcodeCase = {
  id: string;
  input: string;
  core: string;
  yf: string;
  bb: string;
  market: TwMarket;
  recovered: boolean;
  inUniverse: boolean;
};

export const XCODE_CASES: XcodeCase[] = [
  { id: "N2330", input: "2330", core: "2330", yf: "2330.TW", bb: "2330 TT", market: "TWSE", recovered: false, inUniverse: true },
  { id: "YF2330", input: "2330.TW", core: "2330", yf: "2330.TW", bb: "2330 TT", market: "TWSE", recovered: false, inUniverse: true },
  { id: "BB2330", input: "2330 TT", core: "2330", yf: "2330.TW", bb: "2330 TT", market: "TWSE", recovered: false, inUniverse: true },
  { id: "BAD2330", input: "2330.TWO", core: "2330", yf: "2330.TW", bb: "2330 TT", market: "TWSE", recovered: true, inUniverse: true },
  { id: "TIGHT", input: "2330TT", core: "2330", yf: "2330.TW", bb: "2330 TT", market: "TWSE", recovered: true, inUniverse: true },
  { id: "DAM", input: "2330.TX", core: "2330", yf: "2330.TW", bb: "2330 TT", market: "TWSE", recovered: true, inUniverse: true },
  { id: "N5347", input: "5347", core: "5347", yf: "5347.TWO", bb: "5347 TT", market: "TPEX", recovered: false, inUniverse: true },
  { id: "YF5347", input: "5347.TWO", core: "5347", yf: "5347.TWO", bb: "5347 TT", market: "TPEX", recovered: false, inUniverse: true },
  { id: "BAD5347", input: "5347.TW", core: "5347", yf: "5347.TWO", bb: "5347 TT", market: "TPEX", recovered: true, inUniverse: true },
  { id: "VRN2637", input: "華南投顧-2637-慧洋-KY-1141202.pdf", core: "2637", yf: "2637.TW", bb: "2637 TT", market: "TWSE", recovered: false, inUniverse: true },
];

export type XcodeRow = {
  id: string;
  input: string;
  core: string;
  fetchKey: string;
  recovered: boolean;
  fetched: boolean;
  light: Light;
  note: string;
};

export function cacheFetchKey(input: string): { key: string; recovered: boolean; core: string; market: TwMarket } | null {
  const hit = resolveTwTicker(input);
  if (!hit) return null;
  return { key: hit.yfinance, recovered: hit.recovered, core: hit.core, market: hit.market };
}

function usedWrongBoard(input: string, key: string, market: TwMarket): boolean {
  if (market === "TWSE" && /\.TWO/i.test(key)) return true;
  if (market === "TPEX" && /\.TW$/i.test(key) && !/\.TWO/i.test(key)) return true;
  if (market === "TWSE" && /\.TWO/i.test(input) && /\.TWO/i.test(key)) return true;
  if (market === "TPEX" && /\.TW(?!O)/i.test(input) && /\.TW$/i.test(key) && !/\.TWO/i.test(key)) return true;
  return false;
}

export function probeXcode(c: XcodeCase): XcodeRow {
  const hit = resolveTwTicker(c.input);
  if (!hit) {
    return { id: c.id, input: c.input, core: "", fetchKey: "", recovered: false, fetched: false, light: "bad", note: "無法轉碼" };
  }
  if (hit.core !== c.core || hit.yfinance !== c.yf || hit.bloomberg !== c.bb || hit.market !== c.market) {
    return {
      id: c.id,
      input: c.input,
      core: hit.core,
      fetchKey: hit.yfinance,
      recovered: hit.recovered,
      fetched: false,
      light: "bad",
      note: `轉碼不符 · 得 ${hit.core}/${hit.yfinance}/${hit.market}`,
    };
  }
  if (hit.recovered !== c.recovered) {
    return {
      id: c.id,
      input: c.input,
      core: hit.core,
      fetchKey: hit.yfinance,
      recovered: hit.recovered,
      fetched: false,
      light: "bad",
      note: `recovered=${hit.recovered} 期望 ${c.recovered}`,
    };
  }
  if (usedWrongBoard(c.input, hit.yfinance, hit.market)) {
    return {
      id: c.id,
      input: c.input,
      core: hit.core,
      fetchKey: hit.yfinance,
      recovered: hit.recovered,
      fetched: false,
      light: "bad",
      note: "擷取鍵仍用錯板",
    };
  }
  const mem = lookupTw(hit.core);
  if (c.inUniverse) {
    if (!mem || mem.yfinance !== hit.yfinance) {
      return {
        id: c.id,
        input: c.input,
        core: hit.core,
        fetchKey: hit.yfinance,
        recovered: hit.recovered,
        fetched: false,
        light: "bad",
        note: "宇宙 YF 與擷取鍵不一致",
      };
    }
    return {
      id: c.id,
      input: c.input,
      core: hit.core,
      fetchKey: hit.yfinance,
      recovered: hit.recovered,
      fetched: true,
      light: "ok",
      note: `CACHE 擷取 ${hit.yfinance} · ${mem.name} · 禁網`,
    };
  }
  return {
    id: c.id,
    input: c.input,
    core: hit.core,
    fetchKey: hit.yfinance,
    recovered: hit.recovered,
    fetched: false,
    light: "ok",
    note: `轉碼 ${hit.yfinance} · 宇宙未列 · 不LIVE`,
  };
}

export function runTranscodeFetchTest(cases: XcodeCase[] = XCODE_CASES): {
  rows: XcodeRow[];
  pass: number;
  fail: number;
  fetchOk: number;
  total: number;
  ok: boolean;
  note: string;
} {
  const rows = cases.map(probeXcode);
  const fail = rows.filter((r) => r.light === "bad").length;
  const pass = rows.filter((r) => r.light === "ok").length;
  const fetchOk = rows.filter((r) => r.fetched).length;
  return {
    rows,
    pass,
    fail,
    fetchOk,
    total: rows.length,
    ok: fail === 0 && pass === rows.length,
    note: `轉碼 ${pass}/${rows.length} · CACHE 擷取 ${fetchOk} · 禁網`,
  };
}

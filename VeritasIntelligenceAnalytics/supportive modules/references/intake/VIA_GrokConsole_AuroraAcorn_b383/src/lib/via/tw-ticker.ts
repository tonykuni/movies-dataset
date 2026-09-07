import { YEAR_SUSPECT } from "./knowledge.ts";
import type { Light } from "./types.ts";
import { TPEX_SET, TWSE_SET } from "./vdf-mother.ts";

/**
 * TW_STOCK_TICKER: four digits, first digit not 0.
 * Year-band 2021–2030 is NOT baked into the regex (that killed 2027 大成鋼).
 * Disambiguate with official list + 年/季 cues + CJK corroboration.
 */
/** CGE C8：Python \\b 把 CJK 當字元，改 lookaround。第一碼不可 0。 */
export const TW_CORE_RE = /(?<![0-9A-Za-z.])([1-9]\d{3})(?![0-9A-Za-z.])/;
export const TW_YF_RE = /(?<![0-9A-Za-z.])([1-9]\d{3})\.(TW|TWO)(?![A-Za-z0-9])/i;
export const TW_BB_RE = /(?<![0-9A-Za-z])([1-9]\d{3})\s+TT(?:\s+Equity)?(?![A-Za-z0-9])/;
export const TW_BB_TIGHT_RE = /([1-9]\d{3})TT/;
export const TW_YF_DAMAGED_RE = /(?<![0-9A-Za-z.])([1-9]\d{3})\.[A-Za-z]{1,4}(?![A-Za-z0-9])/;

export const OFFICIAL_VENUES = ["TWSE", "TPEX", "MOPS", "TDCC"] as const;

/** 2021–2030 年碼陷阱裡的真實上市櫃。 */
export const YEAR_BAND_REAL: Record<string, string> = {
  "2021": "中鋼構",
  "2022": "聚亨",
  "2023": "燁輝",
  "2024": "志聯",
  "2025": "千興",
  "2027": "大成鋼",
  "2028": "威致",
  "2029": "盛餘",
  "2030": "彰源",
};

const DATE_CUES = ["年", "Q1", "Q2", "Q3", "Q4", "H1", "H2", "FY", "上半年", "下半年", "第一季", "第二季", "第三季", "第四季"];

export type NameTok = { tok: string; kind: "CJK" | "LATIN" | "DIGIT" };
export type YearVerdict = "TICKER" | "YEAR" | "AMBIGUOUS";

export type TwMarket = "TWSE" | "TPEX";
export type TwKind = "native" | "yfinance" | "bloomberg";

export type TwForms = {
  native: string;
  market: TwMarket;
  yfinance: string;
  bloomberg: string;
  venues: string;
};

export type TwHit = TwForms & {
  core: string;
  kind: TwKind;
  recovered: boolean;
  from: string;
  two: string;
  tw: string;
};

function charKind(ch: string): NameTok["kind"] | "OTHER" {
  if (ch >= "0" && ch <= "9") return "DIGIT";
  const o = ch.charCodeAt(0);
  if ((o >= 0x4e00 && o <= 0x9fff) || (o >= 0x3400 && o <= 0x4dbf) || (o >= 0xf900 && o <= 0xfaff)) return "CJK";
  const u = ch.toUpperCase();
  if (u >= "A" && u <= "Z") return "LATIN";
  return "OTHER";
}

export function tokenizeFilename(name: string): NameTok[] {
  const stem = name.replace(/\.(pdf|docx?|pptx?|png|jpe?g|tiff?|webp|heic)$/i, "");
  const norm = stem.normalize("NFKC").replace(/[\s._\-－—–／/\\|,:;()[\]{}【】「」『』《》<>]+/g, " ");
  const out: NameTok[] = [];
  for (const chunk of norm.split(/\s+/).filter(Boolean)) {
    let cur = "";
    let kind: NameTok["kind"] | null = null;
    for (const ch of chunk) {
      const k = charKind(ch);
      if (k === "OTHER") {
        if (cur && kind) out.push({ tok: cur, kind });
        cur = "";
        kind = null;
        continue;
      }
      if (kind == null || k === kind) {
        cur += ch;
        kind = k;
      } else {
        out.push({ tok: cur, kind });
        cur = ch;
        kind = k;
      }
    }
    if (cur && kind) out.push({ tok: cur, kind });
  }
  return out;
}

export function disambiguateYear(tok: string, neighbor = "", firstPage?: string): { verdict: YearVerdict; conf: number; reason: string } {
  if (!YEAR_SUSPECT.test(tok)) return { verdict: "TICKER", conf: 1, reason: "非 2021–2030" };
  if (firstPage && tok === firstPage) return { verdict: "TICKER", conf: 0.97, reason: "首頁資訊區一致" };
  if (TWSE_SET.has(tok) || TPEX_SET.has(tok)) return { verdict: "TICKER", conf: 0.9, reason: "官方宇宙" };
  const upper = neighbor.toUpperCase();
  const packed = neighbor.replace(/[\s._\-]+/g, "");
  if (DATE_CUES.some((c) => neighbor.includes(c) || upper.includes(c) || packed.toUpperCase().includes(c))) {
    return { verdict: "YEAR", conf: 0.9, reason: "年/季/FY 鄰字" };
  }
  const name = YEAR_BAND_REAL[tok];
  if (name && neighbor.includes(name)) return { verdict: "TICKER", conf: 0.85, reason: `真碼 ${name} ＋中文佐證` };
  if (name) return { verdict: "AMBIGUOUS", conf: 0.5, reason: `真碼 ${name} 無佐證` };
  return { verdict: "AMBIGUOUS", conf: 0.4, reason: "年碼帶無佐證" };
}

export function okCore(core: string): boolean {
  if (!/^[1-9]\d{3}$/.test(core)) return false;
  if (!YEAR_SUSPECT.test(core)) return true;
  return Boolean(TWSE_SET.has(core) || TPEX_SET.has(core) || YEAR_BAND_REAL[core]);
}

export function marketOf(core: string, hint?: "TW" | "TWO"): TwMarket {
  if (TPEX_SET.has(core) && !TWSE_SET.has(core)) return "TPEX";
  if (TWSE_SET.has(core)) return "TWSE";
  if (hint === "TWO") return "TPEX";
  return "TWSE";
}

export function yfTicker(core: string, market: TwMarket): string {
  return market === "TPEX" ? `${core}.TWO` : `${core}.TW`;
}

export function expandTw(core: string, hint?: "TW" | "TWO"): TwForms | null {
  if (!okCore(core)) return null;
  const market = marketOf(core, hint);
  return {
    native: core,
    market,
    yfinance: yfTicker(core, market),
    bloomberg: `${core} TT`,
    venues: OFFICIAL_VENUES.join("/"),
  };
}

function pack(core: string, kind: TwKind, recovered: boolean, from: string, hint?: "TW" | "TWO"): TwHit | null {
  const forms = expandTw(core, hint);
  if (!forms) return null;
  return {
    ...forms,
    core,
    kind,
    recovered,
    from,
    tw: forms.market === "TWSE" ? forms.yfinance : "—",
    two: forms.market === "TPEX" ? forms.yfinance : "—",
  };
}

function pickNativeFromName(text: string): TwHit | null {
  const toks = tokenizeFilename(text);
  const neighbor = `${text} ${toks.map((t) => t.tok).join(" ")}`;
  const digits = toks.filter((t) => t.kind === "DIGIT" && t.tok.length === 4);
  const ordered = [
    ...digits.filter((d) => !YEAR_SUSPECT.test(d.tok)),
    ...digits.filter((d) => YEAR_SUSPECT.test(d.tok)),
  ];
  for (const d of ordered) {
    const v = disambiguateYear(d.tok, neighbor);
    if (v.verdict !== "TICKER") continue;
    if (!okCore(d.tok)) continue;
    return pack(d.tok, "native", false, d.tok);
  }
  return null;
}

export function resolveTwTicker(text: string): TwHit | null {
  const yf = text.match(TW_YF_RE);
  if (yf && okCore(yf[1]!)) {
    const core = yf[1]!;
    const suffix = /two/i.test(yf[2]!) ? "TWO" : "TW";
    const known = TWSE_SET.has(core) ? "TWSE" : TPEX_SET.has(core) ? "TPEX" : null;
    const wrong = (known === "TWSE" && suffix === "TWO") || (known === "TPEX" && suffix === "TW");
    return pack(core, "yfinance", Boolean(wrong), yf[0], wrong ? undefined : suffix);
  }

  const bb = text.match(TW_BB_RE);
  if (bb && okCore(bb[1]!)) return pack(bb[1]!, "bloomberg", false, bb[0]);

  const tight = text.match(TW_BB_TIGHT_RE);
  if (tight && okCore(tight[1]!)) return pack(tight[1]!, "bloomberg", true, tight[0]);

  const damaged = text.match(TW_YF_DAMAGED_RE);
  if (damaged && okCore(damaged[1]!)) return pack(damaged[1]!, "yfinance", true, damaged[0]);

  const fromName = pickNativeFromName(text);
  if (fromName) return fromName;

  const tokens = text.split(/[_\-\s./]+/);
  for (const tok of tokens) {
    if (okCore(tok) && disambiguateYear(tok, text).verdict === "TICKER") return pack(tok, "native", false, tok);
  }

  const native = text.match(TW_CORE_RE);
  if (native && okCore(native[1]!) && disambiguateYear(native[1]!, text).verdict === "TICKER") {
    return pack(native[1]!, "native", false, native[0]);
  }

  return null;
}

export function extractTwCore(text: string): string {
  return resolveTwTicker(text)?.core ?? "";
}

export function sameCompany(a: string, b: string): boolean {
  const x = extractTwCore(a);
  const y = extractTwCore(b);
  return Boolean(x && x === y);
}

export function triCodeCheck(filenameTicker: string, raw?: string, yf?: string, bbg?: string): {
  verdict: "PASS" | "FAIL";
  checks: { code: string; value: string; ok: boolean }[];
} {
  const checks: { code: string; value: string; ok: boolean }[] = [];
  const add = (code: string, value: string | undefined, ok: boolean) => {
    if (value == null) return;
    checks.push({ code, value, ok });
  };
  add("TW_TICKER", raw, Boolean(raw && TW_CORE_RE.test(raw) && extractTwCore(raw) === filenameTicker));
  add("TW_YFINANCE", yf, Boolean(yf && TW_YF_RE.test(yf) && extractTwCore(yf) === filenameTicker));
  add("TW_BLOOMBERG", bbg, Boolean(bbg && TW_BB_RE.test(bbg) && extractTwCore(bbg) === filenameTicker));
  return { verdict: checks.every((c) => c.ok) ? "PASS" : "FAIL", checks };
}

export function tickerFilenameQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const steel = resolveTwTicker("大成鋼-2027-個股.pdf");
  const year = resolveTwTicker("review_2024_notes.pdf");
  const fy = resolveTwTicker("2454_FY2024_annual_report.pdf");
  const tri = triCodeCheck("2330", "2330", "2330.TW", "2330 TT");
  const toks = tokenizeFilename("台積電2330_FY2024.pdf");
  const baked = /202\[1-9\]|2030/.test(String(TW_CORE_RE));
  return [
    { id: "FN_RE", metric: "年碼不進 regex", value: baked ? "負向前瞻" : "無負向前瞻", light: baked ? "bad" : "ok", note: "2027 大成鋼不被剔除" },
    { id: "FN_STEEL", metric: "真碼＋中文", value: steel?.core ?? "—", light: steel?.core === "2027" ? "ok" : "bad", note: YEAR_BAND_REAL["2027"] ?? "大成鋼" },
    { id: "FN_YEAR", metric: "日期檔無名碼", value: year ? year.core : "空", light: year ? "bad" : "ok", note: "review_2024_notes 不抽 2024" },
    { id: "FN_FY", metric: "FY 鄰字", value: fy?.core ?? "—", light: fy?.core === "2454" ? "ok" : "bad", note: "2454_FY2024 抽 2454 不抽 2024" },
    { id: "FN_TRI", metric: "三碼對帳", value: tri.verdict, light: tri.verdict === "PASS" ? "ok" : "bad", note: "TW / YF / BB 前四碼一致" },
    { id: "FN_TOK", metric: "檔名切詞", value: String(toks.length), light: toks.some((t) => t.kind === "CJK") && toks.some((t) => t.tok === "2330") ? "ok" : "bad", note: "CJK/LATIN/DIGIT 分段" },
  ];
}

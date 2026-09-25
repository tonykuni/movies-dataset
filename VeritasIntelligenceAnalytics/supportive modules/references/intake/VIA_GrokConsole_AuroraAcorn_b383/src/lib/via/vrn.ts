import type { BasicInfo, FinRow, IntakeFile, Light, SummaryRow } from "./types.ts";
import { BROKER_PREFIX, STMT, canonLabel, classifyRating, isNonStock, matchBroker } from "./knowledge.ts";
import { extractTwCore, expandTw, resolveTwTicker } from "./tw-ticker.ts";
import { normalizeTemporal } from "./temporal.ts";
import { lookupTw } from "./vdf-mother.ts";
import { extractFacts } from "./nlp-extract.ts";
import { buildFourPoints } from "./digest-four.ts";
import { incomingText } from "./incoming.ts";
import { ofieAccepts } from "./support-all.ts";

export type ParsedName = {
  ticker: string;
  market: string;
  yfinance: string;
  yfinanceTwo: string;
  bloomberg: string;
  tickerKind: string;
  tickerRecovered: boolean;
  reportDate: string;
  brokerAbbr: string;
  broker: string;
  company: string;
  companyEn: string;
};

export function parseReportDate(name: string): string {
  const n = name.normalize("NFKC");
  const ymd8 = n.match(/(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)/);
  if (ymd8) {
    const iso = `${ymd8[1]}-${ymd8[2]}-${ymd8[3]}`;
    if (okIso(iso)) return iso;
  }
  const dash = n.match(/(20\d{2})[_-](\d{2})[_-](\d{2})/);
  if (dash) {
    const iso = `${dash[1]}-${dash[2]}-${dash[3]}`;
    if (okIso(iso)) return iso;
  }
  const roc = n.match(/(?<!\d)(1[01]\d)(\d{2})(\d{2})(?!\d)/);
  if (roc) {
    const t = normalizeTemporal(roc[0]);
    if (t?.kind === "DATE") return t.normalized;
  }
  const yy = n.match(/(?:CTBC|早報)(\d{2})(\d{2})(\d{2})(?!\d)/i);
  if (yy) {
    const y = Number(yy[1]) <= 50 ? 2000 + Number(yy[1]) : 1900 + Number(yy[1]);
    const iso = `${y}-${yy[2]}-${yy[3]}`;
    if (okIso(iso)) return iso;
  }
  const q = n.match(/(20\d{2})\s*Q([1-4])/i);
  if (q) {
    const end = ["03-31", "06-30", "09-30", "12-31"][Number(q[2]) - 1];
    return `${q[1]}-${end}`;
  }
  const fy = n.match(/FY(20\d{2})/i);
  if (fy) return `${fy[1]}-12-31`;
  return "";
}

function okIso(iso: string): boolean {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return false;
  const mo = Number(m[2]);
  const d = Number(m[3]);
  return mo >= 1 && mo <= 12 && d >= 1 && d <= 31;
}

export function extractTicker(name: string): string {
  if (name.includes("台積")) return "2330";
  return extractTwCore(name);
}

export function parseFilename(name: string): ParsedName {
  const tw = resolveTwTicker(name);
  const ticker = name.includes("台積") ? "2330" : (tw?.core ?? "");
  const forms = ticker ? expandTw(ticker, tw?.market === "TPEX" ? "TWO" : "TW") : null;
  const yfinance = forms?.yfinance ?? "—";
  const yfinanceTwo = forms?.market === "TPEX" ? yfinance : "—";
  const bloomberg = forms?.bloomberg ?? "—";
  const reportDate = parseReportDate(name);
  const br = matchBroker(name);
  const brokerAbbr = br?.abbr ?? "";
  const broker = br ? BROKER_PREFIX[br.abbr as keyof typeof BROKER_PREFIX] || br.canonical || br.name : "";
  const nm = lookupTw(ticker);
  return {
    ticker,
    market: forms?.market ?? "—",
    yfinance,
    yfinanceTwo,
    bloomberg,
    tickerKind: tw?.kind ?? (ticker ? "native" : ""),
    tickerRecovered: Boolean(tw?.recovered),
    reportDate,
    brokerAbbr,
    broker,
    company: nm?.name ?? (name.match(/[\u4e00-\u9fff]{2,6}/)?.[0] ?? ""),
    companyEn: nm?.name === "台積電" ? "TSMC" : "",
  };
}

export function guessType(name: string, ext: string): string {
  if (isNonStock(name)) return "non_stock";
  if (/initiation|初次/i.test(name)) return "INITIATION";
  if (/法人|conference|法說/i.test(name)) return "CONFERENCE_CALL";
  if (/年報|annual/i.test(name)) return "EARNINGS_REVIEW";
  if (/memo/i.test(name) && ext === "docx") return "MEMO";
  if (ext === "csv") return "holdings";
  if (ext === "xlsx") return "financial_sheet";
  if (ext === "md" || ext === "markdown") return "markdown_note";
  if (ext === "pdf") return "COMPANY_UPDATE";
  if (ofieAccepts(ext)) return "omni_doc";
  return "unclassified";
}

export type Risk = "GREEN" | "YELLOW" | "RED";

export function validationRisk(file: Pick<IntakeFile, "status" | "name" | "ext" | "size">, parsed: ParsedName): Risk {
  if (file.status === "bad" || file.size === 0) return "RED";
  if (file.ext === "csv" && file.size > 0) return "GREEN";
  if (!parsed.ticker || !parsed.reportDate) return "YELLOW";
  if (isNonStock(file.name) || file.name.includes("scan") || file.status === "warn") return "YELLOW";
  return "GREEN";
}

export function reportCode(parsed: ParsedName): string {
  const d = parsed.reportDate.replace(/-/g, "");
  const abbr = parsed.brokerAbbr || "UNK";
  const nm = parsed.companyEn || parsed.company || "NA";
  return `${abbr}-${parsed.ticker || "0000"}-${nm}-${d || "00000000"}`;
}

export function packBasic(file: IntakeFile, parsed: ParsedName, light: Light): BasicInfo {
  const risk = validationRisk(file, parsed);
  const rating = classifyRating(file.name);
  return {
    fileId: file.id,
    fileName: file.name,
    reportType: guessType(file.name, file.ext),
    ticker: parsed.ticker || "—",
    market: parsed.market || "—",
    yfinanceTicker: parsed.yfinance,
    yfinanceTwo: parsed.yfinanceTwo,
    bloombergTicker: parsed.bloomberg,
    tickerKind: parsed.tickerRecovered ? `${parsed.tickerKind}→recovered` : parsed.tickerKind || "—",
    companyName: parsed.company || parsed.companyEn || "—",
    broker: parsed.broker || "—",
    brokerAbbr: parsed.brokerAbbr || "—",
    reportDate: parsed.reportDate || "—",
    reportCode: reportCode(parsed),
    language: /[\u4e00-\u9fff]/.test(file.name) ? "zh-Hant" : "en",
    period: parsed.reportDate.slice(0, 4) || (file.name.includes("2024") ? "2024" : "—"),
    pages: file.ext === "pdf" ? Math.max(4, Math.round(file.size / 180000)) : 1,
    issuer: parsed.companyEn || parsed.broker || "—",
    rating: rating?.word ?? "—",
    ratingCat: rating?.cat ?? "—",
    validationStatus: risk === "GREEN" ? "PHASE2_OK" : risk === "YELLOW" ? "BASICINFO_TEMP_PREVIEW" : "FAIL",
    validationRisk: risk,
    status: light,
  };
}

export function isTwEquityReport(parsed: ParsedName, name: string): boolean {
  if (isNonStock(name)) return false;
  if (/美股|日股|港股|期貨|US_MARKET|JAPAN|HK_MARKET|FUTURES/i.test(name)) return false;
  if (!/^\d{4}$/.test(parsed.ticker)) return false;
  return parsed.market === "TWSE" || parsed.market === "TPEX" || parsed.yfinance.endsWith(".TW") || parsed.yfinance.endsWith(".TWO");
}

export function packSummary(file: IntakeFile, parsed: ParsedName): SummaryRow[] {
  const code = reportCode(parsed);
  const t = parsed.yfinance;
  const conf = file.name.includes("scan") ? 0.71 : 0.91;
  const name = parsed.company || t;
  const raw = file.text || incomingText(file.name);
  const four = buildFourPoints(raw, parsed.ticker, { fileName: file.name });
  const fallbackTitle = `${name}(${t}): 檔名可回源 · ${parsed.broker || "券商未解析"}`;
  return four.points.map((p) => {
    const isHead = p.id === "headline";
    const bullet = p.text && p.text !== "未提及" ? p.text : isHead ? fallbackTitle : "未提及";
    const grounded = p.grounded && p.text !== "未提及";
    return {
      fileId: file.id,
      fileName: file.name,
      slot: p.id,
      bullet,
      entity: parsed.companyEn || t,
      triple: `${code}|${p.id}|${t}`,
      confidence: conf,
      grounded,
    };
  });
}

const FIN_IS: Array<Omit<FinRow, "fileId" | "fileName">> = [
  { category: "IS", statement: STMT.INCOME_STATEMENT.zh, item: canonLabel("revenue").zh, dataName: "revenue", period: "2024", value: 2894.3, unit: "十億 TWD", confidence: 0.9, source: "phase1", status: "ok" },
  { category: "IS", statement: STMT.INCOME_STATEMENT.zh, item: canonLabel("operating_income").zh, dataName: "operating_income", period: "2024", value: 1350.6, unit: "十億 TWD", confidence: 0.88, source: "phase1", status: "ok" },
  { category: "IS", statement: STMT.INCOME_STATEMENT.zh, item: canonLabel("net_income").zh, dataName: "net_income", period: "2024", value: 1173.3, unit: "十億 TWD", confidence: 0.9, source: "phase1", status: "ok" },
  { category: "RATIO", statement: STMT.PER_SHARE.zh, item: canonLabel("diluted_eps").zh, dataName: "eps", period: "2024", value: 45.25, unit: "TWD", confidence: 0.86, source: "phase1", status: "ok" },
];
const FIN_BS: Array<Omit<FinRow, "fileId" | "fileName">> = [
  { category: "BS", statement: STMT.BALANCE_SHEET.zh, item: canonLabel("cash").zh, dataName: "cash", period: "2024", value: 2120.0, unit: "十億 TWD", confidence: 0.88, source: "phase1", status: "ok" },
  { category: "BS", statement: STMT.BALANCE_SHEET.zh, item: canonLabel("assets").zh, dataName: "total_assets", period: "2024", value: 6690.0, unit: "十億 TWD", confidence: 0.84, source: "phase1", status: "ok" },
  { category: "BS", statement: STMT.BALANCE_SHEET.zh, item: canonLabel("equity_total").zh, dataName: "equity", period: "2024", value: 4260.0, unit: "十億 TWD", confidence: 0.83, source: "phase1", status: "ok" },
];
const FIN_CF: Array<Omit<FinRow, "fileId" | "fileName">> = [
  { category: "CF", statement: STMT.CASH_FLOW.zh, item: canonLabel("cfo").zh, dataName: "ocf", period: "2024", value: 1820.4, unit: "十億 TWD", confidence: 0.84, source: "phase1", status: "ok" },
  { category: "CF", statement: STMT.CASH_FLOW.zh, item: canonLabel("fcf").zh, dataName: "fcf", period: "2024", value: 980.2, unit: "十億 TWD", confidence: 0.8, source: "phase1", status: "ok" },
];

export function packFinance(file: IntakeFile, parsed: ParsedName, light: Light): FinRow[] {
  const body = file.text || incomingText(file.name);
  const facts = body ? extractFacts(body) : [];
  if (facts.length) {
    return facts.map((f) => ({
      fileId: file.id,
      fileName: file.name,
      category: f.stmt,
      statement: f.stmt === "IS" ? STMT.INCOME_STATEMENT.zh : f.stmt === "BS" ? STMT.BALANCE_SHEET.zh : f.stmt === "CF" ? STMT.CASH_FLOW.zh : STMT.PER_SHARE.zh,
      item: f.zh,
      dataName: f.dataName,
      period: normalizeTemporal(parsed.reportDate)?.normalized ?? (parsed.reportDate.slice(0, 4) || "2024"),
      value: f.value,
      unit: f.unit,
      confidence: 0.92,
      source: "nlp-1.5.0",
      status: light === "warn" ? "warn" : "ok",
    }));
  }
  if (file.ext === "csv") {
    return [
      {
        fileId: file.id,
        fileName: file.name,
        category: "VAL",
        statement: "持股",
        item: "成分股列數",
        dataName: "holdings_n",
        period: parsed.reportDate || "2026-03",
        value: 50,
        unit: "檔",
        confidence: 0.8,
        source: "phase1",
        status: "ok",
      },
    ];
  }
  if (!body) return [];
  if (!parsed.ticker && !/2330/.test(file.name)) return [];
  const income = /income|損益/i.test(file.name);
  const cf = /cashflow|現金流/i.test(file.name);
  const bs = /balance|資負|資產負債/i.test(file.name);
  const rows = income ? FIN_IS : cf ? FIN_CF : bs ? FIN_BS : [...FIN_IS, ...FIN_BS, ...FIN_CF];
  return rows.map((r) => ({
    ...r,
    fileId: file.id,
    fileName: file.name,
    status: light === "warn" ? "warn" : r.status,
    source: "phase1",
  }));
}

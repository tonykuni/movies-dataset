/** 一題四點：P1 上漲空間（報告或 SSOT 目標價 × VDF adj close）· P2 n～n+3 稀釋 EPS · P3/P4 首頁其餘。K5 可空。不發明、不平均。 */
import { DIGEST_SLOTS } from "./knowledge.ts";
import { gleBodyText } from "./vrn-layout.ts";
import { vrnUpside, vrnYoy } from "./vrn-method.ts";
import { VRN_SSOT_RECS } from "./vrn-ssot-cache.ts";

export const ADJ_CLOSE_CACHE: Record<string, { date: string; adj: number; src: string }> = {
  "2330": { date: "2026-08-27", adj: 1200, src: "VDF_CACHE" },
  "2317": { date: "2026-08-27", adj: 185, src: "VDF_CACHE" },
  "2454": { date: "2026-08-27", adj: 1420, src: "VDF_CACHE" },
  "2303": { date: "2026-08-27", adj: 48.5, src: "VDF_CACHE" },
  "2637": { date: "2026-08-27", adj: 72.4, src: "VDF_CACHE" },
};

export type AdjPx = { date: string; adj: number; src: string };
export type FourOpts = { adj?: Record<string, AdjPx>; fileName?: string };

const USED_LABEL = /^(標題|核心結論|目標價|評價方式|基於|主要原因|券商|日期)[:：]/;

export type DigestPoint = { id: string; zh: string; text: string; grounded: boolean };

function grab(text: string, re: RegExp): string {
  const m = text.match(re);
  return m?.[1]?.trim().slice(0, 180) ?? "";
}

export function extractTargetPrice(text: string): number | null {
  const m = text.match(/目標價[:：]?\s*([\d,.]+)\s*元?/);
  if (!m) return null;
  const n = Number(m[1]!.replace(/,/g, ""));
  return Number.isFinite(n) ? n : null;
}

export function extractValMethod(text: string): string {
  return grab(text, /評價方式[:：]\s*(.+)/);
}

export function extractBasis(text: string): string {
  return grab(text, /基於[:：]\s*(.+)/);
}

export function extractReason(text: string): string {
  return grab(text, /主要原因[:：]\s*(.+)/);
}

export function extractEpsYears(text: string): { year: number; eps: number }[] {
  const out: { year: number; eps: number }[] = [];
  const seen = new Set<number>();
  const re = /(20[2-3]\d)\s*[:：|]?\s*(?:稀釋)?(?:每股盈餘|EPS)?\s*([\d.]+)/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    const year = Number(m[1]);
    const eps = Number(m[2]);
    if (!seen.has(year) && Number.isFinite(eps)) {
      seen.add(year);
      out.push({ year, eps });
    }
  }
  const table = text.match(/稀釋每股盈餘\s*\|\s*([\d.]+)/);
  if (table && !out.length) {
    out.push({ year: 2024, eps: Number(table[1]) });
  }
  return out.sort((a, b) => a.year - b.year);
}

function firstPage(text: string): string {
  const body = gleBodyText(text);
  const cut = body.split(/\f|\n頁\s*2\b|\n-{3,}\n/)[0] ?? body;
  return cut.split(/\r?\n/).slice(0, 48).join("\n");
}

export function remainderTwo(text: string): [string, string] {
  const page = firstPage(text);
  const keep = page
    .split(/\r?\n/)
    .map((ln) => ln.trim())
    .filter((ln) => ln && !USED_LABEL.test(ln) && !/^20[2-3]\d\s+稀釋/.test(ln) && !ln.startsWith("|") && !/^[-:|\s]+$/.test(ln) && !/^科目/.test(ln));
  if (!keep.length) return ["", ""];
  const mid = Math.ceil(keep.length / 2);
  return [keep.slice(0, mid).join(" "), keep.slice(mid).join(" ")];
}

export function formatPct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

export function ssotTarget(fileName: string): { tp: number; raw: string } | null {
  const rec = VRN_SSOT_RECS.find((r) => r.doc === fileName);
  if (!rec?.tp) return null;
  const n = Number(String(rec.tp).split(";")[0]);
  return Number.isFinite(n) ? { tp: n, raw: rec.tp } : null;
}

export function buildFourPoints(text: string, ticker: string, opts: FourOpts = {}): {
  title: string;
  points: DigestPoint[];
} {
  const page = firstPage(text);
  const title = grab(page, /(?:標題|核心結論)[:：]\s*(.+)/);
  const bodyTp = extractTargetPrice(page);
  const ssot = opts.fileName ? ssotTarget(opts.fileName) : null;
  const tp = bodyTp ?? ssot?.tp ?? null;
  const tpSrc = bodyTp != null ? "報告正文" : ssot ? "VRN_SSOT" : "";
  const method = extractValMethod(page);
  const basis = extractBasis(page);
  const px = opts.adj?.[ticker] ?? ADJ_CLOSE_CACHE[ticker];
  const up = tp != null && px ? vrnUpside(tp, px.adj) : null;

  let k1 = "未提及";
  let g1 = false;
  if (tp != null && px && up != null) {
    const multi = ssot && ssot.raw.includes(";") && bodyTp == null ? ` · 列 ${ssot.raw} 不平均` : "";
    k1 = `潛在上漲空間 ${formatPct(up)}（最新 adj close ${px.date} ${px.adj}元 ${px.src}）· 目標價 ${tp}元（${tpSrc}）${multi} · 評價方式 ${method || "未提及"} · 基於 ${basis || "未提及"}`;
    g1 = true;
  } else if (tp != null) {
    k1 = `目標價 ${tp}元（${tpSrc}）· 上漲空間未算（該檔 adj close 不在 VDF 價湖 CACHE）· 評價方式 ${method || "未提及"} · 基於 ${basis || "未提及"}`;
    g1 = true;
  }

  const eps = extractEpsYears(page);
  const reason = extractReason(page);
  let k2 = "未提及";
  let g2 = false;
  if (eps.length) {
    const n = eps[0]!.year;
    const span = [0, 1, 2, 3].map((i) => {
      const hit = eps.find((e) => e.year === n + i);
      return hit ? `${hit.year} ${hit.eps}` : `${n + i} 未提及`;
    });
    const yoyBits = [];
    for (let i = 1; i < eps.length; i++) {
      const y = vrnYoy(eps[i]!.eps, eps[i - 1]!.eps);
      yoyBits.push(y.value == null ? `${eps[i]!.year} YoY ${y.state}` : `${eps[i]!.year} YoY ${formatPct(y.value)}`);
    }
    k2 = `稀釋EPS ${span.join("、")} · ${yoyBits.join("；") || "YoY 未算"} · 主要原因 ${reason || "未提及"}`;
    g2 = true;
  }

  const [a, b] = remainderTwo(page);
  const byId: Record<string, { text: string; grounded: boolean }> = {
    headline: { text: title, grounded: Boolean(title) },
    K1: { text: k1, grounded: g1 },
    K2: { text: k2, grounded: g2 },
    K3: { text: a || "未提及", grounded: Boolean(a) },
    K4: { text: b || "未提及", grounded: Boolean(b) },
    K5: { text: "未提及", grounded: false },
  };

  return {
    title,
    points: [{ id: "headline", zh: "標題" }, ...DIGEST_SLOTS].map((s) => ({
      id: s.id,
      zh: s.zh,
      text: byId[s.id]?.text || "未提及",
      grounded: Boolean(byId[s.id]?.grounded),
    })),
  };
}

export const FOUR_POINT_SLOTS = [
  { id: "P1", digest: "K1", zh: "潛在上漲空間" },
  { id: "P2", digest: "K2", zh: "稀釋EPS n～n+3" },
  { id: "P3", digest: "K3", zh: "首頁其餘甲" },
  { id: "P4", digest: "K4", zh: "首頁其餘乙" },
] as const;

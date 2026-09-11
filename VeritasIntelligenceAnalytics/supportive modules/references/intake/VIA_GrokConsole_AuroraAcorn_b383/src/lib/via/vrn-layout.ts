/** GenericLayoutEngine 2.1 契約。本台無 32 後端 · SKIPPED_UNAVAILABLE。不雲端、不 Adobe。 */
import type { Light } from "./types.ts";

export const GLE_VER = "2.1.0";
export const GLE_HEADER = 0.1;
export const GLE_FOOTER = 0.88;
export const GLE_DISABLED = ["adobe_extract_api"] as const;
export const GLE_OCR_LANG = "chi_tra+chi_sim+eng";

export type GleStatus =
  | "PASS"
  | "WARN"
  | "FAIL"
  | "TIMEOUT"
  | "SKIPPED_UNAVAILABLE"
  | "SKIPPED_POLICY";

export type GleTag = "title" | "heading" | "body" | "table" | "caption" | "header" | "footer" | "noise";

export const GLE_LEVELS = [
  { lv: 1, engines: ["pdfplumber", "pypdf", "poppler", "pdf-parse"] },
  { lv: 2, engines: ["pymupdf", "pdfminer", "pdfbox", "pdfjs", "mupdf", "pymupdf4llm", "camelot", "tabula"] },
  { lv: 3, engines: ["docling", "unstructured", "tika", "pdfsharp"] },
  { lv: 4, engines: ["marker", "mineru", "layoutparser", "deepdoctection", "huridocs", "tatr"] },
  { lv: 5, engines: ["tesseract", "paddleocr", "ppstructure", "paddle_layout", "paddle_pdf", "paddle_det", "easyocr", "ocrmypdf", "transkribus"] },
] as const;

export const GLE_N = GLE_LEVELS.reduce((n, l) => n + l.engines.length, 0);

export function gleProbe(): { name: string; level: number; status: GleStatus }[] {
  const rows: { name: string; level: number; status: GleStatus }[] = [];
  for (const l of GLE_LEVELS) {
    for (const name of l.engines) {
      rows.push({ name, level: l.lv, status: "SKIPPED_UNAVAILABLE" });
    }
  }
  rows.push({ name: "adobe_extract_api", level: 0, status: "SKIPPED_POLICY" });
  return rows;
}

export function gleZone(y1: number, y2: number, h: number): "header" | "footer" | "body" {
  if (h <= 0) return "body";
  if (y2 >= h * GLE_FOOTER) return "footer";
  if (y1 <= h * GLE_HEADER) return "header";
  return "body";
}

export function gleTagLine(line: string, zone: "header" | "footer" | "body"): GleTag {
  const t = line.trim();
  if (!t) return "noise";
  if (zone === "header") return "header";
  if (zone === "footer") return "footer";
  if (/^\|/.test(t) || /\t/.test(t)) return "table";
  if (/^(圖|表|Figure|Table)\s*\d/i.test(t)) return "caption";
  if (t.length >= 2 && t.length <= 120 && /標題[:：]/.test(t)) return "title";
  if (/[:：]/.test(t) && t.length <= 180) return "body";
  if (t.length >= 2 && t.length <= 40 && !/[。．]$/.test(t)) return "heading";
  return "body";
}

export type GleSpan = { zone: "header" | "footer" | "body"; tag: GleTag; text: string };

export function gleRestore(text: string): GleSpan[] {
  const lines = text.split(/\r?\n/);
  const n = Math.max(lines.length, 1);
  return lines.map((raw, i) => {
    const y1 = (i / n) * 1000;
    const y2 = ((i + 1) / n) * 1000;
    const zone = gleZone(y1, y2, 1000);
    const textLine = raw.replace(/\uFFFD/g, "").replace(/[ \t]{2,}/g, " ").trimEnd();
    return { zone, tag: gleTagLine(textLine, zone), text: textLine };
  });
}

export function gleBodyText(text: string): string {
  const spans = gleRestore(text);
  if (spans.length < 8) return text;
  return spans
    .filter((s) => {
      if (/標題[:：]|投資結論[:：]|成長動能[:：]|財務[:：]|同業[:：]|風險[:：]|目標價[:：]|評價方式[:：]|基於[:：]|主要原因[:：]|稀釋/.test(s.text)) return true;
      return s.zone === "body" && s.tag !== "noise" && s.tag !== "footer" && s.tag !== "header";
    })
    .map((s) => s.text)
    .filter(Boolean)
    .join("\n");
}

export function gleNote(): string {
  return `GLE ${GLE_VER} · ${GLE_N} 後端全 SKIPPED_UNAVAILABLE · Adobe 禁 · 本機 CACHE 分區`;
}

export function gleQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const probe = gleProbe();
  const skip = probe.filter((p) => p.status === "SKIPPED_UNAVAILABLE").length;
  const pol = probe.filter((p) => p.status === "SKIPPED_POLICY").length;
  return [
    { id: "G_N", metric: "後端", value: String(GLE_N), light: GLE_N === 31 ? "ok" : "bad", note: "L1–L5 本機 · Adobe 另列" },
    { id: "G_SKIP", metric: "未裝", value: String(skip), light: skip === 31 ? "ok" : "warn", note: "不假裝 PASS" },
    { id: "G_POL", metric: "政策略過", value: String(pol), light: pol === 1 ? "ok" : "bad", note: "adobe_extract_api" },
    { id: "G_OCR", metric: "OCR 語系", value: GLE_OCR_LANG, light: "ok", note: "繁+簡+英 · LIVE 關" },
  ];
}

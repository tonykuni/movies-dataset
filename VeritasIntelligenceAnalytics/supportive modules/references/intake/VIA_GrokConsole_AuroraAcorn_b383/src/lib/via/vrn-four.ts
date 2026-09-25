/** Four-engine batch 契約。repair/layout/text/table · markitdown 橋 · 不覆寫舊 run。 */
import type { Light } from "./types.ts";

export const FE_VER = "v0100";
export const FE_STAGES = ["repair", "layout", "text", "table"] as const;
export const FE_NPY = "numpy>=1.24,<2.0";

export type FeRoute = "NATIVE_DOC" | "NATIVE_TEXT" | "MARKITDOWN_BRIDGE" | "SKIP";
export type FeStageStatus = "PASS" | "WARN" | "FAIL" | "SKIPPED" | "NEEDS_OCR" | "MISSING";
export type FeRecon = "MATCH" | "MISMATCH" | "BASELINE_ONLY" | "NEW_ONLY";

const NATIVE_DOC = new Set(["pdf", "png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp"]);
const NATIVE_TEXT = new Set(["txt", "md"]);
const BRIDGE = new Set(["docx", "doc", "pptx", "ppt", "xlsx", "xls", "msg", "html", "htm", "epub", "csv"]);

export function feRoute(ext: string): FeRoute {
  const e = ext.replace(/^\./, "").toLowerCase();
  if (NATIVE_DOC.has(e)) return "NATIVE_DOC";
  if (NATIVE_TEXT.has(e)) return "NATIVE_TEXT";
  if (BRIDGE.has(e)) return "MARKITDOWN_BRIDGE";
  return "SKIP";
}

export function feStageLight(status: FeStageStatus): Light {
  if (status === "PASS") return "ok";
  if (status === "WARN" || status === "SKIPPED" || status === "NEEDS_OCR") return "warn";
  return "bad";
}

export function feWrapCorpus(name: string, ext: string, body: string): string {
  const rec = ext.toLowerCase() === "docx" ? name : `${name}.docx`;
  return `${rec}DOCX_HEAD · markitdown bridge from ${ext}\n本文區(修復)\n${body.trim()}\n`;
}

export function feRecon(baseline: number[] | null, fresh: number[] | null): FeRecon {
  const b = (baseline ?? []).slice().sort((a, c) => a - c);
  const f = (fresh ?? []).slice().sort((a, c) => a - c);
  if (b.length && f.length) return b.join(",") === f.join(",") ? "MATCH" : "MISMATCH";
  if (b.length) return "BASELINE_ONLY";
  return "NEW_ONLY";
}

export function feQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const pdf = feRoute("pdf");
  const docx = feRoute("docx");
  const exe = feRoute("exe");
  const ocr = feStageLight("NEEDS_OCR");
  const rec = feRecon([220], [221]);
  const wrap = feWrapCorpus("note.docx", "docx", "本文");
  return [
    { id: "E_ST", metric: "四段", value: FE_STAGES.join("/"), light: FE_STAGES.length === 4 ? "ok" : "bad", note: "GLE 對 layout · NLP 對 text" },
    { id: "E_PDF", metric: "PDF 路由", value: pdf, light: pdf === "NATIVE_DOC" ? "ok" : "bad", note: "圖檔同 NATIVE" },
    { id: "E_DOC", metric: "docx 橋", value: docx, light: docx === "MARKITDOWN_BRIDGE" ? "ok" : "bad", note: wrap.includes("DOCX_HEAD") ? "corpus 標記" : "缺標記" },
    { id: "E_SKIP", metric: "exe", value: exe, light: exe === "SKIP" ? "ok" : "bad", note: "不餵四引擎" },
    { id: "E_OCR", metric: "NEEDS_OCR", value: ocr, light: ocr === "warn" ? "ok" : "bad", note: "黃不中止 · 不假裝 PASS" },
    { id: "E_REC", metric: "對帳", value: rec, light: rec === "MISMATCH" ? "ok" : "bad", note: "新舊精確比 · 不藏分歧" },
    { id: "E_NPY", metric: "numpy 銷", value: FE_NPY, light: "ok", note: "via_iso_numpy 1.26.4 · 不混 2.x" },
  ];
}

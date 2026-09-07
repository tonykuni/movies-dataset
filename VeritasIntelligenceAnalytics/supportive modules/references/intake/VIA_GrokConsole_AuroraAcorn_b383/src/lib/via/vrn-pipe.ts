/** MDL 全景／三角／四點摘要契約。快照非本機實跑。不啟動、不灌 134k 引擎。 */
import type { Light } from "./types.ts";
import { VRN_FAILS, VRN_FAIL_N } from "./vrn-fail-cache.ts";
import { expandTw, tickerFilenameQc } from "./tw-ticker.ts";
import { twRxQc } from "./tw-ticker-all.ts";

import { YEAR_SUSPECT } from "./knowledge.ts";
import { VRN_CORE_N, vrnCoreNote, vrnHgLocal, vrnNlpMounted, vrnRestoreTables, vrnTrust } from "./vrn-core.ts";
import { gleQc } from "./vrn-layout.ts";
import { xvalQc } from "./vrn-xval.ts";
import { seedByCode } from "./consensus.ts";
import { isTwEquityReport, parseFilename } from "./vrn.ts";
import { fwdQc } from "./fwd-vintage.ts";
import { feQc } from "./vrn-four.ts";

export const VRN_HG = {
  policy: "BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH",
  seal: "PARTIAL",
  capable: 3,
  of: 7,
  loaded: ["ssot", "celeritas", "aegis"],
  absent: ["registry", "runtime_bridge", "env_manager", "ast_planner"],
} as const;

export const VRN_CV_SNAP = {
  when: "2026-05-06",
  pass: 22,
  fail: 0,
  cls: "READY",
  tables: 0,
  apiRows: 10,
  triangle: 1,
  phaseA: 8,
  phaseB: 6,
  p1OnlyA: 1,
  p1OnlyB: 3,
  tol: 0.02,
} as const;

export const VRN_MDL = ["MDL001", "MDL002", "MDL003", "MDL004", "MDL005", "MDL006", "MDL007", "MDL008", "MDL009", "MDL010"] as const;

/** 四點：P1 上漲空間→K1 · P2 EPS→K2 · P3/P4 首頁其餘→K3/K4；K5 可空不發明。 */
export const VRN_FOUR_TO_DIGEST = {
  潛在上漲空間: "K1",
  目標價: "K1",
  評價方式: "K1",
  稀釋EPS: "K2",
  主要原因: "K2",
  首頁其餘甲: "K3",
  首頁其餘乙: "K4",
} as const;

export function vrnYfFromMaster(core: string): string {
  return expandTw(core)?.yfinance ?? "";
}

export function vrnTickerNotYear(token: string): boolean {
  return YEAR_SUSPECT.test(token);
}

export function vrnPhaseDiff(a: number, b: number, tol = VRN_CV_SNAP.tol): "MATCH" | "MISMATCH" {
  const den = Math.max(Math.abs(a), Math.abs(b), 1e-12);
  return Math.abs(a - b) / den <= tol ? "MATCH" : "MISMATCH";
}

export function vrnCoverageOnly(p1Keys: string[], p2Keys: string[]): string[] {
  const s = new Set(p2Keys);
  return p1Keys.filter((k) => !s.has(k));
}

export function vrnNovelNumbers(summary: string, source: string): string[] {
  const grab = (t: string) => [...t.matchAll(/-?\d+(?:\.\d+)?%?/g)].map((m) => m[0].replace(/,/g, ""));
  const allow = new Set(grab(source));
  return [...new Set(grab(summary))].filter((n) => !allow.has(n));
}

export function vrnPipeQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const impl = VRN_FAILS.filter((f) => f.st.startsWith("IMPLEMENTED")).length;
  const p1 = vrnCoverageOnly(["rev", "gp", "op", "ni"], ["rev", "gp", "op"]);
  const ocr = vrnPhaseDiff(220, 221);
  const yf = vrnYfFromMaster("2317");
  const novel = vrnNovelNumbers("目標價 9999", "目標價 850 現價 678");
  const hg = vrnHgLocal();
  const nlp = vrnNlpMounted();
  const trust = vrnTrust({ entityOk: false, periodOk: true, arithOk: true, officialOk: true });
  const tabs = vrnRestoreTables("| a | b |\n| --- | --- |\n| 1 | 2 |");
  const gle = gleQc();
  const xv = xvalQc();
  const fwd = fwdQc();
  const fe = feQc();
  const cns = seedByCode().get("2330");
  const twOk = isTwEquityReport(parseFilename("GS-2330 台積電_20251130.pdf"), "GS-2330 台積電_20251130.pdf");
  const twNo = isTwEquityReport(parseFilename("凱基美股分析20251205.pdf"), "凱基美股分析20251205.pdf");
  const fn = tickerFilenameQc();
  const rx = twRxQc();
  return [
    { id: "P_HG", metric: "HardGate 快照", value: `${VRN_HG.seal} ${VRN_HG.capable}/${VRN_HG.of}`, light: "warn", note: VRN_HG.policy },
    { id: "P_HGL", metric: "HardGate 本樹", value: `${hg.ok}/${hg.n}`, light: hg.light, note: hg.note },
    { id: "P_CV", metric: "交叉驗證", value: `${VRN_CV_SNAP.pass}/${VRN_CV_SNAP.pass + VRN_CV_SNAP.fail}`, light: VRN_CV_SNAP.fail === 0 ? "ok" : "bad", note: `快照 ${VRN_CV_SNAP.when} · 表 ${VRN_CV_SNAP.tables} · 非本機實跑` },
    { id: "P_MDL", metric: "核心模組", value: `${VRN_CORE_N}/${VRN_MDL.length}`, light: VRN_CORE_N === 10 ? "ok" : "bad", note: VRN_MDL.join("·") },
    { id: "P_NLP", metric: "NLP 工具", value: `${nlp.ok}/${nlp.n}`, light: nlp.light, note: "灰→CACHE · LIVE 關" },
    { id: "P_OCR", metric: "OCR 容差", value: ocr, light: ocr === "MATCH" && p1.length === 1 ? "ok" : "bad", note: "0.45%<2% 仍 MATCH · 缺欄=p1_only 非三角失敗" },
    { id: "P_TAB", metric: "表還原", value: `${tabs}`, light: tabs >= 1 ? "ok" : "bad", note: "MDL003 markdown 表" },
    { id: "P_TR", metric: "Trust", value: trust.status, light: trust.closed ? "ok" : "bad", note: "實體錯配 fail-closed" },
    { id: "P_YF", metric: "YF 後綴", value: yf, light: yf === "2317.TW" ? "ok" : "bad", note: "主檔市場 · 檔名 .TWO 不改後綴" },
    { id: "P_NUM", metric: "禁發明數", value: novel.length ? novel.join(",") : "無", light: novel.length ? "ok" : "bad", note: "摘要數字必須在來源" },
    { id: "P_GLE", metric: "Layout GLE", value: gle.map((r) => r.value).join("/"), light: gle.every((r) => r.light !== "bad") ? "ok" : "bad", note: "31 後端未裝 · Adobe 禁" },
    { id: "P_TW", metric: "台股過濾", value: twOk && !twNo ? "TW-only" : "漏", light: twOk && !twNo ? "ok" : "bad", note: "美股／日股／港股／期貨不進 TAB2" },
    { id: "P_FN", metric: "檔名 ticker", value: fn.filter((r) => r.light === "ok").length + "/" + fn.length, light: fn.every((r) => r.light !== "bad") ? "ok" : "bad", note: "年碼不進 regex · 切詞 · 三碼" },
    { id: "P_RX", metric: "TW regex 13類", value: rx.find((r) => r.id === "RX_SELF")?.value ?? "", light: rx.every((r) => r.light !== "bad") ? "ok" : "bad", note: "v0100 只增不減 · DORMANT 5碼 · LIVE 關" },
    { id: "P_CNS", metric: "共識雙源", value: `FS ${cns?.medianFs ?? "—"} · YF ${cns?.medianYf ?? "—"}`, light: cns?.medianFs != null && cns?.medianYf != null ? "ok" : "bad", note: "FactSet×YF CACHE · LIVE 關" },
    { id: "P_XVAL", metric: "MDL008", value: xv[0]?.value ?? "", light: xv.every((r) => r.light !== "bad") ? "ok" : "bad", note: xv.map((r) => r.id).join("·") },
    { id: "P_FWD", metric: "估值 vintage", value: fwd.filter((r) => r.light === "ok").length + "/" + fwd.length, light: fwd.every((r) => r.light !== "bad") ? "ok" : "bad", note: "指數≠ETF · 不平均來源" },
    { id: "P_FE", metric: "四引擎", value: fe[0]?.value ?? "", light: fe.every((r) => r.light !== "bad") ? "ok" : "bad", note: "repair/layout/text/table · docx 橋 CACHE" },
    { id: "P_FB", metric: "失敗手冊", value: `${impl}/${VRN_FAIL_N}`, light: VRN_FAIL_N === 15 ? "ok" : "bad", note: "REGISTERED 3 · PARTIAL 歪斜" },
  ];
}

export function vrnPipeNote(): string {
  return vrnCoreNote();
}

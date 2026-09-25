/** Ordered VRN run-to-end. S04 失敗留 TAB 1。NLP 閘關不算紅。 */
import { auditFinancialRows } from "./fin-audit.ts";
import { BASIC_INFO_COLUMNS, FINANCIAL_DATA_COLUMNS } from "./knowledge.ts";
import { sealVrn, type Seal } from "./seal.ts";
import type { BasicInfo, FinRow, IntakeFile, Light, SummaryRow } from "./types.ts";

export type VrnStep = {
  id: string;
  name: string;
  result: "RAN" | "CACHE" | "SKIP" | "FAIL";
  light: Light;
  out: string;
};

export function runVrnToEnd(input: {
  files: IntakeFile[];
  basics: BasicInfo[];
  summaries: SummaryRow[];
  finances: FinRow[];
  confirmNlp: boolean;
}): { steps: VrnStep[]; seal: Seal; fail: number } {
  const steps: VrnStep[] = [];
  const files = input.files;
  const s04 = files.filter((f) => f.status === "bad" && f.stuckStep === "S04");
  steps.push({
    id: "R01",
    name: "S04 零位元組",
    result: s04.length ? "RAN" : files.length ? "FAIL" : "SKIP",
    light: s04.length || !files.length ? "ok" : "bad",
    out: s04.length ? `失敗 ${s04.length} 留 TAB 1` : files.length ? "S04 失敗件未留" : "尚未進件",
  });

  const red = input.basics.filter((b) => b.validationRisk === "RED");
  steps.push({
    id: "R02",
    name: "TAB 2 無 RED",
    result: red.length ? "FAIL" : "RAN",
    light: red.length ? "bad" : "ok",
    out: red.length ? `RED ${red.length}` : `BASIC ${input.basics.length}`,
  });

  const green = input.basics.filter((b) => b.validationRisk === "GREEN");
  steps.push({
    id: "R03",
    name: "INFO 綠件",
    result: green.length >= 3 ? "RAN" : "FAIL",
    light: green.length >= 3 ? "ok" : "warn",
    out: `GREEN ${green.length}`,
  });

  const yfAsTicker = input.basics.filter((b) => /\.TW|\.TWO| TT$/.test(b.ticker));
  steps.push({
    id: "R04",
    name: "代碼四碼",
    result: yfAsTicker.length ? "FAIL" : "RAN",
    light: yfAsTicker.length ? "bad" : "ok",
    out: yfAsTicker.length ? `YF 混入 ${yfAsTicker.map((b) => b.ticker).join(",")}` : "TAB 2 ticker 非 YF",
  });

  const grounded = input.summaries.filter((s) => s.grounded);
  steps.push({
    id: "R05",
    name: "摘要接地",
    result: grounded.length >= 10 ? "RAN" : "FAIL",
    light: grounded.length >= 10 ? "ok" : "warn",
    out: `GROUNDED ${grounded.length}/${input.summaries.length}`,
  });

  const hasIS = input.finances.some((f) => f.category === "IS");
  const hasBS = input.finances.some((f) => f.category === "BS");
  const hasCF = input.finances.some((f) => f.category === "CF");
  const stmtN = [hasIS, hasBS, hasCF].filter(Boolean).length;
  steps.push({
    id: "R06",
    name: "IS/BS/CF",
    result: stmtN === 3 ? "RAN" : "FAIL",
    light: stmtN === 3 ? "ok" : "warn",
    out: `${stmtN}/3 · FIN ${input.finances.length}`,
  });

  const audit = input.finances.length ? auditFinancialRows(input.finances) : null;
  const auditFail = audit?.gates.some((g) => g.status === "FAIL") ?? false;
  steps.push({
    id: "R07",
    name: "財務原子",
    result: !input.finances.length ? "SKIP" : auditFail ? "FAIL" : "RAN",
    light: !input.finances.length ? "warn" : auditFail ? "bad" : audit?.verdict === "GREEN" ? "ok" : "warn",
    out: audit ? `${audit.verdict} · 假綠 ${audit.fakeGreen}` : "尚未 TAB 4",
  });

  const cols = BASIC_INFO_COLUMNS.length + FINANCIAL_DATA_COLUMNS.length;
  steps.push({
    id: "R08",
    name: "Knowledge SSOT",
    result: cols >= 8 ? "RAN" : "FAIL",
    light: cols >= 8 ? "ok" : "bad",
    out: `欄 ${cols} · 不發明`,
  });

  steps.push({
    id: "R09",
    name: "NLP 閘",
    result: input.confirmNlp ? "RAN" : "SKIP",
    light: "ok",
    out: input.confirmNlp ? "閘開 · 仍 quote-or-abstain" : "閘關正確 · 不外呼",
  });

  const seal = sealVrn(files, input.basics, input.summaries, input.finances);
  steps.push({
    id: "R10",
    name: "VRN 封印",
    result: seal.light === "bad" ? "FAIL" : "RAN",
    light: seal.light,
    out: seal.note,
  });

  const closed = !steps.some((s) => s.result === "FAIL" || s.light === "bad");
  steps.push({
    id: "R11",
    name: "VRN 收官",
    result: closed ? "RAN" : "FAIL",
    light: closed ? "ok" : "bad",
    out: closed ? "進件實測通過 · NLP LIVE 另閘 · DCT01–20 不動" : "收官未齊",
  });

  return { steps, seal, fail: steps.filter((s) => s.result === "FAIL").length };
}

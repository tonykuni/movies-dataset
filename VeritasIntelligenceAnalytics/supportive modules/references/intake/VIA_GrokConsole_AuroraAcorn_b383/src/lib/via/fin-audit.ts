/** VIA-VRN-ENG-001 compact: 一列必須是原子事實。P 級不得掛綠。 */
import type { FinRow, Light } from "./types.ts";
import { normalizeTemporal } from "./temporal.ts";

export const PERIOD_RE =
  /\b[1-4]Q\d{2}[EF]?\b|\b\d{4}[EF]?\b|\b[1-2]H\d{2}[EF]?\b|\b\d{2}Q[1-4]\b|\b(?:FY)\d{2,4}\b|\b\d{4}-\d{2}(?:-\d{2})?\b/g;
export const REVERSED_RE = /\b[5-9]2Q[1-4]\b|\bF\d2Q[1-4]\b/;
const NUMBER_RE = /-?\d[\d,]*\.?\d*%?/g;

export type FinGrade = "V" | "M" | "P";
export type FinGate = { code: string; title: string; status: "PASS" | "WARN" | "FAIL"; detail: string };

export type FinAudit = {
  rows: FinRow[];
  dropped: number;
  dups: number;
  gradeV: number;
  gradeM: number;
  gradeP: number;
  fakeGreen: number;
  gates: FinGate[];
  verdict: "GREEN" | "AMBER" | "RED";
};

function periodsOf(text: string): string[] {
  const n = normalizeTemporal(text);
  if (n) return [n.normalized];
  return text.match(PERIOD_RE) ?? [];
}

export function gradeRow(row: FinRow): { grade: FinGrade; defects: string[]; status: Light } {
  const defects: string[] = [];
  const periodText = String(row.period ?? "");
  const valueText = row.value == null || !Number.isFinite(row.value) ? "" : String(row.value);
  const periods = periodsOf(periodText);
  const values = valueText ? [valueText] : (String(row.value ?? "").match(NUMBER_RE) ?? []);

  if (!periodText.trim()) defects.push("PERIOD_EMPTY");
  else if (!periods.length) defects.push("PERIOD_UNPARSEABLE");
  if (REVERSED_RE.test(periodText) || REVERSED_RE.test(valueText)) defects.push("PERIOD_REVERSED");
  if (valueText && valueText === String(row.item).trim()) defects.push("VALUE_ECHOES_METRIC");
  if (!values.length) defects.push("VALUE_NO_NUMBER");
  else if (values.length > 1) defects.push("VALUE_IS_ROW_BLOB");

  let grade: FinGrade = "P";
  if (periods.length === 1 && values.length === 1 && !defects.includes("VALUE_ECHOES_METRIC")) grade = "V";
  else if (periods.length >= 1 && periods.length === values.length) grade = "M";

  const status: Light = grade === "V" ? "ok" : grade === "M" ? "warn" : "bad";
  return { grade, defects, status };
}

export function auditFinancialRows(rows: FinRow[]): FinAudit {
  const kept: FinRow[] = [];
  let dropped = 0;
  let dups = 0;
  const idx = new Map<string, number>();
  for (const raw of rows) {
    if (raw.value == null || !Number.isFinite(raw.value) || !String(raw.unit ?? "").trim()) {
      dropped += 1;
      continue;
    }
    const g = gradeRow(raw);
    const row: FinRow = { ...raw, grade: g.grade, defects: g.defects, status: g.status };
    const key = `${row.fileId}|${row.dataName}|${row.period}`;
    const at = idx.get(key);
    if (at != null) {
      dups += 1;
      if (row.confidence >= kept[at]!.confidence) kept[at] = row;
      continue;
    }
    idx.set(key, kept.length);
    kept.push(row);
  }
  const gradeV = kept.filter((r) => r.grade === "V").length;
  const gradeM = kept.filter((r) => r.grade === "M").length;
  const gradeP = kept.filter((r) => r.grade === "P").length;
  const fakeGreen = kept.filter((r) => r.grade === "P" && r.status === "ok").length;
  const total = kept.length || 1;
  const atomic = (100 * gradeV) / total;
  const noPeriod = kept.filter((r) => (r.defects ?? []).some((d) => d.startsWith("PERIOD_"))).length;
  const blob = kept.filter((r) => (r.defects ?? []).includes("VALUE_IS_ROW_BLOB")).length;
  const echo = kept.filter((r) => (r.defects ?? []).includes("VALUE_ECHOES_METRIC")).length;

  const gates: FinGate[] = [
    { code: "F01", title: "ATOMICITY", status: atomic >= 80 ? "PASS" : atomic >= 20 ? "WARN" : "FAIL", detail: `原子列 ${gradeV}/${kept.length} = ${atomic.toFixed(1)}%` },
    { code: "F02", title: "PERIOD_PRESENT", status: noPeriod === 0 ? "PASS" : "WARN", detail: `${noPeriod} 列期間異常` },
    { code: "F03", title: "VALUE_NOT_BLOB", status: blob === 0 ? "PASS" : "FAIL", detail: `${blob} 列多值` },
    { code: "F04", title: "VALUE_NOT_ECHO", status: echo === 0 ? "PASS" : "FAIL", detail: `${echo} 列值等於科目` },
    { code: "F08", title: "NO_FAKE_GREEN", status: fakeGreen === 0 ? "PASS" : "FAIL", detail: `${fakeGreen} 列假綠燈` },
  ];
  const fails = gates.filter((g) => g.status === "FAIL").length;
  const warns = gates.filter((g) => g.status === "WARN").length;
  return {
    rows: kept,
    dropped,
    dups,
    gradeV,
    gradeM,
    gradeP,
    fakeGreen,
    gates,
    verdict: fails ? "RED" : warns ? "AMBER" : "GREEN",
  };
}

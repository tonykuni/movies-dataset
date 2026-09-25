/** CGE C9 時間語彙。認不出來回 null，不亂認。 */
const CN_Q: Record<string, number> = { 一: 1, 二: 2, 三: 3, 四: 4, "1": 1, "2": 2, "3": 3, "4": 4 };

function year(value: number): number {
  if (value < 100) return value <= 50 ? 2000 + value : 1900 + value;
  if (value < 1911) return value + 1911;
  return value;
}

export function normalizeTemporal(text: string): { kind: string; normalized: string } | null {
  const raw = text.normalize("NFKC").trim();
  if (!raw) return null;
  let m = raw.match(/^(?:民國)?(\d{2,4})年(\d{1,2})月(\d{1,2})日?$/);
  if (m) return { kind: "DATE", normalized: `${year(+m[1]!).toString().padStart(4, "0")}-${m[2]!.padStart(2, "0")}-${m[3]!.padStart(2, "0")}` };
  m = raw.match(/^(?:民國)?(\d{2,4})年(\d{1,2})月$/);
  if (m) return { kind: "MONTH", normalized: `${year(+m[1]!).toString().padStart(4, "0")}-${m[2]!.padStart(2, "0")}` };
  m = raw.match(/^(?:民國)?(\d{2,4})年第([一二三四1-4])季$/);
  if (m) return { kind: "QUARTER", normalized: `${year(+m[1]!)}-Q${CN_Q[m[2]!]}` };
  m = raw.match(/^(\d{4})Q([1-4])$/i);
  if (m) return { kind: "QUARTER", normalized: `${m[1]}-Q${m[2]}` };
  m = raw.match(/^(\d{2})Q([1-4])$/i);
  if (m) return { kind: "QUARTER", normalized: `${year(+m[1]!)}-Q${m[2]}` };
  m = raw.match(/^([1-4])Q(\d{2}|\d{4})([EF])?$/i);
  if (m) return { kind: "QUARTER", normalized: `${year(+m[2]!)}-Q${m[1]}${(m[3] ?? "").toUpperCase()}` };
  m = raw.match(/^([12])H(\d{2}|\d{4})([EF])?$/i);
  if (m) return { kind: "HALF", normalized: `${year(+m[2]!)}-H${m[1]}${(m[3] ?? "").toUpperCase()}` };
  m = raw.match(/^(?:民國)?(\d{2,4})年?(上|下)半年$/);
  if (m) return { kind: "HALF", normalized: `${year(+m[1]!)}-H${m[2] === "上" ? 1 : 2}` };
  if (raw === "上半年" || raw === "下半年") return { kind: "HALF_RELATIVE", normalized: raw[0] === "上" ? "H1" : "H2" };
  m = raw.match(/^FY(\d{2}|\d{4})$/i);
  if (m) return { kind: "FISCAL_YEAR", normalized: `FY${year(+m[1]!)}` };
  m = raw.match(/^(\d{4})(\d{2})(\d{2})$/);
  if (m) return { kind: "DATE", normalized: `${m[1]}-${m[2]}-${m[3]}` };
  m = raw.match(/^(\d{3})(\d{2})(\d{2})$/);
  if (m) return { kind: "DATE", normalized: `${+m[1]! + 1911}-${m[2]}-${m[3]}` };
  m = raw.match(/^(?:民國)?(\d{2,4})年$/);
  if (m) return { kind: "YEAR", normalized: `${year(+m[1]!)}` };
  const rel: Record<string, string> = { 月底: "EOM", 月末: "EOM", 年底: "EOY", 年末: "EOY", 今年以來: "YTD", 年初至今: "YTD", 季底: "EOQ" };
  if (rel[raw]) return { kind: "RELATIVE", normalized: rel[raw]! };
  if (/^\d{4}(-\d{2}(-\d{2})?)?$/.test(raw)) return { kind: "DATE", normalized: raw };
  return null;
}

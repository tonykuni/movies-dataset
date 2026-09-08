/** Compact port of VIA_NLP_OneEngine v1.5.0 table_ops + ingest (verbatim, no silent fill). */
import { gleBodyText } from "./vrn-layout.ts";
import { buildFourPoints, FOUR_POINT_SLOTS } from "./digest-four.ts";

export type NlpTable = { kind: string; headers: string[]; rows: string[][] };
export type NlpFact = { key: string; zh: string; dataName: string; value: number; unit: string; stmt: "IS" | "BS" | "CF" | "RATIO" };

const KV = /^\s*([^:：|]{1,40}?)\s*[:：]\s*(\S.{0,160})\s*$/;
const NUM_ALL = /-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+\.\d+|-?\d+/g;

const ITEM_MAP: Array<{ keys: RegExp; zh: string; dataName: string; stmt: NlpFact["stmt"]; unit: string }> = [
  { keys: /營業收入|營收合計|revenue/i, zh: "營業收入合計", dataName: "revenue", stmt: "IS", unit: "十億 TWD" },
  { keys: /營業利益|operating.?income/i, zh: "營業利益", dataName: "operating_income", stmt: "IS", unit: "十億 TWD" },
  { keys: /稅後純益|淨利|net.?income/i, zh: "本期淨利", dataName: "net_income", stmt: "IS", unit: "十億 TWD" },
  { keys: /每股盈餘|diluted.?eps|\beps\b/i, zh: "稀釋每股盈餘", dataName: "eps", stmt: "RATIO", unit: "TWD" },
  { keys: /現金及約當|cash\b/i, zh: "現金及約當現金", dataName: "cash", stmt: "BS", unit: "十億 TWD" },
  { keys: /資產總額|total.?assets/i, zh: "資產總額", dataName: "total_assets", stmt: "BS", unit: "十億 TWD" },
  { keys: /權益總額|equity/i, zh: "權益總額", dataName: "equity", stmt: "BS", unit: "十億 TWD" },
  { keys: /營業活動|operating.?cash|cfo/i, zh: "營業活動現金流", dataName: "ocf", stmt: "CF", unit: "十億 TWD" },
  { keys: /自由現金|free.?cash|fcf/i, zh: "自由現金流量", dataName: "fcf", stmt: "CF", unit: "十億 TWD" },
];

export function extractTables(text: string): NlpTable[] {
  const lines = text.split(/\r?\n/);
  const out: NlpTable[] = [];
  let i = 0;
  while (i < lines.length) {
    const cells = pipeCells(lines[i] ?? "");
    const next = pipeCells(lines[i + 1] ?? "");
    if (cells.length >= 2 && next.length === cells.length && /^[\s|:-]+$/.test(lines[i + 1] ?? "")) {
      const headers = cells;
      const rows: string[][] = [];
      i += 2;
      while (i < lines.length) {
        const r = pipeCells(lines[i] ?? "");
        if (r.length !== headers.length) break;
        rows.push(r);
        i += 1;
      }
      out.push({ kind: "markdown", headers, rows });
      continue;
    }
    i += 1;
  }
  const kvRows = lines
    .map((ln) => ln.match(KV))
    .filter((m): m is RegExpMatchArray => Boolean(m))
    .map((m) => [m[1]!.trim(), m[2]!.trim()]);
  if (kvRows.length >= 3) out.push({ kind: "key_value", headers: ["key", "value"], rows: kvRows });
  return out;
}

function pipeCells(line: string): string[] {
  if (!line.includes("|")) return [];
  return line
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((c) => c.trim());
}

export function parseNum(raw: string): number | null {
  NUM_ALL.lastIndex = 0;
  const tokens = raw.match(NUM_ALL);
  NUM_ALL.lastIndex = 0;
  if (!tokens || tokens.length !== 1) return null;
  const n = Number(tokens[0]!.replace(/,/g, ""));
  return Number.isFinite(n) ? n : null;
}

export function extractFacts(text: string): NlpFact[] {
  const facts: NlpFact[] = [];
  const seen = new Set<string>();
  const tables = extractTables(text);
  const cells: string[][] = [];
  for (const t of tables) {
    for (const row of t.rows) {
      if (t.kind === "key_value") cells.push(row);
      else cells.push([row[0] ?? "", row.slice(1).join(" ")]);
    }
  }
  for (const ln of text.split(/\r?\n/)) {
    const kv = ln.match(KV);
    if (kv) cells.push([kv[1]!, kv[2]!]);
    else if (ln.includes(",") && !ln.includes("|")) {
      const [a, b] = ln.split(",").map((x) => x.trim());
      if (a && b) cells.push([a, b]);
    }
  }
  for (const [k, v] of cells) {
    const n = parseNum(v);
    if (n == null) continue;
    const hit = ITEM_MAP.find((it) => it.keys.test(k));
    if (!hit || seen.has(hit.zh)) continue;
    seen.add(hit.zh);
    facts.push({ key: k, zh: hit.zh, dataName: hit.dataName, value: n, unit: hit.unit, stmt: hit.stmt });
  }
  return facts;
}

export function extractDigest(text: string): Partial<Record<string, string>> {
  const body = gleBodyText(text);
  const out: Partial<Record<string, string>> = {};
  const grab = (id: string, re: RegExp) => {
    const m = body.match(re) ?? text.match(re);
    if (m?.[1]) out[id] = m[1].trim().slice(0, 180);
  };
  grab("headline", /(?:標題|核心結論)[:：]\s*(.+)/);
  grab("K1", /(?:目標價|潛在上漲|評價方式)[:：]\s*(.+)/);
  grab("K2", /(?:稀釋每股盈餘|主要原因)[:：]\s*(.+)/);
  grab("K3", /(?:首頁其餘|成長動能|財務)[:：]\s*(.+)/);
  grab("K4", /(?:其餘乙|同業)[:：]\s*(.+)/);
  grab("K5", /(?:風險|風險與展望)[:：]\s*(.+)/);
  return out;
}

export { FOUR_POINT_SLOTS };

export function summarizeTitleFour(text: string, ticker = ""): {
  title: string;
  points: { id: string; digest?: string; zh: string; text: string; grounded: boolean }[];
} {
  const built = buildFourPoints(text, ticker);
  return {
    title: built.title,
    points: built.points
      .filter((p) => p.id !== "headline" && p.id !== "K5")
      .map((p) => ({
        id: FOUR_POINT_SLOTS.find((s) => s.digest === p.id)?.id ?? p.id,
        digest: p.id,
        zh: p.zh,
        text: p.text,
        grounded: p.grounded,
      })),
  };
}

/**
 * 報告型別分類 + 年份守衛(批418)——與母倉 VRN_ENG073 v0108 同律。
 *
 * 為什麼要有:操作員把工作站 63 份**真研究報告**交出來當測試輸入,逐檔名跑過
 * 之後查出兩件會毀掉整批的事:
 *   ① 「第三場 AI潮流下展望2026半導體產業趨勢」被抽出代號 2026——那是**年份**,
 *      而 2026 恰好也是真實上市代號(聚亨),所以連「逐驗官方名冊」都擋不住。
 *      假代號入庫比缺代號更糟。
 *   ② 63 份裡有 19 份**本來就不是個股報告**(產業/大盤晨報/海外/研討會)。
 *      它們沒有代號、沒有目標價、沒有 EPS 是**對的**,但判準若一律要求那些東西,
 *      就會把 19 份算成失敗——一整面假紅,跟假綠一樣糟。
 *
 * 這一份是唯讀邏輯:不跑、不抓、不連線,只把檔名分類。
 */

export type ReportKind = "個股" | "產業" | "大盤晨報" | "海外" | "研討會" | "其他";

const YEAR_TAIL = /^\s*(?:年|年度|年報|上半年?|下半年?|[Hh][12]|[Qq][1-4]|全年)/;
const OUTLOOK = ["展望", "趨勢", "前瞻", "回顧", "年度", "大趨勢", "投資策略", "策略會", "論壇", "研討"];
const TICKER_MARKS = ["(", "（", ")", "）", "TT", "tt", "代號", "股號"];

const KIND_RULES: Array<[ReportKind, string[]]> = [
  ["研討會", ["第一場", "第二場", "第三場", "第四場", "研討會", "論壇", "說明會", "法說會"]],
  ["大盤晨報", ["盤勢", "投資早報", "早報", "晨會", "晨間", "解盤", "收盤", "盤後", "盤前",
                "日報", "週報", "月報", "市場評論", "新聞與重要訊息"]],
  ["海外", ["日股", "美股", "港股", "陸股", "海外", "Asia", "asia", "US ", "Japan", "China", "Global", "global"]],
  ["產業", ["產業", "類股", "Thermal", "thermal", "ABF", "abf", "Memory", "memory", "PCB", "pcb",
            "CCL", "ccl", "Automation", "automation", "Solutions", "Insights", "Hardware",
            "TPU", "GPU", "AI ", "半導體", "供應鏈", "鋼鐵", "面板", "航運"]],
];

const DATE_RXS = [
  /(20\d{2})[-_]?(\d{2})[-_]?(\d{2})/g,
  /(?<!\d)(1[01]\d)(\d{2})(\d{2})(?!\d)/g,
  /(?<!\d)(2[3-9])(\d{2})(\d{2})(?!\d)/g,
];

function dateSpans(stem: string): Array<[number, number]> {
  const out: Array<[number, number]> = [];
  for (const rx of DATE_RXS) {
    rx.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = rx.exec(stem)) !== null) out.push([m.index, m.index + m[0].length]);
  }
  return out;
}

/** 4 碼候選讀起來是年份就不准當代號;回傳否決理由(空=不是年份)。 */
export function yearReject(stem: string, at: number, tok: string): string {
  const end = at + tok.length;
  for (const [x, y] of dateSpans(stem)) if (at >= x && end <= y) return "落在日期字串內";
  if (YEAR_TAIL.test(stem.slice(end, end + 4))) return "後接年份詞";
  const v = Number(tok);
  if (v >= 1990 && v <= 2099 && OUTLOOK.some((w) => stem.includes(w))) {
    const near = stem.slice(Math.max(0, at - 2), at) + stem.slice(end, end + 2);
    if (!TICKER_MARKS.some((t) => near.includes(t))) return "年份值+展望/趨勢類標題+旁無代號記號";
  }
  return "";
}

/** 自檔名抽代號;`roster` 給了就逐驗名冊(與母倉同律)。年份一律先擋掉。 */
export function tickerFromStem(stem: string, roster?: Set<string>): { ticker: string; rejected: string[] } {
  const rx = /(?<!\d)(\d{4})(?!\d)/g;
  const rejected: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = rx.exec(stem)) !== null) {
    const why = yearReject(stem, m.index, m[1]!);
    if (why) {
      rejected.push(`${m[1]}(${why})`);
      continue;
    }
    if (!roster || roster.has(m[1]!)) return { ticker: m[1]!, rejected };
  }
  return { ticker: "", rejected };
}

/** 報告型別 + 判準理由。有代號一律先算個股;全不中=「其他」誠實留白,不硬塞。 */
export function classifyKind(stem: string, ticker: string): { kind: ReportKind; why: string } {
  if (ticker) return { kind: "個股", why: `檔名帶可驗證代號 ${ticker}` };
  for (const [kind, words] of KIND_RULES) {
    for (const w of words) if (stem.includes(w)) return { kind, why: `檔名含「${w.trim()}」` };
  }
  return { kind: "其他", why: "無代號且無型別關鍵詞=誠實留白(不硬塞個股)" };
}

/** 只有個股型才「應該」有代號——其餘型別沒有代號是對的,不是失敗。 */
export function kindExpectsTicker(kind: ReportKind): boolean {
  return kind === "個股";
}

/** 一批檔名的型別分佈(給結果面板用)。 */
export function kindHistogram(stems: string[], roster?: Set<string>): Record<ReportKind, number> {
  const out = { 個股: 0, 產業: 0, 大盤晨報: 0, 海外: 0, 研討會: 0, 其他: 0 } as Record<ReportKind, number>;
  for (const s of stems) {
    const { ticker } = tickerFromStem(s, roster);
    out[classifyKind(s, ticker).kind] += 1;
  }
  return out;
}

import type { Reading } from "./engine";
import type { TopicDef } from "./registry";

export type TopicStatus = "看得到" | "看不到" | "樣本不足";

export type TopicRow = {
  id: string;
  name: string;
  question: string;
  rule: string;
  version: number;
  status: TopicStatus;
  detail: string;
};

function pick(readings: Reading[], id: string, label: string): Reading | undefined {
  return readings.find((row) => row.id === id && row.label.trim() === label.trim());
}

function num(value: number | null | undefined, digits = 2): string {
  return value == null ? "—" : value.toFixed(digits);
}

function ready(rows: Array<Reading | undefined>): rows is Reading[] {
  return rows.every((row) => row != null && row.value != null);
}

function sameSide(left: number, right: number): boolean {
  return (left > 0 && right > 0) || (left < 0 && right < 0);
}

export function runTopics(defs: TopicDef[], readings: Reading[]): TopicRow[] {
  return defs.map((def) => {
    const base = { id: def.id, name: def.name, question: def.question, rule: def.rule, version: def.version };
    const close = pick(readings, "VIA-VQG-TA-CMP001", "當天");
    const sma20 = pick(readings, "VIA-VQG-TA-TRD001", "20日");
    const sma10 = pick(readings, "VIA-VQG-TA-TRD001", "10日");
    const sma60 = pick(readings, "VIA-VQG-TA-TRD001", "60日");
    const ema20 = pick(readings, "VIA-VQG-TA-TRD002", "20日");
    const dema = pick(readings, "VIA-VQG-TA-TRD006", "窗口");
    const tema = pick(readings, "VIA-VQG-TA-TRD007", "窗口");
    const hma = pick(readings, "VIA-VQG-TA-TRD008", "窗口");
    const aroonUp = pick(readings, "VIA-VQG-TA-TRD009", "Up");
    const aroonDown = pick(readings, "VIA-VQG-TA-TRD009", "Down");
    const slope = pick(readings, "VIA-VQG-TA-TRD010", "窗口");
    const mom = pick(readings, "VIA-VQG-TA-MOM008", "窗口");
    const roc20 = pick(readings, "VIA-VQG-TA-MOM004", "20日");
    const rsi = pick(readings, "VIA-VQG-TA-MOM001", "14日");
    const hist = pick(readings, "VIA-VQG-TA-MOM002", "柱");
    const k = pick(readings, "VIA-VQG-TA-MOM003", "K");
    const d = pick(readings, "VIA-VQG-TA-MOM003", "D");
    const ppo = pick(readings, "VIA-VQG-TA-MOM009", "柱");
    const tsi = pick(readings, "VIA-VQG-TA-MOM010", "窗口");
    const ultimate = pick(readings, "VIA-VQG-TA-MOM011", "窗口");
    const width = pick(readings, "VIA-VQG-TA-TRD003", "20日");
    const atr = pick(readings, "VIA-VQG-TA-VOL003", "S3");
    const draw = pick(readings, "VIA-VQG-TA-RSK006", "當前");
    const sharpe = pick(readings, "VIA-VQG-TA-RSK003", "S2");
    const skew = pick(readings, "VIA-VQG-TA-STA004", "窗口");
    const upper = pick(readings, "VIA-VQG-TA-VOL005", "上軌");
    const blanks = ["VIA-VQG-TA-FLW007", "VIA-VQG-TA-FLW008", "VIA-VQG-TA-FLW009", "VIA-VQG-TA-FLW010"].map((id) =>
      readings.filter((row) => row.id === id),
    );

    const gap = (row: TopicStatus, detail: string): TopicRow => ({ ...base, status: row, detail });

    if (def.id === "VIA-VQG-TP-001") {
      if (!ready([close, sma20, ema20])) return gap("樣本不足", "收盤、20 日簡單均線或 20 日指數均線還沒有值。");
      const vsSma = close!.value! - sma20!.value!;
      const vsEma = close!.value! - ema20!.value!;
      const side = vsSma > 0 && vsEma > 0 ? "兩條均線之上" : vsSma < 0 && vsEma < 0 ? "兩條均線之下" : "";
      return gap(side ? "看得到" : "看不到", side ? `收盤同時在${side}。` : "收盤夾在兩條 20 日均線中間，兩側不一致。");
    }
    if (def.id === "VIA-VQG-TP-002") {
      if (!ready([sma10, sma60])) return gap("樣本不足", "10 日或 60 日簡單均線還沒有值。");
      return gap(sma10!.value! > sma60!.value! ? "看得到" : "看不到", `10 日 ${num(sma10!.value, 1)}，60 日 ${num(sma60!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-003") {
      if (!ready([close, dema, tema])) return gap("樣本不足", "收盤、雙重或三重指數均線還沒有值。");
      const both = close!.value! > dema!.value! && close!.value! > tema!.value!;
      return gap(both ? "看得到" : "看不到", `收盤 ${num(close!.value, 1)}，DEMA ${num(dema!.value, 1)}，TEMA ${num(tema!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-004") {
      if (!ready([close, hma])) return gap("樣本不足", "收盤或赫爾均線還沒有值。");
      return gap(close!.value! > hma!.value! ? "看得到" : "看不到", `收盤 ${num(close!.value, 1)}，赫爾均線 ${num(hma!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-005") {
      if (!ready([aroonUp, aroonDown])) return gap("樣本不足", "Aroon 缺最高或最低，沒有比較。");
      return gap(aroonUp!.value! > aroonDown!.value! ? "看得到" : "看不到", `Up ${num(aroonUp!.value, 1)}，Down ${num(aroonDown!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-006") {
      if (!ready([slope])) return gap("樣本不足", "迴歸斜率還沒有值。");
      return gap(slope!.value! > 0 ? "看得到" : "看不到", `斜率 ${num(slope!.value, 4)} 點/日。`);
    }
    if (def.id === "VIA-VQG-TP-007") {
      if (!ready([mom, roc20])) return gap("樣本不足", "10 日動量或 20 日漲跌還沒有值。");
      const aligned = sameSide(mom!.value!, roc20!.value!);
      return gap(aligned ? "看得到" : "看不到", `10 日點數差 ${num(mom!.value, 1)}，20 日漲跌 ${num(roc20!.value, 2)}%。`);
    }
    if (def.id === "VIA-VQG-TP-008") {
      if (!rsi || rsi.percentile == null) return gap("樣本不足", "RSI 的自身分位還沒有。");
      return gap(rsi.percentile >= 80 ? "看得到" : "看不到", `RSI ${num(rsi.value, 1)}，分位 ${rsi.percentile.toFixed(0)}。`);
    }
    if (def.id === "VIA-VQG-TP-009") {
      if (!ready([hist])) return gap("樣本不足", "MACD 柱還沒有值。");
      return gap(hist!.value! > 0 ? "看得到" : "看不到", `柱 ${num(hist!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-010") {
      if (!ready([k, d])) return gap("樣本不足", "K 或 D 留空。最高等於最低時本來就不算。");
      return gap(k!.value! > d!.value! ? "看得到" : "看不到", `K ${num(k!.value, 1)}，D ${num(d!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-011") {
      if (!ready([ppo, hist])) return gap("樣本不足", "PPO 柱或 MACD 柱還沒有值。");
      return gap(sameSide(ppo!.value!, hist!.value!) ? "看得到" : "看不到", `PPO 柱 ${num(ppo!.value)}%，MACD 柱 ${num(hist!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-012") {
      if (!ready([tsi])) return gap("樣本不足", "TSI 還沒有值。");
      return gap(tsi!.value! > 0 ? "看得到" : "看不到", `TSI ${num(tsi!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-013") {
      if (!ultimate || ultimate.percentile == null) return gap("樣本不足", "Ultimate Oscillator 的自身分位還沒有。");
      return gap(ultimate.percentile >= 80 ? "看得到" : "看不到", `數值 ${num(ultimate.value, 1)}，分位 ${ultimate.percentile.toFixed(0)}。`);
    }
    if (def.id === "VIA-VQG-TP-014") {
      if (!width || width.percentile == null) return gap("樣本不足", "布林帶寬的自身分位還沒有。");
      return gap(width.percentile <= 20 ? "看得到" : "看不到", `帶寬 ${num(width.value, 4)}，分位 ${width.percentile.toFixed(0)}。`);
    }
    if (def.id === "VIA-VQG-TP-015") {
      if (!atr || atr.percentile == null) return gap("樣本不足", "真實波幅占比還沒有。沒有最高最低就不判。");
      return gap(atr.percentile >= 80 ? "看得到" : "看不到", `占比 ${num(atr.value, 4)}，分位 ${atr.percentile.toFixed(0)}。`);
    }
    if (def.id === "VIA-VQG-TP-016") {
      if (!draw || draw.percentile == null) return gap("樣本不足", "當前回撤還沒有自身分位。");
      return gap(draw.percentile <= 20 ? "看得到" : "看不到", `當前回撤 ${num(draw.value, 4)}，分位 ${draw.percentile.toFixed(0)}。這不是虧損排名。`);
    }
    if (def.id === "VIA-VQG-TP-017") {
      if (!sharpe || sharpe.percentile == null) return gap("樣本不足", "滾動夏普 S2 還沒有自身分位。");
      return gap(sharpe.percentile <= 20 ? "看得到" : "看不到", `S2 ${num(sharpe.value, 4)}，分位 ${sharpe.percentile.toFixed(0)}。`);
    }
    if (def.id === "VIA-VQG-TP-018") {
      if (!ready([skew])) return gap("樣本不足", "偏態留空或還沒有值。");
      return gap(skew!.value! > 0 ? "看得到" : "看不到", `偏態 ${num(skew!.value, 2)}。正值只表示這一段上漲日的尾巴較長。`);
    }
    if (def.id === "VIA-VQG-TP-019") {
      if (!ready([close, upper])) return gap("樣本不足", "收盤或唐奇安上軌還沒有值。");
      return gap(close!.value! > upper!.value! ? "看得到" : "看不到", `收盤 ${num(close!.value, 1)}，上軌 ${num(upper!.value, 1)}。`);
    }
    if (def.id === "VIA-VQG-TP-020") {
      const rows = blanks.flat();
      if (rows.length === 0) return gap("樣本不足", "資金流四條還沒有登錄。");
      const leaked = rows.filter((row) => row.value != null);
      return gap(leaked.length === 0 ? "看得到" : "看不到", leaked.length === 0 ? "四條都留空，沒有用成交值代替股數。" : `${leaked.length} 個解出現數字。股數欄未接上時不應有值。`);
    }
    return gap("樣本不足", "這個專題還沒有接上規則。");
  });
}

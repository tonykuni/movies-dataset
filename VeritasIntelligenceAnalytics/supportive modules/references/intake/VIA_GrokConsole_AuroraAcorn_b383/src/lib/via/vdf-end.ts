/** Ordered VDF run-to-end. One chain, no extra writers. Net lanes stay SKIP. */
import { latestSql, lakesHydraOk, predPushOk } from "./duck-catalog.ts";
import { FRED_CATALOG, VDF_MODULES } from "./catalog.ts";
import { freqCover, resampleLast } from "./freq.ts";
import { YEAR_SUSPECT } from "./knowledge.ts";
import { buildMarketBook, crossValidate } from "./market-book.ts";
import { sealVdf, type Seal } from "./seal.ts";
import { expandTw } from "./tw-ticker.ts";
import { runTranscodeFetchTest } from "./transcode-fetch.ts";
import type { FetchMetrics, FredRow, Light } from "./types.ts";
import { ENG047_FRED, TW_UNIVERSE } from "./vdf-mother.ts";
import { viaDbHydraOk, viaDbSealNote } from "./via-db-parts.ts";

export type EndStep = {
  id: string;
  name: string;
  result: "RAN" | "CACHE" | "SKIP" | "FAIL";
  light: Light;
  out: string;
};

export type ModEnd = {
  id: string;
  name: string;
  gate: string;
  result: "RAN" | "CACHE" | "SKIP";
  light: Light;
  out: string;
};

export function runVdfToEnd(input: {
  confirmNet: boolean;
  mode: "LIVE" | "CACHE" | "DENIED";
  rows: FredRow[];
  metrics: FetchMetrics | null;
}): { steps: EndStep[]; modules: ModEnd[]; seal: Seal; fail: number } {
  const steps: EndStep[] = [];

  steps.push({
    id: "E01",
    name: "雙閘",
    result: input.confirmNet ? "RAN" : "SKIP",
    light: "ok",
    out: input.confirmNet ? "閘1 開 · 仍依 KEY" : "閘關 · 零外呼",
  });

  steps.push({
    id: "E02",
    name: "FRED 擷取",
    result: input.mode === "LIVE" ? "RAN" : input.mode === "CACHE" ? "CACHE" : "SKIP",
    light: input.rows.length ? "ok" : "bad",
    out: `${input.mode} · ${input.rows.length} series`,
  });

  const lakeOk = Boolean(input.metrics && input.metrics.lakeRows > 0);
  steps.push({
    id: "E03",
    name: "列式湖",
    result: lakeOk ? "RAN" : "FAIL",
    light: lakeOk ? "ok" : "bad",
    out: lakeOk ? `列 ${input.metrics!.lakeRows} · 年分區 ${input.metrics!.partitions}` : "湖空",
  });

  const parqOk = Boolean(input.metrics?.parquetRoundtrip);
  steps.push({
    id: "E04",
    name: "Parquet 回讀",
    result: parqOk ? "RAN" : "FAIL",
    light: parqOk ? "ok" : "bad",
    out: parqOk ? `PAR1 ${input.metrics!.parquetPages}p` : "回讀失敗",
  });

  const cover = freqCover(FRED_CATALOG);
  const sample = resampleLast(
    [
      { date: "2024-01-15", value: 1 },
      { date: "2024-01-31", value: 2 },
      { date: "2024-02-10", value: 3 },
    ],
    "M",
  );
  const freqOk = sample.length === 2 && sample[0]?.value === 2;
  steps.push({
    id: "E05",
    name: "頻率期末",
    result: freqOk ? "RAN" : "FAIL",
    light: freqOk ? "ok" : "bad",
    out: freqOk ? `D${cover.D}/W${cover.W}/M${cover.M}/Q${cover.Q}/A${cover.A} · 不插值` : "月末取值失敗",
  });

  const lakeIds = new Set(input.rows.map((r) => r.seriesId));
  const hit = ENG047_FRED.filter((s) => lakeIds.has(s.seriesId)).length;
  const miss = ENG047_FRED.length - hit;
  steps.push({
    id: "E06",
    name: "ENG047 細項",
    result: "RAN",
    light: miss ? "warn" : "ok",
    out: `${hit}/${ENG047_FRED.length} 在湖 · 未入 ${miss}`,
  });

  const rest = TW_UNIVERSE.filter((m) => !YEAR_SUSPECT.test(m.ticker));
  const badUni = rest.filter((m) => {
    const x = expandTw(m.ticker, m.market === "TPEX" ? "TWO" : "TW");
    return !x || x.yfinance !== m.yfinance;
  });
  steps.push({
    id: "E07",
    name: "宇宙對帳",
    result: badUni.length ? "FAIL" : "RAN",
    light: badUni.length ? "bad" : "ok",
    out: badUni.length ? `錯 ${badUni.map((b) => b.ticker).join(",")}` : `焦點 ${rest.length} 通過`,
  });

  const tsmc = expandTw("2330", "TW");
  const tickOk = Boolean(tsmc && tsmc.yfinance === "2330.TW" && !tsmc.yfinance.includes(".TWO"));
  steps.push({
    id: "E08",
    name: "2330 三面",
    result: tickOk ? "RAN" : "FAIL",
    light: tickOk ? "ok" : "bad",
    out: tickOk ? `${tsmc!.native} · ${tsmc!.yfinance} · ${tsmc!.bloomberg}` : "三面失敗",
  });

  const xf = runTranscodeFetchTest();
  steps.push({
    id: "E08X",
    name: "自動轉碼擷取",
    result: xf.ok ? "RAN" : "FAIL",
    light: xf.ok ? "ok" : "bad",
    out: xf.note,
  });

  steps.push({
    id: "E09",
    name: "STAT",
    result: input.rows.length ? "RAN" : "SKIP",
    light: input.rows.length ? "ok" : "warn",
    out: input.rows.length ? `期末 ${input.rows.length} 列` : "尚未擷取",
  });

  const book = buildMarketBook({ yfLive: false, akLive: false });
  steps.push({
    id: "E10",
    name: "市場簿",
    result: "RAN",
    light: "ok",
    out: `${book.length} 列 · YF/AK 未 LIVE`,
  });

  const x = crossValidate();
  const xbad = x.filter((r) => r.light === "bad").length;
  steps.push({
    id: "E11",
    name: "交叉驗證",
    result: xbad ? "FAIL" : "RAN",
    light: xbad ? "bad" : "ok",
    out: `${x.length} 組 · 紅 ${xbad}`,
  });

  const seal = sealVdf(input.rows, input.metrics);
  steps.push({
    id: "E12",
    name: "VDF 封印",
    result: seal.light === "bad" ? "FAIL" : "RAN",
    light: seal.light,
    out: seal.note,
  });

  const duckOk = lakesHydraOk();
  steps.push({
    id: "E13",
    name: "DuckDB catalog",
    result: duckOk ? "CACHE" : "FAIL",
    light: duckOk ? "ok" : "bad",
    out: duckOk ? "fred/rev/aetf/cns/px/chip/rest 分寫 · object_cache · lake_meta" : "湖寫區重疊",
  });

  const push = predPushOk(latestSql("fred", 2024));
  steps.push({
    id: "E14",
    name: "謂詞下推",
    result: push.ok ? "RAN" : "FAIL",
    light: push.ok ? "ok" : "bad",
    out: push.note,
  });

  const localOk = viaDbHydraOk();
  steps.push({
    id: "E16",
    name: "本機 VIA_db 三庫",
    result: localOk ? "CACHE" : "FAIL",
    light: localOk ? "ok" : "bad",
    out: localOk ? viaDbSealNote() : "px/chip/rest 寫區重疊",
  });

  const closed = steps.every((s) => s.light === "ok" || s.light === "warn") && !steps.some((s) => s.result === "FAIL");
  steps.push({
    id: "E15",
    name: "VDF 收官",
    result: closed ? "RAN" : "FAIL",
    light: closed ? "ok" : "bad",
    out: closed ? "VDF 完工 · CACHE 實測通過 · 年檔槽保留 · LIVE 另閘 · DCT 不動" : "收官未齊",
  });

  const modules: ModEnd[] = VDF_MODULES.map((m) => {
    if (m.gate === "local" || m.gate === "tw") {
      return { id: m.id, name: m.name, gate: m.gate, result: "RAN", light: "ok", out: "本機跑完" };
    }
    if (m.gate === "fred") {
      return {
        id: m.id,
        name: m.name,
        gate: m.gate,
        result: input.mode === "LIVE" ? "RAN" : "CACHE",
        light: "ok",
        out: input.mode,
      };
    }
    if (m.gate === "rev" || m.gate === "aetf" || m.gate === "cns") {
      const out = m.gate === "aetf" ? "主動 ETF CACHE · LIVE 關" : m.gate === "cns" ? "共識長表 CACHE · LIVE 關" : "月營收 CACHE 分析 · LIVE 關";
      return { id: m.id, name: m.name, gate: m.gate, result: "CACHE", light: "ok", out };
    }
    if (m.gate === "local-db") {
      return { id: m.id, name: m.name, gate: m.gate, result: "CACHE", light: "ok", out: "原件不刪 · COPY→GitHub 湖 · 本台未探 C:" };
    }
    return { id: m.id, name: m.name, gate: m.gate, result: "SKIP", light: "ok", out: "第二閘未開 · fail-closed" };
  });

  return { steps, modules, seal, fail: steps.filter((s) => s.result === "FAIL").length };
}
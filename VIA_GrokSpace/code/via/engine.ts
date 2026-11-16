import definition from "../../../data/via/parameter-definition.json" with { type: "json" };
import { bollinger, computeAll, ema, sma } from "../vqg/engine";

export { bollinger, computeAll as run, ema, sma };
export const ENGINE_ID = definition.engine;
export const WATCHLIST_ENGINE_ID = definition.watchlistEngine;

export type WatchItem = (typeof definition.watchlist)[number];

export type WatchQuote = {
  symbol: string;
  price: number | null;
  changePct: number | null;
};

export type WatchRow = {
  code: string;
  symbol: string;
  name: string;
  groupLabel: string;
  story: string;
  role: string;
  price: number | null;
  changePct: number | null;
  place: string;
};

function placeOf(pct: number | null, ranked: number[]): string {
  if (pct == null || ranked.length < 5) return pct == null ? "沒有報價" : "樣本不足";
  const below = ranked.filter((value) => value < pct).length;
  const percentile = (below / ranked.length) * 100;
  if (percentile >= 80) return "清單裡偏強";
  if (percentile <= 20) return "清單裡偏弱";
  return "清單裡中間";
}

export function runWatchlist(quotes: WatchQuote[]): WatchRow[] {
  const bySymbol = new Map(quotes.map((row) => [row.symbol, row]));
  const ranked = definition.watchlist
    .map((item) => bySymbol.get(item.symbol)?.changePct)
    .filter((value): value is number => value != null && Number.isFinite(value));
  return definition.watchlist.map((item) => {
    const quote = bySymbol.get(item.symbol);
    const changePct = quote?.changePct ?? null;
    return {
      code: item.code,
      symbol: item.symbol,
      name: item.name,
      groupLabel: item.groupLabel,
      story: item.story,
      role: item.role,
      price: quote?.price ?? null,
      changePct,
      place: placeOf(changePct, ranked),
    };
  });
}

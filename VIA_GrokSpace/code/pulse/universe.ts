import definition from "../../../data/via/parameter-definition.json" with { type: "json" };

export type PulseGroup = "lead" | "tw" | "chain" | "macro" | "region";

export type SymbolSpec = {
  symbol: string;
  name: string;
  group: PulseGroup;
  unit?: string;
  board?: boolean;
};

export type MoverSpec = {
  symbol: string;
  name: string;
  story: string;
  role: "先動" | "同動" | "後動";
};

type WatchItem = (typeof definition.watchlist)[number];

function isGroup(value: string): value is PulseGroup {
  return value === "lead" || value === "tw" || value === "chain" || value === "macro" || value === "region";
}

export const WATCHLIST = definition.watchlist;

export const GROUP_LABEL: Record<PulseGroup, string> = {
  lead: "隔夜傳導",
  tw: "台股主機",
  chain: "權值觀察",
  macro: "匯率、利率、原物料",
  region: "其他時區",
};

export const SYMBOLS: SymbolSpec[] = WATCHLIST.filter((item): item is WatchItem & { group: PulseGroup } => isGroup(item.group)).map(
  (item) => ({
    symbol: item.symbol,
    name: item.name,
    group: item.group,
    unit: item.unit || undefined,
    board: item.board,
  }),
);

export const MOVERS: MoverSpec[] = WATCHLIST.filter(
  (item): item is WatchItem & { role: MoverSpec["role"] } => item.role === "先動" || item.role === "同動" || item.role === "後動",
).map((item) => ({
  symbol: item.symbol,
  name: item.name,
  story: item.story,
  role: item.role,
}));

export const SPARKS = WATCHLIST.filter((item) => item.spark).map((item) => ({
  symbol: item.symbol,
  name: item.name,
  zone: item.sparkZone,
}));

export const TIME_ZONES = WATCHLIST.filter((item) => item.timeZone).map((item) => ({
  zone: item.timeZone,
  name: item.timeName,
  symbol: item.symbol,
}));

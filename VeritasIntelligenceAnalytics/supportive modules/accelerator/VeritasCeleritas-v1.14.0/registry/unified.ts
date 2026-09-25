import { ACCEL_30, PRE_DEPRESS } from "@/lib/ps-stack";

export type ActionLayer = "stmt" | "call";

export type AstAction = {
  id: string;
  lineno: number;
  kind: string;
  name: string;
  layer: ActionLayer;
  unsafe: boolean;
  status: "idle" | "traced" | "accel" | "shield";
};

export type UnifyCommand = {
  id: string;
  title: string;
  origin: string;
  source: string;
  actions: AstAction[];
};

export const UNIFY_COMMANDS: UnifyCommand[] = [
  {
    id: "finance",
    title: "金融 NPV 矩陣",
    origin: "ExtraFinanceXEngine",
    source: [
      "def npv_batch(symbols):",
      "    out = []",
      "    for s in symbols:",
      "        cal = load_calendar(s)",
      "        flow = cashflow_frame(s)",
      "        irr(flow)",
      "        npv(flow)",
      "        json.dumps(s)",
      "        eval('blocked')",
      "        out.append(s)",
      "    return out",
    ].join("\n"),
    actions: [
      { id: "a1", lineno: 2, kind: "Assign", name: "out", layer: "stmt", unsafe: false, status: "idle" },
      { id: "a2", lineno: 3, kind: "For", name: "symbols", layer: "stmt", unsafe: false, status: "idle" },
      { id: "a3", lineno: 4, kind: "Assign", name: "cal", layer: "stmt", unsafe: false, status: "idle" },
      { id: "a4", lineno: 4, kind: "Call", name: "load_calendar", layer: "call", unsafe: false, status: "idle" },
      { id: "a5", lineno: 5, kind: "Assign", name: "flow", layer: "stmt", unsafe: false, status: "idle" },
      { id: "a6", lineno: 5, kind: "Call", name: "cashflow_frame", layer: "call", unsafe: false, status: "idle" },
      { id: "a7", lineno: 6, kind: "Call", name: "irr", layer: "call", unsafe: false, status: "idle" },
      { id: "a8", lineno: 7, kind: "Call", name: "npv", layer: "call", unsafe: false, status: "idle" },
      { id: "a9", lineno: 8, kind: "Call", name: "dumps", layer: "call", unsafe: false, status: "idle" },
      { id: "a10", lineno: 9, kind: "Call", name: "eval", layer: "call", unsafe: true, status: "idle" },
      { id: "a11", lineno: 10, kind: "Call", name: "append", layer: "call", unsafe: false, status: "idle" },
      { id: "a12", lineno: 11, kind: "Return", name: "out", layer: "stmt", unsafe: false, status: "idle" },
    ],
  },
  {
    id: "quotes",
    title: "價量抓取",
    origin: "xfetch",
    source: [
      "def fetch_batch(tickers):",
      "    raw = xfetch(tickers)",
      "    text = decode_body(raw)",
      "    frame = to_frame(text)",
      "    cache_payload(frame)",
      "    return frame",
    ].join("\n"),
    actions: [
      { id: "q1", lineno: 2, kind: "Assign", name: "raw", layer: "stmt", unsafe: false, status: "idle" },
      { id: "q2", lineno: 2, kind: "Call", name: "xfetch", layer: "call", unsafe: false, status: "idle" },
      { id: "q3", lineno: 3, kind: "Assign", name: "text", layer: "stmt", unsafe: false, status: "idle" },
      { id: "q4", lineno: 3, kind: "Call", name: "decode_body", layer: "call", unsafe: false, status: "idle" },
      { id: "q5", lineno: 4, kind: "Assign", name: "frame", layer: "stmt", unsafe: false, status: "idle" },
      { id: "q6", lineno: 4, kind: "Call", name: "to_frame", layer: "call", unsafe: false, status: "idle" },
      { id: "q7", lineno: 5, kind: "Call", name: "cache_payload", layer: "call", unsafe: false, status: "idle" },
      { id: "q8", lineno: 6, kind: "Return", name: "frame", layer: "stmt", unsafe: false, status: "idle" },
    ],
  },
];

export const PS_UNDER_PY = [...PRE_DEPRESS, ...ACCEL_30].map((u) => ({
  id: u.code,
  title: u.title,
  owner: "python" as const,
}));

export function unifyCoverage(actions: AstAction[]): number {
  if (!actions.length) return 0;
  const done = actions.filter((a) => a.status === "accel" || a.status === "shield" || a.status === "traced").length;
  return Math.round((100 * done) / actions.length);
}

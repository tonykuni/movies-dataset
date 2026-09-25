export type SiteKind =
  | "parallel"
  | "numeric"
  | "io"
  | "serde"
  | "frame"
  | "cache"
  | "unsafe"
  | "serial";

export type SiteStatus = "idle" | "probed" | "wrapped" | "shielded";

export type ProbeSite = {
  id: string;
  name: string;
  depth: number;
  kind: SiteKind;
  backend: string;
  fallback: string;
  status: SiteStatus;
};

export type MountLib = {
  id: string;
  pip: string;
  version: string;
  role: string;
  installed: boolean;
};

export type MountCommand = {
  id: string;
  title: string;
  blurb: string;
  origin: string;
  sites: ProbeSite[];
};

export const MOUNT_LIBS: MountLib[] = [
  {
    id: "wrapt",
    pip: "wrapt",
    version: "2.4.1",
    role: "簽名不變的掛載包裝，指令可被加速仍保持原呼叫形狀",
    installed: true,
  },
  {
    id: "cloudpickle",
    pip: "cloudpickle",
    version: "3.1.2",
    role: "嵌套閉包可進行程池，補 pickle 蓋不到的熱路徑",
    installed: true,
  },
  {
    id: "loky",
    pip: "loky",
    version: "3.6.0",
    role: "可重用 CPU 行程池，防洩漏、自適應 worker",
    installed: true,
  },
  {
    id: "parso",
    pip: "parso",
    version: "0.8.7",
    role: "不 import 目標即可向下探 AST，安全分類加速點",
    installed: true,
  },
  {
    id: "watchdog",
    pip: "watchdog",
    version: "6.0.0",
    role: "源碼變更 CONNECT SYNC，自動再探並向中央回報",
    installed: true,
  },
];

export const MOUNT_STEPS = [
  { id: "connect", label: "CONNECT", desc: "wrapt 掛上指令，簽名不變" },
  { id: "probe", label: "PROBE", desc: "parso 向下探巢狀呼叫" },
  { id: "classify", label: "CLASSIFY", desc: "平行 / 數值 / IO / 不安全" },
  { id: "wrap", label: "WRAP", desc: "loky + cloudpickle 或盾" },
  { id: "sync", label: "SYNC", desc: "watchdog 熱同步" },
  { id: "report", label: "REPORT", desc: "心跳回中央系統" },
  { id: "cover", label: "COVER", desc: "每點都有後備 → 100%" },
] as const;

export const MOUNT_COMMANDS: MountCommand[] = [
  {
    id: "quotes",
    title: "價量抓取批次",
    blurb: "xfetch → JSON → Frame → 快取",
    origin: "VDS_M01_GlobalDataFetcher",
    sites: [
      { id: "q1", name: "fetch_batch", depth: 0, kind: "io", backend: "xfetch / curl_cffi", fallback: "urllib", status: "idle" },
      { id: "q2", name: "decode_body", depth: 1, kind: "serde", backend: "jiter", fallback: "json", status: "idle" },
      { id: "q3", name: "detect_encoding", depth: 1, kind: "serial", backend: "charset-normalizer", fallback: "utf-8", status: "idle" },
      { id: "q4", name: "to_frame", depth: 1, kind: "frame", backend: "narwhals / polars", fallback: "list[dict]", status: "idle" },
      { id: "q5", name: "map_tickers", depth: 0, kind: "parallel", backend: "loky", fallback: "ThreadPool", status: "idle" },
      { id: "q6", name: "cache_payload", depth: 1, kind: "cache", backend: "diskcache", fallback: "sqlite3", status: "idle" },
      { id: "q7", name: "compress_blob", depth: 2, kind: "serial", backend: "cramjam", fallback: "gzip", status: "idle" },
      { id: "q8", name: "heartbeat", depth: 0, kind: "serial", backend: "xreport", fallback: "logging", status: "idle" },
    ],
  },
  {
    id: "finance",
    title: "金融 NPV / IRR 矩陣",
    blurb: "列式行情 → 日曆 → 現金流指標",
    origin: "ExtraFinanceXEngine",
    sites: [
      { id: "f1", name: "load_calendar", depth: 0, kind: "serial", backend: "exchange-calendars", fallback: "weekday filter", status: "idle" },
      { id: "f2", name: "cashflow_frame", depth: 1, kind: "frame", backend: "narwhals", fallback: "list", status: "idle" },
      { id: "f3", name: "npv_vector", depth: 1, kind: "numeric", backend: "numpy-financial", fallback: "pure python", status: "idle" },
      { id: "f4", name: "irr_vector", depth: 1, kind: "numeric", backend: "numpy-financial", fallback: "newton", status: "idle" },
      { id: "f5", name: "map_symbols", depth: 0, kind: "parallel", backend: "loky", fallback: "ThreadPool", status: "idle" },
      { id: "f6", name: "pickle_worker", depth: 1, kind: "parallel", backend: "cloudpickle", fallback: "pickle", status: "idle" },
      { id: "f7", name: "guard_eval", depth: 2, kind: "unsafe", backend: "shield", fallback: "deny", status: "idle" },
      { id: "f8", name: "report_kpi", depth: 0, kind: "serial", backend: "xreport", fallback: "logging", status: "idle" },
    ],
  },
  {
    id: "filings",
    title: "財報 PDF 探鏈",
    blurb: "PDF → 繁中對齊 → 表抽取",
    origin: "ExtraPdfEngine",
    sites: [
      { id: "p1", name: "open_pdf", depth: 0, kind: "io", backend: "pymupdf", fallback: "stdlib bytes", status: "idle" },
      { id: "p2", name: "zh_align", depth: 1, kind: "serial", backend: "zhconv", fallback: "identity", status: "idle" },
      { id: "p3", name: "table_extract", depth: 1, kind: "frame", backend: "narwhals", fallback: "rows", status: "idle" },
      { id: "p4", name: "page_map", depth: 0, kind: "parallel", backend: "loky", fallback: "ThreadPool", status: "idle" },
      { id: "p5", name: "json_dump", depth: 1, kind: "serde", backend: "jiter", fallback: "json", status: "idle" },
      { id: "p6", name: "watch_dir", depth: 0, kind: "serial", backend: "watchdog", fallback: "manual xsync", status: "idle" },
      { id: "p7", name: "os_system", depth: 2, kind: "unsafe", backend: "shield", fallback: "deny", status: "idle" },
    ],
  },
];

export const CPU_POLICY = {
  architecture: "CPU-only",
  physical: 2,
  workers: 2,
  memHeadroom: "L3-aware chunk",
  gpu: "disabled",
  safety: "no eval · no builtins patch · AST-only probe",
  adaptive: "workers = min(physical, ram_gb * 2, pressure_gate)",
};

export function kindLabel(k: SiteKind): string {
  return {
    parallel: "平行",
    numeric: "數值",
    io: "IO",
    serde: "序列化",
    frame: "表",
    cache: "快取",
    unsafe: "盾",
    serial: "串行",
  }[k];
}

export function coverageOfSites(sites: ProbeSite[]): number {
  if (!sites.length) return 0;
  const done = sites.filter((s) => s.status === "wrapped" || s.status === "shielded").length;
  return Math.round((100 * done) / sites.length);
}

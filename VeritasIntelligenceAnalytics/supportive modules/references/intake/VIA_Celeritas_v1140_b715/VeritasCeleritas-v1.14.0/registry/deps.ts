import { SCAN } from "@/lib/scan";

export type EdgeKind = "need" | "accel" | "feed" | "fallback";

export type DepNode = {
  id: string;
  title: string;
  layer: number;
  layerLabel: string;
  x: number;
  y: number;
};

export type DepEdge = {
  from: string;
  to: string;
  kind: EdgeKind;
  via: string;
  note: string;
};

export type DomainState = "live" | "partial" | "degraded" | "blocked" | "empty";

export const LAYER_LABELS = [
  "後備",
  "執行期",
  "數值",
  "載荷",
  "領域",
  "編排",
] as const;

export const DEP_NODES: DepNode[] = [
  { id: "via_stdlib", title: "標準庫後備", layer: 0, layerLabel: "後備", x: 70, y: 250 },
  { id: "via_sys", title: "系統 / 日誌", layer: 1, layerLabel: "執行期", x: 230, y: 78 },
  { id: "via_codec", title: "壓縮 / 雜湊", layer: 1, layerLabel: "執行期", x: 230, y: 230 },
  { id: "via_serde", title: "JSON / 序列化", layer: 1, layerLabel: "執行期", x: 230, y: 382 },
  { id: "via_core", title: "數值 / JIT", layer: 2, layerLabel: "數值", x: 410, y: 150 },
  { id: "via_accel", title: "平行 / 非同步", layer: 2, layerLabel: "數值", x: 410, y: 330 },
  { id: "via_df", title: "DataFrame / SQL", layer: 3, layerLabel: "載荷", x: 590, y: 70 },
  { id: "via_cache", title: "快取 / KV", layer: 3, layerLabel: "載荷", x: 590, y: 230 },
  { id: "via_io", title: "HTTP / 檔案 / PDF", layer: 3, layerLabel: "載荷", x: 590, y: 390 },
  { id: "via_vision", title: "影像 / OCR", layer: 4, layerLabel: "領域", x: 780, y: 36 },
  { id: "via_gpu", title: "GPU 表", layer: 4, layerLabel: "領域", x: 780, y: 148 },
  { id: "via_ml", title: "機器學習", layer: 4, layerLabel: "領域", x: 780, y: 260 },
  { id: "via_fin", title: "金融 / 日曆", layer: 4, layerLabel: "領域", x: 780, y: 390 },
  { id: "via_bridge", title: "VIA 編排", layer: 5, layerLabel: "編排", x: 960, y: 140 },
  { id: "via_mount", title: "掛載 / 探針", layer: 5, layerLabel: "編排", x: 960, y: 330 },
];

export const DEP_EDGES: DepEdge[] = [
  { from: "via_sys", to: "via_stdlib", kind: "fallback", via: "HardwareTuner", note: "psutil 缺則 os.cpu_count / logging" },
  { from: "via_codec", to: "via_stdlib", kind: "fallback", via: "CompressionEngine", note: "cramjam / zstd 缺則 gzip · lzma · hashlib" },
  { from: "via_serde", to: "via_stdlib", kind: "fallback", via: "JSONEngine", note: "jiter / orjson 缺則 json" },
  { from: "via_core", to: "via_stdlib", kind: "fallback", via: "numpy 後備", note: "無 ndarray 時走純 Python 數值" },
  { from: "via_accel", to: "via_stdlib", kind: "fallback", via: "ParallelEngine", note: "ray / joblib 缺則 ThreadPoolExecutor" },
  { from: "via_cache", to: "via_stdlib", kind: "fallback", via: "AutotuneCache", note: "diskcache 缺則 sqlite3 WAL" },
  { from: "via_io", to: "via_stdlib", kind: "fallback", via: "xfetch", note: "curl_cffi / requests 缺則 urllib" },

  { from: "via_accel", to: "via_sys", kind: "need", via: "HardwareTuner", note: "執行緒預算依賴 CPU / 記憶體探測" },
  { from: "via_core", to: "via_accel", kind: "accel", via: "ANC-05 ENV", note: "NUMBA / OMP / POLARS 執行緒上限" },

  { from: "via_df", to: "via_core", kind: "need", via: "DataFrameEngine", note: "pandas 路徑與 Arrow 緩衝需要 ndarray" },
  { from: "via_df", to: "via_accel", kind: "accel", via: "polars / dask", note: "列式平行掃描、concat、sort" },

  { from: "via_cache", to: "via_codec", kind: "need", via: "CacheManager", note: "快取值壓縮" },
  { from: "via_cache", to: "via_serde", kind: "need", via: "AutotuneCache", note: "鍵值 JSON / msgpack 序列化" },

  { from: "via_io", to: "via_serde", kind: "need", via: "xfetch", note: "HTTP JSON 編解碼" },
  { from: "via_io", to: "via_codec", kind: "need", via: "charset / cramjam", note: "編碼偵測與壓縮體" },
  { from: "via_df", to: "via_io", kind: "feed", via: "connectorx / fastexcel", note: "DB / Excel → Arrow / Polars" },

  { from: "via_vision", to: "via_core", kind: "need", via: "OpenCV", note: "影像即 ndarray" },
  { from: "via_vision", to: "via_io", kind: "feed", via: "PIL / pymupdf", note: "檔案與財報 PDF 進影像層" },

  { from: "via_gpu", to: "via_core", kind: "need", via: "cudf", note: "GPU 陣列語意" },
  { from: "via_gpu", to: "via_df", kind: "accel", via: "cudf", note: "GPU DataFrame 加速列式路徑" },

  { from: "via_ml", to: "via_core", kind: "need", via: "sklearn / torch", note: "張量與特徵陣列" },
  { from: "via_ml", to: "via_df", kind: "need", via: "訓練表", note: "表格式樣本進模型" },
  { from: "via_ml", to: "via_accel", kind: "accel", via: "joblib", note: "模型平行擬合" },

  { from: "via_fin", to: "via_core", kind: "need", via: "ExtraFinanceXEngine", note: "NPV / IRR / 技術指標" },
  { from: "via_fin", to: "via_df", kind: "need", via: "pandas_ta / calendars", note: "列式行情與交易日曆" },
  { from: "via_fin", to: "via_io", kind: "feed", via: "xfetch", note: "外部價量與財報抓取" },

  { from: "via_bridge", to: "via_sys", kind: "need", via: "VIA_EnvManager", note: "環境探測與相位心跳" },
  { from: "via_bridge", to: "via_core", kind: "accel", via: "CeleritasKernel", note: "數值熱路徑" },
  { from: "via_bridge", to: "via_accel", kind: "accel", via: "ANC-00 ENGINES", note: "交叉平行調度" },
  { from: "via_bridge", to: "via_df", kind: "accel", via: "ExtraFrameEngine", note: "narwhals / polars 適配" },
  { from: "via_bridge", to: "via_io", kind: "accel", via: "xfetch", note: "TLS HTTP 出口" },
  { from: "via_bridge", to: "via_fin", kind: "accel", via: "ExtraFinanceXEngine", note: "金融運算出口" },
  { from: "via_mount", to: "via_stdlib", kind: "fallback", via: "ast / pickle / futures", note: "無 wrapt/loky 時仍可掛載" },
  { from: "via_mount", to: "via_sys", kind: "need", via: "HardwareTuner", note: "worker 數看實體核與記憶體" },
  { from: "via_mount", to: "via_accel", kind: "accel", via: "loky", note: "CPU 行程池疊在平行層上" },
  { from: "via_bridge", to: "via_mount", kind: "need", via: "MountPilot", note: "智慧掛載與中央回報" },
];

export const KIND_LABEL: Record<EdgeKind, string> = {
  need: "硬依賴",
  accel: "加速",
  feed: "資料流",
  fallback: "後備",
};

export function coverageOf(id: string): { installed: number; total: number; pct: number } {
  if (id === "via_stdlib") {
    const s = SCAN.stdlibSummary;
    return { installed: s.installed, total: s.total, pct: s.coverage };
  }
  const b = SCAN.byEnv[id] ?? { installed: 0, total: 0, missing: 0 };
  const pct = b.total ? Math.round((100 * b.installed) / b.total) : 0;
  return { installed: b.installed, total: b.total, pct };
}

export function domainStates(): Record<string, DomainState> {
  const order = [...DEP_NODES].sort((a, b) => a.layer - b.layer);
  const state: Record<string, DomainState> = {};
  for (const node of order) {
    const { pct, installed } = coverageOf(node.id);
    if (node.id === "via_stdlib" || pct === 100) {
      state[node.id] = "live";
      continue;
    }
    if (installed > 0) {
      state[node.id] = "partial";
      continue;
    }
    const needs = DEP_EDGES.filter((e) => e.from === node.id && e.kind === "need");
    const blocked = needs.some((e) => {
      const s = state[e.to];
      return s === "empty" || s === "blocked";
    });
    if (blocked) {
      state[node.id] = "blocked";
      continue;
    }
    const hasFallback = DEP_EDGES.some(
      (e) => e.from === node.id && e.kind === "fallback" && e.to === "via_stdlib",
    );
    state[node.id] = hasFallback ? "degraded" : "empty";
  }
  return state;
}

export function edgesFrom(id: string): DepEdge[] {
  return DEP_EDGES.filter((e) => e.from === id);
}

export function edgesTo(id: string): DepEdge[] {
  return DEP_EDGES.filter((e) => e.to === id);
}

export function blastRadius(id: string): string[] {
  const seen = new Set<string>();
  const stack = DEP_EDGES.filter((e) => e.to === id).map((e) => e.from);
  while (stack.length) {
    const n = stack.pop()!;
    if (seen.has(n)) continue;
    seen.add(n);
    for (const e of DEP_EDGES) {
      if (e.to === n && !seen.has(e.from)) stack.push(e.from);
    }
  }
  return [...seen];
}

export const STATE_LABEL: Record<DomainState, string> = {
  live: "完整",
  partial: "部分",
  degraded: "降級",
  blocked: "阻塞",
  empty: "未裝",
};

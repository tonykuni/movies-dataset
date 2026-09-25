/** VIA EnvManager 旗艦規範 SSOT。改這份再 `govPrompt()`，勿改散落的長文。 */

export const GOV_ID = "VIA_ENV_GOV";
export const GOV_LOG = "logs/env_governance.log";
export const GOV_LAUNCHER = "launch.ps1";

export const GOV_ENVS = [
  { id: "base", role: "host", note: "極簡啟動器 · 衝突不刪" },
  { id: "via_core", role: "core", note: "AST／SSOT／ruff" },
  { id: "via_vrn", role: "sub", note: "VRN PDF／NLP" },
  { id: "via_vdf", role: "sub", note: "Polars／DuckDB／FRED" },
  { id: "via_vap", role: "sub", note: "VAP Router" },
  { id: "via_nlp", role: "sub", note: "OpenCC" },
  { id: "via_iso_*", role: "slot", note: "衝突件專槽 · via_iso_numpy／via_iso_plotly 已釘 · 不進 PATH" },
] as const;

export const UV_MIRRORS = [
  { id: "tsinghua", url: "https://pypi.tuna.tsinghua.edu.cn/simple" },
  { id: "aliyun", url: "https://mirrors.aliyun.com/pypi/simple" },
  { id: "pypi", url: "https://pypi.org/simple" },
] as const;

export const LKGC_UV = {
  when: "2026-09-06",
  venv: ".venv-via_vdf",
  winner: "tsinghua",
  freeze: "locks/via_vdf.txt",
} as const;

/** 三鏡競向 · 台北探測時延（CACHE 模擬 · 本台不 HTTP） */
export const MIRROR_PROBE_MS = {
  tsinghua: 18,
  aliyun: 32,
  pypi: 210,
} as const;

/** uv ＋ 八路衝突快檢 · 與 GA-01–20／PS-01–20 分冊 */
export const UV_CLASH_TOOLS = [
  { id: "UVT-01", name: "PubGrub 圖", layer: "resolve", ms: 4, note: "SAT 學習不相容 · 不裝" },
  { id: "UVT-02", name: "uv pip check", layer: "installed", ms: 9, note: "已裝 metadata · 指令留母機" },
  { id: "UVT-03", name: "Pin 雙版", layer: "pin", ms: 1, note: "ENV_PINS 同包兩版 → via_iso_*" },
  { id: "UVT-04", name: "LKGC 漂移", layer: "lock", ms: 2, note: "意圖 vs 2026-09-06 成功組合" },
  { id: "UVT-05", name: "三鏡雜湊", layer: "mirror", ms: 6, note: "清華／阿里／官方競向" },
  { id: "UVT-06", name: "標記分叉", layer: "marker", ms: 3, note: "PEP 508 fork · 一包多版" },
  { id: "UVT-07", name: "Extra 互斥", layer: "extra", ms: 2, note: "extras／groups 不能同裝" },
  { id: "UVT-08", name: "九頭龍寫區", layer: "hydra", ms: 1, note: "G/L/C/V 寫區不互踩" },
] as const;

export const GOV_ACCEL = [
  { id: "GA-01", name: "AST 精準解析", job: "ast" },
  { id: "GA-02", name: "多語言語意", job: "sem" },
  { id: "GA-03", name: "九頭龍預警", job: "hydra" },
  { id: "GA-04", name: "依賴拓撲", job: "topo" },
  { id: "GA-05", name: "沙盒隔離", job: "sandbox" },
  { id: "GA-06", name: "自動 Patch", job: "patch" },
  { id: "GA-07", name: "三輪全景", job: "pano" },
  { id: "GA-08", name: "SSOT 對齊", job: "ssot" },
  { id: "GA-09", name: "矩陣 UI", job: "ui" },
  { id: "GA-10", name: "錯誤分群", job: "cluster" },
  { id: "GA-11", name: "複雜度", job: "perf" },
  { id: "GA-12", name: "多子系統同步", job: "sync" },
  { id: "GA-13", name: "版本回滾", job: "lkgc" },
  { id: "GA-14", name: "覆蓋率回歸", job: "cov" },
  { id: "GA-15", name: "修正順序", job: "order" },
  { id: "GA-16", name: "動態進度", job: "progress" },
  { id: "GA-17", name: "動態說明", job: "narrate" },
  { id: "GA-18", name: "非阻塞 PS", job: "ps" },
  { id: "GA-19", name: "多引擎整合", job: "poly" },
  { id: "GA-20", name: "uv 部署初始化", job: "uv" },
] as const;

export const GOV_PIPELINES = [
  { id: "G1", job: "GOV_AST", winner: "VIS-ENV-000001", write: "ast-src", layer: "ast", name: "AST／語法" },
  { id: "G2", job: "GOV_SSOT", winner: "VRN_SYN", write: "ssot-regex", layer: "ssot", name: "SSOT／Regex" },
  { id: "G3", job: "GOV_PLUG", winner: "VAP_MDL001", write: "plug-sub", layer: "plug", name: "VRN/VDF/VAP 解耦" },
  { id: "G4", job: "GOV_UV", winner: "SUP_MDL737", write: "uv-iso", layer: "uv", name: "uv 衝突隔離" },
  { id: "G5", job: "GOV_REG", winner: "VRN_AUDITU", write: "sandbox-reg", layer: "reg", name: "沙盒回歸" },
  { id: "G6", job: "GOV_UI", winner: "VIA_CGC", write: "ui-matrix", layer: "ui", name: "UI Matrix 部署" },
] as const;

export const GOV_ROUNDS = [
  { id: 1, name: "Parallel-Fixable", kind: "parallel" as const },
  { id: 2, name: "Sequence-Dependent", kind: "sequence" as const },
  { id: 3, name: "Harden／Lockfile", kind: "harden" as const },
] as const;

export const GOV_ZONES = ["MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"] as const;

export const GOV_REQUIRED_LIBS = [
  "polars",
  "duckdb",
  "pyarrow",
  "numpy",
  "pypdf",
  "pdfplumber",
  "opencc",
  "ruff",
  "pydantic",
  "fredapi",
] as const;

export const GOV_INVARIANTS = [
  "零九頭龍：job／winner／write／layer 不互踩，且不寫 L/C/V 湖",
  "VDF 收官 D1–D6 寫區與 L/C/V/G 全異；加速器與網具只掛不外呼",
  "衝突立拔隔離：via_iso_* · 禁止 conda remove／pip uninstall／刪 base",
  "LKGC：只從上次成功組合擴張 · 需使用者同意才 APPLY",
  "本台不 spawn conda／uv · 只產指令與鎖檔",
  "PS20 資料加速器與 GA-01–20 治理加速器分冊，不混 ID",
  "最多三輪；NLP／NET LIVE 另閘",
  "DCT01–20 不動",
  "旗艦 Mega-Prompt 已封為未來動作規範；原文「拔除／重建」＝新建 via_iso_*，不刪 base",
  "uv 三鏡競向（清華／阿里／官方）＋ UVT-01–08 快檢 · 只從 LKGC 擴張 · 不混 GA/PS ID",
] as const;

export const GOV_LOOP =
  "test → debug → upgrade → test → debug → optimize → test → debug → consolidate → test → debug → user-test → debug → activate → test → debug";

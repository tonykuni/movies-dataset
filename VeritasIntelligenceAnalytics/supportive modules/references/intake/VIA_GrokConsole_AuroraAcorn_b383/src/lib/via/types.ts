export type Light = "ok" | "warn" | "bad" | "idle" | "run" | "pending";

export type ToolKind = "accel" | "net" | "nlp" | "gov";

export type MountedTool = {
  id: string;
  kind: ToolKind;
  name: string;
  lane: string;
  version: string;
  status: Light;
  note: string;
};

export type FredRow = {
  seriesId: string;
  title: string;
  category: string;
  frequency: string;
  units: string;
  lastDate: string;
  lastValue: number | null;
  change: number | null;
  source: "FRED_LIVE" | "VDF_CACHE" | "DENIED";
  status: Light;
};

export type LogLine = {
  id: string;
  t: string;
  level: "INFO" | "WARN" | "FAIL" | "OK" | "GATE";
  step: string;
  msg: string;
  detail?: string;
};

export type PipelineStep = {
  id: string;
  name: string;
  title: string;
};

export type IntakeFile = {
  id: string;
  name: string;
  ext: string;
  size: number;
  lastModified: number;
  origin: "folder" | "drop";
  path?: string;
  text?: string;
  skipDup: boolean;
  dupOf?: string;
  fingerprint: string;
  status: Light;
  stuckStep: string | null;
  stuckDetail: string | null;
  steps: Record<string, Light>;
};

export type BasicInfo = {
  fileId: string;
  fileName: string;
  reportType: string;
  ticker: string;
  market: string;
  yfinanceTicker: string;
  yfinanceTwo: string;
  bloombergTicker: string;
  tickerKind: string;
  companyName: string;
  broker: string;
  brokerAbbr: string;
  reportDate: string;
  reportCode: string;
  language: string;
  period: string;
  pages: number;
  issuer: string;
  rating: string;
  ratingCat: string;
  validationStatus: string;
  validationRisk: "GREEN" | "YELLOW" | "RED";
  status: Light;
};

export type SummaryRow = {
  fileId: string;
  fileName: string;
  slot: string;
  bullet: string;
  entity: string;
  triple: string;
  confidence: number;
  grounded: boolean;
};

export type FinRow = {
  fileId: string;
  fileName: string;
  category: string;
  statement: string;
  item: string;
  dataName: string;
  period: string;
  value: number | null;
  unit: string;
  confidence: number;
  source: string;
  status: Light;
  grade?: "V" | "M" | "P";
  defects?: string[];
};

export type EngineRec = {
  id: string;
  name: string;
  kind: string;
  path: string;
  hash: string;
  accel: boolean;
  net: boolean;
  nlp: boolean;
  ssot: boolean;
  status: Light;
  note: string;
};

export type FetchMetrics = {
  concurrency: number;
  series: number;
  lakeRows: number;
  chunks: number;
  skipped: number;
  scanned: number;
  cacheHits: number;
  encodeMs: number;
  queryMs: number;
  fetchMs: number;
  wallMs: number;
  planFactor: number;
  active: number;
  conflicts: number;
  pipeline: boolean;
  skipRatio: number;
  isa: "scalar" | "avx2" | "avx512";
  f64Width: number;
  i32Width: number;
  align: number;
  kernel: string;
  downclock: boolean;
  phys: number;
  width: number;
  compactBytes: number;
  rowBytes: number;
  storeRatio: number;
  partitions: number;
  parquetBytes: number;
  parquetPages: number;
  parquetTokenRatio: number;
  parquetReadPages: number;
  parquetSkipPages: number;
  parquetRoundtrip: boolean;
};

export type Deck = "console" | "vdf" | "vrn" | "engine" | "var";

export type Activated = {
  vdf: boolean;
  vrn: boolean;
  engine: boolean;
  var: boolean;
};

export type MountDraft = { name: string; path: string; kind: string };

export type RepairKind = "NONE" | "REPAIRED" | "UNREPAIRABLE";

export type AuditRow = {
  engineId: string;
  engineName: string;
  kind: string;
  steps: Record<string, Light>;
  repair: RepairKind;
  findings: string[];
  status: Light;
  note: string;
};

export type AuditDetail = {
  id: string;
  t: string;
  engineId: string;
  engineName: string;
  step: string;
  finding: string;
  repair: RepairKind;
  status: Light;
};

export type GovRow = { key: string; value: string; status: "ok" | "warn" };

export type PlanLane = {
  id: string;
  engine: string;
  intended: "LIVE" | "LOCAL" | "SKIP";
  reason: string;
};

export type LaneResult = {
  id: string;
  engine: string;
  result: "LIVE" | "CACHE" | "LOCAL" | "SKIP" | "DENIED";
  rows: number;
  note: string;
};

export type FetchManifest = {
  network: string;
  series: number;
  lakeRows: number;
  wallMs: number;
  skipLanes: number;
};

export type AutoRow = {
  id: string;
  system: "VIA" | "VDF" | "VRN" | "ENG" | "GOV";
  name: string;
  light: Light;
  cycle: "TEST" | "DEBUG" | "OPTIMIZE" | "CONSOLIDATE" | "USER-TEST" | "ACTIVATE" | "PENDING";
  result: string;
  tomorrow: string;
  github: "in-tree" | "missing" | "contract";
};

export type HandoverRow = {
  id: string;
  system: string;
  light: Light;
  tonight: string;
  tomorrow: string;
  blocker: string;
  cmd: string;
};

import { VDF_FETCH_LANES, VDF_MODULES } from "./catalog.ts";
import { canFetchFred } from "./fred-api.ts";
import type { FetchMetrics } from "./types.ts";
import { TW_UNIVERSE_COUNTS, VDF_UNIFIED_PARAMS } from "./vdf-mother.ts";
import { isLocalLane, viaDbPart } from "./via-db-parts.ts";

export const VDF_DICT = {
  paramsSsot: "dict/VDF/_ssot/VDF_Extraction_Params_SSOT.json",
  headerRegistry: "dict/VDF/_ssot/VDF_DataScope_HeaderRegistry_SSOT.json",
  database: "dict/VDF/DATABASE",
  pointer: "dict/VDF/_active/VDF_ACTIVE_POINTER.json",
  fetchPlan: "dict/VDF/_active/VDF_PRODUCTION_FETCH_CONTROLLER_v016/registry/VDF_ProductionFetchPlan_v016.json",
  fetchManifest: "dict/VDF/_active/VDF_PRODUCTION_FETCH_CONTROLLER_v016/registry/VDF_ProductionFetchManifest_v016.json",
  fetchResult: "dict/VDF/_active/VDF_PRODUCTION_FETCH_CONTROLLER_v016/runtime/vdf_production_fetch_result_v016.json",
} as const;

export type GovRow = { key: string; value: string; status: "ok" | "warn" };

export function invokeVdfStatus(): GovRow[] {
  return [
    { key: "status", value: "VDF_ACTIVE_READER_READY", status: "ok" },
    { key: "policy", value: "Read SSOT. No delete. No Stop-Process. No exit.", status: "ok" },
    { key: "params_ssot", value: `本台精簡 · start ${VDF_UNIFIED_PARAMS.start} · batch ${VDF_UNIFIED_PARAMS.batch}`, status: "ok" },
    { key: "tw_universe", value: `焦點 ${TW_UNIVERSE_COUNTS.members} · 上市 ${TW_UNIVERSE_COUNTS.twse} · 上櫃 ${TW_UNIVERSE_COUNTS.tpex}`, status: "ok" },
    { key: "header_registry", value: VDF_DICT.headerRegistry, status: "warn" },
    { key: "database", value: `${VDF_DICT.database} · 本樹無實體 · 列式湖`, status: "warn" },
    { key: "active_pointer", value: VDF_DICT.pointer, status: "warn" },
  ];
}

export function invokeVdfFetchStatus(): GovRow[] {
  return [
    { key: "status", value: "VDF_PRODUCTION_FETCH_CONTROLLER_READY", status: "ok" },
    { key: "policy", value: "Network disabled unless dual-gate AND.", status: "ok" },
    { key: "fetch_plan", value: VDF_DICT.fetchPlan, status: "ok" },
    { key: "fetch_manifest", value: VDF_DICT.fetchManifest, status: "ok" },
    { key: "fetch_result", value: VDF_DICT.fetchResult, status: "ok" },
    { key: "modules", value: String(VDF_MODULES.length), status: "ok" },
    { key: "parquet", value: "PAR1 year pages · dict+u16 date · 比 JSON 省 token", status: "ok" },
  ];
}

export type PlanLane = {
  id: string;
  engine: string;
  intended: "LIVE" | "LOCAL" | "SKIP";
  reason: string;
};

export function buildProductionPlan(input: { confirmNet: boolean; apiKey: string; apiUrl: string; startYear: number }): {
  version: string;
  startYear: number;
  network: "ENABLED" | "DISABLED";
  lanes: PlanLane[];
} {
  const fred = canFetchFred(input);
  return {
    version: "v016",
    startYear: input.startYear,
    network: fred.ok ? "ENABLED" : "DISABLED",
    lanes: VDF_FETCH_LANES.map((l) => {
      if (isLocalLane(l.id) || ("local" in l && Boolean((l as { local?: boolean }).local))) {
        const part = viaDbPart(l.id);
        return {
          id: l.id,
          engine: l.engine,
          intended: "LOCAL",
          reason: part ? `本機 ${part.folder} · COPY_ONLY 不刪` : "本機三庫優先 · 原件不刪",
        };
      }
      return {
        id: l.id,
        engine: l.engine,
        intended: l.live && fred.ok ? "LIVE" : "SKIP",
        reason: l.live ? (fred.ok ? "雙閘通過" : fred.reason) : "車道未掛 · fail-closed",
      };
    }),
  };
}

export type LaneResult = {
  id: string;
  engine: string;
  result: "LIVE" | "CACHE" | "LOCAL" | "SKIP" | "DENIED";
  rows: number;
  note: string;
};

export function sealFetch(plan: ReturnType<typeof buildProductionPlan>, fred: { mode: "LIVE" | "CACHE" | "DENIED"; note: string; series: number; metrics: FetchMetrics }): {
  lanes: LaneResult[];
  manifest: { network: string; series: number; lakeRows: number; wallMs: number; skipLanes: number };
} {
  const lanes: LaneResult[] = plan.lanes.map((l) => {
    if (l.id === "FRED") {
      return { id: l.id, engine: l.engine, result: fred.mode, rows: fred.series, note: fred.note };
    }
    if (l.intended === "LOCAL" || isLocalLane(l.id)) {
      return { id: l.id, engine: l.engine, result: "LOCAL", rows: 0, note: `${l.reason} · 本台未探 C:` };
    }
    return { id: l.id, engine: l.engine, result: "SKIP", rows: 0, note: l.reason };
  });
  return {
    lanes,
    manifest: {
      network: plan.network,
      series: fred.series,
      lakeRows: fred.metrics.lakeRows,
      wallMs: fred.metrics.wallMs,
      skipLanes: lanes.filter((l) => l.result === "SKIP").length,
    },
  };
}

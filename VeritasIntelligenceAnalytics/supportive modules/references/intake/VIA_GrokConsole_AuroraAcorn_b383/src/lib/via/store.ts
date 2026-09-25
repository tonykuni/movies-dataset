import { create } from "zustand";
import { uid, nowStamp } from "@/lib/utils";
import { applyAuditPatch, auditEngine } from "./audit";
import { FOLDER_SEEDS, PIPELINE_STEPS, REGISTERED_ENGINES } from "./catalog";
import { motherIntakeFiles } from "./incoming-roster";
import { DEFAULT_FRED_API } from "./fred-api";
import { DEFAULT_EIA_API, canFetchEia } from "./eia-api";
import { TOOL_BUS, byKinds, patchTools } from "./bus";
import { applyCpuToPlan, pairAccels, type PairPlan, type PairRow } from "./accel";
import { autoTestAll, buildHandover, nextDayIso } from "./autotest";
import { dispatchDryRun, mintToken } from "./govern";
import { pullFred } from "./fred";
import { buildMarketBook, crossValidate, etfFlowSum, type MarketRow, type XValRow } from "./market-book";
import { runRepairPack, type RepairToolRow } from "./repair-pack";
import { completeVdf } from "./complete-vdf";
import { sealGoLive, sealParquet, sealVrn, sealConsole, sealEng075, sealGlss, sealEng077, sealLocalDb, type Seal } from "./seal";
import { sealVap } from "./vap";
import { runGovEnv, motherPathScript } from "./gov-env";
import { runEnvManager } from "./env-manager";
import { runCentralEntry } from "./central-entry";
import { megaSeal } from "./gov-mega";
import { runVdfToEnd, type EndStep, type ModEnd } from "./vdf-end";
import { packAea, type AetfCash, type AetfHoldDelta, type AetfRow, type AetfScope } from "./active-etf";
import { aggregateHolds, defaultPicked, fundPickList, type FundPick, type HoldAggRow } from "./aetf-hold-matrix";
import { specWideRows, type SpecWide } from "./spectrum";
import { runCnsSim, type CnsCompare, type CnsLong, type CnsMode, type CnsRow } from "./consensus";
import { inspectGap, afterCacheCoverage, dualGateNext, LAKE_START_YEAR, nextRoundNeeded, type GapReport } from "./gap-fill";
import { emptyCkpt, type LakeCkpt } from "./lake-incr";
import { cacheRevRows, canFetchRev, groupAnalysis, latestSnapshot, revContract, type RevGroup, type RevRow } from "./tw-revenue";
import { runGffSim, type GffRow } from "./gff";
import { hydrateVdf } from "./hydrate";
import { buildProductionPlan, invokeVdfFetchStatus, invokeVdfStatus, sealFetch } from "./vdf-controller";
import type {
  Activated,
  AuditDetail,
  AuditRow,
  AutoRow,
  BasicInfo,
  Deck,
  EngineRec,
  FetchManifest,
  FetchMetrics,
  FinRow,
  FredRow,
  GovRow,
  HandoverRow,
  IntakeFile,
  LaneResult,
  Light,
  LogLine,
  MountDraft,
  MountedTool,
  PlanLane,
  RepairKind,
  SummaryRow,
  ToolKind,
} from "./types";
import { decideStep, statusFromSteps } from "./pipeline";
import { applySsot, HANDOVER_STAMP, isolationScript, isolationSteps, scanEnvConflicts, type IsoStep } from "./inventory";
import { runProcessPack, type ProcRow } from "./processes";
import { completeVrn } from "./complete-vrn";
import { parseFilename, packBasic, packSummary, packFinance } from "./vrn";
import { runVrnToEnd, type VrnStep } from "./vrn-end";
import { runViaToEnd, type ViaStep } from "./via-end";

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

function pushLog(
  list: LogLine[],
  level: LogLine["level"],
  step: string,
  msg: string,
  detail?: string,
): LogLine[] {
  return [...list, { id: uid("log"), t: nowStamp(), level, step, msg, detail }].slice(-400);
}

function classifyDropped(file: File, existing: IntakeFile[], text?: string): IntakeFile {
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  const fingerprint = `${ext}:${file.size}`;
  const dupOf = existing.find((f) => f.fingerprint === fingerprint)?.name;
  return {
    id: uid("in"),
    name: file.name,
    ext,
    size: file.size,
    lastModified: file.lastModified,
    origin: "drop",
    text,
    skipDup: Boolean(dupOf),
    dupOf,
    fingerprint,
    status: "idle",
    stuckStep: null,
    stuckDetail: null,
    steps: Object.fromEntries(PIPELINE_STEPS.map((s) => [s.id, "idle"])),
  };
}

type State = {
  deck: Deck;
  setDeck: (d: Deck) => void;
  fredKey: string;
  fredApi: string;
  eiaKey: string;
  eiaApi: string;
  startYear: number;
  lakeCkpt: LakeCkpt;
  gapReport: GapReport | null;
  setFredKey: (v: string) => void;
  setFredApi: (v: string) => void;
  setEiaKey: (v: string) => void;
  setEiaApi: (v: string) => void;
  setStartYear: (y: number) => void;
  tools: MountedTool[];
  busLogs: LogLine[];
  activated: Activated;
  vdfBusy: boolean;
  vdfProgress: number;
  vdfNote: string;
  fredRows: FredRow[];
  collapsed: Record<string, boolean>;
  toggleCat: (c: string) => void;
  setCatsOpen: (open: boolean) => void;
  vdfLogs: LogLine[];
  vdfTab: string;
  setVdfTab: (t: string) => void;
  pairRows: PairRow[];
  pairPlan: PairPlan | null;
  fetchMetrics: FetchMetrics | null;
  vdfGov: GovRow[];
  vdfFetchGov: GovRow[];
  vdfPlanLanes: PlanLane[];
  vdfLaneResults: LaneResult[];
  vdfManifest: FetchManifest | null;
  vdfSeal: Seal | null;
  vdfEndRows: EndStep[];
  vdfModRows: ModEnd[];
  marketRows: MarketRow[];
  xvalRows: XValRow[];
  etfFlow: { aum: number; inFlow: number; outFlow: number } | null;
  revRows: RevRow[];
  revGroups: RevGroup[];
  revNote: string;
  gffRows: GffRow[];
  gffNote: string;
  aetfRows: AetfRow[];
  aetfNote: string;
  aetfVerify: AetfRow[];
  aetfNavLogic: AetfRow[];
  aetfJsonMap: AetfRow[];
  aetfCash: AetfCash[];
  aetfDeltas: AetfHoldDelta[];
  aetfFilter: string;
  setAetfFilter: (q: string) => void;
  aetfPicked: string[];
  aetfHoldAgg: HoldAggRow[];
  aetfFundPicks: FundPick[];
  toggleAetfPick: (ticker: string) => void;
  aetfPickAll: () => void;
  aetfPickNone: () => void;
  aetfScope: AetfScope | "ALL";
  setAetfScope: (s: AetfScope | "ALL") => void;
  specRows: SpecWide[];
  cnsRows: CnsRow[];
  cnsNote: string;
  cnsLong: CnsLong[];
  cnsCompare: CnsCompare[];
  cnsMode: CnsMode;
  cnsQuery: string;
  setCnsMode: (m: CnsMode) => void;
  setCnsQuery: (q: string) => void;
  runVdf: () => Promise<void>;
  vdfNextRound: boolean;
  roundConsent: boolean;
  setRoundConsent: (v: boolean) => void;
  runVdfNextRound: () => Promise<void>;

  files: IntakeFile[];
  intakeLogs: LogLine[];
  intakeBusy: boolean;
  intakeProgress: number;
  intakeTab: string;
  setIntakeTab: (t: string) => void;
  addDropped: (list: File[]) => void;
  toggleSkip: (id: string) => void;
  skipAllDups: boolean;
  setSkipAllDups: (v: boolean) => void;
  runIntake: () => Promise<void>;
  vrnSeal: Seal | null;
  vrnEndSteps: VrnStep[];
  viaEndSteps: ViaStep[];
  liveSeal: Seal | null;
  goLiveRows: Seal[];
  procRows: ProcRow[];
  runSeal: () => Promise<void>;
  basics: BasicInfo[];
  summaries: SummaryRow[];
  finances: FinRow[];

  engines: EngineRec[];
  engineLogs: LogLine[];
  engineBusy: boolean;
  confirmNet: boolean;
  confirmNlp: boolean;
  setConfirmNet: (v: boolean) => void;
  setConfirmNlp: (v: boolean) => void;
  pendingMounts: MountDraft[];
  setPendingMounts: (p: MountDraft[]) => void;
  mountEngines: () => Promise<void>;

  autoAudit: boolean;
  setAutoAudit: (v: boolean) => void;
  auditBusy: boolean;
  auditProgress: number;
  auditTab: string;
  setAuditTab: (t: string) => void;
  auditLogs: LogLine[];
  auditRows: AuditRow[];
  auditDetails: AuditDetail[];
  repairTools: RepairToolRow[];
  runAudit: () => Promise<void>;
  downToken: string;
  downCommit: boolean;
  setDownToken: (v: string) => void;
  setDownCommit: (v: boolean) => void;
  mintDownToken: () => void;
  runDownward: () => void;
  downRows: ReturnType<typeof dispatchDryRun>;
  autoRows: AutoRow[];
  handoverRows: HandoverRow[];
  handoverDay: string;
  runAutoTest: () => void;
  bootGovern: () => void;
  bootDone: boolean;
  isoSteps: IsoStep[];
  isoScript: string;
  mintIsolation: () => void;
  runEnvManagerPlan: (consent?: boolean) => void;
  pathScript: string;
};

export const useVia = create<State>((set, get) => {
  const bus = (level: LogLine["level"], step: string, msg: string) =>
    set((s) => ({ busLogs: pushLog(s.busLogs, level, step, msg) }));

  const BOOT = hydrateVdf();

  function refreshAuto() {
    const s = get();
    const rows = autoTestAll({
      engines: s.engines,
      activated: s.activated,
      confirmNet: s.confirmNet,
      confirmNlp: s.confirmNlp,
      vdfRan: s.activated.vdf,
      vdfLive: s.fredRows.some((r) => r.source === "FRED_LIVE"),
      vrnRan: s.activated.vrn,
      vrnPass: s.files.filter((f) => f.status === "ok").length,
      vrnFail: s.files.filter((f) => f.status === "bad").length,
      varRan: s.activated.var,
    });
    const day = nextDayIso();
    set({ autoRows: rows, handoverRows: buildHandover(rows, day), handoverDay: day });
  }

  async function ensureMounted(kinds: ToolKind[], logKey: "vdfLogs" | "intakeLogs" | "engineLogs" | "auditLogs") {
    const need = get().tools.filter((t) => kinds.includes(t.kind) && t.status !== "ok");
    if (need.length === 0) {
      set((s) => ({
        [logKey]: pushLog(s[logKey], "OK", "BUS", `${kinds.join("+")} 已在總線 · 跳過重掛`),
        busLogs: pushLog(s.busLogs, "OK", "BUS", `${kinds.join("+")} 已在總線`),
      }));
      return;
    }
    set((s) => ({ tools: patchTools(s.tools, byKinds(kinds), "run") }));
    await Promise.all(
      need.map(async (t) => {
        await sleep(12);
        set((s) => ({
          tools: patchTools(s.tools, (x) => x.id === t.id, "ok"),
          [logKey]: pushLog(s[logKey], "OK", "MOUNT", `${t.id} ${t.name} 在位`),
          busLogs: pushLog(s.busLogs, "OK", "MOUNT", `${t.id} 掛上總線`),
        }));
      }),
    );
  }

  return {
    deck: "console",
    setDeck: (d) => set({ deck: d }),
    fredKey: "",
    fredApi: DEFAULT_FRED_API,
    eiaKey: "",
    eiaApi: DEFAULT_EIA_API,
    startYear: LAKE_START_YEAR,
    lakeCkpt: afterCacheCoverage(
      emptyCkpt(LAKE_START_YEAR),
      new Date().getUTCFullYear(),
      BOOT.rows.filter((r) => r.lastValue != null).length,
      BOOT.rows.length,
    ),
    gapReport: null,
    setFredKey: (v) => set({ fredKey: v }),
    setFredApi: (v) => set({ fredApi: v }),
    setEiaKey: (v) => set({ eiaKey: v }),
    setEiaApi: (v) => set({ eiaApi: v }),
    setStartYear: (y) => set({ startYear: y }),
    tools: TOOL_BUS.map((t) => ({ ...t })),
    busLogs: [],
    activated: { vdf: BOOT.done.fail === 0, vrn: BOOT.vrn.pass > 0, engine: true, var: false },
    vdfBusy: false,
    vdfProgress: 100,
    vdfNote: BOOT.done.seal.note,
    fredRows: BOOT.rows,
    collapsed: {},
    toggleCat: (c) => set((s) => ({ collapsed: { ...s.collapsed, [c]: !s.collapsed[c] } })),
    setCatsOpen: (open) =>
      set((s) => ({
        collapsed: Object.fromEntries(Array.from(new Set(s.fredRows.map((r) => r.category))).map((c) => [c, !open])),
      })),
    vdfLogs: [],
    vdfTab: "tab1",
    setVdfTab: (t) => set({ vdfTab: t }),
    pairRows: BOOT.pairRows,
    pairPlan: BOOT.pairPlan,
    fetchMetrics: BOOT.metrics,
    vdfGov: BOOT.gov,
    vdfFetchGov: BOOT.fetchGov,
    vdfPlanLanes: BOOT.lanes,
    vdfLaneResults: BOOT.laneResults,
    vdfManifest: BOOT.manifest,
    vdfSeal: BOOT.done.seal,
    vdfEndRows: BOOT.ended.steps,
    vdfModRows: BOOT.ended.modules,
    marketRows: BOOT.book,
    xvalRows: BOOT.xval,
    etfFlow: BOOT.flow,
    revRows: BOOT.revSnap,
    revGroups: BOOT.revGroups,
    revNote: BOOT.revNote,
    gffRows: BOOT.gff.rows,
    gffNote: BOOT.gff.note,
    aetfFilter: "",
    ...(() => {
      const aea = packAea(new Date(), "");
      return { aetfRows: aea.rows, aetfNote: aea.note, aetfVerify: aea.verify, aetfNavLogic: aea.navLogic, aetfJsonMap: aea.jsonMap, aetfCash: aea.cash, aetfDeltas: aea.deltas };
    })(),
    setAetfFilter: (q) => {
      const aea = packAea(new Date(), q);
      set({ aetfFilter: q, aetfDeltas: aea.deltas, aetfRows: aea.rows, aetfNote: aea.note, aetfVerify: aea.verify, aetfNavLogic: aea.navLogic, aetfJsonMap: aea.jsonMap, aetfCash: aea.cash });
    },
    aetfPicked: defaultPicked(),
    aetfHoldAgg: aggregateHolds(defaultPicked()),
    aetfFundPicks: fundPickList(),
    toggleAetfPick: (ticker) => {
      const cur = get().aetfPicked;
      const next = cur.includes(ticker) ? cur.filter((x) => x !== ticker) : [...cur, ticker];
      set({ aetfPicked: next, aetfHoldAgg: aggregateHolds(next) });
    },
    aetfPickAll: () => {
      const scope = get().aetfScope;
      const all = fundPickList()
        .filter((f) => f.hasHold && (scope === "ALL" || f.scope === scope))
        .map((f) => f.ticker);
      set({ aetfPicked: all, aetfHoldAgg: aggregateHolds(all) });
    },
    aetfPickNone: () => set({ aetfPicked: [], aetfHoldAgg: [] }),
    aetfScope: "TW",
    setAetfScope: (s) => set({ aetfScope: s }),
    specRows: specWideRows(),
    ...(() => {
      const boot = runCnsSim({ mode: "GROUP", query: "2330" });
      return { cnsRows: boot.rows, cnsNote: boot.note, cnsLong: boot.long, cnsCompare: boot.compare };
    })(),
    cnsMode: "GROUP" as const,
    cnsQuery: "2330",
    setCnsMode: (m) => {
      const sim = runCnsSim({ mode: m, query: get().cnsQuery, confirmNet: get().confirmNet });
      set({ cnsMode: m, cnsRows: sim.rows, cnsNote: sim.note, cnsLong: sim.long, cnsCompare: sim.compare });
    },
    setCnsQuery: (q) => {
      const sim = runCnsSim({ mode: get().cnsMode, query: q, confirmNet: get().confirmNet });
      set({ cnsQuery: q, cnsRows: sim.rows, cnsNote: sim.note, cnsLong: sim.long, cnsCompare: sim.compare });
    },
    runVdf: async () => {
      if (get().vdfBusy) {
        while (get().vdfBusy) await sleep(40);
        return;
      }
      const { fredKey, fredApi, startYear, confirmNet, eiaKey, eiaApi } = get();
      const plan = pairAccels();
      const prod = buildProductionPlan({ confirmNet, apiKey: fredKey, apiUrl: fredApi, startYear });
      set({
        vdfBusy: true,
        vdfProgress: 8,
        vdfNote: `Invoke-VDF-Fetch v016 · 網 ${prod.network} · 搭配 ${plan.active}/20`,
        vdfLogs: [],
        fredRows: [],
        pairRows: plan.rows,
        pairPlan: plan,
        fetchMetrics: null,
        vdfGov: invokeVdfStatus(),
        vdfFetchGov: invokeVdfFetchStatus(),
        vdfPlanLanes: prod.lanes,
        vdfLaneResults: [],
        vdfManifest: null,
      });
      bus("INFO", "VDF", `擷取啟動 · 計畫加乘 ×${plan.planFactor} · 網 ${prod.network}`);
      const mountP = ensureMounted(["accel", "net"], "vdfLogs");
      const eiaGate = canFetchEia({ confirmNet, apiKey: eiaKey, apiUrl: eiaApi });
      set((s) => ({
        vdfLogs: pushLog(
          pushLog(
            s.vdfLogs,
            fredKey && confirmNet ? "GATE" : "WARN",
            "NET_GATE",
            confirmNet
              ? fredKey
                ? "雙閘 AND · VIA_NET_CONSENT × KEY · FRED 車道可 LIVE"
                : "閘 1 開 · KEY 空 · 不外呼"
              : "NET 閘未確認 · 零外呼 · 列式湖走快取",
          ),
          "WARN",
          "EIA_PARAM",
          eiaGate.ok ? "EIA LIVE（旗不應開）" : eiaGate.reason,
        ),
        vdfNote: "管線：掛載 ∥ FRED / 編碼 / 查詢",
        vdfProgress: 35,
      }));
      try {
        const [, result] = await Promise.all([
          mountP,
          pullFred({ data: { apiKey: fredKey, startYear, apiUrl: fredApi, confirmNet } }),
        ]);
        const cpuPlan = applyCpuToPlan(plan, {
          isa: result.metrics.isa,
          model: "server",
          flags: [],
          f64Width: result.metrics.f64Width,
          i32Width: result.metrics.i32Width,
          align: result.metrics.align,
          vector: 2048,
          batch: 65536,
          kernel: result.metrics.kernel,
          downclock: result.metrics.downclock,
          note: result.metrics.kernel,
        });
        const sealed = sealFetch(prod, {
          mode: result.mode,
          note: result.note,
          series: result.rows.length,
          metrics: result.metrics,
        });
        const book = buildMarketBook({ yfLive: false, akLive: false });
        const xval = crossValidate();
        const flow = etfFlowSum(book);
        const ended = runVdfToEnd({
          confirmNet,
          mode: result.mode,
          rows: result.rows,
          metrics: result.metrics,
        });
        const revPack = cacheRevRows();
        const revSnap = latestSnapshot(revPack);
        const revG = groupAnalysis(revPack);
        const revC = revContract();
        const revGate = canFetchRev({ confirmNet });
        const revNote = revGate.ok
          ? `LIVE ${revSnap.length}`
          : `CACHE 分析 ${revSnap.length} 家 · 最新 ${revC.latest} · 月檔 ${revC.files} · LIVE 關`;
        const gff = runGffSim();
        const aea = packAea(new Date(), get().aetfFilter);
        const cns = runCnsSim({ mode: get().cnsMode, query: get().cnsQuery, confirmNet });
        const filled = afterCacheCoverage(get().lakeCkpt, new Date().getUTCFullYear(), result.rows.filter((r) => r.lastValue != null).length, result.rows.length);
        const gap = inspectGap(filled, { start: get().startYear, live: confirmNet && result.mode === "LIVE" });
        const doneVdf = completeVdf({
          testsPass: ended.fail === 0 && ended.seal.light !== "bad",
          confirmNet,
          rows: result.rows,
          metrics: result.metrics,
        });
        set((s) => ({
          fredRows: result.rows,
          vdfNote: `${doneVdf.seal.note} · 跑完 E01–E15`,
          vdfProgress: 100,
          vdfBusy: false,
          activated: { ...s.activated, vdf: doneVdf.fail === 0 },
          fetchMetrics: result.metrics,
          pairRows: cpuPlan.rows,
          pairPlan: cpuPlan,
          vdfLaneResults: sealed.lanes,
          vdfManifest: sealed.manifest,
          vdfSeal: doneVdf.seal,
          vdfEndRows: ended.steps,
          vdfModRows: ended.modules,
          marketRows: book,
          xvalRows: xval,
          etfFlow: flow,
          revRows: revSnap,
          revGroups: revG,
          revNote,
          gffRows: gff.rows,
          gffNote: gff.note,
          aetfRows: aea.rows,
          aetfNote: aea.note,
          aetfVerify: aea.verify,
          aetfNavLogic: aea.navLogic,
          aetfJsonMap: aea.jsonMap,
          aetfCash: aea.cash,
          aetfDeltas: aea.deltas,
          cnsRows: cns.rows,
          cnsNote: cns.note,
          cnsLong: cns.long,
          cnsCompare: cns.compare,
          lakeCkpt: filled,
          gapReport: gap,
          vdfNextRound: nextRoundNeeded(gap),
          vdfLogs: pushLog(
            s.vdfLogs,
            ended.fail ? "WARN" : result.mode === "LIVE" ? "OK" : "WARN",
            "FRED",
            `${result.note} · E15 ${ended.seal.note}`,
            `wall ${result.metrics.wallMs}ms · skip ${sealed.manifest.skipLanes} · fail ${ended.fail}`,
          ),
          busLogs: pushLog(s.busLogs, ended.fail ? "WARN" : result.mode === "LIVE" ? "OK" : "WARN", "VDF", `跑完 · ${ended.seal.note} · ×${cpuPlan.planFactor}`),
          tools: patchTools(s.tools, (t) => t.id === "NET-FRED", result.mode === "LIVE" ? "ok" : "warn"),
        }));
        refreshAuto();
      } catch (err) {
        set((s) => ({
          vdfBusy: false,
          vdfProgress: 100,
          vdfNote: "擷取失敗",
          vdfLogs: pushLog(s.vdfLogs, "FAIL", "FRED", err instanceof Error ? err.message : "unknown"),
          busLogs: pushLog(s.busLogs, "FAIL", "VDF", "擷取失敗"),
        }));
      }
    },

    files: BOOT.vrn.files,
    intakeLogs: [],
    intakeBusy: false,
    intakeProgress: 100,
    intakeTab: "tab2",
    setIntakeTab: (t) => set({ intakeTab: t }),
    skipAllDups: true,
    setSkipAllDups: (v) =>
      set((s) => ({
        skipAllDups: v,
        files: s.files.map((f) => (f.dupOf ? { ...f, skipDup: v } : f)),
      })),
    addDropped: (list) => {
      void (async () => {
        const readable = new Set(["txt", "csv", "tsv", "md", "json", "html", "htm", "xlsx"]);
        const parsed: Array<{ file: File; text?: string }> = [];
        for (const file of list) {
          const ext = (file.name.split(".").pop() || "").toLowerCase();
          let text: string | undefined;
          if (readable.has(ext) && file.size < 2_000_000) {
            try {
              text = await file.text();
            } catch {
              text = undefined;
            }
          }
          parsed.push({ file, text });
        }
        set((s) => {
          let files = s.files;
          const added: IntakeFile[] = [];
          for (const row of parsed) {
            const rec = classifyDropped(row.file, files, row.text);
            added.push(rec);
            files = [...files, rec];
          }
          let logs = s.intakeLogs;
          let busLogs = s.busLogs;
          for (const rec of added) {
            const msg = rec.dupOf ? `拖入 ${rec.name} · 疑重複 ${rec.dupOf}` : `拖入 ${rec.name} · incoming`;
            logs = pushLog(logs, rec.dupOf ? "WARN" : "INFO", "I/O", msg);
            busLogs = pushLog(busLogs, rec.dupOf ? "WARN" : "INFO", "VRN", msg);
          }
          return { files, intakeLogs: logs, busLogs };
        });
      })();
    },
    toggleSkip: (id) =>
      set((s) => ({ files: s.files.map((f) => (f.id === id ? { ...f, skipDup: !f.skipDup } : f)) })),
    basics: BOOT.vrn.basics,
    summaries: BOOT.vrn.summaries,
    finances: BOOT.vrn.finances,
    runIntake: async () => {
      if (get().intakeBusy) {
        while (get().intakeBusy) await sleep(40);
        return;
      }
      const snapshot = get().files;
      set({
        intakeBusy: true,
        intakeProgress: 2,
        intakeTab: "tab1",
        basics: [],
        summaries: [],
        finances: [],
        files: snapshot.map((f) => ({
          ...f,
          status: "idle",
          stuckStep: null,
          stuckDetail: null,
          steps: Object.fromEntries(PIPELINE_STEPS.map((s) => [s.id, "idle"])),
        })),
        intakeLogs: pushLog([], "INFO", "START", `VRN 驗證 ${snapshot.length} 件 · 去重=${get().skipAllDups ? "ON" : "OFF"}`),
      });
      bus("INFO", "VRN", "研報管線啟動");
      try {
      await ensureMounted(["accel", "nlp"], "intakeLogs");

      const basics: BasicInfo[] = [];
      const summaries: SummaryRow[] = [];
      const finances: FinRow[] = [];

      for (let fi = 0; fi < snapshot.length; fi++) {
        const file = get().files[fi];
        if (!file) continue;
        set((s) => ({
          intakeProgress: Math.round(((fi + 0.05) / snapshot.length) * 100),
          intakeLogs: pushLog(s.intakeLogs, "INFO", "FILE", `處理 ${file.name}`),
        }));

        let aborted = false;
        let skipRest = false;
        for (const step of PIPELINE_STEPS) {
          await sleep(snapshot.length > 16 ? 6 : 55);
          const d = decideStep(file, step.id, skipRest);
          skipRest = d.skipRest;
          aborted = d.aborted;
          set((s) => ({
            files: s.files.map((f) => {
              if (f.id !== file.id) return f;
              const steps = { ...f.steps, [step.id]: d.light };
              return {
                ...f,
                steps,
                status: statusFromSteps(steps, aborted, skipRest, !aborted && !skipRest),
                stuckStep: d.stuck ?? f.stuckStep,
                stuckDetail: d.detail ?? f.stuckDetail,
              };
            }),
            intakeLogs: pushLog(
              s.intakeLogs,
              d.light === "bad" ? "FAIL" : d.light === "warn" ? "WARN" : skipRest ? "INFO" : "OK",
              step.id,
              d.detail ?? `${file.name} · ${step.title}`,
            ),
          }));
          if (aborted || skipRest) break;
        }

        const current = get().files.find((f) => f.id === file.id);
        if (!current) continue;
        if (current.status === "bad" || (current.skipDup && current.dupOf)) {
          if (current.skipDup && current.dupOf) {
            set((s) => ({
              files: s.files.map((f) => (f.id === file.id ? { ...f, status: "warn" } : f)),
            }));
          }
          continue;
        }

        const parsed = parseFilename(file.name);
        const light: Light = current.status === "warn" ? "warn" : "ok";
        basics.push(packBasic({ ...file, status: light }, parsed, light));
        if (parsed.ticker || file.ext === "xlsx" || file.ext === "csv") {
          summaries.push(...packSummary(file, parsed));
          finances.push(...packFinance(file, parsed, light));
        }

        set((s) => ({
          files: s.files.map((f) => (f.id === file.id ? { ...f, status: light } : f)),
          basics: [...basics],
          summaries: [...summaries],
          finances: [...finances],
        }));
      }

      const failN = get().files.filter((f) => f.status === "bad").length;
      const pack = runRepairPack({ files: get().files, engines: get().engines, finances });
      set((s) => ({
        intakeBusy: false,
        intakeProgress: 100,
        intakeTab: basics.length ? "tab2" : "tab1",
        activated: { ...s.activated, vrn: true },
        finances: pack.finances,
        repairTools: pack.tools,
        intakeLogs: pushLog(
          s.intakeLogs,
          failN ? "WARN" : "OK",
          "DONE",
          `驗證結束 · 失敗 ${failN} 在 TAB 1 · 通過 ${basics.length} → TAB 2 · 摘要 ${summaries.length} → TAB 3 · 財務 ${pack.finances.length} → TAB 4 · ${pack.note}`,
        ),
        busLogs: pushLog(s.busLogs, failN ? "WARN" : "OK", "VRN", `TAB2 ${basics.length} · TAB4 ${pack.finances.length} · ${pack.note}`),
        vrnSeal: sealVrn(get().files, basics, summaries, pack.finances),
      }));
      refreshAuto();
      } finally {
        if (get().intakeBusy) set({ intakeBusy: false });
      }
    },

    vrnSeal: BOOT.vrn.seal,
    vrnEndSteps: BOOT.vrn.ended.steps,
    viaEndSteps: [],
    liveSeal: null,
    goLiveRows: [],
    procRows: BOOT.proc,
    runSeal: async () => {
      await get().runVdf();
      await get().runIntake();
      await get().runAudit();
      get().runAutoTest();
      const s = get();
      const procRows = runProcessPack({
        confirmNet: s.confirmNet,
        fredMode: s.fetchMetrics ? (s.fredRows[0]?.source === "FRED_LIVE" ? "LIVE" : s.fredRows[0]?.source === "DENIED" ? "DENIED" : "CACHE") : null,
        vdfRows: s.fredRows.length,
        parquetOk: Boolean(s.fetchMetrics?.parquetRoundtrip),
        vrnPass: s.files.filter((f) => f.status === "ok").length,
        vrnFail: s.files.filter((f) => f.status === "bad").length,
        files: s.files,
        finances: s.finances,
      });
      const vrnEnded = runVrnToEnd({
        files: s.files,
        basics: s.basics,
        summaries: s.summaries,
        finances: s.finances,
        confirmNlp: s.confirmNlp,
      });
      const viaEnded = runViaToEnd({
        engines: s.engines,
        confirmNet: s.confirmNet,
        confirmNlp: s.confirmNlp,
      });
      const testsPass =
        vrnEnded.fail === 0 &&
        viaEnded.fail === 0 &&
        s.autoRows.length > 0 &&
        s.autoRows.every((r) => r.light !== "bad");
      const done = completeVrn({ confirmNlp: s.confirmNlp, testsPass });
      const vrnSeal = testsPass && done.fail === 0 ? done.seal : s.vrnSeal ?? done.seal;
      const dct: Seal = { id: "DCT", name: "DCT01–20", light: "ok", note: "不動 · 已 FIXED · 本輪不重做" };
      const cgc = sealConsole(s.engines.length);
      const e075 = sealEng075(s.revRows.length, revContract().latest);
      const glss = sealGlss(s.gffRows.length);
      const e077 = sealEng077(s.cnsLong.length, new Set(s.cnsLong.map((r) => r.code)).size);
      const rows = [s.vdfSeal, vrnSeal, sealParquet(s.fetchMetrics), cgc, e075, glss, e077, sealLocalDb(3), sealVap(), runGovEnv({ apply: false }).seal, viaEnded.seal, dct, megaSeal()].filter((x): x is Seal => Boolean(x));
      const live = sealGoLive(rows.filter((r) => r.id === "VDF" || r.id === "VRN" || r.id === "PARQ" || r.id === "CGC" || r.id === "VIA"));
      const failN = procRows.filter((p) => p.result === "FAIL").length;
      set({
        procRows,
        vrnSeal,
        vrnEndSteps: vrnEnded.steps,
        viaEndSteps: viaEnded.steps,
        goLiveRows: [...rows, live],
        liveSeal: live,
      });
      bus(failN ? "WARN" : live.light === "ok" ? "OK" : "WARN", "SEAL", `${live.note} · 程序 ${procRows.length} · 失敗 ${failN}`);
    },

    engines: applySsot(REGISTERED_ENGINES),
    engineLogs: [],
    engineBusy: false,
    confirmNet: false,
    confirmNlp: false,
    roundConsent: true,
    setConfirmNet: (v) => {
      set({ confirmNet: v });
      if (v) void ensureMounted(["net"], "engineLogs");
      refreshAuto();
    },
    setConfirmNlp: (v) => {
      set({ confirmNlp: v });
      if (v) void ensureMounted(["nlp"], "engineLogs");
      refreshAuto();
    },
    setRoundConsent: (v) => {
      set({ roundConsent: v });
      refreshAuto();
    },
    pendingMounts: [],
    setPendingMounts: (p) => set({ pendingMounts: p }),
    mountEngines: async () => {
      const { pendingMounts, confirmNet, confirmNlp, engines, engineBusy } = get();
      if (!pendingMounts.length || engineBusy) return;
      set({ engineBusy: true });
      await ensureMounted(["accel"], "engineLogs");
      if (confirmNet) await ensureMounted(["net"], "engineLogs");
      if (confirmNlp) await ensureMounted(["nlp"], "engineLogs");

      const recs: EngineRec[] = [];
      for (const draft of pendingMounts) {
        const rec: EngineRec = {
          id: uid("ENG").toUpperCase(),
          name: draft.name.replace(/\.[^.]+$/, ""),
          kind: draft.kind,
          path: draft.path,
          hash: Math.random().toString(16).slice(2, 8),
          accel: true,
          net: confirmNet,
          nlp: confirmNlp,
          ssot: true,
          status: draft.kind === "NET" && !confirmNet ? "warn" : "ok",
          note: [
            "ACCEL 自動掛載",
            confirmNet ? "NET 已確認" : "NET 未確認 · 零外呼",
            confirmNlp ? "NLP 已確認" : "NLP 未掛",
            "SSOT append-only",
          ].join(" · "),
        };
        if (engines.some((e) => e.name === rec.name && e.path === rec.path) || recs.some((e) => e.name === rec.name && e.path === rec.path)) {
          rec.status = "warn";
          rec.note = "hash 去重 · 同名已在冊 · 本次標為鏡像";
        }
        recs.push(rec);
      }

      set((s) => ({
        engines: [...recs, ...s.engines],
        engineBusy: false,
        pendingMounts: [],
        activated: { ...s.activated, engine: true },
        engineLogs: recs.reduce(
          (logs, rec) => pushLog(logs, rec.status === "warn" ? "WARN" : "OK", "SSOT", `${rec.id} 登錄 ${rec.note}`),
          s.engineLogs,
        ),
        busLogs: pushLog(s.busLogs, "OK", "ENG", `SSOT +${recs.length}`),
      }));
      if (get().autoAudit) void get().runAudit();
      else refreshAuto();
    },

    autoAudit: true,
    setAutoAudit: (v) => set({ autoAudit: v }),
    auditBusy: false,
    auditProgress: 0,
    auditTab: "tab1",
    setAuditTab: (t) => set({ auditTab: t }),
    auditLogs: [],
    auditRows: [],
    auditDetails: [],
    repairTools: [],
    runAudit: async () => {
      if (get().auditBusy) return;
      const engines = get().engines;
      set({
        auditBusy: true,
        auditProgress: 4,
        auditTab: "tab1",
        auditRows: [],
        auditDetails: [],
        auditLogs: pushLog([], "INFO", "AUDIT", `自動鑑測 ${engines.length} 具引擎`),
      });
      await ensureMounted(["accel"], "auditLogs");

      const { confirmNet, confirmNlp } = get();
      const rows: AuditRow[] = [];
      const details: AuditDetail[] = [];

      for (let i = 0; i < engines.length; i++) {
        const eng = get().engines.find((e) => e.id === engines[i].id) ?? engines[i];
        const result = auditEngine(eng, { confirmNet, confirmNlp });
        const level: LogLine["level"] =
          result.repair === "UNREPAIRABLE" ? "FAIL" : result.repair === "REPAIRED" ? "WARN" : "OK";
        const detail = result.findings.join(" · ");
        rows.push({
          engineId: result.engineId,
          engineName: result.engineName,
          kind: result.kind,
          steps: result.steps,
          repair: result.repair,
          findings: result.findings,
          status: result.status,
          note: result.note,
        });
        details.push({
          id: uid("det"),
          t: nowStamp(),
          engineId: result.engineId,
          engineName: result.engineName,
          step: "A10",
          finding: detail,
          repair: result.repair as RepairKind,
          status: result.status,
        });
        set((s) => ({
          auditProgress: Math.round(((i + 1) / engines.length) * 100),
          auditRows: [...rows],
          auditDetails: [...details],
          engines: s.engines.map((e) => (e.id === eng.id ? applyAuditPatch(e, result) : e)),
          auditLogs: pushLog(s.auditLogs, level, result.engineId, `${result.repair} · ${result.engineName}`, detail),
          busLogs: pushLog(s.busLogs, level, "VAR", `${result.engineId} ${result.repair}`),
        }));
        await sleep(engines.length > 20 ? 6 : 28);
      }

      const unrepaired = rows.filter((r) => r.repair === "UNREPAIRABLE").length;
      const fixed = rows.filter((r) => r.repair === "REPAIRED").length;
      const pack = runRepairPack({ files: get().files, engines: get().engines, finances: get().finances });
      set((s) => ({
        auditBusy: false,
        auditProgress: 100,
        activated: { ...s.activated, var: true },
        engines: pack.engines,
        finances: pack.finances.length ? pack.finances : s.finances,
        repairTools: pack.tools,
        auditLogs: pushLog(
          s.auditLogs,
          unrepaired ? "WARN" : "OK",
          "DONE",
          `鑑測結束 · 修復 ${fixed} · 無法 ${unrepaired} · ${pack.note} · DETAILS 保留`,
        ),
      }));
      refreshAuto();
    },
    downToken: "",
    downCommit: false,
    downRows: dispatchDryRun(),
    setDownToken: (v) => set({ downToken: v, downRows: dispatchDryRun({ token: v, commit: get().downCommit }) }),
    setDownCommit: (v) => set({ downCommit: v, downRows: dispatchDryRun({ token: get().downToken, commit: v }) }),
    mintDownToken: () => {
      const token = mintToken();
      set({ downToken: token, downRows: dispatchDryRun({ token, commit: get().downCommit }) });
    },
    runDownward: () => {
      const token = get().downToken;
      const commit = get().downCommit;
      const rows = dispatchDryRun({ token, commit });
      set((s) => ({
        downRows: rows,
        auditLogs: pushLog(
          s.auditLogs,
          rows.some((r) => r.state === "APPLY") ? "OK" : "WARN",
          "DOWN",
          rows.some((r) => r.state === "APPLY")
            ? "權杖通過 · APPLY DryRun · 本台不 spawn"
            : "未核准 · APPLY SKIPPED · 唯讀契約",
        ),
      }));
    },
    autoRows: [],
    handoverRows: [],
    handoverDay: nextDayIso(),
    runAutoTest: () => {
      refreshAuto();
      bus("OK", "AUTO", `全日曆測 ${get().autoRows.length} 列 · 隔日 ${get().handoverDay}`);
    },
    bootDone: false,
    pathScript: "",
    vdfNextRound: false,
    bootGovern: () => {
      if (get().bootDone) return;
      const iso = scanEnvConflicts();
      const gov = runGovEnv({ apply: false });
      const gap = inspectGap(get().lakeCkpt, { start: LAKE_START_YEAR, live: get().confirmNet });
      set({
        bootDone: true,
        startYear: LAKE_START_YEAR,
        gapReport: gap,
        vdfNextRound: nextRoundNeeded(gap),
        isoSteps: isolationSteps(iso),
        isoScript: isolationScript(iso),
        pathScript: motherPathScript(),
        engines: applySsot(get().engines),
      });
      refreshAuto();
      bus("OK", "BOOT", `LKGC PATH · 起始年 ${LAKE_START_YEAR} · ${gov.seal.note}`);
      bus(iso.length ? "WARN" : "OK", "ENV", iso.length ? `隔離 ${iso.map((c) => c.isolate).join(", ")} · 不刪` : "無衝突");
      const em = runEnvManager({ consent: false });
      bus(em.light === "ok" ? "OK" : "WARN", "ENV", em.note);
      const entry = runCentralEntry({ consent: false });
      bus("OK", "ENTRY", entry.note);
      bus("WARN", "ISO", "本台不 spawn conda · 指令在隔離表／PATH");
      bus("INFO", "BOOT", "先 VDF CACHE 再 VRN 實測 · LIVE 關 · 不 spawn");
      if (get().activated.vdf && get().activated.vrn) {
        get().runAutoTest();
        if (get().roundConsent) void get().runVdfNextRound();
        return;
      }
      void get()
        .runSeal()
        .then(() => {
          if (get().roundConsent) return get().runVdfNextRound();
        });
    },
    runVdfNextRound: async () => {
      if (get().vdfBusy) return;
      if (!get().vdfNextRound) {
        bus("OK", "VDF", "無增量缺口 · 不必下一輪");
        return;
      }
      const gate = dualGateNext({
        confirmNet: get().confirmNet,
        roundConsent: get().roundConsent,
        apiKey: get().fredKey,
      });
      if (!gate.gate2Round) {
        bus("WARN", "VDF", "閘2 未同意 · 不補年檔");
        return;
      }
      if (gate.live) {
        bus("INFO", "VDF", gate.note);
        await get().runVdf();
        return;
      }
      const gap = inspectGap(get().lakeCkpt, { start: get().startYear, live: false });
      set((s) => ({
        gapReport: gap,
        vdfNote: `${gate.note} · ${gap.note}`,
        vdfLogs: pushLog(s.vdfLogs, "WARN", "GAP", `${gate.note} · ${gap.note}`),
        busLogs: pushLog(s.busLogs, "WARN", "VDF", `下一輪 CACHE · ${gap.note}`),
      }));
    },
    isoSteps: isolationSteps(),
    isoScript: isolationScript(),
    mintIsolation: () => {
      const hits = scanEnvConflicts();
      const steps = isolationSteps(hits);
      const script = isolationScript(hits);
      set({ isoSteps: steps, isoScript: script });
      bus("WARN", "ISO", `本台不 spawn conda · ${hits.map((c) => c.isolate).join(", ") || "無衝突"} · 指令已寫入隔離表`);
    },
    runEnvManagerPlan: (consent = false) => {
      const em = runEnvManager({ consent });
      bus(em.light === "ok" ? "OK" : "WARN", "ENV", em.note);
      em.log.forEach((line) => bus("INFO", "ENV", line));
    },
  };
});

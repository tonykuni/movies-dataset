/** Compact ports of 新增資料夾 mother tools. v0110 wins over v0100. C: path is SSOT label only. */
import { isUnknownStub } from "./inventory.ts";
import { auditFinancialRows } from "./fin-audit.ts";
import type { EngineRec, FinRow, IntakeFile, Light } from "./types.ts";

export const MOTHER_FOLDER =
  "C:\\Users\\tonyk\\OneDrive\\Documents\\新增資料夾";

export type RepairToolRow = {
  id: string;
  file: string;
  pick: string;
  light: Light;
  note: string;
};

export const REPAIR_TOOLS: RepairToolRow[] = [
  { id: "CGC", file: "VIA_CentralGovernanceEngine.py", pick: "engine", light: "ok", note: "向下總控 · 非第二 UI" },
  { id: "CONS", file: "VIA_CentralGovernanceConsole.py", pick: "this-console", light: "ok", note: "本台即 Console · 唯一 HTML" },
  { id: "DOWN", file: "VIA_DownwardController.py", pick: "v0111 DAG", light: "ok", note: "DCT01–20 · 權杖綁雜湊 · 分系封印" },
  { id: "PRIO", file: "VIA_FilePriorityRouter.py", pick: "incoming", light: "ok", note: "VRN I/O 優先序" },
  { id: "LAUNCH", file: "VIA_Launch_NonBlocking_v0100.ps1", pick: "v0100", light: "ok", note: "非阻塞啟動" },
  { id: "R1", file: "VIA_Round1_CodeRepair_v0100.ps1", pick: "v0100", light: "ok", note: "只增不減修補" },
  { id: "SAME", file: "VIA_SameNameConsolidator_v0110.ps1", pick: "v0110>v0100", light: "ok", note: "同名只留權威版；v0100 契約列" },
  { id: "TOOL", file: "VIA_ToolchainInstaller_v0100.ps1", pick: "v0100", light: "ok", note: "node/tsc/playwright 在位" },
  { id: "VER", file: "VIA_VersionGuard_v0110.ps1", pick: "v0110", light: "ok", note: "禁止舊檔蓋新檔" },
  { id: "AUTH", file: "VIA_AuthorityAudit.py", pick: "CGC", light: "ok", note: "本台總管=唯一 UI SSOT" },
  { id: "FINAUD", file: "VIA_VRN_FinancialRowAuditor.py", pick: "row-id", light: "ok", note: "財務列：有限值／單位／去重" },
  { id: "PROF", file: "VIA_Profile_Doctor_v0100.ps1", pick: "v0100", light: "ok", note: "via_core／via_* 契約層" },
  { id: "POLY", file: "VIA_Polyglot_Repair_Injector_v0100.ps1", pick: "v0100", light: "ok", note: "ACCEL-BRIDGE 只增不減" },
  { id: "TACC", file: "VIA_TestAccelerator.py", pick: "PS20", light: "ok", note: "搭配 DAG 已測" },
  { id: "ENV", file: "VIA_EnvDeepProbe.py", pick: "probe", light: "ok", note: "母根／資料根／env 協調" },
  { id: "HARD", file: "VIA_EngineHardening.py", pick: "harden", light: "ok", note: "全日曆測燈" },
  { id: "REC", file: "VIA_Recover_v0110.ps1", pick: "v0110", light: "ok", note: "UNREPAIRABLE 不刪，只隔離" },
];

export function versionGuard(a: string, b: string): string {
  const na = Number((a.match(/v0?(\d+)/i) ?? [])[1] ?? 0);
  const nb = Number((b.match(/v0?(\d+)/i) ?? [])[1] ?? 0);
  return na >= nb ? a : b;
}

export function consolidateSameName(files: IntakeFile[]): IntakeFile[] {
  const seen = new Map<string, IntakeFile>();
  const out: IntakeFile[] = [];
  for (const f of files) {
    const key = f.name.toLowerCase();
    const prev = seen.get(key);
    if (!prev) {
      seen.set(key, f);
      out.push(f);
      continue;
    }
    if (f.size > prev.size || f.lastModified > prev.lastModified) {
      out[out.indexOf(prev)] = { ...prev, skipDup: true, dupOf: f.name, status: "warn" };
      seen.set(key, f);
      out.push(f);
    } else {
      out.push({ ...f, skipDup: true, dupOf: prev.name, status: f.status === "bad" ? "bad" : "warn" });
    }
  }
  return out;
}

export function auditFinRows(rows: FinRow[]) {
  const a = auditFinancialRows(rows);
  return { rows: a.rows, dropped: a.dropped, dups: a.dups, verdict: a.verdict, gates: a.gates };
}

export function authorityOf(engines: EngineRec[]): { id: string; note: string } {
  const cgc = engines.find((e) => /CGC|GOV|EnvManager/i.test(e.id) || e.kind === "GOV");
  return { id: cgc?.id ?? "VIS-ENV-000001", note: "UI 權威= Central Govern；湖權威=母機 Python" };
}

export function hardenEngines(engines: EngineRec[]): EngineRec[] {
  return engines.filter((e) => !isUnknownStub(e)).map((e) => {
    if (!e.path.trim() || /orphan/i.test(e.id)) {
      return {
        ...e,
        status: "warn",
        note: /UNREPAIRABLE|DETAILS 保留/.test(e.note) ? e.note : `UNREPAIRABLE · DETAILS 保留 · 不自動修 · ${e.note || "路徑空白"}`,
      };
    }
    if (!e.hash) return { ...e, hash: e.id.replace(/[^a-f0-9]/gi, "a").slice(0, 6).padEnd(6, "a"), ssot: true };
    return e;
  });
}

export function runRepairPack(input: { files: IntakeFile[]; engines: EngineRec[]; finances: FinRow[] }): {
  tools: RepairToolRow[];
  files: IntakeFile[];
  engines: EngineRec[];
  finances: FinRow[];
  note: string;
} {
  const files = consolidateSameName(input.files);
  const engines = hardenEngines(input.engines);
  const fin = auditFinRows(input.finances);
  const auth = authorityOf(engines);
  const tools = REPAIR_TOOLS.map((t) =>
    t.id === "AUTH" ? { ...t, note: `${t.note} · ${auth.id}` } : t.id === "FINAUD" ? { ...t, note: `${t.note} · ${fin.verdict} 留 ${fin.rows.length} 去重 ${fin.dups} 丟 ${fin.dropped}` } : t,
  );
  return {
    tools,
    files,
    engines,
    finances: fin.rows,
    note: `v0110 同名／財務列／權威 ${auth.id}`,
  };
}

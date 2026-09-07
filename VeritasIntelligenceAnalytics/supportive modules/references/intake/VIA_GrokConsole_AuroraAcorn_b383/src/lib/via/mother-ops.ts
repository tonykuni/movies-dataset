/** Compact ports: launcher A01–A20 detect-only, downward DAG, L1 priority. */
import type { Light } from "./types.ts";

export type AccelState = "READY" | "BUILTIN" | "ABSENT";
export type LaunchAccel = { id: string; name: string; state: AccelState; kind: string; detail: string };

export const LAUNCH_ACCELS: LaunchAccel[] = [
  { id: "A01", name: "Python 執行期", state: "ABSENT", kind: "RUNTIME", detail: "本台 HTML 無 python；母機才 READY" },
  { id: "A02", name: "PowerShell 7", state: "ABSENT", kind: "RUNTIME", detail: "本台無 pwsh" },
  { id: "A03", name: "uv", state: "ABSENT", kind: "EXTERNAL", detail: "不安裝、不假裝" },
  { id: "A04", name: "ruff", state: "ABSENT", kind: "EXTERNAL", detail: "ABSENT" },
  { id: "A05", name: "PSScriptAnalyzer", state: "ABSENT", kind: "EXTERNAL", detail: "ABSENT" },
  { id: "A06", name: "polars", state: "ABSENT", kind: "PYLIB", detail: "湖在母機" },
  { id: "A07", name: "pyarrow", state: "ABSENT", kind: "PYLIB", detail: "湖在母機" },
  { id: "A08", name: "duckdb", state: "ABSENT", kind: "PYLIB", detail: "湖在母機" },
  { id: "A09", name: "pydantic", state: "ABSENT", kind: "PYLIB", detail: "ABSENT" },
  { id: "A10", name: "rapidfuzz", state: "ABSENT", kind: "PYLIB", detail: "ABSENT" },
  { id: "A11", name: "psutil", state: "ABSENT", kind: "PYLIB", detail: "ABSENT" },
  { id: "A12", name: "AST 精準解析", state: "BUILTIN", kind: "INTERNAL", detail: "Round1 / Console" },
  { id: "A13", name: "依賴拓撲排序", state: "BUILTIN", kind: "INTERNAL", detail: "DownwardController" },
  { id: "A14", name: "九頭龍爆炸半徑", state: "BUILTIN", kind: "INTERNAL", detail: "TopologyGuard" },
  { id: "A15", name: "PEP 508 標記", state: "BUILTIN", kind: "INTERNAL", detail: "EnvManager" },
  { id: "A16", name: "介面契約 G15", state: "BUILTIN", kind: "INTERNAL", detail: "ContractGovernor" },
  { id: "A17", name: "指紋回滾", state: "BUILTIN", kind: "INTERNAL", detail: "Round1 指紋" },
  { id: "A18", name: "檔案優先序", state: "BUILTIN", kind: "INTERNAL", detail: "FilePriorityRouter" },
  { id: "A19", name: "非阻塞進度", state: "BUILTIN", kind: "INTERNAL", detail: "Launch_NonBlocking" },
  { id: "A20", name: "Visual Lock 矩陣", state: "BUILTIN", kind: "INTERNAL", detail: "本台 HTML" },
];

export function accelLight(state: AccelState): Light {
  if (state === "ABSENT") return "warn";
  return "ok";
}

export type Capability = {
  urn: string;
  name: string;
  kind: string;
  mutating: boolean;
  dependsOn: string[];
  script: string;
};

export const CAPABILITIES: Capability[] = [
  { urn: "VIA-SYS-ENG-001", name: "環境治理", kind: "ENV", mutating: false, dependsOn: [], script: "VIA_EnvManager_UnifiedGovernance_v0110.ps1" },
  { urn: "VIA-SYS-ENG-003", name: "檔案優先序", kind: "ANALYSIS", mutating: false, dependsOn: [], script: "VIA_FilePriorityRouter.py" },
  { urn: "VIA-SUP-LIB-001", name: "Supportive 分類", kind: "ANALYSIS", mutating: false, dependsOn: [], script: "VIA_SupportiveModules_Classifier_v0100.ps1" },
  { urn: "VIA-SYS-LIB-001", name: "Profile 醫生", kind: "HYGIENE", mutating: false, dependsOn: [], script: "VIA_Profile_Doctor_v0100.ps1" },
  { urn: "VIA-SYS-ENG-002", name: "Round1 修復 DryRun", kind: "REPAIR", mutating: false, dependsOn: ["VIA-SYS-ENG-001", "VIA-SYS-ENG-003"], script: "VIA_Round1_CodeRepair_v0100.ps1" },
  { urn: "VIA-SYS-ENG-002-APPLY", name: "Round1 套用", kind: "REPAIR", mutating: true, dependsOn: ["VIA-SYS-ENG-002"], script: "VIA_Round1_CodeRepair_v0100.ps1" },
  { urn: "VIA-SUP-ENG-001", name: "Polyglot 注入 DryRun", kind: "REPAIR", mutating: false, dependsOn: ["VIA-SYS-ENG-002"], script: "VIA_Polyglot_Repair_Injector_v0100.ps1" },
  { urn: "VIA-SYS-MGR-001", name: "中央治理複驗", kind: "ANALYSIS", mutating: false, dependsOn: ["VIA-SYS-ENG-001", "VIA-SYS-ENG-002", "VIA-SUP-ENG-001"], script: "VIA_CentralGovernanceConsole.py" },
];

export function topoLevels(
  caps = CAPABILITIES,
  opts: { authorized?: boolean } = {},
): { level: number; urn: string; name: string; state: string; note: string }[] {
  const by = new Map(caps.map((c) => [c.urn, c]));
  const indeg = new Map(caps.map((c) => [c.urn, 0]));
  const unresolved: string[] = [];
  for (const c of caps) {
    for (const p of c.dependsOn) {
      if (p === c.urn) continue;
      if (!by.has(p)) {
        unresolved.push(`${c.urn}→${p}`);
        continue;
      }
      indeg.set(c.urn, (indeg.get(c.urn) ?? 0) + 1);
    }
  }
  const out: { level: number; urn: string; name: string; state: string; note: string }[] = [];
  let ready = caps.filter((c) => (indeg.get(c.urn) ?? 0) === 0 && !c.dependsOn.includes(c.urn)).map((c) => c.urn);
  const seen = new Set<string>();
  let level = 0;
  const auth = Boolean(opts.authorized);
  while (ready.length) {
    for (const u of ready) {
      const c = by.get(u)!
      seen.add(u);
      const hanging = c.dependsOn.filter((p) => p !== c.urn && !by.has(p));
      out.push({
        level,
        urn: u,
        name: c.name,
        state: hanging.length ? "BLOCKED" : c.mutating ? (auth ? "APPLY" : "SKIPPED") : "ANALYSIS",
        note: hanging.length
          ? `UNRESOLVED_DEPENDENCY ${hanging.join(", ")}`
          : c.mutating
            ? auth
              ? "權杖＋commit 通過 · 本台仍不 spawn"
              : "變更類需 ==VEM-APPROVE== 權杖 + commit"
            : "唯讀可自動",
      });
    }
    const nxt: string[] = [];
    for (const u of ready) {
      for (const c of caps) {
        if (!c.dependsOn.includes(u)) continue;
        indeg.set(c.urn, (indeg.get(c.urn) ?? 1) - 1);
        if ((indeg.get(c.urn) ?? 1) === 0 && !seen.has(c.urn)) nxt.push(c.urn);
      }
    }
    ready = nxt;
    level += 1;
  }
  void unresolved;
  return out;
}

export function filePriority(name: string, ext: string, size: number): { priority: string; reason: string } {
  const n = name.toLowerCase();
  if (/\.env|credential|\.pem$|\.key$|^id_rsa|secret/.test(n) || ["pem", "key", "pfx"].includes(ext)) return { priority: "SKIP", reason: "SECRET 只登記不讀" };
  if (/snapshot|preview\.json|_matrix_|governance_snapshot/.test(n)) return { priority: "SKIP", reason: "DERIVED 防回饋迴路" };
  if (/governance|registry|ssot|ledger|contract/.test(n)) return { priority: "P0-GOVERNANCE", reason: "契約／台帳先讀" };
  if (size === 0) return { priority: "SKIP", reason: "空檔" };
  if (["py", "ps1", "ts", "tsx"].includes(ext)) return { priority: "P1-CODE", reason: "VIA 第一級語料" };
  if (["pdf", "md", "txt", "docx"].includes(ext)) return { priority: "P2-DOC", reason: "文件" };
  if (["csv", "xlsx", "json", "parquet"].includes(ext)) return { priority: "P3-DATA", reason: "表" };
  if (["html", "xml"].includes(ext)) return { priority: "P4-SEMI", reason: "半結構" };
  if (["log", "tmp", "bak"].includes(ext)) return { priority: "P5-NOISE", reason: "噪音／碎屑" };
  return { priority: "P5-NOISE", reason: "未知副檔名先登記" };
}

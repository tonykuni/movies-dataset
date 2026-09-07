/** Downward D01–D08, DCT01–DCT20, AST four-layer + Name ctx. Browser is contract-only. */
import { CAPABILITIES, topoLevels, type Capability } from "./mother-ops.ts";
import type { Light } from "./types.ts";

export const TOKEN_RE = /^==[A-Z-]+APPROVE==\d{8}_\d{6}-[0-9a-f]{6,}$/;

/** FNV-1a 32-bit；URN 皆 ASCII，與母機 v0110 plan_digest 一致。 */
export function fnv1aHex(text: string, n = 6): string {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16).padStart(8, "0").slice(0, n);
}

export function planDigest(caps: Capability[] = CAPABILITIES): string {
  return fnv1aHex(caps.map((c) => `${c.urn}:${c.script}`).sort().join("|"));
}

export function registryHmac(caps: Capability[] = CAPABILITIES, key = "VIA-SYS-MGR-003"): string {
  const payload = caps.map((c) => `${c.urn}|${c.script}|${c.mutating ? 1 : 0}`).sort().join("\n");
  return fnv1aHex(`${key}\n${payload}`, 8);
}

export function stampToken(now = new Date()): string {
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");
  return `${y}${m}${d}_${hh}${mm}${ss}`;
}

export function mintToken(now = new Date(), caps: Capability[] = CAPABILITIES): string {
  return `==VEM-APPROVE==${stampToken(now)}-${planDigest(caps)}`;
}

export function authorized(token: string, commit: boolean, caps: Capability[] = CAPABILITIES): boolean {
  if (!commit || !token || !TOKEN_RE.test(token)) return false;
  const hex = token.split("-").pop() ?? "";
  return hex.startsWith(planDigest(caps));
}

export function blocksDownstream(state: string, verdict: string, strict = false): boolean {
  const hard = state === "FAILED" || state === "TIMEOUT" || state === "MISSING";
  const soft = verdict === "RED" || verdict === "CRASHED" || verdict === "TIMEOUT";
  return hard || (strict && soft);
}

export type TopoReport = {
  levels: ReturnType<typeof topoLevels>;
  selfLoops: string[];
  unresolved: string[];
  cycles: string[];
};

export function analyzeTopo(caps: Capability[] = CAPABILITIES): TopoReport {
  const by = new Set(caps.map((c) => c.urn));
  const selfLoops: string[] = [];
  const unresolved: string[] = [];
  for (const c of caps) {
    for (const p of c.dependsOn) {
      if (p === c.urn) selfLoops.push(c.urn);
      else if (!by.has(p)) unresolved.push(`${c.urn}→${p}`);
    }
  }
  const levels = topoLevels(caps);
  const seen = new Set(levels.map((r) => r.urn));
  const cycles = caps.filter((c) => !seen.has(c.urn)).map((c) => c.urn);
  return { levels, selfLoops, unresolved, cycles: [...new Set([...cycles, ...selfLoops])] };
}

export type GateRow = { code: string; title: string; status: "PASS" | "WARN" | "FAIL"; detail: string; light: Light };

export function downwardGates(opts: { token?: string; commit?: boolean } = {}): GateRow[] {
  const topo = analyzeTopo();
  const auth = authorized(opts.token ?? "", Boolean(opts.commit));
  const apply = topoLevels(CAPABILITIES, { authorized: auth }).find((r) => r.urn.includes("APPLY"));
  const d01: GateRow = {
    code: "D01",
    title: "CAPABILITY_PRESENT",
    status: "PASS",
    detail: `${CAPABILITIES.length} 支出廠能力 · 本台契約在冊`,
    light: "ok",
  };
  const d02: GateRow = {
    code: "D02",
    title: "NO_CAPABILITY_CYCLE",
    status: topo.cycles.length || topo.unresolved.length ? "FAIL" : "PASS",
    detail: topo.cycles.length || topo.unresolved.length
      ? `循環 ${topo.cycles.join(", ") || "—"} · 未知上游 ${topo.unresolved.join(", ") || "—"}`
      : "無環 · 未知上游不靜默（DCT08）",
    light: topo.cycles.length || topo.unresolved.length ? "bad" : "ok",
  };
  const d03: GateRow = {
    code: "D03",
    title: "NO_UNAUTHORIZED_MUTATION",
    status: "PASS",
    detail: auth
      ? "權杖＋commit 齊 · 變更類可下行"
      : `${apply?.state ?? "SKIPPED"} · 無權杖變更類不下發`,
    light: "ok",
  };
  const d04: GateRow = {
    code: "D04",
    title: "NO_TIMEOUT",
    status: "PASS",
    detail: "本台不 spawn 子行程",
    light: "ok",
  };
  const d05: GateRow = {
    code: "D05",
    title: "FAILURE_ISOLATED",
    status: "PASS",
    detail: "硬故障才 BLOCKED · 軟 RED 不連坐",
    light: "ok",
  };
  const d06: GateRow = {
    code: "D06",
    title: "EVIDENCE_COLLECTED",
    status: "WARN",
    detail: "本台無 Python 快照 · 不假裝 GREEN",
    light: "warn",
  };
  const d07: GateRow = {
    code: "D07",
    title: "APPEND_ONLY_REGISTRY",
    status: "PASS",
    detail: "停用 enabled=false · 不刪 URN",
    light: "ok",
  };
  const worst = [d01, d02, d03, d04, d05, d06, d07].some((g) => g.status === "FAIL")
    ? "FAIL"
    : [d01, d02, d03, d04, d05, d06, d07].some((g) => g.status === "WARN")
      ? "WARN"
      : "PASS";
  const d08: GateRow = {
    code: "D08",
    title: "AGGREGATE_VERDICT",
    status: worst,
    detail: worst === "PASS" ? "GREEN" : worst === "WARN" ? "AMBER · D06 本台無快照" : "RED",
    light: worst === "FAIL" ? "bad" : worst === "WARN" ? "warn" : "ok",
  };
  return [d01, d02, d03, d04, d05, d06, d07, d08];
}

export type DctRow = {
  code: string;
  title: string;
  sev: "FAIL" | "WARN";
  status: "FIXED" | "PARTIAL" | "OPEN";
  light: Light;
  lib: string;
  note: string;
};

export const DCT_CATALOG: DctRow[] = [
  { code: "DCT01", title: "字串拼接命令列", sev: "FAIL", status: "FIXED", light: "ok", lib: "shlex", note: "argv list · 無 shell=True" },
  { code: "DCT02", title: "逾時不殺孫行程", sev: "FAIL", status: "FIXED", light: "ok", lib: "atexit", note: "進程樹 taskkill/killpg + atexit" },
  { code: "DCT03", title: "逾時不留證據", sev: "WARN", status: "FIXED", light: "ok", lib: "signal", note: "先落地 .out/.err 再殺" },
  { code: "DCT04", title: "並行互蓋工作區", sev: "FAIL", status: "FIXED", light: "ok", lib: "tempfile", note: "每 URN mkdtemp under work/runs" },
  { code: "DCT05", title: "看門狗同緒", sev: "FAIL", status: "FIXED", light: "ok", lib: "threading", note: "daemon 緒 timeout+2s 殺樹" },
  { code: "DCT06", title: "future 例外被吞", sev: "FAIL", status: "FIXED", light: "ok", lib: "", note: "as_completed + result()" },
  { code: "DCT07", title: "自環無提示", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "self-loop → cycles／D02 FAIL" },
  { code: "DCT08", title: "未知上游靜默丟", sev: "FAIL", status: "FIXED", light: "ok", lib: "difflib", note: "UNRESOLVED_DEPENDENCY 阻斷該支" },
  { code: "DCT09", title: "登記檔可改腳本", sev: "FAIL", status: "FIXED", light: "ok", lib: "hmac", note: "hmac + tools 目錄內解析" },
  { code: "DCT10", title: "PIPE 回填死鎖", sev: "FAIL", status: "FIXED", light: "ok", lib: "", note: "stdout/stderr 檔案重導向" },
  { code: "DCT11", title: "軟 RED 阻斷下游", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "硬故障才 BLOCKED · --strict-chain" },
  { code: "DCT12", title: "權杖只比字串", sev: "FAIL", status: "FIXED", light: "ok", lib: "hmac", note: "格式＋commit＋計畫雜湊" },
  { code: "DCT13", title: "快照只看 mtime", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "stamp 檔名優先，其次 mtime" },
  { code: "DCT14", title: "子行程繼承環境", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "最小 env PATH/SystemRoot" },
  { code: "DCT15", title: "cwd＝受測根", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "cwd=隔離 runs/URN" },
  { code: "DCT16", title: "並行度不依資源", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "workers=min(10, CPU)" },
  { code: "DCT17", title: "無重複啟動鎖", sev: "FAIL", status: "FIXED", light: "ok", lib: "", note: "downward.lock PID · --force" },
  { code: "DCT18", title: "逾時全域一刀", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "每能力 300–1800s" },
  { code: "DCT19", title: "失敗不重試", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "TIMEOUT/CRASH 最多 2 次 backoff" },
  { code: "DCT20", title: "最差者綁架整體", sev: "WARN", status: "FIXED", light: "ok", lib: "", note: "硬故障才 RED；分析 RED 只抬 AMBER" },
];

export type DispatchRow = { level: number; urn: string; name: string; state: string; note: string };

export function dispatchDryRun(opts: { token?: string; commit?: boolean } = {}): DispatchRow[] {
  const auth = authorized(opts.token ?? "", Boolean(opts.commit));
  const levels = topoLevels(CAPABILITIES, { authorized: auth });
  const by = new Map(CAPABILITIES.map((c) => [c.urn, c]));
  const blocked = new Set<string>();
  const out: DispatchRow[] = [];
  for (const r of levels) {
    const cap = by.get(r.urn);
    if (!cap) continue;
    const hanging = cap.dependsOn.filter((p) => !by.has(p));
    if (hanging.length) {
      blocked.add(r.urn);
      out.push({ ...r, state: "BLOCKED", note: `UNRESOLVED_DEPENDENCY ${hanging.join(", ")}` });
      continue;
    }
    const up = cap.dependsOn.filter((p) => blocked.has(p));
    if (up.length) {
      blocked.add(r.urn);
      out.push({ ...r, state: "BLOCKED", note: `上游硬故障 ${up.join(", ")}` });
      continue;
    }
    if (cap.mutating && !auth) {
      out.push({ ...r, state: "SKIPPED", note: "變更類 · 需權杖＋commit" });
      continue;
    }
    out.push({
      ...r,
      state: cap.mutating ? "APPLY" : "ANALYSIS",
      note: cap.mutating ? "權杖通過 · 本台 DryRun 不 spawn" : "唯讀契約 · 本台不 spawn",
    });
  }
  return out;
}

export type LaneEv = { kind: string; state: string; verdict: string };

export function aggregateLanes(rows: LaneEv[]): { overall: "GREEN" | "AMBER" | "RED"; lanes: Record<string, string> } {
  const rank: Record<string, number> = { GREEN: 0, SKIPPED: 0, ANALYSIS: 0, APPLY: 0, AMBER: 1, UNKNOWN: 1, BLOCKED: 1, MISSING: 1, RED: 2, CRASHED: 2, TIMEOUT: 2, FAILED: 2 };
  const lanes: Record<string, string> = {};
  let hard = false;
  let found = false;
  let soft = false;
  for (const ev of rows) {
    const kind = ev.kind || "OTHER";
    const prev = lanes[kind] ?? "GREEN";
    if ((rank[ev.verdict] ?? 1) > (rank[prev] ?? 0)) lanes[kind] = ev.verdict;
    if (ev.state === "FAILED" || ev.state === "TIMEOUT" || ev.verdict === "CRASHED") hard = true;
    else if (ev.state === "OK" && ev.verdict === "RED") found = true;
    else if (ev.state === "BLOCKED" || ev.state === "MISSING" || ev.verdict === "AMBER") soft = true;
  }
  return { overall: hard ? "RED" : found || soft ? "AMBER" : "GREEN", lanes };
}

export const CONTROLLER_LAUNCH = [
  "pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/VIA-Launch-Controller.ps1",
  "pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/VIA-Launch-Controller.ps1 -MintToken",
  "pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/VIA-Launch-Controller.ps1 -Commit -Token \"==VEM-APPROVE==…\"",
].join("\n");

export const AST_LAYERS = [
  { id: "L0", name: "位元組", tool: "tokenize.detect_encoding", sees: "編碼／BOM", misses: "語意", light: "ok" as Light },
  { id: "L1", name: "token", tool: "tokenize.tokenize", sees: "Tab／空白混用", misses: "綁定", light: "ok" as Light },
  { id: "L2", name: "語法樹", tool: "ast.parse", sees: "座標／Call／except", misses: "編碼、scope", light: "ok" as Light },
  { id: "L3", name: "作用域", tool: "symtable", sees: "FAST／GLOBAL／DEREF", misses: "動態 getattr", light: "ok" as Light },
];

export type NameNode = {
  id: string;
  ctx: "Load" | "Store" | "Del";
  line: number;
  where: "body" | "defaults" | "decorator";
};

export function unboundLocal(
  nodes: NameNode[],
  params: string[] = [],
  declaredGlobal: string[] = [],
): { id: string; load: number; store: number }[] {
  const skip = new Set([...params, ...declaredGlobal]);
  const firstLoad = new Map<string, number>();
  const firstStore = new Map<string, number>();
  for (const n of nodes) {
    if (n.where !== "body") continue;
    if (n.ctx === "Load") firstLoad.set(n.id, firstLoad.get(n.id) ?? n.line);
    if (n.ctx === "Store") firstStore.set(n.id, firstStore.get(n.id) ?? n.line);
  }
  const out: { id: string; load: number; store: number }[] = [];
  for (const [id, load] of firstLoad) {
    if (skip.has(id)) continue;
    const store = firstStore.get(id);
    if (store != null && load < store) out.push({ id, load, store });
  }
  return out;
}

export const NAME_CTX = [
  { ctx: "Load", syntax: "讀值", example: "print(x) · obj in obj.attr" },
  { ctx: "Store", syntax: "綁定", example: "x=1 · y+=2 · a:=b" },
  { ctx: "Del", syntax: "解除", example: "del z" },
];

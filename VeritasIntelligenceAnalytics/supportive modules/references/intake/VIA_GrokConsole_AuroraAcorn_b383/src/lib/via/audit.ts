import type { EngineRec, Light } from "./types.ts";

export const AUDIT_STEPS = [
  { id: "A01", name: "IDENTITY", title: "識別" },
  { id: "A02", name: "PATH", title: "路徑" },
  { id: "A03", name: "HASH", title: "指紋" },
  { id: "A04", name: "IMPORT", title: "載入" },
  { id: "A05", name: "ACCEL", title: "加速器" },
  { id: "A06", name: "NET", title: "網路閘" },
  { id: "A07", name: "NLP", title: "NLP閘" },
  { id: "A08", name: "SSOT", title: "SSOT" },
  { id: "A09", name: "SELFTEST", title: "自測" },
  { id: "A10", name: "REPAIR", title: "修復" },
] as const;

export type RepairKind = "NONE" | "REPAIRED" | "UNREPAIRABLE";

export type AuditCtx = {
  confirmNet: boolean;
  confirmNlp: boolean;
};

export type AuditResult = {
  engineId: string;
  engineName: string;
  kind: string;
  steps: Record<string, Light>;
  repair: RepairKind;
  patch: Partial<EngineRec>;
  findings: string[];
  status: Light;
  note: string;
};

export function repairHash(id: string): string {
  const hex = id.toLowerCase().replace(/[^a-f0-9]/g, "a");
  return (hex + "aaaaaa").slice(0, 6);
}

function isOrphan(engine: EngineRec): boolean {
  return !engine.path.trim() || /orphan|broken/i.test(engine.name) || /orphan|broken/i.test(engine.id);
}

export function auditEngine(engine: EngineRec, ctx: AuditCtx): AuditResult {
  const steps: Record<string, Light> = {};
  const patch: Partial<EngineRec> = {};
  const findings: string[] = [];
  let repaired = false;
  let blocked = false;

  if (!engine.id.trim()) {
    steps.A01 = "bad";
    blocked = true;
    findings.push("無 vis_id · 無法修復");
  } else {
    steps.A01 = "ok";
  }

  if (!engine.path.trim()) {
    steps.A02 = "bad";
    blocked = true;
    findings.push("路徑空白 · 無法自動修復");
  } else {
    steps.A02 = "ok";
  }

  if (!engine.hash || engine.hash.length < 4) {
    steps.A03 = "warn";
    patch.hash = repairHash(engine.id || engine.name);
    repaired = true;
    findings.push(`指紋缺失 · 補 ${patch.hash}`);
  } else {
    steps.A03 = "ok";
  }

  if (isOrphan(engine)) {
    steps.A04 = "bad";
    blocked = true;
    findings.push("載入失敗 · 原件不在 · 無法顯示執行態，仍寫入 DETAILS");
  } else {
    steps.A04 = "ok";
  }

  if (!engine.accel) {
    steps.A05 = "warn";
    patch.accel = true;
    repaired = true;
    findings.push("ACCEL 橋缺失 · 已自動掛上");
  } else {
    steps.A05 = "ok";
  }

  if (engine.kind === "NET" && !engine.net) {
    if (ctx.confirmNet) {
      steps.A06 = "warn";
      patch.net = true;
      repaired = true;
      findings.push("NET 閘已確認 · 接通");
    } else {
      steps.A06 = "warn";
      blocked = true;
      findings.push("NET 未確認 · 保持零外呼 · 閘無法自動修復");
    }
  } else {
    steps.A06 = "ok";
  }

  if (engine.kind === "NLP" && !engine.nlp) {
    if (ctx.confirmNlp) {
      steps.A07 = "warn";
      patch.nlp = true;
      repaired = true;
      findings.push("NLP 閘已確認 · 接通樞紐");
    } else {
      steps.A07 = "warn";
      blocked = true;
      findings.push("NLP 未確認 · 不掛樞紐 · 閘無法自動修復");
    }
  } else {
    steps.A07 = "ok";
  }

  if (!engine.ssot) {
    steps.A08 = "warn";
    patch.ssot = true;
    repaired = true;
    findings.push("SSOT 未完 · 補登錄 append-only");
  } else {
    steps.A08 = "ok";
  }

  const prior = ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08"].map((k) => steps[k]);
  if (prior.includes("bad")) steps.A09 = "bad";
  else if (prior.includes("warn")) steps.A09 = "warn";
  else steps.A09 = "ok";

  let repair: RepairKind;
  if (blocked) {
    repair = "UNREPAIRABLE";
    steps.A10 = repaired ? "warn" : "bad";
  } else if (repaired) {
    repair = "REPAIRED";
    steps.A10 = "ok";
  } else {
    repair = "NONE";
    steps.A10 = "ok";
  }

  const status: Light = repair === "UNREPAIRABLE" ? (repaired ? "warn" : "bad") : repair === "REPAIRED" ? "ok" : "ok";
  const note =
    findings.length > 0
      ? findings.join(" · ")
      : repair === "NONE"
        ? "AUDIT 通過 · 無需修復"
        : "AUDIT 完成";

  return {
    engineId: engine.id,
    engineName: engine.name,
    kind: engine.kind,
    steps,
    repair,
    patch,
    findings: findings.length ? findings : ["通過"],
    status,
    note,
  };
}

export function applyAuditPatch(engine: EngineRec, result: AuditResult): EngineRec {
  return {
    ...engine,
    ...result.patch,
    status: result.status,
    note: result.note,
  };
}

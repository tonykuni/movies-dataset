import { useMemo, useState } from "react";
import { FileCode, ShieldAlert, Sparkles } from "lucide-react";
import {
  PS_FILES,
  TEMPLATE_FILE,
  auditPs,
  generateJoined,
  type PsAudit,
  type PsFile,
} from "@/lib/ps-audit";
import { saveUrlAsFile } from "@/lib/save-file";
import { cn } from "@/lib/utils";

export function PsAuditBay() {
  const [files, setFiles] = useState<PsFile[]>(PS_FILES);
  const [sel, setSel] = useState(PS_FILES[2]!.id);
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [scanned, setScanned] = useState(false);

  const audits = useMemo(() => files.map(auditPs), [files]);
  const current = audits.find((a) => a.file.id === sel) ?? audits[0]!;
  const pass = audits.filter((a) => a.verdict === "pass").length;
  const joinN = audits.filter((a) => a.verdict === "join").length;
  const block = audits.filter((a) => a.verdict === "block").length;
  const avg = Math.round(audits.reduce((s, a) => s + a.score, 0) / Math.max(1, audits.length));

  async function scan() {
    if (busy) return;
    setBusy(true);
    setScanned(false);
    setLog([]);
    for (const a of audits) {
      setLog((l) => [`CHECK ${a.file.name}  ${a.verdict.toUpperCase()}  ${a.score}`, ...l].slice(0, 16));
      await wait(90);
    }
    setLog((l) => [`DONE  ${pass} 通過 · ${joinN} 待接入 · ${block} 阻擋`, ...l].slice(0, 16));
    setScanned(true);
    setBusy(false);
  }

  async function joinSel() {
    if (busy) return;
    const f = files.find((x) => x.id === sel);
    if (!f || f.kind === "origin" || f.kind === "template") return;
    if (f.kind === "joined") return;
    setBusy(true);
    setLog((l) => [`JOIN ${f.name} → 模板`, ...l].slice(0, 16));
    await wait(180);
    const next = generateJoined(f);
    setFiles((prev) => prev.map((p) => (p.id === f.id ? next : p)));
    setSel(next.id);
    setLog((l) => [`JOINED ${next.name}  IEX/HKLM/High 已盾`, ...l].slice(0, 16));
    setBusy(false);
  }

  async function joinAll() {
    if (busy) return;
    setBusy(true);
    const raw = files.filter((f) => f.kind === "ai-raw");
    for (const f of raw) {
      setLog((l) => [`JOIN ${f.name}`, ...l].slice(0, 16));
      await wait(140);
    }
    setFiles((prev) => prev.map((p) => (p.kind === "ai-raw" ? generateJoined(p) : p)));
    setLog((l) => ["ALL JOINED  AI 產出已接入模板", ...l].slice(0, 16));
    setBusy(false);
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">PS TEMPLATE GUARD · ANC-30</p>
            <h2 className="mt-1 text-lg font-medium tracking-display">PS 檔智慧檢查</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              自動掃全部 PowerShell 檔。AI 被要求產出 .ps1 時強制接入模板；禁令命中即擋。
            </p>
          </div>
          <div className="min-w-28">
            <p className="font-mono text-[10px] tracking-widest text-muted">SCORE</p>
            <p className="font-mono text-3xl tabular-nums">{avg}</p>
          </div>
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Kpi label="檔案" value={String(audits.length)} />
          <Kpi label="通過" value={String(pass)} />
          <Kpi label="待接入" value={String(joinN)} />
          <Kpi label="阻擋" value={String(block)} />
        </dl>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void scan()}
            disabled={busy}
            className="min-h-11 rounded-[var(--radius-md)] bg-accent px-4 text-sm font-medium text-accent-fg disabled:opacity-60"
          >
            {busy ? "檢查中…" : scanned ? "再檢查一次" : "智慧檢查全部"}
          </button>
          <button
            type="button"
            onClick={() => void joinSel()}
            disabled={busy || current.file.kind !== "ai-raw"}
            className="min-h-11 rounded-[var(--radius-md)] border border-border px-4 text-sm text-fg hover:bg-bg-subtle disabled:opacity-40"
          >
            此檔接入模板
          </button>
          <button
            type="button"
            onClick={() => void joinAll()}
            disabled={busy || !files.some((f) => f.kind === "ai-raw")}
            className="min-h-11 rounded-[var(--radius-md)] border border-border px-4 text-sm text-fg hover:bg-bg-subtle disabled:opacity-40"
          >
            AI 產出全部接入
          </button>
          <button
            type="button"
            onClick={() => void saveUrlAsFile(TEMPLATE_FILE, "VeritasCeleritas.PS7.Template.ps1")}
            className="inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] border border-border px-4 text-sm text-fg hover:bg-bg-subtle"
          >
            存模板 .ps1
          </button>
        </div>
      </section>

      <div className="overflow-x-auto rounded-[var(--radius-xl)] border border-border">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="bg-bg-elevated font-mono text-[10px] tracking-widest text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">檔案</th>
              <th className="px-3 py-2 font-medium">接入</th>
              <th className="px-3 py-2 font-medium">還原</th>
              <th className="px-3 py-2 font-medium">PS7</th>
              <th className="px-3 py-2 font-medium">禁令</th>
              <th className="px-3 py-2 font-medium">分數</th>
              <th className="px-3 py-2 font-medium">判定</th>
            </tr>
          </thead>
          <tbody>
            {audits.map((a) => (
              <tr
                key={a.file.id}
                className={cn(
                  "cursor-pointer border-t border-border",
                  sel === a.file.id ? "bg-bg-elevated" : "hover:bg-bg-subtle",
                )}
                onClick={() => setSel(a.file.id)}
              >
                <td className="px-3 py-2">
                  <span className="block font-mono text-xs text-fg">{a.file.name}</span>
                  <span className="block text-xs text-muted">{a.file.intent}</span>
                </td>
                <td className="px-3 py-2 font-mono text-xs">{a.joined ? "是" : "否"}</td>
                <td className="px-3 py-2 font-mono text-xs">{a.restore ? "是" : "否"}</td>
                <td className="px-3 py-2 font-mono text-xs">{a.requires7 ? "7+" : "缺"}</td>
                <td className="px-3 py-2 font-mono text-xs">{a.forbidden}</td>
                <td className="px-3 py-2 font-mono text-xs tabular-nums">{a.score}</td>
                <td className="px-3 py-2">
                  <Verdict v={a.verdict} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
          <div className="mb-3 flex items-center gap-2 text-accent">
            <FileCode className="size-4" strokeWidth={1.75} />
            <h3 className="text-sm font-medium">{current.file.name}</h3>
          </div>
          <pre className="max-h-56 overflow-auto rounded-[var(--radius-md)] bg-bg p-3 font-mono text-xs text-muted">
            {current.file.source}
          </pre>
        </article>
        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
          <div className="mb-3 flex items-center gap-2 text-accent">
            <ShieldAlert className="size-4" strokeWidth={1.75} />
            <h3 className="text-sm font-medium">發現</h3>
          </div>
          <ul className="space-y-1.5">
            {current.findings.map((f) => (
              <li key={f.id} className="flex items-center gap-2 rounded-[var(--radius-md)] bg-bg px-3 py-2">
                <span className="min-w-0 flex-1">
                  <span className="block text-xs text-fg">{f.rule}</span>
                  <span className="block font-mono text-[10px] text-muted">{f.detail}</span>
                </span>
                <span
                  className={cn(
                    "font-mono text-[10px] tracking-widest",
                    f.sev === "forbid"
                      ? f.hit
                        ? "text-danger"
                        : "text-ok"
                      : f.hit
                        ? "text-ok"
                        : "text-warn",
                  )}
                >
                  {f.sev === "forbid" ? (f.hit ? "HIT" : "CLEAN") : f.hit ? "OK" : "MISS"}
                </span>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
        <div className="mb-3 flex items-center gap-2 text-accent">
          <Sparkles className="size-4" strokeWidth={1.75} />
          <h3 className="text-sm font-medium">檢查日誌</h3>
        </div>
        <ol className="max-h-40 space-y-1 overflow-auto font-mono text-xs text-muted">
          {log.length === 0 ? (
            <li className="text-subtle">尚未掃描。點「智慧檢查全部」。裸生成檔必須接入模板。</li>
          ) : (
            log.map((line, i) => (
              <li key={`${line}-${i}`} className="rounded-[var(--radius-sm)] bg-bg px-3 py-1.5">
                {line}
              </li>
            ))
          )}
        </ol>
      </article>
    </div>
  );
}

function Verdict({ v }: { v: PsAudit["verdict"] }) {
  const label = v === "pass" ? "通過" : v === "join" ? "待接入" : "阻擋";
  return (
    <span
      className={cn(
        "font-mono text-[10px] tracking-widest",
        v === "pass" ? "text-ok" : v === "join" ? "text-warn" : "text-danger",
      )}
    >
      {label}
    </span>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2">
      <p className="font-mono text-[10px] tracking-widest text-muted">{label}</p>
      <p className="font-mono text-lg tabular-nums">{value}</p>
    </div>
  );
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

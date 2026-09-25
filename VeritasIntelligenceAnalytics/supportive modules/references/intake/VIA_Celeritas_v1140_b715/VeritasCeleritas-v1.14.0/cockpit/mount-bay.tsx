import { useEffect, useMemo, useState } from "react";
import { Cpu, Link2, Radio, Shield, Waypoints } from "lucide-react";
import {
  CPU_POLICY,
  MOUNT_COMMANDS,
  MOUNT_LIBS,
  MOUNT_STEPS,
  coverageOfSites,
  kindLabel,
  type MountCommand,
  type ProbeSite,
  type SiteStatus,
} from "@/lib/mount";
import { cn } from "@/lib/utils";

type StepId = (typeof MOUNT_STEPS)[number]["id"] | "idle" | "ready";

function cloneCommand(cmd: MountCommand): MountCommand {
  return { ...cmd, sites: cmd.sites.map((s) => ({ ...s, status: "idle" })) };
}

export function MountBay() {
  const [cmdId, setCmdId] = useState(MOUNT_COMMANDS[1]!.id);
  const [cmd, setCmd] = useState<MountCommand>(() => cloneCommand(MOUNT_COMMANDS[1]!));
  const [step, setStep] = useState<StepId>("idle");
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  const cover = coverageOfSites(cmd.sites);
  const wrapped = cmd.sites.filter((s) => s.status === "wrapped").length;
  const shielded = cmd.sites.filter((s) => s.status === "shielded").length;
  const stepIndex = MOUNT_STEPS.findIndex((s) => s.id === step);

  const report = useMemo(
    () => ({
      target: cmd.origin,
      phase: step === "ready" ? "READY" : step === "idle" ? "IDLE" : String(step).toUpperCase(),
      coverage: cover,
      workers: CPU_POLICY.workers,
      physical: CPU_POLICY.physical,
      sites: cmd.sites.length,
      wrapped,
      shielded,
    }),
    [cmd, cover, shielded, step, wrapped],
  );

  useEffect(() => {
    const next = MOUNT_COMMANDS.find((c) => c.id === cmdId);
    if (!next) return;
    setCmd(cloneCommand(next));
    setStep("idle");
    setLog([]);
    setBusy(false);
  }, [cmdId]);

  async function runMount() {
    if (busy) return;
    setBusy(true);
    setLog((l) => [`CONNECT ${cmd.origin}`, ...l].slice(0, 12));
    setStep("connect");
    await wait(220);

    setStep("probe");
    setLog((l) => [`PROBE parso depth-walk ${cmd.sites.length} sites`, ...l].slice(0, 12));
    setCmd((c) => ({ ...c, sites: c.sites.map((s) => ({ ...s, status: "probed" as SiteStatus })) }));
    await wait(280);

    setStep("classify");
    setLog((l) => ["CLASSIFY parallel/numeric/io/unsafe", ...l].slice(0, 12));
    await wait(220);

    setStep("wrap");
    setCmd((c) => ({
      ...c,
      sites: c.sites.map((s) => ({
        ...s,
        status: s.kind === "unsafe" ? "shielded" : "wrapped",
      })),
    }));
    setLog((l) => ["WRAP wrapt + loky/cloudpickle · SHIELD unsafe", ...l].slice(0, 12));
    await wait(260);

    setStep("sync");
    setLog((l) => ["SYNC watchdog observing source", ...l].slice(0, 12));
    await wait(200);

    setStep("report");
    setLog((l) => [`REPORT central coverage=100 workers=${CPU_POLICY.workers}`, ...l].slice(0, 12));
    await wait(200);

    setStep("cover");
    await wait(180);
    setStep("ready");
    setLog((l) => ["COVER 100% — every site wrapped or shielded", ...l].slice(0, 12));
    setBusy(false);
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">MOUNT PILOT · ANC-28</p>
            <h2 className="mt-1 text-lg font-medium tracking-display">智慧掛載艙</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              對任何指令 CONNECT → 向下探群 → CPU 自適應加速 → 向中央回報。不安全點只盾、不加速。覆蓋率以「每個探到的點都有包裝或後備」計。
            </p>
          </div>
          <CoverMeter value={cover} />
        </div>

        <ol className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
          {MOUNT_STEPS.map((s, i) => {
            const on = step === s.id || (step === "ready" && i === MOUNT_STEPS.length - 1);
            const done = stepIndex > i || step === "ready";
            return (
              <li
                key={s.id}
                className={cn(
                  "rounded-[var(--radius-md)] border px-3 py-2",
                  on ? "border-accent bg-bg" : "border-border bg-bg",
                )}
              >
                <p
                  className={cn(
                    "font-mono text-[10px] tracking-widest",
                    on || done ? "text-accent" : "text-subtle",
                  )}
                >
                  {s.label}
                </p>
                <p className="mt-1 text-xs text-muted">{s.desc}</p>
              </li>
            );
          })}
        </ol>
      </section>

      <section className="grid gap-4 lg:grid-cols-5">
        <div className="space-y-3 lg:col-span-2">
          <div className="flex flex-wrap gap-2">
            {MOUNT_COMMANDS.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setCmdId(c.id)}
                className={cn(
                  "min-h-11 rounded-[var(--radius-md)] border px-3 py-2 text-left text-sm",
                  cmdId === c.id ? "border-accent bg-bg-elevated text-fg" : "border-border text-muted hover:text-fg",
                )}
              >
                <span className="block font-medium text-fg">{c.title}</span>
                <span className="text-xs text-muted">{c.blurb}</span>
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => void runMount()}
            disabled={busy}
            className="min-h-11 w-full rounded-[var(--radius-md)] bg-accent px-4 text-sm font-medium text-accent-fg disabled:opacity-60"
          >
            {busy ? "掛載中…" : step === "ready" ? "再掛載一次" : "掛載此指令"}
          </button>

          <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
            <div className="mb-3 flex items-center gap-2 text-accent">
              <Cpu className="size-4" strokeWidth={1.75} />
              <h3 className="text-sm font-medium">CPU 自適應 · 安全門</h3>
            </div>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <KV k="架構" v={CPU_POLICY.architecture} />
              <KV k="實體核" v={String(CPU_POLICY.physical)} />
              <KV k="worker" v={String(CPU_POLICY.workers)} />
              <KV k="GPU" v={CPU_POLICY.gpu} />
            </dl>
            <p className="mt-3 text-xs text-muted">{CPU_POLICY.adaptive}</p>
            <p className="mt-1 text-xs text-subtle">{CPU_POLICY.safety}</p>
          </article>
        </div>

        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 lg:col-span-3">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-accent">
              <Waypoints className="size-4" strokeWidth={1.75} />
              <h3 className="text-sm font-medium">向下探群 · {cmd.origin}</h3>
            </div>
            <p className="font-mono text-xs text-muted">
              {wrapped} 包裝 · {shielded} 盾 · {cmd.sites.length} 點
            </p>
          </div>
          <ul className="space-y-1.5">
            {cmd.sites.map((s) => (
              <SiteRow key={s.id} site={s} />
            ))}
          </ul>
        </article>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
          <div className="mb-3 flex items-center gap-2 text-accent">
            <Radio className="size-4" strokeWidth={1.75} />
            <h3 className="text-sm font-medium">中央系統回報</h3>
          </div>
          <dl className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <KV k="相位" v={report.phase} />
            <KV k="覆蓋" v={`${report.coverage}%`} />
            <KV k="目標" v={report.target} />
            <KV k="worker" v={`${report.workers}/${report.physical}`} />
          </dl>
          <ol className="space-y-1 font-mono text-xs text-muted">
            {log.length === 0 ? (
              <li className="text-subtle">尚未掛載。中央等待心跳。</li>
            ) : (
              log.map((line, i) => (
                <li key={`${line}-${i}`} className="rounded-[var(--radius-sm)] bg-bg px-3 py-2">
                  {line}
                </li>
              ))
            )}
          </ol>
        </article>

        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
          <div className="mb-3 flex items-center gap-2 text-accent">
            <Link2 className="size-4" strokeWidth={1.75} />
            <h3 className="text-sm font-medium">EXTRA 5 · 掛載層</h3>
          </div>
          <ul className="space-y-2">
            {MOUNT_LIBS.map((lib) => (
              <li
                key={lib.id}
                className="flex items-start justify-between gap-3 rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2"
              >
                <div>
                  <p className="font-mono text-sm text-fg">{lib.id}</p>
                  <p className="text-xs text-muted">{lib.role}</p>
                </div>
                <span className="shrink-0 font-mono text-[10px] tracking-widest text-ok">
                  {lib.version}
                </span>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}

function CoverMeter({ value }: { value: number }) {
  return (
    <div
      className="grid size-24 place-items-center rounded-full"
      style={{
        background: `conic-gradient(var(--color-ok) ${value}%, var(--color-border) 0)`,
      }}
      aria-label={`加速覆蓋 ${value}%`}
    >
      <div className="grid size-16 place-items-center rounded-full bg-bg-elevated">
        <p className="font-mono text-lg tabular-nums">{value}</p>
      </div>
    </div>
  );
}

function KV({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-bg px-2 py-2">
      <dt className="font-mono text-[10px] tracking-widest text-muted">{k}</dt>
      <dd className="mt-0.5 truncate font-mono text-xs text-fg" title={v}>
        {v}
      </dd>
    </div>
  );
}

function SiteRow({ site }: { site: ProbeSite }) {
  return (
    <li className="flex items-center gap-2 rounded-[var(--radius-md)] bg-bg px-3 py-2">
      <span
        className={cn(
          "shrink-0 font-mono text-[10px] text-subtle",
          site.depth === 1 && "pl-3",
          site.depth >= 2 && "pl-6",
        )}
      >
        {site.depth > 0 ? "↳" : "·"}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate font-mono text-xs text-fg">{site.name}</span>
        <span className="block truncate text-xs text-muted">
          {site.backend} · {site.fallback}
        </span>
      </span>
      <span className="shrink-0 font-mono text-[10px] tracking-widest text-subtle">
        {kindLabel(site.kind)}
      </span>
      <StatusChip status={site.status} unsafe={site.kind === "unsafe"} />
    </li>
  );
}

function StatusChip({ status, unsafe }: { status: SiteStatus; unsafe: boolean }) {
  if (status === "shielded" || (unsafe && status !== "idle")) {
    return (
      <span className="inline-flex items-center gap-1 font-mono text-[10px] tracking-widest text-warn">
        <Shield className="size-3" strokeWidth={1.75} />
        盾
      </span>
    );
  }
  const label =
    status === "wrapped" ? "WRAP" : status === "probed" ? "PROBE" : "IDLE";
  return (
    <span
      className={cn(
        "font-mono text-[10px] tracking-widest",
        status === "wrapped" ? "text-ok" : status === "probed" ? "text-accent" : "text-subtle",
      )}
    >
      {label}
    </span>
  );
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

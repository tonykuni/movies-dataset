import { useMemo, useState } from "react";
import { Download, Layers, ShieldAlert } from "lucide-react";
import { ACCEL_30, CPU_POLICY_PS, LAYERS, PRE_DEPRESS, PS_STACK_FILE, PS_STACK_VERSION, REFUSED, type AccelItem, type AccelLayer } from "@/lib/ps-stack";
import { PACK_FILE, PACK_NAME } from "@/lib/registry";
import { saveUrlAsFile } from "@/lib/save-file";
import { cn } from "@/lib/utils";

type Phase = "idle" | "depress" | "stack" | "ready";

export function PsStack() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [applied, setApplied] = useState<Set<string>>(new Set());
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [layer, setLayer] = useState<AccelLayer | "all">("all");

  const all = useMemo(() => [...PRE_DEPRESS, ...ACCEL_30], []);
  const visible = layer === "all" ? all : all.filter((a) => a.layer === layer);
  const pct = Math.round((100 * applied.size) / all.length);

  async function run() {
    if (busy) return;
    setBusy(true);
    setApplied(new Set());
    setLog([]);
    setPhase("depress");
    const next = new Set<string>();
    for (const item of PRE_DEPRESS) {
      next.add(item.code);
      setApplied(new Set(next));
      setLog((l) => [`${item.code}  ${item.title}`, ...l].slice(0, 14));
      await wait(90);
    }
    setPhase("stack");
    for (const item of ACCEL_30) {
      next.add(item.code);
      setApplied(new Set(next));
      setLog((l) => [`${item.code}  ${item.title}`, ...l].slice(0, 14));
      await wait(55);
    }
    setPhase("ready");
    setLog((l) => ["READY  本行程已堆疊 · 關閉即還原", ...l].slice(0, 14));
    setBusy(false);
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">
              PS7 CPU STACK · v{PS_STACK_VERSION}
            </p>
            <h2 className="mt-1 text-lg font-medium tracking-display">PowerShell 7 交叉堆疊</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              先對本行程減壓，再疊 30 個加速器。只動目前 PID，不掃其他進程、不改系統檔。執行緒池封頂 64，優先權最高 AboveNormal，Error 不吞。
            </p>
          </div>
          <div className="min-w-28">
            <p className="font-mono text-[10px] tracking-widest text-muted">STACK</p>
            <p className="font-mono text-3xl tabular-nums">{pct}%</p>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-bg">
              <div
                className="h-full bg-ok transition-[width] duration-150"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void run()}
            disabled={busy}
            className="min-h-11 rounded-[var(--radius-md)] bg-accent px-4 text-sm font-medium text-accent-fg disabled:opacity-60"
          >
            {busy ? "堆疊中…" : phase === "ready" ? "再堆一次" : "套用 5+30 堆疊"}
          </button>
          <button
            type="button"
            onClick={() => void saveUrlAsFile(PS_STACK_FILE, "VeritasCeleritas.PS7.ps1")}
            className="inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] border border-border px-4 text-sm text-fg hover:bg-bg-subtle"
          >
            <Download className="size-4" strokeWidth={1.75} />
            下載 .ps1
          </button>
          <button
            type="button"
            onClick={() => void saveUrlAsFile(PACK_FILE, PACK_NAME)}
            className="inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] border border-border px-4 text-sm text-fg hover:bg-bg-subtle"
          >
            <Download className="size-4" strokeWidth={1.75} />
            下載全包 ZIP
          </button>
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        <LayerChip id="all" label="全部" on={layer === "all"} onClick={() => setLayer("all")} />
        {LAYERS.map((l) => (
          <LayerChip
            key={l.id}
            id={l.id}
            label={`${l.label} ${l.blurb}`}
            on={layer === l.id}
            onClick={() => setLayer(l.id)}
          />
        ))}
      </div>

      <section className="grid gap-4 lg:grid-cols-5">
        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 lg:col-span-3">
          <div className="mb-3 flex items-center gap-2 text-accent">
            <Layers className="size-4" strokeWidth={1.75} />
            <h3 className="text-sm font-medium">加速器矩陣</h3>
          </div>
          <ul className="grid gap-1.5 sm:grid-cols-2">
            {visible.map((item) => (
              <AccelRow key={item.code} item={item} on={applied.has(item.code)} />
            ))}
          </ul>
        </article>

        <div className="space-y-4 lg:col-span-2">
          <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
            <h3 className="text-sm font-medium text-accent">本行程策略</h3>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <KV k="架構" v={CPU_POLICY_PS.architecture} />
              <KV k="優先權" v={CPU_POLICY_PS.priority} />
              <KV k="執行緒池" v={CPU_POLICY_PS.pool} />
              <KV k="平行" v={CPU_POLICY_PS.parallel} />
              <KV k="GPU" v={CPU_POLICY_PS.gpu} />
              <KV k="還原" v={CPU_POLICY_PS.restore} />
            </dl>
          </article>
          <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
            <h3 className="text-sm font-medium text-accent">堆疊紀錄</h3>
            <ol className="mt-3 max-h-56 space-y-1 overflow-auto font-mono text-xs text-muted">
              {log.length === 0 ? (
                <li className="text-subtle">尚未套用。點「套用 5+30 堆疊」。</li>
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
      </section>

      <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
        <div className="mb-3 flex items-center gap-2 text-warn">
          <ShieldAlert className="size-4" strokeWidth={1.75} />
          <h3 className="text-sm font-medium">安全門 · 明確拒絕</h3>
        </div>
        <p className="mb-3 text-sm text-muted">
          下列寫法會傷到其他軟體或把錯誤藏起來，模組不會做。減壓只清本行程。
        </p>
        <ul className="grid gap-2 sm:grid-cols-2">
          {REFUSED.map((r) => (
            <li key={r.bad} className="rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2">
              <p className="font-mono text-xs text-fg">{r.bad}</p>
              <p className="mt-0.5 text-xs text-muted">{r.why}</p>
            </li>
          ))}
        </ul>
      </article>
    </div>
  );
}

function LayerChip({
  id,
  label,
  on,
  onClick,
}: {
  id: string;
  label: string;
  on: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "min-h-11 rounded-[var(--radius-md)] border px-3 text-sm",
        on ? "border-accent bg-bg-elevated text-fg" : "border-border text-muted hover:text-fg",
      )}
    >
      {label}
    </button>
  );
}

function AccelRow({ item, on }: { item: AccelItem; on: boolean }) {
  return (
    <li
      className={cn(
        "flex items-start gap-2 rounded-[var(--radius-md)] border px-3 py-2",
        on ? "border-ok/40 bg-bg" : "border-border bg-bg",
      )}
    >
      <span className={cn("font-mono text-[10px] tracking-widest", on ? "text-ok" : "text-subtle")}>
        {item.code}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm text-fg">{item.title}</span>
        <span className="block truncate text-xs text-muted">{item.effect}</span>
      </span>
    </li>
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

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

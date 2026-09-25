import { useEffect, useState } from "react";
import { Cpu, GitMerge, Shield, Waypoints } from "lucide-react";
import {
  PS_UNDER_PY,
  UNIFY_COMMANDS,
  unifyCoverage,
  type AstAction,
  type UnifyCommand,
} from "@/lib/unified";
import { cn } from "@/lib/utils";

type Step = "idle" | "ast" | "inject" | "trace" | "ps" | "ready";

function clone(cmd: UnifyCommand): UnifyCommand {
  return { ...cmd, actions: cmd.actions.map((a) => ({ ...a, status: "idle" })) };
}

export function UnifyBay() {
  const [id, setId] = useState(UNIFY_COMMANDS[0]!.id);
  const [cmd, setCmd] = useState<UnifyCommand>(() => clone(UNIFY_COMMANDS[0]!));
  const [step, setStep] = useState<Step>("idle");
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [psOn, setPsOn] = useState(0);

  const cover = unifyCoverage(cmd.actions);
  const shielded = cmd.actions.filter((a) => a.status === "shield").length;
  const accel = cmd.actions.filter((a) => a.status === "accel").length;

  useEffect(() => {
    const next = UNIFY_COMMANDS.find((c) => c.id === id);
    if (!next) return;
    setCmd(clone(next));
    setStep("idle");
    setLog([]);
    setPsOn(0);
    setBusy(false);
  }, [id]);

  async function run() {
    if (busy) return;
    setBusy(true);
    setPsOn(0);
    setStep("ast");
    setLog((l) => [`AST inventory ${cmd.actions.length} actions`, ...l].slice(0, 14));
    setCmd((c) => ({ ...c, actions: c.actions.map((a) => ({ ...a, status: "traced" })) }));
    await wait(280);

    setStep("inject");
    setCmd((c) => ({
      ...c,
      actions: c.actions.map((a) => ({
        ...a,
        status: a.unsafe ? "shield" : "accel",
      })),
    }));
    setLog((l) => ["INJECT _CEL_T before every stmt · shield eval", ...l].slice(0, 14));
    await wait(280);

    setStep("trace");
    setLog((l) => ["AUTO-TRACE sys.settrace line hits", ...l].slice(0, 14));
    await wait(220);

    setStep("ps");
    for (let n = 5; n <= PS_UNDER_PY.length; n += 6) {
      setPsOn(Math.min(n, PS_UNDER_PY.length));
      await wait(70);
    }
    setPsOn(PS_UNDER_PY.length);
    setLog((l) => [`PS7 ${PS_UNDER_PY.length} units owned by Python`, ...l].slice(0, 14));
    await wait(180);

    setStep("ready");
    setLog((l) => ["UNIFIED 100% actions covered", ...l].slice(0, 14));
    setBusy(false);
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">
              UNIFIED ENGINE · ANC-37
            </p>
            <h2 className="mt-1 text-lg font-medium tracking-display">單一整合引擎</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              覆蓋率是探針數除以站點數，不再寫死 100。class 本體、except、match、while-else 都算站點。except 裡的 eval 會被盾掉。
            </p>
          </div>
          <div className="min-w-28">
            <p className="font-mono text-[10px] tracking-widest text-muted">ACTIONS</p>
            <p className="font-mono text-3xl tabular-nums">{cover}%</p>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-bg">
              <div className="h-full bg-ok transition-[width] duration-150" style={{ width: `${cover}%` }} />
            </div>
          </div>
        </div>
        <ol className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-5">
          {[
            ["AST", "清點全部動作"],
            ["INJECT", "每句插入追蹤"],
            ["TRACE", "自動行追蹤"],
            ["PS⊂PY", "35 單元由 Python 管"],
            ["COVER", "探針 / 站點"],
          ].map(([k, v], i) => {
            const order: Step[] = ["ast", "inject", "trace", "ps", "ready"];
            const on = step === order[i] || (step === "ready" && i === 4);
            const done = order.indexOf(step) > i || step === "ready";
            return (
              <li
                key={k}
                className={cn(
                  "rounded-[var(--radius-md)] border px-3 py-2",
                  on ? "border-accent bg-bg" : "border-border bg-bg",
                )}
              >
                <p className={cn("font-mono text-[10px] tracking-widest", on || done ? "text-accent" : "text-subtle")}>
                  {k}
                </p>
                <p className="mt-1 text-xs text-muted">{v}</p>
              </li>
            );
          })}
        </ol>
      </section>

      <div className="flex flex-wrap gap-2">
        {UNIFY_COMMANDS.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => setId(c.id)}
            className={cn(
              "min-h-11 rounded-[var(--radius-md)] border px-3 py-2 text-left text-sm",
              id === c.id ? "border-accent bg-bg-elevated text-fg" : "border-border text-muted hover:text-fg",
            )}
          >
            <span className="block font-medium text-fg">{c.title}</span>
            <span className="text-xs text-muted">{c.origin}</span>
          </button>
        ))}
        <button
          type="button"
          onClick={() => void run()}
          disabled={busy}
          className="min-h-11 rounded-[var(--radius-md)] bg-accent px-4 text-sm font-medium text-accent-fg disabled:opacity-60"
        >
          {busy ? "整合中…" : step === "ready" ? "再整合一次" : "AST 整合覆蓋"}
        </button>
      </div>

      <section className="grid gap-4 lg:grid-cols-5">
        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 lg:col-span-2">
          <div className="mb-3 flex items-center gap-2 text-accent">
            <Cpu className="size-4" strokeWidth={1.75} />
            <h3 className="text-sm font-medium">指令源碼</h3>
          </div>
          <pre className="overflow-auto rounded-[var(--radius-md)] bg-bg p-3 font-mono text-xs text-muted">
            {cmd.source}
          </pre>
        </article>
        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 lg:col-span-3">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-accent">
              <Waypoints className="size-4" strokeWidth={1.75} />
              <h3 className="text-sm font-medium">AST 全部動作 · {cmd.origin}</h3>
            </div>
            <p className="font-mono text-xs text-muted">
              {accel} 加速 · {shielded} 盾 · {cmd.actions.length} 點
            </p>
          </div>
          <ul className="space-y-1.5">
            {cmd.actions.map((a) => (
              <ActionRow key={a.id} action={a} />
            ))}
          </ul>
        </article>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
          <div className="mb-3 flex items-center gap-2 text-accent">
            <GitMerge className="size-4" strokeWidth={1.75} />
            <h3 className="text-sm font-medium">PS 棧 ⊂ Python</h3>
          </div>
          <p className="mb-3 text-sm text-muted">
            35 個 PowerShell 加速器由 UnifiedEngine 擁有。Python 負責 emit / 狀態 / 還原契約。
          </p>
          <p className="mb-2 font-mono text-xs text-ok">
            {psOn}/{PS_UNDER_PY.length} 已納管
          </p>
          <ul className="grid max-h-48 grid-cols-2 gap-1 overflow-auto sm:grid-cols-3">
            {PS_UNDER_PY.map((u, i) => (
              <li
                key={u.id}
                className={cn(
                  "rounded-[var(--radius-sm)] border px-2 py-1 font-mono text-[10px]",
                  i < psOn ? "border-ok/40 text-fg" : "border-border text-subtle",
                )}
              >
                {u.id} {u.title}
              </li>
            ))}
          </ul>
        </article>
        <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
          <h3 className="text-sm font-medium text-accent">自動追蹤</h3>
          <ol className="mt-3 max-h-56 space-y-1 overflow-auto font-mono text-xs text-muted">
            {log.length === 0 ? (
              <li className="text-subtle">尚未整合。點「AST 整合覆蓋」。</li>
            ) : (
              log.map((line, i) => (
                <li key={`${line}-${i}`} className="rounded-[var(--radius-sm)] bg-bg px-3 py-1.5">
                  {line}
                </li>
              ))
            )}
          </ol>
        </article>
      </section>
    </div>
  );
}

function ActionRow({ action }: { action: AstAction }) {
  return (
    <li className="flex items-center gap-2 rounded-[var(--radius-md)] bg-bg px-3 py-2">
      <span className="w-8 shrink-0 font-mono text-[10px] text-subtle">L{action.lineno}</span>
      <span className="min-w-0 flex-1">
        <span className="block truncate font-mono text-xs text-fg">
          {action.name}
        </span>
        <span className="block text-xs text-muted">
          {action.kind} · {action.layer}
        </span>
      </span>
      {action.status === "shield" || action.unsafe ? (
        <span className="inline-flex items-center gap-1 font-mono text-[10px] tracking-widest text-warn">
          <Shield className="size-3" strokeWidth={1.75} />
          盾
        </span>
      ) : (
        <span
          className={cn(
            "font-mono text-[10px] tracking-widest",
            action.status === "accel" ? "text-ok" : action.status === "traced" ? "text-accent" : "text-subtle",
          )}
        >
          {action.status === "accel" ? "ACCEL" : action.status === "traced" ? "TRACE" : "IDLE"}
        </span>
      )}
    </li>
  );
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

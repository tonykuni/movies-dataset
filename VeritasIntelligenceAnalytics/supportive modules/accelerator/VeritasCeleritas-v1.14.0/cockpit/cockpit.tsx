import { useMemo, useState } from "react";
import {
  ArrowRight,
  Cpu,
  GitBranch,
  Grid3x3,
  Layers,
  Radio,
  Replace,
  ShieldCheck,
} from "lucide-react";
import { InstallMatrix } from "@/components/install-matrix";
import { DepGraph } from "@/components/dep-graph";
import { MountBay } from "@/components/mount-bay";
import { PsStack } from "@/components/ps-stack";
import { PackSave } from "@/components/pack-save";
import { UnifyBay } from "@/components/unify-bay";
import { PsAuditBay } from "@/components/ps-audit";
import { BenchBay } from "@/components/bench";
import { VectorBay } from "@/components/vector-bay";
import { JitBay } from "@/components/jit-bay";
import { LlvmBay } from "@/components/llvm-bay";
import { FailureBay } from "@/components/failure-bay";
import {
  ENGINE_CLASSES,
  EXTRAS,
  KERNEL,
  PHASES,
  RETIRED,
  VERSION,
} from "@/lib/registry";
import { SCAN } from "@/lib/scan";
import { cn } from "@/lib/utils";

type Tab = "fail" | "llvm" | "jit" | "vec" | "race" | "psa" | "unify" | "out" | "ps7" | "mount" | "deps" | "matrix" | "overview" | "extras" | "retired" | "phases" | "engines";

const TABS: { id: Tab; label: string }[] = [
  { id: "fail", label: "失效" },
  { id: "llvm", label: "LLVM" },
  { id: "jit", label: "編譯" },
  { id: "vec", label: "向量化" },
  { id: "race", label: "誰快" },
  { id: "psa", label: "PS 模板" },
  { id: "unify", label: "整合引擎" },
  { id: "out", label: "輸出" },
  { id: "ps7", label: "PS7 棧" },
  { id: "mount", label: "掛載艙" },
  { id: "deps", label: "依賴圖" },
  { id: "matrix", label: "安裝矩陣" },
  { id: "overview", label: "總覽" },
  { id: "extras", label: "EXTRA 15" },
  { id: "retired", label: "退役矩陣" },
  { id: "phases", label: "相位" },
  { id: "engines", label: "引擎" },
];

export function Cockpit() {
  const [tab, setTab] = useState<Tab>("out");
  const [q, setQ] = useState("");

  const extras = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return EXTRAS;
    return EXTRAS.filter(
      (t) =>
        t.name.toLowerCase().includes(s) ||
        t.layer.toLowerCase().includes(s) ||
        t.role.includes(s),
    );
  }, [q]);

  return (
    <div className="min-h-dvh overflow-x-hidden bg-bg text-fg">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "linear-gradient(to right, color-mix(in oklab, var(--color-fg) 5%, transparent) 1px, transparent 1px), linear-gradient(to bottom, color-mix(in oklab, var(--color-fg) 5%, transparent) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse at top, black 20%, transparent 75%)",
        }}
      />

      <header className="relative border-b border-border">
        <div className="mx-auto flex max-w-6xl flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="font-mono text-xs tracking-[0.22em] text-accent">
                VIA / VDF · {KERNEL}
              </p>
              <h1 className="mt-2 text-3xl font-medium tracking-display sm:text-4xl">
                Veritas Celeritas
              </h1>
              <p className="mt-1 max-w-xl text-sm text-muted">
                極限交叉加速引擎 v{VERSION}。十七個分頁已點過。全包可輸出到下載資料夾。
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <PackSave compact />
              <div className="flex items-center gap-2 rounded-[var(--radius-xl)] border border-border bg-bg-elevated px-4 py-3">
                <span className="size-2 rounded-full bg-ok" />
                <div>
                  <p className="font-mono text-[11px] tracking-widest text-muted">PHASE</p>
                  <p className="font-mono text-sm">READY</p>
                </div>
              </div>
            </div>
          </div>

          <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
            <Kpi label="登錄" value={String(SCAN.summary.total)} hint="註冊表工具" />
            <Kpi label="已裝" value={String(SCAN.summary.installed)} hint="CPython 3.10" />
            <Kpi label="未裝" value={String(SCAN.summary.missing)} hint="待補齊" />
            <Kpi label="覆蓋" value={`${SCAN.summary.coverage}%`} hint="可選加速庫" />
            <Kpi label="VIA 域" value={String(Object.keys(SCAN.byEnv).length)} hint="邏輯環境" />
            <Kpi label="conda via_*" value="0" hint="實體環境未偵測" />
          </dl>
        </div>
      </header>

      <div className="relative mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <nav
          className="mb-6 flex flex-nowrap gap-1 overflow-x-auto pb-1"
          aria-label="區段"
        >
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={cn(
                "min-h-11 shrink-0 rounded-[var(--radius-md)] px-4 py-2.5 text-sm font-medium transition-colors duration-150",
                tab === t.id
                  ? "bg-accent text-accent-fg"
                  : "text-muted hover:bg-bg-subtle hover:text-fg",
              )}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {tab === "fail" && <FailureBay />}
        {tab === "llvm" && <LlvmBay />}
        {tab === "jit" && <JitBay />}
        {tab === "vec" && <VectorBay />}
        {tab === "race" && <BenchBay />}
        {tab === "psa" && <PsAuditBay />}
        {tab === "unify" && <UnifyBay />}
        {tab === "out" && <PackSave />}
        {tab === "ps7" && <PsStack />}
        {tab === "mount" && <MountBay />}
        {tab === "deps" && <DepGraph />}
        {tab === "matrix" && <InstallMatrix />}
        {tab === "overview" && <Overview />}
        {tab === "extras" && <Extras q={q} setQ={setQ} rows={extras} />}
        {tab === "retired" && <Retired />}
        {tab === "phases" && <Phases />}
        {tab === "engines" && <Engines />}
      </div>
    </div>
  );
}

function Kpi({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-border bg-bg-elevated px-3 py-3">
      <dt className="font-mono text-[10px] tracking-[0.18em] text-muted">{label}</dt>
      <dd className="mt-1 font-mono text-2xl tabular-nums tracking-tight">{value}</dd>
      <p className="mt-0.5 text-xs text-subtle">{hint}</p>
    </div>
  );
}

function Overview() {
  return (
    <div className="grid gap-4 lg:grid-cols-5">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-5 lg:col-span-3">
        <div className="mb-4 flex items-center gap-2 text-accent">
          <Layers className="size-4" strokeWidth={1.75} />
          <h2 className="text-sm font-medium tracking-wide">升級契約</h2>
        </div>
        <ul className="space-y-3 text-sm text-muted">
          <li className="flex gap-3">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-ok" strokeWidth={1.75} />
            <span>
              公開符號不刪。退役名稱仍可 import，熱路徑改走後繼，呼叫端不必改。
            </span>
          </li>
          <li className="flex gap-3">
            <Replace className="mt-0.5 size-4 shrink-0 text-accent" strokeWidth={1.75} />
            <span>
              移除 10 個停更函式庫的熱路徑依賴，各配一個更強本機免費替代。
            </span>
          </li>
          <li className="flex gap-3">
            <Grid3x3 className="mt-0.5 size-4 shrink-0 text-accent" strokeWidth={1.75} />
            <span>
              新增 15 個 EXTRA：JSON、壓縮、編碼、DF 適配、金融、Excel、SQL、FS、PDF、向量、繁中、HTTP。
            </span>
          </li>
        </ul>
        <div className="mt-5 grid gap-2 sm:grid-cols-2">
          {[
            ["json_dumps / loads", "jiter → orjson → stdlib"],
            ["compress_bytes", "cramjam → zstd → lz4"],
            ["xfetch", "curl_cffi impersonate → requests"],
            ["xnpv / xirr", "numpy-financial 純 Python 後備"],
          ].map(([k, v]) => (
            <div
              key={k}
              className="rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2.5"
            >
              <p className="font-mono text-xs text-fg">{k}</p>
              <p className="mt-0.5 text-xs text-muted">{v}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-5 lg:col-span-2">
        <div className="mb-4 flex items-center gap-2 text-accent">
          <GitBranch className="size-4" strokeWidth={1.75} />
          <h2 className="text-sm font-medium tracking-wide">替換速覽</h2>
        </div>
        <ol className="space-y-2">
          {RETIRED.map((r) => (
            <li
              key={r.id}
              className="flex items-center justify-between gap-2 rounded-[var(--radius-md)] bg-bg px-3 py-2 text-sm"
            >
              <span className="font-mono text-muted line-through decoration-border-strong">
                {r.name}
              </span>
              <ArrowRight className="size-3.5 shrink-0 text-subtle" />
              <span className="font-mono text-fg">{r.successor}</span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function Extras({
  q,
  setQ,
  rows,
}: {
  q: string;
  setQ: (v: string) => void;
  rows: typeof EXTRAS;
}) {
  return (
    <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-sm font-medium tracking-wide">EXTRA 15 · 本機免費</h2>
        <label className="block w-full sm:max-w-xs">
          <span className="sr-only">篩選</span>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="層級 / 名稱 / 用途"
            className="h-11 w-full rounded-[var(--radius-md)] border border-border bg-bg px-3 text-sm text-fg outline-none placeholder:text-subtle focus:border-border-strong"
          />
        </label>
      </div>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="font-mono text-[11px] tracking-widest text-muted">
            <tr className="border-b border-border">
              <th className="py-2 pr-3 font-medium">#</th>
              <th className="py-2 pr-3 font-medium">PACKAGE</th>
              <th className="py-2 pr-3 font-medium">LAYER</th>
              <th className="py-2 pr-3 font-medium">ROLE</th>
              <th className="py-2 font-medium">REPLACES</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t, i) => (
              <tr key={t.id} className="border-b border-border/80">
                <td className="py-3 pr-3 font-mono tabular-nums text-subtle">
                  {String(i + 1).padStart(2, "0")}
                </td>
                <td className="py-3 pr-3 font-mono">{t.pip}</td>
                <td className="py-3 pr-3 text-muted">{t.layer}</td>
                <td className="py-3 pr-3 text-muted">{t.role}</td>
                <td className="py-3 font-mono text-xs text-accent">
                  {t.replaces ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="grid gap-2 md:hidden">
        {rows.map((t) => (
          <article
            key={t.id}
            className="rounded-[var(--radius-md)] border border-border bg-bg p-3"
          >
            <p className="font-mono text-sm">{t.pip}</p>
            <p className="mt-1 text-xs text-muted">{t.layer}</p>
            <p className="mt-1 text-sm">{t.role}</p>
            {t.replaces ? (
              <p className="mt-2 font-mono text-xs text-accent">← {t.replaces}</p>
            ) : null}
          </article>
        ))}
      </div>
      {rows.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted">沒有符合的 EXTRA。</p>
      ) : null}
    </section>
  );
}

function Retired() {
  return (
    <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
      <h2 className="mb-4 text-sm font-medium tracking-wide">
        退役 10 · 熱路徑移除、符號保留
      </h2>
      <div className="grid gap-3">
        {RETIRED.map((r) => (
          <article
            key={r.id}
            className="grid gap-3 rounded-[var(--radius-lg)] border border-border bg-bg p-4 sm:grid-cols-[1fr_auto_1fr]"
          >
            <div>
              <p className="font-mono text-[10px] tracking-widest text-danger">RETIRED</p>
              <p className="mt-1 font-mono text-sm">{r.name}</p>
              <p className="mt-1 text-xs text-muted">{r.role}</p>
            </div>
            <div className="hidden items-center sm:flex">
              <ArrowRight className="size-4 text-subtle" />
            </div>
            <div>
              <p className="font-mono text-[10px] tracking-widest text-ok">SUCCESSOR</p>
              <p className="mt-1 font-mono text-sm">{r.successor}</p>
              <p className="mt-1 text-xs text-muted">{r.reason}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Phases() {
  return (
    <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
      <div className="mb-5 flex items-center gap-2 text-accent">
        <Radio className="size-4" strokeWidth={1.75} />
        <h2 className="text-sm font-medium tracking-wide">運作相位</h2>
      </div>
      <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {PHASES.map((p, i) => {
          const ready = p.id === "ready";
          return (
            <li
              key={p.id}
              className={cn(
                "rounded-[var(--radius-lg)] border p-4",
                ready ? "border-accent bg-bg" : "border-border bg-bg",
              )}
            >
              <p className="font-mono text-[11px] tabular-nums text-subtle">
                {String(i + 1).padStart(2, "0")}
              </p>
              <p className="mt-1 font-mono text-sm">{p.label}</p>
              <p className="mt-1 text-xs text-muted">{p.desc}</p>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function Engines() {
  return (
    <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
      <div className="mb-4 flex items-center gap-2 text-accent">
        <Cpu className="size-4" strokeWidth={1.75} />
        <h2 className="text-sm font-medium tracking-wide">已註冊引擎</h2>
      </div>
      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {ENGINE_CLASSES.map((name) => (
          <li
            key={name}
            className="rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2.5 font-mono text-xs sm:text-sm"
          >
            {name}
          </li>
        ))}
      </ul>
    </section>
  );
}

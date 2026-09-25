import { useMemo, useState } from "react";
import { Box, Filter, MapPin, Search } from "lucide-react";
import { SCAN, VIA_ENVS, type ScanStatus, type ScanTool } from "@/lib/scan";
import { cn } from "@/lib/utils";

type InstallFilter = "all" | "on" | "off" | "extra" | "retired" | "support" | "stdlib";

const FILTERS: { id: InstallFilter; label: string }[] = [
  { id: "all", label: "全部登錄" },
  { id: "off", label: "未安裝" },
  { id: "on", label: "已安裝" },
  { id: "extra", label: "EXTRA" },
  { id: "retired", label: "退役" },
  { id: "support", label: "VIA 模組" },
  { id: "stdlib", label: "標準庫後備" },
];

const STATUS_LABEL: Record<ScanStatus, string> = {
  core: "CORE",
  extra: "EXTRA",
  retired: "RETIRED",
  support: "VIA",
  stdlib: "STDLIB",
};

export function InstallMatrix() {
  const [env, setEnv] = useState<string | null>(null);
  const [filter, setFilter] = useState<InstallFilter>("all");
  const [q, setQ] = useState("");

  const source: ScanTool[] = filter === "stdlib" ? SCAN.stdlib : SCAN.tools;

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return source.filter((t) => {
      if (env && t.env !== env) return false;
      if (filter === "on" && !t.installed) return false;
      if (filter === "off" && t.installed) return false;
      if (filter === "extra" && t.status !== "extra") return false;
      if (filter === "retired" && t.status !== "retired") return false;
      if (filter === "support" && t.status !== "support") return false;
      if (!needle) return true;
      return (
        t.id.toLowerCase().includes(needle) ||
        t.pip.toLowerCase().includes(needle) ||
        t.env.toLowerCase().includes(needle) ||
        t.layer.toLowerCase().includes(needle) ||
        t.role.includes(needle)
      );
    });
  }, [source, env, filter, q]);

  const missing = SCAN.summary.missing;
  const installed = SCAN.summary.installed;
  const total = SCAN.summary.total;

  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">RUNTIME SCAN</p>
            <h2 className="mt-1 text-lg font-medium tracking-display">
              VIA 工具安裝矩陣
            </h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">{SCAN.runtime.note}</p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2 font-mono text-xs">
            <p className="text-muted">CPython {SCAN.runtime.version}</p>
            <p className="mt-0.5 text-fg">conda via_* · 0</p>
          </div>
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat label="登錄工具" value={String(total)} hint="Celeritas 註冊表" />
          <Stat label="已安裝" value={String(installed)} hint="目前直譯器" tone="ok" />
          <Stat label="未安裝" value={String(missing)} hint="待補齊" tone="warn" />
          <Stat
            label="覆蓋率"
            value={`${SCAN.summary.coverage}%`}
            hint={`標準庫後備 ${SCAN.stdlibSummary.installed}/${SCAN.stdlibSummary.total}`}
          />
        </dl>
      </section>

      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="mb-3 flex items-center gap-2 text-accent">
          <Box className="size-4" strokeWidth={1.75} />
          <h3 className="text-sm font-medium tracking-wide">邏輯 VIA 域</h3>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {VIA_ENVS.map((item) => {
            const bucket = SCAN.byEnv[item.id] ?? { total: 0, installed: 0, missing: 0 };
            const pct = bucket.total ? Math.round((100 * bucket.installed) / bucket.total) : 0;
            const active = env === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setEnv(active ? null : item.id)}
                className={cn(
                  "min-h-11 rounded-[var(--radius-md)] border px-3 py-3 text-left transition-colors duration-150",
                  active
                    ? "border-accent bg-bg"
                    : "border-border bg-bg hover:border-border-strong",
                )}
              >
                <p className="font-mono text-[11px] text-accent">{item.id}</p>
                <p className="mt-1 text-sm font-medium">{item.title}</p>
                <p className="mt-0.5 text-xs text-subtle">{item.blurb}</p>
                <div className="mt-2 flex items-baseline justify-between gap-2">
                  <p className="font-mono text-xs tabular-nums text-muted">
                    {bucket.installed}/{bucket.total}
                  </p>
                  <p
                    className={cn(
                      "font-mono text-xs tabular-nums",
                      pct === 0 ? "text-warn" : pct === 100 ? "text-ok" : "text-muted",
                    )}
                  >
                    {pct}%
                  </p>
                </div>
                <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-bg-subtle">
                  <div
                    className={cn("h-full", pct === 0 ? "bg-warn" : "bg-ok")}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-2 text-accent">
            <Filter className="size-4" strokeWidth={1.75} />
            <h3 className="text-sm font-medium tracking-wide">
              {env ?? "全域"} · {rows.length} 筆
            </h3>
          </div>
          <label className="relative block w-full lg:max-w-xs">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-subtle" />
            <span className="sr-only">搜尋工具</span>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="名稱 / 域 / 層級 / 用途"
              className="h-11 w-full rounded-[var(--radius-md)] border border-border bg-bg pl-10 pr-3 text-sm text-fg outline-none placeholder:text-subtle focus:border-border-strong"
            />
          </label>
        </div>

        <div className="mb-4 flex flex-wrap gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => {
                setFilter(f.id);
                if (f.id === "stdlib") setEnv(null);
              }}
              className={cn(
                "min-h-11 shrink-0 rounded-[var(--radius-md)] px-4 text-sm font-medium transition-colors duration-150",
                filter === f.id
                  ? "bg-accent text-accent-fg"
                  : "text-muted hover:bg-bg-subtle hover:text-fg",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="hidden overflow-x-auto md:block">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="font-mono text-[11px] tracking-widest text-muted">
              <tr className="border-b border-border">
                <th className="py-2 pr-3 font-medium">狀態</th>
                <th className="py-2 pr-3 font-medium">工具</th>
                <th className="py-2 pr-3 font-medium">VIA 域</th>
                <th className="py-2 pr-3 font-medium">層級</th>
                <th className="py-2 pr-3 font-medium">版本</th>
                <th className="py-2 font-medium">環境位置</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t, i) => (
                <tr key={`${t.env}-${t.id}-${i}`} className="border-b border-border/80 align-top">
                  <td className="py-3 pr-3">
                    <InstallBadge on={t.installed} />
                  </td>
                  <td className="py-3 pr-3">
                    <p className="font-mono text-fg">{t.pip}</p>
                    <p className="mt-0.5 text-xs text-muted">{t.role}</p>
                    <p className="mt-0.5 font-mono text-[10px] tracking-widest text-subtle">
                      {STATUS_LABEL[t.status]}
                    </p>
                  </td>
                  <td className="py-3 pr-3 font-mono text-xs text-accent">{t.env}</td>
                  <td className="py-3 pr-3 text-muted">{t.layer}</td>
                  <td className="py-3 pr-3 font-mono text-xs tabular-nums text-muted">
                    {t.version ?? "—"}
                  </td>
                  <td className="py-3">
                    <LocationCell tool={t} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="grid gap-2 md:hidden">
          {rows.map((t, i) => (
            <article
              key={`${t.env}-${t.id}-${i}`}
              className="rounded-[var(--radius-md)] border border-border bg-bg p-3"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="font-mono text-sm">{t.pip}</p>
                <InstallBadge on={t.installed} />
              </div>
              <p className="mt-1 text-xs text-muted">{t.role}</p>
              <p className="mt-2 font-mono text-[11px] text-accent">{t.env}</p>
              <LocationCell tool={t} />
            </article>
          ))}
        </div>

        {rows.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted">沒有符合的工具。</p>
        ) : null}
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint: string;
  tone?: "ok" | "warn";
}) {
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-bg px-3 py-3">
      <dt className="font-mono text-[10px] tracking-[0.18em] text-muted">{label}</dt>
      <dd
        className={cn(
          "mt-1 font-mono text-2xl tabular-nums tracking-tight",
          tone === "ok" && "text-ok",
          tone === "warn" && "text-warn",
        )}
      >
        {value}
      </dd>
      <p className="mt-0.5 text-xs text-subtle">{hint}</p>
    </div>
  );
}

function InstallBadge({ on }: { on: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-1 font-mono text-[10px] tracking-widest",
        on ? "bg-bg-subtle text-ok" : "bg-bg-subtle text-warn",
      )}
    >
      <span className={cn("size-1.5 rounded-full", on ? "bg-ok" : "bg-warn")} />
      {on ? "INSTALLED" : "MISSING"}
    </span>
  );
}

function LocationCell({ tool }: { tool: ScanTool }) {
  if (tool.installed && tool.location) {
    return (
      <p className="mt-1 flex items-start gap-1.5 font-mono text-[11px] leading-snug break-all text-muted md:mt-0">
        <MapPin className="mt-0.5 size-3 shrink-0 text-subtle" />
        <span>CPython {SCAN.runtime.version} · {tool.location}</span>
      </p>
    );
  }
  if (tool.declared) {
    return (
      <p className="mt-1 font-mono text-[11px] leading-snug break-all text-warn md:mt-0">
        未安裝 · 宣告於 {tool.declared}
      </p>
    );
  }
  return (
    <p className="mt-1 font-mono text-[11px] text-warn md:mt-0">
      未安裝 · 邏輯域 {tool.env}
    </p>
  );
}

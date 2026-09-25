import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { StatusLight } from "@/components/status-light";
import { cn } from "@/lib/utils";
import { coordinateLayers, tri } from "@/lib/via/coordinate";
import type { Deck, Light } from "@/lib/via/types";

export function LeftEngine({
  nav,
  deck,
  lights,
  counts,
  engineOk,
  engineBad,
  engineWarn,
  activated,
  collapsed,
  onToggle,
  onNav,
  onTest,
}: {
  nav: Array<{ id: Deck; label: string; kicker: string }>;
  deck: Deck;
  lights: Record<Deck, Light>;
  counts: { ok: number; warn: number; bad: number; grey: number };
  engineOk: number;
  engineBad: number;
  engineWarn: number;
  activated: boolean;
  collapsed: boolean;
  onToggle: () => void;
  onNav: (d: Deck) => void;
  onTest: () => void;
}) {
  const layers = coordinateLayers({ engineOk, engineBad, engineWarn, activated });
  const live = activated;

  return (
    <aside
      data-left-engine="1"
      data-dash="left"
      className={cn(
        "flex shrink-0 flex-col border-b border-border bg-surface transition-[width] duration-200 lg:h-full lg:border-b-0 lg:border-r",
        collapsed ? "max-lg:hidden lg:w-12" : "lg:w-64",
      )}
    >
      <div className="hidden items-center justify-between gap-1 px-2 py-2 lg:flex">
        {!collapsed ? (
          <p className="hidden font-mono text-xs uppercase tracking-widest text-subtle sm:block">VIA 左欄</p>
        ) : null}
        <button
          type="button"
          data-action="toggle-left"
          aria-label={collapsed ? "展開左欄" : "折疊左欄"}
          onClick={onToggle}
          className="inline-flex min-h-10 min-w-10 items-center justify-center rounded-md bg-elevated text-muted hover:text-fg"
        >
          {collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
        </button>
      </div>

      {!collapsed ? (
        <div className="hidden px-3 pb-3 lg:block">
          <h2 className="text-sm font-medium leading-tight tracking-tight">唯一總管引擎</h2>
          <p className="mt-1 text-xs leading-snug text-muted">協調 GitHub · 母檔 · via_core · via_*</p>
          <div className="mt-3 flex items-center gap-2">
            <StatusLight status={live ? "ok" : "warn"} />
            <span className="font-mono text-xs text-subtle">{live ? "ACTIVATED" : "協調中"}</span>
          </div>
          <p className="mt-2 font-mono text-xs tabular-nums text-subtle">
            綠 {counts.ok} · 黃 {counts.warn} · 紅 {counts.bad} · 灰 {counts.grey ?? 0}
          </p>
        </div>
      ) : null}

      {!collapsed ? (
        <div className="hidden px-2 pb-2 lg:block">
          <p className="px-1 pb-1 text-xs font-medium uppercase tracking-wide text-subtle">協調層</p>
          <ul className="space-y-0.5">
            {layers.map((l) => (
              <li key={l.id} className="flex items-center gap-2 rounded-sm px-1.5 py-1">
                <StatusLight status={tri(l.light)} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-medium">{l.layer}</p>
                  <p className="truncate font-mono text-xs text-subtle">{l.name}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <nav className={cn("flex gap-1 overflow-x-auto px-2 pb-2", collapsed ? "lg:flex-col" : "lg:flex-col")}>
        {nav.map((item) => {
          const active = deck === item.id;
          return (
            <button
              key={item.id}
              type="button"
              data-deck={item.id}
              aria-label={item.label}
              aria-current={active ? "page" : undefined}
              title={item.label}
              onClick={() => onNav(item.id)}
              className={cn(
                "flex min-h-10 items-center gap-2 rounded-md px-2 text-left text-xs transition-colors duration-150 lg:w-full",
                collapsed ? "min-w-8 justify-center" : "min-w-0 flex-1 lg:min-w-28",
                active ? "bg-elevated text-fg shadow-[var(--shadow-border)]" : "text-muted hover:text-fg",
              )}
            >
              <span className="font-mono text-xs text-subtle">{item.kicker}</span>
              {!collapsed ? (
                <>
                  <span className="flex-1">{item.label}</span>
                  <StatusLight status={tri(lights[item.id])} />
                </>
              ) : (
                <StatusLight status={tri(lights[item.id])} />
              )}
            </button>
          );
        })}
      </nav>

      {!collapsed ? (
        <div className="mt-auto hidden px-2 pb-3 lg:block">
          <button
            type="button"
            data-action="auto-test"
            onClick={onTest}
            className="min-h-10 w-full rounded-md bg-elevated px-2 text-left text-xs text-muted shadow-[var(--shadow-border)] hover:text-fg"
          >
            全日曆測 · 三色刷新
          </button>
        </div>
      ) : null}
    </aside>
  );
}

import { Badge } from "@/components/ui/badge";
import { StatusLight } from "@/components/status-light";
import { aliasOf } from "@/lib/via/inventory";
import type { EngineRec } from "@/lib/via/types";

const KIND_ORDER = ["VIA", "VRN", "VDF", "NLP", "ACCEL", "NET", "GOV", "ENG"];

export function groupEngines(engines: EngineRec[]) {
  const groups = new Map<string, EngineRec[]>();
  for (const e of engines) {
    const k = KIND_ORDER.includes(e.kind) ? e.kind : "ENG";
    const list = groups.get(k) ?? [];
    list.push(e);
    groups.set(k, list);
  }
  return KIND_ORDER.filter((k) => groups.has(k)).map((k) => ({ kind: k, rows: groups.get(k) ?? [] }));
}

export function EngineRoster({
  engines,
  title = "總管引擎",
  liveOnly = true,
}: {
  engines: EngineRec[];
  title?: string;
  liveOnly?: boolean;
}) {
  const visible = liveOnly ? engines.filter((e) => !aliasOf(e.id)) : engines;
  const groups = groupEngines(visible);
  const ok = visible.filter((e) => e.status === "ok").length;
  const warn = visible.filter((e) => e.status === "warn").length;
  const bad = visible.filter((e) => e.status === "bad").length;
  const aliases = engines.filter((e) => aliasOf(e.id)).length;

  return (
    <aside className="flex min-h-0 flex-col rounded-lg bg-surface shadow-[var(--shadow-border)]">
      <div className="border-b border-border px-3 py-3">
        <p className="text-xs font-medium uppercase tracking-wide text-subtle">{title}</p>
        <p className="mt-1 font-mono text-xs tabular-nums text-muted">
          活路 {visible.length} · 綠 {ok} · 黃 {warn} · 紅 {bad}
        </p>
        <p className="mt-0.5 font-mono text-xs text-subtle">ALIAS {aliases} · 工具保留</p>
      </div>
      <div className="max-h-[70vh] space-y-3 overflow-auto px-2 py-2">
        {groups.map((g) => (
          <div key={g.kind}>
            <div className="mb-1 flex items-center justify-between px-1">
              <Badge tone="mute">{g.kind}</Badge>
              <span className="font-mono text-xs tabular-nums text-subtle">{g.rows.length}</span>
            </div>
            <ul className="space-y-0.5">
              {g.rows.map((e) => {
                const win = aliasOf(e.id);
                return (
                  <li key={e.id} className="flex items-center gap-2 rounded-sm px-1.5 py-1">
                    <StatusLight status={win ? "idle" : e.status} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium">{e.name}</p>
                      <p className="truncate font-mono text-xs text-subtle">{win ? `ALIAS → ${win}` : e.id}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </aside>
  );
}
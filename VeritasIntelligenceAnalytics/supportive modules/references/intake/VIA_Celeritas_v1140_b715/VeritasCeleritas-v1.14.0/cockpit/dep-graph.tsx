import { useMemo, useState } from "react";
import { GitBranch, Share2, Waypoints } from "lucide-react";
import {
  blastRadius,
  coverageOf,
  DEP_EDGES,
  DEP_NODES,
  domainStates,
  edgesFrom,
  edgesTo,
  KIND_LABEL,
  LAYER_LABELS,
  STATE_LABEL,
  type DepEdge,
  type DepNode,
  type DomainState,
  type EdgeKind,
} from "@/lib/deps";
import { cn } from "@/lib/utils";

const KIND_CODE: Record<EdgeKind, string> = {
  need: "n",
  accel: "a",
  feed: "d",
  fallback: "b",
};

const KIND_DASH: Record<EdgeKind, string> = {
  need: "none",
  accel: "6 4",
  feed: "2 4",
  fallback: "1 3",
};

function nodeById(id: string): DepNode {
  return DEP_NODES.find((n) => n.id === id)!;
}

function pathFor(edge: DepEdge): string {
  const a = nodeById(edge.from);
  const b = nodeById(edge.to);
  const x1 = a.x - 64;
  const y1 = a.y;
  const x2 = b.x + 64;
  const y2 = b.y;
  const mx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
}

export function DepGraph() {
  const [sel, setSel] = useState<string | null>("via_fin");
  const states = useMemo(() => domainStates(), []);
  const counts = useMemo(() => {
    const c = { live: 0, partial: 0, degraded: 0, blocked: 0, empty: 0 };
    for (const n of DEP_NODES) c[states[n.id]] += 1;
    return c;
  }, [states]);

  const outbound = sel ? edgesFrom(sel) : [];
  const inbound = sel ? edgesTo(sel) : [];
  const blast = sel ? blastRadius(sel) : [];
  const selected = sel ? nodeById(sel) : null;
  const cov = sel ? coverageOf(sel) : null;

  const related = new Set<string>();
  if (sel) {
    related.add(sel);
    for (const e of DEP_EDGES) {
      if (e.from === sel || e.to === sel) {
        related.add(e.from);
        related.add(e.to);
      }
    }
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">DEPENDENCY GRAPH</p>
            <h2 className="mt-1 text-lg font-medium tracking-display">VIA 域依賴關係</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              箭頭指向被依賴的上游。硬依賴決定能否開全速，加速與資料流可缺；後備接到 CPython 標準庫。
            </p>
            {selected && cov ? (
              <p className="mt-3 font-mono text-xs text-accent">
                {selected.id} · {STATE_LABEL[states[selected.id]]} · {cov.installed}/{cov.total} · 衝擊 {blast.length} 域
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            {(
              [
                ["blocked", counts.blocked, "阻塞"],
                ["degraded", counts.degraded, "降級"],
                ["partial", counts.partial, "部分"],
                ["empty", counts.empty, "未裝"],
                ["live", counts.live, "完整"],
              ] as const
            ).map(([k, n, label]) => (
              <div
                key={k}
                className="rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2"
              >
                <p className="font-mono text-[10px] tracking-widest text-muted">{label}</p>
                <p
                  className={cn(
                    "font-mono text-lg tabular-nums",
                    k === "blocked" && "text-danger",
                    k === "degraded" && "text-warn",
                    k === "partial" && "text-accent",
                    k === "live" && "text-ok",
                  )}
                >
                  {n}
                </p>
              </div>
            ))}
          </div>
        </div>

        <ul className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
          <li className="flex items-center gap-2">
            <span className="inline-block w-6 border-t border-fg" />硬依賴
          </li>
          <li className="flex items-center gap-2">
            <span className="inline-block w-6 border-t border-dashed border-fg" />加速
          </li>
          <li className="flex items-center gap-2">
            <span className="inline-block w-6 border-t border-dotted border-fg" />資料流
          </li>
          <li className="flex items-center gap-2 text-subtle">
            <span className="inline-block w-6 border-t border-dotted border-subtle" />後備
          </li>
        </ul>
      </section>

      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-3 sm:p-5">
        <div className="hidden overflow-x-auto md:block">
          <svg
            viewBox="0 0 1100 470"
            role="img"
            aria-label="VIA 域依賴圖"
            className="h-auto w-full min-w-[880px]"
          >
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 8 8"
                refX="7"
                refY="4"
                markerWidth="7"
                markerHeight="7"
                orient="auto"
              >
                <path d="M 0 0 L 8 4 L 0 8 z" fill="var(--color-accent)" />
              </marker>
              <marker
                id="arrow-muted"
                viewBox="0 0 8 8"
                refX="7"
                refY="4"
                markerWidth="7"
                markerHeight="7"
                orient="auto"
              >
                <path d="M 0 0 L 8 4 L 0 8 z" fill="var(--color-subtle)" />
              </marker>
            </defs>
            {[
              [70, "後備"],
              [230, "執行期"],
              [410, "數值"],
              [590, "載荷"],
              [780, "領域"],
              [960, "編排"],
            ].map(([x, label]) => (
              <text
                key={String(label)}
                x={x as number}
                y={18}
                textAnchor="middle"
                fill="var(--color-subtle)"
                fontSize="10"
                fontFamily="var(--font-mono)"
                letterSpacing="0.16em"
              >
                {label}
              </text>
            ))}
            {DEP_EDGES.map((e) => {
              const on = !sel || e.from === sel || e.to === sel;
              return (
                <path
                  key={`${e.from}-${e.to}-${e.kind}-${e.via}`}
                  d={pathFor(e)}
                  fill="none"
                  stroke={on ? "var(--color-accent)" : "var(--color-border)"}
                  strokeWidth={on && e.kind === "need" ? 1.6 : 1}
                  strokeDasharray={KIND_DASH[e.kind]}
                  opacity={on ? 0.9 : 0.28}
                  markerEnd={on ? "url(#arrow)" : "url(#arrow-muted)"}
                />
              );
            })}
            {DEP_NODES.map((n) => (
              <NodeMark
                key={n.id}
                node={n}
                state={states[n.id]}
                selected={sel === n.id}
                dim={!!sel && !related.has(n.id)}
                onSelect={() => setSel(sel === n.id ? null : n.id)}
              />
            ))}
          </svg>
        </div>

        <div className="grid gap-2 md:hidden">
          {LAYER_LABELS.map((label, layer) => (
            <div key={label}>
              <p className="mb-1 font-mono text-[10px] tracking-widest text-subtle">{label}</p>
              <div className="grid grid-cols-1 gap-2">
                {DEP_NODES.filter((n) => n.layer === layer).map((n) => (
                  <button
                    key={n.id}
                    type="button"
                    onClick={() => setSel(sel === n.id ? null : n.id)}
                    className={cn(
                      "flex min-h-11 items-center justify-between rounded-[var(--radius-md)] border px-3 py-2 text-left",
                      sel === n.id ? "border-accent bg-bg" : "border-border bg-bg",
                    )}
                  >
                    <span>
                      <span className="block font-mono text-xs text-accent">{n.id}</span>
                      <span className="text-sm">{n.title}</span>
                    </span>
                    <StateChip state={states[n.id]} />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {selected && cov ? (
        <section className="grid gap-4 lg:grid-cols-5">
          <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5 lg:col-span-2">
            <div className="mb-3 flex items-center gap-2 text-accent">
              <Waypoints className="size-4" strokeWidth={1.75} />
              <h3 className="text-sm font-medium tracking-wide">{selected.id}</h3>
            </div>
            <p className="text-sm text-muted">{selected.title}</p>
            <dl className="mt-3 grid grid-cols-3 gap-2">
              <MiniStat label="狀態" value={STATE_LABEL[states[selected.id]]} />
              <MiniStat label="覆蓋" value={`${cov.pct}%`} />
              <MiniStat label="已裝" value={`${cov.installed}/${cov.total}`} />
            </dl>
            <p className="mt-3 text-xs text-muted">
              下游衝擊 {blast.length} 域
              {blast.length ? `：${blast.join(" · ")}` : "（末端）"}
            </p>
          </article>

          <article className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5 lg:col-span-3">
            <div className="mb-3 flex items-center gap-2 text-accent">
              <Share2 className="size-4" strokeWidth={1.75} />
              <h3 className="text-sm font-medium tracking-wide">上游 / 下游</h3>
            </div>
            <EdgeList title="此域依賴" rows={outbound} dir="to" />
            <EdgeList title="依賴此域" rows={inbound} dir="from" />
            {outbound.length === 0 && inbound.length === 0 ? (
              <p className="text-sm text-muted">無連邊。</p>
            ) : null}
          </article>
        </section>
      ) : null}

      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="mb-3 flex items-center gap-2 text-accent">
          <GitBranch className="size-4" strokeWidth={1.75} />
          <h3 className="text-sm font-medium tracking-wide">鄰接矩陣 · 列依賴行</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse text-center text-[11px]">
            <thead>
              <tr>
                <th className="sticky left-0 bg-bg-elevated py-2 pr-2 text-left font-mono font-medium text-muted">
                  FROM
                </th>
                {DEP_NODES.map((n) => (
                  <th
                    key={n.id}
                    className="px-1 py-2 font-mono font-medium text-subtle"
                    title={n.id}
                  >
                    {n.id.replace("via_", "")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DEP_NODES.map((row) => (
                <tr key={row.id} className="border-t border-border">
                  <th className="sticky left-0 bg-bg-elevated py-1.5 pr-2 text-left font-mono font-medium text-accent">
                    <button type="button" onClick={() => setSel(row.id)} className="min-h-11 text-left">
                      {row.id}
                    </button>
                  </th>
                  {DEP_NODES.map((col) => {
                    const hits = DEP_EDGES.filter((e) => e.from === row.id && e.to === col.id);
                    const active = sel === row.id || sel === col.id;
                    return (
                      <td key={col.id} className="px-1 py-1">
                        {hits.length ? (
                          <span
                            className={cn(
                              "inline-block rounded-sm px-1 font-mono",
                              active ? "bg-accent text-accent-fg" : "bg-bg-subtle text-muted",
                            )}
                            title={hits.map((h) => `${KIND_LABEL[h.kind]} · ${h.via}`).join(" / ")}
                          >
                            {hits.map((h) => KIND_CODE[h.kind]).join("")}
                          </span>
                        ) : (
                          <span className="text-subtle">·</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-subtle">n 硬依賴 · a 加速 · d 資料流 · b 後備</p>
      </section>
    </div>
  );
}

function NodeMark({
  node,
  state,
  selected,
  dim,
  onSelect,
}: {
  node: DepNode;
  state: DomainState;
  selected: boolean;
  dim: boolean;
  onSelect: () => void;
}) {
  const stroke =
    state === "blocked"
      ? "var(--color-danger)"
      : state === "degraded" || state === "empty"
        ? "var(--color-warn)"
        : state === "partial"
          ? "var(--color-accent)"
          : "var(--color-ok)";
  return (
    <g
      transform={`translate(${node.x}, ${node.y})`}
      opacity={dim ? 0.28 : 1}
      className="cursor-pointer"
      onClick={onSelect}
    >
      <rect
        x={-64}
        y={-22}
        width={128}
        height={44}
        rx={8}
        fill={selected ? "var(--color-bg-subtle)" : "var(--color-bg)"}
        stroke={selected ? "var(--color-accent)" : stroke}
        strokeWidth={selected ? 1.8 : 1}
      />
      <text
        x={0}
        y={-3}
        textAnchor="middle"
        fill="var(--color-accent)"
        fontSize="9"
        fontFamily="var(--font-mono)"
      >
        {node.id}
      </text>
      <text
        x={0}
        y={12}
        textAnchor="middle"
        fill="var(--color-fg)"
        fontSize="10"
        fontFamily="var(--font-sans)"
      >
        {node.title}
      </text>
    </g>
  );
}

function StateChip({ state }: { state: DomainState }) {
  return (
    <span
      className={cn(
        "rounded-full px-2 py-1 font-mono text-[10px] tracking-widest",
        state === "live" && "text-ok",
        state === "partial" && "text-accent",
        state === "degraded" && "text-warn",
        state === "blocked" && "text-danger",
        state === "empty" && "text-muted",
      )}
    >
      {STATE_LABEL[state]}
    </span>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-bg px-2 py-2">
      <dt className="font-mono text-[10px] tracking-widest text-muted">{label}</dt>
      <dd className="mt-0.5 font-mono text-sm">{value}</dd>
    </div>
  );
}

function EdgeList({
  title,
  rows,
  dir,
}: {
  title: string;
  rows: DepEdge[];
  dir: "from" | "to";
}) {
  if (!rows.length) return null;
  return (
    <div className="mb-3 last:mb-0">
      <p className="mb-1 font-mono text-[10px] tracking-widest text-subtle">{title}</p>
      <ul className="space-y-1">
        {rows.map((e) => (
          <li
            key={`${e.from}-${e.to}-${e.kind}-${e.via}`}
            className="rounded-[var(--radius-md)] bg-bg px-3 py-2 text-sm"
          >
            <p className="font-mono text-xs text-accent">
              {dir === "to" ? e.to : e.from}
              <span className="ml-2 text-subtle">{KIND_LABEL[e.kind]}</span>
            </p>
            <p className="text-xs text-muted">
              {e.via} · {e.note}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

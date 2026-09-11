import type { ReactNode } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export function Matrix({
  columns,
  rows,
  empty,
  align,
}: {
  columns: string[];
  rows: Array<Array<ReactNode>>;
  empty?: string;
  align?: Array<"left" | "right">;
}) {
  return (
    <div className="overflow-x-auto rounded-md shadow-[var(--shadow-border)]">
      <table className="w-full border-collapse text-left text-xs">
        <thead className="sticky top-0 bg-elevated text-muted">
          <tr>
            {columns.map((c, i) => (
              <th
                key={c}
                className={cn(
                  "px-2.5 py-1.5 font-medium tracking-wide",
                  align?.[i] === "right" && "text-right font-mono tabular-nums",
                )}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-8 text-center text-subtle">
                {empty ?? "無資料"}
              </td>
            </tr>
          ) : (
            rows.map((cells, i) => (
              <tr key={i} className="border-t border-border even:bg-inset/40">
                {cells.map((cell, j) => (
                  <td
                    key={j}
                    className={cn(
                      "max-w-64 break-words px-2.5 py-1.5 align-middle text-fg",
                      align?.[j] === "right" && "text-right font-mono tabular-nums",
                    )}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export function CategoryBlock({
  title,
  count,
  open,
  onToggle,
  children,
}: {
  title: string;
  count: number;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <section className="rounded-lg bg-surface p-2 shadow-[var(--shadow-border)]">
      <button
        type="button"
        onClick={onToggle}
        className={cn(
          "flex min-h-11 w-full items-center justify-between rounded-md px-3 text-sm font-medium",
        )}
      >
        <span className="flex items-center gap-2">
          {open ? <ChevronDown className="size-4 text-muted" /> : <ChevronRight className="size-4 text-muted" />}
          <span data-cat={title}>{title}</span>
        </span>
        <span className="font-mono text-xs tabular-nums text-muted">{count}</span>
      </button>
      {open ? <div className="mt-1">{children}</div> : null}
    </section>
  );
}

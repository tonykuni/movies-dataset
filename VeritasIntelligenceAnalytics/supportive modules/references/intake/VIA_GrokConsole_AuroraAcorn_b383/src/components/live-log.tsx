import { useEffect, useRef } from "react";
import type { LogLine } from "@/lib/via/types";
import { cn } from "@/lib/utils";

const tone: Record<LogLine["level"], string> = {
  INFO: "text-log-dim",
  OK: "text-log-ok",
  WARN: "text-log-warn",
  FAIL: "text-log-bad",
  GATE: "text-log-gate",
};

export function LiveLog({ lines, compact = false }: { lines: LogLine[]; compact?: boolean }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [lines.length]);

  return (
    <div
      className={cn(
        "overflow-auto rounded-md bg-log p-2 font-mono text-xs leading-snug text-log-fg shadow-[var(--shadow-border)]",
        compact ? "h-full min-h-52 max-h-80" : "h-48",
      )}
    >
      {lines.length === 0 ? <p className="text-log-dim">LIVE LOG 待命</p> : null}
      {lines.map((l) => (
        <div key={l.id} className="border-b border-white/5 py-0.5 last:border-0">
          <div className="flex flex-wrap gap-x-2 gap-y-0">
            <span className="tabular-nums text-log-dim">{l.t}</span>
            <span className={cn("font-medium", tone[l.level])}>{l.level}</span>
            <span className="text-log-dim">{l.step}</span>
          </div>
          <p className="break-words text-log-fg">{l.msg}</p>
          {l.detail ? <p className="break-words text-log-dim">{l.detail}</p> : null}
        </div>
      ))}
      <div ref={end} />
    </div>
  );
}

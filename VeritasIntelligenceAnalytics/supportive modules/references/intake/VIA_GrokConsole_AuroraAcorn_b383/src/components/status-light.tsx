import { cn } from "@/lib/utils";
import { lamp } from "@/lib/via/coordinate";
import type { Light } from "@/lib/via/types";

const LAMP_CLASS: Record<ReturnType<typeof lamp>, string> = {
  ok: "lamp lamp-ok",
  warn: "lamp lamp-warn",
  bad: "lamp lamp-bad",
  pending: "lamp lamp-grey",
};

const LABELS: Record<Light, string> = {
  ok: "綠",
  warn: "黃",
  bad: "紅",
  idle: "灰",
  pending: "灰",
  run: "黃",
};

export function StatusLight({ status, label }: { status: Light; label?: string }) {
  const zh = LABELS[status] ?? "灰";
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={cn(LAMP_CLASS[lamp(status)])} aria-hidden="true" />
      <span className="font-mono text-[10px] leading-none text-muted">{label ?? zh}</span>
    </span>
  );
}

export function LightLegend() {
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
      <StatusLight status="ok" label="綠 通過" />
      <StatusLight status="warn" label="黃 待協調" />
      <StatusLight status="bad" label="紅 失敗" />
      <StatusLight status="pending" label="灰 待辦" />
    </div>
  );
}

export function lightZh(s: Light) {
  return LABELS[s] ?? "灰";
}
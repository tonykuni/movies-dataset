import { EngineRoster } from "@/components/engine-roster";
import { Badge } from "@/components/ui/badge";
import { StatusLight } from "@/components/status-light";
import { GOV_TOOLS } from "@/lib/via/catalog";
import { handoverPanorama } from "@/lib/via/autotest";
import { cashRows } from "@/lib/via/active-etf";
import { tri } from "@/lib/via/coordinate";
import type { EngineRec } from "@/lib/via/types";

const SHORT = [
  { id: "via-entry", zh: "唯一入口：隔離→PATH" },
  { id: "via-path", zh: "venv 在前 · iso 不進" },
  { id: "via-aea", zh: "主動 ETF 29 檔看板" },
  { id: "via-rev", zh: "台股月營收 U · ENG075" },
  { id: "via-gh", zh: "foreach add · 禁止強制推送" },
  { id: "via-brk", zh: "券商 29 · 無陸券 · 摩根已刪" },
];

export function RightRail({
  engines,
  day,
}: {
  engines: EngineRec[];
  day: string;
}) {
  const top = cashRows()[0];
  const hands = handoverPanorama(day);
  return (
    <div data-right-rail="1" className="w-full space-y-3 lg:sticky lg:top-2 lg:w-60 lg:self-start">
      <div className="space-y-2 rounded-lg bg-surface p-3 shadow-[var(--shadow-border)]">
        <p className="text-xs font-medium uppercase tracking-wide text-subtle">右側板 · 不擋左</p>
        <p className="text-pretty text-xs text-muted">短指令中文 · 小字換行 · Git 單檔用 foreach</p>
        <ul className="space-y-1">
          {SHORT.map((s) => (
            <li key={s.id} className="min-w-0">
              <p className="truncate font-mono text-xs">{s.id}</p>
              <p className="text-pretty text-xs text-subtle">{s.zh}</p>
            </li>
          ))}
        </ul>
      </div>
      <div className="space-y-2 rounded-lg bg-surface p-3 shadow-[var(--shadow-border)]">
        <p className="text-xs font-medium uppercase tracking-wide text-subtle">AEA · 29 檔</p>
        {top ? (
          <p className="text-pretty text-xs text-muted">
            首檔 {top.ticker} {top.name} · {(top.aum / 1e8).toFixed(0)} 億 · 流 CACHE 無 Δ單位
          </p>
        ) : null}
        <Badge tone="ok">COPY_ONLY · LIVE 關</Badge>
      </div>
      <div className="space-y-2 rounded-lg bg-surface p-3 shadow-[var(--shadow-border)]">
        <p className="text-xs font-medium uppercase tracking-wide text-subtle">U · 月營收</p>
        <p className="text-pretty text-xs text-muted">VIA_U → VDF_ENG075 · MOPS 月檔 sii/otc · 2023-01 起 · 不 ticker 迴圈</p>
        <Badge tone="ok">CACHE · LIVE 關</Badge>
      </div>
      <div className="space-y-2 rounded-lg bg-surface p-3 shadow-[var(--shadow-border)]">
        <p className="text-xs font-medium uppercase tracking-wide text-subtle">治理工具</p>
        <ul className="space-y-1">
          {GOV_TOOLS.map((t) => (
            <li key={t.id} className="flex items-start gap-2">
              <StatusLight status={t.status} />
              <div className="min-w-0">
                <p className="text-pretty text-xs">{t.name}</p>
                <p className="text-pretty font-mono text-xs text-subtle">{t.id}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
      <div className="space-y-2 rounded-lg bg-surface p-3 shadow-[var(--shadow-border)]">
        <p className="text-xs font-medium uppercase tracking-wide text-subtle">隔日 · {day}</p>
        <ul className="space-y-1">
          {hands.map((r) => (
            <li key={r.id} className="flex items-start gap-2">
              <StatusLight status={tri(r.light)} />
              <div className="min-w-0">
                <p className="text-xs">{r.system}</p>
                <p className="text-pretty text-xs text-subtle">{r.tonight}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
      <EngineRoster engines={engines} title="活路引擎" />
    </div>
  );
}

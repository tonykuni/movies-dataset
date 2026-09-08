import { useState } from "react";
import { Activity, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { ConsoleDeck } from "@/components/console-deck";
import { EngineDeck } from "@/components/engine-deck";
import { IntakeDeck } from "@/components/intake-deck";
import { LeftEngine } from "@/components/left-engine";
import { VarDeck } from "@/components/var-deck";
import { MotherDeck } from "@/components/mother-deck";
import { VdfDeck } from "@/components/vdf-deck";
import { Button } from "@/components/ui/button";
import { StatusLight } from "@/components/status-light";
import { lamp } from "@/lib/via/coordinate";
import { PS20 } from "@/lib/via/accel";
import { psrOverall } from "@/lib/via/psrepair-rounds";
import { useVia } from "@/lib/via/store";
import type { Deck, Light } from "@/lib/via/types";

const NAV: Array<{ id: Deck; label: string; kicker: string }> = [
  { id: "console", label: "總管", kicker: "00" },
  { id: "vdf", label: "VDF", kicker: "01" },
  { id: "vrn", label: "VRN", kicker: "02" },
  { id: "engine", label: "引擎", kicker: "03" },
  { id: "var", label: "VAR", kicker: "04" },
  { id: "mother", label: "母倉", kicker: "05" },
];

function worst(rows: { light: Light }[], fallback: Light): Light {
  if (rows.some((r) => r.light === "bad")) return "bad";
  if (rows.some((r) => r.light === "run")) return "run";
  if (rows.some((r) => r.light === "warn")) return "warn";
  if (rows.some((r) => r.light === "pending" || r.light === "idle")) return "pending";
  if (rows.length && rows.every((r) => r.light === "ok")) return "ok";
  return fallback;
}

export function Shell() {
  const deck = useVia((s) => s.deck);
  const setDeck = useVia((s) => s.setDeck);
  const activated = useVia((s) => s.activated);
  const vdfBusy = useVia((s) => s.vdfBusy);
  const intakeBusy = useVia((s) => s.intakeBusy);
  const engineBusy = useVia((s) => s.engineBusy);
  const auditBusy = useVia((s) => s.auditBusy);
  const autoRows = useVia((s) => s.autoRows);
  const runAutoTest = useVia((s) => s.runAutoTest);
  const [leftOpen, setLeftOpen] = useState(true);

  const vdfLight: Light = vdfBusy ? "run" : worst(autoRows.filter((r) => r.system === "VDF"), activated.vdf ? "ok" : "warn");
  const vrnLight: Light = intakeBusy ? "run" : worst(autoRows.filter((r) => r.system === "VRN"), activated.vrn ? "ok" : "warn");
  const engLight: Light = engineBusy ? "run" : activated.engine ? "ok" : "warn";
  const varLight: Light = auditBusy ? "run" : activated.var ? "ok" : "warn";
  const govLight: Light = worst(autoRows.filter((r) => r.system === "VIA" || r.system === "GOV"), "warn");
  const motherLight: Light = psrOverall();   // 母倉成果台:PS 三輪最壞燈(R3a 5 個不可解析腳本=紅)
  const lights: Record<Deck, Light> = { console: govLight, vdf: vdfLight, vrn: vrnLight, engine: engLight, var: varLight, mother: motherLight };
  const live = activated.vdf && activated.vrn && activated.engine && activated.var;

  const lampRows = autoRows.map((r) => ({ light: lamp(r.light) }));
  const nOk = lampRows.filter((r) => r.light === "ok").length;
  const nWarn = lampRows.filter((r) => r.light === "warn").length;
  const nBad = lampRows.filter((r) => r.light === "bad").length;
  const nGrey = lampRows.filter((r) => r.light === "pending").length;
  const engineOk = autoRows.filter((r) => r.system === "ENG" || r.system === "VDF" || r.system === "VRN").filter((r) => lamp(r.light) === "ok").length;
  const engineBad = autoRows.filter((r) => lamp(r.light) === "bad").length;
  const engineWarn = autoRows.filter((r) => lamp(r.light) === "warn").length;

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-bg text-fg" data-dashboard="1">
      <header
        data-dash="header"
        className="z-40 flex shrink-0 items-center justify-between gap-3 border-b border-border bg-surface px-3 py-2"
      >
        <div className="flex min-w-0 items-center gap-2">
          <button
            type="button"
            data-action="toggle-left"
            aria-label={leftOpen ? "折疊左欄" : "展開左欄"}
            onClick={() => setLeftOpen((v) => !v)}
            className="inline-flex min-h-10 min-w-10 items-center justify-center rounded-md bg-elevated text-muted hover:text-fg lg:hidden"
          >
            {leftOpen ? <PanelLeftClose className="size-4" /> : <PanelLeftOpen className="size-4" />}
          </button>
          <Activity className="hidden size-4 shrink-0 text-accent sm:block" aria-hidden />
          <div className="min-w-0">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-subtle">VIA · dashboard</p>
            <h1 className="truncate text-sm font-semibold tracking-tight">Central Governance · 頭尾鎖定 · 左欄可折</h1>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="hidden items-center gap-1.5 font-mono text-xs text-subtle sm:flex">
            <StatusLight status="ok" /> {nOk}
            <StatusLight status="warn" /> {nWarn}
            <StatusLight status="bad" /> {nBad}
            <StatusLight status="pending" /> {nGrey}
          </span>
          <span className="hidden font-mono text-xs text-subtle md:block">
            PS-{String(PS20.length).padStart(2, "0")} · 不卡斷 · LIVE {live ? "開" : "關"}
          </span>
          <Button size="sm" variant="outline" data-action="auto-test-header" onClick={() => runAutoTest()}>
            全日曆測
          </Button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
        <LeftEngine
          nav={NAV}
          deck={deck}
          lights={lights}
          counts={{ ok: nOk, warn: nWarn, bad: nBad, grey: nGrey }}
          engineOk={engineOk}
          engineBad={engineBad}
          engineWarn={engineWarn}
          activated={live}
          collapsed={!leftOpen}
          onToggle={() => setLeftOpen((v) => !v)}
          onNav={setDeck}
          onTest={() => runAutoTest()}
        />
        <main className="min-w-0 flex-1 overflow-y-auto px-3 py-4 sm:px-5 lg:px-7">
          {deck === "console" ? <ConsoleDeck /> : null}
          {deck === "vdf" ? <VdfDeck /> : null}
          {deck === "vrn" ? <IntakeDeck /> : null}
          {deck === "engine" ? <EngineDeck /> : null}
          {deck === "var" ? <VarDeck /> : null}
          {deck === "mother" ? <MotherDeck /> : null}
        </main>
      </div>

      <footer
        data-dash="footer"
        className="z-40 flex shrink-0 flex-col gap-1 border-t border-border bg-surface px-3 py-1.5 font-mono text-xs text-subtle"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span>底欄鎖定 · 綠 {nOk} 黃 {nWarn} 紅 {nBad} 灰 {nGrey} · CACHE · LIVE 關</span>
          <span className="hidden sm:inline">ACC-PS20 · 非阻塞 DAG</span>
        </div>
        <div className="flex flex-wrap gap-1" data-ps20="1">
          {PS20.map((p) => (
            <span key={p.id} className="rounded-sm bg-inset px-1.5 py-0.5 text-subtle" title={p.note}>
              {p.id.replace("PS-", "")}
            </span>
          ))}
        </div>
      </footer>
    </div>
  );
}

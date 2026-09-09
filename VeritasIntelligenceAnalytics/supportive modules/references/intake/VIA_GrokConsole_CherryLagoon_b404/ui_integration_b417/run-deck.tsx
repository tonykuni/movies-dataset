import { useRef, useState } from "react";
import { PlayCircle, SlidersHorizontal, Table2, Upload } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Matrix } from "@/components/matrix";
import { LightLegend, StatusLight } from "@/components/status-light";
import {
  familyLight,
  overallLight,
  readiness,
  resultRows,
  verdictText,
  type RunCounts,
} from "@/lib/via/run-console";
import { useVia } from "@/lib/via/store";
import type { Light } from "@/lib/via/types";

/**
 * 整合台(批417):左輸入、右結果,一鍵把 VDF → ETF → VRN 跑成一輪。
 * Zero-Hydra:引擎一支都不新造——跑的是既有 runVdf / runIntake,
 * 這一頁只做「輸入集中」與「結果彙整」,細節仍在各自分頁。
 */

function Panel({
  icon,
  title,
  light,
  sub,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  light?: Light;
  sub?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg bg-surface p-3 shadow-[var(--shadow-border)]">
      <header className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="text-muted" aria-hidden>
            {icon}
          </span>
          <h2 className="truncate text-sm font-semibold tracking-tight">{title}</h2>
          {light ? <StatusLight status={light} /> : null}
        </div>
        {sub ? <p className="font-mono text-[11px] text-subtle">{sub}</p> : null}
      </header>
      {children}
    </section>
  );
}

export function RunDeck() {
  const startYear = useVia((s) => s.startYear);
  const setStartYear = useVia((s) => s.setStartYear);
  const confirmNet = useVia((s) => s.confirmNet);
  const setConfirmNet = useVia((s) => s.setConfirmNet);
  const fredKey = useVia((s) => s.fredKey);
  const setFredKey = useVia((s) => s.setFredKey);

  const aetfFundPicks = useVia((s) => s.aetfFundPicks);
  const aetfPicked = useVia((s) => s.aetfPicked);
  const toggleAetfPick = useVia((s) => s.toggleAetfPick);
  const aetfPickAll = useVia((s) => s.aetfPickAll);
  const aetfPickNone = useVia((s) => s.aetfPickNone);
  const aetfRows = useVia((s) => s.aetfRows);

  const files = useVia((s) => s.files);
  const addDropped = useVia((s) => s.addDropped);
  const skipAllDups = useVia((s) => s.skipAllDups);
  const setSkipAllDups = useVia((s) => s.setSkipAllDups);

  const fredRows = useVia((s) => s.fredRows);
  const vdfLaneResults = useVia((s) => s.vdfLaneResults);
  const basics = useVia((s) => s.basics);
  const summaries = useVia((s) => s.summaries);
  const finances = useVia((s) => s.finances);

  const vdfBusy = useVia((s) => s.vdfBusy);
  const vdfProgress = useVia((s) => s.vdfProgress);
  const intakeBusy = useVia((s) => s.intakeBusy);
  const intakeProgress = useVia((s) => s.intakeProgress);
  const runVdf = useVia((s) => s.runVdf);
  const runIntake = useVia((s) => s.runIntake);
  const setDeck = useVia((s) => s.setDeck);

  const fileRef = useRef<HTMLInputElement>(null);
  const [ran, setRan] = useState(false);

  const input = { startYear, confirmNet, fredKey, etfPicked: aetfPicked, vrnFiles: files.length };
  const ready = readiness(input);
  const counts: RunCounts = {
    fredRows: fredRows.length,
    laneResults: vdfLaneResults.length,
    laneLive: vdfLaneResults.filter((l) => l.result === "LIVE" || l.result === "CACHE" || l.result === "LOCAL").length,
    etfRows: aetfRows.length,
    etfPicked: aetfPicked.length,
    vrnFiles: files.length,
    vrnBasics: basics.length,
    vrnSummaries: summaries.length,
    vrnFinances: finances.length,
    vrnBad: files.filter((f) => f.status === "bad").length,
  };
  const rows = resultRows(counts, { vdf: vdfBusy, vrn: intakeBusy });
  const overall = overallLight(rows);
  const busy = vdfBusy || intakeBusy;
  const willRunVrn = files.length > 0;

  async function runAll() {
    setRan(true);
    await runVdf();
    if (willRunVrn) await runIntake();
  }

  return (
    <div className="flex flex-col gap-3" data-deck="run">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-subtle">integrated run · input × result</p>
          <h1 className="text-sm font-semibold tracking-tight">整合台 · 一頁輸入,一頁結果(VDF → ETF → VRN)</h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusLight status={overall} label={verdictText(rows)} />
          <LightLegend />
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.15fr)]">
        {/* ─── 左:輸入 ─────────────────────────────────────────── */}
        <div className="flex flex-col gap-3">
          <Panel icon={<SlidersHorizontal className="size-4" />} title="輸入 · 共用" sub={`起始 ${startYear}`}>
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-muted">起始年</span>
                <Input
                  type="number"
                  value={startYear}
                  min={1990}
                  max={2030}
                  data-input="start-year"
                  onChange={(e) => setStartYear(Number(e.target.value) || startYear)}
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[11px] text-muted">FRED API KEY(空=走離線列式湖)</span>
                <Input
                  value={fredKey}
                  placeholder="留空即零外呼"
                  data-input="fred-key"
                  onChange={(e) => setFredKey(e.target.value)}
                />
              </label>
            </div>
            <label className="mt-2 flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={confirmNet}
                data-input="net-gate"
                onChange={(e) => setConfirmNet(e.target.checked)}
              />
              <span>
                我確認開啟網路閘(<span className="font-mono">VIA_NET_CONSENT</span>)——
                <span className="text-subtle">不勾就是零外呼;本頁不會替你開任何同意閘</span>
              </span>
            </label>
          </Panel>

          <Panel
            icon={<Table2 className="size-4" />}
            title="輸入 · 主動 ETF"
            sub={`已挑 ${aetfPicked.length}/${aetfFundPicks.length}`}
          >
            <div className="mb-2 flex gap-2">
              <Button size="sm" variant="outline" onClick={aetfPickAll} data-action="etf-all">
                全選
              </Button>
              <Button size="sm" variant="outline" onClick={aetfPickNone} data-action="etf-none">
                全不選
              </Button>
            </div>
            <div className="max-h-44 overflow-y-auto rounded-md shadow-[var(--shadow-border)]">
              <table className="w-full border-collapse text-left text-xs">
                <tbody>
                  {aetfFundPicks.map((f) => (
                    <tr key={f.ticker} className="border-t border-[var(--line)] first:border-t-0">
                      <td className="px-2 py-1">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={aetfPicked.includes(f.ticker)}
                            onChange={() => toggleAetfPick(f.ticker)}
                          />
                          <span className="font-mono">{f.ticker}</span>
                          <span className="truncate text-muted">{f.name}</span>
                        </label>
                      </td>
                      <td className="px-2 py-1 text-right font-mono text-subtle">{f.issuer}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel
            icon={<Upload className="size-4" />}
            title="輸入 · VRN 研究報告"
            sub={`${files.length} 件`}
          >
            <div
              className="rounded-md border border-dashed border-[var(--line)] p-3 text-center text-xs text-muted"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const list = e.dataTransfer?.files;
                if (list) addDropped(Array.from(list));
              }}
            >
              把報告 PDF 拖到這裡,或
              <input
                ref={fileRef}
                type="file"
                multiple
                className="hidden"
                onChange={(e) => {
                  const list = e.target.files;
                  if (list) addDropped(Array.from(list));
                }}
              />
              <Button size="sm" variant="outline" className="mx-2" onClick={() => fileRef.current?.click()}>
                選擇檔案
              </Button>
            </div>
            <label className="mt-2 flex items-center gap-2 text-xs">
              <input type="checkbox" checked={skipAllDups} onChange={(e) => setSkipAllDups(e.target.checked)} />
              <span>重複件一律略過</span>
            </label>
            {files.length ? (
              <ul className="mt-2 max-h-28 overflow-y-auto text-[11px] text-muted">
                {files.slice(0, 12).map((f) => (
                  <li key={f.id} className="flex items-center justify-between gap-2 py-0.5">
                    <span className="truncate font-mono">{f.name}</span>
                    <StatusLight status={f.status} />
                  </li>
                ))}
              </ul>
            ) : null}
          </Panel>

          <Panel icon={<PlayCircle className="size-4" />} title="整備" sub={busy ? "跑動中" : "待跑"}>
            <Matrix
              columns={["族", "可跑", "說明"]}
              rows={ready.map((r) => [
                <span key="f" className="font-mono">{r.family}</span>,
                <StatusLight key="l" status={r.ready ? "ok" : "pending"} label={r.ready ? "可跑" : "缺輸入"} />,
                <span key="w" className="text-muted">{r.why}</span>,
              ])}
            />
            <Button className="mt-2 w-full" disabled={busy} data-action="run-all" onClick={() => void runAll()}>
              {busy ? "跑動中…" : willRunVrn ? "整合跑 · VDF → ETF → VRN" : "整合跑 · VDF → ETF(VRN 無檔跳過)"}
            </Button>
            {!willRunVrn ? (
              <p className="mt-1 text-[11px] text-subtle">
                VRN 沒有輸入就不會有結果——這一輪只跑 VDF 與 ETF,VRN 那三列維持灰的,不假綠。
              </p>
            ) : null}
          </Panel>
        </div>

        {/* ─── 右:結果 ─────────────────────────────────────────── */}
        <div className="flex flex-col gap-3">
          <Panel
            icon={<Table2 className="size-4" />}
            title="結果 · 三族整合矩陣"
            light={overall}
            sub={ran || counts.fredRows ? verdictText(rows) : "尚未跑"}
          >
            {busy ? (
              <div className="mb-2 grid gap-1">
                <Progress value={vdfProgress} />
                {willRunVrn ? <Progress value={intakeProgress} /> : null}
              </div>
            ) : null}
            <Matrix
              columns={["族", "指標", "值", "燈", "說明"]}
              align={["left", "left", "right", "left", "left"]}
              rows={rows.map((r) => [
                <Badge key="f" tone="mute">{r.family}</Badge>,
                <span key="k">{r.key}</span>,
                <span key="v" className="font-mono tabular-nums">{r.value}</span>,
                <StatusLight key="l" status={r.light} />,
                <span key="n" className="text-muted">{r.note}</span>,
              ])}
            />
            <div className="mt-2 flex flex-wrap gap-2">
              {(["VDF", "ETF", "VRN"] as const).map((f) => (
                <span key={f} className="inline-flex items-center gap-1.5 rounded-md bg-elevated px-2 py-1 text-[11px]">
                  <span className="font-mono">{f}</span>
                  <StatusLight status={familyLight(rows, f)} />
                </span>
              ))}
            </div>
          </Panel>

          <Panel icon={<Table2 className="size-4" />} title="結果 · 擷取車道(VDF)" sub={`${counts.laneLive}/${counts.laneResults} 有料`}>
            <Matrix
              columns={["車道", "引擎", "結果", "列", "說明"]}
              align={["left", "left", "left", "right", "left"]}
              empty="尚未跑——按左邊的整合跑"
              rows={vdfLaneResults.map((l) => [
                <span key="i" className="font-mono">{l.id}</span>,
                <span key="e" className="text-muted">{l.engine}</span>,
                <Badge key="r" tone={l.result === "DENIED" || l.result === "SKIP" ? "warn" : "ok"}>{l.result}</Badge>,
                <span key="n" className="font-mono tabular-nums">{l.rows}</span>,
                <span key="t" className="text-muted">{l.note}</span>,
              ])}
            />
          </Panel>

          <Panel icon={<Table2 className="size-4" />} title="結果 · 主動 ETF 檢核" sub={`${aetfRows.length} 列`}>
            <Matrix
              columns={["層", "指標", "值", "燈", "說明"]}
              empty="尚未跑——按左邊的整合跑"
              rows={aetfRows.slice(0, 12).map((r) => [
                <span key="l" className="font-mono">{r.layer}</span>,
                <span key="m">{r.metric}</span>,
                <span key="v" className="font-mono tabular-nums">{r.value}</span>,
                <StatusLight key="g" status={r.light} />,
                <span key="n" className="text-muted">{r.note}</span>,
              ])}
            />
          </Panel>

          <Panel icon={<Table2 className="size-4" />} title="結果 · VRN 報告" sub={`${basics.length} 件入庫`}>
            <Matrix
              columns={["檔名", "代號", "券商", "評等", "判定"]}
              empty={files.length ? "尚未跑——按左邊的整合跑" : "尚無報告檔:拖 PDF 進左欄"}
              rows={basics.slice(0, 10).map((b) => [
                <span key="f" className="truncate font-mono">{b.fileName}</span>,
                <span key="t" className="font-mono">{b.ticker || "—"}</span>,
                <span key="b" className="text-muted">{b.broker || "—"}</span>,
                <span key="r" className="text-muted">{b.rating || "—"}</span>,
                <StatusLight key="s" status={b.status} />,
              ])}
            />
          </Panel>

          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => setDeck("vdf")}>
              看 VDF 細節
            </Button>
            <Button size="sm" variant="outline" onClick={() => setDeck("vrn")}>
              看 VRN 細節
            </Button>
            <Button size="sm" variant="outline" onClick={() => setDeck("mother")}>
              母倉現況
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

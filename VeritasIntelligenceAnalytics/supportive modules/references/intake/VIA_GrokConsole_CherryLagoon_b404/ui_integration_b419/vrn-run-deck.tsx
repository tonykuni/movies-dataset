import { AlertTriangle, CalendarClock, FileCheck2, LayoutPanelTop } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Matrix } from "@/components/matrix";
import { LightLegend, StatusLight } from "@/components/status-light";
import {
  ASOF, RUN_CLOSEOUT, RUN_DIGESTS, STALE_DAYS, TP_SANITY_HI, TP_SANITY_LO,
  auditDigest, auditLight, auditTally, digestLight,
} from "@/lib/via/vrn-run";
import type { Light } from "@/lib/via/types";

/**
 * VRN 實跑台(批419)——工作站那一跑的唯讀鏡面 + 判讀。
 * 微系統 U/I 的第一塊:一個引擎的真實輸出,一頁看完,而且看得出哪幾份可信。
 */

function Panel({
  icon, title, light, sub, children,
}: {
  icon: React.ReactNode; title: string; light?: Light; sub?: string; children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg bg-surface p-3 shadow-[var(--shadow-border)]">
      <header className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="text-muted" aria-hidden>{icon}</span>
          <h2 className="truncate text-sm font-semibold tracking-tight">{title}</h2>
          {light ? <StatusLight status={light} /> : null}
        </div>
        {sub ? <p className="font-mono text-[11px] text-subtle">{sub}</p> : null}
      </header>
      {children}
    </section>
  );
}

const pct = (x: number | null) => (x === null ? "—" : `${(x * 100).toFixed(1)}%`);

export function VrnRunDeck() {
  const c = RUN_CLOSEOUT;
  const tally = auditTally();
  const light = auditLight();
  const rows = RUN_DIGESTS.map((r) => ({ r, a: auditDigest(r) }));
  const order: Record<string, number> = { "TP 疑誤": 0, 非當期: 1, 未算: 2, 可信: 3 };
  rows.sort((x, y) => (order[x.a.verdict]! - order[y.a.verdict]!) || (y.r.reportDate < x.r.reportDate ? -1 : 1));

  return (
    <div className="flex flex-col gap-3" data-deck="vrnrun">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-subtle">vrn live run · read-only mirror</p>
          <h1 className="text-sm font-semibold tracking-tight">
            VRN 實跑台 · {c.ranAt} 工作站 65 份真報告(唯讀鏡面,不跑不抓)
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusLight status={light} label={`可信 ${tally.可信}/${RUN_DIGESTS.length}`} />
          <LightLegend />
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <Panel icon={<FileCheck2 className="size-4" />} title="鏈跑完了" light="ok" sub={`${c.reports} 份`}>
          <Matrix
            columns={["段", "份數"]}
            align={["left", "right"]}
            rows={Object.entries(c.stages).map(([k, v]) => [
              <span key="k">{k}</span>,
              <span key="v" className="font-mono tabular-nums">{v}</span>,
            ])}
          />
          <p className="mt-2 text-[11px] text-muted">
            收尾閘:DONE {c.done} · FAIL {c.fail} · PENDING {c.pending}。
            三方對照 {c.cross.checked}/{c.cross.of} 份 · DIVERGE {c.cross.diverge} · 表格獨有 {c.cross.onlyTable}。
          </p>
        </Panel>

        <Panel icon={<LayoutPanelTop className="size-4" />} title="頁面再生" light={c.ui.light} sub={`${c.ui.fresh}/${c.ui.pages} 新鮮`}>
          <ul className="text-xs text-muted">
            <li className="py-0.5">VRN 控制塔(產出索引/共識全景/共識明細)</li>
            <li className="py-0.5">VRN 每日觀察摘要</li>
            <li className="py-0.5">VRN 一題四點文摘(潛在上漲空間/目標價除權息調整)</li>
          </ul>
          <p className="mt-2 text-[11px] text-subtle">via-famui 判定 GREEN · 樞紐未起=頁內嵌快照</p>
        </Panel>

        <Panel icon={<AlertTriangle className="size-4" />} title="四點文摘判讀" light={light} sub={`${c.digest.reports} 份`}>
          <div className="flex flex-wrap gap-1.5">
            {(Object.entries(tally) as Array<[string, number]>).map(([k, n]) => (
              <span key={k} className="inline-flex items-center gap-1.5 rounded-md bg-elevated px-2 py-1 text-[11px]">
                <StatusLight status={digestLight(k as never)} />
                <span>{k} {n}</span>
              </span>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-muted">
            37 份裡只有 <b>{tally.可信} 份</b>的「潛在上漲空間」是它字面的意思。
            其餘:{tally.非當期} 份拿今日價比舊報告、{tally["TP 疑誤"]} 份目標價疑為擷取誤判、
            {tally.未算} 份沒抽到目標價。
          </p>
        </Panel>
      </div>

      <Panel
        icon={<CalendarClock className="size-4" />}
        title="逐份判讀 · 目標價合理帶與價格基準日"
        light={light}
        sub={`基準日 ${ASOF} · 合理帶 ${TP_SANITY_LO}–${TP_SANITY_HI} · 逾 ${STALE_DAYS} 天=非當期`}
      >
        <Matrix
          columns={["判讀", "檔名", "代號", "報告日", "距今", "目標價", "基準價", "比值", "今日比值", "說明"]}
          align={["left", "left", "left", "left", "right", "right", "right", "right", "right", "left"]}
          rows={rows.map(({ r, a }) => [
            <span key="v" className="inline-flex items-center gap-1.5">
              <StatusLight status={digestLight(a.verdict)} />
              <span className="whitespace-nowrap">{a.verdict}</span>
            </span>,
            <span key="f" className="truncate font-mono">{r.file}</span>,
            <span key="t" className="font-mono">{r.ticker}</span>,
            <span key="d" className="font-mono">{r.reportDate || "—"}</span>,
            <span key="g" className="font-mono tabular-nums">{a.days === null ? "—" : `${a.days}d`}</span>,
            <span key="p" className="font-mono tabular-nums">{r.tpAdj === null ? "—" : r.tpAdj}</span>,
            <span key="x" className="font-mono tabular-nums">{r.price}</span>,
            <span key="r" className="font-mono tabular-nums">{a.ratio === null ? "—" : a.ratio.toFixed(3)}</span>,
            <span key="u" className="font-mono tabular-nums">{pct(a.upside)}</span>,
            <span key="w" className="text-muted">{a.why}</span>,
          ])}
        />
        <p className="mt-2 text-[11px] text-subtle">
          兩道閘都<b>不刪任何數字</b>:照列,但講白它是什麼、不許它冒充預測。
          母倉同律在 <span className="font-mono">VRN_ENG080 v0101</span>(tp_sanity / basis_state)。
        </p>
      </Panel>
    </div>
  );
}

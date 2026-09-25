import { GitCompareArrows, ShieldCheck, Wrench } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Matrix } from "@/components/matrix";
import { StatusLight, LightLegend } from "@/components/status-light";
import { PSR_FINDINGS, PSR_LAST_RUN, PSR_NO_FLOOD, PSR_ROOT_CAUSE, PSR_ROUNDS, psrFindingsSplit, psrOverall, psrSandboxNote } from "@/lib/via/psrepair-rounds";
import { triEdgeRows, triNote } from "@/lib/via/tri-xcheck";
import type { Light } from "@/lib/via/types";

/** 母倉(movies-dataset)批402–404 成果台:唯讀鏡面,不跑不抓。 */

const BRIDGE_ROWS: Array<{ kind: string; scope: string; have: number; total: number; note: string }> = [
  { kind: "ACCEL", scope: "註冊夾", have: 521, total: 521, note: "ACCEL-BRIDGE → VIA_SuperAccel_Module → SUP_MDL737 → VeritasCeleritas.py" },
  { kind: "NET", scope: "VRN 擷取檔", have: 8, total: 8, note: "NET-BRIDGE → via_net_unified → SUP_MDL740 v0112 → VeritasAegisNexus.py(批402 正典優先)" },
  { kind: "PS-ACCEL", scope: "在冊 ps1", have: 788, total: 788, note: "VIA_PS_Accel_Module $VIA_ACCEL20 01–20" },
];

const INTAKE_ROWS: Array<{ state: string; n: number; tone: "ok" | "warn" | "pending"; note: string }> = [
  { state: "同", n: 36, tone: "ok", note: "逐位元相同 → 不重複收(Zero-Hydra)" },
  { state: "異", n: 23, tone: "warn", note: "同名不同內容 → 加 __cherrylagoon 尾綴並存,母倉正本零觸碰" },
  { state: "缺", n: 4, tone: "pending", note: "全新:Invoke-VIA-Spectrum / VRN_PIPELINE_LAUNCHER / VRN_Pipeline_Runner / Spectrum_preview_dual(4.3MB 只記指紋)" },
];

function Section({
  icon,
  title,
  light,
  sub,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  light: Light;
  sub: string;
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
          <StatusLight status={light} />
        </div>
        <p className="font-mono text-[11px] text-subtle">{sub}</p>
      </header>
      {children}
    </section>
  );
}

export function MotherDeck() {
  const split = psrFindingsSplit();
  const edges = triEdgeRows();

  return (
    <div className="flex flex-col gap-3" data-deck="mother">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-subtle">mother repo · movies-dataset</p>
          <h1 className="text-sm font-semibold tracking-tight">母倉成果台 · 批402–404(唯讀鏡面)</h1>
        </div>
        <LightLegend />
      </div>

      <Section
        icon={<GitCompareArrows className="size-4" />}
        title="VRN 三方對照 · 檔名 × 首頁 × 財報頁表格"
        light="ok"
        sub={triNote()}
      >
        <Matrix
          columns={["#", "邊", "狀態", "說明"]}
          align={["left", "left", "left", "left"]}
          rows={edges.map((e) => [
            <span key="i" className="font-mono text-subtle">{e.id}</span>,
            e.dim,
            <StatusLight key="l" status={e.light} label={e.state} />,
            <span key="n" className="text-muted">{e.note}</span>,
          ])}
        />
        <p className="mt-2 text-xs text-subtle">
          原缺口=財報頁表格從不與首頁/檔名對照(全樹只有 ENG074 讀 <code>vrn_report_financial</code>,四點取的是{" "}
          <code>vrn_report_metrics</code>)。批403 由 <code>ENG074 v0102 crosscheck()</code> 補齊第三邊,三角閉合。
        </p>
      </Section>

      <Section
        icon={<Wrench className="size-4" />}
        title="PS 修復三輪 · 卡斷修與洗版修"
        light={psrOverall()}
        sub={`${PSR_FINDINGS.files} 檔 · ${PSR_FINDINGS.total} findings · 並行可修 ${split.parallel}(${split.pctParallel}%)· 序相依 ${split.sequence}`}
      >
        <Matrix
          columns={["輪", "段", "rc", "狀態", "實跑"]}
          align={["left", "left", "right", "left", "left"]}
          rows={PSR_ROUNDS.map((r) => {
            const f = PSR_LAST_RUN.find((x) => x.id === r.id);
            return [
              <span key="i" className="font-mono">{r.id}</span>,
              <span key="l">
                {r.label}
                {r.readOnly ? <Badge tone="mute" className="ml-1.5">唯讀</Badge> : <Badge tone="warn" className="ml-1.5">-Fix</Badge>}
              </span>,
              <span key="rc" className="font-mono">{f && f.rc >= 0 ? f.rc : "—"}</span>,
              <StatusLight key="s" status={f?.light ?? "pending"} />,
              <span key="d" className="text-muted">{f?.detail ?? ""}</span>,
            ];
          })}
        />
        <ul className="mt-2 space-y-1 text-xs text-subtle">
          <li>
            <span className="text-warn">根因</span> {PSR_ROOT_CAUSE}
          </li>
          <li>
            <span className="text-ok">洗版修</span> {PSR_NO_FLOOD}
          </li>
          <li>{psrSandboxNote()}</li>
        </ul>
      </Section>

      <Section
        icon={<ShieldCheck className="size-4" />}
        title="橋覆蓋 · 加速/網路/PS 加速器"
        light="ok"
        sub="737／740 留作橋,不直 import;不代設 VIA_NET_CONSENT"
      >
        <Matrix
          columns={["種類", "範圍", "覆蓋", "鏈"]}
          align={["left", "left", "right", "left"]}
          rows={BRIDGE_ROWS.map((b) => [
            <span key="k" className="font-mono">{b.kind}</span>,
            b.scope,
            <span key="c" className="font-mono">{b.have}/{b.total}</span>,
            <span key="n" className="text-muted">{b.note}</span>,
          ])}
        />
      </Section>

      <Section
        icon={<GitCompareArrows className="size-4" />}
        title="本倉收容差異 · cherry-lagoon-honey-dove → 母倉"
        light="warn"
        sub="head ad5b0a17 · attachments + public/via 共 63 件逐件比對 · 只收異與缺 26 件"
      >
        <Matrix
          columns={["狀態", "件數", "處置"]}
          align={["left", "right", "left"]}
          rows={INTAKE_ROWS.map((r) => [
            <Badge key="s" tone={r.tone}>{r.state}</Badge>,
            <span key="n" className="font-mono">{r.n}</span>,
            <span key="d" className="text-muted">{r.note}</span>,
          ])}
        />
        <p className="mt-2 text-xs text-subtle">
          正典核對:本倉 <code>VeritasAegisNexus.py</code>(5172 行)/<code>VeritasCeleritas.py</code>(5694 行)比母倉正典
          (5186／5708)舊,與 b345／b383 收容件同版 → 批402 的正典選定站得住,無回退風險。
          TypeScript 面 <code>src/lib/via</code> 89 模組 + 66 測試共 21,346 行,母倉無對應實作,列冊候裁決。
        </p>
      </Section>
    </div>
  );
}

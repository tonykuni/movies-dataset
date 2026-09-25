import { useEffect } from "react";
import { Play, Shield } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LiveLog } from "@/components/live-log";
import { Matrix } from "@/components/matrix";
import { StatusLight } from "@/components/status-light";
import { AUDIT_STEPS } from "@/lib/via/audit";
import { accelLight, CAPABILITIES, LAUNCH_ACCELS } from "@/lib/via/mother-ops";
import { aggregateLanes, AST_LAYERS, CONTROLLER_LAUNCH, DCT_CATALOG, downwardGates } from "@/lib/via/govern";
import { MOTHER_FOLDER } from "@/lib/via/repair-pack";
import { useVia } from "@/lib/via/store";
import type { RepairKind } from "@/lib/via/types";

function repairTone(r: RepairKind): "ok" | "warn" | "bad" | "idle" {
  if (r === "REPAIRED") return "ok";
  if (r === "UNREPAIRABLE") return "bad";
  return "idle";
}

export function VarDeck() {
  const {
    autoAudit,
    setAutoAudit,
    auditBusy,
    auditProgress,
    auditTab,
    setAuditTab,
    auditLogs,
    auditRows,
    auditDetails,
    repairTools,
    runAudit,
    engines,
    downToken,
    downCommit,
    setDownToken,
    setDownCommit,
    mintDownToken,
    runDownward,
    downRows,
  } = useVia();

  useEffect(() => {
    const s = useVia.getState();
    if (s.autoAudit && !s.activated.var && !s.auditBusy) void s.runAudit();
  }, []);

  const fixed = auditRows.filter((r) => r.repair === "REPAIRED").length;
  const blocked = auditRows.filter((r) => r.repair === "UNREPAIRABLE").length;
  const lanes = aggregateLanes(
    downRows.map((r) => {
      const cap = CAPABILITIES.find((c) => c.urn === r.urn);
      const state = r.state === "APPLY" || r.state === "ANALYSIS" ? "OK" : r.state;
      const verdict = r.state === "BLOCKED" ? "BLOCKED" : r.state === "SKIPPED" ? "SKIPPED" : "GREEN";
      return { kind: cap?.kind ?? "OTHER", state, verdict };
    }),
  );

  return (
    <div className="space-y-5">
      <header>
        <p className="text-xs font-medium uppercase tracking-widest text-subtle">VAR · Action 04 · Central Govern</p>
        <h2 className="text-lg font-medium tracking-tight">VAR 自動鑑測</h2>
        <p className="mt-1 max-w-2xl text-xs leading-relaxed text-muted">
          對在冊全部引擎跑 AUDIT → TEST → DEBUG。可修復項只增不減（加速器、指紋、SSOT）。無法修復的仍寫入 LIVE LOG 與 DETAILS，不隱藏。
        </p>
      </header>

      <div className="flex flex-col gap-3 rounded-lg bg-surface p-4 shadow-[var(--shadow-border)] sm:flex-row sm:items-center">
        <label className="flex min-h-11 items-center gap-3 text-sm">
          <Switch checked={autoAudit} onCheckedChange={setAutoAudit} />
          自動鑑測
        </label>
        <Badge tone="mute">{engines.length} 具引擎</Badge>
        <Badge tone={fixed ? "ok" : "idle"}>修復 {fixed}</Badge>
        <Badge tone={blocked ? "bad" : "idle"}>無法 {blocked}</Badge>
        <span className="ml-auto font-mono text-xs tabular-nums text-subtle">{auditProgress}%</span>
        <Button data-action="var-start" disabled={auditBusy} onClick={() => void runAudit()}>
          <Play className="size-4" />
          啟動鑑測
        </Button>
      </div>
      <Progress value={auditProgress} />

      <Tabs value={auditTab} onValueChange={setAuditTab}>
        <TabsList>
          <TabsTrigger value="tab1">TAB 1 LIVE LOG / DETAILS</TabsTrigger>
          <TabsTrigger value="tab2">TAB 2 鑑測矩陣</TabsTrigger>
          <TabsTrigger value="tab3">TAB 3 修復狀態</TabsTrigger>
          <TabsTrigger value="tab4">TAB 4 母工具包</TabsTrigger>
        </TabsList>

        <TabsContent value="tab1" className="space-y-4" hidden={auditTab !== "tab1"}>
          <LiveLog lines={auditLogs} />
          <div>
            <div className="mb-2 flex items-center gap-2">
              <Shield className="size-4 text-muted" />
              <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">DETAILS</h3>
            </div>
            <Matrix
              columns={["燈", "時刻", "引擎", "ID", "修復", "發現"]}
              rows={auditDetails.map((d) => [
                <StatusLight key="l" status={d.status} />,
                <span key="t" className="font-mono tabular-nums">
                  {d.t}
                </span>,
                d.engineName,
                <span key="id" className="font-mono">
                  {d.engineId}
                </span>,
                <Badge key="r" tone={repairTone(d.repair)}>
                  {d.repair}
                </Badge>,
                <span key="f" className="max-w-md text-pretty text-muted">
                  {d.finding}
                </span>,
              ])}
              empty="尚無鑑測 DETAILS"
            />
          </div>
        </TabsContent>

        <TabsContent value="tab2" hidden={auditTab !== "tab2"}>
          <Matrix
            columns={["燈", "ID", "名稱", "類", ...AUDIT_STEPS.map((s) => s.id), "註"]}
            rows={auditRows.map((r) => [
              <StatusLight key="l" status={r.status} />,
              <span key="id" className="font-mono">
                {r.engineId}
              </span>,
              r.engineName,
              r.kind,
              ...AUDIT_STEPS.map((s) => <StatusLight key={s.id} status={r.steps[s.id] ?? "idle"} />),
              <span key="n" className="max-w-72 truncate text-muted">
                {r.note}
              </span>,
            ])}
            empty="尚未鑑測"
          />
        </TabsContent>

        <TabsContent value="tab3" hidden={auditTab !== "tab3"}>
          <h3 className="mb-2 text-xs font-medium">修復狀態矩陣</h3>
          <Matrix
            columns={["燈", "修復", "ID", "名稱", "發現"]}
            rows={auditRows.map((r) => [
              <StatusLight key="l" status={r.status} />,
              <Badge key="r" tone={repairTone(r.repair)}>
                {r.repair}
              </Badge>,
              r.engineId,
              r.engineName,
              r.findings.join(" · "),
            ])}
            empty="尚無修復列"
          />
        </TabsContent>
        <TabsContent value="tab4" hidden={auditTab !== "tab4"}>
          <h3 className="mb-2 text-xs font-medium">新增資料夾母工具包 · v0110 優先</h3>
          <p className="mb-2 font-mono text-[11px] text-subtle">{MOTHER_FOLDER}</p>
          <Matrix
            columns={["燈", "ID", "檔", "採用", "註"]}
            rows={(repairTools.length ? repairTools : []).map((t) => [
              <StatusLight key="l" status={t.light} />,
              t.id,
              t.file,
              t.pick,
              t.note,
            ])}
            empty="尚未跑鑑測"
          />
          <h3 className="mb-2 mt-4 text-xs font-medium">啟動器加速器 · 偵測不到就是 ABSENT</h3>
          <Matrix
            columns={["燈", "ID", "名稱", "態", "類"]}
            rows={LAUNCH_ACCELS.map((a) => [
              <StatusLight key="l" status={accelLight(a.state)} />,
              a.id,
              a.name,
              a.state,
              a.kind,
            ])}
          />
          <h3 className="mb-2 mt-4 text-xs font-medium">下行雙閘 · 權杖綁計畫雜湊</h3>
          <div className="mb-3 flex flex-col gap-2 rounded-md bg-surface p-3 shadow-[var(--shadow-border)] sm:flex-row sm:items-end">
            <label className="min-w-0 flex-1 text-xs">
              <span className="mb-1 block text-subtle">權杖</span>
              <Input
                autoComplete="off"
                spellCheck={false}
                className="font-mono"
                placeholder="==VEM-APPROVE==YYYYMMDD_HHMMSS-digest"
                value={downToken}
                onChange={(e) => setDownToken(e.target.value)}
              />
            </label>
            <label className="flex min-h-11 items-center gap-2 text-xs">
              <Switch checked={downCommit} onCheckedChange={setDownCommit} />
              commit
            </label>
            <Button size="sm" variant="ghost" type="button" onClick={() => mintDownToken()}>
              產生權杖
            </Button>
            <Button size="sm" data-action="down-start" type="button" onClick={() => runDownward()}>
              下行 DryRun
            </Button>
          </div>
          <pre className="mb-2 overflow-x-auto font-mono text-xs leading-relaxed text-subtle">{CONTROLLER_LAUNCH}</pre>
          <h3 className="mb-2 mt-4 text-xs font-medium">下行拓撲 · 變更類無權杖 SKIPPED</h3>
          <Matrix
            columns={["層", "URN", "能力", "態", "註"]}
            rows={downRows.map((r) => [String(r.level), r.urn, r.name, r.state, r.note])}
          />
          <h3 className="mb-2 mt-4 text-xs font-medium">分系封印 · 分析 RED 不綁架</h3>
          <p className="mb-2 font-mono text-xs text-subtle">overall {lanes.overall}</p>
          <Matrix
            columns={["系", "最差"]}
            rows={Object.entries(lanes.lanes).map(([k, v]) => [k, v])}
          />
          <h3 className="mb-2 mt-4 text-xs font-medium">下行閘門 D01–D08</h3>
          <Matrix
            columns={["燈", "碼", "閘", "裁", "註"]}
            rows={downwardGates({ token: downToken, commit: downCommit }).map((g) => [
              <StatusLight key="l" status={g.light} />,
              g.code,
              g.title,
              g.status,
              g.detail,
            ])}
          />
          <h3 className="mb-2 mt-4 text-xs font-medium">DCT 硬化 · 母機子行程域</h3>
          <Matrix
            columns={["燈", "碼", "故障", "級", "態", "庫", "註"]}
            rows={DCT_CATALOG.map((d) => [
              <StatusLight key="l" status={d.light} />,
              d.code,
              d.title,
              d.sev,
              d.status,
              d.lib || "—",
              d.note,
            ])}
          />
          <h3 className="mb-2 mt-4 text-xs font-medium">AST 四層 · Name ctx 契約</h3>
          <Matrix
            columns={["燈", "層", "工具", "看見", "看不見"]}
            rows={AST_LAYERS.map((l) => [
              <StatusLight key="l" status={l.light} />,
              `${l.id} ${l.name}`,
              l.tool,
              l.sees,
              l.misses,
            ])}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

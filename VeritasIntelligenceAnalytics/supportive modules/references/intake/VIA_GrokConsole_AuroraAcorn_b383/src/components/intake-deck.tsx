import { useEffect, useRef, useState } from "react";
import { Play, Upload } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LiveLog } from "@/components/live-log";
import { CategoryBlock, Matrix } from "@/components/matrix";
import { StatusLight } from "@/components/status-light";
import { formatBytes, formatNum } from "@/lib/utils";
import { PIPELINE_STEPS } from "@/lib/via/catalog";
import { VRN_INCOMING_PATHS, VRN_NLP_ENGINE_PATH } from "@/lib/via/incoming";
import { KNOWLEDGE_SOURCES, METHOD_PILLARS } from "@/lib/via/knowledge";
import { useVia } from "@/lib/via/store";

export function IntakeDeck() {
  const {
    files,
    addDropped,
    toggleSkip,
    skipAllDups,
    setSkipAllDups,
    runIntake,
    intakeBusy,
    intakeProgress,
    intakeLogs,
    intakeTab,
    setIntakeTab,
    basics,
    summaries,
    finances,
    vrnSeal,
  } = useVia();
  const inputRef = useRef<HTMLInputElement>(null);
  const tabsRef = useRef<HTMLDivElement>(null);
  const [over, setOver] = useState(false);
  const [knowOpen, setKnowOpen] = useState(false);

  const onFiles = (list: FileList | null) => {
    if (!list?.length) return;
    addDropped(Array.from(list));
  };

  const errorRows = files.filter((f) => f.status === "bad" || (f.stuckStep && f.status !== "ok"));
  const done = !intakeBusy && intakeProgress === 100;

  useEffect(() => {
    if (done && intakeTab !== "tab1") {
      tabsRef.current?.scrollIntoView({ block: "start", behavior: "smooth" });
    }
  }, [done, intakeTab]);

  return (
    <div className="space-y-4">
      <header>
        <p className="text-xs font-medium uppercase tracking-widest text-subtle">VRN · Action 02 · Central Govern</p>
        <h2 className="text-lg font-medium tracking-tight">VRN 研報管線</h2>
        <p className="mt-1 max-w-2xl text-xs leading-relaxed text-muted">
          CACHE 已灌進件：TAB 2 身份、TAB 3 一題四點、TAB 4 財務。零位元組留 TAB 1。NLP LIVE 關。可再拖檔重跑。
        </p>
        <p className="mt-2 font-mono text-[11px] leading-relaxed text-subtle">
          incoming {VRN_INCOMING_PATHS[0]} · 備援 {VRN_INCOMING_PATHS[1]}
          <br />
          NLP {VRN_NLP_ENGINE_PATH} · 表擷取 v1.5.0 verbatim
        </p>
        {vrnSeal ? (
          <Badge className="mt-2" tone={vrnSeal.light === "ok" ? "ok" : vrnSeal.light === "bad" ? "bad" : "warn"}>
            {vrnSeal.note}
          </Badge>
        ) : null}
        <p className="mt-2 font-mono text-xs text-subtle">知識冊 {KNOWLEDGE_SOURCES.length} · 支柱 {METHOD_PILLARS.join("／")}</p>
      </header>

      <CategoryBlock title="知識冊 SSOT" count={KNOWLEDGE_SOURCES.length} open={knowOpen} onToggle={() => setKnowOpen((v) => !v)}>
        <Matrix columns={["冊", "檔", "職"]} rows={KNOWLEDGE_SOURCES.map((k) => [k.id, k.file, k.role])} />
      </CategoryBlock>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          onFiles(e.dataTransfer.files);
        }}
        className={`rounded-lg bg-surface p-4 shadow-[var(--shadow-border)] ${over ? "ring-2 ring-ring" : ""}`}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-medium">VRN WINDOW I/O</p>
            <p className="text-xs text-muted">拖曳檔案或選取本機檔案。不寫入來源。</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <input
              ref={inputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => onFiles(e.target.files)}
            />
            <Button variant="outline" onClick={() => inputRef.current?.click()}>
              <Upload className="size-3.5" />
              新增檔案
            </Button>
            <Button data-action="vrn-start" disabled={files.length === 0} onClick={() => void runIntake()}>
              <Play className="size-3.5" />
              {intakeBusy ? "驗證中" : "啟動驗證"}
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex min-h-10 items-center gap-2 text-xs">
          <Checkbox checked={skipAllDups} onCheckedChange={(v) => setSkipAllDups(Boolean(v))} />
          去重：副檔名與大小相同則略過
        </label>
        <Badge tone="mute">{files.length} 件</Badge>
        <span className="ml-auto font-mono text-xs tabular-nums text-subtle">{intakeProgress}%</span>
      </div>
      <Progress value={intakeProgress} />

      {done ? (
        <div className="flex flex-wrap items-center gap-2 rounded-md bg-surface px-3 py-2 shadow-[var(--shadow-border)]">
          <span className="text-xs text-muted">結果</span>
          <Button size="sm" variant={intakeTab === "tab1" ? "default" : "outline"} onClick={() => setIntakeTab("tab1")}>
            TAB 1 失敗 {errorRows.length}
          </Button>
          <Button size="sm" variant={intakeTab === "tab2" ? "default" : "outline"} data-jump="tab2" onClick={() => setIntakeTab("tab2")}>
            TAB 2 INFO {basics.length}
          </Button>
          <Button size="sm" variant={intakeTab === "tab3" ? "default" : "outline"} data-jump="tab3" onClick={() => setIntakeTab("tab3")}>
            TAB 3 摘要 {summaries.length}
          </Button>
          <Button size="sm" variant={intakeTab === "tab4" ? "default" : "outline"} data-jump="tab4" onClick={() => setIntakeTab("tab4")}>
            TAB 4 財務 {finances.length}
          </Button>
        </div>
      ) : null}

      <div ref={tabsRef} id="vrn-tabs" className="sticky top-0 z-10 -mx-1 bg-bg/95 px-1 py-2 backdrop-blur-sm">
        <Tabs value={intakeTab} onValueChange={setIntakeTab} data-intake-tab={intakeTab}>
          <TabsList>
            <TabsTrigger value="tab1">TAB 1 日誌 · {errorRows.length}</TabsTrigger>
            <TabsTrigger value="tab2">TAB 2 INFO · {basics.length}</TabsTrigger>
            <TabsTrigger value="tab3">TAB 3 摘要 · {summaries.length}</TabsTrigger>
            <TabsTrigger value="tab4">TAB 4 財務 · {finances.length}</TabsTrigger>
          </TabsList>

          <TabsContent value="tab1" className="space-y-4" hidden={intakeTab !== "tab1"}>
            <Matrix
              columns={["去重", "燈", "來源", "檔名", "格式", "大小", "停在", "原因", ...PIPELINE_STEPS.map((s) => s.id)]}
              rows={files.map((f) => [
                f.dupOf ? (
                  <Checkbox key="c" checked={f.skipDup} onCheckedChange={() => toggleSkip(f.id)} />
                ) : (
                  <span key="c" className="text-subtle">
                    —
                  </span>
                ),
                <StatusLight key="l" status={f.status} />,
                f.origin === "folder" ? "資料夾" : "拖曳",
                <span key="n" className="max-w-56 truncate font-medium">
                  {f.name}
                </span>,
                f.ext,
                formatBytes(f.size),
                f.stuckStep ?? "—",
                <span key="d" className="max-w-52 truncate text-muted">
                  {f.stuckDetail ?? "—"}
                </span>,
                ...PIPELINE_STEPS.map((s) => <StatusLight key={s.id} status={f.steps[s.id] ?? "idle"} />),
              ])}
              empty="尚無輸入"
            />
            <div>
              <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">錯誤步驟矩陣</h3>
              <Matrix
                columns={["燈", "檔名", "步驟", "步驟名", "詳情"]}
                rows={errorRows.map((f) => {
                  const step = PIPELINE_STEPS.find((s) => s.id === f.stuckStep);
                  return [
                    <StatusLight key="l" status={f.status} />,
                    f.name,
                    f.stuckStep ?? "—",
                    step?.title ?? "—",
                    f.stuckDetail ?? "—",
                  ];
                })}
                empty="無卡住步驟"
              />
            </div>
            <LiveLog lines={intakeLogs} />
          </TabsContent>

          <TabsContent value="tab2" hidden={intakeTab !== "tab2"}>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">TAB 2 · BASIC INFO · MDL006 SSOT</h3>
            <Matrix
              columns={["燈", "風險", "驗證", "類型", "評等", "檔名", "代碼", "市場", "YF", "TT", "公司", "券商", "報告日", "report_code"]}
              rows={basics.map((b) => [
                <StatusLight key="l" status={b.status} />,
                <Badge
                  key="r"
                  tone={b.validationRisk === "GREEN" ? "ok" : b.validationRisk === "YELLOW" ? "warn" : "bad"}
                >
                  {b.validationRisk}
                </Badge>,
                b.validationStatus,
                b.reportType,
                b.ratingCat === "—" ? "—" : `${b.ratingCat}/${b.rating}`,
                b.fileName,
                <span key="t" className="font-mono">
                  {b.ticker}
                </span>,
                b.market,
                b.yfinanceTicker,
                b.bloombergTicker,
                b.companyName,
                b.broker,
                b.reportDate,
                <span key="c" className="font-mono text-xs">
                  {b.reportCode}
                </span>,
              ])}
              empty="尚未通過驗證"
            />
          </TabsContent>

          <TabsContent value="tab3" hidden={intakeTab !== "tab3"}>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">TAB 3 · SUMMARIZER · 一題四點（K1 上漲空間 · K2 EPS · K3/K4 首頁其餘 · K5 可空）</h3>
            <Matrix
              columns={["檔名", "槽", "摘要句", "實體", "三元組", "信心", "回源"]}
              rows={summaries.map((s) => [
                s.fileName,
                s.slot,
                <span key="b" className="max-w-md text-pretty">
                  {s.bullet}
                </span>,
                s.entity,
                <span key="t" className="font-mono text-xs">
                  {s.triple}
                </span>,
                <span key="c" className="tabular-nums">
                  {s.confidence.toFixed(2)}
                </span>,
                s.grounded ? <Badge tone="ok">GROUNDED</Badge> : <Badge tone="bad">UNGROUNDED</Badge>,
              ])}
              empty="尚無摘要"
            />
          </TabsContent>

          <TabsContent value="tab4" hidden={intakeTab !== "tab4"}>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">TAB 4 · FINANCIAL · 原子列 V 才綠 · 假綠燈禁止</h3>
            <Matrix
              columns={["燈", "級", "檔名", "類", "報表", "科目", "canonical", "期間", "數值", "單位", "缺陷"]}
              rows={finances.map((r) => [
                <StatusLight key="l" status={r.status} />,
                r.grade ?? "—",
                r.fileName,
                r.category,
                r.statement,
                r.item,
                r.dataName,
                r.period,
                <span key="v" className="tabular-nums">
                  {formatNum(r.value, 1)}
                </span>,
                r.unit,
                (r.defects ?? []).join(" ") || "—",
              ])}
              empty="尚無財務列"
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

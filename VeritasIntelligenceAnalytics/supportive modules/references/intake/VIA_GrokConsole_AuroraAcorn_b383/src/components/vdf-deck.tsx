import type { ReactNode } from "react";
import { useState } from "react";
import { Play, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LiveLog } from "@/components/live-log";
import { CategoryBlock, Matrix } from "@/components/matrix";
import { StatusLight } from "@/components/status-light";
import { formatNum } from "@/lib/utils";
import { STRUCT_RULES } from "@/lib/via/accel";
import { VDF_FETCH_LANES, VDF_MODULES } from "@/lib/via/catalog";
import { celAegNote, celAegRows } from "@/lib/via/cel-aeg";
import { useVia } from "@/lib/via/store";
import { resolveTwTicker } from "@/lib/via/tw-ticker";
import { runTranscodeFetchTest } from "@/lib/via/transcode-fetch";
import { ENG047_FRED, MACRO_PLUS, MOTHER_PACK, TW_LEADERS, TW_UNIVERSE_COUNTS, lookupTw } from "@/lib/via/vdf-mother";
import { GFF_MEMBERS } from "@/lib/via/gff";
import { CNS_STRUCT, universeGroups } from "@/lib/via/consensus";
import { viaDbRows } from "@/lib/via/via-db-parts";
import { AETF_UNIVERSE, aetfMeta, formatPct, formatYi } from "@/lib/via/active-etf";
import { costPnl, fsUpside, holdKpis, yfUpside } from "@/lib/via/aetf-hold-matrix";
import { SPEC_COLS, spectrumCells } from "@/lib/via/spectrum";

export function VdfDeck() {
  const {
    fredKey,
    fredApi,
    eiaKey,
    eiaApi,
    startYear,
    setFredKey,
    setFredApi,
    setEiaKey,
    setStartYear,
    tools,
    vdfBusy,
    vdfProgress,
    vdfNote,
    fredRows,
    collapsed,
    toggleCat,
    setCatsOpen,
    vdfLogs,
    vdfTab,
    setVdfTab,
    pairRows,
    pairPlan,
    fetchMetrics,
    confirmNet,
    setConfirmNet,
    vdfGov,
    vdfFetchGov,
    vdfPlanLanes,
    vdfLaneResults,
    vdfManifest,
    vdfSeal,
    vdfEndRows,
    vdfModRows,
    marketRows,
    xvalRows,
    etfFlow,
    revRows,
    revGroups,
    revNote,
    gffRows,
    gffNote,
    aetfRows,
    aetfNote,
    aetfVerify,
    aetfNavLogic,
    aetfJsonMap,
    aetfCash,
    aetfDeltas,
    aetfFilter,
    setAetfFilter,
    aetfPicked,
    aetfHoldAgg,
    aetfFundPicks,
    toggleAetfPick,
    aetfPickAll,
    aetfPickNone,
    aetfScope,
    setAetfScope,
    specRows,
    cnsRows,
    cnsNote,
    cnsLong,
    cnsCompare,
    cnsMode,
    cnsQuery,
    setCnsMode,
    setCnsQuery,
    runVdf,
    vdfNextRound,
    roundConsent,
    setRoundConsent,
    runVdfNextRound,
    gapReport,
    procRows,
    runSeal,
  } = useVia();

  const [govOpen, setGovOpen] = useState(false);
  const [motherOpen, setMotherOpen] = useState(false);
  const [xvalOpen, setXvalOpen] = useState(true);
  const [bookOpen, setBookOpen] = useState(true);
  const [revOpen, setRevOpen] = useState(true);
  const [gffOpen, setGffOpen] = useState(true);
  const [aeaOpen, setAeaOpen] = useState(true);
  const [holdOpen, setHoldOpen] = useState(true);
  const [specOpen, setSpecOpen] = useState(true);
  const [cnsOpen, setCnsOpen] = useState(true);
  const [q, setQ] = useState("2330");
  const cats = Array.from(new Set(fredRows.map((r) => r.category)));
  const hit = resolveTwTicker(q);
  const member = hit ? lookupTw(hit.core) : undefined;
  const xcode = runTranscodeFetchTest();

  return (
    <div className="space-y-4">
      <header className="flex flex-col gap-1">
        <p className="text-xs font-medium uppercase tracking-widest text-subtle">VDF · Action 01 · Central Govern</p>
        <h2 className="text-lg font-medium tracking-tight">VDF 擷取主管台</h2>
        <p className="max-w-2xl text-xs leading-relaxed text-muted">
          CACHE 已灌：FRED 列、2023 湖槽、主動 ETF、月營收。閘關不外呼。再按「跑完 VDF」重跑。
        </p>
      </header>

      <section className="grid items-start gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(14rem,28%)]" data-vdf-close="1">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">VDF 收官六程 · D1–D6</h3>
            <Button size="sm" variant="outline" data-action="seal-vdf" onClick={() => void runSeal()}>
              實測收官
            </Button>
          </div>
          <Matrix
            columns={["燈", "結果", "ID", "程序", "輸出"]}
            rows={(procRows ?? [])
              .filter((r) => r.id.startsWith("D"))
              .map((r) => [
                <StatusLight key="l" status={r.light} />,
                r.result,
                r.id,
                r.name,
                r.out,
              ])}
            empty="按 實測收官 跑 D1–D6"
          />
        </div>
        <aside className="min-w-0 space-y-1">
          <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">LIVE LOG</h3>
          <LiveLog lines={vdfLogs} compact />
        </aside>
      </section>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <Field label="FRED API">
          <Input
            autoComplete="off"
            spellCheck={false}
            placeholder="https://api.stlouisfed.org/fred/series/observations"
            value={fredApi}
            onChange={(e) => setFredApi(e.target.value)}
          />
        </Field>
        <Field label="FRED KEY">
          <Input
            type="password"
            autoComplete="off"
            placeholder="32 位 hex"
            value={fredKey}
            onChange={(e) => setFredKey(e.target.value)}
          />
        </Field>
        <Field label="EIA KEY">
          <Input
            type="password"
            autoComplete="off"
            placeholder="參數 · 以後再測"
            title={eiaApi}
            value={eiaKey}
            onChange={(e) => setEiaKey(e.target.value)}
          />
        </Field>
        <Field label="起始年">
          <Input
            type="number"
            min={1990}
            max={2026}
            value={startYear}
            onChange={(e) => setStartYear(Number(e.target.value) || 2023)}
          />
        </Field>
        <Field label="閘1 NET">
          <div className="flex h-8 items-center gap-2">
            <Switch checked={confirmNet} onCheckedChange={setConfirmNet} />
            <span className="font-mono text-xs text-subtle">{confirmNet ? "CONSENT" : "OFF"}</span>
          </div>
        </Field>
        <Field label="閘2 下一輪">
          <div className="flex h-8 items-center gap-2">
            <Switch checked={roundConsent} onCheckedChange={setRoundConsent} />
            <span className="font-mono text-xs text-subtle">{roundConsent ? "YES" : "OFF"}</span>
          </div>
        </Field>
        <div className="flex items-end gap-2">
          <Button className="w-full" data-action="vdf-start" disabled={vdfBusy} onClick={() => void runVdf()}>
            <Play className="size-3.5" />
            跑完 VDF
          </Button>
          <Button
            className="w-full"
            variant="outline"
            data-action="vdf-next"
            disabled={vdfBusy || !vdfNextRound}
            onClick={() => void runVdfNextRound()}
          >
            手動下一輪
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-xs text-muted">{vdfNote}</p>
          {pairPlan ? (
            <Badge tone="ok">
              ×{pairPlan.planFactor} · {pairPlan.active}/20
            </Badge>
          ) : null}
          <Badge tone={confirmNet ? "ok" : "warn"}>閘1 NET {confirmNet ? "開" : "關"}</Badge>
          <Badge tone={roundConsent ? "ok" : "warn"}>閘2 下一輪 {roundConsent ? "YES" : "關"}</Badge>
          <Badge tone="warn">EIA {eiaKey.trim() ? "KEY 已收 · 以後再測" : "KEY 空 · 以後再測"}</Badge>
          {vdfSeal ? <Badge tone={vdfSeal.light === "ok" ? "ok" : "warn"}>{vdfSeal.note}</Badge> : null}
          {fetchMetrics ? (
            <Badge tone={fetchMetrics.isa === "scalar" ? "warn" : "ok"}>
              {fetchMetrics.isa} · f64×{fetchMetrics.f64Width} · {fetchMetrics.align}B
            </Badge>
          ) : null}
          <span className="ml-auto font-mono text-xs tabular-nums text-subtle">{vdfProgress}%</span>
        </div>
        <Progress value={vdfProgress} />
      </div>

      <Tabs value={vdfTab} onValueChange={setVdfTab}>
        <TabsList>
          <TabsTrigger value="tab1">TAB 1 擷取</TabsTrigger>
          <TabsTrigger value="tab2">TAB 2 搭配</TabsTrigger>
          <TabsTrigger value="tab3">TAB 3 結構</TabsTrigger>
          <TabsTrigger value="tab4">TAB 4 加乘</TabsTrigger>
        </TabsList>

        <TabsContent value="tab1" className="space-y-4" hidden={vdfTab !== "tab1"}>
          <section className="space-y-2" data-vdf-end="1">
            <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">跑完矩陣 · E01–E15 收官</h3>
            <Matrix
              columns={["燈", "結果", "步", "名", "輸出"]}
              rows={vdfEndRows.map((r) => [
                <StatusLight key="l" status={r.light} />,
                r.result,
                r.id,
                r.name,
                r.out,
              ])}
              empty="按 跑完 VDF"
            />
            <Matrix
              columns={["燈", "結果", "模組", "閘", "輸出"]}
              rows={vdfModRows.map((r) => [
                <StatusLight key="l" status={r.light} />,
                r.result,
                r.id,
                r.gate,
                r.out,
              ])}
              empty=""
            />
          </section>

          {gapReport ? (
            <section className="space-y-2">
              <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">2023 起補湖 · {gapReport.note}</h3>
              <Matrix
                columns={["燈", "年", "動作", "種子", "註"]}
                rows={gapReport.rows.map((r) => [
                  <StatusLight key={r.year} status={r.light} />,
                  String(r.year),
                  r.action,
                  String(r.seed ?? 0),
                  r.note,
                ])}
              />
            </section>
          ) : null}

          <section className="space-y-2 rounded-md bg-surface p-3 shadow-[var(--shadow-border)]">
            <p className="text-xs font-medium">自動轉碼擷取測試 · 四碼／.TW／.TWO／TT → 擷取鍵</p>
            <div className="flex flex-wrap items-end gap-2">
              <Field label="代號">
                <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="2330 或 2330.TW 或 5347.TWO" />
              </Field>
              <p className="font-mono text-xs text-muted">
                {hit
                  ? `${hit.native} · ${hit.market} · 擷取鍵 ${hit.yfinance}${hit.recovered ? " · 已救回" : ""} · ${hit.bloomberg}${member ? ` · ${member.name}/${member.group}` : " · CACHE 未列"}`
                  : "無法解析"}
              </p>
            </div>
            <Matrix
              columns={["燈", "例", "輸入", "四碼", "擷取鍵", "救回", "CACHE", "註"]}
              rows={xcode.rows.map((r) => [
                <StatusLight key={r.id} status={r.light} />,
                r.id,
                r.input,
                r.core,
                r.fetchKey,
                r.recovered ? "是" : "—",
                r.fetched ? "命中" : "未列",
                r.note,
              ])}
            />
            <p className="font-mono text-xs text-subtle">{xcode.note} · 閘關不外呼</p>
          </section>

          <CategoryBlock
            title="母系統契約"
            count={MOTHER_PACK.length + TW_UNIVERSE_COUNTS.members}
            open={motherOpen}
            onToggle={() => setMotherOpen((v) => !v)}
          >
            <div className="space-y-3">
              <p className="font-mono text-xs text-subtle">
                焦點宇宙 {TW_UNIVERSE_COUNTS.members} · 上市 {TW_UNIVERSE_COUNTS.twse} · 上櫃 {TW_UNIVERSE_COUNTS.tpex} · 族群 {TW_UNIVERSE_COUNTS.groups}
              </p>
              <Matrix
                columns={["代號", "市場", "YF", "TT", "名稱", "族群"]}
                rows={TW_LEADERS.slice(0, 16).map((m) => [m.ticker, m.market, m.yfinance, m.bloomberg, m.name, m.group])}
              />
              <Matrix columns={["FRED", "名稱", "類"]} rows={ENG047_FRED.slice(0, 8).map((s) => [s.seriesId, s.title, s.category])} />
              <Matrix columns={["代號", "名稱", "類", "閘"]} rows={MACRO_PLUS.map((s) => [s.seriesId, s.title, s.category, s.gate])} />
              <Matrix columns={["冊", "檔", "職"]} rows={MOTHER_PACK.map((p) => [p.id, p.file, p.role])} />
            </div>
          </CategoryBlock>

          <CategoryBlock title="多源驗證 · 同日 FRED×YF×AK" count={xvalRows.length} open={xvalOpen} onToggle={() => setXvalOpen((v) => !v)}>
            <Matrix
              columns={["燈", "項目", "源A", "A", "源B", "B", "差", "日"]}
              rows={xvalRows.map((r) => [
                <StatusLight key="l" status={r.light} />,
                r.name,
                r.a,
                r.va,
                r.b,
                r.vb,
                r.pct == null ? "—" : `${(r.pct * 100).toFixed(2)}%`,
                r.date,
              ])}
            />
          </CategoryBlock>

          <CategoryBlock title="台股月營收 · VDF_ENG075 · MOPS 月檔" count={revRows.length} open={revOpen} onToggle={() => setRevOpen((v) => !v)}>
            <p className="font-mono text-xs text-subtle">{revNote} · 單位 CACHE 指數 · 非官方億元 · LIVE 後換 MOPS 原值</p>
            <Matrix
              columns={["燈", "代號", "名稱", "市場", "族群", "月營收", "YoY", "MoM", "連增"]}
              rows={revRows.map((r) => [
                <StatusLight key="l" status={r.light} />,
                r.ticker,
                r.name,
                r.market,
                r.group,
                r.rev,
                r.yoy == null ? "—" : `${(r.yoy * 100).toFixed(1)}%`,
                r.mom == null ? "—" : `${(r.mom * 100).toFixed(1)}%`,
                r.streak,
              ])}
            />
            <Matrix
              columns={["燈", "族群", "家數", "YoY 中位"]}
              rows={revGroups.map((g) => [
                <StatusLight key="l" status={g.light} />,
                g.group,
                g.n,
                g.yoyMed == null ? "—" : `${(g.yoyMed * 100).toFixed(1)}%`,
              ])}
            />
          </CategoryBlock>

          <CategoryBlock title="VIA-GLSS · Global Liquidity Sandbox Simulation" count={GFF_MEMBERS.length} open={gffOpen} onToggle={() => setGffOpen((v) => !v)}>
            <p className="font-mono text-xs text-subtle">{gffNote || "跑完 VDF 後出模擬列"}</p>
            <Matrix
              columns={["燈", "引擎", "職", "寫入", "LIVE"]}
              rows={GFF_MEMBERS.map((m) => [
                <StatusLight key={m.id} status={m.id === "VDF_ENG075" ? "ok" : m.live ? "ok" : "warn"} />,
                m.id,
                m.role,
                m.write,
                m.live ? "可" : "關",
              ])}
            />
            <Matrix
              columns={["燈", "層", "指標", "值", "註"]}
              rows={gffRows.map((r) => [
                <StatusLight key={r.id} status={r.light} />,
                r.layer,
                r.metric,
                r.value,
                r.note,
              ])}
            />
          </CategoryBlock>

          <CategoryBlock title="VIA-AEA · 主動台股 ETF 全冊" count={aetfCash.length} open={aeaOpen} onToggle={() => setAeaOpen((v) => !v)}>
            <p className="font-mono text-xs text-subtle">{aetfNote}</p>
            <div className="flex flex-wrap gap-1">
              {(["TW", "GL", "ALL"] as const).map((s) => (
                <Button key={s} size="sm" variant={aetfScope === s ? "default" : "outline"} data-action={`aea-${s.toLowerCase()}`} onClick={() => setAetfScope(s)}>
                  {s === "TW" ? "台股成分" : s === "GL" ? "海外" : "全部 29"}
                </Button>
              ))}
            </div>
            <div className="grid items-start gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(14rem,28%)]">
              <div className="min-w-0 space-y-2">
                <p className="text-xs font-medium uppercase tracking-wide text-subtle">名冊 · 規模／溢價</p>
                <Matrix
                  columns={["代碼", "簡稱", "投信", "域", "風格", "AUM", "NAV", "市價", "溢價", "流入", "流出"]}
                  align={["left", "left", "left", "left", "left", "right", "right", "right", "right", "right", "right"]}
                  empty="無名冊"
                  rows={(aetfScope === "ALL" ? aetfCash : aetfCash.filter((c) => aetfMeta(c.ticker).scope === aetfScope)).map((c) => {
                    const m = aetfMeta(c.ticker);
                    return [
                      c.ticker,
                      m.name,
                      m.issuer,
                      m.scope === "TW" ? "台股" : "海外",
                      m.style,
                      formatYi(c.aum),
                      c.nav.toFixed(2),
                      c.px.toFixed(2),
                      formatPct(c.premium),
                      formatYi(c.inFlow),
                      formatYi(c.outFlow),
                    ];
                  })}
                />
                <p className="text-xs font-medium uppercase tracking-wide text-subtle">驗證 · 缺漏／自動更新</p>
                <Matrix
                  columns={["燈", "層", "指標", "值", "註"]}
                  rows={aetfVerify.map((r) => [
                    <StatusLight key={r.id} status={r.light} />,
                    r.layer,
                    r.metric,
                    r.value,
                    r.note,
                  ])}
                />
                <p className="text-xs font-medium uppercase tracking-wide text-subtle">日 NAV 契約 · 可驗</p>
                <Matrix
                  columns={["燈", "層", "指標", "值", "註"]}
                  rows={aetfNavLogic.map((r) => [
                    <StatusLight key={r.id} status={r.light} />,
                    r.layer,
                    r.metric,
                    r.value,
                    r.note,
                  ])}
                />
                <p className="text-xs font-medium uppercase tracking-wide text-subtle">TWSE JSON h 對照</p>
                <Matrix
                  columns={["燈", "層", "指標", "值", "註"]}
                  rows={aetfJsonMap.map((r) => [
                    <StatusLight key={r.id} status={r.light} />,
                    r.layer,
                    r.metric,
                    r.value,
                    r.note,
                  ])}
                />
                <p className="text-xs font-medium uppercase tracking-wide text-subtle">現金流 · 僅 CACHE 三檔有 Δ單位</p>
                <Matrix
                  columns={["代碼", "名稱", "AUM", "NAV", "市價", "溢價", "流入", "流出", "淨流"]}
                  align={["left", "left", "right", "right", "right", "right", "right", "right", "right"]}
                  empty="無 NAV 快照"
                  rows={(aetfScope === "ALL" ? aetfCash : aetfCash.filter((c) => aetfMeta(c.ticker).scope === aetfScope)).map((c) => [
                    c.ticker,
                    c.name || aetfMeta(c.ticker).name,
                    formatYi(c.aum),
                    c.nav.toFixed(2),
                    c.px.toFixed(2),
                    formatPct(c.premium),
                    formatYi(c.inFlow),
                    formatYi(c.outFlow),
                    formatYi(c.net),
                  ])}
                />
              </div>
              <aside className="min-w-0 space-y-2">
                <p className="text-xs font-medium uppercase tracking-wide text-subtle">持股變化 · 篩選</p>
                <div className="space-y-1">
                  <Label htmlFor="aea-q" className="text-xs uppercase tracking-wide text-subtle">代碼</Label>
                  <Input
                    id="aea-q"
                    list="aea-funds"
                    value={aetfFilter}
                    onChange={(e) => setAetfFilter(e.target.value)}
                    placeholder="全部 或 00980A"
                    className="h-8 font-mono text-xs"
                  />
                  <datalist id="aea-funds">
                    <option value="全部" />
                    {AETF_UNIVERSE.map((t) => (
                      <option key={t} value={t} />
                    ))}
                  </datalist>
                </div>
                <Matrix
                  columns={["基金", "持股", "名稱", "權重", "前日", "Δ"]}
                  align={["left", "left", "left", "right", "right", "right"]}
                  empty="無日持股源 · 不造假 · 僅 CACHE 三檔可篩"
                  rows={aetfDeltas.map((d) => [
                    d.fund,
                    d.stock,
                    d.name,
                    `${d.wgt.toFixed(1)}%`,
                    d.prev == null ? "—" : `${d.prev.toFixed(1)}%`,
                    d.dwgt == null ? "—" : `${d.dwgt > 0 ? "+" : ""}${d.dwgt.toFixed(1)}`,
                  ])}
                />
                <p className="font-mono text-xs text-subtle">右側對齊 LIVE LOG 欄寬 28% · 數字等寬右齊</p>
              </aside>
            </div>
            <Matrix
              columns={["燈", "層", "指標", "值", "註"]}
              rows={aetfRows.map((r) => [
                <StatusLight key={r.id} status={r.light} />,
                r.layer,
                r.metric,
                r.value,
                r.note,
              ])}
            />
          </CategoryBlock>

          <CategoryBlock title="持股 × Consensus · 單檔／總勾選" count={aetfHoldAgg.length} open={holdOpen} onToggle={() => setHoldOpen((v) => !v)}>
            {(() => {
              const k = holdKpis(aetfHoldAgg);
              const picksView = aetfFundPicks.filter((f) => aetfScope === "ALL" || f.scope === aetfScope);
              const nHold = picksView.filter((f) => f.hasHold).length;
              const nOn = aetfPicked.length;
              return (
                <>
                  <p className="font-mono text-xs text-subtle">
                    勾選 {nOn}/{nHold} 有持股 · 宇宙 29 · 封存 asOf 2026-08-29 · 估均價＝成本預估 · LIVE 關
                  </p>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-md bg-inset px-3 py-2">
                      <p className="text-xs uppercase tracking-wide text-subtle">N+1 本益</p>
                      <p className="font-mono text-lg tabular-nums">{k.pe}</p>
                    </div>
                    <div className="rounded-md bg-inset px-3 py-2">
                      <p className="text-xs uppercase tracking-wide text-subtle">加權成本損益</p>
                      <p className="font-mono text-lg tabular-nums text-ok">{k.wgtUp}</p>
                    </div>
                    <div className="rounded-md bg-inset px-3 py-2">
                      <p className="text-xs uppercase tracking-wide text-subtle">FS 偏保守列</p>
                      <p className="font-mono text-lg tabular-nums">{k.review}</p>
                    </div>
                  </div>
                  <div className="grid items-start gap-3 lg:grid-cols-[minmax(14rem,28%)_minmax(0,1fr)]">
                    <aside className="min-w-0 space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-xs font-medium uppercase tracking-wide text-subtle">基金勾選</p>
                        <div className="flex gap-1">
                          <Button size="sm" variant="outline" onClick={() => aetfPickAll()}>全</Button>
                          <Button size="sm" variant="outline" onClick={() => aetfPickNone()}>清</Button>
                        </div>
                      </div>
                      <ul className="max-h-80 space-y-1 overflow-y-auto pr-1">
                        {picksView.map((f) => (
                          <li key={f.ticker} className="flex min-h-11 items-center gap-2">
                            <Checkbox
                              checked={aetfPicked.includes(f.ticker)}
                              disabled={!f.hasHold}
                              onCheckedChange={() => toggleAetfPick(f.ticker)}
                              aria-label={f.ticker}
                            />
                            <span className="font-mono text-xs tabular-nums">{f.ticker}</span>
                            <span className="truncate text-xs text-muted">{f.name} · {f.issuer}{f.scope === "GL" ? " · 海外" : ""}</span>
                          </li>
                        ))}
                      </ul>
                    </aside>
                    <div className="min-w-0 space-y-2">
                      <p className="text-xs font-medium uppercase tracking-wide text-subtle">
                        {nOn <= 1 ? "單一 ETF 持股 × 成本預估" : "總勾選聚合 × 成本預估"}
                      </p>
                      <Matrix
                        columns={["#", "個股", "族群", "權重", "廣度", "動作", "估均價", "Adj", "FS 目標 Med", "FS +-%", "YF 目標 Med", "YF +-%"]}
                        align={["right", "left", "left", "right", "right", "left", "right", "right", "right", "right", "right", "right"]}
                        empty="無持股源 · 不造假 · 勾左側有持股檔或按 全"
                        rows={aetfHoldAgg.map((r, i) => [
                          i + 1,
                          `${r.name} ${r.stock}`,
                          r.group,
                          `${r.wgt.toFixed(1)}%`,
                          `${r.holdN}/${r.selN}`,
                          <Badge key={r.stock} tone={r.action === "超額配置" ? "warn" : r.action === "逢低承接" ? "run" : r.action === "單檔持有" ? "idle" : "ok"}>{r.action}</Badge>,
                          r.cost?.toFixed(1) ?? "—",
                          r.adj?.toFixed(1) ?? "—",
                          r.fsMedian?.toFixed(1) ?? "—",
                          <span key={`${r.stock}-fs`} className={`font-mono tabular-nums ${(fsUpside(r.adj, r.fsMedian) ?? 0) >= 0 ? "text-ok" : "text-bad"}`}>{formatPct(fsUpside(r.adj, r.fsMedian))}</span>,
                          r.yfMedian?.toFixed(1) ?? "—",
                          <span key={`${r.stock}-yf`} className={`font-mono tabular-nums ${(yfUpside(r.yfPx, r.yfMedian) ?? 0) >= 0 ? "text-ok" : "text-bad"}`}>{formatPct(yfUpside(r.yfPx, r.yfMedian))}</span>,
                        ])}
                      />
                    </div>
                  </div>
                </>
              );
            })()}
          </CategoryBlock>

          <CategoryBlock title="Dual Spectrum · 共識同一列" count={specRows.length} open={specOpen} onToggle={() => setSpecOpen((v) => !v)}>
            <p className="font-mono text-xs text-subtle">
              FactSet + YFinance 同一列 · TARGET＝Median · Mean 僅備註 · 樣本價 140 與 CNS 920 分列不混尺 · LIVE 關
            </p>
            <Matrix
              columns={SPEC_COLS}
              align={SPEC_COLS.map((c) => (c === "代號" || c === "Med 缺口" ? "left" : "right"))}
              empty="無共識列"
              rows={specRows.map((w) => spectrumCells(w))}
            />
          </CategoryBlock>

          <CategoryBlock title="VIA-CNS · FactSet × YFinance 台股共識 · VDF_ENG077" count={cnsLong.length} open={cnsOpen} onToggle={() => setCnsOpen((v) => !v)}>
            <p className="font-mono text-xs text-subtle">{cnsNote} · 公開 marketinfo · 不登入 · 長表 {cnsLong.length} · LIVE 雙閘才外呼</p>
            <div className="flex flex-wrap items-end gap-2">
              <div className="flex gap-1">
                <Button size="sm" variant={cnsMode === "GROUP" ? "default" : "outline"} onClick={() => setCnsMode("GROUP")}>
                  族群／個股
                </Button>
                <Button size="sm" variant={cnsMode === "ALL" ? "default" : "outline"} onClick={() => setCnsMode("ALL")}>
                  全部台股
                </Button>
              </div>
              <div className="min-w-[12rem] flex-1">
                <Label htmlFor="cns-q" className="text-xs uppercase tracking-wide text-subtle">代號或族群</Label>
                <Input
                  id="cns-q"
                  list="cns-groups"
                  value={cnsQuery}
                  onChange={(e) => setCnsQuery(e.target.value)}
                  placeholder="2330 或 半導體"
                  className="h-8 font-mono text-xs"
                  disabled={cnsMode === "ALL"}
                />
                <datalist id="cns-groups">
                  {universeGroups().map((g) => (
                    <option key={g} value={g} />
                  ))}
                </datalist>
              </div>
            </div>
            <Matrix
              columns={["燈", "層", "指標", "值", "註"]}
              rows={cnsRows.map((r) => [
                <StatusLight key={r.id} status={r.light} />,
                r.layer,
                r.metric,
                r.value,
                r.note,
              ])}
            />
            <Matrix
              columns={["燈", "代號", "指標", "FactSet", "YFinance", "差", "等級"]}
              rows={cnsCompare.map((r) => [
                <StatusLight key={`${r.code}-${r.metric}`} status={r.light} />,
                r.code,
                r.metric,
                r.fs == null ? "—" : String(r.fs),
                r.yf == null ? "—" : String(r.yf),
                r.pct == null ? "—" : `${(r.pct * 100).toFixed(1)}%`,
                r.grade,
              ])}
            />
            <Matrix
              columns={["編號", "資料結構", "倍數", "引擎", "說明"]}
              rows={CNS_STRUCT.map((r) => [r.id, r.strategy, r.gain, r.applies, r.note])}
            />
          </CategoryBlock>

          <CategoryBlock title="區域指數／ETF／商品／加密" count={marketRows.length} open={bookOpen} onToggle={() => setBookOpen((v) => !v)}>
            <p className="font-mono text-xs text-subtle">
              ETF AUM {etfFlow ? formatNum(etfFlow.aum) : "—"} mn · 流入 {etfFlow ? formatNum(etfFlow.inFlow) : "—"} · 流出 {etfFlow ? formatNum(etfFlow.outFlow) : "—"} · YF/AK 閘關走 CACHE · 流=Δunits×NAV
            </p>
            <Matrix
              columns={["燈", "區", "類", "名稱", "代號", "源", "價", "AUM mn", "1d流", "日"]}
              rows={marketRows.map((r) => [
                <StatusLight key="l" status={r.light} />,
                r.region,
                r.kind,
                r.name,
                r.ticker,
                r.sources,
                r.px,
                r.aumUsd ?? "—",
                r.flow1d ?? "—",
                r.asOf,
              ])}
            />
          </CategoryBlock>

          <section className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <ShieldCheck className="size-3.5 text-muted" />
              <h3 className="text-xs font-medium">分類摺疊矩陣</h3>
              <Badge tone="mute">{fredRows.length} series</Badge>
              {fredRows.length > 0 ? (
                <div className="ml-auto flex gap-2">
                  <Button size="sm" variant="ghost" data-action="vdf-expand" onClick={() => setCatsOpen(true)}>
                    全部展開
                  </Button>
                  <Button size="sm" variant="ghost" data-action="vdf-fold" onClick={() => setCatsOpen(false)}>
                    全部折疊
                  </Button>
                </div>
              ) : null}
            </div>
            {fredRows.length === 0 ? (
              <div className="rounded-md bg-surface px-4 py-10 text-center text-xs text-subtle shadow-[var(--shadow-border)]">
                尚未啟動
              </div>
            ) : (
              cats.map((cat) => {
                const rows = fredRows.filter((r) => r.category === cat);
                const open = !collapsed[cat];
                return (
                  <CategoryBlock key={cat} title={cat} count={rows.length} open={open} onToggle={() => toggleCat(cat)}>
                    <Matrix
                      columns={["燈", "系列", "名稱", "頻", "單位", "末日", "最新", "變化", "來源"]}
                      rows={rows.map((r) => [
                        <StatusLight key="l" status={r.status} />,
                        <span key="id" className="font-mono">
                          {r.seriesId}
                        </span>,
                        r.title,
                        r.frequency,
                        r.units,
                        <span key="d" className="tabular-nums">
                          {r.lastDate}
                        </span>,
                        <span key="v" className="tabular-nums">
                          {formatNum(r.lastValue)}
                        </span>,
                        <span key="c" className="tabular-nums">
                          {formatNum(r.change)}
                        </span>,
                        <Badge key="s" tone={r.source === "FRED_LIVE" ? "ok" : r.source === "DENIED" ? "warn" : "idle"}>
                          {r.source}
                        </Badge>,
                      ])}
                    />
                  </CategoryBlock>
                );
              })
            )}
          </section>

          <div className="flex flex-wrap gap-2">
            {vdfGov
              .filter((r) => r.key.includes("READY") || r.value.includes("READY"))
              .slice(0, 2)
              .map((r) => (
                <Badge key={r.key} tone={r.status}>
                  {r.value}
                </Badge>
              ))}
            {vdfFetchGov
              .filter((r) => String(r.value).includes("READY"))
              .slice(0, 2)
              .map((r) => (
                <Badge key={r.key} tone={r.status}>
                  {r.value}
                </Badge>
              ))}
          </div>

          <CategoryBlock title="控制器／契約" count={vdfGov.length + VDF_MODULES.length} open={govOpen} onToggle={() => setGovOpen((v) => !v)}>
            <div className="space-y-3">
              <p className="font-mono text-xs text-subtle">{celAegNote()}</p>
              <Matrix
                columns={["燈", "ID", "職", "檔", "勝", "註"]}
                rows={celAegRows().map((r) => [
                  <StatusLight key="l" status={r.light} />,
                  r.id,
                  r.role,
                  r.file,
                  r.winner,
                  r.note,
                ])}
              />
              <Matrix
                columns={["項", "值", "燈"]}
                rows={vdfGov.map((r) => [r.key, r.value, <Badge key={r.key} tone={r.status}>{r.status === "ok" ? "READY" : "缺實體"}</Badge>])}
              />
              <Matrix
                columns={["項", "值", "燈"]}
                rows={vdfFetchGov.map((r) => [r.key, r.value, <Badge key={r.key} tone={r.status}>OK</Badge>])}
              />
              <Matrix
                columns={["車道", "引擎", "計畫", "結果", "列", "說明"]}
                rows={
                  vdfLaneResults.length
                    ? vdfLaneResults.map((l) => [l.id, l.engine, vdfPlanLanes.find((p) => p.id === l.id)?.intended ?? "—", l.result, String(l.rows), l.note])
                    : vdfPlanLanes.length
                      ? vdfPlanLanes.map((p) => [p.id, p.engine, p.intended, "—", "—", p.reason])
                      : VDF_FETCH_LANES.map((l) => [l.id, l.engine, l.live ? "LIVE?" : "SKIP", "—", "—", l.note])
                }
              />
              {vdfManifest ? (
                <p className="font-mono text-xs text-subtle">
                  manifest · 網 {vdfManifest.network} · series {vdfManifest.series} · lake {vdfManifest.lakeRows} · skip {vdfManifest.skipLanes} · {vdfManifest.wallMs}ms
                </p>
              ) : null}
              <Matrix
                columns={["ID", "名稱", "車道", "閘", "狀態", "說明"]}
                rows={VDF_MODULES.map((m) => [
                  m.id,
                  m.name,
                  m.lane,
                  m.gate,
                  (m.gate === "fred" || m.lane === "macro") && fredRows.length ? <Badge tone="ok">本台已跑</Badge> : m.gate === "local-db" ? <Badge tone="warn">LOCAL</Badge> : <Badge tone="mute">契約</Badge>,
                  m.note,
                ])}
              />
              <h4 className="text-xs font-medium">本機 VIA_db · 原件不刪 · LAKE→LOCAL→CACHE→LIVE</h4>
              <Matrix
                columns={["燈", "ID", "名", "資料夾", "湖", "註"]}
                rows={viaDbRows().map((r) => [
                  <StatusLight key="l" status={r.light} />,
                  r.id,
                  r.name,
                  r.folder,
                  r.lake,
                  r.note,
                ])}
              />
            </div>
          </CategoryBlock>

          <section>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">掛載狀態 · 總線</h3>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {tools.map((t) => (
                <div key={t.id} className="flex items-start justify-between gap-3 rounded-md bg-surface p-3 shadow-[var(--shadow-border)]">
                  <div>
                    <p className="text-xs font-medium">{t.name}</p>
                    <p className="font-mono text-xs text-subtle">
                      {t.id} · {t.lane} · {t.version}
                    </p>
                    <p className="mt-1 text-xs text-muted">{t.note}</p>
                  </div>
                  <StatusLight status={t.status} />
                </div>
              ))}
            </div>
          </section>
        </TabsContent>

        <TabsContent value="tab2" hidden={vdfTab !== "tab2"}>
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">TAB 2 · PS Accel 20 搭配檢查</h3>
          <p className="mb-2 text-xs text-muted">缺前置的車道關閉，避免互相踩線。全開且 DAG 滿足才進加乘。</p>
          <Matrix
            columns={["燈", "ID", "名稱", "層", "搭配", "boost", "說明"]}
            rows={pairRows.map((r) => [
              <StatusLight key="l" status={r.status} />,
              r.id,
              r.name,
              r.layer,
              r.pairedWith,
              <span key="b" className="tabular-nums">
                {r.boost.toFixed(2)}
              </span>,
              r.reason,
            ])}
            empty="尚未啟動 · 啟動後寫入搭配矩陣"
          />
        </TabsContent>

        <TabsContent value="tab3" hidden={vdfTab !== "tab3"}>
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">TAB 3 · 列式湖契約</h3>
          <p className="mb-2 text-xs text-muted">
            年分區＋序列主序。落盤 compact（u16 日、u8 字典）不含 SIMD pad。母機 Polars／DuckDB 用同一契約。
          </p>
          <Matrix
            columns={["ID", "策略", "欄位", "加速器", "說明"]}
            rows={STRUCT_RULES.map((r) => [r.id, r.strategy, r.field, r.applies, r.note])}
          />
        </TabsContent>

        <TabsContent value="tab4" hidden={vdfTab !== "tab4"}>
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">TAB 4 · 加乘實測</h3>
          <p className="mb-2 text-xs text-muted">計畫加乘是相容車道 boost 乘積。wall／encode／query 是這次實測，不把行銷倍數當實測。</p>
          {fetchMetrics ? (
            <Matrix
              columns={["項", "值"]}
              rows={[
                ["計畫加乘", `×${fetchMetrics.planFactor}`],
                ["在位車道", `${fetchMetrics.active}/20`],
                ["衝突關閉", String(fetchMetrics.conflicts)],
                ["工作者池", String(fetchMetrics.concurrency)],
                ["管線並行", fetchMetrics.pipeline ? "開" : "關"],
                ["序列", String(fetchMetrics.series)],
                ["湖列數", String(fetchMetrics.lakeRows)],
                ["chunk", String(fetchMetrics.chunks)],
                ["minmax 跳過", `${fetchMetrics.skipped}（${Math.round(fetchMetrics.skipRatio * 100)}%）`],
                ["掃描列", String(fetchMetrics.scanned)],
                ["快取命中", String(fetchMetrics.cacheHits)],
                ["fetch ms", String(fetchMetrics.fetchMs)],
                ["encode ms", String(fetchMetrics.encodeMs)],
                ["query ms", String(fetchMetrics.queryMs)],
                ["wall ms", String(fetchMetrics.wallMs)],
                ["CPU ISA", fetchMetrics.isa],
                ["kernel", fetchMetrics.kernel],
                ["f64 寬度", String(fetchMetrics.f64Width)],
                ["i32 寬度", String(fetchMetrics.i32Width)],
                ["對齊", `${fetchMetrics.align}B`],
                ["phys 列（含 pad）", String(fetchMetrics.phys)],
                ["年分區", String(fetchMetrics.partitions)],
                ["落盤 compact", `${fetchMetrics.compactBytes} B`],
                ["parquet PAR1", `${fetchMetrics.parquetBytes} B · ${fetchMetrics.parquetPages} pages`],
                ["parquet 回讀", `${fetchMetrics.parquetReadPages} page · 跳過 ${fetchMetrics.parquetSkipPages}`],
                ["parquet 回讀對帳", fetchMetrics.parquetRoundtrip ? "一致" : "不一致"],
                ["token 比 JSON", String(fetchMetrics.parquetTokenRatio)],
                ["row object", `${fetchMetrics.rowBytes} B`],
                ["存量比", `${fetchMetrics.storeRatio}`],
                ["降頻風險", fetchMetrics.downclock ? "是 · 可退 AVX2" : "否"],
              ]}
            />
          ) : (
            <div className="rounded-md bg-surface px-4 py-10 text-center text-xs text-subtle shadow-[var(--shadow-border)]">
              啟動後寫入實測
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

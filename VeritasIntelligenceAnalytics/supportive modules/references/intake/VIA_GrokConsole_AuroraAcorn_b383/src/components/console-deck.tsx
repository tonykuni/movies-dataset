import { useEffect } from "react";
import { Activity, Cpu, FileSearch, LayoutGrid, Shield } from "lucide-react";
import { RightRail } from "@/components/right-rail";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LiveLog } from "@/components/live-log";
import { Matrix } from "@/components/matrix";
import { StatusLight } from "@/components/status-light";
import { countKind, countOk } from "@/lib/via/bus";
import { fredSample, isolateRows, tab2Sample, tab4Sample, vdfCloseSnap, vrnCloseSnap } from "@/lib/via/close-detail";
import { coordinateLayers, tri } from "@/lib/via/coordinate";
import { FETCH_PRIORITY, ingestPlan, viaDbRows } from "@/lib/via/via-db-parts";
import { ingestRunCommand, ingestRunNote } from "@/lib/via/via-ingest-ps";
import { govZoneRows, libTableHealth } from "@/lib/via/gov-env";
import { GOV_ACCEL, GOV_ROUNDS, LKGC_UV } from "@/lib/via/gov-spec";
import { GOV_TOOLS } from "@/lib/via/catalog";
import { GOV_LESSONS, runEnvManager } from "@/lib/via/env-manager";
import { runCentralEntry } from "@/lib/via/central-entry";
import { raceMirrors, runClashTools } from "@/lib/via/uv-clash";
import {
  GOV_MEGA_BIND,
  GOV_MEGA_PIPES,
  GOV_MEGA_PROMPT_ZH,
  GOV_MEGA_TITLE,
  GOV_MEGA_TITLE_EN,
  GOV_MEGA_WHEN,
  megaSeal,
} from "@/lib/via/gov-mega";
import {
  accelBindTable,
  accelBindSummary,
  envTable,
  HANDOVER_STAMP,
  jsLibTable,
  lockfileYml,
  moduleTable,
  scanEnvConflicts,
  toolTable,
} from "@/lib/via/inventory";
import { handoverPanorama, handoverReport } from "@/lib/via/autotest";
import { NPY_MEALS, npyPlanNote } from "@/lib/via/numpy-matrix";
import { vrnCompanyTp, vrnSsotNote, vrnSsotQc } from "@/lib/via/vrn-ssot";
import { VRN_LEX_FILLS } from "@/lib/via/vrn-lexicon";
import { vrnMethodNote, vrnMethodQc } from "@/lib/via/vrn-method";
import { vrnAnnByBlock, vrnDictNote, vrnDictQc, vrnExtTw } from "@/lib/via/vrn-dict";
import { vrnPipeNote, vrnPipeQc } from "@/lib/via/vrn-pipe";
import { VRN_CORE } from "@/lib/via/vrn-core";
import { gleQc } from "@/lib/via/vrn-layout";
import { xvalQc } from "@/lib/via/vrn-xval";
import { FOUR_POINT_SLOTS } from "@/lib/via/nlp-extract";
import { CNS_SEED } from "@/lib/via/consensus";
import { fwdQc } from "@/lib/via/fwd-vintage";
import { feQc, FE_STAGES } from "@/lib/via/vrn-four";
import { tickerFilenameQc } from "@/lib/via/tw-ticker";
import { TW_RX_REGISTRY, twRxQc } from "@/lib/via/tw-ticker-all";
import { COMPILE_SNAP, UPLOAD_NEED, UPLOAD_SKIP, compileNote, compileQc, compileRows, uploadGapQc } from "@/lib/via/compile-matrix";
import { celAegNote, celAegRows } from "@/lib/via/cel-aeg";
import { engineMountNote, engineMountQc, engineMountRows } from "@/lib/via/engine-mount";
import { ENV_BUILD_SLOTS, envBuildNote, envBuildQc, envSlotPinned } from "@/lib/via/env-build";
import { useVia } from "@/lib/via/store";
import type { Light } from "@/lib/via/types";

export function ConsoleDeck() {
  const setDeck = useVia((s) => s.setDeck);
  const bootGovern = useVia((s) => s.bootGovern);
  const activated = useVia((s) => s.activated);
  const engines = useVia((s) => s.engines);
  const tools = useVia((s) => s.tools);
  const confirmNet = useVia((s) => s.confirmNet);
  const confirmNlp = useVia((s) => s.confirmNlp);
  const fredRows = useVia((s) => s.fredRows);
  const basics = useVia((s) => s.basics);
  const finances = useVia((s) => s.finances);
  const files = useVia((s) => s.files);
  const summaries = useVia((s) => s.summaries);
  const fetchMetrics = useVia((s) => s.fetchMetrics);
  const aetfNote = useVia((s) => s.aetfNote);
  const cnsNote = useVia((s) => s.cnsNote);
  const cnsRows = useVia((s) => s.cnsRows);
  const revNote = useVia((s) => s.revNote);
  const revRows = useVia((s) => s.revRows);
  const autoRows = useVia((s) => s.autoRows);
  const handoverRows = useVia((s) => s.handoverRows);
  const handoverDay = useVia((s) => s.handoverDay);
  const isoSteps = useVia((s) => s.isoSteps);
  const isoScript = useVia((s) => s.isoScript);
  const mintIsolation = useVia((s) => s.mintIsolation);
  const runEnvManagerPlan = useVia((s) => s.runEnvManagerPlan);
  const pathScript = useVia((s) => s.pathScript);
  const busLogs = useVia((s) => s.busLogs);
  const runAutoTest = useVia((s) => s.runAutoTest);
  const runSeal = useVia((s) => s.runSeal);
  const goLiveRows = useVia((s) => s.goLiveRows);
  const procRows = useVia((s) => s.procRows);
  const liveSeal = useVia((s) => s.liveSeal);

  useEffect(() => {
    setDeck("console");
    bootGovern();
  }, [setDeck, bootGovern]);

  const vdfLight: Light = activated.vdf ? "ok" : "warn";
  const vrnLight: Light = activated.vrn ? "ok" : "warn";
  const engLight: Light = activated.engine ? "ok" : "warn";
  const varLight: Light = activated.var ? "ok" : "warn";
  const mega = megaSeal();
  const bind = accelBindSummary();
  const uvRace = raceMirrors();
  const uvClash = runClashTools();
  const envMgr = runEnvManager({ consent: false });
  const central = runCentralEntry({ consent: false });
  const layers = coordinateLayers({
    engineOk: engines.filter((e) => e.status === "ok").length,
    engineBad: engines.filter((e) => e.status === "bad").length,
    engineWarn: engines.filter((e) => e.status === "warn").length,
    activated: activated.vdf && activated.vrn && activated.engine && activated.var,
  });
  const vdfSnap = vdfCloseSnap({
    rows: fredRows,
    metrics: fetchMetrics,
    aetfNote,
    cnsNote,
    cnsN: cnsRows.length,
    revNote,
    revN: revRows.length,
    confirmNet,
  });
  const vrnSnap = vrnCloseSnap({ files, basics, summaries, finances, confirmNlp });

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-subtle">00 · 總管</p>
        <h1 className="text-lg font-semibold tracking-tight">VIA Central Governance Console · 中央唯一入口</h1>
        <p className="text-pretty text-sm text-muted">同一總管。衝突隔離 → 裝庫 → PATH。via_iso_* 不刪、不進 PATH。GitHub 上傳另腳本。</p>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" data-action="seal-run" onClick={() => void runSeal()}>
            實測完工
          </Button>
          <Button size="sm" variant="outline" onClick={() => runAutoTest()}>
            全日曆測
          </Button>
          {liveSeal ? <Badge tone={liveSeal.light === "ok" ? "ok" : liveSeal.light === "bad" ? "bad" : "warn"}>{liveSeal.note}</Badge> : <Badge tone="mute">尚未按實測完工</Badge>}
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Pillar icon={Activity} code="01" title="VDF" desc="湖／擷取" light={vdfLight} onOpen={() => setDeck("vdf")} />
        <Pillar icon={FileSearch} code="02" title="VRN" desc="研報／NLP" light={vrnLight} onOpen={() => setDeck("vrn")} />
        <Pillar icon={Cpu} code="03" title="引擎" desc="SSOT 在冊" light={engLight} onOpen={() => setDeck("engine")} />
        <Pillar icon={Shield} code="04" title="VAR" desc="審計／修復" light={varLight} onOpen={() => setDeck("var")} />
      </div>

      <section className="space-y-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">實測矩陣 · 封印</h3>
        <p className="font-mono text-xs text-subtle">六程同步 · 無九頭龍 · L2／L6 寫區互斥 · DCT 不動</p>
        <Matrix
          columns={["燈", "ID", "名", "註"]}
          empty="按「實測完工」"
          rows={goLiveRows.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.name,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">程序矩陣</h4>
        <Matrix
          columns={["燈", "ID", "系", "結果", "產出"]}
          empty="按「實測完工」"
          rows={procRows.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.system,
            r.result,
            r.out,
          ])}
        />
      </section>

      <section className="space-y-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">編譯矩陣 · 何者可編</h3>
        <p className="font-mono text-xs text-subtle">{compileNote()}</p>
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={compileQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "系", "名", "層", "可編", "註"]}
          rows={compileRows().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.system,
            r.name,
            r.tier,
            r.can ? "可" : "否",
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">還差上傳 · sha／v0114 閘鏈不要</h4>
        <p className="font-mono text-xs text-subtle">{`P1 先傳 · 清單沒有的先搜母機 · ${COMPILE_SNAP.when}`}</p>
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={uploadGapQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "P", "系", "檔", "清單", "註"]}
          rows={UPLOAD_NEED.filter((r) => r.pri <= 2).map((r) => [
            <StatusLight key="l" status={tri(r.attached ? "ok" : r.staged ? "ok" : r.listed ? "warn" : "bad")} />,
            String(r.pri),
            r.sys,
            r.file,
            r.attached ? "本台" : r.staged ? "TEMP" : r.listed ? "有列" : "沒有",
            r.why,
          ])}
        />
        <p className="font-mono text-xs text-subtle">{`SKIP ${UPLOAD_SKIP.join(" · ")}`}</p>
      </section>

      <section className="space-y-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">座標層 · GitHub × 母檔 × Data × via_*</h3>
        <Matrix
          columns={["燈", "層", "名稱", "GitHub", "PC", "註"]}
          rows={layers.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.layer,
            r.name,
            <span key="g" className="max-w-52 truncate font-mono text-xs">
              {r.github}
            </span>,
            <span key="p" className="max-w-56 truncate font-mono text-xs">
              {r.pc}
            </span>,
            r.note,
          ])}
        />
      </section>

      <section className="space-y-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">本機 VIA_db 三庫</h3>
        <Matrix
          columns={["燈", "ID", "名", "資料夾", "湖", "GitHub", "PC"]}
          rows={viaDbRows().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.name,
            r.folder,
            r.lake,
            <span key="g" className="max-w-52 truncate font-mono text-xs">
              {r.github}
            </span>,
            <span key="p" className="max-w-56 truncate font-mono text-xs">
              {r.pc}
            </span>,
          ])}
        />
        <h4 className="text-xs font-medium">擷取優先序</h4>
        <Matrix columns={["序", "層", "說明"]} rows={FETCH_PRIORITY.map((r) => [String(r.rank), r.tier, r.note])} />
        <h4 className="text-xs font-medium">COPY 計畫 · 2023–2026 · 母機執行</h4>
        <Matrix
          columns={["燈", "庫", "年", "動作", "目的", "註"]}
          rows={ingestPlan().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            String(r.year),
            r.action,
            <span key="d" className="max-w-64 truncate font-mono text-xs">
              {r.dest}
            </span>,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">母機 · {ingestRunNote()}</h4>
        <pre className="overflow-auto rounded-md bg-inset p-3 font-mono text-xs leading-relaxed text-muted shadow-[var(--shadow-border)]">
          {ingestRunCommand()}
        </pre>
        <p className="font-mono text-xs text-subtle">{`CMD 先 cd /d · 看到 PS> 再跑 Enter-Root 然後 Ingest · 原件只 COPY`}</p>
      </section>

      <section className="space-y-3" data-inventory="1">
        <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">開機盤點 · 模組／庫／工具／JS／環境</h3>
        <p className="font-mono text-xs text-subtle">
          {HANDOVER_STAMP.when} · {HANDOVER_STAMP.from} · 下一手 {HANDOVER_STAMP.next}
        </p>
        <h4 className="text-xs font-medium">模組表 · 同職 ALIAS 退下活路</h4>
        <Matrix
          columns={["燈", "ID", "系", "名稱", "註"]}
          rows={moduleTable(engines).map((r) => [
            <StatusLight key="l" status={tri(r.status)} />,
            r.id,
            r.kind,
            r.name,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">VDF 加速／網路正典 · {celAegNote()}</h4>
        <Matrix
          columns={["燈", "ID", "職", "檔", "勝", "註"]}
          rows={celAegRows().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.role,
            r.file,
            r.winner,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">引擎掛載 · {engineMountNote()}</h4>
        <Matrix
          columns={["燈", "項", "值", "註"]}
          rows={engineMountQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "ID", "編號", "加速器", "網路", "NLP", "類"]}
          rows={engineMountRows()
            .filter((r) => !r.aliased)
            .map((r) => [
              <StatusLight key="l" status={tri(r.light)} />,
              r.id,
              r.reg,
              r.accel,
              r.net,
              r.nlp,
              r.kind,
            ])}
        />
        <h4 className="text-xs font-medium">
          加速器綁定 · {bind.bound}/{bind.lanes} 綠 · 缺 {bind.miss}
        </h4>
        <Matrix
          columns={["燈", "ID", "名", "層", "工具", "缺"]}
          rows={accelBindTable().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.name,
            r.layer,
            r.tools,
            r.missing,
          ])}
        />
        <h4 className="text-xs font-medium">工具表</h4>
        <Matrix
          columns={["燈", "ID", "類", "名稱", "註"]}
          rows={toolTable().map((r) => [
            <StatusLight key="l" status={tri(r.status)} />,
            r.id,
            r.kind,
            r.name,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">JavaScript library 表</h4>
        <Matrix
          columns={["燈", "ID", "類", "名稱", "註"]}
          rows={jsLibTable().map((r) => [
            <StatusLight key="l" status={tri(r.status)} />,
            r.id,
            r.kind,
            r.name,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">環境／工具／LIBS 建構 · 鎖檔 CACHE · 不 spawn</h4>
        <p className="font-mono text-xs text-subtle">{envBuildNote()}</p>
        <Matrix
          columns={["燈", "ID", "項", "值", "註"]}
          rows={envBuildQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "槽", "Py", "PATH", "註"]}
          rows={ENV_BUILD_SLOTS.map((s) => [
            <StatusLight key="l" status={envSlotPinned(s.id) ? "ok" : "bad"} />,
            s.id,
            s.py,
            s.path ? "ON" : "OFF",
            s.note,
          ])}
        />
        <h4 className="text-xs font-medium">治理四分區 MODULE／ENGINE／FUNCTION-LIB／OTHERS</h4>
        <Matrix
          columns={["燈", "分區", "列", "註"]}
          rows={govZoneRows().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.zone,
            String(r.n),
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">uv 三鏡競向 · LKGC {LKGC_UV.when} · 不切鏡除非同意</h4>
        <Matrix
          columns={["燈", "序", "鏡", "ms", "職", "URL"]}
          rows={uvRace.rows.map((r) => [
            <StatusLight key="l" status={r.ok ? "ok" : "bad"} />,
            String(r.rank),
            r.id,
            String(r.ms),
            r.role === "winner" ? "冠" : r.role === "standby" ? "備" : "官",
            r.url,
          ])}
        />
        <p className="font-mono text-xs text-subtle">{uvRace.note}</p>
        <h4 className="text-xs font-medium">UVT-01–08 衝突快檢 · 從成功布局擴張</h4>
        <Matrix
          columns={["燈", "ID", "名", "層", "ms", "擊", "註"]}
          rows={uvClash.rows.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.name,
            r.layer,
            String(r.ms),
            String(r.hits),
            r.note,
          ])}
        />
        <p className="font-mono text-xs text-subtle">{uvClash.note}</p>
        <h4 className="text-xs font-medium">VIA_EnvManager · 從 LKGC 擴張 · 日誌當教訓</h4>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={envMgr.light === "ok" ? "ok" : "warn"}>{envMgr.id}</Badge>
          <Badge tone="mute">{envMgr.envs.length} 槽</Badge>
          <Button size="sm" data-action="env-plan" onClick={() => runEnvManagerPlan(false)}>
            擬計畫
          </Button>
          <Button size="sm" data-action="env-consent" onClick={() => runEnvManagerPlan(true)}>
            同意後產指令
          </Button>
        </div>
        <p className="font-mono text-xs text-subtle">{envMgr.plan}</p>
        <h4 className="text-xs font-medium">PATH 規劃 · 衝突解完才釘</h4>
        <Matrix
          columns={["燈", "槽", "職", "PATH", "註"]}
          rows={central.path.map((r) => [
            <StatusLight key="l" status={r.on ? "ok" : "idle"} />,
            r.id,
            r.role,
            r.on ? "ON" : "OFF",
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">右邊治理工具</h4>
        <Matrix
          columns={["燈", "ID", "名", "註"]}
          rows={GOV_TOOLS.map((r) => [
            <StatusLight key="l" status={tri(r.status)} />,
            r.id,
            r.name,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">GitHub 上傳 · VIA_GH_YES=1 才 push · 不 --force</h4>
        <pre className="max-h-48 overflow-auto rounded-md bg-inset p-3 font-mono text-xs leading-relaxed text-muted shadow-[var(--shadow-border)]">
          {central.github}
        </pre>
        <Matrix
          columns={["燈", "ID", "時", "教訓"]}
          rows={GOV_LESSONS.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.when,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">未來動作規範 · Mega-Prompt 已封 · {GOV_MEGA_WHEN}</h4>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={mega.light === "ok" ? "ok" : "bad"}>{mega.note}</Badge>
        </div>
        <p className="text-pretty text-xs text-muted">{GOV_MEGA_TITLE}</p>
        <p className="text-pretty text-xs text-subtle">{GOV_MEGA_TITLE_EN}</p>
        <p className="text-pretty text-xs text-muted">
          原文「拔除／重建」＝ via_iso_* 隔離不刪。DCT 不動。LIVE 雙閘。本台不 spawn conda／uv。
        </p>
        <Matrix
          columns={["燈", "ID", "原文", "綁定", "註"]}
          rows={GOV_MEGA_BIND.map((b) => [
            <StatusLight key="l" status={tri(b.light)} />,
            b.id,
            b.from,
            b.to,
            b.note,
          ])}
        />
        <h4 className="text-xs font-medium">六程 · G1–G6 寫區互斥</h4>
        <Matrix
          columns={["ID", "流程", "寫區", "贏家"]}
          rows={GOV_MEGA_PIPES.map((p) => [p.id, `P${p.pipeline} ${p.long}`, p.write, p.winner])}
        />
        <p className="text-pretty text-xs text-muted">三輪 {GOV_ROUNDS.map((r) => `R${r.id} ${r.name}`).join(" → ")}</p>
        <h4 className="text-xs font-medium">GA-01–20 治理加速器（與 PS-01–20 分冊）</h4>
        <div className="flex flex-wrap gap-1">
          {GOV_ACCEL.map((a) => (
            <Badge key={a.id} tone="mute">
              {a.id} {a.name}
            </Badge>
          ))}
        </div>
        <details className="rounded-md bg-inset p-3" data-mega="1">
          <summary className="cursor-pointer text-xs font-medium">原文 · 核心大腦指令</summary>
          <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words font-mono text-xs text-muted">
            {GOV_MEGA_PROMPT_ZH}
          </pre>
        </details>
        <h4 className="text-xs font-medium">函式庫釘裝（無遺漏）</h4>
        <Matrix
          columns={["燈", "ID", "套件", "註"]}
          rows={libTableHealth().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.id,
            r.name,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "環境", "類", "註"]}
          rows={envTable().map((r) => [
            <StatusLight key="l" status={tri(r.status)} />,
            r.id,
            r.kind,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">隔離政策 · 衝突件不刪</h4>
        <p data-iso="ISO99" className="font-mono text-xs text-subtle">
          ISO99 · via_iso_numpy · 隔離不刪套件 · 無名 orphan 從名冊刪
        </p>
        <h4 className="text-xs font-medium">NumPy 套餐矩陣</h4>
        <p className="text-pretty text-xs text-muted">{npyPlanNote()}</p>
        <Matrix
          columns={["燈", "套餐", "Py", "NumPy", "槽", "工具", "生成"]}
          rows={NPY_MEALS.map((m) => [
            <StatusLight key="l" status={tri(m.light)} />,
            m.meal,
            m.py,
            m.numpy,
            m.slot,
            <span key="t" className="max-w-72 text-pretty text-muted">
              {m.tools}
            </span>,
            m.spawn,
          ])}
        />
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" data-action="iso-mint" onClick={() => mintIsolation()}>
            產生隔離指令
          </Button>
          <Badge tone="warn">via_iso_numpy</Badge>
          <Badge tone="warn">{scanEnvConflicts().map((c) => c.isolate).join(" · ") || "無衝突"}</Badge>
        </div>
        <Matrix
          columns={["燈", "步", "指令", "註"]}
          rows={isoSteps.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            `${r.id} ${r.title}`,
            <span key="c" className="max-w-72 truncate font-mono text-xs">
              {r.cmd}
            </span>,
            r.note,
          ])}
          empty="按「產生隔離指令」"
        />
        {isoScript ? (
          <pre className="max-h-40 overflow-auto rounded-md bg-inset p-3 font-mono text-xs text-muted">{isoScript}</pre>
        ) : null}
        {pathScript ? (
          <pre className="max-h-40 overflow-auto rounded-md bg-inset p-3 font-mono text-xs text-muted">{pathScript}</pre>
        ) : null}
        <details className="rounded-md bg-inset p-3">
          <summary className="cursor-pointer text-xs font-medium">via_vdf 鎖檔預覽</summary>
          <pre className="mt-2 max-h-40 overflow-auto font-mono text-xs text-muted">{lockfileYml("via_vdf")}</pre>
        </details>
      </section>

      <section className="space-y-2">
        <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">收關矩陣 · VDF / VRN</h3>
        <p className="text-pretty text-xs text-muted">{vrnSsotNote()}</p>
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={vrnSsotQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["代碼", "券商", "目標價 MEDIAN", "原列", "檔"]}
          rows={vrnCompanyTp().map((r) => [
            r.ticker,
            r.broker,
            r.median.toFixed(r.median % 1 ? 1 : 0),
            r.prices.join(";"),
            r.doc,
          ])}
          empty="無公司目標價"
        />
        <p className="text-pretty text-xs text-muted">{vrnMethodNote()}</p>
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={vrnMethodQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["節點", "中", "英（候審）"]}
          rows={VRN_LEX_FILLS.map((r) => [r.node, r.zh, r.en])}
        />
        <p className="text-pretty text-xs text-muted">{vrnDictNote()}</p>
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={vrnDictQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["報表", "欄數"]}
          rows={Object.entries(vrnAnnByBlock()).map(([k, n]) => [k, String(n)])}
        />
        <p className="text-pretty text-[10px] text-muted">臺券 {vrnExtTw().join("／")}</p>
        <p className="text-pretty text-xs text-muted">{vrnPipeNote()}</p>
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={vrnPipeQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["模組", "職", "NLP", "NET"]}
          rows={VRN_CORE.map((m) => [m.id.replace("VRN_", ""), m.name, m.nlp ? "CACHE" : "—", m.net ? "閘" : "—"])}
        />
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={gleQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">檔名 ticker SSOT · 年碼不剔除真碼</h4>
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={tickerFilenameQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <h4 className="text-xs font-medium">TW regex v0100 · 13 類只增不減</h4>
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={twRxQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["class", "類別", "第六碼", "例"]}
          rows={TW_RX_REGISTRY.map((r) => [r.cls, r.zh, r.sfx, r.sample])}
        />
        <Matrix
          columns={["點", "DIGEST", "中"]}
          rows={FOUR_POINT_SLOTS.map((s) => [s.id, s.digest, s.zh])}
        />
        <Matrix
          columns={["代碼", "FS中位", "YF中位", "FS評", "YF評"]}
          rows={CNS_SEED.slice(0, 6).map((s) => [
            s.code,
            String(s.medianFs ?? "—"),
            String(s.medianYf ?? "—"),
            s.ratingFs ?? "—",
            s.ratingYf ?? "—",
          ])}
        />
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={xvalQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={fwdQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "指標", "值", "註"]}
          rows={feQc().map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <p className="text-[10px] text-muted">四引擎 {FE_STAGES.join(" → ")} · 不覆寫舊 BATCH</p>
        <Matrix
          columns={["燈", "層", "指標", "值", "註"]}
          rows={vdfSnap.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.layer,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "樣本"]}
          rows={fredSample(fredRows).map((r) => [<StatusLight key="l" status={tri(r.light)} />, r.cells.join(" · ")])}
        />
        <Matrix
          columns={["燈", "層", "指標", "值", "註"]}
          rows={vrnSnap.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.layer,
            r.metric,
            r.value,
            r.note,
          ])}
        />
        <Matrix
          columns={["燈", "TAB2"]}
          rows={tab2Sample(basics).map((r) => [<StatusLight key="l" status={tri(r.light)} />, r.cells.join(" · ")])}
        />
        <Matrix
          columns={["燈", "TAB4"]}
          rows={tab4Sample(finances).map((r) => [<StatusLight key="l" status={tri(r.light)} />, r.cells.join(" · ")])}
        />
        <Matrix
          columns={["燈", "層", "名", "值", "註"]}
          rows={isolateRows(engines).map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.layer,
            r.metric,
            r.value,
            r.note,
          ])}
        />
      </section>

      <section className="space-y-2">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">隔日接手 · {handoverDay}</h3>
          <Button size="sm" onClick={() => runAutoTest()}>
            全日曆測
          </Button>
        </div>
        <Matrix
          columns={["燈", "系統", "今夜", "明日接手", "阻塞", "指令"]}
          rows={handoverRows.map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.system,
            r.tonight,
            r.tomorrow,
            <span key="b" className="max-w-72 text-pretty text-muted">
              {r.blocker}
            </span>,
            <span key="c" className="font-mono text-xs">
              {r.cmd}
            </span>,
          ])}
          empty="按全日曆測"
        />
        <h4 className="text-xs font-medium">全景交接 · AEA／GIT／ENV／PATH／SEAL</h4>
        <Matrix
          columns={["燈", "系", "今夜", "明日接手", "阻塞", "指令"]}
          rows={handoverPanorama(handoverDay).map((r) => [
            <StatusLight key="l" status={tri(r.light)} />,
            r.system,
            r.tonight,
            r.tomorrow,
            <span key="b" className="max-w-72 text-pretty text-muted">
              {r.blocker}
            </span>,
            <span key="c" className="font-mono text-xs">
              {r.cmd}
            </span>,
          ])}
        />
        <pre className="max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-md bg-inset p-3 font-mono text-xs leading-relaxed text-muted shadow-[var(--shadow-border)]">
          {handoverReport(handoverDay, handoverRows)}
        </pre>
      </section>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_240px]">
        <div className="min-w-0 space-y-4">
          <section className="space-y-2">
            <div className="flex items-center gap-2">
              <LayoutGrid className="size-4 text-muted" />
              <h3 className="text-sm font-medium">總管整合矩陣</h3>
            </div>
            <Matrix
              columns={["燈", "柱", "模組", "啟動", "共用資源", "產出"]}
              rows={[
                [
                  <StatusLight key="l" status={vdfLight} />,
                  "01",
                  "VDF",
                  activated.vdf ? "已啟動" : "黃待協調",
                  `ACCEL ${countOk(tools, "accel")}/${countKind(tools, "accel")} · NET ${countOk(tools, "net")}/${countKind(tools, "net")}`,
                  `${fredRows.length} series`,
                ],
                [
                  <StatusLight key="l2" status={vrnLight} />,
                  "02",
                  "VRN",
                  activated.vrn ? "已啟動" : "黃待協調",
                  `NLP ${countOk(tools, "nlp")}/${countKind(tools, "nlp")}`,
                  `INFO ${basics.length} · FIN ${finances.length}`,
                ],
                [
                  <StatusLight key="l3" status={engLight} />,
                  "03",
                  "引擎 SSOT",
                  activated.engine ? "在冊" : "黃待協調",
                  `NET ${confirmNet ? "開" : "黃"} · NLP ${confirmNlp ? "開" : "黃"}`,
                  `${engines.length} 列`,
                ],
                [
                  <StatusLight key="l4" status={varLight} />,
                  "04",
                  "VAR",
                  activated.var ? "已啟動" : "黃待協調",
                  "AUDIT / REPAIR",
                  "收官列",
                ],
              ]}
            />
          </section>

          <section className="space-y-2">
            <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">全日曆測列</h3>
            <Matrix
              columns={["燈", "ID", "系", "名", "週期", "結果"]}
              rows={autoRows.map((r) => [
                <StatusLight key="l" status={tri(r.light)} />,
                r.id,
                r.system,
                r.name,
                r.cycle,
                <span key="r" className="max-w-56 truncate text-muted">
                  {r.result}
                </span>,
              ])}
              empty="左側全日曆測"
            />
          </section>

          <section className="space-y-2">
            <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">啟動 PowerShell</h3>
            <pre className="overflow-auto rounded-md bg-inset p-3 font-mono text-xs leading-relaxed text-muted shadow-[var(--shadow-border)]">
              {`# 已在 PS 母目錄。scripts\\ 檔不在這台。
# 貼 VIA-CmdMatrix.ps1 整段後：
via-enter
via-matrix
via-ingest`}
            </pre>
          </section>
          <LiveLog lines={busLogs} />
        </div>
        <RightRail engines={engines} day={handoverDay} />
      </div>
    </div>
  );
}

function Pillar({
  icon: Icon,
  code,
  title,
  desc,
  light,
  onOpen,
}: {
  icon: typeof Activity;
  code: string;
  title: string;
  desc: string;
  light: Light;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex items-start gap-3 rounded-md bg-inset p-3 text-left shadow-[var(--shadow-border)]"
    >
      <Icon className="mt-0.5 size-4 text-muted" />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2">
          <StatusLight status={tri(light)} />
          <span className="font-mono text-[11px] text-subtle">{code}</span>
          <span className="text-sm font-medium">{title}</span>
        </span>
        <span className="mt-1 block text-xs text-muted">{desc}</span>
      </span>
    </button>
  );
}

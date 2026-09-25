# VIA Central Government · Adaptive Downstream v0100 驗證報告

## def 驗證範圍

本輪以目前提供的 8 個 VIA 核心資產建立隔離副本進行三輪驗證；這不是使用者 Windows Mother Root 全目錄掃描，因此數量只代表本次樣本。

## def 結果

- Gate：`HOLD_REMEDIATION_REQUIRED`（Fail-Closed；不是引擎執行失敗）
- Assets：8；Open Issues：55；Unresolved High：22
- Overlay 修正：2；Contract Sidecars：8
- Dependency Cycles：1；Interface References：21
- Adaptive DEEP：7 / 8
- Canonical Mutation：False；Network：False；Target Import：False；Activation：NOT_ACTIVATED

## def 測試

- Python self-test：8/8 PASS
- Python `py_compile`：新引擎 + 7 個 Python 核心檔 PASS
- Policy / Capabilities JSON：PASS
- Canonical SHA-256：8/8 測試前後一致
- PowerShell：靜態括號、禁用指令與網路指令掃描 PASS；此 Linux 驗證環境沒有 PowerShell 7。啟動器已內建 `Parser.ParseFile`，在 Windows PowerShell 7 執行時會先完成原生 AST 自檢，通過後才啟動治理。

## def P1/P2 修正順序

### P1 · VCG-F001 · Aegis ↔ SSOT 循環相依與 self-import

證據：VeritasAegisNexus.py:140 from VeritasAegisNexus import *；VIA_SSOT_Unified.py:116 import VIA_SSOT_Unified；dependency cycle Aegis → SSOT → Aegis。

處置：先移除 self-import，再以 Runtime Context/Registry 注入對端能力；兩檔不得互相在 module scope eager import。

### P1 · VCG-F002 · Celeritas 頂層使用尚未定義的 Lazy Loader

證據：_LazyModule/_spec_exists used at lines 86/91/96; definitions near lines 384/373。

處置：把 lazy-loader 定義移到 support bootstrap 前，或將 peer module 綁定延後至 def_bootstrap_runtime；禁止以 broad except 靜默吞掉。

### P1 · VCG-F003 · Runtime Bridge 呼叫不存在的 xbatch 契約

證據：ctx.celeritas.xbatch referenced at lines 271–272；VeritasCeleritas exports do not include xbatch。

處置：由 SSOT 契約決定 canonical API：新增相容 xbatch adapter，或將 Bridge 改綁現有 batch API；先做 consumer/producer contract test。

### P1 · VCG-F004 · Mother Root 與 runtime path 仍綁定 OneDrive／/mnt/data／版本檔名

證據：13 PATH_HARDCODED_EXTERNAL_ROOT findings。

處置：改由 Central Root Resolver + Registry ID + Env alias 動態解析；保留舊路徑只作 migration candidate，不得作 active authority。

### P1 · VCG-F005 · SSOT Regex 規則與自帶 examples 不一致

證據：TW_STOCK_CODE_4DIGIT misses pass 0050；TW_STOCK_CODE_4DIGIT matches fail 12345；TABLE_HEADER_BALANCE_SHEET misses Equity；HTML_ANTI_BOT_SIGNAL misses verify you are human。

處置：先由 SSOT owner 決定 0050 是否屬股票/ETF共同代碼契約，再修 pattern 與 examples；加入 corpus unit test 作 Gate。

### P1 · VCG-F006 · Dashboard 真實 DOM ID 重複

證據：cmdBody duplicated；legoBody duplicated。

處置：依頁面/模組命名空間改為唯一 ID，更新所有 querySelector/getElementById 引用後跑 UI wiring test。

### P1 · VCG-F007 · Aegis 缺少兩個本地依賴

證據：VIA_SafeFix_PathRegistry not found；VIA_SuperAccel_Module not found。

處置：不得猜測同名版本；由 Registry 查唯一 canonical owner，若無 owner 則標記 optional capability 並提供明確 fallback contract。

### P2 · VCG-F008 · Broad except/pass 與 import-time side effects 降低可觀測性

證據：6 PY_BROAD_EXCEPT_PASS findings；3 PY_IMPORT_TIME_SIDE_EFFECT findings。

處置：將 bootstrap 轉成顯式 setup(ctx)；except 必須寫 evidence/error_code，禁止無聲降級。

## def 安全 Overlay

- `VIA_Panorama_AST_RuntimeInjector.py`：FMT_MIXED_NEWLINES；PASS_PY_COMPILE；canonical 未改。
- `VPN_v35_Dashboard (3).html`：FMT_FINAL_NEWLINE；PASS_TEXT_ROUNDTRIP；canonical 未改。
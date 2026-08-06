# VIA Industry Forecast · P1 Safe Master Launcher — README v0100

**一支 PowerShell 啟動全部** · read-only 探索 · append-only 輸出 · 不執行你的目標腳本 · 不動 canonical

## 三個檔(放同一資料夾)
| 檔 | 角色 |
|---|---|
| `via_if_activate.ps1` | 單一入口 master launcher(PS7)。路徑探索 + 目錄 scaffold + 部署 + 跑引擎 + 開 HTML |
| `via_if_engine.py` | 安全全景引擎。read-only 掃描 + auto-ID/alias/evidence registry + 模組綁定 + 15 accelerator 分析 + RYG HTML matrix |
| `via_if_config.json` | 全參數。roots / module_bindings(CodexNexus=fetch)/ opex_policy(Conservative)/ factor / alias / universe |

## 執行(PowerShell 7)
把三個檔放進 `C:\Users\tonyk\Downloads\` 任一資料夾,然後:
```powershell
cd <放三個檔的資料夾>
.\via_if_activate.ps1
```
可選參數:
```powershell
.\via_if_activate.ps1 -Base "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" -PythonExe "C:\Users\tonyk\envs\via_core\Scripts\python.exe" -TimeoutSeconds 900
.\via_if_activate.ps1 -NoOpen      # 不自動開 HTML
```
引擎可獨立自測:
```powershell
python .\via_if_engine.py --selftest
```

## 它會做什麼(P1)
1. 用 Windows I/O 找到 base(預設 `...\Downloads\VeritasIntelligenceAnalytics`)。
2. 在 base 下 scaffold `VIA_IndustryForecast\00_config … 08_docs`(已存在則不覆蓋)。
3. append-only 部署引擎與 config 到 `01_engines` / `00_config`。
4. 跑引擎:read-only 掃描整棵樹 → 分類 layer/role/risk → AST → anchor → 15 accelerator pass。
5. 綁定既有模組角色:**`Invoke-VeritasCodexNexus.ps1` = fetch_engine**、`VIA_SSOT_Unified.py`/`VIA_RegistryCore_v1.py` = ssot_core、governance / env / runtime_bridge / registries…(只確認存在,**P1 不執行**)。
6. 發 VIA 內部自動編號(`VIA-ENG/ACT/UI/CFG/DOC/... -YYYYMMDD-######`,append-only 不重編)。
7. 外部代號(SAP / MS-PM / 股票三碼 / 商品)寫 alias registry,全部 `can_modify=false`。
8. 產出 `07_runs\RUN_*\VIA_IF_SafePanorama_Matrix.html`(FlowSystem 風格 RYG matrix)+ CSV/JSON(+Parquet 若有 pyarrow)。
9. 開 HTML matrix。

## 安全界線(重要)
- **不執行**你的 supportive/functional 腳本;只跑本套件自己的 Python 引擎。
- 修正一律 **proposal-only** 寫進 `via_optimization_proposals.csv`;高風險節點只建議,不自動改 → 走你的核可制。
- canonical 不覆寫;每次 run 是新的時間戳資料夾。

## 下一步(P2,需要你提供)
實際呼叫 `Invoke-VeritasCodexNexus.ps1` 抓資料,需要它的 **param 區塊 / CLI 參數**。給我之後,我把 fetch adapter 接上(config 已預留 `invoke_template` 與 `execute_in_p1` 開關)。

---
*Policy: READ_ONLY_NO_TARGET_EXECUTION_APPEND_ONLY_NO_CANONICAL_MUTATION · VersionDate 20260702*

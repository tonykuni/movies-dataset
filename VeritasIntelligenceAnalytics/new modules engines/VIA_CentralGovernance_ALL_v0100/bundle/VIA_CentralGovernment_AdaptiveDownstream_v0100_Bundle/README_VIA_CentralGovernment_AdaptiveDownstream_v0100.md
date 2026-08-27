# VIA Central Government · Adaptive Downstream Governance v0100

## def 定位

本套件把 VIA Central Governance 從「盤點／註冊／啟動橋接」補強為可向下遞迴的治理閉環：

`發現 → 靜態分析 → 契約推斷 → 相依圖 → Hydra／漂移偵測 → 安全 overlay → 沙盒驗證 → 再分析 → Gate 裁決`

它只讀 canonical。任何修正都寫入每次執行專屬的 run-local overlay，不會覆蓋、刪除、重新命名或啟用正式來源。

## def 核心能力

1. **六條獨立治理 Lane**：AST、SSOT/Contract、Dependency/Route、Hydra/Identity、Security、Quality。PowerShell 啟動器會在任何治理動作前先用原生 `Parser.ParseFile` 驗證自身 AST。
2. **三輪上限**：第一輪只處理平行安全修正；第二輪依相依順序產生契約 sidecar 與修復計畫；第三輪重新驗證並裁決 Gate。
3. **向下自適應深度 A08**：依風險分數、入口角色及相依扇入／扇出，自動選擇 LIGHT／STANDARD／DEEP，向下追蹤 1／3／5 層。
4. **失敗斷路器 A15**：同一資產連續三次存在 HIGH／CRITICAL 問題時，自動停止自修並轉 `HUMAN_REVIEW_ONLY`。
5. **跨模組介面契約**：檢查 Runtime Bridge 對 EnvManager、Registry、SSOT、Aegis、Celeritas 的方法引用是否存在。
6. **Hash 冪等**：原始 Hash、契約 Hash、語意 Hash、overlay proposed Hash 與 append-only ledger 全數保留。
7. **HTML RYG 矩陣**：每輪都輸出 Error、Optimization、Hydra、Dependency、Cycle、Interface、Fix Order、Adaptive Depth、Circuit Breaker、SSOT 與數量驗證。

## def 單一 PowerShell 執行

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& "C:\你的套件路徑\Invoke-VIA-CentralGovernment-AdaptiveDownstream-v0100.ps1"
```

指定母檔與模式：

```powershell
& "C:\你的套件路徑\Invoke-VIA-CentralGovernment-AdaptiveDownstream-v0100.ps1" `
  -Root "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" `
  -Mode STAGE `
  -MaxWorkers 12 `
  -MaxDepth 24
```

`AUDIT` 僅分析；`STAGE` 允許四類白名單格式修正寫入 overlay。兩種模式都不會修改 canonical，也不會自動 Activation。

## def Python 直接執行

```powershell
python .\VIA_CentralGovernment_AdaptiveDownstream_v0100.py selftest
python .\VIA_CentralGovernment_AdaptiveDownstream_v0100.py capabilities
python .\VIA_CentralGovernment_AdaptiveDownstream_v0100.py run `
  --root "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" `
  --output-root "$env:LOCALAPPDATA\VIA\CentralGovernanceRuns" `
  --mode STAGE `
  --rounds 3
```

## def Gate 解讀

- `HOLD_REMEDIATION_REQUIRED`：偵測到尚未解決的 HIGH／CRITICAL 問題；這是 fail-closed 的正常安全結果，不等於引擎失敗。
- `READY_FOR_MANUAL_USER_TEST_REVIEW`：靜態、契約、相依與沙盒驗證未留下 HIGH／CRITICAL 問題，但仍未 Activation。
- 本引擎不會輸出 `ACTIVATED`；正式啟用必須由另一個經簽核的控制面執行。

## def 輸出結構

```text
RUN_<timestamp>_VIA_CentralGovernment_AdaptiveDownstream_v0100/
├─ round_1/                         # JSON / CSV / HTML
├─ round_2/                         # JSON / CSV / HTML
├─ round_3/                         # 最終 JSON / CSV / HTML
├─ overlay/round_1/                 # copy-on-write 修正副本
├─ contracts/                       # inferred contract sidecars
├─ plans/                           # dependency / path / fix-order plans
├─ event_ledger.jsonl               # append-only 事件證據
├─ hash_ledger.json                 # original/proposed hash
├─ baseline.json                    # 下次增量掃描與斷路器基準
└─ VIA_CG_Adaptive_Summary.json
```

## def 明確不執行

不連網、不安裝套件、不 rebuild 環境、不 import 被掃描模組、不 dot-source PowerShell、不刪除、不改名、不覆寫 canonical、不自動啟用、不自動處理高風險 Hydra。

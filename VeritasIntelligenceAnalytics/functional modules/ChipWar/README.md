# VIA ChipWar — 台股籌碼戰/資金盤市場情報引擎家族

2026-08-10 歸檔（操作員令:new engine）。上傳批次 17+5 檔經逐位元裁定後歸檔於此;
運算邏輯零觸碰,僅補丁路徑常數(見各引擎頭部歸檔註記與原始 sha256)。

## 依賴鏈(via_test_harness.py 契約)

```
chipwar(鏈頭) → macro → {bloc, social} → {fomo_index, xmkt} → 三報告
獨立:sector_rotation(輪動剔除) · VIA_GovFundEngine_v040(護盤偵測) · globalflow(未上傳)
```

**⚠ 鏈頭現況**:真正的 `via_chipwar_engine.py` 未在上傳批次中。現行檔案為依 harness
I/O 契約重建之 **T4 佔位鏈頭**(合成宇宙 duckdb + regime;頭部有大字標示)。依 SSOT
治理 T4 = pipeline 測試專用、**絕不得進入實盤決策**。真鏈頭到位後 version-forward
取代該檔即可,下游十支零改動。`via_globalflow_engine.py` 同樣未上傳,harness 對其
誠實 SKIP。

## 一鍵執行(經 VIA_WorkflowEngine master 動詞)

```powershell
# repo 根目錄
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 master "VeritasIntelligenceAnalytics\functional modules\ChipWar\chipwar_params.json" --dry-run   # 預覽 12 階段
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 master "VeritasIntelligenceAnalytics\functional modules\ChipWar\chipwar_params.json"             # 全鏈執行
```

產物落 `_generated/`(gitignored,可再生):`staging/*.json` + `staging/ssot_chipwar.duckdb`
+ `reports/*.html`(Visual Lock)+ `staging/_test_matrix.json`(harness 驗收矩陣)。
路徑可用環境變數 `VIA_CHIPWAR_STAGING` / `VIA_CHIPWAR_REPORTS` 覆寫。

首跑驗收(2026-08-10 本容器):**11/11 階段 SUCCESS · harness verdict ALL_PASS**
(L1 六引擎 clean · L2 方法論斷言 8/8 · globalflow SKIP)。加入 govfund 後為 12 階段。

## 目錄

| 位置 | 內容 |
|---|---|
| `ssot/` | SSOT_ChipWar_Schema.json v0.12.0(27 表 · 37 魔鬼條款 · T1-T4 證據分級)· tw_investor_taxonomy v1.2 · tw_market_monitor_architecture |
| `engines/` | 鏈頭(T4 佔位)+ macro/bloc/social/fomo_index/xmkt 五 lane + 三報告 + rotation + GovFund v040 + test harness |
| `chipwar_params.json` | master 動詞參數檔(12 階段 · stop_on_error) |
| `VIA_ChipWar_Panorama_全景現況.html` | 全景快照(靜態參考文件) |

## 依賴

`pip install numpy pandas scipy duckdb scikit-learn statsmodels`(rotation 需 sklearn;
其餘 lane 需 duckdb+scipy)。缺席時各階段誠實 FAIL,stop_on_error 即止。

## 裁定紀錄(2026-08-10 批次)

- 三份 SSOT_ChipWar_Schema、兩份 taxonomy、兩份 fomo 引擎:各組**逐位元相同**,唯一版本歸檔
- sector_rotation 兩次上傳:逐位元相同
- VIA_FIS_Validation_v3_1 / VIA_FIS_Backtest_Harness_1:與 `supportive modules/VIA_FlowSystem/`
  正本逐位元相同,且已載於 audit_tools/VIA_FIS_Family_Dedup_Record_v0100.json — 零動作

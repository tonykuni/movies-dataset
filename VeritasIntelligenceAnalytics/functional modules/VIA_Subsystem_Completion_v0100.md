# VIA 子系統補完報告 v0100(VAP / VDF / VRN)

日期:2026-08-31 · 前提:GroupIndex 已依指示擱置(歷史保留於 `a78706a`)。
四份上傳元件全部歸戶完成;三子系統以各自測試面驗證並修復。

## def 元件歸戶

| 上傳元件 | 歸戶 | 驗證 |
| --- | --- | --- |
| forward_valuation_vintage_v2.py | **VDF/engine/**(估值錨屬資料鑄造域) | `--self-test` status=pass(含 pandas 3.x merge_asof dtype 修復) |
| VIA_Hybrid_TW_Flow_Engine v1.5.0 | **VDF/FinMind_TW_Flow_Engine/**(TW 官方+FinMind 入庫 canonical) | unittest **33/33**(含 VeritasCeleritas F821 修復) |
| VUSIPE v0100 FINAL | supportive modules(既有,免搬) | pytest 26/26 |
| MarkdownEditingEngine v1.2.0 FINAL | supportive modules(既有,免搬) | MANIFEST 34/34 |

## def 子系統驗證矩陣

| 子系統 | 編譯閘 | 測試面 | 結果 | 修復 |
| --- | --- | --- | --- | --- |
| **VAP** | 13/13 | v025 套件測試(靜態+runtime+node core) | **17/17 PASS**;40 圖 canon 與 v018 同套 | — |
| **VDF** | 53/53 | MDL105 CrossValidator selftest(238 registry items/8 驗證/5 共識法+紅黃綠燈)+ 歸戶雙元件 | **PASS** | MDL105 registry 路徑改候選解析(cwd → canonical `supportive modules/registry`,零複製) |
| **VRN** | 81/81 | VIA_HardGate_BootPrecheck | exit 0,seal=**PARTIAL**(沙盒無 OCR 運行時,n_loaded=0 屬誠實依賴閘;本機 Paddle 環境可轉滿封) | `comprehensive_pdf_extractor (1)`:f-string 反斜線(3.12-only)→ 先算後嵌恢復 3.9+ 相容 |

## def 修復帳(本輪)

1. `VDF/VDF_MDL105_CrossValidator.py`:selftest 寫死 cwd 相對 registry → 候選解析(本機慣用 cwd 優先、canonical 備援)。
2. `VRN/comprehensive_pdf_extractor (1)_sha72238d6aa40a.py`:f-string 運算式含反斜線,Python 3.11 語法錯誤 → 提出變數;並修正縮排至方法層。
3. 歸戶自 GroupIndex 歷史取回之兩元件保留先前修復(pandas ns 鎖定、Celeritas 惰性載入)。

## def 遺留(需本機執行,沙盒無法代驗)

- VDF MDL001 TWEquityEngine / MDL302 FinalActivation:live 引擎,無離線 selftest;由編譯閘 + 本機啟動流程涵蓋。
- VRN OCR 引擎群:依賴 PaddleOCR 等本機運行時;HardGate 會在載入後自動轉滿封。

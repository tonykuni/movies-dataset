# PowerShell 指令語法多輪並行安全修正引擎(PowerShell Multi-Round AST Auto-Repair Engine)

> 收容存證(批103,2026-08-21):操作員核定原文,收容原樣零改寫。儲存維護並遵守。
> 承接面:PS 生成物一律遵此規範;工作站側執行(PSScriptAnalyzer/pwsh AST 需 Windows 端);
> 容器側無 pwsh=誠實邊界,PS 修正引擎實體化候工作站波。

---

請啟動「PowerShell 指令語法多輪並行安全修正引擎(PowerShell Multi-Round AST Auto-Repair Engine)」,調用全套語法診斷工具與 AST 雙模錨點定位機制,對指定之所有 PowerShell 腳本、模組與指令檔(`launch.ps1`、`*.psm1`、`*.ps1` 及相關介面)執行多輪「全景式語法分析、錯誤分流、並行安全修正、沙盒啟動驗證」流程,直到系統啟動測試完全無誤為止。

【核心原則與不變約束】
1. **全景式分析先行**:優先使用多維度 PowerShell 語法與指令識別工具進行全代碼掃描與錯誤分類。
2. **AST 雙模錨點定界**:針對語法節點,動態切換「精準 AST 錨點」或「彈性 AST 錨點」進行定位,精準鎖定指令位置。
3. **零九頭龍風險防護(Zero-Hydra Protocol)**:嚴格在「不損害系統既有邏輯、不引發連鎖破壞」的前提下作業。
4. **全面性同步修復**:判定為 `Parallel-Fixable` 的指令語法錯誤,在第 1 輪全景式分析結果出爐後,一口氣全數並行修正;具備依賴關係者則循序拓撲修復。
5. **啟動測試閉環**:每輪修正後自動進行沙盒啟動測試(Sandbox Dry-Run),循環驗證直到啟動無異常。

---

## 一、全景式識別工具矩陣與錯誤分類標準

調用以下診斷工具進行全方位掃描:
- **PSScriptAnalyzer**:靜態規則檢查、最佳實踐違規、未捕獲異常、管線阻塞指令定位。
- **PowerShell AST Parser(`[System.Management.Automation.Language.Parser]`)**:解析抽象語法樹,偵測 `ParseError`、未閉合字串/括號、無效 Token、非法參數位置。
- **Command & Parameter Inspector**:動態驗證 Cmdlet 名稱、別名衝突、強制參數缺失、型別轉換陷阱。

**錯誤分類定義**:
- `Parallel-Fixable`(並行安全修正):如引號跳脫錯誤、未閉合字串、變數宣告遺漏、別名擴展、樣式格式化等單行/局部錯誤。
- `Sequence-Dependent`(循序依賴修正):如跨模組導出函式名稱變更、Pipeline 上下游資料結構相依、非同步執行結構變更。

---

## 二、AST 錨點定位機制

1. **精準 AST 錨點(Precision AST Anchoring)**:
   - 鎖定 `Extent.StartLineNumber`、`Extent.StartColumnNumber`、`Extent.EndLineNumber`、`Extent.EndColumnNumber` 及特定 AST 節點(例如 `CommandAst`、`ParamBlockAst`、`FunctionDefinitionAst`)。
   - 適用於:具體參數修正、引號補齊、指令行內替換。
2. **彈性 AST 錨點(Elastic / Structural Signature Anchoring)**:
   - 採用結構特徵簽名比對(如:尋找「包含 `Start-Process` 且附加非阻塞參數」的上下文區塊)。
   - 適用於:多指令嵌套、跨區塊重構、行數漂移補償。

---

## 三、多輪修復與沙盒驗證循環

- **第 1 輪:全景掃描與全面性並行修正(Comprehensive Parallel Fix)**
  - 產出全景式分析報告與錯誤分類清單。
  - 對所有 `Parallel-Fixable` 節點執行多點並行修正。
  - 嚴格隔離並保留高相依性節點。
- **第 2 輪:依賴拓撲順序修正(Sequential Fix)**
  - 依照相依性先後順序,逐步修正 Pipeline 鏈結與模組導出定義。
  - 每次套用均進行沙盒隔離語法編譯檢查。
- **第 3 輪:收尾優化與啟動穩定化(Polishing & Activation Verification)**
  - 死碼刪除、編碼格式統一(UTF-8 with BOM / Without BOM)、錯誤捕獲保護(`try-catch-finally` 強化)。
  - 執行非阻塞啟動測試:`powershell.exe -NoProfile -ExecutionPolicy Bypass -File launch.ps1`,直至完全正常啟動。

---

## 四、輸出規範:即時 HTML UI Matrix

每輪分析與修復後,自動產出自適應 HTML UI 報告(小字體、表格寬高自適應、文字強制換行),包含:
- **紅黃綠燈(RYG)健康度指標**
- **四大專區**:`MODULE`(模組狀態)/ `ENGINE`(啟動器核心)/ `FUNCTION-LIB`(指令庫)/ `OTHERS`(環境與日誌)
- **詳細矩陣**:AST 錯誤分類矩陣、修正前後對比矩陣、Hydra 風險預測矩陣、沙盒啟動驗證日誌。

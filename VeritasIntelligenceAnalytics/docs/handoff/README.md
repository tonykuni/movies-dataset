# VCGC 交接防遺漏

每次接手：既有操作主控台 → `via-vcgc token` → `via-vcgc handoff check`。沿用已載入加速模板的 PowerShell 入口，不另建執行通道。

`HANDOFF_latest.json` 是可機器核對的交接快照。它記錄中央需求、模組指紋、凍結成功來源、已驗證項、待辦、負責者與下一步。快照更新前，前版按內容 SHA 保留於 `history/`。

- GREEN：交接資料可續接；未完成事項仍在 pending。
- YELLOW：需求或版本改變、尚未 checkpoint，應先看差異。
- RED：需求／待辦遺失、成功鎖被改、模組未註冊、測試證據錯誤或過期，禁止成功加鎖。

`closeout_lamp` 分開判斷驗收。交接 GREEN 不代表 VDF 已更新資料庫，也不代表 VRN 已完整擷取所有樣本。SDD 仍保留原本的驗證条件，並額外阻止未完成交接項被宣告 CLOSED。

修改後：登錄需求和來源 → 開新版模組 → `handoff test <case>` → 原有 `registry-sync --apply` → 中央編號 `--apply` → SDD 檢查 → `handoff checkpoint` → GitHub CI。每個測試收據包含精確命令、目標成功標記、實際 rc、相依 SHA、測試紀錄 SHA、時間與測試環境；相依未變的成功證據直接沿用。

目前測試 case：`handoff`、`provenance`、`numbering`、`entry`、`manager`、`sdd`。新功能必須加上其需求、管理模組與測試 case；檢查器會拒絕沒有測試相依證據的新程式。

來源驗證走 `via-vcgc run VRN_SystemManager provenance --report <LAYOUT_REVIEW.json> --source <樣本檔或夾> --out <證據輸出夾>`。重用既有成功擷取；每個來源有中央 SRC 號，每筆觀測有中央規格的 OBS 號，原文、修復值、空值、0、表格欄列與座標均保留。同一字形經不同引擎讀取不算兩個獨立來源。數值相符不等於完整性驗收。

來源模組會列出失敗區域的下一級工具與預算，但目前不自動啟動重度 OCR；年度頁判型、期間／單位語意正規化與完整樣本實測仍屬 pending。不得把規劃欄位當成已執行紀錄。

主機接續：已找到 OneDrive「VRN測式文件」的 106 件樣本清單並下載一份 DOCX，部分 PDF 下載由服務端回覆 403。可直接沿用已取得的本機 PDF 樣本；OneDrive 的讀檔連線不等於 Windows 主機或資料庫執行入口。實際主機結果需由既有 Windows runner／操作主控台回傳。授權已具備，不需再次核准。

原始成功引擎與舊薄尾依賴保留原位。未使用候選只列隔離清單，經依賴確認才實際搬移；本版不刪舊功能，不使用 TA-Lib。

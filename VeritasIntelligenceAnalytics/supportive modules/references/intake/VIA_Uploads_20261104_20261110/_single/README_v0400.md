# NON_STOCK_CORE v0400 — 整合強化版

更新日期：2026-11-08（Asia/Taipei）。本次為新製作的整合版本，未覆寫既有來源、未部署到使用者 Windows、未推送 GitHub。

## 版本查核結論

已查可取得的檔案及 `tonykuni/movies-dataset`、`tonykuni/VIA-VDF-VRN` 預設分支搜尋結果。找到的相關外層最新版本為 `VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py`；未找到獨立命名且高於 v0200 的 NON_STOCK_CORE。此結論不涵蓋未連接的 Windows 磁碟、所有其他分支或未提供的檔案。

| 版本 | 查得功能與關係 | 本次處理 |
|---|---|---|
| NonStock Intelligence v0100 | 產業／事件／公司、來源證據、舊分類詞彙 | 將適用詞彙映射到新版正式分類，保留來源 SHA；不重複建立舊分類 |
| NON_STOCK_CORE v0200 | 四種 profile、Claims／Events、數值／實體／時間檢查、新舊資訊、矛盾候選、摘要遺漏檢查 | 保留資料結構及 `def_analyze` 主要介面，修正語義與失敗回報 |
| SUMMARIZER v0300 | 一報告一列、一標題四點、四張表、VRN Layout／Repair／NLP 整合 | 經 v0310 繼承此邏輯 |
| SUMMARIZER v0310 | 附帶核心及三個 VRN 模組、缺件檢查與診斷 | 內部核心仍是 v0200；本次改為單檔內嵌、雜湊驗證、按需載入 |
| **NON_STOCK_CORE v0400** | 核心、整合報告與重用元件統一交付 | 新版；原始來源及歷史測試不冒充本輪驗收 |

v0300／v0310 兩套件內 `internal/NON_STOCK_CORE_v0200.py` 與 v0200 主引擎逐位元相同，SHA256：

`92f53d82c2facb41e599bf730b8be524901ed5d355aaed22a73444e85dccfa27`

## 本版強化

1. **單一主要 PY**：不需要外部 `internal`／`reuse` 資料夾；內嵌元件逐一核對 SHA，保留來源出處。這是套件完整性檢查，不是數位簽章。
2. **公司歸屬**：多公司段落以句內代碼優先；不把整段全部代碼套給每一句。同一句多公司共用目標價時標示待確認；互相衝突的評等／目標價不任意取第一個。
3. **完整原文重點**：四個角色以不重複的來源句配對；不足時留空並 REVIEW，不以截斷數字或無關標題湊滿四點。
4. **逐點證據**：主表、主題與公司重點均回連 claim／evidence SID；舊版填補重點遺漏 evidence SID 的問題一起修正。
5. **精確匹配與正規化**：避免 EV 命中 revenue、LINE 命中 airline／pipeline；日期驗證合法日曆；支援負 EPS、年減／季減符號、YYYYQ#／YYYY.Q#。
6. **結構化 JSON**：只讀明確 text／blocks／evidence_index 契約，不把任意 metadata 序列化成投資訊息；重複 SID／非法 page／不支援 schema 明確失敗。
7. **不隱藏遺漏**：超過輸入或 claim 上限明確失敗；短而有資訊的文字段落保留；空內容、空資料夾、缺少輸入不再回報 PASS。
8. **數值複核**：同句不同月份／情境的多個數值標為 `METRIC_CONTEXT_REVIEW`；跨 claim 的差異僅列 `POTENTIAL_CONFLICT_REVIEW`，仍需核對範圍、幣別與情境，不宣稱已證明矛盾。
9. **本機增量**：快取鍵涵蓋來源內容／路徑、引擎 SHA、設定、Python／相關套件版本及 prior 檔 SHA。快取 payload 校驗失敗會重算；來源變動會失效。
10. **有界加速**：預設單工、字詞快取、輕量本地抽取；不在啟動時匯入全部大型模型或反覆掃描使用者倉庫。外部 Celeritas 尚未實機連線，沒有宣稱 20 加速器已全數啟用。
11. **輸出可對帳**：CSV、Parquet 寫完讀回驗證；空表仍有 schema。缺少 PyArrow 明確失敗，除非使用者指定 `--csv-only`。
12. **發布與復原**：單寫入鎖、不可變批次資料夾、產物 SHA manifest，最後才更新 `LATEST.json`。中途失敗保留上一版發布；無自動刪除不明鎖或重播歷史清理操作。

## 一鍵 Windows 入口

解壓完整 ZIP，進入 `NON_STOCK_CORE_v0400` 資料夾，在 PowerShell 7 執行：

```powershell
& .\Invoke-NON-STOCK-CORE-v0400.ps1 -InputPath 'C:\測試樣本報告' -InstallDependencies -Recursive -OpenHtml
```

流程：尋找實際可用 Python 3.11+ → 建立／進入 `%LOCALAPPDATA%\VIA\venvs\via_nonstock_0400` → 安裝明確指定的依賴 → doctor／核心自測 → 執行、對帳與發布 → 開啟離線 HTML。入口結束會還原呼叫視窗的 PATH／VIRTUAL_ENV，不主動關閉視窗。

`-InstallDependencies` 會使用網路安裝套件；文件分析本身走本機路徑，不下載模型。已有依賴時可省略。僅處理 TXT／JSON 且不用 Parquet，可選 `-CsvOnly`；不會將此模式記成 Parquet 通過。

若下載的 PS1 被簽章政策阻擋，先在 PowerShell 7 貼上以下整段，將第一行路徑改為實際解壓位置。只調整目前程序，並在結束時還原；群組原則強制 AllSigned／Restricted 時停止。

```powershell
& {
    $ViaScript = Join-Path $HOME 'Downloads\NON_STOCK_CORE_v0400\Invoke-NON-STOCK-CORE-v0400.ps1'
    $ViaPolicy = Get-ExecutionPolicy -Scope MachinePolicy
    if ($ViaPolicy -eq 'Undefined') { $ViaPolicy = Get-ExecutionPolicy -Scope UserPolicy }
    if ($ViaPolicy -in @('AllSigned', 'Restricted')) { throw '群組原則要求簽章或禁止執行，需使用符合原則的簽章版本。' }
    $ViaOldPolicy = Get-ExecutionPolicy -Scope Process
    try {
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
        Unblock-File -LiteralPath $ViaScript
        & $ViaScript -InputPath 'C:\測試樣本報告' -InstallDependencies -Recursive -OpenHtml
    }
    finally { Set-ExecutionPolicy -Scope Process -ExecutionPolicy $ViaOldPolicy -Force }
}
```

PowerShell 入口在本輪僅作人工程式檢查，尚未在 Windows／PowerShell runtime 實跑；Python 測試環境與結果見 QA 檔。

## 直接使用 Python

```text
python NON_STOCK_CORE_v0400.py --doctor
python NON_STOCK_CORE_v0400.py --selftest
python NON_STOCK_CORE_v0400.py "C:\測試樣本報告" --recursive --outdir "C:\Users\tonyk\AppData\Local\VIA\NON_STOCK_CORE_v0400\output"
python NON_STOCK_CORE_v0400.py sample.txt --csv-only --outdir output
python NON_STOCK_CORE_v0400.py sample.txt --legacy-core --outdir core_output
python NON_STOCK_CORE_v0400.py sample.txt --prior-intelligence previous.nonstock.json --outdir output
python test_nonstock_v0400.py
```

`--legacy-core` 保留 v0200 的核心輸出契約；一般模式輸出四表並在 details 保存 Claims／Events／Novelty／Contradiction／Summary Loss 等完整核心結果。prior 檔使用核心輸出的 `.nonstock.json` 契約。

執行新版請使用 v0400 入口。舊 v0310 的 loader 仍明確指向 `internal/NON_STOCK_CORE_v0200.py`，下載新檔不會自動切換已安裝的 VCGC／VRN；本次未改寫那些入口或正式註冊資料。

支援 PDF、TXT、MD、LOG、HTML、DOCX、ENEX、結構化 JSON。影像掃描 PDF 無可抽文字時會報錯；本版沒有假稱已啟用 OCR。PDF／DOCX 與 Parquet 的依賴見 `requirements-runtime.txt`。PyMuPDF 等依賴的商業再散布授權需沿用專案既有審核；此交付沒有新增商業授權保證。

## 輸出與狀態

- `LATEST.json`：最後完成發布的批次與狀態；只以它指定的批次為準。
- `batches/<batch_id>/REPORT_SUMMARY.csv/.parquet`：一報告一列，四點摘要與 evidence IDs。
- `TOPIC_DETAIL.csv/.parquet`、`COMPANY_DETAIL.csv/.parquet`、`EVIDENCE_DETAIL.csv/.parquet`：下鑽明細。
- `REPORT_SUMMARY.html`：離線報表；詳細表有顯示上限，完整資料保留在 CSV／Parquet／JSON。
- `RESULTS.json`：每個來源的執行／快取／錯誤狀態與資料表計數。
- `details/<report_id>.json`：完整來源、核心結果及四點驗證。
- `MANIFEST.json`：該批次所有產物 SHA256。

新版 REPORT_ID 加入完整來源路徑及內容雜湊以避免不同資料夾同名檔碰撞；主表另保留 `LEGACY_REPORT_ID` 對照 v0300／v0310 的舊編號。更新既有資料庫時先依此映射，不能直接以新版 ID 覆蓋中央 SSOT ID。

CLI 退出碼 `0` 表示本輪所有必要結果閘門通過；`2` 表示 REVIEW 或 ERROR，應查看錯誤訊息及 RESULTS（若已發布）。來源忠實度、schema 與數值字面守衛通過，不等於已完成外部事實查核或投資結論驗證。

寫入程序意外終止可能留下 `.nonstock-writer.lock`。先檢查鎖內 PID／時間，確認沒有該輸出目錄的執行程序，再人工處理；引擎不會自行刪除其他程序的鎖。未被 LATEST 指到的未完成批次不視為成功發布。

## 驗收界線

實際數量、來源 SHA、版本比較與執行環境見 `QA_v0400.json`／`VERSION_COMPARISON_v0400.json`。測試包括原核心自測、獨立搬移單檔、負面案例、來源不改寫、CSV／Parquet 讀回、快取失效及發布失敗復原。

已使用可取得的兩份原始 PDF 與 TEST MESSAGE.txt 重新處理。內容需複核的列保留 REVIEW，不將舊版固定 PASS 當作新版本驗收基準。原始 PDF／訊息檔不放入發行包。HTML 只作生成與安全轉義檢查，本輪未作真實瀏覽器互動驗收。

## 稽核與維護

主檔頂部集中核心參數，內嵌重用元件保持來源可追溯；使用下列命令匯出完整元件供檢視，已有同名檔時拒絕覆寫：

```text
python NON_STOCK_CORE_v0400.py --export-components exported_components
```

修改主檔後需重新跑測試、更新 SHA 與 PS 入口期待值；不要把改過內容的檔案冒充本發行包。正式 VCGC SSOT 發號、客戶部署及 Windows 相容驗收尚未執行。

## 本次實跑摘要

- 核心自測 9/9；回歸測試 41/41；Python AST 解析 5/5（僅此發行檔與內嵌元件）。
- 三份真實來源均完成處理；內容結果仍有 REVIEW，不宣稱全面業務正確。
- 四張表均通過 CSV／Parquet 寫後讀回；第二次執行 3/3 命中快取，四表內容一致。
- 本機單次量測：首次 23.722 秒、再次 0.840 秒；不外推到 Windows 或其他資料。

| 來源 | 主題 | 公司 | 證據 | 狀態 |
|---|---:|---:|---:|---|
| 20260916兆豐台灣產業專題-AI末日論？假的.pdf | 15 | 3 | 116 | REVIEW |
| 20260916兆豐台灣產業專題-航太產業.pdf | 19 | 6 | 111 | REVIEW |
| TEST MESSAGE.txt | 58 | 33 | 1822 | REVIEW |

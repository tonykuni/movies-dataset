# MarkdownEditingEngine v1.2.0

本機、免費、可稽核的多語言 Markdown 重組與修復引擎。v1.2.0 在既有 17 項第三方免費工具、Python／Node.js／Rust／Go／Lua／PowerShell 架構之上，新增句界、區塊、表格 shape、資訊單元及證據鏈守門。所有工具都在本機執行，不上傳文件。

## v1.2.0 核心升級

- 文字 20 類與表格 20 類失敗因素都有固定代碼、症狀、控制及嚴重度。
- `split-first-merge-never`：可證明的結構邊界可以切開；不自動把句子、標題或表格資料格接在一起。
- 先分類 `frontmatter / code / table / heading / list / quote / HTML / paragraph`，再切句，避免在程式碼、網址、版本號、縮寫及 inline code 中誤斷。
- 表格以狀態機保護跳脫 pipe 與 inline-code pipe，並驗證 header、delimiter、逐列欄數與 matrix SHA-256。
- 原始資料轉成 `narrative / definition / action / metric / key_value / table_record` 資訊單元；每筆保留標題路徑、來源行、來源區塊及 SHA-256。
- 每檔產生 `.structure.json`；批次產生 `Sentence_SSOT.csv`、`Information_SSOT.csv`、`Table_SSOT.csv`。
- 修復前後同時比較傳統 AST 語意簽章與重建簽章。FAIL 不寫回，REVIEW 在 strict 模式封鎖。
- 暫存驗證會複製已存在的相對連結目標，避免隔離環境造成假性 broken link。

完整 40 類失敗說明與驗證方法見 `RECONSTRUCTION_GUIDE.md`。

## 資料變成資訊的切割順序

1. 位元層：UTF-8、換行、NUL、檔案 SHA-256。
2. 保護層：front matter、fenced code、HTML、inline code、URL。
3. 區塊層：標題、段落、清單、引用、表格與空白邊界。
4. 句子層：中英句尾、版本號、小數、縮寫及標點狀態機。
5. 結構層：標題路徑、段落歸屬、表格 header／row shape。
6. 資訊層：敘述、定義、動作、指標、鍵值與表格紀錄。
7. 證據層：來源行、block ID、table ID、信心分數及 SHA-256。

## 執行語言

| 語言                       | 檔案                                                      | 責任                             |
| -------------------------- | --------------------------------------------------------- | -------------------------------- |
| PowerShell                 | `MarkdownEditingEngine.ps1`、安裝與測試腳本               | Windows 單一入口、環境建置       |
| Python 3.12+               | `engine/markdown_engine.py`、`semantic_reconstruction.py` | 並行流水線、重建守門、備份、報告 |
| JavaScript／Node.js 20.18+ | `node/ast_reorganizer.mjs`                                | remark/GFM AST、TOC、結構簽章    |
| Rust                       | `rust/src/main.rs`                                        | UTF-8、NUL、fenced code 快速檢查 |
| Go                         | `go/cmd/mdlinkcheck/main.go`                              | 本地連結與圖片路徑檢查           |
| Lua                        | `filters/preserve_callouts.lua`                           | Pandoc 可選 callout filter       |

## 安全流水線

1. 讀取原檔 SHA-256、AST 簽章與重建簽章。
2. 複製到每檔獨立暫存區，並帶入已存在的相對連結目標。
3. 只執行一個指定主格式化器，再套用不合併內容的安全結構修復。
4. 執行多解析器、lint、拼字、表格、連結與重建驗證。
5. 比對標題、連結、圖片、程式碼、inline code、front matter、HTML、句子及表格矩陣。
6. PASS 才能備份並原子替換；REVIEW 需人工確認；FAIL 禁止寫回。
7. 產生 JSON／HTML／CSV 報告、結構 sidecar 及可驗證的備份雜湊鏈。

## Windows 一鍵使用

雙擊 `Start-MarkdownEditingEngine.cmd` 可執行 doctor。首次安裝請在 PowerShell 執行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\Install-MarkdownEditingEngine.ps1 -InstallSystemRuntimes -WaitForKey
```

安裝器建立專案專用 `.venv`、安裝固定版 NPM／Python套件、編譯 Rust／Go 驗證器並安裝 mdBook；不刪除既有環境。

## 常用指令

```powershell
# 只分析結構、句界、表格與資訊單元
.\MarkdownEditingEngine.ps1 analyze-structure "C:\Docs" -Strict -Workers 4

# 唯讀嚴格檢查
.\MarkdownEditingEngine.ps1 check "C:\Docs" -Strict -Workers 4

# 試跑，不寫回
.\MarkdownEditingEngine.ps1 fix "C:\Docs" -DryRun

# 正式修復，預設 Prettier
.\MarkdownEditingEngine.ps1 fix "C:\Docs"

# 修復並更新目錄
.\MarkdownEditingEngine.ps1 reorganize "C:\Docs" -Toc

# 改用另一個唯一主格式化器
.\MarkdownEditingEngine.ps1 fix "C:\Docs" -Formatter rumdl
.\MarkdownEditingEngine.ps1 fix "C:\Docs" -Formatter mdformat
.\MarkdownEditingEngine.ps1 fix "C:\Docs" -Formatter pandoc
```

Pandoc round-trip 的格式變動最大，只建議用於已確認為標準 GFM 的文件。MyST、MDX 或大量 raw HTML 文件宜使用 `prettier` 或 `none`。

## 主要設定與輸出

- `config/engine.json`：formatter、worker、timeout、驗證器、安全及重建守門。
- `config/reconstruction_rules.json`：文字 20 類、表格 20 類失敗分類 SSOT。
- `reports/run-*.*`：JSON、HTML、UTF-8 BOM CSV 稽核報告。
- `reports/structure/<run-id>/*.structure.json`：逐檔區塊、句子、表格、資訊單元及證據。
- `Sentence_SSOT.csv`：句子、來源行、block ID、信心與語意雜湊。
- `Information_SSOT.csv`：資訊類型、標題路徑、來源及指標。
- `Table_SSOT.csv`：表格 shape、header、row count 與 matrix SHA-256。
- `.markdown-editing-backup/<run-id>/`：原檔備份及 `backup_hash_chain.jsonl`。
- `reports/quarantine/<run-id>/`：被守門拒絕的候選版本。

## 驗證與測試

```powershell
.\Run-Tests.ps1 -WaitForKey
```

驗證採五層守門：解析成功、結構不變、句子不變、表格矩陣不變、二次執行無新變更。測試包含故障注入、相對連結暫存、中文 callout、版本號與縮寫、inline-code pipe、表格欄數錯誤、零造字／零造格、批次並行及備份鏈。完整結果見 `TEST_REPORT.md`。

## 已知界線

- 工具不能可靠猜回來源已遺失的字、欄位、colspan、rowspan 或 PDF 版面。
- B013、B014、B016、B019 要自動恢復時，必須額外提供 HTML 結構或 PDF 頁碼／BBox 證據；否則一律 REVIEW。
- 外部 HTTP 連結預設不連網；Go 驗證器只檢查本地相對路徑。
- CJK 表格顯示寬度因字型與終端而異；MD060 視覺補空格不作封鎖，欄數與內容由重建守門驗證。
- `mdformat` 與 `markdown-table-fixer` 的 style check 預設關閉、可按需啟用；它們不是主格式化器時僅作 advisory，避免格式風格衝突阻擋安全修復。

第三方工具與授權見 `THIRD_PARTY.md`。

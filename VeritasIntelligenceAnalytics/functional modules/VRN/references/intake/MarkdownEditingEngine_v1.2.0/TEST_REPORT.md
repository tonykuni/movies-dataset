# MarkdownEditingEngine v1.2.0 測試報告

- 測試日期：2026/08/31
- 測試平台：Linux x86_64、Python 3.12.13、Node.js 24.19.0、Pandoc 3.1.3
- 目標平台：Windows 11／PowerShell 7；同時支援 Python CLI

## 最終結果

| 測試層                |       結果 | 證據                                                                             |
| --------------------- | ---------: | -------------------------------------------------------------------------------- |
| Python 單元與故障注入 | 25/25 PASS | 句界、表格 shape、零補造、inline/reference/HTML 相對連結、語意守門、原子寫回、報告、雜湊鏈、quarantine |
| Node AST              |   2/2 PASS | GFM 簽章與 validate                                                              |
| 失敗分類 SSOT         | 40/40 PASS | T001–T020、B001–B020 各 20 個且代碼唯一                                          |
| Python 相依完整性     |       PASS | `pip check` 無 broken requirements                                               |
| Node 直接相依         |      READY | `npm install`、固定版 lockfile、Node 測試通過                                    |
| CSpell 離線檢查       |       PASS | README、重建指南、測試報告及 fixtures 零 issue                                   |
| 嚴格修復試跑          |       PASS | broken fixture 經 Prettier＋安全重建後零 warning、零 error                       |
| 受控並行壓力          | 16/16 PASS | 1、4、16 worker 的結構守門皆通過；16-worker 實際併發 16 檔                      |
| 批次修復              | 13/13 PASS | 首輪 12 changed、1 unchanged、0 failed                                           |
| 冪等回歸              | 13/13 PASS | 第二輪 13 unchanged，逐檔 SHA-256 完全相同                                       |
| 重建輸出              |       PASS | `.structure.json`、Sentence／Information／Table SSOT CSV                         |
| 備份雜湊鏈            |       PASS | `previous_hash` 與 `entry_hash` 可重新計算                                       |
| 報告矩陣              |       PASS | JSON、HTML、UTF-8 BOM CSV 同步產出並含 reconstruction gate                       |
| 連結故障注入          |       PASS | 改變 URL 後拒絕寫回、原檔不動、候選檔隔離                                        |
| 表格故障注入          |       PASS | B003 欄數錯誤判 FAIL，原檔保持不變                                               |

## v1.2 重建驗證案例

| 案例                     | 預期                                    | 實測 |
| ------------------------ | --------------------------------------- | ---- |
| `Version 1.2.3`、`Dr.`   | 不在句點中間斷句                        | PASS |
| `[!NOTE]` callout        | marker 不成為句子、不被 remark 當壞連結 | PASS |
| 標題黏正文               | 只插入可證明的空白邊界                  | PASS |
| `                        | --                                      | :-:  | `   | 只擴展為有效 delimiter；不增加資料格 | PASS |
| inline code `` `a\|b` `` | pipe 不切欄                             | PASS |
| 表格某列多一欄           | B003、FAIL、禁止寫回                    | PASS |
| 表格無 delimiter         | B001、REVIEW、不自行補表                | PASS |
| 鍵值／動作／表格列       | 轉成資訊單元並保留 lineage              | PASS |
| 前後句子或表格值改變     | reconstruction guard 拒絕               | PASS |
| 已存在相對連結           | 暫存驗證保留解析環境                    | PASS |

所有安全結構修復的 audit 均要求 `merge_operations = 0` 與 `fabricated_cells = 0`。這表示引擎能補明確語法邊界，但不會猜接句子、創造遺失文字或補造資料格。

## 除錯與最佳化紀錄

1. Prettier 對 CJK 表格可能輸出兩個 delimiter dash；新增 delimiter-like 狀態判斷，只擴展 dash 長度，不改欄數與內容。
2. markdownlint MD060 以顯示寬度要求 padding，會和 CJK 字型寬度及 Prettier 衝突；改由表格 shape 與 matrix SHA-256 守門，MD060 不封鎖。
3. remark recommended preset 原先把 `[!NOTE]` 視為未定義 reference；限定允許 NOTE、TIP、IMPORTANT、WARNING、CAUTION 五類 callout。
4. 每檔獨立暫存曾讓正常相對連結變成假性 missing；現在安全複製已存在的連結目標到相同相對位置。
5. `mdformat --check` 與 `markdown-table-fixer` 是風格檢查，和唯一主 formatter 可能不一致；預設關閉、按需啟用且列為 non-blocking advisory。
6. 可選 Rust／Go／mdBook runtime 缺少時只在 doctor 與逐工具結果如實記錄，不把乾淨文件誤標成 warning。

## 工具狀態

doctor 共登錄 21 個 adapter，其中 17 個在本環境 ready。可動態執行的核心包括 Prettier、markdownlint-cli2、remark、lint-md、mdast、rumdl、PyMarkdown、mdformat、markdown-table-fixer、Pandoc、CSpell、三個 v1.1 擴充及 v1.2 semantic reconstruction。

## 本環境未動態執行

此 Linux 容器沒有 PowerShell、Rust、Go 與 mdBook runtime，因此未動態執行 PowerShell 入口、Rust `mdscan`、Go `mdlinkcheck` 與 mdBook 建置。Prettydiff 維持隔離的 legacy adapter。相關原始碼與 Windows 安裝／編譯流程均保留；doctor 會如實標示 unavailable，不會誤報為已測。

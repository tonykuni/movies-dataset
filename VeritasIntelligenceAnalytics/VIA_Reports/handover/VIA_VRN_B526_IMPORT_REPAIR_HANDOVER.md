# VIA／VRN B526 Import 修復交接報告

**驗收時間：** 2026-09-16 15:05（Asia/Taipei）  
**Git 工作樹：** `/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics`  
**驗收範圍：** `functional modules/VRN` active tree；`references/intake` 排除，沿用 VRN 全景驗收規則。

## 終極實測判定

本輪修復後，VRN active tree 已達到 **GREEN**：

| 指標 | 實測結果 | 判定 |
|---|---:|---|
| Python active files | 288 | PASS |
| Compile | 288/288 | PASS |
| Import | 288/288 | PASS |
| Compile failures | 0 | PASS |
| Import failures | 0 | PASS |
| Latest-family import failures | 0 | PASS |
| PDF fixture 雙引擎頁數互核 | 2/2 | PASS |
| PDF fixture manifest/artifacts | 全部存在 | PASS |
| PDF fixture 狀態 | GREEN | PASS |

機器可讀結果位於：`/home/ubuntu/work/vrn_pdf_validation_b524.json`。

## 已修復項目

本次原始失敗為 10 個 import failure，實際分成以下四類：

| 類別 | 檔案數 | 修復內容 |
|---|---:|---|
| VRN 根目錄啟動腳本 | 2 | 加入 VRN root 與 20260804 legacy module loader；把歷史 MDL001/002/006/007/008 正本以明確檔案映射載入。 |
| pip vendor editable 中介 | 1 | 對已由新版 pip 移除的 `setuptools_build` helper 加入保守 fallback；不改變現代 pip 路徑。 |
| pip resolvelib reporter 中介 | 2 | 對裸檔探針與 package 模式加入相容匯入；缺少 pip private base 時僅退回型別註記，不攔截 reporter 類別建立。 |
| rich table／reporter 中介 | 4 | 加入 package-relative 優先、已安裝 `rich` absolute fallback；並安裝 `rich>=13,<15` 至 `quantguard_venv`。 |
| web scraping classifier 路徑 | 1 | 加入 engine directory 到 `sys.path`，讓 classifier 與 compliance SSOT 從同一受控目錄載入。 |

修復共修改 10 個既有檔案，沒有刪除核心 VRN 引擎，也沒有改寫使用者樣本或資料庫。

## 驗證方式

驗收不是只看語法：

1. 使用既有 `probe_module.py` 對每個 active Python 檔執行 compile/import/interface probe。
2. 使用 `run_vrn_pdf_validation_b524.py` 重跑全樹掃描與 PDF regression。
3. 兩個原本會在 import 時誤啟動測試流程的啟動器，已改為 import-safe；直接以命令列執行時仍保留原有實測流程。
4. synthetic PDF 以 fitz 與 pdfplumber 兩個解析器互核；2 頁、雙引擎皆有非空文字，12 個表格儲存格與所有 regression artifact 均存在。

## 邊界與未宣稱事項

`GREEN` 在本報告表示 **active tree 的 compile/import 健康與 PDF fixture regression 通過**。它不等同於所有外部服務已在線：

- 啟動器以 `/tmp/fake_ssot` 做 import-safe 探針時，HardGate 顯示 0/7 capable；這是測試環境 capability 缺席，不是 import failure。
- 直接執行兩個啟動器仍需要其原始 `/home/claude/work/test_pdfs` fixture；本沙盒沒有該目錄，因此本輪不把完整 MDL pipeline runtime 結果冒稱為通過。
- 使用者列出的 Windows PDF/DOCX 仍未掛載；本報告不宣稱那些原始報告已完成內容級驗證。

## 回復點與雜湊

修復前備份：

`/home/ubuntu/work/vrn_import_repair_b526_backup_20260916T1454/VRN_active_tree_before_fix.tar.gz`

修復前備份 SHA-256：

`0fe1693d1f7f26c10321338193926a0596581bbae9d1566d0878571005a56d25`

修復後 active Python 雜湊清單：

`/home/ubuntu/work/vrn_import_repair_b526_after_sha256.txt`

修復後雜湊清單 SHA-256：

`1d6db512f4b4de5532f7e42b353f41b90587a1b29234ed0c500b62a3bb788812`

## 下一位 AI 最省額度接手指令

```bash
ROOT='/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics'
PY='/home/ubuntu/work/quantguard_venv/bin/python'
cd "$ROOT"
cat VIA_Reports/handover/VIA_VRN_B526_IMPORT_REPAIR_HANDOVER.md
$PY - <<'PY'
import json
p='/home/ubuntu/work/vrn_pdf_validation_b524.json'
x=json.load(open(p,encoding='utf-8'))
print(x['vrn']['state'], x['vrn']['compile_ok'], x['vrn']['import_ok'], x['vrn']['active_python_files'], x['pdf']['state'])
PY
```

**接手結論：** VRN active tree import gate 已完成 GREEN；下一階段應處理 HardGate capability 實體掛載與原始 PDF/DOCX 掛載，不應重做本輪 288 檔 import 修復。

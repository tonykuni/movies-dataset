# SuperDocExtractor 超級文件擷取器

**Word / Excel / CSV 文字與表格擷取 → 編碼修復 → 驗證 → 對照**，全部使用本地免費開源技術（local free libs），資料不出機器。

`superextract` 的核心**只用 Python 標準庫**就能完整運作（自製 OOXML 解析器）；有安裝選用套件時自動升級能力。支援 `.docx` / `.xlsx` / `.xls` / `.csv` / `.tsv` / `.txt`。

```
擷取 Extract          修復 Repair              驗證 Validate           對照 Compare
─────────────        ─────────────            ─────────────           ─────────────
vMerge/gridSpan  →   只填補真正合併的儲存格    重複/空白表頭            文字 unified diff + HTML
巢狀表格攤平+抽出     零寬字元/NBSP/亂碼修復    前導零識別欄警告          表格自動配對（防錯位）
追蹤修訂過濾          NFKC 全半形統一          日/月順序模糊日期        主鍵對齊逐格差異
公式快取值/日期序號    破損 CSV 列修復          排版用表格偵測           datacompy 專業報表
編碼自動偵測(Big5…)   表頭去重命名             不可見字元掃描           多引擎交叉驗證
```

## 快速開始 Quick start

```bash
# 零安裝即可用（標準庫模式）；要完整火力就裝選用套件：
pip install -r requirements.txt

python super_extract.py doctor                      # 檢查哪些選用套件可用
python super_extract.py selftest                    # 15 項端到端自我驗證
python super_extract.py extract  report.docx       # 擷取 → <report>_extracted/
python super_extract.py validate orders.xlsx        # 只跑驗證，印出所有發現
python super_extract.py compare  old.docx new.docx --key 品名 -o diff_out --html
python super_extract.py crosscheck contract.docx    # 多引擎交叉驗證
```

Python API：

```python
from superextract import extract_any, compare_files, crosscheck_docx

result = extract_any("contract.docx")        # 擷取+修復+驗證 一次完成
print(result.text)                           # 修復後全文（含頁首頁尾）
for grid in result.tables:                   # 每張表格（含巢狀表）
    print(grid.to_markdown())
    grid.to_csv("out.csv")                   # utf-8-sig，Excel 直接開不亂碼
    df = grid.to_dataframe()                 # 需要 pandas 時
for issue in result.issues:                  # 驗證發現
    print(issue)
for fix in result.text_fixes:                # 修復稽核紀錄（改了什麼都有記錄）
    print(fix)

report = compare_files("old.docx", "new.docx", key="品名")   # 對照
```

## CLI 指令總覽

| 指令 | 功能 |
| --- | --- |
| `doctor` | 列出選用套件安裝狀態與各自的加值 |
| `extract FILE [-o DIR]` | 擷取文字 (.txt) + 每張表格 (.csv) + 報表 (.md/.json) |
| `validate FILE` | 擷取並執行所有驗證檢查，只印報告 |
| `compare OLD NEW [--key COL] [-o DIR] [--html]` | 文字 diff + 表格配對 + 逐格差異 + datacompy |
| `crosscheck FILE.docx` | 用所有可用引擎各解析一次並互相比對 |
| `selftest [--keep DIR]` | 產生刁鑽樣本檔並驗證整條管線（15 項檢查） |

常用參數：`--engine`（強制指定解析引擎）、`--encoding`（跳過編碼偵測）、`--password`（加密 Office 檔）、`--values formula`（讀公式而非快取值）、`--row-policy repair|skip|strict|keep`（CSV 破損列策略）、`--no-repair`（只擷取不修復）、`--drop-layout-tables`（排除排版用表格）。

## 設計重點

### 1. 合併儲存格：只填補「真正被合併」的格子

一般做法用 `pandas.ffill()` 向下填補，會**誤殺真實空值**（那格本來就沒資料，也被上面的值蓋掉）。本工具解析 Word 底層 XML 的 `<w:vMerge>` / `<w:gridSpan>`（Excel 則讀 `<mergeCells>`），把每個延續格的「錨點」記進 `Grid.merge_map`，`fill_merged()` 只填補這些格子——真正的空格永遠保持空白。selftest 的 `docx_merges` / `xlsx_both_engines` 兩項就是在驗證這件事。

### 2. 編碼問題（編碼偵測 + 亂碼修復兩段式）

偵測鏈：**BOM → 嚴格 UTF-8 →( charset_normalizer → chardet )→ 啟發式候選**（utf-8 → cp950/Big5 → gb18030 → shift_jis → cp1252 → latin-1）。

嚴格 UTF-8 放在偵測器之前是刻意的：合法 UTF-8 位元組流幾乎不可能是其它 CJK 編碼，而「本身是合法 UTF-8 的亂碼」（雙重編碼 mojibake）必須先按 UTF-8 讀進來，交給第二段的 `fix_mojibake()`（有 ftfy 用 ftfy，沒有就用內建 reverse-transcode，且只在亂碼分數**確實下降**時採用，絕不越修越糟）。每一步都寫入稽核紀錄，報表看得到「這些位元組是怎麼被解讀的」。

### 3. 表格對照前先「配對」

新版文件中間插入一張新表格時，天真的「第 N 張比第 N 張」會整份錯位。`pair_tables()` 先用表頭 Jaccard + 內容取樣 + 形狀相似度做貪婪配對，配不到的表格明確列為「新增/刪除」，配到的才進入逐格比對。列對齊優先用主鍵（`--key` 指定或自動偵測唯一欄位），報表會標明用了哪種對齊方式。

### 4. 多引擎交叉驗證（crosscheck）

同一份 `.docx` 用 rawxml（本工具）、python-docx、docx2python 各解析一次再互相 diff。三個獨立實作一致 = 擷取結果可信；不一致的地方就是需要人工檢查的地方。實測就抓到一個真實差異：**python-docx 會漏掉追蹤修訂的插入文字**（`w:ins` 內的 run），rawxml 引擎則正確納入。

## 十大實務地雷 → 本工具的對策

| # | 地雷 | 對策 |
| --- | --- | --- |
| 1 | 假 `.docx`（其實是 OLE2 的 .doc）`BadZipFile` | 檔案簽章偵測，回報 OLE2/加密與轉檔指令（`soffice --headless --convert-to docx`） |
| 2 | vMerge 造成欄列錯位 | rawxml 引擎依 XML 網格語意展開，錨點記錄於 `merge_map` |
| 3 | 追蹤修訂的已刪文字滲入 | `w:delText` 天然排除、`w:ins` 納入，並在 notes 提示文件含修訂 |
| 4 | 巢狀表格炸裂 | 遞迴解析：攤平進外層儲存格文字，同時獨立抽出為 `cell(r,c)` 具名表格 |
| 5 | 排版用表格污染資料 | `is_layout_table()` 啟發式（過小/過空），報表標記、可 `--drop-layout-tables` |
| 6 | `ffill` 誤殺真實空值 | 見設計重點 1——只填 merge_map 中的格子 |
| 7 | 幽靈差異（零寬字元/NBSP/全半形） | 修復段清除+NFKC；比對一律走 `normalize_for_compare()` |
| 8 | 表格數量不對等造成錯位比對 | 見設計重點 3——先配對再比對 |
| 9 | 插列後 index 比對全錯 | 主鍵自動偵測/`--key` 指定；用 index 對齊時報表明確警告 |
| 10 | `1,000` vs `1000` vs `１０００`、前導零 `00123` | 數值感知等值比較；前導零視為識別碼**不**轉數字並發出警告 |

Excel/CSV 側另涵蓋：公式 vs 快取值（`--values`）、日期序號含 1900 閏年 bug 與 1904 系統、`.xls` 舊格式（xlrd）、加密檔（msoffcrypto-tool + `--password`）、BOM、分隔符嗅探、破損列修復、模糊日期（10/11 是十月還是十一月）警告。

## 選用套件（全部本地免費）

| 套件 | 加值 |
| --- | --- |
| charset-normalizer / chardet | 更準的編碼偵測（沒有時用內建啟發式） |
| ftfy | 工業級亂碼修復（沒有時用內建 reverse-transcode） |
| pandas | `Grid.to_dataframe()`、datacompy 前置需求 |
| openpyxl | 首選 .xlsx 引擎（沒有時用內建 rawxml 解析器） |
| python-docx / docx2python | crosscheck 交叉驗證用的替代引擎 |
| datacompy | 專業表格比對報表（0.x 的 `Compare` 與 1.x 的 `PandasCompare` 皆相容） |
| xlrd | 舊版二進位 .xls |
| msoffcrypto-tool | 密碼保護的 Office 檔 |

## 測試

```bash
python super_extract.py selftest        # 不需 pytest，15 項端到端檢查
python -m pytest tests/ -v              # 同一組檢查的 pytest 包裝
```

selftest 會現場手工打造刁鑽樣本（含 vMerge/gridSpan/巢狀表/追蹤修訂的 docx、含公式/合併/日期序號/前導零的 xlsx、Big5/BOM/mojibake/破損列/分號分隔的 CSV、假副檔名檔案），逐一驗證上表的每個對策。標準庫模式（把所有選用套件遮蔽）同樣 15/15 通過。

## 專案結構

```
SuperDocExtractor/
├── super_extract.py          # CLI 入口（也可 python -m superextract）
├── requirements.txt          # 全部為選用套件
├── superextract/
│   ├── pipeline.py           # extract_any / compare_files 高階管線
│   ├── word_extract.py       # docx：rawxml 引擎 + python-docx/docx2python 引擎
│   ├── excel_extract.py      # xlsx/xls：openpyxl + rawxml 後備 + xlrd
│   ├── csv_extract.py        # 編碼偵測 + 分隔符嗅探 + 破損列修復
│   ├── encoding.py           # 編碼偵測鏈（BOM/UTF-8/偵測器/啟發式）
│   ├── textclean.py          # 亂碼修復、零寬字元、NFKC、稽核紀錄
│   ├── tableops.py           # Grid 結構、merge_map、匯出、數值感知
│   ├── validate.py           # 驗證檢查（表頭/前導零/模糊日期/排版表…）
│   ├── compare.py            # diff、表格配對、逐格比對、datacompy、crosscheck
│   ├── report.py             # Markdown / JSON 報表
│   ├── samples.py            # 刁鑽樣本產生器（手工 OOXML）
│   ├── selftest.py           # 15 項端到端檢查
│   └── availability.py       # 選用套件註冊表（doctor）
└── tests/test_extractor.py   # pytest 包裝
```

## 實測紀錄

在本 repo 的真實資料上：`data/movie_metadata.csv`（5044 列 × 28 欄）1.2 秒完成擷取+驗證，並自動修復了 5252 個儲存格——這個資料集的電影片名尾端都藏著 `\xa0`（不換行空格），`'Avatar\xa0'` → `'Avatar'`。

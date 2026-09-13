# VRN 全景實測與缺功能表列(批465)

日期 2026-09-13 · 分支 `claude/via-envmanager-governance-7cls8h`

操作員令兩條:
1. 「實測 VRN 修正直到成功 TEST DEBUG 全景式分析研究哪邊卡住 表列 缺少的功能」
2. 「輸入介面不再有特定系統內指定位置,改為一律 WINDOWS I/O 或拖曳式輸入,
   搜尋檔案夾中的 WORD PDF IMAGE 檔案」
3. 追令:「VDF 有用四碼台股代碼去擷取 TWSE/TPEX/MOPS 每日更新的全台股清單,
   名稱統一從這裡更新」

本文所有數字都是在本容器**跑出來的**,不是讀碼推測的。跑不到的部分明說跑不到。

---

## 一、全景掃描:38 個版號族,33 支有自測

掃描器對每一族取尾版,帶 180s 逾時逐支跑 `--selftest`。

| | 改動前 | 改動後 |
|---|---|---|
| 可測 | 28 支 | 28 支 |
| GREEN | 24 | **25** |
| 非綠 | 4 | **3** |

無自測旗標(10 支,非缺陷,只是沒有自測面):ENG049 / ENG050 / ENG052 /
ENG055 / ENG056 / ENG057 / ENG062 / OperatorRegex_TWTicker / TW01 / TW02。

### 剩下 3 支非綠 —— 全部是**本容器缺料**,不是程式錯

| 引擎 | 燈 | 缺什麼 |
|---|---|---|
| `VRN_ENG068_DailyBrief_v0103` | 十一檢 OK 7 · FAIL 4 | 無 VDF 倉庫:VIA grid 燈、台股五表、`prices_canonical`、因子庫 |
| `VRN_ENG069_ConsensusDB_v0102` | 八檢 OK 6 · FAIL 2 | 外部 0 檔 · 券商 0 檔;④ 需要 2330 在庫 |
| `VRN_ENG070_YahooConsensus_v0101` | 八檢 OK 7 · FAIL 1 | ⑥ 多源共存依賴 ENG069 的表有列 |

這三支在工作站上**有倉庫**時應會轉綠 —— 但我沒有他的倉庫,**不能替它們宣告綠**。

---

## 二、端到端實測:三件料只取到兩件

造了三件真料(TW 券商報告樣態):`2330…pdf`、`2454…docx`、`3008…png`。

```
v0113:取件 2 份
  [DUAL_ZONES]             2330_TSMC_20260911.pdf   · 563 字
  [DOCX_LIB_MISSING]       2454_MediaTek_20260910.docx ·   0 字
  (3008_scan_20260909.png 完全沒出現)
```

影像件**不是抽失敗,是從頭到尾沒被當成一件**:收件閘寫死
`sorted([*d.glob("*.pdf"), *d.glob("*.docx")])`。

```
v0114:取件 3 份
  [DUAL_ZONES]             2330…pdf   · 563 字   ← 零回歸
  [DOCX_ZIP_FALLBACK]      2454…docx  · 156 字   ← 0 → 156
  [IMAGE_OCR(…)[無中文語言檔:數字可信、中文字形八成全錯]] 3008…png · 180 字
```

---

## 三、缺功能表列(量到的證據 → 補了什麼)

| # | 缺什麼 | 量到的證據 | 補法 | 狀態 |
|---|---|---|---|---|
| A | 影像件完全不收 | 三件料的夾只取到兩件 | ENG072 v0114:冊 `input.intake` 宣告 PDF/WORD/IMAGE | ✅ 27/27 |
| B | WORD 無零相依退路 | `DOCX_LIB_MISSING` → 0 字 | `.docx` 本來就是 zip,直讀 `word/document.xml` 的 `<w:t>` | ✅ 0→156 字 |
| C | 輸入位置寫死 | `$inbox = Join-Path $vrn "input\incoming"` | `--in <檔或夾>` 收系統任何位置;`--no-incoming` | ✅ |
| D | 無 Windows 原生選檔器 | 全倉 grep `OpenFileDialog` 零命中 | `VIA_WinIO_InputPicker_v0100.ps1` + `via-vrnin.cmd` | ✅ 11/11 |
| E | 主控台拖曳區只收 pdf/docx | `accept=".pdf,.docx"`、`/\.(pdf\|docx)$/i` | MDL139 v0103:由冊生成 | ✅ 14/14 |
| F | 「抽到字」被當成「抽到對的字」 | tesseract 只有 eng/osd:`台積電`→`ARs` | tag 掛第三態 | ✅ |
| G | 未捕捉例外 = 假死不是紅燈 | ENG068 `--selftest` 以 traceback 收場 | 四道護欄 + 逐檢 guard | ✅ 11 盞全亮 |
| H | 自測覆寫正式 UI 頁 | 跑一次自測就把 545,364 列覆寫成「缺」 | 批410 同律:自測重導輸出 | ✅ |
| I | 個股名冊對不上報告文字 | `classify("台積電")` = GENERAL | MDL142 名稱正典冊 | ✅ 9/9 |
| J | **OCR 沒有中文語言檔** | `tesseract --list-langs` = eng, osd | **操作員側**:放 `chi_tra.traineddata` | ⬜ 待操作員 |
| K | 19 支尾版仍引用殘缺表 | 見第五節 | **待裁示**(有寫入方,不能一律改讀) | ⬜ 待裁示 |

---

## 四、輸入介面:三條道,都只交出真實路徑

| 道 | 怎麼用 | 位置 | 複製? |
|---|---|---|---|
| 原生選檔 | `via-vrnin -Pick File`(可多選) | 任何位置 | 否,就地讀 |
| 原生選夾 | `via-vrnin -Pick Folder` | 任何位置 | 否,就地讀 |
| 拖曳 | 把檔/夾拖到 `via-vrnin.cmd` 圖示上 | 任何位置 | 否,就地讀 |
| 參數 | `via-vrnin -Path "D:\a.pdf","E:\報告夾"` | 任何位置 | 否,就地讀 |
| (舊)瀏覽器主控台 | 拖進 MDL139 的拖曳區 | — | **是**,複製進 incoming |

最後一列不是設計偷懶:瀏覽器的 `webkitdirectory` / `<input type=file>`
**拿不到真實路徑**,只給 `webkitRelativePath`(相對名),所以那條道**必然**是
複製。這句話現在直接寫在頁上,不讓人自己猜。

三個實作坑(都是跑出來才知道的):
- **PS7 預設 MTA** → 對話框 `ShowDialog()` 會拋
  `current thread must be set to single thread apartment`。一律丟進 STA runspace。
- **`.ps1` 收不到拖曳** → 檔案總管拖到 `.ps1` 上只會用記事本開它;`.cmd` 才收得到 `%*`。
- **`$input` 會預讀 stdin 卡死** → 腳本一提 `$input`,PowerShell 在 `-File` 模式
  會先把 stdin 讀到 EOF 才開跑。stdin 是沒人關的管線時,它不是慢,是**永遠不回**
  (自測第一次就這樣掛住)。管線輸入改成只有明講 `-FromPipe` 才讀。

零彈窗律沒有破:對話框**只在操作員自己要求時**開(`-Pick`);
`VIA_NO_DIALOG=1` / CI / 非互動 / 非 Windows 一律不開,改為誠實要求 `-Path`。

---

## 五、名稱正典(追令)—— 待裁示的 19 支

庫裡有兩張清單表,名稱樣態完全不同:

| 表 | 列 | 名稱樣態 | 判 |
|---|---|---|---|
| `tw_listings` | 891 | **全名**「茂生農經股份有限公司」· industry 只有代碼 `33` · isin 空 | 殘缺 |
| `tw_listings_industry` | **1,978** | 四碼 + **簡稱**「台積電」· TWSE 1,088 / TPEX 890 · 產業名 · yf_ticker | **正典** |

研究報告寫的是簡稱。拿全名冊比對報告文字,**一個字都不會命中** ——
ENG067 ③⑤ 兩盞紅燈就是這麼來的。

已立 `CGC_MDL142_TWNameBook_v0100.py`(唯讀、零網路、零發明、九檢 9/9),
取數次序 ① 正典表 → ② 落盤 → ③ 全名補位,每一家標得出 `src`。ENG067 v0103
已改綁它。

**尚未處理、需要操作員裁示**:全樹 **19 支尾版**仍引用 `tw_listings`(非 `_industry`)。
不能一律改讀,因為其中有**寫入方**:

| 支 | 殘缺表引用 | 正典引用 | 備註 |
|---|---|---|---|
| `VDF_ENG079_LocalDbConsolidate_v0100` | 21 | 3 | |
| `VRN_ENG073_ReportStructuredDB_v0118` | 15 | 2 | |
| `VDF_ENG081_UniverseAlign_v0100` | 13 | 0 | **疑寫入方** |
| `VRN_ENG080_FourPointDigest_v0103` | 7 | 0 | |
| `VDF_ENG052_MegaFetch_v0102` | 7 | 0 | **寫入方** |
| `VIA_VRN_FirstPageEngine_v0123` | 6 | 7 | |
| `VAP_ENG009_DashboardUI_v0107` | 6 | 0 | |
| `VDF_ENG070_GroupClassificationIndex_v0111` | 5 | 0 | |
| `VDF_ENG054_TWDailyBackfill_v0104` | 5 | 0 | |
| `CGC_MDL119_SystemAPI_v0103` | 4 | 6 | |
| `CGC_MDL139_InputConsole_v0103` | 4 | 0 | |
| `VRN_ENG067_MindMapSSOT_v0102` | 4 | 0 | 已由 v0103 取代 |
| 其餘 7 支各 1 次 | 1 | 0–1 | MDL098 / MDL064 / MDL118 / MDL096 / MDL095 / ENG074 / ENG072(VDF) |

---

## 六、本批產物

| 檔 | 檢 | 說明 |
|---|---|---|
| `VRN_ENG072_FirstPageText_v0114.py` | 27/27 | 三類受理 + 位置解放 + docx 零相依 + 影像 OCR + CJK 第三態 |
| `VIA_WinIO_InputPicker_v0100.ps1` | 11/11 | 原生對話框 + STA 保險 + 零彈窗律 + 不卡斷 |
| `via-vrnin.cmd` | — | 拖曳梭 |
| `CGC_MDL139_InputConsole_v0103.py` | 14/14 | 拖曳區由冊生成 + 真實路徑限制寫明 |
| `VRN_ENG068_DailyBrief_v0103.py` | 11 盞全亮 | 護欄 + 自測重導 |
| `VRN_ENG067_MindMapSSOT_v0103.py` | 9/9 | 改綁 MDL142 |
| `CGC_MDL142_TWNameBook_v0100.py` | 9/9 | 名稱正典冊 |
| `VIA_InputConsole_Spec_v0100.json` | — | 加 `input.intake`(只增不減) |

---

## 七、我這一批犯的錯(留給下一棒)

1. **檢法自我指涉** —— 三次。`-notmatch "Stop-Process"` 這句本身就含
   `Stop-Process`;`.pdf,.docx` 寫在解說註解裡。**缺席檢一律要先把自測段/註解剝掉**。
2. **根因判錯一次** —— ENG067 我先判「DuckDB 缺 → 冊空」,量完發現庫在、891 家、
   冊不空,真因是**兩張表名稱樣態不同**。是我自己加的那行 `ticker_src` 註記把我抓出來的。
   燈要印出「這個數字是哪來的」,不然改對改錯都看不出來。
3. **誤用既有函式** —— 拿 `ocr_did_run()`(問「跑了但零字、該不該升階」)
   去當「這段字出自 OCR 道嗎」用,第三態一次都不會掛。**名字像不等於語意像。**
4. **先做了第二份實作才想起 Zero-Hydra** —— v0102 手併兩本名冊,綠了,但那是
   VDF/VAP/VRN 各寫各的第 N 份。v0103 才改成委派 MDL142。


---

## 八、批466 追加:整條鏈下游實測(①站通了不代表鏈通)

### 量到的兩個硬斷點

| 站 | v0105/v0118 的閘 | 後果 |
|---|---|---|
| ② ENG073 入庫 | `zdir.glob("*.json")` | ENG072 只有**分區道**寫 `.json`,WORD/IMAGE/OCR/pypdf 只寫 `.txt` → 新收的 docx 與 png **一件都沒進庫** |
| ③ ENG074 財報頁 | `d.glob("*.pdf")` | 同一個夾直接回「無 PDF」rc=2 —— docx 與影像**連被看見都沒有** |

### 還抓到一個會炸掉整批入庫的缺陷

`extract_one` 的 `if tpv:` 看的是**值**,而 `tp.group(0)` 假設本檔 `TP_RX` 有命中。
批442 起目標價會由首頁引擎橋接管(`tpv = _tp_fp`),那時 `tp` 仍是 `None`
→ `AttributeError`。而 `run()` 的 try 只包住 json 讀取,**一份壞件讓整批入庫死掉**,
畫面上沒有任何一行說它死了(實測:67 份的批次連「入庫計」都沒印出來)。

### 真料實測(操作員上傳兩份真 .docx)

| 檔 | zip | 表格 | 純文字 | ①站 | ②站 | ③站 |
|---|---|---|---|---|---|---|
| `…20260708.docx` | 48 件 | 36 | 73,456 字 | 1,151 字 ✅ | 未分類 ✅ | 36 表無一通過財報頁判準 ✅ |
| `VIA….docx` | 12 件 | 19 | 1,346,930 字 | 1,190 字 ✅ | 未分類 ✅ | 19 表無一通過財報頁判準 ✅ |

兩份都不是個股研究報告(討論稿與架構樹),鏈**誠實留白、零發明**,全程 1.1–1.5 秒。

**而真料抓到一個真缺陷**:`1379b53b-____20260708` 被判成「個股 1379」——
那四碼是**上傳雜湊的前綴**,不是股票代號;而 1379 益缶**真的在冊上**,
所以名冊對帳擋不住。`TICK_RX = (?<!\d)(\d{4})(?!\d)` 只擋相鄰數字,不擋相鄰字母。

修法**不能**一刀改成「兩側必須非英數」——那會誤殺批420 明令要認的 `3014TT`。
**邊界律**:左須邊界;右須邊界,**或**已知市場後綴(`TWO/TT/TW/T`)再接邊界。

| 檔名 | v0123 | v0124 |
|---|---|---|
| `1379b53b-____20260708` | 個股 **1379** ❌ | 未分類 ✅ |
| `ab2330cd` | 個股 2330 ❌ | 未分類 ✅ |
| `3014TT` | 個股 3014 | 個股 3014 ✅ |
| `2330.TW` / `2330_TSMC_20260911` / `MS-2308_20250101` / `GS-2330 20251205` | 個股 | 個股 ✅ |

### 批466 產物

| 檔 | 檢 |
|---|---|
| `VRN_ENG072_FirstPageText_v0115.py` | 28/28 — 每一件都留 sidecar,無幾何者不編造分區 |
| `VRN_ENG073_ReportStructuredDB_v0119.py` | 36/36 — `tp` None 崩潰修 + 逐件護欄 + 邊界律退路 |
| `VRN_ENG074_FinancialPages_v0106.py` | 18/18 — 三類收件 + WORD `<w:tbl>` 零相依表格讀法 |
| `VIA_VRN_FirstPageEngine_v0124.py` | 41/41 — 邊界律 + ㊵ 對照組釘版 |

### 又一個我自己的錯

㊵ 的對照組寫成「尾版以外的最後一個檔」= **版本相對**。本檔一複製成 v0124,
「上一版」就變成 v0123 —— 那一版**已經修好了**,對照當然不成立,整盞燈轉紅,
而且紅得像回歸。**對照組要釘死在缺陷所在的那一版**(v0122),不是釘「上一版」。

---

_Generated by [Claude Code](https://claude.ai/code)_

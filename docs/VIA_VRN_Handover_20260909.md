# VIA 接棒報告 — 2026-09-09

分支 `claude/via-envmanager-governance-7cls8h` · HEAD `2e41e86e`(批421)
上一批 `5bd57724`(批420)· 對照 main:PR #30 已併,批381 之後皆未併

---

## 一、一句話現況

**VRN 五段鏈全線通,59 份真研報跑到底、`rc=0`、`PENDING 0`;
卡住的是「抽不出目標價」這一件事,不是鏈路。**

`DONE 25` · `DONE_NS 22`(非個股,已完成)· `FAIL 12` · `PENDING 0`
總判 `RED` —— 這個 RED 是誠實的:12 份確實沒過核對,不是燈壞。

---

## 二、鏈是怎麼串的(接棒者先看這張)

```
報告檔(input/incoming)
   │
   ├①收件 ─────────────────────────────────────────────┐
   │                                                    │
   ├②首頁  via-console run --item vrn_firstpage         │
   │        └ VRN_ENG072_FirstPageText_v0107            │
   │           ├ 法A fitz 文字                           │
   │           ├ 法B docx                                │
   │           └ 法C GLE 九宮分區 ──→ SUP_MDL743 ────┐   │
   │           └ 句級修復 TextProcessor ─→ SUP_MDL744─┤   │
   │           產出:*.firstpage.json(sidecar)      │   │
   │                                                 │   │
   ├③入庫  via-console run --item vrn_structdb        │   │
   │        └ VRN_ENG073_ReportStructuredDB_v0114     │   │
   │           ├ 檔名拆解 tokenize_filename(批420)   │   │
   │           ├ 券商/評等/分析師 → 疊加層 SSOT       │   │
   │           ├ 正規化 _nfkc ──→ SUP_MDL744 ─────────┤   │
   │           └ 價表核對 → VDF tw_daily_prices       │   │
   │           產出:vrn_report_basic / _metrics      │   │
   │                                                 │   │
   ├④財報頁 via-console run --item vrn_finpages       │   │
   │        └ VRN_ENG074_FinancialPages_v0102        │   │
   │           └ fitz 文字 + 行級 regex(**只有一法**) │   │
   │           產出:vrn_report_financial + 三方對照   │   │
   │                                                 │   │
   └⑤四點  via-console run --item vrn_fourpoint       │   │
            └ VRN_ENG080_FourPointDigest_v0102       │   │
               └ K1 上漲空間 = 目標價(除權息同口徑)  │   │
                  ÷ VDF 最新 adj close               │   │
                                                     │   │
收尾:via-closeout vrn ─ CGC_MDL141_ClosingGate_v0104 ┘   │
       逐份判 DONE / DONE_NS / FAIL / PENDING           ─┘

支援模組(批421 新登錄,supportive modules/70_VRN_Rules/):
  SUP_MDL743_GenericLayoutHub  → GenericLayoutEngine v2.1.0(19 後端 / 32 adapter / 4 路由)
  SUP_MDL744_NLPApplicationHub → VIA_NLP_Application_System v1.8.0(39 模組 / 6 研報服務)
```

**兩支橋是這批才接上的。** 在此之前 ENG072/ENG073 把 NLP 收容夾**寫死**成
`VIA_NLP_OneEngine_v1.1.0`(18 模組),v1.5.0/v1.8.0 收容了也永遠掛不上。
工作站已驗證走通:

```
[NLP 掛載] 路徑=HUB · 橋=SUP_MDL744…→ VIA_NLP_Application_System_v1.8.0(VERIFIED) · 研報服務 6/6
```

---

## 三、12 筆 FAIL 拆成三族(這是明天的工作面)

### A 族:目標價根本沒抽到(8 筆,最大宗)

| 報告 | 狀態 | 證據 |
|---|---|---|
| `GS-1590 20231012` | MISSING_SOURCE | TP=None,庫P=1010 |
| `GS-1590 20251203` | MISSING_SOURCE | TP=None,庫P=885 |
| `GS-2317 20251205` | MISSING_SOURCE | TP=None,庫P=228.5 |
| `GS-2382 20231012` | MISSING_SOURCE | TP=None,庫P=238 |
| `GS-3706 20251130` | MISSING_SOURCE | TP=None,庫P=91.7 |
| `Daiwa-3653 20251002` | MISSING_SOURCE | TP=None,P=2470 |
| `Daiwa-6278 20260521` | MISSING_SOURCE | TP=None,P=223 |
| `6933_AMAX-KY 個股介紹報告` | MISSING_SOURCE | TP=None,庫P=None(DB_NO_MATCH) |

**共同特徵:代號認得出(BASIC 多為 VERIFIED)、價表查得到,就是文件裡的目標價抽不出來。**
五筆 GS 全中,而且 GS-2383 / GS-6415 兩份**同一家券商是 EXACT_MATCH**——
所以不是「GS 格式一律不行」,是這幾份的版面或文字層有差。

> ⚠️ 下一步別直接改 regex。先確認這幾份的 PDF 是不是**沒有文字層**(掃描/向量圖)。
> 工作站的 GLE 後端矩陣顯示 `tesseract` / `marker` / `poppler` **都在位**(7/19),
> 沙盒只有 4 支。OCR 在你機器上是可用的 —— 這是 A 族該走的路,不是改 regex。

### B 族:抓到數字但抓錯欄(4 筆)—— 其中 2 筆是**假綠**,見下節

| 報告 | 抽到 | 庫價 | TP÷庫價 | ENG073 態 | 收尾判 |
|---|---|---|---|---|---|
| `8210 勤誠 MS` | TP=18.0 P=7.0 | 626.0 | 0.029 | `PARSE_SUSPECT` | FAIL ✓ |
| `2891 中信金 凱基` | TP=59.0 P=19.0 | 54.8 | 1.077 | `PARSE_SUSPECT` | FAIL ✓ |
| `3653 健策 JP` | TP=26.0 P=60.0 | 2470.0 | **0.011** | `DB_DERIVED` | **DONE ✗** |
| `2308 台達電 MS` | TP=38.0 P=28.0 | 942.0 | **0.040** | `DB_DERIVED` | **DONE ✗** |

數字抓到了,只是抓到隔壁欄。前兩筆被 `PARSE_SUSPECT` 攔下來了,後兩筆沒有。

### C 族:庫價本身可疑(2 筆,這不是 VRN 的病)

| 報告 | TP | 庫P | 庫算升幅 |
|---|---|---|---|
| `6669 緯穎 MS` | 3500 | 1161.66 | **201.3%** |
| `6669 緯穎 CLST` | 4200 | 1111.37 | **277.9%** |

緯穎不是千元出頭的股票。**`tw_daily_prices` 對 6669 的復權價有問題**,
要回到 VDF 側查(`via-price` / `via-hist` / ENG060 調整後價格層),不要在 VRN 改。

另有 `Citi-3231 緯創`:TP=165 P=114 庫P=109.5(`P_DB_CONFLICT(KEEP_BOTH)`),
報告升幅 48.1 / 算 44.7 / 庫算 50.7 → `FORMULA_MISMATCH`。
這是**報告自己的數字對不上**,系統誠實留 FAIL 是對的,不要去湊。

---

---

## 三之二、⚠️ 找到一個假綠:兩道閘互不相通

**`CGC_MDL141_ClosingGate_v0104` 只讀 `vrn_report_basic.upside_state`,
從來不讀 `vrn_fourpoint.tp_state`。**

```python
# CGC_MDL141_ClosingGate_v0104.py:271
_REAL_BAD_STATES = ("FORMULA_MISMATCH", "FORMULA_MISMATCH_DB", "PARSE_SUSPECT")
_us = str((r or {}).get("upside_state") or "")     # ← 只看 ENG073 的態
if _us not in _REAL_BAD_STATES:
    verdict = "DONE_NS"
```

而 `VRN_ENG080_FourPointDigest_v0102` **自己有一道合理性閘,而且抓到了**:

```python
# VRN_ENG080_FourPointDigest_v0102.py:203
TP_SANITY_LO, TP_SANITY_HI = 0.2, 5.0      # 目標價÷現價 的合理帶
_tp_state, _tp_ratio = tp_sanity(tp_adj if tp_adj is not None else tp, adj)
#                                                        ↑ adj = VDF **最新**復權收盤
```

它的自測 ⑬ 逐字寫著要攔的就是這幾筆:

> 「工作站真跑 37 份,三份的 TP/價 比是 0.020(MS-2308)、0.019(MS-8210)、
> 0.005(JP-3653)——目標價只有股價的 1/50 到 1/200,那是抽錯的數。
> 把它印成「潛在上漲空間 -98.0%」比不印更糟,讀的人會以為那是預測。」

**結果**:`JP-3653` 與 `MS-2308` 在今天的收尾清單裡是

```
DONE    JP-3653 20251003    段 4/4(四點) BASIC VERIFIED FIN VERIFIED
DONE    MS-2308 20251128    段 4/4(四點) BASIC VERIFIED FIN VERIFIED
```

系統自己知道那兩個目標價是錯的,收尾閘卻報 DONE。**這就是假綠。**

### 修法(**未動,等指令**——因為它會改動你讀的 RYG)

`MDL141` 的逐份判定要**同時**讀 `vrn_fourpoint.tp_state`:
`TP_SUSPECT` 一律不得判 DONE。

改完後數字會變成 **DONE 23 · FAIL 14**(+2),`DONE_NS 22` 與 `PENDING 0` 不變。
我沒有自己改,因為改的是收尾判準本身、直接改變你看到的燈 —— 一句話我就動。

> 這條也該進紀律備忘:**同一件事有兩道閘時,要確認下游真的在聽上游**。
> 兩道閘各自都對、各自自測都綠,合起來仍然漏 —— 因為沒有人測「它們有沒有接上」。

---

## 四、今天新發現、還沒處理的三件

### 1. `vrn_firstpage` 的預設夾指向一個不存在的資料夾

```
[via-console run] NEED_DIR:報告夾缺:…\functional modules\VRN\input_reports
```

實際的檔案在 `input/incoming`。這次沒有造成損失(先前跑的 sidecar 還在,
段 histogram `收件 0 · 首頁 0` 表示沒有任何一份卡在前兩段),
但**第一段實際上這一輪沒有重跑**。
修法:`via-console set vrn-dir=…\input\incoming`,或把 `input_reports` 併進冊的預設候選。

### 2. 三方對照 `AGREE 0` —— 這道對照目前等於沒在對照

```
[三方對照] 已對照 59/59 份 · AGREE 0 · DIVERGE 4 · 單位差 0 · 表格獨有 445
```

59 份、445 個表格獨有值、**零個 AGREE**。
意思是「首頁 rx 抽到的值」與「財報頁表格抽到的值」幾乎**從不落在同一個
(dimension, period) 鍵上**,所以兩邊根本沒有機會互相驗證。
`DIVERGE 4` 是 `3014TT-20231005`×2 與 `國泰-神達(3706)`×2。

這不是紅燈,但它代表 ENG074 的三方對照現在提供的資訊價值接近零 —— 值得查鍵怎麼對不上。

### 3. ENG074 只有一法(這是我上一則講錯、已更正的事)

ENG074 的抽取只有 `fitz` 文字 + 行級 regex **一條路**,沒有第二法可以互相印證。
批421 本來要加第三法,實測後**沒有加**:`fitz sort=True` 會把分欄版面併回同一行,
舊法在合成樣本上是 work 的,我造的樣本沒重現真實故障 —— 不憑猜測動已跑綠的鏈。

---

## 五、明天的起手式(按投報排序)

**① 先驗 A 族是不是沒有文字層** ← 最高投報,8/12 筆都在這族
拿 `GS-1590 20251203` 一份出來,用剛開通的兩支橋做逐頁診斷:

```powershell
via-gle probe          # 確認 tesseract/marker/poppler 在位(工作站顯示 7/19)
via-nlp demo           # 確認 table_ops / layout_analysis 服務可用
```

然後把那份 PDF 的第一頁文字量印出來。**文字量接近 0 = 掃描件,答案就出來了**;
文字量正常 = 是版面問題,再往 `layout_analysis` 走。

**② 接通兩道閘,消掉假綠** ← 改動最小、且是誠實三態的直接違反
見第三之二節。`MDL141` 的逐份判定加讀 `vrn_fourpoint.tp_state`,
`TP_SUSPECT` 不得判 DONE。**一句話就能動**,DONE 25→23 · FAIL 12→14。

> 我原本以為是「合理性閘門檻沒涵蓋這個型態」,**查了原始碼發現不是**:
> 閘比的就是庫價(`tp_sanity(tp_adj, adj)`),而且抓到了。
> 問題在下游沒聽。診斷寫錯會讓接棒的人改錯地方,所以這裡留這一句。

**③ C 族回 VDF 查 6669 復權價** ← 不在 VRN 動手
```powershell
via-price run          # 確認 tw_daily_prices 對 6669 的覆蓋與復權因子
```

---

## 六、不要做的事(紀律備忘,踩過的坑)

| 規矩 | 為什麼(哪一批踩到的) |
|---|---|
| 不代設 `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` | 同意閘是操作員的意圖,不是預設值 |
| 不 `Stop-Process` / `Remove-Item` / `conda remove` 環境 | 破壞不可逆 |
| 不 force push | — |
| 引擎改動一律開新版號檔,正本零觸碰 | 尾版律 |
| 收容件原地不動,綁既有引擎不複製實作 | Zero-Hydra |
| 診斷程式碼不可以把主流程弄掛 | 批419d:`"…\None"` IOException 讓整段 rc=1,**比沒有診斷更糟** |
| 捕捉到的因由一定要顯示出來 | 批419e:`_FIN["why"]` 只在模組 None 時才印 → 對外只剩沒有理由的 `0/59` |
| 檢的 fixture 要帶真實狀態 | 批419d:fixture 用空字串代替 `MISSING_SOURCE`,測的就不是真的那條路 |
| 斷言要對著真實狀態寫 | 批421:我斷言路由表六模式,實際只有四個具名鍵 |
| 不能用「兩邊答案相同」的輸入當證據 | 批421:全形轉半形 stdlib 也會做,測不出走沒走正主 |
| 沙盒重生的產出頁不要 commit | 批416/批421:`VIA_UI_IntakeRoster` 會把沙盒狀態寫進工作站頁 |
| 兩道閘要測「有沒有接上」 | 本報告三之二:ENG080 閘抓到了、MDL141 不讀它 → 假綠。兩邊自測都綠,合起來仍漏 |

---

## 七、一貼即用

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -Command "git -C 'C:\Users\tonyk\Downloads\movies-dataset-b381' pull origin claude/via-envmanager-governance-7cls8h; Set-Location 'C:\Users\tonyk\Downloads\movies-dataset-b381\VeritasIntelligenceAnalytics'; $r = Get-ChildItem -LiteralPath '.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; via-handover build; via-gle probe; via-nlp status; via-closeout vrn"
```

---

## 八、還掛著的長期項目(未動,等指令)

| 項目 | 狀態 |
|---|---|
| 主動 ETF 持股史深 | 覆蓋 3/23(僅群益驗真)· 13 家投信 26 檔待逐家查端點 |
| 元大 PCF | 端點形制已知(`POST {base}/api/trans`),FuncId 未找到 → **未寫車道** |
| `via-psrepair -Fix` | 976 支 ps1 中 65 支可平行修 —— **等明示指令** |
| `via-envgov` RED 重建 | 需 `--approve-remove` —— **等明示指令** |
| 158 支舊短令死路 · 5 支無法解析 ps1 · `HARNESS_SELFCHECK_FAILED` | 待清 |
| GROK 側 `claude/via-mother-deck-b405` | HEAD `cdf7b20`,250 檢全過,**未開 PR** |
| GROK 24 支 VRN 模組 | 已採 2(券商冊/評等冊)· 我寫 2 · **未採 20**,其中 `vrn-rx`/`vrn-annual-cache`/`vrn-xval`/`vrn-field-cache` 直指本報告 A/B 兩族 |

---

*批421 · 兩收容系統升格為 VRN 支援模組。台帳 914 · docs 四十九 · SelftestGrid v0261 · Register v0166。*

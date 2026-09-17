# VIA 交接報告 · 多 AI 協作版(批541 立 · **批568 更新** · 2026-09-17)

> 這一份是**給下一個接手的人或 AI 看的**,不是給機器讀的。
> 目的只有一個:讓你在**不問任何人**的情況下,知道東西在哪、規矩是什麼、現在卡在哪。
> 自動產生的那份 `VIA_Handover_ONEPAGE.md` 有 260 KB(機器全量吐的),這一份是人讀的入口。

---

## 一、母系統在哪

| 層 | 位置 | 說明 |
|---|---|---|
| **倉庫根** | `movies-dataset/` | GitHub 倉庫的根;底下還有三個兄弟專案(見下) |
| **母系統** | `movies-dataset/VeritasIntelligenceAnalytics/` | **VIA 本體**。以下所有相對路徑都是從這裡起算 |
| 兄弟專案 | `VIA_GlobalETF_RiskModel/` · `VeritasStorageOptimizer/` | 獨立子專案,不受 VIA 治理家族管 |

**工作站絕對路徑**(Windows):
```
C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics
```

### 母系統的四個門(任何一個都進得去)

| 門 | 檔 | 用途 |
|---|---|---|
| **總管** | `VIA_SYSTEM_MANAGER_v0140.py` | 正式任務 81 項 + 總控頁再生。`python VIA_SYSTEM_MANAGER_v0140.py --no-open` |
| **短令冊** | `Register-VIA-Commands-v0213.ps1`(**在母系統根,不在 `supportive modules/`**) | 所有 `via-*` 短令的來源。**尾版律**:永遠點最新那一支 |
| **中央控管台** | `supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0111.py` | 唯一對接口(律 L20)。`registry-sync --apply` 是元件冊的**唯一寫者** |
| **自測格** | `supportive modules/registry/CGC_MDL064_SelftestGrid_v0332.py` | **231 站**驗收閘。要判斷系統健不健康,跑這一支就夠。<br>注意:不帶旗標或帶不認得的旗標=**跑全矩陣**(很久);單站除錯用 `--only "站名片段"` |

### 程式碼分佈(實測檔數,不含收容件與 `__pycache__`)

```
functional modules/VDF    182 .py   資料鍛造(價格/籌碼/月營收/ETF)
functional modules/VRN    308 .py   研報擷取(PDF→欄位→入庫→文摘)
functional modules/VAP    246 .py   自動繪圖與產出
supportive modules      1,650 .py   治理/登錄/工具(其中 registry 765 支)
```
中央治理家族(CGC_MDL***)**127 個**模組編號。(批555 實測;不含 `__pycache__` 與收容件)

---

## 二、資料庫在哪

**一句話:正典庫都在 `functional modules/<家>/…` 底下,`VIA_Reports/` 底下的全是產物與沙盒,不是正本。**

### 正典庫(有真資料的)

| 庫 | 路徑 | 本境實測 |
|---|---|---|
| **台股總庫** | `functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb` | **179 MB** · 22 表 · `features_daily` / `prices_canonical` / `tw_daily_prices` / `tw_prices_adj` 各 **577,733 列** · `tw_trading_daily` 57,649 |
| **國際總庫** | `functional modules/VDF/output_hub/mega/vdf_global_market.duckdb` | 16 MB · 9 表 · `features_daily` / `gl_prices_adj` / `global_daily` 各 **47,973 列** |
| **主動式 ETF** | `functional modules/VDF/output_hub/active_tw_etf/…/ActiveTWETF.duckdb` | 3.6 MB · `holdings_daily` 1,125 · `active_tw_etf_universe` 154 |
| **研報庫** | `functional modules/VRN/db/vrn_reports.duckdb` | 1.8 MB · 5 表 · `vrn_report_basic` **2 列** ← **本境幾乎是空的**(工作站 64 份) |

### ⚠️ 本境 ≠ 工作站(教訓 LL49,最容易踩的一個坑)

雲端容器每次開機都是**乾淨 clone**,`VIA_Reports/*` 大多在 `.gitignore` 裡。
所以本境的 VRN 庫只有 2 份報告,而工作站有 64 份真研報。**後果有兩個,都很痛:**

1. 任何「本境跑出來是空的」**不等於**「這個功能壞了」——很可能只是這裡沒料(要判 NODATA,不是 RED)。
2. 跑完自測格或總控頁再生之後,**約 20~30 個 UI 頁與登錄 JSON 會被空庫改寫**。
   **提交前一定要把那批 churn 還原**,只留真正要改的那幾個檔。否則你會把「空的」推上去蓋掉真的。

### 產物夾(可以砍,砍了會重生)
```
VIA_Reports/first_page_logic/   第一頁邏輯實測(CORPUS_latest.json 就在這)
VIA_Reports/selftest_grid/      自測格存證 GRID_*.json
VIA_Reports/vcgc/               中央控管台一頁交接
```

### 收容件(intake)—— 正本零觸碰
外來的程式碼/字典/字型一律先落在 `references/intake/`,**原名原位元組,一個 byte 都不准改**,
旁邊放 `_INTAKE_MANIFEST_*.json` 記 md5/sha256,由「橋」(Bridge 引擎)用 `importlib` 載進來,
所有防呆都寫在橋這一側。目前 6 個收容夾、頂層共 72 項(展開後 1,622 個檔)。

---

## 三、GitHub 連結

| 項目 | 連結 / 值 |
|---|---|
| 倉庫 | https://github.com/tonykuni/movies-dataset |
| **開發分支** | `claude/via-envmanager-governance-7cls8h` |
| **PR #37** | [tonykuni/movies-dataset#37](https://github.com/tonykuni/movies-dataset/pull/37) → **已由 tonykuni 併入 `main`**(2026-09-17 12:41Z,併的是 `7ed4d860`=批553;47 commits · 663 檔) |
| 目前 HEAD | `edb3ad52`(批555) |
| **分支超前 `main`** | 兩批:`51ec2603`(批554)· `edb3ad52`(批555)。三點差異 **11 檔**,就是這兩批的內容,**沒有夾帶** |
| `main` 超前分支 | 只有兩個 merge commit(#36 · #37),**內容為零** → 下一個 PR 會乾淨,不需要 rebase |
| 上一批 | `7ed4d860`(批553,已在 main)· `fce11b2e`(批552)· `103eeb82`(批551) |

> **PR #37 已經是完成品,不能拿來裝新東西。** 批554/555 要開的是**新 PR**(我不自己開,等你一句話)。
> 分支與 main 沒有衝突,所以**不需要 rebase、不需要 force push**——規矩沒破。

**規矩(不可違)**:只推這一個分支 · **不 force push** · 不自己 merge、不自己 approve PR。

---

## 四、多 AI 協作開發

### 目前已經發生的協作(git 實測,不是規劃)

```
                   批541      批554      session
Claude Opus 5      126   →    140        session_01RLMQGZLcigd5Bt5aN6J4Ck
Claude Fable 5.1   116   →    130        session_01R2d69oa1AGvnPVwjSUdSv5
tonykuni (人)      145   →    163        裁決者
                                         (git 樹共 333 筆)
```

> 數法:前兩列數 commit message 的 `Co-Authored-By` 標,第三列數 `%an`。
> 兩種數法不同類,加起來不等於 333——**這是誠實分母,不是對帳表**(LL86)。

兩個不同模型、兩個不同 session,在**同一個分支**上接力做了 250+ 批。能接得起來,是因為有下面五樣東西:

### 協作靠的五樣共用件(接手前先認識它們)

| # | 件 | 路徑 | 它解決什麼 |
|---|---|---|---|
| ① | **台帳**(只增不減) | `supportive modules/registry/VIA_AutoCode_Registry_v0100.json` | **1,086 筆**(批554)。每一批做了什麼、為什麼這樣做,全寫在這。接手第一件事是讀最後 3 筆 |
| ② | **律與教訓** | `supportive modules/registry/VIA_Policy_Laws_SSOT_v0100.json` | **律 59 條 · 教訓 107 條**(批554 加 LL107)。教訓都是**踩過才寫**的,每條都有批次編號可回溯 |
| ③ | **元件自動編號冊** | `…/VIA_Component_Inventory_SSOT_v0100.json` | **5,145 個活元件**。防撞名。唯一寫者是 `via-vcgc registry-sync --apply`,**不要手改** |
| ④ | **自測格 230 站** | `CGC_MDL064_SelftestGrid_v0321.py` | 共同驗收標準。你改完東西,它說綠才算綠 |
| ⑤ | **commit trailer** | 每個 commit 尾巴 | `Co-Authored-By:` + `Claude-Session:` → 任何一行程式碼都追得回哪個 AI、哪一場對話寫的 |

### 接手流程(冷啟動,照做就好)

```powershell
# ① 進母系統 + 拉最新
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull --ff-only origin claude/via-envmanager-governance-7cls8h

# ② 點最新短令冊(尾版律:永遠 Select -Last 1,不要釘版號)
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName

# ③ 先知道現況,再動手
via-vcgc              # 中央控管台十九檢
python .\supportive` modules\registry\CGC_MDL064_SelftestGrid_v0321.py   # 230 站
```
然後讀:台帳最後 3 筆 → 教訓最後 5 條 → 本檔第六節「現在卡在哪」。

### 多 AI 同時開發的**限制**(誠實講,這是目前的缺口)

- 只有**一條**開發分支,**沒有**併發鎖。兩個 AI 同時寫,一定衝突。
  目前靠的是「同一時間只有一個 session 在動」這個約定,不是機制。
- 元件冊有 `append_only` 旗標,但那是**寫入語意**,不是併發保護。
- 真要多 AI 並行,下一步該做的是:一批一分支 + 各自跑自測格 + 由人合併。**這件事還沒做。**

### 協作紀律(兩個 AI 都必須遵守,違反過的都寫進教訓了)

| 律 | 白話 |
|---|---|
| **只增不減** | 舊版本檔不刪。引擎改行為 → 開新版號檔(`_vNNNN`),不是就地改 |
| **尾版律** | 找引擎一律用 glob 取最新,**不准釘死版號** |
| **正本零觸碰** | `references/intake/` 底下一個 byte 都不改 |
| **不代設** | 不替操作員設任何同意閘(`VIA_NET_CONSENT` 等)、不代裝套件。要裝要開,是**他的手** |
| **誠實四態** | rc 0=GREEN · 1=RED · 2=NODATA · 3=ABSENT。**判錯的紅燈和假綠一樣傷** |
| **零九頭龍** | 同一件事不准有第二套實作。要整合就收斂到一處,不是再長一顆頭 |

> 這張表是**六句口訣**。完整的流程與政策(一批怎麼跑 · 功能註冊七處 · 推之前必跑 ·
> 不代做的四件 · 誠實五態)在 **[十、流程與政策](#十流程與政策批567-立)** —— 接手的人請把那一節讀完再動手。

---

## 五、交接報告有哪幾份(別找錯)

| 檔 | 大小 | 誰產的 | 看它的時機 |
|---|---|---|---|
| **本檔** `docs/VIA_Handover_MultiAI_B541.md` | 14 KB | 手寫 | **冷啟動、換人、換 AI** ← 從這裡開始 |
| `docs/VIA_Handover_20260914_B498.md` | 188 KB | 手寫累積 | 想知道某一批**為什麼**那樣做。批498 至今逐批記錄 |
| `docs/VIA_Handover_ONEPAGE.md` | 310 KB | `via-vcgc page --publish` 自動產 | 要機器全量快照(政策庫/邏輯庫/因子庫/資料庫/調度/多矩陣…十二段) |
| `../VIA_HANDOVER_LATEST.md` | 310 KB | 同上(倉庫根**鏡像**,逐位元相同) | 同上。給不進 VIA 夾的人看 |
| `supportive modules/ui_support/VIA_UI_MasterControl_v0100.html` | — | `VIA_SYSTEM_MANAGER --no-open` | 要用**瀏覽器**看 81 項正式任務 |

> **ONEPAGE 的批次段是從 `VIA_Handover_20260914_B498.md` 抽的**,所以逐批紀錄請以 B498 為正本。
> 批553/554 兩段我是**手動補進 ONEPAGE**(容器裡不能跑 `page --publish`——沙盒庫是空的,
> 跑了會用假資料覆蓋整份正本,那就是 LL49)。在工作站跑一次 `via-vcgc page --publish`
> 就會從 B498 重新生成、內容一致;根目錄鏡像同步更新。

---

## 六、現在的狀態(批557 · 2026-09-17 實測,不是上次的紀錄)

**三家全跑過一遍,零 RED。** 動詞 `matrix --apply-family <家> --profile test`(有界自測,不寫正本庫):

| 家 | 項 | 結果 |
|---|---|---|
| **VDF** 資料鍛造 | 33 | **GREEN 33** |
| **VRN** 研報擷取 | 15 | **GREEN 13 · ABSENT 2 · RED 0** |
| **VAP** 自動繪圖 | 6 | **GREEN 6** |
| 中央控管台 VCGC v0111 | 19 檢 | **OK 19 · FAIL 0** |
| 自測格 v0332 | 231 站 | 兩個異動站 `--only` 實跑 OK(全矩陣很久,沒跑) |

VRN 那兩盞 **ABSENT 是誠實的缺件,不是壞掉**:

| 項 | 態 | 差什麼 |
|---|---|---|
| `vrn_pdfplus` | ABSENT | 引擎自述「需要 reportlab」——**要你的手**(裝套件我不代做) |
| `vrn_nlp_vrn_vdf_pipeline` | ABSENT | argparse 自述「required: `--in`」——冊上這項的 params 該由主控台/`--ids` 帶值 |

> **第 1 站 `vrn_firstpage`(ENG072 v0134)現在 GREEN**——那就是你連看了十批的 ㉜ 紅燈。
> 但**這一盞在本境的綠是半盞**:容器一個 OCR 後端都沒有,`ocr_page1` 會 SKIP,
> 走不到出事那一步(這正是 LL106 的形狀)。你機器上 tesseract 在,會走得更遠——
> **要你那邊跑出來才算數。**

### 工作站實證(批558 · 操作員貼回來的那一跑)

**ENG072 的 ㉜ 紅燈在工作站也綠了** —— 這才算數,本境那盞是半盞(容器沒有 OCR 後端)。
操作員那一跑的 log 走完了真的 OCR 階梯(`tesseract_direct` · `NEEDS_OCR` · ㉟ DPI 帶 · ㊱ retry-failed · ㊷ 車道候選),
`vrn_firstpage` GREEN 181s。連 `vrn_pdfplus`(20.98s)與 `vrn_nlp_vrn_vdf_pipeline` 也 GREEN
—— 本境那兩盞 ABSENT 是**容器缺 reportlab / 缺 `--in` 帶值**,工作站兩樣都有。

```
[矩陣] 63 項 · profile=test · 真跑家族 vrn · GREEN 15 · PLAN 48
```

> ⚠️ **工作站上有三支比倉庫新的檔**:ENG072 **v0135** · ENG086 **v0109** · EngineBus **v0128**。
> `main` 與本分支都沒有它們。那是另一條線(或本機未推)的成果——
> **請把它們推上來**,否則下一批就會有兩個頭(九頭龍風險不是假設,是這種狀況的定義)。

### 規則收斂現況(`via-vrnrules drift`)

```
[正本  ] ENG086 第一頁邏輯橋  v0108  評等 38/38 · 目標價  7/16
[委樞  ] ENG073 報告結構庫    v0128  評等 38/38 · 目標價 16/16   ← 批554 委由樞紐
[落差  ] TW02 報告解析器      v0101  評等 12/38 · 目標價 10/16
[落差  ] 首頁全能引擎          v0125  評等 25/38 · 目標價 11/16
[不適用] ENG080 四點文摘      v0105  評等   —   · 目標價  5/16
```

### 分支與冊

| 項 | 值 |
|---|---|
| HEAD | `55a96ead`(批556)→ 本批後 批557 |
| 超前 `main` | 批554 · 批555 · 批556(+本批);**PR #37 已併,要開新 PR** |
| 台帳 | 1,086 筆 |
| 律 · 教訓 | 59 條 · **107 條**(批554 加 LL107) |
| 元件冊 | 活元件 5,174 · 退役 0 |

---

## 七、現在卡在哪(接手就看這節)

### A. 等操作員一句話才能動的

| 件 | 狀態 | 要什麼 |
|---|---|---|
| 三支評等落差引擎 | **ENG073 已接(批554)· 還剩兩支** | ~~ENG073 報告結構庫~~ → 首頁全能 v0125(低,評等 25/38 · 目標價 11/16)→ TW02 v0101(低,評等 12/38 · 目標價 10/16)。接法照 ENG073 的樣子:**向樞紐要實作,不抄詞表**;每支都要用同一份 64 份語料驗零回歸 |
| ENG086 正本自己的目標價同義字 | **7/16**(批554 量出來) | 正本實作只認 5 條強線索,加寬的 11 條走樞紐弱道。要不要把加寬道併進 ENG086 本體,是你的決定(併了會動到 64 份語料驗過的正本,風險不是零) |
| 批554 的真語料增減 | **未量** | 容器裡沒有那 64 份報告,批554 的正負對照全是合成文字。第二道從「全文」收窄到「前 40 行」理論上只少假評等——請在工作站跑一次,以 `rating_ssot_key` 與目標價命中數的變化為準 |
| 報告類全景項 | 掛著 | HARDIMP 100 · PINVER 23 · VERB 6 |
| 兩件收容件 | 存了但**沒接線** | `VIA_CodeChain_ALL_b534` · `VIA_CGE_AdaptiveInterface_b532` |

### B. 需要操作員的手(我不能代做)

`Z43` FactSet 共識 0 列 · `FRED` 金鑰 · 國際期貨 `BZ=F/CL=F/GC=F` ·
族群分類快照 · `pip install seaborn` · `Z49`/`Z56` 目標價原始 PDF

### C. 對不起來的數字(要先查清楚才能下判斷)

工作站上次顯示 **實測 15/17(2 RED)**,掃 1,287 檔 / 99 項;
我這邊掃 1,455 檔 / 129 項。**兩邊分母不同,結論就不可比**(教訓 LL86 尺錯了整組漂移作廢)。
→ 工作站先 `git pull --ff-only` 再跑一次,對得起來才能談那 2 盞紅燈是什麼。

---

## 八、批541 收在哪裡

- `f5def0d6` 批541:券商表去衝突(撞名 0 · 45 家)· 候選同義字 harvest(只提不寫冊)· 收容件導入驗證 ⑱ + 負控 ⑱'
- `81e4054c` 批541b:補短令 `via-vrnrules`(批540 漏了七處之一)
- 實測:ENG086 v0105 **19/19** · 64 份語料**零回歸**(券商 64/64 · 評等 36 · 目標價 30 · 真 RED 0)· 樞紐 **10/10** · 自測格 230 站 OK 227
- 新教訓:**LL88**(檔案在≠導得進來;檔案對冊≠驗過)· **LL89**(永遠回 0 的濾網=假綠燈)· **LL90**(同義的裁定權在操作員)

---

## 九、批542–556 收在哪裡(批557 追記)

| 批 | commit | 一句話 |
|---|---|---|
| 542 | `1d634ab1` | PS 叫用器加速:首呼 1137→280ms(−75%)· 後續 279→37ms(−87%)· 行為 6/6 不變 |
| 543 | `e3e86eb7` | 40 支缺的 `.cmd` 梭一次補齊(現在零缺) |
| 544 | `a96f0a92` | **CGC_MDL159 統一主控台**:TAB1 給 AI 的資訊全放一起(可轉 JSON/MD)· TAB2 收兩個既有頁 |
| 545–553 | `3ba666e6`…`7ed4d860` | ENG072 的 ㉜ 紅燈。**十批才收掉**,誠實帳見下 |
| 554 | `51ec2603` | 同義字收斂到一處:評等向樞紐要實作(前三道漏 14 → 0)· 目標價讀機構 SSOT(「目標 / target」在缺的 11 條裡)· 一個真迴歸修 |
| 555 | `edb3ad52` | 交接更新:多 AI 版刷到批554 · 一頁交接補 批553/554 · 根鏡像同步 |
| 556 | `55a96ead` | 一/二/三節重量:短令冊在**母系統根**(我前兩則給錯路徑)· PR #37 已併入 main · 自測格 231 站 |
| 557 | `ee662aef` | **三家全跑一遍**:VDF 33/33 · VRN 13 GREEN + 2 ABSENT + **RED 0** · VAP 6/6 · VCGC 19/19;新增第六節「現在的狀態」 |
| 558 | 本批 | **在哪裡找**:補 `footer`(主 join 從批237 起就漏這一區)· 中間本文標題區 · 兩處刻意改判各自單獨列檢 |

### ㉜ 那十批的誠實帳(接手的人請先讀這段)

紅燈從 批544 掛到 批553,**真 bug 只有兩個**:
① ㊷ 的斷言寫反了(只有在那個套件**不存在**時才會過);
② 夾具檔 `far/scan65.pdf` **從來沒被建立過**。

其餘八批是:**三次診斷錯**(說 ACCEL-BRIDGE 注入 → 其實是 CRLF;說 `pyvenv.cfg` 壞 →
那個值是我自己的 PowerShell 捏出來的;說「只剩 638 行」→ 那行根本沒被執行)、
**兩次拆我自己蒙的眼罩**(`str(exc)[:60]`、`f"({_g32[:90]})"`)、兩次更正、一次全景稽核。
**生產影響是零**(tesseract 道全程正常)。

三條新教訓寫在 LL102 / LL106 / LL107,共同形狀是同一句:
> **我先有了解釋,再去把任何數字湊上去。**

### 批554 現在的 drift 長這樣(一眼看誰還沒收斂)

```
[正本] ENG086 第一頁邏輯橋  v0108  評等 38/38 · 目標價  7/16
[委樞] ENG073 報告結構庫    v0128  評等 38/38 · 目標價 16/16   ← 委由樞紐(沒抄詞表=對的做法)
[落差] TW02 報告解析器      v0101  評等 12/38 · 目標價 10/16
[落差] 首頁全能引擎          v0125  評等 25/38 · 目標價 11/16
[不適用] ENG080 四點文摘     v0105  評等   —   · 目標價  5/16
```

一貼即用:

```powershell
Set-Location 'D:\OneDrive\文件\GitHub\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName   # 冊在 VIA 根
via-vrnrules drift      # 誰還沒收斂
via-ryg vrn             # VRN 四態燈
via-unified             # 批544 統一主控台(TAB1 給 AI · TAB2 兩頁合一)
```
---

## 十、流程與政策(批567 立)

> 操作員令「交接報告加入流程或政策」。
> 底下每一條都是**被燒出來才寫的**,括號裡是實錄批次,不是紙上規劃。

### 10.1 一批怎麼跑(七步,沒有例外)

```
① 量   —— 先量現況,不要先有解釋再湊數字(LL102/106/107)
② 判   —— 量出來若與指令的前提不符,誠實說「這件已經成立」,不假裝再做一次(批567)
③ 做   —— 引擎改行為=開新版號檔 _vNNNN;未版號檔才就地改(尾版律)
④ 證   —— 本境真跑:舊版 vs 新版同一輸入的前後對照,不是只跑新版看它綠
⑤ 登錄 —— 功能註冊七處(10.2),少一處等於沒上線
⑥ 推前驗 —— 10.3 三條必跑
⑦ 推   —— commit 批NNN:… + push,再回報操作員(「每一個進度就上傳 GITHUB」)
```

### 10.2 功能註冊七處(新引擎 / 新短令,少一處就等於沒上線)

| # | 處 | 檔 | 漏過沒 |
|---|---|---|---|
| 1 | 引擎本體 | `*_vNNNN.py` + `--selftest` 自己會報 n/n | |
| 2 | **短令冊 + 梭** | `Register-VIA-Commands-v*.ps1`(**在 VIA 根,不在 `supportive modules\`**)+ `via-xxx.cmd` | **批564 漏,`via-consensus` 不認得,連兩次** |
| 3 | 自測格站 | `supportive modules\registry\CGC_MDL064_SelftestGrid_v*.py` | 批563 改名改到隔壁站(regex 先撞到別人) |
| 4 | **正主管理器正式名稱 + 總控頁再生** | `VIA_SYSTEM_MANAGER_v*.py --no-open` → `VIA_UI_MasterControl_v0100.html` | **批565 漏,頁還印 98 而引擎族已 99,CI `test_11` 當場紅** |
| 5 | 主控台任務 | `CGC_MDL095_DeckServer_v*.py` / Console `GOV-NN` | |
| 6 | 政策 / 動詞 SSOT | `VIA_Policy_Laws_SSOT_v0100.json` 等 | |
| 7 | 台帳 | `supportive modules\registry\VIA_AutoCode_Registry_v0100.json`(`append_only`) | |

### 10.3 推之前必跑(三條半,都是被燒出來的)

| 驗 | 怎麼跑 | 出處 |
|---|---|---|
| **短令零 ghost** | 本批新寫的每一個 `via-*` 都要在冊上;PS 一貼即用區塊裡叫到的也算 | LL110(批564);守衛已寫進 `CGC_MDL157 v0103` |
| **總控頁同步** | 跑 `VIA_SYSTEM_MANAGER --no-open`。diff 只有時戳=引擎族數沒變 → **回退該檔**;有變 → 把再生的頁一起帶上,並在本境先跑合約測 | LL111(批565);CI `test_11` |
| **分母對帳** | 任何 `n/N` 的顯示,分子與分母必須來自同一個計數來源;做不到就加一條跑完對帳,讓不一致自己講出來 | LL112(批566) |
| **敗站不截斷** | 判為 FAIL 的站,原因行 / 例外全文 / 主控台 / 落檔四處都要原物;綠站與 SKIP 維持短切 | **L62 · LL113(批567)** |
| **合成檢關沙盒** | 合成檢只准驗自己合成的東西。引擎有幾個資料來源,自測就要把**每一個**都關進暫存夾——少關一個,那盞燈就是在看機器臉色 | **LL114(批567)**;VCGC ⑨ 曾因機器上一份 2.2h 前的真報告而假紅 |
| **來源閘(列舉靠機器)** | 「每一個」不能靠記性:用 AST 掃該條路,列出所有 `REPORTS / …` 磁碟來源與 `VIA_*` 覆寫鍵,**沒配鍵的、沒關沙盒的逐一指名報紅** | **L63 · LL115(批568)**;批567 我只關一個,同一個檢在兩台機器紅成兩種樣子 |
| **順手跑別人的自測** | 改完別只跑自己那支。誤傷與**舊傷**都是這樣照出來的 | LL114;⑨ 那一紅不是這批造成的,但不跑就永遠看不到 |

### 10.4 不代做的四件(這是界線,不是客氣)

| 不代做 | 為什麼 | 我改成做什麼 |
|---|---|---|
| 設同意閘(`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` / API key) | 觸網與付費是操作員的決定,不是我的 | 把要貼的那兩行**列出來給他貼**;該段標誠實態 **GATED** |
| 裝套件 / `conda remove` / `Stop-Process` / `Remove-Item` 動他的環境 | 那是他的機器,壞了我修不回來 | 給 `via-envgov apply --approve` 這類指令,**他的手**貼。容器沙盒裡為了自證而裝,不在此限 |
| force push / 併 PR / 核可 PR | 歷史與審查不是我的權 | 只推分支;PR 他開他併。`--approve-remove` 只在他明令時才帶 |
| 往正典冊裡寫同義字 | **裁定權在操作員**(LL90) | 候選一律標 `PENDING_OPERATOR`,附證據與衝突列表 |

### 10.5 誠實五態(混在一起,操作員就不知道該去補什麼)

| 態 | rc | 意思 | 不要混成 |
|---|---|---|---|
| **GREEN** | 0 | 真跑過,真的對 | — |
| **RED** | 1 | 壞了 | 判錯的紅燈和假綠一樣傷 |
| **NODATA** | 2 | 跑得動,但庫裡沒料 | 不是 RED |
| **ABSENT** | 3 | 引擎/檔根本不在 | 不是 NODATA |
| **GATED** | — | 閘未開(批566 新增) | **不是 SKIP(缺件),不是 FAIL(壞了)** |

### 10.6 本境 ≠ 工作站(LL49;最容易踩,踩下去會污染正本)

- 本境沙盒庫是**空的**。用它再生出來的頁與名冊**不准 commit** —— 那會拿假資料覆蓋正本。
  跑完 grid / manager 之後,先 `git status` 看有沒有 UI 頁與名冊的雜訊,有就回退。
- 網路**只認 AegisNexus**,`SUP_MDL740` 留作橋;收容件 `references/intake/` **只收不掛線**。
- **自測零網路**:任何 `--selftest` 不得觸網,否則在沒網的機器上就是假紅。

### 10.7 收尾一貼即用

```powershell
Set-Location 'D:\OneDrive\文件\GitHub\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName   # 冊在 VIA 根
via-oneshot            # 批566 一鍵統包:24 段 · 25 加速器 · 動態進度條 · 觸網段標 GATED
via-ryg                # 四態燈
via-vrnrules drift     # 規則收斂落差
```

### 10.8 PEIS 能力引擎(批568 收留 —— 省 token 的正主)

AI 讀全文原始碼是最貴的一件事。PEIS 把「同功能、不同名稱」的引擎函式**聚眾成能力**,
測試通過才封印,之後 AI **只讀能力卡**就能呼叫能力,不必讀全文。本境實測:
VDF+VRN 674 檔 / 14,984 函式 → 2,606 能力、折疊 10,436、省 **99.92%**;
CGC+SUP 1,780 檔 / 31,416 函式 → 7,291 能力、折疊 18,694、省 **99.95%**。

```powershell
via-peis                       # 收容正本在不在 + 它自己的 69 檢
via-peis scan --family vdf,vrn # 聚眾→測試→鎖定→能力卡(AUDIT · 零網路 · 不改來源)
via-peis cards <能力>          # 讀卡(不讀原始碼)
via-peis run <能力> --params '{"k":v}'   # 快速截取層 RUN(capability, params)
```

細節、來源 commit、上游缺陷與紀律 19 檢:**`docs/VIA_PEIS_B568.md`**。
**沒有 `--apply`** —— 能力表落地與引擎鎖定是操作員的裁定。

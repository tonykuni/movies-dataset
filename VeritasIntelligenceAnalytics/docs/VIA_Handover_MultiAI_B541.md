# VIA 交接報告 · 多 AI 協作版(批541 · 2026-09-17)

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
| **短令冊** | `Register-VIA-Commands-v0211.ps1` | 所有 `via-*` 短令的來源。**尾版律**:永遠點最新那一支 |
| **中央控管台** | `supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0111.py` | 唯一對接口(律 L20)。`registry-sync --apply` 是元件冊的**唯一寫者** |
| **自測格** | `supportive modules/registry/CGC_MDL064_SelftestGrid_v0321.py` | **230 站**驗收閘。要判斷系統健不健康,跑這一支就夠 |

### 程式碼分佈(實測檔數,不含收容件與 `__pycache__`)

```
functional modules/VDF    182 .py   資料鍛造(價格/籌碼/月營收/ETF)
functional modules/VRN    299 .py   研報擷取(PDF→欄位→入庫→文摘)
functional modules/VAP    246 .py   自動繪圖與產出
supportive modules      1,635 .py   治理/登錄/工具(其中 registry 751 支)
```
中央治理家族(CGC_MDL***)**126 個**模組編號。

---

## 二、資料庫在哪

**一句話:正典庫都在 `functional modules/<家>/…` 底下,`VIA_Reports/` 底下的全是產物與沙盒,不是正本。**

### 正典庫(有真資料的)

| 庫 | 路徑 | 本境實測 |
|---|---|---|
| **台股總庫** | `functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb` | 147 MB · 22 表 · `features_daily` / `prices_canonical` / `tw_daily_prices` / `tw_prices_adj` 各 **577,733 列** · `tw_trading_daily` 57,649 |
| **國際總庫** | `functional modules/VDF/output_hub/mega/vdf_global_market.duckdb` | 16 MB · 9 表 · `features_daily` / `gl_prices_adj` / `global_daily` 各 **47,973 列** |
| **主動式 ETF** | `functional modules/VDF/output_hub/active_tw_etf/…/ActiveTWETF.duckdb` | 3.6 MB · `holdings_daily` 1,125 · `active_tw_etf_universe` 154 |
| **研報庫** | `functional modules/VRN/db/vrn_reports.duckdb` | 576 KB · `vrn_report_basic` **2 列** ← **本境幾乎是空的** |

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
所有防呆都寫在橋這一側。目前 6 個收容夾、共 72 件。

---

## 三、GitHub 連結

| 項目 | 連結 / 值 |
|---|---|
| 倉庫 | https://github.com/tonykuni/movies-dataset |
| **開發分支** | `claude/via-envmanager-governance-7cls8h` |
| **PR** | [tonykuni/movies-dataset#37](https://github.com/tonykuni/movies-dataset/pull/37) → base `main` |
| 目前 HEAD | `81e4054c`(批541b) |
| 上一批 | `f5def0d6`(批541)· `36be0197`(批540)· `594b51a4`(批539) |

**規矩(不可違)**:只推這一個分支 · **不 force push** · 不自己 merge、不自己 approve PR。

---

## 四、多 AI 協作開發

### 目前已經發生的協作(git 實測,不是規劃)

```
Claude Opus 5      126 commits    session_01RLMQGZLcigd5Bt5aN6J4Ck  (184 筆帶此 session 標)
Claude Fable 5.1   116 commits    session_01R2d69oa1AGvnPVwjSUdSv5  ( 58 筆帶此 session 標)
tonykuni (人)      145 commits    裁決者
```

兩個不同模型、兩個不同 session,在**同一個分支**上接力做了 240+ 批。能接得起來,是因為有下面五樣東西:

### 協作靠的五樣共用件(接手前先認識它們)

| # | 件 | 路徑 | 它解決什麼 |
|---|---|---|---|
| ① | **台帳**(只增不減) | `supportive modules/registry/VIA_AutoCode_Registry_v0100.json` | **1,073 筆**。每一批做了什麼、為什麼這樣做,全寫在這。接手第一件事是讀最後 3 筆 |
| ② | **律與教訓** | `supportive modules/registry/VIA_Policy_Laws_SSOT_v0100.json` | **律 59 條 · 教訓 90 條**。教訓都是**踩過才寫**的,每條都有批次編號可回溯 |
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

---

## 五、交接報告有哪幾份(別找錯)

| 檔 | 大小 | 誰產的 | 看它的時機 |
|---|---|---|---|
| **本檔** `docs/VIA_Handover_MultiAI_B541.md` | ~12 KB | 手寫 | **冷啟動、換人、換 AI** ← 從這裡開始 |
| `docs/VIA_Handover_20260914_B498.md` | 152 KB | 手寫累積 | 想知道某一批**為什麼**那樣做。批498 至今逐批記錄 |
| `docs/VIA_Handover_ONEPAGE.md` | 260 KB | `via-vcgc page --publish` 自動產 | 要機器全量快照(政策庫/邏輯庫/因子庫/資料庫/調度/多矩陣…十二段) |
| `../VIA_HANDOVER_LATEST.md` | 260 KB | 同上(倉庫根副本) | 同上。給不進 VIA 夾的人看 |
| `supportive modules/ui_support/VIA_UI_MasterControl_v0100.html` | — | `VIA_SYSTEM_MANAGER --no-open` | 要用**瀏覽器**看 81 項正式任務 |

---

## 六、現在卡在哪(接手就看這節)

### A. 等操作員一句話才能動的

| 件 | 狀態 | 要什麼 |
|---|---|---|
| 三支評等落差引擎 | **一支都還沒接** | ENG073 報告結構庫(中風險)→ 首頁全能 v0125(低)→ TW02(低)。建議一支一支,每支都用同一份 64 份語料驗零回歸 |
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

## 七、批541 收在哪裡(最近一批)

- `f5def0d6` 批541:券商表去衝突(撞名 0 · 45 家)· 候選同義字 harvest(只提不寫冊)· 收容件導入驗證 ⑱ + 負控 ⑱'
- `81e4054c` 批541b:補短令 `via-vrnrules`(批540 漏了七處之一)
- 實測:ENG086 v0105 **19/19** · 64 份語料**零回歸**(券商 64/64 · 評等 36 · 目標價 30 · 真 RED 0)· 樞紐 **10/10** · 自測格 230 站 OK 227
- 新教訓:**LL88**(檔案在≠導得進來;檔案對冊≠驗過)· **LL89**(永遠回 0 的濾網=假綠燈)· **LL90**(同義的裁定權在操作員)

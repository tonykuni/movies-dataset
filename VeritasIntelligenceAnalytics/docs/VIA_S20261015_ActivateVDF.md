# VDF 獨立啟動 ActivateVDF · 實測 · 檢查 · 補強(2026-10-15)

操作員令(原話):「VCGC VDF VRN 都是獨立系統 現在範圍限縮在 VDF 其他不管 實測 檢查 補強 用 VCGC 工具進行檢視
AST 注入每個 PS PY 檔案都要用加速器覆蓋率 100% VDF 檔案都要導入網路工具 ActivateVDF.py 啟動一切並連結 html u/i
在開始指令前第一個動作為優化 cpu dram 狀況優化 在 cpu/dram 允許範圍內三個獨立流程同步進行 善用 temp 支援不足的記憶體
先掌握生成台股個股清單及主動式台股 etf 清單引擎順利產出所有清單作為重要輸入之二後逐一啟動檢查修復各引擎
檢視現在資料庫現況補不足」;「他是獨立系統有自己的 main 跟其他相關 跟其他系統互不干擾」。

範圍:只有 `functional modules/VDF/`。VCGC / VRN 的檔、冊、號一個都沒改;VCGC 工具只拿來**只讀檢視**(token · handoff check ·
雙橋清掃器 audit · pslint · dbcard · 擊斃閘)。

## 一鍵啟動

```powershell
python "VeritasIntelligenceAnalytics\functional modules\VDF\ActivateVDF.py"                 # 全部:① → ② → ③ → ④,開總覽頁
python "VeritasIntelligenceAnalytics\functional modules\VDF\ActivateVDF.py" plan            # 只看計畫
python "VeritasIntelligenceAnalytics\functional modules\VDF\ActivateVDF.py" resources       # 只做 ① 並印資源卡
python "VeritasIntelligenceAnalytics\functional modules\VDF\ActivateVDF.py" --selftest      # 14 檢(沙盒 · 假管理員 · 零網路)
```

要真抓資料(清單 + 擷取 + 補不足),在**同一個視窗**由操作員自己開雙閘後再跑(AI 永不代設):
`$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='<有效值>'`,補不足真跑再加 `--refill-apply`。

| 步 | 內容 | 走誰 |
|---|---|---|
| ① CPU/DRAM(第一個動作) | 量核數 · 負載 · 可用記憶體 → gc → 並行條數 = min(3, 可用核−1, (可用−1 GB) ÷ 1 GB),至少 1 → 每條執行緒上限 · DuckDB 記憶體上限 → temp 溢寫夾(`VIA_TEMP_ROOT` > `%LOCALAPPDATA%\VIA_TEMP` > 系統 temp,不在 OneDrive;只留最近 5 輪)→ 背景記憶體壓力閘(可用 < 10% 時新步驟先等) | 本檔自己(不載入他系統) |
| ② 兩張清單 | `fetch run 009` · `fetch run 010` 同時跑 → `fetch verify 009 010`;本輪產出 = GREEN · 閘關但既有清單驗收過 = YELLOW 照用 · 都沒有 = 擷取流程 BLOCKED | VDF_SystemManager 尾版 → MDL008 → MDL009 / MDL010 |
| ③ 三條獨立流程(同時) | 擷取:`fetch run <擷取冊其餘 34 列> --mode live --apply` · 引擎:`engine list` → `engine launch <全部>`(逐一載入 + 自測)· 資料庫:`db check` → `refill`(預設只列計畫) | 同上 |
| ④ U/I | 管理員 `ui` → `VIA_Reports/vdf/VDF_UI_latest.html`;總覽 `VIA_Reports/vdf/activate/ACTIVATE_VDF_latest.{html,json}`(燈 · 資源卡 · 每步一列 · 連 VDF 操作頁 / 資料庫閘 / 引擎矩陣),開瀏覽器 | 同上 |

rc:0 全綠 · 2 有黃 / 閘關 / 擋下(不算綠)· 1 有紅。

## 新檔(只增不減,舊版一個位元都沒動)

| 檔 | 為什麼 |
|---|---|
| `VDF/ActivateVDF.py` | 固定檔名入口(操作員指定);只找本體尾版交 main |
| `VDF/VDF_MDL013_ActivateVDF_v0100.py` | 本體;自測 14/14 |
| `VDF/VDF_MDL012_FetchGroups_v0106.py` | 實測修:① `find_db` 家優先(v0100 按檔案大小挑,倉內 15 MB 舊庫蓋過 `--home` 新庫;自測 `KeyError: 'lag_days'` 崩)② 前版自測 ⑫ `optimize --apply` 經 find_db 對倉內**真庫**做 CHECKPOINT + ANALYZE(沙盒外洩;CI 沒真庫從沒響)→ 跑前版鏈自測期間封倉。全鏈 rc 0,真庫 md5 不變 |
| `VDF/VDF_MDL011_AkshareFetcher_v0103.py` | 實測修:沒 polars 時 v0102 載前版鏈就崩(rc 1)→ 缺套件 = `[ABSENT]` rc 2 NODATA;v0102 自測吞掉前版鏈紅回 0 的假綠一併改回照實 |

## 實測(容器 · 2026-10-15)

- 雙橋覆蓋(VCGC 雙橋清掃器 audit,活樹判準 = CGC_MDL158):VDF 活樹 .py **115/115 加速器橋 · 115/115 網路橋**;
  PS 尾版(pslint)缺加速 0 · 自吞頁 0。
  不在分母的照實列:`references/intake/` 66 支 .py + 7 支 .ps1 = 收容正本(KILL-03 正本零觸碰);
  已被新版蓋過的舊版 30 支缺網路橋 · 1 支缺加速橋(KILL-02 尾版律:出了新版,舊版一個位元不准動;執行期由尾版的橋載入,同一行程生效)。
- VDF 活樹 115 支自測(三條並行):rc0 83 · rc2 10(全是缺 rich / gspread 等套件的誠實 NODATA)· rc3 1(ENG086 缺 polars)·
  沒自測 16(無版號舊件)· **rc1 2 → 已修**(MDL012 v0106 · MDL011 v0103)。
- ActivateVDF 容器真跑(live;閘關):① 核 4 · 可用 15.4/16.1 GB → 並行條數依流程數算(3 條流程 = 3 條 · 每條 1 執行緒)· 記憶體閘最低可用 14.4 GB、等待 0 次;
  ② 清單 GATED(同意閘)→ 擷取流程 BLOCKED;引擎流程 **94/94 可啟動 · 自測 GREEN 67 · NODATA 8 · RED 0 · 沒自測 19**
  (按家族全名啟動,同號異名 ENG110 ×3 / ENG117 ×2 / ENG118 ×2 都起);`_rebuilds_superseded/` 6 支被取代件不啟動、照實列
  (第一輪按 eid 啟動時 MDL005 / MDL103 被取代件載入失敗 → 已改);資料庫流程 RED = 資料真缺(見下);U/I 頁產出 GREEN。
- 清單引擎:MDL009 v0102 自測 5/5 + 前版 PASS · MDL010 v0100 7/7;經管理員 `fetch run 009 010 --mode fixture` 全鏈 4/4 檔驗收過;
  `--mode live` 在容器 = rc 4 GATED(同意閘是操作員的手)→ 真清單要在工作站開閘跑。
- 資料庫閘(`db check`,容器的庫是 09-24 未追蹤舊快照):RED 34(缺表 26 · 空表 5 · 缺庫 3)· YELLOW 22 · GREEN 7。
  缺口追到根全要上網(例:`tw_universe` 要先有籌碼 `tw_chip_*` ← ENG056;`tw_financial*` ← ENG082 MOPS;`us_macro` ← FRED);
  其中 `vrn_*` 8 張是 VRN 寫的表,不在本範圍。容器裡沒有能離線補的 → ActivateVDF 的資料庫流程在工作站開閘後 `--refill-apply` 補。
- 擊斃閘 CGC_MDL187 v0103(--run-selftest):11 條全過,債 2 筆(兩支薄尾委派前版自測,屬正常)。

## 留給下一步

- 已查清不必動:`VDF_FetchSystem_SSOT` v0106 把 MDL011 釘在 v0102,但擷取系統(MDL008 v0101 起)起子行程前先比對列上的
  `requires`(akshare · polars · duckdb),缺件直接 rc 3、零子行程(容器實測 `fetch run 011 --mode block` → `[rc3] MDL011 0.0s`)。
  MDL011 v0103 管的是「直接起引擎」(`engine run MDL011`)那條路。
- 工作站跑一次 `ActivateVDF.py`(開閘)拿真清單與補不足的收據。

## 工作站實測 · v0101(2026-10-16)

worktree `C:\Users\tonyk\via-main`(origin/main `b1e0064`)· 家族境 `via_vdf_312`:

- `ActivateVDF.py --selftest`:**16/16 PASS**(8 核 · psutil)· `plan`:管理員 v0154 · 擷取冊 v0106 · 並行 3 條。
- 真跑(雙閘由操作員本視窗開;`--fetch-home <OneDrive 倉 VDF 夾> --db-home <同上>\output_hub --refill-apply`):
  ① 8 核 · 可用 7.7/16.1 GB → 並行 3 條 · 每條 2 執行緒 · DuckDB 1335 MB;**② 兩張清單 GREEN(本輪產出且驗收過)**;
  ③ 三條流程起跑後 v0100 一行都不印 → 操作員看成「卡斷」按 Ctrl+C → traceback、總覽沒寫(讀到的是更早一輪的舊 JSON)。

### v0100 → v0101 修的三件(`VDF_MDL013_ActivateVDF_v0101.py`;固定入口 `ActivateVDF.py` 自動取尾版)

| 件 | 根因 | 修法 | 證據 |
|---|---|---|---|
| 看起來卡住 | 流程跑完前完全沒輸出(擷取 34 列,單列上限可到 4 小時) | 心跳:每 `VIA_ACT_HEARTBEAT_S` 秒(預設 30)印在跑的步 · 已跑時間 · 它日誌最後一行 · 可用記憶體;每步完成一行。子行程 `PYTHONUNBUFFERED=1` | 自測 ①② · 容器真跑心跳 63 段 |
| Ctrl+C 收不乾淨 | 主執行緒 KeyboardInterrupt 直接拋;子行程(管理員 → 引擎)沒收、可能還握 DuckDB 鎖;沒寫總覽 | 子行程自成行程組;SIGINT 處理器先收整棵樹(Windows `taskkill /T /F`、POSIX 行程組)再設停止旗標;還沒起的步不再起;照寫總覽,燈 `INTERRUPTED`、rc 130 | 自測 ③④⑥⑧(⑧ = 清單階段真送 SIGINT,端到端:0 殘留、無 traceback) |
| 清單間歇 rc 1 | 兩支清單引擎都寫 `vdf_master_lists.duckdb`,v0100 讓它們同時跑 → `IO Error: Could not set lock on file ... Conflicting lock is held`(容器重現 3 次中 2 次;工作站那輪 GREEN 是時機錯開) | 兩張清單依序跑;資料庫流程(db check / refill)等擷取流程寫完才開庫;引擎流程(自測在沙盒)照樣並行 | 自測 ⑨⑩ · 容器 fixture 連跑 3 輪清單 3/3 GREEN、資料庫流程確實等擷取 |

v0101 自測 10/10(連跑 3 輪穩定)+ 前版鏈 16/16;擊斃閘 11 條全過(債 1 = 薄尾委派前版自測)。

## PR #527 Codex 兩條 P1 與登錄收尾(2026-10-16)

- **P1 記憶體閘等待不理會 Ctrl+C**(成立):壓力中卡在 `MemGate.wait`(最多 600 秒)的步還沒有子行程,`interrupt()` 收不到;收尾又逐條各等 60 秒。
  → v0101 `gate_wait`:每 0.5 秒看停止旗標;中斷收尾改全部流程共用一個 60 秒期限。自測 ④b:壓力中按 Ctrl+C 1.0 秒放手、零子行程。v0101 自測 11/11。
- **P1 新版沒登錄**(成立,PR #526 也漏):交接閘報 `MODULE_UNREGISTERED`(ActivateVDF.py · MDL013 v0100 / v0101)與 `CHANGED_CODE_WITHOUT_TEST`。補齊:
  - 需求冊 v0196 新增 **VDF-REQ018**(PARTIAL;工作站 v0101 全流程收據待回)· 編號 `VIA-VDF-REQ018`
  - `ActivateVDF_v0100.py` = 固定入口的內容相同雙胞(照 PR #518 裁定),讓 registry-sync 登冊;原檔照用
  - registry-sync --apply:新 65 · 變更 15(先在暫存副本試寫核對 = 全部是 VDF 本批元件,零他系統條目)
  - 交接案 `vdf_activatevdf` · `vdf_fetchgroups_home`(經 VDF_SystemManager engine run)rc 0 · 標記見到 → VERIFIED;重測 `vdf_activate` · `vdf_akshare_card` · `numbering` · `chain` 全 rc 0
  - 盤點冊 v0170 登兩新案站(CGC_MDL224 ⑧)
  - 編號(R04 先提交再編號):REQ +1 · LGC +5 · MDL +3 · FNC_VDF +43 · ENV +2(含補 PR #526 漏編的 MDL012 v0106 / MDL011 v0103);稽核 遺失 0 · 改身分 0 · 重號 0
  - SDD:X-NUM 的 VDF 項清零(REQ 453 全編);剩 CGC_MDL140 v0107 · CGC_MDL183 v0105 · VRN_ENG086 v0120 三支他系統尾版未編號(主線既有)
- 交接閘:本批 VDF 項全清。剩 5 條 RED 都是開工前第一次 `handoff check` 就在的(ENG086 v0102 容器缺 polars 自測 rc 3、交接案要 rc 0 → 待工作站;VRN FirstPage v0130 · SUP_MDL749 v0116/v0117 · CGC_MDL264 屬他系統),checkpoint 照實記 RED,**不寫成成功**。
- 擊斃閘:KILL-11 對 `ActivateVDF_v0100.py` 誤判(**VCGC 工具缺陷,未改**):CGC_MDL187 `_tail_on_ref` 的正則 `ActivateVDF_v(\d{4})\.py$` 用 `search` 沒錨定檔名開頭,
  配到 origin/main 上的 `VDF_MDL013_ActivateVDF_v0100.py` 當同家族 → 判「版號比基線舊」;以檔名錨定比對,同家族在 origin/main 上 0 支 = 全新一族,本該放行。
  其餘 10 條全過。修法建議(給 VCGC 自己的線):`rx.search(line)` 改比對 basename 全名(`re.fullmatch`)。

## 工作站實測 · v0101 → v0102(2026-10-18)

工作站(8 核 · 可用 4.4 GB · Python 3.12 · worktree 在 main `7339d5d88`)回報:自測兩次 **10/11 FAIL**(⑩);開雙閘真跑 ② 兩張清單 **GREEN**
(009 70.2 秒 · 010 54.2 秒 · verify 17.4 秒 · 依序跑,沒撞寫入鎖)→ 擷取 `fetch_run_all` 15:25 起、資料庫流程照設計 `[等候]`、引擎 15:26 起與擷取並行,心跳每 30 秒一段。
回報時擷取與引擎流程還在跑(③ 結果 · `[計]` · `ACTIVATE_VDF_latest.json` 摘要待回)。看到三個問題,v0102 薄尾修(v0100 / v0101 一個位元都沒動):

| 工作站看到 | 根因(容器重現) | v0102 修法 | 證據 |
|---|---|---|---|
| 自測 ⑩ FAIL `(2.21, 1.43, GREEN×3)` | ⑩ 要 engine launch 在擷取起跑後 0.55 秒內起;引擎流程要先起 engine list 子行程、再起 engine launch,Windows 起一支 Python 約 1 秒 → 必超過。容器用 sitecustomize 讓每支子行程慢 0.8 秒,v0101 ⑩ 同樣 FAIL `(1.47, 0.83)` | ⑩ 的門檻寫錯(把 Linux 起行程快當前提),流程本身是對的(真跑兩條確實並行)。**不能**把 engine list 挪到清單階段:v0100 ⑤ 釘住「清單跑完才起三條流程(含 engine list)」= 操作員令「清單引擎先跑」。→ 本版 ⑫ 換掉 ⑩:同一性質(清單依序 · 清單後才 engine list · engine launch 起跑時擷取還在跑 · 資料庫等擷取跑完),每支假步驟 3 秒、子行程慢 0.8 秒照樣要過;委派前版自測只容 v0101 ⑩ 這一條失敗(照印「由 ⑫ 取代」),其餘任何一條失敗照判 FAIL,並補跑 v0100 自測(v0101 失敗時不往下委派) | 慢 0.8 秒:v0102 6/6 · v0101 ⑩ 被取代、其餘 10 條過 · v0100 16/16 · rc 0;正常:v0102 6/6 · v0101 11/11 · v0100 16/16(Python 3.11 / 3.12 都 rc 0) |
| `VDF_MDL013_ActivateVDF_v0101.py:635: SyntaxWarning: invalid escape sequence '\]'`(每次載入都印;引擎啟動那段心跳的「最後一行」也被它佔走) | v0101 ⑦ 的同意閘正則後半段少了 `r` 前綴;Python 3.12 編譯時警告 | v0101 已發佈不改;本版載入前版時只在載入那一刻擋 SyntaxWarning / DeprecationWarning(執行期警告照常)。心跳「日誌最後一行」略過 `SyntaxWarning` · `DeprecationWarning` · `<unknown>:N:` 這種編譯雜訊,顯示真正的進度行 | ⑪ 重新編譯(`-X pycache_prefix` 新夾 · `-W always`)零 invalid escape;⑮ |
| lists_run_010:`Error. nthreads cannot be larger than environment variable "NUMEXPR_MAX_THREADS" (2)`(不致命,清單照樣 GREEN) | v0100 把 `NUMEXPR_MAX_THREADS` 設成每條執行緒數(2);子行程裡的加速器 Celeritas `apply_thread_limits` 再把 `NUMEXPR_NUM_THREADS` 拉高 → numexpr 拒絕 | `NUMEXPR_NUM_THREADS` = 每條執行緒數(用量照舊受限);`NUMEXPR_MAX_THREADS` = 核數 × 2(只是天花板,不再比加速器設的用量小)。OMP / MKL / OPENBLAS / POLARS / VIA_DUCKDB_THREADS 不動 | ⑭ |
| 引擎流程起跑前約 68 秒心跳只列擷取一步 | v0100 的 engine list 用 `subprocess.run`(沒登記):心跳看不到;Ctrl+C 也收不到它(最多再跑 600 秒) | engine list 改 Popen 登記在跑:心跳列得到 `engine_list`、Ctrl+C 一起收、引擎流程記 INTERRUPTED(不是紅);完成印一行「N 支要啟動 · M 支已被取代」 | ⑬;容器真跑 `[完成] engine_list · GREEN · rc 0 · 8.9s · 94 支要啟動 · 6 支已被取代(不啟動)` |

- 擊斃閘 CGC_MDL187 v0103 `--run-selftest`:11 條全過(債 1 = 薄尾委派前版自測)。
- 交接案 `vdf_activatevdf` 標記改 `[計] VDF_MDL013_ActivateVDF v0102 本版 6/6 · PASS`;新交接項 `VDF-REQ018:activatevdf-v0102`;`VDF-REQ018:workstation-v0101` 照實留 PENDING(收據未完)。
- 引擎啟動那段心跳的另一行 `<unknown>:3: SyntaxWarning: invalid escape sequence '\*'` 來自 **VCGC 自己的** `CGC_MDL156_VIAAcceleratorControl_v0114.py` 第 3 行 docstring(`Scripts\*.py`),
  依 L120 三系統獨立不代修,只記在這裡給 VCGC 的線。VDF 自己另有三支舊檔有同類警告(都是已發佈的前版,本批沒碰):
  `VDF_MDL011_AkshareFetcher_v0100.py:3` `\V` · `VDF_ENG093_LaunchConsole_v0101.py:591` `\d` · `engine/VDF_ENG051_ActiveTWETF_Holdings(_v0101).py:2` `\d`。

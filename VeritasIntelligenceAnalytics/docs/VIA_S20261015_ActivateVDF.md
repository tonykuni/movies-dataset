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
- PR #528 Codex P1(成立):委派尾段 `return 0 if rc1 == 0 else (rc1 if rc1 in (2, 3) else 2)` 會把前版自測的紅(rc 1)改成 2,
  管理員把 2 判 NODATA → 真退步被降級、模組照樣可啟動。改成前版回什麼就回什麼(0 / 1 / 2 / 3;其他值 → 1)。
  變異測:v0101 其他條紅 → 1 · 只 ⑩ 紅但 v0100 紅 → 1 · 前版 2 → 2 · 前版 0 → 0;全鏈自測正常 / 慢 0.8 秒都 rc 0;擊斃閘 11 條全過;交接案重測 rc 0。

## 工作站實測 · v0102 → v0103 + PS 一鍵(2026-10-18)

工作站更新到 `bd32a6717`(含 v0102)後 `--selftest`:⑪ ⑫ ⑬ 過,⑭ 丟 `TypeError: dict() got multiple values for keyword argument 'NUMEXPR_NUM_THREADS'`。
⑭ 的「有裝 numexpr 才真測」段把子行程環境寫成 `dict(os.environ, **{…NUMEXPR_*…}, NUMEXPR_NUM_THREADS=…)`,同鍵給兩次;
容器沒裝 numexpr 走「只驗數字」分支,所以沒現形(容器用 numexpr 測試替身重現)。執行邏輯(用量 = 每條執行緒數 · 上限 = 核數 × 2)本身沒錯。

- **v0103 薄尾**:⑰ 取代 v0102 ⑭ 的真測段 —— 加速器把用量拉到核數時本鏈環境不印 `nthreads cannot be larger`,
  同一探針在 v0100 環境(上限 = 每條執行緒數)必印得出(證明抓得到病);沒裝 numexpr 用照同一規則的替身。
  委派 v0102 自測時讓那一段 `import numexpr` 走 ImportError 分支(數字照驗),其餘照跑;前版紅照實回。
  有 numexpr(替身)/ 沒 numexpr 兩種全鏈 rc 0;擊斃閘 11 條全過;交接案 `vdf_activatevdf` 改 v0103 標記 rc 0。
- **PS 一鍵 `functional modules/VDF/Invoke-VDF-Activate-v0100.ps1`**(操作員令「FIX ALL AND INTEGRATE ALL INTI A PS CODE WITH ACCELERATORS AND NETWORK MODULES.」= L70 許可 P019,新檔、不動任何舊 .ps1):
  ① 加速器 PS 端(`[VIA:PS-TEMPLATE:v0101]` Celeritas PS7 模板 + `[VIA:PS-ACCEL:v0101]` 25 格)② 加速器 Py 端(SUP_MDL737 尾版 `--selftest`)
  ③ 網路模組(`via_net_unified` 尾版 `--selftest` → SUP_MDL740 → VeritasAegisNexus 鎖版;離線)④ 同意閘只讀不寫(沒開照跑,印兩行讓操作員自己打)
  ⑤ ActivateVDF 自測(紅 = 停)⑥ ActivateVDF 真跑(`--no-open`;`-FetchHome` 給了 `-DbHome` 預設 `<FetchHome>\output_hub`;上限 `-TimeoutHours` 預設 12)
  ⑦ MATRIX SUMMARY(每步一列 + 總覽 JSON 拆成 CPU/DRAM · 清單 · 三流程 · U/I)+ `Open-VIAOwnPage` 跳總覽頁。python 只經 `Invoke-VIAPython`(VDF 家族環境)。
  容器 pwsh 7.4.6 實跑:preflight exit 0 · selftest exit 0 · run(engines)exit 2(同意閘沒開 → 清單 GATED;引擎 94/94 RED 0);
  ParseFile 錯 0 · CGC_MDL168 參數道 GREEN · pslint GREEN(tails 704 · no_accel 0 · own_page 0)· 全景 read 問題 0 · 擊斃閘過(P019 位元吻合)。
  收據 `docs/handoff/evidence/vdf_ps_launcher_pwsh.txt`。
- PR #529 Codex 兩條(都成立,未進線前同一許可 P019 重算 sha256):
  P1 先決步驟(加速器 / 網路模組自測)紅了結束碼還是 0 → `Merge-VDFExit` 取較壞者(0 < 2 < 1 < 124 < 130),preflight / selftest / run 都帶進結束碼;
  P2 本輪沒寫出新總覽仍開舊頁 → 只在總覽 JSON 是本輪寫的才開頁,否則印黃字不開。
  pwsh 實跑:正常 preflight 0 · 壞 python(/bin/false)preflight 1(兩列 RED)· 失敗真跑 1 且不開舊頁 · selftest 0;pslint GREEN;擊斃閘過。

## PS 一鍵 v0101:每次跑都確認全部 VDF 模組接了加速器與網路工具(2026-10-18)

操作員令「INTEGRATE INTO ONE PS CODE WITH 加速器模板並確保所有VDF模組都有導入網路工具 善用VCGC節省TOKEN工具注入AST上加速覆蓋到7全部」= L70 許可 P020(新檔 v0101;v0100 一字不動)。

**先量(經 VCGC 的橋掃器 CGC_MDL124 v0111 + 契約閘 CGC_MDL183 v0105,只讀):覆蓋已經全滿,這次沒有要注入的。**

| 面 | 量法 | 結果 |
|---|---|---|
| VDF Py 加速器橋 | `CGC_MDL124 --subsystems` | 140/140(100%);排除 393 = 版史 + `_sha` 存證副本(具名理由) |
| VDF Py 網路橋 | 同上 | 140/140(100%) |
| 全樹 Py 加速器橋 | 同上 | 1781/1781(100%) |
| VDF PS-ACCEL | `CGC_MDL124 --ps --ps-tail --root "functional modules/VDF"` | 掃 172 · 已掛 165 · 缺 0 · 排除 7 |
| PS 模板章 | `CGC_MDL183` | 全樹基線外新缺 0;既有債 28 支**沒有一支是 VDF**(VAP / WorkOps / intake 等,L70 操作員的手) |
| VDF 管理員自己的尺 | `VDF_SystemManager bridges` | 加速器 93/93 · 網路 93/93(真擷取 9)· 缺 0 |

**v0101 多一步 ③b 覆蓋檢查**(每次一鍵都跑,缺了就紅,不靠記得):
- 3b Py:VDF 自己的管理員 `bridges`(尾版逐支;尺 = CGC_MDL124 排除清單與真擷取判定,只讀)—— VDF 獨立,不經 VCGC 主控台。
- 3c PS:VDF 夾內每族尾版 `.ps1` 要有模板章 `CELERITAS-TEMPLATE-JOIN` 與 `[VIA:PS-ACCEL]`(排除 history / intake / 虛擬環境 / 已取代)。
- 缺 = 結束碼紅,並印 VCGC 的 AST 注入補橋指令(CGC_MDL124 `--subsystems` / `--ps --ps-tail` 先看計畫再 `--apply`);本支不代改任何檔(模板章是 .ps1 改動,L70)。
- 反證:放一支沒橋的 .ps1 → 3c RED;放一支在冊、會觸網、沒橋的 .py → 3b RED 指名;兩支都 exit 1(探針已刪)。

## PS 一鍵 v0102:工作站視窗殘件三件(2026-10-18)

操作員貼回工作站實跑(當時 main 還在 v0100;PR #530 合併前一刻拉的):自測全綠(v0103 2/2 · v0102 6/6 · v0101 10/11 而 ⑩ 由 ⑫ 取代 · v0100 16/16;v0102 ⑭ 的 TypeError 已不再出現),
結束碼 0 · AMBER,但有三件不是 VDF 程式本身、而是**操作員視窗裡別的東西**造成的毛病。L70 許可 P021(新檔 v0102;v0100 / v0101 一字不動)。

| 現象 | 根因(容器 pwsh 7.4.6 重現) | v0102 怎麼修 |
|---|---|---|
| ① 「Celeritas PS7 模板沒接上」黃;總表頭 `Celeritas  applied=False workers=` | Register 的 `Invoke-VIACeleritasScoped` 只匯出 `Restore-CeleritasPS7` 進視窗;模板塊看到它就以為已接而略過;`Get-CeleritasStatus` 不在 / 狀態空 | 模板塊沒由本支接上時,把正主點源進**本支範圍**重接(`[VDF:CEL-REJOIN:v0102]`);跑完還原;優先權前後都 Normal |
| 每個 Python 步驟前多印 `[DEPRECATED] Set-VIABoot 已覆蓋…` 與一行 `2` | 操作員 `$PROFILE` 最後點源的短令覆蓋檔把 `Set-VIABoot` 換成殘樁(印一行、`return 2`);中央 `Invoke-VIAPython` 每次都叫它 | **只在偵測到殘樁時**給本支範圍一個做原本那件事的安靜同名函式(`[VDF:BOOT-SHIM:v0102]`:VIA_ROOT + bootstrap 進 PYTHONPATH),跑完兩個環境變數還原;視窗裡那一個不動 |
| 每行尾巴殘字(`…_NET_CONSENT…` `]`) | 中央 `Invoke-VIAPython` 的進度條與本支逐行直播搶同一列 | 子步驟期間本範圍 `$ProgressPreference = 'SilentlyContinue'`(本支已逐行直播) |

重現與驗證(證據 `docs/handoff/evidence/vdf_ps_launcher_pwsh.txt`):仿操作員視窗(先跑一次 scoped 助手 + 殘樁 Set-VIABoot + 空狀態的總表函式 + 進度探針)——
v0101:① YELLOW、`[DEPRECATED]` + `2` 三次、進度條 Continue;v0102:① GREEN(重接)、雜訊 0、進度條 SilentlyContinue、PYTHONPATH / VIA_ROOT 前後相同、優先權前後 Normal、selftest exit 0。
乾淨視窗 v0102:preflight 0 · selftest 0(7 步 OK 6 · SKIP 1 · GREEN)。Parser 錯 0 · pslint GREEN(704 · no_accel 0 · own_page 0)· 擊斃閘 11 條全過(P021 位元吻合)。

**他系統的根(只報不改,L120):** `docs/handoff/ps/VIA-Commands-Override-v0102.ps1` 的 `$keep` 沒列 `Set-VIABoot`(中央 `Invoke-VIAPython` 要叫它),
建議 VCGC 側下一版把它加進 `$keep`;Register 的 scoped 助手匯出 `Restore-CeleritasPS7` 進視窗也會讓其他用 `Get-Command Restore-CeleritasPS7` 判「已接」的 PS 尾版誤判。

## PS 一鍵 v0103 + ActivateVDF v0104:每支 Python 起跑慢到逾時(2026-10-18)

操作員貼回工作站實跑 PS 一鍵 v0102。好的部分:① GREEN(Celeritas 正主重接成功),`[DEPRECATED] Set-VIABoot` 與 `2` 都消失了。壞的部分:

| 步 | v0100(工作站) | v0102(工作站) |
|---|---|---|
| ② 加速器自測 | 38.1 秒 | **300 秒逾時** |
| ③ 網路模組自測 | 15.7 秒 | **300 秒逾時** |
| 3b 覆蓋檢查 | — | 357.5 秒(容器約 1 秒) |
| ⑤ ActivateVDF 自測 | GREEN | v0103 ⑰ 的 `python -c "import numexpr"` **120 秒逾時**,丟 `TimeoutExpired` traceback |

**根因(容器重現):** v0102 的 Set-VIABoot 替身做「原本那件事」——把**本樹**(`C:\Users\tonyk\via-main`)的 `supportive modules\bootstrap` 疊到 PYTHONPATH 最前面。
但操作員 `$PROFILE` 早就放了**另一棵樹**(OneDrive)的同一夾。兩份 `sitecustomize.py` 同時在 PYTHONPATH 上,它的 `_chain_shadowed()` 會執行「sys.path 上下一份同名檔」→ 兩份互相接力,直到遞迴上限才停;每支 Python(連子行程)起跑都重做一大段 `_boot()`。
容器量:一份 bootstrap `python -c` 1.5 秒 → 兩份 10 秒;仿操作員視窗(另一棵樹的 bootstrap + VIA_ROOT 已設)跑 v0102 preflight 86 秒(② 39.7 秒)→ v0103 6 秒(② 1.3 秒)。工作站全裝 88 件冊、Windows 起行程更慢,就逾時了。

**修法(只動 VDF;v0100–v0102 與 ActivateVDF v0100–v0103 一字不動):**
- **PS 一鍵 v0103**(L70 許可 P022):替身只在 PYTHONPATH **還沒有任何** bootstrap 時才補本樹那一份,VIA_ROOT 已設就不動(= v0100 在工作站的環境);起跑先查 PYTHONPATH,兩份以上只留第一份(印 `[開機]` 一行),跑完還原。
- **ActivateVDF v0104**(薄尾):子行程環境(flow_env)只留一份 bootstrap(記 `VIA_BOOTSTRAP_DEDUPED`);numexpr 探針同樣去重,逾時照實回「出錯」不當機。
  自測 ⑲ 去重規則(含 Windows 反斜線)· ⑳ 真跑兩份 bootstrap → 子行程不再接力到另一棵樹 · ㉑ 探針逾時不丟 traceback · ㉒ 橋 / 他系統 / TA-Lib / 同意閘;兩個突變(拿掉去重、拿掉逾時捕捉)各被 ⑳ / ㉑ 抓到。

**他系統的根(L120:只報不改):** `supportive modules/bootstrap/sitecustomize.py` 的 `_chain_shadowed()` 只排除自己那一夾;PYTHONPATH 上有兩棵 VIA 樹的 bootstrap 時會互相接力到遞迴上限。
建議中央下一版:接力時跳過「也是 VIA bootstrap 的 sitecustomize」(同檔名 + 同標頭),或以環境旗標防重入。

## PS 一鍵 v0104 + ActivateVDF v0105:去重時空段照留(PR #532 Codex P2,2026-10-18)

PR #532(v0103 / v0104)由操作員合併後,Codex 的 P2 才到:去重先把 PYTHONPATH 的**空段**丟掉再拼回去;
Python 把空段當「目前目錄」,`bootstrapA::bootstrapB` 這種正好要去重的情況會連帶拿掉目前目錄。
已發布版不改,出新版(L70 許可 P023;v0100–v0103 與 ActivateVDF v0100–v0104 一字不動):
- **PS 一鍵 v0104**:只拿掉第一份之後的 bootstrap;空段、重複的一般路徑原樣原序保留(不再 `Select-Object -Unique`)。
  三例實測:`/a/b::/b/b:/z → /a/b::/z` · 只一份不動 · `:/a/b:x:/b/b/: → :/a/b:x:`。
- **ActivateVDF v0105**(薄尾):換上保留空段的 `dedupe_bootstrap`(v0104 的 flow_env 與 numexpr 探針呼叫時查模組全域 → 一換即生效)。
  自測 ㉓ 空段 / 開頭結尾空段 / 重複一般路徑都保留、子行程環境同樣保留;㉔ 橋。突變(改回丟空段)→ ㉓ FAIL。

## PS 一鍵 v0105 + ActivateVDF v0106 + VDF_SystemManager v0155:跑完自動跳出的頁直接清點資料庫(2026-10-19)

操作員令:「這裡專注 修正獨立系統VDF 自動跳出HTML U/I清點資料庫沒問題就是收尾」。
工作站 v0104 真跑:④ 雙閘沒開(新視窗)→ 清單 / 擷取 / refill GATED;**db_check RED**,但終端那一行被截斷,總覽頁只有一條「資料庫閘」連結 → 看不到哪幾張表、為什麼紅,也沒有「能不能收尾」。

**查因(容器同一支 db check,家 = VDF\output_hub,與工作站同一個預設):** RED 34 列裡
- 12 列是 **VRN 寫進 vdf_tw_market.duckdb 的表**(vrn_report_* · vrn_four_point_digest · via_policy_* …;寫入者 VRN_ENG074 / VRN_ENG082,或沒登寫入者但表名 vrn_)。VDF 的 refill 補不了也不該補(L120),卻把 VDF 的燈染紅 → 清點永遠過不了。
- 7 列是冊上 **min_rows = 0**(冊自己說可為空:tw_financial_mops · fwd_valuation_daily …),但 v0151 用 `min_rows or 1` 把 0 當 1 判。
- 其餘 18 列是容器部分副本的真缺(工作站的庫不同,要看工作站真跑的頁)。

**修法(只動 VDF;已發布版一字不動):**
- **VDF_SystemManager v0155**(薄尾,換 v0151 模組的 db_check / _print_db):他系統表 → INFO 照列不計燈(狀態寫「他系統表(VRN 寫)· 原狀態 · VDF 只攤開不代修」);min_rows 0:空 = 綠、缺表 / 缺庫 = 黃(待首寫);VDF 自己 min ≥ 1 的表判法不改。自測 ①–⑥(⑦ = 沒 duckdb 的分支)+ 全鏈 0 FAIL。容器真跑 RED 34 → 18。
- **ActivateVDF v0106**(薄尾):總覽 JSON 加 `db` 節;自動跳出的總覽頁在步驟表之前加「資料庫清點」:判定一句話(VDF 自己的表 0 紅 = 可收尾;黃不擋)· 計數卡 · 紅黃逐列(庫 · 表 · 狀態 · 列數 / 上次 · 最新日 · 寫入者 · 怎麼補)· 收合的綠列與他系統表。只認本輪起跑後寫出的 DB_CHECK_latest.json(舊檔 = NOT_RUN,不冒充)。卡片長路徑可折行(390 px 原本被 temp 路徑撐到 418 px)。自測 ㉕–㉘。
- **PS 一鍵 v0105**(L70 許可 P024):開跑即印同意閘(沒開就印要打的兩行,不用等到 ④);**Ctrl+C / 中途停 = INTERRUPTED 結束碼 130**(v0104 在 ② 中途 Ctrl+C 印「結束碼 0 GREEN」,容器 SIGINT 重現);主體丟錯 = 紅 1;總表多 **6⑤ 資料庫清點** 列,末段印 `[收尾]` 一行;-DbHome 沒給時操作員設的 VIA_VDF_DB_HOME 優先。

**收尾條件:** 工作站 v0105 真跑(雙閘本視窗親手開 · -RefillApply)→ 總覽頁「資料庫清點」VDF 自己的表 0 紅、終端印「[收尾] 資料庫清點沒問題」。

sha256:
- 0b738b925d753c1183fe0e7b5ae16330ddbbfee578ed65cf85dc6d5a9237ad44  functional modules/VDF/Invoke-VDF-Activate-v0105.ps1
- fb40540a3fdbfd779584892e48f9801717434d90eebfa1c893582700576005f5  functional modules/VDF/VDF_MDL013_ActivateVDF_v0106.py
- 44041f4bc0731754710dcddf8ba9ecb4752f5571052782717b03979aca2aa47b  functional modules/VDF/VDF_SystemManager_v0155.py

**PR #535 Codex 兩條 P2(未合併,直接改 v0106):**
- 落檔標成 v0102:v0102 外層在跑時把 schema 改回 v0102 再寫 → 本版先標 v0106 再直接交 v0100 原版寫;自測 ㉗ 照真跑開著 v0102 的 _IN_RUN(突變:改回走 v0102 外層 → ㉗ FAIL)。
- 2 秒容差可能吃到前一輪的 DB_CHECK:改成起跑記檔的指紋(mtime_ns · 大小 · sha256),寫總覽時指紋沒變 = NOT_RUN,沒有時間容差;自測 ㉕(突變:指紋永不相等 → ㉕ FAIL)。
  容器真跑:--flows db → 落檔 schema VDF_ActivateVDF_v0106;接著 --flows fetch(不跑資料庫)→ 清點 NOT_RUN「本輪起跑後沒重寫」。

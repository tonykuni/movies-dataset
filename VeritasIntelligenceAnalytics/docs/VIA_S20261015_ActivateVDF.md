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

## ActivateVDF v0107 + ENG045 v0102:記憶體 / TEMP 本輪真生效 · 全流程跑完(2026-10-19)

操作員令:「繼續 跑完貼回結果 對於記憶體跟TEMP支援方式用最快最佳的方法 自動完成」。

**量測(改前):** v0100 起每條流程已給子行程 TMP / TEMP / TMPDIR / POLARS_TEMP_DIR / VIA_DUCKDB_TEMP_DIR(本輪 temp 夾,
`%LOCALAPPDATA%\VIA_TEMP\ActivateVDF\run_*`,不在 OneDrive)· VIA_DUCKDB_MEM(每條預算)· 執行緒上限。
但 VDF 有 267 支直接 `duckdb.connect()`,**DuckDB 不讀環境變數** —— 只有 VCGC 的 CGC_MDL262_DuckTempHook 代裝進環境(.pth)後才補。
沒裝的境:DuckDB 溢寫落在**資料庫旁邊**(工作站 = `VDF\output_hub`,OneDrive 同步拖慢)、每支行程各吃實體記憶體 80%、執行緒 = 全部核(三條並行互搶)。

**最快最佳解(不改任何引擎、不裝進環境、不改他系統):ActivateVDF v0107**
- 每輪把一支小啟動鉤寫進本輪 temp 夾(`run_*/pyhook/sitecustomize.py`,不在倉內,舊輪照滾動清),排子行程 PYTHONPATH **最後**:
  中央 bootstrap 的 sitecustomize 本來就接力「sys.path 上下一份同名檔」→ 跑到本鉤;沒有 bootstrap 時本鉤就是那一份;本鉤跑完只往**後面**接力(不回頭、不遞迴)。
- duckdb 被 import 那一刻才掛(沒用 duckdb 的行程零成本);每個 `connect()` 呼叫端沒給的才補:
  `temp_directory` = 本輪流程 temp/p<pid> · `memory_limit` = 每條預算 · `threads` = 每條執行緒。子行程再起的孫行程同樣生效。
- 環境已裝 VCGC 的 `via_duck_temp` 鉤 → 本鉤讓位(不疊兩層);`VIA_DUCK_TEMP=0` → 不掛。
- 起跑實測約 1 秒:終端 `①b 記憶體 / TEMP` 一行 · 總覽頁「記憶體 / TEMP」卡 · `resources.memtemp`。
- 自測 ㉙–㉞(㉟ = 沒 duckdb 分支);突變:鉤不裝 → ㉚ FAIL · 不往後接力 → ㉛ FAIL · 不讓位 → ㉜ FAIL。

**容器全流程真跑(PS 一鍵 v0105 · 仿操作員視窗 · 雙閘沒開):** 593 秒 · `①b 記憶體 / TEMP GREEN`(溢寫 → 本輪 temp/probe/p<pid> · 記憶體 2.6 GiB = 預算 2841 MB · 執行緒 1 = 每條 · 鉤 VDF 本輪鉤);
加速器 / 網路 / 覆蓋 GREEN(Py 93/93 · PS 161/161);擷取 GATED(閘沒開);引擎 94/94 可啟動 · 自測 GREEN 65 · NODATA 8 · **RED 2**;資料庫清點 RED 18(容器庫是部分副本)。

**RED 2 查因 + 修正:**
- ENG045_OutputHub v0101 6/7:自測固定寫共用夾 `VIA_Reports/vdfout_runs/selftest_out`(每次先改名 .bak,已累積 150 支)。同一秒兩支自測 → 互相改名 / 占 DuckDB 檔。
  容器四支併跑三輪各 2 支 FAIL(parquet / duckdb 往返)重現;單跑永遠 7/7。→ **ENG045 v0102**(薄尾):自測把 EV 暫換成本次私有暫存夾再跑前版七檢,跑完刪;共用夾一字不動。新檢 ① 共用夾不動 · ② 四支併跑全過;突變(改回共用夾)→ ① FAIL。真跑照 v0101。
- ActivateVDF v0107 自測 5/6:在一輪真跑裡被引擎啟動檢查叫起時,帶到父輪的 `VIA_VDF_DUCK_HOOK` → ㉙ 誤判。→ 自測基底環境拿掉該標記(未合併,直接改)。
  兩支都在真跑環境經管理員 `engine run … --selftest` 驗過 rc 0。

**修正後第二次容器全流程真跑:** 505 秒 · ①b 記憶體 / TEMP GREEN · 引擎 94/94 可啟動 · 自測 GREEN 67 · NODATA 8 · **RED 0** · 加速器 / 網路 / 覆蓋 GREEN ·
擷取 GATED(閘沒開)· 資料庫清點 RED 18(容器部分副本;工作站要看自己的頁)· 結束碼 1(只因資料庫清點)。

sha256:
- 6ac6badea1a7fe2740c8ee4a99bab527ac7dbc0bd6fee8ea3ed3505f82c52b16  functional modules/VDF/VDF_MDL013_ActivateVDF_v0107.py
- 80af855844a199bf23d9a62b4b6bf1486894a8b7685b854138ec6b3a52aea55f  functional modules/VDF/VDF_ENG045_OutputHub_v0102.py

**PR #536 Codex P1(未合併,直接改 v0107):** 環境已有 VCGC `via_duck_temp` 鉤時,本鉤整個讓位 → VCGC 鉤只補 temp / 記憶體,**執行緒沒人管**(三條並行又互搶全部核)。
改:VCGC 鉤在 → temp / 記憶體照讓它管(不疊兩層),本鉤只另包一層補 `threads`(冪等標記 `_vdf_duck_threads`)。自測 ㉜ 改驗「讓位 + 執行緒照補」;
突變「VCGC 在就整個不掛」→ ㉜ FAIL。全鏈自測 0 FAIL · 擊斃閘過 · vdf_activatevdf / numbering 重測 rc 0。

## ActivateVDF v0108 → v0109 → v0110:溢寫不等 · VCGC 鉤機器自測 · 擷取後日期格式 + 跨來源對照(2026-10-19 ~ 20 · 分支 claude/optimistic-goodall-yhalc5)

範圍同上:只有 `functional modules/VDF/` 的 ActivateVDF 鏈(只增不改;前版檔一個位元都沒動)。VCGC / VRN 的檔、冊、號沒改;
VCGC 的 DuckDB 鉤只從子行程「看」它有沒有生效(不 import、不裝、不改)。三版都只在**自己 activate 那一輪**換上東西,跑完換回原樣
(前版自測驗的函式身分不變)。**編號 / 登錄冊沒寫**(那是 VCGC 的冊,本分支不碰;要登錄由 VCGC 自己的流程做)。

**v0108 — 溢寫模式時記憶體閘不等**(操作員令 2026-10-19:「自動修改 VDF 讓溢寫模式時不用等 · 用最快的方法完成指令」)
- 工作站(16 GB · 可用 620 / 1,142 MB):每步起跑前卡記憶體閘(可用 < 10% = 壓力)滿 600 秒、一行不印 → 40 分鐘裡約 30 分鐘空等。
  記憶體少時 v0100 本來就開溢寫(子行程 TEMP / DuckDB 上限 256 MB 起),v0107 再讓 DuckDB 真的溢寫到本機 TEMP → 溢寫模式再等是浪費。
- 起跑資源計畫是溢寫模式(可用 < 約 4 GB)→ 記憶體閘有壓力也直接起,每步印 `[溢寫不等]`;不是溢寫模式照 v0101 等;`VIA_ACT_SPILL_NOWAIT=0` 可關;
  資料庫等擷取寫完才開庫照舊(保資料)。總覽 JSON `spill_nowait` 節 · 總覽頁「溢寫不等」卡 · 長路徑手機寬折行。自測 ㉟–㊸。
- 端到端(記憶體固定 620 MB · 假管理員):2.8 秒 · 記憶體閘等待 0 次(7 步直接起);關掉(=0)→ 等 7 次。

**v0109 — 自測 ㊹ 取代 v0107 ㉚**(工作站一鍵 ⑤ 紅 → 不真跑)
- 工作站 `via_vdf_312` 境裡已有 VCGC(CGC_MDL262)代裝的 `via_duck_temp` 鉤。v0107 照自己的設計讓位,實際值全對
  (溢寫夾在本輪 temp · 記憶體 974.6 MiB = 預算 1,022 MB · 執行緒 2 = 預算 · `VIA_DUCK_TEMP=0` 不掛),但 ㉚ 寫死「生效的鉤必須是 v0107 自己的」;
  而且 v0107 在 ㉚ 失敗時不往下委派 → 工作站上 v0106…v0100 自測沒跑到。
- ㊹ 同一個性質重驗(先看境裡本來有沒有鉤 → 應生效的是它或 v0107 本輪鉤);委派時只容 v0107 ㉚ 一條失敗(印 `[取代]`)並補跑 v0106 → … → v0100
  (同 v0102 ⑫ 取代 v0101 ⑩)。反向:VCGC 鉤把記憶體設錯(300MB)→ ㊹ FAIL · rc 1 · 不往下委派。
- 工作站實跑(2026-10-20 02:05):⑤ 自測 v0109 5/5 · v0108 9/9 · `[取代]` · v0106…v0100 全 PASS → 進真跑:清單 GREEN(009 83.7 秒 · 010 73.0 秒 · 驗收過)·
  engine list GREEN(94 支要啟動 · 6 支已被取代)· 擷取 / 引擎啟動進行中(本文寫時尚未回報結束)。

**v0110 — 擷取後日期格式一律 YYYY / YYYY-MM / YYYY-MM-DD · 不同來源寫中間檔(TEMP · 標註來源)交叉對照 · 兩個以上來源相同 = 對照成功**
(操作員令 2026-10-20;「剩餘的你決定」)
- 現況(倉內盤點):TW 日收盤有兩個來源 —— 交易所 `tw_trading_daily`(TWSE / TPEX 官方 · 日期原樣存民國 7 碼 `1150824`,ENG057 又寫 ISO → 同一欄混兩種)
  × Yahoo `tw_daily_prices`(`2330.TW` / `.TWO`);月營收 `tw_monthly_revenue` 有 `source` 欄(MOPS_OFFICIAL × CNYES · `ym` 存 YYYYMM)。
  擷取流程裡沒有任何一步拿不同來源互相比對(ENG063 只取官方那筆;ENG098 / ENG102 不在擷取冊)。總經 `us_macro` 三支都是 FRED = 單一來源。
- 三條流程跑完後(資料庫只唯讀開):
  - ⑦ 日期格式體檢:資料庫家底下每個 `.duckdb` 的 VDF 表、每個日期欄 → 標準(YYYY / YYYY-MM / YYYY-MM-DD 字串或 DATE 型別)· 不標準格式與筆數 ·
    同一欄混兩種以上格式。他系統 `vrn_` / `via_policy` 表與 `fetched_at` 這類紀錄時間不列。
  - ⑧ 跨來源對照:TW 日收盤(最近 10 個交易日,`VIA_XSRC_DAYS` 可改)· 同表有 `source` 欄且兩個以上來源的(同來源同期多次取最新)。
    中間檔:`<本輪 temp>/xsrc/<資料集>/<資料集>__<來源>.csv`(`source` 欄標來源 · `date` 標準格式 · `date_raw` 原寫法 · `origin` 庫:表)+ `<資料集>__對照結果.csv`。
    判定:兩個以上來源相同 = 成功(第三個不同記離群)· 沒有任兩個相同 = 衝突 · 只有一個來源 = 沒得對照;價格到 0.01 · 營收整數 · 其他數值照兩邊較粗的小數位;
    衝突多半固定倍數 → 標「疑單位不同」。
  - 總燈:綠 + 有衝突 → 黃(不擋、不紅)。總覽 JSON `datefmt` / `xsrc` 兩節 · 總覽頁「擷取後:跨來源對照」卡(資料庫清點之前)· 終端 ⑦ ⑧。
- **決定:引擎的表不改寫成標準格式。** 各引擎 upsert 用自己的日期格式當鍵(例:`tw_trading_daily` 鍵 date+code+market),改寫既有列 → 下一輪原格式再寫進來就成重複列。
  標準格式寫在中間檔與對照結果;體檢逐欄列出還不是標準的欄。要讓庫本身也統一 = 逐支改寫入引擎 + 舊列搬鍵(下一步,另開)。
- 心跳:日誌最後一行另略過「警告下一行被印出的原始碼」(工作站每步都顯示 `VDF_SystemManager_v0155.py` 第 6 行那句舊說明;那支說明文字的 `\o` 只是警告)。
- 自測 Ⓐ–Ⓙ(有 duckdb 10 檢 · 沒有 7 檢):日期 53 種寫法 + 民國 7 / 5 碼 · 整欄判斷(成交量不當日期)· 對照規則 · 心跳 · 測試庫(工作站同名表)對照 / 中間檔 / 體檢 ·
  頁面卡跳脫 · 總燈 · 落檔標 v0110 · 換上的函式跑完換回 · 唯讀(沒有寫入語句)。
- 端到端(假管理員 · 測試庫):⑦ 不標準 3 欄(交易所 date 混用)· ⑧ 成功 5 · 衝突 1 · 單一 3 → 總燈黃;中間檔 7 個(`2026-08-24` · 原寫法 `1150824`)·
  頁面卡在資料庫清點之前 · Chromium 390 / 1280 寬不橫捲。

**驗證總表(容器 · 乾淨 checkout `b66ad194`)**

| 項目 | 結果 |
|---|---|
| `ActivateVDF.py --selftest`(境裡有 VCGC 鉤 · 仿工作站) | rc 0 · v0110 10/10 · v0109 5/5 · v0108 9/9 · v0107 5/6 → `[取代]` · v0106…v0100 全 PASS |
| 同上(沒 VCGC 鉤 · 有 duckdb)/(沒 duckdb) | rc 0 / rc 0(全 PASS,不需取代) |
| `VDF_SystemManager_v0155.py bridges` | GREEN · 加速器 93/93 · 網路 93/93 · 排除 0 |
| 一鍵(下面那一行)· 仿工作站 via-main(main e4ccd40e + 未追蹤 v0108 / v0109)· 跑兩次 | ② v0108 / v0109 / v0110 就位(git blob 核對)· ⑤ 替身跑真的自測鏈 rc 0 + v0110 端到端 · 結束碼 0 |
| 一鍵的其他情境(v0109 版時驗) | 本機 VDF_ROOT 指非 git 夾(工作站真況)→ 自動找 `%USERPROFILE%\via-main` · VDF_ROOT 不動;不能快轉 → 黃照跑;v0107 被改 → 紅不跑;blob 不對 → 紅不跑 |

**沒驗到的(不寫成綠):** 工作站真資料的 ⑦ ⑧ 數字(倉內沒有 VDF 資料庫);擷取 / 引擎啟動 / 資料庫流程在工作站跑完的結果(v0109 那輪進行中);
⑦ 的時間上限 120 秒只在換庫時檢查(單一超大庫可能多跑一點);`VDF_SystemManager_v0155.py` 說明文字的 SyntaxWarning 本身沒改(心跳已略過)。

sha256 · git blob:
- VDF_MDL013_ActivateVDF_v0108.py:cb6539bf13f4f4b63a733de4ae99417cefb23677810a7bd3499ec029c1ad8dee · 022689247f66210d85391e3a150679a6aa98b4bc
- VDF_MDL013_ActivateVDF_v0109.py:2af9633f3cad75d6a6662635950f5af2849c82515fded711d02385d301ca8949 · c3d6a62ba3c70373c01f566120ad3448e6e1e1cd
- VDF_MDL013_ActivateVDF_v0110.py:6575675356a205826349794795715d2326fa4e142561669c93d020b9d74067ce · 92f5c39fdbe548232679edca611dcdac02fa3c9a

**工作站一鍵(cmd 或 PowerShell 都能貼;要 PowerShell 7)**:更新 via-main(main 有的未追蹤舊檔先移到 `%TEMP%\vdf1_bk_*`)→ 從本分支放 v0108 / v0109 / v0110
(git blob 核對;main 收了就用 main 的)→ 開雙閘(操作員貼這一行 = 親手開 · 只在那個 PowerShell 行程)→ `Invoke-VDF-Activate` 尾版 `-FetchHome <VDF> -RefillApply`。
找倉:`VDF_GIT` > `%USERPROFILE%\via-main` > 目前夾 > `%USERPROFILE%\OneDrive\Documents\movies-dataset`(要有 `.git` 與 VDF 夾;不讀 `VDF_ROOT`,那是 VAP / 舊 VDF 工具的變數)。

```
pwsh -NoProfile -ExecutionPolicy Bypass -EncodedCommand dAByAHkAewBbAEMAbwBuAHMAbwBsAGUAXQA6ADoATwB1AHQAcAB1AHQARQBuAGMAbwBkAGkAbgBnAD0AWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgAfQBjAGEAdABjAGgAewB9AAoAJABCAHIAPQAnAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQAnADsAJABEAD0AJwBWAGUAcgBpAHQAYQBzAEkAbgB0AGUAbABsAGkAZwBlAG4AYwBlAEEAbgBhAGwAeQB0AGkAYwBzAC8AZgB1AG4AYwB0AGkAbwBuAGEAbAAgAG0AbwBkAHUAbABlAHMALwBWAEQARgAnADsAJABGADcAPQAiACQARAAvAFYARABGAF8ATQBEAEwAMAAxADMAXwBBAGMAdABpAHYAYQB0AGUAVgBEAEYAXwB2ADAAMQAwADcALgBwAHkAIgAKACQAUgA9AEAAKAAkAGUAbgB2ADoAVgBEAEYAXwBHAEkAVAAsACIAJABIAE8ATQBFAC8AdgBpAGEALQBtAGEAaQBuACIALAAkAFAAVwBEAC4AUABhAHQAaAAsACIAJABIAE8ATQBFAC8ATwBuAGUARAByAGkAdgBlAC8ARABvAGMAdQBtAGUAbgB0AHMALwBtAG8AdgBpAGUAcwAtAGQAYQB0AGEAcwBlAHQAIgApAHwAPwB7ACQAXwAgAC0AYQBuAGQAKABUAGUAcwB0AC0AUABhAHQAaAAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAIgAkAF8ALwAuAGcAaQB0ACIAKQAtAGEAbgBkACgAVABlAHMAdAAtAFAAYQB0AGgAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACIAJABfAC8AJABEACIAKQB9AHwAcwBlAGwAZQBjAHQAIAAtAEYAaQByAHMAdAAgADEACgBpAGYAKAAkAFIAKQB7ACQAUgA9AFsASQBPAC4AUABhAHQAaABdADoAOgBHAGUAdABGAHUAbABsAFAAYQB0AGgAKAAkAFIAKQB9AAoAJABIAD0AQAB7ACcAMAAxADAAOAAnAD0AJwAwADIAMgA2ADgAOQAyADQANwBmADYANgAyADEAMABkADgANQAzADkAMQBlADMAYQAxADUAMAA2ADcAOQBhADYAYQBhADkAOABiADQAYgBjACcAOwAnADAAMQAwADkAJwA9ACcAYwAzAGQANgBhADYAMgBiAGEAMwBjADcAMAAzADcAMwBjADAAMQBmADUANgA2ADEAMgAwAGEAZAAzADQANAA4AGUANgBlADEAZQAxAGMAZAAnADsAJwAwADEAMQAwACcAPQAnADkAMgBmADUAYwAzADkAZgBkAGIAZQA1ADQAOAAyADMAMgA2ADcAOQBlAGQAYwBhADYAMQAxAGQAYwBkAGEAYwAwADIAZgBhADMAYwA5AGEAJwB9AAoAZgB1AG4AYwB0AGkAbwBuACAAUwBhAHkAKAAkAGMALAAkAG0AKQB7AFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAkAG0AIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAJABjAH0ACgBmAHUAbgBjAHQAaQBvAG4AIABHAHsAZwBpAHQAIAAtAEMAIAAkAFIAIABAAGEAcgBnAHMAIAAyAD4AJABuAHUAbABsAH0ACgBTAGEAeQAgAFkAZQBsAGwAbwB3ACAAIgBbAFYARABGACAAAE51k10AIABQAG8AdwBlAHIAUwBoAGUAbABsACAAJAAoACQAUABTAFYAZQByAHMAaQBvAG4AVABhAGIAbABlAC4AUABTAFYAZQByAHMAaQBvAG4AKQAgALcAIABnAGkAdAAgAAlQIAAkAFIAIgAKAGkAZgAoACQAUABTAFYAZQByAHMAaQBvAG4AVABhAGIAbABlAC4AUABTAFYAZQByAHMAaQBvAG4ALgBNAGEAagBvAHIAIAAtAGwAdAAgADcAKQB7AFMAYQB5ACAAUgBlAGQAIAAnAFsAUgBFAEQAXQAgAIGJIABQAG8AdwBlAHIAUwBoAGUAbABsACAANwAoAHAAdwBzAGgAKQAnADsAcgBlAHQAdQByAG4AfQAKAGkAZgAoACEAJABSACkAewBTAGEAeQAgAFIAZQBkACAAJwBbAFIARQBEAF0AIAB+Yg1OMFIgAHYAaQBhAC0AbQBhAGkAbgAoAIGJCWcgAC4AZwBpAHQAIAAHgiAAVgBEAEYAIAA+WSkAtwAgAEhRIABzAGUAdAAgAFYARABGAF8ARwBJAFQAPQA8AAlQ742RXz4AIACNUbyMJwA7AHIAZQB0AHUAcgBuAH0ACgBmAG8AcgBlAGEAYwBoACgAJAB3ACAAaQBuACAAMAAsADIALAA0ACwAOAApAHsAUwB0AGEAcgB0AC0AUwBsAGUAZQBwACAAJAB3ADsARwAgAGYAZQB0AGMAaAAgAC0AcQAgAG8AcgBpAGcAaQBuACAAbQBhAGkAbgAgACQAQgByAHwATwB1AHQALQBOAHUAbABsADsAaQBmACgAIQAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACkAewBiAHIAZQBhAGsAfQB9AAoAaQBmACgAJABMAEEAUwBUAEUAWABJAFQAQwBPAEQARQApAHsAUwBhAHkAIABZAGUAbABsAG8AdwAgACcAWwBZAEUATABMAE8AVwBdACAAYCQgAJNiDU4wUiAARwBpAHQASAB1AGIAKACyfe+NKQC3ACAAZ3EsZ19q/nPBbNGNJwB9AAoAJABiAGsAPQBKAG8AaQBuAC0AUABhAHQAaAAgACgAWwBJAE8ALgBQAGEAdABoAF0AOgA6AEcAZQB0AFQAZQBtAHAAUABhAHQAaAAoACkAKQAgACIAdgBkAGYAMQBfAGIAawBfACQAKABHAGUAdAAtAEQAYQB0AGUAIAAtAGYAIAB5AHkAeQB5AE0ATQBkAGQAXwBIAEgAbQBtAHMAcwApACIACgBmAG8AcgBlAGEAYwBoACgAJABwACAAaQBuACAAQAAoAEcAIABsAHMALQBmAGkAbABlAHMAIAAtAG8AIAAtAC0AZQB4AGMAbAB1AGQAZQAtAHMAdABhAG4AZABhAHIAZAAgAC0ALQAgACIAJABEAC8AVgBEAEYAXwBNAEQATAAwADEAMwBfAEEAYwB0AGkAdgBhAHQAZQBWAEQARgBfAHYAKgAuAHAAeQAiACkAKQB7AEcAIABjAGEAdAAtAGYAaQBsAGUAIAAtAGUAIAAiAG8AcgBpAGcAaQBuAC8AbQBhAGkAbgA6ACQAcAAiADsAaQBmACgAIQAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACkAewAkAG4AdQBsAGwAPQBOAGUAdwAtAEkAdABlAG0AIAAtAEkAdABlAG0AVAB5AHAAZQAgAEQAaQByAGUAYwB0AG8AcgB5ACAALQBGAG8AcgBjAGUAIAAtAFAAYQB0AGgAIAAkAGIAawA7AE0AbwB2AGUALQBJAHQAZQBtACAALQBMAGkAdABlAHIAYQBsAFAAYQB0AGgAIAAiACQAUgAvACQAcAAiACAAJABiAGsAIAAtAEYAbwByAGMAZQA7AFMAYQB5ACAAQwB5AGEAbgAgACIAWwAIil0AIABgJCAALGdfaipn/Y9kjoR2IAAkACgAUwBwAGwAaQB0AC0AUABhAHQAaAAgACQAcAAgAC0ATABlAGEAZgApACAAbQBhAGkAbgAgAPJdCWcgAJIhIAD7eTBSIAAkAGIAawAoAA1Oy2TrX0mPKQAiAH0AfQAKAEcAIABtAGUAcgBnAGUAIAAtAHEAIAAtAC0AZgBmAC0AbwBuAGwAeQAgAG8AcgBpAGcAaQBuAC8AbQBhAGkAbgB8AE8AdQB0AC0ATgB1AGwAbAAKAGkAZgAoACEAJABMAEEAUwBUAEUAWABJAFQAQwBPAEQARQApAHsAUwBhAHkAIABHAHIAZQBlAG4AIAAiAFsARwBSAEUARQBOAF0AIABgJCAAdgBpAGEALQBtAGEAaQBuACAAPQAgAG0AYQBpAG4AIAAAZ7BlIAAkACgARwAgAHIAZQB2AC0AcABhAHIAcwBlACAALQAtAHMAaABvAHIAdAAgAEgARQBBAEQAKQAiAH0AZQBsAHMAZQB7AFMAYQB5ACAAWQBlAGwAbABvAHcAIAAnAFsAWQBFAEwATABPAFcAXQAgAGAkIAANTv2A619JjzBSIABtAGEAaQBuACgALGdfaglnJVKEdtBjpE4gAC8AIAA5ZdVSKQC3ACAAZ3H+c8Fs0Y0nAH0ACgBpAGYAKAAtAG4AbwB0ACgAVABlAHMAdAAtAFAAYQB0AGgAIAAtAEwAaQB0AGUAcgBhAGwAUABhAHQAaAAgACIAJABSAC8AJABGADcAIgApACkAewBHACAAcgBlAHMAdABvAHIAZQAgAC0ALQBzAG8AdQByAGMAZQA9AG8AcgBpAGcAaQBuAC8AbQBhAGkAbgAgAC0ALQB3AG8AcgBrAHQAcgBlAGUAIAAtAC0AIAAkAEYANwB8AE8AdQB0AC0ATgB1AGwAbAB9AAoAaQBmACgAKABHACAAaABhAHMAaAAtAG8AYgBqAGUAYwB0ACAALQAtACAAJABGADcAKQAgAC0AbgBlACAAKABHACAAcgBlAHYALQBwAGEAcgBzAGUAIAAiAG8AcgBpAGcAaQBuAC8AbQBhAGkAbgA6ACQARgA3ACIAKQApAHsAUwBhAHkAIABSAGUAZAAgACcAWwBSAEUARABdACAAYSQgACxnX2ogAHYAMAAxADAANwAgAA1OL2YgAG0AYQBpAG4AIACEdkhyLGcgALcAIAANTtGNJwA7AHIAZQB0AHUAcgBuAH0ACgAkAG4APQAnACcACgBmAG8AcgBlAGEAYwBoACgAJAB2ACAAaQBuACAAJwAwADEAMAA4ACcALAAnADAAMQAwADkAJwAsACcAMAAxADEAMAAnACkAewAkAGYAPQAiACQARAAvAFYARABGAF8ATQBEAEwAMAAxADMAXwBBAGMAdABpAHYAYQB0AGUAVgBEAEYAXwB2ACQAdgAuAHAAeQAiADsARwAgAGMAYQB0AC0AZgBpAGwAZQAgAC0AZQAgACIAbwByAGkAZwBpAG4ALwBtAGEAaQBuADoAJABmACIAOwBpAGYAKAAkAEwAQQBTAFQARQBYAEkAVABDAE8ARABFACkAewBHACAAcgBlAHMAdABvAHIAZQAgAC0ALQBzAG8AdQByAGMAZQA9ACIAbwByAGkAZwBpAG4ALwAkAEIAcgAiACAALQAtAHcAbwByAGsAdAByAGUAZQAgAC0ALQAgACQAZgB8AE8AdQB0AC0ATgB1AGwAbAA7ACQAYgA9AEcAIABoAGEAcwBoAC0AbwBiAGoAZQBjAHQAIAAtAC0AIAAkAGYAOwBpAGYAKAAkAGIAIAAtAG4AZQAgACQASABbACQAdgBdACkAewBTAGEAeQAgAFIAZQBkACAAIgBbAFIARQBEAF0AIABhJCAAdgAkAHYAIAD/Yg1OMFIWYmdRuVsNTg1cKABnAGkAdAAgAGIAbABvAGIAIAAkAGIAKQC3ACAADU7RjSIAOwByAGUAdAB1AHIAbgB9ADsAJABuACsAPQAiACAAdgAkAHYAKAAkACgAJABiAC4AUwB1AGIAcwB0AHIAaQBuAGcAKAAwACwANwApACkAKQAiAH0AZQBsAHMAZQB7ACQAbgArAD0AIgAgAHYAJAB2ACgAbQBhAGkAbgAgAPJdNmUpACIAfQB9AAoAUwBhAHkAIABHAHIAZQBlAG4AIAAiAFsARwBSAEUARQBOAF0AIABhJCAAQQBjAHQAaQB2AGEAdABlAFYARABGACQAbgAgADFcTU8gALcAIACKdShXIABtAGEAaQBuACAAhHYgAHYAMAAxADAANwAiAAoAdAByAHkAewAkAG8APQBHAGUAdAAtAEMAaQBtAEkAbgBzAHQAYQBuAGMAZQAgAFcAaQBuADMAMgBfAE8AcABlAHIAYQB0AGkAbgBnAFMAeQBzAHQAZQBtADsAJABmAHIAPQBbAGkAbgB0AF0AKAAkAG8ALgBGAHIAZQBlAFAAaAB5AHMAaQBjAGEAbABNAGUAbQBvAHIAeQAvADEASwBCACkAOwBTAGEAeQAgAEMAeQBhAG4AIAAiAFsACIpdACAAYiQgAO9TKHUYirZh1JogACQAZgByACAALwAgACQAKABbAGkAbgB0AF0AKAAkAG8ALgBUAG8AdABhAGwAVgBpAHMAaQBiAGwAZQBNAGUAbQBvAHIAeQBTAGkAegBlAC8AMQBLAEIAKQApACAATQBCACQAKABpAGYAKAAkAGYAcgAgAC0AbAB0ACAANAAwADkANgApAHsAJwAgALcAIACibutbIWoPXyAAkiEgABiKtmHUmpiVDU5JeygAdgAwADEAMAA4ACkAJwB9ACkAIgB9AGMAYQB0AGMAaAB7AH0ACgAkAGUAbgB2ADoAVgBJAEEAXwBOAEUAVABfAEMATwBOAFMARQBOAFQAPQAnAFkARQBTACcAOwAkAGUAbgB2ADoAVgBJAEEAXwBTAEMAUgBBAFAARQBfAEMATwBOAFMARQBOAFQAPQAnAFkARQBTACcACgBTAGEAeQAgAEMAeQBhAG4AIAAnAFsACIpdACAAYyQgAAxUD2GYlYuVKADNZFxP4VS8jBmQAE5MiCAAPQAgAKqJS2KLlSAAtwAgAOpTKFcZkAtQIABQAG8AdwBlAHIAUwBoAGUAbABsACAATIgLeikAJwAKACQAVgA9ACIAJABSAC8AJABEACIAOwAkAGkAbgB2AD0ARwBlAHQALQBDAGgAaQBsAGQASQB0AGUAbQAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAJABWACAALQBGAGkAbAB0AGUAcgAgACcASQBuAHYAbwBrAGUALQBWAEQARgAtAEEAYwB0AGkAdgBhAHQAZQAtAHYAKgAuAHAAcwAxACcAfABTAG8AcgB0AC0ATwBiAGoAZQBjAHQAIABOAGEAbQBlAHwAUwBlAGwAZQBjAHQALQBPAGIAagBlAGMAdAAgAC0ATABhAHMAdAAgADEACgBpAGYAKAAhACQAaQBuAHYAKQB7AFMAYQB5ACAAUgBlAGQAIAAnAFsAUgBFAEQAXQAgAGQkIAB+Yg1OMFIgAEkAbgB2AG8AawBlAC0AVgBEAEYALQBBAGMAdABpAHYAYQB0AGUAJwA7AHIAZQB0AHUAcgBuAH0ACgBTAGEAeQAgAEMAeQBhAG4AIAAiAFsACIpdACAAZCQgACQAKAAkAGkAbgB2AC4ATgBhAG0AZQApACAALQBGAGUAdABjAGgASABvAG0AZQAgADwAVgBEAEYAPgAgAC0AUgBlAGYAaQBsAGwAQQBwAHAAbAB5ACIACgBQAHUAcwBoAC0ATABvAGMAYQB0AGkAbwBuACAAJABSADsAdAByAHkAewAmACAAJABpAG4AdgAuAEYAdQBsAGwATgBhAG0AZQAgAC0ARgBlAHQAYwBoAEgAbwBtAGUAIAAkAFYAIAAtAFIAZQBmAGkAbABsAEEAcABwAGwAeQA7ACQAcgBjAD0AJABMAEEAUwBUAEUAWABJAFQAQwBPAEQARQB9AGYAaQBuAGEAbABsAHkAewBQAG8AcAAtAEwAbwBjAGEAdABpAG8AbgB9AAoAUwBhAHkAIABDAHkAYQBuACAAIgBbAAiKXQAgAFYARABGACAAUH1fZ7x4IAAkAHIAYwAoADAAIACgfSAAtwAgADIAIADDniAAtwAgADEAIAAFfSAAtwAgADEAMgA0ACAAPpBCZiAAtwAgADEAMwAwACAALU63ZSkAIgAKAA==
```

上面那一行解碼後的原文(UTF-16LE base64;換版時改 `$H` 與版號清單後重新編碼):

```powershell
try{[Console]::OutputEncoding=[Text.Encoding]::UTF8}catch{}
$Br='claude/optimistic-goodall-yhalc5';$D='VeritasIntelligenceAnalytics/functional modules/VDF';$F7="$D/VDF_MDL013_ActivateVDF_v0107.py"
$R=@($env:VDF_GIT,"$HOME/via-main",$PWD.Path,"$HOME/OneDrive/Documents/movies-dataset")|?{$_ -and(Test-Path -LiteralPath "$_/.git")-and(Test-Path -LiteralPath "$_/$D")}|select -First 1
if($R){$R=[IO.Path]::GetFullPath($R)}
$H=@{'0108'='022689247f66210d85391e3a150679a6aa98b4bc';'0109'='c3d6a62ba3c70373c01f566120ad3448e6e1e1cd';'0110'='92f5c39fdbe548232679edca611dcdac02fa3c9a'}
function Say($c,$m){Write-Host $m -ForegroundColor $c}
function G{git -C $R @args 2>$null}
Say Yellow "[VDF 一鍵] PowerShell $($PSVersionTable.PSVersion) · git 倉 $R"
if($PSVersionTable.PSVersion.Major -lt 7){Say Red '[RED] 要 PowerShell 7(pwsh)';return}
if(!$R){Say Red '[RED] 找不到 via-main(要有 .git 與 VDF 夾)· 先 set VDF_GIT=<倉路徑> 再貼';return}
foreach($w in 0,2,4,8){Start-Sleep $w;G fetch -q origin main $Br|Out-Null;if(!$LASTEXITCODE){break}}
if($LASTEXITCODE){Say Yellow '[YELLOW] ① 抓不到 GitHub(網路)· 照本機現況跑'}
$bk=Join-Path ([IO.Path]::GetTempPath()) "vdf1_bk_$(Get-Date -f yyyyMMdd_HHmmss)"
foreach($p in @(G ls-files -o --exclude-standard -- "$D/VDF_MDL013_ActivateVDF_v*.py")){G cat-file -e "origin/main:$p";if(!$LASTEXITCODE){$null=New-Item -ItemType Directory -Force -Path $bk;Move-Item -LiteralPath "$R/$p" $bk -Force;Say Cyan "[計] ① 本機未追蹤的 $(Split-Path $p -Leaf) main 已有 → 移到 $bk(不擋快轉)"}}
G merge -q --ff-only origin/main|Out-Null
if(!$LASTEXITCODE){Say Green "[GREEN] ① via-main = main 最新 $(G rev-parse --short HEAD)"}else{Say Yellow '[YELLOW] ① 不能快轉到 main(本機有別的提交 / 改動)· 照現況跑'}
if(-not(Test-Path -LiteralPath "$R/$F7")){G restore --source=origin/main --worktree -- $F7|Out-Null}
if((G hash-object -- $F7) -ne (G rev-parse "origin/main:$F7")){Say Red '[RED] ② 本機 v0107 不是 main 的版本 · 不跑';return}
$n=''
foreach($v in '0108','0109','0110'){$f="$D/VDF_MDL013_ActivateVDF_v$v.py";G cat-file -e "origin/main:$f";if($LASTEXITCODE){G restore --source="origin/$Br" --worktree -- $f|Out-Null;$b=G hash-object -- $f;if($b -ne $H[$v]){Say Red "[RED] ② v$v 拿不到或內容不對(git blob $b)· 不跑";return};$n+=" v$v($($b.Substring(0,7)))"}else{$n+=" v$v(main 已收)"}}
Say Green "[GREEN] ② ActivateVDF$n 就位 · 疊在 main 的 v0107"
try{$o=Get-CimInstance Win32_OperatingSystem;$fr=[int]($o.FreePhysicalMemory/1KB);Say Cyan "[計] ③ 可用記憶體 $fr / $([int]($o.TotalVisibleMemorySize/1KB)) MB$(if($fr -lt 4096){' · 溢寫模式 → 記憶體閘不等(v0108)'})"}catch{}
$env:VIA_NET_CONSENT='YES';$env:VIA_SCRAPE_CONSENT='YES'
Say Cyan '[計] ④ 同意閘開(操作員貼這一行 = 親手開 · 只在這個 PowerShell 行程)'
$V="$R/$D";$inv=Get-ChildItem -LiteralPath $V -Filter 'Invoke-VDF-Activate-v*.ps1'|Sort-Object Name|Select-Object -Last 1
if(!$inv){Say Red '[RED] ⑤ 找不到 Invoke-VDF-Activate';return}
Say Cyan "[計] ⑤ $($inv.Name) -FetchHome <VDF> -RefillApply"
Push-Location $R;try{& $inv.FullName -FetchHome $V -RefillApply;$rc=$LASTEXITCODE}finally{Pop-Location}
Say Cyan "[計] VDF 結束碼 $rc(0 綠 · 2 黃 · 1 紅 · 124 逾時 · 130 中斷)"
```


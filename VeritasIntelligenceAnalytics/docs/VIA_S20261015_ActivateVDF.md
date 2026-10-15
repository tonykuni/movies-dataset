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

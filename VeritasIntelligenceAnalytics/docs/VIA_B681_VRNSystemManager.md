# 批681 · VRN 子系統管理對接口 —— VIA 往下讀 VRN,從此只走一扇門

操作員令:「他已經進入收尾階段 設立一個 VRN_SystemManager.py 上下銜接 VIA 也管理子系統的政策邏輯因子參數
以後讀取就從 VIA 往下透過 VRN_System 作為管理對接口 自適應 智慧化上下資訊自動更新的連結」。

(令裡的「普系統」我讀成「子系統」= VRN;若是指全系統,對接口的域表可以再擴,先講明不猜。)
本批同時交出接手掃描 `docs/VIA_VRN_Panorama_20260921.md`;批號自 681 起算——680 留給前一個 session 那五個 stage 未 commit 的檔(Z57)。

## 一 · 先量(LL329 拿到規格先去量既有實作)

| 量到 | 結果 |
|---|---|
| 樹上叫「管理器」的 | `VIA_SYSTEM_MANAGER v0146`(總管理器:任務正式名稱 + 總控頁)· `CGC_MDL069_SystemManager v0110`(三輪協議)· `CGC_MDL081_SubsystemManagerV2 v0101` · `SUP_MDL506_MotherSystemManager` · 收容件 `new modules engines/VIA_SubsystemManager_v001` |
| 沒有的 | **VRN 這一層的門**:VCGC v0117 的 `logic()` / `factors()` 各自 import ENG082 / SUP_MDL748;參數冊由 via_params_central 掃 68 本;VRN 四庫沒有一個統一的讀口,也沒有人替 VRN 報「上行七處掛了幾處」 |
| 版號(LL334) | 掃 30 條活分支:`VRN_SystemManager` / Grid `v0433` / VCGC `v0118` 都是空號;PR #53(busy-bell)佔著 Register v0241 / Manager v0147 / Deck v0158——本批不碰那三支 |

## 二 · 造了什麼(全部真跑)

| 件 | 檔(版號) | 自測 | 證據 |
|---|---|---|---|
| VRN 子系統管理對接口 | `functional modules/VRN/VRN_SystemManager_v0100.py` | 廿二檢 **22/22** | 中央冊 `VIA-SYS-0011` |
| VCGC 經口讀 VRN | `supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0118.py` | 廿四檢 **24/24** | ⑬ 由 5909/5908 → **5955/5955**;㉔ 在位署名 / 缺席 ABSENT×3 |
| 格子兩站 | `CGC_MDL064_SelftestGrid_v0433.py`(285 → 287 站) | `--only "VRN 子系統管理"` **OK 2** | 第二站 nodata_ok(rc2 = 過期≠壞) |
| 規格項 | `VIA_InputConsole_Spec_v0100.json` +group `management` / item `vrn_system`(63 → 64 項) | round-trip 位元相同後才改(LL333) | 30 行純增 |
| 中央元件冊 | `registry-sync --apply`:活 5955 · 新 47 · 變更 99 · 退役 1 | — | 退役的那一筆 `VIA-ENV-0001 (未路由:加速器通用件)` 就是 ⑬ 差 1 的來源 |
| 台帳 / 掉球 / 總控頁 | 台帳 1275 筆 · 掉球 +Z57–Z68 · 總控頁再生 2 行 | 契約測試 **19/19**(py3.11;CI 用 3.12) | — |

## 三 · 契約:這扇門長什麼樣

```
VIA ─(L20 唯一對接口 VCGC)─► VRN_SystemManager ─► policy · logic · factor · param · engine · handover
```

| 動詞 | 做什麼 | 寫檔? |
|---|---|---|
| `status` | 六域一行一燈 + 連結計數 + 七處自審 | 否 |
| `catalog` | 每一域 正本在哪 · 怎麼讀 · 上游誰在吃 | 否 |
| `links` | 全部連結攤平(現解尾版 · 現算 sha · 現量年齡) | 否 |
| `read <域> [key] [--full]` | 統一讀口;每個回傳署名 `via: VRN_SystemManager v0100` | 否 |
| `sync [--apply]` | 對上一次快照判 NEW / CHANGED / GONE / SAME;`--apply` 才落 json/md/html + LEDGER.tsv | 只落 `VIA_Reports/vrn_system/` |
| `--selftest` | 廿二檢;`VIA_SELFTEST=1` + 快照夾指向暫存(L17) | 只寫暫存 |

| 域 | 正本(不複製,只指) | 燈怎麼判 |
|---|---|---|
| policy | 律冊 VRN 子集(律 8 · lessons 35)· ENG082 政策因子 1766 | 冊在=GREEN |
| logic | 索引冊 v0104(六層 · 指標 50)+ 守門**委派** `via_vrn_logic_book.do_check` + ENG082 LOGIC_latest | 守門紅=RED;件 0=latest NODATA |
| factor | `SUP_MDL748.policy_rows`(130 列) | 列 >0=GREEN |
| param | `via_params_central.BOOKS` VRN 子集 34 本 + 樞紐自報常數 4 本(SUP_MDL749.SSOT / MDL176.UNION_OUT / MDL115.OUTJ / 疊加層 / 正典)= 38 本 | 缺一本=ABSENT |
| engine | 六層鏈快照(不重跑)· 尾版家族 58(**同 VCGC._tail_files 一把尺**)· 規格 15 / 格子 69 / 短令 25 / Deck 9 / 元件冊 1404 | 燈**照抄鏈跑器**,RED 再拆:缺件 / 缺料 / 其餘 |
| handover | ENG082 三處 hash(委派)· 逐批 · 掉球 · 一頁批號 vs 律冊批號 | 一頁比律冊舊=STALE(不是 RED) |

rc:0 GREEN · 1 RED(冊缺 / 守門紅 / 讀器炸)· 2 STALE 或 NODATA。**引擎面的燈不折進 rc**——尺只講它量過的事(LL324)。

## 四 · 「自適應 · 自動更新的連結」是怎麼做的

- **不是一本冊。** 冊會過期(批666 一盞綠燈配一本舊冊)。每一條連結都在呼叫當下 glob 尾版、算 sha、量 mtime;引擎開新版號,下一次 `sync` 就是 CHANGED。
- **差異有負控。** 自測⑮ 改一條 sha → CHANGED 1;快照裡塞一條鬼連結 → GONE 1。會過的檢等於沒有檢(LL89)。
- **上行是雙向的。** VCGC v0118 的 `logic()` / `factors()` 一律 `VRN_SystemManager.read()`,對接口缺席就 ABSENT——**不退回舊路**(退回舊路=同一判準寫兩處,L05);
  對接口反過來自審七處(規格 / 格子 / 短令 / Deck / Manager / 元件冊 / 交接),掛幾處就報幾處,本批 **4/7**,不假綠。
- **同一把尺。** 尾版家族用 VCGC 的 `_tail_files()`、四面用 VCGC 的讀器、守門用索引冊自己的 `do_check()`、參數清單用 via_params_central 的 `BOOKS`——抄到函式才算出處(LL316)。

## 五 · 容器實測(這是容器,不是你的機器)

```
政策 GREEN  律 99 · lessons 305 · VRN 律 8 / lessons 35 · 批 批662 · 尾 L101/LL305 · 政策因子 1766
邏輯 GREEN  索引 v0104 層 6 指標 44 · 守門 GREEN 指標 50 · 尾版 50 · 過期 0 · 邏輯庫 ENG082 v0110 件 0(容器)
因子 GREEN  130 列 {allinone 77 · financial_data_standardization 53}
參數 GREEN  冊 38 · 缺 []
引擎 RED    鏈 RED {RED 16 · GATED 1 · NODATA 13 · GREEN 16} · RED 拆 {ABSENT 11 · NODATA 1 · RED 4}(缺件≠壞掉;燈照抄鏈跑器)
交接 STALE  一頁 批554 vs 律冊 批662 · 逐批 B664 · B 文 679 · 掉球 68 列/未結 64(追加前)
上行 七處 3/7(規格 ✅ 格子 ✅ 元件冊 ✅;短令/Deck/Manager ❌=L70;交接 ❌→本文寫入後 ✅)
[計] 連結 105 · GREEN 102 · RED 1 · STALE 2 · 本口 rc 2 STALE/NODATA
```

VCGC v0118 status 多的那一行(容器):`VRN 系統管理 STALE/NODATA:燈 {…} · 連結 105 · 七處 3/7 · VRN_SystemManager_v0100(via VRN_SystemManager v0100)`。
rc 2 的兩個來源都是真的:一頁交接停在 批554(Z58),邏輯庫件 0(容器缺料)。

### 全格子(LL117:推之前先跑;容器 FAST;套件缺件先補齊再跑,免得整張格子都是缺件紅)

| 跑 | 條件 | 結果 |
|---|---|---|
| 基線 main(Grid v0432,乾淨樹;stash 本批後跑) | 同容器 · 套件補齊 | OK 249 · FAIL 22 · SKIP 8 · TIMEOUT 0(279 站;GRID_20260921_075217) |
| **本批(Grid v0433)** | 同容器 · 套件補齊 | **OK 252 · FAIL 21 · SKIP 8 · TIMEOUT 0**(281 站;GRID_20260921_074714) |
| 本批第一跑(參考) | duckdb / fitz / pandas / pyarrow / pydantic 未裝 | OK 245 · FAIL 26 · SKIP 10(GRID_20260921_074101) |

差集(站名逐一比對):**只在本批紅的站 0**;只在基線紅的站 1 = 「Veritas 中央控管台二十二檢」(⑬ 5909/5908,本批 registry-sync 修掉)。
其餘 21 紅兩邊一模一樣:容器缺料(`tw_daily_prices` / `tw_prices_adj` / `features_daily` / `tw_listings` 表不在、台股 0 列、66 份真 sidecar 不在)、
缺件(matplotlib / pkuseg / pwsh)、六層鏈實跑 rc1(容器)——不是本批造成,也不是本批能修的;每一盞在 GRID json 裡都帶因由。

## 六 · 我這一批犯的錯(四個,四個都被自己的檢擋下來)

1. **相鄰字串沒接起來。** 給 VCGC 打 patch 時,新段落用多行字串「排」在一起卻沒放進括號,Python 只認第一行 → `onepage_md` 的 `return` 被吃掉 → 自測 `TypeError: data must be str, not NoneType`。**patch 完要跑正主的自測,`ast.parse` 過了不算。**
2. **同名鍵互相覆蓋。** `collect()` 的 meta 鍵 `engine`(引擎檔名)與引擎域 `engine`(整個 dict)同名,VCGC 印出一整坨 dict。改名 `me`。
3. **去重去掉了出處。** 檢⑦ 第一版把「同一本冊兩個出處(名冊 + 樞紐常數)」去重成一個,樞紐那條出處就不見了,檢當場紅。改成 `also_src` 兩個都留——只增不減連出處也算。
4. **錨點不唯一。** Grid v0433 第一次拿 `r"""` 當錨,檔內有兩處,守衛擋下;改成只換第一處。

## 七 · 沒做的,以及為什麼(L87 豁免必附理由)

| 沒做 | 為什麼 | 掉球代號 |
|---|---|---|
| Register 短令 `via-vrnsys`、根與 `bin\` 梭、Deck 任務、Manager 正式名稱 | L70 未經逐次許可不改 `.ps1`;且 v0241 / v0147 / v0158 已被 PR #53 佔號 | Z65 |
| 改鏈跑器 MDL172 把 import 缺件判 ABSENT | 那是鏈跑器自己的一批;本口先把 16 紅拆開講 | Z60 |
| `via-vcgc page --publish`(一頁交接三處) | 容器缺料段會把 ABSENT 寫進倉根;工作站跑更準 | Z58 |
| LL306–LL335 收回律冊 | 要逐條對 docs/commit,單獨一批 | Z59 |

## 八 · 你的手

1. 前一個 session 的 批680 五檔:回去按 go,或裁「棄」(Z57)。
2. 一句「准改 Register」→ 短令 + 梭 + Deck + Manager 四面一起補(Z65)。
3. 開閘補上市所 ADJ 價(Z62);PR #53 裁併/關(Z64)。
4. 工作站跑一次 `via-vcgc page --publish`(Z58)。

## 九 · 一貼即用(前兩行固定;本批在側枝 `claude/awesome-bardeen-h0wm5v`,`git switch -` 可以回原枝)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git fetch origin claude/awesome-bardeen-h0wm5v
git switch claude/awesome-bardeen-h0wm5v
$m = (Get-ChildItem ".\functional modules\VRN\VRN_SystemManager_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
python $m --selftest
python $m status
python $m sync --apply
via-vcgc status
via-vcgc --selftest
```

貼回:`python $m status` 全段、`via-vcgc status` 的「VRN 系統管理」那一行、`via-vcgc --selftest` 最後兩行。
你的機器有庫有境,邏輯庫「件 0」與引擎面「RED 16」應該會變——變成什麼,貼回來我才知道。

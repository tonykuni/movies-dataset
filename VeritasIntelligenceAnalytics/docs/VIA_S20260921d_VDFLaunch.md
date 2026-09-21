# VIA 交接紀錄 · 側線 2026-09-21 d(branch `claude/busy-bell-97sa4f`;主線批號由併線的手指定 L25)

操作員令:「**GO 我需要擷取 VDF 的資料,幫我完善到可啟動她**」

〇 接手提示詞 → docs/VIA_AI_Handover_Prompt_v*.md(尾版)。本批接手驗收在六、貼行在七。前一批(c)在 `VIA_S20260921c_VDFFixCycle.md`,再前一批(b)在 `VIA_S20260921b_VDFSystemManager.md`。

## 一 · 律(本批沒有新律;用到的逐條註明)

- L61 / LL331 先量再造:啟動面先量出「正主是誰、差什麼」,再決定造什麼(二)。
- L04 尾版律:VDF_SystemManager v0103 · Grid v0441 · 單元測試 v0102 都是新版檔,舊版留版史;`via_boot_update.ps1` 是無版號的開機腳本,主線一向就地改,本批就地改(三之一)。
- L05 / L30 零 Hydra:家族境 python 的尺是 CGC_MDL136 `envpy` 正本(Register 的 `Get-VIAEnvPython` 自己就寫著「規則正本+自測=CGC_MDL136」);必要庫表與探針是 CGC_MDL137 的 `FAMILY_LIBS` / `probe_libs`;燈是 L16 五態表,與 CGC_MDL170 同一張;開機鏈兩份腳本用同一把尺 `_STEP_RX` 量。本批**沒有**再抄一份別名表、必要庫表或燈表。
- L07 / L08 同意閘只讀、永不代設;L19 能跑閘 GREEN 24h 內才算 INSTALL_OK;L16 誠實態(ABSENT 缺件 ≠ GATED 等閘 ≠ NODATA 沒跑過 ≠ RED 壞);L17 自測零污染;L57 SKIP 不進分母。
- L70 `.ps1` 逐次許可:本批把「GO … 完善到可啟動」讀成對 `via_boot_update.ps1` 這一次的許可(三之一);讀錯就一行還原,那一行也寫在三之一。
- L93:`.ps1` 在庫是 LF,照舊(不轉 CRLF)。
- LL49 再生冊:中央元件冊由 `registry-sync --apply` 重建、總控頁由 Manager 再生,其餘容器再生物不入 commit。LL89 會過的檢等於沒有檢:㉘ 帶合成負控(少一步必 RED)。

## 二 · 先量:VDF 擷取要怎麼「啟動」(容器,零網路,同意閘未開)

| 啟動面 | 正主(量到的) | 現況 |
|---|---|---|
| 一鍵抓史深 | `via-vdffetch [年]`(Register v0242)→ 尾版 `Invoke-VIA-VdfFetch-v0104.ps1`(批383):① 自找 VIA 根 → ①b 倉庫自癒(`-NoHeal` 關)→ ② 點源短令冊(`-NoEnter` 關)→ ③ 同意閘不覆蓋(`Set-VIAGateDefaults`:**未設補 OFF = fail-closed**,已設者尊重)→ ④ 家族境 python(`Get-VIAEnvPython vdf`)→ ⑤ 年份旗標 `VIA_HIST_SINCE=<年>-01-01` / `VIA_REV_SINCE=<年>-01`(`-Limit N` 先小量;`-Dry` 只印)→ ⑥ 20 加速器 + MDL134 `plan` Hydra 哨兵 H1–H6(H3 進程雙頭 / H5 尾版律 FAIL = 誠實停)→ ⑦ CGC_MDL134 `run --only datahome,hist_2023,global,fred,revenue_backfill,etf_universe,etf_fetch,etf_history,consensus,revenue_consensus,etf_revenue` 十道並行 → `digest` + MDL131 `digest`;梭 `via-vdffetch.cmd` | 在位;啟動要用的 16 短令 16/16 在冊 |
| 每日增量 | `via_boot_update.sh`(正主;倉根 SessionStart hook;腳本自帶 `VIA_NET_CONSENT=YES`,批123/137/150 常令)/ `via_boot_update.ps1`(工作站:`VIA.ps1` 全自動 · `launch.ps1` · Deck「boot」→ `Start-Process powershell -File`) | **`.ps1` 比 `.sh` 少 13 步、且用裸 `python` 起引擎**——Z98 只照出 ④a/④b 兩步;整份量下來還少 ⑩ ENG076 與 ⑪–⑳ 十一步(MDL131 · MDL133 · MDL135 · MDL136 · ENG079 · MDL137 · ENG081 · MDL139 · MDL140 · MDL141)。裸 python 在沒 duckdb/pandas 的 base 會把**每一步**跑成 ModuleNotFoundError |
| 家族境 | CGC_MDL137 `python_for("vdf")` → CGC_MDL136 → `via_vdf_312`;必要 duckdb / pandas / numpy / pyarrow | 容器 BASE_FALLBACK,缺 duckdb · pandas · pyarrow → ABSENT(工作站家族境是操作員的手;AI 不裝套件) |
| 閘 | `VIA_NET_CONSENT`(http 道)· `VIA_SCRAPE_CONSENT`(爬蟲道要期望 token,`via-gates` 印)· `FRED_API_KEY`(via-fred) | 三個都未設 → 閘態 GATED;鑰缺 → 那一步 SKIP 印指令 |
| 網路工具 | `supportive modules/network/via_net_unified_v0101.py`(統包唯一)→ 後端 VeritasAegisNexus 正典 | 在;`net_ok` 在容器 None(requests 不在 base) |
| 上次實跑存證 | boot marker `.last_boot_update` · `VIA_Reports/boot_update_logs/BOOT_*.log` · `rungate/RUNGATE_latest.json` · `vdf_chain/VDFCHAIN_latest.json` · `lanes/LANES_*.json` | marker 2026-09-21 · BOOT_20260921_023505.log · 能跑閘 RED(base 退路;vdf RED)· 獨立鏈 GATED(GREEN 6 · ABSENT 3 · GATED 1)· 十道無存證(via-vdffetch 從沒跑過) |
| 落點 | `functional modules/VDF/output_hub/mega/`(.gitignore 批128 不入版控) | 夾在;庫/parquet 0 件 = 沒抓過,不是壞 |
| 名字像啟動器的 | VDF 根 `Invoke-VDF.ps1` / `Invoke-VDF-Fetch.ps1` = `VIA-VDF-Path-Contract.ps1`(VIA_DATA_ROOT `dict\VDF\_ssot/_active`)的**唯讀狀態殼**;`Start-VIA-VDF-v0104.ps1` = 加速器/網路橋注入 + v0160C 工作台 | 都不是擷取啟動器,別按 |

所以「可啟動」差的三件,兩件是操作員的手(家族境 · 閘),一件是樹上的檔(`.ps1` 不同鏈)。AI 能做的是:把樹上那件修掉,把另外兩件**每跑一次量一次、把下一行印出來**——這就是 v0103 的 `launch`。

## 三 · 做了什麼

### 三之一 · `via_boot_update.ps1` 補齊到與 `.sh` 同鏈 ⓪–⑳(L70:這一次的許可讀自「GO … 完善到可啟動」)

- +④a `VDF_ENG077_ActiveETFUniverse` run · +④b `VDF_ENG078_ActiveETFHoldingsHistory` daily · +⑩c2 `VDF_ENG076_ETFRevenueMomentum` run · +⑪–⑳(MDL131 build · MDL133 build · MDL135 run --offline --quiet · MDL136 status --quiet · ENG079 scan · MDL137 run --fast --quiet · ENG081 check · MDL139 build · MDL140 build · MDL141 all;段前 `$env:VIA_NO_OPEN="1"`,與 `.sh` 每步前置 `VIA_NO_OPEN=1` 同義)。節序照 `.sh` 第 83/85/111/117–136 行。
- ⓪ 家族境 python:`& python <CGC_MDL136 尾版> envpy vdf --json` → `$PY`(尺=正本,不抄別名表);`Step` 改 `& $PY $script`;境未見 = base 退路且**寫進 log 第二行**(`--- ⓪ 家族境 python(尺=CGC_MDL136 envpy):<python> · <state>`)。
- 不裝套件(`.sh` ⓪ 的 pip 自補是容器非持久境的事)、不改同意閘行為、LF 照舊、無 BOM 照舊。
- **還原(讀錯許可時一行)**:`git checkout -- "VeritasIntelligenceAnalytics/supportive modules/registry/via_boot_update.ps1"`(併線後:`git show <本批前一個 commit>:"VeritasIntelligenceAnalytics/supportive modules/registry/via_boot_update.ps1" > …`)。
- 容器沒有 pwsh:格子「PowerShell 語法與參數名閘」站 SKIP(ABSENT 不假綠),本批 `.ps1` 改動只有人眼複讀過,工作站要跑一次 `via-selftest --only "PowerShell 語法"`(Z105)。

### 三之二 · VDF_SystemManager v0103:`launch`(啟動就緒;只量不動手)

- 八項現量:① 家族境 python + 必要庫(`--no-probe` 讀上次能跑閘快照,零子行程;不帶則用家族境 python 現探一個子行程)② 同意閘現態 + FRED 鑰在不在(只讀)③ 網路工具掛載 ④ 啟動器/短令/鏈在位(Invoke-VIA-VdfFetch 尾版 · via-vdffetch.cmd · Register 尾版 16 短令 · MDL134 · MDL170 · MDL136)⑤ 開機鏈雙載體同鏈 ⑥ 上次實跑存證 ⑦ 落點 ⑧ 下一步卡。
- 燈與 rc(L16 五態碼,與 CGC_MDL170 同一張):RED 1(啟動器/鏈缺 · 雙載體不同鏈)> ABSENT 3(必要庫不在家族境)> GATED 4(閘未開)> GREEN 0(可啟動);從沒跑過只是紀錄,不擋啟動。下一步卡第一行對得上燈:GATED/ABSENT 是「[你的手]」那一行、RED 是「[修]」、GREEN 直接 `via-vdffetch`。
- `status` / `page` 也帶「一之三 · 啟動就緒」(零子行程版);連結表 109 → 113(`launch:boot_sh` · `launch:boot_ps1` · `launch:fetch` · `launch:lanes`),`sync` 從此看得見鏈被改;`read launch [probe]` 同讀;`catalog` +一列。本口 rc 不變(RC_SCOPE 不含 launch;格子的 status 站照舊 nodata_ok)。
- 自測 27 → 29:㉘ 開機鏈雙載體同鏈(合成負控:`.ps1` 少一步 → RED 點名、整行註解裡的鬼引擎不算步;補上 → GREEN;裸 python → STALE;真鏈現量 GREEN 42/42)· ㉙ 啟動就緒只量不動手(燈 ∈ 冊 · rc 表 · 尺是 MDL137→MDL136 · 閘前後同 · 下一步卡對得上燈 · status 帶同一段)。

### 三之三 · 七處與冊

- 規格 `vdf_system`:outputs 頁名 v0103、zh 註 launch(verb 仍 status 唯讀)。
- 格子 v0441:站名「廿七檢」→「廿九檢」;+站「VDF 啟動就緒」(`launch --no-probe`;gated_ok:rc4 閘未開 GATED 不是紅、rc3 家族境缺件由境缺分類器收 SKIP、rc1 才是壞);站 289 → 290。
- Deck / Manager / Register:同家族不加項(launch 是 via-vdfsys 的動詞,`via-vdfsys launch` 走 v0242 既有短令);中央冊 `registry-sync --apply` 6117(新 8 = launch 段八個函式);台帳 +1;總控頁再生(LL49 例外件);交接 = 本文。
- 單元測試 v0102:+T07 啟動就緒六測;T05 格子站 2 → 3 改**集合等式**(v0101 釘死「兩站」,第三站一上就紅——把暫態釘成不變量,同 ⑱ 那一課;v0101 留版史,單跑會在 T05 紅,Z104)。

## 四 · 容器實測總表

| 檢 | 結果 |
|---|---|
| `VDF_SystemManager_v0103.py --selftest` | 29 檢 OK 29 · FAIL 0(零污染) |
| `… launch`(現探) | ABSENT rc 3:BASE_FALLBACK · 必要庫 1/4 缺 duckdb, pandas, pyarrow · 閘 UNSET · 雙載體 GREEN 42/42 · 啟動器 16/16 · 下一步第一行「[你的手] 建境」 |
| `… launch --no-probe` | 同上,必要庫讀 RUNGATE_latest(2026-09-21T02:45:16) |
| `… status` | rc 2(工具 STALE · 邏輯 STALE,同 c 批)· 連結 113 · 啟動 ABSENT 一行在 |
| `test_vdf_system_manager_v0102.py` | Ran 26 · OK |
| `test_vdf_honest_states_v0100.py` | Ran 10 · OK |
| VCGC v0120 `--selftest` | 二十六檢 OK 26(registry-sync 前 ⑬ 6109/6117 紅,重建後綠) |
| `test_master_control_contract_v0102.py` | Ran 19 · OK(Manager 再生總控頁後) |
| CGC_MDL164 v0108 | 23/23(v0103 的 launch 段沒有新的自我指涉判定器) |
| CGC_MDL174 v0101 | GATED(同 c 批;VDF ⑥ 不在卡點) |
| Grid v0441 `--only "VDF 子系統管理,VDF 啟動就緒,VDF 獨立鏈,PowerShell 語法"` | 廿九檢 OK · 實跑 OK · 啟動就緒 SKIP(rc3 境缺=分類器)· 獨立鏈 十九檢 OK · 實跑 OK · PowerShell 語法 SKIP(pwsh 缺) |

工作站(有 via_vdf_312)預期:`via-vdfsys launch` → GATED rc 4(閘未開)→ 你設閘 → GREEN rc 0;格子「VDF 啟動就緒」站 GATED/GREEN 都收。

## 四之二 · 併線(推之後主線又動了:PR #63 awesome-bardeen 批689B,9 commits)

- 七檔衝突,按 L25 解:`VRN_SystemManager_v0102.py` 與 `CGC_MDL064_SelftestGrid_v0439.py` 撞名 → 取主線;三本再生冊(中央元件冊 · VRN 索引冊 · 總控頁)取主線後各以 builder 重建(registry-sync 6118 · via-vrnbook build 守門 GREEN · Manager 再生);掉球冊與台帳聯集(台帳 1294 + 本線 4 = 1298;主線把 批687/688 兩條改名 687B/688B 的舊拼法不重收)。
- 撞名的兩處把本線的差再貼到更高版號:**VRN_SystemManager v0104** = 主線 v0103 + 側線 b 的 ⑱ 改量不釘(主線 v0103 仍寫「Register 未登必須 False」,v0242 已登 via-vrnsys → 併後必紅;v0104 27/27);**Grid v0442** = v0441 + 主線 v0439 的八處站名/期望改動(ENG086 二十二檢 · SUP_MDL749 四十九檢×2 · ENG068/首頁引擎 nodata_ok · VRN 對接口廿七檢);站數 290 不變。
- 掉球號第五次重取:主線批689B 取了 Z88–Z92,本線 b/c/d 三段全部 +4(五)。
- 併後複測:VDF 對接口 29/29 · VRN 對接口 v0104 27/27 · VCGC 26/26 · 單元測試 26 + 10 OK · 契約 19/19 · MDL164 23/23 · Grid v0442 十站 OK 9 · SKIP 1(啟動就緒 rc3 境缺)。

## 五 · 掛著(接續 Z102 → Z103–Z105;Z98 本批結;併 main 批689B(PR #63)後本線掉球全部 +4:原 Z94 = 現 Z98、原 Z99–Z101 = 現 Z103–Z105;程式註解與自測 ㉘ 標籤裡寫的「Z94」指的是現在的 Z98)

- Z98 已結:`.ps1` 補 13 步 + 家族境 python;同鏈由 launch ㉘ 每跑守。
- Z103 工作站實跑 `via-vdfsys launch` 並回貼:ABSENT 就先建境(`via-envgov apply --approve` ENSURE_ENV via_vdf_312;AI 不裝)、GATED 就設閘,然後 `via-vdffetch 2023 --dry` → `via-vdffetch 2023`;抓完 `via-vdfsys`(引擎域拿到十道/獨立鏈快照)。
- Z104 `test_vdf_system_manager_v0101.py` T05 釘死格子「兩站」,第三站上了就紅;v0102 已改集合等式,v0101 留版史候裁(刪或留)。
- Z105 容器無 pwsh,`via_boot_update.ps1` 本批改動只人眼複讀:工作站跑一次 `via-selftest --only "PowerShell 語法"`;紅了就一行還原(三之一)。

## 六 · 接手驗收(一行一答)

1. `python "functional modules/VDF/VDF_SystemManager_v0103.py" --selftest` → 29 檢 FAIL 0。
2. `via-vdfsys launch` → 印八項 + 下一步卡;rc 0/4/3/1 對得上第一行的燈。
3. `python "supportive modules/registry/tests/test_vdf_system_manager_v0102.py"` → Ran 26 · OK。
4. `via-selftest --only "VDF 子系統管理,VDF 啟動就緒"` → 廿九檢 OK · 實跑 OK · 啟動就緒 GATED/GREEN(容器 SKIP)。
5. `type "supportive modules\registry\via_boot_update.ps1" | Select-String "④a|④b|⑩c2|⑪|⑳|envpy"` → 六行都在。

## 七 · 一貼即用(工作站;閘那一行是你的手)

```powershell
via-fresh                        # 或重點源 Register v0242(短令 via-vdfsys / via-vdffetch 都在冊)
via-vdfsys launch                # 八項現量 + 下一步卡(rc 0 可啟動 / 4 閘未開 / 3 家族境缺件 / 1 壞)
via-gates                        # 閘態一覽(不印原值)
$env:VIA_NET_CONSENT = 'YES'     # 你的手;爬蟲道另需 $env:VIA_SCRAPE_CONSENT = <期望 token>(via-gates 印)
via-vdffetch 2023 --dry          # 只印十一步計畫(Hydra 哨兵 H3/H5 紅=誠實停)
via-vdffetch 2023 --limit 100    # 先小量;不加 --limit = 全市場(史深 2023-01-01 起;十道並行;逾時 kill 不卡斷)
via-vdfchain run                 # 獨立鏈(rc0 綠 / rc4 閘)
via-vdfinc plan                  # 只列缺口,不重抓(批569 律)
via-vdfcov roster ; via-align check ; via-vdfsys
# 每日:VIA.ps1(全自動)或 launch.ps1 → via_boot_update.ps1(與 .sh 同鏈 ⓪–⑳;marker 每日首跑一次;
#   log VIA_Reports\boot_update_logs\BOOT_*_ps1.log 第二行寫 ⓪ 家族境 python 解到誰)
```

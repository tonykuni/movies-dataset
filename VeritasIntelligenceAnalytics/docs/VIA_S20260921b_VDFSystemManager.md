# VIA 交接紀錄 · 側線 2026-09-21 b(branch `claude/busy-bell-97sa4f`;主線批號由併線的手指定 L25)

操作員令:「將 session_01RLMQGZLcigd5Bt5aN6J4Ck 關於 VDF **全數接過來** · 建立 **VDF_SystemManager** 與 VIA 對接 · **VDF 所有引擎找出來** ·
讀取 VIA 政策**所有 PY 檔案一定要接加速器** · **所有 VDF 都要加裝網路工具**(`supportive modules\VeritasCeleritas.py` / `supportive modules\VeritasAegisNexus.py`)」
+ 貼回 via-vcgc:「註冊稽核 中央冊 5849/5879 缺 30 · 家族 267 已登 266 未登 1 · 操作介面 225:VRN_ENG088_SsotAdditiveBridge_v0100.py」
+ 工作站 `git push -u origin claude/brave-goldberg-ri5k42` → `error: src refspec does not match any`。

〇 接手提示詞 → docs/VIA_AI_Handover_Prompt_v*.md(尾版)。本批的接手驗收在第八段;一貼即用在第九段。

## 一 · 律(本批沒有新律;用到的逐條註明)

L02/L18 七處登記 · L04 尾版律 · L05/L30 Zero-Hydra(同一判準只寫一處;抄到函式才算出處 LL316)· L07/L08 同意閘只讀永不代設 · L09 網路只認 Nexus ·
L16 誠實四態 · L17 自測只落暫存 · L20 VCGC 唯一對接口 · L22/LL49 再生冊不入 git(Manager 再生的總控頁例外)· L25 多 AI 交會(先併主線再造件;側線不占批號)·
L57 誠實分母 · L61/LL331 先量再造 · L70 .ps1 逐次許可 · L92 修法句 · L93 先疑尺。

## 二 · 開始前先量(L61):令裡四件事,量出來各是什麼

| 令 | 量到的現況(造件前) | 結論 |
|---|---|---|
| 「VDF 全數接過來」 | 那個 session 的 VDF 工作已在本線:`docs/VIA_VDF_StatusReview_20260921.md`(〇–十三 + 追記);主線批663–679d(15 份 B 文 · VDF 獨立鏈 CGC_MDL170 · 全景批次計畫 · 打包閘 · 兩條車道)與批681/682(VRN 那扇門)已由兩次 merge(`8a6c8cd0` · `884fe02e`)併進本線 | 不複本,**指**:對接口 records 域由 git 尾註量血脈(session 11 · commit 800 · 提到 VDF 75)、VDF 文 16、收容包 11、活線 31 |
| 「所有 PY 一定要接加速器」 | VDF 下 196 支 .py(不含 references):加速器橋 **196/196**;尾版 43 支 **43/43** | 律已滿。本口每跑逐支量並守住:尾版少一支就是 **RED**(尺=CGC_MDL124 的表頭常數;docstring 提到不算) |
| 「所有 VDF 都要加裝網路工具」 | 尾版網路橋 **43/43**;真向外擷取(批402 判定)3 支都有橋;版史 188/196(舊版 8 支沒有,只報不判) | 同上。本口自己也是 VDF 件 → 檔頭也掛兩座橋(自測 ② 三座橋在位) |
| 「VDF 所有引擎找出來」 | VCGC 的尺(ENGINE_GLOBS)只掃 `VDF/engine`,**VDF 根目錄三支**(VDF_ENG045_OutputHub · vdf_input_matrix · 新的 VDF_SystemManager)不在受治理範圍;`engine/` 另有 **8 支沒版號的 .py**(ENG046/047/049/050/051 · MDL002/003/007)尺照舊看不見 | VCGC v0120 ENGINE_GLOBS +VDF 根 → 家族 270→273、中央冊補號;無版號 8 支:對接口 logic 域分開報「無版號」(5 支只有無版號檔而卡書指著它們;3 支 ENG047/050/051 旁邊另有尾版=疑似舊複本,L05 候裁),**只報不改**——立版號/清複本是操作員的手 |
| 貼回「未登 1:VRN_ENG088」 | 工作站的樹沒有批682 的中央冊(ENG088 在本線已是 VIA-ENG-0091);本線併主線後 registry-sync 又量到新缺 82(VCGC v0119/對接口/根目錄三支的 AST 件) | `registry-sync --apply` 一次:新 83 · 變更 208 · 退役 0;再 plan:新 0 · 變更 0。VCGC status:**中央冊 6074/6074 缺 0 · 家族 273 已登 273 未登 0** |

## 三 · 造了什麼(每件一句話 + 證據)

| 件 | 做了什麼 | 證據 |
|---|---|---|
| `functional modules/VDF/VDF_SystemManager_v0100.py`(新) | VDF 子系統管理對接口,與 VRN 那扇門(批681/682 v0101)**同一份契約**:九域(政策/邏輯/因子/參數/引擎/**橋**/**工具**/交接/紀錄)· 動詞 status/engines/bridges/tools/catalog/links/records/read/sync/page/--selftest · 六態燈 · rc 0/1/2(引擎面不折進 rc)· 雙模式 subsystem/standalone · 快照只落 VIA_Reports/vdf_system 且 --apply 才寫 · 自適應連結(現解尾版/現算 sha/現量年齡;sync 對上次快照 NEW/CHANGED/GONE/SAME)| `--selftest` **27/27**(py3.11 · 3.12);status 連結 106(GREEN 101 · STALE 4 · NODATA 1)rc 2 |
| 同上:橋域 | 每支尾版量加速器橋/網路橋/真擷取;排除清單與真擷取判定**委派** CGC_MDL124(`_excluded` / `_is_net_caller`),標記的尺用它的 `ACCEL_START/NET_START` | 單元測試 T02:對接口逐支判定與 `CGC_MDL124.scan` 逐檔同答(≥40 支) |
| 同上:工具域 | 兩支工具正典位在不在 · 各副本 md5 同不同一份 · SUP_MDL740/737 尾版 · 加速器控制面存證 · 同意閘現態(只讀)| VeritasAegisNexus 3 副本同一份 GREEN;**VeritasCeleritas 3 副本兩個版本 STALE**(accelerator/ 237,382 B `f6ecbfc4…` vs 根 + 50_Protection 237,062 B `d9b107e2…`)→ 候操作員裁哪份是正典(L05) |
| `CGC_MDL149 …_v0120.py`(新版;主線批682B 同一小時取了 v0119=㉕ 執行期境不進等式,L25 改號:本線疊在它上面,它的 ㉕ 原樣保留)| +`_vdfsys()/vdf_system()`(缺席 ABSENT 不退舊路)· status 一行 · 一頁 **十四** · 頁一卡 · ENGINE_GLOBS +`functional modules/VDF` 根 · +㉖ | **26/26**(py3.11 · 3.12);status:VDF 系統管理 STALE/NODATA · 橋 加速器 43/43 網路 43/43 真擷取 3 · 七處 5/7 |
| 規格冊 `VIA_InputConsole_Spec_v0100.json` | vdf 家族 +`management` 群 +`vdf_system` 項(verb=status · test_verb=--selftest · net false · outputs 四件)| 規格 65→66 項;EngineBus `matrix --apply-family vdf --ids vdf_system --profile test` **GREEN** 5.1 s |
| Grid v0434(新版) | +兩站(廿七檢 rc0 · status nodata_ok);中央控管台站名 二十二檢→**二十六檢**(兩批沒跟上,一起對正)| `--only 子系統管理`:**5 站 OK**(VRN 兩站 · VDF 兩站 · 子系統管理十檢;REFAIL_20260921_085823.json);add( 285→287 |
| Deck v0159(新版) | +`vdf_system` **+`vrn_system`**(批681 主線刻意不碰 PR #53 佔著的 Deck,VRN 那扇門的 Deck/Manager 兩處一直缺著);釘 90→92(① 與 ㉕ 一起改)| Deck `--selftest` 25/25;VRN 對接口七處 4/7 → 6/7 |
| Manager v0148(新版) | +四個純中文正式名稱(vrn_system/vdf_system 任務 · VRN_SystemManager/VDF_SystemManager 引擎);`--no-open` 再生總控頁(正式任務 92)| Manager 十檢 10/10;契約測試 19/19(py3.12);總控頁 diff 只在任務清單(LL49 例外件,入 git) |
| 中央冊 `VIA_Component_Inventory_SSOT_v0100.json` | `registry-sync --apply`(唯一寫入口)| VDF_SystemManager=**VIA-SYS-0012** · VDF_ENG045_OutputHub=ENG · vdf_input_matrix=SYS;⑬ 由紅轉綠 |
| 台帳 `VIA_AutoCode_Registry_v0100.json` | +1 筆(1280→1281;indent=2 同式)| — |
| `tests/test_vdf_system_manager_v0100.py`(新) | 20 檢:本體 3 · 橋律兩把尺 2 · VCGC 委派 3 · 快照 1 · 七處 6 · 讀器 5;Register 短令**只量不假設** | py3.11 · 3.12 **20/20**(交接文寫完前 19/20,缺的正是本文) |
| `VDF_SystemManager_v0101.py`(新版) | Register 一登冊,v0100 的 ⑱ 就紅:它把「Register 未登必須 False」這個**暫態**釘成不變量。v0101 改成量 Register 尾版(登了 True、沒登 False);其餘一字不動,v0100 留作版史(L04) | 27/27(py3.11 · 3.12);單元測試 20/20 |
| `VRN_SystemManager_v0102.py`(新版;主線 v0101 留作版史) | 同一處 ⑱:via-vrnsys 一登冊,主線 v0101 的「未登必須 False」就紅(Grid --only 子系統管理 實錄 4/5)。v0102 改量 Register 尾版;其餘一字不動。主線批號由併線的手指定(L25) | 25/25(py3.11 · 3.12);Grid 5/5 |
| Register v0242(新版;v0241 一字不動) | 操作員「依你建議執行」= L70 這一次的許可 → +`via-vdfsys`(資料對接口)· +`via-vrnsys`(研報對接口;批682 Z65)守門版 + 梭 4 支(根+bin,不釘版號) | 兩扇門七處 **7/7**;Z65 · Z88 結案 |

## 四 · 量到但沒改的(L16 只報,候裁)

1. **VeritasCeleritas 兩個版本**(工具域 STALE):`supportive modules/accelerator/`(CGC_MDL156 正典位)與 `supportive modules/` 根、`50_Protection_Acceleration/` 不是同一份。哪份是正典要操作員裁;裁了之後對接口自己會轉綠。
2. **engine/ 8 支無版號 .py**(L04 外):ENG046_FetchMatrixRegistry · ENG049_FiveDayFetch · MDL002_YFinanceFetchingEngine · MDL003_SentimentMacroEngine · MDL007_SSOTResolver 只有無版號檔(卡書指著它們);ENG047_USMacroDetailFetcher · ENG050_OrderFetch · ENG051_ActiveTWETF_Holdings 旁邊另有尾版檔(疑似舊複本)。立版號/清複本後卡書要重建(不手改)。
3. **卡書 vs 樹**:冊有樹無 1(sector_rotation_capital_flow_engine)· 樹有冊無 3(VDF_ENG091_VdfAuditGate · VDF_ENG045_OutputHub · vdf_input_matrix)——卡書 45 張是舊快照,重建卡書是主線的事。
4. **一頁交接 批554 < 律冊 批662**(交接域 STALE;VRN 那扇門同樣報)· **VDF 獨立鏈容器沒跑過**(引擎域 NODATA:`via-vdfchain run` 在工作站跑一次就有快照)。
5. 規格冊 VRN `vrn_system` 項的 `verb` 原是六個動詞的清單(批681 主線寫法);EngineBus test profile 量到 **NODATA**(整串當 argv)。b 批既已動到這一項(outputs 檔名跟版號走),一併對正成 `verb=["status"]`+`test_verb=["--selftest"]` → GREEN。

## 五 · 兩條線、三條線(L25)

- 本線:`claude/busy-bell-97sa4f`(PR #53)。造件前把 `origin/main`(批663–679d + 批681)與 `origin/claude/awesome-bardeen-h0wm5v`(批682)併進來:兩處衝突(VRN 邏輯架構冊 · 總控頁)都取主線版;台帳與規格冊做聯集(1280 筆 · 65 項)。
- 第三條線 `claude/brave-goldberg-ri5k42`(session_01JaiaB5…):本文第一版(09:00 前量的)寫「遠端沒有這條分支」;之後它從那個 session 推上去了,主線以 **PR #58** 併入(EngineBus v0128/v0129 · VCGC v0119 執行期境不進等式 · B682B 文 · 台帳 1282)。工作站那次 `src refspec does not match any` 的原因照舊:本地沒有那條分支,push 只能在那個 session 裡下。
- 18:01 貼回:工作站 HEAD 在 `claude/awesome-bardeen-h0wm5v` 批684(0b6f7dfb;批683 橋掃器 v0106 + PS 尾版注橋 · 批684 吸收 PR #57 的 EngineBus v0128 與 VDF 審視文),那三筆 main 還沒有。本線把它併進來(五處衝突:掉球冊取主線 · VDF 審視文取本線(本線多兩行追記,其餘逐行相同)· 台帳聯集 1285 · 元件冊取主線再以 v0120 重跑(6076/6076;VDF_SystemManager 仍 VIA-SYS-0012)· 總控頁由 Manager v0148 再生),所以工作站在 awesome-bardeen 上 `git merge --ff-only origin/claude/busy-bell-97sa4f` 是**快轉、零衝突**。
- 18:36 貼回:工作站 awesome-bardeen 已推到 批686(53736e39;批685 上傳整合引擎收容 · 批686 鏈跑器 v0102 + Grid v0435/v0436),main 併了 PR #60(到 批685)。本線再併一次(四處衝突:掉球冊取主線+本線五顆改號 Z88–Z92 · 台帳聯集 1288 · 元件冊取主線再以 v0120 重跑 · 總控頁再生);Grid **v0437** = 主線 v0436 + 本線兩站 + 中央控管台站名(主線 v0435/v0436 從 v0433 長出來,沒有本線 v0434 的兩站,尾版律下兩站會消失——併線的手要重貼)。之後工作站 `--ff-only` 又成立。
- 撞號(L25):本線與主線批682B **同一小時各造一支 VCGC v0119**(主線批686 的掉球冊 Z86 也記了這一顆;本線 v0120 已解,Z86 標已解)。本線併主線時取主線的 v0119,本線的 VDF 對接口段改號 **v0120** 疊在它上面(它的 ㉕ 原樣保留,本線的 VDF 檢改 ㉖,二十六檢);台帳聯集 1283;元件冊以 v0120 重跑(273/273 未登 0)。

## 六 · 容器實測(全部零網路)

| 檢 | 結果 |
|---|---|
| VDF_SystemManager `--selftest` | 27/27(py3.11 · 3.12;`-W error` 可編譯) |
| VCGC v0120 `--selftest` | 26/26(py3.11 · 3.12;主線 v0119 的 ㉕ 原樣保留) |
| VCGC status 註冊稽核 | 中央冊 6074/6074 缺 0 · 家族 273 已登 273 未登 0 · 操作介面 231 · Deck 92 · 規格 66 · 格子 289 站 · Register 166 |
| Deck v0159 / Manager v0148 | 25/25 · 10/10 |
| 契約測試 test_master_control_contract_v0102(py3.12) | 19/19 |
| Grid v0434 `--only 子系統管理` | 5/5 OK |
| EngineBus v0129(主線 PR #58 尾版)test profile `vdf_system` / `vrn_system` | GREEN / GREEN(vrn 項 verb 對正前 NODATA) |
| Register v0242 · 梭 4 支 | VCGC Register 168 指令 · 兩扇門七處 **7/7** · CGC_MDL157 29/29(短令必有梭)· CGC_MDL174 四面登錄 VDF/VRN GREEN(Register · 梭 根+bin)· CGC_MDL168 A 語法道 ABSENT(容器無 pwsh,工作站格子會判;B 參數道 GREEN) |
| MDL174 打包閘 VDF ④ 四面登錄 | GREEN 93/93 |
| 單元測試 test_vdf_system_manager_v0100 | 20/20(py3.11 · 3.12) |

## 七 · 掛著(下一手接)

- Z88 已結:Register v0242 + 梭 4 支(操作員「依你建議執行」)。(本文第一版寫 Z74–Z78 撞主線批683 的 Z74–Z77;第二版 Z82–Z86 又撞主線批685/686 的 Z82–Z87;第三版接續 Z88–Z92)
- Z89 VeritasCeleritas 正典裁定(四-1)。
- Z90 engine/ 無版號 8 支立版號 + 卡書重建(四-2、四-3)。
- Z91 工作站跑 `via-vdfchain run`(引擎域拿到快照)與 `via-vcgc page --publish`(交接域批號對上)。
- Z70 已結:brave-goldberg 由 PR #58 併入 main。
- Z92 工作站把本線快轉進 awesome-bardeen 後跑 `via-vdfsys` 與 `via-vcgc`(應印 v0120);17:08/18:01 兩次貼回的 via-vcgc 都是 v0118 · Deck 90 · 規格 65 · 台帳 1282 = awesome-bardeen 批684 的樹,還沒有本線;`git checkout` 被工作站再生的 VIA_VRN_LogicArchitecture_SSOT 冊擋住(LL49 冊,stash 掉即可)。

## 八 · 接手驗收(一行一答)

1. `python "functional modules/VDF/VDF_SystemManager_v0100.py" --selftest` → 27 檢 FAIL 0。
2. `python "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0120.py" status`(或 `via-vcgc`,應印 v0120)→ 有「VDF 系統管理」一行;註冊稽核 未登 0。
3. `python "supportive modules/registry/tests/test_vdf_system_manager_v0100.py"` → Ran 20 · OK。
4. `via-selftest --only 子系統管理` → 5 站 OK。

## 九 · 一貼即用(已入 Register v0242 + 梭;下面兩行留給還沒點源新冊的視窗——點源 v0242 或 `via-fresh` 之後就不用貼)

```powershell
# ── 側線 2026-09-21:via-vdfsys —— VDF 子系統管理對接口(VDF_SystemManager;上接 VCGC 下管四庫+引擎面+橋/工具面+交接/紀錄;零網路 · 預設只讀 · sync --apply 才落 VIA_Reports/vdf_system)
#   via-vdfsys                         status:九域燈 + 連結表 + 七處自審(rc0 綠 / rc2 過期或缺料 / rc1 壞)
#   via-vdfsys engines|bridges|tools|catalog|links|records
#   via-vdfsys read <policy|logic|factor|param|engine|bridge|tool|handover|records|upstream> [key] [--full]
#   via-vdfsys sync --apply            落快照(只落 VIA_Reports/vdf_system)
#   via-vdfsys --selftest              廿七檢(零污染)
function global:via-vdfsys { $a = ConvertTo-VIACleanArgs $args; $eng = Get-VIANewest "$VIA\functional modules\VDF" "VDF_SystemManager_v*.py"; if (-not $eng) { Write-Host "  [via-vdfsys] ABSENT:functional modules\VDF\VDF_SystemManager_v*.py 不在這棵樹(把 claude/busy-bell-97sa4f 併進來)" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }; $py = Get-VIAEnvPython "vdf"; Invoke-VIAPython -Python $py $eng $(if ($a) { $a } else { "status" }) }
Set-Alias -Name 資料對接口 -Value via-vdfsys -Scope Global -Force

# ── 批681/682:via-vrnsys —— VRN 子系統管理對接口(VRN_SystemManager;Z65 候准)
function global:via-vrnsys { $a = ConvertTo-VIACleanArgs $args; $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_SystemManager_v*.py"; if (-not $eng) { Write-Host "  [via-vrnsys] ABSENT:functional modules\VRN\VRN_SystemManager_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }; $py = Get-VIAEnvPython "vrn"; Invoke-VIAPython -Python $py $eng $(if ($a) { $a } else { "status" }) }
Set-Alias -Name 研報對接口 -Value via-vrnsys -Scope Global -Force
```

18:01 實錄:第一版貼行在沒有對接口的樹上跑出 `python.exe: can't open file '…\status'`——`Get-VIANewest` 回空,`Invoke-VIAPython` 就把 `status` 當腳本餵給 python。上面已改成守門版:缺件印 ABSENT、rc 2、不呼 python(L16)。操作員 17:08 已把第一版兩個 function 貼進 PowerShell 現行 session(不是 Register 檔)。同一貼回的 via-vcgc 印 **v0118 · Deck 90 · 規格 65 · 台帳 1282**:工作站的樹是 main(PR #58 之後),還沒有本線,所以那棵樹上 `via-vdfsys` 會找不到 `VDF_SystemManager_v*.py`。本線已含 awesome-bardeen 批684,工作站在 awesome-bardeen 上快轉即可:

```powershell
git stash push -m "工作站再生冊(LL49)" -- "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VRN_LogicArchitecture_SSOT_v0100.json"
git fetch origin claude/busy-bell-97sa4f
git merge --ff-only origin/claude/busy-bell-97sa4f
git stash drop     # 那份是引擎再生冊,要就 via-vrnbook build 再生
via-vcgc           # 應印 v0120,多一行「VDF 系統管理」
via-vdfsys         # 九域燈;via-vdfsys bridges → 加速器 43/43 · 網路 43/43
```
操作員「依你建議執行」後已寫進 Register v0242 + 根/bin 兩支梭(L70 這一次的許可)。

工作站驗收(切到本線之後):`via-vdfsys` → 九域燈;`via-vdfsys bridges` → 43/43 · 43/43;`via-vcgc` → 註冊稽核 未登 0;`via-vdfchain run` → 對接口引擎域從 NODATA 轉為鏈跑器的燈。

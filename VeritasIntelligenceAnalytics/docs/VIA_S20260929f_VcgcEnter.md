# 側線 2026-09-29 f:`via-vcgc enter` —— 一句進環境(位置 · 只快轉的更新 · 閘 · 加速器 · 工具版本 · 啟動全部)

主線批號由併線的手指定(L25)。本批接在 PR #371(ae3895a7)之後。

## 一、操作員令(原文)

- 「應該要有進入環境指令 由vcgc進入跑他的流程如規定 加入加速器並告知目前加速器 網路工具 layout工具版本 ssot一切整合最佳化測試除厝更新啟動全部」
- 同一則實錄:PowerShell 停在 `C:\Users\tonyk`,`git push` → `fatal: not a git repository`。

## 二、先量(改碼之前)

| 量到的 | 所以 |
|---|---|
| `git push` 失敗的原因是 shell 所在的資料夾不在倉內(`C:\Users\tonyk`),不是倉壞了 | 進環境的第一件事是「現在在哪」:不在倉內要講出那一行 `Set-Location`,git 要一律帶 `-C 倉根` |
| 母倉 `via-entry`(Register v0243)會 `Set-Location $VIA`、設 `VIA_ROOT` 等環境;Grok 的 `via-enter` 走寫死的根目錄 | 「進倉」的短令已經有了;缺的是進倉之後照規定跑的那一整串 |
| 工作流 SSOT 已經規定入口流程:VCGC-WKF001「中樞入口流程」,STP002 流程閘(`status`)必須是本輪第一筆中樞事件 | `enter` 照它走:閘沒過,一步都不跑 |
| `via-vcgc status` 只**列出**加速器與網路工具(步驟矩陣第 3 步「導入,不執行」),沒有真的載入,也沒有 layout 版本 | `enter` 真的載入加速器(`activate()`),並把鎖冊上的六件工具版本一次報出來 |
| `via-vcgc go`(v0166)跑操作台 PowerShell 尾版:閘 → ENV MANAGER → 註冊同步 → VDF → 全景實測 → … → 單一路徑驗證 → 紀錄上傳;但**不會 git pull** | 「更新」要在 `enter` 補上;「啟動全部」交給 `go`,不另寫第二份流程 |
| 容器量:載入加速器 0.3 秒(`VeritasCeleritas_v1141.py`,執行緒預算寫進 17 個環境變數)· 網路核心載入 1.2 秒(`VeritasAegisNexus_v1652.py`,不連網、不寫檔) | 兩件都便宜,每次 `enter` 都真載 |
| Python 改不了 PowerShell 的目前資料夾 | 「進倉再跑」要一句完成,得在命令冊加一行 —— L70 不動 `.ps1`,寫成一次貼(第八節) |

## 三、做了什麼:`CGC_MDL149_VeritasCentralGovernanceConsole_v0173`(新,薄尾)

```
via-vcgc enter [--card] [--no-pull] [go 的參數 …]
```

| 步 | 做什麼 | 紅了怎樣 |
|---|---|---|
| 0 第一步 省 Token | 同 v0170 的第一步 | 紅就停(不讀政策、不開子系統) |
| 1 位置與更新 | 目前資料夾在不在倉內(不在 → 印那一行 `Set-Location -LiteralPath '<倉根>'`)· 分支 · HEAD · 上游 · 本機改動檔數;`git fetch` 上游 → **只快轉**(`merge --ff-only`) | 分岔:不合併,講出 `git pull --no-rebase` 讓操作員決定;本機改動會被蓋:git 自己拒絕,照實印;都照目前版本繼續。不 stash、不 rebase、不 force、不 push |
| ↳ HEAD 有變 | 交給**更新後**的 VCGC 尾版接手(子行程 `enter --no-pull`,帶原參數) | 閘與後面各步都跑在新碼上 |
| 2 閘 | 照 VCGC-WKF001-STP002 跑 `status`(政策整冊 · 子系統座位 · 加速器 / 網路已接) | rc 不是 0 → 一步都不跑 |
| 3 加速器 | `VIA_SuperAccel_Module` → SUP_MDL737 尾版 → 鎖冊那一本 Celeritas,`activate()`:執行緒預算寫進本行程環境,後面 `go` 起的每一支子行程都帶著(L103 ①) | 載不起來 / 載到的不是鎖冊那一本 → 停 |
| 4 工具版本 | 鎖冊(CGC_MDL233 尾版 `status`)六件:加速器 · 網路工具 · layout · nlp · token · frame 的檔名 · 版號 · sha · 待啟用;網路載入器(SUP_MDL740 尾版)解析到哪一支、核心載不載得起來、同意閘開 / 閉(只報開閉,不印值);`layout` 動詞走哪一支;PS 模板章在不在 | sha 對不上 / 缺件 / 網路核心載不起來 / PS 模板缺 → 停(換版只經 `via-vcgc tools activate … --apply`) |
| 5 啟動全部 | 交給 `go`(操作台 PowerShell 尾版跑整輪);`--card` 只出卡不啟動 | `go` 的 rc 就是 `enter` 的 rc |
| 總結 | 一行總結 + 一筆中樞事件(verb `enter`;`VIA_HUB_RUN` 沒設就給本輪 `enter-…` 輪號,結束還原) | — |

幾個取捨(照實):

- **更新放在閘之前**:閘要判的是等一下真的會跑的碼;而且閘後座位冊若有變,既有流程(`VIA_VCGC_PUSH`)推 GitHub 時不會因為落後被拒、把本機分支弄成分岔。更新只做快轉,不是一個「步」,不留中樞事件;本輪第一筆中樞事件仍是閘。
- **總結事件排在本輪最後**:v0168 的 `run_events` 依 `t0` 排序。第一版把 `enter` 的開始時間當 `t0`,容器實跑 `via-vcgc workflow <輪號>` 判 **RED**「本輪第一筆不是 H1 流程閘」—— 總結事件包住整輪,開始得最早。改成 `t0` 記寫入當下、開始時間另存 `started`;自測 ⑮ 用工作流冊尾版實核(含一個時間確定的排序案例)。
- 推送仍只走既有流程;本動詞自己不 push、不設同意閘、不裝件。

## 四、格子 `CGC_MDL064_SelftestGrid_v0503`(新)

站名檢數(LL213):Veritas 中央控管台 **三十八 → 七十一**。站名從 v0129 起就沒跟上 —— v0130~v0172 各薄尾的檢號都由 `PRIOR.selftest()` 串著照跑,v0172 實印 56 檢,v0173 再 +15 = 71,照實數。站數不變,其餘站一字不動;新薄尾由 `newest()` 自動接上。

## 五、驗證

| 項 | 結果 |
|---|---|
| v0173 自測 ①~⑮ + 前版鏈 | rc 0 · 71 檢全 OK · 約 48 秒;更新那幾檢用暫存 bare 倉實跑 git(最新 · 落後快轉 · `--no-pull` · 本機改動被 git 拒 · 分岔 · 沒上游 · 不是倉),不連網 |
| 突變 | 18/18 全殺(第一輪 16/18:毫秒內排序同分被穩定排序蓋過、載入失敗第二道也判紅但理由錯 → 補確定性排序案例與判語檢查) |
| 殺手閘 CGC_MDL187 v0103(`--base origin/main --run-selftest`) | 11 條全過 · rc 0;KILL-10 記債(薄尾委派前版自測,前版檢號照跑) |
| 全景卡 | 問題 0 |
| 格子 `--only` | Veritas 中央控管台七十一檢 OK;SSOT 正則·同義字連動 三站:檢 · 規劃 OK,驗收 FAIL(見第六節,main 原樣就紅) |
| 容器實跑 `enter --card`(倉內) | rc 0 · 五步全綠:加速器 `VeritasCeleritas_v1141.py`(= 鎖冊,執行緒 3 maxsafe)· 網路工具 `VeritasAegisNexus_v1652.py`(載入器 SUP_MDL740 v0118 解析同一支,核心已載入,同意閘 閉)· layout `SUP_MDL743_GenericLayoutHub_v0109.py`(layout 動詞走同一支)· nlp v0105 · token v0116 · frame v0100 · PS 模板 ✓ |
| 容器實跑 `enter -NoOpen`(倉外) | 位置:不在倉內 → 印進倉那一行;閘過 · 加速器 · 工具全綠;交給 `go` → 容器沒有 pwsh,照實 ABSENT rc 2;中樞事件 status → go → enter 三筆同一輪號 |
| 工作流核對 | 修正後本輪第一筆 = H1 閘;未跑的步只是黃(容器沒跑 `go`) |

## 六、測到的既有紅(不是本批造成的)

`via-vcgc ssot verify`(格子「SSOT 正則·同義字連動驗收」站)在 **main 原樣**(拿掉本批兩支新檔、v0172 跑)就 rc 1:
「陸券清除驗收:殘留 2」(CGC_MDL177 verify:掃尾版 4050 支,活的陸券解析資料 2 支)。

| 檔 | 內容 | 進倉 |
|---|---|---|
| `functional modules/VRN/knowledge/VRN_Broker_Dict_v0100.json` | CICC · 中信證券 · 中金公司 | fee13320f(2026-09-25「broker: add the v2.0 houses without removing or renaming」) |
| `functional modules/VRN/VIA_VRNLogic_AllInOne_v0201.py` | 中信證券 | 126832518(2026-09-28「vrn: add the all-in-one logic file without removing a node」) |

兩批都是「只增不刪」的收件,和操作員批413 的拒絕清單衝突。要留(加許可)還是清(出新版檔清掉)是操作員的裁定(LL90),本批不動。

## 七、登錄

- 元件冊:`registry-sync --apply`,新 23 · 變更 51 · 退役 0(新增 v0173 的定義 · 格子 v0503 的定義換行號;沒有容器路徑)。
- 編號冊只增合併:`VIA-VCGC-MDL1436` 格子 v0503 · `VIA-VCGC-MDL1437` VCGC v0173 · FNC_VCGC +72;容器雜訊(FM 862 · TST 6 · LGC 2 · 時間戳翻動)全丟;編號 SSOT 只改兩本冊的 n/sha 與元件冊的 content_sha,各冊 n/sha 核過一致。
- 座位冊:CONSOLE 尾版 → v0173(閘自己寫的)。
- 台帳 1359(ADD)。

## 八、操作員怎麼用

第一次(工作站還沒有 v0173):

```powershell
Set-Location -LiteralPath C:\Users\tonyk\movies-dataset
git pull --ff-only
```

之後每天:

```powershell
via-entry            # 既有的唯一入口:進 $VIA(在倉內,git push 就不會再報 not a git repository)· 設環境
via-vcgc enter       # 照規定跑:更新 → 閘 → 加速器 → 工具版本 → 全部
```

- 只要看卡、不啟動:`via-vcgc enter --card`;不更新:`--no-pull`;`go` 的參數照傳,例如 `via-vcgc enter -Full -NoOpen`。
- 全程常超過 `Invoke-VIAPython` 預設逾時 1800 秒:先 `$env:VIA_PY_TIMEOUT_SEC = 7200`(`go` 開跑前也會提醒)。
- 要**一句**完成「進倉 + 全部」,需要在命令冊加一行短令(L70:本批不動 `.ps1`,這一行由操作員決定要不要加、加在哪):

```powershell
function global:via-in { via-entry; via-vcgc enter @args }
```

加在哪:下一版命令冊(`Register-VIA-Commands-v0263.ps1`,dot-source v0262 之後),或先貼在自己的 PowerShell profile 試用。
為什麼:Python 子行程改不了 PowerShell 的目前資料夾,只有 PowerShell 函式能 `Set-Location`;`via-in` 名稱已掃過母倉命令冊與 Grok 矩陣,沒有撞名。

## 九、還原

- `git revert` 本批的合併提交;或刪掉 `CGC_MDL149_VeritasCentralGovernanceConsole_v0173.py` 與 `CGC_MDL064_SelftestGrid_v0503.py`(`newest()` 會退回 v0172 / v0502),再把四本冊(元件冊 · 編號冊 MDL / FNC_VCGC · 編號 SSOT)與座位冊還原到前一版。

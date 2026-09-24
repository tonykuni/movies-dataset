# 批731 · 自測慢在哪 · 加速器真的用上 · 自測報告自己跳出來 · 2026-09-24

> 操作員 2026-09-24(貼回 via-vrnrun 全程之後):「PS PY檔案都要依規定裝加速器  剛剛跑好慢」;跑到一半補一句「自測報告要自動跳出來」。
> 常令:「自測實測自AUDIT直到完工  結果也要實測正確性  請自動完成」。
> 一句話:橋一直都在,**沒有一行碼用它**。這批讓它真的出力,並證明出力之後每一個答案都跟以前一樣。

## 一 · 工作站實錄:慢在哪

| 步 | 時間 | 結果 |
|---|---|---|
| V1 冊重建 | 1 秒 | rc 0 |
| V2 六層鏈實測 | 438 秒 | rc 2(GREEN 32 · NODATA 15)|
| V3 庫價與上漲空間 | 19 秒 | rc 0 |
| V4 驗真矩陣 · V5 U/I | 1 + 9 秒 | rc 0 |
| V6 實檔自測迴圈(106 份)| **1800 秒撞天花板被停**(rc 124)| G06 整批入庫 **20 分 13 秒**(一份 11.4 秒)· G07 6 分 36 秒 · G08 把 106 份**整批再入庫一次**,做到第 17 份被砍 |
| 合計 | 2268 秒(38 分)| 第一行還有「[Celeritas] 模板未接(無法將 'Test-CeleritasJoin' 字詞辨識…)」|

根因(容器逐段量過):

1. **一顆核心**:106 份一份接一份在同一個行程跑。加速器橋每支 .py 都有,但**從來沒有人呼叫 `VIA_ACCEL.activate()`**,它算好的執行緒預算沒被任何一段碼用上。
2. **同一個檔重讀好幾次**:首頁、附錄小字、欄表、G06、G07、G08 各自叫 pdfplumber 重新剖析同一份 PDF。剖析就是大頭(一份報告的時間幾乎全在這裡)。拒絕清單每次呼叫都重新正規化也是重複工,但在報告形狀的檔上量不出差別——照實記,不算它的功。
3. **G08 冪等整批重做**:冪等是 `upsert(ReportID)` 的性質,抽樣就驗得出,不必把 106 份再擷取一遍。
4. **PS 端加速器首載就炸(Z137)**:Celeritas 正主第 18 行開 StrictMode,第 24 行讀還沒設的 `$script:CeleritasPS7`;同族還有 `$OFS`、`$PSNativeCommandArgumentPassing`。
5. **V2 陪一格等到天花板**:六層鏈 L3 那一格跑 `VRN_AutoTestLoop --selftest`,裡面 104 支單元測試序跑要 80 秒;格子給每格 60 秒、工作站 180 秒。容器那一格就是撞 60 秒 → NODATA(「沒跑完=沒有結論」),同一層的其他格都得等它。工作站那一格佔 438 秒裡多少,要你這次貼回才知道。

## 二 · 修法

| 件 | 修什麼 |
|---|---|
| **VRN_BatchPool v0100**(新,`functional modules/VRN/engine/`)| 整批入庫的平行池。行程數 = `VRN_BATCH_WORKERS`(1 = 照舊序跑)> 加速器執行緒預算 `VIA_ACCEL_ACTIVE_THREADS` > CPU − 1,上限 6,不到 6 份照舊序跑。結果照原檔序交回;工作行程讀過的附錄小字帶回主行程快取。spawn 起動,主程式沒有 `if __name__` 守衛就不開池(容器實錄:沒守衛的測試腳本整批跑了四次)。池起不來或中途壞 → 沒跑完的改回序跑,並印一行原因 |
| 資料庫引擎 v0104 | `batch_pool_results()` 接池;`process_batch(only_files=)` 給 G08 抽樣用 |
| 證據核心 | 每頁字元、附錄小字、頁數**同一個檔版本只解析一次**(鍵 = 路徑 · 大小 · mtime_ns;檔改了就重讀;呼叫端拿副本,改了不污染快取);拒絕清單正規化一次 |
| **自測迴圈 v0104** | ① G08 抽 12 檔(首尾必在:檔名以報告日開頭,尾檔 = 最新一份;`--g08-sample N`、`--g08-full` 全批)② 起跑先 `VIA_ACCEL.activate()`,印 `[加速器]` 一行 ③ 進度總數 = G06 + G07 + G08 抽樣,百分比不倒退 ④ `--selftest` 單元測試並排跑:一個工作單位一個子行程(行程數同平行池),多類別的檔分份(每份一個類別,類別的共用前置一份跑一次),成本高的先跑;父行程被外面的天花板砍掉時子行程自己收(stdin 關了就走),不留著佔住市場庫 ⑤ 自測時平行池的一行說明改走 stdout:六層鏈先讀 stdout 再讀 stderr、只顯示最後兩行,`[計]` 那一行要是最後一行 |
| ADJ 真庫對照測試 | 一個類別拆成共用基底 + 三個類別(十個方法**逐字不動**,已比對),讓自測能並排跑它 |
| **跑手 Invoke-VIA-VRN-v0104.ps1**(新;v0103 不動)| V6 天花板 3600 秒(你設了 `VIA_PY_TIMEOUT_SEC` 就照你的);**跑完自動用瀏覽器開自測報告**(`via-open` 只找 Edge / Chrome / Firefox 的 exe,不走 .html 預設程式 = 不會跳 VS Code);`-NoOpen` 不開;報告沒生出來照實講 |
| **Celeritas PS7 正主(Z137)** | 你 2026-09-24 這句就是許可(L70):三處改成 `Get-Variable` 讀(第 24 行 `$script:CeleritasPS7` · `$OFS` · `$PSNativeCommandArgumentPassing`),其餘一字不動;收件夾原件不動 |
| **橋掃器 CGC_MDL124 v0107**(新)| ① Celeritas 本體與模板列進 PS 不可動冊(它們就是加速器,模板開了 StrictMode,再點源 25 冊會炸,Z137 同族)② **具名豁免名冊讀 CGC_MDL156 尾版 `_ACCEL_EXEMPT`**(一個出處;`ast.literal_eval`,不執行它)——見第四節 |
| CGC_MDL178 v0100 / v0101 | 補加速器橋(四系最後兩支) |

## 三 · 量測(容器 4 核 · 合成 20 份報告形狀的 PDF · 同一棵樹前後三跑)

| 段 | 修前 | 快取 + G08 抽樣 | + 平行池(3 行程)|
|---|---|---|---|
| G06 整批入庫 | 66 秒 | 75 秒 | **24 秒** |
| G07 首頁逐檔 | 20 秒 | 6 秒 | **6 秒** |
| G08 冪等 | 66 秒(全批)| 36 秒(抽 12)| **16 秒** |
| 一輪 | 158 秒 | 118 秒 | **48 秒(3.3×)** |

**答案一個都沒變**:三跑的 80 列閘結果「閘 · 名 · 狀態」逐列相同;明細只差 G08 多一句「抽 12/20 檔再入庫」;落庫 20 列(去掉時間戳欄)逐列相同。三跑都是 RED,紅的是同一批 G07 列——語料是同一份仿真報告換 20 個券商 / 代碼檔名,檔名與首頁本來就對不上,前後一樣紅才對。

自測門(`VRN_AutoTestLoop --selftest`):**80.4 → 約 52 秒**(四跑 51.4–54.2;107 支單元測試 + 合成小批,結論相同);`VRN_BATCH_WORKERS=1` 退回序跑 79.3 秒、同 107 支。

工作站估計(**估的,不算數,要你貼回**):G06 20 分 → 4–8 分(看你的核心數,最多 6 個行程)· G07 6.6 分 → 約 2 分 · G08 → 抽 12 份約 1 分 · V6 合計約 8–15 分,在 3600 秒天花板內;V2 那一格有機會在 180 秒內給出結論。

## 四 · 加速器覆蓋(全樹實掃)

| 面 | 結果 |
|---|---|
| PY 四系(併 main 之後)| VDF 242/242 · VAP 250/250 · VRN 396/396 · VIA 1985/1985 —— 100% |
| PY 全樹 | **3059/3059(100%)**;具名豁免 6 條,出處 `CGC_MDL156_VIAAcceleratorControl_v0109.py`。併進來的 main 只有一支沒橋:`CGC_MDL135_EnvGovernance_8Hub_v0100.py`(PR #105)——用橋掃器 `--apply` 注入(只插 14 行、原碼一字不動;它自己的 4 條測試照綠) |
| PS-ACCEL(25 加速器橋)| 掃 1045 · 已掛 846 · **缺 0** · 排除 199 —— 100%(跑手 v0104 入冊後算進已掛) |
| Celeritas PS7 模板 | 容器 pwsh 7.4 實接:「模板已接」· 收尾還原優先權 · 呼叫端的非嚴格模式沒被改 |
| Python 加速器 | 自測迴圈起跑就啟用:`[加速器] Celeritas 在位 · lib 16/88 · 執行緒預算 3`(容器) |

量到一個尺的洞:橋掃器 `--subsystems` 根層那一行一直是 **99.3%(3058/3079)**,差的 21 支全在批647 的正典 U/I TEMPLATE `VIA_HTML_UI`。那是 byte-exact 正本,完整性由它自己的 manifest.json(223 筆 sha256)守;批658 已裁定「正本零觸碰優先於全樹導入令」,MDL156 / MDL158 / via_bridge_sweeper 都有這條豁免,**只有 CGC_MDL124 沒有**——`--subsystems --apply` 會把橋注進正典。修的是尺(v0107 讀 MDL156 的名冊),不是那 21 支;名冊只增:原有各條排除理由照舊先答。另有 11 支本來就有橋、現在改報豁免(收容件 CGC_MDL001 六版 · 唯讀疊加層四版 · 一次性補丁一支),橋一個字都沒拿掉。

## 五 · 正確性

- `tests/test_VRN_BatchSpeed.py`(新,10 條):平行池 1 行程 vs 2 行程落庫逐列相同且同序 · 頁快取給副本、檔改了重讀、附錄答案 = 不走快取的答案 · 拒絕判斷與舊版逐字等價(被拒名從冊上現場取,本檔零字面)· G08 抽樣固定、分散、首尾必在 · 自測分份:每支測試恰好跑一次、成本高的先跑、失敗或死掉的單位照報不漏。
- VRN/tests **107/107**;自測門 2/2;資料庫引擎 `--self-test` PASS;全景稽核:本批新碼零新增(兩處吞例外改成講原因)。
- 陸券清除驗收:本批新測試檔一度把一個被拒名寫成字面值(格子抓到),已改成從拒絕清單現場取 → **活的 0 支**。

## 六 · 全格子(v0480 · 1179 秒 · 存證 `GRID_20260924_123050.json`)

**OK 340 · FAIL 2 · SKIP 6 · TIMEOUT 0**。六個 SKIP 與批730 相同(環境缺件照實報)。平行段一共紅過四站,逐一追到底:

| 站 | 原因 | 處置 |
|---|---|---|
| 陸券清除實跑驗收 | 我新寫的測試字串帶一個被拒陸券名 | 改從拒絕清單取;verify 活的 0 支;格子序跑複驗綠 |
| VRN 六層鏈實跑 | L5 `VRN_ENG069_ConsensusDB` 自測的 `build()` 寫**正式**市場庫、拿寫鎖,與同時段別站的讀鎖互撞(DuckDB 一寫多讀不能並存)| 格子序跑複驗綠;根因與候選件登 **Z189**(不是本批造成,平行格子才會撞)|
| 全景批次修復規劃器 ⑫-b | 負向例「尾版橋掃器不得被排除」:v0107 還沒 commit,`git ls-files` 看不到 = 「未在冊」(那支檔自己的註解記過同一個坑)| commit 後重跑,見第八節 |
| VCGC ⑬ 元件冊 | 格子跑到一半我在橋掃器加了兩個函式(9567/9569)| registry-sync 重跑 → 活元件 9569 · VCGC 37/37 |

## 七 · 掉球(LL334 改號兩次:main 已用到 Z182、側線分支推到 Z187 還沒併,本批取 Z188–Z190;`docs/VIA_DroppedBalls_B507.md`)

| 代號 | 事 | 狀態 | 誰 | 下一步 |
|------|----|------|----|--------|
| ~~Z137~~ | ~~Celeritas PS7 正主首載在 StrictMode 下炸~~ | 已結(批731)| 母線 | 三處 `Get-Variable`;容器 pwsh 7.4 實接、還原、不外溢 |
| Z188 | 本批的速度與自動開頁要在工作站實量(容器只有合成語料)| 操作員的手 | 操作員 → 母線 | 第九節那一段;貼回每一步秒數、V2 的 L3 那一格、V6 的 `[加速器]` `[VRN] 平行池` G08 明細,和報告有沒有自己跳出來 |
| Z189 | 平行格子共用正式市場庫 `vdf_tw_market.duckdb`:`VRN_ENG069_ConsensusDB` 自測寫正式庫(違 L17「自測只寫暫存」),撞到同時段的讀者就紅;靜態掃還有約 23 支尾版的自測可能開可寫連線(啟發式,未逐支核)| 未做 | AI | 逐支改成自測寫暫存庫(ENG070 / ENG071 v0103 的做法):ENG069 先;每改一支,全格子前後各跑一次比紅燈數 |
| ~~Z182~~ | ~~VRN 單元測試 `test_synthetic_loop_ends_green_or_amber` 沒有 python-docx 就紅(側線記的)~~ | 已結(批731) | VRN 線 | 斷言扣掉因缺 python-docx 跳過的檔(看報告 G05 SKIP 列),PDF 那一半照測;模擬沒有 python-docx:舊斷言紅、新斷言綠 |
| Z190 | main 的環境八樞紐 `CGC_MDL135_EnvGovernance_8Hub_v0100.py` 跟既有族撞號 MDL135(CGC_MDL157 站紅,main 也紅)| 候(操作員裁)| 操作員 → 環境線 | 改用 CGC_MDL186(改兩處引用)或併進 MDL135 族當下一版;本批只記不動 |

## 八 · commit 前重跑(本批檔全部暫存 → `git ls-files` 看得到 v0107)

| 站 | 結果 |
|---|---|
| 全景批次修復規劃器廿一檢 | OK |
| Veritas 中央控管台三十七檢 | OK(37/37;元件冊活元件 9569 · 新 2) |
| 陸券清除閘自測 · 實跑驗收 | OK · OK(活的 0 支) |
| VRN 六層鏈廿五檢 · 實跑 | OK · OK **86 秒**(平行段那一跑 116 秒);單站重跑時 L3 `VRN_AutoTestLoop` 那一格從 NODATA(撞 60 秒)變 **GREEN 52 秒**,鏈總表 GREEN 32 → 34 · NODATA 13 → 12(全格子平行負載下見八之二) |
| VRN 第二血統總驗(自測門) | OK 53 秒 |
| 橋塊掃描注入器 · 加速器控制面三十七檢 · Celeritas 產出契約閘 / 實跑 · PowerShell 語法與參數名閘 · SSOT 正則同義字連動 · 總控頁契約十九測 | 全 OK |

再生閘(CGC_MDL167)兩次:格子改寫的 40 + 1 支再生冊還原;留下元件冊 · regex 清冊(1372 → 1373 樣式,一條沒少)· VRN 索引冊 · 總控頁四件設計寫入口。

## 八之二 · 併 main dc5ed25e(PR #105 環境八樞紐 · PR #106 側線第四段 · PR #108 整併稽核)

本批 commit 之後 main 又進了 11 個 commit;照規矩先 commit 再 merge(不 rebase、不 force)。衝突四件:掉球清單(兩邊都接在 Z177 之後:main 的 Z178–Z182 在前,本批改號 Z188–Z189 在後)· 台帳(兩邊各自追加,取聯集:基底 1329 + main 1 + 本批 2)· 元件冊與 regex 清冊(取 main 那份,再用 registry-sync / CGC_MDL115 重生:活元件 9603 · 新 13,regex 1372 → 1373)。main 帶進來的六層鏈跑器 v0105 與格子 v0481 都重跑過,見本節末。

併線後全格子 **v0481**(947 秒 · 存證 `GRID_20260924_134049.json`):**OK 341 · FAIL 1 · SKIP 6 · TIMEOUT 0**。

| 站 | 結果 |
|---|---|
| 唯一接觸口控制面(CGC_MDL157)| **紅**,28/29:main 的環境八樞紐跟既有族撞號 MDL135(main 自己也紅)→ **Z190** 候你裁,本批不改別條線的模組名 |
| Celeritas 產出契約實跑(CGC_MDL183)| 平行段紅 → 序跑綠:main 新進的 `tests/test_env_governance_8hub.py` 沒加速器橋,用 via_accel_injector 的 `inject_py` 單檔注入(只插 14 行,4 條測試照綠) |
| VRN 六層鏈實跑(鏈跑器 v0105)· VRN 第二血統總驗 · 陸券清除 · 橋塊掃描 · VCGC 三十七檢 · PowerShell 語法 · 全景批次修復規劃器 | 全 OK |

照實記一件:六層鏈 L3 `VRN_AutoTestLoop` 那一格,**單站重跑 GREEN 52 秒**;但在全格子 348 站同時跑的負載下,自測門要 98 秒,這一跑那一格又撞格子給的 60 秒 → NODATA(不是紅)。工作站的 V2 是單獨跑鏈、每格 180 秒,是你那邊要看的情況(Z188 請你貼回)。

## 九 · 工作站(一貼即用)

同批730 那一段,只換成認批731 的檔(`VRN_BatchPool.py`)、分支叫 `b731-時間`、最後一行多撈 `[加速器]` `平行池` 與秒數。`via-vrnrun` 會自己挑最新的跑手 v0104;跑完**自測報告頁自己用瀏覽器開**。不要它開:`via-vrnrun -NoOpen`;要退回舊的序跑:先 `$env:VRN_BATCH_WORKERS = '1'`。

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
$top = git rev-parse --show-toplevel
"  [前] 分支 " + (git branch --show-current) + " · " + (git log --oneline -1)
git reflog -3 --format="  [前] %h %gs"
if (git rev-parse -q --verify MERGE_HEAD) { "  [前] 卡在合併:" + (git log --oneline -1 MERGE_HEAD) + " → merge --abort"; git merge --abort }
$held = @()
foreach ($p in @(git -C $top diff --name-only --diff-filter=U)) { if ($p -match '(ui_support/.+\.html|registry/VIA_(VRN_LogicArchitecture_SSOT|Engine_Consolidation_Register|Engine_Contract|SSOT_RegexDict|Schema_Registry|Unified_Register|ParallelLanes|ProjectCompletion|ProductGate|Component_Inventory_SSOT)_v\d+\.json)$') { git -C $top checkout HEAD -- $p; "  [解卡] 再生冊取提交版:" + $p } else { $held += $p } }
if ($held.Count -eq 0) {
    git reset -q
    via-regen --apply
    if (git status --porcelain --untracked-files=no) { git stash push -m "workstation-local-before-b731" }
    git stash list | Select-Object -First 3
    git fetch https://github.com/tonykuni/movies-dataset main
    git merge-base --is-ancestor main FETCH_HEAD 2>$null; $ff = ($LASTEXITCODE -eq 0)
    if (-not (git rev-parse -q --verify refs/heads/main)) { git switch -c main FETCH_HEAD } elseif ($ff) { git switch main; git merge --ff-only FETCH_HEAD } else { git switch -c ("main-latest-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    if (-not (Test-Path ".\functional modules\VRN\engine\VRN_BatchPool.py")) {
        "  [拉取] main 還沒併批731 → 改拉批731 的分支(它 = main + 批731,本機另開 b731-時間,不動 main)"
        git fetch https://github.com/tonykuni/movies-dataset claude/awesome-bardeen-h0wm5v
        if ($LASTEXITCODE -eq 0) { git switch -c ("b731-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    }
} else { "  [解卡] 人寫件卡在衝突,不自動處理,先停:" + ($held -join " · ") }
if ($held.Count -eq 0 -and $LASTEXITCODE -eq 0 -and (Test-Path .\Invoke-VIA-VRN-v0104.ps1) -and (Test-Path ".\functional modules\VRN\engine\VRN_BatchPool.py")) {
    "  [後] 分支 " + (git branch --show-current) + " · " + (git log --oneline -1)
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
    via-vrnrun 2>&1 | Tee-Object -FilePath "$env:TEMP\vrnrun_b731.txt"
    Select-String -Path "$env:TEMP\vrnrun_b731.txt" -Pattern '\[Celeritas\]|\[加速器\]|平行池|\[進度\] \d+/6|\[V[1-6]\]|\[進度\] \d+/\d+ L3|\[ROUND|G08|\[DONE\]|\[附錄\]|\[ADJ\]|FAIL G|WARN G|RED|rc=|總計|via-open' | ForEach-Object { $_.Line }
} else { Write-Host "  [拉取] main 跟批731 分支都沒拉到(上面幾行就是原因),先停" -ForegroundColor Red; git status --short | Select-Object -First 15 }
```

要貼回:`[前]` 幾行 · `[解卡]` 行 · `git stash list` 三行 · `[後]` 一行 · 最後撈出來的全部行,特別是 `[進度] 6/6 完成 · 總計 …` 那一行(每一步幾秒)、V2 裡 `L3_驗證 VRN_AutoTestLoop` 那一格、`[加速器]`(執行緒預算)、`[VRN] 平行池 N 個工作行程`、G08 的「抽 12/106」、`[DONE]`,以及**報告頁有沒有自己跳出來**(有的話是哪個瀏覽器)。

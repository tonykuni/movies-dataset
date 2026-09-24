# 批735 · VRN 模板(制式 U/I 套版 · synchronizer 控制)· 上下游自動連結與新增檢查 · 2026-09-24

> 操作員 2026-09-24(批733 以 PR #115 併進 main 之後):「實測無誤後結果驗證無誤後收尾並用制式模板html u/i套進去形成vrn模板都由synchonizer控制交接自適應式自動化」
> 「上下的自動連結更新新增檢查機能建構須完成」「若成功跑一次測試文件的成果用我們使用的html u/i顯示」。
> **LL334 改號**:取號前掃了 41 條分支——側線 `claude/upbeat-feynman-1uurww` 已經用了**批734**、**格子 v0492**、**掉球 Z207–Z209**
> (另有 PR #104 改號到批734)。本批改號 **批735**、格子跳號 **v0493**、掉球從 **Z210** 起。VCGC v0129、六層冊 v0108、VRN_ENG089 都沒人用。

## 一 · 做了什麼

| 件 | 改了什麼 |
|---|---|
| **VRN_ENG089_TemplateView v0100**(新)| 把自測迴圈的成果套進制式 U/I(`VIA_HTML_UI` 三入口),**模板一個位元組都不動**;synchronizer 控制;上下游連結冊;新增必上頁;十二檢 |
| VRN_AutoTestLoop v0106(原地改,無版號檔)| 每輪寫完報告就自動建 VRN 模板(落在 `<--out>/template`,永遠在這一輪的輸出夾底下);報告頁頂端橫幅「開中央頁 · 開 synchronizer · 對上一輪新增/異動/消失」;自測門 +③ |
| via_vrn_logic_book v0108 | L4_產出 +1 節點 ENG089(不上冊的話守門 ⑧「每個 VRN_ENG 家族都要被交代」會紅);引擎指標 45 → 46 |
| CGC_MDL149 VCGC v0129 | 一頁交接 +**十六段 VRN 模板**(讀 ENG089 的交接口,本台只翻譯)· 頁 +1 卡 · status +1 行 · +㊳(缺席 = ABSENT、炸掉 = RED 的反面控制);三十八檢 |
| CGC_MDL064 格子 v0493 | +1 站「VRN 模板十二檢」;站名檢數 Veritas 中央控管台 三十七 → 三十八(LL213,只換數字) |

版號補記:批732 / 批733 動過自測迴圈(財報恆等式、沒有框線的表),碼內註記寫 v0105,但 `LOOP_VERSION` 沒跟著改,報告一直印 v0104。本批一起補正,報告從此印 **v0106**。

## 二 · 制式模板怎麼套(模板零改動)

- **建之前先驗模板**:三個入口(啟動頁 `VIA-Complete-System.html` · 中央 U/I `VIA-UI-Standalone-NoServer.html` · `VIA-SYNCHRONIZER-Standalone.html`)逐檔對 `manifest.json` 的 sha256;對不上就不建(BLOCKED,講哪一支)。工作站 git 把換行改成 CRLF 的,換回 LF 再比一次,內容一致照建並點名(同批650:換行 ≠ 內容漂移)。
- **原樣複製到 `ui/`**,檔名不變,模板自己頁與頁之間的相對連結照通。啟動頁逐位元組 = 模板;中央頁與 synchronizer 只**插入**三段(`<!-- VRN-TEMPLATE:… -->` 夾住),拿掉插入段 = 模板原檔(自測 ③ 逐位元組驗)。
  - 預置(`<head>` 之後):synchronizer 共享狀態 `via.sync.state.v2` 的模組冊**只增不減**加一個 `vrn-report-template`。沒存過狀態就用模板自己的 `DEFAULT_MODULES`(建構時從 synchronizer 原始碼抽出來,不另寫一份);VRN 模組已經在(就算被你關掉)→ 一個字都不動;壞 JSON / 舊 v1 → 不寫(自測 ⑨ 用 node 實跑五種狀態)。
  - 資料(`</body>` 之前):這一輪的成果,`type="application/json"`,頁上零連線(借 CGC_MDL160 離線四尺驗,插入段零命中)。
  - 外掛:走模板正式外掛 API——中央頁 `VIA_REGISTER_ADDON`、synchronizer 頁 `VIA_REGISTER_SYNC_ADDON`。
- **由 synchronizer 控制**:中央頁 VRN 面板的開 / 關跟著 synchronizer 模組冊的 `enabled` 走(localStorage + BroadcastChannel `via.sync.v2`,即時)。在 synchronizer 關掉,中央頁面板當場收起;打開就回來;釘選、排序也在 synchronizer。
- **自適應**:認得的欄畫專屬段(總覽 KPI · 這一輪 · 關卡總表 · 關卡明細 · 欄位規格 · 財報 · 上漲空間 · 附錄 · 相依 · 引擎 · VCGC 尺 …)。**沒人認得的頂層欄一律一欄一段**(「其他欄位:… 自動收」),不吞。逐檔表的欄取每檔記錄鍵的聯集:上游每檔多一個欄,表就多一欄。超過 25 列的表收合;WARN / FAIL / 異動 / 消失的列拉到收合外面,不展開也看得到;收合摘要寫各狀態幾列。

## 三 · 上下游自動連結 · 自動更新 · 新增檢查

- **上游** = 自測迴圈報告 + 產出它的引擎(報告 `engines` 欄,逐支 sha256)+ 模板三入口 + **建構器自己**(本支換版或改碼 → 舊頁判 STALE)。
  報告用「內容簽章」:每輪必變的欄(產生時間 · 工作夾 · 樣本夾 · 最後入庫摘要 · 各輪明細)不算,兩輪結果一樣就是 SAME。檔案本身重寫過另用 `report_sha` 抓:頁上印著產生時間,所以 check 判 STALE、建構也不走「不重寫」捷徑。
- **下游** = 三張衍生頁 + synchronizer 模組 + VCGC 一頁交接(十六段讀 ENG089 的 `handover()`)。
- 每次建構寫連結冊 `VRN_TEMPLATE_LINKS.json`,逐項 NEW / CHANGED / GONE / SAME。**比對基準自動找**:輸出夾自己的上一版;沒有就找同一個上層夾裡上一輪的連結冊。PS 第六步每輪一夾(`VIA_Reports\vrn_autotest\<時間>\`),所以**每一輪自動接上前一輪**,新增 / 異動 / 消失講的是「對上一輪」。
- **新增檢查**:上游新出現的東西(新頂層欄 · 新關卡 · 新檔 · 新欄位規格)逐項點名,而且驗它**真的上了頁**(落在哪一段、那一段有那一列);有一項沒上頁 = 建構 rc1 並點名(反面控制 ⑦:把落點段拿掉,建構必須紅)。
- `check`:上游變了 → STALE;頁被手改或不見 → DRIFT;都對 → OK;沒建過 → rc2。上游、模板、建構器都沒變而且頁都在 → 頁不重寫(冪等)。

## 四 · 跑一次測試文件,成果用制式 U/I 顯示

- **真檔進不了容器**:`C:\測試樣本報告` 的 60 份 PDF + 4 份 DOCX 從來沒掛進 AI 環境(Z51 / Z144)。容器裡跑的是自測迴圈的**標準測試語料**:用名冊檔名合成的 107 檔 PDF / DOCX / TXT / JPG。
- 結果 **AMBER · PASS 358 · WARN 1 · FAIL 0**(29.6 秒),跟前幾次整批跑一模一樣。唯一的 WARN 是 `926708.jpg OCR_REQUIRED`:圖片檔要 OCR,OCR 還沒接,照實標。
- 模板建成 21 段;headless Chromium 實跑:衍生頁**零頁面錯誤** · synchronizer 模組冊第 6 列是 VRN(已啟用、已釘選)· 在 synchronizer 關 → 開,中央頁即時 1 → 0 → 1 · synchronizer 自己的操作紀錄記下「已停用 → 已啟用」。截圖兩張 + 中央頁本體已交給你。
- **跨輪**:同一個上層夾連跑兩輪整批,第二輪自動以第一輪為基準 → **新增 0 · 異動 0 · 消失 0 · 未變 512**(結果一樣就該是這樣);第一輪首建 512 項全算新增。
- 另外一次「把合成的 20 檔當真檔讀」出現 2 條 WARN「no broker」:那是合成檔的檔名本來就沒有券商、又走真檔模式才出現,不是退步。

## 五 · 制式模板的既有缺陷(Z210)——要模板線修

中央 U/I 的同步段呼叫 `toast(...)`,但 `toast` 是另一個 IIFE 裡的區域常數;同步段的範圍裡 `toast` 解析到 `<div id="toast">`(瀏覽器的 window 具名存取)。結果是 **synchronizer 每改一次狀態,中央頁就丟一次 `toast is not a function`**:狀態先套完才丟,功能沒掉,但通知不出來,主控台多一條未攔的錯。

- 證據:ENG089 的瀏覽器實跑**每一次都先拿原封模板對照**(沒有插入的三入口,在 synchronizer 切一個預設模組),原封模板的中央頁就丟這條錯;模板自己的 e2e `test_via_cross_page_sync.py` 沒聽 pageerror,所以一直沒抓到。
- 衍生頁的處置:插入段在外掛掛上時,把外掛 API 給的 `toast`(模板自己的那一支)掛上 `window.toast`。模板修好(`window.toast` 已是函式)這段就不作用。**模板位元組一個都沒動。**
- 模板本身怎麼修要你點頭(L100 正典模板):第一個 IIFE 定義 toast 後加 `window.toast = toast;`,或同步段改呼叫 `window.__viaToast`;重生 manifest;e2e 加聽 pageerror。模板修好那天,ENG089 的對照組會自己印「原封模板對照零錯」。

## 六 · 驗證

| 項 | 結果 |
|---|---|
| VRN_ENG089 自測 | **12/12**(有 node + playwright);沒有 playwright 的環境 11 + SKIP 1(瀏覽器那一檢照實 SKIP)|
| 自測迴圈 v0106 自測門 | **3/3**(① VRN/tests 全部單元測試 · ② 合成小批無 FAIL · ③ 模板三頁 + 連結冊落在暫存、報告頁有連結)53 秒 |
| 六層冊 v0108 | 17/17 · 引擎指標 46 |
| VCGC v0129 | **38/38**(registry-sync APPLIED:活元件 9725,新 39)|
| 契約 | 19/19 |
| 格子新站單跑 | VRN 模板十二檢 OK · `[正式庫]` 這 1 站前後三本一致 |
| 全格子 v0493 | (收尾跑完填)|

## 七 · 掉球

- **Z210** 制式模板既有缺陷(toast 具名存取)· 候(模板線)· 提議見第五節。
- **Z211** `via-vrnrun` 跑完自動跳出來的是報告頁;要**直接跳 VRN 模板頁**得改 .ps1(L70 逐次許可)· 等你定:① 維持現狀(報告頁頂端點橫幅)② 准改 .ps1,跳報告頁之後再開模板中央頁(在才開,-NoOpen 照舊不跳)。
- Z72 補記:第六步起每輪自動建模板,實檔跑一次就有實檔版的模板頁。

## 八 · 工作站(一貼即用)

同批733 那一段,只換成認批735 的檔(`functional modules\VRN\VRN_ENG089_TemplateView_v0100.py`)、分支叫 `b735-時間`。`via-vrnrun` 第六步跑完會自動建模板;跑完再開最新那一版的中央頁、印一次交接口。**本批沒有改任何 .ps1。**

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
    if (git status --porcelain --untracked-files=no) { git stash push -m "workstation-local-before-b735" }
    git stash list | Select-Object -First 3
    git fetch https://github.com/tonykuni/movies-dataset main
    git merge-base --is-ancestor main FETCH_HEAD 2>$null; $ff = ($LASTEXITCODE -eq 0)
    if (-not (git rev-parse -q --verify refs/heads/main)) { git switch -c main FETCH_HEAD } elseif ($ff) { git switch main; git merge --ff-only FETCH_HEAD } else { git switch -c ("main-latest-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    if (-not (Test-Path ".\functional modules\VRN\VRN_ENG089_TemplateView_v0100.py")) {
        "  [拉取] main 還沒併批735 → 改拉批735 的分支(它 = main + 批735,本機另開 b735-時間,不動 main)"
        git fetch https://github.com/tonykuni/movies-dataset claude/awesome-bardeen-h0wm5v
        if ($LASTEXITCODE -eq 0) { git switch -c ("b735-" + (Get-Date -Format "MMddHHmm")) FETCH_HEAD }
    }
} else { "  [解卡] 人寫件卡在衝突,不自動處理,先停:" + ($held -join " · ") }
$tv = ".\functional modules\VRN\VRN_ENG089_TemplateView_v0100.py"
if ($held.Count -eq 0 -and $LASTEXITCODE -eq 0 -and (Test-Path .\Invoke-VIA-VRN-v0104.ps1) -and (Test-Path $tv)) {
    "  [後] 分支 " + (git branch --show-current) + " · " + (git log --oneline -1)
    . (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
    $log = "$env:TEMP\vrnrun_b735.txt"
    via-vrnrun 2>&1 | Tee-Object -FilePath $log
    Invoke-VIAPython -Family vrn $tv status 2>&1 | Tee-Object -FilePath $log -Append
    $run = Get-ChildItem .\VIA_Reports\vrn_autotest -Directory -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    $page = if ($run) { Join-Path $run.FullName 'template\ui\VIA-UI-Standalone-NoServer.html' } else { '' }
    if ($page -and (Test-Path $page)) { "  [VRN 模板] 中央頁 " + $page; via-open $page } else { "  [VRN 模板] 這一輪沒有模板頁(看上面 V6 的 [VRN 模板] 那一行)" }
    Select-String -Path $log -Pattern '\[Celeritas\]|\[加速器\]|平行池|\[進度\] \d+/6|\[V[1-6]\]|\[ROUND|\[DONE\]|\[VRN 模板\]|\[ADJ\]|\[財報\]|rc=|總計|via-open' | ForEach-Object { $_.Line }
} else { Write-Host "  [拉取] main 跟批735 分支都沒拉到(上面幾行就是原因),先停" -ForegroundColor Red; git status --short | Select-Object -First 15 }
```

## 九 · 要貼回什麼

1. V6 的 `[VRN 模板]` 那一行(狀態 · 對上一輪新增 / 異動 / 消失 · 中央頁路徑),以及 `status` 印的「最新一版 · 共幾版 · OK / STALE」;
2. 中央頁 VRN 面板的截圖(實檔版);再到 synchronizer 頁把「VRN 研報自測成果」關掉,中央頁面板有沒有當場收起(一句話就好);
3. Z211 你選 ① 或 ②;Z210 模板要不要修(要修我就出模板新版 + manifest + e2e 聽 pageerror)。

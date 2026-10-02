# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-Review-v0106.ps1 — 短指令 via-review(別名 總檢):一次完整、快速的系統狀態總檢(只讀為主;GitHub 為主、本機為輔)
#   操作員(R49 2026-10-02):「整合成一次完整快速檢視系統狀態的工具 只檢查 github 整合 … 包含環境檢查 衝突去重
#   所有缺的環境補安裝一個指令 進入環境跑全部優化一回 所有控管的模組沒有號碼沒有註冊也是紅燈 all in one ps to review all
#   錯誤都要標註 ast 精準或彈性定位點」+「拿 via-vdffetch v0108 那段來改結合」。
#   本檔**不另寫一份邏輯**:每步都是既有正主(L04 只增不減),步驟機制沿 v0108(每步經 VCGC、VIA_FROM_VCGC=YES 只設本行程、跑完還原;
#   rc:0 綠 · 2 沒料/有發現 · 3 缺席 · 4 閘關 · 其他 紅)。
#   ① Git 整合檢視(唯讀快):fetch · 落後/領先 · 本機改動 · 衝突(UU)· 未追蹤;-Sync 才交給拉齊醫生 CGC_MDL143 sync --apply(零 force)
#   ② 撞名 / 短令閘(唯讀):CGC_MDL165 collide --json(每個短令真的指到一個東西;撞名 = 紅)
#   ③ 環境:CGC_MDL240 EnvManager check → 總判不是 GREEN 且帶 -Install(= 你親手開閘)才接正主
#        CGC_MDL135 tools --apply --approve → CGC_MDL137 run --family vdf,vrn --approve-install → 再 check(前後總判都記)
#   ④ 編號 / 註冊 / 下放漂移:`sdd check` + `ssot panorama`(VCGC → VDF → VRN 單向下放:參數 · regex · 同義字 · 編號 · 命名 · 註冊)
#        + 本檔的彈性掃描:受控夾裡的 .py 沒有家族編號(XXX_MDL###_ / XXX_ENG###_)或不在 FunctionInventory SSOT 尾版 = 紅燈
#   ⑤ 全景 AST 錨點:PAN-SCAN scan --fast --json + PAN-READ read … --json(CGC_MDL158 鎖冊 token;只 ast.parse 不執行)
#        + 本檔對全部 PS 進行 Parser.ParseFile(語法錯 = 紅);**每一條錯誤都標定位種類**:
#        AST精準 = 檔:行 來自 AST(PAN / PS Parser)· 彈性 = 檔:行 來自 regex/檔名(本檔掃描)· 行程 = 只有 rc / 訊息沒有行號
#   ⑥ 清單七步(-Lists):v0108 的 ① 原表(台股清單 / 主動 ETF / 新上市下市 / 兩張清單檔),經 VCGC,閘沒開誠實回 GATE
#   ⑦ 全部優化一回(-Optimize):交給 Invoke-VIA-RealTestCore 尾版(25 加速器 · VDF ∥ VRN · 覆蓋 · 全景 + 三合一),不複製它
#   ⑧ 多頁矩陣 HTML(自動開):總覽 · Git · 環境 · 編號註冊 · AST 錨點(含定位種類)· 步驟燈號 · 日誌;
#        貼回包 VIA_Reports\review\REVIEW_<時間>.md + REVIEW_latest.md(省 token:只收判決行 / 紅黃行 / 錨點)→ 剪貼簿
#   不代開網路同意閘;不 force;不 reset;不刪檔;VIA_Reports 不提交。
#   v0101(操作員 2026-10-02 實跑 v0100 貼回):(a) 修紅:函數內 $out 與腳本 $Out 同名(PS 變數不分大小寫)→ 日誌路徑被輸出陣列蓋掉,Join-Path 整片紅;改 $OutDir。
#        (b) 速度:②③④⑤ 全部改背景並行(直跑 python,不走脈動;PYTHONWARNINGS=ignore 只設本行程),① git / PS Parser / 彈性掃描在前景同時跑;
#        (c) 加檢視:SSOT 矩陣(參數 · regex · 同義字 · 編號 · 命名 · 註冊 · 上下連結)· 政策/邏輯庫(VCGC 每次 run 前置的 [政策][位階][衝突][靜態])·
#            WORKFLOW 檢視(sdd check)· MAIN 檢視(status · check · audit)· Python 編譯警告(SyntaxWarning 檔:行 = AST精準,只 compile 不執行、不寫 pyc);
#        (d) -Optimize 的全部優化一回帶 -StallSec 120 -MaxMin 20 上限。其餘一字照 v0100。
#   v0102(操作員 2026-10-02「強化不卡斷在加速」):車道看門狗 — 一條進度列顯示 完成/進行中/剩餘時間,整體上限 -LaneMaxMin(預設 8 分);
#        逾時的車道只停**本檔自己起的子行程**(不碰其他進程)、燈標 TIMEOUT(rc 124)、其餘照收照報,不卡死整輪。其餘一字照 v0101。
#   v0103(操作員 2026-10-02「進入環境指令加入」):⓪ 進入環境 = 正主 `via-vcgc enter --card`(側線 S20260929f:位置與更新(只快轉)· 閘 status ·
#        真載加速器 activate()· 鎖冊六件工具版本 · PS 模板章;--card 只出卡不啟動 go)。閘沒過 → 標紅、照樣往下做診斷(本檔是檢視不是啟動)。
#        -NoEnter 跳過;-NoPull 進環境不快轉更新。卡片全文進「進入環境」頁。本檔開頭也先 Set-Location 倉根並設 VIA_ROOT / PYTHONUTF8(同母倉 via-entry)。其餘一字照 v0102。
#   v0104(操作員 2026-10-02 貼回 v0103「test debug till it works 加速器 不卡斷」):
#        (a) 修紅:HTML 編碼函數取名 H 撞到內建別名 h = Get-History(別名優先於函數)→ 總覽表整片 Get-History 紅、$pages 掛掉;改名 HtmlEnc。
#        (b) 不卡斷:⓪ enter --card(內含 test --quick,量到 251s)改進背景車道與其餘 10 條並行,看門狗一起管;PYTHONWARNINGS=ignore 提前到最前面(enter 也不洗版)。
#        (c) 註冊檢視:1532/2301 紅是我的冊比對太窄(只比 FunctionInventory 一本)。改比 registry 夾全部 *.json/*.jsonl/*.md/*.txt(含 Consolidation / Roster / SSOT),
#            字根或帶版號皆算;逐支明細落 REGISTER_GAPS_<時間>.csv,錨點只收前 200 條(其餘看 csv),矩陣頁按家族計數。
#        (d) 報告一律用 ShellExecute 直開(不經任何包裝;-NoOpen 才不開)。其餘一字照 v0103。
#   v0105(操作員 2026-10-02「VIA-Review-OneClick-v0104 + VIA_PanoramaCheck_ALL_v0160 整合優化 指令整合為一」):
#        ⑨ VIA-VERB-ENGINE(右邊系統)的五支獨立入口併進同一輪 —— 不另寫邏輯,直跑 verb-engine 自己的正主,四條背景車道與其餘並行、同一個看門狗:
#          Invoke-VIAHealth      → ⑨a health.py(治理冊站點)
#          Invoke-VIA-GlobalRead → ⑨b global_read.py --html(只讀全景;範圍 GitHub HEAD)
#          Invoke-VIA-FullCheck  → ⑨c fullcheck.py --html(七段 + 三輪)
#          Invoke-VIA-LockCloseout → ⑨d engines.VIA_PanoramaCheck.status()(收尾鎖)
#          Invoke-VIA-PanoramaCloseout = GitHub 全景 DryRun + fullcheck → 已由 ① Git 整合檢視 + ⑨c 涵蓋,不重跑。
#        找引擎:-VerbEngine <夾> → 環境變數 VIA_VERB_ENGINE → %USERPROFILE%\VIA-VERB-ENGINE\verb-engine;找不到 = ⑨ ABSENT(不猜不下載)。
#        沒帶 -NoPull 先 git pull --ff-only(同原入口;失敗只記黃、不強推、照現有版本檢)。-NoVerb 整段略過。
#        非綠明細:health 站列 + 兩份 HTML 報告的 AMBER / RED 表列 → 步驟燈 · 貼回包 · 矩陣「VERB-ENGINE」頁。舊五支入口照舊保留(只增不減)。其餘一字照 v0104。
#   v0106(操作員 2026-10-02「檢視指令太多頁有重複有衝突 應該整合為一頁 各細節不漏 統一」;裁定由 via-review 產出這一頁):
#        ⑧ 不再自拼 13 分頁的多頁矩陣:把原每一頁的資料(總覽 · 進入環境 · Git · 環境 · 編號註冊 · AST 錨點 · SSOT 矩陣 · 政策 · WORKFLOW · MAIN ·
#        VERB-ENGINE · 步驟燈號 · 紅黃全文)寫成 REVIEW_<時間>.json,交給 VCGC 正主 CGC_MDL254_ReviewOnePage build --review 併進唯一頁
#        VIA_Reports\review\ONEPAGE_latest.html(各工具最新結果 · 燈號口徑統一 · 過期不冒充 · 衝突照列並標正主 · 冊外來源列未登錄 · 下一步只一份);
#        自動開的是這一頁;剪貼簿貼回包換成 ONEPAGE_latest.md。正主不在 / 失敗 → 退回 v0105 的多頁(不中斷)。其餘一字照 v0105。
# 用法:via-review [-Install] [-Sync] [-Lists] [-Optimize] [-NoEnter] [-NoPull] [-NoOpen] [-NoClipboard] [-Since yyyy-MM-dd] [-Dry] [-LaneMaxMin 8] [-VerbEngine <夾>] [-NoVerb]
# 結束碼:0 全綠 · 2 有發現(黃 / GATE / NODATA / ABSENT)· 1 有紅
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$Sync,
    [switch]$Lists,
    [switch]$Optimize,
    [switch]$NoOpen,
    [switch]$NoClipboard,
    [string]$Since = "",
    [switch]$Dry,
    [switch]$NoEnter,
    [switch]$NoPull,
    [int]$LaneMaxMin = 8,
    [string]$VerbEngine = "",
    [switch]$NoVerb
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$ErrorActionPreference = "Continue"
$script:Dotted = ($MyInvocation.InvocationName -eq ".")
$VIA   = $PSScriptRoot
$Repo  = Split-Path $VIA -Parent
$Reg   = Join-Path $VIA "supportive modules\registry"
$Rep   = Join-Path $VIA "VIA_Reports"
$OutDir   = Join-Path $Rep "review"
if (-not (Test-Path -LiteralPath $OutDir)) { $null = New-Item -ItemType Directory -Path $OutDir -Force }
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Utf8  = [Text.UTF8Encoding]::new($false)
$Red   = New-Object System.Collections.Generic.List[string]
$Yel   = New-Object System.Collections.Generic.List[string]
$Steps = New-Object System.Collections.Generic.List[object]
$Anch  = New-Object System.Collections.Generic.List[object]   # 錨點:File Line Cls Detail Locate(AST精準/彈性/行程) Source
$T0    = Get-Date

function Get-Py { foreach ($c in @($env:VIA_PY, "python", "python3", "py")) { if (-not $c) { continue }; $cmd = Get-Command $c -ErrorAction SilentlyContinue | Select-Object -First 1; if ($cmd -and $cmd.Source -notmatch 'WindowsApps') { return $cmd.Source } }; return $null }
function Get-Newest([string]$Dir, [string]$Filter) { Get-ChildItem -LiteralPath $Dir -Filter $Filter -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1 }
function G { & git -C $Repo @args 2>&1 | ForEach-Object { "" + $_ } }
function Read-JsonTail([string]$p) { if (-not (Test-Path -LiteralPath $p)) { return $null }; $t = Get-Content -LiteralPath $p -Raw -Encoding UTF8; $i = $t.IndexOf("{"); if ($i -lt 0) { return $null }; try { return ($t.Substring($i) | ConvertFrom-Json -Depth 64) } catch { return $null } }
function Add-Anchor([string]$File, $Line, [string]$Cls, [string]$Detail, [string]$Locate, [string]$Source) {
    $Anch.Add([pscustomobject]@{ 檔=$File; 行=$(if ($Line) { "" + $Line } else { "-" }); 類=$Cls; 說明=$Detail; 定位=$Locate; 來源=$Source }) }
function Lamp([int]$rc) { switch ($rc) { 0 { "GREEN" } 2 { "NODATA" } 3 { "ABSENT" } 4 { "GATE" } 124 { "TIMEOUT" } default { "RED" } } }
function Add-Step([string]$No, [string]$Name, [string]$Lamp, $Rc, [int]$Secs, [string]$Note) {
    $Steps.Add([pscustomobject]@{ No=$No; Step=$Name; Lamp=$Lamp; Rc=$Rc; Secs=$Secs; Note=$Note })
    $c = if ($Lamp -eq "GREEN") { "Green" } elseif ($Lamp -eq "RED") { "Red" } elseif ($Lamp -eq "INFO") { "DarkGray" } else { "Yellow" }
    Write-Host ("  [" + $No + "] " + $Name + " · " + $Lamp + " · rc " + $Rc + " · " + $Secs + "s" + $(if ($Note) { " · " + $Note } else { "" })) -ForegroundColor $c
    if ($Lamp -eq "RED") { $Red.Add($No + " " + $Name + ":" + $Note) } elseif ($Lamp -notin @("GREEN", "INFO")) { $Yel.Add($No + " " + $Name + ":" + $Lamp + " " + $Note) } }
# 經 VCGC 跑一個正主(沿 v0108):回 @{ rc; out; secs }
function Invoke-Vcgc([string[]]$Argv, [string]$LogName) {
    $t0 = Get-Date
    $argv = @($V.FullName) + $Argv
    $raw = if (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue) { Invoke-VIAPython -Python "python" @argv 2>&1 } else { & $py @argv 2>&1 }
    $rc = $LASTEXITCODE
    $out = @($raw | ForEach-Object { "" + $_ })
    if ($LogName) { $out | Set-Content -LiteralPath (Join-Path $OutDir ($LogName + "_" + $stamp + ".log")) -Encoding UTF8 }
    return @{ rc = $rc; out = $out; secs = [int]((Get-Date) - $t0).TotalSeconds } }
# 從正主輸出抓紅黃行 → 行程級錨點(沒有行號)
function Harvest-Lines([string[]]$Lines, [string]$Source) {
    foreach ($l in @($Lines | Where-Object { $_ -match '\[(RED|YELLOW)\s*\]|^\s*\[FAIL\]|Traceback|Error:|錯誤|失敗' } | Select-Object -First 40)) {
        $cls = if ($l -match '\[RED\s*\]|\[FAIL\]|Traceback|Error:|錯誤|失敗') { "RED" } else { "YELLOW" }
        $m = [regex]::Match($l, '([\w\-\.\\/ ]+\.(py|ps1|json))[:,]?\s*(?:line\s*)?(\d+)')
        if ($m.Success) { Add-Anchor $m.Groups[1].Value $m.Groups[3].Value $cls $l "彈性(regex 從訊息抽檔:行)" $Source }
        else { Add-Anchor "-" "" $cls $l "行程(只有訊息,無行號)" $Source } } }

$py = Get-Py
$V  = Get-Newest $Reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
if (-not $py -or -not $V) { Write-Host "  [via-review] 找不到 python(非 Store 別名)或 VCGC 主控台尾版 CGC_MDL149" -ForegroundColor Red; if ($script:Dotted) { $global:LASTEXITCODE = 1; return } else { exit 1 } }
Write-Host ("=== [via-review v0106] 系統總檢 · VCGC " + $V.Name + " · python " + $py + " ===") -ForegroundColor Cyan
# 進倉(同母倉 via-entry):shell 不在倉內時 git / 正主都會迷路
$keepLoc = Get-Location
Set-Location -LiteralPath $VIA; $env:VIA_ROOT = $VIA; $env:PYTHONUTF8 = "1"
$keepFrom = $env:VIA_FROM_VCGC; $keepConsent = $env:VIA_NET_CONSENT; $keepWarn = $env:PYTHONWARNINGS
$env:VIA_FROM_VCGC = "YES"; $env:PYTHONWARNINGS = "ignore"
if ($Install) { $env:VIA_NET_CONSENT = "YES" }   # -Install = 操作員親手開閘,只在本行程,finally 還原

try {
# ---------------------------------------------------------------- ⓪ 進入環境(正主 via-vcgc enter --card):改為背景車道,與 ②③④⑤ 並行;閘結果在收車道後決定 ⑥⑦ 跑不跑
$enterOut = @(); $enterRc = 3; $enterNote = "-NoEnter 跳過"
# ---------------------------------------------------------------- ① Git 整合檢視(唯讀快)
$t0 = Get-Date
$null = G fetch --quiet
$branch = (G rev-parse --abbrev-ref HEAD | Select-Object -Last 1)
$ab = (G rev-list --left-right --count "HEAD...@{upstream}" | Select-Object -Last 1) -replace '\s+', '/'   # 領先/落後
$por = @(G -c core.quotepath=false status --porcelain -uall)
$conf = @($por | Where-Object { $_ -match '^(UU|AA|DD|AU|UA|DU|UD)' })
$mod  = @($por | Where-Object { $_ -match '^( M|M |MM|A |D | D)' })
$untr = @($por | Where-Object { $_ -match '^\?\?' })
$ledg = @($mod + $untr | Where-Object { $_ -match '_Ledger_v\d{3,4}\.jsonl?$' })
$gitRows = @(
    [pscustomobject]@{ 項目="分支"; 值=$branch }
    [pscustomobject]@{ 項目="領先/落後 upstream"; 值=$ab }
    [pscustomobject]@{ 項目="衝突(UU 等)"; 值=$conf.Count }
    [pscustomobject]@{ 項目="本機改動"; 值=$mod.Count }
    [pscustomobject]@{ 項目="未追蹤"; 值=$untr.Count }
    [pscustomobject]@{ 項目="其中只增寫帳本"; 值=$ledg.Count }
)
foreach ($c in $conf) { Add-Anchor ($c.Substring(3)) "" "GIT_CONFLICT" $c "彈性(git porcelain 狀態碼)" "① git" }
$gitLamp = if ($conf.Count -gt 0) { "RED" } elseif (($ab -match '^\d+/[1-9]') -or $mod.Count -gt 0 -or $untr.Count -gt 0) { "NODATA" } else { "GREEN" }
$gitNote = "領先/落後 " + $ab + " · 衝突 " + $conf.Count + " · 改動 " + $mod.Count + " · 未追蹤 " + $untr.Count
Add-Step "①" "Git 整合檢視(唯讀)" $gitLamp $(if ($gitLamp -eq "RED") { 1 } elseif ($gitLamp -eq "GREEN") { 0 } else { 2 }) ([int]((Get-Date) - $T0).TotalSeconds) $gitNote
$mmLine = ""
if ($Sync) {
    $mm = Invoke-Vcgc @("run", "--family", "core", "CGC_MDL143_MergeMedic", "sync", "--apply") "MERGEMEDIC"
    $mmLine = @($mm.out | Where-Object { $_ -match '拉齊|MergeMedic|merge|分叉|DIVERGED|BEHIND|UP_TO_DATE|AHEAD|衝突|聯集' } | Select-Object -Last 3) -join " | "
    Harvest-Lines $mm.out "①b MergeMedic"
    Add-Step "①b" "拉齊醫生 CGC_MDL143 sync --apply(零 force)" (Lamp $mm.rc) $mm.rc $mm.secs $mmLine
}

# ---------------------------------------------------------------- ②③④⑤ 背景並行車道(直跑 python;每道一個 log)
$Lanes = New-Object System.Collections.Generic.List[object]
function Start-Lane([string]$Id, [string]$Exe, [string]$ArgLine) {
    $lg = Join-Path $OutDir ($Id + "_" + $stamp + ".log"); $er = Join-Path $OutDir ($Id + "_" + $stamp + ".err.log")
    try { $pr = Start-Process -FilePath $Exe -ArgumentList $ArgLine -WorkingDirectory $VIA -NoNewWindow -PassThru -RedirectStandardOutput $lg -RedirectStandardError $er
          $Lanes.Add([pscustomobject]@{ Id=$Id; Proc=$pr; Log=$lg; Err=$er; T0=(Get-Date); TimedOut=$false }) }
    catch { Add-Step $Id ("車道 " + $Id) "RED" 1 0 ("起不來:" + $_.Exception.Message) } }
function Read-Lane([string]$Id) { $l = $Lanes | Where-Object { $_.Id -eq $Id } | Select-Object -First 1; if (-not $l) { return @() }; @(if (Test-Path -LiteralPath $l.Log) { Get-Content -LiteralPath $l.Log -Encoding UTF8 } else { @() }) + @(if (Test-Path -LiteralPath $l.Err) { Get-Content -LiteralPath $l.Err -Encoding UTF8 } else { @() }) }
function Lane-Rc([string]$Id) { $l = $Lanes | Where-Object { $_.Id -eq $Id } | Select-Object -First 1; if (-not $l) { return 3 }; if ($l.TimedOut) { return 124 }; try { $l.Proc.ExitCode } catch { -1 } }
function Lane-Secs([string]$Id) { $l = $Lanes | Where-Object { $_.Id -eq $Id } | Select-Object -First 1; if (-not $l) { return 0 }; try { if ($l.Proc.HasExited) { [int]($l.Proc.ExitTime - $l.T0).TotalSeconds } else { [int]((Get-Date) - $l.T0).TotalSeconds } } catch { 0 } }
$Vq = '"' + $V.FullName + '"'
if (-not $NoEnter) { Start-Lane "ENTER" $py ($Vq + ' enter --card' + $(if ($NoPull) { ' --no-pull' } else { '' })) }
Start-Lane "COLLIDE" $py ($Vq + ' run --family core CGC_MDL165_CommandRunGate collide --json')
Start-Lane "ENV"     $py ($Vq + ' run --family core CGC_MDL240_EnvManager check')
Start-Lane "SDD"     $py ($Vq + ' sdd check')
Start-Lane "SSOT"    $py ($Vq + ' ssot panorama')
Start-Lane "STATUS"  $py ($Vq + ' status')
Start-Lane "CHECK"   $py ($Vq + ' check')
Start-Lane "AUDIT"   $py ($Vq + ' audit')
$tok = $null
try { $tok = Join-Path $Repo ((Get-Content -LiteralPath (Join-Path $Reg "VIA_ToolVersion_Lock_v0100.json") -Raw -Encoding UTF8 | ConvertFrom-Json).token.path) } catch { }
if (-not $tok -or -not (Test-Path -LiteralPath $tok)) { $t = Get-Newest $Reg "CGC_MDL158_VIAPanoramaAuditRepair_v*.py"; if ($t) { $tok = $t.FullName } }
if ($tok) { Start-Lane "PANSCAN" $py ('"' + $tok + '" scan --fast --json'); Start-Lane "PANREAD" $py ('"' + $tok + '" read "functional modules\VDF" "functional modules\VRN" "supportive modules\registry" --json') }
else { Add-Step "⑤" "全景 AST 線" "ABSENT" 3 0 "找不到 CGC_MDL158 鎖冊 token 工具" }
# Python 編譯警告車道(只 compile,不執行、不寫 pyc;SyntaxWarning 檔:行 = AST精準)
$pyc = Join-Path $OutDir ("pycompile_" + $stamp + ".py")
$pySrc = @(
    'import sys, os, json, warnings, io, tokenize',
    'roots = sys.argv[1:]; skip = ("references","intake","_output","runs","test","tests","fixtures","sandbox","__pycache__","_to_delete","archive","backup")',
    'out = []',
    'for root in roots:',
    '    for dp, dn, fn in os.walk(root):',
    '        dn[:] = [d for d in dn if d not in skip]',
    '        for f in fn:',
    '            if not f.endswith(".py"): continue',
    '            p = os.path.join(dp, f)',
    '            try:',
    '                with tokenize.open(p) as fh: src = fh.read()',
    '            except Exception as e:',
    '                out.append({"file": p, "line": 0, "cls": "READ", "msg": str(e)}); continue',
    '            with warnings.catch_warnings(record=True) as w:',
    '                warnings.simplefilter("always")',
    '                try: compile(src, p, "exec")',
    '                except SyntaxError as e: out.append({"file": p, "line": e.lineno or 0, "cls": "SYNTAX", "msg": e.msg})',
    '                for x in w: out.append({"file": p, "line": x.lineno or 0, "cls": x.category.__name__, "msg": str(x.message)})',
    'print(json.dumps({"n": len(out), "rows": out}, ensure_ascii=False))'
) -join "`n"
[IO.File]::WriteAllText($pyc, $pySrc, $Utf8)
Start-Lane "PYCOMPILE" $py ('"' + $pyc + '" "functional modules\VDF" "functional modules\VRN" "supportive modules\registry" "supportive modules\VIA_Central_Governance" "supportive modules\70_VRN_Rules"')

# ---------------------------------------------------------------- ⑨ VIA-VERB-ENGINE 四條車道(v0105;與上面各道並行,同一個看門狗)
$VE = $null; $veNote = ""; $veGlobalHtml = ""; $veFullHtml = ""
if (-not $NoVerb) {
    foreach ($c in @($VerbEngine, $env:VIA_VERB_ENGINE, $(if ($env:USERPROFILE) { Join-Path $env:USERPROFILE 'VIA-VERB-ENGINE\verb-engine' } else { "" }))) {
        if ($c -and (Test-Path -LiteralPath (Join-Path $c 'fullcheck.py'))) { $VE = (Resolve-Path -LiteralPath $c).Path; break }
    }
    if ($VE) {
        $veGit = Split-Path -Parent $VE
        if (-not $NoPull -and (Test-Path -LiteralPath (Join-Path $veGit '.git'))) {
            $pl = @(& git -C $veGit pull --ff-only 2>&1 | ForEach-Object { "" + $_ }); $plRc = $LASTEXITCODE
            $veNote = "快轉 rc " + $plRc + " · " + (@($pl | Select-Object -Last 1) -join "")
            if ($plRc -ne 0) { $Yel.Add("⑨ verb-engine 快轉失敗(不強推;照現有版本檢):" + ($pl -join " | ")) }
        }
        $veLock = Join-Path $OutDir ("velock_" + $stamp + ".py")
        [IO.File]::WriteAllText($veLock, ("import json, sys`nsys.path.insert(0, sys.argv[1])`nfrom engines.VIA_PanoramaCheck import status`nprint(json.dumps(status(), ensure_ascii=False))`n"), $Utf8)
        $veGlobalHtml = Join-Path $OutDir ("VE_GLOBAL_" + $stamp + ".html"); $veFullHtml = Join-Path $OutDir ("VE_FULL_" + $stamp + ".html")
        Start-Lane "VE_HEALTH" $py ('-X utf8 "' + (Join-Path $VE 'health.py') + '"')
        Start-Lane "VE_GLOBAL" $py ('-X utf8 "' + (Join-Path $VE 'global_read.py') + '" --html "' + $veGlobalHtml + '"')
        Start-Lane "VE_FULL"   $py ('-X utf8 "' + (Join-Path $VE 'fullcheck.py') + '" --html "' + $veFullHtml + '"')
        Start-Lane "VE_LOCK"   $py ('-X utf8 "' + $veLock + '" "' + $VE + '"')
    }
}
Write-Host ("  ⓪②③④⑤ " + $Lanes.Count + " 條車道已在背景並行(enter --card · collide · env · sdd · ssot · status · check · audit · pan-scan · pan-read · py-compile)") -ForegroundColor DarkGray

# ---------------------------------------------------------------- ④a 本檔彈性掃描(前景):受控夾 .py 的家族編號 + 是否在 FunctionInventory SSOT 尾版
$t0 = Get-Date
$inv = Get-Newest $Reg "VIA_VCGC_FunctionInventory_SSOT_v*.json"
$regBooks = @(Get-ChildItem -LiteralPath $Reg -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @('.json', '.jsonl', '.md', '.txt') -and $_.Length -lt 50MB })
$invText = ($regBooks | ForEach-Object { try { [IO.File]::ReadAllText($_.FullName) } catch { "" } }) -join "`n"
$ctrl = @("functional modules\VDF", "functional modules\VRN", "supportive modules\registry") | ForEach-Object { Join-Path $VIA $_ } | Where-Object { Test-Path -LiteralPath $_ }
$skipRx = '\\(references|intake|_output|runs|tests?|fixtures|sandbox|__pycache__|_to_delete|archive|backup)\\'
$numRx  = '^(?<fam>[A-Z]{2,5})_(?<kind>MDL|ENG)(?<no>\d{3})_(?<name>\w+?)(_v\d{4})?\.py$'
$regRows = New-Object System.Collections.Generic.List[object]; $gapAnch = 0
foreach ($d in $ctrl) {
    foreach ($f in @(Get-ChildItem -LiteralPath $d -Filter *.py -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch $skipRx })) {
        $m = [regex]::Match($f.Name, $numRx)
        $numbered = $m.Success
        $stem = if ($numbered) { $m.Groups['fam'].Value + "_" + $m.Groups['kind'].Value + $m.Groups['no'].Value + "_" + $m.Groups['name'].Value } else { ($f.BaseName -replace '_v\d{4}$', '') }
        $registered = ($invText.Length -gt 0) -and ($invText.Contains($stem) -or $invText.Contains($f.BaseName))
        $rel = $f.FullName.Substring($VIA.Length).TrimStart('\')
        if (-not $numbered) { if ($gapAnch -lt 200) { Add-Anchor $rel 1 "NO_NUMBER" ("無家族編號(需 XXX_MDL###_ / XXX_ENG###_):" + $f.Name) "彈性(檔名 regex)" "④ 編號" }; $gapAnch++ }
        elseif (-not $registered) { if ($gapAnch -lt 200) { Add-Anchor $rel 1 "NOT_REGISTERED" ("registry 夾 " + $regBooks.Count + " 本冊都沒有:" + $stem) "彈性(registry 全冊字串比對)" "④ 註冊" }; $gapAnch++ }
        $regRows.Add([pscustomobject]@{ 檔=$rel; 家族=$(if ($numbered) { $m.Groups['fam'].Value } else { "-" }); 編號=$(if ($numbered) { $m.Groups['kind'].Value + $m.Groups['no'].Value } else { "無" }); 在冊=$(if ($registered) { "是" } else { "否" }); 燈=$(if ($numbered -and $registered) { "GREEN" } else { "RED" }) })
    }
}
$regRed = @($regRows | Where-Object { $_.燈 -eq "RED" }).Count
$gapCsv = Join-Path $OutDir ("REGISTER_GAPS_" + $stamp + ".csv")
$regRows | Where-Object { $_.燈 -eq "RED" } | Export-Csv -LiteralPath $gapCsv -NoTypeInformation -Encoding UTF8
$regFam = @($regRows | Group-Object 家族 | ForEach-Object { [pscustomobject]@{ 家族=$_.Name; 總數=$_.Count; 無編號=@($_.Group | Where-Object 編號 -eq '無').Count; 未註冊=@($_.Group | Where-Object { $_.編號 -ne '無' -and $_.在冊 -eq '否' }).Count; 燈=$(if (@($_.Group | Where-Object 燈 -eq 'RED').Count) { 'RED' } else { 'GREEN' }) } } | Sort-Object 總數 -Descending)
Add-Step "④a" ("彈性掃描:受控 .py " + $regRows.Count + " 支(無編號 / 未註冊 = 紅)") $(if ($regRed -gt 0) { "RED" } else { "GREEN" }) $(if ($regRed -gt 0) { 1 } else { 0 }) ([int]((Get-Date) - $t0).TotalSeconds) ("紅 " + $regRed + "(錨點只收前 200,全部在 " + (Split-Path $gapCsv -Leaf) + ")· 比對 registry 夾 " + $regBooks.Count + " 本冊")

# ---------------------------------------------------------------- ⑤a PS Parser(前景,精準)
$t0 = Get-Date
$psFiles = @(Get-ChildItem -LiteralPath $VIA -Filter "Invoke-VIA-*.ps1" -File) + @(Get-ChildItem -LiteralPath $VIA -Filter "Register-VIA-Commands-v*.ps1" -File) + @(Get-ChildItem -LiteralPath (Join-Path $VIA "supportive modules") -Filter *.ps1 -File -ErrorAction SilentlyContinue)
$psErr = 0
foreach ($f in $psFiles) {
    $tk = $null; $er = $null
    try { $null = [System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tk, [ref]$er) } catch { $er = @([pscustomobject]@{ Message = $_.Exception.Message; Extent = $null }) }
    foreach ($e in @($er)) { $psErr++; $ln = if ($e.Extent) { $e.Extent.StartLineNumber } else { "" }; Add-Anchor ($f.FullName.Substring($VIA.Length).TrimStart('\')) $ln "PS_SYNTAX" $e.Message $(if ($ln) { "AST精準(PS Parser)" } else { "行程(Parser 例外)" }) "⑤ PS Parser" }
}
Add-Step "⑤a" ("PS Parser 精準定位:" + $psFiles.Count + " 支") $(if ($psErr -gt 0) { "RED" } else { "GREEN" }) $(if ($psErr -gt 0) { 1 } else { 0 }) ([int]((Get-Date) - $t0).TotalSeconds) ("語法錯 " + $psErr)

# ---------------------------------------------------------------- 收車道:看門狗(一條進度列;整體上限 -LaneMaxMin;逾時只停本檔自己的子行程)
$deadline = (Get-Date).AddMinutes($LaneMaxMin)
while ($true) {
    $running = @($Lanes | Where-Object { try { -not $_.Proc.HasExited } catch { $false } })
    if ($running.Count -eq 0) { break }
    $left = [int]($deadline - (Get-Date)).TotalSeconds
    if ($left -le 0) { break }
    $done = $Lanes.Count - $running.Count
    Write-Progress -Id 7 -Activity ("車道 " + $done + "/" + $Lanes.Count + " 完成") -Status ("進行中:" + (($running | ForEach-Object { $_.Id }) -join " ") + " · 看門狗剩 " + [int]($left / 60) + "m" + ($left % 60) + "s") -PercentComplete ([int](100 * $done / [Math]::Max(1, $Lanes.Count)))
    Start-Sleep -Seconds 2
}
Write-Progress -Id 7 -Activity "車道" -Completed
foreach ($l in @($Lanes | Where-Object { try { -not $_.Proc.HasExited } catch { $false } })) {
    try { $l.Proc.Kill(); $l.TimedOut = $true; Write-Host ("  [逾時] 車道 " + $l.Id + " 超過 " + $LaneMaxMin + " 分,已停本檔自己起的子行程(rc 124),其餘照收") -ForegroundColor Yellow } catch { }
    $Yel.Add("車道 " + $l.Id + " 逾時 " + $LaneMaxMin + " 分(TIMEOUT)")
}
# ⓪ enter
if (-not $NoEnter) {
    $enterOut = Read-Lane "ENTER"; $enterRc = Lane-Rc "ENTER"
    Harvest-Lines $enterOut "⓪ enter"
    $enterNote = (@($enterOut | Where-Object { $_ -match '總結|串測|入口 rc|閘' } | Select-Object -Last 1) -join "").Trim()
    Add-Step "⓪" "進入環境 via-vcgc enter --card(位置與更新 · 閘 status · 真載加速器 · 鎖冊六件工具版本 · PS 模板章;不啟動 go)" (Lamp $enterRc) $enterRc (Lane-Secs "ENTER") $enterNote
    if ($enterRc -ne 0) { $Yel.Add("⓪ 進入環境閘沒過(rc " + $enterRc + "):以下各步仍為唯讀診斷,啟動類動作(-Lists / -Optimize)照 VCGC 規定不會跑") }
}
# ② 撞名
$cgOut = Read-Lane "COLLIDE"; $cj = $null
try { $j = ($cgOut -join "`n"); $k = $j.IndexOf('{"state"'); if ($k -lt 0) { $k = $j.IndexOf("{") }; if ($k -ge 0) { $cj = ($j.Substring($k) | ConvertFrom-Json -Depth 32) } } catch { }
$collideNote = if ($cj) { "state " + $cj.state + " · total " + $cj.n_total + " · bad " + $cj.n_bad } else { (@($cgOut | Select-Object -Last 2) -join " | ") }
Harvest-Lines $cgOut "② 撞名閘"
Add-Step "②" "撞名 / 短令閘 CGC_MDL165 collide" $(if ($cj -and $cj.n_bad -gt 0) { "RED" } else { Lamp (Lane-Rc "COLLIDE") }) (Lane-Rc "COLLIDE") (Lane-Secs "COLLIDE") $collideNote
# 政策 / 邏輯庫(VCGC 每次 run 的前置站列)
$polLines = @($cgOut | Where-Object { $_ -match '^\s*\[(政策|位階|衝突|不衝突|靜態|分群|還原|環境計畫|加速|同步|流程)\]' } | ForEach-Object { $_.Trim() } | Select-Object -Unique)
$polRows = @($polLines | ForEach-Object { $m = [regex]::Match($_, '^\[(.+?)\]\s*(.*)$'); [pscustomobject]@{ 站=$m.Groups[1].Value; 燈=$(if ($_ -match 'RED|不可鎖定') { "RED" } elseif ($_ -match '通過|GREEN|不衝突|政策過') { "GREEN" } else { "INFO" }); 內容=$m.Groups[2].Value } })
Add-Step "②p" "政策 / 邏輯庫(律 · lessons · 位階 · 衝突 · 靜態 · 還原)" $(if (@($polRows | Where-Object 燈 -eq 'RED').Count -gt 0) { "NODATA" } else { "GREEN" }) 0 0 ("站列 " + $polRows.Count + " · 紅 " + @($polRows | Where-Object 燈 -eq 'RED').Count)
# ③ 環境
$envJson = Join-Path $Rep "env_manager\ENVMGR_latest.json"
$e1 = @{ out = (Read-Lane "ENV"); rc = (Lane-Rc "ENV"); secs = (Lane-Secs "ENV") }
$envBefore = "NODATA"; try { $envBefore = (Get-Content -LiteralPath $envJson -Raw -Encoding UTF8 | ConvertFrom-Json).verdict } catch { }
$envAfter = $envBefore; $installLine = ""
Harvest-Lines $e1.out "③ ENV check"
if ($envBefore -ne "GREEN") {
    if ($Install) {
        Write-Host "  ③ 環境完整安裝 ① 工具冊順序安裝(CGC_MDL135 tools --apply --approve)…" -ForegroundColor Cyan
        $i1 = Invoke-Vcgc @("run", "--family", "core", "CGC_MDL135_EnvGovernance", "tools", "--apply", "--approve") "INSTALL_TOOLS"
        Write-Host "  ③ 環境完整安裝 ② 鏈上缺件裝進家族境(CGC_MDL137 run --family vdf,vrn --approve-install)…" -ForegroundColor Cyan
        $i2 = Invoke-Vcgc @("run", "--family", "core", "CGC_MDL137_RunGate", "run", "--family", "vdf,vrn", "--approve-install") "INSTALL_CHAIN"
        $null = Invoke-Vcgc @("run", "--family", "core", "CGC_MDL240_EnvManager", "check") "ENVCHECK_AFTER"
        $envAfter = "NODATA"; try { $envAfter = (Get-Content -LiteralPath $envJson -Raw -Encoding UTF8 | ConvertFrom-Json).verdict } catch { }
        Harvest-Lines ($i1.out + $i2.out) "③ 安裝"
        $installLine = "ENV " + $envBefore + " → " + $envAfter + " · 工具冊 rc " + $i1.rc + " · 家族境 rc " + $i2.rc
        Add-Step "③b" "環境補安裝(MDL135 → MDL137 → 再 check)" $(if ($envAfter -eq "GREEN") { "GREEN" } elseif ($i1.rc -eq 1 -or $i2.rc -eq 1) { "RED" } else { "NODATA" }) ($i1.rc + $i2.rc) ($i1.secs + $i2.secs) $installLine
    } else { $installLine = "ENV " + $envBefore + " · 未帶 -Install:只列不裝(帶 -Install = 你親手開閘)" }
}
Add-Step "③" "環境 CGC_MDL240 EnvManager check" $(if ($envBefore -eq "GREEN") { "GREEN" } elseif ($envBefore -eq "NODATA") { "NODATA" } else { "RED" }) $e1.rc $e1.secs ("總判 " + $envBefore + $(if ($installLine) { " · " + $installLine } else { "" }))
# ④ SDD(WORKFLOW 檢視)· SSOT(參數 regex 同義字 編號 命名 註冊 上下連結)· MAIN(status check audit)
$ssotCat = [ordered]@{ "參數"='參數|param'; "regex"='regex|正則|樣式'; "同義字"='同義|synonym|別名'; "編號"='編號|number|MDL\d|ENG\d'; "命名"='命名|naming|檔名'; "註冊"='註冊|register|登錄|在冊'; "上下連結"='連結|link|上下|下放'; "政策"='政策|policy|律'; "邏輯"='邏輯|logic|工作流|步' }
$ssotRows = New-Object System.Collections.Generic.List[object]
foreach ($id in @("SDD", "SSOT", "STATUS", "CHECK", "AUDIT")) {
    $txt = Read-Lane $id
    $reds = @($txt | Where-Object { $_ -match '\[RED\s*\]' }); $yels = @($txt | Where-Object { $_ -match '\[YELLOW\s*\]|\[AMBER\s*\]' })
    foreach ($l in $reds) { Add-Anchor "-" "" ("VCGC_" + $id) $l.Trim() "行程(VCGC 站列)" ("④ " + $id) }
    foreach ($l in @($txt | Where-Object { $_ -match '\[(RED|YELLOW|AMBER|GREEN)\s*\]' })) {
        $lamp = if ($l -match '\[RED') { "RED" } elseif ($l -match '\[GREEN') { "GREEN" } else { "YELLOW" }
        $cats = @($ssotCat.Keys | Where-Object { $l -match $ssotCat[$_] }); if ($cats.Count -eq 0) { $cats = @("其他") }
        foreach ($c in $cats) { $ssotRows.Add([pscustomobject]@{ 檢視=$id; 類別=$c; 燈=$lamp; 站列=$l.Trim() }) } }
    $tot = @($txt | Where-Object { $_ -match '總判|VERDICT|整體' } | Select-Object -Last 1) -join ""
    $title = switch ($id) { "SDD" { "WORKFLOW 檢視 sdd check(工作流冊:步 · 碼 · 需求回指 · 鎖尾版)" } "SSOT" { "SSOT 檢視 ssot panorama(參數 · regex · 同義字 · 編號 · 命名 · 註冊 · 上下連結)" } default { "MAIN 檢視 " + $id.ToLower() } }
    Add-Step ("④" + $id) $title $(if ($reds.Count -gt 0) { "RED" } elseif ($yels.Count -gt 0) { "NODATA" } elseif ((Lane-Rc $id) -eq 0) { "GREEN" } else { Lamp (Lane-Rc $id) }) (Lane-Rc $id) (Lane-Secs $id) ("紅 " + $reds.Count + " · 黃 " + $yels.Count + $(if ($tot) { " · " + $tot.Trim() } else { "" }))
}
$ssotMatrix = @(foreach ($c in @($ssotCat.Keys) + @("其他")) { $r = @($ssotRows | Where-Object 類別 -eq $c); [pscustomobject]@{ 類別=$c; 紅=@($r | Where-Object 燈 -eq 'RED').Count; 黃=@($r | Where-Object 燈 -eq 'YELLOW').Count; 綠=@($r | Where-Object 燈 -eq 'GREEN').Count; 燈=$(if (@($r | Where-Object 燈 -eq 'RED').Count) { "RED" } elseif (@($r | Where-Object 燈 -eq 'YELLOW').Count) { "YELLOW" } elseif ($r.Count) { "GREEN" } else { "INFO" }) } })
# ⑤ PAN + PY compile
$severe = @("SYNTAX", "COMPILE", "TALIB"); $sevN = 0; $panN = 0
$panScan = ($Lanes | Where-Object Id -eq "PANSCAN" | Select-Object -First 1).Log; $panRead = ($Lanes | Where-Object Id -eq "PANREAD" | Select-Object -First 1).Log
$sj = if ($panScan) { Read-JsonTail $panScan } else { $null }
if ($sj) { foreach ($r in @($sj.rows | Where-Object { -not $_.exempt })) { $panN++; if ($severe -contains ("" + $r.cls)) { $sevN++ }; Add-Anchor ("" + $r.file) $r.line ("治理:" + $r.cls) ("" + $r.detail) "AST精準(PAN-SCAN)" "⑤ PAN-SCAN" } }
$rj = if ($panRead) { Read-JsonTail $panRead } else { $null }
if ($rj) { foreach ($c in @($rj.cards)) { $rel = ("" + $c.path); if ($rel.StartsWith($VIA)) { $rel = $rel.Substring($VIA.Length).TrimStart('\', '/') }; foreach ($is in @($c.issues)) { if (-not $is) { continue }; $panN++; if ($severe -contains ("" + $is.cls)) { $sevN++ }; Add-Anchor $rel $is.line ("AST:" + $is.cls) ("" + $is.detail) "AST精準(PAN-READ)" "⑤ PAN-READ" } } }
if ($tok) { Add-Step "⑤" ("全景 AST 錨點(PAN-SCAN " + $(if ($sj) { $sj.files_scanned } else { "?" }) + " 檔 · PAN-READ " + $(if ($rj) { $rj.files } else { "?" }) + " 檔)") $(if (-not $sj -or -not $rj) { "RED" } elseif ($sevN -gt 0) { "RED" } elseif ($panN -gt 0) { "NODATA" } else { "GREEN" }) $(if (-not $sj -or -not $rj) { 1 } elseif ($sevN -gt 0) { 1 } elseif ($panN -gt 0) { 2 } else { 0 }) ([Math]::Max((Lane-Secs "PANSCAN"), (Lane-Secs "PANREAD"))) ("錨點 " + $panN + " · 嚴重(SYNTAX/COMPILE/TALIB) " + $sevN + $(if (-not $sj -or -not $rj) { " · 有線沒產出 JSON(看 review\PAN*.err.log)" } else { "" })) }
$pjLane = $Lanes | Where-Object Id -eq "PYCOMPILE" | Select-Object -First 1; $pj = if ($pjLane) { Read-JsonTail $pjLane.Log } else { $null }; $pyWarn = 0; $pySyn = 0
if ($pj) { foreach ($r in @($pj.rows)) { $rel = ("" + $r.file); if ($rel.StartsWith($VIA)) { $rel = $rel.Substring($VIA.Length).TrimStart('\', '/') }; if ($r.cls -eq "SYNTAX") { $pySyn++ } else { $pyWarn++ }; Add-Anchor $rel $r.line ("PY_" + $r.cls) ("" + $r.msg) "AST精準(Python compile)" "⑤ PY compile" } }
Add-Step "⑤b" "Python 編譯警告(只 compile 不執行;SyntaxWarning 無效跳脫等)" $(if (-not $pj) { "RED" } elseif ($pySyn -gt 0) { "RED" } elseif ($pyWarn -gt 0) { "NODATA" } else { "GREEN" }) (Lane-Rc "PYCOMPILE") (Lane-Secs "PYCOMPILE") $(if ($pj) { '語法錯 ' + $pySyn + ' · 警告 ' + $pyWarn + '(多為 docstring 內 \d \. \( 未 raw 化;改 r"""…""" 或 \\)' } else { '車道沒產出 JSON(看 review\PYCOMPILE_*.err.log)' })

# ⑨ VIA-VERB-ENGINE 判讀(v0105)
$veRows = New-Object System.Collections.Generic.List[object]
if ($NoVerb) { Add-Step "⑨" "VIA-VERB-ENGINE(-NoVerb 略過)" "INFO" 0 0 "" }
elseif (-not $VE) { Add-Step "⑨" "VIA-VERB-ENGINE 五支入口" "ABSENT" 3 0 "找不到 verb-engine(設 -VerbEngine <夾> 或 VIA_VERB_ENGINE;預設 %USERPROFILE%\VIA-VERB-ENGINE\verb-engine)" }
else {
    $veParts = @(
        @{ Id = "VE_HEALTH"; No = "⑨a"; Name = "verb-engine 健康檢查 health.py(治理冊站點)"; Html = "" },
        @{ Id = "VE_GLOBAL"; No = "⑨b"; Name = "verb-engine 只讀全景 global_read.py(GitHub HEAD)"; Html = $veGlobalHtml },
        @{ Id = "VE_FULL";   No = "⑨c"; Name = "verb-engine 七段全檢 fullcheck.py"; Html = $veFullHtml },
        @{ Id = "VE_LOCK";   No = "⑨d"; Name = "verb-engine 收尾鎖 VIA_PanoramaCheck.status()"; Html = "" })
    foreach ($p in $veParts) {
        $ln = $Lanes | Where-Object { $_.Id -eq $p.Id } | Select-Object -First 1
        $j = if ($ln) { Read-JsonTail $ln.Log } else { $null }
        $rc = Lane-Rc $p.Id
        $lamp = "RED"
        if ($rc -eq 124) { $lamp = "TIMEOUT" }
        elseif ($rc -ne 0 -or -not $j) { $lamp = "RED" }
        elseif ($p.Id -eq "VE_LOCK") { $lamp = $(if ($j.locked -eq $true) { "GREEN" } else { "RED" }) }
        elseif ($j.lamp -eq "GREEN") { $lamp = "GREEN" }
        elseif ($j.lamp -eq "RED") { $lamp = "RED" }
        else { $lamp = "NODATA" }
        $note = ""
        if (-not $j) { $note = (@(Read-Lane $p.Id | Select-Object -Last 2) -join " | ") }
        elseif ($p.Id -eq "VE_HEALTH") { $note = "站 " + $j.stations + " · 紅 " + $j.red + " · 黃 " + $j.amber + " · 綠 " + $j.green }
        elseif ($p.Id -eq "VE_GLOBAL") { $note = "燈 " + $j.lamp + " · 檔 " + $j.files + " · GitHub " + $j.commit }
        elseif ($p.Id -eq "VE_LOCK") { $note = "鎖 " + $j.locked + " · 隔離 " + $j.quarantine + " · 註冊 " + $j.registered }
        else { $note = "燈 " + $j.lamp }
        $detail = New-Object System.Collections.Generic.List[string]
        if ($p.Id -eq "VE_HEALTH" -and $j -and $j.rows) { foreach ($r in @($j.rows | Where-Object { $_.level -ne "GREEN" })) { $detail.Add($r.id + " " + $r.level + " " + $r.detail) } }
        if ($p.Html -and (Test-Path -LiteralPath $p.Html)) {
            $h = Get-Content -LiteralPath $p.Html -Raw -Encoding UTF8
            foreach ($m in [regex]::Matches($h, "<tr><td>([^<]+)</td><td class='(AMBER|RED|YELLOW)'>[^<]*</td><td>([^<]*)</td></tr>")) { $detail.Add($m.Groups[1].Value + " " + $m.Groups[2].Value + " " + [System.Net.WebUtility]::HtmlDecode($m.Groups[3].Value)) }
        }
        if ($detail.Count -gt 0) { $note += " · " + ((@($detail) | Select-Object -First 3) -join " ; ") }
        if ($p.Id -eq "VE_HEALTH" -and $veNote) { $note += " · " + $veNote }
        Add-Step $p.No $p.Name $lamp $rc (Lane-Secs $p.Id) $note
        $veRows.Add([pscustomobject]@{ 站 = $p.No; 檢查 = $p.Name; 燈 = $lamp; rc = $rc; 摘要 = $note; 報告 = $(if ($p.Html -and (Test-Path -LiteralPath $p.Html)) { $p.Html } else { "-" }); 明細 = (@($detail) -join "`n") })
    }
}

# ---------------------------------------------------------------- ⑥ 清單七步(-Lists;v0108 ① 原表,經 VCGC)
if ($Lists -and $enterRc -eq 0) {
    $dryArg = @(if ($Dry) { "--dry" })
    $plan = @(
        @{ n = "台股上市櫃公司清單";       a = @("run", "CGC_MDL139_InputConsole", "run", "--item", "macro_lanes", "lanes=L1") + $dryArg; dryOk = $true },
        @{ n = "主動式台股 ETF 總清單";     a = @("run", "CGC_MDL139_InputConsole", "run", "--item", "etf_universe") + $dryArg; dryOk = $true },
        @{ n = "主動 ETF 每日持股(驗證)";  a = @("run", "CGC_MDL139_InputConsole", "run", "--item", "etf_holdings_daily") + $dryArg; dryOk = $true },
        @{ n = "主動 ETF 名碼官方定奪";     a = @("run", "FLOW_ENG023_FlowTwActiveEtf", "--refresh"); dryOk = $false },
        @{ n = "股票日快照";               a = @("run", "CGC_MDL139_InputConsole", "run", "--item", "tw_universe_update") + $dryArg; dryOk = $true },
        @{ n = "台股清單 新上市 / 下市";    a = @("run", "--family", "vdf", "VDF_ENG087_MarketListGovernance", "diff") + $dryArg; dryOk = $true },
        @{ n = "每日兩張清單檔";            a = @("run", "--family", "vdf", "VDF_ENG231_GlobalListings", "lists"); dryOk = $false }
    )
    $i = 0
    foreach ($s in $plan) { $i++
        if ($Dry -and -not $s.dryOk) { Add-Step ("⑥." + $i) $s.n "INFO" "-" 0 "SKIP(-Dry 本步沒有乾跑)"; continue }
        $r = Invoke-Vcgc $s.a ("LIST" + $i)
        Harvest-Lines $r.out ("⑥." + $i + " " + $s.n)
        Add-Step ("⑥." + $i) $s.n (Lamp $r.rc) $r.rc $r.secs (@($r.out | Select-Object -Last 1) -join "")
    }
}

# ---------------------------------------------------------------- ⑦ 全部優化一回(-Optimize → RealTestCore 尾版,不複製)
if ($Optimize -and $enterRc -eq 0) {
    $core = Get-Newest $VIA "Invoke-VIA-RealTestCore-v*.ps1"
    if ($core) {
        $t0 = Get-Date
        Write-Host ("  ⑦ 全部優化一回 → " + $core.Name + "(25 加速器 · VDF ∥ VRN · 覆蓋 · 全景 + 三合一)") -ForegroundColor Cyan
        & $core.FullName -NoOpen:$NoOpen -StallSec 120 -MaxMin 20
        $rc7 = $LASTEXITCODE
        Add-Step "⑦" ("全部優化一回 " + $core.Name) $(if ($rc7 -eq 0) { "GREEN" } elseif ($rc7 -eq 2) { "NODATA" } else { "RED" }) $rc7 ([int]((Get-Date) - $t0).TotalSeconds) ("rc " + $rc7 + "(0 全綠 · 2 有發現 · 1 紅 · 124 超時)")
        $rtAnch = Join-Path $Rep "realtest\AST_ANCHORS_latest.txt"
        if (Test-Path -LiteralPath $rtAnch) { foreach ($l in @(Get-Content -LiteralPath $rtAnch -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith("#") } | Select-Object -First 400)) { $m = [regex]::Match($l, '^(.+?):(\d*)\s+(\S+)\s+(.*)$'); if ($m.Success) { Add-Anchor $m.Groups[1].Value $m.Groups[2].Value $m.Groups[3].Value $m.Groups[4].Value "AST精準(realtest 全景)" "⑦ RealTest" } } }
    } else { Add-Step "⑦" "全部優化一回" "ABSENT" 3 0 "Invoke-VIA-RealTestCore-v*.ps1 不在(先 git pull)" }
}

}
finally { $env:VIA_FROM_VCGC = $keepFrom; $env:VIA_NET_CONSENT = $keepConsent; $env:PYTHONWARNINGS = $keepWarn; try { Set-Location $keepLoc } catch { } }

# ---------------------------------------------------------------- ⑧ 錨點全文 · 貼回包 · 多頁矩陣 HTML
$anchorFile = Join-Path $OutDir ("ANCHORS_" + $stamp + ".txt")
$anchLines = @("# via-review 錨點 · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " · 共 " + $Anch.Count + "(檔:行  類  定位  說明;一個不漏)") + @($Anch | Sort-Object 檔, 行 | ForEach-Object { "{0}:{1}  {2}  [{3}]  {4}" -f $_.檔, $_.行, $_.類, $_.定位, $_.說明 })
$anchLines | Set-Content -LiteralPath $anchorFile -Encoding UTF8
Copy-Item -LiteralPath $anchorFile -Destination (Join-Path $OutDir "ANCHORS_latest.txt") -Force
$locStat = @($Anch | Group-Object 定位 | ForEach-Object { [pscustomobject]@{ 定位種類=$_.Name; 數=$_.Count } })
$final = if ($Red.Count -gt 0) { 1 } elseif ($Yel.Count -gt 0) { 2 } else { 0 }
$secsAll = [int]((Get-Date) - $T0).TotalSeconds
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# via-review " + $stamp + " · 結束碼 " + $final + " · " + $secsAll + "s · 分支 " + $branch + " · 領先/落後 " + $ab)
$md.Add("## 步驟燈號"); foreach ($s in $Steps) { $md.Add("- [" + $s.Lamp + "] " + $s.No + " " + $s.Step + " · rc " + $s.Rc + " · " + $s.Secs + "s" + $(if ($s.Note) { " · " + $s.Note } else { "" })) }
$md.Add("## 紅字(" + $Red.Count + ")"); foreach ($r in $Red) { $md.Add("- " + $r) }
$md.Add("## 黃字(" + $Yel.Count + ")"); foreach ($y in $Yel) { $md.Add("- " + $y) }
$md.Add("## 錨點(" + $Anch.Count + ";定位種類:" + (($locStat | ForEach-Object { $_.定位種類 + " " + $_.數 }) -join " · ") + ")")
foreach ($l in @($anchLines | Select-Object -Skip 1 -First 120)) { $md.Add("- " + $l) }
if ($Anch.Count -gt 120) { $md.Add("- …其餘見 " + $anchorFile) }
$mdPath = Join-Path $OutDir ("REVIEW_" + $stamp + ".md")
[IO.File]::WriteAllText($mdPath, (($md -join "`n") + "`n"), $Utf8)
Copy-Item -LiteralPath $mdPath -Destination (Join-Path $OutDir "REVIEW_latest.md") -Force
# v0106:剪貼簿改放唯一頁的貼回包(下面 ⑧ 唯一頁之後才放)

# 多頁矩陣 HTML(自含;不依賴任何模組)
$enc = [System.Net.WebUtility]
function HtmlEnc([object]$v) { $enc::HtmlEncode("" + $v) }
function Tbl([object[]]$rows, [string[]]$cols) {
    if (-not $rows -or $rows.Count -eq 0) { return "<p class='dim'>(無資料)</p>" }
    if (-not $cols) { $cols = @($rows[0].PSObject.Properties.Name) }
    $sb = [System.Text.StringBuilder]::new(); $null = $sb.Append("<div class='wrap'><table><tr>"); foreach ($c in $cols) { $null = $sb.Append("<th>" + (HtmlEnc $c) + "</th>") }; $null = $sb.Append("</tr>")
    foreach ($r in $rows) { $null = $sb.Append("<tr>"); foreach ($c in $cols) { $v = "" + $r.$c; $cls = if ($v -match '^(GREEN|RED|NODATA|GATE|ABSENT|INFO|YELLOW|是|否)$') { " class='" + $v + "'" } else { "" }; $null = $sb.Append("<td" + $cls + ">" + (HtmlEnc $v) + "</td>") }; $null = $sb.Append("</tr>") }
    $null = $sb.Append("</table></div>"); $sb.ToString() }
$css = "body{margin:0;font-family:'Segoe UI','Microsoft JhengHei';background:#0b1220;color:#e5e7eb;font-size:13px}header{padding:12px 20px;background:#111827;border-bottom:1px solid #334155}h1{margin:0;font-size:18px;color:#93c5fd}nav{display:flex;flex-wrap:wrap;gap:6px;padding:8px 20px;background:#0f172a;position:sticky;top:0}nav button{background:#1e293b;color:#cbd5e1;border:1px solid #334155;padding:5px 12px;border-radius:6px;cursor:pointer}nav button.on{background:#2563eb;color:#fff}section{display:none;padding:12px 20px}section.on{display:block}h2{color:#93c5fd;font-size:15px;margin:14px 0 6px}table{border-collapse:collapse;margin:4px 0 12px;font-size:12px}td,th{border:1px solid #334155;padding:4px 8px;vertical-align:top}th{background:#1e293b;position:sticky;top:40px}tr:nth-child(even){background:#0f172a}.GREEN,.是{color:#4ade80;font-weight:600}.RED,.否{color:#f87171;font-weight:600}.NODATA,.GATE,.ABSENT,.YELLOW{color:#fbbf24}.INFO{color:#64748b}.dim{color:#64748b}pre{background:#111827;padding:8px;overflow:auto;font-size:11px}.wrap{overflow-x:auto}.big{font-size:22px;font-weight:700}"
$js = 'function go(i){document.querySelectorAll("nav button").forEach((b,k)=>b.classList.toggle("on",k===i));document.querySelectorAll("section").forEach((s,k)=>s.classList.toggle("on",k===i));}document.addEventListener("DOMContentLoaded",()=>go(0));'
$overview = @(
    [pscustomobject]@{ 項目="總判"; 值=$(if ($final -eq 0) { "GREEN" } elseif ($final -eq 2) { "YELLOW" } else { "RED" }) }
    [pscustomobject]@{ 項目="紅字 / 黃字"; 值=("" + $Red.Count + " / " + $Yel.Count) }
    [pscustomobject]@{ 項目="錨點"; 值=("" + $Anch.Count + "(" + (($locStat | ForEach-Object { $_.定位種類 + " " + $_.數 }) -join " · ") + ")") }
    [pscustomobject]@{ 項目="進入環境 enter --card"; 值=("rc " + $enterRc + " · " + $enterNote) }
    [pscustomobject]@{ 項目="Git"; 值=$gitNote + $(if ($mmLine) { " · " + $mmLine } else { "" }) }
    [pscustomobject]@{ 項目="環境"; 值=("總判 " + $envBefore + $(if ($installLine) { " · " + $installLine } else { "" })) }
    [pscustomobject]@{ 項目="受控 .py 無編號 / 未註冊"; 值=("" + $regRed + " / " + $regRows.Count) }
    [pscustomobject]@{ 項目="全景 AST 嚴重"; 值=("" + $sevN + "(SYNTAX / COMPILE / TALIB)") }
    [pscustomobject]@{ 項目="SSOT 矩陣(紅/黃/綠)"; 值=(("" + @($ssotRows | Where-Object 燈 -eq 'RED').Count) + " / " + @($ssotRows | Where-Object 燈 -eq 'YELLOW').Count + " / " + @($ssotRows | Where-Object 燈 -eq 'GREEN').Count) }
    [pscustomobject]@{ 項目="Python 編譯"; 值=("語法錯 " + $pySyn + " · 警告 " + $pyWarn) }
    [pscustomobject]@{ 項目="VIA-VERB-ENGINE"; 值=$(if ($NoVerb) { "略過(-NoVerb)" } elseif (-not $VE) { "ABSENT(找不到 verb-engine)" } else { $VE + " · " + ((@($veRows) | ForEach-Object { $_.站 + " " + $_.燈 }) -join " · ") }) }
    [pscustomobject]@{ 項目="耗時"; 值=("" + $secsAll + "s") }
    [pscustomobject]@{ 項目="貼回包"; 值=$mdPath }
)
$pages = [ordered]@{
    "總覽"            = (Tbl $overview) + "<h2>步驟燈號</h2>" + (Tbl @($Steps))
    "進入環境"        = "<p class='big " + $(if ($enterRc -eq 0) { 'GREEN' } elseif ($enterRc -eq 3) { 'INFO' } else { 'RED' }) + "'>enter --card rc " + $enterRc + "</p><p>正主 via-vcgc enter:位置與更新(只快轉)→ 閘 status → 真載加速器 activate() → 鎖冊六件工具版本(加速器 · 網路 · layout · nlp · token · frame)→ PS 模板章;--card 只出卡不啟動 go。</p><pre>" + (HtmlEnc ((@($enterOut | Select-Object -Last 100)) -join "`n")) + "</pre>"
    "Git 整合"        = (Tbl $gitRows) + "<h2>衝突</h2>" + (Tbl @($conf | ForEach-Object { [pscustomobject]@{ 狀態=$_.Substring(0,2); 檔=$_.Substring(3) } })) + "<h2>本機改動 / 未追蹤(前 80)</h2>" + (Tbl @(($mod + $untr) | Select-Object -First 80 | ForEach-Object { [pscustomobject]@{ 狀態=$_.Substring(0,2); 檔=$_.Substring(3) } }))
    "環境"            = "<p class='big " + $(if ($envBefore -eq 'GREEN') { 'GREEN' } else { 'RED' }) + "'>ENV " + (HtmlEnc $envBefore) + $(if ($installLine) { " → " + (HtmlEnc $envAfter) } else { "" }) + "</p><pre>" + (HtmlEnc ((@($e1.out | Select-Object -Last 60)) -join "`n")) + "</pre>"
    "編號 / 註冊"     = "<p>規則:受控夾 .py 檔名需 XXX_MDL###_ 或 XXX_ENG###_,且字根(或帶版號檔名)要出現在 registry 夾任一本冊(json / jsonl / md / txt,共 " + $regBooks.Count + " 本);缺一即紅。逐支明細:" + (HtmlEnc $gapCsv) + "</p><h2>按家族</h2>" + (Tbl @($regFam)) + "<h2>紅燈明細(前 300)</h2>" + (Tbl @($regRows | Where-Object 燈 -eq 'RED' | Sort-Object 家族, 檔 | Select-Object -First 300))
    "AST 錨點"        = "<p>定位種類:<b>AST精準</b> = 檔:行 來自 AST(PAN-SCAN / PAN-READ / PS Parser)· <b>彈性</b> = 檔:行 來自 regex / 檔名 / git 狀態 · <b>行程</b> = 只有訊息沒有行號(正主站列)。</p>" + (Tbl @($locStat)) + (Tbl @($Anch | Sort-Object 檔, 行))
    "SSOT 矩陣"       = "<p>ssot panorama / sdd check / status / check / audit 的站列依類別歸位(一行可屬多類);紅黃綠來自 VCGC 自己的燈。</p>" + (Tbl @($ssotMatrix)) + "<h2>站列明細</h2>" + (Tbl @($ssotRows | Sort-Object 燈, 類別))
    "政策 / 邏輯庫"   = "<p>VCGC 每次 run 前置:律 · lessons · 位階 · 衝突 / 不衝突 · 靜態 · 還原點 · 環境計畫 · 加速(唯讀站列)。</p>" + (Tbl @($polRows))
    "WORKFLOW 檢視"   = "<pre>" + (HtmlEnc ((@(Read-Lane "SDD" | Select-Object -Last 120)) -join "`n")) + "</pre>"
    "MAIN 檢視"       = "<h2>status</h2><pre>" + (HtmlEnc ((@(Read-Lane "STATUS" | Select-Object -Last 60)) -join "`n")) + "</pre><h2>check</h2><pre>" + (HtmlEnc ((@(Read-Lane "CHECK" | Select-Object -Last 60)) -join "`n")) + "</pre><h2>audit</h2><pre>" + (HtmlEnc ((@(Read-Lane "AUDIT" | Select-Object -Last 60)) -join "`n")) + "</pre>"
    "VERB-ENGINE"     = "<p>VIA-VERB-ENGINE 五支入口併進同一輪(health · global_read · fullcheck · 收尾鎖;PanoramaCloseout 由 ① + ⑨c 涵蓋)。引擎:" + (HtmlEnc $(if ($VE) { $VE } else { '找不到' })) + "</p>" + (Tbl @($veRows | Select-Object 站, 檢查, 燈, rc, 摘要, 報告)) + "<h2>非綠明細</h2><pre>" + (HtmlEnc ((@($veRows) | Where-Object { $_.明細 } | ForEach-Object { '[' + $_.站 + '] ' + $_.明細 }) -join "`n")) + "</pre>"
    "步驟燈號"        = (Tbl @($Steps))
    "紅黃全文"        = "<h2>紅字</h2><pre>" + (HtmlEnc ($Red -join "`n")) + "</pre><h2>黃字</h2><pre>" + (HtmlEnc ($Yel -join "`n")) + "</pre>"
}
# ---------------------------------------------------------------- ⑧ 唯一頁(v0106):原每一頁的資料 → CGC_MDL254 併進同一頁
function To-Rows($x) { @($x | ForEach-Object { if ($_ -is [string]) { [pscustomobject]@{ 值 = $_ } } else { $_ } }) }
$review = [ordered]@{
    stamp = $stamp; final = $final; branch = $branch
    overview = @($overview); steps = @($Steps); red = @($Red); yellow = @($Yel)
    anchors = @($Anch | Sort-Object 檔, 行 | Select-Object -First 2000)
    sections = [ordered]@{
        "進入環境(enter --card rc $enterRc)" = ((@($enterOut | Select-Object -Last 100)) -join "`n")
        "Git 整合" = [ordered]@{ "總表" = @(To-Rows $gitRows); "衝突" = @($conf | ForEach-Object { [pscustomobject]@{ 狀態 = $_.Substring(0, 2); 檔 = $_.Substring(3) } }); "本機改動 / 未追蹤(前 80)" = @(($mod + $untr) | Select-Object -First 80 | ForEach-Object { [pscustomobject]@{ 狀態 = $_.Substring(0, 2); 檔 = $_.Substring(3) } }) }
        "環境(ENV $envBefore$(if ($installLine) { ' → ' + $envAfter } else { '' }))" = ((@($e1.out | Select-Object -Last 60)) -join "`n")
        "編號 / 註冊(冊 $($regBooks.Count) 本 · 明細 $gapCsv)" = [ordered]@{ "按家族" = @(To-Rows $regFam); "紅燈明細(前 300)" = @($regRows | Where-Object 燈 -eq 'RED' | Sort-Object 家族, 檔 | Select-Object -First 300) }
        "AST 錨點定位種類" = @(To-Rows $locStat)
        "SSOT 矩陣" = [ordered]@{ "矩陣" = @(To-Rows $ssotMatrix); "站列明細" = @($ssotRows | Sort-Object 燈, 類別) }
        "政策 / 邏輯庫" = @(To-Rows $polRows)
        "WORKFLOW 檢視" = ((@(Read-Lane "SDD" | Select-Object -Last 120)) -join "`n")
        "MAIN 檢視" = [ordered]@{ "status" = ((@(Read-Lane "STATUS" | Select-Object -Last 60)) -join "`n"); "check" = ((@(Read-Lane "CHECK" | Select-Object -Last 60)) -join "`n"); "audit" = ((@(Read-Lane "AUDIT" | Select-Object -Last 60)) -join "`n") }
        "VIA-VERB-ENGINE" = @($veRows | Select-Object 站, 檢查, 燈, rc, 摘要, 報告, 明細)
    }
}
$revJson = Join-Path $OutDir ("REVIEW_" + $stamp + ".json")
$onePage = Join-Path $Rep "review\ONEPAGE_latest.html"
$oneMd = Join-Path $Rep "review\ONEPAGE_latest.md"
$oneOk = $false
try {
    [IO.File]::WriteAllText($revJson, ($review | ConvertTo-Json -Depth 8 -Compress), $Utf8)
    $keepFrom1 = $env:VIA_FROM_VCGC; $env:VIA_FROM_VCGC = "YES"
    try { $op = Invoke-Vcgc @("run", "CGC_MDL254_ReviewOnePage", "build", "--review", $revJson, "--no-open") "ONEPAGE" }
    finally { $env:VIA_FROM_VCGC = $keepFrom1 }
    $oneOk = (Test-Path -LiteralPath $onePage) -and ((Get-Item -LiteralPath $onePage).LastWriteTime -ge $T0)
    foreach ($l in @($op.out | Where-Object { $_ -match '^\[唯一頁\]|^\s+\[(下一步|衝突|頁)\]' } | Select-Object -First 14)) { Write-Host ("  " + $l.Trim()) -ForegroundColor $(if ($l -match '衝突') { 'Yellow' } else { 'Cyan' }) }
} catch { Write-Host ("  [唯一頁] 沒出成(" + $_.Exception.Message + ")→ 退回多頁") -ForegroundColor Yellow }
if ($oneOk) {
    if (-not $NoClipboard) { try { Get-Content -LiteralPath $oneMd -Raw -Encoding UTF8 | Set-Clipboard; Write-Host "  唯一頁貼回包已放進剪貼簿(Ctrl+V 貼給 AI)" -ForegroundColor Yellow } catch { } }
    if (-not $NoOpen) { try { $psi = [System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $onePage; $psi.UseShellExecute = $true; $null = [System.Diagnostics.Process]::Start($psi); Write-Host ("  [唯一頁] 已開:" + $onePage) -ForegroundColor Green } catch { Write-Host ("  [唯一頁] 自己開:" + $onePage) -ForegroundColor Yellow } }
    Write-Host ("=== [via-review v0106] 畢 · 結束碼 " + $final + " · 紅 " + $Red.Count + " · 黃 " + $Yel.Count + " · 錨點 " + $Anch.Count + " · " + $secsAll + "s · 唯一頁 " + $onePage + " ===") -ForegroundColor $(if ($final -eq 0) { "Green" } elseif ($final -eq 2) { "Yellow" } else { "Red" })
    if ($script:Dotted) { $global:LASTEXITCODE = $final; return } else { exit $final }
}
if (-not $NoClipboard) { try { ($md -join "`n") | Set-Clipboard; Write-Host "  貼回包已放進剪貼簿(Ctrl+V 貼給 AI)" -ForegroundColor Yellow } catch { } }
# ---------------------------------------------------------------- 退路:唯一頁沒出成 → v0105 原多頁(一字照舊)
$hb = [System.Text.StringBuilder]::new()
$null = $hb.Append("<!doctype html><html><head><meta charset='utf-8'><title>via-review " + $stamp + "</title><style>" + $css + "</style><script>" + $js + "</script></head><body><header><h1>via-review 系統總檢 · " + $stamp + " · 總判 <span class='" + $(if ($final -eq 0) { 'GREEN' } elseif ($final -eq 2) { 'YELLOW' } else { 'RED' }) + "'>" + $(if ($final -eq 0) { 'GREEN' } elseif ($final -eq 2) { 'YELLOW' } else { 'RED' }) + "</span></h1><div class='dim'>VCGC " + (HtmlEnc $V.Name) + " · 分支 " + (HtmlEnc $branch) + " · " + (HtmlEnc $py) + "</div></header><nav>")
$i = 0; foreach ($k in $pages.Keys) { $null = $hb.Append("<button onclick='go(" + $i + ")'>" + (HtmlEnc $k) + "</button>"); $i++ }
$null = $hb.Append("</nav>"); foreach ($k in $pages.Keys) { $null = $hb.Append("<section>" + $pages[$k] + "</section>") }; $null = $hb.Append("</body></html>")
$html = Join-Path $OutDir ("REVIEW_" + $stamp + ".html")
[IO.File]::WriteAllText($html, $hb.ToString(), $Utf8)
Copy-Item -LiteralPath $html -Destination (Join-Path $OutDir "REVIEW_latest.html") -Force
if (-not $NoOpen) { try { $psi = [System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName = $html; $psi.UseShellExecute = $true; $null = [System.Diagnostics.Process]::Start($psi); Write-Host ("  [多頁矩陣] 已開:" + $html) -ForegroundColor Green } catch { Write-Host ("  [多頁矩陣] 開不起來(自己開):" + $html) -ForegroundColor Yellow } }
Write-Host ("=== [via-review v0106] 畢(退回多頁)· 結束碼 " + $final + " · 紅 " + $Red.Count + " · 黃 " + $Yel.Count + " · 錨點 " + $Anch.Count + " · " + $secsAll + "s · " + $html + " ===") -ForegroundColor $(if ($final -eq 0) { "Green" } elseif ($final -eq 2) { "Yellow" } else { "Red" })
if ($script:Dotted) { $global:LASTEXITCODE = $final; return } else { exit $final }

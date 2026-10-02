# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-Review-v0100.ps1 — 短指令 via-review(別名 總檢):一次完整、快速的系統狀態總檢(只讀為主;GitHub 為主、本機為輔)
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
# 用法:via-review [-Install] [-Sync] [-Lists] [-Optimize] [-NoOpen] [-NoClipboard] [-Since yyyy-MM-dd] [-Dry]
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
    [switch]$Dry
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
$Out   = Join-Path $Rep "review"
if (-not (Test-Path -LiteralPath $Out)) { $null = New-Item -ItemType Directory -Path $Out -Force }
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
function Lamp([int]$rc) { switch ($rc) { 0 { "GREEN" } 2 { "NODATA" } 3 { "ABSENT" } 4 { "GATE" } default { "RED" } } }
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
    if ($LogName) { $out | Set-Content -LiteralPath (Join-Path $Out ($LogName + "_" + $stamp + ".log")) -Encoding UTF8 }
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
Write-Host ("=== [via-review v0100] 系統總檢 · VCGC " + $V.Name + " · python " + $py + " ===") -ForegroundColor Cyan
$keepFrom = $env:VIA_FROM_VCGC; $keepConsent = $env:VIA_NET_CONSENT
$env:VIA_FROM_VCGC = "YES"
if ($Install) { $env:VIA_NET_CONSENT = "YES" }   # -Install = 操作員親手開閘,只在本行程,finally 還原

try {
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

# ---------------------------------------------------------------- ② 撞名 / 短令閘(唯讀)
$cg = Invoke-Vcgc @("run", "--family", "core", "CGC_MDL165_CommandRunGate", "collide", "--json") "COLLIDE"
$cj = $null; try { $cj = (($cg.out -join "`n").Substring((($cg.out -join "`n").IndexOf("{"))) | ConvertFrom-Json -Depth 32) } catch { }
$collideNote = if ($cj) { ((@($cj.PSObject.Properties | Where-Object { $_.Name -match 'collide|collision|dup|red|yellow|total|count' } | ForEach-Object { $_.Name + "=" + $_.Value }) | Select-Object -First 6) -join " · ") } else { (@($cg.out | Select-Object -Last 2) -join " | ") }
Harvest-Lines $cg.out "② 撞名閘"
Add-Step "②" "撞名 / 短令閘 CGC_MDL165 collide" (Lamp $cg.rc) $cg.rc $cg.secs $collideNote

# ---------------------------------------------------------------- ③ 環境
$envJson = Join-Path $Rep "env_manager\ENVMGR_latest.json"
$e1 = Invoke-Vcgc @("run", "--family", "core", "CGC_MDL240_EnvManager", "check") "ENVCHECK"
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

# ---------------------------------------------------------------- ④ 編號 / 註冊 / 下放漂移(SDD + SSOT 並行,唯讀)+ 本檔彈性掃描
$t0 = Get-Date
$lanes = @()
foreach ($g in @(@{ id = "SDD"; a = 'sdd check' }, @{ id = "SSOT"; a = 'ssot panorama' })) {
    $gl = Join-Path $Out ($g.id + "_" + $stamp + ".log")
    try { $gp = Start-Process -FilePath $py -ArgumentList ('"' + $V.FullName + '" ' + $g.a) -WorkingDirectory $VIA -NoNewWindow -PassThru -RedirectStandardOutput $gl -RedirectStandardError (Join-Path $Out ($g.id + "_" + $stamp + ".err.log")); $lanes += [pscustomobject]@{ id=$g.id; proc=$gp; log=$gl } }
    catch { Add-Step ("④" + $g.id) ("VCGC 下放檢查 " + $g.id) "RED" 1 0 ("起不來:" + $_.Exception.Message) }
}
# 本檔彈性掃描:受控夾 .py 的家族編號 + 是否在 FunctionInventory SSOT 尾版
$inv = Get-Newest $Reg "VIA_VCGC_FunctionInventory_SSOT_v*.json"
$invText = if ($inv) { Get-Content -LiteralPath $inv.FullName -Raw -Encoding UTF8 } else { "" }
$ctrl = @("functional modules\VDF", "functional modules\VRN", "supportive modules\registry") | ForEach-Object { Join-Path $VIA $_ } | Where-Object { Test-Path -LiteralPath $_ }
$skipRx = '\\(references|intake|_output|runs|tests?|fixtures|sandbox|__pycache__|_to_delete|archive|backup)\\'
$numRx  = '^(?<fam>[A-Z]{2,5})_(?<kind>MDL|ENG)(?<no>\d{3})_(?<name>\w+?)(_v\d{4})?\.py$'
$regRows = New-Object System.Collections.Generic.List[object]
foreach ($d in $ctrl) {
    foreach ($f in @(Get-ChildItem -LiteralPath $d -Filter *.py -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch $skipRx })) {
        $m = [regex]::Match($f.Name, $numRx)
        $numbered = $m.Success
        $stem = if ($numbered) { $m.Groups['fam'].Value + "_" + $m.Groups['kind'].Value + $m.Groups['no'].Value + "_" + $m.Groups['name'].Value } else { ($f.BaseName -replace '_v\d{4}$', '') }
        $registered = ($invText.Length -gt 0) -and ($invText.Contains($stem))
        $rel = $f.FullName.Substring($VIA.Length).TrimStart('\')
        if (-not $numbered) { Add-Anchor $rel 1 "NO_NUMBER" ("無家族編號(需 XXX_MDL###_ / XXX_ENG###_):" + $f.Name) "彈性(檔名 regex)" "④ 編號" }
        elseif (-not $registered) { Add-Anchor $rel 1 "NOT_REGISTERED" ("不在 FunctionInventory SSOT 尾版 " + $(if ($inv) { $inv.Name } else { "(無冊)" }) + ":" + $stem) "彈性(SSOT 冊字串比對)" "④ 註冊" }
        $regRows.Add([pscustomobject]@{ 檔=$rel; 家族=$(if ($numbered) { $m.Groups['fam'].Value } else { "-" }); 編號=$(if ($numbered) { $m.Groups['kind'].Value + $m.Groups['no'].Value } else { "無" }); 在冊=$(if ($registered) { "是" } else { "否" }); 燈=$(if ($numbered -and $registered) { "GREEN" } else { "RED" }) })
    }
}
$regRed = @($regRows | Where-Object { $_.燈 -eq "RED" }).Count
Add-Step "④a" ("彈性掃描:受控 .py " + $regRows.Count + " 支(無編號 / 未註冊 = 紅)") $(if ($regRed -gt 0) { "RED" } else { "GREEN" }) $(if ($regRed -gt 0) { 1 } else { 0 }) ([int]((Get-Date) - $t0).TotalSeconds) ("紅 " + $regRed + " · 冊 " + $(if ($inv) { $inv.Name } else { "無" }))

# ---------------------------------------------------------------- ⑤ 全景 AST 錨點(PAN-SCAN ∥ PAN-READ 背景)+ PS Parser
$t0 = Get-Date
$tok = $null
try { $tok = Join-Path $Repo ((Get-Content -LiteralPath (Join-Path $Reg "VIA_ToolVersion_Lock_v0100.json") -Raw -Encoding UTF8 | ConvertFrom-Json).token.path) } catch { }
if (-not $tok -or -not (Test-Path -LiteralPath $tok)) { $t = Get-Newest $Reg "CGC_MDL158_VIAPanoramaAuditRepair_v*.py"; if ($t) { $tok = $t.FullName } }
$panScan = Join-Path $Out ("PANSCAN_" + $stamp + ".json"); $panRead = Join-Path $Out ("PANREAD_" + $stamp + ".json"); $panProcs = @()
if ($tok) {
    try {
        $panProcs += Start-Process -FilePath $py -ArgumentList ('"' + $tok + '" scan --fast --json') -WorkingDirectory $VIA -NoNewWindow -PassThru -RedirectStandardOutput $panScan -RedirectStandardError (Join-Path $Out ("PANSCAN_" + $stamp + ".err.log"))
        $panProcs += Start-Process -FilePath $py -ArgumentList ('"' + $tok + '" read "functional modules\VDF" "functional modules\VRN" "supportive modules\registry" --json') -WorkingDirectory $VIA -NoNewWindow -PassThru -RedirectStandardOutput $panRead -RedirectStandardError (Join-Path $Out ("PANREAD_" + $stamp + ".err.log"))
    } catch { Add-Step "⑤" "全景 AST 線" "RED" 1 0 ("起不來:" + $_.Exception.Message) }
} else { Add-Step "⑤" "全景 AST 線" "ABSENT" 3 0 "找不到 CGC_MDL158 鎖冊 token 工具" }
# PS Parser(精準):倉根 Invoke-VIA-*.ps1 / Register-VIA-Commands-v*.ps1 / supportive modules\*.ps1
$psFiles = @(Get-ChildItem -LiteralPath $VIA -Filter "Invoke-VIA-*.ps1" -File) + @(Get-ChildItem -LiteralPath $VIA -Filter "Register-VIA-Commands-v*.ps1" -File) + @(Get-ChildItem -LiteralPath (Join-Path $VIA "supportive modules") -Filter *.ps1 -File -ErrorAction SilentlyContinue)
$psErr = 0
foreach ($f in $psFiles) {
    $tk = $null; $er = $null
    try { $null = [System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tk, [ref]$er) } catch { $er = @([pscustomobject]@{ Message = $_.Exception.Message; Extent = $null }) }
    foreach ($e in @($er)) { $psErr++; $ln = if ($e.Extent) { $e.Extent.StartLineNumber } else { "" }; Add-Anchor ($f.FullName.Substring($VIA.Length).TrimStart('\')) $ln "PS_SYNTAX" $e.Message $(if ($ln) { "AST精準(PS Parser)" } else { "行程(Parser 例外)" }) "⑤ PS Parser" }
}
Add-Step "⑤a" ("PS Parser 精準定位:" + $psFiles.Count + " 支") $(if ($psErr -gt 0) { "RED" } else { "GREEN" }) $(if ($psErr -gt 0) { 1 } else { 0 }) ([int]((Get-Date) - $t0).TotalSeconds) ("語法錯 " + $psErr)

# ---------------------------------------------------------------- ⑥ 清單七步(-Lists;v0108 ① 原表,經 VCGC)
if ($Lists) {
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
if ($Optimize) {
    $core = Get-Newest $VIA "Invoke-VIA-RealTestCore-v*.ps1"
    if ($core) {
        $t0 = Get-Date
        Write-Host ("  ⑦ 全部優化一回 → " + $core.Name + "(25 加速器 · VDF ∥ VRN · 覆蓋 · 全景 + 三合一)") -ForegroundColor Cyan
        & $core.FullName -NoOpen:$NoOpen
        $rc7 = $LASTEXITCODE
        Add-Step "⑦" ("全部優化一回 " + $core.Name) $(if ($rc7 -eq 0) { "GREEN" } elseif ($rc7 -eq 2) { "NODATA" } else { "RED" }) $rc7 ([int]((Get-Date) - $t0).TotalSeconds) ("rc " + $rc7 + "(0 全綠 · 2 有發現 · 1 紅 · 124 超時)")
        $rtAnch = Join-Path $Rep "realtest\AST_ANCHORS_latest.txt"
        if (Test-Path -LiteralPath $rtAnch) { foreach ($l in @(Get-Content -LiteralPath $rtAnch -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith("#") } | Select-Object -First 400)) { $m = [regex]::Match($l, '^(.+?):(\d*)\s+(\S+)\s+(.*)$'); if ($m.Success) { Add-Anchor $m.Groups[1].Value $m.Groups[2].Value $m.Groups[3].Value $m.Groups[4].Value "AST精準(realtest 全景)" "⑦ RealTest" } } }
    } else { Add-Step "⑦" "全部優化一回" "ABSENT" 3 0 "Invoke-VIA-RealTestCore-v*.ps1 不在(先 git pull)" }
}

# ---------------------------------------------------------------- 收 ④ SDD/SSOT 與 ⑤ PAN 背景線
foreach ($ln in $lanes) { try { $ln.proc.WaitForExit(300000) | Out-Null } catch { } }
foreach ($ln in $lanes) {
    $txt = @(if (Test-Path -LiteralPath $ln.log) { Get-Content -LiteralPath $ln.log -Encoding UTF8 } else { @() })
    $reds = @($txt | Where-Object { $_ -match '\[RED\s*\]' }); $yels = @($txt | Where-Object { $_ -match '\[YELLOW\s*\]' })
    foreach ($l in $reds) { Add-Anchor "-" "" ("SSOT_" + $ln.id) $l "行程(VCGC 下放檢查站列)" ("④ " + $ln.id) }
    $tot = @($txt | Where-Object { $_ -match '總判|VERDICT|GREEN|RED' } | Select-Object -Last 1) -join ""
    Add-Step ("④" + $ln.id) ("VCGC 下放檢查 " + $ln.id + $(if ($ln.id -eq "SDD") { "(工作流冊:步 · 碼 · 需求回指)" } else { "(編號 · 命名 · 註冊 · 參數 · regex · 上下連結)" })) $(if ($reds.Count -gt 0) { "RED" } elseif ($yels.Count -gt 0) { "NODATA" } else { "GREEN" }) $ln.proc.ExitCode 0 ("紅 " + $reds.Count + " · 黃 " + $yels.Count + $(if ($tot) { " · " + $tot } else { "" }))
}
foreach ($p in $panProcs) { try { $p.WaitForExit(300000) | Out-Null } catch { } }
$severe = @("SYNTAX", "COMPILE", "TALIB"); $sevN = 0; $panN = 0
$sj = Read-JsonTail $panScan
if ($sj) { foreach ($r in @($sj.rows | Where-Object { -not $_.exempt })) { $panN++; if ($severe -contains ("" + $r.cls)) { $sevN++ }; Add-Anchor ("" + $r.file) $r.line ("治理:" + $r.cls) ("" + $r.detail) "AST精準(PAN-SCAN)" "⑤ PAN-SCAN" } }
$rj = Read-JsonTail $panRead
if ($rj) { foreach ($c in @($rj.cards)) { $rel = ("" + $c.path); if ($rel.StartsWith($VIA)) { $rel = $rel.Substring($VIA.Length).TrimStart('\', '/') }; foreach ($is in @($c.issues)) { if (-not $is) { continue }; $panN++; if ($severe -contains ("" + $is.cls)) { $sevN++ }; Add-Anchor $rel $is.line ("AST:" + $is.cls) ("" + $is.detail) "AST精準(PAN-READ)" "⑤ PAN-READ" } } }
if ($tok) { Add-Step "⑤" ("全景 AST 錨點(PAN-SCAN " + $(if ($sj) { $sj.files_scanned } else { "?" }) + " 檔 · PAN-READ " + $(if ($rj) { $rj.files } else { "?" }) + " 檔)") $(if (-not $sj -or -not $rj) { "RED" } elseif ($sevN -gt 0) { "RED" } elseif ($panN -gt 0) { "NODATA" } else { "GREEN" }) $(if (-not $sj -or -not $rj) { 1 } elseif ($sevN -gt 0) { 1 } elseif ($panN -gt 0) { 2 } else { 0 }) 0 ("錨點 " + $panN + " · 嚴重(SYNTAX/COMPILE/TALIB) " + $sevN + $(if (-not $sj -or -not $rj) { " · 有線沒產出 JSON(看 review\PAN*.err.log)" } else { "" })) }
}
finally { $env:VIA_FROM_VCGC = $keepFrom; $env:VIA_NET_CONSENT = $keepConsent }

# ---------------------------------------------------------------- ⑧ 錨點全文 · 貼回包 · 多頁矩陣 HTML
$anchorFile = Join-Path $Out ("ANCHORS_" + $stamp + ".txt")
$anchLines = @("# via-review 錨點 · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " · 共 " + $Anch.Count + "(檔:行  類  定位  說明;一個不漏)") + @($Anch | Sort-Object 檔, 行 | ForEach-Object { "{0}:{1}  {2}  [{3}]  {4}" -f $_.檔, $_.行, $_.類, $_.定位, $_.說明 })
$anchLines | Set-Content -LiteralPath $anchorFile -Encoding UTF8
Copy-Item -LiteralPath $anchorFile -Destination (Join-Path $Out "ANCHORS_latest.txt") -Force
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
$mdPath = Join-Path $Out ("REVIEW_" + $stamp + ".md")
[IO.File]::WriteAllText($mdPath, (($md -join "`n") + "`n"), $Utf8)
Copy-Item -LiteralPath $mdPath -Destination (Join-Path $Out "REVIEW_latest.md") -Force
if (-not $NoClipboard) { try { ($md -join "`n") | Set-Clipboard; Write-Host "  貼回包已放進剪貼簿(Ctrl+V 貼給 AI)" -ForegroundColor Yellow } catch { } }

# 多頁矩陣 HTML(自含;不依賴任何模組)
$enc = [System.Net.WebUtility]
function H([object]$v) { $enc::HtmlEncode("" + $v) }
function Tbl([object[]]$rows, [string[]]$cols) {
    if (-not $rows -or $rows.Count -eq 0) { return "<p class='dim'>(無資料)</p>" }
    if (-not $cols) { $cols = @($rows[0].PSObject.Properties.Name) }
    $sb = [System.Text.StringBuilder]::new(); $null = $sb.Append("<div class='wrap'><table><tr>"); foreach ($c in $cols) { $null = $sb.Append("<th>" + (H $c) + "</th>") }; $null = $sb.Append("</tr>")
    foreach ($r in $rows) { $null = $sb.Append("<tr>"); foreach ($c in $cols) { $v = "" + $r.$c; $cls = if ($v -match '^(GREEN|RED|NODATA|GATE|ABSENT|INFO|YELLOW|是|否)$') { " class='" + $v + "'" } else { "" }; $null = $sb.Append("<td" + $cls + ">" + (H $v) + "</td>") }; $null = $sb.Append("</tr>") }
    $null = $sb.Append("</table></div>"); $sb.ToString() }
$css = "body{margin:0;font-family:'Segoe UI','Microsoft JhengHei';background:#0b1220;color:#e5e7eb;font-size:13px}header{padding:12px 20px;background:#111827;border-bottom:1px solid #334155}h1{margin:0;font-size:18px;color:#93c5fd}nav{display:flex;flex-wrap:wrap;gap:6px;padding:8px 20px;background:#0f172a;position:sticky;top:0}nav button{background:#1e293b;color:#cbd5e1;border:1px solid #334155;padding:5px 12px;border-radius:6px;cursor:pointer}nav button.on{background:#2563eb;color:#fff}section{display:none;padding:12px 20px}section.on{display:block}h2{color:#93c5fd;font-size:15px;margin:14px 0 6px}table{border-collapse:collapse;margin:4px 0 12px;font-size:12px}td,th{border:1px solid #334155;padding:4px 8px;vertical-align:top}th{background:#1e293b;position:sticky;top:40px}tr:nth-child(even){background:#0f172a}.GREEN,.是{color:#4ade80;font-weight:600}.RED,.否{color:#f87171;font-weight:600}.NODATA,.GATE,.ABSENT,.YELLOW{color:#fbbf24}.INFO{color:#64748b}.dim{color:#64748b}pre{background:#111827;padding:8px;overflow:auto;font-size:11px}.wrap{overflow-x:auto}.big{font-size:22px;font-weight:700}"
$js = 'function go(i){document.querySelectorAll("nav button").forEach((b,k)=>b.classList.toggle("on",k===i));document.querySelectorAll("section").forEach((s,k)=>s.classList.toggle("on",k===i));}document.addEventListener("DOMContentLoaded",()=>go(0));'
$overview = @(
    [pscustomobject]@{ 項目="總判"; 值=$(if ($final -eq 0) { "GREEN" } elseif ($final -eq 2) { "YELLOW" } else { "RED" }) }
    [pscustomobject]@{ 項目="紅字 / 黃字"; 值=("" + $Red.Count + " / " + $Yel.Count) }
    [pscustomobject]@{ 項目="錨點"; 值=("" + $Anch.Count + "(" + (($locStat | ForEach-Object { $_.定位種類 + " " + $_.數 }) -join " · ") + ")") }
    [pscustomobject]@{ 項目="Git"; 值=$gitNote + $(if ($mmLine) { " · " + $mmLine } else { "" }) }
    [pscustomobject]@{ 項目="環境"; 值=("總判 " + $envBefore + $(if ($installLine) { " · " + $installLine } else { "" })) }
    [pscustomobject]@{ 項目="受控 .py 無編號 / 未註冊"; 值=("" + $regRed + " / " + $regRows.Count) }
    [pscustomobject]@{ 項目="全景 AST 嚴重"; 值=("" + $sevN + "(SYNTAX / COMPILE / TALIB)") }
    [pscustomobject]@{ 項目="耗時"; 值=("" + $secsAll + "s") }
    [pscustomobject]@{ 項目="貼回包"; 值=$mdPath }
)
$pages = [ordered]@{
    "總覽"            = (Tbl $overview) + "<h2>步驟燈號</h2>" + (Tbl @($Steps))
    "Git 整合"        = (Tbl $gitRows) + "<h2>衝突</h2>" + (Tbl @($conf | ForEach-Object { [pscustomobject]@{ 狀態=$_.Substring(0,2); 檔=$_.Substring(3) } })) + "<h2>本機改動 / 未追蹤(前 80)</h2>" + (Tbl @(($mod + $untr) | Select-Object -First 80 | ForEach-Object { [pscustomobject]@{ 狀態=$_.Substring(0,2); 檔=$_.Substring(3) } }))
    "環境"            = "<p class='big " + $(if ($envBefore -eq 'GREEN') { 'GREEN' } else { 'RED' }) + "'>ENV " + (H $envBefore) + $(if ($installLine) { " → " + (H $envAfter) } else { "" }) + "</p><pre>" + (H ((@($e1.out | Select-Object -Last 60)) -join "`n")) + "</pre>"
    "編號 / 註冊"     = "<p>規則:受控夾 .py 檔名需 XXX_MDL###_ 或 XXX_ENG###_,且字根要在 " + (H $(if ($inv) { $inv.Name } else { "(無冊)" })) + " 內;缺一即紅。SDD / SSOT 站列紅黃見「AST 錨點」頁。</p>" + (Tbl @($regRows | Sort-Object 燈, 檔))
    "AST 錨點"        = "<p>定位種類:<b>AST精準</b> = 檔:行 來自 AST(PAN-SCAN / PAN-READ / PS Parser)· <b>彈性</b> = 檔:行 來自 regex / 檔名 / git 狀態 · <b>行程</b> = 只有訊息沒有行號(正主站列)。</p>" + (Tbl @($locStat)) + (Tbl @($Anch | Sort-Object 檔, 行))
    "步驟燈號"        = (Tbl @($Steps))
    "紅黃全文"        = "<h2>紅字</h2><pre>" + (H ($Red -join "`n")) + "</pre><h2>黃字</h2><pre>" + (H ($Yel -join "`n")) + "</pre>"
}
$hb = [System.Text.StringBuilder]::new()
$null = $hb.Append("<!doctype html><html><head><meta charset='utf-8'><title>via-review " + $stamp + "</title><style>" + $css + "</style><script>" + $js + "</script></head><body><header><h1>via-review 系統總檢 · " + $stamp + " · 總判 <span class='" + $(if ($final -eq 0) { 'GREEN' } elseif ($final -eq 2) { 'YELLOW' } else { 'RED' }) + "'>" + $(if ($final -eq 0) { 'GREEN' } elseif ($final -eq 2) { 'YELLOW' } else { 'RED' }) + "</span></h1><div class='dim'>VCGC " + (H $V.Name) + " · 分支 " + (H $branch) + " · " + (H $py) + "</div></header><nav>")
$i = 0; foreach ($k in $pages.Keys) { $null = $hb.Append("<button onclick='go(" + $i + ")'>" + (H $k) + "</button>"); $i++ }
$null = $hb.Append("</nav>"); foreach ($k in $pages.Keys) { $null = $hb.Append("<section>" + $pages[$k] + "</section>") }; $null = $hb.Append("</body></html>")
$html = Join-Path $Out ("REVIEW_" + $stamp + ".html")
[IO.File]::WriteAllText($html, $hb.ToString(), $Utf8)
Copy-Item -LiteralPath $html -Destination (Join-Path $Out "REVIEW_latest.html") -Force
if (-not $NoOpen -and [Environment]::UserInteractive) { try { Start-Process $html } catch { Write-Host ("  [多頁矩陣] 開不起來(自己開):" + $html) -ForegroundColor Yellow } }
Write-Host ("=== [via-review v0100] 畢 · 結束碼 " + $final + " · 紅 " + $Red.Count + " · 黃 " + $Yel.Count + " · 錨點 " + $Anch.Count + " · " + $secsAll + "s · " + $html + " ===") -ForegroundColor $(if ($final -eq 0) { "Green" } elseif ($final -eq 2) { "Yellow" } else { "Red" })
if ($script:Dotted) { $global:LASTEXITCODE = $final; return } else { exit $final }
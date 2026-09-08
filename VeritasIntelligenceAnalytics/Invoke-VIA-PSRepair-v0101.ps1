# =====================================================================
# Invoke-VIA-PSRepair-v0101.ps1 — PS 修復單一總入口(批253 立;批403 卡斷修)
# =====================================================================
# 統包三輪(現役 MDL101×收容 Accel20 雙引擎合流;收容件原地不動=駕馭):
#   R1 全景:收容 Invoke-VIA-PSRepair-Accel20(尾版)dry-run——真 PS AST
#      +20 加速器矩陣+PSScriptAnalyzer 橋(缺=誠實 NOT_INSTALLED)
#   R2 合修(-Fix 才動):①Accel20 -GoToken GO_v1(Parallel-Fixable+
#      .psrepair.bak 讓位)②python MDL101 fix(窄類+manifest+UNDO)
#   R3 驗證:收容 PostRepairVerify(尾版)+MDL101 scan 對照+啟動沙盒
#      =VIA.ps1 AST parse(非阻塞:只 parse 不執行)
#   輸出:Accel20 HTML 矩陣+MDL101 RYG 四專區矩陣+終端三態總結
#
# v0100→v0101(批403 操作員工作站實錄「[R1] rc=1 … [R2b] 卡斷」):
#  ① 參數綁定修(真 bug,非設定問題):v0100 用 `pwsh -File $accel
#     -ExcludePattern $Excl`。PowerShell 的 -File 模式**不支援陣列引數**
#     ——$Excl 的 9 個樣式會被攤平成散落的位置引數,第 1 個綁上
#     -ExcludePattern,第 2 個起依宣告序掉進 -Paths(1)、-ThrottleLimit(3)…
#     於是 '*\_bytecode_originals\*' 撞上 [int]$ThrottleLimit →
#     "Cannot convert value ... to type System.Int32" → R1/R2a rc=1 全滅。
#     改法:子行程改走 -Command,於子行程內以「雜湊表字面量+splatting」
#     呼叫(陣列真的是陣列);仍是獨立行程=收容腳本的 exit 不會殺母行程。
#     收容原件零觸碰(references/intake 不可動律)。
#  ② 不卡斷(20 加速器 #16/#17/#18):每輪走 Invoke-VIAGuarded 看門狗
#     ——同視窗直播、逾時 Kill 整樹回 rc=124 誠實印明,不再無聲吊死;
#     六段輪次進度條(Write-VIAProgress Id 12)。加速器缺席=graceful
#     退回直呼(功能不變,只少進度條)。
#  ③ R3a 誠實化:PostRepairVerify 尾版同樣是 [string[]]$ExcludePattern,
#     一併走 -Command 道;其 -PythonExe 預設為他機硬寫路徑,故本入口
#     顯式帶入本機解譯器(缺=誠實不帶,由收容件自理)。
#  ④ -Selftest:純字串檢查子行程命令建構(零外呼、零寫檔),八檢。
# 用法:pwsh -File .\Invoke-VIA-PSRepair-v0101.ps1 [-Fix] [-NoOpen]
#         [-TimeoutSec 1800] [-Throttle 8] [-ShowCmd] | -Selftest
# =====================================================================
param(
    [switch]$Fix,
    [switch]$NoOpen,
    [int]$TimeoutSec = 1800,
    [int]$Throttle = 8,
    [switch]$ShowCmd,
    [switch]$Selftest
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
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
$VIA = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutRoot = Join-Path $VIA "VIA_Reports\ps_repair\accel20"
$Excl = @('*\rollback\*', 'rb-*', '*\_bytecode_originals\*', '*\__pycache__\*',
          '*\node_modules\*', '*\90_PRIOR_PACKAGES\*', '*\VIA_Reports\*',
          '*\uploads\*', '*\.git\*')

function ConvertTo-VIAPSLiteral {
    # 值 → PowerShell 字面量(單引號字串內之 ' 以 '' 逸出;陣列=@(...);布林=$true/$false)
    param($Value)
    if ($null -eq $Value) { return '$null' }
    if ($Value -is [System.Management.Automation.SwitchParameter]) {
        return $(if ($Value.IsPresent) { '$true' } else { '$false' })
    }
    if ($Value -is [bool]) { return $(if ($Value) { '$true' } else { '$false' }) }
    if ($Value -is [int] -or $Value -is [long] -or $Value -is [double]) { return "$Value" }
    if ($Value -is [System.Array]) {
        $items = @($Value | ForEach-Object { "'" + ([string]$_ -replace "'", "''") + "'" })
        return '@(' + ($items -join ',') + ')'
    }
    return "'" + ([string]$Value -replace "'", "''") + "'"
}

function New-VIAChildCommand {
    # 建構子行程腳本:雜湊表字面量 + splatting(-File 不支援陣列之正解)
    param([string]$Script, [hashtable]$Named)
    $pairs = @()
    foreach ($k in ($Named.Keys | Sort-Object)) {
        $pairs += ("'" + $k + "'=" + (ConvertTo-VIAPSLiteral $Named[$k]))
    }
    return ('$p=@{' + ($pairs -join ';') + '}; & ''' +
            ($Script -replace "'", "''") + ''' @p')
}

function Invoke-VIAChildPS {
    # 子行程 pwsh -Command(陣列安全)+ 看門狗(不卡斷;逾時 124)
    param([string]$Name, [string]$Script, [hashtable]$Named, [int]$Timeout = 1800)
    $cmd = New-VIAChildCommand -Script $Script -Named $Named
    if ($ShowCmd) { Write-Host ("    [cmd] " + $cmd) -ForegroundColor DarkGray }
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $cmd)
    if (Get-Command Invoke-VIAGuarded -ErrorAction SilentlyContinue) {
        return (Invoke-VIAGuarded -Name $Name -Exe 'pwsh' -CmdArgs $a -TimeoutSec $Timeout -Cwd $VIA)
    }
    & pwsh @a                       # graceful:加速器缺席=直呼(無進度條)
    return $LASTEXITCODE
}

function Invoke-VIAChildExe {
    # 外部工人(python 等)同款看門狗;缺加速器=直呼
    param([string]$Name, [string]$Exe, [string[]]$CmdArgs, [int]$Timeout = 1800)
    if (Get-Command Invoke-VIAGuarded -ErrorAction SilentlyContinue) {
        return (Invoke-VIAGuarded -Name $Name -Exe $Exe -CmdArgs $CmdArgs -TimeoutSec $Timeout -Cwd $VIA)
    }
    & $Exe @CmdArgs
    return $LASTEXITCODE
}

function Write-VIARound {
    param([string]$Stage, [int]$Index)
    if (Get-Command Write-VIAProgress -ErrorAction SilentlyContinue) {
        Write-VIAProgress -Activity 'VIA PS 修復三輪' -Status $Stage -Percent ([int](100 * $Index / 6)) -Id 12
    }
}

function Show-VIARc {
    param([string]$Tag, [int]$Rc, [int]$Timeout)
    if ($Rc -eq 124) {
        Write-Host ("  [$Tag] 逾時 " + $Timeout + "s=看門狗收樹(誠實;加 -TimeoutSec 放寬或縮小 -Root)") -ForegroundColor Red
    } elseif ($Rc -eq 0) {
        Write-Host ("  [$Tag] rc=0") -ForegroundColor Green
    } else {
        Write-Host ("  [$Tag] rc=" + $Rc) -ForegroundColor Yellow
    }
}

# --- 自測(純字串;零外呼零寫檔) --------------------------------------
if ($Selftest) {
    Write-Host "=== PS 修復總入口 v0101 · 八檢自測(零外呼)===" -ForegroundColor Cyan
    $fails = @()
    function Test-VIA([string]$Name, [bool]$Cond, [string]$Note = '') {
        Write-Host ("  [" + $(if ($Cond) { 'OK' } else { 'FAIL' }) + "] $Name $Note")
        if (-not $Cond) { $script:fails += $Name }
    }
    $c1 = New-VIAChildCommand -Script 'C:\a b\x.ps1' -Named @{ Root = 'C:\r'; ExcludePattern = @('*\a\*', 'rb-*'); NoOpen = $true }
    Test-VIA '① 陣列真的是陣列(@(...)非攤平=本批根因修)' ($c1.Contains('''ExcludePattern''=@(''*\a\*'',''rb-*'')'))
    Test-VIA '② 布林 → $true(不落位置參數)' ($c1.Contains('''NoOpen''=$true'))
    Test-VIA '③ 腳本以 & 單引號路徑 @p 呼叫(splatting)' ($c1.Contains('& ''C:\a b\x.ps1'' @p'))
    $c2 = New-VIAChildCommand -Script "C:\o'ne.ps1" -Named @{ Root = "C:\it's" }
    Test-VIA '④ 單引號逸出(雙寫=字面單引號)' (
        $c2.Contains('''Root''=''C:\it''''s''') -and $c2.Contains('& ''C:\o''''ne.ps1'' @p'))
    Test-VIA '⑤ 零雙引號(Start-Process 引數包裝安全)' (-not $c1.Contains('"'))
    Test-VIA '⑥ 整數不加引號(ThrottleLimit 型別安全)' ((ConvertTo-VIAPSLiteral 8) -eq '8')
    Test-VIA '⑦ 排除冊完整(9 樣式;收容原件零觸碰律)' ($Excl.Count -eq 9 -and $Excl -contains '*\_bytecode_originals\*')
    $src = Get-Content -LiteralPath $PSCommandPath -Raw
    Test-VIA '⑧ 不卡斷律(看門狗+進度條+逾時 124 誠實印)' (
        ($src -match 'Invoke-VIAGuarded') -and ($src -match 'Write-VIAProgress') -and ($src -match '124'))
    Write-Host ("  [計] 八檢 OK " + (8 - $fails.Count) + " · FAIL " + $fails.Count)
    exit $(if ($fails.Count) { 1 } else { 0 })
}

function Get-NewestFile([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Recurse -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}

$intake = Join-Path $VIA "supportive modules\references\intake"
$accel = Get-NewestFile $intake "Invoke-VIA-PSRepair-Accel20-v*.ps1"
$verify = Get-NewestFile $intake "Invoke-VIA-PostRepairVerify-Accel20-v*.ps1"
$mdl101 = Get-NewestFile (Join-Path $VIA "supportive modules\registry") "CGC_MDL101_PSAstRepair_v*.py"
$pyexe = (Get-Command python -ErrorAction SilentlyContinue).Source

Write-Host "=== VIA PS 修復總入口 v0101(批253/403)· 雙引擎三輪 · $(if ($Fix) { 'FIX 模式' } else { 'DRY-RUN(加 -Fix 才動檔)' }) ===" -ForegroundColor Cyan
Write-Host ("  Accel20=" + $(if ($accel) { Split-Path $accel -Leaf } else { "缺(誠實;先 via-intake)" }))
Write-Host ("  Verify =" + $(if ($verify) { Split-Path $verify -Leaf } else { "缺(誠實)" }))
Write-Host ("  MDL101 =" + $(if ($mdl101) { Split-Path $mdl101 -Leaf } else { "缺(誠實)" }))
Write-Host ("  看門狗 =" + $TimeoutSec + "s/輪 · throttle " + $Throttle + " · 陣列走 -Command splatting(批403 綁定修)")

# --- R1 全景(真 AST+20 加速器;dry-run 永遠先跑) -------------------
if ($accel) {
    Write-VIARound 'R1 全景掃描' 1
    Write-Host "`n[R1] Accel20 全景掃描(真 PS AST+PSSA 橋+20 加速器矩陣)…" -ForegroundColor Yellow
    $rc = Invoke-VIAChildPS -Name 'R1 Accel20 scan' -Script $accel -Timeout $TimeoutSec -Named @{
        Root = $VIA; OutRoot = $OutRoot; ExcludePattern = $Excl
        ThrottleLimit = $Throttle; NoOpen = $true }
    Show-VIARc 'R1' $rc $TimeoutSec
} else { Write-Host "[R1] SKIP(Accel20 收容缺)" -ForegroundColor Yellow }

# --- R2 合修(-Fix 才動;雙引擎皆自帶讓位備份) -----------------------
if ($Fix) {
    if ($accel) {
        Write-VIARound 'R2a Accel20 修' 2
        Write-Host "`n[R2a] Accel20 並行安全修(GO_v1;.psrepair.bak 讓位)…" -ForegroundColor Yellow
        $rc = Invoke-VIAChildPS -Name 'R2a Accel20 fix' -Script $accel -Timeout $TimeoutSec -Named @{
            Root = $VIA; OutRoot = $OutRoot; ExcludePattern = $Excl
            ThrottleLimit = $Throttle; GoToken = 'GO_v1'; NoOpen = $true }
        Show-VIARc 'R2a' $rc $TimeoutSec
    }
    if ($mdl101 -and $pyexe) {
        Write-VIARound 'R2b MDL101 修' 3
        Write-Host "[R2b] MDL101 fix(窄類+manifest+UNDO)…" -ForegroundColor Yellow
        $rc = Invoke-VIAChildExe -Name 'R2b MDL101 fix' -Exe $pyexe -CmdArgs @($mdl101, 'fix') -Timeout $TimeoutSec
        Show-VIARc 'R2b' $rc $TimeoutSec
    } elseif ($mdl101) {
        Write-Host "[R2b] SKIP(python 不在 PATH=誠實;先 via-envpy)" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[R2] DRY-RUN=不動檔(修復請加 -Fix)" -ForegroundColor DarkGray
}

# --- R3 驗證+啟動沙盒(非阻塞:只 parse 不執行) ---------------------
if ($verify) {
    Write-VIARound 'R3a 修後複驗' 4
    Write-Host "`n[R3a] PostRepairVerify(收容驗證器)…" -ForegroundColor Yellow
    $vn = @{ Root = $VIA; OutRoot = $OutRoot; NoOpen = $true }
    if ($pyexe) { $vn['PythonExe'] = $pyexe }   # 收容件預設為他機硬寫路徑,顯式覆蓋
    $rc = Invoke-VIAChildPS -Name 'R3a verify' -Script $verify -Timeout $TimeoutSec -Named $vn
    Show-VIARc 'R3a' $rc $TimeoutSec
}
if ($mdl101 -and $pyexe) {
    Write-VIARound 'R3b MDL101 掃描' 5
    Write-Host "[R3b] MDL101 scan 對照(RYG 四專區矩陣)…" -ForegroundColor Yellow
    $rc = Invoke-VIAChildExe -Name 'R3b MDL101 scan' -Exe $pyexe -CmdArgs @($mdl101, 'scan') -Timeout $TimeoutSec
    Show-VIARc 'R3b' $rc $TimeoutSec
}
Write-VIARound 'R3c 啟動沙盒' 6
Write-Host "[R3c] 啟動沙盒:VIA.ps1 AST parse(非阻塞)…" -ForegroundColor Yellow
$errs = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $VIA "VIA.ps1"), [ref]$null, [ref]$errs)
if (Get-Command Write-VIAProgress -ErrorAction SilentlyContinue) {
    Write-Progress -Id 12 -Activity 'VIA PS 修復三輪' -Completed
}
if ($errs -and $errs.Count -gt 0) {
    Write-Host ("  [R3c] RED:VIA.ps1 ParseError " + $errs.Count + " 處") -ForegroundColor Red
    $errs | ForEach-Object { Write-Host ("    L" + $_.Extent.StartLineNumber + " " + $_.Message) }
    exit 1
}
Write-Host "  [R3c] GREEN:VIA.ps1 AST parse 零錯(啟動沙盒過)" -ForegroundColor Green

$page = Join-Path $VIA "VIA_Reports\ps_repair\PS_REPAIR_MATRIX.html"
if (-not $NoOpen -and (Test-Path $page)) { Start-Process $page }
Write-Host "`n[計] 三輪畢 · 矩陣:$page + $OutRoot(Accel20 HTML)" -ForegroundColor Cyan
exit 0

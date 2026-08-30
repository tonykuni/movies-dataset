# =====================================================================
# Invoke-VIA-PSRepair-v0100.ps1 — PS 修復單一總入口(批253;操作員令
# 「one powershell to handle」Mega-Prompt+20 加速器)
# =====================================================================
# 統包三輪(現役 MDL101×收容 Accel20 雙引擎合流;收容件原地不動=駕馭):
#   R1 全景:收容 Invoke-VIA-PSRepair-Accel20(尾版)dry-run——真 PS AST
#      +20 加速器矩陣+PSScriptAnalyzer 橋(缺=誠實 NOT_INSTALLED)
#   R2 合修(-Fix 才動):①Accel20 -GoToken GO_v1(Parallel-Fixable+
#      .psrepair.bak 讓位)②python MDL101 fix(窄類+manifest+UNDO)
#   R3 驗證:收容 PostRepairVerify(尾版)+MDL101 scan 對照+啟動沙盒
#      =VIA.ps1 AST parse(非阻塞:只 parse 不執行)
#   輸出:Accel20 HTML 矩陣+MDL101 RYG 四專區矩陣+終端三態總結
# 用法:pwsh -File .\Invoke-VIA-PSRepair-v0100.ps1 [-Fix] [-NoOpen]
# =====================================================================
param([switch]$Fix, [switch]$NoOpen)
$ErrorActionPreference = "Continue"
$VIA = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutRoot = Join-Path $VIA "VIA_Reports\ps_repair\accel20"
$Excl = @('*\rollback\*', 'rb-*', '*\_bytecode_originals\*', '*\__pycache__\*',
          '*\node_modules\*', '*\90_PRIOR_PACKAGES\*', '*\VIA_Reports\*',
          '*\uploads\*', '*\.git\*')

function Get-NewestFile([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Recurse -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}

$intake = Join-Path $VIA "supportive modules\references\intake"
$accel = Get-NewestFile $intake "Invoke-VIA-PSRepair-Accel20-v*.ps1"
$verify = Get-NewestFile $intake "Invoke-VIA-PostRepairVerify-Accel20-v*.ps1"
$mdl101 = Get-NewestFile (Join-Path $VIA "supportive modules\registry") "CGC_MDL101_PSAstRepair_v*.py"

Write-Host "=== VIA PS 修復總入口 v0100(批253)· 雙引擎三輪 · $(if ($Fix) { 'FIX 模式' } else { 'DRY-RUN(加 -Fix 才動檔)' }) ===" -ForegroundColor Cyan
Write-Host ("  Accel20=" + $(if ($accel) { Split-Path $accel -Leaf } else { "缺(誠實;先 via-intake)" }))
Write-Host ("  Verify =" + $(if ($verify) { Split-Path $verify -Leaf } else { "缺(誠實)" }))
Write-Host ("  MDL101 =" + $(if ($mdl101) { Split-Path $mdl101 -Leaf } else { "缺(誠實)" }))

# --- R1 全景(真 AST+20 加速器;dry-run 永遠先跑) -------------------
if ($accel) {
    Write-Host "`n[R1] Accel20 全景掃描(真 PS AST+PSSA 橋+20 加速器矩陣)…" -ForegroundColor Yellow
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $accel -Root $VIA -OutRoot $OutRoot -ExcludePattern $Excl -NoOpen
    Write-Host ("  [R1] rc=" + $LASTEXITCODE)
} else { Write-Host "[R1] SKIP(Accel20 收容缺)" -ForegroundColor Yellow }

# --- R2 合修(-Fix 才動;雙引擎皆自帶讓位備份) -----------------------
if ($Fix) {
    if ($accel) {
        Write-Host "`n[R2a] Accel20 並行安全修(GO_v1;.psrepair.bak 讓位)…" -ForegroundColor Yellow
        & pwsh -NoProfile -ExecutionPolicy Bypass -File $accel -Root $VIA -OutRoot $OutRoot -ExcludePattern $Excl -GoToken "GO_v1" -NoOpen
        Write-Host ("  [R2a] rc=" + $LASTEXITCODE)
    }
    if ($mdl101) {
        Write-Host "[R2b] MDL101 fix(窄類+manifest+UNDO)…" -ForegroundColor Yellow
        & python $mdl101 fix
        Write-Host ("  [R2b] rc=" + $LASTEXITCODE)
    }
} else {
    Write-Host "`n[R2] DRY-RUN=不動檔(修復請加 -Fix)" -ForegroundColor DarkGray
}

# --- R3 驗證+啟動沙盒(非阻塞:只 parse 不執行) ---------------------
if ($verify) {
    Write-Host "`n[R3a] PostRepairVerify(收容驗證器)…" -ForegroundColor Yellow
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $verify -Root $VIA -OutRoot $OutRoot -NoOpen 2>$null
    Write-Host ("  [R3a] rc=" + $LASTEXITCODE + "(參數不合=誠實略,矩陣以 R3b/R3c 為準)")
}
if ($mdl101) {
    Write-Host "[R3b] MDL101 scan 對照(RYG 四專區矩陣)…" -ForegroundColor Yellow
    & python $mdl101 scan
}
Write-Host "[R3c] 啟動沙盒:VIA.ps1 AST parse(非阻塞)…" -ForegroundColor Yellow
$errs = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $VIA "VIA.ps1"), [ref]$null, [ref]$errs)
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

#requires -Version 7.0
# ============================================================================
# RUN_VIA_Deploy.ps1 — 自尋並執行 VIA_ActiveETF_Deploy（處理路徑/誤存.txt/封鎖/執行原則）
# 用法：在 PS7 執行  & "完整路徑\RUN_VIA_Deploy.ps1"   或雙擊（若已關聯 pwsh）
# 找不到 Deploy 時，會在 vetf / Downloads / modules 樹遞迴搜尋，含被存成 .ps1.txt 的情況。
# ============================================================================
param(
    [string]$Vetf = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf",
    [switch]$Install,
    [switch]$AddToPath,
    [string]$UpdateTime = ""
)

try { Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force } catch {}
$name = "VIA_ActiveETF_Deploy"

function Write-Status { param([string]$Level,[string]$Message)
    $c = switch ($Level.ToUpper()) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} default{"Cyan"} }
    Write-Host ("[{0}] {1}" -f $Level.ToUpper(), $Message) -ForegroundColor $c }

Write-Status INFO ("vetf = {0}" -f $Vetf)
if (Test-Path $Vetf) {
    Write-Host "== 目前 vetf 內容 ==" -ForegroundColor Cyan
    Get-ChildItem -LiteralPath $Vetf -File | Select-Object Name, @{n='KB';e={[int]($_.Length/1KB)}}, LastWriteTime | Format-Table -AutoSize
} else { Write-Status FAIL "資料夾不存在：$Vetf"; exit 1 }

$dirs = @($Vetf, (Join-Path $env:USERPROFILE 'Downloads'),
          "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules") | Where-Object { Test-Path $_ }
$hit = $null
foreach ($d in $dirs) {
    $f = Get-ChildItem -LiteralPath $d -Recurse -Depth 3 -File -Filter "$name*" -ErrorAction SilentlyContinue |
         Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($f) { $hit = $f; break }
}
if (-not $hit) {
    Write-Status FAIL "找不到 $name 腳本。"
    Write-Status WARN ("請把 VIA_ActiveETF_Deploy.ps1 存到 {0}（存檔類型選 All Files，副檔名 .ps1 而非 .txt）。" -f $Vetf)
    exit 1
}
$target = Join-Path $Vetf "$name.ps1"
if ($hit.Extension -ne '.ps1' -or $hit.FullName -ne $target) {
    Copy-Item -LiteralPath $hit.FullName -Destination $target -Force
    Write-Status OK ("已正規化為 .ps1：{0}（來源 {1}）" -f $target, $hit.Name)
}
Unblock-File -LiteralPath $target -ErrorAction SilentlyContinue

$pass = @()
if ($Install)   { $pass += "-Install" }
if ($AddToPath) { $pass += "-AddToPath" }
if ($UpdateTime){ $pass += @("-UpdateTime",$UpdateTime) }
Write-Status INFO ("執行：{0} {1}" -f (Split-Path $target -Leaf), ($pass -join ' '))
& $target @pass
exit $LASTEXITCODE

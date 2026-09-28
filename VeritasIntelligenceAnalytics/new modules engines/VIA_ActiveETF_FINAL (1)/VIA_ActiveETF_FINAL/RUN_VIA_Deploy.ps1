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
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====


try { Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force } catch {}
$name = "VIA_ActiveETF_Deploy"

function Write-Status { param([string]$Level,[string]$Message)
    $c = switch ($Level.ToUpper()) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} default{"Cyan"} }
    Write-Host ("[{0}] {1}" -f $Level.ToUpper(), $Message) -ForegroundColor $c }

Write-Status INFO ("vetf = {0}" -f $Vetf)
if (Test-Path $Vetf) {
    Write-Host "== 目前 vetf 內容 ==" -ForegroundColor Cyan
    Get-ChildItem -LiteralPath $Vetf -File | Select-Object Name, @{n='KB';e={[int]($_.Length/1KB)}}, LastWriteTime | Format-Table -AutoSize
} else { Write-Status FAIL "資料夾不存在：$Vetf"; if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; exit 1 }

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
    if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; exit 1
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
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; exit $LASTEXITCODE
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit

# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# ===== [VIA:PS-TEMPLATE:v0100] Celeritas 模板章(L102 ②;不包裹接法 L103 ③:不 cd、不動 param()、只動 $PID、關閉即還原;模板 StrictMode 不外溢) =====
try {
    $VIACelProbe = $PSScriptRoot
    while ($VIACelProbe -and (Split-Path $VIACelProbe -Parent)) {
        $VIACelPS7 = Join-Path $VIACelProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
        if (Test-Path -LiteralPath $VIACelPS7) { . $VIACelPS7 -RestoreOnly; break }
        $VIACelProbe = Split-Path $VIACelProbe -Parent
    }
    Set-StrictMode -Off
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) {
        if (-not (Get-EventSubscriber -SourceIdentifier PowerShell.Exiting -ErrorAction SilentlyContinue)) { $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { try { Restore-CeleritasPS7 } catch { } } }
        [void](Start-CeleritasPS7)
    }
} catch { }
# ===== [VIA:PS-TEMPLATE:END] =====
#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath (Split-Path -Parent $via)
$env:VIA_FROM_VCGC = "YES"
if (-not $env:VIA_VRN_SAMPLES) { $env:VIA_VRN_SAMPLES = "C:\測試樣本報告" }
$folder = Join-Path $via "functional modules/VRN"
$eng = Get-ChildItem -LiteralPath $folder -Filter "VRN_ENG110_TabReport_v*.py" | Sort-Object Name | Select-Object -Last 1
if (-not $eng) { throw "VRN_ENG110_TabReport 不在這棵樹" }
$py = "python"
foreach ($cand in @(
        (Join-Path $env:USERPROFILE "envs\via_vrn_312\Scripts\python.exe"),
        (Join-Path $env:USERPROFILE "envs\via_vdf_312\Scripts\python.exe"),
        "python")) {
    if (-not (Test-Path -LiteralPath $cand) -and -not (Get-Command $cand -ErrorAction SilentlyContinue)) { continue }
    & $cand -c "import fitz" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $cand; break }
}
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& $py $eng.FullName
$code = $LASTEXITCODE
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原
exit $code
if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原

# =============================================================================
# def VAP ACTIVE ENTRY · Fullscreen HMI Auto Layout Editor
# =============================================================================
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
$VapBase = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VAP"
$ActiveEditor = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VAP\TEMPLATE_WORKBENCH\VIA_VAP_Template_Workbench_Fullscreen_HMI_AutoLayoutEditor.html"
$FallbackMaster = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VAP\COCKPIT\VAP_Master_Cockpit.html"
$FallbackGallery = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VAP\COCKPIT\VAP_Gallery_Cockpit.html"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "def VAP ACTIVE ENTRY · Fullscreen HMI Auto Layout Editor" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ("VAP Base : {0}" -f $VapBase)

$opened = $false

if (Test-Path -LiteralPath $ActiveEditor) {
    Start-Process -FilePath $ActiveEditor
    $opened = $true
} elseif (Test-Path -LiteralPath $FallbackMaster) {
    Start-Process -FilePath $FallbackMaster
    $opened = $true
} elseif (Test-Path -LiteralPath $FallbackGallery) {
    Start-Process -FilePath $FallbackGallery
    $opened = $true
}

Write-Host ("Opened   : {0}" -f $opened)
Write-Host "Active   : Fullscreen HMI Auto Layout Editor"
Write-Host "Policy   : No Stop-Process. No browser close. No PowerShell close."
Write-Host "PowerShell session remains open." -ForegroundColor Cyan

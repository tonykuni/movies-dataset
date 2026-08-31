# VRN · Safe Stream 01 · ParserOnly
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
$Target = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\60_PowerShell_Entry_Internal\Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
if(-not $Target -or -not(Test-Path -LiteralPath $Target -PathType Leaf)){ Write-Host "[WARN] Missing target: $Target" -ForegroundColor Yellow; return }
$tokens=$null; $errors=$null
[System.Management.Automation.Language.Parser]::ParseFile($Target,[ref]$tokens,[ref]$errors)|Out-Null
if(@($errors).Count -eq 0){ Write-Host "[OK] ParserOnly passed." -ForegroundColor Green } else { Write-Host "[FAIL] Parser errors: $(@($errors).Count)" -ForegroundColor Red; @($errors | Select-Object -First 10) | ForEach-Object { Write-Host $_.Message -ForegroundColor Red } }
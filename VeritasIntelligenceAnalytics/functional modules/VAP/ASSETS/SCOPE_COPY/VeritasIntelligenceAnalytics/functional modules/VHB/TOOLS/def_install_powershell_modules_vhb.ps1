# def Install PowerShell modules for CurrentUser
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
$ErrorActionPreference = 'Continue'
$Mods = @(
  "PSScriptAnalyzer",
  "Pester",
  "ImportExcel",
  "PSWriteHTML",
  "ThreadJob",
  "powershell-yaml",
  "platyPS",
  "PSFramework",
  "Pode",
  "BurntToast"
)
foreach ($m in $Mods) {
    try {
        if (-not (Get-Module -ListAvailable -Name $m)) {
            Install-Module $m -Scope CurrentUser -Force -AllowClobber
        }
        Import-Module $m -ErrorAction SilentlyContinue
        Write-Host "[OK] $m"
    } catch {
        Write-Host "[WARN] $m :: $($_.Exception.Message)"
    }
}


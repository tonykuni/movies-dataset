# def Install PowerShell modules for CurrentUser
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

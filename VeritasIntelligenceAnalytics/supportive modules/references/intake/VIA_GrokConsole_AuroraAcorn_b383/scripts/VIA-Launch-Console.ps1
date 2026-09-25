#requires -Version 7.0
# VIA Central Governance Console · 本機啟動探針
# 協調 GitHub × 母檔 × Data × via_core × via_* × engine/module/lib
# 三色: GREEN / YELLOW / RED    政策: 不刪、不殺行程、預設禁網、不 exit
$ErrorActionPreference = "Continue"

$Roots = @(
    "C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics",
    "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics",
    "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics"
)
$Root = $Roots | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Root) {
    Write-Host "RED     Mother root not found" -ForegroundColor Red
    $Roots | ForEach-Object { Write-Host "        $_" }
    return
}
Set-Location -LiteralPath $Root
Write-Host "GREEN   ENTER  $Root" -ForegroundColor Green

function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { "GREEN" { "Green" } "RED" { "Red" } default { "Yellow" } }
    Write-Host ("{0,-7} {1,-12} {2}" -f $c, $layer, $msg) -ForegroundColor $col
}

# GitHub
$git = Join-Path $Root ".git"
if (Test-Path $git) {
    $br = (git -C $Root rev-parse --abbrev-ref HEAD 2>$null)
    $rem = (git -C $Root remote get-url origin 2>$null)
    Lamp "GREEN" "GitHub" "$br  $rem"
} else {
    Lamp "YELLOW" "GitHub" "no .git · 用 clone tonykuni/movies-dataset 對帳"
}

# Mother / Data
$vdf = Join-Path $Root "functional modules\VDF"
$data = Join-Path $Root "dict\VDF\DATABASE"
Lamp $(if (Test-Path $vdf) { "GREEN" } else { "YELLOW" }) "Mother" "functional modules\VDF"
Lamp $(if (Test-Path $data) { "GREEN" } else { "YELLOW" }) "Data" "dict\VDF\DATABASE"

# via_core / via_* conda
$viaCore = @(
    (Join-Path $Root "via_core"),
    (Join-Path $Root "supportive modules")
) | Where-Object { Test-Path $_ } | Select-Object -First 1
Lamp $(if ($viaCore) { "GREEN" } else { "YELLOW" }) "via_core" $(if ($viaCore) { $viaCore } else { "not on disk" })

$envs = @()
if (Get-Command conda -ErrorAction SilentlyContinue) {
    $envs = @(conda env list 2>$null | Select-String -Pattern '^via_')
}
if ($envs.Count -gt 0) { Lamp "GREEN" "via_env" ($envs -join "; ") }
else { Lamp "YELLOW" "via_env" "no via_* conda env visible in this shell" }

# engine / module / lib
$eng = Join-Path $vdf "engine"
$lib = Join-Path $Root "supportive modules"
Lamp $(if (Test-Path $eng) { "GREEN" } else { "YELLOW" }) "engine" $eng
Lamp $(if (Test-Path (Join-Path $Root "functional modules\VRN")) { "GREEN" } else { "YELLOW" }) "module" "VDF+VRN"
Lamp $(if (Test-Path $lib) { "GREEN" } else { "YELLOW" }) "lib" "supportive modules"

$inv = Join-Path $vdf "Invoke-VDF.ps1"
$fet = Join-Path $vdf "Invoke-VDF-Fetch.ps1"
if (Test-Path $inv) { Write-Host "`n--- Invoke-VDF status ---"; & $inv status }
if (Test-Path $fet) { Write-Host "`n--- Invoke-VDF-Fetch status (network disabled) ---"; & $fet status }

Write-Host "`nYELLOW  Console UI is the Grok preview (唯一總管). This script only probes PC." -ForegroundColor Yellow
Get-Location | Format-List

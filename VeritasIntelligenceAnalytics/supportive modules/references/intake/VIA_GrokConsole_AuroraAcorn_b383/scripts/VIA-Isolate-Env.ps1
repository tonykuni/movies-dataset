#requires -Version 7.0
# VIA isolate · 母機雙閘後才跑
# 政策: 衝突件隔離不刪、不卸載、不殺行程、不 exit
$ErrorActionPreference = "Stop"

$Lock = Join-Path $PSScriptRoot "..\locks"
if (-not (Test-Path -LiteralPath $Lock)) { New-Item -ItemType Directory -Path $Lock | Out-Null }

Write-Host "ISO  numpy  via_vdf@2.1.1 vs base@1.26.4  -> via_iso_numpy"
conda create -n via_iso_numpy python=3.11 numpy==2.1.1 --yes
conda env export -n via_vdf --no-builds | Out-File -Encoding utf8 (Join-Path $Lock "via_vdf.yml")
conda env update -n via_vdf -f (Join-Path $Lock "via_vdf.yml") --prune
conda run -n via_iso_numpy python -c "import numpy as m; print(m.__version__)"
Write-Host "ISO  DONE · base 未刪 · 衝突件在 via_iso_*"
return

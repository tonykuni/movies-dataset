# Start VDF through VCGC. Status only. No fetch.
$ErrorActionPreference = "Stop"
$env:VIA_FROM_VCGC = "YES"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $via "supportive modules\registry\CGC_MDL209_VdfStart_v0100.py"
python $py
exit $LASTEXITCODE

#Requires -Version 7.0
# CELERITAS-TEMPLATE-JOIN v1
[CmdletBinding()]
param(
    [string[]]$Roots = @('C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics', 'C:\Users\tonyk\OneDrive\Documents\movies-dataset'),
    [string]$ViaRoot = '',
    [string]$Python = '',
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'VIA\VCGC_Panorama_v0101'),
    [ValidateRange(1,16)][int]$Workers = 4,
    [ValidateRange(30,86400)][int]$StepTimeout = 1800,
    [ValidateRange(300,172800)][int]$FullTestTimeout = 43200,
    [switch]$ReuseReceipts,
    [switch]$ForceFull,
    [switch]$IncludeDependencies,
    [switch]$NoOpen
)
$ErrorActionPreference = 'Stop'
$script:RunCode = 1
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$run = Join-Path $OutputRoot $stamp
$null = New-Item -ItemType Directory -Path $run -Force
$bootstrap = [ordered]@{version='v0100'; at=(Get-Date).ToUniversalTime().ToString('o'); ps_version=$PSVersionTable.PSVersion.ToString(); pid=$PID; bridge='ABSENT'; celeritas='ABSENT'; errors=@()}
try {
    if (-not $ViaRoot) {
        foreach ($root in (@($Roots | Select-Object -Last 1) + @($Roots))) {
            foreach ($candidate in @((Join-Path $root 'VeritasIntelligenceAnalytics'), $root)) {
                if (Test-Path -LiteralPath (Join-Path $candidate 'supportive modules\registry\VIA_ToolVersion_Lock_v0100.json')) { $ViaRoot=$candidate; break }
            }
            if ($ViaRoot) { break }
        }
    }
    if (-not $ViaRoot) { throw '找不到 VCGC 的工具鎖冊。請用 -ViaRoot 指向含 supportive modules 的 VIA 目錄。' }
    $ViaRoot = (Resolve-Path -LiteralPath $ViaRoot).Path
    $bootstrap.via_root = $ViaRoot
    # [VIA:PS-ACCEL:v0101] Existing bridge; record actual load failure.
    $bridge = Join-Path $ViaRoot 'supportive modules\VIA_PS_Accel_Module.ps1'
    if (Test-Path -LiteralPath $bridge) {
        try { . $bridge; $bootstrap.bridge='LOADED' } catch { $bootstrap.errors += "PS bridge: $_" }
    }
    # [VIA:PS-TEMPLATE:v0100] Apply the existing template to this process only.
    $template = Join-Path $ViaRoot 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
    if (Test-Path -LiteralPath $template) {
        try {
            . $template -RestoreOnly
            Set-StrictMode -Off
            if (Get-Command Start-CeleritasPS7 -ErrorAction SilentlyContinue) {
                $null = Start-CeleritasPS7
                $bootstrap.celeritas='START_RETURNED'
            }
        } catch { $bootstrap.errors += "Celeritas PS7: $_" }
    }
    $bootstrap | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $run 'PS_BOOTSTRAP.json') -Encoding utf8
    $pythonPrefix = @()
    if (-not $Python) {
        $probes = @()
        if ($env:VIRTUAL_ENV) { $probes += (Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe') }
        foreach ($root in (@($ViaRoot) + $Roots)) {
            foreach ($name in @('via_core','via_core_312')) {
                $probes += (Join-Path $root "$name\Scripts\python.exe")
                $probes += (Join-Path $root ".venvs\$name\Scripts\python.exe")
                $probes += (Join-Path $root "venvs\$name\Scripts\python.exe")
            }
        }
        foreach ($p in $probes) { if (Test-Path -LiteralPath $p) { $Python=$p; break } }
        if (-not $Python) {
            $pc = Get-Command python -ErrorAction SilentlyContinue
            if ($pc) { $Python=$pc.Source }
        }
        if (-not $Python) {
            $pc = Get-Command py -ErrorAction SilentlyContinue
            if ($pc) { $Python=$pc.Source; $pythonPrefix=@('-3.12') }
        }
    }
    if (-not $Python) { throw '找不到 Python。請用 -Python 指定既有 via_core 的 Scripts\python.exe。' }
    & $Python @pythonPrefix -c 'import sys; print(sys.executable); assert sys.version_info >= (3,11), "Python 3.11+ required"'
    if ($LASTEXITCODE -ne 0) { throw 'Python 啟動失敗；未安裝或變更任何環境。' }
    $runner = Join-Path $PSScriptRoot 'VCGC_Panorama_v0101.py'
    if (-not (Test-Path -LiteralPath $runner)) { throw '請完整解壓縮 ZIP，PS1 與 PY 必須放在同一資料夾。' }
    $invokeArgs = @($runner,'--via-root',$ViaRoot,'--out',$run,'--workers',"$Workers",'--step-timeout',"$StepTimeout",'--full-timeout',"$FullTestTimeout",'--pwsh',(Join-Path $PSHOME 'pwsh.exe'))
    foreach ($root in $Roots) { $invokeArgs += @('--root',$root) }
    if ($ReuseReceipts) { $invokeArgs += '--reuse-receipts' }
    if ($ForceFull) { $invokeArgs += '--force-full' }
    if ($IncludeDependencies) { $invokeArgs += '--include-dependencies' }
    Write-Host "理 · VIA / VCGC 全景檢查 v0101" -ForegroundColor Cyan
    Write-Host "作用中目錄：$ViaRoot"
    Write-Host "完整日誌與矩陣：$run"
    & $Python @pythonPrefix @invokeArgs
    $script:RunCode = $LASTEXITCODE
} catch {
    $bootstrap.errors += "$_"
    $bootstrap | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $run 'PS_BOOTSTRAP.json') -Encoding utf8
    Write-Host "[BLOCKED] $_" -ForegroundColor Red
} finally {
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) {
        try { Restore-CeleritasPS7 } catch { Write-Warning "加速器還原：$_" }
    }
    $page = Join-Path $run 'VCGC_PANORAMA.html'
    if ((-not $NoOpen) -and (Test-Path -LiteralPath $page)) { Start-Process -FilePath $page }
    Write-Host "完成狀態碼：$script:RunCode；報告：$run" -ForegroundColor Yellow
    Write-Host '0=本次檢查通過；1=失敗/阻擋；2=有待確認項。PowerShell 視窗保留。'
    $global:LASTEXITCODE = $script:RunCode
}

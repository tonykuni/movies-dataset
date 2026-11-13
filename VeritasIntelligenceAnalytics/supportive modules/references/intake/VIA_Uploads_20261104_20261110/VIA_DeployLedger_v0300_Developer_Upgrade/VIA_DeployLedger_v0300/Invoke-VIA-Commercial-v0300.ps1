#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$PythonPath = '',
    [string]$Contract = '',
    [string]$Job = '',
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'VIA\DeployLedger'),
    [switch]$Repair,
    [switch]$NoBrowser
)
# [VIA:ACCEL-BRIDGE] conservative process budget; canonical accelerator probe is required by the deploy contract.
$ErrorActionPreference = 'Stop'
$CandidateEnvs = @('via_core','via_core_312','via_extract_312')
$ThreadBudget = [Math]::Max(1, [Math]::Min(4, [int]([Environment]::ProcessorCount / 2)))
$env:OMP_NUM_THREADS = [string]$ThreadBudget
$env:OPENBLAS_NUM_THREADS = [string]$ThreadBudget
$env:MKL_NUM_THREADS = [string]$ThreadBudget
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONNOUSERSITE = '1'
$RunOutput = Join-Path $OutputRoot (Get-Date -Format 'yyyyMMdd_HHmmss_fff')
$Engine = Join-Path $PSScriptRoot 'VIA_DeployLedger_v0300.py'

function Find-VIAPython {
    if ($PythonPath) {
        if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw '指定 Python 不存在。' }
        return $PythonPath
    }
    foreach ($alias in $CandidateEnvs) {
        $candidate = Join-Path $env:USERPROFILE "envs\$alias\Scripts\python.exe"
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    throw '找不到既有 via_ 環境；請透過 VCGC 建立／修復環境，或用 -PythonPath 指定。'
}

function Invoke-VIACommercial {
    $py = Find-VIAPython
    $activate = Join-Path (Split-Path $py) 'Activate.ps1'
    if (Test-Path -LiteralPath $activate) { . $activate }
    New-Item -ItemType Directory -Path $RunOutput -Force | Out-Null
    & $py -I -c 'import cryptography; print("Cryptography ready")' | Out-Host
    if ($LASTEXITCODE -ne 0) { throw '現有環境缺 cryptography；交 VCGC InstallGate 處理，本啟動器不直接 pip。' }
    if ($Job) {
        $arguments = @($Engine, 'pipeline', '--job', $Job, '--output', $RunOutput)
    } elseif ($Contract) {
        $arguments = @($Engine, 'prepare', '--contract', $Contract, '--output', $RunOutput)
        if ($Repair) { $arguments += '--repair' }
    } else {
        $arguments = @($Engine, 'discover', '--output', $RunOutput)
    }
    Write-Progress -Activity 'VIA 商業部署升級' -Status 'VCGC 現況、部署基線與授權檢查' -PercentComplete 10
    & $py @arguments 2>&1 | Tee-Object -FilePath (Join-Path $RunOutput 'console.log') | Out-Host
    $code = $LASTEXITCODE
    Write-Progress -Activity 'VIA 商業部署升級' -Completed
    $page = Join-Path $RunOutput 'Deployment_Status.html'
    if ((Test-Path -LiteralPath $page) -and -not $NoBrowser) { Start-Process -FilePath $page }
    Write-Host "結果目錄：$RunOutput"
    Write-Host "Exit code：$code（0=本階段成功；2=需補完整部署契約／有阻擋；3=驗證失敗）"
    return $code
}

try { $global:VIADeployExitCode = Invoke-VIACommercial }
catch { Write-Host ('BLOCKED：' + $_.Exception.Message) -ForegroundColor Yellow; $global:VIADeployExitCode = 3 }
# Do not exit the PowerShell window. The CMD entrypoint uses -NoExit.

param(
    [string]$PythonPath = '',
    [string]$RunRoot = (Join-Path $PSScriptRoot 'runs'),
    [string]$EnvironmentPath = (Join-Path $PSScriptRoot 'envs\via_vrn_annual_v0108'),
    [switch]$InstallDependencies
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
function Invoke-VRNPackVerification {
    param([string]$SeedPython, [string]$RunBase, [string]$ViaEnvironment, [bool]$Install)
    $Pack = Join-Path $PSScriptRoot 'pack'
    $Verifier = Join-Path $PSScriptRoot 'tools\VerifyPack_v0108.py'
    $RunId = (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + ([guid]::NewGuid().ToString('N').Substring(0,6))
    $RunDirectory = Join-Path $RunBase $RunId
    $Results = Join-Path $RunDirectory 'results'
    $StatePath = Join-Path $RunDirectory 'RUN_STATUS.json'
    $Stage = 'PRECHECK'
    $Lock = $null
    New-Item -ItemType Directory -Path $RunDirectory -Force | Out-Null
    try {
        $Lock = [System.IO.File]::Open((Join-Path $PSScriptRoot 'RUN.lock'), [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
        @{status='RUNNING'; stage=$Stage; run_id=$RunId; results=$Results} | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding utf8
        Write-Progress -Activity 'VRN 安裝、重跑及驗證' -Status '尋找 Python 3.12' -PercentComplete 5
        $Candidates = @()
        if ($SeedPython) { $Candidates += $SeedPython }
        if ($env:VIRTUAL_ENV) { $Candidates += (Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe') }
        $Candidates += (Join-Path $env:USERPROFILE 'envs\via_vrn_312\Scripts\python.exe')
        $Candidates += (Join-Path $env:USERPROFILE 'envs\via_core\Scripts\python.exe')
        $Command = Get-Command python -ErrorAction SilentlyContinue
        if ($Command) { $Candidates += $Command.Source }
        $Python = $null
        foreach ($Candidate in ($Candidates | Select-Object -Unique)) {
            if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) { continue }
            $Version = & $Candidate -X utf8 -c "import sys; print('3.12' if sys.version_info[:2] == (3,12) else 'UNSUPPORTED')"
            if ($LASTEXITCODE -eq 0 -and $Version -eq '3.12') { $Python = $Candidate; break }
        }
        if (-not $Python) { throw '找不到 Python 3.12；請用 -PythonPath 指定。' }
        & $Python -X utf8 $Verifier --pack $Pack --integrity-only --receipt (Join-Path $RunDirectory 'PRECHECK.json')
        if ($LASTEXITCODE -ne 0) { throw '原始封裝完整性未通過，停止執行。' }
        $Stage = 'ENVIRONMENT'
        Write-Progress -Activity 'VRN 安裝、重跑及驗證' -Status '準備獨立 via_ 環境' -PercentComplete 15
        $EnvPython = Join-Path $ViaEnvironment 'Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $EnvPython -PathType Leaf)) {
            if (-not $Install) { throw '尚無專用環境；首次請加 -InstallDependencies。' }
            & $Python -m venv $ViaEnvironment
            if ($LASTEXITCODE -ne 0) { throw '專用環境建立失敗。' }
        }
        $EnvVersion = & $EnvPython -c "import sys; print('3.12' if sys.version_info[:2] == (3,12) else 'UNSUPPORTED')"
        if ($LASTEXITCODE -ne 0 -or $EnvVersion -ne '3.12') { throw '專用環境不是 Python 3.12。' }
        if ($Install) {
            & $EnvPython -m pip install -r (Join-Path $Pack 'requirements_annual.txt') 2>&1 | Tee-Object -FilePath (Join-Path $RunDirectory 'install.log')
            if ($LASTEXITCODE -ne 0) { throw '依賴套件安裝失敗。' }
        }
        & $EnvPython -m pip check 2>&1 | Tee-Object -FilePath (Join-Path $RunDirectory 'pip_check.log')
        if ($LASTEXITCODE -ne 0) { throw '環境相依性衝突。' }
        & $EnvPython -X utf8 -c "import fitz,pdfplumber,polars,openpyxl,reportlab,fontTools,numpy,pandas,docx,PIL; print('IMPORT_PASS')"
        if ($LASTEXITCODE -ne 0) { throw '必要函式庫載入失敗。' }
        $Stage = 'ANNUAL_ENGINE'
        Write-Progress -Activity 'VRN 安裝、重跑及驗證' -Status '重讀 43 表並完成年度驗算' -PercentComplete 35
        & $EnvPython -X utf8 (Join-Path $PSScriptRoot 'tools\RunAnnual_v0108.py') --dispatcher-root (Join-Path $Pack 'engine') --input-root (Join-Path $Pack 'inputs') --output-root $Results 2>&1 | Tee-Object -FilePath (Join-Path $RunDirectory 'engine.log')
        if ($LASTEXITCODE -ne 0) { throw '年度引擎或品質閘門未通過。' }
        $Stage = 'VERIFY_RESULTS'
        Write-Progress -Activity 'VRN 安裝、重跑及驗證' -Status '獨立核對資料、Excel、PDF 與引擎原檔' -PercentComplete 85
        & $EnvPython -X utf8 $Verifier --pack $Pack --results $Results --receipt (Join-Path $RunDirectory 'RESULT_VERIFICATION.json') 2>&1 | Tee-Object -FilePath (Join-Path $RunDirectory 'verification.log')
        if ($LASTEXITCODE -ne 0) { throw '獨立結果驗證未通過。' }
        @{status='PASS_WITH_SOURCE_LIMITATIONS'; stage='DONE'; run_id=$RunId; results=$Results; completed_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding utf8
        Write-Progress -Activity 'VRN 安裝、重跑及驗證' -Status '完成' -PercentComplete 100
        Write-Host ('PASS_WITH_SOURCE_LIMITATIONS：' + $RunDirectory)
        Write-Host 'GS 缺值及 CLST 原文矛盾仍保留。請再人工檢視 PDF 裁切與 Excel 還原表。'
        $global:LASTEXITCODE = 0
    }
    catch {
        @{status='FAIL'; stage=$Stage; run_id=$RunId; error=$_.Exception.Message; results=$Results; failed_at=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding utf8
        Write-Host ('FAIL [' + $Stage + '] ' + $_.Exception.Message) -ForegroundColor Red
        Write-Host ('紀錄：' + $RunDirectory)
        $global:LASTEXITCODE = 1
    }
    finally {
        if ($Lock) { $Lock.Dispose() }
        Write-Progress -Activity 'VRN 安裝、重跑及驗證' -Completed
    }
}
Invoke-VRNPackVerification -SeedPython $PythonPath -RunBase $RunRoot -ViaEnvironment $EnvironmentPath -Install ([bool]$InstallDependencies)

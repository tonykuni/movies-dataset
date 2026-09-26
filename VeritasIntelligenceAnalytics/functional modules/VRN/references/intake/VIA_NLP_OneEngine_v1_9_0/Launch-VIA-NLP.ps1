param(
    [string]$InputPath = '',
    [string]$ViaEnv = (Join-Path $env:USERPROFILE 'envs\via_nlp_v190'),
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'VIA\NLP190'),
    [string]$ConfigPath = ''
)

# Parameters above are the only user-adjustable settings.
$ErrorActionPreference = 'Stop'
$EnginePath = Join-Path $PSScriptRoot 'VIA_NLP_OneEngine_v1_9_0.py'
$PythonPath = Join-Path $ViaEnv 'Scripts\python.exe'
$RunDirectory = Join-Path $OutputRoot (Get-Date -Format 'yyyyMMdd_HHmmss_ffff')

try {
    if (-not (Test-Path -LiteralPath $EnginePath -PathType Leaf)) {
        throw "找不到單檔引擎：$EnginePath"
    }
    Write-Progress -Activity 'VIA NLP OneEngine' -Status '準備專用環境' -PercentComplete 10
    if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            & uv venv --python 3.12 --no-python-downloads $ViaEnv
        } elseif (Get-Command py -ErrorAction SilentlyContinue) {
            & py -3.12 -m venv $ViaEnv
        } else {
            throw '需要已安裝的 Python 3.12 與 uv 或 py launcher；本啟動器不自動下載 Python。'
        }
        if ($LASTEXITCODE -ne 0) { throw '建立 via_nlp_v190 環境失敗。' }
    }
    . (Join-Path $ViaEnv 'Scripts\Activate.ps1')
    & $PythonPath -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
    if ($LASTEXITCODE -ne 0) { throw 'Python 版本不符。' }
    New-Item -ItemType Directory -Path $RunDirectory -Force | Out-Null
    Write-Progress -Activity 'VIA NLP OneEngine' -Status '執行內建驗證' -PercentComplete 35
    & $PythonPath $EnginePath self-test --output $RunDirectory |
        Out-File -LiteralPath (Join-Path $RunDirectory 'selftest_console.json') -Encoding utf8
    if ($LASTEXITCODE -ne 0) {
        Start-Process (Join-Path $RunDirectory 'matrix.html')
        throw "核心測試未通過，請查看：$RunDirectory"
    }
    Write-Progress -Activity 'VIA NLP OneEngine' -Status '處理輸入與產生報告' -PercentComplete 75
    if ($InputPath) {
        if (-not (Test-Path -LiteralPath $InputPath)) { throw "找不到輸入：$InputPath" }
        $EngineArguments = @()
        if ($ConfigPath) { $EngineArguments += @('--config', $ConfigPath) }
        if (Test-Path -LiteralPath $InputPath -PathType Container) {
            $EngineArguments += @('batch', '--input', $InputPath, '--output', (Join-Path $RunDirectory 'analysis'))
        } elseif ([IO.Path]::GetExtension($InputPath) -in @('.csv','.tsv','.jsonl','.ndjson')) {
            $EngineArguments += @('batch', '--input', $InputPath, '--output', (Join-Path $RunDirectory 'analysis'))
        } else {
            $EngineArguments += @('process', '--file', $InputPath, '--output', (Join-Path $RunDirectory 'analysis'), '--markdown-analysis', '--analysis-task', 'knowledge')
        }
        & $PythonPath $EnginePath @EngineArguments |
            Out-File -LiteralPath (Join-Path $RunDirectory 'analysis_console.json') -Encoding utf8
        if ($LASTEXITCODE -ne 0) { throw "分析含錯誤，檢查點與報告已保留於：$RunDirectory" }
        $Report = Get-ChildItem -LiteralPath (Join-Path $RunDirectory 'analysis') -Filter matrix.html -Recurse |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($Report) { Start-Process $Report.FullName }
    } else {
        Start-Process (Join-Path $RunDirectory 'matrix.html')
    }
    Write-Host "VIA NLP 完成：$RunDirectory"
} finally {
    Write-Progress -Activity 'VIA NLP OneEngine' -Completed
}
# Deliberately no exit, Stop-Process, global package installation, or source overwrite.

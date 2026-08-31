param(
    [string]$Python = "python",
    [string]$Config = "",
    [switch]$InstallDependencies,
    [switch]$InstallBrowserTests,
    [switch]$RunTests,
    [switch]$NoBrowser,
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeFile = Join-Path $PackageRoot "runtime\vap_data_runtime_v025.py"
$VdfManifestTool = Join-Path $PackageRoot "runtime\vap_vdf_manifest_tool_v025.py"
$RequirementsFile = Join-Path $PackageRoot "runtime\requirements-v025.txt"
if (-not $Config) { $Config = Join-Path $PackageRoot "config\vap_runtime_config.json" }

function def_Write-Step([string]$Text) {
    Write-Host ("[VAP v025] " + $Text) -ForegroundColor Cyan
}

function def_Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "必要檔案不存在：$Path" }
}

function def_Get-PythonVersion {
    $Output = & $Python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    if ($LASTEXITCODE -ne 0) { throw "無法執行 Python：$Python" }
    return $Output.Trim()
}

function def_Wait-Health([int]$Port = 8765) {
    $Endpoint = "http://127.0.0.1:$Port/api/health"
    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
        try {
            $Health = Invoke-RestMethod -Uri $Endpoint -TimeoutSec 2
            if ($Health.status -eq "READY") { return $Health }
        } catch { Start-Sleep -Milliseconds 250 }
    }
    throw "Runtime 未在預期時間內就緒：$Endpoint"
}

def_Assert-File $RuntimeFile
def_Assert-File $VdfManifestTool
def_Assert-File $Config
$PythonVersion = def_Get-PythonVersion
def_Write-Step "Python $PythonVersion"

if ($InstallDependencies) {
    def_Assert-File $RequirementsFile
    def_Write-Step "安裝 DuckDB／Parquet 選用套件"
    & $Python -m pip install -r $RequirementsFile
    if ($LASTEXITCODE -ne 0) { throw "選用套件安裝失敗" }
}

if ($InstallBrowserTests) {
    $Npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $Npm) { throw "安裝瀏覽器測試需要 Node.js 與 npm" }
    def_Write-Step "安裝 Playwright 測試套件；沿用本機 Chrome／Edge，不下載瀏覽器"
    & npm install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "Playwright 測試套件安裝失敗" }
}

def_Write-Step "執行 Runtime 自我檢查"
def_Write-Step "驗證 VDF 授權 Manifest 與 Fingerprint"
& $Python $VdfManifestTool
if ($LASTEXITCODE -ne 0) { throw "VDF Manifest 驗證失敗" }
& $Python $RuntimeFile --config $Config --run-self-test
if ($LASTEXITCODE -ne 0) { throw "Runtime 自我檢查失敗" }

if ($RunTests) {
    def_Write-Step "執行完整套件測試"
    & $Python (Join-Path $PackageRoot "tests\run_all_tests_v025.py")
    if ($LASTEXITCODE -ne 0) { throw "完整套件測試失敗" }
}

$Arguments = @($RuntimeFile, "--config", $Config, "--sync-connect")
if ($NoBrowser) { $Arguments += "--no-browser" }
if ($Background) {
    def_Write-Step "背景啟動唯讀 Runtime"
    $Process = Start-Process -FilePath $Python -ArgumentList $Arguments -WorkingDirectory $PackageRoot -PassThru
    $Health = def_Wait-Health
    def_Write-Step "READY · PID $($Process.Id) · http://127.0.0.1:$($Health.port)/"
    return
}

def_Write-Step "啟動唯讀 Runtime；按 Ctrl+C 停止"
def_Write-Step "VDF → Adjusted Price Gate → TA-Lib → Runtime → Workbench · SYNC CONNECT"
& $Python @Arguments
if ($LASTEXITCODE -ne 0) { throw "Runtime 非正常結束，Exit Code $LASTEXITCODE" }

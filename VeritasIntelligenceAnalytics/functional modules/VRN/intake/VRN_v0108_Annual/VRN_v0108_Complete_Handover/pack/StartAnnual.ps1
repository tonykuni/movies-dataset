param(
    [string]$PythonPath = '',
    [string]$OutputRoot = (Join-Path $PSScriptRoot 'rerun_output'),
    [switch]$InstallDependencies
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
function Invoke-VRNAnnualFinal {
    param([string]$Interpreter, [string]$Destination, [bool]$Install)
    $CandidatePaths = @()
    if ($Interpreter) { $CandidatePaths += $Interpreter }
    if ($env:VIRTUAL_ENV) { $CandidatePaths += (Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe') }
    $CandidatePaths += (Join-Path $env:USERPROFILE 'envs\via_vrn_312\Scripts\python.exe')
    $CandidatePaths += (Join-Path $env:USERPROFILE 'envs\via_core\Scripts\python.exe')
    $FoundPython = Get-Command python -ErrorAction SilentlyContinue
    if ($FoundPython) { $CandidatePaths += $FoundPython.Source }
    $SelectedPython = $null
    Write-Progress -Activity 'VRN 年度最後一輪' -Status '檢查 Python 3.12 環境' -PercentComplete 5
    foreach ($Candidate in ($CandidatePaths | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) { continue }
        $VersionCheck = & $Candidate -c 'import sys; print("READY" if sys.version_info[:2] == (3,12) else "OTHER_VERSION")'
        if ($LASTEXITCODE -eq 0 -and $VersionCheck -eq 'READY') { $SelectedPython = $Candidate; break }
    }
    if (-not $SelectedPython) { throw '找不到 Python 3.12；請用 -PythonPath 指定 via_ 環境的 python.exe。' }
    $Modules = 'fitz,pdfplumber,polars,openpyxl,reportlab,fontTools,numpy,pandas,docx,PIL'
    $Missing = & $SelectedPython -c 'import importlib.util,sys; print(",".join(m for m in sys.argv[1].split(",") if importlib.util.find_spec(m) is None))' $Modules
    if ($Missing) {
        if (-not $Install) { throw ('缺少函式庫：' + $Missing + '。加上 -InstallDependencies 可安裝完整需求。') }
        Write-Progress -Activity 'VRN 年度最後一輪' -Status '安裝需求到選定環境' -PercentComplete 15
        & $SelectedPython -m pip install -r (Join-Path $PSScriptRoot 'requirements_annual.txt')
        if ($LASTEXITCODE -ne 0) { throw '函式庫安裝失敗；尚未執行資料擷取。' }
    }
    Write-Progress -Activity 'VRN 年度最後一輪' -Status '重讀來源、驗算與輸出讀回' -PercentComplete 35
    & $SelectedPython -X utf8 (Join-Path $PSScriptRoot 'VRN_AnnualFinancial_v0108.py') --dispatcher-root (Join-Path $PSScriptRoot 'engine') --input-root (Join-Path $PSScriptRoot 'inputs') --output-root $Destination
    if ($LASTEXITCODE -ne 0) { throw '品質閘門未通過；請保留錯誤訊息，不能宣稱完成。' }
    Write-Progress -Activity 'VRN 年度最後一輪' -Status '完成' -PercentComplete 100
    Write-Progress -Activity 'VRN 年度最後一輪' -Completed
    Write-Host ('成果：' + $Destination)
    Write-Host '整體 PASS_WITH_SOURCE_LIMITATIONS；來源缺值與矛盾均保留。'
}
try { Invoke-VRNAnnualFinal -Interpreter $PythonPath -Destination $OutputRoot -Install ([bool]$InstallDependencies) }
catch { Write-Progress -Activity 'VRN 年度最後一輪' -Completed; Write-Host $_.Exception.Message -ForegroundColor Red }

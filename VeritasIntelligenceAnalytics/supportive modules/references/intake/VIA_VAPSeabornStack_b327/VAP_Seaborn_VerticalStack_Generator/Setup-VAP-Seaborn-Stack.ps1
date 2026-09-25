[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvRoot = Join-Path $ScriptRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$VenvPythonw = Join-Path $VenvRoot "Scripts\pythonw.exe"
$Requirements = Join-Path $ScriptRoot "requirements.txt"
$UiScript = Join-Path $ScriptRoot "vap_seaborn_stack_ui.py"
$PythonCandidates = @("py", "python")

function Find-PythonCommand {
    foreach ($Candidate in $PythonCandidates) {
        try {
            if ($Candidate -eq "py") {
                & $Candidate -3.12 --version *> $null
                if ($LASTEXITCODE -eq 0) {
                    return @($Candidate, "-3.12")
                }
            }
            else {
                & $Candidate -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" *> $null
                if ($LASTEXITCODE -eq 0) {
                    return @($Candidate)
                }
            }
        }
        catch {
            continue
        }
    }
    throw "找不到 Python 3.12。"
}

function Ensure-VapEnvironment {
    if (Test-Path -LiteralPath $VenvPython) {
        & $VenvPython -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "現有 .venv 不是 Python 3.12。請先重新命名或移除套件內的 .venv，再執行安裝。"
        }
    }
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        $PythonCommand = @(Find-PythonCommand)
        if ($PythonCommand.Count -eq 2) {
            & $PythonCommand[0] $PythonCommand[1] -m venv $VenvRoot
        }
        else {
            & $PythonCommand[0] -m venv $VenvRoot
        }
        if ($LASTEXITCODE -ne 0) {
            throw "建立 VAP 虛擬環境失敗。"
        }
    }
    if (-not $SkipInstall) {
        & $VenvPython -m pip install --disable-pip-version-check -r $Requirements
        if ($LASTEXITCODE -ne 0) {
            throw "安裝 VAP 依賴套件失敗。"
        }
    }
}

function Start-VapWorkbench {
    if ($NoLaunch) {
        return
    }
    $Launcher = if (Test-Path -LiteralPath $VenvPythonw) { $VenvPythonw } else { $VenvPython }
    Start-Process -FilePath $Launcher -ArgumentList @("vap_seaborn_stack_ui.py") -WorkingDirectory $ScriptRoot
}

Push-Location $ScriptRoot
try {
    Ensure-VapEnvironment
    Start-VapWorkbench
}
finally {
    Pop-Location
}

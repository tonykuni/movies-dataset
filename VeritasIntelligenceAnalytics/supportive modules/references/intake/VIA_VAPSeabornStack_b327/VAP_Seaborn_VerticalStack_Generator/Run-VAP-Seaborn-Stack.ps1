[CmdletBinding()]
param(
    [ValidateSet("demo", "render", "render-one", "list", "discover", "auto-config")]
    [string]$Action = "demo",
    [string]$Config = "examples/demo_stack.json",
    [string]$Id = "",
    [string]$Source = "",
    [string]$Table = "",
    [string]$Sheet = "",
    [string]$Output = "",
    [switch]$OpenOutput
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ScriptRoot ".venv\Scripts\python.exe"
$PythonExe = $null
$PythonPrefix = @()

if (Test-Path -LiteralPath $VenvPython) {
    & $VenvPython -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "套件內 .venv 不是 Python 3.12，請重新執行 Setup-and-Run-VAP-Seaborn-Stack.cmd。"
    }
    $PythonExe = $VenvPython
}
else {
    foreach ($Candidate in @("py", "python")) {
        try {
            if ($Candidate -eq "py") {
                & $Candidate -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" *> $null
                if ($LASTEXITCODE -eq 0) {
                    $PythonExe = $Candidate
                    $PythonPrefix = @("-3.12")
                    break
                }
            }
            else {
                & $Candidate -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" *> $null
                if ($LASTEXITCODE -eq 0) {
                    $PythonExe = $Candidate
                    break
                }
            }
        }
        catch {
            continue
        }
    }
}

if (-not $PythonExe) {
    throw "找不到 Python 3.12。請先執行 Setup-and-Run-VAP-Seaborn-Stack.cmd。"
}

Push-Location $ScriptRoot
try {
    $CommandArguments = @("vap_seaborn_stack_generator.py", $Action)
    if ($Action -in @("demo", "render", "render-one", "list", "auto-config")) {
        $CommandArguments += @("--config", $Config)
    }
    if ($Action -eq "render-one") {
        if (-not $Id) { throw "render-one 必須提供 -Id。" }
        $CommandArguments += @("--id", $Id)
    }
    if ($Action -in @("discover", "auto-config")) {
        if (-not $Source) { throw "$Action 必須提供 -Source。" }
        $CommandArguments += @("--source", $Source)
        if ($Table) { $CommandArguments += @("--table", $Table) }
        if ($Sheet) { $CommandArguments += @("--sheet", $Sheet) }
    }
    if ($Action -eq "discover" -and $Output) {
        $CommandArguments += @("--output", $Output)
    }
    & $PythonExe @PythonPrefix @CommandArguments
    if ($LASTEXITCODE -ne 0) {
        throw "VAP Seaborn 圖組生成失敗，ExitCode=$LASTEXITCODE"
    }

    if ($OpenOutput -and $Action -in @("demo", "render")) {
        $ResolvedConfig = (Resolve-Path -LiteralPath $Config).Path
        $ConfigObject = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResolvedConfig | ConvertFrom-Json
        $ConfiguredDirectory = [string]$ConfigObject.project.output_directory
        if ([IO.Path]::IsPathRooted($ConfiguredDirectory)) {
            $OutputDirectory = $ConfiguredDirectory
        }
        else {
            $OutputDirectory = Join-Path (Split-Path -Parent $ResolvedConfig) $ConfiguredDirectory
        }
        $OpenedOutput = $false
        foreach ($Format in @($ConfigObject.project.output_formats)) {
            $NormalizedFormat = ([string]$Format).Trim().TrimStart(".").ToLowerInvariant()
            if (-not $NormalizedFormat) { continue }
            $OutputFile = Join-Path $OutputDirectory (([string]$ConfigObject.project.output_name) + "." + $NormalizedFormat)
            if (Test-Path -LiteralPath $OutputFile) {
                Start-Process -FilePath $OutputFile
                $OpenedOutput = $true
                break
            }
        }
        if (-not $OpenedOutput) {
            Write-Warning "圖表已生成，但找不到設定格式的輸出檔可開啟。"
        }
    }
}
finally {
    Pop-Location
}

#requires -Version 7.0
# VIA Industry Forecast · Single-Entry Safe Master Launcher v0100
# Policy: READ-ONLY discovery of supportive / functional modules · NO child execution of target scripts
#         APPEND-ONLY output · NO canonical mutation. Only this launcher's own Python engine runs.
# The 15 accelerators are orchestrated by the Python engine (safe analysis passes); high-risk nodes
# are proposal-only and never auto-applied. All heavy repair remains under human approval (核可制).
param(
    [string]$Base = "",
    [string]$PythonExe = "",
    [string]$ConfigPath = "",
    [string]$EnginePath = "",
    [int]$TimeoutSeconds = 900,
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$script:Stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$script:Accelerators = @(
    "A01 AST 精準解析",
    "A02 多語言語意分類",
    "A03 九頭龍風險偵測 Hydra",
    "A04 依賴拓撲排序",
    "A05 沙盒隔離執行",
    "A06 自動修正建議生成",
    "A07 三輪全景式分析",
    "A08 SSOT 對齊",
    "A09 視覺化矩陣生成 RYG",
    "A10 錯誤分類與分群",
    "A11 性能與複雜度分析",
    "A12 多子系統同步檢視",
    "A13 版本差異與回滾偵測",
    "A14 覆蓋率與回歸檢查",
    "A15 修正順序最佳化"
)

function def_WriteHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 84) -ForegroundColor DarkCyan
    Write-Host ("def {0}" -f $Title) -ForegroundColor Cyan
    Write-Host ("=" * 84) -ForegroundColor DarkCyan
}

function def_Progress {
    param([int]$Step, [int]$Total, [string]$Message)
    $pct = 0
    if ($Total -gt 0) {
        $pct = [int](($Step / $Total) * 100)
    }
    Write-Progress -Id 1 -Activity "VIA IF Launcher" -Status $Message -PercentComplete $pct
    Write-Host ("[{0,3}%] {1}" -f $pct, $Message) -ForegroundColor Green
}

function def_Prop {
    param($Obj, [string]$Name, $Default)
    if ($null -eq $Obj) {
        return $Default
    }
    $p = $Obj.PSObject.Properties[$Name]
    if ($null -eq $p) {
        return $Default
    }
    return $p.Value
}

function def_EnsureDir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        $null = New-Item -ItemType Directory -Path $Path -Force
    }
}

function def_WriteText {
    param([string]$Path, [string]$Text)
    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Text, $enc)
}

function def_ResolveBase {
    param([string]$Override, [string]$ConfigBase)
    $candidates = @()
    if ($Override -ne "") {
        $candidates += $Override
    }
    if ($ConfigBase -ne "") {
        $candidates += $ConfigBase
    }
    $candidates += "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
    foreach ($c in $candidates) {
        if ($c -ne "" -and (Test-Path -LiteralPath $c)) {
            return (Resolve-Path -LiteralPath $c).Path
        }
    }
    throw ("Base not found. Tried: {0}" -f ($candidates -join " ; "))
}

function def_ResolveFileBeside {
    param([string]$Override, [string]$ScriptDir, [string]$Name)
    if ($Override -ne "" -and (Test-Path -LiteralPath $Override)) {
        return (Resolve-Path -LiteralPath $Override).Path
    }
    $beside = Join-Path $ScriptDir $Name
    if (Test-Path -LiteralPath $beside) {
        return (Resolve-Path -LiteralPath $beside).Path
    }
    throw ("{0} not found beside launcher; pass the matching -Path parameter." -f $Name)
}

function def_ResolvePython {
    param([string]$Override)
    if ($Override -ne "") {
        return $Override
    }
    $candidates = @(
        "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
        "C:\Users\tonyk\envs\venv_core\Scripts\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) {
            return $c
        }
    }
    return "python"
}

function def_DeployAsset {
    param([string]$Src, [string]$DestDir, [string]$Name)
    def_EnsureDir $DestDir
    $dest = Join-Path $DestDir $Name
    if (-not (Test-Path -LiteralPath $dest)) {
        Copy-Item -LiteralPath $Src -Destination $dest
    }
    return $dest
}

function def_RunEngine {
    param(
        [string]$PythonPath,
        [string]$Engine,
        [string]$Config,
        [string]$BaseArg,
        [string]$Runs,
        [int]$TimeoutMs
    )
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $PythonPath
    [void]$psi.ArgumentList.Add($Engine)
    [void]$psi.ArgumentList.Add("--config")
    [void]$psi.ArgumentList.Add($Config)
    [void]$psi.ArgumentList.Add("--base")
    [void]$psi.ArgumentList.Add($BaseArg)
    [void]$psi.ArgumentList.Add("--output-root")
    [void]$psi.ArgumentList.Add($Runs)
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    $done = $proc.WaitForExit($TimeoutMs)
    if (-not $done) {
        $proc.Kill($true)
        return @{ Code = -1; Out = $outTask.Result; Err = ("TIMEOUT after {0} ms" -f $TimeoutMs); TimedOut = $true }
    }
    return @{ Code = $proc.ExitCode; Out = $outTask.Result; Err = $errTask.Result; TimedOut = $false }
}

function def_Main {
    $scriptDir = $PSScriptRoot
    def_WriteHeader "VIA Industry Forecast · Safe Master Launcher v0100"
    Write-Host "def Policy: READ-ONLY · NO TARGET EXECUTION · APPEND-ONLY · NO CANONICAL MUTATION" -ForegroundColor Yellow
    Write-Host "def Accelerators embedded (orchestrated by engine):" -ForegroundColor Cyan
    foreach ($a in $script:Accelerators) {
        Write-Host ("  - {0}" -f $a) -ForegroundColor DarkGray
    }

    $config = def_ResolveFileBeside $ConfigPath $scriptDir "via_if_config.json"
    $engine = def_ResolveFileBeside $EnginePath $scriptDir "via_if_engine.py"
    $cfg = Get-Content -LiteralPath $config -Raw -Encoding UTF8 | ConvertFrom-Json

    $roots = def_Prop $cfg "roots" $null
    $configBase = [string](def_Prop $roots "base" "")
    $sysDirName = [string](def_Prop $roots "system_dir_name" "VIA_IndustryForecast")
    $scaffold = def_Prop $cfg "scaffold_folders" @()

    $base = def_ResolveBase $Base $configBase
    def_Progress 1 6 "Base resolved"

    $sysDir = Join-Path $base $sysDirName
    def_EnsureDir $sysDir
    foreach ($f in $scaffold) {
        $sub = ([string]$f).Replace("/", "\")
        def_EnsureDir (Join-Path $sysDir $sub)
    }
    def_Progress 2 6 "Scaffold ready"

    $py = def_ResolvePython $PythonExe
    $deployedEngine = def_DeployAsset $engine (Join-Path $sysDir "01_engines") "via_if_engine.py"
    $null = def_DeployAsset $config (Join-Path $sysDir "00_config") "via_if_config.json"
    def_Progress 3 6 "Assets deployed (append-only)"

    $runs = Join-Path $sysDir "07_runs"
    def_EnsureDir $runs
    Write-Host ("def Python : {0}" -f $py) -ForegroundColor Gray
    Write-Host ("def Engine : {0}" -f $deployedEngine) -ForegroundColor Gray
    Write-Host ("def Base   : {0}" -f $base) -ForegroundColor Gray

    def_Progress 4 6 "Running safe panorama engine"
    $result = def_RunEngine $py $deployedEngine $config $base $runs ($TimeoutSeconds * 1000)
    if ($result.TimedOut) {
        Write-Host "def Engine TIMED OUT - process killed." -ForegroundColor Red
    }
    if ($result.Code -ne 0) {
        Write-Host ("def Engine exit code {0}" -f $result.Code) -ForegroundColor Red
        if ($result.Err -ne "") {
            Write-Host $result.Err -ForegroundColor DarkRed
        }
    }
    else {
        Write-Host "def Engine completed OK." -ForegroundColor Green
    }

    def_Progress 5 6 "Locating latest run and HTML matrix"
    $latest = Get-ChildItem -LiteralPath $runs -Directory -Filter "RUN_*" |
        Sort-Object -Property @{ Expression = "Name"; Descending = $true } |
        Select-Object -First 1
    $htmlPath = ""
    if ($null -ne $latest) {
        $candidate = Join-Path $latest.FullName "VIA_IF_SafePanorama_Matrix.html"
        if (Test-Path -LiteralPath $candidate) {
            $htmlPath = $candidate
        }
    }

    $manifest = [ordered]@{
        launcher     = "VIA IF Safe Master Launcher v0100"
        stamp        = $script:Stamp
        base         = $base
        python       = $py
        engine       = $deployedEngine
        config       = $config
        engine_exit  = $result.Code
        html_matrix  = $htmlPath
        accelerators = $script:Accelerators
        policy       = "READ_ONLY_NO_TARGET_EXECUTION_APPEND_ONLY_NO_CANONICAL_MUTATION"
    }
    $manifestJson = $manifest | ConvertTo-Json -Depth 6
    $manifestPath = Join-Path $runs ("launcher_manifest_{0}.json" -f $script:Stamp)
    def_WriteText $manifestPath $manifestJson

    def_Progress 6 6 "Done"
    Write-Progress -Id 1 -Activity "VIA IF Launcher" -Completed
    Write-Host ""
    Write-Host ("def Manifest : {0}" -f $manifestPath) -ForegroundColor Gray
    if ($htmlPath -ne "") {
        Write-Host ("def Matrix   : {0}" -f $htmlPath) -ForegroundColor Green
        if (-not $NoOpen) {
            Start-Process $htmlPath
        }
    }
    else {
        Write-Host "def Matrix   : not found (check engine output above)." -ForegroundColor Yellow
    }
}

def_Main

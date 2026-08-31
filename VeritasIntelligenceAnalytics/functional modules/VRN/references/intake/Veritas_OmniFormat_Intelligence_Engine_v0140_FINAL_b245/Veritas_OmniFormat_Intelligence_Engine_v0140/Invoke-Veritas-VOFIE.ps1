#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string[]]$InputPaths = @(),

    [string]$OutputPath = (Join-Path $PSScriptRoot "Veritas_VOFIE_Output"),

    [ValidateSet("md", "json", "docx", "pptx", "xlsx", "csv", "html", "css", "js")]
    [string[]]$Formats = @("md", "json", "csv", "html", "css", "js"),

    [string]$Title = "",

    [ValidateSet("zh-Hant", "zh-Hans", "en", "auto")]
    [string]$Language = "zh-Hant",

    [ValidateRange(1000, 1000000)]
    [int]$MaxTopicChars = 18000,

    [string]$PythonExe = "",

    [switch]$NoVSIS,

    [switch]$NoQuarantine,

    [switch]$Manifest,

    [switch]$SelfTest,

    [switch]$UserTest,

    [switch]$Activate,

    [switch]$ToolAudit,

    [ValidateSet("all", "javascript", "powershell")]
    [string]$ToolLanguage = "all",

    [switch]$ProbeInstalled,

    [switch]$ToolPlan,

    [string]$ToolTarget = "",

    [ValidateSet(
        "syntax_parse", "static_analysis", "formatting", "unit_test", "coverage",
        "dependency_graph", "unused_code", "refactor_codmod", "schema_ui_validate",
        "build_automation"
    )]
    [string[]]$ToolFunctions = @("syntax_parse", "static_analysis", "unit_test"),

    [switch]$ExecuteSafe,

    [switch]$HydraAudit,

    [string[]]$HydraTargets = @(),

    [switch]$RuntimeCopy,

    [string[]]$RuntimeTargets = @(),

    [string]$RuntimeOutput = (Join-Path $PSScriptRoot "Veritas_VOFIE_RuntimeCopy"),

    [string]$RuntimeApprovalToken = "",

    [switch]$RollbackCheck,

    [string]$RuntimeManifest = "",

    [switch]$Simple,

    [switch]$Gui,

    [ValidateSet("ENGINE", "SYSTEM")]
    [string]$Role = "ENGINE",

    [ValidateSet("text_merge", "code_merge", "restructure", "deduplicate", "optimize")]
    [string[]]$Operations = @("text_merge", "code_merge", "restructure", "deduplicate", "optimize"),

    [switch]$OpenHtml
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$Script:EngineName = "Veritas OmniFormat Intelligence Engine"
$Script:EngineVersion = "1.4.0"
$Script:EngineRoot = $PSScriptRoot
$Script:EngineFile = Join-Path $PSScriptRoot "Veritas_OmniFormat_Intelligence_Engine.py"


function Write-VOFIEProgress {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Stage,
        [Parameter(Mandatory)][string]$Message
    )

    $payload = [ordered]@{
        engine  = $Script:EngineName
        version = $Script:EngineVersion
        stage   = $Stage
        message = $Message
    } | ConvertTo-Json -Compress
    Write-Host "@@PROGRESS $payload"
}


function Test-VOFIEPythonCandidate {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Candidate)

    try {
        if ([IO.Path]::IsPathRooted($Candidate) -and -not (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
            return $false
        }
        & $Candidate -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 7)" 2>$null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}


function Resolve-VOFIEPython {
    [CmdletBinding()]
    param()

    $candidates = [Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($PythonExe)) {
        $candidates.Add($PythonExe)
    }
    foreach ($relative in @(
        "..\via_core_312\Scripts\python.exe",
        "..\via_core\Scripts\python.exe",
        ".venv\Scripts\python.exe",
        "venv\Scripts\python.exe"
    )) {
        $candidates.Add((Join-Path $Script:EngineRoot $relative))
    }
    $candidates.Add("python")
    $candidates.Add("python3")
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-VOFIEPythonCandidate -Candidate $candidate) {
            return $candidate
        }
    }
    throw "找不到 Python 3.11+；請使用 -PythonExe 指定 VIA via_core Python。"
}


function Resolve-VOFIEInput {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    $expanded = [Environment]::ExpandEnvironmentVariables($Path)
    $resolved = (Resolve-Path -LiteralPath $expanded -ErrorAction Stop).Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "輸入必須是現有檔案：$resolved"
    }
    return $resolved
}


function Invoke-VOFIEPython {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ResolvedPython,
        [Parameter(Mandatory)][string[]]$Arguments
    )

    Push-Location -LiteralPath $Script:EngineRoot
    try {
        & $ResolvedPython $Script:EngineFile @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "VOFIE 執行失敗，ExitCode=$LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}


function Start-VeritasVOFIE {
    [CmdletBinding()]
    param()

    Write-VOFIEProgress -Stage "gate" -Message "解析 Python 與唯讀輸入路徑"
    $python = Resolve-VOFIEPython

    if ($Gui) {
        Invoke-VOFIEPython -ResolvedPython $python -Arguments @("gui")
        return
    }

    if ($SelfTest) {
        $report = Join-Path $Script:EngineRoot "Veritas_VOFIE_SELF_TEST.json"
        Invoke-VOFIEPython -ResolvedPython $python -Arguments @("self-test", "--report", $report)
        Write-VOFIEProgress -Stage "complete" -Message "自測完成：$report"
        return
    }

    if ($Manifest) {
        $manifestPath = Join-Path $Script:EngineRoot "Veritas_VOFIE_RegistryManifest.json"
        Invoke-VOFIEPython -ResolvedPython $python -Arguments @("manifest", "--file", $manifestPath)
        Write-VOFIEProgress -Stage "complete" -Message "Registry Manifest 完成：$manifestPath"
        return
    }

    if ($UserTest) {
        $report = Join-Path $Script:EngineRoot "Veritas_VOFIE_USER_TEST.json"
        Invoke-VOFIEPython -ResolvedPython $python -Arguments @("user-test", "--report", $report)
        Write-VOFIEProgress -Stage "complete" -Message "使用者流程測試完成：$report"
        return
    }

    if ($Activate) {
        $report = Join-Path $Script:EngineRoot "Veritas_VOFIE_ACTIVATION.json"
        Invoke-VOFIEPython -ResolvedPython $python -Arguments @("activate", "--report", $report)
        Write-VOFIEProgress -Stage "complete" -Message "啟用測試完成：$report"
        return
    }

    if ($ToolAudit) {
        $report = Join-Path $Script:EngineRoot "Veritas_VOFIE_POLYGLOT_TOOL_AUDIT.json"
        $toolArguments = [Collections.Generic.List[string]]::new()
        $toolArguments.Add("tool-audit")
        $toolArguments.Add("--language")
        $toolArguments.Add($ToolLanguage)
        $toolArguments.Add("--report")
        $toolArguments.Add($report)
        if ($ProbeInstalled) {
            $toolArguments.Add("--probe-installed")
        }
        Invoke-VOFIEPython -ResolvedPython $python -Arguments $toolArguments.ToArray()
        Write-VOFIEProgress -Stage "complete" -Message "雙語言 Top-20 CPU 工具稽核完成：$report"
        return
    }

    if ($ToolPlan) {
        if ([string]::IsNullOrWhiteSpace($ToolTarget)) {
            throw "-ToolPlan 需要 -ToolTarget 指定 JavaScript、TypeScript 或 PowerShell 檔案。"
        }
        $resolvedTarget = Resolve-VOFIEInput -Path $ToolTarget
        $report = Join-Path $Script:EngineRoot "Veritas_VOFIE_TOOL_PLAN.json"
        $planArguments = [Collections.Generic.List[string]]::new()
        $planArguments.Add("tool-plan")
        $planArguments.Add($resolvedTarget)
        $planArguments.Add("--functions")
        $planArguments.Add(($ToolFunctions -join ","))
        $planArguments.Add("--report")
        $planArguments.Add($report)
        if ($ExecuteSafe) {
            $planArguments.Add("--execute-safe")
        }
        Invoke-VOFIEPython -ResolvedPython $python -Arguments $planArguments.ToArray()
        Write-VOFIEProgress -Stage "complete" -Message "按需工具計畫完成：$report"
        return
    }

    if ($HydraAudit) {
        $report = Join-Path $Script:EngineRoot "Veritas_VOFIE_HYDRA_RISK_AUDIT.json"
        $hydraArguments = [Collections.Generic.List[string]]::new()
        $hydraArguments.Add("hydra-audit")
        foreach ($target in $HydraTargets) {
            $hydraArguments.Add((Resolve-VOFIEInput -Path $target))
        }
        $hydraArguments.Add("--report")
        $hydraArguments.Add($report)
        Invoke-VOFIEPython -ResolvedPython $python -Arguments $hydraArguments.ToArray()
        Write-VOFIEProgress -Stage "complete" -Message "九頭龍 Top-20 review-only 稽核完成：$report"
        return
    }

    if ($RuntimeCopy) {
        if ($RuntimeTargets.Count -eq 0) {
            throw "-RuntimeCopy 需要 1–5 個 -RuntimeTargets。"
        }
        $report = Join-Path $Script:EngineRoot "Veritas_VOFIE_RUNTIME_COPY.json"
        $runtimeArguments = [Collections.Generic.List[string]]::new()
        $runtimeArguments.Add("runtime-copy")
        foreach ($target in $RuntimeTargets) {
            $runtimeArguments.Add((Resolve-VOFIEInput -Path $target))
        }
        $runtimeArguments.Add("--output")
        $runtimeArguments.Add($RuntimeOutput)
        $runtimeArguments.Add("--approval-token")
        $runtimeArguments.Add($RuntimeApprovalToken)
        $runtimeArguments.Add("--report")
        $runtimeArguments.Add($report)
        Invoke-VOFIEPython -ResolvedPython $python -Arguments $runtimeArguments.ToArray()
        Write-VOFIEProgress -Stage "complete" -Message "Runtime Copy sandbox 完成：$report"
        return
    }

    if ($RollbackCheck) {
        if ([string]::IsNullOrWhiteSpace($RuntimeManifest)) {
            throw "-RollbackCheck 需要 -RuntimeManifest。"
        }
        $manifest = Resolve-VOFIEInput -Path $RuntimeManifest
        $report = Join-Path $Script:EngineRoot "Veritas_VOFIE_ROLLBACK_CHECK.json"
        Invoke-VOFIEPython -ResolvedPython $python -Arguments @("rollback-check", $manifest, "--report", $report)
        Write-VOFIEProgress -Stage "complete" -Message "Rollback dry-run 完成：$report"
        return
    }

    if ($InputPaths.Count -eq 0) {
        throw "轉換模式至少需要一個 -InputPaths。"
    }
    $resolvedInputs = @($InputPaths | ForEach-Object { Resolve-VOFIEInput -Path $_ })
    if ($Simple -and $resolvedInputs.Count -gt 5) {
        throw "簡易模式最多 5 個輸入檔；目前為 $($resolvedInputs.Count)。"
    }
    $arguments = [Collections.Generic.List[string]]::new()
    $arguments.Add($(if ($Simple) { "simple" } else { "convert" }))
    foreach ($path in $resolvedInputs) {
        $arguments.Add($path)
    }
    $arguments.Add("--output")
    $arguments.Add($OutputPath)
    if ($Simple) {
        $arguments.Add("--role")
        $arguments.Add($Role)
        $arguments.Add("--operations")
        $arguments.Add(($Operations -join ","))
    }
    else {
        $arguments.Add("--formats")
        $arguments.Add(($Formats -join ","))
    }
    $arguments.Add("--language")
    $arguments.Add($Language)
    $arguments.Add("--max-topic-chars")
    $arguments.Add("$MaxTopicChars")
    if (-not [string]::IsNullOrWhiteSpace($Title)) {
        $arguments.Add("--title")
        $arguments.Add($Title)
    }
    if ($NoVSIS) {
        $arguments.Add("--no-vsis")
    }
    if ($NoQuarantine) {
        $arguments.Add("--no-quarantine")
    }

    Write-VOFIEProgress -Stage "convert" -Message $(if ($Simple) { "建立五個主要檔與整合視圖" } else { "建立 Universal Content IR 與完整格式產物" })
    Invoke-VOFIEPython -ResolvedPython $python -Arguments $arguments.ToArray()

    if ($OpenHtml) {
        $htmlName = $(if ($Simple) { "Veritas_VOFIE.html" } else { "Veritas_VOFIE_Template.html" })
        $htmlPath = Get-ChildItem -LiteralPath $OutputPath -Filter $htmlName -File -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $htmlPath) {
            Start-Process -FilePath $htmlPath.FullName
        }
    }
    Write-VOFIEProgress -Stage "complete" -Message "完成；來源檔未修改。"
}


Start-VeritasVOFIE

#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$InputPath,

    [Parameter(Mandatory = $false)]
    [string]$OutputDir = (Join-Path $PSScriptRoot "run_output_v0210"),

    [Parameter(Mandatory = $false)]
    [string]$PythonExe = "python",

    [Parameter(Mandatory = $false)]
    [string]$KeywordDb = "",

    [Parameter(Mandatory = $false)]
    [string]$NonKeywordDb = "",

    [Parameter(Mandatory = $false)]
    [string]$SsotDb = "",

    [Parameter(Mandatory = $false)]
    [string[]]$KeywordReviewPath = @(),

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 20)]
    [int]$SummarySentences = 7,

    [Parameter(Mandatory = $false)]
    [ValidateSet("CONSERVATIVE", "BALANCED", "PERFORMANCE")]
    [string]$ResourceMode = "BALANCED",

    [Parameter(Mandatory = $false)]
    [ValidateRange(10, 100)]
    [double]$MaxCpuPercent = 85,

    [Parameter(Mandatory = $false)]
    [ValidateRange(10, 99)]
    [double]$MaxMemoryPercent = 82,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 512)]
    [int]$BatchSize = 16,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 64)]
    [int]$MaxWorkers = 4,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 32)]
    [int]$NativeThreadLimit = 2,

    [Parameter(Mandatory = $false)]
    [bool]$Recursive = $true,

    [Parameter(Mandatory = $false)]
    [bool]$RunTests = $true,

    [Parameter(Mandatory = $false)]
    [switch]$DisableDiskCache,

    [Parameter(Mandatory = $false)]
    [switch]$DisableAnalyticsExports,

    [Parameter(Mandatory = $false)]
    [switch]$DisableCompressedJson,

    [Parameter(Mandatory = $false)]
    [switch]$EnableLocalLlm,

    [Parameter(Mandatory = $false)]
    [ValidateSet("ollama")]
    [string]$LocalLlmProvider = "ollama",

    [Parameter(Mandatory = $false)]
    [string]$LocalLlmModel = "qwen3:latest",

    [Parameter(Mandatory = $false)]
    [string]$LocalLlmEndpoint = "http://127.0.0.1:11434",

    [Parameter(Mandatory = $false)]
    [ValidateRange(1024, 65535)]
    [int]$KeywordReviewPort = 8765,

    [Parameter(Mandatory = $false)]
    [ValidateRange(60, 86400)]
    [int]$KeywordReviewIdleSeconds = 1800,

    [Parameter(Mandatory = $false)]
    [switch]$OpenHtml
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def 01. 顯示、AST 與資源監測
# =============================================================================

function def_WriteStage {
    param(
        [Parameter(Mandatory = $true)][int]$Percent,
        [Parameter(Mandatory = $true)][string]$Message,
        [Parameter(Mandatory = $false)][ValidateSet("INFO", "PASS", "WARN")][string]$State = "INFO"
    )
    $color = switch ($State) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        default { "Cyan" }
    }
    Write-Progress -Activity "VIA NLP Fusion Engine v0210" -Status $Message -PercentComplete $Percent
    Write-Host ("def [{0,3}%] [{1}] {2}" -f $Percent, $State, $Message) -ForegroundColor $color
}

function def_TestPowerShellAst {
    param([Parameter(Mandatory = $true)][string]$ScriptPath)
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $ScriptPath,
        [ref]$tokens,
        [ref]$errors
    )
    if ($errors.Count -gt 0) {
        throw ("PowerShell AST 驗證失敗：{0}" -f ($errors.Message -join "; "))
    }
}

function def_GetResourceSnapshot {
    try {
        $processor = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop |
            Measure-Object -Property LoadPercentage -Average
        $operatingSystem = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
        $totalKb = [double]$operatingSystem.TotalVisibleMemorySize
        $freeKb = [double]$operatingSystem.FreePhysicalMemory
        $usedPercent = if ($totalKb -gt 0) { (($totalKb - $freeKb) / $totalKb) * 100 } else { 0 }
        return [pscustomobject]@{
            CpuPercent       = [math]::Round([double]$processor.Average, 1)
            MemoryPercent    = [math]::Round($usedPercent, 1)
            FreeMemoryMb     = [math]::Round($freeKb / 1024, 1)
            Monitor          = "CIM"
        }
    }
    catch {
        return [pscustomobject]@{
            CpuPercent       = 0
            MemoryPercent    = 0
            FreeMemoryMb     = 0
            Monitor          = "PYTHON_FALLBACK"
        }
    }
}

function def_ShowResourceSnapshot {
    param([Parameter(Mandatory = $true)][string]$Label)
    $snapshot = def_GetResourceSnapshot
    Write-Host ("def Resource {0}: CPU={1}% DRAM={2}% Free={3}MB Monitor={4}" -f
        $Label, $snapshot.CpuPercent, $snapshot.MemoryPercent, $snapshot.FreeMemoryMb, $snapshot.Monitor) -ForegroundColor DarkCyan
}

# =============================================================================
# def 02. 路徑與 Python
# =============================================================================

function def_ResolvePython {
    param([Parameter(Mandatory = $true)][string]$Command)
    $resolved = Get-Command $Command -ErrorAction Stop
    return $resolved.Source
}

function def_ResolveInputPaths {
    param([Parameter(Mandatory = $true)][string[]]$Paths)
    $resolved = [System.Collections.Generic.List[string]]::new()
    foreach ($item in $Paths) {
        $candidate = (Resolve-Path -LiteralPath $item -ErrorAction Stop).Path
        [void]$resolved.Add($candidate)
    }
    return $resolved.ToArray()
}

function def_ResolveOptionalFiles {
    param([Parameter(Mandatory = $true)][string[]]$Paths)
    $resolved = [System.Collections.Generic.List[string]]::new()
    foreach ($item in $Paths) {
        if ([string]::IsNullOrWhiteSpace($item)) {
            continue
        }
        [void]$resolved.Add((Resolve-Path -LiteralPath $item -ErrorAction Stop).Path)
    }
    return $resolved.ToArray()
}

function def_ResolveWritablePath {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$Fallback
    )
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return [System.IO.Path]::GetFullPath($Fallback)
    }
    return [System.IO.Path]::GetFullPath($Value)
}

function def_QuoteProcessArgument {
    param([Parameter(Mandatory = $true)][string]$Value)
    return '"' + $Value.Replace('"', '\"') + '"'
}

# =============================================================================
# def 03. 測試與引擎執行
# =============================================================================

function def_InvokePythonTests {
    param(
        [Parameter(Mandatory = $true)][string]$ResolvedPython,
        [Parameter(Mandatory = $true)][string]$ProjectDir
    )
    Push-Location $ProjectDir
    try {
        & $ResolvedPython -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) {
            throw "Python 測試失敗，ExitCode=$LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

function def_InvokeNlpEngine {
    param(
        [Parameter(Mandatory = $true)][string]$ResolvedPython,
        [Parameter(Mandatory = $true)][string]$EnginePath,
        [Parameter(Mandatory = $true)][string[]]$ResolvedInputs,
        [Parameter(Mandatory = $true)][string[]]$ResolvedReviews,
        [Parameter(Mandatory = $true)][string]$ResolvedOutput,
        [Parameter(Mandatory = $true)][string]$ResolvedNonKeywordDb
    )
    $arguments = [System.Collections.Generic.List[string]]::new()
    [void]$arguments.Add($EnginePath)
    foreach ($item in $ResolvedInputs) {
        [void]$arguments.Add("--input")
        [void]$arguments.Add($item)
    }
    [void]$arguments.Add("--output")
    [void]$arguments.Add($ResolvedOutput)
    [void]$arguments.Add("--non-keyword-db")
    [void]$arguments.Add($ResolvedNonKeywordDb)
    [void]$arguments.Add("--summary-sentences")
    [void]$arguments.Add([string]$SummarySentences)
    [void]$arguments.Add("--resource-mode")
    [void]$arguments.Add($ResourceMode)
    [void]$arguments.Add("--max-cpu-percent")
    [void]$arguments.Add([string]$MaxCpuPercent)
    [void]$arguments.Add("--max-memory-percent")
    [void]$arguments.Add([string]$MaxMemoryPercent)
    [void]$arguments.Add("--batch-size")
    [void]$arguments.Add([string]$BatchSize)
    [void]$arguments.Add("--max-workers")
    [void]$arguments.Add([string]$MaxWorkers)
    [void]$arguments.Add("--native-thread-limit")
    [void]$arguments.Add([string]$NativeThreadLimit)
    if (-not $Recursive) { [void]$arguments.Add("--no-recursive") }
    if ($DisableDiskCache.IsPresent) { [void]$arguments.Add("--disable-disk-cache") }
    if ($DisableAnalyticsExports.IsPresent) { [void]$arguments.Add("--disable-analytics-exports") }
    if ($DisableCompressedJson.IsPresent) { [void]$arguments.Add("--disable-compressed-json") }
    if ($KeywordDb) {
        [void]$arguments.Add("--keyword-db")
        [void]$arguments.Add([System.IO.Path]::GetFullPath($KeywordDb))
    }
    if ($SsotDb) {
        [void]$arguments.Add("--ssot-db")
        [void]$arguments.Add([System.IO.Path]::GetFullPath($SsotDb))
    }
    foreach ($review in $ResolvedReviews) {
        [void]$arguments.Add("--keyword-review")
        [void]$arguments.Add($review)
    }
    if ($EnableLocalLlm.IsPresent) {
        [void]$arguments.Add("--enable-local-llm")
        [void]$arguments.Add("--local-llm-provider")
        [void]$arguments.Add($LocalLlmProvider)
        [void]$arguments.Add("--local-llm-model")
        [void]$arguments.Add($LocalLlmModel)
        [void]$arguments.Add("--local-llm-endpoint")
        [void]$arguments.Add($LocalLlmEndpoint)
    }
    & $ResolvedPython @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "NLP 引擎執行失敗，ExitCode=$LASTEXITCODE"
    }
}

function def_ReadGate {
    param([Parameter(Mandatory = $true)][string]$ResultPath)
    $result = Get-Content -LiteralPath $ResultPath -Raw -Encoding UTF8 | ConvertFrom-Json
    return $result.gate.gate
}

function def_StartKeywordReviewServer {
    param(
        [Parameter(Mandatory = $true)][string]$ResolvedPython,
        [Parameter(Mandatory = $true)][string]$ServerPath,
        [Parameter(Mandatory = $true)][string]$HtmlPath,
        [Parameter(Mandatory = $true)][string]$DatabasePath
    )
    $token = ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N"))
    $values = @(
        $ServerPath, "--html", $HtmlPath, "--db", $DatabasePath,
        "--token", $token, "--host", "127.0.0.1", "--port", [string]$KeywordReviewPort,
        "--idle-seconds", [string]$KeywordReviewIdleSeconds
    )
    $argumentLine = ($values | ForEach-Object { def_QuoteProcessArgument -Value ([string]$_) }) -join " "
    $process = Start-Process -FilePath $ResolvedPython -ArgumentList $argumentLine -PassThru
    Start-Sleep -Milliseconds 800
    if ($process.HasExited) {
        throw "本機關鍵字審核服務啟動失敗，ExitCode=$($process.ExitCode)"
    }
    return $process
}

# =============================================================================
# def 04. 主流程
# =============================================================================

function def_Main {
    def_WriteStage -Percent 3 -Message "Preflight · PowerShell 7 / local-only / no install / no source mutation"
    def_TestPowerShellAst -ScriptPath $PSCommandPath
    def_ShowResourceSnapshot -Label "BEFORE"

    def_WriteStage -Percent 9 -Message "Resolve Python, governed inputs and keyword review decisions"
    $resolvedPython = def_ResolvePython -Command $PythonExe
    $resolvedInputs = def_ResolveInputPaths -Paths $InputPath
    $resolvedReviews = def_ResolveOptionalFiles -Paths $KeywordReviewPath
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDir)
    [void][System.IO.Directory]::CreateDirectory($resolvedOutput)
    $resolvedNonKeywordDb = def_ResolveWritablePath -Value $NonKeywordDb -Fallback (Join-Path $resolvedOutput "VIA_NLP_NonKeyword_SSOT.sqlite3")

    $enginePath = Join-Path $PSScriptRoot "via_nlp_fusion_engine.py"
    $resourcePath = Join-Path $PSScriptRoot "via_resource_optimizer.py"
    $keywordPath = Join-Path $PSScriptRoot "via_financial_keyword_governance.py"
    $serverPath = Join-Path $PSScriptRoot "via_keyword_review_server.py"
    foreach ($required in @($enginePath, $resourcePath, $keywordPath, $serverPath)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "找不到必要引擎：$required"
        }
    }

    def_WriteStage -Percent 17 -Message "Compile Python core, resource optimizer and keyword governance"
    & $resolvedPython -m py_compile $enginePath $resourcePath $keywordPath $serverPath (Join-Path $PSScriptRoot "via_text_intelligence.py")
    if ($LASTEXITCODE -ne 0) { throw "Python compile 驗證失敗" }

    if ($RunTests) {
        def_WriteStage -Percent 28 -Message "Run unit / integration / regression / resource tests"
        def_InvokePythonTests -ResolvedPython $resolvedPython -ProjectDir $PSScriptRoot
        def_WriteStage -Percent 40 -Message "All Python tests passed" -State "PASS"
    }
    else {
        def_WriteStage -Percent 40 -Message "Tests skipped by explicit parameter" -State "WARN"
    }

    def_WriteStage -Percent 48 -Message "Prepare append-only run output and SSD spill scope"
    def_ShowResourceSnapshot -Label "PRE-ENGINE"

    def_WriteStage -Percent 58 -Message "Execute 18-stage NLP + adaptive CPU/DRAM + bilingual financial keywords"
    $invokeParameters = @{
        ResolvedPython      = $resolvedPython
        EnginePath         = $enginePath
        ResolvedInputs      = $resolvedInputs
        ResolvedReviews     = $resolvedReviews
        ResolvedOutput      = $resolvedOutput
        ResolvedNonKeywordDb = $resolvedNonKeywordDb
    }
    def_InvokeNlpEngine @invokeParameters

    def_WriteStage -Percent 82 -Message "Validate JSON, HTML, SQLite, resource evidence and non-keyword SSOT"
    $resultPath = Join-Path $resolvedOutput "VIA_NLP_Fusion_Result.json"
    $htmlPath = Join-Path $resolvedOutput "VIA_NLP_Fusion_Command_Center.html"
    $resourceEvidencePath = Join-Path $resolvedOutput "VIA_NLP_Resource_Evidence.json"
    $candidatePath = Join-Path $resolvedOutput "VIA_NLP_Financial_Keyword_Candidates.csv"
    foreach ($required in @($resultPath, $htmlPath, $resourceEvidencePath, $candidatePath, $resolvedNonKeywordDb)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "缺少必要輸出：$required"
        }
    }
    $gate = def_ReadGate -ResultPath $resultPath
    if ($gate -eq "FAIL_CLOSED") {
        throw "NLP Gate=FAIL_CLOSED；請查看 HTML、Quality Findings 與 Resource Evidence。"
    }

    def_WriteStage -Percent 92 -Message "Seal SHA-256 evidence and prepare keyword review"
    $resultHash = (Get-FileHash -LiteralPath $resultPath -Algorithm SHA256).Hash
    $htmlHash = (Get-FileHash -LiteralPath $htmlPath -Algorithm SHA256).Hash
    $reviewProcess = $null
    if ($OpenHtml.IsPresent) {
        $reviewProcess = def_StartKeywordReviewServer `
            -ResolvedPython $resolvedPython `
            -ServerPath $serverPath `
            -HtmlPath $htmlPath `
            -DatabasePath $resolvedNonKeywordDb
    }

    def_ShowResourceSnapshot -Label "AFTER"
    def_WriteStage -Percent 100 -Message "VIA NLP Fusion v0210 delivery complete" -State "PASS"
    Write-Progress -Activity "VIA NLP Fusion Engine v0210" -Completed
    Write-Host "def Gate              : $gate" -ForegroundColor Green
    Write-Host "def Result            : $resultPath" -ForegroundColor White
    Write-Host "def Result SHA256     : $resultHash" -ForegroundColor White
    Write-Host "def HTML              : $htmlPath" -ForegroundColor White
    Write-Host "def HTML SHA256       : $htmlHash" -ForegroundColor White
    Write-Host "def Non-Keyword SSOT  : $resolvedNonKeywordDb" -ForegroundColor White
    Write-Host "def Resource Evidence : $resourceEvidencePath" -ForegroundColor White
    if ($null -ne $reviewProcess) {
        Write-Host "def Review Server PID : $($reviewProcess.Id)" -ForegroundColor White
        Write-Host "def Review Server     : http://127.0.0.1:$KeywordReviewPort/ (idle timeout $KeywordReviewIdleSeconds sec)" -ForegroundColor White
    }
    Write-Host "def PowerShell remains open." -ForegroundColor Yellow
}

def_Main

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

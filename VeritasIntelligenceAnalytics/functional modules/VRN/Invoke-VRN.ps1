#Requires -Version 7.0

param(
    [switch]$Run,
    [switch]$SafeProbe,
    [switch]$Plan,
    [string]$TargetFile
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

# >>> VIA_VRN_RESEARCH_REPORT_SSOT_V2_ENTRYPOINT_INTEGRATION_v0153B >>>
# This block is generated and governed by VIA v0153B.
# It resolves the active Research Report SSOT pointer at entrypoint startup.
# It does not import, dot-source, execute, or mutate any SSOT authority.
$script:VIA_VRN_ResearchReportSSOT_ActiveContext = $null

function def_Resolve_VRNResearchReportSSOTActiveV2 {
    [CmdletBinding()]
    param()

    $pointerPath = Join-Path $PSScriptRoot (
        "SSOT\VRN_ResearchReport_SSOT.active.json"
    )

    if (-not (Test-Path -LiteralPath $pointerPath -PathType Leaf)) {
        throw "VRN Research Report active pointer is missing: $pointerPath"
    }

    $pointer = (
        Get-Content -LiteralPath $pointerPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    )

    if ($pointer.promotion_state -ne "ACTIVE") {
        throw "VRN Research Report pointer is not ACTIVE."
    }

    $resourceMap = @(
        [pscustomobject]@{
            Name = "canonical"
            Path = [string]$pointer.active_canonical_path
            Sha256 = [string]$pointer.active_canonical_sha256
        },
        [pscustomobject]@{
            Name = "schema"
            Path = [string]$pointer.active_schema_path
            Sha256 = [string]$pointer.active_schema_sha256
        },
        [pscustomobject]@{
            Name = "record_schema"
            Path = [string]$pointer.active_record_json_schema_path
            Sha256 = [string]$pointer.active_record_json_schema_sha256
        },
        [pscustomobject]@{
            Name = "reader_adapter"
            Path = [string]$pointer.runtime_adapter_path
            Sha256 = [string]$pointer.runtime_adapter_sha256
        }
    )

    foreach ($resource in $resourceMap) {
        if (
            [string]::IsNullOrWhiteSpace($resource.Path) -or
            -not (Test-Path -LiteralPath $resource.Path -PathType Leaf)
        ) {
            throw (
                "VRN Research Report pointer target missing: {0} -> {1}" -f
                $resource.Name,
                $resource.Path
            )
        }

        $actualSha = (
            Get-FileHash -LiteralPath $resource.Path -Algorithm SHA256
        ).Hash.ToLowerInvariant()

        if (
            [string]::IsNullOrWhiteSpace($resource.Sha256) -or
            $actualSha -ne $resource.Sha256.ToLowerInvariant()
        ) {
            throw (
                "VRN Research Report pointer target SHA mismatch: {0}" -f
                $resource.Name
            )
        }
    }

    return [pscustomobject]@{
        PointerPath = $pointerPath
        TransactionId = [string]$pointer.transaction_id
        CanonicalPath = [string]$pointer.active_canonical_path
        CanonicalSha256 = [string]$pointer.active_canonical_sha256
        SchemaPath = [string]$pointer.active_schema_path
        SchemaSha256 = [string]$pointer.active_schema_sha256
        RecordSchemaPath = [string]$pointer.active_record_json_schema_path
        RecordSchemaSha256 = [string]$pointer.active_record_json_schema_sha256
        ReaderAdapterPath = [string]$pointer.runtime_adapter_path
        ReaderAdapterSha256 = [string]$pointer.runtime_adapter_sha256
        ReaderModes = @($pointer.reader_modes)
        DefaultReaderMode = "resolved_only"
        UnresolvedReviewQueueEnabled = [bool]$pointer.unresolved_review_queue_enabled
    }
}

$script:VIA_VRN_ResearchReportSSOT_ActiveContext = (
    def_Resolve_VRNResearchReportSSOTActiveV2
)

$env:VIA_VRN_RESEARCH_REPORT_SSOT_ACTIVE_POINTER = (
    $script:VIA_VRN_ResearchReportSSOT_ActiveContext.PointerPath
)
$env:VIA_VRN_RESEARCH_REPORT_SSOT_CANONICAL = (
    $script:VIA_VRN_ResearchReportSSOT_ActiveContext.CanonicalPath
)
$env:VIA_VRN_RESEARCH_REPORT_SSOT_SCHEMA = (
    $script:VIA_VRN_ResearchReportSSOT_ActiveContext.SchemaPath
)
$env:VIA_VRN_RESEARCH_REPORT_SSOT_RECORD_SCHEMA = (
    $script:VIA_VRN_ResearchReportSSOT_ActiveContext.RecordSchemaPath
)
$env:VIA_VRN_RESEARCH_REPORT_SSOT_READER_ADAPTER = (
    $script:VIA_VRN_ResearchReportSSOT_ActiveContext.ReaderAdapterPath
)
$env:VIA_VRN_RESEARCH_REPORT_SSOT_READER_MODE = (
    $script:VIA_VRN_ResearchReportSSOT_ActiveContext.DefaultReaderMode
)
# <<< VIA_VRN_RESEARCH_REPORT_SSOT_V2_ENTRYPOINT_INTEGRATION_v0153B <<<


Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

# =============================================================================
# VIA v035.7 Guarded Root Entry
# Project   : VRN
# Candidate : C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\60_PowerShell_Entry_Internal\Invoke-VRN-MQ-NoOCR-Staging-v222.ps1
# =============================================================================
# Default behavior is SAFE PROBE only.
# Full run requires explicit -Run.
# =============================================================================


$SelectedCandidate = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\60_PowerShell_Entry_Internal\Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
$ExpectedEntry = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VRN\Invoke-VRN.ps1"

function Write-GuardedLine {
    param([string]$Level,[string]$Message)
    $c="Gray"
    if($Level -eq "OK"){$c="Green"}
    elseif($Level -eq "WARN"){$c="Yellow"}
    elseif($Level -eq "FAIL"){$c="Red"}
    elseif($Level -eq "RUN"){$c="Cyan"}
    Write-Host "[$(Get-Date -Format 'HH:mm:ss.fff')] [$Level] $Message" -ForegroundColor $c
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VIA v035.7 · VRN Guarded Root Entry" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

if(-not(Test-Path -LiteralPath $SelectedCandidate -PathType Leaf)){
    Write-GuardedLine "FAIL" "Selected candidate missing: $SelectedCandidate"
    return
}

try {
    $tokens=$null
    $errors=$null
    [System.Management.Automation.Language.Parser]::ParseFile($SelectedCandidate,[ref]$tokens,[ref]$errors)|Out-Null

    if(@($errors).Count -eq 0){
        Write-GuardedLine "OK" "Candidate parser OK."
    } else {
        Write-GuardedLine "FAIL" "Candidate parser errors: $(@($errors).Count)"
        @($errors | Select-Object -First 10) | ForEach-Object { Write-GuardedLine "FAIL" $_.Message }
        return
    }

    $item=Get-Item -LiteralPath $SelectedCandidate -Force
    $hash=(Get-FileHash -LiteralPath $SelectedCandidate -Algorithm SHA256).Hash
    Write-GuardedLine "OK" "Candidate bytes: $($item.Length)"
    Write-GuardedLine "OK" "Candidate SHA256: $hash"
} catch {
    Write-GuardedLine "FAIL" $_.Exception.Message
    return
}

if($Plan -or -not $Run){
    Write-GuardedLine "OK" "SAFE_PROBE_COMPLETE"
    Write-GuardedLine "WARN" "Default mode does not execute candidate. Use -Run only after production approval."
    Write-GuardedLine "WARN" "Expected entry: $ExpectedEntry"
    return
}

if ([string]::IsNullOrWhiteSpace($TargetFile)) {
    Write-GuardedLine "FAIL" "Explicit -TargetFile is required with -Run."
    throw "Explicit -TargetFile is required with -Run."
}

if (-not (Test-Path -LiteralPath $TargetFile -PathType Leaf)) {
    Write-GuardedLine "FAIL" "TargetFile not found: $TargetFile"
    throw "TargetFile not found: $TargetFile"
}

if ([System.IO.Path]::GetExtension($TargetFile) -ine ".pdf") {
    Write-GuardedLine "FAIL" "TargetFile must be a .pdf file: $TargetFile"
    throw "TargetFile must be a .pdf file: $TargetFile"
}

Write-GuardedLine "RUN" "Explicit -Run and validated -TargetFile detected."
& pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $SelectedCandidate -TargetFile $TargetFile

$CandidateExitCode = $LASTEXITCODE

if ($CandidateExitCode -ne 0) {
    Write-GuardedLine "FAIL" "Selected candidate exited with code $CandidateExitCode."
    throw "Selected candidate exited with code $CandidateExitCode."
}

Write-GuardedLine "OK" "CANDIDATE_RUN_COMPLETE"

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

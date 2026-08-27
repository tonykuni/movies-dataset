[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$SourcePath,
    [Parameter(Mandatory)] [ValidateRange(1, 1048576)] [int]$MaximumBytes,
    [Parameter(Mandatory)] [string]$OutputPath,
    [Parameter(Mandatory)] [ValidateSet("true", "false")] [string]$ContentReadAuthorized
)


# =============================================================================
# def 00. BOUNDARY
# =============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"


# =============================================================================
# def 01. RUN-LOCAL JSON
# =============================================================================

function def_WriteJson {
    param(
        [Parameter(Mandatory)] [object]$Data,
        [Parameter(Mandatory)] [string]$Path
    )
    $def_Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $def_Parent -PathType Container)) {
        throw "Output parent not found: $def_Parent"
    }
    $def_Temp = Join-Path $def_Parent (".{0}.{1}.tmp" -f (Split-Path -Leaf $Path), $PID)
    $Data |
        ConvertTo-Json -Depth 12 |
        Set-Content -LiteralPath $def_Temp -Encoding utf8NoBOM
    Move-Item -LiteralPath $def_Temp -Destination $Path
}


# =============================================================================
# def 02. NON-PERSISTENT BUFFER PROFILE
# =============================================================================

function def_GetBufferProfile {
    param(
        [Parameter(Mandatory)] [byte[]]$Buffer,
        [Parameter(Mandatory)] [int]$Count
    )
    $def_NewlineCount = 0
    $def_CommaCount = 0
    $def_ContainsNul = $false
    for ($def_Index = 0; $def_Index -lt $Count; $def_Index++) {
        if ($Buffer[$def_Index] -eq 10) {
            $def_NewlineCount++
        }
        elseif ($Buffer[$def_Index] -eq 44) {
            $def_CommaCount++
        }
        elseif ($Buffer[$def_Index] -eq 0) {
            $def_ContainsNul = $true
        }
    }
    $def_Bom = "NONE"
    if ($Count -ge 3 -and $Buffer[0] -eq 239 -and $Buffer[1] -eq 187 -and $Buffer[2] -eq 191) {
        $def_Bom = "UTF8"
    }
    elseif ($Count -ge 2 -and $Buffer[0] -eq 255 -and $Buffer[1] -eq 254) {
        $def_Bom = "UTF16_LE"
    }
    elseif ($Count -ge 2 -and $Buffer[0] -eq 254 -and $Buffer[1] -eq 255) {
        $def_Bom = "UTF16_BE"
    }
    return [ordered]@{
        bytes_read = $Count
        bom = $def_Bom
        newline_count = $def_NewlineCount
        comma_count = $def_CommaCount
        contains_nul = $def_ContainsNul
        raw_content_persisted = $false
        content_hash_computed = $false
    }
}


# =============================================================================
# def 03. DOTNET FILESTREAM PROBE
# =============================================================================

function def_Main {
    $def_Result = [ordered]@{
        outcome = "NOT_STARTED"
        source_open_attempts = 0
        source_open_successes = 0
        source_bytes_read = 0
        buffer_profile = [ordered]@{}
        error = ""
        errno = $null
        winerror = $null
        source_hashes = 0
        source_writes = 0
        source_copies = 0
        source_content_artifacts = 0
        source_metadata_reads = 0
        content_read_safe = ($ContentReadAuthorized -eq "true")
        implicit_hydration_risk = ($ContentReadAuthorized -ne "true")
    }
    $def_Stream = $null
    try {
        if ($ContentReadAuthorized -ne "true") {
            $def_Result.outcome = "SKIPPED_IMPLICIT_HYDRATION_OR_PREFLIGHT_RISK"
            return
        }
        $def_Result.source_open_attempts = 1
        $def_Share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
        $def_Stream = [System.IO.File]::Open(
            $SourcePath,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            $def_Share
        )
        $def_Result.source_open_successes = 1
        $def_Buffer = [byte[]]::new($MaximumBytes)
        $def_Read = $def_Stream.Read($def_Buffer, 0, $MaximumBytes)
        $def_Result.outcome = "OPEN_SUCCESS"
        $def_Result.source_bytes_read = $def_Read
        $def_Result.buffer_profile = def_GetBufferProfile -Buffer $def_Buffer -Count $def_Read
    }
    catch {
        $def_Result.outcome = if ($null -eq $def_Stream) { "OPEN_FAILED" } else { "READ_FAILED_AFTER_OPEN" }
        $def_Result.error = "$($_.Exception.GetType().FullName): $($_.Exception.Message)"
        $def_Result.hresult = $_.Exception.HResult
    }
    finally {
        if ($null -ne $def_Stream) {
            $def_Stream.Dispose()
        }
        def_WriteJson -Data $def_Result -Path $OutputPath
    }
}

def_Main

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

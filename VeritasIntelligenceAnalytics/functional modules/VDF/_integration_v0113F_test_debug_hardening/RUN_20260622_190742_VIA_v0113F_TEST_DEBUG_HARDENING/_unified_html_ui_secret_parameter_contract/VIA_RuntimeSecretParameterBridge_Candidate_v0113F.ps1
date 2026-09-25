# =============================================================================
# def VIA · Runtime Secret Parameter Bridge Candidate · v0113F
# Policy: never log secret value, never write secret value to disk.
# =============================================================================

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
function New-VIAFredRuntimeSecretPayload {
    param(
        [Parameter(Mandatory=$true)]
        [SecureString]$FRED_API_KEY
    )

    return [pscustomobject][ordered]@{
        provider = "FRED"
        secret_parameter_name = "FRED_API_KEY"
        secret_parameter_secure = $FRED_API_KEY
        value_printed = $false
        persistence = "runtime_memory_only"
        forbidden_sinks = "csv,json,html,log,localStorage,sessionStorage,url_query,canonical_registry"
    }
}


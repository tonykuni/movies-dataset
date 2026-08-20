# =============================================================================
# def VIA · Runtime Secret Parameter Bridge Candidate · v0113F
# Policy: never log secret value, never write secret value to disk.
# =============================================================================

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

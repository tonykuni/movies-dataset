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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

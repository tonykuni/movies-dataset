#requires -Version 7.0
$ErrorActionPreference = "Stop"

function Invoke-VDF {
    param(
        [ValidateSet("status","open-database","open-header-registry","show-active-pointer","show-ssot","show-output-manifest")]
        [string]$Action = "status"
    )

    $Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
    $VdfDict = Join-Path $Root "dict\VDF"
    $SsotDir = Join-Path $VdfDict "_ssot"
    $DbDir = Join-Path $VdfDict "DATABASE"

    $ParamsJson = Join-Path $SsotDir "VDF_Extraction_Params_SSOT.json"
    $HeaderRegistryJson = Join-Path $SsotDir "VDF_DataScope_HeaderRegistry_SSOT.json"
    $ActivePointer = Join-Path $VdfDict "_active\VDF_ACTIVE_POINTER.json"
    $OutputManifest = "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_ACTIVE_READER_USERTEST_v014_20260609_215513\\registry\\VDF_DatabaseSkeleton_OutputManifest_v014.json"

    if ($Action -eq "status") {
        [pscustomobject]@{
            status = "VDF_ACTIVE_READER_READY"
            root = $Root
            params_ssot = $ParamsJson
            header_registry = $HeaderRegistryJson
            database = $DbDir
            active_pointer = $ActivePointer
            output_manifest = $OutputManifest
            policy = "Read SSOT. No delete. No Stop-Process. No exit."
        } | Format-List
        return
    }

    if ($Action -eq "open-database") {
        Start-Process -FilePath $DbDir
        return
    }

    if ($Action -eq "open-header-registry") {
        Start-Process -FilePath $HeaderRegistryJson
        return
    }

    if ($Action -eq "show-active-pointer") {
        Get-Content -LiteralPath $ActivePointer -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
        return
    }

    if ($Action -eq "show-ssot") {
        Get-Content -LiteralPath $ParamsJson -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
        return
    }

    if ($Action -eq "show-output-manifest") {
        Get-Content -LiteralPath $OutputManifest -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
        return
    }
}

Invoke-VDF @args

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

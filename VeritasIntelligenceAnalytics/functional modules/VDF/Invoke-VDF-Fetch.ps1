#requires -Version 7.0
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
$ErrorActionPreference = "Stop"

function Invoke-VDF-Fetch {
    param(
        [ValidateSet("status","open-database","show-plan","show-manifest","show-result","open-report")]
        [string]$Action = "status"
    )

    $Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
    $DatabaseRoot = Join-Path $Root "dict\VDF\DATABASE"
    $FetchPlan = "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_PRODUCTION_FETCH_CONTROLLER_v016_20260609_220337\\registry\\VDF_ProductionFetchPlan_v016.json"
    $FetchManifest = "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_PRODUCTION_FETCH_CONTROLLER_v016_20260609_220337\\registry\\VDF_ProductionFetchManifest_v016.json"
    $FetchResult = "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_PRODUCTION_FETCH_CONTROLLER_v016_20260609_220337\\runtime\\vdf_production_fetch_result_v016.json"
    $HtmlReport = "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_PRODUCTION_FETCH_CONTROLLER_v016_20260609_220337\\report\\VDF_ProductionFetchController_Report_v016.html"
    $PythonController = "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_PRODUCTION_FETCH_CONTROLLER_v016_20260609_220337\\runtime\\vdf_production_fetch_controller_v016.py"

    if ($Action -eq "status") {
        [pscustomobject]@{
            status = "VDF_PRODUCTION_FETCH_CONTROLLER_READY"
            database_root = $DatabaseRoot
            fetch_plan = $FetchPlan
            fetch_manifest = $FetchManifest
            fetch_result = $FetchResult
            python_controller = $PythonController
            html_report = $HtmlReport
            policy = "Network disabled unless caller explicitly enables it through v016 generator. No delete. No Stop-Process. No exit."
        } | Format-List
        return
    }

    if ($Action -eq "open-database") {
        Start-Process -FilePath $DatabaseRoot
        return
    }

    if ($Action -eq "show-plan") {
        Get-Content -LiteralPath $FetchPlan -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
        return
    }

    if ($Action -eq "show-manifest") {
        Get-Content -LiteralPath $FetchManifest -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
        return
    }

    if ($Action -eq "show-result") {
        Get-Content -LiteralPath $FetchResult -Raw -Encoding UTF8 | ConvertFrom-Json | Format-List
        return
    }

    if ($Action -eq "open-report") {
        Start-Process -FilePath $HtmlReport
        return
    }
}

Invoke-VDF-Fetch @args


# VIA Downloads Register All + Cross Analysis All
# Version: 20260702
# Policy: read-only scan, no execution, no source mutation, append-only output.

$ErrorActionPreference = "Continue"

$def_Version = "20260702"
$def_RunId = "RUN_" + (Get-Date -Format "yyyyMMdd_HHmmss") + "_VIA_DOWNLOADS_REGISTER_ALL_CROSS_ANALYSIS"
$def_OutRoot = Join-Path $env:USERPROFILE "Downloads\VIA_Downloads_RegisterAll_CrossAnalysis_$def_RunId"

$def_Paths = @(
    "C:\Users\tonyk\Downloads\PMIS-Lite (4)"
    "C:\Users\tonyk\Downloads\VIA_UI_FILE_READER_GAP_AUDITOR_v20260702"
    "C:\Users\tonyk\Downloads\VIA_UI_MASTER_PARAMETER_LIBRARY_v20260702"
    "C:\Users\tonyk\Downloads\1743478702766.jpg"
    "C:\Users\tonyk\Downloads\AUTO_SSOT_Sales_Battlecard.md"
    "C:\Users\tonyk\Downloads\BOM_Template_Blank (1).csv"
    "C:\Users\tonyk\Downloads\BOM_Template_Blank.csv"
    "C:\Users\tonyk\Downloads\BOM_Template_Sample (1).csv"
    "C:\Users\tonyk\Downloads\BOM_Template_Sample.csv"
    "C:\Users\tonyk\Downloads\SUP_MDL048_FetchMailbox.py"
    "C:\Users\tonyk\Downloads\image_thumb51.png"
    "C:\Users\tonyk\Downloads\launcher_minimal (1).html"
    "C:\Users\tonyk\Downloads\launcher_minimal.html"
    "C:\Users\tonyk\Downloads\PMIS-Lite (4).zip"
    "C:\Users\tonyk\Downloads\PMIS-Lite_PRO_2026.md"
    "C:\Users\tonyk\Downloads\PMIS-Lite_UX_FEEDBACK_2026.md"
    "C:\Users\tonyk\Downloads\SAP-MRO-Master-Data-Management.png"
    "C:\Users\tonyk\Downloads\SuperBOM_Financial_Model.html"
    "C:\Users\tonyk\Downloads\SuperBOM_Template_Sample.csv"
    "C:\Users\tonyk\Downloads\VIA_Capability_Matrix (1).html"
    "C:\Users\tonyk\Downloads\VIA_Capability_Matrix (2).html"
    "C:\Users\tonyk\Downloads\VIA_Capability_Matrix (3).html"
    "C:\Users\tonyk\Downloads\VIA_Capability_Matrix.html"
    "C:\Users\tonyk\Downloads\VIA_Central_Management.html"
    "C:\Users\tonyk\Downloads\VIA_CostStructure_Peer_Verify.html"
    "C:\Users\tonyk\Downloads\VIA_Doomsday_Intake.html"
    "C:\Users\tonyk\Downloads\VIA_Electric_SuperBOM.html"
    "C:\Users\tonyk\Downloads\VIA_Financial_Statements (1).html"
    "C:\Users\tonyk\Downloads\VIA_Hierarchy_Index_Valuation.html"
    "C:\Users\tonyk\Downloads\VIA_Industry_CapexProcessEquipment (1).html"
    "C:\Users\tonyk\Downloads\VIA_Industry_CapexProcessEquipment.html"
    "C:\Users\tonyk\Downloads\VIA_Integrated_Platform (1).html"
    "C:\Users\tonyk\Downloads\VIA_Integrated_Platform (2).html"
    "C:\Users\tonyk\Downloads\VIA_INTEGRATED_UI_SYSTEM_v20260702.zip"
    "C:\Users\tonyk\Downloads\VIA_Master_Codex (1).md"
    "C:\Users\tonyk\Downloads\VIA_Master_Codex (2).md"
    "C:\Users\tonyk\Downloads\VIA_Master_Codex (3).md"
    "C:\Users\tonyk\Downloads\VIA_Master_Codex.md"
    "C:\Users\tonyk\Downloads\VIA_MSProject_SSOT_Sync (1).html"
    "C:\Users\tonyk\Downloads\VIA_MSProject_SSOT_Sync (2).html"
    "C:\Users\tonyk\Downloads\VIA_MSProject_SSOT_Sync (3).html"
    "C:\Users\tonyk\Downloads\VIA_MSProject_SSOT_Sync.html"
    "C:\Users\tonyk\Downloads\VIA_PMIS_ReadOnly_SuperRegistry_v0100.ps1"
    "C:\Users\tonyk\Downloads\via_pmis_registry_builder_v0100.py"
    "C:\Users\tonyk\Downloads\VIA_PowerThermal_Registry.html"
    "C:\Users\tonyk\Downloads\VIA_PowerThermal_SAP_SuperBOM.html"
    "C:\Users\tonyk\Downloads\VIA_PSU_Thermal_AllInOne (1).html"
    "C:\Users\tonyk\Downloads\VIA_PSU_Thermal_AllInOne.html"
    "C:\Users\tonyk\Downloads\VIA_PSU_Thermal_SSOT.html"
    "C:\Users\tonyk\Downloads\VIA_SAP_FixedCode_CostObject_Registry_20260702.json"
    "C:\Users\tonyk\Downloads\VIA_Super_BOM_Dashboard_Delta_AcBel_LiteOn_v20260701.html"
    "C:\Users\tonyk\Downloads\VIA_Super_BOM_OnePage_SAP_ManagementAccounting_Delta_LiteOn_AcBel_v20260701.html"
    "C:\Users\tonyk\Downloads\VIA_Super_Engine.html"
    "C:\Users\tonyk\Downloads\VIA_SuperBOM_Relational_Intelligence_Console_20260702.html"
    "C:\Users\tonyk\Downloads\VIA_SuperBOM_Relational_SSOT_20260702 (1).json"
    "C:\Users\tonyk\Downloads\VIA_SuperBOM_Relational_SSOT_20260702.json"
    "C:\Users\tonyk\Downloads\VIA_Synonym_SSOT_PLM_PMBOK (1).html"
    "C:\Users\tonyk\Downloads\VIA_Synonym_SSOT_PLM_PMBOK.html"
    "C:\Users\tonyk\Downloads\VIA_UI_COMPLETE_CHECKLIST_AND_GAP_MATRIX_v20260702 (1).xlsx"
    "C:\Users\tonyk\Downloads\VIA_UI_COMPLETE_CHECKLIST_AND_GAP_MATRIX_v20260702.xlsx"
    "C:\Users\tonyk\Downloads\VIA_UI_FILE_READER_GAP_AUDITOR_v20260702 (1).zip"
    "C:\Users\tonyk\Downloads\VIA_UI_FILE_READER_GAP_AUDITOR_v20260702.zip"
    "C:\Users\tonyk\Downloads\VIA_UI_MASTER_PARAMETER_LIBRARY_v20260702.zip"
    "C:\Users\tonyk\Downloads\VIA_Unified_Code_Registry.html"
    "C:\Users\tonyk\Downloads\VIS_Launch_All.ps1"
    "C:\Users\tonyk\Downloads\VISWorkbench_AUTO_CODING_SSOT.md"
    "C:\Users\tonyk\Downloads\VISWorkbench_BOM_TEMPLATE_PLAN (1).md"
    "C:\Users\tonyk\Downloads\VISWorkbench_BOM_TEMPLATE_PLAN.md"
    "C:\Users\tonyk\Downloads\VISWorkbench_ENTERPRISE_SSOT.md"
    "C:\Users\tonyk\Downloads\VISWorkbench_OAUTH_2026.md"
    "C:\Users\tonyk\Downloads\VISWorkbench_PSU_INDUSTRY_SSOT (1).md"
    "C:\Users\tonyk\Downloads\VISWorkbench_PSU_INDUSTRY_SSOT.md"
    "C:\Users\tonyk\Downloads\VISWorkbench_SAP_PLM_REFERENCE.md"
    "C:\Users\tonyk\Downloads\VISWorkbench_SUPER_BOM_PLAN (1).md"
    "C:\Users\tonyk\Downloads\VISWorkbench_SUPER_BOM_PLAN.md"
    "C:\Users\tonyk\Downloads\VISWorkbench_VIA_IMPORT_PROMPT.md"
    "C:\Users\tonyk\Downloads\1520187732429.jpg"
    "C:\Users\tonyk\Downloads\Benefits-of-Process-Mining (1).png"
    "C:\Users\tonyk\Downloads\Benefits-of-Process-Mining.png"
    "C:\Users\tonyk\Downloads\How-Does-Process-Mining-Work.png"
    "C:\Users\tonyk\Downloads\indices_flow (1).html"
    "C:\Users\tonyk\Downloads\indices_flow.html"
    "C:\Users\tonyk\Downloads\p766 (1).pdf"
    "C:\Users\tonyk\Downloads\p766.pdf"
    "C:\Users\tonyk\Downloads\PMIS-Lite (1).zip"
    "C:\Users\tonyk\Downloads\PMIS-Lite (2).zip"
    "C:\Users\tonyk\Downloads\PMIS-Lite (3).zip"
    "C:\Users\tonyk\Downloads\PMIS-Lite.zip"
    "C:\Users\tonyk\Downloads\VIA_Financial_Statements.html"
    "C:\Users\tonyk\Downloads\VIA_Industry_BOM_Professional_HTML.html"
    "C:\Users\tonyk\Downloads\VIA_Industry360_Intelligence_Suite_Professional.html"
    "C:\Users\tonyk\Downloads\VIA_Integrated_Platform.html"
    "C:\Users\tonyk\Downloads\VIS_Global_Crude_Oil_Market_v0111.html"
    "C:\Users\tonyk\Downloads\SUP_MDL166_VpnsAstSymbolEngine.py"
    "C:\Users\tonyk\Downloads\vpns_rename_map.SAMPLE.json"
    "C:\Users\tonyk\Downloads\一鍵讀信箱.bat"
    "C:\Users\tonyk\Downloads\台達電.docx"
    "C:\Users\tonyk\Downloads\_backup_nettoolkit_20260213_235824"
    "C:\Users\tonyk\Downloads\_VPN_SAFE_INTEGRATION_OUT"
    "C:\Users\tonyk\Downloads\backup_20251013_115831"
    "C:\Users\tonyk\Downloads\circle-flags-gh-pages"
    "C:\Users\tonyk\Downloads\DRUCK    Macro Terminal"
    "C:\Users\tonyk\Downloads\files (27)"
    "C:\Users\tonyk\Downloads\files (33)"
    "C:\Users\tonyk\Downloads\VDS_Integration_20260226_233923"
    "C:\Users\tonyk\Downloads\VDS_Integration_20260226_233933"
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
    "C:\Users\tonyk\Downloads\VIA_FlowSystem (2)"
    "C:\Users\tonyk\Downloads\02-difference-between-median-target-price-and-closing-price-top-and-bottom-10 (1).webp"
    "C:\Users\tonyk\Downloads\02-difference-between-median-target-price-and-closing-price-top-and-bottom-10.webp"
    "C:\Users\tonyk\Downloads\2026_macro_investment_engine_v10 (2).pdf"
    "C:\Users\tonyk\Downloads\circle-flags-gh-pages.zip"
    "C:\Users\tonyk\Downloads\EarningsInsight_062626.pdf"
    "C:\Users\tonyk\Downloads\factor_dict_matrix.html"
    "C:\Users\tonyk\Downloads\flow_monitor.html"
    "C:\Users\tonyk\Downloads\global_map_sim.html"
    "C:\Users\tonyk\Downloads\Invoke-VIA-SupportiveFunctionalRegistry-AIO-v0105.ps1"
    "C:\Users\tonyk\Downloads\perf_trend (1).html"
    "C:\Users\tonyk\Downloads\perf_trend.html"
    "C:\Users\tonyk\Downloads\spec.html"
    "C:\Users\tonyk\Downloads\Veritas Intelligence Analytics Brief.html"
    "C:\Users\tonyk\Downloads\Veritas Intelligence Analytics Brief.pdf"
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics_OnePage_System_Overview_v0200.html"
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics_Workbench_Enabler_Overview_v0300 (1).html"
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics_Workbench_Enabler_Overview_v0300 (2).html"
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics_Workbench_Enabler_Overview_v0300 (3).html"
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics_Workbench_Enabler_Overview_v0300.html"
    "C:\Users\tonyk\Downloads\VIA · 族群分類完善化 v1.1.pdf"
    "C:\Users\tonyk\Downloads\PMIS-Lite (3)"
)

function def_EnsureDir {
    param([string]$Path)
    if (!(Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_ClassifyPath {
    param([string]$Path)
    $low = $Path.ToLowerInvariant()
    $name = Split-Path -Leaf $Path
    $ext = [System.IO.Path]::GetExtension($name).ToLowerInvariant()

    if ($low -match "superbom|super_bom|bom_template|bom") { $domain = "SUPER_BOM" }
    elseif ($low -match "sap|plm|pmbok") { $domain = "SAP_PLM" }
    elseif ($low -match "pmis|msproject|project") { $domain = "PMIS_PROJECT" }
    elseif ($low -match "financial|valuation|coststructure|statements") { $domain = "FINANCIAL_MODEL" }
    elseif ($low -match "ui|launcher|integrated_platform|central_management") { $domain = "UI_PLATFORM" }
    elseif ($low -match "capability|unified_code|engine|registry|codex") { $domain = "REGISTRY_ENGINE" }
    elseif ($low -match "process-mining|process_mining|flow|benefits-of-process") { $domain = "PROCESS_MINING" }
    elseif ($low -match "oil|macro|earningsinsight|indices|factor") { $domain = "MARKET_MACRO" }
    elseif ($low -match "台達電|delta|powerthermal|psu_thermal|electric") { $domain = "COMPANY_INDUSTRY" }
    elseif ($ext -in @(".jpg",".jpeg",".png",".webp")) { $domain = "IMAGE_REFERENCE" }
    elseif ($ext -eq ".zip") { $domain = "PACKAGE_ARCHIVE" }
    elseif ($ext -in @(".py",".ps1",".bat",".cmd")) { $domain = "CODE_SCRIPT" }
    elseif ($ext -in @(".md",".txt",".docx",".pdf")) { $domain = "DOC_SOURCE" }
    else { $domain = "MISC" }

    if ([string]::IsNullOrWhiteSpace($ext)) { $ftype = "folder_or_no_extension" }
    elseif ($ext -in @(".html",".htm")) { $ftype = "html" }
    elseif ($ext -eq ".json") { $ftype = "json" }
    elseif ($ext -eq ".csv") { $ftype = "csv" }
    elseif ($ext -eq ".xlsx") { $ftype = "spreadsheet" }
    elseif ($ext -eq ".md") { $ftype = "markdown" }
    elseif ($ext -in @(".py",".ps1",".bat",".cmd")) { $ftype = "script" }
    elseif ($ext -in @(".jpg",".jpeg",".png",".webp")) { $ftype = "image" }
    elseif ($ext -in @(".pdf",".docx")) { $ftype = $ext.TrimStart(".") }
    elseif ($ext -eq ".zip") { $ftype = "archive" }
    else { $ftype = $ext.TrimStart(".") }

    return @{ domain=$domain; file_type=$ftype }
}

function def_ReadPreview {
    param([string]$Path, [string]$FileType)
    $result = @{ ok=$false; preview=""; error="" }
    try {
        if ($FileType -in @("html","json","csv","markdown","script","txt")) {
            $text = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
            if ($text.Length -gt 1600) { $text = $text.Substring(0,1600) }
            $result.ok = $true
            $result.preview = $text
        } elseif ($FileType -eq "docx") {
            Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue | Out-Null
            $tmp = Join-Path $env:TEMP ("via_docx_" + [Guid]::NewGuid().ToString("N"))
            [System.IO.Compression.ZipFile]::ExtractToDirectory($Path, $tmp)
            $docXml = Join-Path $tmp "word\document.xml"
            if (Test-Path -LiteralPath $docXml) {
                $xml = Get-Content -LiteralPath $docXml -Raw
                $plain = [regex]::Replace($xml, "<[^>]+>", " ")
                $plain = [System.Net.WebUtility]::HtmlDecode($plain)
                if ($plain.Length -gt 1600) { $plain = $plain.Substring(0,1600) }
                $result.ok = $true
                $result.preview = $plain
            }
            Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
        } else {
            $result.ok = $false
            $result.error = "preview_not_supported_for_type"
        }
    } catch {
        $result.error = $_.Exception.Message
    }
    return $result
}

function def_WriteHtmlReport {
    param([array]$Rows,[string]$OutPath)
    $htmlRows = foreach ($r in $Rows) {
        "<tr><td>$($r.record_id)</td><td>$($r.status)</td><td>$($r.domain)</td><td>$($r.file_type)</td><td>$([System.Web.HttpUtility]::HtmlEncode($r.name))</td><td>$($r.size_bytes)</td><td>$($r.sha256)</td><td>$([System.Web.HttpUtility]::HtmlEncode($r.path))</td></tr>"
    }
    $doc = @"
<!doctype html><html><head><meta charset="utf-8"><title>VIA Downloads Register All</title>
<style>body{font-family:Segoe UI,Microsoft JhengHei,sans-serif;background:#F9F9F6;color:#1F2933;font-size:11px}.wrap{max-width:1600px;margin:0 auto;padding:20px}table{width:100%;border-collapse:collapse;background:white}th,td{border:1px solid #DFECEA;padding:6px;vertical-align:top}th{background:#F3F6F4;color:#6B7C78}h1{font-size:20px}.pill{display:inline-block;border:1px solid #DFECEA;border-radius:999px;padding:3px 8px;margin:2px}</style></head>
<body><div class="wrap"><h1>VIA Downloads Register All + Cross Analysis All</h1>
<div><span class="pill">RunId: $def_RunId</span><span class="pill">Rows: $($Rows.Count)</span><span class="pill">Policy: read-only / no execute / no mutation</span></div>
<table><thead><tr><th>ID</th><th>Status</th><th>Domain</th><th>Type</th><th>Name</th><th>Bytes</th><th>SHA256</th><th>Path</th></tr></thead><tbody>
$($htmlRows -join "`n")
</tbody></table></div></body></html>
"@
    Set-Content -LiteralPath $OutPath -Value $doc -Encoding UTF8
}

try {
    def_EnsureDir $def_OutRoot
    $rows = New-Object System.Collections.Generic.List[object]
    $idx = 0

    foreach ($p in $def_Paths) {
        $idx++
        Write-Progress -Activity "VIA Register All + Cross Analysis" -Status $p -PercentComplete (($idx / [Math]::Max(1,$def_Paths.Count)) * 100)
        $class = def_ClassifyPath $p
        $exists = Test-Path -LiteralPath $p
        $item = $null
        $sha = ""
        $size = $null
        $status = if ($exists) { "FOUND" } else { "MISSING" }
        $previewOk = $false
        $preview = ""
        $previewErr = ""

        if ($exists) {
            try {
                $item = Get-Item -LiteralPath $p -Force
                if (-not $item.PSIsContainer) {
                    $size = $item.Length
                    $sha = (Get-FileHash -LiteralPath $p -Algorithm SHA256 -ErrorAction Stop).Hash
                    $pv = def_ReadPreview -Path $p -FileType $class.file_type
                    $previewOk = $pv.ok
                    $preview = $pv.preview
                    $previewErr = $pv.error
                } else {
                    $childCount = (Get-ChildItem -LiteralPath $p -Force -ErrorAction SilentlyContinue | Measure-Object).Count
                    $size = $childCount
                }
            } catch {
                $status = "FOUND_READ_WARN"
                $previewErr = $_.Exception.Message
            }
        }

        $rows.Add([pscustomobject]@{
            record_id = ("VIA-20260702-LOCAL-" + $idx.ToString("0000"))
            path = $p
            name = Split-Path -Leaf $p
            status = $status
            domain = $class.domain
            file_type = $class.file_type
            size_bytes = $size
            sha256 = $sha
            preview_ok = $previewOk
            preview_error = $previewErr
            preview_excerpt = $preview
            policy = "READ_ONLY_NO_EXECUTE_NO_MUTATION"
        }) | Out-Null
    }

    $jsonPath = Join-Path $def_OutRoot "VIA_Downloads_RegisterAll_CrossAnalysis.registry.json"
    $csvPath  = Join-Path $def_OutRoot "VIA_Downloads_RegisterAll_CrossAnalysis.registry.csv"
    $htmlPath = Join-Path $def_OutRoot "VIA_Downloads_RegisterAll_CrossAnalysis.report.html"

    $payload = [pscustomobject]@{
        run_id = $def_RunId
        generated_at = (Get-Date).ToString("s")
        policy = @("read-only","no execution","no source mutation","no delete","append-only output")
        rows = $rows
    }

    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
    $rows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8
    def_WriteHtmlReport -Rows $rows -OutPath $htmlPath

    Write-Progress -Activity "VIA Register All + Cross Analysis" -Completed
    Write-Host ""
    Write-Host "================================================================================"
    Write-Host "VIA REGISTER ALL + CROSS ANALYSIS COMPLETE" -ForegroundColor Green
    Write-Host "OutputRoot: $def_OutRoot"
    Write-Host "JSON      : $jsonPath"
    Write-Host "CSV       : $csvPath"
    Write-Host "HTML      : $htmlPath"
    Write-Host "Policy    : read-only / no execute / no mutation / append-only"
    Write-Host "================================================================================"
    Start-Process $htmlPath
} catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace
} finally {
    Write-Host ""
    Write-Host "PowerShell remains open. No destructive action was executed." -ForegroundColor Yellow
}

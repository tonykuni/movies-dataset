param(
    [string]$RootPath = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\VIA_Governance_Runtime\v0162B\runtime\run_20260802_100751\sandbox\round_1\functional modules\VAP',
    [string]$OutputDirectory = '',
    [int]$MaximumFileSizeMB = 30
)

$ErrorActionPreference = 'Stop'
$ScriptVersion = 'v015'
$AllowedExtensions = @('.html', '.htm', '.json', '.js', '.ps1', '.md', '.csv')
$ChartTermPattern = '(?i)(seaborn|plotly|sns\.color_palette|diverging_palette|VAP-CH-\d{2,3}|單軸|雙軸|secondary_y|yaxis2|twinx|candlestick|k[ -]?line|K線|volume|成交量|stack(?:ed)?|堆疊|histogram|box(?:plot)?|violin|KDE|ECDF|rug|regression|resid(?:ual)?|density|pair\s?grid|facet\s?grid|joint\s?grid|heatmap|scatter|bar|line|area|radar|event\s?matrix|rolling|sharpe|sortino|alpha|backtest|intraday|spot|futures|palette|colorway|colorscale|tick(?:s|vals|mode)?|interval|間隔|刻度|renderer|template)'
$ChartTypePattern = '(?i)\b(line|area|bar|hbar|scatter|sarea|sbar|sbar100|gbar|dline|dbarline|evtmx|corrheat|brush|map|roll|rollcorr|rollsharpe|sortino|radar|alpha|econcal|consensus|backtest|intraday|candle|spotfut|hist|box|violin|kde|reg|density|pairgrid|facet|ecdf|rug|resid|joint)\b'
$PropertyPattern = '(?i)["'']([^"'']*(?:chart|plot|axis|palette|color|renderer|template|tick|interval)[^"'']*)["'']\s*:'
$HexColorPattern = '(?i)#[0-9a-f]{6}\b'
$ChartCodePattern = '(?i)\bVAP-CH-\d{2,3}\b'
$StepPattern = '(?i)(?:tickMultiples|stepFamily|interval(?:Value|Step)?|間隔值)[^\r\n]{0,120}(?:2(?:\.0)?|2\.5|5|10)'

function def_Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function def_Get-RelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$FullPath
    )
    $base = $BasePath.TrimEnd('\') + '\'
    $baseUri = New-Object System.Uri($base)
    $fullUri = New-Object System.Uri($FullPath)
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($fullUri).ToString()).Replace('/', '\')
}

function def_Get-UniqueMatches {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Pattern,
        [int]$Group = 0
    )
    $values = foreach ($match in [regex]::Matches($Text, $Pattern)) {
        $match.Groups[$Group].Value.Trim()
    }
    return @($values | Where-Object { $_ } | Sort-Object -Unique)
}

function def-Get-RuleSnippets {
    param([Parameter(Mandatory = $true)][string]$Text)
    $snippets = foreach ($line in ($Text -split "`r?`n")) {
        $value = $line.Trim()
        if ($value.Length -gt 0 -and $value.Length -le 900 -and $value -match $ChartTermPattern) {
            $value
        }
    }
    return @($snippets | Select-Object -Unique -First 200)
}

function def-Inspect-File {
    param([Parameter(Mandatory = $true)][System.IO.FileInfo]$File)
    $relative = def_Get-RelativePath -BasePath $RootPath -FullPath $File.FullName
    $record = [ordered]@{
        relative_path = $relative
        extension = $File.Extension.ToLowerInvariant()
        bytes = $File.Length
        sha256 = def_Get-Sha256 -Path $File.FullName
        status = 'READ'
        chart_codes = @()
        chart_types = @()
        property_keys = @()
        colors = @()
        axis_step_evidence = @()
        rule_snippets = @()
        error = $null
    }
    if ($File.Length -gt ($MaximumFileSizeMB * 1MB)) {
        $record.status = 'SKIPPED_TOO_LARGE'
        return [pscustomobject]$record
    }
    try {
        $text = [System.IO.File]::ReadAllText($File.FullName)
        if ($text -notmatch $ChartTermPattern) {
            $record.status = 'READ_NO_CHART_SIGNAL'
            return [pscustomobject]$record
        }
        $record.status = 'CHART_SPEC_SIGNAL_FOUND'
        $record.chart_codes = @(def_Get-UniqueMatches -Text $text -Pattern $ChartCodePattern)
        $record.chart_types = @(def_Get-UniqueMatches -Text $text -Pattern $ChartTypePattern)
        $record.property_keys = @(def_Get-UniqueMatches -Text $text -Pattern $PropertyPattern -Group 1)
        $record.colors = @(def_Get-UniqueMatches -Text $text -Pattern $HexColorPattern)
        $record.axis_step_evidence = @(def_Get-UniqueMatches -Text $text -Pattern $StepPattern)
        $record.rule_snippets = @(def-Get-RuleSnippets -Text $text)
    }
    catch {
        $record.status = 'READ_ERROR'
        $record.error = $_.Exception.Message
    }
    return [pscustomobject]$record
}

function def-HtmlEncode {
    param([AllowNull()][object]$Value)
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def-Build-HtmlReport {
    param(
        [Parameter(Mandatory = $true)][object[]]$Records,
        [Parameter(Mandatory = $true)][hashtable]$Summary
    )
    $rows = foreach ($record in $Records) {
        $codes = def-HtmlEncode ($record.chart_codes -join ', ')
        $types = def-HtmlEncode ($record.chart_types -join ', ')
        $colors = def-HtmlEncode ($record.colors -join ', ')
        $steps = def-HtmlEncode ($record.axis_step_evidence -join ' | ')
        '<tr><td><b>' + (def-HtmlEncode $record.relative_path) + '</b><small>' + (def-HtmlEncode $record.sha256) + '</small></td><td>' + (def-HtmlEncode $record.status) + '</td><td>' + $codes + '</td><td>' + $types + '</td><td>' + $steps + '</td><td>' + $colors + '</td></tr>'
    }
    $generated = def-HtmlEncode $Summary.generated_at
    $root = def-HtmlEncode $Summary.root_path
    return @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VAP 本機圖表規格擷取 $ScriptVersion</title><style>
:root{--paper:#f5f4f0;--white:#fff;--ink:#1b1a17;--mut:#6b6860;--line:#dcdad3;--teal:#439a9a}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Microsoft JhengHei","Segoe UI",sans-serif}header{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);padding:16px 22px;z-index:2}h1{font-size:19px;margin:3px 0}.k{font:800 10px ui-monospace,monospace;color:var(--teal);letter-spacing:.12em}.sub{font-size:11px;color:var(--mut)}main{width:min(1500px,calc(100% - 28px));margin:16px auto}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}.cards b{background:#fff;border:1px solid var(--line);border-radius:8px;padding:11px;font:800 22px ui-monospace,monospace}.cards span,small{display:block;font-size:9px;color:var(--mut);overflow:hidden;text-overflow:ellipsis}.table{background:#fff;border:1px solid var(--line);border-radius:9px;overflow:auto}table{border-collapse:collapse;width:100%;font-size:10px}th,td{padding:8px;border-bottom:1px solid #ecebe6;vertical-align:top;text-align:left}th{position:sticky;top:0;background:#eeece6;font:800 9px ui-monospace,monospace}@media(max-width:800px){.cards{grid-template-columns:1fr 1fr}}</style></head><body><header><div class="k">VIA · READ-ONLY LOCAL EXTRACTION · $ScriptVersion</div><h1>VAP 本機圖表規格擷取報告</h1><div class="sub">$root · $generated · 不執行 HTML／JS／PowerShell</div></header><main><section class="cards"><b>$($Summary.files_scanned)<span>FILES SCANNED</span></b><b>$($Summary.chart_signal_files)<span>CHART SIGNALS</span></b><b>$($Summary.unique_chart_codes)<span>CHART CODES</span></b><b>$($Summary.read_errors)<span>READ ERRORS</span></b></section><section class="table"><table><thead><tr><th>FILE / SHA-256</th><th>STATUS</th><th>CHART CODES</th><th>CHART TYPES</th><th>AXIS STEP EVIDENCE</th><th>COLORS</th></tr></thead><tbody>$($rows -join "`n")</tbody></table></section></main></body></html>
"@
}

if (-not (Test-Path -LiteralPath $RootPath -PathType Container)) {
    throw "VAP root directory not found: $RootPath"
}
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $RootPath '_chart_spec_extract_v015'
}
if (-not (Test-Path -LiteralPath $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}

$files = @(Get-ChildItem -LiteralPath $RootPath -File -Recurse | Where-Object { $AllowedExtensions -contains $_.Extension.ToLowerInvariant() })
$records = @($files | ForEach-Object { def-Inspect-File -File $_ })
$signalRecords = @($records | Where-Object { $_.status -eq 'CHART_SPEC_SIGNAL_FOUND' })
$codes = @($signalRecords.chart_codes | Sort-Object -Unique)
$summary = @{
    schema = 'VIA-VAP-LOCAL-CHART-SPEC-EXTRACTION/1.0'
    version = $ScriptVersion
    generated_at = [DateTime]::UtcNow.ToString('o')
    root_path = $RootPath
    policy = 'READ_ONLY_SCAN_NO_EXECUTION'
    files_scanned = $records.Count
    chart_signal_files = $signalRecords.Count
    unique_chart_codes = $codes.Count
    chart_codes = $codes
    read_errors = @($records | Where-Object { $_.status -eq 'READ_ERROR' }).Count
    skipped_too_large = @($records | Where-Object { $_.status -eq 'SKIPPED_TOO_LARGE' }).Count
    axis_contract = @{
        interval_count = 4
        tick_count = 5
        dual_axis_equal_interval_counts = $true
        step_family = @(2, 2.5, 5, 10)
        decimal_precision = 'UNIFIED_LEFT_RIGHT'
    }
    seaborn_color_contract = @{
        version = '0.13.2'
        data_palette = 'sns.color_palette()'
        heatmap_palette = 'sns.diverging_palette(220, 20, as_cmap=True)'
        heatmap_zmid = 0
        heatmap_stops = 15
    }
}
$package = [ordered]@{
    summary = $summary
    records = $records
}

$jsonPath = Join-Path $OutputDirectory 'VIA_VAP_Local_Chart_Spec_Extraction_v015.json'
$csvPath = Join-Path $OutputDirectory 'VIA_VAP_Local_Chart_Spec_Extraction_v015.csv'
$htmlPath = Join-Path $OutputDirectory 'VIA_VAP_Local_Chart_Spec_Extraction_v015.html'
$package | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
$records | Select-Object relative_path, extension, bytes, sha256, status, @{n='chart_codes';e={$_.chart_codes -join '|'}}, @{n='chart_types';e={$_.chart_types -join '|'}}, @{n='axis_step_evidence';e={$_.axis_step_evidence -join '|'}}, @{n='colors';e={$_.colors -join '|'}}, error | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8
def-Build-HtmlReport -Records $records -Summary $summary | Set-Content -LiteralPath $htmlPath -Encoding UTF8

Write-Host "PASS · VAP chart specification extraction completed" -ForegroundColor Green
Write-Host "Files scanned: $($records.Count) · Chart signals: $($signalRecords.Count) · Codes: $($codes.Count) · Errors: $($summary.read_errors)"
Write-Host $jsonPath
Write-Host $csvPath
Write-Host $htmlPath

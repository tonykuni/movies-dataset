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
$ErrorActionPreference = 'Continue'

param(
    [switch]$OpenHtmlReport
)

$ExitCode = 0

try {
    $ProjectRoot = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'
    $ActiveRoot = Join-Path $ProjectRoot 'dict\VDF\_active'
    $FreezeRoot = Join-Path $ProjectRoot 'dict\VDF\_freeze'
    $ToolRoot = Join-Path $ProjectRoot 'tools\VIA_DualProjectDailyHealth'
    $DailyRoot = Join-Path $ToolRoot 'daily_runs'
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $RunRoot = Join-Path $DailyRoot ('RUN_' + $Stamp)
    $ReportDir = Join-Path $RunRoot 'report'
    $RuntimeDir = Join-Path $RunRoot 'runtime'

    foreach ($d in @($DailyRoot,$RunRoot,$ReportDir,$RuntimeDir)) {
        try { [System.IO.Directory]::CreateDirectory($d) | Out-Null } catch {}
    }

    function ReadJsonSafe {
        param([string]$Path)
        try {
            if (Test-Path -LiteralPath $Path) {
                return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
            }
        } catch {}
        return $null
    }

    function GetProp {
        param([AllowNull()][object]$Obj,[string]$Name,[AllowNull()][object]$Default='')
        if ($null -eq $Obj) { return $Default }
        try {
            $p = $Obj.PSObject.Properties[$Name]
            if ($null -ne $p -and $null -ne $p.Value) { return $p.Value }
        } catch {}
        return $Default
    }

    function FindLatest {
        param([string]$Filter)
        try {
            return Get-ChildItem -LiteralPath $ActiveRoot -Recurse -File -Filter $Filter -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
        } catch {
            return $null
        }
    }

    function E {
        param([AllowNull()][object]$Value)
        if ($null -eq $Value) { return '' }
        try { return [System.Net.WebUtility]::HtmlEncode([string]$Value) } catch { return '' }
    }

    function WriteText {
        param([string]$Path,[string]$Text)
        try { [System.IO.File]::WriteAllText($Path,$Text,[System.Text.UTF8Encoding]::new($false)) } catch {}
    }

    $Issues = [System.Collections.Generic.List[string]]::new()

    $ActivePointer = Join-Path $ActiveRoot 'VDF_ACTIVE_POINTER.json'
    $FrozenPointer = Join-Path $FreezeRoot 'VDF_FINAL_ACTIVATION_SEAL_POINTER_v02868.json'

    $Active = ReadJsonSafe $ActivePointer
    $Frozen = ReadJsonSafe $FrozenPointer

    $SmokeFile = FindLatest 'VIA_ReadOnlyLaneSmoke_Runtime_v02874.json'
    $ConsoleFile = FindLatest 'VIA_DualProjectUserTestConsoleHotfix_Runtime_v028731.json'

    $Smoke = if ($SmokeFile) { ReadJsonSafe $SmokeFile.FullName } else { $null }

    $ActiveStatus = [string](GetProp $Active 'status' '')
    $FrozenStatus = [string](GetProp $Frozen 'status' '')
    $SmokeStatus = [string](GetProp $Smoke 'status' '')
    $SmokeOk = [int](GetProp $Smoke 'smoke_ok' 0)
    $SmokeBlock = [int](GetProp $Smoke 'smoke_block' 0)

    if ($ActiveStatus -ne 'FINAL_PROMOTED_ACTIVE_POINTER_LOCKED') { $Issues.Add('Active pointer review: ' + $ActiveStatus) | Out-Null }
    if ($FrozenStatus -ne 'FINAL_PROMOTED_ACTIVE_POINTER_LOCKED') { $Issues.Add('Frozen pointer review: ' + $FrozenStatus) | Out-Null }
    if ($SmokeStatus -ne 'READONLY_LANE_SMOKE_READY') { $Issues.Add('Smoke review: ' + $SmokeStatus) | Out-Null }
    if ($SmokeOk -lt 6) { $Issues.Add('Smoke OK less than 6: ' + $SmokeOk) | Out-Null }
    if ($SmokeBlock -gt 0) { $Issues.Add('Smoke block greater than 0: ' + $SmokeBlock) | Out-Null }

    if ($Issues.Count -eq 0) {
        $Status = 'DAILY_HEALTH_READY'
        $Risk = 'LOW'
    }
    else {
        $Status = 'DAILY_HEALTH_REVIEW_REQUIRED'
        $Risk = 'MEDIUM'
    }

    $RuntimePath = Join-Path $RuntimeDir 'VIA_DualProjectDailyHealth_Runtime.json'
    $HtmlPath = Join-Path $ReportDir 'VIA_DualProjectDailyHealth_Report.html'

    $Runtime = [pscustomobject]@{
        generated_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fffK')
        status = $Status
        risk = $Risk
        active_status = $ActiveStatus
        frozen_status = $FrozenStatus
        smoke_status = $SmokeStatus
        smoke_ok = $SmokeOk
        smoke_block = $SmokeBlock
        latest_smoke_runtime = if ($SmokeFile) { $SmokeFile.FullName } else { '' }
        latest_console_runtime = if ($ConsoleFile) { $ConsoleFile.FullName } else { '' }
        issues = @($Issues)
        policy = [pscustomobject]@{
            db_write = $false
            source_repair = $false
            pointer_rewrite = $false
            destructive_delete = $false
            stop_process = $false
            vrn_extraction = $false
            vdf_db_write = $false
        }
    }

    try {
        $Runtime | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $RuntimePath -Encoding UTF8
    } catch {}

    if ($Issues.Count -eq 0) {
        $IssueRows = '<tr><td>OK</td><td>No current issue.</td></tr>'
    }
    else {
        $IssueRows = (@($Issues) | ForEach-Object {
            '<tr><td>REVIEW</td><td>' + (E $_) + '</td></tr>'
        }) -join ''
    }

    $Html = @()
    $Html += '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA Daily Health</title>'
    $Html += '<style>body{font-family:Microsoft JhengHei,Segoe UI,Arial,sans-serif;background:#f8fbfa;color:#1d3438;margin:0;font-size:12px}header{padding:16px 24px;background:white;border-bottom:1px solid rgba(38,70,75,.18)}h1{margin:0;text-align:center;font-size:18px}.wrap{padding:16px 24px}.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:14px}.card{background:white;border:1px solid rgba(38,70,75,.16);border-radius:10px;padding:10px}.k{font-size:10px;color:#657f82}.v{font-size:16px;font-weight:700}table{width:100%;border-collapse:collapse;background:white;border:1px solid rgba(38,70,75,.16)}th,td{border-bottom:1px solid rgba(38,70,75,.12);padding:7px;text-align:left;vertical-align:top}th{background:#edf8f6}code{font-family:Consolas,monospace;word-break:break-word}</style>'
    $Html += '</head><body><header><h1>def VIA Dual Project Daily Health</h1></header><div class="wrap">'
    $Html += '<div class="grid">'
    $Html += '<div class="card"><div class="k">Status</div><div class="v">' + (E $Status) + '</div></div>'
    $Html += '<div class="card"><div class="k">Risk</div><div class="v">' + (E $Risk) + '</div></div>'
    $Html += '<div class="card"><div class="k">Active</div><div class="v">' + (E $ActiveStatus) + '</div></div>'
    $Html += '<div class="card"><div class="k">Frozen</div><div class="v">' + (E $FrozenStatus) + '</div></div>'
    $Html += '<div class="card"><div class="k">Smoke</div><div class="v">' + (E $SmokeStatus) + '</div></div>'
    $Html += '<div class="card"><div class="k">Smoke OK</div><div class="v">' + [string]$SmokeOk + '</div></div>'
    $Html += '</div><h2>Issues</h2><table><thead><tr><th>Status</th><th>Message</th></tr></thead><tbody>' + $IssueRows + '</tbody></table>'
    $Html += '<h2>Paths</h2><table>'
    $Html += '<tr><th>Runtime</th><td><code>' + (E $RuntimePath) + '</code></td></tr>'
    $Html += '<tr><th>Latest Smoke</th><td><code>' + (E $Runtime.latest_smoke_runtime) + '</code></td></tr>'
    $Html += '<tr><th>Latest Console</th><td><code>' + (E $Runtime.latest_console_runtime) + '</code></td></tr>'
    $Html += '</table></div></body></html>'

    WriteText $HtmlPath ($Html -join '')

    Write-Host ''
    Write-Host '================================================================================' -ForegroundColor Cyan
    Write-Host 'VIA DUAL PROJECT DAILY HEALTH' -ForegroundColor Cyan
    Write-Host '================================================================================' -ForegroundColor Cyan
    Write-Host ('Status : ' + $Status)
    Write-Host ('Risk   : ' + $Risk)
    Write-Host ('HTML   : ' + $HtmlPath)
    Write-Host ('Runtime: ' + $RuntimePath)
    Write-Host 'Read-only daily health complete. No DB write. No Stop-Process.' -ForegroundColor Green

    if ($OpenHtmlReport -and (Test-Path -LiteralPath $HtmlPath)) {
        try { Start-Process $HtmlPath } catch {}
    }
}
catch {
    try {
        $FatalRoot = Join-Path 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics' 'tools\VIA_DualProjectDailyHealth\daily_runs'
        [System.IO.Directory]::CreateDirectory($FatalRoot) | Out-Null
        $FatalPath = Join-Path $FatalRoot ('DAILY_HEALTH_FATAL_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.txt')
        [System.IO.File]::WriteAllText($FatalPath, ($_.Exception.Message + "
" + $_.ScriptStackTrace), [System.Text.UTF8Encoding]::new($false))
        Write-Host ('Daily health fatal captured: ' + $FatalPath) -ForegroundColor Yellow
    } catch {}
}

exit $ExitCode

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

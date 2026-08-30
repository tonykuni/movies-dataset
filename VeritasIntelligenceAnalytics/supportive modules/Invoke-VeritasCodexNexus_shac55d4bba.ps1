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
<#
.SYNOPSIS
  Invoke-VeritasCodexNexus.ps1 - Veritas Codex Nexus 多語言引擎主指令(骨架)
.DESCRIPTION
  5 引擎 / 5 Registry / 1 主指令。-Mode 管範疇、-Task 管單功能。
  編排模式:寫狀態 -> ProcessStartInfo 跑 Python 工具 -> (可選)HttpListener -> 瀏覽器。
  Append-only(只增不減)。對齊 VHS_Launch.ps1 慣例。
.EXAMPLE
  pwsh ./Invoke-VeritasCodexNexus.ps1 -Mode All -Scan . -Serve
  pwsh ./Invoke-VeritasCodexNexus.ps1 -Mode Visual -Task ExtractChartSpec
  pwsh ./Invoke-VeritasCodexNexus.ps1 -Mode Spec -Scan ./templates -Out ./_out
#>
[CmdletBinding()]
param(
    [ValidateSet('All','Spec','Visual','Layout','Interaction','Governance')]
    [string]$Mode = 'All',
    [string]$Task = '',
    [string]$Scan = '.',
    [string]$Out  = './_codex_out',
    [string]$Registry = './VHS_LockRegistry.json',
    [switch]$Serve,
    [int]$Port = 8770,
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

function Write-Step {
    param([string]$Msg, [string]$Color = 'Gray')
    Write-Host ('  [{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $Msg) -ForegroundColor $Color
}
function Write-Head {
    param([string]$Msg)
    Write-Host ''
    Write-Host ('=== {0} ===' -f $Msg) -ForegroundColor Cyan
}

# ---- 引擎配置:Mode -> { Registry, Tools(任務->Python指令), Output } -------------
$Engines = [ordered]@{
    Spec = @{
        registry = 'UnifiedSpec.json'
        output   = 'UnifiedSpec.json'
        tasks    = [ordered]@{
            ExtractAll      = @{ tool='VHS_Reader.py';          args={ param($s,$o) @('--scan',$s,'--out',(Join-Path $o 'vhs_specs.json'),'--registry',$Registry) } }
            ThreeBucket     = @{ tool='VAP_TemplateIngestor.py'; args={ param($s,$o) @('--scan',$s,'--out',(Join-Path $o 'VAP_template_index.json')) } }
        }
    }
    Visual = @{
        registry = 'VisualRegistry.json'
        output   = 'VisualRegistry.json'
        tasks    = [ordered]@{
            ExtractChartSpec = @{ tool='VVX_Extractor.py';       args={ param($s,$o) @('--scan',$s,'--out',$o,'--recurse') } }
        }
    }
    Layout = @{
        registry = 'LayoutRegistry.json'
        output   = 'LayoutRegistry.json'
        tasks    = [ordered]@{
            ExtractLayout = @{ tool='VHS_Reader.py'; args={ param($s,$o) @('--scan',$s,'--out',(Join-Path $o 'layout_specs.json'),'--registry',$Registry) } }
        }
    }
    Interaction = @{
        registry = 'InteractionRegistry.json'
        output   = 'InteractionRegistry.json'
        tasks    = [ordered]@{
            ExtractInteraction = @{ tool='VAP_TemplateIngestor.py'; args={ param($s,$o) @('--scan',$s,'--out',(Join-Path $o 'interaction_index.json')) } }
        }
    }
    Governance = @{
        registry = 'GovernanceRegistry.json'
        output   = 'GovernanceRegistry.json'
        tasks    = [ordered]@{
            BuildReport = @{ tool=''; args={ param($s,$o) @() } }   # 收尾:彙總 + (可選)報告/freeze
        }
    }
}

# ---- 執行單一 Python 工具(ProcessStartInfo,擷取輸出/退出碼)------------------
function Invoke-PyTool {
    param([string]$Tool, [string[]]$Arguments)
    $toolPath = Join-Path $Root $Tool
    if (-not (Test-Path $toolPath)) {
        Write-Step ("工具不存在,略過:{0}" -f $Tool) 'DarkYellow'
        return @{ ok=$false; code=-1; note='tool-missing' }
    }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Python
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute = $false
    $psi.WorkingDirectory = $Root
    $null = $psi.ArgumentList.Add($toolPath)
    foreach ($a in $Arguments) { $null = $psi.ArgumentList.Add([string]$a) }
    $p = [System.Diagnostics.Process]::Start($psi)
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    if ($stdout) { $stdout.TrimEnd().Split("`n") | ForEach-Object { Write-Step ("  {0}" -f $_) 'DarkGray' } }
    if ($p.ExitCode -ne 0 -and $stderr) { Write-Step ("  ERR {0}" -f $stderr.Trim()) 'Red' }
    return @{ ok=($p.ExitCode -eq 0); code=$p.ExitCode; note=$stderr.Trim() }
}

# ---- 執行單一引擎(可指定 Task)----------------------------------------------
function Invoke-Engine {
    param([string]$Name, [string]$OnlyTask)
    $eng = $Engines[$Name]
    Write-Head ("ENGINE {0}  (-Mode {0})  Registry={1}" -f $Name, $eng.registry)
    $regPath = Join-Path $Root $eng.registry
    if (Test-Path $regPath) { Write-Step ("讀取 Registry:{0}" -f $eng.registry) 'Green' }
    else { Write-Step ("Registry 缺(將以工具輸出補):{0}" -f $eng.registry) 'DarkYellow' }

    $results = @()
    foreach ($tk in $eng.tasks.Keys) {
        if ($OnlyTask -and $OnlyTask -ne $tk) { continue }
        $t = $eng.tasks[$tk]
        if (-not $t.tool) { Write-Step ("Task {0}:收尾/彙總(無外部工具)" -f $tk) 'Gray'; $results += @{ task=$tk; ok=$true; note='consolidate' }; continue }
        Write-Step ("Task {0} -> {1}" -f $tk, $t.tool) 'White'
        $argv = & $t.args $Scan $Out
        $r = Invoke-PyTool -Tool $t.tool -Arguments $argv
        $results += @{ task=$tk; ok=$r.ok; code=$r.code; note=$r.note }
    }
    return @{ engine=$Name; tasks=$results }
}

# ---- HttpListener 服務(對齊 VHS_Launch.ps1)----------------------------------
function Start-CodexServer {
    param([string]$ServeDir, [int]$P)
    Add-Type -AssemblyName System.Net.HttpListener -ErrorAction SilentlyContinue
    $listener = New-Object System.Net.HttpListener
    $prefix = ('http://localhost:{0}/' -f $P)
    $listener.Prefixes.Add($prefix)
    $listener.Start()
    Write-Step ("HttpListener 啟動:{0}" -f $prefix) 'Green'
    Start-Process $prefix
    Write-Step '按 Ctrl+C 結束服務' 'DarkGray'
    while ($listener.IsListening) {
        $ctx = $listener.GetContext()
        $rel = $ctx.Request.Url.AbsolutePath.TrimStart('/')
        if ([string]::IsNullOrWhiteSpace($rel)) { $rel = 'VeritasCodexNexus_EngineMatrix.html' }
        $file = Join-Path $ServeDir $rel
        if (-not (Test-Path $file)) { $file = Join-Path $Root $rel }
        if (Test-Path $file) {
            $bytes = [System.IO.File]::ReadAllBytes($file)
            $ext = [System.IO.Path]::GetExtension($file).ToLower()
            $ctx.Response.ContentType = switch ($ext) {
                '.html' { 'text/html; charset=utf-8' }
                '.json' { 'application/json; charset=utf-8' }
                '.js'   { 'application/javascript; charset=utf-8' }
                '.png'  { 'image/png' }
                default { 'application/octet-stream' }
            }
            $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
            $ctx.Response.StatusCode = 404
        }
        $ctx.Response.Close()
    }
}

# ============================ MAIN =========================================
Write-Host ''
Write-Host 'Veritas Codex Nexus' -ForegroundColor Cyan -NoNewline
Write-Host ('  -  {0}  ({1})' -f $Stamp, $PSVersionTable.PSVersion) -ForegroundColor DarkGray
if (-not (Test-Path $Out)) { New-Item -ItemType Directory -Path $Out -Force | Out-Null }

$modesToRun = if ($Mode -eq 'All') { @($Engines.Keys) } else { @($Mode) }
$summary = @()

# 治理:順序執行(可平行的引擎彼此獨立;此骨架以順序+每步重測收尾,九頭龍安全)
foreach ($m in $modesToRun) {
    $res = Invoke-Engine -Name $m -OnlyTask $Task
    $summary += $res
}

# 收尾彙總 -> GovernanceRegistry 執行紀錄(append-only)
$runlog = [ordered]@{
    schema    = 'VIA.CodexNexus.RunLog'
    generated = $Stamp
    mode      = $Mode
    task      = $Task
    scan      = (Resolve-Path $Scan -ErrorAction SilentlyContinue).Path
    out       = (Resolve-Path $Out  -ErrorAction SilentlyContinue).Path
    results   = $summary
}
$runlogPath = Join-Path $Out ('CodexRunLog_{0}.json' -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
$runlog | ConvertTo-Json -Depth 8 | Out-File -FilePath $runlogPath -Encoding utf8
Write-Head 'SUMMARY'
foreach ($r in $summary) {
    $okN = (@($r.tasks | Where-Object { $_.ok }).Count)
    $tot = (@($r.tasks).Count)
    $col = if ($okN -eq $tot) { 'Green' } else { 'Yellow' }
    Write-Step ('{0,-12} {1}/{2} tasks OK' -f $r.engine, $okN, $tot) $col
}
Write-Step ('RunLog -> {0}' -f $runlogPath) 'DarkGray'

if ($Serve) { Start-CodexServer -ServeDir $Out -P $Port }

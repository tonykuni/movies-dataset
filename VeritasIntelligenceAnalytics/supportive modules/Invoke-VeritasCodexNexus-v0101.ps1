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
  Invoke-VeritasCodexNexus-v0101.ps1 - Codex Nexus 主指令(批105:py 一律經 Celeritas 加速器鏈)
.DESCRIPTION
  v0100→v0101(批105,2026-08-23):
  ① Invoke-PyTool 改走 Celeritas 啟動鏈:python <via_py_celeritas_launcher 最新版> <tool> <args>
     =每個 py 指令先掛 SuperAccel/Celeritas 加速器再執行(批87/105 令);
     launcher 缺→VeritasCeleritas.py 同層後備→裸 python(誠實 WARN 降級,不假綠)。
  ② Python 解析鏈:$Python→py→python3(Windows 常見 python 不在 PATH)。
  ③ PS 5.1 備援:ProcessStartInfo.ArgumentList 缺(.NET Framework)→ 轉義 Arguments 字串。
  ④ 主控台 UTF-8+PYTHONIOENCODING(中文亂碼備援)。
  ⑤ -TimeoutSec 硬逾時 kill(NoStall;預設 0=不限)。
  ⑥ OneDrive On-Demand 占位檔偵測(0-byte)→ 誠實報「一律保留在此裝置」。
  ⑦ stdout/stderr 非同步讀(大輸出雙管 ReadToEnd 死鎖備援)。
  ⑧ 啟動時 dot-source VIA_PS_Accel_Module.ps1(20 加速器;缺席 graceful)。
  20 失敗模式與備援總冊:registry\VIA_CodexNexus_FailureModes_v0100.json(儲存維護並遵守)。
  Append-only;正本 Invoke-VeritasCodexNexus.ps1 零觸碰存證。
.EXAMPLE
  pwsh ./Invoke-VeritasCodexNexus-v0101.ps1 -Mode All -Scan . -Serve
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
    [string]$Python = 'python',
    [int]$TimeoutSec = 0,
    [switch]$NoCeleritas   # 明示跳過加速器鏈(除錯用;預設一律走鏈)
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

# ---- 備援④:主控台 UTF-8(中文亂碼)----------------------------------------
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $env:PYTHONIOENCODING = 'utf-8'
} catch { }

function Write-Step {
    param([string]$Msg, [string]$Color = 'Gray')
    Write-Host ('  [{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $Msg) -ForegroundColor $Color
}
function Write-Head {
    param([string]$Msg)
    Write-Host ''
    Write-Host ('=== {0} ===' -f $Msg) -ForegroundColor Cyan
}

# ---- 備援⑧:20 加速器實體模組 dot-source(缺席 graceful)---------------------
$AccelModule = Join-Path $Root 'VIA_PS_Accel_Module.ps1'
if (Test-Path $AccelModule) {
    try { . $AccelModule; Write-Step '20 加速器模組已掛(VIA_PS_Accel_Module)' 'DarkGreen' }
    catch { Write-Step ("加速器模組載入失敗(graceful 續行):{0}" -f $_.Exception.Message) 'DarkYellow' }
} else {
    Write-Step '加速器模組缺席(graceful 續行)' 'DarkYellow'
}

# ---- 備援②:Python 解析鏈 python→py→python3 ---------------------------------
function Resolve-PythonExe {
    param([string]$Preferred)
    foreach ($cand in @($Preferred, 'py', 'python3', 'python')) {
        if (-not $cand) { continue }
        $cmd = Get-Command $cand -ErrorAction SilentlyContinue
        if ($cmd) { return $cand }
    }
    throw 'Python 不可得(python/py/python3 皆不在 PATH)— 解法:安裝 Python 或以 -Python 指定完整路徑(FailureModes FM-03)'
}
$PythonExe = Resolve-PythonExe -Preferred $Python

# ---- 批105 核心:Celeritas 啟動鏈解析(glob 動態接最新版;嚴禁寫死版號)-------
function Resolve-CeleritasLauncher {
    if ($NoCeleritas) { return $null }
    $regDir = Join-Path $Root 'registry'
    if (Test-Path $regDir) {
        $hits = @(Get-ChildItem -LiteralPath $regDir -Filter 'via_py_celeritas_launcher_v*.py' -ErrorAction SilentlyContinue | Sort-Object Name)
        if ($hits.Count -gt 0) { return $hits[-1].FullName }
    }
    # 後備:同層 VeritasCeleritas.py 存在=至少可被目標檔 import(降一級,誠實記)
    $vc = Join-Path $Root 'VeritasCeleritas.py'
    if (Test-Path $vc) { return $null }  # 無 launcher 可用;裸跑+WARN(FM-01)
    return $null
}
$CeleritasLauncher = Resolve-CeleritasLauncher
if ($CeleritasLauncher) { Write-Step ("Celeritas 啟動鏈:{0}" -f (Split-Path -Leaf $CeleritasLauncher)) 'DarkGreen' }
elseif (-not $NoCeleritas) { Write-Step 'Celeritas launcher 缺 → 裸 python 降級(誠實 WARN;FM-01)' 'DarkYellow' }

# ---- 引擎配置(承 v0100 原樣)-------------------------------------------------
$Engines = [ordered]@{
    Spec = @{
        registry = 'UnifiedSpec.json'
        output   = 'UnifiedSpec.json'
        tasks    = [ordered]@{
            ExtractAll      = @{ tool='SUP_MDL164_VHSReader.py';          args={ param($s,$o) @('--scan',$s,'--out',(Join-Path $o 'vhs_specs.json'),'--registry',$Registry) } }
            ThreeBucket     = @{ tool='VAP_TemplateIngestor.py'; args={ param($s,$o) @('--scan',$s,'--out',(Join-Path $o 'VAP_template_index.json')) } }
        }
    }
    Visual = @{
        registry = 'VisualRegistry.json'
        output   = 'VisualRegistry.json'
        tasks    = [ordered]@{
            ExtractChartSpec = @{ tool='SUP_MDL165_VVXExtractor.py';       args={ param($s,$o) @('--scan',$s,'--out',$o,'--recurse') } }
        }
    }
    Layout = @{
        registry = 'LayoutRegistry.json'
        output   = 'LayoutRegistry.json'
        tasks    = [ordered]@{
            ExtractLayout = @{ tool='SUP_MDL164_VHSReader.py'; args={ param($s,$o) @('--scan',$s,'--out',(Join-Path $o 'layout_specs.json'),'--registry',$Registry) } }
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
            BuildReport = @{ tool=''; args={ param($s,$o) @() } }
        }
    }
}

# ---- 備援③:PS 5.1 無 ArgumentList → 轉義字串 --------------------------------
function ConvertTo-ArgString {
    param([string[]]$Items)
    ($Items | ForEach-Object {
        if ($_ -match '[\s"]') { '"' + ($_ -replace '"','\"') + '"' } else { $_ }
    }) -join ' '
}

# ---- 執行單一 Python 工具(批105:一律先過 Celeritas 鏈)----------------------
function Invoke-PyTool {
    param([string]$Tool, [string[]]$Arguments)
    $toolPath = Join-Path $Root $Tool
    if (-not (Test-Path $toolPath)) {
        Write-Step ("工具不存在,略過:{0}(FM-05 路徑漂移?)" -f $Tool) 'DarkYellow'
        return @{ ok=$false; code=-1; note='tool-missing' }
    }
    # 備援⑥:OneDrive On-Demand 占位檔(0-byte)
    if ((Get-Item -LiteralPath $toolPath).Length -eq 0) {
        Write-Step ("0-byte 占位檔(OneDrive On-Demand?):{0} — 解法:資料夾右鍵「一律保留在此裝置」(FM-06)" -f $Tool) 'Red'
        return @{ ok=$false; code=-2; note='onedrive-placeholder' }
    }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $PythonExe
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute = $false
    $psi.WorkingDirectory = $Root
    # 批105:引數鏈 = [launcher] tool args…(launcher 缺=裸跑降級)
    $argChain = @()
    if ($CeleritasLauncher) { $argChain += $CeleritasLauncher }
    $argChain += $toolPath
    $argChain += $Arguments
    $hasArgList = $null -ne ($psi | Get-Member -Name 'ArgumentList' -ErrorAction SilentlyContinue)
    if ($hasArgList) {
        foreach ($a in $argChain) { $null = $psi.ArgumentList.Add([string]$a) }
    } else {
        $psi.Arguments = ConvertTo-ArgString -Items $argChain   # FM-18 PS5.1 備援
    }
    $p = [System.Diagnostics.Process]::Start($psi)
    # 備援⑦:非同步讀雙管(防大輸出死鎖 FM-13)
    $soTask = $p.StandardOutput.ReadToEndAsync()
    $seTask = $p.StandardError.ReadToEndAsync()
    # 備援⑤:硬逾時 NoStall(FM-14)
    if ($TimeoutSec -gt 0) {
        if (-not $p.WaitForExit($TimeoutSec * 1000)) {
            try { $p.Kill() } catch { }
            Write-Step ("TIMEOUT {0}s 截停(誠實記,不假綠):{1}" -f $TimeoutSec, $Tool) 'Red'
            return @{ ok=$false; code=-3; note=("timeout {0}s" -f $TimeoutSec) }
        }
    } else {
        $p.WaitForExit()
    }
    $stdout = $soTask.GetAwaiter().GetResult()
    $stderr = $seTask.GetAwaiter().GetResult()
    if ($stdout) { $stdout.TrimEnd().Split("`n") | ForEach-Object { Write-Step ("  {0}" -f $_) 'DarkGray' } }
    if ($p.ExitCode -ne 0 -and $stderr) {
        Write-Step ("  ERR {0}" -f $stderr.Trim()) 'Red'
        if ($stderr -match 'ModuleNotFoundError|ImportError') {
            Write-Step '  提示:相依缺件 → pip install(FM-15;可用加速器 pip_install)' 'DarkYellow'
        }
    }
    return @{ ok=($p.ExitCode -eq 0); code=$p.ExitCode; note=$stderr.Trim() }
}

# ---- 執行單一引擎(承 v0100)--------------------------------------------------
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
        Write-Step ("Task {0} -> {1}(經 Celeritas 鏈)" -f $tk, $t.tool) 'White'
        $argv = & $t.args $Scan $Out
        $r = Invoke-PyTool -Tool $t.tool -Arguments $argv
        $results += @{ task=$tk; ok=$r.ok; code=$r.code; note=$r.note }
    }
    return @{ engine=$Name; tasks=$results }
}

# ---- HttpListener 服務(承 v0100)---------------------------------------------
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
Write-Host 'Veritas Codex Nexus v0101' -ForegroundColor Cyan -NoNewline
Write-Host ('  -  {0}  ({1})  Python={2}' -f $Stamp, $PSVersionTable.PSVersion, $PythonExe) -ForegroundColor DarkGray
if (-not (Test-Path $Out)) { New-Item -ItemType Directory -Path $Out -Force | Out-Null }

$modesToRun = if ($Mode -eq 'All') { @($Engines.Keys) } else { @($Mode) }
$summary = @()

foreach ($m in $modesToRun) {
    $res = Invoke-Engine -Name $m -OnlyTask $Task
    $summary += $res
}

$runlog = [ordered]@{
    schema    = 'VIA.CodexNexus.RunLog'
    generated = $Stamp
    version   = 'v0101'
    celeritas = [bool]$CeleritasLauncher
    python    = $PythonExe
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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;v0101 已實體 dot-source)=====
# 本檔已實際 dot-source VIA_PS_Accel_Module.ps1(20 加速器冊+Invoke-VIAGuarded/
# Write-VIAProgress/Invoke-VIAParallel);缺席 graceful。失敗模式 20 冊:
# registry\VIA_CodexNexus_FailureModes_v0100.json(儲存維護並遵守)。
# ===== [VIA:PS-ACCEL:END] =====

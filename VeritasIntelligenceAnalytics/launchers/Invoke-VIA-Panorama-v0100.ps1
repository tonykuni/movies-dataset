#Requires -Version 7.0
# ===== Parameters / environment entry =====
param(
    [string]$ViaRoot = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
    [ValidateRange(1,24)][int]$Months = 2,
    [ValidateRange(1,86400)][int]$StationTimeout = 600,
    [ValidateRange(1,86400)][int]$FetchTimeout = 7200,
    [ValidateRange(1,100)][int]$BatchSize = 20,
    [string]$InputDir = '',
    [string]$PriceDatabase = '',
    [string]$EtfDatabase = '',
    [switch]$Fetch,
    [switch]$ReadOnly
)
Set-Location -LiteralPath $ViaRoot
$ErrorActionPreference = 'Stop'
$Register = Get-ChildItem -LiteralPath $ViaRoot -Filter 'Register-VIA-Commands-v*.ps1' -File | Sort-Object Name | Select-Object -Last 1
if (-not $Register) { throw '找不到中央 VIA 指令冊' }
. $Register.FullName
Set-Location -LiteralPath $ViaRoot
$Python = Get-VIAEnvPython 'vrn'
$EnvRoot = Split-Path $Python -Parent
if ((Split-Path $EnvRoot -Leaf) -in @('Scripts','bin')) { $EnvRoot = Split-Path $EnvRoot -Parent }
if (-not (Test-Path -LiteralPath $Python -PathType Leaf) -or (Split-Path $EnvRoot -Leaf) -notlike 'via_*') {
    throw "中央 VRN 家族境未就緒：$Python"
}
. (Join-Path $ViaRoot 'supportive modules\VIA_PS_Accel_Module.ps1')
$Roster = Get-VIAAccelRoster
if ($Roster.Count -ne 20) { throw "PS 加速器冊應為20項，實際 $($Roster.Count)" }
$Roster.GetEnumerator() | Format-Table Key,Value -AutoSize | Out-Host
if (-not $InputDir) { $InputDir = Join-Path $ViaRoot 'functional modules\VRN\input\incoming' }
$RunDir = Join-Path $ViaRoot ('VIA_Reports\panorama\' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
$Target = Get-ChildItem -LiteralPath (Join-Path $ViaRoot 'supportive modules\registry') -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' -File | Sort-Object Name | Select-Object -Last 1
if (-not $Target) { throw '中央治理主程式缺席' }
$Bootstrap = Join-Path $RunDir 'accelerated_panorama_child.py'
@'
import importlib.util, json, pathlib, runpy, sys
root, target, *arguments = sys.argv[1:]
root = pathlib.Path(root)
paths = sorted((root / 'supportive modules').glob('SUP_MDL737_SuperAccelModule_v*.py'))
if not paths:
    raise RuntimeError('中央 SuperAccel 模組缺席')
spec = importlib.util.spec_from_file_location('panorama_accel', paths[-1])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
print('ACCEL_ACTIVATION', json.dumps(module.activate(), default=str), flush=True)
sys.path.insert(0, str(pathlib.Path(target).parent))
sys.argv = [target, *arguments]
runpy.run_path(target, run_name='__main__')
'@ | Set-Content -LiteralPath $Bootstrap -Encoding utf8

# ===== Single central process / buffered logs / dynamic progress =====
function def_RunPanorama {
    $Info = [Diagnostics.ProcessStartInfo]::new()
    $Info.FileName = $Python
    $Info.WorkingDirectory = $ViaRoot
    $Info.UseShellExecute = $false
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    $Info.Environment['PYTHONUTF8'] = '1'
    $Info.Environment['PYTHONUNBUFFERED'] = '1'
    $Info.Environment['VIA_ROOT'] = $ViaRoot
    $Info.Environment['VIA_FAMILY'] = 'vrn'
    $Info.Environment['VIRTUAL_ENV'] = $EnvRoot
    $Info.Environment['PATH'] = (Join-Path $EnvRoot 'Scripts') + ';' + $EnvRoot + ';' + $env:PATH
    $BootDir = Join-Path $ViaRoot 'supportive modules\bootstrap'
    $Info.Environment['PYTHONPATH'] = $BootDir + [IO.Path]::PathSeparator + $env:PYTHONPATH
    if ($PriceDatabase) { $Info.Environment['VIA_DB_VDF_TW_MARKET'] = (Resolve-Path -LiteralPath $PriceDatabase).Path }
    if ($EtfDatabase) { $Info.Environment['VIA_DB_ACTIVETWETF'] = (Resolve-Path -LiteralPath $EtfDatabase).Path }
    # The user explicitly authorized fetching; grant only to this child process.
    if ($Fetch -and -not $ReadOnly) {
        $Info.Environment['VIA_NET_CONSENT'] = 'YES'
        $Info.Environment['VIA_SCRAPE_CONSENT'] = 'YES'
    }
    $ArgList = @('-u',$Bootstrap,$ViaRoot,$Target.FullName,'panorama','--months',"$Months",'--timeout',"$StationTimeout",'--fetch-timeout',"$FetchTimeout",'--batch-size',"$BatchSize",'--input-dir',$InputDir,'--out',$RunDir)
    if (-not $ReadOnly) { $ArgList += '--apply' }
    if ($Fetch -and -not $ReadOnly) { $ArgList += '--fetch' }
    foreach ($Argument in $ArgList) { $Info.ArgumentList.Add([string]$Argument) }
    $Process = [Diagnostics.Process]::new()
    $Process.StartInfo = $Info
    $Writer = [IO.StreamWriter]::new((Join-Path $RunDir 'panorama_run.log'),$false,[Text.UTF8Encoding]::new($false))
    $Writer.AutoFlush = $true
    $Timer = [Diagnostics.Stopwatch]::StartNew()
    $PageOpened = $false
    $ReportPath = Join-Path $RunDir 'PANORAMA.html'
    try {
        if (-not $Process.Start()) { throw '中央全景程序無法啟動' }
        $Streams = @($Process.StandardOutput,$Process.StandardError)
        $Tasks = @($Streams[0].ReadLineAsync(),$Streams[1].ReadLineAsync())
        while (-not $Process.HasExited -or $null -ne $Tasks[0] -or $null -ne $Tasks[1]) {
            for ($i=0; $i -lt 2; $i++) {
                $Drained = 0
                while ($null -ne $Tasks[$i] -and $Tasks[$i].IsCompleted -and $Drained -lt 200) {
                    $Line = $Tasks[$i].GetAwaiter().GetResult()
                    if ($null -eq $Line) { $Tasks[$i] = $null }
                    else {
                        $Writer.WriteLine($Line)
                        Write-Host $Line
                        $Tasks[$i] = $Streams[$i].ReadLineAsync()
                    }
                    $Drained++
                }
            }
            if (-not $PageOpened -and (Test-Path -LiteralPath $ReportPath)) {
                try { Start-Process -FilePath $ReportPath; $PageOpened = $true } catch { Write-Host "報告可手動開啟：$ReportPath"; $PageOpened = $true }
            }
            Write-Progress -Activity 'VCGC · VRN / VDF / VETF 全景實測' -Status ("已執行 {0:N0} 秒；詳情由矩陣持續更新" -f $Timer.Elapsed.TotalSeconds)
            Start-Sleep -Milliseconds 40
        }
        $Process.WaitForExit()
        return $Process.ExitCode
    }
    finally {
        $Writer.Dispose()
        $Process.Dispose()
        Write-Progress -Activity 'VCGC · VRN / VDF / VETF 全景實測' -Completed
    }
}

# ===== Evidence package / visible final report =====
$ResultCode = $null
try { $ResultCode = def_RunPanorama }
catch { $_.Exception.ToString() | Set-Content (Join-Path $RunDir 'launcher_error.txt') -Encoding utf8; Write-Host $_.Exception.Message -ForegroundColor Red }
finally {
    # Include all station logs referenced by this run; no original broker files or credentials.
    $MatrixPath = Join-Path $RunDir 'PANORAMA.json'
    if (Test-Path -LiteralPath $MatrixPath) {
        $Matrix = Get-Content -LiteralPath $MatrixPath -Raw | ConvertFrom-Json
        $LogsDir = Join-Path $RunDir 'station_logs'
        New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
        $BusLogRoot = [IO.Path]::GetFullPath((Join-Path $ViaRoot 'VIA_Reports\engine_bus\station_logs')) + [IO.Path]::DirectorySeparatorChar
        foreach ($Row in $Matrix.results) {
            if ($Row.stdout_log -and (Test-Path -LiteralPath $Row.stdout_log -PathType Leaf)) {
                $LogFull = [IO.Path]::GetFullPath([string]$Row.stdout_log)
                if ($LogFull.StartsWith($BusLogRoot,[StringComparison]::OrdinalIgnoreCase)) { Copy-Item -LiteralPath $LogFull -Destination $LogsDir }
            }
        }
        $Matrix.results | Select-Object id,family,phase,state,seconds | Format-Table -AutoSize | Out-Host
    }
    $Bundle = $RunDir + '_evidence.zip'
    try { Compress-Archive -Path (Join-Path $RunDir '*') -DestinationPath $Bundle -Force; Write-Host "後續修復紀錄包：$Bundle" -ForegroundColor Cyan }
    catch { Write-Host "紀錄仍在 $RunDir；壓縮失敗：$($_.Exception.Message)" -ForegroundColor Yellow }
    Write-Host "全景報告：$(Join-Path $RunDir 'PANORAMA.html')"
    Write-Host "返回碼：$ResultCode；存在待修項目時不核可安裝。"
}

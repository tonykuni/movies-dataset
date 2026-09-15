#Requires -Version 7.0
param(
    [string]$ViaRoot = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
    [string]$InputDir = '',
    [ValidateRange(1,86400)][int]$StationTimeout = 600
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-Location -LiteralPath $ViaRoot
$Register = Get-ChildItem -LiteralPath $ViaRoot -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1
if (-not $Register) { throw '缺少 VIA 指令註冊冊' }
. $Register.FullName
Set-Location -LiteralPath $ViaRoot
$VdfPython = Get-VIAEnvPython 'vdf'
$VrnPython = Get-VIAEnvPython 'vrn'
# 直接使用家族解譯器；同時把子程序 PATH 對準家族環境。
foreach ($Python in @($VdfPython, $VrnPython)) {
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "環境不存在：$Python" }
    $EnvName = Split-Path (Split-Path (Split-Path $Python -Parent) -Parent) -Leaf
    if ($EnvName -notlike 'via_*') { throw "拒絕 base 退路：$Python；請先以中央環境管理修復家族環境" }
}
. (Join-Path $ViaRoot 'supportive modules\VIA_PS_Accel_Module.ps1')
$Roster = Get-VIAAccelRoster
if ($Roster.Count -ne 20) { throw "PS 加速器冊不是20項：$($Roster.Count)" }
$Roster.GetEnumerator() | Format-Table Key,Value -AutoSize | Out-Host
if (-not $InputDir) { $InputDir = Join-Path $ViaRoot 'functional modules\VRN\input\incoming' }
if (-not (Test-Path -LiteralPath $InputDir -PathType Container)) { throw "輸入資料夾不存在：$InputDir" }
$RunDir = Join-Path $ViaRoot ('VIA_Reports\accelerated_test\' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
$Rows = [System.Collections.Generic.List[object]]::new()
$Failure = $null
$Bootstrap = Join-Path $RunDir 'accelerated_child.py'
@'
import importlib.util, pathlib, runpy, sys, json
root, family, target, *arguments = sys.argv[1:]
root = pathlib.Path(root)
def load(pattern, folder, name):
    paths = sorted((root / folder).glob(pattern))
    if not paths: raise RuntimeError('Missing: ' + pattern)
    spec = importlib.util.spec_from_file_location(name, paths[-1])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
accel = load('SUP_MDL737_SuperAccelModule_v*.py', 'supportive modules', 'via_test_accel')
print('ACCEL_ACTIVATION', json.dumps(accel.activate(), default=str), flush=True)
if family == 'vdf':
    net = load('SUP_MDL740_NetUnified_v*.py', 'supportive modules/network', 'VIA_NET_UNIFIED')
    print('VDF_NETWORK_TOOL', net.__file__, flush=True)
sys.argv = [target, *arguments]
sys.path.insert(0, str(pathlib.Path(target).parent))
runpy.run_path(target, run_name='__main__')
'@ | Set-Content -LiteralPath $Bootstrap -Encoding utf8

function def_Newest([string]$Folder, [string]$Pattern) {
    $File = Get-ChildItem -LiteralPath (Join-Path $ViaRoot $Folder) -Filter $Pattern -File | Sort-Object Name | Select-Object -Last 1
    if (-not $File) { throw "缺少 $Pattern" }
    return $File.FullName
}

function def_Step([string]$Name, [string]$Family, [string]$Target, [string[]]$Arguments) {
    $Python = if ($Family -eq 'vdf') { $VdfPython } else { $VrnPython }
    $Info = [System.Diagnostics.ProcessStartInfo]::new()
    $Info.FileName = $Python
    $Info.WorkingDirectory = $ViaRoot
    $Info.UseShellExecute = $false
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    $Info.Environment['PYTHONUTF8'] = '1'
    $Info.Environment['PYTHONUNBUFFERED'] = '1'
    $Info.Environment['PATH'] = (Split-Path $Python -Parent) + ';' + $env:PATH
    $Info.Environment['VIRTUAL_ENV'] = Split-Path (Split-Path $Python -Parent) -Parent
    foreach ($Argument in @('-u',$Bootstrap,$ViaRoot,$Family,$Target) + $Arguments) { $Info.ArgumentList.Add($Argument) }
    $Process = [System.Diagnostics.Process]::new()
    $Process.StartInfo = $Info
    $Timer = [Diagnostics.Stopwatch]::StartNew()
    $Log = Join-Path $RunDir ($Name + '.log')
    Write-Host "`n=== $Name / $Family ===" -ForegroundColor Cyan
    if (-not $Process.Start()) { throw "啟動失敗：$Name" }
    $Streams = @($Process.StandardOutput, $Process.StandardError)
    $Tasks = @($Streams[0].ReadLineAsync(), $Streams[1].ReadLineAsync())
    while (-not $Process.HasExited -or $null -ne $Tasks[0] -or $null -ne $Tasks[1]) {
        for ($i = 0; $i -lt 2; $i++) {
            if ($null -ne $Tasks[$i] -and $Tasks[$i].IsCompleted) {
                $Line = $Tasks[$i].GetAwaiter().GetResult()
                if ($null -eq $Line) { $Tasks[$i] = $null }
                else {
                    Write-Host $Line
                    Add-Content -LiteralPath $Log -Value $Line -Encoding utf8
                    $Tasks[$i] = $Streams[$i].ReadLineAsync()
                }
            }
        }
        Write-Progress -Activity 'VDF / VRN 加速實測' -Status ("$Name 已執行 {0:N0} 秒；已完成 $($Rows.Count) 個階段" -f $Timer.Elapsed.TotalSeconds)
        Start-Sleep -Milliseconds 100
    }
    $Code = $Process.ExitCode
    $Rows.Add([pscustomobject]@{Step=$Name;Family=$Family;ExitCode=$Code;Seconds=[math]::Round($Timer.Elapsed.TotalSeconds,1);Log=$Log})
    $Rows | Export-Csv (Join-Path $RunDir 'summary.csv') -NoTypeInformation -Encoding utf8BOM
    $Process.Dispose()
    if ($Code -ne 0) { throw "$Name 未通過，EXIT_CODE=$Code；紀錄：$RunDir" }
}

try {
    $Accel = def_Newest 'supportive modules' 'SUP_MDL737_SuperAccelModule_v*.py'
    $Net = def_Newest 'supportive modules\network' 'SUP_MDL740_NetUnified_v*.py'
    $Bus = def_Newest 'supportive modules\registry' 'CGC_MDL148_EngineBus_v*.py'
    if (-not (Select-String -LiteralPath $Bus -Pattern '--profile' -SimpleMatch -Quiet)) { throw 'EngineBus版本過舊，不支援有界測試；請先同步批508或更新版' }
    def_Step '01_VDF_Accel' 'vdf' $Accel @('--selftest')
    def_Step '02_VRN_Accel' 'vrn' $Accel @('--selftest')
    def_Step '03_VDF_Network' 'vdf' $Net @('--selftest')
    $Logic = def_Newest 'functional modules\VRN' 'VRN_ENG082_ExtractionLogic_v*.py'
    def_Step '04_VRN_Logic' 'vrn' $Logic @('--selftest')
    def_Step '05_VDF_Matrix' 'vdf' $Bus @('matrix','--apply-family','vdf','--profile','test','--timeout',"$StationTimeout",'--html')
    def_Step '06_VRN_Matrix' 'vrn' $Bus @('matrix','--apply-family','vrn','--profile','test','--timeout',"$StationTimeout",'--html')
    $Closing = def_Newest 'supportive modules\registry' 'CGC_MDL141_ClosingGate_v*.py'
    def_Step '07_VRN_RealReports' 'vrn' $Closing @('vrn','--run','--dir',$InputDir)
    $Gate = def_Newest 'supportive modules\registry' 'CGC_MDL137_RunGate_v*.py'
    def_Step '08_EnvironmentGate' 'vrn' $Gate @('run','--fast','--family','vdf,vrn')
    $Console = def_Newest 'supportive modules\registry' 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py'
    def_Step '09_Handover' 'vrn' $Console @('page','--publish')
    def_Step '10_ApprovalCheck' 'vrn' $Console @('check')
}
catch {
    $Failure = $_.Exception.Message
    Write-Host $Failure -ForegroundColor Red
    [pscustomobject]@{Status='BLOCKED';Reason=$Failure;CompletedSteps=$Rows.Count} |
        ConvertTo-Json | Set-Content (Join-Path $RunDir 'failure.json') -Encoding utf8
}
finally {
    Write-Progress -Activity 'VDF / VRN 加速實測' -Completed
    $Rows | Format-Table Step,Family,ExitCode,Seconds -AutoSize | Out-Host
    Write-Host "測試紀錄：$RunDir"
}
if ($Failure) { throw $Failure }

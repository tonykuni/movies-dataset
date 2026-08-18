#requires -Version 7.0
# Invoke-VME v0.1 — VME 編排器(TOOL-056;深研報告 preflight 範式落地)
# PowerShell=Launcher/Preflight/Lifecycle;Python=Business+Data Logic。
# fail-closed:preflight 任一缺=停;Python 非零 exit=硬閘門($LASTEXITCODE)。
param(
    [ValidateSet('InspectOnly','SandboxDryRun','RuntimeAppendOnly')][string]$Mode = 'InspectOnly',
    [switch]$ApproveRuntimeAppend
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$VmeRoot = Split-Path $PSCommandPath -Parent
$log = Join-Path $VmeRoot ("..\..\VIA_Reports\command_logs\VME_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
Start-Transcript -Path $log -Append | Out-Null   # 常備令Ⅰ
try {
    foreach($p in @('config\system_config.json','config\schema_registry.json','engines\vme_main.py')){
        $fp = Join-Path $VmeRoot $p
        if(-not (Test-Path -LiteralPath $fp)){ throw "Preflight 缺件:$p" }
        if($p -like '*.json' -and -not (Get-Content -LiteralPath $fp -Raw | Test-Json)){ throw "JSON 壞:$p" } }
    Write-Host "def [OK] Preflight PASS · Mode=$Mode"
    $args2 = @((Join-Path $VmeRoot 'engines\vme_main.py'),'--mode',$Mode)
    if($ApproveRuntimeAppend){ $args2 += '--approve-runtime-append' }
    & py @args2
    if($LASTEXITCODE -ne 0){ throw "vme_main exit=$LASTEXITCODE(硬閘門)" }
    Write-Host "def [OK] VME 完成 · result=runtime\json\operation_result.json"
} catch {
    Write-Host "def [FAIL] $($_.Exception.Message)"
} finally {
    Stop-Transcript | Out-Null
}

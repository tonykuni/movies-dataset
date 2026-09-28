#requires -Version 7.0
# Invoke-VME v0.1 — VME 編排器(TOOL-056;深研報告 preflight 範式落地)
# PowerShell=Launcher/Preflight/Lifecycle;Python=Business+Data Logic。
# fail-closed:preflight 任一缺=停;Python 非零 exit=硬閘門($LASTEXITCODE)。
param(
    [ValidateSet('InspectOnly','SandboxDryRun','RuntimeAppendOnly')][string]$Mode = 'InspectOnly',
    [switch]$ApproveRuntimeAppend
)
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====

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

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit

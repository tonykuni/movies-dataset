#requires -Version 7.0
param(
    [ValidateSet("Probe","Plan","DownloadOnly","Validate","Install")]
    [string]$Action = "Probe",

    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",

    [string]$PythonExe = "",

    [switch]$OpenReport,

    [switch]$ForceInstallUnlock
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$def_PARAM_RUN_STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$def_PARAM_CELERITAS_PY = Join-Path $BaseDir "50_Protection_Acceleration\VeritasCeleritas.py"
$def_PARAM_OUT_DIR = Join-Path $BaseDir "_nexuscore_celeritas_safe_adapter\RUN_$def_PARAM_RUN_STAMP"
$def_PARAM_REPORT_JSON = Join-Path $def_PARAM_OUT_DIR "CELERITAS_SAFE_ADAPTER_REPORT.json"
$def_PARAM_REPORT_HTML = Join-Path $def_PARAM_OUT_DIR "CELERITAS_SAFE_ADAPTER_REPORT.html"

function def_EnsureDir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_ResolvePython {
    if ($PythonExe -and (Test-Path -LiteralPath $PythonExe)) { return $PythonExe }

    foreach ($p in @(
        "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_core_313\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_vrn_312\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe"
    )) {
        if (Test-Path -LiteralPath $p) { return $p }
    }

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $cmd) { return $cmd.Source }

    return ""
}

function def_InvokeProcessWithTimeout {
    param([string]$FileName, [string[]]$Arguments, [int]$TimeoutSeconds)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FileName
    foreach ($arg in $Arguments) { [void]$psi.ArgumentList.Add($arg) }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    [void]$p.Start()
    $completed = $p.WaitForExit($TimeoutSeconds * 1000)

    if (-not $completed) {
        try { $p.Kill() } catch {}
        return [pscustomobject]@{ ExitCode=124; StdOut=""; StdErr="TIMEOUT"; Status="TIMEOUT" }
    }

    return [pscustomobject]@{
        ExitCode=$p.ExitCode
        StdOut=$p.StandardOutput.ReadToEnd()
        StdErr=$p.StandardError.ReadToEnd()
        Status=if($p.ExitCode -eq 0){"PASS"}else{"REVIEW"}
    }
}

function def_WriteHtml {
    param([array]$Rows, [string]$OutPath)

    $table = $Rows | ConvertTo-Html -Fragment
    $html = @"
<!doctype html><html><head><meta charset="utf-8">
<title>Celeritas Safe Adapter Report</title>
<style>
body{font-family:Arial,"Microsoft JhengHei",sans-serif;background:#f6f7fb;color:#111827;margin:24px}
.card{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:18px;margin:16px 0}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#111827;color:#fff;padding:8px;text-align:left}
td{border-bottom:1px solid #e5e7eb;padding:7px;vertical-align:top}
</style></head><body>
<h1>Celeritas Safe Adapter Report</h1>
<div class="card">$table</div>
</body></html>
"@
    $html | Set-Content -LiteralPath $OutPath -Encoding UTF8
}

function def_Main {
    def_EnsureDir -Path $def_PARAM_OUT_DIR

    if ($Action -eq "Install") {
        if (-not $ForceInstallUnlock) {
            throw "INSTALL_LOCKED: Celeritas adapter blocks install by default."
        }
        throw "INSTALL_BLOCKED_SAFE_VERSION: This adapter does not install."
    }

    $python = def_ResolvePython
    $rows = @()

    $exists = Test-Path -LiteralPath $def_PARAM_CELERITAS_PY
    $rows += [pscustomobject]@{
        Check="CeleritasExists"
        Detail=$def_PARAM_CELERITAS_PY
        Status=if($exists){"PASS"}else{"FAIL"}
        Risk=if($exists){"LOW"}else{"HIGH"}
    }

    $rows += [pscustomobject]@{
        Check="Python"
        Detail=$python
        Status=if($python){"PASS"}else{"FAIL"}
        Risk=if($python){"LOW"}else{"HIGH"}
    }

    if ($exists -and $python) {
        $code = @"
import ast, pathlib, json
p = pathlib.Path(r'''$def_PARAM_CELERITAS_PY''')
text = p.read_text(encoding='utf-8', errors='replace')
tree = ast.parse(text)
funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
safe = [k for k in ['dry','dry_run','plan','scan','probe','validate','check','report','download','cache','wheel','install'] if k in text.lower()]
print(json.dumps({'function_count':len(funcs),'functions':funcs[:60],'safe_keywords':safe}, ensure_ascii=False))
"@
        $probe = def_InvokeProcessWithTimeout -FileName $python -Arguments @("-c", $code) -TimeoutSeconds 20
        $rows += [pscustomobject]@{
            Check="ASTSafeProbe"
            Detail=($probe.StdOut + " " + $probe.StdErr).Trim()
            Status=if($probe.ExitCode -eq 0){"PASS"}else{"REVIEW"}
            Risk=if($probe.ExitCode -eq 0){"LOW"}else{"MEDIUM"}
        }
    }

    $rows += [pscustomobject]@{
        Check="AdapterAction"
        Detail="Action=$Action; Mode is non-destructive. DownloadOnly only prepares contract, no network download in safe adapter."
        Status="PASS"
        Risk="LOW"
    }

    $rows += [pscustomobject]@{
        Check="InstallLock"
        Detail="Install remains locked."
        Status="PASS"
        Risk="LOW"
    }

    $rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $def_PARAM_REPORT_JSON -Encoding UTF8
    def_WriteHtml -Rows $rows -OutPath $def_PARAM_REPORT_HTML

    $fail = @($rows | Where-Object { $_.Risk -eq "HIGH" }).Count
    $warn = @($rows | Where-Object { $_.Risk -eq "MEDIUM" }).Count
    $ok = @($rows | Where-Object { $_.Risk -eq "LOW" }).Count
    $risk = if($fail -gt 0){"HIGH"}elseif($warn -gt 0){"MEDIUM"}else{"LOW"}
    $status = if($risk -eq "LOW"){"CELERITAS_SAFE_ADAPTER_READY"}else{"CELERITAS_SAFE_ADAPTER_REVIEW_REQUIRED"}

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def CELERITAS SAFE ADAPTER COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status  : $status"
    Write-Host "Risk    : $risk"
    Write-Host "OK      : $ok"
    Write-Host "WARN    : $warn"
    Write-Host "FAIL    : $fail"
    Write-Host "Install : LOCKED"
    Write-Host "HTML    : $def_PARAM_REPORT_HTML"

    if ($OpenReport -and (Test-Path -LiteralPath $def_PARAM_REPORT_HTML)) {
        Start-Process $def_PARAM_REPORT_HTML
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

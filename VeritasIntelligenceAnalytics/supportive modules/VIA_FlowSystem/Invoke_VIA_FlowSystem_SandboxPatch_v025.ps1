param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VIA_FlowSystem (2)\VIA_FlowSystem",
    [bool]$ApplyPatch = $true,
    [bool]$OpenHtml = $true,
    [bool]$KeepPowerShellOpen = $true
)
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

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function def_WriteBanner {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 84) -ForegroundColor DarkCyan
    Write-Host "def $Title" -ForegroundColor Cyan
    Write-Host ("=" * 84) -ForegroundColor DarkCyan
}

function def_NewUtf8NoBomEncoding {
    return [System.Text.UTF8Encoding]::new($false)
}

function def_ReadText {
    param([string]$Path)
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function def_WriteText {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Text, (def_NewUtf8NoBomEncoding))
}

function def_WriteJson {
    param([object]$Data, [string]$Path)
    $json = $Data | ConvertTo-Json -Depth 20
    def_WriteText -Path $Path -Text $json
}

function def_HtmlEncode {
    param([AllowNull()][object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_NormalizePath {
    param([string]$Path)
    return $Path.Replace('/', '\')
}

function def_CopyBackup {
    param([string]$SourcePath, [string]$BackupRoot, [string]$RelativePath)
    $safeRel = (def_NormalizePath $RelativePath)
    $backupPath = Join-Path $BackupRoot ($safeRel + ".before_v025.bak")
    $backupDir = Split-Path -Parent $backupPath
    if (-not (Test-Path -LiteralPath $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    }
    Copy-Item -LiteralPath $SourcePath -Destination $backupPath -Force
    return $backupPath
}

function def_AddSandboxHelper {
    param([string]$Text)

    if ($Text -match '(?m)^\s*def\s+_sandbox_tmp\s*\(') {
        return $Text
    }

    $needsTempfile = -not ($Text -match '(?m)^\s*import\s+tempfile\b|^\s*from\s+tempfile\s+import\s+')
    $needsPath = -not ($Text -match '(?m)^\s*from\s+pathlib\s+import\s+.*\bPath\b|^\s*import\s+pathlib\b')

    $helper = New-Object System.Collections.Generic.List[string]
    [void]$helper.Add("")
    [void]$helper.Add("# VIA v025 sandbox temp helper · reviewed-safe · self-created temp only")
    if ($needsTempfile) { [void]$helper.Add("import tempfile") }
    if ($needsPath) { [void]$helper.Add("from pathlib import Path") }
    [void]$helper.Add("")
    [void]$helper.Add("def _sandbox_tmp(name: str) -> Path:")
    [void]$helper.Add("    d = Path(tempfile.gettempdir()) / \"via_flow_sandbox\"")
    [void]$helper.Add("    d.mkdir(parents=True, exist_ok=True)")
    [void]$helper.Add("    return d / name")
    [void]$helper.Add("# /VIA v025 sandbox temp helper")
    [void]$helper.Add("")

    $lines = $Text -split "`r?`n", -1
    $insertIndex = 0

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $t = $lines[$i].Trim()
        if ($t -match '^(from|import)\s+') {
            $insertIndex = $i + 1
        }
    }

    if ($insertIndex -eq 0) {
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $t = $lines[$i].Trim()
            if ($i -eq 0 -and $t.StartsWith("#!")) { $insertIndex = $i + 1; continue }
            if ($t -match '^#.*coding[:=]') { $insertIndex = $i + 1; continue }
            break
        }
    }

    $newLines = New-Object System.Collections.Generic.List[string]
    if ($insertIndex -gt 0) {
        for ($i = 0; $i -lt $insertIndex; $i++) { [void]$newLines.Add($lines[$i]) }
    }
    foreach ($line in $helper) { [void]$newLines.Add($line) }
    if ($insertIndex -lt $lines.Count) {
        for ($i = $insertIndex; $i -lt $lines.Count; $i++) { [void]$newLines.Add($lines[$i]) }
    }

    return ($newLines -join "`r`n")
}

function def_RunPythonCompile {
    param([string]$PythonExe, [string]$TargetFile)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $PythonExe
    [void]$psi.ArgumentList.Add("-m")
    [void]$psi.ArgumentList.Add("py_compile")
    [void]$psi.ArgumentList.Add($TargetFile)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    return [pscustomobject]@{
        File = $TargetFile
        ExitCode = $p.ExitCode
        Stdout = $stdout
        Stderr = $stderr
        Status = $(if ($p.ExitCode -eq 0) { "PASS" } else { "FAIL" })
    }
}

function def_WriteHtmlReport {
    param(
        [string]$Path,
        [object]$Summary,
        [object[]]$PatchRows,
        [object[]]$VerifyRows,
        [object[]]$CompileRows
    )

    $rowHtml = New-Object System.Collections.Generic.List[string]
    foreach ($r in $PatchRows) {
        $cls = if ($r.RYG -eq "GREEN") { "ok" } elseif ($r.RYG -eq "YELLOW") { "warn" } else { "fail" }
        [void]$rowHtml.Add("<tr><td>$(def_HtmlEncode $r.RelativePath)</td><td>$(def_HtmlEncode $r.Action)</td><td class='$cls'>$(def_HtmlEncode $r.Status)</td><td>$(def_HtmlEncode $r.Before)</td><td>$(def_HtmlEncode $r.After)</td><td>$(def_HtmlEncode $r.Message)</td></tr>")
    }

    $verifyHtml = New-Object System.Collections.Generic.List[string]
    foreach ($r in $VerifyRows) {
        $cls = if ($r.RYG -eq "GREEN") { "ok" } elseif ($r.RYG -eq "YELLOW") { "warn" } else { "fail" }
        [void]$verifyHtml.Add("<tr><td>$(def_HtmlEncode $r.RelativePath)</td><td class='$cls'>$(def_HtmlEncode $r.Status)</td><td>$(def_HtmlEncode $r.HelperPresent)</td><td>$(def_HtmlEncode $r.BeforeRemaining)</td><td>$(def_HtmlEncode $r.AfterPresent)</td><td>$(def_HtmlEncode $r.Message)</td></tr>")
    }

    $compileHtml = New-Object System.Collections.Generic.List[string]
    foreach ($r in $CompileRows) {
        $cls = if ($r.Status -eq "PASS") { "ok" } else { "fail" }
        [void]$compileHtml.Add("<tr><td>$(def_HtmlEncode $r.File)</td><td class='$cls'>$(def_HtmlEncode $r.Status)</td><td>$(def_HtmlEncode $r.ExitCode)</td><td>$(def_HtmlEncode $r.Stderr)</td></tr>")
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>理 · VIA FlowSystem Sandbox Patch v025</title>
<style>
body{font-family:Inter,'Noto Sans TC',Arial,sans-serif;background:#f5f4f0;color:#1f2933;margin:24px;}
.card{background:#fff;border:1px solid #d8dedb;border-radius:18px;padding:18px;margin:14px 0;box-shadow:0 8px 28px rgba(31,41,51,.06)}
h1{font-size:24px;margin:0 0 6px}.sub{color:#64748b}.pill{display:inline-block;border-radius:999px;padding:6px 10px;margin:4px;background:#eef3f1}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left;vertical-align:top}th{background:#f8fafc}.ok{color:#166534;font-weight:700}.warn{color:#b7791f;font-weight:700}.fail{color:#b91c1c;font-weight:700}code{background:#f1f5f9;padding:2px 5px;border-radius:6px}
</style>
</head>
<body>
<h1>理 · VIA FlowSystem Sandbox Patch v025</h1>
<div class="sub">reviewed-safe · sandbox temp path patch · backup-first · no delete · no activation · no kill</div>
<div class="card">
<span class="pill">Gate: <b>$(def_HtmlEncode $Summary.Gate)</b></span>
<span class="pill">Run ID: <b>$(def_HtmlEncode $Summary.RunId)</b></span>
<span class="pill">Applied: <b>$(def_HtmlEncode $Summary.Applied)</b></span>
<span class="pill">Files patched: <b>$(def_HtmlEncode $Summary.FilesPatched)</b></span>
<span class="pill">Compile fail: <b>$(def_HtmlEncode $Summary.CompileFail)</b></span>
</div>
<div class="card"><h2>1 · Patch Matrix</h2><table><thead><tr><th>File</th><th>Action</th><th>Status</th><th>Before</th><th>After</th><th>Message</th></tr></thead><tbody>$($rowHtml -join "`n")</tbody></table></div>
<div class="card"><h2>2 · Verify Matrix</h2><table><thead><tr><th>File</th><th>Status</th><th>Helper</th><th>Before Remaining</th><th>After Present</th><th>Message</th></tr></thead><tbody>$($verifyHtml -join "`n")</tbody></table></div>
<div class="card"><h2>3 · Python Compile Matrix</h2><table><thead><tr><th>File</th><th>Status</th><th>ExitCode</th><th>stderr</th></tr></thead><tbody>$($compileHtml -join "`n")</tbody></table></div>
<div class="card"><h2>4 · Policy</h2><p>No delete. No activation. No SAP/PLM/MS Project write-back. This patch only redirects self-created temporary files to a sandbox temp folder and keeps backups under the run folder.</p></div>
</body></html>
"@
    def_WriteText -Path $Path -Text $html
}

try {
    def_WriteBanner -Title "VIA FlowSystem · Sandbox Temp Patch v025"
    Write-Host "def BaseDir : $BaseDir" -ForegroundColor White
    Write-Host "def Policy  : backup-first · append-only run output · no delete · no activation · no kill" -ForegroundColor Yellow
    Write-Host "def Apply   : $ApplyPatch" -ForegroundColor White

    if (-not (Test-Path -LiteralPath $BaseDir)) {
        throw "BaseDir not found: $BaseDir"
    }

    $runId = "RUN_$(Get-Date -Format 'yyyyMMdd_HHmmss')_VIA_FLOWSYSTEM_SANDBOX_PATCH_v025"
    $runRoot = Join-Path $BaseDir "_via_flow_runs"
    $runDir = Join-Path $runRoot $runId
    $backupRoot = Join-Path $runDir "backup"
    $matrixDir = Join-Path $runDir "matrix"
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $matrixDir -Force | Out-Null

    $patchSpecs = @(
        [pscustomobject]@{
            RelativePath = "engines\FLOW_ENG001_FlowAutotest.py"
            Replacements = @(
                [pscustomobject]@{ Before = "        out = ROOT / `"_test_sim.html`"";  After = "        out = _sandbox_tmp(`"_test_sim.html`")" },
                [pscustomobject]@{ Before = "        out = ROOT / `"_test_perf.html`""; After = "        out = _sandbox_tmp(`"_test_perf.html`")" },
                [pscustomobject]@{ Before = "        out = ROOT / `"_test_mon.html`"";  After = "        out = _sandbox_tmp(`"_test_mon.html`")" }
            )
        },
        [pscustomobject]@{
            RelativePath = "engines\flow_bridge.py"
            Replacements = @(
                [pscustomobject]@{ Before = "    out = Path(`"_v4_sample.csv`")"; After = "    out = _sandbox_tmp(`"_v4_sample.csv`")" }
            )
        }
    )

    $patchRows = New-Object System.Collections.Generic.List[object]
    $verifyRows = New-Object System.Collections.Generic.List[object]
    $changedFiles = New-Object System.Collections.Generic.List[string]

    foreach ($spec in $patchSpecs) {
        $target = Join-Path $BaseDir $spec.RelativePath
        if (-not (Test-Path -LiteralPath $target)) {
            [void]$patchRows.Add([pscustomobject]@{ RelativePath=$spec.RelativePath; Action="LOOKUP"; Status="FAIL"; RYG="RED"; Before=""; After=""; Message="File not found" })
            continue
        }

        $original = def_ReadText -Path $target
        $patched = def_AddSandboxHelper -Text $original
        $fileChanged = $false

        foreach ($r in $spec.Replacements) {
            if ($patched.Contains($r.Before)) {
                $patched = $patched.Replace($r.Before, $r.After)
                $fileChanged = $true
                [void]$patchRows.Add([pscustomobject]@{ RelativePath=$spec.RelativePath; Action="REPLACE"; Status="APPLIED"; RYG="GREEN"; Before=$r.Before; After=$r.After; Message="Exact reviewed-safe proposal applied" })
            } elseif ($patched.Contains($r.After)) {
                [void]$patchRows.Add([pscustomobject]@{ RelativePath=$spec.RelativePath; Action="REPLACE"; Status="ALREADY_APPLIED"; RYG="GREEN"; Before=$r.Before; After=$r.After; Message="After text already present" })
            } else {
                [void]$patchRows.Add([pscustomobject]@{ RelativePath=$spec.RelativePath; Action="REPLACE"; Status="NOT_FOUND"; RYG="YELLOW"; Before=$r.Before; After=$r.After; Message="Exact before text not found; manual review may be needed" })
            }
        }

        if ($patched -ne $original) {
            if ($ApplyPatch) {
                $backupPath = def_CopyBackup -SourcePath $target -BackupRoot $backupRoot -RelativePath $spec.RelativePath
                def_WriteText -Path $target -Text $patched
                [void]$changedFiles.Add($target)
                [void]$patchRows.Add([pscustomobject]@{ RelativePath=$spec.RelativePath; Action="BACKUP_WRITE"; Status="PASS"; RYG="GREEN"; Before=$target; After=$backupPath; Message="Backup created before source update" })
            } else {
                [void]$patchRows.Add([pscustomobject]@{ RelativePath=$spec.RelativePath; Action="PREVIEW_ONLY"; Status="PASS"; RYG="YELLOW"; Before=""; After=""; Message="Patch generated but not written because ApplyPatch=false" })
            }
        } elseif (-not $fileChanged) {
            [void]$patchRows.Add([pscustomobject]@{ RelativePath=$spec.RelativePath; Action="NO_CHANGE"; Status="PASS"; RYG="GREEN"; Before=""; After=""; Message="No source change required" })
        }
    }

    foreach ($spec in $patchSpecs) {
        $target = Join-Path $BaseDir $spec.RelativePath
        if (-not (Test-Path -LiteralPath $target)) { continue }
        $txt = def_ReadText -Path $target
        $helperPresent = [bool]($txt -match '(?m)^\s*def\s+_sandbox_tmp\s*\(')
        $beforeRemaining = 0
        $afterPresent = 0
        foreach ($r in $spec.Replacements) {
            if ($txt.Contains($r.Before)) { $beforeRemaining++ }
            if ($txt.Contains($r.After)) { $afterPresent++ }
        }
        $status = if ($helperPresent -and $beforeRemaining -eq 0 -and $afterPresent -eq $spec.Replacements.Count) { "PASS" } else { "REVIEW" }
        $ryg = if ($status -eq "PASS") { "GREEN" } else { "YELLOW" }
        [void]$verifyRows.Add([pscustomobject]@{
            RelativePath = $spec.RelativePath
            Status = $status
            RYG = $ryg
            HelperPresent = $helperPresent
            BeforeRemaining = $beforeRemaining
            AfterPresent = "$afterPresent/$($spec.Replacements.Count)"
            Message = $(if ($status -eq "PASS") { "Sandbox temp patch verified" } else { "Patch verification incomplete" })
        })
    }

    $compileRows = New-Object System.Collections.Generic.List[object]
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCmd) { $pythonCmd = Get-Command py -ErrorAction SilentlyContinue }
    if ($null -ne $pythonCmd) {
        $compileTargets = @()
        foreach ($spec in $patchSpecs) { $compileTargets += (Join-Path $BaseDir $spec.RelativePath) }
        foreach ($target in $compileTargets) {
            if (Test-Path -LiteralPath $target) {
                [void]$compileRows.Add((def_RunPythonCompile -PythonExe $pythonCmd.Source -TargetFile $target))
            }
        }
    } else {
        [void]$compileRows.Add([pscustomobject]@{ File="python"; ExitCode=999; Stdout=""; Stderr="Python executable not found"; Status="FAIL" })
    }

    $compileFail = @($compileRows | Where-Object { $_.Status -ne "PASS" }).Count
    $verifyFail = @($verifyRows | Where-Object { $_.Status -ne "PASS" }).Count
    $patchHardFail = @($patchRows | Where-Object { $_.Status -eq "FAIL" }).Count
    $gate = if ($patchHardFail -eq 0 -and $verifyFail -eq 0 -and $compileFail -eq 0) { "PASS_SANDBOX_PATCH_APPLIED" } elseif ($ApplyPatch) { "REVIEW_PATCH_APPLIED_WITH_WARNINGS" } else { "PASS_PREVIEW_ONLY" }

    $summary = [ordered]@{
        Gate = $gate
        RunId = $runId
        BaseDir = $BaseDir
        Applied = $ApplyPatch
        FilesPatched = @($changedFiles).Count
        PatchHardFail = $patchHardFail
        VerifyFail = $verifyFail
        CompileFail = $compileFail
        RunDir = $runDir
        Policy = "backup-first; no delete; no activation; no kill; sandbox temp only"
    }

    $summaryPath = Join-Path $runDir "VIA_FlowSystem_SandboxPatch_v025.summary.json"
    $patchPath = Join-Path $matrixDir "patch_matrix.json"
    $verifyPath = Join-Path $matrixDir "verify_matrix.json"
    $compilePath = Join-Path $matrixDir "compile_matrix.json"
    $htmlPath = Join-Path $runDir "VIA_FlowSystem_SandboxPatch_v025.html"

    def_WriteJson -Data $summary -Path $summaryPath
    def_WriteJson -Data @($patchRows) -Path $patchPath
    def_WriteJson -Data @($verifyRows) -Path $verifyPath
    def_WriteJson -Data @($compileRows) -Path $compilePath
    def_WriteHtmlReport -Path $htmlPath -Summary ([pscustomobject]$summary) -PatchRows @($patchRows) -VerifyRows @($verifyRows) -CompileRows @($compileRows)

    def_WriteBanner -Title "VIA FlowSystem · Sandbox Patch v025 Result"
    Write-Host "def Gate        : $gate" -ForegroundColor Cyan
    Write-Host "def FilesPatched: $(@($changedFiles).Count)" -ForegroundColor White
    Write-Host "def VerifyFail  : $verifyFail" -ForegroundColor White
    Write-Host "def CompileFail : $compileFail" -ForegroundColor White
    Write-Host "def RunDir      : $runDir" -ForegroundColor White
    Write-Host "def HTML        : $htmlPath" -ForegroundColor White
    Write-Host ""
    Write-Host "def Patch Matrix" -ForegroundColor Cyan
    $patchRows | Format-Table -AutoSize
    Write-Host ""
    Write-Host "def Verify Matrix" -ForegroundColor Cyan
    $verifyRows | Format-Table -AutoSize
    Write-Host ""
    Write-Host "def Python Compile Matrix" -ForegroundColor Cyan
    $compileRows | Select-Object File,Status,ExitCode,Stderr | Format-Table -AutoSize

    if ($OpenHtml -and (Test-Path -LiteralPath $htmlPath)) {
        Start-Process -FilePath $htmlPath | Out-Null
    }

    Write-Host ""
    Write-Host "def Done. Backup-first patch only. No delete. No activation. No kill." -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host ("=" * 84) -ForegroundColor DarkRed
    Write-Host "def OUTER SAFE CATCH" -ForegroundColor Red
    Write-Host ("=" * 84) -ForegroundColor DarkRed
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "def PowerShell remains open. No delete. No activation. No source rollback/delete executed." -ForegroundColor Yellow
}
finally {
    if ($KeepPowerShellOpen) {
        Write-Host ""
        Write-Host "def PowerShell remains open. Press Enter to return to prompt." -ForegroundColor Yellow
        try { [void](Read-Host) } catch { }
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

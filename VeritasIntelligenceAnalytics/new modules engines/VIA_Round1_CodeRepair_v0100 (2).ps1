#requires -Version 7.0
param(
    [string[]]$Path      = @('.'),
    [string]$WorkRoot    = 'C:\VeritasIntelligenceAnalytics\CGE\Repair',
    [int]$Throttle       = 10,
    [string]$PythonExe   = '',
    [string]$RuffExe     = '',
    [switch]$DryRun,
    [switch]$NoBrowser
)

# ============================================================
# VIA Round-1 Code Repair Engine v0100
#
# 一輪修正：先全面並行修，再列出順序修，全程不得產生脫落風險。
#
# 工具矩陣（偵測到才用，一律不自動安裝）：
#   Python      ruff check --fix        （毫秒級死碼/未用 import/無效跳脫/import 排序）
#   PowerShell  PSScriptAnalyzer -Fix   （沒裝就退回內建 AST 修正器）
#   內建 AST    [Language.Parser] 精準錨點：別名展開、尾隨空白、BOM
#
# 零脫落保證（Zero-Hydra）：
#   每個檔案在修改前先取「公開介面指紋」（函式/類別/參數/匯出/__all__）。
#   修改後重新解析並比對指紋 —— 只要語法壞掉或公開介面少了任何一個名字，
#   該檔案立刻從備份還原。修得好就留下，修壞就退回，不會留下半殘狀態。
#
# 分流：
#   Parallel-Fixable   第 1 輪一口氣並行修（ThrottleLimit 預設 10）
#   Sequence-Dependent 只列清單與拓撲順序，不自動修（等第 2 輪）
#   Suggest-Only       高 Hydra 風險，永遠只給建議
#
# 執行：pwsh -NoProfile -ExecutionPolicy Bypass -File "<this file>" -Path <目標>
# ============================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Script:Stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$Script:Log   = [System.Collections.Generic.List[string]]::new()
$Script:Start = Get-Date

function Write-Utf8NoBom {
    param([string]$TargetPath, [string]$Text)
    $dir = Split-Path -Path $TargetPath -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::WriteAllText($TargetPath, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Write-Stage {
    param([string]$Message, [int]$Percent = 0, [string]$Level = 'INFO')
    $line = '[' + (Get-Date).ToString('HH:mm:ss') + '][' + $Level + '] ' + $Message
    $Script:Log.Add($line)
    $color = 'Gray'
    if ($Level -eq 'OK')   { $color = 'Green' }
    if ($Level -eq 'WARN') { $color = 'Yellow' }
    if ($Level -eq 'FAIL') { $color = 'Red' }
    Write-Host $line -ForegroundColor $color
    Write-Progress -Activity 'VIA Round-1 Code Repair v0100' -Status $Message -PercentComplete ([math]::Min(100, [math]::Max(0, $Percent)))
}

function ConvertTo-HtmlText {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return $Text.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;').Replace('"', '&quot;')
}

# ------------------------------------------------------------
# 規則政策
# ------------------------------------------------------------

# 第 1 輪可並行自動修：局部、無跨模組副作用
# 只放 ruff 在 safe 模式真的會動手的規則。F841/E711/E712 屬 unsafe-fix，
# 會改變行為（--unsafe-fixes 才動），因此歸到僅建議，不在第 1 輪碰。
$SafeRuffRules = @('F401', 'W291', 'W293', 'W605', 'I001')
$UnsafeRuffRules = @('F841', 'E711', 'E712', 'E713', 'E714')

# 依賴順序修：牽動介面或跨模組，本輪只列不修
$SequenceRuffRules = @('F821', 'F811', 'F403', 'F405', 'E402')
$DiagnoseRuffRules = $SafeRuffRules + $UnsafeRuffRules + $SequenceRuffRules

# VIA 慣例豁免：這些是 Tony 刻意的寫法，工具不得「修正」
$PolicyExempt = @(
    'PSAvoidUsingWriteHost',            # LL：進度輸出刻意用 Write-Host
    'PSAvoidUsingInvokeExpression',     # 計畫腳本刻意用 Invoke-Expression
    'PSUseShouldProcessForStateChangingFunctions',
    'PSAvoidUsingPositionalParameters',
    'PSUseSingularNouns',
    'PSAvoidGlobalVars'
)

# PSScriptAnalyzer 可安全自動修的規則
$SafePssaRules = @(
    'PSAvoidUsingCmdletAliases', 'PSAvoidTrailingWhitespace',
    'PSUseCorrectCasing', 'PSAvoidSemicolonsAsLineTerminators',
    'PSPlaceOpenBrace', 'PSPlaceCloseBrace', 'PSUseConsistentWhitespace'
)

foreach ($sub in @('logs', 'out', 'plans', '_backup')) {
    $target = Join-Path $WorkRoot $sub
    if (-not (Test-Path -LiteralPath $target)) { New-Item -Path $target -ItemType Directory -Force | Out-Null }
}
$BackupDir  = Join-Path $WorkRoot ('_backup\' + $Script:Stamp)
$HtmlPath   = Join-Path $WorkRoot ('out\VIA_Repair_Matrix_' + $Script:Stamp + '.html')
$JsonPath   = Join-Path $WorkRoot ('out\repair_snapshot_' + $Script:Stamp + '.json')
$PlanPath   = Join-Path $WorkRoot ('plans\round2_sequential_' + $Script:Stamp + '.md')
$ProbePath  = Join-Path $WorkRoot 'engine\via_fix_probe.py'
$RollbackPs = Join-Path $WorkRoot ('plans\rollback_repair_' + $Script:Stamp + '.ps1')

Write-Stage -Message 'VIA Round-1 Code Repair Engine v0100 啟動' -Percent 1 -Level 'OK'

# ------------------------------------------------------------
# 0. 工具偵測（偵測到才用，絕不自動安裝）
# ------------------------------------------------------------

function Resolve-Exe {
    param([string]$Preferred, [string[]]$Candidates)
    if ($Preferred) { return $Preferred }
    foreach ($candidate in $Candidates) {
        $found = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $found) { return $found.Source }
    }
    return ''
}

$pyExe   = Resolve-Exe -Preferred $PythonExe -Candidates @('python', 'python3', 'py')
$ruffExe = Resolve-Exe -Preferred $RuffExe   -Candidates @('ruff')
$hasPssa = $null -ne (Get-Module -ListAvailable -Name PSScriptAnalyzer -ErrorAction SilentlyContinue)
if ($hasPssa) { Import-Module PSScriptAnalyzer -ErrorAction SilentlyContinue }

$tools = [System.Collections.Generic.List[object]]::new()
$tools.Add([pscustomobject]@{ tool = 'python'; path = $pyExe;   state = $(if ($pyExe) { 'AVAILABLE' } else { 'ABSENT' }); role = '指紋擷取與 AST 解析' })
$tools.Add([pscustomobject]@{ tool = 'ruff';   path = $ruffExe; state = $(if ($ruffExe) { 'AVAILABLE' } else { 'ABSENT' }); role = 'Python 診斷與安全自動修' })
$tools.Add([pscustomobject]@{ tool = 'PSScriptAnalyzer'; path = ''; state = $(if ($hasPssa) { 'AVAILABLE' } else { 'ABSENT' }); role = 'PowerShell 診斷與自動修' })
$tools.Add([pscustomobject]@{ tool = 'Language.Parser'; path = 'built-in'; state = 'AVAILABLE'; role = 'PowerShell AST 精準錨點（PSSA 缺席時的後援）' })
foreach ($tool in $tools) {
    Write-Stage -Message ('  ' + $tool.tool.PadRight(18) + $tool.state) -Percent 4 -Level $(if ($tool.state -eq 'AVAILABLE') { 'OK' } else { 'WARN' })
}

# ------------------------------------------------------------
# 1. 目標探索
# ------------------------------------------------------------

$enumOptions = [System.IO.EnumerationOptions]::new()
$enumOptions.RecurseSubdirectories = $true
$enumOptions.IgnoreInaccessible    = $true
$enumOptions.AttributesToSkip      = [System.IO.FileAttributes]::ReparsePoint
$skipDirs = @('.git', '.venv', 'venv', '__pycache__', 'node_modules', 'site-packages', '_backup', '_legacy', '_to_delete', 'out', 'logs')

$targets = [System.Collections.Generic.List[object]]::new()
foreach ($root in $Path) {
    $resolved = (Resolve-Path -LiteralPath $root -ErrorAction SilentlyContinue)
    if ($null -eq $resolved) { Write-Stage -Message ('找不到路徑：' + $root) -Percent 6 -Level 'WARN'; continue }
    $full = $resolved.Path
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        $targets.Add([pscustomobject]@{ path = $full; name = (Split-Path $full -Leaf); ext = [System.IO.Path]::GetExtension($full).ToLowerInvariant() })
        continue
    }
    foreach ($file in [System.IO.Directory]::EnumerateFiles($full, '*', $enumOptions)) {
        $ext = [System.IO.Path]::GetExtension($file).ToLowerInvariant()
        if ($ext -ne '.py' -and $ext -ne '.ps1' -and $ext -ne '.psm1') { continue }
        $blocked = $false
        foreach ($segment in $file.Split([char[]]@('\', '/'))) {
            if ($skipDirs -contains $segment.ToLowerInvariant()) { $blocked = $true; break }
        }
        if ($blocked) { continue }
        $targets.Add([pscustomobject]@{ path = $file; name = [System.IO.Path]::GetFileName($file); ext = $ext })
    }
}

if ($targets.Count -eq 0) {
    Write-Stage -Message '沒有可處理的 .py / .ps1 / .psm1' -Percent 100 -Level 'FAIL'
    return
}
$pyTargets = @($targets | Where-Object { $_.ext -eq '.py' })
$psTargets = @($targets | Where-Object { $_.ext -ne '.py' })
Write-Stage -Message ('目標：' + $targets.Count + ' 檔（Python ' + $pyTargets.Count + '，PowerShell ' + $psTargets.Count + '）') -Percent 8 -Level 'OK'

function Get-Zone {
    param([string]$Name, [string]$Ext)
    $lower = $Name.ToLowerInvariant()
    if ($Ext -eq '.psm1' -or $lower -match 'manager|console|launcher|dispatcher|^invoke-|^start-') { return 'MODULE' }
    if ($lower -match 'engine|nexus|harness|inspector|celeritas|aegis|guard') { return 'ENGINE' }
    if ($lower -match 'lib|util|toolkit|support|helper|batch|client') { return 'FUNCTION-LIB' }
    return 'OTHERS'
}

# ------------------------------------------------------------
# 2. 指紋探針（Python 端以內嵌引擎批次處理）
# ------------------------------------------------------------

$probeSource = @'
"""VIA fix probe - stdlib only. Extract the public surface fingerprint."""
import ast
import json
import os
import sys


def read(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    for enc in ("utf-8-sig", "utf-8", "cp950", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


def fingerprint(path):
    row = {"path": path, "ok": True, "error": "", "functions": [], "classes": [],
           "dunder_all": [], "assigns": [], "is_init": os.path.basename(path) == "__init__.py"}
    try:
        text = read(path)
    except OSError as exc:
        row["ok"] = False
        row["error"] = str(exc)
        return row
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        row["ok"] = False
        row["error"] = "line %s: %s" % (exc.lineno, exc.msg)
        return row
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            row["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            row["classes"].append(node.name)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    row["assigns"].append(target.id)
                    if target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        row["dunder_all"] = [e.value for e in node.value.elts
                                             if isinstance(e, ast.Constant)]
    row["functions"] = sorted(set(row["functions"]))
    row["classes"] = sorted(set(row["classes"]))
    row["assigns"] = sorted(set(row["assigns"]))
    return row


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        paths = json.load(handle)
    rows = [fingerprint(p) for p in paths if os.path.isfile(p)]
    with open(sys.argv[2], "w", encoding="utf-8") as handle:
        json.dump({"rows": rows}, handle, ensure_ascii=False)


if __name__ == "__main__":
    main()
'@

function Get-PythonFingerprints {
    param([object[]]$Files, [string]$Tag)
    $result = @{}
    if ($Files.Count -eq 0 -or -not $pyExe) { return $result }
    $listPath = Join-Path $WorkRoot ('engine\probe_list_' + $Tag + '.json')
    $outPath  = Join-Path $WorkRoot ('engine\probe_out_' + $Tag + '.json')
    Write-Utf8NoBom -TargetPath $listPath -Text (@($Files | ForEach-Object { $_.path }) | ConvertTo-Json -Depth 3)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $pyExe
    $psi.Arguments = ('"' + $ProbePath + '" "' + $listPath + '" "' + $outPath + '"')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $false
    $psi.RedirectStandardError  = $false
    $psi.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    $proc.WaitForExit()
    if ($proc.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $outPath)) { return $result }
    $doc = Get-Content -LiteralPath $outPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($row in $doc.rows) { $result[[string]$row.path] = $row }
    return $result
}

function Get-PsFingerprint {
    param([string]$FilePath)
    $tokens = $null
    $errs   = $null
    $names  = [System.Collections.Generic.List[string]]::new()
    try {
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($FilePath, [ref]$tokens, [ref]$errs)
    } catch {
        return [pscustomobject]@{ ok = $false; error = $_.Exception.Message; names = @() }
    }
    if ($null -ne $errs -and $errs.Count -gt 0) {
        return [pscustomobject]@{ ok = $false; error = ('line ' + $errs[0].Extent.StartLineNumber + ': ' + $errs[0].Message); names = @() }
    }
    foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
        $names.Add('fn:' + $fn.Name)
    }
    foreach ($pb in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.ParamBlockAst] }, $true)) {
        foreach ($p in $pb.Parameters) { $names.Add('param:' + $p.Name.VariablePath.UserPath) }
    }
    $cmdCount = 0
    $elemCount = 0
    foreach ($cmd in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
        $cmdCount++
        $elemCount += $cmd.CommandElements.Count
        $first = $cmd.GetCommandName()
        if ($first -and $first -ieq 'Export-ModuleMember') {
            foreach ($el in $cmd.CommandElements) { $names.Add('export:' + $el.Extent.Text) }
        }
    }
    return [pscustomobject]@{ ok = $true; error = ''; names = @($names | Sort-Object -Unique)
                              cmd_count = $cmdCount; elem_count = $elemCount }
}

Write-Stage -Message '取得修改前的公開介面指紋' -Percent 12
Write-Utf8NoBom -TargetPath $ProbePath -Text $probeSource
$pyBefore = Get-PythonFingerprints -Files $pyTargets -Tag 'before'

$psBefore = @{}
$psResults = @($psTargets | ForEach-Object -ThrottleLimit $Throttle -Parallel {
    $file = $_
    $tokens = $null
    $errs = $null
    $names = [System.Collections.Generic.List[string]]::new()
    $cmdCount = 0
    $elemCount = 0
    $ok = $true
    $err = ''
    try {
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($file.path, [ref]$tokens, [ref]$errs)
        if ($null -ne $errs -and $errs.Count -gt 0) {
            $ok = $false
            $err = 'line ' + $errs[0].Extent.StartLineNumber + ': ' + $errs[0].Message
        } else {
            foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) { $names.Add('fn:' + $fn.Name) }
            foreach ($pb in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.ParamBlockAst] }, $true)) {
                foreach ($p in $pb.Parameters) { $names.Add('param:' + $p.Name.VariablePath.UserPath) }
            }
            foreach ($cmd in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
                $cmdCount++
                $elemCount += $cmd.CommandElements.Count
            }
        }
    } catch {
        $ok = $false
        $err = $_.Exception.Message
    }
    [pscustomobject]@{ path = $file.path; ok = $ok; error = $err; names = @($names | Sort-Object -Unique)
                       cmd_count = $cmdCount; elem_count = $elemCount }
})
foreach ($row in $psResults) { $psBefore[$row.path] = $row }
$brokenBefore = @($psResults | Where-Object { -not $_.ok }).Count +
                @($pyBefore.Values | Where-Object { -not $_.ok }).Count
Write-Stage -Message ('指紋完成；修前語法不通過的檔案 ' + $brokenBefore + ' 個（這些一律不修）') -Percent 20 -Level $(if ($brokenBefore) { 'WARN' } else { 'OK' })

# ------------------------------------------------------------
# 3. 全景診斷
# ------------------------------------------------------------

Write-Stage -Message '全景診斷' -Percent 24

$diagnostics = [System.Collections.Generic.List[object]]::new()

if ($ruffExe -and $pyTargets.Count -gt 0) {
    $argList = @('check', '--output-format', 'json', '--no-fix', '--isolated', '--select', ($DiagnoseRuffRules -join ','))
    foreach ($file in $pyTargets) { $argList += $file.path }
    try {
        $raw = & $ruffExe @argList 2>$null | Out-String
        if ($raw.Trim()) {
            foreach ($item in ($raw | ConvertFrom-Json)) {
                $code = [string]$item.code
                $bucket = 'SUGGEST'
                if ($SafeRuffRules -contains $code) { $bucket = 'PARALLEL' }
                elseif ($SequenceRuffRules -contains $code) { $bucket = 'SEQUENCE' }
                $diagnostics.Add([pscustomobject]@{
                    tool = 'ruff'; file = [string]$item.filename
                    name = (Split-Path ([string]$item.filename) -Leaf)
                    line = [int]$item.location.row; rule = $code
                    message = [string]$item.message; bucket = $bucket
                })
            }
        }
    } catch {
        Write-Stage -Message ('ruff 診斷失敗：' + $_.Exception.Message) -Percent 26 -Level 'WARN'
    }
    Write-Stage -Message ('ruff 診斷：' + @($diagnostics | Where-Object { $_.tool -eq 'ruff' }).Count + ' 項') -Percent 30 -Level 'OK'
} elseif ($pyTargets.Count -gt 0) {
    Write-Stage -Message 'ruff 不存在，Python 端只做語法解析，不做規則診斷' -Percent 30 -Level 'WARN'
}

if ($hasPssa -and $psTargets.Count -gt 0) {
    foreach ($file in $psTargets) {
        try {
            foreach ($record in (Invoke-ScriptAnalyzer -Path $file.path -Severity Warning, Error -ErrorAction SilentlyContinue)) {
                $rule = [string]$record.RuleName
                if ($PolicyExempt -contains $rule) { continue }
                $bucket = 'SUGGEST'
                if ($SafePssaRules -contains $rule) { $bucket = 'PARALLEL' }
                $diagnostics.Add([pscustomobject]@{
                    tool = 'PSSA'; file = $file.path; name = $file.name
                    line = [int]$record.Line; rule = $rule
                    message = [string]$record.Message; bucket = $bucket
                })
            }
        } catch {
            Write-Stage -Message ('PSSA 掃描失敗 ' + $file.name + '：' + $_.Exception.Message) -Percent 32 -Level 'WARN'
        }
    }
    Write-Stage -Message ('PSSA 診斷：' + @($diagnostics | Where-Object { $_.tool -eq 'PSSA' }).Count + ' 項') -Percent 34 -Level 'OK'
}

# 內建 AST 後援：別名展開 + 尾隨空白 + BOM（不需要 PSSA）
$builtinFixPlan = @{}
foreach ($file in $psTargets) {
    $before = $psBefore[$file.path]
    if (-not $before.ok) { continue }
    $tokens = $null
    $errs   = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($file.path, [ref]$tokens, [ref]$errs)
    $localFunctions = @()
    foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
        $localFunctions += $fn.Name
    }
    $edits = [System.Collections.Generic.List[object]]::new()
    foreach ($cmd in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
        $name = $cmd.GetCommandName()
        if (-not $name) { continue }
        if ($localFunctions -contains $name) { continue }
        # '?' 與 '%' 會被 Get-Alias 當萬用字元，一次比中一堆別名，
        # 定義串接後會把 '? { }' 改成 'Where-Object ForEach-Object ...'。必須跳脫。
        $escaped = [System.Management.Automation.WildcardPattern]::Escape($name)
        $aliasHits = @(Get-Alias -Name $escaped -ErrorAction SilentlyContinue)
        if ($aliasHits.Count -ne 1) { continue }
        $definition = [string]$aliasHits[0].Definition
        if (-not $definition -or $definition -ieq $name) { continue }
        if ($definition -notmatch '^[A-Za-z][A-Za-z0-9-]*$') { continue }
        $element = $cmd.CommandElements[0]
        $edits.Add([pscustomobject]@{
            offset = $element.Extent.StartOffset; length = ($element.Extent.EndOffset - $element.Extent.StartOffset)
            replacement = $definition; line = $element.Extent.StartLineNumber; original = $name
        })
        $diagnostics.Add([pscustomobject]@{
            tool = 'AST'; file = $file.path; name = $file.name
            line = $element.Extent.StartLineNumber; rule = 'VIA-AliasExpansion'
            message = ('別名 ' + $name + ' 應展開為 ' + $definition); bucket = 'PARALLEL'
        })
    }
    $text = [System.IO.File]::ReadAllText($file.path)
    $needsWhitespace = [regex]::IsMatch($text, '(?m)[ \t]+$')
    $needsBomStrip = $false
    $bytes = [System.IO.File]::ReadAllBytes($file.path)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $needsBomStrip = $true }
    if ($needsWhitespace) {
        $diagnostics.Add([pscustomobject]@{
            tool = 'AST'; file = $file.path; name = $file.name; line = 0
            rule = 'VIA-TrailingWhitespace'; message = '存在尾隨空白'; bucket = 'PARALLEL' })
    }
    if ($edits.Count -gt 0 -or $needsWhitespace -or $needsBomStrip) {
        $builtinFixPlan[$file.path] = [pscustomobject]@{
            edits = @($edits); whitespace = $needsWhitespace; bom = $needsBomStrip }
    }
}
Write-Stage -Message ('內建 AST 後援：' + $builtinFixPlan.Keys.Count + ' 個檔案有可修項目') -Percent 38 -Level 'OK'

$parallelCount = @($diagnostics | Where-Object { $_.bucket -eq 'PARALLEL' }).Count
$sequenceCount = @($diagnostics | Where-Object { $_.bucket -eq 'SEQUENCE' }).Count
$suggestCount  = @($diagnostics | Where-Object { $_.bucket -eq 'SUGGEST' }).Count
Write-Stage -Message ('分流：並行 ' + $parallelCount + '，順序 ' + $sequenceCount + '，僅建議 ' + $suggestCount) -Percent 42 -Level 'OK'

# ------------------------------------------------------------
# 4. 備份
# ------------------------------------------------------------

$touchable = @($targets | Where-Object {
    $record = $null
    if ($_.ext -eq '.py') { $record = $pyBefore[$_.path] } else { $record = $psBefore[$_.path] }
    $null -ne $record -and $record.ok
})
Write-Stage -Message ('可安全修改的檔案：' + $touchable.Count + ' / ' + $targets.Count) -Percent 46

if (-not $DryRun) {
    foreach ($file in $touchable) {
        $dest = Join-Path $BackupDir ($file.path -replace '^[A-Za-z]:', '' -replace '^[\\/]', '')
        $destDir = Split-Path -Path $dest -Parent
        if (-not (Test-Path -LiteralPath $destDir)) { New-Item -Path $destDir -ItemType Directory -Force | Out-Null }
        Copy-Item -LiteralPath $file.path -Destination $dest -Force
    }
    Write-Stage -Message ('備份完成 -> ' + $BackupDir) -Percent 50 -Level 'OK'
} else {
    Write-Stage -Message 'DRY-RUN：不備份也不修改' -Percent 50 -Level 'WARN'
}

# ------------------------------------------------------------
# 5. 第 1 輪：並行修正
# ------------------------------------------------------------

$applied = [System.Collections.Generic.List[object]]::new()

if (-not $DryRun -and $ruffExe -and $pyTargets.Count -gt 0) {
    Write-Stage -Message ('第 1 輪 Python：ruff --fix（' + ($SafeRuffRules -join ',') + '）') -Percent 54
    $fixable = @($touchable | Where-Object { $_.ext -eq '.py' })
    if ($fixable.Count -gt 0) {
        $argList = @('check', '--fix', '--isolated', '--no-cache', '--select', ($SafeRuffRules -join ','))
        # __init__.py 的未使用 import 常常是刻意的再匯出，整檔排除 F401
        $initFiles = @($fixable | Where-Object { $_.name -ieq '__init__.py' })
        $normal    = @($fixable | Where-Object { $_.name -ine '__init__.py' })
        if ($normal.Count -gt 0) {
            $runArgs = $argList + @($normal | ForEach-Object { $_.path })
            try { $null = & $ruffExe @runArgs 2>&1 } catch { Write-Stage -Message ('ruff --fix 例外：' + $_.Exception.Message) -Percent 56 -Level 'WARN' }
        }
        if ($initFiles.Count -gt 0) {
            $initRules = @($SafeRuffRules | Where-Object { $_ -ne 'F401' })
            $runArgs = @('check', '--fix', '--isolated', '--no-cache', '--select', ($initRules -join ',')) + @($initFiles | ForEach-Object { $_.path })
            try { $null = & $ruffExe @runArgs 2>&1 } catch { }
            Write-Stage -Message ($initFiles.Count.ToString() + ' 個 __init__.py 已排除 F401（再匯出保護）') -Percent 57 -Level 'OK'
        }
        $applied.Add([pscustomobject]@{ tool = 'ruff'; scope = ($fixable.Count.ToString() + ' py'); rules = ($SafeRuffRules -join ',') })
    }
}

if (-not $DryRun -and $psTargets.Count -gt 0) {
    Write-Stage -Message ('第 1 輪 PowerShell：並行度 ' + $Throttle) -Percent 60
    $psFixable = @($touchable | Where-Object { $_.ext -ne '.py' })
    $planTable = $builtinFixPlan
    $usePssa = $hasPssa
    $safeRules = $SafePssaRules
    $results = @($psFixable | ForEach-Object -ThrottleLimit $Throttle -Parallel {
        $file = $_
        $plan = ($using:planTable)[$file.path]
        $changed = [System.Collections.Generic.List[string]]::new()
        try {
            if ($using:usePssa) {
                Import-Module PSScriptAnalyzer -ErrorAction SilentlyContinue
                Invoke-ScriptAnalyzer -Path $file.path -Fix -IncludeRule ($using:safeRules) -ErrorAction SilentlyContinue | Out-Null
                $changed.Add('PSSA -Fix')
            }
            if ($null -ne $plan) {
                $text = [System.IO.File]::ReadAllText($file.path)
                if ($plan.edits.Count -gt 0) {
                    foreach ($edit in ($plan.edits | Sort-Object -Property @{ e = 'offset'; desc = $true })) {
                        if ($edit.offset -lt 0 -or ($edit.offset + $edit.length) -gt $text.Length) { continue }
                        $text = $text.Remove($edit.offset, $edit.length).Insert($edit.offset, $edit.replacement)
                    }
                    $changed.Add('alias x' + $plan.edits.Count)
                }
                if ($plan.whitespace) {
                    $text = [regex]::Replace($text, '(?m)[ \t]+$', '')
                    $changed.Add('trailing-ws')
                }
                if ($plan.bom -or $changed.Count -gt 0) {
                    [System.IO.File]::WriteAllText($file.path, $text, [System.Text.UTF8Encoding]::new($false))
                    if ($plan.bom) { $changed.Add('bom-strip') }
                }
            }
            [pscustomobject]@{ path = $file.path; name = $file.name; changed = @($changed); error = '' }
        } catch {
            [pscustomobject]@{ path = $file.path; name = $file.name; changed = @(); error = $_.Exception.Message }
        }
    })
    foreach ($row in $results) {
        if ($row.changed.Count -gt 0) {
            $applied.Add([pscustomobject]@{ tool = 'PS'; scope = $row.name; rules = ($row.changed -join ', ') })
        }
        if ($row.error) { Write-Stage -Message ('修正例外 ' + $row.name + '：' + $row.error) -Percent 64 -Level 'WARN' }
    }
    Write-Stage -Message ('PowerShell 第 1 輪完成：' + @($results | Where-Object { $_.changed.Count -gt 0 }).Count + ' 檔有變更') -Percent 66 -Level 'OK'
}

# ------------------------------------------------------------
# 6. 驗證與自動回滾（零脫落保證）
# ------------------------------------------------------------

Write-Stage -Message '驗證公開介面指紋，任何脫落即回滾' -Percent 70

$rollbacks = [System.Collections.Generic.List[object]]::new()
$verified  = [System.Collections.Generic.List[object]]::new()

function Restore-FromBackup {
    param([string]$FilePath)
    $dest = Join-Path $BackupDir ($FilePath -replace '^[A-Za-z]:', '' -replace '^[\\/]', '')
    if (-not (Test-Path -LiteralPath $dest)) { return $false }
    Copy-Item -LiteralPath $dest -Destination $FilePath -Force
    return $true
}

if (-not $DryRun) {
    $pyAfter = Get-PythonFingerprints -Files @($touchable | Where-Object { $_.ext -eq '.py' }) -Tag 'after'
    foreach ($file in $touchable) {
        $reason = ''
        if ($file.ext -eq '.py') {
            $before = $pyBefore[$file.path]
            $after  = $pyAfter[$file.path]
            if ($null -eq $after) { $reason = '修後無法取得指紋' }
            elseif (-not $after.ok) { $reason = '修後語法錯誤：' + $after.error }
            else {
                $lostFn = @($before.functions | Where-Object { $after.functions -notcontains $_ })
                $lostCls = @($before.classes | Where-Object { $after.classes -notcontains $_ })
                $lostAll = @($before.dunder_all | Where-Object { $after.dunder_all -notcontains $_ })
                $lostAsg = @($before.assigns | Where-Object { $after.assigns -notcontains $_ })
                if ($lostFn.Count) { $reason = '函式脫落：' + ($lostFn -join ', ') }
                elseif ($lostCls.Count) { $reason = '類別脫落：' + ($lostCls -join ', ') }
                elseif ($lostAll.Count) { $reason = '__all__ 脫落：' + ($lostAll -join ', ') }
                elseif ($lostAsg.Count) { $reason = '模組層變數脫落：' + ($lostAsg -join ', ') }
            }
        } else {
            $before = $psBefore[$file.path]
            $after  = Get-PsFingerprint -FilePath $file.path
            if (-not $after.ok) { $reason = '修後語法錯誤：' + $after.error }
            else {
                $lost = @($before.names | Where-Object { $after.names -notcontains $_ })
                if ($lost.Count) { $reason = '介面脫落：' + (($lost | Select-Object -First 6) -join ', ') }
                elseif ($before.cmd_count -ne $after.cmd_count) {
                    $reason = '指令數量改變：' + $before.cmd_count + ' -> ' + $after.cmd_count
                }
                elseif ($before.elem_count -ne $after.elem_count) {
                    # 別名展開只換名字，不會增減參數元素。變了就是改壞了。
                    $reason = '指令元素數量改變：' + $before.elem_count + ' -> ' + $after.elem_count
                }
            }
        }
        if ($reason) {
            $restored = Restore-FromBackup -FilePath $file.path
            $rollbacks.Add([pscustomobject]@{ name = $file.name; path = $file.path; reason = $reason; restored = $restored })
        } else {
            $verified.Add([pscustomobject]@{ name = $file.name; path = $file.path; zone = (Get-Zone -Name $file.name -Ext $file.ext) })
        }
    }
    Write-Stage -Message ('驗證：通過 ' + $verified.Count + '，回滾 ' + $rollbacks.Count) -Percent 78 -Level $(if ($rollbacks.Count) { 'WARN' } else { 'OK' })
}

# ------------------------------------------------------------
# 7. 修後重新診斷（delta）
# ------------------------------------------------------------

$afterDiagCount = -1
if (-not $DryRun -and $ruffExe -and $pyTargets.Count -gt 0) {
    $argList = @('check', '--output-format', 'json', '--no-fix', '--isolated', '--select', ($DiagnoseRuffRules -join ','))
    foreach ($file in $pyTargets) { $argList += $file.path }
    try {
        $raw = & $ruffExe @argList 2>$null | Out-String
        if ($raw.Trim()) { $afterDiagCount = @($raw | ConvertFrom-Json).Count } else { $afterDiagCount = 0 }
    } catch { $afterDiagCount = -1 }
    Write-Stage -Message ('修後 ruff 剩餘：' + $afterDiagCount + ' 項（修前 ' + @($diagnostics | Where-Object { $_.tool -eq 'ruff' }).Count + '）') -Percent 84 -Level 'OK'
}

# ------------------------------------------------------------
# 8. 第 2 輪清單（只列不修）與 rollback 腳本
# ------------------------------------------------------------

$sequenceItems = @($diagnostics | Where-Object { $_.bucket -eq 'SEQUENCE' } |
    Sort-Object -Property @{ e = 'rule'; desc = $false }, @{ e = 'name'; desc = $false })
$md = [System.Collections.Generic.List[string]]::new()
$md.Add('# VIA Round-2 Sequential Queue — ' + $Script:Stamp)
$md.Add('')
$md.Add('本輪**未修**下列項目。它們會牽動跨模組介面或執行順序，必須依拓撲順序逐一沙盒驗證。')
$md.Add('')
$md.Add('| # | Rule | File | Line | Message |')
$md.Add('|---|---|---|---|---|')
$order = 0
foreach ($item in $sequenceItems) {
    $order++
    $md.Add('| ' + $order + ' | ' + $item.rule + ' | ' + $item.name + ' | ' + $item.line + ' | ' + ($item.message -replace '\|', '\\|') + ' |')
}
if ($sequenceItems.Count -eq 0) { $md.Add('| — | — | — | — | 無 |') }
$md.Add('')
$md.Add('## 政策豁免（工具報了但 VIA 刻意如此，不修）')
foreach ($rule in $PolicyExempt) { $md.Add('- ' + $rule) }
Write-Utf8NoBom -TargetPath $PlanPath -Text (($md -join "`n") + "`n")

$rb = [System.Collections.Generic.List[string]]::new()
$rb.Add('#requires -Version 7.0')
$rb.Add('param([switch]$Commit)')
$rb.Add('# 把第 1 輪的所有修改整批還原到 ' + $Script:Stamp + ' 之前的狀態。')
$rb.Add('$ErrorActionPreference = ''Stop''')
$rb.Add('$Backup = ''' + $BackupDir.Replace("'", "''") + '''')
$rb.Add('if (-not (Test-Path -LiteralPath $Backup)) { Write-Host ''找不到備份目錄'' -ForegroundColor Red; return }')
foreach ($file in $verified) {
    $dest = Join-Path $BackupDir ($file.path -replace '^[A-Za-z]:', '' -replace '^[\\/]', '')
    $rb.Add('if (-not $Commit) { Write-Host ("[DRY] restore " + ''' + $file.path.Replace("'", "''") + ''') -ForegroundColor Yellow } else { Copy-Item -LiteralPath ''' + $dest.Replace("'", "''") + ''' -Destination ''' + $file.path.Replace("'", "''") + ''' -Force; Write-Host ("[RESTORED] " + ''' + $file.name.Replace("'", "''") + ''') -ForegroundColor Green }')
}
Write-Utf8NoBom -TargetPath $RollbackPs -Text (($rb -join "`n") + "`n")

# ------------------------------------------------------------
# 9. HTML UI Matrix
# ------------------------------------------------------------

Write-Stage -Message '渲染 UI Matrix' -Percent 90

function New-Rows {
    param([object[]]$Items, [string[]]$Fields, [string]$StatusField = '', [int]$Limit = 500)
    $sb = [System.Text.StringBuilder]::new()
    $count = 0
    foreach ($item in $Items) {
        if ($count -ge $Limit) { break }
        $count++
        $null = $sb.Append('<tr>')
        foreach ($field in $Fields) {
            $value = ''
            if ($item.PSObject.Properties.Name -contains $field) {
                $raw = $item.$field
                if ($raw -is [System.Array]) { $value = ($raw -join ', ') } else { $value = [string]$raw }
            }
            $cls = ''
            if ($StatusField -and $field -eq $StatusField) {
                if ($value -match 'AVAILABLE|PARALLEL|OK|GREEN') { $cls = " class='ok'" }
                elseif ($value -match 'ABSENT|SEQUENCE|FAIL|RED') { $cls = " class='fail'" }
                elseif ($value -match 'SUGGEST|WARN|AMBER') { $cls = " class='warn'" }
            }
            $null = $sb.Append('<td' + $cls + '>' + (ConvertTo-HtmlText -Text $value) + '</td>')
        }
        $null = $sb.Append('</tr>')
    }
    if ($count -eq 0) { $null = $sb.Append("<tr><td colspan='" + $Fields.Count + "' class='muted'>—— 無 ——</td></tr>") }
    return $sb.ToString()
}

$zoneRows = [System.Collections.Generic.List[object]]::new()
foreach ($zone in @('MODULE', 'ENGINE', 'FUNCTION-LIB', 'OTHERS')) {
    $members = @($targets | Where-Object { (Get-Zone -Name $_.name -Ext $_.ext) -eq $zone })
    if ($members.Count -eq 0) { continue }
    $names = @($members | ForEach-Object { $_.name })
    $issues = @($diagnostics | Where-Object { $names -contains $_.name }).Count
    $rolled = @($rollbacks | Where-Object { $names -contains $_.name }).Count
    $light = 'GREEN'
    if ($issues -gt 0) { $light = 'AMBER' }
    if ($rolled -gt 0) { $light = 'RED' }
    $zoneRows.Add([pscustomobject]@{ zone = $zone; files = $members.Count; issues = $issues; rolled = $rolled; light = $light })
}

$verdict = 'GREEN'
if ($sequenceCount -gt 0 -or $suggestCount -gt 0) { $verdict = 'AMBER' }
if ($rollbacks.Count -gt 0 -or $brokenBefore -gt 0) { $verdict = 'RED' }
$verdictClass = 'ok'
if ($verdict -eq 'AMBER') { $verdictClass = 'warn' }
if ($verdict -eq 'RED')   { $verdictClass = 'fail' }
$elapsed = [int]((Get-Date) - $Script:Start).TotalSeconds
$modeText = 'APPLIED（已備份，指紋不符自動回滾）'
if ($DryRun) { $modeText = 'DRY-RUN（只診斷不修改）' }

$html = @"
<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Round-1 Code Repair Matrix</title>
<style>
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
tr:hover td{background:#fbfbfb}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:34vh;overflow:auto}
code{background:#ececed;padding:1px 5px;border-radius:2px}
</style></head><body>
<div class="seal">修</div>
<h1>Round-1 Code Repair Matrix</h1>
<p class="lede">$($Script:Stamp) · $modeText · 並行度 $Throttle · 耗時 ${elapsed}s · 備份 $(ConvertTo-HtmlText -Text $BackupDir)</p>
<div class="cards">
  <div class="card"><div class="k">Verdict</div><div class="v $verdictClass">$verdict</div></div>
  <div class="card"><div class="k">Files</div><div class="v">$($targets.Count)</div></div>
  <div class="card"><div class="k">Parallel Fixed</div><div class="v ok">$parallelCount</div></div>
  <div class="card"><div class="k">Sequence Queue</div><div class="v warn">$sequenceCount</div></div>
  <div class="card"><div class="k">Suggest Only</div><div class="v warn">$suggestCount</div></div>
  <div class="card"><div class="k">Verified</div><div class="v ok">$($verified.Count)</div></div>
  <div class="card"><div class="k">Rolled Back</div><div class="v fail">$($rollbacks.Count)</div></div>
  <div class="card"><div class="k">Pre-broken</div><div class="v fail">$brokenBefore</div></div>
</div>

<h2>四大分區（RYG）</h2>
<table><colgroup><col style="width:22%"><col style="width:16%"><col style="width:20%"><col style="width:20%"><col style="width:22%"></colgroup>
<tr><th>Zone</th><th>Files</th><th>Issues</th><th>Rolled Back</th><th>Light</th></tr>
$(New-Rows -Items @($zoneRows) -Fields @('zone','files','issues','rolled','light') -StatusField 'light')</table>

<h2>工具矩陣</h2>
<table><colgroup><col style="width:20%"><col style="width:14%"><col style="width:30%"><col style="width:36%"></colgroup>
<tr><th>Tool</th><th>State</th><th>Path</th><th>Role</th></tr>
$(New-Rows -Items @($tools) -Fields @('tool','state','path','role') -StatusField 'state')</table>

<h2>回滾清單（零脫落保證觸發）</h2>
<p class="lede">修完發現公開介面少了東西或語法壞掉，該檔案已自動還原成修改前的樣子。</p>
<table><colgroup><col style="width:20%"><col style="width:50%"><col style="width:10%"><col style="width:20%"></colgroup>
<tr><th>File</th><th>Reason</th><th>Restored</th><th>Path</th></tr>
$(New-Rows -Items @($rollbacks) -Fields @('name','reason','restored','path'))</table>

<h2>已套用的修正</h2>
<table><colgroup><col style="width:14%"><col style="width:26%"><col style="width:60%"></colgroup>
<tr><th>Tool</th><th>Scope</th><th>Rules</th></tr>
$(New-Rows -Items @($applied) -Fields @('tool','scope','rules'))</table>

<h2>診斷明細</h2>
<table><colgroup><col style="width:9%"><col style="width:9%"><col style="width:16%"><col style="width:6%"><col style="width:14%"><col style="width:46%"></colgroup>
<tr><th>Bucket</th><th>Tool</th><th>File</th><th>Line</th><th>Rule</th><th>Message</th></tr>
$(New-Rows -Items @($diagnostics | Sort-Object -Property @{ e = 'bucket'; desc = $false }, @{ e = 'name'; desc = $false }) -Fields @('bucket','tool','name','line','rule','message') -StatusField 'bucket')</table>

<h2>第 2 輪順序佇列（本輪未修）</h2>
<p class="lede">計畫檔：<code>$(ConvertTo-HtmlText -Text $PlanPath)</code></p>
<table><colgroup><col style="width:14%"><col style="width:20%"><col style="width:6%"><col style="width:60%"></colgroup>
<tr><th>Rule</th><th>File</th><th>Line</th><th>Message</th></tr>
$(New-Rows -Items @($sequenceItems) -Fields @('rule','name','line','message'))</table>

<h2>執行日誌</h2>
<pre>$(ConvertTo-HtmlText -Text ($Script:Log -join "`n"))</pre>
</body></html>
"@

Write-Utf8NoBom -TargetPath $HtmlPath -Text $html

$snapshot = [ordered]@{
    engine = 'VIA_Round1_CodeRepair'; version = 'v0100'; stamp = $Script:Stamp
    mode = $modeText; verdict = $verdict; throttle = $Throttle
    targets = $targets.Count; python = $pyTargets.Count; powershell = $psTargets.Count
    tools = @($tools); zones = @($zoneRows)
    parallel = $parallelCount; sequence = $sequenceCount; suggest = $suggestCount
    pre_broken = $brokenBefore; verified = @($verified); rollbacks = @($rollbacks)
    applied = @($applied); diagnostics = @($diagnostics)
    ruff_remaining_after = $afterDiagCount
    backup = $BackupDir; rollback_script = $RollbackPs; round2_plan = $PlanPath
}
Write-Utf8NoBom -TargetPath $JsonPath -Text ($snapshot | ConvertTo-Json -Depth 7)

Write-Stage -Message ('完成。裁決 ' + $verdict) -Percent 100 -Level $(if ($verdict -eq 'RED') { 'FAIL' } elseif ($verdict -eq 'AMBER') { 'WARN' } else { 'OK' })
Write-Progress -Activity 'VIA Round-1 Code Repair v0100' -Completed

Write-Host ''
Write-Host (' matrix   : ' + $HtmlPath)   -ForegroundColor DarkCyan
Write-Host (' snapshot : ' + $JsonPath)   -ForegroundColor DarkCyan
Write-Host (' round2   : ' + $PlanPath)   -ForegroundColor DarkCyan
Write-Host (' backup   : ' + $BackupDir)  -ForegroundColor DarkCyan
Write-Host (' rollback : ' + $RollbackPs) -ForegroundColor DarkCyan
Write-Host ''
Write-Host '============================================================'
Write-Host (' ROUND 1 COMPLETE  ->  ' + $verdict)
Write-Host (' 並行修 ' + $parallelCount + ' 項｜順序佇列 ' + $sequenceCount + ' 項｜自動回滾 ' + $rollbacks.Count + ' 檔')
Write-Host ' 修壞的一律已還原，不留半殘狀態。'
Write-Host '============================================================'

if (-not $NoBrowser) {
    try { Start-Process -FilePath $HtmlPath | Out-Null } catch { Write-Host ' (browser launch skipped)' -ForegroundColor DarkGray }
}

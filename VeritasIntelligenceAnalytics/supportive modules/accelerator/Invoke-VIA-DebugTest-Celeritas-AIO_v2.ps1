$VIA_AIO_Path = Join-Path $env:TEMP "Invoke-VIA-DebugTest-Celeritas-AIO_v2.ps1"

$VIA_AIO_Code = @'
#requires -Version 7.0
# =============================================================================
#   VIA Debug Test Celeritas AIO v2
#   v2 changes (panorama analysis fix):
#     - Bug#1 : avoid $args automatic variable (rename to $procArgs)
#     - Bug#2 : stricter Invoke-Expression / iex regex
#     - Bug#3 : Stop-Process demoted FAIL -> WARN
#     - Bug#4 : exit demoted FAIL -> WARN
#     - Bug#5 : import_probe default $false (LL#25/26 timeout risk)
#     - Bug#6 : Raw stripped before JSON serialize (smaller report)
#     - Bug#7 : SystemExit(0) reclassified PASS (not WARN)
#     - Bug#8 : preferences saved/restored in Main
#     - Bug#11: Celeritas missing-function gets explicit detail
#   No side effects : static parse / py_compile / optional import probe only
# =============================================================================

# =============================================================================
# def PARAMETERS
# =============================================================================

$def_PARAM_ProjectRoot = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics"
$def_PARAM_ModuleRoot  = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module"
$def_PARAM_VDFRoot     = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF"
$def_PARAM_SupportRoot = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"
$def_PARAM_OutputRoot  = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\_via_debug_test_runs"

$def_PARAM_VenvCandidates = @(
    "C:\Users\tonyk\envs\via_core_312",
    "C:\Users\tonyk\envs\via_core",
    "C:\Users\tonyk\envs\via_vdf",
    "C:\Users\tonyk\envs\via_extract_312",
    "C:\Users\tonyk\envs\via_ml",
    "C:\Users\tonyk\venvs\optimizer_env"
)

$def_PARAM_SupportPyFiles = @(
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_RegistryCore_v1.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Runtime_Bridge_All_in_One.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_Panorama_AST_RuntimeInjector.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
)

$def_PARAM_VDFPyFiles = @(
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\VDF_E0_Registry_v1.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\VDF_E1_DailyFetcher_v1.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\VDF_E2_QuarterlyVerifyFetcher_v1.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\VDF_E3_AKShareFetcher_v1.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\VDF_E4_MacroFetcher_v1.py",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\VDF_E4_MacroFetcher_v2.py"
)

$def_PARAM_PSFiles = @(
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\Invoke-VIA-FinishProject-SafeFast.ps1",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\Invoke-VIA-PanoramaHardGateSafeFix.ps1",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\Invoke-VIA-SupportiveHardGate.ps1",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_ENV_PARTITION_v2.ps1"
)

$def_PARAM_TimeoutSec        = 30
$def_PARAM_ImportTimeoutSec  = 90   # 重型外掛模組 import 用，避免 LL#25/26 timeout
$def_PARAM_EnableImportProbe = $false  # Bug#5: 預設關閉，避免 import 卡死
$def_PARAM_EnableAutoDiscoverVDF = $true
$def_PARAM_OpenHtml = $true

# =============================================================================
# def CORE HELPERS
# =============================================================================

function def_WriteLog {
    param([string]$Level, [string]$Message)

    $ts = (Get-Date).ToString("HH:mm:ss.fff")
    $color = switch ($Level) {
        "PASS" { "Green" }
        "OK"   { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
        "ERR"  { "Red" }
        "INFO" { "Cyan" }
        "SKIP" { "DarkGray" }
        default { "White" }
    }

    Write-Host ("[{0}] [{1}] {2}" -f $ts, $Level, $Message) -ForegroundColor $color
}

function def_EnsureDir {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_HtmlEncode {
    param([object]$Value)

    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_GetPythonExeFromVenv {
    param([string]$VenvPath)

    $p1 = Join-Path $VenvPath "Scripts\python.exe"
    $p2 = Join-Path $VenvPath "python.exe"

    if (Test-Path -LiteralPath $p1) { return $p1 }
    if (Test-Path -LiteralPath $p2) { return $p2 }
    return ""
}

function def_InvokeBoundedProcess {
    param(
        [string]$FileName,
        [string[]]$Arguments,
        [int]$TimeoutSec,
        [string]$WorkingDirectory = ""
    )

    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    $result = [ordered]@{
        Status = "UNKNOWN"
        ExitCode = $null
        Timeout = $false
        DurationSec = 0
        Stdout = ""
        Stderr = ""
    }

    try {
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $FileName

        foreach ($a in $Arguments) {
            [void]$psi.ArgumentList.Add($a)
        }

        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true

        if ($WorkingDirectory -and (Test-Path -LiteralPath $WorkingDirectory)) {
            $psi.WorkingDirectory = $WorkingDirectory
        }

        $proc = [System.Diagnostics.Process]::Start($psi)
        $done = $proc.WaitForExit($TimeoutSec * 1000)

        if (-not $done) {
            $result.Timeout = $true
            $result.Status = "TIMEOUT"
            try { $proc.Kill($true) } catch {}
            try { $proc.WaitForExit(2000) | Out-Null } catch {}
        } else {
            $result.ExitCode = $proc.ExitCode
            if ($proc.ExitCode -eq 0) {
                $result.Status = "PASS"
            } else {
                $result.Status = "WARN"
            }
        }

        $result.Stdout = $proc.StandardOutput.ReadToEnd()
        $result.Stderr = $proc.StandardError.ReadToEnd()
    } catch {
        $result.Status = "FAIL"
        $result.Stderr = $_.Exception.Message
    } finally {
        $sw.Stop()
        $result.DurationSec = [math]::Round($sw.Elapsed.TotalSeconds, 3)
    }

    return [PSCustomObject]$result
}

function def_SelectBestPython {
    foreach ($v in $def_PARAM_VenvCandidates) {
        $py = def_GetPythonExeFromVenv -VenvPath $v
        if ($py -and (Test-Path -LiteralPath $py)) {
            $ver = def_InvokeBoundedProcess -FileName $py -Arguments @("--version") -TimeoutSec 8
            return [PSCustomObject]@{
                PythonExe = $py
                VenvPath = $v
                Version = (($ver.Stdout + " " + $ver.Stderr).Trim())
                Reason = "FIRST_VALID_VENV"
            }
        }
    }

    foreach ($cmd in @("py", "python")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) {
            $ver = def_InvokeBoundedProcess -FileName $found.Source -Arguments @("--version") -TimeoutSec 8
            return [PSCustomObject]@{
                PythonExe = $found.Source
                VenvPath = "SYSTEM"
                Version = (($ver.Stdout + " " + $ver.Stderr).Trim())
                Reason = "SYSTEM_FALLBACK"
            }
        }
    }

    return [PSCustomObject]@{
        PythonExe = ""
        VenvPath = ""
        Version = "NONE"
        Reason = "NO_PYTHON_FOUND"
    }
}

# =============================================================================
# def PYTHON PROBE WRITER
# =============================================================================

function def_WritePythonProbe {
    param([string]$RunDir)

    $probePath = Join-Path $RunDir "VIA_DebugProbe.py"

    # Bug#7 fix: SystemExit(0) -> PASS, otherwise WARN
    $lines = @(
'from __future__ import annotations',
'import argparse, ast, importlib.util, json, py_compile, sys, traceback',
'from pathlib import Path',
'',
'def def_read_text(path_value):',
'    try:',
'        return path_value.read_text(encoding="utf-8")',
'    except UnicodeDecodeError:',
'        return path_value.read_text(encoding="utf-8", errors="replace")',
'',
'def def_extract_ast(path_value):',
'    src = def_read_text(path_value)',
'    tree = ast.parse(src, filename=str(path_value))',
'    funcs = []',
'    classes = []',
'    imports = []',
'    anchors = []',
'    has_main = False',
'    has_dry_run = False',
'    manual_cli_cmds = set()',
'    for node in ast.walk(tree):',
'        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):',
'            funcs.append({"name": node.name, "line": node.lineno})',
'        elif isinstance(node, ast.ClassDef):',
'            classes.append({"name": node.name, "line": node.lineno})',
'        elif isinstance(node, ast.Import):',
'            for n in node.names:',
'                imports.append(n.name.split(".")[0])',
'        elif isinstance(node, ast.ImportFrom):',
'            if node.module:',
'                imports.append(node.module.split(".")[0])',
'        elif isinstance(node, ast.If):',
'            try:',
'                t = ast.unparse(node.test)',
'            except Exception:',
'                t = ""',
'            if "__name__" in t and "__main__" in t:',
'                has_main = True',
'        elif isinstance(node, ast.Call):',
'            fn = ""',
'            if isinstance(node.func, ast.Attribute):',
'                fn = node.func.attr',
'            elif isinstance(node.func, ast.Name):',
'                fn = node.func.id',
'            if fn == "add_argument":',
'                for a in node.args:',
'                    if isinstance(a, ast.Constant) and isinstance(a.value, str):',
'                        if "dry" in a.value.lower() and "run" in a.value.lower():',
'                            has_dry_run = True',
'        elif isinstance(node, ast.Compare):',
'            left_is_cmd_var = isinstance(node.left, ast.Name) and node.left.id in ("command","cmd","action","subcommand","arg")',
'            if left_is_cmd_var and node.ops:',
'                op = node.ops[0]',
'                if isinstance(op, (ast.Eq, ast.In)):',
'                    for cmp_node in node.comparators:',
'                        if isinstance(cmp_node, ast.Constant) and isinstance(cmp_node.value, str):',
'                            manual_cli_cmds.add(cmp_node.value)',
'                        elif isinstance(cmp_node, (ast.List, ast.Tuple)):',
'                            for elt in cmp_node.elts:',
'                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):',
'                                    manual_cli_cmds.add(elt.value)',
'    for i, line in enumerate(src.splitlines(), start=1):',
'        if "ANCHOR[" in line or "[VIA:ANCHOR:" in line or "# [ANC:" in line or "ANC-" in line:',
'            anchors.append(i)',
'    return {',
'        "loc": len(src.splitlines()),',
'        "functions": funcs,',
'        "classes": classes,',
'        "imports": sorted(set(imports)),',
'        "anchor_count": len(anchors),',
'        "has_main_guard": has_main,',
'        "has_dry_run": has_dry_run,',
'        "manual_cli": len(manual_cli_cmds) > 0,',
'        "manual_commands": sorted(list(manual_cli_cmds)),',
'    }',
'',
'def def_compile(path_value):',
'    try:',
'        py_compile.compile(str(path_value), doraise=True)',
'        return {"status": "PASS", "detail": ""}',
'    except Exception as exc:',
'        return {"status": "FAIL", "detail": str(exc), "traceback": traceback.format_exc()}',
'',
'def def_import_probe(path_value, support_root):',
'    try:',
'        parent = str(path_value.parent)',
'        if parent not in sys.path:',
'            sys.path.insert(0, parent)',
'        if support_root and support_root not in sys.path:',
'            sys.path.insert(0, support_root)',
'        mod_name = "via_probe_" + path_value.stem.replace("-", "_").replace(".", "_")',
'        spec = importlib.util.spec_from_file_location(mod_name, str(path_value))',
'        if spec is None or spec.loader is None:',
'            return {"status": "FAIL", "detail": "spec_or_loader_none"}',
'        module = importlib.util.module_from_spec(spec)',
'        spec.loader.exec_module(module)',
'        exports = [x for x in dir(module) if not x.startswith("_")]',
'        return {"status": "PASS", "detail": "import_ok", "exported_count": len(exports)}',
'    except SystemExit as exc:',
'        code = exc.code if isinstance(exc.code, int) else 0 if exc.code is None else 1',
'        if code == 0:',
'            return {"status": "PASS", "detail": "SystemExit(0) during import (likely self-test ok)"}',
'        return {"status": "WARN", "detail": "SystemExit(" + str(code) + ") during import", "traceback": traceback.format_exc()}',
'    except Exception as exc:',
'        return {"status": "FAIL", "detail": str(exc), "traceback": traceback.format_exc()}',
'',
'def def_main():',
'    parser = argparse.ArgumentParser()',
'    parser.add_argument("--file", required=True)',
'    parser.add_argument("--support-root", default="")',
'    parser.add_argument("--import-probe", action="store_true")',
'    parsed_args = parser.parse_args()',
'    p = Path(parsed_args.file)',
'    out = {',
'        "file": str(p), "exists": p.exists(), "kind": "python",',
'        "overall": "UNKNOWN", "blockers": [], "warnings": [],',
'        "ast": {}, "compile": {}, "import_probe": {"status": "SKIP", "detail": ""}',
'    }',
'    if not p.exists():',
'        out["overall"] = "FAIL"',
'        out["blockers"].append("FILE_NOT_FOUND")',
'        print(json.dumps(out, ensure_ascii=False))',
'        return 0',
'    try:',
'        out["ast"] = def_extract_ast(p)',
'    except SyntaxError as exc:',
'        out["overall"] = "FAIL"',
'        out["blockers"].append("AST_SYNTAX_ERROR")',
'        out["ast"] = {"detail": "line %s: %s" % (exc.lineno, exc.msg), "traceback": traceback.format_exc()}',
'        print(json.dumps(out, ensure_ascii=False))',
'        return 0',
'    except Exception as exc:',
'        out["overall"] = "FAIL"',
'        out["blockers"].append("AST_PARSE_FAIL")',
'        out["ast"] = {"detail": str(exc), "traceback": traceback.format_exc()}',
'        print(json.dumps(out, ensure_ascii=False))',
'        return 0',
'    out["compile"] = def_compile(p)',
'    if out["compile"].get("status") != "PASS":',
'        out["blockers"].append("PY_COMPILE_FAIL")',
'    if parsed_args.import_probe:',
'        out["import_probe"] = def_import_probe(p, parsed_args.support_root)',
'        ip_status = out["import_probe"].get("status")',
'        if ip_status == "FAIL":',
'            out["warnings"].append("IMPORT_PROBE_FAIL")',
'        elif ip_status == "WARN":',
'            out["warnings"].append("IMPORT_PROBE_WARN")',
'    if out["blockers"]:',
'        out["overall"] = "FAIL"',
'    elif out["warnings"]:',
'        out["overall"] = "WARN"',
'    else:',
'        out["overall"] = "PASS"',
'    print(json.dumps(out, ensure_ascii=False))',
'    return 0',
'',
'if __name__ == "__main__":',
'    raise SystemExit(def_main())'
    )

    [System.IO.File]::WriteAllLines($probePath, $lines, [System.Text.UTF8Encoding]::new($false))
    return $probePath
}

# =============================================================================
# def TEST FUNCTIONS
# =============================================================================

function def_TestCeleritas {
    param([string]$PythonExe, [string]$RunDir)

    $probePath = Join-Path $RunDir "VIA_CeleritasProbe.py"

    # Bug#11 fix: 對缺失函式給明確 detail
    $lines = @(
'import json, sys, traceback',
'support = r"' + $def_PARAM_SupportRoot + '"',
'if support and support not in sys.path:',
'    sys.path.insert(0, support)',
'out = {"ok": False, "detail": "", "functions": {}, "missing": []}',
'expected = ["cross_init", "get_profile", "detect_libraries", "cross_accelerate", "xjson_dumps", "xjson_loads", "xmap", "xbatch"]',
'try:',
'    import VeritasCeleritas as vc',
'    out["ok"] = True',
'    out["file"] = getattr(vc, "__file__", "")',
'    for fn in expected:',
'        has = hasattr(vc, fn)',
'        out["functions"][fn] = has',
'        if not has:',
'            out["missing"].append(fn)',
'    if out["missing"]:',
'        out["detail"] = "imported_ok_but_missing: " + ", ".join(out["missing"])',
'    else:',
'        out["detail"] = "all_expected_functions_present"',
'except Exception as e:',
'    out["detail"] = "import_failed: " + str(e)',
'    out["traceback"] = traceback.format_exc()',
'print(json.dumps(out, ensure_ascii=False))'
    )

    [System.IO.File]::WriteAllLines($probePath, $lines, [System.Text.UTF8Encoding]::new($false))

    # Celeritas 用較長 timeout（LL#25 已知 import 可能慢）
    $r = def_InvokeBoundedProcess -FileName $PythonExe -Arguments @($probePath) -TimeoutSec $def_PARAM_ImportTimeoutSec -WorkingDirectory $def_PARAM_SupportRoot

    try {
        return ($r.Stdout.Trim() | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        return [PSCustomObject]@{
            ok = $false
            detail = "CELERITAS_JSON_PARSE_FAIL: " + $r.Stderr
            raw = ($r.Stdout + "`n" + $r.Stderr)
        }
    }
}

function def_TestPythonFile {
    param(
        [string]$PythonExe,
        [string]$ProbePath,
        [string]$FilePath,
        [bool]$IsSupportModule = $false
    )

    # Bug#1 fix: 避開 $args 自動變數
    $procArgs = @($ProbePath, "--file", $FilePath, "--support-root", $def_PARAM_SupportRoot)

    if ($def_PARAM_EnableImportProbe) {
        $procArgs += "--import-probe"
    }

    # 支援模組用較長 timeout
    $effectiveTimeout = if ($IsSupportModule) { $def_PARAM_ImportTimeoutSec } else { $def_PARAM_TimeoutSec }

    $run = def_InvokeBoundedProcess -FileName $PythonExe -Arguments $procArgs -TimeoutSec $effectiveTimeout -WorkingDirectory (Split-Path $FilePath -Parent)

    try {
        $parsed = $run.Stdout.Trim() | ConvertFrom-Json -ErrorAction Stop
    } catch {
        $parsed = [PSCustomObject]@{
            overall = "FAIL"
            blockers = @("PROBE_JSON_PARSE_FAIL")
            warnings = @()
            ast = [PSCustomObject]@{
                imports = @()
                functions = @()
                classes = @()
                anchor_count = 0
                has_main_guard = $false
                has_dry_run = $false
                manual_cli = $false
                manual_commands = @()
            }
            compile = [PSCustomObject]@{
                status = "UNKNOWN"
                detail = ""
            }
            import_probe = [PSCustomObject]@{
                status = "UNKNOWN"
                detail = ""
            }
        }
    }

    $funcs = 0
    $classes = 0
    $imports = @()
    $anchorCount = 0
    $hasMain = $false
    $hasDryRun = $false
    $manualCli = $false
    $manualCmds = @()

    try { $funcs = @($parsed.ast.functions).Count } catch {}
    try { $classes = @($parsed.ast.classes).Count } catch {}
    try { $imports = @($parsed.ast.imports) } catch {}
    try { $anchorCount = [int]$parsed.ast.anchor_count } catch {}
    try { $hasMain = [bool]$parsed.ast.has_main_guard } catch {}
    try { $hasDryRun = [bool]$parsed.ast.has_dry_run } catch {}
    try { $manualCli = [bool]$parsed.ast.manual_cli } catch {}
    try { $manualCmds = @($parsed.ast.manual_commands) } catch {}

    return [PSCustomObject]@{
        Kind = "PY"
        Name = [System.IO.Path]::GetFileName($FilePath)
        Path = $FilePath
        Exists = Test-Path -LiteralPath $FilePath
        Overall = [string]$parsed.overall
        DurationSec = $run.DurationSec
        Timeout = $run.Timeout
        Compile = try { [string]$parsed.compile.status } catch { "UNKNOWN" }
        ImportProbe = try { [string]$parsed.import_probe.status } catch { "SKIP" }
        Functions = $funcs
        Classes = $classes
        Imports = ($imports -join ", ")
        AnchorCount = $anchorCount
        HasMain = $hasMain
        HasDryRun = $hasDryRun
        ManualCli = $manualCli
        ManualCommands = ($manualCmds -join ", ")
        Blockers = try { (@($parsed.blockers) -join "; ") } catch { "" }
        Warnings = try { (@($parsed.warnings) -join "; ") } catch { "" }
        Detail = try { [string]$parsed.compile.detail } catch { "" }
        Raw = ($run.Stdout + "`n" + $run.Stderr).Trim()
    }
}

function def_TestPowerShellFile {
    param([string]$FilePath)

    if (-not (Test-Path -LiteralPath $FilePath)) {
        return [PSCustomObject]@{
            Kind = "PS1"
            Name = [System.IO.Path]::GetFileName($FilePath)
            Path = $FilePath
            Exists = $false
            Overall = "FAIL"
            DurationSec = 0
            Timeout = $false
            Compile = "N/A"
            ImportProbe = "N/A"
            Functions = 0
            Classes = 0
            Imports = ""
            AnchorCount = 0
            HasMain = $false
            HasDryRun = $false
            ManualCli = $false
            ManualCommands = ""
            Blockers = "FILE_NOT_FOUND"
            Warnings = ""
            Detail = ""
            Raw = ""
        }
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $tokens = $null
    $errors = $null
    $overall = "PASS"
    $blockers = @()
    $warnings = @()
    $detail = @()
    $funcCount = 0
    $cmdCount = 0

    try {
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($FilePath, [ref]$tokens, [ref]$errors)
        $funcCount = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)).Count
        $cmdCount = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)).Count

        if (@($errors).Count -gt 0) {
            $overall = "FAIL"
            $blockers += "PS_AST_PARSE_FAIL"
            $detail += @($errors | ForEach-Object { "L$($_.Extent.StartLineNumber): $($_.Message)" })
        }

        # Bug#2/3/4 fix: 重新分類危險度
        # FAIL = AST 解析失敗（無法執行）
        # WARN = 高風險但合理使用模式（iex/exit/Stop-Process 都改 WARN）
        $patBlockClose = [string]::Concat('#', ' ', ')')  # 避開字面值 self-lint
        $lines = Get-Content -LiteralPath $FilePath -Encoding UTF8 -ErrorAction SilentlyContinue
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $lineNo = $i + 1
            $line = [string]$lines[$i]

            # 跳過註解
            $trimmed = $line.TrimStart()
            if ($trimmed.StartsWith('#') -and -not $trimmed.StartsWith($patBlockClose)) { continue }

            # Bug#2 fix: 嚴格 Invoke-Expression / iex 偵測
            # 不誤匹 $iex_xxx 變數名
            if ($line -match '(?<![\$\w])Invoke-Expression(?!\w)' -or $line -match '(?<![\$\w])iex(?!\w|-)') {
                if ($overall -eq "PASS") { $overall = "WARN" }
                $warnings += "IEX_USAGE"
                $detail += "L${lineNo} IEX_USAGE"
            }

            # Bug#4 fix: exit 行首改 WARN
            if ($line -match '^\s*exit\b') {
                if ($overall -eq "PASS") { $overall = "WARN" }
                $warnings += "EXIT_USAGE"
                $detail += "L${lineNo} EXIT_USAGE"
            }

            # Bug#3 fix: Stop-Process 改 WARN
            if ($line -match '\bStop-Process\b') {
                if ($overall -eq "PASS") { $overall = "WARN" }
                $warnings += "STOP_PROCESS_USAGE"
                $detail += "L${lineNo} STOP_PROCESS_USAGE"
            }
        }
    } catch {
        $overall = "FAIL"
        $blockers += "PS_PARSE_EXCEPTION"
        $detail += $_.Exception.Message
    }

    $sw.Stop()

    return [PSCustomObject]@{
        Kind = "PS1"
        Name = [System.IO.Path]::GetFileName($FilePath)
        Path = $FilePath
        Exists = $true
        Overall = $overall
        DurationSec = [math]::Round($sw.Elapsed.TotalSeconds, 3)
        Timeout = $false
        Compile = if ($overall -eq "FAIL") { "FAIL" } else { "PASS" }
        ImportProbe = "N/A"
        Functions = $funcCount
        Classes = 0
        Imports = ""
        AnchorCount = 0
        HasMain = $false
        HasDryRun = $false
        ManualCli = $false
        ManualCommands = ""
        Blockers = (($blockers | Select-Object -Unique) -join "; ")
        Warnings = (($warnings | Select-Object -Unique) -join "; ")
        Detail = ($detail -join " | ")
        Raw = ""
    }
}

function def_BuildTargetList {
    $pyList = [System.Collections.Generic.List[string]]::new()
    $psList = [System.Collections.Generic.List[string]]::new()
    $supportSet = [System.Collections.Generic.HashSet[string]]::new()

    foreach ($f in $def_PARAM_SupportPyFiles) {
        if ($f) {
            $pyList.Add($f)
            [void]$supportSet.Add($f)
        }
    }

    foreach ($f in $def_PARAM_VDFPyFiles) {
        if ($f) { $pyList.Add($f) }
    }

    if ($def_PARAM_EnableAutoDiscoverVDF -and (Test-Path -LiteralPath $def_PARAM_VDFRoot)) {
        Get-ChildItem -LiteralPath $def_PARAM_VDFRoot -Filter "*.py" -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "\\__pycache__\\" } |
            ForEach-Object { $pyList.Add($_.FullName) }
    }

    foreach ($f in $def_PARAM_PSFiles) {
        if ($f) { $psList.Add($f) }
    }

    return [PSCustomObject]@{
        Py = @($pyList | Select-Object -Unique)
        PS = @($psList | Select-Object -Unique)
        SupportSet = $supportSet
    }
}

# =============================================================================
# def REPORT
# =============================================================================

function def_GetBadge {
    param([string]$Status)

    $cls = switch ($Status) {
        "PASS" { "ok" }
        "OK" { "ok" }
        "WARN" { "warn" }
        "FAIL" { "fail" }
        "TIMEOUT" { "fail" }
        default { "skip" }
    }

    return "<span class='badge $cls'>$(def_HtmlEncode $Status)</span>"
}

function def_WriteReports {
    param(
        [array]$Rows,
        [object]$PyInfo,
        [object]$Celeritas,
        [string]$RunDir
    )

    def_EnsureDir -Path $RunDir

    $jsonPath = Join-Path $RunDir "VIA_DebugTest_Result.json"
    $csvPath  = Join-Path $RunDir "VIA_DebugTest_Result.csv"
    $htmlPath = Join-Path $RunDir "VIA_DebugTest_Report.html"

    $total = @($Rows).Count
    $pass = @($Rows | Where-Object { $_.Overall -eq "PASS" }).Count
    $warn = @($Rows | Where-Object { $_.Overall -eq "WARN" }).Count
    $fail = @($Rows | Where-Object { $_.Overall -eq "FAIL" }).Count
    $timeout = @($Rows | Where-Object { $_.Timeout -eq $true }).Count

    # Bug#6 fix: JSON 序列化前 strip Raw 大欄位（避免報告檔肥大）
    $rowsForJson = $Rows | ForEach-Object {
        $clone = [ordered]@{}
        foreach ($prop in $_.PSObject.Properties) {
            if ($prop.Name -ne "Raw") {
                $clone[$prop.Name] = $prop.Value
            } else {
                # Raw 截斷為前 500 字
                $rawVal = [string]$prop.Value
                if ($rawVal.Length -gt 500) {
                    $clone["RawSnippet"] = $rawVal.Substring(0, 500) + "...(truncated)"
                } else {
                    $clone["RawSnippet"] = $rawVal
                }
            }
        }
        [PSCustomObject]$clone
    }

    $payload = [ordered]@{
        generated_at = (Get-Date).ToString("s")
        run_dir = $RunDir
        python = $PyInfo
        celeritas = $Celeritas
        summary = [ordered]@{
            total = $total
            pass = $pass
            warn = $warn
            fail = $fail
            timeout = $timeout
        }
        rows = $rowsForJson
    }

    $payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
    $Rows | Select-Object * -ExcludeProperty Raw | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8BOM

    $rowHtml = ""
    foreach ($r in $Rows) {
        $rowClass = "skip"
        if ($r.Overall) { $rowClass = $r.Overall.ToLower() }

        $rowHtml += "<tr class='$rowClass'>"
        $rowHtml += "<td>$(def_HtmlEncode $r.Kind)</td>"
        $rowHtml += "<td><b>$(def_HtmlEncode $r.Name)</b><div class='path'>$(def_HtmlEncode $r.Path)</div></td>"
        $rowHtml += "<td>$(def_GetBadge $r.Overall)</td>"
        $rowHtml += "<td>$(def_HtmlEncode $r.DurationSec)</td>"
        $rowHtml += "<td>$(def_GetBadge $r.Compile)</td>"
        $rowHtml += "<td>$(def_GetBadge $r.ImportProbe)</td>"
        $rowHtml += "<td>$(def_HtmlEncode $r.Functions)</td>"
        $rowHtml += "<td>$(def_HtmlEncode $r.Classes)</td>"
        $rowHtml += "<td>$(def_HtmlEncode $r.AnchorCount)</td>"
        $rowHtml += "<td>$(def_HtmlEncode $r.HasMain)</td>"
        $rowHtml += "<td>$(def_HtmlEncode $r.HasDryRun)</td>"
        $rowHtml += "<td>$(def_HtmlEncode $r.ManualCli)</td>"
        $rowHtml += "<td class='small'>$(def_HtmlEncode $r.ManualCommands)</td>"
        $rowHtml += "<td class='small'>$(def_HtmlEncode $r.Blockers)</td>"
        $rowHtml += "<td class='small'>$(def_HtmlEncode $r.Warnings)</td>"
        $rowHtml += "<td class='small'>$(def_HtmlEncode $r.Detail)</td>"
        $rowHtml += "</tr>"
    }

    $celeritasOk = $false
    try { $celeritasOk = [bool]$Celeritas.ok } catch {}

    $celeritasDetail = ""
    try { $celeritasDetail = [string]$Celeritas.detail } catch {}

    $html = @"
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Debug Test Celeritas Report v2</title>
<style>
:root{--bg:#f5f4f0;--card:#fff;--line:#d8d5ce;--text:#24231f;--muted:#6f6b62;--ok:#2f8f55;--warn:#b7791f;--fail:#c53030;--skip:#718096;--blue:#356f9f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI",Arial,sans-serif;font-size:13px}
.wrap{max-width:1680px;margin:0 auto;padding:16px}
.header{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin-bottom:12px}
h1{margin:0;font-size:24px;letter-spacing:-.5px}
.sub{color:var(--muted);margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:12px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}
.kpi .n{font-size:24px;font-weight:800}
.kpi .l{font-size:11px;color:var(--muted);text-transform:uppercase}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin:10px 0}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:12px}
th{position:sticky;top:0;background:#ebe8df;border:1px solid var(--line);padding:8px;text-align:left;z-index:2}
td{border:1px solid var(--line);padding:7px;vertical-align:top}
tr.fail{background:#fff5f5}
tr.warn{background:#fffaf0}
tr.pass{background:#f0fff4}
.badge{display:inline-block;border-radius:999px;padding:2px 8px;font-weight:700;font-size:11px}
.badge.ok{background:#dcfce7;color:var(--ok)}
.badge.warn{background:#fef3c7;color:var(--warn)}
.badge.fail{background:#fee2e2;color:var(--fail)}
.badge.skip{background:#edf2f7;color:var(--skip)}
.path{font-family:Consolas,monospace;font-size:10px;color:var(--muted);margin-top:2px}
.small{font-size:11px;color:#3f3b36;max-width:320px;word-break:break-word}
.scroll{max-height:72vh;overflow:auto;border:1px solid var(--line);border-radius:12px}
.code{font-family:Consolas,monospace;background:#f7fafc;border:1px solid var(--line);border-radius:10px;padding:10px;white-space:pre-wrap;font-size:11px}
.fix-note{background:#eef6ff;border-left:4px solid var(--blue);padding:10px 12px;margin:8px 0;border-radius:6px}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>VIA Debug Test Celeritas Report v2</h1>
    <div class="sub">VERITAS INTELLIGENCE ANALYTICS · Panorama Analysis · Generated $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</div>
  </div>

  <div class="grid">
    <div class="kpi"><div class="n">$total</div><div class="l">Total</div></div>
    <div class="kpi"><div class="n" style="color:var(--ok)">$pass</div><div class="l">Pass</div></div>
    <div class="kpi"><div class="n" style="color:var(--warn)">$warn</div><div class="l">Warn</div></div>
    <div class="kpi"><div class="n" style="color:var(--fail)">$fail</div><div class="l">Fail</div></div>
    <div class="kpi"><div class="n" style="color:var(--fail)">$timeout</div><div class="l">Timeout</div></div>
    <div class="kpi"><div class="n" style="color:var(--blue)">$celeritasOk</div><div class="l">Celeritas</div></div>
  </div>

  <div class="card">
    <h2>v2 修補摘要</h2>
    <div class="fix-note">
      Bug#1 `$args` -> `$procArgs`  |
      Bug#2 嚴格 iex regex (不誤匹 `$iex_xxx`)  |
      Bug#3 Stop-Process FAIL -> WARN  |
      Bug#4 exit FAIL -> WARN  |
      Bug#5 import_probe 預設關閉 + 支援模組 90s timeout  |
      Bug#6 JSON Raw 大欄位截斷  |
      Bug#7 SystemExit(0) -> PASS  |
      Bug#11 Celeritas 缺失函式明確 detail
    </div>
  </div>

  <div class="card">
    <h2>Runtime</h2>
    <div class="code">Python: $(def_HtmlEncode $PyInfo.PythonExe)
Venv: $(def_HtmlEncode $PyInfo.VenvPath)
Version: $(def_HtmlEncode $PyInfo.Version)
Reason: $(def_HtmlEncode $PyInfo.Reason)
RunDir: $(def_HtmlEncode $RunDir)
Celeritas OK: $(def_HtmlEncode $celeritasOk)
Celeritas Detail: $(def_HtmlEncode $celeritasDetail)
JSON: $(def_HtmlEncode $jsonPath)
CSV: $(def_HtmlEncode $csvPath)
Import Probe Default: DISABLED (set EnableImportProbe=true to enable)</div>
  </div>

  <div class="card">
    <h2>Next Three Processes</h2>
    <ol>
      <li><b>錯誤定位：</b>先看 FAIL / TIMEOUT / PS_AST_PARSE_FAIL。</li>
      <li><b>精準錨點修復：</b>只針對 blocker 產生 patch plan，不直接破壞原檔。</li>
      <li><b>再測封印：</b>重新跑本腳本，直到 FAIL=0、TIMEOUT=0。</li>
    </ol>
  </div>

  <div class="card">
    <h2>Detailed Matrix</h2>
    <div class="scroll">
      <table>
        <thead>
          <tr>
            <th>Kind</th><th>File</th><th>Overall</th><th>Sec</th><th>Compile/Parse</th><th>Import</th>
            <th>Def</th><th>Class</th><th>Anc</th><th>Main</th><th>DryRun</th><th>ManualCLI</th><th>Cmds</th>
            <th>Blockers</th><th>Warnings</th><th>Detail</th>
          </tr>
        </thead>
        <tbody>$rowHtml</tbody>
      </table>
    </div>
  </div>
</div>
</body>
</html>
"@

    [System.IO.File]::WriteAllText($htmlPath, $html, [System.Text.UTF8Encoding]::new($false))

    return [PSCustomObject]@{
        Json = $jsonPath
        Csv = $csvPath
        Html = $htmlPath
    }
}

# =============================================================================
# def MAIN
# =============================================================================

function def_Main {
    # Bug#8 fix: 保存原 preferences，最後還原
    $origEAP = $ErrorActionPreference
    $origPP  = $ProgressPreference
    $ErrorActionPreference = "Continue"
    $ProgressPreference = "SilentlyContinue"

    try {
        def_WriteLog "INFO" "VIA Debug Test Celeritas AIO v2 啟動"
        def_EnsureDir -Path $def_PARAM_OutputRoot

        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $runDir = Join-Path $def_PARAM_OutputRoot ("VIA_DEBUG_TEST_CELERITAS_{0}" -f $stamp)
        def_EnsureDir -Path $runDir

        def_WriteLog "INFO" "RunDir = $runDir"
        def_WriteLog "INFO" ("ImportProbe = " + $def_PARAM_EnableImportProbe + " (set `$def_PARAM_EnableImportProbe=`$true to enable)")

        $pyInfo = def_SelectBestPython

        if ($pyInfo.PythonExe) {
            def_WriteLog "PASS" "Python = $($pyInfo.PythonExe) · $($pyInfo.Version)"
        } else {
            def_WriteLog "FAIL" "找不到 Python；Python 檔案會標為 NO_PYTHON"
        }

        $probePath = ""
        $celeritas = [PSCustomObject]@{ ok = $false; detail = "NO_PYTHON" }

        if ($pyInfo.PythonExe) {
            $probePath = def_WritePythonProbe -RunDir $runDir
            def_WriteLog "OK" "Probe = $probePath"

            def_WriteLog "INFO" "測試 VeritasCeleritas 加速器（${def_PARAM_ImportTimeoutSec}s timeout）"
            $celeritas = def_TestCeleritas -PythonExe $pyInfo.PythonExe -RunDir $runDir

            if ($celeritas.ok) {
                def_WriteLog "PASS" "Celeritas import OK: $($celeritas.detail)"
            } else {
                def_WriteLog "WARN" "Celeritas not ready: $($celeritas.detail)"
            }
        }

        $targets = def_BuildTargetList
        def_WriteLog "INFO" "Python targets = $(@($targets.Py).Count), PS targets = $(@($targets.PS).Count)"

        $rows = [System.Collections.Generic.List[object]]::new()

        foreach ($pyFile in $targets.Py) {
            if ($pyInfo.PythonExe -and $probePath) {
                $isSupport = $targets.SupportSet.Contains($pyFile)
                $marker = if ($isSupport) { "[SUPPORT]" } else { "[VDF]" }
                def_WriteLog "INFO" "PY TEST $marker $pyFile"
                $rows.Add((def_TestPythonFile -PythonExe $pyInfo.PythonExe -ProbePath $probePath -FilePath $pyFile -IsSupportModule $isSupport))
            } else {
                $rows.Add([PSCustomObject]@{
                    Kind = "PY"
                    Name = [System.IO.Path]::GetFileName($pyFile)
                    Path = $pyFile
                    Exists = Test-Path -LiteralPath $pyFile
                    Overall = "FAIL"
                    DurationSec = 0
                    Timeout = $false
                    Compile = "SKIP"
                    ImportProbe = "SKIP"
                    Functions = 0
                    Classes = 0
                    Imports = ""
                    AnchorCount = 0
                    HasMain = $false
                    HasDryRun = $false
                    ManualCli = $false
                    ManualCommands = ""
                    Blockers = "NO_PYTHON"
                    Warnings = ""
                    Detail = ""
                    Raw = ""
                })
            }
        }

        foreach ($psFile in $targets.PS) {
            def_WriteLog "INFO" "PS1 TEST: $psFile"
            $rows.Add((def_TestPowerShellFile -FilePath $psFile))
        }

        $reports = def_WriteReports -Rows @($rows) -PyInfo $pyInfo -Celeritas $celeritas -RunDir $runDir

        $pass = @($rows | Where-Object { $_.Overall -eq "PASS" }).Count
        $warn = @($rows | Where-Object { $_.Overall -eq "WARN" }).Count
        $fail = @($rows | Where-Object { $_.Overall -eq "FAIL" }).Count
        $timeout = @($rows | Where-Object { $_.Timeout -eq $true }).Count

        Write-Host ""
        def_WriteLog "INFO" "================ RESULT ================"
        def_WriteLog "PASS" "PASS=$pass"

        if ($warn -gt 0) {
            def_WriteLog "WARN" "WARN=$warn"
        } else {
            def_WriteLog "OK" "WARN=0"
        }

        if ($fail -gt 0) {
            def_WriteLog "FAIL" "FAIL=$fail"
        } else {
            def_WriteLog "OK" "FAIL=0"
        }

        if ($timeout -gt 0) {
            def_WriteLog "FAIL" "TIMEOUT=$timeout"
        } else {
            def_WriteLog "OK" "TIMEOUT=0"
        }

        def_WriteLog "INFO" "HTML = $($reports.Html)"
        def_WriteLog "INFO" "JSON = $($reports.Json)"
        def_WriteLog "INFO" "CSV  = $($reports.Csv)"

        if ($def_PARAM_OpenHtml -and (Test-Path -LiteralPath $reports.Html)) {
            Start-Process $reports.Html
        }

        Write-Host ""
        Write-Host "PowerShell session remains open." -ForegroundColor Cyan
    }
    finally {
        # Bug#8 fix: 還原 preferences
        $ErrorActionPreference = $origEAP
        $ProgressPreference = $origPP
    }
}

# =============================================================================
# def RUN
# =============================================================================

try {
    def_Main
} catch {
    def_WriteLog "ERR" ("未預期錯誤: " + $_.Exception.Message)

    if ($_.ScriptStackTrace) {
        Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    }

    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}
'@

Set-Content -LiteralPath $VIA_AIO_Path -Value $VIA_AIO_Code -Encoding UTF8

Write-Host "[OK] AIO v2 script written:" $VIA_AIO_Path -ForegroundColor Green
Write-Host "[RUN] Executing..." -ForegroundColor Cyan

& $VIA_AIO_Path

Write-Host ""
Write-Host "[DONE] PowerShell session remains open." -ForegroundColor Cyan

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

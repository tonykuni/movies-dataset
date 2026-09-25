#Requires -Version 7.0
<#
.SYNOPSIS
  VIA Final xbatch Hard Shim + 100% Symbol Coverage Re-Test
.DESCRIPTION
  最後一個毛點修復：只補 VeritasCeleritas.py 的 xbatch。
  備份、EOF 全域 shim、清 __pycache__、新 process import smoke、HTML/JSON/CSV。
#>

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
$ErrorActionPreference = "Stop"

# ══════════════════════════════════════════════════════════════════════════════
# def PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

$script:CFG = [ordered]@{
    SupportiveRoot = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"
    OutputRoot     = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\_via_governance_runs"
    TargetFile     = "VeritasCeleritas.py"
    PythonCandidates = @(
        "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
        "C:\Python313\python.exe",
        "python"
    )
    OpenHtml = $true
}

$script:STATE = [ordered]@{
    RunId       = ""
    RunDir      = ""
    BackupDir   = ""
    Python      = ""
    PatchPy     = ""
    JsonPath    = ""
    CsvPath     = ""
    HtmlPath    = ""
    SummaryPath = ""
}

# ══════════════════════════════════════════════════════════════════════════════
# def LOG
# ══════════════════════════════════════════════════════════════════════════════

function def_Write-Line {
    param([string]$Message, [string]$Color = "Gray")
    Write-Host $Message -ForegroundColor $Color
}

function def_Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host ("═" * 96) -ForegroundColor DarkCyan
    Write-Host ("  " + $Message) -ForegroundColor Cyan
    Write-Host ("═" * 96) -ForegroundColor DarkCyan
}

# ══════════════════════════════════════════════════════════════════════════════
# def LAYOUT / PYTHON
# ══════════════════════════════════════════════════════════════════════════════

function def_New-RunLayout {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $script:STATE.RunId = "VIA_FINAL_XBATCH_FIX_$stamp"
    $script:STATE.RunDir = Join-Path $script:CFG.OutputRoot $script:STATE.RunId
    $script:STATE.BackupDir = Join-Path $script:STATE.RunDir "_backup"
    New-Item -ItemType Directory -Force -Path $script:STATE.RunDir | Out-Null
    New-Item -ItemType Directory -Force -Path $script:STATE.BackupDir | Out-Null

    $script:STATE.PatchPy = Join-Path $script:STATE.RunDir "via_final_xbatch_fix.py"
    $script:STATE.JsonPath = Join-Path $script:STATE.RunDir "final_xbatch_result.json"
    $script:STATE.CsvPath = Join-Path $script:STATE.RunDir "final_xbatch_result.csv"
    $script:STATE.HtmlPath = Join-Path $script:STATE.RunDir "final_xbatch_result.html"
    $script:STATE.SummaryPath = Join-Path $script:STATE.RunDir "final_xbatch_summary.json"

    def_Write-Line "[OK] RunDir = $($script:STATE.RunDir)" Green
}

function def_Find-Python {
    foreach ($candidate in $script:CFG.PythonCandidates) {
        try {
            if ($candidate -eq "python") {
                $cmd = Get-Command python -ErrorAction SilentlyContinue
                if ($null -ne $cmd) {
                    $script:STATE.Python = $cmd.Source
                    return
                }
            } elseif (Test-Path -LiteralPath $candidate) {
                $script:STATE.Python = $candidate
                return
            }
        } catch {}
    }
    throw "Python not found."
}

function def_Backup-Target {
    $src = Join-Path $script:CFG.SupportiveRoot $script:CFG.TargetFile
    if (-not (Test-Path -LiteralPath $src)) {
        throw "Target missing: $src"
    }
    Copy-Item -LiteralPath $src -Destination (Join-Path $script:STATE.BackupDir $script:CFG.TargetFile) -Force
    def_Write-Line "[OK] Backup = $(Join-Path $script:STATE.BackupDir $script:CFG.TargetFile)" Green
}

# ══════════════════════════════════════════════════════════════════════════════
# def PATCHER
# ══════════════════════════════════════════════════════════════════════════════

function def_Write-PatcherPython {
    $code = @'
from __future__ import annotations

import ast
import csv
import html
import importlib
import json
import py_compile
import shutil
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime

# def PARAMETERS
def_PARAM_SUPPORTIVE_ROOT = Path(r"__SUPPORTIVE_ROOT__")
def_PARAM_TARGET = def_PARAM_SUPPORTIVE_ROOT / "VeritasCeleritas.py"
def_PARAM_JSON_PATH = Path(r"__JSON_PATH__")
def_PARAM_CSV_PATH = Path(r"__CSV_PATH__")
def_PARAM_HTML_PATH = Path(r"__HTML_PATH__")
def_PARAM_SUMMARY_PATH = Path(r"__SUMMARY_PATH__")
def_PARAM_FINAL_TAG_START = "# ===== [VIA:ANCHOR:PATCH:XBATCH-FINAL-GLOBAL-SHIM-20260506:START] ====="

# def HELPERS
def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_read(path_value: Path) -> str:
    try:
        return path_value.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path_value.read_text(encoding="utf-8", errors="replace")


def def_write(path_value: Path, text: str) -> None:
    path_value.write_text(text, encoding="utf-8")


def def_clean_pycache() -> list[str]:
    removed = []
    for p in def_PARAM_SUPPORTIVE_ROOT.rglob("__pycache__"):
        try:
            shutil.rmtree(p)
            removed.append(str(p))
        except Exception:
            pass
    return removed


def def_compile_target() -> dict:
    try:
        source = def_read(def_PARAM_TARGET)
        ast.parse(source, filename=str(def_PARAM_TARGET))
        py_compile.compile(str(def_PARAM_TARGET), doraise=True)
        return {"ok": True, "detail": "AST_COMPILE_OK"}
    except Exception as exc:
        return {"ok": False, "detail": str(exc), "traceback": traceback.format_exc()}


def def_patch_xbatch_final() -> dict:
    if not def_PARAM_TARGET.exists():
        return {"ok": False, "patched": False, "reason": "TARGET_MISSING", "target": str(def_PARAM_TARGET)}

    text = def_read(def_PARAM_TARGET)
    already = def_PARAM_FINAL_TAG_START in text

    patch = r'''

# ===== [VIA:ANCHOR:PATCH:XBATCH-FINAL-GLOBAL-SHIM-20260506:START] =====
# Final hard global shim. Appended at EOF so xbatch exists in module globals.
def xbatch(items, batch_size=20):
    """
    VIA final compatibility shim.
    Returns list-of-batches and never raises on normal iterable input.
    """
    try:
        if items is None:
            return []
        try:
            bs = int(batch_size)
        except Exception:
            bs = 20
        if bs <= 0:
            bs = 20
        if isinstance(items, list):
            seq = items
        else:
            seq = list(items)
        return [seq[i:i + bs] for i in range(0, len(seq), bs)]
    except Exception:
        try:
            return [list(items)]
        except Exception:
            return []

try:
    __all__
except Exception:
    __all__ = []
try:
    if "xbatch" not in __all__:
        __all__.append("xbatch")
except Exception:
    pass
try:
    globals()["xbatch"] = xbatch
except Exception:
    pass
# ===== [VIA:ANCHOR:PATCH:XBATCH-FINAL-GLOBAL-SHIM-20260506:END] =====
'''
    if not already:
        def_write(def_PARAM_TARGET, text.rstrip() + "\n" + patch + "\n")

    check = def_compile_target()
    return {
        "ok": check["ok"],
        "patched": not already,
        "reason": "PATCHED" if not already else "ALREADY_PATCHED",
        "compile": check,
        "target": str(def_PARAM_TARGET),
    }


def def_import_smoke() -> dict:
    started = time.perf_counter()
    if str(def_PARAM_SUPPORTIVE_ROOT) not in sys.path:
        sys.path.insert(0, str(def_PARAM_SUPPORTIVE_ROOT))
    try:
        sys.modules.pop("VeritasCeleritas", None)
        mod = importlib.import_module("VeritasCeleritas")
        has = hasattr(mod, "xbatch")
        smoke = None
        smoke_ok = False
        if has:
            smoke = mod.xbatch([1, 2, 3, 4, 5], batch_size=2)
            smoke_ok = smoke == [[1, 2], [3, 4], [5]]
        symbols = ["thread_budget", "thread_budget_cross", "apply_vrn_vds_max_accel", "cross_init", "xmap", "xbatch"]
        found = [s for s in symbols if hasattr(mod, s)]
        missing = [s for s in symbols if not hasattr(mod, s)]
        return {
            "ok": has and smoke_ok and len(missing) == 0,
            "import_ok": True,
            "has_xbatch": has,
            "smoke_ok": smoke_ok,
            "smoke_result": smoke,
            "symbols_found": len(found),
            "symbols_total": len(symbols),
            "missing_symbols": missing,
            "module_file": getattr(mod, "__file__", ""),
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:
        return {
            "ok": False,
            "import_ok": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
        }


def def_write_outputs(payload: dict) -> None:
    smoke = payload.get("smoke", {})
    total = int(smoke.get("symbols_total", 6) or 6)
    found = int(smoke.get("symbols_found", 0) or 0)
    summary = {
        "ok": bool(smoke.get("ok")),
        "generated_at": def_now(),
        "target": str(def_PARAM_TARGET),
        "supportive_root": str(def_PARAM_SUPPORTIVE_ROOT),
        "patch_ok": bool(payload.get("patch", {}).get("ok")),
        "import_ok": bool(smoke.get("import_ok")),
        "has_xbatch": bool(smoke.get("has_xbatch")),
        "smoke_ok": bool(smoke.get("smoke_ok")),
        "symbols": f"{found}/{total}",
        "symbol_coverage": int(round(100 * found / max(1, total))),
        "missing_symbols": smoke.get("missing_symbols", []),
        "pycache_removed": payload.get("pycache_removed", []),
    }

    def_PARAM_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    def_PARAM_JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    def_PARAM_SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    with def_PARAM_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        row = dict(summary)
        row["missing_symbols"] = ";".join(row.get("missing_symbols") or [])
        row["pycache_removed"] = ";".join(row.get("pycache_removed") or [])
        writer.writerow(row)

    ok_cls = "ok" if summary["ok"] else "bad"
    ok_text = "PASS 100%" if summary["ok"] else "NEEDS DEBUG"
    html_doc = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA Final xbatch Fix</title><style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--coral:#c96b5a;--amber:#c4943a}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1200px;margin:0 auto;padding:14px}}.hero{{background:var(--sf);border:1px solid var(--bd);border-radius:14px;box-shadow:0 12px 35px rgba(30,29,26,.08);overflow:hidden;margin-bottom:10px}}.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--amber),var(--coral))}}.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}}.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--blue);border-radius:10px;padding:10px}}.kpi.ok{{border-left-color:var(--green)}}.kpi.bad{{border-left-color:var(--coral)}}.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:22px;font-weight:900}}.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-top:10px}}.ok{{color:var(--green);font-weight:900}}.bad{{color:var(--coral);font-weight:900}}code{{font-family:Consolas,monospace;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:2px 5px}}pre{{background:#1e1d1a;color:#f5f4f0;border-radius:10px;padding:10px;overflow:auto;font-size:11px}}.progress{{height:7px;background:#e3e0d8;border-radius:99px;overflow:hidden;margin-top:8px}}.bar{{height:100%;width:{summary['symbol_coverage']}%;background:linear-gradient(90deg,var(--blue),var(--teal),var(--green));animation:load 1s ease-out}}@keyframes load{{from{{width:0}}}}
</style></head><body><div class="wrap"><div class="hero"><div class="heroIn"><div><h1>VIA Final xbatch Hard Shim</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS · Final Test Debug User-Test Debug</div><div class="sub">Generated: {html.escape(summary['generated_at'])}</div></div><div class="{ok_cls}" style="font-size:20px">{ok_text}</div></div></div>
<div class="grid"><div class="kpi {'ok' if summary['patch_ok'] else 'bad'}"><div class="k">Patch</div><div class="v">{summary['patch_ok']}</div></div><div class="kpi {'ok' if summary['import_ok'] else 'bad'}"><div class="k">Import</div><div class="v">{summary['import_ok']}</div></div><div class="kpi {'ok' if summary['has_xbatch'] else 'bad'}"><div class="k">Has xbatch</div><div class="v">{summary['has_xbatch']}</div></div><div class="kpi {'ok' if summary['smoke_ok'] else 'bad'}"><div class="k">Smoke</div><div class="v">{summary['smoke_ok']}</div></div><div class="kpi {'ok' if summary['symbol_coverage']==100 else 'bad'}"><div class="k">Symbols</div><div class="v">{summary['symbols']}</div></div></div>
<div class="card"><b>Symbol Coverage</b><div class="progress"><div class="bar"></div></div></div><div class="card"><b>Target</b><br><code>{html.escape(summary['target'])}</code></div><div class="card"><b>Missing Symbols</b><pre>{html.escape(json.dumps(summary['missing_symbols'], ensure_ascii=False, indent=2))}</pre></div><div class="card"><b>Full Result</b><pre>{html.escape(json.dumps(payload, ensure_ascii=False, indent=2, default=str))}</pre></div></div></body></html>"""
    def_PARAM_HTML_PATH.write_text(html_doc, encoding="utf-8")


# def MAIN
def def_main() -> int:
    payload = {
        "generated_at": def_now(),
        "target": str(def_PARAM_TARGET),
        "patch": def_patch_xbatch_final(),
        "pycache_removed": def_clean_pycache(),
    }
    payload["smoke"] = def_import_smoke()
    def_write_outputs(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    def_main()
'@
    $code = $code.Replace("__SUPPORTIVE_ROOT__", ($script:CFG.SupportiveRoot -replace "\\", "\\"))
    $code = $code.Replace("__JSON_PATH__", ($script:STATE.JsonPath -replace "\\", "\\"))
    $code = $code.Replace("__CSV_PATH__", ($script:STATE.CsvPath -replace "\\", "\\"))
    $code = $code.Replace("__HTML_PATH__", ($script:STATE.HtmlPath -replace "\\", "\\"))
    $code = $code.Replace("__SUMMARY_PATH__", ($script:STATE.SummaryPath -replace "\\", "\\"))
    Set-Content -LiteralPath $script:STATE.PatchPy -Value $code -Encoding UTF8
    def_Write-Line "[OK] PatchPy = $($script:STATE.PatchPy)" Green
}

# ══════════════════════════════════════════════════════════════════════════════
# def EXECUTE
# ══════════════════════════════════════════════════════════════════════════════

function def_Invoke-FinalFix {
    def_Write-Step "Apply Final xbatch Shim + Clean Cache + Smoke Test"
    $out = & $script:STATE.Python $script:STATE.PatchPy 2>&1
    Write-Host ($out | Out-String)
    if (-not (Test-Path -LiteralPath $script:STATE.SummaryPath)) {
        throw "Summary not generated: $($script:STATE.SummaryPath)"
    }
    return Get-Content -LiteralPath $script:STATE.SummaryPath -Raw -Encoding UTF8 | ConvertFrom-Json
}

function def_Show-Final {
    param([object]$Summary)
    def_Write-Step "FINAL SUMMARY"
    $c = if ($Summary.ok) { "Green" } else { "Yellow" }
    def_Write-Line ("OK              = " + $Summary.ok) $c
    def_Write-Line ("Patch OK        = " + $Summary.patch_ok) $c
    def_Write-Line ("Import OK       = " + $Summary.import_ok) $c
    def_Write-Line ("Has xbatch      = " + $Summary.has_xbatch) $c
    def_Write-Line ("Smoke OK        = " + $Summary.smoke_ok) $c
    def_Write-Line ("Symbols         = " + $Summary.symbols) $c
    def_Write-Line ("Symbol Coverage = " + $Summary.symbol_coverage + "%") $c
    def_Write-Line ("Backup          = " + $script:STATE.BackupDir) Green
    def_Write-Line ("HTML            = " + $script:STATE.HtmlPath) Green
    def_Write-Line ("JSON            = " + $script:STATE.JsonPath) Green
    def_Write-Line ("CSV             = " + $script:STATE.CsvPath) Green
    if ($script:CFG.OpenHtml -and (Test-Path -LiteralPath $script:STATE.HtmlPath)) {
        Start-Process $script:STATE.HtmlPath
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# def MAIN
# ══════════════════════════════════════════════════════════════════════════════

function Invoke-VIAFinalXbatchFix {
    try {
        def_Write-Step "VIA FINAL XBATCH FIX"
        def_New-RunLayout
        def_Write-Step "Find Python"
        def_Find-Python
        def_Write-Line "[OK] Python = $($script:STATE.Python)" Green
        try { def_Write-Line ("     " + ((& $script:STATE.Python --version 2>&1) | Out-String).Trim()) DarkGray } catch {}
        def_Write-Step "Backup"
        def_Backup-Target
        def_Write-Step "Generate Final Patcher"
        def_Write-PatcherPython
        $summary = def_Invoke-FinalFix
        def_Show-Final -Summary $summary
        return [pscustomobject]@{
            Ok = $summary.ok
            SymbolCoverage = $summary.symbol_coverage
            HasXbatch = $summary.has_xbatch
            SmokeOk = $summary.smoke_ok
            RunDir = $script:STATE.RunDir
            BackupDir = $script:STATE.BackupDir
            HtmlPath = $script:STATE.HtmlPath
            JsonPath = $script:STATE.JsonPath
            CsvPath = $script:STATE.CsvPath
        }
    }
    catch {
        Write-Host ""
        def_Write-Line ("[ERR] " + $_.Exception.Message) Red
        if ($_.ScriptStackTrace) { def_Write-Line $_.ScriptStackTrace DarkRed }
        return [pscustomobject]@{
            Ok = $false
            Error = $_.Exception.Message
            RunDir = $script:STATE.RunDir
            BackupDir = $script:STATE.BackupDir
        }
    }
}

# def RUN
Invoke-VIAFinalXbatchFix


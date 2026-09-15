#requires -Version 7.0
<#
Start-VIA-VDF-v0104 · 一鍵：加速器導入 + VDF 網路工具 + 工作台啟動
================================================================
功能只增不減。預設 Preview 盤點後啟動 v0160C 工作台。
-Apply     才寫入 py 錨點（自動備份）
-Force     略過確認
-ConsentNet 僅本行程設定 VIA_NET_CONSENT=YES（不 setx、不代設永久）
-NoWorkbench 只盤點/注入，不開瀏覽器
回退：via-vdf.cmd 指向 Start-VIA-VDF-v0103.ps1
#>
[CmdletBinding()]
param(
    [ValidateSet('Preview', 'Apply', 'LaunchOnly')]
    [string]$Mode = 'Preview',
    [switch]$Force,
    [switch]$ConsentNet,
    [switch]$NoWorkbench,
    [string]$DataRoot = ''
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

$ErrorActionPreference = 'Stop'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function Resolve-ViaBase {
    param([string]$Start)
    $probe = $Start
    while ($probe) {
        $hit = Join-Path $probe "supportive modules\VIA_SuperAccel_Module.py"
        if (Test-Path -LiteralPath $hit) { return $probe }
        $parent = Split-Path $probe -Parent
        if (-not $parent -or $parent -eq $probe) { break }
        $probe = $parent
    }
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$Base = Resolve-ViaBase -Start $PSScriptRoot
$VdfRoot = Join-Path $Base "functional modules\VDF"
$Sup = Join-Path $Base "supportive modules"
$NetDir = Join-Path $Sup "network"
$NetShim = Join-Path $NetDir "via_net_unified_v0100.py"
$Injector = Join-Path $VdfRoot "tools\VDF_InjectAccelNetBridges_v0104.py"
$ReportDir = Join-Path $VdfRoot "tools\RUN_ACCELNET_v0104_$Stamp"
$ReportJson = Join-Path $ReportDir "ACCELNET_MATRIX_$Stamp.json"
$ReportHtml = Join-Path $ReportDir "ACCELNET_MATRIX_$Stamp.html"

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

function Write-Utf8File {
    param([string]$Path, [string]$Content)
    $dir = Split-Path $Path -Parent
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

$NetShimBody = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""via_net_unified_v0100 — VDF 統包網路工具 shim（只增不減）"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
import importlib.util, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SUP = HERE.parent
_NS = None
_NS_ERR = ""
def _load_netsupport():
    global _NS, _NS_ERR
    if _NS is not None:
        return _NS
    cand = SUP / "VIA_NetSupport.py"
    if not cand.exists():
        _NS_ERR = "VIA_NetSupport.py missing"
        return None
    try:
        spec = importlib.util.spec_from_file_location("VIA_NetSupport_dyn", cand)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["VIA_NetSupport_dyn"] = mod
        spec.loader.exec_module(mod)
        _NS = mod
        return _NS
    except Exception as exc:
        _NS_ERR = f"{type(exc).__name__}: {str(exc)[:120]}"
        return None
def net_consent() -> bool:
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "net_consent"):
        return bool(ns.net_consent())
    return os.environ.get("VIA_NET_CONSENT", "").upper() in ("YES", "1", "TRUE")
def net_ok() -> bool:
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "net_ok"):
        return bool(ns.net_ok())
    try:
        import requests
        return True
    except ImportError:
        return False
def get_session():
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "get_session"):
        return ns.get_session()
    return None
def fetch_json(url: str, **kw):
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "fetch_json"):
        return ns.fetch_json(url, **kw)
    return None
def fetch_text(url: str, **kw):
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "fetch_text"):
        return ns.fetch_text(url, **kw)
    return None
def http_json(url: str, **kw) -> dict:
    if not net_consent():
        return {"state": "NO_CONSENT", "data": None, "note": "VIA_NET_CONSENT not YES"}
    data = fetch_json(url, **kw)
    if data is None:
        return {"state": "FAIL", "data": None, "note": (_NS_ERR or "fetch_json returned None")[:160]}
    return {"state": "OK", "data": data, "note": ""}
def http_text(url: str, **kw) -> dict:
    if not net_consent():
        return {"state": "NO_CONSENT", "data": None, "note": "VIA_NET_CONSENT not YES"}
    text = fetch_text(url, **kw)
    if text is None:
        return {"state": "FAIL", "data": None, "note": _NS_ERR or "fetch_text returned None"}
    return {"state": "OK", "data": text, "note": ""}
def yahoo_quote_summary(*_a, **_k) -> dict:
    return {"state": "SKIP", "data": None, "note": "yahoo_quote_summary not in NetSupport shim (honest)"}
if __name__ == "__main__":
    print(f"via_net_unified_v0100 · net_ok={net_ok()} · consent={'YES' if net_consent() else 'NO'} · accel={'ON' if VIA_ACCEL is not None else 'OFF'}")
'@

if (-not (Test-Path -LiteralPath $NetShim)) {
    Write-Host "[ADD] network shim $NetShim"
    Write-Utf8File -Path $NetShim -Content $NetShimBody
} else {
    Write-Host "[OK]  network shim exists"
}

$InjectorSrc = Join-Path $PSScriptRoot "tools\VDF_InjectAccelNetBridges_v0104.py"
if (-not (Test-Path -LiteralPath $Injector)) {
    $fallback = @(
        (Join-Path $PSScriptRoot "VDF_InjectAccelNetBridges_v0104.py"),
        (Join-Path (Get-Location) "VDF_InjectAccelNetBridges_v0104.py")
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($fallback) {
        New-Item -ItemType Directory -Force -Path (Split-Path $Injector) | Out-Null
        Copy-Item -LiteralPath $fallback -Destination $Injector -Force
    }
}

Write-Host "=== VDF ALL v0104 ==="
Write-Host "Base     : $Base"
Write-Host "VDF      : $VdfRoot"
Write-Host "Mode     : $Mode"
Write-Host "Consent  : $(if ($ConsentNet) { 'SESSION YES (not persistent)' } else { 'unchanged (default closed)' })"

$py = Get-Command py -ErrorAction SilentlyContinue
$python = if ($py) { "py" } else { "python" }

$matrix = $null
if ($Mode -ne 'LaunchOnly') {
    if (-not (Test-Path -LiteralPath $Injector)) {
        Write-Warning "Injector missing: $Injector — skip file-level inject, runtime PATH still set."
    } else {
        $injMode = if ($Mode -eq 'Apply') { 'apply' } else { 'preview' }
        if ($Mode -eq 'Apply' -and -not $Force) {
            $ans = Read-Host "將對缺錨點的 VDF .py 寫入 ACCEL/NET 橋（先備份）。輸入 YES 繼續"
            if ($ans -ne 'YES') { throw "已取消（未寫檔）。改用 -Mode Preview 或 -Force" }
        }
        & $python $Injector --vdf-root $VdfRoot --mode $injMode --backup-dir $ReportDir --report $ReportJson
        if (Test-Path -LiteralPath $ReportJson) {
            $matrix = Get-Content -LiteralPath $ReportJson -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    }
}

$htmlRows = ""
$needA = 0; $needN = 0; $okN = 0; $total = 0
if ($matrix) {
    $total = [int]$matrix.total
    $needA = [int]$matrix.need_accel
    $needN = [int]$matrix.need_net
    $okN = [int]$matrix.already_ok
    foreach ($r in $matrix.rows) {
        $st = if ($r.ok) { "READY" } elseif ($r.need_accel -and $r.need_net) { "NEED ACCEL+NET" } elseif ($r.need_accel) { "NEED ACCEL" } else { "NEED NET" }
        $rel = [string]$r.path
        if ($rel.StartsWith($VdfRoot)) { $rel = $rel.Substring($VdfRoot.Length).TrimStart('\', '/') }
        $htmlRows += "<tr><td>$rel</td><td>$st</td><td>$($r.need_accel)</td><td>$($r.need_net)</td></tr>`n"
    }
}

$html = @"
<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"/>
<title>VDF Accel+Net Matrix v0104 $Stamp</title>
<style>
body{font-family:Segoe UI,Noto Sans TC,sans-serif;background:#0b1220;color:#d7e2f2;margin:24px}
h1{font-size:20px;letter-spacing:.04em}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}
.card{background:#132033;border:1px solid #2a3f5c;padding:12px 16px;min-width:140px}
.card b{display:block;font-size:22px;color:#7fd0ff}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{border-bottom:1px solid #24344c;padding:6px 8px;text-align:left}
th{color:#8fb4d9;position:sticky;top:0;background:#132033}
</style></head><body>
<h1>VDF 全景 · 加速器 / 網路工具矩陣 v0104</h1>
<div class="kpi">
<div class="card">掃描<b>$total</b></div>
<div class="card">已雙橋<b>$okN</b></div>
<div class="card">缺加速器<b>$needA</b></div>
<div class="card">缺網路橋<b>$needN</b></div>
<div class="card">模式<b>$Mode</b></div>
</div>
<p>Base = $Base · 報告 = $ReportDir</p>
<table><thead><tr><th>檔案</th><th>狀態</th><th>need_accel</th><th>need_net</th></tr></thead>
<tbody>
$htmlRows
</tbody></table>
</body></html>
"@
Write-Utf8File -Path $ReportHtml -Content $html
Write-Host "[REPORT] $ReportHtml"

# session runtime: every python child sees supportive modules
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$Sup;$($env:PYTHONPATH)" } else { $Sup }
if ($ConsentNet) {
    $env:VIA_NET_CONSENT = "YES"
    Write-Host "[SESSION] VIA_NET_CONSENT=YES （不寫入使用者環境）"
}

# activate SuperAccel if present
$accel = Join-Path $Sup "VIA_SuperAccel_Module.py"
if (Test-Path -LiteralPath $accel) {
    Write-Host "[ACCEL] activate"
    & $python $accel --activate
}

if (-not $NoWorkbench) {
    $Gate = Join-Path $VdfRoot "Start-VIA-VDF-v0103.ps1"
    if (-not (Test-Path -LiteralPath $Gate)) {
        throw "缺少 v0103 gate：$Gate"
    }
    Write-Host "[LAUNCH] hand-off Start-VIA-VDF-v0103 → v0160C workbench"
    $extra = @()
    if ($DataRoot) { $extra += @("-DataRoot", $DataRoot) }
    & $Gate @extra @args
} else {
    Write-Host "[SKIP] workbench (-NoWorkbench)"
}

Write-Host "=== DONE v0104 ==="
Write-Host "矩陣 HTML：$ReportHtml"

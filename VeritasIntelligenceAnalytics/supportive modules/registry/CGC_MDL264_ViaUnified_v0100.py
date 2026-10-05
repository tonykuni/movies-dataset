#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL264_ViaUnified v0100 — 所有短令整合成一個入口 via 的驗證器(VCGC-REQ169)

操作員令「integrate all short command into one」:Register-VIA-Commands 尾版加一個總門 via。
本支不實作 via(本體在 PS 尾版),只做兩件事:
  check      靜態:尾版 Register 檔 pwsh Parser 0 錯 · 兩章在 · 三個函式(via / Resolve-VIAUnified / Get-VIAUnifiedRoster)在 ·
             全樹短令數(via-* 定義 + 指向 via-* 的別名,後檔蓋前檔)
  --selftest 動態:pwsh 只從尾版檔用 AST 取出那三個函式定義(不點源整條鏈 · 不碰 $PROFILE · 不觸網),
             配 stub 短令逐條驗:原行為 · 正名 · 底線名 · 中文別名 · 精確優先 · 唯一前綴 · 多支不猜 · 找不到不跑 ·
             list 說明取自註解 · which 只解析 · 陣列參數原樣轉交
沒有 pwsh = 動態檢查誠實 SKIP(rc 2),不算過。
"""
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
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE = Path(__file__).stem
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FUNCS = ("via", "Resolve-VIAUnified", "Get-VIAUnifiedRoster")
_FN_RX = re.compile(r"^function\s+(?:global:)?(via-[A-Za-z0-9_-]+)", re.M)
_AL_RX = re.compile(r"Set-Alias\s+-Name\s+(\S+)\s+-Value\s+(via-[A-Za-z0-9_-]+)", re.M)


def _vnum(p: Path) -> int:
    m = re.search(r"-v(\d{4})\.ps1$", p.name)
    return int(m.group(1)) if m else -1


def tail_register() -> Path | None:
    """定義了總門 via 的最新 Register 檔(尾版律:取版號最大且帶 Resolve-VIAUnified 的那支)。"""
    for p in sorted(VIA.glob("Register-VIA-Commands-v*.ps1"), key=_vnum, reverse=True):
        if "function global:Resolve-VIAUnified" in p.read_text(encoding="utf-8", errors="ignore"):
            return p
    return None


def roster_static() -> dict:
    """全部 Register 檔依版號序:via-* 函式名與別名(後檔蓋前檔)。"""
    fns, als = set(), {}
    for p in sorted(VIA.glob("Register-VIA-Commands-v*.ps1"), key=_vnum):
        t = p.read_text(encoding="utf-8", errors="ignore")
        fns.update(_FN_RX.findall(t))
        for a, d in _AL_RX.findall(t):
            als[a] = d
    return {"functions": len(fns), "aliases": len(als), "alias_to_known": sum(1 for d in als.values() if d in fns)}


def _pwsh() -> str | None:
    return shutil.which("pwsh")


def _run_ps(script: str, timeout: int = 180) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "harness.ps1"
        f.write_text(script, encoding="utf-8-sig")
        try:
            p = subprocess.run([_pwsh(), "-NoProfile", "-NonInteractive", "-File", str(f)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
            return p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            return 124, "timeout"


def static_check(path: Path) -> list[tuple[str, bool, str]]:
    t = path.read_text(encoding="utf-8", errors="ignore")
    out = [("① 兩章在(CELERITAS-TEMPLATE-JOIN · PS-ACCEL)",
            "CELERITAS-TEMPLATE-JOIN" in t and "[VIA:PS-ACCEL:v0101]" in t, path.name),
           ("② 前版鏈點源(v0271 以前一字不動,只往上加)",
            re.search(r'\. \(Join-Path \$PSScriptRoot "Register-VIA-Commands-v\d{4}\.ps1"\)', t) is not None, "")]
    missing = [f for f in FUNCS if f"function global:{f}" not in t]
    out.append(("③ 三個函式都在(via · Resolve-VIAUnified · Get-VIAUnifiedRoster)", not missing, f"缺 {missing}" if missing else ""))
    if _pwsh():
        ps = ("$e=$null;$tk=$null;[void][System.Management.Automation.Language.Parser]::ParseFile("
              f"'{path}',[ref]$tk,[ref]$e);'PARSE_ERRORS='+$e.Count")
        rc, o = _run_ps(ps, 60)
        m = re.search(r"PARSE_ERRORS=(\d+)", o)
        out.append(("④ pwsh Parser 0 錯", rc == 0 and m is not None and m.group(1) == "0", (m.group(0) if m else o[-200:])))
    return out


HARNESS = r"""
$ErrorActionPreference = 'Stop'
$path = '__PATH__'
$e = $null; $tk = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tk, [ref]$e)
foreach ($n in 'Get-VIAUnifiedRoster', 'Resolve-VIAUnified', 'via') {
    $fn = $ast.Find({ param($a) $a -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $a.Name -eq "global:$n" }, $true)
    if (-not $fn) { "CHK|load $n|FAIL|missing"; exit 1 }
    . ([scriptblock]::Create($fn.Extent.Text))
}
$td = Join-Path ([IO.Path]::GetTempPath()) ("viaunified_" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $td | Out-Null
$reg = Join-Path $td 'Register-VIA-Commands-v9999.ps1'
@('# 總檢站說明:十四站一次跑', 'function global:via-precheck { }', '# 第一支說明', 'function global:via-alpha { }') | Set-Content -LiteralPath $reg -Encoding UTF8
$global:VIARegisterPath = $reg
function global:via-precheck { 'PRE:' + (@($args | ForEach-Object { if ($_ -is [array]) { 'ARR[' + ($_ -join '+') + ']' } else { "$_" } }) -join ',') }
function global:via-alpha { 'ALPHA:' + ($args -join ',') }
function global:via-alphabet { 'ALPHABET:' + ($args -join ',') }
function global:via-alpine { 'ALPINE' }
Set-Alias -Name via_precheck -Value via-precheck -Scope Global -Force
Set-Alias -Name 總檢 -Value via-precheck -Scope Global -Force
$global:VIAUnifiedPrevVia = { 'PREV' }
function chk([string]$name, [bool]$ok, [string]$note) { "CHK|$name|$(if ($ok) { 'OK' } else { 'FAIL' })|$note" }
try {
    $o = via; chk '⑤ via 無參數 = 原行為(VIA.ps1 總入口照舊轉呼)' ($o -eq 'PREV') "$o"
    $o = via precheck a b; chk '⑥ via <名> → via-<名>,參數原樣轉交' ($o -eq 'PRE:a,b') "$o"
    $o = via via_precheck x; $o2 = via 總檢 y; $o3 = via via-precheck z
    chk '⑦ 底線名 · 中文別名 · 全名都認' ($o -eq 'PRE:x' -and $o2 -eq 'PRE:y' -and $o3 -eq 'PRE:z') "$o | $o2 | $o3"
    $o = via alpha 1; chk '⑧ 精確名優先於前綴(via-alpha 不被 via-alphabet 搶)' ($o -eq 'ALPHA:1') "$o"
    $o = via alphab 2; chk '⑨ 唯一前綴直接跑' ($o -eq 'ALPHABET:2') "$o"
    $global:LASTEXITCODE = 0; $o = via alp; $rc = $global:LASTEXITCODE
    chk '⑩ 前綴對到多支 = 只列不跑(rc 2)' ($null -eq $o -and $rc -eq 2) "rc $rc · out [$o]"
    $global:LASTEXITCODE = 0; $o = via nosuchthing; $rc = $global:LASTEXITCODE
    chk '⑪ 找不到 = 不跑(rc 2)' ($null -eq $o -and $rc -eq 2) "rc $rc"
    $o = (via list alpha 6>&1 | Out-String)
    chk '⑫ via list 關鍵字:列名 + 說明取自定義處上方註解' ($o -match 'via-alpha' -and $o -match '第一支說明' -and $o -notmatch 'via-precheck') ($o -replace '\s+', ' ').Trim()
    $o = (via list 總檢 6>&1 | Out-String)
    chk '⑬ via list 以別名 / 說明找得到' ($o -match 'via-precheck' -and $o -match '十四站') ($o -replace '\s+', ' ').Trim()
    $o = (via which 總檢 6>&1 | Out-String)
    chk '⑭ via which 只解析不執行' ($o -match 'alias' -and $o -match 'via-precheck' -and $o -notmatch 'PRE:') ($o -replace '\s+', ' ').Trim()
    $direct = via-precheck token,bridge; $o = via precheck token,bridge
    chk '⑮ 陣列參數(不加引號的 token,bridge)轉交與直呼相同' ($o -eq $direct -and $o -eq 'PRE:ARR[token+bridge]') "$o vs $direct"
} catch { "CHK|harness|FAIL|$($_.Exception.Message)" }
finally { Remove-Item -LiteralPath $td -Recurse -Force -ErrorAction Ignore }
"""


def dynamic_check(path: Path) -> list[tuple[str, bool, str]]:
    rc, out = _run_ps(HARNESS.replace("__PATH__", str(path).replace("'", "''")))
    rows = []
    for line in out.splitlines():
        if line.startswith("CHK|"):
            _, name, st, note = (line.split("|", 3) + [""])[:4]
            rows.append((name, st == "OK", note[:200]))
    if not rows:
        rows.append(("harness", False, f"rc {rc} · {out[-300:]}"))
    return rows


def selftest() -> int:
    path = tail_register()
    print(f"=== {ENGINE} · 所有短令整合成一個入口 via · 自測(零網路 · 不點源整條鏈 · 不碰 $PROFILE)===")
    if path is None:
        print("  [FAIL] 找不到定義總門 via 的 Register 檔")
        return 1
    rows = static_check(path)
    if _pwsh():
        rows += dynamic_check(path)
    for name, ok, note in rows:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")
    n_ok = sum(1 for _, ok, _ in rows if ok)
    if not _pwsh():
        print(f"  [計] {ENGINE} 自測 {n_ok}/{len(rows)} · SKIP(沒有 pwsh,動態檢查沒跑 = 不算過)")
        return 2
    ok = n_ok == len(rows)
    print(f"  [計] {ENGINE} 自測 {n_ok}/{len(rows)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def check() -> int:
    path = tail_register()
    r = roster_static()
    print(f"  [via 總門] 尾版 {path.name if path else '(無)'} · 短令 {r['functions']} 支 · 別名 {r['aliases']} 個(指向已知短令 {r['alias_to_known']})")
    if path is None:
        return 1
    rows = static_check(path)
    for name, ok, note in rows:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")
    return 0 if all(ok for _, ok, _ in rows) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] in (["check"], []):
        return check()
    print("  用法:check | --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

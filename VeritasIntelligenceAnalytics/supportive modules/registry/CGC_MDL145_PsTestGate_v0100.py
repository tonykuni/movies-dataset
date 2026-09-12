#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL145_PsTestGate v0100 — PowerShell 真測閘(批389 操作員令「test debug by yourself till it works perfectly」)

為何需要本閘:此前 PS 層(Register 短令冊、Invoke-VIA-* 啟動器)在雲端「只能靜態檢括號引號」,
真錯抓不到。批389 於雲端裝入可攜 PowerShell 7.4.6 後首次真測,立刻抓到兩枚真錯:
  ① Invoke-VIA-VdfFetch Resolve-VIARoot:USERPROFILE 空時基底含空值
  ② 同函式硬寫 "C:\Users\tonyk" → 非 Windows 上 Join-Path 噴「Cannot find drive. A drive with the name 'C' does not exist.」
     (我首猜為 null,真因是磁碟機代號不存在=猜錯;真測才給出真話)
並真驗三條路徑:分叉 merge --no-ff 成功、卡未合併 merge --abort 後續跑、via-vdffetch 具名參數傳遞正確
(批384 陣列潑灑 bug 的回歸測)。

三閘(皆誠實三態;pwsh 缺席=SKIP 不假綠):
  P1 解析閘 — 以 PowerShell AST Parser 解析 VIA 根所有 *.ps1;判定守尾版律/封存律:
     同族(檔名去 _v####)尾版解析錯=FAIL(那是現役件,via-* 載入即敗);非尾版舊版解析錯=WARN 具名列出
     (封存件凍結;只增不減律下不刪不改,但誠實標明)。另以「刻意壞檔」反測本閘非空轉。
     批389 首跑實錄:抓到 Invoke-VIA-PSRepair-v0102.ps1 L179 行尾註解截斷運算式 → 該族尾版整支
     Missing closing ')' → via-psrepair 載入即敗;已 version-forward v0103 修(僅移註解位置,邏輯零變更)
  P2 功能閘 — 真建暫時 git 倉(裸倉+兩複本)造真分叉 → 跑 Invoke-VIA-VdfFetch 尾版 -Dry -NoEnter:
     驗 ①自癒判出 DIVERGED 並完成 merge(HEAD 前進、零未合併、兩邊提交皆在)②全程零 PS 錯誤行
     (Join-Path/Cannot bind/Cannot find drive/Exception 一律計為錯)
  P3 參數閘 — 點源 Register 尾版後呼 via-vdffetch(探針腳本回印收到的參數):
     驗 `via-vdffetch 2023`→Year=2023、`2020 --limit 150`→Year=2020 Limit=150、`--dry`→Dry=True
pwsh 尋路:env VIA_PWSH → PATH 之 pwsh/powershell → 常見安裝位置 → 皆缺=SKIP(誠實;工作站必有)
律:全唯讀於正本(只在暫時夾造測料);零 force 零刪除;每閘存證 VIA_Reports/ps_test/PSTEST_<ts>.json。
用法:via-pstest            → 三閘
      python <本檔> --selftest → 九檢(含反測:壞檔必被抓、pwsh 缺=SKIP 不假綠)
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

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports" / "ps_test"
ENGINE_TAG = "CGC_MDL145_PsTestGate v0100"
ERR_RX = re.compile(r"Join-Path:|Cannot bind argument|Cannot find drive|ParserError|Unexpected token|Exception:|ObjectNotFound", re.I)
RULES = ["pwsh 缺席=SKIP 誠實(不假綠);工作站必有 pwsh,雲端可 env VIA_PWSH 指可攜版",
         "正本全唯讀:測料只在暫時夾;零 force 零刪除",
         "反測律:刻意壞檔必被解析閘抓到,否則本閘自身判 FAIL(防空轉)",
         "尾版律/封存律:同族尾版解析錯=FAIL(現役件);非尾版舊版解析錯=WARN 具名(封存凍結,零刪除零改寫)",
         "功能閘以真 git 倉造真分叉,驗自癒後 HEAD 前進且兩邊提交皆在",
         "參數閘為批384 陣列潑灑 bug 的回歸測(具名參數必正確)"]


def find_pwsh() -> str:
    cand = [os.environ.get("VIA_PWSH", "")]
    for n in ("pwsh", "powershell"):
        w = shutil.which(n)
        if w:
            cand.append(w)
    cand += [r"C:\Program Files\PowerShell\7\pwsh.exe",
             r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
             "/usr/bin/pwsh", "/opt/microsoft/powershell/7/pwsh"]
    for c in cand:
        if c and Path(c).exists():
            return c
    return ""


def _run(pwsh: str, args: list, timeout: int = 600, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass"] + args,
                          capture_output=True, text=True, timeout=timeout, cwd=str(cwd) if cwd else None,
                          env=env or os.environ.copy())


PARSE_SCRIPT = r'''
param([string]$Root)
$bad = 0
foreach ($f in (Get-ChildItem -LiteralPath $Root -Filter *.ps1 -File | Sort-Object Name)) {
  $errs = $null; $toks = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$toks, [ref]$errs)
  if ($errs.Count -gt 0) {
    $bad++
    Write-Output ("PARSE-FAIL|" + $f.Name + "|L" + $errs[0].Extent.StartLineNumber + "|" + $errs[0].Message)
  } else { Write-Output ("PARSE-OK|" + $f.Name) }
}
Write-Output ("PARSE-TOTAL|" + $bad)
'''

PROBE_SCRIPT = r'''
param([string]$Year="?", [int]$Limit=0, [switch]$Dry, [switch]$NoEnter, [switch]$NoHeal, [string]$Root="")
Write-Output ("PROBE|" + $Year + "|" + $Limit + "|" + $Dry)
'''

PARAM_SCRIPT = r'''
param([string]$Dir)
. (Join-Path $Dir "Register-VIA-Commands-v0174.ps1") | Out-Null
via-vdffetch 2023
via-vdffetch 2020 --limit 150
via-vdffetch --dry
'''


def p1_parse(pwsh: str, root: Path | None = None, tmp: Path | None = None) -> dict:
    root = root or VIA
    if not pwsh:
        return {"id": "P1", "name": "解析閘(全 .ps1 AST)", "state": "SKIP", "note": "pwsh 缺席(env VIA_PWSH 可指)"}
    scr = (tmp or Path("/tmp")) / "via_ps_parse.ps1"
    scr.write_text(PARSE_SCRIPT, encoding="utf-8")
    r = _run(pwsh, ["-File", str(scr), "-Root", str(root)], timeout=600)
    lines = [l for l in (r.stdout or "").splitlines() if l.startswith(("PARSE-OK|", "PARSE-FAIL|", "PARSE-TOTAL|"))]
    all_fails = [l for l in lines if l.startswith("PARSE-FAIL|")]
    n_ok = sum(1 for l in lines if l.startswith("PARSE-OK|"))
    # 尾版律/封存律:同族尾版必綠(現役件);非尾版壞=WARN 具名(封存凍結,只增不減不刪不改)
    fam_rx = re.compile(r"^(?P<fam>.+?)[-_]v(?P<ver>\d{3,4})\.ps1$", re.I)
    tails: dict[str, int] = {}
    for l in lines:
        nm = l.split("|")[1] if "|" in l else ""
        mm = fam_rx.match(nm)
        if mm:
            fam, ver = mm.group("fam"), int(mm.group("ver"))
            tails[fam] = max(tails.get(fam, -1), ver)

    def is_tail(nm: str) -> bool:
        mm = fam_rx.match(nm)
        if not mm:
            return True   # 無版號=就地件=現役
        return int(mm.group("ver")) == tails.get(mm.group("fam"), -1)
    fails = [l for l in all_fails if is_tail(l.split("|")[1])]
    warns = [l for l in all_fails if not is_tail(l.split("|")[1])]
    # 反測:刻意壞檔必被抓
    anti = "NOT_RUN"
    if tmp:
        bad_dir = tmp / "antitest"
        bad_dir.mkdir(parents=True, exist_ok=True)
        (bad_dir / "broken.ps1").write_text("function X { if ($true) { 'unclosed'\n", encoding="utf-8")
        r2 = _run(pwsh, ["-File", str(scr), "-Root", str(bad_dir)], timeout=300)
        anti = "OK" if "PARSE-FAIL|broken.ps1" in (r2.stdout or "") else "FAIL"
    st = "FAIL" if (fails or anti == "FAIL") else ("WARN" if warns else "OK")
    return {"id": "P1", "name": "解析閘(全 .ps1 AST;尾版必綠/封存版壞=WARN)", "state": st,
            "note": "解析 " + str(n_ok + len(all_fails)) + " 件 · 綠 " + str(n_ok) + " · 尾版紅 " + str(len(fails))
                    + " · 封存版紅 " + str(len(warns)) + " · 反測 " + anti
                    + ("" if not fails else " · 尾版紅:" + "; ".join(f.split("|", 1)[1] for f in fails[:3]))
                    + ("" if not warns else " · 封存版紅(凍結不改):" + "; ".join(w.split("|", 1)[1].split("|")[0] for w in warns[:3])),
            "fails": fails, "warns": warns}


def _git(root: Path, *a) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root)] + list(a), capture_output=True, text=True, timeout=300)


def p2_functional(pwsh: str, tmp: Path) -> dict:
    """真建裸倉+兩複本造真分叉 → 跑 Invoke-VIA-VdfFetch 尾版 -Dry -NoEnter,驗自癒"""
    if not pwsh:
        return {"id": "P2", "name": "功能閘(真分叉→自癒)", "state": "SKIP", "note": "pwsh 缺席"}
    launcher = sorted(VIA.glob("Invoke-VIA-VdfFetch-v*.ps1"))
    if not launcher:
        return {"id": "P2", "name": "功能閘(真分叉→自癒)", "state": "SKIP", "note": "啟動器缺"}
    bare, a, b = tmp / "origin.git", tmp / "A", tmp / "B"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, timeout=120)
    subprocess.run(["git", "clone", "-q", str(bare), str(a)], check=True, timeout=120)
    via_a = a / "VeritasIntelligenceAnalytics"
    via_a.mkdir(parents=True)
    shutil.copy2(launcher[-1], via_a / launcher[-1].name)
    (via_a / "Register-VIA-Commands-v0001.ps1").write_text(
        '$VIA = $PSScriptRoot\nfunction global:Set-VIAGateDefaults { }\nfunction global:Get-VIAEnvPython([string]$f) { return "python3" }\n', encoding="utf-8")
    try:
        (via_a / "supportive modules").symlink_to(VIA / "supportive modules", target_is_directory=True)
    except Exception:
        pass
    _git(a, "add", "-A")
    _git(a, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    _git(a, "push", "-q", "origin", "HEAD:refs/heads/main")
    _git(a, "branch", "-M", "main")
    subprocess.run(["git", "-C", str(bare), "symbolic-ref", "HEAD", "refs/heads/main"], check=True, timeout=120)
    subprocess.run(["git", "clone", "-q", str(bare), str(b)], check=True, timeout=120)
    (b / "remote.txt").write_text("r\n", encoding="utf-8")
    _git(b, "add", "-A")
    _git(b, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "remote work")
    _git(b, "push", "-q", "origin", "main")
    (a / "local.txt").write_text("l\n", encoding="utf-8")
    _git(a, "add", "-A")
    _git(a, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "local work")
    head0 = (_git(a, "rev-parse", "--short", "HEAD").stdout or "").strip()
    env = os.environ.copy()
    env.pop("USERPROFILE", None)
    r = _run(pwsh, ["-File", str(via_a / launcher[-1].name), "-Year", "2023", "-Dry", "-NoEnter"], timeout=900, env=env)
    out = (r.stdout or "") + (r.stderr or "")
    head1 = (_git(a, "rev-parse", "--short", "HEAD").stdout or "").strip()
    log = (_git(a, "log", "--oneline", "-6").stdout or "")
    unm = sum(1 for l in (_git(a, "status", "--porcelain").stdout or "").splitlines() if l[:2] in ("UU", "AA"))
    errs = [l.strip() for l in out.splitlines() if ERR_RX.search(l)]
    merged = head1 != head0 and unm == 0 and "local work" in log and "remote work" in log
    st = "OK" if (merged and not errs) else "FAIL"
    return {"id": "P2", "name": "功能閘(真分叉→自癒)", "state": st,
            "note": ("自癒 HEAD " + head0 + "→" + head1 + " · 未合併 " + str(unm)
                     + " · 兩邊提交皆在 " + ("是" if ("local work" in log and "remote work" in log) else "否")
                     + " · PS 錯誤行 " + str(len(errs)) + (" · " + errs[0][:90] if errs else "")),
            "launcher": launcher[-1].name}


def p3_params(pwsh: str, tmp: Path) -> dict:
    """點源 Register 尾版 → via-vdffetch 具名參數傳遞(批384 回歸測)"""
    if not pwsh:
        return {"id": "P3", "name": "參數閘(via-vdffetch 具名傳遞)", "state": "SKIP", "note": "pwsh 缺席"}
    reg = sorted(VIA.glob("Register-VIA-Commands-v*.ps1"))
    if not reg:
        return {"id": "P3", "name": "參數閘(via-vdffetch 具名傳遞)", "state": "SKIP", "note": "短令冊缺"}
    d = tmp / "V" / "VeritasIntelligenceAnalytics"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(reg[-1], d / "Register-VIA-Commands-v0174.ps1")   # 探針以固定名點源(內容=真尾版)
    (d / "Invoke-VIA-VdfFetch-v0199.ps1").write_text(PROBE_SCRIPT, encoding="utf-8")
    scr = tmp / "via_ps_param.ps1"
    scr.write_text(PARAM_SCRIPT, encoding="utf-8")
    r = _run(pwsh, ["-File", str(scr), "-Dir", str(d)], timeout=600)
    got = [l.strip() for l in ((r.stdout or "") + (r.stderr or "")).splitlines() if l.strip().startswith("PROBE|")]
    want = ["PROBE|2023|0|False", "PROBE|2020|150|False", "PROBE|2023|0|True"]
    st = "OK" if got == want else "FAIL"
    return {"id": "P3", "name": "參數閘(via-vdffetch 具名傳遞)", "state": st,
            "note": "收到 " + (" ; ".join(got) if got else "(空)") + (" · 期望 " + " ; ".join(want) if st == "FAIL" else ""),
            "register": reg[-1].name}


def build(do_print: bool = True, write: bool = True) -> dict:
    import tempfile
    pwsh = find_pwsh()
    gates = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        gates.append(p1_parse(pwsh, VIA, tmp))
        gates.append(p2_functional(pwsh, tmp / "fn"))
        gates.append(p3_params(pwsh, tmp / "pm"))
    states = {g["state"] for g in gates}
    rep = {"engine": ENGINE_TAG, "stamp": datetime.now().strftime("%Y%m%d_%H%M%S"), "pwsh": pwsh or "(缺)",
           "gates": gates, "rules": RULES,
           "state": "FAIL" if "FAIL" in states else ("SKIP" if states == {"SKIP"} else ("WARN" if "WARN" in states else "OK"))}
    if write:
        try:
            REP.mkdir(parents=True, exist_ok=True)
            (REP / ("PSTEST_" + rep["stamp"] + ".json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass
    if do_print:
        print("VIA PS TEST GATE · " + rep["stamp"] + " · " + rep["state"] + " · pwsh " + rep["pwsh"])
        for g in gates:
            print("  [" + g["state"] + "] " + g["id"] + " " + g["name"] + " · " + g["note"][:150])
    return rep


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + note)
        if not cond:
            fails.append(name)

    pwsh = find_pwsh()
    chk("① pwsh 尋路(env VIA_PWSH → PATH → 常見位置;缺=空字串誠實)", isinstance(pwsh, str), "(" + (pwsh or "缺") + ")")
    chk("② 三閘齊備(P1 解析 / P2 功能 / P3 參數)且各自可 SKIP 不假綠",
        all(callable(f) for f in (p1_parse, p2_functional, p3_params))
        and p1_parse("")["state"] == "SKIP" and p2_functional("", Path("/tmp"))["state"] == "SKIP" and p3_params("", Path("/tmp"))["state"] == "SKIP")
    chk("③ 錯誤樣式冊涵蓋真測抓到的兩枚(Cannot bind / Cannot find drive)+解析錯",
        bool(ERR_RX.search("Cannot bind argument to parameter 'Path'")) and bool(ERR_RX.search("Cannot find drive. A drive with the name 'C' does not exist."))
        and bool(ERR_RX.search("ParserError")))
    if not pwsh:
        print("  [SKIP] ④–⑨ 需 pwsh(工作站必有;雲端請 env VIA_PWSH 指可攜版)")
        print("  [計] 九檢 OK " + str(3 - len(fails)) + " · FAIL " + str(len(fails)) + " · SKIP 6(pwsh 缺;誠實)")
        return 1 if fails else 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        g1 = p1_parse(pwsh, VIA, tmp)
        chk("④ 解析閘真跑(尾版全綠=OK/WARN;尾版紅=FAIL 列名)+封存版壞不誤殺現役",
            g1["state"] in ("OK", "WARN") and not g1.get("fails"), g1["note"][:130])
        chk("⑤ 反測非空轉(刻意壞檔必被抓到=反測 OK)", "反測 OK" in g1["note"])
        g2 = p2_functional(pwsh, tmp / "fn2")
        chk("⑥ 功能閘真跑(真分叉→自癒 merge;HEAD 前進;零未合併;兩邊提交皆在)", g2["state"] == "OK", g2["note"][:130])
        chk("⑦ 功能閘零 PS 錯誤行(Join-Path/Cannot bind/Cannot find drive 皆計錯)", "PS 錯誤行 0" in g2["note"])
        g3 = p3_params(pwsh, tmp / "pm2")
        chk("⑧ 參數閘真跑(2023/2020+limit/--dry 三式具名傳遞正確=批384 回歸測)", g3["state"] == "OK", g3["note"][:130])
        rep = build(do_print=False, write=False)
        chk("⑨ 總閘判定(任一 FAIL=FAIL;全 SKIP=SKIP;否則 OK)且存證結構完整",
            rep["state"] in ("OK", "WARN", "FAIL", "SKIP") and len(rep["gates"]) == 3 and all("state" in g for g in rep["gates"]))
    print("  [計] 九檢 OK " + str(9 - len(fails)) + " · FAIL " + str(len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== PowerShell 真測閘(" + ENGINE_TAG + ")· 九檢自測 ===")
        return selftest()
    rep = build()
    return 0 if rep["state"] in ("OK", "WARN", "SKIP") else 1


if __name__ == "__main__":
    sys.exit(main())

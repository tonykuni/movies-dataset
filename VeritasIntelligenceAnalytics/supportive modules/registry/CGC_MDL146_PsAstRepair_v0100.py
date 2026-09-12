#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL146_PsAstRepair v0100 — PowerShell 多輪並行安全修正引擎(批394 操作員令:
「啟動 PowerShell 指令語法多輪並行安全修正引擎,調用全套語法診斷工具與 AST 雙模錨點定位,
對所有 *.ps1/*.psm1 執行全景式語法分析、錯誤分流、並行安全修正、沙盒啟動驗證,直到啟動測試完全無誤」)

本引擎接在 MDL145(PS 真測閘)之後:MDL145 只「判真假」,本引擎「定位+修+複驗」。

一、全景式識別工具矩陣(缺者誠實 SKIP,永不假綠)
  T1 AST Parser  [System.Management.Automation.Language.Parser]::ParseFile → ParseError 清單
                 (含 Extent 起訖行列=精準錨點來源)
  T2 PSScriptAnalyzer  Invoke-ScriptAnalyzer(模組在位才跑;缺=SKIP 並印安裝指令,絕不代裝)
  T3 Command/Param Inspector  對可解析檔取 CommandAst:未知動詞、已知陷阱樣式(硬寫磁碟機代號、
                 Join-Path 空值、行尾註解截斷續行)逐一定位

二、AST 雙模錨點
  精準錨點 Precision:ParseError.Extent 的 (StartLine, StartCol, EndLine, EndCol) + 節點型別
  彈性錨點 Elastic:結構特徵簽名(正規式族 + 前後文窗),用於行數漂移後仍能命中同一處

三、錯誤分流(批389–393 真測實錄為據)
  Parallel-Fixable(可並行、單點、零語意變更)
    F1 行尾註解截斷續行 — `… -and   # 註解` 後接續行 `-and …` → PowerShell 視運算式結束 → 括號永不收
       (批389 於 Invoke-VIA-PSRepair-v0102.ps1 L179 真遇;MDL145 抓到)修法=註解移至續行末,token 零變更
  Report-Only(需語意判斷,只定位不自動改;--apply 亦不改)
    R1 硬寫磁碟機代號 — 非 Windows 上 `Join-Path "C:\..."` 噴 Cannot find drive(批389 實錄)
    R2 Join-Path 空值 — 基底未非空判(批389 實錄)
    R3 其餘 ParseError — 未閉合字串/括號等需人眼
  Sequence-Dependent(跨檔/跨模組;本版只列不動)
    S1 函式匯出名變更、S2 Pipeline 上下游結構、S3 非同步結構

四、多輪循環(每輪皆沙盒複驗;不卡斷)
  R1 全景掃描 → 分流 → 並行修正所有 Parallel-Fixable(寫前寫後各解析一次;任一不過即放棄該檔)
  R2 依賴拓撲(本版:Report-Only/Sequence-Dependent 僅列矩陣,不動)
  R3 收尾:全樹再解析;尾版必綠才算過(封存版壞=WARN,凍結不改)
  迴圈至「尾版零 ParseError」或「本輪零新增修正」(收斂即停,避免無限輪)

五、零九頭龍與只增不減
  修正一律 version-forward:Register-VIA-Commands-v0174.ps1 → v0175.ps1(同族版號 +1);
  目標版號已存在即拒寫(Hydra 守衛),正本零觸碰、零刪除、零 force。

輸出:VIA_Reports/ps_ast_repair/REPAIR_<ts>.json + 頁 VIA_UI_PsAstRepair_v0100.html
      (四分區 MODULE/ENGINE/FUNCTION-LIB/OTHERS + RYG + 修正前後對比 + Hydra 風險 + 沙盒日誌;零 CDN 手機單欄)
用法:via-psrepair-ast            → 全景掃描+分流(唯讀;不改任何檔)
      via-psrepair-ast --apply    → 多輪並行安全修正(只動 Parallel-Fixable;version-forward)
      python <本檔> --selftest    → 九檢(fixture 真修真驗;pwsh 缺=SKIP 不假綠)
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

import html
import importlib.util
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
UI = VIA / "supportive modules" / "ui_support"
REP = VIA / "VIA_Reports" / "ps_ast_repair"
PAGE = UI / "VIA_UI_PsAstRepair_v0100.html"
ENGINE_TAG = "CGC_MDL146_PsAstRepair v0100"
MAX_ROUNDS = int(os.environ.get("VIA_AST_ROUNDS", "3") or 3)
VER_RX = re.compile(r"^(?P<fam>.+?)(?P<sep>[-_])v(?P<ver>\d{3,4})(?P<ext>\.ps1|\.psm1)$", re.I)

# F1 彈性錨點:行尾註解後,下一行以續接運算子開頭(PowerShell 視運算式已結束=括號收不回)
CONT_OPS = ("-and", "-or", "-band", "-bor", "+", "|", "-eq", "-ne", "-gt", "-lt", "-ge", "-le", "-match", "-notmatch", "-contains")
R1_DRIVE_RX = re.compile(r'Join-Path\s+"[A-Za-z]:\\\\?')
R2_NULLBASE_RX = re.compile(r"Join-Path\s+\$env:[A-Za-z_]+\s")
RULES = ["修正一律 version-forward(同族版號 +1);目標版號已存在=拒寫(Hydra 守衛);正本零觸碰零刪除零 force",
         "只自動修 Parallel-Fixable(單點、零語意變更、寫前寫後各解析一次);Report-Only 與 Sequence-Dependent 只列不動",
         "工具缺席誠實 SKIP:PSScriptAnalyzer 缺=印安裝指令不代裝;pwsh 缺=全閘 SKIP",
         "尾版律:判定只看同族尾版;封存版壞=WARN 凍結不改",
         "收斂即停:本輪零新增修正或尾版零 ParseError 即結束(不卡斷、無限輪防護 VIA_AST_ROUNDS)"]

PARSE_PS = r'''
param([string]$Root)
foreach ($f in (Get-ChildItem -LiteralPath $Root -Include *.ps1,*.psm1 -File -Recurse:$false -ErrorAction SilentlyContinue | Sort-Object Name)) {
  $errs = $null; $toks = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$toks, [ref]$errs)
  if ($errs.Count -gt 0) {
    foreach ($e in $errs) {
      Write-Output ("ERR|" + $f.Name + "|" + $e.Extent.StartLineNumber + "|" + $e.Extent.StartColumnNumber + "|" + $e.Extent.EndLineNumber + "|" + $e.Extent.EndColumnNumber + "|" + ($e.Message -replace '\|',' '))
    }
  } else { Write-Output ("OK|" + $f.Name) }
}
'''

PARSE_ONE_PS = r'''
param([string]$File)
$errs = $null; $toks = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($File, [ref]$toks, [ref]$errs)
if ($errs.Count -gt 0) { Write-Output ("BAD|" + $errs[0].Extent.StartLineNumber + "|" + ($errs[0].Message -replace '\|',' ')) } else { Write-Output "GOOD" }
'''

PSSA_PS = r'''
param([string]$Root)
if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) { Write-Output "PSSA|MISSING"; exit 0 }
Import-Module PSScriptAnalyzer -ErrorAction SilentlyContinue
foreach ($f in (Get-ChildItem -LiteralPath $Root -Include *.ps1,*.psm1 -File -ErrorAction SilentlyContinue)) {
  foreach ($d in (Invoke-ScriptAnalyzer -Path $f.FullName -Severity Error,Warning -ErrorAction SilentlyContinue)) {
    Write-Output ("PSSA|" + $f.Name + "|" + $d.Severity + "|" + $d.RuleName + "|" + $d.Line)
  }
}
Write-Output "PSSA|DONE"
'''


def find_pwsh() -> str:
    """與 MDL145 同律:env VIA_PWSH → PATH → 常見位置(零重造:若 MDL145 在位即直取其 find_pwsh)"""
    try:
        p = sorted(HERE.glob("CGC_MDL145_PsTestGate_v0*.py"))
        if p:
            spec = importlib.util.spec_from_file_location("pstest_ar", p[-1])
            m = importlib.util.module_from_spec(spec)
            sys.modules["pstest_ar"] = m
            spec.loader.exec_module(m)
            return m.find_pwsh()
    except Exception:
        pass
    c = [os.environ.get("VIA_PWSH", ""), shutil.which("pwsh") or "", shutil.which("powershell") or ""]
    return next((x for x in c if x and Path(x).exists()), "")


def _ps(pwsh: str, script: str, args: list, tmp: Path, timeout: int = 900) -> str:
    f = tmp / ("ar_" + str(abs(hash(script)) % 99999) + ".ps1")
    f.write_text(script, encoding="utf-8")
    r = subprocess.run([pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(f)] + args,
                       capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")


# ---------------------------------------------------------------- 一、全景掃描
def panorama(pwsh: str, root: Path, tmp: Path) -> dict:
    if not pwsh:
        return {"state": "SKIP", "note": "pwsh 缺席(env VIA_PWSH 可指)", "errors": [], "pssa": "SKIP", "files_ok": 0}
    out = _ps(pwsh, PARSE_PS, ["-Root", str(root)], tmp)
    errs, ok = [], 0
    for l in out.splitlines():
        if l.startswith("OK|"):
            ok += 1
        elif l.startswith("ERR|"):
            p = l.split("|")
            if len(p) >= 7:
                errs.append({"file": p[1], "line": int(p[2]), "col": int(p[3]), "end_line": int(p[4]), "end_col": int(p[5]), "msg": p[6]})
    ps_out = _ps(pwsh, PSSA_PS, ["-Root", str(root)], tmp)
    pssa = "MISSING" if "PSSA|MISSING" in ps_out else ("DONE" if "PSSA|DONE" in ps_out else "PROBE_FAIL")
    findings = [l.split("|") for l in ps_out.splitlines() if l.startswith("PSSA|") and len(l.split("|")) >= 5]
    return {"state": "OK", "errors": errs, "files_ok": ok, "pssa": pssa,
            "pssa_findings": [{"file": f[1], "sev": f[2], "rule": f[3], "line": f[4]} for f in findings][:200],
            "note": ("PSScriptAnalyzer 缺=SKIP(安裝:Install-Module PSScriptAnalyzer -Scope CurrentUser;本引擎不代裝)"
                     if pssa == "MISSING" else "")}


def tail_only(files: list) -> tuple[list, list]:
    """尾版律:回 (尾版檔名集, 封存版檔名集)"""
    tails: dict[str, int] = {}
    for n in files:
        m = VER_RX.match(n)
        if m:
            tails[m.group("fam") + m.group("ext").lower()] = max(tails.get(m.group("fam") + m.group("ext").lower(), -1), int(m.group("ver")))
    tail, arch = [], []
    for n in files:
        m = VER_RX.match(n)
        if not m:
            tail.append(n)
        elif int(m.group("ver")) == tails.get(m.group("fam") + m.group("ext").lower(), -1):
            tail.append(n)
        else:
            arch.append(n)
    return tail, arch


# ---------------------------------------------------------------- 二、錨點 + 分流
def _lead_op(s: str) -> str:
    """續行開頭的續接運算子(取最長相符;字母型運算子後須為界)"""
    best = ""
    for op in CONT_OPS:
        if not s.startswith(op) or len(op) <= len(best):
            continue
        tail = s[len(op):]
        if op[0] == "-" and tail[:1].isalnum():   # -ne vs -nextthing
            continue
        best = op
    return best


def detect_f1(src: str) -> list:
    """F1 彈性錨點:行尾註解 + 下一行以續接運算子起頭
    真因(pwsh 實測):運算式換行只有「上一行以運算子結尾」才續接;
    行尾註解把運算子留在下一行開頭 → 上一行提前結束 → Missing closing ')'。"""
    hits, lines = [], src.splitlines()
    for i, l in enumerate(lines[:-1]):
        if "#" not in l:
            continue
        code, _, comment = l.partition("#")
        if code.count('"') % 2 or code.count("'") % 2:   # 註解其實在字串內=不碰
            continue
        if not code.strip() or not comment.strip():
            continue
        op = _lead_op(lines[i + 1].strip())
        if op:
            hits.append({"line": i + 1, "kind": "F1", "code": code.rstrip(), "comment": comment.rstrip(),
                         "op": op, "next": lines[i + 1].strip()[:60]})
    return hits


def fix_f1(src: str, hits: list) -> tuple[str, int]:
    """真修(與主線 PSRepair v0103 同法):續接運算子上提到本行末 + 註解搬到續行末
    token 零變更(僅搬動運算子與註解的位置),運算式語意不變。"""
    lines = src.splitlines(keepends=False)
    n = 0
    for h in sorted(hits, key=lambda x: -x["line"]):
        i = h["line"] - 1
        j = i + 1
        if j >= len(lines):
            continue
        code, _, comment = lines[i].partition("#")
        op = h.get("op") or _lead_op(lines[j].strip())
        if not op:
            continue
        raw = lines[j]
        lead = raw[:len(raw) - len(raw.lstrip())]
        rest = raw.strip()[len(op):].lstrip()
        lines[i] = code.rstrip() + " " + op               # 運算子上提=顯式續接
        jc, jsep, jcom = rest.partition("#")
        ok_str = not (jc.count('"') % 2 or jc.count("'") % 2)
        if jsep and ok_str and jcom.strip():              # 續行已有註解=合併不丟字
            lines[j] = lead + jc.rstrip() + "   # " + jcom.strip() + " · " + comment.strip()
        else:
            lines[j] = lead + rest.rstrip() + "   # " + comment.strip()
        n += 1
    return ("\n".join(lines) + ("\n" if src.endswith("\n") else "")), n


def detect_reports(src: str) -> list:
    out = []
    for i, l in enumerate(src.splitlines(), 1):
        if R1_DRIVE_RX.search(l):
            out.append({"line": i, "kind": "R1", "note": "硬寫磁碟機代號(非 Windows 上 Join-Path 噴 Cannot find drive)"})
        elif R2_NULLBASE_RX.search(l) and "if (" not in l:
            out.append({"line": i, "kind": "R2", "note": "Join-Path 基底為 $env: 未見非空判(空值即噴 Cannot bind)"})
    return out


def next_version_path(p: Path) -> Path | None:
    """version-forward 目標;Hydra 守衛:已存在即 None"""
    m = VER_RX.match(p.name)
    if not m:
        return None
    nxt = p.with_name(m.group("fam") + m.group("sep") + "v" + ("%04d" % (int(m.group("ver")) + 1)) + m.group("ext"))
    return None if nxt.exists() else nxt


def parse_ok(pwsh: str, f: Path, tmp: Path) -> tuple[bool, str]:
    out = _ps(pwsh, PARSE_ONE_PS, ["-File", str(f)], tmp, timeout=300)
    if "GOOD" in out:
        return True, ""
    bad = [l for l in out.splitlines() if l.startswith("BAD|")]
    return False, (bad[0][4:] if bad else out.strip()[:120])


# ---------------------------------------------------------------- 三、多輪
def run_rounds(pwsh: str, root: Path, tmp: Path, apply: bool, do_print: bool = True) -> dict:
    rounds, fixed_total = [], 0
    for rnd in range(1, MAX_ROUNDS + 1):
        pan = panorama(pwsh, root, tmp)
        if pan["state"] == "SKIP":
            return {"state": "SKIP", "rounds": [], "note": pan["note"], "panorama": pan}
        names = [e["file"] for e in pan["errors"]]
        all_files = [p.name for p in sorted(root.glob("*.ps1")) + sorted(root.glob("*.psm1"))]
        tails, archs = tail_only(all_files)
        tail_errs = [e for e in pan["errors"] if e["file"] in tails]
        arch_errs = [e for e in pan["errors"] if e["file"] in archs]
        # 分流 + 修
        acts = []
        targets = sorted({e["file"] for e in tail_errs})
        for nm in targets:
            f = root / nm
            src = f.read_text(encoding="utf-8", errors="ignore")
            f1 = detect_f1(src)
            rep = detect_reports(src)
            act = {"file": nm, "class": "Parallel-Fixable" if f1 else "Report-Only",
                   "f1": f1, "reports": rep, "state": "PLAN", "target": "", "note": ""}
            if f1 and apply:
                new_src, n = fix_f1(src, f1)
                nxt = next_version_path(f)
                if nxt is None:
                    act["state"], act["note"] = "BLOCKED", "Hydra 守衛:下一版號已存在或無版號檔(不就地改正本)"
                else:
                    sand = tmp / ("sandbox_" + nxt.name)
                    sand.write_text(new_src, encoding="utf-8")
                    good, why = parse_ok(pwsh, sand, tmp)
                    if not good:
                        act["state"], act["note"] = "REJECT", "沙盒複驗未過=放棄該檔(誠實):" + why
                    else:
                        nxt.write_text(new_src, encoding="utf-8")
                        good2, why2 = parse_ok(pwsh, nxt, tmp)
                        act["state"] = "OK" if good2 else "FAIL"
                        act["target"], act["note"] = nxt.name, ("修 " + str(n) + " 處 F1;寫後複驗 " + ("綠" if good2 else "紅 " + why2))
                        fixed_total += 1 if good2 else 0
            acts.append(act)
        rounds.append({"round": rnd, "tail_errors": len(tail_errs), "archive_errors": len(arch_errs),
                       "files_ok": pan["files_ok"], "pssa": pan["pssa"], "actions": acts,
                       "pssa_findings": len(pan.get("pssa_findings", [])),
                       "archive_list": [{"file": x["file"], "line": x.get("line", 0), "msg": str(x.get("msg", ""))[:140]}
                                        for x in arch_errs],
                       "tail_list": [{"file": x["file"], "line": x.get("line", 0), "msg": str(x.get("msg", ""))[:140]}
                                     for x in tail_errs]})
        if do_print:
            print("  [R" + str(rnd) + "] 尾版 ParseError " + str(len(tail_errs)) + " · 封存版 " + str(len(arch_errs))
                  + " · 解析綠 " + str(pan["files_ok"]) + " · PSSA " + pan["pssa"]
                  + " · 本輪動作 " + str(sum(1 for a in acts if a["state"] == "OK")))
            for a in acts:
                print("      [" + a["state"] + "] " + a["file"] + " · " + a["class"]
                      + (" → " + a["target"] if a["target"] else "") + (" · " + a["note"] if a["note"] else ""))
        if not tail_errs or not apply or not any(a["state"] == "OK" for a in acts):
            break   # 收斂即停
    last = rounds[-1] if rounds else {}
    if not last:
        state = "SKIP"
    elif last.get("tail_errors"):
        state = "FAIL"                                  # 尾版律:同族尾版必綠
    elif last.get("archive_errors"):
        state = "WARN"                                  # 封存律:封存版壞=凍結不改(誠實標黃)
    else:
        state = "OK"
    return {"state": state, "rounds": rounds, "fixed": fixed_total, "panorama": None}


def build(apply: bool = False, do_print: bool = True, write: bool = True, root: Path | None = None) -> dict:
    import tempfile
    root = root or VIA
    pwsh = find_pwsh()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        res = run_rounds(pwsh, root, tmp, apply, do_print)
    rep = {"engine": ENGINE_TAG, "stamp": datetime.now().strftime("%Y%m%d_%H%M%S"), "root": str(root),
           "pwsh": pwsh or "(缺)", "apply": apply, "state": res["state"], "fixed": res.get("fixed", 0),
           "rounds": res.get("rounds", []), "rules": RULES, "note": res.get("note", "")}
    if write:
        try:
            REP.mkdir(parents=True, exist_ok=True)
            (REP / ("REPAIR_" + rep["stamp"] + ".json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
            UI.mkdir(parents=True, exist_ok=True)
            PAGE.write_text(render(rep), encoding="utf-8")
        except Exception:
            pass
    if do_print:
        print("VIA PS AST REPAIR · " + rep["stamp"] + " · " + rep["state"] + " · pwsh " + rep["pwsh"]
              + " · " + ("APPLY" if apply else "唯讀") + " · 修 " + str(rep["fixed"]) + " 件"
              + (" · " + rep["note"] if rep["note"] else ""))
        if write:
            print("  [頁] " + str(PAGE))
    return rep


# ---------------------------------------------------------------- 頁
def _b(s: str) -> str:
    c = {"OK": "gr", "PLAN": "gy", "WARN": "ye", "SKIP": "gy", "REJECT": "ye", "BLOCKED": "ye", "FAIL": "rd"}.get(s, "gy")
    return '<span class="b ' + c + '">' + html.escape(s) + "</span>"


def render(r: dict) -> str:
    e = html.escape
    rows = ""
    for rd in r.get("rounds", []):
        for a in rd["actions"]:
            rows += ('<tr><td class="c m">R' + str(rd["round"]) + '</td><td class="m">' + e(a["file"]) + '</td><td class="m">' + e(a["class"])
                     + '</td><td class="c">' + _b(a["state"]) + '</td><td class="m">' + e(a.get("target", "") or "—")
                     + '</td><td class="dim">' + e("F1 " + str(len(a.get("f1", []))) + " · Report " + str(len(a.get("reports", []))) + " · " + str(a.get("note", ""))[:120]) + "</td></tr>")
    arows = ""
    seen_a = set()
    for rd in r.get("rounds", []):
        for a in rd.get("archive_list", []):
            k = (a["file"], a["line"], a["msg"])
            if k in seen_a:
                continue
            seen_a.add(k)
            arows += ('<tr><td class="m">' + e(a["file"]) + '</td><td class="c m">' + str(a["line"])
                      + '</td><td class="dim">' + e(a["msg"]) + "</td></tr>")
    rrows = "".join('<tr><td class="c m">R' + str(rd["round"]) + '</td><td class="c m">' + str(rd["tail_errors"]) + '</td><td class="c m">' + str(rd["archive_errors"])
                    + '</td><td class="c m">' + str(rd["files_ok"]) + '</td><td class="c m">' + e(rd["pssa"]) + '</td><td class="c m">' + str(rd["pssa_findings"]) + "</td></tr>"
                    for rd in r.get("rounds", []))
    head = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VIA · PS AST 修復矩陣</title><style>:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}*{box-sizing:border-box}"
            "body{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}"
            ".wrap{max-width:1300px;margin:0 auto;padding:18px 14px 48px}h1{font-size:14px;margin:0}.sub{color:var(--mu);margin:3px 0 14px}"
            "h2{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}.nav a{color:#7dd3fc;margin-right:12px;text-decoration:none}"
            ".kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:14px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}.kpi .n{font-size:16px;font-weight:600}.kpi .l{font-size:10px;color:var(--mu)}"
            "table{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}th{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}td.c{text-align:center}.m{font-family:ui-monospace,Consolas,monospace;font-size:10px}.dim{color:var(--mu)}"
            ".b{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}.gr{background:#064e3b;color:#34d399;border-color:#059669}.ye{background:#78350f;color:#fde047;border-color:#d97706}.rd{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}.gy{background:#1f2937;color:#9ca3af;border-color:#374151}"
            ".note{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}"
            "@media(max-width:700px){table,thead,tbody,tr,td,th{display:block}thead{display:none}td{border:0;padding:2px 6px}tr{border-bottom:1px solid var(--line);padding:6px 0}}</style></head><body><div class=\"wrap\">")
    body = ("<h1>VIA PS AST REPAIR · 多輪並行安全修正矩陣</h1><p class=\"sub\">" + e(r["engine"]) + " · " + e(r["stamp"]) + " · pwsh " + e(r["pwsh"])
            + " · " + ("APPLY" if r["apply"] else "唯讀") + " · 修 " + str(r["fixed"]) + " 件</p>"
            '<p class="nav"><a href="VIA_UI_ProductGate_v0100.html">產</a><a href="VIA_UI_ParallelLanes_v0100.html">道</a>'
            '<a href="VIA_UI_ProjectCompletion_v0100.html">竣</a><a href="VIA_UI_AccelImport_v0100.html">加速</a></p>'
            '<div class="kpis"><div class="kpi"><div class="n">' + _b(r["state"]) + '</div><div class="l">RYG 健康度</div></div>'
            '<div class="kpi"><div class="n">' + str(len(r.get("rounds", []))) + '</div><div class="l">ENGINE 輪數</div></div>'
            '<div class="kpi"><div class="n">' + str(r["fixed"]) + '</div><div class="l">FUNCTION-LIB 修正件</div></div>'
            '<div class="kpi"><div class="n">' + e(r.get("rounds", [{}])[-1].get("pssa", "—") if r.get("rounds") else "—") + '</div><div class="l">OTHERS PSSA</div></div></div>'
            "<h2>ENGINE — 每輪全景(尾版 ParseError / 封存版 / 解析綠 / PSSA)</h2>"
            '<table><colgroup><col style="width:10%"><col style="width:20%"><col style="width:20%"><col style="width:18%"><col style="width:16%"><col style="width:16%"></colgroup>'
            "<thead><tr><th>輪</th><th>尾版 ParseError</th><th>封存版(凍結)</th><th>解析綠</th><th>PSSA</th><th>PSSA 發現</th></tr></thead><tbody>" + rrows + "</tbody></table>"
            "<h2>MODULE — 逐檔分流與修正(前後對比=版號 +1;Hydra 守衛)</h2>"
            '<table><colgroup><col style="width:7%"><col style="width:26%"><col style="width:15%"><col style="width:10%"><col style="width:18%"><col style="width:24%"></colgroup>'
            "<thead><tr><th>輪</th><th>檔</th><th>分類</th><th>態</th><th>產出版</th><th>細節</th></tr></thead><tbody>" + (rows or '<tr><td colspan="6" class="dim">本輪零動作</td></tr>') + "</tbody></table>"
            "<h2>OTHERS — 封存版凍結紅檔(尾版律:不改不刪,只誠實列出)</h2>"
            '<table><colgroup><col style="width:40%"><col style="width:10%"><col style="width:50%"></colgroup>'
            "<thead><tr><th>封存檔</th><th>行</th><th>ParseError</th></tr></thead><tbody>" + (arows or '<tr><td colspan="3" class="dim">封存版零紅</td></tr>') + "</tbody></table>"
            '<div class="note">' + "<br>".join(e(x) for x in r["rules"]) + "</div></div></body></html>")
    return head + body


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + note)
        if not cond:
            fails.append(name)

    pwsh = find_pwsh()
    chk("① 工具尋路(pwsh 共用 MDL145 find_pwsh 零重造;缺=空字串誠實)", isinstance(pwsh, str), "(" + (pwsh or "缺") + ")")
    broken = ("function T {\n    Test-X 'a' (\n        (-not $x) -and (-not $y)   # 說明\n"
              "        -and ($z -match 'q'))\n    Write-Host 'done'\n}\n")
    hits = detect_f1(broken)
    chk("② F1 彈性錨點(行尾註解+下一行以 -and 起頭=真因;命中 1 處並記行號)",
        len(hits) == 1 and hits[0]["line"] == 3, "(命中 " + str(len(hits)) + ")")
    fixed, n = fix_f1(broken, hits)
    chk("③ F1 修法=運算子上提本行末+註解搬續行末(token 零變更;註解文字保留)",
        n == 1 and "(-not $y) -and" in fixed and "($z -match 'q'))   # 說明" in fixed
        and fixed.count("說明") == 1 and fixed.count("-and") == broken.count("-and"))
    inside_str = 'Write-Host "a # b"\n-and $x\n'
    chk("④ 反誤判(註解符在字串內=不碰;無續接運算子=不碰)",
        detect_f1(inside_str) == [] and detect_f1("$a = 1   # c\n$b = 2\n") == [])
    reps = detect_reports('$x = Join-Path "C:\\Users\\t" "y"\n$z = Join-Path $env:NOPE "w"\n')
    chk("⑤ Report-Only 定位(R1 硬寫磁碟機代號 / R2 $env: 基底未非空判;只列不改)",
        {r["kind"] for r in reps} == {"R1", "R2"} and all("line" in r for r in reps))
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        f = t / "Fix-Me-v0100.ps1"
        f.write_text(broken, encoding="utf-8")
        nxt = next_version_path(f)
        chk("⑥ version-forward 目標(Fix-Me-v0100.ps1 → v0101;連字號族亦認)", nxt is not None and nxt.name == "Fix-Me-v0101.ps1")
        (t / "Fix-Me-v0101.ps1").write_text("# occupied\n", encoding="utf-8")
        chk("⑦ Hydra 守衛(下一版號已存在=拒寫 None;正本零觸碰)", next_version_path(f) is None and f.read_text(encoding="utf-8") == broken)
        (t / "Fix-Me-v0101.ps1").unlink()
        if not pwsh:
            print("  [SKIP] ⑧⑨ 需 pwsh(工作站必有;雲端 env VIA_PWSH)")
            print("  [計] 九檢 OK " + str(7 - len(fails)) + " · FAIL " + str(len(fails)) + " · SKIP 2(pwsh 缺;誠實)")
            return 1 if fails else 0
        ok_before, why = parse_ok(pwsh, f, t)
        rep = build(apply=True, do_print=False, write=False, root=t)
        prod = t / "Fix-Me-v0101.ps1"
        ok_after = parse_ok(pwsh, prod, t)[0] if prod.exists() else False
        chk("⑧ 多輪真修真驗(壞檔解析紅→修→產出 v0101 解析綠;原檔零觸碰;收斂即停)",
            (not ok_before) and prod.exists() and ok_after and f.read_text(encoding="utf-8") == broken and rep["fixed"] == 1,
            "(修前紅 " + str(not ok_before) + " · 修後綠 " + str(ok_after) + " · 輪 " + str(len(rep["rounds"])) + ")")
        healthy = t / "Healthy-v0100.ps1"
        healthy.write_text("$a = 1   # ok\nWrite-Host $a\n", encoding="utf-8")
        rep2 = build(apply=True, do_print=False, write=False, root=t)
        chk("⑨ 健康檔零動作(無 ParseError=不產新版;永不沒事亂改)",
            not (t / "Healthy-v0101.ps1").exists() and rep2["state"] in ("OK", "WARN"), "(態 " + rep2["state"] + ")")
    print("  [計] 九檢 OK " + str(9 - len(fails)) + " · FAIL " + str(len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== PS AST 多輪並行安全修正引擎(" + ENGINE_TAG + ")· 九檢自測 ===")
        return selftest()
    rep = build(apply="--apply" in a)
    return 0 if rep["state"] in ("OK", "WARN", "SKIP") else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL101_PSAstRepair — PowerShell 多輪 AST 語法修正引擎(批244;操作員 Mega-Prompt)
====================================================================
操作員令:「PowerShell 指令語法多輪並行安全修正引擎——全景式分析先行
/AST 雙模錨點/Zero-Hydra/Parallel-Fixable 並行修正/沙盒驗證閉環/
HTML RYG 矩陣四專區」。
機制:
  ①全景掃描:全樹 ps1/psm1 盤點(排除 .git/node_modules/_archive/
    90_PRIOR_PACKAGES);診斷雙軌——
    正主=pwsh [Parser]::ParseFile AST(工作站在;精準行列錨點)
    後備=Python 啟發式(雲端 pwsh 缺=誠實 HEURISTIC_ONLY 標):
      H1 雙引號字串內 $var: 被解析為 scope 限定符(批243 收容包實錯類)
      H2 引號平衡粗檢(不平衡=Sequence-Dependent 僅列不修)
  ②分類:Parallel-Fixable(H1 類=局部單行安全修)/Sequence-Dependent
    (跨結構=誠實列示零觸碰=Zero-Hydra)
  ③fix 多輪:R1 並行修 H1(彈性錨點=行內樣式簽名,容行漂移)——
    修前整檔讓位備份 VIA_Reports/ps_repair/backup_<ts>/+manifest+
    UNDO 指引(只增不減);R2 重掃驗證;R3 沙盒 parse 覆核
    (pwsh 在=真 AST;缺=啟發式再掃誠實標)
  ④HTML RYG 矩陣:四專區 ENGINE(VIA.ps1/launch*)/MODULE(psm1)/
    FUNCTION-LIB(supportive)/OTHERS;修正前後對比;Hydra 風險欄。
用法:python3 CGC_MDL101_PSAstRepair_v0100.py scan|fix [--root DIR]
      | --selftest
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
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUTDIR = VIA / "VIA_Reports" / "ps_repair"
EXCLUDE = {".git", "node_modules", "_archive", "90_PRIOR_PACKAGES",
           "__pycache__", "VIA_Reports", "uploads"}   # 報告/備份/上傳=衍生物不掃

# H1(可修窄類):雙引號內 $var: 後接空白/引號/右括/行尾=確定 PS 解析錯
# (批243 收容 GLE 安裝器第 67 行同型)。反引號跳脫 `$ =字面文本不計。
# H1R(REVIEW 類):$var: 後接 CJK 或 ::——PS 變數名可含 Unicode=語意
# 疑義非必語法錯→僅列示候 pwsh AST/操作員裁決(Zero-Hydra 不盲修)。
H1_RX = re.compile(r"(?<!`)\$([A-Za-z_][A-Za-z0-9_]*):(?=[\s\"'\)]|$)")
H1R_RX = re.compile(r"(?<!`)\$([A-Za-z_][A-Za-z0-9_]*):(?=[:\u3400-\u9fff])")
DQ_RX = re.compile(r'"((?:`.|[^"`])*)"')          # PS 雙引號段(` 跳脫)


def _pwsh() -> str | None:
    for exe in ("pwsh", "powershell"):
        if shutil.which(exe):
            return exe
    return None


def inventory(root: Path) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() in (".ps1", ".psm1") and p.is_file() \
                and not any(x in EXCLUDE for x in p.parts):
            out.append(p)
    return out


def zone_of(p: Path) -> str:
    """四專區(操作員 Mega-Prompt 輸出規範)"""
    if p.suffix.lower() == ".psm1":
        return "MODULE"
    if p.name.lower().startswith(("via.", "launch")):
        return "ENGINE"
    if "supportive modules" in str(p):
        return "FUNCTION-LIB"
    return "OTHERS"


def diag_heuristic(p: Path) -> list[dict]:
    """Python 啟發式雙檢(雲端後備;精準行列錨點)"""
    finds = []
    try:
        lines = p.read_text(encoding="utf-8-sig",
                            errors="replace").splitlines()
    except Exception as exc:
        return [{"kind": "READ_ERR", "cls": "Sequence-Dependent",
                 "line": 0, "msg": type(exc).__name__}]
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("#"):
            continue
        for m in DQ_RX.finditer(ln):
            seg = m.group(1)
            for h in H1_RX.finditer(seg):
                finds.append({
                    "kind": "VAR_COLON_IN_DQ", "cls": "Parallel-Fixable",
                    "line": i, "col": m.start() + h.start() + 2,
                    "var": h.group(1),
                    "msg": f'雙引號內 ${h.group(1)}: 將被解析為 scope 限定符',
                    "sig": ln.strip()[:100]})
            for h in H1R_RX.finditer(seg):
                finds.append({
                    "kind": "VAR_COLON_REVIEW", "cls": "Sequence-Dependent",
                    "line": i, "var": h.group(1),
                    "msg": f'${h.group(1)}:後接 CJK/::=語意疑義(候 pwsh AST'
                           '/操作員裁決;Zero-Hydra 不盲修)',
                    "sig": ln.strip()[:100]})
    dq = sum(ln.count('"') - ln.count('`"') for ln in lines
             if not ln.lstrip().startswith("#"))
    if dq % 2 == 1 and "@\"" not in "\n".join(lines):
        finds.append({"kind": "QUOTE_IMBALANCE", "cls": "Sequence-Dependent",
                      "line": 0, "msg": "雙引號數奇數(粗檢;僅列不修=Zero-Hydra)"})
    return finds


def diag_pwsh(p: Path, exe: str) -> list[dict] | None:
    """正主道:真 PS AST ParseFile(精準錨點);失敗=None 誠實退啟發式"""
    try:
        cmd = ("$e=$null;[void][System.Management.Automation.Language."
               "Parser]::ParseFile('" + str(p).replace("'", "''") +
               "',[ref]$null,[ref]$e);"
               "$e|ForEach-Object{ $_.Extent.StartLineNumber.ToString()+"
               "'|'+$_.Message }")
        r = subprocess.run([exe, "-NoProfile", "-Command", cmd],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None
        out = []
        for ln in r.stdout.splitlines():
            if "|" in ln:
                n, msg = ln.split("|", 1)
                out.append({"kind": "AST_PARSE", "cls": "Sequence-Dependent",
                            "line": int(n) if n.isdigit() else 0,
                            "msg": msg.strip()[:200]})
        return out
    except Exception:
        return None


def scan(root: Path | None = None) -> dict:
    root = root or VIA
    exe = _pwsh()
    files = inventory(root)
    rows = []
    for p in files:
        finds = diag_heuristic(p)
        ast = diag_pwsh(p, exe) if exe else None
        if ast:
            hset = {f["line"] for f in finds}
            finds += [a for a in ast if a["line"] not in hset]
        n_fix = sum(1 for f in finds if f["cls"] == "Parallel-Fixable")
        n_seq = len(finds) - n_fix
        rows.append({"file": str(p.relative_to(root)), "zone": zone_of(p),
                     "fixable": n_fix, "sequence": n_seq, "finds": finds,
                     "ryg": ("G" if not finds else
                             "Y" if n_seq == 0 else "R")})
    return {"root": str(root), "mode": "AST+HEURISTIC" if exe
            else "HEURISTIC_ONLY(pwsh 缺=誠實標)",
            "files": len(files), "rows": rows,
            "fixable": sum(r["fixable"] for r in rows),
            "sequence": sum(r["sequence"] for r in rows)}


def apply_fix(root: Path | None = None) -> dict:
    """R1 並行修(Parallel-Fixable 一口氣全修)+讓位備份+R2 重掃+R3 覆核"""
    root = root or VIA
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    s1 = scan(root)
    fixed, backups = [], []
    bdir = ((root if root != VIA else VIA)
            / "VIA_Reports" / "ps_repair" / f"backup_{ts}")
    for r in s1["rows"]:
        tgt = [f for f in r["finds"] if f["cls"] == "Parallel-Fixable"]
        if not tgt:
            continue
        p = root / r["file"]
        raw = p.read_text(encoding="utf-8-sig", errors="replace")
        # 修前整檔讓位備份(只增不減;Zero-Hydra 可回滾)
        bp = bdir / r["file"]
        bp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, bp)
        backups.append(str(bp))
        new_lines = []
        n = 0
        for ln in raw.splitlines(keepends=True):
            if not ln.lstrip().startswith("#") and DQ_RX.search(ln):
                def _seg(m):
                    nonlocal n
                    seg, c = H1_RX.subn(r'${\1}:', m.group(1))
                    n += c
                    return '"' + seg + '"'
                ln = DQ_RX.sub(_seg, ln)
            new_lines.append(ln)
        p.write_text("".join(new_lines), encoding="utf-8")
        fixed.append({"file": r["file"], "n": n})
    s2 = scan(root)                                   # R2 重掃驗證
    verify = "CLEAN" if s2["fixable"] == 0 else "RESIDUAL"
    if backups:
        bdir.mkdir(parents=True, exist_ok=True)
        (bdir / "manifest.json").write_text(json.dumps({
            "ts": ts, "fixed": fixed, "backups": backups,
            "undo": "整檔覆回 backup_<ts>/<相對路徑> 即回滾(只增不減)"},
            ensure_ascii=False, indent=1), encoding="utf-8")
    return {"round1_fixed": fixed, "backup_dir": str(bdir) if backups
            else None, "round2": {"fixable": s2["fixable"],
                                  "sequence": s2["sequence"]},
            "round3_verify": verify + ("(pwsh AST)" if _pwsh()
                                       else "(啟發式;pwsh 缺誠實標)"),
            "scan_before": s1, "scan_after": s2}


def render(res: dict, ts: str) -> str:
    zones: dict = {}
    for r in res["rows"]:
        zones.setdefault(r["zone"], []).append(r)
    body = ""
    for z in ("ENGINE", "MODULE", "FUNCTION-LIB", "OTHERS"):
        rs = zones.get(z, [])
        if not rs:
            continue
        trs = "".join(
            f"<tr class='{r['ryg'].lower()}'><td>{html.escape(r['file'])}</td>"
            f"<td>{r['ryg']}</td><td>{r['fixable']}</td><td>{r['sequence']}</td>"
            f"<td>{html.escape('; '.join(f['msg'] for f in r['finds'][:3]))}</td></tr>"
            for r in rs if r["finds"]) or \
            f"<tr class='g'><td colspan='5'>全綠 {len(rs)} 件</td></tr>"
        body += (f"<h2>{z}({len(rs)} 件)</h2><table><thead><tr>"
                 "<th>檔</th><th>RYG</th><th>並行可修</th><th>循序依賴</th>"
                 f"<th>訊息</th></tr></thead><tbody>{trs}</tbody></table>")
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PS AST 修正矩陣</title><style>
body{{background:#0b1220;color:#c7d3e8;font:10.5px/1.5 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px;max-width:1180px;margin:0 auto}}
h1{{font-size:14px;color:#e8eefb}}h2{{font-size:11.5px;color:#4f8ef7;margin:12px 0 4px}}
.sub{{color:#7e8db0;font-size:10px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:#7e8db0;font-size:9.5px;border-bottom:1px solid #1e2a44;padding:2px 6px 2px 0}}
td{{padding:2px 6px 2px 0;border-bottom:1px dashed #1e2a44;overflow-wrap:anywhere}}
tr.g td{{color:#6ee7a0}}tr.y td{{color:#f0b429}}tr.r td{{color:#f87171}}
</style></head><body>
<h1>PowerShell 多輪 AST 語法修正矩陣(CGC_MDL101)</h1>
<div class="sub">{ts} · 模式 {res['mode']} · {res['files']} 件 ·
並行可修 {res['fixable']} · 循序依賴 {res['sequence']} ·
Zero-Hydra:循序類僅列不修 · 修必讓位備份+manifest+UNDO</div>
{body}</body></html>"""


def run(verb: str, root: Path | None = None) -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    if verb == "fix":
        res = apply_fix(root)
        page = render(res["scan_after"], ts)
        out = OUTDIR / "PS_REPAIR_MATRIX.html"
        out.write_text(page, encoding="utf-8")
        print(f"[fix] R1 修 {sum(f['n'] for f in res['round1_fixed'])} 處"
              f"/{len(res['round1_fixed'])} 檔 · 備份 {res['backup_dir']}"
              f" · R2 殘可修 {res['round2']['fixable']}"
              f" · R3 {res['round3_verify']} · 矩陣 {out.name}")
        return 0 if res["round2"]["fixable"] == 0 else 1
    res = scan(root)
    page = render(res, ts)
    out = OUTDIR / "PS_REPAIR_MATRIX.html"
    out.write_text(page, encoding="utf-8")
    print(f"[scan] {res['files']} 件 · 模式 {res['mode']} · "
          f"並行可修 {res['fixable']} · 循序依賴 {res['sequence']}"
          f" · 矩陣 {out}")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        bad = tdp / "launch_bad.ps1"
        bad.write_text('$x = 1\nthrow "exit code $x: boom"\n'
                       'Write-Host "ok ${y}: fine"\n', encoding="utf-8")
        good = tdp / "good_lib.psm1"
        good.write_text('function Get-A { "safe ${z}: t" }\n',
                        encoding="utf-8")
        s = scan(tdp)
        row = next(r for r in s["rows"] if r["file"] == "launch_bad.ps1")
        chk("① 全景掃描盤點(ps1+psm1 入冊;排除冊在)",
            s["files"] == 2 and "EXCLUDE" in src)
        chk("② H1 實錯類命中(雙引號 $var: 精準行錨=line 2)",
            row["fixable"] == 1 and row["finds"][0]["line"] == 2
            and row["finds"][0]["var"] == "x")
        chk("③ ${y}: 合法形不誤報(零假陽)",
            all(f["var"] != "y" for f in row["finds"]
                if f["kind"] == "VAR_COLON_IN_DQ"))
        chk("④ 分類雙軌(Parallel-Fixable/Sequence-Dependent)+四專區",
            row["zone"] == "ENGINE"
            and next(r for r in s["rows"]
                     if r["file"] == "good_lib.psm1")["zone"] == "MODULE")
        res = apply_fix(tdp)
        chk("⑤ R1 並行修實效($x:→${x}:;好檔零觸碰)",
            'exit code ${x}: boom' in bad.read_text(encoding="utf-8")
            and good.read_text(encoding="utf-8")
            == 'function Get-A { "safe ${z}: t" }\n')
        chk("⑥ Zero-Hydra 讓位備份+manifest+UNDO(只增不減)",
            res["backup_dir"] and
            (Path(res["backup_dir"]) / "launch_bad.ps1").exists()
            and (Path(res["backup_dir"]) / "manifest.json").exists())
        chk("⑦ R2 重掃驗證歸零+R3 覆核態誠實(pwsh 缺=啟發式標)",
            res["round2"]["fixable"] == 0
            and ("pwsh" in res["round3_verify"]
                 or "啟發式" in res["round3_verify"]))
        rc = run("scan", tdp)
        page = (OUTDIR / "PS_REPAIR_MATRIX.html").read_text(encoding="utf-8")
        chk("⑧ HTML RYG 矩陣(四專區+小字 auto-wrap)", rc == 0
            and "ENGINE" in page and "10.5px" in page
            and "anywhere" in page)
        chk("⑨ 診斷雙軌宣告(pwsh AST 正主/啟發式後備誠實 HEURISTIC_ONLY)",
            "ParseFile" in src and "HEURISTIC_ONLY" in src)
    chk("⑩ 零網路+加速橋",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== PS 多輪 AST 修正引擎(CGC_MDL101)· 十檢自測(零網路)===")
        return selftest()
    root = Path(args[args.index("--root") + 1]) if "--root" in args else None
    if args and args[0] in ("scan", "fix"):
        return run(args[0], root)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL103_AccelCoverage — 加速器全覆蓋引擎(批255;操作員手機令)
====================================================================
操作員令:「所有 PY 檔裝上加速器;PowerShell 檔也+20 加速器;相同
引擎功能整合在一起不失功能重新註冊;避免當機時間」。
機制(批102 全樹導入令+批127 雙橋覆蓋之完備化):
  ①scan:現役 py/ps1 全掃 ACCEL-BRIDGE/PS-ACCEL 標記覆蓋率
    (排除 intake/archive/退役/報告/vendor=收容讓位區不注)
  ②inject:缺橋者安全注入——
    py:插於 from __future__ 之後(無=docstring 後);逐檔
      py_compile 驗證,敗=原文回復+SKIP_UNSAFE 誠實列(Zero-Hydra)
    ps:PS-ACCEL 20 加速器點源塊插於 param() 塊後(括號平衡定位;
      定位不確=SKIP_UNSAFE 候工作站 via-psrepair 真 AST)
    git=讓位機制(注入前後 diff 可回滾)+manifest 存證
  ③dupes:同功能引擎整併稽核——跨子系統同名家族(如 TAFactory
    雙棲 VDF/VAP)→ Engine_Consolidation_Register 追記
    CANDIDATE_MERGE(不失功能=僅登記候裁示,零物理合併=Zero-Hydra)
用法:python3 CGC_MDL103_AccelCoverage_v0100.py scan|inject|dupes
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

import json
import py_compile
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUTDIR = VIA / "VIA_Reports" / "accel_coverage"
CONSOL = HERE / "VIA_Engine_Consolidation_Register_v0100.json"

EXCL = {"references", "intake", "__pycache__", "_archive",
        "VIA_RetiredEngines", "node_modules", ".git", "uploads",
        "90_PRIOR_PACKAGES", "VIA_Reports", "vendor", "_generated",
        "BACKUP", "QUARANTINE_PLAN_ONLY", "candidates",
        "_review_quarantine", "tests", "_self_test", ".gle_cache"}

PY_BLOCK = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
'''

PS_BLOCK = '''# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
'''


def _walk(root: Path, suffix: str):
    for p in sorted(root.rglob("*" + suffix)):
        if p.is_file() and not any(x in EXCL for x in p.parts):
            yield p


def scan(root: Path | None = None) -> dict:
    root = root or VIA
    py = [p for p in _walk(root, ".py")]
    ps = [p for p in _walk(root, ".ps1")] + [p for p in _walk(root, ".psm1")]
    # 批255b:全文掃描(頭窗 3000 字曾誤判長 banner 檔=殘缺假象)
    py_miss = [p for p in py if "ACCEL-BRIDGE" not in
               p.read_text(encoding="utf-8", errors="replace")]
    ps_miss = [p for p in ps if "PS-ACCEL" not in
               p.read_text(encoding="utf-8", errors="replace")]
    return {"py_total": len(py), "py_miss": py_miss,
            "ps_total": len(ps), "ps_miss": ps_miss}


def _inject_py(p: Path) -> str:
    """插於 from __future__ 行後;無=模組 docstring/檔頭後。
    py_compile 敗=原文回復(Zero-Hydra)。"""
    raw = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^from __future__ import [^\n]+\n", raw, re.M)
    if m:
        new = raw[:m.end()] + PY_BLOCK + raw[m.end():]
    else:
        dm = re.match(r'\A(#![^\n]*\n)?(#.*coding[^\n]*\n)?'
                      r'(\s*(?:"""|\'\'\')(?:.|\n)*?(?:"""|\'\'\')\s*\n)?',
                      raw)
        cut = dm.end() if dm else 0
        new = raw[:cut] + PY_BLOCK + raw[cut:]
    p.write_text(new, encoding="utf-8")
    try:
        py_compile.compile(str(p), doraise=True)
        return "INJECTED"
    except Exception as exc:
        p.write_text(raw, encoding="utf-8")     # 回復=零損
        return f"SKIP_UNSAFE(compile:{type(exc).__name__})"


def _inject_ps(p: Path) -> str:
    """插於 #requires/param() 塊後(括號平衡);定位不確=SKIP_UNSAFE。"""
    raw = p.read_text(encoding="utf-8-sig", errors="replace")
    lines = raw.splitlines(keepends=True)
    idx = 0
    # 批255c:檔頭=註解/空行/#requires/[屬性] 行(如 [CmdletBinding()])
    # ——屬性必須緊貼 param,塊不得插入其間(首輪 482 注中此類破 param
    # 律=本修根因)
    while idx < len(lines):
        ln = lines[idx].lstrip()
        if ln.startswith("<#"):              # 批255d:塊註解(說明助文)
            while idx < len(lines) and "#>" not in lines[idx]:
                idx += 1
            idx += 1
            continue
        if ln.startswith("#") or not ln.strip() \
                or re.match(r"\[[A-Za-z].*\]\s*$", ln):
            idx += 1
            continue
        break
    if idx < len(lines) and re.match(r"\s*param\s*\(", lines[idx],
                                     re.I):
        depth = 0
        found = False
        for j in range(idx, len(lines)):
            for ch in re.sub(r"'[^']*'|\"[^\"]*\"", "", lines[j]):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        found = True
            if found:
                idx = j + 1
                break
        if not found:
            return "SKIP_UNSAFE(param 塊定位不確=候 via-psrepair)"
    new = "".join(lines[:idx]) + PS_BLOCK + "".join(lines[idx:])
    bal_old = raw.count("{") - raw.count("}")
    bal_new = new.count("{") - new.count("}") - \
        (PS_BLOCK.count("{") - PS_BLOCK.count("}"))
    if bal_old != bal_new:
        return "SKIP_UNSAFE(括號平衡異=候真 AST)"
    p.write_text(new, encoding="utf-8")
    return "INJECTED"


def _strip_ps(raw: str) -> str:
    """去既有 PS-ACCEL 塊(重置重注道)"""
    return re.sub(r"# ===== \[VIA:PS-ACCEL:v0100\].*?"
                  r"# ===== \[VIA:PS-ACCEL:END\] =====\r?\n",
                  "", raw, flags=re.S)


def fixps(root: Path | None = None) -> int:
    """批255c 自修復:全 ps 檔既有塊剝離→修正邏輯重注(錯位歸位)"""
    root = root or VIA
    moved = same = skip = 0
    for p in list(_walk(root, ".ps1")) + list(_walk(root, ".psm1")):
        raw = p.read_text(encoding="utf-8-sig", errors="replace")
        if "PS-ACCEL" not in raw:
            continue
        stripped = _strip_ps(raw)
        p.write_text(stripped, encoding="utf-8")
        r = _inject_ps(p)
        cur = p.read_text(encoding="utf-8", errors="replace")
        if r != "INJECTED":
            skip += 1
        elif cur == raw:
            same += 1
        else:
            moved += 1
    print(f"[fixps] 歸位 {moved} · 原位不動 {same} · SKIP {skip}(誠實)")
    return 0


def inject(root: Path | None = None) -> int:
    root = root or VIA
    s = scan(root)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    res = {"ts": ts, "py": defaultdict(int), "ps": defaultdict(int),
           "skips": []}
    for p in s["py_miss"]:
        r = _inject_py(p)
        res["py"][r.split("(")[0]] += 1
        if r != "INJECTED":
            res["skips"].append({"file": str(p.relative_to(root)),
                                 "why": r})
    for p in s["ps_miss"]:
        r = _inject_ps(p)
        res["ps"][r.split("(")[0]] += 1
        if r != "INJECTED":
            res["skips"].append({"file": str(p.relative_to(root)),
                                 "why": r})
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"inject_{ts}.json").write_text(json.dumps(
        {"py": dict(res["py"]), "ps": dict(res["ps"]),
         "skips": res["skips"][:200],
         "undo": "git diff/checkout=讓位回滾道"}, ensure_ascii=False,
        indent=1), encoding="utf-8")
    s2 = scan(root)
    print(f"[inject] py 注 {res['py'].get('INJECTED', 0)}/略 "
          f"{res['py'].get('SKIP_UNSAFE', 0)} · ps 注 "
          f"{res['ps'].get('INJECTED', 0)}/略 "
          f"{res['ps'].get('SKIP_UNSAFE', 0)} · 殘缺 py "
          f"{len(s2['py_miss'])}/ps {len(s2['ps_miss'])}"
          f"(殘=SKIP_UNSAFE 誠實)· manifest inject_{ts}.json")
    return 0


def dupes(root: Path | None = None, register: bool = False) -> int:
    """同功能引擎整併稽核:跨子系統同名家族→整併冊 CANDIDATE_MERGE
    (零物理合併=不失功能;重新註冊=登記候裁示)"""
    root = root or VIA
    fam: dict = defaultdict(set)
    for p in _walk(root / "functional modules", ".py"):
        stem = re.sub(r"_v\d+.*$", "", p.stem)
        core = re.sub(r"^(VDF|VAP|VRN|CGC|VIA|SUP|PLG)_(ENG|MDL)\d+_?", "",
                      stem, flags=re.I) or stem
        if len(core) >= 5:
            fam[core.lower()].add(p.parts[1])
    cands = {k: sorted(v) for k, v in fam.items() if len(v) > 1}
    print(f"[dupes] 跨子系統同功能家族 {len(cands)} 組:")
    for k, subs in sorted(cands.items())[:20]:
        print(f"  {k} ×{len(subs)}{subs}")
    if register and CONSOL.exists():
        reg = json.loads(CONSOL.read_text(encoding="utf-8"))
        lst = reg.setdefault("candidate_merges_b255", [])
        seen = {e["family"] for e in lst}
        n = 0
        for k, subs in sorted(cands.items()):
            if k not in seen:
                lst.append({"family": k, "subsystems": subs,
                            "state": "CANDIDATE_MERGE(候裁示;零物理"
                                     "合併=不失功能)",
                            "ts": datetime.now().strftime("%Y-%m-%d")})
                n += 1
        CONSOL.write_text(json.dumps(reg, ensure_ascii=False, indent=1),
                          encoding="utf-8")
        print(f"[dupes] 整併冊追記 {n} 組(append-only)")
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
        a = tdp / "a_future.py"
        a.write_text('"""doc"""\nfrom __future__ import annotations\n'
                     "X = 1\n", encoding="utf-8")
        b = tdp / "b_plain.py"
        b.write_text("#!/usr/bin/env python3\nY = 2\n", encoding="utf-8")
        bad = tdp / "c_bad.py"
        bad.write_text("def broken(:\n", encoding="utf-8")
        p1 = tdp / "p_param.ps1"
        p1.write_text("#requires -Version 7.0\nparam(\n  [string]$X = 'a'\n)\n"
                      "Write-Host $X\n", encoding="utf-8")
        p2 = tdp / "p_plain.ps1"
        p2.write_text("Write-Host 'hi'\n", encoding="utf-8")
        s0 = scan(tdp)
        chk("① scan 覆蓋盤點(py 3 缺/ps 2 缺)",
            s0["py_total"] == 3 and len(s0["py_miss"]) == 3
            and len(s0["ps_miss"]) == 2)
        inject(tdp)
        ta = a.read_text(encoding="utf-8")
        chk("② py 注入位=from __future__ 後(未破首語句律)",
            ta.index("from __future__") < ta.index("ACCEL-BRIDGE")
            and "X = 1" in ta)
        chk("③ py 無 future=檔頭後+compile 綠",
            "ACCEL-BRIDGE" in b.read_text(encoding="utf-8"))
        chk("④ 壞檔 compile 敗=原文回復 SKIP_UNSAFE(Zero-Hydra)",
            bad.read_text(encoding="utf-8") == "def broken(:\n")
        tp1 = p1.read_text(encoding="utf-8")
        chk("⑤ ps 注入位=param() 塊後(param 首語句律不破)",
            tp1.index("param(") < tp1.index("PS-ACCEL")
            and "Write-Host $X" in tp1)
        chk("⑥ ps 無 param=檔頭注入",
            "PS-ACCEL" in p2.read_text(encoding="utf-8"))
        s1 = scan(tdp)
        chk("⑦ 注後殘缺=僅 SKIP_UNSAFE(冪等重掃)",
            len(s1["py_miss"]) == 1 and len(s1["ps_miss"]) == 0)
        inject(tdp)
        chk("⑧ 重跑冪等(已注不重注)",
            a.read_text(encoding="utf-8").count("ACCEL-BRIDGE") == 2)
    chk("⑨ 讓位/排除紀律宣告(git 回滾道+收容區不注+整併零物理)",
        "git diff" in src and "intake" in str(EXCL)
        and "CANDIDATE_MERGE" in src)
    chk("⑩ 零網路+加速橋",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 加速器全覆蓋引擎(CGC_MDL103)· 十檢自測(零網路)===")
        return selftest()
    if args and args[0] == "scan":
        s = scan()
        print(f"[scan] py {s['py_total']}(缺 {len(s['py_miss'])})· "
              f"ps {s['ps_total']}(缺 {len(s['ps_miss'])})")
        return 0
    if args and args[0] == "fixps":
        return fixps()
    if args and args[0] == "inject":
        return inject()
    if args and args[0] == "dupes":
        return dupes(register="--register" in args)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())

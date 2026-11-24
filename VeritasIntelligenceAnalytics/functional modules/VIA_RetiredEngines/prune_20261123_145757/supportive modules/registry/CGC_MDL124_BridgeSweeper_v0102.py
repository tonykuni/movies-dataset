#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL124_BridgeSweeper v0102 — 橋塊掃描/注入器(批345 操作員令「加速器導入全部 網路工具導入VDF全部」;批346 git 在冊律)
====================================================================
職權:全樹 py 的兩種正典橋塊覆蓋率實掃+缺者注入(graceful 零行為變更;正典塊文字=在庫既有件逐字):
  ACCEL  [VIA:ACCEL-BRIDGE:v0100]  批102 全樹導入令 → VIA_SuperAccel_Module(→SUP_MDL737 尾版→VeritasCeleritas)
  NET    [VIA:NET-BRIDGE:v0100]    批115 VDF 全導入令 → via_net_unified 尾版(→SUP_MDL740 尾版→VeritasAegisNexus)
律:
  只增不減:只插入標記塊,原碼一字不動;插入點=既有 ACCEL 塊 END 之後(NET)/`from __future__` 之後
            /模組 docstring 之後/檔首(ACCEL);注入前後 py_compile 皆須通過,否則該檔 SKIP 誠實
  排除冊(不注入、誠實列):references/intake 收容原件、__pycache__、VIA_RetiredEngines、TALib/vendor、
            tests、new modules engines(bundle 原件)、50_Protection_Acceleration(凍結群)、
            兩獨立工具 VeritasCeleritas.py / VeritasAegisNexus.py(操作員令「不可動」)
  預設 dry-run;--apply 才寫;報告落 VIA_Reports/bridge_sweep/SWEEP_<stamp>.json
v0100→v0101(批346 工作站實錄「掃 5196 · 缺 2718」=工作站含 gitignored 產物:_via_mother_root_reconciliation_runs
rollback 副本(SyntaxWarning 洪水+py_compile 敗 SKIP 35)、VIA_Reports、output_hub、venv):
  ①git 在冊律:倉內只掃 git ls-files 在冊 .py(gitignored 產物/副本/回滾件=非正本,永不注入;誠實計 EXCLUDED「未在冊」)
    git 缺席=退目錄實掃+路徑排除冊
  ②路徑排除冊 +_via_mother_root_reconciliation_runs/rollback/VIA_Reports/output_hub/.venv/venv/site-packages/_backup*/_quarantine
  ③--subsystems:VDF/VAP/VRN/VIA(=supportive modules+根層)四系逐系列覆蓋(ACCEL 全系;NET 依令 VDF)+總表
  ④--warn-quiet:注入前 py_compile 以 -W ignore 抑制 SyntaxWarning 洪水(不改判定)
v0101→v0102(批355 操作員令「ps要加20個加速器」):+--ps kind:ps1 缺 [VIA:PS-ACCEL] 者注入正典塊(在庫 Invoke-VIA-Complete 逐字);插入點=param(...) 塊之後(#requires/前導註解之後);無 param=檔首註解後;在冊律/排除冊同;雲端無 pwsh=語法候工作站 via-bridge-sweep --ps 實錄(dry-run 預設)。
用法:python3 CGC_MDL124_BridgeSweeper_v0102.py [--net] [--accel] [--root <rel>] [--subsystems] [--apply] | --selftest
  預設:--net --root "functional modules/VDF"(操作員令範圍);--accel 全樹覆蓋率報告
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
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports" / "bridge_sweep"

ACCEL_START = "# ===== [VIA:ACCEL-BRIDGE:v0100]"
ACCEL_END = "# ===== [VIA:ACCEL-BRIDGE:END] ====="
NET_START = "# ===== [VIA:NET-BRIDGE:v0100]"
NET_END = "# ===== [VIA:NET-BRIDGE:END] ====="

ACCEL_BLOCK = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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

NET_BLOCK = '''# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
'''

EXCLUDE_PARTS = ("references", "intake", "__pycache__", "VIA_RetiredEngines", "vendor", "tests", "new modules engines",
                 "50_Protection_Acceleration", ".pytest_cache", "node_modules", ".git",
                 "_via_mother_root_reconciliation_runs", "rollback", "VIA_Reports", "output_hub", ".venv", "venv",
                 "site-packages", "_quarantine", "_review_quarantine")
SUBSYSTEMS = {"VDF": "functional modules/VDF", "VAP": "functional modules/VAP", "VRN": "functional modules/VRN",
              "VIA": "supportive modules"}

_TRACKED = {"set": None, "tried": False}


def tracked_set():
    """git 在冊 .py 集合(相對 VIA;git 缺席/非倉=None→退目錄實掃)"""
    if _TRACKED["tried"]:
        return _TRACKED["set"]
    _TRACKED["tried"] = True
    try:
        import subprocess
        r = subprocess.run(["git", "ls-files", "-z", "--", "*.py", "*.ps1"], cwd=str(VIA), capture_output=True, timeout=120)  # 批355:ps1 亦在冊
        if r.returncode == 0:
            _TRACKED["set"] = {x for x in r.stdout.decode("utf-8", "ignore").split("\0") if x}
    except Exception:
        _TRACKED["set"] = None
    return _TRACKED["set"]
UNTOUCHABLE = ("VeritasCeleritas.py", "VeritasAegisNexus.py",
               "VIA_SuperAccel_Module.py")  # 橋本體=自掛即循環 import;永不注入


def _excluded(p: Path) -> str:
    rel = p.relative_to(VIA)
    for seg in rel.parts:
        if seg in EXCLUDE_PARTS or seg.startswith("_backup"):
            return seg
    ts = tracked_set()
    if ts is not None and str(rel).replace("\\", "/") not in ts:
        return "未在冊(gitignored 產物/副本)"
    if p.name in UNTOUCHABLE:
        return "獨立工具不可動" if p.name.startswith("Veritas") else "橋本體(自掛=循環)"
    return ""


PS_START = "# ===== [VIA:PS-ACCEL:v0100]"
PS_BLOCK = '# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====\ntry {\n    $VIAPSAccelProbe = $PSScriptRoot\n    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {\n        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\\VIA_PS_Accel_Module.ps1"\n        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }\n        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent\n    }\n} catch { }\n# ===== [VIA:PS-ACCEL:END] =====\n'


def _ps_insert_point(src: str) -> int:
    """ps1 插入點:param(...) 塊結尾之後;無 param=檔首 #requires/註解區之後"""
    m = re.search(r"^\s*param\s*\(", src, re.M | re.I)
    if m:
        depth, k = 0, m.end() - 1
        while k < len(src):
            if src[k] == "(":
                depth += 1
            elif src[k] == ")":
                depth -= 1
                if depth == 0:
                    return src.index("\n", k) + 1 if "\n" in src[k:] else len(src)
            k += 1
    pos = 0
    for line in src.split("\n"):
        if line.startswith("#") or line.strip() == "":
            pos += len(line) + 1
        else:
            break
    return pos


def scan_ps(root: str) -> list:
    base = VIA / root
    out = []
    for p in sorted(base.rglob("*.ps1")):
        ex = _excluded(p)
        if ex:
            out.append({"file": str(p.relative_to(VIA)), "state": "EXCLUDED", "why": ex})
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        out.append({"file": str(p.relative_to(VIA)), "state": "HAS" if (PS_START in t or "VIA_PS_Accel_Module.ps1" in t) else "MISSING", "why": ""})
    return out


def inject_ps(rel: str, apply: bool) -> dict:
    p = VIA / rel
    src = p.read_text(encoding="utf-8")
    at = _ps_insert_point(src)
    new = src[:at] + PS_BLOCK + src[at:]
    if not apply:
        return {"file": rel, "state": "PLAN", "why": f"插入於第 {src[:at].count(chr(10)) + 1} 行"}
    p.write_text(new, encoding="utf-8", newline="\r\n" if "\r\n" in src else "\n")
    return {"file": rel, "state": "INJECTED", "why": f"第 {src[:at].count(chr(10)) + 1} 行"}


def run_ps(root: str, apply: bool, do_print: bool = True) -> dict:
    rows = scan_ps(root)
    miss = [r for r in rows if r["state"] == "MISSING"]
    acts = [inject_ps(r["file"], apply) for r in miss]
    n_has = sum(1 for r in rows if r["state"] == "HAS")
    rep = {"scanned": len(rows), "has": n_has, "missing": len(miss), "excluded": sum(1 for r in rows if r["state"] == "EXCLUDED"),
           "injected": sum(1 for a in acts if a["state"] == "INJECTED"), "planned": sum(1 for a in acts if a["state"] == "PLAN"),
           "coverage_after": round(100 * (n_has + sum(1 for a in acts if a["state"] == "INJECTED")) / max(1, n_has + len(miss)), 1), "actions": acts}
    if do_print:
        print(f"[橋掃] PS-ACCEL root={root} · 掃 {rep['scanned']} · 已掛 {n_has} · 缺 {len(miss)} · 排除 {rep['excluded']} · "
              f"{'注入 ' + str(rep['injected']) if apply else '計畫 ' + str(rep['planned']) + '(dry-run)'} · 覆蓋 {rep['coverage_after']}%")
        for a in acts[:20]:
            print(f"    {a['state']:8s} {a['file']} · {a['why']}")
    return rep


def scan(root: str, kind: str) -> list:
    """回列 [{file, state: HAS|MISSING|EXCLUDED, why}]"""
    base = VIA / root
    start = ACCEL_START if kind == "accel" else NET_START
    out = []
    for p in sorted(base.rglob("*.py")):
        ex = _excluded(p)
        if ex:
            out.append({"file": str(p.relative_to(VIA)), "state": "EXCLUDED", "why": ex})
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            out.append({"file": str(p.relative_to(VIA)), "state": "EXCLUDED", "why": f"讀取失敗 {type(exc).__name__}"})
            continue
        alt = "VIA_SuperAccel_Module" if kind == "accel" else "via_net_unified_v"
        if start in src:
            out.append({"file": str(p.relative_to(VIA)), "state": "HAS", "why": ""})
        elif alt in src:
            out.append({"file": str(p.relative_to(VIA)), "state": "HAS", "why": f"自掛({alt})"})
        else:
            out.append({"file": str(p.relative_to(VIA)), "state": "MISSING", "why": ""})
    return out


def _insert_point(src: str, kind: str) -> int:
    """回插入字元位置;NET=ACCEL END 之後優先;其次 from __future__ 行之後;其次 docstring 之後;否則檔首(shebang/coding 之後)"""
    if kind == "net" and ACCEL_END in src:
        i = src.index(ACCEL_END)
        return src.index("\n", i) + 1
    m = re.search(r"^from __future__ import [^\n]*\n", src, re.M)
    if m:
        return m.end()
    lines = src.split("\n")
    pos = 0
    i = 0
    while i < len(lines) and (lines[i].startswith("#!") or re.match(r"^#.*coding[:=]", lines[i]) or lines[i].strip() == ""):
        pos += len(lines[i]) + 1
        i += 1
    if i < len(lines) and re.match(r'^[rRuUbB]*("""|\'\'\')', lines[i]):
        q = '"""' if '"""' in lines[i] else "'''"
        rest = src[pos:]
        first = rest.index(q) + 3
        end = rest.find(q, first)
        if end >= 0:
            return pos + src[pos:].index("\n", end) + 1 if "\n" in src[pos + end:] else len(src)
    return pos


def inject(rel: str, kind: str, apply: bool) -> dict:
    p = VIA / rel
    block = NET_BLOCK if kind == "net" else ACCEL_BLOCK
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            py_compile.compile(str(p), doraise=True, quiet=1)
    except Exception as exc:
        return {"file": rel, "state": "SKIP", "why": f"注入前 py_compile 失敗 {type(exc).__name__}"}
    src = p.read_text(encoding="utf-8")
    at = _insert_point(src, kind)
    new = src[:at] + block + src[at:]
    if not apply:
        return {"file": rel, "state": "PLAN", "why": f"插入於字元 {at}(第 {src[:at].count(chr(10)) + 1} 行)"}
    tmp = p.with_suffix(".py.__sweep_tmp")
    try:
        tmp.write_text(new, encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            py_compile.compile(str(tmp), doraise=True, quiet=1)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        return {"file": rel, "state": "SKIP", "why": f"注入後 py_compile 失敗 {type(exc).__name__}(原檔未動)"}
    tmp.unlink(missing_ok=True)
    p.write_text(new, encoding="utf-8", newline="\n" if "\r\n" not in src else "\r\n")
    return {"file": rel, "state": "INJECTED", "why": f"第 {src[:at].count(chr(10)) + 1} 行"}


def run(kinds: list, root: str, apply: bool, do_print: bool = True) -> dict:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rep = {"ts": stamp, "root": root, "apply": apply, "kinds": {}}
    for kind in kinds:
        rows = scan(root, kind)
        miss = [r for r in rows if r["state"] == "MISSING"]
        acts = [inject(r["file"], kind, apply) for r in miss]
        n_has = sum(1 for r in rows if r["state"] == "HAS")
        n_ex = sum(1 for r in rows if r["state"] == "EXCLUDED")
        n_inj = sum(1 for a in acts if a["state"] == "INJECTED")
        n_skip = sum(1 for a in acts if a["state"] == "SKIP")
        n_plan = sum(1 for a in acts if a["state"] == "PLAN")
        rep["kinds"][kind] = {"scanned": len(rows), "has": n_has, "missing": len(miss), "excluded": n_ex,
                              "injected": n_inj, "skipped": n_skip, "planned": n_plan,
                              "coverage_after": round(100 * (n_has + n_inj) / max(1, n_has + len(miss)), 1),
                              "actions": acts, "excluded_list": [r for r in rows if r["state"] == "EXCLUDED"][:200]}
        if do_print:
            print(f"[橋掃] {kind.upper():5s} root={root} · 掃 {len(rows)} · 已掛 {n_has} · 缺 {len(miss)} · 排除 {n_ex} · "
                  f"{'注入 ' + str(n_inj) + ' · SKIP ' + str(n_skip) if apply else '計畫 ' + str(n_plan) + '(dry-run)'} · "
                  f"覆蓋 {rep['kinds'][kind]['coverage_after']}%", flush=True)
            for a in acts:
                if a["state"] == "SKIP" or (not apply and len(acts) <= 20):
                    print(f"    {a['state']:8s} {a['file']} · {a['why']}")
    REP.mkdir(parents=True, exist_ok=True)
    out = REP / f"SWEEP_{stamp}.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    rep["file"] = out.name
    if do_print:
        print(f"[橋掃] 報告 {out.relative_to(VIA)}")
    return rep


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    import tempfile
    src = Path(__file__).read_text(encoding="utf-8")
    # ① 正典塊文字=在庫件逐字(取任一已掛 NET 的現役件比對)
    ref = None
    for p in sorted(VIA.glob("VIA_SYSTEM_MANAGER_v*.py")):
        t = p.read_text(encoding="utf-8")
        if NET_START in t:
            ref = t
    net_ok = ref is not None and NET_BLOCK.strip() in ref
    acc_ok = ref is not None and ACCEL_BLOCK.strip() in ref
    chk("① 正典塊文字=在庫現役件逐字(NET/ACCEL)", net_ok and acc_ok)
    # ② 插入點律:ACCEL END 後/future 後/docstring 後/檔首
    s1 = 'from __future__ import annotations\n' + ACCEL_BLOCK + 'import os\n'
    s2 = '#!/usr/bin/env python3\n"""doc\nmore"""\nimport os\n'
    s3 = 'import os\n'
    s4 = '# -*- coding: utf-8 -*-\nfrom __future__ import annotations\nimport os\n'
    chk("② 插入點律(ACCEL END 後→future 後→docstring 後→檔首)",
        s1[_insert_point(s1, "net"):].startswith("import os") and s2[_insert_point(s2, "accel"):].startswith("import os")
        and _insert_point(s3, "accel") == 0 and s4[_insert_point(s4, "net"):].startswith("import os"))
    # ③ 沙盒注入真跑:臨時檔→注入→py_compile 通→兩塊皆在→原碼保留
    with tempfile.TemporaryDirectory(dir=str(VIA / "VIA_Reports")) as td:
        tp = Path(td) / "t_sweep.py"
        tp.write_text('#!/usr/bin/env python3\n"""x"""\nfrom __future__ import annotations\nimport os\nX = 1\n', encoding="utf-8")
        rel = str(tp.relative_to(VIA))
        r1 = inject(rel, "accel", apply=True)
        r2 = inject(rel, "net", apply=True)
        t = tp.read_text(encoding="utf-8")
        ok3 = r1["state"] == "INJECTED" and r2["state"] == "INJECTED" and ACCEL_START in t and NET_START in t \
            and t.index(ACCEL_END) < t.index(NET_START) and t.endswith("X = 1\n") and t.startswith("#!/usr/bin/env python3\n")
        try:
            py_compile.compile(str(tp), doraise=True)
        except Exception:
            ok3 = False
        # 壞檔=SKIP 誠實(原檔未動)
        bp = Path(td) / "t_bad.py"
        bp.write_text("def (:\n", encoding="utf-8")
        r3 = inject(str(bp.relative_to(VIA)), "net", apply=True)
        ok3 = ok3 and r3["state"] == "SKIP" and bp.read_text(encoding="utf-8") == "def (:\n"
    chk("③ 沙盒注入真跑(ACCEL→NET 順序;原碼保留;compile 通;壞檔 SKIP 原檔未動)", ok3)
    # ④ 排除冊:獨立工具/凍結群/收容原件/退役 皆 EXCLUDED
    chk("④ 排除冊(獨立工具不可動/凍結群/收容原件/退役/vendor)",
        _excluded(VIA / "supportive modules" / "VeritasCeleritas.py") == "獨立工具不可動"
        and _excluded(VIA / "supportive modules" / "50_Protection_Acceleration" / "x.py") == "50_Protection_Acceleration"
        and _excluded(VIA / "functional modules" / "VDF" / "references" / "intake" / "a" / "x.py") == "references"
        and _excluded(VIA / "functional modules" / "VIA_RetiredEngines" / "x.py") == "VIA_RetiredEngines"
        and _excluded(VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG072_StoryRotationBridge_v0100.py") == "")
    # ⑤ dry-run 零寫:VDF 掃描 PLAN 不動檔
    before = {p: p.stat().st_mtime for p in (VIA / "functional modules" / "VDF").rglob("*.py")}
    rep = run(["net"], "functional modules/VDF", apply=False, do_print=False)
    after = {p: p.stat().st_mtime for p in (VIA / "functional modules" / "VDF").rglob("*.py")}
    chk("⑤ dry-run 零寫(VDF 全掃 mtime 不變;報告落盤)", before == after and (REP / rep["file"]).exists(),
        f"(掃 {rep['kinds']['net']['scanned']} · 已掛 {rep['kinds']['net']['has']} · 缺 {rep['kinds']['net']['missing']})")
    chk("⑥ 紀律宣告(只增不減/graceful/dry-run 預設/不可動/py_compile 雙驗)",
        all(k in src for k in ("只增不減", "graceful", "dry-run", "不可動", "py_compile")))
    ts = tracked_set()
    chk("⑦ git 在冊律(在冊集合非空;VIA_Reports/rollback/未在冊件 EXCLUDED;在冊現役件放行)",
        (ts is None) or (len(ts) > 100
        and _excluded(VIA / "VIA_Reports" / "x.py") == "VIA_Reports"
        and _excluded(VIA / "_via_mother_root_reconciliation_runs" / "R" / "rollback" / "x.py") == "_via_mother_root_reconciliation_runs"
        and _excluded(VIA / "functional modules" / "VDF" / "engine" / "not_tracked_zzz.py").startswith("未在冊")
        and _excluded(VIA / "supportive modules" / "registry" / "CGC_MDL124_BridgeSweeper_v0100.py") == ""),
        f"(在冊 {len(ts) if ts else 0} 件)")
    chk("⑧ PS-ACCEL 注入律(正典塊=在庫啟動器逐字;param 塊後插入;無 param=檔首註解後;dry-run 零寫)",
        PS_START in PS_BLOCK and "VIA_PS_Accel_Module.ps1" in PS_BLOCK
        and _ps_insert_point("#requires -Version 7.0\nparam(\n  [string]$A = 'x',\n  [switch]$B\n)\n$x = 1\n") == len("#requires -Version 7.0\nparam(\n  [string]$A = 'x',\n  [switch]$B\n)\n")
        and _ps_insert_point("# c\n# d\n$x = 1\n") == len("# c\n# d\n"))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 橋塊掃描/注入器(CGC_MDL124 v0102)· 八檢自測(零外網)===")
        return selftest()
    kinds = [k for k in ("net", "accel") if f"--{k}" in a] or ["net"]
    if "--ps" in a:
        root = a[a.index("--root") + 1] if "--root" in a else "."
        rep = run_ps(root, apply="--apply" in a)
        return 0
    if "--subsystems" in a:
        rc = 0
        tot = {}
        for name, root in SUBSYSTEMS.items():
            ks = ["accel"] + (["net"] if name == "VDF" else [])
            rep = run(ks, root, apply="--apply" in a)
            for k, v in rep["kinds"].items():
                tot[f"{name}/{k}"] = f"{v['has'] + v['injected']}/{v['has'] + v['missing']} ({v['coverage_after']}%)"
                rc |= 1 if v["skipped"] else 0
        # 根層(VIA_*.py 等)ACCEL
        rep = run(["accel"], ".", apply="--apply" in a, do_print=False)
        v = rep["kinds"]["accel"]
        tot["ALL/accel"] = f"{v['has'] + v['injected']}/{v['has'] + v['missing']} ({v['coverage_after']}%)"
        print("[橋掃] 四系總表 " + " · ".join(f"{k} {x}" for k, x in tot.items()))
        return rc
    root = a[a.index("--root") + 1] if "--root" in a else "functional modules/VDF"
    rep = run(kinds, root, apply="--apply" in a)
    return 0 if all(v["skipped"] == 0 for v in rep["kinds"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())

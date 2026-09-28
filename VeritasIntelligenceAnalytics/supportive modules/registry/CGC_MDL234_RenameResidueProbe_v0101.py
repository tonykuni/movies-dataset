#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL234_RenameResidueProbe v0101 — 舊檔名殘留全景探針:PS 殘留分四態(只讀)

v0100 把 .ps1 裡叫舊檔名的非註解行一律記 LIVE(64 處 / 29 支)。R21 修掉有人叫的幾支之後,舊字串照「只增不減」
留在原處、下一行改問鎖冊或命名冊——v0100 還是記 LIVE,分不出「已修」「沒人叫」「後繼已退役」。v0101 分四態:
  RESOLVED  同一支檔已經叫 Get-CeleritasToolPath(兩件工具)或 Resolve-CeleritasRenamed(改名的工具):執行期拿到的是新名
  RETIRED   舊名在命名冊的後繼只存在於 VIA_RetiredEngines(整代退役的清單,例如 VDF_MDL0xx 套件清單)
  PROTECTED 列在 Celeritas 基線冊 ps1_debt、而且至今沒接模板章的既有 .ps1(照列不動,L70)
  GENERATED 那個名字是腳本自己寫出來的檔(Set-Content,不是叫舊檔)
  ORPHAN    樹上沒有任何活檔(.ps1/.py/.cmd/.bat)叫這支腳本的名字:孤兒舊腳本,不影響任何流程
  LIVE      其餘:有人叫、而且仍會拿到舊名 → 待修(動 .ps1 要操作員批准,L70)
.py 的判法與 ARCHIVE 照 v0100。只收 VCGC 呼叫。零網路。不改任何檔。
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

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL234_RenameResidueProbe"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
VIA = _PRIOR.VIA
ENGINE = Path(__file__).stem
TOOLS = _PRIOR.TOOL_STEMS
_PROBE = _PRIOR.probe
NOT_CALLERS = ("references/", "VIA_Reports/", "VIA_RetiredEngines", "_output/", "RUN_2026", "SCOPE_COPY", "new modules engines")


def _callers(root: Path) -> dict:
    """base name of every live script/code file -> how many *other* live files mention it."""
    listed = subprocess.run(["git", "ls-files", "*.ps1", "*.py", "*.psm1", "*.cmd", "*.bat"], cwd=root,
                            capture_output=True, text=True).stdout.splitlines()
    return {f: f for f in listed if not any(s in f for s in NOT_CALLERS)}


def _called(root: Path, rel: str, files: dict) -> bool:
    base = re.sub(r"-?_?v\d{4}\.ps1$", "", Path(rel).name).replace(".ps1", "")
    out = subprocess.run(["git", "grep", "-l", "-F", base, "--"] + ["*.ps1", "*.py", "*.psm1", "*.cmd", "*.bat"],
                         cwd=root, capture_output=True, text=True).stdout.splitlines()
    return any(o != rel and o in files for o in out)


def _retired_only(canonical: str, root: Path) -> bool:
    if not canonical:
        return False
    listed = subprocess.run(["git", "ls-files", f"*{canonical}*"], cwd=root, capture_output=True, text=True).stdout.splitlines()
    return bool(listed) and all("VIA_RetiredEngines" in f for f in listed)


def _baseline_debt() -> set:
    """Celeritas baseline ps1_debt: named legacy .ps1 kept as they are (L70) → PROTECTED, not a miss to fix here."""
    hits = [p for p in HERE.glob("VIA_CeleritasPolicy_Baseline_v*.json") if re.search(r"_v\d+$", p.stem)]
    if not hits:
        return set()
    book = json.loads(max(hits, key=_vnum).read_text(encoding="utf-8"))
    return set((book.get("ps1_debt") or {}).get("files") or [])


def _generated(text: str, old: str) -> bool:
    """The script writes a file with that name itself: a matrix row '<old>.py … OK_WRITTEN', or a variable built by
    Join-Path ending in '<old>.py' that is then passed to Set-Content / Out-File."""
    if re.search(r'"' + re.escape(old) + r'\.py"[^\n]*"OK_WRITTEN"', text):
        return True
    for m in re.finditer(r'^\s*\$(\w+)\s*=\s*Join-Path[^\n]*"' + re.escape(old) + r'\.py"', text, re.M):
        if re.search(r'(Set-Content|Out-File)[^\n]*\$' + re.escape(m.group(1)) + r'\b', text):
            return True
    return False


def classify_ps(rows: list, root: Path = VIA) -> list:
    files = _callers(root)
    debt = _baseline_debt()
    text_cache, called_cache = {}, {}
    for r in rows:
        if r["kind"] != "LIVE":
            continue
        rel = r["file"]
        if rel not in text_cache:
            text_cache[rel] = (root / rel).read_text(encoding="utf-8", errors="ignore")
        text = text_cache[rel]
        if rel in debt and "VIA:PS-TEMPLATE" not in text:          # still an unjoined legacy file = debt kept as is
            r["kind"] = "PROTECTED"
            continue
        if (r["old"] in TOOLS and "Get-CeleritasToolPath" in text) or \
                (r["old"] not in TOOLS and "Resolve-CeleritasRenamed" in text):
            r["kind"] = "RESOLVED"
        elif _generated(text, r["old"]):
            r["kind"] = "GENERATED"
        elif _retired_only(r.get("now") or "", root):
            r["kind"] = "RETIRED"
        else:
            if rel not in called_cache:
                called_cache[rel] = _called(root, rel, files)
            if not called_cache[rel]:
                r["kind"] = "ORPHAN"
    return rows


def probe() -> dict:
    rep = _PROBE()
    classify_ps(rep["rows"])
    ps = [r for r in rep["rows"] if r["kind"] in ("LIVE", "RESOLVED", "RETIRED", "ORPHAN", "PROTECTED", "GENERATED", "ARCHIVE")]
    count = lambda k: sum(1 for r in ps if r["kind"] == k)
    files = lambda k: len({r["file"] for r in ps if r["kind"] == k})
    rep["ps"] = {k: count(k) for k in ("LIVE", "RESOLVED", "RETIRED", "ORPHAN", "PROTECTED", "GENERATED", "ARCHIVE")}
    rep["ps_files"] = {k: files(k) for k in ("LIVE", "RESOLVED", "RETIRED", "ORPHAN", "PROTECTED", "GENERATED", "ARCHIVE")}
    rep["door"] = ENGINE
    rep["rule"] = ("py LOAD → 出新版號改問鎖冊/正典名(L04);ps LIVE → 操作員批准後改(L70);RESOLVED 已改問冊;"
                   "RETIRED 後繼整代退役;ORPHAN 沒人叫;ARCHIVE 歸檔不動")
    return rep


_PRIOR.probe = probe


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if not args or args[0] != "probe":
        print(__doc__)
        return 0
    rep = probe()
    _PRIOR.OUT.mkdir(parents=True, exist_ok=True)
    (_PRIOR.OUT / "RENAME_RESIDUE_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("old_names", "py", "ps", "ps_files")}, ensure_ascii=False, indent=1))
    if "--json" not in args:
        for r in rep["rows"]:
            if r["kind"] in ("LOAD", "LIVE"):
                print(f"  {r['kind']:5} {r['file']}:{r['line']}  {r['old']} → {r['now']}")
    return 0


def selftest() -> int:
    import tempfile
    rc = _PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / "fixed.ps1").write_text('$a = "VeritasAegisNexus.py"\n$p = Get-CeleritasToolPath -Family network\n', encoding="utf-8")
        (root / "lonely.ps1").write_text('& python "OldTool.py"\n', encoding="utf-8")
        (root / "used.ps1").write_text('& python "OldTool.py"\n', encoding="utf-8")
        (root / "caller.ps1").write_text('& "./used.ps1"\n', encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        rows = [{"kind": "LIVE", "file": "fixed.ps1", "old": "VeritasAegisNexus", "now": "lock"},
                {"kind": "LIVE", "file": "lonely.ps1", "old": "OldTool", "now": "NewTool_v0100"},
                {"kind": "LIVE", "file": "used.ps1", "old": "OldTool", "now": "NewTool_v0100"}]
        got = {r["file"]: r["kind"] for r in classify_ps(rows, root)}
    chk("⑤ 四態:改問鎖冊 = RESOLVED · 沒人叫 = ORPHAN · 有人叫又拿舊名 = LIVE",
        got == {"fixed.ps1": "RESOLVED", "lonely.ps1": "ORPHAN", "used.ps1": "LIVE"}, str(got))
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

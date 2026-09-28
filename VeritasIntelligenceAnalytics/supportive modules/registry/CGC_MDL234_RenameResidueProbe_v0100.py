#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL234_RenameResidueProbe v0100 — 舊檔名殘留全景探針(改名後指令裡漏換的地方;只讀)

操作員 2026-09-28:「舊檔案名稱全景式檢視探針找到指令中的部分替換物遺漏」「SSOT 同義字中有」。
舊名不由本支列:
  · 命名冊 VIA_Naming_Registry_v* 的 renamed_from(舊路徑 → canonical;今天 559 個可比對的舊名)
  · 工具鎖冊 VIA_ToolVersion_Lock_v* 的 previous / removed,加上兩件工具的無版號名(用哪一版由鎖冊決定)
掃描面:
  · .py = VCGC 治理尾版(CGC_MDL149 audit 的 _tail_files,同一份排除清單),AST:import 舊名、
    字串常數裡的舊名而且那一行是在開檔/組路徑/載入/派子行程(說明字串、docstring、自測夾具不算)
  · .ps1 = 各家族尾版的非註解行,舊名帶 .py/.ps1 副檔名(真的在叫檔)
每一筆分:LOAD(.py 真的在用)· LIVE(.ps1 活指令檔)· ARCHIVE(_output / RUN_ / input/SOURCE_ / _nexuscore_ 歸檔夾)。
本支不改任何檔(L70 動 .ps1 要操作員批准;.py 照 L04 出新版號)。只收 VCGC 呼叫。零網路。

用法:
  python CGC_MDL234_RenameResidueProbe_v0100.py probe [--json]
  python CGC_MDL234_RenameResidueProbe_v0100.py --selftest
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

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "toolprobe"
ENGINE = Path(__file__).stem
USE = ("Path(", "open(", "spec_from_file_location", "with_name", "joinpath", "run_path", "import_module",
       "exec_module", "_load(", "glob(", "/ \"", "subprocess", "run(")
ARCHIVE = ("_output/", "RUN_2026", "input/SOURCE_", "_nexuscore_")
PS_SKIP = ("references/", "VIA_RetiredEngines", "new modules engines", "VIA_Reports/", "_superseded",
           "SCOPE_COPY", "VIA_Standalone_Package", "_backup")
TOOL_STEMS = ("VeritasAegisNexus", "VeritasCeleritas")


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if re.search(r"_v\d+$", p.stem)]
    return max(hits, key=_vnum) if hits else None


def old_names() -> dict:
    """old base name -> what replaced it. Read from the SSOT books, not listed here."""
    out = {}
    book = _newest(HERE, "VIA_Naming_Registry_v*.json")
    items = (json.loads(book.read_text(encoding="utf-8")).get("items") or {}) if book else {}
    for row in (items.values() if isinstance(items, dict) else items):
        if isinstance(row, dict) and row.get("renamed_from"):
            base = re.sub(r"\.(py|ps1)$", "", Path(row["renamed_from"]).name)
            if len(base) >= 6 and base != row.get("canonical"):
                out[base] = str(row.get("canonical"))
    lock = _newest(HERE, "VIA_ToolVersion_Lock_v*.json")
    data = json.loads(lock.read_text(encoding="utf-8")) if lock else {}
    for fam in ("accelerator", "network"):
        ent = data.get(fam) or {}
        now = Path(str(ent.get("path") or "")).name
        prev = Path(str((ent.get("previous") or {}).get("path") or "")).stem
        if prev and prev + ".py" != now:
            out[prev] = now
    for rel in data.get("removed") or []:
        out.setdefault(Path(rel).stem, "lock book")
    for stem in TOOL_STEMS:
        out.setdefault(stem, "鎖冊指定的版號工具(CGC_MDL233 pinned)")
    return out


def _rx(names) -> re.Pattern:
    return re.compile(r"(?<![\w-])(" + "|".join(sorted(map(re.escape, names), key=len, reverse=True)) + r")(?![\w])")


def _governed_py() -> list:
    # the newest console version that defines _tail_files itself (later versions are thin tails over it)
    console = next(p for p in sorted(HERE.glob("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"), key=_vnum, reverse=True)
                   if "def _tail_files" in p.read_text(encoding="utf-8", errors="ignore"))
    spec = importlib.util.spec_from_file_location("vcgc_tails_for_mdl234", console)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return [p for p in mod._tail_files().values() if p.suffix == ".py"]


def scan_py(files: list, names: dict) -> list:
    rx = _rx(names)
    hits = []
    for p in files:
        if p.resolve() == Path(__file__).resolve():
            continue
        src = p.read_text(encoding="utf-8", errors="replace")
        if not rx.search(src):
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            hits.append({"kind": "UNPARSED", "file": str(p.relative_to(VIA)), "line": exc.lineno or 0, "old": "", "now": ""})
            continue
        lines = src.splitlines()
        doc = {n.body[0].lineno for n in ast.walk(tree)
               if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body
               and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant)}
        selftest_at = next((n.lineno for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "selftest"), 10 ** 9)
        for n in ast.walk(tree):
            found = None
            if isinstance(n, ast.Import):
                found = next((a.name.split(".")[0] for a in n.names if a.name.split(".")[0] in names), None)
            elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in names:
                found = n.module.split(".")[0]
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.lineno not in doc and n.lineno < selftest_at:
                m = re.search(r"(?<![\w-])(" + "|".join(map(re.escape, [k for k in names if k in n.value])) + r")\.(?:py|ps1)(?![\w])", n.value) \
                    if any(k in n.value for k in names) else None
                if m and any(k in lines[n.lineno - 1] for k in USE):
                    found = m.group(1)
            if found:
                hits.append({"kind": "LOAD", "file": str(p.relative_to(VIA)), "line": n.lineno, "old": found,
                             "now": names.get(found, ""), "code": lines[n.lineno - 1].strip()[:100]})
    return hits


def _ps_tails() -> list:
    listed = subprocess.run(["git", "ls-files", "*.ps1"], cwd=VIA, capture_output=True, text=True).stdout.splitlines()
    fam = {}
    for rel in listed:
        if any(s in rel for s in PS_SKIP):
            continue
        key = (str(Path(rel).parent), re.sub(r"-?_?v\d{4}$", "", Path(rel).stem))
        fam.setdefault(key, []).append(rel)
    return [VIA / max(v) for v in fam.values()]


def scan_ps(files: list, names: dict) -> list:
    rx = re.compile(r"(?<![\w-])(" + "|".join(sorted(map(re.escape, names), key=len, reverse=True)) + r")\.(?:py|ps1)(?![\w])")
    hits = []
    for p in files:
        rel = str(p.relative_to(VIA)).replace("\\", "/")
        block = False
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            s = line.strip()
            if s.startswith("<#"):
                block = True
            if block:
                block = "#>" not in s
                continue
            if not s or s.startswith("#"):
                continue
            m = rx.search(s)
            if m:
                hits.append({"kind": "ARCHIVE" if any(a in rel for a in ARCHIVE) else "LIVE", "file": rel, "line": i,
                             "old": m.group(1), "now": names.get(m.group(1), ""), "code": s[:100]})
    return hits


def probe() -> dict:
    names = old_names()
    py = scan_py(_governed_py(), names)
    ps = scan_ps(_ps_tails(), names)
    count = lambda rows, k: sum(1 for r in rows if r["kind"] == k)
    files = lambda rows, k: len({r["file"] for r in rows if r["kind"] == k})
    return {"via": "vcgc", "door": ENGINE, "old_names": len(names),
            "py": {"LOAD": count(py, "LOAD"), "files": files(py, "LOAD"), "UNPARSED": count(py, "UNPARSED")},
            "ps": {"LIVE": count(ps, "LIVE"), "live_files": files(ps, "LIVE"), "ARCHIVE": count(ps, "ARCHIVE"),
                   "archive_files": files(ps, "ARCHIVE")},
            "rows": py + ps,
            "rule": "py LOAD → 出新版號改問鎖冊/正典名(L04);ps LIVE → 列給操作員批准後改(L70);ARCHIVE 不動(歸檔)"}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if not args or args[0] != "probe":
        print(__doc__)
        return 0
    rep = probe()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "RENAME_RESIDUE_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    brief = {k: rep[k] for k in ("old_names", "py", "ps")}
    print(json.dumps(brief if "--json" not in args else rep, ensure_ascii=False, indent=1))
    for r in rep["rows"]:
        if r["kind"] in ("LOAD", "LIVE") and "--json" not in args:
            print(f"  {r['kind']:5} {r['file']}:{r['line']}  {r['old']} → {r['now']}")
    return 0


def selftest() -> int:
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    keep = os.environ.pop("VIA_FROM_VCGC", None)
    chk("① 沒從 VCGC 進就拒", main(["probe"]) == 2)
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    names = old_names()
    chk("② 舊名讀自 SSOT(命名冊 renamed_from + 工具鎖冊),不是碼裡列的", len(names) > 500 and "VeritasAegisNexus" in names, f"{len(names)} 個")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        a, b = root / "a.py", root / "b.py"
        a.write_text('"""doc mentions OldTool.py"""\nfrom pathlib import Path\nP = Path("x") / "OldTool.py"\nnote = "OldTool.py was renamed"\n', encoding="utf-8")
        b.write_text("import OldTool\n", encoding="utf-8")
        global VIA
        saved = VIA
        VIA = root
        try:
            hits = scan_py([a, b], {"OldTool": "NewTool_v0100"})
            ps = root / "x.ps1"
            ps.write_text('# & python OldTool.py\n& python "OldTool.py"\n', encoding="utf-8")
            ps_hits = scan_ps([ps], {"OldTool": "NewTool_v0100"})
        finally:
            VIA = saved
    chk("③ .py:組路徑與 import 算;docstring 與說明字串不算", sorted((h["line"], h["kind"]) for h in hits) == [(1, "LOAD"), (3, "LOAD")],
        str([(h["file"], h["line"]) for h in hits]))
    chk("④ .ps1:註解不算,活指令算", [h["line"] for h in ps_hits] == [2])
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

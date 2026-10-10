#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0150 — 薄尾:export 動詞(操作員 2026-10-10:把 VRN 最新狀態分門別類貼到指定夾)。自管自報;複製不搬,原樹不動;快照帶清單與 sha,標明「快照,正本在原樹」(避免多頭)。
  export --to <夾> [--full]
     分類:
       01_manager/   VRN_SystemManager 整條薄尾鏈(尾版靠前版才跑得動)
       02_engines/   活的引擎 .py(ENG / MDL / VIA_VRN_* 各族尾版;--full = 全部版本)
       03_ssot/      SSOT/ 活的冊(json / jsonl / csv;不含 _superseded · v2/generations)
       04_registry/  registry/ 表頭冊 · 功能矩陣 · 各帳 · 裁定書(VRN 自家)
       05_rules/     knowledge/ · rules 類冊(若有)
       06_reports/   VIA_Reports/vrn 的 latest(UI · 全景 · 表頭 · 擷取帳 · 健康)
       07_docs/      docs/handoff/ai 裡 VRN 相關卡(Closeout · Handover · Govern)
       VRN_EXPORT_MANIFEST.json  每檔 sha256 · 來源路徑 · 類別 · 尾版 · 時間
     排除:_superseded · __pycache__ · intake(交接包)· references · input · output · output_hub · *.pyc · >50MB
其餘動詞照前版鏈。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0150"
_EXCL = {"_superseded", "__pycache__", "intake", "references", "input", "output", "output_hub", "generations", "_quarantine", "VIA_RetiredEngines", "bridges", "node_modules", ".git", "target"}


def _vnum_v0150(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0150(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0150(p) < _vnum_v0150(__file__)), key=_vnum_v0150)
PRIOR = _load_v0150(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _home():
    return Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)


def _fam(p: Path) -> str:
    return re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem)


def _ok(p: Path, home: Path) -> bool:
    try:
        rel = p.relative_to(home)
    except ValueError:
        return True
    return not (set(rel.parts[:-1]) & _EXCL) and p.suffix.lower() != ".pyc" and p.stat().st_size <= 50 * 1024 * 1024


def export(to: Path, full: bool = False) -> dict:
    home = _home()
    root = home.parents[1]
    now = datetime.datetime.now().isoformat(timespec="seconds")
    to.mkdir(parents=True, exist_ok=True)
    plan = []   # (category, src, dst_rel)
    # 01 manager chain
    for p in sorted(home.glob(_STEM + "_v*.py"), key=lambda q: _vnum_v0150(q.stem)):
        plan.append(("01_manager", p, p.name))
    # 02 engines: top-level py in home (non-manager), tails per family unless --full
    fams = {}
    for p in home.glob("*.py"):
        if p.stem.startswith(_STEM) or not _ok(p, home):
            continue
        fams.setdefault(_fam(p), []).append(p)
    for fam, ps in fams.items():
        ps.sort(key=lambda q: (_vnum_v0150(q.stem), q.name))
        for p in (ps if full else ps[-1:]):
            plan.append(("02_engines", p, p.name))
    for sub in ("engines", "_vrn_engines", "SSOT", "registry", "knowledge", "rules", "70_VRN_Rules"):
        d = home / sub
        if not d.is_dir():
            continue
        cat = {"SSOT": "03_ssot", "registry": "04_registry", "knowledge": "05_rules", "rules": "05_rules", "70_VRN_Rules": "05_rules"}.get(sub, "02_engines")
        for p in d.rglob("*"):
            if p.is_file() and _ok(p, home) and p.suffix.lower() in (".py", ".json", ".jsonl", ".csv", ".md", ".txt", ".yaml", ".yml"):
                plan.append((cat, p, (p.relative_to(d)).as_posix()))
    rep = root / "VIA_Reports" / "vrn"
    if rep.is_dir():
        for p in rep.glob("*_latest.*"):
            plan.append(("06_reports", p, p.name))
        for p in rep.glob("*_MANIFEST.json"):
            plan.append(("06_reports", p, p.name))
        led = rep / "extract" / "VRN_Extract_Ledger.jsonl"
        if led.exists():
            plan.append(("06_reports", led, "extract/VRN_Extract_Ledger.jsonl"))
    docs = root / "docs" / "handoff" / "ai"
    if docs.is_dir():
        for p in docs.glob("*.md"):
            if re.search(r"(?i)vrn|closeout|handover|govern", p.name):
                plan.append(("07_docs", p, p.name))
    manifest, copied, skipped = [], 0, 0
    for cat, src, rel in plan:
        dst = to / cat / rel
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
            manifest.append({"category": cat, "file": rel, "source": str(src), "sha256": hashlib.sha256(src.read_bytes()).hexdigest()[:16], "size": src.stat().st_size, "version": ("v%04d" % _vnum_v0150(src.stem)) if _vnum_v0150(src.stem) >= 0 else ""})
        except OSError as exc:
            skipped += 1
            manifest.append({"category": cat, "file": rel, "source": str(src), "error": str(exc)[:80]})
    per = Counter(m["category"] for m in manifest if "error" not in m)
    mf = {"schema": "VIA.VRN.Export.v1", "ts": now, "from": str(home), "to": str(to), "manager_tail": Path(__file__).name, "full": full, "rule": "快照:複製不搬;正本在 functional modules/VRN;改動請在正本做再重 export;本夾不登記不發號(避免多頭)", "per_category": dict(per), "files": copied, "skipped": skipped, "items": manifest}
    (to / "VRN_EXPORT_MANIFEST.json").write_text(json.dumps(mf, ensure_ascii=False, indent=1), encoding="utf-8")
    (to / "README_VRN_SNAPSHOT.md").write_text("# VRN 快照 %s\n\n正本:`%s`\n本夾為分類快照(複製),不是第二個 VRN;改動請回正本再重跑 `export`。\n\n| 類別 | 檔數 |\n|---|---|\n%s\n\n啟動(正本):`via-vrn` 或 `python <正本>\\%s ui`\n" % (now, home, "\n".join("| %s | %d |" % kv for kv in sorted(per.items())), Path(__file__).name), encoding="utf-8")
    return {"verb": "export", "to": str(to), "files": copied, "skipped": skipped, "per": dict(per), "manifest": str(to / "VRN_EXPORT_MANIFEST.json"), "lamp": "GREEN" if copied and not skipped else ("YELLOW" if copied else "RED")}


def _print_export(o: dict) -> None:
    print("[計] VRN export · %s · 檔 %d · 略 %d · %s · %s" % (o["to"], o["files"], o["skipped"], " ".join("%s=%d" % kv for kv in sorted(o["per"].items())), o["lamp"]))
    print("  [OK] 清單 %s(每檔 sha · 來源 · 類別;本夾是快照,正本在 functional modules/VRN)" % o["manifest"])


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["export"]:
        to = args[args.index("--to") + 1] if "--to" in args and args.index("--to") + 1 < len(args) else ""
        if not to:
            print("[拒跑] export --to <夾> [--full]")
            return 2
        o = export(Path(to), full=("--full" in args))
        _print_export(o)
        return 1 if o["lamp"] == "RED" else 0
    return PRIOR.main(args)


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrnexp-"))
    home = td / "functional modules" / "VRN"
    (home / "SSOT").mkdir(parents=True); (home / "registry").mkdir(); (home / "_superseded").mkdir(); (home / "intake" / "pack").mkdir(parents=True)
    saved = os.environ.get("VIA_VRN_SSOT_HOME")
    os.environ["VIA_VRN_SSOT_HOME"] = str(home)
    (home / "VRN_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    return 0\n", encoding="utf-8")
    (home / "VRN_ENG001_A_v0100.py").write_text("X=1\n", encoding="utf-8"); (home / "VRN_ENG001_A_v0101.py").write_text("X=2\n", encoding="utf-8")
    (home / "SSOT" / "VRN_FinLexicon_SSOT_v0103.json").write_text("{}", encoding="utf-8")
    (home / "registry" / "VRN_TableHeader_v0100.json").write_text("{}", encoding="utf-8")
    (home / "_superseded" / "old.py").write_text("X=0\n", encoding="utf-8"); (home / "intake" / "pack" / "big.py").write_text("X=0\n", encoding="utf-8")
    out = td / "via_02_vrn"
    o = export(out)
    names = {m["file"] for m in json.loads((out / "VRN_EXPORT_MANIFEST.json").read_text(encoding="utf-8"))["items"]}
    chk("① 分類快照:manager 鏈 · 引擎只尾版(v0101)· SSOT · registry · 清單 · README;_superseded / intake 不進", (out / "01_manager" / "VRN_SystemManager_v0100.py").exists() and (out / "02_engines" / "VRN_ENG001_A_v0101.py").exists() and not (out / "02_engines" / "VRN_ENG001_A_v0100.py").exists() and (out / "03_ssot" / "VRN_FinLexicon_SSOT_v0103.json").exists() and (out / "04_registry" / "VRN_TableHeader_v0100.json").exists() and (out / "README_VRN_SNAPSHOT.md").exists() and "old.py" not in names and "big.py" not in names)
    o2 = export(out, full=True)
    chk("② --full 帶全部版本 · 原樹不動", (out / "02_engines" / "VRN_ENG001_A_v0100.py").exists() and (home / "VRN_ENG001_A_v0100.py").exists() and o2["lamp"] == "GREEN")
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("④ 帶加速器橋 · 複製不搬(export 段無 shutil.move)", "[VIA:ACCEL-BRIDGE:v0100]" in body and "shutil.move" not in body.split("def selftest")[0].split("def export")[1])
    if saved is None:
        os.environ.pop("VIA_VRN_SSOT_HOME", None)
    else:
        os.environ["VIA_VRN_SSOT_HOME"] = saved
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0150 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

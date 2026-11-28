#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0310 — 薄尾(v0300–v0309 一字不動):第九輪(PR #782 Codex P2)被同層裸名匯入的重複模組不退役

v0300 的 retirement_plan 只改寫「從根算起的完整模組名」匯入;巢狀夾的重複模組(例 nested/CGC_b.py)若被別的檔用裸名
  `import CGC_b` / `from CGC_b import …` 引用(契約工作行程與調度器都支援這種寫法),它照樣把 CGC_b.py 從候選拿掉、
  那行 import 不改 → 收據 READY,候選裡的呼叫端卻 ModuleNotFoundError(Codex 重現)。
本版選擇保守那條路:呼叫 v0300 retirement_plan 前,先把「在子夾、且被任何檔用裸名匯入」的重複成員從重複群組拿掉(它就不會被退役,
  原檔與引用都照舊),再把它們補進收據 retained(reason BARE_SIBLING_IMPORT_NOT_PROVEN)。根目錄的模組裸名 = 完整名,照 v0300 原本改寫。
  retirement_plan 會就地改寫 files,所以一定要在呼叫前過濾,不在呼叫後補救。文件與 toolkit.index 改指 v0310。
其餘照 v0309 → v0300。自測零網路 · 暫存資料 · 不碰 TA-Lib · 不設同意閘。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import importlib.util
import json
import re
import sys
from pathlib import PurePosixPath, Path

VERSION = "v0310"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0309
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.V300


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_ORIG = {k: getattr(V300, k) for k in ("retirement_plan", "ENGINE_FILE", "__file__")}


def bare_imported(files: dict) -> set:
    """所有檔裡以裸名(level 0、不含點)匯入的模組名。"""
    names = set()
    for raw in files.values():
        try:
            tree = ast.parse(V300.source_text(raw)[0])
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
                names.add(n.module.split(".")[0])
    return names


def retirement_plan(cfg: dict, files: dict, index: dict, contracts: list) -> dict:
    bare = bare_imported(files)
    held, groups = [], []
    for group in index.get("exact_duplicates", []):
        keep = []
        for m in group:
            p = PurePosixPath(m)
            if len(p.parts) > 1 and p.stem in bare:
                held.append(m)
            else:
                keep.append(m)
        if len(keep) > 1:
            groups.append(keep)
    plan = _ORIG["retirement_plan"](cfg, files, dict(index, exact_duplicates=groups), contracts)
    for m in held:
        plan["retained"].append({"path": m, "reason": "BARE_SIBLING_IMPORT_NOT_PROVEN"})
    return plan


def install() -> None:
    V300.retirement_plan = retirement_plan
    V300.ENGINE_FILE = Path(__file__).name
    V300.__file__ = str(Path(__file__).resolve())


def uninstall() -> None:
    for k, v in _ORIG.items():
        setattr(V300, k, v)


install()


def _fixture():
    pure = b"def f(x):\n    return x + 1\n"
    files = {"nested/CGC_a.py": pure, "nested/CGC_b.py": pure, "nested/caller.py": b"import CGC_b\n\n\ndef g():\n    return CGC_b.f(1)\n",
             "top_a.py": pure, "top_b.py": pure, "top_caller.py": b"import top_b\n"}
    index = {"exact_duplicates": [["nested/CGC_a.py", "nested/CGC_b.py"], ["top_a.py", "top_b.py"]],
             "actions": {"a": {"path": "nested/CGC_a.py"}, "b": {"path": "nested/CGC_b.py"}, "ta": {"path": "top_a.py"}, "tb": {"path": "top_b.py"}}}
    cfg = {"fusion": {"closed_world": True, "quality": {}}}
    contracts = [{"action": a} for a in ("a", "b", "ta", "tb")]
    return cfg, files, index, contracts


def selftest() -> int:
    ok = []

    def chk(label, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + label + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存資料 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路工具橋", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    cfg, files, index, contracts = _fixture()
    old = _ORIG["retirement_plan"](cfg, files, index, contracts)
    old_caller = files["nested/caller.py"].decode()
    cfg, files2, index, contracts = _fixture()
    new = retirement_plan(cfg, files2, index, contracts)
    old_out = [e["path"] for e in old["eligible"]]
    new_out = [e["path"] for e in new["eligible"]]
    held = [r for r in new["retained"] if r["reason"] == "BARE_SIBLING_IMPORT_NOT_PROVEN"]
    chk("T2 (P2)nested/CGC_b 被同層 `import CGC_b` 引用:前版照樣退役它、caller 的 import 沒改;本版不退役、列入 retained,caller 原樣",
        "nested/CGC_b.py" in old_out and "import CGC_b" in old_caller and "nested/CGC_b.py" not in new_out
        and [r["path"] for r in held] == ["nested/CGC_b.py"] and files2["nested/caller.py"] == _fixture()[1]["nested/caller.py"],
        (old_out, new_out, held))
    chk("T3 根目錄的重複(裸名 = 完整名)照 v0300 退役並改寫 import(top_b → top_a)",
        "top_b.py" in new_out and b"top_a" in files2["top_caller.py"], (new_out, files2["top_caller.py"]))
    chk("T4 綁定 / 子行程指本檔", V300.ENGINE_FILE == Path(__file__).name and Path(V300.__file__).resolve() == Path(__file__).resolve()
        and V300.retirement_plan is retirement_plan)
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("T5 前版 v0309 自測照過(含 v0308 → v0300 原有 107 項)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

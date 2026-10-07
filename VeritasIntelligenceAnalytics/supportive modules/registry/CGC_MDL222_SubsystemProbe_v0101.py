#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL222 SubsystemProbe v0101 — 薄尾:VCGC 記號沿薄尾鏈找(座位探針與流程閘共用同一個判斷)。

v0100 → v0101(2026-10-06;操作員令「VRN 已是獨立系統、你負責;不重要或與現行程序衝突的就清」):
  v0100 的 mark 只看尾版檔面有沒有 VIA_FROM_VCGC。VDF_SystemManager v0131–v0146 是薄尾
  (PRIOR = 前一版),VCGC 入口契約寫在本體鏈(v0130),尾版檔面沒有 → VDF 被記 unmarked →
  流程閘 CGC_MDL223 擋下所有 via-vcgc run。
  本版:mark 改成「尾版自帶,或沿 PRIOR 鏈繼承」才算 GREEN;每一版都要有 PRIOR 連結才往前走,
  鏈斷就停(照舊 YELLOW)。列上記 mark_from(帶記號的那一版)。其餘(座位同步、頁、入口)照前版。
  inherited_contract() 是唯一正本:CGC_MDL223 v0102 直接用這支,不另寫一份。
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
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL222_SubsystemProbe"
CONTRACT = "VIA_FROM_VCGC"
_LINK = re.compile(r"^\s*PRIOR\s*=", re.M)


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)\.py$", str(p))
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
_SEEN_PRIOR = PRIOR.seen
FAMILIES = PRIOR.FAMILIES
SEAT = PRIOR.SEAT
PAGE = PRIOR.PAGE


def inherited_contract(folder, pattern: str, needle: str = CONTRACT):
    """尾版往舊版走:某版帶針 → 回那一版;某版沒有 PRIOR 連結(鏈斷)或走完都沒有 → None。"""
    versions = sorted((p for p in Path(folder).glob(pattern) if _vnum(p) >= 0), key=_vnum, reverse=True)
    for p in versions:
        text = p.read_text(encoding="utf-8", errors="ignore")
        if needle in text:
            return p
        if not _LINK.search(text):
            return None
    return None


def seen() -> list[dict]:
    rows = _SEEN_PRIOR()
    spec = {system: (folder, pattern) for system, folder, pattern in FAMILIES}
    for row in rows:
        if row["mark"] == "GREEN" or not row["disk"] or row["system"] not in spec:
            continue
        src = inherited_contract(*spec[row["system"]])
        if src is not None:
            row["mark"] = "GREEN"
            row["mark_from"] = src.name
            row["lamp"] = "GREEN" if row["same"] else "YELLOW"
    return rows


PRIOR.seen = seen                                   # 前版 check() 取模組全域 seen → 換上本版


def check() -> dict:
    card = PRIOR.check()
    card["door"] = Path(__file__).stem
    return card


def write_seat(rows: list[dict]) -> None:
    PRIOR.write_seat(rows)


def write_page(card: dict) -> None:
    PRIOR.write_page(card)


def main() -> int:
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {_STEM} v0101 · 薄尾自測(VCGC 記號沿 PRIOR 鏈繼承)===")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "X_SystemManager_v0100.py").write_text("import os\nos.environ.get('VIA_FROM_VCGC')\n", encoding="utf-8")
        (d / "X_SystemManager_v0101.py").write_text("PRIOR = object()\n", encoding="utf-8")
        (d / "X_SystemManager_v0102.py").write_text("PRIOR = object()\n", encoding="utf-8")
        got = inherited_contract(d, "X_SystemManager_v*.py")
        chk("① 薄尾鏈 v0102 → v0101 → v0100:繼承到本體的記號", got is not None and got.name == "X_SystemManager_v0100.py", got)
        (d / "X_SystemManager_v0101.py").write_text("x = 1\n", encoding="utf-8")
        chk("② 中間一版沒有 PRIOR(鏈斷)→ 不算繼承", inherited_contract(d, "X_SystemManager_v*.py") is None)
        (d / "Y_SystemManager_v0100.py").write_text("PRIOR = object()\n", encoding="utf-8")
        chk("③ 整條鏈都沒有記號 → 不算繼承", inherited_contract(d, "Y_SystemManager_v*.py") is None)
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    rows = {r["system"]: r for r in card["rows"]}
    chk("④ 六族記號全綠(尾版自帶或照實繼承)", all(r["mark"] == "GREEN" for r in card["rows"]),
        [(r["system"], r["mark"], r.get("mark_from", "")) for r in card["rows"]])
    chk("⑤ unmarked 清空;drift 照前版判(座位不同就同步座位,不改引擎)", card["unmarked"] == [], card["drift"])
    chk("⑥ VDF 列標出記號來源", "VDF" not in rows or rows["VDF"]["mark"] == "GREEN", rows.get("VDF", {}).get("mark_from") or "尾版自帶")
    chk("⑦ 門卡標本版", card.get("door") == Path(__file__).stem)
    good = all(ok)
    print(f"  [計] {_STEM} v0101 本版 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    if not good:
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0105 — 薄尾:名冊 prior 每次指回直接前版 · 席位恰一列(Codex #378 兩條 P2)

實測(Codex 對已併 PR #378 的審查,兩條都成立):
  · v0104 roster_next 只在名冊還沒有 prior 時補 prior;第二次啟用起尾版已帶 prior,v0104 → v0105 會把 v0105 的 prior
    留在 v0103,跳過直接前版,版號鏈斷(架構正本 snapshot 規則:prior 指回前版)。
  · v0104 席位檢查是「≤ 1 列」:家族沒有 engine 列時也放行,apply 只在有席位時改指標 —— 鎖冊換了、引擎版本冊沒有現役指標。
本版:
  ① roster_next():產下一個版號檔時 prior 一律設成直接前版(rp.name)。
  ② checks():席位檢查改成「恰一列」:0 列或多列都擋(新版先登 role=candidate;席位列缺了先補,不由 apply 默默略過)。
其餘照 v0104。只有 VCGC 能啟用。零網路。
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL233_ToolActivate"
ENGINE = Path(__file__).stem


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
BASE = _PRIOR.BASE
SEAT_CHECK = "席位恰一列(同家族 role=engine 必須正好一列;新版先登 role=candidate,席位缺了先補)"
_V0104_CHECKS = _PRIOR.checks
_V0104_ROSTER_NEXT = _PRIOR.roster_next


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def roster_next(rp: Path, prev_name: str, file_name: str) -> tuple | None:
    got = _V0104_ROSTER_NEXT(rp, prev_name, file_name)
    if got is None:
        return None
    nxt, text = got
    doc = json.loads(text)
    if isinstance(doc, dict) and doc.get("prior") != rp.name:
        doc["prior"] = rp.name
        text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    return nxt, text


def checks(family: str, file_name: str, register: dict | None = None, root: Path | None = None) -> list:
    out = _V0104_CHECKS(family, file_name, register, root)
    reg = register if register is not None else BASE._json(HERE / _PRIOR.REGISTER)
    seats = _PRIOR.seat_rows(reg, family)
    rows = [c for c in out if c.get("check") != _PRIOR.SEAT_CHECK]
    rows.append({"check": SEAT_CHECK, "ok": len(seats) == 1,
                 "detail": " / ".join(f"{r.get('code')} {r.get('file')}" for r in seats) or "無席位列(先在引擎版本冊補 role=engine 席位列)"})
    return rows


_PRIOR.roster_next = roster_next        # v0104 apply() looks it up in its own globals
BASE.checks = checks                    # plan() and the prior selftests look it up in the body


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    BASE.checks = _V0104_CHECKS          # v0104 ㉖ asserts its own checks are installed: run the chain as it was shipped
    try:
        rc = _PRIOR.selftest()
    finally:
        BASE.checks = checks             # then this tail is the one installed
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        r2 = Path(tmp) / "VIA_ToolRoster_SSOT_v0102.json"
        r2.write_text(json.dumps({"version": "VIA_ToolRoster_SSOT_v0102", "prior": "VIA_ToolRoster_SSOT_v0101.json",
                                  "tools": ["Tool_v0116.py"]}, indent=1) + "\n", encoding="utf-8")
        n3 = roster_next(r2, "Tool_v0116.py", "Tool_v0117.py")
        n3[0].write_text(n3[1], encoding="utf-8")
        n4 = roster_next(n3[0], "Tool_v0117.py", "Tool_v0118.py")
        d3, d4 = json.loads(n3[1]), json.loads(n4[1])
    chk("㉗ 名冊 prior 每次指回直接前版(v0102 → v0103 → v0104:v0104 的 prior = v0103,不停在 v0101)",
        d3.get("prior") == "VIA_ToolRoster_SSOT_v0102.json" and d4.get("prior") == "VIA_ToolRoster_SSOT_v0103.json"
        and d4.get("tools") == ["Tool_v0118.py"], (d3.get("prior"), d4.get("prior")))
    fn = _PRIOR._registered("token") or ""
    zero = next(c for c in checks("token", fn, register={"rows": []}) if c["check"] == SEAT_CHECK)
    one = next(c for c in checks("token", fn, register={"rows": [{"family": "token", "role": "engine", "file": fn, "code": "A"}]})
               if c["check"] == SEAT_CHECK)
    two = next(c for c in checks("token", fn, register={"rows": [{"family": "token", "role": "engine", "file": fn, "code": "A"},
                                                                  {"family": "token", "role": "engine", "file": fn, "code": "B"}]})
               if c["check"] == SEAT_CHECK)
    chk("㉘ 席位恰一列:0 列擋 · 1 列放行 · 2 列擋;舊的「≤ 1」檢查換掉不重複", not zero["ok"] and one["ok"] and not two["ok"]
        and sum(1 for c in checks("token", fn, register={"rows": []}) if "席位" in c["check"]) == 1, zero["detail"])
    reg = BASE._json(HERE / _PRIOR.REGISTER)
    fams = sorted(_PRIOR.FAMILIES)
    counts = {f: len(_PRIOR.seat_rows(reg, f)) for f in fams}
    chk("㉙ 實冊:鎖版六家每家正好一列席位", all(v == 1 for v in counts.values()), counts)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("㉚ 裝進本體(plan 走本版檢查 · apply 走本版名冊)· 加速器橋在 · 不碰 TA-Lib",
        BASE.checks is checks and _PRIOR.roster_next is roster_next and "VIA:ACCEL-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

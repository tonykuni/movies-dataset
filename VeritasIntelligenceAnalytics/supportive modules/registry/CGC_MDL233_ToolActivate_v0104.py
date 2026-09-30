#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0104 — 薄尾:席位唯一 · 啟用時間 activated_at(UTC)· 名冊改寫出新版號檔(不就地改)

實測(側線 2026-09-30 a,風險 R06 · R01 · R08;正本 VIA_Registry_Architecture_SSOT):
  · 引擎版本冊 token v0117 同檔兩列 engine(VIA-TOOL-0194 席位 + VIA-TOOL-0212):v0100 的閘要求候選檔「冊上已登錄」,
    apply 又把該家第一列 engine(席位)就地改成新版 —— 候選若也登成 engine,就一版兩號、席位不唯一。
    network v1652 的先例是候選登 role=candidate(VIA-TOOL-0191),席位 VIA-TOOL-0181 再由 apply 指過去。
  · apply 把名冊尾版(VIA_Accelerator_Roster_SSOT / VIA_ToolRoster_SSOT)就地字串替換 —— 已發布的版號冊被改(R01)。
  · 鎖冊只記版本、不記啟用時間(R08)。
本版:
  ① checks() 多一檢「席位唯一」:同家族 role=engine 最多一列;新版先登 role=candidate(apply 才把席位指過去)。
  ② apply():席位列照 v0100 指到新版並帶 activated_at;鎖冊該家帶 activated_at(UTC ISO)· activated_by 記本版名;
     名冊要換名時寫下一個版號檔(version 欄換成新檔名、prior 指回前版),前版一字不動。
其餘照 v0103(六家同一把尺、鎖冊格式、只有 VCGC 能啟用)。零網路。
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
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL233_ToolActivate"
ENGINE = Path(__file__).stem
REGISTER = "VIA_EngineVersion_Register_v0100.json"
ROSTERS = ("VIA_Accelerator_Roster_SSOT_v*.json", "VIA_ToolRoster_SSOT_v*.json")
SEAT_CHECK = "席位唯一(同家族 role=engine 最多一列;新版先登 role=candidate)"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
BASE = _PRIOR
while getattr(BASE, "_PRIOR", None) is not None:          # v0100 body: checks / plan / apply / main live there
    BASE = BASE._PRIOR
FAMILIES = _PRIOR.FAMILIES
_V0100_CHECKS = BASE.checks


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


# ---------------------------------------------------------------- ① seat uniqueness
def seat_rows(register: dict, family: str) -> list:
    return [r for r in register.get("rows") or [] if r.get("family") == family and r.get("role") == "engine"]


def checks(family: str, file_name: str, register: dict | None = None, root: Path | None = None) -> list:
    out = _V0100_CHECKS(family, file_name, register, root)
    reg = register if register is not None else BASE._json(HERE / REGISTER)
    seats = seat_rows(reg, family)
    out.append({"check": SEAT_CHECK, "ok": len(seats) <= 1,
                "detail": " / ".join(f"{r.get('code')} {r.get('file')}" for r in seats) or "無席位列(新家族)"})
    return out


# ---------------------------------------------------------------- ② apply: pointer + time + roster as a new version
def lock_entry(prev: dict, writes: dict, why: str, when: str) -> dict:
    same = prev.get("path") == writes["path"]              # re-activation of the same file (new bytes): keep the real previous
    previous = (prev.get("previous") if same else
                {k: prev.get(k) for k in ("version", "path", "sha256", "activated_at") if prev.get(k) is not None})
    return dict(writes, why=why, activated_by="VCGC " + ENGINE, activated_at=when, previous=previous)


def roster_next(rp: Path, prev_name: str, file_name: str) -> tuple | None:
    """(next version path, text) with the tool name replaced; None when this roster does not name the previous file."""
    text = rp.read_text(encoding="utf-8")
    if not prev_name or prev_name not in text:
        return None
    m = re.match(r"(?P<stem>.+)_v(?P<v>\d{4})\.json$", rp.name)
    nxt = rp.with_name(f"{m.group('stem')}_v{int(m.group('v')) + 1:04d}.json")
    new = text.replace(prev_name, file_name).replace(f'"{rp.stem}"', f'"{nxt.stem}"')
    doc = json.loads(new)
    if isinstance(doc, dict) and "prior" not in doc:
        doc["prior"] = rp.name
        new = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    json.loads(new)
    return nxt, new


def apply(family: str, file_name: str, why: str) -> dict:
    p = BASE.plan(family, file_name)
    if not p["ok"]:
        return p
    _stem, folder, _req, _rosters = FAMILIES[family]
    w = p["writes"]
    when = now_utc()
    lp = BASE.lock_path()
    lock = BASE._json(lp)
    prev = lock.get(family) or {}
    lock[family] = lock_entry(prev, w["lock"], why, when)
    lp.write_text(json.dumps(lock, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
    reg_p = HERE / REGISTER
    reg = json.loads(reg_p.read_text(encoding="utf-8"))
    seats = seat_rows(reg, family)
    if seats and seats[0]["file"] != file_name:
        seats[0]["file"] = file_name
        seats[0]["path"] = str((folder / file_name).relative_to(BASE.VIA)).replace("\\", "/")
        seats[0]["activated_at"] = when
        reg_p.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
    prev_name = Path(str(prev.get("path") or "")).name
    touched = []
    for glob in ROSTERS:
        rp = BASE._newest(HERE, glob)
        nxt = roster_next(rp, prev_name, file_name) if rp else None
        if nxt:
            nxt[0].write_text(nxt[1], encoding="utf-8", newline="")
            touched.append(nxt[0].name)
    p["applied"] = {"lock": lp.name, "register": reg_p.name, "rosters": touched, "previous": prev.get("version"),
                    "activated_at": when}
    p["next"] = "none"
    return p


BASE.checks = checks            # plan() and the prior selftests look these up in the body's globals
BASE.apply = apply


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    rc = _PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    fn = _PRIOR._registered("token") or ""
    two = {"rows": [{"family": "token", "role": "engine", "file": fn, "code": "A"},
                    {"family": "token", "role": "engine", "file": fn, "code": "B"}]}
    one = {"rows": [{"family": "token", "role": "engine", "file": fn, "code": "A"},
                    {"family": "token", "role": "candidate", "file": fn, "code": "B"}]}
    seat_two = next(c for c in checks("token", fn, register=two) if c["check"] == SEAT_CHECK)
    seat_one = next(c for c in checks("token", fn, register=one) if c["check"] == SEAT_CHECK)
    chk("㉒ 席位唯一:同家族兩列 engine 擋下;席位 + candidate(network v1652 先例)放行", not seat_two["ok"] and seat_one["ok"],
        f"兩列 {seat_two['detail']} · 一列 {seat_one['detail']}")
    reg = BASE._json(HERE / REGISTER)
    many = {fam: len(seat_rows(reg, fam)) for fam in {r.get("family") for r in reg.get("rows") or []}}
    chk("㉓ 實冊:每家席位最多一列(token 的 VIA-TOOL-0212 已改 candidate)", all(v <= 1 for v in many.values()), many)
    when = now_utc()
    e1 = lock_entry({"version": "v0116", "path": "p/a_v0116.py", "sha256": "s1"}, {"version": "v0117", "path": "p/a_v0117.py", "sha256": "s2"}, "w", when)
    e2 = lock_entry(e1, {"version": "v0117", "path": "p/a_v0117.py", "sha256": "s3"}, "w2", now_utc())
    chk("㉔ 鎖冊帶 activated_at(UTC 帶時區)· previous 留前版;同檔重啟用沿用真前版",
        re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$", e1["activated_at"]) and e1["previous"]["version"] == "v0116"
        and e2["previous"] == e1["previous"] and e1["activated_by"] == "VCGC " + ENGINE, e1)
    with tempfile.TemporaryDirectory() as tmp:
        rp = Path(tmp) / "VIA_ToolRoster_SSOT_v0102.json"
        rp.write_text(json.dumps({"version": "VIA_ToolRoster_SSOT_v0102", "tools": ["Tool_v0116.py"]}, indent=1) + "\n", encoding="utf-8")
        before = rp.read_bytes()
        nxt = roster_next(rp, "Tool_v0116.py", "Tool_v0117.py")
        none = roster_next(rp, "Other_v0001.py", "Other_v0002.py")
        doc = json.loads(nxt[1]) if nxt else {}
        same = rp.read_bytes() == before
    chk("㉕ 名冊換名出下一個版號檔(version 換新 · prior 指回前版),前版位元不動;沒提到的名冊不寫",
        bool(nxt) and nxt[0].name == "VIA_ToolRoster_SSOT_v0103.json" and doc.get("tools") == ["Tool_v0117.py"]
        and doc.get("version") == "VIA_ToolRoster_SSOT_v0103" and doc.get("prior") == "VIA_ToolRoster_SSOT_v0102.json"
        and same and none is None, doc)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("㉖ 裝進本體(plan / main 走本版)· 加速器橋在 · 不碰 TA-Lib",
        BASE.checks is checks and BASE.apply is apply and "VIA:ACCEL-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

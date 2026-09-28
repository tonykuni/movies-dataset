#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL225_VersionPanorama v0101 — the version ruler follows the tails.

v0100 pinned SUP_MDL737 v0108 and SUP_MDL740 v0115 by name, so the network
loader tail v0117 never showed up (the operator saw "no network version").
This tail keeps v0100's register rows and adds:
  * loaders resolved by tail glob (no pinned file name)
  * each loader tail must be a row in VIA_EngineVersion_Register (append-only)
  * VIA_ToolVersion_Lock sha must still match the engine and network files
  * the PS7 seat pairs with the newest TA-Lib-free VeritasCeleritas_v*.py
Read only. Nothing is fetched, nothing is installed, the inventory is untouched.
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
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
SUPP = VIA / "supportive modules"
LOCK = HERE / "VIA_ToolVersion_Lock_v0100.json"
PS7 = SUPP / "ps7" / "VeritasCeleritas.PS7.ps1"
ENGINE_TAG = "CGC_MDL225_VersionPanorama_v0101"
_STEM = "CGC_MDL225_VersionPanorama"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def _tail(folder: Path, stem: str) -> Path | None:
    hits = [p for p in folder.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
PRIOR = _load(PRIOR_PATH, "cgc_mdl225_prior_for_v0101")
BOOK = PRIOR.BOOK
PAGE = PRIOR.PAGE
write_page = PRIOR.write_page


def __getattr__(name):
    return getattr(PRIOR, name)


def loaders() -> dict:
    """Tail loaders by glob. The file name is never pinned here."""
    return {"accelerator": _tail(SUPP, "SUP_MDL737_SuperAccelModule"),
            "network": _tail(SUPP / "network", "SUP_MDL740_NetUnified")}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""


def engine_tail() -> Path | None:
    """Newest VeritasCeleritas_v*.py with no talib in its first 12 lines (same rule as the PS7 seat)."""
    best = None
    for p in SUPP.glob("VeritasCeleritas_v*.py"):
        if _vnum(p) < 0:
            continue
        head = "\n".join(p.read_text(encoding="utf-8", errors="ignore").splitlines()[:12])
        if re.search(r"(?i)talib", head):
            continue
        if best is None or _vnum(p) > _vnum(best):
            best = p
    return best


def extra_rows(book: dict) -> list:
    files = {r["file"] for r in book.get("rows") or []}
    rows = []
    for fam, p in loaders().items():
        ok = bool(p) and p.name in files
        rows.append({"lamp": "GREEN" if ok else "RED", "family": fam, "role": "loader tail",
                     "file": p.name if p else "ABSENT", "code": "register" if ok else "not registered",
                     "versioned": True, "exists": bool(p), "in_inventory": ok})
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.is_file() else {}
    for fam in ("accelerator", "network"):
        ent = lock.get(fam) or {}
        p = VIA.parent / ent.get("path", "") if ent.get("path") else None
        ok = bool(p) and p.is_file() and _sha(p) == ent.get("sha256")
        rows.append({"lamp": "GREEN" if ok else "RED", "family": fam, "role": "lock sha",
                     "file": (p.name if p else "ABSENT"), "code": ent.get("version", "-"),
                     "versioned": True, "exists": bool(p and p.is_file()), "in_inventory": ok})
    eng = engine_tail()
    ps7_text = PS7.read_text(encoding="utf-8", errors="ignore") if PS7.is_file() else ""
    pairs = "VeritasCeleritas_v*.py" in ps7_text and "talib" in ps7_text.lower()
    ok = bool(eng) and pairs
    rows.append({"lamp": "GREEN" if ok else "RED", "family": "accelerator", "role": "ps7 seat",
                 "file": PS7.name, "code": ("v%d" % _vnum(eng)) if eng else "-",
                 "versioned": True, "exists": PS7.is_file(), "in_inventory": ok})
    return rows


def _resolved() -> dict:
    ld = loaders()
    net = _load(ld["network"], "net_tail_panorama_v0101") if ld["network"] else None
    aegis = Path(net._resolve_aegis_path() or "").name if net and hasattr(net, "_resolve_aegis_path") else ""
    eng = engine_tail()
    return {"accelerator": eng.name if eng else "", "network": aegis,
            "accelerator_loader": ld["accelerator"].name if ld["accelerator"] else "",
            "network_loader": ld["network"].name if ld["network"] else ""}


def check() -> dict:
    card = PRIOR.check()
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    extra = extra_rows(book)
    card["rows"] = card["rows"] + extra
    card["resolved"] = _resolved()
    red = card["missing"] + [r["file"] + " (" + r["role"] + ")" for r in extra if r["lamp"] != "GREEN"]
    card["missing"] = red
    card["door"] = ENGINE_TAG
    card["lock_success"] = not red and book.get("inventory_edited") is False
    card["next"] = "none" if not red else "do not unlock; name the red file"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    write_page(card)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(ok)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    ld = loaders()
    chk("① loaders come from the tail glob", all(ld.values()), " · ".join(p.name for p in ld.values() if p))
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    rows = extra_rows(book)
    chk("② every loader tail is in the register", all(r["lamp"] == "GREEN" for r in rows if r["role"] == "loader tail"),
        " · ".join(f"{r['file']} {r['lamp']}" for r in rows if r["role"] == "loader tail"))
    chk("③ lock sha still matches engine and network", all(r["lamp"] == "GREEN" for r in rows if r["role"] == "lock sha"))
    chk("④ PS7 seat pairs with the TA-Lib-free engine tail", any(r["role"] == "ps7 seat" and r["lamp"] == "GREEN" for r in rows),
        next((r["code"] for r in rows if r["role"] == "ps7 seat"), "-"))
    fake = {"rows": [r for r in book["rows"] if r["file"] != (ld["network"].name if ld["network"] else "")]}
    chk("⑤ a loader tail missing from the register turns RED", any(r["lamp"] == "RED" and r["role"] == "loader tail" for r in extra_rows(fake)))
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    chk("⑥ denied without VIA_FROM_VCGC", denied)
    inv = PRIOR.INVENTORY
    before = inv.read_bytes() if inv.is_file() else b""
    card = check()
    chk("⑦ whole card locks and inventory untouched", card["lock_success"] and (inv.read_bytes() if inv.is_file() else b"") == before,
        ",".join(card["missing"]) or json.dumps(card["resolved"], ensure_ascii=False))
    ok = all(results)
    print(f"  {ENGINE_TAG} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

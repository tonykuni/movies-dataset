#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Field rulers tail (v0102). Phone cue words are not English names.

Merge note (2026-10-02, PR #419): cut as v0101 on an old base; main already has v0101
(rules book tail + mine). Renumbered to v0102 with the prior set to main's v0101. The patch is
applied to both v0101 and its v0100 body, so calls inside v0100 see it exactly as before.

v0100 drops titles, then still keeps ``Tel Fax`` because that pair matches
the corrected English-name pattern and is not on the title list. The phone
guard already names those words. A candidate whose every token is one of
those cues is not a name. This file does not copy a second regex.
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "CGC_MDL182_ReportFieldRulers_v0101.py"
_spec = importlib.util.spec_from_file_location("cgc_mdl182_v0101_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = vars(PRIOR).get("PRIOR", PRIOR)  # v0101 讀的 v0100 本體


def _cue_tokens(R: dict) -> set:
    raw = (((R.get("phone") or {}).get("guard") or {}).get("cue_rx") or "")
    return {w.lower() for w in re.findall(r"[A-Za-z\u4e00-\u9fff]{2,}", raw)}


def _keep_names(names: list, R: dict) -> list:
    cues = _cue_tokens(R)
    kept = []
    for name in names:
        tokens = [t.lower().rstrip(".") for t in re.split(r"[ .\-]+", name) if t]
        if tokens and all(t in cues for t in tokens):
            continue
        kept.append(name)
    return kept


def _restamp(row: dict, R: dict) -> dict:
    before = list(row.get("name_en") or [])
    after = _keep_names(before, R)
    if after == before:
        return row
    row["name_en"] = after
    if "agree" in row:
        row["agree"] = [n for n in row["agree"] if n in after]
    if not after and row.get("state") == "YELLOW" and not row.get("name_cn"):
        row["state"] = "NODATA"
    return row


_BASE_CONTACTS = BASE.contacts_of
_BASE_ANALYST = BASE.analyst_of


def contacts_of(text: str, R: dict | None = None, C: dict | None = None) -> list:
    book = R if R is not None else PRIOR.rules()
    return [_restamp(row, book) for row in _BASE_CONTACTS(text, R, C)]


def analyst_of(text: str, R: dict | None = None, C: dict | None = None) -> dict:
    book = R if R is not None else PRIOR.rules()
    row = _BASE_ANALYST(text, R, C)
    row["name_en"] = _keep_names(list(row.get("name_en") or []), book)
    row["agree"] = [n for n in (row.get("agree") or []) if n in row["name_en"]]
    return row


for _m in {id(PRIOR): PRIOR, id(BASE): BASE}.values():
    _m.contacts_of = contacts_of
    _m.analyst_of = analyst_of


def selftest() -> int:
    rc = PRIOR.selftest()
    rows = contacts_of("Senior Analyst\nTel Fax\na@kgi.com")
    names = [n for row in rows for n in row.get("name_en") or []]
    ok = rc == 0 and names == []
    print("  [OK]" if ok else "  [FAIL] cue-name " + str(names))
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())

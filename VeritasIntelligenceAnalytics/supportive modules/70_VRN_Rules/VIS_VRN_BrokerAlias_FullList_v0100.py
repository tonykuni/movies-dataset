# -*- coding: utf-8 -*-
"""
VIS_VRN_BrokerAlias_FullList_v0100
Append-only supportive helper. NO DB WRITE / NO SSOT / NO OCR.

Superset drop-in for VIS_VRN_BrokerAlias_Compatibility_v0222: re-exports the
whole v0222 surface (bridge functions included), then overrides the alias
table with the FULL 20-broker registry from VRN_BROKER_LIST_v01.json so
domestic brokers (中信/兆豐/凱基/華南/國泰/台新/統一...) and the remaining
internationals (Daiwa/Citi/CLST/GF/UBS/CLSA...) resolve too.
Evidence basis: 2026-08-05 batch run - only the four gate-listed brokers
matched; 35/60 corpus files fell to NONE.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from typing import Dict, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_BASE_PATH = os.path.join(_HERE, "VIS_VRN_BrokerAlias_Compatibility_v0222.py")
_spec = importlib.util.spec_from_file_location("vis_vrn_brokeralias_v0222_base", _BASE_PATH)
_base = importlib.util.module_from_spec(_spec)
sys.modules["vis_vrn_brokeralias_v0222_base"] = _base
_spec.loader.exec_module(_base)

# re-export every public name from the v0222 base (bridge health, smoke test, dataclass...)
globals().update({k: v for k, v in vars(_base).items() if not k.startswith("_")})
BrokerAliasResult = _base.BrokerAliasResult

# ---- full 20-broker table from the registry SSOT ----------------------------
_LIST_PATH = os.path.normpath(os.path.join(
    _HERE, "..", "..", "functional modules", "VRN", "registry", "VRN_BROKER_LIST_v01.json"))


def _load_full_table() -> Dict[str, Dict[str, object]]:
    table: Dict[str, Dict[str, object]] = {}
    with open(_LIST_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    for b in data["brokers"]:
        aliases = list(dict.fromkeys(
            [b["canonical"], b["canonical_en"]] + list(b.get("aliases", []))))
        aliases.sort(key=len, reverse=True)  # longest-first: 華南永昌 before 華南
        table[b["canonical"]] = {
            "canonical": b["canonical_en"],
            "aliases": aliases,
            "country": b.get("country", ""),
            "requires_compatibility_gate": bool(b.get("requires_compatibility_gate", False)),
        }
    return table


BROKER_ALIAS_TABLE = _load_full_table()


def def_normalize_broker_name(text: str) -> Optional[BrokerAliasResult]:
    source = text or ""
    for key, item in BROKER_ALIAS_TABLE.items():
        for alias in item["aliases"]:
            # CJK aliases: no ascii-boundary guards (dates/digits legitimately abut, e.g. 20250819兆豐).
            # ASCII aliases: letter-only boundaries so CTBC251208 matches but JP never fires inside Japan.
            if re.search(r"[㐀-鿿]", alias):
                pattern = re.escape(alias)
            else:
                pattern = rf"(?<![A-Za-z]){re.escape(alias)}(?![A-Za-z])"
            if re.search(pattern, source, re.I):
                return BrokerAliasResult(
                    raw=alias,
                    canonical=item["canonical"],
                    matched_key=key,
                    confidence=0.95 if alias in (key, item["canonical"]) else 0.88,
                    requires_compatibility_gate=bool(item["requires_compatibility_gate"]),
                    aliases=list(item["aliases"]),
                )
    return None


def def_get_broker_alias_table() -> Dict[str, Dict[str, object]]:
    return BROKER_ALIAS_TABLE


def def_smoke_test() -> bool:
    cases = {
        "GS-2317 20251205.pdf": "Goldman Sachs",
        "MS-ABF 20260518.pdf": "Morgan Stanley",
        "20250819兆豐個股報告-泓德能源(6873).pdf": "Megabank",
        "凱基投顧_1476 儒鴻_20260519.pdf": "KGI",
        "華南投顧-2606-裕民-1141202.pdf": "HuaNan",
        "統一投顧-20251209投資早報.pdf": "President",
        "Daiwa-6278 20260521.pdf": "Daiwa Securities",
        "UBS-Asia Hardware Insights 20251205.pdf": "UBS",
        "Citi-3231 20250604.pdf": "Citigroup",
        "CLST-6669 20251001.pdf": "CLST",
    }
    ok = True
    for name, want in cases.items():
        got = def_normalize_broker_name(name)
        if got is None or got.canonical != want:
            print("SMOKE FAIL:", name, "->", (got.canonical if got else None), "want", want)
            ok = False
    return ok


if __name__ == "__main__":
    print("brokers:", len(BROKER_ALIAS_TABLE))
    print("smoke:", "PASS" if def_smoke_test() else "FAIL")

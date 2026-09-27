#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF manager tail. The scrape ruler follows a loaded prior file and does not treat OFF as open.

v0116 still reads only the newest tail. This file does not fetch and does not set a consent.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "VDF_SystemManager_v0116.py"
GATE = HERE.parents[1] / "supportive modules" / "registry" / "CGC_MDL224_ScrapeGate_v0100.py"
_PRIOR_RX = re.compile(r"""PRIOR\s*=\s*HERE\s*/\s*["']([^"']+\.py)["']""")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _inherited(body) -> list[str]:
    fams, _ruler = body._tails()
    found = []
    for fam, rel in fams.items():
        path = body.VIA / rel
        if body._SCRAPE_YES_RX.search(body._src(path)):
            continue
        seen = set()
        cur = path
        for _step in range(4):
            match = _PRIOR_RX.search(body._src(cur))
            if not match:
                break
            nxt = cur.parent / match.group(1)
            if nxt in seen or not nxt.is_file():
                break
            seen.add(nxt)
            if body._SCRAPE_YES_RX.search(body._src(nxt)):
                found.append(fam)
                break
            cur = nxt
    return sorted(set(found))


def _facade():
    body = _load(PRIOR, "vdf_v0116_for_v0117")._facade()
    gate = _load(GATE, "scrape_gate_for_v0117")
    orig = body.scrape_gate_split
    orig_rows = body._launch_rows

    def scrape_gate_split(environ=None):
        card = orig(environ)
        env = os.environ if environ is None else environ
        raw = env.get("VIA_SCRAPE_CONSENT") or ""
        if raw == gate.TOKEN:
            card["value"] = "TOKEN"
        card["inherited"] = _inherited(body)
        card["accepts"] = sorted(gate.OPEN)
        card["off_is_closed"] = True
        return card

    def _launch_rows(la):
        rows = []
        split = ((la.get("consent") or {}).get("scrape_split") or {})
        for item, lamp, detail in orig_rows(la):
            if item == "閘二三把尺":
                value = split.get("value")
                still = ", ".join(split.get("blocked_direct") or []) or "-"
                inherited = ", ".join(split.get("inherited") or []) or "-"
                if value == "TOKEN" and split.get("blocked_direct"):
                    lamp = "GATED"
                elif value not in ("YES", "TOKEN"):
                    lamp = "GATED"
                detail = "值 %s · OFF 與空值都不算開 · 字面 YES 仍擋 %s · 繼承閘未進入口 %s" % (value, still, inherited)
            rows.append((item, lamp, detail))
        return rows

    body.scrape_gate_split = scrape_gate_split
    body._launch_rows = _launch_rows
    return body


def collect() -> dict:
    return _facade().collect()


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    return _load(PRIOR, "vdf_v0116_passthrough_v0117").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    body = _facade()
    card = body.scrape_gate_split()
    rows = dict((item, lamp) for item, lamp, _detail in body._launch_rows(body.read_launch(probe=False)))
    ok = (
        denied
        and "VDF_ENG054_TWDailyBackfill" in card["inherited"]
        and card["off_is_closed"] is True
        and card["value"] == "UNSET"
        and rows.get("閘二三把尺") == "GATED"
        and rows.get("同意閘") == "GATED"
    )
    print("  [OK]" if ok else "  [FAIL] " + str({"inherited": card.get("inherited"), "rows": rows.get("閘二三把尺")}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

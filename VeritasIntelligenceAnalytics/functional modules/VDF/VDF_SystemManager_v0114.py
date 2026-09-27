#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF manager tail. measure reads the nine lamps and writes the matrix page.

The law-book year is not a batch number. v0113 still owns matrix. This file does not fetch.
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PRIOR = HERE / "VDF_SystemManager_v0113.py"
BODY = HERE / "VDF_SystemManager_v0104.py"
PAGE = VIA / "VIA_Reports" / "vdf_system" / "VDF_Manager_Matrix_v0114.html"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _body():
    body = _load(BODY, "vdf_body_for_v0114")
    orig = body.read_handover

    def read_handover():
        out = orig()
        batch = str(body.read_policy().get("batch") or "")
        found = re.search(r"批(\d+)", batch)
        lawb = int(found.group(1)) if found else None
        page = dict(out.get("onepage") or {})
        page["laws_batch"] = lawb
        out["onepage"] = page
        if out.get("state") == "STALE" and "律冊" in str(out.get("why") or "") and lawb is None:
            if page.get("same") is False:
                out["why"] = "docs ONEPAGE 與倉根 VIA_HANDOVER_LATEST.md 不同一份"
            else:
                out["state"] = "GREEN"
                out["why"] = "律冊批次沒有批號，不拿年份去比一頁交接"
        return out

    body.read_handover = read_handover
    return body


def _page(rows: list[dict]) -> None:
    body = []
    for row in rows:
        body.append(
            "<tr><td class='%s'>%s</td><td>%s</td><td>%s</td></tr>"
            % (html.escape(row["lamp"].lower()), html.escape(row["lamp"]), html.escape(row["lamp_name"]), html.escape(row["why"]))
        )
    text = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>VDF Manager Matrix</title>
<style>
body{margin:0;background:#101412;color:#d7ddd8;font:12px/1.45 ui-sans-serif,sans-serif}
main{max-width:980px;margin:auto;padding:18px}
h1{font-size:16px;font-weight:600;letter-spacing:.04em;margin:0 0 10px}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid #2a332e;padding:6px 8px;text-align:left;vertical-align:top}
th{color:#8d9992;font-weight:600}
.green{color:#7dcea0;font-weight:700}.red{color:#e07a7a;font-weight:700}.stale,.nodata,.absent{color:#e0c36a;font-weight:700}
</style><main><h1>VDF SYSTEM MANAGER MATRIX</h1>
<table><tr><th>lamp</th><th>domain</th><th>why</th></tr>__ROWS__</table>
</main></html>""".replace("__ROWS__", "".join(body))
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(text, encoding="utf-8")


def measure() -> dict:
    body = _body()
    card = body.collect()
    rows = []
    for name, lamp in (card.get("lamps") or {}).items():
        domain = card.get(name) or {}
        why = str(domain.get("why") or (domain.get("chain") or {}).get("why") or domain.get("state") or "")
        rows.append({"lamp": lamp, "lamp_name": name, "why": why[:240]})
    open_rows = [row["lamp_name"] for row in rows if row["lamp"] != "GREEN"]
    out = {
        "via": "vcgc",
        "door": "VDF_SystemManager_v0114",
        "enter": "vcgc",
        "exit": "vcgc",
        "page": str(PAGE),
        "rc_name": card.get("rc_name"),
        "rows": rows,
        "open": open_rows,
        "fetched": False,
        "intake_edited": False,
        "next": "none" if not open_rows else "open lamps remain",
    }
    _page(rows)
    return out


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    if "measure" in sys.argv[1:]:
        card = measure()
        print(json.dumps(card, ensure_ascii=False, indent=1))
        if "--open" in sys.argv[1:] and PAGE.is_file():
            try:
                os.startfile(PAGE)  # type: ignore[attr-defined]
            except AttributeError:
                pass
        return 0 if not card["open"] else 2
    return _load(PRIOR, "vdf_v0113_for_v0114").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = measure()
    lamps = {row["lamp_name"]: row["lamp"] for row in card["rows"]}
    ok = denied and lamps.get("logic") == "GREEN" and lamps.get("bridge") == "GREEN" and lamps.get("tool") == "GREEN" and lamps.get("handover") == "GREEN"
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(lamps, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Page 1 via PyMuPDF, with the first error kept. Open outside the no-open gate."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ERR = {"name": ""}


def _prior():
    spec = importlib.util.spec_from_file_location("tab_report_v0101", HERE / "VRN_ENG110_TabReport_v0101.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _page1(path: Path) -> str:
    try:
        import fitz
        with fitz.open(str(path)) as doc:
            if not doc.page_count:
                return ""
            for index in range(min(doc.page_count, 5)):
                text = (doc[index].get_text("text") or "").strip()
                if text:
                    body = text[:4000]
                    return body if index == 0 else f"[p{index + 1}]\n{body}"
            return ""
    except Exception as exc:
        if not _ERR["name"]:
            _ERR["name"] = type(exc).__name__ + ": " + str(exc)[:160]
        return ""


def _open(page: Path) -> tuple[bool, str]:
    if sys.platform.startswith("win"):
        done = subprocess.call(["cmd", "/c", "start", "", str(page)])
        return done == 0, "cmd"
    import webbrowser
    return bool(webbrowser.open(page.as_uri())), "webbrowser"


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _prior()
    base = prior._prior()
    base._page1 = _page1
    _ERR["name"] = ""
    card = base.run(folder, data_root, False)
    opened, how = (False, "")
    if open_page:
        opened, how = _open(Path(card["page"]))
    card["door"] = "VRN_ENG110_TabReport_v0102"
    card["reader"] = "fitz"
    card["reader_error"] = _ERR["name"]
    card["opened"] = opened
    card["open_how"] = how
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _prior()._prior()
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["present"] else 2


def selftest() -> int:
    folder = Path("/tmp/vrn_sample_reports_v0102")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "JP-2330 20250718.pdf").write_bytes(b"not a pdf")
    card = run(folder, Path("/tmp/vrn_sample_out_v0102"), False)
    ok = card["written"] == 0 and card["opened"] is False and card["reader_error"] != "" and "2330" in Path(card["page"]).read_text(encoding="utf-8")
    print("  [OK]" if ok else "  [FAIL] " + card.get("reader_error", ""))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

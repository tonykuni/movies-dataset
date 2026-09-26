#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same three-tab report. Read page 1 with PyMuPDF, and open the page on Windows."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("tab_report_v0100", HERE / "VRN_ENG110_TabReport_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _page1(path: Path) -> str:
    try:
        import fitz
        with fitz.open(str(path)) as doc:
            if doc.page_count:
                return (doc[0].get_text("text") or "")[:4000]
    except Exception:
        pass
    return ""


def _open(page: Path) -> tuple[bool, str]:
    try:
        os.startfile(page)  # type: ignore[attr-defined]
        return True, "startfile"
    except AttributeError:
        return bool(webbrowser.open(page.as_uri())), "webbrowser"
    except Exception as exc:
        return False, type(exc).__name__


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _prior()
    prior._page1 = _page1
    card = prior.run(folder, data_root, False)
    opened, how = (False, "")
    if open_page:
        opened, how = _open(Path(card["page"]))
    card["door"] = "VRN_ENG110_TabReport_v0101"
    card["reader"] = "fitz"
    card["opened"] = opened
    card["open_how"] = how
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _prior()
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["present"] else 2


def selftest() -> int:
    folder = Path("/tmp/vrn_sample_reports_v0101")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "JP-2330 20250718.pdf").write_bytes(b"%PDF-1.1\n")
    card = run(folder, Path("/tmp/vrn_sample_out_v0101"), False)
    ok = card["written"] == 0 and card["reader"] == "fitz" and card["opened"] is False and "2330" in Path(card["page"]).read_text(encoding="utf-8")
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

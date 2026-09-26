#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panorama of the VCGC route and the prepared left/right page. Does not fetch or push."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BOOK = HERE / "VIA_VDF_FetchMatrix_v0100.json"
PAGE = VIA / "supportive modules" / "ui_support" / "VIA_UI_FetchDeck_v0100.html"
SYNC = VIA / "Invoke-VIA-VCGC-SyncAll.ps1"
CONSOLE = sorted(HERE.glob("CGC_MDL139_InputConsole_v*.py"))


def _page(book: dict) -> str:
    rows = []
    for row in book["classes"]:
        since = row["since"] or book["default_since"]
        lock = "已鎖" if row.get("locked") else "可改"
        rows.append(
            f"<tr><td><input type='checkbox' checked disabled></td><td>{row['id']}</td>"
            f"<td>{row['name']}</td><td><input value='{since}' readonly></td><td>{lock}</td></tr>"
        )
    body = "\n".join(rows)
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<title>VDF 輸入 / 顯示</title>
<style>
body {{ margin:0; background:#121418; color:#d7dde6; font:13px/1.4 "Segoe UI",sans-serif; }}
header {{ padding:10px 14px; border-bottom:1px solid #2a3140; }}
main {{ display:grid; grid-template-columns:1fr 1fr; min-height:calc(100vh - 42px); }}
section {{ padding:12px 14px; }}
section + section {{ border-left:1px solid #2a3140; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ border-bottom:1px solid #2a3140; padding:4px 6px; text-align:left; }}
input {{ background:#0e1116; color:#d7dde6; border:1px solid #3a4458; padding:2px 4px; }}
small {{ color:#8b97a8; }}
</style></head><body>
<header>VDF 對接準備 · 左輸入 / 右顯示 · 不抓數 · 不推 GitHub</header>
<main>
<section><h2>輸入</h2>
<table><tr><th>選</th><th>編碼</th><th>類別</th><th>起始</th><th>鎖</th></tr>
{body}
</table>
<p><small>預設 {book['default_since']}。個股起始只給台灣財報。要收窄輸出，改 VIA_VDF_FetchOverride_v0100.json，再跑 via-export。</small></p>
</section>
<section><h2>顯示</h2>
<p>右面板讀 export 目錄的水位與 20 列，不把整表放進這頁。</p>
<table><tr><th>輸出</th><th>檔</th></tr>
<tr><td>CSV / Google 試算表匯入</td><td>VDF_Export_gsheet.csv</td></tr>
<tr><td>JSON</td><td>VDF_Export_status.json</td></tr>
<tr><td>Markdown</td><td>VDF_Export_status.md</td></tr>
</table>
<p><small>編碼 utf-8-sig。這頁是快照，按鈕不在這裡啟動下載。</small></p>
</section>
</main></body></html>
"""


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(_page(book), encoding="utf-8")
    console = CONSOLE[-1].read_text(encoding="utf-8", errors="replace") if CONSOLE else ""
    sync = SYNC.read_text(encoding="utf-8", errors="replace") if SYNC.is_file() else ""
    gaps = []
    if "VDF-TW-EQ" not in console:
        gaps.append("console_has_no_fetch_matrix")
    if "VDF_ENG118" not in console:
        gaps.append("console_has_no_export_desk")
    if "ForwardVintageLock_v0101" not in sync:
        gaps.append("sync_missing_vintage_lock")
    if "MacroMethod_v0101" not in sync:
        gaps.append("sync_missing_macro_refresh")
    if "git push" in sync:
        gaps.append("sync_pushes")
    return {
        "via": "vcgc",
        "door": "CGC_MDL196_RouteDeck_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "page": PAGE.name,
        "classes": len(book["classes"]),
        "console": CONSOLE[-1].name if CONSOLE else None,
        "github": "pull_only",
        "gaps": gaps,
        "open": ["github_push", "watermark_table", "vrn_stays_on_mdl139"],
        "hub_edited": False,
        "intake_edited": False,
        "fetched": False,
        "pushed": False,
        "do_not": ["push from this door", "edit intake macro_ssot", "rewrite MDL139 in place", "start a download from the snapshot page"],
        "next": "none" if gaps == ["console_has_no_fetch_matrix", "console_has_no_export_desk"] else "name any extra gap",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    card = check()
    html = PAGE.read_text(encoding="utf-8")
    ok = (
        "cdn" not in html.lower()
        and "VDF-TW-EQ" in html
        and "VDF-US-MACRO" in html
        and "左" in html
        and card["github"] == "pull_only"
        and card["pushed"] is False
        and "console_has_no_fetch_matrix" in card["gaps"]
    )
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())

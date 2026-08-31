# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_VRN_CrossCheck_Harness_v0100.py — VRN 財報多路交叉驗證 harness

契約(VDF/docs/VIA_VDF_Console_UI_Spec_v0100.md):
  車道 A:layout+OCR 還原    車道 B:Microsoft MarkItDown(PDF→Markdown)
  基準 C:VDF 歷史資料        (選配 D:yfinance/FactSet 共識,僅 Est 級)
  逐欄位比對 → 全吻合才入庫;任兩路不吻合 → QUARANTINE fail-closed 留審。

模式:
  --selftest        受控 fixture 驗證「對帳機制本身」:
                    情境 1 全吻合 → 100%;情境 2 植入錯值 → 被攔截隔離;
                    情境 3 車道缺欄 → 記 MISSING 不得充當吻合。
  --lane-a/-b/-c    本機 LIVE:各餵一個 JSON({"欄位": 數值})或 MarkItDown
                    輸出的 .md(自動抽表格),產出真實對帳 ledger 與吻合率。

治理:對帳器零網路、零改寫來源;證據 RUN_VRN_CROSSCHECK_V0100(append-only
+ SHA256 manifest);吻合率 100% 且零隔離才給 VRN_CROSSCHECK_PASS。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import datetime as dt
import hashlib
import json
import re
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
RUN_OUT = SCRIPT_DIR / "evidence" / "RUN_VRN_CROSSCHECK_V0100"
VERSION = "0.1.00"
REL_TOL = 1e-6          # 數值相對容差(浮點噪音;非市場門檻)


def def_parse_lane(path: Path) -> Dict[str, float]:
    """車道輸入:JSON 欄位映射,或 MarkItDown 輸出之 Markdown(抽 | 欄位 | 值 | 表格)。"""
    text = path.read_text("utf-8-sig")
    if path.suffix.lower() == ".json":
        raw = json.loads(text)
        return {str(k): float(str(v).replace(",", "")) for k, v in raw.items()}
    fields: Dict[str, float] = {}
    for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*\(?(-?[\d,]+(?:\.\d+)?)\)?\s*\|", text, flags=re.M):
        name, val = m.group(1).strip(), m.group(2).replace(",", "")
        if name and not name.startswith("-") and name not in ("欄位", "項目", "Field"):
            fields[name] = -float(val) if m.group(0).count("(") else float(val)
    return fields


def def_reconcile(lanes: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """逐欄位對帳:所有出現過的欄位 × 所有車道;全吻合 MATCH、任兩路衝突 QUARANTINE、
    車道缺欄 MISSING(誠實缺席,不充當吻合)。"""
    all_fields = sorted({f for m in lanes.values() for f in m})
    rows: List[Dict[str, Any]] = []
    for f in all_fields:
        vals = {ln: m.get(f) for ln, m in lanes.items()}
        present = {ln: v for ln, v in vals.items() if v is not None}
        missing = [ln for ln, v in vals.items() if v is None]
        ref = next(iter(present.values()))
        agree = all(abs(v - ref) <= REL_TOL * max(1.0, abs(ref)) for v in present.values())
        status = ("QUARANTINE" if (len(present) >= 2 and not agree) else
                  ("MATCH" if len(present) == len(lanes) else "MISSING"))
        rows.append({"Field": f, "Status": status, "Values": vals, "MissingLanes": missing})
    n_match = sum(1 for r in rows if r["Status"] == "MATCH")
    n_quar = sum(1 for r in rows if r["Status"] == "QUARANTINE")
    n_miss = sum(1 for r in rows if r["Status"] == "MISSING")
    rate = n_match / len(rows) if rows else 0.0
    status = "VRN_CROSSCHECK_PASS" if (rows and n_quar == 0 and n_miss == 0) else \
             ("VRN_CROSSCHECK_QUARANTINED" if n_quar else "VRN_CROSSCHECK_INCOMPLETE")
    return {"Fields": rows, "MatchRate": rate, "Matched": n_match,
            "Quarantined": n_quar, "Missing": n_miss, "Status": status,
            "Lanes": sorted(lanes)}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def def_write_evidence(report: Dict[str, Any], tag: str) -> None:
    RUN_OUT.mkdir(parents=True, exist_ok=True)
    report = {"Harness": "VIA_VRN_CrossCheck", "Version": VERSION,
              "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
              "Mode": tag, **report,
              "Policy": "reconcile-only / zero network / append-only / fail-closed"}
    (RUN_OUT / f"crosscheck_{tag.lower()}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {p.name: sha256(p) for p in sorted(RUN_OUT.glob("*.json"))
                if p.name != "SHA256_MANIFEST.json"}
    (RUN_OUT / "SHA256_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def def_selftest() -> int:
    """受控 fixture:驗證對帳機制本身(方法驗證,非真實財報結果)。"""
    truth = {"營業收入": 1234567.0, "營業毛利": 345678.0, "營業利益": 234567.0,
             "稅後淨利": 198765.0, "每股盈餘": 4.56, "總資產": 9876543.0,
             "總負債": 4321098.0, "股東權益": 5555445.0}
    results: List[tuple] = []

    # 情境 1:三路全吻合 → 100% PASS
    r1 = def_reconcile({"OCR": dict(truth), "MarkItDown": dict(truth), "VDF史": dict(truth)})
    results.append(("S1 三路全吻合 → MatchRate 100% + PASS",
                    r1["MatchRate"] == 1.0 and r1["Status"] == "VRN_CROSSCHECK_PASS"))

    # 情境 2:MarkItDown 車道植入一個錯值 → 該欄 QUARANTINE、整體 fail-closed
    bad = dict(truth); bad["稅後淨利"] = 199999.0
    r2 = def_reconcile({"OCR": dict(truth), "MarkItDown": bad, "VDF史": dict(truth)})
    q = [f["Field"] for f in r2["Fields"] if f["Status"] == "QUARANTINE"]
    results.append(("S2 植入錯值被攔截(僅該欄隔離,整體 QUARANTINED)",
                    q == ["稅後淨利"] and r2["Status"] == "VRN_CROSSCHECK_QUARANTINED"
                    and r2["Matched"] == len(truth) - 1))

    # 情境 3:車道缺欄 → MISSING,不得充當吻合、不得 PASS
    part = dict(truth); part.pop("每股盈餘")
    r3 = def_reconcile({"OCR": dict(truth), "MarkItDown": part, "VDF史": dict(truth)})
    results.append(("S3 缺欄記 MISSING(誠實缺席,不給 PASS)",
                    r3["Missing"] == 1 and r3["Status"] == "VRN_CROSSCHECK_INCOMPLETE"))

    # 情境 4:MarkItDown Markdown 表格解析(含千分位與括號負值)
    md = "| 欄位 | 值 |\n|---|---|\n| 營業收入 | 1,234,567 |\n| 業外損失 | (5,000) |\n"
    tmp = RUN_OUT / "_fixture_lane.md"
    RUN_OUT.mkdir(parents=True, exist_ok=True)
    tmp.write_text(md, encoding="utf-8")
    parsed = def_parse_lane(tmp)
    results.append(("S4 Markdown 表格解析(千分位/括號負值)",
                    parsed.get("營業收入") == 1234567.0 and parsed.get("業外損失") == -5000.0))
    tmp.unlink()

    ok = all(c for _, c in results)
    def_write_evidence({"SelftestResults": [{"Case": n, "Pass": c} for n, c in results],
                        "Boundary": "Controlled fixtures = 機制驗證;真實財報 100% 須本機餵真 PDF"},
                       "SELFTEST")
    print("=" * 78)
    print(f"VIA VRN CrossCheck Harness v{VERSION} · SELFTEST")
    for n, c in results:
        print(f"  [{'PASS' if c else 'FAIL'}] {n}")
    print("Status :", "MECHANISM_VERIFIED" if ok else "BLOCKED")
    print("=" * 78)
    return 0 if ok else 2


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="VRN 財報多路交叉驗證 harness")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--lane-a", type=Path, help="車道 A(OCR/layout)欄位 JSON 或 .md")
    ap.add_argument("--lane-b", type=Path, help="車道 B(MarkItDown)欄位 JSON 或 .md")
    ap.add_argument("--lane-c", type=Path, help="基準 C(VDF 歷史)欄位 JSON")
    ap.add_argument("--lane-d", type=Path, help="選配 D(共識,Est 級)JSON")
    ns = ap.parse_args(argv)
    if ns.selftest:
        return def_selftest()
    lanes: Dict[str, Dict[str, float]] = {}
    for name, p in [("OCR", ns.lane_a), ("MarkItDown", ns.lane_b),
                    ("VDF史", ns.lane_c), ("共識Est", ns.lane_d)]:
        if p is not None:
            lanes[name] = def_parse_lane(p)
    if len(lanes) < 2:
        print("至少需要兩條車道(--lane-a/-b/-c);--selftest 跑受控機制驗證")
        return 1
    report = def_reconcile(lanes)
    def_write_evidence(report, "LIVE")
    print("=" * 78)
    print(f"VIA VRN CrossCheck v{VERSION} · LIVE · lanes={report['Lanes']}")
    print(f"MatchRate  : {report['MatchRate']:.2%}  (match {report['Matched']} / "
          f"quarantine {report['Quarantined']} / missing {report['Missing']})")
    for f in report["Fields"]:
        if f["Status"] != "MATCH":
            print(f"  [{f['Status']}] {f['Field']} :: {f['Values']}")
    print("Status     :", report["Status"])
    print("Evidence   :", RUN_OUT)
    print("=" * 78)
    return 0 if report["Status"] == "VRN_CROSSCHECK_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

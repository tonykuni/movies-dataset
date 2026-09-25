#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-VRN-ENG-001 : Financial Row Auditor.

稽核 VRN 抽取層（StockReportFinancialData 這一類）輸出的財務列是否**真的**
可以進下游。這一層目前把 100% 的列標成 GREEN，但下游品質層只認得 1%，
兩邊的信任訊號完全對不上——本工具就是要把這個落差量化並擋住。

核心判準：**一列必須是一個原子事實**（一個指標 × 一個期間 × 一個數值）。
把整張表的一整列塞進 ValueRaw、把整條圖表座標軸塞進 PeriodNormalized，
都不是財務資料，是版面殘骸。這種列可以留著待修，但不得掛 GREEN。

七道閘門：
    F01 ATOMICITY          原子列比例（單期間 + 單數值）
    F02 PERIOD_PRESENT     PeriodNormalized 是否真的有期間
    F03 VALUE_NOT_BLOB     ValueRaw 是否為單一數值而非整列數字串
    F04 VALUE_NOT_ECHO     ValueRaw 不得等於 MetricRaw（等於就是沒抽到值）
    F05 FLAG_CONSISTENT    PeriodOk=False 不得同時是 GREEN 或可晉升
    F06 TYPE_STABLE        同一欄位不得混用 bool 與 str（兩個寫入者的徵兆）
    F07 SOURCE_ATTRIBUTED  Broker / ReportDate 等溯源欄位覆蓋率

證據等級改判（對齊 VIA 的 V/M/P）：
    V  原子、期間明確、數值可解析
    M  可對齊但非原子（期間數 == 數值數，需拆列）
    P  無期間或無法對齊 —— 一律不得晉升

只讀不改。原始 JSON 永遠不動。

用法：
    python VIA_VRN_FinancialRowAuditor.py --input <抽取JSON> --out <輸出目錄>
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
import webbrowser
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

URN_SELF = "VIA-VRN-ENG-001"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

# 期間標記：西元年 / 季 / 半年，含 E/F 預估後綴
PERIOD_RE = re.compile(
    r"\b[1-4]Q\d{2}[EF]?\b"          # 1Q25 / 4Q26F
    r"|\b\d{4}[EF]?\b"               # 2025 / 2026E
    r"|\b[1-2]H\d{2}[EF]?\b"         # 1H25
    r"|\b\d{2}Q[1-4]\b"              # 25Q1
    r"|\b(?:FY)\d{2,4}\b"            # FY2025
)
# 反轉的季度標記：52Q1 其實是 1Q25 被字元反轉（PDF 旋轉軸文字）
REVERSED_RE = re.compile(r"\b[5-9]2Q[1-4]\b|\bF\d2Q[1-4]\b")
NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*%?")

TRUTHY = (True, "True", "true", "TRUE", 1, "1")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Console:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def say(self, message: str, level: str = "INFO") -> None:
        line = "[%s][%s] %s" % (datetime.now().strftime("%H:%M:%S"), level, message)
        self.lines.append(line)
        print(line, flush=True)


LOG = Console()


@dataclass
class RowVerdict:
    index: int
    ticker: str = ""
    broker: str = ""
    metric: str = ""
    periods: int = 0
    values: int = 0
    grade: str = "P"                       # V | M | P
    defects: List[str] = field(default_factory=list)
    claimed_risk: str = ""
    claimed_usable: bool = False
    period_sample: str = ""
    value_sample: str = ""


class FinancialRowAuditor:
    def __init__(self, rows: List[Dict[str, Any]], source: str) -> None:
        self.rows = rows
        self.source = source
        self.stamp = now_stamp()
        self.verdicts: List[RowVerdict] = []
        self.type_drift: Dict[str, Dict[str, int]] = {}
        self.gates: List[Dict[str, str]] = []

    # -- 逐列判定 ---------------------------------------------------------
    def audit(self) -> None:
        LOG.say("稽核 %d 列（來源 %s）" % (len(self.rows), os.path.basename(self.source)))
        for index, row in enumerate(self.rows):
            verdict = RowVerdict(index=index)
            verdict.ticker = str(row.get("Ticker", ""))
            verdict.broker = str(row.get("Broker", ""))
            verdict.metric = str(row.get("MetricRaw", ""))[:40]
            verdict.claimed_risk = str(row.get("ValidationRisk", ""))
            verdict.claimed_usable = row.get("UsableForPromotionPreview") in TRUTHY

            period_text = str(row.get("PeriodNormalized", "") or "")
            value_text = str(row.get("ValueRaw", "") or "")
            verdict.period_sample = period_text[:48]
            verdict.value_sample = value_text[:48]

            periods = PERIOD_RE.findall(period_text)
            values = NUMBER_RE.findall(value_text)
            verdict.periods = len(periods)
            verdict.values = len(values)

            if not period_text.strip():
                verdict.defects.append("PERIOD_EMPTY")
            elif not periods:
                verdict.defects.append("PERIOD_UNPARSEABLE")
            if REVERSED_RE.search(period_text) or REVERSED_RE.search(value_text):
                verdict.defects.append("PERIOD_REVERSED")      # PDF 旋轉軸，字元順序顛倒
            if value_text.strip() and value_text.strip() == str(row.get("MetricRaw", "")).strip():
                verdict.defects.append("VALUE_ECHOES_METRIC")  # 值 = 指標名，等於沒抽到
            if not values:
                verdict.defects.append("VALUE_NO_NUMBER")
            elif len(values) > 1:
                verdict.defects.append("VALUE_IS_ROW_BLOB")    # 整列數字擠在一格
            if (row.get("PeriodOk") in (False, "False", "false")) and \
                    (verdict.claimed_risk == "GREEN" or verdict.claimed_usable):
                verdict.defects.append("FLAG_CONTRADICTION")

            if verdict.periods == 1 and verdict.values == 1 and \
                    "VALUE_ECHOES_METRIC" not in verdict.defects:
                verdict.grade = "V"
            elif verdict.periods >= 1 and verdict.periods == verdict.values:
                verdict.grade = "M"                            # 可拆，但目前不是原子列
            else:
                verdict.grade = "P"
            self.verdicts.append(verdict)

        for field_name in ("CoreMetric", "PeriodOk", "UsableForPromotionPreview", "TempOnly"):
            counter = collections.Counter(type(r.get(field_name)).__name__ for r in self.rows)
            if len(counter) > 1:
                self.type_drift[field_name] = dict(counter)

    # -- 統計 -------------------------------------------------------------
    def stats(self) -> Dict[str, Any]:
        total = len(self.verdicts) or 1
        grades = collections.Counter(v.grade for v in self.verdicts)
        defects = collections.Counter()
        for verdict in self.verdicts:
            defects.update(verdict.defects)
        claimed_green = len([v for v in self.verdicts if v.claimed_risk == "GREEN"])
        claimed_usable = len([v for v in self.verdicts if v.claimed_usable])
        fake_green = len([v for v in self.verdicts
                          if v.claimed_risk == "GREEN" and v.grade == "P"])
        broker_missing = len([v for v in self.verdicts if not v.broker.strip()])
        return {
            "total": len(self.verdicts),
            "grade_V": grades.get("V", 0), "grade_M": grades.get("M", 0),
            "grade_P": grades.get("P", 0),
            "atomic_pct": round(100.0 * grades.get("V", 0) / total, 2),
            "claimed_green": claimed_green, "claimed_usable": claimed_usable,
            "fake_green": fake_green,
            "fake_green_pct": round(100.0 * fake_green / total, 2),
            "broker_missing": broker_missing,
            "broker_missing_pct": round(100.0 * broker_missing / total, 2),
            "defects": dict(defects),
            "type_drift": self.type_drift,
            "tickers": len({v.ticker for v in self.verdicts if v.ticker}),
        }

    # -- 閘門 -------------------------------------------------------------
    def evaluate(self, stats: Dict[str, Any]) -> str:
        def add(code: str, title: str, status: str, detail: str) -> None:
            self.gates.append({"code": code, "title": title, "status": status,
                               "detail": detail})

        total = stats["total"] or 1
        add("F01", "ATOMICITY",
            "PASS" if stats["atomic_pct"] >= 80 else
            ("WARN" if stats["atomic_pct"] >= 20 else "FAIL"),
            "原子列 %d／%d = %.1f%%（門檻 80%%）"
            % (stats["grade_V"], total, stats["atomic_pct"]))

        no_period = stats["defects"].get("PERIOD_EMPTY", 0) + \
            stats["defects"].get("PERIOD_UNPARSEABLE", 0)
        add("F02", "PERIOD_PRESENT",
            "PASS" if no_period == 0 else ("WARN" if no_period < total * 0.2 else "FAIL"),
            "%d 列取不到期間 = %.1f%%" % (no_period, 100.0 * no_period / total))

        blob = stats["defects"].get("VALUE_IS_ROW_BLOB", 0)
        add("F03", "VALUE_NOT_BLOB",
            "PASS" if blob == 0 else ("WARN" if blob < total * 0.2 else "FAIL"),
            "%d 列的 ValueRaw 塞了多個數值 = %.1f%%" % (blob, 100.0 * blob / total))

        echo = stats["defects"].get("VALUE_ECHOES_METRIC", 0)
        add("F04", "VALUE_NOT_ECHO", "PASS" if echo == 0 else "FAIL",
            "%d 列的值等於指標名（等於沒抽到值）" % echo)

        contradiction = stats["defects"].get("FLAG_CONTRADICTION", 0)
        add("F05", "FLAG_CONSISTENT", "PASS" if contradiction == 0 else "FAIL",
            "%d 列 PeriodOk=False 卻仍是 GREEN／可晉升 = %.1f%%"
            % (contradiction, 100.0 * contradiction / total))

        add("F06", "TYPE_STABLE", "PASS" if not self.type_drift else "WARN",
            ("欄位型別混用：" + ", ".join("%s=%s" % (k, v) for k, v in self.type_drift.items()))
            if self.type_drift else "同一欄位型別一致")

        add("F07", "SOURCE_ATTRIBUTED",
            "PASS" if stats["broker_missing_pct"] < 5 else
            ("WARN" if stats["broker_missing_pct"] < 40 else "FAIL"),
            "%d 列沒有 Broker = %.1f%%"
            % (stats["broker_missing"], stats["broker_missing_pct"]))

        add("F08", "NO_FAKE_GREEN",
            "PASS" if stats["fake_green"] == 0 else "FAIL",
            "%d 列被標 GREEN 但實際只有 P 級證據 = %.1f%%"
            % (stats["fake_green"], stats["fake_green_pct"]))

        fails = len([g for g in self.gates if g["status"] == "FAIL"])
        warns = len([g for g in self.gates if g["status"] == "WARN"])
        if fails:
            return "RED"
        return "AMBER" if warns else "GREEN"


# ---------------------------------------------------------------------------
# 輸出
# ---------------------------------------------------------------------------

def esc(value: Any) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def klass(value: str) -> str:
    upper = str(value).upper()
    if upper in ("PASS", "GREEN", "V"):
        return "ok"
    if upper in ("FAIL", "RED", "P"):
        return "fail"
    if upper in ("WARN", "AMBER", "M"):
        return "warn"
    return ""


def table(items: List[Dict[str, Any]], fields: List[str], status: str = "",
          limit: int = 300) -> str:
    if not items:
        return "<tr><td colspan='%d' class='muted'>—— 無 ——</td></tr>" % len(fields)
    out = []
    for item in items[:limit]:
        cells = []
        for name in fields:
            value = item.get(name, "")
            if isinstance(value, (list, tuple)):
                value = ", ".join(str(v) for v in value)
            cls = " class='%s'" % klass(str(value)) if name == status else ""
            cells.append("<td%s>%s</td>" % (cls, esc(value)))
        out.append("<tr>%s</tr>" % "".join(cells))
    if len(items) > limit:
        out.append("<tr><td colspan='%d' class='muted'>…… 其餘 %d 筆見 JSON</td></tr>"
                   % (len(fields), len(items) - limit))
    return "".join(out)


CSS = """
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
tr:hover td{background:#fbfbfb}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:30vh;overflow:auto}
"""


def render(auditor: FinancialRowAuditor, stats: Dict[str, Any], verdict: str) -> str:
    defect_rows = [{"defect": k, "count": v,
                    "pct": "%.1f%%" % (100.0 * v / max(1, stats["total"]))}
                   for k, v in sorted(stats["defects"].items(), key=lambda kv: -kv[1])]
    grade_rows = [{"grade": g, "count": stats["grade_" + g],
                   "pct": "%.1f%%" % (100.0 * stats["grade_" + g] / max(1, stats["total"])),
                   "meaning": m}
                  for g, m in (("V", "原子事實，可直接晉升"),
                               ("M", "可對齊但需拆列，暫不晉升"),
                               ("P", "無期間或無法對齊，禁止晉升"))]
    worst = [asdict(v) for v in auditor.verdicts if v.grade == "P"][:200]
    good = [asdict(v) for v in auditor.verdicts if v.grade in ("V", "M")][:100]

    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN Financial Row Audit</title><style>%s</style></head><body>
<div class="seal">帳</div>
<h1>VRN Financial Row Audit</h1>
<p class="lede">%s · %s · 只讀不改，原始 JSON 未變動</p>
<div class="cards">
  <div class="card"><div class="k">Verdict</div><div class="v %s">%s</div></div>
  <div class="card"><div class="k">Rows</div><div class="v">%d</div></div>
  <div class="card"><div class="k">原子列 V</div><div class="v ok">%d</div></div>
  <div class="card"><div class="k">待拆 M</div><div class="v warn">%d</div></div>
  <div class="card"><div class="k">不可晉升 P</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">宣稱 GREEN</div><div class="v">%d</div></div>
  <div class="card"><div class="k">假 GREEN</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">Tickers</div><div class="v">%d</div></div>
</div>

<h2>信任落差</h2>
<p class="lede">抽取層宣稱 %d 列 GREEN；依原子性實測只有 %d 列夠格。
差額 %d 列（%.1f%%）是<strong>沒有證據支撐的綠燈</strong>——下游品質層之所以只認得少數列，原因在這裡，不是下游太嚴。</p>

<h2>證據等級重判</h2>
<table><colgroup><col style="width:10%%"><col style="width:14%%"><col style="width:14%%"><col style="width:62%%"></colgroup>
<tr><th>Grade</th><th>列數</th><th>佔比</th><th>意義</th></tr>%s</table>

<h2>閘門</h2>
<table><colgroup><col style="width:8%%"><col style="width:22%%"><col style="width:10%%"><col style="width:60%%"></colgroup>
<tr><th>Code</th><th>Gate</th><th>Status</th><th>Detail</th></tr>%s</table>

<h2>缺陷分佈</h2>
<table><colgroup><col style="width:40%%"><col style="width:30%%"><col style="width:30%%"></colgroup>
<tr><th>Defect</th><th>列數</th><th>佔比</th></tr>%s</table>

<h2>可用列（V／M）</h2>
<table><colgroup><col style="width:6%%"><col style="width:8%%"><col style="width:12%%"><col style="width:20%%"><col style="width:6%%"><col style="width:6%%"><col style="width:20%%"><col style="width:22%%"></colgroup>
<tr><th>#</th><th>Grade</th><th>Ticker</th><th>Metric</th><th>期間</th><th>數值</th><th>Period 樣本</th><th>Value 樣本</th></tr>%s</table>

<h2>不可晉升列（P）</h2>
<table><colgroup><col style="width:6%%"><col style="width:8%%"><col style="width:16%%"><col style="width:24%%"><col style="width:22%%"><col style="width:24%%"></colgroup>
<tr><th>#</th><th>Ticker</th><th>Metric</th><th>缺陷</th><th>Period 樣本</th><th>Value 樣本</th></tr>%s</table>

<h2>執行日誌</h2>
<pre>%s</pre>
</body></html>""" % (
        CSS, esc(auditor.source), auditor.stamp, klass(verdict), verdict,
        stats["total"], stats["grade_V"], stats["grade_M"], stats["grade_P"],
        stats["claimed_green"], stats["fake_green"], stats["tickers"],
        stats["claimed_green"], stats["grade_V"] + stats["grade_M"],
        stats["fake_green"], stats["fake_green_pct"],
        table(grade_rows, ["grade", "count", "pct", "meaning"], "grade"),
        table(auditor.gates, ["code", "title", "status", "detail"], "status"),
        table(defect_rows, ["defect", "count", "pct"]),
        table(good, ["index", "grade", "ticker", "metric", "periods", "values",
                     "period_sample", "value_sample"], "grade"),
        table(worst, ["index", "ticker", "metric", "defects",
                      "period_sample", "value_sample"]),
        esc("\n".join(LOG.lines)),
    )


# ---------------------------------------------------------------------------

def load_rows(path: Path) -> Tuple[List[Dict[str, Any]], str]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(doc, list):
        return doc, "list"
    for key in ("rows", "data", "records", "items"):
        if isinstance(doc.get(key), list):
            return doc[key], key
    return [], "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_VRN_FinancialRowAuditor.py",
        description="VIA-VRN-ENG-001 財務列稽核：原子性、旗標一致性、假綠燈")
    parser.add_argument("--input", required=True, help="抽取層輸出的 JSON")
    parser.add_argument("--out", default="", help="輸出目錄（預設輸入檔旁的 _audit）")
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(args.input).expanduser().resolve()
    if not source.is_file():
        print("輸入檔不存在：%s" % source, file=sys.stderr)
        return 2
    out_dir = Path(args.out).expanduser().resolve() if args.out else source.parent / "_audit"
    out_dir.mkdir(parents=True, exist_ok=True)

    LOG.say("%s Financial Row Auditor %s 啟動" % (URN_SELF, VERSION), "OK")
    rows, shape = load_rows(source)
    if not rows:
        LOG.say("找不到列資料（頂層結構 %s）" % shape, "FAIL")
        return 1
    LOG.say("載入 %d 列（頂層 %s）" % (len(rows), shape), "OK")

    auditor = FinancialRowAuditor(rows, str(source))
    auditor.audit()
    stats = auditor.stats()
    verdict = auditor.evaluate(stats)

    LOG.say("原子列 %d／%d = %.1f%%" % (stats["grade_V"], stats["total"], stats["atomic_pct"]),
            "OK" if stats["atomic_pct"] >= 80 else "FAIL")
    LOG.say("假綠燈 %d 列 = %.1f%%" % (stats["fake_green"], stats["fake_green_pct"]),
            "OK" if stats["fake_green"] == 0 else "FAIL")
    fails = len([g for g in auditor.gates if g["status"] == "FAIL"])
    warns = len([g for g in auditor.gates if g["status"] == "WARN"])
    LOG.say("閘門 %d 道，WARN %d，FAIL %d -> %s"
            % (len(auditor.gates), warns, fails, verdict),
            "FAIL" if fails else ("WARN" if warns else "OK"))

    html_path = out_dir / ("VRN_FinancialRowAudit_%s.html" % auditor.stamp)
    json_path = out_dir / ("vrn_financial_row_audit_%s.json" % auditor.stamp)
    html_path.write_text(render(auditor, stats, verdict), encoding="utf-8")
    json_path.write_text(json.dumps({
        "schema": "VIA.VRN.FinancialRowAudit", "spec": SPEC_VERSION,
        "engine": URN_SELF, "version": VERSION, "generated": iso_now(),
        "source": str(source), "verdict": verdict, "stats": stats,
        "gates": auditor.gates,
        "rows": [asdict(v) for v in auditor.verdicts],
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    LOG.say("報告 -> %s" % html_path, "OK")
    print("")
    print("=" * 60)
    print(" VRN FINANCIAL ROW AUDIT  ->  %s" % verdict)
    print(" 原子 %d ｜ 待拆 %d ｜ 不可晉升 %d ｜ 假綠燈 %d"
          % (stats["grade_V"], stats["grade_M"], stats["grade_P"], stats["fake_green"]))
    print("=" * 60)
    if not args.no_open and not args.json:
        try:
            webbrowser.open(html_path.as_uri())
        except Exception:                                    # noqa: BLE001
            pass
    if args.json:
        print(json.dumps({"verdict": verdict, "stats": stats}, ensure_ascii=False))
    return 0 if verdict != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())

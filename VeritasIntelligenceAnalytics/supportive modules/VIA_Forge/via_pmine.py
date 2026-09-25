#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA PMine  ——  via_pmine.py   (\u7b2c\u56db\u652f\u5f15\u64ce / \u4e8b\u4ef6\u65e5\u8a8c\u00b7\u63a7\u7ba1\u8868\u00b7\u6d41\u7a0b\u63a2\u52d8\u00b7SSOT)
================================================================================
Veritas Intelligence Analytics \u00b7 VeritasDataForge subsystem \u00b7 \u7db1

\u628a VIA_Forge \u64f7\u53d6\u51fa\u4f86\u7684 records / \u6216\u4efb\u610f\u8cc7\u6599\u593e\uff0c\u8f49\u6210\uff1a
  A. \u4e8b\u4ef6\u65e5\u8a8c (case_id, activity, timestamp)  \u2014 PM4Py \u76f8\u5bb9
  B. \u81ea\u6f14\u5316\u898f\u5247\u5206\u985e\u5668 (\u96fb\u5b50\u696d\u5c08\u7528\uff0c\u6599\u865f/\u90e8\u9580/\u512a\u5148\u5ea6/\u671f\u9650)
  C. \u5de5\u4f5c\u63a7\u7ba1\u8868 (Excel \u689d\u4ef6\u683c\u5f0f\u00b7\u591a\u5206\u9801)
  D. \u6d41\u7a0b\u63a2\u52d8 (\u76f8\u9130\u91cd\u8907\u6298\u758a\u00b7Top-K \u8b8a\u9ad4\u00b780/20\u00b7DFG)
  E. \u81ea\u6f14\u5316 SSOT (Parquet \u5feb\u53d6\u00b7\u589e\u91cf\u878d\u5408\u00b7\u4fdd\u7559\u624b\u52d5\u72c0\u614b)

\u5168\u90e8\u512a\u96c5\u964d\u7d1a\uff1apolars\u2192pandas\uff1bparquet\u2192JSONL\uff1bpm4py\u2192\u7d14 Python DFG\u3002
\u6cbb\u7406\uff1aappend-only\uff1b\u53ea\u589e\u4e0d\u6e1b\uff1b\u898f\u5247\u6f14\u5316\u53ea\u65b0\u589e\u4e0d\u522a\u9664\u3002

CLI:
  python via_pmine.py --selftest
  python via_pmine.py --scan <dir> --context Electronics --control --mine --ssot
================================================================================
"""
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

import os
import re
import csv
import json
import importlib
from datetime import datetime, timezone, timedelta

UTC = timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, HERE)

try:
    import via_forge as _forge
except Exception:
    _forge = None


def _try(name):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _now():
    return datetime.now(UTC).isoformat()


# ============================================================ B. \u81ea\u6f14\u5316\u898f\u5247 ==
DEFAULT_CONTEXT_RULES = {
    # \u4f9d\u696d\u52d9\u60c5\u5883\u7684\u6d3b\u52d5\u62bd\u8c61\u5316 (\u964d\u566a\uff0c\u907f\u514d\u8718\u86db\u7db2\u5716) \u2014 \u53ef\u5728 registry \u64f4\u5145
    "Electronics": [
        {"theme": "\u88fd\u7a0b\u8207\u826f\u7387\u7570\u5e38", "dept": "\u88fd\u9020\u90e8", "priority": "High",
         "keywords": ["AOI", "SMT", "\u505c\u7dda", "\u4e0d\u826f", "\u91cd\u5de5", "\u6a5f\u53f0", "\u826f\u7387"]},
        {"theme": "\u5de5\u7a0b\u898f\u683c\u8b8a\u66f4 (ECR)", "dept": "\u7814\u767c\u90e8", "priority": "Medium",
         "keywords": ["ECR", "ECO", "\u8b8a\u66f4", "\u898f\u683c", "\u5716\u9762", "\u8173\u4f4d", "\u7c3d\u6838"]},
        {"theme": "\u4f9b\u61c9\u93c8\u9054\u4ea4\u8b8a\u66f4", "dept": "\u63a1\u8cfc\u90e8", "priority": "Medium",
         "keywords": ["\u9054\u4ea4", "\u4ea4\u671f", "\u77ed\u7f3a", "\u63a1\u8cfc", "\u4f9b\u61c9\u5546", "\u51fa\u8ca8"]},
        {"theme": "\u5ba2\u8a34\u8207\u54c1\u8cea\u8ffd\u8e64 (RMA)", "dept": "\u54c1\u4fdd\u90e8", "priority": "High",
         "keywords": ["RMA", "\u5ba2\u8a34", "\u9000\u8ca8", "\u6aa2\u9a57", "AQL"]},
    ],
    "ITSM": [
        {"theme": "\u4e8b\u4ef6\u8655\u7406", "dept": "IT", "priority": "High",
         "keywords": ["incident", "\u6545\u969c", "\u7570\u5e38", "down", "\u4e2d\u65b7"]},
        {"theme": "\u670d\u52d9\u8acb\u6c42", "dept": "IT", "priority": "Medium",
         "keywords": ["request", "\u7533\u8acb", "\u5b89\u88dd", "\u6b0a\u9650"]},
    ],
    "General": [],
}

PN_PATTERN = re.compile(r"(?i)(?:pn|p/n|\u6599\u865f|\u5de5\u55ae|\u55ae\u865f)[-_:\s]*([a-z0-9]{3,})")
CODE_PATTERN = re.compile(r"\b[A-Z]{2,4}-\d{3,5}\b")
DATE_PATTERN = re.compile(r"(20\d\d)[-/](\d{2})[-/](\d{2})")


class EvolvingRules:
    """\u9748\u6d3b\u898f\u5247\u5206\u985e\u5668 + \u81ea\u6f14\u5316 (append-only)\u3002"""

    def __init__(self, cfg, context="General"):
        self.cfg = cfg
        self.context = context
        pm = cfg.get("pmine", {})
        self.rules = pm.get("context_rules", DEFAULT_CONTEXT_RULES).get(context, [])
        self.evolve_threshold = pm.get("evolve_threshold", 3)
        self.registry_path = os.path.join(cfg["paths"]["ledger"],
                                          pm.get("evolve_registry", "pmine_evolve.jsonl"))
        self._unknown = {}

    def classify(self, text):
        text = text or ""
        m = PN_PATTERN.search(text)
        ticket_id = m.group(1).upper() if m else "\u65e5\u5e38\u8ffd\u8e64"
        if ticket_id == "\u65e5\u5e38\u8ffd\u8e64":
            for code in CODE_PATTERN.findall(text):
                self._unknown[code] = self._unknown.get(code, 0) + 1

        theme, dept, priority = "\u5176\u4ed6\u65e5\u5e38\u4ea4\u8fa6", "\u7ba1\u7406\u90e8", "Low"
        low = text.lower()
        for rule in self.rules:
            if any(k.lower() in low for k in rule["keywords"]):
                theme, dept, priority = rule["theme"], rule["dept"], rule["priority"]
                if priority == "Medium" and "\u6025" in text:
                    priority = "High"
                break

        dm = DATE_PATTERN.search(text)
        deadline = "%s-%s-%s" % (dm.group(1), dm.group(2), dm.group(3)) if dm else ""
        return {"ticket_id": ticket_id, "theme": theme, "department": dept,
                "priority": priority, "deadline": deadline}

    def evolving_suggestions(self):
        """\u9ad8\u983b\u672a\u5206\u985e\u4ee3\u78bc \u2192 \u5efa\u8b70\u7d0d\u5165\u8ffd\u8e64\u3002\u53ea\u5efa\u8b70/\u8a18\u9304\uff0c\u4e0d\u81ea\u52d5\u6539\u898f\u5247\u3002"""
        sug = [k for k, v in self._unknown.items() if v >= self.evolve_threshold]
        if sug:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            with open(self.registry_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"observed_at": _now(), "context": self.context,
                                    "high_freq_unclassified": sug,
                                    "counts": {k: self._unknown[k] for k in sug}},
                                   ensure_ascii=False) + "\n")
        return sug


# ============================================================ A. \u4e8b\u4ef6\u65e5\u8a8c ==
def collapse_adjacent_dupes(events):
    """\u6298\u758a\u76f8\u9130\u91cd\u8907\u4e8b\u4ef6 (\u865b\u64ec\u91cd\u5de5\u904e\u6ffe\uff0c\u5982 AOI \u9023\u8b80\u5931\u6557)\u3002"""
    out = []
    last = None
    for e in events:
        key = (e["case_id"], e["activity"])
        if key != last:
            out.append(e)
            last = key
    return out


class EventLogBuilder:
    def __init__(self, cfg, context="General"):
        self.cfg = cfg
        self.context = context
        self.rules = EvolvingRules(cfg, context)

    def from_forge_records(self, records):
        """VIA_Forge records \u2192 \u4e8b\u4ef6\u65e5\u8a8c\u3002case_id \u512a\u5148\u7528\u6599\u865f/\u55ae\u865f\uff0c
        activity \u7528\u4e3b\u984c\uff0ctimestamp \u7528\u6a94\u6848\u8655\u7406/\u4fee\u6539\u6642\u9593\u3002"""
        events = []
        for r in records:
            if r.get("status") != "OK":
                continue
            text = " ".join([r.get("file_name", ""),
                             " ".join(r.get("aspects", {}).get("keywords", [])),
                             r.get("text_preview", "")])
            c = self.rules.classify(text)
            case_id = c["ticket_id"] if c["ticket_id"] != "\u65e5\u5e38\u8ffd\u8e64" else \
                (r.get("aspects", {}).get("content_domain") or "GENERAL")
            ts = r.get("modified_time") or r.get("processed_at") or _now()
            events.append({
                "case_id": str(case_id), "activity": c["theme"], "timestamp": ts,
                "doc_id": r.get("doc_id"), "department": c["department"],
                "priority": c["priority"], "resource": r.get("format_family", ""),
            })
        self.rules.evolving_suggestions()
        events.sort(key=lambda e: (e["case_id"], e["timestamp"]))
        return events

    def to_csv(self, events, path):
        cols = ["case_id", "activity", "timestamp", "department", "priority", "resource", "doc_id"]
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(cols)
            for e in events:
                w.writerow([e.get(c, "") for c in cols])
        return path

    def to_xes_min(self, events, path):
        """\u6975\u7c21 XES (pm4py \u53ef\u8b80)\u3002\u4f9d case \u5206\u7d44\u3002"""
        from collections import defaultdict
        traces = defaultdict(list)
        for e in events:
            traces[e["case_id"]].append(e)
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<log xes.version="1.0">']
        for cid, evs in traces.items():
            lines.append('  <trace>')
            lines.append('    <string key="concept:name" value="%s"/>' % _xesc(cid))
            for e in evs:
                lines.append('    <event>')
                lines.append('      <string key="concept:name" value="%s"/>' % _xesc(e["activity"]))
                lines.append('      <string key="time:timestamp" value="%s"/>' % _xesc(e["timestamp"]))
                lines.append('    </event>')
            lines.append('  </trace>')
        lines.append('</log>')
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path


def _xesc(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


# ============================================================ D. \u6d41\u7a0b\u63a2\u52d8 ==
def case_variants(events):
    """\u6bcf case \u7684 activity \u5e8f\u5217 = \u4e00\u689d\u8b8a\u9ad4\u3002"""
    from collections import defaultdict, Counter
    traces = defaultdict(list)
    for e in events:
        traces[e["case_id"]].append(e["activity"])
    variants = Counter(tuple(v) for v in traces.values())
    return variants


def filter_top_k_variants(events, k=10):
    """80/20\uff1a\u53ea\u7559\u524d k \u5927\u8b8a\u9ad4\u7684 case\u3002"""
    from collections import defaultdict
    traces = defaultdict(list)
    for e in events:
        traces[e["case_id"]].append(e)
    variants = case_variants(events)
    top = set(v for v, _ in variants.most_common(k))
    keep = []
    for cid, evs in traces.items():
        seq = tuple(e["activity"] for e in evs)
        if seq in top:
            keep.extend(evs)
    keep.sort(key=lambda e: (e["case_id"], e["timestamp"]))
    return keep


def discover_dfg(events):
    """\u76f4\u63a5\u8ddf\u96a8\u5716 (Directly-Follows Graph)\u3002\u7d14 Python\uff0c\u7121\u9700 pm4py\u3002
    \u82e5 pm4py \u5b58\u5728\u53ef\u4e26\u5b58\uff1b\u9019\u88e1\u7d66\u81ea\u5305\u7248\u4ee5\u4fdd\u672c\u5730\u96f6\u4f9d\u8cf4\u3002"""
    from collections import defaultdict, Counter
    traces = defaultdict(list)
    for e in events:
        traces[e["case_id"]].append(e)
    edges = Counter(); starts = Counter(); ends = Counter()
    for cid, evs in traces.items():
        evs = sorted(evs, key=lambda e: e["timestamp"])
        acts = [e["activity"] for e in evs]
        if acts:
            starts[acts[0]] += 1; ends[acts[-1]] += 1
        for a, b in zip(acts, acts[1:]):
            edges[(a, b)] += 1
    return {
        "edges": [{"from": a, "to": b, "count": c} for (a, b), c in edges.most_common()],
        "start_activities": dict(starts), "end_activities": dict(ends),
        "activities": sorted({e["activity"] for e in events}),
    }


def dfg_via_pm4py(events):
    """\u82e5 pm4py + pandas \u5b58\u5728\uff0c\u7528\u5b98\u65b9\u7b97\u6cd5 (\u53ef\u9078)\u3002"""
    pm4py = _try("pm4py")
    pd = _try("pandas")
    if pm4py is None or pd is None:
        return None
    try:
        df = pd.DataFrame(events)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        log = pm4py.format_dataframe(df, case_id="case_id", activity_key="activity",
                                     timestamp_key="timestamp")
        dfg, start, end = pm4py.discover_dfg(log)
        return {"edges": [{"from": a, "to": b, "count": int(c)} for (a, b), c in dfg.items()],
                "start_activities": {k: int(v) for k, v in start.items()},
                "end_activities": {k: int(v) for k, v in end.items()}}
    except Exception:
        return None


# ============================================================ C. \u63a7\u7ba1\u8868 ==
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def build_control_sheet(records, cfg, out_path, context="General"):
    """records \u2192 \u5de5\u4f5c\u63a7\u7ba1\u8868 (Excel\u00b7\u689d\u4ef6\u683c\u5f0f\u00b7\u591a\u5206\u9801)\u3002"""
    rules = EvolvingRules(cfg, context)
    tasks = []
    for r in records:
        if r.get("status") != "OK":
            continue
        text = " ".join([r.get("file_name", ""),
                         " ".join(r.get("aspects", {}).get("keywords", [])),
                         r.get("text_preview", "")])
        c = rules.classify(text)
        es = r.get("email_structure") or {}
        tasks.append({
            "\u63a7\u7ba1\u55ae\u865f": c["ticket_id"], "\u95dc\u9375\u4e3b\u984c": c["theme"],
            "\u4e3b\u8cac\u90e8\u9580": c["department"], "\u7dca\u6025\u7a0b\u5ea6": c["priority"],
            "\u9810\u8a08\u7d50\u6848\u65e5": c["deadline"] or "", "\u7576\u524d\u72c0\u614b": "\u5f85\u8655\u7406",
            "\u4f86\u6e90\u6a94": r.get("file_name", ""),
            "\u4e3b\u65e8": es.get("subject", ""),
            "\u654f\u611f\u5ea6": r.get("aspects", {}).get("sensitivity", ""),
            "doc_id": r.get("doc_id", ""),
        })
    tasks.sort(key=lambda t: (PRIORITY_ORDER.get(t["\u7dca\u6025\u7a0b\u5ea6"], 3), t["\u9810\u8a08\u7d50\u6848\u65e5"] or "9999"))

    xw = _try("xlsxwriter")
    if xw is None:
        # \u964d\u7d1a\uff1aopenpyxl \u7c21\u8868
        op = _try("openpyxl")
        if op is None:
            # \u518d\u964d\uff1aCSV
            p = out_path.rsplit(".", 1)[0] + ".csv"
            with open(p, "w", encoding="utf-8-sig", newline="") as f:
                if tasks:
                    w = csv.DictWriter(f, fieldnames=list(tasks[0].keys())); w.writeheader(); w.writerows(tasks)
            return p
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active; ws.title = "\u63a7\u7ba1\u7e3d\u8868"
        if tasks:
            cols = list(tasks[0].keys()); ws.append(cols)
            for t in tasks:
                ws.append([t[c] for c in cols])
        wb.save(out_path); return out_path

    # xlsxwriter\uff1a\u689d\u4ef6\u683c\u5f0f + \u591a\u5206\u9801
    import xlsxwriter
    wb = xlsxwriter.Workbook(out_path)
    hdr = wb.add_format({"bold": True, "bg_color": "#4c78a8", "font_color": "white",
                         "border": 1, "align": "center"})
    high = wb.add_format({"bg_color": "#f4d7d2", "font_color": "#9C0006", "bold": True})
    med = wb.add_format({"bg_color": "#fdf0cf", "font_color": "#9C6500"})
    done = wb.add_format({"bg_color": "#d5ecd8", "font_color": "#006100"})

    def write_sheet(name, rows):
        ws = wb.add_worksheet(name)
        if not rows:
            ws.write(0, 0, "\u7121\u8cc7\u6599"); return
        cols = list(rows[0].keys())
        for ci, col in enumerate(cols):
            ws.write(0, ci, col, hdr); ws.set_column(ci, ci, 20)
        for ri, t in enumerate(rows, 1):
            for ci, col in enumerate(cols):
                ws.write(ri, ci, t[col])
        n = len(rows); pcol = cols.index("\u7dca\u6025\u7a0b\u5ea6"); scol = cols.index("\u7576\u524d\u72c0\u614b")
        ws.conditional_format(1, pcol, n, pcol, {"type": "cell", "criteria": "==", "value": '"High"', "format": high})
        ws.conditional_format(1, pcol, n, pcol, {"type": "cell", "criteria": "==", "value": '"Medium"', "format": med})
        ws.conditional_format(1, scol, n, scol, {"type": "cell", "criteria": "==", "value": '"\u5df2\u5b8c\u6210"', "format": done})

    write_sheet("\u63a7\u7ba1\u7e3d\u8868", tasks)
    critical = [t for t in tasks if t["\u7dca\u6025\u7a0b\u5ea6"] == "High" and t["\u7576\u524d\u72c0\u614b"] != "\u5df2\u5b8c\u6210"]
    write_sheet("\u6025\u4ef6\u8207\u91cd\u5927\u7570\u5e38", critical)
    wb.close()
    return out_path


# ============================================================ E. \u81ea\u6f14\u5316 SSOT ==
class SSOTEngine:
    """\u672c\u6a5f\u81ea\u6f14\u5316 SSOT\uff1a\u4f9d UID \u53bb\u91cd\u00b7\u589e\u91cf\u878d\u5408\u00b7\u4fdd\u7559\u624b\u52d5\u72c0\u614b\u3002
    Parquet \u512a\u5148\uff0c\u7121 pyarrow \u5247\u964d\u7d1a JSONL\u3002"""

    def __init__(self, cfg):
        self.cfg = cfg
        pm = cfg.get("pmine", {})
        self.dir = os.path.join(cfg["paths"]["runtime"], "ssot")
        os.makedirs(self.dir, exist_ok=True)
        self.uid_field = pm.get("ssot_uid_field", "doc_id")
        self.status_field = "\u7576\u524d\u72c0\u614b"
        self.pl = _try("polars")
        self.pa = _try("pyarrow")
        self.parquet_ok = (self.pl is not None and self.pa is not None)
        self.cache = os.path.join(self.dir, "master_ssot.parquet" if self.parquet_ok else "master_ssot.jsonl")

    def _load(self):
        if not os.path.exists(self.cache):
            return []
        if self.parquet_ok:
            return self.pl.read_parquet(self.cache).to_dicts()
        out = []
        with open(self.cache, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    out.append(json.loads(ln))
        return out

    def _save(self, rows):
        if self.parquet_ok:
            self.pl.DataFrame(rows).write_parquet(self.cache)
        else:
            with open(self.cache, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def synchronize(self, new_rows):
        """\u589e\u91cf\u878d\u5408\uff1a\u65b0\u8cc7\u6599\u4f9d UID \u66f4\u65b0\uff0c\u4f46\u4e0d\u8986\u84cb\u4f7f\u7528\u8005\u624b\u6539\u7684\u72c0\u614b\u3002"""
        hist = self._load()
        hist_by_uid = {r.get(self.uid_field): r for r in hist if r.get(self.uid_field)}
        merged = {}
        # \u5148\u653e\u820a\u8cc7\u6599
        for uid, r in hist_by_uid.items():
            merged[uid] = r
        # \u65b0\u8cc7\u6599\u878d\u5408\uff1a\u4fdd\u7559\u820a\u624b\u52d5\u72c0\u614b
        for r in new_rows:
            uid = r.get(self.uid_field)
            if not uid:
                continue
            if uid in hist_by_uid:
                old_status = hist_by_uid[uid].get(self.status_field)
                if old_status and old_status != "\u5f85\u8655\u7406":
                    r = dict(r); r[self.status_field] = old_status  # \u4fdd\u7559\u624b\u6539
            merged[uid] = r
        rows = list(merged.values())
        self._save(rows)
        return {"total": len(rows), "new": len([r for r in new_rows if r.get(self.uid_field) not in hist_by_uid]),
                "backend": "parquet" if self.parquet_ok else "jsonl", "cache": self.cache}


# ============================================================ \u5229\u5bb3\u95dc\u4fc2\u4eba ==
class StakeholderEngine:
    """\u81ea\u52d5\u5efa\u7acb\u5229\u5bb3\u95dc\u4fc2\u4eba\u7cfb\u7d71\uff1a\u5f9e records \u7684 email_structure \u8207\u5206\u985e\uff0c
    \u840d\u53d6\u53c3\u8207\u8005/\u7d44\u7e54\uff0c\u7d71\u8a08\u4e92\u52d5\u983b\u7387\u3001\u95dc\u806f\u9818\u57df\u8207\u55ae\u865f\uff0c\u63a8\u65b7\u89d2\u8272\u3002
    append-only registry (\u53ea\u589e\u4e0d\u6e1b)\u3002"""

    ROLE_HINT = {
        "\u54c1\u4fdd\u90e8": ["qa", "quality", "\u54c1\u4fdd", "\u54c1\u7ba1"],
        "\u7814\u767c\u90e8": ["rd", "engineer", "\u7814\u767c", "\u5de5\u7a0b"],
        "\u63a1\u8cfc\u90e8": ["buyer", "purchas", "procure", "\u63a1\u8cfc"],
        "\u88fd\u9020\u90e8": ["mfg", "production", "\u88fd\u9020", "\u7522\u7dda"],
        "\u4f9b\u61c9\u5546": ["supplier", "vendor", "\u4f9b\u61c9"],
        "\u5ba2\u6236": ["client", "customer", "\u5ba2\u6236"],
    }

    def __init__(self, cfg):
        self.cfg = cfg
        pm = cfg.get("pmine", {})
        self.registry_path = os.path.join(cfg["paths"]["ledger"],
                                          pm.get("stake_registry", "stakeholders.jsonl"))

    def _role(self, email, name):
        hay = (email + " " + (name or "")).lower()
        for role, hints in self.ROLE_HINT.items():
            if any(h in hay for h in hints):
                return role
        return "\u5f85\u6a19\u8a3b"

    def build(self, records):
        from collections import defaultdict
        stake = defaultdict(lambda: {"email": "", "name": "", "org": "",
                                     "roles": set(), "domains": set(), "tickets": set(),
                                     "interaction_count": 0, "first_seen": None, "last_seen": None})
        rules = EvolvingRules(self.cfg, self.cfg.get("pmine", {}).get("stake_context", "Electronics"))
        for r in records:
            if r.get("status") != "OK":
                continue
            es = r.get("email_structure") or {}
            parts = es.get("participants") or []
            orgs = es.get("organizations") or []
            domain = (r.get("aspects") or {}).get("content_domain", "")
            ts = r.get("modified_time") or r.get("processed_at") or ""
            text = " ".join([r.get("file_name", ""), r.get("text_preview", "")])
            ticket = rules.classify(text)["ticket_id"]
            for i, email in enumerate(parts):
                s = stake[email]
                s["email"] = email
                s["org"] = email.split("@")[-1] if "@" in email else (orgs[0] if orgs else "")
                s["roles"].add(self._role(email, ""))
                if domain:
                    s["domains"].add(domain)
                if ticket and ticket != "\u65e5\u5e38\u8ffd\u8e64":
                    s["tickets"].add(ticket)
                s["interaction_count"] += 1
                if ts:
                    s["first_seen"] = min(s["first_seen"] or ts, ts)
                    s["last_seen"] = max(s["last_seen"] or ts, ts)

        out = []
        for email, s in stake.items():
            out.append({
                "stakeholder_id": "VIA-STK-" + _forge.blake2s_short(email, 4),
                "email": email, "org": s["org"],
                "roles": sorted(s["roles"]), "domains": sorted(s["domains"]),
                "tickets": sorted(s["tickets"]), "interaction_count": s["interaction_count"],
                "first_seen": s["first_seen"], "last_seen": s["last_seen"],
                "influence": _influence(s["interaction_count"], len(s["domains"]), len(s["tickets"])),
            })
        out.sort(key=lambda x: (-x["interaction_count"], x["email"]))
        self._append_registry(out)
        return out

    def _append_registry(self, stakeholders):
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(self.registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"built_at": _now(), "count": len(stakeholders),
                                "stakeholders": stakeholders}, ensure_ascii=False) + "\n")

    def summary(self, stakeholders):
        from collections import Counter
        by_org = Counter(s["org"] for s in stakeholders if s["org"])
        by_role = Counter(r for s in stakeholders for r in s["roles"])
        return {"total": len(stakeholders),
                "by_org": dict(by_org.most_common(10)),
                "by_role": dict(by_role.most_common()),
                "high_influence": [s["email"] for s in stakeholders if s["influence"] == "High"][:10]}


def _influence(interactions, n_domains, n_tickets):
    score = interactions + n_domains * 2 + n_tickets
    return "High" if score >= 6 else "Medium" if score >= 3 else "Low"


# ============================================================ \u5f15\u64ce\u4e3b\u9ad4 ==
class PMineEngine:
    def __init__(self, cfg=None, context="General"):
        self.cfg = cfg or _forge.load_config()
        _ensure_pmine_cfg(self.cfg)
        self.context = context
        self.builder = EventLogBuilder(self.cfg, context)
        self.ssot = SSOTEngine(self.cfg)
        self.stake = StakeholderEngine(self.cfg)

    def run(self, records, do_control=True, do_mine=True, do_ssot=True, do_stake=True):
        result = {"context": self.context}
        events = self.builder.from_forge_records(records)
        result["event_count"] = len(events)
        result["evolving_suggestions"] = self.builder.rules._unknown

        if do_stake:
            stakeholders = self.stake.build(records)
            result["stakeholders"] = stakeholders
            result["stakeholder_summary"] = self.stake.summary(stakeholders)

        if do_mine and events:
            collapsed = collapse_adjacent_dupes(events)
            topk = filter_top_k_variants(collapsed, k=self.cfg["pmine"].get("top_k_variants", 10))
            dfg = dfg_via_pm4py(topk) or discover_dfg(topk)
            result["mining"] = {
                "events_after_collapse": len(collapsed),
                "events_after_topk": len(topk),
                "variant_count": len(case_variants(events)),
                "dfg": dfg,
            }
        if do_control:
            out = os.path.join(self.cfg["paths"]["reports"], "control_sheet.xlsx")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            result["control_sheet"] = build_control_sheet(records, self.cfg, out, self.context)
        if do_ssot:
            tasks = _records_to_tasks(records, self.cfg, self.context)
            result["ssot"] = self.ssot.synchronize(tasks)
        return result, events


def _records_to_tasks(records, cfg, context):
    rules = EvolvingRules(cfg, context)
    out = []
    for r in records:
        if r.get("status") != "OK":
            continue
        text = " ".join([r.get("file_name", ""),
                         " ".join(r.get("aspects", {}).get("keywords", [])),
                         r.get("text_preview", "")])
        c = rules.classify(text)
        out.append({"doc_id": r.get("doc_id"), "\u63a7\u7ba1\u55ae\u865f": c["ticket_id"],
                    "\u95dc\u9375\u4e3b\u984c": c["theme"], "\u4e3b\u8cac\u90e8\u9580": c["department"],
                    "\u7dca\u6025\u7a0b\u5ea6": c["priority"], "\u7576\u524d\u72c0\u614b": "\u5f85\u8655\u7406",
                    "\u4f86\u6e90\u6a94": r.get("file_name", "")})
    return out


PMINE_DEFAULTS = {
    "context_rules": DEFAULT_CONTEXT_RULES,
    "evolve_threshold": 3,
    "evolve_registry": "pmine_evolve.jsonl",
    "top_k_variants": 10,
    "ssot_uid_field": "doc_id",
}


def _ensure_pmine_cfg(cfg):
    if "pmine" not in cfg:
        cfg["pmine"] = PMINE_DEFAULTS
    else:
        for k, v in PMINE_DEFAULTS.items():
            cfg["pmine"].setdefault(k, v)
    return cfg


# ==================================================================== SELFTEST ==
def selftest():
    import tempfile
    p, f = 0, 0

    def ck(n, c):
        nonlocal p, f
        if c:
            p += 1; print("  [PASS] pmine: %s" % n)
        else:
            f += 1; print("  [FAIL] pmine: %s" % n)

    if _forge is None:
        print("  [FAIL] pmine: via_forge import"); print("pmine: 0 PASS / 1 FAIL"); return 0, 1

    cfg = _ensure_pmine_cfg(_forge.load_config())
    side = tempfile.mkdtemp()
    cfg["paths"]["ledger"] = side
    cfg["paths"]["reports"] = side
    cfg["paths"]["runtime"] = side

    # \u6a21\u64ec forge records
    def rec(doc_id, fn, kws, ts, sens="INTERNAL"):
        return {"doc_id": doc_id, "file_name": fn, "status": "OK",
                "format_family": "TEXT", "modified_time": ts,
                "aspects": {"keywords": kws, "content_domain": "GENERAL", "sensitivity": sens},
                "text_preview": " ".join(kws), "email_structure": {"subject": fn}}

    records = [
        rec("VIA-DOC-1", "PN-9942 AOI \u505c\u7dda.eml", ["AOI", "\u505c\u7dda", "\u4e0d\u826f", "PN-9942"], "2026-07-11T09:00:00Z"),
        rec("VIA-DOC-2", "PN-9942 \u91cd\u5de5\u5b8c\u6210.eml", ["\u91cd\u5de5", "AOI", "PN-9942"], "2026-07-11T14:00:00Z"),
        rec("VIA-DOC-3", "ECR-100 \u898f\u683c\u8b8a\u66f4.docx", ["ECR", "\u8b8a\u66f4", "\u898f\u683c", "\u6025"], "2026-07-10T08:00:00Z"),
        rec("VIA-DOC-4", "\u4f9b\u61c9\u5546\u9054\u4ea4.xlsx", ["\u9054\u4ea4", "\u4ea4\u671f", "\u63a1\u8cfc"], "2026-07-09T08:00:00Z"),
        rec("VIA-DOC-5", "RMA \u5ba2\u8a34.md", ["RMA", "\u5ba2\u8a34", "\u9000\u8ca8"], "2026-07-08T08:00:00Z"),
        rec("VIA-DOC-6", "\u672a\u77e5 ABC-1234 \u8ffd\u8e64.txt", ["ABC-1234"], "2026-07-07T08:00:00Z"),
        rec("VIA-DOC-7", "\u672a\u77e5 ABC-1234 \u518d\u6b21.txt", ["ABC-1234"], "2026-07-06T08:00:00Z"),
        rec("VIA-DOC-8", "\u672a\u77e5 ABC-1234 \u4e09\u6b21.txt", ["ABC-1234"], "2026-07-05T08:00:00Z"),
    ]

    eng = PMineEngine(cfg, context="Electronics")
    result, events = eng.run(records, do_control=True, do_mine=True, do_ssot=True)

    ck("event log built", result["event_count"] == 8)
    idx = {e["doc_id"]: e for e in events}
    ck("AOI -> \u88fd\u9020\u90e8 High", idx["VIA-DOC-1"]["department"] == "\u88fd\u9020\u90e8" and idx["VIA-DOC-1"]["priority"] == "High")
    ck("ECR + \u6025 -> High", idx["VIA-DOC-3"]["priority"] == "High")
    ck("\u9054\u4ea4 -> \u63a1\u8cfc\u90e8", idx["VIA-DOC-4"]["department"] == "\u63a1\u8cfc\u90e8")
    ck("RMA -> \u54c1\u4fdd\u90e8", idx["VIA-DOC-5"]["department"] == "\u54c1\u4fdd\u90e8")
    ck("PN case_id extracted", idx["VIA-DOC-1"]["case_id"] == "9942")

    # \u81ea\u6f14\u5316\uff1aABC-1234 \u51fa\u73fe 3 \u6b21 -> \u5efa\u8b70
    sug = eng.builder.rules.evolving_suggestions()
    ck("self-evolving suggestion", "ABC-1234" in sug)
    ck("evolve registry written", os.path.exists(eng.builder.rules.registry_path))

    # \u6d41\u7a0b\u63a2\u52d8
    m = result["mining"]
    ck("dfg computed", m["dfg"] is not None and "edges" in m["dfg"])
    ck("collapse works", m["events_after_collapse"] <= result["event_count"])
    ck("variants counted", m["variant_count"] >= 1)

    # PN-9942 \u6709 AOI\u505c\u7dda -> \u91cd\u5de5 \u7684\u8ddf\u96a8\u95dc\u4fc2 (\u540c case, \u5169\u6b65)
    dfg = m["dfg"]
    case9942 = [e for e in events if e["case_id"] == "9942"]
    ck("PN-9942 has 2 events same case", len(case9942) == 2)

    # \u63a7\u7ba1\u8868
    ck("control sheet created", os.path.exists(result["control_sheet"]))
    ck("control sheet xlsx", result["control_sheet"].endswith(".xlsx"))

    # SSOT \u540c\u6b65 + \u4fdd\u7559\u624b\u52d5\u72c0\u614b
    ss = result["ssot"]
    ck("ssot synced", ss["total"] == 8)
    # \u624b\u52d5\u628a VIA-DOC-1 \u6539\u6210\u5df2\u5b8c\u6210\uff0c\u518d\u540c\u6b65\uff0c\u78ba\u8a8d\u4e0d\u88ab\u8986\u84cb
    hist = eng.ssot._load()
    for r in hist:
        if r["doc_id"] == "VIA-DOC-1":
            r["\u7576\u524d\u72c0\u614b"] = "\u5df2\u5b8c\u6210"
    eng.ssot._save(hist)
    tasks2 = _records_to_tasks(records, cfg, "Electronics")
    eng.ssot.synchronize(tasks2)
    hist2 = {r["doc_id"]: r for r in eng.ssot._load()}
    ck("ssot preserves manual status", hist2["VIA-DOC-1"]["\u7576\u524d\u72c0\u614b"] == "\u5df2\u5b8c\u6210")
    ck("ssot re-sync no dup", len(hist2) == 8)

    # \u532f\u51fa\u4e8b\u4ef6\u65e5\u8a8c CSV + XES
    csvp = eng.builder.to_csv(events, os.path.join(side, "eventlog.csv"))
    ck("eventlog csv", os.path.exists(csvp))
    xesp = eng.builder.to_xes_min(events, os.path.join(side, "eventlog.xes"))
    with open(xesp, encoding="utf-8") as fh:
        xes = fh.read()
    ck("xes valid-ish", "<log" in xes and "concept:name" in xes)

    # \u53ea\u589e\u4e0d\u6e1b\uff1a\u898f\u5247\u6f14\u5316\u53ea\u9644\u52a0
    with open(eng.builder.rules.registry_path, encoding="utf-8") as fh:
        n1 = sum(1 for _ in fh)
    EvolvingRules(cfg, "Electronics").evolving_suggestions()  # \u7a7a\u8de1\u4e0d\u5beb
    with open(eng.builder.rules.registry_path, encoding="utf-8") as fh:
        n2 = sum(1 for _ in fh)
    ck("evolve registry append-only", n2 == n1)

    # \u5229\u5bb3\u95dc\u4fc2\u4eba\u7cfb\u7d71
    email_recs = [
        {"doc_id": "M1", "status": "OK", "file_name": "PN-9942 AOI.eml", "modified_time": "2026-07-11T09:00:00Z",
         "aspects": {"content_domain": "GENERAL", "keywords": ["AOI"]}, "text_preview": "PN-9942 AOI \u505c\u7dda",
         "email_structure": {"subject": "AOI", "participants": ["qa.li@corp.com", "rd.wang@corp.com"],
                             "organizations": ["corp.com"]}},
        {"doc_id": "M2", "status": "OK", "file_name": "\u4f9b\u61c9\u5546.eml", "modified_time": "2026-07-10T09:00:00Z",
         "aspects": {"content_domain": "SALES", "keywords": ["\u9054\u4ea4"]}, "text_preview": "\u9054\u4ea4 \u63a1\u8cfc",
         "email_structure": {"subject": "\u9054\u4ea4", "participants": ["qa.li@corp.com", "buyer.chen@supplier.com"],
                             "organizations": ["corp.com", "supplier.com"]}},
    ]
    stakeholders = eng.stake.build(email_recs)
    ck("stakeholders built", len(stakeholders) == 3)  # qa.li, rd.wang, buyer.chen
    byemail = {s["email"]: s for s in stakeholders}
    ck("qa.li top interactions", byemail["qa.li@corp.com"]["interaction_count"] == 2)
    ck("role inferred qa", "\u54c1\u4fdd\u90e8" in byemail["qa.li@corp.com"]["roles"])
    ck("role inferred buyer", "\u63a1\u8cfc\u90e8" in byemail["buyer.chen@supplier.com"]["roles"])
    ck("stakeholder id format", all(s["stakeholder_id"].startswith("VIA-STK-") for s in stakeholders))
    ck("influence computed", all(s["influence"] in ("High", "Medium", "Low") for s in stakeholders))
    ss = eng.stake.summary(stakeholders)
    ck("stakeholder summary orgs", "corp.com" in ss["by_org"])
    ck("stake registry written", os.path.exists(eng.stake.registry_path))

    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(description="VIA PMine — event log / control sheet / process mining / SSOT")
    ap.add_argument("--scan"); ap.add_argument("--context", default="General")
    ap.add_argument("--control", action="store_true"); ap.add_argument("--mine", action="store_true")
    ap.add_argument("--ssot", action="store_true"); ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        a, b = selftest(); print("pmine: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)

    if args.scan:
        forge_eng = _forge.ForgeEngine()
        records = forge_eng.scan(args.scan, do_fix=True)
        eng = PMineEngine(forge_eng.cfg, context=args.context)
        result, events = eng.run(records, do_control=args.control or True,
                                 do_mine=args.mine or True, do_ssot=args.ssot or True)
        print("events=%d variants=%d" % (result["event_count"],
                                         result.get("mining", {}).get("variant_count", 0)))
        if "control_sheet" in result:
            print("control sheet -> %s" % result["control_sheet"])
        if "ssot" in result:
            print("ssot -> %s (%d rows, %s)" % (result["ssot"]["cache"], result["ssot"]["total"], result["ssot"]["backend"]))


if __name__ == "__main__":
    main()

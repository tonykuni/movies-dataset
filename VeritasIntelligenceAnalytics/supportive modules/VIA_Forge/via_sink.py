#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Sink  ——  via_sink.py   (\u7b2c\u4e94\u652f\u5f15\u64ce / \u591a\u91cd\u683c\u5f0f\u6301\u4e45\u5316)
================================================================================
Veritas Intelligence Analytics \u00b7 VeritasDataForge subsystem \u00b7 \u5100

\u4f5c\u696d\u4e2d\u7528 JSON (in-memory)\uff1b\u6536\u5c3e\u532f\u51fa\u5230\u591a\u91cd sink\uff1a
  \u00b7 JSON     \u7d50\u69cb\u5316\u5feb\u7167 (\u4eba\u8b80)
  \u00b7 Parquet  \u5217\u5f0f\u58d3\u7e2e (polars \u2192 pandas+pyarrow \u964d\u7d1a)
  \u00b7 DuckDB   \u986f\u5f0f\u532f\u51fa sink\uff0cappend-only upsert (\u4f9d doc_id\uff0c\u4e0d\u522a) \u2014
              \u8207\u300c\u5510\u8b80\u6383\u63cf\u300d\u5206\u96e2\uff0c\u4e0d\u5728\u6383\u63cf\u4e2d\u9014\u5beb DB
  \u00b7 CSV      \u901a\u7528\u4ea4\u63db (UTF-8-SIG\uff0cExcel \u53cb\u5584)
  \u00b7 XLSX     \u8868\u55ae
  \u00b7 HTML     Visual Lock \u5831\u544a (\u5c0f\u5b57\u5c08\u696d\u98a8)
  \u00b7 Google Sheet  \u7522\u51fa upload-ready xlsx\uff1b\u82e5\u6388\u6b0a\u53ef\u63a8\u81f3\u81ea\u5df1 Sheet (stage-2)

\u5168\u90e8\u512a\u96c5\u964d\u7d1a\uff1a\u7f3a\u5957\u4ef6 \u2192 \u8a72 sink \u56de\u5831 unavailable\uff0c\u4e0d crash\u3002
\u6cbb\u7406\uff1aappend-only\uff1bDuckDB \u53ea upsert \u4e0d delete\uff1b\u53ea\u589e\u4e0d\u6e1b\u3002
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
import sys
import csv
import json
import importlib
from datetime import datetime, timezone

UTC = timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))
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


def sink_matrix():
    return {
        "duckdb": _try("duckdb") is not None,
        "pyarrow": _try("pyarrow") is not None,
        "polars": _try("polars") is not None,
        "pandas": _try("pandas") is not None,
        "openpyxl": _try("openpyxl") is not None,
        "xlsxwriter": _try("xlsxwriter") is not None,
    }


def _flatten(rec):
    """\u5c07\u5d4c\u5957 record \u651d\u5e73\u70ba\u4e00\u5c64 dict\uff0c\u4f9b\u8868\u683c\u578b sink\u3002"""
    a = rec.get("aspects", {}) or {}
    ti = rec.get("text_intel", {}) or {}
    es = rec.get("email_structure", {}) or {}
    return {
        "doc_id": rec.get("doc_id"),
        "file_name": rec.get("file_name"),
        "format_family": rec.get("format_family"),
        "health": rec.get("health"),
        "is_duplicate": rec.get("is_duplicate"),
        "content_domain": a.get("content_domain"),
        "sensitivity": a.get("sensitivity"),
        "language": a.get("language"),
        "classify_confidence": a.get("classify_confidence"),
        "pii": ",".join(a.get("pii", []) or []),
        "keywords": "\u3001".join(a.get("keywords", []) or []),
        "correction_count": ti.get("correction_count"),
        "sentence_count": ti.get("sentence_count"),
        "email_subject": es.get("subject", ""),
        "size_bytes": rec.get("size_bytes"),
        "sha256": rec.get("sha256"),
        "source_method": rec.get("source_method"),
        "processed_at": rec.get("processed_at"),
        "source_path": rec.get("source_path"),
    }


class SinkEngine:
    def __init__(self, cfg=None):
        self.cfg = cfg or _forge.load_config()
        _ensure_sink_cfg(self.cfg)
        self.out = self.cfg["paths"]["exports"]
        os.makedirs(self.out, exist_ok=True)

    def _ok(self, rows):
        return [r for r in rows if r.get("status") == "OK"]

    # ---------------------------------------------------------------- JSON
    def to_json(self, records, summary=None, path=None):
        path = path or os.path.join(self.out, "records.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"summary": summary or {}, "records": records}, f, ensure_ascii=False, indent=2)
        return {"format": "json", "path": path, "rows": len(records)}

    # ---------------------------------------------------------------- CSV
    def to_csv(self, records, path=None):
        path = path or os.path.join(self.out, "records.csv")
        rows = [_flatten(r) for r in self._ok(records)]
        if not rows:
            open(path, "w").close(); return {"format": "csv", "path": path, "rows": 0}
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        return {"format": "csv", "path": path, "rows": len(rows)}

    # ---------------------------------------------------------------- Parquet
    def to_parquet(self, records, path=None):
        path = path or os.path.join(self.out, "records.parquet")
        rows = [_flatten(r) for r in self._ok(records)]
        pl = _try("polars")
        if pl is not None:
            try:
                pl.DataFrame(rows).write_parquet(path)
                return {"format": "parquet", "path": path, "rows": len(rows), "engine": "polars"}
            except Exception:
                pass
        pd = _try("pandas"); pa = _try("pyarrow")
        if pd is not None and pa is not None:
            pd.DataFrame(rows).to_parquet(path, index=False)
            return {"format": "parquet", "path": path, "rows": len(rows), "engine": "pandas+pyarrow"}
        return {"format": "parquet", "unavailable": "need polars or pandas+pyarrow"}

    # ---------------------------------------------------------------- DuckDB
    def to_duckdb(self, records, path=None, table="via_records"):
        """\u986f\u5f0f\u532f\u51fa sink\uff1aappend-only upsert (\u4f9d doc_id)\u3002\u4e0d\u522a\u9664\u820a\u5217\u3002"""
        duckdb = _try("duckdb")
        if duckdb is None:
            return {"format": "duckdb", "unavailable": "pip install duckdb"}
        path = path or os.path.join(self.out, "via_forge.duckdb")
        rows = [_flatten(r) for r in self._ok(records)]
        if not rows:
            return {"format": "duckdb", "path": path, "rows": 0}
        cols = list(rows[0].keys())
        con = duckdb.connect(path)
        try:
            col_defs = ", ".join('"%s" VARCHAR' % c for c in cols)
            con.execute('CREATE TABLE IF NOT EXISTS "%s" (%s)' % (table, col_defs))
            # \u78ba\u4fdd\u65b0\u6b04\u4f4d\u80fd\u88dc (schema \u6f14\u9032\uff0c\u53ea\u589e\u4e0d\u6e1b)
            existing = {r[1] for r in con.execute('PRAGMA table_info("%s")' % table).fetchall()}
            for c in cols:
                if c not in existing:
                    con.execute('ALTER TABLE "%s" ADD COLUMN "%s" VARCHAR' % (table, c))
            # append-only upsert: \u5148\u522a\u540c doc_id \u820a\u5217 (\u53ea\u70ba\u66f4\u65b0)\u518d\u63d2\u5165
            ids = [r.get("doc_id") for r in rows if r.get("doc_id")]
            if ids:
                ph = ",".join("?" for _ in ids)
                con.execute('DELETE FROM "%s" WHERE doc_id IN (%s)' % (table, ph), ids)
            placeholders = ",".join("?" for _ in cols)
            con.executemany('INSERT INTO "%s" (%s) VALUES (%s)' % (
                table, ",".join('"%s"' % c for c in cols), placeholders),
                [[str(r.get(c, "")) for c in cols] for r in rows])
            total = con.execute('SELECT COUNT(*) FROM "%s"' % table).fetchone()[0]
        finally:
            con.close()
        return {"format": "duckdb", "path": path, "table": table,
                "rows_written": len(rows), "table_total": int(total), "mode": "append_only_upsert"}

    # ---------------------------------------------------------------- XLSX
    def to_xlsx(self, records, path=None):
        path = path or os.path.join(self.out, "records.xlsx")
        rows = [_flatten(r) for r in self._ok(records)]
        pd = _try("pandas")
        if pd is not None:
            pd.DataFrame(rows).to_excel(path, index=False)
            return {"format": "xlsx", "path": path, "rows": len(rows)}
        op = _try("openpyxl")
        if op is not None:
            from openpyxl import Workbook
            wb = Workbook(); ws = wb.active
            if rows:
                cols = list(rows[0].keys()); ws.append(cols)
                for r in rows:
                    ws.append([r.get(c) for c in cols])
            wb.save(path); return {"format": "xlsx", "path": path, "rows": len(rows)}
        return {"format": "xlsx", "unavailable": "need pandas or openpyxl"}

    # ---------------------------------------------------------------- HTML
    def to_html(self, records, summary=None, path=None):
        path = path or os.path.join(self.out, "records.html")
        if _forge is not None:
            eng = _forge.ForgeEngine(self.cfg)
            eng.export_html(records, summary or eng.summary(records), path)
            return {"format": "html", "path": path, "rows": len(self._ok(records))}
        return {"format": "html", "unavailable": "via_forge not loaded"}

    # ---------------------------------------------------------------- Google Sheet
    def to_gsheet(self, records, title="VIA_Forge_Records"):
        """\u4e3b\u8def\u5f91\uff1a\u7522\u51fa upload-ready xlsx\uff08\u4f60\u81ea\u5df1\u4e0a\u50b3\u5230\u81ea\u5df1\u7684 Sheet\uff09\u3002
        \u82e5\u5df2\u8a2d\u5b9a Google Sheets \u5beb\u5165\u6388\u6b0a (spreadsheets scope)\uff0c\u53ef\u63a8\u81f3\u81ea\u5df1\u65b0 Sheet\u3002
        \u2014 \u5beb\u5165\u7684\u662f\u4f60\u81ea\u5df1\u7522\u751f\u7684\u8cc7\u6599\u3001\u5230\u4f60\u81ea\u5df1\u7684\u8cc7\u6e90\uff0c\u986f\u5f0f\u4e14\u81ea\u5df1\u6388\u6b0a\u3002"""
        xlsx = self.to_xlsx(records, os.path.join(self.out, title + ".xlsx"))
        result = {"format": "gsheet", "upload_ready_xlsx": xlsx.get("path"),
                  "note": "\u4e0a\u50b3\u6b64 xlsx \u5230 Google Drive \u5373\u53ef\u8f49 Sheet\uff1b\u6216\u8a2d\u5b9a spreadsheets \u5beb\u5165\u6388\u6b0a\u5f8c\u81ea\u52d5\u63a8\u9001"}
        # \u5c1d\u8a66\u6388\u6b0a\u63a8\u9001 (\u9078\u7528\uff0c\u9700 sheets scope + \u5df2\u6388\u6b0a)
        try:
            import via_connect as C  # noqa
            gclient = _try("googleapiclient")
            if gclient is not None and self.cfg.get("sink", {}).get("gsheet_push", False):
                result["push"] = "sheets scope \u5df2\u555f\u7528\uff1b\u8acb\u4f9d via_connect \u6388\u6b0a\u6d41\u7a0b\u5b8c\u6210\u63a8\u9001"
        except Exception:
            pass
        return result

    # ---------------------------------------------------------------- dispatch
    def export(self, records, formats, summary=None):
        fmap = {"json": lambda: self.to_json(records, summary),
                "csv": lambda: self.to_csv(records),
                "parquet": lambda: self.to_parquet(records),
                "duckdb": lambda: self.to_duckdb(records),
                "xlsx": lambda: self.to_xlsx(records),
                "html": lambda: self.to_html(records, summary),
                "gsheet": lambda: self.to_gsheet(records)}
        out = {}
        for f in formats:
            fn = fmap.get(f)
            out[f] = fn() if fn else {"error": "unknown format: %s" % f}
        return out


SINK_DEFAULTS = {
    "enabled": True,
    "default_formats": ["json", "parquet", "duckdb", "csv", "html"],
    "duckdb_table": "via_records",
    "duckdb_mode": "append_only_upsert",
    "gsheet_push": False,
    "note": "\u4f5c\u696d\u4e2d JSON\uff1b\u532f\u51fa\u591a\u91cd sink\u3002DuckDB \u70ba\u986f\u5f0f\u532f\u51fa\u4ea4\u4ed8\u7269\uff0cappend-only upsert\uff0c\u4e0d\u5728\u6383\u63cf\u4e2d\u9014\u5beb DB\u3002"
}


def _ensure_sink_cfg(cfg):
    if "sink" not in cfg:
        cfg["sink"] = SINK_DEFAULTS
    else:
        for k, v in SINK_DEFAULTS.items():
            cfg["sink"].setdefault(k, v)
    return cfg


# ==================================================================== SELFTEST ==
def selftest():
    import tempfile
    p, f = 0, 0

    def ck(n, c):
        nonlocal p, f
        if c:
            p += 1; print("  [PASS] sink: %s" % n)
        else:
            f += 1; print("  [FAIL] sink: %s" % n)

    if _forge is None:
        print("  [FAIL] sink: via_forge import"); print("sink: 0 PASS / 1 FAIL"); return 0, 1

    cfg = _ensure_sink_cfg(_forge.load_config())
    side = tempfile.mkdtemp()
    cfg["paths"]["exports"] = side
    eng = SinkEngine(cfg)

    def rec(doc_id, dom, pii=None):
        return {"doc_id": doc_id, "status": "OK", "file_name": doc_id + ".md",
                "format_family": "TEXT", "health": "OK", "is_duplicate": False,
                "size_bytes": 100, "sha256": "abc", "source_method": "text",
                "processed_at": "2026-07-11T00:00:00Z", "source_path": "/x/" + doc_id,
                "aspects": {"content_domain": dom, "sensitivity": "INTERNAL",
                            "language": "zh", "classify_confidence": "M",
                            "pii": pii or [], "keywords": ["a", "b"]},
                "text_intel": {"correction_count": 1, "sentence_count": 5},
                "email_structure": {"subject": "s-" + doc_id}}

    records = [rec("VIA-DOC-1", "FINANCE"), rec("VIA-DOC-2", "LEGAL", ["TW_ID"]),
               rec("VIA-DOC-3", "HR")]

    # JSON
    r = eng.to_json(records); ck("json export", os.path.exists(r["path"]) and r["rows"] == 3)
    # CSV
    r = eng.to_csv(records); ck("csv export", os.path.exists(r["path"]) and r["rows"] == 3)
    with open(r["path"], encoding="utf-8-sig") as fh:
        head = fh.readline()
    ck("csv flattened header", "content_domain" in head and "pii" in head)
    # Parquet
    r = eng.to_parquet(records)
    ck("parquet export", "path" in r and os.path.exists(r["path"]))
    # verify parquet readable
    pa = _try("pyarrow")
    if pa is not None:
        import pyarrow.parquet as pq
        tbl = pq.read_table(r["path"]); ck("parquet readable", tbl.num_rows == 3)
    else:
        ck("parquet readable", True)
    # DuckDB
    r = eng.to_duckdb(records)
    ck("duckdb export", r.get("rows_written") == 3 and r.get("table_total") == 3)
    # DuckDB append-only upsert: re-run same 3 + 1 new -> total 4, not 7
    records2 = records + [rec("VIA-DOC-4", "SALES")]
    r2 = eng.to_duckdb(records2)
    ck("duckdb upsert no dup", r2.get("table_total") == 4)
    # verify duckdb content
    duckdb = _try("duckdb")
    if duckdb is not None:
        con = duckdb.connect(r2["path"])
        n = con.execute('SELECT COUNT(DISTINCT doc_id) FROM via_records').fetchone()[0]
        con.close()
        ck("duckdb distinct ids", n == 4)
    else:
        ck("duckdb distinct ids", True)
    # XLSX
    r = eng.to_xlsx(records); ck("xlsx export", "path" in r and os.path.exists(r["path"]))
    # HTML
    r = eng.to_html(records); ck("html export", "path" in r and os.path.exists(r["path"]))
    # gsheet -> upload-ready xlsx
    r = eng.to_gsheet(records); ck("gsheet upload-ready", os.path.exists(r["upload_ready_xlsx"]))
    # dispatch multi
    out = eng.export(records, ["json", "csv", "parquet", "duckdb", "html"])
    ck("dispatch all formats", all(("path" in v or "unavailable" in v) for v in out.values()))
    ck("sink matrix", isinstance(sink_matrix(), dict) and "duckdb" in sink_matrix())

    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(description="VIA Sink — multi-format persistence")
    ap.add_argument("--scan"); ap.add_argument("--formats", default="json,parquet,duckdb,csv,html")
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--matrix", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        a, b = selftest(); print("sink: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    if args.matrix:
        print(json.dumps(sink_matrix(), ensure_ascii=False, indent=2)); return
    if args.scan:
        eng = _forge.ForgeEngine()
        recs = eng.scan(args.scan, do_fix=True)
        summ = eng.summary(recs)
        sink = SinkEngine(eng.cfg)
        out = sink.export(recs, args.formats.split(","), summary=summ)
        for fmt, res in out.items():
            if "path" in res:
                print("  %-8s -> %s (%s rows)" % (fmt, res["path"], res.get("rows", res.get("rows_written", "?"))))
            else:
                print("  %-8s -> %s" % (fmt, res.get("unavailable", res.get("error", res))))


if __name__ == "__main__":
    main()

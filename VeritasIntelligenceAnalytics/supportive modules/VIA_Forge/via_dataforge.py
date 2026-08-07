#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA DataForge  ——  via_dataforge.py   (\u5eab \u00b7 \u8cc7\u6599\u57fa\u5e95\u5f37\u5f15\u64ce)
================================================================================
\u5408\u4f75 forge + sink \u70ba\u55ae\u4e00\u5f37\u5f15\u64ce\uff1a
  \u2022 \u8b80\u53d6 39 \u683c\u5f0f \u2192 \u4fee\u5fa9\u6587\u5b57 \u2192 \u5206\u985e(\u9818\u57df/\u654f\u611f/PII) \u2192 \u53bb\u91cd \u2192 VIA \u7de8\u865f
  \u2022 \u591a\u683c\u5f0f\u6301\u4e45\u5316/\u532f\u51fa(json/parquet/csv/xlsx/html/duckdb)
\u5e95\u5c64 via_forge / via_sink \u4fdd\u7559\u4e0d\u52d5\uff08\u53ea\u589e\u4e0d\u6e1b\u3001173 \u6e2c\u8a66\u4e0d\u7834\uff09\uff1b
\u672c\u5f15\u64ce\u4ee5\u7d44\u5408\u65b9\u5f0f\u5c07\u5169\u8005\u5448\u73fe\u70ba\u4e00\u652f\u5f37\u5f15\u64ce\u3002
================================================================================
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import via_forge as _F
import via_sink as _S


class DataForgeEngine:
    """\u8cc7\u6599\u57fa\u5e95\uff1a\u64f7\u53d6\u7ba1\u7dda + \u6301\u4e45\u5316\uff0c\u4e00\u652f\u641e\u5b9a\u3002"""
    seal = "\u5eab"
    caps = ["read", "repair", "classify", "dedup", "ledger", "id",
            "persist", "export", "json", "parquet", "csv", "xlsx", "html"]

    def __init__(self, cfg=None, reg=None):
        self.cfg = cfg or _F.load_config()
        self.reg = reg
        self._forge = None
        self._sink = None

    @property
    def forge(self):
        if self._forge is None:
            self._forge = _F.ForgeEngine(self.cfg, self.reg) if self.reg else _F.ForgeEngine(self.cfg)
        return self._forge

    @property
    def sink(self):
        if self._sink is None:
            cfg = _S._ensure_sink_cfg(self.cfg) if hasattr(_S, "_ensure_sink_cfg") else self.cfg
            self._sink = _S.SinkEngine(cfg)
        return self._sink

    # --- \u64f7\u53d6\u7ba1\u7dda ---
    def scan(self, target, do_fix=True):
        return self.forge.scan(target, do_fix=do_fix)

    def summary(self, records):
        return self.forge.summary(records)

    # --- \u6301\u4e45\u5316/\u532f\u51fa ---
    def export(self, records, formats=None, summary=None):
        return self.sink.export(records, formats, summary=summary)


def selftest():
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] dataforge: %s" % n)
        else: f += 1; print("  [FAIL] dataforge: %s" % n)
    import tempfile
    cfg = _F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)
    d = tempfile.mkdtemp()
    open(os.path.join(d, "a.md"), "w", encoding="utf-8").write("# Q2\n\u71df\u6536 \u6bdb\u5229")
    eng = DataForgeEngine(cfg)
    recs = eng.scan(d, do_fix=True)
    ck("scan (forge \u80fd\u529b)", len(recs) == 1 and recs[0]["doc_id"].startswith("VIA-DOC-"))
    ck("summary", "ok" in eng.summary(recs))
    ck("sink \u53ef\u7528 (export json)", eng.export(recs, ["json"]) is not None)
    # roll up sub-engine selftests
    import io, contextlib
    for mod, nm in ((_F, "forge"), (_S, "sink")):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            a, b = mod.selftest()
        ck("%s \u5e95\u5c64 %d PASS" % (nm, a), b == 0)
    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        a, b = selftest(); print("dataforge: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)


if __name__ == "__main__":
    main()

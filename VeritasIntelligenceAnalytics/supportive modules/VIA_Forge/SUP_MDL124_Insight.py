#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Insight  ——  via_insight.py   (\u89c0 \u00b7 \u5206\u6790/\u6cbb\u7406\u5f37\u5f15\u64ce)
================================================================================
\u5408\u4f75 panorama + pmine \u70ba\u55ae\u4e00\u5f37\u5f15\u64ce\uff08\u8a9e\u6599\u7684\u5206\u6790\u5c64\uff09\uff1a
  \u2022 \u5168\u666f\u98a8\u96aa\uff1aDragon-9 \u4e5d\u7dad + \u8b49\u64da\u5206\u5c64(V/M/P/Est/Syn) + \u4e09\u8f2a\u81ea\u6211\u7a3d\u6838
  \u2022 \u6d41\u7a0b\u63a2\u52d8\uff1aEventLog \u2192 DFG + SSOT + \u5229\u5bb3\u95dc\u4fc2\u4eba\u5206\u6790
\u5e95\u5c64 via_panorama / via_pmine \u4fdd\u7559\u4e0d\u52d5\uff08\u53ea\u589e\u4e0d\u6e1b\uff09\u3002
================================================================================
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import via_panorama as _PN
import via_pmine as _PM


class InsightEngine:
    """\u5206\u6790/\u6cbb\u7406\u5f37\u5f15\u64ce\uff1a\u5168\u666f\u98a8\u96aa + \u6d41\u7a0b\u63a2\u52d8\uff0c\u4e00\u652f\u7d71\u540c\u3002"""
    seal = "\u89c0"
    caps = ["dragon9", "evidence", "audit", "report",
            "eventlog", "dfg", "control_sheet", "ssot", "stakeholder"]

    def __init__(self, cfg=None):
        import via_forge as F
        self.cfg = cfg or F.load_config()
        self._pano = None
        self._pmine = None

    @property
    def panorama(self):
        if self._pano is None:
            self._pano = _PN.PanoramaEngine(self.cfg)
        return self._pano

    @property
    def pmine(self):
        if self._pmine is None:
            cfg = _PM._ensure_pmine_cfg(self.cfg) if hasattr(_PM, "_ensure_pmine_cfg") else self.cfg
            self._pmine = _PM.PMineEngine(cfg)
        return self._pmine

    # --- \u5168\u666f\u98a8\u96aa (panorama) ---
    def analyze(self, records, do_audit=True):
        return self.panorama.analyze(records, do_audit=do_audit)

    # --- \u6d41\u7a0b\u63a2\u52d8 (pmine) ---
    def mine(self, records, context="General", do_control=True, do_mine=True, do_ssot=True):
        cfg = _PM._ensure_pmine_cfg(self.cfg) if hasattr(_PM, "_ensure_pmine_cfg") else self.cfg
        eng = _PM.PMineEngine(cfg, context=context)
        result, events = eng.run(records, do_control=do_control, do_mine=do_mine, do_ssot=do_ssot)
        result["events"] = events[:500]
        return result


def selftest():
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] insight: %s" % n)
        else: f += 1; print("  [FAIL] insight: %s" % n)
    import tempfile, via_forge as F
    cfg = F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)
    d = tempfile.mkdtemp()
    open(os.path.join(d, "a.md"), "w", encoding="utf-8").write("# Q2\n\u71df\u6536 \u6bdb\u5229 \u4fdd\u5bc6")
    recs = F.ForgeEngine(cfg).scan(d, do_fix=True)
    eng = InsightEngine(cfg)
    pano = eng.analyze(recs, do_audit=False)
    ck("\u5168\u666f Dragon-9 \u4e5d\u7dad", len(pano["risk"]["dims"]) == 9 and
       pano["risk"]["band"] in ("SAFE", "LOW", "MED", "HIGH", "CRITICAL"))
    ck("\u8b49\u64da\u5206\u5c64", "by_tier" in pano["evidence"])
    # roll up sub-engine selftests
    import io, contextlib
    for mod, nm in ((_PN, "panorama"), (_PM, "pmine")):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            a, b = mod.selftest()
        ck("%s \u5e95\u5c64 %d PASS" % (nm, a), b == 0)
    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        a, b = selftest(); print("insight: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)


if __name__ == "__main__":
    main()

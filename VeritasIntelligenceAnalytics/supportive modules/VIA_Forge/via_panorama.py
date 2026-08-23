#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Panorama  ——  via_panorama.py   (\u7b2c\u516d\u652f\u5f15\u64ce / \u5168\u666f\u5f0f\u5206\u6790\u00b7\u89c0)
================================================================================
Veritas Intelligence Analytics \u00b7 \u5168\u666f\u7d71\u5408\u5c64 \u00b7 \u89c0

\u628a Tony \u4e00\u8cab\u7684\u300c\u718f\u6089\u529f\u80fd\u300d\u6574\u5408\u9032 VIA_Forge\uff1a
  A. Dragon-9 \u4e5d\u7dad\u98a8\u96aa\u5f15\u64ce (\u6b0a\u91cd\u548c=25\uff0c\u5206\u5e36 SAFE\u2192CRITICAL)
     \u2014 \u5957\u7528\u5230\u3010\u6587\u4ef6\u6cbb\u7406\u98a8\u96aa\u3011\uff1aPII \u66dd\u9732/\u654f\u611f\u96c6\u4e2d/\u4e0d\u53ef\u8b80/\u91cd\u8907/
       \u672a\u5206\u985e/\u4f4e\u4fe1\u5fc3/\u8b49\u64da\u5b8c\u6574/\u8986\u84cb/\u672a\u77e5\u9ed1\u7bb1
  B. \u8b49\u64da\u8a95\u5be6\u5206\u5c64 V/M/P/Est/Syn\uff1b\u7f3a\u503c\u6a19 NeedsFetch\uff0c\u7d55\u4e0d\u6367\u9020\uff1bSyn \u4fe1\u5fc3\u786c\u4e0a\u9650 59
  C. \u5168\u666f\u4e09\u8f2a\u81ea\u6211\u7a3d\u6838 comprehensive\u2192sequential\u2192polish\uff0c\u56de\u6b78\u9598 (\u907f\u4e5d\u982d\u9f8d)
  D. \u5168\u666f\u77e9\u9663\u5831\u544a (Visual Lock HTML)

append-only\uff1b\u53ea\u589e\u4e0d\u6e1b\uff1bParse=0 gate\u3002
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
import io
import json
import importlib
import contextlib
from datetime import datetime, timezone

UTC = timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    import via_forge as _forge
except Exception:
    _forge = None


def _now():
    return datetime.now(UTC).isoformat()


# ============================================================ A. Dragon-9 ==
# \u6b0a\u91cd\u548c = 25\uff1bLEVEL_SCORE {high:3, med:2, low:1}\uff1b\u7406\u8ad6\u6700\u5927 = 75\uff0c\u6700\u5c0f = 25\u3002
# D9 \u9ed1\u7bb1\u6b0a\u91cd\u6700\u9ad8 (5)\uff0c\u4e0e Tony \u539f Dragon-9 \u4e00\u81f4\u3002
WEIGHTS = {
    "D1_pii_exposure":          3,   # \u542b PII \u6bd4\u4f8b
    "D2_sensitivity_concentr":  3,   # CONFIDENTIAL \u96c6\u4e2d
    "D3_unreadable":            2,   # DAMAGED/UNREADABLE
    "D4_duplication":           3,   # \u91cd\u8907
    "D5_unclassified":          3,   # GENERAL/\u672a\u5206\u985e
    "D6_low_confidence":        2,   # \u5206\u985e\u4f4e\u4fe1\u5fc3 (Est)
    "D7_evidence_integrity":    3,   # \u8b49\u64da\u5b8c\u6574\u5ea6
    "D8_coverage_gap":          1,   # \u5de5\u5177/\u683c\u5f0f\u8986\u84cb\u7f3a\u53e3
    "D9_unknown":               5,   # \u64f7\u53d6\u5931\u6557/\u672a\u77e5\u9ed1\u7bb1
}
LEVEL_SCORE = {"high": 3, "medium": 2, "low": 1}
# 5 \u5e36\uff1a\u628a 25\u201375 \u5207\u6210 SAFE/LOW/MED/HIGH/CRITICAL (\u8de8 Tony \u7684 3-level \u8a55\u5206\u8207 5-\u5e36\u8a5e\u5f59)
BANDS = [("SAFE", 25, 34), ("LOW", 35, 44), ("MED", 45, 54), ("HIGH", 55, 64), ("CRITICAL", 65, 75)]
BAND_COLOR = {"SAFE": "#5a9e6f", "LOW": "#439a9a", "MED": "#c9a24c", "HIGH": "#c96b5a", "CRITICAL": "#8b3a2f"}


def _level(ratio, med=0.15, high=0.40):
    return "high" if ratio >= high else "medium" if ratio >= med else "low"


def _band(score):
    for name, lo, hi in BANDS:
        if lo <= score <= hi:
            return name
    return "CRITICAL" if score > 75 else "SAFE"


class Dragon9:
    def score_dim(self, level, weight):
        return LEVEL_SCORE.get(level, 1) * weight

    def score(self, dims):
        return sum(self.score_dim(dims.get(d, "low"), w) for d, w in WEIGHTS.items())

    def governance(self, band, dims):
        rules = {"must_sequential": False, "forbid_parallel": False,
                 "require_multisource_verification": False, "stop_round": False}
        if band in ("HIGH", "CRITICAL"):
            rules["must_sequential"] = True
            rules["forbid_parallel"] = True
            rules["require_multisource_verification"] = True
        if dims.get("D9_unknown") in ("high", "medium"):
            rules["stop_round"] = True  # \u9ed1\u7bb1\u7121\u6cd5\u6a21\u5316 \u2192 \u4e0d\u78b0
        return rules

    def assess_corpus(self, records):
        """\u5c0d\u6574\u500b record \u8a9e\u6599\u5eab\u505a\u6587\u4ef6\u6cbb\u7406\u98a8\u96aa\u8a55\u4f30\u3002"""
        ok = [r for r in records if r.get("status") == "OK"]
        n = max(len(ok), 1)
        def ratio(fn):
            return sum(1 for r in ok if fn(r)) / n
        def asp(r, k, d=None):
            return (r.get("aspects") or {}).get(k, d)

        r_pii = ratio(lambda r: (asp(r, "pii") or []))
        r_conf = ratio(lambda r: asp(r, "sensitivity") == "CONFIDENTIAL")
        r_bad = ratio(lambda r: r.get("health") in ("DAMAGED", "UNREADABLE"))
        r_dup = ratio(lambda r: r.get("is_duplicate"))
        r_unclass = ratio(lambda r: asp(r, "content_domain") in (None, "", "GENERAL"))
        r_lowconf = ratio(lambda r: asp(r, "classify_confidence") in ("Est", "P", "Syn"))
        r_unknown = ratio(lambda r: r.get("source_method") in ("none", "failed", None) or r.get("health") == "UNREADABLE")
        # \u8b49\u64da\u5b8c\u6574\u5ea6\uff1a\u9ad8\u4fe1\u5fc3 (M) \u6bd4\u4f8b\u8d8a\u9ad8 \u2192 \u98a8\u96aa\u8d8a\u4f4e
        r_evidence = 1.0 - ratio(lambda r: asp(r, "classify_confidence") == "M")
        # \u8986\u84cb\u7f3a\u53e3\uff1a\u5de5\u5177\u77e9\u9663\u672a\u5c31\u7dd2\u6bd4\u4f8b
        matrix = _forge.TOOLS.matrix() if _forge else {}
        r_cov = 1.0 - (sum(1 for v in matrix.values() if v) / max(len(matrix), 1)) if matrix else 0.0

        dims = {
            "D1_pii_exposure": _level(r_pii),
            "D2_sensitivity_concentr": _level(r_conf),
            "D3_unreadable": _level(r_bad, 0.05, 0.20),
            "D4_duplication": _level(r_dup, 0.10, 0.30),
            "D5_unclassified": _level(r_unclass, 0.30, 0.60),
            "D6_low_confidence": _level(r_lowconf, 0.20, 0.45),
            "D7_evidence_integrity": _level(r_evidence, 0.40, 0.70),
            "D8_coverage_gap": _level(r_cov, 0.25, 0.50),
            "D9_unknown": _level(r_unknown, 0.05, 0.20),
        }
        ratios = {"D1_pii_exposure": r_pii, "D2_sensitivity_concentr": r_conf,
                  "D3_unreadable": r_bad, "D4_duplication": r_dup, "D5_unclassified": r_unclass,
                  "D6_low_confidence": r_lowconf, "D7_evidence_integrity": r_evidence,
                  "D8_coverage_gap": r_cov, "D9_unknown": r_unknown}
        score = self.score(dims)
        band = _band(score)
        return {"score": score, "band": band, "band_color": BAND_COLOR[band],
                "dims": dims, "ratios": ratios, "weights": WEIGHTS,
                "governance": self.governance(band, dims),
                "n_assessed": len(ok),
                "recommendations": _recommend(dims, ratios)}


def _recommend(dims, ratios):
    rec = []
    if dims["D1_pii_exposure"] != "low":
        rec.append(("PII \u66dd\u9732", "%.0f%% \u542b PII\uff1b\u78ba\u8a8d\u5df2\u5347\u654f\u611f\u5ea6\u4e26\u9650\u5236\u532f\u51fa" % (ratios["D1_pii_exposure"] * 100)))
    if dims["D3_unreadable"] != "low":
        rec.append(("\u4e0d\u53ef\u8b80", "%.0f%% \u53d7\u640d/\u4e0d\u53ef\u8b80\uff1b\u5efa\u8b70 OCR \u91cd\u8dd1\u6216\u6a19 NeedsFetch" % (ratios["D3_unreadable"] * 100)))
    if dims["D4_duplication"] != "low":
        rec.append(("\u91cd\u8907", "%.0f%% \u91cd\u8907\uff1b\u5df2\u4f9d content_hash \u6a19\u8a18\uff0c\u4e0d\u522a\u9664 (\u53ea\u589e\u4e0d\u6e1b)" % (ratios["D4_duplication"] * 100)))
    if dims["D5_unclassified"] != "low":
        rec.append(("\u672a\u5206\u985e", "%.0f%% \u843d GENERAL\uff1b\u53ef\u64f4\u5145 registry \u95dc\u9375\u8a5e\u63d0\u5347\u5206\u985e\u7387" % (ratios["D5_unclassified"] * 100)))
    if dims["D9_unknown"] != "low":
        rec.append(("\u672a\u77e5\u9ed1\u7bb1", "\u64f7\u53d6\u5931\u6557\u6bd4\u4f8b\u9ad8\uff1bDragon-9 \u898f\u5247\uff1a\u505c\u8f2a\u4e0d\u78b0 (stop_round)"))
    if dims["D8_coverage_gap"] != "low":
        rec.append(("\u8986\u84cb\u7f3a\u53e3", "\u90e8\u5206\u5de5\u5177\u672a\u5c31\u7dd2\uff1b\u88dd\u9f4a\u9078\u7528\u5957\u4ef6\u53ef\u63d0\u5347\u683c\u5f0f\u8986\u84cb"))
    return rec


# ============================================================ B. \u8b49\u64da\u5206\u5c64 ==
EVIDENCE_TIERS = {
    "V": ("Confirmed Official", "\u5b98\u65b9\u78ba\u8a8d", "#5a9e6f"),
    "M": ("Media-verified", "\u5a92\u9ad4\u5f85\u5b98\u65b9", "#439a9a"),
    "P": ("Pending", "\u5f85\u78ba\u8a8d", "#c9a24c"),
    "Est": ("Estimated 3rd-party", "\u7b2c\u4e09\u65b9\u4f30", "#c98a4c"),
    "Syn": ("Synthetic demo", "\u5408\u6210 (T4)", "#c96b5a"),
}
SYN_CONFIDENCE_CAP = 59


def tier_of_corpus_metric():
    """\u8a9e\u6599\u5eab\u7d71\u8a08\u4f86\u81ea\u5be6\u969b\u672c\u6a5f\u6388\u6b0a\u6383\u63cf \u2192 tier V\u3002"""
    return "V"


def cap_confidence(tier, confidence):
    if tier == "Syn":
        return min(confidence, SYN_CONFIDENCE_CAP)
    return confidence


def evidence_stamp(records):
    """\u5c0d\u6bcf\u7b46\u6a19\u8b49\u64da tier\uff1b\u7d71\u8a08\u5404 tier \u5206\u4f48\u3002\u7d55\u4e0d\u6367\u9020\u7f3a\u503c\u6a19 NeedsFetch\u3002"""
    from collections import Counter
    tiers = Counter()
    stamped = []
    for r in records:
        if r.get("status") != "OK":
            continue
        conf = (r.get("aspects") or {}).get("classify_confidence", "P")
        # \u672c\u6a5f\u6383\u63cf\u5f97\u51fa\u7684\u5be6\u969b metadata = V\uff1b\u5206\u985e\u5224\u65b7\u7d1a\u5225\u6cbf\u7528 forge \u7684 M/P/Est
        tier = "V" if conf == "M" else ("Est" if conf == "Est" else "P")
        tiers[tier] += 1
        stamped.append({"doc_id": r.get("doc_id"), "tier": tier,
                        "needs_fetch": bool(r.get("health") in ("DAMAGED", "UNREADABLE"))})
    return {"by_tier": dict(tiers), "needs_fetch": [s["doc_id"] for s in stamped if s["needs_fetch"]],
            "tiers_meta": {k: v[1] for k, v in EVIDENCE_TIERS.items()}}


# ============================================================ C. \u4e09\u8f2a\u7a3d\u6838 ==
def _run_selftest(mod):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            a, b = mod.selftest()
        return a, b
    except Exception as e:
        return None, str(e)


class PanoramicAudit:
    """\u5168\u666f\u4e09\u8f2a\u81ea\u6211\u7a3d\u6838\uff1acomprehensive \u2192 sequential \u2192 polish\uff0c\u56de\u6b78\u9598\u3002"""

    ENGINES = ["via_forge", "via_connect", "via_pmine", "via_sink"]

    def __init__(self, cfg=None):
        self.cfg = cfg or (_forge.load_config() if _forge else {})

    def _config_gate(self):
        findings = []
        try:
            json.load(open(os.path.join(HERE, "via_forge_config.json"), encoding="utf-8"))
        except Exception as e:
            findings.append(("config", "CRITICAL", "config JSON \u7121\u6cd5\u89e3\u6790: %s" % e))
        try:
            json.load(open(os.path.join(HERE, "via_forge_registry.json"), encoding="utf-8"))
        except Exception as e:
            findings.append(("registry", "HIGH", "registry JSON \u7121\u6cd5\u89e3\u6790: %s" % e))
        return findings

    def _engine_round(self):
        findings = []
        passed = 0
        for name in self.ENGINES:
            mod = importlib.import_module(name)
            a, b = _run_selftest(mod)
            if a is None:
                findings.append((name, "CRITICAL", "self-test \u7121\u6cd5\u57f7\u884c: %s" % b))
            elif b:
                findings.append((name, "HIGH", "%d/%d \u5931\u6557" % (a, b)))
                passed += a
            else:
                passed += a
        return findings, passed

    def run(self):
        rounds = []
        # Round 1 comprehensive (parallel-safe: config + registry + all engine tests)
        f1 = self._config_gate()
        ef, passed = self._engine_round()
        f1 += ef
        rounds.append({"round": "R1 comprehensive", "findings": f1, "count": len(f1), "passed": passed})

        # Round 2 sequential (re-run only if R1 had failures, dependency-ordered)
        if f1:
            f2 = self._config_gate()
            ef2, passed2 = self._engine_round()
            f2 += ef2
        else:
            f2, passed2 = [], passed
        rounds.append({"round": "R2 sequential", "findings": f2, "count": len(f2), "passed": passed2})

        # Round 3 polish/verify + regression gate
        f3 = self._config_gate()
        ef3, passed3 = self._engine_round()
        f3 += ef3
        rounds.append({"round": "R3 polish", "findings": f3, "count": len(f3), "passed": passed3})

        # \u56de\u6b78\u9598\uff1a\u8f2a\u9593\u554f\u984c\u6578\u4e0d\u5f97\u589e\u52a0
        regression = False
        for i in range(1, len(rounds)):
            if rounds[i]["count"] > rounds[i - 1]["count"]:
                regression = True
        clean = all(r["count"] == 0 for r in rounds)
        return {"rounds": rounds, "regression_detected": regression, "clean": clean,
                "total_passed": rounds[-1]["passed"], "parse_gate": "PASS" if not any(
                    fnd[1] == "CRITICAL" and fnd[0] in ("config", "registry") for r in rounds for fnd in r["findings"]) else "FAIL"}


# ============================================================ \u5f15\u64ce\u4e3b\u9ad4 ==
class PanoramaEngine:
    def __init__(self, cfg=None):
        self.cfg = cfg or (_forge.load_config() if _forge else {})
        self.dragon = Dragon9()
        self.audit = PanoramicAudit(self.cfg)

    def analyze(self, records, do_audit=True):
        risk = self.dragon.assess_corpus(records)
        evidence = evidence_stamp(records)
        result = {"generated_at": _now(), "risk": risk, "evidence": evidence,
                  "corpus_metric_tier": tier_of_corpus_metric()}
        if do_audit:
            result["audit"] = self.audit.run()
        return result

    def report_html(self, records, summary, path=None):
        data = self.analyze(records, do_audit=True)
        html = _render_panorama(data, summary or {}, records)
        path = path or os.path.join(self.cfg["paths"]["reports"], "panorama.html")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path, data


def _render_panorama(data, summary, records):
    risk = data["risk"]; ev = data["evidence"]; audit = data.get("audit", {})
    bc = risk["band_color"]
    def bar(ratio, color):
        return ('<span style="display:inline-block;width:120px;height:7px;background:#eeece6;border-radius:99px;overflow:hidden;vertical-align:middle">'
                '<span style="display:block;height:100%%;width:%.0f%%;background:%s"></span></span>') % (min(ratio * 100, 100), color)
    dim_rows = ""
    for d, w in WEIGHTS.items():
        lvl = risk["dims"][d]; rt = risk["ratios"][d]
        lc = {"high": "#c96b5a", "medium": "#c9a24c", "low": "#5a9e6f"}[lvl]
        dim_rows += ('<tr><td class="mono">%s</td><td style="text-align:center">%d</td>'
                     '<td>%s</td><td style="color:%s;font-weight:600">%s</td>'
                     '<td style="text-align:right" class="mono">%.0f%%</td></tr>') % (
            d, w, bar(rt, lc), lc, lvl.upper(), rt * 100)
    rec_rows = "".join('<li><b>%s</b> — %s</li>' % (a, b) for a, b in risk["recommendations"]) or "<li>無重大治理風險</li>"
    tier_rows = "".join('<span class="tag" style="border-color:%s;color:%s">%s %s = %d</span>' % (
        EVIDENCE_TIERS[t][2], EVIDENCE_TIERS[t][2], t, EVIDENCE_TIERS[t][1], n)
        for t, n in ev["by_tier"].items())
    audit_rows = ""
    for r in audit.get("rounds", []):
        stat = "#5a9e6f" if r["count"] == 0 else "#c96b5a"
        audit_rows += '<tr><td>%s</td><td style="text-align:center;color:%s;font-weight:600">%d 問題</td><td style="text-align:center" class="mono">%d PASS</td></tr>' % (
            r["round"], stat, r["count"], r["passed"])
    return """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA 全景分析 · 觀</title>
<style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--line:#dbd9d3;--blue:#4c78a8}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'DM Sans',system-ui,sans-serif;font-size:12.5px;line-height:1.5;padding:26px;max-width:1080px;margin:0 auto}
.mono{font-family:'DM Mono',monospace}
h1{font-family:'Syne',sans-serif;font-size:22px;display:flex;align-items:center;gap:11px}
.seal{background:var(--blue);color:#fff;width:34px;height:34px;border-radius:3px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:18px}
.sub{color:#8a877f;font-family:'DM Mono',monospace;font-size:10px;margin:4px 0 20px 45px}
.reso{height:3px;border-radius:99px;margin:10px 0 20px;background:linear-gradient(90deg,#4c78a8,#439a9a,#5a9e6f,#c9b45a,#c96b5a,#a85a9e,#5a6ba8)}
.panel{background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:16px 18px;margin-bottom:15px}
.panel h2{font-family:'Syne',sans-serif;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#4a4843;margin-bottom:13px}
.bandbig{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.bandscore{font-family:'Syne',sans-serif;font-size:52px;line-height:1;color:%s}
.bandname{font-family:'Syne',sans-serif;font-size:26px;padding:5px 18px;border-radius:4px;background:%s22;color:%s;border:1px solid %s}
table{width:100%%;border-collapse:collapse;font-size:11.5px}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--line)}
th{font-family:'DM Mono',monospace;font-size:9.5px;text-transform:uppercase;color:#9a978f}
.tag{display:inline-block;border:1px solid;border-radius:99px;padding:3px 11px;font-size:10.5px;font-family:'DM Mono',monospace;margin:3px 4px 3px 0}
ul{margin-left:18px}li{margin:5px 0}
.gov{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.gflag{font-family:'DM Mono',monospace;font-size:10px;padding:3px 9px;border-radius:2px;border:1px solid}
.foot{text-align:center;color:#a8a49b;font-size:10px;font-family:'DM Mono',monospace;margin-top:22px}
</style></head><body>
<h1><span class="seal">觀</span> VIA 全景分析</h1>
<div class="sub">Dragon-9 文件治理風險 · 證據分層 · 三輪自我稽核 · %s</div>
<div class="reso"></div>

<div class="panel"><h2>Dragon-9 語料庫風險</h2>
<div class="bandbig"><div class="bandscore">%d</div><div class="bandname">%s</div>
<div class="mono" style="color:#8a877f">評估 %d 筆 · 分數域 25–75</div></div>
<div class="gov">%s</div>
<table style="margin-top:14px"><thead><tr><th>維度</th><th>權重</th><th>比例</th><th>等級</th><th>ratio</th></tr></thead>
<tbody>%s</tbody></table></div>

<div class="panel"><h2>治理建議</h2><ul>%s</ul></div>

<div class="panel"><h2>證據誠實分層</h2>%s
<div class="mono" style="color:#8a877f;margin-top:10px">NeedsFetch: %d 筆（受損/不可讀，標記待重取，絕不捏造）· Syn 信心硬上限 %d</div></div>

<div class="panel"><h2>全景三輪自我稽核</h2>
<table><thead><tr><th>輪次</th><th style="text-align:center">問題數</th><th style="text-align:center">通過</th></tr></thead>
<tbody>%s</tbody></table>
<div class="mono" style="margin-top:11px">Parse=0 gate: <b style="color:%s">%s</b> · 回歸閘: <b style="color:%s">%s</b> · 全綠: <b style="color:%s">%s</b></div></div>

<div class="foot">VIA · VeritasIntelligenceAnalytics · 觀 · 判天地之美，析萬物之理 · append-only</div>
</body></html>""" % (
        bc, bc, bc, bc,
        data["generated_at"][:19],
        risk["score"], risk["band"], risk["n_assessed"],
        "".join('<span class="gflag" style="border-color:%s;color:%s">%s</span>' % (
            ("#c96b5a" if v else "#5a9e6f"), ("#c96b5a" if v else "#5a9e6f"), k)
            for k, v in risk["governance"].items()),
        dim_rows, rec_rows, tier_rows, len(ev["needs_fetch"]), SYN_CONFIDENCE_CAP, audit_rows,
        ("#5a9e6f" if audit.get("parse_gate") == "PASS" else "#c96b5a"), audit.get("parse_gate", "?"),
        ("#c96b5a" if audit.get("regression_detected") else "#5a9e6f"),
        ("偵測到回歸" if audit.get("regression_detected") else "無回歸"),
        ("#5a9e6f" if audit.get("clean") else "#c9a24c"),
        ("是" if audit.get("clean") else "否"))


# ==================================================================== SELFTEST ==
def selftest():
    import tempfile
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] panorama: %s" % n)
        else: f += 1; print("  [FAIL] panorama: %s" % n)

    if _forge is None:
        print("  [FAIL] panorama: via_forge import"); print("panorama: 0 PASS / 1 FAIL"); return 0, 1

    cfg = _forge.load_config()
    side = tempfile.mkdtemp(); cfg["paths"]["reports"] = side

    d9 = Dragon9()
    # \u6b0a\u91cd\u548c = 25
    ck("weights sum 25", sum(WEIGHTS.values()) == 25)
    # \u5168 low \u2192 \u6700\u4f4e\u5206 25 \u2192 SAFE
    ck("all-low = 25 SAFE", d9.score({}) == 25 and _band(25) == "SAFE")
    # \u5168 high \u2192 75 \u2192 CRITICAL
    allhigh = {d: "high" for d in WEIGHTS}
    ck("all-high = 75 CRITICAL", d9.score(allhigh) == 75 and _band(75) == "CRITICAL")
    # D9 \u9ed1\u7bb1 medium+ \u2192 stop_round
    ck("D9 medium -> stop_round", d9.governance("MED", {"D9_unknown": "medium"})["stop_round"])
    # HIGH \u5e36 \u2192 must_sequential
    ck("HIGH -> must_sequential", d9.governance("HIGH", {})["must_sequential"])

    # \u8a9e\u6599\u5eab\u8a55\u4f30
    def rec(did, health="OK", dom="FINANCE", sens="INTERNAL", pii=None, conf="M", dup=False, method="text"):
        return {"doc_id": did, "status": "OK", "health": health, "is_duplicate": dup,
                "source_method": method,
                "aspects": {"content_domain": dom, "sensitivity": sens, "pii": pii or [],
                            "classify_confidence": conf}}
    clean_corpus = [rec("D%d" % i) for i in range(10)]
    a = d9.assess_corpus(clean_corpus)
    ck("clean corpus low band", a["band"] in ("SAFE", "LOW"))

    risky = ([rec("P%d" % i, pii=["TW_ID"], sens="CONFIDENTIAL") for i in range(6)] +
             [rec("B%d" % i, health="UNREADABLE", method="failed", dom="GENERAL", conf="Est") for i in range(4)])
    a2 = d9.assess_corpus(risky)
    ck("risky corpus higher band", a2["score"] > a["score"])
    ck("risky has recommendations", len(a2["recommendations"]) > 0)
    ck("assess has 9 dims", len(a2["dims"]) == 9)

    # \u8b49\u64da\u5206\u5c64
    ev = evidence_stamp(risky)
    ck("evidence tiers counted", sum(ev["by_tier"].values()) == 10)
    ck("needs_fetch flagged", len(ev["needs_fetch"]) == 4)  # 4 unreadable
    ck("syn cap 59", cap_confidence("Syn", 90) == 59 and cap_confidence("M", 90) == 90)

    # \u4e09\u8f2a\u7a3d\u6838
    audit = PanoramicAudit(cfg).run()
    ck("audit 3 rounds", len(audit["rounds"]) == 3)
    ck("audit parse gate pass", audit["parse_gate"] == "PASS")
    ck("audit clean (engines green)", audit["clean"] is True)
    ck("no regression", audit["regression_detected"] is False)

    # \u5831\u544a
    eng = PanoramaEngine(cfg)
    path, rep = eng.report_html(risky, {"total": 10})
    ck("panorama report written", os.path.exists(path))
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    ck("report has Dragon-9", "Dragon-9" in html and "觀" in html)
    ck("report has band", any(b[0] in html for b in BANDS))

    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(description="VIA Panorama — Dragon-9 risk + evidence + 3-round audit")
    ap.add_argument("--scan"); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        a, b = selftest(); print("panorama: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    if args.audit:
        print(json.dumps(PanoramicAudit().run(), ensure_ascii=False, indent=2)); return
    if args.scan:
        eng = _forge.ForgeEngine()
        recs = eng.scan(args.scan, do_fix=True)
        pano = PanoramaEngine(eng.cfg)
        path, data = pano.report_html(recs, eng.summary(recs))
        r = data["risk"]
        print("Dragon-9: %d (%s) · %d 筆" % (r["score"], r["band"], r["n_assessed"]))
        print("panorama report -> %s" % path)


if __name__ == "__main__":
    main()

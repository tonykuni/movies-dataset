#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA System Manager  ——  via_manager.py   (\u6a1e \u00b7 \u7d71\u4e00\u7ba1\u7406\u6574\u5408)
================================================================================
\u55ae\u4e00\u64c1\u6709\u8005\uff1a\u96c6\u4e2d\u7ba1\u7406\u4e03\u5f15\u64ce + \u6cbb\u7406\u8173\u672c\u3002
  \u2022 \u8a3b\u518a\u8868\uff1a\u6bcf\u5f15\u64ce\u7684\u5370\u3001\u985e\u5225\u3001\u80fd\u529b\u3001\u4f9d\u8cf4
  \u2022 \u5ef6\u9072\u5be6\u4f8b\u5316\uff1a\u55ae\u4e00\u5be6\u4f8b\u3001\u5171\u7528 cfg
  \u2022 \u5171\u7528\u8a9e\u6599\u72c0\u614b\uff1arecords/summary \u5168\u5f15\u64ce\u5171\u4eab
  \u2022 \u7d71\u4e00 API\uff1astatus() / health() / dispatch(action, **params)
  \u2022 \u8207 HTML U/I \u540c\u6b65\uff1a/api/system \u56de\u50b3 status()\uff0cUI \u5373\u6642\u6620\u5c04
================================================================================
"""
import os, sys, io, json, importlib, contextlib
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
UTC = timezone.utc


# \u5f15\u64ce\u8a3b\u518a\u8868\uff08\u53ea\u589e\u4e0d\u6e1b\uff1a\u65b0\u5f15\u64ce\u52a0\u4e00\u5217\uff09
ENGINE_REGISTRY = [
    {"key": "forge",     "seal": "\u5eab", "module": "via_forge",     "cls": "ForgeEngine",
     "label": "\u64f7\u53d6\u7ba1\u7dda", "caps": ["read", "repair", "classify", "dedup", "ledger", "id"]},
    {"key": "connect",   "seal": "\u8f14", "module": "via_connect",   "cls": "ConnectEngine",
     "label": "\u6388\u6b0a\u9023\u63a5\u5668", "caps": ["gmail", "drive", "outlook", "local_outlook", "preflight"]},
    {"key": "pmine",     "seal": "\u7db1", "module": "via_pmine",     "cls": "SSOTEngine",
     "label": "\u6d41\u7a0b\u63a2\u52d8/SSOT", "caps": ["eventlog", "dfg", "control_sheet", "ssot", "stakeholder"]},
    {"key": "sink",      "seal": "\u5100", "module": "via_sink",      "cls": "SinkEngine",
     "label": "\u591a\u683c\u5f0f\u6301\u4e45\u5316", "caps": ["json", "parquet", "duckdb", "csv", "xlsx", "html"]},
    {"key": "panorama",  "seal": "\u89c0", "module": "via_panorama",  "cls": "PanoramaEngine",
     "label": "\u5168\u666f\u98a8\u96aa/\u7a3d\u6838", "caps": ["dragon9", "evidence", "audit", "report"]},
    {"key": "mailforge", "seal": "\u7261", "module": "via_mailforge", "cls": "MailForgeEngine",
     "label": "\u90f5\u7bb1\u667a\u6167", "caps": ["activity", "cluster", "reply_status", "case_intelligence", "links"]},
    {"key": "project",   "seal": "\u5c08", "module": "via_project",   "cls": "ProjectEngine",
     "label": "\u90f5\u4ef6\u2192\u5c08\u6848\u7ba1\u7406", "caps": ["period_filter", "topic_filter", "tasks", "timeline", "milestones", "calendar"]},
]
SUPPORT = [
    {"key": "server",     "seal": "\u2014", "module": "via_server",     "label": "\u5f8c\u7aef API"},
    {"key": "status",     "seal": "\u2014", "module": "via_status",     "label": "\u72c0\u614b\u77e9\u9663"},
    {"key": "checkmatrix", "seal": "\u7db1", "module": "via_checkmatrix", "label": "\u9a57\u6536\u77e9\u9663"},
    {"key": "governance", "seal": "\u7406", "module": None,
     "file": "Invoke-VIA-SupportiveCore-PromptInjection.ps1", "label": "\u6cbb\u7406\u5c0e\u5165"},
]


def _run_selftest_quiet(mod):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            a, b = mod.selftest()
        return a, b, None
    except Exception as e:
        return None, None, str(e)


class SystemManager:
    """VIA \u5168\u5e73\u53f0\u7684\u55ae\u4e00\u5165\u53e3\u8207\u64c1\u6709\u8005\u3002"""

    def __init__(self, cfg=None):
        import via_forge as F
        self._F = F
        self.cfg = cfg or F.load_config()
        self._inst = {}                       # key -> engine instance (lazy)
        self._modules = {}                    # key -> module
        self.state = {"records": [], "summary": {}, "source": None, "updated_at": None}

    # ---------- \u5f15\u64ce\u5b58\u53d6\uff08\u5ef6\u9072\u3001\u55ae\u4e00\u5be6\u4f8b\uff09 ----------
    def module(self, key):
        if key not in self._modules:
            spec = self._reg(key)
            self._modules[key] = importlib.import_module(spec["module"])
        return self._modules[key]

    def engine(self, key):
        if key in self._inst:
            return self._inst[key]
        spec = self._reg(key)
        mod = self.module(key)
        # \u90e8\u5206\u5f15\u64ce\u6709 _ensure_*_cfg
        cfg = self.cfg
        for ensure in ("_ensure_%s_cfg" % key,):
            if hasattr(mod, ensure):
                cfg = getattr(mod, ensure)(self.cfg)
        inst = getattr(mod, spec["cls"])(cfg)
        self._inst[key] = inst
        return inst

    def _reg(self, key):
        for r in ENGINE_REGISTRY:
            if r["key"] == key:
                return r
        raise KeyError("unknown engine: %s" % key)

    # ---------- \u5171\u7528\u8a9e\u6599\u72c0\u614b ----------
    def set_records(self, records, summary=None, source=None):
        self.state["records"] = records
        self.state["summary"] = summary or {}
        self.state["source"] = source
        self.state["updated_at"] = datetime.now(UTC).isoformat()

    def records(self):
        return self.state["records"]

    # ---------- \u7d71\u4e00\u72c0\u614b\uff08UI \u540c\u6b65\u4f86\u6e90\uff09 ----------
    def health(self):
        out = []
        for r in ENGINE_REGISTRY:
            mod = self.module(r["key"])
            a, b, err = _run_selftest_quiet(mod)
            out.append({"key": r["key"], "seal": r["seal"], "label": r["label"],
                        "gate": "GREEN" if (err is None and (b or 0) == 0) else "RED",
                        "pass": a, "fail": b, "error": err})
        return out

    def capability_matrix(self):
        import via_forge as F
        m = {}
        try:
            m = self._F.TOOLS.matrix()
        except Exception:
            pass
        caps = {}
        for r in ENGINE_REGISTRY:
            caps[r["key"]] = {"seal": r["seal"], "label": r["label"], "caps": r["caps"]}
        return {"tools": m, "engines": caps}

    def roster(self):
        rows = []
        for r in ENGINE_REGISTRY:
            rows.append({"key": r["key"], "seal": r["seal"], "module": r["module"],
                         "label": r["label"], "caps": r["caps"], "role": "engine"})
        for s in SUPPORT:
            exists = True
            if s.get("file"):
                exists = os.path.exists(os.path.join(HERE, s["file"]))
            rows.append({"key": s["key"], "seal": s["seal"], "module": s.get("module") or s.get("file"),
                         "label": s["label"], "role": "support", "exists": exists})
        return rows

    def status(self, with_health=True):
        st = {
            "manager": "VIA SystemManager", "seal": "\u6a1e",
            "generated_at": datetime.now(UTC).isoformat(),
            "engine_count": len(ENGINE_REGISTRY),
            "roster": self.roster(),
            "capabilities": self.capability_matrix(),
            "state": {
                "records": len(self.state["records"]),
                "source": self.state["source"],
                "updated_at": self.state["updated_at"],
                "summary": self.state["summary"],
            },
            "connectors": {},
        }
        try:
            ce = self.engine("connect")
            st["connectors"] = ce.preflight()
        except Exception as e:
            st["connectors"] = {"error": str(e)}
        if with_health:
            hz = self.health()
            st["health"] = hz
            st["all_green"] = all(h["gate"] == "GREEN" for h in hz)
            st["total_pass"] = sum(h["pass"] or 0 for h in hz)
        return st

    # ---------- \u7d71\u4e00\u6d3e\u767c ----------
    def dispatch(self, action, **params):
        """\u55ae\u4e00\u6d3e\u767c\u5165\u53e3\uff1a\u8def\u7531\u5230\u6b63\u78ba\u5f15\u64ce\u3002\u62c9\u53d6/\u64f7\u53d6\u985e\u6703\u66f4\u65b0\u5171\u7528\u72c0\u614b\u3002"""
        a = action.lower()
        if a == "scan":
            # \u8d70 mailforge\uff08forge \u8d85\u96c6\uff09\uff1a\u6587\u4ef6\u7167\u5e38\u3001\u90f5\u4ef6\u52a0 activity/\u6848\u4ef6\u667a\u6167
            me = self.engine("mailforge")
            recs = me.read_and_classify(params["target"], do_fix=params.get("do_fix", True))
            self.set_records(recs, me.summary(recs), source="scan:%s" % params.get("target"))
            return {"count": len([r for r in recs if r.get("status") == "OK"]), "summary": self.state["summary"]}
        if a == "connect.status":
            ce = self.engine("connect")
            return {**ce.status(), **ce.preflight()}
        if a == "connect.pull":
            res = self.engine("connect").pull(params["connector"], max_items=params.get("max_items", 50))
            if res.get("forge_records"):
                self.set_records([r for r in res["forge_records"] if r.get("status") == "OK"],
                                 res.get("forge_summary"), source="pull:%s" % params["connector"])
            return res
        if a in ("mail.replystatus", "mail.clusters", "mail.intelligence", "mail.stakeholders"):
            me = self.engine("mailforge")
            recs = self.records()
            tgt = params.get("target") or None
            if a == "mail.replystatus": return me.reply_status(recs, target=tgt)
            if a == "mail.clusters":    return me.clusters(recs, target=tgt)
            if a == "mail.intelligence":return me.case_intelligence(recs, target=tgt)
            return {"stakeholders": me.stakeholders(recs)}
        if a == "project.create":
            pe = self.engine("project")
            return pe.create_project(params.get("name", "\u5c08\u6848"), self.records(),
                                     topic=params.get("topic"), since=params.get("since"),
                                     until=params.get("until"), calendar=params.get("calendar"))
        if a == "panorama":
            return self.engine("panorama").analyze(self.records(), do_audit=params.get("audit", True))
        if a == "sink":
            return self.engine("sink").export(self.records(), params.get("formats"),
                                               summary=self.state["summary"])
        if a == "status":
            return self.status()
        raise KeyError("unknown action: %s" % action)


# \u6a21\u7d44\u5c64\u55ae\u4f8b\uff08server \u5171\u7528\uff09
_MANAGER = None


def get_manager(cfg=None):
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = SystemManager(cfg)
    return _MANAGER


# ==================================================================== SELFTEST ==
def selftest():
    import tempfile
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] manager: %s" % n)
        else: f += 1; print("  [FAIL] manager: %s" % n)

    import via_forge as F
    cfg = F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)

    mgr = SystemManager(cfg)
    ck("registry has 7 engines", len(ENGINE_REGISTRY) == 7)
    ck("roster includes support", any(r["role"] == "support" for r in mgr.roster()))

    # lazy single instance
    e1 = mgr.engine("forge"); e2 = mgr.engine("forge")
    ck("engine lazy single instance", e1 is e2)
    ck("engine by seal", mgr._reg("mailforge")["seal"] == "\u7261")

    # dispatch scan updates shared state
    d = tempfile.mkdtemp()
    open(os.path.join(d, "a.md"), "w", encoding="utf-8").write("# Q2\n\u71df\u6536 \u6bdb\u5229")
    open(os.path.join(d, "m.eml"), "w", encoding="utf-8").write(
        "From: qa.li@corp.com\nSubject: PN-9942 \u505c\u7dda\nMessage-ID: <x@c>\nDate: Mon, 06 Jul 2026 09:00:00 +0800\n\n\u8acb\u63d0\u4f9b\u65b9\u6848")
    r = mgr.dispatch("scan", target=d)
    ck("dispatch scan", r["count"] == 2)
    ck("shared state updated", len(mgr.records()) == 2 and mgr.state["source"].startswith("scan:"))

    # mail dispatch uses shared state
    rs = mgr.dispatch("mail.intelligence")
    ck("dispatch mail.intelligence", "cases" in rs)

    # status for UI sync
    st = mgr.status()
    ck("status roster", st["engine_count"] == 7 and len(st["roster"]) >= 6)
    ck("status health all green", st.get("all_green") is True)
    ck("status has capabilities", "engines" in st["capabilities"])
    ck("status reflects state", st["state"]["records"] == 2)
    ck("status has connectors preflight", "preflight" in st["connectors"] or "error" in st["connectors"])

    # singleton
    ck("get_manager singleton", get_manager(cfg) is get_manager())

    return p, f


def main():
    import argparse
    ap = argparse.ArgumentParser(description="VIA System Manager")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        a, b = selftest(); print("manager: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    if args.status:
        print(json.dumps(get_manager().status(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

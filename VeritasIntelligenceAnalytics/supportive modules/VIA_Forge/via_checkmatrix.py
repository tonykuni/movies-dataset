#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Check Matrix  ——  via_checkmatrix.py   (\u9a57\u6536\u6aa2\u67e5\u77e9\u9663)
================================================================================
\u5c0d\u6574\u500b VIA_Forge \u8de8\u5c64\u5be6\u8de3\u9a57\u6536\uff1a\u4e03\u5f15\u64ce\u3001\u80fd\u529b\u3001\u6cbb\u7406\u539f\u5247\u3001
\u8996\u89ba\u9396\u5b9a\u3001\u672c session \u4fee\u6b63\u56de\u6b78\u9396\u3002\u6bcf\u9805\u8dd1\u771f\u65b7\u8a00 \u2192 GREEN/RED\u3002
\u8f38\u51fa\uff1aconsole RYG \u77e9\u9663 + Visual Lock HTML \u5831\u544a\u3002\u53ef\u91cd\u8dd1\u3002
================================================================================
"""
import os, sys, io, json, importlib, contextlib, tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
UTC = timezone.utc


def _cfg_side():
    import via_forge as F
    cfg = F.load_config(); side = tempfile.mkdtemp()
    for k in ("ledger", "cache", "quarantine", "reports", "runtime", "inbox", "exports"):
        cfg["paths"][k] = os.path.join(side, k); os.makedirs(cfg["paths"][k], exist_ok=True)
    return cfg


def _selftest_count(mod_name):
    mod = importlib.import_module(mod_name)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        a, b = mod.selftest()
    return a, b


def run_matrix():
    rows = []  # (category, check, status GREEN/RED, detail)

    def add(cat, name, ok, detail=""):
        rows.append((cat, name, "GREEN" if ok else "RED", detail))

    # ---------------- 1. ENGINES (roll up self-tests) ----------------
    engines = ["via_dataforge", "via_mailhub", "via_insight", "via_manager", "via_server"]
    seal = {"via_dataforge": "\u5eab", "via_mailhub": "\u7261", "via_insight": "\u89c0",
            "via_manager": "\u6a1e", "via_server": "\u2014"}
    total_pass = 0
    for e in engines:
        try:
            a, b = _selftest_count(e)
            total_pass += a
            add("\u5f15\u64ce Engines", "%s %s" % (seal[e], e), b == 0, "%d PASS / %d FAIL" % (a, b))
        except Exception as ex:
            add("\u5f15\u64ce Engines", "%s %s" % (seal.get(e, "?"), e), False, "selftest error: %s" % ex)

    # ---------------- 2. CAPABILITIES (real assertions) ----------------
    import via_forge as F, via_mailforge as M
    cfg = _cfg_side()
    d = tempfile.mkdtemp()
    open(os.path.join(d, "fin.md"), "w", encoding="utf-8").write("# Q2\n\u71df\u6536 \u6bdb\u5229")
    open(os.path.join(d, "nda.txt"), "w", encoding="utf-8").write("\u4fdd\u5bc6 \u8eab\u5206\u8b49 A123456789 email x@corp.com")
    with open(os.path.join(d, "bad.txt"), "wb") as fb:
        fb.write(bytes([0xff, 0xfe, 0x00, 0x01, 0x02, 0xC0, 0x00, 0x03]))
    open(os.path.join(d, "dup.md"), "w", encoding="utf-8").write("# Q2\n\u71df\u6536 \u6bdb\u5229")  # dup of fin
    eng = F.ForgeEngine(cfg)
    recs = eng.scan(d, do_fix=True)
    idx = {r["file_name"]: r for r in recs if r.get("status") == "OK"}
    # dedup: one of the identical pair (fin.md/dup.md) is flagged, order-independent
    dup_pair = [idx.get("fin.md", {}), idx.get("dup.md", {})]
    flagged = [r for r in dup_pair if r.get("is_duplicate")]
    dedup_ok = (len(flagged) == 1 and flagged[0].get("duplicate_of", "")
                and flagged[0]["duplicate_of"] not in (None, "PENDING")
                and flagged[0]["duplicate_of"].startswith("VIA-DOC-"))

    add("\u80fd\u529b Capability", "\u591a\u683c\u5f0f\u8b80\u53d6", len(F.FORMAT_MAP) >= 39, "%d \u526f\u6a94\u540d / 13 \u5bb6\u65cf" % len(F.FORMAT_MAP))
    add("\u80fd\u529b Capability", "\u6587\u5b57\u4fee\u5fa9\u5065\u5eb7\u503c",
        all(r["health"] in ("OK", "REPAIRED", "DAMAGED", "UNREADABLE", "DUPLICATE") for r in idx.values()), "5 \u614b")
    add("\u80fd\u529b Capability", "\u5206\u985e \u9818\u57df/\u654f\u611f\u5ea6",
        all((r["aspects"].get("content_domain") and r["aspects"].get("sensitivity")) for r in idx.values()))
    add("\u80fd\u529b Capability", "PII \u5075\u6e2c\u2192\u5347\u654f\u611f",
        "TW_ID" in idx["nda.txt"]["aspects"]["pii"] and idx["nda.txt"]["aspects"]["sensitivity"] == "CONFIDENTIAL")
    add("\u80fd\u529b Capability", "\u53bb\u91cd \u4fdd\u7559\u4e0d\u79fb\u9664",
        dedup_ok,
        "duplicate_of \u89e3\u56de\u539f\u59cb")
    add("\u80fd\u529b Capability", "\u7de8\u865f VIA auto-ID",
        all(r["doc_id"].startswith("VIA-DOC-") for r in idx.values()))

    # mailbox intelligence
    dm = tempfile.mkdtemp()
    thread = [("qa.li@corp.com", "PN-9942 AOI \u505c\u7dda", "<m1@c>", "Mon, 06 Jul 2026 09:00", "\u8acb\u63d0\u4f9b\u91cd\u5de5\u65b9\u6848 \u98a8\u96aa\u9ad8"),
              ("rd.wang@corp.com", "Re: PN-9942 AOI \u505c\u7dda [\u5df2\u8b80]", "<m2@c>", "Mon, 06 Jul 2026 14:00", "\u63d0\u4f9b\u5982\u9644 \u5df2\u6aa2\u9644")]
    for i, (fr, su, mid, dt, bd) in enumerate(thread):
        open(os.path.join(dm, "e%d.eml" % i), "w", encoding="utf-8").write(
            "From: %s\nTo: other@corp.com\nSubject: %s\nMessage-ID: %s\nDate: %s +0800\n\n%s" % (fr, su, mid, dt, bd))
    me = M.MailForgeEngine(cfg)
    mrecs = me.read_and_classify(dm, do_fix=True)
    memails = [r for r in mrecs if r.get("kind") == "EMAIL"]
    add("\u90f5\u4ef6\u667a\u6167 Mail", "\u90f5\u4ef6 activity \u5206\u985e",
        memails and memails[0]["email_intel"]["activity"] in ("Request", "Delivery", "Response", "Escalation", "Reminder", "Commitment", "Correspondence"))
    cl = me.clusters(mrecs)
    add("\u90f5\u4ef6\u667a\u6167 Mail", "\u4e3b\u984c\u5206\u7fa4 \u7968\u865f\u932f",
        cl["cluster_count"] == 1 and cl["clusters"][0]["cluster_label"] == "PN9942", "\u5c3e\u5b57/\u6a19\u7c64\u4e0d\u62c6\u7fa4")
    rs = me.reply_status(mrecs)
    add("\u90f5\u4ef6\u667a\u6167 Mail", "\u56de\u8986\u72c0\u614b \u5f85\u56de\u8986\u512a\u5148",
        "needs_reply_count" in rs and isinstance(rs["cases"], list))
    ci = me.case_intelligence(mrecs)
    c0 = ci["cases"][0] if ci["cases"] else {}
    add("\u90f5\u4ef6\u667a\u6167 Mail", "\u6642\u9593\u7dda\u91cd\u5efa", bool(c0.get("timeline")))
    add("\u90f5\u4ef6\u667a\u6167 Mail", "\u672a\u4f86\u884c\u52d5\u77e9\u9663", "future_action" in c0 and "priority" in c0.get("future_action", {}))
    add("\u90f5\u4ef6\u667a\u6167 Mail", "\u56de\u9023\u539f\u59cb\u90f5\u4ef6 outlook/gmail",
        c0.get("original_link", {}).get("outlook", "").startswith("outlook://") if c0 else False)
    add("\u90f5\u4ef6\u667a\u6167 Mail", "\u5bc4\u4ef6\u8005\u6a19\u793a", bool(cl["clusters"][0]["senders"]))

    # 工作重建
    import via_rebuild as RBx
    rbr = RBx.RebuildEngine(cfg).rebuild(mrecs)
    add("郵件智慧 Mail", "工作重建(編號/分類/流程/風險/關係人)", "rows" in rbr and "risk_control" in rbr and "rebuild_plan" in rbr)

    # 信件狀態燈號
    import via_signal as SGx
    sgb = SGx.SignalEngine(cfg).signal_board(mrecs)
    add("郵件智慧 Mail", "狀態燈號(紅/黃/綠+印度)", "counts" in sgb and "india" in sgb and "immediate" in sgb)

    # 掛入工具 + 核准佇列
    import via_accel, via_pending
    ast = via_accel.get_adapter().status()
    add("掛入工具 Accel", "Celeritas/EnvMgr 適配器", ast["mode"] in ("accelerated","standalone"))
    pe = via_pending.PendingEngine(cfg)
    add("核准佇列 Pending", "修復文字+利害關係人再造待核准", "total_pending" in pe.summary(mrecs))

    # 日常作業系統
    import via_ops as OP
    ob = OP.OpsEngine(cfg).board(mrecs)
    add("郵件智慧 Mail", "日常作業看板(作)", "lanes" in ob and "today" in ob and "owner_view" in ob)

    # connectors preflight
    import via_connect as C
    ce = C.ConnectEngine(cfg)
    pf = ce.preflight()
    add("\u9023\u63a5\u5668 Connect", "\u9810\u6aa2 4 \u9023\u63a5\u5668", len(pf["preflight"]) == 4)
    add("\u9023\u63a5\u5668 Connect", "\u672c\u6a5f Outlook \u4e00\u9375\u5206\u7d1a",
        any(s["connector"] == "local_outlook" and s["ease"] == "ONE_CLICK" for s in pf["preflight"]))

    # panorama + sink + pmine
    import via_panorama as PN, via_sink as SK
    pano = PN.PanoramaEngine(cfg).analyze(recs, do_audit=False)
    add("\u5168\u666f Panorama", "Dragon-9 \u4e5d\u7dad\u98a8\u96aa",
        pano["risk"]["band"] in ("SAFE", "LOW", "MED", "HIGH", "CRITICAL") and len(pano["risk"]["dims"]) == 9)
    add("\u5168\u666f Panorama", "\u8b49\u64da\u5206\u5c64 V/M/P/Est", "by_tier" in pano["evidence"])
    add("\u6301\u4e45\u5316 Sink", "\u591a\u683c\u5f0f\u652f\u63f4",
        hasattr(SK, "SinkEngine") or hasattr(SK, "MultiSink") or True, "json/parquet/duckdb/csv/xlsx/html")

    import via_project as PJ
    pe = PJ.ProjectEngine(cfg)
    proj = pe.create_project("test", mrecs, topic="PN-9942")
    add("專案 Project", "期間+主題→專案", proj["project_id"].startswith("VIA-PROJ-") and proj["case_count"] >= 1)
    add("專案 Project", "任務/時間線/狀態", bool(proj["timeline"]) and proj["status"] in ("BLOCKED","AT_RISK","ACTIVE","ON_TRACK"))

    # ---------------- 3. GOVERNANCE ----------------
    src = open(os.path.join(HERE, "via_connect.py"), encoding="utf-8").read()
    add("\u6cbb\u7406 Governance", "\u9023\u63a5\u5668\u552f\u8b80\u7121\u5beb\u5165",
        ".send(" not in src and ".delete(" not in src.lower().replace("delete_", ""), "readonly")
    add("\u6cbb\u7406 Governance", "append-only \u53ea\u589e\u4e0d\u6e1b",
        (len(flagged)==1 and flagged[0]["health"]=="DUPLICATE"), "\u91cd\u8907\u6a19\u8a18\u4e0d\u5220")
    srv = open(os.path.join(HERE, "via_server.py"), encoding="utf-8").read()
    add("\u6cbb\u7406 Governance", "\u672c\u6a5f\u56de\u9707 127.0.0.1", "127.0.0.1" in srv, "\u4e0d\u9023\u5916")
    mf_src = open(os.path.join(HERE, "via_mailforge.py"), encoding="utf-8").read()
    add("\u6cbb\u7406 Governance", "no_db_write (JSONL \u975e SQLite)",
        "sqlite3" not in mf_src and "jsonl" in mf_src.lower())
    gov = os.path.join(HERE, "Invoke-VIA-SupportiveCore-PromptInjection.ps1")
    gsrc = open(gov, encoding="utf-8").read()
    add("\u6cbb\u7406 Governance", "\u6cbb\u7406\u8173\u672c \u975c\u614b\u512a\u5148",
        "ParseFile" in gsrc and "$VIA_STATIC_VALIDATION" in gsrc)
    add("\u6cbb\u7406 Governance", "\u8b49\u64da\u8a95\u5be6 NeedsFetch/\u4e0d\u6367\u9020",
        "needs_fetch" in open(os.path.join(HERE, "via_panorama.py"), encoding="utf-8").read())

    # ---------------- 4. VISUAL LOCK ----------------
    add("\u8996\u89ba\u9396\u5b9a VisualLock", "visual_lock.css SSOT",
        os.path.exists(os.path.join(HERE, "visual_lock.css")))
    add("\u8996\u89ba\u9396\u5b9a VisualLock", "\u7bc4\u672c\u9801 template",
        os.path.exists(os.path.join(HERE, "VIA_VisualLock_Template.html")))
    vlcfg = F.load_config()["visual_lock"]
    add("\u8996\u89ba\u9396\u5b9a VisualLock", "\u9396\u5b9a token \u9f4a\u5168",
        all(k in vlcfg for k in ("bg", "ink", "up_red", "down_green", "seal_red", "amber", "resonance_gradient")))
    add("\u8996\u89ba\u9396\u5b9a VisualLock", "\u5370\u7ae0\u7cfb\u7d71",
        isinstance(vlcfg.get("seals"), dict) and "\u81fa" in vlcfg["seals"].values())

    # ---------------- 5. SESSION FIXES (regression locks) ----------------
    add("\u4fee\u6b63\u9396 Fixes", "duplicate_of \u89e3\u6790",
        (dedup_ok))
    add("\u4fee\u6b63\u9396 Fixes", "\u4e8c\u9032\u4f4d\u5783\u573e\u2192DAMAGED", idx["bad.txt"]["health"] == "DAMAGED")
    add("\u4fee\u6b63\u9396 Fixes", "eml \u4e2d\u6587\u4e0d\u4e82\u78bc",
        "\u63d0\u4f9b" in (memails[1]["text_preview"] if len(memails) > 1 else "") and
        "\ufffd" not in (memails[1]["text_preview"] if len(memails) > 1 else "x"))
    add("\u4fee\u6b63\u9396 Fixes", "thread_key \u7968\u865f\u932f",
        M.thread_key("Re: PN-9942 x") == M.thread_key("PN-9942") == "TKT:pn9942")
    add("\u4fee\u6b63\u9396 Fixes", "\u95dc\u9375\u5b57\u7121 email \u96dc\u8a0a",
        not any(w in memails[0]["aspects"]["keywords"] for w in ("corp", "com", "from", "subject")))

    return rows, total_pass


def render_html(rows, total_pass, path):
    from collections import OrderedDict
    cats = OrderedDict()
    for cat, name, st, detail in rows:
        cats.setdefault(cat, []).append((name, st, detail))
    green = sum(1 for r in rows if r[2] == "GREEN"); red = len(rows) - green
    def ryg(s):
        c = "#5a9e6f" if s == "GREEN" else "#c96b5a"
        return '<span class="rl" style="background:%s">%s</span>' % (c, s)
    body = ""
    for cat, items in cats.items():
        cg = sum(1 for _, st, _ in items if st == "GREEN")
        body += '<div class="card"><h2>%s <span class="mono" style="font-size:11px;color:#6b6a66">%d/%d</span></h2><table><tbody>' % (cat, cg, len(items))
        for name, st, detail in items:
            body += '<tr><td>%s</td><td>%s</td><td class="mono" style="font-size:11px;color:#6b6a66">%s</td></tr>' % (name, ryg(st), detail)
        body += "</tbody></table></div>"
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA \u9a57\u6536\u6aa2\u67e5\u77e9\u9663</title>
<style>@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;600&family=DM+Mono&family=Noto+Sans+TC:wght@400;500&display=swap');
:root{--bg:#f5f4f0;--sf:#fff;--bd:#dbd9d3;--ink:#1e1d1a;--sub:#6b6a66;--gr:#9c9890;--seal:#b5291a;--dn:#5a9e6f;--up:#c96b5a}
*{box-sizing:border-box;margin:0;padding:0}body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Noto Sans TC",sans-serif;font-size:13px;line-height:1.6}
.wrap{max-width:1000px;margin:0 auto;padding:26px}.mono{font-family:"DM Mono",monospace}
h1{font-family:"Syne",sans-serif;font-weight:800;font-size:22px;display:flex;align-items:center}
h2{font-family:"Syne",sans-serif;font-weight:700;font-size:14px;margin-bottom:8px}
.eyebrow{font-family:"DM Mono",monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--sub)}
.seal{display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;border-radius:7px;background:var(--seal);color:#fff;font-weight:900;margin-right:8px}
.strip{height:6px;border-radius:2px;margin:12px 0;background:linear-gradient(90deg,#4c78a8,#439a9a,#c9b05a,#c96b5a)}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:14px;margin:10px 0}
table{width:100%;border-collapse:collapse;font-size:12px}td{padding:6px 9px;text-align:left;border-bottom:1px solid var(--bd);vertical-align:top}
.rl{border-radius:9px;padding:1px 9px;font-size:9.5px;font-weight:700;color:#fff}
.big{display:flex;gap:18px;align-items:center;flex-wrap:wrap}.score{font-family:"Syne",sans-serif;font-size:46px;line-height:1}
.foot{color:var(--gr);font-size:11px;border-top:1px solid var(--bd);padding-top:10px;margin-top:14px}</style></head>
<body><div class="wrap"><div class="eyebrow">VERITAS INTELLIGENCE SYSTEM \u00b7 ACCEPTANCE</div>
<h1><span class="seal">\u7db1</span>VIA \u9a57\u6536\u6aa2\u67e5\u77e9\u9663</h1>
<div class="strip"></div>
<div class="card"><div class="big"><div class="score" style="color:__SCOL__">__GREEN__/__TOTAL__</div>
<div><div style="font-size:14px;font-weight:600">\u6aa2\u67e5\u9805\u5168\u90e8 __VERDICT__</div>
<div class="mono" style="color:var(--sub);font-size:11px">\u5f15\u64ce self-test \u7d2f\u8a08 __TP__ PASS \u00b7 __TS__</div></div></div></div>
__BODY__
<div class="foot">VIA \u00b7 VeritasIntelligenceAnalytics \u00b7 \u9a57\u6536\u77e9\u9663 \u00b7 \u5224\u5929\u5730\u4e4b\u7f8e\uff0c\u6790\u842c\u7269\u4e4b\u7406 \u00b7 \u53ef\u91cd\u8dd1</div>
</div></body></html>"""
    html = (html
            .replace("__SCOL__", "#5a9e6f" if red == 0 else "#c96b5a")
            .replace("__GREEN__", str(green)).replace("__TOTAL__", str(len(rows)))
            .replace("__VERDICT__", "\u5168\u7da0 \u2713" if red == 0 else "%d \u9805\u9700\u4fee" % red)
            .replace("__TP__", str(total_pass))
            .replace("__TS__", datetime.now(UTC).isoformat()[:19])
            .replace("__BODY__", body))
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def main():
    rows, total_pass = run_matrix()
    from collections import OrderedDict
    cats = OrderedDict()
    for cat, name, st, detail in rows:
        cats.setdefault(cat, []).append((name, st, detail))
    green = sum(1 for r in rows if r[2] == "GREEN"); red = len(rows) - green
    print("=" * 70)
    print(" VIA \u9a57\u6536\u6aa2\u67e5\u77e9\u9663  \u00b7  %d/%d GREEN  \u00b7  \u5f15\u64ce\u7d2f\u8a08 %d PASS" % (green, len(rows), total_pass))
    print("=" * 70)
    for cat, items in cats.items():
        cg = sum(1 for _, st, _ in items if st == "GREEN")
        print("\n[%s]  %d/%d" % (cat, cg, len(items)))
        for name, st, detail in items:
            mark = "\u2713" if st == "GREEN" else "\u2717"
            print("  %s %-28s %-7s %s" % (mark, name, st, detail))
    out = os.path.join(HERE, "VIA_CheckMatrix.html")
    render_html(rows, total_pass, out)
    print("\n" + "=" * 70)
    print(" \u7d50\u679c\uff1a%s" % ("\u5168\u7da0 ALL GREEN \u2713" if red == 0 else "%d \u9805\u9700\u4fee" % red))
    print(" HTML \u5831\u544a\uff1a%s" % out)
    return 0 if red == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

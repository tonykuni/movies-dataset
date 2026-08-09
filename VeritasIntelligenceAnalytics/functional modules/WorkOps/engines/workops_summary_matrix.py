# -*- coding: utf-8 -*-
r"""Veritas WorkOps 總結矩陣引擎 v0100(ENG-037)— DETAILED SUMMARY MATRIX:RESULT + DB

操作員令(2026/08/10):詳盡且有條理的總結矩陣,展示全系統成果與資料庫。
三區矩陣(全唯讀;缺席誠實列示,絕不編造):
  A 成果 RESULTS   板/週報/簡報/佇列頁/引擎與分析報告/結案報告/稽核包 — 在位·大小·更新時間
  B 側車 SIDE-CARS 歸戶/命名/互鏈/回覆/決策/路由/準確度/自測 — 筆數與關鍵指標
  C 資料庫 DB      WorkOps sqlite(逐表列數)+ VDF/VAP db 目錄(檔型·大小)
產物:out/VIA_Summary_Matrix.html(VisualLock 風格)+ 主控台矩陣。
動詞:build(預設)。via-workops matrix。
"""
import csv, io, json, sqlite3, sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
WORKOPS = HERE.parent
OUT = WORKOPS / "out"
VIAROOT = WORKOPS.parent.parent
HTML_P = OUT / "VIA_Summary_Matrix.html"


def fsize(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%.1f %s" % (n, u) if u != "B" else "%d B" % n
        n /= 1024.0


def stat_row(name, p, note=""):
    p = Path(p)
    if p.exists():
        st = p.stat()
        return {"name": name, "gate": "在位", "detail": note,
                "size": fsize(st.st_size), "mtime": datetime.fromtimestamp(st.st_mtime).strftime("%m/%d %H:%M"),
                "path": str(p)}
    return {"name": name, "gate": "缺席", "detail": note, "size": "—", "mtime": "—", "path": str(p)}


def jload(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def csv_n(p):
    try:
        with io.open(p, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            return sum(1 for _ in csv.DictReader(f))
    except Exception:
        return None


def jsonl_n(p):
    try:
        return sum(1 for ln in Path(p).read_text(encoding="utf-8").splitlines() if ln.strip())
    except Exception:
        return None


def newest(root, pattern):
    if not Path(root).exists():
        return None
    c = sorted(Path(root).glob(pattern))
    return c[-1] if c else None


def sqlite_info(p):
    """唯讀開 sqlite:逐表列數(表多取前 15)。"""
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % Path(p).as_posix(), uri=True)
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        rows = []
        for t in tables[:15]:
            try:
                n = conn.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
            except Exception:
                n = None
            rows.append((t, n))
        conn.close()
        return tables, rows
    except Exception:
        return None, []


def gather():
    A = []
    A.append(stat_row("指揮板", VIAROOT / "VIA_Reports/workops_run/VIA_WorkOps_CommandBoard.html", "十面板 00-09"))
    A.append(stat_row("週報", VIAROOT / "VIA_Reports/workops_run/VIA_WorkOps_WeeklyReport.html", "via-workops report"))
    A.append(stat_row("自動簡報", OUT / "VIA_WorkOps_Slides.html", "六張投影片(ENG-033)"))
    A.append(stat_row("歸戶確認佇列", OUT / "WopConfirmQueue.html", "滑鼠一鍵(ENG-028)"))
    A.append(stat_row("超級引擎報告", OUT / "deep/engine_out/engine_report.html", "板 01 面可內嵌"))
    A.append(stat_row("進階分析報告", OUT / "deep/engine_out/analytics_report.html", "NLP/DM/PM"))
    A.append(stat_row("結案報告", VIAROOT / "VIA_Reports/closure/VIA_Trinity_Closure_Report.html", "VDF·VRN·VAP(ENG-034)"))
    nb = newest(OUT / "audit_bundle", "*.zip")
    A.append(stat_row("稽核包(最新)", nb if nb else OUT / "audit_bundle/(尚無)", "IT/主管交件(ENG-036)"))
    ns = newest(OUT / "deep/scanrange", "RUN_*/VIA_Outlook_TimeRange_ReadOnly_Report.html")
    A.append(stat_row("唯讀掃描報告(最新)", ns if ns else OUT / "deep/scanrange/(尚無)", "時段全資料夾"))

    B = []
    reg = jload(OUT / "wop_registry.json") or {}
    led = jload(OUT / "workops_id_ledger.json") or {}
    B.append({"name": "WOP 歸戶 registry", "gate": "在位" if reg else "缺席",
              "detail": "專案 %d 案 · 序號 WOP %s/THR %s" % (len(reg.get("projects", {})), led.get("seq_wop", "—"), led.get("seq_thr", "—"))})
    nm = jload(OUT / "workops_naming.json") or {}
    ents = nm.get("entries", {}) or {}
    okn = sum(1 for v in ents.values() if isinstance(v, dict) and v.get("approved"))
    B.append({"name": "命名帳本", "gate": "在位" if nm else "缺席",
              "detail": "%d 筆 · 已核 %d · 待核 %d" % (len(ents), okn, len(ents) - okn)})
    tc = jload(OUT / "thr_case_map.json") or {}
    B.append({"name": "THR↔CASE 互鏈", "gate": "在位" if tc else "缺席",
              "detail": "%d 串連結" % len(tc.get("map", tc) if isinstance(tc, dict) else [])})
    rs = jload(OUT / "reply_status.json") or {}
    fl = rs.get("flags", {})
    B.append({"name": "回覆解析狀態", "gate": "在位" if rs else "缺席",
              "detail": "判讀 %d 串 · ⚡%d ⏸%d · 未解析 %s" % (len(rs.get("status", {})),
                        sum(1 for f in fl.values() if f.get("risk")), sum(1 for f in fl.values() if f.get("ooo")),
                        (rs.get("unparsed") or {}).get("n", "—"))})
    ne = jsonl_n(OUT / "reply_events.jsonl")
    B.append({"name": "回覆事實流", "gate": "在位" if ne is not None else "缺席", "detail": "事件 %s 筆(append-only)" % (ne if ne is not None else "—")})
    nd = csv_n(OUT / "decision_log.csv")
    B.append({"name": "決策 KPI 匯出", "gate": "在位" if nd is not None else "缺席", "detail": "DEC %s 筆" % (nd if nd is not None else "—")})
    st = jload(OUT / "wop_route_stats.json") or {}
    B.append({"name": "路由分佈", "gate": "在位" if st else "缺席",
              "detail": "本輪 %s 串 · 雜訊 %s · 層 %d" % (st.get("total", "—"), st.get("noise", "—"), len(st.get("hits", {})))})
    nh = jsonl_n(OUT / "wop_route_history.jsonl")
    B.append({"name": "L8 趨勢歷史", "gate": "在位" if nh else "缺席", "detail": "%s 輪(append-only)" % (nh if nh else "—")})
    ac = jload(OUT / "accuracy_report.json")
    B.append({"name": "Gold Set 實測", "gate": "在位" if ac else "未實測",
              "detail": ("歸戶 %.1f%% · 樣本 %d" % (100 * ac["assignment_accuracy"], ac.get("gold_rows", 0))) if ac and ac.get("assignment_accuracy") is not None else "板 05 面三步引導"})
    ngt = csv_n(OUT / "gold_set_template.csv")
    B.append({"name": "Gold Set 樣板", "gate": "在位" if ngt is not None else "缺席", "detail": "%s 筆待核對" % (ngt if ngt is not None else "—")})
    sfr = jload(OUT / "selftest_report.json")
    B.append({"name": "全鏈自測", "gate": (sfr or {}).get("final_gate", "缺席"),
              "detail": "%d 段" % len((sfr or {}).get("stages", [])) if sfr else "via-workops selftest"})
    ask = jload(OUT / "wop_ask.json") or {}
    B.append({"name": "確認中心餘量", "gate": "在位" if ask else "缺席",
              "detail": "ASK %s · 留置 %s" % (ask.get("n_ask", "—"), ask.get("n_quarantine", "—"))})

    C = []
    for name, p in [("超級引擎 DB", OUT / "deep/engine_out/super_engine.db"),
                    ("決策帳本 DB", OUT / "decision_log.db"),
                    ("行動庫 DB", OUT / "email_actions.db")]:
        if Path(p).exists():
            tables, rows = sqlite_info(p)
            tot = sum(n for _, n in rows if n is not None)
            det = "%d 表 · %s 列 · " % (len(tables or []), tot) + " / ".join("%s %s" % (t, n) for t, n in rows[:6])
            C.append({"name": name, "gate": "在位", "detail": det, "size": fsize(Path(p).stat().st_size), "path": str(p)})
        else:
            C.append({"name": name, "gate": "缺席", "detail": "—", "size": "—", "path": str(p)})
    for name, d in [("VDF 資料庫目錄", VIAROOT / "functional modules/VDF/db"),
                    ("VAP 資料庫目錄", VIAROOT / "functional modules/VAP/db")]:
        d = Path(d)
        if d.exists():
            files = [f for f in d.rglob("*") if f.is_file()]
            by_ext = {}
            tot = 0
            for f in files:
                by_ext[f.suffix or "(無副檔)"] = by_ext.get(f.suffix or "(無副檔)", 0) + 1
                tot += f.stat().st_size
            det = ("%d 檔 · " % len(files)) + (" / ".join("%s×%d" % (k, v) for k, v in sorted(by_ext.items())) if files else "空目錄")
            C.append({"name": name, "gate": "在位" if files else "空", "detail": det, "size": fsize(tot), "path": str(d)})
        else:
            C.append({"name": name, "gate": "缺席", "detail": "—", "size": "—", "path": str(d)})
    return A, B, C


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    A, B, C = gather()
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    print("=========== VIA 總結矩陣(成果 × 側車 × DB;全唯讀)===========")
    for title, rows, cols in [("A 成果", A, ("name", "gate", "size", "mtime", "detail")),
                              ("B 側車", B, ("name", "gate", "detail")),
                              ("C 資料庫", C, ("name", "gate", "size", "detail"))]:
        print("---- %s ----" % title)
        for r in rows:
            print("  " + " | ".join(str(r.get(k, "")) for k in cols))
    ok = sum(1 for r in A + B + C if r["gate"] in ("在位", "PASS"))
    print("[矩陣] %d 項盤點 · 在位/PASS %d · 其餘誠實列示" % (len(A) + len(B) + len(C), ok))

    def table(rows, cols, heads):
        h = "<table><tr>" + "".join("<th>%s</th>" % esc(x) for x in heads) + "</tr>"
        for r in rows:
            g = r.get("gate", "")
            cls = "ok" if g in ("在位", "PASS") else ("warn" if g in ("未實測", "空") else "bad")
            h += "<tr class='%s'>" % cls + "".join("<td>%s</td>" % esc(r.get(k, "—")) for k in cols) + "</tr>"
        return h + "</table>"

    html = ("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA 總結矩陣</title><style>"
            "body{font:14.5px/1.6 'Noto Sans TC','Microsoft JhengHei',sans-serif;background:#f5f4f0;color:#23221e;padding:30px}"
            ".k{font-family:'DM Mono',Consolas,monospace;font-size:11px;letter-spacing:.16em;color:#6f6c63}"
            "h1{font-size:23px;margin:4px 0 2px}h2{font-size:17px;margin:22px 0 8px}"
            "table{border-collapse:collapse;background:#fff;border:1px solid #dedbd2;border-radius:10px;overflow:hidden;width:100%}"
            "th,td{padding:6px 12px;border-bottom:1px solid #e4e1d8;font-size:13px;text-align:left;vertical-align:top}"
            "th{background:#eceae3;font-size:12px}tr.bad td:nth-child(2){color:#b04532;font-weight:700}"
            "tr.ok td:nth-child(2){color:#2f6f5e;font-weight:700}tr.warn td:nth-child(2){color:#8a5a2b;font-weight:700}"
            ".note{color:#6f6c63;font-size:12.5px;margin-top:14px}</style></head><body>"
            "<div class='k'>VERITAS INTELLIGENCE ANALYTICS</div><h1>總結矩陣 — 成果 × 側車 × 資料庫</h1>"
            "<p class='note'>產生 " + esc(now) + " · 全唯讀盤點;缺席=誠實列示非故障;路徑為同機正本位置</p>"
            + "<h2>A 成果 RESULTS</h2>" + table(A, ("name", "gate", "size", "mtime", "detail", "path"), ("項目", "狀態", "大小", "更新", "說明", "路徑"))
            + "<h2>B 側車 SIDE-CARS(筆數與關鍵指標)</h2>" + table(B, ("name", "gate", "detail"), ("項目", "狀態", "指標"))
            + "<h2>C 資料庫 DB(逐表列數/檔型統計)</h2>" + table(C, ("name", "gate", "size", "detail", "path"), ("庫", "狀態", "大小", "內容", "路徑"))
            + "<p class='note'>紅=缺席(先跑 via-workops all 或對應動詞)· 棕=待人工步驟 · 綠=在位。矩陣本身不改任何正本。</p></body></html>")
    OUT.mkdir(parents=True, exist_ok=True)
    HTML_P.write_text(html, encoding="utf-8")
    print("[產物] %s" % HTML_P)
    return 0


if __name__ == "__main__":
    sys.exit(build())

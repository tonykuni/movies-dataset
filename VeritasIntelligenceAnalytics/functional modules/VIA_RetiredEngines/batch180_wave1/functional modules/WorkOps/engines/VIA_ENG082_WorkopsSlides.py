# -*- coding: utf-8 -*-
r"""Veritas WorkOps 自動簡報引擎 v0100(ENG-033)— 板資料 → 週報 slides(候令開工:UI 重規劃 §4.4)

操作員產品化令:「未來自動簡報生成 · 給主管的控管表更新」。本引擎把既有 side-car
(歸戶/追蹤/決策/準確度/確認餘量)合成一份 HTML 翻頁簡報:滑鼠點擊/方向鍵翻頁,
Ctrl+P 列印=一頁一張投影片(@page 分頁)。零新資料源、零觸碰正本、缺料誠實標示。
產物:out/VIA_WorkOps_Slides.html。動詞:build(預設)。via-workops slides。
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import csv, io, json, sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
SLIDES_P = OUT / "VIA_WorkOps_Slides.html"


def jload(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def csv_rows(p):
    try:
        with io.open(p, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def bar(pc, color="#2f6f5e"):
    pc = max(0, min(100, int(pc)))
    return ("<div style='background:#e4e1d8;border-radius:5px;overflow:hidden;max-width:340px'>"
            "<div style='width:%d%%;background:%s;color:#fff;font-size:11px;padding:2px 6px;white-space:nowrap'>%d%%</div></div>" % (pc, color, pc))


def missing(what):
    return "<p class='miss'>(%s 資料尚缺 — 先跑 via-workops all)</p>" % esc(what)


def gather():
    d = {}
    d["reg"] = jload(OUT / "wop_registry.json", {})
    d["led"] = jload(OUT / "workops_id_ledger.json", {})
    d["rs"] = jload(OUT / "reply_status.json", {})
    d["acc"] = jload(OUT / "accuracy_report.json", None)
    d["stats"] = jload(OUT / "wop_route_stats.json", {})
    d["ask"] = jload(OUT / "wop_ask.json", {})
    d["naming"] = jload(OUT / "workops_naming.json", {})
    d["wt"] = jload(HERE / "watchtower_params.json", {})
    d["dec"] = csv_rows(OUT / "decision_log.csv")
    d["pend"] = csv_rows(OUT / "pending.csv")
    hist = []
    hp = OUT / "wop_route_history.jsonl"
    if hp.exists():
        for ln in hp.read_text(encoding="utf-8").splitlines():
            try:
                hist.append(json.loads(ln))
            except Exception:
                pass
    d["hist"] = hist[-10:]
    return d


def build():
    d = gather()
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    projects = d["reg"].get("projects", {})
    n_wop = len(projects)
    n_thr = int(d["led"].get("seq_thr") or 0)
    flags = d["rs"].get("flags", {})
    n_risk = sum(1 for f in flags.values() if f.get("risk"))
    n_ooo = sum(1 for f in flags.values() if f.get("ooo"))
    un = (d["rs"].get("unparsed") or {}).get("n", 0)
    ents = d["naming"].get("entries", {}) or {}
    n_nm = len(ents)
    n_nm_ok = sum(1 for v in ents.values() if isinstance(v, dict) and v.get("approved"))
    dec = d["dec"]
    n_dec = len(dec)
    n_dec_done = sum(1 for r in dec if (r.get("狀態") or r.get("status") or "") == "DONE")
    ry = d["wt"].get("daily_rhythm", {}) or {}
    S = []

    # ---- S1 封面 ----
    S.append("<div class='kick'>VERITAS WORKOPS</div><h1>工作追蹤週報</h1>"
             "<p class='sub'>產生 %s · 本簡報由系統自動合成(唯讀 side-car;絕不代寄)</p>"
             "<p class='sub'>翻頁:點擊或 ←→ 鍵 · 列印:Ctrl+P(一頁一張)</p>" % esc(now))

    # ---- S2 總覽 KPI ----
    h = "<h2>總覽</h2><div class='grid'>"
    for v, k in [(n_wop, "WOP 專案"), (n_thr, "THR 追蹤串"), (n_risk, "⚡風險越級"),
                 (n_ooo, "⏸OOO 凍結"), (max(0, n_nm - n_nm_ok), "待核命名"), (un, "未解析回信")]:
        h += "<div class='cell'><div class='v'>%s</div><div class='k'>%s</div></div>" % (esc(v), esc(k))
    h += "</div>"
    if ry:
        h += ("<p class='note'>日節奏:%s 產草稿 → 次日 %s 回覆期限 → 下午僅急件(%s 起)</p>"
              % (esc(ry.get("generate_drafts_time", "16:00")), esc(ry.get("reply_deadline_next_day", "12:00")),
                 esc(ry.get("afternoon_starts", "13:00"))))
    S.append(h)

    # ---- S3 專案重點(THR 數 top10)----
    h = "<h2>專案重點(依串量)</h2>"
    if projects:
        rows = sorted(projects.items(), key=lambda kv: -len(kv[1].get("thr", [])))[:10]
        h += "<table><tr><th>WOP</th><th>名稱</th><th>串數</th><th>狀態</th></tr>"
        for wid, pr in rows:
            h += ("<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>"
                  % (esc(wid), esc(pr.get("label", "")), len(pr.get("thr", [])), esc(pr.get("status", ""))))
        h += "</table>"
    else:
        h += missing("WOP 歸戶")
    S.append(h)

    # ---- S4 決策 KPI ----
    h = "<h2>會議決策落地</h2>"
    if dec:
        rate = int(100 * n_dec_done / n_dec) if n_dec else 0
        h += "<p>決議 %d 件 · 完成 %d 件</p>%s" % (n_dec, n_dec_done, bar(rate))
        h += "<table><tr><th>DEC</th><th>決議</th><th>負責人</th><th>截止</th><th>狀態</th></tr>"
        for r in dec[:8]:
            h += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                  % tuple(esc(r.get(k, "")) for k in ("編號", "決議", "負責人", "截止", "狀態")))
        h += "</table>"
    else:
        h += missing("決策帳本")
    S.append(h)

    # ---- S5 準確度 ----
    h = "<h2>系統準確度</h2>"
    acc = d["acc"]
    if acc and acc.get("assignment_accuracy") is not None:
        h += "<p>歸戶準確率(對人工 Gold Set 實測,樣本 %d)</p>%s" % (
            acc.get("gold_rows", 0), bar(round(100 * acc["assignment_accuracy"])))
        if acc.get("status_accuracy") is not None:
            h += "<p>狀態準確率</p>%s" % bar(round(100 * acc["status_accuracy"]))
    else:
        h += "<p class='miss'>(Gold Set 尚未實測 — 板 05 面三步引導;絕不以信心分數冒充)</p>"
    hits = (d["stats"] or {}).get("hits", {})
    if hits:
        tot = d["stats"].get("total", 0) or 1
        l8 = sum(v for k, v in hits.items() if k.startswith("L8"))
        h += "<p>本輪路由:共 %d 串 · L8 佔比(越低=越自動)</p>%s" % (tot, bar(round(100 * l8 / tot), "#8a5a2b"))
    if d["hist"]:
        pts = " → ".join("%d%%" % round(100 * (r.get("l8_share") or 0)) for r in d["hist"])
        h += "<p class='note'>L8 趨勢(近 %d 輪):%s</p>" % (len(d["hist"]), esc(pts))
    S.append(h)

    # ---- S6 待辦與下一步 ----
    h = "<h2>待辦與下一步</h2><ul>"
    n_ask = d["ask"].get("n_ask", 0)
    h += "<li>歸戶待確認 %s 件(滑鼠佇列頁一鍵清空)</li>" % esc(n_ask)
    h += "<li>命名待核 %d 筆(naming_review.csv 改第三欄)</li>" % max(0, n_nm - n_nm_ok)
    h += "<li>未解析回信 %s 件(對方回覆帶訊號即自動判讀)</li>" % esc(un)
    open_dec = [r for r in dec if (r.get("狀態") or "") not in ("DONE",)][:5]
    for r in open_dec:
        h += "<li>未結決議 %s:%s(%s)</li>" % (esc(r.get("編號", "")), esc(r.get("決議", "")), esc(r.get("負責人", "")))
    h += "</ul><p class='note'>本頁即主管檢視點:紅=需人,綠=系統自動中。原控管表永不回寫 — 更新一律另出新檔。</p>"
    S.append(h)

    slides = "".join("<section class='slide'>%s</section>" % s for s in S)
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>Veritas WorkOps 週報簡報</title><style>
:root{--bg:#f5f4f0;--ink:#23221e;--mut:#6f6c63;--line:#dedbd2;--teal:#2f6f5e}
*{box-sizing:border-box;margin:0}body{background:var(--bg);color:var(--ink);font:16px/1.65 "Noto Sans TC","Microsoft JhengHei",sans-serif}
.slide{display:none;min-height:100vh;padding:8vh 10vw;flex-direction:column;justify-content:center}
.slide.on{display:flex}
.kick{font-family:"DM Mono",Consolas,monospace;font-size:12px;letter-spacing:.18em;color:var(--mut);margin-bottom:14px}
h1{font-size:44px;margin-bottom:12px}h2{font-size:30px;margin-bottom:18px}
.sub{color:var(--mut);margin-top:6px}.note{color:var(--mut);font-size:13.5px;margin-top:14px}
.miss{color:#8a5a2b;font-size:14px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;max-width:760px}
.cell{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.cell .v{font-size:34px;font-weight:800}.cell .k{color:var(--mut);font-size:13px;margin-top:2px}
table{border-collapse:collapse;margin-top:10px;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{padding:8px 14px;border-bottom:1px solid var(--line);font-size:14px;text-align:left}th{background:#eceae3;font-size:12.5px}
ul{margin:8px 0 0 22px}li{margin:6px 0}
.pg{position:fixed;right:18px;bottom:14px;color:var(--mut);font-family:"DM Mono",Consolas,monospace;font-size:12px}
@media print{.slide{display:flex;page-break-after:always;min-height:auto;padding:24px 32px}.pg{display:none}body{background:#fff}}
</style></head><body>
%SLIDES%
<div class="pg" id="pg"></div>
<script>
var i=0,ss=document.querySelectorAll(".slide");
function show(n){i=Math.max(0,Math.min(ss.length-1,n));
 for(var j=0;j<ss.length;j++){ss[j].classList.remove("on");}
 ss[i].classList.add("on");
 var p=document.getElementById("pg");if(p)p.textContent=(i+1)+" / "+ss.length;}
document.addEventListener("keydown",function(e){if(e.key==="ArrowRight"||e.key===" ")show(i+1);if(e.key==="ArrowLeft")show(i-1);});
document.addEventListener("click",function(e){if(e.clientX>window.innerWidth/2)show(i+1);else show(i-1);});
show(0);
</script></body></html>"""
    html = html.replace("%SLIDES%", slides)
    OUT.mkdir(parents=True, exist_ok=True)
    SLIDES_P.write_text(html, encoding="utf-8")
    print("[簡報] %d 張投影片 → %s" % (len(S), SLIDES_P))
    print("[提示] 開啟後 ←→ 或點擊翻頁;Ctrl+P 列印=一頁一張;資料缺席頁已誠實標示")
    return 0


if __name__ == "__main__":
    sys.exit(build())

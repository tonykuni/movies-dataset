#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL090_SystemHub — 系統同步樞紐 UI(批168;via-hub)
====================================================================
操作員令:「Handle all problem and create html ui synchronized, and
connected with the system」——單一 HTML 樞紐,與系統連動同步:
  同步機制=via_boot_update.sh ⑨步每日開機自動重生(本引擎 run)+
    任何批次收官重生;頁面時戳+來源存證名可稽
  連動面(全存證 join,零重測零發明):
    ① 測試面:最新 GRID 存證(紅黃綠+SKIP 明細)+最新 PYRAMID 判定
    ② 資料面:vdf_tw_market/vdf_global_market DuckDB 各表列數實測
    ③ 治理面:VSM 六燈快照+問題台帳(VIA_Problem_Ledger 六態分類)
    ④ 資產面:台帳筆數/名冊 counters/ui_support 頁清單(mtime)
  視覺=MDL089 模板正主 token 冊(改冊即換裝;手機直式優先)
v0100→v0101(批190 操作員令:「ensure file system…VAP/VDF/VRN
function work well and sync connected to the user interface with left
panel」):+左側面板(寬/色/斷點全取 token 冊 dashboard 節=批167
Layout element 定案 260px/768;零寫死)——四系統節點燈(VIA/VDF/
VAP/VRN 實測態)+supportive toolkit 燈+資料三層基座列數(正典價格
→因子庫→共識庫)+四頁 UI 互鏈;Mobile ≤768 面板轉上方橫列。
用法:python3 CGC_MDL090_SystemHub_v0101.py run | --selftest
"""
from __future__ import annotations
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

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_SystemHub_v0100.html"
GRID_RUNS = VIA / "VIA_Reports" / "selftest_runs"
PYR_RUNS = VIA / "VIA_Reports" / "pyramid_runs"
PROB = HERE / "VIA_Problem_Ledger_v0100.json"
AUTOCODE = HERE / "VIA_AutoCode_Registry_v0100.json"
NAMING = HERE / "VIA_Naming_Registry_v0100.json"
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DB_GL = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_global_market.duckdb"
UI_DIR = VIA / "supportive modules" / "ui_support"


def _mdl089():
    p = sorted(HERE.glob("CGC_MDL089_UIBaseTemplate_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("cgc_mdl089_hub", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["cgc_mdl089_hub"] = m
    spec.loader.exec_module(m)
    return m


def harvest() -> dict:
    """全連動收割(唯讀;存證 join 零重測)"""
    out = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M")}
    # ① 測試面
    g = sorted(GRID_RUNS.glob("GRID_*.json"))
    if g:
        items = json.loads(g[-1].read_text(encoding="utf-8"))
        items = items if isinstance(items, list) else (
            items.get("results") or items.get("stations") or [])
        cnt = {"OK": 0, "FAIL": 0, "SKIP": 0}
        for i in items:
            cnt[i.get("state", "SKIP")] = cnt.get(i.get("state", "SKIP"), 0) + 1
        out["grid"] = {"name": g[-1].name, "n": len(items), **cnt,
                       "skips": [i["name"] for i in items if i.get("state") == "SKIP"],
                       "fails": [i["name"] for i in items if i.get("state") == "FAIL"]}
    else:
        out["grid"] = None
    p = sorted(PYR_RUNS.glob("PYRAMID_*.json"))
    if p:
        try:
            d = json.loads(p[-1].read_text(encoding="utf-8"))
            out["pyramid"] = {"name": p[-1].name,
                              "verdict": d.get("verdict") or d.get("judgement") or "見存證"}
        except Exception:
            out["pyramid"] = {"name": p[-1].name, "verdict": "見存證"}
    else:
        out["pyramid"] = None
    # ② 資料面
    out["db"] = {}
    try:
        import duckdb
        for label, path in (("台股庫", DB_TW), ("全球庫", DB_GL)):
            if not path.exists():
                out["db"][label] = {"note": "缺(誠實)"}
                continue
            con = duckdb.connect(str(path), read_only=True)
            tbls = {}
            for (t,) in con.execute("SHOW TABLES").fetchall():
                tbls[t] = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
            con.close()
            out["db"][label] = {"tables": tbls, "total": sum(tbls.values())}
    except Exception as e:
        out["db"]["error"] = str(e)[:80]
    # ③ 治理面
    prob = json.loads(PROB.read_text(encoding="utf-8")) if PROB.exists() else None
    out["problems"] = prob
    # ④ 資產面
    try:
        ac = json.loads(AUTOCODE.read_text(encoding="utf-8"))
        out["ledger_n"] = len(ac.get("ledger", []))
    except Exception:
        out["ledger_n"] = None
    try:
        nm = json.loads(NAMING.read_text(encoding="utf-8"))
        out["counters"] = nm.get("counters", {})
    except Exception:
        out["counters"] = {}
    out["uis"] = sorted(
        ({"name": f.name,
          "mtime": datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d %H:%M")}
         for f in UI_DIR.glob("VIA_UI_*.html")),
        key=lambda x: x["mtime"], reverse=True)[:12]
    # ⑤ 左面板連動:四系統節點+資料三層基座(唯讀實測)
    tw = out["db"].get("台股庫", {}).get("tables", {})
    out["base3"] = {"正典價格 prices": tw.get("tw_prices_adj", 0),
                    "因子庫 features": tw.get("features_daily", 0),
                    "共識庫 consensus": tw.get("consensus_daily", 0)}
    g = out.get("grid")
    out["sys4"] = {
        "VIA": {"ok": bool(g) and g["FAIL"] == 0,
                "note": f"grid {g['OK']}綠/{g['FAIL']}紅" if g else "無存證"},
        "VDF": {"ok": tw.get("tw_prices_adj", 0) > 1_000_000,
                "note": f"正典 {tw.get('tw_prices_adj', 0):,} 列"},
        "VAP": {"ok": (UI_DIR / "VIA_UI_Dashboard_v0100.html").exists(),
                "note": f"UI {len(out['uis'])} 頁"},
        "VRN": {"ok": tw.get("consensus_daily", 0) > 0,
                "note": f"共識 {tw.get('consensus_daily', 0):,} 筆"},
    }
    out["toolkit_ok"] = (VIA / "supportive modules" / "VIA_SuperAccel_Module.py").exists() \
        and (VIA / "supportive modules" / "network").exists() \
        and (out["counters"].get("SUP_MDL", 0) >= 742)
    return out


_STATUS_ZH = {"FIXED": "已修復", "ADJUDICATED": "裁定結案", "BY_DESIGN": "設計誠實閘",
              "PENDING_OPERATOR": "候操作員", "NO_WORKAROUND": "誠實無解",
              "TRACKED": "持續追蹤"}


def render(h: dict, T, tk: dict) -> str:
    st = tk["status"]
    g = h["grid"]
    lamp = st["FAIL"] if (g and g["FAIL"]) else (st["SKIP"] if (g and g["SKIP"]) else st["OK"])
    # 測試面
    grid_html = "無 GRID 存證(誠實)"
    if g:
        skips = "".join(f"<li>{s}</li>" for s in g["skips"])
        grid_html = (f'<div class="kpi"><span style="color:{st["OK"]}">●綠 {g["OK"]}</span>'
                     f'<span style="color:{st["SKIP"]}">●黃 {g["SKIP"]}</span>'
                     f'<span style="color:{st["FAIL"]}">●紅 {g["FAIL"]}</span>'
                     f'<span class="mut">{g["n"]} 站 · {g["name"]}</span></div>'
                     f'<div class="mut">黃(SKIP 誠實):</div><ul class="mut">{skips}</ul>')
    pyr = h["pyramid"]
    pyr_html = (f'{pyr["name"]} · 判定 <b>{pyr["verdict"]}</b>' if pyr else "無金字塔存證")
    # 資料面
    db_rows = ""
    for label, v in h["db"].items():
        if not isinstance(v, dict) or "tables" not in v:
            db_rows += f"<tr><td>{label}</td><td colspan=2 class='mut'>{v}</td></tr>"
            continue
        top = sorted(v["tables"].items(), key=lambda x: -x[1])[:6]
        det = " · ".join(f"{t} {n:,}" for t, n in top)
        db_rows += (f"<tr><td>{label}</td><td class='num'>{v['total']:,}</td>"
                    f"<td class='mut'>{det}</td></tr>")
    # 治理面
    prob = h["problems"]
    vsm_html, prob_rows = "", ""
    if prob:
        vs = prob.get("vsm_snapshot", {})
        vsm_html = " ".join(
            f'<span><span class="dot" style="background:'
            f'{st["OK"] if vs.get(k) == "GREEN" else st["FAIL"]}"></span>{k}</span>'
            for k in ("S1", "S2", "S3", "S3star", "S4", "S5"))
        for pr in prob["problems"]:
            c = {"FIXED": st["OK"], "ADJUDICATED": st["OK"], "BY_DESIGN": st["OK"],
                 "TRACKED": st["SKIP"], "PENDING_OPERATOR": st["SKIP"],
                 "NO_WORKAROUND": st["SKIP"]}.get(pr["status"], st["UNTESTED"])
            prob_rows += (f'<tr><td><span class="dot" style="background:{c}"></span>'
                          f'{_STATUS_ZH.get(pr["status"], pr["status"])}</td>'
                          f'<td>{pr["id"]} {pr["title"]}</td>'
                          f'<td class="mut">{pr["detail"]}</td></tr>')
    # 資產面
    cnt = h["counters"]
    cnt_html = " · ".join(f"{k} {v}" for k, v in sorted(cnt.items())) or "冊缺(誠實)"
    ui_rows = "".join(f"<tr><td>{u['name']}</td><td class='num'>{u['mtime']}</td></tr>"
                      for u in h["uis"])
    # 左側面板(批190;全值取 token 冊 dashboard 節=批167 定案,零寫死)
    db_tk = tk.get("dashboard", {})
    pw = db_tk.get("panel_w_px", 260)
    bp = db_tk.get("breakpoint_px", 768)
    pbg = db_tk.get("color_panel_bg", "#f7f7f7")
    pbd = db_tk.get("color_border", "#e0e0e0")
    hh = db_tk.get("header_h_px", 38)
    sys_rows = "".join(
        f'<a class="lpitem" href="#sec{i}"><span class="dot" style="background:'
        f'{st["OK"] if v["ok"] else st["SKIP"]}"></span><b>{k}</b>'
        f'<span class="mut"> {v["note"]}</span></a>'
        for i, (k, v) in enumerate(h["sys4"].items(), 1))
    base_rows = "".join(f'<div class="lpitem"><span class="mut">{k}</span>'
                        f'<span class="num">{v:,}</span></div>'
                        for k, v in h["base3"].items())
    tkc = st["OK"] if h["toolkit_ok"] else st["SKIP"]
    pages = [("VIA_UI_SystemTestPages_v0100.html", "五系統分頁"),
             ("VIA_UI_Dashboard_v0100.html", "儀表板"),
             ("VIA_UI_DailyBrief_v0100.html", "每日觀察"),
             ("VIA_UI_Charter_v0100.html", "系統憲章")]
    page_rows = "".join(f'<a class="lpitem" href="{f}">▸ {z}</a>'
                        for f, z in pages)
    left_panel = f"""<aside id="leftpanel">
<div class="lphead"><span class="dot big" style="background:{lamp}"></span>VIA 樞紐</div>
<div class="lpsec">四系統(同步實測)</div>{sys_rows}
<div class="lpsec">資料三層基座</div>{base_rows}
<div class="lpsec">supportive toolkit</div>
<div class="lpitem"><span class="dot" style="background:{tkc}"></span>加速/網路/冊
<span class="mut"> SUP_MDL {h['counters'].get('SUP_MDL', '?')}</span></div>
<div class="lpsec">頁面(同步重生)</div>{page_rows}
</aside>"""
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 系統樞紐 v0101</title><style>{T.base_css(tk)}
.hubgrid{{display:grid;grid-template-columns:1fr;gap:10px}}
ul{{margin:.2em 0 .4em 1.2em;padding:0}}
.hublayout{{display:flex;gap:12px;align-items:flex-start}}
#leftpanel{{width:{pw}px;min-width:{pw}px;background:{pbg};
border:1px solid {pbd};border-radius:6px;padding:8px;
position:sticky;top:8px}}
.lphead{{height:{hh}px;display:flex;align-items:center;gap:6px;
font-weight:bold;border-bottom:1px solid {pbd}}}
.lpsec{{margin:.7em 0 .2em;font-weight:bold;color:#666;font-size:.9em}}
.lpitem{{display:flex;align-items:center;gap:6px;padding:3px 2px;
text-decoration:none;color:inherit;justify-content:flex-start}}
.lpitem .num{{margin-left:auto}}
.hubmain{{flex:1;min-width:0}}
@media (max-width:{bp}px){{.hublayout{{flex-direction:column}}
#leftpanel{{width:100%;min-width:0;position:static}}}}
</style></head><body><div class="wrap">
<div class="hublayout">{left_panel}<div class="hubmain">
<h1><span class="dot big" style="background:{lamp}"></span>VIA 系統樞紐(同步連動)</h1>
<div class="mut">{h['ts']} · 開機⑨步自動重生=同步 · 全面板=存證/冊/庫唯讀 join
零重測零發明 · 視覺單源 token 冊(左面板=批167 定案 {pw}px/斷點 {bp})</div>
<div class="hubgrid">
<section class="page on" id="sec1"><h2>① 測試面(grid×金字塔)</h2>
{grid_html}<div class="env">金字塔:{pyr_html}</div></section>
<section class="page on" id="sec2"><h2>② 資料面(DuckDB 實測列數)</h2>
<div class="tablewrap"><table><tr><th>庫</th><th>總列</th><th>前六表</th></tr>
{db_rows}</table></div></section>
<section class="page on" id="sec3"><h2>③ 治理面(VSM 六燈+問題台帳 {len(prob['problems']) if prob else 0} 案)</h2>
<div class="kpi">{vsm_html}</div>
<div class="tablewrap"><table class="cards"><tr><th>處置</th><th>問題</th><th>明細</th></tr>
{prob_rows}</table></div></section>
<section class="page on" id="sec4"><h2>④ 資產面(台帳 {h['ledger_n']} 筆 · 名冊 counters)</h2>
<div class="env">{cnt_html}</div>
<div class="tablewrap"><table><tr><th>UI 頁(ui_support)</th><th>更新</th></tr>
{ui_rows}</table></div></section>
</div></div></div>
<div class="foot">同步機制:via_boot_update.sh ⑨步每日開機自動重生本頁+五系統分頁;
批次收官亦重生。誠實三態:黃=SKIP/候件/無解(不假綠)· 問題台帳 append-only</div>
</div></body></html>"""


def build() -> Path:
    T = _mdl089()
    tk = T.load_tokens()
    h = harvest()
    UI_OUT.parent.mkdir(parents=True, exist_ok=True)
    UI_OUT.write_text(render(h, T, tk), encoding="utf-8")
    return UI_OUT


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 問題台帳冊在位(六態分類+VSM 快照+append-only)",
        PROB.exists() and len(json.loads(PROB.read_text(encoding="utf-8"))["problems"]) >= 10
        and json.loads(PROB.read_text(encoding="utf-8"))["append_only"] is True)
    h = harvest()
    chk("② 測試面連動(最新 GRID 存證計數+SKIP 明細)",
        h["grid"] is not None and h["grid"]["n"] >= 110
        and len(h["grid"]["skips"]) == h["grid"]["SKIP"],
        f"({h['grid']['name'] if h['grid'] else '缺'})")
    chk("③ 資料面連動(雙庫實測列數)",
        "台股庫" in h["db"] and h["db"]["台股庫"].get("total", 0) > 1_000_000,
        f"(台股庫 {h['db'].get('台股庫', {}).get('total', 0):,} 列)")
    chk("④ 資產面連動(台帳筆數+名冊 counters+UI 冊)",
        (h["ledger_n"] or 0) >= 530 and h["counters"].get("CGC_MDL", 0) >= 90
        and len(h["uis"]) >= 5)
    p = build()
    html = p.read_text(encoding="utf-8")
    chk("⑤ 模板正主消費(token 冊 CSS+手機卡片化;零寫死)",
        "table.cards" in html and "@media" in html)
    chk("⑥ 問題板全案列示(12 案+六態中文+VSM 六燈)",
        html.count("<tr><td><span class=\"dot\"") >= 10 and "S3star" in html
        and "誠實無解" in html and "候操作員" in html)
    chk("⑦ 零 CDN 零外鏈+同步宣告(開機⑨步)",
        "http://" not in html and "https://" not in html and "⑨步" in html)
    boot = (HERE / "via_boot_update.sh").read_text(encoding="utf-8")
    chk("⑧ 開機同步接線(via_boot_update.sh 含樞紐重生步)",
        "CGC_MDL090" in boot or "SystemHub" in boot)
    tk = _mdl089().load_tokens()
    pw = tk.get("dashboard", {}).get("panel_w_px", 0)
    bp = tk.get("dashboard", {}).get("breakpoint_px", 0)
    chk("⑨ 左側面板(批190:token 冊取值零寫死+四系統節點+三層基座+"
        "toolkit 燈+四頁互鏈+行動斷點轉上列)",
        'id="leftpanel"' in html and f"width:{pw}px" in html
        and f"max-width:{bp}px" in html
        and all(k in html for k in ("VIA", "VDF", "VAP", "VRN"))
        and "因子庫 features" in html and "supportive toolkit" in html
        and 'href="VIA_UI_Dashboard_v0100.html"' in html
        and "flex-direction:column" in html,
        f"(panel {pw}px·bp {bp})")
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 系統同步樞紐(CGC_MDL090)· 八檢自測(零網路)===")
        return selftest()
    p = build()
    print(f"[UI] {p.name} · 同步=開機⑨步+批次收官")
    return 0


if __name__ == "__main__":
    sys.exit(main())

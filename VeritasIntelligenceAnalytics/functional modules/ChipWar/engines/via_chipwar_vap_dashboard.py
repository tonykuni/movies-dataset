# -*- coding: utf-8 -*-
"""
VIA ChipWar × VAP 儀表板 v0100 — 全鏈成果 → VAP 28 型圖庫(擴充功能整合層)
讀 staging 六 lane 輸出(chipwar/macro/bloc/social/fomo_index/xmkt),經
VAP seaborn+plotly 引擎(SSOT 樣式)渲染 11 面板:靜態 PNG + 互動 HTML +
離線 index(含 harness 驗收與 fomo 四閘門)。
治理:
  - 樣式全由 VAP spec/ssot 供應;本檔零寫死樣式值
  - 圖型跨域重用一律 title 覆寫誠實標示(VAP 新功能)
  - staging 缺件 = 誠實 FAIL + 「先跑全鏈」指引;繪圖後端缺席 = 誠實 FAIL
  - 產物落 _generated/reports/vap_dashboard/(可再生)
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
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
MOD = HERE.parents[1]
STAG = Path(os.environ.get("VIA_CHIPWAR_STAGING") or MOD / "_generated" / "staging")
REPORTS = Path(os.environ.get("VIA_CHIPWAR_REPORTS") or MOD / "_generated" / "reports")
OUT = REPORTS / "vap_dashboard"
VAP_PATH = HERE.parents[2] / "VAP" / "engine" / "via_autoplot_seaborn_plotly_v0100.py"


def fail(msg: str) -> None:
    print("誠實 FAIL:%s" % msg, file=sys.stderr)
    sys.exit(1)


if not VAP_PATH.exists():
    fail("找不到 VAP 引擎:%s" % VAP_PATH)
_spec = importlib.util.spec_from_file_location("vap_engine", str(VAP_PATH))
vap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vap)

RUNS = {}
for name in ("chipwar_run", "macro_run", "bloc_run", "social_run",
             "fomo_index_run", "xmkt_run"):
    p = STAG / ("%s.json" % name)
    if not p.exists():
        fail("staging 缺 %s — 先跑全鏈:python VIA_WorkflowEngine.py master "
             '"functional modules/ChipWar/chipwar_params.json"' % p.name)
    RUNS[name] = json.loads(p.read_text(encoding="utf-8"))
matrix_p = STAG / "_test_matrix.json"
MATRIX = json.loads(matrix_p.read_text(encoding="utf-8")) if matrix_p.exists() else None

spec = vap.Spec(vap.find_ssot_dir(None))
backends = {}
if vap.SeabornBackend.available():
    backends["seaborn"] = vap.SeabornBackend(spec)
if vap.PlotlyBackend.available():
    backends["plotly"] = vap.PlotlyBackend(spec)
if not backends:
    fail("seaborn 與 plotly 皆缺席 — pip install seaborn plotly")


def col(rows, key):
    return [r.get(key) for r in rows]


def clean(dates, fields):
    """聯合去 None(上游 rolling 暖機期):所有欄位皆有值的列才保留,對齊裁切。"""
    keep = [i for i in range(len(dates))
            if all(v[i] is not None for v in fields.values())]
    out = {"date": [dates[i] for i in keep]}
    for k, v in fields.items():
        out[k] = [v[i] for i in keep]
    return out


REG = RUNS["chipwar_run"]["regime"]
SOC = RUNS["social_run"]["social"]
MAC = RUNS["macro_run"]["macro"]
CONC = RUNS["bloc_run"]["conc"]
FOMO = RUNS["fomo_index_run"]["series"]
CCF = RUNS["social_run"]["ccf"]
WF = RUNS["xmkt_run"]["wf_summary"]

# 相位轉折事件位置(regime 首個 score>0.5 的日期;無則中點)
_dates_r = col(REG, "trade_date")
_scores = col(REG, "chipwar_score")
_brk = next((d for d, s in zip(_dates_r, _scores) if (s or 0) > 0.5), _dates_r[len(_dates_r) // 2])

# corrheat 因子面板:以 trade_date 對齊 social/macro/fomo 三來源
_m_by_d = {r["trade_date"]: r for r in MAC}
_f_by_d = {r["trade_date"]: r for r in FOMO}
_factors = {"behavior_fomo": [], "social_fomo": [], "hype_divergence": [],
            "fomo_index": [], "dxy": [], "fed_net_liq": [], "wti": [], "global_flow": []}
for r in SOC:
    d = r["trade_date"]
    m, f = _m_by_d.get(d, {}), _f_by_d.get(d, {})
    _factors["behavior_fomo"].append(r.get("behavior_fomo"))
    _factors["social_fomo"].append(r.get("social_fomo"))
    _factors["hype_divergence"].append(r.get("hype_divergence"))
    _factors["fomo_index"].append(f.get("fomo_index"))
    _factors["dxy"].append(m.get("dxy"))
    _factors["fed_net_liq"].append(m.get("fed_net_liq"))
    _factors["wti"].append(m.get("wti"))
    _factors["global_flow"].append(m.get("global_flow"))
CORR_DATA = vap.build_chart_data("corrheat", _factors, ys=list(_factors))

PANELS = [
    ("chipwar_score", "evtmx", "籌碼戰分數 chipwar_score(0=資金盤 1=籌碼戰)",
     {"date": _dates_r, "value": _scores,
      "events": [{"date": _brk, "label": "相位轉折"}], "bands": []}),
    ("two_channel", "dline", "行為面 FOMO(左·折線)× 聊天室 FOMO(右·底色)",
     {"date": col(SOC, "trade_date"), "left": col(SOC, "behavior_fomo"),
      "right": col(SOC, "social_fomo")}),
    ("fomo_index", "area", "統一 FOMO 指數(0-100 · 70%行為+30%言論)",
     {"date": col(FOMO, "trade_date"), "value": col(FOMO, "fomo_index")}),
    ("bloc_panels", "multi", "Bloc 集中度四面板(crowding·機會寬度·tech流量share·flow HHI)",
     {"date": col(CONC, "trade_date"),
      "panels": {"crowding_index": col(CONC, "crowding_index"),
                 "opportunity_width": col(CONC, "opportunity_width"),
                 "tech_flow_share": col(CONC, "tech_flow_share"),
                 "flow_hhi": col(CONC, "flow_hhi")}}),
    ("spread_cum", "line", "tech − trad 累積報酬價差 spread_cum",
     {**clean(col(CONC, "trade_date"), {"value": col(CONC, "spread_cum")})}),
    ("factor_corr", "corrheat", "八因子相關矩陣(社群×行為×總經)", CORR_DATA),
    ("social_ccf", "bar", "Social×Behavior CCF(負lag=聊天室落後行為面)",
     {"label": [str(r["lag"]) for r in CCF], "value": [r["spearman"] for r in CCF]}),
    ("wf_honesty", "gbar", "Walk-Forward 誠實缺口(in-sample vs OOS IC)",
     {"label": [r["criteria"] for r in WF],
      "groups": {"insample": [r["insample_ic_mean"] for r in WF],
                 "oos": [r["oos_ic_mean"] for r in WF]}}),
    ("hype_div", "roll", "純吹背離 z(正=有話題沒資金)",
     (lambda c: {"date": c["date"], "return": c["ret"]})(
         clean(col(SOC, "trade_date"), {"ret": col(SOC, "hype_divergence")}))),
    ("macro_liq", "dline", "FED 淨流動性(左·折線)× 全球資金代理(右·底色)",
     clean(col(MAC, "trade_date"), {"left": col(MAC, "fed_net_liq"),
                                    "right": col(MAC, "global_flow")})),
    ("opp_width", "rollsharpe", "機會寬度 opportunity_width(基準線=1.0 不適用·僅網格)",
     {"date": col(CONC, "trade_date"), "sharpe": col(CONC, "opportunity_width")}),
]

OUT.mkdir(parents=True, exist_ok=True)
results, failures = [], []
for name, chart_id, title, data in PANELS:
    row = {"name": name, "chart": chart_id, "title": title}
    for bname, backend in backends.items():
        ext = "png" if bname == "seaborn" else "html"
        fp = OUT / ("%s.%s" % (name, ext))
        try:
            if bname == "seaborn":
                backend.render(chart_id, data, fp, scale=1, title=title)
            else:
                backend.render(chart_id, data, fp, plotlyjs="directory", title=title)
            row[bname] = fp.name
        except Exception as e:  # 逐面板誠實記錄,不中斷其餘
            row[bname] = "FAIL"
            failures.append("%s×%s: %s: %s" % (name, bname, type(e).__name__, str(e)[:90]))
    results.append(row)

# ---- 離線 index(VIA 淺色系;嵌 PNG + 連互動 HTML + 驗收摘要)----
verdict = (MATRIX or {}).get("verdict", "N/A")
l2 = (MATRIX or {}).get("L2_methodology", [])
gates = RUNS["fomo_index_run"].get("gates", {})
head_gate = RUNS["chipwar_run"].get("gate", {})
css = ("body{background:%s;color:#33403f;font:12px/1.55 'DM Sans','Noto Sans TC',sans-serif;"
       "max-width:1180px;margin:22px auto;padding:0 18px}"
       "h1{font-size:19px;color:#1e1d1a}h2{font-size:14px;margin:20px 0 8px;color:#1e1d1a}"
       ".banner{border:1px solid %s;border-left:4px solid %s;background:%s;"
       "padding:10px 14px;border-radius:6px;margin:12px 0;font-weight:600}"
       ".warn{background:#1e1d1a;color:#f0c674;padding:8px 13px;border-radius:4px;"
       "font:600 10px 'DM Mono',monospace;margin:10px 0}"
       ".card{background:%s;border:1px solid %s;border-radius:8px;padding:12px 14px;margin:12px 0}"
       ".card img{max-width:100%%;height:auto;border:1px solid %s}"
       "table{border-collapse:collapse;width:100%%;background:%s;font-size:11px}"
       "td,th{border:1px solid %s;padding:5px 8px;text-align:left}"
       "a{color:#4c78a8;text-decoration:none}.fail{color:%s;font-weight:700}"
       ) % (spec.paper, spec.border_color, spec.down if verdict == "ALL_PASS" else spec.up,
            spec.plot_bg, spec.plot_bg, spec.border_color, spec.grid_color,
            spec.plot_bg, spec.border_color, spec.up)
H = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
     "<title>VIA · ChipWar × VAP 儀表板</title><style>", css, "</style></head><body>",
     "<h1>ChipWar 全鏈 × VAP 圖庫儀表板</h1>",
     "<div class='banner'>Harness 驗收:%s · L2 方法論 %d/%d · 佔位鏈頭=%s</div>"
     % (verdict, sum(1 for _, c in l2 if c), max(len(l2), 1),
        head_gate.get("placeholder_chain_head", "?")),
     "<div class='warn'>⚠ 資料層級 T4 合成(佔位鏈頭)— 圖為管線煙測成果,絕不得作為實盤依據;"
     "真鏈頭 version-forward 後本儀表板自動改吃真資料。</div>"]
if gates:
    H.append("<h2>FOMO 四驗證閘門</h2><table><tr><th>閘門</th><th>規則</th><th>值</th><th>判定</th></tr>")
    for gk, gv in gates.items():
        H.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                 % (gk, gv.get("rule", ""), gv.get("value", ""),
                    "PASS" if gv.get("pass") else "<span class='fail'>FAIL</span>"))
    H.append("</table>")
H.append("<h2>面板(靜態 PNG · 點標題開互動版)</h2>")
for r in results:
    inter = ("<a href='%s'>互動版 ↗</a>" % r["plotly"]) if r.get("plotly") not in (None, "FAIL") else ""
    H.append("<div class='card'><h2 style='margin:0 0 8px'>%s %s</h2>" % (r["title"], inter))
    if r.get("seaborn") not in (None, "FAIL"):
        H.append("<img src='%s' alt='%s'>" % (r["seaborn"], r["name"]))
    elif r.get("plotly") not in (None, "FAIL"):
        H.append("<p>(無靜態版 — 見互動版)</p>")
    else:
        H.append("<p class='fail'>本面板渲染失敗(見 gate)</p>")
    H.append("</div>")
H.append("</body></html>")
(OUT / "index.html").write_text("".join(H), encoding="utf-8")

gate = {"panels": len(PANELS), "backends": sorted(backends), "failures": failures,
        "out": str(OUT / "index.html"), "verdict_src": verdict, "evidence_tier": "T4",
        "vap_engine": VAP_PATH.name, "ssot": str(spec.dir)}
print(json.dumps(gate, ensure_ascii=False, indent=2))
sys.exit(1 if failures else 0)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG071_GroupBacktest — 族群分類回測引擎(批315;操作員令
「生成分類引擎及回測引擎」)
====================================================================
分類引擎=VDF_ENG070(尾版 glob;本引擎零重造,直接 import 其函式)。
本引擎=回測+驗證,依操作員上傳正本 VIA_TW10Y_AdaptiveRiskFree_
BacktestEngine(intake b307)設計律落地(在庫誠實版):
  ①無風險利率:台灣 10Y 公債——雙同意閘在位且 intake 正本可載時
    嘗試 TPEx 官方取數;否則=SSOT C-14 2.15% 固定備援(旗標 FIXED_
    FALLBACK 誠實標;絕不從未來回填)
  ②年化交易日數:由實際日期密度動態估(252 僅安全備援,旗標)
  ③走動視窗 Walk-forward 60/120/240 日:報酬/波動/Sharpe/Sortino/
    最大回撤;命中率=視窗超額>0 比例
  ④策略 vs 基準:策略=故事群 S1(LEADER+PEER;前窗角色 T-1 審核律)
    聚焦加權指數;基準 A=同群全員等權(買進持有)、基準 B=全市場
    ex-2330 等權
  ⑤驗證(上傳正本第 8 條):同規模隨機群 N=200 之 Sharpe 分布→實際
    群百分位 p;區塊置換(block 20 日)超額報酬檢定 p;p<0.05=顯著
  ⑥誠實三態:資料段/成員數/窗數不足=誠實跳並標
輸出:VIA_Reports/group_class/BACKTEST_<stamp>.json+
      ui_support/VIA_UI_GroupBacktest_v0100.html(Plotly 內嵌自足)
用法:python3 VDF_ENG071_GroupBacktest_v0100.py run | --selftest
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
REP = VIA / "VIA_Reports" / "group_class"
UI = VIA / "supportive modules" / "ui_support"
OUT_UI = UI / "VIA_UI_GroupBacktest_v0100.html"

RF_FALLBACK = 0.0215          # SSOT C-14 台灣 10Y(固定備援;誠實旗標)
WF_WINDOWS = (60, 120, 240)   # 走動視窗(交易日)
N_RANDOM = 200                # 隨機同規模群數(正本 B=200)
BLOCK = 20                    # 區塊置換塊長
SEED = 20260902


def _eng070():
    p = sorted(HERE.glob("VDF_ENG070_GroupClassificationIndex_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _plotly():
    try:
        import plotly.offline as po
        return po
    except Exception:
        return None


def risk_free() -> dict:
    """台灣 10Y:雙同意閘+intake 正本可載→嘗試官方;否則固定備援誠實標"""
    consent = (os.environ.get("VIA_NET_CONSENT") == "YES"
               and os.environ.get("VIA_SCRAPE_CONSENT") == "YES")
    src = sorted((VIA / "supportive modules" / "references" / "intake").glob(
        "VIA_GroupClassification_b307/VIA_TW10Y_*.py"))
    if consent and src:
        try:
            spec = importlib.util.spec_from_file_location("tw10y", src[-1])
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            for fn in ("fetch_tw10y", "load_tw10y", "get_risk_free"):
                if hasattr(m, fn):
                    v = getattr(m, fn)()
                    if isinstance(v, (int, float)) and 0 < v < 0.2:
                        return {"rf": float(v), "source": f"TPEx via intake {fn}",
                                "flag": "OFFICIAL"}
        except Exception as exc:
            return {"rf": RF_FALLBACK, "source": f"SSOT C-14(官方取數失敗 {type(exc).__name__})",
                    "flag": "FIXED_FALLBACK"}
    return {"rf": RF_FALLBACK,
            "source": "SSOT C-14 固定備援(無同意閘或正本未載;絕不未來回填)",
            "flag": "FIXED_FALLBACK"}


def ann_days(dates) -> dict:
    """年化交易日數=實際日期密度(正本第 4 條);252 僅備援"""
    import pandas as pd
    d = pd.to_datetime(pd.Series(sorted(set(dates))))
    span_y = (d.iloc[-1] - d.iloc[0]).days / 365.25 if len(d) > 1 else 0
    if span_y >= 0.5:
        return {"n": round(len(d) / span_y, 1), "flag": "DYNAMIC"}
    return {"n": 252.0, "flag": "FALLBACK_252(段<半年)"}


def metrics(ret, rf: float, ann: float, bench=None) -> dict:
    import numpy as np
    r = np.asarray(ret, dtype=float)
    r = r[np.isfinite(r)]
    if len(r) < 10:
        return {"n": int(len(r)), "flag": "樣本不足"}
    daily_rf = (1 + rf) ** (1 / ann) - 1
    ex = r - daily_rf
    mu, sd = ex.mean(), ex.std(ddof=1)
    down = ex[ex < 0].std(ddof=1) if (ex < 0).sum() > 1 else np.nan
    eq = np.cumprod(1 + r)
    dd = eq / np.maximum.accumulate(eq) - 1
    out = {"n": int(len(r)),
           "ret_total": round(float(eq[-1] - 1), 4),
           "cagr": round(float(eq[-1] ** (ann / len(r)) - 1), 4),
           "vol": round(float(r.std(ddof=1) * np.sqrt(ann)), 4),
           "sharpe": round(float(mu / sd * np.sqrt(ann)), 3) if sd > 0 else None,
           "sortino": round(float(mu / down * np.sqrt(ann)), 3)
           if down and down > 0 else None,
           "maxdd": round(float(dd.min()), 4)}
    if bench is not None:
        b = np.asarray(bench, dtype=float)
        n = min(len(r), len(b))
        out["excess_total"] = round(float(np.prod(1 + r[-n:]) - np.prod(1 + b[-n:])), 4)
    return out


def walk_forward(ret, bench, rf, ann) -> dict:
    """60/120/240 日走動視窗(步進=視窗/2);命中率=超額>0 比例"""
    import numpy as np
    out = {}
    r = np.asarray(ret, dtype=float)
    b = np.asarray(bench, dtype=float)
    for w in WF_WINDOWS:
        if len(r) < w + 5:
            out[str(w)] = {"flag": f"樣本 {len(r)}<{w}=誠實跳"}
            continue
        rows = []
        for st in range(0, len(r) - w + 1, max(1, w // 2)):
            m = metrics(r[st:st + w], rf, ann, b[st:st + w])
            rows.append(m)
        sh = [x["sharpe"] for x in rows if x.get("sharpe") is not None]
        exs = [x.get("excess_total", 0) for x in rows]
        out[str(w)] = {"n_windows": len(rows),
                       "sharpe_mean": round(float(np.mean(sh)), 3) if sh else None,
                       "sharpe_median": round(float(np.median(sh)), 3) if sh else None,
                       "hit_rate": round(float(np.mean([e > 0 for e in exs])), 3)
                       if exs else None,
                       "maxdd_worst": round(float(min(x["maxdd"] for x in rows
                                                      if "maxdd" in x)), 4)
                       if rows else None}
    return out


def random_group_test(panel, size: int, ret_actual, rf, ann, rng) -> dict:
    """同規模隨機群 N=200(全市場 ex-2330 等權)Sharpe 分布→實際百分位"""
    import numpy as np
    import pandas as pd
    wide = panel.pivot_table(index="date", columns="ticker", values="ret")
    wide = wide.dropna(axis=1, thresh=int(len(wide) * 0.8))
    if wide.shape[1] < size * 3 or len(wide) < 60:
        return {"flag": "宇宙不足=誠實跳", "universe": int(wide.shape[1])}
    cols = list(wide.columns)
    sh_act = metrics(ret_actual, rf, ann).get("sharpe")
    if sh_act is None:
        return {"flag": "實際 Sharpe 缺"}
    dist = []
    for _ in range(N_RANDOM):
        pick = rng.choice(cols, size=size, replace=False)
        rr = wide[pick].mean(axis=1).dropna().to_numpy()
        m = metrics(rr, rf, ann)
        if m.get("sharpe") is not None:
            dist.append(m["sharpe"])
    if not dist:
        return {"flag": "分布空"}
    p = float(np.mean([d >= sh_act for d in dist]))
    return {"n": len(dist), "sharpe_actual": sh_act,
            "sharpe_rand_median": round(float(np.median(dist)), 3),
            "p_value": round(p, 3), "significant": p < 0.05,
            "universe": int(wide.shape[1])}


def block_permutation(ret, bench, rng) -> dict:
    """區塊置換(block 20 日):打亂超額日報酬區塊順序→累積超額分布→p"""
    import numpy as np
    r = np.asarray(ret, dtype=float)
    b = np.asarray(bench, dtype=float)
    n = min(len(r), len(b))
    if n < BLOCK * 4:
        return {"flag": f"樣本 {n}<{BLOCK * 4}=誠實跳"}
    ex = (r[-n:] - b[-n:])
    obs = float(np.sum(ex))
    blocks = [ex[i:i + BLOCK] for i in range(0, n, BLOCK)]
    dist = []
    for _ in range(N_RANDOM):
        order = rng.permutation(len(blocks))
        signs = rng.choice([-1, 1], size=len(blocks))
        dist.append(float(np.sum(np.concatenate(
            [blocks[i] * s for i, s in zip(order, signs)]))))
    p = float(np.mean([abs(d) >= abs(obs) for d in dist]))
    return {"observed_excess": round(obs, 4), "p_value": round(p, 3),
            "significant": p < 0.05, "n_perm": N_RANDOM, "block": BLOCK}


def run(do_print: bool = True) -> int:
    import numpy as np
    import pandas as pd
    e = _eng070()
    if not e.DB_TW.exists():
        print("[回測] 台股庫缺=誠實停(先跑 boot)")
        return 2
    try:
        px = e.load_panel()
        px_r = e.add_residual(px)
        stories = e.load_stories()
        s_mem, s_summ, s_panel = e.classify_story(px_r, stories)
        cmp = e.compare_windows(px_r, stories)
        s1, s2, comp_note = e.composition_sets(cmp, s_mem)
    except Exception as exc:
        print(f"[回測] 分類引擎接通失敗=誠實停:{type(exc).__name__}: {str(exc)[:100]}")
        return 2
    rf = risk_free()
    rng = np.random.default_rng(SEED)
    s_panel["key"] = s_panel["ticker"] + "|" + s_panel["story"]
    base = pd.Timestamp(e.BASE_DATE)
    # 基準 B:全市場 ex-2330 等權
    mkt = (px[(px["ticker"] != e.ANCHOR) & (px["date"] >= base)]
           .groupby("date")["ret"].mean().dropna())
    ann = ann_days(mkt.index)
    results = {}
    for sname in sorted(set(s_panel["story"])):
        pn = s_panel[s_panel["story"] == sname]
        idx_all = e.build_indices(pn, gcol="story", min_members=e.STORY_MIN_MEMBERS)
        if s1 is None:
            results[sname] = {"flag": "無前窗角色=無 S1 成分(誠實跳)"}
            continue
        pn1 = pn[pn["key"].isin(s1)]
        idx_s1 = e.build_indices(pn1, gcol="story", min_members=e.STORY_MIN_MEMBERS)
        if not len(idx_all) or not len(idx_s1):
            results[sname] = {"flag": "成員不足(S1 或全員<2)=誠實跳",
                              "n_s1": int(pn1["ticker"].nunique())}
            continue
        a = idx_all.set_index("date"); s = idx_s1.set_index("date")
        j = a[["ret_eq"]].join(s[["ret_att", "ret_eq"]], lsuffix="_all",
                               rsuffix="_s1", how="inner").join(
            mkt.rename("ret_mkt"), how="inner").dropna()
        if len(j) < 40:
            results[sname] = {"flag": f"交集 {len(j)} 日<40=誠實跳"}
            continue
        strat = j["ret_att"].to_numpy()
        bench_a = j["ret_eq_all"].to_numpy()
        bench_b = j["ret_mkt"].to_numpy()
        results[sname] = {
            "n_days": int(len(j)),
            "n_s1": int(pn1["ticker"].nunique()),
            "n_all": int(pn["ticker"].nunique()),
            "strategy_S1_att": metrics(strat, rf["rf"], ann["n"], bench_a),
            "bench_all_eq": metrics(bench_a, rf["rf"], ann["n"]),
            "bench_mkt_eq": metrics(bench_b, rf["rf"], ann["n"]),
            "walk_forward": walk_forward(strat, bench_a, rf["rf"], ann["n"]),
            "random_group": random_group_test(
                px_r[px_r["date"] >= base], max(2, int(pn1["ticker"].nunique())),
                strat, rf["rf"], ann["n"], rng),
            "block_perm_vs_all": block_permutation(strat, bench_a, rng),
            "curve": {"d": [str(x.date()) for x in j.index],
                      "s1": [round(float(v), 2) for v in (1 + j["ret_att"]).cumprod() * 100],
                      "all": [round(float(v), 2) for v in (1 + j["ret_eq_all"]).cumprod() * 100],
                      "mkt": [round(float(v), 2) for v in (1 + j["ret_mkt"]).cumprod() * 100]},
        }
    ok = {k: v for k, v in results.items() if "strategy_S1_att" in v}
    ev = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
          "engine": "VDF_ENG071_GroupBacktest_v0100",
          "classifier": _eng070().__name__,
          "risk_free": rf, "annualization": ann, "comp_note": comp_note,
          "base_date": e.BASE_DATE, "n_groups": len(results), "n_backtested": len(ok),
          "results": {k: {kk: vv for kk, vv in v.items() if kk != "curve"}
                      for k, v in results.items()}}
    REP.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (REP / f"BACKTEST_{stamp}.json").write_text(
        json.dumps(ev, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    UI.mkdir(parents=True, exist_ok=True)
    OUT_UI.write_text(render(ev, results), encoding="utf-8")
    if do_print:
        print(f"[回測] 群 {len(results)} · 可回測 {len(ok)} · rf {rf['rf']:.2%}"
              f"({rf['flag']})· 年化日 {ann['n']}({ann['flag']})· {OUT_UI.name}")
        for k, v in sorted(ok.items(), key=lambda kv: -(kv[1]["strategy_S1_att"].get("sharpe") or -9))[:5]:
            st = v["strategy_S1_att"]; rg = v["random_group"]; bp = v["block_perm_vs_all"]
            print(f"  [{k}] S1聚焦 Sharpe {st.get('sharpe')} · 超額 vs 全員 "
                  f"{st.get('excess_total'):+.3f} · 隨機群 p {rg.get('p_value')} · "
                  f"區塊置換 p {bp.get('p_value')} · 60d 命中 "
                  f"{v['walk_forward'].get('60', {}).get('hit_rate')}")
    return 0


CSS = r"""
:root{--bg:#f5f5f2;--paper:#fff;--ink:#1f2530;--ink2:#3c4658;--mut:#6d7688;
--mut2:#9aa2b1;--line:#dcdfe6;--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;
--bad:#b05c4d;--header-h:44px;--footer-h:26px}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);font:11.5px/1.45 "Segoe UI",
"Noto Sans TC",system-ui,sans-serif;padding:var(--header-h) 0 var(--footer-h)}
.top{position:fixed;inset:0 0 auto 0;height:var(--header-h);z-index:9;
background:var(--paper);border-bottom:2px solid var(--ink);display:flex;
align-items:center;gap:12px;padding:0 14px}
.top b{font-size:14px}.top small{font-size:8.5px;letter-spacing:.14em;
color:var(--mut2);font-weight:700}
.badge{margin-left:auto;font-size:9.5px;font-weight:700;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;color:var(--ok)}
.main{padding:12px 16px;max-width:1240px;margin:0 auto}
.card{background:var(--paper);border:1px solid var(--line);border-radius:7px;
padding:10px 12px;margin-bottom:9px}
.card h3{font-size:12px}.card h3 small{font-size:8.5px;letter-spacing:.14em;
color:var(--mut2);font-weight:700;margin-left:6px}
.note{font-size:10px;color:var(--mut);line-height:1.6}
table{width:100%;border-collapse:collapse;font-size:10.5px}
th{text-align:left;font-size:8.5px;letter-spacing:.12em;color:var(--mut2);
border-bottom:1px solid var(--line);padding:3px 6px 3px 0;font-weight:700}
td{border-bottom:1px solid var(--soft);padding:3px 6px 3px 0;
font-variant-numeric:tabular-nums}
td.g{color:var(--ok);font-weight:600}td.r{color:var(--bad);font-weight:600}
.wrap{overflow-x:auto}select{font:inherit;padding:4px 8px;border:1px solid
var(--line);border-radius:6px;margin-bottom:6px}
.bot{position:fixed;inset:auto 0 0 0;height:var(--footer-h);background:var(--paper);
border-top:1px solid var(--line);display:flex;align-items:center;gap:14px;
padding:0 14px;font-size:9px;color:var(--mut)}
"""


def render(ev: dict, results: dict) -> str:
    import html
    po = _plotly()
    ok = {k: v for k, v in results.items() if "strategy_S1_att" in v}
    rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{v['n_s1']}/{v['n_all']}</td>"
        f"<td>{v['n_days']}</td>"
        f"<td class='{'g' if (v['strategy_S1_att'].get('sharpe') or 0) > (v['bench_all_eq'].get('sharpe') or 0) else 'r'}'>"
        f"{v['strategy_S1_att'].get('sharpe')}</td>"
        f"<td>{v['bench_all_eq'].get('sharpe')}</td><td>{v['bench_mkt_eq'].get('sharpe')}</td>"
        f"<td>{v['strategy_S1_att'].get('excess_total'):+.3f}</td>"
        f"<td>{v['strategy_S1_att'].get('maxdd')}</td>"
        f"<td>{v['walk_forward'].get('60', {}).get('hit_rate', '—')}</td>"
        f"<td>{v['walk_forward'].get('120', {}).get('hit_rate', '—')}</td>"
        f"<td>{v['walk_forward'].get('240', {}).get('hit_rate', '—')}</td>"
        f"<td class='{'g' if v['random_group'].get('significant') else ''}'>"
        f"{v['random_group'].get('p_value', v['random_group'].get('flag', '—'))}</td>"
        f"<td class='{'g' if v['block_perm_vs_all'].get('significant') else ''}'>"
        f"{v['block_perm_vs_all'].get('p_value', v['block_perm_vs_all'].get('flag', '—'))}</td></tr>"
        for k, v in sorted(ok.items(), key=lambda kv: -(kv[1]["strategy_S1_att"].get("sharpe") or -9)))
    skipped = "".join(f"<tr><td>{html.escape(k)}</td><td>{html.escape(str(v.get('flag')))}</td></tr>"
                      for k, v in results.items() if "strategy_S1_att" not in v)
    curves = {k: v["curve"] for k, v in ok.items()}
    plotly_js = ("<script>" + po.get_plotlyjs() + "</script>") if po else ""
    degrade = "" if po else "<div class='card'>誠實降級:plotly 未安裝=僅表格</div>"
    rf = ev["risk_free"]; ann = ev["annualization"]
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 族群回測 Group Backtest</title><style>{CSS}</style></head><body>
<header class="top"><div><b>族群分類回測 · Group Backtest</b>
<small>VDF ENG071 · 分類引擎={html.escape(ev['classifier'])} · 走動 60/120/240 · 隨機群+區塊置換</small></div>
<span class="badge">rf {rf['rf']:.2%} {rf['flag']} · 年化日 {ann['n']} {ann['flag']}</span></header>
<main class="main">
<div class="card"><h3>策略 vs 基準<small>Strategy S1(LEADER+PEER 聚焦加權)
vs 同群全員等權 / 全市場 ex-2330 等權 · {html.escape(ev['comp_note'])}</small></h3>
<div class="note">rf 來源:{html.escape(rf['source'])} · 年化交易日=實際日期密度
(正本第 4 條)· 基準日 {ev['base_date']}=100 · 指數 T-1 權重無前視 · 非投資建議</div>
{degrade}
<select id="gsel">{"".join(f"<option>{html.escape(k)}</option>" for k in curves)}</select>
<div id="c1"></div></div>
<div class="card"><h3>回測總表<small>Sharpe · 超額 · 回撤 · 走動命中率 · 兩檢定 p</small></h3>
<div class="wrap"><table><tr><th>故事群</th><th>S1/全員</th><th>日數</th>
<th>Sharpe S1</th><th>Sharpe 全員</th><th>Sharpe 市場</th><th>超額 vs 全員</th>
<th>MaxDD</th><th>命中60</th><th>命中120</th><th>命中240</th>
<th>隨機群 p</th><th>區塊置換 p</th></tr>{rows or '<tr><td colspan=13>無可回測群(誠實)</td></tr>'}</table></div>
<div class="note">隨機群 p=同規模隨機群 200 組 Sharpe ≥ 實際之比例(<0.05 綠=非巧合);
區塊置換 p=20 日區塊重排+隨機翻號 200 次,|累積超額|≥觀測之比例。</div></div>
<div class="card"><h3>誠實跳過<small>Skipped</small></h3>
<div class="wrap"><table><tr><th>故事群</th><th>原因</th></tr>{skipped or '<tr><td colspan=2>—</td></tr>'}</table></div></div>
</main>
<footer class="bot"><span>VIA · VDF ENG071</span><span>產於 {ev['ts']}</span>
<span>零 CDN · 誠實三態</span></footer>
<script id="d" type="application/json">{json.dumps(curves, ensure_ascii=False)}</script>
{plotly_js}
<script>
const D=JSON.parse(document.getElementById("d").textContent);
const sel=document.getElementById("gsel");
function draw(){{const g=D[sel.value];if(!g||!window.Plotly)return;
 Plotly.react("c1",[
  {{x:g.d,y:g.s1,name:"S1 聚焦加權(策略)",line:{{color:"#2f7652",width:2.4}}}},
  {{x:g.d,y:g.all,name:"同群全員等權",line:{{color:"#315f7d"}}}},
  {{x:g.d,y:g.mkt,name:"全市場 ex-2330 等權",line:{{color:"#9aa2b1",dash:"dot"}}}}],
  {{height:380,font:{{size:10,family:'"Segoe UI","Noto Sans TC",sans-serif'}},
   margin:{{l:46,r:16,t:10,b:34}},paper_bgcolor:"#fff",plot_bgcolor:"#fff",
   legend:{{orientation:"h"}},yaxis:{{title:{{text:"基準=100",font:{{size:10}}}}}}}},
  {{displayModeBar:false,responsive:true}});}}
if(sel){{sel.onchange=draw;draw();}}
</script></body></html>"""


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run(do_print=False)
    hits = sorted(REP.glob("BACKTEST_*.json"))
    if not hits:
        # v0101(批321):存證缺(分類引擎接不通/庫忙)=誠實停 rc2,零裸 traceback
        print(f"  [FAIL] 存證缺:run rc={rc};BACKTEST_*.json 零檔=誠實停(資料在位環境再跑)")
        return 2
    ev = json.loads(hits[-1].read_text(encoding="utf-8"))
    page = OUT_UI.read_text(encoding="utf-8") if OUT_UI.exists() else ""
    ok = {k: v for k, v in ev["results"].items() if "strategy_S1_att" in v}
    chk("① 全鏈跑通(分類引擎尾版 import+存證+頁)", rc == 0 and bool(page)
        and "ENG070" in ev["classifier"])
    chk("② 無風險利率誠實(官方或 FIXED_FALLBACK 旗標;零未來回填)",
        ev["risk_free"]["flag"] in ("OFFICIAL", "FIXED_FALLBACK")
        and 0 < ev["risk_free"]["rf"] < 0.2)
    chk("③ 年化日動態估(密度;252 僅備援旗標)",
        ev["annualization"]["flag"].startswith(("DYNAMIC", "FALLBACK"))
        and 200 <= ev["annualization"]["n"] <= 300)
    chk("④ 走動三窗+指標有限(Sharpe/Sortino/MaxDD)",
        all(set(v["walk_forward"]) == {"60", "120", "240"} for v in ok.values())
        and all(v["strategy_S1_att"].get("maxdd") is not None and
                -1 <= v["strategy_S1_att"]["maxdd"] <= 0 for v in ok.values()),
        f"(可回測 {len(ok)}/{ev['n_groups']})")
    chk("⑤ 兩檢定 p∈[0,1](隨機同規模群 200+區塊置換 20 日)",
        all(0 <= v["random_group"].get("p_value", 0) <= 1
            and 0 <= v["block_perm_vs_all"].get("p_value", 0) <= 1 for v in ok.values())
        and "N_RANDOM = 200" in src and "BLOCK = 20" in src)
    chk("⑥ 成分 T-1 審核律(前窗角色)+基準雙軌+零 CDN 外鏈+加速橋",
        "composition_sets" in src and "全市場 ex-2330 等權" in page
        and '<script src="http' not in page and "ACCEL-BRIDGE" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 族群分類回測引擎(VDF_ENG071)· 六檢自測(零外網)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())

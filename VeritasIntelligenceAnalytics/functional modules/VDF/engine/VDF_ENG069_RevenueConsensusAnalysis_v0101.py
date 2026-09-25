#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG069_RevenueConsensusAnalysis — 台股月營收×共識分析(批264)
====================================================================
操作員令:「via taiwan stock revenue analysis (with consensus data)」
——把既有 ENG063 月營收分析視圖×共識庫接成分析成品(Zero-Hydra:
零網路零重抓,單庫 SQL join 全讀在庫存證):
  ①每檔最新月:yoy_pct 年增/mom_pct 月增/yoy_streak 連續年增月數
    /high_60m 近60月新高 × consensus_latest 目標價中位/upside/分析師數
  ②四象限分佈(營收動能 yoy>0 × 共識 upside>0)+雙強榜
    (yoy>0 且 upside>0,依 upside 排序)
  ③族群層:revenue_group_analysis 最新月動能榜直引(ENG063 產,不重算)
  ④誠實界定:共識覆蓋≠全市場(覆蓋數如實標);未覆蓋不假 0;
    來源分欄不跨源平均
輸出:
  VIA_Reports/revenue_consensus/REV_CONSENSUS_<月>.json(存證)
  ui_support/VIA_UI_RevenueConsensusAnalysis_v0100.html(手機單欄+
    內嵌 SVG 四象限散點=VAP 視覺律零 CDN;Portal 尾版自收)
v0100→v0101(批273 操作員令「卡住 不卡斷」):唯讀連線三重試
(背景日更寫庫撞鎖=2s 退避;全敗=誠實停不懸吊)+run 入口
try 包=任何庫例外一句誠實訊息 rc2,零裸 traceback。
用法:python3 VDF_ENG069_RevenueConsensusAnalysis_v0101.py run | probe
      | --selftest
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

import html
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
REP = VIA / "VIA_Reports" / "revenue_consensus"
OUT_UI = (VIA / "supportive modules" / "ui_support"
          / "VIA_UI_RevenueConsensusAnalysis_v0100.html")
def _connect_ro(dbp):
    """唯讀連線三重試(批273 不卡斷令):背景日更寫庫=鎖忙→2s 退避
    ×3;全敗=拋原例外由呼叫端誠實停(零 Read-Host 零懸吊)"""
    import time
    import duckdb
    last = None
    for i in range(3):
        try:
            return duckdb.connect(str(dbp), read_only=True)
        except Exception as exc:
            last = exc
            time.sleep(2)
    raise last



# 單庫 join:每檔最新月營收動能 × 共識最新視圖(全在庫零發明)。
# 去重律(批264 實測揪蟲):consensus_latest 每 code 可雙源
# (CNYES_FACTSET+EXTERNAL_ANALYST)→每 code 取分析師數最多之單源列
# (平手依源名;來源分欄不跨源平均=既有紀律)。
Q_JOIN = """
WITH latest AS (
  SELECT code, MAX(ym) AS ym FROM monthly_revenue_analysis GROUP BY code
), con1 AS (
  SELECT * FROM consensus_latest
  QUALIFY ROW_NUMBER() OVER (PARTITION BY code
    ORDER BY n_analysts DESC NULLS LAST, source) = 1
)
SELECT m.code, m.ym, m.revenue, m.mom_pct, m.yoy_pct, m.yoy_streak,
       m.high_60m, c.target_median,
       c.upside_pct * 100,  -- 單位律(批264 實測):在庫實為分數→×100 百分比
       c.n_analysts, c.source
FROM monthly_revenue_analysis m
JOIN latest l ON m.code = l.code AND m.ym = l.ym
LEFT JOIN con1 c ON m.code = c.code
ORDER BY m.code
"""


def analyze() -> dict:
    c = _connect_ro(DB_TW)
    try:
        rows = c.execute(Q_JOIN).fetchall()
        groups = c.execute(
            "SELECT gid, ym, n_members, yoy_median, "
            "CASE WHEN n_yoy > 0 THEN CAST(n_yoy_pos AS DOUBLE)/n_yoy END "
            "FROM revenue_group_analysis "
            "WHERE ym = (SELECT MAX(ym) FROM revenue_group_analysis) "
            "ORDER BY yoy_median DESC NULLS LAST LIMIT 12").fetchall()
    finally:
        c.close()
    all_rows = []
    for (code, ym, rev, mom, yoy, streak, hi, tp, up, n, src) in rows:
        all_rows.append({
            "code": code, "ym": ym, "revenue": rev,
            "mom": round(float(mom), 1) if mom is not None else None,
            "yoy": round(float(yoy), 1) if yoy is not None else None,
            "streak": streak, "high_60m": bool(hi),
            "tp": tp, "upside": round(float(up), 1) if up is not None else None,
            "n_analysts": n, "source": src})
    cov = [r for r in all_rows
           if r["upside"] is not None and r["yoy"] is not None]
    quad = {"strong": 0, "rev_only": 0, "cons_only": 0, "weak": 0}
    for r in cov:
        k = ("strong" if r["yoy"] > 0 and r["upside"] > 0 else
             "rev_only" if r["yoy"] > 0 else
             "cons_only" if r["upside"] > 0 else "weak")
        quad[k] += 1
    dual = sorted((r for r in cov if r["yoy"] > 0 and r["upside"] > 0),
                  key=lambda r: -r["upside"])[:30]
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "latest_ym": max((r["ym"] for r in all_rows), default=None),
            "n_market": len(all_rows), "n_covered": len(cov),
            "quad": quad, "dual": dual,
            "cov_rows": cov,
            "groups": [{"gid": g, "ym": y, "members": m,
                        "yoy_median": round(float(md), 1)
                        if md is not None else None,
                        "pos_ratio": round(float(p), 2)
                        if p is not None else None}
                       for g, y, m, md, p in groups]}


def _svg_quad(cov: list) -> str:
    """四象限散點:x=最新月 yoy、y=共識 upside(軸截 ±80 誠實標)"""
    if not cov:
        return "<p>共識×營收交集 0=誠實無圖</p>"
    W = H = 340
    cx, cy = W / 2, H / 2

    def px(v, lim=80.0):
        return max(-lim, min(lim, v)) / lim
    pts = []
    for r in cov:
        x = cx + px(r["yoy"]) * (W / 2 - 20)
        y = cy - px(r["upside"]) * (H / 2 - 20)
        col = "var(--green)" if r["yoy"] > 0 and r["upside"] > 0 \
            else "var(--muted)"
        pts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" '
                   f'fill="{col}" opacity=".7"><title>'
                   f'{html.escape(r["code"])} yoy {r["yoy"]}% / '
                   f'upside {r["upside"]}%</title></circle>')
    return (f'<svg viewBox="0 0 {W} {H}" role="img" '
            'style="width:100%;max-width:400px;height:auto">'
            f'<line x1="{cx}" y1="10" x2="{cx}" y2="{H - 10}" '
            'stroke="var(--line)"/>'
            f'<line x1="10" y1="{cy}" x2="{W - 10}" y2="{cy}" '
            'stroke="var(--line)"/>'
            f'<text x="{W - 12}" y="{cy - 6}" text-anchor="end" '
            'font-size="10" fill="var(--muted)">yoy% →(截±80)</text>'
            f'<text x="{cx + 6}" y="18" font-size="10" '
            'fill="var(--muted)">upside% ↑</text>'
            + "".join(pts) + "</svg>")


def render(d: dict) -> str:
    dual_rows = "".join(
        f"<tr><td>{html.escape(r['code'])}</td><td>{r['ym']}</td>"
        f"<td class='g'>{r['yoy']:+.1f}%</td>"
        f"<td>{r['streak'] or 0} 月</td>"
        f"<td>{'★' if r['high_60m'] else ''}</td>"
        f"<td class='g'>{r['upside']:+.1f}%</td>"
        f"<td>{r['n_analysts'] or '—'}</td></tr>" for r in d["dual"])
    grp_rows = "".join(
        f"<tr><td>{html.escape(str(g['gid']))}</td><td>{g['members']}</td>"
        f"<td class='{'g' if (g['yoy_median'] or 0) > 0 else 'r'}'>"
        f"{'%+.1f%%' % g['yoy_median'] if g['yoy_median'] is not None else '—'}"
        f"</td><td>{g['pos_ratio'] if g['pos_ratio'] is not None else '—'}"
        "</td></tr>" for g in d["groups"])
    q = d["quad"]
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 月營收×共識分析</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--green:#5a9e6f;--red:#c96b5a}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--green:#79b58c;
--red:#d98a7c}}}}
body{{background:var(--bg);color:var(--text);margin:0 auto;
font:13px/1.55 "Segoe UI","Noto Sans TC",sans-serif;padding:16px;
max-width:860px}}
h1{{font-size:16px}}h2{{font-size:12px;color:var(--muted);
text-transform:uppercase;letter-spacing:.08em;margin:18px 0 6px}}
.sub{{color:var(--muted);font-size:11px}}
table{{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:8px}}
td,th{{padding:6px 8px;border-bottom:1px solid var(--line);
text-align:left;font-variant-numeric:tabular-nums}}
th{{font-size:10.5px;color:var(--muted)}}
td.g{{color:var(--green);font-weight:600}}td.r{{color:var(--red)}}
.wrap{{overflow-x:auto}}</style></head><body>
<h1>台股月營收×共識分析(批264)</h1>
<div class="sub">最新月 {d['latest_ym']} · 全市場 {d['n_market']} 檔 ·
共識×營收交集 {d['n_covered']} 檔(覆蓋如實標,未覆蓋不假 0)·
產於 {d['ts']} · 全讀在庫零網路</div>
<h2>四象限(yoy × upside)</h2>{_svg_quad(d['cov_rows'])}
<div class="sub">雙強 {q['strong']} · 僅營收正 {q['rev_only']} ·
僅共識正 {q['cons_only']} · 雙弱 {q['weak']}</div>
<h2>雙強榜(yoy&gt;0 且 upside&gt;0;依 upside;前 30)</h2>
<div class="wrap"><table><tr><th>代碼</th><th>月</th><th>年增</th>
<th>連增</th><th>60月高</th><th>upside</th><th>分析師</th></tr>
{dual_rows}</table></div>
<h2>族群月營收動能榜(ENG063 視圖直引)</h2>
<div class="wrap"><table><tr><th>族群</th><th>成員</th><th>年增中位</th>
<th>正年增佔比</th></tr>{grp_rows}</table></div>
<p class="sub">來源:monthly_revenue_analysis(ENG063/MOPS 正源)×
consensus_latest(ENG069/071)· 來源分欄不跨源平均 · 非投資建議</p>
</body></html>"""


def probe() -> int:
    print(f"  [{'OK' if DB_TW.exists() else 'FAIL'}] 台股庫 {DB_TW.name}")
    return 0 if DB_TW.exists() else 2


def run() -> int:
    if not DB_TW.exists():
        print("[營收共識] 台股庫缺=誠實停(先跑 boot)")
        return 2
    try:
        d = analyze()
    except Exception as exc:
        print(f"[分析] 庫忙/例外=誠實停({type(exc).__name__}):"
              "背景日更寫庫中,稍後再跑 via-analysis 即通")
        return 2
    REP.mkdir(parents=True, exist_ok=True)
    j = REP / f"REV_CONSENSUS_{str(d['latest_ym']).replace('-', '')}.json"
    ev = {k: v for k, v in d.items() if k != "cov_rows"}
    j.write_text(json.dumps(ev, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    OUT_UI.write_text(render(d), encoding="utf-8")
    q = d["quad"]
    print(f"[營收共識] {d['latest_ym']} · 交集 {d['n_covered']}/"
          f"{d['n_market']} · 雙強 {q['strong']} · {j.name} + {OUT_UI.name}")
    for r in d["dual"][:3]:
        print(f"  [雙強] {r['code']} yoy {r['yoy']:+.1f}% 連增 "
              f"{r['streak'] or 0} 月 upside {r['upside']:+.1f}%")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run()
    d = analyze() if rc == 0 else {}
    chk("① 單庫 join 接通(營收×共識;零網路)", rc == 0
        and d.get("n_market", 0) > 1000 and d.get("n_covered", 0) > 0)
    chk("② 每檔唯一最新月(join 不放大列數;交集代碼零重複)",
        len({r["code"] for r in d.get("cov_rows", [])})
        == len(d.get("cov_rows", [])) == d.get("n_covered", -1)
        and d.get("n_market", 0) >= d.get("n_covered", 0))
    q = d.get("quad", {})
    chk("③ 四象限守恆(四格和=交集數)",
        sum(q.values()) == d.get("n_covered", -1))
    chk("④ 雙強榜律(全列 yoy>0 且 upside>0,依 upside 降冪)",
        all(r["yoy"] > 0 and r["upside"] > 0 for r in d.get("dual", []))
        and [r["upside"] for r in d.get("dual", [])] ==
        sorted((r["upside"] for r in d.get("dual", [])), reverse=True))
    page = OUT_UI.read_text(encoding="utf-8") if OUT_UI.exists() else ""
    chk("⑤ U/I 頁產出(四象限 SVG+族群榜+零 CDN)",
        "月營收×共識分析" in page and "<svg" in page
        and "族群月營收動能榜" in page and 'src="http' not in page)
    chk("⑥ 零網路+加速橋+誠實界定宣告", "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src
                for k in ("requests", "httpx", "urllib"))
        and "誠實" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 月營收×共識分析(VDF_ENG069)· 六檢自測(零網路)===")
        return selftest()
    if "probe" in a:
        return probe()
    return run()


if __name__ == "__main__":
    sys.exit(main())


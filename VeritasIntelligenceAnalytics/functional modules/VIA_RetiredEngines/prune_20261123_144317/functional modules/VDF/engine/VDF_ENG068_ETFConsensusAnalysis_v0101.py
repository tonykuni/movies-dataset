#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG068_ETFConsensusAnalysis — 主動式 ETF×共識分析(批264;操作員令)
====================================================================
操作員令:「via active etf analysis (with consensus data)」——把既有
ENG051 持股庫×ENG069/071 共識庫接成「分析成品」(非再一支擷取器=
Zero-Hydra:零網路零重抓,全讀在庫存證):
  ①每檔主動 ETF(最新 portfolio_date):
     持股數/共識覆蓋率(檔數+權重)/加權共識上漲空間
     (Σ w×upside ÷ Σ w,僅覆蓋檔;來源=consensus_latest 不跨源造數)
     /前十大持股×目標價中位×upside×分析師數
  ②跨 ETF 個股聚合:被幾檔 ETF 持有×權重合計×共識 upside
     →主動經理人共識重疊榜
  ③誠實界定:upside 缺=NULL 不入加權(分母只算有共識權重);
     共識未覆蓋=UNCOVERED 如實列計,不假 0
輸出:
  VIA_Reports/etf_consensus_analysis/ETF_CONSENSUS_<日>.json(存證)
  ui_support/VIA_UI_ETFConsensusAnalysis_v0100.html(手機單欄+
    內嵌 SVG 加權 upside 榜=VAP 視覺律零 CDN;Portal 尾版自收)
v0100→v0101(批273 操作員令「卡住 不卡斷」):唯讀連線三重試
(背景日更寫庫撞鎖=2s 退避;全敗=誠實停不懸吊)+run 入口
try 包=任何庫例外一句誠實訊息 rc2,零裸 traceback。
用法:python3 VDF_ENG068_ETFConsensusAnalysis_v0101.py run | probe
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
DB_ETF = (VDF / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings"
          / "ActiveTWETF.duckdb")
REP = VIA / "VIA_Reports" / "etf_consensus_analysis"
OUT_UI = (VIA / "supportive modules" / "ui_support"
          / "VIA_UI_ETFConsensusAnalysis_v0100.html")
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




def _consensus() -> dict:
    """code→共識(consensus_latest;每 code 雙源時取分析師數最多之
    單源列=去重律,平手依源名;來源分欄不跨源平均)"""
    c = _connect_ro(DB_TW)
    try:
        # 單位律(批264 實測):在庫 upside_pct 實為分數(0.333=+33.3%)
        # →庫端 ×100 統一為百分比,下游全域一致
        rows = c.execute(
            "SELECT code, source, target_median, upside_pct*100, "
            "n_analysts, close FROM consensus_latest "
            "QUALIFY ROW_NUMBER() OVER (PARTITION BY code "
            "ORDER BY n_analysts DESC NULLS LAST, source) = 1").fetchall()
    finally:
        c.close()
    return {r[0]: {"source": r[1], "tp": r[2], "upside": r[3],
                   "n": r[4], "close": r[5]} for r in rows}


def _holdings() -> tuple[str, list]:
    """最新 portfolio_date 全持股(欄名=ENG051 在庫原欄)"""
    e = _connect_ro(DB_ETF)
    try:
        d = e.execute("SELECT MAX(portfolio_date) FROM holdings_daily"
                      ).fetchone()[0]
        rows = e.execute(
            "SELECT etf_ticker, etf_name, holding_ticker, holding_name, "
            "weight_pct FROM holdings_daily WHERE portfolio_date=? "
            "ORDER BY etf_ticker, weight_pct DESC", [d]).fetchall()
    finally:
        e.close()
    return str(d), rows


def analyze() -> dict:
    con = _consensus()
    asof, rows = _holdings()
    etfs: dict = {}
    stocks: dict = {}
    for etf, ename, tick, hname, w in rows:
        w = float(w or 0)
        E = etfs.setdefault(etf, {"etf": etf, "name": ename, "n": 0,
                                  "w_all": 0.0, "n_cov": 0, "w_cov": 0.0,
                                  "wx": 0.0, "top": []})
        E["n"] += 1
        E["w_all"] += w
        c = con.get(tick)
        up = c["upside"] if c else None
        if c and up is not None:
            E["n_cov"] += 1
            E["w_cov"] += w
            E["wx"] += w * float(up)
        if len(E["top"]) < 10:
            E["top"].append({"code": tick, "name": hname, "w": round(w, 2),
                            "tp": c["tp"] if c else None,
                            "upside": round(float(up), 1)
                            if up is not None else None,
                            "n_analysts": c["n"] if c else None})
        S = stocks.setdefault(tick, {"code": tick, "name": hname,
                                     "etfs": 0, "w_sum": 0.0,
                                     "upside": round(float(up), 1)
                                     if up is not None else None,
                                     "tp": c["tp"] if c else None,
                                     "n_analysts": c["n"] if c else None})
        S["etfs"] += 1
        S["w_sum"] += w
    for E in etfs.values():
        E["w_all"] = round(E["w_all"], 2)
        E["w_cov"] = round(E["w_cov"], 2)
        E["cov_w_pct"] = round(100 * E["w_cov"] / E["w_all"], 1) \
            if E["w_all"] else 0.0
        E["wtd_upside"] = round(E["wx"] / E["w_cov"], 2) \
            if E["w_cov"] else None                 # 誠實:零覆蓋=None
        del E["wx"]
    for S in stocks.values():
        S["w_sum"] = round(S["w_sum"], 2)
    overlap = sorted(stocks.values(),
                     key=lambda s: (-s["etfs"], -s["w_sum"]))[:25]
    return {"asof": asof, "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "consensus_codes": len(con), "n_etfs": len(etfs),
            "etfs": sorted(etfs.values(),
                           key=lambda e: -(e["wtd_upside"]
                                           if e["wtd_upside"] is not None
                                           else -999)),
            "overlap": overlap}


def _svg_bar(etfs: list) -> str:
    """加權 upside 橫條(內嵌 SVG=VAP 視覺律零 CDN;缺值=灰誠實)"""
    rows = [e for e in etfs if e["wtd_upside"] is not None]
    if not rows:
        return "<p>共識覆蓋 0=誠實無圖</p>"
    mx = max(abs(e["wtd_upside"]) for e in rows) or 1
    h = 26 * len(rows) + 10
    parts = [f'<svg viewBox="0 0 640 {h}" role="img" '
             'style="width:100%;height:auto">']
    for i, e in enumerate(rows):
        y = 8 + i * 26
        bw = 300 * abs(e["wtd_upside"]) / mx
        col = "var(--green)" if e["wtd_upside"] >= 0 else "var(--red)"
        parts.append(
            f'<text x="0" y="{y + 13}" font-size="11" '
            f'fill="var(--text)">{html.escape(e["etf"])} '
            f'{html.escape(str(e["name"] or ""))[:8]}</text>'
            f'<rect x="200" y="{y}" width="{bw:.0f}" height="17" rx="3" '
            f'fill="{col}" opacity=".75"/>'
            f'<text x="{205 + bw:.0f}" y="{y + 13}" font-size="11" '
            f'fill="var(--text)">{e["wtd_upside"]:+.1f}%'
            f'(覆蓋 {e["cov_w_pct"]:.0f}%)</text>')
    parts.append("</svg>")
    return "".join(parts)


def render(d: dict) -> str:
    etf_rows = "".join(
        f"<tr><td>{html.escape(e['etf'])}<br><small>"
        f"{html.escape(str(e['name'] or ''))}</small></td>"
        f"<td>{e['n']}</td><td>{e['n_cov']}({e['cov_w_pct']}%)</td>"
        f"<td class='{'g' if (e['wtd_upside'] or 0) >= 0 else 'r'}'>"
        f"{'%+.2f%%' % e['wtd_upside'] if e['wtd_upside'] is not None else '—'}"
        "</td></tr>" for e in d["etfs"])
    ov_rows = "".join(
        f"<tr><td>{html.escape(s['code'])} "
        f"{html.escape(str(s['name'] or ''))}</td><td>{s['etfs']}</td>"
        f"<td>{s['w_sum']:.2f}</td>"
        f"<td>{'%+.1f%%' % s['upside'] if s['upside'] is not None else '未覆蓋'}"
        f"</td><td>{s['n_analysts'] or '—'}</td></tr>"
        for s in d["overlap"])
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 主動 ETF×共識分析</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--green:#5a9e6f;--red:#c96b5a}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--green:#79b58c;
--red:#d98a7c}}}}
body{{background:var(--bg);color:var(--text);margin:0;
font:13px/1.55 "Segoe UI","Noto Sans TC",sans-serif;padding:16px;
max-width:860px;margin:0 auto}}
h1{{font-size:16px}}h2{{font-size:12px;color:var(--muted);
text-transform:uppercase;letter-spacing:.08em;margin:18px 0 6px}}
.sub{{color:var(--muted);font-size:11px}}
table{{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:8px}}
td,th{{padding:6px 8px;border-bottom:1px solid var(--line);
text-align:left;font-variant-numeric:tabular-nums}}
th{{font-size:10.5px;color:var(--muted)}}
td.g{{color:var(--green);font-weight:600}}
td.r{{color:var(--red);font-weight:600}}
small{{color:var(--muted)}}
.wrap{{overflow-x:auto}}</style></head><body>
<h1>主動式 ETF×共識分析(批264)</h1>
<div class="sub">持股 asof {d['asof']} · 共識庫 {d['consensus_codes']} 檔 ·
{d['n_etfs']} 檔主動 ETF · 產於 {d['ts']} · 全讀在庫存證零網路 ·
加權 upside=Σw×upside÷Σw(僅共識覆蓋權重;未覆蓋誠實不入)</div>
<h2>加權共識上漲空間榜(SVG)</h2>{_svg_bar(d['etfs'])}
<h2>ETF 總表</h2><div class="wrap"><table><tr><th>ETF</th><th>持股</th>
<th>共識覆蓋</th><th>加權 upside</th></tr>{etf_rows}</table></div>
<h2>跨 ETF 共識重疊榜(前 25)</h2><div class="wrap"><table>
<tr><th>個股</th><th>被持 ETF 數</th><th>權重合計</th><th>共識 upside</th>
<th>分析師</th></tr>{ov_rows}</table></div>
<p class="sub">來源:ENG051 holdings_daily × consensus_latest(ENG069/071
入庫)· 來源分欄不跨源平均 · 非投資建議</p></body></html>"""


def probe() -> int:
    print(f"  [{'OK' if DB_TW.exists() else 'FAIL'}] 台股庫 {DB_TW.name}")
    print(f"  [{'OK' if DB_ETF.exists() else 'FAIL'}] ETF 庫 {DB_ETF.name}")
    return 0 if DB_TW.exists() and DB_ETF.exists() else 2


def run() -> int:
    if not (DB_TW.exists() and DB_ETF.exists()):
        print("[ETF共識] 在庫來源缺=誠實停(先跑 boot/backfill)")
        return 2
    try:
        d = analyze()
    except Exception as exc:
        print(f"[分析] 庫忙/例外=誠實停({type(exc).__name__}):"
              "背景日更寫庫中,稍後再跑 via-analysis 即通")
        return 2
    REP.mkdir(parents=True, exist_ok=True)
    j = REP / f"ETF_CONSENSUS_{d['asof'].replace('-', '')}.json"
    j.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    OUT_UI.write_text(render(d), encoding="utf-8")
    cov = [e for e in d["etfs"] if e["wtd_upside"] is not None]
    print(f"[ETF共識] {d['n_etfs']} 檔 ETF · 共識可加權 {len(cov)} 檔 · "
          f"asof {d['asof']} · {j.name} + {OUT_UI.name}")
    for e in cov[:3]:
        print(f"  [榜] {e['etf']} {e['name']} 加權 upside "
              f"{e['wtd_upside']:+.2f}%(覆蓋 {e['cov_w_pct']}%)")
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
    chk("① 在庫雙源接通(holdings×consensus;零網路)", rc == 0
        and d.get("n_etfs", 0) > 0 and d.get("consensus_codes", 0) > 0)
    cov = [e for e in d.get("etfs", []) if e["wtd_upside"] is not None]
    chk("② 加權律=僅覆蓋權重入分母(w_cov>0 才有值)",
        all(e["w_cov"] > 0 for e in cov) and len(cov) > 0)
    E = cov[0] if cov else None
    manual = None
    if E:
        con = _consensus()
        _, rows = _holdings()
        wx = wc = 0.0
        for etf, _, t, _, w in rows:
            if etf == E["etf"] and t in con \
                    and con[t]["upside"] is not None:
                wx += float(w) * float(con[t]["upside"])
                wc += float(w)
        manual = round(wx / wc, 2) if wc else None
    chk("③ 加權值可複算(手算=引擎值)", E is not None
        and manual == E["wtd_upside"], f"({manual})")
    chk("④ 重疊榜真聚合(首檔被持 ETF 數≥2)",
        bool(d.get("overlap")) and d["overlap"][0]["etfs"] >= 2)
    page = OUT_UI.read_text(encoding="utf-8") if OUT_UI.exists() else ""
    chk("⑤ U/I 頁產出(單欄+SVG 榜+零 CDN)",
        "主動式 ETF×共識分析" in page and "<svg" in page
        and 'src="http' not in page)
    chk("⑥ 零網路+加速橋+誠實界定宣告", "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src
                for k in ("requests", "httpx", "urllib"))
        and "誠實" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 主動 ETF×共識分析(VDF_ENG068)· 六檢自測(零網路)===")
        return selftest()
    if "probe" in a:
        return probe()
    return run()


if __name__ == "__main__":
    sys.exit(main())


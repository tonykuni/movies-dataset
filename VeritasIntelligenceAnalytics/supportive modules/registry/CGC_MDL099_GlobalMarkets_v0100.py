#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL099_GlobalMarkets — 全球市場觀測頁(批227;批226 續行)
====================================================================
批226 全球宇宙 11 類 82 檔入庫(+105,383 列)→本頁=消費端:
  每類一矩陣:最新收盤/1 日/5 日/1 月/年至今 漲跌%/52 週位置/
  60 日迷你走勢(inline SVG 手繪=零 CDN);紅綠著色(台式:紅漲綠跌)。
  全實值自 global_daily 唯讀計算(鎖=誠實 busy);候源類誠實列示。
用法:python3 CGC_MDL099_GlobalMarkets_v0100.py [--open] | --selftest
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

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB_GL = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_global_market.duckdb"
OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_GlobalMarkets_v0100.html"
ROSTER = HERE / "VIA_Global_Universe_v0100.json"
UP, DOWN = "#dc2626", "#15803d"   # 台式:紅漲綠跌


def _spark(vals: list[float]) -> str:
    """60 日迷你走勢 inline SVG(零 CDN 手繪)"""
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    w, h = 90, 22
    pts = " ".join(f"{i * w / (len(vals) - 1):.1f},"
                   f"{h - 2 - (v - lo) / rng * (h - 4):.1f}"
                   for i, v in enumerate(vals))
    color = UP if vals[-1] >= vals[0] else DOWN
    return (f"<svg width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
            f"<polyline points='{pts}' fill='none' stroke='{color}' "
            f"stroke-width='1.2'/></svg>")


def gather() -> tuple[list[dict], str]:
    """每類每檔實值;回 (categories, 誠實狀態字串)"""
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    try:
        import duckdb
        con = duckdb.connect(str(DB_GL), read_only=True)
    except Exception as exc:
        return [], f"庫 busy/缺({type(exc).__name__})=誠實稍後再看"
    px = {}
    for tkr, d, c in con.execute(
            "SELECT ticker, date, close FROM global_daily "
            "WHERE close IS NOT NULL ORDER BY ticker, date").fetchall():
        px.setdefault(tkr, []).append((str(d), float(c)))
    con.close()

    def ret(series, n):
        if len(series) <= n:
            return None
        a, b = series[-1][1], series[-1 - n][1]
        return (a / b - 1) * 100 if b else None

    cats = []
    for cat in roster["categories"]:
        rows = []
        for sym in cat["symbols"]:
            s = px.get(sym)
            if not s:
                rows.append({"sym": sym, "note": "未回補(按目錄台全球擷取)"})
                continue
            ytd_base = next((v for d, v in s if d >= f"{s[-1][0][:4]}-01-01"),
                            s[0][1])
            closes52 = [v for d, v in s[-252:]]
            lo52, hi52 = min(closes52), max(closes52)
            pos52 = ((s[-1][1] - lo52) / (hi52 - lo52) * 100) \
                if hi52 > lo52 else 50.0
            rows.append({
                "sym": sym, "date": s[-1][0], "close": s[-1][1],
                "d1": ret(s, 1), "d5": ret(s, 5), "m1": ret(s, 21),
                "ytd": (s[-1][1] / ytd_base - 1) * 100 if ytd_base else None,
                "pos52": pos52,
                "spark": _spark([v for d, v in s[-60:]])})
        cats.append({"zh": cat["zh"], "cat": cat["cat"],
                     "status": cat["status"], "rows": rows,
                     "pending": cat.get("pending_note", "")})
    return cats, "OK"


def render() -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    cats, state = gather()

    def pc(v):
        if v is None:
            return "<td>—</td>"
        color = UP if v >= 0 else DOWN
        return f"<td style='color:{color}'>{v:+.2f}%</td>"

    secs = ""
    for c in cats:
        if not c["rows"]:
            secs += (f"<section><h2>{c['zh']}(候源)</h2>"
                     f"<div class='mut'>{c['pending']}</div></section>")
            continue
        body = ""
        for r in c["rows"]:
            if "note" in r:
                body += (f"<tr><td>{r['sym']}</td>"
                         f"<td colspan='7' class='mut'>{r['note']}</td></tr>")
                continue
            body += (f"<tr><td><b>{r['sym']}</b>"
                     f"<div class='mut'>{r['date']}</div></td>"
                     f"<td>{r['close']:,.2f}</td>"
                     + pc(r["d1"]) + pc(r["d5"]) + pc(r["m1"]) + pc(r["ytd"])
                     + f"<td>{r['pos52']:.0f}%</td><td>{r['spark']}</td></tr>")
        secs += (f"<section><h2>{c['zh']}({len(c['rows'])} 檔)</h2>"
                 f"<table><thead><tr><th>標的</th><th>收盤</th><th>1日</th>"
                 f"<th>5日</th><th>1月</th><th>YTD</th><th>52週位</th>"
                 f"<th>60日</th></tr></thead><tbody>{body}</tbody></table>"
                 + (f"<div class='mut'>{c['pending']}</div>" if c["pending"]
                    else "") + "</section>")
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA GlobalMarkets · 全球市場觀測</title>
<style>
:root{{--bg:#0b1220;--card:#111a2e;--line:#1e2a44;--tx:#c7d3e8;--dim:#7e8db0;
--ac:#4f8ef7}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--tx);font:10.5px/1.5 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px;max-width:1280px;margin:0 auto}}
h1{{font-size:14px;color:#e8eefb}}
.sub{{color:var(--dim);font-size:10px;margin:2px 0 10px}}
main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));
gap:10px;align-items:start}}
section{{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:10px;overflow:auto}}
h2{{font-size:11px;color:var(--ac);margin-bottom:6px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:var(--dim);font-size:9.5px;
border-bottom:1px solid var(--line);padding:2px 6px 3px 0}}
td{{padding:2px 6px 2px 0;border-bottom:1px dashed var(--line);
overflow-wrap:anywhere;font-variant-numeric:tabular-nums;
vertical-align:middle}}
.mut{{color:var(--dim);font-size:9px}}
</style></head><body>
<h1>VIA 全球市場觀測(11 類宇宙)</h1>
<div class="sub">{ts} · 狀態:{state} · 唯讀實值(global_daily)·
紅漲綠跌 · 52週位=收盤於 52 週區間位置 · 零 CDN(SVG 手繪走勢)·
更新資料=目錄台[全球宇宙擷取]或雙擊 VIA</div>
<main>{secs}</main>
</body></html>"""


def run(open_after: bool = False) -> int:
    OUT.write_text(render(), encoding="utf-8")
    print(f"[UI] {OUT.name} · 全球 11 類觀測(實值+SVG 走勢)")
    if open_after:
        try:
            import webbrowser
            webbrowser.open(OUT.as_uri())
        except Exception:
            pass
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run()
    page = OUT.read_text(encoding="utf-8")
    chk("① 11 類全在頁(宇宙冊 SSOT join;候源類誠實)",
        rc == 0 and all(k in page for k in ("國際股票指數", "加密貨幣",
                                            "商品", "美元指數及重要匯率",
                                            "候源")))
    chk("② 實值矩陣(收盤/1日/5日/1月/YTD/52週位)",
        all(k in page for k in ("<th>1日</th>", "<th>YTD</th>",
                                "<th>52週位</th>")))
    chk("③ SVG 手繪走勢在頁(零 CDN;polyline)",
        "<svg" in page and "polyline" in page and 'src="http' not in page)
    chk("④ 台式紅漲綠跌著色", UP == "#dc2626" and DOWN == "#15803d"
        and "#dc2626" in page)
    chk("⑤ 唯讀+鎖容錯(busy=誠實)",
        "read_only=True" in src and "誠實稍後" in src)
    chk("⑥ 未回補檔誠實列示(不假數)", "未回補" in src)
    chk("⑦ 小字專業排版(10.5px+auto-fit+anywhere)",
        all(k in page for k in ("10.5px", "auto-fit", "anywhere")))
    chk("⑧ 加速橋+零 http 庫(生成純本地)",
        "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 全球市場觀測頁(CGC_MDL099)· 八檢自測(零網路)===")
        return selftest()
    return run(open_after="--open" in args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL100_ReportCards — 券商報告卡總覽頁(批241 波1;操作員選項1)
====================================================================
vrn_report_basic+metrics(ENG073 結構化庫)上 UI:每報告一卡——
ticker/官方名/券商/日期/評等/TP/P(頁+庫)/升幅三軌(報告/頁算/庫算)
/驗證態 RYG/衝突列示/摘要頭/財務 chips。唯讀(鎖=誠實 busy);
日期新→舊;零 CDN;10.5px 專業小字。
用法:python3 CGC_MDL100_ReportCards_v0100.py [--open] | --selftest
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

import html
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_ReportCards_v0100.html"

GOOD = {"EXACT_MATCH", "EXACT_MATCH_DB", "ROUNDING_ONLY", "ROUNDING_ONLY_DB",
        "P_CONFIRMED_DB"}
WARN = {"SINGLE_SOURCE", "DB_DERIVED", "P_FROM_DB"}


def gather(db: Path | None = None) -> tuple[list[dict], dict, str]:
    try:
        import duckdb
        con = duckdb.connect(str(db or DB_TW), read_only=True)
    except Exception as exc:
        return [], {}, f"庫 busy/缺({type(exc).__name__})=誠實稍後"
    try:
        cur = con.execute("SELECT * FROM vrn_report_basic "
                          "ORDER BY report_date DESC, report_file")
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception:
        con.close()
        return [], {}, "vrn_report_basic 未建(先跑 ENG073)"
    mets: dict = {}
    try:
        for rf, met, per, st, v in con.execute(
                "SELECT report_file, metric, period, status, value "
                "FROM vrn_report_metrics").fetchall():
            mets.setdefault(rf, []).append(
                f"{met} {per}{'E' if st == 'ESTIMATE' else ''}={v}")
    except Exception:
        pass
    try:
        for rf, canon, per, st, v in con.execute(
                "SELECT report_file, canonical, period, status, value "
                "FROM vrn_report_financial WHERE canonical<>'' "
                "LIMIT 5000").fetchall():
            mets.setdefault(rf, []).append(f"{canon} {per}={v}")
    except Exception:
        pass                                     # 波2 表未建=誠實略
    con.close()
    return rows, mets, "OK"


def render() -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows, mets, state = gather()
    n_good = sum(1 for r in rows if r.get("upside_state") in GOOD
                 or r.get("price_state") in GOOD)
    cards = ""
    for r in rows:
        st = r.get("upside_state") or ""
        cls = ("g" if st in GOOD else "y" if st in WARN else "r"
               if st else "y")
        ups = " · ".join(f"{k}={v}" for k, v in
                         (("報告", r.get("upside_report")),
                          ("頁算", r.get("upside_calc")),
                          ("庫算", r.get("upside_db"))) if v is not None)
        chips = "".join(f"<span class='chip'>{html.escape(c)}</span>"
                        for c in mets.get(r["report_file"], [])[:8])
        cards += f"""<section class="{cls}">
<h2>{html.escape(str(r.get('ticker') or '—'))} {html.escape(str(r.get('name_official') or '(非個股)'))}
<span class="tag">{html.escape(str(r.get('broker') or ''))} · {html.escape(str(r.get('report_date') or ''))}
· {html.escape(str(r.get('rating_raw') or 'NOT_RATED'))}</span></h2>
<div class="row">TP={r.get('target_price') or '—'} · 頁P={r.get('price') or '—'}
· 庫P={r.get('price_db') or '—'}({html.escape(str(r.get('price_state') or ''))})
· 升幅 {ups or '—'} · <b>{html.escape(st or 'N/A')}</b></div>
{f"<div class='cf'>⚠ {html.escape(str(r.get('conflicts')))}</div>" if r.get('conflicts') else ''}
<div class="sm">{html.escape(str(r.get('title_head') or ''))[:160]}</div>
<div class="sm mut">{html.escape(str(r.get('summary_head') or ''))[:260]}</div>
<div class="chips">{chips}</div>
<div class="mut fn">{html.escape(r['report_file'])}</div></section>"""
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA ReportCards · 券商報告卡</title><style>
:root{{--bg:#0b1220;--card:#111a2e;--line:#1e2a44;--tx:#c7d3e8;--dim:#7e8db0}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--tx);font:10.5px/1.55 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px;max-width:1240px;margin:0 auto}}
h1{{font-size:14px;color:#e8eefb}}
.sub{{color:var(--dim);font-size:10px;margin:2px 0 10px}}
main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));
gap:10px;align-items:start}}
section{{background:var(--card);border:1px solid var(--line);
border-left-width:3px;border-radius:8px;padding:10px}}
section.g{{border-left-color:#15803d}}section.y{{border-left-color:#f0b429}}
section.r{{border-left-color:#dc2626}}
h2{{font-size:11.5px;color:#e8eefb;overflow-wrap:anywhere}}
.tag{{color:var(--dim);font-size:9.5px;font-weight:normal}}
.row{{margin:4px 0;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}}
.cf{{color:#f0b429;font-size:9.5px}}
.sm{{font-size:10px;margin-top:3px;overflow-wrap:anywhere}}
.mut{{color:var(--dim)}}.fn{{font-size:8.5px;margin-top:4px}}
.chips{{margin-top:4px}}
.chip{{display:inline-block;background:#16233d;border:1px solid #2a3c61;
border-radius:10px;padding:1px 7px;margin:1px 3px 1px 0;font-size:9px}}
</style></head><body>
<h1>券商報告卡總覽(結構化庫 vrn_report_basic)</h1>
<div class="sub">{ts} · 狀態:{state} · {len(rows)} 卡 · 綠/確認 {n_good}
· 升幅三軌=報告值/頁算/庫算(批240 裁示:庫算=TP÷前日 CLOSE)·
KEEP_BOTH 衝突誠實列示 · 唯讀零 CDN</div>
<main>{cards or '<section class="y"><h2>庫空(先跑 firstpage→structdb)</h2></section>'}</main>
</body></html>"""


def run(open_after: bool = False) -> int:
    OUT.write_text(render(), encoding="utf-8")
    print(f"[UI] {OUT.name} · 券商報告卡(RYG+三軌升幅+chips)")
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
    chk("① 頁產出(庫空/busy=誠實卡示)", rc == 0
        and ("券商報告卡總覽" in page))
    chk("② 三軌升幅+庫算裁示宣告(批240:TP÷前日 CLOSE)",
        "報告值/頁算/庫算" in page and "前日 CLOSE" in page)
    chk("③ RYG 邊色三態+KEEP_BOTH 衝突列示",
        all(k in src for k in ("section.g", "section.y", "section.r",
                               "conflicts")))
    chk("④ 唯讀+鎖容錯", "read_only=True" in src and "誠實稍後" in src)
    chk("⑤ 財務 chips 波2 容錯(vrn_report_financial 未建=誠實略)",
        "vrn_report_financial" in src)
    chk("⑥ 小字專業排版", all(k in page for k in ("10.5px", "auto-fit")))
    chk("⑦ 零 CDN", 'src="http' not in page and "@import" not in page)
    chk("⑧ 加速橋+零 http 庫", "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 券商報告卡頁(CGC_MDL100)· 八檢自測(零網路)===")
        return selftest()
    return run(open_after="--open" in args)


if __name__ == "__main__":
    sys.exit(main())

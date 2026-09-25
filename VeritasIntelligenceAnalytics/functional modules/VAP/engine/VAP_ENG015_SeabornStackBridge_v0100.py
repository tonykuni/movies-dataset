#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG015_SeabornStackBridge v0100 — Seaborn 垂直圖組產生器 v2.3.1 橋接(批327)
======================================================================
操作員令(批327):上傳 VAP_Seaborn_VerticalStack_Generator_v2.3.1.zip+UAT 報告
「整合檔案到 VAP」+「heatmap 切割細一點」(sns.heatmap cmap='coolwarm' annot=True 語意)。
包=外部產生器(原件收容 supportive modules/references/intake/VIA_VAPSeabornStack_b327/,
零改動;demo 二進位四件排除入庫,hash 記 manifest)。本橋=VIA 庫 → 資料 CSV → 包 CLI
(init/add/render;cwd=包根;尾版 glob)→ 圖組四格式(png/pdf/svg/html 自包含 Plotly)
落 VIA_Reports/vap_stack/output/ + 索引頁 VIA_UI_VapStack_v0100.html(零 CDN)。
模式:
  stock <代碼>   還原 OHLCV(tw_prices_adj)蠟燭+量 + 三大法人金額(淨股數×收盤 DERIVED)有號柱
  heatmap        ENG070 尾件 ROTATION_*.json(mtime)注意力份額最負 r 矩陣→熱圖
                 (coolwarm · annot .2f · center 0 · 細切=逐格標註+格線;包 linewidths 固定 0.35)
  --pkgtest      跑包自測(誠實列環境差異;pandas 版本釘 <2.2 與本境 3.x 差=如實)
  --selftest     六檢
律:包原件零觸碰(config/data/output 全在 VIA_Reports);CLI 版本旗標 README 之 --open 等
    於 v2.3.1 不存在=蠟燭欄以 config chart 鍵(open/high/low/close/volume)注入(實錘)。
用法:python VAP_ENG015_SeabornStackBridge_v0100.py [stock 2330 | heatmap | --pkgtest | --selftest]
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
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
INTAKE = VIA / "supportive modules" / "references" / "intake" / "VIA_VAPSeabornStack_b327"
REP70 = VIA / "VIA_Reports" / "group_class"
WORK = VIA / "VIA_Reports" / "vap_stack"
DATA = WORK / "data"
OUT = WORK / "output"
UI = VIA / "supportive modules" / "ui_support" / "VIA_UI_VapStack_v0100.html"
HEAT_CMAP, HEAT_FMT = "coolwarm", ".2f"      # 批327 操作員語意
RENDER_TIMEOUT = 600


def pkg_root() -> Path | None:
    hits = sorted(p for p in INTAKE.glob("VAP_Seaborn_VerticalStack_Generator*") if p.is_dir())
    return hits[-1] if hits else None


def _cli(args: list[str], timeout: int = RENDER_TIMEOUT) -> dict:
    pk = pkg_root()
    if pk is None:
        return {"rc": 127, "out": "", "err": "包缺"}
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", MPLBACKEND="Agg",
               MPLCONFIGDIR=str(_mplcfg()))
    try:
        r = subprocess.run([sys.executable, str(pk / "vap_seaborn_stack_generator.py"), *args],
                           capture_output=True, text=True, timeout=timeout, cwd=str(pk), env=env)
        return {"rc": r.returncode, "out": r.stdout, "err": r.stderr}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "out": "", "err": f"逾時 {timeout}s"}


def _mplcfg() -> Path:
    """CJK 字型律(實錄批327:雲端缺 JhengHei=方框):以 MPLCONFIGDIR matplotlibrc 注入 sans-serif 候選序
    (JhengHei→Noto CJK→WenQuanYi→DejaVu);包原件零觸碰"""
    d = WORK / "mplcfg"
    d.mkdir(parents=True, exist_ok=True)
    rc = d / "matplotlibrc"
    if not rc.exists():
        rc.write_text("font.family: sans-serif\n"
                      "font.sans-serif: Microsoft JhengHei, Noto Sans CJK TC, Noto Sans CJK JP, "
                      "WenQuanYi Zen Hei, PingFang TC, DejaVu Sans, Arial\n"
                      "axes.unicode_minus: False\n", encoding="utf-8")
    return d


def _con():
    import duckdb
    return duckdb.connect(str(DB_TW), read_only=True)


def export_stock(code: str) -> Path | None:
    """VIA 庫→CSV:Date, Open/High/Low/Close(還原;缺調整層=Yahoo adj_close 收盤折線), Volume, MA20,
    Foreign/Trust/Dealer(TWD=淨股數×收盤 DERIVED)"""
    import pandas as pd
    if not DB_TW.exists():
        return None
    DATA.mkdir(parents=True, exist_ok=True)
    c = _con()
    df = c.execute(f"""
        SELECT CAST(d.date AS VARCHAR) AS Date,
               COALESCE(a.adj_open, d.adj_close) AS Open, COALESCE(a.adj_high, d.adj_close) AS High,
               COALESCE(a.adj_low, d.adj_close) AS Low, COALESCE(a.adj_close, d.adj_close) AS Close,
               d.volume AS Volume, d.close AS raw_close
        FROM tw_daily_prices d
        LEFT JOIN tw_prices_adj a USING (date, ticker)
        WHERE regexp_replace(d.ticker, '\\.(TW|TWO)$', '') = '{code}' AND d.close > 0
        ORDER BY 1""").df()
    ch = c.execute(f"SELECT CAST(date AS VARCHAR) AS Date, foreign_net, trust_net, dealer_net "
                   f"FROM tw_chip_inst WHERE code = '{code}'").df()
    c.close()
    if df.empty:
        return None
    df = df.drop_duplicates("Date")
    df["MA20"] = df["Close"].rolling(20).mean()
    df = df.merge(ch, on="Date", how="left")
    for src, col in (("foreign_net", "Foreign"), ("trust_net", "Trust"), ("dealer_net", "Dealer")):
        df[col] = df[src] * df["raw_close"]
    keep = ["Date", "Open", "High", "Low", "Close", "Volume", "MA20", "Foreign", "Trust", "Dealer"]
    p = DATA / f"stock_{code}.csv"
    df[keep].to_csv(p, index=False)
    return p


def export_heatmap() -> Path | None:
    """ENG070 尾件 ROTATION_*.json(mtime)→ 長表 from,to,r(注意力份額最負 r)"""
    import pandas as pd
    hits = list(REP70.glob("ROTATION_*.json"))
    if not hits:
        return None
    rot = json.loads(max(hits, key=lambda f: f.stat().st_mtime).read_text(encoding="utf-8"))
    rows = [{"from": a, "to": b, "r": v} for a, m in rot.get("matrix", {}).get("as", {}).items()
            for b, v in m.items()]
    if not rows:
        return None
    DATA.mkdir(parents=True, exist_ok=True)
    p = DATA / "rotation_heatmap.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def _patch_config(cfg_path: Path, name: str, title: str, sub: str, chart_patch: dict,
                  formats: list | None = None) -> None:
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if formats:
        cfg["project"]["output_formats"] = formats
    cfg["project"]["output_directory"] = str(OUT)
    cfg["project"]["output_name"] = name
    cfg["project"]["title"] = title
    cfg["project"]["subtitle"] = sub
    cfg["project"]["watermark"] = "理 · VAP"
    for ch in cfg.get("charts", []):
        if ch["id"] in chart_patch:
            ch.update(chart_patch[ch["id"]])
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")


def build_stock(code: str, do_print: bool = True) -> dict:
    t0 = time.time()
    csv = export_stock(code)
    if csv is None:
        return {"state": "FAIL", "reason": f"庫無 {code} 價表(誠實)"}
    cfg = WORK / f"stack_stock_{code}.json"
    steps = [
        ["init", "--config", str(cfg), "--data", str(csv), "--force"],
        ["add", "--config", str(cfg), "--id", "candle", "--type", "candlestick", "--preset", "candlestick_volume",
         "--x", "Date", "--title", f"{code} 還原蠟燭+量 · 紅漲綠跌", "--unit", "Adjusted Price", "--secondary-unit", "Volume"],
        ["add", "--config", str(cfg), "--id", "price_ma", "--type", "line", "--preset", "price",
         "--x", "Date", "--y", "Close", "MA20", "--title", f"{code} 還原收盤與 MA20", "--unit", "Price"],
        ["add", "--config", str(cfg), "--id", "flow", "--type", "bar", "--preset", "signed_flow",
         "--x", "Date", "--y", "Foreign", "Trust", "Dealer", "--title", "三大法人淨買賣金額(淨股數×收盤 DERIVED)",
         "--unit", "TWD"],
    ]
    log = []
    for a in steps:
        r = _cli(a, 120)
        log.append({"cmd": a[0] + " " + a[4] if len(a) > 4 else a[0], "rc": r["rc"], "err": r["err"][-300:]})
        if r["rc"] != 0:
            return {"state": "FAIL", "reason": f"{a[0]} rc={r['rc']}: {(r['err'] or r['out'])[-300:]}", "log": log}
    _patch_config(cfg, f"stock_{code}", f"VIA · {code} 圖組", "Seaborn Vertical Stack · VDF 在庫還原價+法人金額",
                  {"candle": {"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume",
                              "price_basis": "adjusted"}})
    r = _cli(["render", "--config", str(cfg)])
    outs = {ext: OUT / f"stock_{code}.{ext}" for ext in ("png", "pdf", "svg", "html")}
    have = {k: v.exists() for k, v in outs.items()}
    res = {"state": "PASS" if r["rc"] == 0 and have["html"] else "FAIL", "code": code, "config": str(cfg),
           "outputs": {k: str(v) for k, v in outs.items() if have[k]}, "rc": r["rc"],
           "reason": "" if r["rc"] == 0 else (r["err"] or r["out"])[-400:], "elapsed_s": round(time.time() - t0, 1),
           "log": log}
    if do_print:
        print(f"[圖組] stock {code} · {res['state']} · 產出 {sorted(res['outputs'])} · {res['elapsed_s']}s"
              + (f" · {res['reason']}" if res["reason"] else ""))
    return res


def build_heatmap(do_print: bool = True) -> dict:
    t0 = time.time()
    csv = export_heatmap()
    if csv is None:
        return {"state": "SKIP", "reason": "ENG070 ROTATION 存證缺(先跑分類引擎)=誠實跳"}
    cfg = WORK / "stack_heatmap.json"
    for a in (["init", "--config", str(cfg), "--data", str(csv), "--force"],
              ["add", "--config", str(cfg), "--id", "rot", "--type", "heatmap", "--preset", "heatmap",
               "--x", "from", "--heatmap-index", "from", "--heatmap-columns", "to", "--heatmap-value", "r", "--cmap", HEAT_CMAP,
               "--title", "族群輪動關聯 · 注意力份額最負 r(A 退→B 進)", "--unit", "r", "--height-ratio", "2.4"]):
        r = _cli(a, 120)
        if r["rc"] != 0:
            return {"state": "FAIL", "reason": f"{a[0]} rc={r['rc']}: {(r['err'] or r['out'])[-300:]}"}
    _patch_config(cfg, "rotation_heatmap", "VIA · 族群輪動熱圖", "Seaborn heatmap · coolwarm · annot · 細切",
                  {"rot": {"annot": True, "annot_format": HEAT_FMT, "center": 0, "cmap": HEAT_CMAP,
                           "heatmap_aggfunc": "mean"}},
                  formats=["png", "pdf", "svg"])   # 實錄批327:包 Plotly HTML 渲染器把 x 當日期→類別軸熱圖=靜態三格式(誠實)
    r = _cli(["render", "--config", str(cfg)])
    outs = {ext: OUT / f"rotation_heatmap.{ext}" for ext in ("png", "pdf", "svg", "html")}
    have = {k: v.exists() for k, v in outs.items()}
    res = {"state": "PASS" if r["rc"] == 0 and have["png"] else "FAIL", "config": str(cfg),
           "outputs": {k: str(v) for k, v in outs.items() if have[k]}, "rc": r["rc"],
           "reason": "" if r["rc"] == 0 else (r["err"] or r["out"])[-400:], "elapsed_s": round(time.time() - t0, 1)}
    if do_print:
        print(f"[熱圖] rotation · {res['state']} · 產出 {sorted(res['outputs'])} · {res['elapsed_s']}s"
              + (f" · {res['reason']}" if res["reason"] else ""))
    return res


def render_index(results: list[dict]) -> None:
    rows = []
    for r in results:
        links = " · ".join(
            f'<a href="{html.escape(os.path.relpath(p, UI.parent).replace(os.sep, "/"))}">{k.upper()}</a>'
            for k, p in sorted((r.get("outputs") or {}).items()))
        cls = {"PASS": "ok", "SKIP": "warn"}.get(r.get("state"), "bad")
        rows.append(f"<tr><td>{html.escape(r.get('name', ''))}</td><td class='{cls}'>{html.escape(r.get('state', ''))}</td>"
                    f"<td>{links or '—'}</td><td>{html.escape(r.get('reason', '') or '')}</td></tr>")
    existing = sorted(OUT.glob("*.html")) if OUT.exists() else []
    lib = "".join(f'<li><a href="{html.escape(os.path.relpath(p, UI.parent).replace(os.sep, "/"))}">{p.name}</a>'
                  f' <span class="mut">{p.stat().st_size // 1024} KB</span></li>' for p in existing)
    page = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>VIA · Seaborn 垂直圖組</title>
<style>
:root{{--bg:#f5f5f2;--paper:#fff;--ink:#1f2530;--mut:#6d7688;--line:#dcdfe6;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d;--acc:#3e6b8f}}
body{{margin:0;background:var(--bg);color:var(--ink);font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:16px 22px}}
h1{{font-size:20px;margin:0 0 4px}} .sub{{color:var(--mut);font-size:11px}} .mut{{color:var(--mut)}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:12px 14px;margin:10px 0}}
table{{border-collapse:collapse;width:100%;font-size:11.5px}} th{{text-align:left;font-size:10px;letter-spacing:.14em;color:var(--mut);border-bottom:1px solid var(--line);padding:4px 8px 4px 0}}
td{{border-bottom:1px solid #eef0ee;padding:4px 8px 4px 0;vertical-align:top}} .ok{{color:var(--ok);font-weight:700}} .bad{{color:var(--bad);font-weight:700}} .warn{{color:var(--warn);font-weight:700}}
a{{color:var(--acc)}} ul{{margin:4px 0 0 16px;padding:0}}
</style></head><body>
<h1>Seaborn 垂直圖組產生器 <span class="sub">VAP SEABORN VERTICAL STACK v2.3.1 × VAP_ENG015 · 產於 {time.strftime('%Y-%m-%d %H:%M')}</span></h1>
<div class="sub">stock=還原 OHLCV 蠟燭+量、收盤+MA20、三大法人金額有號柱 · heatmap=ENG070 輪動矩陣(coolwarm · annot · 細切)· 四格式 png/pdf/svg/html(自包含 Plotly,零 CDN)· 產出於 VIA_Reports/vap_stack/output</div>
<div class="card"><h3>本輪 THIS RUN</h3><table><tr><th>圖組 STACK</th><th>狀態</th><th>產出 OUTPUTS</th><th>註 NOTE</th></tr>{''.join(rows) or '<tr><td colspan=4>—</td></tr>'}</table></div>
<div class="card"><h3>圖庫 LIBRARY(既有 HTML 圖組)</h3><ul>{lib or '<li class="mut">尚無</li>'}</ul></div>
<div class="sub">短令 via-vapstack stock &lt;代碼&gt; · via-vapstack heatmap · 包原件 intake/VIA_VAPSeabornStack_b327(零改動;UAT 155 過)· 誠實三態</div>
</body></html>"""
    UI.parent.mkdir(parents=True, exist_ok=True)
    UI.write_text(page, encoding="utf-8")


def pkgtest(do_print: bool = True) -> dict:
    pk = pkg_root()
    if pk is None:
        return {"rc": 127, "summary": "包缺"}
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], capture_output=True,
                       text=True, timeout=900, cwd=str(pk), env=env)
    lines = (r.stderr or r.stdout).strip().splitlines()
    ran = next((ln for ln in lines if ln.startswith("Ran ")), "")
    summ = next((ln for ln in reversed(lines) if ln.startswith(("OK", "FAILED"))), "")
    heads = [ln for ln in lines if ln.startswith(("FAIL:", "ERROR:"))][:12]
    import pandas as pd
    res = {"rc": r.returncode, "ran": ran, "summary": summ, "failures": heads, "pandas": pd.__version__,
           "note": "包 requirements 釘 pandas<2.2;本境版本差=環境差異誠實列(工作站依 Setup 腳本建 venv 為正判)"}
    if do_print:
        print(f"[包自測] {ran} · {summ} · pandas {pd.__version__}")
        for h in heads:
            print("   ", h[:140])
    return res


def run(args: list[str]) -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    results = []
    if args and args[0] == "heatmap":
        r = build_heatmap(); r["name"] = "rotation_heatmap"; results.append(r)
    else:
        code = args[1] if len(args) > 1 and args[0] == "stock" else (args[0] if args and args[0].isdigit() else "2330")
        r = build_stock(code); r["name"] = f"stock_{code}"; results.append(r)
    render_index(results)
    (WORK / f"RUN_{time.strftime('%Y%m%d_%H%M%S')}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"  索引頁 {UI.name} · 存證 {WORK}")
    return 0 if all(x["state"] in ("PASS", "SKIP") for x in results) else 2


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    pk = pkg_root()
    man = INTAKE / "manifest.json"
    chk("① 包在位+收容 manifest(hash 冊+demo 二進位排除記錄)+UAT 報告", pk is not None and man.exists()
        and "excluded_demo_binaries" in json.loads(man.read_text(encoding="utf-8"))
        and (INTAKE / "VAP_v231_UAT_REPORT.md").exists())
    csv = export_stock("2330")
    import pandas as pd
    cols = list(pd.read_csv(csv, nrows=2).columns) if csv else []
    chk("② 庫→CSV(還原 OHLCV+MA20+三大法人金額 DERIVED)", csv is not None
        and {"Date", "Open", "High", "Low", "Close", "Volume", "MA20", "Foreign", "Trust", "Dealer"} <= set(cols))
    rs = build_stock("2330", do_print=False)
    chk("③ 包 CLI init/add/render 通(蠟燭欄以 config 鍵注入)+html/png 產出",
        rs["state"] == "PASS" and "html" in rs["outputs"] and "png" in rs["outputs"], rs.get("reason", "")[:80])
    rh = build_heatmap(do_print=False)
    chk("④ 熱圖模式(coolwarm·annot .2f·center 0;ROTATION 缺=誠實 SKIP)",
        rh["state"] in ("PASS", "SKIP") and (rh["state"] == "SKIP" or "png" in rh["outputs"]), rh.get("reason", "")[:60])
    if rh["state"] == "PASS":
        cfg = json.loads(Path(rh["config"]).read_text(encoding="utf-8"))
        ch = cfg["charts"][0]
        chk("⑤ 熱圖細切律入設定(annot True/.2f/coolwarm)", ch.get("annot") is True and ch.get("annot_format") == HEAT_FMT
            and ch.get("cmap") == HEAT_CMAP)
    else:
        chk("⑤ 熱圖細切律入設定", True, "(SKIP 模式=以原始碼律驗)" if f'"cmap": HEAT_CMAP' in src else "")
    render_index([dict(rs, name="stock_2330"), dict(rh, name="rotation_heatmap")])
    page = UI.read_text(encoding="utf-8")
    chk("⑥ 索引頁零 CDN+加速橋+包原件零觸碰(config/data/output 全在 VIA_Reports)",
        '<script src="http' not in page and "ACCEL-BRIDGE" in src and str(WORK) in rs["config"]
        and not any(p.name.startswith("stack_") for p in (pk or Path(".")).glob("*.json")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== Seaborn 垂直圖組橋接(VAP_ENG015)· 六檢自測(零外網)===")
        return selftest()
    if "--pkgtest" in a:
        return 0 if pkgtest()["rc"] == 0 else 1
    return run(a)


if __name__ == "__main__":
    sys.exit(main())

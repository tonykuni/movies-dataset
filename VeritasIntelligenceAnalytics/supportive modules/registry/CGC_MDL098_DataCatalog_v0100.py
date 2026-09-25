#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL098_DataCatalog — 資料庫目錄+擷取細則台(批226;操作員令)
====================================================================
操作員令:「台股資料庫有哪些、抓取哪些項目細則(完整 header);
開始日~最新(勾選),把勾打掉可輸入日期,起始時間可改;全球分類
更多(指數/ETF/美日個股/財報/原油/美元匯率/商品/加密/總經/聯準會/
財政利率)」。
產出 VIA_UI_DataCatalog_v0100.html:
  ① 台股庫完整目錄:每表全 header(欄名:型別)+列數+日期範圍
  ② 全球庫完整目錄(同細則)
  ③ 擷取控制:勾選「開始日~最新」=預設;取消勾選=日期輸入啟用
     (起始/結束可改)→橋 /run?task=…&start=&end=(&cats=)直跑
  ④ 全球 11 類覆蓋矩陣(宇宙冊 SSOT join:在庫/擴充/候源誠實)
唯讀聚合(庫鎖=誠實 busy);零 CDN;10.5px 專業小字;auto-fit。
用法:python3 CGC_MDL098_DataCatalog_v0100.py [--open] | --selftest
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
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_DataCatalog_v0100.html"
ROSTER = HERE / "VIA_Global_Universe_v0100.json"

# 來源引擎對映冊(表→抓取道;人讀細則)
SOURCE_MAP = {
    "tw_daily_prices": "yahoo_chart 統包(boot ②+回補 ENG064)",
    "tw_prices_adj": "ENG060 調整層(boot ②b 重建)",
    "prices_canonical": "ENG060 正典鏡像(重建)",
    "features_daily": "ENG061 因子庫(boot ②c 重建;11 因子)",
    "group_features_daily": "ENG062 族群聚合層(boot ⑧b)",
    "dq_ohlc_flags": "ENG060 品質旗標(保序判準)",
    "tw_chip_inst": "TWSE/TPEX 官方三大法人(boot ③)",
    "tw_chip_margin": "TWSE/TPEX 官方融資券(boot ③)",
    "tw_chip_derived": "籌碼衍生(重建)",
    "tw_trading_daily": "TWSE/TPEX 官方成交值(boot ⑥)",
    "tw_valuation_daily": "TWSE/TPEX 官方本益比/殖利率/淨值比(boot ⑦)",
    "tw_monthly_revenue": "MOPS 官方月營收 L/P/O 三版(ENG063 ⑦d)",
    "monthly_revenue_analysis": "ENG063 月索引 RANGE 視圖(重建)",
    "revenue_group_analysis": "ENG063 族群月營收榜(重建)",
    "analyst_estimates": "券商報告 digest(EXTERNAL_ANALYST)",
    "consensus_daily": "三源共識(分析師+Yahoo QS+鉅亨 FactSet ⑦b/c/e)",
    "consensus_latest": "共識尾版視圖(重建)",
    "etf_book": "ETF 持股冊(ENG051 ④)",
    "tw_listings": "TWSE/TPEX 上市櫃名冊(boot ①)",
    "tw_listings_industry": "官方產業分類(boot ①)",
    "tw_daytrade_eligible": "現沖標的冊(官方)",
    "tw_daytrade_market": "現沖市場統計(官方)",
    "tw_market_agg": "市場聚合(重建)",
    "tw_rates_cbc": "央行 A13 利率(cbc xls)",
    "global_daily": "yahoo_chart 統包(OmniFetch+ENG066 宇宙冊 11 類)",
    "us_macro": "FRED 官方(16 序列;key 本機 gitignored)",
    "features_daily_gl": "全球因子層(重建)",
}


def catalog(db: Path, label: str) -> list[dict]:
    """每表:全 header(欄:型別)+列數+日期範圍;鎖=誠實 busy"""
    out = []
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
    except Exception as exc:
        return [{"t": f"({label} 庫 busy/缺:{type(exc).__name__}=誠實稍後)",
                 "cols": [], "n": 0, "rng": ""}]
    for (t,) in sorted(con.execute("SHOW TABLES").fetchall()):
        cols = [f"{c[0]}:{c[1]}" for c in con.execute(f'DESCRIBE "{t}"').fetchall()]
        n = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        rng = ""
        if any(c.startswith("date:") for c in cols):
            try:
                a, b = con.execute(
                    f'SELECT min(date), max(date) FROM "{t}"').fetchone()
                rng = f"{a}~{b}" if a else ""
            except Exception:
                pass
        elif any(c.startswith("ym:") for c in cols):
            try:
                a, b = con.execute(
                    f'SELECT min(ym), max(ym) FROM "{t}"').fetchone()
                rng = f"{a}~{b}" if a else ""
            except Exception:
                pass
        out.append({"t": t, "cols": cols, "n": n, "rng": rng})
    con.close()
    return out


def render() -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tw = catalog(MEGA / "vdf_tw_market.duckdb", "台股")
    gl = catalog(MEGA / "vdf_global_market.duckdb", "全球")
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))

    def cat_table(rows, label):
        body = "".join(
            f"<tr><td><b>{r['t']}</b><div class='mut'>"
            f"{SOURCE_MAP.get(r['t'], '(重建/衍生)')}</div></td>"
            f"<td>{r['n']:,}</td><td>{r['rng']}</td>"
            f"<td class='hdr'>{' · '.join(r['cols'])}</td></tr>"
            for r in rows)
        return (f"<table><thead><tr><th>表(來源細則)</th><th>列數</th>"
                f"<th>日期範圍</th><th>完整 header(欄:型別)</th></tr></thead>"
                f"<tbody>{body}</tbody></table>")

    cats_ck = "".join(
        f"<label class='ck'><input type='checkbox' class='cat' "
        f"value='{c['cat']}' {'checked' if c['symbols'] else 'disabled'}>"
        f"{c['zh']}({len(c['symbols'])}檔"
        f"{';候源' if not c['symbols'] else ''})</label>"
        for c in roster["categories"])
    cov = "".join(
        f"<tr><td>{c['zh']}</td><td>{c['cat']}</td><td>{c['status']}</td>"
        f"<td>{len(c['symbols'])}</td>"
        f"<td class='hdr'>{' '.join(c['symbols']) or c.get('pending_note', c.get('in_db_note', ''))}</td></tr>"
        for c in roster["categories"])
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA DataCatalog · 資料庫目錄+擷取細則</title>
<style>
:root{{--bg:#0b1220;--card:#111a2e;--line:#1e2a44;--tx:#c7d3e8;--dim:#7e8db0;
--ac:#4f8ef7}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--tx);font:10.5px/1.5 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px;max-width:1280px;margin:0 auto}}
h1{{font-size:14px;color:#e8eefb}}
.sub{{color:var(--dim);font-size:10px;margin:2px 0 10px}}
h2{{font-size:11.5px;color:var(--ac);margin:14px 0 6px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:10px;margin-bottom:10px;overflow:auto}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:var(--dim);font-size:9.5px;
border-bottom:1px solid var(--line);padding:2px 6px 3px 0}}
td{{padding:3px 6px 3px 0;border-bottom:1px dashed var(--line);
vertical-align:top;overflow-wrap:anywhere}}
.hdr{{color:var(--dim);font-size:9px}}
.mut{{color:var(--dim);font-size:9px}}
.row{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:6px 0}}
label.ck{{display:inline-flex;gap:4px;align-items:center;border:1px solid
var(--line);border-radius:6px;padding:4px 8px;cursor:pointer}}
input[type=date]{{background:#16233d;color:var(--tx);border:1px solid #2a3c61;
border-radius:6px;padding:4px 6px;font-size:10.5px}}
input[type=date]:disabled{{opacity:.35}}
.act{{background:#16233d;color:#c7d3e8;border:1px solid #2a3c61;
border-radius:6px;padding:6px 12px;font-size:10.5px;cursor:pointer}}
.act:hover{{border-color:var(--ac);color:#fff}}
#amx{{margin-top:4px}}
</style></head><body>
<h1>VIA 資料庫目錄+擷取細則台</h1>
<div class="sub">{ts} · 完整 header(欄:型別)+來源引擎細則+日期範圍
· 唯讀聚合(庫忙=誠實 busy)· <span id="bstate">⏳ 橋偵測中…</span></div>

<section><h2>③ 擷取控制(勾選=開始日~最新;取消勾選=可輸日期,起始可改)</h2>
<div class="row">
<label class="ck"><input type="checkbox" id="latest" checked>
開始日~最新(預設)</label>
起始 <input type="date" id="d0" value="2022-01-01" disabled>
結束 <input type="date" id="d1" disabled>
</div>
<div class="row">{cats_ck}</div>
<div class="row">
<button class="act" data-task="backfill">📥 台股回補(範圍)</button>
<button class="act" data-task="global">🌍 全球宇宙擷取(勾選類)</button>
<button class="act" data-task="revenue">🏢 月營收</button>
<button class="act" data-task="boot">🔄 日更全鏈</button>
</div>
<div class="mut">台股自訂範圍下限=2022-01-01(2020/21=批212 操作員終止;
解除僅憑明令);全球域無終止令,預設 2020-01-01~最新</div>
<div id="amx" class="mut"></div></section>

<section><h2>① 台股庫 vdf_tw_market.duckdb({len(tw)} 表)</h2>
{cat_table(tw, "台股")}</section>
<section><h2>② 全球庫 vdf_global_market.duckdb({len(gl)} 表)</h2>
{cat_table(gl, "全球")}</section>
<section><h2>④ 全球 11 類覆蓋矩陣(宇宙冊 SSOT;候源=誠實不假抓)</h2>
<table><thead><tr><th>分類</th><th>代碼</th><th>狀態</th><th>檔數</th>
<th>symbols / 候源說明</th></tr></thead><tbody>{cov}</tbody></table></section>

<script>
const BASE = location.origin.startsWith("http") ? "" : "http://127.0.0.1:8765";
let BRIDGE = false;
const LAMP = {{idle: "#bbb", running: "#f0b429", ok: "#15803d", fail: "#dc2626"}};
const $ = id => document.getElementById(id);
$("latest").onchange = () => {{
  const off = !$("latest").checked;      // 把勾打掉=日期輸入啟用
  $("d0").disabled = !off; $("d1").disabled = !off;
}};
fetch(BASE + "/ping").then(r => r.json()).then(j => {{
  if (j && j.via === "deck-bridge") {{
    BRIDGE = true;
    $("bstate").textContent = "🟢 橋接中=按下直接執行";
    setInterval(pollA, 2500); pollA();
  }}
}}).catch(() => {{ $("bstate").textContent =
  "⚪ 無橋=先雙擊 VIA 啟橋(誠實提示)"; }});
function pollA() {{
  fetch(BASE + "/status").then(r => r.json()).then(st => {{
    $("amx").innerHTML = Object.entries(st).map(([id, s]) =>
      `<span style="margin-right:10px"><span style="display:inline-block;` +
      `width:8px;height:8px;border-radius:50%;background:` +
      `${{LAMP[s.state] || "#bbb"}};margin-right:3px"></span>${{s.zh}}` +
      `${{s.fix ? "·" + s.fix : ""}}</span>`).join("");
  }}).catch(() => {{}});
}}
document.querySelectorAll(".act").forEach(b => b.onclick = () => {{
  if (!BRIDGE) {{ alert("無橋:請先雙擊桌面 VIA(啟動指揮台橋)"); return; }}
  let q = "task=" + b.dataset.task;
  if (!$("latest").checked && $("d0").value) {{
    const end = $("d1").value ||
      new Date().toISOString().slice(0, 10);   // 結束留空=最新(誠實補今日)
    q += `&start=${{$("d0").value}}&end=${{end}}`;
  }}
  if (b.dataset.task === "global") {{
    const cs = [...document.querySelectorAll(".cat:checked")]
      .map(x => x.value).join(",");
    if (cs) q += "&cats=" + cs;
  }}
  fetch(BASE + "/run?" + q).then(r => r.json()).then(j => {{
    b.textContent = (j.ok ? "🟡 " : "⛔ ") + b.textContent.replace(/^[🟡⛔] /, "");
    pollA(); }}).catch(() => {{}});
}});
</script>
</body></html>"""


def run(open_after: bool = False) -> int:
    OUT.write_text(render(), encoding="utf-8")
    print(f"[UI] {OUT.name} · 目錄+細則+擷取控制(勾選日期/11 類)")
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
    chk("① 四區在頁(擷取控制/台股目錄/全球目錄/11 類覆蓋)", rc == 0 and
        all(k in page for k in ("③ 擷取控制", "① 台股庫", "② 全球庫",
                                "④ 全球 11 類覆蓋矩陣")))
    chk("② 完整 header 細則(欄:型別 + 來源引擎對映)",
        "date:VARCHAR" in page and "close:DOUBLE" in page
        and "MOPS 官方月營收" in page and "完整 header(欄:型別)" in page)
    chk("③ 勾選=開始日~最新;取消=日期輸入啟用(起始可改)",
        'id="latest" checked' in page and "把勾打掉=日期輸入啟用" in page
        and 'input[type=date]:disabled' in page)
    chk("④ 台股終止令下限誠實宣告(2022-01-01;全球無終止)",
        "2022-01-01(2020/21=批212" in page and "全球域無終止令" in page)
    chk("⑤ 11 類覆蓋=宇宙冊 SSOT join(候源誠實列示)",
        all(k in page for k in ("國際股票指數", "加密貨幣", "聯準會",
                                "美國財政及利率", "候源")))
    chk("⑥ 橋帶參直跑(start/end/cats query;無橋誠實提示)",
        "&start=" in page and "&cats=" in page and "無橋:請先雙擊桌面 VIA" in page)
    chk("⑦ 零 CDN+唯讀聚合(庫鎖誠實 busy)",
        all(k not in page for k in ('src="http', "@import"))
        and "read_only=True" in src and "誠實 busy" in src)
    chk("⑧ 加速橋+零 http 庫(頁生成純本地)",
        "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 資料庫目錄+擷取細則台(CGC_MDL098)· 八檢自測(零網路)===")
        return selftest()
    return run(open_after="--open" in args)


if __name__ == "__main__":
    sys.exit(main())

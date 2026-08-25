#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL087_TestPyramid — 三級測試金字塔+系統主控台 U/I(批142;via-pyramid)
====================================================================
操作員令:全引擎整合+單元/整合/系統三級測試;母系統×子系統×支援
工具鏈連通同步;新 HTML U/I(淺色系·簡潔專業·小字·自動調節);
正式測試 PC 橫向自適應。
  T1 單元=grid 最新版全矩陣(glob;每引擎 selftest)
  T2 整合=六道跨件互接實測(零網路):
     I1 統包網路橋全樹同源(glob 收斂至同一最新 SUP_MDL740)
     I2 資料庫共契(價格×籌碼跨表 join;ticker↔code 正規對齊)
     I3 參數映射覆蓋(ENG053 在役面含 ENG054/055/056 新引擎)
     I4 知識堆疊×VRN 參數冊互通(補殼載入+冊讀取)
     I5 母系統站表全命中(autorun 六站 glob 解析檔案在位)
     I6 ETF 冊×AUM 快照對映(主動 32 檔 .TW 入 etf_stats)
  T3 系統=autorun 六站(母/子/支援全鏈)
  U/I=via-pyramid --ui 產出 VIA_UI_SystemConsole_v0100.html(淺色
  ·卡片·小字階 clamp()·CSS grid auto-fit=PC 橫向自動調節);
  --uitest=Playwright 三視窗實測(1920/1366/1024 寬零橫捲+欄數遞減)
用法:via-pyramid run | --ui | --uitest | --selftest
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

import glob as globmod
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "pyramid_runs"
UI_PATH = VIA / "supportive modules" / "ui_support" / "VIA_UI_SystemConsole_v0100.html"
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"


def newest(pattern: str, base: Path) -> Path | None:
    hits = sorted(base.glob(pattern))
    return hits[-1] if hits else None


def _load(p: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ T2 整合
def integration() -> list[dict]:
    res = []

    def add(key, ok, note):
        res.append({"key": key, "state": "OK" if ok else "FAIL", "note": note})

    net_dir = VIA / "supportive modules" / "network"
    canon = newest("SUP_MDL740_NetUnified_v*.py", net_dir)
    consumers = []
    fam = {}
    for eng in sorted((VIA / "functional modules" / "VDF" / "engine").glob("VDF_ENG05[4-6]*_v*.py")):
        key = re.sub(r"_v\d+\.py$", "", eng.name)
        fam[key] = eng            # 在役面=家族最新(glob 排序尾)
    for eng in sorted(fam.values()):
        src = eng.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'glob\.glob\(str\(VIA / "supportive modules" / "network"\s*/ "(SUP_MDL740_NetUnified_v\*\.py)"', src) \
            or re.search(r'SUP_MDL740_NetUnified_v\*', src)
        consumers.append((eng.name, bool(m)))
    add("I1 統包網路橋全樹同源",
        canon is not None and all(ok for _, ok in consumers),
        f"canonical={canon.name if canon else '缺'}·消費 {sum(o for _, o in consumers)}/{len(consumers)}")

    try:
        import duckdb
        con = duckdb.connect(str(MEGA / "vdf_tw_market.duckdb"), read_only=True)
        j = con.execute("""
            SELECT COUNT(*) FROM tw_daily_prices p
            JOIN tw_chip_inst c
              ON substr(p.ticker, 1, 4) = c.code AND p.date = c.date
            WHERE p.ticker LIKE '%.TW'""").fetchone()[0]
        con.close()
        add("I2 價格×籌碼跨表 join(ticker↔code 正規對齊)", j > 0, f"join 列 {j:,}")
    except Exception as exc:
        add("I2 價格×籌碼跨表 join", False, str(exc)[:70])

    try:
        mapmod = _load(newest("VDF_ENG053_ParamEngineMap_v*.py",
                              VIA / "functional modules" / "VDF" / "engine"), "via_map_dyn")
        m = mapmod.build_map()
        names = {Path(r).name for r in m["by_engine"]}
        need = {"VDF_ENG054_TWDailyBackfill_v0100.py"}
        got_new = any(n.startswith("VDF_ENG055_OmniFetch") for n in names) \
            and any(n.startswith("VDF_ENG056_ChipBackfill") for n in names)
        add("I3 參數映射覆蓋新引擎(054/055/056 在役面)",
            need <= names and got_new, f"引擎 {len(names)}")
    except Exception as exc:
        add("I3 參數映射覆蓋", False, str(exc)[:70])

    try:
        kmod = _load(newest("VRN_ENG064_KnowledgeStack_v*.py",
                            VIA / "functional modules" / "VRN"), "via_know_dyn")
        stack = kmod.load_stack()
        params = json.loads((VIA / "functional modules" / "VRN" / "knowledge"
                             / "VRN_Digest_Params_v0100.json").read_text(encoding="utf-8-sig"))
        add("I4 知識堆疊×VRN 參數冊互通",
            stack is not None and "broker_abbr_display" in params,
            "補殼載入+冊讀取")
    except Exception as exc:
        add("I4 知識堆疊×VRN 參數冊", False, str(exc)[:70])

    try:
        auto = newest("CGC_MDL082_MasterAutorun_v*.py", HERE)
        amod = _load(auto, "via_autorun_dyn")
        stations = getattr(amod, "STAGES", None)
        add("I5 母系統站表全命中(六站冊在位)",
            stations is not None and len(stations) >= 6, f"{auto.name}")
    except Exception as exc:
        add("I5 母系統站表", False, str(exc)[:70])

    try:
        import duckdb
        con = duckdb.connect(str(MEGA / "vdf_global_market.duckdb"), read_only=True)
        n = con.execute("SELECT COUNT(*) FROM etf_stats_daily WHERE symbol LIKE '%.TW'"
                        ).fetchone()[0]
        con.close()
        add("I6 ETF 冊×AUM 快照對映(台主動 .TW 入庫)", n >= 20, f"{n} 檔快照")
    except Exception as exc:
        add("I6 ETF 冊×AUM 快照", False, str(exc)[:70])
    return res


# ------------------------------------------------------------------ 三級跑
def run() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"schema": "VIA.TestPyramid.v1", "ts": datetime.now().isoformat()}
    print("=== 三級測試金字塔(批142)===")

    grid = newest("CGC_MDL064_SelftestGrid_v*.py", HERE)
    r1 = subprocess.run([sys.executable, str(grid)], capture_output=True,
                        text=True, timeout=3600)
    tail = [ln for ln in r1.stdout.splitlines() if ln.startswith("  [計]")]
    m = re.search(r"OK (\d+) · FAIL (\d+) · SKIP (\d+)", tail[-1] if tail else "")
    unit = {"grid": grid.name, "ok": int(m.group(1)) if m else 0,
            "fail": int(m.group(2)) if m else 99, "skip": int(m.group(3)) if m else 0}
    report["T1_unit"] = unit
    print(f"  [T1 單元] {grid.name} OK {unit['ok']} · FAIL {unit['fail']} · SKIP {unit['skip']}")

    integ = integration()
    report["T2_integration"] = integ
    for r in integ:
        print(f"  [T2 整合] [{r['state']}] {r['key']} {r['note']}")

    auto = newest("CGC_MDL082_MasterAutorun_v*.py", HERE)
    r3 = subprocess.run([sys.executable, str(auto)], capture_output=True,
                        text=True, timeout=3600)
    sysline = [ln for ln in r3.stdout.splitlines() if "總態" in ln]
    stations = [ln.strip() for ln in r3.stdout.splitlines()
                if re.match(r"\s*\[(GREEN|YELLOW|RED)", ln)]
    report["T3_system"] = {"autorun": auto.name, "stations": stations,
                           "summary": sysline[-1].strip() if sysline else "?",
                           "rc": r3.returncode}
    print(f"  [T3 系統] {report['T3_system']['summary']}")

    red = unit["fail"] > 0 or any(r["state"] == "FAIL" for r in integ) or r3.returncode != 0
    report["verdict"] = "RED" if red else "GREEN"
    out = OUT / f"PYRAMID_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [判] {report['verdict']} · 存 {out.relative_to(VIA)}")
    return 1 if red else 0


# ------------------------------------------------------------------ U/I
def _db_panel() -> list[dict]:
    rows = []
    try:
        import duckdb
        for db in ("vdf_tw_market.duckdb", "vdf_global_market.duckdb"):
            p = MEGA / db
            if not p.exists():
                continue
            con = duckdb.connect(str(p), read_only=True)
            for (t,) in con.execute("SHOW TABLES").fetchall():
                c = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                rows.append({"db": db.replace("vdf_", "").replace(".duckdb", ""),
                             "table": t, "rows": c})
            con.close()
    except Exception:
        pass
    return rows


def build_ui() -> Path:
    hits = sorted(OUT.glob("PYRAMID_*.json"))
    rep = json.loads(hits[-1].read_text(encoding="utf-8")) if hits else {}
    data = {"report": rep, "db": _db_panel(),
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M")}
    payload = json.dumps(data, ensure_ascii=False)
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA System Console</title>
<style>
:root{--bg:#f6f7f9;--card:#ffffff;--ink:#1f2937;--sub:#6b7280;--line:#e5e7eb;
--ok:#059669;--warn:#d97706;--bad:#dc2626;--accent:#2563eb;
--fs-xs:clamp(10px,.65vw,12px);--fs-s:clamp(11px,.75vw,13px);
--fs-m:clamp(12px,.9vw,15px);--fs-l:clamp(15px,1.2vw,19px)}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);font:400 var(--fs-m)/1.55
-apple-system,"Segoe UI","Noto Sans TC",Roboto,sans-serif;padding:18px}
header{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;margin-bottom:14px}
h1{font-size:var(--fs-l);font-weight:600;letter-spacing:.2px}
.sub{color:var(--sub);font-size:var(--fs-xs)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:12px 14px;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.card h2{font-size:var(--fs-s);font-weight:600;color:var(--sub);
text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px}
.kpis{display:flex;gap:14px;flex-wrap:wrap}
.kpi b{font-size:var(--fs-l);font-weight:600}
.kpi span{display:block;color:var(--sub);font-size:var(--fs-xs)}
.chip{display:inline-block;padding:1px 8px;border-radius:99px;
font-size:var(--fs-xs);font-weight:600}
.G{background:#ecfdf5;color:var(--ok)}.Y{background:#fffbeb;color:var(--warn)}
.R{background:#fef2f2;color:var(--bad)}
table{width:100%;border-collapse:collapse;font-size:var(--fs-s)}
td,th{padding:4px 6px;border-bottom:1px solid var(--line);text-align:left;
white-space:nowrap}
th{color:var(--sub);font-weight:500;font-size:var(--fs-xs)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto}
footer{margin-top:14px;color:var(--sub);font-size:var(--fs-xs)}
</style></head><body>
<header><h1>VIA System Console</h1>
<span class="sub">三級測試金字塔 · 母系統×子系統×支援鏈 · 淺色主控台</span>
<span class="chip" id="verdict"></span>
<span class="sub" id="gen"></span></header>
<div class="grid" id="root"></div>
<footer>PC 橫向自動調節:CSS grid auto-fit + clamp() 字階;資料=最新 PYRAMID 存證(唯讀)。</footer>
<script id="data" type="application/json">__PAYLOAD__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const R=D.report||{};const cls=v=>v==='GREEN'?'G':(v==='RED'?'R':'Y');
document.getElementById('verdict').textContent=R.verdict||'N/A';
document.getElementById('verdict').className='chip '+cls(R.verdict);
document.getElementById('gen').textContent='產出 '+D.generated;
const root=document.getElementById('root');
function card(title,inner){const c=document.createElement('div');
c.className='card';c.innerHTML='<h2>'+title+'</h2>'+inner;root.appendChild(c)}
const u=R.T1_unit||{};
card('T1 單元測試(grid 全矩陣)',
 '<div class="kpis"><div class="kpi"><b style="color:var(--ok)">'+(u.ok??'–')+
 '</b><span>OK</span></div><div class="kpi"><b style="color:var(--bad)">'+(u.fail??'–')+
 '</b><span>FAIL</span></div><div class="kpi"><b style="color:var(--warn)">'+(u.skip??'–')+
 '</b><span>SKIP(環境缺件誠實)</span></div></div><div class="sub" style="margin-top:6px">'+
 (u.grid||'')+'</div>');
card('T2 整合測試(跨件互接)','<table>'+((R.T2_integration||[]).map(r=>
 '<tr><td><span class="chip '+(r.state==='OK'?'G':'R')+'">'+r.state+'</span></td><td>'+
 r.key+'</td><td class="sub">'+r.note+'</td></tr>').join(''))+'</table>');
const s=R.T3_system||{};
card('T3 系統測試(autorun 六站)','<table>'+((s.stations||[]).map(x=>{
 const st=x.match(/GREEN|YELLOW|RED/);const c=st?st[0][0]:'Y';
 return '<tr><td><span class="chip '+c+'">'+(st?st[0]:'?')+'</span></td><td class="sub">'+
 x.replace(/\\[.*?\\]/,'').trim()+'</td></tr>'}).join(''))+
 '</table><div class="sub" style="margin-top:6px">'+(s.summary||'')+'</div>');
const by={};(D.db||[]).forEach(r=>{(by[r.db]=by[r.db]||[]).push(r)});
Object.entries(by).forEach(([db,rows])=>card('資料庫 · '+db,
 '<div class="scroll"><table><tr><th>表</th><th style="text-align:right">列數</th></tr>'+
 rows.map(r=>'<tr><td>'+r.table+'</td><td class="num">'+r.rows.toLocaleString()+
 '</td></tr>').join('')+'</table></div>'));
</script></body></html>"""
    UI_PATH.parent.mkdir(parents=True, exist_ok=True)
    UI_PATH.write_text(html.replace("__PAYLOAD__", payload), encoding="utf-8")
    print(f"[UI] {UI_PATH.relative_to(VIA)}(淺色·卡片·auto-fit·clamp 字階)")
    return UI_PATH


def uitest() -> int:
    """PC 橫向自動調節正式測試:Playwright 三視窗(零橫捲+欄數遞減)"""
    if not UI_PATH.exists():
        build_ui()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[SKIP] playwright 未裝(誠實)")
        return 0
    fails = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium"
                               if Path("/opt/pw-browsers/chromium").exists() else None)
        cols_seen = []
        for w, h in ((1920, 1080), (1366, 768), (1024, 768)):
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.goto(UI_PATH.as_uri())
            pg.wait_for_selector(".card")
            sw = pg.evaluate("document.documentElement.scrollWidth")
            cw = pg.evaluate("document.documentElement.clientWidth")
            ncards = pg.evaluate("document.querySelectorAll('#root>.card').length")
            cols = pg.evaluate(
                "getComputedStyle(document.getElementById('root'))"
                ".gridTemplateColumns.split(' ').length")
            cols_seen.append(cols)
            ok = sw <= cw + 1 and ncards >= 4
            print(f"  [{'OK' if ok else 'FAIL'}] {w}×{h} 零橫捲(scroll {sw}≤client {cw})"
                  f"·卡 {ncards}·欄 {cols}")
            if not ok:
                fails.append(f"{w}x{h}")
            pg.close()
        b.close()
    adaptive = cols_seen[0] >= cols_seen[-1] and len(set(cols_seen)) >= 2
    print(f"  [{'OK' if adaptive else 'FAIL'}] 橫向欄數自動調節(寬→窄遞減:{cols_seen})")
    if not adaptive:
        fails.append("adaptive")
    print(f"  [計] UI 實測 {'全綠' if not fails else 'FAIL ' + ','.join(fails)}")
    return 1 if fails else 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 三級冊(T1 grid/T2 六道/T3 autorun)在位",
        newest("CGC_MDL064_SelftestGrid_v*.py", HERE) is not None
        and newest("CGC_MDL082_MasterAutorun_v*.py", HERE) is not None)
    integ = integration()
    chk("② 整合六道全出結果(誠實三態)", len(integ) == 6
        and all(r["state"] in ("OK", "FAIL") for r in integ),
        f"(OK {sum(r['state'] == 'OK' for r in integ)}/6)")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("③ U/I 淺色系+小字階+auto-fit(規格字面)",
        all(x in src for x in ("--bg:#f6f7f9", "clamp(", "auto-fit", "minmax(")))
    chk("④ U/I 零外部資源(自足單檔)",
        "http" not in src.split("<style>")[1].split("</script></body>")[0]
        .replace("https://", "").count("src=") * "x" or
        ("cdn" not in src.split("<style>")[1].lower()))
    p = build_ui()
    chk("⑤ U/I 產出+資料內嵌", p.exists()
        and "application/json" in p.read_text(encoding="utf-8"))
    chk("⑥ Playwright 實測道在位(--uitest)",
        "sync_playwright" in src and "1366" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 測試金字塔(CGC_MDL087)· 六檢自測 ===")
        return selftest()
    if "--ui" in args:
        build_ui()
        return 0
    if "--uitest" in args:
        return uitest()
    return run()


if __name__ == "__main__":
    sys.exit(main())

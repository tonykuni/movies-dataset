# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_Subsystems_Console_Builder_v0100.py — VAP/VDF/VRN ALL-IN-ONE 主控台(簡潔版)

自包含 HTML(零外部資產、零網路),四分頁:總覽 / VAP / VDF / VRN。
嵌入 USER-TEST 結果、HardGate 七工具封印、引擎盤點與一鍵啟動命令。
輸出:VIA_Reports/VIA_Subsystems_Console_v0100.html
"""
from __future__ import annotations

from pathlib import Path
import datetime as dt
import json
import re
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
FM_DIR = SCRIPT_DIR.parent
VIA_DIR = FM_DIR.parent
OUT_HTML = VIA_DIR / "VIA_Reports" / "VIA_Subsystems_Console_v0100.html"
RUN_UT = SCRIPT_DIR / "evidence" / "RUN_SUBSYSTEMS_USERTEST_V0100"
VERSION = "0.1.00"

# 沿用本套件已驗證之視覺鎖 tokens(台股慣例:上=紅、下=青綠;分類藍/金/綠/紫)
C = {"bg": "#f5f4f0", "sf": "#fff", "ink": "#1e1d1a", "sub": "#6b6a66", "bd": "#dbd9d3",
     "up": "#c9584a", "dn": "#1f9e9e", "amber": "#c4943a", "blue": "#3b6fc4",
     "teal": "#0f9678", "violet": "#8f56c8", "seal": "#b5291a"}


def def_inventory(sub: str) -> dict:
    d = FM_DIR / sub
    py = list(d.rglob("*.py"))
    return {"py": len([p for p in py if "__pycache__" not in p.parts]),
            "ps1": len(list(d.rglob("*.ps1"))),
            "html": len(list(d.rglob("*.html"))),
            "json": len(list(d.rglob("*.json")))}


def def_hardgate() -> dict:
    sp = subprocess.run([sys.executable, str(FM_DIR / "VRN" / "VIA_HardGate_BootPrecheck.py"), "--quiet"],
                        capture_output=True, text=True, timeout=300, cwd=SCRIPT_DIR)
    m = re.search(r"\{.*\}", sp.stdout, flags=re.S)
    doc = json.loads(m.group(0)) if m else {}
    return {"seal": doc.get("seal", "?"), "n_loaded": doc.get("n_loaded", 0),
            "n_capable": doc.get("n_capable", 0), "ok": doc.get("ok", {})}


def def_build() -> None:
    ut = json.loads((RUN_UT / "usertest_summary.json").read_text("utf-8"))
    hg = def_hardgate()
    inv = {s: def_inventory(s) for s in ["VAP", "VDF", "VRN"]}
    checks = ut["Checks"]
    by_sub = {s: [c for c in checks if c["Subsystem"] == s] for s in ["VAP", "VDF", "VRN"]}

    def pill(v: str) -> str:
        col = C["teal"] if v == "PASS" else C["seal"]
        return f'<span class="pill" style="background:{col}">{v}</span>'

    def bar(label: str, val: float, vmax: float, color: str) -> str:
        w = 0 if vmax <= 0 else max(2, round(260 * val / vmax))
        return (f'<div class="brow"><span class="blab">{label}</span>'
                f'<span class="btrack"><span class="bfill" style="width:{w}px;background:{color}"></span></span>'
                f'<span class="bval">{val:g}</span></div>')

    # 總覽:每子系統 PASS 數長條(Plotly 風水平 bar,直接標值)
    ov_bars = "".join(
        bar(s, sum(1 for c in by_sub[s] if c["Verdict"] == "PASS"), 3,
            {"VAP": C["blue"], "VDF": C["teal"], "VRN": C["violet"]}[s])
        for s in ["VAP", "VDF", "VRN"])
    inv_bars = "".join(bar(s, inv[s]["py"], max(v["py"] for v in inv.values()), C["amber"])
                       for s in ["VAP", "VDF", "VRN"])

    def check_table(sub: str) -> str:
        body = "".join(
            f"<tr><td class='mono'>{c['Check']}</td><td>{c['Detail']}</td>"
            f"<td class='num'>{c['Seconds']}s</td><td>{pill(c['Verdict'])}</td></tr>"
            for c in by_sub[sub])
        return ("<table><tr><th>USER-TEST</th><th>結果</th><th>秒</th><th>判定</th></tr>"
                + body + "</table>")

    hg_rows = "".join(
        f"<tr><td class='mono'>{k}</td><td>{pill('PASS' if v else 'FAIL')}</td></tr>"
        for k, v in hg["ok"].items())

    launch = {
        "全部(USER-TEST + 主控台重建)": r'pwsh -ExecutionPolicy Bypass -File "$HOME\movies-dataset\VeritasIntelligenceAnalytics\functional modules\SubsystemsConsole\Start-VIA-Subsystems.ps1"',
        "VAP v025 工作台": r'start "" "$HOME\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VAP\VAP_v025_Complete_Package\ui\VAP_Workbench_v025.html"',
        "VDF Hybrid TW 入庫(本機 LIVE)": r'pwsh -File "$HOME\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VDF\FinMind_TW_Flow_Engine\Run_TW_Hybrid_Latest.ps1"',
        "VRN HardGate 滿封驗證": r'python "$HOME\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VRN\VIA_HardGate_BootPrecheck.py"',
    }
    launch_rows = "".join(
        f"<tr><td>{k}</td><td class='mono' style='font-size:10px'>{v}</td></tr>"
        for k, v in launch.items())

    tabs_def = [("ov", "總覽"), ("vap", "VAP"), ("vdf", "VDF"), ("vrn", "VRN")]
    tabbar = "".join(f'<span class="tb" data-t="{t}">{n}</span>' for t, n in tabs_def)

    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · 子系統主控台(VAP/VDF/VRN)</title><style>
body{{background:{C['bg']};color:{C['ink']};margin:0;padding:18px;
font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;font-size:13px}}
.wrap{{max-width:1080px;margin:0 auto}}
.eyebrow{{font-family:ui-monospace,monospace;font-size:11px;letter-spacing:2px;color:{C['sub']};text-transform:uppercase}}
h1{{font-size:20px;margin:6px 0 2px;font-weight:800}}
h2{{font-size:13px;margin:0 0 8px;font-weight:700}}
.strip{{height:6px;border-radius:2px;margin:12px 0;background:linear-gradient(90deg,{C['blue']},{C['teal']},{C['amber']},{C['violet']})}}
.tabbar{{display:flex;gap:6px;margin:4px 0 12px}}
.tb{{cursor:pointer;border:1px solid {C['bd']};border-radius:3px;padding:6px 16px;font-weight:700;background:{C['sf']};user-select:none}}
.tb.on{{background:{C['ink']};color:{C['bg']};border-color:{C['ink']}}}
.card{{background:{C['sf']};border:1px solid {C['bd']};border-radius:8px;padding:12px;margin:10px 0}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:8px 0}}
.kpi{{background:{C['sf']};border:1px solid {C['bd']};border-radius:4px;padding:8px 12px;text-align:center}}
.kpi .v{{font-family:ui-monospace,monospace;font-size:18px;font-weight:700}}
.kpi .l{{font-size:9px;color:{C['sub']};text-transform:uppercase;letter-spacing:.5px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th,td{{padding:5px 8px;border-bottom:1px solid #eceae2;text-align:left;word-break:break-word}}
th{{font-size:9.5px;color:{C['sub']};text-transform:uppercase}}
td.num{{font-family:ui-monospace,monospace;text-align:right}}.mono{{font-family:ui-monospace,monospace}}
.pill{{padding:1px 8px;border-radius:3px;font-family:ui-monospace,monospace;font-size:10px;color:#fff;font-weight:700}}
.brow{{display:flex;align-items:center;gap:8px;margin:5px 0}}
.blab{{width:46px;font-weight:700}}.bval{{font-family:ui-monospace,monospace}}
.btrack{{background:#ecebe6;border-radius:3px;height:14px;width:260px;display:inline-block}}
.bfill{{display:inline-block;height:14px;border-radius:3px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}@media(max-width:860px){{.grid2{{grid-template-columns:1fr}}}}
section{{display:none}}section.on{{display:block}}
.foot{{color:#9c9890;font-size:11px;border-top:1px solid {C['bd']};padding-top:10px;margin-top:14px}}
</style></head><body><div class="wrap">
<div class="eyebrow">VERITAS INTELLIGENCE · SUBSYSTEMS CONSOLE · SELF-CONTAINED · OFFLINE EVIDENCE</div>
<h1>VIA 子系統主控台 — VAP / VDF / VRN</h1>
<div class="strip"></div>
<div class="tabbar" id="tabbar">{tabbar}</div>

<section id="sec-ov">
 <div class="kpis">
  <div class="kpi"><div class="v" style="color:{C['teal']}">{ut['Status'].split('_')[-1]}</div><div class="l">USER-TEST 總判定</div></div>
  <div class="kpi"><div class="v">{sum(1 for c in checks if c['Verdict'] == 'PASS')}/{len(checks)}</div><div class="l">情境通過</div></div>
  <div class="kpi"><div class="v" style="color:{C['violet']}">{hg['seal']}</div><div class="l">VRN HardGate 封印</div></div>
  <div class="kpi"><div class="v">{hg['n_capable']}/7</div><div class="l">七工具 capable</div></div>
 </div>
 <div class="grid2">
 <div class="card"><h2>各子系統 USER-TEST 通過數</h2>{ov_bars}</div>
 <div class="card"><h2>引擎盤點(.py 檔數)</h2>{inv_bars}</div>
 </div>
 <div class="card"><h2>一鍵啟動(自動啟動所有功能)</h2>
  <table><tr><th>功能</th><th>命令(整行複製、單獨貼上)</th></tr>{launch_rows}</table></div>
</section>

<section id="sec-vap">
 <div class="card"><h2>VAP · v025 套件(40 圖 canon 與 v018 同套)</h2>{check_table('VAP')}</div>
 <div class="card"><h2>盤點</h2><div class="mono">py {inv['VAP']['py']} · ps1 {inv['VAP']['ps1']} · html {inv['VAP']['html']} · json {inv['VAP']['json']}</div></div>
</section>

<section id="sec-vdf">
 <div class="card"><h2>VDF · 資料鑄造(CrossValidator/前瞻評價/Hybrid TW 入庫)</h2>{check_table('VDF')}</div>
 <div class="card"><h2>盤點</h2><div class="mono">py {inv['VDF']['py']} · ps1 {inv['VDF']['ps1']} · html {inv['VDF']['html']} · json {inv['VDF']['json']}</div></div>
</section>

<section id="sec-vrn">
 <div class="card"><h2>VRN · HardGate 七工具封印 = <b style="color:{C['violet']}">{hg['seal']}</b>({hg['n_loaded']}/7 載入 · {hg['n_capable']}/7 capable)</h2>
  <table><tr><th>支援工具</th><th>capable</th></tr>{hg_rows}</table>
  <div style="color:{C['sub']};font-size:11px;margin-top:6px">新舊雙代 API 簽名(舊名|新名)擇一命中即 capable;OCR 引擎群屬本機運行時,LIVE 於本機啟動。</div></div>
 <div class="card"><h2>USER-TEST</h2>{check_table('VRN')}</div>
</section>

<div class="foot">VIA Subsystems Console v{VERSION} · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} ·
evidence: SubsystemsConsole/evidence/RUN_SUBSYSTEMS_USERTEST_V0100 · 零外部資產/零網路,可離線開啟</div>
</div><script>
const tabs=document.querySelectorAll(".tb"),secs=document.querySelectorAll("section");
function show(t){{tabs.forEach(e=>e.classList.toggle("on",e.dataset.t===t));
secs.forEach(s=>s.classList.toggle("on",s.id==="sec-"+t));}}
tabs.forEach(e=>e.onclick=()=>show(e.dataset.t));show("ov");
</script></body></html>"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print("=" * 72)
    print(f"VIA Subsystems Console v{VERSION}")
    print("Output :", OUT_HTML, f"({OUT_HTML.stat().st_size // 1024} KB)")
    print("Seal   :", hg["seal"], f"| USER-TEST {ut['Status']}")
    print("=" * 72)


if __name__ == "__main__":
    def_build()

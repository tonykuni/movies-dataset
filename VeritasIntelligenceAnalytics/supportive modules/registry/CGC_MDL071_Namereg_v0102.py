#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_namereg_v0102 — 自動編號註冊命名冊(TOOL-047;操作員令 2026-08-18)
======================================================================
v0100→v0101(操作員令:U/X U/I 以 Veritas Header copy.dc.html 為視覺
鎖定模板):U/I 檢索板全面套用理印紙墨系——暖象牙紙 #f2f1ec/#fbfaf7、
墨 #1b1a17、印紅 #9e2b25(理印徽)、青 #3c6660、金 #8a6420、髮線
#dbd9d3;Cormorant Garamond+Noto Serif CJK TC 襯線標題、JhengHei 內文、
SFMono 代碼欄;viaSweep 掃線動效。零 CDN 鐵律維持:字體純本地堆疊
(工作站有裝則用,無則 Georgia/PMingLiU 誠實回退,不發包)。
編號/指派核心零變動(先發先得 append-only 同 v0100)。
v0101→v0102(操作員令:高度自動化集中化;功能左 panel、視覺展現右;
以電腦螢幕橫向長方形為基準之響應式設計;上下滾動自動隱藏標頭):
U/I 改雙欄格局——左 250px 固定功能 panel(檢索/類別/SYS 子系統計數
即點即濾/冊況),右 stage 視覺展現(掃線+表格);標頭 fixed,下滾隱
上滾現(transform 過場);窄幅(<820px 直向)panel 自動收頂單欄。
令:「UNIT-TEST 重新編號命名 SYS(VRN....) MDL001/ENG001 CLS FNC LIB
範例: VRN_MDL001_YfinanceFetcher.py 自動編號註冊命名」。
紅線先聲明(鐵則):
  ① 編號永不變 — 先發先得、append-only;重跑冪等,舊號零變動
  ② 正本不就地修改 — 實體檔「零改名」;本冊為正典對映(canonical
     alias),改名落地需操作員明確令另行裁決
  ③ 只增不減 — 冊內項目永不刪;檔案消失記 MISSING 不除名
機制:
  · 資料源 = 介面合約冊(TOOL-041;AST 零執行已萃取 fn/cls/import)
  · 家族鍵 = 目錄+去版號檔莖(vrn_table_omni_v0104→vrn_table_omni;
    同家族各版共一號,符「版本前行不換號」)
  · SYS 碼 = VRN/VDF/VAP/CGC/FLOW/CHW(ChipWar)/GRP(GroupIndex)/
    PLG(plugins)/SUP(支援)/VIA(其他)——路徑優先於子系統欄
  · 類別 = ENG(functional modules 或 /engines/)/MDL(支援模組)
  · 正典名 = <SYS>_<ENG|MDL><NNN>_<Camel>(Camel=去 via_/vrn_ 前綴
    去版號後駝峰化;範例 vrn_yfinance_fetcher→VRN_MDLnnn_YfinanceFetcher)
  · CLS###/FNC### = 家族內首見序 append-only;LIB### = 全域 import 冊
輸出:VIA_Naming_Registry_v0100.json(tracked;append-only)
     VIA_Reports/VIA_UI_NamingRegistry.html(U/I:零 CDN 純本地檢索板)
用法:via-namereg            → 註冊(冪等)+U/I 刷新
     via-namereg --dry      → 只報告零寫入(棋盤站用)
     via-namereg --selftest → 單元測試六檢(合成冊,零觸正冊)
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
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
IFACE = HERE / "VIA_Interface_Contract_Registry_v0100.json"
REG = HERE / "VIA_Naming_Registry_v0100.json"
UI = VIA / "VIA_Reports" / "VIA_UI_NamingRegistry.html"
OUT = VIA / "VIA_Reports" / "namereg_runs"

VER_RX = re.compile(r"[_-]v?\d{2,4}[a-z]?$", re.I)
SYS_PATH = [("VIA_FlowSystem", "FLOW"), ("functional modules/ChipWar", "CHW"),
            ("functional modules/GroupIndex", "GRP"), ("functional modules/VRN", "VRN"),
            ("functional modules/VDF", "VDF"), ("functional modules/VAP", "VAP")]
SYS_SUB = {"VRN": "VRN", "VDF": "VDF", "VAP": "VAP", "CGC": "CGC", "PLUG": "PLG",
           "SUPPORT": "SUP", "OTHER": "VIA"}


def family_key(rel: str) -> str:
    p = Path(rel)
    stem = VER_RX.sub("", p.stem)
    return str(p.parent / stem).replace("\\", "/")


def camel_of(rel: str) -> str:
    stem = VER_RX.sub("", Path(rel).stem)
    stem = re.sub(r"^(via|vrn|vdf|vap|veritas)[_-]", "", stem, flags=re.I)
    parts = re.split(r"[^0-9A-Za-z]+", stem)
    out = []
    for w in parts:
        if not w:
            continue
        # 已駝峰之字保留內部大寫(GovFundEngine 不壓平),首字母保證大寫
        out.append(w[0].upper() + w[1:])
    return "".join(out) or "Unnamed"


def sys_of(rel: str, subsystem: str) -> str:
    for frag, code in SYS_PATH:
        if frag in rel:
            return code
    return SYS_SUB.get(subsystem, "VIA")


def kind_of(rel: str) -> str:
    return "ENG" if ("functional modules" in rel or "/engines/" in rel) else "MDL"


def assign(iface_modules: dict, reg: dict) -> dict:
    """核心指派:append-only;舊號零變動;回統計。"""
    items = reg.setdefault("items", {})
    libs = reg.setdefault("libs", {})
    counters = reg.setdefault("counters", {})
    stat = {"new": 0, "kept": 0, "cls_new": 0, "fnc_new": 0, "lib_new": 0}

    def nxt(scope: str) -> int:
        counters[scope] = counters.get(scope, 0) + 1
        return counters[scope]

    for urn in sorted(iface_modules, key=lambda u: iface_modules[u]["rel"]):
        m = iface_modules[urn]
        rel = m["rel"]
        fam = family_key(rel)
        c = m.get("contract", {})
        if fam in items:
            it = items[fam]
            stat["kept"] += 1
            if rel not in it["members"]:
                it["members"].append(rel)  # 家族新版本收錄,號不變
        else:
            sysc = sys_of(rel, m.get("subsystem", "OTHER"))
            kind = kind_of(rel)
            num = nxt(f"{sysc}_{kind}")
            it = items[fam] = {
                "sys": sysc, "kind": kind, "num": num,
                "canonical": f"{sysc}_{kind}{num:03d}_{camel_of(rel)}",
                "iface_urn": urn, "members": [rel],
                "cls": {}, "fnc": {},
                "assigned_at": datetime.now().strftime("%Y%m%d"),
            }
            stat["new"] += 1
        # CLS/FNC:家族內首見序 append-only
        for cl in c.get("classes", []):
            nm = cl.get("name") if isinstance(cl, dict) else str(cl)
            if nm and nm not in it["cls"]:
                it["cls"][nm] = f"CLS{len(it['cls']) + 1:03d}"
                stat["cls_new"] += 1
        for fn in c.get("functions", []):
            nm = fn.get("name") if isinstance(fn, dict) else str(fn)
            if nm and not nm.startswith("_") and nm not in it["fnc"]:
                it["fnc"][nm] = f"FNC{len(it['fnc']) + 1:03d}"
                stat["fnc_new"] += 1
        # LIB:全域 import 冊(頂層套件名)
        for imp in c.get("imports", []):
            top = str(imp).split(".")[0].strip()
            if top and top not in libs:
                libs[top] = f"LIB{len(libs) + 1:03d}"
                stat["lib_new"] += 1
    return stat


def write_ui(reg: dict) -> None:
    rows = []
    for fam, it in sorted(reg["items"].items(), key=lambda kv: (kv[1]["sys"], kv[1]["kind"], kv[1]["num"])):
        rows.append({"c": it["canonical"], "s": it["sys"], "k": it["kind"],
                     "f": fam, "n": len(it["members"]), "cl": len(it["cls"]), "fn": len(it["fnc"])})
    data = json.dumps(rows, ensure_ascii=False)
    n_lib = len(reg.get("libs", {}))
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA 命名冊 U/I</title><style>
/* 視覺鎖定:Veritas Header copy.dc.html 理印紙墨系(零 CDN,字體本地堆疊誠實回退)
   佈局令 2026-08-18:功能左 panel · 視覺展現右 · 橫向螢幕基準響應式 · 滾動自動隱藏標頭 */
:root{--paper:#f2f1ec;--card:#fbfaf7;--ink:#1b1a17;--muted:#6b6860;--hair:#dbd9d3;
--seal:#9e2b25;--teal:#3c6660;--green:#3d7a52;--gold:#8a6420;--blue:#24457f;--mastH:76px}
@keyframes viaSweep{0%{transform:translateX(-100%)}100%{transform:translateX(340%)}}
*{box-sizing:border-box}
body{font-family:'Microsoft JhengHei','Segoe UI',system-ui,sans-serif;margin:0;background:var(--paper);color:var(--ink)}
/* 標頭:滾動下隱上現 */
.mast{position:fixed;top:0;left:0;right:0;z-index:20;display:flex;align-items:center;gap:.8rem;
padding:.8rem 1.4rem .7rem;border-bottom:1px solid var(--hair);background:var(--card);
transition:transform .28s ease}
.mast.hide{transform:translateY(-110%)}
.seal{width:44px;height:44px;border-radius:6px;background:var(--seal);color:#f2f1ec;display:flex;align-items:center;justify-content:center;
font-family:'Noto Serif CJK TC','Songti TC','PMingLiU',serif;font-size:26px;font-weight:600;flex:0 0 auto}
.mtitle{font-family:'Cormorant Garamond',Georgia,serif;font-size:1.35rem;font-weight:600;letter-spacing:.02em}
.msub{font-family:'Noto Serif CJK TC','PMingLiU',serif;color:var(--muted);font-size:.8rem}
.sweepbar{position:relative;height:3px;background:var(--hair);overflow:hidden}
.sweepbar::after{content:'';position:absolute;inset:0;width:30%;background:var(--teal);animation:viaSweep 3.2s ease-in-out infinite}
/* 主格局:左功能 panel + 右視覺展現(橫向螢幕基準) */
.layout{display:grid;grid-template-columns:250px 1fr;gap:0;padding-top:var(--mastH);min-height:100vh}
.panel{position:sticky;top:var(--mastH);align-self:start;height:calc(100vh - var(--mastH));overflow-y:auto;
background:var(--card);border-right:1px solid var(--hair);padding:1rem}
.panel h3{font-family:'Noto Serif CJK TC','PMingLiU',serif;color:var(--teal);font-size:.9rem;margin:.2rem 0 .5rem;
border-bottom:1px solid var(--hair);padding-bottom:.3rem}
.panel .grp{margin-bottom:1.1rem}
input,select{width:100%;padding:.45rem .6rem;border-radius:4px;border:1px solid var(--hair);background:#fff;color:var(--ink);font-family:inherit;margin-bottom:.4rem}
input:focus,select:focus{outline:2px solid var(--teal);outline-offset:0}
.syslist{list-style:none;margin:0;padding:0;font-size:.82rem}
.syslist li{display:flex;justify-content:space-between;padding:.22rem .3rem;border-radius:3px;cursor:pointer}
.syslist li:hover{background:#edece5}
.syslist li.on{background:var(--teal);color:#f2f1ec}
.syslist .n{font-family:'SFMono-Regular',Consolas,monospace;font-size:.75rem}
.stage{padding:1rem 1.4rem;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.85rem;background:var(--card);border:1px solid var(--hair)}
th,td{border-bottom:1px solid var(--hair);padding:.4rem .55rem;text-align:left}
th{font-family:'Noto Serif CJK TC','PMingLiU',serif;color:var(--teal);position:sticky;top:0;background:var(--card);
border-bottom:2px solid var(--teal);font-weight:600}
tr:hover{background:#edece5}
td:first-child{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace;font-size:.8rem;color:var(--blue)}
.badge{display:inline-block;padding:.1rem .5rem;border-radius:3px;background:var(--seal);color:#f2f1ec;font-size:.72rem;letter-spacing:.05em}
.muted{color:var(--muted)}
.kENG{color:var(--green)}.kMDL{color:var(--gold)}
/* 直向/窄幅回退:panel 收頂 */
@media (max-width:820px){.layout{grid-template-columns:1fr}
.panel{position:static;height:auto;border-right:none;border-bottom:1px solid var(--hair)}}</style></head><body>
<div class="mast" id="mast"><div class="seal">理</div><div>
<div class="mtitle">VIA 自動編號命名冊 <span class="badge">TOOL-047</span></div>
<div class="msub">正典對映 · 先發先得 append-only · 實體檔零改名(紅線)</div></div></div>
<div class="layout">
<aside class="panel" id="panel">
  <div class="grp"><h3>檢索</h3>
    <input id="q" placeholder="搜尋正典名/家族路徑…">
    <select id="kind"><option value="">ENG+MDL</option><option>ENG</option><option>MDL</option></select>
    <div class="muted" id="stat"></div></div>
  <div class="grp"><h3>SYS 子系統</h3><ul class="syslist" id="syslist"></ul></div>
  <div class="grp"><h3>冊況</h3><div class="muted" id="meta">LIB 全域冊 __NLIB__ 件<br>零 CDN 純本地<br>視覺鎖定:理印紙墨系</div></div>
</aside>
<main class="stage">
<div class="sweepbar" style="margin-bottom:.8rem"></div>
<table><thead><tr><th>正典名</th><th>SYS</th><th>類</th><th>家族(去版鍵)</th><th>版本數</th><th>CLS</th><th>FNC</th></tr></thead>
<tbody id="tb"></tbody></table>
</main>
</div>
<script>
const D=__DATA__;
const tb=document.getElementById('tb'),q=document.getElementById('q'),
 ki=document.getElementById('kind'),st=document.getElementById('stat'),sl=document.getElementById('syslist');
let SYS='';
const counts={};D.forEach(r=>counts[r.s]=(counts[r.s]||0)+1);
['',...Object.keys(counts).sort()].forEach(s=>{
 const li=document.createElement('li');li.dataset.sys=s;
 li.innerHTML=`<span>${s||'全部'}</span><span class="n">${s?counts[s]:D.length}</span>`;
 li.onclick=()=>{SYS=s;[...sl.children].forEach(x=>x.classList.toggle('on',x.dataset.sys===s));render()};
 sl.appendChild(li)});
sl.firstChild.classList.add('on');
function render(){const t=q.value.toLowerCase(),k=ki.value;
 const rows=D.filter(r=>(!SYS||r.s===SYS)&&(!k||r.k===k)&&(!t||r.c.toLowerCase().includes(t)||r.f.toLowerCase().includes(t)));
 tb.innerHTML=rows.slice(0,800).map(r=>`<tr><td>${r.c}</td><td>${r.s}</td><td class="k${r.k}">${r.k}</td><td class="muted">${r.f}</td><td>${r.n}</td><td>${r.cl}</td><td>${r.fn}</td></tr>`).join('');
 st.textContent=`${rows.length}/${D.length} 筆`+(rows.length>800?'(顯示前 800)':'')}
q.oninput=render;ki.onchange=render;render();
/* 標頭滾動自動隱藏:下滾隱、上滾現 */
let lastY=0;const mast=document.getElementById('mast');
addEventListener('scroll',()=>{const y=scrollY;
 mast.classList.toggle('hide',y>lastY&&y>80);lastY=y},{passive:true});
</script></body></html>"""
    html = html.replace("__DATA__", data).replace("__NLIB__", str(n_lib))
    UI.parent.mkdir(parents=True, exist_ok=True)
    UI.write_text(html, encoding="utf-8")


def selftest() -> int:
    print("=== 命名冊 v0102 · 單元測試六檢(合成冊,零觸正冊)===")
    fake = {
        "U1": {"rel": "functional modules/VRN/vrn_yfinance_fetcher_v0100.py", "subsystem": "VRN",
               "contract": {"classes": [{"name": "Fetcher"}], "functions": [{"name": "fetch"}], "imports": ["yfinance", "pandas"]}},
        "U2": {"rel": "supportive modules/registry/via_demo_tool_v0101.py", "subsystem": "SUPPORT",
               "contract": {"classes": [], "functions": [{"name": "main"}, {"name": "_hidden"}], "imports": ["json"]}},
    }
    reg: dict = {}
    s1 = assign(fake, reg)
    fam1 = "functional modules/VRN/vrn_yfinance_fetcher"
    checks = [("首輪新編 2", s1["new"] == 2)]
    checks.append(("正典名範例合致", reg["items"][fam1]["canonical"] == "VRN_ENG001_YfinanceFetcher"))
    # 冪等:重跑零新編零變動
    before = json.dumps(reg["items"], sort_keys=True)
    s2 = assign(fake, reg)
    checks.append(("冪等重跑零新編", s2["new"] == 0 and json.dumps(reg["items"], sort_keys=True) == before))
    # 家族新版本:號不變、members 增
    fake["U3"] = {"rel": "functional modules/VRN/vrn_yfinance_fetcher_v0101.py", "subsystem": "VRN",
                  "contract": {"functions": [{"name": "fetch"}, {"name": "retry"}], "imports": []}}
    assign(fake, reg)
    it = reg["items"][fam1]
    checks.append(("同家族新版共號", it["num"] == 1 and len(it["members"]) == 2))
    checks.append(("FNC append-only", it["fnc"]["fetch"] == "FNC001" and it["fnc"]["retry"] == "FNC002"))
    # 新家族取次號;私名不編;LIB 全域
    fake["U4"] = {"rel": "functional modules/VRN/vrn_other_tool.py", "subsystem": "VRN",
                  "contract": {"functions": [], "imports": ["pandas"]}}
    assign(fake, reg)
    n2 = reg["items"]["functional modules/VRN/vrn_other_tool"]["num"]
    checks.append(("新家族次號+私名不編+LIB 不重複",
                   n2 == 2 and "_hidden" not in reg["items"]["supportive modules/registry/via_demo_tool"]["fnc"]
                   and reg["libs"]["pandas"] == "LIB002"))
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n}/{len(checks)} 檢通過")
    return 0 if n == len(checks) else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    dry = "--dry" in argv
    if not IFACE.exists():
        print(f"[FAIL] 介面合約冊缺:{IFACE.name}(先跑 via-iface)")
        return 1
    iface = json.loads(IFACE.read_text(encoding="utf-8"))["modules"]
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {
        "schema": "VIA.NamingRegistry.v1", "policy": "append_only·先發先得·實體檔零改名(正典對映)"}
    stat = assign(iface, reg)
    n_it = len(reg["items"])
    print(f"=== 命名冊 v0102 · {'DRY(零寫入)' if dry else 'REGISTER'} ===")
    print(f"  [冊] 家族 {n_it} · 新編 {stat['new']} · 沿用 {stat['kept']} · CLS+{stat['cls_new']} · FNC+{stat['fnc_new']} · LIB {len(reg.get('libs', {}))}(+{stat['lib_new']})")
    by = {}
    for it in reg["items"].values():
        by[f"{it['sys']}_{it['kind']}"] = by.get(f"{it['sys']}_{it['kind']}", 0) + 1
    print("  [屬] " + " · ".join(f"{k}×{v}" for k, v in sorted(by.items())))
    if dry:
        print("  [dry] 冊/U-I 零寫入(誠實)")
        return 0
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    write_ui(reg)
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    (OUT / f"NAMEREG_{ts}.json").write_text(json.dumps({"ts": ts, "stat": stat, "families": n_it},
                                                       ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [寫] {REG.name}(append-only)+ U/I {UI.name} + 存證 NAMEREG_{ts}.json")
    print("  [紅線] 實體檔零改名——正典名屬對映;落地改名需操作員明確令")
    return 0


if __name__ == "__main__":
    sys.exit(main())

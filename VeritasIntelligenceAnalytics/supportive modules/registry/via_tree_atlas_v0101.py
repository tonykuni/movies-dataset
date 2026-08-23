#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_tree_atlas_v0101 — VIA 向右樹枝狀圖譜+環境工具矩陣+六級測試梯(TOOL-066)
--------------------------------------------------------------------
v0100→v0101:品牌銘言入刊頭(批34 Observa · Intellege · Praevide)。
====================================================================
操作員令(批27):VIA 向右樹枝狀 子系統→模組→引擎→CLS→FNC→LIB
樹枝狀架構;ENV LIB STATUS 環境工具矩陣;UNIT/INTEGRATION/SUBSYSTEM/
SYSTEM/USER-TEST/ACTIVATE 逐級 test debug till all work perfectly。

落地:
  ① 向右樹(HTML,理印紙墨):VIA 根 → 子系統 → 模組/引擎(kind)
     → 家族 canonical → CLS/FNC 展枝;LIB 冊獨立枝。<details> 巢狀
     摺疊,樹向右生長;各節點計數;搜尋框即時濾枝。
  ② ENV LIB STATUS:importlib.util.find_spec 安全探測(零 import
     執行)——STDLIB/INSTALLED/MISSING 三態矩陣+計數;缺件走
     via-install 同意閘補(誠實列,不代裝)。
  ③ 六級測試梯 --ladder:
     L1 UNIT        代表性引擎 selftest(更名/救援/字庫)
     L2 INTEGRATION VDF 輸出樞紐+族群圖規→樞紐落庫煙測
     L3 SUBSYSTEM   FlowSystem 14 檢+產品門面檢
     L4 SYSTEM      全域 grid --fast(動態最新)
     L5 USER-TEST   圖譜 HTML 結構檢(樹/矩陣/零 CDN)
     L6 ACTIVATE    產出圖譜+體檢摘要落 VIA_Reports
     各級誠實三態;任一 FAIL → rc1 不假綠。

用法:
  --build        產出向右樹圖譜 HTML+ENV 矩陣(預設)
  --env          ENV LIB STATUS 矩陣列印
  --ladder       六級測試梯全跑
  --selftest     八檢
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

import importlib.util
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
UI_PATH = REPORTS / "VIA_UI_TreeAtlas.html"
REG_PATH = HERE / "VIA_Naming_Registry_v0100.json"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

SYS_ZH = {"VRN": "個股報告", "VDF": "資料擷取", "VAP": "視覺資產", "FLOW": "資金流",
          "VME": "方法論引擎", "CHW": "晶片戰", "GRP": "族群指數", "CGC": "治理主控",
          "SUP": "支援模組", "VIA": "母系統", "PLG": "外掛", "OTHER": "其他"}


def load_reg() -> dict:
    return json.loads(REG_PATH.read_text(encoding="utf-8"))


def probe_lib(name: str) -> str:
    if name in sys.stdlib_module_names:
        return "STDLIB"
    try:
        return "INSTALLED" if importlib.util.find_spec(name) else "MISSING"
    except Exception:
        return "MISSING"


def env_matrix(reg: dict) -> dict:
    out = {}
    for lib, code in sorted(reg.get("libs", {}).items()):
        out[lib] = {"code": code, "status": probe_lib(lib)}
    return out


def active_items(reg: dict):
    for k, it in reg.get("items", {}).items():
        if not it.get("moved_to") and not it.get("reverted"):
            yield k, it


def build_tree_html(reg: dict, env: dict) -> str:
    by_sys: dict = {}
    for k, it in active_items(reg):
        by_sys.setdefault(it["sys"], {}).setdefault(it["kind"], []).append(it)
    n_fam = sum(len(v) for s in by_sys.values() for v in s.values())
    n_cls = sum(len(it.get("cls", {})) for s in by_sys.values() for v in s.values() for it in v)
    n_fnc = sum(len(it.get("fnc", {})) for s in by_sys.values() for v in s.values() for it in v)
    st = Counter(v["status"] for v in env.values())

    def fam_node(it):
        cls = it.get("cls", {})
        fnc = it.get("fnc", {})
        inner = ""
        if cls:
            rows = "".join(f"<li><code>{cid}</code> {nm}</li>"
                           for nm, cid in list(cls.items())[:12])
            more = f"<li>…另 {len(cls)-12}</li>" if len(cls) > 12 else ""
            inner += f"<details><summary>CLS ×{len(cls)}</summary><ul>{rows}{more}</ul></details>"
        if fnc:
            rows = "".join(f"<li><code>{fid}</code> {nm}()</li>"
                           for nm, fid in list(fnc.items())[:12])
            more = f"<li>…另 {len(fnc)-12}</li>" if len(fnc) > 12 else ""
            inner += f"<details><summary>FNC ×{len(fnc)}</summary><ul>{rows}{more}</ul></details>"
        mem = it["members"][0] if it.get("members") else ""
        return (f"<details class='fam'><summary><b>{it['canonical']}</b>"
                f" <span class='p'>{mem}</span></summary>{inner or '<ul><li>(無 CLS/FNC 合約)</li></ul>'}</details>")

    sys_html = ""
    for s in sorted(by_sys, key=lambda x: -sum(len(v) for v in by_sys[x].values())):
        kinds = by_sys[s]
        n = sum(len(v) for v in kinds.values())
        kind_html = ""
        for kd in sorted(kinds):
            fams = sorted(kinds[kd], key=lambda i: i["num"])
            kind_html += (f"<details><summary>{'引擎 ENG' if kd=='ENG' else '模組 MDL'}"
                          f" ×{len(fams)}</summary>" + "".join(fam_node(i) for i in fams) + "</details>")
        sys_html += (f"<details class='sys'><summary>{s} · {SYS_ZH.get(s, s)}"
                     f"({n} 家族)</summary>{kind_html}</details>")
    lib_rows = "".join(
        f"<tr class='st{v['status'][0]}'><td><code>{v['code']}</code></td><td>{lib}</td>"
        f"<td><span class='dot {'g' if v['status']!='MISSING' else 'r'}'></span>{v['status']}</td></tr>"
        for lib, v in env.items())
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Tree Atlas</title><style>
:root{{--paper:#f2f1ec;--card:#fbfaf7;--ink:#1b1a17;--seal:#9e2b25;--teal:#3c6660;
--green:#3d7a52;--gold:#8a6420;--hair:#dbd9d3}}
*{{box-sizing:border-box;margin:0}}body{{background:var(--paper);color:var(--ink);
font:12px/1.6 "Microsoft JhengHei","Noto Serif CJK TC",serif;padding:14px}}
h1{{font:600 20px/1.3 "Cormorant Garamond","Noto Serif CJK TC",serif}}
.mast{{background:var(--card);border:1px solid var(--hair);border-top:3px solid var(--seal);
padding:10px 14px;margin-bottom:10px}}
.grid{{display:grid;grid-template-columns:3fr 2fr;gap:12px}}
@media(max-width:820px){{.grid{{grid-template-columns:1fr}}}}
details{{margin:2px 0 2px 14px;border-left:2px solid var(--hair);padding-left:10px}}
details.sys{{margin-left:0;background:var(--card);border:1px solid var(--hair);
border-left:3px solid var(--teal);padding:6px 10px}}
summary{{cursor:pointer;user-select:none}}
details.fam summary b{{color:var(--teal)}}
.p{{color:#8a877f;font-size:11px;word-break:break-all}}
code{{font-family:Consolas,monospace;font-size:11px;color:var(--gold)}}
ul{{margin-left:26px}}
table{{width:100%;border-collapse:collapse;background:var(--card)}}
td,th{{border:1px solid var(--hair);padding:2px 6px;word-break:break-word}}
th{{background:#efede6}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}}
.dot.g{{background:var(--green)}}.dot.r{{background:var(--seal)}}
#q{{width:100%;padding:5px 8px;border:1px solid var(--hair);font:inherit;margin-bottom:8px}}
.hide{{display:none}}</style></head><body>
<div class="mast"><h1>VIA 向右樹枝狀圖譜 <span class="p">v0101 · {NOW}</span></h1>
<div class="motto" style="letter-spacing:.14em;color:var(--seal);font:600 11px/1.4 'Cormorant Garamond',serif">VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE</div>
<div>子系統 → 模組/引擎 → 家族 → CLS/FNC → LIB · 家族 {n_fam} · CLS {n_cls} · FNC {n_fnc}
· LIB {len(env)}(STDLIB {st.get('STDLIB',0)} · 已裝 {st.get('INSTALLED',0)} · 缺 {st.get('MISSING',0)})</div></div>
<div class="grid"><div>
<input id="q" placeholder="搜尋 canonical / 檔名(即時濾枝)">
{sys_html}
</div><div>
<h1 style="font-size:15px">ENV LIB STATUS 環境工具矩陣</h1>
<div class="p">find_spec 安全探測零執行;缺件 via-install 同意閘補(誠實不代裝)</div>
<table><tr><th>LIB#</th><th>名</th><th>態</th></tr>{lib_rows}</table>
</div></div>
<script>
document.getElementById('q').addEventListener('input', function() {{
  var v = this.value.toLowerCase();
  document.querySelectorAll('details.fam').forEach(function(d) {{
    d.classList.toggle('hide', v && d.textContent.toLowerCase().indexOf(v) < 0);
  }});
  if (v) document.querySelectorAll('details.sys,details.sys>details').forEach(
    function(d) {{ d.open = true; }});
}});
</script></body></html>"""


def cmd_build(quiet=False) -> int:
    reg = load_reg()
    env = env_matrix(reg)
    REPORTS.mkdir(parents=True, exist_ok=True)
    UI_PATH.write_text(build_tree_html(reg, env), encoding="utf-8")
    st = Counter(v["status"] for v in env.values())
    if not quiet:
        n_fam = sum(1 for _ in active_items(reg))
        print(f"  [圖譜] 家族 {n_fam} · LIB {len(env)}"
              f"(STDLIB {st.get('STDLIB',0)}/已裝 {st.get('INSTALLED',0)}/缺 {st.get('MISSING',0)})")
        print(f"  [出] {UI_PATH}")
    return 0


def cmd_env() -> int:
    env = env_matrix(load_reg())
    st = Counter(v["status"] for v in env.values())
    print(f"  [ENV] LIB {len(env)} · STDLIB {st.get('STDLIB',0)} · 已裝 {st.get('INSTALLED',0)}"
          f" · 缺 {st.get('MISSING',0)}")
    missing = [l for l, v in env.items() if v["status"] == "MISSING"]
    print("  [缺件] " + (" ".join(missing[:20]) + (f" …另{len(missing)-20}" if len(missing) > 20 else "")
                        if missing else "無"))
    print("  [補法] via-install <庫名>(同意閘;誠實不代裝)")
    return 0


def _run(argv, timeout=900):
    r = subprocess.run([sys.executable] + argv, capture_output=True,
                       text=True, timeout=timeout, cwd=str(VIA.parent))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _newest(pat, root):
    fs = sorted(root.glob(pat))
    return fs[-1] if fs else None


def cmd_ladder() -> int:
    res = []

    def level(name, fn):
        try:
            ok, note = fn()
            res.append((name, "OK" if ok else "FAIL", note))
            print(f"  [{'OK  ' if ok else 'FAIL'}] {name} · {note}")
        except Exception as e:
            res.append((name, "FAIL", str(e)))
            print(f"  [FAIL] {name} · {e}")

    def unit():
        n = 0
        for pat in ("CGC_MDL077_RenameEngine_v0*.py", "CGC_MDL076_SyntaxRescue_v0*.py"):
            eng = _newest(pat, HERE)
            rc, _ = _run([str(eng), "--selftest"])
            n += int(rc == 0)
        return n == 2, f"代表性引擎 selftest {n}/2"

    def integration():
        hub = _newest("VDF_ENG045_OutputHub_v0*.py", VIA / "functional modules/VDF")
        rc, _ = _run([str(hub), "--selftest"], timeout=600)
        return rc == 0, "VDF 輸出樞紐(跨格式六道)"

    def subsystem():
        fs = VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_selftest.py"
        rc1, _ = _run([str(fs)], timeout=600) if fs.exists() else (1, "")
        pu = _newest("CGC_MDL072_ProductUi_v0*.py", HERE)
        rc2, _ = _run([str(pu), "--selftest"], timeout=600)
        return rc1 == 0 and rc2 == 0, "FlowSystem 14 檢+產品門面"

    def system():
        g = _newest("CGC_MDL064_SelftestGrid_v0*.py", HERE)
        rc, out = _run([str(g), "--fast"], timeout=1800)
        tail = [l for l in out.splitlines() if "[計]" in l]
        return rc == 0 and "FAIL 0" in (tail[-1] if tail else ""), \
            (tail[-1].strip() if tail else "no summary")

    def usertest():
        cmd_build(quiet=True)
        html = UI_PATH.read_text(encoding="utf-8")
        ok = all(x in html for x in ("details", "ENV LIB STATUS", "搜尋")) \
            and "fonts.googleapis" not in html
        return ok, "圖譜結構(樹/矩陣/搜尋/零 CDN)"

    def activate():
        ev = REPORTS / "atlas_runs"
        ev.mkdir(parents=True, exist_ok=True)
        summary = {"ts": NOW, "levels": [(n, s) for n, s, _ in res]}
        (ev / f"LADDER_{NOW}.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        return True, f"圖譜+體檢摘要落 VIA_Reports/atlas_runs/LADDER_{NOW}.json"

    level("L1 UNIT", unit)
    level("L2 INTEGRATION", integration)
    level("L3 SUBSYSTEM", subsystem)
    level("L4 SYSTEM", system)
    level("L5 USER-TEST", usertest)
    level("L6 ACTIVATE", activate)
    n_fail = sum(1 for _, s, _ in res if s == "FAIL")
    print(f"  [計] 六級測試梯:OK {6 - n_fail} · FAIL {n_fail}(誠實不假綠)")
    return 0 if n_fail == 0 else 1


def selftest() -> int:
    ok, total = 0, 8
    reg = load_reg()
    if sum(1 for _ in active_items(reg)) > 1000:
        ok += 1; print("  [PASS] 命名冊載入(活躍家族>1000)")
    else:
        print("  [FAIL] 冊")
    env = env_matrix(reg)
    st = Counter(v["status"] for v in env.values())
    if st.get("STDLIB", 0) > 20 and st.get("INSTALLED", 0) > 5:
        ok += 1; print(f"  [PASS] ENV 探測三態(STDLIB {st.get('STDLIB',0)}/裝 {st.get('INSTALLED',0)}/缺 {st.get('MISSING',0)})")
    else:
        print("  [FAIL] ENV")
    if probe_lib("json") == "STDLIB" and probe_lib("no_such_lib_xyz") == "MISSING":
        ok += 1; print("  [PASS] find_spec 安全探測(零 import 執行)")
    else:
        print("  [FAIL] 探測")
    html = build_tree_html(reg, env)
    if all(x in html for x in ("details class='sys'", "CLS ×", "FNC ×", "ENV LIB STATUS")):
        ok += 1; print("  [PASS] 向右樹五層(子系統/kind/家族/CLS/FNC)+LIB 枝")
    else:
        print("  [FAIL] 樹")
    if "fonts.googleapis" not in html and "--seal:#9e2b25" in html:
        ok += 1; print("  [PASS] 理印視覺鎖+零 CDN")
    else:
        print("  [FAIL] 視覺")
    if "getElementById('q')" in html:
        ok += 1; print("  [PASS] 即時搜尋濾枝")
    else:
        print("  [FAIL] 搜尋")
    moved = sum(1 for _, it in reg["items"].items() if it.get("moved_to"))
    shown = sum(1 for _ in active_items(reg))
    if moved > 200 and shown + moved + sum(1 for _, i in reg["items"].items() if i.get("reverted")) >= len(reg["items"]):
        ok += 1; print(f"  [PASS] 更名鍵遷移相容(moved {moved} 不重複展枝)")
    else:
        print("  [FAIL] 遷移相容")
    if cmd_build(quiet=True) == 0 and UI_PATH.exists():
        ok += 1; print("  [PASS] 圖譜落檔")
    else:
        print("  [FAIL] 落檔")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    if "--env" in a:
        return cmd_env()
    if "--ladder" in a:
        return cmd_ladder()
    return cmd_build()


if __name__ == "__main__":
    raise SystemExit(main())

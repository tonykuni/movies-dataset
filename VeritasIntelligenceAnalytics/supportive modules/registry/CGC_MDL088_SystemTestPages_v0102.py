#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL088_SystemTestPages v0102(批349 Windows 路徑歸屬修) — 五系統測試結果分頁 UI(批163;via-syspages)
====================================================================
操作員令:UI 基本功能=版面與系統連動;每系統一頁測試結果(上到下
多指標),顯示引擎/庫×環境×紅黃綠三色現況;五系統(VIA Supportive
Toolkits/VIA Central Governance/VDF/VAP/VRN)**同一測試模板**;
版面未定前不雕視覺——字小、專業、自動化。
機制(零重測=連動存證):
  站表=grid 尾版 battery()(114 站含 path)× 最新 GRID_*.json 實跑
  存證(name join)→按引擎路徑自動歸屬五系統(+OTHER 附錄=
  GroupIndex 等 functional 未列系統,誠實不塞併)
  顏色:綠=OK/黃=SKIP(環境缺件誠實)/紅=FAIL
  環境列=python/平台+關鍵庫版本實測(importlib.metadata;缺=誠實)
  --fresh=重跑 grid 後再產頁;預設=讀最新存證(秒級)
產出:ui_support/VIA_UI_SystemTestPages_v0100.html(單檔分頁 tab)
用法:via-syspages run [--fresh] | --status | --selftest
v0100→v0101(批166):切換消費 CGC_MDL089 原始模板正主——CSS/三態
  色碼/六槽 section 全由 MDL089+token 冊(VIA_UI_TemplateSSOT)供給,
  本引擎內零寫死視覺值;版面定案後改 token 冊即全站換裝,不動引擎。
  資料層(battery×GRID 存證 join/歸屬判準/環境收割)零變更。
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
import platform
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_SystemTestPages_v0100.html"
GRID_RUNS = VIA / "VIA_Reports" / "selftest_runs"

SYSTEMS = [  # (key, 顯名;順序=操作員列序)
    ("SUP", "VIA Supportive Toolkits"),
    ("CGC", "VIA Central Governance"),
    ("VDF", "VDF 資料工廠"),
    ("VAP", "VAP 自動繪圖"),
    ("VRN", "VRN 報告智能"),
    ("OTHER", "其他功能系統(附錄)"),
]
KEY_LIBS = ("pandas", "numpy", "duckdb", "scikit-learn", "matplotlib",
            "jieba", "opencc-python-reimplemented", "requests", "pyarrow")
_CGC_RX = re.compile(r"CGC_MDL|Central|central|mother|autorun|command_center|"
                     r"governance|ssot|selftest_grid|conflict_guard", re.I)


def classify(path_str: str) -> str:
    """站→系統歸屬(路徑判準;誠實 OTHER 不塞併)"""
    p = (path_str or "").replace("\\", "/")  # 批349:Windows 反斜線路徑正規化(工作站實錄 VDF/VAP/VRN 全歸 OTHER)
    if "functional modules/VRN" in p:
        return "VRN"
    if "functional modules/VDF" in p:
        return "VDF"
    if "functional modules/VAP" in p:
        return "VAP"
    if "supportive modules" in p:
        return "CGC" if _CGC_RX.search(Path(p).stem or "") else "SUP"
    if p == "PYCODE":
        return "OTHER"
    return "OTHER"


def _grid_module():
    hits = sorted(HERE.glob("CGC_MDL064_SelftestGrid_v*.py"))
    spec = importlib.util.spec_from_file_location("via_grid_dyn88", hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules["via_grid_dyn88"] = m
    spec.loader.exec_module(m)
    return m, hits[-1].name


def _latest_grid_json() -> tuple[Path | None, list]:
    hits = sorted(GRID_RUNS.glob("GRID_*.json"))
    if not hits:
        return None, []
    d = json.loads(hits[-1].read_text(encoding="utf-8"))
    items = d if isinstance(d, list) else d.get("stations") or d.get("results") or []
    return hits[-1], items


def assemble() -> dict:
    """battery(path)×GRID 存證(state)name join→六區歸屬"""
    gm, grid_name = _grid_module()
    battery = gm.battery(fast=False)
    src, items = _latest_grid_json()
    state_by = {i["name"]: i for i in items}
    pages = {k: [] for k, _ in SYSTEMS}
    for b in battery:
        st = state_by.get(b["name"], {})
        pages[classify(str(b.get("path") or ""))].append({
            "name": b["name"],
            "engine": Path(str(b.get("path"))).name if b.get("path") and b["path"] != "PYCODE" else "內聯檢",
            "state": st.get("state", "UNTESTED"),
            "secs": st.get("secs"), "note": str(st.get("note", ""))[:110]})
    return {"grid": grid_name, "evidence": src.name if src else None,
            "evidence_missing": src is None, "pages": pages}


def harvest_env() -> dict:
    import importlib.metadata as md
    libs = {}
    for lib in KEY_LIBS:
        try:
            libs[lib] = md.version(lib)
        except Exception:
            libs[lib] = "缺(誠實)"
    return {"python": platform.python_version(), "platform": platform.platform(terse=True),
            "libs": libs}


def _mdl089():
    """glob 尾版動態載入 CGC_MDL089 原始模板正主(token 冊+CSS+六槽 render)"""
    p = sorted(HERE.glob("CGC_MDL089_UIBaseTemplate_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("cgc_mdl089", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["cgc_mdl089"] = m
    spec.loader.exec_module(m)
    return m


def build_ui(data: dict, env: dict) -> Path:
    """v0101:視覺全數委派 MDL089 模板正主(CSS 純 token 冊生成+
    六槽 render_section);本引擎零寫死視覺值=改冊即全站換裝"""
    T = _mdl089()
    tokens = T.load_tokens()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tabs = "".join(
        f'<button class="tab" onclick="show(\'{k}\')" id="tab-{k}">{t.split("(")[0]}'
        f'<b>{len(data["pages"][k])}</b></button>'
        for k, t in SYSTEMS if data["pages"][k])
    pages = "".join(T.render_section(k, t, data["pages"][k], env, tokens)
                    for k, t in SYSTEMS if data["pages"][k])
    warn = ('<div class="warn">⚠ 無 GRID 存證(先跑 via-selftest)=各站 UNTESTED 誠實</div>'
            if data["evidence_missing"] else "")
    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 系統測試分頁 v0101</title><style>{T.base_css(tokens)}</style></head>
<body><div class="wrap">
<h1>VIA 系統測試分頁(五系統同一模板)</h1>
<div class="mut">批166 · {ts} · grid={data['grid']} · 存證={data['evidence']} ·
模板正主={T.SSOT.name} · 綠=OK/黃=SKIP 環境缺件誠實/紅=FAIL</div>
{warn}
<div class="tabs">{tabs}</div>
{pages}
<div class="foot">視覺單源=token 冊(改冊即全站換裝,不動引擎)· 頁面=存證
join 零重測 · 誠實三態:黃 SKIP 不假綠/灰 UNTESTED 不假測</div>
<script>
function show(k){{document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
document.getElementById(k).classList.add('on');
document.getElementById('tab-'+k).classList.add('on');}}
show('SUP');
</script></div></body></html>"""
    UI_OUT.write_text(html, encoding="utf-8")
    return UI_OUT


def run(fresh: bool = False) -> int:
    if fresh:
        gm_path = sorted(HERE.glob("CGC_MDL064_SelftestGrid_v*.py"))[-1]
        print(f"[fresh] 重跑 grid {gm_path.name}(數分鐘)…", flush=True)
        subprocess.run([sys.executable, str(gm_path)], cwd=HERE)
    data = assemble()
    env = harvest_env()
    for k, t in SYSTEMS:
        rows = data["pages"][k]
        if not rows:
            continue
        ok = sum(1 for r in rows if r["state"] == "OK")
        fail = sum(1 for r in rows if r["state"] == "FAIL")
        skip = sum(1 for r in rows if r["state"] == "SKIP")
        print(f"  [{k}] {t}:{len(rows)} 站 · 綠 {ok} 黃 {skip} 紅 {fail}")
    p = build_ui(data, env)
    print(f"[UI] {p.name} · 存證 {data['evidence']}")
    return 0


def status() -> int:
    src, items = _latest_grid_json()
    print(f"UI={'在' if UI_OUT.exists() else '未生'} · 最新存證={src.name if src else '缺'}"
          f"({len(items)} 站)")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① grid 尾版+GRID 存證在位",
        bool(sorted(HERE.glob("CGC_MDL064_SelftestGrid_v*.py")))
        and _latest_grid_json()[0] is not None)
    chk("② 歸屬判準真值(五系統+OTHER)",
        classify("x/functional modules/VRN/a.py") == "VRN"
        and classify("x/functional modules/VDF/engine/a.py") == "VDF"
        and classify("x/functional modules/VAP/engine/a.py") == "VAP"
        and classify("x/supportive modules/registry/CGC_MDL064_SelftestGrid_v1.py") == "CGC"
        and classify("x/supportive modules/network/SUP_MDL740_NetUnified_v1.py") == "SUP"
        and classify("x/functional modules/GroupIndex/engine/a.py") == "OTHER"
        and classify("C:\\x\\functional modules\\VDF\\engine\\a.py") == "VDF")
    data = assemble()
    n = sum(len(v) for v in data["pages"].values())
    chk("③ 站表合流(battery×存證 join≥110 站)", n >= 110,
        f"({n} 站·存證 {data['evidence']})")
    chk("④ 五系統皆有站(SUP/CGC/VDF/VAP/VRN 非空)",
        all(data["pages"][k] for k in ("SUP", "CGC", "VDF", "VAP", "VRN")),
        f"({ {k: len(v) for k, v in data['pages'].items()} })")
    env = harvest_env()
    chk("⑤ 環境收割(python+關鍵庫版本;缺=誠實)",
        env["python"] and sum(1 for v in env["libs"].values() if "缺" not in v) >= 5)
    import tempfile
    global UI_OUT
    _u = UI_OUT
    with tempfile.TemporaryDirectory() as td:
        UI_OUT = Path(td) / "ui.html"
        p = build_ui(data, env)
        h = p.read_text(encoding="utf-8")
        chk("⑥ 同一模板五頁(render_page 同構;section×tab 對齊)",
            h.count('<section id=') >= 5 and h.count('class="tab"') >= 5
            and h.count("多指標,上→下") >= 5)
        T = _mdl089()
        tk = T.load_tokens()
        chk("⑦ 三色+響應式(色碼=token 冊值+冊定字級+viewport+auto wrap)",
            all(c in h for c in tk["status"].values())
            and tk["font"]["fs"] in h and "viewport" in h
            and "overflow-wrap:anywhere" in h)
        _src = Path(__file__).read_text(encoding="utf-8")
        chk("⑨ 模板正主消費(CSS 純冊生成+卡片化媒體查詢+本檔零寫死視覺)",
            tk["palette"]["bg"] in h and "table.cards" in h
            and T.SSOT.name in h
            and not any(v in _src for v in tk["status"].values())
            and tk["palette"]["bg"] not in _src)
    UI_OUT = _u
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(同一測試模板/誠實 OTHER/存證連動零重測/改冊不動引擎)",
        all(k in src for k in ("同一測試模板", "OTHER 不塞併", "存證", "改冊即全站換裝")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 五系統測試分頁(CGC_MDL088 v0101)· 九檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "run" in args:
        return run(fresh="--fresh" in args)
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())

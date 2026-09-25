#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL114_CommandCenterBridge — AIO 指揮中心收容橋(批288;操作員令)
====================================================================
操作員令:「繼續完成整合」+ VIA_CommandCenter_AutoCatchSync_AIO
v0.2.0 收容件。AIO 獨門=逐引擎 14 閘靜態驗證+AST 契約抽取
(入口點/參數/依賴/輸出推定)——與現役互補:
  MDL112 Atlas=名冊層/MDL113 統一編號=編號層/本橋=契約+健康層。
收容律=原件不動,本橋駕馭:
  ①掛載 intake 原件(importlib 動態載入=零複製)
  ②域調校:IGNORE 加 VIA 特例(intake/_retired/ASSETS/SCOPE_COPY/
    output_hub/fixtures=收容凍結與資料區不掃)+runtime 產物區
    gitignore(再生類)
  ③auto 靜態全鏈(scan→sync→14 閘 validate-all;零 smoke=唯讀
    紀律)→六矩陣落 runtime_command_center/
  ④摘要頁 VIA_UI_CommandCenter_v0100.html(健康分佈+紅件誠實列)
  ⑤指揮中心家族 CANDIDATE_MERGE 入整併冊(vs MDL095/112/113;
    候裁示零破壞)
用法:python3 CGC_MDL114_CommandCenterBridge_v0100.py run | probe
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

import html
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
AIO = (HERE.parent / "references" / "intake" / "VIA_CommandCenter_AIO_b288"
       / "VIA_CommandCenter_AutoCatchSync_AIO_v0200.py")
OUT = (VIA / "supportive modules" / "ui_support"
       / "VIA_UI_CommandCenter_v0100.html")
EXTRA_IGNORE = {"references", "intake", "_retired_b280", "ASSETS",
                "SCOPE_COPY", "fixtures", "output_hub", "vap_images",
                "md_out", "components", "runtime_command_center",
                "detection", "__pycache__"}


def _mount():
    if not AIO.exists():
        return None
    spec = importlib.util.spec_from_file_location("via_cc_aio", AIO)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.IGNORE_DIRS = set(m.IGNORE_DIRS) | EXTRA_IGNORE  # 域調校(不改原件)
    return m


def probe() -> dict:
    m = _mount()
    if m is None:
        return {"ok": False, "err": "intake 缺=誠實停"}
    return {"ok": True, "app": m.APP_NAME, "version": m.APP_VERSION,
            "gates": 14, "ignore_extra": sorted(EXTRA_IGNORE)}


def run() -> int:
    m = _mount()
    if m is None:
        print("[指中橋] intake 缺=誠實停")
        return 2
    engines = m.def_sync_registry(VIA)
    validated = [m.def_validate_engine(e, smoke=False) for e in engines]
    m.def_save_registry(VIA, validated)
    m.def_export_reports(VIA, validated)
    s = m.def_summary(validated)
    reds = [e for e in validated if e.health == "FAILED"][:20]
    OUT.write_text(render(s, reds), encoding="utf-8")
    print(f"[指中橋] {m.APP_VERSION} · 掃 {s['total']} 件 · HEALTHY "
          f"{s['healthy']} · DEGRADED {s['degraded']} · FAILED "
          f"{s['failed']} · 均分 {s['average_score']}% · 六矩陣落 "
          f"runtime_command_center/ · {OUT.name}")
    return 0


def render(s: dict, reds: list) -> str:
    sub_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>"
        for k, v in sorted(s["by_subsystem"].items(), key=lambda kv: -kv[1]))
    red_rows = "".join(
        f"<tr><td>{html.escape(e.name)}</td>"
        f"<td>{html.escape(e.subsystem)}</td><td>{e.score}%</td></tr>"
        for e in reds) or "<tr><td colspan=3>FAILED 0=全綠</td></tr>"
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 指揮中心健康總圖</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8;--green:#5a9e6f;--red:#c96b5a}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--blue:#7ba3cc;
--green:#79b58c;--red:#d98a7c}}}}
body{{background:var(--bg);color:var(--text);margin:0 auto;
font:12.5px/1.5 "Segoe UI","Noto Sans TC",sans-serif;padding:16px;
max-width:860px}}
h1{{font-size:16px}}h2{{font-size:11px;color:var(--muted);
text-transform:uppercase;letter-spacing:.08em;margin:14px 0 6px}}
.sub{{color:var(--muted);font-size:11px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;
margin:10px 0}}
.kpi{{background:var(--panel);border:1px solid var(--line);
border-radius:8px;padding:10px;border-left:3px solid var(--green)}}
.kpi b{{font-size:20px}}.kpi small{{display:block;color:var(--muted)}}
table{{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:8px}}
td,th{{padding:5px 8px;border-bottom:1px solid var(--line);
text-align:left;font-variant-numeric:tabular-nums;
overflow-wrap:anywhere}}
th{{font-size:10px;color:var(--muted)}}
.wrap{{overflow-x:auto}}
@media(max-width:640px){{.kpis{{grid-template-columns:1fr 1fr}}}}
</style></head><body>
<h1>指揮中心健康總圖(批288)</h1>
<div class="sub">{s['generated_at']} · AIO v{s['version']} 收容橋 ·
14 閘靜態驗證(零 smoke=唯讀紀律)· 契約層=AST 入口/參數/依賴/
輸出推定 · 六矩陣 CSV/JSON 落 runtime_command_center/</div>
<div class="kpis">
<div class="kpi"><b>{s['total']}</b><small>掃描件</small></div>
<div class="kpi"><b>{s['healthy']}</b><small>HEALTHY</small></div>
<div class="kpi"><b>{s['degraded']}</b><small>DEGRADED</small></div>
<div class="kpi"><b>{s['average_score']}%</b><small>均分</small></div>
</div>
<h2>子系統分佈</h2><div class="wrap"><table>
<tr><th>子系統</th><th>件數</th></tr>{sub_rows}</table></div>
<h2>FAILED 誠實列(前 20)</h2><div class="wrap"><table>
<tr><th>件</th><th>子系統</th><th>分</th></tr>{red_rows}</table></div>
<p class="sub">家族界定:MDL112=名冊/MDL113=編號/本橋=契約+健康;
CANDIDATE_MERGE 入整併冊候裁示 · 零網路零 CDN</p></body></html>"""


def register_merge() -> str:
    cons = HERE / "VIA_Engine_Consolidation_Register_v0100.json"
    if not cons.exists():
        return "冊缺=誠實略"
    d = json.loads(cons.read_text(encoding="utf-8"))
    key = "command_center_family_b288"
    lst = d.get("candidate_merges_b256")
    if not isinstance(lst, list):
        lst = d.setdefault("candidates", [])
    if any(isinstance(e, dict) and e.get("key") == key for e in lst):
        return "SKIP_IDENTICAL"
    lst.append({"key": key,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "family": "指揮中心/清冊",
                "members": ["AIO CommandCenter v0.2.0(收容;14 閘+契約)",
                            "CGC_MDL095 DeckServer(執行樞紐)",
                            "CGC_MDL112 Atlas(名冊)",
                            "CGC_MDL113 UnifiedRegistry(編號)"],
                "rule": "不失功能重新註冊;候操作員裁示,零破壞"})
    cons.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    return "REGISTERED"


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    p = probe()
    chk("① 收容在位+掛載(v0.2.0+域調校 IGNORE)",
        p.get("version") == "0.2.0"
        and (AIO.parent / "_INTAKE_MANIFEST.json").exists())
    rc = run()
    rt = VIA / "runtime_command_center"
    chk("② auto 靜態全鏈(scan→14 閘 validate-all 零 smoke)rc0",
        rc == 0 and (rt / "engine_registry.json").exists())
    reg = json.loads((rt / "engine_registry.json")
                     .read_text(encoding="utf-8"))
    chk("③ 契約抽取真值(>200 件;入口/依賴欄在)",
        reg["count"] > 200
        and all(k in reg["engines"][0]
                for k in ("entry_points", "dependencies", "parameters")))
    summ = json.loads((rt / "summary.json").read_text(encoding="utf-8"))
    chk("④ 六矩陣落盤+摘要頁(健康分佈+FAILED 誠實列)",
        all((rt / f).exists() for f in
            ("validation_matrix.json", "validation_matrix.csv",
             "summary.json", "inputs_matrix.csv", "status_matrix.csv",
             "outputs_matrix.csv"))
        and OUT.exists() and str(summ["total"]) in
        OUT.read_text(encoding="utf-8"))
    r = register_merge()
    chk("⑤ 指揮中心家族整併冊登記(冪等)",
        r in ("REGISTERED", "SKIP_IDENTICAL")
        and register_merge() == "SKIP_IDENTICAL")
    chk("⑥ 唯讀紀律(零 smoke 宣告+原件不動)+零網路+加速橋",
        "smoke=False" in src and "原件不動" in src
        and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 指揮中心收容橋(CGC_MDL114)· 六檢自測(零網路)===")
        return selftest()
    if "probe" in a:
        print(json.dumps(probe(), ensure_ascii=False, indent=1))
        return 0
    return run()


if __name__ == "__main__":
    sys.exit(main())

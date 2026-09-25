#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL102_CommandRoster — 新舊指令整合冊(批249;操作員令「整合新舊
指令簡化優化」)
====================================================================
機制(全動態盤點;嚴禁寫死版號):
  ①正道短指令:VIA.ps1 Register-Profile 段 function 名實掃(regen-all
    /via/via-status/selftest/via-intake…=現行 profile 註冊)
  ②檔級啟動器:根夾+VDF/VAP *.ps1 Invoke-*/Collect-* 盤點(舊代=
    檔案直呼;標 LEGACY_FILE)
  ③引擎 CLI:engine/registry 尾版引擎之 run/scan/probe 動詞
    (docstring 用法行實抽)
  輸出=VIA_UI_CommandRoster_v0100.html 一頁冊(新/舊分區+來源+
    尾版檔名)+--print 終端表(via-help 接此)
用法:python3 CGC_MDL102_CommandRoster_v0100.py [--print] | --selftest
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
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_CommandRoster_v0100.html"

DESC = {"regen-all": "重生全部 UI 頁(MDL096 統一道)",
        "via": "一鍵啟動(同步+日更+回補+Portal)",
        "via-status": "開同步狀態台",
        "via-selftest": "全面自測矩陣(grid 尾版)",
        "selftest": "= via-selftest 別名",
        "via-intake": "Downloads 名冊收容器(尾版)",
        "via-help": "本指令冊(終端表)"}


def profile_cmds() -> list[dict]:
    """①正道:VIA.ps1 Register-Profile 段 function 實掃"""
    src = (VIA / "VIA.ps1").read_text(encoding="utf-8", errors="replace")
    out = []
    for m in re.finditer(r"^function ([a-z][a-z0-9-]*)\s*\{(.*)$",
                         src, re.M):
        out.append({"cmd": m.group(1), "kind": "PROFILE(正道)",
                    "src": "VIA.ps1 Register-Profile",
                    "note": DESC.get(m.group(1), m.group(2).strip()[:70])})
    return out


def launcher_cmds() -> list[dict]:
    """②檔級啟動器(舊代=檔案直呼)"""
    out = []
    pools = [VIA, VIA / "functional modules" / "VDF",
             VIA / "functional modules" / "VAP"]
    for root in pools:
        for p in sorted(root.glob("*.ps1")):
            if p.name == "VIA.ps1":
                continue
            out.append({"cmd": p.stem, "kind": "LEGACY_FILE(檔呼)",
                        "src": str(p.relative_to(VIA)),
                        "note": "pwsh -File 直呼(候整併正道)"})
    return out


def engine_verbs() -> list[dict]:
    """③引擎 CLI 動詞(尾版引擎 docstring 用法行實抽)"""
    out = []
    best: dict[str, Path] = {}
    for pool in (HERE, VIA / "functional modules" / "VRN",
                 VIA / "functional modules" / "VDF" / "engine",
                 VIA / "functional modules" / "VAP" / "engine"):
        for p in sorted(pool.glob("*_v0*.py")):
            stem = p.stem.rsplit("_v", 1)[0]
            best[stem] = p                     # sorted=尾版覆蓋
    for stem, p in sorted(best.items()):
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:3000]
        except Exception:
            continue
        m = re.search(r"用法:(?:python3?|py) \S+ ([^\n|]+)", head)
        if m:
            out.append({"cmd": stem.split("_", 1)[-1], "kind": "ENGINE_CLI",
                        "src": p.name, "note": m.group(1).strip()[:70]})
    return out


def gather() -> dict:
    return {"profile": profile_cmds(), "legacy": launcher_cmds(),
            "engines": engine_verbs()}


def render(data: dict) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    def table(rows):
        return ("<table><thead><tr><th>指令</th><th>類</th><th>來源(尾版)"
                "</th><th>說明</th></tr></thead><tbody>" + "".join(
                    f"<tr><td><b>{html.escape(r['cmd'])}</b></td>"
                    f"<td>{html.escape(r['kind'])}</td>"
                    f"<td>{html.escape(r['src'])}</td>"
                    f"<td>{html.escape(r['note'])}</td></tr>"
                    for r in rows) + "</tbody></table>")
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 指令冊 · 新舊整合</title><style>
body{{background:#0b1220;color:#c7d3e8;font:10.5px/1.5 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px;max-width:1180px;margin:0 auto}}
h1{{font-size:14px;color:#e8eefb}}h2{{font-size:11.5px;color:#4f8ef7;margin:12px 0 4px}}
.sub{{color:#7e8db0;font-size:10px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:#7e8db0;font-size:9.5px;border-bottom:1px solid #1e2a44;padding:2px 6px 2px 0}}
td{{padding:2px 6px 2px 0;border-bottom:1px dashed #1e2a44;overflow-wrap:anywhere}}
</style></head><body>
<h1>VIA 指令冊(新舊整合;批249)</h1>
<div class="sub">{ts} · 正道={len(data['profile'])} · 舊代檔呼=
{len(data['legacy'])} · 引擎 CLI={len(data['engines'])} · 全動態盤點
(嚴禁寫死版號)· 簡化原則:新視窗打短指令=正道;檔呼=候整併</div>
<h2>① 正道短指令(profile 註冊;任何新 PS 視窗直打)</h2>
{table(data['profile'])}
<h2>② 引擎 CLI(尾版動態;python 檔呼)</h2>
{table(data['engines'])}
<h2>③ 舊代檔級啟動器(LEGACY;候整併)</h2>
{table(data['legacy'])}
</body></html>"""


def run(do_print: bool = False) -> int:
    data = gather()
    OUT.write_text(render(data), encoding="utf-8")
    print(f"[指令冊] 正道 {len(data['profile'])} · 引擎 CLI "
          f"{len(data['engines'])} · 舊代 {len(data['legacy'])} · {OUT.name}")
    if do_print:
        for sec, rows in (("正道", data["profile"]),
                          ("引擎", data["engines"])):
            for r in rows:
                print(f"  [{sec}] {r['cmd']:<28} {r['note'][:60]}")
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
    data = gather()
    chk("① 正道短指令實掃(selftest/via-intake 在冊)", rc == 0
        and {r["cmd"] for r in data["profile"]} >=
        {"regen-all", "via", "selftest", "via-intake"})
    chk("② 引擎 CLI 尾版動態(rsplit _v 取尾;ENG075 在冊)",
        any("ENG075" in r["src"] for r in data["engines"])
        and "rsplit" in src)
    chk("③ 舊代檔呼盤點(Collect-VIA-Intake 尾版在)",
        any("Collect-VIA-Intake" in r["cmd"] for r in data["legacy"]))
    chk("④ 三分區頁產出+簡化原則宣告",
        all(k in page for k in ("① 正道短指令", "② 引擎 CLI",
                                "③ 舊代檔級啟動器", "候整併")))
    chk("⑤ 零 CDN+小字", 'src="http' not in page and "10.5px" in page)
    chk("⑥ 零網路+加速橋",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 指令整合冊(CGC_MDL102)· 六檢自測(零網路)===")
        return selftest()
    return run("--print" in args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL125_LifecycleRACI — 生命週期角色責任引擎(批344;操作員令「GitHub/PC/引擎/資料
角色責任;回測→優化→修改→整併→除錯→使用者測→啟用→完美 之閉環;最低 token」)
====================================================================
職權:
  ①讀 VIA_LifecycleRACI_v*.json(六角色×九階段 RACI;每階段=證據來源+閘+下一步)
  ②真證直取(零發明):git HEAD/dirty · DB 三檔 · 最新 six_streams.json · 最新 probe.json
    · 引擎版本檔在位 · 門檻冊/總冊在位;缺=誠實 UNKNOWN
  ③依閘判定目前階段與唯一下一步(機制:每次只推進一格;閘不過=回指定階段)
  ④digest:≤25 行純文字(via-loop 直印;操作員貼此即可,零整段 log)
    NEED_LOG:<path> 只在必要時指一檔;助理讀 digest 判下一版
  ⑤頁:VIA_UI_LifecycleRACI_v0100.html(左=角色卡;右=九階段頁籤;RACI 矩陣;燈號)
v0100→v0101(批347):產物經 apply_type_scale;自測 +⑧
用法:python3 CGC_MDL125_LifecycleRACI_v0101.py [digest|page|--open] [--selftest]
"""
from __future__ import annotations
import glob
import hashlib
import html
import json
import re
import os
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"
OUT = UI / "VIA_UI_LifecycleRACI_v0100.html"
DIGEST = VIA / "VIA_Reports" / "loop" / "DIGEST_latest.txt"



# ===== 批347 字階守恆(全頁族統一;來源=VIA_UISpec 尾版六階;越階值就近收斂到階) =====
def _type_scale():
    try:
        import json as _j
        c = sorted(Path(__file__).resolve().parent.glob("VIA_UISpec_v*.json"))
        th = _j.loads(c[-1].read_text(encoding="utf-8")).get("theme", {}) if c else {}
        steps = [("fs_xs", 9.0), ("fs_s", 10.5), ("fs", 11.5), ("fs_m", 12.5), ("fs_l", 14.0), ("fs_xl", 16.0)]
        return [(k, float(str(th.get(k, d)).replace("px", ""))) for k, d in steps]
    except Exception:
        return [("fs_xs", 9.0), ("fs_s", 10.5), ("fs", 11.5), ("fs_m", 12.5), ("fs_l", 14.0), ("fs_xl", 16.0)]


def apply_type_scale(page: str) -> str:
    """把 <style> 內所有 px 字級收斂到六階(最大 fs_xl);inline style 同理;零其他改動"""
    steps = _type_scale()
    def snap(v):
        v = float(v)
        for k, px in steps:
            if v <= px:
                return px
        return steps[-1][1]
    def fmt(x):
        return (str(x).rstrip("0").rstrip(".") if "." in str(x) else str(x)) + "px"
    def fix_style(m):
        css = m.group(1)
        css = re.sub(r"(font-size\s*:\s*)([0-9.]+)px", lambda x: x.group(1) + fmt(snap(x.group(2))), css)
        css = re.sub(r"(font\s*:\s*)([0-9.]+)px", lambda x: x.group(1) + fmt(snap(x.group(2))), css)
        return "<style>" + css + "</style>"
    page = re.sub(r"<style>(.*?)</style>", fix_style, page, flags=re.S)
    page = re.sub(r'(style="[^"]*font-size\s*:\s*)([0-9.]+)px', lambda x: x.group(1) + fmt(snap(x.group(2))), page)
    # JS-built elements (cssText strings) carry font:NNpx too; snap them so the runtime DOM obeys the scale
    page = re.sub(r"(font(?:-size)?\s*:\s*)([0-9.]+)px", lambda x: x.group(1) + fmt(snap(x.group(2))), page)
    return page

def _raci() -> dict:
    c = sorted(HERE.glob("VIA_LifecycleRACI_v*.json"))
    return json.loads(c[-1].read_text(encoding="utf-8")) if c else {}


def _git(*args) -> str:
    try:
        r = subprocess.run(["git", "-C", str(VIA), *args], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _latest_json(rel_glob: str) -> tuple[str, dict]:
    hits = sorted(glob.glob(str(VIA / rel_glob)))
    if not hits:
        return "", {}
    try:
        return hits[-1], json.loads(Path(hits[-1]).read_text(encoding="utf-8"))
    except Exception:
        return hits[-1], {}


# ---------------------------------------------------------------------
# 真證
# ---------------------------------------------------------------------
def evidence() -> dict:
    ev = {}
    ev["head"] = _git("log", "-1", "--format=%h %ad %s", "--date=short")[:90] or "UNKNOWN(git 缺或非 repo)"
    ev["remote_ahead"] = _git("rev-list", "--count", "@{u}..HEAD") or "?"
    dirty = _git("status", "--porcelain")
    ev["dirty"] = len([l for l in dirty.splitlines() if l.strip()]) if dirty != "" else 0
    dbs = ["functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb",
           "functional modules/VDF/output_hub/mega/vdf_global_market.duckdb",
           "functional modules/VDF/output_hub/ActiveTWETF.duckdb"]
    ev["db_present"] = sum(1 for d in dbs if (VIA / d).exists())
    ev["db_total"] = len(dbs)
    p6, j6 = _latest_json("VIA_Reports/six_streams/RUN_*/six_streams.json")
    ev["six"] = {"path": p6, "overall": j6.get("overall", "NONE"), "stamp": j6.get("stamp", ""),
                 "red": [s["id"] for s in j6.get("streams", []) if s.get("state") == "RED"],
                 "yellow": [s["id"] for s in j6.get("streams", []) if s.get("state") in ("YELLOW", "MISSING")]}
    pp, jp = _latest_json("VIA_Reports/charter_probe/PROBE_*/probe.json")
    steps = jp.get("steps", [])
    ev["probe"] = {"path": pp, "mode": jp.get("mode", "NONE"), "stamp": jp.get("stamp", ""),
                   "ok": sum(1 for s in steps if s.get("state") == "OK"),
                   "fail": sum(1 for s in steps if s.get("state") in ("FAIL", "ERROR")),
                   "timeout": sum(1 for s in steps if s.get("state") == "TIMEOUT"),
                   "planned": sum(1 for s in steps if s.get("state") == "PLANNED"),
                   "logs": [s.get("log", "") for s in steps if s.get("state") in ("FAIL", "TIMEOUT", "ERROR") and s.get("log")]}
    reg = VIA / "supportive modules" / "registry"
    ev["engines"] = {k: bool(sorted(reg.glob(k))) for k in
                     ("CGC_MDL095_DeckServer_v0*.py", "CGC_MDL116_UnifiedShell_v0*.py", "CGC_MDL122_IntakeRoster_v0*.py",
                      "CGC_MDL123_SixStreams_v0*.py", "CGC_MDL124_SystemCharter_v0*.py", "VIA_ShellValidation_Thresholds_v*.json",
                      "VIA_SystemCharter_v*.json", "CGC_MDL115_SSOTRegexDict_v0*.py")}
    ev["engines_present"] = sum(ev["engines"].values())
    ev["engines_total"] = len(ev["engines"])
    ch = sorted(UI.glob("VIA_UI_SystemCharter_v0100.html"))
    ev["charter_page"] = bool(ch)
    # drift ledger (from Unified runs) if any
    dl = sorted(glob.glob(str(VIA / "VIA_Reports" / "six_streams" / "RUN_*" / "S1_unified" / "UNIFIED_*" / "drift_ledger.csv")))
    ev["drift_families"] = None
    if dl:
        try:
            names = {l.split(",")[0] for l in Path(dl[-1]).read_text(encoding="utf-8").splitlines()[1:] if l.strip()}
            ev["drift_families"] = len(names)
        except Exception:
            pass
    return ev


# ---------------------------------------------------------------------
# 機制:閘判定→目前階段→唯一下一步
# ---------------------------------------------------------------------
def decide(ev: dict) -> dict:
    blockers = []
    need_log = "none"
    # S0 intake gate
    if ev["engines_present"] < ev["engines_total"]:
        missing = [k for k, v in ev["engines"].items() if not v]
        blockers.append(f"registry 缺 {len(missing)}: " + ", ".join(m.split('_v0')[0] for m in missing[:3]))
    if ev["db_present"] < ev["db_total"]:
        blockers.append(f"DB {ev['db_present']}/{ev['db_total']}(本機 output_hub/mega)")
    if blockers:
        return {"stage": "S0", "gate": "FAIL", "blockers": blockers,
                "next": "上船:複製缺檔至 registry;確認 DuckDB 三檔在 output_hub;再 via-loop", "need_log": need_log}
    # S1 backtest gate (probe)
    if ev["probe"]["mode"] == "NONE":
        return {"stage": "S1", "gate": "PENDING", "blockers": ["尚無兩日試鏈紀錄"],
                "next": "via-charter --probe --days 2 --go(12 步;各步逾時 30 分)", "need_log": need_log}
    if ev["probe"]["mode"].startswith("PLAN"):
        return {"stage": "S1", "gate": "PENDING", "blockers": ["試鏈只有計畫未派工"],
                "next": "via-charter --probe --days 2 --go", "need_log": need_log}
    if ev["probe"]["timeout"] or ev["probe"]["fail"]:
        need_log = ev["probe"]["logs"][0] if ev["probe"]["logs"] else "none"
        return {"stage": "S5", "gate": "FAIL", "blockers": [f"試鏈 fail {ev['probe']['fail']} timeout {ev['probe']['timeout']}"],
                "next": "除錯:貼 NEED_LOG 那一檔尾 30 行;助理出該引擎 vNNNN+1", "need_log": need_log}
    # S5 debug gate (six streams)
    if ev["six"]["overall"] == "NONE":
        return {"stage": "S5", "gate": "PENDING", "blockers": ["尚無 via-six 矩陣"], "next": "via-six", "need_log": need_log}
    if ev["six"]["overall"] == "RED":
        return {"stage": "S5", "gate": "FAIL", "blockers": ["six RED: " + ",".join(ev["six"]["red"])],
                "next": "除錯逾時流程:看 " + (ev["six"]["path"].replace("six_streams.json", "logs/") if ev["six"]["path"] else "logs"), "need_log": need_log}
    # S6 usertest: operator must state it; unknown → ask (cheapest possible)
    # S7 activate gate
    if ev["dirty"] > 0 or (ev["remote_ahead"] not in ("0", "?") ):
        return {"stage": "S7", "gate": "PENDING",
                "blockers": [f"工作區 {ev['dirty']} 變更; 領先 origin {ev['remote_ahead']}"],
                "next": "USERTEST=PASS 則分批 commit 後 push;否則列缺陷回 S5", "need_log": need_log}
    if ev["six"]["overall"] == "YELLOW":
        return {"stage": "S8", "gate": "PENDING", "blockers": ["six YELLOW: " + ",".join(ev["six"]["yellow"][:4])],
                "next": "維持;逐項清黃(先 S1b/S3 版本未更新類)", "need_log": need_log}
    return {"stage": "S8", "gate": "PASS", "blockers": [], "next": "維持;連續三輪 GREEN 即封版", "need_log": need_log}


def digest_text(ev: dict, d: dict) -> str:
    lines = [
        f"VIA LOOP DIGEST · {datetime.now().strftime('%Y-%m-%d %H:%M')} · 批344",
        f"stage        {d['stage']}  gate={d['gate']}",
        f"head         {ev['head']}",
        f"dirty/ahead  {ev['dirty']} / {ev['remote_ahead']}",
        f"db           {ev['db_present']}/{ev['db_total']}",
        f"registry     {ev['engines_present']}/{ev['engines_total']}",
        f"six          {ev['six']['overall']} {ev['six']['stamp']}  red={','.join(ev['six']['red']) or '-'}  yellow={','.join(ev['six']['yellow'][:5]) or '-'}",
        f"probe        {ev['probe']['mode']} {ev['probe']['stamp']}  ok={ev['probe']['ok']} fail={ev['probe']['fail']} timeout={ev['probe']['timeout']} planned={ev['probe']['planned']}",
        f"drift        {ev['drift_families'] if ev['drift_families'] is not None else '?'} families",
    ]
    for i, b in enumerate(d["blockers"][:3], 1):
        lines.append(f"blocker{i}     {b}")
    lines.append(f"NEXT         {d['next']}")
    lines.append(f"NEED_LOG     {d['need_log']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------
# 頁
# ---------------------------------------------------------------------
def render(raci: dict, ev: dict, d: dict) -> str:
    e = html.escape
    actors = raci.get("actors", {})
    stages = raci.get("stages", [])
    cur = d["stage"]
    def led(s):
        return {"PASS": "ok", "PENDING": "warn", "FAIL": "bad"}.get(s, "off")
    acards = "".join(
        f'<div class="card"><h3>{e(k)} <small>{e(v["zh"])}</small></h3><div class="kv"><div class="k">OWNS</div><div>{e("; ".join(v["owns"]))}</div>'
        f'<div class="k">NEVER</div><div class="dim">{e("; ".join(v["never"]))}</div></div></div>' for k, v in actors.items())
    tabs = "".join(f'<button class="{"on" if s["id"] == cur else ""}" data-t="{s["id"]}"><span class="led {"ok" if s["id"] < cur else ("warn" if s["id"] == cur else "off")}"></span>{s["id"]} {e(s["zh"])}</button>' for s in stages)
    panes = ""
    for s in stages:
        ra = "".join(f'<tr><td class="mono">{e(a)}</td><td class="c">{"R" if s["R"] == a else ""}</td><td class="c">{"A" if s["A"] == a else ""}</td><td class="c">{"C" if a in s["C"] else ""}</td><td class="c">{"I" if a in s["I"] else ""}</td></tr>' for a in actors)
        evd = "".join(f"<li>{e(x)}</li>" for x in s["evidence"])
        panes += (f'<div class="tp {"on" if s["id"] == cur else ""}" data-t="{s["id"]}"><div class="grid"><div class="card"><h3>RACI <small>{e(s["id"])} {e(s["zh"])}</small></h3>'
                  f'<table><tr><th>actor</th><th>R</th><th>A</th><th>C</th><th>I</th></tr>{ra}</table></div>'
                  f'<div class="card"><h3>證據與閘 <small>EVIDENCE · GATE</small></h3><ul style="margin:2px 0 6px 16px;padding:0">{evd}</ul>'
                  f'<div class="kv"><div class="k">GATE</div><div>{e(s["gate"])}</div><div class="k">PASS→</div><div class="mono">{e(s["next_on_pass"])}</div><div class="k">FAIL→</div><div class="mono">{e(s["next_on_fail"])}</div></div></div></div></div>')
    dg = e(digest_text(ev, d))
    css = """:root{--bg:#f5f5f2;--paper:#fff;--paper2:#fafaf8;--ink:#1f2530;--ink2:#3c4658;--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d;--rail-w:270px;--hd:84px}
*{box-sizing:border-box}html{scrollbar-width:thin}body{margin:0;background:var(--bg);color:var(--ink);font:12px/1.45 "Segoe UI","Microsoft JhengHei",sans-serif}.app{display:flex;min-height:100vh}
.rail{width:var(--rail-w);min-width:var(--rail-w);background:var(--paper);border-right:1px solid var(--line);position:sticky;top:0;height:100vh;overflow-y:auto;padding:0 0 10px}
.brand{height:var(--hd);padding:0 14px;display:flex;flex-direction:column;justify-content:center;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--paper);z-index:5}.brand h1{font-size:15px;margin:0}.brand .sub{font-size:9px;letter-spacing:.14em;color:var(--mut2);text-transform:uppercase}
.rail .card{margin:8px 8px 0;padding:8px 10px}.card{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:10px 12px;margin-bottom:10px}.card h3{margin:0 0 6px;font-size:12px}.card h3 small{margin-left:6px;font-size:9px;letter-spacing:.12em;color:var(--mut2);font-weight:400}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;font-size:10.5px}.kv .k{color:var(--mut);font-size:9px;letter-spacing:.08em;font-weight:700}.dim{color:var(--mut2)}.mono{font-family:Consolas,monospace}
.main{flex:1;min-width:0;padding:0 18px}.hdwrap{position:sticky;top:0;z-index:6;background:var(--bg);height:var(--hd);display:flex;flex-direction:column;justify-content:flex-end;padding-top:6px}
.head{display:flex;align-items:flex-end;gap:14px;border-bottom:2px solid var(--ink);padding-bottom:6px;margin-bottom:9px}.head h2{font-size:22px;margin:0;line-height:1.1}.head h2 small{display:block;font-size:9.5px;letter-spacing:.16em;color:var(--mut2);font-weight:400}
.spec{margin-left:auto;display:flex;gap:14px}.spec .k{font-size:8.5px;letter-spacing:.12em;color:var(--mut2)}.spec .v{font-family:Consolas,monospace;font-size:11px;font-weight:700}
.led{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--mut2);margin-right:5px}.led.ok{background:var(--ok)}.led.warn{background:var(--warn)}.led.bad{background:var(--bad)}.led.off{opacity:.45}
.tabs{display:flex;gap:3px;flex-wrap:wrap;border-bottom:1px solid var(--line);margin:6px 0 10px;position:sticky;top:var(--hd);background:var(--bg);z-index:4}.tabs button{font:10.5px/1 inherit;padding:6px 9px;border:1px solid transparent;border-bottom:0;background:transparent;color:var(--mut);cursor:pointer;border-radius:5px 5px 0 0}.tabs button.on{background:var(--paper);border-color:var(--line);color:var(--ink);font-weight:700}
.tp{display:none}.tp.on{display:block}.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.grid .card{margin:0}
table{width:100%;border-collapse:collapse;font-size:10.5px}th{font-size:9px;letter-spacing:.1em;color:var(--mut2);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #eeece7;white-space:normal;word-break:break-word}td.c{text-align:center;font-weight:700}
pre{background:#1e1d1a;color:#d9d6cf;font:10.5px/1.5 Consolas,monospace;padding:10px;border-radius:6px;white-space:pre-wrap;word-break:break-all;margin:0}
@media(max-width:900px){.grid{grid-template-columns:1fr}.rail{position:static;height:auto;width:100%;min-width:0}.app{flex-direction:column}}"""
    js = """<script>(function(){var t=document.querySelector('.tabs');t.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){var k=b.getAttribute('data-t');t.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b);});document.querySelectorAll('.tp').forEach(function(p){p.classList.toggle('on',p.getAttribute('data-t')===k);});});});})();</script>"""
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA · 生命週期角色責任</title><style>{css}</style></head><body><div class="app">
<aside class="rail"><div class="brand"><h1>角色與責任 RACI</h1><div class="sub">GITHUB · PC · ENGINE · DATA · OPERATOR · ASSISTANT</div></div>{acards}
<div class="card"><h3>Token 律</h3><div class="dim">{e(raci.get("token_rule", ""))}</div></div></aside>
<main class="main"><div class="hdwrap"><div class="head"><h2>生命週期閉環 <small>BACKTEST → OPTIMIZE → MODIFY → CONSOLIDATE → DEBUG → USERTEST → ACTIVATE → PERFECT</small></h2>
<div class="spec"><div><div class="k">STAGE</div><div class="v"><span class="led {led(d["gate"])}"></span>{e(cur)}</div></div><div><div class="k">GATE</div><div class="v">{e(d["gate"])}</div></div><div><div class="k">SIX</div><div class="v">{e(ev["six"]["overall"])}</div></div><div><div class="k">DB</div><div class="v">{ev["db_present"]}/{ev["db_total"]}</div></div></div></div></div>
<div class="card"><h3>DIGEST <small>貼這段即可 · ≤25 行</small></h3><pre>{dg}</pre></div>
<div class="tabs">{tabs}</div>{panes}
<div class="dim mono" style="padding:10px 0">零發明:每格=git/DB/矩陣/試鏈實證;缺=UNKNOWN · 生成 {datetime.now().strftime("%Y-%m-%d %H:%M")}</div></main></div>{js}</body></html>'''


# ---------------------------------------------------------------------
def selftest() -> int:
    fails = []
    def chk(n, c):
        print(f"  [{'OK' if c else 'FAIL'}] {n}")
        if not c:
            fails.append(n)
    raci = _raci(); ev = evidence(); d = decide(ev); page = render(raci, ev, d); dg = digest_text(ev, d)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("① RACI 冊在位(六角色×九階段;每階段 R/A/C/I+evidence+gate+next 齊)",
        len(raci.get("actors", {})) == 6 and len(raci.get("stages", [])) == 9
        and all({"R", "A", "C", "I", "evidence", "gate", "next_on_pass", "next_on_fail"} <= set(s) for s in raci["stages"]))
    chk("② 每階段恰一 R 一 A 且皆為在冊角色;A≠助理於啟用/完美階段(操作員裁決)",
        all(s["R"] in raci["actors"] and s["A"] in raci["actors"] for s in raci["stages"])
        and all(s["A"] == "OPERATOR" for s in raci["stages"] if s["id"] in ("S7", "S8", "S6")))
    chk("③ 真證直取(git/DB/six/probe/registry 皆有欄;缺=UNKNOWN/NONE 而非例外)",
        all(k in ev for k in ("head", "dirty", "db_present", "six", "probe", "engines_present")) and ev["six"]["overall"] in ("NONE", "GREEN", "YELLOW", "RED"))
    chk("④ 機制單步推進(decide 回傳 stage∈S0..S8;next 一行;blockers≤3;need_log 一檔或 none)",
        d["stage"] in {s["id"] for s in raci["stages"]} and "\\n" not in d["next"] and len(d["blockers"]) <= 3 and isinstance(d["need_log"], str))
    chk("⑤ digest ≤25 行且含全部 digest_fields 語意(stage/six/probe/db/registry/NEXT/NEED_LOG)",
        len(dg.splitlines()) <= 25 and all(k in dg for k in ("stage", "six", "probe", "db", "registry", "NEXT", "NEED_LOG")))
    chk("⑥ 頁:左角色卡 6 張+Token 律;右九階段頁籤+RACI 矩陣;digest 內嵌;零 CDN;結構成對",
        page.count('<div class="card"><h3>') >= 7 + 9 and page.count('data-t="S') == 18 and "DIGEST" in page
        and 'src="http' not in page and page.count("<div") == page.count("</div>") and page.count("<table") == page.count("</table>"))
    chk("⑦ 助理零直動律(本引擎無 subprocess 派工;僅 git 唯讀查詢)",
        ("Po" + "pen(") not in src and src.count("subprocess." + "run(") == 1 and '"git"' in src)
    chk("⑧ 批347 字階守恆(產物零越階;最大=UISpec fs_xl)", all(any(abs(float(v) - px) < 0.01 for _, px in _type_scale()) for v in re.findall(r"font(?:-size)?\\s*:\\s*([0-9.]+)px", apply_type_scale(page))))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 生命週期角色責任引擎(CGC_MDL125 v0101)· 七檢自測(零派工)===")
        return selftest()
    raci = _raci()
    if not raci:
        print("[loop] VIA_LifecycleRACI_v*.json 缺(誠實)"); return 2
    ev = evidence(); d = decide(ev)
    dg = digest_text(ev, d)
    DIGEST.parent.mkdir(parents=True, exist_ok=True)
    DIGEST.write_text(dg + "\n", encoding="utf-8")
    if "page" in a or "--open" in a:
        OUT.write_text(apply_type_scale(render(raci, ev, d)), encoding="utf-8")
        print(f"[loop] {OUT.name} 已產出")
        if "--open" in a:
            try:
                webbrowser.open(OUT.resolve().as_uri())
            except Exception:
                pass
    print(dg)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL089_UIBaseTemplate — 原始 UI 模板引擎(批165;操作員手機令)
====================================================================
操作員令:「完成實測並建立原始 UI 模板」——把批163「同一測試模板」
升格為可重用正主:
  單一樣式 SSOT=VIA_UI_TemplateSSOT_v0100.json(色/字/距/斷點/槽位
    全由冊供給;引擎內零寫死;版面定案後改冊不改引擎)
  槽位制 render:header_lamp→env_row→kpi→station_table→engine_list
    →footer(六槽;缺選配槽誠實省略,不佔位)
  行動裝置優先:操作員以手機操作=直式卡片化(≤斷點 station_table
    轉卡片)、tap 目標≥冊定最小值、body 零橫向捲動
  實測連動(零重測零發明):資料=CGC_MDL064 最新 GRID 存證 join,
    重用 CGC_MDL088 assemble/harvest_env(glob 尾版;引擎不重造)
  產出=ui_support/VIA_UI_BaseTemplate_v0100.html(模板說明頁+五系統
    實料示範 tab;零 CDN 零外鏈,單檔可離線開)
用法:python3 CGC_MDL089_UIBaseTemplate_v0100.py run | --selftest
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
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SSOT = HERE / "VIA_UI_TemplateSSOT_v0100.json"
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_BaseTemplate_v0100.html"


def load_tokens() -> dict:
    return json.loads(SSOT.read_text(encoding="utf-8"))


def _mdl088():
    """glob 尾版動態載入 CGC_MDL088(引擎不重造:assemble/harvest_env 唯讀重用)"""
    p = sorted(HERE.glob("CGC_MDL088_SystemTestPages_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("cgc_mdl088", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["cgc_mdl088"] = m
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- CSS(全由冊生成)
def base_css(t: dict) -> str:
    p, f, sp, r, ly = t["palette"], t["font"], t["space"], t["radius"], t["layout"]
    st = t["status"]
    return f"""
:root{{--fs:{f['fs']};--ok:{st['OK']};--fail:{st['FAIL']};--skip:{st['SKIP']};
--untested:{st['UNTESTED']}}}
*{{box-sizing:border-box}}
body{{margin:0;background:{p['bg']};color:{p['text']};
font:var(--fs)/{f['line_height']} {f['family']}}}
.wrap{{max-width:{ly['max_width']};margin:0 auto;padding:{sp['pad_page']}}}
h1{{font-size:{f['h1']};margin:.3em 0 .1em}}
h2{{font-size:{f['h2']};margin:.2em 0 .3em}}
.mut{{color:{p['mut']}}}
.tabs{{display:flex;flex-wrap:wrap;gap:{sp['gap']};margin:.5em 0}}
.tab{{font:inherit;border:1px solid {p['border']};background:{p['surface']};
border-radius:{r['tab']};padding:4px 10px;cursor:pointer;
min-height:{ly['tap_min_px']}px}}
.tab b{{margin-left:5px;color:{p['untested'] if 'untested' in p else p['mut']};font-weight:600}}
.tab.on{{background:{p['accent']};color:{p['accent_text']}}}
.tab.on b{{color:{p['border']}}}
.page{{display:none;background:{p['surface']};border:1px solid {p['border']};
border-radius:{r['card']};padding:{sp['pad_card']};overflow-wrap:anywhere}}
.page.on{{display:block}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}}
.dot.big{{width:11px;height:11px}}
.env{{color:{p['sub']};font-size:.9em;border-bottom:1px solid {p['line']};
padding-bottom:5px}}
.kpi{{display:flex;gap:16px;margin:.4em 0;font-weight:600}}
.tablewrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:.93em}}
th,td{{text-align:left;padding:3px 6px;border-bottom:1px solid {p['line']};
vertical-align:top}}
th{{color:{p['sub']}}}
.num{{text-align:right;color:{p['mut']}}}
.engs{{margin-top:.5em;font-size:.88em}}
.warn{{background:{p['warn_bg']};border:1px solid {p['warn_border']};
border-radius:{r['warn']};padding:6px 10px;margin:.4em 0}}
.foot{{color:{p['mut']};font-size:.88em;margin-top:.6em;border-top:1px solid
{p['line']};padding-top:5px}}
.slotmap td:first-child{{white-space:nowrap;color:{p['sub']}}}
@media (max-width:{ly['mobile_breakpoint_px']}px){{
  .kpi{{gap:10px;flex-wrap:wrap}}
  table.cards,table.cards tbody{{display:block}}
  table.cards tr{{display:block;border:1px solid {p['line']};
  border-radius:{r['warn']};margin:.35em 0;padding:2px 6px}}
  table.cards td{{display:block;border:none;padding:1px 2px}}
  table.cards th{{display:none}}
  table.cards td.num{{text-align:left}}
}}"""


# ---------------------------------------------------------------- 槽位 render
def render_section(key: str, title: str, rows: list, env: dict, t: dict) -> str:
    """同一測試模板 section(六槽:燈→環境→KPI→表→清單→頁尾由 shell 統一)"""
    st = t["status"]
    ok = sum(1 for r in rows if r["state"] == "OK")
    fail = sum(1 for r in rows if r["state"] == "FAIL")
    skip = sum(1 for r in rows if r["state"] == "SKIP")
    tone = st["FAIL"] if fail else (st["SKIP"] if skip else st["OK"])
    envs = " · ".join(f"{k} {v}" for k, v in list(env["libs"].items())[:6])

    def _tr(r):
        secs = "" if r["secs"] is None else f"{r['secs']:.1f}s"
        return (f'<tr><td><span class="dot" style="background:'
                f'{st.get(r["state"], st["UNTESTED"])}"></span>{r["state"]}</td>'
                f'<td>{r["name"]}</td><td class="mut">{r["engine"]}</td>'
                f'<td class="num">{secs}</td><td class="mut">{r["note"]}</td></tr>')

    trs = "".join(_tr(r) for r in rows)
    engines = sorted({r["engine"] for r in rows})
    eng_list = "、".join(engines[:24])
    eng_slot = (f'<div class="mut engs">引擎/庫({len(engines)}):{eng_list}</div>'
                if engines else "")  # 選配槽:缺=誠實省略
    return f"""<section id="{key}" class="page">
<h2><span class="dot big" style="background:{tone}"></span>{title}
<span class="mut">({len(rows)} 站)</span></h2>
<div class="env">環境:Python {env['python']} · {env['platform']} · {envs}</div>
<div class="kpi"><span style="color:{st['OK']}">●綠 {ok}</span>
<span style="color:{st['SKIP']}">●黃 {skip}</span>
<span style="color:{st['FAIL']}">●紅 {fail}</span></div>
<div class="tablewrap"><table class="cards">
<tr><th>狀態</th><th>測站(多指標,上→下)</th><th>引擎/庫</th><th>秒</th><th>摘要</th></tr>
{trs}</table></div>
{eng_slot}
</section>"""


def render_spec_section(t: dict) -> str:
    """模板說明 tab:槽位圖+冊 token 表(原始模板自我文件化)"""
    slot_rows = "".join(
        f'<tr><td>{s["id"]}</td><td>{s["zh"]}</td>'
        f'<td>{"必備" if s["required"] else "選配(缺=誠實省略)"}</td></tr>'
        for s in t["slots"])
    st_rows = "".join(
        f'<tr><td>{k}</td><td><span class="dot" style="background:{v}"></span>'
        f'{v}</td></tr>' for k, v in t["status"].items())
    return f"""<section id="SPEC" class="page">
<h2>原始模板規格(SSOT={SSOT.name} · {t['version']})</h2>
<div class="env">{t['policy']}</div>
<h2>槽位(上→下固定順序)</h2>
<div class="tablewrap"><table class="slotmap">
<tr><th>槽位</th><th>內容</th><th>屬性</th></tr>{slot_rows}</table></div>
<h2>三態色碼(誠實三態,冊定單源)</h2>
<div class="tablewrap"><table class="slotmap">
<tr><th>狀態</th><th>色</th></tr>{st_rows}</table></div>
<div class="mut engs">行動優先:≤{t['layout']['mobile_breakpoint_px']}px 逐站表轉卡片
· tap≥{t['layout']['tap_min_px']}px · body 零橫向捲動 · 字級 {t['font']['fs']}</div>
</section>"""


def build(fresh_data: dict | None = None) -> Path:
    t = load_tokens()
    m = _mdl088()
    data = fresh_data or m.assemble()
    env = m.harvest_env()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = [render_spec_section(t)]
    tabs = ['<button class="tab on" onclick="show(\'SPEC\')" id="tab-SPEC">模板規格</button>']
    for k, title in m.SYSTEMS:
        rows = data["pages"][k]
        if not rows:
            continue
        sections.append(render_section(k, title, rows, env, t))
        tabs.append(f'<button class="tab" onclick="show(\'{k}\')" id="tab-{k}">'
                    f'{title.split("(")[0]}<b>{len(rows)}</b></button>')
    warn = ('<div class="warn">⚠ 無 GRID 存證=UNTESTED 誠實</div>'
            if data["evidence_missing"] else "")
    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 原始 UI 模板 v0100</title><style>{base_css(t)}</style></head>
<body><div class="wrap">
<h1>VIA 原始 UI 模板(批165)</h1>
<div class="mut">{ts} · token 冊={SSOT.name} · 實測存證={data['evidence']} ·
grid={data['grid']} · 行動優先直式</div>
{warn}
<div class="tabs">{''.join(tabs)}</div>
{''.join(sections)}
<div class="foot">誠實三態:綠 OK/黃 SKIP(環境缺件·誠實發現)/紅 FAIL;
灰 UNTESTED=無存證不假測 · 頁面=存證 join 零重測 · 版面定案後:改冊不改引擎</div>
<script>
function show(k){{document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
document.getElementById(k).classList.add('on');
document.getElementById('tab-'+k).classList.add('on');}}
show('SPEC');
</script></div></body></html>"""
    UI_OUT.parent.mkdir(parents=True, exist_ok=True)
    UI_OUT.write_text(html, encoding="utf-8")
    return UI_OUT


# ---------------------------------------------------------------- 八檢自測
def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    t = load_tokens()
    chk("① token 冊在位+schema+三態色齊",
        SSOT.exists() and t.get("schema") == "VIA_UI_TEMPLATE_SSOT_V1"
        and set(t["status"]) == {"OK", "FAIL", "SKIP", "UNTESTED"}
        and t.get("append_only") is True)
    css = base_css(t)
    chk("② CSS 純冊生成(四狀態色+版面值皆出自冊)",
        all(v in css for v in t["status"].values())
        and t["palette"]["bg"] in css and t["font"]["fs"] in css
        and t["layout"]["max_width"] in css)
    m = _mdl088()
    chk("③ MDL088 橋(glob 尾版;assemble/harvest_env 唯讀重用=引擎不重造)",
        hasattr(m, "assemble") and hasattr(m, "harvest_env")
        and hasattr(m, "SYSTEMS"))
    env = {"python": "x", "platform": "y", "libs": {"a": "1"}}
    rows = [{"state": "OK", "name": "n", "engine": "e", "secs": 1.0, "note": ""},
            {"state": "UNTESTED", "name": "u", "engine": "e2", "secs": None,
             "note": "無存證"}]
    sec = render_section("T", "測", rows, env, t)
    chk("④ 槽位渲染(六槽序+UNTESTED 灰+選配槽在)",
        sec.index('class="env"') < sec.index('class="kpi"') < sec.index("<table")
        and t["status"]["UNTESTED"] in sec and 'class="mut engs"' in sec)
    sec0 = render_section("T0", "空", [], env, t)
    chk("⑤ 空 rows 誠實(0 站=綠 0 黃 0 紅 0,不假綠)",
        "(0 站)" in sec0 and f'background:{t["status"]["OK"]}' in sec0
        and "●綠 0" in sec0)
    p = build()
    h = p.read_text(encoding="utf-8")
    chk("⑥ 行動優先(viewport+@media 卡片化+tap 冊值+overflow-wrap)",
        "viewport" in h and f"@media (max-width:{t['layout']['mobile_breakpoint_px']}px)" in h
        and "table.cards tr{display:block" in h
        and f"min-height:{t['layout']['tap_min_px']}px" in h
        and "overflow-wrap:anywhere" in h)
    chk("⑦ 零 CDN 零外鏈+實測存證連動",
        "http://" not in h and "https://" not in h
        and ("GRID_" in h or "無 GRID 存證" in h) and "模板規格" in h)
    chk("⑧ 紀律宣告(SSOT 單源/append-only 版本制/改冊不改引擎/誠實三態)",
        "SSOT" in h and "改冊不改引擎" in h and "不假測" in h
        and "append_only" in SSOT.read_text(encoding="utf-8"))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 原始 UI 模板(CGC_MDL089)· 八檢自測(零網路)===")
        return selftest()
    p = build()
    print(f"[UI] {p.name} · token 冊 {SSOT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_master_hub_v0106 — VIA Central Governance Console(活數補齊版)
=============================================================================
v0105→v0106(補齊令):VAP 圖型冊活數「候」根因=路徑錯——正本在
spec/ssot/vap_chartlib.json(via-six L3 同源);改多候選 glob,28 型點亮。
=============================================================================
v0104→v0105(操作員令:Central Governance Console + VDF + VRN + VAP
整個系統架構及 U/I 及系統完成):
  ① 四頁全面改用 UI 範本 v0100(SPEC-012 SysMan 基準:Grid KPI/折疊/
     黏性表頭/燈號雙態/JS 過濾/響應式)
  ② 母版升格「VIA Central Governance Console」+系統架構圖(治理層→
     三子系統層→資料層→商品層,純 CSS 零 CDN)
  ③ 活數接真資料(graceful):SSOT v2 筆數/本機 via.duckdb 表數/
     VAP 圖型冊/台帳筆數/動詞數
=============================================================================
v0102→v0103(儲存規定令 2026-08-12):紅線增「網路工具啟用前先經操作員
同意(VIA_NET_CONSENT)」;鐵則增「安裝一律 via-install 過 EngineForge+
EnvManager 閘並註冊 VIA_Lib_Registry+導入輔助模組」。
v0101→v0102(工作站實錄:via-master 每跑改寫追蹤正本 SSOT(updated_at/
動詞重掃)→工作區髒→git pull Aborting):
  運行態(動詞重掃/updated_at)改寫入 VIA_MasterGovernance_SSOT_v0100.local.json
  (gitignore,單機檔);追蹤正本唯 --sync 時才更新(要提交進化時用)。
  UI 生成讀「正本+local 疊加」視圖,行為不變。
v0100→v0101:操作員上傳三台視覺鎖 UI(去重裁決後全數在庫)——
  VRN=VIA_VisualLock/VIA_VRN_VisualLock_Sidebar_v0159.html(Sidebar Workbench)
  VDF=VDF/VIA_VDF_Fetch_ONE__Standalone.html(Fetch ONE)
  VAP=VAP/VIA_VAP_ONE__Standalone.html(VAP ONE)
生成時 byte-exact 複製至 VIA_Reports/VIA_UI_<K>_Standalone.html,
母版卡與藍圖頁雙連結(實裝 UI + 藍圖);原正本零觸碰。
操作員令(2026-08-12):母版管理(central governance/SSOT/規範/輔助性模組)
存於 JSON、顯示於 UI、共用於所有、持續更新進化自動、也是子系統的入口;
另規劃三個子系統 U/I;所有子系統可打包成商品(一商品一碼鎖一機——
打包重用 via-pack v0103 既有產品號+單機綁定,不重造)。
行為:
  ① SSOT:VIA_MasterGovernance_SSOT_v0100.json — 紅線/鐵則/子系統/UI 藍圖/
     商品規則;動詞表每跑自動從 bin/*.cmd 重掃(自動進化);既有鍵只增不減
  ② UI:母版入口 VIA_Master_Hub.html + 三子系統 UI(VRN 情報台/VDF 鍛造台/
     VAP 視覺台)— 小字體/自動換行/紅黃綠燈/分區;互相連結
用法:py via_master_hub_v0106.py [--no-open] [--json] [--sync(寫回追蹤正本)]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SSOT_P = HERE / "VIA_MasterGovernance_SSOT_v0100.json"
REPORTS = VIA / "VIA_Reports"

RED_LINES = [
    "凍結件零觸碰(freeze.lock)", "只增不減(append-only)", "正本不就地修改(版本前進)",
    "編號永不變(先發先得)", "金鑰只走環境變數(永不落檔/落庫/入 commit)",
    "不爬站 · 零 CDN(自家資產)", "上傳原件唯讀封存(_sha 鏡像 byte-exact)",
    "Outlook 原件唯讀 · .Send() 永不", "誠實 OK/FAIL 不卡斷 · 不假綠", "AI 只整理不發明",
    "網路工具啟用前先經操作員同意(VIA_NET_CONSENT=YES 才發包;NetSupport 同意閘)",
]
IRON_RULES = [
    "動態解析鐵律:啟動器 dir /b /o:n 取最新版,嚴禁寫死版號",
    "dry-run 預設:落庫/改檔類引擎 --commit 才寫",
    "三輪協議 ≤3 輪(sysman);高風險節點→建議不自動修正",
    "每 commit 雙推 main + claude/via-system-followup-tz7k9t",
    "台帳登錄:所有功能/工具/模組自動編號(TOOL/ENG/SPEC 先發先得)",
    "安裝鐵則:新 libs/工具一律 via-install 過 EngineForge+EnvManager 閘,註冊 VIA_Lib_Registry 並導入輔助模組",
    "儲存鐵則(2026-08-12):不落 OneDrive——資料庫/新產物一律本機正典(repo VDF\\db);OneDrive 舊件唯讀凍結參照,候 via-store --migrate 遷回",
]
SUBSYSTEMS = {
    "VRN": {"zh": "研究報告情報台", "color": "#2c4f4a",
            "mission": "券商研究報告 收件→鑑識→OCR→對帳→SSOT→落庫 全鏈",
            "verbs": ["via-batch", "via-pdfcheck", "via-rescue", "via-docx", "via-reconcile", "via-store", "via-ocr"],
            "stores": ["SSOT v2 64 筆", "via.duckdb 4 表(canon/text/cells/log)", "staging/ocr_out"],
            "ui_sections": ["收件矩陣", "鑑識判決(pdfcheck)", "OCR 救援鏈", "對帳覆蓋 64/64", "落庫稽核"]},
    "VDF": {"zh": "市場數據鍛造台", "color": "#31506f",
            "mission": "市場/ETF/總經數據 抓取→鍛造→訊號→庫 全鏈",
            "verbs": ["via-datahub", "via-vdf", "via-flow", "via-plot", "via-forge"],
            "stores": ["via_marketflow.duckdb(候建)", "market.duckdb", "VDF_ACTIVE_SCHEMA"],
            "ui_sections": ["數據心跳(datahub)", "抓取鏈狀態", "訊號燈板", "圖表快照"]},
    "VAP": {"zh": "視覺分析台", "color": "#6f5c31",
            "mission": "MacroMicro 式分析圖庫 28 型 + 面板 + SQL 虛擬表",
            "verbs": ["via-vap", "Invoke-VAP", "via-plot"],
            "stores": ["vap_intelligence.duckdb(_warehouse)", "VAP Spec SSOT v1.0.0", "圖型冊 28 型"],
            "ui_sections": ["圖型冊", "工作台 RUN", "Spec SSOT 對照", "面板組合器"]},
}
STANDALONE_UI = {
    "VRN": "supportive modules/VIA_VisualLock/VIA_VRN_VisualLock_Sidebar_v0159.html",
    "VDF": "functional modules/VDF/VIA_VDF_Fetch_ONE__Standalone.html",
    "VAP": "functional modules/VAP/VIA_VAP_ONE__Standalone.html",
}
PRODUCT_RULES = {
    "packer": "via-pack(v0103 既有:產品號+單機綁定+封面U/I;entry_newest 動態跟版)",
    "rule": "一商品一碼鎖一機:machine_id=sha256(MachineGuid+電腦名) · 商品組合號=sha256(組合+machine_id)[:12]",
    "fresh_pc": "Bootstrap-VIA-FreshPC-v0100.cmd → Install-VIA-Product-v0101.ps1(PS7 自救+pip+綁機 全自動)",
    "combos": ["VRN 單品", "VDF 單品", "VAP 單品", "VRN+VDF", "全家桶 VRN+VDF+VAP"],
}


TPL_CSS = """<style>
:root{--bg:#f4f3ef;--paper:#fff;--ink:#1b1a17;--mut:#6b6860;--line:#dbd9d3;--soft:#ebe9e3;
 --g:#2c4f4a;--gbg:#e6efec;--o:#6f5c31;--obg:#f2ecdd;--r:#9e2b25;--rbg:#f3e7e6;--grad:linear-gradient(90deg,#2c4f4a,#5b8a83)}
*{box-sizing:border-box}
body{font-family:'Segoe UI','Noto Sans TC',Arial,sans-serif;font-size:11.5px;background:var(--bg);color:var(--ink);margin:18px auto;max-width:1100px;padding:0 14px;line-height:1.5}
h1{font-size:17px;letter-spacing:.05em;margin:2px 0}
.mast{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;border-bottom:2px solid var(--ink);padding-bottom:8px;margin-bottom:12px}
.num{font-family:Consolas,monospace;font-size:9.5px;letter-spacing:.14em;color:var(--mut);text-transform:uppercase}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin:8px 0}
.kpi{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:8px 12px;text-align:center}
.kpi b{display:block;font-size:16px}
.kpi .l{font-family:Consolas,monospace;font-size:8px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:var(--paper);margin:6px 0}
table{width:100%;border-collapse:collapse;font-size:10.5px}
th,td{border-bottom:1px solid var(--soft);padding:4px 8px;text-align:left;vertical-align:top;word-wrap:break-word;overflow-wrap:anywhere}
th{font-family:Consolas,monospace;font-size:8.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);background:var(--paper);position:sticky;top:0}
.tag{display:inline-block;padding:1px 7px;border-radius:8px;font-family:Consolas,monospace;font-size:8.5px;font-weight:700;background:var(--gbg);color:var(--g);margin:1px 2px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:middle}
.dot.g{background:var(--g)}.dot.o{background:#c4943a}
details{background:var(--paper);border:1px solid var(--line);border-radius:8px;margin:10px 0;padding:0 12px 8px}
summary{cursor:pointer;font-weight:700;font-size:12.5px;padding:9px 0}
.sechead{font-size:12.5px;font-weight:700;margin:16px 0 4px;border-left:3px solid var(--ink);padding-left:7px}
.card{display:inline-block;vertical-align:top;background:var(--paper);border:1px solid var(--line);border-radius:9px;padding:10px 14px;margin:5px 8px 5px 0;width:300px;min-height:140px}
.card h2{font-size:13px;margin:0 0 4px}
.mono{font-family:Consolas,monospace;font-size:.95em}.small{font-size:9.5px;color:var(--mut)}
a{color:#31506f;text-decoration:none}a:hover{text-decoration:underline}
.arch{display:grid;gap:6px;margin:8px 0}
.layer{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:8px 12px}
.layer .lt{font-family:Consolas,monospace;font-size:8.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px}
.node{display:inline-block;background:var(--soft);border-radius:6px;padding:3px 10px;margin:2px 3px;font-size:10px}
.node.hot{background:var(--gbg);color:var(--g);font-weight:700}
.down{text-align:center;color:var(--mut);font-size:11px;line-height:.6}
.filter{font-family:Consolas,monospace;font-size:10px;padding:5px 9px;border:1px solid var(--line);border-radius:5px;width:230px;max-width:100%;margin:4px 0}
.foot{font-family:Consolas,monospace;font-size:9px;color:var(--mut);text-align:center;padding:10px 0}
@media(max-width:720px){.card{width:100%}}
</style><script>
function viaFilter(inp,tbodyId){var q=(inp.value||'').toLowerCase();
 var rows=document.getElementById(tbodyId).rows;
 for(var i=0;i<rows.length;i++){rows[i].style.display=rows[i].textContent.toLowerCase().indexOf(q)>=0?'':'none';}}
</script>"""


def live_stats():
    """活數(graceful:缺件誠實顯示 候)。"""
    st = {}
    try:
        v2 = VIA / "functional modules/VRN/SSOT/v2/VRN_ResearchReport_SSOT.v2.jsonl"
        st["ssot_v2"] = sum(1 for l in v2.read_text(encoding="utf-8-sig").splitlines() if l.strip())
    except Exception:
        st["ssot_v2"] = "候"
    try:
        import duckdb
        dbp = VIA / "functional modules/VDF/db/via.duckdb"
        if dbp.exists():
            con = duckdb.connect(str(dbp), read_only=True)
            st["db_tables"] = con.execute("select count(*) from information_schema.tables where table_schema='main'").fetchone()[0]
            con.close()
        else:
            st["db_tables"] = "候落庫"
    except Exception:
        st["db_tables"] = "候"
    st["charts"] = "候"
    for cand in (VIA / "functional modules/VAP/spec/ssot/vap_chartlib.json",
                 VIA / "functional modules/VAP/spec/vap_chartlib.json"):
        try:
            cl = json.loads(cand.read_text(encoding="utf-8-sig"))
            st["charts"] = sum(len(g.get("charts", [])) for g in cl.get("groups", []))
            break
        except Exception:
            continue
    try:
        rg = json.loads((HERE / "VIA_AutoCode_Registry_v0100.json").read_text(encoding="utf-8"))
        st["ledger"] = len(rg.get("ledger", []))
    except Exception:
        st["ledger"] = "候"
    st["verbs"] = len(list((VIA / "bin").glob("*.cmd")))
    return st


def scan_verbs():
    verbs = {}
    for cmd in sorted((VIA / "bin").glob("*.cmd")):
        desc = ""
        try:
            for line in cmd.read_text(encoding="utf-8", errors="replace").splitlines()[1:4]:
                if line.lower().startswith("rem"):
                    desc = line[3:].strip()
                    break
        except Exception:
            pass
        verbs[cmd.stem] = desc[:110]
    return verbs


LOCAL_P = SSOT_P.with_suffix(".local.json")  # 運行態(gitignore 單機檔)


def build_ssot():
    old = {}
    if SSOT_P.exists():
        try:
            old = json.loads(SSOT_P.read_text(encoding="utf-8"))
        except Exception:
            old = {}
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ssot = dict(old)  # 只增不減:既有鍵保留
    ssot.update({
        "schema": "VIA.MasterGovernance.v1",
        "updated_at": ts,
        "red_lines": RED_LINES,
        "iron_rules": IRON_RULES,
        "subsystems": SUBSYSTEMS,
        "product_rules": PRODUCT_RULES,
        "verbs": scan_verbs(),  # 自動進化:每跑重掃 bin
        "entry": {"hub_ui": "VIA_Reports/VIA_Master_Hub.html",
                  "sub_ui": {k: f"VIA_Reports/VIA_UI_{k}.html" for k in SUBSYSTEMS},
                  "sub_ui_standalone": STANDALONE_UI},
    })
    payload = json.dumps(ssot, ensure_ascii=False, indent=1) + "\n"
    if "--sync" in sys.argv:
        SSOT_P.write_text(payload, encoding="utf-8")  # 進化寫回追蹤正本(提交前用)
        print("  [sync] 追蹤正本已更新(候提交)")
    else:
        LOCAL_P.write_text(payload, encoding="utf-8")  # 運行態單機檔——正本零觸碰,pull 不再卡
    return ssot


CSS = """<style>
body{font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;background:#f4f3ef;color:#1b1a17;margin:18px auto;max-width:1060px;padding:0 14px}
h1{font-size:17px;letter-spacing:.05em;margin:2px 0}
.mast{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #1b1a17;padding-bottom:8px;margin-bottom:12px}
.num{font-family:Consolas,monospace;font-size:9.5px;letter-spacing:.14em;color:#6b6860;text-transform:uppercase}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dbd9d3;margin:6px 0}
th,td{border-bottom:1px solid #ebe9e3;padding:4px 8px;text-align:left;vertical-align:top;font-size:10.5px;word-wrap:break-word;overflow-wrap:anywhere}
th{font-family:Consolas,monospace;font-size:8.5px;text-transform:uppercase;letter-spacing:.06em;color:#6b6860}
.sechead{font-size:12.5px;font-weight:700;margin:16px 0 4px;border-left:3px solid #1b1a17;padding-left:7px}
.card{display:inline-block;vertical-align:top;background:#fff;border:1px solid #dbd9d3;border-radius:9px;padding:10px 14px;margin:5px 8px 5px 0;width:300px;min-height:150px}
.card h2{font-size:13px;margin:0 0 4px}
.tag{display:inline-block;padding:1px 7px;border-radius:8px;font-family:Consolas,monospace;font-size:8.5px;font-weight:700;background:#e6efec;color:#2c4f4a;margin:1px 2px}
.mono{font-family:Consolas,monospace;font-size:.95em}.small{font-size:9.5px;color:#6b6860}
a{color:#31506f;text-decoration:none}a:hover{text-decoration:underline}
.foot{font-family:Consolas,monospace;font-size:9px;color:#6b6860;text-align:center;padding:10px 0}
</style>"""


def hub_html(ssot):
    ts = ssot["updated_at"]
    st = live_stats()
    cards = ""
    for k, sub in ssot["subsystems"].items():
        vb = " ".join(f'<span class="tag">{v}</span>' for v in sub["verbs"][:6])
        stx = "<br>".join(f"· {x}" for x in sub["stores"])
        sa = f' · <a href="VIA_UI_{k}_Standalone.html">實裝 ⇱</a>' if (VIA / STANDALONE_UI[k]).exists() else ""
        cards += f"""<div class="card" style="border-top:3px solid {sub['color']}">
<h2><a href="VIA_UI_{k}.html">{k} · {sub['zh']} →</a>{sa}</h2>
<div class="small">{sub['mission']}</div><div style="margin:6px 0">{vb}</div>
<div class="small">{stx}</div></div>"""
    red = "".join(f"<tr><td>{i + 1}</td><td>{r}</td></tr>" for i, r in enumerate(ssot["red_lines"]))
    iron = "".join(f"<tr><td>{i + 1}</td><td>{r}</td></tr>" for i, r in enumerate(ssot["iron_rules"]))
    verbs = "".join(f'<tr><td class="mono">{k}</td><td>{v}</td></tr>' for k, v in sorted(ssot["verbs"].items()))
    pr = ssot["product_rules"]
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Central Governance Console</title>{TPL_CSS}</head><body>
<div class="mast"><div><div class="num">VIA CENTRAL GOVERNANCE CONSOLE · {ts} · SSOT 存 JSON · 持續進化 · UI 範本 v0100</div>
<h1>VIA 中央治理主控台 · Central Governance Console</h1></div>
<div class="mono small">VDF 鍛造 · VRN 報告 · VAP 視覺<br>子系統唯一入口</div></div>
<div class="kpis">
<div class="kpi"><b>{st['ssot_v2']}</b><span class="l">SSOT v2 筆</span></div>
<div class="kpi"><b>{st['db_tables']}</b><span class="l">via.duckdb 表(本機)</span></div>
<div class="kpi"><b>{st['charts']}</b><span class="l">VAP 圖型冊</span></div>
<div class="kpi"><b>{st['ledger']}</b><span class="l">台帳筆數</span></div>
<div class="kpi"><b>{st['verbs']}</b><span class="l">動詞</span></div></div>
<div class="sechead">系統架構(治理 → 子系統 → 資料 → 商品)</div>
<div class="arch">
<div class="layer"><div class="lt">① 治理層 · CENTRAL GOVERNANCE</div>
<span class="node hot">母版 SSOT(JSON)</span><span class="node hot">台帳 AutoCode Registry</span>
<span class="node">sysman 三輪協議(v01.00)</span><span class="node">provision 首啟/體檢</span>
<span class="node">install 安裝閘</span><span class="node">tidy 整理引擎</span><span class="node">NetSupport 同意閘</span></div>
<div class="down">▼</div>
<div class="layer"><div class="lt">② 子系統層 · SUBSYSTEMS</div>
<span class="node hot">VDF · VeritasDataForge 市場數據鍛造</span>
<span class="node hot">VRN · VeritasReportNova 研究報告情報</span>
<span class="node hot">VAP · VeritasAutoPlot 視覺分析</span>
<span class="node">Pipeline 輪動證偽實驗室</span><span class="node">FlowSystem v2</span></div>
<div class="down">▼</div>
<div class="layer"><div class="lt">③ 資料層 · DATA(本機正典;不落 OneDrive)</div>
<span class="node hot">via.duckdb(VDF/db,{st['db_tables']} 表)</span>
<span class="node">SSOT v2({st['ssot_v2']} 筆)</span><span class="node">staging parquet(文字/表格)</span>
<span class="node">VAP _warehouse</span></div>
<div class="down">▼</div>
<div class="layer"><div class="lt">④ 商品層 · PRODUCTS</div>
<span class="node hot">via-pack 一商品一碼鎖一機</span><span class="node">FreshPC 引導鏈(PS7 自救+綁機)</span>
<span class="node">組合:{' / '.join(pr['combos'])}</span></div></div>
<div class="sechead">子系統入口(三台)</div>{cards}
<details><summary>紅線(永久 · {len(ssot['red_lines'])} 條)</summary>
<div class="scroll"><table><tr><th>#</th><th>紅線</th></tr>{red}</table></div></details>
<details><summary>鐵則({len(ssot['iron_rules'])} 條)</summary>
<div class="scroll"><table><tr><th>#</th><th>鐵則</th></tr>{iron}</table></div></details>
<details open><summary>動詞總表(bin 自動重掃 · {len(ssot['verbs'])} 個)</summary>
<input class="filter" placeholder="即時過濾…" oninput="viaFilter(this,'verbBody')">
<div class="scroll"><table><tr><th>動詞</th><th>說明</th></tr><tbody id="verbBody">{verbs}</tbody></table></div></details>
<div class="foot">VERITAS INTELLIGENCE ANALYTICS · CENTRAL GOVERNANCE CONSOLE · 母版 SSOT 存 JSON · 共用於所有 · 持續更新進化自動</div>
</body></html>"""


def sub_html(key, s, ssot):
    ts = ssot["updated_at"]
    secs = "".join(f'<div class="card" style="border-top:3px solid {s["color"]}"><h2>{sec}</h2>'
                   f'<div class="small">藍圖區塊——引擎實跑產物接入點(候接資料源)</div></div>'
                   for sec in s["ui_sections"])
    verbs = "".join(f'<tr><td class="mono">{v}</td><td>{ssot["verbs"].get(v, "(PS 動詞)")}</td></tr>'
                    for v in s["verbs"])
    stores = "".join(f"<tr><td>{x}</td></tr>" for x in s["stores"])
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>VIA {key}</title>{TPL_CSS}</head><body>
<div class="mast"><div><div class="num">VIA-{key} · {ts} · <a href="VIA_Master_Hub.html">← 母版中樞</a> ·
<a href="VIA_UI_{key}_Standalone.html">實裝 UI ⇱</a></div>
<h1 style="color:{s['color']}">{key} · {s['zh']}</h1></div><div class="small">{s['mission']}</div></div>
<div class="sechead">功能分區(UI 藍圖)</div>{secs}
<div class="sechead">動詞</div><table><tr><th>動詞</th><th>說明</th></tr>{verbs}</table>
<div class="sechead">資料庫/存放</div><table><tr><th>存放</th></tr>{stores}</table>
<div class="foot">VIA {key} 子系統 UI v0100(藍圖版)· 可經 via-pack 打包為單品(一商品一碼鎖一機)</div>
</body></html>"""


def main() -> int:
    ssot = build_ssot()
    REPORTS.mkdir(parents=True, exist_ok=True)
    hub = REPORTS / "VIA_Master_Hub.html"
    hub.write_text(hub_html(ssot), encoding="utf-8")
    pages = [hub]
    import shutil
    for k, s in ssot["subsystems"].items():
        p = REPORTS / f"VIA_UI_{k}.html"
        p.write_text(sub_html(k, s, ssot), encoding="utf-8")
        pages.append(p)
        src = VIA / STANDALONE_UI[k]
        if src.exists():  # 實裝 UI byte-exact 複製(正本零觸碰)
            dst = REPORTS / f"VIA_UI_{k}_Standalone.html"
            shutil.copy2(src, dst)
            pages.append(dst)
    print(f"=== Central Governance Console v0106 · SSOT + {len(pages)} 頁 UI(含三台實裝;運行態走 .local)===")
    print(f"  [SSOT] {SSOT_P.name}(動詞 {len(ssot['verbs'])} 個自動重掃)")
    for p in pages:
        print(f"  [UI  ] {p.name}")
    if "--json" in sys.argv:
        print(json.dumps({"ssot": str(SSOT_P), "pages": [str(p) for p in pages]}, ensure_ascii=False))
    if "--no-open" not in sys.argv and sys.platform == "win32":
        import os
        os.startfile(str(hub))  # noqa
    return 0


if __name__ == "__main__":
    sys.exit(main())

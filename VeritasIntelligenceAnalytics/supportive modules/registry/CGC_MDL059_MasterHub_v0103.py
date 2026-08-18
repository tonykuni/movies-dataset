#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_master_hub_v0103 — 母版管理中樞(儲存規定條文版)
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
用法:py via_master_hub_v0103.py [--no-open] [--json] [--sync(寫回追蹤正本)]
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
    cards = ""
    for k, s in ssot["subsystems"].items():
        vb = " ".join(f'<span class="tag">{v}</span>' for v in s["verbs"][:6])
        st = "<br>".join(f"· {x}" for x in s["stores"])
        sa = f' · <a href="VIA_UI_{k}_Standalone.html">實裝 UI ⇱</a>' if (VIA / STANDALONE_UI[k]).exists() else ""
        cards += f"""<div class="card" style="border-top:3px solid {s['color']}">
<h2><a href="VIA_UI_{k}.html">{k} · {s['zh']} →</a>{sa}</h2>
<div class="small">{s['mission']}</div><div style="margin:6px 0">{vb}</div>
<div class="small">{st}</div></div>"""
    red = "".join(f"<tr><td>{i + 1}</td><td>{r}</td></tr>" for i, r in enumerate(ssot["red_lines"]))
    iron = "".join(f"<tr><td>{i + 1}</td><td>{r}</td></tr>" for i, r in enumerate(ssot["iron_rules"]))
    verbs = "".join(f'<tr><td class="mono">{k}</td><td>{v}</td></tr>' for k, v in sorted(ssot["verbs"].items()))
    pr = ssot["product_rules"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>VIA Master Hub</title>{CSS}</head><body>
<div class="mast"><div><div class="num">VIA-MASTER-HUB · {ts} · CENTRAL GOVERNANCE SSOT · 子系統入口</div>
<h1>母版管理中樞 · MASTER GOVERNANCE HUB</h1></div>
<div class="mono small">SSOT: VIA_MasterGovernance_SSOT_v0100.json<br>自動進化:via-master 每跑重掃</div></div>
<div class="sechead">子系統入口(三台)</div>{cards}
<div class="card" style="border-top:3px solid #9e2b25"><h2>商品打包 · 一商品一碼鎖一機</h2>
<div class="small">{pr['rule']}</div><div style="margin:5px 0"><span class="tag">via-pack</span>
<span class="tag">FreshPC 鏈</span></div><div class="small">組合:{' / '.join(pr['combos'])}<br>{pr['fresh_pc']}</div></div>
<div class="card" style="border-top:3px solid #6b6860"><h2>首啟布建 · 機況體檢</h2>
<div class="small">初次啟動詢問存放位置→依規畫布建;體檢存安裝計畫 JSON</div>
<div style="margin:5px 0"><span class="tag">via-provision</span><span class="tag">via-provision --check</span>
<span class="tag">via-sysman</span></div></div>
<div class="sechead">紅線(永久)</div><table><tr><th>#</th><th>紅線</th></tr>{red}</table>
<div class="sechead">鐵則</div><table><tr><th>#</th><th>鐵則</th></tr>{iron}</table>
<div class="sechead">動詞總表(bin 自動重掃 · {len(ssot['verbs'])} 個)</div>
<table><tr><th>動詞</th><th>說明</th></tr>{verbs}</table>
<div class="foot">VERITAS INTELLIGENCE ANALYTICS · 母版 SSOT 存 JSON · 共用於所有 · 持續更新進化自動</div>
</body></html>"""


def sub_html(key, s, ssot):
    ts = ssot["updated_at"]
    secs = "".join(f'<div class="card" style="border-top:3px solid {s["color"]}"><h2>{sec}</h2>'
                   f'<div class="small">藍圖區塊——引擎實跑產物接入點(候接資料源)</div></div>'
                   for sec in s["ui_sections"])
    verbs = "".join(f'<tr><td class="mono">{v}</td><td>{ssot["verbs"].get(v, "(PS 動詞)")}</td></tr>'
                    for v in s["verbs"])
    stores = "".join(f"<tr><td>{x}</td></tr>" for x in s["stores"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>VIA {key}</title>{CSS}</head><body>
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
    print(f"=== 母版管理中樞 v0103 · SSOT + {len(pages)} 頁 UI(含三台實裝;運行態走 .local)===")
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

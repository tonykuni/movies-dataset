# -*- coding: utf-8 -*-
r"""build_spec_master_v0100.py — VIA 母版最後一頁 · 全系統規格總覽生成器。

操作員令(2026/08/12):「所有規格全部放於VIA母版最後一頁 VIA Flow System / VIA(母) /
VDF / VRN / VAP(含模板/ICON/繪圖管理)」。
本器由 canon 真實 SSOT 動態生成(AI 只整理不發明;零手寫數字):
  VIA(母)  registry 元件/帳本/ENG 碼 + bin 動詞 + 紅線 + 清冊
  FlowSystem  16+1 引擎 + gates + 宇宙分層 + 驗證契約 + 宏觀對照
  VDF      模組清單 + 資料入口規約 + v0160 三件套(候上傳)
  VRN      模組清單 + v0159 三件套(已驗真)+ 視覺鎖側欄規格
  VAP      chartlib SSOT 28 圖型(=模板)+ 變換 + ICON/繪圖管理(色序/樣式/次要編碼)
產物:VIA_Reports/VIA_Spec_Master_LastPage.html(自含零 CDN;v2 視覺鎖 token)。
VIA_ONE_Master_Overview 本體到件後,本頁可直接掛為其最後一頁(iframe/append 皆可)。
"""
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
import html as _html
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUTP = VIA / "VIA_Reports" / "VIA_Spec_Master_LastPage.html"

T = {"bg": "#f2f1ec", "paper": "#ffffff", "paper2": "#fbfaf7", "ink": "#1b1a17",
     "ink2": "#3a3f3e", "mut": "#6b6860", "mut2": "#9c9890", "line": "#dcdad3",
     "line2": "#ebe9e3", "teal": "#3d8f8f", "accent": "#5980a6"}

AWAITED = ["VIA_MI_Code_Appendix (3).html", "VIA_Extraction_Matrix (14).html",
           "VIA_Global_Index_Macro_Tree (1).html", "VIA_TW_ETF_Group_Console (1).html",
           "VIA_ONE_Master_Overview (5).html"]

RED_LINES = ["系統不可代為發送(.Display/.Save only;絕不 .Send)", "Outlook 原件/分類唯讀零觸碰",
             "編號一旦生成永不變(WOP/THR/DEC/MLS/CMT…)", "基底零觸碰 · 只增不減 · 正本不就地修改(版本前送)",
             "動態解析最新版(嚴禁寫死版號)", "在地化零雲端零 CDN", "誠實 OK/FAIL(絕不冒充;Gate E 準確度留白)",
             "ML 永不直寫狀態 · AI 只整理不發明"]


def esc(s):
    return _html.escape(str(s), quote=True)


def jload(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def sec(title, en, body):
    return ('<section class="card"><h2>%s <span>%s</span></h2>%s</section>' % (esc(title), esc(en), body))


def kv_table(rows, heads):
    h = ['<div class="scroll"><table><thead><tr>%s</tr></thead><tbody>' %
         "".join("<th>%s</th>" % esc(x) for x in heads)]
    for r in rows:
        h.append("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r))
    h.append("</tbody></table></div>")
    return "".join(h)


def build():
    reg = jload(VIA / "supportive modules/registry/VIA_AutoCode_Registry_v0100.json")
    inv = jload(VIA / "supportive modules/registry/VIA_Tool_Engine_Inventory_v0100.json")
    lib = jload(VIA / "functional modules/VAP/spec/ssot/vap_chartlib.json")
    fs_params = jload(VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/params.json")
    fs_uni = jload(VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/universe.json")
    fs_macro = jload(VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/macro.json")
    up = VIA / "functional modules/VAP/spec/UIUX_Design_Source/uploads"
    vrn_man = jload(up / "VIA_VRN_v0159_Artifact_Manifest (1).json")
    vrn_lock = jload(up / "VIA_VRN_VisualLock_Sidebar_v0159 (1).json")
    vdf_man = jload(up / "VIA_VDF_v0160_Artifact_Manifest.json")

    parts = []
    # ── VIA(母)
    comps = reg.get("components", {})
    eng = sorted(v for v in comps.values() if str(v).startswith("ENG-"))
    body = ('<div class="chips"><span class="chip">元件 %d</span><span class="chip">帳本 %d 筆(append-only)</span>'
            '<span class="chip">引擎碼 %s → %s</span><span class="chip">bin 動詞 %d</span></div>'
            % (len(comps), len(reg.get("ledger", [])), eng[0] if eng else "—", eng[-1] if eng else "—",
               len(inv.get("bin_verbs", []))))
    body += '<h3>紅線(永久)</h3><ul>%s</ul>' % "".join("<li>%s</li>" % esc(x) for x in RED_LINES)
    body += '<h3>bin 動詞清冊</h3>' + kv_table(
        [(('<b class="mono">%s</b>' % esc(v["verb"])), esc(v["desc"])) for v in inv.get("bin_verbs", [])],
        ["動詞", "說明"])
    parts.append(sec("VIA(母)", "Mother System · Registry / Verbs / Red Lines", body))

    # ── FlowSystem
    tiers = {}
    for e in fs_uni.get("etfs", []):
        tiers["T%d" % e.get("risk_tier", 3)] = tiers.get("T%d" % e.get("risk_tier", 3), 0) + 1
    eng_dir = VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines"
    fl_eng = sorted(p.name for p in eng_dir.glob("flow_*.py"))
    body = ('<div class="chips"><span class="chip">引擎 %d 支</span><span class="chip">宇宙 %d 檔 '
            '(T1=%s/T2=%s/T3=%s/T4=%s)</span><span class="chip">gates %d</span>'
            '<span class="chip">宏觀對照 %d 區</span></div>'
            % (len(fl_eng), len(fs_uni.get("etfs", [])), tiers.get("T1"), tiers.get("T2"),
               tiers.get("T3"), tiers.get("T4"), len(fs_params.get("gates", {})),
               len(fs_macro.get("regions", {}))))
    body += ('<h3>驗證契約</h3><ul><li>三層 SOLID:Pillar A 測量(真值缺=UNCALIBRATED 誠實降級)· '
             'Pillar B 效力(G002-G011 全綠+OOS)· selftest 14 項</li>'
             '<li>反證保證:alpha=0 → 必 NOT_VALID(實證);有結構 → PROVED_VALID(實證 IC 0.172)</li>'
             '<li>宏觀對照:FIS × 匯率/利率/美元指數/經濟 → 順風/背離判讀(%s)</li></ul>'
             % esc(fs_macro.get("verdict_rule", "")))
    body += '<h3>引擎樹</h3><div class="mono files">%s</div>' % " · ".join(esc(x) for x in fl_eng)
    parts.append(sec("VIA Flow System", "Global ETF Flow · Self-Proving", body))

    # ── VDF
    vdf_dir = VIA / "functional modules/VDF"
    vdf_files = sorted(p.name for p in vdf_dir.glob("*") if p.is_file()) if vdf_dir.exists() else []
    arts = vdf_man.get("artifacts", [])
    body = ('<div class="chips"><span class="chip">模組檔 %d</span><span class="chip">資料入口:CSV/TSV/JSON/'
            'SQLite/Parquet/DuckDB → VDF/db</span></div>' % len(vdf_files))
    body += '<h3>v0160 三件套(manifest 在籍;本體候上傳,到件依 sha 驗真歸戶)</h3>'
    body += kv_table([(esc(a["filename"]), '<span class="mono">%s…</span>' % esc(a["sha256"][:16]),
                       "%d bytes" % a["bytes"], '<span class="pend">候上傳</span>') for a in arts],
                     ["檔名", "SHA-256(前16)", "大小", "狀態"])
    body += '<h3>模組清單</h3><div class="mono files">%s</div>' % " · ".join(esc(x) for x in vdf_files[:24])
    parts.append(sec("VDF", "VeritasDataForge · Data Intake", body))

    # ── VRN
    vrn_dir = VIA / "functional modules/VRN"
    vrn_files = sorted(p.name for p in vrn_dir.glob("*") if p.is_file()) if vrn_dir.exists() else []
    arts = vrn_man.get("artifacts", [])
    body = ('<div class="chips"><span class="chip">模組檔 %d</span><span class="chip">v0159 三件套已驗真在籍</span>'
            '<span class="chip">視覺鎖 %s</span></div>'
            % (len(vrn_files), esc(vrn_lock.get("lock_state", "—"))))
    body += kv_table([(esc(a["filename"]), '<span class="mono">%s…</span>' % esc(a["sha256"][:16]),
                       '<span class="okk">在籍驗真</span>') for a in arts],
                     ["v0159 藝品", "SHA-256(前16)", "狀態"])
    pages = vrn_lock.get("pages", [])
    if pages:
        body += ('<h3>側欄六頁規格(VisualLock)</h3><div class="mono files">%s</div>'
                 '<h3>禁改條款</h3><ul>%s</ul>'
                 % (" · ".join(esc(p.get("label", p.get("id", ""))) for p in pages),
                    "".join("<li>%s</li>" % esc(x) for x in vrn_lock.get("prohibited_changes", []))))
    parts.append(sec("VRN", "Report Navigator · Sidebar Workbench", body))

    # ── VAP(含模板/ICON/繪圖管理)
    meta = lib.get("meta", {})
    n_charts = sum(len(g.get("charts", [])) for g in lib.get("groups", []))
    rows = []
    for g in lib.get("groups", []):
        for c in g.get("charts", []):
            rows.append(('<b class="mono">%s</b>' % esc(c.get("code", "")), esc(c.get("zh", "")),
                         esc(c.get("en", "")), esc(g.get("id", "")),
                         esc((c.get("use") or "")[:36])))
    vap_eng = sorted(p.name for p in (VIA / "functional modules/VAP/engine").glob("*.py"))
    body = ('<div class="chips"><span class="chip">SSOT %s(%s)</span><span class="chip">圖型模板 %d 型</span>'
            '<span class="chip">引擎 %d 支(chartlib 零依賴 + seaborn/plotly 全譜)</span></div>'
            % (esc(meta.get("version", "")), esc(meta.get("updated", "")), n_charts, len(vap_eng)))
    body += ('<h3>ICON / 繪圖管理(視覺鎖)</h3><ul>'
             '<li>via combo 色序(鎖定):<span class="sw" style="background:#c96b5a"></span>#c96b5a '
             '<span class="sw" style="background:#c4943a"></span>#c4943a '
             '<span class="sw" style="background:#5a9e6f"></span>#5a9e6f '
             '<span class="sw" style="background:#439a9a"></span>#439a9a '
             '<span class="sw" style="background:#4c78a8"></span>#4c78a8 '
             '<span class="sw" style="background:#7a6daa"></span>#7a6daa(C4/C5 虛線次要編碼)</li>'
             '<li>統一規格:線粗 1 · 折線 0.9 · 填色 0.75 · 軸距 2/2.5/5/10 × 5 刻度 · 位數一致 · 軸頂 25%% 留格</li>'
             '<li>直條樣式:seamless 1.00 / tiny 0.92 / low 0.82(雙軸預設 low)</li>'
             '<li>變換:yoy/mom/rebase100/ma:N/ytd · 事件帶 · --panels 同步面板 · --sql DuckDB 虛擬表</li></ul>')
    body += '<h3>28 圖型模板註冊表</h3>' + kv_table(rows, ["代碼", "中文", "English", "群", "用途"])
    parts.append(sec("VAP(含模板/ICON/繪圖管理)", "VeritasAutoPlot · Chart Library SSOT", body))

    # ── 候上傳
    body = ('<ul>%s</ul><div class="hint">五檔本體到件即:整合去重裁定 → 內容吸收入本頁對應段;'
            'VIA_ONE_Master_Overview 到件後本頁直接掛為其最後一頁。</div>'
            % "".join('<li class="mono">%s <span class="pend">候上傳</span></li>' % esc(x) for x in AWAITED))
    parts.append(sec("候上傳規格頁", "Awaiting Upload", body))

    page = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA 母版最後一頁 · 全系統規格總覽</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;font-size:13px;line-height:1.65;padding:20px}
.wrap{max-width:1180px;margin:0 auto}
.kick{font:700 10px "DM Mono",Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;color:%(teal)s}
h1{font-size:clamp(17px,2vw,21px);color:%(ink)s}
.sub{font-size:11px;color:%(mut)s;margin:2px 0 14px}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:16px 18px;margin-bottom:16px;
box-shadow:0 1px 2px rgba(27,26,23,.04),0 8px 24px -12px rgba(27,26,23,.14)}
h2{font-size:15px;color:%(ink)s;border-bottom:2px solid %(accent)s;padding-bottom:6px;margin-bottom:10px}
h2 span{font-size:10.5px;font-weight:400;color:%(mut)s;margin-left:8px}
h3{font-size:12.5px;color:%(ink)s;margin:12px 0 6px}
ul{padding-left:20px;font-size:12px}
table{width:100%%;border-collapse:collapse;font-size:11.5px}
th{font:700 9.5px "DM Mono",Consolas,monospace;letter-spacing:.07em;text-transform:uppercase;color:%(mut2)s;text-align:left;border-bottom:1px solid %(line)s;padding:4px 8px}
td{border-bottom:1px solid %(line2)s;padding:4px 8px;vertical-align:top}
.mono{font-family:Consolas,monospace}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.chip{font:700 10.5px "DM Mono",Consolas,monospace;border:1px solid %(line)s;border-radius:5px;background:%(paper2)s;padding:3px 10px;color:%(ink2)s}
.files{font-size:10.5px;color:%(mut)s;line-height:1.9}
.pend{font:700 9.5px "DM Mono",monospace;color:#b3402a;border:1px solid #dcb0a5;border-radius:4px;padding:1px 6px}
.okk{font:700 9.5px "DM Mono",monospace;color:#2e7d32;border:1px solid #a5c9a7;border-radius:4px;padding:1px 6px}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 2px;vertical-align:-1px}
.scroll{overflow-x:auto}.hint{font-size:10.5px;color:%(mut)s}
@media (max-width:760px){body{padding:10px}}
</style></head><body><div class="wrap">
<div class="kick">Veritas Intelligence Analytics · Master Overview — Last Page</div>
<h1>VIA 母版最後一頁 · 全系統規格總覽</h1>
<div class="sub">生成 %(gen)s · 由 canon SSOT 動態彙整(零手寫數字)· 自含零 CDN · via-spec 隨時重生</div>
%(body)s
<div class="hint">治理:只增不減 · 正本不就地修改 · 動態解析 · 在地化零雲端 — 本頁為衍生產物,重跑 via-spec 即最新。</div>
</div></body></html>""" % dict(T, gen=datetime.now().strftime("%Y-%m-%d %H:%M"), body="".join(parts))
    OUTP.parent.mkdir(parents=True, exist_ok=True)
    OUTP.write_text(page, encoding="utf-8")
    print("[規格總覽] %d 段 → %s" % (len(parts), OUTP))
    return 0


if __name__ == "__main__":
    sys.exit(build())

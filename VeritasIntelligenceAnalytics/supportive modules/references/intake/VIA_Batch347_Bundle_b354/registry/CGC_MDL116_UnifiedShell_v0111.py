#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL116_UnifiedShell — 統一版型殼引擎(批302;操作員令)
====================================================================
操作員令:「將總控及各子系統弄成如圖示的使用者介面」+中途裁示
「不管色票只管 layout 及內容輸入介面」。
四設計正本(全在庫;hash 已收容):
  圖1 VAP_Workbench_v023(intake b245)·圖2 VDF_Fetch_ONE Standalone
  ·圖3 ETF Matrix(Dashboard_Format_Standardization)·圖4 UIUX
  Design Source「Veritas Intelligence Analytics UI.html」。
版型五律(自四正本萃取;色票=單一中性=操作員裁示):
  ①左欄:品牌區(拉丁小字 letterspaced+中文大標+版本徽章)+
    編號導航(01/02/03…中文粗體+英文小字;active 高亮)+
    底部狀態小格(四格 key/value)
  ②主區麵包屑鏈(a → b → c · LAYOUT SPEC)
  ③規格帶(BUILD/TASKS/PAGES/GATE 鍵值對;右上)
  ④大數字統計卡列(數字+中文標+英文小字)
  ⑤內容卡(標題+雙語副標+目錄表;表頭=中文 粗+英文 letterspaced)
產出四子系統殼頁(真值全直取零發明):
  VIA_UI_Shell_CGC_v0100.html /_VDF /_VRN /_VAP
  資料源:MDL112 Atlas gather()+MDL095 task_registry()(任務依
  argv 引擎路徑歸系統)+MDL105 LINKS/PAGE_ROSTER(區內頁面冊)
  +台帳筆數。總控台輸入介面=MANAGER v0106 同律改造(本引擎只管
  四殼頁;總控=Manager ui 職權=零重造)。
紀律:零 CDN 零外網(字體=系統字疊);頁名 v0100 穩定律;
誠實三態(樞紐任務數/頁數缺=如實標)。
v0100→v0101(批303 操作員令「字體小一點比較專業 layout 緊湊
一點」):全字階 -1~2px+間距收 25%(緊湊專業階;結構零變)。
v0101→v0102(批324 操作員令「VapDeck 整合所有功能到 Shell_CGC;
Shell_VRN 連 Revenue/ETF 共識分析;完成系統與 U/I 連結」):
  ①頁面冊=真連結(頁族→ui_support 尾版檔 href+KB+更新時戳;零純文字)
  ②CGC 殼=全功能整合殼:內嵌 VapDeck 尾版四頁籤(月營收/族群/ETF 持股
    /個股 K線;CSS 以 .deck 作用域隔離;fetch 一律絕對樞紐
    http://127.0.0.1:8765=file:// 頁可用,CORS 已開;離線=誠實橫幅)
    +全頁索引(ui_support 42 頁族全列真連結+歸屬區標)
  ③VRN 殼區內頁面直連二共識分析頁(MDL105 v0116 LINKS 直取)
  ④自測 +③檢:頁面冊全連結在位/CGC 內嵌四頁籤+絕對樞紐/全頁索引守恆
v0102→v0103(批332 操作員令「六主體統整成標準系統 U/I 前後端相連」):
  導航頂增「系統總台 System」(MDL120 產;六主體;樞紐 /api/*)+⑩檢。
v0103→v0104(批333 Codex 安全模型採納):CGC 殼 file:// 開啟先探樞紐同源
/VIA_UI_Shell_CGC_v0100.html 導向(副作用呼叫由 shim 轉 POST);總控台導航→樞紐 /master。
v0104→v0105(批336):導航 +上船件冊 IntakeRoster。
用法:python3 CGC_MDL116_UnifiedShell_v0105.py [--selftest]
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
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"



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

def _mod(pat: str):
    p = sorted(HERE.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# 四殼定義(職能敘述=各系統既有定位;零發明)
SHELLS = {
    "CGC": {"page": "VIA_UI_Shell_CGC_v0100.html", "seal": "理",
            "zh": "中央治理", "en": "CENTRAL GOVERNANCE",
            "sub": "統一編碼 · 權威登錄 · 台帳 append-only —— 不執行擷取,只裁定何者為真",
            "crumb": ["VIA 母系統", "治理 · SSOT · 編碼", "現況總覽"],
            "links_key": "governance"},
    "VDF": {"page": "VIA_UI_Shell_VDF_v0100.html", "seal": "庫",
            "zh": "資料鍛造", "en": "VERITAS DATA FORGE",
            "sub": "台股全市場+全球 11 類擷取 · 單庫 SSOT · 誠實三態不假綠",
            "crumb": ["VIA 母系統", "VDF 擷取 · 入庫", "資料現況"],
            "links_key": "vdf"},
    "VRN": {"page": "VIA_UI_Shell_VRN_v0100.html", "seal": "觀",
            "zh": "報告新星", "en": "VERITAS REPORT NOVA",
            "sub": "券商報告五法擷取 · 結構化入庫 · 目標價迴歸 TP 100%",
            "crumb": ["VIA 母系統", "VRN 報告 · 共識", "報告現況"],
            "links_key": "vrn"},
    "VAP": {"page": "VIA_UI_Shell_VAP_v0100.html", "seal": "繪",
            "zh": "自動繪圖", "en": "VERITAS AUTO PLOT",
            "sub": "圖表契約 · TPN 模板 · 標準儀表板 —— 更新模板=引用圖全同步",
            "crumb": ["VIA 母系統", "VAP 圖表 · 模板", "繪圖現況"],
            "links_key": "vap"},
}
ORDER = ["CGC", "VDF", "VRN", "VAP"]

CSS = """
:root{--bg:#f5f5f2;--paper:#ffffff;--paper2:#fafaf8;--ink:#1f2530;
--ink2:#3c4658;--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;
--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d;
--rail-w:224px;--hd:84px;--ft:30px}
html{scrollbar-width:thin;scrollbar-color:rgba(60,70,88,.28) transparent}
*::-webkit-scrollbar{width:6px;height:6px}
*::-webkit-scrollbar-thumb{background:rgba(60,70,88,.28);border-radius:3px}
*::-webkit-scrollbar-track{background:transparent}
.led{display:inline-block;width:8px;height:8px;border-radius:50%;
vertical-align:middle;margin-right:5px;background:var(--mut2);
box-shadow:0 0 0 2px rgba(0,0,0,.04)}
.led.ok{background:var(--ok)}.led.warn{background:var(--warn)}
.led.bad{background:var(--bad)}.led.off{background:var(--mut2);opacity:.5}
.railtg{position:fixed;left:calc(var(--rail-w) - 12px);top:calc(var(--hd) + 8px);
z-index:30;width:22px;height:22px;border:1px solid var(--line);
background:var(--paper);border-radius:50%;cursor:pointer;font-size:11px;
line-height:20px;text-align:center;color:var(--mut);box-shadow:0 1px 3px rgba(0,0,0,.08);
transition:left .18s}
.railtg:hover{color:var(--ink)}
body.railc{--rail-w:0px}
body.railc .rail{display:none}
body.railc .railtg{left:6px}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);
font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;display:flex;
min-height:100vh}
code,.mono{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
/* ①左欄 */
/* v0106 輸入面板(VDF/VRN) */
.rin{margin:6px 8px 3px;padding:6px 8px;border:1px solid var(--line);
border-radius:6px;background:var(--paper2)}
.rin .t{font-size:8.5px;letter-spacing:.2em;color:var(--mut2);font-weight:700;
margin-bottom:5px}
.rin .g{margin:6px 0 2px;font-size:10px;font-weight:700;color:var(--ink2)}
.rin label{display:block;font-size:9.5px;color:var(--mut);margin:4px 0 1px}
.rin input,.rin select,.rin textarea{width:100%;font:11px/1.4 inherit;
padding:4px 6px;border:1px solid var(--line);border-radius:4px;
background:var(--paper);color:var(--ink)}
.rin textarea{min-height:44px;resize:vertical}
.rin .chk{display:flex;flex-direction:column;gap:2px;max-height:110px;
overflow:auto;border:1px solid var(--line);border-radius:4px;padding:4px 6px;
background:var(--paper)}
.rin .chk label{display:flex;gap:6px;align-items:center;margin:0;
font-size:10px;color:var(--ink2)}
.rin .chk input{width:auto}
.rin .row{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.rin .btn{display:block;width:100%;margin-top:8px;padding:6px 8px;
font:11px/1 inherit;font-weight:700;letter-spacing:.06em;color:#fff;
background:var(--acc);border:0;border-radius:4px;cursor:pointer}
.rin .btn:hover{filter:brightness(1.08)}
.rin .hint{font-size:9px;color:var(--mut2);margin-top:5px;line-height:1.35}
.rin .out{display:none;margin-top:6px;font:9.5px/1.35 Consolas,monospace;
padding:6px;background:var(--paper);border:1px dashed var(--line);
border-radius:4px;white-space:pre-wrap;word-break:break-all;max-height:120px;
overflow:auto}
.rin .out.show{display:block}
.rin .out.bad{border-color:var(--bad);color:var(--bad)}
.rin .out.ok{border-color:var(--ok);color:var(--ok)}
.panels{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}
.fmx{width:100%;border-collapse:collapse;font-size:10.5px;margin-top:6px}
.fmx th,.fmx td{padding:3px 5px;border-bottom:1px solid var(--line);text-align:left;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:160px}
.fmx th{font-size:9px;letter-spacing:.1em;color:var(--mut2)}
.fmx tr.dup td{background:rgba(181,138,62,.10)}
.fmx tr.exist td{background:rgba(176,92,77,.08)}
.drop{margin-top:5px;border:1.5px dashed var(--line);border-radius:5px;padding:9px 6px;
text-align:center;font-size:10px;color:var(--mut);background:var(--paper);cursor:pointer}
.drop.over{border-color:var(--acc);background:var(--soft);color:var(--ink)}
.fmbar{display:flex;gap:6px;align-items:center;margin-top:5px;font-size:10px}
.fmbar button{font:10px/1 inherit;padding:3px 7px;border:1px solid var(--line);
background:var(--paper);border-radius:3px;cursor:pointer;color:var(--ink2)}
.vcol{white-space:normal!important;max-width:none!important}
.fmsec{margin-top:6px;border:1px solid var(--line);border-radius:5px;background:var(--paper)}
.fmsec>summary{cursor:pointer;padding:6px 9px;font-size:11px;font-weight:700;color:var(--ink2);
list-style:none;display:flex;gap:8px;align-items:center}
.fmsec>summary::-webkit-details-marker{display:none}
.fmsec>summary .n{margin-left:auto;font-weight:400;color:var(--mut2);font-size:10px}
.fmsec .fmx td{max-width:220px}
.fmsec .fmx td.id{color:var(--acc);font-weight:700}
.fmtop{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:10.5px;margin:4px 0}
.fmtop .pill{font-size:9.5px}
.panels .card{margin:0}
.panels .card.full{grid-column:1/-1}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;font-size:11px}
.kv .k{color:var(--mut);font-weight:700;font-size:9.5px;letter-spacing:.06em}
.pill{display:inline-block;font-size:9px;font-weight:700;padding:1px 6px;
border-radius:3px;border:1px solid var(--line);color:var(--mut)}
.pill.ok{color:var(--ok);border-color:var(--ok)}
.pill.warn{color:var(--warn);border-color:var(--warn)}
.pill.bad{color:var(--bad);border-color:var(--bad)}
@media(max-width:900px){.panels{grid-template-columns:1fr}}
.rail{width:var(--rail-w);min-width:var(--rail-w);background:var(--paper);
border-right:1px solid var(--line);padding:0 0 8px;display:flex;
flex-direction:column;gap:3px;position:sticky;top:0;height:100vh;
overflow-y:auto}
.brand{height:var(--hd);display:flex;flex-direction:column;justify-content:center;
position:sticky;top:0;background:var(--paper);z-index:5}
.brand{padding:0 14px 0;border-bottom:1px solid var(--line)}
.brand .latin{font-size:9.5px;letter-spacing:.22em;color:var(--mut);
font-weight:700}
.brand h1{font-size:16px;margin:3px 0 1px;letter-spacing:.02em}
.brand .en{font-size:9.5px;letter-spacing:.14em;color:var(--acc);
font-weight:700}
.brand .badge{display:inline-block;margin-top:5px;font-size:9.5px;
font-weight:700;padding:2px 8px;border:1px solid var(--line);
border-radius:4px;color:var(--mut);letter-spacing:.08em}
.seal{float:right;width:28px;height:28px;border:2px solid var(--ink2);
border-radius:6px;display:grid;place-items:center;font-size:15px;
font-weight:700}
.navsec{font-size:8.5px;letter-spacing:.2em;color:var(--mut2);
font-weight:700;padding:10px 16px 3px}
.nav a{display:grid;grid-template-columns:26px 1fr;gap:8px;
align-items:baseline;padding:5px 16px;color:var(--ink2)}
.nav a:hover{background:var(--paper2);text-decoration:none}
.nav a.active{background:var(--soft);border-right:3px solid var(--acc);
color:var(--ink);font-weight:700}
.nav .no{font-size:9px;color:var(--mut2);font-weight:700}
.nav .lb small{display:block;font-size:8.5px;letter-spacing:.14em;
color:var(--mut2);font-weight:600}
.railfoot{margin-top:auto;border-top:1px solid var(--line);
padding:8px 16px 0;display:grid;grid-template-columns:1fr 1fr;gap:8px}
.railfoot .k{font-size:9px;letter-spacing:.16em;color:var(--mut2);
font-weight:700}
.railfoot .v{font-size:11.5px;font-weight:700;
font-variant-numeric:tabular-nums}
/* 主區 */
.main{flex:1;padding:0 18px 0;max-width:1240px;min-width:0}
.hdwrap{position:sticky;top:0;z-index:6;background:var(--bg);height:var(--hd);
display:flex;flex-direction:column;justify-content:flex-end;padding-top:6px}
.crumb{font-size:9.5px;color:var(--mut);letter-spacing:.04em;
margin-bottom:4px}
.crumb b{color:var(--acc)}
.crumb .lock{letter-spacing:.16em;font-weight:700;font-size:10px}
.head{display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap;
border-bottom:2px solid var(--ink);padding-bottom:6px;margin-bottom:9px}
.head h2{font-size:24px;letter-spacing:.01em;line-height:1.1}
.head h2 small{font-size:10px;color:var(--mut);font-weight:400;
margin-left:10px;letter-spacing:.1em}
.head .sub{width:100%;font-size:11px;color:var(--mut)}
/* ③規格帶 */
.spec{margin-left:auto;display:flex;gap:16px;flex-wrap:wrap}
.spec div{text-align:left}
.spec .k{font-size:9px;letter-spacing:.18em;color:var(--mut2);
font-weight:700}
.spec .v{font-size:11px;font-weight:700;
font-variant-numeric:tabular-nums}
.spec .v.ok{color:var(--ok)}.spec .v.warn{color:var(--warn)}
/* ④統計卡 */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));
gap:8px;margin-bottom:12px}
.stat{background:var(--paper);border:1px solid var(--line);
border-radius:7px;padding:9px 12px}
.stat .n{font-size:27px;font-weight:800;
font-variant-numeric:tabular-nums}
.stat .zh{font-size:10.5px;color:var(--ink2);margin-top:2px}
.stat .en{font-size:9px;letter-spacing:.18em;color:var(--mut2);
font-weight:700}
/* ⑤內容卡 */
.card{background:var(--paper);border:1px solid var(--line);
border-radius:7px;padding:12px 14px;margin-bottom:10px}
.card h3{font-size:12.5px;letter-spacing:.02em}
.card h3 small{font-size:10px;letter-spacing:.16em;color:var(--mut2);
font-weight:700;margin-left:8px}
.card .note{font-size:10px;color:var(--mut);margin:3px 0 7px}
.tbl{width:100%;border-collapse:collapse;font-size:11px}
.tbl th{text-align:left;font-size:10px;letter-spacing:.14em;
color:var(--mut2);border-bottom:1px solid var(--line);padding:4px 8px 4px 0;
font-weight:700}
.tbl td{border-bottom:1px solid var(--soft);padding:4px 8px 4px 0;
vertical-align:top}
.tbl tr:last-child td{border-bottom:0}
.tag{display:inline-block;font-size:10px;font-weight:700;padding:1px 7px;
border-radius:3px;background:var(--soft);color:var(--ink2)}
.tag.net{background:#f3ece1;color:var(--warn)}
.wrap-x{overflow-x:auto}
.foot{position:sticky;bottom:0;background:var(--bg);z-index:5;
height:var(--ft);display:flex;align-items:center;border-top:1px solid var(--line);
margin-top:10px;font-size:10.5px;color:var(--mut2);margin-top:6px}
/* 響應雙態(批302 中途令):PC=水平長方形(左欄+主區);
   手機=垂直長方形(欄轉頂條+導航橫捲+單欄卡);自動最佳化=
   clamp 流體字級+auto-fit 卡格+表格自 overflow;零動畫零校正負擔 */
.head h2{font-size:clamp(17px,2.4vw,23px)}
.stat .n{font-size:clamp(17px,2vw,21px)}
@media(max-width:860px){
 body{flex-direction:column}
 .rail{width:100%;min-width:0;padding:14px 0 8px;position:static}
 .brand{padding:0 16px 10px}
 .brand h1{font-size:18px}
 .nav{display:flex;overflow-x:auto;gap:2px;padding:0 10px;
  -webkit-overflow-scrolling:touch}
 .nav a{grid-template-columns:auto;white-space:nowrap;padding:7px 10px;
  border-radius:6px}
 .nav a.active{border-right:0;border-bottom:3px solid var(--acc)}
 .nav .no{display:none}
 .nav .lb small{display:none}
 .railfoot{grid-template-columns:repeat(4,1fr);padding:10px 16px 0}
 .main{padding:16px 14px}
 .spec{margin-left:0;gap:14px}
 .stats{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:400px){.stats{grid-template-columns:1fr}}
"""


BRIDGE = "http://127.0.0.1:8765"


def page_families() -> dict:
    """ui_support 全頁族(尾版檔;KB;更新時戳)=真連結源"""
    fam: dict = {}
    for f in sorted(UI.glob("VIA_UI_*.html")):
        base = re.sub(r"_v\d+$", "", f.stem)[len("VIA_UI_"):]
        st = f.stat()
        fam[base] = {"file": f.name, "kb": round(st.st_size / 1024, 1),
                     "ts": datetime.fromtimestamp(st.st_mtime).strftime("%m-%d %H:%M")}
    return fam


def _scope_css(css: str, scope: str = ".deck") -> str:
    """VapDeck CSS 作用域化:每條規則選擇器前綴 scope;:root 律→scope;body/*→scope"""
    out = []
    for rule in css.split("}"):
        if "{" not in rule:
            continue
        sel, body = rule.split("{", 1)
        sels = []
        for one in sel.split(","):
            one = one.strip()
            if not one:
                continue
            if one in (":root", "body", "*"):
                sels.append(scope if one != "*" else scope + " *")
            else:
                sels.append(f"{scope} {one}")
        out.append(", ".join(sels) + "{" + body + "}")
    return "\n".join(out)


def deck_embed() -> dict:
    """VapDeck 尾版四頁籤內嵌件(批324):body 內容+作用域 CSS+絕對樞紐 JS;缺=誠實空"""
    hits = sorted(UI.glob("VIA_UI_VapDeck_v0*.html"))
    if not hits:
        return {"css": "", "body": "", "js": "", "src": "", "tabs": 0}
    raw = hits[-1].read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", raw, re.S)
    body = re.search(r'<div class="wrap">(.*?)<div class="foot">', raw, re.S)
    js = re.search(r"<script>(.*?)</script>", raw, re.S)
    b = body.group(1) if body else ""
    b = re.sub(r"<h1>.*?</h1>\s*<div class=\"mut\">.*?</div>", "", b, count=1, flags=re.S)
    b = re.sub(r'<div class="off" id="offline">.*?</div>',
               '<div class="off" id="offline">⚠ 樞紐 127.0.0.1:8765 未連線(誠實):於倉庫根打 <b>via</b> 帶起後重新整理</div>',
               b, count=1, flags=re.S)
    j = js.group(1) if js else ""
    j = ("var B='" + BRIDGE + "';\n"
         "/* 批340:不自動導向;同源版連結由 BRIDGE 探測後在規格帶被動出現 */\n"
         + j.replace("J('/", "J(B+'/").replace("fetch('/ping')", "fetch(B+'/ping')"))
    return {"css": _scope_css(css.group(1) if css else ""), "body": b, "js": j,
            "src": hits[-1].name, "tabs": b.count('class="tab')}


def _allpages_rows(fam: dict, roster: dict) -> str:
    rows = []
    for i, (k, v) in enumerate(sorted(fam.items()), 1):
        area = roster.get(k) or "—"
        rows.append(f'<tr><td class="mono">{i:02d}</td>'
                    f'<td><a href="{html.escape(v["file"])}">{html.escape(k)}</a></td>'
                    f'<td><span class="tag">{html.escape(str(area))}</span></td>'
                    f'<td class="mono">{v["kb"]}</td><td class="mono">{v["ts"]}</td></tr>')
    return "".join(rows)


def _n(x) -> int:
    """真值正規化:list/dict=計數;數=原值(atlas 欄型混=實錘)"""
    if isinstance(x, (list, dict, set, tuple)):
        return len(x)
    return int(x) if isinstance(x, (int, float)) else 0


# ===== v0106 真值直取:VDF 參數冊 / 資料現況 · VRN 稽核冊 =====
def _vdf_params() -> dict:
    """VDF_Param_Registry 尾版:依 src 引擎歸 財報/國際商品/其他(真取零發明)"""
    out = {"file": "", "total": 0, "fin": 0, "global": 0, "other": 0,
           "engines": [], "harvested": ""}
    try:
        cands = sorted((VIA / "functional modules" / "VDF").glob("VDF_Param_Registry_v*.json"))
        if not cands:
            return out
        f = cands[-1]
        import json as _json
        d = _json.loads(f.read_text(encoding="utf-8"))
        params = d.get("params", []) or []
        out["file"] = f.name
        out["total"] = len(params)
        eng = {}
        hv = ""
        for p in params:
            if not isinstance(p, dict):
                continue
            src = str(p.get("src", ""))
            hv = max(hv, str(p.get("harvested", "")))
            eng[src] = eng.get(src, 0) + 1
            low = src.lower()
            if any(k in low for k in ("financial", "revenue", "eps", "fundamental", "sentiment")):
                out["fin"] += 1
            elif any(k in low for k in ("global", "commodity", "fx", "freight", "macro", "fred")):
                out["global"] += 1
            else:
                out["other"] += 1
        out["engines"] = sorted(eng.items(), key=lambda kv: -kv[1])
        out["harvested"] = hv
    except Exception:
        pass
    return out


def _vdf_status() -> dict:
    """dict/VDF/DATABASE 實掃:dataset × 檔數/首末日(缺=誠實空)"""
    out = {"root": "", "present": False, "rows": [], "files": 0}
    try:
        db = VIA / "dict" / "VDF" / "DATABASE"
        out["root"] = str(db)
        if not db.is_dir():
            return out
        out["present"] = True
        groups = {}
        for f in db.iterdir():
            if not f.is_file():
                continue
            out["files"] += 1
            stem = f.stem
            key = re.sub(r"[_-]?\d{6,8}.*$", "", stem) or stem
            dates = re.findall(r"(20\d{6})", stem)
            g = groups.setdefault(key, {"n": 0, "min": "", "max": "", "kb": 0})
            g["n"] += 1
            g["kb"] += f.stat().st_size // 1024
            for dt in dates:
                g["min"] = min(g["min"] or dt, dt)
                g["max"] = max(g["max"], dt)
        out["rows"] = sorted(({"ds": k, **v} for k, v in groups.items()), key=lambda r: r["ds"])
    except Exception:
        pass
    return out


def _vrn_snapshot() -> dict:
    """區內最新 01_repair 稽核冊(repair_audit.csv+financial_data.jsonl)真取;缺=誠實空"""
    out = {"present": False, "src": "", "docs": 0, "methods": {}, "status": {},
           "tickers": 0, "ratings": 0, "targets": 0, "fin_rows": 0, "fin_metrics": {},
           "warn_docs": 0, "q_min": None, "q_med": None, "q_max": None,
           "sources": [], "unverified": 0}
    try:
        base = VIA / "functional modules" / "VRN"
        cands = [p for p in base.rglob("repair_audit.csv")
                 if "SCOPE_COPY" not in p.parts and "rollback" not in p.parts]
        if not cands:
            return out
        f = max(cands, key=lambda p: p.stat().st_mtime)
        import csv as _csv
        import statistics as _st
        rows = list(_csv.DictReader(f.open(encoding="utf-8-sig")))
        out["present"] = True
        out["src"] = str(f.relative_to(VIA))
        out["docs"] = len(rows)
        q = []
        for r in rows:
            m = r.get("extraction_method", "") or "?"
            out["methods"][m] = out["methods"].get(m, 0) + 1
            st = r.get("status", "") or "?"
            out["status"][st] = out["status"].get(st, 0) + 1
            if r.get("ticker"):
                out["tickers"] += 1
            if r.get("rating"):
                out["ratings"] += 1
            if r.get("target_price"):
                out["targets"] += 1
            try:
                if int(r.get("warning_count", "0") or 0) > 0:
                    out["warn_docs"] += 1
            except Exception:
                pass
            try:
                q.append(float(r.get("quality_after", "") or "nan"))
            except Exception:
                pass
            src = r.get("source", "") or r.get("broker", "")
            if src and src not in out["sources"]:
                out["sources"].append(src)
        q = [x for x in q if x == x]
        if q:
            out["q_min"], out["q_med"], out["q_max"] = min(q), _st.median(q), max(q)
        fin = f.parent / "financial_data.jsonl"
        if fin.exists():
            import json as _json
            for line in fin.open(encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = _json.loads(line)
                except Exception:
                    continue
                out["fin_rows"] += 1
                met = str(rec.get("metric", "?")).upper()
                out["fin_metrics"][met] = out["fin_metrics"].get(met, 0) + 1
                if str(rec.get("evidence", "")).upper().startswith("UNVERIFIED"):
                    out["unverified"] += 1
    except Exception:
        pass
    return out


def _vrn_incoming() -> dict:
    """VRN/input/incoming 真掃(名/尺寸/副檔名)供拖入去重比對;缺=誠實空"""
    out = {"path": "", "present": False, "files": [], "n": 0}
    try:
        p = VIA / "functional modules" / "VRN" / "input" / "incoming"
        out["path"] = str(p)
        if not p.is_dir():
            return out
        out["present"] = True
        for f in sorted(p.iterdir()):
            if f.is_file() and f.suffix.lower() in (".pdf", ".docx", ".doc"):
                out["files"].append({"n": f.name, "s": f.stat().st_size, "e": f.suffix.lower().lstrip(".")})
        out["n"] = len(out["files"])
    except Exception:
        pass
    return out


def _vdf_buckets(status: dict) -> dict:
    """DATABASE 資料集分兩桶(操作員裁:國際股市每日交易 / 台股+國際財報);欄名經 pyarrow(缺=誠實)"""
    out = {"global_daily": [], "financials": [], "other": [], "pyarrow": False}
    try:
        import pyarrow.parquet as _pq  # noqa
        out["pyarrow"] = True
    except Exception:
        _pq = None
    db = VIA / "dict" / "VDF" / "DATABASE"
    if not db.is_dir():
        return out
    for r in status.get("rows", []):
        name = r["ds"].lower()
        cols = []
        if out["pyarrow"]:
            try:
                sample = next((f for f in db.iterdir() if f.is_file() and f.stem.lower().startswith(name) and f.suffix.lower() == ".parquet"), None)
                if sample:
                    cols = list(_pq.read_schema(sample).names)[:12]
            except Exception:
                cols = []
        row = {**r, "cols": cols}
        if any(k in name for k in ("financial", "revenue", "eps", "fundamental", "income", "balance")):
            out["financials"].append(row)
        elif any(k in name for k in ("global", "price", "index", "daily", "fx", "commodity", "freight")):
            out["global_daily"].append(row)
        else:
            out["other"].append(row)
    return out


THRESH_DEFAULT = {
    "ticker_coverage_pct": {"green": 60, "yellow": 30},
    "quality_median": {"green": 90, "yellow": 80},
    "warn_docs_pct": {"green": 10, "yellow": 40},
    "metric_coverage_pct": {"green": 100, "yellow": 33},
}


def _thresholds() -> dict:
    """批342:門檻冊真取;缺=內建預設+CONSTANT_FALLBACK 誠實標"""
    out = {"source": "CONSTANT_FALLBACK", "file": "", "t": dict(THRESH_DEFAULT)}
    try:
        cands = sorted(HERE.glob("VIA_ShellValidation_Thresholds_v*.json"))
        if cands:
            import json as _json
            d = _json.loads(cands[-1].read_text(encoding="utf-8"))
            th = d.get("thresholds", {})
            t = {}
            for k, dv in THRESH_DEFAULT.items():
                v = th.get(k, {})
                t[k] = {"green": v.get("green", dv["green"]), "yellow": v.get("yellow", dv["yellow"])}
            out = {"source": "SOURCED", "file": cands[-1].name, "t": t}
    except Exception:
        pass
    return out


def _fetch_matrix() -> dict:
    """VDF_FetchOne_Matrix_Registry 尾版真嵌(批340:顯示所有擷取的資料內容;缺=誠實空)"""
    out = {"file": "", "items": [], "counts": {}, "sections": [], "generated": ""}
    try:
        cands = sorted((VIA / "functional modules" / "VDF").glob("VDF_FetchOne_Matrix_Registry_v*.json"))
        if not cands:
            return out
        import json as _json
        d = _json.loads(cands[-1].read_text(encoding="utf-8"))
        items = [i for i in d.get("items", []) if isinstance(i, dict)]
        out["file"] = cands[-1].name
        out["items"] = items
        out["generated"] = str(d.get("generated", ""))
        cm = d.get("counts_measured") or {}
        st = {}
        for i in items:
            st[str(i.get("status", "?"))] = st.get(str(i.get("status", "?")), 0) + 1
        out["counts"] = {"total": len(items), **st, "registry_counts_measured": cm}
        secs = []
        for i in items:
            sname = str(i.get("section", "")) or "(無 section)"
            if sname not in secs:
                secs.append(sname)
        out["sections"] = secs
    except Exception:
        pass
    return out


def _auto_start(status: dict) -> str:
    """VDF 起始日自動律:DATABASE 末日+1;缺=今日-30(誠實預填,可改)"""
    from datetime import timedelta, date as _date
    best = ""
    for r in status.get("rows", []):
        if r.get("max") and r["max"] > best:
            best = r["max"]
    try:
        if len(best) == 8:
            d = datetime.strptime(best, "%Y%m%d").date() + timedelta(days=1)
            return d.isoformat()
    except Exception:
        pass
    return (_date.today() - timedelta(days=30)).isoformat()


def _sys_of_task(argv) -> str:
    s = " ".join(str(a) for a in argv).replace("\\", "/")
    if "/VDF/" in s or "VDF_" in s:
        return "VDF"
    if "/VRN/" in s or "VRN_" in s:
        return "VRN"
    if "/VAP/" in s or "VAP_" in s:
        return "VAP"
    return "CGC"


def gather() -> dict:
    """真值聚合(全直取零發明;缺=誠實 0/空)"""
    d = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M")}
    try:
        d["atlas"] = _mod("CGC_MDL112_SystemAtlas_v0*.py").gather()
    except Exception:
        d["atlas"] = {}
    try:
        T = _mod("CGC_MDL095_DeckServer_v0*.py").task_registry()
        d["tasks"] = {k: {"zh": v.get("zh", ""), "net": bool(v.get("net")),
                          "sys": _sys_of_task(v.get("argv", []))}
                      for k, v in T.items()}
    except Exception:
        d["tasks"] = {}
    try:
        m105 = _mod("CGC_MDL105_GovernanceConsole_v0*.py")
        d["links"] = {k: list(v) for k, v in m105.LINKS.items()}
        d["roster"] = dict(m105.PAGE_ROSTER)
    except Exception:
        d["links"] = {}
        d["roster"] = {}
    d["fam"] = page_families()
    d["deck"] = deck_embed()
    d["vdf_params"] = _vdf_params()
    d["vdf_status"] = _vdf_status()
    d["vdf_buckets"] = _vdf_buckets(d["vdf_status"])
    d["vdf_start"] = _auto_start(d["vdf_status"])
    d["fetch_matrix"] = _fetch_matrix()
    d["thresh"] = _thresholds()
    d["vrn"] = _vrn_snapshot()
    d["vrn_in"] = _vrn_incoming()
    try:
        m95 = _mod("CGC_MDL095_DeckServer_v0*.py")
        d["global_cats"] = sorted(m95.GLOBAL_CATEGORIES)
        d["intake_dests"] = sorted(getattr(m95, "INTAKE_DESTS", set()))
        d["deck_tasks"] = set(m95.task_registry().keys())
    except Exception:
        d["global_cats"] = []
        d["intake_dests"] = []
        d["deck_tasks"] = set()
    return d


def _nav(cur: str, d: dict) -> str:
    rows = ['<div class="navsec">系統 SYSTEMS</div><div class="nav">',
            '<a href="VIA_UI_IntakeRoster_v0100.html"><span class="no">船'
            '</span><span class="lb">上船件冊<small>INTAKE ROSTER · 批336</small>'
            '</span></a>',
            '<a href="VIA_UI_System_v0100.html"><span class="no">統'
            '</span><span class="lb">系統總台<small>STANDARD SYSTEM UI · 6 SUBJECTS</small>'
            '</span></a>',
            '<a href="http://127.0.0.1:8765/master"><span class="no">00'
            '</span><span class="lb">總控台<small>MASTER CONTROL · 樞紐同源 /master</small>'
            '</span></a>']
    for i, k in enumerate(ORDER, 1):
        s = SHELLS[k]
        cls = ' class="active"' if k == cur else ""
        rows.append(
            f'<a href="{s["page"]}"{cls}><span class="no">0{i}</span>'
            f'<span class="lb">{s["zh"]} · {k}<small>{s["en"]}</small>'
            f'</span></a>')
    rows.append("</div>")
    links = d.get("links", {}).get(SHELLS[cur]["links_key"], [])
    if links:
        rows.append('<div class="navsec">區內頁面 PAGES</div>'
                    '<div class="nav">')
        for j, (zh, href) in enumerate(links, 1):
            rows.append(
                f'<a href="{html.escape(str(href))}">'
                f'<span class="no">{j:02d}</span>'
                f'<span class="lb">{html.escape(str(zh))}</span></a>')
        rows.append("</div>")
    return "".join(rows)


# ===== v0106 輸入面板(左欄) =====
def _rail_inputs(cur: str, d: dict) -> str:
    if cur == "VDF":
        vp = d.get("vdf_params", {})
        cats = d.get("global_cats", [])
        ZH = {"idx": "指數", "etf": "ETF", "us_jp": "美日股", "fin_reports": "財報",
              "oil": "原油", "fx": "匯率", "cmdty": "商品", "crypto": "加密",
              "us_macro": "美總經", "fed": "聯準會", "us_fiscal_rates": "美財政利率"}
        GROUPS = [("財報 FINANCIAL", ["fin_reports"]),
                  ("國際商品 GLOBAL COMMODITY", ["oil", "fx", "cmdty"]),
                  ("國際股市 GLOBAL EQUITY", ["idx", "etf", "us_jp"]),
                  ("總經 MACRO", ["us_macro", "fed", "us_fiscal_rates", "crypto"])]
        seen = set()
        blocks = ""
        for gzh, keys in GROUPS:
            ks = [k for k in keys if k in cats]
            if not ks:
                continue
            seen.update(ks)
            blocks += f'<div class="g">{gzh} <span class="mono" style="font-weight:400;color:var(--mut2)">{len(ks)}</span></div><div class="chk">' + "".join(
                f'<label><input type="checkbox" name="cats" value="{k}">{ZH.get(k, k)} <span class="mono" style="color:var(--mut2)">{k}</span></label>' for k in ks) + '</div>'
        rest = [k for k in cats if k not in seen]
        if rest:
            blocks += '<div class="g">其他 OTHER</div><div class="chk">' + "".join(
                f'<label><input type="checkbox" name="cats" value="{k}">{ZH.get(k, k)} <span class="mono" style="color:var(--mut2)">{k}</span></label>' for k in rest) + '</div>'
        src_note = (f"類別冊=DeckServer GLOBAL_CATEGORIES 真取 {len(cats)} 類" if cats
                    else "DeckServer 缺→類別冊空(誠實;殼不發明類別)")
        has_task = "global" in d.get("deck_tasks", set())
        return f'''<div class="rin" id="rin">
<div class="t">INPUT RAIL · 輸入面板</div>
<form id="vdfForm" onsubmit="return VIA_submitVDF(event)">
<div class="g">① 新增 / 移除資料 <span class="mono" style="font-weight:400;color:var(--mut2)">CATEGORIES</span></div>
{blocks or '<div class="chk"><label><span class="led off"></span>類別冊空(誠實)</label></div>'}
<div class="hint">{src_note} · 勾選=納入本次全球宇宙擷取(任務 global;只增不減)</div>
<div class="row">
<div><label>起始日期 START <span class="mono" style="color:var(--mut2)">auto</span></label><input type="date" name="start" value="{d.get("vdf_start", "")}" required></div>
<div><label>結束日期 END <span class="mono" style="color:var(--mut2)">留空=今日(契約:起訖成對)</span></label><input type="date" name="end"></div>
</div>
<button class="btn" type="submit"{"" if has_task else " disabled"}>送出 → 樞紐 POST /run · task=global</button>
<div class="hint"><span class="led {"ok" if has_task else "bad"}"></span>任務冊 global {"在位" if has_task else "缺(誠實;鈕停用)"} · 參數冊={html.escape(vp.get("file", "缺"))} 總 {vp.get("total", 0)}(財報 {vp.get("fin", 0)} · 國際 {vp.get("global", 0)})<br>契約=白名單 {{task,codes,start,end,cats}}(批304);本頁零直執行;需同源開啟(file://=只檢視)</div>
<div class="out" id="vdfOut"></div>
</form></div>'''
    if cur == "VRN":
        vi = d.get("vrn_in", {})
        import json as _json
        inc_json = html.escape(_json.dumps([{"n": f["n"], "s": f["s"]} for f in vi.get("files", [])], ensure_ascii=False), quote=True)
        inc_led = "ok" if vi.get("present") and vi.get("n", 0) > 0 else ("warn" if vi.get("present") else "bad")
        return f'''<div class="rin" id="rin" data-incoming="{inc_json}">
<div class="t">INPUT RAIL · 輸入面板</div>
<form id="vrnForm" onsubmit="return VIA_submitVRN(event)">
<div class="g">增加輸入 <span class="mono" style="font-weight:400;color:var(--mut2)">ADD INPUT · Windows 拖曳</span></div>
<div class="drop" id="drop" onclick="document.getElementById('fpick').click()">拖曳 PDF / DOCX 至此<br><span style="font-size:9px">或點此選檔(可多選)</span></div>
<input type="file" id="fpick" name="files" multiple accept=".pdf,.docx,.doc" style="display:none" onchange="VIA_addFiles(this.files)">
<div class="fmbar"><span id="fmcount" class="mono">0 件</span>
<button type="button" onclick="VIA_selAll(true)">全選</button>
<button type="button" onclick="VIA_selAll(false)">全不選</button>
<button type="button" onclick="VIA_selAll(null)">反選</button>
<button type="button" onclick="VIA_clearFiles()">清空</button></div>
<div class="chk" style="max-height:150px;padding:0"><table class="fmx" id="fmx"><thead><tr><th></th><th>檔名 NAME</th><th>格式</th><th>KB</th><th>券商</th><th>日期</th><th>狀態</th></tr></thead><tbody id="fmb"></tbody></table></div>
<div class="hint"><span class="led {inc_led}"></span>incoming 現有 {vi.get("n", 0)} 件(伺服端真掃;拖入同名=WARN 已在庫;同尺寸=WARN 疑似同源;同名重拖=跳過)</div>
<label>路徑 PATH <span class="mono" style="color:var(--mut2)">auto</span></label><input type="text" name="path" value="{html.escape(vi.get("path", ""))}">
<label>收件後續 AFTER INTAKE</label><select name="method">
<option value="none">只收件 INTAKE ONLY</option>
<option value="firstpage"{"" if "firstpage" in d.get("deck_tasks", set()) else " disabled"}>ENG072 首頁擷取(task firstpage){"" if "firstpage" in d.get("deck_tasks", set()) else " · 任務冊缺"}</option>
<option value="firstpage+structdb"{"" if {"firstpage", "structdb"} <= d.get("deck_tasks", set()) else " disabled"}>首頁擷取 → 結構化入庫(firstpage→structdb)</option>
<option value="four_engine" disabled>四引擎套件 · 任務冊無此鍵(誠實)</option>
</select>
<button class="btn" type="submit">送出勾選檔 → 樞紐 POST /intake · dest=vrn_incoming</button>
<div class="hint">每檔 base64 逐送;伺服端 hash 去重(同名同 hash=冪等 200;同名異 hash=_sha8 讓位 201;零覆寫)。券商/日期=檔名判讀(民國7碼→西元)。需同源開啟(file://=只檢視)</div>
<div class="out" id="vrnOut"></div>
</form></div>'''
    return ""


BRIDGE_PROBE = """
<script>
(function(){var k='via.rail.collapsed';try{if(localStorage.getItem(k)==='1')document.body.classList.add('railc');}catch(e){}
 var t=document.createElement('button');t.className='railtg';t.title='收起/展開左欄';t.textContent='\u2039';
 function sync(){var c=document.body.classList.contains('railc');t.textContent=c?'\u203a':'\u2039';try{localStorage.setItem(k,c?'1':'0');}catch(e){}}
 t.onclick=function(){document.body.classList.toggle('railc');sync();};document.body.appendChild(t);sync();})();
(function(){var B='%s',l=document.getElementById('bled'),t=document.getElementById('btxt');if(!l)return;
 var c=new AbortController();var tm=setTimeout(function(){c.abort();},2500);
 fetch(B+'/probe',{mode:'no-cors',cache:'no-store',signal:c.signal}).then(function(){clearTimeout(tm);
   var same=(location.origin===B);l.className='led '+(same?'ok':'warn');
   if(same){t.textContent='127.0.0.1:8765 同源在線';}
   else{t.innerHTML='127.0.0.1:8765 在線 · <a href="'+B+'/'+location.pathname.split('/').pop()+(location.hash||'')+'" title="需送出時再點(批340:不自動導向)">開同源版 ›</a>';}
 }).catch(function(){clearTimeout(tm);l.className='led bad';t.textContent='127.0.0.1:8765 離線(誠實)';});})();
</script>
""" % BRIDGE


RAIL_JS = r"""
<script>
var B='%s';
var FM=[];var INC={};
(function(){try{var r=document.getElementById('rin');if(!r)return;var a=JSON.parse(r.getAttribute('data-incoming')||'[]');a.forEach(function(x){INC[x.n]=x.s;});}catch(e){}})();
var BR=[['兆豐','兆豐'],['華南','華南'],['凱基','凱基'],['統一','統一'],['台新','台新'],['MS-','MS'],['GS-','GS'],['UBS','UBS'],['Daiwa','Daiwa'],['JP-','JP'],['GF-','GF'],['MQ-','MQ']];
function VIA_guess(n){var b='';for(var i=0;i<BR.length;i++){if(n.indexOf(BR[i][0])>=0){b=BR[i][1];break;}}
 var d='',m=n.match(/(20\d{6})/);if(m){d=m[1].slice(0,4)+'-'+m[1].slice(4,6)+'-'+m[1].slice(6,8);}
 else{m=n.match(/(?:^|\D)(1[0-2]\d{5})(?:\D|$)/);if(m){var y=parseInt(m[1].slice(0,3),10)+1911;d=y+'-'+m[1].slice(3,5)+'-'+m[1].slice(5,7);}}
 return {b:b,d:d};}
function VIA_addFiles(fl){var added=0;for(var i=0;i<fl.length;i++){var f=fl[i];
 if(FM.some(function(x){return x.n===f.name;}))continue;
 var g=VIA_guess(f.name);FM.push({n:f.name,e:(f.name.split('.').pop()||'').toLowerCase(),s:f.size,b:g.b,d:g.d,on:true,file:f});added++;}
 VIA_render();}
function VIA_render(){var tb=document.getElementById('fmb'),cnt=document.getElementById('fmcount');if(!tb)return;tb.innerHTML='';
 var sizes={};FM.forEach(function(x){sizes[x.s]=(sizes[x.s]||0)+1;});
 FM.forEach(function(x,i){var st=[],cls='';
  if(INC[x.n]!==undefined){st.push('已在 incoming');cls='exist';}
  if(sizes[x.s]>1){st.push('同尺寸疑似同源');cls=cls||'dup';}
  var led=cls==='exist'?'bad':(cls==='dup'?'warn':'ok');
  var tr=document.createElement('tr');tr.className=cls;
  tr.innerHTML='<td><input type="checkbox" '+(x.on?'checked':'')+' onchange="FM['+i+'].on=this.checked;VIA_count()"></td>'+
   '<td title="'+x.n.replace(/"/g,'&quot;')+'">'+x.n+'</td><td>'+x.e+'</td><td>'+Math.round(x.s/1024)+'</td>'+
   '<td><input type="text" value="'+x.b+'" style="width:52px" onchange="FM['+i+'].b=this.value"></td>'+
   '<td><input type="date" value="'+x.d+'" style="width:108px" onchange="FM['+i+'].d=this.value"></td>'+
   '<td><span class="led '+led+'"></span>'+(st.join(' / ')||'新')+'</td>';
  tb.appendChild(tr);});
 VIA_count();}
function VIA_count(){var c=document.getElementById('fmcount');if(c)c.textContent=FM.filter(function(x){return x.on;}).length+' / '+FM.length+' 件';}
function VIA_selAll(v){FM.forEach(function(x){x.on=(v===null)?!x.on:v;});VIA_render();}
function VIA_clearFiles(){FM=[];VIA_render();}
(function(){var z=document.getElementById('drop');if(!z)return;
 ['dragenter','dragover'].forEach(function(e){z.addEventListener(e,function(ev){ev.preventDefault();z.classList.add('over');});});
 ['dragleave','drop'].forEach(function(e){z.addEventListener(e,function(ev){ev.preventDefault();z.classList.remove('over');});});
 z.addEventListener('drop',function(ev){if(ev.dataTransfer&&ev.dataTransfer.files)VIA_addFiles(ev.dataTransfer.files);});})();
function VIA_copy(txt){try{navigator.clipboard.writeText(txt);}catch(e){}}
function VIA_gate(o){
  if(location.origin!==B){o.className='out show';o.textContent='獨立頁(file://)=不連 server(批340)。載荷已備妥,可複製貼總控台;要直接送出請點規格帶「開同源版」。';return false;}
  return true;}
function VIA_submitVDF(ev){
  ev.preventDefault();var f=ev.target,o=document.getElementById('vdfOut');
  var cats=[];new FormData(f).forEach(function(v,k){if(k==='cats')cats.push(v);});
  var end=f.end.value||new Date().toISOString().slice(0,10);
  var p={task:'global',start:f.start.value,end:end,cats:cats.join(',')};
  if(!cats.length){o.className='out show bad';o.textContent='未勾選任何類別(誠實)';return false;}
  if(!VIA_gate(o)){var js=JSON.stringify(p,null,1);o.textContent+='\n\n載荷 JSON:\n'+js;var b=document.createElement('button');b.type='button';b.textContent='複製載荷';b.style.cssText='margin-top:6px;font:10px/1 inherit;padding:3px 8px';b.onclick=function(){VIA_copy(js);b.textContent='已複製';};o.appendChild(b);return false;}
  o.className='out show';o.textContent='POST /run … '+JSON.stringify(p);
  fetch('/run',{method:'POST',body:JSON.stringify(p)})
   .then(function(r){return r.text().then(function(t){return {ok:r.ok,st:r.status,t:t};});})
   .then(function(r){o.className='out show '+(r.ok?'ok':'bad');o.textContent='樞紐 '+r.st+'\n'+r.t.slice(0,800);})
   .catch(function(e){o.className='out show bad';o.textContent='送出失敗(誠實): '+e;});
  return false;}
function VIA_b64(file){return new Promise(function(res,rej){var r=new FileReader();r.onload=function(){res(String(r.result).split(',')[1]||'');};r.onerror=rej;r.readAsDataURL(file);});}
function VIA_submitVRN(ev){
  ev.preventDefault();var f=ev.target,o=document.getElementById('vrnOut');
  var sel=FM.filter(function(x){return x.on;});
  if(!sel.length){o.className='out show bad';o.textContent='未勾選任何檔案(誠實)';return false;}
  if(!VIA_gate(o)){var js=JSON.stringify({sys:'vrn',dest:'vrn_incoming',method:f.method.value,path:f.path.value,files:sel.map(function(x){return {name:x.n,ext:x.e,bytes:x.s,broker:x.b,date:x.d};})},null,1);o.textContent+='\n\n載荷 JSON(檔案本體不隨 JSON 走):\n'+js;var b=document.createElement('button');b.type='button';b.textContent='複製載荷';b.style.cssText='margin-top:6px;font:10px/1 inherit;padding:3px 8px';b.onclick=function(){VIA_copy(js);b.textContent='已複製';};o.appendChild(b);return false;}
  var method=f.method.value,log=[],i=0;o.className='out show';
  function step(){if(i>=sel.length){return after();}var x=sel[i++];var file=null;
    var fp=document.getElementById('fpick');for(var j=0;fp&&j<fp.files.length;j++){if(fp.files[j].name===x.n){file=fp.files[j];break;}}
    if(!file&&x.file)file=x.file;
    if(!file){log.push('SKIP '+x.n+' (無檔案物件;請重新拖入)');o.textContent=log.join('\n');return step();}
    VIA_b64(file).then(function(b64){return fetch('/intake',{method:'POST',body:JSON.stringify({name:x.n,b64:b64,dest:'vrn_incoming'})});})
     .then(function(r){return r.json().then(function(j){return {st:r.status,j:j};});})
     .then(function(r){var j=r.j||{};log.push((r.st===201?'新收 ':(r.st===200?'冪等 ':'拒 '))+r.st+' '+x.n+(j.skip?' · '+j.skip:'')+(j.saved?' → '+j.saved.split(/[\\/]/).pop():'')+(j.err?' · '+j.err:''));o.textContent=log.join('\n');step();})
     .catch(function(e){log.push('失敗 '+x.n+' '+e);o.textContent=log.join('\n');step();});}
  function after(){if(method==='none'){o.className='out show ok';return;}
    var tasks=method==='firstpage+structdb'?['firstpage','structdb']:['firstpage'];
    (function run(k){if(k>=tasks.length){o.className='out show ok';return;}
      fetch('/run',{method:'POST',body:JSON.stringify({task:tasks[k]})}).then(function(r){return r.text().then(function(t){log.push('task '+tasks[k]+' → '+r.status+' '+t.slice(0,160));o.textContent=log.join('\n');run(k+1);});})
      .catch(function(e){log.push('task '+tasks[k]+' 失敗 '+e);o.textContent=log.join('\n');run(k+1);});})(0);}
  step();return false;}
</script>
""" % BRIDGE


def _fetch_matrix_panel(d: dict) -> str:
    fm = d.get("fetch_matrix", {})
    items = fm.get("items", [])
    if not items:
        return ('<div class="card full"><h3>擷取資料總冊<small>FETCH MATRIX</small></h3>'
                '<div class="note"><span class="led warn"></span>VDF_FetchOne_Matrix_Registry 缺(誠實空)</div></div>')
    c = fm.get("counts", {})
    def led(stt):
        return {"DONE": "ok", "PROXY": "warn", "TODO": "off"}.get(stt, "bad")
    top = (f'<div class="fmtop"><span class="pill">總 {c.get("total", 0)}</span>'
           f'<span class="pill ok"><span class="led ok"></span>DONE {c.get("DONE", 0)}</span>'
           f'<span class="pill warn"><span class="led warn"></span>PROXY {c.get("PROXY", 0)}</span>'
           f'<span class="pill"><span class="led off"></span>TODO {c.get("TODO", 0)}</span>'
           f'<span class="mono" style="color:var(--mut2)">{html.escape(fm.get("file", ""))} · {html.escape(fm.get("generated", ""))}</span></div>')
    secs = ""
    for sname in fm.get("sections", []):
        rows = [i for i in items if (str(i.get("section", "")) or "(無 section)") == sname]
        done = sum(1 for i in rows if i.get("status") == "DONE")
        trs = "".join(
            f'<tr><td class="id mono">{html.escape(str(i.get("id", "")))}</td>'
            f'<td title="{html.escape(str(i.get("name", "")))}">{html.escape(str(i.get("name", "")))}</td>'
            f'<td class="mono">{html.escape(str(i.get("source", "")))}</td>'
            f'<td class="mono">{html.escape(str(i.get("fetcher", "")))}</td>'
            f'<td class="mono">{html.escape(str(i.get("freq", "")))}</td>'
            f'<td class="vcol mono" style="font-size:9.5px">{html.escape(str(i.get("fields", "")))}</td>'
            f'<td class="mono">{html.escape(str(i.get("refs", "")))}</td>'
            f'<td><span class="led {led(str(i.get("status", "")))}"></span>{html.escape(str(i.get("status", "")))}</td></tr>'
            for i in rows)
        secs += (f'<details class="fmsec"><summary><span class="led {"ok" if done == len(rows) else ("warn" if done else "off")}"></span>'
                 f'{html.escape(sname)}<span class="n">{done}/{len(rows)} DONE</span></summary>'
                 f'<div class="wrap-x"><table class="fmx"><tr><th>碼</th><th>資料項 ITEM</th><th>來源</th><th>FETCHER</th><th>頻率</th><th class="vcol">主要欄位 FIELDS</th><th>消費</th><th>狀態</th></tr>{trs}</table></div></details>')
    return (f'<div class="card full"><h3>擷取資料總冊<small>FETCH MATRIX · ALL DATA VIA VDF</small></h3>'
            f'<div class="note">登錄冊尾版真嵌(零發明);section 可摺疊;狀態燈=DONE 綠 / PROXY 黃 / TODO 灰。'
            f'此冊=「VDF 顯示所有擷取的資料內容」之單一真相。</div>{top}{secs}</div>')


# ===== v0106 顯示面板(右主區) =====
def _panels(cur: str, d: dict) -> str:
    def card(title, en, body, full=False):
        return (f'<div class="card{" full" if full else ""}"><h3>{title}<small>{en}</small></h3>{body}</div>')
    if cur == "VDF":
        vs = d.get("vdf_status", {})
        vp = d.get("vdf_params", {})
        if vs.get("present") and vs.get("rows"):
            rows = "".join(
                f'<tr><td class="mono">{html.escape(r["ds"])}</td><td class="mono">{r["n"]}</td>'
                f'<td class="mono">{r["min"] or "—"}</td><td class="mono">{r["max"] or "—"}</td>'
                f'<td class="mono">{r["kb"]}</td></tr>' for r in vs["rows"])
            tbl = (f'<div class="wrap-x"><table class="tbl"><tr><th>資料集 DATASET</th><th>檔 FILES</th>'
                   f'<th>首 FIRST</th><th>末 LAST</th><th>KB</th></tr>{rows}</table></div>')
            note = f'<div class="note">DATABASE 實掃 {vs.get("files", 0)} 檔 · {html.escape(vs.get("root", ""))}</div>'
        else:
            tbl = ""
            note = (f'<div class="note"><span class="pill warn">誠實空</span> DATABASE 缺或空:'
                    f'{html.escape(vs.get("root", ""))} — 左欄勾選資料集+起始日期送樞紐後再生</div>')
        eng = "".join(f'<tr><td class="mono">{html.escape(k)}</td><td class="mono">{v}</td></tr>'
                      for k, v in (vp.get("engines") or [])[:12]) or '<tr><td colspan="2">參數冊缺(誠實)</td></tr>'
        pcard = card("參數歸類", f'PARAM REGISTRY · {vp.get("total", 0)}',
                     f'<div class="kv"><div class="k">財報 FINANCIAL</div><div>{vp.get("fin", 0)}</div>'
                     f'<div class="k">國際商品 GLOBAL</div><div>{vp.get("global", 0)}</div>'
                     f'<div class="k">其他 OTHER</div><div>{vp.get("other", 0)}</div>'
                     f'<div class="k">採收 HARVESTED</div><div class="mono">{html.escape(vp.get("harvested", "—"))}</div></div>'
                     f'<div class="wrap-x" style="margin-top:6px"><table class="tbl"><tr><th>來源引擎 SRC</th><th>參數 N</th></tr>{eng}</table></div>')
        bk = d.get("vdf_buckets", {})
        def _brows(rows):
            if not rows:
                return '<tr><td colspan="5"><span class="led off"></span>此桶無資料集(誠實空)</td></tr>'
            return "".join(
                f'<tr><td class="mono">{html.escape(r["ds"])}</td><td class="mono">{r["n"]}</td>'
                f'<td class="mono">{r["min"] or "—"}</td><td class="mono">{r["max"] or "—"}</td>'
                f'<td class="mono vcol" style="font-size:9.5px">{html.escape(", ".join(r.get("cols", [])) or ("(pyarrow 缺:欄名不讀)" if not bk.get("pyarrow") else "—"))}</td></tr>'
                for r in rows)
        bled = "ok" if (bk.get("global_daily") or bk.get("financials")) else "warn"
        ext = (f'<div class="note"><span class="led {bled}"></span>操作員裁:可行擷取內容僅二桶=國際股市每日交易數據 · 台股與國際股票財報。'
               f'其他資料集列於「其他」誠實不併桶。欄名={"pyarrow 讀取" if bk.get("pyarrow") else "pyarrow 缺(誠實)"}。</div>'
               f'<div class="g" style="margin-top:6px;font-size:10.5px;font-weight:700">① 國際股市每日交易數據 <span class="mono" style="font-weight:400;color:var(--mut2)">GLOBAL DAILY · {len(bk.get("global_daily", []))}</span></div>'
               f'<table class="fmx"><tr><th>資料集</th><th>檔</th><th>首</th><th>末</th><th class="vcol">欄 COLUMNS</th></tr>{_brows(bk.get("global_daily", []))}</table>'
               f'<div class="g" style="margin-top:6px;font-size:10.5px;font-weight:700">② 台股 + 國際股票財報 <span class="mono" style="font-weight:400;color:var(--mut2)">FINANCIALS · {len(bk.get("financials", []))}</span></div>'
               f'<table class="fmx"><tr><th>資料集</th><th>檔</th><th>首</th><th>末</th><th class="vcol">欄 COLUMNS</th></tr>{_brows(bk.get("financials", []))}</table>'
               + (f'<div class="g" style="margin-top:6px;font-size:10.5px;font-weight:700">其他 <span class="mono" style="font-weight:400;color:var(--mut2)">OTHER · {len(bk.get("other", []))}</span></div>'
                  f'<table class="fmx"><tr><th>資料集</th><th>檔</th><th>首</th><th>末</th><th class="vcol">欄</th></tr>{_brows(bk.get("other", []))}</table>' if bk.get("other") else ""))
        return (f'<div class="panels">{_fetch_matrix_panel(d)}{card("擷取內容", "EXTRACTED CONTENT", ext, full=True)}'
                f'{card("資料現況矩陣", "DATA STATUS MATRIX", note + tbl, full=True)}{pcard}'
                f'{card("顯示規約", "DISPLAY RULE", "<div class=\"note\">左欄=輸入(增減資料·起始日 auto·財報·國際商品參數);右區=顯示。<br>資料集歸類=參數冊 src 引擎名關鍵字;起始日=DATABASE 末日+1(缺=今日-30)。</div>")}</div>')
    if cur == "VRN":
        v = d.get("vrn", {})
        if not v.get("present"):
            empty = '<div class="note"><span class="pill warn">誠實空</span> 區內無 01_repair/repair_audit.csv — 左欄輸入送樞紐後再生</div>'
            return (f'<div class="panels">{card("SUMMARY MATRIX", "摘要矩陣", empty, full=True)}'
                    f'{card("BASIC INFO", "基本資訊", empty)}{card("SUMMARY", "摘要", empty)}'
                    f'{card("FINANCIAL DATA", "財務數據", empty)}{card("VALIDATE MATRIX", "驗證矩陣", empty)}</div>')
        meth = "".join(f'<tr><td class="mono">{html.escape(k)}</td><td class="mono">{n}</td></tr>' for k, n in sorted(v["methods"].items(), key=lambda kv: -kv[1]))
        stat = "".join(f'<tr><td class="mono">{html.escape(k)}</td><td class="mono">{n}</td></tr>' for k, n in sorted(v["status"].items(), key=lambda kv: -kv[1]))
        sm = (f'<div class="wrap-x"><table class="tbl"><tr><th>擷取法 METHOD</th><th>件 N</th></tr>{meth}</table></div>'
              f'<div class="wrap-x" style="margin-top:6px"><table class="tbl"><tr><th>狀態 STATUS</th><th>件 N</th></tr>{stat}</table></div>')
        docs = max(1, v["docs"])
        def _v(cond_ok, cond_warn, ok_t, warn_t, bad_t):
            if cond_ok: return f'<span class="led ok"></span>{ok_t}'
            if cond_warn: return f'<span class="led warn"></span>{warn_t}'
            return f'<span class="led bad"></span>{bad_t}'
        TH = d.get("thresh", {}).get("t", THRESH_DEFAULT)
        tsrc = d.get("thresh", {}).get("source", "CONSTANT_FALLBACK")
        tfile = d.get("thresh", {}).get("file", "")
        tk = v["tickers"] * 100 // docs
        bi = (f'<table class="fmx"><tr><th>項 FIELD</th><th>值 VALUE</th><th class="vcol">驗證 VALIDATION</th></tr>'
              f'<tr><td>來源冊 SRC</td><td class="mono">{html.escape(v["src"].split("/")[-3] if "/" in v["src"] else v["src"])}</td><td class="vcol">{_v(v["present"], False, "稽核冊在位", "", "缺")}</td></tr>'
              f'<tr><td>文件 DOCS</td><td>{v["docs"]}</td><td class="vcol">{_v(v["docs"] > 0, False, "非空", "", "0 件")}</td></tr>'
              f'<tr><td>券商 SOURCES</td><td>{len(v["sources"])}</td><td class="vcol">{_v(len(v["sources"]) > 1, len(v["sources"]) == 1, "多源可交叉", "單源", "無來源欄")}</td></tr>'
              f'<tr><td>有代碼 TICKER</td><td>{v["tickers"]} ({tk}%)</td><td class="vcol">{_v(tk >= TH["ticker_coverage_pct"]["green"], tk >= TH["ticker_coverage_pct"]["yellow"], "覆蓋合理", "偏低:多為產業/策略報告本無單一標的", "極低:檢查抽取器")}</td></tr>'
              f'<tr><td>有評等 RATING</td><td>{v["ratings"]}</td><td class="vcol">{_v(v["ratings"] > 0, False, "有評等", "", "全無")}</td></tr>'
              f'<tr><td>有目標價 TP</td><td>{v["targets"]}</td><td class="vcol">{_v(v["targets"] <= v["ratings"] and v["targets"] > 0, v["targets"] == 0, "TP≤評等數 合理", "無 TP", "TP>評等數 異常")}</td></tr>'
              f'</table><div class="note">驗證規則:代碼覆蓋≥{TH["ticker_coverage_pct"]["green"]}% 綠/≥{TH["ticker_coverage_pct"]["yellow"]}% 黃;TP 數不得超過評等數;來源>1 才可交叉核對。門檻=<span class="pill {"ok" if tsrc == "SOURCED" else "warn"}">{tsrc}</span> {html.escape(tfile)}</div>')
        qn = "—" if v["q_med"] is None else f'{v["q_min"]:.1f} / {v["q_med"]:.1f} / {v["q_max"]:.1f}'
        qok = v["q_med"] is not None and v["q_med"] >= TH["quality_median"]["green"]
        qwn = v["q_med"] is not None and v["q_med"] >= TH["quality_median"]["yellow"]
        wr = v["warn_docs"] * 100 // docs
        su = (f'<table class="fmx"><tr><th>項 FIELD</th><th>值 VALUE</th><th class="vcol">驗證 VALIDATION</th></tr>'
              f'<tr><td>品質 min/med/max</td><td class="mono">{qn}</td><td class="vcol">{_v(qok, qwn, "中位≥" + str(TH["quality_median"]["green"]), "中位 " + str(TH["quality_median"]["yellow"]) + "-" + str(TH["quality_median"]["green"]) + ":雙欄版面偏弱", "中位<" + str(TH["quality_median"]["yellow"]))}</td></tr>'
              f'<tr><td>含警告 WARN DOCS</td><td>{v["warn_docs"]} ({wr}%)</td><td class="vcol">{_v(wr < TH["warn_docs_pct"]["green"], wr < TH["warn_docs_pct"]["yellow"], "警告率<" + str(TH["warn_docs_pct"]["green"]) + "%", "警告率偏高", "警告率>" + str(TH["warn_docs_pct"]["yellow"]) + "%")}</td></tr>'
              f'<tr><td>財務筆數 FIN ROWS</td><td>{v["fin_rows"]}</td><td class="vcol">{_v(v["fin_rows"] > 0, False, "有擷取", "", "0 筆")}</td></tr>'
              f'<tr><td>未驗證 UNVERIFIED</td><td>{v["unverified"]}</td><td class="vcol">{_v(False, True, "", "擷取物非驗證物:進 SSOT 前回 TWSE/TDCC/原報告核對", "")}</td></tr>'
              f'</table><div class="note">驗證規則:品質中位數 ≥{TH["quality_median"]["green"]} 綠 / ≥{TH["quality_median"]["yellow"]} 黃;警告率 <{TH["warn_docs_pct"]["green"]}% 綠 / <{TH["warn_docs_pct"]["yellow"]}% 黃。門檻=<span class="pill {"ok" if tsrc == "SOURCED" else "warn"}">{tsrc}</span></div>')
        def _mv(k, n):
            cov = n * 100 // docs
            if cov >= TH["metric_coverage_pct"]["green"]: return f'<span class="led ok"></span>每件≥1 筆'
            if cov >= TH["metric_coverage_pct"]["yellow"]: return f'<span class="led warn"></span>覆蓋 {cov}%'
            return f'<span class="led off"></span>稀疏 {n * 100 // docs}%'
        fm = "".join(f'<tr><td class="mono">{html.escape(k)}</td><td class="mono">{n}</td><td class="vcol">{_mv(k, n)}</td></tr>' for k, n in sorted(v["fin_metrics"].items(), key=lambda kv: -kv[1])[:14]) or '<tr><td colspan="3">financial_data.jsonl 缺(誠實)</td></tr>'
        fd = (f'<table class="fmx"><tr><th>指標 METRIC</th><th>筆 N</th><th class="vcol">驗證 VALIDATION</th></tr>{fm}</table>'
              f'<div class="note">驗證規則=覆蓋率(筆數/文件數):≥{TH["metric_coverage_pct"]["green"]}% 綠 / ≥{TH["metric_coverage_pct"]["yellow"]}% 黃 / 其餘灰。數值本身=擷取物;進 SSOT 前須回源核對。門檻=<span class="pill {"ok" if tsrc == "SOURCED" else "warn"}">{tsrc}</span></div>')
        def _p(ok, txt):
            return f'<span class="pill {"ok" if ok else "warn"}">{txt}</span>'
        vm = (f'<div class="kv">'
              f'<div class="k">四引擎 layout bbox</div><div>{_p(False, "WARN · 純文字語料無座標")}</div>'
              f'<div class="k">text 後端重跑</div><div>{_p(False, "WARN · 輸入已為文字")}</div>'
              f'<div class="k">table 擷取</div><div>{_p(False, "WARN · 0 表")}</div>'
              f'<div class="k">NEEDS_OCR</div><div>{_p(v["status"].get("NEEDS_OCR", 0) == 0, str(v["status"].get("NEEDS_OCR", 0)) + " 件")}</div>'
              f'<div class="k">雙路徑對帳</div><div>{_p(False, "未執行 · 原始 PDF 重跑後才有")}</div></div>'
              f'<div class="note">三結構性 WARN=輸入型態所致(pre-fetched text),非引擎缺陷;以原始 PDF 重跑可關閉。</div>')
        return (f'<div class="panels">{card("SUMMARY MATRIX", "摘要矩陣", sm, full=True)}'
                f'{card("BASIC INFO", "基本資訊", bi)}{card("SUMMARY", "摘要", su)}'
                f'{card("FINANCIAL DATA", "財務數據", fd)}{card("VALIDATE MATRIX", "驗證矩陣", vm)}</div>')
    return ""


def _data_led(cur: str, d: dict) -> str:
    if cur == "VDF":
        st = d.get("vdf_status", {})
        return "ok" if st.get("present") and st.get("files", 0) else "warn"
    if cur == "VRN":
        v = d.get("vrn", {})
        return "ok" if v.get("present") and v.get("docs", 0) else "warn"
    a = d.get("atlas", {})
    return "ok" if _n(a.get("ledger", 0)) else "off"


def _data_txt(cur: str, d: dict) -> str:
    if cur == "VDF":
        st = d.get("vdf_status", {})
        return f'{st.get("files", 0)} 檔' if st.get("present") else "DATABASE 缺"
    if cur == "VRN":
        v = d.get("vrn", {})
        return f'{v.get("docs", 0)} 件 / {v.get("fin_rows", 0)} 筆' if v.get("present") else "稽核冊缺"
    return f'台帳 {_n(d.get("atlas", {}).get("ledger", 0))}'


def _same_origin_redirect(cur: str) -> str:
    """批340:零自動導向。file:// 頁=獨立正本;同源版只作被動連結(見 BRIDGE_PROBE)。"""
    return ""


def _shell_page(cur: str, d: dict) -> str:
    s = SHELLS[cur]
    a = d.get("atlas", {})
    tasks = {k: v for k, v in d.get("tasks", {}).items() if v["sys"] == cur}
    fam = d.get("roster", {})
    pages = sorted(k for k, v in fam.items() if v == s["links_key"])
    crumb = " → ".join(f"<b>{c}</b>" for c in s["crumb"])
    stats = [
        (len(tasks), "一鍵任務", "DECK TASKS"),
        (len(pages), "現役頁族", "PAGE FAMILIES"),
        (_n(a.get("ledger", 0)), "台帳筆數", "LEDGER"),
        (_n(a.get("ssot", 0)), "SSOT 冊", "REGISTRY"),
    ]
    if cur == "CGC":
        stats[3] = (_n(a.get("subs", 0)), "子系統", "SUBSYSTEMS")
    stat_html = "".join(
        f'<div class="stat"><div class="n">{n}</div>'
        f'<div class="zh">{zh}</div><div class="en">{en}</div></div>'
        for n, zh, en in stats)
    tag_net = '<span class="tag net">NET</span>'
    tag_loc = '<span class="tag">本機</span>'
    trows = "".join(
        f'<tr><td><code>{k}</code></td><td>{html.escape(v["zh"])}</td>'
        f'<td>{tag_net if v["net"] else tag_loc}</td></tr>'
        for k, v in sorted(tasks.items())) or (
        '<tr><td colspan="3">此系統暫無深控一鍵任務(誠實空)</td></tr>')
    fmeta = d.get("fam", {})

    def _prow(i, p):
        m = fmeta.get(p)
        if m:
            return (f'<tr><td class="mono">{i:02d}</td>'
                    f'<td><a href="{html.escape(m["file"])}">{html.escape(p)}</a></td>'
                    f'<td class="mono">{m["kb"]}</td><td class="mono">{m["ts"]}</td></tr>')
        return (f'<tr><td class="mono">{i:02d}</td><td>{html.escape(p)}</td>'
                f'<td colspan="2"><span class="tag">尚未產出(誠實)</span></td></tr>')
    prows = "".join(_prow(i, p) for i, p in enumerate(pages, 1)) or (
        '<tr><td colspan="4">頁族冊空(誠實)</td></tr>')
    extra = ""
    if cur == "CGC":
        dk = d.get("deck", {})
        deck_html = (f'<div class="card" id="deck"><h3>分析台(VapDeck 全功能整合)'
                     f'<small>ANALYSIS DECK · {html.escape(dk.get("src", ""))}</small></h3>'
                     f'<div class="note">月營收 · 族群 · ETF 持股 · 個股 K線 四頁籤=VapDeck 尾版原功能'
                     f'內嵌本殼;資料經樞紐 {BRIDGE}(唯讀誠實雙道;離線=橫幅誠實)。</div>'
                     f'<div class="deck">{dk.get("body", "")}</div></div>'
                     if dk.get("body") else
                     '<div class="card" id="deck"><h3>分析台<small>ANALYSIS DECK</small></h3>'
                     '<div class="note">VapDeck 頁缺=誠實空(跑 via-manager ui 再生)</div></div>')
        allrows = _allpages_rows(fmeta, fam)
        extra = deck_html + (
            f'<div class="card" id="allpages"><h3>全頁索引<small>ALL PAGES · {len(fmeta)}</small></h3>'
            f'<div class="note">ui_support 全頁族(尾版檔真連結;歸屬區=MDL105 單一架構歸屬冊;'
            f'KB/更新=檔案實值)。</div><div class="wrap-x"><table class="tbl">'
            f'<tr><th>NO</th><th>頁族 FAMILY</th><th>區 AREA</th><th>KB</th><th>更新 UPDATED</th></tr>'
            f'{allrows}</table></div></div>')
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA · {s["zh"]} {cur} 現況台</title>{_same_origin_redirect(cur)}<style>{CSS}
{d.get("deck", {}).get("css", "") if cur == "CGC" else ""}</style></head><body>
<aside class="rail">
<div class="brand"><span class="seal">{s["seal"]}</span>
<div class="latin">VERITAS INTELLIGENCE ANALYTICS</div>
<h1>{s["zh"]}現況台</h1>
<div class="en">{s["en"]}</div>
<span class="badge">SHELL v0111 · LIVE</span></div>
{_nav(cur, d)}
{_rail_inputs(cur, d)}
<div class="railfoot">
<div><div class="k">TASKS</div><div class="v">{len(tasks)}</div></div>
<div><div class="k">PAGES</div><div class="v">{len(pages)}</div></div>
<div><div class="k">STATE</div><div class="v">LIVE</div></div>
<div><div class="k">LEDGER</div><div class="v">{_n(a.get("ledger", 0))}</div></div>
</div></aside>
<main class="main">
<div class="hdwrap">
<div class="crumb">{crumb} · <span class="lock">LAYOUT SPEC(批302)</span></div>
<div class="head"><h2>{s["zh"]} {cur}<small>{s["en"]}</small></h2>
<div class="spec">
<div><div class="k">BUILD</div><div class="v">SHELL v0111</div></div>
<div><div class="k">TASKS</div><div class="v"><span class="led {"ok" if tasks else "off"}"></span>{len(tasks)}</div></div>
<div><div class="k">DATA</div><div class="v"><span class="led {_data_led(cur, d)}"></span>{_data_txt(cur, d)}</div></div>
<div><div class="k">BRIDGE</div><div class="v"><span class="led warn" id="bled"></span><span id="btxt">127.0.0.1:8765 探測中</span></div></div>
</div>
<div class="sub">{s["sub"]}</div></div></div>
<div class="stats">{stat_html}</div>
{_panels(cur, d)}
<div class="card"><h3>一鍵任務冊<small>DECK TASKS</small></h3>
<div class="note">執行入口=總控台 MasterControl(下拉/勾選;樞紐
127.0.0.1:8765 白名單真跑)。本頁=現況展示(唯讀)。</div>
<div class="wrap-x"><table class="tbl">
<tr><th>任務 TASK</th><th>名稱 NAME</th><th>通路 LANE</th></tr>
{trows}</table></div></div>
<div class="card"><h3>頁面冊<small>PAGE FAMILIES</small></h3>
<div class="note">本區現役頁族(MDL105 單一架構歸屬冊直取;
左欄「區內頁面」可直開)。</div>
<div class="wrap-x"><table class="tbl">
<tr><th>NO</th><th>頁族 FAMILY</th><th>KB</th><th>更新 UPDATED</th></tr>
{prows}</table></div></div>
{extra}
<div class="foot">VIA · {s["en"]} · 真值直取(Atlas+任務冊+歸屬冊)
零發明 · 產於 {d["ts"]} · 版型=批302 四設計正本萃取(hash 已收容)
· 零 CDN 零外網</div>
</main>{("<script>" + d.get("deck", {}).get("js", "") + "</script>") if cur == "CGC" and d.get("deck", {}).get("js") else ""}{BRIDGE_PROBE}{RAIL_JS if cur in ("VDF", "VRN") else ""}</body></html>"""


def run(do_print: bool = True, open_after: bool = False) -> int:
    d = gather()
    UI.mkdir(parents=True, exist_ok=True)
    for k in ORDER:
        (UI / SHELLS[k]["page"]).write_text(apply_type_scale(_shell_page(k, d)),
                                            encoding="utf-8")
    if do_print:
        n_t = len(d.get("tasks", {}))
        print(f"[統一殼] 四子系統殼頁再生 · 任務歸屬 {n_t} · "
              f"台帳 {d.get('atlas', {}).get('ledger', 0)} · "
              + " ".join(SHELLS[k]["page"] for k in ORDER))
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run(do_print=False)
    pages = {k: (UI / SHELLS[k]["page"]).read_text(encoding="utf-8")
             for k in ORDER}
    d = gather()
    chk("① 四殼頁全產出(rc0+檔在位)", rc == 0
        and all((UI / SHELLS[k]["page"]).exists() for k in ORDER))
    chk("② 版型五律全在(左欄導航+麵包屑+規格帶+統計卡+內容卡)",
        all('class="rail"' in p and 'class="crumb"' in p
            and 'class="spec"' in p and 'class="stats"' in p
            and 'class="card"' in p for p in pages.values()))
    chk("③ 編號導航+跨殼互連(00 總控+01-04 四系統)",
        all('http://127.0.0.1:8765/master' in p
            and all(SHELLS[j]["page"] in p for j in ORDER)
            for p in pages.values()))
    chk("④ 真值直取零發明(任務歸屬+台帳數入頁)",
        len(d.get("tasks", {})) >= 30
        and all(str(_n(d.get("atlas", {}).get("ledger", 0))) in p
                for p in pages.values()))
    chk("⑤ 雙語標籤律(中文標+英文 letterspaced)",
        all("VERITAS INTELLIGENCE ANALYTICS" in p
            and SHELLS[k]["en"] in p for k, p in pages.items()))
    chk("⑥ 零 CDN+加速橋+誠實宣告",
        all('<script src="http' not in p and "src=\"http" not in p
            for p in pages.values())
        and "ACCEL-BRIDGE" in src and "誠實" in src)
    fam = d.get("fam", {})
    chk("⑦ 頁面冊真連結(每殼區內頁族 href=尾版檔在位;KB/更新入頁)",
        all(f'href="{fam[p]["file"]}"' in pages[k] for k in ORDER
            for p in (q for q, a in d.get("roster", {}).items() if a == SHELLS[k]["links_key"])
            if p in fam) and all("更新 UPDATED" in p for p in pages.values()))
    dk = d.get("deck", {})
    chk("⑧ CGC 殼內嵌 VapDeck 四頁籤+絕對樞紐+作用域 CSS+離線誠實橫幅",
        dk.get("tabs", 0) >= 4 and 'id="deck"' in pages["CGC"]
        and f"var B='{BRIDGE}'" in pages["CGC"] and "J(B+'/" in pages["CGC"]
        and "J('/" not in pages["CGC"] and ".deck .tab" in pages["CGC"]
        and 'id="offline"' in pages["CGC"] and "id=\"deck\"" not in pages["VDF"])
    chk("⑨ 全頁索引守恆(ui_support 全族均可自 CGC 殼直達)+VRN 殼直連二共識分析頁",
        len(fam) >= 30 and all(f'href="{v["file"]}"' in pages["CGC"] for v in fam.values())
        and "RevenueConsensusAnalysis" in pages["VRN"] and "ETFConsensusAnalysis" in pages["VRN"])
    chk("⑩ 四殼導航頂連系統總台 System(批332)",
        all('href="VIA_UI_System_v0100.html"' in p for p in pages.values()))
    chk("⑪ 批340 零自動導向律(四殼皆無 location.replace;規格帶被動「開同源版」連結)",
        all("location.replace(" not in p for p in pages.values())
        and all("開同源版" in p for p in pages.values()))
    chk("⑫ 四殼導航連上船件冊(批336)", all('href="VIA_UI_IntakeRoster_v0100.html"' in p for p in pages.values()))
    chk("⑬ 輸入面板僅 VDF/VRN 在位(左欄·導航下)·CGC/VAP 零變(批337;v0108 欄名=cats/財報·國際商品分組)",
        'id="rin"' in pages["VDF"] and 'id="rin"' in pages["VRN"]
        and 'id="rin"' not in pages["CGC"] and 'id="rin"' not in pages["VAP"]
        and 'name="start"' in pages["VDF"] and 'name="cats"' in pages["VDF"]
        and "財報 FINANCIAL" in pages["VDF"] and "國際商品 GLOBAL COMMODITY" in pages["VDF"]
        and 'type="file"' in pages["VRN"] and "VIA_submitVDF(" in pages["VDF"]
        and "VIA_submitVRN(" in pages["VRN"] and f"var B='{BRIDGE}'" in pages["VRN"])
    chk("⑭ VRN 五顯示面板全在+VDF 資料現況矩陣+誠實空律",
        all(t in pages["VRN"] for t in ("SUMMARY MATRIX", "BASIC INFO", "SUMMARY<",
                                        "FINANCIAL DATA", "VALIDATE MATRIX"))
        and "DATA STATUS MATRIX" in pages["VDF"] and "PARAM REGISTRY" in pages["VDF"]
        and ("誠實空" in pages["VDF"] or "DATABASE 實掃" in pages["VDF"]))
    chk("⑮ 殼版律(批338):左欄可收(railtg+localStorage)·頁首等高 sticky(--hd/hdwrap)·頁尾 sticky·捲軸 thin·燈號 led 入規格帶(四殼)",
        all("railtg" in p and "via.rail.collapsed" in p and 'class="hdwrap"' in p
            and "--hd:" in p and "scrollbar-width:thin" in p and 'class="led' in p
            and 'id="bled"' in p for p in pages.values()))
    chk("⑯ VRN 拖曳輸入→檔案矩陣(drop+fmx+全選/反選/清空+去重+同尺寸警告+incoming 內嵌真掃)+券商/日期自動判讀+路徑 auto",
        'id="drop"' in pages["VRN"] and 'id="fmx"' in pages["VRN"] and "VIA_selAll(" in pages["VRN"]
        and "VIA_addFiles(" in pages["VRN"] and "data-incoming=" in pages["VRN"]
        and "同尺寸疑似同源" in pages["VRN"] and "已在 incoming" in pages["VRN"]
        and "VIA_guess(" in pages["VRN"] and "1911" in pages["VRN"]
        and 'name="path" value="' in pages["VRN"] and 'id="drop"' not in pages["VDF"])
    chk("⑰ 驗證欄入三面板(BASIC INFO/SUMMARY/FINANCIAL DATA 每列燈號+判定)+VDF 擷取內容二桶+起始日 auto",
        pages["VRN"].count("驗證 VALIDATION") >= 3 and "驗證規則" in pages["VRN"]
        and "EXTRACTED CONTENT" in pages["VDF"] and "GLOBAL DAILY" in pages["VDF"]
        and "FINANCIALS" in pages["VDF"] and 'name="start" value="' in pages["VDF"])
    chk("⑱ 前後端契約(批339):VDF 類別=DeckServer GLOBAL_CATEGORIES 真取(fin_reports 在)·送 /run task=global·VRN 送 /intake dest=vrn_incoming·任務鍵存在檢(firstpage/structdb)·four_engine 誠實停用",
        'value="fin_reports"' in pages["VDF"] and "task:'global'" in pages["VDF"]
        and "fetch('/run'" in pages["VDF"] and "fetch('/intake'" in pages["VRN"]
        and "dest:'vrn_incoming'" in pages["VRN"] and 'value="four_engine" disabled' in pages["VRN"]
        and len(d.get("global_cats", [])) >= 11 and "/api/vrn/intake" not in pages["VRN"]
        and "/api/health" not in pages["VRN"]
        and "end:end" in pages["VDF"])
    chk("⑲ BRIDGE 燈探 /probe(四殼)+file:// 送出=載荷 JSON+複製鈕(誠實零假送)+同源才走 /run /intake",
        all("fetch(B+'/probe'" in p for p in pages.values())
        and "function VIA_gate(" in pages["VRN"] and "function VIA_gate(" in pages["VDF"]
        and "VIA_copy(" in pages["VRN"] and "複製載荷" in pages["VDF"]
        and "獨立頁(file://)=不連 server" in pages["VRN"])
    fmr = d.get("fetch_matrix", {})
    chk("⑳ VDF 擷取資料總冊真嵌(登錄冊項數=頁內列數守恆;DONE/PROXY/TODO 燈;section 摺疊)",
        len(fmr.get("items", [])) >= 300
        and pages["VDF"].count('<td class="id mono">') == len(fmr.get("items", []))
        and "FETCH MATRIX" in pages["VDF"] and '<details class="fmsec">' in pages["VDF"]
        and "FETCH MATRIX" not in pages["VRN"])
    chk("㉑ --open 自動跳出(webbrowser 零 server)在位", "def _open_shells" in src and '"--open" in sys.argv' in src)
    chk("㉒ 結構守恆(四殼 <script>/</script> 與 <div>/</div> 成對;無未閉合)",
        all(p.count("<script") == p.count("</script>") and p.count("<div") == p.count("</div>")
            for p in pages.values()))
    th = d.get("thresh", {})
    chk("㉓ 批342 門檻冊 SSOT(registry 冊在位·頁標 SOURCED·五組數值自冊而非硬碼·冊缺=CONSTANT_FALLBACK 誠實)",
        th.get("source") == "SOURCED" and th.get("file", "").startswith("VIA_ShellValidation_Thresholds_v")
        and pages["VRN"].count("SOURCED") >= 3 and "CONSTANT_FALLBACK" not in pages["VRN"]
        and ("≥" + str(th["t"]["ticker_coverage_pct"]["green"]) + "%") in pages["VRN"]
        and ("tk >= " + "60") not in src and ("wr < " + "10") not in src and ("q_med\"] >= " + "90") not in src)
    chk("㉔ 批347 字階守恆(四殼 <style> 零越階;最大=UISpec fs_xl)", all(all(any(abs(float(v) - px) < 0.01 for _, px in _type_scale()) for v in re.findall(r"font(?:-size)?\\s*:\\s*([0-9.]+)px", p)) for p in pages.values()))
    print(f"  [計] 廿四檢 OK {24 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0



def _open_shells():
    """批340 自動跳出:預設瀏覽器開四殼(file://;零 server)"""
    import webbrowser
    for k in ORDER:
        p = UI / SHELLS[k]["page"]
        if p.exists():
            try:
                webbrowser.open(p.resolve().as_uri())
            except Exception:
                pass


def main() -> int:
    if "--open" in sys.argv:
        rc = run(do_print=True)
        _open_shells()
        return rc
    if "--selftest" in sys.argv[1:]:
        print("=== 統一版型殼引擎(CGC_MDL116 v0111)· 廿三檢自測(零網路)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())

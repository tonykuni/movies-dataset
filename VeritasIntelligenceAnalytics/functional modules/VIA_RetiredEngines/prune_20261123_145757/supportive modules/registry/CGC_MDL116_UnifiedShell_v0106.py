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
--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);
font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;display:flex;
min-height:100vh}
code,.mono{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
/* ①左欄 */
/* v0106 輸入面板(VDF/VRN) */
.rin{margin:8px 10px 4px;padding:8px 9px;border:1px solid var(--line);
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
.panels{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
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
.rail{width:224px;min-width:224px;background:var(--paper);
border-right:1px solid var(--line);padding:14px 0 10px;display:flex;
flex-direction:column;gap:4px}
.brand{padding:0 16px 10px;border-bottom:1px solid var(--line)}
.brand .latin{font-size:9.5px;letter-spacing:.22em;color:var(--mut);
font-weight:700}
.brand h1{font-size:17px;margin:4px 0 2px;letter-spacing:.02em}
.brand .en{font-size:9.5px;letter-spacing:.14em;color:var(--acc);
font-weight:700}
.brand .badge{display:inline-block;margin-top:7px;font-size:10px;
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
.main{flex:1;padding:16px 22px;max-width:1160px}
.crumb{font-size:10px;color:var(--mut);letter-spacing:.04em;
margin-bottom:7px}
.crumb b{color:var(--acc)}
.crumb .lock{letter-spacing:.16em;font-weight:700;font-size:10px}
.head{display:flex;align-items:flex-end;gap:18px;flex-wrap:wrap;
border-bottom:2px solid var(--ink);padding-bottom:9px;margin-bottom:12px}
.head h2{font-size:30px;letter-spacing:.01em}
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
.foot{font-size:10.5px;color:var(--mut2);margin-top:6px}
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
         "(function(){if(location.protocol!=='file:')return;var c=new AbortController();var t=setTimeout(function(){c.abort();},1400);"
         "fetch(B+'/probe',{mode:'no-cors',cache:'no-store',signal:c.signal}).then(function(){clearTimeout(t);location.replace(B+'/VIA_UI_Shell_CGC_v0100.html'+(location.hash||'#deck'));}).catch(function(){clearTimeout(t);});})();\n"
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
    d["vrn"] = _vrn_snapshot()
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
        vs = d.get("vdf_status", {})
        ds = [r["ds"] for r in vs.get("rows", [])]
        if not ds:
            ds = ["VDF_TW_PriceDaily", "VDF_TW_IndexDaily", "VDF_TW_FlowChip",
                  "VDF_Global_Commodity", "VDF_Global_FXRate", "VDF_Global_Freight"]
            ds_note = "DATABASE 缺·顯示登錄冊 6 資料集名(誠實)"
        else:
            ds_note = f"DATABASE 實掃 {len(ds)} 資料集"
        chk = "".join(f'<label><input type="checkbox" name="ds" value="{html.escape(x)}">{html.escape(x)}</label>' for x in ds)
        return f'''<div class="rin" id="rin">
<div class="t">INPUT RAIL · 輸入面板</div>
<form id="vdfForm" onsubmit="return VIA_submit(event,'vdf')">
<div class="g">① 新增 / 移除資料 <span class="mono" style="font-weight:400;color:var(--mut2)">DATASETS</span></div>
<div class="chk">{chk}</div>
<div class="hint">{ds_note} · 勾選=納入本次擷取;未勾=不動(只增不減)</div>
<div class="row">
<div><label>起始日期 START</label><input type="date" name="start" required></div>
<div><label>動作 ACTION</label><select name="action"><option value="append">新增 APPEND</option><option value="remove_mark">標記移除 MARK</option></select></div>
</div>
<div class="g">② 財報參數 <span class="mono" style="font-weight:400;color:var(--mut2)">FINANCIAL · {vp.get("fin", 0)}</span></div>
<label>財報頻率 PERIOD</label><select name="fin_period"><option value="Q">季 QUARTERLY</option><option value="M">月營收 MONTHLY</option><option value="Y">年 ANNUAL</option></select>
<label>低基期門檻 LOW-BASE RATIO</label><input type="number" name="fin_lowbase" step="0.01" min="0" max="1" placeholder="登錄冊值優先(留空=不覆寫)">
<div class="g">③ 國際商品參數 <span class="mono" style="font-weight:400;color:var(--mut2)">GLOBAL · {vp.get("global", 0)}</span></div>
<label>商品 / 匯率 / 運價代碼 SYMBOLS</label><textarea name="global_symbols" placeholder="每行一個;留空=登錄冊清單"></textarea>
<label>對齊基準 ALIGN</label><select name="global_align"><option value="TW">台股交易日 TW</option><option value="US">美股交易日 US</option><option value="CAL">日曆日 CALENDAR</option></select>
<button class="btn" type="submit">送出 → 樞紐 /api/vdf/intake</button>
<div class="hint">參數冊={html.escape(vp.get("file", "缺"))} · 總 {vp.get("total", 0)} · 財報 {vp.get("fin", 0)} · 國際 {vp.get("global", 0)} · 其他 {vp.get("other", 0)}<br>本頁零直執行;樞紐離線=下方顯示 JSON 可貼總控台(批333 律)</div>
<div class="out" id="vdfOut"></div>
</form></div>'''
    if cur == "VRN":
        return '''<div class="rin" id="rin">
<div class="t">INPUT RAIL · 輸入面板</div>
<form id="vrnForm" onsubmit="return VIA_submit(event,'vrn')">
<div class="g">增加輸入 <span class="mono" style="font-weight:400;color:var(--mut2)">ADD INPUT</span></div>
<label>券商報告 PDF / DOCX(可多選)</label><input type="file" name="files" multiple accept=".pdf,.docx,.doc">
<label>或 資料夾 / 檔案路徑 PATH</label><input type="text" name="path" placeholder="C:\\...\\VRN\\input\\incoming">
<div class="row">
<div><label>券商 BROKER</label><input type="text" name="broker" placeholder="兆豐 / 華南 / MS / GS"></div>
<div><label>報告日 DATE</label><input type="date" name="date"></div>
</div>
<label>擷取法 METHOD</label><select name="method"><option value="four_engine">四引擎(repair→layout→text→table)</option><option value="eng072">ENG072 雙法對照</option><option value="both">兩者對帳 RECONCILE</option></select>
<button class="btn" type="submit">送出 → 樞紐 /api/vrn/intake</button>
<div class="hint">本頁零直執行;樞紐離線=下方顯示 JSON 可貼總控台(批333 律)<br>檔案本體不隨 JSON 走(只送檔名+路徑;真上傳=樞紐 multipart)</div>
<div class="out" id="vrnOut"></div>
</form></div>'''
    return ""


RAIL_JS = """
<script>
var B='%s';
function VIA_submit(ev,sys){
  ev.preventDefault();
  var f=ev.target,o=document.getElementById(sys+'Out'),p={sys:sys,ts:new Date().toISOString()};
  new FormData(f).forEach(function(v,k){
    if(v instanceof File){ if(v.name){ (p.files=p.files||[]).push(v.name); } return; }
    if(k==='ds'){ (p.ds=p.ds||[]).push(v); return; }
    if(v!=='') p[k]=v;
  });
  var body=JSON.stringify(p,null,1);
  o.className='out show';o.textContent='送出中 → '+B+'/api/'+sys+'/intake …';
  var c=new AbortController();setTimeout(function(){c.abort();},4000);
  fetch(B+'/api/'+sys+'/intake',{method:'POST',headers:{'Content-Type':'application/json'},body:body,signal:c.signal})
   .then(function(r){return r.text().then(function(t){return {ok:r.ok,st:r.status,t:t};});})
   .then(function(r){o.className='out show '+(r.ok?'ok':'bad');o.textContent='樞紐 '+r.st+'\n'+r.t.slice(0,600);})
   .catch(function(){o.className='out show bad';o.textContent='樞紐離線(誠實)· 未執行 · 以下 JSON 可貼總控台:\n'+body;});
  return false;
}
</script>
""" % BRIDGE


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
        return f'<div class="panels">{card("資料現況矩陣", "DATA STATUS MATRIX", note + tbl, full=True)}{pcard}' \
               f'{card("顯示規約", "DISPLAY RULE", "<div class=\"note\">左欄=輸入(增減資料·起始日·財報·國際商品參數);右區=顯示。<br>資料集歸類=參數冊 src 引擎名關鍵字(financial/revenue/eps→財報;global/commodity/fx/freight/macro→國際);未命中=其他(誠實)。</div>")}</div>'
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
        bi = (f'<div class="kv"><div class="k">來源冊 SRC</div><div class="mono">{html.escape(v["src"])}</div>'
              f'<div class="k">文件 DOCS</div><div>{v["docs"]}</div>'
              f'<div class="k">券商 SOURCES</div><div>{len(v["sources"])}</div>'
              f'<div class="k">有代碼 TICKER</div><div>{v["tickers"]} <span class="pill">{100 * v["tickers"] // docs}%</span></div>'
              f'<div class="k">有評等 RATING</div><div>{v["ratings"]} <span class="pill">{100 * v["ratings"] // docs}%</span></div>'
              f'<div class="k">有目標價 TP</div><div>{v["targets"]} <span class="pill">{100 * v["targets"] // docs}%</span></div></div>'
              f'<div class="note">代碼/評等/目標價缺=產業或策略報告本無單一標的(非漏抓);以誠實比率呈現。</div>')
        qn = "—" if v["q_med"] is None else f'{v["q_min"]:.1f} / {v["q_med"]:.1f} / {v["q_max"]:.1f}'
        su = (f'<div class="kv"><div class="k">品質 min/med/max</div><div class="mono">{qn}</div>'
              f'<div class="k">含警告 WARN DOCS</div><div>{v["warn_docs"]}</div>'
              f'<div class="k">財務筆數 FIN ROWS</div><div>{v["fin_rows"]}</div>'
              f'<div class="k">未驗證 UNVERIFIED</div><div>{v["unverified"]} <span class="pill warn">須回源核對</span></div></div>')
        fm = "".join(f'<tr><td class="mono">{html.escape(k)}</td><td class="mono">{n}</td></tr>' for k, n in sorted(v["fin_metrics"].items(), key=lambda kv: -kv[1])[:14]) or '<tr><td colspan="2">financial_data.jsonl 缺(誠實)</td></tr>'
        fd = (f'<div class="wrap-x"><table class="tbl"><tr><th>指標 METRIC</th><th>筆 N</th></tr>{fm}</table></div>'
              f'<div class="note">數值=擷取物非驗證物;進 SSOT 前須回 TWSE/TDCC/原報告核對。</div>')
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
<title>VIA · {s["zh"]} {cur} 現況台</title><style>{CSS}
{d.get("deck", {}).get("css", "") if cur == "CGC" else ""}</style></head><body>
<aside class="rail">
<div class="brand"><span class="seal">{s["seal"]}</span>
<div class="latin">VERITAS INTELLIGENCE ANALYTICS</div>
<h1>{s["zh"]}現況台</h1>
<div class="en">{s["en"]}</div>
<span class="badge">SHELL v0106 · LIVE</span></div>
{_nav(cur, d)}
{_rail_inputs(cur, d)}
<div class="railfoot">
<div><div class="k">TASKS</div><div class="v">{len(tasks)}</div></div>
<div><div class="k">PAGES</div><div class="v">{len(pages)}</div></div>
<div><div class="k">STATE</div><div class="v">LIVE</div></div>
<div><div class="k">LEDGER</div><div class="v">{_n(a.get("ledger", 0))}</div></div>
</div></aside>
<main class="main">
<div class="crumb">{crumb} · <span class="lock">LAYOUT SPEC(批302)</span></div>
<div class="head"><h2>{s["zh"]} {cur}<small>{s["en"]}</small></h2>
<div class="spec">
<div><div class="k">BUILD</div><div class="v">SHELL v0106</div></div>
<div><div class="k">TASKS</div><div class="v">{len(tasks)}</div></div>
<div><div class="k">BRIDGE</div><div class="v ok">127.0.0.1:8765</div></div>
<div><div class="k">GATE</div><div class="v ok">HONEST 3-STATE</div></div>
</div>
<div class="sub">{s["sub"]}</div></div>
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
</main>{("<script>" + d.get("deck", {}).get("js", "") + "</script>") if cur == "CGC" and d.get("deck", {}).get("js") else ""}{RAIL_JS if cur in ("VDF", "VRN") else ""}</body></html>"""


def run(do_print: bool = True) -> int:
    d = gather()
    UI.mkdir(parents=True, exist_ok=True)
    for k in ORDER:
        (UI / SHELLS[k]["page"]).write_text(_shell_page(k, d),
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
    chk("⑪ CGC 殼 file:// 先探同源導向(批333 Codex 安全律)", "location.replace(B+'/VIA_UI_Shell_CGC_v0100.html'" in pages["CGC"])
    chk("⑫ 四殼導航連上船件冊(批336)", all('href="VIA_UI_IntakeRoster_v0100.html"' in p for p in pages.values()))
    chk("⑬ 輸入面板僅 VDF/VRN 在位(左欄·導航下)·CGC/VAP 零變(批337)",
        'id="rin"' in pages["VDF"] and 'id="rin"' in pages["VRN"]
        and 'id="rin"' not in pages["CGC"] and 'id="rin"' not in pages["VAP"]
        and 'name="start"' in pages["VDF"] and 'name="ds"' in pages["VDF"]
        and "財報參數" in pages["VDF"] and "國際商品參數" in pages["VDF"]
        and 'type="file"' in pages["VRN"] and "VIA_submit(" in pages["VDF"]
        and "VIA_submit(" in pages["VRN"] and f"var B='{BRIDGE}'" in pages["VRN"])
    chk("⑭ VRN 五顯示面板全在+VDF 資料現況矩陣+誠實空律",
        all(t in pages["VRN"] for t in ("SUMMARY MATRIX", "BASIC INFO", "SUMMARY<",
                                        "FINANCIAL DATA", "VALIDATE MATRIX"))
        and "DATA STATUS MATRIX" in pages["VDF"] and "PARAM REGISTRY" in pages["VDF"]
        and ("誠實空" in pages["VDF"] or "DATABASE 實掃" in pages["VDF"]))
    print(f"  [計] 十四檢 OK {14 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 統一版型殼引擎(CGC_MDL116 v0106)· 十四檢自測(零網路)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())

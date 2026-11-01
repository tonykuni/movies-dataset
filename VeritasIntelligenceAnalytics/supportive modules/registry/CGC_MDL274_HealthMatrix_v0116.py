#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL274_HealthMatrix v0116 — 薄尾:VCGC 頁換 VeritasReportNova Workbench 範本的印章頁首 + 字型(模板冊 v0104 assets)· VRN 分頁改指 VeritasReportNova

操作員令(2026-11-01):「VRN-2 完成上述工作後 · 子系統名稱還原為 VeritasReportNova · 成為 VRN 唯一系統 · 完成後開始針對 VDF / VCGC CLOSE OUT ·
  擁有相同的 U/I 模板視覺或動畫視覺鎖定 · 印章 logo 為透明去背無框無特效 · 以紅字大小為依據跟 header 文字做 header 大小 logo 最佳化調節加入」。
冊:registry 的 VIA_UI_Template_SSOT 尾版(v0104 起 = VRN Workbench 範本 · 三系統同一套 tokens / design.css · assets 節 = 共用印章 + 字型 · 雜湊鎖);
  顏色 / 字級 / 分頁 / 卡片 / 表格 / 動畫由 v0115 照冊套(本版不動);本版只做 design.css 規則做不到的三件(冊規則:css 不收 url():
  ① 印章頁首:VCGC 操作台 VCGC_UI_latest.html 與入口頁 VIA_UI_latest.html 的 <header> 換成範本頁首 —— 左印章(assets.seal · data URI · 無框無陰影無濾鏡 · 透明底)·
     大寫等寬小字(systems.VCGC.caps)→ h1 系統名(systems.VCGC.title)→ 標語(原頁首的說明與燈號圖例原樣保留)· 主印框高 = 文字區塊高(瀏覽器實量 · 44 ~ 120px · 小印垂右下);
  ② 字型:assets.fonts(DM Sans · DM Mono · Syne · Noto Sans TC · 零網路)解到頁面所在夾 via_ui_assets/ · 頁上加一條 fonts.css 連結(冪等換新);
  ③ VRN 分頁:VRN 唯一系統 = VeritasReportNova → 操作台的「VRN U/I」分頁與入口頁的 VRN 改指 VIA_Reports/vrn2/VRN2_Workbench_latest.html(VRN 自己產的頁 · 只讀顯示 · 不寫 VRN 的檔);
     入口頁 VRN 的燈讀 VRN 自報的收尾頁收據 vrn2/VRN2_CloseoutUI_latest.json(只讀 · PASS 綠 · REVIEW / BLOCKED 黃 · OPEN 紅 · 沒有 → 灰)。
  資產雜湊對不上 / 冊沒有 assets → 不嵌(照實印黃 · 頁照前版)。其餘(matrix · ui · portal · theme · 展現規則 · 只收 VCGC 呼叫 · 零網路 · 不碰 TA-Lib)照 v0115。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import base64
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

ME = Path(__file__).resolve()
HERE = ME.parent
_STEM = "CGC_MDL274_HealthMatrix"
TAG = "v0116"
SELF_ID = "VCGC"
ASSET_DIR = "via_ui_assets"
MARK = "<!-- CGC_MDL274_HealthMatrix v0116 workbench header -->"
VRN_WB = "vrn2/VRN2_Workbench_latest.html"
STATE_LAMP_V0116 = {"PASS": "GREEN", "DATA_GAP": "GRAY", "REVIEW": "YELLOW", "BLOCKED": "YELLOW", "OPEN": "RED"}


def _vnum_v0116(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0116(p) < _vnum_v0116(ME)), key=_vnum_v0116)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0116", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
TK_ROOT = PRIOR.TK_ROOT


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def assets_load(root=None) -> dict:
    """冊尾版 assets 節 → {ok, seal_uri, main_frac, fonts_zip, caps, title, why};檔案雜湊對不上 → ok False(不嵌 · 照實)。"""
    root = Path(root or PRIOR._paths()["root"])
    name, d, err = PRIOR._read_book_v0115(root)
    out = {"ok": False, "book": name, "seal_uri": "", "main_frac": 1.0, "fonts_zip": None, "caps": "", "title": "", "why": err}
    if d is None:
        return out
    a = d.get("assets") or {}
    sysd = (d.get("systems") or {}).get(SELF_ID) or {}
    out.update({"caps": str(sysd.get("caps") or ""), "title": str(sysd.get("title") or "")})
    why = []
    seal = a.get("seal") or {}
    sp = root / str(seal.get("file") or "-")
    if seal and sp.is_file() and _sha(sp.read_bytes()) == seal.get("sha256"):
        out["seal_uri"] = "data:image/png;base64," + base64.b64encode(sp.read_bytes()).decode("ascii")
        out["main_frac"] = float(seal.get("main_frac") or 1.0)
    else:
        why.append("印章 %s" % ("冊沒有 assets.seal" if not seal else ("檔不在" if not sp.is_file() else "雜湊對不上")))
    fonts = a.get("fonts") or {}
    fp = root / str(fonts.get("file") or "-")
    if fonts and fp.is_file() and _sha(fp.read_bytes()) == fonts.get("sha256"):
        out["fonts_zip"] = fp
    else:
        why.append("字型 %s" % ("冊沒有 assets.fonts" if not fonts else ("檔不在" if not fp.is_file() else "雜湊對不上")))
    out["ok"] = bool(out["seal_uri"]) and out["fonts_zip"] is not None
    out["why"] = ";".join(why) or None
    return out


def fonts_place(out_dir: Path, fonts_zip) -> bool:
    """字型包解到 <頁面夾>/via_ui_assets/(雜湊記號相同就不重解 · 冪等)。"""
    if not fonts_zip:
        return False
    target = Path(out_dir) / ASSET_DIR
    stamp = target / ".sha256"
    want = _sha(Path(fonts_zip).read_bytes())
    if stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == want and (target / "fonts.css").is_file():
        return True
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(fonts_zip) as z:
        for n in z.namelist():
            if n.endswith("/") or ".." in n or n.startswith("/"):
                continue
            dest = target / n
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(n))
    stamp.write_text(want + "\n", encoding="utf-8")
    return (target / "fonts.css").is_file()


CSS_V0116 = """header.via-wb{display:flex;align-items:center;gap:14px;padding:10px 20px;min-height:var(--hd,100px);flex-wrap:wrap}
header.via-wb .via-seal{height:var(--seal-main,56px);flex:none;display:block;overflow:visible;background:none;border:none;box-shadow:none;padding:0}
header.via-wb .via-seal img{height:var(--seal-full,62px);width:auto;display:block;border:none;box-shadow:none;filter:none;background:transparent}
header.via-wb .via-hdtxt{min-width:0;flex:1}
header.via-wb .via-tag{font-size:12px;color:var(--dim);overflow-wrap:anywhere}
"""
JS_V0116 = """<script id="via-seal-fit-v0116">(function(){var F=%s,MIN=44,MAX=120;function fit(){var h=document.querySelector('header.via-wb'),t=h&&h.querySelector('.via-hdtxt');if(!t)return;
var m=Math.max(MIN,Math.min(MAX,Math.round(t.getBoundingClientRect().height)));h.style.setProperty('--seal-main',m+'px');h.style.setProperty('--seal-full',Math.round(m/F)+'px');}
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit);window.addEventListener('load',fit);var tm;window.addEventListener('resize',function(){clearTimeout(tm);tm=setTimeout(fit,80)});fit();})();</script>"""


def _clean(page: str) -> str:
    """拿掉本版上次加的(冪等換新)。"""
    page = re.sub(r'<link rel="stylesheet" id="via-fonts-v0116"[^>]*>', "", page)
    page = re.sub(r'<style id="via-wb-v0116">.*?</style>', "", page, flags=re.S)
    page = re.sub(r'<script id="via-seal-fit-v0116">.*?</script>', "", page, flags=re.S)
    return page


def header_html(a: dict, tag_html: str, title: str) -> str:
    seal = '<div class="via-seal"><img alt="seal" src="%s"></div>' % a["seal_uri"] if a.get("seal_uri") else ""
    return '%s<header class="via-wb">%s<div class="via-hdtxt"><small>%s</small><h1>%s</h1><div class="via-tag">%s</div></div></header>' % (
        MARK, seal, html.escape(a.get("caps") or "VERITAS INTELLIGENCE ANALYTICS · VERITAS CENTRAL GOVERNANCE · VCGC"), html.escape(title), tag_html)


_RX_UI_HDR = re.compile(r"(?:%s)?<header(?: class=\"via-wb\")?>(?:<h1>VCGC · 母系統</h1><small>(?P<small>.*?)</small>|.*?<div class=\"via-tag\">(?P<tag>.*?)</div></div>)</header>" % re.escape(MARK), re.S)
_RX_PORTAL_HDR = re.compile(r"(?:%s)?<header(?: class=\"via-wb\")?>(?:<h1>VIA</h1>(?P<rest>.*?)|.*?<div class=\"via-tag\">(?P<tag>.*?)</div></div>)</header>" % re.escape(MARK), re.S)


def upgrade_ui(page: str, out_dir: Path, a: dict) -> tuple:
    """VCGC 操作台:印章頁首 + 字型 + VRN 分頁改指 VeritasReportNova。回 (新頁, 動了哪些)。"""
    did = []
    page = _clean(page)
    m = _RX_UI_HDR.search(page)
    if m:
        tag = m.group("small") if m.group("small") is not None else m.group("tag")
        page = page[:m.start()] + header_html(a, tag, a.get("title") or "Veritas Central Governance Console") + page[m.end():]
        did.append("頁首")
    if '<button class="on" onclick="tab(' in page or '<button onclick="tab(' in page:     # 分頁按鈕用範本標題字(Syne)· 字級套件的字體吸附對 .via-serif 放行
        page = page.replace('<button class="on" onclick="tab(', '<button class="on via-serif" onclick="tab(').replace('<button onclick="tab(', '<button class="via-serif" onclick="tab(')
        did.append("分頁字")
    if '>VRN U/I</button>' in page:
        page = page.replace('>VRN U/I</button>', '>VRN · VeritasReportNova</button>', 1)
        did.append("VRN 分頁名")
    if '<iframe src="../../vrn/VRN_UI_latest.html"></iframe>' in page:
        page = page.replace('<iframe src="../../vrn/VRN_UI_latest.html"></iframe>', '<iframe src="../../%s"></iframe>' % VRN_WB, 1)
        did.append("VRN 分頁 → Workbench")
    return _finish(page, out_dir, a, did)


def _vrn_state(reports: Path) -> tuple:
    c = {}
    try:
        c = json.loads((Path(reports) / "vrn2" / "VRN2_CloseoutUI_latest.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        c = {}
    st = str(c.get("state") or "")
    return STATE_LAMP_V0116.get(st, "GRAY"), st or "沒有收尾頁收據"


def upgrade_portal(page: str, out_dir: Path, a: dict) -> tuple:
    """入口頁:印章頁首 + 字型 + VRN = VeritasReportNova Workbench(燈讀 VRN 自報 · 只讀)。"""
    did = []
    page = _clean(page)
    m = _RX_PORTAL_HDR.search(page)
    if m:
        tag = m.group("rest") if m.group("rest") is not None else m.group("tag")
        page = page[:m.start()] + header_html(dict(a, caps="VERITAS INTELLIGENCE ANALYTICS · VIA · VRN · VDF · VCGC"), tag, "Veritas Intelligence Analytics") + page[m.end():]
        did.append("頁首")
    wb = Path(out_dir) / VRN_WB
    pages = list(re.finditer(r"<div class='page( on)?'>(.*?)</div>(?=<div class='page|\s*</div>)", page, re.S))
    btns = list(re.finditer(r"<button class='sysbtn( on)?' onclick=\"pick\((\d+),this\)\"><i class='lp (\w+)' style='background:[^']*'></i><b>(VRN)</b><small>(.*?)</small></button>", page, re.S))
    if wb.is_file() and len(pages) >= 3:
        p3 = pages[2]
        page = page[:p3.start(2)] + "<iframe src='%s'></iframe>" % VRN_WB + page[p3.end(2):]
        did.append("VRN → Workbench")
        btns = list(re.finditer(r"<button class='sysbtn( on)?' onclick=\"pick\((\d+),this\)\"><i class='lp (\w+)' style='background:[^']*'></i><b>(VRN)</b><small>(.*?)</small></button>", page, re.S))
        if btns:
            b = btns[0]
            lamp, st = _vrn_state(out_dir)
            new = "<button class='sysbtn%s' onclick=\"pick(%s,this)\"><i class='lp %s' style='background:%s'></i><b>VRN</b><small>VeritasReportNova · 收尾 %s · 自報(只讀)</small></button>" % (
                b.group(1) or "", b.group(2), lamp, PRIOR.LAMP.get(lamp, PRIOR.LAMP["GRAY"]), html.escape(st))
            page = page[:b.start()] + new + page[b.end():]
            did.append("VRN 燈 %s" % lamp)
    return _finish(page, out_dir, a, did)


def _finish(page: str, out_dir: Path, a: dict, did: list) -> tuple:
    if fonts_place(out_dir, a.get("fonts_zip")):
        did.append("字型")
        link = '<link rel="stylesheet" id="via-fonts-v0116" href="%s/fonts.css">' % ASSET_DIR
    else:
        link = ""
    block = link + '<style id="via-wb-v0116">%s</style>' % CSS_V0116
    i = page.lower().rfind("</head>")
    page = (page[:i] + block + page[i:]) if i >= 0 else (block + page)
    j = page.lower().rfind("</body>")
    js = JS_V0116 % a.get("main_frac", 1.0)
    page = (page[:j] + js + page[j:]) if j >= 0 else (page + js)
    return page, did


def fonts_only(page: str, out_dir: Path, a: dict) -> tuple:
    """同夾的內嵌頁(健康矩陣頁 · iframe 裡):只連字型(iframe 看不到外層載入的字型)· 頁首不動 · 冪等。"""
    page = re.sub(r'<link rel="stylesheet" id="via-fonts-v0116"[^>]*>', "", page)
    if not fonts_place(out_dir, a.get("fonts_zip")):
        return page, []
    link = '<link rel="stylesheet" id="via-fonts-v0116" href="%s/fonts.css">' % ASSET_DIR
    i = page.lower().rfind("</head>")
    return ((page[:i] + link + page[i:]) if i >= 0 else (link + page)), ["字型"]


def _apply_file(fp: Path, kind: str, a: dict) -> str:
    if not fp.is_file():
        return "沒有 %s" % fp.name
    old = fp.read_text(encoding="utf-8")
    new, did = {"ui": upgrade_ui, "portal": upgrade_portal, "fonts": fonts_only}[kind](old, fp.parent, a)
    if new != old:
        fp.write_text(new, encoding="utf-8")
    return "%s · %s" % (fp.name, " · ".join(did) or "沒變")


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    rc = PRIOR.main(a)
    if a[:1] in (["ui"], ["portal"]):
        P = PRIOR._paths()
        ast_ = assets_load(P["root"])
        if a[:1] == ["ui"]:
            r = _apply_file(Path(P["out"]) / "VCGC_UI_latest.html", "ui", ast_) + " ‖ " + _apply_file(Path(P["out"]) / "HEALTH_MATRIX_latest.html", "fonts", ast_)
        else:
            r = _apply_file(Path(P["root"]) / "VIA_Reports" / "VIA_UI_latest.html", "portal", ast_)
        print("  [範本] %s %s · 冊 %s · %s%s" % (_STEM, TAG, ast_.get("book") or "—", r, (" · [YELLOW] " + ast_["why"]) if ast_.get("why") else ""))
    return rc


def _fixture_ui() -> str:
    return ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VCGC U/I</title><style>body{margin:0}</style></head><body>'
            '<header><h1>VCGC · 母系統</h1><small>2026-11-01T00:00 · 左:只有兩組設定(程式檔案夾 · 資料庫)· 右:多頁展示 · <span style="color:#16a34a">●</span>綠</small></header>'
            '<aside><div class="card"><b>程式檔案夾</b></div></aside><main><div class="tabs"><button class="on" onclick="tab(0,this)">健康矩陣</button><button onclick="tab(4,this)">VDF U/I</button>'
            '<button onclick="tab(5,this)">VRN U/I</button></div><div class="pages"><div class="page on"><iframe src="HEALTH_MATRIX_latest.html"></iframe></div>'
            '<div class="page"><iframe src="../../vdf/VDF_UI_latest.html"></iframe></div><div class="page"><iframe src="../../vrn/VRN_UI_latest.html"></iframe></div></div></main></body></html>')


def _fixture_portal() -> str:
    return ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA U/I</title></head><body>'
            '<header><h1>VIA</h1><span style="align-self:center;color:var(--dim);margin-left:auto">2026-11-01 · 入口只讀各系統自報清單</span></header><aside>'
            "<button class='sysbtn on' onclick=\"pick(0,this)\"><i class='lp GREEN' style='background:#16a34a'></i><b>VCGC</b><small>x</small></button>"
            "<button class='sysbtn' onclick=\"pick(1,this)\"><i class='lp GRAY' style='background:#9ca3af'></i><b>VDF</b><small>x</small></button>"
            "<button class='sysbtn' onclick=\"pick(2,this)\"><i class='lp GRAY' style='background:#9ca3af'></i><b>VRN</b><small>未跑 ui · 頁籤 0 · —</small></button></aside>"
            "<main><div class='pages'><div class='page on'><iframe src='review/vcgc_health/VCGC_UI_latest.html'></iframe></div><div class='page'><iframe src='vdf/VDF_UI_latest.html'></iframe></div>"
            "<div class='page'><div class='empty'>VRN 尚未產 U/I:在啟動器跑 -Sub VRN -Verb ui</div></div></div></main></body></html>")


ERA_MAX_V0116 = 103          # 前版鏈(v0113 ~ v0115)自測寫死的是 v0103 的冊值


def _prior_selftest_era() -> int:
    """前版鏈自測:鏈上每支的 TK_ROOT 暫時指到只放 v0100 ~ v0103 冊副本的暫存根 → 前版邏輯照它那個年代的冊驗;跑完還原(不寫 registry)。"""
    import shutil
    import tempfile
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = getattr(m, "PRIOR", None)
    real = Path(TK_ROOT) / "supportive modules" / "registry"
    with tempfile.TemporaryDirectory() as era:
        reg = Path(era) / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        for bk in real.glob("VIA_UI_Template_SSOT_v*.json"):
            if 0 <= _vnum_v0116(bk) <= ERA_MAX_V0116:
                shutil.copy2(str(bk), str(reg / bk.name))
        saved = [(x, x.TK_ROOT) for x in mods if hasattr(x, "TK_ROOT")]
        for x, _ in saved:
            x.TK_ROOT = Path(era)
        try:
            return PRIOR.selftest()
        finally:
            for x, v in saved:
                x.TK_ROOT = v


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 薄尾自測(VeritasReportNova Workbench 範本:印章頁首 · 字型 · VRN 分頁)===" % (_STEM, TAG))
    a = assets_load()
    chk("① 冊尾版 ≥ v0104 有 assets(印章 · 字型 · 雜湊對上)· systems.VCGC caps / title(冊 %s)" % a.get("book"), a["ok"] and a["main_frac"] < 1 and "VCGC" in a["caps"] and a["title"], a.get("why"))
    with tempfile.TemporaryDirectory() as t:
        out = Path(t) / "review" / "vcgc_health"
        out.mkdir(parents=True)
        new, did = upgrade_ui(_fixture_ui(), out, a)
        chk("② 操作台頁首 = 範本頁首(印章 data URI · 大寫小字 · h1 · 原說明與燈號圖例原樣)", '<header class="via-wb"><div class="via-seal"><img alt="seal" src="data:image/png;base64,' in new
            and "<h1>Veritas Central Governance Console</h1>" in new and "左:只有兩組設定" in new and '<span style="color:#16a34a">●</span>綠' in new, did)
        chk("③ VRN 分頁 → VeritasReportNova Workbench(名稱 + iframe)· VDF 分頁不動", '>VRN · VeritasReportNova</button>' in new and '<iframe src="../../vrn2/VRN2_Workbench_latest.html">' in new
            and '<iframe src="../../vdf/VDF_UI_latest.html">' in new)
        chk("④ 字型包解到 via_ui_assets/(fonts.css + woff2)· 頁上一條 fonts.css 連結", (out / ASSET_DIR / "fonts.css").is_file() and len(list((out / ASSET_DIR / "fonts").glob("*.woff2"))) > 100
            and new.count('id="via-fonts-v0116"') == 1)
        again, _ = upgrade_ui(new, out, a)
        chk("⑤ 冪等:再跑一次逐字相同(換新不疊)", again == new and again.count(MARK) == 1 and again.count('<style id="via-wb-v0116">') == 1 and again.count("via-seal-fit-v0116") == 1)
        chk("⑥ 印章無框無陰影無濾鏡 · 主印框高 = 文字區塊高 ÷ 佔比 · 44 ~ 120px", "filter:none" in CSS_V0116 and "box-shadow:none" in CSS_V0116 and "MIN=44,MAX=120" in new and "var F=%s," % a["main_frac"] in new)
        base = re.sub(r"%s<header class=\"via-wb\">.*?</header>" % re.escape(MARK), "", _clean(new), flags=re.S).replace('>VRN · VeritasReportNova</button>', '>VRN U/I</button>').replace("../../vrn2/VRN2_Workbench_latest.html", "../../vrn/VRN_UI_latest.html").replace(' class="on via-serif" onclick="tab(', ' class="on" onclick="tab(').replace(' class="via-serif" onclick="tab(', ' onclick="tab(')
        orig = re.sub(r"<header>.*?</header>", "", _fixture_ui(), flags=re.S)
        chk("⑦ 原有功能不改:拿掉本版加的 = 前版頁(左面板 · 分頁 · 其他 iframe)", base == orig)
        rep = Path(t)
        (rep / "vrn2").mkdir()
        (rep / "vrn2" / "VRN2_Workbench_latest.html").write_text("<html></html>", encoding="utf-8")
        (rep / "vrn2" / "VRN2_CloseoutUI_latest.json").write_text(json.dumps({"state": "REVIEW"}), encoding="utf-8")
        np_, did2 = upgrade_portal(_fixture_portal(), rep, a)
        chk("⑧ 入口頁:範本頁首 · VRN = VeritasReportNova Workbench · 燈讀 VRN 自報(REVIEW → 黃)", "<h1>Veritas Intelligence Analytics</h1>" in np_ and "<iframe src='vrn2/VRN2_Workbench_latest.html'>" in np_
            and "<i class='lp YELLOW'" in np_ and "VeritasReportNova · 收尾 REVIEW" in np_ and "<iframe src='vdf/VDF_UI_latest.html'>" in np_, did2)
        hm, d3 = fonts_only("<html><head><title>x</title></head><body><table></table></body></html>", out, a)
        hm2, _ = fonts_only(hm, out, a)
        chk("⑧b 同夾健康矩陣頁(iframe)只連字型 · 冪等 · 頁首不動", hm.count('id="via-fonts-v0116"') == 1 and hm2 == hm and "<header" not in hm, d3)
        bad = dict(a, seal_uri="", fonts_zip=None)
        nb, _ = upgrade_ui(_fixture_ui(), out, bad)
        chk("⑨ 資產對不上 → 不嵌印章 / 字型(頁首照範本字 · 不當掉)", "via-seal" not in nb.split("<style")[0] and 'id="via-fonts-v0116"' not in nb and "<h1>" in nb)
    body = ME.read_text(encoding="utf-8")
    chk("⑩ 只讀他系統:不寫 VRN / VDF 的檔 · 零網路 · 不碰 TA-Lib", "import " + "talib" not in body and "https:" + "//" not in body and ".write_text" not in body.split("def _vrn_state")[1].split("def upgrade_portal")[0])
    print("  ── 前版鏈自測(VIA_SKIP_PRIOR_SELFTEST=1 略過 · 前版用它那個年代的冊 v0103 以前:它們的自測寫死 v0103 的色值)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else _prior_selftest_era()
    chk("⑪ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s %s 本版 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

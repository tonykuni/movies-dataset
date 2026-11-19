#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0108 — 薄尾(v0107 … v0100 一字不動):項目冊可以要 Dashboard 版面(貼近兩邊 · 系統訊號 · 功能分欄)。
為什麼:操作員 2026-11-19:「U/I 可以接近兩邊邊界近一點,當 DASHBOARD,一頁可彈性地放入不同類型資料型式」
「VCGC 有中央監管功能 / 節省 TOKEN 及支援功能 / 具對話顯示功能,最佳化視覺展現」。
本版只加一件;項目冊沒帶這個鍵時,行為與 v0107 完全相同:
  項目冊 {"layout": {"mode": "dashboard", "pillars": [{"name": "…", "note": "…", "sections": ["區塊名", …], "feedback": false}, …]}}
    · 頁面貼近兩邊(.wrap 加 .dash);最上面一排「系統訊號」(原本 ② 的系統卡片);
    · 接著「功能分欄」:③ 的群組卡片照 pillars 分進各欄,每欄一盞燈(欄內最差)與列數,每張卡多一條紅黃綠灰比例條;
      標了 feedback 的那一欄把 ④ 更新回饋的文字收進來;沒列到的群組歸「其他」一欄;
    · ① 依類別的卡片、⑤ 回饋包、⑥ 矩陣、⑦ 對帳照舊在下面;卡片仍然可以點(矩陣跟著篩)。
  版面規則全部在另一本冊 VIA_UI_WorkPlatform_DashboardLayout(尾版)的 css 裡,本檔沒有任何顏色與尺寸;模板鎖冊一字不動。
  那本冊不在、雜湊不符、或 css 裡出現顏色時不套 Dashboard(照舊版面),並在頁首說明列照實寫。
  頁面結構和預期不一樣(找不到那幾個區塊)時原樣輸出,不硬改。
唯讀倉;不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。動詞與旗標同 v0107。
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
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0108"
VERSION = "v0108"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0107.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0107", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0107"] = PRIOR
_spec.loader.exec_module(PRIOR)
V6 = PRIOR.PRIOR            # v0106:展開區
V5 = PRIOR.V5               # v0105:收據的 version 由它的 write_out 寫
V3 = PRIOR.V3
P0 = PRIOR.P0               # v0100 本體(run 用它的全域名呼叫 render)
PRIOR.ENGINE = V6.ENGINE = V5.ENGINE = V5.PRIOR.ENGINE = V3.ENGINE = V3.PRIOR.ENGINE = V3.P1.ENGINE = P0.ENGINE = ENGINE
PRIOR.VERSION = V6.VERSION = V5.VERSION = VERSION
V3.MANIFEST["engine"] = ENGINE
_O = {"render": P0.render}  # 此刻指到 v0106 的包裝
CTX = {"layout": None, "css": "", "note": ""}
LAYOUT_BOOK = "VIA_UI_WorkPlatform_DashboardLayout"
COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(")
REST = "其他"
ZH = {"r": "紅", "y": "黃", "g": "綠", "x": "灰"}
DASH_RULE = ".wrap.dash{"                             # 版面冊有這條規則才套 Dashboard
BTN = re.compile(r'<button type="button" class="kc"[^>]*data-kind="grp"[^>]*data-key="([^"]*)"[^>]*>.*?</button>', re.S)
H_CLS, H_SYS = '<h2>① 要處理的:依類別</h2><div class="cards">', '<h2>② 要處理的:依系統</h2><div class="cards">'
H_GRP_PLAIN = '<h2>③ 全部列:依群組</h2><div class="cards">'
H_NOTE = '<div class="note">還沒管到的面向:'
FB_OPEN = '<section class="card"><h2>④ '


def doc_layout(src: str):
    """讀項目冊自帶的 layout。格式不對就當沒帶(回 None),不猜。"""
    try:
        doc = json.loads(Path(src).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    lay = doc.get("layout") if isinstance(doc, dict) else None
    if not (isinstance(lay, dict) and lay.get("mode") == "dashboard" and isinstance(lay.get("pillars"), list) and 0 < len(lay["pillars"]) <= 6):
        return None
    out = []
    for p in lay["pillars"]:
        if not (isinstance(p, dict) and isinstance(p.get("name"), str) and p["name"].strip() and isinstance(p.get("sections"), list) and all(isinstance(s, str) for s in p["sections"])):
            return None
        out.append({"name": p["name"].strip()[:24], "note": str(p.get("note") or "").strip()[:60], "sections": list(p["sections"]), "feedback": p.get("feedback") is True})
    return {"mode": "dashboard", "pillars": out}


def layout_css(via) -> tuple:
    """回 (css, 說明)。版面冊尾版在、雜湊相符、沒有顏色、有 Dashboard 規則才回 css;否則回空字串與原因。"""
    if via is None:
        return "", "找不到 VIA 夾(版面冊沒讀)"
    reg = Path(via) / "supportive modules" / "registry"
    hits = [p for p in reg.glob(LAYOUT_BOOK + "_v[0-9][0-9][0-9][0-9].json")]
    if not hits:
        return "", "版面冊 %s 不在(照舊版面)" % LAYOUT_BOOK
    book = max(hits, key=lambda p: p.stem[-4:])
    try:
        b = json.loads(book.read_text(encoding="utf-8"))
        css = b["css"]
    except (OSError, ValueError, KeyError, TypeError):
        return "", "%s 讀不懂(照舊版面)" % book.name
    if not isinstance(css, str) or hashlib.sha256(css.encode("utf-8")).hexdigest() != b.get("css_sha256"):
        return "", "%s 的 css 與鎖的雜湊不符(照舊版面)" % book.name
    if COLOR.search(css):
        return "", "%s 的 css 出現顏色(版面冊不准帶顏色;照舊版面)" % book.name
    if DASH_RULE not in css:
        return "", "%s 沒有 Dashboard 規則(照舊版面)" % book.name
    return css, book.stem


def apply_layout(layout, css="", note=""):
    CTX.update(layout=layout, css=css if layout else "", note=note if layout else "")


def restore():
    CTX.update(layout=None, css="", note="")


def _cut(html, start, end):
    """回 (前段, 中段, 後段);找不到回 None。中段不含 start 與 end。"""
    i = html.find(start)
    if i < 0:
        return None
    j = html.find(end, i + len(start))
    if j < 0:
        return None
    return html[:i], html[i + len(start):j], html[j + len(end):]


def _with_bar(btn: str) -> str:
    m = re.search(r'<span class="kr">紅 (\d+) · 黃 (\d+) · 綠 (\d+) · 灰 (\d+)</span>', btn)
    if not m:
        return btn
    n = [int(x) for x in m.groups()]
    tot = sum(n) or 1
    bar = '<span class="mb">' + "".join('<i class="lamp %s" style="width:%.1f%%"></i>' % (k, 100.0 * v / tot) for k, v in zip("rygx", n) if v) + "</span>"
    return btn.replace("</button>", bar + "</button>", 1) if btn.endswith("</button>") else btn


def dashboard(html: str, layout: dict) -> str:
    """把 v0107 出的頁重排成 Dashboard;任何一塊找不到就原樣回。"""
    if DASH_RULE not in html or '<div class="wrap">' not in html:
        return html
    c_cls = _cut(html, H_CLS, "</div>")
    if c_cls is None:
        return html
    head, cls_btns, rest = c_cls
    c_sys = _cut(rest, H_SYS, "</div>")
    if c_sys is None or c_sys[0].strip():
        return html
    sys_btns, rest = c_sys[1], c_sys[2]
    if rest.startswith('<details class="card" id="xp"'):
        k = rest.find('<div class="cards">')
        c_grp = _cut(rest, rest[:k + len('<div class="cards">')], "</div></details>") if k > 0 else None
    else:
        c_grp = _cut(rest, H_GRP_PLAIN, "</div>") if rest.startswith(H_GRP_PLAIN) else None
    if c_grp is None or c_grp[0]:
        return html
    grp_btns, rest = c_grp[1], c_grp[2]
    if not rest.startswith(H_NOTE):
        return html
    cards = {m.group(1): m.group(0) for m in BTN.finditer(grp_btns)}
    if not cards or "".join(cards.values()) != grp_btns:
        return html
    fb_html = ""
    c_fb = _cut(rest, FB_OPEN, "</section>")
    if c_fb is not None and any(p["feedback"] for p in layout["pillars"]):
        m = re.search(r"<pre[^>]*>.*?</pre>", c_fb[1], re.S)
        if m:
            fb_html = '<div class="note">文字型 · 更新回饋(這一輪跟上一輪比)</div>' + m.group(0)
            rest = c_fb[0] + c_fb[2]
    used, cols = set(), []
    pillars = list(layout["pillars"])
    left = [k for k in cards if not any(P0.E(s) == k or s == k for p in pillars for s in p["sections"])]
    if left:
        pillars.append({"name": REST, "note": "", "sections": left, "feedback": False})
    for p in pillars:
        keys = [k for k in cards if (k in [P0.E(s) for s in p["sections"]] or k in p["sections"]) and k not in used]
        used.update(keys)
        lamps = [re.search(r'<span class="lamp (\w)">', cards[k]).group(1) for k in keys if re.search(r'<span class="lamp (\w)">', cards[k])]
        n = sum(int(re.search(r'<span class="kn">(\d+)</span>', cards[k]).group(1)) for k in keys if re.search(r'<span class="kn">(\d+)</span>', cards[k]))
        lamp = "r" if "r" in lamps else "y" if "y" in lamps else "g" if "g" in lamps else "x"
        cols.append('<section class="card"><h2><span class="lamp %s">%s</span> %s<span class="note"> · %d 列%s</span></h2><div class="cards">%s</div>%s</section>'
                    % (lamp, ZH[lamp], P0.E(p["name"]), n, (" · " + P0.E(p["note"])) if p["note"] else "", "".join(_with_bar(cards[k]) for k in keys), fb_html if p["feedback"] else ""))
    new = (head.replace('<div class="wrap">', '<div class="wrap dash">', 1)
           + '<h2>系統訊號<span class="chip">卡片型</span><span class="note"> · 每個系統一句話由它自己的管理器彙總;點一張卡,矩陣只看那個系統</span></h2><div class="cards sysrow">' + sys_btns + "</div>"
           + '<h2>功能分欄<span class="chip">卡片型 + 比例條</span><span class="note"> · 點一張卡,矩陣只看那一區</span></h2><div class="grid3">' + "".join(cols) + "</div>"
           + H_CLS + cls_btns + "</div>" + rest)
    return new


def render(res, cards, pack, css, tpl_note, accel) -> str:
    html = _O["render"](res, cards, pack, css, tpl_note, accel)
    lay = CTX["layout"]
    if not lay:
        return html
    if not CTX["css"] or "</style>" not in html:
        return html.replace("</header>", '<div class="note">Dashboard 版面沒有套:%s</div></header>' % P0.E(CTX["note"] or "沒有版面冊"), 1) if CTX["note"] else html
    return dashboard(html.replace("</style>", "\n" + CTX["css"] + "</style>", 1), lay)


P0.render = render


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    chk("v0107(含前版鏈)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf108_st_"))
    try:
        raw = [{"section": "甲區", "system": "VCGC", "lamp": "y", "id": "a", "title": "a", "detail": "待看"},
               {"section": "乙區", "system": "VCGC", "lamp": "g", "id": "b", "title": "b", "detail": "好"},
               {"section": "丙區", "system": "VCGC", "lamp": "r", "id": "c", "title": "c", "detail": "仍紅"},
               {"section": "丁區", "system": "VDF", "lamp": "y", "id": "d", "title": "d", "detail": "自報 YELLOW"}]
        groups = [[s, [s]] for s in ("甲區", "乙區", "丙區", "丁區")]
        lay = {"mode": "dashboard", "pillars": [{"name": "監管", "note": "說明", "sections": ["甲區", "丙區"]}, {"name": "對話", "sections": ["乙區"], "feedback": True}]}
        base = {"source": "自測冊", "title": "自測一覽", "groups": groups, "systems": ["VCGC", "VDF"], "expand": {"system": "VCGC", "label": "展開", "open": False}, "items": raw}
        book = tmp / "book.json"
        book.write_text(json.dumps(dict(base, layout=lay), ensure_ascii=False), encoding="utf-8")
        got = doc_layout(str(book))
        chk("讀得到項目冊自帶的 layout(欄名 · 說明 · 區塊 · 回饋欄)", got == {"mode": "dashboard", "pillars": [{"name": "監管", "note": "說明", "sections": ["甲區", "丙區"], "feedback": False},
                                                                                          {"name": "對話", "note": "", "sections": ["乙區"], "feedback": True}]}, got)
        bad = tmp / "bad.json"
        bad.write_text(json.dumps(dict(base, layout={"mode": "dashboard", "pillars": [{"name": "", "sections": ["甲區"]}]}), ensure_ascii=False), encoding="utf-8")
        bad2 = tmp / "bad2.json"
        bad2.write_text(json.dumps(dict(base, layout={"mode": "wide", "pillars": lay["pillars"]}), ensure_ascii=False), encoding="utf-8")
        chk("layout 格式不對 / 模式不認得 / 不是 JSON:當沒帶", doc_layout(str(bad)) is None and doc_layout(str(bad2)) is None and doc_layout(str(tmp / "nope.json")) is None)
        css_dash = DASH_RULE + "max-width:none}"
        for label, with_expand in (("帶展開區", True), ("不帶展開區", False)):
            V5.apply_extras([(g, tuple(s)) for g, s in groups], "自測一覽")
            V6.apply_extras(["VCGC", "VDF"], base["expand"] if with_expand else None)
            apply_layout(got, css_dash, "自測版面")
            try:
                r = P0.assemble(raw, "自測冊", None)
                page = P0.render(r, P0.cards_of(r), list(r["head"]), ".x{}", "自測", "自測")
                plain = _O["render"](r, P0.cards_of(r), list(r["head"]), ".x{}", "自測", "自測")
            finally:
                restore()
                V6.restore()
                V5.restore()
            i_sys, i_pl, i_cls, i_mx = page.find("系統訊號"), page.find("功能分欄"), page.find("① 要處理的:依類別"), page.find('id="mx"')
            chk("Dashboard(%s):貼近兩邊 · 次序是 系統訊號 → 功能分欄 → 依類別 → 矩陣" % label, '<div class="wrap dash">' in page and 0 < i_sys < i_pl < i_cls < i_mx, (i_sys, i_pl, i_cls, i_mx))
            cols = re.findall(r'<section class="card"><h2><span class="lamp (\w)">.</span> ([^<]+)<span class="note"> · (\d+) 列', page)
            chk("Dashboard(%s):群組卡片照 pillars 分欄;欄燈 = 欄內最差;沒列到的區塊歸「其他」;列數相加 = 全部" % label,
                cols == [("r", "監管", "2"), ("g", "對話", "1"), ("y", "其他", "1")], cols)
            chk("Dashboard(%s):卡片一張不少、仍是可點的按鈕;每張多一條比例條;④ 回饋收進標了 feedback 的那一欄(頁上只剩一份)" % label,
                page.count('data-kind="grp"') == plain.count('data-kind="grp"') == 4 and page.count('class="mb"') == 4 and page.count("文字型 · 更新回饋") == 1
                and page.count("<pre") == plain.count("<pre") and FB_OPEN not in page and page.count('data-kind="sys"') == plain.count('data-kind="sys"')
                and page.count('data-kind="cls"') == plain.count('data-kind="cls"'))
            chk("Dashboard(%s):資料與腳本原封不動(矩陣的資料段、篩選腳本位元組相同)" % label, page[page.find('<section class="card" id="mx">'):] == plain[plain.find('<section class="card" id="mx">'):])
        V5.apply_extras([(g, tuple(s)) for g, s in groups], "自測一覽")
        apply_layout(got, "", "版面冊不在(照舊版面)")
        try:
            r = P0.assemble(raw, "自測冊", None)
            old = P0.render(r, P0.cards_of(r), list(r["head"]), ".x{}", "自測", "自測")
            same = _O["render"](r, P0.cards_of(r), list(r["head"]), ".x{}", "自測", "自測")
        finally:
            restore()
            V5.restore()
        chk("版面冊拿不到:不套 Dashboard,頁首多一行照實說原因,其餘與 v0107 相同", "wrap dash" not in old and "Dashboard 版面沒有套:版面冊不在" in old
            and old.replace('<div class="note">Dashboard 版面沒有套:版面冊不在(照舊版面)</div>', "", 1) == same)
        bk = tmp / "supportive modules" / "registry"
        bk.mkdir(parents=True)
        good = DASH_RULE + "max-width:none}"
        mk = lambda name, css, sha=None: (bk / name).write_text(json.dumps({"css": css, "css_sha256": sha or hashlib.sha256(css.encode("utf-8")).hexdigest()}), encoding="utf-8")
        chk("版面冊:不在 → 空", layout_css(tmp)[0] == "" and "不在" in layout_css(tmp)[1] and layout_css(None)[0] == "")
        mk(LAYOUT_BOOK + "_v0100.json", good)
        chk("版面冊:在、雜湊相符、沒有顏色 → 回 css 與冊名", layout_css(tmp) == (good, LAYOUT_BOOK + "_v0100"), layout_css(tmp))
        mk(LAYOUT_BOOK + "_v0101.json", good, "0" * 64)
        r1 = layout_css(tmp)
        mk(LAYOUT_BOOK + "_v0102.json", good + ".a{color:#fff}")
        r2 = layout_css(tmp)
        mk(LAYOUT_BOOK + "_v0103.json", ".a{margin:0}")
        r3 = layout_css(tmp)
        chk("版面冊負控(看尾版):雜湊不符 → 不套;css 帶顏色 → 不套;沒有 Dashboard 規則 → 不套;各寫原因", r1[0] == "" and "雜湊不符" in r1[1] and r2[0] == "" and "顏色" in r2[1] and r3[0] == "" and "沒有 Dashboard 規則" in r3[1], (r1, r2, r3))
        chk("頁面結構不如預期(找不到區塊):原樣回,不硬改", dashboard("<html>" + DASH_RULE + '<div class="wrap">x</div></html>', got) == "<html>" + DASH_RULE + '<div class="wrap">x</div></html>')
        r0 = P0.assemble(raw, "自測冊", None)
        p0 = P0.render(r0, P0.cards_of(r0), list(r0["head"]), ".x{}", "自測", "自測")
        chk("跑完還原;沒帶 layout:頁面照舊、不載版面冊", CTX == {"layout": None, "css": "", "note": ""} and "wrap dash" not in p0 and "功能分欄" not in p0 and "Dashboard 版面" not in p0)
        out = tmp / "out"
        rc = main(["run", "--in", str(book), "--out", str(out), "--no-open", "--no-clip"])
        html = (out / "WORKPLATFORM_latest.html").read_text(encoding="utf-8") if (out / "WORKPLATFORM_latest.html").exists() else ""
        real_css, real_note = layout_css(P0.find_via())
        chk("走 main 的 run --in:頁面寫出;真樹的版面冊拿得到就套 Dashboard、拿不到就照舊並說原因(現在:%s);rc 照內容(有紅 = 1)" % real_note,
            rc == 1 and "<h1>自測一覽:" in html and (("wrap dash" in html and "功能分欄" in html and DASH_RULE in html) if real_css else ("wrap dash" not in html and "Dashboard 版面沒有套" in html)), rc)
        chk("main 跑完也還原", CTX["layout"] is None and CTX["css"] == "" and PRIOR.CTX["sys_info"] is None and V3.SYS_ORDER is V6._BUILTIN["SYS_ORDER"])
        rec = json.loads((out / "STATUS_latest.json").read_text(encoding="utf-8")) if (out / "STATUS_latest.json").exists() else {}
        chk("收據的 version 與 engine 都是本版", rec.get("version") == VERSION and rec.get("engine") == ENGINE, (rec.get("version"), rec.get("engine")))
        src = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]
        chk("本檔沒有色碼、沒有尺寸規則(版面只在版面冊)· 沒留下暫存檔", not re.search(r"#[0-9a-fA-F]{6}\b", src) and "max-width" not in src and "px;" not in src and not list(out.glob("*.tmp")))
    finally:
        restore()
        shutil.rmtree(str(tmp), ignore_errors=True)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if not fails else "RED", len(fails), ENGINE), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    verb = args[0] if args and not args[0].startswith("-") else ("selftest" if "--selftest" in args else "run")
    if verb == "selftest":
        return selftest()
    if verb == "version":
        print("%s · %s(薄尾,前版 %s)" % (Path(__file__).name, ENGINE, PRIOR_NAME))
        return 0
    src = args[args.index("--in") + 1] if "--in" in args and args.index("--in") + 1 < len(args) else ""
    if verb == "run" and src:
        lay = doc_layout(src)
        if lay:
            root = args[args.index("--root") + 1] if "--root" in args and args.index("--root") + 1 < len(args) else None
            apply_layout(lay, *layout_css(Path(root) if root else P0.find_via()))
    try:
        return PRIOR.main(args)
    finally:
        restore()


if __name__ == "__main__":
    sys.exit(main())

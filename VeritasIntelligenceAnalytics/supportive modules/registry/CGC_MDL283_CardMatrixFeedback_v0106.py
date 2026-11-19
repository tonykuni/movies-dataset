#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0106 — 薄尾(v0105 … v0100 一字不動):外來的項目冊可以自帶「系統卡片的順序」與「展開區」。
為什麼:操作員 2026-11-19:「展現的方式可分卡片,VCGC 自己可以展開卡片;VDF VRN VQG VAP VDB(資料庫)」「各自有各自的 system manager 做總控,
包含顯示,互不干擾,互相觀察更新狀態」。②「依系統」的卡片是寫死的六張(沒有 VDB,落進「其他」);③ 的群組卡片永遠攤開,看不出它是哪個系統自己的。
本版只加兩件;項目冊沒帶這兩個鍵時,行為與 v0105 完全相同:
  ① 項目冊 {"systems": ["VCGC", "VDF", …]}:這一輪 ② 的系統卡片照這個順序出(沒列到的系統仍歸「其他」);跑完還原成內建六張。
  ② 項目冊 {"expand": {"system": "VCGC", "label": "…", "open": false}}:③ 的群組卡片收進一個可展開的區塊,標題用 label;
     點 ② 裡那個系統的卡片會順手把它展開。其餘版面、樣式、篩選、對帳都不動。
別的系統的列只是攤開它自己報的燈(由送項目冊的一方負責只讀);本引擎不讀、不執行任何系統。
唯讀倉;不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。動詞與旗標同 v0105。
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
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0106"
VERSION = "v0106"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0105.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0105", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0105"] = PRIOR
_spec.loader.exec_module(PRIOR)
V3 = PRIOR.V3               # v0103:系統卡順序 SYS_ORDER 在它的全域
P0 = PRIOR.P0               # v0100 本體(run 用它的全域名呼叫 render)
PRIOR.ENGINE = PRIOR.PRIOR.ENGINE = V3.ENGINE = V3.PRIOR.ENGINE = V3.P1.ENGINE = P0.ENGINE = ENGINE
PRIOR.VERSION = VERSION     # 收據 STATUS_latest.json 的 version 由 v0105 的 write_out 寫,讓它寫本版
V3.MANIFEST["engine"] = ENGINE
_O = {"render": P0.render}  # 此刻指到 v0105 為止的包裝
_BUILTIN = {"SYS_ORDER": V3.SYS_ORDER}
CTX = {"expand": None}
REST = "其他"
GRP_OPEN = '<h2>③ 全部列:依群組</h2><div class="cards">'
GRP_CLOSE = '</div><div class="note">還沒管到的面向:'
EXPAND_JS = ("<script>(function(){var d=document.getElementById('xp');if(!d)return;[].forEach.call(document.querySelectorAll('.kc[data-kind=\"sys\"]'),function(k){"
             "if(k.dataset.key===d.dataset.sys){k.addEventListener('click',function(){d.open=true})}})})();</script>")


def doc_extras(src: str):
    """讀項目冊自帶的 (systems, expand)。格式不對的一律當沒帶(回 None),不猜。"""
    try:
        doc = json.loads(Path(src).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None
    if not isinstance(doc, dict):
        return None, None
    systems = doc.get("systems")
    if not (isinstance(systems, list) and 0 < len(systems) <= 12 and all(isinstance(s, str) and s.strip() and len(s) <= 16 for s in systems)
            and len({s.strip() for s in systems}) == len(systems)):
        systems = None
    else:
        systems = [s.strip() for s in systems if s.strip() != REST]
    ex = doc.get("expand")
    if isinstance(ex, dict) and isinstance(ex.get("system"), str) and ex["system"].strip() and isinstance(ex.get("label"), str) and ex["label"].strip():
        ex = {"system": ex["system"].strip()[:16], "label": ex["label"].strip()[:80], "open": ex.get("open") is True}
    else:
        ex = None
    return systems, ex


def apply_extras(systems, expand):
    if systems:
        V3.SYS_ORDER = list(systems) + [REST]
    CTX["expand"] = expand


def restore():
    V3.SYS_ORDER = _BUILTIN["SYS_ORDER"]
    CTX["expand"] = None


def render(res, cards, pack, css, tpl_note, accel) -> str:
    html = _O["render"](res, cards, pack, css, tpl_note, accel)
    ex = CTX["expand"]
    if ex and html.count(GRP_OPEN) == 1 and GRP_CLOSE in html.split(GRP_OPEN, 1)[1]:
        a, rest = html.split(GRP_OPEN, 1)
        mid, b = rest.split(GRP_CLOSE, 1)
        html = (a + '<details class="card" id="xp" data-sys="%s"%s><summary><b>③ %s</b></summary><div class="cards">' % (P0.E(ex["system"]), " open" if ex["open"] else "", P0.E(ex["label"]))
                + mid + "</div></details>" + GRP_CLOSE[len("</div>"):] + b)
        html = html.replace("</body>", EXPAND_JS + "</body>", 1) if "</body>" in html else html + EXPAND_JS
    return html


P0.render = render


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    chk("v0105(含前版鏈)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf106_st_"))
    try:
        raw = [{"section": "甲區", "system": "VCGC", "lamp": "y", "id": "a", "title": "a", "detail": "待看"},
               {"section": "同儕", "system": "VDB", "lamp": "r", "id": "b", "title": "b", "detail": "自報 RED"},
               {"section": "同儕", "system": "VRN-2", "lamp": "y", "id": "c", "title": "c", "detail": "自報 YELLOW"},
               {"section": "同儕", "system": "XYZ", "lamp": "y", "id": "d", "title": "d", "detail": "沒列到的系統"}]
        base = {"source": "自測冊", "title": "自測一覽", "groups": [["甲", ["甲區"]], ["同儕", ["同儕"]]], "items": raw}
        book = tmp / "book.json"
        book.write_text(json.dumps(dict(base, systems=["VCGC", "VDF", "VRN-2", "VDB"], expand={"system": "VCGC", "label": "VCGC 展開:各區", "open": False}), ensure_ascii=False), encoding="utf-8")
        s, ex = doc_extras(str(book))
        chk("讀得到項目冊自帶的系統順序與展開區", s == ["VCGC", "VDF", "VRN-2", "VDB"] and ex == {"system": "VCGC", "label": "VCGC 展開:各區", "open": False}, (s, ex))
        bad = tmp / "bad.json"
        bad.write_text(json.dumps(dict(base, systems=["A", "A", 3], expand={"system": "", "label": 5}), ensure_ascii=False), encoding="utf-8")
        chk("系統順序重複 / 不是字串、展開區缺欄:當沒帶", doc_extras(str(bad)) == (None, None), doc_extras(str(bad)))
        chk("不是 JSON / 檔不在:當沒帶", doc_extras(str(tmp / "nope.json")) == (None, None))
        apply_extras(s, ex)
        try:
            r = P0.assemble(raw, "自測冊", None)
            sysn = [(c["key"], c["n"]) for c in V3.STATE["sys"]]
            chk("系統卡片照項目冊的順序,沒列到的歸「其他」,合計 = 入選數", [k for k, _ in sysn] == ["VCGC", "VDF", "VRN-2", "VDB", "其他"] and dict(sysn) == {"VCGC": 1, "VDF": 0, "VRN-2": 1, "VDB": 1, "其他": 1}
                and r["checks"].get("系統卡合計 = 入選數") is True, sysn)
            page = P0.render(r, P0.cards_of(r), list(r["head"]), "", "自測", "自測")
            chk("群組卡片收進可展開區(預設收合),標題用項目冊給的;原本的小標不再出現", '<details class="card" id="xp" data-sys="VCGC"><summary><b>③ VCGC 展開:各區</b></summary><div class="cards">' in page
                and GRP_OPEN not in page and page.count("</details>") >= 1 and GRP_CLOSE[len("</div>"):] in page)
            chk("系統卡片寫進頁面(含 VDB);點系統卡展開的腳本只加一段", 'data-kind="sys" data-key="VDB"' in page and page.count("getElementById('xp')") == 1)
        finally:
            restore()
        chk("跑完還原內建六張與展開設定", V3.SYS_ORDER is _BUILTIN["SYS_ORDER"] and CTX["expand"] is None)
        r0 = P0.assemble(raw, "自測冊", None)
        page0 = P0.render(r0, P0.cards_of(r0), list(r0["head"]), "", "自測", "自測")
        chk("沒帶這兩個鍵:系統卡照舊六張、群組卡照舊攤開(與 v0105 相同)", [c["key"] for c in V3.STATE["sys"]] == list(_BUILTIN["SYS_ORDER"]) and GRP_OPEN in page0 and 'id="xp"' not in page0)
        out = tmp / "out"
        book2 = tmp / "book2.json"
        book2.write_text(json.dumps(dict(base, systems=["VCGC", "VDF", "VRN-2", "VDB"], expand={"system": "VCGC", "label": "VCGC 展開:各區", "open": True}), ensure_ascii=False), encoding="utf-8")
        rc = main(["run", "--in", str(book2), "--out", str(out), "--no-open", "--no-clip"])
        html = (out / "WORKPLATFORM_latest.html").read_text(encoding="utf-8") if (out / "WORKPLATFORM_latest.html").exists() else ""
        chk("走 main 的 run --in:頁面寫出,帶標題(v0105)、系統卡 VDB、展開區(open);rc 照內容(有紅 = 1)",
            rc == 1 and "<h1>自測一覽:" in html and 'data-key="VDB"' in html and 'id="xp" data-sys="VCGC" open>' in html, rc)
        chk("main 跑完也還原(含 v0105 的群組與標題)", V3.SYS_ORDER is _BUILTIN["SYS_ORDER"] and CTX["expand"] is None and PRIOR.CTX["title"] == "")
        rec = json.loads((out / "STATUS_latest.json").read_text(encoding="utf-8")) if (out / "STATUS_latest.json").exists() else {}
        chk("收據的 version 與 engine 都是本版", rec.get("version") == VERSION and rec.get("engine") == ENGINE, (rec.get("version"), rec.get("engine")))
        chk("沒留下暫存檔", not list(out.glob("*.tmp")))
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
        apply_extras(*doc_extras(src))
    try:
        return PRIOR.main(args)
    finally:
        restore()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0152 — 薄尾:ui 套三系統統一版面(政策 L121;承 L120 三系統對等獨立)

操作員令(2026-10-10):「三個系統統一設計自適應式對任何模板但功能獨立只有左面板可折疊下方有通往各系統的GATE」。
  ui  照前版鏈產出 VIA_Reports/vdf/VDF_UI_latest.html(頁面內容、動詞、清單照舊),再由本版就地套版面:
      ① 左面板(<aside>)整塊可折疊(⇔;記在瀏覽器,手機寬折成一條)
      ② 左面板底部「GATE · 三系統」:VCGC · VDF · VRN 各自的 U/I 頁 + 閘頁(燈 · 相對連結 · 產生它的指令);VDF 那塊標本頁
      ③ 右側(<main>)不折疊:<details>/<summary> 一律改成固定區塊
      ④ 版面與閘讀 supportive modules/ui_support/VIA_UI_ThreeSystems_SSOT_v*.json(尾版,只讀資料冊);讀不到用本檔內建同一份預設
      ⑤ 先關自動開頁、套完版面再開(前版是先開後改,瀏覽器可能讀到舊版)
      版面不是「一個 aside + 一個 main」就不硬改(照實回 YELLOW)。已套過不重套。清單 VDF_UI_MANIFEST.json 加 layout=L121。
其餘動詞照前版鏈。只收 VIA_FROM_VCGC=YES(舊名;= 經任一系統自己的 manager / 啟動器啟動,L120 ⑥ 甲)。不抓網、不碰 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====


import datetime
import html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0152"
SELF_ID = "VDF"


def _vnum_v0152(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0152(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0152(p) < _vnum_v0152(__file__)), key=_vnum_v0152)
PRIOR = _load_v0152(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _out_dir() -> Path:
    return Path(os.environ.get("VIA_VDF_HEALTH_OUT") or (Path(os.environ.get("VIA_VDF_HOME") or HERE).parents[1] / "VIA_Reports" / "vdf"))


# ---------- 三系統版面冊(L121):讀尾版;讀不到用內建同一份預設 ----------
DEFAULT_THREE = {
    "layout": {"left_collapsible": True, "right_collapsible": False, "gates_at": "left_bottom", "gate_title": "GATE · 三系統",
               "gate_rule": "只讀跳轉、互相監控(L120 ③);不是唯一入口。檔不在 = 灰燈 + 產生它的指令"},
    "systems": [
        {"id": "VCGC", "zh": "VCGC 治理",
         "ui": {"zh": "VCGC 操作台", "file": "VIA_Reports/ui_engine/VIA_UI_Engine_latest.html", "cmd": "via-vcgc run CGC_MDL261_UIEngine build --open"},
         "gates": [{"zh": "全綠閘", "file": "VIA_Reports/gate/GATE_latest.json", "cmd": "via-vcgc gate"},
                   {"zh": "交接閘", "file": "docs/handoff/HANDOFF_latest.json", "cmd": "via-vcgc handoff check"}]},
        {"id": "VDF", "zh": "VDF 資料",
         "ui": {"zh": "VDF 操作頁", "file": "VIA_Reports/vdf/VDF_UI_latest.html", "cmd": "via-vcgc run VDF_SystemManager ui"},
         "gates": [{"zh": "資料庫閘", "file": "VIA_Reports/vdf/DB_CHECK_latest.html", "cmd": "via-vcgc run VDF_SystemManager db check"},
                   {"zh": "引擎矩陣", "file": "VIA_Reports/vdf/ENGINE_MATRIX_latest.html", "cmd": "via-vcgc run VDF_SystemManager engine matrix"}]},
        {"id": "VRN", "zh": "VRN 報告",
         "ui": {"zh": "VRN 操作頁", "file": "VIA_Reports/vrn/VRN_UI_latest.html", "cmd": "via-vcgc run VRN_SystemManager ui"},
         "gates": [{"zh": "報告矩陣", "file": "VIA_Reports/vrn/VRN_REPORT_MATRIX.html", "cmd": "via-vcgc run VIA_VRN_FirstPageEngine --report"}]},
    ],
}


def three_book(path=None, root=None) -> dict:
    """→ 三系統版面冊(尾版)。讀不到 / 壞掉 / 少系統 → 內建預設,並寫明原因。"""
    root = Path(root or VIA_ROOT)
    if path is None:
        hits = sorted((root / "supportive modules" / "ui_support").glob("VIA_UI_ThreeSystems_SSOT_v*.json"), key=_vnum_v0152)
        path = hits[-1] if hits else None
    why = "找不到 VIA_UI_ThreeSystems_SSOT_v*.json"
    if path is not None:
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            ids = [s.get("id") for s in d.get("systems") or []]
            if len(ids) >= 3 and all(ids) and len(set(ids)) == len(ids):
                d["_path"] = Path(path).name
                return d
            why = "冊內系統不齊或重號:%s" % ids
        except Exception as exc:  # noqa: BLE001 — 冊壞照實記,用預設照常出頁
            why = "讀不了 %s:%s" % (Path(path).name, type(exc).__name__)
    d = json.loads(json.dumps(DEFAULT_THREE))
    d.update({"_path": None, "_fallback": why})
    return d


def _href(target: Path, page_dir: Path) -> str:
    try:
        return os.path.relpath(target, page_dir).replace(os.sep, "/")
    except ValueError:          # Windows 跨磁碟機:改絕對 file://
        return target.resolve().as_uri()


def _stamp(x: dict, root: Path, page_dir: Path) -> dict:
    p = root / (x.get("file") or "")
    ok = bool(x.get("file")) and p.is_file()
    return {**x, "exists": ok, "href": _href(p, page_dir) if ok else None,
            "ts": datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%m-%d %H:%M") if ok else None}


def three_systems(self_id=SELF_ID, path=None, page_dir=None, root=None) -> dict:
    root = Path(root or VIA_ROOT)
    page_dir = Path(page_dir or _out_dir())
    book = three_book(path, root)
    lay = dict(DEFAULT_THREE["layout"], **(book.get("layout") or {}))
    systems = [{"id": s.get("id"), "zh": s.get("zh") or s.get("id"), "self": s.get("id") == self_id,
                "ui": _stamp(s.get("ui") or {}, root, page_dir), "gates": [_stamp(g, root, page_dir) for g in s.get("gates") or []]}
               for s in book.get("systems") or []]
    return {"title": lay.get("gate_title"), "rule": lay.get("gate_rule"), "layout": lay, "spec": book.get("_path"),
            "fallback": book.get("_fallback"), "self": self_id, "systems": systems}


def gates_html(t: dict) -> str:
    esc = html.escape

    def dot(on):
        return "<i class='l121-dot%s'></i>" % (" on" if on else "")

    def lk(x, label):
        return ("<a href='%s' target='_blank' rel='noopener'>%s</a>" % (esc(x["href"]), label)) if x.get("exists") else "<span>%s</span>" % label

    def cb(c):
        return ("<button type='button' class='l121-cmd' data-l121cmd='%s' title='%s'>指令</button>" % (esc(c), esc(c))) if c else ""

    mini = "".join(
        ("<a class='g3m' href='%s' target='_blank' rel='noopener' title='%s'>%s</a>" % (esc(s["ui"]["href"]), esc(s["zh"]), esc(s["id"])))
        if (not s["self"] and s["ui"].get("exists")) else
        ("<span class='g3m%s' title='%s'>%s</span>" % (" on" if s["self"] else "", esc(s["zh"]) + ("(本頁)" if s["self"] else "(還沒產生)"), esc(s["id"])))
        for s in t["systems"])
    blocks = []
    for s in t["systems"]:
        u = s["ui"]
        head = ("<b>%s</b><span class='pill'>本頁</span>" % esc(s["zh"])) if s["self"] else lk(u, "<b>%s</b>" % esc(s["zh"]))
        rows = "".join("<div class='g3g'>%s%s%s%s</div>" % (dot(g["exists"]), lk(g, esc(g.get("zh") or "")),
                                                          ("<span class='ts'>%s</span>" % esc(g["ts"])) if g.get("ts") else "", cb(g.get("cmd")))
                       for g in s["gates"])
        blocks.append("<div class='g3s%s' data-sys='%s'><div class='g3n'>%s%s%s</div>%s</div>" % (
            " self" if s["self"] else "", esc(s["id"] or ""), dot(s["self"] or u.get("exists")), head, cb(u.get("cmd")), rows))
    note = esc(t.get("rule") or "") + ((" · 版面冊讀不到,用內建預設(%s)" % esc(t["fallback"])) if t.get("fallback") else "")
    return ("<div class='gates3' id='gates3'><div class='g3t'>%s</div><div class='g3mini'>%s</div>%s<div class='g3note'>%s</div></div>"
            % (esc(t.get("title") or "GATE · 三系統"), mini, "".join(blocks), note))


L121_CSS = """<style id="via-l121">/* [VIA:L121:v0100] 三系統統一版面:只有左面板可折疊 · 左下 GATE · 三系統 */
aside{display:flex;flex-direction:column}aside>*{flex:none}
#l121-fold{align-self:flex-end;margin:0 0 6px;padding:2px 9px;font-size:12px;cursor:pointer;border:1px solid var(--line,#e0e0e0);border-radius:6px;background:#fff}
.l121-in{min-width:0}
#gates3{margin-top:auto;position:sticky;bottom:-10px;z-index:2;max-height:46vh;overflow:auto;background:var(--panel,#f7f7f7);border-top:2px solid var(--txt,#1f2937);padding:6px 0 4px;box-shadow:0 -8px 10px -8px rgba(0,0,0,.18)}
#gates3 .g3t{font-weight:700;font-size:12px;letter-spacing:.05em;margin:2px 0 6px}
#gates3 .g3s{border:1px solid var(--line,#e0e0e0);border-radius:8px;background:#fff;padding:5px 8px;margin:5px 0}
#gates3 .g3s.self{border-color:var(--acc,#2563eb);background:#eef3f9}
#gates3 .g3n,#gates3 .g3g{display:flex;align-items:center;gap:6px;font-size:12px;margin:2px 0}
#gates3 .g3n b{font-size:12.5px}#gates3 a{color:var(--acc,#2563eb)}
#gates3 .l121-cmd{margin:0 0 0 auto;padding:1px 6px;font-size:11px}
#gates3 .ts{color:var(--dim,#6b7280);font-size:11px;white-space:nowrap}
#gates3 .pill{border-radius:10px;padding:0 6px;font-size:11px;background:#e5e7eb}
.l121-dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--lamp-gray,#9ca3af);flex:none}.l121-dot.on{background:var(--lamp-green,#16a34a)}
#gates3 .g3mini{display:none}
#gates3 .g3m{display:block;font-size:9px;font-weight:700;text-align:center;border:1px solid var(--line,#e0e0e0);border-radius:6px;padding:4px 1px;color:var(--acc,#2563eb);text-decoration:none;background:#fff;overflow:hidden}
#gates3 .g3m.on{background:var(--txt,#1f2937);color:#fff}
#gates3 .g3note{color:var(--dim,#6b7280);font-size:11px;margin-top:4px}
[data-l121=summary]{font-weight:600;margin:4px 0}
body.l121-fold{grid-template-columns:46px minmax(0,1fr)!important}
body.l121-fold aside{padding:8px 4px!important;overflow-x:hidden}
body.l121-fold aside>.l121-in{display:none}
body.l121-fold #gates3>*:not(.g3mini){display:none}
body.l121-fold #gates3 .g3mini{display:flex;flex-direction:column;gap:4px}
body.l121-fold #gates3{border-top-width:1px;box-shadow:none}
body.l121-fold #l121-fold{align-self:center}
@media(max-width:800px){#gates3{position:static;max-height:none;box-shadow:none}
 body.l121-fold{grid-template-columns:1fr!important}
 body.l121-fold aside{max-height:none;flex-direction:row;align-items:center;gap:8px}
 body.l121-fold #gates3{margin:0;border:0;padding:0}
 body.l121-fold #gates3 .g3mini{flex-direction:row}
 body.l121-fold #gates3 .g3m{padding:4px 8px}
 body.l121-fold #l121-fold{margin:0}}
</style>"""

L121_JS = """<script>(function(){var K='via.l121.fold.VDF';
function set(f){document.body.classList.toggle('l121-fold',!!f);try{localStorage.setItem(K,f?'1':'0')}catch(e){}}
var f=false;try{f=localStorage.getItem(K)==='1'}catch(e){}set(f);
document.addEventListener('click',function(ev){var t=ev.target.closest&&ev.target.closest('#l121-fold,[data-l121cmd]');if(!t)return;
 if(t.id==='l121-fold'){set(!document.body.classList.contains('l121-fold'));return}
 var c=t.getAttribute('data-l121cmd');function done(){t.textContent='已複製';setTimeout(function(){t.textContent='指令'},1200)}
 function fb(){var a=document.createElement('textarea');a.value=c;document.body.appendChild(a);a.select();try{document.execCommand('copy')}catch(e){}a.remove();done()}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(c).then(done,fb)}else fb()});})();</script>"""

FOLD_BTN = "<button type='button' id='l121-fold' title='收合 / 展開左面板'>⇔</button>"


def l121_patch(page, self_id=SELF_ID, spec_path=None, root=None) -> dict:
    """就地把 U/I 頁套成 L121 版面。版面不是一個 aside + 一個 main 就不動(照實回)。已套過不重套。"""
    page = Path(page)
    if not page.is_file():
        return {"patched": False, "why": "頁不在", "lamp": "YELLOW"}
    h = page.read_text(encoding="utf-8", errors="replace")
    if 'id="via-l121"' in h:
        return {"patched": False, "already": True, "why": "已套過", "lamp": "GREEN"}
    counts = {k: h.count(k) for k in ("<aside", "</aside>", "<main", "</main>")}
    mb = re.search(r"<body[^>]*>", h)
    if any(v != 1 for v in counts.values()) or not mb:
        return {"patched": False, "why": "版面不是一個 aside + 一個 main(不硬改):%s" % counts, "lamp": "YELLOW"}
    # ① <body> 與第一個版面元素之間的散卡(例:VRN v0151 主作業卡)→ 移進左面板最上面
    firsts = [i for i in (h.find("<header", mb.end()), h.find("<aside", mb.end()), h.find("<main", mb.end())) if i >= 0]
    cut = min(firsts) if firsts else mb.end()
    stray = h[mb.end():cut]
    moved = bool(stray.strip()) and "<script" not in stray
    if moved:
        h = h[:mb.end()] + h[cut:]
    t = three_systems(self_id, spec_path, page.parent, root)
    ma = re.search(r"<aside[^>]*>", h)
    h = h[:ma.end()] + FOLD_BTN + "<div class='l121-in'>" + (stray.strip() if moved else "") + h[ma.end():]
    h = h.replace("</aside>", "</div>" + gates_html(t) + "</aside>", 1)
    # ② 右側不折疊:<main> 內的 details / summary 改成固定區塊
    i, j = h.find("<main"), h.find("</main>")
    seg = h[i:j]
    n_det = seg.count("<details")
    seg = re.sub(r"<details\b([^>]*)>", r"<div data-l121='details'\1>", seg).replace("</details>", "</div>")
    seg = re.sub(r"<summary\b([^>]*)>", r"<div data-l121='summary'\1>", seg).replace("</summary>", "</div>")
    h = h[:i] + seg + h[j:]
    # ③ 前版頁開頁就呼 pre() 讀動詞欄;v0143 起左面板改族群設定、動詞欄已不在 → 載入即丟錯。只在缺欄時加守門
    js_guard = 0
    if "id='verb'" not in h and 'id="verb"' not in h and "\npre();\n" in h:
        h = h.replace("\npre();\n", "\nif(document.getElementById('verb'))pre();\n", 1)
        js_guard = 1
    # ④ 版面樣式 + 折疊 / 複製指令
    h = h.replace("</head>", L121_CSS + "</head>", 1) if "</head>" in h else L121_CSS + h
    a, sep, b = h.rpartition("</body>")
    h = (a + L121_JS + sep + b) if sep else h + L121_JS
    page.write_text(h, encoding="utf-8")
    return {"patched": True, "lamp": "GREEN" if not t.get("fallback") else "YELLOW", "moved_card": moved, "right_details": n_det, "js_guard": js_guard,
            "systems": [s["id"] for s in t["systems"]], "spec": t.get("spec"), "fallback": t.get("fallback"),
            "gates_on": sum(1 for s in t["systems"] for g in s["gates"] if g["exists"]), "gates_n": sum(len(s["gates"]) for s in t["systems"])}


def _manifest_note(page: Path, r: dict) -> None:
    mp = page.parent / (SELF_ID + "_UI_MANIFEST.json")
    try:
        m = json.loads(mp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    m.update({"layout": "L121", "left_collapsible": True, "right_collapsible": False, "gates_at": "left_bottom",
              "l121": {k: r.get(k) for k in ("patched", "already", "lamp", "systems", "spec", "fallback", "moved_card", "right_details", "js_guard")},
              "manager_l121": Path(__file__).name})
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def _open(page: Path) -> bool:
    if os.name != "nt":
        return False
    try:
        os.startfile(str(page))  # type: ignore[attr-defined]  # noqa: S606 — 本機頁面
        return True
    except OSError:
        return False


def ui_l121(args) -> int:
    want_open = os.environ.get("VIA_NO_OPEN") != "1"
    keep = os.environ.get("VIA_NO_OPEN")
    os.environ["VIA_NO_OPEN"] = "1"          # 先不開:套完版面再開
    try:
        rc = PRIOR.main(args)
    finally:
        if keep is None:
            os.environ.pop("VIA_NO_OPEN", None)
        else:
            os.environ["VIA_NO_OPEN"] = keep
    page = _out_dir() / (SELF_ID + "_UI_latest.html")
    r = l121_patch(page)
    _manifest_note(page, r)
    opened = _open(page) if (want_open and page.is_file()) else False
    print("[計] %s ui %s · L121 版面(左可折 · 左下 GATE · 三系統 · 右不折)· 系統 %s · 閘在 %s/%s · 散卡移左 %s · 右側 details 改固定 %s · 開頁腳本守門 %s · 冊 %s%s · %s%s" % (
        SELF_ID, TAG, "/".join(r.get("systems") or []), r.get("gates_on", "—"), r.get("gates_n", "—"), "是" if r.get("moved_card") else "否",
        r.get("right_details", 0), r.get("js_guard", 0), r.get("spec") or "內建預設", (" · " + r["why"]) if r.get("why") else "", r["lamp"], " · 已開頁" if opened else ""))
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["ui"]:
        return ui_l121(args)
    return PRIOR.main(args)


_FAKE = """<!doctype html><html><head><meta charset="utf-8"><style>body{display:grid;grid-template-columns:320px 1fr}</style></head>
<body><div id='card'>主作業卡</div><header><h1>X</h1></header>
<aside><div class='card'>左</div><button>組指令</button></aside>
<main><div class='tabs'><button onclick="tab(0,this)">一</button></div><details open><summary class='s'>右摺</summary><p>內容</p></details></main>
<script>function pre(){document.getElementById('verb').value}
pre();
</script></body></html>"""


def selftest() -> int:
    import shutil
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

    print("=== %s %s · 薄尾自測(L121 三系統統一版面)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="l121_" + SELF_ID.lower() + "_"))
    keep = {k: os.environ.get(k) for k in ("VIA_NO_OPEN", "VIA_VDF_HEALTH_OUT")}
    try:
        t = three_systems(SELF_ID)
        chk("① 版面冊尾版:三系統 VCGC · VDF · VRN;本系統 %s 標本頁;左可折 · 右不可折 · 閘在左下" % SELF_ID,
            [s["id"] for s in t["systems"]] == ["VCGC", "VDF", "VRN"] and [s["id"] for s in t["systems"] if s["self"]] == [SELF_ID]
            and t["layout"].get("left_collapsible") is True and t["layout"].get("right_collapsible") is False and t["layout"].get("gates_at") == "left_bottom"
            and t["spec"] and not t["fallback"], t.get("fallback"))
        bad = td / "bad.json"
        bad.write_text("{x", encoding="utf-8")
        fb = [three_systems(SELF_ID, q, td, td) for q in (td / "nope.json", bad)]
        chk("② 冊讀不到 / 壞 → 內建預設照常出三塊並寫明原因(不假裝讀到)",
            all(x["fallback"] and [s["id"] for s in x["systems"]] == ["VCGC", "VDF", "VRN"] for x in fb), [x["fallback"] for x in fb])
        root = td / "via"
        (root / "VIA_Reports" / "vcgc_x").mkdir(parents=True)
        (root / "VIA_Reports" / "ui_engine").mkdir(parents=True)
        (root / "VIA_Reports" / "ui_engine" / "VIA_UI_Engine_latest.html").write_text("x", encoding="utf-8")
        pd = root / "VIA_Reports" / SELF_ID.lower()
        pd.mkdir(parents=True)
        page = pd / (SELF_ID + "_UI_latest.html")
        page.write_text(_FAKE, encoding="utf-8")
        r = l121_patch(page, SELF_ID, td / "nope.json", root)
        h = page.read_text(encoding="utf-8")
        aside = h[h.find("<aside"):h.find("</aside>")]
        chk("③ 套版:折疊鈕在左面板頂 · GATE · 三系統在左面板最後 · 散卡移進左面板 · 頁首回到 body 第一格",
            r["patched"] and "id='l121-fold'" in aside and aside.rstrip().endswith("</div></div>") and "id='gates3'" in aside
            and aside.find("id='gates3'") > aside.find("組指令") and "主作業卡" in aside and re.search(r"<body[^>]*><header", h) is not None, r)
        chk("④ 右側不折疊:<main> 內 0 個 <details>/<summary>;內容照留", "<details" not in h and "<summary" not in h and "右摺" in h and "內容" in h
            and r["right_details"] == 1)
        chk("④b 動詞欄不在時開頁腳本加守門(載入不再丟錯);有動詞欄的頁不動", r["js_guard"] == 1 and "if(document.getElementById('verb'))pre();" in h)
        chk("⑤ 閘連結用相對路徑(搬家 / 打包照樣能跳);沒產生的閘灰燈無連結",
            "href='../ui_engine/VIA_UI_Engine_latest.html'" in h and h.count("<a class='g3m'") == 1 and "(還沒產生)" in h)
        chk("⑥ 樣式 + 折疊記憶 + 複製指令在;已套過不重套(冪等)",
            'id="via-l121"' in h and "via.l121.fold.%s" % SELF_ID in h and "data-l121cmd" in h and l121_patch(page, SELF_ID, None, root).get("already") is True)
        odd = td / "odd.html"
        odd.write_text("<html><body><main>x</main></body></html>", encoding="utf-8")
        before = odd.read_bytes()
        r2 = l121_patch(odd)
        chk("⑦ 版面不是一個 aside + 一個 main → 不硬改(檔不動,照實回 YELLOW)", not r2["patched"] and r2["lamp"] == "YELLOW" and odd.read_bytes() == before, r2)
        os.environ["VIA_VDF_HEALTH_OUT"] = str(td / "real_out")
        os.environ["VIA_NO_OPEN"] = "1"
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["ui"])
        real = td / "real_out" / (SELF_ID + "_UI_latest.html")
        rh = real.read_text(encoding="utf-8") if real.is_file() else ""
        man = {}
        try:
            man = json.loads((td / "real_out" / (SELF_ID + "_UI_MANIFEST.json")).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        chk("⑧ 真跑 ui(前版鏈產頁 → 本版套版):rc 0 · 頁有左下 GATE · 三系統 · 右側 0 details · 清單 layout=L121",
            rc == 0 and "id='gates3'" in rh and "<details" not in rh[rh.find("<main"):rh.find("</main>")] and man.get("layout") == "L121"
            and "L121 版面" in buf.getvalue(), buf.getvalue()[-400:])
        body = Path(__file__).read_text(encoding="utf-8")
        import ast
        chk("⑨ 橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式(只讀資料冊)· 不直派子行程",
            all(x in body for x in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]")) and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
            and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "261_UIEngine_v" not in body
            and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.name or "").split(".")[0] == "sub" + "process" for a in n.names) for n in ast.walk(ast.parse(body))))
        print("  ── 前版鏈自測(原樣印出;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
        chk("⑩ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("[計] %s_v0152 自測 %d/%d · %s" % (_STEM, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

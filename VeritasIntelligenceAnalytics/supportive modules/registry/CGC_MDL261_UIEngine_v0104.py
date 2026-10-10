#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL261_UIEngine v0104 — 薄尾:三系統統一版面(政策 L121)· 左下 GATE · 三系統 · 右側不折疊

操作員令(2026-10-10):「三個系統統一設計自適應式對任何模板但功能獨立只有左面板可折疊下方有通往各系統的GATE」
  (政策 L121;承 L120 三系統對等獨立:VCGC · VDF · VRN 各自的 U/I 引擎各出各的頁,版面規則同一份,功能互不影響)。
  ① 左面板底部 = 「GATE · 三系統」:VCGC · VDF · VRN 三塊,各有該系統自己的 U/I 頁 + 閘頁(燈 · 連結 · 產生它的指令);
     本頁那一塊標「本頁」。收合時只留三個系統代號的小鈕(仍可跳)。
  ② 只有左面板可折疊:右側五頁拿掉所有 <details>(第一頁大類改成固定標頭 + 表;第四頁文件清單改成固定列)。
  ③ 版面與閘讀 supportive modules/ui_support/VIA_UI_ThreeSystems_SSOT_v*.json(尾版);讀不到用本檔內建的同一份預設照常出頁。
  ④ 品牌字與頁首不再寫「VCGC → VDF × VRN」(那是舊的一對二);改「三系統對等」。其餘照 v0103(五頁 · 匯入 · 自動跳出)。
只讀:不連網、不寫冊;閘只看檔在不在 + 時間,不代跑他系統。只收 VCGC 呼叫。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
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

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI_DIR = VIA / "supportive modules" / "ui_support"
SELF_ID = "VCGC"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = _vnum(__file__)
    hits = [p for p in HERE.glob("CGC_MDL261_UIEngine_v*.py") if 0 <= _vnum(p) < me]
    return max(hits, key=_vnum)


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE           # v0100 本體:build / inject / BUILTIN / snapshot 在這裡


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"CGC_MDL261_UIEngine v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
BUILTIN_V0103 = PRIOR.BUILTIN_V0103
_SNAPSHOT_V0103 = BASE.snapshot


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


def three_book(path=None) -> dict:
    """→ 三系統版面冊(尾版)。讀不到 / 壞掉 / 少系統 → 內建預設,並寫明原因(不假裝讀到)。"""
    if path is None:
        hits = sorted(UI_DIR.glob("VIA_UI_ThreeSystems_SSOT_v*.json"), key=_vnum)
        path = hits[-1] if hits else None
    why = "找不到 VIA_UI_ThreeSystems_SSOT_v*.json"
    if path is not None:
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            ids = [s.get("id") for s in d.get("systems") or []]
            if len(ids) >= 3 and all(ids) and len(set(ids)) == len(ids):
                d["_path"] = Path(path).resolve().relative_to(VIA).as_posix() if Path(path).resolve().is_relative_to(VIA) else str(path)
                return d
            why = f"冊內系統不齊或重號:{ids}"
        except Exception as exc:  # noqa: BLE001
            why = f"讀不了 {Path(path).name}:{type(exc).__name__}"
    return {**json.loads(json.dumps(DEFAULT_THREE)), "_path": None, "_fallback": why}


def _stamp(x: dict) -> dict:
    p = VIA / (x.get("file") or "")
    ok = bool(x.get("file")) and p.is_file()
    return {**x, "exists": ok, "uri": p.resolve().as_uri() if ok else None,
            "ts": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(timespec="minutes") if ok else None}


def three_systems(self_id: str = SELF_ID, path=None) -> dict:
    """→ 左下 GATE 區的資料:三系統各自的 U/I 頁 + 閘頁(在不在 · 連結 · 時間 · 指令);self_id 那塊標本頁。"""
    book = three_book(path)
    lay = {**DEFAULT_THREE["layout"], **(book.get("layout") or {})}
    systems = [{"id": s.get("id"), "zh": s.get("zh") or s.get("id"), "self": s.get("id") == self_id,
                "ui": _stamp(s.get("ui") or {}), "gates": [_stamp(g) for g in s.get("gates") or []]}
               for s in book.get("systems") or []]
    return {"title": lay.get("gate_title"), "rule": lay.get("gate_rule"), "layout": lay, "spec": book.get("_path"),
            "fallback": book.get("_fallback"), "self": self_id, "systems": systems}


def snapshot_v0104(cfg: dict, home):
    snap = _SNAPSHOT_V0103(cfg, home)
    snap.setdefault("oc", {})["three"] = three_systems(SELF_ID)
    return snap


# ---------- 範本:在 v0103 範本上換段(每個錨點只准出現一次;沒換到的記進 PATCH_MISSES,自測會紅) ----------
_GATES3_JS = r"""function gates3(){var L=O.three||{},SY=L.systems||[];
 if(!SY.length&&(O.gates||[]).length)SY=[{id:'VCGC',zh:'閘',self:true,ui:{},gates:O.gates}];
 function lk(x,t){return x.exists?'<a href="'+esc(x.uri)+'" target="_blank" rel="noopener">'+t+'</a>':'<span>'+t+'</span>'}
 function cb(c){return c?'<button class="fold-btn" data-cmd="'+esc(c)+'" title="'+esc(c)+'">指令</button>':''}
 var h='<div class="gates3" id="gates3"><div class="g3t">'+esc(L.title||'GATE · 三系統')+'</div><div class="g3mini">'
  +SY.map(function(s){var u=s.ui||{};return (!s.self&&u.exists)?'<a class="g3m" href="'+esc(u.uri)+'" target="_blank" rel="noopener" title="'+esc(s.zh)+'">'+esc(s.id)+'</a>'
   :'<span class="g3m'+(s.self?' on':'')+'" title="'+esc(s.zh)+(s.self?'(本頁)':'(還沒產生)')+'">'+esc(s.id)+'</span>'}).join('')+'</div>';
 SY.forEach(function(s){var u=s.ui||{};
  h+='<div class="g3s'+(s.self?' self':'')+'" data-sys="'+esc(s.id)+'"><div class="g3n">'+dot(s.self||u.exists?'GREEN':'NODATA')
   +(s.self?'<b>'+esc(s.zh)+'</b><span class="pill">本頁</span>':lk(u,'<b>'+esc(s.zh)+'</b>'))+cb(u.cmd)+'</div>'
   +(s.gates||[]).map(function(g){return '<div class="gate">'+dot(g.exists?'GREEN':'NODATA')+lk(g,esc(g.zh))
     +(g.ts?'<span class="note">'+esc(String(g.ts).slice(5,16).replace('T',' '))+'</span>':'')+cb(g.cmd)+'</div>'}).join('')+'</div>'});
 return h+'<div class="note">'+esc(L.rule||'')+(L.fallback?' · 版面冊讀不到,用內建預設('+esc(L.fallback)+')':'')+'</div></div>'}
"""

_CSS_V0104 = (".side{display:flex;flex-direction:column}.side>*{flex:none}"
              ".side{padding-bottom:10px}"
              ".gates3{margin-top:auto;border-top:2px solid var(--ink);padding-top:6px;position:sticky;bottom:-10px;z-index:2;"
              "max-height:46vh;overflow:auto;background:var(--paper);box-shadow:0 -8px 10px -8px rgba(30,29,26,.18)}"
              ".g3t{font-weight:700;font-size:12px;letter-spacing:.05em;margin:4px 0 6px}"
              ".g3s{border:1px solid var(--line);border-radius:var(--r);background:var(--paper2);padding:6px 9px;margin:6px 0}"
              ".g3s.self{border-color:var(--blue);background:#eef3f9}"
              ".g3n{display:flex;align-items:center;gap:6px;font-size:12.5px}.g3n a{color:var(--blue)}"
              ".gate .note{white-space:nowrap}.gates3 .gate{margin:2px 0}.gates3 .fold-btn{padding:1px 6px;font-size:11px}"
              ".g3mini{display:none}.g3m{display:block;font-size:9px;font-weight:700;text-align:center;border:1px solid var(--line);"
              "border-radius:6px;padding:4px 1px;overflow:hidden;color:var(--blue);text-decoration:none;background:var(--paper2)}.g3m.on{background:var(--ink);color:#fff}"
              ".app.fold .side>.gates3{display:block;border-top:1px solid var(--line)}.app.fold .gates3>*:not(.g3mini){display:none}"
              ".app.fold .gates3>.g3mini{display:flex;flex-direction:column;gap:4px}"
              ".cathd{padding:9px 12px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}.cathd b{font-size:13.5px}.cat>.tw{margin:0 10px 10px}"
              ".seg.docs{max-height:132px;overflow:auto}")
_CSS_V0104_MOBILE = ("@media (max-width:900px){.gates3{position:static;max-height:none;box-shadow:none}.app.fold .side>.gates3{display:block;margin-top:6px}"
                     ".app.fold .gates3>.g3mini{flex-direction:row;flex-wrap:wrap}.app.fold .g3m{padding:4px 8px}}\n")


def _build_v0104(tpl: str):
    misses = []

    def swap(old: str, new: str):
        nonlocal tpl
        if tpl.count(old) != 1:
            misses.append(old[:48])
            return
        tpl = tpl.replace(old, new)

    a = tpl.find("h+='<details open><summary>③ 跳到 VCGC / VDF 閘")
    b = tpl.find("$('#side').innerHTML=h}")
    if a < 0 or b < a:
        misses.append("③ 跳到 VCGC / VDF 閘 … side() 結尾")
    else:
        tpl = tpl[:a] + "h+=gates3();\n " + tpl[b:]
    swap("function side(){", _GATES3_JS + "function side(){")
    swap("<small>VCGC → VDF × VRN · 左功能 右顯示</small>", "<small>VCGC 治理 · 三系統對等 · 左功能 右顯示</small>")
    swap("\">VCGC → VDF × VRN · '", "\">VCGC · VDF · VRN 對等 · '")
    swap("h+='<details class=\"cat\"><summary><b>'", "h+='<div class=\"cat\"><div class=\"cathd\"><b>'")
    swap("<span class=\"pill bad\">✗ '+esc(s.TODO||0)+'</span></summary>'", "<span class=\"pill bad\">✗ '+esc(s.TODO||0)+'</span></div>'")
    swap("{max:520})+'</details>'});", "{max:360})+'</div>'});")
    swap("'<details class=\"docs\"'+(d?'':' open')+'><summary class=\"note\" style=\"cursor:pointer\">有首頁全文的文件 '+docs.length+' 份(點選切換)</summary><div class=\"seg\">'",
         "'<div class=\"note\" style=\"margin-top:6px\">有首頁全文的文件 '+docs.length+' 份(點選切換)</div><div class=\"seg docs\">'")
    swap("'</div></details></div>';", "'</div></div>';")
    swap("from:'CGC_MDL261_UIEngine v0103'", "from:'CGC_MDL261_UIEngine v0104'")
    swap(".lp{white-space:nowrap}", ".lp{white-space:nowrap}" + _CSS_V0104)
    swap("</style>", _CSS_V0104_MOBILE + "</style>")
    return tpl, misses


BUILTIN_V0104, PATCH_MISSES = _build_v0104(BUILTIN_V0103)
BASE.BUILTIN = BUILTIN_V0104
PRIOR.BUILTIN = BUILTIN_V0104
BASE.snapshot = snapshot_v0104
BASE.TAG = PRIOR.TAG = TAG


def right_segment(page_or_tpl: str) -> str:
    """右面板五頁的 JS 段(自測用:這段不准有 <details)。"""
    a = page_or_tpl.find("// ---------- 右面板(顯示)----------")
    b = page_or_tpl.find("function render(){", a)
    return page_or_tpl[a:b] if 0 <= a < b else ""


def cmd_three() -> int:
    t = three_systems(SELF_ID)
    print(f"[ui-engine] {t['title']} · 冊 {t['spec'] or '內建預設'}" + (f" · {t['fallback']}" if t.get("fallback") else ""))
    for s in t["systems"]:
        u = s["ui"]
        print(f"  [{s['id']}] {s['zh']}{'(本頁)' if s['self'] else ''} · U/I {'在' if u.get('exists') else '缺'} {u.get('file', '')}")
        for g in s["gates"]:
            print(f"      {'●' if g['exists'] else '○'} {g['zh']} · {g.get('file')} · {g.get('cmd')}")
    return 0


# ---------- 自測 ----------
def selftest() -> int:
    import ast
    import shutil
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    keep_b, keep_s = BASE.BUILTIN, BASE.snapshot
    BASE.BUILTIN, BASE.snapshot = BUILTIN_V0103, _SNAPSHOT_V0103
    PRIOR.BUILTIN = BUILTIN_V0103
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
    finally:
        BASE.BUILTIN, BASE.snapshot = keep_b, keep_s
        PRIOR.BUILTIN = keep_b
        BASE.TAG = PRIOR.TAG = TAG
    chk("① v0103 自測照過(連 v0102 · v0101 · v0100 鏈;跑前版時用前版自己的範本與快照)", prior_rc == 0, buf.getvalue()[-300:])
    chk("② 範本換段全數到位(每個錨點恰好一次)", not PATCH_MISSES, PATCH_MISSES)
    t = three_systems("VCGC")
    lay = t["layout"]
    chk("③ 版面冊:三系統 VCGC · VDF · VRN 各有 U/I 頁 + 閘 + 指令;只有 VCGC 標本頁;左可折 · 右不可折 · 閘在左下",
        [s["id"] for s in t["systems"]] == ["VCGC", "VDF", "VRN"] and [s["self"] for s in t["systems"]] == [True, False, False]
        and all(s["ui"].get("file") and s["ui"].get("cmd") and s["gates"] and all(g.get("cmd") for g in s["gates"]) for s in t["systems"])
        and lay.get("left_collapsible") is True and lay.get("right_collapsible") is False and lay.get("gates_at") == "left_bottom"
        and t["spec"] and not t["fallback"], t)
    tmp = Path(tempfile.mkdtemp(prefix="mdl261v4_"))
    keep_wd = (BASE.WORK_DIR, BASE.WORK_CONFIG)
    try:
        bad = tmp / "VIA_UI_ThreeSystems_SSOT_v0999.json"
        bad.write_text("{not json", encoding="utf-8")
        two = tmp / "two.json"
        two.write_text(json.dumps({"systems": [{"id": "VCGC"}, {"id": "VDF"}]}), encoding="utf-8")
        fb = [three_systems("VDF", p) for p in (tmp / "nope.json", bad, two)]
        chk("④ 冊讀不到 / 壞 JSON / 少系統 → 內建預設照常出三塊並寫明原因;self 跟呼叫者走(VDF 呼叫就標 VDF)",
            all(f["fallback"] and [s["id"] for s in f["systems"]] == ["VCGC", "VDF", "VRN"] and [s["self"] for s in f["systems"]] == [False, True, False]
                for f in fb), [f["fallback"] for f in fb])
        st = _stamp({"zh": "x", "file": "VIA_Reports/gate/GATE_latest.json"})
        miss = _stamp({"zh": "y", "file": "VIA_Reports/__nope__/X.html"})
        chk("⑤ 閘戳:在 → 連結 + 時間;不在 → 灰燈無連結(不代跑他系統)",
            (st["exists"] == (VIA / "VIA_Reports/gate/GATE_latest.json").is_file()) and miss["exists"] is False and miss["uri"] is None and miss["ts"] is None, (st, miss))
        BASE.WORK_DIR = tmp / "work"
        BASE.WORK_CONFIG = BASE.WORK_DIR / "ui_config.json"
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        cfg = BASE.load_config(sets=[f"locations.db_root={home}"])
        with contextlib.redirect_stdout(io.StringIO()):
            snap, out, rep = BASE.build(cfg, home, tmp / "ui" / "page.html")
        page = out.read_text(encoding="utf-8")
        script = page[page.index("<script>\n(function"):]
        side_js = script[script.index("function side(){"):script.index("$('#side').innerHTML=h}") + 24]
        chk("⑥ 頁面:左下 GATE · 三系統(side() 最後一段 = gates3)· 快照帶三系統 · 舊「③ 跳到 VCGC / VDF 閘」已換掉",
            side_js.rstrip().endswith("h+=gates3();\n $('#side').innerHTML=h}") and 'id="gates3"' in script and "③ 跳到 VCGC / VDF 閘" not in page
            and len(((snap.get("oc") or {}).get("three") or {}).get("systems") or []) == 3, side_js[-120:])
        chk("⑦ 只有左面板可折疊:右側五頁 0 個 <details>;第一頁大類 = 固定標頭 + 表;第四頁文件清單固定列",
            right_segment(script) and "<details" not in right_segment(script) and 'class="cat"><div class="cathd">' in script
            and 'class="seg docs"' in script and 'id="fold"' in script, right_segment(script).count("<details"))
        chk("⑧ 版面:左面板直欄、GATE 釘在左面板底部(margin-top:auto + sticky,不用捲就看得到);收合時留三個系統代號小鈕;手機寬也留",
            all(k in page for k in (".side{display:flex;flex-direction:column}", ".gates3{margin-top:auto", "position:sticky;bottom:-10px", ".app.fold .side>.gates3{display:block",
                                    ".app.fold .gates3>.g3mini{display:flex", "@media (max-width:900px){.gates3{position:static", ".app.fold .side>.gates3{display:block;margin-top:6px}")))
        chk("⑨ 不再寫一對二(VCGC → VDF × VRN);匯出標本版號;零 CDN · 零 fetch",
            "VCGC → VDF × VRN" not in page and "from:'CGC_MDL261_UIEngine v0104'" in script
            and not re.search(r'(src|href)="https?://', page) and "fetch(" not in script and "XMLHttpRequest" not in page)
    finally:
        BASE.WORK_DIR, BASE.WORK_CONFIG = keep_wd
        shutil.rmtree(tmp, ignore_errors=True)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 檔頭:加速器橋 · 網路橋在(__future__ 之後);不碰 TA-Lib;本檔不以目前解譯器直派子行程",
        "[VIA:ACCEL-BRIDGE:" in text and "[VIA:NET-BRIDGE:" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE:")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((a.name or "").split(".")[0] == "sub" + "process" for a in n.names)
                    for n in ast.walk(ast.parse(text))))
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0103 鏈 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv[:1] == ["three"]:
        return cmd_three()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

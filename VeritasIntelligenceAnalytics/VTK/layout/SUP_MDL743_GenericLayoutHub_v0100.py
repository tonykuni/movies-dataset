#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL743_GenericLayoutHub — GLE 全後端統轄橋(批421;操作員令)
====================================================================
操作員令:「REGISTER AND IMPLEMENT THESE TWO SYSTEMS AS SUPPORTIVE
MODULES TO SUPPORT VRN」(GenericLayoutEngine_AllEngines v2.1.0 +
VIA_NLP_Application_System v1.8.0)。本檔=前者的支援模組正主。

收容查驗(批421 實測,誠實記錄):上傳包 18 檔對在庫
`GenericLayoutEngine_AllEngines_v2.1.0_b245` 逐檔比對 → 16 檔位元相同;
`Install-GenericLayoutEngine-All.ps1` 唯一差異是 `${ExitCode}:`→`$ExitCode:`
(後者在 PowerShell 會把 `:` 誤讀為範圍/磁碟限定符=上傳版反而是回歸,
不採);另多一枚 `dist/*.whl`(原始碼的建置產物,原始碼已在庫=不重複收容)。
→ 結論:**GLE 不新增收容夾**(Zero-Hydra:不造第二份實作),本橋改為
把既有收容件升格為全樹可用的支援服務。

本橋之所以存在(在此之前的缺口):
  · GLE 收容件在庫,但只有 VRN_ENG072 私下掛載,且只用 generic_layout_engine
    一支;`all_backend_engines`(30 後端優先序)與 `multi_engine_orchestrator`
    (路由/共識/快取)**全樹無人呼叫**=收容了但沒被採用。
  · ENG073/ENG074/ENG080 想用 GLE 只能各自再寫一份掛載=九頭龍。
本橋=單一掛載點,誰要誰呼,實作零複製(收容件原地不動)。

尾版律(承 ENG072 批246 教訓,原樣沿用不另立):夾名字母序會踩
`AllEngines_v2.1.0` < `v2.0.0` 的陷阱 → 一律取夾名鏈上 vX.Y.Z 語意最大者。

誠實三態:收容缺席=absent(不假裝);模組可掛但後端未裝=
SKIPPED_UNAVAILABLE 列名不假在;例外=帶例外型別回報,絕不吞。
零網路:全程 importlib/檔案系統,不連外。
只增不減:不刪、不改收容件一個位元;重械(paddle/tesseract 等)備而不載。

用法:python3 SUP_MDL743_GenericLayoutHub_v0100.py [status|probe|route] | --selftest
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

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = VIA / "functional modules" / "VRN" / "references" / "intake"

MODULE_ID = "SUP_MDL743"
HUB_NAME = "GenericLayoutHub"
HUB_VERSION = "v0100"
GLE_GLOB = "GenericLayoutEngine*"
#: 收容件內四支正主(缺一即降級,絕不自行補寫替代品=Zero-Hydra)
GLE_MODULES = ("generic_layout_engine", "adapter_sdk",
               "all_backend_engines", "multi_engine_orchestrator")

_CACHE: dict = {}


def _label(d: Path) -> str:
    """辨識名=收容夾相對路徑。巢狀型只印 d.name 會得到光禿禿的
    `GenericLayoutEngine`,看不出是 v2.0.0_b242 還是 AllEngines_v2.1.0_b245。"""
    try:
        return str(d.relative_to(INTAKE))
    except Exception:
        return d.name


def _ver(d: Path) -> tuple:
    """語意版號排序(ENG072 批246 教訓沿用):取夾名鏈上 vX.Y.Z 最大者。
    字母序會讓 `AllEngines_v2.1.0` 排在 `v2.0.0` 之前=尾版取錯。"""
    names = d.name + "|" + d.parent.name
    vs = [tuple(int(x) for x in m.groups())
          for m in re.finditer(r"v(\d+)\.(\d+)\.(\d+)", names)]
    return max(vs) if vs else (0, 0, 0)


def roots() -> list[Path]:
    """收容件候選夾(頂層型 v2.0.0_b242 + 巢狀一層型 AllEngines_v2.1.0_b245)"""
    out: list[Path] = []
    if not INTAKE.is_dir():
        return out
    for top in sorted(INTAKE.glob(GLE_GLOB)):
        if not top.is_dir():
            continue
        if (top / "generic_layout_engine.py").exists():
            out.append(top)
        for sub in sorted(top.iterdir()):
            if sub.is_dir() and (sub / "generic_layout_engine.py").exists():
                out.append(sub)
    return out


def newest() -> Path | None:
    """尾版夾;收容缺席=None(誠實 absent)"""
    c = roots()
    return max(c, key=_ver) if c else None


def mount() -> dict:
    """掛載尾版收容件(單例;收容件原地不動)。
    回 {state, dir, version, loaded:[], missing:[{name,error}]}"""
    if "mount" in _CACHE:
        return _CACHE["mount"]
    d = newest()
    if d is None:
        _CACHE["mount"] = {"state": "ABSENT", "dir": None, "version": None,
                           "loaded": [], "missing": [],
                           "why": f"收容件缺席(找不到 {GLE_GLOB}/generic_layout_engine.py)"}
        return _CACHE["mount"]
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))
    loaded, missing, mods = [], [], {}
    for name in GLE_MODULES:
        try:
            mods[name] = __import__(name)
            loaded.append(name)
        except Exception as exc:                    # 誠實:帶型別,不吞
            missing.append({"name": name, "error": f"{type(exc).__name__}: {exc}"})
    ver = ".".join(str(x) for x in _ver(d))
    _CACHE["mods"] = mods
    _CACHE["mount"] = {
        "state": "VERIFIED" if len(loaded) == len(GLE_MODULES)
                 else ("PARTIAL" if loaded else "FAILED"),
        "dir": str(d), "dir_name": _label(d), "version": ver,
        "loaded": loaded, "missing": missing,
        "why": "" if len(loaded) == len(GLE_MODULES) else "部分正主未掛載",
    }
    return _CACHE["mount"]


def _mod(name: str):
    mount()
    return _CACHE.get("mods", {}).get(name)


def gle():
    """generic_layout_engine 正主(版面/分區/字重/表格富化);缺席=None"""
    return _mod("generic_layout_engine")


def backend_engines():
    """all_backend_engines 正主(30 後端 adapter 優先序);缺席=None"""
    return _mod("all_backend_engines")


def orchestrator():
    """multi_engine_orchestrator 正主(路由/共識/快取);缺席=None"""
    return _mod("multi_engine_orchestrator")


def adapter_sdk():
    """adapter_sdk 正主(BaseAdapter/AdapterResult 契約);缺席=None"""
    return _mod("adapter_sdk")


def backend_matrix() -> dict:
    """後端在位矩陣(誠實:未裝=列名 available False,不假在、不預載)"""
    G = gle()
    if G is None:
        return {"available": False, "total": 0, "on": [], "off": [],
                "why": mount().get("why") or "GLE 正主缺席"}
    try:
        st = G.probe_backends()
    except Exception as exc:
        return {"available": False, "total": 0, "on": [], "off": [],
                "why": f"probe 例外({type(exc).__name__}: {exc})"}
    on = sorted(s.name for s in st if s.available)
    off = sorted(s.name for s in st if not s.available)
    return {"available": True, "total": len(st), "on": on, "off": off,
            "rows": [{"name": s.name, "role": s.role, "available": s.available,
                      "python": s.python_available, "binary": s.binary_available,
                      "message": s.message} for s in st],
            "why": ""}


def adapter_roster() -> list[dict]:
    """all_backend_engines 的 adapter 優先序冊(輕→重;不代裝任何一支)"""
    B = backend_engines()
    if B is None:
        return []
    rows = []
    for k, v in vars(B).items():
        if k.endswith("_PRIORITY") and isinstance(v, int):
            rows.append({"adapter": k[:-len("_PRIORITY")].lower(), "priority": v})
    return sorted(rows, key=lambda r: (r["priority"], r["adapter"]))


def route_modes() -> dict:
    """orchestrator 的模式→adapter 具名路由表。
    實測(批421):MODE_ADAPTERS 只有四個具名鍵 consensus/tables/paddle/ocr;
    DEFAULT_MODE="auto" 與 "all" **不在表內**,由 build_route 的 else 分支落到
    build_all_adapters()(且 mode!="all" 時再濾 resource_level<=5)。
    此處只回具名表=不替引擎編造不存在的鍵。落空模式見 route_fallthrough()。"""
    O = orchestrator()
    if O is None:
        return {}
    m = getattr(O, "MODE_ADAPTERS", None)
    return {k: list(v) for k, v in m.items()} if isinstance(m, dict) else {}


def route_fallthrough() -> dict:
    """落空模式(具名表外)之真實去向;orchestrator 缺席=空"""
    O = orchestrator()
    if O is None:
        return {}
    named = set(route_modes())
    default = str(getattr(O, "DEFAULT_MODE", ""))
    return {"default_mode": default,
            "named": sorted(named),
            "fallthrough": sorted({default, "all"} - named),
            "goes_to": "build_all_adapters()(mode!='all' 再濾 resource_level<=5)"}


def zone_annotate(blocks: list[dict], W: float, H: float) -> dict:
    """九宮分區標+字重階層+本文字級推定+後端矩陣(單一實作)。
    輸出契約與 VRN_ENG072 v0106 `gle_annotate` 逐鍵相同=引擎可原地改呼本橋
    而輸出零變化(Zero-Hydra:實作只留這一份)。
    blocks 元素需含 x0/y0/x1/y1/size/lines,選配 font/bold。"""
    G = gle()
    if G is None:
        return {"available": False, "note": "GLE 收容件缺席=誠實 absent"}
    try:
        els = []
        for b in blocks:
            bb = G.BBox(b["x0"], b["y0"], b["x1"], b["y1"])
            wt, bold, italic = G.font_weight_from_name(
                b.get("font", ""), 16 if b.get("bold") else 0)
            els.append({"zone": G.zone_for_bbox(bb, W, H),
                        "weight": wt, "bold": bold, "italic": italic,
                        "size": round(b["size"], 1),
                        "head": " ".join(b["lines"])[:80]})
        body_font = G.weighted_median(
            [(b["size"], sum(len(ln) for ln in b["lines"])) for b in blocks])
        bm = backend_matrix()
        return {"available": True, "engine": "GenericLayoutEngine/2.x",
                "engine_dir": mount().get("dir_name", "?"),
                "body_font": round(body_font, 1) if body_font else None,
                "elements": els,
                "backends_available": bm.get("on", []),
                "backends_total": bm.get("total", 0)}
    except Exception as exc:
        return {"available": False, "note": f"GLE 例外({type(exc).__name__})"}


def status() -> dict:
    m = mount()
    bm = backend_matrix()
    return {"module": MODULE_ID, "hub": HUB_NAME, "version": HUB_VERSION,
            "mount": m, "backends": {"total": bm.get("total", 0),
                                     "on": bm.get("on", []),
                                     "off_count": len(bm.get("off", []))},
            "adapters": len(adapter_roster()), "route_modes": sorted(route_modes())}


def _print_status() -> int:
    s = status()
    m = s["mount"]
    print(f"=== {MODULE_ID} {HUB_NAME} {HUB_VERSION} · GLE 全後端統轄橋 ===")
    print(f"  掛載態  {m['state']}  夾={m.get('dir_name') or '(缺席)'}  版={m.get('version')}")
    if m["missing"]:
        for x in m["missing"]:
            print(f"    [缺] {x['name']} — {x['error']}")
    if m.get("why"):
        print(f"    **為何**:{m['why']}")
    print(f"  正主    載入 {len(m['loaded'])}/{len(GLE_MODULES)} — {', '.join(m['loaded']) or '(無)'}")
    b = s["backends"]
    print(f"  後端    在位 {len(b['on'])}/{b['total']} — {', '.join(b['on']) or '(無)'}")
    print(f"          未裝 {b['off_count']} 支=SKIPPED_UNAVAILABLE(列名不假在;不預載)")
    print(f"  adapter 優先序冊 {s['adapters']} 支 · 路由模式 {', '.join(s['route_modes']) or '(無)'}")
    return 0


def _print_probe() -> int:
    bm = backend_matrix()
    if not bm["available"]:
        print(f"[絕] 後端矩陣不可得:{bm['why']}")
        return 1
    print(f"=== GLE 後端矩陣({bm['total']} 支;零網路 importlib/which 探測)===")
    for r in bm["rows"]:
        mark = "在位" if r["available"] else "未裝"
        print(f"  [{mark}] {r['name']:<22} {r['role']:<12} py={r['python']!s:<5} bin={r['binary']!s:<5}")
    print(f"  [計] 在位 {len(bm['on'])} · 未裝 {len(bm['off'])}")
    return 0


def _print_route() -> int:
    modes = route_modes()
    if not modes:
        print("[絕] 路由表不可得(orchestrator 未掛載)")
        return 1
    print("=== GLE 多引擎路由表(mode → adapters)===")
    for k in sorted(modes):
        print(f"  {k:<10} {len(modes[k]):>2} 支 · {', '.join(modes[k][:8])}"
              + (" …" if len(modes[k]) > 8 else ""))
    ft = route_fallthrough()
    print(f"  {'(落空)':<10} {', '.join(ft.get('fallthrough', [])) or '-'}"
          f" → {ft.get('goes_to', '?')}")
    ros = adapter_roster()
    print(f"  [優先序冊] {len(ros)} 支(輕→重):"
          + ", ".join(f"{r['adapter']}({r['priority']})" for r in ros[:10]) + " …")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    m = mount()
    chk("① 收容件在位且四正主全掛載(generic_layout_engine/adapter_sdk/"
        "all_backend_engines/multi_engine_orchestrator)",
        m["state"] == "VERIFIED" and len(m["loaded"]) == 4,
        f"({m['state']};載入 {len(m['loaded'])}/4;{m.get('why') or '無異'})")

    # ② 尾版律對照組:字母序 vs 語意序必須不同答案,否則本檢空轉
    cands = roots()
    alpha = sorted(cands)[-1] if cands else None
    semantic = newest()
    chk("② 尾版律=語意版號(對照組:字母序取 v2.0.0=錯,語意序取 v2.1.0=對)",
        len(cands) >= 2 and alpha is not None and semantic is not None
        and _ver(semantic) > _ver(alpha) and _ver(semantic) == (2, 1, 0),
        f"(候選 {len(cands)};字母序={alpha.name if alpha else '-'}"
        f"→{_ver(alpha) if alpha else '-'};語意序={semantic.name if semantic else '-'}"
        f"→{_ver(semantic) if semantic else '-'})")

    bm = backend_matrix()
    chk("③ 後端矩陣誠實(在位+未裝總和=全冊;未裝者列名不假在)",
        bm["available"] and bm["total"] > 0
        and len(bm["on"]) + len(bm["off"]) == bm["total"],
        f"(在位 {len(bm['on'])}/{bm['total']};未裝 {len(bm['off'])} 列名保留)")

    src = Path(__file__).read_text(encoding="utf-8")
    import ast as _ast
    _imports = set()
    for _n in _ast.walk(_ast.parse(src)):
        if isinstance(_n, _ast.Import):
            _imports |= {a.name.split(".")[0] for a in _n.names}
        elif isinstance(_n, _ast.ImportFrom) and _n.module:
            _imports.add(_n.module.split(".")[0])
    chk("④ 重械備而不預載:本橋 AST 零安裝面(不匯入 subprocess/os;"
        "未裝後端只列名不代裝、不代設同意閘)",
        not (_imports & {"subprocess", "os", "pip"}),
        f"(匯入 {sorted(_imports)})")
    chk("④b 未裝後端誠實掛 False(對照組:在位者與未裝者同時存在才算真測)",
        bool(bm.get("on")) and bool(bm.get("off"))
        and all(r["available"] is False for r in bm.get("rows", [])
                if r["name"] in set(bm.get("off", []))),
        f"(在位 {len(bm.get('on', []))} · 未裝 {len(bm.get('off', []))})")

    ros = adapter_roster()
    chk("⑤ adapter 優先序冊在位且輕型優先(pdfplumber < paddle_ocr < adobe)",
        len(ros) >= 25
        and next(r["priority"] for r in ros if r["adapter"] == "pdfplumber")
        < next(r["priority"] for r in ros if r["adapter"] == "paddle_ocr")
        < next(r["priority"] for r in ros if r["adapter"] == "adobe_extract"),
        f"({len(ros)} 支)")

    modes, ft = route_modes(), route_fallthrough()
    chk("⑥ 路由表如實=四具名(consensus/tables/paddle/ocr)+ auto/all 落空到"
        " build_all_adapters(不編造不存在的鍵)",
        set(modes) == {"consensus", "tables", "paddle", "ocr"}
        and ft.get("default_mode") == "auto"
        and set(ft.get("fallthrough", [])) == {"auto", "all"}
        and "build_all_adapters" in ft.get("goes_to", "")
        and "camelot" in modes["tables"] and "tesseract" in modes["ocr"],
        f"(具名 {sorted(modes)};落空 {ft.get('fallthrough')})")

    # ⑦ 契約對齊:zone_annotate 的鍵必須與 ENG072 v0106 gle_annotate 一字不差
    blocks = [{"x0": 10, "y0": 10, "x1": 300, "y1": 40, "size": 18.0,
               "font": "Arial-Bold", "bold": True, "lines": ["台積電 2330 TT 買進"]},
              {"x0": 10, "y0": 60, "x1": 500, "y1": 400, "size": 10.0,
               "font": "Arial", "bold": False, "lines": ["本文" * 40]}]
    ann = zone_annotate(blocks, 595.0, 842.0)
    want = {"available", "engine", "engine_dir", "body_font", "elements",
            "backends_available", "backends_total"}
    chk("⑦ zone_annotate 契約與 ENG072 gle_annotate 逐鍵相同(引擎可原地改呼=零輸出變化)",
        ann.get("available") and set(ann) == want
        and len(ann["elements"]) == 2 and ann["body_font"] == 10.0
        and ann["elements"][0]["bold"] is True,
        f"(鍵 {len(set(ann))};body_font={ann.get('body_font')};"
        f"zone0={ann['elements'][0]['zone'] if ann.get('elements') else '-'})")

    # ⑧ 缺席誠實(對照組:把 INTAKE 指到空夾,必須回 ABSENT 而非假綠)
    global INTAKE
    keep, keep_cache = INTAKE, dict(_CACHE)
    try:
        INTAKE = HERE / "_no_such_intake_dir_"
        _CACHE.clear()
        m2, bm2 = mount(), backend_matrix()
        ok = (m2["state"] == "ABSENT" and not bm2["available"]
              and "缺席" in m2["why"] and bm2["why"])
    finally:
        INTAKE = keep
        _CACHE.clear()
        _CACHE.update(keep_cache)
    chk("⑧ 收容缺席=ABSENT 且說得出為何(對照組:指向空夾;不假綠、不吞原因)", ok)

    chk("⑨ 紀律宣告(只增不減/Zero-Hydra/收容件原地不動/零網路 在檔)",
        all(t in src for t in ("只增不減", "Zero-Hydra", "收容件原地不動",
                               "零網路", "VIA:ACCEL-BRIDGE")))

    n = 9
    print(f"  [計] 九檢 OK {n - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== {MODULE_ID} {HUB_NAME} · 九檢自測(零網路;含尾版律與缺席對照組)===")
        return selftest()
    if "--json" in args:
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return 0
    verb = next((a for a in args if not a.startswith("-")), "status")
    return {"probe": _print_probe, "route": _print_route}.get(verb, _print_status)()


if __name__ == "__main__":
    sys.exit(main())

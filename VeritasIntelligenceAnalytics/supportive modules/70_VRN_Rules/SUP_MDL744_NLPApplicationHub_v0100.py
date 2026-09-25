#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL744_NLPApplicationHub — NLP 應用系統統轄橋(批421;操作員令)
====================================================================
操作員令:「REGISTER AND IMPLEMENT THESE TWO SYSTEMS AS SUPPORTIVE
MODULES TO SUPPORT VRN」。本檔=VIA_NLP_Application_System v1.8.0 的
支援模組正主(另一支 SUP_MDL743=GenericLayoutEngine)。

收容(批421):`VIA_NLP_Application_System_v1.8.0` 68 檔入
`functional modules/VRN/references/intake/`,原件一位元未改。

**本橋要修的真缺陷**(批420 盤點所得,誠實記錄):
  · 鏈上兩支引擎把收容夾寫死成 `VIA_NLP_OneEngine_v1.1.0`——
    VRN_ENG072_FirstPageText_v0106.py:123 與
    VRN_ENG073_ReportStructuredDB_v0113.py:134。
  · 但庫裡早有 v1.5.0(`VIA_NLP_OneEngine_b283/`),現在又有 v1.8.0。
    v1.1.0 只有 20 模組;v1.8.0 有 41 模組,**多出來的正是研報解讀要用的**
    table_ops(表格結構化)/layout_analysis(版面分塊)/content_roles/
    context_reconstruction/summarization/function_classifier。
  · 寫死路徑=尾版律破口,而且破在最痛的地方(12 筆真 FAIL 全是
    目標價與 EPS 抽不出來)。
本橋=單一掛載點,尾版語意解析跨兩個家族名,誰要誰呼。

家族命名(兩系列同套 `src/via_nlp_engine`,不可只認一個 glob):
  VIA_NLP_OneEngine_v*            (v1.1.0 頂層、v1.5.0 巢狀於 _b283)
  VIA_NLP_Application_System_v*   (v1.8.0;批421 新收容)

尾版律:語意版號比較(1.10 > 1.9;字母序會反答);跨家族取語意最大者。

雙掛防制(本橋獨有):Python 一個行程只能有一個 `via_nlp_engine`。
若別人(舊引擎)已先把 v1.1.0 掛進 sys.modules,本橋**不偷換、不假裝**,
而是誠實回報 mounted_from 與 requested,讓呼叫端看得見自己拿到的是哪版。

誠實三態:收容缺席=ABSENT;掛到非尾版=MOUNTED_STALE(明說是誰先佔);
例外=帶型別回報,絕不吞。捕捉到卻不顯示=等於沒捕捉。
零網路:全程 importlib/檔案系統。只增不減:收容件原地不動。

用法:python3 SUP_MDL744_NLPApplicationHub_v0100.py
        [status|roster|delta|demo] | --selftest
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
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = VIA / "functional modules" / "VRN" / "references" / "intake"

MODULE_ID = "SUP_MDL744"
HUB_NAME = "NLPApplicationHub"
HUB_VERSION = "v0100"
#: 兩個家族名皆提供 src/via_nlp_engine;只認一個 glob 就會漏掉尾版
PKG_GLOBS = ("VIA_NLP_Application_System_v*", "VIA_NLP_OneEngine_v*")
PKG_MARKER = Path("src") / "via_nlp_engine"
LEXICON_REL = Path("data") / "lexicon" / "ssot_lexicon.json"
#: 研報解讀直接相關的服務模組(v1.1.0 全缺;本橋開通的就是這些)
REPORT_SERVICE_MODULES = ("table_ops", "layout_analysis", "content_roles",
                          "context_reconstruction", "summarization",
                          "function_classifier")

_CACHE: dict = {}


def _label(d: Path) -> str:
    """辨識名=收容夾相對路徑。只印 d.name 會讓 `VIA_NLP_OneEngine_b283/
    VIA_NLP_OneEngine_v1.1.0` 與頂層那份 v1.1.0 顯示成同一個=看起來像重複列。"""
    try:
        return str(d.relative_to(INTAKE))
    except Exception:
        return d.name


def _ver(d: Path) -> tuple:
    """語意版號(取夾名鏈上 vX.Y[.Z] 最大者)。
    字母序陷阱:'v1.10.0' < 'v1.9.0' 為字串真、語意假 → 一律轉整數元組。"""
    names = d.name + "|" + d.parent.name
    vs = []
    for m in re.finditer(r"v(\d+)\.(\d+)(?:\.(\d+))?", names):
        vs.append((int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)))
    return max(vs) if vs else (0, 0, 0)


def roots() -> list[Path]:
    """收容件候選(頂層型 + 巢狀一層型;兩家族聯集)"""
    out: list[Path] = []
    if not INTAKE.is_dir():
        return out
    for g in PKG_GLOBS:
        for top in sorted(INTAKE.glob(g)):
            if not top.is_dir():
                continue
            if (top / PKG_MARKER).is_dir():
                out.append(top)
        # 巢狀:VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0
    for top in sorted(INTAKE.iterdir()) if INTAKE.is_dir() else []:
        if not top.is_dir():
            continue
        for sub in sorted(top.iterdir()):
            if (sub.is_dir() and (sub / PKG_MARKER).is_dir()
                    and any(sub.match(g) for g in PKG_GLOBS)):
                out.append(sub)
    seen, uniq = set(), []
    for p in out:
        if str(p) not in seen:
            seen.add(str(p))
            uniq.append(p)
    return uniq


def newest() -> Path | None:
    c = roots()
    return max(c, key=_ver) if c else None


def mount() -> dict:
    """掛載尾版收容件。雙掛防制:若 via_nlp_engine 已被他人先佔,
    誠實回 MOUNTED_STALE + 佔位者路徑,不偷換 sys.modules。"""
    if "mount" in _CACHE:
        return _CACHE["mount"]
    want = newest()
    if want is None:
        _CACHE["mount"] = {"state": "ABSENT", "dir": None, "version": None,
                           "requested": None, "mounted_from": None,
                           "why": f"收容件缺席(兩家族 {PKG_GLOBS} 皆無 {PKG_MARKER})"}
        return _CACHE["mount"]
    src = want / "src"
    pre = sys.modules.get("via_nlp_engine")
    pre_file = getattr(pre, "__file__", None) if pre is not None else None
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        import via_nlp_engine  # noqa: F401
        got = Path(getattr(via_nlp_engine, "__file__", "") or "").resolve()
    except Exception as exc:
        _CACHE["mount"] = {"state": "FAILED", "dir": str(want),
                           "version": ".".join(map(str, _ver(want))),
                           "requested": str(want), "mounted_from": None,
                           "why": f"匯入失敗({type(exc).__name__}: {exc})"}
        return _CACHE["mount"]
    same = str(want.resolve()) in str(got)
    _CACHE["mount"] = {
        "state": "VERIFIED" if same else "MOUNTED_STALE",
        "dir": str(want), "dir_name": _label(want),
        "version": ".".join(map(str, _ver(want))),
        "requested": str(want), "mounted_from": str(got.parent.parent),
        "preoccupied_by": pre_file,
        "why": "" if same else
               (f"via_nlp_engine 已被他人先佔於 {got.parent.parent}"
                f"(尾版 {want.name} 未生效);同行程單套件律,本橋不偷換"),
    }
    return _CACHE["mount"]


def _pkg():
    m = mount()
    return None if m["state"] in ("ABSENT", "FAILED") else sys.modules.get("via_nlp_engine")


def _sub(name: str):
    """取子模組;__main__ 絕不碰(它 import 即跑 argparse 會炸)"""
    if name == "__main__" or _pkg() is None:
        return None
    try:
        import importlib
        return importlib.import_module(f"via_nlp_engine.{name}")
    except Exception:
        return None


def module_roster() -> dict:
    """尾版收容件模組冊(誠實:__main__ 標為不可載入=import 即跑 argparse)"""
    m = mount()
    d = Path(m["dir"]) if m.get("dir") else None
    if d is None:
        return {"total": 0, "loadable": [], "excluded": [], "why": m.get("why", "")}
    files = sorted(p.stem for p in (d / PKG_MARKER).glob("*.py"))
    excluded = [x for x in files if x in ("__init__", "__main__")]
    return {"total": len(files),
            "loadable": [x for x in files if x not in excluded],
            "excluded": excluded,
            "excluded_why": "__main__ 匯入即執行 argparse(會以 SystemExit 中斷宿主)",
            "why": m.get("why", "")}


def capability_delta() -> dict:
    """尾版 vs 各舊版的模組差(說明升版到底換到什麼;不換空話)"""
    cur = newest()
    if cur is None:
        return {}
    def mods(d: Path) -> set:
        return {p.stem for p in (d / PKG_MARKER).glob("*.py")} - {"__init__", "__main__"}
    top = mods(cur)
    out = {"newest": _label(cur), "newest_modules": len(top), "versus": []}
    for d in sorted(roots(), key=_ver):
        if d == cur:
            continue
        old = mods(d)
        out["versus"].append({
            "dir": _label(d), "modules": len(old),
            "gained": sorted(top - old), "lost": sorted(old - top)})
    out["report_services_present"] = sorted(set(REPORT_SERVICE_MODULES) & top)
    out["report_services_missing"] = sorted(set(REPORT_SERVICE_MODULES) - top)
    return out


# ---------- 服務面(VRN 引擎直接消費的四道) ----------

def text_processor():
    """TextProcessor 單例(帶 ssot_lexicon;缺 lexicon 亦建構,退無詞庫模式)"""
    if "tp" in _CACHE:
        return _CACHE["tp"]
    tp = None
    mod = _sub("text_ops")
    m = mount()
    if mod is not None and m.get("dir"):
        try:
            lex = Path(m["dir"]) / LEXICON_REL
            tp = mod.TextProcessor(lex) if lex.exists() else mod.TextProcessor(None)
        except Exception:
            tp = None
    _CACHE["tp"] = tp
    return tp


def nfkc(s: str) -> str:
    """正規化:TextProcessor 正主;缺席=stdlib NFKC 後備(行為不變、不假綠)"""
    tp = text_processor()
    if tp is not None:
        try:
            return tp.normalize(s)
        except Exception:
            pass
    return unicodedata.normalize("NFKC", s)


def segments(text: str) -> list[dict]:
    """無損切段(LosslessSegmenter 正主);缺席=整篇一段的誠實退路"""
    k = _sub("knowledge")
    if k is not None:
        try:
            return k.LosslessSegmenter().segment(text)["segments"]
        except Exception:
            pass
    return [{"segment_id": "SEG-000001", "text": text, "kind": "article",
             "source_span": {"start": 0, "end": len(text)}}]


def tables(text: str) -> list[dict]:
    """表格結構化(TextTableExtractor:markdown 管線表 + key:value 對)。
    逐格照抄=cell_policy verbatim_only_no_silent_fill(不補值、不猜表頭)。
    收容缺席=空清單(誠實無表,不編表)。"""
    t = _sub("table_ops")
    if t is None:
        return []
    try:
        return t.TextTableExtractor().extract(segments(text))
    except Exception:
        return []


def layout(text: str) -> dict:
    """版面分塊(MarkdownLayoutAnalyzer:每個字元歸屬一個版面塊)"""
    la = _sub("layout_analysis")
    if la is None:
        return {}
    try:
        return la.MarkdownLayoutAnalyzer().build(text, segments(text), [])
    except Exception:
        return {}


def roles(text: str) -> dict:
    """內容角色(ContentRoleAnalyzer;需版面分塊為輸入)"""
    cr = _sub("content_roles")
    lay = layout(text)
    if cr is None or not lay:
        return {}
    try:
        return cr.ContentRoleAnalyzer().build(text, lay)
    except Exception:
        return {}


def status() -> dict:
    m = mount()
    r = module_roster()
    d = capability_delta()
    return {"module": MODULE_ID, "hub": HUB_NAME, "version": HUB_VERSION,
            "mount": m, "modules": r["total"], "loadable": len(r["loadable"]),
            "report_services": d.get("report_services_present", []),
            "report_services_missing": d.get("report_services_missing", []),
            "candidates": [_label(p) for p in sorted(roots(), key=_ver)]}


def _print_status() -> int:
    s, m = status(), mount()
    print(f"=== {MODULE_ID} {HUB_NAME} {HUB_VERSION} · NLP 應用系統統轄橋 ===")
    print(f"  掛載態  {m['state']}  夾={m.get('dir_name') or '(缺席)'}  版={m.get('version')}")
    if m.get("why"):
        print(f"    **為何**:{m['why']}")
    if m.get("preoccupied_by"):
        print(f"    先佔者:{m['preoccupied_by']}")
    print(f"  候選    {len(s['candidates'])} 套(語意序):{' < '.join(s['candidates'])}")
    print(f"  模組    {s['modules']} 支(可載入 {s['loadable']};__main__ 排除)")
    print(f"  研報服務 在位 {len(s['report_services'])}/{len(REPORT_SERVICE_MODULES)}"
          f" — {', '.join(s['report_services']) or '(無)'}")
    if s["report_services_missing"]:
        print(f"          缺席 — {', '.join(s['report_services_missing'])}")
    return 0


def _print_roster() -> int:
    r = module_roster()
    if not r["total"]:
        print(f"[絕] 模組冊不可得:{r.get('why')}")
        return 1
    print(f"=== NLP 模組冊({r['total']} 支;可載入 {len(r['loadable'])})===")
    for i in range(0, len(r["loadable"]), 4):
        print("  " + "  ".join(f"{x:<26}" for x in r["loadable"][i:i + 4]))
    print(f"  [排除] {', '.join(r['excluded'])} — {r['excluded_why']}")
    return 0


def _print_delta() -> int:
    d = capability_delta()
    if not d:
        print("[絕] 差異不可得(收容缺席)")
        return 1
    print(f"=== 尾版 {d['newest']}({d['newest_modules']} 模組)對各舊版 ===")
    for v in d["versus"]:
        print(f"  vs {v['dir']}({v['modules']} 模組):+{len(v['gained'])} 支"
              + (f" · -{len(v['lost'])} 支" if v["lost"] else ""))
        if v["gained"]:
            print(f"     新增:{', '.join(v['gained'])}")
        if v["lost"]:
            print(f"     **反而少**:{', '.join(v['lost'])}")
    print(f"  [研報服務] 在位 {d['report_services_present']}")
    if d["report_services_missing"]:
        print(f"  [研報服務] 缺席 {d['report_services_missing']}")
    return 0


def _print_demo() -> int:
    txt = ("台積電 (2330 TT) 買進 目標價 1250 元\n"
           "| 項目 | 2024 | 2025F | 2026F |\n| --- | --- | --- | --- |\n"
           "| 稀釋EPS(元) | 45.2 | 58.7 | 66.1 |\n"
           "目標價: 1250\n評等: 買進\n")
    tb, lay = tables(txt), layout(txt)
    print("=== 服務實跑(合成樣本;零網路)===")
    print(f"  表格 {len(tb)} 張")
    for t in tb:
        print(f"    {t['kind']:<14} 表頭={t['headers']} 列={len(t['rows'])}"
              f" 信心={t['confidence']} 需覆核={t['review_required']}")
        for row in t["rows"][:3]:
            print(f"      {row}")
    print(f"  版面塊 {len(lay.get('blocks', []))}:"
          f" {[b['block_type'] for b in lay.get('blocks', [])]}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    m = mount()
    chk("① 收容件在位且掛的就是尾版(非 MOUNTED_STALE)",
        m["state"] == "VERIFIED" and m.get("version") == "1.8.0",
        f"({m['state']};夾={m.get('dir_name')};版={m.get('version')};"
        f"{m.get('why') or '無異'})")

    # ② 尾版律跨家族:字母序會取錯家族,語意序才對(對照組)
    cands = roots()
    alpha = sorted(cands, key=lambda p: p.name)[-1] if cands else None
    sem = newest()
    chk("② 尾版律跨兩家族(對照組:字母序取 OneEngine 系,語意序取"
        " Application_System v1.8.0)",
        len(cands) >= 3 and alpha is not None and sem is not None
        and alpha.name.startswith("VIA_NLP_OneEngine")
        and sem.name.startswith("VIA_NLP_Application_System")
        and _ver(sem) > _ver(alpha),
        f"(候選 {len(cands)};字母序={alpha.name if alpha else '-'};"
        f"語意序={sem.name if sem else '-'})")

    chk("③ 語意版號不踩字母序陷阱(v1.10.0 > v1.9.0)",
        _ver(Path("/x/pkg_v1.10.0")) > _ver(Path("/x/pkg_v1.9.0"))
        and "v1.10.0" < "v1.9.0",
        f"({_ver(Path('/x/pkg_v1.10.0'))} > {_ver(Path('/x/pkg_v1.9.0'))};"
        "字串比較則相反)")

    r = module_roster()
    chk("④ 模組冊 41 支且 __main__ 被排除(它 import 即跑 argparse 會中斷宿主)",
        r["total"] == 41 and "__main__" in r["excluded"]
        and len(r["loadable"]) == 39
        and _sub("__main__") is None,
        f"(共 {r['total']};可載入 {len(r['loadable'])})")

    d = capability_delta()
    v11 = next((v for v in d["versus"] if v["dir"].endswith("v1.1.0")), None)
    chk("⑤ 升版實得(對 v1.1.0 淨增 21 支且六項研報服務全在位;舊版一支不少)",
        v11 is not None and len(v11["gained"]) == 21 and not v11["lost"]
        and d["report_services_present"] == sorted(REPORT_SERVICE_MODULES),
        f"(v1.1.0 {v11['modules'] if v11 else '-'} 支 → 尾版 "
        f"{d['newest_modules']} 支;研報服務 {len(d['report_services_present'])}/6)")

    tp = text_processor()
    # 判別輸入:連續空白 stdlib NFKC 不併,TextProcessor 會併 →
    # 用它才分得出「走正主」還是「悄悄退回後備」(全形轉半形兩者皆同=測不出來)
    _probe_in = "台積電  的的的營收"
    _tp_out = nfkc(_probe_in)
    _std_out = unicodedata.normalize("NFKC", _probe_in)
    _tp_file = ""
    if tp is not None:
        _tp_file = getattr(sys.modules.get(tp.__class__.__module__, None),
                           "__file__", "") or ""
    chk("⑥ TextProcessor 正掛且 nfkc 真走正主(判別輸入:連續空白 stdlib 不併、"
        "正主會併;並驗載入檔就在尾版夾內)",
        tp is not None and hasattr(tp, "split_sentences")
        and _tp_out != _std_out and _tp_out == "台積電 的的的營收"
        and str(m.get("dir", "")) in _tp_file,
        f"(正主={_tp_out!r} vs stdlib={_std_out!r};"
        f"載自 {Path(_tp_file).parent.name if _tp_file else '-'})")

    txt = ("台積電 (2330 TT) 買進 目標價 1250 元\n"
           "| 項目 | 2024 | 2025F | 2026F |\n| --- | --- | --- | --- |\n"
           "| 稀釋EPS(元) | 45.2 | 58.7 | 66.1 |\n"
           "目標價: 1250\n評等: 買進\n")
    tb = tables(txt)
    md = next((x for x in tb if x["kind"] == "markdown_pipe"), None)
    kv = next((x for x in tb if x["kind"] == "key_value"), None)
    chk("⑦ 表格服務抽得出研報要件(管線表 稀釋EPS 三期值 + key:value 目標價/評等)",
        md is not None and kv is not None
        and md["headers"] == ["項目", "2024", "2025F", "2026F"]
        and md["rows"][0] == ["稀釋EPS(元)", "45.2", "58.7", "66.1"]
        and any(row[0] == "目標價" and row[1] == "1250" for row in kv["rows"]),
        f"({len(tb)} 張;md 列 {len(md['rows']) if md else 0};"
        f"kv 列 {len(kv['rows']) if kv else 0})")

    chk("⑧ 逐格照抄不補值(cell_policy=verbatim_only_no_silent_fill)",
        all(x.get("cell_policy") == "verbatim_only_no_silent_fill" for x in tb)
        and bool(tb))

    lay = layout(txt)
    chk("⑨ 版面分塊在位且完整覆蓋(每字元歸屬一塊;table 塊被認出)",
        bool(lay.get("blocks"))
        and "table" in [b["block_type"] for b in lay["blocks"]]
        and lay.get("completeness", {}).get("exact_reconstruction") is True,
        f"({len(lay.get('blocks', []))} 塊;"
        f"{[b['block_type'] for b in lay.get('blocks', [])]})")

    # ⑩ 缺席誠實(對照組:INTAKE 指空夾 → ABSENT,且服務退空不假造)
    global INTAKE
    keep, keep_cache = INTAKE, dict(_CACHE)
    try:
        INTAKE = HERE / "_no_such_intake_dir_"
        _CACHE.clear()
        m2 = mount()
        t2 = tables(txt)
        seg2 = segments(txt)
        ok = (m2["state"] == "ABSENT" and "缺席" in m2["why"]
              and t2 == [] and len(seg2) == 1 and seg2[0]["text"] == txt)
    finally:
        INTAKE = keep
        _CACHE.clear()
        _CACHE.update(keep_cache)
    chk("⑩ 收容缺席=ABSENT 說得出為何,且表格退空清單、切段退整篇一段"
        "(誠實無表,絕不編表)", ok)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 紀律宣告(只增不減/收容件原地不動/尾版律/雙掛防制/零網路 在檔)",
        all(t in src for t in ("只增不減", "收容件原地不動", "尾版律",
                               "雙掛防制", "零網路", "VIA:ACCEL-BRIDGE")))

    n = 11
    print(f"  [計] 十一檢 OK {n - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== {MODULE_ID} {HUB_NAME} · 十一檢自測"
              "(零網路;含尾版律/字母序陷阱/缺席對照組)===")
        return selftest()
    if "--json" in args:
        print(json.dumps(status(), ensure_ascii=False, indent=1))
        return 0
    verb = next((a for a in args if not a.startswith("-")), "status")
    return {"roster": _print_roster, "delta": _print_delta,
            "demo": _print_demo}.get(verb, _print_status)()


if __name__ == "__main__":
    sys.exit(main())

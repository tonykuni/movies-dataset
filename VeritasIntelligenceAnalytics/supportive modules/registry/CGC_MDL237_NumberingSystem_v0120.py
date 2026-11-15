#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0120 — 薄尾:舊同義字列補 scope(mom_alias 不再被詞彙表擋)· .py 常數正則用 AST 取原式

操作員令(2026-11-14):「mom_alias 也一起修,開 PR 並盯著 · HANDLE ALL PROBLEMS」。
實錄:候選冊 v0102 的操作員提案 mom_alias(VQG · scope indicator.names · MOM / Momentum / 動能指標 → VQG.IND.MOM)
  中央檢測一直 REVIEW:LEGACY_ALIAS_SCOPE_UNKNOWN —— 撞到舊列 VIA-VCGC-SYN214(glossary|MOMENTUM:動能 / MOMENTUM,
  中英詞彙表)。v0114 make_plan 對「沒有 scope、分類也不是 中央同義冊/」的舊同義字列一律當成範圍不明而擋。
  真倉 3217 列舊同義字:584 列分類帶 中央同義冊/<scope>;其餘 2633 列(ins 2022 · glossary 389 · macro 214 · xsrc 6 ·
  macro-family 2)沒有 scope —— 任何新同義字只要有一個字跟它們重疊就卡住。
本版只加三格(v0100 … v0119 一字不動):
  ① 舊同義字列 scope = legacy.<鍵前綴>(鍵本身就帶命名空間:glossary|… · ins|… · macro|…;沒有前綴時用分類)——
     讀冊投影(load_state;存冊一字不動)+ 收集時同樣補(synonym_items)。不同 scope 照 v0114 既有規則「同字異域各自保留」
     (記 SAME_WORD_OTHER_SCOPE_RETAINED 註記,不擋);同 owner 同 scope 的舊列照比目標、不同照擋。
  ② R22 舊正則列的來源是 .py 模組常數(VeritasCeleritas DataValidator._TW_TICKER_RE · VeritasAegisNexus TW_TICKER_REGEX …)
     時,用 AST 讀那個常數(re.compile("…") 的第一個字面參數或字面字串)當原式;只讀,不執行被讀的檔。
號不變;寫冊只走前版的 --apply(本檔不寫任何檔)。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL237_NumberingSystem"
CENTRAL_SYN_PREFIX = "中央同義冊/"


def _vnum_v0120(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0120(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0120(p) < _vnum_v0120(__file__)), key=_vnum_v0120)
PRIOR = _load_v0120(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0119:R22 舊正則列 scope + 原式 · 讀冊投影
BASE = PRIOR.BASE
BASE.ENGINE = ENGINE
_LOAD_STATE_V0119 = BASE.load_state                                     # = v0119.load_state(已投影 R22 舊正則列)
_SYN_ITEMS_ORIG_V0120 = BASE.synonym_items
_ENRICH_V0119 = PRIOR.enrich
_PY_INDEX_V0120: dict = {}


def _sanitize_v0120(s: str) -> str:
    return re.sub(r"[^a-z0-9_.:-]+", "_", str(s).lower()).strip("._") or "x"


def legacy_syn_scope(row: dict) -> str | None:
    """舊同義字列的 scope:已有 scope / 分類是 中央同義冊/ → None(不動);否則 legacy.<鍵前綴>(沒前綴用分類)。"""
    if row.get("kind") != "SYN" or row.get("asset_intake") or row.get("scope") or str(row.get("cat", "")).startswith(CENTRAL_SYN_PREFIX):
        return None
    key = str(row.get("key") or "")
    ns = key.split("|", 1)[0] if "|" in key else str(row.get("cat") or "misc")
    return "legacy." + _sanitize_v0120(ns)


def load_state() -> dict:
    """同 v0119(R22 舊正則列已投影),另把舊同義字列沒有 scope 的當場補 legacy.<鍵前綴>(唯讀投影;存冊一字不動)。"""
    st = _LOAD_STATE_V0119()
    rows = st.get("rows") or {}
    for k, r in list(rows.items()):
        sc = legacy_syn_scope(r)
        if sc:
            rows[k] = dict(r, scope=sc)
    return st


def synonym_items(extra: list) -> list:
    """同 v0100;收集出來的舊同義字項同樣補 scope(apply 時 make_plan 的 legacy 走這份)。"""
    out = []
    for it in _SYN_ITEMS_ORIG_V0120(extra):
        sc = legacy_syn_scope(it)
        out.append(dict(it, scope=sc) if sc else it)
    return out


def py_path(source: str) -> Path | None:
    name = Path(str(source)).name
    if not name.endswith(".py"):
        return None
    if (HERE / name).is_file():
        return HERE / name
    if not _PY_INDEX_V0120:
        for root, dirs, files in os.walk(BASE.VIA):
            dirs[:] = [d for d in dirs if d not in PRIOR.SKIP_DIRS_V0119]
            for f in files:
                if f.endswith(".py"):
                    _PY_INDEX_V0120.setdefault(f, Path(root) / f)
        _PY_INDEX_V0120.setdefault("\0built", Path("."))
    return _PY_INDEX_V0120.get(name)


def py_constant(tree: ast.AST, dotted: str):
    """AST 取常數:「名」= 模組層賦值;「類.名」= 類本體賦值。值 = re.compile("…") 第一個字面參數,或字面字串;取不到回 None。"""
    parts = dotted.split(".")
    body = getattr(tree, "body", [])
    for cls in parts[:-1]:
        body = next((n.body for n in body if isinstance(n, ast.ClassDef) and n.name == cls), None)
        if body is None:
            return None
    want = parts[-1]
    for n in body:
        targets = n.targets if isinstance(n, ast.Assign) else ([n.target] if isinstance(n, ast.AnnAssign) and n.value is not None else [])
        if not any(isinstance(t, ast.Name) and t.id == want for t in targets):
            continue
        v = n.value
        if isinstance(v, ast.Call) and v.args and isinstance(v.args[0], ast.Constant) and isinstance(v.args[0].value, str):
            fn = v.func.attr if isinstance(v.func, ast.Attribute) else getattr(v.func, "id", "")
            if fn == "compile":
                return v.args[0].value
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            return v.value
    return None


def enrich(it: dict, cache: dict | None = None) -> dict:
    """同 v0119;來源是 .py 模組常數而 v0119 取不到時,用 AST 讀那個常數(只讀、不執行)。"""
    out = _ENRICH_V0119(it, cache)
    if out is it or out.get("pattern") or out.get("pattern_ref"):
        return out
    pp = py_path(str(out.get("source") or ""))
    if pp is None:
        return out
    cache = {} if cache is None else cache
    key = ("py", str(pp))
    if key not in cache:
        try:
            cache[key] = ast.parse(pp.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError, ValueError):
            cache[key] = None
    val = py_constant(cache[key], str(out.get("name") or "")) if cache[key] is not None else None
    if PRIOR._is_regex_v0119(val):
        out = dict(out, pattern=val)
    elif isinstance(val, str) and val.strip():
        out = dict(out, pattern_ref=val.strip()[:200])
    return out


PRIOR.enrich = enrich                                    # v0119 r22_items / load_state 以模組全域叫 enrich() → 走本版
BASE.load_state = load_state
BASE.synonym_items = synonym_items                       # v0100 collect() 以模組全域叫 synonym_items()


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(舊同義字列 scope · .py 常數正則 AST)===")
    C = PRIOR
    glo = {"kind": "SYN", "key": "glossary|MOMENTUM@v0100", "cat": "詞彙表(中英)", "words": ["動能", "MOMENTUM"], "sub": "VCGC", "lamp": "GREEN", "name": "動能"}
    cen = {"kind": "SYN", "key": "syn|x", "cat": "中央同義冊/rating", "words": ["BUY"], "sub": "VDF"}
    chk("① scope 規則:glossary|… → legacy.glossary · ins|… → legacy.ins · 分類 中央同義冊/ 的不動 · 已有 scope 的不動 · 候選列不動",
        legacy_syn_scope(glo) == "legacy.glossary" and legacy_syn_scope(dict(glo, key="ins|2330.TW@v0100")) == "legacy.ins"
        and legacy_syn_scope(cen) is None and legacy_syn_scope(dict(glo, scope="x")) is None and legacy_syn_scope(dict(glo, asset_intake=True)) is None)
    cand = {"candidate_id": "mom_alias", "ssot_code": None, "asset_type": "SYNONYM", "owner": "VQG", "source_id": "operator-proposal:t",
            "source_pointer": "mom_alias", "source_sha256": "a" * 64, "version": "1.0.0", "supersedes": None, "scope": "indicator.names",
            "semantic_key": "mom", "name": "MOM", "value": "VQG.IND.MOM", "risk_level": "MED", "environment": "via_core", "libraries": [],
            "aliases": ["MOM", "Momentum", "動能指標"], "positive": [], "negative": []}
    before = C.make_plan([cand], [], [glo])["results"][0]
    after = C.make_plan([cand], [], [dict(glo, scope=legacy_syn_scope(glo))])["results"][0]
    chk("② mom_alias:舊詞彙表列沒 scope → %s %s;補 scope 後 → %s(同字異域各自保留 %s)" % (before["state"], before["reasons"], after["state"], after.get("notes")),
        before["state"] == "REVIEW" and "LEGACY_ALIAS_SCOPE_UNKNOWN" in before["reasons"] and after["state"] == "READY"
        and "SAME_WORD_OTHER_SCOPE_RETAINED" in (after.get("notes") or []), (before, after))
    same = {"kind": "SYN", "key": "x|y", "sub": "VQG", "words": ["MOM"], "scope": "indicator.names", "name": "VQG.IND.OTHER", "lamp": "GREEN"}
    clash = C.make_plan([cand], [], [same])["results"][0]
    chk("③ 同 owner 同 scope 的舊列照比目標:目標不同 → 照樣擋(%s %s)—— 不是全面放行" % (clash["state"], clash["reasons"]),
        clash["state"] in ("REVIEW", "BLOCKED") and "LEGACY_ALIAS_CONFLICT" in clash["reasons"], clash)
    st = BASE.load_state()
    syn = [r for r in st["rows"].values() if r.get("kind") == "SYN" and not r.get("asset_intake")]
    unscoped = [r for r in syn if not r.get("scope") and not str(r.get("cat", "")).startswith(CENTRAL_SYN_PREFIX)]
    raw = json.loads((HERE / "VIA_Numbering_SSOT_v0100.json").read_text(encoding="utf-8")) if (HERE / "VIA_Numbering_SSOT_v0100.json").is_file() else {}
    raw_scoped = sum(1 for r in (raw.get("rows") or {}).get("SYN") or [] if "scope" in r and not r.get("asset_intake"))
    chk("④ 讀冊投影:真倉舊同義字 %d 列,沒 scope 又不在中央同義冊的剩 %d 列 · 存冊本身一字不動(舊同義字列有 scope 欄 %d;候選收件列本來就帶)" % (len(syn), len(unscoped), raw_scoped),
        syn and not unscoped and raw_scoped == 0 and BASE.load_state is load_state, len(unscoped))
    try:
        books = sorted(HERE.glob(C.BOOK_PATTERN), key=_vnum_v0120)
        assets = C.read_book(books[-1])["assets"] if books else []
        reg = list(st["rows"].values())
        legacy = [r for r in reg if not r.get("asset_intake") and r.get("kind") in ("SYN", "RGX")]
        res = {r["candidate_id"]: r for r in C.make_plan(assets, reg, legacy)["results"]}
        mom = res.get("mom_alias") or {}
        chk("⑤ 真候選冊(%s)× 真存冊:mom_alias → %s(manager 照這份計畫發號)" % (books[-1].name if books else "無", mom.get("state")),
            mom.get("state") in ("READY", "REGISTERED"), mom)
    except Exception as exc:  # noqa: BLE001
        chk("⑤ 真候選冊 × 真存冊", False, f"{type(exc).__name__}: {exc}")
    tree = ast.parse("import re\nclass DataValidator:\n    _TW_TICKER_RE = re.compile(r'^[1-9][0-9]{3}$')\nTW_TICKER_REGEX = r'^[0-9]{4}$'\nX = 1\n")
    chk("⑥ AST 取 .py 常數:類.名 → re.compile 字面 · 模組層字串 · 非字串 / 找不到 → None",
        py_constant(tree, "DataValidator._TW_TICKER_RE") == "^[1-9][0-9]{3}$" and py_constant(tree, "TW_TICKER_REGEX") == "^[0-9]{4}$"
        and py_constant(tree, "X") is None and py_constant(tree, "Nope.A") is None)
    allrx = [it for it in BASE.r22_items() if it.get("kind") == "RGX"]
    pys = [it for it in allrx if str(it.get("source", "")).endswith(".py")]
    got = [it for it in pys if it.get("pattern") or it.get("pattern_ref")]
    chk("⑦ 真倉 R22 舊正則來源是 .py 的 %d 列:取到原式 / 引用 %d 列(%s)" % (len(pys), len(got), [(x["name"], x.get("pattern") or x.get("pattern_ref")) for x in got][:3]),
        pys and len(got) == len(pys) and PRIOR.enrich is enrich, [(x.get("source"), x.get("name")) for x in pys if x not in got])
    items = BASE.synonym_items([])
    chk("⑧ 收集時同樣補:synonym_items 產出的舊同義字項都有 scope(或屬中央同義冊)· %d 項" % len(items),
        BASE.synonym_items is synonym_items and all(legacy_syn_scope(i) is None for i in items))
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑨ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 本檔不寫任何檔 · 不執行被讀的 .py(只 ast.parse)",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and ".write_text(" not in body and "open(" not in body and "exec_module(cache" not in body)
    rc_prior = 0
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        keep = (BASE.ENGINE, BASE.load_state, BASE.synonym_items, PRIOR.enrich)
        BASE.ENGINE, BASE.load_state, BASE.synonym_items, PRIOR.enrich = PRIOR.ENGINE, _LOAD_STATE_V0119, _SYN_ITEMS_ORIG_V0120, _ENRICH_V0119
        try:
            rc_prior = PRIOR.selftest()
        finally:
            BASE.ENGINE, BASE.load_state, BASE.synonym_items, PRIOR.enrich = keep
        chk("⑩ 前版鏈 v0119 → … 自測 rc 0;跑完 door 報本尾版、load_state / synonym_items / enrich 仍是本版",
            rc_prior == 0 and BASE.ENGINE == ENGINE and BASE.load_state is load_state and BASE.synonym_items is synonym_items and PRIOR.enrich is enrich,
            f"rc {rc_prior}")
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if rc_prior == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

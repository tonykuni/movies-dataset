#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0119 — 薄尾:R22 目錄帶進來的舊正則列(RGX)補 scope 與原式

操作員令(2026-11-01):「改 CGC_MDL237 補那 4 列,開 PR 並盯著」。
實錄(PR #579 收件後):VDF 兩條代號正則(VDF_InputUniverse_SSOT v0104 · 附正反例 · [0-9] 可證明)送中央檢測一律
REVIEW:LEGACY_REGEX_CONFLICT_OR_UNPROVEN。原因在中央自己的資料:v0114 make_plan 對「同 owner 的舊正則列」凡是
scope 為空就要證明不重疊,原式取 old['pattern'] 或退回 old['name'];而 r22_items()(R22 目錄 → RGX 列)只帶名字
(冊上路徑,如 verbs.vdf.verb.start.regex),沒有 scope、沒有原式 → 中央證明不了 → 該 owner 之後任何新正則都卡住。
VDF 這 4 列:VIA-VDF-RGX001 … 003(VIA_VDF_StartTestRegister_SSOT 三條動詞式)· RGX004(VIA_VDF_TWMarketEndpoints_SSOT ticker.rx)。
本版只加一格(v0100 … v0118 一字不動):r22_items() 產出的 RGX 項多帶
  scope        = "legacy." + 冊族(去版尾、小寫)+ "." + 冊上路徑(小寫)—— 正則的適用範圍就是它宣告所在的那一欄;
                 不同欄的新候選不再拿它比(v0114「不同 scope 各自成義」的既有規則),同一欄照比
  pattern      = 冊上那一欄的原式(鍵名本身帶點,逐層取最長相符鍵);值不是正則(例:「正本 TW_TICKER」這種引用)就不填 pattern,
                 改記 pattern_ref(照實,不假造原式)
讀冊時投影:load_state() 讀進來的 R22 舊正則列若沒有 scope,當場用同一規則補上(唯讀投影,不寫冊)——
  VCGC 不寫子系統正本,舊列的來源是 VDF 冊(衝突閘「子系統邊界」擋 --scope VDF 冊),所以存冊不改;
  manager plan / sync、CGC_MDL278 收件讀到的都是補過的列,號不變。之後該列真的在本批範圍時,assign 會照項寫回。
只收 VCGC 呼叫(經 via-vcgc run);零網路;不碰 TA-Lib;唯讀子系統的冊。
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

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL237_NumberingSystem"
SKIP_DIRS_V0119 = {".git", "node_modules", "__pycache__", "VIA_Reports", "VIA_RetiredEngines", "_superseded_redundant"}


def _vnum_v0119(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0119(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0119(p) < _vnum_v0119(__file__)), key=_vnum_v0119)
PRIOR = _load_v0119(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0118:IMMUT 豁免交接收據
BASE = PRIOR.BASE                                                       # v0100:collect() 以模組全域叫 r22_items()
BASE.ENGINE = ENGINE                                                    # door / SSOT engine 報實際尾版(同 v0117 ②)
_R22_ORIG_V0119 = BASE.r22_items
_BOOK_INDEX_V0119: dict = {}


def _sanitize_v0119(s: str) -> str:
    return re.sub(r"[^a-z0-9_.:-]+", "_", str(s).lower()).strip("._") or "x"


def legacy_scope(source: str, name: str) -> str:
    """舊正則列的適用範圍 = 它宣告所在的冊族 + 冊上路徑(v0114 scope 字集 [a-z0-9_.:-])。"""
    fam = re.sub(r"_v\d{3,4}$", "", Path(str(source)).stem)
    return "legacy.%s.%s" % (_sanitize_v0119(fam), _sanitize_v0119(name))


def book_path(source: str) -> Path | None:
    """R22 目錄的 source 是檔名(不帶夾):先找本夾(registry),再一次性索引 VIA 樹的 *.json(略過報表 / 退役夾)。"""
    name = Path(str(source)).name
    if not name.endswith(".json"):
        return None
    if (HERE / name).is_file():
        return HERE / name
    if not _BOOK_INDEX_V0119:
        for root, dirs, files in os.walk(BASE.VIA):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS_V0119]
            for f in files:
                if f.endswith(".json"):
                    _BOOK_INDEX_V0119.setdefault(f, Path(root) / f)
        _BOOK_INDEX_V0119.setdefault("\0built", Path("."))
    return _BOOK_INDEX_V0119.get(name)


def resolve_path(obj, path: str):
    """冊上路徑取值;鍵名本身可能帶點(verbs → vdf.verb.start → regex),每層取最長相符鍵;
    陣列索引照 R22 目錄的寫法 `name[1].pattern` / `a[0][2].rx`(也收 `a.1.rx`);取不到回 None。"""
    if path == "":
        return obj
    if isinstance(obj, list):
        m = re.match(r"^\[(\d+)\]\.?(.*)$", path) or re.match(r"^(\d+)(?:\.(.*))?$", path)
        if m and int(m.group(1)) < len(obj):
            return resolve_path(obj[int(m.group(1))], m.group(2) or "")
        return None
    if isinstance(obj, dict):
        for k in sorted((str(x) for x in obj), key=len, reverse=True):
            if path == k:
                return obj[k]
            for sep in (".", "["):
                if path.startswith(k + sep):
                    hit = resolve_path(obj[k], path[len(k) + 1:] if sep == "." else path[len(k):])
                    if hit is not None:
                        return hit
        return None
    return None


def _is_regex_v0119(v) -> bool:
    if not isinstance(v, str) or not v.strip():
        return False
    if not (v.startswith("^") or v.endswith("$") or re.search(r"\\[dDwWsSb]|\[[^\]]+\]|\(\?|[*+?{|]", v)):
        return False
    try:
        re.compile(v)
        return True
    except re.error:
        return False


def enrich(it: dict, cache: dict | None = None) -> dict:
    """R22 的 RGX 項補 scope + pattern(或 pattern_ref);其他項原樣。"""
    if it.get("kind") != "RGX" or not str(it.get("key") or "").startswith("r22|"):
        return it
    src, name = str(it.get("source") or ""), str(it.get("name") or "")
    out = dict(it, scope=legacy_scope(src, name))
    cache = {} if cache is None else cache
    bp = book_path(src)
    if bp is not None:
        if bp not in cache:
            try:
                cache[bp] = json.loads(bp.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                cache[bp] = None                          # 冊讀不到:scope 照補,原式不填(照實)
        val = resolve_path(cache[bp], name) if cache[bp] is not None else None
        if _is_regex_v0119(val):
            out["pattern"] = val
        elif isinstance(val, str) and val.strip():
            out["pattern_ref"] = val.strip()[:200]
    return out


def r22_items() -> list:
    cache = {}
    return [enrich(it, cache) for it in _R22_ORIG_V0119()]


BASE.r22_items = r22_items                               # v0100 collect() 以模組全域叫 r22_items() → 走本版
_LOAD_STATE_ORIG_V0119 = BASE.load_state


def load_state() -> dict:
    """同 v0100,讀進來的 R22 舊正則列沒有 scope 就當場補(唯讀投影;存冊一字不動)。"""
    st = _LOAD_STATE_ORIG_V0119()
    rows, cache = st.get("rows") or {}, {}
    for k, r in list(rows.items()):
        if r.get("kind") == "RGX" and str(r.get("key") or "").startswith("r22|") and not r.get("scope"):
            rows[k] = enrich(r, cache)
    return st


BASE.load_state = load_state                             # manager snapshot · make_plan 的 registered / legacy · CGC_MDL278 都讀這支


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)                             # v0117 的動詞 / 旗標守門照舊


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(R22 舊正則列補 scope 與原式 · 讀冊投影)===")
    verb = {"kind": "RGX", "key": "r22|RX-0064", "name": "verbs.vdf.verb.start.regex", "source": "VIA_VDF_StartTestRegister_SSOT_v0100.json", "sub": "VDF"}
    tick = {"kind": "RGX", "key": "r22|RX-0067", "name": "daily_universe.columns.ticker.rx", "source": "VIA_VDF_TWMarketEndpoints_SSOT_v0100.json", "sub": "VDF"}
    other = {"kind": "PRMT", "key": "r22|PA-0001", "name": "x", "source": "VIA_VDF_StartTestRegister_SSOT_v0100.json"}
    ev, et, eo = enrich(verb), enrich(tick), enrich(other)
    chk("① 動詞式:scope = 冊族 + 冊上路徑 · 原式從冊上取(鍵帶點也取得到)· %s · %s" % (ev.get("scope"), ev.get("pattern")),
        ev.get("scope") == "legacy.via_vdf_starttestregister_ssot.verbs.vdf.verb.start.regex" and ev.get("pattern") == "^(start|啟動|via-vdf-start)$")
    chk("② 冊上那一欄是引用不是正則(「正本 TW_TICKER」)→ 只記 pattern_ref,不假造 pattern · %s" % et.get("pattern_ref"),
        et.get("scope", "").startswith("legacy.via_vdf_twmarketendpoints_ssot.") and "pattern" not in et and et.get("pattern_ref") == "正本 TW_TICKER")
    chk("③ 非 RGX / 非 R22 的項原樣不動", eo is other and enrich(dict(verb, key="rx|x")) == dict(verb, key="rx|x"))
    doc = {"locked_alignment": [{"pattern": "^A$"}, {"pattern": "^B[0-9]$"}], "g": {"a.b": [[{"rx": "^X$"}], [{"rx": "^Y$"}]]}}
    got = [resolve_path(doc, x) for x in ("locked_alignment[1].pattern", "locked_alignment.0.pattern", "g.a.b[1][0].rx", "locked_alignment[9].pattern")]
    chk("③b 陣列索引:name[1].pattern · name.0.pattern · 帶點鍵 + 多層索引 a.b[1][0].rx 都取得到;越界回 None · %s" % got,
        got == ["^B[0-9]$", "^A$", "^Y$", None])
    C = PRIOR
    cand = {"candidate_id": "VDF:RGX:IN-01", "ssot_code": None, "asset_type": "REGEX", "owner": "VDF", "source_id": "vdf-ssotsync:t",
            "source_pointer": "VDF:RGX:IN-01", "source_sha256": "a" * 64, "version": "1.0.0", "supersedes": None,
            "scope": "vdf.regex.vdf_inputuniverse_ssot.code_regex", "semantic_key": "IN-01", "name": "t", "value": "^[1-9][0-9]{3}$",
            "risk_level": "MED", "environment": "via_core", "libraries": [], "aliases": [], "positive": ["2330"], "negative": ["0050"]}
    try:
        before = C.make_plan([cand], [], [verb, tick])["results"][0]
        after = C.make_plan([cand], [], [ev, et])["results"][0]
        same_scope = dict(enrich(dict(verb, name="code_regex")), pattern="^[0-9]{4}$", semantic_key="OLD")
        clash = C.make_plan([dict(cand, scope=same_scope["scope"])], [], [same_scope])["results"][0]
        chk("④ 中央檢測:舊列沒 scope → %s %s;補 scope 後 → %s(不同欄的新正則不再拿它比)" % (before["state"], before["reasons"], after["state"]),
            before["state"] == "REVIEW" and "LEGACY_REGEX_CONFLICT_OR_UNPROVEN" in before["reasons"] and after["state"] == "READY", (before, after))
        chk("⑤ 同一欄照比:同 scope · 原式重疊 · 語意鍵不同 → 照樣擋(%s %s)—— 不是全面放行" % (clash["state"], clash["reasons"]),
            clash["state"] in ("REVIEW", "BLOCKED") and "LEGACY_REGEX_CONFLICT_OR_UNPROVEN" in clash["reasons"], clash)
    except Exception as exc:                                   # make_plan 的正例實測要 duckdb;本境缺就照實記不過
        chk("④ 中央檢測補 scope 前後", False, f"{type(exc).__name__}: {exc}")
        chk("⑤ 同一欄照比", False, "同上")
    real = [it for it in BASE.r22_items() if it.get("kind") == "RGX" and it.get("sub") == "VDF"
            and it.get("source") in ("VIA_VDF_StartTestRegister_SSOT_v0100.json", "VIA_VDF_TWMarketEndpoints_SSOT_v0100.json")]
    chk("⑥ 換裝在位:v0100 collect 叫的 r22_items = 本版 · 真倉 VDF 那 4 列都有 scope(%d 列 · 原式 %d · 引用 %d)"
        % (len(real), sum(1 for x in real if x.get("pattern")), sum(1 for x in real if x.get("pattern_ref"))),
        BASE.r22_items is r22_items and len(real) == 4 and all(x.get("scope") for x in real) and sum(1 for x in real if x.get("pattern")) == 3)
    allrx = [it for it in BASE.r22_items() if it.get("kind") == "RGX"]
    br = [it for it in allrx if "[" in str(it.get("name"))]
    chk("⑥a 真倉 R22 正則 %d 列:帶陣列索引的 %d 列取到原式 / 引用 %d 列(只有冊讀不到或那一欄不在才缺)"
        % (len(allrx), len(br), sum(1 for x in br if x.get("pattern") or x.get("pattern_ref"))),
        br and sum(1 for x in br if x.get("pattern") or x.get("pattern_ref")) >= 0.9 * len(br),
        [(x.get("source"), x.get("name")) for x in br if not (x.get("pattern") or x.get("pattern_ref"))][:5])
    st = BASE.load_state()
    vdf4 = {r.get("code"): r for r in st["rows"].values() if r.get("code") in ("VIA-VDF-RGX001", "VIA-VDF-RGX002", "VIA-VDF-RGX003", "VIA-VDF-RGX004")}
    raw = json.loads((HERE / "VIA_Numbering_SSOT_v0100.json").read_text(encoding="utf-8")) if (HERE / "VIA_Numbering_SSOT_v0100.json").is_file() else {}
    raw4 = [r for r in (raw.get("rows") or {}).get("RGX") or [] if r.get("code") in vdf4]
    chk("⑥b 讀冊投影:存冊那 4 列(VIA-VDF-RGX001 … 004)讀進來都有 scope · 號不變 · 存冊本身一字不動(沒有 scope 欄)",
        len(vdf4) == 4 and all(r.get("scope") for r in vdf4.values()) and BASE.load_state is load_state
        and len(raw4) == 4 and not any("scope" in r for r in raw4), {c: r.get("scope") for c, r in vdf4.items()})
    try:
        books = sorted(HERE.glob(C.BOOK_PATTERN), key=_vnum_v0119)
        assets = C.read_book(books[-1])["assets"] if books else []
        rx = [a for a in assets if a.get("owner") == "VDF" and a.get("asset_type") == "REGEX" and str(a.get("source_id", "")).endswith("SSOT_Register")]
        reg = list(st["rows"].values())
        legacy = [r for r in reg if not r.get("asset_intake") and r.get("kind") in ("SYN", "RGX")]
        res = C.make_plan(assets, reg, legacy)["results"]
        mine = [r for a, r in zip(assets, res) if a in rx]
        chk("⑥c 真候選冊(%s)× 真存冊:VDF 兩條代號正則 → %s(manager 照這份計畫發號)"
            % (books[-1].name if books else "無", [r["state"] for r in mine]),
            len(mine) == 2 and all(r["state"] in ("READY", "REGISTERED") for r in mine), mine)
    except Exception as exc:
        chk("⑥c 真候選冊 × 真存冊", False, f"{type(exc).__name__}: {exc}")
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 本檔不寫任何檔(寫冊只走前版的 --apply)",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and ".write_text(" not in body and "open(" not in body)
    rc_prior = 0
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        keep = (BASE.ENGINE, BASE.r22_items, BASE.load_state)
        BASE.ENGINE, BASE.r22_items, BASE.load_state = PRIOR.ENGINE, _R22_ORIG_V0119, _LOAD_STATE_ORIG_V0119   # 前版鏈驗它自己那一版
        try:
            rc_prior = PRIOR.selftest()
        finally:
            BASE.ENGINE, BASE.r22_items, BASE.load_state = keep
        chk("⑧ 前版鏈 v0118 → … 自測 rc 0;跑完 door 報本尾版、r22_items / load_state 仍是本版",
            rc_prior == 0 and BASE.ENGINE == ENGINE and BASE.r22_items is r22_items and BASE.load_state is load_state, f"rc {rc_prior}")
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if rc_prior == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

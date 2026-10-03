# -*- coding: utf-8 -*-
r"""VRN_TW02_ReportParser v0102 — 薄尾:評等 / 目標價詞表改**委由樞紐**(SUP_MDL749_VRNFieldRuleHub),不再自己寫死一份
(SSOT 全景 SYN@VRN 下游落差 2 支之一:v0101 評等 34/66 · 目標價 10/16 · 「沒載收容件字典(自己寫死一份)」)。
做法:載入前版後,把樞紐三源聯集的 raw 詞**只增**進 RATING_SYNONYMS / TARGET_PRICE_SYNONYMS,重編兩個 PATTERN;前版列一個不刪、順序不動。
R-SYN-04:細桶(STRONG_BUY / STRONG_SELL / ACCUMULATE / ADD)映到粗桶,強度另記 RATING_STRENGTH(給 rating_strength 欄位)。
+ --selftest(前版沒有;編號引擎契約)。其餘一字照前版。
"""
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
import importlib.util, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VRN_TW02_ReportParser"
ENGINE = STEM + "_v0102"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


# ---- 樞紐委派(SUP_MDL749_VRNFieldRuleHub;L109 ④ · R-SYN-04:同義字只映粗正典,強度另立 rating_strength)----
import importlib.util as _ilu, re as _re, sys as _sys, os as _os
from pathlib import Path as _P

def _via_root() -> _P:
    p = _P(__file__).resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir():
            return p
        p = p.parent
    return _P(__file__).resolve().parent

def _hub():
    """載最新 SUP_MDL749_VRNFieldRuleHub 尾版;缺席回 None(誠實,不假綠)。"""
    d = _via_root() / "supportive modules" / "70_VRN_Rules"
    cands = sorted(d.glob("SUP_MDL749_VRNFieldRuleHub_v*.py"), key=lambda q: int(_re.search(r"_v(\d+)$", q.stem).group(1)))
    if not cands:
        return None
    key = "via_hub749_for_" + _P(__file__).stem
    if key in _sys.modules:
        return _sys.modules[key]
    spec = _ilu.spec_from_file_location(key, cands[-1]); mod = _ilu.module_from_spec(spec); _sys.modules[key] = mod; spec.loader.exec_module(mod)
    return mod

# 粗正典映射(R-SYN-04):細桶 → 粗桶;強度桶記錄在 RATING_STRENGTH
COARSE = {"BUY": "BUY", "STRONG_BUY": "BUY", "OUTPERFORM": "BUY", "OVERWEIGHT": "BUY", "ACCUMULATE": "BUY", "ADD": "ADD",
          "HOLD": "HOLD", "NEUTRAL": "HOLD", "MARKET_PERFORM": "HOLD", "EQUAL_WEIGHT": "HOLD",
          "SELL": "SELL", "STRONG_SELL": "SELL", "REDUCE": "SELL", "UNDERPERFORM": "SELL", "UNDERWEIGHT": "SELL",
          "NOT_RATED": "NOT_RATED", "NR": "NOT_RATED", "RATING_NOT_RATED": "NOT_RATED"}
STRENGTH = {"STRONG_BUY": "strong", "STRONG_SELL": "strong", "ACCUMULATE": "accumulate", "ADD": "accumulate"}
RATING_STRENGTH: dict = {}      # raw 詞 → 強度(給下游 rating_strength 欄位;不是第二個正典)
HUB_UNKNOWN_BUCKETS: set = set()

def hub_rating_words(targets: tuple) -> dict:
    """三源聯集 → {粗桶: [raw 詞…]};只回 targets 裡有的桶。缺樞紐回空 dict。"""
    mod = _hub()
    out = {k: [] for k in targets}
    if mod is None or not hasattr(mod, "load_sources"):
        return out
    try:
        srcs = mod.load_sources()
    except Exception:
        return out
    seen = {k: set() for k in targets}
    for s in srcs.values():
        for word, info in (s.get("rating") or {}).items():
            raws = list(info.get("raw") or [word]) if isinstance(info, dict) else [word]
            buckets = list(info.get("buckets") or []) if isinstance(info, dict) else []
            for b in buckets:
                bu = str(b).upper(); c = COARSE.get(bu)
                if c is None:
                    HUB_UNKNOWN_BUCKETS.add(bu); continue
                if c == "ADD" and "ADD" not in targets:
                    c = "BUY"
                if c not in targets:
                    continue
                for r in raws:
                    if bu in STRENGTH:
                        RATING_STRENGTH[str(r)] = STRENGTH[bu]
                    if str(r).lower() not in seen[c]:
                        seen[c].add(str(r).lower()); out[c].append(str(r))
    return out

def hub_tp_words() -> list:
    mod = _hub(); out, seen = [], set()
    if mod is None or not hasattr(mod, "load_sources"):
        return out
    try:
        srcs = mod.load_sources()
    except Exception:
        return out
    for s in srcs.values():
        for _k, info in (s.get("tp") or {}).items():
            for r in (info.get("raw") or []) if isinstance(info, dict) else []:
                if str(r).lower() not in seen:
                    seen.add(str(r).lower()); out.append(str(r))
    return out


def _apply() -> dict:
    """只增:把樞紐詞併進前版表,重編 PATTERN。回報每桶新增數。"""
    added = {}
    words = hub_rating_words(tuple(PRIOR.RATING_SYNONYMS.keys()))
    for bucket, lst in PRIOR.RATING_SYNONYMS.items():
        have = {w.lower() for w in lst}; n = 0
        for w in words.get(bucket, []):
            if w.lower() not in have:
                lst.append(w); have.add(w.lower()); n += 1
        added[bucket] = n
    tp_have = {w.lower() for w in PRIOR.TARGET_PRICE_SYNONYMS}; n = 0
    for w in hub_tp_words():
        if w.lower() not in tp_have:
            PRIOR.TARGET_PRICE_SYNONYMS.append(w); tp_have.add(w.lower()); n += 1
    added["TARGET_PRICE"] = n
    PRIOR.RATING_PATTERN = re.compile(r"\b(" + "|".join(re.escape(s) for syns in PRIOR.RATING_SYNONYMS.values() for s in syns) + r")\b", re.IGNORECASE)
    PRIOR.TARGET_PRICE_PATTERN = re.compile(r"(?:" + "|".join(re.escape(s) for s in PRIOR.TARGET_PRICE_SYNONYMS) + r")[\s:：]*" + r"(?:NT\$|TWD|NTD)?[\s]*([\d,]+(?:\.\d+)?)\s*(?:元|TWD)?", re.IGNORECASE)
    return added


ADDED = _apply()
RATING_SYNONYMS = PRIOR.RATING_SYNONYMS
TARGET_PRICE_SYNONYMS = PRIOR.TARGET_PRICE_SYNONYMS
RATING_PATTERN = PRIOR.RATING_PATTERN
TARGET_PRICE_PATTERN = PRIOR.TARGET_PRICE_PATTERN


def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    total = sum(len(v) for v in RATING_SYNONYMS.values())
    chk("① 樞紐在,三源聯集併入(評等 ≥ 60 詞)", _hub() is not None and total >= 60, f"評等 {total} · 新增 {ADDED}")
    chk("② 前版詞一個不少(只增)", all(w in RATING_SYNONYMS["BUY"] for w in ("買進", "Strong Buy")) and "目標價" in TARGET_PRICE_SYNONYMS)
    r = PRIOR.PageParser.parse_first_page("評等:強力買進 目標價 NT$ 1,200 元")
    chk("③ 第一頁解析走新表:強力買進 → BUY · 目標價 1200", r.get("rating") == "BUY" and str(r.get("target_price")) == "1200", str({k: r.get(k) for k in ("rating", "target_price")}))
    chk("④ 強度另記不當第二正典:強力買進 → rating_strength strong", RATING_STRENGTH.get("強力買進") == "strong" or RATING_STRENGTH.get("Strong Buy") == "strong")
    chk("⑤ 本土尺度詞進表(優於大盤 → BUY · 劣於大盤 → SELL)", any("優於大盤" == w for w in RATING_SYNONYMS["BUY"]) and any("劣於大盤" == w for w in RATING_SYNONYMS["SELL"]), f"未知桶 {sorted(HUB_UNKNOWN_BUCKETS)}")
    chk("⑥ 委樞印記在本檔(HUB_MARK)· 加速器橋在", "SUP_MDL749_VRNFieldRuleHub" in Path(__file__).read_text(encoding="utf-8") and "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        raise SystemExit(selftest())
    PRIOR.self_test()

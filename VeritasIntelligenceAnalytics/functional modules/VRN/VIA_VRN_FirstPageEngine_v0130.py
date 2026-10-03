# -*- coding: utf-8 -*-
r"""VIA_VRN_FirstPageEngine v0130 — 薄尾:BrokerRatingDict.RATING 改**委由樞紐**(SUP_MDL749_VRNFieldRuleHub)只增補齊
(SSOT 全景 SYN@VRN 下游落差 2 支之一:v0129 評等 41/66 · 目標價 11/16;本土尺度缺 13 · 收容冊缺 14)。
做法:載入前版後,把樞紐三源聯集 raw 詞只增進 BrokerRatingDict.RATING 的五桶(BUY / HOLD / SELL / ADD / NOT_RATED);前版詞不動。
R-SYN-04:STRONG_* 映粗桶、強度另記 RATING_STRENGTH。main / selftest / 其餘一字照前版(前版自測照跑,本版再加三檢)。
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
STEM = "VIA_VRN_FirstPageEngine"
ENGINE = STEM + "_v0130"


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
    R = PRIOR.BrokerRatingDict.RATING
    words = hub_rating_words(tuple(R.keys()))
    added = {}
    for bucket, lst in R.items():
        have = {w.lower() for w in lst}; n = 0
        for w in words.get(bucket, []):
            if w.lower() not in have:
                lst.append(w); have.add(w.lower()); n += 1
        added[bucket] = n
    return added


ADDED = _apply()


def selftest() -> int:
    rc_prior = PRIOR.selftest()
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    R = PRIOR.BrokerRatingDict.RATING; total = sum(len(v) for v in R.values())
    chk("① 樞紐三源聯集併入 RATING(≥ 60 詞)", _hub() is not None and total >= 60, f"{total} · 新增 {ADDED}")
    chk("② 前版詞一個不少 · 本土尺度進表(優於大盤 → BUY)", "逢低加碼" in R["BUY"] and "優於大盤" in R["BUY"], f"未知桶 {sorted(HUB_UNKNOWN_BUCKETS)}")
    chk("③ 委樞印記 · 加速器橋在本檔", all(m in Path(__file__).read_text(encoding="utf-8") for m in ("SUP_MDL749_VRNFieldRuleHub", "VIA:ACCEL-BRIDGE")))
    print(f"  [計] {ENGINE} 薄尾 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc_prior == 0 else 'rc=' + str(rc_prior)} · 合計 {'PASS' if all(ok) and rc_prior == 0 else 'FAIL'}")
    return 0 if all(ok) and rc_prior == 0 else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())

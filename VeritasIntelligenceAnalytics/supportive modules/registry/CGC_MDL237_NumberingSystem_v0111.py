#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL237_NumberingSystem v0111 — 薄尾:同義冊「一詞兩主」依裁定歸位(別名列保號轉綠 · 評等粗細兩軸不算兩主)(R34 重號)
操作員(R34,2026-09-30):「重號問題授權你可改 依據可用測試樣本如果跟他有關」。
實錄:v0110 稽核「冊內不一致 1 · 紅列 21」,其中 15 列是 SYN 的「一詞兩主(待裁定 key_alias)」:
  ① 券商(13 列):同一家在不同冊用兩三種正典鍵拼法(BAML/BOFA/ML · CITI/CITIGROUP · FCB/FIRST/FIRSTSEC · HNSC/HUANAN ·
     MORGAN STANLEY/MORGANSTANLEY/MS)。樣本索引 StockReportBasicInfo.json 的 Morgan Stanley 13 份 · Citi 2 份就解不成一個主。
     裁定在同義冊正主 CGC_MDL176 v0103(KEY_ALIAS_RULINGS +8,正典鍵 = institution 冊)。本版:
     正典鍵那一列照前版(把別名的詞併進來、不再判兩主);**別名鍵那一列也照發(同一個鍵 · 同一個號 · 身分不變)**,
     燈轉 GREEN,註記「別名 → 正典鍵」——號不改、不刪、不併號(只增律)。
  ② 評等(2 列):「強力賣出 / 強烈賣出 / 避免 / avoid → SELL / STRONG_SELL」是同一條粗細軸(冊政策:評等記最細的鍵,
     粗尺由 coarse_of 當場投影),不是兩主:一個詞同時掛著細鍵與它的粗投影時,只記細鍵。真的兩主(兩個互不為粗細的鍵)照舊紅。
其餘照 v0110(只登本批 · 真基準 · 寫後自核)。VIA_FROM_VCGC:只收 VCGC 呼叫。零網路。不用 TA-Lib。
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

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum,
                 default=HERE / "CGC_MDL237_NumberingSystem_v0110.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                    # v0100 本體:collect() 在這裡解 synonym_items
_V0100_SYNONYM_ITEMS = BASE.synonym_items
VRN_SCOPES = ("broker", "rating", "rating_label", "target_price", "valuation_method")


def __getattr__(name: str):
    return getattr(PRIOR, name)


def owners_canon(owners: list, ka: dict, coarse: dict, scope: str) -> list:
    """The canonical keys a word belongs to: key_alias folded to the canonical key; in rating, a coarse projection of a finer
    key the same word already has is dropped (the book records the finest key)."""
    canon = sorted({ka.get(str(o.get("canonical")).upper()) or o.get("canonical") for o in owners
                    if isinstance(o, dict) and o.get("canonical") and o.get("inclusion") != "DENIED"})
    if scope == "rating" and coarse:
        canon = [c for c in canon if not any(f != c and coarse.get(f) == c for f in canon)]
    return canon


def synonym_items(extra: list) -> list:
    """v0100's synonym rows with the two R34 rulings: alias keys keep their own row (same key, same code) turned GREEN as an
    alias of the canonical key; rating fine/coarse pairs are one axis, not two owners."""
    out = []
    su = BASE._newest(BASE.HERE, "VIA_SSOT_SynonymUnion_v*.json")
    book = BASE._json(su) or {}
    rel = BASE._rel(su) if su else ""
    ver = "v" + str(book.get("version") or "0100")
    ka_full = {k.upper(): v for k, v in (book.get("key_alias") or {}).items() if isinstance(v, dict)}
    ka = {k: v.get("canonical") for k, v in ka_full.items()}
    coarse = book.get("coarse_of") or {}
    for scope, table in (book.get("scopes") or {}).items():
        groups, owners_of, alias_words = {}, {}, {}
        sub = "VRN" if scope in VRN_SCOPES else "VCGC"
        for raw, owners in (table or {}).items():
            canon = owners_canon(owners or [], ka, coarse, scope)
            owners_of[raw] = canon
            for c in canon:
                groups.setdefault(c, {c}).add(raw)
            for o in owners or []:
                key = str((o or {}).get("canonical") or "").upper() if isinstance(o, dict) else ""
                if key in ka and (o or {}).get("inclusion") != "DENIED":
                    alias_words.setdefault(str(o.get("canonical")), {str(o.get("canonical"))}).add(raw)
        for canon, words in sorted(groups.items()):
            words = sorted(words, key=lambda w: (not BASE._cjk(w), w))
            clash = [w for w in words if len([c for c in owners_of.get(w, []) if len(c) > 3]) > 1]
            short = [w for w in words if len(owners_of.get(w, [])) > 1 and w not in clash]
            lamp = "RED" if clash else "AMBER" if short else "GREEN"
            note = (("一詞兩主(待裁定 key_alias):" + ", ".join(f"{w}→{'/'.join(owners_of[w])}" for w in clash[:4])) if clash else
                    ("短碼待併:" + ", ".join(f"{w}→{'/'.join(owners_of[w])}" for w in short[:4])) if short else
                    " ≡ ".join(words))
            out.append(BASE.item("SYN", f"union|{scope}|{canon}", canon, "中央同義冊/" + scope, rel, "scopes." + scope, BASE.updated(rel),
                                 sub, ver, lamp, note[:120], words=words))
        for alias, words in sorted(alias_words.items()):
            target = ka.get(alias.upper())
            if not target or target not in groups:
                continue
            words = sorted(words, key=lambda w: (not BASE._cjk(w), w))
            note = f"別名 → {target}(key_alias 裁定;號不改、不併號)· " + " ≡ ".join(words)
            out.append(BASE.item("SYN", f"union|{scope}|{alias}", alias, "中央同義冊/" + scope, rel, "scopes." + scope, BASE.updated(rel),
                                 sub, ver, "GREEN", note[:120], words=words, alias_of=target))
    for key, words, cat, src, lamp in extra:
        words = [str(w) for w in dict.fromkeys(w for w in words if w)]
        out.append(BASE.item("SYN", key, words[0] if words else key, cat, src, "—",
                             BASE.updated(src) if "/" in str(src) else BASE.updated(BASE._rel(Path(BASE.__file__))),
                             BASE.subsystem_of(src), None, lamp, " ≡ ".join(words)[:120], words=words))
    return out


BASE.synonym_items = synonym_items


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    import contextlib
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = PRIOR.selftest()
    chk("前版 v0110(含本體鏈)自測", prc == 0, (buf.getvalue().strip().splitlines() or [""])[-1])
    ka = {"BAML": "BOFA", "ML": "BOFA"}
    coarse = {"STRONG_SELL": "SELL", "SELL": "SELL", "STRONG_BUY": "BUY", "BUY": "BUY", "HOLD": "HOLD"}
    o = lambda c, inc="BASELINE": {"canonical": c, "inclusion": inc}   # noqa: E731
    chk("別名折到正典鍵:美林 → BAML/BOFA/ML 只剩 BOFA", owners_canon([o("BAML"), o("BOFA"), o("ML")], ka, coarse, "broker") == ["BOFA"])
    chk("評等粗細同軸:強力賣出 → SELL/STRONG_SELL 只記 STRONG_SELL", owners_canon([o("SELL"), o("STRONG_SELL")], ka, coarse, "rating") == ["STRONG_SELL"])
    chk("真兩主照舊兩主:BUY 與 SELL 互不為粗細", owners_canon([o("BUY"), o("SELL")], ka, coarse, "rating") == ["BUY", "SELL"])
    chk("DENIED 不算擁有", owners_canon([o("BOFA"), o("CITI", "DENIED")], ka, coarse, "broker") == ["BOFA"])
    rows = synonym_items([])
    by = {r["key"].split("@")[0] if "@" in r["key"] else r["key"]: r for r in rows}
    reds = [r for r in rows if r.get("lamp") == "RED"]
    # 授權範圍 = 「依據可用測試樣本如果跟他有關」:樣本索引券商(與 MDL176 v0103 已裁的別名)涉及的紅列必須歸零;
    # 樣本沒有的券商(麥格理 · 元富)不代裁,照實列成待裁定。
    sample_keys = {"MS", "MORGAN STANLEY", "MORGANSTANLEY", "CITI", "CITIGROUP", "GS", "JPM", "J.P. MORGAN", "JPMORGAN",
                   "DAIWA", "DAIWA SECURITIES", "KGI", "UBS", "CATHAY", "CTBC", "BOFA", "BAML", "ML",
                   "FIRST", "FCB", "FIRSTSEC", "HUANAN", "HNSC"}
    hit = [r for r in reds if str(r.get("name")) in sample_keys]
    chk("實冊:樣本相關的一詞兩主紅列歸零", not hit, " · ".join(str(r.get("name")) for r in hit[:6]))
    if reds:
        print("  [待裁定] 樣本沒有、不代裁(照實留紅):" + " · ".join(str(r.get("name")) for r in reds))
    alias_rows = [r for r in rows if r.get("alias_of")]
    chk("實冊:別名鍵各自保一列(同鍵 · 轉綠 · 指向正典)", {r["name"]: r["alias_of"] for r in alias_rows if r["name"] in ("BAML", "ML", "MORGAN STANLEY", "CITIGROUP")}
        == {"BAML": "BOFA", "ML": "BOFA", "MORGAN STANLEY": "MS", "CITIGROUP": "CITI"}, [r["name"] for r in alias_rows])
    keys = [r["key"] for r in rows]
    chk("實冊:鍵不重複(一鍵一列)", len(keys) == len(set(keys)))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print(f"[編號 v0111 重號歸位] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())

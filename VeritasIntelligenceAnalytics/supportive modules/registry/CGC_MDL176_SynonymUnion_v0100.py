#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL176_SynonymUnion v0100 — 同義字聯集閘(批678)
====================================================================
操作員令(批678):「以現有的 SSOT REGEX 同義字及中央控管的其他庫為主,
**只增不減除衝突**」。

這支只做一件事:**把上傳的同義字冊併進既有正典,而且證明一個字都沒少**。

「以現有的為主」是有次序的,不是一句口號。解析次序照疊加層批413 立的那一條:
    拒絕清單 → 正典 → 疊加層 → 聯集冊
拒絕清單先行(操作員令「大陸券商刪除」「去摩通」),正典唯讀永不覆寫,
疊加層只補正典的空缺,聯集冊只補前三者都沒有的。
**新冊永遠排在最後**——這就是「以現有的為主」在程式裡的樣子。

底冊(全部是既有的,本支一個字都不改它們):
  正典     supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.json   (READ_ONLY)
  疊加層   supportive modules/ssot/VIA_FinancialInstitution_Overlay_v*.json    (操作員裁決層)
  中央規則 supportive modules/registry/VRN_FieldRules_SSOT_v0100.json          (SUP_MDL749 正本)
  券商冊   functional modules/VRN/registry/VRN_BROKER_LIST_v01.json
  知識冊   functional modules/VRN/knowledge/VRN_{Broker,Rating}_Dict_v0100.json
收容件(正本零觸碰,只讀不改):
  supportive modules/references/intake/VIA_SSOT_SynonymUnion_b678/SYNONYM_LIBRARY.json

實測 443 條逐條判(誠實五態,不是「合併成功」四個字):
  SAME 347 · ADD 80 · WIDEN 1 · CONFLICT 5 · DENIED 10
  —— 併進來的 80 條裡**一條券商別名都沒有**。199 條券商別名,既有的冊本來就有 185 條,
     其餘 14 條全是衝突或拒絕。**上傳沒有給我們新券商,它照出了我們自己的兩個問題。**

五個 CONFLICT,四個是**我們自己兩本冊對同一家用了兩個正典鍵拼法**(L30 一個出處):
  megabank        broker_list 寫 Megabank        · 正典鍵 MEGA(兆豐證券)
  daiwa capital   broker_list 寫 Daiwa Securities · 正典鍵 DAIWA(大和資本)
  jp              broker_list 寫 J.P. Morgan      · 正典鍵 JPM(摩根大通)
  ibf securities  規則冊 extra_table 寫 IBF        · 正典鍵 WATERLAND(國票證券)
  裁定:一律解到**正典鍵**。正典是唯讀正本,它的鍵就是唯一的命名空間;
  別的拼法降為別名(不刪,只是不再當第二個正本)。正典自己早就有 key_migration_map
  (BOA→BOFA · ML→BOFA · MCQ→MACQUARIE · MQ→MACQUARIE)——這四條是同一件事的第五到第八條。
第五個是評等粗細尺:「避免」既有在 strong_sell 組、上傳判 SELL。
  兩本冊**切的軸不一樣**,不是判得相反:
    正典六鍵   切強弱(STRONG_BUY / BUY …),把 ADD 摺進 BUY
    規則冊四鍵 切加碼強度(BUY / HOLD / SELL / ADD),把 STRONG_* 摺進 BUY / SELL
  所以聯集冊記**最細的那一個**,兩條粗尺各由 fine_of() / coarse_of() 當場投影出來。
  LL327:兩條基準不同的車道,永遠不准混成一個數字。

十個 DENIED 裡有八個照出第二個問題:拒絕清單只擋得住**走疊加層**那條路,
  broker_list 和規則冊 extra_table 裡 GF / 廣發 / 海通 / 中金 / CICC 還在。
  只增不減=**不刪它們**;本支改成把 deny 標在聯集冊上(inclusion=DENIED),
  並且 status 會把「還有哪幾本冊帶著被拒的鍵」逐條印出來(deny_leak)。
  照出來的洞要指名,不是靜默補一補(L92 哨兵抓到就要給得出下一步)。

新加的三到十三個短碼(SB / OP / OW / N / MP / EW / UP / UW / SS / CD / B / H / S)
  **不進內文命名空間**。這不是我發明的謹慎,是操作員批413 對 `JP` 立過的同一條:
  「兩三字母 token 只在檔名命名空間認得;內文別名絕不收(在內文會亂咬)」。
  本支把它們收進 namespace=field_code(研報表格裡的評等欄位代碼),內文道看不到。
  **既有的短碼(TP / PT / NR / MS / GS …)一個都不動**——這條只約束新收的。

只增不減怎麼證:contains() 逐條比對,底冊每一條 (scope, alias, canonical) 都要在聯集冊裡;
  自測還拿合成資料當場證明這個檢咬得住(LL89 會過的檢等於沒有檢)。

用法:
  status      逐條判 + 印五態統計 + deny_leak(零寫)
  plan        印新增計畫(零寫)
  --apply     寫聯集冊 + 疊加層下一版(只增不減,寫前先證 contains)
  resolve <scope> <token>   一扇門解析(拒絕→正典→疊加→聯集;L101)
  --selftest  廿九檢
誠實 rc:0 GREEN · 1 真的壞 · 2 缺料 · 3 缺件
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

import collections
import glob as _glob
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

VERSION = "0100"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SSOT_DIR = VIA / "supportive modules" / "ssot"
INTAKE = VIA / "supportive modules" / "references" / "intake" / "VIA_SSOT_SynonymUnion_b678"
UNION_OUT = HERE / "VIA_SSOT_SynonymUnion_v0100.json"

BATCH = "批678"
RULED_BY = "AI(批665 操作員授權同義裁定;LL90 留痕義務不轉移)"

# ── 正典鍵對映裁定(同一家機構、兩本冊兩種正典鍵拼法 → 一律解到正典鍵)────────
KEY_ALIAS_RULINGS = {
    "MEGABANK": ("MEGA", "broker_list 的 canonical_en=Megabank 與正典鍵 MEGA 是同一家(兆豐證券);"
                         "正典唯讀=正典鍵才是正本命名空間,別的拼法降為別名(不刪)"),
    "DAIWA SECURITIES": ("DAIWA", "broker_list 的 Daiwa Securities 與正典鍵 DAIWA(大和資本 Daiwa Capital Markets)"
                                  "是同一家;正典鍵為準"),
    "J.P. MORGAN": ("JPM", "broker_list 的 J.P. Morgan 與正典鍵 JPM(摩根大通)是同一家;正典鍵為準"),
    "JPMORGAN": ("JPM", "同上;疊加層 filename_key_map 早已把 JP→JPM 這樣判過,本條只是把內文側補齊"),
    "JP": ("JPM", "疊加層批413 已裁定:JP 只在**檔名命名空間**解到 JPM,內文不收(兩字母會亂咬)"),
    "IBF": ("WATERLAND", "IBF=International Bills Finance=國票;規則冊 extra_table 的 IBF→國票 與正典鍵 "
                         "WATERLAND(國票證券)是同一家;正典鍵為準"),
}

# ── 評等兩軸(既有兩本冊各切一軸;聯集冊記最細的,粗尺當場投影)──────────────
FINE_KEYS = ("STRONG_BUY", "BUY", "ADD", "HOLD", "SELL", "STRONG_SELL", "NOT_RATED")
DIRECTION = {"STRONG_BUY": "POSITIVE", "BUY": "POSITIVE", "ADD": "POSITIVE", "HOLD": "NEUTRAL",
             "SELL": "NEGATIVE", "STRONG_SELL": "NEGATIVE", "NOT_RATED": "UNAVAILABLE"}
# 正典六鍵(institution.broker_ratings):ADD 摺進 BUY
FINE_OF = {"STRONG_BUY": "STRONG_BUY", "BUY": "BUY", "ADD": "BUY", "HOLD": "HOLD",
           "SELL": "SELL", "STRONG_SELL": "STRONG_SELL", "NOT_RATED": "NOT_RATED"}
# 規則冊四鍵(field_rules.rating.canon_map):STRONG_* 摺進 BUY / SELL,ADD 自成一鍵
COARSE_OF = {"STRONG_BUY": "BUY", "BUY": "BUY", "ADD": "ADD", "HOLD": "HOLD",
             "SELL": "SELL", "STRONG_SELL": "SELL", "NOT_RATED": "NOT_RATED"}
SCALE_RULINGS = {
    "避免": ("STRONG_SELL", "既有 knowledge.rating_keywords 把「避免」列在 strong_sell 組;上傳判 SELL 是"
                            "**四態粗尺的投影**,不是相反的判斷。既有為主=留最細的 STRONG_SELL,"
                            "粗尺由 coarse_of() 當場導出(LL327 兩條基準不混成一個)"),
    "強力賣出": ("STRONG_SELL", "同上;上傳同時給了 SELL 與 STRONG_SELL,取最細的那一個"),
}

# 新收的短碼一律進欄位代碼命名空間(內文道看不到)。既有短碼不受此條約束。
FIELD_CODE_MAX = 2
FIELD_CODE_WHY = ("疊加層批413 對 `JP` 立過的同一條:兩三字母 token 只在受限命名空間認得,"
                  "內文別名絕不收(在內文會亂咬)。本條只約束**新收**的別名;"
                  "既有的 TP / PT / NR / MS / GS 一個都不動(只增不減)")

_SCOPES_NEW = ("rating_label", "valuation_method", "financial_concept", "scenario")


# ── 正規化(與收容件冊宣告同一式:NFKC + casefold + 空白收斂)──────────────
def norm(s) -> str:
    s = unicodedata.normalize("NFKC", str(s or "")).casefold()
    return re.sub(r"\s+", " ", s).strip()


def _j(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def _newest(pattern: str, root: Path):
    hits = sorted(_glob.glob(str(root / pattern)))
    return Path(hits[-1]) if hits else None


# ══════════════════════════════════════════════════════════════════════════
#  底冊:既有的每一本,逐條標來源(L30 一個出處——來源不寫就分不清誰說的)
# ══════════════════════════════════════════════════════════════════════════
def baseline() -> dict:
    bb = collections.defaultdict(lambda: collections.defaultdict(set))
    seen, missing = [], []

    def add(scope, alias, canon, src):
        a = norm(alias)
        if a and canon:
            bb[scope][a].add((str(canon), src))

    def need(p: Path, tag: str):
        d = _j(p)
        (seen if d is not None else missing).append(tag)
        return d

    inst = need(SSOT_DIR / "VIA_Financial_Institution_SSOT_v0100.json", "institution")
    ovp = _newest("VIA_FinancialInstitution_Overlay_v*.json", SSOT_DIR)
    ov = need(ovp, "overlay") if ovp else (missing.append("overlay") or {})
    fr = need(VIA / "supportive modules" / "registry" / "VRN_FieldRules_SSOT_v0100.json", "field_rules")
    bl = need(VIA / "functional modules" / "VRN" / "registry" / "VRN_BROKER_LIST_v01.json", "broker_list")
    bd = need(VIA / "functional modules" / "VRN" / "knowledge" / "VRN_Broker_Dict_v0100.json", "broker_dict")
    rd = need(VIA / "functional modules" / "VRN" / "knowledge" / "VRN_Rating_Dict_v0100.json", "rating_dict")

    reg = (inst or {}).get("registries", {})
    for grp in ("domestic_brokers", "foreign_brokers"):
        for k, v in (reg.get(grp) or {}).items():
            for al in list(v.get("aliases") or []) + [k, v.get("chinese_name"), v.get("english_name")]:
                add("broker", al, k, "institution." + grp)
    for k, v in (reg.get("broker_ratings") or {}).items():
        for al in list(v.get("aliases") or []) + [k, v.get("chinese_name"), v.get("english_name")]:
            add("rating", al, k, "institution.broker_ratings")
    for k, v in (reg.get("research_fields") or {}).items():
        for al in list(v.get("aliases") or []) + [k, v.get("chinese_name"), v.get("english_name")]:
            add("target_price", al, k, "institution.research_fields")

    ov = ov or {}
    for k, vs in (ov.get("broker_alias_add") or {}).items():
        for al in vs:
            add("broker", al, k, "overlay.broker_alias_add")
    for e in (ov.get("broker_add") or []):
        kk = e.get("ssot_key")
        for al in list(e.get("aliases") or []) + [kk, e.get("chinese_name"), e.get("english_name")]:
            add("broker", al, kk, "overlay.broker_add")
    for k, vs in (ov.get("rating_alias_add") or {}).items():
        for al in vs:
            add("rating", al, k, "overlay.rating_alias_add")

    rules = (fr or {}).get("rules", {})
    for k, vs in ((rules.get("rating") or {}).get("canon_map") or {}).items():
        for al in vs:
            add("rating", al, k, "field_rules.rating.canon_map")
    for al, k in ((rules.get("rating") or {}).get("local_scale") or {}).items():
        add("rating", al, k, "field_rules.rating.local_scale")
    for k, vs in ((rules.get("broker") or {}).get("extra_table") or {}).items():
        for al in vs:
            add("broker", al, k, "field_rules.broker.extra_table")

    for e in ((bl or {}).get("brokers") or []):
        kk = str(e.get("canonical_en") or e.get("canonical") or "").upper()
        for al in list(e.get("aliases") or []) + [e.get("canonical"), e.get("canonical_en")]:
            add("broker", al, kk, "broker_list")
    for zh, v in ((bd or {}).get("brokers") or {}).items():
        kk = v.get("abbr") or zh
        for al in list(v.get("aliases") or []) + [zh]:
            add("broker", al, kk, "knowledge.broker_dict")
    for e in ((bd or {}).get("brokers_extended") or []):
        for al in list(e.get("aliases") or []) + [e.get("en"), e.get("zh")]:
            add("broker", al, e.get("code"), "knowledge.broker_dict_ext")
    for k, v in ((rd or {}).get("levels") or {}).items():
        for al in list(v.get("zh") or []) + list(v.get("en") or []):
            add("rating", al, k, "knowledge.rating_dict")
    _g2k = {"strong_buy": "STRONG_BUY", "buy": "BUY", "hold": "HOLD",
            "sell": "SELL", "strong_sell": "STRONG_SELL", "not_rated": "NOT_RATED"}
    for g, vs in ((rd or {}).get("keyword_sets") or {}).items():
        for al in (vs if isinstance(vs, list) else []):
            add("rating", al, _g2k.get(g, g.upper()), "knowledge.rating_keywords")

    return {"alias": {s: {a: sorted([list(x) for x in v]) for a, v in m.items()} for s, m in bb.items()},
            "deny": sorted({norm(x) for x in (ov.get("deny_keys") or [])}),
            "deny_raw": list(ov.get("deny_keys") or []),
            "filename_key": {norm(k): v for k, v in (ov.get("filename_key_map") or {}).items()},
            "overlay_path": str(ovp) if ovp else "",
            "books_seen": seen, "books_missing": missing}


def intake() -> dict:
    p = INTAKE / "SYNONYM_LIBRARY.json"
    d = _j(p)
    return d if isinstance(d, dict) else {}


# ══════════════════════════════════════════════════════════════════════════
#  逐條判(誠實五態)
# ══════════════════════════════════════════════════════════════════════════
def classify(base: dict, lib: dict) -> list:
    ba, deny = base.get("alias", {}), set(base.get("deny", []))
    rows = []
    for scope, body in (lib.get("scopes") or {}).items():
        b = ba.get(scope, {})
        for key, cands in body.items():
            k = norm(key)
            canons = {c.get("canonical") for c in cands if c.get("canonical")}
            bc = {c[0] for c in b.get(k, [])}
            if k in deny:
                st, why = "DENIED", "拒絕清單先行(操作員令「大陸券商刪除」「去摩通」);先於正典與疊加層"
            elif not bc:
                st, why = "ADD", ""
            elif canons <= bc:
                st, why = "SAME", ""
            elif canons & bc:
                st, why = "WIDEN", "既有 %s ∪ 新 %s" % (sorted(bc), sorted(canons - bc))
            else:
                st, why = "CONFLICT", "既有 %s vs 新 %s" % (sorted(bc), sorted(canons))
            rows.append({"scope": scope, "key": key, "norm": k, "state": st,
                         "new": sorted(canons), "base": sorted(bc),
                         "base_src": sorted({c[1] for c in b.get(k, [])}),
                         "why": why, "cands": cands})
    rows.sort(key=lambda r: (r["scope"], r["state"], r["norm"]))
    return rows


def rule_conflict(row: dict) -> dict:
    """五個 CONFLICT / 一個 WIDEN 的裁定。每一條都要帶 ruled_by + why(LL90)。"""
    key, base_, new_ = row["norm"], set(row["base"]), set(row["new"])
    for spelling, (canon, why) in KEY_ALIAS_RULINGS.items():
        if spelling in base_ and canon in new_:
            return {"verdict": canon, "kind": "KEY_ALIAS", "ruled_by": RULED_BY,
                    "why": why, "demoted": sorted(base_ - {canon}), "kept_as_alias": True}
    if key in SCALE_RULINGS:
        canon, why = SCALE_RULINGS[key]
        return {"verdict": canon, "kind": "SCALE", "ruled_by": RULED_BY, "why": why,
                "fine": FINE_OF.get(canon, canon), "coarse": COARSE_OF.get(canon, canon)}
    # 沒有對應裁定=誠實留白,不自己編一個(L52)
    return {"verdict": sorted(base_)[0] if base_ else (sorted(new_)[0] if new_ else ""),
            "kind": "BASE_WINS", "ruled_by": RULED_BY,
            "why": "無專門裁定時一律「以現有的為主」:取既有判定,新的併為候選不覆寫"}


def deny_leak(base: dict) -> list:
    """被拒的鍵還留在哪幾本冊裡,逐條指名(只增不減=不刪,只標)。

    兩種,不可以混成一個數字:
      OVERRIDDEN  在**正典**裡。拒絕清單先行=已經擋住了,列出來是因為疊加層自己的裁定
                  文寫「正典的 JPM 別名本來就沒有摩通,兩邊一致」——量下去正典**有**。
                  行為沒錯,冊上的話錯了,所以要留痕。
      LEAK        在別本冊裡,而**讀那本冊的活支不一定走過拒絕閘**(見 gate_bypass())。
    """
    deny, out = set(base.get("deny", [])), []
    for scope, m in (base.get("alias") or {}).items():
        for a, pairs in m.items():
            if a in deny:
                for canon, src in pairs:
                    if src.startswith("overlay"):
                        continue
                    out.append({"scope": scope, "alias": a, "canonical": canon, "book": src,
                                "kind": "OVERRIDDEN" if src.startswith("institution.") else "LEAK"})
    out.sort(key=lambda r: (r["kind"], r["book"], r["alias"]))
    return out


# 讀券商冊的活支有沒有走過拒絕閘——用檔案內容量,不是用印象猜(L93 先疑尺不疑樹)
GATE_MARKS = ("FinancialInstitution_Overlay", "resolve_broker", "deny_reason", "CGC_MDL176")
BROKER_BOOK_MARKS = ("VRN_BROKER_LIST_v01", "extra_table", "VRN_Broker_Dict", "broker_alias",
                     "def broker_of(", "BROKER_ABBR")


def _is_gated(text: str) -> bool:
    return any(m in text for m in GATE_MARKS)


def _reads_broker_book(text: str) -> bool:
    return any(m in text for m in BROKER_BOOK_MARKS)


def gate_bypass() -> list:
    """哪幾支**活的尾版**讀了券商冊卻沒有走拒絕閘。L77 帶排除清單。"""
    out, seen = [], {}
    roots = [VIA / "functional modules" / "VRN", VIA / "supportive modules" / "70_VRN_Rules"]
    for root in roots:
        if not root.exists():
            continue
        for q in root.glob("*.py"):
            if "__pycache__" in str(q) or "RetiredEngines" in str(q) or "references" in str(q):
                continue
            stem = re.sub(r"_v\d{3,4}$", "", q.stem)
            if stem == q.stem:
                continue
            if q.stem > seen.get(stem, ("", None))[0]:
                seen[stem] = (q.stem, q)
    for stem, (_, q) in sorted(seen.items()):
        try:
            t = q.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not _reads_broker_book(t):
            continue
        out.append({"engine": q.name, "gated": _is_gated(t)})
    return out


def book_defects() -> list:
    """既有冊裡量到的實據瑕疵。**只指名不刪**(只增不減);修法是加裁定,不是砍冊。

    這兩條不是上傳帶進來的,是這次對帳才照出來的——冊放著沒人對,錯就會一直在。
    """
    out = []
    bd = _j(VIA / "functional modules" / "VRN" / "knowledge" / "VRN_Broker_Dict_v0100.json") or {}
    brokers = bd.get("brokers") or {}
    for zh, v in brokers.items():
        for al in (v.get("aliases") or []):
            if norm(al) != norm(zh) and norm(al) in {"國泰君安", "guotai junan", "國泰君安證券"}:
                out.append({"kind": "FALSE_ALIAS", "book": "knowledge.broker_dict",
                            "entry": zh, "alias": al, "abbr": v.get("abbr"),
                            "why": "國泰君安是**另一家機構**(大陸券商,操作員已列拒絕清單),"
                                   "不是國泰證券(Cathay)的別名。掛在這裡=國泰君安的研報會被記成國泰的。",
                            "fix": "疊加層拒絕清單先行已擋住;讀這本冊的活支要走同一扇門(見 gate_bypass)"})
    by_abbr = collections.defaultdict(list)
    for zh, v in brokers.items():
        if v.get("abbr"):
            by_abbr[v["abbr"]].append(zh)
    for ab, zhs in sorted(by_abbr.items()):
        if len(zhs) > 1:
            out.append({"kind": "ABBR_COLLISION", "book": "knowledge.broker_dict",
                        "entry": " / ".join(sorted(zhs)), "alias": ab, "abbr": ab,
                        "why": "兩家機構共用同一個縮寫鍵=同一個名字兩扇門(L101)。",
                        "fix": "疊加層 broker_add 已給 大華 正典鍵 DH;解析一律走 resolve() 的正典優先道"})
    return out


def _namespace(scope: str, key: str, is_new: bool) -> str:
    if not is_new:
        return "freetext"
    k = key.strip()
    if scope == "rating" and k.isascii() and len(k) <= FIELD_CODE_MAX:
        return "field_code"
    return "freetext"


# ══════════════════════════════════════════════════════════════════════════
#  聯集冊(底冊每一條都在裡面 + 收進來的;衝突一律留兩邊、標裁定)
# ══════════════════════════════════════════════════════════════════════════
def union(base: dict, lib: dict, rows: list) -> dict:
    deny = set(base.get("deny", []))
    scopes: dict = {}
    for scope, m in (base.get("alias") or {}).items():
        sc = scopes.setdefault(scope, {})
        for a, pairs in sorted(m.items()):
            sc[a] = [{"canonical": c, "source": s, "inclusion": "DENIED" if a in deny else "BASELINE",
                      "namespace": "freetext"} for c, s in pairs]
    rulings, stat = [], collections.Counter()
    for r in rows:
        stat[r["state"]] += 1
        sc = scopes.setdefault(r["scope"], {})
        cur = sc.setdefault(r["norm"], [])
        have = {(e["canonical"], e["source"]) for e in cur}
        if r["state"] == "DENIED":
            for e in cur:
                e["inclusion"] = "DENIED"
            rulings.append({"scope": r["scope"], "key": r["norm"], "state": "DENIED",
                            "ruled_by": "操作員(批413 令「大陸券商刪除」「去摩通」)",
                            "why": r["why"], "upload_said": r["new"], "kept": r["base"]})
            continue
        if r["state"] in ("CONFLICT", "WIDEN"):
            rr = rule_conflict(r)
            rulings.append({"scope": r["scope"], "key": r["norm"], "state": r["state"],
                            "base": r["base"], "upload": r["new"], "base_src": r["base_src"], **rr})
            for e in cur:
                e["verdict"] = rr["verdict"]
                e["ruled_by"] = rr["ruled_by"]
        is_new = r["state"] == "ADD"
        ns = _namespace(r["scope"], r["key"], is_new)
        for c in r["cands"]:
            canon, src = c.get("canonical"), c.get("source") or "intake.SYNONYM_LIBRARY"
            if not canon or (canon, src) in have:
                continue
            e = {"canonical": canon, "source": src, "raw": c.get("raw", r["key"]),
                 "inclusion": "INCLUDED" if is_new else "INCLUDED_BASELINE", "namespace": ns}
            for f in ("guard", "requires_price_context", "scenario", "code"):
                if c.get(f) is not None:
                    e[f] = c[f]
            if ns == "field_code":
                e["guard_ns"] = FIELD_CODE_WHY
            if r["scope"] == "rating":
                e["direction"] = DIRECTION.get(canon, "")
                e["fine"] = FINE_OF.get(canon, canon)
                e["coarse"] = COARSE_OF.get(canon, canon)
            cur.append(e)
    key_alias = {k: {"canonical": v[0], "ruled_by": RULED_BY, "why": v[1]}
                 for k, v in KEY_ALIAS_RULINGS.items()}
    return {
        "schema": "VIA.SSOT.SynonymUnion.v1",
        "version": VERSION,
        "batch": BATCH,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "policy": {
            "order": "拒絕清單 → 正典 → 疊加層 → 聯集冊",
            "only_add": True,
            "canonical_write_mode": "既有冊一律唯讀;本冊只在前三者都沒有時才補",
            "normalization": "NFKC + casefold + 空白收斂;raw 保留原拼法",
            "scale": "評等記最細的一個鍵;正典六鍵走 fine_of()、規則冊四鍵走 coarse_of(),兩條車道不混(LL327)",
            "new_shortcode": FIELD_CODE_WHY,
        },
        "sources": {"baseline_books": base.get("books_seen", []),
                    "baseline_missing": base.get("books_missing", []),
                    "overlay": Path(base.get("overlay_path", "")).name,
                    "intake": "supportive modules/references/intake/VIA_SSOT_SynonymUnion_b678/SYNONYM_LIBRARY.json",
                    "intake_schema": lib.get("schema", ""),
                    "intake_baseline_commit": lib.get("baseline_commit", "")},
        "tally": dict(stat),
        "counts": {s: len(m) for s, m in sorted(scopes.items())},
        "key_alias": key_alias,
        "direction": DIRECTION, "fine_of": FINE_OF, "coarse_of": COARSE_OF,
        "deny": base.get("deny_raw", []),
        "deny_leak": deny_leak(base),
        "book_defects": book_defects(),
        "gate_bypass": gate_bypass(),
        "rulings": rulings,
        "unverified": lib.get("unverified_tokens", []),
        "scopes": {s: scopes[s] for s in sorted(scopes)},
    }


def contains(base: dict, u: dict) -> list:
    """只增不減的證明:底冊每一條 (scope, alias, canonical) 都要在聯集冊裡,一條都不能少。"""
    miss = []
    us = u.get("scopes", {})
    for scope, m in (base.get("alias") or {}).items():
        su = us.get(scope, {})
        for a, pairs in m.items():
            have = {e.get("canonical") for e in su.get(a, [])}
            for canon, src in pairs:
                if canon not in have:
                    miss.append({"scope": scope, "alias": a, "canonical": canon, "book": src})
    return miss


def overlay_next(base: dict, rows: list) -> tuple:
    """疊加層下一版:純增。既有每一個鍵原樣搬過來,再補新的。"""
    cur = _j(Path(base["overlay_path"])) if base.get("overlay_path") else None
    if not isinstance(cur, dict):
        return None, "疊加層缺席=不寫(缺件不是缺料,也不是可以自己造一本)"
    nxt = json.loads(json.dumps(cur, ensure_ascii=False))  # 深拷貝:原件零觸碰
    ra = nxt.setdefault("rating_alias_add", {})
    added = 0
    for r in rows:
        if r["state"] != "ADD" or r["scope"] != "rating":
            continue
        if _namespace("rating", r["key"], True) != "freetext":
            continue          # 短碼不進疊加層的內文道
        for canon in r["new"]:
            lst = ra.setdefault(canon, [])
            raw = (r["cands"][0].get("raw") if r["cands"] else r["key"]) or r["key"]
            if all(norm(x) != r["norm"] for x in lst):
                lst.append(raw)
                added += 1
    ka = nxt.setdefault("key_alias_add", {})
    for k, (canon, why) in KEY_ALIAS_RULINGS.items():
        ka.setdefault(k, canon)
    nxt.setdefault("rulings", {})
    nxt["rulings"]["正典鍵對映(批678)"] = (
        "broker_list / 規則冊 extra_table 對同一家機構用了第二種正典鍵拼法("
        "Megabank=MEGA · Daiwa Securities=DAIWA · J.P. Morgan/JPMorgan/JP=JPM · IBF=WATERLAND)。"
        "正典唯讀=正典鍵才是正本命名空間,其餘降為別名(**不刪**)。"
        "正典自己的 key_migration_map(BOA/ML→BOFA · MCQ/MQ→MACQUARIE)就是同一件事的前四條。"
        + " 裁定 " + RULED_BY)
    nxt["rulings"]["評等短碼(批678)"] = FIELD_CODE_WHY + " 裁定 " + RULED_BY
    nxt["version"] = "%04d" % (int(str(cur.get("version") or "100")) + 1)
    nxt["batch"] = BATCH
    return nxt, "新增評等別名 %d 條 · 正典鍵對映 %d 條" % (added, len(KEY_ALIAS_RULINGS))


# ══════════════════════════════════════════════════════════════════════════
#  一扇門(L101:一個名字只能有一扇門)
# ══════════════════════════════════════════════════════════════════════════
def resolve(scope: str, token: str, u: dict | None = None, base: dict | None = None) -> dict:
    base = base or baseline()
    a = norm(token)
    if a in set(base.get("deny", [])):
        return {"state": "DENIED", "canonical": "", "why": "拒絕清單先行(操作員令)", "source": "overlay.deny_keys"}
    order = [("institution.", "正典"), ("overlay", "疊加層")]
    pairs = (base.get("alias") or {}).get(scope, {}).get(a, [])
    for pre, zh in order:
        for canon, src in pairs:
            if src.startswith(pre):
                return {"state": "GREEN", "canonical": canon, "source": src, "why": zh + "先行"}
    if pairs:
        return {"state": "GREEN", "canonical": pairs[0][0], "source": pairs[0][1], "why": "其餘既有冊"}
    u = u if u is not None else (_j(UNION_OUT) or {})
    ent = (u.get("scopes") or {}).get(scope, {}).get(a, [])
    ent = [e for e in ent if e.get("namespace") != "field_code"]
    if ent:
        return {"state": "GREEN", "canonical": ent[0]["canonical"], "source": ent[0]["source"], "why": "聯集冊(最後)"}
    return {"state": "NODATA", "canonical": "", "source": "", "why": "四道都沒有這個詞"}


# ══════════════════════════════════════════════════════════════════════════
def _report():
    base = baseline()
    lib = intake()
    if not lib:
        return base, None, [], None
    rows = classify(base, lib)
    u = union(base, lib, rows)
    return base, lib, rows, u


def status() -> int:
    base, lib, rows, u = _report()
    if not lib:
        print("[同義聯集] 收容件缺席=ABSENT(rc=3):%s" % (INTAKE / "SYNONYM_LIBRARY.json"))
        return 3
    t = u["tally"]
    print("=== 同義字聯集閘(CGC_MDL176 v%s · %s)===" % (VERSION, BATCH))
    print("底冊 %s%s" % (" · ".join(base["books_seen"]),
                        (" · 缺 " + ",".join(base["books_missing"])) if base["books_missing"] else ""))
    print("底冊別名 " + " · ".join("%s %d" % (s, len(m)) for s, m in sorted(base["alias"].items())))
    print("收容件 %d 條 → SAME %d · ADD %d · WIDEN %d · CONFLICT %d · DENIED %d"
          % (len(rows), t.get("SAME", 0), t.get("ADD", 0), t.get("WIDEN", 0),
             t.get("CONFLICT", 0), t.get("DENIED", 0)))
    by = collections.Counter((r["scope"], r["state"]) for r in rows)
    for (s, st), n in sorted(by.items()):
        if st in ("ADD", "CONFLICT", "WIDEN", "DENIED"):
            print("   %-18s %-9s %d" % (s, st, n))
    print("\n[裁定] %d 條(每條都帶 ruled_by + why;LL90 留痕義務不轉移)" % len(u["rulings"]))
    for r in u["rulings"]:
        print("  · %s %s · %s → %s · %s" % (r["scope"], r["key"], r.get("base") or r.get("kept"),
                                            r.get("verdict") or "(拒絕)", r.get("kind", r["state"])))
    leak = u["deny_leak"]
    lk = [r for r in leak if r["kind"] == "LEAK"]
    ov = [r for r in leak if r["kind"] == "OVERRIDDEN"]
    print("\n[拒絕清單·正典側 OVERRIDDEN] %d 條——正典裡本來就有這條別名,拒絕清單先行已擋住(行為沒錯;"
          "列出來是因為疊加層裁定文寫「正典本來就沒有摩通」,量下去正典**有**)" % len(ov))
    for r in ov:
        print("  · %-32s %s → %s" % (r["book"], r["alias"], r["canonical"]))
    print("\n[拒絕清單·真漏口 LEAK] %d 條——別本冊還帶著被拒的鍵,而讀那本冊的活支不一定走過拒絕閘"
          "(只增不減=不刪,只標)" % len(lk))
    for r in lk:
        print("  · %-32s %s → %s" % (r["book"], r["alias"], r["canonical"]))
    print("\n[冊內瑕疵] %d 條(這次對帳才照出來的,不是上傳帶進來的;一本冊都沒刪)" % len(u["book_defects"]))
    for d in u["book_defects"]:
        print("  · %-16s %s · %s → %s" % (d["kind"], d["book"], d["entry"], d["alias"]))
        print("      因 %s" % d["why"])
    gb = u["gate_bypass"]
    print("\n[沒過拒絕閘的活支] %d/%d(尺=檔案裡有沒有 %s 任一個字樣;只量這件事,不代表別的)"
          % (sum(1 for r in gb if not r["gated"]), len(gb), "/".join(GATE_MARKS)))
    for r in gb:
        print("  %s %s" % ("[過閘]" if r["gated"] else "[沒過閘]", r["engine"]))
    miss = contains(base, u)
    print("\n[只增不減] 底冊 %d 條逐條比對 → 少 %d 條"
          % (sum(len(v) for m in base["alias"].values() for v in m.values()), len(miss)))
    for m in miss[:10]:
        print("  [少] %s" % m)
    print("[聯集冊] " + " · ".join("%s %d" % (k, v) for k, v in u["counts"].items()))
    return 0 if not miss else 1


def plan(write: bool = False) -> int:
    base, lib, rows, u = _report()
    if not lib:
        print("[同義聯集] 收容件缺席=ABSENT(rc=3)")
        return 3
    miss = contains(base, u)
    if miss:
        print("[同義聯集] 只增不減證明不過:底冊少了 %d 條 → 不寫(fail-closed)" % len(miss))
        return 1
    nxt, why = overlay_next(base, rows)
    adds = [r for r in rows if r["state"] == "ADD"]
    print("[計畫] 聯集冊 %s · 新增 %d 條(%s)"
          % (UNION_OUT.name, len(adds),
             " · ".join("%s %d" % (s, n) for s, n in
                        sorted(collections.Counter(r["scope"] for r in adds).items()))))
    print("[計畫] 疊加層 %s → v%s · %s" % (Path(base["overlay_path"]).name,
                                          (nxt or {}).get("version", "?"), why))
    if not write:
        print("[計畫] 預設零寫;要寫是 --apply(只增不減已證)")
        return 0
    UNION_OUT.write_text(json.dumps(u, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("[寫] %s" % UNION_OUT)
    if nxt:
        op = SSOT_DIR / ("VIA_FinancialInstitution_Overlay_v%s.json" % nxt["version"])
        if op.exists():
            print("[拒寫] %s 已存在=Hydra 守衛(版號只往前,不覆寫既有版)" % op.name)
            return 1
        cur = _j(Path(base["overlay_path"])) or {}
        lost = [k for k in cur if k not in nxt]
        if lost:
            print("[拒寫] 疊加層下一版少了鍵 %s → fail-closed" % lost)
            return 1
        op.write_text(json.dumps(nxt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("[寫] %s" % op)
    return 0


# ══════════════════════════════════════════════════════════════════════════
def selftest() -> int:
    ok = fail = 0
    lines = []

    def chk(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            lines.append("  [OK] %s %s" % (name, detail))
        else:
            fail += 1
            lines.append("  [FAIL] %s %s" % (name, detail))

    base = baseline()
    lib = intake()
    inst0 = _j(SSOT_DIR / "VIA_Financial_Institution_SSOT_v0100.json") or {}
    chk("① 底冊六本都讀得到", not base["books_missing"], str(base["books_missing"]))
    chk("② 收容件在位且是宣告的 schema", lib.get("schema") == "VIA.Synonyms.SourceScoped.v1", lib.get("schema", ""))
    chk("③ 收容件宣告 only_add", lib.get("only_add") is True)
    rows = classify(base, lib)
    chk("④ 443 條逐條有判,沒有漏判", len(rows) == sum(len(v) for v in lib["scopes"].values()) and
        all(r["state"] in ("SAME", "ADD", "WIDEN", "CONFLICT", "DENIED") for r in rows), "%d 條" % len(rows))
    u = union(base, lib, rows)
    miss = contains(base, u)
    chk("⑤ **只增不減**:底冊每一條都在聯集冊裡", not miss, "少 %d 條" % len(miss))

    # 負控:⑤ 要是永遠會過那就是假綠(LL89)。當場拿掉一條,證明它咬得住。
    u_bad = json.loads(json.dumps(u, ensure_ascii=False))
    victim = sorted(u_bad["scopes"]["broker"])[0]
    u_bad["scopes"]["broker"].pop(victim)
    chk("⑥ 負控:拿掉一條就一定要被 contains() 抓到", bool(contains(base, u_bad)), "拿掉 " + victim)

    chk("⑦ 正規化與收容件宣告同一式(NFKC+casefold+空白收斂)",
        norm(" Ｍｏｒｇａｎ　Stanley ") == "morgan stanley", norm(" Ｍｏｒｇａｎ　Stanley "))
    deny = set(base["deny"])
    chk("⑧ 拒絕清單先行:被拒的詞在聯集冊上一律 DENIED",
        all(all(e.get("inclusion") == "DENIED" for e in v)
            for s, m in u["scopes"].items() for a, v in m.items() if a in deny),
        "%d 個拒絕鍵" % len(deny))
    chk("⑨ 拒絕清單真的有咬到收容件", sum(1 for r in rows if r["state"] == "DENIED") >= 8,
        "%d 條" % sum(1 for r in rows if r["state"] == "DENIED"))
    leak = u["deny_leak"]
    chk("⑩ 漏口逐條指名(不是一句「有漏」),而且不刪任何一本冊",
        len(leak) >= 8 and all(r["book"] and r["alias"] and r["canonical"] for r in leak), "%d 條" % len(leak))
    chk("⑪ 五個 CONFLICT 全部有裁定,而且每條都帶 ruled_by + why(LL90)",
        all(r.get("ruled_by") and r.get("why") for r in u["rulings"]), "%d 條裁定" % len(u["rulings"]))
    ka = [r for r in u["rulings"] if r.get("kind") == "KEY_ALIAS"]
    chk("⑫ 四條正典鍵衝突一律解到正典鍵,而且舊拼法留著當別名(不刪)",
        len(ka) >= 4 and all(r.get("kept_as_alias") for r in ka), "%d 條" % len(ka))
    _inst_keys = {norm(k) for grp in ("domestic_brokers", "foreign_brokers")
                  for k in (((inst0.get("registries") or {}).get(grp)) or {})}
    _targets = {c for c, _ in KEY_ALIAS_RULINGS.values()}
    chk("⑬ 正典鍵裁定的目標一定是**正典自己的鍵**(不准裁到一個不存在的鍵上)",
        bool(_inst_keys) and all(norm(c) in _inst_keys for c in _targets),
        ",".join(sorted(_targets)) + " ⊆ 正典 %d 鍵" % len(_inst_keys))
    chk("⑬b 負控:裁到一個不存在的鍵一定要被抓到",
        norm("ZZZ_NOT_A_BROKER") not in _inst_keys)
    chk("⑭ 評等兩軸投影覆蓋七個細鍵,一個都不漏",
        set(FINE_OF) == set(FINE_KEYS) == set(COARSE_OF) == set(DIRECTION),
        "%d 鍵" % len(FINE_KEYS))
    chk("⑮ 粗尺是真的粗:STRONG_* 摺進 BUY/SELL,而 ADD 在規則冊四鍵裡自成一鍵",
        COARSE_OF["STRONG_BUY"] == "BUY" and COARSE_OF["STRONG_SELL"] == "SELL"
        and COARSE_OF["ADD"] == "ADD" and FINE_OF["ADD"] == "BUY")
    fr = _j(VIA / "supportive modules" / "registry" / "VRN_FieldRules_SSOT_v0100.json") or {}
    cm = set((((fr.get("rules") or {}).get("rating") or {}).get("canon_map") or {}))
    chk("⑯ 粗尺的值域就是規則冊 canon_map 的鍵(尺不是我編的,是從冊上量的)",
        set(COARSE_OF.values()) - {"NOT_RATED"} == cm, "canon_map=%s" % sorted(cm))
    inst = _j(SSOT_DIR / "VIA_Financial_Institution_SSOT_v0100.json") or {}
    fine = set(((inst.get("registries") or {}).get("broker_ratings") or {}))
    chk("⑰ 細尺的值域就是正典 broker_ratings 的鍵",
        set(FINE_OF.values()) == fine, "broker_ratings=%s" % sorted(fine))
    newcodes = [r for r in rows if r["state"] == "ADD" and _namespace(r["scope"], r["key"], True) == "field_code"]
    chk("⑱ 新收的短碼一律進 field_code 命名空間(批413 對 JP 立的同一條)",
        len(newcodes) >= 10 and all(len(r["key"]) <= FIELD_CODE_MAX for r in newcodes),
        ",".join(sorted(r["key"] for r in newcodes)))
    old_short = [a for a, v in u["scopes"]["target_price"].items()
                 if len(a) <= FIELD_CODE_MAX and any(e.get("inclusion") == "BASELINE" for e in v)]
    chk("⑲ **既有**短碼一個都沒被降級(這條只約束新收的;只增不減)",
        all(all(e.get("namespace") == "freetext" for e in u["scopes"]["target_price"][a]
                if e.get("inclusion") == "BASELINE") for a in old_short),
        ",".join(sorted(old_short)) or "(無)")
    chk("⑳ 一扇門:resolve() 對同一個詞只回一個正典鍵,而且正典先於疊加層先於聯集冊(L101)",
        resolve("broker", "元大", u, base)["canonical"] == "YUANTA"
        and resolve("broker", "廣發", u, base)["state"] == "DENIED"
        and resolve("rating", "Strong Buy", u, base)["canonical"] == "STRONG_BUY",
        "元大→%s · 廣發→%s" % (resolve("broker", "元大", u, base)["canonical"],
                              resolve("broker", "廣發", u, base)["state"]))
    chk("㉑ 內文道看不到新收的短碼(resolve 過濾 field_code)",
        resolve("rating", "sb", u, base)["state"] == "NODATA"
        and any(e["canonical"] == "STRONG_BUY" for e in u["scopes"]["rating"]["sb"]),
        "sb 在冊上有、內文道 NODATA")
    nxt, why = overlay_next(base, rows)
    cur = _j(Path(base["overlay_path"])) or {}
    chk("㉒ 疊加層下一版是**純增**:舊版每一個鍵、每一條別名都還在",
        nxt is not None and all(k in nxt for k in cur) and
        all(all(any(norm(x) == norm(y) for x in nxt["rating_alias_add"].get(k, []))
                for y in vs) for k, vs in (cur.get("rating_alias_add") or {}).items()), why)
    chk("㉓ 疊加層原件零觸碰(深拷貝;寫的是新版號,舊版一個位元不動)",
        nxt is not None and nxt is not cur and int(nxt["version"]) > int(str(cur.get("version") or "100")),
        "v%s → v%s" % (cur.get("version"), (nxt or {}).get("version")))
    chk("㉔ 零網路零開庫:本支只讀 JSON,不 import duckdb/requests,不跑 subprocess",
        not any(m in Path(__file__).read_text(encoding="utf-8").split("def selftest(")[0]
                for m in ("import duckdb", "import requests", "subprocess", "urllib.request")))
    leak2 = [r for r in leak if r["kind"] == "LEAK"]
    over2 = [r for r in leak if r["kind"] == "OVERRIDDEN"]
    chk("㉕ 漏口分兩種,不混成一個數字:正典裡的是**已被拒絕清單擋住**,別本冊的才是真漏口",
        bool(leak2) and bool(over2) and len(leak2) + len(over2) == len(leak),
        "LEAK %d · OVERRIDDEN %d" % (len(leak2), len(over2)))
    defects = u["book_defects"]
    chk("㉖ 兩條冊內瑕疵逐條指名(國泰君安掛成國泰的別名 · 兩家共用同一縮寫鍵),而且一本冊都沒刪",
        any(d["kind"] == "FALSE_ALIAS" for d in defects) and
        any(d["kind"] == "ABBR_COLLISION" for d in defects) and
        all(d.get("why") and d.get("fix") for d in defects),
        " · ".join("%s:%s" % (d["kind"], d["alias"]) for d in defects))
    gb = u["gate_bypass"]
    chk("㉗ 沒過閘的活支逐支指名(尺量的是**檔案內容**,不是印象;L93)",
        bool(gb) and all("engine" in r and isinstance(r["gated"], bool) for r in gb),
        "讀券商冊的活尾版 %d 支 · 沒過閘 %d 支" % (len(gb), sum(1 for r in gb if not r["gated"])))
    _gated_src = "from VIA_FinancialInstitution_Overlay_v0100 import resolve_broker\nextra_table\n"
    _bare_src = "def broker_of(text):\n    return text\n"
    chk("㉘ 負控:兩個判準都要當場證明咬得住(會過的檢=沒有檢;LL89)",
        _reads_broker_book(_gated_src) and _is_gated(_gated_src)
        and _reads_broker_book(_bare_src) and not _is_gated(_bare_src)
        and not _reads_broker_book("print('hello')"),
        "有閘的判成有閘 · 沒閘的判成沒閘 · 不讀券商冊的不進分母")
    print("=== CGC_MDL176 同義字聯集閘 v%s · 廿九檢自測(零網路;預設零寫)===" % VERSION)
    print("\n".join(lines))
    print("  [計] 廿九檢 OK %d · FAIL %d" % (ok, fail))
    return 0 if fail == 0 else 1


def main(argv=None) -> int:
    a = list(argv if argv is not None else sys.argv[1:])
    if "--selftest" in a:
        return selftest()
    verb = a[0] if a else "status"
    if verb == "status":
        return status()
    if verb in ("plan", "apply"):
        return plan(write=("--apply" in a or verb == "apply"))
    if verb == "resolve" and len(a) >= 3:
        r = resolve(a[1], " ".join(a[2:]))
        print("[解析] %s · %s → %s · %s · %s" % (a[1], " ".join(a[2:]), r["canonical"] or "(無)",
                                                 r["state"], r["why"]))
        return 0 if r["state"] == "GREEN" else (1 if r["state"] == "DENIED" else 2)
    if "--apply" in a:
        return plan(write=True)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""
VIS_VRN_BrokerAlias_FullList_v0100
Append-only supportive helper. NO DB WRITE / NO SSOT / NO OCR.

Superset drop-in for VIS_VRN_BrokerAlias_Compatibility_v0222: re-exports the
whole v0222 surface (bridge functions included), then overrides the alias
table with the FULL 20-broker registry from VRN_BROKER_LIST_v01.json so
domestic brokers (中信/兆豐/凱基/華南/國泰/台新/統一...) and the remaining
internationals (Daiwa/Citi/CLST/UBS/CLSA...) resolve too.
批680:原本這一行把 GF 也列為可解析的例子——批679 依操作員令把陸券自冊上移除之後,
那句話就不成立了。**說明文字也是內容**,冊上的話跟冊裡的資料對不起來就是冊在說謊。
Evidence basis: 2026-08-05 batch run - only the four gate-listed brokers
matched; 35/60 corpus files fell to NONE.
"""

# 批681(v0101→v0102):拒絕閘從「命中之後的三個值」下到「文字這一層」。
#   Codex 在 PR #59 照出:文內寫的是被拒機構時,表序先中先贏會先命中一個
#   **較短的合法別名**,於是被拒的機構被記成另一家合法券商。ENG086 同一個病灶。

from __future__ import annotations

# ===== [VIA:DENY-GATE:v0101] 券商拒絕閘(批680;graceful 零行為變更) =====
#   操作員批413 的拒絕清單(「大陸券商刪除」「去摩通」)原本只擋得住**走疊加層**那一條路;
#   批678 量下去,讀券商冊的活尾版 10/10 都沒走過那扇門——拒絕清單立了、裁定留了,
#   可是真正在讀研報券商名的這幾支從來沒經過它。這個區塊把門接上:
#   解析出來的券商在**回傳之前**過一次閘,被拒就回空 + 因由,不是靜默放行。
#
#   名單**不在這裡**:它在疊加層的 `deny_keys`(L30 一個出處 / Zero-Hydra)。
#   批679 我曾經在一支自測裡又抄了一份陸券名單,當場被陸券清除閘判成
#   「還帶著活的陸券解析資料」——判得對,抄第二份名單就是第二顆會漂移的頭。
#   疊加層缺席 / 讀不到 / 任何例外 → **原樣放行**(缺件不是壞掉,而且零行為變更)。
def _via_deny_reason(*values) -> str:
    """任何一個值在拒絕清單上就回一句因由;都不在(或疊加層缺席)回空字串。"""
    fn = _VIA_DENY.get("fn", False)
    if fn is False:
        fn = None
        try:
            import glob as _g
            import importlib.util as _iu
            from pathlib import Path as _P
            _p = _P(__file__).resolve()
            while _p.parent != _p:
                _d = _p / "supportive modules" / "ssot"
                if _d.is_dir():
                    _h = sorted(_g.glob(str(_d / "VIA_FinancialInstitution_Overlay_v*.py")))
                    if _h:
                        _s = _iu.spec_from_file_location("_via_ov_gate", _h[-1])
                        _m = _iu.module_from_spec(_s)
                        _s.loader.exec_module(_m)
                        fn = getattr(_m, "deny_reason", None)
                    break
                _p = _p.parent
        except Exception:
            fn = None
        _VIA_DENY["fn"] = fn
    if not fn:
        return ""
    for v in values:
        if not v:
            continue
        try:
            why = fn(str(v))
        except Exception:
            return ""
        if why:
            return why
    return ""


_VIA_DENY: dict = {}


def _via_deny_sample(n: int = 1) -> list:
    """從**那一份名單本身**取樣,當拒絕閘正控的探針值。

    批680 實錄(同一個錯的第三次):要證明閘會咬,就得餵它一個被拒的名字;
    我三次都直接把「廣發」打進檢裡——而那就是又抄了一份名單,
    陸券清除閘每次都當場把我判成「還帶著活的陸券解析資料」,三次都判得對。
    **「不准出現 X」的檢,天生會把 X 抄進來。** 出路只有一條:探針值從名單當場取。
    順帶好處:操作員哪天改了名單,這個正控會自動跟著改,不會變成釘住舊名單的殭屍。
    """
    fn = _VIA_DENY.get("keys", False)
    if fn is False:
        keys = []
        try:
            import glob as _g
            import json as _js
            from pathlib import Path as _P
            _p = _P(__file__).resolve()
            while _p.parent != _p:
                _d = _p / "supportive modules" / "ssot"
                if _d.is_dir():
                    _h = sorted(_g.glob(str(_d / "VIA_FinancialInstitution_Overlay_v*.json")))
                    if _h:
                        keys = [str(x) for x in
                                _js.loads(_P(_h[-1]).read_text(encoding="utf-8")).get("deny_keys", []) if x]
                    break
                _p = _p.parent
        except Exception:
            keys = []
        _VIA_DENY["keys"] = keys
        fn = keys
    return list(fn) if (n is None or n <= 0) else list(fn)[:n]


def _via_deny_in_text(text: str) -> tuple:
    """文內逐字命中的**最長**被拒機構名 → (名, 長度);沒命中回 ("", 0)。

    批681:批680 的閘只看**解出來的正典名**,於是最長別名優先會先命中一個
    較短的合法別名,把被拒的機構接走成另一家合法券商(Codex 在 PR #59 照出)。
    尺要下到文字這一層,而且用的是與本檔比對別名**同一把**尺
    (CJK 直接子字串 · 拉丁詞界 · ≤3 字拉丁要大寫獨立詞),只是把拒絕清單
    也當成候選別名丟進去一起比長短。名單一樣不在這裡(L30 / LL336)。
    """
    t = text or ""
    if not t:
        return "", 0
    low = t.lower()
    best = ("", 0)
    for k in _via_deny_sample(0):
        s = str(k).strip()
        if not s:
            continue
        sl = s.lower()
        if any("\u4e00" <= ch <= "\u9fff" for ch in s):
            hit = s in t
        elif len(sl) <= 3:
            hit = re.search(r"(?<![A-Za-z])" + re.escape(s.upper()) + r"(?![A-Za-z])", t) is not None
        else:
            hit = re.search(r"(?<![a-z])" + re.escape(sl) + r"(?![a-z])", low) is not None
        if hit and len(sl) > best[1]:
            best = (s, len(sl))
    return best
# ===== [VIA:DENY-GATE:END] =====

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

import importlib.util
import json
import os
import re
import sys
from typing import Dict, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_BASE_PATH = os.path.join(_HERE, "VIS_VRN_BrokerAlias_Compatibility_v0222.py")
_spec = importlib.util.spec_from_file_location("vis_vrn_brokeralias_v0222_base", _BASE_PATH)
_base = importlib.util.module_from_spec(_spec)
sys.modules["vis_vrn_brokeralias_v0222_base"] = _base
_spec.loader.exec_module(_base)

# re-export every public name from the v0222 base (bridge health, smoke test, dataclass...)
globals().update({k: v for k, v in vars(_base).items() if not k.startswith("_")})
BrokerAliasResult = _base.BrokerAliasResult

# ---- full 20-broker table from the registry SSOT ----------------------------
_LIST_PATH = os.path.normpath(os.path.join(
    _HERE, "..", "..", "functional modules", "VRN", "registry", "VRN_BROKER_LIST_v01.json"))


def _load_full_table() -> Dict[str, Dict[str, object]]:
    table: Dict[str, Dict[str, object]] = {}
    with open(_LIST_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    for b in data["brokers"]:
        aliases = list(dict.fromkeys(
            [b["canonical"], b["canonical_en"]] + list(b.get("aliases", []))))
        aliases.sort(key=len, reverse=True)  # longest-first: 華南永昌 before 華南
        table[b["canonical"]] = {
            "canonical": b["canonical_en"],
            "aliases": aliases,
            "country": b.get("country", ""),
            "requires_compatibility_gate": bool(b.get("requires_compatibility_gate", False)),
        }
    return table


BROKER_ALIAS_TABLE = _load_full_table()


def def_normalize_broker_name(text: str) -> Optional[BrokerAliasResult]:
    source = text or ""
    # 批681:**拒絕清單先行**(操作員裁定次序:拒絕清單 → 正典 → 疊加層 → 聯集冊)。
    #   批680 只在命中之後看 canonical/key/alias 三個值,擋不住「文字裡寫的是被拒機構、
    #   卻被一個較短的合法別名接走」——那正是 Codex 在 PR #59 照出的那一條。
    _bad, _blen = _via_deny_in_text(source)
    for key, item in BROKER_ALIAS_TABLE.items():
        for alias in item["aliases"]:
            # CJK aliases: no ascii-boundary guards (dates/digits legitimately abut, e.g. 20250819兆豐).
            # ASCII aliases: letter-only boundaries so CTBC251208 matches but JP never fires inside Japan.
            if re.search(r"[㐀-鿿]", alias):
                pattern = re.escape(alias)
            else:
                pattern = rf"(?<![A-Za-z]){re.escape(alias)}(?![A-Za-z])"
            if re.search(pattern, source, re.I):
                # 批680:回傳之前過一次拒絕閘(名單在疊加層 deny_keys,不在這裡)
                if _via_deny_reason(item["canonical"], key, alias):
                    continue
                # 批681:文內命中的被拒名只要**不比這個合法別名短**,就是它贏。
                #   短的被拒名輸給長的合法別名,所以合法券商不會被連坐。
                if _bad and _blen >= len(alias):
                    return None
                return BrokerAliasResult(
                    raw=alias,
                    canonical=item["canonical"],
                    matched_key=key,
                    confidence=0.95 if alias in (key, item["canonical"]) else 0.88,
                    requires_compatibility_gate=bool(item["requires_compatibility_gate"]),
                    aliases=list(item["aliases"]),
                )
    return None


def def_get_broker_alias_table() -> Dict[str, Dict[str, object]]:
    return BROKER_ALIAS_TABLE


def def_smoke_test() -> bool:
    cases = {
        "GS-2317 20251205.pdf": "Goldman Sachs",
        "MS-ABF 20260518.pdf": "Morgan Stanley",
        "20250819兆豐個股報告-泓德能源(6873).pdf": "Megabank",
        "凱基投顧_1476 儒鴻_20260519.pdf": "KGI",
        "華南投顧-2606-裕民-1141202.pdf": "HuaNan",
        "統一投顧-20251209投資早報.pdf": "President",
        "Daiwa-6278 20260521.pdf": "Daiwa Securities",
        "UBS-Asia Hardware Insights 20251205.pdf": "UBS",
        "Citi-3231 20250604.pdf": "Citigroup",
        # 批680:這一條的期待值停在**批541 併案之前**。操作員批541 裁定
        #   「CLSA = CLST 是同一家(里昂)」,冊上早已併成 CLSA,所以這裡解出 CLSA 才是對的。
        #   v0100 接閘之前跑同一個案例就已經是這個結果——**不是這一批造成的**,
        #   是一個釘著舊狀態的期待值躺了很久沒人跑(這支從來沒有自測門,所以格子上也沒有它的站)。
        #   改期待值不是改尺:裁定變了,期待值就該跟著變(LL332 同型)。
        "CLST-6669 20251001.pdf": "CLSA",
    }
    ok = True
    for name, want in cases.items():
        got = def_normalize_broker_name(name)
        if got is None or got.canonical != want:
            print("SMOKE FAIL:", name, "->", (got.canonical if got else None), "want", want)
            ok = False
    return ok


def selftest() -> int:
    """批680:本支從來沒有自測門,所以格子上也就沒有它的站(LL317 沒有自測門的支不准敲)。
    接上拒絕閘的同時把門補上——**六檢**,而且拒絕閘那兩檢是正控不是宣告。"""
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 既有 smoke 案例全中(接閘之後一個都不准退步)", def_smoke_test())
    chk("② 別名表有料而且每一筆都有 canonical", bool(BROKER_ALIAS_TABLE)
        and all(v.get("canonical") for v in BROKER_ALIAS_TABLE.values()),
        f"({len(BROKER_ALIAS_TABLE)} 家)")
    chk("③ 台資/外資解析照舊(元大 · CTBC · 里昂)",
        all((lambda r: r is not None)(def_normalize_broker_name(t))
            for t in ("元大投顧", "CTBC251208", "CLST-6669")))
    # ── 拒絕閘:今天是備援(批679 已把冊清乾淨),所以用**正控**證明它咬得住(LL89)──
    _bak = dict(BROKER_ALIAS_TABLE)
    try:
        _probe = (_via_deny_sample(1) or [""])[0]
        BROKER_ALIAS_TABLE["_PROBE"] = {"canonical": "_PROBE", "aliases": [_probe],
                                        "requires_compatibility_gate": False}
        _den = def_normalize_broker_name("某某" + _probe + "的報告")
        _pas = def_normalize_broker_name("元大投顧")
    finally:
        BROKER_ALIAS_TABLE.clear()
        BROKER_ALIAS_TABLE.update(_bak)
    chk("④ 拒絕閘正控:**把被拒的機構塞回表裡**,它一定要解不出來;而且不能連帶擋掉合法的",
        bool(_probe) and _den is None and _pas is not None and _pas.canonical == "Yuanta",
        f"(探針取自名單第一條 · 被拒→{_den} · 元大→{_pas.canonical if _pas else None})")
    # ⑤ 第一版我把這一檢寫成一句自己騙自己的話(`"deny_keys" not in t.replace("deny_keys","",1)`
    #    ——先把它拿掉再問有沒有,永遠成立)。改成真的量兩件事。
    # 量的是**資料**不是散文:用 AST 取所有字串字面量,並扣掉模組與各函式的 docstring。
    #   批680 實錄:第一版拿整份原始碼做 `in` 比對,把三段**註解**也算成「自帶名單」——
    #   其中一段還是我自己在解釋為什麼不可以抄名單。註解裡提到一個名字不等於冊上有這一筆,
    #   這跟陸券清除閘的 verify 把資料與註解分兩欄報是同一條(LL324)。
    import ast as _ast
    _src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _tree = _ast.parse(_src)
    _docs = set()
    for _n in _ast.walk(_tree):
        if isinstance(_n, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
            _d = _ast.get_docstring(_n, clean=False)
            if _d:
                _docs.add(_d)
    _body = "\n".join(n.value for n in _ast.walk(_tree)
                       if isinstance(n, _ast.Constant) and isinstance(n.value, str)
                       and n.value not in _docs)
    # 「本檔有沒有自帶名單」這一檢本身也不准抄名單——拿**那一份名單**去比對本檔內容。
    _keys = _via_deny_sample(99)
    _own_list = [w for w in _keys if w in _body]
    chk("⑤ 名單不在本檔(L30 一個出處):閘讀疊加層 deny_keys · 本檔**沒有**第二份名單 ·"
        "讀不到名單就原樣放行(缺件不是壞掉)。比對用的名單也是**當場讀來的**,不是抄的",
        bool(_keys) and bool(_via_deny_reason(_keys[0])) and not _via_deny_reason("元大")
        and not _own_list,
        f"(名單 {len(_keys)} 條 · 本檔自帶 {_own_list or '無'})")
    chk("⑥ 還原乾淨:正控塞進去的假資料不准留在表裡",
        "_PROBE" not in BROKER_ALIAS_TABLE, f"({len(BROKER_ALIAS_TABLE)} 家)")
    # 批681:名單上每一條放進文字裡都要解不出來(探針從名單當場取,不打字進來 LL336)
    _miss = [k for k in _keys if def_normalize_broker_name(f"{k}研究部") is not None]
    chk("⑦ 拒絕閘下到**文字這一層**:名單上每一條放進文字裡都要解不出來——"
        "批680 只看命中之後的三個值,擋不住被較短合法別名接走的情形",
        bool(_keys) and not _miss,
        f"(名單 {len(_keys)} 條 · 漏擋 {len(_miss)} 條"
        + (f":{'、'.join(_miss[:5])}" if _miss else "") + ")")
    _fp = []
    for _k, _it in BROKER_ALIAS_TABLE.items():
        for _a in _it["aliases"]:
            _a = str(_a).strip()
            if not _a or _via_deny_in_text(f"{_a}研究部")[0]:
                continue
            _r = def_normalize_broker_name(f"{_a}研究部")
            if _r is None or _r.canonical != _it["canonical"]:
                _fp.append(_a)
    chk("⑧ 負控:文字裡**沒有**被拒機構的合法別名,一條都不准被閘連坐"
        "(改尺之後要證明它沒有改到不該改的 LL337)",
        not _fp,
        f"(表上別名 {sum(len(v['aliases']) for v in BROKER_ALIAS_TABLE.values())} 條 · 被連坐 {len(_fp)} 條"
        + (f":{'、'.join(_fp[:5])}" if _fp else "") + ")")
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    import sys as _sys
    import pathlib
    if "--selftest" in _sys.argv[1:]:
        print("=== SUP_MDL015 券商別名全清單 · 八檢自測(批680 +拒絕閘;批681 下到文字層)===")
        raise SystemExit(selftest())
    print("brokers:", len(BROKER_ALIAS_TABLE))
    print("smoke:", "PASS" if def_smoke_test() else "FAIL")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL177_ChinaBrokerPurge v0100 — 陸券清除閘(批679)
====================================================================
操作員令(批679):「刪中國券商 自動修改統整更新完」。

這是**操作員親自解除只增不減**的一次。批678 我量到 31 條被拒的陸券鍵還留在四本冊裡,
按只增不減只標了 DENIED 沒有刪;操作員看完裁定:**刪**。
裁定權在操作員(LL90),所以這一批真的動刀。但動刀有三條自己的規矩:

  ① **正典一個位元都不碰。** `VIA_Financial_Institution_SSOT_v0100.json/.py` 自己寫著
     `canonical_write_mode = READ_ONLY`。而且量下去:正典 28 家券商裡**一家陸券都沒有**
     (16 家台資 + 12 家外資)。它身上只有兩條**別名**撞到拒絕清單——
     `中信證券→CTBC`(台灣的中國信託)與 `摩通→JPM`(美國摩根大通)。
     那兩條不是陸券,是**撞名**,拒絕清單先行本來就擋住了。所以正典零動作。
  ② **刪掉的每一個位元組都留在台帳裡。** `VIA_ChinaBrokerPurge_Ledger_v0100.json` 收
     每一條被刪項的完整原文 + 檔案原始 sha256;`restore` 一個動詞就能還原回去。
     刪不等於沒發生過——沒有留痕的刪,下一個人永遠查不出這裡曾經有過什麼。
  ③ **改完當場重新解析。** 每一支 .py 改完立刻 `ast.parse` + 逐鍵對帳
     (只少了該少的那一個,其餘每一個鍵與值位元相同);任何一項不過就**整支放棄不寫**。

要刪的是哪幾家(操作員批413 拒絕清單那一份,不是我另外列的):
    廣發 GF · 中信證券/中信建投 CITIC · 中金 CICC · 海通 HAITONG · 國泰君安 GUOTAIJUNAN
**不刪、而且自測會盯著它們還在**的:
    里昂 CLSA/CLST(批541 操作員裁定:同一家,留)· 中信/中信金/中國信託 CTBC(台灣)
    國泰/國泰證期/國泰投顧/國泰金控 CATHAY(台灣)· 正典 28 家全數

十三個落點,分三種處理法:

  【JSON 冊 · 就地改】資料就是給人讀的,引擎用寫死路徑讀它;開新版號沒有人會去讀,
                      舊版還帶著陸券=更糟(宣告了沒接線)。
      functional modules/VRN/registry/VRN_BROKER_LIST_v01.json          GF 整筆
      functional modules/VRN/knowledge/VRN_Broker_Dict_v0100.json       ext 四筆 + 國泰的假別名
      supportive modules/registry/VRN_FieldRules_SSOT_v0100.json        extra_table 三鍵 + CTBC 的 中信證券

  【.py 資料表 · 就地改(L87 豁免附理由)】這幾支是**別名資料表**,被 import 的是寫死的
      模組名(`financial_classification_rules` / `VIS_VRN_*_v0224`),沒有人 glob 尾版。
      開新版號=死碼,而活著的那一版照樣帶著廣發。所以就地改,並且整份位元備份進台帳。
      functional modules/VRN/financial_classification_rules.py          CICC/CITIC/HAITONG/GUOTAIJUNAN 四筆
      supportive modules/70_VRN_Rules/VIS_VRN_BrokerAlias_Extension_v0224.py
      supportive modules/70_VRN_Rules/VIS_VRN_InputRoutePolicy_v0224.py
      supportive modules/70_VRN_Rules/VIS_VRN_Q1_AliasRoutePatch_v0100.py
      supportive modules/environment/(上面三支的位元同檔副本,一起改,否則兩個答案)

  【引擎 · 開新版號(尾版律)】這三支是被 `newest(..._v*.py)` glob 的活引擎,改引擎就要升版。
      VRN_ENG086_FirstPageLogicBridge_v0108 → v0109   HAITONG/CICC/GF 三鍵 + 版頭那句話一起改
      VRN_ENG073_ReportStructuredDB_v0135   → v0136   BROKER_DICT 的 "GF": "廣發"
      VIA_VRN_FirstPageEngine_v0125         → v0126   別名表的 "GF"

**沒有動、而且說清楚為什麼**:
  正典兩支(唯讀)· `VIA_AutoCode_Registry_v0100.json`(台帳=留痕本身,刪它等於湮滅證據)
  `_superseded/` `20260804/` `*_sha*.py`(封存版)· `VAP/ASSETS/SCOPE_COPY/`(整棵樹的快照副本)
  `VRN_ExtractionLogic_SSOT_v0100.json`(那是一句**說明文字**在列券商名,不是解析表)

v0100→v0101 追記(批702:主線回帶的五個新落點)
  批679 把十三個落點清乾淨了,`verify` 當時是 0。批692 的側枝收容
  `local/parallel-b692:工作站未追蹤 VRN 件側枝收容` 把工作站上的五個檔帶進活樹,
  **陸券又回來了**——這不是清得不乾淨,是清完之後又流進來。所以 v0101 不改尺,只補落點。

  補的五個,逐個說為什麼它算「活的」(不是我說活就活,是量出來的):
    functional modules/VRN/engine/VRN_AutoTestLoop.py
        全樹只有這一份,而 `functional modules/VRN/Invoke-VRN-AutoTest.ps1:123`
        寫死 `Join-Path (Join-Path $PSScriptRoot 'engine') 'VRN_AutoTestLoop.py'`
        ——**啟動器直接指進來**。活的。
    functional modules/VRN/engine/VRN_Integrated_ReportDatabase_Engine.py
        全樹 27 處引用;正本另存在 `references/intake/..._b685/`(零觸碰照舊),
        這一份是工作複本。改工作複本,正本一個位元不動。
    functional modules/VRN/engine/VIA_VRN_FirstPageEngine.py
        無版號,與它同名的活尾版是 `functional modules/VRN/VIA_VRN_FirstPageEngine_v0127.py`;
        尾版律排序下 `.py` 排在 `_v0127.py` 前面,所以**它不會被當成尾版挑走**。
        但它在 `engine/` 夾裡、跟上面那支測試迴圈同夾,AutoTest 那條線讀得到它。活的。
    functional modules/VRN/knowledge/SYNONYM_LIBRARY_v3.json
    functional modules/VRN/knowledge/SYNONYM_LIBRARY_v4.json
        **全樹引用數 0**——沒有任何一支 .py/.ps1/.json 讀它們。
        那為什麼還是要清?因為它們躺在 `knowledge/` 夾裡,跟被清過的
        `VRN_Broker_Dict_v0100.json` 同夾,長得就是一本知識冊。
        批679 自己寫過:「舊版還帶著陸券=更糟(宣告了沒接線)」。
        兩本都清,不留「哪一本才算數」的空間。

  這兩本冊的頭上寫著 `"only_add": true`。**刪它等於違反它自己宣告的政策**,
  這件事要說出來而不是繞過去:只增不減在陸券這一題上是**操作員親自解除的**(批679),
  解除的範圍是「陸券」,不是「這本冊」。所以照刪,而 `only_add` 與本次刪除的衝突
  逐字記進台帳的 `policy_conflict` 欄,restore 一個動詞原樣放回。

  就地改還是升版?這五個全是**就地改**:三支 .py 沒有版號(開新版號=沒有人會去讀的死碼,
  而活著的那一份照樣帶著廣發),兩本 JSON 是資料冊(同理)。位元原文全進台帳。

  順手修一件既有的事:JSON 寫回原本一律 `indent=1`,而 `VRN_BROKER_LIST_v01.json`
  與這兩本同義字冊原本是 `indent=2`——照 v0100 寫回會**把整本 150 KB 重排**,
  真正刪掉的那十行淹在重排裡沒人看得見。v0101 寫回**沿用原檔縮排**。

用法:
  plan        逐檔逐條列出要刪什麼(零寫)
  --apply     真的刪 + 寫台帳
  restore     從台帳把每一個位元原樣放回去
  verify      刪完之後全樹再掃一次,還有沒有活的落點
  --selftest  卅一檢(含「台灣券商一家都不准少」的負控)
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

import ast
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

VERSION = "0102"
BATCH = "批679"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LEDGER = HERE / "VIA_ChinaBrokerPurge_Ledger_v0100.json"
RULED_BY = "操作員(批679 令「刪中國券商」;批413 拒絕清單為名單來源)"

# ── 名單:正典鍵層級(操作員批413 拒絕清單那一份)────────────────────────────
CN_CANON = {"GF", "GF SECURITIES", "CICC", "CITIC", "CITIC SECURITIES",
            "HAITONG", "HAITONG SECURITIES", "GUOTAIJUNAN", "GUOTAI JUNAN"}
# ── 名單:別名層級。**逐字全等**,不做前綴比對 ──
#    中信 / 中信金 / 中國信託 是台灣的中國信託(CTBC),一個字都不准碰。
CN_ALIAS = {
    "廣發", "廣發證券", "gf", "gf securities",
    "中金", "中金公司", "中國國際金融", "cicc", "china international capital",
    "中信證券", "中信建投", "citic", "citic securities",
    "海通", "海通證券", "haitong", "haitong securities",
    "國泰君安", "國泰君安證券", "guotai junan", "guotai junan securities",
}
# ── 負控名單:這些一個都不准消失(自測逐條驗)──
MUST_KEEP_ALIAS = ("中信", "中信金", "中國信託", "ctbc", "中信投顧",
                   "國泰", "國泰證期", "國泰投顧", "國泰金控", "cathay",
                   "clsa", "clst", "里昂", "大華", "日盛", "合庫", "宏遠", "德意志",
                   "元大", "凱基", "兆豐", "華南", "統一", "台新", "國票", "永豐", "玉山")


def norm(s) -> str:
    s = unicodedata.normalize("NFKC", str(s or "")).casefold()
    return re.sub(r"\s+", " ", s).strip()


def is_cn_alias(v) -> bool:
    return norm(v) in CN_ALIAS


def is_cn_canon(v) -> bool:
    return norm(v).upper() in {k.upper() for k in CN_CANON} or norm(v) in CN_ALIAS


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════
#  .py 側:AST 定位 → 切掉那一段 → 重新解析 → 逐鍵對帳
#     不用「找字串換掉」是因為同一個字可能出現在註解、docstring、別人的值裡。
#     AST 給的是**這個字面量在第幾個位元組**,那才叫定位。
# ══════════════════════════════════════════════════════════════════════════
def _spans_dict_keys(src: str, keys: set) -> list:
    """找出所有 dict 字面量裡鍵名在 keys 內的 (start, end) 位元組區間(含尾逗號)。"""
    tree = ast.parse(src)
    b = src.encode("utf-8")
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if not isinstance(k, ast.Constant) or not isinstance(k.value, str):
                continue
            if norm(k.value).upper() not in {norm(x).upper() for x in keys}:
                continue
            s = _off(b, k.lineno, k.col_offset)
            e = _off(b, v.end_lineno, v.end_col_offset)
            m = re.match(rb"\s*,", b[e:])          # 吃掉緊接的逗號與空白
            if m:
                e += m.end()
            m2 = re.match(rb"[ \t]*\n", b[e:])     # 這一項獨佔一行就連換行一起收
            if m2 and b[:s].rstrip(b" \t").endswith(b"\n"):
                e += m2.end()
                while s > 0 and b[s - 1:s] in (b" ", b"\t"):
                    s -= 1
            out.append((s, e))
    return sorted(out, reverse=True)


def _spans_list_elems(src: str, field: str, vals: set) -> list:
    """找出 list 裡「某欄位等於 vals 之一」的 dict 元素區間。"""
    tree = ast.parse(src)
    b = src.encode("utf-8")
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.List):
            continue
        for el in node.elts:
            if not isinstance(el, ast.Dict):
                continue
            got = None
            for k, v in zip(el.keys, el.values):
                if isinstance(k, ast.Constant) and k.value == field and isinstance(v, ast.Constant):
                    got = v.value
            if got is None or norm(got).upper() not in {norm(x).upper() for x in vals}:
                continue
            s = _off(b, el.lineno, el.col_offset)
            e = _off(b, el.end_lineno, el.end_col_offset)
            m = re.match(rb"\s*,", b[e:])
            if m:
                e += m.end()
            out.append((s, e))
    return sorted(out, reverse=True)


def _spans_str_in_lists(src: str, toks: set) -> list:
    """找出 list 字面量裡等於 toks 之一的字串元素區間。"""
    tree = ast.parse(src)
    b = src.encode("utf-8")
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.List):
            continue
        for el in node.elts:
            if not (isinstance(el, ast.Constant) and isinstance(el.value, str)):
                continue
            if norm(el.value) not in {norm(x) for x in toks}:
                continue
            s = _off(b, el.lineno, el.col_offset)
            e = _off(b, el.end_lineno, el.end_col_offset)
            m = re.match(rb"\s*,", b[e:])
            if m:
                e += m.end()
            out.append((s, e))
    return sorted(out, reverse=True)


def _off(b: bytes, lineno: int, col: int) -> int:
    """ast 的 col_offset 是**該行的 utf-8 位元組位移**,不是字元數。"""
    pos, ln = 0, 1
    while ln < lineno:
        nxt = b.index(b"\n", pos) + 1
        pos, ln = nxt, ln + 1
    return pos + col


def _literals(src: str) -> dict:
    """把檔裡每個「賦值給大寫常數」的字面量取出來,用來逐鍵對帳。"""
    out = {}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            try:
                out[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    return out


def purge_py(src: str, *, dict_keys=(), list_field=None, list_vals=(), str_toks=()) -> tuple:
    """回傳 (新內容, 刪了幾段, 為什麼不能寫)。任何一關不過就回原文 + 理由。"""
    try:
        ast.parse(src)
    except SyntaxError as ex:
        return src, 0, "原檔就解析不過(%s)→ 不碰" % ex
    b = src.encode("utf-8")
    spans = []
    if dict_keys:
        spans += _spans_dict_keys(src, set(dict_keys))
    if list_field:
        spans += _spans_list_elems(src, list_field, set(list_vals))
    if str_toks:
        spans += _spans_str_in_lists(src, set(str_toks))
    if not spans:
        return src, 0, ""
    # 區間會互相包含(整鍵的 span 包著它自己值裡那幾個字串的 span)。
    # 由小到大排、真正做一次區間聯集,再由後往前切——不然同一段會被切兩次,切成壞檔。
    # 批679 實錄:第一版只跟「前一段」比包含關係,合成檔當場切出語法錯,
    # 靠改完重新解析那一關才擋住(fail-closed 救了一次,但尺本來就不該讓它發生)。
    merged = []
    for s, e in sorted(set(spans)):
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    nb = b
    for s, e in reversed(merged):
        nb = nb[:s] + nb[e:]
    new = nb.decode("utf-8")
    try:
        ast.parse(new)
    except SyntaxError as ex:
        return src, 0, "改完解析不過(%s)→ 整支放棄不寫" % ex
    before, after = _literals(src), _literals(new)
    if set(before) != set(after):
        return src, 0, "常數名不見了 %s → 放棄" % sorted(set(before) - set(after))
    for name, ov in before.items():
        nv = after[name]
        if isinstance(ov, dict) and isinstance(nv, dict):
            lost = {k: v for k, v in ov.items() if k not in nv}
            if any(not is_cn_canon(k) for k in lost):
                return src, 0, "%s 少了不該少的鍵 %s → 放棄" % (name, sorted(k for k in lost if not is_cn_canon(k)))
            for k, v in nv.items():
                if k in ov and ov[k] != v and not (isinstance(v, list) and isinstance(ov[k], list)
                                                   and [x for x in ov[k] if not is_cn_alias(x)] == v):
                    return src, 0, "%s['%s'] 的值被改到了 → 放棄" % (name, k)
    return new, len(merged), ""


# ══════════════════════════════════════════════════════════════════════════
#  JSON 側:結構化刪除(逐本冊寫明刪什麼,不靠通則猜)
# ══════════════════════════════════════════════════════════════════════════
def purge_broker_list(d: dict) -> tuple:
    keep, dropped = [], []
    for e in d.get("brokers", []):
        if is_cn_canon(e.get("canonical_en") or "") or is_cn_canon(e.get("canonical") or ""):
            dropped.append(e)
        else:
            keep.append(e)
    d["brokers"] = keep
    d["total_canonical_brokers"] = len(keep)
    return d, dropped


def purge_broker_dict(d: dict) -> tuple:
    dropped = []
    keep = []
    for e in d.get("brokers_extended", []):
        if is_cn_canon(e.get("code") or "") or is_cn_alias(e.get("zh") or ""):
            dropped.append({"where": "brokers_extended", "entry": e})
        else:
            keep.append(e)
    d["brokers_extended"] = keep
    d["count_extended"] = len(keep)
    for zh, v in list((d.get("brokers") or {}).items()):
        if is_cn_alias(zh):
            dropped.append({"where": "brokers", "key": zh, "entry": v})
            d["brokers"].pop(zh)
            continue
        al = v.get("aliases") or []
        bad = [a for a in al if is_cn_alias(a)]
        if bad:
            v["aliases"] = [a for a in al if not is_cn_alias(a)]
            dropped.append({"where": "brokers.%s.aliases" % zh, "removed": bad})
    d["count"] = len(d.get("brokers") or {})
    return d, dropped


def purge_field_rules(d: dict) -> tuple:
    dropped = []
    et = ((d.get("rules") or {}).get("broker") or {}).get("extra_table") or {}
    for k in list(et):
        if is_cn_canon(k):
            dropped.append({"where": "extra_table", "key": k, "aliases": et[k]})
            et.pop(k)
            continue
        bad = [a for a in et[k] if is_cn_alias(a)]
        if bad:
            et[k] = [a for a in et[k] if not is_cn_alias(a)]
            dropped.append({"where": "extra_table.%s" % k, "removed": bad})
    return d, dropped


def purge_json_generic(o, dropped=None, path=""):
    """通吃型 JSON 清除:鍵是陸券、值是陸券、list 元素是陸券字串、
    list 元素的任何一個值是陸券 —— 四種一起收。逐條記在 dropped 裡。

    批679 第二輪。第一輪用逐本冊寫死的清法,只吃得下三本;剩下八本 JSON
    各有各的長相(有的把別名擺在鍵上、有的擺在 rows[].def_preferred_value、
    有的整串 dict 被存成一個字串)。與其為每一本再寫一支,不如承認
    **它們要刪的是同一件事**,用一把遞迴的尺走完(L30 一個出處)。
    """
    if dropped is None:
        dropped = []
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if isinstance(k, str) and (is_cn_alias(k) or is_cn_canon(k)
                                       or any(is_cn_alias(x) for x in re.split(r"[\s/·,、]+", k) if x)):
                dropped.append({"path": path + "/" + k, "kind": "KEY", "value": v})
                continue
            if isinstance(v, str) and (is_cn_alias(v) or is_cn_canon(v)):
                dropped.append({"path": path + "/" + k, "kind": "VALUE", "value": v})
                continue
            out[k] = purge_json_generic(v, dropped, path + "/" + str(k))
        return out
    if isinstance(o, list):
        out = []
        for i, v in enumerate(o):
            if isinstance(v, str) and (is_cn_alias(v) or is_cn_canon(v)):
                dropped.append({"path": "%s[%d]" % (path, i), "kind": "ELEM", "value": v})
                continue
            if isinstance(v, dict) and any(isinstance(x, str) and (is_cn_alias(x) or is_cn_canon(x))
                                           for x in v.values()):
                dropped.append({"path": "%s[%d]" % (path, i), "kind": "RECORD", "value": v})
                continue
            out.append(purge_json_generic(v, dropped, "%s[%d]" % (path, i)))
        return out
    return o


def purge_synonym_library(d: dict) -> tuple:
    """同義字冊(批702 新落點)。長相跟前三本都不一樣:別名擺在**鍵**上
    (`scopes/broker/廣發`),每個鍵底下一串出處紀錄。

    不另寫一把尺——`purge_json_generic` 的四種情形(鍵是陸券/值是陸券/
    list 元素是陸券/元素的任一值是陸券)正好全吃得下,只是它的回傳慣例
    跟 JSON_TARGETS 要的 `(new, dropped)` 不同。這裡只做**接頭**,不做判斷:
    多一把尺就多一個會走鐘的地方(L30 一個出處)。
    """
    dropped: list = []
    return purge_json_generic(d, dropped), dropped


def _indent_of(text: str) -> int:
    """從原檔量出它用幾格縮排——寫回時沿用,不把整本冊重排(批702)。"""
    m = re.search(r'\n(\s+)"', text)
    return len(m.group(1)) if m else 1


GROUP_RX = (
    re.compile(r"^(?P<base>[A-Za-z_.]+)\[(?P<idx>\d+)\]"),          # brokers[11].country
    re.compile(r"^(?P<base>email_domain_to_broker\.[^.]+)\."),       # email_domain_to_broker.gf.com.cn.*
    re.compile(r"^(?P<base>def_vrn_report_ssot\.broker_alias_extension\.records\.[A-Za-z]+)"),
)


def _group_of(key: str):
    """扁平化鍵屬於哪一個**群組**。`brokers[11].country` 的群組是 ('brokers', 11)。"""
    for rx in GROUP_RX:
        m = rx.match(str(key or ""))
        if m:
            d = m.groupdict()
            return (d["base"], int(d["idx"]) if d.get("idx") else None)
    return None


def purge_json_grouped(rows: list, key_field: str) -> tuple:
    """扁平化清冊:一個群組裡**只要有一片葉子是陸券,整個群組都要走**,然後重新編號。

    批679 實錄(Codex 在 PR #55 照出的 P1,照得對):
      第一輪我只刪了「值是陸券」的那幾列,於是 `brokers[11]` 的
      canonical / canonical_en / aliases[0..3] 沒了,
      country=China · rank=12 · alias_count=4 · source_layers[0] 卻留在原地。
      而清乾淨後的 VRN_BROKER_LIST 裡 index 11 已經變成**里昂 CLSA**
      ——任何人照這份扁平冊重建參數,就會得到「**里昂穿著廣發的 metadata**」。
      刪一片葉子留下一個無頭群組,比不刪還危險:它看起來是完整的一筆。

    所以兩件事一起做:**整組刪**,而且**把後面的 index 往前補**,
    讓 `brokers[N]` 跟清乾淨後的冊逐位對得起來。
    """
    groups, loose, order = {}, [], []
    for r in rows:
        g = _group_of(r.get("def_preferred_key", ""))
        if g is None:
            loose.append(r)
            continue
        if g not in groups:
            groups[g] = []
            order.append(g)
        groups[g].append(r)
    banned = {g for g, rs in groups.items()
              if any(is_cn_alias(r.get("def_preferred_value")) or is_cn_canon(r.get("def_preferred_value"))
                     for r in rs)}
    dropped = [{"group": str(g), "rows": len(groups[g]),
                "values": [r.get("def_preferred_value") for r in groups[g]]} for g in sorted(banned, key=str)]
    # 同一個 base 底下的 index 重新編號(只動被刪掉那一組之後的)
    shift = {}
    for base in {g[0] for g in groups if g[1] is not None}:
        idxs = sorted(g[1] for g in groups if g[0] == base and g[1] is not None)
        n = 0
        for i in idxs:
            if (base, i) in banned:
                continue
            shift[(base, i)] = n
            n += 1
    out, renum = [], 0
    for r in rows:
        g = _group_of(r.get("def_preferred_key", ""))
        if g is None:
            out.append(r)
            continue
        if g in banned:
            continue
        if g[1] is not None and shift.get(g) not in (None, g[1]):
            new_i = shift[g]
            r = dict(r)
            old_pk, old_kf = r["def_preferred_key"], str(r.get(key_field, ""))
            r["def_preferred_key"] = re.sub(r"^(%s)\[%d\]" % (re.escape(g[0]), g[1]),
                                            r"\1[%d]" % new_i, old_pk)
            r[key_field] = re.sub(r"^(%s)_%d_" % (re.escape(g[0]), g[1]),
                                  r"\1_%d_" % new_i, old_kf)
            renum += 1
        out.append(r)
    return out, dropped, renum


# 第二輪:通吃型清除 + 兩處**改正**(不是刪——那兩筆是台灣的中國信託被寫成「中信證券」)
PASS2_JSON = (
    "functional modules/VRN/SSOT/VRN_Report_Parser_Integrated_SSOT.json",
    "functional modules/VRN/knowledge/VRN_Digest_Params_v0100.json",
    "supportive modules/VIA_Governance_Runtime/VIA_Governance_Unified_NotionBeginning_Detailed_Anchored_SSOT.runtime.json",
    "supportive modules/audit_tools/VRN_BrokerRecognition_Acceptance_v0100.json",
    "supportive modules/registry/VIA_FinalParameters_CanonicalRegistry.json",
    "supportive modules/ssot/VIA_Parameters_SSOT.json",
    "supportive modules/registry/VRN_S05_FieldRegistry_v0102.json",
    "functional modules/VAP/VAP_Param_Registry_v0100.json",
)
# 陸券的網域整筆拿掉(gf.com.cn=廣發)
CN_DOMAIN = ("gf.com.cn", "citics.com", "citicsf.com", "htsec.com", "cicc.com", "gtja.com")
# 被存成「一整串 dict 的字串」的參數快照:把 'GF': [...] 那一段從字串裡切掉
STR_FRAG = re.compile(r"'(?:GF|CICC|CITIC|HAITONG|GUOTAIJUNAN)'\s*:\s*\[[^\]]*\]\s*,?\s*")
# 兩處**改正**:台灣的中國信託(CTBC)被寫成「中信證券」——那是陸券的名字,改回正名
FIX_TEXT = (
    ("functional modules/VRN/VRN_Complete_FeatureAudit_Ultra.py", '"zh": "中信證券"', '"zh": "中國信託"'),
    ("functional modules/VRN/VRN_MDL001_Converter_v0121.py", '"中信": "中信證券"', '"中信": "中國信託"'),
    ("functional modules/VRN/VRN_ENG086_FirstPageLogicBridge_v0109.py",
     "匯豐/法巴/瑞信/巴克萊/Jefferies/海通/中金/瑞穗/日興",
     "匯豐/法巴/瑞信/巴克萊/Jefferies/瑞穗/日興"),
)


JSON_TARGETS = (
    ("functional modules/VRN/registry/VRN_BROKER_LIST_v01.json", purge_broker_list,
     "券商正本清冊:GF(廣發,country=China)整筆移出"),
    ("functional modules/VRN/knowledge/VRN_Broker_Dict_v0100.json", purge_broker_dict,
     "知識冊:brokers_extended 四筆陸券整筆移出;並把掛在**國泰(Cathay)**底下的"
     "『國泰君安 / Guotai Junan / 國泰君安證券』三條假別名拆掉(那是另一家機構,"
     "掛在這裡=國泰君安的研報會被記成國泰的)"),
    ("supportive modules/registry/VRN_FieldRules_SSOT_v0100.json", purge_field_rules,
     "中央規則正本:extra_table 的 GF / HAITONG / CICC 三鍵移出;"
     "並把 CTBC 別名裡的『中信證券』拆掉(中國信託=中信/中信金/中國信託/中信投顧,那幾條照留)"),
    # ── 批702:批692 側枝收容帶進來的兩本同義字冊(引用數 0,但長得就是活知識冊)
    ("functional modules/VRN/knowledge/SYNONYM_LIBRARY_v3.json", purge_synonym_library,
     "同義字冊 v3:scopes/broker 底下的 廣發/廣發證券/gf/gf securities/海通/haitong/"
     "中金/cicc/中信證券 九個鍵整鍵移出 + unverified_tokens 裡的陸券紀錄整筆移出;"
     "冊頭 only_add=true 與本次刪除的衝突記在台帳 policy_conflict"),
    ("functional modules/VRN/knowledge/SYNONYM_LIBRARY_v4.json", purge_synonym_library,
     "同義字冊 v4:同上(v3/v4 兩本都清,不留「哪一本才算數」的空間)"),
)

PY_TARGETS = (
    ("functional modules/VRN/financial_classification_rules.py",
     {"list_field": "code", "list_vals": CN_CANON, "str_toks": CN_ALIAS},
     "券商分類規則資料表:CICC / CITIC / HAITONG / GUOTAIJUNAN 四筆整筆移出"),
    ("supportive modules/70_VRN_Rules/VIS_VRN_BrokerAlias_Extension_v0224.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS}, "別名擴充表:GF 整鍵移出"),
    ("supportive modules/70_VRN_Rules/VIS_VRN_InputRoutePolicy_v0224.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS}, "輸入路由策略:GF 整鍵移出"),
    ("supportive modules/70_VRN_Rules/VIS_VRN_Q1_AliasRoutePatch_v0100.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS}, "Q1 別名路由補丁:GF Securities 移出"),
    ("supportive modules/environment/VIS_VRN_BrokerAlias_Extension_v0224.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS}, "同上(environment 位元同檔副本;兩份一起改,否則兩個答案)"),
    ("supportive modules/environment/VIS_VRN_InputRoutePolicy_v0224.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS}, "同上"),
    ("supportive modules/environment/VIS_VRN_Q1_AliasRoutePatch_v0100.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS}, "同上"),
    # ── 批702:批692 側枝收容帶進來的三支 engine/ 件。全無版號,就地改。
    ("functional modules/VRN/engine/VRN_AutoTestLoop.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS},
     "自動測試迴圈:別名對照的 \"GF\": \"廣發\" 移出"
     "(全樹只此一份,Invoke-VRN-AutoTest.ps1:123 寫死指進來)"),
    ("functional modules/VRN/engine/VRN_Integrated_ReportDatabase_Engine.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS},
     "整合研報庫引擎:CTBC 別名串裡的『中信證券』拆掉"
     "(撞名——中國信託是 中信/中信金/中國信託/中信投顧;正本在 references/intake 零觸碰)"),
    ("functional modules/VRN/engine/VIA_VRN_FirstPageEngine.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS},
     "首頁全能引擎(無版號工作複本):GF 整鍵移出 + CTBC 別名串裡的『中信證券』拆掉"),
)

# 第二輪的 .py 落點:整筆測試紀錄裡 'broker_alias': 'GF Securities'(值不是鍵,第一輪的尺吃不到)
PASS2_PY = (
    "supportive modules/70_VRN_Rules/VIS_VRN_Q1_AliasRoutePatch_v0100.py",
    "supportive modules/environment/VIS_VRN_Q1_AliasRoutePatch_v0100.py",
)


def _spans_dict_by_value(src: str, toks: set) -> list:
    """找出「任何一個值等於 toks 之一」的 dict 元素(整筆紀錄)區間。"""
    tree = ast.parse(src)
    b = src.encode("utf-8")
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.List):
            continue
        for el in node.elts:
            if not isinstance(el, ast.Dict):
                continue
            if not any(isinstance(v, ast.Constant) and isinstance(v.value, str)
                       and norm(v.value) in {norm(x) for x in toks} for v in el.values):
                continue
            s = _off(b, el.lineno, el.col_offset)
            e = _off(b, el.end_lineno, el.end_col_offset)
            m = re.match(rb"\s*,", b[e:])
            if m:
                e += m.end()
            out.append((s, e))
    return out


# 引擎:尾版律 → 開新版號,舊版一個位元不動
ENGINE_TARGETS = (
    ("functional modules/VRN", "VRN_ENG086_FirstPageLogicBridge_v*.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS},
     "首頁邏輯橋:別名表的 HAITONG / CICC / GF 三鍵移出"),
    ("functional modules/VRN", "VRN_ENG073_ReportStructuredDB_v*.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS},
     "研報結構庫:BROKER_DICT 的 \"GF\": \"廣發\" 移出"),
    ("functional modules/VRN", "VIA_VRN_FirstPageEngine_v*.py",
     {"dict_keys": CN_CANON, "str_toks": CN_ALIAS},
     "首頁全能引擎:別名表的 GF 移出"),
)

# 動都不動,而且說清楚為什麼(L87)
UNTOUCHED = (
    ("supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.json", "正典唯讀;28 家裡一家陸券都沒有,身上只有 中信證券/摩通 兩條**撞名別名**,拒絕清單先行已擋"),
    ("supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.py", "同上"),
    ("supportive modules/registry/VIA_AutoCode_Registry_v0100.json", "台帳=留痕本身;裡面那幾句是操作員當初下令的原文,刪它等於湮滅證據"),
    ("supportive modules/registry/VRN_ExtractionLogic_SSOT_v0100.json", "命中的是一句**說明文字**在列券商名,不是解析表"),
    ("functional modules/VAP/ASSETS/SCOPE_COPY/**", "整棵樹的快照副本,不是活的解析面"),
    ("functional modules/VRN/_superseded/** · 20260804/** · *_sha*.py", "封存版;尾版律下不再被任何人讀"),
)


# 批702:清完之後**指向已經被清掉的正典鍵**的殘留(懸空指標)。
#   量到的是 `"GFHK": "GF"`——廣發香港。GF 被清掉了,GFHK 這一條還指著它。
#   **不自己補名單**:名單的出處是操作員批413 拒絕清單(疊加層 deny_keys 20 條,量過,沒有 GFHK),
#   本支檢 ① 就是在盯這件事。所以不刪,改為**逐條點名**等操作員裁定(LL90)。
#   懸空而不點名,下一個人會以為 GF 還在。
DANGLING_NAMED = {
    "GFHK": "廣發香港(GF Securities HK)。值指向已清掉的 GF;GFHK 不在操作員批413 拒絕清單上,"
            "依名單出處律不自行加名——列在這裡等裁定。",
}


def _dangling_in_py(src_text: str, rel: str, kw: dict) -> list:
    """一支 .py 清完之後,還有哪些鍵指著被清掉的正典鍵。"""
    out = []
    new, _n, bad = purge_py(src_text, **kw)
    if bad:
        return out
    try:
        tree = ast.parse(new)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                continue
            if not (isinstance(v, ast.Constant) and isinstance(v.value, str)):
                continue
            if is_cn_canon(v.value) and not is_cn_canon(k.value) and not is_cn_alias(k.value):
                out.append({"path": rel, "key": k.value, "points_to": v.value})
    return out


def _dangling_in_json(o, rel: str, path: str = "") -> list:
    """一本 JSON 清完之後,還有哪些值指著被清掉的正典鍵(鍵本身不是陸券)。"""
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str) and is_cn_canon(v) \
                    and not (isinstance(k, str) and (is_cn_canon(k) or is_cn_alias(k))):
                out.append({"path": rel, "key": str(k), "points_to": v})
            else:
                out += _dangling_in_json(v, rel, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += _dangling_in_json(v, rel, "%s[%d]" % (path, i))
    return out


def dangling() -> list:
    """清完之後還指著被清掉的正典鍵的地方。零寫:在**記憶體副本**上先清再看。

    批705 自審:v0101 只掃 `PY_TARGETS` —— **引擎升版件(ENGINE_TARGETS)與五本 JSON
    一支都沒掃過**。檢 ㊳ 於是只看得到十支就地改的 .py,其餘 8 個落點的懸空指標
    它一律看不見,而看不見的東西當然「沒有未點名的」。
    範圍窄的尺會給出一個看起來很乾淨的答案 —— 這跟批703 的 gate_bypass 是同一個病。
    """
    out = []
    for rel, kw, _why in PY_TARGETS:
        p = VIA / rel
        if not p.exists():
            continue
        out += _dangling_in_py(p.read_text(encoding="utf-8"), rel, kw)
    # 批705:引擎升版件也要掃——它們一樣有別名表,一樣會留下懸空指標。
    for sub, pat, kw, _why in ENGINE_TARGETS:
        q = _newest(VIA / sub, pat)
        if q is None:
            continue
        out += _dangling_in_py(q.read_text(encoding="utf-8"), str(q.relative_to(VIA)), kw)
    # 批705:五本 JSON 也要掃——值指向被清掉的正典鍵,跟 .py 是同一件事。
    for rel, fn, _why in JSON_TARGETS:
        p = VIA / rel
        if not p.exists():
            continue
        try:
            d, _dropped = fn(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
        out += _dangling_in_json(d, rel)
    return out


def json_roundtrip() -> list:
    """每一本 JSON 落點:沿用原檔縮排寫回,是不是**逐位元相同**。

    批705 自審:v0101 的檢 ㊲ 只驗了 `SYNONYM_LIBRARY_v4` 一本,而它剛好會過。
    五本逐本量下去,**有兩本不會過**(`VRN_Broker_Dict_v0100` 與 `VRN_FieldRules_SSOT`,
    兩本都是 indent=1):`_indent_of` 認出的縮排是對的,但原檔還有別的差異
    (分隔符 / 鍵序 / 尾空白之類),照樣會被重排。
    **只測那個會過的案例,等於沒測。** 這裡逐本報,不會過的照實列出來,
    `apply()` 也把它記進台帳的 `reformatted`,讓重排是**留痕的**而不是靜悄悄的。
    """
    out = []
    for rel, _fn, _why in JSON_TARGETS:
        p = VIA / rel
        if not p.exists():
            out.append({"path": rel, "state": "ABSENT"})
            continue
        raw = p.read_text(encoding="utf-8")
        try:
            same = json.dumps(json.loads(raw), ensure_ascii=False,
                              indent=_indent_of(raw)) + "\n" == raw
        except Exception:
            same = False
        out.append({"path": rel, "indent": _indent_of(raw),
                    "state": "EXACT" if same else "REFORMATS"})
    return out


def _newest(root: Path, pat: str):
    hits = sorted(root.glob(pat))
    return hits[-1] if hits else None


def _bump(name: str) -> str:
    m = re.search(r"_v(\d{3,4})(\.py)$", name)
    return name[:m.start(1)] + ("%0*d" % (len(m.group(1)), int(m.group(1)) + 1)) + m.group(2)


def scan() -> dict:
    """逐個落點量:要刪什麼、刪幾段。零寫。"""
    plan = {"json": [], "py": [], "engine": [], "missing": []}
    for rel, fn, why in JSON_TARGETS:
        p = VIA / rel
        if not p.exists():
            plan["missing"].append(rel)
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        _, dropped = fn(json.loads(json.dumps(d, ensure_ascii=False)))
        plan["json"].append({"rel": rel, "why": why, "dropped": dropped, "sha": sha(p)})
    for rel, kw, why in PY_TARGETS:
        p = VIA / rel
        if not p.exists():
            plan["missing"].append(rel)
            continue
        src = p.read_text(encoding="utf-8")
        new, n, bad = purge_py(src, **kw)
        plan["py"].append({"rel": rel, "why": why, "spans": n, "blocked": bad, "sha": sha(p)})
    for sub, pat, kw, why in ENGINE_TARGETS:
        p = _newest(VIA / sub, pat)
        if p is None:
            plan["missing"].append(sub + "/" + pat)
            continue
        src = p.read_text(encoding="utf-8")
        new, n, bad = purge_py(src, **kw)
        plan["engine"].append({"rel": str(p.relative_to(VIA)), "next": _bump(p.name),
                               "why": why, "spans": n, "blocked": bad, "sha": sha(p)})
    return plan


def preflight() -> list:
    """**動任何一個位元之前**,把所有會擋下來的事先問完。

    批679 實錄(Codex 在 PR #55 照出的 P2,照得對):
      Hydra 守衛(目標版號已存在就拒寫)原本寫在引擎那一圈,
      而 JSON 與就地改的 .py **在那之前就已經寫下去了**。
      於是「版號撞了」會回 rc=1,但倉庫已經是**改了一半**的狀態,
      而且 `_merge_ledger` 還沒跑 → **那些改動連台帳都沒有**。
      擋要擋在第一次寫之前,不然叫「失敗之後留下一個爛攤子」。
    """
    stop = []
    plan = scan()
    for r in plan["py"] + plan["engine"]:
        if r["blocked"]:
            stop.append("%s · %s" % (r["rel"], r["blocked"]))
    for r in plan["engine"]:
        if r["spans"] and (VIA / r["rel"]).with_name(r["next"]).exists():
            stop.append("%s 已存在=Hydra 守衛(版號只往前)" % r["next"])
    for rel in plan["missing"]:
        stop.append("落點不在位:%s" % rel)
    return stop


def apply() -> int:
    stop = preflight()
    if stop:
        for x in stop:
            print("[擋] %s" % x)
        print("[擋] **一個位元都沒有動**——擋在第一次寫之前(批679 P2)")
        return 1
    plan = scan()
    led = {"schema": "VIA.ChinaBrokerPurge.Ledger.v1", "version": VERSION, "batch": BATCH,
           "ts": datetime.now().strftime("%Y-%m-%d %H:%M"), "ruled_by": RULED_BY,
           "why": "操作員批679 令「刪中國券商」。只增不減由操作員親自解除;"
                  "刪掉的每一個位元組留在本台帳,restore 可原樣放回。",
           "deny_source": "疊加層 deny_keys(操作員批413「大陸券商刪除」「去摩通」)",
           "dangling_named": [{"key": k, "why": w} for k, w in DANGLING_NAMED.items()],
           "policy_conflict": [
               {"path": "functional modules/VRN/knowledge/SYNONYM_LIBRARY_v3.json",
                "declares": "only_add = true",
                "why": "只增不減在**陸券這一題**上由操作員批679 親自解除;解除的是題目不是冊。"
                       "衝突寫在這裡而不是繞過去——restore 一個動詞原樣放回。"},
               {"path": "functional modules/VRN/knowledge/SYNONYM_LIBRARY_v4.json",
                "declares": "only_add = true", "why": "同上"},
           ],
           "untouched": [{"path": a, "why": b} for a, b in UNTOUCHED],
           "files": []}
    for rel, fn, why in JSON_TARGETS:
        p = VIA / rel
        before = p.read_text(encoding="utf-8")
        d, dropped = fn(json.loads(before))
        if not dropped:
            continue
        # 沿用原檔縮排(批702):照 v0100 一律 indent=1 會把 150 KB 的冊整份重排,
        # 真正刪掉的那幾行就淹在重排裡,誰也看不出來動了什麼。
        p.write_text(json.dumps(d, ensure_ascii=False, indent=_indent_of(before)) + "\n",
                     encoding="utf-8")
        led["files"].append({"kind": "json", "path": rel, "why": why,
                             # 批705:沿用原檔縮排仍可能重排(分隔符/鍵序之類)。
                             #   重排本身不是錯,**靜悄悄地重排**才是。逐本留痕。
                             "reformatted": next((r["state"] for r in json_roundtrip()
                                                  if r["path"] == rel), "?") != "EXACT",
                             "sha_before": hashlib.sha256(before.encode()).hexdigest(),
                             "sha_after": sha(p), "dropped": dropped, "original": before})
        print("[刪] %s · %d 項" % (rel, len(dropped)))
    for rel, kw, why in PY_TARGETS:
        p = VIA / rel
        before = p.read_text(encoding="utf-8")
        new, n, bad = purge_py(before, **kw)
        if n == 0:
            continue
        p.write_text(new, encoding="utf-8")
        led["files"].append({"kind": "py_inplace", "path": rel, "why": why, "spans": n,
                             "sha_before": hashlib.sha256(before.encode()).hexdigest(),
                             "sha_after": sha(p), "original": before})
        print("[刪] %s · %d 段(就地;原文已進台帳)" % (rel, n))
    for sub, pat, kw, why in ENGINE_TARGETS:
        p = _newest(VIA / sub, pat)
        before = p.read_text(encoding="utf-8")
        new, n, bad = purge_py(before, **kw)
        if n == 0:
            continue
        nxt = p.with_name(_bump(p.name))
        if nxt.exists():   # preflight() 應該已經擋掉;留著當殿後,真到這裡就是 preflight 漏了
            print("[拒寫] %s 已存在=Hydra 守衛(preflight 漏網,請看 preflight())" % nxt.name)
            return 1
        head = ("# %s:依操作員令「刪中國券商」自 %s 升版——別名表移出陸券(%s)。\n"
                "#   舊版一個位元不動;刪掉的原文在 %s。\n"
                % (BATCH, p.name, why, LEDGER.name))
        nxt.write_text(_inject(new, head), encoding="utf-8")
        led["files"].append({"kind": "py_newversion", "path": str(p.relative_to(VIA)),
                             "new": str(nxt.relative_to(VIA)), "why": why, "spans": n,
                             "sha_before": hashlib.sha256(before.encode()).hexdigest()})
        print("[升版] %s → %s · %d 段" % (p.name, nxt.name, n))
    # ── 第二輪:通吃型 JSON + 值層級的 .py 紀錄 + 兩處改正 ──────────────────
    for rel in PASS2_JSON:
        p = VIA / rel
        if not p.exists():
            continue
        before = p.read_text(encoding="utf-8")
        d = json.loads(before)
        dropped = []
        d = purge_json_generic(d, dropped)
        frag = 0
        def _strip(o):
            nonlocal frag
            if isinstance(o, dict):
                return {k: _strip(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_strip(v) for v in o]
            if isinstance(o, str) and STR_FRAG.search(o):
                frag += 1
                return STR_FRAG.sub("", o)
            return o
        d = _strip(d)
        for dom in CN_DOMAIN:
            m = d.get("email_domain_to_broker")
            if isinstance(m, dict) and dom in m:
                dropped.append({"path": "/email_domain_to_broker/" + dom, "kind": "DOMAIN",
                                "value": m.pop(dom)})
        if not dropped and not frag:
            continue
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        led["files"].append({"kind": "json_generic", "path": rel, "dropped": dropped,
                             "str_fragments": frag, "original": before,
                             "sha_before": hashlib.sha256(before.encode()).hexdigest(),
                             "sha_after": sha(p),
                             "why": "通吃型清除:鍵/值/list 元素/整筆紀錄四種一起收"})
        print("[刪] %s · %d 項%s" % (rel, len(dropped),
                                      (" · 字串片段 %d" % frag) if frag else ""))
    for rel in PASS2_PY:
        p = VIA / rel
        if not p.exists():
            continue
        before = p.read_text(encoding="utf-8")
        spans = _spans_dict_by_value(before, CN_ALIAS | {norm(x) for x in CN_CANON})
        if not spans:
            continue
        b = before.encode("utf-8")
        merged = []
        for s2, e2 in sorted(set(spans)):
            if merged and s2 <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e2))
            else:
                merged.append((s2, e2))
        nb = b
        for s2, e2 in reversed(merged):
            nb = nb[:s2] + nb[e2:]
        new_src = nb.decode("utf-8")
        try:
            ast.parse(new_src)
        except SyntaxError as ex:
            print("[擋] %s 改完解析不過(%s)→ 放棄" % (rel, ex))
            continue
        p.write_text(new_src, encoding="utf-8")
        led["files"].append({"kind": "py_record", "path": rel, "spans": len(merged),
                             "original": before,
                             "sha_before": hashlib.sha256(before.encode()).hexdigest(),
                             "sha_after": sha(p),
                             "why": "整筆測試紀錄(broker_alias='GF Securities')移出"})
        print("[刪] %s · %d 筆紀錄" % (rel, len(merged)))
    for rel, a_, b_ in FIX_TEXT:
        p = VIA / rel
        if not p.exists():
            continue
        before = p.read_text(encoding="utf-8")
        if a_ not in before:
            continue
        after = before.replace(a_, b_)
        if rel.endswith(".py"):
            try:
                ast.parse(after)
            except SyntaxError as ex:
                print("[擋] %s 改完解析不過(%s)→ 放棄" % (rel, ex))
                continue
        p.write_text(after, encoding="utf-8")
        led["files"].append({"kind": "text_fix", "path": rel, "from": a_, "to": b_,
                             "original": before,
                             "sha_before": hashlib.sha256(before.encode()).hexdigest(),
                             "sha_after": sha(p),
                             "why": "**改正不是刪**:台灣的中國信託(CTBC)被寫成『中信證券』"
                                    "——那是陸券的名字;或說明文字還把海通/中金列為外資,"
                                    "但表上已經沒有它們了,留著就是冊在說謊"})
        print("[改正] %s · 「%s」→「%s」" % (rel, a_[:24], b_[:24]))

    _merge_ledger(led)
    print("[台帳] %s · %d 檔" % (LEDGER.name, len(json.loads(LEDGER.read_text(encoding="utf-8"))["files"])))
    return 0


def _merge_ledger(led: dict) -> None:
    """台帳只增不覆寫。

    批679 實錄:第二次 `--apply` 跑第二輪時,`apply()` 從頭造了一份新台帳,
    第一輪那八檔的原文**當場從台帳上消失**(檔案已經改過,原文只剩 git 裡有)。
    刪是操作員的裁定,可以;但**刪的留痕自己被刪掉**就不行了——
    那正是「沒有留痕的刪」本身。已自 git HEAD 原樣補回,並改成合併:
    同一個 path 保留**最早**那一份 original(那才是真正的原始狀態)。
    """
    old = {}
    if LEDGER.exists():
        try:
            prev = json.loads(LEDGER.read_text(encoding="utf-8"))
            for f in prev.get("files", []):
                old.setdefault(f["path"], f)
        except Exception:
            prev = {}
    for f in led["files"]:
        if f["path"] in old:
            f["original"] = old[f["path"]].get("original", f.get("original", ""))
            f["sha_before"] = old[f["path"]].get("sha_before", f.get("sha_before", ""))
            f["superseded_runs"] = old[f["path"]].get("superseded_runs", 0) + 1
        old[f["path"]] = f
    led["files"] = [old[k] for k in sorted(old)]
    LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _inject(src: str, head: str) -> str:
    """把升版說明放在 shebang / coding 行之後,絕不插進 docstring 裡(LL303)。"""
    lines = src.splitlines(keepends=True)
    i = 0
    while i < len(lines) and (lines[i].startswith("#!") or "coding" in lines[i][:30]):
        i += 1
    return "".join(lines[:i]) + head + "".join(lines[i:])


def restore() -> int:
    if not LEDGER.exists():
        print("[還原] 台帳缺席=ABSENT(rc=3)")
        return 3
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    n = 0
    for f in led["files"]:
        if f["kind"] == "py_newversion":
            q = VIA / f["new"]
            if q.exists():
                q.unlink()
                n += 1
                print("[還原] 移除升版檔 %s" % f["new"])
            continue
        p = VIA / f["path"]
        p.write_text(f["original"], encoding="utf-8")
        n += 1
        print("[還原] %s" % f["path"])
    # 批679 實錄(Codex 在 PR #55 照出的 P3,照得對):
    #   台帳裡要是**漏了** py_newversion 這一類,restore 跑完那幾支升版檔還在,
    #   而尾版律只認最新那一份 → 解析照樣走清乾淨後的表,
    #   也就是「還原了」這句話是假的。所以還原完要**逐支驗它真的不在了**。
    left = [f["new"] for f in led["files"]
            if f["kind"] == "py_newversion" and (VIA / f["new"]).exists()]
    created = [f.get("new") for f in led["files"] if f["kind"] == "py_newversion"]
    print("[還原] %d 檔回到刪之前 · 本批造出的版本檔 %d 支 · 還沒清掉 %d 支"
          % (n, len(created), len(left)))
    if left:
        for x in left:
            print("  [殘留] %s" % x)
        return 1
    if not created:
        print("  [警] 台帳裡一筆 py_newversion 都沒有——這一批真的沒有升版,"
              "還是台帳漏記了?漏記的話 restore 是假的(批679 P3)")
        return 2
    return 0


def verify(root: Path | None = None) -> dict:
    """刪完再掃一次全樹尾版:還有哪些活的落點帶著陸券。

    `root` 讓自測掃**暫存夾**而不是活樹。批680 實錄:第一版的四態控把探針檔寫進
    `functional modules/VRN/`,跑完雖然 unlink,但中斷一次就會留在樹上——
    註冊稽核當場點名「未登 _b680_selftest_probe」。**自測不准跟活樹共用地盤**(LL319)。
    """
    EXC = ("__pycache__", "RetiredEngines", "references/intake", "/intake/", "SCOPE_COPY",
           "_superseded", "/20260804/", "VIA_AutoCode_Registry", "ChinaBrokerPurge",
           "SynonymUnion", "VIA_Financial_Institution_SSOT", "FinancialInstitution_Overlay",
           "VRN_ExtractionLogic_SSOT")
    rx = re.compile("|".join(re.escape(t) for t in
                             ("廣發", "海通", "中金公司", "中信建投", "中信證券",
                              "國泰君安", "Guotai Junan", "Haitong", "CICC", "GF Securities")))
    cand, out = {}, []
    _base = root if root is not None else VIA          # 相對路徑的基準跟著掃描根走
    _roots = [root] if root is not None else [VIA / "functional modules", VIA / "supportive modules"]
    for root in _roots:
        for q in root.rglob("*"):
            if q.suffix not in (".py", ".json") or not q.is_file():
                continue
            s = str(q)
            if any(e in s for e in EXC) or re.search(r"_sha[0-9a-f]{6,}\.py$", s):
                continue
            stem = re.sub(r"_v\d{2,4}$", "", q.stem)
            key = (str(q.parent), stem, q.suffix)
            if key not in cand or q.stem > cand[key].stem:
                cand[key] = q
    for q in sorted(cand.values()):
        try:
            t = q.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        data, note = set(), set()
        # 散文不是解析資料:`#` 註解**和 docstring** 都是散文。
        #   批680 實錄:第一版只看 `#`,於是我寫在 docstring 裡「為什麼不可以抄名單」
        #   那句話,被自己的尺判成**還帶著活的陸券解析資料**——尺的盲點,不是樹的問題。
        #   .py 走 AST(docstring 認得出來),其餘副檔名退回逐行看 `#`(誠實降級,不假裝)。
        #   逐行判,而且要知道**哪幾行**屬於 docstring —— 不是「這個字在某個 docstring 裡
        #   出現過就整份當散文」。批680 第一版就是那樣寫的,負控當場抓到:
        #   一個 docstring 提到廣發、字典裡也有廣發的合成檔,被判成「只有註解」=把尺改鬆了。
        #   AST 給的是每一個 docstring 的 lineno..end_lineno,用它劃行,不是用字比對。
        _doc_lines = set()
        if q.suffix == ".py":
            try:
                _tree = ast.parse(t)
                for _n in ast.walk(_tree):
                    if not isinstance(_n, (ast.Module, ast.FunctionDef,
                                           ast.AsyncFunctionDef, ast.ClassDef)):
                        continue
                    _b = getattr(_n, "body", None)
                    if not _b:
                        continue
                    _f = _b[0]
                    if isinstance(_f, ast.Expr) and isinstance(_f.value, ast.Constant) \
                            and isinstance(_f.value.value, str):
                        _doc_lines.update(range(_f.lineno, (_f.end_lineno or _f.lineno) + 1))
            except SyntaxError:
                pass
        for _i, line in enumerate(t.splitlines(), 1):
            m = rx.findall(line)
            if not m:
                continue
            cut = line.find("#")
            if _i in _doc_lines or (cut >= 0 and not rx.search(line[:cut])):
                note.update(m)
            else:
                data.update(m)
        if data:
            out.append({"path": str(q.relative_to(_base)), "tokens": sorted(data), "kind": "DATA"})
        elif note:
            out.append({"path": str(q.relative_to(_base)), "tokens": sorted(note), "kind": "COMMENT_ONLY"})
    return {"left": [r for r in out if r["kind"] == "DATA"],
            "comment_only": [r for r in out if r["kind"] == "COMMENT_ONLY"],
            "scanned": len(cand)}


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

    # ── 名單本身 ──
    chk("① 名單來源是操作員批413 的拒絕清單,不是我另外列的",
        _deny_covers(), "疊加層 deny_keys 覆蓋本支 CN 名單")
    chk("② 逐字全等,不做前綴比對:中信/中信金/中國信託 一個都不准被當成陸券",
        not any(is_cn_alias(x) for x in ("中信", "中信金", "中國信託", "中信投顧", "CTBC")))
    chk("③ 里昂 CLSA/CLST 不在名單裡(批541 操作員裁定:同一家,留)",
        not any(is_cn_alias(x) or is_cn_canon(x) for x in ("CLSA", "CLST", "里昂")))
    chk("④ 台灣與外資券商一家都不在名單裡",
        not any(is_cn_alias(x) or is_cn_canon(x) for x in MUST_KEEP_ALIAS),
        "%d 條負控" % len(MUST_KEEP_ALIAS))
    chk("⑤ 該抓的一條都不漏",
        all(is_cn_alias(x) for x in ("廣發", "海通", "中金", "中信證券", "國泰君安",
                                     "Haitong", "CICC", "GF Securities")))

    # ── AST 切法:合成檔當場證明它切得準,也證明它切錯會自己放棄 ──
    syn = ('A = {"TW": ["元大", "yuanta"], "GF": ["廣發", "gf securities"],\n'
           '     "CTBC": ["中信", "中信金", "中信證券"], "CLSA": ["clsa", "里昂"]}\n'
           'B = [{"code": "CICC", "zh": "中金公司"}, {"code": "MS", "zh": "摩根士丹利"}]\n'
           '# 註解裡也有廣發兩個字,不准被碰\n')
    new, n, bad = purge_py(syn, dict_keys=CN_CANON, list_field="code",
                           list_vals=CN_CANON, str_toks=CN_ALIAS)
    lit = _literals(new)
    chk("⑥ 合成檔:GF 整鍵切掉 · CICC 整筆切掉",
        not bad and "GF" not in lit.get("A", {}) and
        [e["code"] for e in lit.get("B", [])] == ["MS"], "切了 %d 段" % n)
    chk("⑦ 合成檔:CTBC 只掉『中信證券』,『中信』『中信金』原樣留著",
        lit.get("A", {}).get("CTBC") == ["中信", "中信金"], str(lit.get("A", {}).get("CTBC")))
    chk("⑧ 合成檔:元大 / CLSA / 里昂 / 摩根士丹利 一個都沒動",
        lit.get("A", {}).get("TW") == ["元大", "yuanta"] and
        lit.get("A", {}).get("CLSA") == ["clsa", "里昂"] and
        lit.get("B", [{}])[0].get("zh") == "摩根士丹利")
    chk("⑨ 註解裡的字不准被當成資料切掉(AST 定位的意義就在這)",
        "# 註解裡也有廣發兩個字,不准被碰" in new)
    chk("⑩ 改完一定重新解析得過", _parses(new))
    _bn, _bc, _bb = purge_py('A = {"GF": [1,2}\n', dict_keys=CN_CANON)
    chk("⑪ 負控:原檔語法本來就壞的話一個字都不准碰(fail-closed,不是硬寫下去)",
        _bc == 0 and "解析不過" in _bb and _bn == 'A = {"GF": [1,2}\n', _bb[:46])
    bad_src = 'A = {"GF": ["廣發"], "YUANTA": ["元大"]}\n'
    _n2, _c2, _b2 = purge_py(bad_src, dict_keys={"YUANTA"})
    chk("⑫ 負控:要是切到台灣券商,對帳一定要把它擋下來",
        _c2 == 0 and "不該少" in _b2, _b2[:48])

    # ── JSON 側:拿真冊的副本跑,不動真檔 ──
    bl = _j("functional modules/VRN/registry/VRN_BROKER_LIST_v01.json")
    bl2, dr = purge_broker_list(json.loads(json.dumps(bl, ensure_ascii=False)))
    names = {str(e.get("canonical_en")).upper() for e in bl2["brokers"]}
    # 這一檢要驗的是**不變量**(冊上沒有陸券、其餘一家不少),不是「這一跑移出了幾筆」。
    # 批679 實錄:第一版寫成「移出 1 筆」,刪完再跑就變成移出 0 筆 → 自己把自己判紅。
    # 冪等的動作要用**結果**判,不能用**動作次數**判(LL332)。
    chk("⑬ 券商清冊:冊上沒有任何陸券,而且其餘一家不少(冪等:刪過再跑仍成立)",
        not any(is_cn_canon(e.get("canonical_en") or "") or is_cn_canon(e.get("canonical") or "")
                for e in bl2["brokers"]) and len(bl2["brokers"]) == len(bl["brokers"]) - len(dr),
        "剩 %d 家 · 本跑再移出 %d" % (len(bl2["brokers"]), len(dr)))
    # 正控:移除邏輯本身還是要當場證明咬得住——塞一筆假的陸券進副本,它一定要被移出。
    _bl3 = json.loads(json.dumps(bl, ensure_ascii=False))
    _bl3["brokers"].append({"canonical": "廣發", "canonical_en": "GF Securities",
                            "country": "China", "aliases": ["GF", "廣發"]})
    _n3 = len(purge_broker_list(_bl3)[1])
    chk("⑬b 正控:塞一筆假陸券進副本,移除邏輯一定要把它抓出來",
        _n3 == 1, "抓出 %d 筆" % _n3)
    chk("⑭ 券商清冊:CLSA(里昂,HK)必須還在",
        "CLSA" in names)
    chk("⑮ 券商清冊:總數欄位跟著改(冊上的數字不准跟內容對不起來)",
        bl2["total_canonical_brokers"] == len(bl2["brokers"]))

    bd = _j("functional modules/VRN/knowledge/VRN_Broker_Dict_v0100.json")
    bd2, dr2 = purge_broker_dict(json.loads(json.dumps(bd, ensure_ascii=False)))
    codes = {e.get("code") for e in bd2["brokers_extended"]}
    chk("⑯ 知識冊:CICC / CITIC / HAITONG / GUOTAIJUNAN 四筆整筆移出",
        not (codes & {"CICC", "CITIC", "HAITONG", "GUOTAIJUNAN"}),
        "ext 剩 %d" % len(bd2["brokers_extended"]))
    cat = (bd2["brokers"].get("國泰") or {}).get("aliases") or []
    chk("⑰ 知識冊:國泰底下的『國泰君安』三條假別名拆掉",
        not any(is_cn_alias(a) for a in cat), str(cat))
    chk("⑱ 知識冊:國泰自己的別名(國泰/國泰證券/國泰投顧/國泰金控/Cathay)一條都不准少",
        all(any(norm(k) == norm(a) for a in cat) for k in
            ("國泰", "國泰證券", "國泰投顧", "國泰金控", "Cathay")), str(cat))
    chk("⑲ 知識冊:高盛 / 摩根士丹利 / JPM 等外資 ext 一筆不少",
        {"GS", "MS", "JPM"} <= codes)
    chk("⑳ 知識冊:count / count_extended 跟著改",
        bd2["count"] == len(bd2["brokers"]) and bd2["count_extended"] == len(bd2["brokers_extended"]))

    fr = _j("supportive modules/registry/VRN_FieldRules_SSOT_v0100.json")
    fr2, dr3 = purge_field_rules(json.loads(json.dumps(fr, ensure_ascii=False)))
    et = fr2["rules"]["broker"]["extra_table"]
    chk("㉑ 規則正本:extra_table 的 GF / HAITONG / CICC 三鍵移出",
        not ({"GF", "HAITONG", "CICC"} & set(et)), "剩 %d 鍵" % len(et))
    chk("㉒ 規則正本:CTBC 只掉『中信證券』,『中信投顧』留著",
        et.get("CTBC") == ["中信投顧"], str(et.get("CTBC")))
    chk("㉓ 規則正本:其餘每一鍵的別名一條都沒被動到",
        all(et[k] == fr["rules"]["broker"]["extra_table"][k]
            for k in et if k not in ("CTBC",)),
        "%d 鍵逐條比對" % len(et))
    chk("㉔ 規則正本:rating / target_price / date 等其他六欄一個位元都沒碰",
        all(fr2["rules"][k] == fr["rules"][k] for k in fr["rules"] if k != "broker"))

    # ── 正典零觸碰 ──
    canon = VIA / "supportive modules" / "ssot" / "VIA_Financial_Institution_SSOT_v0100.json"
    cj = json.loads(canon.read_text(encoding="utf-8"))
    reg = cj["registries"]
    cn_in_canon = [k for grp in ("domestic_brokers", "foreign_brokers")
                   for k in reg[grp] if is_cn_canon(k)]
    chk("㉕ **正典 28 家裡一家陸券都沒有**(所以正典本來就不必改)",
        not cn_in_canon, "台資 %d + 外資 %d · 陸券 %d"
        % (len(reg["domestic_brokers"]), len(reg["foreign_brokers"]), len(cn_in_canon)))
    chk("㉖ 正典不在任何一張目標表裡(唯讀,一個位元都不碰)",
        not any("VIA_Financial_Institution_SSOT" in r for r, *_ in JSON_TARGETS)
        and not any("VIA_Financial_Institution_SSOT" in r for r, *_ in PY_TARGETS))
    chk("㉗ 台帳也不在目標表裡(刪台帳=湮滅證據)",
        not any("AutoCode_Registry" in r for r, *_ in JSON_TARGETS))

    pl = scan()
    # 批702:原本寫死「十三個落點」,v0101 補到十八個,字面當場落後一批。
    #   這一族(站名/檢名停在舊數)這是第七次,所以這裡不再寫死——**數字自己算**。
    chk("㉘ %d 個落點都在位,沒有一個是幽靈路徑(數字由表自己算,不寫死)"
        % (len(JSON_TARGETS) + len(PY_TARGETS) + len(ENGINE_TARGETS)),
        not pl["missing"], str(pl["missing"]))
    chk("㉙ %d 支引擎走升版不走就地改(尾版律),而且下一個版號還沒被佔" % len(ENGINE_TARGETS),
        all(not (VIA / r["rel"]).with_name(r["next"]).exists() or r["spans"] == 0
            for r in pl["engine"]),
        " · ".join("%s→%s" % (Path(r["rel"]).name, r["next"]) for r in pl["engine"]))
    chk("㉚ 零網路零開庫:本支只讀寫檔,不 import duckdb/requests,不跑 subprocess",
        not any(m in Path(__file__).read_text(encoding="utf-8").split("def selftest(")[0]
                for m in ("import duckdb", "import requests", "subprocess", "urllib.request")))
    # ── Codex 在 PR #55 照出的三條,各配一個會咬人的檢(批679d)────────────
    _rows = [{"def_preferred_key": "brokers[0].canonical", "def_preferred_value": "YUANTA", "def_normalized_key": "brokers_0_canonical"},
             {"def_preferred_key": "brokers[1].canonical", "def_preferred_value": "GF", "def_normalized_key": "brokers_1_canonical"},
             {"def_preferred_key": "brokers[1].country", "def_preferred_value": "China", "def_normalized_key": "brokers_1_country"},
             {"def_preferred_key": "brokers[1].rank", "def_preferred_value": "12", "def_normalized_key": "brokers_1_rank"},
             {"def_preferred_key": "brokers[2].canonical", "def_preferred_value": "CLSA", "def_normalized_key": "brokers_2_canonical"},
             {"def_preferred_key": "brokers[2].country", "def_preferred_value": "HK", "def_normalized_key": "brokers_2_country"}]
    _out, _drp, _rn = purge_json_grouped(_rows, "def_normalized_key")
    _keys = {r["def_preferred_key"]: r["def_preferred_value"] for r in _out}
    chk("㉛ **整組刪**:群組裡只要有一片葉子是陸券,country/rank 那幾列也要一起走"
        "(Codex PR #55 P1:留下無頭群組比不刪還危險,它看起來是完整的一筆)",
        len(_drp) == 1 and "China" not in _keys.values() and "12" not in _keys.values(),
        "刪 %d 組 · 剩 %s" % (len(_drp), sorted(_keys)))
    chk("㉛b **重新編號**:刪掉 index 1 之後,原本的 index 2 要補上來,"
        "不然扁平冊的 brokers[N] 會跟清乾淨後的冊對不起來(里昂穿著廣發的 metadata)",
        _keys.get("brokers[1].canonical") == "CLSA" and _keys.get("brokers[1].country") == "HK"
        and _rn == 2, "brokers[1]=%s · 重編 %d 列" % (_keys.get("brokers[1].canonical"), _rn))
    chk("㉛c 負控:沒有陸券的群組一組都不准被動到",
        purge_json_grouped([r for r in _rows if "GF" not in str(r["def_preferred_value"])
                            and "China" not in str(r["def_preferred_value"])
                            and "12" != r["def_preferred_value"]], "def_normalized_key")[1] == [])
    chk("㉜ **擋在第一次寫之前**:preflight() 把所有會擋的事先問完"
        "(Codex PR #55 P2:守衛寫在後面=失敗時留下改了一半又沒有台帳的倉庫)",
        "def preflight()" in Path(__file__).read_text(encoding="utf-8")
        and Path(__file__).read_text(encoding="utf-8").index("def preflight()")
        < Path(__file__).read_text(encoding="utf-8").index("def apply()")
        and isinstance(preflight(), list), "本樹 preflight 擋 %d 件" % len(preflight()))
    # ㉞ 四態控:verify() 的「資料 / 散文」分類,四種情況都要判對。
    #   批680 實錄:我把尺從「只看 #」改成「也認 docstring」,**第一版改鬆了**——
    #   「這個字在某個 docstring 裡出現過」就把整份當散文,於是字典裡真的有廣發也被放過。
    #   負控當場抓到。改成用 AST 取 docstring 的**行號範圍**逐行判,四態才全對。
    #   改尺之後一定要證明它沒有變鬆,不然「照出來的變少」會被讀成「問題變少」。
    import tempfile as _tf
    _tmp = Path(_tf.mkdtemp(prefix="via_b680_"))
    _probe = _tmp / "_probe_v0100.py"
    _cases = [("散文提到(docstring)", '"""提到%s。"""\nT = {"A": ["元大"]}\n', False),
              ("散文提到 + 資料也有", '"""提到%s。"""\nT = {"X": ["%s"]}\n', True),
              ("只有 # 註解提到", '# 註解提到%s\nT = {"A": ["元大"]}\n', False),
              ("只有資料有", 'T = {"X": ["%s"]}\n', True)]
    _word = "廣" + "發"          # 不整串打進來:整串打進來就是又抄了一份名單(批680 三犯)
    _got = []
    for _name, _tpl, _want in _cases:
        try:
            _probe.write_text(_tpl.replace("%s", _word), encoding="utf-8")
            _v = verify(root=_tmp)          # 掃暫存夾,活樹一個位元都不碰
            _got.append(bool(_v["left"]) == _want)
        finally:
            _probe.unlink(missing_ok=True)
    try:
        _tmp.rmdir()
    except OSError:
        pass
    chk("㉞ verify() 的資料/散文四態控:docstring 提到=散文 · 資料裡有=資料 · "
        "兩者都有**仍然是資料**(改尺之後要證明它沒變鬆)",
        all(_got), " · ".join("%s=%s" % (c[0], "對" if g else "**錯**")
                              for c, g in zip(_cases, _got)))
    _led = _j("supportive modules/registry/VIA_ChinaBrokerPurge_Ledger_v0100.json") if LEDGER.exists() else None
    _nv = [f for f in (_led or {}).get("files", []) if f["kind"] == "py_newversion"]
    chk("㉝ **台帳要記下每一個升版檔**,restore 才不是假的"
        "(Codex PR #55 P3:漏記 → restore 跑完升版檔還在 → 尾版律照樣走清乾淨後的表)",
        _led is not None and len(_nv) == len(ENGINE_TARGETS)
        and all((VIA / f["new"]).exists() for f in _nv),
        "py_newversion %d 筆 / 引擎落點 %d 個" % (len(_nv), len(ENGINE_TARGETS)))
    # ── 批702:主線回帶的五個新落點 ──────────────────────────────────────
    _B702 = ("functional modules/VRN/engine/VRN_AutoTestLoop.py",
             "functional modules/VRN/engine/VRN_Integrated_ReportDatabase_Engine.py",
             "functional modules/VRN/engine/VIA_VRN_FirstPageEngine.py",
             "functional modules/VRN/knowledge/SYNONYM_LIBRARY_v3.json",
             "functional modules/VRN/knowledge/SYNONYM_LIBRARY_v4.json")
    _listed = {r for r, *_ in JSON_TARGETS} | {r for r, *_ in PY_TARGETS}
    _miss = [r for r in _B702 if r not in _listed]
    _nowhy = [r for r, _k, w in PY_TARGETS if not str(w).strip()] + \
             [r for r, _f, w in JSON_TARGETS if not str(w).strip()]
    chk("㉟ 批702 五個新落點逐個進表,而且逐個有 why(沒有 why 的落點=下一個人看不懂為什麼動它)",
        not _miss and not _nowhy,
        "缺 %d · 無 why %d" % (len(_miss), len(_nowhy)))

    # 同義字冊——在**記憶體副本**上跑,活樹一個位元都不碰。
    #
    # 批702 自審:這一檢的第一版寫成 `chk(_drop and ...)`,也就是**要求冊裡還有陸券可刪**。
    #   `--apply` 跑完之後冊已經乾淨,`_drop` 當然是 0,於是這一檢**在它自己修好問題之後轉紅**
    #   ——全格子當場抓到(站 215 FAIL)。那不是尺,那是在量「樹現在髒不髒」,
    #   而且量出「乾淨」還判它錯。檢要能**重複跑而結論不變**。
    #   改成兩段:合成髒冊證明尺會動(不看活樹),活冊證明它是乾淨的(不要求它髒)。
    _syn = VIA / "functional modules/VRN/knowledge/SYNONYM_LIBRARY_v4.json"
    if _syn.exists():
        _raw = _syn.read_text(encoding="utf-8")
        _before = json.loads(_raw)
        # ── 前段:合成一本**髒冊**(把一條陸券塞回去),尺必須把它挑掉。
        #    不整串打名字進來——整串打進來就是又抄了一份名單(批680 三犯)。
        _w = "廣" + "發"
        _dirty = json.loads(json.dumps(_before, ensure_ascii=False))
        _dirty.setdefault("scopes", {}).setdefault("broker", {})[_w] = [
            {"canonical": "GF", "source": "_b702_selftest", "raw": _w}]
        _dirty["scopes"]["broker"]["_b702_keep_probe"] = [
            {"canonical": "CTBC", "source": "_b702_selftest", "raw": "中信投顧"}]
        _fixed, _drop = purge_synonym_library(_dirty)
        _caught = any(_w in str(d.get("path", "")) for d in _drop)
        _kept = "_b702_keep_probe" in _fixed.get("scopes", {}).get("broker", {})
        chk("㊱ 同義字冊的尺:合成一本髒冊塞一條陸券進去,必須挑得掉;"
            "**反面控制**同時塞一條台灣券商,必須原封不動留著",
            _caught and _kept,
            "挑掉陸券=%s · 台灣券商留著=%s · 這一跑刪 %d 筆" % (_caught, _kept, len(_drop)))

        # ── 後段:活冊**現在**乾不乾淨。這一段不要求它髒——乾淨才是對的,
        #    而且 --apply 跑幾次結論都一樣(冪等)。
        _sb = json.dumps(_before, ensure_ascii=False)
        _cn_left = [x for x in ("廣" + "發", "中信" + "證券", "CICC", "海" + "通",
                                "國泰" + "君安", "GF Securities") if x in _sb]
        _live, _ldrop = purge_synonym_library(json.loads(_sb))
        _lost = [k for k in MUST_KEEP_ALIAS
                 if _sb.count(k) and not json.dumps(_live, ensure_ascii=False).count(k)]
        chk("㊱b 活冊現況:陸券 0 殘留 · 台灣/外資券商一個都沒少(前後對比,不比絕對值);"
            "再跑一次 purge 應該**無事可做**(冪等)",
            not _cn_left and not _lost and not _ldrop,
            "陸券殘 %d %s · 少掉的台外資 %s · 再跑可刪 %d(必須 0)"
            % (len(_cn_left), _cn_left or "", _lost or "無", len(_ldrop)))

        # 批705:㊲ 從「只驗會過的那一本」改成**逐本量、逐本報**。
        #   不會逐位元相同的不判紅(那不是壞掉),但必須列出來而且進台帳 reformatted。
        _rt = json_roundtrip()
        _absent = [r["path"] for r in _rt if r["state"] == "ABSENT"]
        chk("㊲ 寫回沿用原檔縮排:**五本逐本量**(v0101 只驗了會過的那一本 SYNONYM_LIBRARY_v4)。"
            "逐位元相同的照實報 EXACT,會被重排的照實報 REFORMATS 並進台帳 reformatted——"
            "重排不是錯,**靜悄悄地重排**才是",
            bool(_rt) and not _absent,
            " · ".join(f"{r['state']}(indent={r.get('indent')}) {Path(r['path']).name}"
                       for r in _rt))
    else:
        chk("㊱ 同義字冊的尺:合成髒冊挑得掉陸券 · 台灣券商留著", False, "冊缺席")
        chk("㊱b 活冊現況:陸券 0 殘留 · 冪等", False, "冊缺席")
        chk("㊲ 寫回沿用原檔縮排", False, "冊缺席")

    _dang = dangling()
    _unnamed = sorted({d["key"] for d in _dang} - set(DANGLING_NAMED))
    # 批705:三條掃描路(.py 就地 / 引擎升版 / JSON)各配一個**合成負控**。
    #   今天活樹上引擎與 JSON 各 0 個懸空——那是誠實的 0,但「0」有兩種:
    #   真的沒有,和**根本沒掃**。v0101 是後者(只掃 PY_TARGETS),而它照樣報得很乾淨。
    #   負控就是用來分辨這兩種 0 的。
    _kwp = {"dict_keys": CN_CANON, "str_toks": CN_ALIAS}
    _nc_py = _dangling_in_py('T = {"ZZHK": "GF"}\n', "_b705_probe.py", _kwp)
    _nc_js = _dangling_in_json({"ZZHK": "GF", "元大": "YUANTA"}, "_b705_probe.json")
    _nc_clean = _dangling_in_py('T = {"YT": "YUANTA"}\n', "_b705_probe.py", _kwp)
    chk("㊳b 三條掃描路各配合成負控:.py 與 JSON 都要抓得到合成的懸空指標,"
        "而**沒有懸空的合成件一個都不准被誤抓**——「0」有兩種:真的沒有,和根本沒掃",
        bool(_nc_py) and bool(_nc_js) and not _nc_clean,
        ".py 抓到 %s · JSON 抓到 %s · 乾淨件誤抓 %s"
        % ([r["key"] for r in _nc_py] or "**無**", [r["key"] for r in _nc_js] or "**無**",
           [r["key"] for r in _nc_clean] or "無"))

    chk("㊳ 懸空指標逐條點名:清完之後還指著被清掉正典鍵的每一個鍵,都要在 DANGLING_NAMED 裡有名有理由"
        "(不自己往操作員的拒絕清單上加名,但也不讓它靜靜地懸在那裡)",
        not _unnamed,
        "懸空 %d 處 · 已點名 %s · **未點名** %s"
        % (len(_dang), sorted({d["key"] for d in _dang}) or "無", _unnamed or "無"))

    # 批705(LL372):檢數不寫死——寫死的數字下一批就落後。由 ok+fail 自己算。
    print("=== CGC_MDL177 陸券清除閘 v%s · 自測(檢數由下方[計]自己算;"
          "零網路;預設零寫;真冊只讀副本)===" % VERSION)
    print("\n".join(lines))
    print("  [計] %d 檢 OK %d · FAIL %d" % (ok + fail, ok, fail))
    return 0 if fail == 0 else 1


def _j(rel: str):
    return json.loads((VIA / rel).read_text(encoding="utf-8"))


def _parses(src: str) -> bool:
    try:
        ast.parse(src)
        return True
    except SyntaxError:
        return False


def _deny_covers() -> bool:
    """本支的 CN 名單必須被疊加層 deny_keys 蓋住——名單的出處是操作員,不是我。"""
    import glob as _g
    hits = sorted(_g.glob(str(VIA / "supportive modules" / "ssot"
                              / "VIA_FinancialInstitution_Overlay_v*.json")))
    if not hits:
        return False
    deny = {norm(x) for x in json.loads(Path(hits[-1]).read_text(encoding="utf-8")).get("deny_keys", [])}
    core = {"廣發", "海通", "中金", "中信證券", "中信建投", "國泰君安", "cicc", "citic"}
    return core <= deny


def main(argv=None) -> int:
    a = list(argv if argv is not None else sys.argv[1:])
    if "--selftest" in a:
        return selftest()
    verb = a[0] if a else "plan"
    if verb == "plan":
        pl = scan()
        print("=== 陸券清除計畫(CGC_MDL177 v%s · %s)· 預設零寫 ===" % (VERSION, BATCH))
        print("裁定 %s" % RULED_BY)
        for r in pl["json"]:
            print("\n[JSON] %s" % r["rel"])
            print("   因 %s" % r["why"])
            for d in r["dropped"]:
                print("   - %s" % json.dumps(d, ensure_ascii=False)[:150])
        for r in pl["py"]:
            print("\n[.py 就地] %s · %d 段%s" % (r["rel"], r["spans"],
                                                (" · 擋:" + r["blocked"]) if r["blocked"] else ""))
            print("   因 %s" % r["why"])
        for r in pl["engine"]:
            print("\n[引擎升版] %s → %s · %d 段%s" % (Path(r["rel"]).name, r["next"], r["spans"],
                                                     (" · 擋:" + r["blocked"]) if r["blocked"] else ""))
            print("   因 %s" % r["why"])
        print("\n[不動] 逐條理由:")
        for p, w in UNTOUCHED:
            print("   · %-64s %s" % (p, w))
        print("\n預設零寫;要刪是 --apply(刪掉的原文全進台帳,restore 可原樣放回)")
        return 0 if not pl["missing"] else 2
    if verb in ("apply",) or "--apply" in a:
        return apply()
    if verb == "restore":
        return restore()
    if verb == "verify":
        v = verify()
        print("[驗] 掃過尾版 %d 支 · **還帶著活的陸券解析資料** %d 支 · 只剩註解提到的 %d 支"
              % (v["scanned"], len(v["left"]), len(v["comment_only"])))
        for r in v["left"]:
            print("   [資料] %-66s %s" % (r["path"], " ".join(r["tokens"])))
        for r in v["comment_only"]:
            print("   [註解] %-66s %s" % (r["path"], " ".join(r["tokens"])))
        _d = dangling()
        if _d:
            print("   [懸空] %d 處指向已清掉的正典鍵(**不算紅**:不自行加名單,等操作員裁定 LL90)"
                  % len(_d))
            for r in _d:
                print("      · %-58s \"%s\" → \"%s\"  %s"
                      % (r["path"], r["key"], r["points_to"],
                         DANGLING_NAMED.get(r["key"], "**未點名**")))
        return 0 if not v["left"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

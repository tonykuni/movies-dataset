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

VERSION = "0100"
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
           "untouched": [{"path": a, "why": b} for a, b in UNTOUCHED],
           "files": []}
    for rel, fn, why in JSON_TARGETS:
        p = VIA / rel
        before = p.read_text(encoding="utf-8")
        d, dropped = fn(json.loads(before))
        if not dropped:
            continue
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        led["files"].append({"kind": "json", "path": rel, "why": why,
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
    chk("㉘ 十三個落點都在位,沒有一個是幽靈路徑",
        not pl["missing"], str(pl["missing"]))
    chk("㉙ 三支引擎走升版不走就地改(尾版律),而且下一個版號還沒被佔",
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
    print("=== CGC_MDL177 陸券清除閘 v%s · 卅七檢自測(零網路;預設零寫;真冊只讀副本)===" % VERSION)
    print("\n".join(lines))
    print("  [計] 卅七檢 OK %d · FAIL %d" % (ok, fail))
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
        return 0 if not v["left"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

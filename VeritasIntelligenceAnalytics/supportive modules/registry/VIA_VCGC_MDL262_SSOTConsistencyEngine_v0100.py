#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_VCGC_MDL262_SSOTConsistencyEngine v0100 — 多系統 SSOT 一致性引擎(正則 · 同義字 · 編號的跨來源偵測、案號帳、血緣檢視)

操作員政策(2026-11-13):「母子系統一律獨立、互不影響、獨立開發進度 · 由 VCGC 進行衝突偵測及給編號 · 由我跟 AI 解決衝突 ·
  給編號具備政策性,所有都要服從」「在所有系統獨立性前提下建立此系統 · 高自動化 · 低風險 · 想 30 個潛在失敗情境及解決方案完善它」。
這是 VCGC 自己的模組(系統對等獨立,L123 · L128 · L129;檔名照 L133):對 VDF / VRN / VAP / VQG 只讀它們自報的冊,不寫、不改、不匯入它們的程式,也不代修。
它不發號:SSOT 號只由 CGC_MDL237 中央編號發(收件走 CGC_MDL278);本檔補的是中央檢測之外的四件事:
  ① 正則關係精確證明(有限自動機;不靠取樣猜):相等 / 子集 / 超集 / 交叉 / 互斥,附最短反例字串。
     支援不了的語法(反向參照 · 字界 \b · 內嵌錨點 …)照實回 UNPROVEN,不給綠。
  ② 靜態風險:ReDoS(巢狀量詞的二義性證明)· 方言漂移(Python 的 \d \w \s 收全形與他國字元,DuckDB / RE2 不收)·
     `$` 放過結尾換行 · 死分支。引擎自己用自動機比對樣本,不讓有回溯風險的式子去跑長字串。
  ③ 多來源血緣:同一鍵 / 同一概念在各系統各自一列,值相同也不合併、不併號;採信值照位階(LOCKED → 已發號 → 中央冊 → 候選 → 自報 → 提案),
     不用「最後寫入者贏」。
  ④ 衝突案號帳:案號 = 內容定址(同一衝突重跑得到同一號,冪等);帳只增、每列串雜湊;裁定要帶操作員原話,
     引擎從不自己裁定;證據變了裁定自動失效;來源缺席時不結案。
用法(從任何目錄):
  python VIA_VCGC_MDL262_SSOTConsistencyEngine_v0100.py check [--apply] [--json]   偵測(預設零寫);--apply 才把案帳補上、寫報表
  ... view <鍵或概念>          血緣檢視(採信值 + 各來源 + 關係 + 案號)
  ... probe <提案檔.json>      沙盒:把一份提案跟現行各冊比(零寫)
  ... cases [--all]            案帳現況
  ... rule <案號> --decision <KEEP_GOLDEN|ADOPT_NEW|SCOPE_SPLIT|ALIAS|WAIVE> --order "<操作員原話>" [--note ..] [--apply]
  ... ledger                   案帳完整性(雜湊鏈 · 殘尾)
  ... fmea                     30 個失敗情境與防護
  ... --selftest               自測(暫存夾;不碰真冊)
零網路 · 純標準庫 · 不裝套件 · 不碰 TA-Lib · 同意閘不讀不寫 · 寫入只限自己的案帳與 VIA_Reports/ssot_consistency。
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
import bisect
import contextlib
import datetime
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

try:                                    # Python 3.11+
    import re._constants as _sc
    import re._parser as _sp
except ImportError:                     # 舊版
    import sre_constants as _sc
    import sre_parse as _sp

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
ENGINE = "VIA_VCGC_MDL262_SSOTConsistencyEngine"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
SOURCES_GLOB = "VIA_SSOT_ConsistencyEngine_Sources_SSOT_v[0-9][0-9][0-9][0-9].json"
FMEA_GLOB = "VIA_SSOT_ConsistencyEngine_FailureModes_SSOT_v[0-9][0-9][0-9][0-9].json"
LEDGER_NAME = "VIA_SSOT_ConflictLedger_v0100.jsonl"
REPORT_DIR = ("VIA_Reports", "ssot_consistency")

MAXU = 0x10FFFF
MAX_STATES = 3000          # 單一自動機狀態上限(超過 = UNPROVEN,不硬算)
MAX_PRODUCT = 6000         # 乘積探索上限
REPEAT_CAP = 64            # {m,n} 展開上限
ALT_CAP = 64               # 邊界錨點分配後的分支上限
TIME_BUDGET = 90.0         # 整輪證明的時間預算(秒);用完的對一律 UNPROVEN
SAMPLE_MAX = 256           # 樣本長度上限
LOCK_STALE_SEC = 600
RANKS = ["LOCKED", "NUMBERED", "CENTRAL", "CANDIDATE", "SELF_REPORT", "PROPOSAL"]
DECISIONS = ("KEEP_GOLDEN", "ADOPT_NEW", "SCOPE_SPLIT", "ALIAS", "WAIVE")
FAMILIES = ("正則", "同義字", "編號", "來源")
SEV_ORDER = {"RED": 2, "YELLOW": 1}


class Unsupported(Exception):
    """這個式子(或這一對)超出可證範圍;呼叫端一律當 UNPROVEN,不是綠。"""


# ============================================================================================
# 一、字元集合(碼位區間)
# ============================================================================================
def iv_norm(ivs) -> tuple:
    out = []
    for lo, hi in sorted(ivs):
        if out and lo <= out[-1][1] + 1:
            if hi > out[-1][1]:
                out[-1] = (out[-1][0], hi)
        else:
            out.append((lo, hi))
    return tuple(out)


def iv_neg(ivs) -> tuple:
    out, p = [], 0
    for lo, hi in ivs:
        if lo > p:
            out.append((p, lo - 1))
        p = hi + 1
    if p <= MAXU:
        out.append((p, MAXU))
    return tuple(out)


def iv_has(ivs, c: int) -> bool:
    i = bisect.bisect_right(ivs, (c, MAXU + 1)) - 1
    return i >= 0 and ivs[i][0] <= c <= ivs[i][1]


ALL_IV = ((0, MAXU),)
_ALLCHARS = None
_ORACLE: dict = {}
_ASCII_CAT = {"CATEGORY_DIGIT": ((48, 57),), "CATEGORY_SPACE": ((9, 13), (32, 32)),
              "CATEGORY_WORD": ((48, 57), (65, 90), (95, 95), (97, 122))}
_CAT_TEXT = {"CATEGORY_DIGIT": r"\d", "CATEGORY_SPACE": r"\s", "CATEGORY_WORD": r"\w",
             "CATEGORY_NOT_DIGIT": r"\D", "CATEGORY_NOT_SPACE": r"\S", "CATEGORY_NOT_WORD": r"\W"}


def _oracle(single: str, flags: int) -> tuple:
    """單一字元類的收字集合:直接問 Python 的 re(對全部碼位掃一遍),不自己模擬大小寫摺疊與 Unicode 類別。"""
    global _ALLCHARS
    key = (single, flags)
    hit = _ORACLE.get(key)
    if hit is None:
        if _ALLCHARS is None:
            _ALLCHARS = "".join(map(chr, range(MAXU + 1)))
        out = []
        for ch in re.compile(single, flags).findall(_ALLCHARS):
            c = ord(ch)
            if out and c == out[-1][1] + 1:
                out[-1][1] = c
            else:
                out.append([c, c])
        hit = _ORACLE[key] = tuple((a, b) for a, b in out)
    return hit


def _esc(c: int) -> str:
    return "\\x%02x" % c if c < 256 else ("\\u%04x" % c if c < 65536 else "\\U%08x" % c)


def _cased(c: int) -> bool:
    s = chr(c)
    return s.lower() != s or s.upper() != s or s.casefold() != s


def node_set(op, av, flags: int, sem: str) -> tuple:
    """LITERAL / NOT_LITERAL / ANY / IN 的收字集合。sem='py' 照 Python 語意;'ascii' = 同式加 re.ASCII(近似 DuckDB / RE2 的 \\d \\w \\s)。"""
    ic = bool(flags & re.IGNORECASE)
    asc = sem == "ascii" or bool(flags & re.ASCII)
    oflags = (re.IGNORECASE if ic else 0) | (re.ASCII if asc else 0)
    if op is _sc.ANY:
        return ALL_IV if flags & re.DOTALL else iv_neg(((10, 10),))
    if op is _sc.LITERAL or op is _sc.NOT_LITERAL:
        ivs = _oracle(_esc(av), oflags) if ic and _cased(av) else ((av, av),)
        return iv_neg(ivs) if op is _sc.NOT_LITERAL else ivs
    if op is _sc.IN:
        neg, simple, cats = False, [], []
        for o, a in av:
            if o is _sc.NEGATE:
                neg = True
            elif o is _sc.LITERAL:
                simple.append((a, a))
            elif o is _sc.RANGE:
                simple.append((a[0], a[1]))
            elif o is _sc.CATEGORY:
                cats.append(str(a))
            else:
                raise Unsupported("CHARSET_ITEM:" + str(o))
        if ic:
            text = "[" + "".join(_esc(a) if a == b else _esc(a) + "-" + _esc(b) for a, b in simple) + \
                   "".join(_CAT_TEXT[c] for c in cats) + "]"
            ivs = _oracle(text, oflags)
        else:
            parts = list(simple)
            for c in cats:
                base = c.replace("NOT_", "")
                pos = _ASCII_CAT[base] if asc else _oracle(_CAT_TEXT[base], 0)
                parts.extend(iv_neg(pos) if "NOT_" in c else pos)
            ivs = iv_norm(parts)
        return iv_neg(ivs) if neg else ivs
    raise Unsupported("NODE:" + str(op))


# ============================================================================================
# 二、NFA 與語言(布林組合:處理起點負向前瞻)
# ============================================================================================
class NFA:
    __slots__ = ("n", "eps", "tr", "start", "final")

    def __init__(self):
        self.n, self.eps, self.tr = 0, {}, []
        self.start = self.new()
        self.final = self.new()

    def new(self) -> int:
        self.n += 1
        if self.n > MAX_STATES:
            raise Unsupported("STATE_CAP")
        return self.n - 1

    def e(self, a: int, b: int) -> None:
        self.eps.setdefault(a, []).append(b)

    def t(self, a: int, ivs, b: int) -> None:
        if ivs:
            self.tr.append((a, ivs, b))


_CHAR_OPS = None


def _char_ops():
    global _CHAR_OPS
    if _CHAR_OPS is None:
        _CHAR_OPS = (_sc.LITERAL, _sc.NOT_LITERAL, _sc.ANY, _sc.IN)
    return _CHAR_OPS


def _b_seq(nfa: NFA, items, flags: int, sem: str):
    s = cur = nfa.new()
    for op, av in items:
        a, b = _b_item(nfa, op, av, flags, sem)
        nfa.e(cur, a)
        cur = b
    return s, cur


def _b_item(nfa: NFA, op, av, flags: int, sem: str):
    if op in _char_ops():
        a, b = nfa.new(), nfa.new()
        nfa.t(a, node_set(op, av, flags, sem), b)
        return a, b
    if op is _sc.BRANCH:
        a, b = nfa.new(), nfa.new()
        for alt in av[1]:
            x, y = _b_seq(nfa, alt, flags, sem)
            nfa.e(a, x)
            nfa.e(y, b)
        return a, b
    if op is _sc.SUBPATTERN:
        _g, add, dele, p = av
        return _b_seq(nfa, p, (flags | add) & ~dele, sem)
    if op is _sc.MAX_REPEAT or op is _sc.MIN_REPEAT:
        lo, hi, p = av
        unbounded = hi == _sc.MAXREPEAT
        if lo > REPEAT_CAP or (not unbounded and hi > REPEAT_CAP):
            raise Unsupported("REPEAT_CAP")
        a = cur = nfa.new()
        for _ in range(lo):
            x, y = _b_seq(nfa, p, flags, sem)
            nfa.e(cur, x)
            cur = y
        if unbounded:
            loop = nfa.new()
            nfa.e(cur, loop)
            x, y = _b_seq(nfa, p, flags, sem)
            nfa.e(loop, x)
            nfa.e(y, loop)
            return a, loop
        end = nfa.new()
        nfa.e(cur, end)
        for _ in range(hi - lo):
            x, y = _b_seq(nfa, p, flags, sem)
            nfa.e(cur, x)
            cur = y
            nfa.e(cur, end)
        return a, end
    if op is _sc.AT:
        raise Unsupported("WORD_BOUNDARY" if "BOUNDARY" in str(av) else "ANCHOR_INNER")
    if op is _sc.ASSERT or op is _sc.ASSERT_NOT:
        raise Unsupported("LOOKAROUND_INNER")
    if op is _sc.GROUPREF or str(op) == "GROUPREF_EXISTS":
        raise Unsupported("BACKREF")
    raise Unsupported("OP:" + str(op))


def _has_marker(items) -> bool:
    for op, av in items:
        if op is _sc.AT or op is _sc.ASSERT or op is _sc.ASSERT_NOT:
            return True
        if op is _sc.BRANCH and any(_has_marker(a) for a in av[1]):
            return True
        if op is _sc.SUBPATTERN and _has_marker(av[3]):
            return True
        if (op is _sc.MAX_REPEAT or op is _sc.MIN_REPEAT) and _has_marker(av[2]):
            return True
    return False


def _is_marker(item) -> bool:
    return item[0] is _sc.AT or item[0] is _sc.ASSERT or item[0] is _sc.ASSERT_NOT


def _norm_alts(items, budget: list) -> list:
    """把貼在邊上的錨點 / 環視從分支與群組裡攤出來:回傳若干條「邊界記號* + 本體 + 邊界記號*」的平面序列。"""
    items = list(items)
    idx = [i for i, it in enumerate(items) if not _is_marker(it)]
    for i in ([idx[0], idx[-1]] if idx else []):
        op, av = items[i]
        if op is _sc.BRANCH and _has_marker([items[i]]):
            out = []
            for alt in av[1]:
                out.extend(_norm_alts(items[:i] + list(alt) + items[i + 1:], budget))
                if len(out) > ALT_CAP:
                    raise Unsupported("ALT_CAP")
            return out
        if op is _sc.SUBPATTERN and _has_marker(av[3]):
            if av[1] or av[2]:
                raise Unsupported("SCOPED_FLAGS_AT_EDGE")
            return _norm_alts(items[:i] + list(av[3]) + items[i + 1:], budget)
    budget[0] += 1
    if budget[0] > ALT_CAP:
        raise Unsupported("ALT_CAP")
    return [items]


def _single_char(sub) -> bool:
    return len(sub) == 1 and sub[0][0] in _char_ops()


def parse_alts(pattern: str):
    """→ (全域旗標, [每條分支 {a_start, a_end, pre_not, post_not, la_neg, la_pos, core}])"""
    if not isinstance(pattern, str):
        raise Unsupported("NOT_TEXT")
    try:
        tree = _sp.parse(pattern)
    except (re.error, RecursionError, OverflowError) as exc:
        raise Unsupported("UNCOMPILABLE:%s" % exc)
    gflags = tree.state.flags
    if gflags & re.MULTILINE:
        raise Unsupported("MULTILINE")
    if gflags & re.LOCALE:
        raise Unsupported("LOCALE")
    alts = []
    for alt in _norm_alts(list(tree), [0]):
        alt = list(alt)
        info = {"a_start": False, "a_end": None, "pre_not": [], "post_not": [], "la_neg": [], "la_pos": []}
        while alt:
            op, av = alt[0]
            if op is _sc.AT:
                if av is _sc.AT_BEGINNING or av is _sc.AT_BEGINNING_STRING:
                    info["a_start"] = True
                    alt.pop(0)
                    continue
                if av is _sc.AT_END or av is _sc.AT_END_STRING:
                    break
                raise Unsupported("WORD_BOUNDARY")
            if op is _sc.ASSERT or op is _sc.ASSERT_NOT:
                d, sub = av
                if d < 0:
                    if op is _sc.ASSERT_NOT and _single_char(sub):
                        info["pre_not"].append(sub[0])
                        alt.pop(0)
                        continue
                    raise Unsupported("LOOKBEHIND")
                if _has_marker(sub):
                    raise Unsupported("LOOKAROUND_NESTED")
                info["la_neg" if op is _sc.ASSERT_NOT else "la_pos"].append(list(sub))
                alt.pop(0)
                continue
            break
        while alt:
            op, av = alt[-1]
            if op is _sc.AT:
                if av is _sc.AT_END:
                    info["a_end"] = info["a_end"] or "$"
                    alt.pop()
                    continue
                if av is _sc.AT_END_STRING:
                    info["a_end"] = "Z"
                    alt.pop()
                    continue
                raise Unsupported("WORD_BOUNDARY" if "BOUNDARY" in str(av) else "ANCHOR_INNER")
            if op is _sc.ASSERT_NOT and av[0] > 0 and _single_char(av[1]):
                info["post_not"].append(av[1][0])
                alt.pop()
                continue
            if op is _sc.ASSERT or op is _sc.ASSERT_NOT:
                raise Unsupported("LOOKAROUND_TAIL")
            break
        info["core"] = alt
        alts.append(info)
    return gflags, alts


def shape(pattern: str) -> dict:
    """式子的外形:是否兩端都錨定(驗證式)· 是否用 `$`(會放過結尾換行)。解析不了回 {'error': ..}。"""
    try:
        _f, alts = parse_alts(pattern)
    except Unsupported as exc:
        return {"error": str(exc), "anchored": pattern.startswith("^") and pattern.endswith("$"), "dollar": pattern.endswith("$")}
    return {"anchored": all(a["a_start"] and a["a_end"] for a in alts), "dollar": any(a["a_end"] == "$" for a in alts),
            "alts": len(alts)}


class Lang:
    """語言 = NFA 葉子的布林組合。expr:('L', i) · ('A', x, y) · ('O', x, y) · ('N', x)"""
    __slots__ = ("expr", "nfas")

    def __init__(self, expr, nfas):
        self.expr, self.nfas = expr, nfas


def _union_set(nodes, flags, sem) -> tuple:
    return iv_norm([iv for op, av in nodes for iv in node_set(op, av, flags, sem)])


def _alt_lang(info: dict, gflags: int, mode: str, sem: str, into: NFA | None) -> Lang | None:
    """一條分支的語言。沒有前瞻時直接接進共用 NFA(into)並回 None;有前瞻時回獨立的布林語言。"""
    anchored_start = info["a_start"] or mode == "full"
    if (info["la_neg"] or info["la_pos"]) and not anchored_start:
        raise Unsupported("LOOKAHEAD_UNANCHORED")
    solo = bool(info["la_neg"] or info["la_pos"])
    nfa = NFA() if solo or into is None else into
    x, y = _b_seq(nfa, info["core"], gflags, sem)
    if anchored_start:
        nfa.e(nfa.start, x)
    else:
        loop = nfa.new()
        nfa.e(nfa.start, loop)
        nfa.t(loop, ALL_IV, loop)
        if info["pre_not"]:
            nfa.e(nfa.start, x)
            q = nfa.new()
            nfa.t(loop, iv_neg(_union_set(info["pre_not"], gflags, sem)), q)
            nfa.e(q, x)
        else:
            nfa.e(loop, x)
    if mode == "full" or info["a_end"] == "Z":
        nfa.e(y, nfa.final)
    elif info["a_end"] == "$":
        nfa.e(y, nfa.final)
        q = nfa.new()
        nfa.t(y, ((10, 10),), q)
        nfa.e(q, nfa.final)
    else:
        nfa.e(y, nfa.final)
        loop = nfa.new()
        nfa.t(loop, ALL_IV, loop)
        nfa.e(loop, nfa.final)
        if info["post_not"]:
            nfa.t(y, iv_neg(_union_set(info["post_not"], gflags, sem)), loop)
        else:
            nfa.e(y, loop)
    if not solo:
        return None if into is not None else Lang(("L", 0), [nfa])
    nfas, expr = [nfa], ("L", 0)
    for neg, subs in ((True, info["la_neg"]), (False, info["la_pos"])):
        for sub in subs:
            la = NFA()
            a, b = _b_seq(la, sub, gflags, sem)
            la.e(la.start, a)
            loop = la.new()
            la.e(b, loop)
            la.t(loop, ALL_IV, loop)
            la.e(loop, la.final)
            nfas.append(la)
            leaf = ("L", len(nfas) - 1)
            expr = ("A", expr, ("N", leaf) if neg else leaf)
    return Lang(expr, nfas)


def _shift(expr, k: int):
    if expr[0] == "L":
        return ("L", expr[1] + k)
    return (expr[0],) + tuple(_shift(e, k) for e in expr[1:])


def lang_or(langs: list) -> Lang:
    nfas, expr = [], None
    for lg in langs:
        e = _shift(lg.expr, len(nfas))
        nfas.extend(lg.nfas)
        expr = e if expr is None else ("O", expr, e)
    return Lang(expr, nfas)


def build_lang(pattern: str, mode: str = "search", sem: str = "py", pick=None) -> Lang:
    """式子 → 語言。mode='full'(整串相符)· 'search'(字串裡找得到);pick = 只取哪幾條頂層分支(查死分支用)。"""
    gflags, alts = parse_alts(pattern)
    shared, langs = NFA(), []
    used_shared = False
    for i, info in enumerate(alts):
        if pick is not None and i not in pick:
            continue
        lg = _alt_lang(info, gflags, mode, sem, shared)
        if lg is None:
            used_shared = True
        else:
            langs.append(lg)
    if used_shared or not langs:
        langs.insert(0, Lang(("L", 0), [shared]))
    return lang_or(langs) if len(langs) > 1 else langs[0]


class _Run:
    def __init__(self, nfa: NFA, classes: list, starts: list):
        self.nfa, self.memo, self.delta = nfa, {}, {}
        for src, ivs, dst in nfa.tr:
            d = self.delta.setdefault(src, {})
            for lo, hi in ivs:
                i = bisect.bisect_left(starts, lo)
                while i < len(classes) and classes[i][1] <= hi:
                    d.setdefault(i, set()).add(dst)
                    i += 1
        self.used = {ci for d in self.delta.values() for ci in d}
        self.init = self.closure({nfa.start})

    def closure(self, states) -> frozenset:
        out, stack = set(), list(states)
        while stack:
            q = stack.pop()
            if q not in out:
                out.add(q)
                stack.extend(self.nfa.eps.get(q, ()))
        return frozenset(out)

    def move(self, S: frozenset, ci: int) -> frozenset:
        key = (S, ci)
        hit = self.memo.get(key)
        if hit is None:
            nxt = set()
            for q in S:
                d = self.delta.get(q)
                if d and ci in d:
                    nxt |= d[ci]
            hit = self.memo[key] = self.closure(nxt) if nxt else frozenset()
        return hit


def _ev(expr, acc) -> bool:
    k = expr[0]
    if k == "L":
        return acc[expr[1]]
    if k == "N":
        return not _ev(expr[1], acc)
    if k == "A":
        return _ev(expr[1], acc) and _ev(expr[2], acc)
    return _ev(expr[1], acc) or _ev(expr[2], acc)


_PREF = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .-_"


def _rep(lo: int, hi: int) -> str:
    for ch in _PREF:
        if lo <= ord(ch) <= hi:
            return ch
    for c in range(max(lo, 33), min(hi, 126) + 1):
        return chr(c)
    for c in range(lo, min(hi, lo + 64) + 1):
        if 0xD800 <= c <= 0xDFFF:
            continue
        if unicodedata.category(chr(c))[0] in "LNPS":
            return chr(c)
    return chr(lo)


def relate(A: Lang, B: Lang, cap: int = MAX_PRODUCT) -> dict:
    """兩個語言的精確關係 + 最短見證字串。EQUAL / SUBSET(A⊂B)/ SUPERSET / OVERLAP / DISJOINT / EMPTY。"""
    nfas = list(A.nfas) + list(B.nfas)
    eb = _shift(B.expr, len(A.nfas))
    bounds = set()
    for n in nfas:
        for _s, ivs, _d in n.tr:
            for lo, hi in ivs:
                bounds.add(lo)
                bounds.add(hi + 1)
    pts = sorted(bounds)
    classes = [(pts[i], pts[i + 1] - 1) for i in range(len(pts) - 1)]
    starts = [c[0] for c in classes]
    runs = [_Run(n, classes, starts) for n in nfas]
    finals = [n.final for n in nfas]
    used = sorted(set().union(*[r.used for r in runs])) if runs else []
    start = tuple(r.init for r in runs)
    seen = {start: None}
    queue, head = [start], 0
    found = {"both": None, "a_only": None, "b_only": None}
    while head < len(queue):
        st = queue[head]
        head += 1
        acc = [finals[i] in st[i] for i in range(len(st))]
        a, b = _ev(A.expr, acc), _ev(eb, acc)
        key = "both" if a and b else "a_only" if a else "b_only" if b else None
        if key and found[key] is None:
            found[key] = st
            if all(v is not None for v in found.values()):
                break
        if not any(st):
            continue                    # 所有葉子都已死:之後的接受與否不再變
        for ci in used:
            nxt = tuple(runs[i].move(st[i], ci) for i in range(len(st)))
            if nxt not in seen:
                seen[nxt] = (st, ci)
                queue.append(nxt)
                if len(seen) > cap:
                    raise Unsupported("PRODUCT_CAP")

    def witness(st):
        if st is None:
            return None
        out = []
        while seen[st] is not None:
            st, ci = seen[st]
            out.append(_rep(*classes[ci]))
        return "".join(reversed(out))

    w = {k: witness(v) for k, v in found.items()}
    if w["both"] is None:
        rel = "EMPTY" if w["a_only"] is None and w["b_only"] is None else "DISJOINT"
    elif w["a_only"] is None and w["b_only"] is None:
        rel = "EQUAL"
    elif w["a_only"] is None:
        rel = "SUBSET"
    elif w["b_only"] is None:
        rel = "SUPERSET"
    else:
        rel = "OVERLAP"
    return {"rel": rel, "both": w["both"], "a_only": w["a_only"], "b_only": w["b_only"], "states": len(seen)}


def accepts(lg: Lang, s: str) -> bool:
    """線性時間比對(NFA 模擬,不回溯):樣本檢查都走這裡,ReDoS 式子拖不垮引擎。"""
    acc = []
    for n in lg.nfas:
        by = {}
        for src, ivs, dst in n.tr:
            by.setdefault(src, []).append((ivs, dst))

        def clo(states, eps=n.eps):
            out, stack = set(), list(states)
            while stack:
                q = stack.pop()
                if q not in out:
                    out.add(q)
                    stack.extend(eps.get(q, ()))
            return out
        cur = clo({n.start})
        for ch in s:
            c = ord(ch)
            cur = clo({dst for q in cur for ivs, dst in by.get(q, ()) if iv_has(ivs, c)})
            if not cur:
                break
        acc.append(n.final in cur)
    return _ev(lg.expr, acc)


def show(s) -> str:
    """見證字串的可讀寫法:非 ASCII 與控制字元帶碼位。"""
    if s is None:
        return "—"
    out = []
    for ch in s:
        c = ord(ch)
        if 32 <= c < 127:
            out.append(ch)
        elif c < 32 or 0xD800 <= c <= 0xDFFF:
            out.append("\\x%02x" % c if c < 256 else "\\u%04x" % c)
        else:
            out.append("%s(U+%04X)" % (ch, c))
    return '"' + "".join(out) + '"'


# ============================================================================================
# 三、靜態風險(不執行式子)
# ============================================================================================
def _frag(items, flags: int, sem: str = "py", plus: bool = False) -> Lang:
    n = NFA()
    x, y = _b_seq(n, items, flags, sem)
    n.e(n.start, x)
    if plus:                                # 本體 · 本體+
        loop = n.new()
        n.e(y, loop)
        a, b = _b_seq(n, items, flags, sem)
        n.e(loop, a)
        n.e(b, loop)
        n.e(b, n.final)
    else:
        n.e(y, n.final)
    return Lang(("L", 0), [n])


def _walk_repeats(items, flags: int, out: list) -> None:
    for op, av in items:
        if op is _sc.BRANCH:
            for alt in av[1]:
                _walk_repeats(alt, flags, out)
        elif op is _sc.SUBPATTERN:
            _walk_repeats(av[3], (flags | av[1]) & ~av[2], out)
        elif op is _sc.ASSERT or op is _sc.ASSERT_NOT:
            _walk_repeats(av[1], flags, out)
        elif op is _sc.MAX_REPEAT or op is _sc.MIN_REPEAT or str(op) == "POSSESSIVE_REPEAT":
            lo, hi, body = av
            if (hi == _sc.MAXREPEAT or hi >= 16) and str(op) != "POSSESSIVE_REPEAT" and not _single_char(body):
                out.append((list(body), flags))
            _walk_repeats(body, flags, out)
        elif str(op) == "ATOMIC_GROUP":
            _walk_repeats(av, flags, out)


def _nested_repeat(items) -> bool:
    for op, av in items:
        if op is _sc.MAX_REPEAT or op is _sc.MIN_REPEAT:
            return True
        if op is _sc.BRANCH and any(_nested_repeat(a) for a in av[1]):
            return True
        if op is _sc.SUBPATTERN and _nested_repeat(av[3]):
            return True
    return False


def lint(pattern: str, validator: bool | None = None) -> list:
    """靜態檢查,不執行式子。回傳 [{code, sev, why, witness}];sev = RED / YELLOW / NOTE。"""
    out = []
    try:
        re.compile(pattern)
    except (re.error, RecursionError, OverflowError) as exc:
        return [{"code": "RGX_UNCOMPILABLE", "sev": "RED", "why": "編不過:%s" % exc, "witness": None}]
    try:
        tree = _sp.parse(pattern)
        bodies = []
        _walk_repeats(list(tree), tree.state.flags, bodies)
    except Exception as exc:                # noqa: BLE001 — 解析器內部錯一律當不可證
        return [{"code": "RGX_UNPROVEN", "sev": "NOTE", "why": "解析不了:%s" % exc, "witness": None}]
    for body, flags in bodies:
        try:
            r = relate(_frag(body, flags), _frag(body, flags, plus=True))
            if r["both"] is not None:
                out.append({"code": "RGX_REDOS", "sev": "YELLOW", "witness": r["both"],
                            "why": "重複的本體有二義切法(同一段字可切成一次或多次):回溯引擎遇到不相符的尾巴會指數爆炸"})
                break
        except Unsupported:
            if _nested_repeat(body):
                out.append({"code": "RGX_REDOS_SUSPECT", "sev": "NOTE", "witness": None,
                            "why": "無上限重複裡還有重複,但語法超出可證範圍 — 沒有證明安全"})
                break
    sh = shape(pattern)
    skipped = []
    is_validator = sh.get("anchored") if validator is None else validator
    try:
        mode = "full" if is_validator else "search"
        r = relate(build_lang(pattern, mode, "py"), build_lang(pattern, mode, "ascii"))
        if r["rel"] not in ("EQUAL", "EMPTY"):
            w = r["a_only"] if r["a_only"] is not None else r["b_only"]
            out.append({"code": "RGX_DIALECT_DRIFT", "sev": "YELLOW" if is_validator else "NOTE", "witness": w,
                        "why": "Python 語意與 ASCII 語意(DuckDB / RE2 的 \\d \\w \\s)收的字不同:同一式在兩邊判法不一樣"})
    except Unsupported as exc:
        skipped.append("方言漂移(%s)" % exc)
    if sh.get("anchored") and sh.get("dollar"):
        out.append({"code": "RGX_DOLLAR_NEWLINE", "sev": "NOTE", "witness": None,
                    "why": "結尾用 `$`:re.match / re.search 會放過多一個結尾換行(要嚴格請用 \\Z 或 fullmatch)"})
    try:
        _f, alts = parse_alts(pattern)
        if 1 < len(alts) <= 12:
            for i in range(1, len(alts)):
                mode = "full" if sh.get("anchored") else "search"
                r = relate(build_lang(pattern, mode, "py", pick={i}), build_lang(pattern, mode, "py", pick=set(range(i))))
                if r["rel"] in ("SUBSET", "EQUAL"):
                    out.append({"code": "RGX_DEAD_BRANCH", "sev": "NOTE", "witness": r["both"],
                                "why": "第 %d 條分支收的字前面的分支全收了(死分支)" % (i + 1)})
                    break
    except Unsupported as exc:
        skipped.append("死分支(%s)" % exc)
    if skipped:
        out.append({"code": "RGX_LINT_PARTIAL", "sev": "NOTE", "witness": None,
                    "why": "這幾項靜態檢查超出可證範圍,沒做(不是通過):" + " · ".join(skipped)})
    return out


# ============================================================================================
# 四、共用小工具
# ============================================================================================
def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(obj) -> str:
    return hashlib.sha256((obj if isinstance(obj, str) else canon(obj)).encode("utf-8", "surrogatepass")).hexdigest()


def norm_word(s) -> str:
    """同義字比對的正規化:NFKC(全形 → 半形)+ casefold + 空白收斂。原拼法另存,不改。"""
    return " ".join(unicodedata.normalize("NFKC", str(s)).casefold().split())


def norm_key(s) -> str:
    return re.sub(r"[^a-z0-9]+", "_", unicodedata.normalize("NFKC", str(s)).casefold()).strip("_")


def rel_posix(p: Path, root: Path) -> str:
    """帳裡只記相對 VIA 根的正斜線路徑(工作站與容器同一份)。"""
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.name


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})$", p.stem)
    return int(m.group(1)) if m else -1


def tails(root: Path, pattern: str) -> list:
    """glob → 每個家族取尾版(家族 = 去掉 _vNNNN 的檔名)。"""
    fam = {}
    for p in sorted(root.glob(pattern)):
        if not p.is_file():
            continue
        m = re.search(r"_v\d{4}$", p.stem)
        f = (str(p.parent), p.stem[:m.start()] if m else p.stem)
        if f not in fam or _vnum(p) > _vnum(fam[f]):
            fam[f] = p
    return [fam[k] for k in sorted(fam)]


def read_json(p: Path):
    """只讀;UTF-8(含 BOM)。壞檔 / 非 UTF-8 丟 ValueError,由呼叫端記成該來源 INVALID。"""
    try:
        return json.loads(p.read_bytes().decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise ValueError("不是 UTF-8:%s" % exc)
    except ValueError as exc:
        raise ValueError("JSON 壞了:%s" % exc)


# ============================================================================================
# 五、來源讀取(只讀;一個來源壞掉不影響別的)
# ============================================================================================
OWNER_SYS = {"VDF": "VDF", "VQG": "VQG", "VCGC": "VCGC", "VAP": "VAP", "VRN": "VRN", "VRN-2": "VRN", "VRN2": "VRN",
             "VRN-1": "VRN"}                # L128:VRN-2 為主、VRN-1 為輔,系統名統稱 VRN


def _asset(**kw) -> dict:
    a = {"sys": "?", "src": "?", "path": "", "kind": "REGEX", "key": "", "scope": "", "value": "", "aliases": [],
         "locked": False, "code": None, "rank": "SELF_REPORT", "mode": None, "positive": [], "negative": [],
         "alias_of": None, "target": None, "grant_stale": False}
    a.update(kw)
    return a


def _ad_central(d, src) -> list:
    out = []
    if not isinstance(d, dict) or not isinstance(d.get("regex"), dict):
        raise ValueError("中央冊形狀不對(沒有 regex 區)")
    for k, v in d["regex"].items():
        if isinstance(v, dict) and isinstance(v.get("pattern"), str):
            ao = v.get("alias_of")
            out.append(_asset(kind="REGEX", key=k, value=v["pattern"], locked=bool(v.get("locked")), scope="central",
                              rank="LOCKED" if v.get("locked") else "CENTRAL",
                              alias_of=re.split(r"[((\s]", ao)[0] if isinstance(ao, str) and ao else None))
    meta = d.get("synonyms_meta") if isinstance(d.get("synonyms_meta"), dict) else {}
    for k, v in (d.get("synonyms") or {}).items():
        if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
            ns = (meta.get(k) or {}).get("namespace") if isinstance(meta.get(k), dict) else None
            out.append(_asset(kind="SYNONYM", key=k, value=k, aliases=list(v), scope="central:" + (ns or k.split("_")[0].lower()),
                              rank="CENTRAL"))
    return out


def _from_contract(a: dict, grant: dict) -> dict | None:
    if not isinstance(a, dict) or a.get("asset_type") not in ("REGEX", "SYNONYM"):
        return None
    g = (grant.get("assets") or {}).get(a.get("source_pointer")) if isinstance(grant, dict) else None
    code = g.get("code") if isinstance(g, dict) else None
    stale = bool(g and g.get("source_sha256") and g.get("version") == a.get("version")
                 and g.get("source_sha256") != a.get("source_sha256"))
    return _asset(kind=a["asset_type"], key=str(a.get("semantic_key") or a.get("candidate_id") or ""), value=a.get("value"),
                  aliases=[x for x in (a.get("aliases") or []) if isinstance(x, str)], scope=str(a.get("scope") or ""),
                  positive=[x for x in (a.get("positive") or []) if isinstance(x, str)],
                  negative=[x for x in (a.get("negative") or []) if isinstance(x, str)],
                  code=code, rank="NUMBERED" if code else "CANDIDATE", grant_stale=stale,
                  sys=OWNER_SYS.get(str(a.get("owner")), "%s(未登記)" % a.get("owner")))


def _ad_candidates(d, src, grant) -> list:
    if not isinstance(d, dict) or not isinstance(d.get("assets"), list):
        raise ValueError("候選冊形狀不對(沒有 assets)")
    return [x for x in (_from_contract(a, grant) for a in d["assets"]) if x]


def _ad_request(d, src, grant) -> list:
    if not isinstance(d, dict):
        raise ValueError("核號請求形狀不對")
    raw = [x for x in list(d.get("ssot_items") or []) + list(d.get("program_items") or []) if isinstance(x, dict)]
    out = []
    for it in raw:
        x = _from_contract(it.get("asset"), grant)
        if x:
            x["sys"] = src["system"]
            x["rank"] = "NUMBERED" if x["code"] else "SELF_REPORT"
            out.append(x)
    return out


def _ad_rule_list(d, src) -> list:
    rows = d if isinstance(d, list) else d.get(src.get("list_path") or "rules") if isinstance(d, dict) else None
    if not isinstance(rows, list):
        raise ValueError("規則清單形狀不對")
    kf, pf, tf = src.get("key_field") or "rule_id", src.get("pattern_field") or "regex", src.get("target_field") or "target"
    return [_asset(kind="REGEX", key=str(r[kf]), value=r[pf], target=r.get(tf), scope=str(src.get("scope") or ""),
                   mode=src.get("mode")) for r in rows if isinstance(r, dict) and isinstance(r.get(pf), str) and r.get(kf)]


def _dig(obj, path: str):
    for part in path.split("/"):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def _ad_json_path(d, src) -> list:
    out = []
    for e in src.get("entries") or []:
        v = _dig(d, e["path"])
        if isinstance(v, str):
            out.append(_asset(kind=e.get("kind") or "REGEX", key=e["key"], value=v, scope=str(e.get("scope") or ""),
                              mode=e.get("mode")))
    if not out:
        raise ValueError("冊上找不到宣告的路徑(%s)" % " · ".join(e["path"] for e in src.get("entries") or []))
    return out


def _ad_proposal(d, src) -> list:
    if not isinstance(d, dict) or not isinstance(d.get("assets"), list):
        raise ValueError("提案冊形狀不對(沒有 assets)")
    out = []
    for a in d["assets"]:
        if isinstance(a, dict) and a.get("key") and a.get("kind") in ("REGEX", "SYNONYM"):
            out.append(_asset(kind=a["kind"], key=a["key"], value=a.get("pattern") if a["kind"] == "REGEX" else a.get("value"),
                              aliases=list(a.get("aliases") or []), scope=str(a.get("scope") or ""), mode=a.get("mode"),
                              positive=list(a.get("positive") or []), negative=list(a.get("negative") or []), rank="PROPOSAL"))
    return out


class Engine:
    def __init__(self, via: Path = VIA, registry: Path | None = None, clock=now_utc, budget: float = TIME_BUDGET):
        self.via = Path(via)
        self.registry = Path(registry) if registry else self.via / "supportive modules" / "registry"
        self.clock = clock
        self.budget = budget
        self.ledger = Ledger(self.registry / LEDGER_NAME, [self.registry / LEDGER_NAME, self.via.joinpath(*REPORT_DIR)], clock)
        self._lang_cache: dict = {}
        self._t0 = time.monotonic()

    # ---------- 來源 ----------
    def sources_book(self):
        hits = sorted(self.registry.glob(SOURCES_GLOB), key=_vnum)
        if not hits:
            raise ValueError("來源冊不存在(%s)" % SOURCES_GLOB)
        return hits[-1], read_json(hits[-1])

    def load(self, extra: list | None = None) -> dict:
        book_path, book = self.sources_book()
        grant = {}
        gp = self.via / str(book.get("grant_book") or "")
        if book.get("grant_book") and gp.is_file():
            try:
                grant = read_json(gp)
            except ValueError:
                grant = {"_invalid": True}
        assets, status = [], []
        specs = list(book.get("sources") or []) + list(extra or [])
        for src in specs:
            st = {"id": src["id"], "system": src["system"], "adapter": src["adapter"], "state": "OK", "files": [], "why": "", "n": 0}
            status.append(st)
            if not src.get("glob"):
                st["state"], st["why"] = "NODATA", src.get("why") or "沒有宣告可讀的檔"
                continue
            files = [Path(src["glob"])] if src.get("absolute") else tails(self.via, src["glob"])
            files = [f for f in files if f.is_file()]
            if not files:
                st["state"], st["why"] = "NODATA", "這個系統還沒有自報檔(%s)" % src["glob"]
                continue
            for f in files:
                rp = rel_posix(f, self.via)
                try:
                    raw = f.read_bytes()
                    d = json.loads(raw.decode("utf-8-sig"))
                    got = {"central_book": lambda: _ad_central(d, src), "asset_candidates": lambda: _ad_candidates(d, src, grant),
                           "number_request": lambda: _ad_request(d, src, grant), "rule_list": lambda: _ad_rule_list(d, src),
                           "json_path": lambda: _ad_json_path(d, src), "proposal": lambda: _ad_proposal(d, src)}[src["adapter"]]()
                except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
                    st["state"], st["why"] = "INVALID", "%s:%s" % (rp, str(exc)[:160])
                    continue
                for a in got:
                    a["src"], a["path"] = src["id"], rp
                    if a["sys"] == "?":
                        a["sys"] = src["system"]
                    a["vsha"] = sha(canon([a["value"], sorted(a["aliases"])]))[:16]
                assets.extend(got)
                st["n"] += len(got)
                st["files"].append({"path": rp, "version": _vnum(f), "sha": hashlib.sha256(raw).hexdigest()})
        return {"book": rel_posix(book_path, self.via), "concepts": book.get("concepts") or {}, "assets": assets,
                "status": status, "grant": grant, "systems": book.get("systems") or [],
                "pseudo": set(book.get("pseudo_systems") or [])}

    # ---------- 語言快取與關係 ----------
    def lang(self, pattern: str, mode: str, sem: str = "py") -> Lang:
        key = (pattern, mode, sem)
        if key not in self._lang_cache:
            try:
                self._lang_cache[key] = build_lang(pattern, mode, sem)
            except Unsupported as exc:
                self._lang_cache[key] = exc
            except RecursionError:
                self._lang_cache[key] = Unsupported("RECURSION")
        hit = self._lang_cache[key]
        if isinstance(hit, Unsupported):
            raise hit
        return hit

    def mode_of(self, a: dict) -> str:
        return a["mode"] or ("full" if shape(a["value"]).get("anchored") else "search")

    def pair(self, a: dict, b: dict) -> dict:
        """兩個正則資產的關係;用法不同(驗證式 vs 抽取式)不比;超時 / 不支援 = UNPROVEN。"""
        ma, mb = self.mode_of(a), self.mode_of(b)
        if a["value"] == b["value"] and ma == mb:
            return {"rel": "SAME_TEXT"}
        if ma != mb:
            return {"rel": "MODE_DIFF", "why": "%s 是%s、%s 是%s:用法不同,不放在同一把尺上比" % (
                a["key"], "驗證式" if ma == "full" else "抽取式", b["key"], "驗證式" if mb == "full" else "抽取式")}
        if time.monotonic() - self._t0 > self.budget:
            return {"rel": "UNPROVEN", "why": "TIME_BUDGET"}
        try:
            return relate(self.lang(a["value"], ma), self.lang(b["value"], mb))
        except Unsupported as exc:
            return {"rel": "UNPROVEN", "why": str(exc)}

    def sample(self, a: dict, s: str):
        """樣本是否相符:優先走自動機;走不了且式子沒有巢狀重複時才退回 re(樣本限長)。回 True / False / None(不可證)。"""
        if len(s) > SAMPLE_MAX:
            return None
        mode = self.mode_of(a)
        try:
            lg = self.lang(a["value"], mode)
        except Unsupported:
            lg = None
        if lg is not None:
            return accepts(lg, s)
        try:
            tree = _sp.parse(a["value"])
            bodies = []
            _walk_repeats(list(tree), tree.state.flags, bodies)
            if any(_nested_repeat(b) for b, _f in bodies):
                return None
            rx = re.compile(a["value"])
            return bool(rx.fullmatch(s) if mode == "full" else rx.search(s))
        except Exception:               # noqa: BLE001
            return None

    # ---------- 偵測 ----------
    def detect(self, data: dict) -> dict:
        self._t0 = time.monotonic()
        assets, cases, notes = data["assets"], {}, []
        ok_src = {s["id"] for s in data["status"] if s["state"] == "OK"}

        def who(a):
            return {"sys": a["sys"], "src": a["src"], "key": a["key"]}

        def case(ctype, sev, family, parts, summary, evidence, suggest=""):
            ident = {"type": ctype, "parts": sorted(([p["sys"], p["src"], p["key"]] for p in parts))}
            cid = "SCC-" + sha(ident)[:10].upper()
            cases[cid] = {"case": cid, "type": ctype, "sev": sev, "family": family, "identity": ident, "parts": parts,
                          "summary": summary, "evidence_fp": sha(evidence)[:16], "suggest": suggest}

        rx = [a for a in assets if a["kind"] == "REGEX" and isinstance(a["value"], str)]
        syn = [a for a in assets if a["kind"] == "SYNONYM"]

        # —— 單式靜態風險 + 自己的正反例 ——
        grouped = {}
        for a in rx:
            for f in lint(a["value"]):
                if f["sev"] == "NOTE":
                    notes.append({"code": f["code"], "sys": a["sys"], "key": a["key"], "why": f["why"], "witness": f["witness"]})
                else:
                    grouped.setdefault((f["code"], f["sev"], a["sys"], a["src"]), []).append((a, f))
        for (code, sev, sys_, src), hits in sorted(grouped.items()):      # 同一來源同一根因 = 一案(一次裁定)
            hits.sort(key=lambda h: h[0]["key"])
            a0, f0 = hits[0]
            case(code, sev, "正則", [{"sys": sys_, "src": src, "key": code}], "%s 有 %d 式:%s%s · %s · 例 %s → %s" % (
                src, len(hits), " · ".join(h[0]["key"] for h in hits[:8]), " …" if len(hits) > 8 else "", f0["why"],
                a0["key"], show(f0["witness"])), sorted([h[0]["key"], h[0]["vsha"]] for h in hits),
                 "式子的正本在它自己的冊;要改就由該系統出新版號冊(LOCKED 的要操作員裁定)")
            bad = []
            for want, samples in ((True, a["positive"]), (False, a["negative"])):
                for s in samples:
                    got = self.sample(a, s)
                    if got is None:
                        notes.append({"code": "RGX_UNPROVEN", "sys": a["sys"], "key": a["key"], "why": "樣本 %s 無法判定" % show(s),
                                      "witness": s})
                    elif got != want:
                        bad.append("%s 應%s卻%s" % (show(s), "收" if want else "拒", "拒" if want else "收"))
            if bad:
                case("RGX_EXAMPLE_FAILED", "RED", "正則", [who(a)], "%s · 自己的樣本不過:%s" % (a["key"], ";".join(bad[:4])),
                     [a["vsha"], bad], "先修式子或修樣本(兩者對不上的式子不能發號)")

        def judge(a, b, ctype, sev, why, same_expected=True):
            r = self.pair(a, b)
            if r["rel"] in ("SAME_TEXT", "EQUAL", "EMPTY"):
                if r["rel"] == "EQUAL":
                    notes.append({"code": "RGX_EQUIVALENT", "sys": a["sys"], "key": a["key"], "witness": None,
                                  "why": "與 %s:%s 寫法不同但收的字完全一樣(已證;自動視為一致)" % (b["sys"], b["key"])})
                return r
            if r["rel"] in ("MODE_DIFF", "UNPROVEN"):
                notes.append({"code": "RGX_" + r["rel"], "sys": a["sys"], "key": a["key"], "witness": None,
                              "why": "與 %s:%s — %s" % (b["sys"], b["key"], r.get("why"))})
                return r
            w = " · ".join("%s %s" % (lab, show(r[k])) for lab, k in (
                ("只有 %s 收" % a["key"], "a_only"), ("只有 %s 收" % b["key"], "b_only"), ("兩邊都收", "both")) if r.get(k) is not None)
            case(ctype, sev, "正則", [who(a), who(b)], "%s — %s(%s)· %s" % (why, r["rel"], _REL_ZH[r["rel"]], w),
                 [a["vsha"], b["vsha"], r["rel"]],
                 "兩邊都不動;操作員裁定:維持採信值 / 採新式(出新版號冊)/ 分範疇並存 / 接受差異")
            return r

        # —— 同鍵跨來源 ——
        by_key = {}
        for a in rx:
            by_key.setdefault(norm_key(a["key"]), []).append(a)
        for k, grp in sorted(by_key.items()):
            for i in range(len(grp)):
                for j in range(i + 1, len(grp)):
                    if grp[i]["src"] != grp[j]["src"] or grp[i]["key"] != grp[j]["key"]:
                        judge(grp[i], grp[j], "RGX_KEY_DIVERGE", "RED", "同一鍵 %s 在 %s 與 %s 收的字不同" % (
                            grp[i]["key"], grp[i]["sys"], grp[j]["sys"]))
        # —— 宣告是別名,語言卻不同 ——
        first = {}
        for a in rx:
            first.setdefault((a["src"], a["key"]), a)
        for a in rx:
            if a["alias_of"]:
                b = first.get((a["src"], a["alias_of"]))
                if b is not None and b is not a:
                    judge(a, b, "RGX_ALIAS_DRIFT", "YELLOW", "%s 宣告是 %s 的別名,收的字卻不同" % (a["key"], b["key"]))
        # —— 同一概念的成員 ——
        concept_of = {}
        for cname, c in sorted(data["concepts"].items()):
            for m in c.get("members") or []:
                concept_of[norm_key(m)] = cname
        for a in rx:
            a["concept"] = concept_of.get(norm_key(a["key"])) or concept_of.get(norm_key(a["target"] or ""))
        by_c = {}
        for a in rx:
            if a["concept"]:
                by_c.setdefault(a["concept"], []).append(a)
        for cname, grp in sorted(by_c.items()):
            grp.sort(key=lambda a: (RANKS.index(a["rank"]), a["sys"], a["key"]))
            reps = []                       # 每個「收的字相同」的等價類只留一個代表(位階最高的),代表之間才逐對比
            for b in grp:
                twin = next((a for a in reps if self.pair(a, b)["rel"] in ("SAME_TEXT", "EQUAL")), None)
                if twin is not None:
                    if twin["value"] != b["value"]:
                        notes.append({"code": "RGX_EQUIVALENT", "sys": b["sys"], "key": b["key"], "witness": None,
                                      "why": "與 %s:%s 寫法不同但收的字完全一樣(已證;自動視為一致)" % (twin["sys"], twin["key"])})
                    continue
                for a in reps:
                    if norm_key(a["key"]) != norm_key(b["key"]):
                        judge(a, b, "RGX_CONCEPT_DIVERGE", "YELLOW", "概念 %s:%s(%s)與 %s(%s)收的字不同" % (
                            cname, a["key"], a["sys"], b["key"], b["sys"]))
                reps.append(b)
        # —— 同範疇不同鍵:交疊 + 搶樣本 ——
        by_scope = {}
        for a in rx:
            if a["scope"] and not a["scope"].startswith("central"):
                by_scope.setdefault(a["scope"], []).append(a)
        for scope, grp in sorted(by_scope.items()):
            for i in range(len(grp)):
                for j in range(i + 1, len(grp)):
                    a, b = grp[i], grp[j]
                    if norm_key(a["key"]) == norm_key(b["key"]):
                        continue
                    r = self.pair(a, b)
                    if r["rel"] in ("EQUAL", "SUBSET", "SUPERSET", "OVERLAP", "SAME_TEXT"):
                        case("RGX_SCOPE_OVERLAP", "RED", "正則", [who(a), who(b)], "範疇 %s:%s 與 %s 是不同的鍵,卻有字兩邊都收(%s)· 例 %s" % (
                            scope, a["key"], b["key"], _REL_ZH.get(r["rel"], r["rel"]), show(r.get("both"))), [a["vsha"], b["vsha"], r["rel"]],
                             "同範疇同一串字只能有一個主:收窄其中一式,或把兩鍵併成同義,或分範疇")
                    elif r["rel"] == "UNPROVEN":
                        notes.append({"code": "RGX_UNPROVEN", "sys": a["sys"], "key": a["key"], "witness": None,
                                      "why": "範疇 %s:與 %s 的交疊無法證明(%s)" % (scope, b["key"], r.get("why"))})
                    for x, y in ((a, b), (b, a)):
                        stolen = [s for s in y["positive"] if self.sample(x, s) is True]
                        if stolen and r["rel"] not in ("EQUAL", "SUBSET", "SUPERSET", "OVERLAP", "SAME_TEXT"):
                            case("RGX_STEAL", "RED", "正則", [who(x), who(y)], "範疇 %s:%s 會收走 %s 的正例 %s" % (
                                scope, x["key"], y["key"], " · ".join(show(s) for s in stolen[:3])), [x["vsha"], y["vsha"], stolen],
                                 "新式不能改掉舊樣本的判法")
        # —— 同義字 ——
        owner, dual = {}, {}
        for a in syn:
            for w in [a["value"]] + list(a["aliases"]):
                owner.setdefault((a["scope"], norm_word(w)), []).append((a, w))
        for (scope, word), hits in sorted(owner.items()):
            targets = {}
            for a, w in hits:
                targets.setdefault(norm_word(a["value"]), []).append((a, w))
            if len(targets) > 1:
                parts = [who(a) for lst in targets.values() for a, _w in lst]
                raws = sorted({w for lst in targets.values() for _a, w in lst})
                names = " / ".join(sorted(a["value"] for lst in targets.values() for a, _w in lst[:1]))
                if len({(p["sys"], p["src"]) for p in parts}) == 1:          # 同一本冊自己掛兩鍵:可能是兩條軸,先併成一案待審
                    dual.setdefault((parts[0]["sys"], parts[0]["src"], scope), []).append((word, names))
                    continue
                case("SYN_MULTI_TARGET", "RED", "同義字", parts, "範疇 %s:「%s」同時指到 %s%s" % (
                    scope, word, names, "(原拼法 %s 正規化後相撞)" % " · ".join(raws) if len(raws) > 1 else ""),
                     sorted(a["vsha"] for lst in targets.values() for a, _w in lst),
                     "一詞一主:裁定歸誰,另一邊降為別名或分範疇(不刪)")
        for (sys_, src, scope), hits in sorted(dual.items()):
            case("SYN_DUAL_KEY", "YELLOW", "同義字", [{"sys": sys_, "src": src, "key": "SYN_DUAL_KEY:" + scope}],
                 "%s 範疇 %s:同一本冊內 %d 個詞各掛兩個鍵(可能是兩條軸,也可能是一詞兩主):%s" % (
                     src, scope, len(hits), ";".join("「%s」→ %s" % h for h in hits[:6])), sorted(hits),
                 "由這本冊的主人說明:是兩條軸(分範疇)還是一詞兩主(裁定歸誰)")
        words = {}
        for a in syn:
            for w in a["aliases"]:
                words.setdefault(norm_word(w), set()).add(a["scope"])
        cross = sorted(w for w, sc in words.items() if len(sc) > 1)
        if cross:
            notes.append({"code": "SYN_OTHER_SCOPE", "sys": "—", "key": "—", "witness": None,
                          "why": "同一個詞出現在不同範疇 %d 個(範疇不同不算衝突,只記):%s" % (len(cross), " · ".join(cross[:6]))})
        canon_of = {}
        for a in syn:
            canon_of.setdefault(norm_word(a["value"]), a)
        for a in syn:
            for w in a["aliases"]:
                b = canon_of.get(norm_word(w))
                if b is None or b is a or norm_word(b["value"]) == norm_word(a["value"]):
                    continue
                if any(norm_word(x) == norm_word(a["value"]) for x in b["aliases"]):
                    if (a["sys"], a["key"]) < (b["sys"], b["key"]):
                        case("SYN_CYCLE", "RED", "同義字", [who(a), who(b)], "%s 把 %s 當別名,%s 又把 %s 當別名(循環)" % (
                            a["key"], b["key"], b["key"], a["key"]), [a["vsha"], b["vsha"]], "裁定哪一個是正典鍵")
                else:
                    notes.append({"code": "SYN_CHAIN", "sys": a["sys"], "key": a["key"], "witness": None,
                                  "why": "別名「%s」本身是另一個正典鍵 %s(別名的別名)" % (w, b["key"])})
        # —— 編號帳(便宜的交叉檢;完整稽核仍是 CGC_MDL237 audit)——
        if data["grant"].get("_invalid"):
            case("NUM_GRANT_INVALID", "RED", "編號", [{"sys": "VCGC", "src": "grant", "key": "VCGC_NUMBER_GRANT"}],
                 "核發冊讀不了", ["grant-invalid"], "由 CGC_MDL278 grant 重出")
        by_code = {}
        for k, g in sorted((data["grant"].get("assets") or {}).items()):
            if isinstance(g, dict) and g.get("code"):
                by_code.setdefault(g["code"], []).append(k)
        for code, keys in sorted(by_code.items()):
            if len(keys) > 1:
                case("NUM_DUP_CODE", "RED", "編號", [{"sys": "VCGC", "src": "grant", "key": k} for k in keys],
                     "中央號 %s 同時掛在 %s(不同來源不得併號)" % (code, " · ".join(keys)), [code, keys],
                     "跑 via-vcgc run CGC_MDL237_NumberingSystem audit;重號由中央編號處理,本檔不改號")
        for a in assets:
            if a["grant_stale"]:
                case("NUM_STALE_GRANT", "YELLOW", "編號", [who(a)], "%s 已發號 %s,但內容指紋跟核發時不同(同一版號內容變了)" % (
                    a["key"], a["code"]), [a["vsha"], a["code"]], "由該系統出新版(supersedes)再送核")
        # —— 來源 ——
        for st in data["status"]:
            if st["state"] == "INVALID":
                case("SRC_INVALID", "RED", "來源", [{"sys": st["system"], "src": st["id"], "key": st["id"]}],
                     "來源 %s 讀不了:%s" % (st["id"], st["why"]), [st["why"]], "由 %s 自己的 manager 修(本檔只攤開不代修)" % st["system"])
        last = self.ledger.state()["sources"]
        for st in data["status"]:
            for f in st["files"]:
                prev = last.get(st["id"] + "|" + _family(f["path"]))
                if prev and f["version"] >= 0 and prev.get("version", -1) > f["version"]:
                    case("SRC_ROLLBACK", "RED", "來源", [{"sys": st["system"], "src": st["id"], "key": _family(f["path"])}],
                         "來源 %s 的尾版倒退:上次看到 v%04d,這次只有 v%04d" % (st["id"], prev["version"], f["version"]),
                         [prev["version"], f["version"]], "尾版被刪或回滾:由該系統確認後補回(只增不減)")
        for c in cases.values():
            c["sources_ok"] = all(p["src"] in ok_src or p["src"] == "grant" for p in c["parts"])
        return {"cases": cases, "notes": notes, "ok_src": sorted(ok_src), "elapsed": round(time.monotonic() - self._t0, 2)}

    # ---------- 血緣 ----------
    def lineage(self, data: dict, name: str) -> dict:
        nk = norm_key(name)
        concept = next((c for c in data["concepts"] if norm_key(c) == nk), None)
        members = {norm_key(m) for m in (data["concepts"].get(concept) or {}).get("members", [])} if concept else {nk}
        rows = [a for a in data["assets"] if norm_key(a["key"]) in members or norm_key(a.get("target") or "") in members
                or (a["kind"] == "SYNONYM" and nk in {norm_key(w) for w in a["aliases"]})]
        rows.sort(key=lambda a: (RANKS.index(a["rank"]), a["sys"], a["src"], a["key"]))
        golden, tie = (rows[0], False) if rows else (None, False)
        for b in rows[1:]:                  # 同位階又不等價的值:不挑(不用最後寫入者贏),等裁定
            if b["rank"] != rows[0]["rank"]:
                break
            same = b["vsha"] == rows[0]["vsha"] or (b["kind"] == rows[0]["kind"] == "REGEX"
                                                    and self.pair(b, rows[0])["rel"] in ("SAME_TEXT", "EQUAL"))
            tie = tie or not same
        out = []
        for a in rows:
            rel = None
            if golden is not None and a is not golden and a["kind"] == "REGEX" and golden["kind"] == "REGEX":
                rel = self.pair(a, golden)
            out.append({"sys": a["sys"], "src": a["src"], "path": a["path"], "key": a["key"], "rank": a["rank"], "code": a["code"],
                        "value": a["value"], "aliases": a["aliases"], "rel": rel})
        return {"name": name, "concept": concept, "parent": (data["concepts"].get(concept) or {}).get("parent") if concept else None,
                "golden": None if tie or not rows else out[0], "tie": tie, "rows": out}


_REL_ZH = {"EQUAL": "相等", "SUBSET": "前者是後者的子集", "SUPERSET": "前者包住後者", "OVERLAP": "交叉", "DISJOINT": "互斥",
           "SAME_TEXT": "同一式"}


def _family(path: str) -> str:
    stem = Path(path).stem
    return re.sub(r"_v\d{4}$", "", stem)


# ============================================================================================
# 六、案帳(只增 · 串雜湊 · 寫鎖 · 原子換檔)
# ============================================================================================
class LedgerError(Exception):
    pass


class Ledger:
    def __init__(self, path: Path, allow: list, clock=now_utc):
        self.path, self.allow, self.clock = Path(path), [Path(a) for a in allow], clock
        self.lock_left = None

    def guard(self, target: Path) -> Path:
        """寫入白名單:只准自己的案帳與報表夾;其餘(含他系統的任何檔)一律拒。"""
        t = Path(target).resolve()
        for a in self.allow:
            a = a.resolve()
            if t == a or a in t.parents:
                return t
        raise PermissionError("拒寫(不在本引擎的寫入白名單):%s" % target)

    def read(self):
        """→ (rows, problems)。problems 非空 = 帳不可信,不接受新增。"""
        if not self.path.is_file():
            return [], []
        rows, problems, prev = [], [], ""
        raw = self.path.read_bytes().decode("utf-8", "replace")
        lines = raw.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        elif lines:
            problems.append("TORN_TAIL:最後一列沒有換行(寫到一半中斷?)")
        for i, line in enumerate(lines):
            try:
                r = json.loads(line)
                body = {k: r[k] for k in ("seq", "ts", "type", "body")}
            except (ValueError, KeyError, TypeError):
                problems.append("TORN_OR_CORRUPT:第 %d 列讀不了" % (i + 1))
                break
            if r["seq"] != i:
                problems.append("SEQ_BROKEN:第 %d 列 seq=%s(有列被刪或插入)" % (i + 1, r["seq"]))
                break
            if r.get("prev") != prev or r.get("sha") != sha(prev + "\n" + canon(body)):
                problems.append("CHAIN_BROKEN:第 %d 列雜湊對不上(被改過)" % (i + 1))
                break
            prev = r["sha"]
            rows.append(r)
        return rows, problems

    def append(self, items: list) -> int:
        """items = [(type, body)]。整檔重寫到暫存檔再 os.replace(原子);同時只准一個寫入者。"""
        if not items:
            return 0
        target = self.guard(self.path)
        lock = target.with_name(target.name + ".lock")
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                age = time.time() - lock.stat().st_mtime
            except OSError:
                age = 0
            raise LedgerError("BUSY:另一個寫入者持有寫鎖(%.0f 秒前;%s)%s" % (
                age, lock.name, " — 超過 %d 秒的殘鎖請操作員確認後手動刪" % LOCK_STALE_SEC if age > LOCK_STALE_SEC else ""))
        try:
            os.write(fd, ("%d %s" % (os.getpid(), self.clock())).encode())
            os.close(fd)
            rows, problems = self.read()
            if problems:
                raise LedgerError("帳不可信,拒絕新增:" + ";".join(problems))
            prev = rows[-1]["sha"] if rows else ""
            out = [canon(r) for r in rows]
            for typ, body in items:
                row = {"seq": len(out), "ts": self.clock(), "type": typ, "body": body}
                row["prev"] = prev
                row["sha"] = prev = sha(prev + "\n" + canon({k: row[k] for k in ("seq", "ts", "type", "body")}))
                out.append(canon(row))
            tmp = target.with_name(target.name + ".tmp")
            with open(tmp, "wb") as fh:
                fh.write(("\n".join(out) + "\n").encode("utf-8"))
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, target)
            return len(items)
        finally:
            try:
                os.unlink(lock)
            except OSError as exc:
                self.lock_left = "%s:%s" % (lock.name, exc)      # 鎖刪不掉:下一次寫入會被 BUSY 擋下並報出來

    def state(self) -> dict:
        rows, problems = self.read()
        cases, sources = {}, {}
        for r in rows:
            b, t = r["body"], r["type"]
            if t == "SOURCE":
                sources[b["source"] + "|" + b["family"]] = b
                continue
            if t == "GENESIS":
                continue
            c = cases.setdefault(b["case"], {"case": b["case"], "state": "OPEN", "evidence_fp": None, "ruling": None, "opened": r["ts"]})
            if t == "CASE_OPEN":
                c.update(state="OPEN", evidence_fp=b["evidence_fp"], type=b["type"], sev=b["sev"], family=b.get("family"),
                         summary=b["summary"], parts=b.get("parts"))
                if c["ruling"] and c["ruling"]["evidence_fp"] == b["evidence_fp"]:
                    c["state"] = "RULED"
            elif t == "CASE_EVIDENCE":
                c.update(evidence_fp=b["evidence_fp"], summary=b["summary"])
                c["state"] = "STALE" if c["ruling"] else "OPEN"
            elif t == "RULING":
                c["ruling"] = b
                c["state"] = "RULED" if b["evidence_fp"] == c["evidence_fp"] else "STALE"
            elif t == "CASE_CLOSED":
                c["state"] = "CLOSED"
        return {"rows": len(rows), "problems": problems, "cases": cases, "sources": sources}

    def plan(self, detected: dict, status: list) -> list:
        """這一輪要補進帳的列(冪等:狀態沒變就 0 列)。來源缺席的案不結案。"""
        st = self.state()
        items = []
        if st["rows"] == 0:
            items.append(("GENESIS", {"engine": ENGINE, "tag": TAG, "rule": "只增;每列串前一列雜湊;案號 = 內容定址;裁定要帶操作員原話"}))
        for cid, c in sorted(detected.items()):
            old = st["cases"].get(cid)
            if old is None or old["state"] == "CLOSED":
                items.append(("CASE_OPEN", {"case": cid, "type": c["type"], "sev": c["sev"], "family": c["family"],
                                            "identity": c["identity"], "parts": c["parts"], "summary": c["summary"],
                                            "evidence_fp": c["evidence_fp"]}))
            elif old["evidence_fp"] != c["evidence_fp"]:
                items.append(("CASE_EVIDENCE", {"case": cid, "evidence_fp": c["evidence_fp"], "summary": c["summary"]}))
        ok = {s["id"] for s in status if s["state"] == "OK"} | {"grant"}
        for cid, old in sorted(st["cases"].items()):
            if old["state"] != "CLOSED" and cid not in detected:
                if all(p["src"] in ok for p in (old.get("parts") or [])):
                    items.append(("CASE_CLOSED", {"case": cid, "reason": "這一輪沒有再偵測到(來源都在)"}))
        for s in status:
            for f in s["files"]:
                key = s["id"] + "|" + _family(f["path"])
                prev = st["sources"].get(key)
                if prev is None or prev.get("sha") != f["sha"]:
                    if prev is None or f["version"] < 0 or f["version"] >= prev.get("version", -1):
                        items.append(("SOURCE", {"source": s["id"], "family": _family(f["path"]), "path": f["path"],
                                                 "version": f["version"], "sha": f["sha"]}))
        return items

    def rule(self, case_id: str, decision: str, order: str, note: str = "", apply: bool = False) -> dict:
        if decision not in DECISIONS:
            raise LedgerError("decision 只能是 %s" % " / ".join(DECISIONS))
        if not order or len(order.strip()) < 4:
            raise LedgerError("裁定要帶操作員原話(--order);引擎不替操作員裁定")
        st = self.state()
        if st["problems"]:
            raise LedgerError("帳不可信:" + ";".join(st["problems"]))
        c = st["cases"].get(case_id)
        if c is None or c["state"] == "CLOSED":
            raise LedgerError("沒有這個待裁的案:%s" % case_id)
        body = {"case": case_id, "decision": decision, "order": order.strip(), "note": note, "evidence_fp": c["evidence_fp"]}
        if apply:
            self.append([("RULING", body)])
        return {"case": case_id, "applied": apply, "ruling": body}


# ============================================================================================
# 七、彙總與輸出
# ============================================================================================
def lamp_of(sevs, unproven: int = 0, ledger_problems: int = 0) -> str:
    """燈的彙總規則:有紅就紅;有黃 / 不可證就黃;全沒有才綠。黃不是綠。"""
    if ledger_problems or "RED" in sevs:
        return "RED"
    if "YELLOW" in sevs or unproven:
        return "YELLOW"
    return "GREEN"


def summarize(eng: Engine, data: dict, det: dict) -> dict:
    st = eng.ledger.state()
    active = {}
    for cid, c in det["cases"].items():
        old = st["cases"].get(cid)
        state = "NEW" if old is None or old["state"] == "CLOSED" else (
            "STALE" if old["ruling"] and old["ruling"]["evidence_fp"] != c["evidence_fp"] else old["state"])
        active[cid] = dict(c, state=state)
    held = {cid: c for cid, c in st["cases"].items() if c["state"] != "CLOSED" and cid not in det["cases"]}
    systems = [s for s in data["systems"]] or sorted({s["system"] for s in data["status"]})
    matrix = {s: {f: [] for f in FAMILIES} for s in systems}
    for c in active.values():
        if c["state"] == "RULED":
            continue
        for p in c["parts"]:
            if p["sys"] in matrix:
                matrix[p["sys"]][c["family"]].append(c["sev"])
    unproven = [n for n in det["notes"] if n["code"] in ("RGX_UNPROVEN", "RGX_REDOS_SUSPECT")]
    cells = {}
    for s in systems:
        reported = [x for x in data["status"] if x["system"] == s or (x["system"] == "BY_OWNER")]
        has = any(a["sys"] == s for a in data["assets"])
        own = [x for x in data["status"] if x["system"] == s]
        for f in FAMILIES:
            if f == "來源":
                cells[(s, f)] = "RED" if any(x["state"] == "INVALID" for x in own) or matrix[s][f] else (
                    "GREEN" if has else "NODATA")
            elif not has and not matrix[s][f]:
                cells[(s, f)] = "NODATA" if reported is not None else "—"
            else:
                up = sum(1 for n in unproven if n["sys"] == s) if f == "正則" else 0
                cells[(s, f)] = lamp_of(matrix[s][f], up)
    open_sev = [c["sev"] for c in active.values() if c["state"] != "RULED"]
    lamp = lamp_of(open_sev, len(unproven), len(st["problems"]))
    return {"lamp": lamp, "cells": cells, "systems": systems, "active": active, "held": held, "ledger": st,
            "unproven": len(unproven), "coverage": "%d/%d" % (
                sum(1 for s in systems if s not in data["pseudo"] and any(a["sys"] == s for a in data["assets"])),
                sum(1 for s in systems if s not in data["pseudo"]))}


def run_check(eng: Engine, apply: bool = False, extra: list | None = None) -> dict:
    data = eng.load(extra)
    det = eng.detect(data)
    summ = summarize(eng, data, det)
    plan = eng.ledger.plan(det["cases"], data["status"]) if not summ["ledger"]["problems"] else []
    wrote = 0
    if apply and not extra:
        wrote = eng.ledger.append(plan)
        summ = summarize(eng, data, det)
        rep = eng.ledger.guard(eng.via.joinpath(*REPORT_DIR) / "SSOT_CONSISTENCY_latest.json")
        rep.parent.mkdir(parents=True, exist_ok=True)
        rep.write_text(json.dumps(report(eng, data, det, summ), ensure_ascii=False, indent=1), encoding="utf-8")
    return {"data": data, "det": det, "summ": summ, "plan": plan, "wrote": wrote}


def report(eng: Engine, data: dict, det: dict, summ: dict) -> dict:
    return {"schema": "VIA.SSOT.ConsistencyReport.v1", "engine": ENGINE + "_" + TAG, "ts": eng.clock(), "lamp": summ["lamp"],
            "coverage": summ["coverage"], "sources_book": data["book"],
            "matrix": {s: {f: summ["cells"][(s, f)] for f in FAMILIES} for s in summ["systems"]},
            "sources": data["status"], "cases": sorted(summ["active"].values(), key=lambda c: (-SEV_ORDER[c["sev"]], c["case"])),
            "held": sorted(summ["held"].values(), key=lambda c: c["case"]),
            "notes": det["notes"], "ledger": {"rows": summ["ledger"]["rows"], "problems": summ["ledger"]["problems"]}}


def print_check(res: dict, eng: Engine) -> None:
    data, det, summ = res["data"], res["det"], res["summ"]
    print("[SSOT 一致性] %s · %s %s · 資產 %d · 案 %d(紅 %d · 黃 %d · 已裁定 %d)· 不可證 %d · 已自報 %s 系統 · %.1fs" % (
        summ["lamp"], ENGINE, TAG, len(data["assets"]), len(summ["active"]),
        sum(1 for c in summ["active"].values() if c["sev"] == "RED" and c["state"] != "RULED"),
        sum(1 for c in summ["active"].values() if c["sev"] == "YELLOW" and c["state"] != "RULED"),
        sum(1 for c in summ["active"].values() if c["state"] == "RULED"), summ["unproven"], summ["coverage"], det["elapsed"]))
    print("  %-14s %s" % ("系統", "  ".join("%-8s" % f for f in FAMILIES)))
    for s in summ["systems"]:
        print("  %-14s %s" % (s, "  ".join("%-8s" % summ["cells"][(s, f)] for f in FAMILIES)))
    for st in data["status"]:
        if st["state"] != "OK":
            print("  [來源] %-8s %s · %s · %s" % (st["state"], st["system"], st["id"], st["why"]))
    for c in sorted(summ["active"].values(), key=lambda c: (c["state"] == "RULED", -SEV_ORDER[c["sev"]], c["case"])):
        print("  [%s] %s %-6s %s · %s" % (c["case"], c["state"], c["sev"], c["type"], c["summary"][:300]))
    for c in sorted(summ["held"].values(), key=lambda c: c["case"]):
        print("  [%s] %s(帳上未結;這一輪沒再偵測到)" % (c["case"], c["state"]))
    tally = {}
    for n in det["notes"]:
        tally[n["code"]] = tally.get(n["code"], 0) + 1
    if tally:
        print("  [附記] " + " · ".join("%s %d" % kv for kv in sorted(tally.items())))
    if summ["ledger"]["problems"]:
        print("  [案帳] RED " + ";".join(summ["ledger"]["problems"]))
    print("  [案帳] %d 列 · 這一輪%s %d 列" % (summ["ledger"]["rows"], "已補" if res["wrote"] else "要補", res["wrote"] or len(res["plan"])))
    opens = [c for c in summ["active"].values() if c["state"] != "RULED"]
    print("  NEXT: " + ("python %s rule <案號> --decision <%s> --order \"<操作員原話>\" --apply" % (
        Path(__file__).name, "|".join(DECISIONS)) if opens else "無待裁的案"))


def print_view(v: dict) -> None:
    print("[血緣] %s%s · 來源 %d 列" % (v["name"], "(概念;上層 %s)" % v["parent"] if v["concept"] else "", len(v["rows"])))
    if v["tie"]:
        print("  採信值:待裁(同位階有不同值;不用最後寫入者贏)")
    for i, r in enumerate(v["rows"]):
        tag = "採信值" if v["golden"] is not None and i == 0 else ("同位階" if v["tie"] and r["rank"] == v["rows"][0]["rank"] else "其他來源")
        val = r["value"] if isinstance(r["value"], str) else json.dumps(r["value"], ensure_ascii=False)
        rel = ""
        if r["rel"]:
            rel = " · 與%s:%s" % ("首列" if v["tie"] else "採信值", _REL_ZH.get(r["rel"]["rel"], r["rel"]["rel"]))
            if r["rel"].get("why"):
                rel += "(%s)" % r["rel"]["why"]
            for lab, k in (("只有它收", "a_only"), ("只有%s收" % ("首列" if v["tie"] else "採信值"), "b_only")):
                if r["rel"].get(k) is not None:
                    rel += " · %s %s" % (lab, show(r["rel"][k]))
        print("  %-6s [%s · %s · %s%s] %s = %s%s" % (tag, r["sys"], r["src"], r["rank"], " · " + r["code"] if r["code"] else "",
                                                     r["key"], val[:160], rel))
    if not v["rows"]:
        print("  沒有任何來源宣告這個鍵")


def load_fmea(registry: Path) -> dict:
    hits = sorted(Path(registry).glob(FMEA_GLOB), key=_vnum)
    if not hits:
        raise ValueError("失敗情境冊不存在(%s)" % FMEA_GLOB)
    return read_json(hits[-1])


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a and not a[0].startswith("--") else "check"
    rest = a[1:] if a and not a[0].startswith("--") else a
    flags = {x for x in rest if x.startswith("--")}

    def opt(name):
        return rest[rest.index(name) + 1] if name in rest and rest.index(name) + 1 < len(rest) else None
    known = {"check": {"--apply", "--json"}, "view": set(), "probe": {"--json"}, "cases": {"--all"}, "ledger": set(), "fmea": set(),
             "rule": {"--decision", "--order", "--note", "--apply"}}
    if verb not in known or flags - known[verb]:
        print("用法:python %s check [--apply] [--json] | view <鍵或概念> | probe <提案檔> | cases [--all] | "
              "rule <案號> --decision <..> --order \"..\" [--apply] | ledger | fmea | --selftest" % Path(__file__).name)
        return 2
    eng = Engine()
    try:
        if verb == "fmea":
            book = load_fmea(eng.registry)
            for m in book["modes"]:
                print("  %s [%s] %s\n      防護:%s\n      自動化:%s" % (m["id"], m["group"], m["scenario"], m["guard"], m["automation"]))
            print("[失敗情境] %d 項 · 每項都有自測(--selftest)" % len(book["modes"]))
            return 0
        if verb == "ledger":
            st = eng.ledger.state()
            print("[案帳] %s · %d 列 · 案 %d(未結 %d)" % ("RED " + ";".join(st["problems"]) if st["problems"] else "GREEN 雜湊鏈完整",
                                                      st["rows"], len(st["cases"]), sum(1 for c in st["cases"].values() if c["state"] != "CLOSED")))
            return 1 if st["problems"] else 0
        if verb == "cases":
            st = eng.ledger.state()
            for cid, c in sorted(st["cases"].items()):
                if c["state"] != "CLOSED" or "--all" in flags:
                    print("  [%s] %-6s %s · %s%s" % (cid, c["state"], c.get("type"), (c.get("summary") or "")[:200],
                                                     " · 裁定 %s" % c["ruling"]["decision"] if c["ruling"] else ""))
            print("[案帳] %d 列 · 案 %d" % (st["rows"], len(st["cases"])))
            return 1 if st["problems"] else 0
        if verb == "rule":
            pos = [x for i, x in enumerate(rest) if not x.startswith("--") and (i == 0 or rest[i - 1] not in ("--decision", "--order", "--note"))]
            r = eng.ledger.rule(pos[0] if pos else "", opt("--decision") or "", opt("--order") or "", opt("--note") or "",
                                apply="--apply" in flags)
            print("[裁定] %s %s · %s · 操作員原話「%s」" % ("已記帳" if r["applied"] else "預覽(加 --apply 才記帳)", r["case"],
                                                  r["ruling"]["decision"], r["ruling"]["order"]))
            return 0
        if verb == "view":
            pos = [x for x in rest if not x.startswith("--")]
            if not pos:
                print("view 要給鍵或概念名")
                return 2
            print_view(eng.lineage(eng.load(), pos[0]))
            return 0
        extra = None
        if verb == "probe":
            pos = [x for x in rest if not x.startswith("--")]
            if not pos or not Path(pos[0]).is_file():
                print("probe 要給提案檔(JSON)")
                return 2
            extra = [{"id": "probe", "system": "OPERATOR", "adapter": "proposal", "glob": str(Path(pos[0]).resolve()), "absolute": True}]
        res = run_check(eng, apply="--apply" in flags, extra=extra)
        if "--json" in flags:
            print(json.dumps(report(eng, res["data"], res["det"], res["summ"]), ensure_ascii=False, indent=1))
        else:
            print_check(res, eng)
        return 0 if res["summ"]["lamp"] == "GREEN" else 1
    except (ValueError, LedgerError, PermissionError) as exc:
        print("[SSOT 一致性] RED · %s" % exc)
        return 2 if isinstance(exc, LedgerError) and "原話" in str(exc) else 1


# ============================================================================================
# 八、自測(暫存夾;30 個失敗情境逐項驗)
# ============================================================================================
def _fixture(root: Path, **over) -> Path:
    reg = root / "supportive modules" / "registry"
    reg.mkdir(parents=True, exist_ok=True)
    (root / "functional modules" / "VDF" / "contract").mkdir(parents=True, exist_ok=True)
    h = "a" * 64
    book = {"schema": "VIA.SSOT.ConsistencyEngine.Sources.v1", "version": "v0100",
            "systems": ["VCGC", "VDF", "VRN", "VAP", "VQG", "OPERATOR"],
            "grant_book": "supportive modules/registry/VCGC_NUMBER_GRANT_latest.json",
            "concepts": {"tw_stock_ticker": {"parent": "ticker", "members": ["TW_TICKER", "tw_stock_ticker"]}},
            "sources": [
                {"id": "vcgc.central", "system": "VCGC", "adapter": "central_book",
                 "glob": "supportive modules/registry/VIA_Central_Synonym_Regex_v[0-9][0-9][0-9][0-9].json"},
                {"id": "vcgc.candidates", "system": "BY_OWNER", "adapter": "asset_candidates",
                 "glob": "supportive modules/registry/VIA_AssetCandidates_SSOT_v[0-9][0-9][0-9][0-9].json"},
                {"id": "vdf.request", "system": "VDF", "adapter": "number_request",
                 "glob": "functional modules/VDF/contract/*_NUMBER_REQUEST_latest.json"},
                {"id": "vap.request", "system": "VAP", "adapter": "number_request",
                 "glob": "functional modules/VAP/contract/*_NUMBER_REQUEST_latest.json"},
                {"id": "operator.proposal", "system": "OPERATOR", "adapter": "proposal",
                 "glob": "supportive modules/registry/VIA_SSOT_Proposal_*_v[0-9][0-9][0-9][0-9].json"}]}
    central = {"regex": {"TW_TICKER": {"pattern": r"^[1-9]\d{3}$", "locked": True},
                         "TW_TICKER_ALIAS": {"pattern": r"^([1-9]\d{3})$", "locked": True, "alias_of": "TW_TICKER(正本)"},
                         "TW_BBG": {"pattern": r"^[1-9][0-9]{3}\s*TT$", "locked": True},
                         "TW_BBG2": {"pattern": r"^[1-9][0-9]{3}\s+TT$", "locked": True, "alias_of": "TW_BBG"}},
               "synonyms": {"EPS": ["每股盈餘", "eps"], "RATING_BUY": ["買進", "Buy"]}, "synonyms_meta": {}}

    def cand(cid, typ, owner, scope, skey, value, aliases=(), pos=(), neg=(), ptr=None, shax=h):
        return {"candidate_id": cid, "ssot_code": None, "asset_type": typ, "owner": owner, "source_id": "t:" + cid,
                "source_pointer": ptr or cid, "source_sha256": shax, "version": "1.0.0", "supersedes": None, "scope": scope,
                "semantic_key": skey, "name": cid, "value": value, "risk_level": "LOW", "environment": "via_core",
                "libraries": [], "aliases": list(aliases), "positive": list(pos), "negative": list(neg)}
    cands = {"schema": "x", "version": "v0100", "assets": [
        cand("c1", "REGEX", "VDF", "tw.code", "four", r"^[0-9]{4}$", pos=["2330"], neg=["23301"]),
        cand("c2", "SYNONYM", "VDF", "central:eps", "EPS_DILUTED", "EPS_DILUTED", aliases=["ＥＰＳ"])]}
    grant = {"assets": {"c1": {"code": "VIA-VDF-RGX001", "version": "1.0.0", "source_sha256": h}}}
    files = {"VIA_SSOT_ConsistencyEngine_Sources_SSOT_v0100.json": book, "VIA_Central_Synonym_Regex_v0100.json": central,
             "VIA_AssetCandidates_SSOT_v0100.json": cands, "VCGC_NUMBER_GRANT_latest.json": grant}
    files.update(over)
    for name, obj in files.items():
        if obj is None:
            continue
        p = reg / name
        if isinstance(obj, bytes):
            p.write_bytes(obj)
        else:
            p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return reg


def selftest() -> int:
    ok, total, failed = 0, 0, []
    seen_modes = set()

    def chk(mode, name, cond, note=""):
        nonlocal ok, total
        total += 1
        seen_modes.add(mode)
        if cond:
            ok += 1
        else:
            failed.append("%s %s %s" % (mode, name, note))
        print("  [%s] %s %s %s" % ("OK " if cond else "NG ", mode, name, note))

    def rel(a, b, mode="full"):
        try:
            return relate(build_lang(a, mode), build_lang(b, mode))
        except Unsupported as exc:
            return {"rel": "UNPROVEN", "why": str(exc)}

    def types(res):
        return {c["type"] for c in res["summ"]["active"].values()}

    with tempfile.TemporaryDirectory(prefix="via_scc_") as td:
        td = Path(td)
        # --- 證明器的地基:跟 Python 的 re 對答案 ---
        probes = ["2330", "0050", "2026", "2030", "1000", "12345", "23", "2330\n", "2330.TW", "2330.TWO", "2330 TT", "2330TT", "abc"]
        pats = [r"^(?:[1-9]\d{3})$|^(?!202[1-9]|2030)\d{4}$", r"^[1-9]\d{3}\.(TW|TWO)$", r"^[1-9]\d{3}\s*TT$", r"(?i)^[a-c]+$",
                r"(?<!\d)([1-9]\d{3})(?!\d)", r"\d{4}\Z", r"^[^0-9]*$"]
        agree = all(accepts(build_lang(p, m), s) == bool(re.fullmatch(p, s) if m == "full" else re.search(p, s))
                    for p in pats for m in ("full", "search") for s in probes)
        chk("P00", "自動機與 re 的判法一致(%d 式 × 2 用法 × %d 樣本)" % (len(pats), len(probes)), agree)

        # --- F01 寫到別的系統 ---
        reg = _fixture(td / "f01")
        eng = Engine(td / "f01")
        try:
            eng.ledger.guard(td / "f01" / "functional modules" / "VDF" / "VDF_Config.json")
            blocked = False
        except PermissionError:
            blocked = True
        chk("F01", "寫他系統的檔被白名單擋下", blocked and eng.ledger.guard(reg / LEDGER_NAME) == (reg / LEDGER_NAME).resolve())
        # --- F02 耦合 / 觸網 ---
        mods = set()
        for node in ast.walk(ast.parse(Path(__file__).read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                mods |= {n.name.split(".")[0] for n in node.names}
            elif isinstance(node, ast.ImportFrom):
                mods.add((node.module or "").split(".")[0])
        allowed = {"__future__", "ast", "bisect", "contextlib", "io", "datetime", "hashlib", "json", "os", "re", "sys", "tempfile", "time", "unicodedata",
                   "pathlib", "sre_constants", "sre_parse", "VIA_SuperAccel_Module"}
        chk("F02", "只匯入標準庫(無他系統程式 · 無網路模組)", mods <= allowed, str(sorted(mods - allowed)))
        # --- F03 來源缺席 ---
        res = run_check(eng)
        cells = res["summ"]["cells"]
        chk("F03", "沒自報的系統標 NODATA,其他系統照跑", cells[("VAP", "正則")] == "NODATA" and cells[("VCGC", "來源")] == "GREEN"
            and len(res["data"]["assets"]) > 0)
        # --- F04 壞檔 / 編碼 ---
        _fixture(td / "f04", **{"VIA_AssetCandidates_SSOT_v0100.json": b"\xa4\xa4\xa4\xe5{"})
        (td / "f04" / "supportive modules" / "registry" / "VIA_Central_Synonym_Regex_v0100.json").write_bytes(
            b"\xef\xbb\xbf" + json.dumps({"regex": {"K": {"pattern": "^a$"}}}).encode())
        r4 = run_check(Engine(td / "f04"))
        chk("F04", "壞編碼的冊記 SRC_INVALID;帶 BOM 的冊照讀;不拖垮整輪", "SRC_INVALID" in types(r4)
            and any(a["key"] == "K" for a in r4["data"]["assets"]) and r4["summ"]["lamp"] == "RED")
        # --- F05 絕對路徑進帳 ---
        w = run_check(eng, apply=True)
        text = (reg / LEDGER_NAME).read_text(encoding="utf-8")
        paths = [r["body"]["path"] for r in eng.ledger.read()[0] if r["type"] == "SOURCE"]
        chk("F05", "帳內只有相對正斜線路徑", w["wrote"] > 0 and str(td) not in text and len(paths) >= 2
            and all(x.startswith("supportive modules/") and "\\" not in x and ":" not in x for x in paths))
        # --- F06 同值不同來源不合併 ---
        _fixture(td / "f06", **{"VIA_SSOT_Proposal_T_v0100.json": {"assets": [
            {"key": "TW_TICKER", "kind": "REGEX", "pattern": r"^[1-9]\d{3}$"}]}})
        e6 = Engine(td / "f06")
        v6 = e6.lineage(e6.load(), "TW_TICKER")
        same = [r for r in v6["rows"] if r["key"] == "TW_TICKER"]
        chk("F06", "值相同的兩個來源各留一列、不併", len(same) == 2 and {r["sys"] for r in same} == {"VCGC", "OPERATOR"}
            and v6["golden"]["rank"] == "LOCKED" and "RGX_KEY_DIVERGE" not in types(run_check(e6)))
        # --- F07 寫法不同但等價 ---
        chk("F07", "寫法不同、語言相等 → 自動視為一致", rel(r"^(a|b)c$", r"^[ab]c$")["rel"] == "EQUAL"
            and "RGX_ALIAS_DRIFT" in types(res)
            and not any("TW_TICKER_ALIAS" in c["summary"] for c in res["summ"]["active"].values() if c["type"] == "RGX_ALIAS_DRIFT"))
        # --- F08 編號帳 ---
        g8 = {"assets": {"c1": {"code": "VIA-VDF-RGX001", "version": "1.0.0", "source_sha256": "b" * 64},
                         "zz": {"code": "VIA-VDF-RGX001", "version": "1.0.0", "source_sha256": "c" * 64}}}
        _fixture(td / "f08", **{"VCGC_NUMBER_GRANT_latest.json": g8})
        t8 = types(run_check(Engine(td / "f08")))
        chk("F08", "重號與核發指紋過期都抓得到", {"NUM_DUP_CODE", "NUM_STALE_GRANT"} <= t8)
        # --- F09 提案不改 LOCKED ---
        prop = {"assets": [{"key": "tw_stock_ticker", "kind": "REGEX", "pattern": r"^[1-9][0-9]{3}[a-zA-Z]?$",
                            "positive": ["2330", "2881A"], "negative": ["0050"]}]}
        _fixture(td / "f09", **{"VIA_SSOT_Proposal_T_v0100.json": prop})
        before = (td / "f09" / "supportive modules" / "registry" / "VIA_Central_Synonym_Regex_v0100.json").read_bytes()
        e9 = Engine(td / "f09")
        r9 = run_check(e9, apply=True)
        c9 = [c for c in r9["summ"]["active"].values() if c["type"] == "RGX_CONCEPT_DIVERGE"]
        chk("F09", "提案與 LOCKED 不等價 → 開案待裁;LOCKED 冊一個位元都沒動", len(c9) == 1 and "LOCKED" not in c9[0]["state"]
            and before == (td / "f09" / "supportive modules" / "registry" / "VIA_Central_Synonym_Regex_v0100.json").read_bytes()
            and e9.lineage(e9.load(), "tw_stock_ticker")["golden"]["key"] == "TW_TICKER")
        # --- F10 不可證不給綠 ---
        r10 = rel(r"^(a)\1$", r"^aa$")
        chk("F10", "超出可證範圍 → UNPROVEN(燈不會是綠)", r10["rel"] == "UNPROVEN" and lamp_of([], unproven=1) == "YELLOW")
        # --- F11 子集吞噬 ---
        r11 = rel("台指期結算", "台指期", "search")
        chk("F11", "子集吞噬(台指期結算 ⊂ 台指期)", r11["rel"] == "SUBSET" and r11["b_only"] == "台指期")
        # --- F12 交叉覆蓋 ---
        r12 = rel(r"^[A-Z]{3}\d$", r"^VI.\d$")
        chk("F12", "交叉覆蓋附三種見證", r12["rel"] == "OVERLAP" and all(r12[k] is not None for k in ("both", "a_only", "b_only"))
            and rel(r"^VIX 報價$", r"^[A-Z]{3} 報價$")["rel"] == "SUBSET")
        # --- F13 ReDoS ---
        t0 = time.monotonic()
        l13 = [f["code"] for f in lint(r"(a+)+$")]
        fast = accepts(build_lang(r"(a+)+$", "search"), "a" * 4000 + "!") is False
        chk("F13", "ReDoS 靜態抓到;引擎自己比對不回溯", "RGX_REDOS" in l13 and fast and time.monotonic() - t0 < 20
            and "RGX_REDOS" not in [f["code"] for f in lint(r"(?:a+b)+$")])
        # --- F14 方言 / 錨點語意 ---
        l14 = {f["code"]: f for f in lint(r"^[1-9]\d{3}$")}
        w14 = l14.get("RGX_DIALECT_DRIFT", {}).get("witness") or ""
        chk("F14", "\\d 收非 ASCII 數字、`$` 放過結尾換行", bool(w14) and re.fullmatch(r"^[1-9]\d{3}$", w14) is not None
            and re.fullmatch(r"^[1-9]\d{3}$", w14, re.ASCII) is None and "RGX_DOLLAR_NEWLINE" in l14
            and accepts(build_lang(r"^\d{4}$", "search"), "2330\n") and not accepts(build_lang(r"^\d{4}\Z", "search"), "2330\n")
            and "RGX_DIALECT_DRIFT" not in {f["code"] for f in lint(r"^[1-9][0-9]{3}$")}, show(w14))
        # --- F15 死分支 ---
        chk("F15", "死分支", "RGX_DEAD_BRANCH" in [f["code"] for f in lint(r"^\d{4}$|^2330$")]
            and "RGX_DEAD_BRANCH" not in [f["code"] for f in lint(r"^2330$|^\d{5}$")])
        # --- F16 搶樣本 / F17 自己的樣本 ---
        cs = json.loads((reg / "VIA_AssetCandidates_SSOT_v0100.json").read_text(encoding="utf-8"))
        tmpl = cs["assets"][0]
        cs["assets"] += [dict(tmpl, candidate_id="c3", source_pointer="c3", semantic_key="year", value=r"^20[0-9]{2}$",
                              positive=["2026"], negative=["1999"]),
                         dict(tmpl, candidate_id="c4", source_pointer="c4", semantic_key="bad", scope="tw.other", value=r"^[a-z]+$",
                              positive=["ABC"], negative=["abc"])]
        _fixture(td / "f16", **{"VIA_AssetCandidates_SSOT_v0100.json": cs})
        t16 = types(run_check(Engine(td / "f16")))
        chk("F16", "同範疇不同鍵有交疊 → 開案", "RGX_SCOPE_OVERLAP" in t16)
        chk("F17", "式子自己的正反例不過 → 紅", "RGX_EXAMPLE_FAILED" in t16)
        # --- F18 規模上限 ---
        try:
            relate(build_lang(r"^(a|b)*a(a|b){11}$"), build_lang(r"^(a|b)*b(a|b){11}$"), cap=200)
            capped = False
        except Unsupported as exc:
            capped = "CAP" in str(exc)
        e18 = Engine(td / "f01", budget=-1.0)
        chk("F18", "狀態爆炸 / 超時 → UNPROVEN,不硬算、不給綠", capped and e18.pair(
            _asset(key="a", value=r"^a+$"), _asset(key="b", value=r"^a*$"))["rel"] == "UNPROVEN")
        # --- F19–F22 同義字 ---
        chk("F19", "一詞兩主(跨來源)", any(c["type"] == "SYN_MULTI_TARGET" and "eps" in c["summary"] for c in res["summ"]["active"].values()))
        chk("F20", "全形 / 大小寫 / 空白正規化後才比", norm_word("ＥＰＳ ") == norm_word("eps") == "eps"
            and any("正規化後相撞" in c["summary"] for c in res["summ"]["active"].values()))
        cen = json.loads((reg / "VIA_Central_Synonym_Regex_v0100.json").read_text(encoding="utf-8"))
        cen["synonyms"] = {"AAA": ["BBB", "x1"], "BBB": ["AAA", "x2"]}
        cen["synonyms_meta"] = {"AAA": {"namespace": "n1"}, "BBB": {"namespace": "n2"}}
        _fixture(td / "f21", **{"VIA_Central_Synonym_Regex_v0100.json": cen, "VIA_AssetCandidates_SSOT_v0100.json": {"assets": []}})
        r21 = run_check(Engine(td / "f21"))
        chk("F21", "同義字循環", "SYN_CYCLE" in types(r21))
        cen2 = dict(cen, synonyms={"RATING_HOLD": ["N", "中立"], "DIRECTION": ["N", "北"]},
                    synonyms_meta={"RATING_HOLD": {"namespace": "rating"}, "DIRECTION": {"namespace": "geo"}})
        _fixture(td / "f22", **{"VIA_Central_Synonym_Regex_v0100.json": cen2, "VIA_AssetCandidates_SSOT_v0100.json": {"assets": []}})
        r22 = run_check(Engine(td / "f22"))
        chk("F22", "同詞不同範疇只記不報衝突", "SYN_MULTI_TARGET" not in types(r22)
            and any(n["code"] == "SYN_OTHER_SCOPE" for n in r22["det"]["notes"]))
        # --- F23 冪等 ---
        again = run_check(eng, apply=True)
        ids1, ids2 = sorted(w["summ"]["active"]), sorted(again["summ"]["active"])
        chk("F23", "重跑同一案得同一號、不多寫一列", again["wrote"] == 0 and ids1 == ids2 and len(ids1) > 0)
        # --- F24 竄改 ---
        lp = reg / LEDGER_NAME
        good = lp.read_text(encoding="utf-8")
        lines = good.split("\n")
        lp.write_text("\n".join([lines[0], lines[1].replace("SCC-", "SCX-", 1)] + lines[2:]), encoding="utf-8")
        tam = eng.ledger.state()["problems"]
        lp.write_text("\n".join(lines[:1] + lines[2:]), encoding="utf-8")
        cut = eng.ledger.state()["problems"]
        lp.write_text(good, encoding="utf-8")
        chk("F24", "改一個字、刪一列都驗得出", any("CHAIN_BROKEN" in p for p in tam) and any("SEQ_BROKEN" in p for p in cut)
            and not eng.ledger.state()["problems"])
        # --- F25 並行 ---
        lock = lp.with_name(lp.name + ".lock")
        lock.write_text("x")
        try:
            eng.ledger.append([("SOURCE", {"source": "t", "family": "t", "path": "t", "version": 1, "sha": "0"})])
            busy = False
        except LedgerError as exc:
            busy = "BUSY" in str(exc)
        lock.unlink()
        chk("F25", "第二個寫入者被寫鎖擋下,帳沒被動", busy and lp.read_text(encoding="utf-8") == good)
        # --- F26 寫到一半 ---
        lp.write_text(good + '{"seq": 99, "ts":', encoding="utf-8")
        torn = eng.ledger.state()["problems"]
        try:
            eng.ledger.append([("SOURCE", {"source": "t", "family": "t", "path": "t", "version": 1, "sha": "0"})])
            refused = False
        except LedgerError:
            refused = True
        lp.write_text(good, encoding="utf-8")
        chk("F26", "殘尾照實報、帳不可信時拒絕新增;換檔是原子的", any("TORN" in p for p in torn) and refused
            and not list(reg.glob("*.tmp")) and not list(reg.glob("*.lock")))
        # --- F27 / F28 裁定 ---
        cid = c9[0]["case"]
        try:
            e9.ledger.rule(cid, "KEEP_GOLDEN", "", apply=True)
            no_order = False
        except LedgerError:
            no_order = True
        with contextlib.redirect_stdout(io.StringIO()):
            rc_rule = main(["rule", "SCC-0000000000", "--decision", "WAIVE"])
        chk("F28", "沒帶操作員原話不能裁定;引擎不自己裁定", no_order and rc_rule == 2
            and e9.ledger.state()["cases"][cid]["ruling"] is None)
        e9.ledger.rule(cid, "KEEP_GOLDEN", "操作員 2026-11-13 測試:維持四碼", apply=True)
        ruled = run_check(e9)["summ"]["active"][cid]["state"]
        prop["assets"][0]["pattern"] = r"^[1-9][0-9]{3}[A-Z]?$"
        (td / "f09" / "supportive modules" / "registry" / "VIA_SSOT_Proposal_T_v0101.json").write_text(json.dumps(prop), encoding="utf-8")
        e9b = Engine(td / "f09")
        stale = run_check(e9b)["summ"]["active"][cid]["state"]
        chk("F27", "裁定後證據變了 → 裁定失效重開", ruled == "RULED" and stale == "STALE", "%s → %s" % (ruled, stale))
        # --- F29 尾版倒退 + 來源缺席不結案 ---
        (td / "f09" / "supportive modules" / "registry" / "VIA_SSOT_Proposal_T_v0101.json").write_text(json.dumps(prop), encoding="utf-8")
        run_check(Engine(td / "f09"), apply=True)
        (td / "f09" / "supportive modules" / "registry" / "VIA_SSOT_Proposal_T_v0101.json").unlink()
        r29 = run_check(Engine(td / "f09"))
        (td / "f09" / "supportive modules" / "registry" / "VIA_SSOT_Proposal_T_v0100.json").unlink()
        gone = run_check(Engine(td / "f09"))
        chk("F29", "尾版倒退抓得到;來源整個不見時案不會被默默結掉", "SRC_ROLLBACK" in types(r29)
            and not any(t == "CASE_CLOSED" and b["case"] == cid for t, b in gone["plan"]) and cid in gone["summ"]["held"])
        # --- F30 燈與 rc 不說謊 ---
        back = [60]

        def backwards():                    # 每叫一次就往回走一秒的鐘
            back[0] -= 1
            return "2026-01-01T00:00:%02d+00:00" % max(back[0], 0)
        _fixture(td / "f30")
        e30 = Engine(td / "f30", clock=backwards)
        run_check(e30, apply=True)
        rows30, prob30 = e30.ledger.read()
        chk("F30", "黃不是綠;時鐘倒退也不亂序(順序靠 seq)", lamp_of(["YELLOW"]) == "YELLOW" and lamp_of([], 1) == "YELLOW"
            and lamp_of(["YELLOW", "RED"]) == "RED" and lamp_of([]) == "GREEN" and lamp_of([], 0, 1) == "RED"
            and [r["seq"] for r in rows30] == list(range(len(rows30))) and not prob30
            and all(r["ts"].endswith("+00:00") for r in rows30) and res["summ"]["lamp"] != "GREEN")
        # --- 失敗情境冊 ↔ 自測 對得上 ---
        try:
            book = load_fmea(HERE)
            ids = [m["id"] for m in book["modes"]]
            chk("P01", "失敗情境冊 %d 項,每一項都有對應自測" % len(ids), len(ids) == 30 and len(set(ids)) == 30
                and set(ids) <= seen_modes, str(sorted(set(ids) - seen_modes)))
        except ValueError as exc:
            chk("P01", "失敗情境冊讀得到", False, str(exc))
    print("[%s %s 自測] %d/%d%s" % (ENGINE, TAG, ok, total, "" if ok == total else " · 不過:" + ";".join(failed)))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())

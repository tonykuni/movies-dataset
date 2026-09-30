#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SUP_MDL749_VRNFieldRuleHub v0116 — 薄尾:VRN SSOT 一致性(consistency)+ 正則文字自檢(regexcheck)+ 薄尾鏈量尺修正

側線 2026-09-30(VCGC→VRN 軌;操作員令「VCGC→VRN 所有 SSOT REGEX / 同義字 / 邏輯一致,嚴守 GitHub 已鎖架構,
不擴範圍、不漂移;輸出=驗證=結果驗證」)。只經 VCGC 呼叫:新動詞要 VIA_FROM_VCGC=YES(沒有就拒絕,rc 2)。

① 量尺修正(本家族自己的紅):v0115 自測 ⑭ FAIL —— `drift` / `downstream` 用 `read_text()` 讀現役引擎的**尾版檔字面**,
   ENG073 v0139 是薄尾(119 行,`__getattr__` 轉接 v0138 本體),字面上沒有樞紐印記 → 被量成 DRIFT 9/66、目標價 1/16;
   SSOT 全景 SYN@VRN 的「下游落差 3 支」其中 ENG073 那一支就是這把尺的假紅(與全景 v0116「看不見薄尾鏈」同一類)。
   本尾版:`_newest` / `_live_tails` 回傳的路徑讀文字時沿薄尾鏈接回本體(尾 → 前版 … → 第一個非薄尾檔),
   並把本家族自己的尾版排除在「消費者」之外(不然本尾版會把 ORPHAN 洗成 USED)。其餘判定函式一位元不改。
② `consistency`:評等詞彙 × 目標價同義字,跨冊(中央同義字冊 · 規則正本冊 · S05 欄位冊 · 同義字聯集冊 · 機構 SSOT)
   與程式常數(ENG086 · ENG073,AST 零執行取字面,沿薄尾鏈)逐詞攤開:
     同一詞在不同來源落在**不同方向**(POSITIVE/NEUTRAL/NEGATIVE/UNAVAILABLE)= RED;同一本冊內一詞兩方向 = RED;
     同方向不同細鍵(STRONG_BUY vs BUY)= YELLOW GRANULARITY;某本冊缺 = YELLOW MISSING;評等詞又是目標價同義字 = YELLOW CROSS_SCOPE。
   方向表與細鍵表**從聯集冊讀**(`direction` / `fine_of`,CGC_MDL176 那一本),本檔不另寫第二份。只攤開不裁定,不改任何冊。
   寫 VIA_Reports/vrn/ssot_consistency_latest.json。
③ `regexcheck`:把鎖定正則(中央冊 12 條;錨點改詞界做文中搜尋)、S05 評等/目標價正則、規則冊線索正則、
   各來源評等詞與目標價同義字、樞紐正本實作 rating_of / tp_of,跑在一夾文字檔上(預設 = VIA_InputConsole_Spec 的
   user.vrn_dir;`--in` 可給檔或夾;.txt/.md 全文,.pdf 取第 1 頁(個股報告只取第一頁,VIA_Policy_VRNTextScope)),
   逐檔逐式出一列(欄位鎖在 REGEXCHECK_COLUMNS,寫出前先驗型別),寫 VIA_Reports/vrn/regex_selfcheck_latest.{json,csv}。

其餘整支照 v0115(__getattr__ 轉接;L04 舊版留作版史)。VRN 不對外:只帶加速器橋,不帶網路橋。TA-Lib 不用。
用法(經 VCGC):run --family vrn SUP_MDL749_VRNFieldRuleHub consistency [--json]
               run --family vrn SUP_MDL749_VRNFieldRuleHub regexcheck [--in <檔或夾> …] [--limit N] [--json]
               run --family vrn SUP_MDL749_VRNFieldRuleHub --selftest
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
import csv
import importlib.util
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
SSOT_DIR = VIA / "supportive modules" / "ssot"
VRN_DIR = VIA / "functional modules" / "VRN"
OUT_DIR = VIA / "VIA_Reports" / "vrn"
_STEM = "SUP_MDL749_VRNFieldRuleHub"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "SUP_MDL749_VRNFieldRuleHub_v0115.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("sup749_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


#: 讀不動 / 非字面而跳過的項(誠實記帳,consistency 報告一併寫出;不靜默吞)
SKIPPED: list = []

# ══════════════ ① 薄尾鏈量尺 ══════════════
_THIN_GETATTR = re.compile(r"^def __getattr__\(", re.M)
_THIN_PRIOR = re.compile(r"^_PRIOR_PATH\s*=", re.M)


def _family(p: Path) -> str:
    return re.sub(r"_v\d+$", "", Path(p).stem)


def is_thin_tail(text: str) -> bool:
    """薄尾 = 模組層 `__getattr__` 轉接 + `_PRIOR_PATH` 載前版(L04 標準式)。"""
    return bool(_THIN_GETATTR.search(text) and _THIN_PRIOR.search(text))


def chain_files(p: Path, limit: int = 64) -> list:
    """尾 → 前版 … → 第一個非薄尾檔(本體)。前版 = 同夾同家族、版號較小者取最大(與薄尾自己的 _PRIOR_PATH 同一律)。"""
    p = Path(p)
    out, cur = [p], p
    while len(out) < limit:
        try:
            t = cur.read_text(encoding="utf-8", errors="replace")
        except OSError:
            break
        if not is_thin_tail(t):
            break
        fam, v = _family(cur), _vnum(cur)
        lower = [q for q in cur.parent.glob(fam + "_v*.py") if _family(q) == fam and 0 <= _vnum(q) < v]
        if not lower:
            break
        cur = max(lower, key=_vnum)
        out.append(cur)
    return out


def chain_text(p: Path) -> str:
    parts = []
    for f in chain_files(p):
        try:
            parts.append(Path(f).read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            SKIPPED.append(f"chain_text {Path(f).name}: {type(exc).__name__}")
    return "\n".join(parts)


class _ChainPath(type(Path())):
    """讀文字時沿薄尾鏈接回本體;其餘行為與 Path 相同(給 v0115 的 drift / downstream / matchers 用)。"""

    def read_text(self, *a, **k):  # noqa: D401
        return chain_text(Path(str(self)))


_prior_newest = PRIOR._newest
_prior_live_tails = PRIOR._live_tails


def _newest_chain(rel_dir: str, glob: str):
    p = _prior_newest(rel_dir, glob)
    return _ChainPath(str(p)) if p is not None else None


def _live_tails_chain(folder: Path, pat: str = "*.py") -> list:
    return [_ChainPath(str(f)) for f in _prior_live_tails(folder, pat) if _family(f) != _STEM]


PRIOR._newest = _newest_chain
PRIOR._live_tails = _live_tails_chain


# ══════════════ ② consistency ══════════════
def _nk(s) -> str:
    """比對鍵:NFKC + casefold + 去空白/連字號/底線(聯集冊 normalization 再收一層拼法差)。"""
    return re.sub(r"[\s\-_]+", "", unicodedata.normalize("NFKC", str(s)).casefold())


_BUCKET_ALIAS = {"RATING_BUY": "BUY", "RATING_SELL": "SELL", "RATING_HOLD": "HOLD",
                 "strong_buy": "STRONG_BUY", "buy": "BUY", "hold": "HOLD", "sell": "SELL",
                 "strong_sell": "STRONG_SELL", "not_rated": "NOT_RATED"}


def _bucket(b) -> str:
    if b is None:
        return "NOT_RATED"
    b = str(b).strip()
    return _BUCKET_ALIAS.get(b) or _BUCKET_ALIAS.get(b.lower()) or b.upper()


def _newest_book(folder: Path, pattern: str):
    hits = [p for p in folder.glob(pattern) if "_sha" not in p.name and _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _read_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def _rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(VIA.parent)).replace("\\", "/")
    except (ValueError, OSError):
        return str(p)


def _src(name: str, kind: str, path=None, state: str = "OK", why: str = "") -> dict:
    return {"name": name, "kind": kind, "path": _rel(path) if path else None, "state": state, "why": why,
            "rating": {}, "tp": {}, "rating_role": "bucketed", "tp_role": "synonyms", "evidence": {}}


def _add(rec: dict, lane: str, word, bucket=None, ev: str = "") -> None:
    w = str(word).strip()
    if not w:
        return
    k = _nk(w)
    slot = rec[lane].setdefault(k, {"raw": [], "buckets": []})
    if w not in slot["raw"]:
        slot["raw"].append(w)
    if bucket is not None and bucket not in slot["buckets"]:
        slot["buckets"].append(bucket)
    if ev and k not in rec["evidence"]:
        rec["evidence"][k] = ev


# ── 正則字面 → 詞(只取純字面的分支;帶元字元的分支不猜)
def _top_split(p: str, sep: str = "|") -> list:
    out, cur, depth, i, in_cls = [], [], 0, 0, False
    while i < len(p):
        c = p[i]
        if c == "\\" and i + 1 < len(p):
            cur.append(p[i:i + 2])
            i += 2
            continue
        if in_cls:
            in_cls = c != "]"
        elif c == "[":
            in_cls = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == sep and depth == 0:
            out.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    out.append("".join(cur))
    return out


def _groups(part: str) -> list:
    """part 裡最外層的 (...) 內容(跳過字元類與跳脫)。"""
    out, depth, start, i, in_cls = [], 0, -1, 0, False
    while i < len(part):
        c = part[i]
        if c == "\\":
            i += 2
            continue
        if in_cls:
            in_cls = c != "]"
        elif c == "[":
            in_cls = True
        elif c == "(":
            if depth == 0:
                start = i + 1
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0 and start >= 0:
                out.append(part[start:i])
        i += 1
    return out


def _lit(s: str):
    s = s.strip()
    for a, b in ((r"\s*", " "), (r"\s+", " "), (r"\s", " "), ("[- ]?", " "), ("[ -]?", " "), ("-?", "-"),
                 (r"\.", "."), (r"\-", "-"), (r"\/", "/"), ("[_\\s]*", " ")):
        s = s.replace(a, b)
    while s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    if not s or re.search(r"[\\\[\]{}()*+?^$|]", s):
        return None
    return re.sub(r"\s+", " ", s).strip() or None


def regex_words(p: str) -> list:
    """一條評等/目標價正則裡的字面分支。"""
    p = re.sub(r"\(\?[aiLmsux]+\)", "", p or "")
    p = re.sub(r"\(\?[aiLmsux-]+:", "(", p)
    p = re.sub(r"\(\?<?[!=](?:[^()\\]|\\.|\([^()]*\))*\)", "", p)
    p = p.replace("(?:", "(").replace(r"\b", "")
    out = []
    for part in _top_split(p):
        gs = [g for g in _groups(part) if "|" in g]
        if gs:
            for g in gs:
                out += regex_words(g)
            continue
        w = _lit(part)
        if w:
            out.append(w)
    seen, uniq = set(), []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq


# ── AST 取常數(零執行;沿薄尾鏈,尾版先找)
def _str_of(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _str_of(node.left), _str_of(node.right)
        return a + b if a is not None and b is not None else None
    if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "compile" and node.args:
        return _str_of(node.args[0])
    return None


def ast_constants(tail: Path, names: tuple, func_locals: dict | None = None) -> dict:
    """{名: (AST 節點, 檔, 行)};func_locals = {函式名: 區域變數名} 取函式內字面(ENG073 _tp_terms 的 base)。"""
    found: dict = {}
    for f in chain_files(tail):
        try:
            tree = ast.parse(Path(f).read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError, ValueError) as exc:
            SKIPPED.append(f"ast_constants {Path(f).name}: {type(exc).__name__}")
            continue
        for n in tree.body:
            tgts = n.targets if isinstance(n, ast.Assign) else ([n.target] if isinstance(n, ast.AnnAssign) else [])
            for t in tgts:
                if isinstance(t, ast.Name) and t.id in names and t.id not in found and n.value is not None:
                    found[t.id] = (n.value, Path(f).name, n.lineno)
            if isinstance(n, ast.FunctionDef) and func_locals and n.name in func_locals:
                key = f"{n.name}.{func_locals[n.name]}"
                for m in ast.walk(n):
                    if (isinstance(m, ast.Assign) and key not in found
                            and any(isinstance(t, ast.Name) and t.id == func_locals[n.name] for t in m.targets)):
                        found[key] = (m.value, Path(f).name, m.lineno)
    return found


def _book_central(path) -> dict:
    s = _src("central", "book", path)
    d = _read_json(path)
    for g, ws in (d.get("synonyms") or {}).items():
        if g.startswith("RATING_"):
            for w in ws:
                _add(s, "rating", w, _bucket(g), f"{path.name}#synonyms.{g}")
        elif g == "TARGET_PRICE":
            for w in ws:
                _add(s, "tp", w, "TARGET_PRICE", f"{path.name}#synonyms.TARGET_PRICE")
    s["regex"] = d.get("regex") or {}
    return s


def _book_field_rules(path) -> dict:
    s = _src("field_rules", "book", path)
    r = (_read_json(path).get("rules") or {})
    ra, tp = r.get("rating") or {}, r.get("target_price") or {}
    for k, ws in (ra.get("canon_map") or {}).items():
        for w in ws:
            _add(s, "rating", w, _bucket(k), f"{path.name}#rules.rating.canon_map.{k}")
    for w, k in (ra.get("local_scale") or {}).items():
        _add(s, "rating", w, _bucket(k), f"{path.name}#rules.rating.local_scale")
    for w in regex_words(tp.get("cue_any_rx") or ""):
        _add(s, "tp", w, "TARGET_PRICE", f"{path.name}#rules.target_price.cue_any_rx")
    if tp.get("alias_source"):
        s["tp_role"] = "DELEGATED"
        s["tp_why"] = f"冊自述同義字正本在 {tp['alias_source']};本冊只留強線索(不抄第二份),缺詞不計 MISSING"
    s["cue_rx"] = {"rating.cue_rx": ra.get("cue_rx"), "target_price.cue_any_rx": tp.get("cue_any_rx")}
    s["cue_rx"].update({f"target_price.cue_rx[{i}]": x for i, x in enumerate(tp.get("cue_rx") or [])})
    return s


def _book_s05(path) -> dict:
    s = _src("s05", "book", path)
    d = _read_json(path)
    for k, v in ((d.get("rating_list") or {}).get("canonical_v22_2") or {}).items():
        for lang in ("chinese", "english"):
            for w in v.get(lang) or []:
                _add(s, "rating", w, _bucket(k), f"{path.name}#rating_list.canonical_v22_2.{k}.{lang}")
    for w in (d.get("target_price_dict") or {}).get("synonyms") or []:
        _add(s, "tp", w, "TARGET_PRICE", f"{path.name}#target_price_dict.synonyms")
    s["regex"] = {k: v.get("pattern") for k, v in (d.get("all_regex") or {}).items()
                  if isinstance(v, dict) and ("RATING" in k or "TARGET" in k)}
    s["regex_examples"] = {k: {"pattern": v.get("pattern"), "pass": v.get("examples_pass") or [],
                               "fail": v.get("examples_fail") or []}
                           for k, v in (d.get("all_regex") or {}).items() if isinstance(v, dict) and v.get("pattern")}
    return s


def _book_union(path) -> dict:
    s = _src("union", "book", path)
    d = _read_json(path)
    verdict = {(r.get("scope"), _nk(r.get("key"))): r.get("verdict") for r in d.get("rulings") or [] if r.get("verdict")}
    for scope, lane in (("rating", "rating"), ("target_price", "tp")):
        for k, es in ((d.get("scopes") or {}).get(scope) or {}).items():
            v = verdict.get((scope, _nk(k)))
            cans = [v] if v else sorted({e.get("canonical") for e in es if e.get("canonical")})
            raw = next((e.get("raw") for e in es if e.get("raw")), k)
            for c in cans:
                _add(s, lane, raw, _bucket(c) if lane == "rating" else c, f"{path.name}#scopes.{scope}.{k}")
    s["direction"] = d.get("direction") or {}
    s["fine_of"] = d.get("fine_of") or {}
    return s


def _book_institution(path) -> dict:
    s = _src("institution", "book", path)
    reg = _read_json(path).get("registries") or {}
    for k, v in (reg.get("broker_ratings") or {}).items():
        for w in [v.get("chinese_name"), v.get("english_name")] + list(v.get("aliases") or []):
            if w:
                _add(s, "rating", w, _bucket(k), f"{path.name}#registries.broker_ratings.{k}")
    for w in ((reg.get("research_fields") or {}).get("TARGET_PRICE") or {}).get("aliases") or []:
        _add(s, "tp", w, "TARGET_PRICE", f"{path.name}#registries.research_fields.TARGET_PRICE.aliases")
    return s


def _code_eng086(tail) -> dict:
    s = _src("code_eng086", "code", tail)
    c = ast_constants(tail, ("LOCAL_RATING_SCALE", "_RATING_FN", "_TITLE_RATING", "_TP_CUE_ANY"))
    if "LOCAL_RATING_SCALE" in c:
        node, f, ln = c["LOCAL_RATING_SCALE"]
        try:
            for w, k in ast.literal_eval(node):
                _add(s, "rating", w, _bucket(k), f"{f}:{ln} LOCAL_RATING_SCALE")
        except (ValueError, TypeError, SyntaxError) as exc:
            SKIPPED.append(f"{f}:{ln} LOCAL_RATING_SCALE 非字面: {type(exc).__name__}")
    if "_RATING_FN" in c and isinstance(c["_RATING_FN"][0], ast.Tuple):
        node, f, ln = c["_RATING_FN"]
        for e in node.elts:
            if isinstance(e, ast.Tuple) and len(e.elts) == 2 and isinstance(e.elts[1], ast.Constant):
                for w in regex_words(_str_of(e.elts[0]) or ""):
                    if " " not in w:
                        _add(s, "rating", w, _bucket(e.elts[1].value), f"{f}:{ln} _RATING_FN")
    if "_TITLE_RATING" in c:
        node, f, ln = c["_TITLE_RATING"]
        for w in regex_words(_str_of(node) or ""):
            _add(s, "rating", w, None, f"{f}:{ln} _TITLE_RATING")
    if "_TP_CUE_ANY" in c:
        node, f, ln = c["_TP_CUE_ANY"]
        for w in regex_words(_str_of(node) or ""):
            _add(s, "tp", w, "TARGET_PRICE", f"{f}:{ln} _TP_CUE_ANY")
    s["found"] = sorted(c)
    return s


def _code_eng073(tail) -> dict:
    s = _src("code_eng073", "code", tail)
    s["rating_role"] = "presence"
    c = ast_constants(tail, ("RATING_RX", "RATING_LIST"), {"_tp_terms": "base"})
    if "RATING_RX" in c:
        node, f, ln = c["RATING_RX"]
        for w in regex_words(_str_of(node) or ""):
            _add(s, "rating", w, None, f"{f}:{ln} RATING_RX")
    if "RATING_LIST" in c:
        node, f, ln = c["RATING_LIST"]
        try:
            for w in ast.literal_eval(node):
                _add(s, "rating", w, None, f"{f}:{ln} RATING_LIST")
        except (ValueError, TypeError, SyntaxError) as exc:
            SKIPPED.append(f"{f}:{ln} RATING_LIST 非字面: {type(exc).__name__}")
    if "_tp_terms.base" in c:
        node, f, ln = c["_tp_terms.base"]
        try:
            for w in ast.literal_eval(node):
                _add(s, "tp", w, "TARGET_PRICE", f"{f}:{ln} _tp_terms.base(冊缺退路)")
        except (ValueError, TypeError, SyntaxError) as exc:
            SKIPPED.append(f"{f}:{ln} _tp_terms.base 非字面: {type(exc).__name__}")
        s["tp_role"] = "FALLBACK"
        s["tp_why"] = "執行期讀機構 SSOT TARGET_PRICE.aliases;這 4 詞只是冊缺時的退路(不計 MISSING)"
    s["found"] = sorted(c)
    return s


#: 來源表(名, 種類, 夾, 尾版 glob, 載入器)。書目與 GitHub 已鎖架構同一組,不另加。
SOURCES = (
    ("central", "book", REG, "VIA_Central_Synonym_Regex_v*.json", _book_central),
    ("field_rules", "book", REG, "VRN_FieldRules_SSOT_v*.json", _book_field_rules),
    ("s05", "book", REG, "VRN_S05_FieldRegistry_v*.json", _book_s05),
    ("union", "book", REG, "VIA_SSOT_SynonymUnion_v*.json", _book_union),
    ("institution", "book", SSOT_DIR, "VIA_Financial_Institution_SSOT_v*.json", _book_institution),
    ("code_eng086", "code", VRN_DIR, "VRN_ENG086_FirstPageLogicBridge_v*.py", _code_eng086),
    ("code_eng073", "code", VRN_DIR, "VRN_ENG073_ReportStructuredDB_v*.py", _code_eng073),
)
#: 掃過、但冊上沒有評等詞/目標價同義字的那幾本(照實記,不冒充比過)。
REFERENCE_BOOKS = (
    ("VIA_VRN_FieldSpec_SSOT_v*.json", "欄位規格:評等/目標價只寫 rules_ref 指回規則正本冊,無詞表"),
    ("VIA_VRN_ReportFieldRules_SSOT_v*.json", "檔名評等槽位式 rx(位置式,非詞表)+ 分析師/電話/網域"),
    ("VIA_VRN_TabFields_v*.json", "分頁欄名(輸出表頭;見 docs/r34/VRN_OUTPUT_HEADERS_r34.json)"),
    ("VIA_SSOT_RegexDict_v*.json", "程式正則收割(AST);無詞→桶對映"),
    ("VIA_VCGC_RegexParamRecord_v*.json", "中央正則參數紀錄:aligned 清單對回中央冊(本支驗)"),
)


def load_sources() -> dict:
    out = {}
    for name, kind, folder, pat, fn in SOURCES:
        p = _newest_book(folder, pat)
        if p is None:
            out[name] = _src(name, kind, None, "ABSENT", f"找不到 {pat}")
            continue
        try:
            out[name] = fn(p)
        except Exception as exc:  # 冊壞=誠實 RED,不編
            out[name] = _src(name, kind, p, "RED", f"讀不動:{type(exc).__name__}: {str(exc)[:80]}")
    return out


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def regex_examples(book: str, examples: dict) -> list:
    """冊上每條正則拿**冊自己的例子**驗:examples_pass 不中 = RED;examples_fail 中了 = RED;
    目標價式的擷取值與例子裡最後一個數字(去千分位)不同 = RED VALUE_TRUNCATED(例:`NT$1,100` 只抓到 `1`)。"""
    out = []
    for rid, e in examples.items():
        try:
            rx = re.compile(e["pattern"])
        except re.error as exc:
            out.append({"book": book, "id": rid, "example": "", "state": "RED", "kind": "COMPILE", "got": str(exc)})
            continue
        for ex in e.get("pass") or []:
            m = rx.search(str(ex))
            got = (next((g for g in m.groups() if g), None) if m and m.groups() else (m.group(0) if m else None))
            kind, state = "", "OK"
            if m is None:
                kind, state = "PASS_EXAMPLE_MISSED", "RED"
            elif "TARGET" in rid and m.groups():
                want = (_NUM.findall(str(ex)) or [""])[-1].replace(",", "")
                if str(got or "").replace(",", "") != want:
                    kind, state = "VALUE_TRUNCATED", "RED"
            out.append({"book": book, "id": rid, "example": str(ex), "state": state, "kind": kind, "got": got})
        for ex in e.get("fail") or []:
            m = rx.search(str(ex))
            out.append({"book": book, "id": rid, "example": str(ex), "state": "RED" if m else "OK",
                        "kind": "FAIL_EXAMPLE_MATCHED" if m else "", "got": m.group(0) if m else None})
    return out


def _regex_section(sources: dict) -> dict:
    rows = []
    cen = sources.get("central") or {}
    for k, v in (cen.get("regex") or {}).items():
        pat = (v or {}).get("pattern", "")
        try:
            re.compile(pat)
            st = "OK"
        except re.error as exc:
            st = f"RED:{exc}"
        rows.append({"id": k, "source": "central", "locked": bool((v or {}).get("locked")), "compile": st})
    for sname, key in (("s05", "regex"), ("field_rules", "cue_rx")):
        for k, pat in ((sources.get(sname) or {}).get(key) or {}).items():
            if not pat:
                continue
            try:
                re.compile(pat)
                st = "OK"
            except re.error as exc:
                st = f"RED:{exc}"
            rows.append({"id": k, "source": sname, "locked": None, "compile": st})
    rec = _newest_book(REG, "VIA_VCGC_RegexParamRecord_v*.json")
    align = {"state": "ABSENT", "path": _rel(rec) if rec else None}
    if rec is not None:
        try:
            d = _read_json(rec)
            want, have = set(d.get("aligned") or []), set(cen.get("regex") or {})
            align = {"state": "OK" if want == have else "YELLOW", "path": _rel(rec),
                     "record_only": sorted(want - have), "book_only": sorted(have - want),
                     "regex_book": d.get("regex_book"), "synonym_book": d.get("synonym_book")}
        except (OSError, ValueError) as exc:
            align = {"state": "RED", "path": _rel(rec), "why": type(exc).__name__}
    ex = []
    for sname, s in sources.items():
        if s.get("state") == "OK" and s.get("regex_examples"):
            ex += regex_examples(sname, s["regex_examples"])
    return {"rows": rows, "param_record": align, "examples": ex,
            "examples_tally": {"OK": sum(1 for x in ex if x["state"] == "OK"),
                               "RED": sum(1 for x in ex if x["state"] == "RED")},
            "red": [r for r in rows if r["compile"] != "OK"] + [x for x in ex if x["state"] == "RED"]}


def compare(sources: dict) -> dict:
    """逐詞攤開(純函式;selftest 用合成來源驗)。"""
    uni = sources.get("union") or {}
    direction, fine_of = uni.get("direction") or {}, uni.get("fine_of") or {}
    ok = {n: s for n, s in sources.items() if s.get("state") == "OK"}
    rbooks = [n for n, s in ok.items() if s["kind"] == "book" and s.get("rating")]
    tbooks = [n for n, s in ok.items() if s["kind"] == "book" and s.get("tp") and s.get("tp_role") == "synonyms"]
    tp_keys = {k for s in ok.values() for k in s.get("tp", {})}

    def _dir(b):
        return direction.get(b, "UNKNOWN") if direction else "UNJUDGED"

    rating_rows = []
    for k in sorted({k for s in ok.values() for k in s.get("rating", {})}):
        per = {n: s["rating"][k] for n, s in ok.items() if k in s.get("rating", {})}
        pairs = [(n, b) for n, rec in per.items() for b in rec["buckets"]]
        dirs = sorted({_dir(b) for _, b in pairs})
        fines = sorted({fine_of.get(b, b) for _, b in pairs})
        intra = sorted(n for n, rec in per.items() if len({_dir(b) for b in rec["buckets"]}) > 1)
        missing = [n for n in rbooks if n not in per]
        kinds = []
        if len([d for d in dirs if d not in ("UNJUDGED",)]) > 1:
            kinds.append("DIRECTION_CONFLICT")
        if intra:
            kinds.append("INTRA_BOOK_CONFLICT")
        if len(fines) > 1 and "DIRECTION_CONFLICT" not in kinds:
            kinds.append("GRANULARITY")
        if "UNKNOWN" in dirs:
            kinds.append("UNKNOWN_BUCKET")
        if missing:
            kinds.append("MISSING")
        if k in tp_keys:
            kinds.append("CROSS_SCOPE")
        state = ("RED" if {"DIRECTION_CONFLICT", "INTRA_BOOK_CONFLICT"} & set(kinds)
                 else "YELLOW" if kinds else "GREEN")
        word = next(iter(per.values()))["raw"][0]
        rating_rows.append({"key": k, "word": word, "state": state, "kinds": kinds,
                            "buckets": {n: rec["buckets"] for n, rec in per.items() if rec["buckets"]},
                            "present": {n: (n in per) for n in ok},
                            "directions": dirs, "fine": fines, "intra_book": intra, "missing_in": missing,
                            "evidence": {n: ok[n]["evidence"].get(k) for n in per}})
    tp_rows = []
    for k in sorted(tp_keys):
        per = {n: s["tp"][k] for n, s in ok.items() if k in s.get("tp", {})}
        cans = sorted({b for rec in per.values() for b in rec["buckets"]})
        missing = [n for n in tbooks if n not in per]
        kinds = (["CANON_CONFLICT"] if len(cans) > 1 else []) + (["MISSING"] if missing else [])
        rk = k in {kk for s in ok.values() for kk in s.get("rating", {})}
        if rk:
            kinds.append("CROSS_SCOPE")
        state = "RED" if "CANON_CONFLICT" in kinds else ("YELLOW" if kinds else "GREEN")
        tp_rows.append({"key": k, "word": next(iter(per.values()))["raw"][0], "state": state, "kinds": kinds,
                        "canon": cans, "present": {n: (n in per) for n in ok}, "missing_in": missing,
                        "evidence": {n: ok[n]["evidence"].get(k) for n in per}})
    cov = {n: {"kind": s["kind"], "state": s["state"], "path": s.get("path"), "why": s.get("why"),
               "rating_n": len(s.get("rating", {})), "tp_n": len(s.get("tp", {})),
               "rating_role": s.get("rating_role"), "tp_role": s.get("tp_role"), "tp_why": s.get("tp_why"),
               "rating_buckets": sorted({b for r in s.get("rating", {}).values() for b in r["buckets"]})}
           for n, s in sources.items()}
    tally = {}
    for r in rating_rows + tp_rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    return {"rating": rating_rows, "tp": tp_rows, "coverage": cov, "tally": tally,
            "rating_books": rbooks, "tp_books": tbooks,
            "direction_table": direction, "fine_table": fine_of,
            "direction_src": uni.get("path") if direction else None}


def consistency(sources: dict | None = None) -> dict:
    srcs = sources if sources is not None else load_sources()
    cmp_ = compare(srcs)
    rx = _regex_section(srcs)
    red = [r for r in cmp_["rating"] + cmp_["tp"] if r["state"] == "RED"] + rx["red"]
    yel = [r for r in cmp_["rating"] + cmp_["tp"] if r["state"] == "YELLOW"]
    bad_src = [n for n, s in srcs.items() if s.get("state") != "OK"]
    verdict = "RED" if red else ("YELLOW" if (yel or bad_src or rx["param_record"].get("state") != "OK") else "GREEN")
    kinds = {}
    for r in cmp_["rating"] + cmp_["tp"]:
        for k in r["kinds"]:
            kinds[k] = kinds.get(k, 0) + 1
    return {"schema": "VIA.VRN.SSOTConsistency.v1", "engine": Path(__file__).name,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "verdict": verdict,
            "rule": ("同一詞不同方向=RED;同一本冊一詞兩方向=RED;同方向不同細鍵=YELLOW GRANULARITY;"
                     "某本冊缺=YELLOW MISSING(code 來源只記在不在,不計缺);評等詞兼目標價詞=YELLOW CROSS_SCOPE;"
                     "方向/細鍵表取自聯集冊 direction/fine_of。正則:全部可編譯、冊上 examples_pass/fail 拿冊自己的例子驗"
                     "(目標價式擷取值被截=RED VALUE_TRUNCATED)、參數紀錄 aligned 對回中央冊。只攤開不裁定、不改冊。"),
            "kinds": kinds, "sources_not_ok": bad_src,
            "conflicts": [{"key": r["key"], "word": r["word"], "kinds": r["kinds"],
                           "buckets": r.get("buckets") or r.get("canon"), "evidence": r["evidence"]} for r in red
                          if "key" in r],
            "granularity": [{"word": r["word"], "buckets": r["buckets"]} for r in cmp_["rating"]
                            if "GRANULARITY" in r["kinds"]],
            "cross_scope": [r["word"] for r in cmp_["rating"] if "CROSS_SCOPE" in r["kinds"]],
            "regex_red": rx["red"], "skipped": sorted(set(SKIPPED)),
            "reference_books": [{"glob": g, "path": _rel(_newest_book(REG, g)) if _newest_book(REG, g) else None,
                                 "role": why} for g, why in REFERENCE_BOOKS],
            "regex": rx, **cmp_}


def write_json(obj: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, path)
    return path


# ══════════════ ③ regexcheck ══════════════
REGEXCHECK_COLUMNS = (("file", "str"), ("file_kind", "str"), ("text_scope", "str"), ("chars", "int"),
                      ("family", "str"), ("pattern_id", "str"), ("source", "str"), ("hits", "int"),
                      ("first_hit", "str"), ("value", "str"), ("bucket", "str"), ("state", "str"),
                      ("evidence", "str"))
TEXT_EXT = {".txt", ".md"}
PDF_EXT = {".pdf"}


def anchored_to_search(p: str) -> str:
    """鎖定正則是整串驗證式(^…$);文中搜尋時把錨點換成英數詞界,式子本體不動。"""
    out, i, in_cls = [], 0, False
    while i < len(p):
        c = p[i]
        if c == "\\" and i + 1 < len(p):
            out.append(p[i:i + 2])
            i += 2
            continue
        if in_cls:
            in_cls = c != "]"
            out.append(c)
        elif c == "[":
            in_cls = True
            out.append(c)
            if i + 1 < len(p) and p[i + 1] == "^":
                out.append("^")
                i += 1
        elif c == "^":
            out.append(r"(?<![0-9A-Za-z.])")
        elif c == "$":
            out.append(r"(?![0-9A-Za-z])")
        else:
            out.append(c)
        i += 1
    return "".join(out)


def _word_rx(w: str):
    if re.fullmatch(r"[A-Za-z0-9 .,/&'()\-]+", w):
        body = r"\s*".join(re.escape(x) for x in w.split())
        return re.compile(r"(?<![A-Za-z])" + body + r"(?![A-Za-z])", re.I)
    return re.compile(re.escape(unicodedata.normalize("NFKC", w)))


def spec_vrn_dirs() -> list:
    """VIA_InputConsole_Spec 尾版的 user.vrn_dir(操作員樣本夾)。冊缺回空(誠實)。"""
    b = _newest_book(REG, "VIA_InputConsole_Spec_v*.json")
    if b is None:
        return []
    try:
        d = (_read_json(b).get("user") or {}).get("vrn_dir")
    except (OSError, ValueError):
        return []
    return [Path(d)] if d else []


def read_text_input(p: Path) -> tuple:
    """(文字, 範圍, 狀態)。PDF 只取第 1 頁;缺 PDF 函式庫=誠實 SKIPPED。"""
    ext = p.suffix.lower()
    if ext in TEXT_EXT:
        return p.read_text(encoding="utf-8", errors="replace"), "txt_full", "OK"
    if ext in PDF_EXT:
        try:
            import fitz  # PyMuPDF(ENG392 同一個)
        except Exception:
            return "", "pdf_page1", "SKIPPED_NO_PDF_LIB"
        try:
            with fitz.open(str(p)) as doc:
                return (doc[0].get_text() if len(doc) else ""), "pdf_page1", "OK"
        except Exception as exc:
            return "", "pdf_page1", f"ERROR:{type(exc).__name__}"
    return "", "", "SKIPPED_EXT"


def collect_inputs(given: list | None) -> tuple:
    notes, files = [], []
    targets = [Path(g) for g in given] if given else spec_vrn_dirs()
    if not targets:
        notes.append("沒有輸入:--in 沒給,VIA_InputConsole_Spec user.vrn_dir 也沒有")
    for t in targets:
        if not t.exists():
            notes.append(f"不在本機:{t}(操作員樣本夾在工作站;容器照實 ABSENT)")
            continue
        cand = [t] if t.is_file() else sorted(q for q in t.rglob("*") if q.is_file())
        files += [q for q in cand if q.suffix.lower() in TEXT_EXT | PDF_EXT]
    return files, notes, [str(t) for t in targets]


def _row(**k) -> dict:
    r = {c: ("" if t == "str" else 0) for c, t in REGEXCHECK_COLUMNS}
    r.update({c: v for c, v in k.items() if c in r})
    return r


def validate_rows(rows: list) -> list:
    """鎖定表頭:欄名與順序一字不差、型別對。回錯誤清單(空=過)。"""
    errs, want = [], [c for c, _ in REGEXCHECK_COLUMNS]
    types = {"str": str, "int": int}
    for i, r in enumerate(rows):
        if list(r) != want:
            errs.append(f"row {i}: columns {list(r)} != {want}")
            continue
        for c, t in REGEXCHECK_COLUMNS:
            if not isinstance(r[c], types[t]) or (t == "int" and isinstance(r[c], bool)):
                errs.append(f"row {i}: {c} expects {t}, got {type(r[c]).__name__}")
    return errs


def check_text(text: str, name: str, kind: str, scope: str, srcs: dict, cons: dict | None = None) -> list:
    rows, n = [], len(text)
    base = {"file": name, "file_kind": kind, "text_scope": scope, "chars": n}
    # REGEX:中央鎖定式(錨點→詞界)
    for rid, v in ((srcs.get("central") or {}).get("regex") or {}).items():
        pat = (v or {}).get("pattern", "")
        try:
            hits = [m.group(0) for m in re.finditer(anchored_to_search(pat), text)]
            st = "HIT" if hits else "MISS"
        except re.error as exc:
            hits, st = [], f"ERROR:{exc}"
        rows.append(_row(**base, family="REGEX", pattern_id=rid, source="central", hits=len(hits),
                         first_hit=(hits[0] if hits else "")[:80], state=st,
                         evidence=f"{(srcs.get('central') or {}).get('path')}#regex.{rid}(anchors→word bounds)"))
    for sname, key in (("s05", "regex"), ("field_rules", "cue_rx")):
        for rid, pat in ((srcs.get(sname) or {}).get(key) or {}).items():
            if not pat:
                continue
            try:
                ms = list(re.finditer(pat, text))
                st = "HIT" if ms else "MISS"
            except re.error as exc:
                ms, st = [], f"ERROR:{exc}"
            val = ""
            if ms and ms[0].groups():
                val = next((g for g in ms[0].groups() if g), "") or ""
            fam = "TP" if ("TARGET" in rid or "target" in rid) else "RATING"
            rows.append(_row(**base, family=fam, pattern_id=rid, source=sname, hits=len(ms),
                             first_hit=(ms[0].group(0) if ms else "")[:80], value=str(val)[:40], state=st,
                             evidence=f"{(srcs.get(sname) or {}).get('path')}#{key}.{rid}"))
    # 詞表:各來源評等詞 / 目標價同義字
    red_keys = {r["key"] for r in (cons or {}).get("rating", []) if r["state"] == "RED"}
    seen_red = set()
    norm_text = unicodedata.normalize("NFKC", text)
    for sname, s in srcs.items():
        if s.get("state") != "OK":
            continue
        for lane, fam in (("rating", "RATING"), ("tp", "TP")):
            found, buckets = [], set()
            for k, rec in s.get(lane, {}).items():
                if any(_word_rx(w).search(norm_text) for w in rec["raw"]):
                    found.append(rec["raw"][0])
                    buckets.update(rec["buckets"])
                    if lane == "rating" and k in red_keys:
                        seen_red.add(rec["raw"][0])
            if not s.get(lane):
                continue
            rows.append(_row(**base, family=fam, pattern_id=f"{lane}_vocab", source=sname, hits=len(found),
                             first_hit="|".join(sorted(found)[:6])[:120],
                             bucket="|".join(sorted(b for b in buckets if b))[:60],
                             state="HIT" if found else "MISS", evidence=str(s.get("path") or "")))
    rows.append(_row(**base, family="RATING", pattern_id="book_conflict_words", source="consistency",
                     hits=len(seen_red), first_hit="|".join(sorted(seen_red))[:120],
                     state="RED" if seen_red else "OK", evidence="VIA_Reports/vrn/ssot_consistency_latest.json"))
    # 樞紐正本實作(ENG086 本體 + 守衛)
    try:
        r = PRIOR.rating_of(text)
        val = (r or {}).get("canonical") or ""
        rows.append(_row(**base, family="RATING", pattern_id="hub.rating_of", source="SUP_MDL749",
                         hits=1 if val else 0, first_hit=str((r or {}).get("raw") or (r or {}).get("word") or "")[:80],
                         value=str(val), bucket=str(val), state="HIT" if val else "MISS",
                         evidence=f"{_PRIOR_PATH.name}:rating_of"))
    except Exception as exc:
        rows.append(_row(**base, family="RATING", pattern_id="hub.rating_of", source="SUP_MDL749",
                         state=f"ERROR:{type(exc).__name__}", evidence=f"{_PRIOR_PATH.name}:rating_of"))
    try:
        v, how = PRIOR.tp_of(text)
        rows.append(_row(**base, family="TP", pattern_id="hub.tp_of", source="SUP_MDL749",
                         hits=1 if v is not None else 0, first_hit=str(how)[:80],
                         value="" if v is None else str(v), state="HIT" if v is not None else "MISS",
                         evidence=f"{_PRIOR_PATH.name}:tp_of"))
    except Exception as exc:
        rows.append(_row(**base, family="TP", pattern_id="hub.tp_of", source="SUP_MDL749",
                         state=f"ERROR:{type(exc).__name__}", evidence=f"{_PRIOR_PATH.name}:tp_of"))
    return rows


def regexcheck(inputs: list | None = None, limit: int = 0, srcs: dict | None = None) -> dict:
    srcs = srcs if srcs is not None else load_sources()
    cons = consistency(srcs)
    files, notes, targets = collect_inputs(inputs)
    if limit:
        files = files[:limit]
    rows, skipped = [], []
    for f in files:
        text, scope, st = read_text_input(f)
        if st != "OK":
            skipped.append({"file": str(f), "state": st})
            rows.append(_row(file=f.name, file_kind=f.suffix.lower().lstrip("."), text_scope=scope,
                             family="INPUT", pattern_id="read", source="regexcheck", state=st, evidence=str(f)))
            continue
        rows += check_text(text, f.name, f.suffix.lower().lstrip("."), scope, srcs, cons)
    errs = validate_rows(rows)
    per_file = {}
    for r in rows:
        pf = per_file.setdefault(r["file"], {"rating": "", "tp": "", "conflict_words": "", "regex_hits": 0})
        if r["pattern_id"] == "hub.rating_of":
            pf["rating"] = r["value"]
        elif r["pattern_id"] == "hub.tp_of":
            pf["tp"] = r["value"]
        elif r["pattern_id"] == "book_conflict_words":
            pf["conflict_words"] = r["first_hit"]
        elif r["family"] == "REGEX":
            pf["regex_hits"] += r["hits"]
    state = ("ABSENT" if not files and any("不在本機" in x for x in notes)
             else "NODATA" if not files else ("RED" if errs else "OK"))
    return {"schema": "VIA.VRN.RegexSelfCheck.v1", "engine": Path(__file__).name,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "state": state,
            "targets": targets, "notes": notes, "files": len(files), "skipped": skipped,
            "columns": [{"name": c, "dtype": t} for c, t in REGEXCHECK_COLUMNS],
            "schema_errors": errs[:20], "consistency_verdict": cons["verdict"],
            "per_file": per_file, "rows": rows}


def write_regexcheck(rep: dict, out_dir: Path = OUT_DIR) -> tuple:
    j = write_json({k: v for k, v in rep.items()}, out_dir / "regex_selfcheck_latest.json")
    c = out_dir / "regex_selfcheck_latest.csv"
    with open(c, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[x for x, _ in REGEXCHECK_COLUMNS])
        w.writeheader()
        w.writerows(rep["rows"])
    return j, c


# ══════════════ selftest(零網路;合成冊與合成文字只落暫存)══════════════
FIXTURES = {
    "zh_kgi.txt": "凱基投顧 個股報告\n台積電(2330)\n投資評等:增加持股\n目標價 1,250 元\n2330.TW 2330 TT\n",
    "en_ms.txt": "Morgan Stanley Research\nTSMC (2330.TW)\nRating: Overweight\nPrice Target: NT$1,300\nEqual-weight peers\n",
    "zh_noise.txt": "公司宣布增持庫藏股 5000 張\n毛利率目標 45%\n潛在上漲空間 23%\n",
}


def _synthetic_sources() -> dict:
    dir_tab = {"STRONG_BUY": "POSITIVE", "BUY": "POSITIVE", "ADD": "POSITIVE", "HOLD": "NEUTRAL",
               "SELL": "NEGATIVE", "NOT_RATED": "UNAVAILABLE"}
    fine = {"STRONG_BUY": "STRONG_BUY", "BUY": "BUY", "ADD": "BUY", "HOLD": "HOLD", "SELL": "SELL",
            "NOT_RATED": "NOT_RATED"}
    a, b, u = _src("a", "book", None), _src("b", "book", None), _src("union", "book", None)
    u.update(direction=dir_tab, fine_of=fine)
    for w, k in (("買進", "BUY"), ("Overweight", "BUY"), ("維持", "HOLD"), ("Strong Buy", "BUY")):
        _add(a, "rating", w, k)
    for w, k in (("買進", "BUY"), ("Overweight", "HOLD"), ("Strong-Buy", "STRONG_BUY"), ("Add", "ADD")):
        _add(b, "rating", w, k)
    _add(u, "rating", "買進", "BUY")
    _add(u, "rating", "Fair Value", "HOLD")
    _add(u, "rating", "減碼", "SELL")
    _add(u, "rating", "減碼", "HOLD")
    for w in ("目標價", "Fair Value"):
        _add(a, "tp", w, "TARGET_PRICE")
    _add(b, "tp", "目標價", "TARGET_PRICE")
    return {"a": a, "b": b, "union": u}


def selftest() -> int:
    print(f"=== SUP_MDL749 v{Path(__file__).stem.rsplit('_v', 1)[-1]} 薄尾 · 先跑前版 {_PRIOR_PATH.name} 自測(沿薄尾鏈量尺)===")
    prior_rc = PRIOR.selftest()
    fails, n = [], [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    print("=== v0116 新增檢(零網路;合成冊與合成文字只落暫存)===")
    chk("① 前版自測 rc 0(含 ⑭ 薄尾鏈:ENG073 v0139 不再被量成 DRIFT)", prior_rc == 0, f"(rc {prior_rc})")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "FAM_X_v0100.py").write_text("MARK_BODY = 1\n", encoding="utf-8")
        (t / "FAM_X_v0101.py").write_text("_PRIOR_PATH = 1\n\ndef __getattr__(name):\n    return name\n", encoding="utf-8")
        (t / "FAM_X_v0102.py").write_text("_PRIOR_PATH = 1\n\ndef __getattr__(name):\n    return name\n", encoding="utf-8")
        ch = [p.name for p in chain_files(t / "FAM_X_v0102.py")]
        chk("② 薄尾鏈:尾 → 前版 → 本體,讀文字接得回本體印記;非薄尾檔只讀自己",
            ch == ["FAM_X_v0102.py", "FAM_X_v0101.py", "FAM_X_v0100.py"]
            and "MARK_BODY" in _ChainPath(str(t / "FAM_X_v0102.py")).read_text()
            and chain_files(t / "FAM_X_v0100.py") == [t / "FAM_X_v0100.py"], f"({ch})")
    lt = [p.name for p in PRIOR._live_tails(HERE)]
    chk("③ 消費者掃描排除本家族自己的尾版(不把 ORPHAN 洗成 USED)",
        not any(x.startswith(_STEM) for x in lt), f"(70_VRN_Rules 活尾 {len(lt)} 支)")
    ws = regex_words(r"[;,，、:：\-–—(（]\s*(強力買進|買進|Equal-?weight|Market Perform)\b")
    ws2 = regex_words(r"目標價|Target\s*Price|(?<![A-Za-z])TP(?![A-Za-z])|(?i:price\s*target)")
    chk("④ 正則字面分支擷取:跳過字元類與環視、\\s*→空白、-?→-;帶元字元的分支不猜",
        ws == ["強力買進", "買進", "Equal-weight", "Market Perform"] and ws2 == ["目標價", "Target Price", "TP", "price target"],
        f"({ws} · {ws2})")
    c = compare(_synthetic_sources())
    rr = {r["word"]: r for r in c["rating"]}
    chk("⑤ 合成冊負控:Overweight 一冊 BUY 一冊 HOLD = RED DIRECTION_CONFLICT;減碼同冊兩方向 = RED INTRA_BOOK;"
        "Strong Buy vs STRONG_BUY = YELLOW GRANULARITY;維持只在一冊 = YELLOW MISSING;Fair Value 兼目標價 = CROSS_SCOPE;"
        "買進三冊同 BUY = GREEN",
        rr["Overweight"]["state"] == "RED" and "DIRECTION_CONFLICT" in rr["Overweight"]["kinds"]
        and rr["減碼"]["state"] == "RED" and "INTRA_BOOK_CONFLICT" in rr["減碼"]["kinds"]
        and rr["Strong Buy"]["state"] == "YELLOW" and "GRANULARITY" in rr["Strong Buy"]["kinds"]
        and "MISSING" in rr["維持"]["kinds"] and "CROSS_SCOPE" in rr["Fair Value"]["kinds"]
        and rr["買進"]["state"] == "GREEN" and rr.get("Add", {}).get("state") == "YELLOW",
        f"({ {w: r['state'] for w, r in rr.items()} })")
    live = load_sources()
    cons = consistency(live)
    chk("⑥ 真冊讀得動(五本冊 + 兩支程式常數,沿薄尾鏈);方向表取自聯集冊;判定三態之一;只讀不寫",
        all(live[x]["state"] == "OK" for x in ("central", "field_rules", "s05", "union", "institution",
                                                "code_eng086", "code_eng073"))
        and bool(cons["direction_table"]) and cons["verdict"] in ("GREEN", "YELLOW", "RED")
        and "LOCAL_RATING_SCALE" in live["code_eng086"]["found"] and "RATING_LIST" in live["code_eng073"]["found"],
        f"({cons['verdict']} · {cons['tally']} · 衝突 {len(cons['conflicts'])} · 粒度 {len(cons['granularity'])})")
    rx = cons["regex"]
    chk("⑦ 中央鎖定正則 12 條全可編譯;參數紀錄 aligned 對回中央冊;冊例自驗有跑(S05 all_regex 帶例子)",
        len([r for r in rx["rows"] if r["source"] == "central"]) == 12
        and not [r for r in rx["rows"] if r["compile"] != "OK"]
        and rx["param_record"]["state"] == "OK" and len(rx["examples"]) >= 40,
        f"(紀錄 {rx['param_record'].get('state')} · 冊例 {rx['examples_tally']} · 紅 "
        f"{[(x['id'], x['example'], x['got']) for x in rx['red']][:3]})")
    syn = regex_examples("t", {"TARGET_PRICE_X": {"pattern": r"TP\s*([0-9]+)", "pass": ["TP 1,100", "TP 900"], "fail": ["TP 5"]},
                               "RATING_X": {"pattern": r"Buy", "pass": ["Sell"], "fail": []}})
    chk("⑮ 冊例自驗負控:千分位被截 = RED VALUE_TRUNCATED;pass 例不中 = RED;fail 例中了 = RED;正常例 = OK",
        [x["state"] + ":" + x["kind"] for x in syn]
        == ["RED:VALUE_TRUNCATED", "OK:", "RED:FAIL_EXAMPLE_MATCHED", "RED:PASS_EXAMPLE_MISSED"],
        f"({[(x['example'], x['state'], x['kind']) for x in syn]})")
    s_rx = anchored_to_search(r"^[1-9]\d{3}\.(TW|TWO)$")
    chk("⑧ 錨點改詞界:『2330.TW』文中搜得到,『12330.TWX』不算", bool(re.search(s_rx, "看 2330.TW 報告"))
        and not re.search(s_rx, "12330.TWX"), f"({s_rx})")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        for k, v in FIXTURES.items():
            (t / k).write_text(v, encoding="utf-8")
        rep = regexcheck([str(t)], srcs=live)
        pf = rep["per_file"]
        chk("⑨ regexcheck 合成中英文研報:凱基『增加持股』→ BUY、目標價 1250;大摩 Overweight → BUY、NT$1,300;"
            "雜訊檔(增持庫藏股 / 毛利率目標 / 上漲空間)評等與目標價都不准抓到",
            rep["state"] == "OK" and rep["files"] == 3
            and pf["zh_kgi.txt"]["rating"] == "BUY" and pf["zh_kgi.txt"]["tp"].replace(",", "") in ("1250", "1250.0")
            and pf["en_ms.txt"]["rating"] == "BUY" and pf["en_ms.txt"]["tp"].replace(",", "") in ("1300", "1300.0")
            and pf["zh_noise.txt"]["rating"] == "" and pf["zh_noise.txt"]["tp"] == "", f"({pf})")
        chk("⑩ 輸出=驗證:每一列欄名/順序/型別鎖在 REGEXCHECK_COLUMNS;壞列一定被抓",
            not rep["schema_errors"] and bool(validate_rows([dict(rep["rows"][0], hits="3")])),
            f"({len(rep['rows'])} 列 · {len(REGEXCHECK_COLUMNS)} 欄)")
        j, cpath = write_regexcheck(rep, t / "out")
        ok_df, df_note = True, "pandas 缺席=只驗 JSON"
        if importlib.util.find_spec("pandas") is not None:
            import pandas as _pd
            df = _pd.read_csv(cpath, encoding="utf-8-sig", dtype=str, keep_default_na=False)
            ok_df = list(df.columns) == [x for x, _ in REGEXCHECK_COLUMNS] and len(df) == len(rep["rows"])
            df_note = f"DataFrame {df.shape}"
        back = json.loads(j.read_text(encoding="utf-8"))
        chk("⑪ JSON/CSV 寫在暫存夾、讀得回來、DataFrame 欄序一致(pandas 缺席就只驗 JSON)",
            ok_df and back["rows"] == rep["rows"], f"({cpath.name} · {df_note})")
        empty = regexcheck([str(t / "no_such_dir")], srcs=live)
        chk("⑫ 樣本夾不在本機 = 誠實 ABSENT(不編列、不冒充綠)", empty["state"] == "ABSENT" and not empty["rows"],
            f"({empty['notes']})")
    d = spec_vrn_dirs()
    chk("⑬ 預設樣本夾取自 VIA_InputConsole_Spec user.vrn_dir(本機不存在就照實 ABSENT)",
        bool(d), f"({[str(x) for x in d]})")
    chk("⑭ 新動詞只收 VCGC:VIA_FROM_VCGC 不是 YES 就拒絕(rc 2)", _gate_rc({}) == 2 and _gate_rc({"VIA_FROM_VCGC": "YES"}) == 0)
    print(f"  [計] v0116 新增 {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}(前版自測 rc {prior_rc})")
    return 1 if fails else 0


def _gate_rc(env: dict) -> int:
    return 0 if env.get("VIA_FROM_VCGC") == "YES" else 2


NEW_VERBS = ("consistency", "regexcheck")


def _cli_new(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="SUP_MDL749 v0116 新動詞")
    ap.add_argument("verb", choices=NEW_VERBS)
    ap.add_argument("--in", dest="inputs", action="append", default=[])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args(argv)
    if _gate_rc(dict(os.environ)) != 0:
        print("  [拒] 這支只收 VCGC 呼叫:via-vcgc run --family vrn SUP_MDL749_VRNFieldRuleHub " + a.verb)
        return 2
    if a.verb == "consistency":
        rep = consistency()
        p = write_json(rep, OUT_DIR / "ssot_consistency_latest.json")
        if a.as_json:
            print(json.dumps({k: rep[k] for k in ("verdict", "tally", "kinds", "conflicts", "granularity",
                                                  "cross_scope", "coverage")}, ensure_ascii=False, indent=1))
            return 0
        print(f"=== VRN SSOT 一致性 · {rep['verdict']} · 評等 {len(rep['rating'])} 詞 · 目標價 {len(rep['tp'])} 詞 · {rep['tally']} ===")
        for nme, cv in rep["coverage"].items():
            print(f"  [{cv['state']:<6}] {nme:<12} 評等 {cv['rating_n']:>4} 詞 · 目標價 {cv['tp_n']:>3} 詞 · "
                  f"桶 {','.join(cv['rating_buckets']) or '—'} · {cv.get('path') or cv.get('why')}")
        print(f"  [種類] {rep['kinds']}")
        for r in rep["conflicts"][:40]:
            print(f"  [RED] {r['word']!r} {r['kinds']} {r['buckets']}")
        for r in rep["granularity"][:20]:
            print(f"  [粒度] {r['word']!r} {r['buckets']}")
        if rep["cross_scope"]:
            print(f"  [跨域] 評等詞兼目標價詞:{rep['cross_scope']}")
        rxr = rep["regex"]
        print(f"  [正則] 編譯 {len(rxr['rows'])} 式 · 冊例自驗 {rxr['examples_tally']} · "
              f"參數紀錄 {rxr['param_record'].get('state')}")
        for x in rxr["red"][:20]:
            print(f"  [RED] {x.get('book') or x.get('source')}.{x['id']} {x.get('kind') or x.get('compile')} · "
                  f"例 {x.get('example')!r} → 擷取 {x.get('got')!r}")
        print(f"  [寫] {_rel(p)}(只攤開不裁定;冊一本都沒改)")
        return 0
    rep = regexcheck(a.inputs or None, a.limit)
    if rep["state"] in ("ABSENT", "NODATA"):
        print(f"  [{rep['state']}] {' ; '.join(rep['notes'])}")
        return 3 if rep["state"] == "ABSENT" else 2
    j, c = write_regexcheck(rep)
    if a.as_json:
        print(json.dumps({k: rep[k] for k in ("state", "files", "per_file", "schema_errors")}, ensure_ascii=False, indent=1))
    else:
        print(f"=== VRN 正則文字自檢 · {rep['state']} · 檔 {rep['files']} · 列 {len(rep['rows'])} · 一致性 {rep['consistency_verdict']} ===")
        for f, v in list(rep["per_file"].items())[:60]:
            print(f"  {f[:48]:<48} 評等 {v['rating'] or '—':<10} 目標價 {v['tp'] or '—':<10} "
                  f"鎖定式命中 {v['regex_hits']:>3}" + (f" · 冊衝突詞 {v['conflict_words']}" if v["conflict_words"] else ""))
        print(f"  [寫] {_rel(j)} · {_rel(c)}")
    return 0 if rep["state"] == "OK" else 1


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] in ("--selftest", "selftest"):
        return selftest()
    if argv and argv[0] in NEW_VERBS:
        return _cli_new(argv)
    return PRIOR.main()     # 其餘動詞照 v0115(行為不變;L04)


if __name__ == "__main__":
    sys.exit(main())

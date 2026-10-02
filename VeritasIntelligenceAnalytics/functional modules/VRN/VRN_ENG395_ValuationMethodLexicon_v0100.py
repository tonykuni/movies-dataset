#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG395_ValuationMethodLexicon v0100 — 財務評價方法(valuation_method)SSOT 的比對器與檢核器

操作員 R36b(2026-10-01):「valuation_method ssot化 編號註冊 … 區分地區慣用語(台灣繁體 vs. 大陸簡體)以及涵蓋完整的使用情境(縮寫、全稱、
衍生詞)… 建立 NLP 字典、資料庫標籤或內部研究報告的標準化」。正本 = VIA_VRN_ValuationMethod_SSOT_v*.json(本支照冊讀,不另寫第二份)。

① match(text):NFKC 正規化(Ｐ／Ｅ → P/E · P / E → P/E)→ 最長詞優先;英文前後不得緊貼英數(EV/EBIT 不吃 EV/EBITDA · PE 不吃 PEG / operating);
   ≤4 字母縮寫只認大寫(per share / pe 不中);回 [代碼 · 命中詞 · 地區 · 變體(forward / trailing / fcff …)· 需語境 · 位置]。
② check():代碼唯一 · seq 唯一連號 · 同一詞不得對到兩個代碼 · 台灣 / 香港欄不得有簡體字、大陸欄不得有繁體字(冊上字對照)·
   variants 的詞必須在本方法的同義字裡 · 舊詞庫全數收編(SYNONYM_LIBRARY_v4 scope valuation_method 的 canonical 與每個 raw 詞、
   VRN_ENG062 尾版 VALUATION_METHODS 的每個詞;冊上 excluded_terms 列明不收的除外)。
③ export:操作員稿建議的 JSON 結構(英文 lowercase 陣列 · zh_tw / zh_cn)另加 zh_hk 與 case_sensitive 兩欄 → VIA_Reports/vrn/valuation_method/。
零網路;不用 TA-Lib;正本唯讀;只收 VCGC 呼叫(VIA_FROM_VCGC=YES;--selftest 例外)。
CLI:check · match --text "<句子>" · export · --selftest
結束碼:0 綠 · 1 紅 · 2 拒絕 / 沒輸入
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
import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
OUT = VIA / "VIA_Reports" / "vrn" / "valuation_method"
ENGINE = Path(__file__).stem
SSOT_GLOB = "VIA_VRN_ValuationMethod_SSOT_v*.json"
LEGACY_LIB = HERE / "knowledge" / "SYNONYM_LIBRARY_v4.json"
REGIONS = ("en", "en_case_sensitive", "zh_tw", "zh_hk", "zh_cn")
REGION_OF = {"en": "en", "en_case_sensitive": "en", "zh_tw": "zh_tw", "zh_hk": "zh_hk", "zh_cn": "zh_cn"}


def load_ssot(path: Path | None = None) -> dict:
    if path is None:
        hits = sorted(REG.glob(SSOT_GLOB))
        if not hits:
            raise FileNotFoundError("正本 " + SSOT_GLOB + " 不在 registry")
        path = hits[-1]
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    d["_path"] = Path(path).name
    return d


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = re.sub(r"\s*/\s*", "/", s)
    return re.sub(r"\s+", " ", s)


def _key(term: str, cs: bool) -> str:
    t = norm(term)
    return t if cs else t.lower()


def build_index(book: dict) -> dict:
    """詞 → [(代碼, 地區, 大小寫敏感)];同一詞多區共用 = 一個代碼多個地區。"""
    idx = {}
    for m in book["methods"]:
        for reg in REGIONS:
            cs = reg == "en_case_sensitive"
            for t in m.get(reg, []):
                k = _key(t, cs)
                idx.setdefault((k, cs), {"term": norm(t), "ids": set(), "regions": set(), "cs": cs})
                idx[(k, cs)]["ids"].add(m["id"])
                idx[(k, cs)]["regions"].add(REGION_OF[reg])
    return idx


class Matcher:
    def __init__(self, book: dict | None = None):
        self.book = book or load_ssot()
        self.idx = build_index(self.book)
        self.by_id = {m["id"]: m for m in self.book["methods"]}
        ents = sorted(self.idx.values(), key=lambda e: len(e["term"]), reverse=True)
        parts = []
        for i, e in enumerate(ents):
            t = re.escape(e["term"])
            if re.search(r"[A-Za-z0-9]", e["term"][:1]):
                t = r"(?<![A-Za-z0-9])" + t
            if re.search(r"[A-Za-z0-9]", e["term"][-1:]):
                t = t + r"(?![A-Za-z0-9])"
            parts.append(f"(?P<g{i}>{t})" if e["cs"] else f"(?P<g{i}>(?i:{t}))")
        self.ents = ents
        self.rx = re.compile("|".join(parts))

    def match(self, text: str) -> list:
        s = norm(text)
        out = []
        for m in self.rx.finditer(s):
            e = self.ents[int(m.lastgroup[1:])]
            for vid in sorted(e["ids"]):
                meth = self.by_id[vid]
                variant = [k for k, terms in (meth.get("variants") or {}).items() if any(norm(x).lower() == e["term"].lower() for x in terms)]
                ctx = next((v for k, v in (meth.get("context_required") or {}).items() if norm(k).lower() == e["term"].lower()), "")
                out.append({"id": vid, "term": m.group(0), "regions": sorted(e["regions"]), "variant": variant,
                            "context_required": ctx, "span": [m.start(), m.end()]})
        return out

    def methods_in(self, text: str, strict: bool = True) -> list:
        """去重的代碼(依出現順序);strict 時需語境的命中不算。"""
        seen = []
        for h in self.match(text):
            if strict and h["context_required"]:
                continue
            if h["id"] not in seen:
                seen.append(h["id"])
        return seen


# ---------------------------------------------------------------- check

def _pairs(book: dict) -> tuple:
    raw = re.sub(r"\s+", "", book.get("simplified_traditional_pairs", ""))
    simp = {raw[i] for i in range(0, len(raw) - 1, 2)}
    trad = {raw[i + 1] for i in range(0, len(raw) - 1, 2)}
    return simp, trad


def _legacy_eng062() -> dict:
    """VRN_ENG062 尾版(檔內有 VALUATION_METHODS 的最新一支)的字典,ast 取值不執行。"""
    hits = sorted(HERE.glob("VRN_ENG062_SummarizerV1*.py"), key=lambda p: p.name)
    for p in reversed(hits):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "VALUATION_METHODS" for t in node.targets):
                try:
                    return {"file": p.name, "map": ast.literal_eval(node.value)}
                except Exception:
                    pass
    return {"file": None, "map": {}}


def _legacy_lib() -> dict:
    if not LEGACY_LIB.exists():
        return {}
    d = json.loads(LEGACY_LIB.read_text(encoding="utf-8"))
    out = {}
    for _k, lst in (d.get("scopes", {}).get("valuation_method") or {}).items():
        for e in lst:
            out.setdefault(e["canonical"], []).append(e["raw"])
    return out


def check(book: dict | None = None) -> dict:
    book = book or load_ssot()
    rows, red = [], 0

    def add(name, ok, note=""):
        nonlocal red
        rows.append({"check": name, "lamp": "GREEN" if ok else "RED", "note": note})
        red += 0 if ok else 1
    ms = book["methods"]
    ids = [m["id"] for m in ms]
    add("代碼唯一 · 合規 VAL_<英數底線>", len(ids) == len(set(ids)) and all(re.fullmatch(r"VAL_[A-Z0-9_]+", i) for i in ids),
        [i for i in ids if not re.fullmatch(r"VAL_[A-Z0-9_]+", i)])
    seqs = [m["seq"] for m in ms]
    add("seq 唯一連號 1..N", sorted(seqs) == list(range(1, len(ms) + 1)), seqs)
    add("每個方法都有分組 · 全稱 · 中文名 · 公式", all(m.get("group") in book["groups"] and m.get("primary_name") and m.get("zh_name") and m.get("formula")
                                          for m in ms))
    idx = build_index(book)
    clash = [(e["term"], sorted(e["ids"])) for e in idx.values() if len(e["ids"]) > 1]
    add("同一詞不對到兩個代碼", not clash, clash)
    simp, trad = _pairs(book)
    bad_tw = [(m["id"], t) for m in ms for reg in ("zh_tw", "zh_hk") for t in m.get(reg, []) if set(t) & simp]
    bad_cn = [(m["id"], t) for m in ms for t in m.get("zh_cn", []) if set(t) & trad]
    add("台灣 / 香港欄沒有簡體字", not bad_tw, bad_tw)
    add("大陸欄沒有繁體字", not bad_cn, bad_cn)
    cs_low = [(m["id"], t) for m in ms for t in m.get("en_case_sensitive", []) if not re.fullmatch(r"[A-Z]{2,5}", t)]
    add("大小寫敏感欄只放 2–5 個大寫字母的縮寫", not cs_low, cs_low)
    syn = {m["id"]: {norm(t).lower() for reg in REGIONS for t in m.get(reg, [])} for m in ms}
    stray = [(m["id"], k, t) for m in ms for k, terms in (m.get("variants") or {}).items() for t in terms if norm(t).lower() not in syn[m["id"]]]
    add("變體詞都在本方法的同義字裡", not stray, stray)
    ctx_stray = [(m["id"], t) for m in ms for t in (m.get("context_required") or {}) if norm(t).lower() not in syn[m["id"]]]
    add("需語境詞都在本方法的同義字裡", not ctx_stray, ctx_stray)
    # 舊詞庫收編
    excluded = {norm(k).lower() for k in book.get("excluded_terms", {})}
    canon = {c: m["id"] for m in ms for c in m.get("legacy_canonical", [])}
    mt = Matcher(book)
    lib = _legacy_lib()
    miss_canon = [c for c in lib if c not in canon]
    add("SYNONYM_LIBRARY_v4 每個 canonical 都對到 VAL 代碼", not miss_canon and bool(lib), miss_canon or ("舊詞庫不在" if not lib else ""))
    miss_raw = [(c, r) for c, raws in lib.items() for r in raws if canon.get(c) not in mt.methods_in(r, strict=False)]
    add("SYNONYM_LIBRARY_v4 每個舊詞都被本冊比到同一代碼", not miss_raw, miss_raw)
    e062 = _legacy_eng062()
    miss062 = []
    for c, kws in e062["map"].items():
        if c not in canon:
            miss062.append((c, "canonical 沒對到"))
            continue
        for kw in kws:
            if norm(kw).lower() in excluded:
                continue
            if canon[c] not in mt.methods_in(kw, strict=False) and canon[c] not in mt.methods_in(kw.upper(), strict=False):
                miss062.append((c, kw))
    add(f"VRN_ENG062 VALUATION_METHODS 每個詞都被本冊收編({e062['file'] or '不在'})", not miss062 and bool(e062["map"]), miss062)
    lamp = "RED" if red else "GREEN"
    return {"engine": ENGINE, "ssot": book.get("_path"), "lamp": lamp, "methods": len(ms), "terms": len(idx), "checks": rows,
            "legacy": {"synonym_library_v4": {c: canon.get(c) for c in lib}, "eng062": {c: canon.get(c) for c in e062["map"]}},
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


def export(book: dict | None = None) -> dict:
    book = book or load_ssot()
    return {"ssot": book.get("_path"), "valuation_methods": [
        {"id": m["id"], "seq": m["seq"], "group": m["group"], "primary_name": m["primary_name"], "zh_name": m["zh_name"],
         "en_synonyms": sorted({norm(t).lower() for t in m.get("en", [])}),
         "case_sensitive": list(m.get("en_case_sensitive", [])),
         "zh_tw_synonyms": list(m.get("zh_tw", [])), "zh_hk_synonyms": list(m.get("zh_hk", [])), "zh_cn_synonyms": list(m.get("zh_cn", []))}
        for m in book["methods"]]}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    cmd = args[0] if args else "check"
    if cmd == "match":
        text = args[args.index("--text") + 1] if "--text" in args and args.index("--text") + 1 < len(args) else ""
        if not text:
            print("[評價方法] match 要 --text \"句子\"")
            return 2
        for h in Matcher().match(text):
            print(f"  {h['id']:<14} 「{h['term']}」 地區 {','.join(h['regions'])}" + (f" · 變體 {','.join(h['variant'])}" if h["variant"] else "")
                  + (f" · 需語境:{h['context_required']}" if h["context_required"] else ""))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    if cmd == "export":
        p = OUT / "VALUATION_METHODS_export.json"
        p.write_text(json.dumps(export(), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[評價方法] 匯出 {p}")
        return 0
    rep = check()
    (OUT / "CHECK_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rep["checks"]:
        print(f"  [{r['lamp']}] {r['check']}" + (f" · {r['note']}" if r["note"] and r["lamp"] != "GREEN" else ""))
    print(f"[評價方法 SSOT] {rep['lamp']} · {rep['methods']} 方法 · {rep['terms']} 詞 · 冊 {rep['ssot']}")
    return 0 if rep["lamp"] == "GREEN" else 1


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    book = load_ssot()
    rep = check(book)
    chk("正本檢核全綠(代碼 · 連號 · 一詞一碼 · 繁簡分欄 · 變體 · 舊詞庫收編)", rep["lamp"] == "GREEN",
        [r for r in rep["checks"] if r["lamp"] != "GREEN"])
    chk("16 個方法 · 四組都有", rep["methods"] == 16 and {m["group"] for m in book["methods"]} == set(book["groups"]))
    chk("舊詞庫 6 個 canonical + ENG062 8 個 canonical 全數對到 VAL 代碼",
        all(rep["legacy"]["synonym_library_v4"].values()) and all(rep["legacy"]["eng062"].values()) and len(rep["legacy"]["eng062"]) == 8,
        rep["legacy"])
    mt = Matcher(book)
    m = mt.methods_in
    chk("台灣:「以 2026 年預估本益比 18 倍評價」→ VAL_PE · 變體 forward", m("以 2026 年預估本益比 18 倍評價") == ["VAL_PE"]
        and mt.match("預估本益比")[0]["variant"] == ["forward"])
    chk("大陸:「动态市盈率」→ VAL_PE · 地區 zh_cn", mt.match("给予 25 倍动态市盈率")[0]["regions"] == ["zh_cn"])
    chk("香港 / 大陸共用「市盈率」→ 地區 zh_cn + zh_hk", mt.match("市盈率")[0]["regions"] == ["zh_cn", "zh_hk"])
    chk("台灣「本益比」只標 zh_tw", mt.match("本益比")[0]["regions"] == ["zh_tw"])
    chk("英文常字不誤中:per share / operating / pe / speed", m("EPS per share rose; operating margin; pe; speed") == [], mt.match("EPS per share rose; operating margin; pe; speed"))
    chk("大寫 PER / PE 才中:「PER 15x」→ VAL_PE", m("target PER 15x") == ["VAL_PE"])
    chk("PEG 不被 PE 吃掉", m("PEG of 1.2") == ["VAL_PEG"])
    chk("EV/EBITDA 不被 EV/EBIT 吃掉,反之亦然", m("EV/EBITDA 12x") == ["VAL_EV_EBITDA"] and m("EV/EBIT of 15x") == ["VAL_EV_EBIT"])
    chk("全形與空白正規化:「Ｐ／Ｅ」「P / E」→ VAL_PE", m("Ｐ／Ｅ 18倍") == ["VAL_PE"] and m("P / E of 18x") == ["VAL_PE"])
    chk("最長詞優先:「本益比河流圖」→ VAL_BAND(不是 VAL_PE)· 變體 pe_basis", m("參考本益比河流圖") == ["VAL_BAND"]
        and mt.match("本益比河流圖")[0]["variant"] == ["pe_basis"])
    chk("「PE River」「股價淨值比河流圖」→ VAL_BAND", m("PE River") == ["VAL_BAND"] and m("股價淨值比河流圖") == ["VAL_BAND"]
        and mt.match("股價淨值比河流圖")[0]["variant"] == ["pb_basis"])
    chk("混合段落依序取出 SOTP · DCF · PE", m("We use SOTP: DCF for the core business and 15x P/E for the rest.") == ["VAL_SOTP", "VAL_DCF", "VAL_PE"])
    chk("需語境的詞 strict 不算:「NAV」「Dividend Yield」", m("NAV per unit rose") == [] and m("Dividend Yield 4.5%") == []
        and m("NAV per unit rose", strict=False) == ["VAL_NAV"])
    chk("殖利率法 → VAL_DY;先前交易 → VAL_MA(id_alias VAL_M&A)", m("採殖利率法評價") == ["VAL_DY"] and m("Precedent Transactions") == ["VAL_MA"]
        and mt.by_id["VAL_MA"].get("id_alias") == "VAL_M&A")
    chk("簡體字:「市净率」「股价账面价值比」→ VAL_PB · zh_cn", m("市净率") == ["VAL_PB"] and mt.match("股价账面价值比")[0]["regions"] == ["zh_cn"])
    # 檢核會抓錯
    bad = json.loads(json.dumps(book))
    bad["methods"][0]["zh_tw"].append("市盈率法价")
    bad["methods"][2]["zh_tw"].append("股價淨值比")                    # VAL_PS 搶 VAL_PB 的詞
    bad["methods"][1]["zh_cn"].append("股價淨值倍数")
    r2 = check(bad)
    reds = {r["check"] for r in r2["checks"] if r["lamp"] == "RED"}
    chk("檢核抓錯:台灣欄混簡體字 · 大陸欄混繁體字 · 同一詞兩碼 → RED",
        r2["lamp"] == "RED" and "台灣 / 香港欄沒有簡體字" in reds and "大陸欄沒有繁體字" in reds and "同一詞不對到兩個代碼" in reds, reds)
    bad = json.loads(json.dumps(book))
    bad["methods"][0]["legacy_canonical"] = []
    chk("檢核抓錯:舊詞庫 canonical PE 沒對到 → RED", check(bad)["lamp"] == "RED")
    ex = export(book)
    pe = ex["valuation_methods"][0]
    chk("匯出:操作員稿結構(英文 lowercase 陣列)+ case_sensitive + zh_hk", pe["id"] == "VAL_PE" and "p/e" in pe["en_synonyms"]
        and pe["case_sensitive"] == ["PE", "PER"] and "市盈率" in pe["zh_hk_synonyms"] and "本益比" in pe["zh_tw_synonyms"])
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 閘 · 不匯入 TA-Lib · 不碰網路", "[VIA:ACCEL-BRIDGE" in body and 'os.environ.get("VIA_FROM_VCGC") != "YES"' in body
        and not re.search(r"^\s*(import|from)\s+(" + "ta" + r"lib|requests|urllib)\b", body, re.M))
    print(f"[VRN_ENG395 v0100 評價方法 SSOT] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

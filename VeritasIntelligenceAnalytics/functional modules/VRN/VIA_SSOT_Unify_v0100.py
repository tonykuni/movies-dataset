#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_SSOT_Unify v0100 — 三系統(VCGC / VDF / VRN)SSOT Regex · 同義字 · 規則 合併成同一套(基層建 · 上層審核編號 · L106~L108 / L116)。

原則:只增不減 · 同一 (namespace, key) 的 regex 不同 = 衝突(兩邊都留 · 標 CONFLICT · 附測試向量結果 · 不自動挑)· 同義字聯集 · 來源逐筆記 provenance ·
      編號欄留空給 VCGC 核號 · 三份副本內容完全相同(VRN / VDF / VCGC 各一 · 只寫在 VRN 的輸出區 · 不碰別系統的檔)

動詞:
  --merge [--vrn-ssot <VRN SSOT 夾>] [--vdf <VDF 引擎夾 / ssot_reference>] [--cgc <governance_vocab.json>] --out <輸出夾>
  --selftest
命名空間:ticker · temporal · finreport · broker · market_field · adjprice · rating
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

VERSION = "v0100"
HERE = Path(__file__).resolve().parent
VECTORS = {
    "ticker": {"hit": ["2330", "6488", "2330.TW", "6488.TWO", "2330 TT", "0050", "00878", "00981A", "00679B", "00631L", "00632R", "00635U", "00701T", "0050.TW"], "miss": ["123", "00050X", "12345", "ABCD"]},
    "temporal": {"hit": ["2024-08-01", "2024/08/01", "20240801", "1130801", "2024Q1", "24Q1", "1Q24", "FY24", "FY-23", "Dec-24", "2025/8/19"], "miss": ["abc", "99"]},
}


def _load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _entry(ns, key, kind, value, src, note=""):
    return {"ns": ns, "key": key, "kind": kind, "value": value, "sources": [src], "note": note, "number": ""}


def collect(vrn_ssot: Path | None, vdf: Path | None, cgc: Path | None) -> list:
    E = []
    # ---- VRN2 Regex(最新版)
    if vrn_ssot and vrn_ssot.is_dir():
        rxs = sorted(vrn_ssot.glob("VRN2_Regex_v[0-9][0-9][0-9][0-9].json"))
        if rxs:
            rx = _load(rxs[-1]) or {}; src = rxs[-1].name
            for k, v in rx.items():
                if isinstance(v, str) and k.isupper() and not k.endswith("_desc") and re.search(r"\\d|\^|\$|\[", v):
                    E.append(_entry("ticker" if "TICKER" in k else "temporal" if re.search(r"YEAR|MONTH|QUARTER|DATE|PERIOD", k) else "misc", k, "regex", v, src))
            for t, tv in (rx.get("TW_TICKER_TYPES") or {}).items():
                for f in ("TW_TICKER", "TW_YF_TICKER", "TW_BB_TICKER"):
                    E.append(_entry("ticker", "%s.%s" % (t, f), "regex", tv[f], src, tv.get("zh", "")))
            for f, v in (rx.get("TW_TICKER_ANY") or {}).items():
                if isinstance(v, str) and v.startswith("^"):
                    E.append(_entry("ticker", "ANY.%s" % f, "regex", v, src))
            dt = rx.get("DATE_AND_TIME_PATTERNS") or {}
            for k, v in dt.items():
                if isinstance(v, dict) and v.get("Regex"):
                    E.append(_entry("temporal", k, "regex", v["Regex"], src + "(MasterDict)"))
            if rx.get("FIRST4_PRINCIPLE"):
                E.append(_entry("ticker", "FIRST4_PRINCIPLE", "rule", rx["FIRST4_PRINCIPLE"], src))
        syns = sorted(vrn_ssot.glob("VRN2_Synonyms_v[0-9][0-9][0-9][0-9].json"))
        if syns:
            sy = _load(syns[-1]) or {}; src = syns[-1].name
            for ab, v in (sy.get("BROKER_ABBR") or {}).items():
                E.append(_entry("broker", ab, "synonyms", sorted(set([v.get("zh") or "", v.get("en") or ""] + list(v.get("aliases") or [])) - {""}), src + "(MasterDict)"))
            for row in sy.get("FIN_ITEMS") or []:
                E.append(_entry("finreport", row.get("std"), "synonyms", sorted(set((row.get("zh") or []) + (row.get("en") or []))), src + "(FinLexicon)", row.get("cat", "")))
            for k, v in (sy.get("MARKET_FIELD_ALIASES") or {}).items():
                E.append(_entry("market_field", k, "synonyms", sorted(set(v)), src + "(VDF ALIASES)"))
        for p in sorted(vrn_ssot.glob("VRN_MasterDict_v*.json"))[-1:]:
            md = _load(p) or {}
            for k in ("RATING_LIST", "TARGET_PRICE_LIST"):
                if md.get(k):
                    E.append(_entry("rating", k, "synonyms" if isinstance(md[k], list) else "rule", md[k], p.name))
    # ---- VDF 引擎 + ssot_reference
    if vdf and vdf.exists():
        eng = next(iter(sorted(vdf.glob("VDF_TW_DataFetchEngine_v*.py"))), None) if vdf.is_dir() else None
        if eng:
            s = eng.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'STOCK_REGEX = r"([^"]+)"', s)
            if m:
                E.append(_entry("ticker", "STOCK.TW_TICKER", "regex", m.group(1), eng.name))
            i = s.find("ALIASES = {"); j = s.find("\n}\n", i)
            if i > 0:
                try:
                    al = eval(s[i + len("ALIASES = "):j + 2])  # 常數字典 · 引擎自帶
                    for k, v in al.items():
                        E.append(_entry("market_field", k, "synonyms", sorted(set(v)), eng.name))
                except Exception:  # noqa: BLE001
                    pass
            E.append(_entry("ticker", "IDENTITY_RULE", "rule", "TWSE→.TW · TPEX→.TWO · 'XXXX TT' · 市場不明不猜尾綴 · 名冊排除 ETF / 權證 / 興櫃", eng.name))
        for p in sorted((vdf / "ssot_reference" if vdf.is_dir() else vdf.parent).glob("VDF_AdjPrice_Rule_SSOT_v*.json")):
            E.append(_entry("adjprice", "ADJ_RULE", "rule", _load(p), p.name))
    # ---- VCGC governance_vocab(在才讀)
    if cgc and cgc.exists():
        gv = _load(cgc) or {}
        src = cgc.name
        for ns_name in ("core", "finreport", "temporal", "NS_TEMPORAL", "provider"):
            for can, body in ((gv.get(ns_name) or {}) if isinstance(gv.get(ns_name), dict) else {}).items():
                if isinstance(body, dict):
                    if body.get("regex"):
                        E.append(_entry("temporal" if "TEMPORAL" in ns_name.upper() else ns_name, can, "regex", body["regex"], src))
                    if body.get("synonyms"):
                        E.append(_entry(ns_name, can, "synonyms", sorted(set(body["synonyms"])), src))
        for can, body in ((gv.get("TW_TICKER_LOCK") or {}) if isinstance(gv.get("TW_TICKER_LOCK"), dict) else {}).items():
            if isinstance(body, dict):
                for k, v in body.items():
                    if isinstance(v, str) and v.startswith("^"):
                        E.append(_entry("ticker", "CGC_LOCK.%s.%s" % (can, k), "regex", v, src))
    return E


def _vec(ns: str, rx: str) -> dict:
    v = VECTORS.get(ns)
    if not v:
        return {}
    try:
        c = re.compile(rx)
    except re.error as exc:
        return {"compile": "ERROR %s" % exc}
    return {"hit": [x for x in v["hit"] if c.search(x)], "miss_wrongly": [x for x in v["miss"] if c.search(x)]}


def merge(entries: list) -> tuple:
    U, C = {}, []
    for e in entries:
        k = (e["ns"], e["key"])
        if k not in U:
            U[k] = dict(e, sources=list(e["sources"]), variants=[])
            continue
        u = U[k]
        if e["kind"] == "synonyms" and u["kind"] == "synonyms":
            u["value"] = sorted(set(u["value"]) | set(e["value"]))              # 同義字聯集 · 只增
            u["sources"] += e["sources"]
        elif e["kind"] == "regex" and u["kind"] == "regex" and e["value"] != u["value"]:
            va, vb = _vec(e["ns"], e["value"]), _vec(u["ns"], u["value"])
            eq = bool(va) and va == vb                                          # 測試向量結果相同 = 等價寫法 · 不算衝突
            u["variants"].append({"value": e["value"], "sources": e["sources"], "vectors": va, "equivalent": eq})
            u["sources"] += e["sources"]
            if eq:
                continue
            C.append({"ns": e["ns"], "key": e["key"], "canonical": u["value"], "canonical_sources": u["sources"][:1], "canonical_vectors": _vec(e["ns"], u["value"]), "variant": e["value"], "variant_sources": e["sources"], "variant_vectors": _vec(e["ns"], e["value"]), "ruling": "待 VCGC 裁決(兩邊都保留 · 不自動挑)"})
        else:
            u["sources"] += e["sources"]
    out = sorted(U.values(), key=lambda x: (x["ns"], str(x["key"])))
    for u in out:
        u["sources"] = sorted(set(u["sources"]))
        u["status"] = "CONFLICT" if any(not v.get("equivalent") for v in u["variants"]) else ("EQUIVALENT" if u["variants"] else "OK")
        if u["kind"] == "regex":
            u["vectors"] = _vec(u["ns"], u["value"])
    return out, C


def write(out_dir: Path, unified: list, conflicts: list, inputs: list) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    book = {"book": "VIA_SSOT_Unified", "version": VERSION, "ts": _dt.datetime.now().isoformat(timespec="seconds"), "built_by": "VRN(基層建 · L116)", "numbering": "number 欄留空 · 由 VCGC 審核後核號", "rule": "只增不減 · 同 (ns,key) regex 不同 = CONFLICT 兩邊都留 · 同義字聯集 · 三系統副本內容相同", "inputs": inputs,
            "namespaces": sorted(set(u["ns"] for u in unified)), "count": {"entries": len(unified), "conflicts": len(conflicts), "regex": sum(1 for u in unified if u["kind"] == "regex"), "synonyms": sum(1 for u in unified if u["kind"] == "synonyms"), "rules": sum(1 for u in unified if u["kind"] == "rule")}, "entries": unified}
    raw = json.dumps(book, ensure_ascii=False, indent=1)
    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    for name in ("VIA_SSOT_Unified_%s.json" % VERSION, "VRN2_SSOT_Unified_latest.json", "VDF_SSOT_Unified_latest.json", "VCGC_SSOT_Unified_latest.json"):
        (out_dir / name).write_text(raw, encoding="utf-8")
    (out_dir / ("VIA_SSOT_Conflicts_%s.json" % VERSION)).write_text(json.dumps({"ts": book["ts"], "conflicts": conflicts}, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# VIA SSOT 統一冊 %s · %s" % (VERSION, book["ts"]), "", "條目 %d(regex %d · 同義字 %d · 規則 %d)· 衝突 %d · 命名空間 %s · 三份副本 sha256 %s" % (len(unified), book["count"]["regex"], book["count"]["synonyms"], book["count"]["rules"], len(conflicts), ", ".join(book["namespaces"]), sha[:12]), ""]
    if conflicts:
        md += ["## 衝突(待 VCGC 裁決)", ""] + ["- %s/%s · 正本 `%s`(%s)· 變體 `%s`(%s)· 向量:正本 %s / 變體 %s" % (c["ns"], c["key"], c["canonical"], ",".join(c["canonical_sources"]), c["variant"], ",".join(c["variant_sources"]), c["canonical_vectors"].get("hit", [])[:6], c["variant_vectors"].get("hit", [])[:6]) for c in conflicts] + [""]
    (out_dir / "VIA_SSOT_Unified_latest.md").write_text("\n".join(md), encoding="utf-8")
    return {"sha": sha, "count": book["count"], "namespaces": book["namespaces"]}


def selftest() -> int:
    ok = 0
    E = [_entry("ticker", "STOCK.TW_TICKER", "regex", r"^([1-9]\d{3})$", "A"), _entry("ticker", "STOCK.TW_TICKER", "regex", r"^[1-9]\d{3}$", "B"),
         _entry("ticker", "X", "regex", r"^(00\d{3})$", "A"), _entry("ticker", "X", "regex", r"^(00\d{2,3})$", "B"),
         _entry("finreport", "revenue", "synonyms", ["營收", "Revenue"], "A"), _entry("finreport", "revenue", "synonyms", ["營業收入", "Revenue"], "B")]
    U, C = merge(E)
    u = {(x["ns"], x["key"]): x for x in U}
    a = u[("finreport", "revenue")]["value"] == ["Revenue", "營业收入"] if False else u[("finreport", "revenue")]["value"] == sorted({"營收", "Revenue", "營業收入"})
    print("  [%s] 同義字聯集 %s" % ("OK" if a else "FAIL", u[("finreport", "revenue")]["value"])); ok += int(a)
    b = len(C) == 1 and u[("ticker", "X")]["status"] == "CONFLICT" and u[("ticker", "STOCK.TW_TICKER")]["status"] == "EQUIVALENT" and "0050" in C[0]["variant_vectors"]["hit"] and "0050" not in C[0]["canonical_vectors"]["hit"]
    print("  [%s] 等價寫法不算衝突(EQUIVALENT)· 真衝突 %d 筆兩邊都留 · 向量顯示 00\\d{3} 對不到 0050 而 00\\d{2,3} 對得到" % ("OK" if b else "FAIL", len(C))); ok += int(b)
    import tempfile
    td = Path(tempfile.mkdtemp())
    r = write(td, U, C, ["selftest"])
    c = all((td / n).exists() for n in ("VRN2_SSOT_Unified_latest.json", "VDF_SSOT_Unified_latest.json", "VCGC_SSOT_Unified_latest.json")) and len({hashlib.sha256((td / n).read_bytes()).hexdigest() for n in ("VRN2_SSOT_Unified_latest.json", "VDF_SSOT_Unified_latest.json", "VCGC_SSOT_Unified_latest.json")}) == 1
    print("  [%s] 三份副本內容相同 · 編號欄留空 %s" % ("OK" if c else "FAIL", all(x["number"] == "" for x in U))); ok += int(c and all(x["number"] == "" for x in U))
    print("[計] VIA_SSOT_Unify %s 自測 %d/3 · %s" % (VERSION, ok, "PASS" if ok == 3 else "FAIL"))
    return 0 if ok == 3 else 1


def main(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest()
    if "--merge" in argv:
        vrn = Path(opt("--vrn-ssot", str(HERE / "SSOT"))); vdf = Path(opt("--vdf", str(HERE / "_vdf_fetch"))); cgc = Path(opt("--cgc")) if opt("--cgc") else None
        if not cgc:
            for cand in (HERE.parent / "VCGC", HERE.parent.parent / "registry", HERE.parent.parent / "VIA_Reports" / "vcgc", HERE.parent.parent / "dict"):   # 只找 VIA 根下固定幾處(≤ 3 層)
                try:
                    hits = [p for pat in ("governance_vocab.json", "*/governance_vocab.json", "*/*/governance_vocab.json") for p in cand.glob(pat)] if cand.is_dir() else []
                except Exception:  # noqa: BLE001
                    hits = []
                if hits:
                    cgc = sorted(hits, key=lambda p: p.stat().st_mtime)[-1]; break
        out = Path(opt("--out", str(HERE.parent.parent / "VIA_Reports" / "vrn2" / "ssot_unified")))
        E = collect(vrn, vdf, cgc)
        U, C = merge(E)
        r = write(out, U, C, [str(vrn), str(vdf), str(cgc) if cgc else "(VCGC governance_vocab 未找到 · 之後再併)"])
        print("[計] SSOT 統一冊 · 條目 %d(regex %d · 同義字 %d · 規則 %d)· 衝突 %d · 命名空間 %s · VCGC 冊 %s · 三份副本 → %s · sha %s" % (
            r["count"]["entries"], r["count"]["regex"], r["count"]["synonyms"], r["count"]["rules"], r["count"]["conflicts"], ",".join(r["namespaces"]), "已併" if cgc else "未找到", out, r["sha"][:12]), flush=True)
        for c in C[:8]:
            print("[計]   衝突 %s/%s · 正本 %s(%s)· 變體 %s(%s)" % (c["ns"], c["key"], c["canonical"], ",".join(c["canonical_sources"])[:40], c["variant"], ",".join(c["variant_sources"])[:40]), flush=True)
        return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

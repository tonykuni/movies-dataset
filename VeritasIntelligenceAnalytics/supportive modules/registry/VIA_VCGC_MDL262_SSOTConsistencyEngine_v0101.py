#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_VCGC_MDL262_SSOTConsistencyEngine v0101 — 薄尾:領域涵蓋(輸入 · 輸出 · 參數 · 時間範圍 · 券商 · 分析師 … 每一類、每個系統都要有 SSOT)

操作員 2026-11-14:「INPUT OUTPUT PARAMTERS TIME RANGE BROKER ANALYST .......ALL SHOULD HAVE SSOT」。
v0100 管的是正則 / 同義字 / 編號在來源之間「對不對得上」;本版補「有沒有」:照領域涵蓋冊
VIA_SSOT_DomainCoverage_SSOT 尾版,逐「類 × 系統」回報:
  GREEN   有正本,且找得到中央號(編號冊有這本冊 / 這類的列,或它在中央冊、聯集冊裡)
  YELLOW  有正本但找不到中央號,或冊上註明只涵蓋一部分(partial)
  NODATA  這個系統在這一類沒有宣告、也找不到正本(= 缺口)
  N/A     該系統自己宣告不適用(帶理由)
新動詞:
  python VIA_VCGC_MDL262_SSOTConsistencyEngine_v0101.py domains [--json]     類 × 系統矩陣 + 缺口清單(零寫;有缺口 rc 1)
其餘動詞(check · view · probe · cases · rule · ledger · fmea)原樣交給 v0100;check 的文字輸出尾端多一行領域涵蓋摘要。
VCGC 自己的模組:對 VDF / VRN / VAP / VQG 只讀;缺口只攤開、指路給該系統的管理器,不代建、不代修(L123)。零網路 · 純標準庫 · 不寫任何檔。
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

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_MDL262_SSOTConsistencyEngine"
ENGINE = _STEM
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
DOMAIN_GLOB = "VIA_SSOT_DomainCoverage_SSOT_v[0-9][0-9][0-9][0-9].json"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_scc_prior_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]


def __getattr__(name: str):
    return getattr(PRIOR, name)


def load_domain_book(registry: Path):
    hits = sorted(Path(registry).glob(DOMAIN_GLOB), key=_vnum)
    if not hits:
        raise ValueError("領域涵蓋冊不存在(%s)" % DOMAIN_GLOB)
    return hits[-1], BASE.read_json(hits[-1])


def _family(name: str) -> str:
    return re.sub(r"(_v\d{4})?\.[A-Za-z0-9]+$", "", name)


def _numbered_sources(registry: Path) -> tuple:
    """編號冊裡出現過的來源檔名 / 冊家族名與各 kind × sub 的列數(分冊 VIA_NumberBooks/*.jsonl + 總冊 VIA_Numbering_SSOT 的 rows:SSOT · RGX · SYN)。
    壞列跳過並計數,不讓一列壞掉拖垮整輪。"""
    names, kinds, bad = set(), {}, 0

    def take(r):
        src = r.get("source")
        if isinstance(src, str) and src:
            base = src.replace("\\", "/").rsplit("/", 1)[-1]
            names.add(base)
            names.add(_family(base))
        if r.get("kind") == "SSOT" and isinstance(r.get("name"), str):
            names.add(r["name"])
        k = (r.get("kind"), r.get("sub"))
        kinds[k] = kinds.get(k, 0) + 1
    for f in sorted(Path(registry).glob("VIA_Numbering_SSOT_v[0-9][0-9][0-9][0-9].json"), key=_vnum)[-1:]:
        try:
            rows = (BASE.read_json(f).get("rows") or {})
        except ValueError:
            rows, bad = {}, bad + 1
        for lst in rows.values() if isinstance(rows, dict) else []:
            for r in lst if isinstance(lst, list) else []:
                if isinstance(r, dict):
                    take(r)
    for f in sorted((Path(registry) / "VIA_NumberBooks").glob("VIA_NumberBook_*.jsonl")):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    bad += 1
                    continue
                if isinstance(r, dict):
                    take(r)
    return names, kinds, bad


def coverage(via: Path, registry: Path) -> dict:
    """類 × 系統:逐格找證據。只讀;來源讀不了的證據記在格子裡,不當成有。"""
    path, book = load_domain_book(registry)
    names, kinds, bad_rows = _numbered_sources(registry)
    cache = {}

    def tail_json(pattern):
        if pattern not in cache:
            hits = sorted(Path(registry).glob(pattern), key=_vnum)
            try:
                cache[pattern] = BASE.read_json(hits[-1]) if hits else None
            except ValueError:
                cache[pattern] = None
        return cache[pattern]

    union = tail_json("VIA_SSOT_SynonymUnion_v[0-9][0-9][0-9][0-9].json") or {}
    central = tail_json("VIA_Central_Synonym_Regex_v[0-9][0-9][0-9][0-9].json") or {}
    cands = (tail_json("VIA_AssetCandidates_SSOT_v[0-9][0-9][0-9][0-9].json") or {}).get("assets") or []
    grant = {}
    gp = Path(registry) / "VCGC_NUMBER_GRANT_latest.json"
    if gp.is_file():
        try:
            grant = (BASE.read_json(gp).get("assets") or {})
        except ValueError:
            grant = {}
    central_keys = list((central.get("regex") or {})) + list((central.get("synonyms") or {}))

    def probe(ev: dict) -> dict:
        partial = ev.get("partial")
        if "book" in ev:
            files = [f for f in BASE.tails(via, ev["book"]) if f.is_file()]
            okf, numbered, broken = [], False, []
            for f in files:
                try:
                    BASE.read_json(f)
                    okf.append(f.name)
                    numbered = numbered or f.name in names or _family(f.name) in names
                except ValueError as exc:
                    broken.append("%s(%s)" % (f.name, str(exc)[:40]))
            return {"kind": "book", "what": ev["book"].rsplit("/", 1)[-1], "found": len(okf), "numbered": numbered, "partial": partial,
                    "detail": " · ".join(okf[:3]) + ((" · 讀不了 " + " · ".join(broken[:2])) if broken else "")}
        if "number_kind" in ev:
            n = kinds.get((ev["number_kind"], ev.get("sub")), 0)
            return {"kind": "number", "what": "編號冊 %s × %s" % (ev["number_kind"], ev.get("sub")), "found": n, "numbered": n > 0, "partial": partial,
                    "detail": "%d 列" % n}
        if "union_scope" in ev:
            n = len((union.get("scopes") or {}).get(ev["union_scope"]) or {})
            return {"kind": "union", "what": "聯集冊範疇 " + ev["union_scope"], "found": n, "numbered": n > 0, "partial": partial, "detail": "%d 詞" % n}
        if "central_key" in ev:
            rx = re.compile(ev["central_key"])
            hit = [k for k in central_keys if rx.search(k)]
            return {"kind": "central", "what": "中央冊鍵 " + ev["central_key"], "found": len(hit), "numbered": bool(hit), "partial": partial,
                    "detail": " · ".join(hit[:4])}
        if "candidate" in ev:
            c = ev["candidate"]
            rx = re.compile(c["scope_rx"], re.I) if c.get("scope_rx") else None
            hit = [a for a in cands if isinstance(a, dict) and a.get("owner") == c.get("owner")
                   and (not c.get("types") or a.get("asset_type") in c["types"])
                   and (rx is None or rx.search(str(a.get("scope") or "")) or rx.search(str(a.get("semantic_key") or "")))]
            num = sum(1 for a in hit if isinstance(grant.get(a.get("source_pointer")), dict) and grant[a["source_pointer"]].get("code"))
            return {"kind": "candidate", "what": "候選冊 %s %s" % (c.get("owner"), "/".join(c.get("types") or []) or c.get("scope_rx")),
                    "found": len(hit), "numbered": num > 0, "partial": partial, "detail": "%d 筆(已發號 %d)" % (len(hit), num)}
        return {"kind": "?", "what": str(ev)[:60], "found": 0, "numbered": False, "partial": partial, "detail": "冊上的證據型別引擎不認得"}

    systems = list(book.get("systems") or [])
    cells, gaps = {}, []
    for dom, spec in (book.get("domains") or {}).items():
        na = spec.get("na") or {}
        for s in systems:
            if s in na:
                cells[(dom, s)] = {"state": "N/A", "why": str(na[s]), "evidence": []}
                continue
            evs = [probe(e) for e in (spec.get("evidence") or {}).get(s) or []]
            found = [e for e in evs if e["found"]]
            if not found:
                state = "NODATA"
                why = "沒有宣告正本" if not evs else "宣告的正本都找不到:" + " · ".join(e["what"] for e in evs[:3])
                gaps.append({"domain": dom, "zh": spec.get("zh", dom), "system": s, "state": state, "why": why,
                             "next": "由 %s 自己的管理器建這一類的 SSOT 正本並送核號;不適用就宣告 na(VCGC 不代建)" % s})
            else:
                partial = [e["partial"] for e in found if e.get("partial")]
                whole = [e for e in found if not e.get("partial")]
                numbered = any(e["numbered"] for e in found)
                state = "GREEN" if whole and numbered else "YELLOW"
                why = ("只涵蓋一部分:" + ";".join(partial[:2])) if not whole else ("有正本,但編號冊找不到它的號" if not numbered else "")
                if state == "YELLOW":
                    gaps.append({"domain": dom, "zh": spec.get("zh", dom), "system": s, "state": state, "why": why,
                                 "next": ("由 %s 補齊這一類的正本" % s) if not whole else "提交後跑中央編號(CGC_MDL237 --apply --scope)"})
            cells[(dom, s)] = {"state": state, "why": why, "evidence": evs}
    tally = {}
    for c in cells.values():
        tally[c["state"]] = tally.get(c["state"], 0) + 1
    lamp = "GREEN" if set(tally) <= {"GREEN", "N/A"} else ("YELLOW" if tally else "NODATA")
    return {"book": BASE.rel_posix(path, via), "systems": systems, "domains": {k: v.get("zh", k) for k, v in (book.get("domains") or {}).items()},
            "cells": cells, "gaps": gaps, "tally": tally, "lamp": lamp, "bad_number_rows": bad_rows}


def print_domains(cov: dict) -> None:
    t = cov["tally"]
    print("[SSOT 領域涵蓋] %s · %s %s · %d 類 × %d 系統 · 綠 %d · 黃 %d · 無 %d · 不適用 %d · 冊 %s" % (
        cov["lamp"], ENGINE, TAG, len(cov["domains"]), len(cov["systems"]), t.get("GREEN", 0), t.get("YELLOW", 0), t.get("NODATA", 0),
        t.get("N/A", 0), cov["book"].rsplit("/", 1)[-1]))
    print("  %-16s %s" % ("類", "  ".join("%-7s" % s for s in cov["systems"])))
    for dom, zh in cov["domains"].items():
        print("  %-16s %s" % (zh, "  ".join("%-7s" % cov["cells"][(dom, s)]["state"] for s in cov["systems"])))
    for g in cov["gaps"]:
        print("  [缺口] %-6s %s × %s · %s → %s" % (g["state"], g["zh"], g["system"], g["why"][:120], g["next"]))
    if cov["bad_number_rows"]:
        print("  [附記] 編號冊有 %d 列讀不了(已跳過,不當成有號)" % cov["bad_number_rows"])


def summary_line(cov: dict) -> str:
    t = cov["tally"]
    return "  [領域涵蓋] %s · 綠 %d · 黃 %d · 無 %d(共 %d 格;細節:domains)" % (cov["lamp"], t.get("GREEN", 0), t.get("YELLOW", 0),
                                                                  t.get("NODATA", 0), len(cov["cells"]))


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a and not a[0].startswith("--") else "check"
    if verb == "domains":
        if set(x for x in a[1:] if x.startswith("--")) - {"--json"} or [x for x in a[1:] if not x.startswith("--")]:
            print("用法:python %s domains [--json]" % Path(__file__).name)
            return 2
        try:
            cov = coverage(BASE.VIA, BASE.VIA / "supportive modules" / "registry")
        except ValueError as exc:
            print("[SSOT 領域涵蓋] RED · %s" % exc)
            return 1
        if "--json" in a:
            out = dict(cov, cells={"%s|%s" % k: v for k, v in cov["cells"].items()})
            print(json.dumps(out, ensure_ascii=False, indent=1))
        else:
            print_domains(cov)
        return 0 if cov["lamp"] == "GREEN" else 1
    rc = PRIOR.main(a)
    if verb == "check" and "--json" not in a and rc in (0, 1):
        try:
            print(summary_line(coverage(BASE.VIA, BASE.VIA / "supportive modules" / "registry")))
        except ValueError as exc:
            print("  [領域涵蓋] RED · %s" % exc)
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK " if cond else "NG ", name, (" · " + str(note)[:200]) if note and not cond else ""))

    print("=== %s %s · 薄尾自測(領域涵蓋:類 × 系統)===" % (ENGINE, TAG))
    with tempfile.TemporaryDirectory(prefix="via_scc_dom_") as td:
        via = Path(td)
        reg = via / "supportive modules" / "registry"
        (reg / "VIA_NumberBooks").mkdir(parents=True)
        (via / "functional modules" / "VDF").mkdir(parents=True)
        (via / "functional modules" / "VRN").mkdir(parents=True)
        (via / "functional modules" / "VDF" / "VDF_Input_SSOT_v0100.json").write_text("{}", encoding="utf-8")
        (via / "functional modules" / "VDF" / "VDF_Out_SSOT_v0100.json").write_text("{}", encoding="utf-8")
        (via / "functional modules" / "VRN" / "VRN_Bad_SSOT_v0100.json").write_bytes(b"{not json")
        (reg / "VIA_NumberBooks" / "VIA_NumberBook_X_v0100.jsonl").write_text(
            json.dumps({"kind": "PRMT", "sub": "VDF", "source": "functional modules/VDF/VDF_Input_SSOT_v0100.json"}) + "\n{broken row\n", encoding="utf-8")
        (reg / "VIA_SSOT_SynonymUnion_v0100.json").write_text(json.dumps({"scopes": {"broker": {"a": [], "b": []}, "job_title": {"t": []}}}), encoding="utf-8")
        (reg / "VIA_Central_Synonym_Regex_v0100.json").write_text(json.dumps({"regex": {"TW_TICKER": {}}, "synonyms": {}}), encoding="utf-8")
        (reg / "VIA_AssetCandidates_SSOT_v0100.json").write_text(json.dumps({"assets": [
            {"owner": "VQG", "asset_type": "INPT", "scope": "x", "semantic_key": "k", "source_pointer": "p1"}]}), encoding="utf-8")
        book = {"systems": ["VCGC", "VDF", "VRN", "VAP", "VQG"], "domains": {
            "input": {"zh": "輸入", "evidence": {"VDF": [{"book": "functional modules/VDF/VDF_Input_SSOT_v[0-9][0-9][0-9][0-9].json"}],
                                               "VQG": [{"candidate": {"owner": "VQG", "types": ["INPT"]}}]}, "na": {"VAP": "VAP 不收外部輸入"}},
            "output": {"zh": "輸出", "evidence": {"VDF": [{"book": "functional modules/VDF/VDF_Out_SSOT_v[0-9][0-9][0-9][0-9].json"}],
                                                "VRN": [{"book": "functional modules/VRN/VRN_Bad_SSOT_v[0-9][0-9][0-9][0-9].json"}]}},
            "parameter": {"zh": "參數", "evidence": {"VDF": [{"number_kind": "PRMT", "sub": "VDF"}], "VRN": [{"number_kind": "PRMT", "sub": "VRN"}]}},
            "broker": {"zh": "券商", "evidence": {"VCGC": [{"union_scope": "broker"}]}},
            "analyst": {"zh": "分析師", "evidence": {"VCGC": [{"union_scope": "job_title", "partial": "只有職稱"}]}},
            "ticker": {"zh": "代號", "evidence": {"VCGC": [{"central_key": "^TW_"}], "VDF": [{"central_key": "^NOPE_"}], "VRN": [{"mystery": 1}]}}}}
        (reg / "VIA_SSOT_DomainCoverage_SSOT_v0100.json").write_text(json.dumps(book, ensure_ascii=False), encoding="utf-8")
        before = sorted((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in via.rglob("*") if p.is_file())
        cov = coverage(via, reg)
        st = {k: v["state"] for k, v in cov["cells"].items()}
        chk("① 有正本 + 編號冊有它 → GREEN", st[("input", "VDF")] == "GREEN")
        chk("② 有正本但編號冊沒有它 → YELLOW(不是綠)", st[("output", "VDF")] == "YELLOW" and "找不到" in cov["cells"][("output", "VDF")]["why"])
        chk("③ 沒有宣告正本 → NODATA 並列進缺口,指路給該系統(VCGC 不代建)", st[("input", "VRN")] == "NODATA"
            and any(g["domain"] == "input" and g["system"] == "VRN" and "不代建" in g["next"] for g in cov["gaps"]))
        chk("④ 宣告了但檔壞掉讀不了 → 不當成有(NODATA)", st[("output", "VRN")] == "NODATA")
        chk("⑤ 系統宣告不適用 → N/A 帶理由,不算缺口", st[("input", "VAP")] == "N/A" and not any(g["system"] == "VAP" and g["domain"] == "input" for g in cov["gaps"]))
        chk("⑥ 編號冊某類 × 某系統有列 → GREEN;沒有列 → NODATA", st[("parameter", "VDF")] == "GREEN" and st[("parameter", "VRN")] == "NODATA")
        chk("⑦ 聯集冊 / 中央冊的證據算數;partial 的證據只給 YELLOW", st[("broker", "VCGC")] == "GREEN" and st[("ticker", "VCGC")] == "GREEN"
            and st[("analyst", "VCGC")] == "YELLOW" and "只有職稱" in cov["cells"][("analyst", "VCGC")]["why"])
        chk("⑧ 候選冊有但沒發號 → YELLOW;中央冊鍵找不到 → NODATA;冊上寫了引擎不認得的證據 → 不當成有",
            st[("input", "VQG")] == "YELLOW" and st[("ticker", "VDF")] == "NODATA" and st[("ticker", "VRN")] == "NODATA")
        chk("⑨ 編號冊壞列跳過並計數,不拖垮整輪", cov["bad_number_rows"] == 1)
        chk("⑩ 整張的燈:有黃或有缺就不是綠", cov["lamp"] == "YELLOW" and cov["tally"].get("NODATA", 0) > 0)
        after = sorted((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in via.rglob("*") if p.is_file())
        chk("⑪ 只讀:跑完樹內一個位元都沒動、沒有多出任何檔", before == after)
        (reg / "VIA_SSOT_DomainCoverage_SSOT_v0100.json").unlink()
        try:
            coverage(via, reg)
            missing = False
        except ValueError:
            missing = True
        chk("⑫ 領域涵蓋冊不在 → 照實報錯,不編一張空的綠表", missing)
    src = Path(__file__).read_text(encoding="utf-8")
    pre = src.split("def selftest")[0]          # 自測以外的程式(自測自己會在暫存夾寫夾具)
    chk("⑬ 加速器橋在;不碰 TA-Lib;自測以外沒有任何寫檔動作", "VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"\.write_text\(|\.write_bytes\(|os\.replace|open\([^)]*['\"][wa]b?['\"]", pre))
    print("[%s %s 薄尾自測] %d/%d %s" % (ENGINE, TAG, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

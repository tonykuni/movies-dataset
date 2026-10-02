#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL255_GitHubPanorama v0101 — 薄尾:+union 動詞(同義字 · 正則 · 冊 三本「只增不衝突」聯集提案;只讀)

操作員(2026-10-03,貼回 v0100 的 SSOT / Regex / Synonyms 三頁):「先就此部分做一輪改善優化 · 定義這些只要不衝突就可以增」。

量到的(origin/main 12e21cb):同義字 dict 13 本散在 9 支引擎;正則字面 1268 條,同一句(台股四碼 · .TW/.TWO · ISO 日期 · _v(\d+)$ 版號 · 季別)
在幾十支裡各抄一份;冊 895 本裡有 sha 副本與正本 sha16 完全相同的、鍵數 0 的空冊、沒版號的。本尾版只做三件事,全部只讀:

  union  →  VIA_Reports/github_panorama/
    VIA_GHP_SynonymUnion_v0100.json  13 本 dict 用 ast.literal_eval 讀出(非純字面的跳過照記),依名稱分命名空間
                                      (company · financial_field · rating · broker · column_param;PS 別名 / 函數別名不算同義字,排除),
                                      方向自動判(值是 list = 正典→別名;值是 str = 別名→正典),別名正規化(去空白 · 全半形 · 大小寫)後聯集;
                                      同命名空間同一別名指向兩個正典 = CONFLICT 照列不裁;其餘 = 可增(additive)
    VIA_GHP_RegexUnion_v0100.json    1268 條依樣式字串精確分群(同句不同檔 = 一群),標家族(ticker / date / quarter / version / percent / html / other),
                                      用到的檔數 · 行;再對 VIA_Central_Synonym_Regex 尾版做字串涵蓋:不在冊且 ≥2 檔共用 = 候選入冊(只提案)
    VIA_GHP_BookDedup_v0100.json     冊:sha16 完全相同的副本群(建議留正本名、副本進名冊,不刪)· keys 0 的空冊 · 沒版號的冊 · BOM / BROKEN 與修好副本的對應
  --promote 把三本冊複製進 registry(已有就下一個版號;只增不減)。
用法  VIA_FROM_VCGC=YES python CGC_MDL255_GitHubPanorama_v0101.py union [--ref origin/main] [--repo <倉根>] [--promote]
      其餘動詞(scan)與自測照 v0100。結束碼:0 同義字零衝突 · 2 有衝突(列在 SynonymUnion.conflicts)· 1 跑不動
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
import collections
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
STEM = "CGC_MDL255_GitHubPanorama"
ENGINE = STEM + "_v0101"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


NS_BY_NAME = [
    (re.compile(r"COMPANY|TICKER", re.I), "company"),
    (re.compile(r"BROKER", re.I), "broker"),
    (re.compile(r"RATING|BUCKET", re.I), "rating"),
    (re.compile(r"FINANCIAL|ACCOUNT|CANON_ALIAS|FINLEX|METRIC", re.I), "financial_field"),
    (re.compile(r"COL_|UNIFIED_ALIAS|PARAM", re.I), "column_param"),
]
EXCLUDE_NAMES = re.compile(r"^(COMMON_ALIASES|ALIASES)$")   # PS 別名 / 函數別名:不是領域同義字
FAMILY_RX = [
    ("ticker", re.compile(r"\[1-9\]\\d\{3\}|00\\d\{3\}|\\.TWO?|\\.\(TW\|TWO\)|TT\\b|\\d\{4\}\[A-Z\]")),
    ("date", re.compile(r"\\d\{4\}-\\d\{2\}-\\d\{2\}|\\d\{2,4\}\)\[\.\\/\-\]|民國|年|\\d\{8\}")),
    ("quarter", re.compile(r"Q\[1-4\]|\[1-4\]\)?Q|FY|H\[12\]|\[12\]\)?H|\[EFA\]|\[AEF\]")),
    ("version", re.compile(r"_v\(\\d|v\(\\d\{2,4\}\)")),
    ("percent_number", re.compile(r"\\d\[\\d,\]\*|%|％|\(\?:\\.\\d\+\)\?")),
    ("html_xml", re.compile(r"<\[\^>\]\+>|<w:|<tr|<t\[dh\]|href|src")),
    ("rating", re.compile(r"買進|賣出|中立|持有|Buy|Sell|Hold|評等")),
]


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKC", str(s)).strip().lower()


def _ckey(c: str) -> str:
    """正典鍵正規化:'Gross Profit' · 'gross_profit' · 'GROSS-PROFIT' 是同一個正典的三種拼法,不算衝突(拼法另列 variants)。"""
    return re.sub(r"[\s_\-]+", "", _norm(c))


def union(repo: Path, ref: str | None, out_dir: Path, promote: bool = False) -> dict:
    idx_p = out_dir / "GHP_latest.json"
    if not idx_p.is_file():
        PRIOR.scan(repo, ref, out_dir, promote=False, open_page=False)
    syn_rows = json.loads((out_dir / "VIA_GHP_Synonyms_SSOT_v0100.json").read_text(encoding="utf-8"))["rows"]
    rx_rows = json.loads((out_dir / "VIA_GHP_Regex_SSOT_v0100.json").read_text(encoding="utf-8"))["rows"]
    bk_rows = json.loads((out_dir / "VIA_GHP_SSOT_SSOT_v0100.json").read_text(encoding="utf-8"))["rows"]
    idx = json.loads(idx_p.read_text(encoding="utf-8"))
    tree = PRIOR.Tree(repo, ref)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # ---- ① 同義字聯集 ----
    ns_map: dict[str, dict[str, set]] = collections.defaultdict(lambda: collections.defaultdict(set))   # ns -> ckey -> aliases
    alias_owner: dict[tuple[str, str], set] = collections.defaultdict(set)                                 # (ns, alias) -> ckeys
    variants: dict[str, dict[str, set]] = collections.defaultdict(lambda: collections.defaultdict(set))  # ns -> ckey -> 正典拼法
    sources, skipped = [], []
    for r in syn_rows:
        name = r["name"]
        if EXCLUDE_NAMES.match(name):
            skipped.append({"file": r["file"], "name": name, "why": "PS 別名 / 函數別名,不是領域同義字"})
            continue
        ns = next((n for rx, n in NS_BY_NAME if rx.search(name)), "other")
        try:
            src = tree.read(r["file"]).decode("utf-8", "replace")
            node = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Assign) and n.lineno == r["line"])
            val = ast.literal_eval(node.value)
        except Exception as exc:
            skipped.append({"file": r["file"], "name": name, "why": "非純字面 dict,literal_eval 不到:" + str(exc)[:60]})
            continue
        if not isinstance(val, dict) or not val:
            skipped.append({"file": r["file"], "name": name, "why": "不是非空 dict"})
            continue
        direction = "canonical->aliases" if all(isinstance(v, (list, tuple, set)) for v in val.values()) else ("alias->canonical" if all(isinstance(v, str) for v in val.values()) else "mixed")
        n_pairs = 0
        for k, v in val.items():
            if direction == "canonical->aliases":
                canon, aliases = str(k), [str(a) for a in v]
            elif direction == "alias->canonical":
                canon, aliases = str(v), [str(k)]
            else:
                continue
            ck = _ckey(canon)
            variants[ns][ck].add(canon)
            for a in aliases:
                if _ckey(a) == ck:
                    continue                                   # 別名就是正典自己的另一種拼法,不算別名
                ns_map[ns][ck].add(a)
                alias_owner[(ns, _norm(a))].add(ck)
                n_pairs += 1
        sources.append({"file": r["file"], "line": r["line"], "name": name, "namespace": ns, "direction": direction, "pairs": n_pairs})
    conflicts = [{"namespace": ns, "alias": a, "canonicals": sorted(c)} for (ns, a), c in alias_owner.items() if len(c) > 1]
    additive = {ns: {c: {"spellings": sorted(variants[ns][c]), "aliases": sorted(al)} for c, al in sorted(m.items())} for ns, m in ns_map.items()}
    multi_spelling = {ns: {c: sorted(v) for c, v in m.items() if len(v) > 1} for ns, m in variants.items()}
    multi_spelling = {ns: m for ns, m in multi_spelling.items() if m}
    syn_book = {"book_id": "GHP-10", "name": "VIA_GHP_SynonymUnion", "version": "v0100", "head": idx["head"], "at": now,
                "rule": "只增不衝突:同命名空間同一別名只能指向一個正典(正典鍵正規化後比對,拼法差異另列 canonical_spelling_variants);衝突照列由操作員裁,不自動改任何一邊;本冊是提案,正本仍在各引擎與 CGC_MDL176",
                "namespaces": {ns: {"canonicals": len(m), "aliases": sum(len(v) for v in m.values())} for ns, m in ns_map.items()},
                "additive": additive, "conflicts": conflicts, "canonical_spelling_variants": multi_spelling, "sources": sources, "skipped": skipped,
                "lamp": "RED" if conflicts else "GREEN"}

    # ---- ② 正則聯集 ----
    clusters: dict[str, dict] = {}
    for r in rx_rows:
        pat = r["pattern"]
        c = clusters.setdefault(pat, {"pattern": pat, "files": set(), "hits": 0, "flags": set()})
        c["files"].add(r["file"]); c["hits"] += 1
        if r.get("flags"):
            c["flags"].add(r["flags"])
    central = ""
    reg = repo / "VeritasIntelligenceAnalytics" / "supportive modules" / "registry"
    cands = sorted(reg.glob("VIA_Central_Synonym_Regex_v*.json")) if reg.is_dir() else []
    if cands:
        central = cands[-1].read_text(encoding="utf-8", errors="replace")
    rows = []
    for pat, c in clusters.items():
        fam = next((f for f, rx in FAMILY_RX if rx.search(pat)), "other")
        in_central = bool(central) and (pat in central or pat.replace("\\", "\\\\") in central)
        rows.append({"id": "RX-" + fam.upper()[:4] + "-" + ("%04d" % (len(rows) + 1)), "family": fam, "pattern": pat, "files": len(c["files"]), "hits": c["hits"],
                     "flags": sorted(c["flags"])[:3], "in_central_book": in_central, "sample_files": sorted(os.path.basename(f) for f in c["files"])[:4],
                     "proposal": ("已在中央冊" if in_central else ("候選入冊(≥2 檔共用)" if len(c["files"]) >= 2 else "單檔自用,不入冊"))})
    rows.sort(key=lambda r: (-r["files"], -r["hits"]))
    fam_count = collections.Counter(r["family"] for r in rows)
    rx_book = {"book_id": "GHP-11", "name": "VIA_GHP_RegexUnion", "version": "v0100", "head": idx["head"], "at": now,
               "rule": "依樣式字串精確分群;候選入冊 = 不在 VIA_Central_Synonym_Regex 尾版且 ≥2 檔共用;只提案不改引擎(引擎改用冊上同一句要各自出新版號)",
               "central_book": cands[-1].name if cands else "", "literals": len(rx_rows), "clusters": len(rows), "families": dict(fam_count),
               "candidates": sum(1 for r in rows if r["proposal"].startswith("候選")), "rows": rows}

    # ---- ③ 冊去重 / 空冊 / 沒版號 ----
    by_sha = collections.defaultdict(list)
    for r in bk_rows:
        by_sha[r["sha16"]].append(r["file"])
    dups = []
    for sha, files in by_sha.items():
        if len(files) > 1:
            canon = sorted(files, key=lambda f: (bool(re.search(r"_sha[0-9a-f]{6,}", f)), len(f)))[0]
            dups.append({"sha16": sha, "keep": canon, "copies": [f for f in files if f != canon], "n": len(files)})
    empty = [r["file"] for r in bk_rows if r["keys"] == 0 and r["state"] == "OK"]
    unversioned = [r["file"] for r in bk_rows if not r["version"]]
    broken = [{"file": r["file"], "state": r["state"]} for r in bk_rows if r["state"] != "OK"]
    bk_book = {"book_id": "GHP-12", "name": "VIA_GHP_BookDedup", "version": "v0100", "head": idx["head"], "at": now,
               "rule": "sha16 相同 = 位元組相同的副本:建議留正本(非 _sha 名、較短名),副本進名冊不刪;空冊與沒版號只列;BOM / BROKEN 修好的副本由操作員裁定要不要出新版",
               "books": len(bk_rows), "duplicate_groups": len(dups), "duplicate_files": sum(d["n"] - 1 for d in dups),
               "empty": empty, "unversioned_n": len(unversioned), "unversioned": unversioned[:200], "broken": broken, "duplicates": dups}

    out_dir.mkdir(parents=True, exist_ok=True)
    for b in (syn_book, rx_book, bk_book):
        (out_dir / f"{b['name']}_v0100.json").write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    if promote:
        for b in (syn_book, rx_book, bk_book):
            existing = sorted(reg.glob(b["name"] + "_v*.json"))
            nxt = (int(re.search(r"_v(\d{4})", existing[-1].name).group(1)) + 1) if existing else 100
            (reg / f"{b['name']}_v{nxt:04d}.json").write_bytes((out_dir / f"{b['name']}_v0100.json").read_bytes())
    summary = {"synonyms": {"namespaces": syn_book["namespaces"], "conflicts": len(conflicts), "skipped": len(skipped), "lamp": syn_book["lamp"]},
               "regex": {"literals": len(rx_rows), "clusters": len(rows), "candidates": rx_book["candidates"], "families": dict(fam_count)},
               "books": {"duplicate_groups": len(dups), "duplicate_files": bk_book["duplicate_files"], "empty": len(empty), "unversioned": len(unversioned), "broken": len(broken)}}
    (out_dir / "UNION_latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


def selftest() -> int:
    rc_prior = PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        reg = repo / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "XX_MDL001_A_v0100.py").write_text("# ===== [VIA:ACCEL-BRIDGE:v0100]\nimport re\nBROKER_ALIAS_TABLE={'MQ':'MACQUARIE','GS':'GOLDMAN'}\nRATING_SYNONYMS={'BUY':['買進','Buy'],'SELL':['賣出']}\nRX=re.compile(r'[1-9]\\d{3}')\n", encoding="utf-8")
        (reg / "XX_MDL002_B_v0100.py").write_text("# ===== [VIA:ACCEL-BRIDGE:v0100]\nimport re\nBROKER_ALIAS_EXTENSION={'MQ':'MACQ'}\nCOMPANY_ALIAS_DICT={'2330':['台積電','TSMC']}\nRX2=re.compile(r'[1-9]\\d{3}')\nCOMMON_ALIASES={'ls':'Get-ChildItem'}\n", encoding="utf-8")
        (reg / "VIA_B_v0100.json").write_text('{"a":1}', encoding="utf-8")
        (reg / "VIA_B_v0100_shaaaaaaaaa.json").write_text('{"a":1}', encoding="utf-8")
        (reg / "VIA_Empty.json").write_text("{}", encoding="utf-8")
        out = repo / "VIA_Reports" / "github_panorama"
        s = union(repo, None, out, promote=False)
        syn = json.loads((out / "VIA_GHP_SynonymUnion_v0100.json").read_text(encoding="utf-8"))
        chk("① 同義字:方向自動判(str 值 = 別名→正典;list 值 = 正典→別名)· 命名空間分對", "broker" in syn["additive"] and "rating" in syn["additive"] and "company" in syn["additive"])
        chk("② 衝突:broker 命名空間 MQ 指向 MACQUARIE 與 MACQ 兩個正典 → CONFLICT 照列不裁", s["synonyms"]["conflicts"] == 1 and syn["conflicts"][0]["alias"] == "mq")
        chk("③ 排除:COMMON_ALIASES(PS 別名)不入同義字冊", any(x["name"] == "COMMON_ALIASES" for x in syn["skipped"]))
        rx = json.loads((out / "VIA_GHP_RegexUnion_v0100.json").read_text(encoding="utf-8"))
        chk("④ 正則:同一句跨兩檔 = 一群 · 家族 ticker · 候選入冊", rx["clusters"] == 1 and rx["rows"][0]["files"] == 2 and rx["rows"][0]["family"] == "ticker" and rx["candidates"] == 1)
        bk = json.loads((out / "VIA_GHP_BookDedup_v0100.json").read_text(encoding="utf-8"))
        chk("⑤ 冊:sha 副本與正本位元組相同 → 一群,留非 _sha 名 · 空冊抓到", bk["duplicate_groups"] == 1 and not re.search(r"_sha", bk["duplicates"][0]["keep"]) and len(bk["empty"]) == 1)
        chk("⑥ 三本冊各自冊號 GHP-10/11/12 · 只讀(registry 沒多出檔)", syn["book_id"] == "GHP-10" and rx["book_id"] == "GHP-11" and bk["book_id"] == "GHP-12" and not list(reg.glob("VIA_GHP_*")))
    ok = rc_prior == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if a and a[0] == "union":
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
            return 2
        ref = a[a.index("--ref") + 1] if "--ref" in a else "origin/main"
        repo = Path(a[a.index("--repo") + 1]) if "--repo" in a else PRIOR.VIA.parent
        out = PRIOR.VIA / "VIA_Reports" / "github_panorama"
        s = union(repo, None if ref in ("worktree", "") else ref, out, promote="--promote" in a)
        print("[GitHub 聯集] 同義字 " + s["synonyms"]["lamp"] + " · 命名空間 " + ",".join(f"{k}:{v['canonicals']}/{v['aliases']}" for k, v in s["synonyms"]["namespaces"].items())
              + f" · 衝突 {s['synonyms']['conflicts']} · 跳過 {s['synonyms']['skipped']} | 正則 {s['regex']['literals']} 條 → {s['regex']['clusters']} 群 · 候選入冊 {s['regex']['candidates']}"
              + f" | 冊 副本群 {s['books']['duplicate_groups']}(副本 {s['books']['duplicate_files']})· 空冊 {s['books']['empty']} · 沒版號 {s['books']['unversioned']} · 壞 {s['books']['broken']}")
        print(f"  三本冊 → {out}\\VIA_GHP_SynonymUnion_v0100.json · VIA_GHP_RegexUnion_v0100.json · VIA_GHP_BookDedup_v0100.json")
        return 0 if s["synonyms"]["conflicts"] == 0 else 2
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

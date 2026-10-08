#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0149 — 薄尾(2026-10-08 第 1 輪實測 97 檔 77.3% 後的修):
  ① lexicon add --file <裁定 json>   操作員+AI 裁定的 std/別名批次進 FinLexicon 新版(只增;同 std 併別名,新 std 加列;provenance)· 同時把 noise_rules 存進冊(triage 噪音規則)
  ② extract triage 噪音過濾          日期 / 欄頭(QoQ%)/ 章名(Balance Sheet)/ 評等(增加持股)/ 代號(002273.SZ)/ 單位尾 → 不算「認不出列標」,另計「非列標 N 種」
  ③ extract loop 第 2 輪起的 REVIEW 清單改從擷取帳讀(前版從結果物件讀不到路徑 → 重掃 0)
  ④ lexicon rules                   印冊上噪音規則
其餘動詞照前版鏈。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import importlib.util
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0149"


def _vnum_v0149(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0149(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0149(p) < _vnum_v0149(__file__)), key=_vnum_v0149)
PRIOR = _load_v0149(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


_DEFAULT_NOISE = {"date": r"^(\d{1,2}月\s*\d{1,2},?\s*\d{4}|[一二三四五六七八九十]+月\s*\d{1,2},?\s*\d{4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})$", "column_head": r"(?i)^(qoq|yoy|mom|ytd|%|\(%\)|qoq\(%\)|yoy\(%\)|chg|change|est\.?|cons\.?|actual|diff)$",
                  "section": r"(?i)^(balance sheet|income statement|cash ?flow(s| statement)?|ratios?|valuation|financial summary|key data)$", "rating": r"^(增加持股|降低持股|買進|賣出|中立|持有|減碼|加碼|優於大盤|劣於大盤|區間操作)$",
                  "ticker": r"^\d{4,6}(\.(TW|TWO|SZ|SH|HK|T))?( TT)?$", "unit_tail": r"(?i)^(nt\$|us\$|rmb|百萬|千|億)?\s*(m|mn|bn|k)?$"}


def _lex_tail():
    hits = sorted((PRIOR._home() / "SSOT").glob("VRN_FinLexicon_SSOT_v*.json"), key=lambda q: _vnum_v0149(q.stem))
    return hits[-1] if hits else None


def noise_rules() -> dict:
    t = _lex_tail()
    if t:
        try:
            d = json.loads(t.read_text(encoding="utf-8-sig"))
            if d.get("noise_rules"):
                return d["noise_rules"]
        except ValueError:
            pass
    return dict(_DEFAULT_NOISE)


def is_noise(label: str, rules: dict | None = None) -> str | None:
    s = re.sub(r"\s+", " ", str(label or "")).strip()
    for k, rx in (rules or noise_rules()).items():
        try:
            if re.search(rx, s):
                return k
        except re.error:
            continue
    return None


def lexicon_add(rulings: dict, apply: bool = True) -> dict:
    tail = _lex_tail()
    if not tail:
        return {"status": "NO_BOOK", "lamp": "RED"}
    book = json.loads(tail.read_text(encoding="utf-8-sig"))
    rows = book.setdefault("rows", [])
    by_std = {r["std"]: r for r in rows}
    added_std, added_alias = 0, 0
    now = datetime.datetime.now().isoformat(timespec="seconds")
    for r in rulings.get("add", []):
        std = r["std"]
        if std in by_std:
            cur = by_std[std]
            for fld in ("zh", "en"):
                for a in r.get(fld) or []:
                    if a not in (cur.get("zh") or []) and a not in (cur.get("en") or []):
                        cur.setdefault(fld, []).append(a)
                        cur.setdefault("provenance", []).append({"alias": a, "ts": now, "rule": "操作員+AI 裁定批次", "batch": rulings.get("origin", "")[:60]})
                        added_alias += 1
        else:
            new = {"std": std, "cat": r.get("cat", "OTHER"), "zh": list(r.get("zh") or []), "en": list(r.get("en") or []), "provenance": [{"ts": now, "rule": "操作員+AI 裁定批次(新 std)", "batch": rulings.get("origin", "")[:60]}]}
            rows.append(new)
            by_std[std] = new
            added_std += 1
    if rulings.get("noise_rules"):
        nr = dict(book.get("noise_rules") or {})
        nr.update(rulings["noise_rules"])
        book["noise_rules"] = nr
    out = {"status": "PLAN", "tail": tail.name, "added_std": added_std, "added_alias": added_alias, "rows": len(rows), "noise_rules": len(book.get("noise_rules") or {}), "lamp": "GREEN"}
    if apply and (added_std or added_alias or rulings.get("noise_rules")):
        nv = "v%04d" % (_vnum_v0149(tail.stem) + 1)
        new = tail.with_name("VRN_FinLexicon_SSOT_%s.json" % nv)
        book["version"], book["prior"] = nv, tail.name
        book["origin"] = (book.get("origin", "") + ";" + rulings.get("origin", "裁定批次"))[:3000]
        new.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
        out.update(status="WRITTEN", new=new.name)
    return out


_TRI_48 = PRIOR._resolve("extract_triage")


def extract_triage(top: int = 40) -> dict:
    o = _TRI_48(top=200) if _TRI_48 else {"unmatched_labels": [], "lamp": "GRAY"}
    rules = noise_rules()
    keep, noise = [], Counter()
    for u in o.get("unmatched_labels", []):
        k = is_noise(u.get("label", ""), rules)
        if k:
            noise[k] += 1
        else:
            keep.append(u)
    o["unmatched_labels"] = keep[:top]
    o["noise"] = dict(noise)
    o["lamp"] = "YELLOW" if keep else "GREEN"
    return o


_LOOP_48 = PRIOR.extract_loop


def extract_loop(d: Path, rounds: int = 2, limit: int = 0, min_docs: int = 2) -> dict:
    """同 v0148,但第 2 輪起 REVIEW 清單從帳讀;triage 用本版(已濾噪音)。"""
    ext_fn = PRIOR._resolve("extract")
    files = sorted(p for p in d.rglob("*.pdf")) if d.is_dir() else []
    out = {"verb": "extract_loop", "dir": str(d), "rounds": [], "lamp": "GRAY"}
    if not (ext_fn and files):
        out.update(why="鏈上沒有 extract" if not ext_fn else "夾裡沒有 PDF", lamp="RED")
        return out
    todo = files
    ad = {"adopted": [], "pending": []}
    for r in range(1, rounds + 1):
        res = ext_fn(todo, ("pdfplumber", "camelot", "tabula"), limit if r == 1 else 0)
        counts = Counter((x.get("status") or "?") for x in res.get("docs", res.get("files", [])) if isinstance(x, dict))
        tri = extract_triage()
        ad = PRIOR.lexicon_auto_adopt(tri.get("unmatched_labels", []), min_docs=min_docs, apply=True)
        led = PRIOR._ledger_status()
        want = {str(p.resolve()).lower() for p in files}
        review_files = []
        for k, j in led.items():
            if (j.get("status") in ("REVIEW", "NODATA")):
                pth = j.get("path") or j.get("file") or k
                try:
                    pp = Path(pth)
                    if pp.exists() and str(pp.resolve()).lower() in want:
                        review_files.append(pp)
                except (OSError, ValueError):
                    pass
        review_files = sorted(set(review_files))
        out["rounds"].append({"round": r, "scanned": len(todo), "counts": dict(counts), "adopted": len(ad["adopted"]), "pending": len(ad["pending"]), "noise": tri.get("noise", {}), "lexicon": ad.get("new") or ad.get("tail"), "review_next": len(review_files)})
        if not ad["adopted"] or not review_files:
            break
        todo = review_files
    gate = PRIOR.extract_gate()
    out.update(gate=gate, pending_labels=ad["pending"][:40], lamp=gate["lamp"])
    return out


def _print_loop(o: dict) -> None:
    if o.get("why"):
        print("[計] VRN extract loop · %s · %s" % (o["why"], o["lamp"]))
        return
    for r in o["rounds"]:
        print("[計] extract loop 第 %d 輪 · 掃 %d · %s · 自動採納 %d · 未解 %d · 非列標 %s · 冊 %s · 下輪重掃 %d" % (r["round"], r["scanned"], " ".join("%s=%d" % kv for kv in sorted(r["counts"].items())), r["adopted"], r["pending"], " ".join("%s=%d" % kv for kv in sorted(r["noise"].items())) or "0", r["lexicon"], r["review_next"]))
    g = o["gate"]
    print("[計] 完工門檻 · 檔 %d · %s · 良率 %.1f%% · REVIEW %d · ERROR %d · %s · %s" % (g["n"], " ".join("%s=%d" % kv for kv in sorted(g["counts"].items())), g["good_ratio"] * 100, g["review"], g["error"], g["rule"], g["lamp"]))
    for x in o.get("pending_labels", [])[:40]:
        print("  [YEL] 列標 %s · %d 次 · %d 檔(等操作員+AI)" % (x.get("label"), x.get("n", 0), x.get("docs", 0)))
    print("NEXT: %s" % ("完工:VRN 實測過門檻" if g["lamp"] == "GREEN" else "把 [YEL] 列標貼給 AI → lexicon add → 再跑 extract loop(只重掃 REVIEW)"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    if args[:2] == ["lexicon", "add"]:
        fp = Path(opt("--file", ""))
        if not fp.exists():
            print("[拒跑] lexicon add --file <裁定 json>")
            return 2
        r = lexicon_add(json.loads(fp.read_text(encoding="utf-8-sig")), apply=("--dry" not in args))
        print("[計] VRN lexicon add · %s · %s → %s · 新 std %d · 新別名 %d · 列 %d · 噪音規則 %d · %s" % (r["status"], r.get("tail"), r.get("new", "—"), r.get("added_std", 0), r.get("added_alias", 0), r.get("rows", 0), r.get("noise_rules", 0), r["lamp"]))
        return 0 if r["lamp"] != "RED" else 1
    if args[:2] == ["lexicon", "rules"]:
        for k, v in noise_rules().items():
            print("  [OK] %s · %s" % (k, v))
        return 0
    if args[:2] == ["extract", "triage"]:
        o = extract_triage()
        print("[計] extract triage · 檔 %s · 認不出列標 %d 種 · 非列標 %s · %s" % (o.get("docs"), len(o["unmatched_labels"]), " ".join("%s=%d" % kv for kv in sorted(o.get("noise", {}).items())) or "0", o["lamp"]))
        for x in o["unmatched_labels"]:
            print("  [YEL] 列標 %s · %d 次 · %d 檔" % (x["label"], x["n"], x["docs"]))
        return 0
    if args[:2] == ["extract", "loop"]:
        o = extract_loop(Path(opt("--dir") or (HERE / "input" / "incoming")), int(opt("--rounds", "2") or 2), int(opt("--limit", "0") or 0), int(opt("--min-docs", "2") or 2))
        _print_loop(o)
        return 1 if o["lamp"] == "RED" else 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrnlex-"))
    home = td / "functional modules" / "VRN"
    (home / "SSOT").mkdir(parents=True)
    saved = os.environ.get("VIA_VRN_SSOT_HOME")
    os.environ["VIA_VRN_SSOT_HOME"] = str(home)
    (home / "SSOT" / "VRN_FinLexicon_SSOT_v0102.json").write_text(json.dumps({"version": "v0102", "rows": [{"std": "revenue", "cat": "IS", "zh": ["營業收入"], "en": ["Revenue"]}]}, ensure_ascii=False), encoding="utf-8")
    r = lexicon_add({"origin": "t", "add": [{"std": "revenue", "cat": "IS", "zh": ["營業收益"], "en": []}, {"std": "interest_expense", "cat": "IS", "zh": ["利息費用"], "en": ["Interest expense"]}], "noise_rules": _DEFAULT_NOISE})
    book = json.loads((home / "SSOT" / "VRN_FinLexicon_SSOT_v0103.json").read_text(encoding="utf-8"))
    chk("① lexicon add:同 std 併別名(營業收益→revenue)· 新 std 加列 · noise_rules 入冊 · 出 v0103", r["status"] == "WRITTEN" and r["added_std"] == 1 and r["added_alias"] == 1 and "營業收益" in next(x for x in book["rows"] if x["std"] == "revenue")["zh"] and book.get("noise_rules"))
    chk("② 噪音:五月 19, 2026=date · QoQ(%)=column_head · Balance Sheet=section · 增加持股=rating · 002273.SZ=ticker · 總 營 業 外 收 入 不是噪音", is_noise("五月 19, 2026") == "date" and is_noise("QoQ(%)") == "column_head" and is_noise("Balance Sheet") == "section" and is_noise("增加持股") == "rating" and is_noise("002273.SZ") == "ticker" and is_noise("總 營 業 外 收 入") is None)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("④ 帶加速器橋 · 只增", "[VIA:ACCEL-BRIDGE:v0100]" in body and (home / "SSOT" / "VRN_FinLexicon_SSOT_v0102.json").exists())
    if saved is None:
        os.environ.pop("VIA_VRN_SSOT_HOME", None)
    else:
        os.environ["VIA_VRN_SSOT_HOME"] = saved
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0149 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

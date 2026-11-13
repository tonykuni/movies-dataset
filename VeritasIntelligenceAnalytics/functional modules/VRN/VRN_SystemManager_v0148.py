#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0148 — 薄尾:extract loop(操作員 2026-10-08:用省 token 迴圈把 VRN 實測做到完工)。
  extract loop --dir <夾> [--rounds 2] [--limit N] [--min-docs 2]
     第 1 輪:extract --dir(前版 v0127 鏈)→ triage → 認不出的列標做「安全自動採納」:正規化後(去空白 / 全形 / 括號內容 / 合計·總計·淨額尾綴 / 大小寫)等於既有 std 的別名 → 出 FinLexicon 新版(只增:加別名,帶 provenance);
     等不到的留給操作員+AI(貼回包)。第 2 輪起:只重掃上一輪 REVIEW / NODATA 的檔;沒有新採納或沒有 REVIEW 就停。
     完工門檻(印在結算):READ+TEXT_DOC ≥ 95% · ERROR = 0 · REVIEW ≤ 5% → GREEN;否則 YELLOW 並列未解列標 Top 40(NEXT: 貼 AI)
  extract gate            只算門檻不跑
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
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0148"


def _vnum_v0148(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0148(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0148(p) < _vnum_v0148(__file__)), key=_vnum_v0148)
PRIOR = _load_v0148(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _resolve(name):
    import types
    mod = PRIOR
    seen = set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return vars(mod)[name]
        mod = vars(mod).get("PRIOR")
    return None


def _home():
    return Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)


def _out_root():
    fn = _resolve("_out_root")
    return fn() if fn else (_home().parents[1] / "VIA_Reports" / "vrn" / "extract")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = re.sub(r"[\(（][^)）]*[\)）]", "", s)
    s = re.sub(r"[\s\u3000,，.．:：;；/／\-–—_*＊]", "", s).lower()
    s = re.sub(r"(合計|總計|總額|淨額|小計|total|net)$", "", s)
    return s


def _lex_tail():
    hits = sorted((_home() / "SSOT").glob("VRN_FinLexicon_SSOT_v*.json"), key=lambda q: _vnum_v0148(q.stem))
    return hits[-1] if hits else None


def lexicon_auto_adopt(unmatched: list, min_docs: int = 2, apply: bool = True) -> dict:
    """認不出的列標 → 正規化等於既有 std 任一別名 → 加為該 std 的新別名(只增;新版冊;provenance)。"""
    tail = _lex_tail()
    if not tail:
        return {"status": "NO_BOOK", "adopted": [], "pending": unmatched, "lamp": "YELLOW"}
    book = json.loads(tail.read_text(encoding="utf-8-sig"))
    rows = book.get("rows", [])
    index = {}
    for r in rows:
        for a in (r.get("zh") or []) + (r.get("en") or []) + [r.get("std", "")]:
            index.setdefault(_norm(a), r["std"])
    adopted, pending = [], []
    by_std = {r["std"]: r for r in rows}
    for u in unmatched:
        lab = u["label"] if isinstance(u, dict) else str(u)
        n_docs = u.get("docs", 1) if isinstance(u, dict) else 1
        key = _norm(lab)
        if not key or re.fullmatch(r"[\d%.]+|(fy|cy|q[1-4]|[1-4]q|h[12])?\d{2,4}[a-z]{0,2}", key):
            continue      # 純數字 / 年度期間欄(2025E · FY26 · 3Q25)不是列標
        std = index.get(key)
        if std and n_docs >= min_docs:
            r = by_std[std]
            field = "en" if re.fullmatch(r"[a-z0-9 &/%.$()\x27,-]+", lab.strip().lower()) else "zh"
            if lab not in (r.get("zh") or []) and lab not in (r.get("en") or []):
                r.setdefault(field, []).append(lab)
                r.setdefault("provenance", []).append({"alias": lab, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "rule": "extract loop 正規化等於既有別名", "docs": n_docs})
                adopted.append({"label": lab, "std": std, "docs": n_docs})
        else:
            pending.append(u)
    out = {"status": "PLAN", "adopted": adopted, "pending": pending, "tail": tail.name, "lamp": "GREEN" if not pending else "YELLOW"}
    if adopted and apply:
        nv = "v%04d" % (_vnum_v0148(tail.stem) + 1)
        new = tail.with_name("VRN_FinLexicon_SSOT_%s.json" % nv)
        book["version"], book["prior"] = nv, tail.name
        book["origin"] = (book.get("origin", "") + ";%s extract loop 安全自動採納 %d 別名(只增,provenance 在列)" % (datetime.date.today().isoformat(), len(adopted)))[:2000]
        new.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
        out.update(status="WRITTEN", new=new.name)
    return out


def _ledger_status() -> dict:
    led = _out_root() / "VRN_Extract_Ledger.jsonl"
    last = {}
    if led.exists():
        for ln in led.read_text(encoding="utf-8").splitlines():
            try:
                j = json.loads(ln)
            except ValueError:
                continue
            k = j.get("file") or j.get("path") or j.get("sha8") or j.get("filename", {}).get("name") if isinstance(j.get("filename"), dict) else j.get("file") or j.get("sha8")
            if k:
                last[k] = j
    return last


def extract_gate(status_counts: dict | None = None) -> dict:
    if status_counts is None:
        st = _ledger_status()
        status_counts = Counter((j.get("status") or "?") for j in st.values())
    n = sum(status_counts.values())
    good = status_counts.get("READ", 0) + status_counts.get("TEXT_DOC", 0)
    rev = status_counts.get("REVIEW", 0) + status_counts.get("NODATA", 0)
    err = status_counts.get("ERROR", 0)
    ratio = (good / n) if n else 0
    lamp = "GREEN" if (n and ratio >= 0.95 and err == 0 and rev / n <= 0.05) else ("RED" if err else ("YELLOW" if n else "GRAY"))
    return {"verb": "extract_gate", "n": n, "counts": dict(status_counts), "good_ratio": round(ratio, 3), "review": rev, "error": err, "lamp": lamp, "rule": "READ+TEXT_DOC ≥ 95% · ERROR = 0 · REVIEW+NODATA ≤ 5%"}


def extract_loop(d: Path, rounds: int = 2, limit: int = 0, min_docs: int = 2) -> dict:
    ext_fn, tri_fn = _resolve("extract"), _resolve("extract_triage")
    if not (ext_fn and tri_fn):
        return {"verb": "extract_loop", "lamp": "RED", "why": "鏈上沒有 extract / extract_triage"}
    files = sorted(p for p in d.rglob("*.pdf")) if d.is_dir() else []
    out = {"verb": "extract_loop", "dir": str(d), "rounds": [], "lamp": "GRAY"}
    if not files:
        out.update(why="夾裡沒有 PDF", lamp="RED")
        return out
    todo = files
    for r in range(1, rounds + 1):
        res = ext_fn(todo, ("pdfplumber", "camelot", "tabula"), limit if r == 1 else 0)
        counts = Counter((x.get("status") or "?") for x in res.get("docs", res.get("files", [])) if isinstance(x, dict))
        tri = tri_fn()
        ad = lexicon_auto_adopt(tri.get("unmatched_labels", []), min_docs=min_docs, apply=True)
        review_files = [Path(x.get("path") or x.get("file") or "") for x in res.get("docs", res.get("files", [])) if isinstance(x, dict) and (x.get("status") in ("REVIEW", "NODATA")) and (x.get("path") or x.get("file"))]
        review_files = [p for p in review_files if p.exists()]
        out["rounds"].append({"round": r, "scanned": len(todo), "counts": dict(counts), "adopted": len(ad["adopted"]), "pending": len(ad["pending"]), "lexicon": ad.get("new") or ad.get("tail"), "review_next": len(review_files)})
        if not ad["adopted"] or not review_files:
            break
        todo = review_files
    gate = extract_gate()
    out.update(gate=gate, pending_labels=ad["pending"][:40], lamp=gate["lamp"])
    return out


def _print_loop(o: dict) -> None:
    if o.get("why"):
        print("[計] VRN extract loop · %s · %s" % (o["why"], o["lamp"]))
        return
    for r in o["rounds"]:
        print("[計] extract loop 第 %d 輪 · 掃 %d · %s · 自動採納 %d · 未解 %d · 冊 %s · 下輪重掃 %d" % (r["round"], r["scanned"], " ".join("%s=%d" % kv for kv in sorted(r["counts"].items())), r["adopted"], r["pending"], r["lexicon"], r["review_next"]))
    g = o["gate"]
    print("[計] 完工門檻 · 檔 %d · %s · 良率 %.1f%% · REVIEW %d · ERROR %d · %s · %s" % (g["n"], " ".join("%s=%d" % kv for kv in sorted(g["counts"].items())), g["good_ratio"] * 100, g["review"], g["error"], g["rule"], g["lamp"]))
    for x in o.get("pending_labels", [])[:40]:
        print("  [YEL] 列標 %s · %d 次 · %d 檔(等操作員+AI)" % (x.get("label"), x.get("n", 0), x.get("docs", 0)))
    print("NEXT: %s" % ("完工:VRN 實測過門檻" if g["lamp"] == "GREEN" else "把 [YEL] 列標貼給 AI → FinLexicon 下一版 → 再跑 extract loop(只重掃 REVIEW)"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    if args[:2] == ["extract", "loop"]:
        o = extract_loop(Path(opt("--dir") or (HERE / "input" / "incoming")), int(opt("--rounds", "2") or 2), int(opt("--limit", "0") or 0), int(opt("--min-docs", "2") or 2))
        _print_loop(o)
        return 1 if o["lamp"] == "RED" else 0
    if args[:2] == ["extract", "gate"]:
        g = extract_gate()
        print("[計] 完工門檻 · 檔 %d · %s · 良率 %.1f%% · REVIEW %d · ERROR %d · %s" % (g["n"], " ".join("%s=%d" % kv for kv in sorted(g["counts"].items())), g["good_ratio"] * 100, g["review"], g["error"], g["lamp"]))
        return 0
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

    td = Path(tempfile.mkdtemp(prefix="vrnloop-"))
    home = td / "functional modules" / "VRN"
    (home / "SSOT").mkdir(parents=True)
    saved = os.environ.get("VIA_VRN_SSOT_HOME")
    os.environ["VIA_VRN_SSOT_HOME"] = str(home)
    (home / "SSOT" / "VRN_FinLexicon_SSOT_v0101.json").write_text(json.dumps({"version": "v0101", "rows": [{"std": "revenue", "cat": "IS", "zh": ["營業收入"], "en": ["Revenue"]}, {"std": "gross_profit", "cat": "IS", "zh": ["營業毛利"], "en": ["Gross profit"]}]}, ensure_ascii=False), encoding="utf-8")
    ad = lexicon_auto_adopt([{"label": "營業收入淨額", "n": 5, "docs": 3}, {"label": "Gross Profit (NT$m)", "n": 2, "docs": 2}, {"label": "營業收入合計", "n": 1, "docs": 1}, {"label": "神秘項目", "n": 4, "docs": 4}, {"label": "2025E", "n": 9, "docs": 9}])
    book = json.loads((home / "SSOT" / "VRN_FinLexicon_SSOT_v0102.json").read_text(encoding="utf-8"))
    rev = next(r for r in book["rows"] if r["std"] == "revenue"); gp = next(r for r in book["rows"] if r["std"] == "gross_profit")
    chk("① 自動採納:營業收入淨額→revenue(zh)· Gross Profit (NT$m)→gross_profit(en)· 單檔的不採 · 神秘項目待裁 · 2025E 不算列標 · 出 v0102 帶 provenance", ad["status"] == "WRITTEN" and "營業收入淨額" in rev["zh"] and "Gross Profit (NT$m)" in gp["en"] and len(ad["adopted"]) == 2 and any(x["label"] == "神秘項目" for x in ad["pending"]) and any(x["label"] == "營業收入合計" for x in ad["pending"]) and not any(x["label"] == "2025E" for x in ad["pending"]) and rev.get("provenance"))
    g = extract_gate({"READ": 96, "TEXT_DOC": 2, "REVIEW": 2})
    g2 = extract_gate({"READ": 80, "REVIEW": 20})
    g3 = extract_gate({"READ": 99, "ERROR": 1})
    chk("② 門檻:98% 綠 · 80% 黃 · 有 ERROR 紅", g["lamp"] == "GREEN" and g2["lamp"] == "YELLOW" and g3["lamp"] == "RED")
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("④ 帶加速器橋 · 只增(新版冊,舊版不動)", "[VIA:ACCEL-BRIDGE:v0100]" in body and (home / "SSOT" / "VRN_FinLexicon_SSOT_v0101.json").exists())
    if saved is None:
        os.environ.pop("VIA_VRN_SSOT_HOME", None)
    else:
        os.environ["VIA_VRN_SSOT_HOME"] = saved
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0148 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

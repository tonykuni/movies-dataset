#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0152 — 薄尾:尺量對(操作員 2026-10-10 驗收第 1 輪:62/13/21/1 字典多 24 條零變動 → 21 個 REVIEW 是沒有財務三表的文件,不是列標問題)。
  ① extract classify     把帳上 REVIEW 的檔分兩種(只增:新帳列 status 改判,帶 why 與依據):
        NONFIN_OK  非個股報告(檔名無四碼代號)且所有表類別 OTHER / 無表 → 正常(策略 · 產業 · 晨會 · ETF 追蹤 · 論壇簡報本來就沒三表)
        REVIEW     個股報告(檔名有代號)但三表認不出 → 真的要字典 / 版面
  ② extract gate / loop  NONFIN_OK 與 TEXT_DOC 同計「良」;門檻不變(READ+TEXT_DOC+NONFIN_OK ≥ 95% · ERROR 0 · 待審 ≤ 5%)
  ③ extract loop         第 2 輪只重掃仍是 REVIEW 的檔 — 用檔名對(帳存檔名不存路徑,前版路徑比對永遠 0)
  ④ extract review       列出仍 REVIEW 的檔:why · 代號 · 表數 · 類別分布(貼給 AI 的就是這份)
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
TAG = "v0152"


def _vnum_v0152(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0152(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0152(p) < _vnum_v0152(__file__)), key=_vnum_v0152)
PRIOR = _load_v0152(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _resolve(name):
    """從本版的 PRIOR 往下走整條鏈找(v0148 的 _resolve 只從 v0147 起找,看不到 v0148+ 的 lexicon_add / lexicon_auto_adopt / 新 triage)。"""
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return vars(mod)[name]
        mod = vars(mod).get("PRIOR")
    return None


def _out_root():
    fn = _resolve("_out_root")
    return fn() if fn else (Path(os.environ.get("VIA_VRN_EXTRACT_OUT") or (HERE.parents[1] / "VIA_Reports" / "vrn" / "extract")))


def _ledger_last() -> dict:
    led = _out_root() / "VRN_Extract_Ledger.jsonl"
    last = {}
    if led.exists():
        for ln in led.read_text(encoding="utf-8").splitlines():
            try:
                j = json.loads(ln)
            except ValueError:
                continue
            k = j.get("file")
            if k:
                last[k] = j
    return last


def _append(rec: dict) -> None:
    led = _out_root() / "VRN_Extract_Ledger.jsonl"
    led.parent.mkdir(parents=True, exist_ok=True)
    with led.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(rec, ts=datetime.datetime.now().isoformat(timespec="seconds")), ensure_ascii=False) + "\n")


_TK_RX = re.compile(r"(?:^|[\s\-_(（,])([1-9]\d{3})(?=TT|[\s\-_)）,.]|$)")
_NONSTOCK_RX = re.compile(r"(?i)(早報|晨會|晨間|解盤|盤勢|盤後|專題|論壇|趨勢|展望|總經|ETF|週報|周報|市場觀察|日股|美股|港股|期貨|產業|策略|散熱|功耗|Databook|Summit|Insights|Hardware|Thermal|Memory|PCB|CCL|ABF|Automation|Power|TPU|Components|Equipment|Apple update|iphone|optical)")


def _ticker_of(name: str) -> str:
    """代號只認分隔符包住的四碼(-2330 · _6526 · (4171, · 3014TT);年份(2026年 · 展望2026半導體)與日期(-1141201)不算。"""
    m = _TK_RX.search(name)
    return m.group(1) if m else ""


def _nonstock_type(name: str) -> str:
    m = _NONSTOCK_RX.search(name)
    return m.group(1) if m else ""


def extract_classify(apply: bool = True) -> dict:
    last = _ledger_last()
    rows = []
    for name, j in last.items():
        if j.get("status") != "REVIEW":
            continue
        tk = _ticker_of(name)
        cats = j.get("categories") or {}
        fin_cats = {k: v for k, v in cats.items() if k not in ("OTHER", "", None) and v}
        why = j.get("why", "")
        kind = _nonstock_type(name)
        if not tk and kind:
            new = "NONFIN_OK"
            basis = "非個股報告(檔名無代號 · 類型「%s」)→ 三表檢查不適用" % kind
        elif not tk:
            new = "REVIEW"
            basis = "檔名無代號也不是已知非個股類型 → 人看(可能是個股報告,如 daiwa_aspeed)"
        elif not fin_cats and j.get("tables", 0) == 0:
            new = "REVIEW"
            basis = "個股報告(%s)但無表 → 版面 / OCR" % tk
        else:
            new = "REVIEW"
            basis = "個股報告(%s)但三表認不出 → 字典 / 版面" % tk
        rows.append({"file": name, "ticker": tk, "tables": j.get("tables"), "cats": cats, "why": why, "new": new, "basis": basis, "sha8": j.get("sha8")})
        if apply and new != "REVIEW":
            _append({"file": name, "sha8": j.get("sha8"), "status": new, "why": basis, "pages": j.get("pages"), "tables": j.get("tables"), "categories": cats, "reclass_from": "REVIEW", "by": Path(__file__).name})
    c = Counter(r["new"] for r in rows)
    return {"verb": "extract_classify", "n": len(rows), "counts": dict(c), "rows": rows, "lamp": "GREEN" if rows else "GRAY"}


def extract_gate(status_counts: dict | None = None) -> dict:
    if status_counts is None:
        status_counts = Counter((j.get("status") or "?") for j in _ledger_last().values())
    n = sum(status_counts.values())
    good = status_counts.get("READ", 0) + status_counts.get("TEXT_DOC", 0) + status_counts.get("NONFIN_OK", 0)
    rev = status_counts.get("REVIEW", 0) + status_counts.get("NODATA", 0)
    err = status_counts.get("ERROR", 0)
    ratio = (good / n) if n else 0
    lamp = "GREEN" if (n and ratio >= 0.95 and err == 0 and rev / n <= 0.05) else ("RED" if err else ("YELLOW" if n else "GRAY"))
    return {"verb": "extract_gate", "n": n, "counts": dict(status_counts), "good_ratio": round(ratio, 3), "review": rev, "error": err, "lamp": lamp, "rule": "READ+TEXT_DOC+NONFIN_OK ≥ 95% · ERROR = 0 · REVIEW+NODATA ≤ 5%"}


_V0150 = vars(PRIOR).get("PRIOR")
if _V0150 is not None:
    setattr(_V0150, "extract_gate", extract_gate)      # 讓 v0151 的 U/I 主作業卡與 RESULT_extract_latest 用本版門檻(NONFIN_OK 計良)


def extract_loop(d: Path, rounds: int = 2, limit: int = 0, min_docs: int = 2) -> dict:
    ext_fn = _resolve("extract")
    tri_fn = _resolve("extract_triage")
    adopt = _resolve("lexicon_auto_adopt")
    files = sorted(p for p in d.rglob("*.pdf")) if d.is_dir() else []
    out = {"verb": "extract_loop", "dir": str(d), "rounds": [], "lamp": "GRAY"}
    if not (ext_fn and files):
        out.update(why="鏈上沒有 extract" if not ext_fn else "夾裡沒有 PDF", lamp="RED")
        return out
    by_name = {p.name: p for p in files}
    todo = files
    ad = {"adopted": [], "pending": []}
    for r in range(1, rounds + 1):
        res = ext_fn(todo, ("pdfplumber", "camelot", "tabula"), limit if r == 1 else 0)
        counts = Counter((x.get("status") or "?") for x in res.get("docs", res.get("rows", res.get("files", []))) if isinstance(x, dict))
        tri = tri_fn() if tri_fn else {"unmatched_labels": [], "noise": {}}
        ad = adopt(tri.get("unmatched_labels", []), min_docs=min_docs, apply=True) if adopt else ad
        cl = extract_classify(apply=True)
        last = _ledger_last()
        review_files = sorted({by_name[n] for n, j in last.items() if j.get("status") in ("REVIEW", "NODATA") and n in by_name})
        out["rounds"].append({"round": r, "scanned": len(todo), "counts": dict(counts), "adopted": len(ad["adopted"]), "pending": len(ad["pending"]), "noise": tri.get("noise", {}), "reclass": cl["counts"], "lexicon": ad.get("new") or ad.get("tail"), "review_next": len(review_files)})
        if not review_files or not ad["adopted"]:      # 字典沒長就不重掃(重掃結果會一樣)
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
        print("[計] extract loop 第 %d 輪 · 掃 %d · %s · 自動採納 %d · 未解 %d · 非列標 %s · 改判 %s · 冊 %s · 下輪重掃 %d" % (r["round"], r["scanned"], " ".join("%s=%d" % kv for kv in sorted(r["counts"].items())), r["adopted"], r["pending"], " ".join("%s=%d" % kv for kv in sorted(r["noise"].items())) or "0", " ".join("%s=%d" % kv for kv in sorted(r["reclass"].items())) or "0", r["lexicon"], r["review_next"]))
    g = o["gate"]
    print("[計] 完工門檻 · 檔 %d · %s · 良率 %.1f%% · 待審 %d · ERROR %d · %s · %s" % (g["n"], " ".join("%s=%d" % kv for kv in sorted(g["counts"].items())), g["good_ratio"] * 100, g["review"], g["error"], g["rule"], g["lamp"]))
    for x in o.get("pending_labels", [])[:40]:
        print("  [YEL] 列標 %s · %d 次 · %d 檔(等操作員+AI)" % (x.get("label"), x.get("n", 0), x.get("docs", 0)))
    print("NEXT: %s" % ("完工:VRN 實測過門檻" if g["lamp"] == "GREEN" else "extract review 看仍待審的個股報告 → 字典 / 版面;非個股報告已改判 NONFIN_OK"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    if args[:2] == ["lexicon", "add"]:
        fp = Path(opt("--file", "") or "")
        la, tailf = _resolve("lexicon_add"), _resolve("_lex_tail")
        if not (fp.is_file() and la and tailf):
            print("[拒跑] lexicon add --file <裁定 json>")
            return 2
        rul = json.loads(fp.read_text(encoding="utf-8-sig"))
        dry = la(rul, apply=False)
        t = tailf()
        cur = (json.loads(t.read_text(encoding="utf-8-sig")).get("noise_rules") or {}) if t else {}
        same_noise = all(cur.get(k) == v for k, v in (rul.get("noise_rules") or {}).items())
        if not dry.get("added_std") and not dry.get("added_alias") and same_noise:
            print("[計] VRN lexicon add · SKIP(冊 %s 已含本批 · 不出新版)· GREEN" % (t.name if t else "—"))
            return 0
        r = la(rul, apply=True)
        print("[計] VRN lexicon add · %s · %s → %s · 新 std %d · 新別名 %d · 列 %d · 噪音規則 %d · %s" % (r["status"], r.get("tail"), r.get("new", "—"), r.get("added_std", 0), r.get("added_alias", 0), r.get("rows", 0), r.get("noise_rules", 0), r["lamp"]))
        return 0
    if args[:2] == ["extract", "classify"]:
        o = extract_classify(apply=("--dry" not in args))
        print("[計] extract classify · REVIEW %d → %s · %s" % (o["n"], " ".join("%s=%d" % kv for kv in sorted(o["counts"].items())) or "無", o["lamp"]))
        for r in o["rows"][:40]:
            print("  [%s] %s · 代號 %s · 表 %s · %s · %s" % ("OK" if r["new"] == "NONFIN_OK" else "YEL", r["file"][:60], r["ticker"] or "—", r["tables"], r["new"], r["basis"]))
        return 0
    if args[:2] == ["extract", "review"]:
        last = _ledger_last()
        rows = [(n, j) for n, j in last.items() if j.get("status") in ("REVIEW", "NODATA")]
        print("[計] extract review · 仍待審 %d" % len(rows))
        for n, j in rows[:40]:
            print("  [YEL] %s · %s · 代號 %s · 表 %s · 類別 %s · %s" % (j.get("status"), n[:60], _ticker_of(n) or "—", j.get("tables"), json.dumps(j.get("categories") or {}, ensure_ascii=False), j.get("why", "")[:50]))
        return 0
    if args[:2] == ["extract", "gate"]:
        g = extract_gate()
        print("[計] 完工門檻 · 檔 %d · %s · 良率 %.1f%% · 待審 %d · ERROR %d · %s" % (g["n"], " ".join("%s=%d" % kv for kv in sorted(g["counts"].items())), g["good_ratio"] * 100, g["review"], g["error"], g["lamp"]))
        return 0
    if args[:2] == ["extract", "loop"]:
        o = extract_loop(Path(opt("--dir") or (HERE / "input" / "incoming")), int(opt("--rounds", "2") or 2), int(opt("--limit", "0") or 0), int(opt("--min-docs", "2") or 2))
        _print_loop(o)
        s = PRIOR.extract_summary() if hasattr(PRIOR, "extract_summary") else None
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

    td = Path(tempfile.mkdtemp(prefix="vrncls-"))
    saved = os.environ.get("VIA_VRN_EXTRACT_OUT")
    os.environ["VIA_VRN_EXTRACT_OUT"] = str(td / "extract")
    (td / "extract").mkdir()
    for rec in [{"file": "GS-2330 20251203.pdf", "sha8": "a", "status": "READ", "categories": {"IS": 2}}, {"file": "20260916兆豐台灣產業專題-航太產業.pdf", "sha8": "b", "status": "REVIEW", "tables": 3, "categories": {"OTHER": 3}, "why": "3 表但類別不確定"},
                {"file": "MS-2308 20251128.pdf", "sha8": "c", "status": "REVIEW", "tables": 4, "categories": {"OTHER": 4}, "why": "4 表但類別不確定"}, {"file": "投資早報251209.pdf", "sha8": "d", "status": "REVIEW", "tables": 0, "categories": {}, "why": "有文字無表"},
                {"file": "260914_daiwa_aspeed.pdf", "sha8": "e", "status": "REVIEW", "tables": 2, "categories": {"OTHER": 2}, "why": "2 表"}]:
        _append(rec)
    o = extract_classify(apply=True)
    g = extract_gate()
    chk("① classify:產業專題 / 投資早報 → NONFIN_OK;MS-2308(個股)與 daiwa_aspeed(無代號但非已知類型)仍 REVIEW;只增新帳列", o["counts"].get("NONFIN_OK") == 2 and o["counts"].get("REVIEW") == 2 and _ledger_last()["投資早報251209.pdf"]["status"] == "NONFIN_OK" and _ledger_last()["260914_daiwa_aspeed.pdf"]["status"] == "REVIEW")
    chk("② gate:NONFIN_OK 計良 → 3/5 = 60% 黃 · 代號認法:年份 / 日期不算", g["n"] == 5 and g["good_ratio"] == 0.6 and g["review"] == 2 and g["lamp"] == "YELLOW" and _ticker_of("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf") == "" and _ticker_of("第三場 AI潮流下展望2026半導體產業趨勢.pdf") == "" and _ticker_of("瑞基(4171,NR_未評等)-CTBC251208.pdf") == "4171" and _ticker_of("3014TT-20231005.pdf") == "3014" and _ticker_of("凱基投顧_6526 達發科技_劉宇程_20260917.pdf") == "6526")
    chk("⑤ 鏈解析:lexicon_add(v0149)· lexicon_auto_adopt(v0148)· 帶噪音的 extract_triage(v0149)都找得到", all(callable(_resolve(n)) for n in ("lexicon_add", "lexicon_auto_adopt", "_lex_tail", "extract", "extract_triage")) and "noise" in (_resolve("extract_triage").__doc__ or "") + str(_resolve("extract_triage").__code__.co_names))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    chk("④ 帶加速器橋", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8"))
    if saved is None:
        os.environ.pop("VIA_VRN_EXTRACT_OUT", None)
    else:
        os.environ["VIA_VRN_EXTRACT_OUT"] = saved
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0152 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

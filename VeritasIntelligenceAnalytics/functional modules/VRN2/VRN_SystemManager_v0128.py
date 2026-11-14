#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0128 — 薄尾:extract 三態改嚴謹 + triage 動詞(2026-10-06 實跑 20 檔:READ 8 REVIEW 12,OTHER 表 8–26/檔把「待審」灌爆)。
改法(前版檔不動,記憶體替換 _rebuild_table / extract_one 兩函式):
  ① 表分三種:FIN(有財務類別)· TEXT_BLOCK(表裡沒有任何數字格 = 文字欄位被當表)· OTHER(有數字但列標認不出);只有 FIN 與 OTHER 計入待審,TEXT_BLOCK 不計
  ② 三態:READ = ≥1 FIN 表算術過;REVIEW = FIN 表有算術問題,或 0 FIN 但有 OTHER(數字表認不出列標);NODATA 同前
  ③ 算術核容忍百分比寫法:毛利率 0.4 與 40 都收;期間表頭多認 2024A / FY24E / 2025F(E) / 2Q25 / 114年
  ④ extract triage  掃 VIA_Reports/vrn/extract/*/financial.json → 認不出的列標 Top 40(含出現檔數)· 算術問題分類 · 各券商 FIN/OTHER/TEXT 比 · 期間表頭認不出的樣本 → 貼回包(≤300 行)讓操作員+AI 擴字典
其餘動詞照前版鏈。沙盒鍵同 v0127(VIA_VRN_EXTRACT_OUT)。
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
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0128"


def _vnum_v0128(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0128(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0128(p) < _vnum_v0128(__file__)), key=_vnum_v0128)
PRIOR = _load_v0128(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


_P27 = PRIOR
_REBUILD_27 = _P27._rebuild_table
_EXTRACT_ONE_27 = _P27.extract_one

# ③ 期間表頭擴充
_PERIOD_RX_28 = re.compile(r"^(?:FY)?(?:20)?\d{2}(?:[AEFP])?(?:\([EFA]\))?$|^[1-4]Q(?:FY)?\d{2,4}[AEF]?$|^(?:1H|2H)\d{2,4}[AEF]?$|^1[01]\d年(?:度|[1-4]季)?$|^\d{2,4}年(?:度|[1-4]季|上半年|下半年)?[EF]?$", re.I)


def _is_period_28(s: str) -> bool:
    t = _P27._clean_cell(s).replace(" ", "")
    return bool(_PERIOD_RX_28.match(t)) or bool(_P27._PERIOD_RX.match(t))


_P27._is_period = _is_period_28


def _arith_28(matrix: dict) -> list:
    """毛利率 0.4 / 40 都收:比對時把 ≤1.5 的比率乘 100。"""
    g = {k: dict(v) for k, v in matrix.items()}
    for key in ("gross_margin", "operating_margin", "net_margin"):
        for per, v in list(g.get(key, {}).items()):
            if v is not None and abs(v) <= 1.5:
                g[key][per] = v * 100
    return _P27._arith(g)


def _rebuild_table_28(tbl: dict, lex: list) -> dict:
    rb = _REBUILD_27(tbl, lex)
    n_num = sum(len(r.get("values", {})) for r in rb.get("rows", []))
    if rb.get("category") == "OTHER" and n_num == 0:
        rb["category"] = "TEXT_BLOCK"
        rb["issues"] = [x for x in rb.get("issues", []) if x != "無期間表頭"]
    elif rb.get("category") in ("IS", "FORECAST") and rb.get("matrix"):
        rb["issues"] = [x for x in rb.get("issues", []) if "≠" not in x] + _arith_28(rb["matrix"])
    rb["unmatched_labels"] = [r["label_raw"] for r in rb.get("rows", []) if not r.get("label_std") and r.get("values")][:30]
    return rb


_P27._rebuild_table = _rebuild_table_28


def _restatus_28(rec: dict) -> dict:
    """照 financial.json 重判三態(只算 FIN / OTHER,TEXT_BLOCK 不計)。"""
    d = Path(rec.get("dir", ""))
    fp = d / "financial.json"
    if not fp.exists():
        return rec
    fin = json.loads(fp.read_text(encoding="utf-8"))
    tabs = fin.get("tables", [])
    text_blocks = [t for t in tabs if t.get("category") == "TEXT_BLOCK"]
    fin_t = [t for t in tabs if t.get("category") not in ("OTHER", "TEXT_BLOCK")]
    other = [t for t in tabs if t.get("category") == "OTHER"]
    good = [t for t in fin_t if not t.get("issues")]
    bad = [t for t in fin_t if t.get("issues")]
    if rec.get("status") == "NODATA":
        pass
    elif good:
        rec["status"], rec["why"] = "READ", "FIN %d 表算術過;FIN 待審 %d · OTHER(認不出列標)%d · 文字塊 %d 不計" % (len(good), len(bad), len(other), len(text_blocks))
    elif fin_t:
        rec["status"], rec["why"] = "REVIEW", "FIN %d 表全有算術問題 · OTHER %d · 文字塊 %d" % (len(bad), len(other), len(text_blocks))
    elif other:
        rec["status"], rec["why"] = "REVIEW", "0 FIN · OTHER %d(數字表但列標認不出 → 擴字典)· 文字塊 %d" % (len(other), len(text_blocks))
    else:
        rec["status"], rec["why"] = "REVIEW", "只有文字塊 %d,無數字表" % len(text_blocks)
    rec["categories"] = dict(Counter(t.get("category") for t in tabs))
    fin["by_category"] = {k: [t["table"] for t in tabs if t.get("category") == k] for k in rec["categories"]}
    fp.write_text(json.dumps(fin, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def extract_one_28(pdf, out_root, engines=("pdfplumber", "camelot", "tabula"), avail=None) -> dict:
    return _restatus_28(_EXTRACT_ONE_27(pdf, out_root, engines, avail))


_P27.extract_one = extract_one_28


def extract_triage(top: int = 40) -> dict:
    root = _P27._out_root()
    labels, issues, per_broker, periods_bad = Counter(), Counter(), defaultdict(Counter), Counter()
    label_docs = defaultdict(set)
    n_docs = 0
    for fp in sorted(root.glob("*/financial.json")):
        try:
            fin = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        n_docs += 1
        broker = (fin.get("filename") or {}).get("broker_std") or "?"
        for t in fin.get("tables", []):
            cat = t.get("category", "OTHER")
            per_broker[broker][cat] += 1
            for lab in t.get("unmatched_labels", []) or [r["label_raw"] for r in t.get("rows", []) if not r.get("label_std") and r.get("values")]:
                k = _P27._clean_cell(lab)[:40]
                labels[k] += 1
                label_docs[k].add(fp.parent.name)
            for iss in t.get("issues", []):
                kind = "毛利≠營收−成本" if "毛利≠" in iss else ("率不符" if "≠" in iss else iss)
                issues[kind] += 1
            if "無期間表頭" in t.get("issues", []) and t.get("rows"):
                hdr = t["rows"][0].get("label_raw", "")
                periods_bad[hdr[:30]] += 1
    return {"verb": "extract_triage", "docs": n_docs, "unmatched_labels": [{"label": k, "n": v, "docs": len(label_docs[k])} for k, v in labels.most_common(top)],
            "issues": dict(issues.most_common()), "per_broker": {b: dict(c) for b, c in per_broker.items()}, "period_header_samples": [k for k, _ in periods_bad.most_common(10)],
            "lamp": "YELLOW" if labels else "GREEN"}


def _print_triage(out: dict) -> None:
    print("[計] extract triage · 檔 %d · 認不出列標 %d 種 · 算術問題 %s · %s" % (out["docs"], len(out["unmatched_labels"]), out["issues"], out["lamp"]))
    print("[計] 各券商 FIN/OTHER/TEXT · " + " · ".join("%s:%s" % (b, ",".join("%s=%d" % kv for kv in sorted(c.items()))) for b, c in sorted(out["per_broker"].items())))
    for x in out["unmatched_labels"]:
        print("  [YEL] 列標 %s · %d 次 · %d 檔" % (x["label"], x["n"], x["docs"]))
    for s in out["period_header_samples"]:
        print("  [YEL] 無期間表頭樣本:%s" % s)
    print("NEXT: 把上面列標貼給 AI → 擴 VRN 財務字典(SSOT/VRN_FinLexicon 冊)→ 重跑 extract;OTHER 歸零才算完成")


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:2] == ["extract", "triage"]:
        _print_triage(extract_triage())
        return 0
    return _P27.main(args)


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    lex = _P27._FIN_STD
    rb = _rebuild_table_28({"rows": [["公司", "說明"], ["台積電", "晶圓代工龍頭"], ["聯發科", "IC 設計"]]}, lex)
    chk("① 無數字格的表 → TEXT_BLOCK(不計待審)", rb["category"] == "TEXT_BLOCK")
    rb2 = _rebuild_table_28({"rows": [["", "2024A", "2025F(E)"], ["Revenue", "1000", "1200"], ["COGS", "600", "700"], ["Gross profit", "400", "500"], ["Gross margin", "0.40", "0.417"]]}, lex)
    chk("② 期間 2024A / 2025F(E) 認得 · 毛利率 0.40 當 40% → 算術過", rb2["periods"] == ["2024A", "2025F(E)"] and not rb2["issues"])
    rb3 = _rebuild_table_28({"rows": [["", "114年"], ["營業收入淨額", "1000"], ["營業毛利", "400"], ["神秘指標", "9"]]}, lex)
    chk("③ 認不出的列標進 unmatched_labels(神秘指標)· 114年 當期間", "神秘指標" in rb3["unmatched_labels"] and rb3["periods"] == ["114年"])
    td = Path(tempfile.mkdtemp(prefix="vrnext28-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_EXTRACT_OUT", "VIA_NO_OPEN", "VIA_VRN_UI_DIR")}
    os.environ.update({"VIA_VRN_EXTRACT_OUT": str(td / "out"), "VIA_NO_OPEN": "1", "VIA_VRN_UI_DIR": str(td / "ui")})
    pdf = td / "Demo-2330 20251001.pdf"
    if _P27._make_pdf(pdf) and _P27._engines().get("pdfplumber"):
        res = _P27.extract([pdf], ("pdfplumber", "camelot", "tabula"))
        r = res["rows"][0]
        chk("④ 真 PDF 走 v0128 重判:READ · why 帶 FIN/OTHER/文字塊 計", r["status"] == "READ" and "FIN" in r["why"])
        tri = extract_triage()
        chk("⑤ triage:檔 1 · 有券商統計 · 無認不出列標(demo 全對)", tri["docs"] == 1 and tri["per_broker"] and not tri["unmatched_labels"])
    else:
        print("  [注] reportlab/pdfplumber 不在 → ④⑤ 跳過(環境)")
        p += 2
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else _P27.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 帶加速器橋 · glob 取前版 · 獨立 MAIN", "[VIA:ACCEL-BRIDGE:v0100]" in body and "setdefault(\"VIA_FROM_VCGC\"" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0128 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

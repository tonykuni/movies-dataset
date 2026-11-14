#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ConsensusJoin v0107 — v0106 薄尾(v0106 ~ v0100 一字不改):Combined 冊新增小數欄 UPSIDE_ADJ · 舊欄 UPSIDE_PCT(ADJ) 保留並標註。

操作員 2026-11-03 裁定:「新增小數欄,舊欄保留並標註」(規格:資料庫存純小數,例 0.236747897;百分比只在 U/I / 摘要乘 100 加 %)。
  · UPSIDE_ADJ(新 · 小數比率)= 市場資料(含 v0105 同步還原補位)的 upside_adj = TARGET_PRICE(ADJ) ÷ ADJ_CLOSE − 1,全精度 9 位小數;
    市場沒有這檔 / 沒有值 → 空(不從格式化字串反推、不填 0)。
  · UPSIDE_PCT(ADJ)(舊 · 百分數,46.0 = 46%)照舊產生、位置不動;增量庫既有列不改寫(新欄在舊列是 null)。
  · 欄序:UPSIDE_ADJ 緊接在 UPSIDE_PCT(ADJ) 後面;Combined JSON / CSV / Parquet 三份同一欄序。
  · 標註:output/VRN2_Combined_columns_latest.json(欄位 → 單位 / 定義 / 舊欄或新欄)· U/I 以它顯示表頭說明。
動詞同 v0106:run · join · --selftest · --engine-shim。
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

VERSION = "v0107"
DISPLAY_NAME = "VRN2_ConsensusJoin"
TAG = "共識合併 v0107"
PRIOR_NAME = "VRN2_ConsensusJoin_v0106.py"
HERE = Path(__file__).resolve().parent
NEW_COL = "UPSIDE_ADJ"
OLD_COL = "UPSIDE_PCT(ADJ)"
NOTES_NAME = "VRN2_Combined_columns_latest.json"
COLUMN_NOTES = {
    OLD_COL: {"unit": "percent", "status": "舊欄保留(v0107 起不建議再拿來計算)", "definition": "上漲空間 × 100 · 小數 1 位(46.0 = 46%)"},
    NEW_COL: {"unit": "ratio", "status": "新欄(v0107)· 資料庫標準", "definition": "TARGET_PRICE(ADJ) ÷ ADJ_CLOSE − 1 · 純小數 9 位(0.46 = 46%)· U/I 才乘 100 加 %"},
}


def _load(path: Path, alias: str):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    return _load(path, "vrn2_consensus_join_prior_v0106")


PRIOR = _prior()                       # v0106(它再載 v0105 → v0104 → v0103 → v0102 → v0101 → v0100)
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0100 = PRIOR.V0100
for _mod in (PRIOR, PRIOR.PRIOR, PRIOR.V0104, PRIOR.V0103, PRIOR.V0102, PRIOR.V0101, V0100):
    _mod.TAG = TAG
_native_write = V0100._write
_native_columns = V0100.columns


def columns(n: int | None = None) -> list:
    cols = list(_native_columns(n))
    if OLD_COL in cols and NEW_COL not in cols:
        cols.insert(cols.index(OLD_COL) + 1, NEW_COL)
    return cols


def ratio_text(v) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return ""
    if x != x:                          # NaN
        return ""
    return format(round(x, 9), ".9f")


def _upside_map(v2: Path) -> dict:
    """join 進行中讀市場資料(v0105 的 jread 已換成「同步還原補位後」那份)→ {FILENAME: upside_adj}。"""
    mk = V0100._jread(Path(v2) / "market" / "VRN2_Market_latest.json", {}) or {}
    out = {}
    for fn, m in (mk.get("per_file") or {}).items():
        if isinstance(m, dict) and m.get("upside_adj") is not None:
            out[fn] = m.get("upside_adj")
    return out


def _write(out_dir: Path, rows: list, cols: list) -> dict:
    """前版 join 用改接後的 columns()(清單已含新欄、列裡沒有)· v0105 改寫 STATUS 時在 join 外再寫一次(那時市場資料沒有同步還原補位)
    → 一律依欄序重建每列;新欄只在空白時才填,已有的值絕不覆蓋。"""
    out_dir = Path(out_dir)
    cols = list(cols)
    if OLD_COL in cols:
        if NEW_COL not in cols:
            cols.insert(cols.index(OLD_COL) + 1, NEW_COL)
        need = [r for r in rows if str(r.get(NEW_COL) or "") == ""]
        ups = _upside_map(out_dir.parent) if need else {}
        rows = [{c: ((r.get(NEW_COL) or ratio_text(ups.get(r.get("FILENAME")))) if c == NEW_COL else r.get(c, "")) for c in cols} for r in rows]
    files = _native_write(out_dir, rows, cols)
    try:
        notes = {"engine": "VRN2_ConsensusJoin %s" % VERSION, "columns": COLUMN_NOTES, "order": cols}
        p = out_dir / NOTES_NAME
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)
        files["column_notes"] = str(p)
    except OSError as error:
        files["column_notes"] = "(沒寫:%s)" % type(error).__name__
    return files


V0100._write = _write
V0100.columns = columns
run, join = PRIOR.run, PRIOR.join


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────────
def selftest(engine: str | None = None) -> int:
    fails = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            fails.append(label)

    chk("① 版鏈:v0107 → v0106 → v0105 → v0100 · v0100 的 _write / columns 改接本版", PRIOR.VERSION == "v0106" and PRIOR.PRIOR.VERSION == "v0105" and V0100._write is _write and V0100.columns is columns)
    cols = columns(2026)
    chk("② 欄序:UPSIDE_ADJ 緊接 UPSIDE_PCT(ADJ) 之後 · 其他欄序照前版", cols.index(NEW_COL) == cols.index(OLD_COL) + 1 and [c for c in cols if c != NEW_COL] == list(_native_columns(2026)))
    chk("③ 小數格式:2.982306163 · 0.46 → 0.460000000 · 空 / 文字 / NaN → 空(不填 0)",
        ratio_text(2.982306163) == "2.982306163" and ratio_text(0.46) == "0.460000000" and ratio_text(None) == "" and ratio_text("n/a") == "" and ratio_text(float("nan")) == "")
    with tempfile.TemporaryDirectory() as td:
        v2 = Path(td)
        (v2 / "market").mkdir()
        (v2 / "market" / "VRN2_Market_latest.json").write_text(json.dumps({"per_file": {"a.pdf": {"upside_adj": 0.236747897, "upside_pct_adj": 23.7}, "b.pdf": {"upside_pct_adj": None}}}), encoding="utf-8")
        base = [c for c in _native_columns(2026)]
        rows = [{c: "" for c in base} for _ in range(3)]
        for r, fn, pct in zip(rows, ("a.pdf", "b.pdf", "c.pdf"), ("23.7", "", "")):
            r.update(FILENAME=fn, **{OLD_COL: pct})
        files = _write(v2 / "output", rows, base)
        js = json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))
        hdr = (v2 / "output" / "VRN2_Combined_latest.csv").read_text(encoding="utf-8-sig").splitlines()[0].split(",")
        notes = json.loads((v2 / "output" / NOTES_NAME).read_text(encoding="utf-8"))
        chk("④ Combined:a.pdf UPSIDE_ADJ = 0.236747897(市場全精度)· 舊欄 23.7 保留 · b / c 沒值 → 空",
            js[0][NEW_COL] == "0.236747897" and js[0][OLD_COL] == "23.7" and js[1][NEW_COL] == "" and js[2][NEW_COL] == "")
        chk("⑤ JSON 鍵序 = CSV 表頭 = columns()", list(js[0].keys()) == cols and hdr == ["\"%s\"" % c if "," in c else c for c in cols])
        chk("⑥ 欄位標註檔:舊欄 percent / 新欄 ratio · 欄序同 Combined", notes["columns"][OLD_COL]["unit"] == "percent" and notes["columns"][NEW_COL]["unit"] == "ratio" and notes["order"] == cols and "column_notes" in files)
        files2 = _write(v2 / "output2", [dict(js[0])], list(js[0].keys()))
        js2 = json.loads((v2 / "output2" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))
        chk("⑦ 已有 UPSIDE_ADJ 的列再寫一次 → 不重複加欄 · 值不變", list(js2[0].keys()).count(NEW_COL) == 1 and js2[0][NEW_COL] == "0.236747897" and "json" in files2)
        (v2 / "market" / "VRN2_Market_latest.json").write_text(json.dumps({"per_file": {}}), encoding="utf-8")
        _write(v2 / "output2", js2, list(js2[0].keys()))
        js3 = json.loads((v2 / "output2" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))
        chk("⑧ join 外重寫(市場資料沒有這檔 · 像 v0105 改寫 STATUS)→ 已有的 UPSIDE_ADJ 不被清空", js3[0][NEW_COL] == "0.236747897")
    with tempfile.TemporaryDirectory() as td:
        v2 = Path(td)
        (v2 / "output").mkdir()
        (v2 / "market").mkdir()
        basic = [{"REPORT_DATE": "2026-05-20", "FILENAME": "x.pdf", "TICKER": "2330", "NAME": "台積電", "TARGET_PRICE": "1300"},
                 {"REPORT_DATE": "2026-05-20", "FILENAME": "y.pdf", "TICKER": "2317", "NAME": "鴻海", "TARGET_PRICE": ""}]
        (v2 / "output" / "VRN2_BasicInfo_latest.json").write_text(json.dumps(basic, ensure_ascii=False), encoding="utf-8")
        (v2 / "market" / "VRN2_Market_latest.json").write_text(json.dumps({"per_file": {"x.pdf": {"target_price_adj": 1300.0, "adj_close": 1000.0, "upside_adj": 0.3, "upside_pct_adj": 30.0}}}), encoding="utf-8")
        try:
            got = V0100.join(v2)
            jsj = json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))
            ok = list(jsj[0].keys()).index(NEW_COL) == list(jsj[0].keys()).index(OLD_COL) + 1 and jsj[0][NEW_COL] == "0.300000000" and jsj[0][OLD_COL] == "30.0" and jsj[1][NEW_COL] == ""
            why = "" if ok else json.dumps({k: jsj[0].get(k) for k in (OLD_COL, NEW_COL)}, ensure_ascii=False)
        except Exception as error:  # noqa: BLE001
            ok, why = False, "%s: %s" % (type(error).__name__, error)
        chk("⑨ 前版 join() 實跑(改接後的 columns 清單已含新欄)→ x.pdf UPSIDE_ADJ 0.300000000 · 舊欄 30.0 · y.pdf 沒市場值 → 空 %s" % why, ok)
    n = 9
    print("[%s] VRN2_ConsensusJoin v0107 自測 %s(%d 項)" % ("GREEN" if not fails else "RED", "全過" if not fails else "不過:%s" % "; ".join(fails), n))
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest(argv[1] if len(argv) > 1 else None)
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())

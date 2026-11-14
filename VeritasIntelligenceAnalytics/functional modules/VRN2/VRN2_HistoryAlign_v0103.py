#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_HistoryAlign v0103 — v0102 薄尾(v0102 ~ v0100 一字不改):FinancialAligned / Deleted 的 Parquet 依欄位型別寫,不再因同欄混型寫不出來。

桌機 2026-11-02 15:18 收據:FinancialAligned 11,905 列 · JSON / CSV 都在,Parquet「(沒寫:ArrowInvalid)」。
根因:v0100 的 _write_books 把 None 換成 ""(空字串),同一欄其他列是數字 → pyarrow 一欄同時看到 str 與 float → ArrowInvalid → 整本 Parquet 沒寫。
v0103:先照 v0100 寫 JSON / CSV / Parquet(前版行為一字不改);**只有** Parquet 沒寫成時,改用「依欄位型別」重寫:
  · 一欄全是數字(int / float · 不含 bool)→ 數字欄 · 空值 = null(不是 0、也不是 "")
  · 一欄全是字串 → 字串欄 · 空值 = null
  · 真混型(數字與字串同欄)→ 整欄轉字串(數字照 repr · 不四捨五入)· 空值 = null · dict / list 照 v0100 用 JSON 字串
  · 寫完讀回比對列數與欄名;不符就不留檔、照報沒寫(不冒充成功)。收據 written[...] 多 parquet_typed = 每欄型別。
JSON / CSV 不動;增量庫(OutputStore)讀的是 JSON,不受影響。動詞同 v0102:align --root <VIA 根> · --selftest
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path

VERSION = "v0103"
DISPLAY_NAME = "VRN2_HistoryAlign"
TAG = "歷史對齊 v0103"
PRIOR_NAME = "VRN2_HistoryAlign_v0102.py"
HERE = Path(__file__).resolve().parent


def _prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_historyalign_prior_v0102", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _prior()                         # v0102(它再載 v0101 → v0100)
BASE = PRIOR.BASE                        # v0100:align() 用它自己 globals 的 _write_books
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
BASE.TAG = TAG
_native_write_books = BASE._write_books


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def column_kinds(rows: list, cols: list) -> dict:
    """每欄型別:num(全是數字)/ str(全是字串)/ mixed(數字與字串同欄)/ empty(全空)· dict / list 算字串。"""
    kinds = {}
    for c in cols:
        seen = set()
        for r in rows:
            v = r.get(c)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                continue
            seen.add("num" if _is_num(v) else "str")
            if len(seen) == 2:
                break
        kinds[c] = "mixed" if len(seen) == 2 else (seen.pop() if seen else "empty")
    return kinds


def _cell(v, kind: str):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if kind == "num":
        return float(v)
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v) if kind in ("str", "mixed", "empty") else v


def write_typed_parquet(path: Path, rows: list) -> dict:
    """依欄位型別寫 Parquet(tmp 再換上)→ 讀回比對列數 / 欄名;回 {ok, kinds, why}。"""
    import pyarrow as pa  # noqa: WPS433
    import pyarrow.parquet as pq  # noqa: WPS433
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    kinds = column_kinds(rows, cols)
    arrays = [pa.array([_cell(r.get(c), kinds[c]) for r in rows], type=pa.float64() if kinds[c] == "num" else pa.string()) for c in cols]
    table = pa.Table.from_arrays(arrays, names=cols) if cols else pa.table({"FILENAME": pa.array([], pa.string())})
    tmp = Path(path).with_suffix(".parquet.tmp")
    pq.write_table(table, str(tmp), compression="zstd")
    back = pq.read_table(str(tmp))
    if back.num_rows != len(rows) or list(back.column_names) != (cols or ["FILENAME"]):
        tmp.unlink(missing_ok=True)
        return {"ok": False, "kinds": kinds, "why": "讀回不符(列 %d / %d · 欄 %d / %d)" % (back.num_rows, len(rows), len(back.column_names), len(cols))}
    tmp.replace(path)
    return {"ok": True, "kinds": kinds, "why": ""}


def _write_books(out_dir: Path, aligned: list, deleted: list) -> dict:
    written = _native_write_books(out_dir, aligned, deleted)
    for name, rows in (("FinancialAligned", aligned), ("Deleted", deleted)):
        w = written.get(name) or {}
        if not str(w.get("parquet", "")).startswith("(沒寫"):
            continue
        pp = Path(out_dir) / ("VRN2_%s_latest.parquet" % name)
        try:
            got = write_typed_parquet(pp, rows)
        except Exception as error:  # noqa: BLE001  型別版也寫不成 → 照實報(JSON / CSV 已寫好)
            w["parquet"] = "%s · 型別版也沒寫成:%s" % (w.get("parquet"), type(error).__name__)
            continue
        if got["ok"]:
            k = got["kinds"]
            w["parquet"] = str(pp)
            w["parquet_typed"] = {"rule": "v0103 依欄位型別寫(前版同欄混型 ArrowInvalid)· 空值 null", "num": sum(1 for v in k.values() if v == "num"),
                                  "str": sum(1 for v in k.values() if v == "str"), "mixed_as_str": sorted(c for c, v in k.items() if v == "mixed"), "rows": len(rows)}
        else:
            w["parquet"] = "%s · 型別版:%s" % (w.get("parquet"), got["why"])
    return written


BASE._write_books = _write_books
align = PRIOR.align


def selftest() -> int:
    fails = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            fails.append(label)

    chk("① 版鏈:v0103 → v0102 → v0100 · v0100 的 _write_books 改接本版", PRIOR.VERSION == "v0102" and BASE._write_books is _write_books)
    rows = [{"FILENAME": "a.pdf", "ITEM": "Revenue", "VALUE_FINAL": 100.5, "HISTORY_VALUE": None, "RECON_RATIO": 1, "NOTE": None},
            {"FILENAME": "a.pdf", "ITEM": "EPS", "VALUE_FINAL": None, "HISTORY_VALUE": 2.1, "RECON_RATIO": "n/a", "NOTE": {"k": 1}},
            {"FILENAME": "b.pdf", "ITEM": "ROE", "VALUE_FINAL": 0.12, "HISTORY_VALUE": None, "RECON_RATIO": None, "NOTE": "x"}]
    k = column_kinds(rows, list(rows[0]))
    chk("② 欄型別:VALUE_FINAL / HISTORY_VALUE 數字 · RECON_RATIO 混型 · NOTE 字串(dict 算字串)",
        k["VALUE_FINAL"] == "num" and k["HISTORY_VALUE"] == "num" and k["RECON_RATIO"] == "mixed" and k["NOTE"] == "str" and k["ITEM"] == "str")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        try:
            import pyarrow as pa  # noqa: WPS433,F401
            import pyarrow.parquet as pq  # noqa: WPS433
            have_pa = True
        except ImportError:
            have_pa = False
        native = _native_write_books(out / "n", rows, [])
        chk("③ 重現:前版 _write_books 對這組列 Parquet 沒寫(None→\"\" 混型)" + ("" if have_pa else "(沒有 pyarrow · 略)"),
            (not have_pa) or str(native["FinancialAligned"].get("parquet", "")).startswith("(沒寫"))
        w = _write_books(out / "t", rows, [])
        fa = w["FinancialAligned"]
        if have_pa:
            t = pq.read_table(fa["parquet"])
            vf = t.column("VALUE_FINAL").to_pylist()
            chk("④ v0103:Parquet 寫成 · 3 列 · VALUE_FINAL 數字欄且空值是 null(不是 0 / \"\")· RECON_RATIO 混型轉字串",
                t.num_rows == 3 and str(t.schema.field("VALUE_FINAL").type) == "double" and vf == [100.5, None, 0.12]
                and t.column("RECON_RATIO").to_pylist() == ["1", "n/a", None] and fa["parquet_typed"]["mixed_as_str"] == ["RECON_RATIO"])
            chk("⑤ JSON / CSV 照前版寫(列數 3 · CSV 空值仍是空字串)", len(json.loads(Path(fa["json"]).read_text(encoding="utf-8"))) == 3
                and Path(fa["csv"]).read_text(encoding="utf-8-sig").splitlines()[1].endswith(","))
            clean = [{"FILENAME": "c.pdf", "VALUE_FINAL": 1.0}]
            w2 = _write_books(out / "c", clean, [])
            chk("⑥ 前版寫得成的(沒混型)→ 不重寫 · 沒有 parquet_typed", "parquet_typed" not in w2["FinancialAligned"] and Path(w2["FinancialAligned"]["parquet"]).is_file())
        else:
            chk("④ 沒有 pyarrow → 照實報沒寫(不冒充)", str(fa.get("parquet", "")).startswith("(沒寫"))
    n = 6
    print("[%s] %s %s 自測 %s(%d 項)" % ("GREEN" if not fails else "RED", DISPLAY_NAME, VERSION, "全過" if not fails else "不過:%s" % "; ".join(fails), n))
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return BASE.main(argv)


if __name__ == "__main__":
    sys.exit(main())

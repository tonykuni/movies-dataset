# -*- coding: utf-8 -*-
"""via_input_precheck_v0100.py — 輸入前檢查共用件(母頁/各子系統 P1 規約)。

先擋後跑:①重複輸入(整列重複/鍵欄重複)②缺欄(必要欄空值)③路徑不存在。
誠實列出問題;無問題 exit 0,有問題 exit 1(呼叫端決定攔或放)。

USAGE
  python via_input_precheck_v0100.py --file data.csv [--key date,ticker] [--required close]
  python via_input_precheck_v0100.py --path "C:\\x\\y.json" [--path ...]
  python via_input_precheck_v0100.py selftest
"""
import argparse
import csv
import json
import sys
from pathlib import Path


def load_rows(fp: Path):
    if fp.suffix.lower() in (".csv", ".tsv"):
        delim = "\t" if fp.suffix.lower() == ".tsv" else ","
        with fp.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f, delimiter=delim))
    if fp.suffix.lower() == ".json":
        j = json.loads(fp.read_text(encoding="utf-8-sig"))
        rows = j.get("records") if isinstance(j, dict) else j
        return rows if isinstance(rows, list) else []
    raise SystemExit("[FAIL] 只支援 csv/tsv/json:%s" % fp)


def check_file(fp: Path, key_cols, required):
    problems = []
    if not fp.exists():
        return [("路徑不存在", str(fp))]
    rows = load_rows(fp)
    if not rows:
        problems.append(("空檔", "0 資料列"))
        return problems
    # 重複:整列
    seen, dup_full = set(), 0
    for r in rows:
        k = json.dumps(r, sort_keys=True, ensure_ascii=False)
        if k in seen:
            dup_full += 1
        seen.add(k)
    if dup_full:
        problems.append(("重複輸入(整列)", "%d 列與前列完全相同" % dup_full))
    # 重複:鍵欄
    if key_cols:
        seenk, dupk = set(), []
        for i, r in enumerate(rows, 1):
            k = tuple(str(r.get(c, "")) for c in key_cols)
            if k in seenk:
                dupk.append((i, k))
            seenk.add(k)
        if dupk:
            problems.append(("重複輸入(鍵 %s)" % ",".join(key_cols),
                             "%d 列重鍵,例:列%d %s" % (len(dupk), dupk[0][0], dupk[0][1])))
    # 缺欄
    for col in required:
        missing = [i for i, r in enumerate(rows, 1)
                   if col not in r or r.get(col) in (None, "", "NaN")]
        if col not in rows[0]:
            problems.append(("缺欄", "欄位 %s 不存在(實有:%s)" % (col, list(rows[0])[:8])))
        elif missing:
            problems.append(("缺值", "欄 %s 有 %d 列空值(例:列%d)" % (col, len(missing), missing[0])))
    return problems


def selftest():
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "t.csv"
        p.write_text("date,ticker,close\n2026-01-01,SPY,100\n2026-01-01,SPY,100\n"
                     "2026-01-02,QQQ,\n", encoding="utf-8")
        pr = check_file(p, ["date", "ticker"], ["close"])
        kinds = {k for k, _ in pr}
        t1 = "重複輸入(整列)" in kinds and any("重複輸入(鍵" in k for k in kinds) and "缺值" in kinds
        print("  dup+missing 偵測      %s" % ("PASS" if t1 else "FAIL")); ok &= t1
        clean = Path(td) / "c.csv"
        clean.write_text("date,close\n2026-01-01,100\n2026-01-02,101\n", encoding="utf-8")
        t2 = check_file(clean, ["date"], ["close"]) == []
        print("  乾淨檔零誤報          %s" % ("PASS" if t2 else "FAIL")); ok &= t2
        t3 = check_file(Path(td) / "no.csv", [], []) == [("路徑不存在", str(Path(td) / "no.csv"))]
        print("  路徑不存在偵測        %s" % ("PASS" if t3 else "FAIL")); ok &= t3
    print("  precheck selftest:%s" % ("3/3 PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if argv[:1] == ["selftest"]:
        return selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--key", default="", help="鍵欄(逗號分隔)— 查鍵重複")
    ap.add_argument("--required", default="", help="必要欄(逗號分隔)— 查缺欄/缺值")
    ap.add_argument("--path", action="append", default=[], help="僅查路徑存在(可多次)")
    a = ap.parse_args(argv)
    problems = []
    for p in a.path:
        if not Path(p).exists():
            problems.append(("路徑不存在", p))
    if a.file:
        problems += check_file(Path(a.file),
                               [c for c in a.key.split(",") if c],
                               [c for c in a.required.split(",") if c])
    if problems:
        print("[輸入前檢查] %d 項問題(先擋後跑):" % len(problems))
        for k, v in problems:
            print("  ✗ %s:%s" % (k, v))
        return 1
    print("[輸入前檢查] 全過 — 無重複/缺欄/路徑問題")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VeritaQuantGuard(VQG)v0111 — v0110 薄尾(v0110 一字不改 · SHA-256 釘在 PRIOR_SHA256)。

操作員 2026-11-11:「WE ONLY ADD INDICATORS AND FORMULA AND REGISTER THEM IN VQG」
              欄位「編號 分類 指標名稱 公式 參數 時間參數 benchmark pros & cons 替代指標」。

本版只加一個動詞 indicators(VQG 自己的指標登記冊 · 不寫他系統 · 不加別的功能):
  冊      同夾 VQG_IndicatorRegister_SSOT_v*.json 尾版(新增指標 = 程式加公式 + 冊出新版號加一列;舊列不刪不改)。
  indicators                列表(編號 · 分類 · 指標名稱 · 時間參數)
  indicators --full         每列全欄(公式 · 參數 · benchmark · pros · cons · 替代指標)
  indicators --id <代碼>    單列(stable_id 或 編號)
  indicators --check        冊 ⇄ 程式對帳:技術指標 stable_id / 公式一字相同 · 量化分析 / 回測 / 因子 / 統計每個輸出欄都有一列登記 ·
                            不重號 · 必填欄不空 · 替代指標指到冊內存在的代碼 → GREEN rc 0 / RED rc 1
  indicators --export [夾]  CSV(utf-8-sig · Excel 可開)+ MD,欄位照操作員順序;預設 <VIA>/VIA_Reports/vqg/indicator_register
邊界:同 v0110(零網路 · 不 import VAP / VDF · 不寫 VDF 夾);只讀冊 · 只在 --export 寫自己的報表夾;前版被改過 → rc 2。不用 TA-Lib。
自測:python VQG_AllInOne_v0111.py selftest(本版 12 項 + v0110 自測於乾淨子行程 · 零網路 · 只在 tempfile 寫)。
"""
from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

VERSION_TAIL = "v0111"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VQG_AllInOne_v0110.py"
PRIOR_SHA256 = "56611ba99ebef4801e281c5ff283fa5081e5e4028dfa4730a50ebd2966360373"   # v0110(main)
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0111 是 v0110 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vqg_v0110_for_v0111", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
V10 = PRIOR
V9 = PRIOR.V9                         # v0109(STRATEGIES · FACTOR_COLS · backtest · factor_ic · stats_rows)
V8 = PRIOR.V8                         # v0108(ANALYSIS_SCHEMA · NEW_CORE)
V7 = PRIOR.V7                         # v0107(via_root)
V4 = V9.V4                            # v0104(CORE:stable_id · formula · solutions)
pl = PRIOR.pl

REGISTER_GLOB = "VQG_IndicatorRegister_SSOT_v*.json"
REQUIRED = ("no", "stable_id", "category", "name_zh", "formula", "time_params", "benchmark", "pros", "cons")
USER_COLUMNS = (("編號", "no"), ("分類", "category"), ("指標名稱", "name_zh"), ("公式", "formula"), ("參數", "params"),
                ("時間參數", "time_params"), ("benchmark", "benchmark"), ("pros", "pros"), ("cons", "cons"), ("替代指標", "alternatives"))


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.json$", p.name)
    return int(m.group(1)) if m else -1


def register_path(folder: Path | None = None) -> Path | None:
    hits = sorted((folder or HERE).glob(REGISTER_GLOB), key=_vnum)
    return hits[-1] if hits else None


def load_register(path: Path | None = None) -> dict:
    p = path or register_path()
    if p is None:
        raise FileNotFoundError("VQG 指標登記冊 %s 不在 %s" % (REGISTER_GLOB, HERE))
    book = json.loads(p.read_text(encoding="utf-8"))
    book["_path"] = str(p)
    return book


# ── 程式端清單(全部從前版程式物件取;回測 / 因子 / 統計的輸出欄用零網路小夾具實跑得到)──────────────
def _fixture():
    d0 = date(2026, 1, 5)
    series, ind = {}, {}
    for k, tk in enumerate(("A.TW", "B.TW", "C.TW", "D.TW")):
        dates = [d0 + timedelta(days=i) for i in range(40)]
        px = [100.0 + k * 3 + 0.4 * i + 2.5 * (((i * (7 + k)) % 5) - 2) for i in range(40)]
        series[tk] = pl.DataFrame({"date": dates, "adj_close": px})
        cols = {"observation_date": dates}
        for j, fc in enumerate(list(V9.FACTOR_COLS) + ["SMA_20_S1"]):
            cols[fc] = [float(((i * (3 + j + k)) % 11) - 5 + (px[i] if fc == "SMA_20_S1" else 0)) for i in range(40)]
        ind[tk] = pl.DataFrame(cols)
    return series, ind


def code_inventory() -> dict:
    series, ind = _fixture()
    _curve, summary, _miss = V9.backtest(series["A.TW"], ind["A.TW"], "A.TW")
    _wide, fsum = V9.factor_ic(ind, series)
    stats, _corr = V9.stats_rows(series)
    fkeys = set()
    for v in (fsum.get("factors") or {}).values():
        fkeys |= set(v)
    return {
        "indicators": {k: (v.get("stable_id"), v.get("formula")) for k, v in V4.CORE.items()},
        "analysis": list(V8.ANALYSIS_SCHEMA),
        "strategies": list(V9.STRATEGIES),
        "backtest": sorted({k for row in summary for k in row}),
        "factors": list(V9.FACTOR_COLS),
        "factor_metrics": sorted(fkeys | {"ic"}),                         # ic = 每日 IC(factor/ 寬表的值)
        "stats": sorted(set(stats.columns) | {"return_corr"}),            # return_corr = 相關矩陣表
    }


def check(book: dict, inv: dict | None = None) -> dict:
    inv = inv or code_inventory()
    entries = book.get("entries") or []
    meta = book.get("meta_columns") or {}
    bad = []
    ids, nos = {}, {}
    for e in entries:
        for f in REQUIRED:
            if not str(e.get(f) or "").strip():
                bad.append("必填欄空:%s · %s" % (e.get("stable_id") or e.get("no"), f))
        for f in ("params", "alternatives"):
            if not isinstance(e.get(f), list):
                bad.append("欄型別錯(要清單):%s · %s" % (e.get("stable_id"), f))
        ids[e.get("stable_id")] = ids.get(e.get("stable_id"), 0) + 1
        nos[e.get("no")] = nos.get(e.get("no"), 0) + 1
    bad += ["重號 stable_id:%s" % k for k, n in ids.items() if n > 1]
    bad += ["重號 編號:%s" % k for k, n in nos.items() if n > 1]
    known = set(ids)
    for e in entries:
        for a in e.get("alternatives") or []:
            if str(a).startswith("VQG.") and a not in known:
                bad.append("替代指標指到不存在的代碼:%s → %s" % (e.get("stable_id"), a))
        for r in e.get("refs") or []:
            if r not in known:
                bad.append("refs 指到不存在的代碼:%s → %s" % (e.get("stable_id"), r))
    live = [e for e in entries if e.get("implemented", True)]
    planned = [e.get("stable_id") for e in entries if not e.get("implemented", True)]
    # 技術指標:程式每一個都要登記 · stable_id / 公式一字相同;冊上已實作的都要在程式裡
    reg_ind = {e.get("code_key"): e for e in live if e.get("kind") == "indicator"}
    for key, (sid, formula) in inv["indicators"].items():
        e = reg_ind.get(key)
        if e is None:
            bad.append("程式有、冊沒登記:指標 %s(%s)" % (key, sid))
            continue
        if e.get("stable_id") != sid:
            bad.append("stable_id 不同:%s 冊 %s ≠ 程式 %s" % (key, e.get("stable_id"), sid))
        if e.get("formula") != formula:
            bad.append("公式不同:%s(冊與程式要一字相同)" % sid)
    bad += ["冊上標已實作、程式沒有:指標 %s" % k for k in reg_ind if k not in inv["indicators"]]

    def cover(kind, field, code_keys, meta_key=None):
        code = set(code_keys) - set(meta.get(meta_key, []) if meta_key else [])
        seen = {}
        for e in live:
            if e.get("kind") != kind:
                continue
            vals = e.get(field)
            for c in (vals if isinstance(vals, list) else [vals]):
                seen[c] = seen.get(c, 0) + 1
        out = ["程式有、冊沒登記:%s 欄 %s" % (kind, c) for c in sorted(code - set(seen))]
        out += ["冊上有、程式沒有:%s 欄 %s" % (kind, c) for c in sorted(set(seen) - code)]
        out += ["同一欄登記兩次:%s 欄 %s" % (kind, c) for c, n in seen.items() if n > 1]
        return out

    bad += cover("analysis", "output_columns", inv["analysis"], "quant_analysis")
    bad += cover("strategy", "strategy_key", inv["strategies"])
    bad += cover("backtest_metric", "output_columns", inv["backtest"], "backtest_summary")
    bad += cover("factor", "factor_key", inv["factors"])
    bad += cover("factor_metric", "output_columns", inv["factor_metrics"], "factor_summary")
    bad += cover("stat", "output_columns", inv["stats"], "stats")
    return {"lamp": "RED" if bad else "GREEN", "register": Path(book.get("_path", "?")).name, "entries": len(entries),
            "planned": planned, "problems": bad,
            "code": {k: len(v) for k, v in inv.items()}}


def _cell(v) -> str:
    if isinstance(v, list):
        return " ; ".join(str(x) for x in v) if v else "—"
    return str(v) if v not in (None, "") else "—"


def export(book: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "VQG_IndicatorRegister_" + str(book.get("version", "v0000"))
    rows = book.get("entries") or []
    head = [c for c, _ in USER_COLUMNS] + ["stable_id"]
    with open(out_dir / (stem + ".csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        for e in rows:
            w.writerow([_cell(e.get(k)) for _, k in USER_COLUMNS] + [e.get("stable_id")])
    md = ["# VQG 指標登記冊 %s(%d 列)" % (book.get("version"), len(rows)), "",
          "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for e in rows:
        md.append("| " + " | ".join(_cell(e.get(k)).replace("|", "\\|") for _, k in USER_COLUMNS) + " | " + str(e.get("stable_id")) + " |")
    (out_dir / (stem + ".md")).write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"csv": str(out_dir / (stem + ".csv")), "md": str(out_dir / (stem + ".md")), "rows": len(rows)}


def _print_list(book: dict, full: bool = False, only: str | None = None) -> int:
    rows = book.get("entries") or []
    if only:
        rows = [e for e in rows if only in (e.get("stable_id"), e.get("no"))]
        if not rows:
            print("[RED] 冊上沒有 %s" % only, flush=True)
            return 1
    print("VQG 指標登記冊 %s · %s · %d 列" % (book.get("version"), Path(book["_path"]).name, len(book.get("entries") or [])), flush=True)
    for e in rows:
        if full or only:
            print("─" * 72, flush=True)
            for label, k in USER_COLUMNS:
                print("  %-8s %s" % (label, _cell(e.get(k))), flush=True)
            print("  %-8s %s" % ("代碼", e.get("stable_id")), flush=True)
        else:
            print("  %-8s %-10s %-30s %-16s %s" % (e.get("no"), e.get("category"), e.get("stable_id"), e.get("name_zh"), e.get("time_params")), flush=True)
    return 0


def indicators(argv: list) -> int:
    try:
        book = load_register()
    except (OSError, ValueError) as error:
        print("[RED] VQG %s indicators · %s" % (VERSION_TAIL, error), flush=True)
        return 1
    if "--check" in argv:
        c = check(book)
        print("[%s] VQG %s 指標冊對帳 · %s · %d 列 · 程式 %s · 問題 %d%s" % (
            c["lamp"], VERSION_TAIL, c["register"], c["entries"], c["code"], len(c["problems"]),
            (" · 規劃中(未實作)%d" % len(c["planned"])) if c["planned"] else ""), flush=True)
        for p in c["problems"]:
            print("  [RED] " + p, flush=True)
        return 0 if c["lamp"] == "GREEN" else 1
    if "--export" in argv:
        i = argv.index("--export")
        nxt = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else None
        via = V7.via_root(None)
        out = Path(nxt) if nxt else ((via / "VIA_Reports" / "vqg" / "indicator_register") if via else Path.cwd() / "VIA_Reports" / "vqg" / "indicator_register")
        r = export(book, out)
        print("[GREEN] VQG %s 指標冊匯出 · %d 列 → %s · %s" % (VERSION_TAIL, r["rows"], r["csv"], r["md"]), flush=True)
        return 0
    only = argv[argv.index("--id") + 1] if "--id" in argv and argv.index("--id") + 1 < len(argv) else None
    return _print_list(book, full="--full" in argv, only=only)


def selftest() -> int:
    ok = total = 0

    def chk(label, cond, note=""):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label, (" · " + str(note)) if note else ""), flush=True)
    print("[VQG %s selftest]" % VERSION_TAIL, flush=True)
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=1700, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    prior_lines = [l for l in (cp.stdout or "").splitlines() if l.strip().startswith(("[PASS]", "[FAIL]"))]
    chk("① 前版 v0110 SHA-256 釘住(一字未改)", PRIOR_SHA_OK)
    book = load_register()
    chk("② 冊在同夾 · 讀得到 · 有列", bool(book.get("entries")), "%s · %d 列" % (Path(book["_path"]).name, len(book["entries"])))
    inv = code_inventory()
    c = check(book, inv)
    chk("③ 冊 ⇄ 程式對帳 GREEN(19 指標公式一字相同 · 每個輸出欄都有登記)", c["lamp"] == "GREEN", c["problems"][:3])
    b = copy.deepcopy(book)
    b["entries"] = [e for e in b["entries"] if e.get("stable_id") != "VQG.IND.RSI"]
    for e in b["entries"]:
        e["alternatives"] = [a for a in e.get("alternatives") or [] if a != "VQG.IND.RSI"]
        e["refs"] = [r for r in e.get("refs") or [] if r != "VQG.IND.RSI"]
    chk("④ 刪掉一個指標列 → RED(程式有、冊沒登記)", any("rsi" in p for p in check(b, inv)["problems"]))
    b = copy.deepcopy(book)
    next(e for e in b["entries"] if e.get("stable_id") == "VQG.IND.SMA")["formula"] += " "
    chk("⑤ 公式差一個字 → RED", any("公式不同" in p and "VQG.IND.SMA" in p for p in check(b, inv)["problems"]))
    b = copy.deepcopy(book)
    tr = next(e for e in b["entries"] if e.get("stable_id") == "VQG.ANA.TREND_REGIME")
    tr["output_columns"] = [x for x in tr["output_columns"] if x != "trend_regime"]
    chk("⑥ 量化分析欄漏登 → RED", any("trend_regime" in p for p in check(b, inv)["problems"]))
    b = copy.deepcopy(book)
    b["entries"].append(dict(b["entries"][0]))
    chk("⑦ 重號 → RED", any("重號" in p for p in check(b, inv)["problems"]))
    b = copy.deepcopy(book)
    b["entries"][0]["alternatives"] = ["VQG.IND.NOT_THERE"]
    chk("⑧ 替代指標指到不存在的代碼 → RED", any("NOT_THERE" in p for p in check(b, inv)["problems"]))
    b = copy.deepcopy(book)
    plan = dict(b["entries"][0], stable_id="VQG.IND.PLANNED_X", no="VQG-999", code_key="planned_x", implemented=False)
    b["entries"].append(plan)
    c9 = check(b, inv)
    chk("⑨ 規劃中(implemented=false)的新列不算孤兒 · 照列出", c9["lamp"] == "GREEN" and "VQG.IND.PLANNED_X" in c9["planned"], c9["problems"][:2])
    b = copy.deepcopy(book)
    b["entries"][3]["benchmark"] = ""
    chk("⑩ 必填欄空(benchmark)→ RED", any("必填欄空" in p and "benchmark" in p for p in check(b, inv)["problems"]))
    with tempfile.TemporaryDirectory() as td:
        r = export(book, Path(td))
        with open(r["csv"], encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
        md = Path(r["md"]).read_text(encoding="utf-8")
        chk("⑪ 匯出 CSV + MD · 欄位照操作員順序 · 列數 = 冊列數",
            rows[0][:10] == [c for c, _ in USER_COLUMNS] and len(rows) - 1 == len(book["entries"]) and md.count("\n| VQG-") == len(book["entries"]), rows[0][:4])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 本檔:第 3 行加速器橋 · 零網路 import · 無 TA-Lib",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and not re.search(r"^\s*(import|from)\s+(urllib|requests|socket|http|httpx|aiohttp|talib)\b", src, re.M))
    prior_ok = cp.returncode == 0
    for l in prior_lines[-3:]:
        print("    前版 " + l.strip(), flush=True)
    good = ok == total and prior_ok
    print("[%s] VQG %s selftest · 本版 %d/%d · 前版鏈 v0110 %s" % ("PASS" if good else "FAIL", VERSION_TAIL, ok, total, "PASS" if prior_ok else "FAIL"), flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = next((a for a in argv if not a.startswith("-")), "scan")
    if cmd in ("selftest", "test") or "--selftest" in argv:
        try:
            return selftest()
        except Exception as error:  # noqa: BLE001
            print("[FAIL] VQG %s selftest 中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
            return 1
    if not PRIOR_SHA_OK:
        print("[RED] VQG %s 前版 %s 被改過(SHA-256 不符)· 停" % (VERSION_TAIL, PRIOR_NAME), flush=True)
        return 2
    if cmd == "indicators":
        return indicators(argv)
    if "--help" in argv or "-h" in argv:
        rc = V10.main(argv)
        print("v0111:indicators [--full | --id <代碼> | --check | --export [夾]](VQG 指標登記冊)", flush=True)
        return rc
    return V10.main(argv)


if __name__ == "__main__":
    sys.exit(main())

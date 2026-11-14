#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ConsensusJoin v0102 — v0101 薄尾(v0101 / v0100 與共識引擎都一字不改):鉅亨沒有 FactSet 頁的代號不拖垮整批的品質閘。

桌機 2026-10-29 19:00(RoundAll v0102)⑥f:共識 41 / 43 · gate FAIL_CLOSED · rc 1。品質矩陣只有兩列不過:
  6933 / 4171 FETCH_PIPELINE「TARGET_PRICE_STATUS_NOT_200: statusCode=404 message=頁面或商品不存在」—— 鉅亨根本沒有這兩檔的 FactSet 頁
  (6933 新上市 · 4171 未評等),不是抓失敗;其餘 41 檔全過。引擎的閘一列不過就整批 FAIL_CLOSED。
v0102:v0101 跑完若 gate = FAIL_CLOSED,且品質矩陣裡每一列不過都屬於「回 404 頁面不存在」的代號(其他檢查沒有不過)→ 把這些代號從代號清單拿掉,
  同一個引擎再跑一次(續跑 · 其他代號沿用 checkpoint)→ 閘只評有覆蓋的代號。收據多 no_coverage(代號 · 原因)與 first_gate;沒覆蓋的代號在 Combined 的
  STATUS 寫「鉅亨沒有 FactSet 頁(404)」。有任何別的不過列 → 不重跑,照 v0101(FAIL_CLOSED 原樣回報)。
動詞同 v0101:run · join · --selftest · --engine-shim。
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

VERSION = "v0102"
DISPLAY_NAME = "VRN2_ConsensusJoin"
TAG = "共識合併 v0102"
PRIOR_NAME = "VRN2_ConsensusJoin_v0101.py"
HERE = Path(__file__).resolve().parent
QUALITY_CSV = "factset_yfinance_consensus_quality_matrix.csv"
_NO_PAGE = re.compile(r"statusCode=404|頁面或商品不存在")


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
    return _load(path, "vrn2_consensus_join_prior_v0101")


PRIOR = _prior()                       # v0101(它自己再載 v0100)
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
PRIOR.TAG = TAG
PRIOR.PRIOR.TAG = TAG
_v0101_run = PRIOR.run
_native_codes = PRIOR.codes_from_basic


def quality_fails(out: Path) -> list:
    """品質矩陣裡 status = FAIL 的列。"""
    path = Path(out) / QUALITY_CSV
    if not path.is_file():
        return []
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            return [r for r in csv.DictReader(fh) if str(r.get("status", "")).upper() == "FAIL"]
    except (OSError, csv.Error):
        return []


def no_coverage(rows: list, codes: list) -> dict:
    """{代號: 原因}:只有在「每一列不過都屬於回 404 頁面不存在的代號」時才回;有任何別的不過列 → {}(照 FAIL_CLOSED)。"""
    bad = {str(r.get("code") or "").strip(): str(r.get("actual") or "")[:160] for r in rows if _NO_PAGE.search(str(r.get("actual") or "") + " " + str(r.get("note") or ""))}
    bad = {c: why for c, why in bad.items() if c in codes}
    if not bad or any(str(r.get("code") or "").strip() not in bad for r in rows) or len(bad) >= len(codes):
        return {}
    return bad


def run(v2: Path, root: Path | None = None, fixtures: list | None = None, timeout: int = 900, engine: str | None = None) -> dict:
    rec = _v0101_run(v2, root, fixtures, timeout, engine)
    if str(rec.get("gate", "")).upper() != "FAIL_CLOSED":
        return rec
    out = Path(v2) / "consensus"
    codes = list(rec.get("codes") or [])
    skip = no_coverage(quality_fails(out), codes)
    if not skip:
        rec["no_coverage"] = {}
        return rec
    first = {k: rec.get(k) for k in ("gate", "rc", "why")}
    print("    [⑥f] [計] 品質閘 FAIL_CLOSED 只因鉅亨沒有 FactSet 頁(404):%s → 這些代號不納入、同一個引擎再跑一次(其他代號續跑沿用)" % ",".join(sorted(skip)), flush=True)
    PRIOR.codes_from_basic = lambda path: [c for c in _native_codes(path) if c not in skip]
    try:
        rec = _v0101_run(v2, root, fixtures, timeout, engine)
    finally:
        PRIOR.codes_from_basic = _native_codes
    rec.update(no_coverage=skip, first_gate=first, codes_all=codes)
    rec["why"] = "%s · 鉅亨沒有 FactSet 頁(404)不納入閘:%s" % (rec.get("why", ""), ",".join(sorted(skip)))
    return PRIOR._finish(out, rec)


PRIOR.run = run
PRIOR.PRIOR.run = run                 # v0100 main() (the CLI 'run' verb RoundAll uses) resolves run in its own globals
_native_join = PRIOR.join


def join(v2: Path) -> dict:
    """v0101 的 join;沒覆蓋的代號那幾列 STATUS 加「鉅亨沒有 FactSet 頁(404)」。"""
    got = _native_join(v2)
    try:
        cons = json.loads((Path(v2) / "consensus" / CONSENSUS_JSON).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return got
    skip = cons.get("no_coverage") or {}
    if not skip:
        return got
    for name in ("VRN2_Combined_latest.json",):
        path = Path(v2) / "output" / name
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        hit = 0
        for row in rows:
            if str(row.get("TICKER") or "")[:4] in skip and "鉅亨沒有 FactSet 頁" not in str(row.get("STATUS") or ""):
                row["STATUS"] = (str(row.get("STATUS") or "") + " · 鉅亨沒有 FactSet 頁(404)").strip(" ·")
                hit += 1
        if hit:
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
            csv_path = path.with_suffix(".csv")
            if rows and csv_path.is_file():
                with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)
            got["no_coverage_rows"] = hit
    return got


PRIOR.join = join
PRIOR.PRIOR.join = join


def selftest(engine: str | None = None) -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    rc = PRIOR.selftest(engine)
    chk("① v0101 自測(含 v0100 · 上櫃 .TWO)照過", rc == 0)
    rows = [{"code": "6933", "check_id": "FETCH_PIPELINE", "actual": "TARGET_PRICE_STATUS_NOT_200: statusCode=404 message=頁面或商品不存在", "status": "FAIL"},
            {"code": "4171", "check_id": "FETCH_PIPELINE", "actual": "TARGET_PRICE_STATUS_NOT_200: statusCode=404 message=頁面或商品不存在", "status": "FAIL"}]
    codes = ["2330", "6933", "4171", "3661"]
    chk("② 只有 404 頁面不存在的列 → 那幾檔不納入(6933 · 4171)", sorted(no_coverage(rows, codes)) == ["4171", "6933"])
    chk("③ 還有別的不過列(2330 HTTP 500)→ 不動(照 FAIL_CLOSED)· 全部代號都 404 → 不動",
        no_coverage(rows + [{"code": "2330", "check_id": "HTTP_PAGE_200", "actual": "500", "status": "FAIL"}], codes) == {} and no_coverage(rows, ["6933", "4171"]) == {})
    with tempfile.TemporaryDirectory(prefix="vrn2-cj102-") as temporary:
        v2 = Path(temporary) / "vrn2"
        (v2 / "consensus").mkdir(parents=True)
        (v2 / "output").mkdir()
        calls = []

        def fake_run(v2_, root=None, fixtures=None, timeout=900, engine=None):
            got = PRIOR.codes_from_basic(v2_)
            calls.append(got)
            if len(calls) == 1:
                with (v2_ / "consensus" / QUALITY_CSV).open("w", encoding="utf-8-sig", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=["code", "check_id", "actual", "expected", "status", "severity", "note"])
                    w.writeheader()
                    for r in rows:
                        w.writerow(dict(r, expected="successful fetch", severity="FAIL", note=""))
                    w.writerow({"code": "2330", "check_id": "HTTP_PAGE_200", "actual": "200", "expected": "200", "status": "PASS", "severity": "FAIL", "note": ""})
                return {"gate": "FAIL_CLOSED", "rc": 1, "codes": got, "why": "共識 2 / 4 代號(缺 6933,4171)", "lamp": "YELLOW"}
            return {"gate": "PASS", "rc": 0, "codes": got, "why": "共識 2 / 2 代號", "lamp": "GREEN"}
        saved = (globals()["_v0101_run"], globals()["_native_codes"])
        globals()["_v0101_run"], globals()["_native_codes"] = fake_run, (lambda path: list(codes))
        PRIOR.codes_from_basic = globals()["_native_codes"]
        try:
            rec = run(v2)
        finally:
            globals()["_v0101_run"], globals()["_native_codes"] = saved
            PRIOR.codes_from_basic = saved[1]
        chk("④ gate FAIL_CLOSED 只因 404 → 拿掉 6933 · 4171 再跑一次 → 第二次 PASS · 收據記 no_coverage / first_gate",
            calls == [codes, ["2330", "3661"]] and rec["gate"] == "PASS" and rec["lamp"] == "GREEN" and sorted(rec["no_coverage"]) == ["4171", "6933"] and rec["first_gate"]["gate"] == "FAIL_CLOSED" and "不納入閘" in rec["why"])
        (v2 / "output" / "VRN2_Combined_latest.json").write_text(json.dumps([{"TICKER": "6933", "STATUS": "共識缺"}, {"TICKER": "2330", "STATUS": "OK"}], ensure_ascii=False), encoding="utf-8")
        saved_join = globals()["_native_join"]
        globals()["_native_join"] = lambda path: {"lamp": "GREEN"}
        try:
            got = join(v2)
        finally:
            globals()["_native_join"] = saved_join
        combined = json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))
        chk("⑤ Combined:沒覆蓋的代號 STATUS 加「鉅亨沒有 FactSet 頁(404)」· 其他列不動", got.get("no_coverage_rows") == 1 and "鉅亨沒有 FactSet 頁(404)" in combined[0]["STATUS"] and combined[1]["STATUS"] == "OK")
    chk("⑥ 啟動器叫的 run / join 與 CLI 的 run / join 都是本版(v0101 · v0100 的模組也指過來)", PRIOR.run is run and PRIOR.PRIOR.run is run and PRIOR.join is join and PRIOR.PRIOR.join is join)
    print("[%s] %s %s --selftest · 6 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest(argv[1] if len(argv) > 1 else None)
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0113]
r"""VeritaQuantGuard(VQG)v0113 — v0112 薄尾(v0112 一字不改 · SHA-256 釘在 PRIOR_SHA256)。

對齊操作員 2026-09-23 還原四價裁定(VCGC 冊 VIA_VDF_TWMarketEndpoints_SSOT#adj_ohlc):
  「四欄全給」· 比例法(其餘三價乘 adj_close / close)是近似 → 要另存 adj_method 講明這一列是哪一種來的。
v0112 登的還原開 / 高 / 低就是比例法,少了 adj_method;本版只補這一項(冊 v0102 加一列 VQG-081 · kind = input_meta):
  derive(row)               v0112 的 14 欄 + adj_method('ratio' = 比例法算出;沒有還原比例 → 空值)
  fields --check            v0112 的 14 欄對帳 + 附註欄對帳(stable_id / 公式一字相同)· 比本版新的列(since 較大)略過,留給更新的尾版
  fields --scan [--json]    v0112 的掃描 + 裁定冊對照:裁定列的四欄 VQG 都有登 · adj_method 有登
  其餘動詞照前版。
邊界:同 v0112(零網路 · 不 import VAP / VDF · 不寫他系統的夾;裁定冊只當文字讀,本冊不抄第二份)。不用 TA-Lib。
自測:python VQG_AllInOne_v0113.py selftest(本版 8 項 + v0112 自測於乾淨子行程 · 零網路 · 只在 tempfile 寫)。
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION_TAIL = "v0113"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VQG_AllInOne_v0112.py"
PRIOR_SHA256 = "9d8468b70fd874ea70d3974bd4ffc3c1d99adb7448c6cd8e6a87e9452a52f132"   # v0112
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0113 是 v0112 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vqg_v0112_for_v0113", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
V12 = PRIOR
V11 = PRIOR.V11


def __getattr__(name):
    """前版公開面照轉(尾版不少名字)。"""
    return getattr(PRIOR, name)


META_KIND = "input_meta"
META_FIELDS = {
    "adj_method": {"stable_id": "VQG.IN.ADJ_METHOD",
                   "formula": "adj_method = 'ratio' if adj_open/adj_high/adj_low = raw * yf_adj_close / yf_close ; null if no factor",
                   "vdf": ("yf_adj_close", "yf_close")},
}
RULING_GLOB = "VIA_VDF_TWMarketEndpoints_SSOT_v*.json"
RULING_KEY = "adj_ohlc"


def derive(row: dict) -> dict:
    """v0112 的 14 欄 + adj_method。比例法算出還原三價的列記 'ratio';沒有還原比例(三價為空)記空值。"""
    out = V12.derive(row)
    flags = out.pop("_flags")
    out["adj_method"] = None if "no_adj_factor" in flags else "ratio"
    out["_flags"] = flags
    return out


def _newer(since: str) -> bool:
    return bool(re.fullmatch(r"v\d{4}", str(since or ""))) and str(since) > VERSION_TAIL


def meta_check(book: dict) -> dict:
    rows = [e for e in (book.get("entries") or []) if e.get("kind") == META_KIND]
    later = [e.get("stable_id") for e in rows if _newer(e.get("since"))]
    mine = {e.get("code_key"): e for e in rows if not _newer(e.get("since"))}
    bad = []
    for k, spec in META_FIELDS.items():
        e = mine.get(k)
        if e is None:
            bad.append("程式有、冊沒登記:附註欄 %s(%s)" % (k, spec["stable_id"]))
            continue
        if e.get("stable_id") != spec["stable_id"]:
            bad.append("stable_id 不同:%s 冊 %s ≠ 程式 %s" % (k, e.get("stable_id"), spec["stable_id"]))
        if e.get("formula") != spec["formula"]:
            bad.append("公式不同:%s(冊與程式要一字相同)" % spec["stable_id"])
        if tuple(e.get("vdf_columns") or ()) != tuple(spec["vdf"]):
            bad.append("VDF 來源欄不同:%s" % k)
    bad += ["冊上有、程式沒有:附註欄 %s" % k for k in mine if k not in META_FIELDS]
    return {"lamp": "RED" if bad else "GREEN", "rows": len(rows), "later": later, "problems": bad}


def ruling(via: Path | None = None) -> dict:
    """VCGC 的還原四價裁定(只讀)。"""
    via = via or V12.via_home()
    p = V12._tail(via / "supportive modules" / "registry", RULING_GLOB) if via else None
    book = V12._read_json(p) or {}
    r = book.get(RULING_KEY) if isinstance(book.get(RULING_KEY), dict) else {}
    return {"file": p.name if p else None, "cols": list(r.get("cols") or []), "ruled_by": r.get("ruled_by"), "rule": r.get("rule"), "honest": r.get("honest")}


def scan(book: dict, via: Path | None = None) -> dict:
    rep = V12.scan(book, via)
    if rep.get("lamp") == "NODATA":
        return rep
    rl = ruling(Path(rep["via"]) if rep.get("via") else via)
    have = {r["name"] for r in rep["rows"]}
    metas = {e.get("code_key") for e in (book.get("entries") or []) if e.get("kind") == META_KIND}
    miss = [c for c in rl["cols"] if c not in have]
    if rl["file"] is None or not rl["cols"]:
        state, lamp = "找不到還原四價裁定冊(%s#%s)" % (RULING_GLOB, RULING_KEY), "YELLOW"
    elif miss:
        state, lamp = "裁定列的欄 VQG 沒登:%s" % ", ".join(miss), "RED"
    elif "adj_method" not in metas:
        state, lamp = "裁定要求另存 adj_method,VQG 冊沒有這一列", "RED"
    else:
        state, lamp = "裁定四欄 %s 都有登 · adj_method 有登(比例法 = ratio)" % " / ".join(rl["cols"]), "GREEN"
    rep["ruling"] = dict(rl, lamp=lamp, state=state)
    e = next((x for x in (book.get("entries") or []) if x.get("code_key") == "adj_method"), {})
    rep["rows"].append({"no": e.get("no", ""), "stable_id": META_FIELDS["adj_method"]["stable_id"], "name": "adj_method", "category": e.get("category", ""),
                        "name_zh": e.get("name_zh", ""), "kind": "附註", "formula": META_FIELDS["adj_method"]["formula"],
                        "vrn": "未登記(VRN 的欄位冊沒有這個欄名)", "vdf": "(VDF 沒有這欄;由 VQG 依裁定產生)",
                        "vcgc": "裁定冊 %s#%s" % (rl["file"], RULING_KEY) if rl["file"] else "裁定冊不在",
                        "vqg": ("已登記 %s" % e.get("no")) if e else "未登記", "lamp": lamp, "state": state})
    worst = [r["lamp"] for r in rep["rows"]]
    rep["lamp"] = "RED" if "RED" in worst or rep["problems"] else "YELLOW" if "YELLOW" in worst else "GREEN"
    rep["counts"] = {x: worst.count(x) for x in ("GREEN", "YELLOW", "RED")}
    return rep


def fields(argv: list) -> int:
    if "--check" in argv:
        rc = V12.fields(argv)
        c = meta_check(V11.load_register())
        print("[%s] VQG %s 輸入欄附註對帳 · 冊 %d 列 · 程式 %d 項 · 問題 %d%s" % (
            c["lamp"], VERSION_TAIL, c["rows"], len(META_FIELDS), len(c["problems"]), (" · 較新的列 %d(留給更新的尾版)" % len(c["later"])) if c["later"] else ""), flush=True)
        for p in c["problems"]:
            print("  [RED] " + p, flush=True)
        return max(rc, 0 if c["lamp"] == "GREEN" else 1)
    if "--scan" in argv or "--export" in argv:
        book = V11.load_register()
        rep = scan(book)
        if "--json" in argv:
            print(json.dumps(rep, ensure_ascii=False, indent=1), flush=True)
        else:
            print("[%s] VQG %s 行情輸入欄 · 跨系統註冊檢查(VRN → VDF → VCGC)· %d 列 · %s" % (rep["lamp"], VERSION_TAIL, len(rep["rows"]), rep.get("counts", {})), flush=True)
            for u in rep.get("universe") or []:
                print("  範圍 %s %s · 代號規則照 VDF 輸入冊 %s" % (u["id"], u.get("zh") or "", u.get("code_regex") or ""), flush=True)
            for r in rep["rows"]:
                print("  [%-6s] %-8s %-6s %-22s VRN:%s ‖ VDF:%s ‖ VCGC:%s ‖ %s" % (r["lamp"], r["no"], r["category"], r["name"], r["vrn"], r["vdf"], r["vcgc"], r["state"]), flush=True)
            if rep.get("ruling"):
                print("  [%-6s] 還原四價裁定 · %s · %s" % (rep["ruling"]["lamp"], rep["ruling"].get("ruled_by") or "—", rep["ruling"]["state"]), flush=True)
            for p in rep.get("problems") or []:
                print("  [RED] " + p, flush=True)
        if "--export" in argv:
            i = argv.index("--export")
            nxt = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else None
            via = V12.via_home()
            out = Path(nxt) if nxt else ((via / "VIA_Reports" / "vqg" / "price_fields") if via else Path.cwd() / "VIA_Reports" / "vqg" / "price_fields")
            r = V12.export_scan(rep, out)
            print("[GREEN] VQG %s 行情輸入欄匯出 · %d 列 → %s · %s" % (VERSION_TAIL, r["rows"], r["csv"], r["md"]), flush=True)
        return 1 if rep["lamp"] in ("RED", "NODATA") else 0
    return V12.fields(argv)


def selftest() -> int:
    ok = total = 0

    def chk(label, cond, note=""):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label, (" · " + str(note)) if note else ""), flush=True)
    print("[VQG %s selftest]" % VERSION_TAIL, flush=True)
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=5000, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    prior_lines = [l for l in (cp.stdout or "").splitlines() if l.strip().startswith(("[PASS]", "[FAIL]"))]
    chk("① 前版 v0112 SHA-256 釘住(一字未改)", PRIOR_SHA_OK)
    book = V11.load_register()
    c = meta_check(book)
    chk("② 冊 ⇄ 程式:adj_method 一列 · stable_id / 公式 / 來源欄一字相同;v0112 的 14 欄對帳照舊 GREEN", c["lamp"] == "GREEN" and V12.fields_check(book)["lamp"] == "GREEN",
        (c["problems"] + V12.fields_check(book)["problems"])[:3])
    b = copy.deepcopy(book)
    next(e for e in b["entries"] if e.get("code_key") == "adj_method")["formula"] += " "
    chk("③ 公式差一個字 → RED", any("公式不同" in p for p in meta_check(b)["problems"]))
    b = copy.deepcopy(book)
    b["entries"].append(dict(next(e for e in b["entries"] if e.get("code_key") == "adj_method"), code_key="adj_asof", stable_id="VQG.IN.ADJ_ASOF", no="VQG-997", since="v0199"))
    c4 = meta_check(b)
    chk("④ 比本版新的列(since 較大)不算孤兒 · 照列出", c4["lamp"] == "GREEN" and "VQG.IN.ADJ_ASOF" in c4["later"], c4["problems"][:2])
    d = derive({"date": "2026-11-13", "ticker": "2330", "open": 100.0, "low": 95.0, "high": 110.0, "close": 105.0, "volume": 1000, "turnover": 104000.0,
                "yf_close": 105.0, "yf_adj_close": 94.5, "day_trade_volume": 300, "day_trade_value": 31000.0})
    d0 = derive({"date": "2026-11-13", "ticker": "2330", "open": 100.0, "low": 95.0, "high": 110.0, "close": 105.0, "yf_close": None, "yf_adj_close": 94.5})
    chk("⑤ 算法:有還原比例 → adj_method = ratio、14 欄值照 v0112;沒有比例 → 還原三價空、adj_method 空",
        d["adj_method"] == "ratio" and abs(d["adj_open"] - 90.0) < 1e-9 and list(d)[:14] == list(V12.INPUT_FIELDS) and list(d)[14:] == ["adj_method", "_flags"]
        and d0["adj_method"] is None and d0["adj_open"] is None, d0["_flags"])
    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        (via / "functional modules" / "VDF").mkdir(parents=True)
        reg = via / "supportive modules" / "registry"
        (reg / "VIA_NumberBooks").mkdir(parents=True)
        names = ["date", "ticker", "open", "low", "high", "close", "volume", "turnover", "day_trade_volume", "day_trade_value", "yf_close", "yf_adj_close"]
        (via / "functional modules" / "VDF" / "VDF_TWEquity_DailyRow_Schema_v0100.json").write_text(json.dumps({"columns": [{"name": n, "zh": n, "dtype": "DOUBLE"} for n in names]}), encoding="utf-8")
        (via / "functional modules" / "VDF" / "VDF_InputUniverse_SSOT_v0100.json").write_text(
            json.dumps({"inputs": [{"id": "IN-01", "group": "S", "zh": "股", "code_regex": "^A$"}, {"id": "IN-02", "group": "E", "zh": "基", "code_regex": "^B$"}]}), encoding="utf-8")
        (reg / "VIA_NumberBooks" / "VIA_NumberBook_FD_v0100.jsonl").write_text("\n".join(json.dumps(
            {"code": "VIA-VDF-FD%03d" % i, "name": n, "sub": "VDF", "source": "functional modules/VDF/VDF_TWEquity_DailyRow_Schema_v0100.json"}) for i, n in enumerate(names, 1)) + "\n", encoding="utf-8")
        r0 = scan(book, via)
        chk("⑥ 裁定冊不在 → YELLOW(照實講找不到,不當成對齊)", r0["ruling"]["lamp"] == "YELLOW" and r0["lamp"] == "YELLOW", r0["ruling"]["state"])
        (reg / "VIA_VDF_TWMarketEndpoints_SSOT_v0100.json").write_text(json.dumps({"adj_ohlc": {"cols": ["adj_open", "adj_high", "adj_low", "adj_close"], "ruled_by": "x"}}), encoding="utf-8")
        r1 = scan(book, via)
        chk("⑦ 裁定四欄 VQG 都有登 + adj_method 有登 → GREEN;15 列", r1["ruling"]["lamp"] == "GREEN" and r1["lamp"] == "GREEN" and len(r1["rows"]) == 15, r1["counts"])
        (reg / "VIA_VDF_TWMarketEndpoints_SSOT_v0101.json").write_text(json.dumps({"adj_ohlc": {"cols": ["adj_open", "adj_high", "adj_low", "adj_close", "adj_vwap"]}}), encoding="utf-8")
        r2 = scan(book, via)
        chk("⑧ 裁定新版多一欄、VQG 沒登 → RED(點名哪一欄)", r2["ruling"]["lamp"] == "RED" and "adj_vwap" in r2["ruling"]["state"], r2["ruling"]["state"])
    prior_ok = cp.returncode == 0
    for l in prior_lines[-3:]:
        print("    前版 " + l.strip(), flush=True)
    if not prior_ok and not prior_lines:
        print("    前版沒有跑起來:" + ((cp.stdout or cp.stderr or "").strip().splitlines() or ["(無輸出)"])[-1][:160], flush=True)
    good = ok == total and prior_ok
    print("[%s] VQG %s selftest · 本版 %d/%d · 前版鏈 v0112 %s" % ("PASS" if good else "FAIL", VERSION_TAIL, ok, total, "PASS" if prior_ok else "FAIL"), flush=True)
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
    if cmd == "fields":
        return fields(argv)
    if cmd == "indicators" and "--check" in argv:
        rc = V11.main(argv)
        return max(rc, fields(["fields", "--check"]))
    if "--help" in argv or "-h" in argv:
        rc = V12.main(argv)
        print("v0113:fields --check / --scan 加上還原方法註記 adj_method 與裁定冊對照", flush=True)
        return rc
    return V12.main(argv)


if __name__ == "__main__":
    sys.exit(main())

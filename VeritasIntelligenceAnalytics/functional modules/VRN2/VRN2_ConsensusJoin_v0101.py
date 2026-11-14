#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ConsensusJoin v0101 — v0100 薄尾(v0100 與共識引擎都一字不改):上櫃股的 YFinance 代號用 .TWO。

桌機 2026-10-29 14:40 RoundAll ⑥f:5274 · 5904 · 8358 · 4966 · 7728 · 6147 · 3264 · 6143 在 Yahoo 全部 404「Quote not found for symbol: ####.TW」。
根因:引擎 def_cnyes_symbol_to_yfinance_ticker() 用鉅亨頁面的 symbol 前綴決定 .TW / .TWO,而鉅亨對上櫃股也回「TWS:####:STOCK」→ 一律 .TW。
⑥e 的 MarketFetch(VDF 身分表:TWSE → .TW · TPEX → .TWO)已經把每個代號的 yfinance_ticker 寫在 market/VRN2_Market_latest.json。
v0101:
  ① run 讀市場冊的 per_ticker / per_file → 代號 → yfinance_ticker 對應表(只收 ####.TW / ####.TWO),寫 consensus/VRN2_YFTickerMap_latest.json。
  ② 引擎改由本檔 --engine-shim 帶起(同一個 Python · 同一個引擎檔 · 參數照舊):載入引擎模組 → 換掉 def_cnyes_symbol_to_yfinance_ticker
     (對應表有這個代號就用它;沒有 → 引擎原本的規則)→ 呼叫引擎自己的 main()。引擎的品質閘 YFINANCE_TICKER_MATCHES_CNYES_MARKET 用同一個函式,前後一致。
  ③ 同日續跑(引擎 checkpoint)的舊資料若是用錯的尾碼抓的(.TW ≠ 對應表的 .TWO)→ 那個代號不沿用、重抓;其他代號照常沿用。
  ④ 沒有市場冊 / 對應表空 → 行為與 v0100 相同。收據多 yf_ticker_map(來源 · 筆數 · 上櫃代號)。
動詞同 v0100:run · join · --selftest;另有內部用的 --engine-shim <引擎> <對應表 json> <引擎參數…>。
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
DISPLAY_NAME = "VRN2_ConsensusJoin"
TAG = "共識合併 v0101"
PRIOR_NAME = "VRN2_ConsensusJoin_v0100.py"
HERE = Path(__file__).resolve().parent
MAP_JSON = "VRN2_YFTickerMap_latest.json"
_YF = re.compile(r"^(\d{4,6})\.(TW|TWO)$")


def _load(path: Path, alias: str):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent.parent / "v146" / "new" / PRIOR_NAME):
        if path.is_file():
            return _load(path, "vrn2_consensus_join_prior_v0100")
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
PRIOR.TAG = TAG


def ticker_map(v2: Path) -> dict:
    """market/VRN2_Market_latest.json → {代號: '####.TW' | '####.TWO'};per_ticker 優先,per_file 補。"""
    try:
        market = json.loads((Path(v2) / "market" / "VRN2_Market_latest.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for rec in list((market.get("per_ticker") or {}).values()) + list((market.get("per_file") or {}).values()):
        m = _YF.match(str((rec or {}).get("yfinance_ticker") or "").strip().upper())
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(0)
    return out


def patch_engine(mod, mapping: dict) -> None:
    """引擎模組:代號 → yfinance 尾碼照對應表;checkpoint 裡用錯尾碼抓的代號不沿用。"""
    native_symbol = mod.def_cnyes_symbol_to_yfinance_ticker
    native_load = mod.def_load_checkpoint_payload

    def symbol_to_ticker(symbol, code):
        base = native_symbol(symbol, code)
        want = mapping.get(mod.def_validate_code(code))
        return mod.def_validate_yfinance_ticker(want) if want and want != base else base

    def load_payload(output_dir, checkpoint, code):
        payload = native_load(output_dir, checkpoint, code)
        want = mapping.get(str(code))
        have = ((payload or {}).get("yfinance") or {}).get("yfinance_ticker")
        if payload is not None and want and have and have != want:
            print("def Resume skip : %s(上次用 %s 抓 · 這次 %s · 重抓)" % (code, have, want), flush=True)
            return None
        return payload

    mod.def_cnyes_symbol_to_yfinance_ticker = symbol_to_ticker
    mod.def_load_checkpoint_payload = load_payload


def engine_shim(argv: list) -> int:
    """--engine-shim <引擎> <對應表 json> <引擎參數…>:同一個 Python 載入引擎 → patch → 引擎自己的 main()。"""
    engine, map_path, rest = argv[0], argv[1], argv[2:]
    mapping = {}
    if map_path and Path(map_path).is_file():
        mapping = {str(k): str(v) for k, v in (json.loads(Path(map_path).read_text(encoding="utf-8")).get("map") or {}).items()}
    sys.argv = [engine] + rest
    mod = _load(Path(engine), "vrn2_consensus_engine_shim")
    patch_engine(mod, mapping)
    if mapping:
        print("def YF map   : %d 代號(上櫃 .TWO %d)· %s" % (len(mapping), sum(1 for v in mapping.values() if v.endswith(".TWO")), map_path), flush=True)
    mod.main()
    return 0


def run(v2: Path, root: Path | None = None, fixtures: list | None = None, timeout: int = 900, engine: str | None = None) -> dict:
    v2 = Path(v2)
    out = v2 / "consensus"
    rec = {"engine_wrapper": "%s %s" % (DISPLAY_NAME, TAG), "verb": "run", "at": now(), "year_n": this_year(), "columns": year_columns()}
    eng = engine_path(root, engine)
    codes = codes_from_basic(v2)
    if os.environ.get("VIA_VRN2_NO_CONSENSUS") == "1":
        rec.update(lamp="GRAY", why="VIA_VRN2_NO_CONSENSUS=1 · 本輪不抓共識")
        return _finish(out, rec)
    if not eng:
        rec.update(lamp="GRAY", why="沒有共識引擎 %s(runtime / functional modules)· 不抓" % ENGINE_GLOB)
        return _finish(out, rec)
    if not codes:
        rec.update(lamp="GRAY", why="基本資料冊沒有 4 碼代號 · 不抓", engine=str(eng))
        return _finish(out, rec)
    py = fetch_python()
    rec.update(engine=str(eng), python=py, codes=codes)
    if not fixtures:
        probe = subprocess.run([py, "-c", "import yfinance; print('ok', yfinance.__version__)"], capture_output=True, text=True, timeout=120)
        if "ok" not in probe.stdout:
            rec.update(lamp="YELLOW", why="擷取環境缺 yfinance(%s)→ 交 VCGC 安裝或用 VDF 包的 via_tw_fetch 環境 · 本輪共識欄留空" % py)
            return _finish(out, rec)
    out.mkdir(parents=True, exist_ok=True)
    mapping = {c: t for c, t in ticker_map(v2).items() if c in codes}
    map_path = out / MAP_JSON
    map_path.write_text(json.dumps({"from": str(v2 / "market" / "VRN2_Market_latest.json"), "at": now(), "map": mapping}, ensure_ascii=False, indent=1), encoding="utf-8")
    rec["yf_ticker_map"] = {"from": "market/VRN2_Market_latest.json", "codes": len(mapping), "tpex": sorted(c for c, t in mapping.items() if t.endswith(".TWO")), "file": str(map_path)}
    cmd = [py, "-X", "utf8", str(Path(__file__).resolve()), "--engine-shim", str(eng), str(map_path), "--codes", ",".join(codes), "--output-dir", str(out), "--skip-unit-tests", "--allow-missing-duckdb"]
    if fixtures:
        cmd += ["--no-resume"]
        for f in fixtures:
            cmd += ["--fixture", str(f)]
    rc, lines = _stream(cmd, eng.parent, timeout)
    gate = next((l.split(":", 1)[1].strip() for l in lines if l.startswith("def Gate")), "")
    rec.update(rc=rc, gate=gate, lines=len(lines), tail=[l[:200] for l in lines[-6:]], yf_404=sorted({m.group(1) for l in lines for m in [re.search(r"symbol: (\d{4,6}\.TWO?)", l)] if m}))
    matrix = out / MATRIX_CSV
    if not matrix.is_file():
        rec.update(lamp="YELLOW", why="引擎沒出矩陣 %s(rc %s · gate %s)· %s" % (MATRIX_CSV, rc, gate or "—", (lines[-1] if lines else "沒有輸出")[:160]))
        return _finish(out, rec)
    per = parse_matrix(matrix)
    got = [c for c in codes if c in per]
    rec.update(per_code=per, codes_got=got, codes_missing=[c for c in codes if c not in per])
    tw = " · 上櫃 .TWO %d" % len(rec["yf_ticker_map"]["tpex"]) if rec["yf_ticker_map"]["tpex"] else ""
    if got and not rec["codes_missing"]:
        rec.update(lamp="GREEN" if rc == 0 else "YELLOW", why="共識 %d / %d 代號 · FactSet 中位數 %d · YFinance 中位數 %d%s · gate %s · rc %s" % (len(got), len(codes), sum(1 for c in got if per[c]["factset_target_median"] is not None), sum(1 for c in got if per[c]["yf_target_median"] is not None), tw, gate or "—", rc))
    elif got:
        rec.update(lamp="YELLOW", why="共識 %d / %d 代號(缺 %s)· YFinance 中位數 %d%s · gate %s · rc %s" % (len(got), len(codes), ",".join(rec["codes_missing"][:8]), sum(1 for c in got if per[c]["yf_target_median"] is not None), tw, gate or "—", rc))
    else:
        rec.update(lamp="YELLOW", why="矩陣裡沒有任何要的代號 · gate %s · rc %s" % (gate or "—", rc))
    return _finish(out, rec)


PRIOR.run = run          # v0100 的 main() / 啟動器 ⑥f 叫的 run 都走本版


def selftest(engine: str | None = None) -> int:
    bad = []

    def chk(label, cond):
        say(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    rc = PRIOR.selftest(engine)                         # v0100 的 ① ~ ⑦(run 已是本版;市場冊沒有 .TWO → 行為同 v0100)
    if rc != 0:
        bad.append("v0100 ① ~ ⑦")
    eng = engine_path(None, engine)
    with tempfile.TemporaryDirectory(prefix="vrn2-cons101-") as td:
        root = Path(td)
        v2 = root / "VIA_Reports" / "vrn2"
        (v2 / "output").mkdir(parents=True)
        (v2 / "market").mkdir()
        json.dump([{"REPORT_DATE": "2025-12-01", "FILENAME": "MS-5274 20251201.pdf", "TICKER": "5274", "BROKER": "MS", "TARGET_PRICE": "6000", "TITLE": "t"},
                   {"REPORT_DATE": "2025-12-02", "FILENAME": "GS-2330 20251202.pdf", "TICKER": "2330", "BROKER": "GS", "TARGET_PRICE": "1500", "TITLE": "t"}], open(v2 / "output" / "VRN2_BasicInfo_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
        json.dump({"per_ticker": {"5274": {"yfinance_ticker": "5274.TWO"}, "2330": {"yfinance_ticker": "2330.TW"}, "0050": {"yfinance_ticker": "bad"}}, "per_file": {}}, open(v2 / "market" / "VRN2_Market_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
        chk("⑧ 對應表:市場冊 per_ticker → 5274 → 5274.TWO · 2330 → 2330.TW · 壞值不收", ticker_map(v2) == {"5274": "5274.TWO", "2330": "2330.TW"})
        if not eng:
            say("[SKIP] 沒有共識引擎檔 · ⑨ ⑩ 只驗對應表")
        else:
            mod = _load(eng, "vrn2_consensus_engine_selftest")
            try:
                native = mod.def_cnyes_symbol_to_yfinance_ticker("TWS:5274:STOCK", "5274")
            except Exception as error:  # noqa: BLE001
                native = "error %s" % error
            patch_engine(mod, {"5274": "5274.TWO"})
            mod_load = mod.def_load_checkpoint_payload
            chk("⑨ 引擎原本:鉅亨 TWS:5274 → 5274.TW(桌機 404 的根因)· patch 後 → 5274.TWO · 2330 照舊 .TW",
                native == "5274.TW" and mod.def_cnyes_symbol_to_yfinance_ticker("TWS:5274:STOCK", "5274") == "5274.TWO" and mod.def_cnyes_symbol_to_yfinance_ticker("TWS:2330:STOCK", "2330") == "2330.TW")
            fx = _fixture(root / "fx5274.json", "5274", "信驊", 5000.0, 6200.0, 6100.0, {2026: 120.0, 2027: 150.0})
            data = json.loads(fx.read_text(encoding="utf-8"))
            data["yfinance_info"]["ticker"] = "5274.TWO"
            data["yfinance_info"]["info"]["symbol"] = "5274.TWO"
            fx.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            fx2 = _fixture(root / "fx2330.json", "2330", "台積電", 1000.0, 1450.0, 1500.0, {2026: 60.0})
            r = run(v2, root, fixtures=[fx, fx2], timeout=600)
            pc = r.get("per_code") or {}
            chk("⑩ 引擎實跑(離線 fixture · Yahoo 代號 5274.TWO):5274 YFinance 中位數 6100 · FactSet 6200 · 收據 yf_ticker_map 上櫃 [5274] · 對應表檔在 consensus/",
                pc.get("5274", {}).get("yf_target_median") == 6100.0 and pc.get("5274", {}).get("factset_target_median") == 6200.0 and r.get("yf_ticker_map", {}).get("tpex") == ["5274"] and (v2 / "consensus" / MAP_JSON).is_file())
            say("    引擎 rc %s · gate %s · %s" % (r.get("rc"), r.get("gate"), r.get("why")))
            out = v2 / "consensus"
            cp = json.loads((out / "consensus_checkpoint.json").read_text(encoding="utf-8"))
            stale = mod_load(str(out), cp, "5274")
            if stale is not None:
                stale["yfinance"]["yfinance_ticker"] = "5274.TW"
                p = mod.def_checkpoint_payload_path(str(out), cp.get("input_hash"), "5274")
                Path(p).write_text(json.dumps(stale, ensure_ascii=False), encoding="utf-8")
                cp["completed"]["5274"]["payload_sha256"] = mod.def_sha256_file(p)
            mod2 = _load(eng, "vrn2_consensus_engine_selftest2")
            native_load = mod2.def_load_checkpoint_payload
            patch_engine(mod2, {"5274": "5274.TWO", "2330": "2330.TW"})
            chk("⑪ 同日續跑:checkpoint 裡 5274 是用 .TW 抓的 → 不沿用(重抓)· 2330 用對的 .TW → 照常沿用",
                stale is not None and native_load(str(out), cp, "5274") is not None and mod2.def_load_checkpoint_payload(str(out), cp, "5274") is None and mod2.def_load_checkpoint_payload(str(out), cp, "2330") is not None)
    n = 11
    say("[%s] %s %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, n, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--engine-shim"]:
        return engine_shim(argv[1:])
    if "--selftest" in argv:
        return selftest(argv[argv.index("--engine") + 1] if "--engine" in argv and argv.index("--engine") + 1 < len(argv) else None)
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())

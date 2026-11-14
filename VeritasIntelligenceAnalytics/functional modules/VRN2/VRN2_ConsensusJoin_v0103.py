#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ConsensusJoin v0103 — v0102 薄尾(v0102 / v0101 / v0100 與共識引擎都一字不改):再跑一次不再整批重抓 · 一時抓不到的代號先重試。

桌機 2026-10-30 20:09(Handle-All v0101 → RoundAll v0109 · 啟動器 v0153)⑥f:第一次 43 檔,6933 / 7728 / 4171 回 404(鉅亨沒有 FactSet 頁)
→ v0102 拿掉這三檔再跑 → 第二次 Run ID 換新、40 檔全部「Fetch」重抓(不是續跑)→ 8358 / 2891 這次拿到的頁面沒有 __NEXT_DATA__
(ASSIGNED_JSON_NOT_FOUND)→ gate FAIL_CLOSED · rc 1 · 收尾 VRN-2 2 項。這兩檔第一次是抓到的。
根因:引擎的 checkpoint 雜湊含代號清單(def_compute_pipeline_input_hash:codes · 日期 · 模式)→ 清單一變就不是同一份 checkpoint →
  v0102 說的「其他代號續跑沿用」沒有發生;40 檔短時間第二輪上網,鉅亨偶爾回沒有資料的頁。(同一天 14:36 那輪 7728 有頁、20:09 回 404:404 也會一時的。)
v0103:
  ① 每次跑引擎前(第一次 · 重試 · 拿掉代號後),若 consensus_checkpoint.json 是「今天」的、但代號清單不同 → 用引擎自己的函式
     (雜湊 · payload 路徑 · sha256 · 封存)把它抓到的 payload 搬進這次清單的 checkpoint → 引擎「Resume」沿用、只抓沒抓過的。
     不是今天的 → 不搬(照引擎原本一天一抓)。離線 fixture(引擎 --no-resume)→ 不搬。
  ② 品質閘 FAIL_CLOSED 的不過列分三種:鉅亨沒有 FactSet 頁(404)· 一時抓不到(FETCH_PIPELINE:ASSIGNED_JSON_NOT_FOUND / NEXT_DATA /
     HTTP_GET_FAILED / 逾時 / 429 / 5xx / 連線中斷)· 其他。有「其他」→ 照 v0101 FAIL_CLOSED 原樣(VRN-2 的事)。
     只有 404 / 一時抓不到 → 等一下(VIA_VRN2_CONSENSUS_RETRY_WAIT 秒,預設 30 · 第 n 次 × n)用同一份清單再跑(續跑:只重抓沒抓到的)·
     一時抓不到最多 VIA_VRN2_CONSENSUS_RETRIES 次(預設 2;0 = 不重試)· 只有 404 → 1 次。
  ③ 重試後仍不過 → 404 的進 no_coverage(同 v0102)· 一時抓不到的進 source_gap(代號 · 最後一次錯誤 · 抓了幾次)→ 拿掉再跑(① 搬過 = 不上網)。
     有 source_gap → 燈不會是綠(YELLOW:鉅亨這次沒給資料 · 下輪再抓 · 負責方 資料源)。收據多 retries · seed · source_gap。
  ④ join:Combined 裡沒覆蓋 / 暫缺的列,CONSENSUS 寫那一檔自己的原因,不再抄整批的摘要(v0100 抄整批 why,裡面有
     「鉅亨沒有 FactSet 頁(404)不納入閘:…」→ 收尾頁把 8358 / 2891 也算成 404)。
  ⑤ 引擎這次沒有產出(rc ≠ 0 · 沒有 Gate 行 · 例:43 檔都沒抓到 NO_PAYLOAD_FETCHED)而矩陣檔是上次的 → v0101 會把上次的矩陣讀成「共識 13 / 13」;
     v0103 不沿用:per_code 清空 · 黃 · engine_no_output(rc · 最後一行)· why 寫「共識引擎這次沒有產出」(沙盒整輪測出來的)。
動詞同 v0102:run · join · --selftest · --engine-shim。
"""
from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time

VERSION = "v0103"
DISPLAY_NAME = "VRN2_ConsensusJoin"
TAG = "共識合併 v0103"
PRIOR_NAME = "VRN2_ConsensusJoin_v0102.py"
HERE = Path(__file__).resolve().parent
_TRANSIENT = re.compile(r"ASSIGNED_JSON_NOT_FOUND|NEXT_DATA_NOT_OBJECT|PAGE_PROPS_NOT_OBJECT|JSON_DECODE_FAILED|HTTP_GET_FAILED|HTTP_STATUS_(?:408|425|429|5\d\d)"
                        r"|HTTP Error (?:408|425|429|5\d\d)|timed out|[Tt]imeout|Connection ?(?:[Rr]eset|aborted|refused)|RemoteDisconnected|IncompleteRead|Temporary failure")
_PERMANENT = re.compile(r"HTTP Error (?:400|401|403|404|410)\b")
NO_PAGE_TEXT = "鉅亨沒有 FactSet 頁(404)"
GAP_TEXT = "鉅亨這次沒給資料(抓了 %d 次 · 下輪再抓)"


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
    return _load(path, "vrn2_consensus_join_prior_v0102")


PRIOR = _prior()                       # v0102(它再載 v0101 → v0100)
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0101 = PRIOR.PRIOR
V0100 = V0101.PRIOR
for _mod in (PRIOR, V0101, V0100):
    _mod.TAG = TAG
_v0101_run = PRIOR._v0101_run          # 真正帶引擎跑的那一支(v0101 的 run)
_native_codes = PRIOR._native_codes
_v0102_run = PRIOR.run
_v0102_join = PRIOR.join


def _say(text: str) -> None:
    print("    [⑥f] [計] " + text, flush=True)


def _env_num(name: str, default: float) -> float:
    try:
        return max(0.0, float(os.environ.get(name, default)))
    except ValueError:
        return default


def classify(rows: list, codes: list) -> tuple:
    """品質閘不過的列 → ({404 代號: 原因}, {一時抓不到的代號: 原因}, [其他列])。"""
    nopage, transient, other = {}, {}, []
    for r in rows:
        code = str(r.get("code") or "").strip()
        text = "%s %s" % (r.get("actual") or "", r.get("note") or "")
        if code in codes and _NO_PAGE.search(text):
            nopage[code] = str(r.get("actual") or "")[:160]
        elif code in codes and str(r.get("check_id") or "") == "FETCH_PIPELINE" and _TRANSIENT.search(text) and not _PERMANENT.search(text):
            transient[code] = str(r.get("actual") or "")[:160]
        else:
            other.append(r)
    return nopage, transient, other


def _kinds(nopage: dict, transient: dict) -> str:
    parts = []
    if nopage:
        parts.append("%s:%s" % (NO_PAGE_TEXT, ",".join(sorted(nopage))))
    if transient:
        parts.append("一時抓不到:%s(%s)" % (",".join(sorted(transient)), next(iter(transient.values()))[:60]))
    return " · ".join(parts) or "—"


def seed_checkpoint(out: Path, engine, keep: list) -> dict:
    """跑引擎前:consensus_checkpoint.json 是今天的、代號清單卻不同 → 用引擎自己的函式把抓到的 payload 搬進 keep 這份清單的 checkpoint
    (引擎續跑就沿用、不上網)。回 {seeded, of, from, to} 或 {seeded: 0, why}。只搬引擎 sha256 對得上的;任何一步不行 → 不搬(引擎照常抓)。"""
    try:
        mod = _load(Path(engine), "vrn2_consensus_engine_seed_v0103")
        cp_path = Path(out) / mod.OUTPUT_CHECKPOINT
        old = mod.def_load_json_file(cp_path, default={}) or {}
        if not old.get("input_hash") or old.get("schema_version") != mod.SCHEMA_VERSION:
            return {"seeded": 0, "why": "沒有可沿用的 checkpoint"}
        codes = mod.def_validate_codes(mod.def_parse_codes_text(",".join(keep)))
        as_of = mod.def_pipeline_as_of_date({})
        if old.get("as_of_date") != as_of:
            return {"seeded": 0, "why": "checkpoint 是 %s 的 · 今天 %s 照常抓" % (old.get("as_of_date"), as_of)}
        new_hash = mod.def_compute_pipeline_input_hash(codes, fixture_map={}, as_of_date=as_of)
        if new_hash == old.get("input_hash"):
            return {"seeded": 0, "why": "同一份清單 · 引擎自己續跑"}
        new = {"engine": mod.ENGINE_NAME, "engine_version": mod.ENGINE_VERSION, "schema_version": mod.SCHEMA_VERSION, "run_id": mod.def_build_run_id(),
               "input_hash": new_hash, "as_of_date": as_of, "codes": list(codes), "status": "IN_PROGRESS", "completed": {}, "failed": {},
               "created_at_utc": mod.def_now_utc_iso(), "updated_at_utc": mod.def_now_utc_iso(), "seeded_by": "%s %s" % (DISPLAY_NAME, VERSION),
               "seeded_from": str(old.get("input_hash"))[:16]}
        moved = []
        for code in codes:
            try:
                payload = mod.def_load_checkpoint_payload(str(out), old, code)
            except Exception:  # noqa: BLE001  壞的 / 對不上的 payload 不搬
                payload = None
            if payload is not None:
                mod.def_save_checkpoint_payload(str(out), new, payload)
                moved.append(code)
        if not moved:
            return {"seeded": 0, "why": "今天的 checkpoint 沒有這份清單用得上的 payload"}
        mod.def_archive_checkpoint(cp_path, old)
        mod.def_save_checkpoint_state(cp_path, new)
        return {"seeded": len(moved), "of": len(codes), "from": new["seeded_from"], "to": new_hash[:16]}
    except Exception as error:  # noqa: BLE001
        return {"seeded": 0, "why": "%s: %s" % (type(error).__name__, str(error)[:160])}


def _engine_pass(v2: Path, root, fixtures, timeout, engine, drop=None) -> tuple:
    """跑一次引擎(drop = 這次不納入的代號);跑之前先 ① 搬 checkpoint。回 (收據, 搬了什麼)。"""
    drop = dict(drop or {})
    codes = [c for c in _native_codes(v2) if c not in drop]
    eng = engine_path(root, engine)
    seed = {"seeded": 0, "why": "離線 fixture(引擎 --no-resume)"} if fixtures else ({"seeded": 0, "why": "沒有引擎 / 代號"} if not (eng and codes) else seed_checkpoint(Path(v2) / "consensus", eng, codes))
    if seed.get("seeded"):
        _say("今天的 checkpoint 是別份代號清單 → 抓到的 %d / %d 份搬進這次的(引擎續跑沿用 · 只抓沒抓過的)" % (seed["seeded"], seed["of"]))
    t0 = time.time()
    V0101.codes_from_basic = lambda path: [c for c in _native_codes(path) if c not in drop]
    try:
        rec = _v0101_run(v2, root, fixtures, timeout, engine)
    finally:
        V0101.codes_from_basic = _native_codes
    matrix = Path(v2) / "consensus" / MATRIX_CSV
    if rec.get("rc") not in (None, 0) and not str(rec.get("gate") or "") and matrix.is_file() and matrix.stat().st_mtime < t0 - 0.5:   # ⑤ 上次的矩陣不算這次的
        last = str((rec.get("tail") or [""])[-1])
        rec.update(per_code={}, codes_got=[], codes_missing=list(rec.get("codes") or []), lamp="YELLOW", engine_no_output={"rc": rec.get("rc"), "last": last[:200]},
                   why="共識引擎這次沒有產出(rc %s · %s)· 上次的矩陣(%s)不算這次的" % (rec.get("rc"), last[:120], time.strftime("%Y-%m-%d %H:%M", time.localtime(matrix.stat().st_mtime))))
        rec = _finish(Path(v2) / "consensus", rec)
    return rec, seed


def _closed(rec: dict) -> bool:
    return str(rec.get("gate", "")).upper() == "FAIL_CLOSED"


def run(v2: Path, root: Path | None = None, fixtures: list | None = None, timeout: int = 900, engine: str | None = None) -> dict:
    v2 = Path(v2)
    out = v2 / "consensus"
    rec, seed = _engine_pass(v2, root, fixtures, timeout, engine)
    seeds = [seed]
    if not _closed(rec):
        rec.update(seed=seeds, retries=[])
        return _finish(out, rec)
    codes = list(rec.get("codes") or [])
    first = {k: rec.get(k) for k in ("gate", "rc", "why")}
    nopage, transient, other = classify(quality_fails(out), codes)
    first_kinds = _kinds(nopage, transient)
    tries, limit = [], int(_env_num("VIA_VRN2_CONSENSUS_RETRIES", 2))
    while (nopage or transient) and not other and len(tries) < (limit if transient else min(1, limit)):
        wait = _env_num("VIA_VRN2_CONSENSUS_RETRY_WAIT", 30) * (len(tries) + 1)
        redo = sorted(set(nopage) | set(transient))
        _say("品質閘 FAIL_CLOSED · %s → 等 %d 秒 · 同一份清單再跑一次(續跑:抓到的沿用 · 只重抓 %s)· 第 %d 次" % (_kinds(nopage, transient), wait, ",".join(redo), len(tries) + 1))
        time.sleep(wait)
        rec, seed = _engine_pass(v2, root, fixtures, timeout, engine)
        seeds.append(seed)
        tries.append({"attempt": len(tries) + 1, "wait_s": wait, "refetch": redo, "gate": rec.get("gate"), "rc": rec.get("rc")})
        if not _closed(rec):
            break
        nopage, transient, other = classify(quality_fails(out), codes)
    if not _closed(rec):
        rec.update(no_coverage={}, source_gap={}, first_gate=first, retries=tries, seed=seeds)
        rec["why"] = "%s · 第一次閘 FAIL_CLOSED(%s)· 重跑 %d 次後過閘" % (rec.get("why", ""), first_kinds, len(tries))
        return _finish(out, rec)
    if other or not (nopage or transient) or len(nopage) + len(transient) >= len(codes):
        rec.update(no_coverage={}, source_gap={}, first_gate=first, retries=tries, seed=seeds)   # 有別的不過(或全部都沒有)→ 照 FAIL_CLOSED
        return _finish(out, rec)
    drop = dict(nopage, **transient)
    _say("品質閘 FAIL_CLOSED 只因 %s → 這些代號不納入、同一個引擎再跑一次" % _kinds(nopage, transient))
    rec, seed = _engine_pass(v2, root, fixtures, timeout, engine, drop)
    seeds.append(seed)
    gap = {c: {"why": why, "tries": len(tries) + 1} for c, why in transient.items()}
    rec.update(no_coverage=nopage, source_gap=gap, first_gate=first, codes_all=codes, retries=tries, seed=seeds)
    parts = [str(rec.get("why", ""))]
    if nopage:
        parts.append("%s不納入閘:%s" % (NO_PAGE_TEXT, ",".join(sorted(nopage))))
    if gap:
        parts.append("鉅亨這次沒給資料(抓了 %d 次)暫不納入閘:%s" % (len(tries) + 1, ",".join(sorted(gap))))
    rec["why"] = " · ".join(p for p in parts if p)
    if gap and rec.get("lamp") == "GREEN":
        rec["lamp"] = "YELLOW"
    return _finish(out, rec)


_SEG = re.compile(r"CONSENSUS: 缺:.*?(?= \| |$)")


def join(v2: Path) -> dict:
    """v0102 的 join;沒覆蓋(404)/ 暫缺(鉅亨這次沒給)的代號那幾列,CONSENSUS 寫它自己的原因(不抄整批摘要)。"""
    got = _v0102_join(v2)
    try:
        cons = json.loads((Path(v2) / "consensus" / CONSENSUS_JSON).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return got
    nopage, gap = cons.get("no_coverage") or {}, cons.get("source_gap") or {}
    if not (nopage or gap):
        return got
    path = Path(v2) / "output" / "VRN2_Combined_latest.json"
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return got
    hit = 0
    for row in rows:
        code = str(row.get("TICKER") or "")[:4]
        if code in nopage:
            why = NO_PAGE_TEXT
        elif code in gap:
            why = GAP_TEXT % int((gap[code] or {}).get("tries") or 1)
        else:
            continue
        st = str(row.get("STATUS") or "")
        if st.endswith(" · " + NO_PAGE_TEXT):                      # v0102 加在尾端的那一段收進 CONSENSUS
            st = st[: -len(" · " + NO_PAGE_TEXT)]
        new = _SEG.sub(lambda m: "CONSENSUS: 缺:" + why, st, count=1) if _SEG.search(st) else (st + " | CONSENSUS: 缺:" + why).strip(" |")
        if new != row.get("STATUS"):
            row["STATUS"] = new
            hit += 1
    if hit:
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        csv_path = path.with_suffix(".csv")
        if rows and csv_path.is_file():
            with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
    got["consensus_reason_rows"] = hit
    return got


def _wire(run_fn, join_fn) -> None:
    for mod in (PRIOR, V0101, V0100):                  # 啟動器叫的 run / join 與 CLI(v0100 main 用自己模組的名字)都走同一支
        mod.run, mod.join = run_fn, join_fn


_wire(run, join)


class _FakeEngine:
    """自測用:照引擎「真的」checkpoint 規則(引擎自己的 def_initialize_checkpoint / save / load)跑,抓網頁換成劇本。"""

    def __init__(self, mod, script):
        self.mod, self.script, self.fetches = mod, script, {}

    def __call__(self, v2, root=None, fixtures=None, timeout=900, engine=None):
        mod, out = self.mod, Path(v2) / "consensus"
        codes = V0101.codes_from_basic(v2)
        _, cp = mod.def_initialize_checkpoint(str(out), codes, fixture_map={}, resume=True)
        cp_path = out / mod.OUTPUT_CHECKPOINT
        fails = []
        for code in codes:
            if code in cp.get("completed", {}) and mod.def_load_checkpoint_payload(str(out), cp, code) is not None:
                continue
            n = self.fetches[code] = self.fetches.get(code, 0) + 1
            err = self.script(code, n)
            if err:
                fails.append({"code": code, "check_id": "FETCH_PIPELINE", "actual": err, "expected": "successful fetch", "status": "FAIL", "severity": "FAIL", "note": "Ticker fetch failed."})
                cp.setdefault("failed", {})[code] = {"error": err}
            else:
                mod.def_save_checkpoint_payload(str(out), cp, {"code": code, "fetched": n})
            mod.def_save_checkpoint_state(cp_path, cp)
        with (out / QUALITY_CSV).open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["code", "check_id", "actual", "expected", "status", "severity", "note"])
            w.writeheader()
            w.writerows(fails + [{"code": c, "check_id": "HTTP_PAGE_200", "actual": "200", "expected": "200", "status": "PASS", "severity": "FAIL", "note": ""} for c in codes if c not in {f["code"] for f in fails}])
        gate = "FAIL_CLOSED" if fails else "PASS"
        return _finish(out, {"gate": gate, "rc": 1 if fails else 0, "codes": codes, "lamp": "YELLOW" if fails else "GREEN", "engine": str(engine),
                             "why": "共識 %d / %d 代號 · gate %s" % (len(codes) - len(fails), len(codes), gate)})


def _basic(v2: Path, codes: list) -> None:
    (v2 / "output").mkdir(parents=True, exist_ok=True)
    (v2 / "consensus").mkdir(parents=True, exist_ok=True)
    (v2 / "output" / "VRN2_BasicInfo_latest.json").write_text(json.dumps([{"FILENAME": "r%s.pdf" % c, "TICKER": c} for c in codes]), encoding="utf-8")


def selftest(engine: str | None = None) -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    _wire(_v0102_run, _v0102_join)                      # 前版自測照前版自己的接線跑
    try:
        rc = PRIOR.selftest(engine)
    finally:
        _wire(run, join)
    chk("① v0102 自測(含 v0101 · v0100 · 引擎離線實跑)照過", rc == 0)
    rows = [{"code": "6933", "check_id": "FETCH_PIPELINE", "actual": "TARGET_PRICE_STATUS_NOT_200: statusCode=404 message=頁面或商品不存在", "status": "FAIL"},
            {"code": "8358", "check_id": "FETCH_PIPELINE", "actual": "ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__", "status": "FAIL"},
            {"code": "2891", "check_id": "FETCH_PIPELINE", "actual": "HTTP_GET_FAILED: url=x error=<urlopen error [Errno 104] Connection reset by peer>", "status": "FAIL"},
            {"code": "1234", "check_id": "FETCH_PIPELINE", "actual": "HTTP_GET_FAILED: url=x error=HTTP Error 404: Not Found", "status": "FAIL"},
            {"code": "2330", "check_id": "HTTP_PAGE_200", "actual": "500", "status": "FAIL"}]
    np_, tr_, ot_ = classify(rows, ["6933", "8358", "2891", "1234", "2330"])
    chk("② 分類:6933 404 = 沒有 FactSet 頁 · 8358 沒有 __NEXT_DATA__ / 2891 連線中斷 = 一時抓不到 · 1234 HTTP 404 / 2330 品質列 = 其他",
        sorted(np_) == ["6933"] and sorted(tr_) == ["2891", "8358"] and sorted(r["code"] for r in ot_) == ["1234", "2330"])
    eng = engine_path(None, engine)
    if not eng:
        print("[SKIP] 沒有共識引擎檔 · ③ ~ ⑫ 要引擎自己的 checkpoint 函式", flush=True)
        bad.append("沒有引擎")
    saved_env = {k: os.environ.get(k) for k in ("VIA_VRN2_CONSENSUS_RETRY_WAIT", "VIA_VRN2_CONSENSUS_RETRIES", "VIA_VRN2_NO_CONSENSUS")}
    os.environ["VIA_VRN2_CONSENSUS_RETRY_WAIT"] = "0"
    os.environ.pop("VIA_VRN2_NO_CONSENSUS", None)
    saved_run = globals()["_v0101_run"]
    try:
        with tempfile.TemporaryDirectory(prefix="vrn2-cj103-") as temporary:
            base = Path(temporary)
            mod = _load(eng, "vrn2_consensus_engine_selftest_v0103") if eng else None
            if mod:
                out = base / "seed"
                cp_path, cp = mod.def_initialize_checkpoint(str(out), ["2330", "6933", "8358"], fixture_map={}, resume=True)
                for c in ("2330", "8358"):
                    mod.def_save_checkpoint_payload(str(out), cp, {"code": c, "x": 1})
                mod.def_save_checkpoint_state(cp_path, cp)
                got = seed_checkpoint(out, eng, ["2330", "8358"])
                mod2 = _load(eng, "vrn2_consensus_engine_selftest_v0103b")
                _, again = mod2.def_initialize_checkpoint(str(out), ["2330", "8358"], fixture_map={}, resume=True)
                chk("③ 搬 checkpoint:今天的 [2330,6933,8358] → [2330,8358] 搬 2 份 · 引擎自己的 def_initialize_checkpoint 認它可續跑 · 兩份 payload 讀得回 · 舊的封存",
                    got.get("seeded") == 2 and again.get("seeded_by") == "%s %s" % (DISPLAY_NAME, VERSION) and all(mod2.def_load_checkpoint_payload(str(out), again, c) for c in ("2330", "8358"))
                    and any((out / "consensus_checkpoint_archive").glob("checkpoint_*.json")))
                stale = dict(again, as_of_date="2026-01-01")
                (out / mod.OUTPUT_CHECKPOINT).write_text(json.dumps(stale), encoding="utf-8")
                chk("④ 不是今天的 checkpoint → 不搬(照引擎一天一抓)", seed_checkpoint(out, eng, ["2330"]).get("seeded") == 0)

                def scenario(name, codes, script, retries="2"):
                    v2 = base / name / "vrn2"
                    _basic(v2, codes)
                    os.environ["VIA_VRN2_CONSENSUS_RETRIES"] = retries
                    fake = _FakeEngine(mod, script)
                    globals()["_v0101_run"] = fake
                    try:
                        rec = run(v2, None, None, 60, str(eng))
                    finally:
                        globals()["_v0101_run"] = saved_run
                    return rec, fake.fetches, v2
                desk = ["2330", "6933", "8358", "2891", "4171"]

                def desktop(code, n):                       # 桌機 20:09:6933 / 4171 404 · 8358 / 2891 第一次有 · 第二次起沒有 __NEXT_DATA__
                    if code in ("6933", "4171"):
                        return "TARGET_PRICE_STATUS_NOT_200: statusCode=404 message=頁面或商品不存在"
                    return "ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__" if code in ("8358", "2891") and n > 1 else ""
                rec, fetches, v2a = scenario("desk", desk, desktop)
                chk("⑤ 桌機 20:09 重演:404 重試 1 次 → 拿掉 6933 / 4171 再跑 → 8358 / 2891 不再上網(沿用第一次)→ PASS · 綠 · no_coverage 2 · source_gap 0",
                    rec.get("gate") == "PASS" and rec.get("lamp") == "GREEN" and sorted(rec.get("no_coverage") or {}) == ["4171", "6933"] and not rec.get("source_gap")
                    and fetches == {"2330": 1, "6933": 2, "8358": 1, "2891": 1, "4171": 2} and len(rec.get("retries") or []) == 1 and any(s.get("seeded") for s in rec.get("seed") or []))
                v2b = base / "desk102" / "vrn2"
                _basic(v2b, desk)
                fake = _FakeEngine(mod, desktop)
                saved102 = (PRIOR._v0101_run, PRIOR._native_codes)
                PRIOR._v0101_run = fake
                _wire(_v0102_run, _v0102_join)
                try:
                    rec102 = _v0102_run(v2b)
                finally:
                    _wire(run, join)
                    PRIOR._v0101_run, PRIOR._native_codes = saved102
                chk("⑥ 同一劇本給 v0102:第二次清單一變 checkpoint 對不上 → 8358 / 2891 重抓 → FAIL_CLOSED(桌機的樣子 · v0103 才修)",
                    rec102.get("gate") == "FAIL_CLOSED" and fake.fetches.get("8358") == 2 and fake.fetches.get("2891") == 2)
                rec, fetches, _ = scenario("blip", ["2330", "8358", "2891"], lambda c, n: "ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__" if c == "8358" and n == 1 else "")
                chk("⑦ 一時抓不到:8358 第一次沒有 __NEXT_DATA__ · 第二次有 → 重試 1 次就過閘 · 只重抓 8358 · 綠",
                    rec.get("gate") == "PASS" and rec.get("lamp") == "GREEN" and fetches == {"2330": 1, "8358": 2, "2891": 1} and len(rec.get("retries") or []) == 1 and "重跑 1 次後過閘" in rec.get("why", ""))
                rec, fetches, v2c = scenario("gap", ["2330", "8358", "2891"], lambda c, n: "ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__" if c == "2891" else "")
                chk("⑧ 一直抓不到:2891 抓 3 次(重試 2 次)仍沒有 → source_gap · 拿掉再跑不上網 → PASS 但黃(鉅亨這次沒給)",
                    rec.get("gate") == "PASS" and rec.get("lamp") == "YELLOW" and (rec.get("source_gap") or {}).get("2891", {}).get("tries") == 3 and fetches == {"2330": 1, "8358": 1, "2891": 3}
                    and "暫不納入閘:2891" in rec.get("why", ""))
                rec, fetches, _ = scenario("other", ["2330", "1234"], lambda c, n: "HTTP_GET_FAILED: url=x error=HTTP Error 404: Not Found" if c == "1234" else "")
                chk("⑨ 別的不過(HTTP 404 網頁本身不在)→ 不重試、不拿掉 · FAIL_CLOSED 原樣(VRN-2 的事)",
                    rec.get("gate") == "FAIL_CLOSED" and fetches == {"2330": 1, "1234": 1} and rec.get("retries") == [] and rec.get("no_coverage") == {} and rec.get("source_gap") == {})
                (v2c / "output" / "VRN2_Combined_latest.json").write_text(json.dumps([
                    {"TICKER": "2891", "STATUS": "TARGET_PRICE(ADJ): x | CONSENSUS: 缺:共識 2 / 2 代號 · 鉅亨沒有 FactSet 頁(404)不納入閘:6933 | BASIC: B"},
                    {"TICKER": "6933", "STATUS": "CONSENSUS: 缺:共識 2 / 2 代號 · 鉅亨沒有 FactSet 頁(404)不納入閘:6933 | BASIC: B · 鉅亨沒有 FactSet 頁(404)"},
                    {"TICKER": "2330", "STATUS": "CONSENSUS: FactSet(鉅亨)5 位 | BASIC: B"}], ensure_ascii=False), encoding="utf-8")
                cons = json.loads((v2c / "consensus" / CONSENSUS_JSON).read_text(encoding="utf-8"))
                cons["no_coverage"] = {"6933": "404"}
                (v2c / "consensus" / CONSENSUS_JSON).write_text(json.dumps(cons, ensure_ascii=False), encoding="utf-8")
                saved_join = globals()["_v0102_join"]
                globals()["_v0102_join"] = lambda path: {"lamp": "GREEN"}
                try:
                    got = join(v2c)
                finally:
                    globals()["_v0102_join"] = saved_join
                comb = json.loads((v2c / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))
                chk("⑩ join:2891 寫「鉅亨這次沒給資料(抓了 3 次)」· 6933 寫「鉅亨沒有 FactSet 頁(404)」· 不再抄整批摘要 · 2330 不動",
                    got.get("consensus_reason_rows") == 2 and comb[0]["STATUS"] == "TARGET_PRICE(ADJ): x | CONSENSUS: 缺:" + GAP_TEXT % 3 + " | BASIC: B"
                    and comb[1]["STATUS"] == "CONSENSUS: 缺:" + NO_PAGE_TEXT + " | BASIC: B" and comb[2]["STATUS"] == "CONSENSUS: FactSet(鉅亨)5 位 | BASIC: B")
                fx = [_fixture(base / ("fx%s.json" % c), c, c, 100.0, 120.0, 118.0, {2026: 5.0}) for c in ("2330", "5274")]
                today = mod.def_pipeline_as_of_date({})
                for f in fx:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    data["captured_at_utc"] = data["yfinance_info"]["captured_at_utc"] = today + "T02:00:00+00:00"
                    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                v2e = base / "e2e" / "VIA_Reports" / "vrn2"
                _basic(v2e, ["2330", "5274"])
                os.environ["VIA_VRN2_CONSENSUS_RETRIES"] = "1"
                offline = run(v2e, None, fx, 600, str(eng))
                _basic(v2e, ["2330", "5274", "6933"])
                stub = base / "yfstub" / "yfinance"
                stub.mkdir(parents=True)
                (stub / "__init__.py").write_text("__version__ = '0+selftest-stub'\n\ndef Ticker(*a, **k):\n    raise RuntimeError('SELFTEST_STUB_NO_NETWORK')\n", encoding="utf-8")
                net = {k: os.environ.get(k) for k in ("PYTHONPATH", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "NO_PROXY", "no_proxy", "VIA_FETCH_PY")}
                os.environ.update(PYTHONPATH=str(stub.parent), HTTPS_PROXY="http://127.0.0.1:9", https_proxy="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9", http_proxy="http://127.0.0.1:9", NO_PROXY="", no_proxy="",
                                  VIA_FETCH_PY=sys.executable)
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):                  # 引擎的輸出收起來(中間兩次閘 FAIL_CLOSED 是預期的 · 不印它的例外堆疊)
                        live = run(v2e, None, None, 600, str(eng))
                finally:
                    for k, v in net.items():
                        os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
                lines = buf.getvalue().splitlines()
                print("    引擎實跑:離線 gate %s · 即時 gate %s · rc %s · 引擎輸出 %d 行(收起來)· Resume %d · Fetch %d · 抓不到 %d · 閘 %s" % (
                    offline.get("gate"), live.get("gate"), live.get("rc"), len(lines), sum("def Resume [" in l for l in lines), sum("def Fetch [" in l for l in lines),
                    sum("] [FAIL] " in l for l in lines), " / ".join(l.split(":", 1)[1].strip() for l in lines if "def Gate" in l)), flush=True)
                if live.get("lamp") != "YELLOW" or sorted(live.get("source_gap") or {}) != ["6933"]:
                    print("\n".join(lines[-40:]), flush=True)
                chk("⑪ 引擎實跑(不連網:代理指到關著的埠 · yfinance 用空殼):離線抓的 2330 / 5274 搬進即時清單 [2330,5274,6933] → 引擎 Resume 沿用 ·"
                    " 6933 連不上 = 一時抓不到 → 重試 1 次 → 拿掉再跑 → 引擎自己的閘過 · 黃 · source_gap 6933",
                    offline.get("gate") in ("PASS", "PASS_WITH_WARNINGS") and live.get("gate") in ("PASS", "PASS_WITH_WARNINGS") and live.get("rc") == 0 and live.get("lamp") == "YELLOW"
                    and sorted(live.get("source_gap") or {}) == ["6933"] and sorted(live.get("codes_got") or []) == ["2330", "5274"] and any(s.get("seeded") == 2 for s in live.get("seed") or []))
                v2s = base / "stale" / "vrn2"
                _basic(v2s, ["2330", "3661"])
                (v2s / "consensus" / MATRIX_CSV).write_text("code\n2330\n", encoding="utf-8")
                os.utime(v2s / "consensus" / MATRIX_CSV, (time.time() - 86400, time.time() - 86400))
                globals()["_v0101_run"] = lambda *a, **k: {"rc": 1, "gate": "", "codes": ["2330", "3661"], "per_code": {"2330": {"factset_target_median": 1.0}}, "codes_got": ["2330"], "codes_missing": ["3661"],
                                                           "lamp": "YELLOW", "why": "共識 1 / 2 代號(缺 3661)· gate — · rc 1", "tail": ["RuntimeError: NO_PAYLOAD_FETCHED: [...]"], "engine": str(eng)}
                try:
                    stale = run(v2s, None, None, 60, str(eng))
                finally:
                    globals()["_v0101_run"] = saved_run
                chk("⑫ 引擎這次沒有產出(rc 1 · 沒有 Gate 行 · NO_PAYLOAD_FETCHED)而矩陣是昨天的 → 不沿用:per_code 清空 · 黃 · engine_no_output · 「共識引擎這次沒有產出」",
                    stale.get("per_code") == {} and stale.get("codes_got") == [] and stale.get("lamp") == "YELLOW" and (stale.get("engine_no_output") or {}).get("rc") == 1 and "共識引擎這次沒有產出" in stale.get("why", ""))
    finally:
        globals()["_v0101_run"] = saved_run
        for k, v in saved_env.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    chk("⑬ 啟動器叫的 run / join 與 CLI 的 run / join 都是本版(v0102 · v0101 · v0100 的模組都指過來)",
        all(m.run is run and m.join is join for m in (PRIOR, V0101, V0100)))
    print("[%s] %s %s --selftest · 13 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest(argv[1] if len(argv) > 1 else None)
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())

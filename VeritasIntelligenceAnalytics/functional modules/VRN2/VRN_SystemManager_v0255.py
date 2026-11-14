#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 v0255: parallel idempotence gate, heartbeat and phase timing (thin tail over v0243).

Desktop run 2026-10-29 08:14 (ActivateVRN-2 v0144 · 52 reports): step ⑦ took 1201 s although the
extraction cache served 52/52 and acceptance 51/52. The manager printed nothing for ~1050 s: the
idempotence gate of v0243 re-extracts three GREEN reports twice (R1 then R2) in ONE single-lane
subprocess per wave, without the extraction cache — six full extractions in series, silently.

v0255 keeps the gate's contract (same shard subprocess path · no extraction cache · R1 vs R2 vs main
record · GREEN / STALE_RECORD / NONDETERMINISTIC) and changes only how the waves run:
  · each wave runs one single-lane shard subprocess PER FILE, concurrently (default 3 lanes ·
    VRN2_IDEM_LANES overrides) — R1 completes before R2 starts, so the shared OCR cache is never
    written by two runs of the same file at once;
  · a heartbeat line every 30 s while a wave runs, so the launcher's silence watchdog sees progress;
  · per-wave / per-file wall time in IDEMPOTENCE_latest.json (timing) and in the [計] 冪等閘 line;
  · phase timing around the native flow (擷取迴圈 p1loop · 驗收 + 摘要 · 輸出冊 · U/I 輸出冊頁 ·
    調節輪 · 冪等閘) printed live, summarised in one [計] 階段耗時 line and written to
    VIA_Reports/vrn2/VRN2_Phase_Timing_latest.json, so the next desktop paste-back shows where the
    time goes without guessing.
Version number: v0244–v0254 are taken by the desktop line in functional modules/VRN; this private
runtime line continues at v0255 with PRIOR pinned to v0243. Financial extraction, acceptance,
books, verifiers and the U/I stay byte-identical (v0243 code reached through PRIOR).
"""
from __future__ import annotations

# ===== 1. Parameters =====
TAG = "v0255"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0243.py"
IDEM_LANES_DEFAULT = 3
IDEM_HEARTBEAT_S = 30
TIMED_VERBS = ("p1loop",)
PHASE_RECEIPT = "VRN2_Phase_Timing_latest.json"

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import types

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0255", Path(__file__).with_name(PRIOR_NAME))
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in list(vars(PRIOR).items()):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


def _rebind(function):
    result = types.FunctionType(function.__code__, globals(), function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__, result.__doc__ = function.__kwdefaults__, function.__doc__
    return result


def _say(text):
    print(text, flush=True)


# ===== 2. Phase timing (live lines + one summary line + receipt) =====
PHASES = []


def _timed(label, function):
    """Wrap a callable: print start / finish with wall time, record it in PHASES. The wrapped function is called as is."""
    def wrapper(*args, **kwargs):
        started = time.time()
        _say("[計] 階段 · %s · 開始" % label)
        try:
            return function(*args, **kwargs)
        finally:
            seconds = round(time.time() - started, 1)
            PHASES.append({"phase": label, "seconds": seconds})
            _say("[計] 階段 · %s · 完成 · 耗時 %.0f 秒" % (label, seconds))
    wrapper.__name__ = getattr(function, "__name__", label)
    wrapper.__doc__ = getattr(function, "__doc__", None)
    wrapper.__wrapped__ = function
    return wrapper


_native_resolve = PRIOR._resolve


def _resolve(name):
    """Native verb lookup; the extraction loop (p1loop) comes back wrapped with phase timing."""
    found = _native_resolve(name)
    if name in TIMED_VERBS and callable(found):
        return _timed("擷取迴圈 " + name, found)
    return found


acceptance = _timed("驗收 + 摘要", PRIOR.acceptance)
_out_books = _timed("輸出冊", PRIOR._out_books)
_out_html = _timed("U/I 輸出冊頁", PRIOR._out_html)
_funnel = _timed("調節輪", PRIOR._funnel)


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    result["manager"] = f"{DISPLAY_NAME} {TAG}"
    return result


# ===== 3. Idempotence gate: same contract as v0243, waves run per file in parallel =====
def _idem_lanes():
    try:
        return max(1, int(os.environ.get("VRN2_IDEM_LANES") or IDEM_LANES_DEFAULT))
    except ValueError:
        return IDEM_LANES_DEFAULT


def _idem_wave(engine_path, directory, selected, tag, timeout_s=1800, lanes=None):
    """One fresh extraction per selected file through the main run's shard subprocess path (no extraction cache),
    one single-lane subprocess per file, up to `lanes` at once. Returns (rows by file, timing)."""
    lanes = lanes or _idem_lanes()
    od = directory / tag / "p1view"
    (od / "img").mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", VIA_VRN2_LANES="1")
    environment.pop("VIA_VRN2_P1_CACHE", None)
    jobs = []
    for index, record in enumerate(selected):
        name = record["file"]
        shard = directory / ("%s_%02d_shard.json" % (tag, index + 1))
        out = directory / ("%s_%02d_out.jsonl" % (tag, index + 1))
        shard.write_text(json.dumps({"jobs": [[1, name, {"p": str(directory / "in" / name), "od": str(od)}]], "out": str(out)}, ensure_ascii=False), encoding="utf-8")
        jobs.append({"name": name, "out": out, "log": directory / ("%s_%02d.log" % (tag, index + 1)), "command": [sys.executable, "-W", "ignore", str(engine_path), "--shard", str(shard)]})
    started = time.time()
    pending, running, rows, elapsed, last_beat = list(jobs), {}, {}, {}, started
    try:
        while pending or running:
            while pending and len(running) < lanes:
                job = pending.pop(0)
                job["t0"] = time.time()
                job["handle"] = open(job["log"], "w", encoding="utf-8")
                job["handle"].write("$ " + " ".join(job["command"]) + "\n")
                job["handle"].flush()
                job["proc"] = subprocess.Popen(job["command"], cwd=str(engine_path.parent), env=environment, stdout=job["handle"], stderr=subprocess.STDOUT)
                running[job["name"]] = job
            for name, job in list(running.items()):
                rc = job["proc"].poll()
                if rc is None:
                    continue
                job["handle"].write("\nrc %s\n" % rc)
                job["handle"].close()
                elapsed[name] = round(time.time() - job["t0"], 1)
                del running[name]
                if rc != 0 or not job["out"].is_file():
                    raise RuntimeError("%s shard rc %s (%s)" % (tag, rc, name))
                for line in job["out"].read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        entry = json.loads(line)
                        rows[entry["r"].get("file")] = entry["r"]
            now = time.time()
            if now - started > timeout_s:
                raise RuntimeError("%s timeout %d s" % (tag, timeout_s))
            if running and now - last_beat >= IDEM_HEARTBEAT_S:
                last_beat = now
                _say("[計] 冪等閘 · %s · 已 %d 秒 · 完成 %d/%d · 跑中 %s" % (tag, now - started, len(elapsed), len(jobs), " | ".join(sorted(running))))
            if running:
                time.sleep(0.5)
    finally:
        for job in running.values():
            try:
                job["proc"].kill()
            except Exception:  # noqa: BLE001 — best effort cleanup after an error above
                pass
            try:
                job["handle"].close()
            except Exception:  # noqa: BLE001
                pass
    return rows, {"elapsed_s": round(time.time() - started, 1), "files": elapsed, "lanes": lanes, "parallel": len(jobs) > 1 and lanes > 1}


def _idem_check(res, indir, k=3):
    selected = sorted((record for record in res if record.get("lamp") == "GREEN" and len(record.get("pages") or []) >= 2), key=lambda record: record.get("file", ""))[:k]
    if not selected:
        return "GRAY", "沒有可重跑的檔"
    engines = sorted(Path(HERE).glob("VRN_ENG397_P1Segment_v[0-9][0-9][0-9][0-9].py"))
    if not engines:
        return "RED", "找不到 ENG397，冪等檢查未執行"
    lanes = _idem_lanes()
    _say("[計] 冪等閘 · 開始 · %d 份 ×2(R1 → R2)· 每波 %d 路並行 · 單路 · 不吃擷取快取 · %s" % (len(selected), min(lanes, len(selected)), "、".join(record["file"] for record in selected)))
    gate_started = time.time()
    directory = Path(tempfile.mkdtemp(prefix="vrn2_idem_v0255_"))
    (directory / "in").mkdir()
    (directory / ".via_keep").touch()
    for record in selected:
        shutil.copy2(Path(indir) / record["file"], directory / "in" / record["file"])
    receipt = {"manager": TAG, "engine": engines[-1].name,
               "method": "same shard subprocess path as the main run (python -W ignore ENG397 --shard) · twice (R1 then R2) · one single-lane subprocess per file, %d lanes · no extraction cache · OCR cache shared" % lanes,
               "ignored_runtime_keys": sorted(RUNTIME_METADATA), "context": _idem_context(), "files": [], "lamp": "RED", "classification": "ERROR", "cache_cleared": [], "timing": {}}
    try:
        for record in selected:
            receipt.setdefault("inputs", {})[record["file"]] = hashlib.sha256((Path(indir) / record["file"]).read_bytes()).hexdigest()
        first, timing_first = _idem_wave(engines[-1], directory, selected, "R1")
        receipt["timing"]["R1"] = timing_first
        _say("[計] 冪等閘 · R1 完成 · 耗時 %.0f 秒 · %s" % (timing_first["elapsed_s"], " · ".join("%s %.0f" % (name, seconds) for name, seconds in sorted(timing_first["files"].items()))))
        second, timing_second = _idem_wave(engines[-1], directory, selected, "R2")
        receipt["timing"]["R2"] = timing_second
        _say("[計] 冪等閘 · R2 完成 · 耗時 %.0f 秒" % timing_second["elapsed_s"])
        entries, stale, nondeterministic = _idem_classify(selected, first, second)
        receipt["files"] = entries
        if nondeterministic:
            receipt.update(lamp="RED", classification="NONDETERMINISTIC", nondeterministic_files=nondeterministic, stale_files=stale)
            hint = next((row["differences_rerun_vs_rerun"][0]["path"] for row in entries if row["differences_rerun_vs_rerun"]), "")
            message = "重跑兩次就不一致 %d 份(引擎非冪等):%s · 第一個差異 %s" % (len(nondeterministic), "、".join(nondeterministic), hint)
        elif stale:
            receipt["cache_cleared"] = _idem_clear_cache(engines[-1], stale, indir)
            receipt.update(lamp="RED", classification="STALE_RECORD", stale_files=stale)
            hint = next((row["differences_main_vs_rerun"][0]["path"] for row in entries if row["differences_main_vs_rerun"]), "")
            message = "主跑紀錄與重跑不同、重跑兩次一致 %d 份:%s · 第一個差異 %s · 已清該檔擷取快取 %d 檔 → 啟動器自動再跑一輪取新紀錄" % (len(stale), "、".join(stale), hint, len(receipt["cache_cleared"]))
        else:
            receipt.update(lamp="GREEN", classification="GREEN")
            message = "重跑 %d 份 ×2(同主跑的子行程路徑 · 每波 %d 路並行),文字／表格／數值／期間／位置一致" % (len(selected), min(lanes, len(selected)))
    except Exception as error:  # noqa: BLE001 — the gate must report, never crash the run
        receipt["error"] = f"{type(error).__name__}: {error}"
        message = "重跑失敗:" + receipt["error"]
    total = round(time.time() - gate_started, 1)
    receipt["timing"]["total_s"] = total
    PHASES.append({"phase": "冪等閘", "seconds": total})
    target = Path(HERE).parents[1] / "VIA_Reports/vrn2/IDEMPOTENCE_latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt["evidence_directory"] = str(directory)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    if receipt["lamp"] == "GREEN":
        shutil.rmtree(directory, ignore_errors=True)
    timing_text = " · 耗時 %.0f 秒(R1 %.0f · R2 %.0f)" % (total, (receipt["timing"].get("R1") or {}).get("elapsed_s", 0), (receipt["timing"].get("R2") or {}).get("elapsed_s", 0))
    return receipt["lamp"], message + timing_text + " · 詳細差異 " + str(target)


# ===== 4. Native flow with v0255 globals (gate · timers) + scope merge kept from v0243 =====
_native_vrn2 = _rebind(PRIOR._native_vrn2)
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0255),同 v0232 ~ v0243 的做法


def vrn2(args, rep=None, indir=None, open_ui=True, reg=None):
    PHASES.clear()
    started = time.time()
    report = Path(rep or _native_resolve("_rep")())
    scope = report.parent / "vrn2/VRN2_Scope_latest.json"
    previous = json.loads(scope.read_text(encoding="utf-8")) if scope.is_file() else {}
    result = _native_vrn2(args, rep=rep, indir=indir, open_ui=open_ui, reg=reg)
    if scope.is_file():
        current = json.loads(scope.read_text(encoding="utf-8"))
        excluded = sorted(set(previous.get("non_stock") or []) | set(current.get("non_stock") or []))
        current.update(non_stock=excluded, stock=[name for name in current.get("stock") or [] if name not in excluded])
        scope.write_text(json.dumps(current, ensure_ascii=False, indent=1), encoding="utf-8")
    total = round(time.time() - started, 1)
    timed = round(sum(entry["seconds"] for entry in PHASES), 1)
    line = "[計] 階段耗時(秒)· %s · 其他 %.0f · 總 %.0f · 收據 %s" % (" · ".join("%s %.0f" % (entry["phase"], entry["seconds"]) for entry in PHASES) or "無", max(total - timed, 0), total, PHASE_RECEIPT)
    try:
        target = report.parent / "vrn2" / PHASE_RECEIPT
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"manager": "%s %s" % (DISPLAY_NAME, TAG), "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "total_s": total, "timed_s": timed, "untimed_s": round(max(total - timed, 0), 1), "phases": list(PHASES)}, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as error:
        line += " · 收據寫入失敗 %s" % type(error).__name__
    _say(line)
    code, lines = result
    return code, list(lines) + [line]


# ===== 5. Self-test =====
FAKE_ENGINE = '''import json, os, sys, time
shard = json.loads(open(sys.argv[sys.argv.index("--shard") + 1], encoding="utf-8").read())
time.sleep(float(os.environ.get("FAKE_SLEEP", "0")))
counter = os.environ.get("FAKE_COUNTER")
value = "1.25"
if counter:
    n = int(open(counter).read() or 0) + 1 if os.path.exists(counter) else 1
    open(counter, "w").write(str(n)); value = "1.%02d" % n
with open(shard["out"], "a", encoding="utf-8") as fh:
    for _index, name, _opts in shard["jobs"]:
        fh.write(json.dumps({"r": {"file": name, "lamp": "GREEN", "n": 1, "pages": [{"pno": 1, "zones": [{"rows": [["2026", value]]}]}, {"pno": 2, "zones": []}]}}) + "\\n")
print("[切] fake " + " ".join(j[1] for j in shard["jobs"]), flush=True)
'''


def selftest():
    global HERE
    assert _native_vrn2.__globals__["_idem_check"] is _idem_check
    assert _native_vrn2.__globals__["acceptance"] is acceptance and _native_vrn2.__globals__["_out_books"] is _out_books
    assert _native_vrn2.__globals__["_resolve"] is _resolve and _native_vrn2.__globals__["completion"] is completion
    assert _native_vrn2.__code__ is PRIOR._native_vrn2.__code__
    assert _native_vrn2.__globals__["_success_register"] is _success_register and _success_register is not PRIOR._success_register and _success_register.__globals__ is globals()
    assert callable(_resolve("p1loop")) and getattr(_resolve("p1loop"), "__wrapped__", None) is _native_resolve("p1loop")
    assert _resolve("_rep") is _native_resolve("_rep")
    PHASES.clear()
    assert _timed("試", lambda value: value * 2)(21) == 42 and PHASES[-1]["phase"] == "試"
    saved_here, saved_env = HERE, dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            HERE = root / "functional modules" / "VRN2"
            HERE.mkdir(parents=True)
            (HERE / "VRN_ENG397_P1Segment_v9999.py").write_text(FAKE_ENGINE, encoding="utf-8")
            indir = root / "in"
            indir.mkdir()
            names = ["a.pdf", "b.pdf", "c.pdf"]
            for name in names:
                (indir / name).write_bytes(b"%PDF-1.4 fake " + name.encode())
            res = [{"file": name, "lamp": "GREEN", "cache": "hit", "n": 3, "pages": [{"pno": 1, "zones": [{"rows": [["2026", "1.25"]]}]}, {"pno": 2, "zones": []}]} for name in names]
            os.environ.pop("VIA_VRN2_P1_CACHE", None)
            os.environ["FAKE_SLEEP"] = "1.5"
            os.environ["VRN2_IDEM_LANES"] = "3"
            lamp, message = _idem_check(res, indir)
            receipt = json.loads((root / "VIA_Reports/vrn2/IDEMPOTENCE_latest.json").read_text(encoding="utf-8"))
            assert lamp == "GREEN" and receipt["classification"] == "GREEN", (lamp, message)
            assert receipt["timing"]["R1"]["lanes"] == 3 and receipt["timing"]["R1"]["parallel"] and len(receipt["timing"]["R1"]["files"]) == 3
            assert receipt["timing"]["R1"]["elapsed_s"] < 3.8, receipt["timing"]   # serial would be ≥ 4.5 s (3 × 1.5 s)
            assert all(seconds >= 1.5 for seconds in receipt["timing"]["R1"]["files"].values())
            assert "每波 3 路並行" in message and "耗時" in message and PHASES[-1]["phase"] == "冪等閘"
            assert not Path(receipt["evidence_directory"]).exists()   # GREEN → evidence folder removed
            os.environ["FAKE_SLEEP"] = "0"
            os.environ["FAKE_COUNTER"] = str(root / "counter.txt")
            lamp, message = _idem_check(res, indir)
            receipt = json.loads((root / "VIA_Reports/vrn2/IDEMPOTENCE_latest.json").read_text(encoding="utf-8"))
            assert lamp == "RED" and receipt["classification"] == "NONDETERMINISTIC" and sorted(receipt["nondeterministic_files"]) == names, (lamp, message)
            assert Path(receipt["evidence_directory"]).is_dir() and sorted(p.name for p in Path(receipt["evidence_directory"]).glob("R1_*.log")) == ["R1_01.log", "R1_02.log", "R1_03.log"]
            shutil.rmtree(receipt["evidence_directory"], ignore_errors=True)
            os.environ["VRN2_IDEM_LANES"] = "1"
            os.environ.pop("FAKE_COUNTER", None)
            lamp, message = _idem_check(res, indir)
            receipt = json.loads((root / "VIA_Reports/vrn2/IDEMPOTENCE_latest.json").read_text(encoding="utf-8"))
            assert lamp == "GREEN" and receipt["timing"]["R1"]["lanes"] == 1 and not receipt["timing"]["R1"]["parallel"]
            assert _idem_check([{"file": "x.pdf", "lamp": "YELLOW", "pages": []}], indir)[0] == "GRAY"
    finally:
        HERE = saved_here
        os.environ.clear()
        os.environ.update(saved_env)
    print("[PASS] v0255: idempotence gate per-file parallel waves (GREEN · NONDETERMINISTIC · lanes 1) with timing in the receipt; phase timers bound into the native flow; success register names v0255; v0243 code reached through PRIOR")
    return 0


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--selftest"]:
        return selftest()
    if arguments[:1] == ["vrn2"]:
        code, lines = vrn2(arguments[1:])
        for line in lines:
            print(line, flush=True)
        return code
    return PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())

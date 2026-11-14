#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ConsensusJoin v0104 — v0103 薄尾(v0103 ~ v0100 一字不改):共識引擎改經 VIA 網路工具 + 加速器出網。

操作員 2026-10-31:「新版有版本號 · 加速器跟網路工具最新版都有版本號 · 直接透過 VCGC 的環境工具管理引擎下載所有不足工具及環境並確認無衝突 ·
改成經網路工具和加速器出網再抓」。
引擎 VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0122(v0121 + 出網一律經 SUP_MDL740_NetUnified 最高版號:鉅亨 → http_bytes 車道 ·
YFinance → yahoo_quote_summary_raw 車道 · 雙同意閘 · DENY = 停、不換道直連)放進 runtime → engine_path 取最高版號 = v0122。本版:
  ① 擷取 Python 檢查:引擎是經網路工具的(檔內有 [VIA:NET-TOOL:)→ 查 requests(Yahoo 車道要它)而不是 yfinance(新引擎不用 yfinance 套件)。
  ② 收據多 net_tool(引擎印的「def Net tool」那行:網路工具版號 · 閘開關 · 加速器)。
  ③ 網路工具 DENY(同意閘未開 / 合規)→ 收據 net_deny {note · gate_closed} · 黃 · why 寫清楚是誰的決定;不重試、不換道直連
     (v0103 的重試只對 404 / 一時抓不到)。同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)是操作員的決定 · VRN-2 永不代設。
  ④ VIA_VRN2_CONSENSUS_REFRESH=1 → 跑之前把今天的 checkpoint 用引擎自己的函式封存 → 這輪全部經網路工具重抓(「再抓」);沒設 = 照 v0103 續跑。
  ⑤ 沒設 REFRESH:今天的 checkpoint 不是經網路工具抓的(consensus\\VRN2_Consensus_NetTool.json 對不上)+ 同意閘開 → 一樣先封存 → 經網路工具重抓;
     閘關 → 不封存(引擎 DENY · 操作員決定)。經網路工具抓完(沒 DENY)→ 記下這份 checkpoint。VIA_VRN2_NO_CONSENSUS_REFRESH=1 = 不封存。
動詞同 v0103:run · join · --selftest · --engine-shim。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile

VERSION = "v0104"
DISPLAY_NAME = "VRN2_ConsensusJoin"
TAG = "共識合併 v0104"
PRIOR_NAME = "VRN2_ConsensusJoin_v0103.py"
HERE = Path(__file__).resolve().parent
NET_MARK = "[VIA:NET-TOOL:"
YF_PROBE = "import yfinance; print('ok', yfinance.__version__)"
REQ_PROBE = "import requests; print('ok', requests.__version__)"
_GATE_CLOSED = re.compile(r"同意閘未開|閘一未開|閘二未開|閘閉")
NET_SIDECAR = "VRN2_Consensus_NetTool.json"     # 今天哪份 checkpoint 是經網路工具抓的(引擎版號字串 v0120 / v0122 都是 2.0.0 · 分不出)


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
    return _load(path, "vrn2_consensus_join_prior_v0103")


PRIOR = _prior()                       # v0103(它再載 v0102 → v0101 → v0100)
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
V0102 = PRIOR.PRIOR
V0101 = V0102.PRIOR
V0100 = V0101.PRIOR
for _mod in (PRIOR, V0102, V0101, V0100):
    _mod.TAG = TAG
_v0103_run = PRIOR.run
_V0103_RUN = PRIOR.run                 # 前版自測要用 v0103 自己的 run(自測裡會替換 _v0103_run)
_v0103_join = PRIOR.join
_STATE = {"net": False, "lines": []}


def uses_net_tool(engine) -> bool:
    """引擎檔是不是經 VIA 網路工具出網的版本(檔內有 [VIA:NET-TOOL: 標記)。"""
    try:
        return NET_MARK in Path(engine).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


class _ProbeShim:
    """v0101 run 的擷取 Python 檢查:經網路工具的引擎 → 查 requests 而不是 yfinance;其他呼叫照原樣。"""

    def __init__(self, real):
        self._real = real

    def run(self, cmd, *a, **kw):
        if _STATE["net"] and isinstance(cmd, list) and cmd and cmd[-1] == YF_PROBE:
            cmd = list(cmd[:-1]) + [REQ_PROBE]
        return self._real.run(cmd, *a, **kw)

    def __getattr__(self, name):
        return getattr(self._real, name)


def _stream_capture(real):
    def wrapped(command, cwd, wait, prefix="    [⑥f] "):
        rc, lines = real(command, cwd, wait, prefix)
        _STATE["lines"].extend(lines)
        return rc, lines
    return wrapped


def refresh_checkpoint(out: Path, engine) -> dict:
    """VIA_VRN2_CONSENSUS_REFRESH=1:今天的 checkpoint 用引擎自己的封存函式收起來 → 這輪全部重抓。"""
    try:
        mod = _load(Path(engine), "vrn2_consensus_engine_refresh_v0104")
        cp_path = Path(out) / mod.OUTPUT_CHECKPOINT
        old = mod.def_load_json_file(cp_path, default={}) or {}
        if not old:
            return {"archived": None, "why": "沒有 checkpoint"}
        archived = mod.def_archive_checkpoint(cp_path, old)
        cp_path.unlink()
        return {"archived": str(archived) if archived else None, "why": "今天的 checkpoint 已封存 · 全部重抓"}
    except Exception as error:  # noqa: BLE001
        return {"archived": None, "why": "%s: %s" % (type(error).__name__, str(error)[:160])}


def provenance_refresh(out: Path, engine, gate_open=None) -> dict | None:
    """經網路工具的引擎跑之前:今天的 checkpoint 不是經網路工具抓的(直連引擎 v0120 抓的 · 版號字串同 2.0.0 分不出 → 看 NET_SIDECAR)
    而且同意閘是開的 → 用引擎自己的函式封存 → 這輪全部經網路工具重抓。閘關 → 不封存(引擎照樣 DENY · 現有 checkpoint 留著)。"""
    try:
        mod = _load(Path(engine), "vrn2_consensus_engine_provenance_v0104")
        cp = mod.def_load_json_file(Path(out) / mod.OUTPUT_CHECKPOINT, default={}) or {}
        if not cp.get("input_hash") or cp.get("as_of_date") != mod.def_pipeline_as_of_date({}):
            return None                                                        # 沒有今天的 checkpoint → 引擎本來就全部經網路工具抓
        side = json.loads((Path(out) / NET_SIDECAR).read_text(encoding="utf-8")) if (Path(out) / NET_SIDECAR).is_file() else {}
        if side.get("input_hash") == cp.get("input_hash"):
            return None                                                        # 今天已經經網路工具抓過
        if gate_open is None:
            gate_open = bool(mod.def_via_net_status().get("gate_open"))
        if not gate_open:
            return {"archived": None, "why": "今天的 checkpoint 是直連引擎抓的 · 同意閘未開 → 不封存(操作員決定)"}
        got = refresh_checkpoint(out, engine)
        got["why"] = "今天的 checkpoint 是直連引擎抓的 → 封存 · 這輪全部經 VIA 網路工具重抓" if got.get("archived") else got.get("why")
        return got
    except Exception as error:  # noqa: BLE001
        return {"archived": None, "why": "%s: %s" % (type(error).__name__, str(error)[:160])}


def mark_provenance(out: Path, engine, net_tool: str) -> None:
    """這輪經網路工具抓完(沒 DENY)→ 記下這份 checkpoint 的 input_hash(下次同一天不再當直連的封存)。"""
    try:
        mod = _load(Path(engine), "vrn2_consensus_engine_mark_v0104")
        cp = mod.def_load_json_file(Path(out) / mod.OUTPUT_CHECKPOINT, default={}) or {}
        if cp.get("input_hash"):
            (Path(out) / NET_SIDECAR).write_text(json.dumps({"input_hash": cp["input_hash"], "as_of_date": cp.get("as_of_date"), "engine": Path(engine).name,
                                                             "net_tool": net_tool, "by": "%s %s" % (DISPLAY_NAME, VERSION)}, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:  # noqa: BLE001  記不下 = 下次再封存重抓一次(只會多抓 · 不會錯)
        pass


def _deny_note(rec: dict, out: Path):
    """收據 tail / 這次的品質矩陣裡的 VIA_NET_DENY(過期的品質矩陣不看)。"""
    for line in list(_STATE["lines"])[::-1] + list(rec.get("tail") or [])[::-1]:
        if "VIA_NET_DENY" in str(line):
            return str(line)[str(line).find("VIA_NET_DENY"):][:240]
    if not rec.get("engine_no_output"):
        for r in quality_fails(out):
            if "VIA_NET_DENY" in str(r.get("actual") or ""):
                return str(r.get("actual"))[:240]
    return None


def run(v2: Path, root: Path | None = None, fixtures: list | None = None, timeout: int = 900, engine: str | None = None) -> dict:
    v2 = Path(v2)
    out = v2 / "consensus"
    eng = engine_path(root, engine)
    _STATE.update(net=bool(eng) and uses_net_tool(eng), lines=[])
    refreshed = None
    if _STATE["net"] and not fixtures and os.environ.get("VIA_VRN2_CONSENSUS_REFRESH") == "1":
        refreshed = refresh_checkpoint(out, eng)
        print("    [⑥f] [計] 經 VIA 網路工具重抓(VIA_VRN2_CONSENSUS_REFRESH=1):%s" % refreshed.get("why"), flush=True)
    elif _STATE["net"] and not fixtures and os.environ.get("VIA_VRN2_NO_CONSENSUS_REFRESH") != "1":
        refreshed = provenance_refresh(out, eng)
        if refreshed is not None:
            print("    [⑥f] [計] %s" % refreshed.get("why"), flush=True)
    real_sub, real_stream = V0101.subprocess, V0101._stream
    V0101.subprocess, V0101._stream = _ProbeShim(real_sub), _stream_capture(real_stream)
    try:
        rec = _v0103_run(v2, root, fixtures, timeout, engine)
    finally:
        V0101.subprocess, V0101._stream = real_sub, real_stream
    if _STATE["net"]:
        net_line = next((l for l in _STATE["lines"] if "def Net tool" in l), "")
        if ":" in net_line:
            rec["net_tool"] = net_line.split(":", 1)[1].strip()
        else:
            rec["net_engine"] = Path(eng).name                                 # 引擎沒跑到出網那步(擷取環境 / 逾時)→ 不算經網路工具抓過
        if "擷取環境缺 yfinance" in str(rec.get("why", "")):
            rec["why"] = str(rec["why"]).replace("擷取環境缺 yfinance", "擷取環境缺 requests(新引擎經 VIA 網路工具 · Yahoo 車道要它 · 交 VCGC 環境工具補)")
    if refreshed is not None:
        rec["refresh"] = refreshed
    note = _deny_note(rec, out) if _STATE["net"] else None
    if note:
        closed = bool(_GATE_CLOSED.search(note))
        rec["net_deny"] = {"note": note, "gate_closed": closed}
        rec["lamp"] = "YELLOW"
        rec["why"] = ("VIA 網路工具 DENY(%s)· %s · 不換道直連" % (
            note[:120], "同意閘 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是操作員的決定(VRN-2 不代設)" if closed else "網路工具合規判定 · VCGC 決定"))
        if not (out / MATRIX_CSV).is_file() or rec.get("engine_no_output") or not rec.get("codes_got"):
            rec.update(per_code={}, codes_got=[], codes_missing=list(rec.get("codes") or []))
    elif _STATE["net"] and not fixtures and rec.get("codes_got") and not rec.get("engine_no_output"):
        mark_provenance(out, eng, rec.get("net_tool") or "")
    return _finish(out, rec)


def _wire(run_fn, join_fn) -> None:
    for mod in (PRIOR, V0102, V0101, V0100):
        mod.run, mod.join = run_fn, join_fn


_wire(run, _v0103_join)
join = _v0103_join


def _legacy_engine():
    """前版自測要的是直連引擎(v0103 的 ⑪ 走代理指到關著的埠驗重試):HERE 裡最高版號、沒有網路工具標記的那支。"""
    hits = [p for p in HERE.glob(ENGINE_GLOB) if not uses_net_tool(p)]
    return str(max(hits, key=_vnum)) if hits else None


def selftest(engine: str | None = None) -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    legacy = _legacy_engine()
    _wire(_V0103_RUN, _v0103_join)                                        # 前版自測照前版自己的接線(v0103 的 run)跑
    try:
        rc = PRIOR.selftest(legacy)
    finally:
        _wire(run, _v0103_join)
    chk("① v0103 自測(含 v0102 ~ v0100 · 直連引擎 %s)照過" % (Path(legacy).name if legacy else "—"), rc == 0)
    net_eng = [p for p in HERE.glob(ENGINE_GLOB) if uses_net_tool(p)]
    newest = engine_path(None, engine)
    chk("② runtime 最高版號的共識引擎經 VIA 網路工具(%s)· 直連引擎留作前版" % (newest.name if newest else "—"),
        bool(newest) and uses_net_tool(newest) and (legacy is None or not uses_net_tool(legacy)))
    calls = []

    class FakeSub:
        @staticmethod
        def run(cmd, *a, **kw):
            calls.append(list(cmd))
            return None
    shim = _ProbeShim(FakeSub)
    _STATE["net"] = True
    shim.run(["py", "-c", YF_PROBE])
    shim.run(["py", "-X", "utf8", "engine.py"])
    _STATE["net"] = False
    shim.run(["py", "-c", YF_PROBE])
    chk("③ 擷取 Python 檢查:經網路工具的引擎 → 查 requests · 其他呼叫照原樣 · 直連引擎照查 yfinance",
        calls == [["py", "-c", REQ_PROBE], ["py", "-X", "utf8", "engine.py"], ["py", "-c", YF_PROBE]])
    with tempfile.TemporaryDirectory(prefix="vrn2-cj104-") as temporary:
        v2 = Path(temporary) / "vrn2"
        (v2 / "consensus").mkdir(parents=True)
        (v2 / "output").mkdir()
        (v2 / "output" / "VRN2_BasicInfo_latest.json").write_text(json.dumps([{"FILENAME": "a.pdf", "TICKER": "2330"}]), encoding="utf-8")
        fake_eng = Path(temporary) / "VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0199.py"
        fake_eng.write_text("# " + NET_MARK + "v0122]\n", encoding="utf-8")
        deny = "PermissionError: VIA_NET_DENY: VIA 網路工具同意閘未開(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT · 操作員決定 · 引擎不代設 · 不換道直連)"
        saved = globals()["_v0103_run"]
        globals()["_v0103_run"] = lambda *a, **k: {"rc": 1, "gate": "", "codes": ["2330"], "lamp": "YELLOW", "why": "引擎沒出矩陣", "tail": ["Traceback", deny], "engine": str(fake_eng)}
        try:
            rec = run(v2, None, None, 60, str(fake_eng))
            globals()["_v0103_run"] = lambda *a, **k: {"rc": 1, "gate": "", "codes": ["2330"], "lamp": "YELLOW", "why": "x", "tail": ["PermissionError: VIA_NET_DENY: robots 合規 DENY url=https://x"], "engine": str(fake_eng)}
            rec2 = run(v2, None, None, 60, str(fake_eng))
            globals()["_v0103_run"] = lambda *a, **k: {"rc": None, "gate": "", "codes": ["2330"], "lamp": "YELLOW", "why": "擷取環境缺 yfinance(/x/py)", "tail": [], "engine": str(fake_eng)}
            rec9 = run(v2, None, None, 60, str(fake_eng))
        finally:
            globals()["_v0103_run"] = saved
        chk("⑨ 引擎沒跑到出網那步(擷取環境缺 requests · 沒有「def Net tool」行)→ 不寫 net_tool(不算經網路工具抓過)· net_engine 記引擎名 · why 寫缺 requests 交 VCGC 環境工具",
            "net_tool" not in rec9 and rec9.get("net_engine") == fake_eng.name and "缺 requests" in rec9.get("why", "") and "VCGC" in rec9.get("why", "") and not rec9.get("net_deny"))
        chk("④ 網路工具 DENY:同意閘未開 → net_deny gate_closed · 黃 · why 寫「操作員的決定」· 共識欄清空(這次沒抓)· 合規 DENY → gate_closed False(VCGC 決定)",
            (rec.get("net_deny") or {}).get("gate_closed") is True and rec.get("lamp") == "YELLOW" and "操作員的決定" in rec.get("why", "") and rec.get("per_code") == {}
            and (rec2.get("net_deny") or {}).get("gate_closed") is False and "VCGC 決定" in rec2.get("why", ""))
        real = engine_path(None, engine)
        if real and uses_net_tool(real):
            mod = _load(real, "vrn2_cj104_selftest_engine")
            out = v2 / "consensus"
            cp_path, cp = mod.def_initialize_checkpoint(str(out), ["2330"], fixture_map={}, resume=True)
            mod.def_save_checkpoint_payload(str(out), cp, {"code": "2330", "x": 1})
            mod.def_save_checkpoint_state(cp_path, cp)
            got = refresh_checkpoint(out, real)
            chk("⑤ 重抓(VIA_VRN2_CONSENSUS_REFRESH=1):今天的 checkpoint 用引擎自己的函式封存 · 檔移走 → 這輪全部經網路工具重抓",
                not cp_path.exists() and bool(got.get("archived")) and Path(got["archived"]).is_file())
            cp_path, cp = mod.def_initialize_checkpoint(str(out), ["2330"], fixture_map={}, resume=True)   # 今天的 · 直連引擎抓的(沒有 NET_SIDECAR)
            mod.def_save_checkpoint_state(cp_path, cp)
            p_closed = provenance_refresh(out, real, gate_open=False)
            kept = cp_path.exists()
            p_open = provenance_refresh(out, real, gate_open=True)
            gone = not cp_path.exists()
            cp_path, cp = mod.def_initialize_checkpoint(str(out), ["2330"], fixture_map={}, resume=True)
            mod.def_save_checkpoint_state(cp_path, cp)
            mark_provenance(out, real, "SUP_MDL740_NetUnified_v0119 · 閘 開")
            p_mark = provenance_refresh(out, real, gate_open=True)
            chk("⑧ 今天的 checkpoint 是直連引擎抓的(沒有 %s)+ 閘開 → 封存 · 經網路工具重抓 · 閘關 → 不封存 · 經網路工具抓過的(記號對得上)→ 照續跑" % NET_SIDECAR,
                (p_closed or {}).get("archived") is None and kept and bool((p_open or {}).get("archived")) and gone and p_mark is None and cp_path.exists())
            cp_path.unlink()
            (out / NET_SIDECAR).unlink()
            status = mod.def_via_net_status()
            print("    引擎網路工具狀態:%s" % json.dumps(status, ensure_ascii=False)[:240], flush=True)
            if status.get("net_tool"):
                saved_env = {k: os.environ.pop(k, None) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
                try:
                    if not status.get("gate_open"):
                        saved_run = globals()["_v0103_run"]
                        buf = io.StringIO()
                        with contextlib.redirect_stdout(buf):                 # 引擎預期的 PermissionError 堆疊收起來
                            rec3 = run(v2, None, None, 120, str(real))
                        print("    真引擎輸出 %d 行(收起來)· %s" % (len(buf.getvalue().splitlines()), next((l.strip()[:120] for l in buf.getvalue().splitlines() if "def Net tool" in l), "—")), flush=True)
                        chk("⑥ 真引擎 + 真網路工具(%s · 閘關):開跑前就停 · net_deny gate_closed · 不換道直連" % status.get("net_tool"),
                            (rec3.get("net_deny") or {}).get("gate_closed") is True and globals()["_v0103_run"] is saved_run)
                    else:
                        print("[SKIP] ⑥ 這台的同意閘是開的(操作員設的)· 自測不跑真網路", flush=True)
                finally:
                    for k, v in saved_env.items():
                        if v is not None:
                            os.environ[k] = v
            else:
                print("[SKIP] ⑥ 這個 runtime 夾不在 VIA 樹裡(找不到 supportive modules\\network)· 真網路工具那段不跑", flush=True)
        else:
            print("[SKIP] ⑤ ⑥ runtime 裡沒有經網路工具的引擎", flush=True)
    chk("⑦ 啟動器 / CLI 的 run 都是本版(v0103 ~ v0100 的模組都指過來)· join 照 v0103", all(m.run is run and m.join is _v0103_join for m in (PRIOR, V0102, V0101, V0100)))
    print("[%s] %s %s --selftest · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest(argv[1] if len(argv) > 1 else None)
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())

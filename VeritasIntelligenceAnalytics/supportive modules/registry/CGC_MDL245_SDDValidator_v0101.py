#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL245_SDDValidator v0101 — 薄尾:實測加「先發現、後解掉」的判法(finding_resolved_by;R33 實測實錄 H4)。

  為什麼要這一版:VCGC-WKF001-STP005(H4)的設計就是「先 dry 看待同步(sync-check rc 2 = FINDING)→ 操作員核准 →
  registry-sync --apply → 複檢 sync-check」。v0100 取同一步最差的一次當結果,所以核准寫入、複檢都 OK 之後這一步還是 FINDING,
  永遠鎖不起來。
  現在:步驟冊寫 `finding_resolved_by: [[目標, 動詞, 必帶旗?], …]`;同一輪裡最後一次 FINDING 之後,有一次解法事件 OK
  → 這一步 OK,並記 `resolved_by`(誰、何時)與 `finding_at`。有 FAIL 不解;解法事件在發現之前不算。
  其餘一字未動(前版照讀,不複製)。VIA_FROM_VCGC:只收中控呼叫(前版 main 守門)。不用 TA-Lib。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL245_SDDValidator_v0100.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("sdd_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
PRIOR.ENGINE = ENGINE
_V0100_REAL = PRIOR.real
LAMP_ORDER = ("FAIL", "NOT_RUN", "FINDING", "NOSELFTEST", "CANON")


def _hit(e: dict, tgt: str, vb, flag=None) -> bool:
    return ((e.get("target") or PRIOR.CONSOLE) == tgt and (vb is None or vb in PRIOR._act(e))
            and (flag is None or flag in (e.get("args") or [])))


def _lamp(states: list) -> str:
    return next((x for x in LAMP_ORDER if x in states), "OK")


def resolve_findings(rep: dict, state: dict, evs: list, ai_evs: list) -> list:
    """FINDING steps whose book names a resolver that ran OK later in the same run → OK. Returns the codes it resolved."""
    done = []
    for _, w in state["wkfs"]:
        r = (rep.get("wkf") or {}).get(w["code"])
        if not r or r.get("state") == "REGISTERED_ONLY":
            continue
        mine = ai_evs if (w.get("tests") or {}).get("real_run") == "ai" else evs
        for st in w.get("steps") or []:
            rb, s = st.get("finding_resolved_by"), (r.get("steps") or {}).get(st.get("code"))
            if not rb or not s or s.get("state") != "FINDING":
                continue
            hits = [e for e in mine for m in st.get("match") or [] if _hit(e, *m)]
            if any(e.get("outcome") == "FAIL" for e in hits):
                continue
            last = max((e.get("t0") or 0 for e in hits if e.get("outcome") == "FINDING"), default=None)
            if last is None:
                continue
            fix = [e for e in mine for m in rb if _hit(e, *m) and e.get("outcome") == "OK" and (e.get("t0") or 0) > last]
            if not fix:
                continue
            f = fix[0]
            s.update({"state": "OK", "rc": f.get("rc"), "at": f.get("ts"), "finding_at": s.get("at"),
                      "resolved_by": " ".join([str(f.get("target") or PRIOR.CONSOLE)] + [str(x) for x in [f.get("verb")] + list(f.get("args") or [])])
                      + f" @ {f.get('ts')}"})
            s.pop("hand", None)
            done.append(st["code"])
    if not done:
        return done
    for r in (rep.get("wkf") or {}).values():          # evidence copies (`step:<code>`) follow their source
        for s in (r.get("steps") or {}).values():
            src = str(s.get("by") or "")
            if src.startswith("step:") and src[5:] in done and s.get("state") == "FINDING":
                s.update({"state": "OK", "resolved_by": "step:" + src[5:]})
                s.pop("hand", None)
    for r in (rep.get("wkf") or {}).values():
        if r.get("state") == "REGISTERED_ONLY":
            continue
        r["state"] = _lamp([s.get("state") for s in (r.get("steps") or {}).values()])
        bad = [s for s in r["steps"].values() if s.get("state") != "OK"]
        if r["state"] in ("FINDING", "FAIL", "CANON", "NOSELFTEST") and bad and all(s.get("hand") for s in bad):
            r["operator_hand"] = True
        else:
            r.pop("operator_hand", None)
        ai = sorted({s.get("ai_open") for s in bad if s.get("ai_open")})
        if ai:
            r["ai_open"] = ai
        else:
            r.pop("ai_open", None)
    return done


def real(run: str | None = None, write: bool = True, ai_run: str | None = None) -> dict:
    """v0101: v0100 的實測,再套 finding_resolved_by。"""
    rep = _V0100_REAL(run, write=False, ai_run=ai_run)
    _, evs = PRIOR.run_events(rep.get("run") or "no-run")
    _, ai_evs = PRIOR.run_events(rep.get("ai_run") or "no-run", "ai-")
    rep["engine"] = ENGINE
    rep["resolved"] = resolve_findings(rep, PRIOR.load_books(), evs, ai_evs)
    if write:
        PRIOR.OUT.mkdir(parents=True, exist_ok=True)
        (PRIOR.OUT / "SDD_REAL_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


PRIOR.real = real


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    C = PRIOR.CONSOLE
    w = {"code": "T-WKF001", "tests": {"real_run": "go"}, "steps": [
        {"code": "T-WKF001-STP001", "match": [["CGC_MDL238_OperatorConsole", "sync-check"], [C, "registry-sync"]],
         "finding_resolved_by": [[C, "registry-sync", "--apply"]]},
        {"code": "T-WKF001-STP002", "evidence": "step:T-WKF001-STP001"}]}
    st = {"wkfs": [("T", w)]}

    def rep0():
        return {"wkf": {"T-WKF001": {"state": "FINDING", "steps": {
            "T-WKF001-STP001": {"state": "FINDING", "rc": 2, "at": "t1", "hand": "x"},
            "T-WKF001-STP002": {"state": "FINDING", "by": "step:T-WKF001-STP001", "hand": "x"}}}}}
    find = {"target": "CGC_MDL238_OperatorConsole", "verb": "run", "act": "sync-check", "outcome": "FINDING", "t0": 1, "ts": "t1"}
    apply_ok = {"target": C, "verb": "registry-sync", "args": ["--apply"], "outcome": "OK", "rc": 0, "t0": 2, "ts": "t2"}
    dry_ok = {"target": C, "verb": "registry-sync", "args": [], "outcome": "OK", "rc": 0, "t0": 2, "ts": "t2"}
    r = rep0()
    done = resolve_findings(r, st, [find, apply_ok], [])
    chk("先 FINDING 後核准 apply OK → 這一步 OK,並記 resolved_by", done == ["T-WKF001-STP001"]
        and r["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP001"].get("resolved_by", "").endswith("@ t2"))
    chk("引這一步的 step: 證據跟著 OK · 工作流燈重算為 OK", r["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP002"]["state"] == "OK"
        and r["wkf"]["T-WKF001"]["state"] == "OK" and "operator_hand" not in r["wkf"]["T-WKF001"])
    r = rep0()
    rec = dict(find, outcome="OK", rc=0, t0=3, ts="t3")
    chk("之後的複檢(同一步的 sync-check)OK 也算解", resolve_findings(r, dict(st, wkfs=[("T", dict(w, steps=[dict(w["steps"][0],
        finding_resolved_by=[["CGC_MDL238_OperatorConsole", "sync-check"]]), w["steps"][1]]))]), [find, rec], []) == ["T-WKF001-STP001"])
    r = rep0()
    chk("複檢之後又 FINDING 就不算解", resolve_findings(r, st, [find, apply_ok, dict(find, t0=4)], []) == [])
    r = rep0()
    chk("解法沒帶必帶旗(只是 dry)不算解", resolve_findings(r, st, [find, dry_ok], []) == []
        and r["wkf"]["T-WKF001"]["state"] == "FINDING")
    r = rep0()
    chk("解法在發現之前不算解", resolve_findings(r, st, [dict(apply_ok, t0=0), find], []) == [])
    r = rep0()
    chk("同一步有 FAIL 就不解", resolve_findings(r, st, [find, dict(find, outcome="FAIL", t0=3), apply_ok], []) == [])
    r = rep0()
    chk("別輪(ai-)的事件不串到 go 輪", resolve_findings(r, st, [find], [apply_ok]) == [])
    book = PRIOR._json(PRIOR.newest("VIA_Workflow_VCGC_SSOT_v*.json"), {}) or {}
    rb = [s for w2 in book.get("workflows") or [] for s in w2.get("steps") or [] if s.get("finding_resolved_by")]
    chk("VCGC 冊尾版的 H4 帶 finding_resolved_by(核准 apply)", any(s.get("code") == "VCGC-WKF001-STP005" for s in rb),
        f"帶的步 {[s.get('code') for s in rb]}")
    body = Path(__file__).read_text(encoding="utf-8")
    chk("本支帶加速器橋 · 網路橋 · VIA_FROM_VCGC 標記", "[VIA:ACCEL-BRIDGE" in body and "[VIA:NET-BRIDGE" in body and "VIA_FROM_VCGC" in body)
    chk("不含 TA-Lib 匯入", not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", body, re.M))
    rc = PRIOR.selftest()
    return 0 if all(ok) and rc == 0 else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

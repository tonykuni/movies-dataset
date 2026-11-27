#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL245_SDDValidator v0110 — 薄尾(v0100–v0109 一字不動):主機實跑步可以指定「事件帳那一筆要帶哪些參數」(match_args)

PR #769 審查(Codex P2,讀碼重現屬實):工作流步的 match 只比「目標 + 動作」,而 VCGC 主控台記的動作是目標後第一個不帶 - 的參數。
操作員打 `run VCGC_CommandHub x via-prune --system VDF` → 事件帳的 act 是 `x`,不是 `via-prune`。
寫 match [["VCGC_CommandHub", "via-prune"]] 永遠對不到(主機跑過仍 NOT_RUN);寫成 "x" 又太寬(任何 x 短令都算)。
事件帳本來就存了 args(目標起算前 6 個),所以不改主控台、不改事件格式,只在驗證這一邊補一個欄:
  步上寫 match_args: ["via-prune", "--system", "VDF"] → 這一步只認「match 對得到、而且 args 裡有這一段(照順序、連在一起)」的那一筆;
  連在一起才算:別的系統的 prune(--system VRN)或 VDF 出現在別的旗標後面,都不能頂替(PR #769 Codex P2 第三輪);
  沒有這樣的事件 = NOT_RUN(主機沒跑過就不亮 OK);有 = 取最差的一次(同本體算法)。沒寫 match_args 的步一字不動。
步改過之後,整條工作流的燈照本體同一條式子重算。不改任何冊。零網路。不用 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
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
ENGINE = Path(__file__).stem
TAG = "v0110"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_PRIOR_REAL = BASE.real                       # 目前裝在本體上的那一支(v0102 包過的)
LAMP_ORDER = ("FAIL", "NOT_RUN", "FINDING", "NOSELFTEST", "CANON")   # 同本體 real() 的工作流燈式子


def __getattr__(name: str):
    return getattr(PRIOR, name)


def has_run(args: list, need: list) -> bool:
    """need 是不是 args 裡照順序、連在一起的一段。"""
    n = len(need)
    return n == 0 or any(args[i:i + n] == need for i in range(len(args) - n + 1))


def args_hits(step: dict, events: list) -> list:
    """這一步的 match 對得到、而且事件 args 裡有 match_args 這一段(照順序、連在一起)的事件。"""
    need = [str(a) for a in step.get("match_args") or []]
    out = []
    for e in events:
        args = [str(a) for a in e.get("args") or []]
        if not has_run(args, need):
            continue
        if any((e.get("target") or BASE.CONSOLE) == tgt and (vb is None or vb in BASE._act(e)) for tgt, vb in step.get("match") or []):
            out.append(e)
    return out


def workflow_lamp(steps: dict) -> str:
    states = [s.get("state") for s in steps.values()]
    return next((k for k in LAMP_ORDER if k in states), "OK")


def apply_match_args(rep: dict, state: dict, evs: list, ai_evs: list) -> list:
    """把寫了 match_args 的步重算一次;回改過的步碼。只動這些步與它們所在工作流的燈。"""
    changed = []
    for _sub, w in state.get("wkfs") or []:
        r = (rep.get("wkf") or {}).get(w.get("code"))
        if not r or r.get("state") == "REGISTERED_ONLY":
            continue
        mine = ai_evs if (w.get("tests") or {}).get("real_run") == "ai" else evs
        touched = False
        for st in w.get("steps") or []:
            if not (st.get("match") and st.get("match_args")):
                continue
            hit = args_hits(st, mine)
            if hit:
                worst = max(hit, key=lambda e: BASE.WORST.get(e.get("outcome"), 0))
                new = {"state": worst.get("outcome"), "rc": worst.get("rc"), "at": worst.get("ts"), "secs": worst.get("secs"),
                       "runs": len(hit), "by": "match_args:" + " ".join(st["match_args"])}
            else:
                new = {"state": "NOT_RUN", "by": "match_args:事件帳沒有帶 " + " ".join(str(a) for a in st["match_args"]) + " 的那一筆"}
            if (r["steps"].get(st["code"]) or {}).get("state") != new["state"]:
                changed.append(st["code"])
            r["steps"][st["code"]] = new
            touched = True
        if touched:
            r["state"] = workflow_lamp(r["steps"])
    return changed


def real(run: str | None = None, write: bool = True, ai_run: str | None = None) -> dict:
    rep = _PRIOR_REAL(run, write=False, ai_run=ai_run)
    _, evs = BASE.run_events(rep.get("run") or "no-run")
    _, ai_evs = BASE.run_events(rep.get("ai_run") or "no-run", "ai-")
    rep["engine"] = ENGINE
    rep["match_args_changed"] = apply_match_args(rep, BASE.load_books(), evs, ai_evs)
    if write:
        BASE.OUT.mkdir(parents=True, exist_ok=True)
        (BASE.OUT / "SDD_REAL_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


BASE.real = real                              # 本體 main() / closeout() 以模組全域叫 real()


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    n = {"ok": 0, "bad": 0}

    def chk(name, cond, note=""):
        n["ok" if cond else "bad"] += 1
        print("  " + ("[OK] " if cond else "[FAIL] ") + name + ((" · " + str(note)) if note else ""))

    print("=== " + ENGINE + " 自測(match_args:主機實跑步要對到事件帳帶指定參數的那一筆)===")
    hub = "VCGC_CommandHub"

    def ev(args, outcome="OK", rc=0):
        return {"verb": "run", "target": hub, "act": args[1] if len(args) > 1 else None, "args": args, "outcome": outcome, "rc": rc, "ts": "t", "secs": 1.0}

    def books(step_extra):
        st3 = dict({"code": "T-WKF001-STP003", "match": [[hub, "x"]]}, **step_extra)
        return {"wkfs": [(None, {"code": "T-WKF001", "tests": {}, "steps": [{"code": "T-WKF001-STP001"}, st3]})]}

    def rep0(s3):
        return {"wkf": {"T-WKF001": {"state": "OK", "steps": {"T-WKF001-STP001": {"state": "OK"}, "T-WKF001-STP003": {"state": s3}}}}}

    need = {"match_args": ["via-prune"]}
    r1 = rep0("OK")          # 本體用 match [hub, x]:任何 x 短令都算 → OK
    c1 = apply_match_args(r1, books(need), [ev([hub, "x", "via-graph", "status"])], [])
    chk("① 只跑過別的 x 短令(via-graph)→ 這一步 NOT_RUN、整條 NOT_RUN", r1["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["state"] == "NOT_RUN"
        and r1["wkf"]["T-WKF001"]["state"] == "NOT_RUN" and c1 == ["T-WKF001-STP003"], r1["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"].get("by"))
    r2 = rep0("NOT_RUN")
    apply_match_args(r2, books(need), [ev([hub, "x", "via-graph"]), ev([hub, "x", "via-prune", "--system", "VDF"])], [])
    chk("② 主機照文件打 x via-prune --system VDF → OK、整條 OK", r2["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["state"] == "OK" and r2["wkf"]["T-WKF001"]["state"] == "OK")
    r3 = rep0("OK")
    apply_match_args(r3, books(need), [ev([hub, "x", "via-prune"]), ev([hub, "x", "via-prune"], "FAIL", 1)], [])
    chk("③ 跑過兩次、一次失敗 → 取最差 FAIL(同本體)", r3["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["state"] == "FAIL" and r3["wkf"]["T-WKF001"]["state"] == "FAIL"
        and r3["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["runs"] == 2)
    r4 = rep0("OK")
    c4 = apply_match_args(r4, books({}), [ev([hub, "x", "via-graph"])], [])
    chk("④ 沒寫 match_args 的步一字不動", r4 == rep0("OK") and c4 == [])
    vdf = {"match_args": ["via-prune", "--system", "VDF"]}
    r5 = rep0("OK")
    apply_match_args(r5, books(vdf), [ev([hub, "x", "via-prune", "--system", "VRN"])], [])
    chk("⑤ 別的系統的 prune(--system VRN)不能頂替 VDF 這一步", r5["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["state"] == "NOT_RUN")
    r5b = rep0("OK")
    apply_match_args(r5b, books(vdf), [ev([hub, "x", "via-prune", "--system", "VRN", "--only", "VDF"]), ev([hub, "x", "via-prune", "VDF", "--system"])], [])
    chk("⑤b 要照順序連在一起:VDF 出現在別的旗標後面、或順序不對,都不算", r5b["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["state"] == "NOT_RUN")
    r5c = rep0("NOT_RUN")
    apply_match_args(r5c, books(vdf), [ev([hub, "x", "via-prune", "--system", "VRN"]), ev([hub, "x", "via-prune", "--system", "VDF"])], [])
    chk("⑤c VRN 與 VDF 都跑過 → 只算 VDF 那一筆(runs 1)· OK", r5c["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["state"] == "OK"
        and r5c["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["runs"] == 1)
    r6 = rep0("OK")
    apply_match_args(r6, books(need), [dict(ev([hub, "x", "via-prune"]), target="CGC_MDL237_NumberingSystem")], [])
    chk("⑥ 參數對但目標不是這一步的 match → 不算", r6["wkf"]["T-WKF001"]["steps"]["T-WKF001-STP003"]["state"] == "NOT_RUN")
    chk("⑦ 工作流燈式子同本體(FAIL > NOT_RUN > FINDING > … > OK)", workflow_lamp({"a": {"state": "OK"}, "b": {"state": "FINDING"}, "c": {"state": "NOT_RUN"}}) == "NOT_RUN"
        and workflow_lamp({"a": {"state": "OK"}}) == "OK" and workflow_lamp({"a": {"state": "FAIL"}, "b": {"state": "NOT_RUN"}}) == "FAIL")
    chk("⑧ 裝進本體:本體叫的 real 就是本版", BASE.real is real)
    chk("⑨ 加速器真的載到(VIA_ACCEL 非空)", VIA_ACCEL is not None)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 加速器橋在語法樹匯入 · 不含本機路徑", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and ("C:" + "\\Users") not in src)
    live = real("no-such-run-zzz", write=False, ai_run="ai-no-such-run-zzz")
    marked = [(w["code"], st["code"]) for _s, w in BASE.load_books()["wkfs"] for st in w.get("steps") or [] if st.get("match_args")]
    chk("⑪ 真冊:寫了 match_args 的步在沒有事件的一輪全是 NOT_RUN(" + str(len(marked)) + " 步)",
        all(((live["wkf"].get(w) or {}).get("steps") or {}).get(s, {}).get("state") == "NOT_RUN" for w, s in marked), marked[:3])
    prc = PRIOR.selftest() if hasattr(PRIOR, "selftest") else 0
    chk("⑫ 前版自測照過", prc == 0, "rc " + str(prc))
    print("[計] " + ENGINE + " 本版 " + str(n["ok"]) + "/" + str(n["ok"] + n["bad"]) + " · " + ("PASS" if n["bad"] == 0 else "FAIL"))
    return 0 if n["bad"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

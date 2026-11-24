#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0114 — 薄尾(v0100–v0113 一字不動):via-install 的計畫要是「這一輪、這份請求」的才裝(PR #735 Codex P1)

Codex P1(對 v0112):「via-install --yes <件> 沒帶 --plan-check 時,計畫檢查子行程失敗,這條路照讀上一輪的 PLANCHECK_latest.json
  再走 --from-plan;同一環境近期的綠計畫會通過 InstallGate v0106 的驗證 → 裝的是一份舊的、無關的套件組,即使這一輪的檢查失敗了。」
  (FastRun v0105 已修同類問題;中樞自己的 install 這條路還沒修。)
本版 install 在 --plan-check 子行程跑完後多三道關,任一不過 → 零安裝、rc 3:
  ① 子行程回的是正常判決碼(0 綠 / 黃 · 1 紅 · 2 灰);逾時(124)或其他當掉的碼 → 停。
  ② PLANCHECK_latest.json 是這一輪寫的(修改時間不早於本步開始)。
  ③ 計畫的 request 就是這一輪要裝的那份清單(同樣的件、同樣順序)。
其餘(--plan-check 只查 · --from-plan 照最新計畫裝 · 沒給件取 doctor 計畫 · 舊閘退回 v0101)照 v0112。不 import 他系統。零 TA-Lib。
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

import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0114"
PLAN_RCS = (0, 1, 2)                                     # 安裝閘 --plan-check 的正常判決碼


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name: str):
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


H112 = _owner("parse_install")                           # v0112:install 的本體(route 叫它模組裡的 cmd_install)
INSTALL_OWNER = H112.INSTALL_OWNER


def fresh_plan(path: Path, since: float, pkgs: list) -> tuple:
    """回 (計畫, 原因);計畫不是這一輪寫的、或不是這份請求 → (None, 原因)。"""
    try:
        if path.stat().st_mtime < since - 2:
            return None, "計畫檔不是這一輪寫的(是上一輪留下的)"
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "這一輪沒有寫出計畫檔"
    if list(plan.get("request") or []) != list(pkgs):
        return None, "計畫的請求不是這一輪要裝的那份"
    return plan, ""


def cmd_install(args: list, run=subprocess.run) -> int:
    o = H112.parse_install(args)
    gate = H112._gate()
    if not gate or "def plan_check" not in gate.read_text(encoding="utf-8", errors="replace") or o["from_plan"]:
        return _INSTALL_V0112(args, run=run)          # 舊閘 / --from-plan:照 v0112(安裝閘 v0106 自己驗計畫的目標環境)
    pkgs = o["pkgs"]
    if not pkgs:
        rep = INSTALL_OWNER.PRIOR._read_json(INSTALL_OWNER.DOCTOR_DIR / "DOCTOR_latest.json")
        if not rep:
            print("[install] 沒有 DOCTOR_latest.json → 先跑 via-doctor。")
            return 2
        pkgs = rep.get("plan", {}).get("pip", [])
    bad = [p for p in pkgs if not INSTALL_OWNER._PKG_RX.match(p)]
    if bad:
        print("[install] 套件名不合法,拒絕(零安裝):%s" % bad)
        return 2
    if not pkgs:
        print("[install] 計畫是空的:沒有要裝的。")
        return 0
    print("[install] 安裝閘 %s · %d 件:%s" % (gate.name, len(pkgs), " ".join(pkgs)))
    q = "先三鏡像查衝突(零安裝)%s?同意閘只在安裝閘子行程,輸入 YES 繼續:" % ("" if o["check_only"] else ",沒問題再依計畫一次裝")
    if not INSTALL_OWNER._yes(q, o["yes"]):
        print("[取消] 同意閘未開,未查、未裝。")
        return 1
    t0 = time.time()
    rc = run([sys.executable, str(gate), "--plan-check", *pkgs], cwd=str(INSTALL_OWNER.tool_root(gate)), env=H112._gate_env(gate)).returncode
    if o["check_only"]:
        return rc
    if rc not in PLAN_RCS:
        print("[install] 計畫檢查這一輪沒跑完(rc %s)→ 零安裝(不拿上一輪的計畫當依據)" % rc)
        return 3
    plan, why = fresh_plan(H112._plan_file(gate), t0, pkgs)
    if plan is None:
        print("[install] %s → 零安裝(不拿上一輪的計畫當依據)" % why)
        return 3
    lamp, todo = plan.get("lamp", "GRAY"), plan.get("plan") or []
    if lamp not in ("GREEN", "YELLOW") or plan.get("new_conflicts"):
        print("[install] 計畫燈 %s → 零安裝(先處理上面的原因再重跑)" % lamp)
        return 2 if lamp == "GRAY" else 1
    if not todo:
        sp = plan.get("special") or []
        print("[install] base 沒有要裝的%s" % ((" · %d 件屬特殊環境,單獨安裝:via-envgov plan → via-envgov apply --approve" % len(sp)) if sp else "(要的都已經裝好)"))
        return 0
    print("[install] 計畫燈 %s · 依計畫一次裝 %d 件(釘版)" % (lamp, len(todo)))
    rc2 = run([sys.executable, str(gate), "--from-plan"], cwd=str(INSTALL_OWNER.tool_root(gate)), env=H112._gate_env(gate)).returncode
    print("[install] 安裝閘 rc %s(同意閘只存在於子行程,本行程未設)" % rc2)
    return rc2


_INSTALL_V0112 = H112.cmd_install
H112.cmd_install = cmd_install                           # v0112 route / main 叫它模組裡的 cmd_install


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    import os
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 5 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 換在 v0112 那一層(route 讀的 cmd_install)· 前版 v0113", Path(H112.__file__).name == "VCGC_CommandHub_v0112.py"
        and H112.cmd_install is cmd_install and PRIOR_PATH.name == "VCGC_CommandHub_v0113.py")
    with tempfile.TemporaryDirectory(prefix="hub114_") as td:
        pf = Path(td) / "PLANCHECK_latest.json"
        old = time.time() - 3600
        calls = []

        def scenario(pc_rc=0, writes=True, request=None, lamp="GREEN"):
            calls.clear()
            pf.write_text(json.dumps({"lamp": "GREEN", "plan": ["old==1"], "new_conflicts": [], "request": ["old"]}), encoding="utf-8")
            os.utime(pf, (old, old))                       # 上一輪留下的綠計畫

            def run(argv, cwd=None, env=None):
                calls.append(argv[2])
                if argv[2] == "--plan-check" and writes:
                    pf.write_text(json.dumps({"lamp": lamp, "plan": ["rich==1"], "new_conflicts": [], "request": request or argv[3:]}), encoding="utf-8")
                return type("R", (), {"returncode": pc_rc if argv[2] == "--plan-check" else 0})()
            with contextlib.redirect_stdout(io.StringIO()):
                rc = cmd_install(["--yes", "rich"], run=run)
            return rc, list(calls)
        keep, keep_yes = H112._plan_file, INSTALL_OWNER._yes
        H112._plan_file = lambda gate: pf
        INSTALL_OWNER._yes = lambda prompt, assume_yes: assume_yes
        try:
            r1 = scenario(pc_rc=124, writes=False)
            r2 = scenario(pc_rc=0, writes=False)
            r3 = scenario(request=["numpy"])
            r4 = scenario()
            r5 = scenario(pc_rc=1, lamp="RED")
        finally:
            H112._plan_file, INSTALL_OWNER._yes = keep, keep_yes
    chk("T2 Codex 重現:計畫檢查 rc 124、只剩上一輪的綠計畫 → 零安裝(rc 3 · 沒叫 --from-plan)", r1 == (3, ["--plan-check"]), r1)
    chk("T3 子行程回 0 但沒寫出新計畫(舊檔還在)→ 零安裝", r2 == (3, ["--plan-check"]), r2)
    chk("T4 計畫是這一輪寫的、但請求不是這份 → 零安裝;都對 → 照計畫裝", r3 == (3, ["--plan-check"]) and r4 == (0, ["--plan-check", "--from-plan"]), (r3, r4))
    chk("T5 紅計畫(rc 1 · 這一輪寫的)照 v0112 拒裝 rc 1", r5 == (1, ["--plan-check"]), r5)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(cmd_install 還原成前版的)" % PRIOR_PATH.name, flush=True)
    H112.cmd_install = _INSTALL_V0112
    try:
        rc_prior = PRIOR.selftest()
    finally:
        H112.cmd_install = cmd_install
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

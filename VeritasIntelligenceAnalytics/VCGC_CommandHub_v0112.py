#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0112 — 薄尾(v0100–v0111 一字不動):via-install 改成「先三鏡像查衝突 → 環境確認無誤 → 依計畫一次裝」

操作員 2026-11-24 原文:「更快先檢查經過衝突檢測三鏡像共同檢查衝突後環境確認無誤進行安裝計畫 依計畫安裝不用編裝邊測
  這個流程要寫入環境安裝規範」。v0101 的 install 是把套件直接丟給安裝閘(閘裡裝下去才 pip check,衝突裝了才看得到;
  一件解不出整批 rc 1)。本版 install 一律兩步(都經安裝閘 CGC_MDL056 尾版,同意閘只在閘的子行程設):
    ① --plan-check:三鏡像(清華 · 阿里 · 官方)同時解析 → 解不出的件點名剔除 → 疊到現況推算裝後新增衝突 → 寫計畫(零安裝)
    ② 計畫燈綠 / 黃且有東西要裝 → --from-plan 照計畫一次裝完(釘版),裝完才驗一次;紅 / 灰 → 零安裝,印原因
  可單獨跑:install --plan-check [件…](只查)· install --from-plan(照最新計畫裝)。沒給件 = 取 via-doctor 的計畫。
  安裝閘尾版沒有 --plan-check(舊閘)→ 照 v0101 原路裝並明說。不 import 他系統。零 TA-Lib。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0112"


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
    """前版鏈上自己定義 name 的那一版(換在真正被讀的那一層;R4 換錯層)。"""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


DISPATCH_OWNER = _owner("dispatch")          # v0102:dispatch 讀它的 main
INSTALL_OWNER = _owner("cmd_install")        # v0101:原本的 install(舊閘時退回它)
_PREV_MAIN = DISPATCH_OWNER.main             # = v0111 的 route


def _gate():
    return INSTALL_OWNER.find_tail("CGC_MDL056_InstallGate")


def _gate_env(gate: Path) -> dict:
    return INSTALL_OWNER._child_env({"VIA_NET_CONSENT": "YES"}, root=INSTALL_OWNER.tool_root(gate))


def _plan_file(gate: Path) -> Path:
    return INSTALL_OWNER.tool_root(gate) / "VIA_Reports" / "install_gate" / "PLANCHECK_latest.json"


def parse_install(args: list) -> dict:
    return {"yes": "--yes" in args, "check_only": "--plan-check" in args, "from_plan": "--from-plan" in args,
            "pkgs": [x for x in args if not x.startswith("--")]}


def cmd_install(args: list, run=subprocess.run) -> int:
    o = parse_install(args)
    gate = _gate()
    if not gate:
        print("[install] 找不到 CGC_MDL056_InstallGate 尾版 → 不裝(不直接 pip)。")
        return 2
    if "def plan_check" not in gate.read_text(encoding="utf-8", errors="replace"):
        print("[install] 安裝閘 %s 是舊版(沒有 --plan-check)→ 照 v0101 原路裝" % gate.name)
        return INSTALL_OWNER.cmd_install(o["pkgs"], o["yes"])
    if o["from_plan"]:
        if not INSTALL_OWNER._yes("照最新的計畫一次裝(同意閘只在安裝子行程)?輸入 YES 繼續:", o["yes"]):
            print("[取消] 同意閘未開,未安裝。")
            return 1
        return run([sys.executable, str(gate), "--from-plan"], cwd=str(INSTALL_OWNER.tool_root(gate)), env=_gate_env(gate)).returncode
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
    rc = run([sys.executable, str(gate), "--plan-check", *pkgs], cwd=str(INSTALL_OWNER.tool_root(gate)), env=_gate_env(gate)).returncode
    try:
        plan = json.loads(_plan_file(gate).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        plan = {}
    lamp, todo = plan.get("lamp", "GRAY"), plan.get("plan") or []
    if o["check_only"]:
        return rc
    if lamp not in ("GREEN", "YELLOW") or plan.get("new_conflicts"):
        print("[install] 計畫燈 %s → 零安裝(先處理上面的原因再重跑)" % lamp)
        return 2 if lamp == "GRAY" else 1
    if not todo:
        print("[install] 要的都已經裝好 → 不用裝")
        return 0
    print("[install] 計畫燈 %s · 依計畫一次裝 %d 件(釘版)" % (lamp, len(todo)))
    rc2 = run([sys.executable, str(gate), "--from-plan"], cwd=str(INSTALL_OWNER.tool_root(gate)), env=_gate_env(gate)).returncode
    print("[install] 安裝閘 rc %s(同意閘只存在於子行程,本行程未設)\nNEXT: via-doctor --only envtools gate_conflict gate_doctor(裝後只驗一次)" % rc2)
    return rc2


def route(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["install"]:
        return cmd_install(a[1:])
    return _PREV_MAIN(a)


DISPATCH_OWNER.main = route
_c = DISPATCH_OWNER.CMD.get("via-install")
if _c is not None and "--plan-check" not in _c["help"]:
    _c["help"] = ("先三鏡像(清華 · 阿里 · 官方)同時解析查衝突(零安裝)→ 解不出的點名剔除 · 推算裝後新增衝突 → "
                  "綠 / 黃才依計畫一次裝完(釘版)· 裝完驗一次。--plan-check 只查 · --from-plan 照最新計畫裝 · 沒給件取 via-doctor 計畫。")
    _c["examples"] = ["via-install --yes", "via-install --plan-check", "via-install --from-plan --yes", "via-install --yes rich"]
    _c["title"] = "先查衝突再依計畫安裝(走 VCGC 安裝閘)"
_h = DISPATCH_OWNER.CMD.get("via-health")
if _h is not None and "環境安裝規範" not in _h["help"]:
    _h["help"] = ("照環境安裝規範(docs/VIA_Environment_EightHub_Policy_v0101.md)一行跑完:① 全面檢視 base / via_core / via_* "
                  "(八路 · pip check · 多層互撞 · 工具冊 · 加速器)→ ② 有衝突風險就不新增、印重建指令 → ③ 沒裝的工具列入新增 → "
                  "④ 特殊環境 / 分類件分出去單獨安裝 → ⑤ 三鏡像查衝突 → ⑥ 寫計畫 → ⑦ 直接照計畫裝、不再測;"
                  "VRN / VDF health 與環境總管並行。--set 換組 · --push 推收據(只有雜湊與數字)。")


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["install"]:
        return cmd_install(a[1:])
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 換在 dispatch 讀的那一層(v0102)· 原 install 在 v0101 · 前版 v0111",
        Path(DISPATCH_OWNER.__file__).name == "VCGC_CommandHub_v0102.py" and Path(INSTALL_OWNER.__file__).name == "VCGC_CommandHub_v0101.py"
        and DISPATCH_OWNER.main is route and PRIOR_PATH.name == "VCGC_CommandHub_v0111.py")
    g = _gate()
    chk("T2 安裝閘尾版有 --plan-check(三鏡像)· 指令冊 via-install 說明換新", g is not None and "def plan_check" in g.read_text(encoding="utf-8")
        and "--plan-check" in DISPATCH_OWNER.CMD["via-install"]["help"], g)
    with tempfile.TemporaryDirectory(prefix="hub112_") as td:
        pf = Path(td) / "PLANCHECK_latest.json"
        calls = []

        def fake(lamp, plan, new=()):
            def run(argv, cwd=None, env=None):
                calls.append((argv[2:], env.get("VIA_NET_CONSENT")))
                if "--plan-check" in argv:
                    pf.write_text(json.dumps({"lamp": lamp, "plan": plan, "new_conflicts": list(new)}), encoding="utf-8")
                return type("R", (), {"returncode": 0})()
            return run
        keep, keep_yes = globals()["_plan_file"], INSTALL_OWNER._yes
        globals()["_plan_file"] = lambda gate: pf
        INSTALL_OWNER._yes = lambda prompt, assume_yes: assume_yes      # 沒打 YES = 操作員沒同意(不等鍵盤)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                calls.clear()
                rc_g = cmd_install(["--yes", "rich", "jieba"], run=fake("GREEN", ["rich==1"]))
                c_g = list(calls)
                calls.clear()
                rc_r = cmd_install(["--yes", "rich"], run=fake("RED", ["rich==1"], ["x"]))
                c_r = list(calls)
                calls.clear()
                rc_c = cmd_install(["--yes", "--plan-check", "rich"], run=fake("GREEN", ["rich==1"]))
                c_c = list(calls)
                calls.clear()
                rc_n = cmd_install(["rich"], run=fake("GREEN", ["rich==1"]))
                c_n = list(calls)
        finally:
            globals()["_plan_file"], INSTALL_OWNER._yes = keep, keep_yes
    chk("T3 綠:先 --plan-check 再 --from-plan(兩個子行程都帶同意閘 · 本行程沒設)",
        rc_g == 0 and [c[0][0] for c in c_g] == ["--plan-check", "--from-plan"] and c_g[0][0][1:] == ["rich", "jieba"]
        and all(c[1] == "YES" for c in c_g), c_g)
    chk("T4 紅(推算有新衝突):只查不裝 · rc 1", rc_r == 1 and [c[0][0] for c in c_r] == ["--plan-check"], c_r)
    chk("T5 --plan-check 只查 · 沒打 YES 就一個子行程都不起", rc_c == 0 and [c[0][0] for c in c_c] == ["--plan-check"] and rc_n == 1 and not c_n, (c_c, c_n))
    seen = []
    keep_route = DISPATCH_OWNER.main
    try:
        globals()["cmd_install"] = lambda args, run=None: seen.append(args) or 0
        with contextlib.redirect_stdout(io.StringIO()):
            r = [main(["x", "via-install", "--yes"]), DISPATCH_OWNER.dispatch("via-install", ["--plan-check"]), main(["install", "--from-plan", "--yes"])]
    finally:
        globals()["cmd_install"] = INSTALL_FN
        DISPATCH_OWNER.main = keep_route
    chk("T6 三條路(x 短令 · 選單 dispatch · 直接 install)都走本版(新旗標不被 v0101 的 argparse 擋掉)",
        r == [0, 0, 0] and seen == [["--yes"], ["--plan-check"], ["--from-plan", "--yes"]], (r, seen))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(dispatch 讀的 main 還原成前版的)" % PRIOR_PATH.name, flush=True)
    DISPATCH_OWNER.main = _PREV_MAIN
    try:
        rc_prior = PRIOR.selftest()
    finally:
        DISPATCH_OWNER.main = route
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


INSTALL_FN = cmd_install

if __name__ == "__main__":
    raise SystemExit(main())

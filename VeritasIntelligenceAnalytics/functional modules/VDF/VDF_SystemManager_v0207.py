#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0207 — 薄尾(v0206 以前一字不動):hostrun —— 主機一次跑完「該檢查的全部」並寫一份摘要

操作員 2026-11-28:「one ps to handle all」。PS(Invoke-VDF-HostRun-v0100.ps1)只負責更新倉 · 叫本動詞 · 摘要進剪貼簿;
  要跑什麼、怎麼判、摘要留哪些行,全在這裡(CLAUDE.md L117:判斷與流程寫在 Python)。
  hostrun [--full] [--only 家族,家族]    唯讀:依序跑(每一步畫面照常印、不吞輸出)
    ① tidy plan(只乾跑,不搬)
    ② vv --engines-only(預設只跑上一輪還沒過的那幾支;--full = 全部引擎;--only 自己點名)
    ③ outputs(輸出對表頭冊)
    ④ ENG232 尾版 --check-db(資料家 tw_index 庫的數字欄型)
  摘要:拿掉心跳與 tidy 的逐項清單,只留各步的燈、[不過] / [原因] / [重跑]、outputs 的黃紅、[temp]、check-db 那行;
    寫到 VIA_Reports/vdf/manager/HOSTRUN_latest.txt(PS 會複製到剪貼簿)。rc = 最差那一步的燈。
  任何寫入 / 搬移(tidy apply、擷取)都不在這個動詞裡 —— 照舊要操作員另外下。
零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

VERSION = "v0207"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent
DEFAULT_ONLY = ("VDF_ENG068,VDF_ENG232,VDF_LocalIntegrateLaunch,VDF_MDL008,VDF_MDL013,VDF_MDL020,VDF_MDL022,VDF_SystemManager")
KEEP_RX = re.compile(r"(tidy plan|vv (RED|YELLOW|GREEN)|outputs (RED|YELLOW|GREEN)|① 驗證|\[自測環境\]|\[不過\]|\[原因\]|\[重跑\]|"
                     r"^\s{9}\S|^\s*(RED|YELLOW) OUT-|\[temp\]|^\s+(OK|NO) temp|\[不搬\]|check-db|\[hostrun\]|Traceback|Error)")
DROP_RX = re.compile(r"\[心跳\]")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0206
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V198 = PRIOR.V198
V194 = V198.V194
LAMP_RC = {0: "GREEN", 2: "YELLOW", 3: "GRAY", 124: "RED"}


def tail_of(folder: Path, stem: str) -> Path | None:
    hits = sorted(folder.glob(stem + "_v*.py"), key=_vnum)
    return hits[-1] if hits else None


def stream(cmd: list, timeout: int, out: list) -> int:
    """子行程輸出逐行照印(不吞)、同時收進 out;逾時照實回 124。"""
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    t0 = time.time()
    p = subprocess.Popen(cmd, cwd=tempfile.gettempdir(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL)
    try:
        for ln in p.stdout:
            print(ln, end="", flush=True)
            out.append(ln.rstrip("\n"))
            if time.time() - t0 > timeout:
                p.kill()
                out.append(f"[hostrun] 逾時 {timeout}s → 停")
                return 124
        return p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
        return 124


def summarize(lines: list) -> list:
    return [ln for ln in lines if KEEP_RX.search(ln) and not DROP_RX.search(ln)]


def plan_steps(args: list) -> list:
    me = str(Path(__file__).resolve())
    py = sys.executable
    only = args[args.index("--only") + 1] if "--only" in args else DEFAULT_ONLY
    vv = [py, me, "vv", "--engines-only"] + ([] if "--full" in args else ["--only", only])
    steps = [("① tidy plan(乾跑)", [py, me, "tidy", "plan"], 600),
             ("② vv " + ("全部引擎" if "--full" in args else "上一輪沒過的"), vv, 7200),
             ("③ outputs", [py, me, "outputs"], 1800)]
    via = V194._p("sm_via_root")()
    e232 = tail_of(via / "functional modules" / "VDF" / "engine", "VDF_ENG232_TWIndexOfficial")
    try:
        h, _why = V198.V195.dataplane(via).P.resolve_home(None)   # 主程序的資料家(不受自測隔離影響)
    except Exception:  # noqa: BLE001 — 解析不了 = 略過 check-db,照實記
        h = None
    db = Path(h) / "output_hub" / "tw_index" / "VDF_TWIndex_Daily.duckdb" if h else None
    if e232 and db and db.is_file():
        steps.append(("④ ENG232 check-db", [py, str(e232), "--check-db", str(db)], 300))
    else:
        steps.append(("④ ENG232 check-db", None, 0))
    return steps


def cmd_hostrun(args: list) -> int:
    via = V194._p("sm_via_root")()
    out_dir = V194._p("v73_out")(via)
    t0 = time.time()
    summary = [f"[hostrun] {TAG} · {time.strftime('%Y-%m-%d %H:%M:%S')} · 唯讀(tidy 只乾跑 · 不擷取 · 不搬)"]
    worst = "GREEN"
    for name, cmd, to in plan_steps(args):
        print(f"\n[hostrun] ==== {name} ====", flush=True)
        if cmd is None:
            msg = f"[hostrun] {name} · 略過(找不到資料家或庫 VDF_TWIndex_Daily.duckdb)"
            print(msg, flush=True)
            summary.append(msg)
            continue
        lines: list = []
        rc = stream(cmd, to, lines)
        lamp = LAMP_RC.get(rc, "RED")
        if name.startswith("④") and rc == 1:
            lamp = "YELLOW"                                    # check-db rc 1 = 有欄被推成整數型(要處理,不是程式壞)
        worst = V194.worst([worst, lamp]) if lamp != "GRAY" else worst
        summary.append(f"[hostrun] {name} · rc {rc} · {lamp}")
        summary += summarize(lines)
    summary.append(f"[hostrun] 總燈 {worst} · {round(time.time() - t0, 1)}s")
    f = out_dir / "HOSTRUN_latest.txt"
    f.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n" + "\n".join(summary[-1:]) + f"\n[收據] {f.relative_to(via)}", flush=True)
    return {"GREEN": 0, "YELLOW": 2}.get(worst, 1)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    raw = ["  [心跳] x · 25s", "[VDF_SystemManager v0194] vv RED · 牆鐘 9s", "     [不過] A · rc 1", "  [原因] A · rc 1",
           "         [FAIL] ① 壞了", "     OK output_hub\\orders\\ORDER_1 → x", "  YELLOW OUT-03 etf_book  契約 GREEN", "  GREEN OUT-04 x",
           "  [temp] 4 項", "     OK temp\\VDF_Manager_v0104\\setup_a → q"]
    got = summarize(raw)
    chk("T2 摘要:留燈 / 不過 / 原因 / 原因下一行 / outputs 黃紅 / temp;丟心跳、runs 逐項、outputs 綠",
        got == [raw[1], raw[2], raw[3], raw[4], raw[6], raw[8], raw[9]], got)
    steps = plan_steps([])
    vvs = next(c for n, c, _t in steps if n.startswith("②"))
    full = next(c for n, c, _t in plan_steps(["--full"]) if n.startswith("②"))
    chk("T3 步驟:tidy 只有 plan(沒有 apply)· vv 預設只跑上一輪沒過的 · --full 全部 · 沒有資料家時 check-db 略過",
        [n[0] for n, *_ in steps] == ["①", "②", "③", "④"] and "apply" not in steps[0][1] and "--only" in vvs and "--only" not in full
        and steps[3][1] is None, steps)
    lines: list = []
    rc = stream([sys.executable, "-c", "print('a');print('b')"], 30, lines)
    chk("T4 子行程輸出逐行照印並收下 · rc 照實", rc == 0 and lines == ["a", "b"], (rc, lines))
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T5 前版 v0206 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["hostrun"]:
        return cmd_hostrun(a[1:])
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

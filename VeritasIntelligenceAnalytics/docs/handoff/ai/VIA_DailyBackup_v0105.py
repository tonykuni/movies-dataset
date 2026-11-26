#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_DailyBackup v0105 — 薄尾(v0104 以前一字不動):G2 環境閘不收舊收據

PR #749 審查(Codex P2,讀碼重現屬實):v0104 gate_doctor 不管這次 doctor 的 rc,只讀 VIA_Reports\vcgc_hub\doctor\DOCTOR_latest.json。
上一輪留下的 GREEN 收據還在、這一輪 doctor 逾時(rc 124)或當掉 → 仍回 GREEN → do_full 照燈放行備份(Fail-Closed 失守)。
本版:G2 只收「這一次叫出來、且 rc 是 doctor 會正常結束的值(0 綠 · 1 紅 · 2 黃)」並且「收據檔在這次叫之後才寫」的結果;
其餘(逾時 124 · 找不到中樞 3 · 其他 rc · 收據沒更新)一律 RED 並寫原因 → Fail-Closed 照擋。其餘照 v0104。
不用 TA-Lib · 不設同意閘 · 不出網。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    import os as _sa_os
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.insert(0, _sa_Path(_sa_os.environ["VIA_REPO"]).resolve() / "VeritasIntelligenceAnalytics")
    for _sa_p in _sa_roots:
        _sa_hit = None
        while True:
            for _sa_c in (_sa_p, _sa_p / "VeritasIntelligenceAnalytics"):
                if (_sa_c / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit or _sa_p.parent == _sa_p:
                break
            _sa_p = _sa_p.parent
        if _sa_hit:
            _sa_sys.path.insert(0, str(_sa_hit / "supportive modules"))
            break
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

VERSION = "v0105"
FAMILY = "VIA_DailyBackup"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
DOCTOR_OK_RC = (0, 1, 2)                     # doctor 正常結束的 rc(綠 · 紅 · 黃);其他 = 這次沒有可信的結果


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def doctor_receipt(via: Path) -> Path:
    return via / "VIA_Reports" / "vcgc_hub" / "doctor" / "DOCTOR_latest.json"


_ORIG_GATE = PRIOR.gate_doctor


def gate_doctor(via: Path) -> dict:
    """前版的 G2 加兩道:這次 doctor 的 rc 要正常 · 收據要是這次寫的;任一不成立 = RED(不吃上一輪的舊收據)。"""
    t0 = time.time()
    res = _ORIG_GATE(via)
    p = doctor_receipt(via)
    fresh = p.is_file() and p.stat().st_mtime >= t0 - 1.0
    why = []
    if res.get("rc") not in DOCTOR_OK_RC:
        why.append(f"這次 doctor rc {res.get('rc')}(逾時 / 當掉 / 找不到中樞)")
    if not fresh:
        why.append("DOCTOR_latest.json 不是這次寫的(舊收據不收)")
    if why:
        res = dict(res, lamp="RED", red=sorted(set(res.get("red") or []) | {"doctor_run"}),
                   note=" · ".join(why) + (" · " + res["note"] if res.get("note") else ""))
    res["fresh_receipt"] = fresh
    return res


def _install():
    PRIOR.gate_doctor = gate_doctor
    PRIOR.TAG = TAG


def _uninstall():
    PRIOR.gate_doctor = _ORIG_GATE
    PRIOR.TAG = f"{FAMILY} v{_vnum(PRIOR_PATH):04d}"


_install()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    keep_run = PRIOR.hub_run
    try:
        with tempfile.TemporaryDirectory() as td:
            via = Path(td)
            rp = doctor_receipt(via)
            rp.parent.mkdir(parents=True)
            green = json.dumps({"lamp": "GREEN", "plugins": [{"key": "accel", "lamp": "GREEN"}], "counts": {}, "plan": {}})
            rp.write_text(green, encoding="utf-8")
            old = time.time() - 3600
            os.utime(rp, (old, old))
            PRIOR.hub_run = lambda via_, args, timeout=3600, capture=True: (124, "逾時 3600s")
            r1 = gate_doctor(via)
            chk("② 舊 GREEN 收據還在 + 這次 doctor 逾時(rc 124)→ RED(Codex P2 重現案例)",
                r1["lamp"] == "RED" and "rc 124" in r1["note"] and r1["fresh_receipt"] is False, r1)

            def ran_ok(via_, args, timeout=3600, capture=True):
                rp.write_text(green, encoding="utf-8")
                return 0, "ok"
            PRIOR.hub_run = ran_ok
            r2 = gate_doctor(via)
            chk("③ 這次 doctor rc 0 且收據是這次寫的 → 照收據燈(GREEN)", r2["lamp"] == "GREEN" and r2["fresh_receipt"] is True, r2)
            os.utime(rp, (old, old))
            PRIOR.hub_run = lambda via_, args, timeout=3600, capture=True: (0, "ok but no write")
            r3 = gate_doctor(via)
            chk("④ rc 0 但收據沒更新 → RED(不收舊收據)", r3["lamp"] == "RED" and "不是這次寫的" in r3["note"], r3)

            def ran_red(via_, args, timeout=3600, capture=True):
                rp.write_text(json.dumps({"lamp": "RED", "plugins": [{"key": "accel", "lamp": "RED"}]}), encoding="utf-8")
                return 1, "red"
            PRIOR.hub_run = ran_red
            r4 = gate_doctor(via)
            chk("⑤ doctor 正常跑完回紅(rc 1)→ 照收據 RED · 點名 accel(不多加 doctor_run)",
                r4["lamp"] == "RED" and "accel" in r4["red"] and "doctor_run" not in r4["red"], r4)
    finally:
        PRIOR.hub_run = keep_run
    chk("⑥ do_full 叫的 gate_doctor 是本版(裝在 v0104 模組全域)", PRIOR.gate_doctor is gate_doctor)
    _uninstall()
    try:
        rc_p = PRIOR.selftest()
    finally:
        _install()
    chk("⑦ 前版 v0104 自測(本版換裝卸下)照過", rc_p == 0, rc_p)
    src = HERE.read_text(encoding="utf-8")
    chk("⑧ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.parent.glob(FAMILY" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

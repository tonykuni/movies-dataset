#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_FastRun v0101 — 薄尾(v0100 一字不動;v0100 已鎖成功,修改開新版):執行失敗不能被 JSON 的綠燈蓋掉(PR 726 Codex P2)

  v0100 的 brief():子行程 stdout 有 JSON 就直接用 JSON 裡的燈,不看回傳碼 —— 先印 {"lamp":"GREEN"} 再逾時(rc 124)
  或報錯退出的,整項還是綠,summarize() 跟 main() 的回傳碼也跟著綠。
  本版:每項的燈 = JSON 的燈 與 回傳碼的燈 取較差;回傳碼的燈:0 綠 · 2 / 3 / 4 黃(各系統的「黃 / 缺件 / 等同意閘」)· 其他(含 124 逾時)紅,
  紅的那一項另加 `rc=<碼>` 要點。其餘(VCGC 一次過閘 · 並行道數 · 每項一行 · .log.txt · --push)全照 v0100。
  經 VCGC 重新進來時跑的是本檔(不是 v0100);輸出的工具名是本版。
用法同 v0100:python VIA_FastRun_v0101.py [--set all|nlp,vrn,vdf] [--lanes N] [--timeout 秒] [--push] [--selftest]
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

import contextlib
import importlib.util
import io
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VIA_FastRun"
TAG = "VIA_FastRun v0101"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_BRIEF_V0100 = PRIOR.brief
_PRIOR_HERE, _PRIOR_TAG = PRIOR.HERE, PRIOR.TAG


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def rc_lamp(rc: int) -> str:
    return "GREEN" if rc == 0 else ("YELLOW" if rc in (2, 3, 4) else "RED")


def brief(job: dict, rc: int, secs: float, stdout: str, stderr: str) -> dict:
    """v0100 的要點照用;燈 = JSON 的燈 與 回傳碼的燈 取較差(失敗 / 逾時不能是綠)。"""
    r = _BRIEF_V0100(job, rc, secs, stdout, stderr)
    by_rc = rc_lamp(rc)
    if PRIOR.ORDER.get(by_rc, 3) > PRIOR.ORDER.get(r["lamp"], 3):
        r["lamp"] = by_rc
        if by_rc == "RED" and not any(b.startswith("rc=") for b in r["bits"]):
            r["bits"].insert(0, f"rc={rc}" + ("(逾時)" if rc == 124 else ""))
    return r


def _install():
    PRIOR.brief = brief                    # v0100 run_job 叫模組全域 brief → 換上本版
    PRIOR.HERE = HERE                      # 經 VCGC 重新進來時跑本檔
    PRIOR.TAG = TAG


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
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    PRIOR.HERE, PRIOR.TAG = _PRIOR_HERE, _PRIOR_TAG                     # 前版自測照前版的檔與名字跑(它會讀自己的原始碼)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc0 = PRIOR.selftest()
    finally:
        _install()
    print(f"=== {TAG} · 薄尾自測(執行失敗不能是綠 · 前版原封不動;暫存夾 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過(本版的 brief 換上後前版 15 項照樣過)" % PRIOR_PATH.name, rc0 == 0, buf.getvalue()[-300:])
    with tempfile.TemporaryDirectory(prefix="via_fastrun101_") as td:
        t = Path(td)
        g_slow = t / "green_then_sleep.py"
        g_slow.write_text("import json,time\nprint(json.dumps({'lamp':'GREEN'}),flush=True)\ntime.sleep(5)\n", encoding="utf-8")
        g_fail = t / "green_then_fail.py"
        g_fail.write_text("import json,sys\nprint(json.dumps({'lamp':'GREEN'}))\nsys.exit(1)\n", encoding="utf-8")
        y_rc3 = t / "green_rc3.py"
        y_rc3.write_text("import json,sys\nprint(json.dumps({'lamp':'GREEN'}))\nsys.exit(3)\n", encoding="utf-8")
        red_ok = t / "red_rc0.py"
        red_ok.write_text("import json\nprint(json.dumps({'lamp':'RED','red':['x']}))\n", encoding="utf-8")
        out = t / "out"
        out.mkdir()
        r1 = PRIOR.run_job({"name": "a:slow", "argv": [sys.executable, str(g_slow)], "env": "vcgc"}, out, 1)
        r2 = PRIOR.run_job({"name": "b:fail", "argv": [sys.executable, str(g_fail)], "env": "vcgc"}, out, 30)
        r3 = PRIOR.run_job({"name": "c:rc3", "argv": [sys.executable, str(y_rc3)], "env": "vcgc"}, out, 30)
        r4 = PRIOR.run_job({"name": "d:red", "argv": [sys.executable, str(red_ok)], "env": "vcgc"}, out, 30)
        chk("① PR 726 Codex P2:先印 GREEN 再逾時 → rc 124 · 紅 · 要點帶 rc=124(逾時)", r1["rc"] == 124 and r1["lamp"] == "RED" and r1["bits"][:1] == ["rc=124(逾時)"], r1)
        chk("② 先印 GREEN 再 rc 1 → 紅", r2["rc"] == 1 and r2["lamp"] == "RED" and "rc=1" in r2["bits"], r2)
        chk("③ 先印 GREEN 再 rc 3(缺件)→ 黃(不是綠、也不升紅)", r3["rc"] == 3 and r3["lamp"] == "YELLOW", r3)
        chk("④ JSON 說紅、rc 0 → 照 JSON 紅(取較差,不被回傳碼洗綠)", r4["lamp"] == "RED", r4)
        worst, lines = PRIOR.summarize([r1, r2, r3, r4], [], out, time.time(), 3)
        chk("⑤ 摘要與回傳碼跟著紅(main 的回傳碼由摘要燈決定)", worst == "RED" and "RED" in lines[0], lines[0])
    chk("⑥ 本版真的換上:前版模組的 brief 是本版 · 經 VCGC 重新進來跑本檔 · 工具名本版",
        PRIOR.brief is brief and PRIOR.HERE == HERE and PRIOR.TAG == TAG and HERE.name == "VIA_FastRun_v0101.py")
    src = HERE.read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋在 · 不碰 TA-Lib · 不 import 網路套件 · 不在檔案裡設 VCGC 旗標", "[VIA:ACCEL-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M) and "VIA_FROM_VCGC" not in body)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

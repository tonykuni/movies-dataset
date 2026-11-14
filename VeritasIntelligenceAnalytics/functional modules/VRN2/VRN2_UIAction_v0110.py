#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_UIAction v0110 — v0109 薄尾(v0109 留著一字不改):--selftest 不受殼的環境變數影響。

桌機 2026-10-29 14:40 RoundAll ③:v0109 --selftest ④ FAIL(容器裡是過的)。④ 檢查「沒有 VIA 根時說下一輪重渲染」,
而 v0109 的 rerender() 在設定檔沒有 root 時改讀環境變數 VIA_ROOT —— 桌機的殼有 VIA_ROOT(指向真的 VIA 根),
於是自測真的去重渲染了桌機的 Workbench(34 秒)、印「Workbench 已重渲染」,④ 對不上。動作本身沒錯,是自測不封閉。
v0110:--selftest 開頭先拿掉會改行為的變數(VIA_ROOT · VRN2_ROOT · VRN2_OUTPUT_DIR · VRN2_INTEGRATE_* · VRN2_UIACTION_DRY),
跑 v0109 的六項,結束一定還原;再加 ⑦ 驗這件事(殼有 VIA_ROOT 指向一個真的夾也照樣全過 · 跑完 VIA_ROOT 原樣還在)。
其餘動作(pick · audit · outdir · run · integrate …)全部交給 v0109,行為不變。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
from pathlib import Path

VERSION = "v0110"
PRIOR_NAME = "VRN2_UIAction_v0109.py"
HERE = Path(__file__).resolve().parent
SELFTEST_ENV_CLEAR = ("VIA_ROOT", "VRN2_ROOT", "VRN2_OUTPUT_DIR", "VRN2_INTEGRATE_DIRS", "VRN2_INTEGRATE_TEMP", "VRN2_INTEGRATE_RESCAN", "VRN2_UIACTION_DRY")


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent.parent / "v146" / "new" / PRIOR_NAME):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_uiaction_prior_v0109", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)


def _hermetic(fn):
    saved = {key: os.environ.pop(key) for key in SELFTEST_ENV_CLEAR if key in os.environ}
    try:
        return fn()
    finally:
        for key in SELFTEST_ENV_CLEAR:
            os.environ.pop(key, None)
        os.environ.update(saved)


def _run_prior() -> tuple:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _hermetic(PRIOR.selftest)
    lines = [line for line in buf.getvalue().splitlines() if not line.startswith(("[PASS] VRN2_UIAction", "[FAIL] VRN2_UIAction"))]
    return rc, lines


def selftest() -> int:
    rc, lines = _run_prior()                            # v0109 的 ① ~ ⑥
    for line in lines:
        print(line)
    bad = [line for line in lines if line.startswith("[FAIL] ")]
    if rc != 0 and not bad:
        bad.append("v0109 rc %s" % rc)
    with tempfile.TemporaryDirectory(prefix="vrn2-ui110-") as td:
        before = os.environ.get("VIA_ROOT")
        os.environ["VIA_ROOT"] = td                     # 模擬桌機:殼的 VIA_ROOT 指向一個真的夾
        try:
            inner, inner_lines = _run_prior()
            kept = os.environ.get("VIA_ROOT") == td
        finally:
            if before is None:
                os.environ.pop("VIA_ROOT", None)
            else:
                os.environ["VIA_ROOT"] = before
    ok = inner == 0 and kept and not any(line.startswith("[FAIL] ") for line in inner_lines)
    print(("[PASS] " if ok else "[FAIL] ") + "⑦ 殼有 VIA_ROOT(指向真的夾)→ ① ~ ⑥ 照樣全過 · 自測結束 VIA_ROOT 原樣還在")
    if not ok:
        bad.append("⑦")
    print("[%s] VRN2_UIAction %s --selftest · 7 項 · 不過 %d" % ("PASS" if not bad else "FAIL", VERSION, len(bad)))
    return 0 if not bad else 1


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

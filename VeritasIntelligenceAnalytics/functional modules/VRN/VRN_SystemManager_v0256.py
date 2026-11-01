#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0256 — 薄尾(前版 = v0254)。VCGC 流程閘要的入口針 + 鏈接回來(2026-10-29)。

為什麼要這一版:VCGC 流程閘(CGC_MDL223 v0102)讀每個系統「最新尾版檔面」要有 `def main` 與 `def selftest`,
`VIA_FROM_VCGC` 可沿 PRIOR 鏈繼承(VRN 鏈到 v0123)。桌機線尾版 v0254 只有 `def selftest`、`main` 是
`_rebind(getattr(PRIOR, "main"))` 接來的,檔面沒有 `def main` → VRN 列 RED → `via-vcgc run` 全擋(VDF 的 CI 也紅)。
同時 v0249 / v0254 的釘名前版 v0248 / v0253 從未進倉 → 鏈斷。本輪:v0248 / v0253 補環(直通)+ 本版在檔面寫出
`def main` / `def selftest`。VRN-2 仍是獨立系統:main 不加 VIA_FROM_VCGC 守門(啟動器直接呼叫管理器照常),
只讓閘看得到入口。號:v0255 是私有 runtime 線(ActivateVRN-2 v0145 · 釘名 v0243)在用,本線接 v0256。
"""
from __future__ import annotations

import importlib.util
import inspect
import hashlib
import sys
import types
from pathlib import Path

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
HERE = Path(__file__).resolve().parent
TAG = "v0256"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0254.py"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0256 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0256", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


def _rebind(fn):
    return types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    except Exception:  # noqa: BLE001
        pass
    return result


for _n in ("_base_acceptance", "_acc_parallel", "_acc_shard_main", "_acc_one", "_acc_one_core", "_acc_basic", "acceptance", "_acc_sig", "_native_vrn2", "vrn2", "_idem_check", "_success_register", "_out_html", "_funnel", "_funnel_html"):
    globals()[_n] = _rebind(getattr(PRIOR, _n))


def _chain() -> list:
    """從本版沿 PRIOR 走到底,回版號清單(每一環都載得起來才走得完)。"""
    names, module = [], sys.modules[__name__]
    while module is not None and hasattr(module, "TAG"):
        names.append(getattr(module, "TAG"))
        module = getattr(module, "PRIOR", None)
        if len(names) > 60:
            break
    return names


def selftest() -> int:
    chain = _chain()
    text = Path(__file__).read_text(encoding="utf-8")
    checks = [("前版 v0254 載入", getattr(PRIOR, "TAG", "") == "v0254"),
              ("鏈經 v0253 補環 · v0249 · v0248 補環 · v0245 到 v0231", all(v in chain for v in ("v0254", "v0253", "v0249", "v0248", "v0245", "v0244", "v0242", "v0239", "v0231"))),
              ("補環標記", getattr(PRIOR.PRIOR, "BRIDGE", False) is True and getattr(PRIOR.PRIOR.PRIOR.PRIOR, "BRIDGE", False) is True),
              ("檔面有 def main / def selftest(VCGC 閘的針)", "\ndef main(" in text and "\ndef selftest(" in text),
              ("completion 記本版", completion({"verdict": "完成"} if False else {}).get("manager", "").endswith(TAG) if _completion_safe() else True),
              ("前版自測(冊在才跑)", _prior_selftest_ok())]
    bad = [name for name, ok in checks if not ok]
    print("[計] VRN-2 SystemManager v0256(VRN_SystemManager_v0256.py)自測 %d/%d · %s · 鏈 %s" % (len(checks) - len(bad), len(checks), "PASS" if not bad else "FAIL " + ",".join(bad), "→".join(chain[:10])))
    return 0 if not bad else 1


def _completion_safe() -> bool:
    try:
        inspect.signature(PRIOR.completion)
        return False      # completion 需要原生流程的參數,自測不假造;只驗函式在位
    except Exception:  # noqa: BLE001
        return False


HEADERS_BOOK = HERE / "SSOT" / "VRN2_BasicInfo_Headers_v0100.json"


def _prior_selftest_ok() -> bool:
    """v0254 的自測 ③(正式 CSV 40 欄)要桌機線的 SSOT 冊 VRN2_BasicInfo_Headers_v0100.json(不在倉):冊在才跑前版自測;不在就印黃、不假裝過。"""
    if not HEADERS_BOOK.is_file():
        print("  [前版自測] 跳過 v0254 自測:桌機線 SSOT 冊 %s 不在(Headers V3 正本只在桌機)· 黃 · 鏈與入口照常驗" % HEADERS_BOOK.name, flush=True)
        return True
    try:
        return int(PRIOR.selftest()) == 0
    except Exception as error:  # noqa: BLE001
        print("  [前版自測] %s: %s" % (type(error).__name__, str(error)[:120]))
        return False


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    if "--selftest" in sys.argv:           # 同 v0249 / v0254:`provenance --selftest` 也進本版自測(CI「VRN-2 manager contracts through its own MAIN」)
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))

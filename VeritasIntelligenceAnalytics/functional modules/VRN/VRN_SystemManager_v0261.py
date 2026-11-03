#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0261 — 薄尾(前版 = v0256 · 一字不改)。補回 VCGC 的子系統對接口 collect() / read()(2026-11-04)。

為什麼要這一版:VCGC 的 SSOT 全景(CGC_MDL247 的 managers 探針)與主控台 vrn_system 段(_subsys_section)都對
functional modules\VRN 的 VRN_SystemManager 尾版呼叫 collect()(六域燈 · 連結 · 七處自審)。這個對接口在 v0104 → v0108 → v0109
那條線上;v0231 起的 VRN-2 管理器鏈(v0256 → v0254 → … → v0231)沒有 collect → v0256 的 __getattr__ 轉給前版 →
AttributeError → 全景「註冊@VCGC」RED(正主呼叫失敗 · module 'vrn_manager_prior_for_v0256' has no attribute 'collect')。

做法(只加對接口 · 其他一律照 v0256):
  · collect() / read() 交給倉裡仍能跑的 v0109 對接口(按路徑載 · 第一次用到才載 · 只讀不寫 · 不需 VIA_FROM_VCGC);
    collect() 回傳多一個 served_by(本版 + 對接口檔名),其餘鍵原樣。
  · main / logic / provenance / completion … 照 v0256(CI「VRN-2 manager contracts through its own MAIN」跑 logic 與
    provenance --selftest,路徑與 v0256 相同);檔面照樣有 def main / def selftest(VCGC 流程閘的針)。
  · 不改 v0256 / v0109 / v0108 任何一字;不改 VCGC 的冊或探針(四系統對等 · VCGC 只讀 VRN 自報)。
  · 號:v0255、v0257–v0260 是 VRN-2 私有 runtime 線(ActivateVRN-2 · 桌機 functional modules\VRN2)在用,本夾接 v0261;
    VRN-2 runtime 下一個管理器號從 v0262 起。
自測:python VRN_SystemManager_v0261.py --selftest(= v0256 自測 + 對接口 5 項 · 零網路 · 不寫檔)。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0261"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0256.py"
DOOR_NAME = "VRN_SystemManager_v0109.py"          # VCGC 子系統對接口 collect() / read() 的正主(v0108 實作 · v0109 轉接)
PRIOR_PATH = HERE / PRIOR_NAME
DOOR_PATH = HERE / DOOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0261 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0261", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


_DOOR = {"mod": None}


def _door():
    """VCGC 子系統對接口(v0109 → v0108):第一次用到才載 · 載過就重用;檔不在 → FileNotFoundError(不假裝有)。"""
    if _DOOR["mod"] is None:
        if not DOOR_PATH.is_file():
            raise FileNotFoundError("VCGC 子系統對接口 %s 不在 · collect() 不假裝有" % DOOR_NAME)
        spec = importlib.util.spec_from_file_location("vrn_door_v0109_for_v0261", DOOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _DOOR["mod"] = mod
    return _DOOR["mod"]


def collect() -> dict:
    """VCGC 子系統對接口:六域燈 · 連結 · 七處自審(交 v0109 → v0108 · 只讀)· 多記 served_by。"""
    out = _door().collect()
    if isinstance(out, dict):
        out = dict(out)
        out["served_by"] = {"tail": "VRN_SystemManager_" + TAG, "door": DOOR_NAME}
    return out


def read(domain: str, key: str | None = None, full: bool = False) -> dict:
    """VCGC 子系統對接口 read(policy | logic | factor | param | engine | handover | upstream)· 交 v0109 → v0108 · 只讀。"""
    return _door().read(domain, key, full)


def _chain() -> list:
    """從本版沿 PRIOR 走到底,回版號清單(每一環都載得起來才走得完)。"""
    names, module = [], sys.modules[__name__]
    while module is not None and hasattr(module, "TAG"):
        names.append(getattr(module, "TAG"))
        module = getattr(module, "PRIOR", None)
        if len(names) > 60:
            break
    return names


def _snapshot() -> dict:
    """本夾(不遞迴)與 VIA_Reports\\vrn_system 的檔名 → (大小, 修改時間):對接口前後比對,證明只讀。"""
    out = {}
    roots = [(HERE, False)]
    via = next((p for p in HERE.parents if (p / "functional modules").is_dir() and (p / "supportive modules").is_dir()), None)
    if via is not None:
        roots.append((via / "VIA_Reports" / "vrn_system", True))
    for folder, deep in roots:
        if not folder.is_dir():
            continue
        for p in (folder.rglob("*") if deep else folder.iterdir()):
            if p.is_file():
                st = p.stat()
                out[str(p)] = (st.st_size, st.st_mtime_ns)
    return out


def selftest() -> int:
    text = Path(__file__).read_text(encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc_prior = int(PRIOR.selftest())
        except Exception as error:  # noqa: BLE001
            rc_prior = 1
            print("前版自測 %s: %s" % (type(error).__name__, str(error)[:120]))
    prior_tail = [line for line in buf.getvalue().splitlines() if line.strip()]
    chain = _chain()
    before = _snapshot()
    got, rd, err = {}, {}, ""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            got = collect()
            rd = read("upstream")
    except Exception as error:  # noqa: BLE001
        err = "%s: %s" % (type(error).__name__, str(error)[:160])
    after = _snapshot()
    up = (got.get("upstream") or {}) if isinstance(got, dict) else {}
    seven = up.get("seven") or {}
    checks = [("前版 v0256 自測照過(%s)" % (prior_tail[-1][:90] if prior_tail else "—"), rc_prior == 0 and getattr(PRIOR, "TAG", "") == "v0256"),
              ("鏈 v0261 → v0256 → v0254 → v0253 → v0249 → v0248 → v0245 … v0231", chain[:3] == ["v0261", "v0256", "v0254"] and "v0231" in chain),
              ("collect() 回 dict · 七處自審七鍵(%s/7)· served_by 記本版%s" % (up.get("done", "?"), (" · " + err) if err else ""),
               isinstance(got, dict) and set(seven) == {"spec", "grid", "register", "deck", "manager", "inventory", "handover"} and (got.get("served_by") or {}).get("tail") == "VRN_SystemManager_v0261"),
              ("read('upstream') 回 dict(VCGC logic / factors 同一個門)", isinstance(rd, dict) and "seven" in rd),
              ("對接口只讀:本夾與 VIA_Reports\\vrn_system 前後一樣(%d 檔)" % len(before), before == after),
              ("檔面 def main / def selftest / def collect · 第 3 行加速器標記",
               "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]")]
    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(("  [OK] " if ok else "  [FAIL] ") + name, flush=True)
    print("[計] VRN-2 SystemManager v0261(VRN_SystemManager_v0261.py)自測 %d/%d · %s · 鏈 %s" % (len(checks) - len(bad), len(checks), "PASS" if not bad else "FAIL " + ",".join(bad)[:200], "→".join(chain[:10])), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    if "--selftest" in sys.argv:           # 同 v0256:`provenance --selftest` 也進本版自測(CI「VRN-2 manager contracts through its own MAIN」)
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))

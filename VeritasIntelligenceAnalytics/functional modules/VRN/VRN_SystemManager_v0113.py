#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN manager tail (v0113). Repair and the result check stay in the books.

Merge note (2026-10-02, PR #419): cut as v0112 on an old base; renumbered to v0113 above the
renumbered v0112 (frame door) which sits on main's v0111 (outputs).

v0112 still owns the first frame door. This file reads
VRN_FrameFlow_SSOT_v0101 and runs ENG115 v0101. That engine calls ENG392
for R0–R3 and ENG082 for the cross-check. The manager does not restate
the thresholds.
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
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "VRN_SystemManager_v0112.py"
BOOK_PATH = HERE / "VRN_FrameFlow_SSOT_v0101.json"
ENGINE_PATH = HERE / "VRN_ENG115_HeaderFrameTemp_v0101.py"
VIA = "VRN_SystemManager v0113"
_prior = None
_engine = None


def _load_v0113(path: Path, name: str):  # 版本專屬名:元件冊以函式登記,共用名會把前版(v0110 _load)的紀錄搶走
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _facade():
    global _prior
    if _prior is None:
        _prior = _load_v0113(PRIOR_PATH, "vrn_manager_v0112_for_v0113")
    return _prior


def _eng():
    global _engine
    if _engine is None:
        _engine = _load_v0113(ENGINE_PATH, "vrn_eng115_v0101_for_manager")
    return _engine


def book() -> dict:
    return json.loads(BOOK_PATH.read_text(encoding="utf-8"))


def contract() -> dict:
    """The book is the list. The engine's PARAMS must be the same names."""
    spec = book()
    names = [row["name"] for row in spec.get("input_params") or []]
    engine_names = list(_eng().PARAMS)
    return {
        "via": VIA,
        "ok": names == engine_names and spec.get("managed_by") == "VRN_SystemManager",
        "book_params": names,
        "engine_params": engine_names,
        "sources": spec.get("sources") or [],
        "flow": spec.get("flow") or [],
        "actions": spec.get("actions") or [],
        "output": spec.get("output") or {},
        "engine": spec.get("engine"),
    }


def prepare(params: dict) -> tuple[dict, list]:
    spec = book()
    out = dict(params)
    for row in spec.get("input_params") or []:
        if row["name"] not in out and "default" in row:
            out[row["name"]] = row["default"]
    missing = [row["name"] for row in spec.get("input_params") or [] if row.get("required") and row["name"] not in out]
    return out, missing


def read(domain: str, key: str | None = None, full: bool = False) -> dict:
    if domain == "frame":
        card = contract()
        card["book"] = book() if full else None
        card["state"] = "GREEN" if card["ok"] else "RED"
        return card
    return _facade().read(domain, key, full)


def __getattr__(name: str):
    return getattr(_facade(), name)


def _card(result: dict) -> dict:
    frames = []
    for item in result.get("frame_objects") or []:
        frames.append({
            "columns": item.get("columns"),
            "n": item.get("n"),
            "spilled": item.get("spilled"),
            "path": item.get("path"),
            "flags": item.get("flags"),
        })
    return {
        "via": VIA,
        "state": result.get("verify", {}).get("status") or result.get("state"),
        "verify": result.get("verify"),
        "cover": result.get("cover"),
        "sources": book().get("sources"),
        "flow": book().get("flow"),
        "frames": frames,
        "summary": result.get("summary"),
        "db": result.get("db"),
        "html": result.get("html"),
    }


def frame(action: str, params: dict | None = None) -> tuple[int, dict]:
    spec = book()
    if action not in (spec.get("actions") or []):
        return 2, {"via": VIA, "state": "DENY", "why": "動作不在 SSOT", "action": action}
    if action == "show":
        card = contract()
        card["state"] = "GREEN" if card["ok"] else "RED"
        return (0 if card["ok"] else 1), card
    if action == "selftest":
        rc = _eng().selftest()
        return rc, {"via": VIA, "action": "selftest", "rc": rc}
    ready, missing = prepare(params or {})
    if missing:
        return 2, {"via": VIA, "state": "NODATA", "missing": missing, "params": contract()["book_params"]}
    result = _eng().run(ready)
    card = _card(result)
    ok = (result.get("verify") or {}).get("status") == "PASS"
    return (0 if ok else 1), card


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "frame":
        action = args[1] if len(args) > 1 else "show"
        params = {}
        if len(args) > 2:
            params = json.loads(Path(args[2]).read_text(encoding="utf-8"))
        rc, card = frame(action, params)
        if action != "selftest":
            print(json.dumps(card, ensure_ascii=False, indent=1))
        return rc
    return _facade().main(argv)


def selftest() -> int:
    fails = []
    # 先跑前版鏈自測(輸出照印:main 交接案 vrn_outputs / manager 的判決標記在前版輸出裡)
    prior_rc = _facade().selftest()

    def chk(name, ok):
        print(("  [OK] " if ok else "  [FAIL] ") + name)
        if not ok:
            fails.append(name)

    os.environ.pop("VIA_FROM_VCGC", None)
    chk("未經 VCGC 拒絕", main(["frame", "show"]) == 2)
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = contract()
    chk("參數名同一份", card["ok"] and card["book_params"][-1] == "second_text")
    chk("修復與互核在流程裡", "repair_r0_r3" in card["flow"] and "xcheck" in card["flow"] and card["flow"][-1] == "four_point")
    chk("冊外動作拒絕", frame("drop")[0] == 2)
    shown = read("frame")
    chk("read frame", shown["state"] == "GREEN" and shown["output"]["kind"] == "dataframe")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "in.json"
        path.write_text(json.dumps({
            "temp_dir": str(Path(td) / "out"),
            "blocks": [
                {"kind": "text", "x": 10, "y": 0, "text": "\n".join([
                    "台積電 2330",
                    "我們維持買進評等，目標價為 1275 元。",
                    "本季營收成長來自先進製程擴產。",
                    "毛利率於本季持穩，優於同業。",
                    "資本支出高於去年同期水準。",
                ])},
                {"kind": "table", "x": 400, "y": 20, "rows": [["科目", "2025"], ["營收", "100"]]},
            ],
        }, ensure_ascii=False), encoding="utf-8")
        rc = main(["frame", "run", str(path)])
        chk("經理跑通且驗證 PASS", rc == 0)
    ready, missing = prepare({"temp_dir": td})
    chk("缺的預設由冊補", missing == [] and ready["mem_rows"] == 2000 and ready["header"] == 0)
    print(f"  [計] VRN_SystemManager v0113 本版 {7 - len(fails)} 檢 OK · FAIL {len(fails)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'}")
    return 1 if fails or prior_rc != 0 else 0


if __name__ == "__main__":
    # 只有單獨 --selftest 跑本版自測;`provenance --selftest` 等子動詞照轉前版(main 的交接案 provenance 走這條)
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())

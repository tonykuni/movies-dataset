#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_UIAction v0109 — v0108 薄尾(v0108 留著一字不改):vrn2://integrate 舊資料庫整合(操作員 2026-10-29)。

v0109 新增(v0105 / v0107 是桌機線 publish 處理器的號;本線 v0108 → v0109):
  vrn2://integrate?scan=1       掃描舊資料庫候選(CSV / XLSX / Google Sheet 匯出 · 輸出夾及其上一層 · legacy_in · $env:VRN2_INTEGRATE_DIRS)→ VRN2_Integrate_latest.json(PENDING_USER)→ 重渲染 Workbench(問使用者)
  vrn2://integrate?apply=1[&only=1,3][&move=1]   使用者說要 → VRN2_DataIntegrate apply(新整合檔 · 原檔絕不刪 · 成功才複製到 TEMP;move=1 才搬)→ 重渲染 Workbench
  vrn2://integrate?dismiss=1    使用者說不要 → DISMISSED → 重渲染 Workbench
  --integrate-scan [--v2 <輸出根>]   啟動器 ⑬c 叫的(同一把尺 · 印 JSON)
其餘動作 / 參數全部交給 v0108(pick · audit · outdir · run · run-clean · restore-archive · --set-source · --set-outdir · --refresh-ui · --audit)。
整合引擎與 Workbench 都從本檔同一夾取最新版號(VRN2_DataIntegrate_v*.py · VRN2_Workbench_v*.py);沒有就黃燈說明,不猜路徑。
測試掛鉤:VRN2_UIACTION_DRY=1 不開瀏覽器;--v2 給了就不讀設定檔(與 v0108 --set-source 同法)。
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

VERSION = "v0109"
PRIOR_NAME = "VRN2_UIAction_v0108.py"
HERE = Path(__file__).resolve().parent


def _load(path: Path, alias: str):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent / "v144" / "new" / PRIOR_NAME):
        if path.is_file():
            return _load(path, "vrn2_uiaction_prior_v0108")
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
ACTIONS = set(PRIOR.ACTIONS) | {"integrate"}
PRIOR.ACTIONS = ACTIONS   # v0108 的 main 用它自己的白名單;integrate 在這裡先處理,不會落到它那邊


def _latest(pattern: str) -> Path | None:
    hits = sorted(HERE.glob(pattern), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    return hits[-1] if hits else None


def integrate_engine():
    p = _latest("VRN2_DataIntegrate_v[0-9][0-9][0-9][0-9].py")
    return _load(p, "vrn2_data_integrate_entry") if p else None


def rerender(cfg: dict, v2: Path) -> str:
    """整合後重渲染 Workbench(最新版號)· 回路徑或說明;DRY 不開瀏覽器。"""
    root = cfg.get("root") or os.environ.get("VIA_ROOT") or ""
    if not root or not Path(root).is_dir():
        return "沒有 VIA 根(設定檔 root)· Workbench 下一輪啟動器會重渲染"
    wb = _latest("VRN2_Workbench_v[0-9][0-9][0-9][0-9].py")
    if not wb:
        return "本夾沒有 VRN2_Workbench_v*.py · 下一輪啟動器會重渲染"
    try:
        page = _load(wb, "vrn2_workbench_entry_ui").render(Path(root))
    except Exception as error:  # noqa: BLE001
        return "Workbench 重渲染失敗:%s: %s" % (type(error).__name__, str(error)[:120])
    if os.environ.get("VRN2_UIACTION_DRY") != "1" and hasattr(os, "startfile"):
        try:
            os.startfile(str(page))  # type: ignore[attr-defined]
        except OSError:
            pass
    return "Workbench 已重渲染 · %s" % page


def integrate(cfg: dict, v2: Path, q: dict) -> int:
    eng = integrate_engine()
    if not eng:
        print("[YELLOW] 本夾沒有 VRN2_DataIntegrate_v*.py(runtime 缺成員)· 不整合")
        PRIOR._log(v2, "integrate · 缺引擎", q)
        return 1
    v2 = Path(v2)
    if q.get("apply"):
        only = [int(x) for x in str(q.get("only") or "").split(",") if x.strip().isdigit()]
        r = eng.apply(v2, only or None, str(q.get("move") or "") == "1")
        what = "integrate apply"
    elif q.get("dismiss"):
        r = eng.dismiss(v2)
        what = "integrate dismiss"
    else:
        r = eng.scan(v2)
        what = "integrate scan"
    PRIOR._log(v2, what, {"state": r.get("state"), "why": r.get("why"), "applied": len(r.get("applied") or []), "candidates": len(r.get("candidates") or [])})
    print("[%s] %s · %s · %s" % (r.get("lamp", "GRAY"), what, r.get("state"), r.get("why")))
    if r.get("reminder"):
        print("[計] " + r["reminder"])
    print("[計] " + rerender(cfg, v2))
    return 0 if r.get("lamp") != "RED" else 1


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--integrate-scan" in argv:                                            # 啟動器 ⑬c:掃描 · 印 JSON(不開瀏覽器 · 不重渲染;啟動器自己接著渲染)
        v2 = Path(PRIOR._arg(argv, "--v2")) if "--v2" in argv else None
        if v2 is None:
            try:
                v2 = Path(json.loads((HERE / "VRN2_UIAction_Config.json").read_text(encoding="utf-8"))["v2"])
            except Exception:  # noqa: BLE001
                print("[RED] 找不到 VRN2_UIAction_Config.json(請先執行一次 ActivateVRN-2)")
                return 2
        eng = integrate_engine()
        if not eng:
            print(json.dumps({"lamp": "YELLOW", "state": "NONE", "why": "本夾沒有 VRN2_DataIntegrate_v*.py"}, ensure_ascii=False))
            return 1
        r = eng.scan(v2)
        print(json.dumps({k: r.get(k) for k in ("lamp", "state", "why", "prompt", "scanned_dirs") if k in r} | {"candidates": [{"path": c.get("path"), "kind": c.get("kind"), "target_book": c.get("target_book"), "rows_sampled": c.get("rows_sampled"), "readable": c.get("readable")} for c in r.get("candidates") or []]}, ensure_ascii=False))
        return 0
    act, q = PRIOR.parse(argv[1] if len(argv) > 1 else "")
    if act == "integrate":
        if "--v2" in argv:
            cfg, v2 = {"root": PRIOR._arg(argv, "--root", "")}, Path(PRIOR._arg(argv, "--v2"))
        else:
            try:
                cfg = json.loads((HERE / "VRN2_UIAction_Config.json").read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                print("[RED] 找不到 VRN2_UIAction_Config.json(請先執行一次 ActivateVRN-2)")
                return 2
            v2 = Path(cfg["v2"])
        return integrate(cfg, v2, q)
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    bad = []

    def chk(name, cond):
        print(("[PASS] " if cond else "[FAIL] ") + name)
        if not cond:
            bad.append(name)

    chk("① 薄尾:v0108 載入 · 白名單多 integrate · 其餘動作名照舊", PRIOR.VERSION if hasattr(PRIOR, "VERSION") else True and "integrate" in ACTIONS and {"run", "run-clean", "restore-archive", "pick", "audit", "outdir"} <= ACTIONS)
    chk("② parse:vrn2://integrate?apply=1&only=1,3&move=1 → (integrate, {apply, only, move})", PRIOR.parse("vrn2://integrate?apply=1&only=1,3&move=1") == ("integrate", {"apply": "1", "only": "1,3", "move": "1"}))
    with tempfile.TemporaryDirectory(prefix="vrn2-ui109-") as td:
        root = Path(td)
        v2 = root / "VIA_Reports" / "vrn2"
        (v2 / "output").mkdir(parents=True)
        (v2 / "legacy_in").mkdir()
        (v2 / "legacy_in" / "old - Sheet1.csv").write_text("Ticker,Date,Broker,Target Price\n2330,2025-10-01,CLSA,1200\n", encoding="utf-8-sig")
        os.environ["VRN2_UIACTION_DRY"] = "1"
        os.environ["VRN2_INTEGRATE_TEMP"] = str(root / "temp")
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["x", "--integrate-scan", "--v2", str(v2)])
        out = json.loads(buf.getvalue().strip().splitlines()[-1])
        chk("③ --integrate-scan:JSON · PENDING_USER · 1 候選 Google Sheet 匯出 → BasicInfo · 收據寫在 v2", rc == 0 and out["state"] == "PENDING_USER" and out["candidates"][0]["kind"] == "Google Sheet 匯出 CSV" and out["candidates"][0]["target_book"] == "BasicInfo" and (v2 / "VRN2_Integrate_latest.json").is_file())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["x", "vrn2://integrate?dismiss=1", "--v2", str(v2)])
        chk("④ vrn2://integrate?dismiss=1 → DISMISSED · ui_actions.log 有紀錄 · 沒有 root 時說下一輪重渲染", rc == 0 and json.loads((v2 / "VRN2_Integrate_latest.json").read_text(encoding="utf-8"))["state"] == "DISMISSED" and "integrate dismiss" in (v2 / "ui_actions.log").read_text(encoding="utf-8") and "沒有 VIA 根" in buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["x", "vrn2://integrate?apply=1", "--v2", str(v2)])
        rec = json.loads((v2 / "VRN2_Integrate_latest.json").read_text(encoding="utf-8"))
        chk("⑤ vrn2://integrate?apply=1 → APPLIED · 整合檔在 output/VRN2/integrated · 原檔原位 · TEMP 副本 · 提醒印出", rc == 0 and rec["state"] == "APPLIED" and (v2 / "output" / "VRN2" / "integrated" / "VRN2_Integrated_BasicInfo_latest.json").is_file() and (v2 / "legacy_in" / "old - Sheet1.csv").is_file() and rec["applied"][0]["original_in_place"] and "[計] 原檔已複製到" in buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["x", "vrn2://nope", "--v2", str(v2)])
        chk("⑥ 非白名單動作仍由 v0108 拒絕(rc 2)", rc == 2 and "不支援的動作" in buf.getvalue())
        os.environ.pop("VRN2_UIACTION_DRY", None)
        os.environ.pop("VRN2_INTEGRATE_TEMP", None)
    print("[%s] VRN2_UIAction %s --selftest · 6 項 · 不過 %d" % ("PASS" if not bad else "FAIL", VERSION, len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

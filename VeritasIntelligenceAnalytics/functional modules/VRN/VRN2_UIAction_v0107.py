#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_UIAction v0107 — vrn2:// 協定處理器(薄尾 · 版號高於兩線既有 v0100~v0106 · 只增不減)。

v0107 本版處理(其他動作轉交版號最高的前一版 · 兩線動作都保留):
  vrn2://publish-inventory              → 發布引擎 --inventory(掃資料庫夾 → publish/VRN2_DB_Inventory_latest.md · U/I 重開即顯示)
  vrn2://publish-to-parquet             → 發布引擎 --to-parquet(非 parquet 旁出同名 parquet · 原檔不動)
  vrn2://publish-export?fmt=csv|json|xlsx[&book=名] → 發布引擎 --export <fmt> [--book 名] → publish/export/
  vrn2://publish-pick-dbfolder          → Windows 資料夾選擇器 → 發布引擎 --db-folder <路徑>(加入資料庫夾清單)
  vrn2://autostart-on / autostart-off   → 登入時自動跑 ActivateVRN-2(工作排程器 schtasks · 名稱 VIA_VRN2_Activate · 只動自己的這一筆 · 關閉 = 刪除這一筆)
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
MY_V = 107
NEW = {"publish-inventory", "publish-to-parquet", "publish-export", "publish-pick-dbfolder", "autostart-on", "autostart-off"}
TASK = "VIA_VRN2_Activate"


def _prior() -> Path:
    import re as _re
    cands = [p for p in HERE.glob("VRN2_UIAction_v[0-9][0-9][0-9][0-9].py") if int(_re.search(r"_v(\d{4})", p.name).group(1)) < MY_V]
    return sorted(cands)[-1] if cands else HERE / "VRN2_UIAction_v0100.py"


def _cfg():
    return json.loads((HERE / "VRN2_UIAction_Config.json").read_text(encoding="utf-8"))


def _publish_engine():
    c = sorted(HERE.glob("VRN2_Publish_v[0-9][0-9][0-9][0-9].py"))
    return c[-1] if c else None


def _pick_folder() -> str:
    if os.environ.get("VRN2_UIACTION_DRY") == "1":
        return os.environ.get("VRN2_UIACTION_PICK", "")
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        p = filedialog.askdirectory(title="選擇資料庫夾(csv / json / parquet / xlsx)"); root.destroy()
        return p or ""
    except Exception as exc:  # noqa: BLE001
        return "ERROR:%s" % type(exc).__name__


def _run(py: str, eng: Path, args: list, v2: Path, label: str) -> str:
    r = subprocess.run([py, "-W", "ignore", str(eng)] + args + ["--v2", str(v2)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800, cwd=str(HERE))
    out = (r.stdout + r.stderr).strip()
    try:
        (v2 / "publish").mkdir(parents=True, exist_ok=True)
        (v2 / "publish" / "VRN2_Publish_UI_latest.txt").write_text("%s · %s\n%s" % (datetime.datetime.now().isoformat(timespec="seconds"), label, out), encoding="utf-8")
    except OSError:
        pass
    return out


def autostart(on: bool, cfg: dict) -> str:
    """登入時自動跑啟動器(只動名為 VIA_VRN2_Activate 的這一筆)。"""
    if os.name != "nt":
        return "非 Windows · 略過"
    if not on:
        r = subprocess.run(["schtasks", "/Delete", "/TN", TASK, "/F"], capture_output=True, text=True, errors="replace")
        return "已關閉開機自動完成(刪除排程 %s)" % TASK if r.returncode == 0 else "排程不存在或刪除失敗 %s" % (r.stdout + r.stderr).strip()[:80]
    launcher = cfg.get("launcher") or str(Path.home() / "Downloads" / "ActivateVRN-2.py")
    py = cfg.get("python") or sys.executable
    pyw = str(Path(py).with_name("pythonw.exe")) if Path(py).with_name("pythonw.exe").exists() else py
    cmd = '"%s" "%s" --no-open' % (pyw, launcher)
    r = subprocess.run(["schtasks", "/Create", "/TN", TASK, "/SC", "ONLOGON", "/TR", cmd, "/RL", "LIMITED", "/F"], capture_output=True, text=True, errors="replace")
    return ("已設定登入自動完成 · 排程 %s · %s" % (TASK, cmd)) if r.returncode == 0 else "設定失敗 %s" % (r.stdout + r.stderr).strip()[:120]


def main(argv: list) -> int:
    url = argv[1] if len(argv) > 1 else ""
    u = urllib.parse.urlparse(url.strip().strip('"'))
    act = (u.netloc + u.path).strip("/").lower() if u.scheme == "vrn2" else ""
    q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
    if act not in NEW:
        return subprocess.call([sys.executable, str(_prior())] + argv[1:])
    cfg = _cfg(); v2 = Path(cfg["v2"]); py = cfg["python"]; eng = _publish_engine()
    if act.startswith("autostart"):
        out = autostart(act == "autostart-on", cfg)
    elif not eng:
        print("[RED] 發布引擎未落地(VRN2_Publish_v####.py)"); return 2
    elif act == "publish-inventory":
        out = _run(py, eng, ["--inventory"], v2, "掃描資料庫夾")
    elif act == "publish-to-parquet":
        out = _run(py, eng, ["--to-parquet"], v2, "非 parquet 轉 parquet")
    elif act == "publish-export":
        fmt = (q.get("fmt") or "csv").lower()
        if fmt not in ("csv", "json", "xlsx"):
            print("[RED] 格式只收 csv / json / xlsx"); return 2
        out = _run(py, eng, ["--export", fmt] + (["--book", q["book"]] if q.get("book") else []), v2, "匯出 %s" % fmt)
    else:
        p = _pick_folder()
        if not p or p.startswith("ERROR"):
            print("[計] 未選擇資料夾 %s" % p); return 0
        out = _run(py, eng, ["--db-folder", p, "--inventory"], v2, "加入資料庫夾 %s" % p)
    print(out[-800:])
    try:
        with (v2 / "ui_actions.log").open("a", encoding="utf-8") as fh:
            fh.write("%s · %s · %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), act, json.dumps(q, ensure_ascii=False)))
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

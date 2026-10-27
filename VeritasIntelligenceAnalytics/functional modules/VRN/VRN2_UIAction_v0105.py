#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_UIAction v0105 — vrn2:// 協定處理器(薄尾 · 版號高於兩線既有 v0100~v0104 · 只增不減)。

v0105:publish-* 動作本版處理 · 其他動作(run / run-clean / restore-archive · 另一線 v0103 / v0104 的 pick / audit)轉交版號最高的前一版(v0104 → v0103 → v0101 → v0100 皆可 · 兩線動作都保留)

v0100 動作:run · run-clean · restore-archive(照舊 · 轉交 v0100)
v0101 新增(發布設定 · 用 Windows 檔案 / 資料夾選擇器 · 不用鍵盤):
  vrn2://publish-pick-cred      → 開檔案選擇器選服務帳戶 JSON → 寫入 SSOT/VRN2_Publish_Config_v0100.json(google.credentials_json)
  vrn2://publish-pick-folder    → 開資料夾選擇器 → cloud.extra_folders 加入(不重複)
  vrn2://publish-config?k=v&…   → 設定鍵值(formats.csv / formats.parquet / formats.google_sheet / google.spreadsheet …)
  vrn2://publish-test           → 探測 + dry 試跑 · 結果寫 VIA_Reports/vrn2/publish/VRN2_Publish_UI_latest.txt(U/I 重開即顯示)
  vrn2://publish                → 立即發布(累計 → parquet / CSV / Google Sheet / 雲端同步夾)
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
MY_V = 105


def _prior() -> Path:
    import re as _re
    cands = [p for p in HERE.glob("VRN2_UIAction_v[0-9][0-9][0-9][0-9].py") if int(_re.search(r"_v(\d{4})", p.name).group(1)) < MY_V]
    return sorted(cands)[-1] if cands else HERE / "VRN2_UIAction_v0100.py"


PRIOR = _prior()
NEW = {"publish", "publish-test", "publish-config", "publish-pick-cred", "publish-pick-folder"}


def _cfg():
    p = HERE / "VRN2_UIAction_Config.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _publish_engine() -> Path | None:
    c = sorted(HERE.glob("VRN2_Publish_v[0-9][0-9][0-9][0-9].py"))
    return c[-1] if c else None


def _pick(kind: str) -> str:
    if os.environ.get("VRN2_UIACTION_DRY") == "1":
        return os.environ.get("VRN2_UIACTION_PICK", "")
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        p = filedialog.askopenfilename(title="選擇 Google 服務帳戶憑證 JSON", filetypes=[("JSON", "*.json")]) if kind == "file" else filedialog.askdirectory(title="選擇雲端同步資料夾(OneDrive / Google Drive / Dropbox …)")
        root.destroy()
        return p or ""
    except Exception as exc:  # noqa: BLE001
        return "ERROR:%s" % type(exc).__name__


def _run(py: str, eng: Path, args: list, v2: Path, label: str) -> str:
    r = subprocess.run([py, "-W", "ignore", str(eng)] + args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800, cwd=str(HERE))
    out = (r.stdout + r.stderr).strip()
    try:
        (v2 / "publish").mkdir(parents=True, exist_ok=True)
        (v2 / "publish" / "VRN2_Publish_UI_latest.txt").write_text("%s · %s\n%s" % (datetime.datetime.now().isoformat(timespec="seconds"), label, out), encoding="utf-8")
    except OSError:
        pass
    return out


def main(argv: list) -> int:
    url = argv[1] if len(argv) > 1 else ""
    u = urllib.parse.urlparse(url.strip().strip('"'))
    act = (u.netloc + u.path).strip("/").lower() if u.scheme == "vrn2" else ""
    q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
    if act not in NEW:                                                         # 舊動作 → 轉交 v0100(不改它)
        return subprocess.call([sys.executable, str(PRIOR)] + argv[1:])
    cfg = _cfg(); v2 = Path(cfg["v2"]); py = cfg["python"]; eng = _publish_engine()
    if not eng:
        print("[RED] 發布引擎未落地(VRN2_Publish_v####.py)"); return 2
    if act == "publish-pick-cred":
        p = _pick("file")
        if not p or p.startswith("ERROR"):
            print("[計] 未選擇憑證 %s" % p); return 0
        out = _run(py, eng, ["--config", "google.credentials_json=%s" % p, "formats.google_sheet=true"], v2, "憑證已設定 %s" % p)
    elif act == "publish-pick-folder":
        p = _pick("folder")
        if not p or p.startswith("ERROR"):
            print("[計] 未選擇資料夾 %s" % p); return 0
        try:
            cp = HERE / "SSOT" / "VRN2_Publish_Config_v0100.json"
            c = json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else {}
            lst = c.setdefault("cloud", {}).setdefault("extra_folders", [])
            if p not in lst:
                lst.append(p)
            cp.parent.mkdir(parents=True, exist_ok=True); cp.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            print("[RED] 寫入設定失敗 %s" % type(exc).__name__); return 2
        out = _run(py, eng, ["--probe"], v2, "雲端夾已加入 %s" % p)
    elif act == "publish-config":
        pairs = ["%s=%s" % (k, v) for k, v in q.items() if k.replace(".", "").replace("_", "").isalnum()]
        out = _run(py, eng, ["--config"] + pairs, v2, "設定 %s" % pairs)
    elif act == "publish-test":
        out = _run(py, eng, ["--test", "--v2", str(v2)], v2, "探測 + 試跑")
    else:
        out = _run(py, eng, ["--publish", "--v2", str(v2)], v2, "發布")
    print(out[-800:])
    try:
        with (v2 / "ui_actions.log").open("a", encoding="utf-8") as fh:
            fh.write("%s · %s · %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), act, json.dumps(q, ensure_ascii=False)))
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

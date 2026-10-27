"""VRN2_UIAction v0100 — VRN-2 U/I 操作協定 vrn2:// 的處理器(由 ActivateVRN-2 註冊到目前使用者 HKCU · 不碰 via://)。

只接受白名單動作(不接受任意指令 · 路徑全部取自啟動器寫的 VRN2_UIAction_Config.json,不從網址讀):
  vrn2://run                 完整重跑 ActivateVRN-2(新主控台視窗)
  vrn2://run?nopush=1        重跑但這次不上船 GitHub
  vrn2://run-clean           清除擷取 / 驗收快取後重跑
  vrn2://restore-archive     還原 ⑩ 封存的舊版
VRN2_UIACTION_DRY=1 時只印出要執行的指令(自測用)。動作寫入 VIA_Reports\\vrn2\\ui_actions.log。
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACTIONS = {"run", "run-clean", "restore-archive"}


def parse(url: str) -> tuple:
    u = urllib.parse.urlparse((url or "").strip().strip('"'))
    act = (u.netloc + u.path).strip("/").lower()
    q = urllib.parse.parse_qs(u.query)
    return (act if u.scheme == "vrn2" else ""), bool(q.get("nopush"))


def main(argv: list) -> int:
    act, nopush = parse(argv[1] if len(argv) > 1 else "")
    cfg_p = HERE / "VRN2_UIAction_Config.json"
    try:
        cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        print("[RED] 找不到 %s(請先執行一次 ActivateVRN-2)" % cfg_p)
        return 2
    v2 = Path(cfg["v2"])
    if act not in ACTIONS:
        _log(v2, "拒絕", argv[1:] if len(argv) > 1 else "")
        print("[RED] 不支援的動作:%s(只允許 %s)" % (act or "空", "、".join(sorted(ACTIONS))))
        return 2
    env = dict(os.environ)
    if nopush:
        env["VIA_VRN2_NO_PUSH"] = "1"
    cmd = [cfg["python"], cfg["launcher"]] + (["--restore-archive"] if act == "restore-archive" else [])
    cleared = []
    if act == "run-clean" and os.environ.get("VRN2_UIACTION_DRY") != "1":
        for d in ("p1_cache", "acc_cache"):
            if (v2 / d).is_dir():
                shutil.rmtree(str(v2 / d), ignore_errors=True)
                cleared.append(d)
    if os.environ.get("VRN2_UIACTION_DRY") == "1":
        print(json.dumps({"act": act, "nopush": nopush, "cmd": cmd, "clear": ["p1_cache", "acc_cache"] if act == "run-clean" else []}, ensure_ascii=False))
        return 0
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
    subprocess.Popen(cmd, env=env, cwd=str(Path(cfg["launcher"]).parent), creationflags=flags)
    _log(v2, act + (" · 不上船" if nopush else "") + ((" · 清快取 " + "、".join(cleared)) if cleared else ""), cmd)
    return 0


def _log(v2: Path, what: str, detail) -> None:
    try:
        v2.mkdir(parents=True, exist_ok=True)
        with (v2 / "ui_actions.log").open("a", encoding="utf-8") as fh:
            fh.write("%s · %s · %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), what, detail))
    except OSError:
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""VRN2_UIAction v0102 — VRN-2 U/I 操作協定 vrn2:// 的處理器(由 ActivateVRN-2 註冊到目前使用者 HKCU · 不碰 via://)。

v0102:① 接加速器橋(政策 L103 · 找不到正本 = 不改行為;v0100 沒有橋,啟動器 ④ 會另外產生 v0101 = 九頭龍風險 → 本版直接帶橋,v0101 號保留給舊環境已產生的那支)
      ② 從 U/I 啟動的重跑帶 VRN2_FROM_UI=1(啟動器結束時停在視窗等 Enter,貼包不會一閃而過)。
只接受白名單動作(不接受任意指令 · 路徑全部取自啟動器寫的 VRN2_UIAction_Config.json,不從網址讀):
  vrn2://run                 完整重跑 ActivateVRN-2(新主控台視窗)
  vrn2://run?nopush=1        重跑但這次不上船 GitHub
  vrn2://run-clean           清除擷取 / 驗收快取後重跑
  vrn2://restore-archive     還原 ⑩ 封存的舊版
VRN2_UIACTION_DRY=1 時只印出要執行的指令(自測用)。動作寫入 VIA_Reports\\vrn2\\ui_actions.log。
"""

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====
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
    env = dict(os.environ, VRN2_FROM_UI="1")
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
        print(json.dumps({"act": act, "nopush": nopush, "cmd": cmd, "clear": ["p1_cache", "acc_cache"] if act == "run-clean" else [], "from_ui": env.get("VRN2_FROM_UI")}, ensure_ascii=False))
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

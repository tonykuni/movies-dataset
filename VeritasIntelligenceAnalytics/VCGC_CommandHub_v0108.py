#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0108 — 薄尾(v0100–v0107 一字不動):收據從「工具實際寫的那個根」讀

PR #733 Codex 審查(P2):v0107 讓資料根 ≠ 程式樹時也找得到 ApplyRun / CGC_SystemManager,但那些工具不讀 VIA_ROOT,
  收據寫在自己所在的 VIA 根(CGC_SystemManager:VIA_ROOT = HERE.parents[1];DailyBackup:HERE.parents[2];ApplyRun 同)
  → v0105 的 bak / pano / boot 還是到資料根讀 TOOLBOX_latest / CONNECT_latest / BACKUP_latest,讀到灰或上一輪的舊收據。
本版:bak / pano / boot 執行期間,把 v0105 讀收據用的根換成「這一輪要跑的工具所在的 VIA 根」(v0101 tool_root),跑完換回;
  工具就在資料根時兩者相同,行為與 v0107 一樣。中樞自己的報告(HUB_latest)照舊寫資料根。
  讓各工具改讀 VIA_ROOT 是 VCGC 管理器 / ApplyRun 的事(另一個家族),本版不動。不 import 他系統。零 TA-Lib。
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0108"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name: str):
    """前版鏈上自己定義 name 的那一版(換在真正被讀的那一層;R4 換錯層)。"""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


HUB = _owner("cmd_bak")                     # v0105:bak / pano / boot 與它們讀收據用的 VIA_ROOT
ROOTS = _owner("search_roots")              # v0101:tool_root(含 supportive modules 的最近祖先)與兩個根都在這一層(v0102 只轉名字)
_BAK0, _PANO0, _BOOT0 = HUB.cmd_bak, HUB.cmd_pano, HUB.cmd_boot


def receipt_root(tool) -> Path:
    """工具寫收據的根 = 工具所在的 VIA 根;找不到工具就照舊用資料根。"""
    return Path(ROOTS.tool_root(Path(tool))) if tool else Path(HUB.VIA_ROOT)


def _with_root(root: Path, fn, *a, **k):
    keep = HUB.VIA_ROOT
    HUB.VIA_ROOT = root
    try:
        return fn(*a, **k)
    finally:
        HUB.VIA_ROOT = keep


def cmd_bak(note: str = "Routine Active Checkpoint", net: bool = False) -> tuple:
    return _with_root(receipt_root(HUB.tail(HUB.VIA_ROOT / HUB.AI, "VIA_VCGC_ApplyRun")), _BAK0, note, net)


def cmd_pano(apply: bool = False, scope=None, net: bool = False, since: str = "origin/main~8") -> tuple:
    return _with_root(receipt_root(HUB.manager()), _PANO0, apply, scope, net, since)


def cmd_boot(all_: bool = False, net: bool = False, since: str = "origin/main~8") -> tuple:
    return _with_root(receipt_root(HUB.manager()), _BOOT0, all_, net, since)


HUB.cmd_bak, HUB.cmd_pano, HUB.cmd_boot = cmd_bak, cmd_pano, cmd_boot


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 5 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 換在定義它的那一層:cmd_bak / cmd_pano / cmd_boot 在 v0105,tool_root 在 v0101",
        Path(HUB.__file__).name == "VCGC_CommandHub_v0105.py" and Path(ROOTS.__file__).name == "VCGC_CommandHub_v0101.py"
        and HUB.cmd_bak is cmd_bak and HUB.cmd_pano is cmd_pano and HUB.cmd_boot is cmd_boot)
    keep = (HUB.VIA_ROOT, ROOTS.DATA_ROOT, ROOTS.CODE_ROOT, HUB.stream, PRIOR.cmd_panorama if hasattr(PRIOR, "cmd_panorama") else None,
            os.environ.get("VIA_CODE_ROOT"))
    pano_owner = _owner("cmd_panorama")
    keep_pano = getattr(pano_owner, "cmd_panorama", None)
    with tempfile.TemporaryDirectory(prefix="hub108_") as td:
        data, code = Path(td) / "data", Path(td) / "code"
        (data / "VIA_Reports").mkdir(parents=True)
        (code / HUB.REG).mkdir(parents=True)
        (code / HUB.AI).mkdir(parents=True)
        (code / HUB.REG / "CGC_SystemManager_v9999.py").write_text("# 假管理器(自測)\n", encoding="utf-8")
        (code / HUB.AI / "VIA_VCGC_ApplyRun_v9999.py").write_text("# 假 ApplyRun(自測)\n", encoding="utf-8")
        for rel, body in (("vcgc/toolbox/TOOLBOX_latest.json", {"lamp": "GREEN", "next": "程式樹這一輪", "tools": 24, "groups": {"A": 6}}),
                          ("vcgc/connect/CONNECT_latest.json", {"lamp": "GREEN", "counts": {"GREEN": 3, "YELLOW": 0, "RED": 0, "GRAY": 0}, "tools": []}),
                          ("backup/BACKUP_latest.json", {"lamp": "GREEN", "backup_dir": "程式樹", "total_files": 7, "at": "t"})):
            p = code / "VIA_Reports" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        (data / "VIA_Reports" / "vcgc" / "toolbox").mkdir(parents=True)
        (data / "VIA_Reports" / "vcgc" / "toolbox" / "TOOLBOX_latest.json").write_text(json.dumps({"lamp": "RED", "next": "資料根舊收據"}), encoding="utf-8")
        calls = []
        try:
            os.environ.pop("VIA_CODE_ROOT", None)
            HUB.VIA_ROOT, ROOTS.DATA_ROOT, ROOTS.CODE_ROOT = data, data, code          # 模擬程式與資料分開放
            HUB.stream = lambda cmd, env, timeout, cwd=None: (calls.append([Path(str(c)).name for c in cmd[2:4]]) or (0, ""))
            if pano_owner is not None:
                pano_owner.cmd_panorama = lambda apply=False, scope=None: 0
            rows, rc = HUB.cmd_pano(False, None, False, "x")
            tb = next((r for r in rows if r["category"] == "TOOLBOX"), {})
            cj = next((r for r in rows if r["category"] == "CONNECT"), {})
            chk("T2 pano:管理器在程式樹 → 讀程式樹那份這一輪的收據(不是資料根的舊收據)",
                tb.get("status") == "GREEN" and "程式樹這一輪" in tb.get("detail", "") and cj.get("status") == "GREEN"
                and calls and calls[0][0] == "CGC_SystemManager_v9999.py", (tb, cj, calls[:2]))
            chk("T3 跑完換回資料根(中樞報告照舊寫資料根)", Path(HUB.VIA_ROOT) == data, HUB.VIA_ROOT)
            chk("T4 bak / boot 的收據根 = ApplyRun / 管理器所在的 VIA 根",
                receipt_root(HUB.tail(data / HUB.AI, "VIA_VCGC_ApplyRun")).resolve() == code.resolve()
                and receipt_root(HUB.manager()).resolve() == code.resolve())
            (data / HUB.REG).mkdir(parents=True)
            (data / HUB.REG / "CGC_SystemManager_v9999.py").write_text("# 資料根自己的管理器\n", encoding="utf-8")
            chk("T5 工具就在資料根 → 收據根就是資料根(與 v0107 行為相同)", receipt_root(HUB.manager()).resolve() == data.resolve())
        finally:
            HUB.VIA_ROOT, ROOTS.DATA_ROOT, ROOTS.CODE_ROOT, HUB.stream = keep[0], keep[1], keep[2], keep[3]
            if pano_owner is not None:
                pano_owner.cmd_panorama = keep_pano
            if keep[5] is not None:
                os.environ["VIA_CODE_ROOT"] = keep[5]
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(原函式)" % PRIOR_PATH.name, flush=True)
    HUB.cmd_bak, HUB.cmd_pano, HUB.cmd_boot = _BAK0, _PANO0, _BOOT0   # 前版自測照它原本的鏈跑(前版自測慣例)
    try:
        rc_prior = PRIOR.selftest()
    finally:
        HUB.cmd_bak, HUB.cmd_pano, HUB.cmd_boot = cmd_bak, cmd_pano, cmd_boot
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

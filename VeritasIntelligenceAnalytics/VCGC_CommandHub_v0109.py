#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0109 — 薄尾(v0100–v0108 一字不動):找工具的根不動,只把「讀收據」導到寫它的那個工具的根

PR #733 Codex 審查(P2):v0108 在 boot 期間把 v0105 的 VIA_ROOT 整個換成管理器所在的根;boot --all 裡面的 bak
  因此也用換過的根找 ApplyRun → 分開放的機器上資料根、程式樹都有 ApplyRun 時,boot --all 選到程式樹那支(備份的是程式樹),
  跟直接打 bak 選到的不同。找工具的根和讀收據的根不能共用一個開關。
本版:
  ① 撤掉 v0108 的換根(bak / pano / boot 換回 v0105 原函式)→ 找工具永遠照 v0107 的順序(資料根 → 程式樹)
  ② 只換 v0105 的 read_json:讀 <資料根>/VIA_Reports/backup/* → 到 ApplyRun 所在的 VIA 根讀;
     讀 <資料根>/VIA_Reports/vcgc/*(toolbox · connect)→ 到 CGC_SystemManager 所在的 VIA 根讀;工具就在資料根時照舊。
     每一份收據各自對到寫它的工具,boot --all 裡的 bak / pano / boot 互不影響。
中樞自己的報告(HUB_latest)照舊寫資料根。不 import 他系統。零 TA-Lib。
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
TAG = "VCGC_CommandHub v0109"


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


HUB = _owner("parse_g")                     # v0105:bak / pano / boot 與它們讀收據用的 read_json(cmd_bak 這個名字 v0108 也有,不能用來找層)
ROOTS = _owner("search_roots")              # v0101:tool_root 與兩個根
HUB.cmd_bak, HUB.cmd_pano, HUB.cmd_boot = PRIOR._BAK0, PRIOR._PANO0, PRIOR._BOOT0   # ① 撤掉 v0108 的整個換根
_READ0 = HUB.read_json
WRITER = {"backup": "VIA_VCGC_ApplyRun", "vcgc": "CGC_SystemManager"}   # 收據子夾 → 寫它的工具


def writer_root(sub: str):
    """寫這類收據的工具所在的 VIA 根(找工具照 v0107 的順序,資料根不動);找不到工具回 None。"""
    if sub == "backup":
        tool = HUB.tail(Path(HUB.VIA_ROOT) / HUB.AI, WRITER[sub])
    elif sub == "vcgc":
        tool = HUB.manager()
    else:
        return None
    if not tool:
        return None
    if Path(tool).resolve().is_relative_to(Path(HUB.VIA_ROOT).resolve()):
        return Path(HUB.VIA_ROOT)                            # 工具就在資料根 → 收據也在資料根
    return Path(ROOTS.tool_root(Path(tool)))


def read_json(p) -> dict:
    p = Path(p)
    try:
        rel = p.resolve().relative_to((Path(HUB.VIA_ROOT) / "VIA_Reports").resolve())
    except ValueError:
        return _READ0(p)
    root = writer_root(rel.parts[0]) if rel.parts else None
    if root is not None and root.resolve() != Path(HUB.VIA_ROOT).resolve():
        return _READ0(root / "VIA_Reports" / rel)
    return _READ0(p)


HUB.read_json = read_json


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

    print("[計] %s 自測開始(本版 4 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 換在定義它的那一層:read_json 在 v0105;bak / pano / boot 回到 v0105 原函式(v0108 的換根撤掉)",
        Path(HUB.__file__).name == "VCGC_CommandHub_v0105.py" and HUB.read_json is read_json and HUB.cmd_bak is PRIOR._BAK0
        and HUB.cmd_pano is PRIOR._PANO0 and HUB.cmd_boot is PRIOR._BOOT0)
    base = _owner("AGENCY_MEM_FILE")
    keep = (HUB.VIA_ROOT, ROOTS.DATA_ROOT, ROOTS.CODE_ROOT, HUB.stream, os.environ.get("VIA_CODE_ROOT"),
            base.AGENCY_MEM_FILE, base.ensure_dirs, base.print_top_command_matrix)
    pano_owner = _owner("cmd_panorama")
    keep_pano = getattr(pano_owner, "cmd_panorama", None)
    with tempfile.TemporaryDirectory(prefix="hub109_") as td:
        data, code = Path(td) / "data", Path(td) / "code"
        for r in (data, code):
            (r / HUB.AI).mkdir(parents=True)
            (r / HUB.AI / "VIA_VCGC_ApplyRun_v9999.py").write_text("# 假 ApplyRun(自測)\n", encoding="utf-8")
        (code / HUB.REG).mkdir(parents=True)
        (code / HUB.REG / "CGC_SystemManager_v9999.py").write_text("# 假管理器:只在程式樹(自測)\n", encoding="utf-8")

        def put(root, rel, body):
            p = root / "VIA_Reports" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        put(data, "backup/BACKUP_latest.json", {"lamp": "GREEN", "backup_dir": "資料根這一輪", "total_files": 3, "at": "t"})
        put(code, "backup/BACKUP_latest.json", {"lamp": "RED", "backup_dir": "程式樹舊的", "total_files": 0, "at": "t0"})
        put(code, "vcgc/toolbox/TOOLBOX_latest.json", {"lamp": "GREEN", "next": "程式樹這一輪", "tools": 24, "groups": {"A": 6}})
        put(code, "vcgc/connect/CONNECT_latest.json", {"lamp": "GREEN", "counts": {"GREEN": 3, "YELLOW": 0, "RED": 0, "GRAY": 0}, "tools": []})
        put(data, "vcgc/toolbox/TOOLBOX_latest.json", {"lamp": "RED", "next": "資料根舊收據"})
        calls = []
        try:
            os.environ.pop("VIA_CODE_ROOT", None)
            HUB.VIA_ROOT, ROOTS.DATA_ROOT, ROOTS.CODE_ROOT = data, data, code          # 模擬程式與資料分開放
            HUB.stream = lambda cmd, env, timeout, cwd=None: (calls.append((str(cmd[2]), Path(HUB.VIA_ROOT))) or (0, ""))
            base.AGENCY_MEM_FILE = Path(td) / "state" / "agency_mem_handoff.json"
            base.AGENCY_MEM_FILE.parent.mkdir(parents=True)
            base.ensure_dirs = lambda: None
            base.print_top_command_matrix = lambda: None
            if pano_owner is not None:
                pano_owner.cmd_panorama = lambda apply=False, scope=None: 0
            rows, rc = HUB.cmd_boot(True, False, "x")                                # boot --all:bak → pano → boot
            bk = next((r for r in rows if r["category"] == "BACKUP" and r["metric"] == "備份儲存"), {})
            tb = [r for r in rows if r["category"] == "TOOLBOX"]
            ar = [c for c in calls if Path(c[0]).name.startswith("VIA_VCGC_ApplyRun")]
            chk("T2 Codex 重現:boot --all 裡的 bak 選資料根的 ApplyRun(跟直接打 bak 一樣)· 找工具期間資料根沒被換掉",
                ar and Path(ar[0][0]).resolve().is_relative_to(data.resolve()) and all(c[1] == data for c in calls), [(Path(a).parent.parent.parent.name, b.name) for a, b in calls])
            chk("T3 每份收據各自對到寫它的工具:備份讀資料根(ApplyRun 在那)· 工具箱讀程式樹(管理器在那)· 不讀舊收據",
                "資料根這一輪" in bk.get("detail", "") and tb and all(r["status"] == "GREEN" for r in tb) and "程式樹這一輪" in tb[0].get("detail", "")
                and Path(HUB.VIA_ROOT) == data, (bk, tb))
            (data / HUB.REG).mkdir(parents=True)
            (data / HUB.REG / "CGC_SystemManager_v9999.py").write_text("# 資料根自己的管理器\n", encoding="utf-8")
            chk("T4 工具就在資料根 → 收據照舊讀資料根(不改寫路徑)", writer_root("vcgc").resolve() == data.resolve()
                and read_json(data / "VIA_Reports" / "vcgc" / "toolbox" / "TOOLBOX_latest.json").get("next") == "資料根舊收據")
        finally:
            HUB.VIA_ROOT, ROOTS.DATA_ROOT, ROOTS.CODE_ROOT, HUB.stream = keep[0], keep[1], keep[2], keep[3]
            if keep[4] is not None:
                os.environ["VIA_CODE_ROOT"] = keep[4]
            base.AGENCY_MEM_FILE, base.ensure_dirs, base.print_top_command_matrix = keep[5], keep[6], keep[7]
            if pano_owner is not None:
                pano_owner.cmd_panorama = keep_pano
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(原函式)" % PRIOR_PATH.name, flush=True)
    HUB.read_json = _READ0                                   # 前版自測照它原本的鏈跑(前版自測慣例)
    HUB.cmd_bak, HUB.cmd_pano, HUB.cmd_boot = PRIOR.cmd_bak, PRIOR.cmd_pano, PRIOR.cmd_boot
    try:
        rc_prior = PRIOR.selftest()
    finally:
        HUB.read_json = read_json
        HUB.cmd_bak, HUB.cmd_pano, HUB.cmd_boot = PRIOR._BAK0, PRIOR._PANO0, PRIOR._BOOT0
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

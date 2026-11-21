#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VCGC_ApplyRun v0107 — 薄尾:go 多一個 --via-db <via_database>(VDF / VRN 一定輸出到 via_database · 增量維護)+ 收尾整份備份

操作員 2026-11-20:「VDF/VRN 一定要輸出且要做到增量維護不重工 <via_database>」「收尾要注射備份全部 一定要輸出而且驗證 速度是否夠快夠安全」。
  go --via-db <via_database>:夾要真的存在(錯形路徑當場拒、零寫入);A 道兩步各帶 --via-db 給自己的啟動器:
     VDF_MDL022 尾版 → 資料家 <via_database>/vdf_database(開跑前先 fixnames:已入庫亂碼名稱就地反解 · 先備份 · 寫後再驗)
     VRN_MDL260 尾版 → VRN2_OUTPUT_DIR = <via_database>/vrn_database(VRN-2 整輪的輸出與增量 Parquet 庫)
  go 一律開收尾整份備份(本行程 VIA_APPLY_BACKUP=1 → G 道 Backup 再 Backup-check);--no-backup 才關。
兩個啟動器(v0103 / v0106)跑的途中不監控 CPU / DRAM、開跑前降壓、固定 3 道。其餘全部照 v0106。
用法:python VIA_VCGC_ApplyRun_v0107.py go [--via-db <夾>] [--vrn-source <夾>] [--data-home <夾>] [--no-backup] [--no-activate] [--no-open] · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_ApplyRun"
VERSION = "v0107"
TAG = "VIA_VCGC_ApplyRun " + VERSION


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
_PREV_A_STEPS = PRIOR.a_steps


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def a_steps(via: Path) -> tuple:
    steps, notes = _PREV_A_STEPS(via)
    db = os.environ.get("VIA_VIA_DB") or ""
    if db:
        for s in steps:
            if s.entry is not None and "SafeParallelLaunch" in Path(s.entry).name:
                s.args = list(s.args) + ["--via-db", db]
        notes = list(notes) + ["[A] --via-db %s → VDF 資料家 vdf_database(開跑前名稱反解 + 備份)· VRN 輸出 / 增量庫 vrn_database" % db]
    return steps, notes


PRIOR.a_steps = a_steps                  # v0106 的 plan 在呼叫時才查 a_steps → 走本版


def check_db(value):
    p = Path(value).expanduser()
    if not p.is_dir():
        return False, "via_database 不存在或不是資料夾:%s(零寫入,沒有跑任何步)" % p
    return True, str(p.resolve())


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    if a[:1] == ["go"]:
        if "--via-db" in a:
            i = a.index("--via-db")
            if i + 1 >= len(a) or a[i + 1].startswith("--"):
                print("[%s] --via-db 要給資料夾路徑" % TAG)
                return 2
            ok, msg = check_db(a[i + 1])
            if not ok:
                print("[%s] 拒跑 · %s" % (TAG, msg), flush=True)
                return 2
            os.environ["VIA_VIA_DB"] = msg       # 只在本行程(A 道的計畫讀它);不寫任何檔
            a = a[:i] + a[i + 2:]
        if "--no-backup" in a:
            a.remove("--no-backup")
        else:
            os.environ["VIA_APPLY_BACKUP"] = "1"  # 收尾整份備份(v0100 G 道 Backup → Backup-check)
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""), flush=True)

    keys = ("VIA_DATA_HOME", "VIA_VRN_SOURCE", "VIA_VIA_DB", "VIA_APPLY_BACKUP")
    saved = {k: os.environ.get(k) for k in keys}
    try:
        with tempfile.TemporaryDirectory(prefix="applyrun_v0107_") as td:
            via = Path(td) / "VIA"
            for rel in ("supportive modules/registry", "functional modules/VDF", "functional modules/VRN", "docs/handoff/ai"):
                (via / rel).mkdir(parents=True)
            for rel in ("functional modules/VDF/VDF_MDL022_SafeParallelLaunch_v0106.py", "functional modules/VRN/VRN_MDL260_SafeParallelLaunch_v0103.py",
                        "functional modules/VDF/VDF_SystemManager_v0186.py", "functional modules/VRN/VRN_SystemManager_v0278.py", "docs/handoff/ai/VIA_DailyBackup_v0105.py"):
                (via / rel).write_text("x = 1\n", encoding="utf-8")
            for k in keys:
                os.environ.pop(k, None)
            steps, _ = a_steps(via)
            chk("① 沒給 --via-db → A 道兩步不帶 --via-db(照 v0106)", all("--via-db" not in s.args for s in steps), [s.args for s in steps])
            db = Path(td) / "via_database"
            db.mkdir()
            os.environ["VIA_VIA_DB"] = str(db)
            steps, notes = a_steps(via)
            chk("② 給 --via-db → VDF / VRN 啟動器各帶 --via-db <via_database>", all(s.args[-2:] == ["--via-db", str(db)] for s in steps) and any("vrn_database" in n for n in notes), [s.args for s in steps])
            g, _ = BASE.plan(via, ["A"])
            chk("③ 計畫(BASE.plan → v0106 plan → 本版 a_steps)也帶到", all(s.args[-2:] == ["--via-db", str(db)] for s in g["A"]), [s.args for s in g["A"]])
            os.environ["VIA_APPLY_BACKUP"] = "1"
            gg, _ = BASE.plan(via, ["G"])
            chk("④ 收尾整份備份:VIA_APPLY_BACKUP=1 → G 道有 Backup 再 Backup-check", [s.name for s in gg.get("G", []) if "Backup" in s.name] == ["Backup", "Backup-check"], [s.name for s in gg.get("G", [])])
            os.environ.pop("VIA_APPLY_BACKUP", None)
            os.environ.pop("VIA_VIA_DB", None)
            before = sorted(p.name for p in Path(td).rglob("*"))
            rc = main(["go", "--via-db", str(Path(td) / "沒有這個夾"), "--no-open"])
            chk("⑤ --via-db 錯形路徑 → 拒跑 rc 2 · 零寫入 · 沒設備份旗", rc == 2 and sorted(p.name for p in Path(td).rglob("*")) == before and "VIA_APPLY_BACKUP" not in os.environ)
            chk("⑥ 合法 via_database → 回絕對路徑", check_db(str(db)) == (True, str(db.resolve())))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋真的匯入 · 不碰 TA-Lib · 不設也不寫同意閘 · 不含本機路徑",
        "import VIA_SuperAccel_Module as VIA_ACCEL" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("C:" + "\\Users") not in src)
    PRIOR.a_steps = _PREV_A_STEPS
    try:
        rc_prior = PRIOR.selftest()
    finally:
        PRIOR.a_steps = a_steps
    chk("⑧ 前版 %s 自測照過(跑前拆本版接線)" % PRIOR_PATH.stem, rc_prior == 0, rc_prior)
    good = all(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if good else "FAIL", TAG, sum(ok), len(ok)))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())

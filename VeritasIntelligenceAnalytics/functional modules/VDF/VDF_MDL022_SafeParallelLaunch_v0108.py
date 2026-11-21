#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_MDL022_SafeParallelLaunch v0108 — 薄尾:run 跑完接官方對帳(VDF_MDL032_TWPriceReconcile 尾版 apply);前版一字不動

操作員 2026-11-21:「輸出驗證」→ 裁定「加官方對帳層(建議)」:Yahoo 照抓,入庫後逐日對官方,官方值覆蓋,改動先備份,可重跑。
VDF_MDL032 v0100 在容器資料家實跑 GREEN(刪休市佔位 2,007 · 改官方 568,411 · 補缺 2,342 · 寫後剩 0);
可是每一輪 Yahoo 增量又會寫進新的休市佔位 / 錯值 → 對帳要跟著每一輪跑,不能只跑一次。
本版只加一件事(照 v0106「跑前先 fixnames」的同一個樣子):run 跑完(不帶 --dry)後,資料家(--data-home / --via-db 換算後)
有 output_hub/mega/vdf_tw_market.duckdb → 叫 VDF_MDL032 尾版 apply --home <資料家>(它自己先整檔備份、一個交易寫完、寫後再驗、冪等);
沒有資料家 / 沒有主庫 / 沒有 MDL032 → 印一行略過的理由,不擋;對帳 RED 而前版 rc 0 → 回 1(不把紅藏在綠裡)。
其餘(降壓等靜 · 固定 3 道 · 不監控 · --via-db · fixnames · 兩座橋)全部轉給 v0107 / v0106。不代設同意閘;不碰 TA-Lib。
用法同前版:run … · check · --selftest
"""
from __future__ import annotations
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。啟動器自己不連網,連網的是各擷取引擎。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0108"
TAG = f"{STEM} {VERSION}"
RECON_GLOB = "VDF_MDL032_TWPriceReconcile_v*.py"
DB_REL = Path("output_hub") / "mega" / "vdf_tw_market.duckdb"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("vdf_launch_prior_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


def data_home(args: list) -> str:
    """同 v0106 的換算(--via-db → --data-home · 相對 → 絕對),回資料家;沒有 = ""。"""
    a = PRIOR.abs_paths(PRIOR.via_db_args(list(args)))
    return a[a.index("--data-home") + 1] if "--data-home" in a and a.index("--data-home") + 1 < len(a) else ""


def reconcile_after_run(args: list, runner=None) -> tuple:
    """回 (rc 或 None, 印的行)。None = 略過(理由在行裡)。"""
    if "--dry" in args:
        return None, [f"[{TAG}] 官方對帳略過:--dry(只數不寫)"]
    dh = data_home(args)
    if not dh:
        return None, [f"[{TAG}] 官方對帳略過:沒給資料家(--data-home / --via-db)"]
    if not (Path(dh) / DB_REL).is_file():
        return None, [f"[{TAG}] 官方對帳略過:資料家沒有 {DB_REL.as_posix()}"]
    m32 = sorted((p for p in HERE.glob(RECON_GLOB) if _vnum(p) >= 0), key=_vnum)
    if not m32:
        return None, [f"[{TAG}] 官方對帳略過:VDF_MDL032_TWPriceReconcile 不在"]
    cmd = [sys.executable, "-B", str(m32[-1]), "apply", "--home", str(dh)]
    env = dict(os.environ, VIA_FROM_VDFSM="YES", PYTHONUTF8="1")
    try:
        cp = (runner or subprocess.run)(cmd, cwd=str(dh), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    except Exception as exc:  # noqa: BLE001
        return 1, [f"[{TAG}] 官方對帳沒跑完:{type(exc).__name__}: {str(exc)[:120]}"]
    lines = [x for x in (cp.stdout or "").splitlines() if x.strip() and not x.startswith("{")][:4]
    return cp.returncode, lines + ([f"[{TAG}] 官方對帳 rc {cp.returncode}(看上一行點名)"] if cp.returncode else [])


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    rc = PRIOR.main(args)
    if args[:1] != ["run"]:
        return rc
    rrc, lines = reconcile_after_run(args)
    for ln in lines:
        print(ln, flush=True)
    return 1 if (rrc not in (None, 0) and rc == 0) else rc


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(run 跑完接官方對帳;假子行程 · 零網路)===")
    chk("⓪ 前版 %s 自測過" % PRIOR_PATH.stem, rc0 == 0, f"rc {rc0}")
    seen = []

    def fake(cmd, **k):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "[VDF_MDL032] GREEN · 刪休市佔位 0 · 改官方 0\n{\"ok\": true}\n", "")
    with tempfile.TemporaryDirectory(prefix="mdl022_v0108_") as td:
        home = Path(td) / "dict"
        rc_a, l_a = reconcile_after_run(["run", "--data-home", str(home)], runner=fake)
        (home / DB_REL).parent.mkdir(parents=True)
        (home / DB_REL).write_bytes(b"")
        rc_b, l_b = reconcile_after_run(["run", "--data-home", str(home)], runner=fake)
        rc_c, l_c = reconcile_after_run(["run", "--data-home", str(home), "--dry"], runner=fake)
        rc_d, l_d = reconcile_after_run(["run"], runner=fake)
        vdb = Path(td) / "via_database"
        ((vdb / "vdf_database") / DB_REL).parent.mkdir(parents=True)
        ((vdb / "vdf_database") / DB_REL).write_bytes(b"")
        rc_e, _ = reconcile_after_run(["run", "--via-db", str(vdb)], runner=fake)
        red = lambda cmd, **k: subprocess.CompletedProcess(cmd, 1, "[VDF_MDL032] RED · 寫後剩 不符 3\n", "")  # noqa: E731
        rc_f, l_f = reconcile_after_run(["run", "--data-home", str(home)], runner=red)
    chk("① 資料家沒有主庫 → 略過一行理由 · 不叫 MDL032", rc_a is None and "沒有" in l_a[0] and not seen[:0], l_a)
    chk("② 有主庫 → 叫 MDL032 尾版 apply --home <資料家>(絕對路徑)· 回它的 rc 與 GREEN 行",
        rc_b == 0 and seen and Path(seen[0][2]).name.startswith("VDF_MDL032_TWPriceReconcile_v") and seen[0][3:5] == ["apply", "--home"]
        and Path(seen[0][5]).is_absolute() and any("GREEN" in x for x in l_b), (seen[:1], l_b))
    chk("③ --dry → 略過(只數不寫)· 沒資料家 → 略過", rc_c is None and rc_d is None and "--dry" in l_c[0] and "資料家" in l_d[0])
    chk("④ --via-db <via_database> → 資料家 = <via_database>/vdf_database(同 v0106 換算)",
        rc_e == 0 and len(seen) == 2 and Path(seen[-1][5]) == (vdb / "vdf_database").resolve(), [c[5] for c in seen])
    chk("⑤ 對帳 RED → 回 rc 1 + 點名行(不把紅藏在綠裡)", rc_f == 1 and any("rc 1" in x for x in l_f), l_f)
    m32 = sorted(HERE.glob(RECON_GLOB), key=_vnum)
    chk("⑥ 對帳模組在(%s)" % (m32[-1].name if m32 else "—"), bool(m32))
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 兩座標準橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "def _via_net" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())

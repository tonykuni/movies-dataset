#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_LocalIntegrateLaunch v0102 — 薄尾(v0100 / v0101 一字不動):自測不吃本機狀態

2026-11-28 主機 vv:v0101 自測 12/13,不過的是「找不到 = None 且列出找過的根」。
根因:v0101 的找境除了 VIA_ENV_ROOT 之外,固定還會看家目錄的 ~/envs · ~/miniconda3/envs · ~/anaconda3/envs …;
  自測把 VIA_ENV_ROOT 指到空夾,但家目錄沒隔離 —— 操作員桌機真的有 via_vdf 境,所以「找不到」那一檢找到了 → NG。
  找境邏輯沒錯(真機上找到正是要的);錯的是自測吃了本機狀態(CLAUDE.md「自測不吃本機狀態」)。
本版只做一件事:自測時把 v0101 的自測放進子行程,家目錄(HOME · USERPROFILE · HOMEDRIVE/HOMEPATH)指到暫存夾再跑;
  另在本行程把 Path.home 暫時指到暫存夾,驗「家目錄隔離後找不到 = None」。其餘一切照 v0101(main 原樣轉交)。
零網路 · 不碰 TA-Lib · 不設同意閘 · 不建境、不刪境。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(操作員 2026-11-25「網路工具也要強制加入」;從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    import os as _nb_os
    from pathlib import Path as _nb_Path
    _nb_roots = [_nb_Path(__file__).resolve(), _nb_Path.cwd().resolve()]
    if _nb_os.environ.get("VIA_REPO"):
        _nb_roots.append(_nb_Path(_nb_os.environ["VIA_REPO"]).resolve())
    for _nb_r in _nb_roots:
        for _nb_q in (_nb_r, *_nb_r.parents):
            for _nb_dir in (_nb_q / "supportive modules" / "network", _nb_q / "VeritasIntelligenceAnalytics" / "supportive modules" / "network"):
                _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py")) if _nb_dir.is_dir() else []
                if _nb_hits:
                    VIA_NET_TOOL_PATH = str(_nb_hits[-1])
                    break
            if VIA_NET_TOOL_PATH:
                break
        if VIA_NET_TOOL_PATH:
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT:載入不出網,真的連線才看閘);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

STEM = "VDF_LocalIntegrateLaunch"
VERSION = "v0102"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve()


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)               # v0101(找境 · VCGC 健康 · 整合)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def isolated_env(home: Path) -> dict:
    """家目錄全指到暫存夾;同意閘拿掉;子行程用 UTF-8。"""
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), HOMEDRIVE=home.drive or "", HOMEPATH=str(home)[len(home.drive):],
               PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT", "VIA_PY_VDF", "VIA_ENV_ROOT", "VIA_ENV_ROOTS"):
        env.pop(k, None)
    env.setdefault("VIA_REPO", str(HERE.parents[2]))
    return env


def prior_selftest_isolated() -> tuple:
    with tempfile.TemporaryDirectory(prefix="vdf_lil102_home_") as td:
        try:
            cp = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=900, stdin=subprocess.DEVNULL, env=isolated_env(Path(td)), cwd=str(HERE.parent))
        except subprocess.TimeoutExpired:
            return 124, ["逾時"]
    bad = [ln.strip() for ln in (cp.stdout + cp.stderr).splitlines() if "[NG]" in ln or "[FAIL]" in ln]
    return cp.returncode, bad


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [NG] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 · 前版 {PRIOR_PATH.name} 自測在隔離家目錄的子行程跑 · 零網路)", flush=True)
    src = HERE.read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路橋在", VIA_ACCEL is not None
        and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    keep_home, keep_env = Path.home, {k: os.environ.get(k) for k in ("VIA_PY_VDF", "VIA_ENV_ROOT", "VIA_ENV_ROOTS", "PATH")}
    with tempfile.TemporaryDirectory(prefix="vdf_lil102_") as td:
        t = Path(td)
        (t / "miniconda3" / "envs").mkdir(parents=True)
        try:
            Path.home = classmethod(lambda cls: t)            # 只在這一檢:家目錄 = 暫存夾(底下有空的 miniconda3/envs)
            for k in ("VIA_PY_VDF", "VIA_ENV_ROOTS"):
                os.environ.pop(k, None)
            os.environ["VIA_ENV_ROOT"] = str(t / "none")
            os.environ["PATH"] = ""
            p, tried = PRIOR.find_vdf_python(t / "repo")
        finally:
            Path.home = keep_home
            for k, v in keep_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    chk("T2 家目錄隔離後:找不到 = None · 找過的根含暫存家目錄的 miniconda3/envs 與 conda env list",
        p is None and "conda env list" in tried and any("miniconda3" in x for x in tried), (p, tried))
    rc, bad = prior_selftest_isolated()
    chk("T3 前版 v0101 自測在隔離家目錄照過(本機的境不再混進自測)", rc == 0 and not bad, (rc, bad[:3]))
    print(f"{TAG} selftest {sum(ok)}/{len(ok)}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())

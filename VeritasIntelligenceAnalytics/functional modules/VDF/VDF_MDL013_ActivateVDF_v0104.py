#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0104 — 薄尾:PYTHONPATH 上兩份 bootstrap 讓每支 Python 起跑慢到逾時(工作站 2026-10-18)

工作站跑 PS 一鍵 v0102:加速器 / 網路自測各 300 秒逾時,v0103 自測 ⑰ 的 `python -c "import numexpr"` 120 秒逾時、
丟 subprocess.TimeoutExpired 的 traceback。根因:PYTHONPATH 上有兩份 `supportive modules/bootstrap`(兩棵樹各一份),
sitecustomize.py 的 _chain_shadowed() 會跑「sys.path 上下一份同名檔」→ 兩份互相接力到遞迴上限,每支 Python 起跑都重做一大段。
本版(執行邏輯其餘全照 v0103):
  · 子行程環境(flow_env)只留第一份 bootstrap(其餘拿掉並記 VIA_BOOTSTRAP_DEDUPED=拿掉幾份);只有一份 / 沒有就一字不動。
  · numexpr 探針同樣去重;子行程逾時不再丟 traceback,照實回「出錯」(⑰ 判 FAIL,不當機)。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0104(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0104(p) < _vnum_v0104(__file__)), key=_vnum_v0104)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- PYTHONPATH 只留一份 bootstrap
_BOOT_RX = re.compile(r"[\\/]supportive modules[\\/]bootstrap[\\/]?$", re.I)


def dedupe_bootstrap(pythonpath: str | None, sep: str = os.pathsep) -> tuple:
    """PYTHONPATH 只留第一份 `supportive modules/bootstrap`(其餘拿掉,其他路徑原序不動)→ (新值, 拿掉幾份)。"""
    if not pythonpath:
        return pythonpath, 0
    parts = [p for p in pythonpath.split(sep) if p]
    seen, out, dropped = False, [], 0
    for p in parts:
        if _BOOT_RX.search(p):
            if seen:
                dropped += 1
                continue
            seen = True
        out.append(p)
    return (sep.join(out) if dropped else pythonpath), dropped


_FLOW_ENV_V0102 = V0100.flow_env                   # = v0102 換上的 flow_env(numexpr 上限)


def flow_env(res: dict, flow: str, base_env: dict | None = None) -> dict:
    """同 v0102 flow_env;子行程 PYTHONPATH 只留一份 bootstrap(拿掉的份數記 VIA_BOOTSTRAP_DEDUPED)。"""
    env = _FLOW_ENV_V0102(res, flow, base_env)
    new, dropped = dedupe_bootstrap(env.get("PYTHONPATH"))
    if dropped:
        env["PYTHONPATH"] = new
        env["VIA_BOOTSTRAP_DEDUPED"] = str(dropped)
    return env


for _m in (V0100, PRIOR.PRIOR, PRIOR):
    _m.flow_env = flow_env


def numexpr_probe(env_thread_keys: dict, raise_to: int, stub_dir: Path | None = None, timeout: int = 120) -> tuple:
    """同 v0103 numexpr_probe;子行程 PYTHONPATH 去重;逾時不丟 traceback → (True, 「逾時」說明, kind)。"""
    env = dict(os.environ)
    env.update({k: str(v) for k, v in env_thread_keys.items() if k.startswith(("NUMEXPR", "OMP"))})
    env["NUMEXPR_NUM_THREADS"] = str(raise_to)
    try:
        import numexpr  # noqa: F401
        kind = "numexpr"
    except ImportError:
        kind = "stub"
        if stub_dir is not None:
            (stub_dir / "numexpr.py").write_text(PRIOR._NUMEXPR_STUB, encoding="utf-8")
            env["PYTHONPATH"] = os.pathsep.join([str(stub_dir)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    new, dropped = dedupe_bootstrap(env.get("PYTHONPATH"))
    if dropped:
        env["PYTHONPATH"] = new
    try:
        r = subprocess.run([sys.executable, "-c", "import numexpr"], env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return True, f"子行程 {timeout} 秒逾時(Python 起跑卡住;查 PYTHONPATH 是否掛了兩份 supportive modules/bootstrap)", kind
    out = (r.stdout + r.stderr).strip()
    return PRIOR._NE_ERR in out, out[-160:], kind


PRIOR.numexpr_probe = numexpr_probe                # v0103 ⑰ 在自己的模組裡用這個名字 → 換上本版

_ACTIVATE_V0103 = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0103 activate(標頭與總覽標本版;總覽 JSON 的 schema 不變)。"""
    keep = PRIOR.TAG                               # v0103.activate 把它自己的 TAG 往下傳 → 換成本版
    PRIOR.TAG = TAG
    try:
        return _ACTIVATE_V0103(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(PYTHONPATH 只留一份 bootstrap · numexpr 探針不當機;沙盒 · 零網路)===")
    a = os.path.join("A", "supportive modules", "bootstrap")
    b = os.path.join("B", "supportive modules", "bootstrap")
    two = os.pathsep.join([a, "X", b, "Y"])
    new, dropped = dedupe_bootstrap(two)
    one, d1 = dedupe_bootstrap(os.pathsep.join([a, "X"]))
    win, dw = dedupe_bootstrap(r"C:\o\VIA\supportive modules\bootstrap;C:\m\VIA\supportive modules\bootstrap\;Z", sep=";")
    chk("⑲ PYTHONPATH 只留第一份 bootstrap:其他路徑原序不動;只有一份 / 沒有就一字不動;Windows 反斜線同判",
        new == os.pathsep.join([a, "X", "Y"]) and dropped == 1 and one == os.pathsep.join([a, "X"]) and d1 == 0
        and dedupe_bootstrap("")[1] == 0 and dedupe_bootstrap(None)[0] is None
        and win == r"C:\o\VIA\supportive modules\bootstrap;Z" and dw == 1,
        {"兩份→": new, "拿掉": dropped, "Windows 拿掉": dw})
    real_boot = HERE.parent.parent / "supportive modules" / "bootstrap"
    with tempfile.TemporaryDirectory(prefix="activatevdf104_") as td:
        t = Path(td)
        res = V0100.optimize_resources(want=3, stamp="20261018_140000", root=t)
        copy_boot = t / "other_tree" / "supportive modules" / "bootstrap"
        copy_boot.mkdir(parents=True)
        real = (real_boot / "sitecustomize.py").is_file()
        if real:
            (copy_boot / "sitecustomize.py").write_text((real_boot / "sitecustomize.py").read_text(encoding="utf-8"),
                                                       encoding="utf-8")
            base = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": os.pathsep.join([str(real_boot), str(copy_boot)]),
                    "VIA_FAMILY": "vdf", "VIA_ROOT": str(HERE.parent.parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
            env = V0100.flow_env(res, "engines", base_env=base)
            r = subprocess.run([sys.executable, "-c", "import os;print(os.environ.get('VIA_BOOT_CHAINED','-'))"],
                               env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            chained = (r.stdout or "").strip()
            good = (env.get("VIA_BOOTSTRAP_DEDUPED") == "1" and str(copy_boot) not in env["PYTHONPATH"]
                    and str(real_boot) in env["PYTHONPATH"] and str(copy_boot) not in chained and r.returncode == 0
                    and int(env["NUMEXPR_MAX_THREADS"]) >= int(env["NUMEXPR_NUM_THREADS"]))
            note = {"拿掉": env.get("VIA_BOOTSTRAP_DEDUPED"), "子行程接力": chained[-60:]}
        else:                                      # 本樹沒有 bootstrap/sitecustomize.py → 照實略過真跑,只驗去重
            good = V0100.flow_env(res, "engines", base_env={"PYTHONPATH": os.pathsep.join([a, b])})["PYTHONPATH"] == a
            note = "本樹沒有 supportive modules/bootstrap/sitecustomize.py:略過真跑,只驗去重"
        chk("⑳ 真跑:母環境掛兩份 bootstrap(本樹 + 另一棵樹的同一支 sitecustomize)→ 子行程環境只剩本樹那份,"
            "子行程不再接力到另一棵樹;其他流程鍵照 v0102(numexpr 上限)", good, note)
        keep_run = subprocess.run

        def _hang(*_a, **_k):
            raise subprocess.TimeoutExpired(cmd=_a[0] if _a else "python", timeout=_k.get("timeout", 0))
        subprocess.run = _hang
        try:
            bad, note, _kind = numexpr_probe({"NUMEXPR_MAX_THREADS": "4"}, 8, t, timeout=1)
            crashed = False
        except Exception:
            bad, note, crashed = None, "", True
        finally:
            subprocess.run = keep_run
        chk("㉑ numexpr 探針的子行程逾時:不丟 traceback,照實回「出錯」並說明(v0103 ⑰ 因此判 FAIL 而不是當機)",
            not crashed and bad is True and "逾時" in note, note[:60])
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("㉒ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    if n != len(ok):
        return 1
    rc1 = PRIOR.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0102;PR #528 Codex P1)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())

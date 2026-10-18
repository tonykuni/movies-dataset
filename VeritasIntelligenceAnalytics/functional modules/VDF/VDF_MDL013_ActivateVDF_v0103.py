#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0103 — 薄尾:v0102 自測 ⑭ 在裝了 numexpr 的機器上當掉(工作站 2026-10-18)

工作站(Python 3.12 · 有 numexpr)跑 v0102 --selftest:⑪ ⑫ ⑬ 過,⑭ 丟
  TypeError: dict() got multiple values for keyword argument 'NUMEXPR_NUM_THREADS'
⑭ 的「有裝 numexpr 才真測」那一段把子行程環境寫成 dict(os.environ, **{…NUMEXPR_*…}, NUMEXPR_NUM_THREADS=…),
同一個鍵給兩次 → Python 直接拒絕。容器沒裝 numexpr,走「只驗數字」那條,所以沒現形(容器用 numexpr 替身重現)。
這是自測碼的錯,不是執行邏輯的錯:v0102 的 numexpr 修法(用量 = 每條執行緒數 · 上限 = 核數 × 2)本身是對的。
本版:
  · ⑰ 取代 v0102 ⑭ 的真測段:子行程環境先照 flow_env 填,再把 NUMEXPR_NUM_THREADS 拉到核數(模擬加速器拉高用量)
    → 真 import numexpr(沒裝就用測試替身,替身照 numexpr 的同一條規則印同一句錯)→ 不得印 nthreads cannot be larger;
    同時用 v0100 的環境(上限 = 每條執行緒數)跑一次,必須**印得出**那句錯(證明這個探針抓得到病)。
  · 委派 v0102 自測時讓 `import numexpr` 在那一段走 ImportError 分支(只驗數字;數字照驗),其餘全照跑。
  · 執行邏輯全照 v0102(只把標頭 / 總覽標成本版)。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
"""
from __future__ import annotations
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


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(__file__)), key=_vnum_v0103)
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


_ACTIVATE_V0102 = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0102 activate(標頭與總覽標本版;總覽 JSON 的 schema 不變 = 格式沒改)。"""
    keep = PRIOR.TAG
    PRIOR.TAG = TAG
    try:
        return _ACTIVATE_V0102(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
_NUMEXPR_STUB = (
    "# 測試替身:照 numexpr 載入時的執行緒規則(用量 > 上限 → 印同一句錯);只在沒裝 numexpr 的機器上用\n"
    "import os\n"
    "_max = int(os.environ.get('NUMEXPR_MAX_THREADS') or 64)\n"
    "_req = int(os.environ.get('NUMEXPR_NUM_THREADS') or os.environ.get('OMP_NUM_THREADS') or 1)\n"
    "if _req > _max:\n"
    "    print('Error.  nthreads cannot be larger than environment variable \"NUMEXPR_MAX_THREADS\" (%d)' % _max)\n")
_NE_ERR = "nthreads cannot be larger"


def numexpr_probe(env_thread_keys: dict, raise_to: int, stub_dir: Path | None = None) -> tuple:
    """子行程環境 = 目前環境 + flow_env 的 NUMEXPR / OMP 鍵,再把 NUMEXPR_NUM_THREADS 拉到 raise_to(模擬加速器);
    import numexpr(沒裝就用替身)→ (印出錯沒有, 輸出, 用的是真 numexpr 還是替身)。"""
    env = dict(os.environ)
    env.update({k: str(v) for k, v in env_thread_keys.items() if k.startswith(("NUMEXPR", "OMP"))})
    env["NUMEXPR_NUM_THREADS"] = str(raise_to)
    try:
        import numexpr  # noqa: F401
        kind = "numexpr"
    except ImportError:
        kind = "stub"
        if stub_dir is not None:
            (stub_dir / "numexpr.py").write_text(_NUMEXPR_STUB, encoding="utf-8")
            env["PYTHONPATH"] = os.pathsep.join([str(stub_dir)] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    r = subprocess.run([sys.executable, "-c", "import numexpr"], env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    out = (r.stdout + r.stderr).strip()
    return _NE_ERR in out, out[-160:], kind


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(numexpr 真測段改正;沙盒 · 零網路)===")
    cores = os.cpu_count() or 1
    with tempfile.TemporaryDirectory(prefix="activatevdf103_ne_") as td:
        t = Path(td)
        res = V0100.optimize_resources(want=3, stamp="20261018_130000", root=t)
        new_env = V0100.flow_env(res, "fetch", base_env={})                 # 本鏈現行(v0102 換上的 flow_env)
        old_env = PRIOR._FLOW_ENV_V0100(res, "fetch", base_env={})          # v0100 原版(上限 = 每條執行緒數)
        stub = t / "stub"
        stub.mkdir()
        raise_to = max(cores, int(old_env["NUMEXPR_MAX_THREADS"]) + 1)      # 比 v0100 的上限大:舊環境必出錯
        bad_new, out_new, kind = numexpr_probe(new_env, raise_to, stub)
        bad_old, out_old, _ = numexpr_probe(old_env, raise_to, stub)
    chk("⑰ 取代 v0102 ⑭ 的真測段:加速器把 numexpr 用量拉到核數時,本鏈環境不印 nthreads cannot be larger;"
        "同一探針在 v0100 環境下必印得出(證明抓得到病)",
        not bad_new and bad_old and int(new_env["NUMEXPR_MAX_THREADS"]) >= raise_to
        and new_env["NUMEXPR_NUM_THREADS"] == str(res["plan"]["threads_per_flow"]),
        {"numexpr": kind, "拉到": raise_to, "本鏈上限": new_env["NUMEXPR_MAX_THREADS"], "本鏈出錯": bad_new,
         "v0100 上限": old_env["NUMEXPR_MAX_THREADS"], "v0100 出錯": bad_old})
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("⑱ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    n = sum(ok)
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}")
    if n != len(ok):
        return 1
    print("  [取代] v0102 ⑭ 的真測段(有裝 numexpr 才跑,子行程環境同鍵給兩次 → TypeError)由本版 ⑰ 取代;"
          "委派時 v0102 ⑭ 走「只驗數字」分支,其餘照跑")
    keep_ne = sys.modules.get("numexpr", ...)
    sys.modules["numexpr"] = None                  # 只讓委派那一段的 import numexpr 走 ImportError 分支
    try:
        rc1 = PRIOR.selftest()
    finally:
        if keep_ne is ...:
            sys.modules.pop("numexpr", None)
        else:
            sys.modules["numexpr"] = keep_ne
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

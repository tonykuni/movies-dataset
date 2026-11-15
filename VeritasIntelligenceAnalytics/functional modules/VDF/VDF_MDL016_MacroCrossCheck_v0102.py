#!/usr/bin/env python3
r"""VDF_MDL016_MacroCrossCheck v0102 — 薄尾:自測不再被操作員自己設的 FRED 鑰(環境變數)左右(引擎行為一字不動)

工作站實跑(2026-11-15 10:06 ActivateVDF v0117 · engine_launch):本支 v0101 RED 3/4 —— ①「測具下前版自測 rc 0」FAIL;
②③④ OK(VAKE 測具本身沒事)。容器同一支 GREEN。
根因(AST 定位,v0100 本體 `find_key()`;本版自測 ④ 會印出行號):
  先讀環境變數裡的 FRED 鑰,沒有才讀輸出根的鑰檔。v0100 自測寫一把假鑰檔,再驗網址帶的是那把假鑰 —
  操作員機器設了環境鑰時,網址帶的是操作員的鑰 → 該項 FAIL;(--live 那一項驗的是假鑰檔)。
  容器沒設鑰 → 全綠,所以只在工作站紅。
本版(v0100 / v0101 一字不動;AI 不設、不寫、不印鑰,也不讀鑰的值):
  前版鏈自測改在子行程跑(自己跑自己,--prior-selftest-child),子行程環境 = 本行程環境少掉「鑰那一個名字」
  + PYTHONIOENCODING=utf-8;本行程環境一字不動(操作員的鑰還在原處)。
自測:① 子環境只少鑰那一個名字(純字典測)② 前版鏈在子行程 rc 0 ③ 本行程環境前後一樣
      ④ AST 定位根因仍在(前版先讀環境鑰、後讀鑰檔)⑤ 兩座橋 · 本檔不寫環境 · 不寫鑰名字面 · 同意閘不讀不寫 · 不匯入他系統 · 不碰 TA-Lib。零網路。
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
    """統包唯一網路工具惰性載入;本檔的連網全經前版(MDL008 子行程改道)。"""
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
# ===== [VIA:NET-BRIDGE:END] =====

_STEM = "VDF_MDL016_MacroCrossCheck"
import ast
import importlib.util
import os
import re
import subprocess
import sys
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
CHILD_FLAG = "--prior-selftest-child"
ROOT_FN = "find_key"                     # v0100 本體裡「先讀環境鑰」的那個函數(根因位置)


def _vnum_tail(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_tail(p) < _vnum_tail(__file__)), key=_vnum_tail)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _key_name() -> str:
    """鑰的環境變數名取自前版常數(本檔不寫字面)。"""
    return str(getattr(PRIOR, "KEY_ENV"))


def child_env(env) -> dict:
    """子行程環境:原樣照抄,只少「鑰那一個名字」(大小寫不分,Windows 環境名不分大小寫)+ PYTHONIOENCODING=utf-8。"""
    hide = _key_name().upper()
    out = {k: v for k, v in dict(env).items() if k.upper() != hide}
    out["PYTHONIOENCODING"] = "utf-8"
    return out


def _base_module(mod):
    """沿 PRIOR 鏈走到本體(沒有 PRIOR 的那一版)。只看模組自己的全域,不走 __getattr__ 轉接。"""
    seen = 0
    while isinstance(vars(mod).get("PRIOR"), type(sys)) and seen < 20:
        mod, seen = vars(mod)["PRIOR"], seen + 1
    return mod


def root_cause_lines() -> dict:
    """AST 定位:本體 ROOT_FN 裡第一次讀 os.environ 的行 · 第一次碰鑰檔常數的行(前者在前 = 根因仍在)。"""
    base = _base_module(PRIOR)
    path = Path(base.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == ROOT_FN), None)
    if fn is None:
        return {"file": path.name, "fn": None}
    env_ln = file_ln = None
    for n in ast.walk(fn):
        ln = getattr(n, "lineno", None)
        if ln is None:
            continue
        if isinstance(n, ast.Attribute) and n.attr == "environ" and isinstance(n.value, ast.Name) and n.value.id == "os":
            env_ln = ln if env_ln is None else min(env_ln, ln)
        if isinstance(n, ast.Name) and n.id == "KEY_FILE":
            file_ln = ln if file_ln is None else min(file_ln, ln)
    return {"file": path.name, "fn": ROOT_FN, "def_line": fn.lineno, "env_line": env_ln, "keyfile_line": file_ln}


def _own_src_ok() -> tuple:
    src = Path(__file__).read_text(encoding="utf-8")
    bad = []
    if "[VIA:ACCEL-BRIDGE:v0100]" not in src or "[VIA:NET-BRIDGE:v0100]" not in src:
        bad.append("缺橋")
    if ("_CON" + "SENT") in src:              # 拆開寫:不讓本行自己被當成「提到同意閘」
        bad.append("提到同意閘")
    if re.search(r"os\.environ\[[^\]]+\]\s*=(?!=)|os\.environ\.(pop|update|setdefault|clear)\(|\bputenv\b|\bsetx\b", src):
        bad.append("寫環境")
    if _key_name() in src:
        bad.append("鑰名字面")
    if re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VRN2_|VCGC|ta" + r"lib\b)", src, re.M):
        bad.append("匯入他系統 / TA-Lib")
    return (not bad), bad


def _run_prior_child() -> tuple:
    t0 = time.time()
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), CHILD_FLAG], env=child_env(os.environ),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    return r.returncode, round(time.time() - t0, 1), (r.stdout or "").splitlines(), (r.stderr or "").splitlines()


def selftest() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("=== %s · 薄尾自測(前版鏈在子行程跑 · 子環境少鑰那一個名字;零網路)===" % TAG, flush=True)
    key = _key_name()
    print("  本機有沒有設 FRED 環境鑰:%s(只看有沒有,值不讀不印)" % ("有" if key in os.environ else "沒有"), flush=True)
    sample = {"PATH": "/x", key: "sim-value", key.lower(): "sim-lower", "VAKE_ROOT": "/v"}
    ce = child_env(sample)
    chk("① 子環境只少鑰那一個名字(大小寫不分)· 其餘照抄 · 多 PYTHONIOENCODING", ce == {"PATH": "/x", "VAKE_ROOT": "/v", "PYTHONIOENCODING": "utf-8"}, ce)
    before = dict(os.environ)
    rc, secs, out, err = _run_prior_child()
    for ln in out[-14:]:
        print("    │ " + ln, flush=True)
    if rc != 0:
        for ln in err[-6:]:
            print("    │ stderr " + ln, flush=True)
    chk("② 前版鏈(%s)在子行程自測 rc 0(%.1f 秒)" % (PRIOR_PATH.stem, secs), rc == 0, "rc %s" % rc)
    chk("③ 本行程環境前後一樣(操作員的鑰若有,原封不動)", dict(os.environ) == before)
    rcl = root_cause_lines()
    chk("④ AST 定位根因:%s %s() 第 %s 行起 · 先讀環境(第 %s 行)後讀鑰檔(第 %s 行)" % (
        rcl.get("file"), rcl.get("fn"), rcl.get("def_line"), rcl.get("env_line"), rcl.get("keyfile_line")),
        rcl.get("fn") and rcl.get("env_line") and rcl.get("keyfile_line") and rcl["env_line"] < rcl["keyfile_line"], rcl)
    ok, bad = _own_src_ok()
    chk("⑤ 兩座橋在 · 本檔不寫環境 · 不寫鑰名字面 · 同意閘不讀不寫 · 不匯入他系統 · 不碰 TA-Lib", ok, bad)
    print("[計] %s 薄尾 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"), flush=True)
    return 0 if not f else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if CHILD_FLAG in argv:
        return PRIOR.selftest()
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())

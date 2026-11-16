#!/usr/bin/env python3
r"""VDF_ENG071_GroupBacktest v0102 — 薄尾:啟動自測不再跑真庫十分鐘回測(逾時紅 → 誠實 NODATA);run 照舊跑真庫(引擎行為一字不動)

工作站實跑(2026-11-14 / 2026-11-15 ActivateVDF engine_launch):本支 v0101 RED · 逾時 600 秒(VIA_VDF_LAUNCH_TIMEOUT)。
容器(沒有台股庫)同一支 0.6 秒 NODATA(rc 2 · 誠實停)。
根因(AST 定位,v0101;本版自測 ④ 印行號):selftest() 第一步就呼叫 run() —— run() 用 ENG070 分類引擎尾版
(load_panel → add_residual → load_stories → classify_story → compare_windows)對**真的台股庫**整條回測,
工作站庫大 → 超過 600 秒。ENG070 本身已照操作員令(2026-11-15)退出啟動(VDF_LaunchRetire_SSOT_v0100.json),原因同一個。
本版(v0101 一字不動):
  自測期間把三個位置指到空暫存夾 —— ENG070 的台股庫路徑(DB_TW)· 存證夾(REP)· 頁(OUT_UI)—— 再跑 v0101 自測:
  庫不在 → v0101 誠實停 rc 2(NODATA,黃)· 不碰真庫 · 不寫真存證 · 不蓋真頁。跑完全數還原。
  真回測照舊:python VDF_ENG071_GroupBacktest_v0102.py(= v0101 run,真庫、真存證、真頁)。
  要不要乾脆跟 ENG070 一樣退出啟動 = 操作員的手(退役冊下一版加一列)。
自測:① 前版自測在測具下 rc 2(誠實停)且秒數有上限 ② 真存證夾 / 真頁零觸碰 ③ 測具全數還原
      ④ AST 定位根因仍在(selftest 先叫 run · run 走 ENG070 真庫鏈)⑤ 兩座橋 · 不寫環境 · 同意閘不讀不寫 · 不匯入他系統 · 不碰 TA-Lib。
回傳:本版各項都過 → rc 2(NODATA:啟動自測刻意不碰真庫,不冒充綠);任一項不過 → rc 1。零網路。
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
    """統包唯一網路工具惰性載入;本引擎零外網(回測只讀本機庫)。"""
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

_STEM = "VDF_ENG071_GroupBacktest"
import ast
import contextlib
import importlib.util
import re
import shutil
import sys
import tempfile
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
SELFTEST_BUDGET_S = 120                 # 測具下前版自測應在幾秒內誠實停;超過 = 測具沒擋住真庫


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


@contextlib.contextmanager
def no_real_db():
    """測具:ENG070 台股庫路徑 · 存證夾 · 頁 → 空暫存夾;跑完全數還原(只動前版模組的三個全域 + 一個載入函數)。"""
    td = Path(tempfile.mkdtemp(prefix="vdf_eng071_box_"))
    keep = {k: vars(PRIOR)[k] for k in ("_eng070", "REP", "OUT_UI")}
    orig_loader = keep["_eng070"]

    def _eng070_boxed():
        m = orig_loader()
        m.DB_TW = td / "db" / "vdf_tw_market.duckdb"          # 不存在 → v0101 run 誠實停 rc 2
        return m
    try:
        PRIOR._eng070 = _eng070_boxed
        PRIOR.REP = td / "rep"
        PRIOR.OUT_UI = td / "ui" / keep["OUT_UI"].name
        yield td
    finally:
        for k, v in keep.items():
            setattr(PRIOR, k, v)
        shutil.rmtree(td, ignore_errors=True)


def _snapshot(rep: Path, page: Path) -> tuple:
    files = sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in rep.glob("*")) if rep.is_dir() else []
    pg = (page.stat().st_size, page.stat().st_mtime_ns) if page.is_file() else None
    return tuple(files), pg


def root_cause_lines() -> dict:
    """AST 定位:前版 selftest() 叫 run() 的行 · run() 叫 ENG070 真庫鏈(load_panel / classify_story)的行。"""
    tree = ast.parse(Path(PRIOR.__file__).read_text(encoding="utf-8"))
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

    def first_call(fn, names):
        if fn is None:
            return None
        hits = [n.lineno for n in ast.walk(fn) if isinstance(n, ast.Call) and (
            (isinstance(n.func, ast.Name) and n.func.id in names) or (isinstance(n.func, ast.Attribute) and n.func.attr in names))]
        return min(hits) if hits else None
    return {"file": Path(PRIOR.__file__).name, "selftest_def": getattr(fns.get("selftest"), "lineno", None),
            "selftest_calls_run": first_call(fns.get("selftest"), {"run"}),
            "run_def": getattr(fns.get("run"), "lineno", None),
            "run_real_chain": first_call(fns.get("run"), {"load_panel", "classify_story"})}


def _own_src_ok() -> tuple:
    src = Path(__file__).read_text(encoding="utf-8")
    bad = []
    if "[VIA:ACCEL-BRIDGE:v0100]" not in src or "[VIA:NET-BRIDGE:v0100]" not in src:
        bad.append("缺橋")
    if ("_CON" + "SENT") in src:              # 拆開寫:不讓本行自己被當成「提到同意閘」
        bad.append("提到同意閘")
    if re.search(r"os\.environ\[[^\]]+\]\s*=(?!=)|os\.environ\.(pop|update|setdefault|clear)\(|\bputenv\b", src):
        bad.append("寫環境")
    if re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VRN2_|VCGC|ta" + r"lib\b)", src, re.M):
        bad.append("匯入他系統 / TA-Lib")
    return (not bad), bad


def selftest() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("=== %s · 薄尾自測(測具:不碰真台股庫 · 不寫真存證 / 頁;零網路)===" % TAG, flush=True)
    real = {k: vars(PRIOR)[k] for k in ("_eng070", "REP", "OUT_UI")}
    snap0 = _snapshot(real["REP"], real["OUT_UI"])
    t0 = time.time()
    with no_real_db():
        rc = PRIOR.selftest()
    secs = round(time.time() - t0, 1)
    chk("① 前版自測在測具下誠實停 rc 2(NODATA)· %.1f 秒(上限 %d)" % (secs, SELFTEST_BUDGET_S), rc == 2 and secs < SELFTEST_BUDGET_S, "rc %s" % rc)
    chk("② 真存證夾(%s)與真頁(%s)零觸碰" % (real["REP"].name, real["OUT_UI"].name), _snapshot(real["REP"], real["OUT_UI"]) == snap0)
    chk("③ 測具全數還原(_eng070 · REP · OUT_UI)", all(vars(PRIOR)[k] is real[k] for k in real))
    rcl = root_cause_lines()
    chk("④ AST 定位根因:%s selftest() 第 %s 行叫 run()(第 %s 行起)· run() 第 %s 行走 ENG070 真庫鏈" % (
        rcl["file"], rcl["selftest_calls_run"], rcl["run_def"], rcl["run_real_chain"]),
        bool(rcl["selftest_calls_run"] and rcl["run_real_chain"]), rcl)
    ok, bad = _own_src_ok()
    chk("⑤ 兩座橋在 · 不寫環境 · 同意閘不讀不寫 · 不匯入他系統 · 不碰 TA-Lib", ok, bad)
    print("[計] %s 薄尾 %d/%d · %s" % (TAG, p, p + f, "NODATA(啟動自測刻意不碰真庫;真回測 = run)" if not f else "FAIL"), flush=True)
    return 2 if not f else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    return PRIOR.run()


if __name__ == "__main__":
    sys.exit(main())

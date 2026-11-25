#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_GovernanceApply v0104 — 薄尾(v0100–v0103 一字不動):加速器以「生效」計併成第 ④ 條初始流程

操作員 2026-11-25 21:47:「用 VCGC 省 Token 工具處理以上全部,整合成一支 py(用最新加速器),再用一支 ps 啟動」(VCGC-REQ268)。
主機兩份貼回(gov apply · Invoke-VIA-AccelCover v0101)對照後,一支 py 要處理的事:
  ① gov 的 accel / net 車道看標記(CGC_MDL230),橋掃描器 v0112 `--effective` 看「生效」,兩邊數字對不上
     (gov:net 應做 0 · accel 缺 11;effective:PY 生效 1822/1822 · VRN 出網檔缺網路橋 2)
     → 本版把 `CGC_MDL124_BridgeSweeper` 尾版 `--effective`(唯讀)當第 ④ 條初始流程,與 ① 計畫 ∥ ② ReworkGuard ∥ ③ 編號稽核
       同時起跑;驗證時鍵沒變就取它的結果,車道寫過檔才重跑。報告多「加速器生效」「加速器非綠」兩行。
  ② accel 11 · param 10 全是「略過」卻亮黃:理由全是終態(名冊豁免 · 收容 / 凍結 · 前輪已解耦 · 另一位置副本)
     → 車道動作全 OK、略過理由全是終態 → 綠;只要有一條不是終態照舊黃,有 FAIL 照舊紅。
  ③ ReworkGuard 回「rc 1」卻沒有判決行,看不出原因 → 沒判決行時附它輸出的最後一行。
其餘照 v0103(快取 · --fresh · 並行驗證 · 計時 · 三個初始流程)。零網路 · 零 TA-Lib · 不 import 他系統 · 不讀寫同意閘。
用法同前:apply [車道…] · verify · --fresh · selftest。
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
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VIA_GovernanceApply"
TAG = "VIA_GovernanceApply v0104"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
V3 = importlib.util.module_from_spec(_spec)                # v0103(V3.V2 = v0102 · V2.G = v0101 · V2.P = v0100)
sys.modules[_spec.name] = V3
_spec.loader.exec_module(V3)
V2, G, P = V3.V2, V3.G, V3.P


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(V3, name)


SWEEP_STEM = "CGC_MDL124_BridgeSweeper"
COVER_JSON = Path("VIA_Reports") / "vcgc" / "accel_cover" / "ACCEL_COVER_latest.json"
TERMINAL = re.compile(r"豁免|凍結|收容|已解耦|副本|唯一實作|只增不減|名冊")
ICON = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴", "GRAY": "⚪"}
_CPOOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gov_cover")


def sweeper(via: Path):
    """橋掃描器尾版(要有 --effective:v0112 以上);沒有回 None。"""
    c = [p for p in (via / "supportive modules" / "registry").glob(SWEEP_STEM + "_v*.py") if _vnum(p) >= 112]
    return max(c, key=_vnum) if c else None


def job_cover(via: Path) -> dict:
    """④ 加速器生效覆蓋(唯讀;只寫 VIA_Reports)。回可存快取的摘要。"""
    tool = sweeper(via)
    if tool is None:
        return {"lamp": "GRAY", "line": "沒有 --effective 版的橋掃描器(要 CGC_MDL124 v0112 以上)", "not_green": [], "rc": None}
    r = G.run([sys.executable, "-B", str(tool), "--effective"], via, 1800, {"PYTHONWARNINGS": "ignore", "PYTHONUTF8": "1"})
    try:
        rep = json.loads((via / COVER_JSON).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        tail = [x for x in (r.stdout + r.stderr).splitlines() if x.strip()][-1:]
        return {"lamp": "RED", "line": "rc %s · 沒有報告 · 末行:%s" % (r.returncode, tail[0][:150] if tail else "—"), "not_green": [], "rc": r.returncode}
    t = rep["total"]
    sysl = " · ".join("%s %s %s/%s 網 %s/%s PS %s/%s" % (ICON.get(v["lamp"], ""), s, v["effective"], v["py"], v["net_has"], v["net_callers"],
                                                        v["ps_has"], v["ps"]) for s, v in rep["systems"].items() if v["lamp"] != "GRAY")
    return {"lamp": rep["lamp"], "rc": r.returncode, "tool": tool.name,
            "line": "%s · PY 生效 %s/%s(%s%%)· 應掃 %d · 已掃 %d · 略過 %d · %s · PS 點源 %s" % (
                tool.stem.split("_")[-1], t["effective"], t["py"], t["pct"], rep["should_scan"], rep["scanned"], rep["skipped"], sysl, rep["ps_runtime"]),
            "not_green": ["%s %s" % (x["state"], x["file"]) for x in rep["not_green"][:20]]}


def job_rg(via: Path) -> str:
    rg = sorted((via / "docs" / "handoff" / "ai").glob("VIA_ReworkGuard_v*.py"), key=_vnum)
    if not rg:
        return "—"
    r = G.run([sys.executable, str(rg[-1]), "check"], via, 900)
    line = next((ln for ln in r.stdout.splitlines() if "check" in ln and "·" in ln), "")
    if line:
        return line[:200]
    tail = [x for x in (r.stdout + r.stderr).splitlines() if x.strip()][-1:]
    return ("rc %s · 沒有判決行 · 末行:%s" % (r.returncode, tail[0][:150] if tail else "—"))[:240]


V3.job_rg = job_rg                                  # v0103 start_initial 從自己的模組全域找它
_ORIG_START = V3.start_initial


def start_initial(via: Path) -> list:
    started = _ORIG_START(via)
    key = V2.state_key(via, "verify")
    if V2.FRESH is False and V3._peek(via, "cover", key):
        return started
    fut = _CPOOL.submit(lambda: V3._ORIG_CACHED_FORCE(via, "cover", key, lambda: V2.timed("加速器生效 CGC_MDL124", lambda: job_cover(via))))
    with V3._ILOCK:
        V3.INFLIGHT[("cover", key)] = fut
    return started + ["加速器生效 CGC_MDL124"]


V3.start_initial = start_initial
_PREV_VERIFY = P.verify


def verify(via: Path, new_files: list) -> dict:
    ex = _PREV_VERIFY(via, new_files)
    key = V2.state_key(via, "verify")             # 車道寫過檔 → 鍵變了 → 重跑;沒變 → 取 ④ 的結果
    try:
        val, _hit = V3.cached(via, "cover", key, lambda: V2.timed("加速器生效 CGC_MDL124", lambda: job_cover(via)))
    except Exception as exc:                        # noqa: BLE001
        val = {"lamp": "RED", "line": "%s: %s" % (type(exc).__name__, str(exc)[:120]), "not_green": []}
    ex["加速器生效"] = "%s %s" % (ICON.get(val.get("lamp"), ""), val.get("line", ""))
    if val.get("not_green"):
        ex["加速器非綠"] = " | ".join(val["not_green"][:10])
    return ex


_PREV_LAMP = P.lamp_of


def lamp_of(lane: dict, results) -> str:
    lp = _PREV_LAMP(lane, results)
    if (lp == "YELLOW" and results is not None and all(r.get("state") == "OK" for r in results)
            and lane.get("skipped") and all(TERMINAL.search(str(why)) for _f, why in lane["skipped"])):
        return "GREEN"                              # 略過理由全是終態(豁免 / 凍結 / 已解耦 / 副本…)= 不是待辦
    return lp


for _n, _f in (("verify", verify), ("lamp_of", lamp_of)):
    setattr(P, _n, _f)
G.verify = verify
P.TAG = TAG


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項 · 前版 %s 在子行程)" % (TAG, PRIOR_PATH.name), flush=True)
    sk_term = [("a.py", "CGC_MDL158 名冊豁免:第三方虛擬環境"), ("b.py", "收容夾 / 凍結來源不改"), ("c.py", "前輪已解耦"), ("d.py", "未帶版號的另一位置副本")]
    g = lamp_of({"lane": "accel", "should": 4, "can": 0, "items": [], "skipped": sk_term}, [])
    y = lamp_of({"lane": "param", "should": 2, "can": 0, "items": [], "skipped": sk_term + [("e.py", "找不到前版")]}, [])
    r = lamp_of({"lane": "net", "should": 1, "can": 1, "items": [1], "skipped": sk_term}, [{"state": "FAIL", "why": "x"}])
    chk("T1 燈:略過全是終態 → 綠 · 有一條非終態 → 黃 · 有 FAIL → 紅", (g, y, r) == ("GREEN", "YELLOW", "RED"), (g, y, r))
    via = P.find_via()
    cv = job_cover(via)
    chk("T2 ④ 加速器生效:叫橋掃描器尾版 --effective(唯讀),回燈與一行摘要", cv.get("lamp") in ("GREEN", "YELLOW", "RED")
        and "PY 生效" in cv.get("line", "") and sweeper(via) is not None, cv)
    keep = G.run
    G.run = lambda *a, **k: subprocess.CompletedProcess(a[0], 1, "第一行\n", "Traceback ...\nValueError: boom\n")
    try:
        msg = job_rg(via)
    finally:
        G.run = keep
    chk("T3 ReworkGuard 沒判決行:附末行(看得出原因)", "沒有判決行" in msg and "ValueError: boom" in msg, msg)
    calls = []
    keep_v, keep_c = globals()["_PREV_VERIFY"], V3.cached
    globals()["_PREV_VERIFY"] = lambda via_, nf: {"編號稽核": "x"}
    V3.cached = lambda via_, name, key, fn: (calls.append(name) or ({"lamp": "RED", "line": "PY 生效 1/1", "not_green": ["NET_MISSING a.py"]}, True))
    try:
        ex = P.verify(via, [])
    finally:
        globals()["_PREV_VERIFY"], V3.cached = keep_v, keep_c
    chk("T4 換裝:P.verify / P.lamp_of / start_initial 都是本版;驗證多「加速器生效」「加速器非綠」兩行",
        P.verify is verify and P.lamp_of is lamp_of and V3.start_initial is start_initial and calls == ["cover"]
        and ex.get("加速器生效", "").startswith("🔴") and ex.get("加速器非綠") == "NET_MISSING a.py", (calls, ex))
    cp = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "selftest"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=1800)
    chk("T5 前版 %s 自測照過(子行程)" % PRIOR_PATH.name, cp.returncode == 0, [x for x in cp.stdout.splitlines() if "FAIL" in x][:3])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T6 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("selftest", "--selftest"):
        return selftest()
    if args and args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return V2.main(args)
    if "--fresh" in args:
        V2.FRESH = True
        args = [a for a in args if a != "--fresh"]
    V2._T0["t"] = time.time()
    if args and args[0] in ("apply", "verify"):
        via = P.find_via()
        started = start_initial(via)
        print(f"[{TAG}] 四個初始流程同步起跑:① 計畫(覆蓋矩陣)" + "".join(f" ∥ {s}" for s in started)
              + ("" if len(started) == 3 else "(其餘沿用上一輪同狀態的結果)"), flush=True)
    try:
        return P.main(args)
    finally:
        V3._POOL.shutdown(wait=True)
        _CPOOL.shutdown(wait=True)


if __name__ == "__main__":
    raise SystemExit(main())

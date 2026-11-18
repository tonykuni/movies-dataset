#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0197 — 薄尾(v0196 一字不動):monitor status(現況顯示掛進既有的 monitor 動詞)

操作員 2026-11-16:「VCGC / VDF / VRN-2 各自在自己的入口加 monitor 動詞,只彙總既有引擎」;2026-11-18:「請你接線」。
VCGC 的 monitor 動詞 v0182 起就在(→ VIA_Panorama:scan · watch · dashboard · lessons · sync · show)。已有同功能就掛動詞,不另做:
本版只在 monitor 底下加一個子動詞 status,其餘(含 monitor 的其他子動詞)一律原樣轉交前版 v0196(子行程 · 參數 / 環境 / rc 不變;只增不減):
  monitor status [--actor <名>] [--no-open] [--no-clip] [--budget N]   跑一輪現況顯示(CGC_MDL283 尾版 run)→ 印燈 · 各系統 · 跟上一輪比 · 主機 · NEXT · 檔案位置
  monitor status --last                                                不跑,只讀上一輪收據 VIA_Reports/vcgc/STATUS_latest.json
  monitor status manifest                                              整合說明(原樣轉交 CGC_MDL283)
  rc:綠 0 · 黃 2 · 紅 1 · 引擎不在 3。這盞燈是現況偵測的彙總,不是任何系統的業務驗收;不是 Windows 主機跑的不算主機實測。
  help 先印前版 help,再補這一行。
對等:monitor 是 VCGC 自己的入口動詞;VDF / VRN-2 的 monitor 各自做,不經 VCGC。不 import 他系統;不設他系統旗標(只補自己的 VIA_FROM_VCGC);
零網路([VIA:NET-BRIDGE] 留名);不碰 TA-Lib;不讀寫同意閘。本檔自己不寫任何檔(輸出由 CGC_MDL283 寫在 VIA_Reports/vcgc)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版兩扇門都不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====

import datetime as _dt
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0197"
FAMILY = "CGC_MDL149_VeritasCentralGovernanceConsole"
TAG = FAMILY + " " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
OWN_FLAG = "VIA_FROM_VCGC"
ENG_STEM = "CGC_MDL283_CardMatrixFeedback"
RC = {"GREEN": 0, "YELLOW": 2, "RED": 1}
ZH = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "g": "綠", "y": "黃", "r": "紅", "x": "灰"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path():
    cands = [p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    return max(cands, key=_vnum) if cands else None


def _tail(d: Path, stem: str):
    hits = [p for p in d.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _env() -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.setdefault(OWN_FLAG, "YES")                     # 只補本系統自己的入口旗標
    return env


def _call(path, args: list) -> int:
    if path is None:
        print("[%s] ABSENT · 要轉交的檔不在(動詞 %s)" % (TAG, args[:1]))
        return 3
    return subprocess.run([sys.executable, str(path), *args], env=_env()).returncode


def forward(args: list) -> int:
    """前版其餘功能原樣轉交 v0196(子行程 · rc 不變)。"""
    return _call(_prior_path(), args)


_PRIOR = None


def _prior_module():
    global _PRIOR
    if _PRIOR is None:
        pp = _prior_path()
        if pp is None:
            raise AttributeError("前版不在")
        spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, pp)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _PRIOR = mod
    return _PRIOR


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(要用才載)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_prior_module(), name)


def _out_dir(args: list) -> Path:
    if "--out" in args and args.index("--out") + 1 < len(args):
        return Path(args[args.index("--out") + 1])
    return VIA / "VIA_Reports" / "vcgc"


def summarize(out: Path, ran: bool, t0=None) -> int:
    """讀現況顯示的收據,印成幾行;回 rc。收據不在或這一輪沒更新都照實說。"""
    p = out / "STATUS_latest.json"
    if not p.is_file():
        print("[現況] 灰 · 還沒有收據(先跑 monitor status)")
        return 2
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        print("[現況] 紅 · 收據讀不懂:%s" % p)
        return 1
    lamp = str(rec.get("lamp") or "")
    stale = False
    if ran and t0 is not None:
        try:
            at = _dt.datetime.fromisoformat(str(rec.get("at") or "").replace("Z", "+00:00"))
            stale = at < t0 - _dt.timedelta(seconds=2)
        except ValueError:
            stale = True
    print("[現況] %s · %s%s" % (ZH.get(lamp, "灰"), rec.get("summary") or "收據沒有摘要", "" if ran else " · 上一輪 %s" % (rec.get("at") or "時間不明")))
    sysl = rec.get("systems") or {}
    if sysl:
        print("[系統] " + " · ".join("%s %s %s" % (k, ZH.get(v.get("lamp"), "灰"), v.get("n")) for k, v in sysl.items()) + "(要處理的項數)")
    d = out / "FEEDBACK_DELTA_latest.txt"
    if d.is_file():
        line = next((x for x in d.read_text(encoding="utf-8").splitlines() if x.startswith("[這一輪跟上一輪比]")), "")
        if line:
            print(line.replace("[這一輪跟上一輪比]", "[更新]"))
    h = rec.get("host") or {}
    print("[主機] %s" % ("Windows 主機實跑" if h.get("counts_as_host_run") else "%s%s:這一輪的綠不算主機實測" % (h.get("system") or "不明", "(容器)" if h.get("container") else "")))
    gaps = rec.get("gaps") or []
    if gaps:
        print("[沒管到] " + "、".join(gaps))
    if rec.get("ok") is False:
        print("[對帳] 不符:" + "、".join(k for k, v in (rec.get("checks") or {}).items() if not v))
    print("[頁面] %s" % (out / "WORKPLATFORM_latest.html"))
    print("[回饋] %s(給動作主力;每次先讀這份)" % d)
    print("NEXT: %s" % (rec.get("next") or "收據沒有下一步"))
    if stale:
        print("[紅] 這一輪跑完但收據沒有更新(時間比開跑還早),上面是舊的")
        return 1
    return RC.get(lamp, 2)


def monitor_status(args: list) -> int:
    eng = _tail(HERE, ENG_STEM)
    if args and args[0] == "manifest":
        return _call(eng, ["manifest"])
    last = "--last" in args
    args = [a for a in args if a != "--last"]
    out = _out_dir(args)
    if last:
        return summarize(out, False)
    if eng is None:
        print("[%s] ABSENT · 現況顯示引擎 %s 不在" % (TAG, ENG_STEM))
        return 3
    print("[%s] monitor status:現況偵測中(第一次或大改之後較久)…" % TAG, flush=True)
    t0 = _dt.datetime.now(_dt.timezone.utc)
    env = dict(_env(), PYTHONIOENCODING="utf-8", PYTHONUTF8="1")   # 引擎的輸出收進管線,不靠主控台的編碼
    cp = subprocess.run([sys.executable, str(eng), "run", *args], env=env, capture_output=True)
    if cp.returncode not in (0, 1, 2):
        tail = (cp.stdout + cp.stderr).decode("utf-8", "replace").strip().splitlines()[-6:]
        print("[紅] 現況顯示引擎沒跑完(rc %d):" % cp.returncode)
        for line in tail:
            print("  " + line)
        return cp.returncode or 1
    for line in cp.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith(("[剪貼簿]", "[沿用]", "[U/I] 開不起來")):
            print(line)
    return summarize(out, True, t0)


def help_extra() -> None:
    print("  ── v0197 接線(現況顯示;VCGC 自己的入口動詞,VDF / VRN-2 各自做)──")
    print("  monitor status [--actor claude|chatgpt] [--no-open] [--no-clip]   跑一輪現況顯示 → 燈 · 各系統 · 跟上一輪比 · NEXT · 頁面位置(rc 綠 0 · 黃 2 · 紅 1)")
    print("  monitor status --last | monitor status manifest                   只讀上一輪收據 | 整合說明;monitor 的其他子動詞照舊(VIA_Panorama)")


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測(薄尾 · monitor status 一個子動詞 + 原樣轉交)===" % TAG, flush=True)
    pp = _prior_path()
    chk("① 前版 v0196 在且是本家族上一版", pp is not None and _vnum(pp) == _vnum(__file__) - 1, pp.name if pp else None)
    cp = subprocess.run([sys.executable, str(pp), "version"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    chk("② 其餘動詞原樣轉交(version → 前版鏈 rc 0)", cp.returncode == 0, (cp.stdout.strip().splitlines() or ["?"])[-1][:80])
    eng = _tail(HERE, ENG_STEM)
    chk("③ monitor status 的正主 CGC_MDL283 在", eng is not None, eng.name if eng else None)
    cp = subprocess.run([sys.executable, str(eng), "manifest"], env=dict(_env(), PYTHONIOENCODING="utf-8", PYTHONUTF8="1"), capture_output=True, timeout=300)
    man = {}
    try:
        man = json.loads(cp.stdout.decode("utf-8", "replace"))
    except ValueError:
        man = {}
    chk("④ monitor status manifest 轉交得到整合說明(有 python_api 與收據欄位)", cp.returncode == 0 and "python_api" in man and "lamp" in (man.get("receipt_fields") or []))
    with tempfile.TemporaryDirectory(prefix="via_console197_") as td:
        out = Path(td)
        chk("⑤ 沒有收據:照實說還沒有,rc 2(不當成綠)", summarize(out, False) == 2)
        now = _dt.datetime.now(_dt.timezone.utc)
        rec = {"lamp": "RED", "summary": "真紅 3", "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "next": "先處理真紅", "ok": True, "gaps": ["資料內容品質"],
               "systems": {"VCGC": {"lamp": "r", "n": 2}, "VDF": {"lamp": "g", "n": 0}}, "host": {"system": "Linux", "container": True, "counts_as_host_run": False}}
        (out / "STATUS_latest.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
        (out / "FEEDBACK_DELTA_latest.txt").write_text("# x\n[這一輪跟上一輪比] 修好 1 · 新增問題 0\n", encoding="utf-8")
        chk("⑥ 紅收據 → rc 1;綠 0;黃 2(燈照收據,不自己判)", summarize(out, False) == 1)
        for lamp, want in (("GREEN", 0), ("YELLOW", 2)):
            rec["lamp"] = lamp
            (out / "STATUS_latest.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
            ok.append(summarize(out, False) == want)
        chk("⑦ 三種燈的 rc 都對", ok[-2] and ok[-1])
        rec["at"] = (now - _dt.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        (out / "STATUS_latest.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
        chk("⑧ 跑完但收據沒更新 → 紅(不拿舊收據充數)", summarize(out, True, now) == 1)
        (out / "STATUS_latest.json").write_text("壞掉", encoding="utf-8")
        chk("⑨ 收據讀不懂 → 紅", summarize(out, False) == 1)
        seen = []
        real = globals()["forward"]
        globals()["forward"] = lambda a: seen.append(list(a)) or 0
        try:
            r1 = main(["monitor", "lessons", "--x"])
            r2 = main(["monitor"])
            r3 = main(["monitor", "status", "--last", "--out", str(out / "none")])
        finally:
            globals()["forward"] = real
        chk("⑩ monitor 的既有子動詞原樣轉交前版(lessons · 空參數),只有 status 留在本版", seen == [["monitor", "lessons", "--x"], ["monitor"]] and r1 == 0 and r2 == 0, seen)
        chk("⑩b monitor status --last --out <空夾> 走只讀路徑,不啟動引擎、不轉交", r3 == 2)
    names = [n for n in dir(_prior_module()) if not n.startswith("_") and callable(getattr(_prior_module(), n, None))]
    chk("⑪ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), "%d 支" % len(names))
    env = _env()
    chk("⑫ 只補自己的旗標(不設 VDF / VRN 旗標)", env.get(OWN_FLAG) and not any(k in env and k not in os.environ for k in ("VIA_FROM_VDFSM", "VIA_FROM_VRN")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑬ 零網路 · 不用 TA-Lib · 不 import 他系統 · 不寫同意閘 · 本檔不寫檔",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|VDF_|VRN_|VIA_AgentOS)", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and ".write_text(" not in src.split("def selftest")[0])
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--selftest", "selftest") and "--legacy" not in args:
        return selftest()
    if args[:2] == ["monitor", "status"]:
        return monitor_status(args[2:])
    if not args or args[0] == "help":
        rc = forward(args or ["help"])
        help_extra()
        return rc
    return forward([a for a in args if a != "--legacy"] if args[0] in ("selftest", "--selftest") else args)


if __name__ == "__main__":
    sys.exit(main())

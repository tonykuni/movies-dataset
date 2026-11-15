#!/usr/bin/env python3
r"""VDF_MDL013_ActivateVDF v0119 — 薄尾:本輪鉤載工具時生的子行程不再掛工具(斷 py-cpuinfo 無限遞迴)· 載入看門狗 · 前版鏈不再當機

工作站實跑(2026-11-15 · C:\Python313 單跑 v0115 自測,以及 2026-11-14 engine_launch 內 via_vdf_312 境):
v0115 自測 ⑥ 的子行程(只掛本輪鉤 · 不掛中央啟動鉤)每次 180 秒逾時 → subprocess.TimeoutExpired 沒接 → 整條前版鏈當機
(ActivateVDF v0117 / v0118 自測 RED 的就是這一條)。容器同一條 0.2 秒過。
根因(程式碼 + 容器重現;三段都查得到原文):
  ① 本輪鉤在每支子行程起跑時「立即」載加速器 VeritasCeleritas_v1141(鎖冊);它 import 時就跑 cross_init()
     (L5571 ENABLE_AUTO_CROSS_INIT)→ HardwareTuner.optimize → get_system_info → detect_simd → cpuinfo.get_cpu_info()。
  ② py-cpuinfo 9.0.0 的 get_cpu_info_json():`Popen([sys.executable, __file__, '--json'])`(環境原樣繼承)——再起一支 python。
  ③ 那支 python 帶著同一個 PYTHONPATH → 又跑本輪鉤 → 又立即載加速器 → 又 cross_init → 又起一支 …… 無限遞迴,
     每一層都在等下一層;逾時只殺得掉第一支,後面的變孤兒行程(吃記憶體)。
  容器沒裝 py-cpuinfo 所以不發作;本版自測用「有深度上限的 cpuinfo 替身」重現:前版鉤一路遞迴到上限,本版鉤只到第 1 層。
  平常的一輪(engine_launch)沒發作,是因為工作站的中央啟動鉤先把兩個工具掛成惰性代理(本輪鉤看到已在 sys.modules →
  0.003 秒略過 · 收據「平均載入 0.003 秒」即此);只有不帶中央啟動鉤的子行程(如 v0115 ⑥)才會走到立即載入。
本版(v0100 … v0118 一字不動;只在本版的一輪 / 本版自測裡生效):
  ① 本輪鉤載工具的期間(立即載的加速器 · 網路工具第一次用到才真正執行的那段)環境多一個標記 VIA_VDF_TOOLS_LOADING=<母行程 pid>;
     期間生的子行程(py-cpuinfo 的 python · 它在 Windows 再 spawn 的 cpuid 行程 …)看到標記 → 不掛工具、不進記憶體准入閘排隊
     (母行程正等它回來),只在 tools_helpers.jsonl 記一行輔助收據(另檔,工具收據照舊一支一行)。載完標記即撤,之後生的子行程照常掛。
  ② 載入看門狗(只在設了 VIA_VDF_HOOK_WATCHDOG_S + _FILE 時):鉤卡住就把各執行緒堆疊寫進檔後結束 —— 下次再卡,看得到卡在哪一行。
  ③ 前版鏈:v0115 自測跑的那段期間,它的 HOOK_SRC_V0115 換成「v0115 鉤 + ①」(其餘一字不差),v0115 的檢查照原樣判;
     v0117 / v0118 比對鉤原文的檢查看的是它們自己的原文,不受影響。
  ④ 一輪收尾多印一行「[加速] 載工具時生的輔助子行程 N 支(不掛工具 · 防遞迴)」。
其餘全照 v0118。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件;不寫環境(只寫子行程 env)。
用法同前(ActivateVDF.py run …;本檔是尾版就用本版)· 自測 python VDF_MDL013_ActivateVDF_v0119.py --selftest(本版 + 前版鏈)。
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
import json
import os
import re
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0119(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0119(p) < _vnum_v0119(__file__)), key=_vnum_v0119)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100, V0115 = PRIOR.V0100, PRIOR.V0115
V0117 = PRIOR.PRIOR
V0116 = V0117.PRIOR


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


MARK = "VIA_VDF_TOOLS_LOADING"
HELPERS_NAME = "tools_helpers.jsonl"

GUARD_DEFS_V0119 = r'''

_VDF_MARK = "VIA_VDF_TOOLS_LOADING"


def _vdf_helper_note(parent):
    # v0119:本行程是「別的行程正在載工具」時生的輔助行程(加速器 import → cross_init → py-cpuinfo 用 sys.executable 再起一支 …)。
    # 不掛工具(否則它又載加速器 → 又起一支 → 無限遞迴)。只記一行輔助收據(另檔,不混進工具收據)。
    log = os.environ.get("VIA_VDF_TOOLS_LOG")
    if not log:
        return
    try:
        import json
        argv = [str(a) for a in (getattr(sys, "orig_argv", None) or getattr(sys, "argv", None) or [])]
        rec = {"pid": os.getpid(), "parent": parent, "argv": " ".join(os.path.basename(a) for a in argv[1:3])[-160:], "tag": _TAG}
        with open(os.path.join(os.path.dirname(log), "tools_helpers.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — 收據寫不進不連累本行程
        pass


class _VdfMarkLoader:
    # v0119:網路工具 LazyLoader 第一次用到才真正執行 —— 執行的那段期間同樣標「正在載工具」(期間生的子行程不再掛工具)。
    def __init__(self, inner):
        self._inner = inner

    def create_module(self, spec):
        return self._inner.create_module(spec)

    def exec_module(self, module):
        had = os.environ.get(_VDF_MARK)
        os.environ[_VDF_MARK] = str(os.getpid())
        try:
            self._inner.exec_module(module)
        finally:
            if had is None:
                os.environ.pop(_VDF_MARK, None)
            else:
                os.environ[_VDF_MARK] = had

    def __getattr__(self, name):
        return getattr(self._inner, name)


_VDF_WD = []


def _vdf_watchdog(on):
    # v0119:載入看門狗(只在設了 VIA_VDF_HOOK_WATCHDOG_S + VIA_VDF_HOOK_WATCHDOG_FILE 時):卡住就把各執行緒堆疊寫進檔後結束。
    try:
        import faulthandler
        if not on:
            if _VDF_WD:
                faulthandler.cancel_dump_traceback_later()
            return
        s = float(os.environ.get("VIA_VDF_HOOK_WATCHDOG_S") or 0)
        f = os.environ.get("VIA_VDF_HOOK_WATCHDOG_FILE")
        if s > 0 and f:
            _VDF_WD.append(open(f, "a", encoding="utf-8"))
            faulthandler.dump_traceback_later(s, exit=True, file=_VDF_WD[-1])
    except Exception:  # noqa: BLE001
        pass'''

TOOLS_EDITS_V0119 = (
    ("    sys._vdf_tools_tag = _TAG\n",
     "    sys._vdf_tools_tag = _TAG\n"
     "    if os.environ.get(_VDF_MARK):                    # v0119:別的行程正在載工具時生的輔助行程 → 不掛工具(防遞迴)\n"
     "        _vdf_helper_note(os.environ.get(_VDF_MARK))\n"
     "        return\n"),
    ("                spec.loader = importlib.util.LazyLoader(spec.loader)\n",
     "                spec.loader = importlib.util.LazyLoader(_VdfMarkLoader(spec.loader))\n"),
    ("            spec.loader.exec_module(m)\n",
     "            os.environ[_VDF_MARK] = str(os.getpid())   # v0119:載的期間生的子行程看得到「正在載工具」\n"
     "            spec.loader.exec_module(m)\n"),
    ("        finally:\n            changed = [k for k in set(os.environ) | set(keep) if os.environ.get(k) != keep.get(k)]\n",
     "        finally:\n            os.environ.pop(_VDF_MARK, None)\n"
     "            changed = [k for k in set(os.environ) | set(keep) if os.environ.get(k) != keep.get(k)]\n"),
    ("try:\n    _vdf_tools()\nexcept Exception:  # noqa: BLE001\n    pass\n",
     "try:\n    _vdf_watchdog(True)\n    _vdf_tools()\nexcept Exception:  # noqa: BLE001\n    pass\nfinally:\n    _vdf_watchdog(False)\n"),
)
GATE_EDIT_V0119 = (
    '    if floor > 0 and not boss and os.environ.get("VIA_VDF_MEM_ADMIT", "1") != "0":\n',
    '    helper = os.environ.get("VIA_VDF_TOOLS_LOADING")   # v0119:載工具時生的輔助行程不排隊(母行程正等它回來)\n'
    '    if helper:\n'
    '        rec["helper"] = helper\n'
    '    if floor > 0 and not boss and not helper and os.environ.get("VIA_VDF_MEM_ADMIT", "1") != "0":\n',
)
ANCHOR_TOOLS = "\n\ndef _vdf_tools():"


def guard_tools(src: str) -> str:
    """鉤原文 → 多 ① 標記 / 輔助行程略過 + ② 看門狗;每個接點必須恰好一處,對不上就報錯(不猜)。"""
    if src.count(ANCHOR_TOOLS) != 1:
        raise RuntimeError("鉤原文對不上接點(def _vdf_tools)")
    out = src.replace(ANCHOR_TOOLS, GUARD_DEFS_V0119 + ANCHOR_TOOLS, 1)
    for old, new in TOOLS_EDITS_V0119:
        if out.count(old) != 1:
            raise RuntimeError("鉤原文對不上接點:%r" % old[:60])
        out = out.replace(old, new, 1)
    return out


def guard_gate(src: str) -> str:
    old, new = GATE_EDIT_V0119
    if src.count(old) != 1:
        raise RuntimeError("准入閘原文對不上接點")
    return src.replace(old, new, 1)


def unguard(src: str) -> str:
    """反向還原(自測用):拿掉本版加的每一段 → 應與前版原文一字不差。"""
    out = src.replace(GATE_EDIT_V0119[1], GATE_EDIT_V0119[0], 1)
    for old, new in TOOLS_EDITS_V0119:
        out = out.replace(new, old, 1)
    return out.replace(GUARD_DEFS_V0119 + ANCHOR_TOOLS, ANCHOR_TOOLS, 1)


HOOK_SRC_V0118_PRIOR = PRIOR.HOOK_SRC_V0118
HOOK_SRC_V0115_RAW = V0117._ORIG["HOOK_SRC_V0115"]
HOOK_SRC_V0119 = guard_gate(guard_tools(HOOK_SRC_V0118_PRIOR))
HOOK_SRC_V0115_GUARDED = guard_tools(HOOK_SRC_V0115_RAW)
_V0114_G = PRIOR._V0114_G
_ACTIVATE_V0118 = PRIOR.activate


def _rows(p: Path, bad: list | None = None) -> list:
    """一行一筆 JSON 的收據檔 → 列;壞行不丟例外、計進 bad(照實回報)。"""
    out = []
    if Path(p).is_file():
        for ln in Path(p).read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError as exc:
                if bad is not None:
                    bad.append("%s: %s" % (type(exc).__name__, ln[:60]))
    return out


def helpers_summary(temp_run) -> dict:
    out = {"n": 0, "parents": 0, "examples": [], "bad": []}
    if not temp_run:
        return out
    rows = _rows(Path(temp_run) / HELPERS_NAME, out["bad"])
    out["n"] = len(rows)
    out["parents"] = len({r.get("parent") for r in rows})
    out["examples"] = sorted({r.get("argv") or "—" for r in rows})[:3]
    return out


def helpers_line(h: dict) -> str:
    return ("[加速] 載工具時生的輔助子行程 %d 支(母行程 %d 支 · 不掛工具 · 防遞迴)%s%s"
            % (h["n"], h["parents"], (" · 例 " + " / ".join(h["examples"])) if h["examples"] else "",
               (" · 收據壞行 %d" % len(h["bad"])) if h.get("bad") else ""))


@contextmanager
def _deploy_v0119():
    """一輪期間:v0118 activate 寫出的本輪鉤 = 本版鉤;總覽標本版。結束還原(前版自測看它自己的狀態)。"""
    keep = (PRIOR.HOOK_SRC_V0118, PRIOR.TAG)
    PRIOR.HOOK_SRC_V0118, PRIOR.TAG = HOOK_SRC_V0119, TAG
    try:
        yield
    finally:
        PRIOR.HOOK_SRC_V0118, PRIOR.TAG = keep


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0118 activate;本輪鉤 = v0119(載工具時生的子行程不再掛工具);收尾多印輔助子行程一行。"""
    with _deploy_v0119():
        card = _ACTIVATE_V0118(opt, manager, py, temp)
    h = helpers_summary(V0115._RUN15.get("temp_run"))
    print("  " + helpers_line(h), flush=True)
    if isinstance(card, dict):
        card["tools_helpers"] = h
    return card


def _patch_v0119() -> None:
    _V0114_G["activate"] = activate


def _unpatch_v0119() -> None:
    _V0114_G["activate"] = _ACTIVATE_V0118


_patch_v0119()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    V0116._patch_v0116()
    V0117._patch_v0117()
    PRIOR._patch_v0118()
    _patch_v0119()
    return V0115.main(argv)


# ---------------------------------------------------------------- 自測(沙盒 · 零網路)
STUB_INIT = "from cpuinfo.cpuinfo import get_cpu_info  # noqa: F401\n"
STUB_SRC = r'''# py-cpuinfo 9.0.0 get_cpu_info() 的最小替身:用 sys.executable 再跑本檔(環境原樣繼承)—— 只多一個深度上限(自測不能真的無限遞迴)。
import json, os, sys, time
def get_cpu_info():
    depth = int(os.environ.get("VDF_STUB_CPUINFO_DEPTH", "0"))
    log = os.environ.get("VDF_STUB_CPUINFO_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"pid": os.getpid(), "depth": depth, "mark": os.environ.get("VIA_VDF_TOOLS_LOADING"),
                                 "tools": "VeritasCeleritas" in sys.modules}) + "\n")
    if depth >= int(os.environ.get("VDF_STUB_CPUINFO_CAP", "4")):
        return {"flags": []}
    from subprocess import Popen, PIPE
    env = dict(os.environ, VDF_STUB_CPUINFO_DEPTH=str(depth + 1))
    p = Popen([sys.executable, __file__, "--json"], stdout=PIPE, stderr=PIPE, stdin=PIPE, env=env)
    out = p.communicate()[0]
    try:
        return json.loads(out.decode("utf-8", "replace") or "{}")
    except ValueError:
        return {}
if __name__ == "__main__":
    print(json.dumps({"flags": ["sse2"]}))
'''


def selftest() -> int:
    import shutil
    import subprocess
    import tempfile
    import time
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:400]) if note else ""))

    print("=== %s · 薄尾自測(載工具時生的子行程不再掛工具 · 看門狗 · 前版鏈;沙盒 · 零網路)===" % TAG)
    try:
        compile(HOOK_SRC_V0119, "sitecustomize.py", "exec")
        compile(HOOK_SRC_V0115_GUARDED, "sitecustomize.py", "exec")
        ok_c = True
    except SyntaxError as exc:
        ok_c = exc
    chk("① 本版鉤 / v0115 守門鉤可編譯 · 拿掉本版加的段落 = v0118 鉤 / v0115 鉤原文一字不差 · 標籤照舊",
        ok_c is True and unguard(HOOK_SRC_V0119) == HOOK_SRC_V0118_PRIOR and unguard(HOOK_SRC_V0115_GUARDED) == HOOK_SRC_V0115_RAW
        and HOOK_SRC_V0119.count(MARK) == 2 and HOOK_SRC_V0119.count("_VDF_MARK") >= 6 and '_TAG = "vdf-activate-v0115"' in HOOK_SRC_V0119, ok_c)
    has_cpuinfo = importlib.util.find_spec("cpuinfo") is not None
    print("  [資訊] 本機 %s:py-cpuinfo %s(加速器 import 時 cross_init → detect_simd 會叫它;它用 sys.executable 再起一支 python)"
          % (sys.executable, "有 → 前版鉤在不帶中央啟動鉤的子行程會無限遞迴" if has_cpuinfo else "沒有 → 前版鉤在本機不發作"))
    tmp = Path(tempfile.mkdtemp(prefix="vdf_act0119_"))
    try:
        stub = tmp / "stub"
        (stub / "cpuinfo").mkdir(parents=True)
        (stub / "cpuinfo" / "__init__.py").write_text(STUB_INIT, encoding="utf-8")
        (stub / "cpuinfo" / "cpuinfo.py").write_text(STUB_SRC, encoding="utf-8")
        t = V0115.tools_resolve()

        def run_child(ver, src, code, extra=None, timeout=170):
            d = tmp / ver
            hd = d / "pyhook"
            hd.mkdir(parents=True)
            (hd / "sitecustomize.py").write_text(src, encoding="utf-8")
            res = {"temp_run": str(d)}
            base = {k: v for k, v in os.environ.items() if not k.startswith(("VIA_VDF_", "VIA_DUCK", "VDF_STUB_")) and k != "PYTHONPATH"}
            env = dict(base, PYTHONPATH=os.pathsep.join([str(hd), str(stub)]), PYTHONIOENCODING="utf-8", VIA_DUCK_TEMP="0",
                       VIA_VDF_MEM_ADMIT="0", VDF_STUB_CPUINFO_LOG=str(d / "cpuinfo_calls.jsonl"), VDF_STUB_CPUINFO_CAP="4",
                       VIA_VDF_HOOK_WATCHDOG_S="150", VIA_VDF_HOOK_WATCHDOG_FILE=str(d / "watchdog.txt"), **V0115.tools_env(res, t))
            env.update(extra or {})
            t0 = time.time()
            try:
                cp = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=timeout)
                out, err, rc = cp.stdout, cp.stderr, cp.returncode
            except subprocess.TimeoutExpired as exc:   # 不再丟 traceback:照實回逾時 + 看門狗堆疊
                out, err, rc = (exc.stdout or ""), (exc.stderr or ""), "TIMEOUT"
                out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
                err = err.decode("utf-8", "replace") if isinstance(err, bytes) else err
            got = json.loads(next((ln[5:] for ln in (out or "").splitlines() if ln.startswith("VDFT ")), "{}"))
            wd = (d / "watchdog.txt").read_text(encoding="utf-8", errors="replace") if (d / "watchdog.txt").is_file() else ""
            return {"rc": rc, "secs": round(time.time() - t0, 2), "got": got, "err": (err or "")[-300:], "wd": wd[:1500],
                    "calls": _rows(d / "cpuinfo_calls.jsonl"), "tools": _rows(d / "tools_receipts.jsonl"), "helpers": _rows(d / HELPERS_NAME)}

        code_a = "import os,sys,json;print('VDFT '+json.dumps({'a':'VeritasCeleritas' in sys.modules}))"
        ra = run_child("v0118", HOOK_SRC_V0118_PRIOR, code_a)
        da = max([c["depth"] for c in ra["calls"]] or [-1])
        chk("② 重現工作站:前版鉤 + 會再起 python 的 cpuinfo(替身,上限 4 層)→ 一路遞迴到上限(每層都又載一次加速器)· %.1f 秒 · 深度 %d"
            % (ra["secs"], da), ra["rc"] == 0 and da == 4 and len(ra["calls"]) == 5 and all(c["tools"] for c in ra["calls"]),
            {k: ra[k] for k in ("rc", "calls", "err", "wd")})
        code_b = ("import faulthandler,os,sys,json;faulthandler.dump_traceback_later(150,exit=True);"
                  "pre={'pandas':'pandas' in sys.modules};n=sys.modules.get('VeritasAegisNexus');k=len(dir(n)) if n is not None else 0;"
                  "print('VDFT '+json.dumps(dict(pre,a='VeritasCeleritas' in sys.modules,k=k,mark=os.environ.get('" + MARK + "'),"
                  "tag=getattr(sys,'_vdf_tools_tag',None))))")
        rb = run_child("v0119", HOOK_SRC_V0119, code_b)
        db = max([c["depth"] for c in rb["calls"]] or [-1])
        g = rb["got"]
        chk("③ 本版鉤:同一個 cpuinfo 只起 1 支輔助行程就停 —— 它看到「正在載工具」(母 pid)→ 不掛工具、不再叫 cpuinfo · 輔助收據 1 行 · %.1f 秒"
            % rb["secs"], rb["rc"] == 0 and db == 0 and len(rb["calls"]) == 1 and rb["calls"][0]["mark"] == str(rb["calls"][0]["pid"])
            and len(rb["helpers"]) == 1 and rb["helpers"][0]["parent"] == rb["calls"][0]["mark"] and "cpuinfo.py" in rb["helpers"][0]["argv"],
            {k: rb[k] for k in ("rc", "calls", "helpers", "err", "wd")})
        chk("④ 本版鉤照樣掛好工具:加速器已載 · 網路工具用到後 %s 個名字 · 起跑沒帶進 pandas · 載完標記已撤 · 工具收據 1 行(輔助行程不混進來)"
            % g.get("k"), g.get("a") is True and (g.get("k") or 0) > 10 and g.get("pandas") is False and g.get("mark") is None
            and g.get("tag") and len(rb["tools"]) == 1 and rb["tools"][0].get("net_mode") == "lazy",
            (g, rb["tools"]))
        eng = tmp / "VDF_ENG998_Big_v0100.py"
        eng.write_text("print('VDFT {}')\n", encoding="utf-8")
        waits = {}
        for name, extra in (("helper", {MARK: "4242"}), ("normal", {})):
            d = tmp / ("gate_" + name)
            hd = d / "pyhook"
            hd.mkdir(parents=True)
            (hd / "sitecustomize.py").write_text(HOOK_SRC_V0119, encoding="utf-8")
            base = {k: v for k, v in os.environ.items() if not k.startswith(("VIA_VDF_", "VIA_DUCK", "VDF_STUB_")) and k != "PYTHONPATH"}
            env = dict(base, PYTHONPATH=str(hd), PYTHONIOENCODING="utf-8", VIA_VDF_TOOLS="0", VIA_DUCK_TEMP="0", VIA_VDF_MEM_LOG=str(d / "mem.jsonl"),
                       VIA_VDF_MEM_FLOOR_MB=str(10 ** 9), VIA_VDF_MEM_ADMIT_MAX_S="1.2", **extra)
            subprocess.run([sys.executable, "-X", "utf8", str(eng), "--selftest"], env=env, capture_output=True, text=True, timeout=60)
            waits[name] = _rows(d / "mem.jsonl")
        wh, wn = waits["helper"], waits["normal"]
        chk("⑤ 准入閘:輔助行程(帶標記)不排隊、收據記 helper;沒標記的引擎自測照 v0118 排隊",
            len(wh) == 1 and wh[0].get("helper") == "4242" and wh[0]["wait_s"] < 0.6 and len(wn) == 1 and wn[0]["wait_s"] >= 1.0
            and "helper" not in wn[0], (wh, wn))
        slow = tmp / "VeritasCeleritas_slow.py"
        slow.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
        re_ = run_child("watchdog", HOOK_SRC_V0119, code_a, {"VIA_VDF_ACCEL_PATH": str(slow), "VIA_VDF_HOOK_WATCHDOG_S": "2"}, timeout=50)
        chk("⑥ 看門狗:鉤載工具卡住(加速器替身睡 60 秒)→ %.1f 秒內結束 · 堆疊檔寫出卡在 _vdf_tools(不再只剩 TimeoutExpired)" % re_["secs"],
            re_["rc"] not in (0, "TIMEOUT") and re_["secs"] < 30 and "_vdf_tools" in re_["wd"] and "VeritasCeleritas_slow" in re_["wd"],
            {k: re_[k] for k in ("rc", "secs", "wd", "err")})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    with _deploy_v0119():
        inside = (PRIOR.activate.__globals__["HOOK_SRC_V0118"] is HOOK_SRC_V0119, PRIOR.activate.__globals__["TAG"] == TAG)
    after = (PRIOR.HOOK_SRC_V0118 is HOOK_SRC_V0118_PRIOR, PRIOR.TAG != TAG)
    chk("⑦ 換裝只在一輪裡:一輪期間 v0118 activate 寫出的本輪鉤 = 本版鉤 · 總覽標本版;結束還原 · main 叫的 activate = 本版",
        all(inside) and all(after) and _V0114_G["activate"] is activate, (inside, after))
    h = helpers_summary(None)
    chk("⑧ 收尾一行:" + helpers_line({"n": 2, "parents": 1, "examples": ["cpuinfo.py --json"]}), h == {"n": 0, "parents": 0, "examples": [], "bad": []})
    me = Path(__file__).read_text(encoding="utf-8")
    body = me.split("def selftest", 1)[0]
    chk("⑨ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 同意閘不讀不寫 · 不碰 TA-Lib · 不寫本行程環境",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|talib)", me, re.M) and "VIA:ACCEL-BRIDGE" in me and "VIA:NET-BRIDGE" in me
        and "_CON" + "SENT" not in body and "os.environ[" not in body.split("GUARD_DEFS_V0119", 1)[0])
    if f:
        print("[計] %s 自測 %d/%d · FAIL" % (TAG, p, p + f))
        return 1
    print("[計] %s 本版 %d/%d · PASS" % (TAG, p, p + f))
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    print("[計] 前版鏈:v0115 自測那段期間用「v0115 鉤 + 本版防遞迴」(其餘一字不差;v0115 原鉤在裝了 py-cpuinfo 的機器上會無限起子行程)")
    st115 = V0115.selftest

    def _st115_guarded():
        keep = V0115.HOOK_SRC_V0115
        V0115.HOOK_SRC_V0115 = HOOK_SRC_V0115_GUARDED
        try:
            return st115()
        finally:
            V0115.HOOK_SRC_V0115 = keep

    _unpatch_v0119()
    V0115.selftest = _st115_guarded
    try:
        rc1 = PRIOR.selftest()
    finally:
        V0115.selftest = st115
        _patch_v0119()
    print("[計] %s 前版鏈 rc %s · %s" % (TAG, rc1, "PASS" if rc1 == 0 else "FAIL"))
    return rc1 if rc1 in (0, 1, 2, 3) else 1


if __name__ == "__main__":
    raise SystemExit(main())

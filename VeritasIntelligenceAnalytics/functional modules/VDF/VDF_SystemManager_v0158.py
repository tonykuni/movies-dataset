#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0158 — 薄尾:前版鏈自測的凍結樣本冊(解 ENG056 升版即紅;TAILAPI 第二輪延後項)

操作員令(2026-10-20):「好,做 ENG056,測完開PR合併  儘快將VDF收尾」。
病因(PR #541 CI 實錄):已發佈的 v0150 自測 ⑤ / ⑥a 用一張寫死 ENG056 v0106 路徑的樣本卡跑 engine matrix;
  launch_paths 只認引擎冊(VCGC 檢視本體 MDL253 依檔案現況算出的各家族尾版)。ENG056 一出 v0107,冊上就只有 v0107,
  樣本路徑變「不在引擎冊」→ ⑤ 可啟動 = 否 → 整條管理員自測紅。已發佈檔不改、測試不跳。
本版(正式動詞行為一字不改,全部轉給前版鏈):
  ① SampleBook:包住冊檢視,VDF 冊上照舊是尾版那一列,另補「凍結樣本路徑」一列(只補冊上已有的家族 · 檔真的在 ·
     冊上還沒有的;拷同家族尾版那列,只換 path / version)。不猜:冊上沒有的家族、檔不在都不補。
  ② scoped_prior_selftest:只在 v0150 自己那一層的自測期間換冊(v0150 的 launch_paths 走 v0149._inv);
     v0150 呼叫的 v0149 自測與其他各層都看原冊;結束(含例外)全部還原。
  ③ 自測:本版 6 項(樣本冊 · 不猜 · 只換一層 · 例外還原 · 真鏈找得到 · 治理),過了再跑前版鏈自測(經 ②)。
VDF 自己的模組:不改 VCGC 的 MDL253(只在本行程包一層);不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====



import json
import os
import re
import sys
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "VDF_SystemManager"
TAG = "v0158"
SELF_ID = "VDF"
# v0150 自測 ⑤ / ⑥a 的凍結樣本卡(已發佈檔不改):路徑 → 家族
FROZEN_SAMPLES_V0150 = {"functional modules/VDF/engine/VDF_ENG056_ChipBackfill_v0106.py": "VDF_ENG056_ChipBackfill"}


def _vnum_v0158(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0158(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0158(p) < _vnum_v0158(__file__)), key=_vnum_v0158)
PRIOR = _load_v0158(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


# ---------------------------------------------------------------- 只給前版鏈自測用的樣本冊(正式動詞不經過這裡)
class SampleBook:
    """包住引擎冊檢視(VCGC 的 MDL253 檢視本體;本檔不改它):VDF 冊上照舊只有各家族尾版那一列,
    另補「凍結樣本路徑」一列 —— 只補冊上已有的家族、檔真的在、而且冊上還沒有那個路徑的;
    補的那列 = 同家族尾版那列的拷貝,只換 path / version(閘 · 旗標照尾版判)。其他屬性原樣轉給被包的冊。"""

    def __init__(self, inv, samples: dict, root: Path):
        self._inv, self._samples, self._root = inv, dict(samples), Path(root)
        self.added: list = []

    def engines(self, system, *a, **kw):
        rows = list(self._inv.engines(system, *a, **kw))
        if system != SELF_ID:
            return rows
        have = {r.get("path") for r in rows}
        for path, fam in self._samples.items():
            if path in have or not (self._root / path).is_file():
                continue
            tail = [r for r in rows if r.get("family") == fam]
            if not tail:
                continue
            row = dict(tail[0], path=path, version="v" + Path(path).stem.rsplit("_v", 1)[-1], sample_of=tail[0].get("path"))
            rows.append(row)
            self.added.append(path)
        return rows

    def __getattr__(self, name):
        return getattr(self._inv, name)


def chain_modules(top=None) -> dict:
    """沿已載入的前版鏈(各支模組的 PRIOR)由新到舊收:{版號: 模組}。"""
    out, mod = {}, (top or PRIOR)
    while mod is not None and getattr(mod, "__file__", None):
        out[_vnum_v0158(mod.__file__)] = mod
        nxt = vars(mod).get("PRIOR")
        mod = nxt if nxt is not mod else None
    return out


def scoped_prior_selftest(m150, m149, samples: dict, root: Path, run):
    """跑 run()(= 前版鏈自測);只在 v0150 自己那一層的自測期間,把 v0149._inv 換成回 SampleBook 的版本
    (v0150 的 launch_paths 走 PRIOR._inv(),PRIOR = v0149);v0150 自測尾端呼叫 v0149 自測時先換回原樣,跑完再換回樣本冊。
    結束(含例外)一律還原 v0150.selftest / v0149.selftest / v0149._inv。回 (run 的結果, 補了哪些路徑)。"""
    orig_inv, orig150, orig149 = m149._inv, m150.selftest, m149.selftest
    books: list = []

    def sample_inv():
        b = SampleBook(orig_inv(), samples, root)
        books.append(b)
        return b

    def s149():
        m149._inv = orig_inv
        try:
            return orig149()
        finally:
            m149._inv = sample_inv

    def s150():
        m149._inv, m149.selftest = sample_inv, s149
        try:
            return orig150()
        finally:
            m149._inv, m149.selftest = orig_inv, orig149

    m150.selftest = s150
    try:
        return run(), sorted({p for b in books for p in b.added})
    finally:
        m150.selftest, m149.selftest, m149._inv = orig150, orig149, orig_inv


def selftest() -> int:
    import types
    import tempfile
    import shutil
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    def safe(fn):
        try:
            return fn()
        except Exception as exc:
            return exc

    print("=== %s %s · 薄尾自測(前版鏈自測的凍結樣本冊;零網路)===" % (_STEM, TAG))
    td = Path(tempfile.mkdtemp(prefix="vdfmgr158_"))
    try:
        fam = "VDF_ENG900_Demo"
        tailp, oldp = "functional modules/VDF/engine/%s_v0102.py" % fam, "functional modules/VDF/engine/%s_v0101.py" % fam
        gone = "functional modules/VDF/engine/VDF_ENG901_Gone_v0100.py"
        for q in (tailp, oldp, gone):
            (td / q).parent.mkdir(parents=True, exist_ok=True)
            (td / q).write_text("x = 1\n", encoding="utf-8")

        class FakeInv:
            def engines(self, system):
                return [{"eid": "ENG900", "family": fam, "path": tailp, "version": "v0102", "flags": ["--selftest"]}]   # 別的系統也回同一列:測「只補 VDF」

            def gate(self, r, system):
                return {"lamp": "GREEN"}

        b = SampleBook(FakeInv(), {oldp: fam, gone: "VDF_ENG901_Gone", "functional modules/VDF/engine/%s_v0100.py" % fam: fam}, td)
        rows = b.engines("VDF")
        add = [r for r in rows if r["path"] == oldp]
        chk("① 樣本冊:冊上家族的前版樣本補一列(拷尾版那列,只換 path / version;旗標照尾版)· 閘照轉給原冊",
            len(rows) == 2 and len(add) == 1 and add[0]["version"] == "v0101" and add[0]["eid"] == "ENG900"
            and add[0]["flags"] == ["--selftest"] and add[0]["sample_of"] == tailp and b.gate(add[0], "VDF") == {"lamp": "GREEN"}, rows)
        chk("② 不猜:冊上沒有的家族不補 · 檔不在不補 · 已在冊上不重複 · 別的系統原樣",
            gone not in {r["path"] for r in rows} and len({r["path"] for r in rows}) == len(rows)
            and SampleBook(FakeInv(), {tailp: fam}, td).engines("VDF") == FakeInv().engines("VDF")
            and b.engines("VRN-2") == FakeInv().engines("VRN-2"), [r["path"] for r in rows])

        seen = []
        m149 = types.SimpleNamespace()
        m149._inv = FakeInv
        m149.selftest = lambda: seen.append(("149", type(m149._inv()).__name__)) or 0
        m150 = types.SimpleNamespace()
        m150.selftest = lambda: seen.append(("150", type(m149._inv()).__name__, [r["path"] for r in m149._inv().engines("VDF")])) or m149.selftest()
        o149, o150, oinv = m149.selftest, m150.selftest, m149._inv
        rc, added = scoped_prior_selftest(m150, m149, {oldp: fam}, td, lambda: m150.selftest())
        chk("③ 只在 v0150 那一層換冊:v0150 自測看到樣本冊(含樣本路徑)· 它呼叫的 v0149 自測看到原冊 · 結束全部還原",
            rc == 0 and added == [oldp] and seen[0][:2] == ("150", "SampleBook") and oldp in seen[0][2] and seen[1] == ("149", "FakeInv")
            and m149.selftest is o149 and m150.selftest is o150 and m149._inv is oinv, (seen, added))

        def boom():
            m150.selftest()
            raise RuntimeError("x")
        r = safe(lambda: scoped_prior_selftest(m150, m149, {oldp: fam}, td, boom))
        chk("④ 前版鏈自測丟例外也還原(例外照拋,不吞)", isinstance(r, RuntimeError) and m149.selftest is o149
            and m150.selftest is o150 and m149._inv is oinv, r)

        mods = chain_modules()
        chk("⑤ 真鏈:沿 PRIOR 找到 v0157 … v0150 · v0149(v0150 的 launch_paths 走 v0149._inv)· 凍結樣本檔都在",
            all(v in mods for v in range(149, 158)) and callable(getattr(mods.get(149), "_inv", None))
            and all((VIA_ROOT / k).is_file() for k in FROZEN_SAMPLES_V0150), sorted(mods)[-10:])
        src = Path(__file__).read_text(encoding="utf-8")
        imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
        chk("⑥ 三橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不寫",
            all(t in src for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]"))
            and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
            and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
            and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    finally:
        shutil.rmtree(td, ignore_errors=True)
    print("  [計] %s %s 本版 %d/%d · %s" % (_STEM, TAG, p, p + f, "PASS" if not f else "FAIL"), flush=True)
    if f:
        return 1
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    mods = chain_modules()
    prc, added = scoped_prior_selftest(mods[150], mods[149], FROZEN_SAMPLES_V0150, VIA_ROOT, PRIOR.selftest)
    print("  [樣本冊] v0150 自測期間補冊:%s" % (", ".join(Path(x).name for x in added) or "無(樣本仍是尾版)"), flush=True)
    return 0 if prc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

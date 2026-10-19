#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0109 — 薄尾:自測 ㊹ 取代 v0107 ㉚(機器上裝了 VCGC 的 DuckDB 環境鉤時 ㉚ 必 FAIL → 一鍵 ⑤ 紅、不真跑)

  工作站實跑(2026-10-20 · 一鍵 Invoke-VDF-Activate v0105 · ActivateVDF v0108):⑤ 自測 RED → 一鍵不真跑(結束碼 1)。
  v0108 9/9 過;v0107 ㉚ FAIL:{'子': {'hook': 'v0100', 'memory_limit': '974.6 MiB', 'threads': '2'}, '孫': 'v0100', '關': None,
  '實測': '… 記憶體 974.6 MiB(預算 1022 MB)· 執行緒 2 · 鉤 VCGC 環境鉤 v0100'}。
  → via_vdf_312 境裡已有 VCGC(CGC_MDL262)代裝的 via_duck_temp 鉤(.pth)。v0107 照它自己的設計 ③ 讓位(temp / 記憶體讓 VCGC 鉤管 ·
  只補執行緒),實際值全對:溢寫夾 = 本輪流程 temp/p<pid> · 記憶體 974.6 MiB = 預算 1,022 MB · 執行緒 2 = 預算 · VIA_DUCK_TEMP=0 → 不掛。
  ㉚ 卻寫死「生效的鉤必須是 v0107 自己的」(把「境裡沒有 VCGC 鉤」當前提)—— 測試錯,不是流程錯(同 v0102 ⑫ 取代 v0101 ⑩)。
  而且 v0107 在 ㉚ 失敗時不往下委派 → 工作站上 v0106 … v0100 的自測根本沒跑到。
本版:
  ① ㊹ 同一個性質重驗:先用「沒掛本輪鉤」的流程環境起一次子行程,看境裡本來有沒有鉤(VCGC 代裝的)→ 有 = 生效的鉤應是它
     (v0107 讓位,執行緒由 v0107 補)· 沒有 = 應是 v0107 本輪鉤;子行程與孫行程:鉤 = 應是的那一個 · 溢寫夾在本輪流程 temp 下 ·
     記憶體 = 每條預算(±5%)· 執行緒 = 每條執行緒;VIA_DUCK_TEMP=0 → 不掛;起跑實測 GREEN 且三項都 ok。沒有 duckdb → 不驗(不代裝)。
  ② 委派前版自測時只容 v0107 的 ㉚ 一條失敗(照印「由 ㊹ 取代」),其餘任何一條失敗照判 FAIL;
     v0107 在 ㉚ 失敗時不往下委派 → 本版補跑 v0106(→ … → v0100)自測。
  ③ 其餘全照 v0108(溢寫模式記憶體閘不等 · v0107 記憶體 / TEMP 鉤與起跑實測);本版一輪落檔的 schema / tag 標 v0109。
VDF 自己的模組:不匯入他系統程式(VCGC 的鉤只從子行程「看」它有沒有生效,不 import、不裝、不改);同意閘不讀不寫;不碰 TA-Lib;
不裝套件、不寫環境。
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
import io
import json
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


def _vnum_v0109(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0109(p) < _vnum_v0109(__file__)), key=_vnum_v0109)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100
V0107 = vars(PRIOR).get("PRIOR")                   # v0108 的前版 = v0107(記憶體 / TEMP 鉤 · PR #536)
_V0106 = vars(V0107).get("PRIOR") if V0107 is not None else None


def __getattr__(name):
    return getattr(PRIOR, name)


_ACTIVATE_PRIOR = PRIOR.activate


def _stamp_layer(prev):
    """總覽落檔最內層再標本版(v0107 / v0108 一輪裡各自包在外層 · 它們標完才到這層);總覽落檔函式本身不換(v0108 ㊶ 照驗)。"""
    def _stamp_then_write(c, u=None):
        c["schema"], c["tag"] = "VDF_ActivateVDF_v0109", TAG
        return prev(c, u) if u is not None else prev(c)
    return _stamp_then_write


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0108 activate(溢寫模式記憶體閘不等 · v0107 記憶體 / TEMP 鉤);這一輪版號與落檔標 v0109。"""
    keep = PRIOR.TAG
    PRIOR.TAG = TAG
    prev = vars(_V0106).get("_WRITE_REPORT_V0100") if _V0106 is not None else None
    if prev is not None:
        _V0106._WRITE_REPORT_V0100 = _stamp_layer(prev)
    try:
        return _ACTIVATE_PRIOR(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep
        if prev is not None:
            _V0106._WRITE_REPORT_V0100 = prev


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
SUPERSEDED = "㉚"                                  # v0107 那一條(本版 ㊹ 取代)


def _superseded(rc1: int, failed: list) -> bool:
    """只容 v0107 ㉚ 這一條失敗(本版 ㊹ 已用不靠「境裡沒有 VCGC 鉤」的判法過了);其餘任何一條失敗照判紅。"""
    return rc1 == 1 and list(failed) == [SUPERSEDED]


def _under(p, root) -> bool:
    if not p or not root:
        return False
    a, b = os.path.normcase(os.path.abspath(str(p))), os.path.normcase(os.path.abspath(str(root)))
    return a == b or a.startswith(b.rstrip("\\/") + os.sep)


def _hook_check() -> tuple:
    """㊹:v0107 ㉚ 同一個性質;生效的鉤可以是境裡本來就有的 VCGC 環境鉤(那時 v0107 讓位、只補執行緒)。
    回 (True / False / None = 本境沒有 duckdb, 細節)。"""
    try:
        import duckdb  # noqa: F401
    except ImportError:
        return None, {}
    with tempfile.TemporaryDirectory(prefix="activatevdf109_") as td:
        t = Path(td)
        res = V0100.optimize_resources(want=3, stamp="20261020_090000", root=t)
        plan = res["plan"]
        base = dict(os.environ)
        for k in ("PYTHONPATH", "VIA_DUCK_TEMP", "VIA_VDF_DUCK_HOOK"):   # 同 v0107 ㉚:父輪的鉤標記不帶進來
            base.pop(k, None)
        V0107._RUN7["on"] = True
        try:
            env = V0107.flow_env(res, "engines", base_env=dict(base))
            probe = V0107.probe_memtemp(res)
        finally:
            V0107._RUN7["on"] = False
        plain = V0107.flow_env(res, "engines", base_env=dict(base))
        env_off = dict(env, VIA_DUCK_TEMP="0")

        def run(e, grand=False):
            args = [sys.executable, "-c", V0107._GRANDCHILD, V0107.PROBE] if grand else [sys.executable, "-c", V0107.PROBE]
            cp = subprocess.run(args, env=e, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
            line = next((ln for ln in cp.stdout.splitlines() if ln.startswith("VDFPROBE ")), None)
            return json.loads(line[9:]) if line else {"rc": cp.returncode, "err": (cp.stderr or "")[-300:]}
        pre = run(plain)
        vcgc = pre.get("hook")                     # 沒掛本輪鉤也生效的 = 境裡本來就有的(VCGC CGC_MDL262 代裝的 via_duck_temp)
        want = vcgc or V0107.HOOK_TAG
        want_tmp = env["VIA_DUCKDB_TEMP_DIR"]
        got, grand, off = run(env), run(env, True), run(env_off)
        mem = V0107._bytes(got.get("memory_limit"))
        budget = plan["duckdb_mem_mb"] * 1e6
        ok = (pre.get("duckdb") is not None and got.get("hook") == want and grand.get("hook") == want
              and _under(got.get("temp_directory"), want_tmp) and _under(grand.get("temp_directory"), want_tmp)
              and bool(mem) and abs(mem - budget) <= 0.05 * budget
              and str(got.get("threads")) == str(plan["threads_per_flow"])
              and (not vcgc or got.get("threads_hook") == V0107.HOOK_TAG)
              and off.get("hook") is None and not _under(off.get("temp_directory"), want_tmp)
              and probe.get("lamp") == "GREEN" and bool(probe.get("temp_ok") and probe.get("mem_ok") and probe.get("threads_ok")))
        note = {"境裡原有的鉤": vcgc or "無", "應生效": want,
                "子": {k: got.get(k) for k in ("hook", "threads_hook", "memory_limit", "threads")} | {"溢寫夾在本輪": _under(got.get("temp_directory"), want_tmp)},
                "孫": grand.get("hook"), "關": off.get("hook"), "實測": probe.get("lamp")}
    return bool(ok), note


class _Tee:
    """同時寫到畫面與緩衝(委派前版自測時照常印出,同時收下來判哪幾條失敗;同 v0102)。"""

    def __init__(self, *outs):
        self.outs = outs

    def write(self, s):
        for o in self.outs:
            o.write(s)
        return len(s)

    def flush(self):
        for o in self.outs:
            o.flush()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note != "" else ""), flush=True)
    print(f"=== {TAG} · 薄尾自測(㊹ 取代 v0107 ㉚:機器上裝了 VCGC 的 DuckDB 環境鉤也要過;沙盒 · 零網路)===", flush=True)
    r, note = _hook_check()
    if r is None:
        chk("㊹ duckdb 不在本境 → 不驗(不代裝;v0107 ㉚ 同樣不跑)", True)
    else:
        chk("㊹ 取代 v0107 ㉚:子行程與孫行程的 duckdb.connect() 都生效 —— 鉤 = 境裡原有的 VCGC 鉤(v0107 讓位 · 執行緒由 v0107 補)或 v0107 本輪鉤 · "
            "溢寫夾在本輪流程 temp 下 · 記憶體 = 每條預算 · 執行緒 = 每條執行緒;VIA_DUCK_TEMP=0 → 不掛;起跑實測 GREEN 且三項都 ok", r, note)
    chk("㊺ 委派判定:前版自測只容 v0107 ㉚ 一條失敗(㉚ 加別條 · 只有別條 · 沒失敗 · 回碼不是 1 都不算取代)",
        _superseded(1, ["㉚"]) and not _superseded(1, ["㉚", "㉛"]) and not _superseded(1, ["㉙"]) and not _superseded(1, [])
        and not _superseded(0, []) and not _superseded(2, ["㉚"]))
    chk("㊻ 前版鏈:v0108(溢寫不等)→ v0107(記憶體 / TEMP 鉤:鉤名 · 實測 · 流程環境都在)→ v0106(總覽落檔 _WRITE_REPORT_V0100)",
        Path(PRIOR_PATH).stem.endswith("_v0108") and hasattr(PRIOR, "spill_nowait_enabled") and V0107 is not None
        and Path(V0107.__file__).stem.endswith("_v0107") and all(hasattr(V0107, k) for k in ("HOOK_TAG", "PROBE", "_GRANDCHILD", "probe_memtemp", "flow_env", "_RUN7"))
        and _V0106 is not None and "_WRITE_REPORT_V0100" in vars(_V0106), f"{Path(PRIOR_PATH).name} → {Path(V0107.__file__).name if V0107 else '?'}")
    seen = []
    layer = _stamp_layer(lambda c, u=None: seen.append(dict(c)) or c)
    layer({"lamp": "GREEN", "schema": "VDF_ActivateVDF_v0108", "tag": "x"})
    chk("㊼ 本版一輪的總覽落檔最內層標 v0109(schema · tag · 蓋過 v0107 / v0108 的標)· 總覽落檔 / 頁面函式不換(v0108 ㊶ 照驗)",
        seen == [{"lamp": "GREEN", "schema": "VDF_ActivateVDF_v0109", "tag": TAG}]
        and V0100.write_report is PRIOR.write_report and V0100.render_html is PRIOR.render_html)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("㊽ 加速器橋 · 網路橋在;不匯入他系統程式(VCGC 的鉤只從子行程看);不碰 TA-Lib;同意閘不寫",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC", "via_duck_temp"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    n_ok = sum(ok)
    print(f"  [計] {TAG} 本版 {n_ok}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    if not all(ok):
        return 1
    buf, keep_out = io.StringIO(), sys.stdout
    sys.stdout = _Tee(keep_out, buf)
    try:
        rc1 = PRIOR.selftest()
    finally:
        sys.stdout = keep_out
    failed = re.findall(r"^\s*\[FAIL\] (\S+)", buf.getvalue(), re.M)
    if _superseded(rc1, failed):
        print("  [取代] v0107 ㉚(把「境裡沒有 VCGC 的 DuckDB 環境鉤」當前提,裝了的機器必 FAIL)由本版 ㊹ 取代;v0107 其餘照過。"
              "v0107 在 ㉚ 失敗時不往下委派 → 本版補跑 v0106 自測", flush=True)
        rc1 = _V0106.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0102 / v0107 / v0108)


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

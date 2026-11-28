#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_HostBoot v0109 — 薄尾(v0100–v0108 一字不動):up 也用網路模組(VCGC-REQ285)

操作員 2026-11-28:「PY module should be employment with network module as well」(原文 PDF,依上下文讀作 PY)。
v0108 的 up 掛了加速器(載不到最多黃)。本版補網路模組,照 CLAUDE.md「有對外擷取的引擎,另經語法樹導入鎖冊上的網路工具」:
  ① 檔頭掛標準網路橋 [VIA:NET-BRIDGE](同 VDF 引擎那一塊:惰性載入統包網路工具,graceful)。
  ② 開跑前檢查一次鎖冊上的網路工具(VIA_ToolVersion_Lock 的 network.path,現役 VeritasAegisNexus_v1652):
     在子行程裡真的載一次(不在本行程載,免得吃記憶體;不出網、不設同意閘)→ 載得到 = 綠,載不到 / 冊讀不到 = 黃。
     VDF 那一道會對外擷取,所以網路工具載不到時:VDF 照跑(它自己有開跑前檢查),但總燈最好只到黃,另加一列寫原因。
  ③ 其餘照 v0108:三道同時 · VCGC 叫管理器 launch · 降壓 · 監工 · 加速器 / 容器封頂 · 三數。
不 import 他系統;零 TA-Lib;同意閘不在本檔設。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(graceful;執行時載得到才算) =====
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
    VIA_ACCEL = None  # graceful:載不到時總燈最好只到黃(v0108 ④)
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
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT 由擷取端自己檢查);缺席回 None(誠實)"""
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
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0109"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
LOCK = "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


_BELOW = [p for p in HERE.parent.glob(FAMILY + "_v[0-9][0-9][0-9][0-9].py") if 0 <= _vnum(p) < _vnum(HERE)]
PRIOR_PATH = max(_BELOW, key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{FAMILY}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE106 = PRIOR.BASE106
_PREV_RUN_UP = vars(BASE106)["run_up"]       # v0108 掛上去的 run_up
say = PRIOR.say


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_PROBE = ("import importlib.util,sys\n"
          "p=sys.argv[1]\n"
          "s=importlib.util.spec_from_file_location('via_net_probe',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
          "print('NET_OK',len(dir(m)))\n")


def net_check(via: Path, py: str = None, timeout: int = 120) -> dict:
    """鎖冊上的網路工具在子行程裡真的載一次。回 {lamp, path, note}。不出網、不設同意閘。"""
    try:
        rel = json.loads((via / LOCK).read_text(encoding="utf-8"))["network"]["path"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        return {"lamp": "YELLOW", "path": None, "note": f"鎖冊讀不到網路工具:{type(e).__name__}"}
    p = via.parent / rel
    if not p.is_file():
        p = via / rel
    if not p.is_file():
        return {"lamp": "YELLOW", "path": rel, "note": "鎖冊上的網路工具檔不在"}
    try:
        r = subprocess.run([py or sys.executable, "-c", _PROBE, str(p)], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env=dict(os.environ, PYTHONWARNINGS="ignore"))
    except subprocess.TimeoutExpired:
        return {"lamp": "YELLOW", "path": rel, "note": f"載網路工具超過 {timeout} 秒"}
    if r.returncode == 0 and "NET_OK" in r.stdout:
        return {"lamp": "GREEN", "path": rel, "note": "鎖冊網路工具載得到(子行程實載)"}
    last = (r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or ["?"])[-1]
    return {"lamp": "YELLOW", "path": rel, "note": f"網路工具載不到:{last[:120]}"}


def apply_net(rc: int, rows: list, net: dict) -> tuple:
    """網路工具那一列加進表;載不到 → 總燈最好只到黃(紅照紅)。"""
    rows = list(rows) + [{"step": "⓪ 網路工具", "rc": None, "secs": 0.0, "lamp": net["lamp"], "note": f"{Path(net['path'] or '?').name} · {net['note']}"}]
    if rc == 0 and net["lamp"] != "GREEN":
        rc = 2
    return rc, rows


def run_up(via: Path, extra: list, skip_backup: bool = False, runner=None, py: str = None) -> tuple:
    net = net_check(via, py)
    say(f"[up] 網路模組:{net['note']}(橋 {'在' if VIA_NET_TOOL_PATH else '沒找到統包網路工具'})")
    rc, rows = _PREV_RUN_UP(via, extra, skip_backup, runner, py)
    return apply_net(rc, rows, net)


def install() -> None:
    BASE106.run_up = run_up         # v0106 的 main 查它模組全域的 run_up
    BASE106.TAG = TAG


install()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return BASE106.main(a)


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    import ast
    src = HERE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    chk("① 加速器:第 3 行標記 · 語法樹匯入 VIA_SuperAccel_Module · 執行時載得到",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and "VIA_SuperAccel_Module" in imports and VIA_ACCEL is not None)
    chk("② 網路橋:[VIA:NET-BRIDGE] 在 · 統包網路工具找得到且載得起來",
        "[VIA:NET-BRIDGE:v0100]" in src and VIA_NET_TOOL_PATH is not None and _via_net() is not None, str(VIA_NET_TOOL_PATH))
    chk("③ 前版經 glob 載入 · 掛鉤在 v0106 那一層", PRIOR_PATH == max(_BELOW, key=_vnum) and vars(BASE106)["run_up"] is run_up, PRIOR_PATH.name)
    body = "\n".join(src.splitlines()[60:])
    chk("④ 不 import 他系統 · 零 TA-Lib", not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_|CGC_|talib)", body, re.M))
    real = net_check(HERE.parents[3])          # 本檔在 VIA/docs/handoff/ai/
    chk("⑤ 真樹:鎖冊上的網路工具子行程實載 → 綠", real["lamp"] == "GREEN", real["note"])
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        (via / "supportive modules/registry").mkdir(parents=True)
        chk("⑥ 反控:鎖冊不在 → 黃(照實)", net_check(via)["lamp"] == "YELLOW")
        (via / LOCK).write_text(json.dumps({"network": {"path": "VeritasIntelligenceAnalytics/supportive modules/network/Nope_v0100.py"}}), encoding="utf-8")
        chk("⑦ 反控:鎖冊指的檔不在 → 黃", net_check(via)["note"].startswith("鎖冊上的網路工具檔不在"))
        bad_tool = via / "supportive modules/network/Broken_v0100.py"
        bad_tool.parent.mkdir(parents=True)
        bad_tool.write_text("raise RuntimeError('boom')\n", encoding="utf-8")
        (via / LOCK).write_text(json.dumps({"network": {"path": "VeritasIntelligenceAnalytics/supportive modules/network/Broken_v0100.py"}}), encoding="utf-8")
        nb = net_check(via)
        chk("⑧ 反控:網路工具一載就丟例外 → 黃 · 帶錯誤行", nb["lamp"] == "YELLOW" and "boom" in nb["note"], nb["note"][:60])
    g = [{"step": "① A", "rc": 0, "lamp": "GREEN"}]
    green, yellow = {"lamp": "GREEN", "path": "x/N_v0100.py", "note": "ok"}, {"lamp": "YELLOW", "path": None, "note": "no"}
    chk("⑨ 網路工具綠 → 總燈不變;黃 → 綠降黃 rc 2;紅照紅;一律多一列 ⓪ 網路工具",
        apply_net(0, g, green)[0] == 0 and apply_net(0, g, yellow)[0] == 2 and apply_net(1, g, yellow)[0] == 1
        and apply_net(0, g, green)[1][-1]["step"] == "⓪ 網路工具")
    chk("⑩ 三數不把 ⓪ 網路工具算成道", PRIOR.tally(apply_net(0, g, green)[1]) == "應 1 · 已 1 · 略過 0")
    env = dict(os.environ)
    env.pop("VIA_FROM_VCGC", None)
    pr = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    chk("⑪ 直接前版自測(乾淨子行程)rc 0", pr.returncode == 0, (pr.stdout.strip().splitlines() or ["?"])[-1][:80])
    print(f"[計] {TAG} 自測 {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else " · PASS"), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())

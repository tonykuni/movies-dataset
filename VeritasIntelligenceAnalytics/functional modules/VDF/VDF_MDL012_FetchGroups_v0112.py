#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL012_FetchGroups v0112 — 薄尾(v0100–v0111 一字不動):並行道起子行程時套擷取冊該列的 env(VAKE_ROOT 回到資料家)

操作員 2026-11-21 令:「VDF/VRN 一定要輸出且要做到增量維護不重工 …via_database」「輸出驗證」。
容器實錄(啟動器 MDL022 → ActivateVDF → MDL012 並行道 → MDL008 _child 011d):擷取道的 011d 把統計局 / 中國宏觀寫進
~/VAKE(桌機 = C:\\VIA\\VAKE,在資料家外面);同一輪補洞(db refill → MDL008 run)的 011d 寫進 <資料家>/vake
→ 兩本 VAKE 庫,補洞那本沒有新鮮紀錄,統計局 721 條整批重抓(TTL 跳過 0),資料也分兩處。
根因:擷取冊每列帶 env(011 / 011d:VAKE_ROOT = {home}/vake);MDL008 v0101 run 起子行程會把它套上({home} → 資料家),
MDL012 v0107 起的並行道(LAUNCH = v0109 launch_child_v0109)直接起 MDL008 _child,用的是道自己的 env,從沒套列的 env。
本版只改一件事:並行道的 LAUNCH 先把該列 env 照 MDL008 v0101 的同一規則套上({home} 換成資料家;列沒 env = 照舊),再交 v0109。
其餘(道 · 心跳 · 逾時 · 判讀 · 頁 · run)全部照 v0111。不代設同意閘;不碰 TA-Lib;零網路自測(假子行程)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG_V0112 = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0112(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if 0 <= _vnum_v0112(p) < _vnum_v0112(__file__)), key=_vnum_v0112)
_spec = importlib.util.spec_from_file_location("VDF_MDL012_FetchGroups_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _chain_v0112() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


V0107 = next((m for m in _chain_v0112() if "LAUNCH" in vars(m) and callable(vars(m).get("launch_child"))), None)
_LAUNCH_PRIOR = vars(V0107)["LAUNCH"] if V0107 is not None else None


def row_env_v0112(env, r: dict, home) -> dict:
    """同 MDL008 v0101 run:dict(env)+ 列的 env({home} → 資料家);列沒 env = 照原 env。"""
    out = dict(env if env is not None else os.environ)
    out.update({k: str(v).replace("{home}", str(home)) for k, v in ((r or {}).get("env") or {}).items()})
    return out


def launch_child_v0112(mdl008, r, mode, home, logs, timeout, env, *a, **k):
    return _LAUNCH_PRIOR(mdl008, r, mode, home, logs, timeout, row_env_v0112(env, r, home), *a, **k)


def _install() -> None:
    if V0107 is not None:
        vars(V0107)["LAUNCH"] = launch_child_v0112


def _restore() -> None:
    if V0107 is not None:
        vars(V0107)["LAUNCH"] = _LAUNCH_PRIOR


_install()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    _restore()
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install()
    print(f"=== {TAG_V0112} · 薄尾自測(並行道套擷取冊列的 env)===")
    chk("⓪ 前版 v0111(含 v0110 → v0100 鏈)自測過", rc0 == 0, f"rc {rc0}")
    chk("① 換裝:並行道的 LAUNCH = 本版(前版 v0109 起子行程的函式在下一層)",
        V0107 is not None and vars(V0107)["LAUNCH"] is launch_child_v0112 and callable(_LAUNCH_PRIOR))
    import subprocess
    seen = []
    real_popen, real_run = subprocess.Popen, subprocess.run

    class FakeP:
        def __init__(self, cmd, *a, **k):
            seen.append(dict(k.get("env") or {}))
            self.stdout = iter(["ok\n"])
            self.returncode = 0

        def poll(self):
            return 0

        def wait(self, timeout=None):
            return 0

        def kill(self):
            pass

    def fake_run(cmd, *a, **k):
        seen.append(dict(k.get("env") or {}))
        return subprocess.CompletedProcess(cmd, 0, "ok\n", "")
    import json
    tail = max(HERE.glob("VDF_FetchSystem_SSOT_v*.json"), key=_vnum_v0112)
    row = next(x for x in json.loads(tail.read_text(encoding="utf-8"))["engines"] if x["id"] == "011d")
    with tempfile.TemporaryDirectory(prefix="mdl012_v0112_") as td:
        home, logs = Path(td) / "dict", Path(td) / "_logs"
        home.mkdir()
        logs.mkdir()
        base = {"PATH": os.environ.get("PATH", ""), "VIA_FG_LANE": "vake"}
        subprocess.Popen, subprocess.run = FakeP, fake_run
        try:
            seen.clear()
            try:
                _LAUNCH_PRIOR(Path("m008.py"), row, "live", home, logs, 30, dict(base))
            except Exception:
                pass
            old = seen[-1] if seen else {}
            seen.clear()
            try:
                launch_child_v0112(Path("m008.py"), row, "live", home, logs, 30, dict(base))
            except Exception:
                pass
            new = seen[-1] if seen else {}
        finally:
            subprocess.Popen, subprocess.run = real_popen, real_run
    chk("② 擷取冊尾版(%s)011d 列帶 env VAKE_ROOT = {home}/vake" % tail.name, (row.get("env") or {}).get("VAKE_ROOT") == "{home}/vake", row.get("env"))
    chk("③ 重現:前版並行道起子行程沒帶 VAKE_ROOT(子行程落到 ~/VAKE · 桌機 C:\\VIA\\VAKE)", bool(old) and "VAKE_ROOT" not in old, sorted(old)[:6])
    chk("④ 本版:子行程帶 VAKE_ROOT = <資料家>/vake · 道的其餘 env 照留(VIA_FG_LANE)",
        new.get("VAKE_ROOT") == str(home / "vake") and new.get("VIA_FG_LANE") == "vake", {k: new.get(k) for k in ("VAKE_ROOT", "VIA_FG_LANE")})
    e2 = row_env_v0112({"A": "1"}, {"id": "x"}, "/h")
    chk("⑤ 列沒有 env → 照原 env(不多不少)", e2 == {"A": "1"}, e2)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑥ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑦ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"[計] {TAG_V0112} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())

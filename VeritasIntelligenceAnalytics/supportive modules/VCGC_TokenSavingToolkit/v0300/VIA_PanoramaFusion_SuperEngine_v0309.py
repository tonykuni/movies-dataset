#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0309 — 薄尾(v0300–v0308 一字不動):第八輪(PR #782 Codex P2)子行程拿到的是這一輪實際生效的設定

v0300 的 config() 讀既有設定檔後,--root / --work 只改記憶體裡的 cfg,`config_path` 仍指舊檔;contracts_run() 與
  probe_candidate_bridges() 把 config_path 經 VIA_DUAL_CONFIG 交給子行程,產生的執行期橋就讀舊檔的 root(舊倉的鎖冊與加速器)。
本版包 config():生效的設定跟存檔內容不同(例如 --root 改了 root)→ 在 work/effective_configs/ 原子寫一份「這一輪實際生效」的快照,
  cfg["config_path"] 指向快照(子行程拿到的就是它),原設定檔不改,cfg["saved_config_path"] 記原檔;快照只留最新 20 份。
  兩者一樣(例如剛 init)→ 不另寫、照舊。文件與 toolkit.index 改指 v0309。其餘照 v0308 → v0300。
自測零網路 · 暫存夾 · 不碰 TA-Lib · 不設同意閘。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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

import argparse
import importlib.util
import json
import re
import sys
import tempfile
import time
import uuid
from pathlib import Path

VERSION = "v0309"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
KEEP = 20


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0308
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.V300


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_ORIG = {k: getattr(V300, k) for k in ("config", "ENGINE_FILE", "__file__")}


def _body(cfg: dict) -> dict:
    return {k: v for k, v in cfg.items() if k not in ("config_path", "saved_config_path")}


def config(args) -> dict:
    cfg = _ORIG["config"](args)
    saved = Path(cfg["config_path"])
    try:
        on_disk = _body(V300.load(saved)) if saved.is_file() else None
    except (OSError, ValueError):
        on_disk = None
    if on_disk == _body(cfg):
        return cfg
    folder = Path(cfg["work"]) / "effective_configs"
    folder.mkdir(parents=True, exist_ok=True)
    snap = folder / f"{time.time_ns()}-{uuid.uuid4().hex[:8]}.json"
    eff = dict(_body(cfg), config_path=str(snap), saved_config_path=str(saved))
    V300.save(snap, eff)                                       # v0300 的 save:原子寫
    for old in sorted(folder.glob("*.json"))[:-KEEP]:
        old.unlink()
    cfg["config_path"], cfg["saved_config_path"] = str(snap), str(saved)
    return cfg


def install() -> None:
    V300.config = config
    V300.ENGINE_FILE = Path(__file__).name
    V300.__file__ = str(Path(__file__).resolve())


def uninstall() -> None:
    for k, v in _ORIG.items():
        setattr(V300, k, v)


install()


def selftest() -> int:
    ok = []

    def chk(label, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + label + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路工具橋", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="pf309_") as td:
        base = Path(td)
        old_root, new_root, work = base / "old_checkout", base / "new_checkout", base / "work"
        old_root.mkdir()
        new_root.mkdir()
        ns = lambda root: argparse.Namespace(config=None, work=work, root=root)  # noqa: E731 — argparse 給的是 Path
        first = config(ns(old_root))                           # 第一次:建設定檔(root = old)
        saved = Path(first["config_path"])
        o = _ORIG["config"](ns(new_root))                      # 前版:--root 換成 new,config_path 仍指舊檔
        old_view = V300.load(Path(o["config_path"]))["root"]
        n = config(ns(new_root))                               # 本版
        new_view = V300.load(Path(n["config_path"]))["root"]
        saved_root = V300.load(saved)["root"]
        same = config(ns(old_root))                            # 跟存檔一樣 → 不另寫快照
    chk("T2 (P2)既有設定 + --root 換倉:前版交給子行程的設定檔 root 仍是舊倉;本版快照 root = 新倉、原設定檔不改",
        o["root"] == str(new_root) and old_view == str(old_root) and n["root"] == str(new_root) and new_view == str(new_root)
        and saved_root == str(old_root) and n["saved_config_path"] == str(saved) and Path(n["config_path"]) != saved,
        (old_view, new_view, saved_root))
    chk("T3 生效設定跟存檔一樣(第一次 init · 同一個 root)→ 不另寫快照,config_path 照舊指原檔",
        Path(first["config_path"]) == saved and Path(same["config_path"]) == saved and "saved_config_path" not in same, same.get("config_path"))
    chk("T4 綁定 / 子行程指本檔", V300.ENGINE_FILE == Path(__file__).name and Path(V300.__file__).resolve() == Path(__file__).resolve()
        and V300.config is config)
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("T5 前版 v0308 自測照過(含 v0307 → v0300 原有 107 項)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0305 — 薄尾(v0300–v0304 一字不動):第四輪(PR #782 Codex 1×P1 + 1×P2)

① (P1)操作員入口指向有防護的尾版:OPERATION_GUIDE.md · README.md · toolkit.index.json 改叫本檔 / Start_v0305.ps1
     (文件改在同一批提交;本檔另把 ENGINE_FILE / __file__ 指到自己,綁定與子行程跟著走)。v0300 本體仍是凍結的實作,不改。
② (P2)備份輪替後回收沒人用的內容 blob:v0300 的 backup 只刪舊快照清單,blob 永遠留著,檔案一直變就一直長。
     本版在 v0300 backup 成功發布後,於同一把 backup.lock 內:讀所有留下的快照(每份都要驗得過 sha),
     只刪不被任何留下快照引用的 blob。有任何一份快照讀不了或驗不過 → 這輪不刪(寧可多留)。
其餘照 v0304 → v0303 → v0302 → v0301 → v0300。自測零網路 · 暫存夾 · 不碰 TA-Lib · 不設同意閘。
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

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0305"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0304
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.V300


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_ORIG = {k: getattr(V300, k) for k in ("backup", "ENGINE_FILE", "__file__")}


def reclaim_blobs(home: Path) -> dict:
    """呼叫端已持有 backup.lock。只刪不被任何留下快照引用的 blob;任何快照讀不了 / 驗不過 → 一個都不刪。"""
    keep = set()
    for snap in sorted((home / "snapshots").glob("*.backup.json")):
        try:
            rec = V300.load(snap)
            if V300.sha(V300.encode(rec["body"])) != rec["sha256"]:
                return {"status": "SKIPPED", "reason": "SNAPSHOT_HASH_MISMATCH", "snapshot": snap.name, "reclaimed": 0}
            keep |= {e["sha256"] for e in rec["body"]["entries"]}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return {"status": "SKIPPED", "reason": type(exc).__name__, "snapshot": snap.name, "reclaimed": 0}
    gone = 0
    for blob in (home / "blobs").iterdir():
        if blob.is_file() and blob.name not in keep:
            blob.unlink()
            gone += 1
    return {"status": "PASS", "reclaimed": gone, "kept": len(keep)}


def backup(cfg: dict) -> dict:
    result = _ORIG["backup"](cfg)
    if result.get("status") == "PASS":
        home = Path(cfg["work"]) / "backups"
        with V300.lock(home / "backup.lock"):
            result["blob_reclaim"] = reclaim_blobs(home)
    return result


def install() -> None:
    V300.backup = backup
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

    print(f"[計] {TAG} 自測開始(本版 5 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路工具橋", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)

    def run(fn, n):
        with tempfile.TemporaryDirectory(prefix="pf305_") as td:
            root, work = Path(td) / "src", Path(td) / "work"
            root.mkdir()
            cfg = {"work": str(work), "backup_roots": [{"label": "t", "path": str(root), "patterns": ["*.txt"]}]}
            last = None
            for i in range(n):
                (root / "a.txt").write_text(f"version {i}\n", encoding="utf-8")
                last = fn(cfg)
                import time as _t
                _t.sleep(0.002)
            home = work / "backups"
            snaps = sorted((home / "snapshots").glob("*.backup.json"))
            blobs = sorted(p.name for p in (home / "blobs").iterdir())
            refs = set()
            for s in snaps:
                refs |= {e["sha256"] for e in V300.load(s)["body"]["entries"]}
            restorable = all(r in blobs for r in refs)
            return len(snaps), len(blobs), restorable, last
    s_old, b_old, _, _ = run(_ORIG["backup"], 7)
    s_new, b_new, restorable, last = run(backup, 7)
    chk("T2 (P2)同一檔變 7 次:前版 5 份快照卻留 7 個 blob;本版 5 份快照 5 個 blob,留下的快照都還原得出來",
        (s_old, b_old) == (5, 7) and (s_new, b_new) == (5, 5) and restorable and last["blob_reclaim"]["status"] == "PASS",
        (s_old, b_old, s_new, b_new, restorable, last.get("blob_reclaim")))
    with tempfile.TemporaryDirectory(prefix="pf305b_") as td:
        home = Path(td)
        (home / "snapshots").mkdir()
        (home / "blobs").mkdir()
        (home / "blobs" / "orphan").write_text("x", encoding="utf-8")
        (home / "snapshots" / "1.backup.json").write_text("{not json", encoding="utf-8")
        r = reclaim_blobs(home)
        kept = (home / "blobs" / "orphan").exists()
    chk("T3 有快照讀不了 → 這輪一個 blob 都不刪(寧可多留)", r["status"] == "SKIPPED" and kept, r)
    guide = (HERE / "OPERATION_GUIDE.md").read_text(encoding="utf-8")
    index = V300.load(HERE.parent / "toolkit.index.json")
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    runs_v0300 = re.findall(r"^\s*(?:python|&).*SuperEngine_v0300\.py", guide, re.M)
    chk("T4 (P1)操作員入口(OPERATION_GUIDE 指令行 · README 主引擎連結 · toolkit.index entrypoint)都指本檔,沒有一行直接跑 v0300 · 沒有寫死的本機使用者路徑",
        not runs_v0300 and Path(__file__).name in guide and index.get("entrypoint", "").endswith(Path(__file__).name)
        and f"]({Path(__file__).name})" in readme and "C:\\Users\\" not in guide,
        (runs_v0300, index.get("entrypoint")))
    chk("T5 綁定 / 子行程指本檔", V300.ENGINE_FILE == Path(__file__).name and Path(V300.__file__).resolve() == Path(__file__).resolve()
        and V300.command_bindings()["engine"] == Path(__file__).name)
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("T6 前版 v0304 自測照過(含 v0303 → v0300 原有 107 項)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

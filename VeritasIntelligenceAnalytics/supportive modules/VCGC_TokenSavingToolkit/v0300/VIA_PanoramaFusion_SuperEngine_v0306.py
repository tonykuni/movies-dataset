#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0306 — 薄尾(v0300–v0305 一字不動):第五輪(PR #782 Codex P1)備份來源不在就不發布、不輪替

v0300 的 backup 走 os.walk 沒給 onerror:備份根被改名 / 拔掉 / 讀不了時靜靜回 0 個檔,照樣發布一份「成功」的空快照並輪替掉舊的;
  v0305 的 blob 回收接著把舊快照的內容刪掉 → 最後一份還原得回來的備份不見了(Codex 用 v0305 重現)。
本版只動 v0300 的 backup 這一個節點(抄入改兩處,types.FunctionType 綁回 v0300 全域,不用 exec):
  ① 鎖內開工前,每個 backup_roots 都必須是存在、可讀、列得出來的資料夾,否則 BACKUP_ROOT_UNAVAILABLE,什麼都不寫。
  ② os.walk 加 onerror:走訪中任何一層讀不了就丟出,快照不發布、不輪替、不回收。
  完整成功之後才跑 v0305 的 blob 回收(reclaim_blobs,本來就要每份留下的快照驗得過)。
其餘照 v0305 → v0300。自測零網路 · 暫存夾 · 不碰 TA-Lib · 不設同意閘。
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

import ast
import importlib.util
import os
import re
import sys
import tempfile
import types
from pathlib import Path

VERSION = "v0306"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0305
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.V300


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _v0306_walk_error(error: OSError) -> None:
    raise ValueError(f"BACKUP_TRAVERSAL_ERROR:{type(error).__name__}:{getattr(error, 'filename', '')}") from error


def _v0306_check_roots(cfg: dict) -> None:
    for item in cfg.get("backup_roots", []):
        base = V300.absolute(item["path"])
        label = item.get("label", str(base))
        if not base.is_dir() or not os.access(base, os.R_OK | os.X_OK):
            raise ValueError(f"BACKUP_ROOT_UNAVAILABLE:{label}")
        try:
            with os.scandir(base) as it:
                next(it, None)
        except OSError as exc:
            raise ValueError(f"BACKUP_ROOT_UNAVAILABLE:{label}:{type(exc).__name__}") from exc


# ---- v0300 backup 節點(第 842–866 行)抄入,改 ① ② 兩處 ----
def _backup_v0306(cfg: dict) -> dict:
    """完整校驗新快照後才輪替；支援 Graphify 大 JSON，並限制總容量。"""
    home=Path(cfg['work'])/'backups';blobs=home/'blobs';snaps=home/'snapshots';blobs.mkdir(parents=True,exist_ok=True);snaps.mkdir(exist_ok=True)
    entries=[];copied=0;total=0
    _v0306_check_roots(cfg)
    with lock(home/'backup.lock'):
        for item in cfg.get('backup_roots',[]):
            base=absolute(item['path'])
            for folder,dirs,files in os.walk(base,followlinks=False,onerror=_v0306_walk_error):
                here=Path(folder);dirs[:]=[d for d in dirs if d not in SKIP_DIRS and not linked(here/d) and not absolute(here/d).is_relative_to(home)]
                for file in files:
                    p=here/file;name=p.relative_to(base).as_posix()
                    if p.name.lower() in SECRET_NAMES or linked(p) or not any(fnmatch.fnmatchcase(name,v) for v in item['patterns']):continue
                    total+=p.stat().st_size
                    if total>MAX_SNAPSHOT_BYTES:raise ValueError('BACKUP_TOTAL_LIMIT')
                    raw=read(p,MAX_SNAPSHOT_BYTES);digest=sha(raw);dest=blobs/digest
                    if not dest.exists():atomic(dest,raw);copied+=1
                    if sha(read(dest,MAX_SNAPSHOT_BYTES))!=digest:raise ValueError('BACKUP_BLOB_CORRUPT')
                    entries.append({'label':item['label'],'root':str(base),'path':name,'sha256':digest,'bytes':len(raw)})
        body={'schema':SCHEMA,'at':now(),'entries':entries,'incremental_blobs':copied}
        path=snaps/(str(time.time_ns())+'.backup.json');record={'body':body,'sha256':sha(encode(body))}
        save(path,record)
        if load(path)!=record:raise ValueError('BACKUP_PUBLICATION_VERIFY')
        for old in sorted(snaps.glob('*.backup.json'))[:-MAX_BACKUP_VERSIONS]:old.unlink()
    return {'status':'PASS','snapshot':str(path),'files':len(entries),'bytes':total,'incremental_blobs':copied,'retained':len(list(snaps.glob('*.backup.json'))),'verified_before_prune':True}



_backup_node = types.FunctionType(_backup_v0306.__code__, V300.__dict__, "backup")
_ORIG = {k: getattr(V300, k) for k in ("backup", "ENGINE_FILE", "__file__")}


def backup(cfg: dict) -> dict:
    result = _backup_node(cfg)                                 # 有任何來源不在 / 讀不了 → 已丟出,下面不會跑
    if result.get("status") == "PASS":
        home = Path(cfg["work"]) / "backups"
        with V300.lock(home / "backup.lock"):
            result["blob_reclaim"] = PRIOR.reclaim_blobs(home)
    return result


def install() -> None:
    V300._v0306_walk_error = _v0306_walk_error
    V300._v0306_check_roots = _v0306_check_roots
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

    print(f"[計] {TAG} 自測開始(本版 6 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路工具橋", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)

    def scenario(fn):
        import time as _t
        with tempfile.TemporaryDirectory(prefix="pf306_") as td:
            root, work = Path(td) / "src", Path(td) / "work"
            root.mkdir()
            (root / "a.txt").write_text("precious\n", encoding="utf-8")
            cfg = {"work": str(work), "backup_roots": [{"label": "t", "path": str(root), "patterns": ["*.txt"]}]}
            first = fn(cfg)
            first_sha = V300.load(Path(first["snapshot"]))["body"]["entries"][0]["sha256"]
            root.rename(Path(td) / "src_gone")
            outcomes = []
            for _ in range(5):
                _t.sleep(0.002)
                try:
                    outcomes.append(fn(cfg)["status"])
                except ValueError as exc:
                    outcomes.append(str(exc).split(":")[0])
            home = work / "backups"
            first_alive = Path(first["snapshot"]).exists()
            blob_alive = (home / "blobs" / first_sha).exists()
            return outcomes, first_alive, blob_alive
    old = scenario(PRIOR.backup)
    new = scenario(backup)
    chk("T2 (P1)來源資料夾被改名後再備份 5 次:前版(v0305)5 次 PASS、第一份快照與 blob 都沒了;本版 5 次 BACKUP_ROOT_UNAVAILABLE,第一份與 blob 都在",
        old == (["PASS"] * 5, False, False) and new == (["BACKUP_ROOT_UNAVAILABLE"] * 5, True, True), (old, new))
    with tempfile.TemporaryDirectory(prefix="pf306b_") as td:
        f = Path(td) / "not_a_dir.txt"
        f.write_text("x", encoding="utf-8")
        try:
            _v0306_check_roots({"backup_roots": [{"label": "f", "path": str(f)}]})
            r = "NO_ERROR"
        except ValueError as exc:
            r = str(exc)
    try:
        _v0306_walk_error(PermissionError(13, "denied", "/x/locked"))
        w = "NO_ERROR"
    except ValueError as exc:
        w = str(exc)
    chk("T3 備份根是檔案 → BACKUP_ROOT_UNAVAILABLE;走訪中讀不了 → BACKUP_TRAVERSAL_ERROR 往上丟",
        r.startswith("BACKUP_ROOT_UNAVAILABLE") and w.startswith("BACKUP_TRAVERSAL_ERROR:PermissionError"), (r, w))
    node = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "_backup_v0306")
    walks = [c for c in ast.walk(node) if isinstance(c, ast.Call) and ast.unparse(c.func) == "os.walk"]
    chk("T4 抄入的 backup 節點:os.walk 都帶 onerror · 鎖前先查根 · 綁 v0300 全域 · 本檔不用 eval / exec",
        walks and all(any(k.arg == "onerror" for k in c.keywords) for c in walks) and "_v0306_check_roots(cfg)" in ast.unparse(node)
        and _backup_node.__globals__ is V300.__dict__ and V300.backup is backup
        and not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"eval", "exec"} for n in ast.walk(ast.parse(src))))
    chk("T5 綁定 / 子行程指本檔", V300.ENGINE_FILE == Path(__file__).name and Path(V300.__file__).resolve() == Path(__file__).resolve())
    newest = max(HERE.glob(STEM + "_v*.py"), key=_vnum).name
    guide = (HERE / "OPERATION_GUIDE.md").read_text(encoding="utf-8")
    index = V300.load(HERE.parent / "toolkit.index.json")
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    stale = re.findall(r"^\s*(?:python|&).*SuperEngine_v(\d{4})\.py", guide, re.M)
    chk("T6 (P1 延續)操作員入口指家族最新尾版(不寫死本檔版號):OPERATION_GUIDE 每一行指令 · README · toolkit.index",
        stale and all(f"{STEM}_v{v}.py" == newest for v in stale) and index.get("entrypoint", "").endswith(newest)
        and f"]({newest})" in readme and "C:\\Users\\" not in guide, (newest, stale, index.get("entrypoint")))
    import contextlib
    import io
    buf = io.StringIO()
    uninstall()
    try:
        with contextlib.redirect_stdout(buf):
            rc = PRIOR.selftest()
    finally:
        install()
    out = buf.getvalue()
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    pinned = "T4 (P1)操作員入口"                                  # v0305 的 T4 把文件釘在「v0305 自己」,文件換指 v0306 後必然不過
    only_pinned = bool(fails) and all(pinned in ln for ln in fails) and "Traceback" not in out and "自測 5/6 FAIL" in out
    chk("T7 前版 v0305 自測:全過,或只有「文件指 v0305 自己」那一行因文件改指 v0306 而不過(其餘 5 項含 v0300 原有 107 項照過)",
        rc == 0 or only_pinned, fails[:3])
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

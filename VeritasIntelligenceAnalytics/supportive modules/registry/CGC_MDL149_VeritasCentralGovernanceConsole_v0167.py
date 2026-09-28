#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL149_VeritasCentralGovernanceConsole v0167 — 薄尾:VCGC 活元件盤點快取(工作站 439 秒的根因)· 抬頭警告消音

工作站實錄(操作員 2026-09-28 R30,`via-vcgc go -Full -ApproveRegistrySync`):
  ① 每載入一次 v0166 就噴 `SyntaxWarning: invalid escape sequence '\V'`——v0166 抬頭把 `.\VIA-OperatorConsole.ps1` 寫進非 raw 的三引號
     (ENG072 v0135 同型,LL175:看久了會開始略過警告)。v0166 已併入 main,照 L04 不改它:本尾版抬頭改用 raw 三引號(r 前綴),
     載前一版時只對 SyntaxWarning 消音(行為零變更)。
  ② 流程閘那一步「439 秒 · 無輸出 281 秒」,操作員問「應該沒上加速器」。量過(容器剖析 status 25 秒):不是加速器——
     `live_components` 每跑一次就把約 580 支尾版檔整支 ast.parse + 走訪(12.8 秒;compile 590 次 · iter_fields 570 萬次),
     status / registry-sync 乾跑 / --apply 各算一遍;工作站在 OneDrive 夾、每讀一檔都被防毒掃,放大到幾百秒。加速器只管資料運算,管不到這段。
     本尾版:以 git 樹狀態(HEAD + `git status --porcelain -uall` + 每支改動 / 未追蹤檔的大小與時間)為鑰,把 live_components 的結果
     存在 VIA_Reports/vcgc/cache/(不入 git);樹沒變就直接用,變了照舊重算。VIA_VCGC_NOCACHE=1 一律重算。
     盤點結果一個欄位都不改(同一支函式算出來的 JSON 原樣存取),registry-sync 的只增律不受影響。
其餘動詞原樣轉給前一版(同夾同名、版號小於自己的最新一支)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
CACHE = VIA / "VIA_Reports" / "vcgc" / "cache"
KEEP = 3


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)           # v0166's header (merged; L04 keeps it as is)
    _spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def tree_key(root: Path = VIA) -> str | None:
    """HEAD + every changed / untracked path with its size and mtime. None when git is unavailable (then: no cache)."""
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=30).stdout.strip()
        st = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "."], cwd=root, capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return None
    if not head:
        return None
    top = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True).stdout.strip() or root)
    parts = [head]
    for line in st.splitlines():
        rel = line[3:].strip().strip('"')
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        p = top / rel
        try:
            s = p.stat()
            parts.append(f"{line[:2]}|{rel}|{s.st_size}|{s.st_mtime_ns}")
        except OSError:
            parts.append(f"{line[:2]}|{rel}|gone")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def cached(fn, name: str = "live_components", cache: Path = CACHE, key_fn=tree_key):
    def wrapper(*a, **k):
        if a or k or os.environ.get("VIA_VCGC_NOCACHE") == "1":
            return fn(*a, **k)
        key = key_fn()
        if key is None:
            return fn()
        f = cache / f"{name.upper()}_{key}.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        out = fn()
        try:
            cache.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
            old = sorted(cache.glob(f"{name.upper()}_*.json"), key=lambda q: q.stat().st_mtime)[:-KEEP]
            for q in old:
                q.unlink()
        except OSError:
            pass
        return out
    wrapper.__wrapped__ = fn
    return wrapper


def _install() -> int:
    """Swap the effective live_components in every loaded chain module that holds it (audit / registry_sync read their own globals)."""
    mods = [m for m in list(sys.modules.values()) if getattr(m, "__file__", "") and _STEM in str(getattr(m, "__file__", ""))]
    eff = None
    for m in mods:
        f = m.__dict__.get("live_components")
        if callable(f) and "audit" in m.__dict__:
            eff = f
            break
    if eff is None or getattr(eff, "__wrapped__", None):
        return 0
    wrapped = cached(eff)
    n = 0
    for m in mods:
        if m.__dict__.get("live_components") is eff:
            m.__dict__["live_components"] = wrapped
            n += 1
    return n


_PATCHED = _install()


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    calls = []

    def fake():
        calls.append(1)
        return {"rows": [{"key": "module|x"}], "counts": {"module": 1}}

    with tempfile.TemporaryDirectory() as td:
        keys = iter(["k1", "k1", "k2"])
        w = cached(fake, "t", Path(td), key_fn=lambda: next(keys))
        a, b, c = w(), w(), w()
        chk("樹沒變 = 用快取(同一份結果、只算一次);樹變了 = 重算", a == b == c and len(calls) == 2, f"算 {len(calls)} 次")
        os.environ["VIA_VCGC_NOCACHE"] = "1"
        try:
            w()
        finally:
            os.environ.pop("VIA_VCGC_NOCACHE", None)
        chk("VIA_VCGC_NOCACHE=1 一律重算", len(calls) == 3)
        chk("鑰拿不到(沒有 git)= 不用快取、照算", cached(fake, "t", Path(td), key_fn=lambda: None)() and len(calls) == 4)
        repo = Path(td) / "r"
        repo.mkdir()
        run = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True)
        run("init", "-q"); run("config", "user.email", "t@t"); run("config", "user.name", "t")
        (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
        run("add", "."); run("commit", "-qm", "a")
        k1 = tree_key(repo)
        (repo / "a.py").write_text("x = 2\n", encoding="utf-8")
        k2 = tree_key(repo)
        (repo / "b.py").write_text("y = 1\n", encoding="utf-8")
        k3 = tree_key(repo)
        chk("鑰:改一支檔、多一支未追蹤檔都會變", k1 and k1 != k2 != k3 and tree_key(repo) == k3)
    chk("接上:活元件盤點已換成快取版(audit / registry-sync 讀的那一份)", _PATCHED >= 1, f"換了 {_PATCHED} 處")
    head = Path(__file__).read_text(encoding="utf-8").split("\n", 3)[2]
    chk("抬頭是 raw 字串(不再噴 invalid escape)", head.startswith('r"""'))
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(selftest() if args == ["--selftest"] else main())

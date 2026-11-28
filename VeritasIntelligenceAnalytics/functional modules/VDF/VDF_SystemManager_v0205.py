#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0205 — 薄尾(v0204 以前一字不動):temp 副本「留最新一份 · 其餘逐檔相同才搬」

操作員 2026-11-28 定案:「同意留最新一份」。
  主機 tidy plan:temp/VDF_Manager_v0104/setup_* 5 份,每份 1761 檔、.py 1294 支,其中 707 支不在 git(舊管理器自己產的
  via_01_vdf 部署程式)→ git 證明不過,照規矩一份沒搬。5 份檔數一模一樣,多半是同一份的重複。
本版(只在 git 證明不過時才用):同一個 temp/VDF_Manager_v*/ 底下的副本裡,保留「最新的那一份」(檔案最晚修改時間最大者)
  在原位,列在「不搬 · 保留最新一份」;其餘每一份跟保留那份逐檔比對(相對路徑集合一樣 + 每檔 sha256 一樣),
  完全相同才算「重複副本」→ 搬進隔離區(只搬不刪,可 tidy undo);有任何一檔不同 → 照實列差幾檔,不搬。
  現役程式提到這條路徑(v0198 的 ①)仍然一律不搬。其餘照 v0204。零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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

import hashlib
import importlib.util
import os
import re
import sys
import tempfile
import time
from pathlib import Path

VERSION = "v0205"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0204
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _find_v198():
    m = PRIOR
    while m is not None:
        if "build_plan" in vars(m) and "apply_plan" in vars(m) and "temp_proof" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


V198 = _find_v198()
_ORIG_BUILD = V198.build_plan                                  # = v0201 的 build_plan(export 不搬)


def manifest(d: Path) -> tuple:
    """(相對路徑 → sha256, 最晚修改時間)。"""
    out, newest = {}, 0.0
    for f in sorted(d.rglob("*")):
        if f.is_file():
            h = hashlib.sha256()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            out[f.relative_to(d).as_posix()] = h.hexdigest()
            newest = max(newest, f.stat().st_mtime)
    return out, newest


def _rel(p: str, home: Path) -> str:
    try:
        return Path(p).relative_to(home).as_posix()
    except ValueError:
        return str(p)


def build_plan(home: Path, via: Path, code_dir: Path, tails_text: str, stamp: str) -> dict:
    plan = _ORIG_BUILD(home, via, code_dir, tails_text, stamp)
    temps = [i for i in plan["items"] if i["cat"] == "temp"]
    if not temps or all(i["ok"] for i in temps):
        return plan
    groups: dict = {}
    for i in temps:
        groups.setdefault(str(Path(i["src"]).parent), []).append(i)
    drop = set()
    for _parent, items in groups.items():
        if len(items) < 2:
            continue
        man = {i["src"]: manifest(Path(i["src"])) for i in items}
        keeper = max(items, key=lambda i: (man[i["src"]][1], i["src"]))
        km = man[keeper["src"]][0]
        drop.add(keeper["src"])
        plan["excluded"].append({"path": _rel(keeper["src"], home),
                                 "why": f"保留最新一份(最晚修改 {time.strftime('%Y-%m-%d %H:%M', time.localtime(man[keeper['src']][1]))} · {len(km)} 檔)"})
        for i in items:
            if i is keeper or i["ok"]:
                continue
            if "'mention': True" in i["note"] or "mention\": true" in i["note"]:
                continue                                       # 現役程式提到路徑 → 照舊不搬
            m = man[i["src"]][0]
            diff = len(set(m) ^ set(km)) + sum(1 for k in set(m) & set(km) if m[k] != km[k])
            if diff == 0:
                i["ok"], i["note"] = True, f"重複副本:與保留的 {Path(keeper['src']).name[:14]} 逐檔相同({len(m)} 檔 · sha256)"
            else:
                i["note"] = f"跟保留的 {Path(keeper['src']).name[:14]} 不同 {diff} 檔 → 不搬(不是重複副本)"
    plan["items"] = [i for i in plan["items"] if i["src"] not in drop]
    return plan


V198.build_plan = build_plan


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="vdf_sm205_") as td:
        d = Path(td)
        home, via = d / "home", d / "via"
        code = via / "functional modules" / "VDF"
        code.mkdir(parents=True)
        base = home / "temp" / "VDF_Manager_v0104"
        t0 = time.time() - 86400
        for n, (name, extra) in enumerate((("setup_a", ""), ("setup_b", ""), ("setup_c", ""), ("setup_d", "x"))):
            p = base / name / "via_01_vdf"
            p.mkdir(parents=True)
            (p / "only_here.py").write_text("y = 2\n" + extra, encoding="utf-8")   # 不在 git → git 證明不過
            (p / "a.json").write_text("{}", encoding="utf-8")
            for f in p.iterdir():
                os.utime(f, (t0 + n * 60, t0 + n * 60))
        os.utime(base / "setup_c" / "via_01_vdf" / "a.json", (t0 + 9999, t0 + 9999))   # c 最新
        os.environ["VIA_TIDY_QUARANTINE"] = str(d / "local" / "VIA_quarantine")
        try:
            plan = V198.build_plan(home, via, code, "", "T205")
        finally:
            os.environ.pop("VIA_TIDY_QUARANTINE", None)
        by = {Path(i["src"]).name: i for i in plan["items"] if i["cat"] == "temp"}
        kept = [e for e in plan["excluded"] if e["path"].endswith("setup_c")]
        chk("T2 留最新一份(c)在原位 · 與它逐檔相同的 a、b 改「重複副本」可搬 · 內容不同的 d 照實不搬",
            "setup_c" not in by and kept and by["setup_a"]["ok"] and by["setup_b"]["ok"] and not by["setup_d"]["ok"]
            and "不同 1 檔" in by["setup_d"]["note"], (list(by), [(k, v["ok"], v["note"][:60]) for k, v in by.items()], kept))
        r = V198.apply_plan(plan, {"temp"}, d / "L.jsonl")
        chk("T3 搬:只搬 a、b(保留的 c 與不同的 d 都在原位)· 每項記帳",
            sorted(Path(x["src"]).name for x in r["moved"]) == ["setup_a", "setup_b"] and (base / "setup_c").is_dir()
            and (base / "setup_d").is_dir() and not (base / "setup_a").exists(), r["moved"])
    V198.build_plan = _ORIG_BUILD                              # 前版自測看它自己的判法
    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    finally:
        V198.build_plan = build_plan
    chk("T4 前版 v0204 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

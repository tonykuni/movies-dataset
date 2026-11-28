#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF SystemManager v0200 — 薄尾(v0199 以前一字不動):PR #777 Codex P2「tidy 的計畫組裝讀 in_repo 欄位」

v0199 把 temp 證明換成「內容在 git 物件庫」,回傳欄位改叫 py_in_git;但 v0198 build_plan 組「證明過」那行附註時
  讀的是 pr['in_repo'] → 只要有一份副本通過證明,tidy plan / tidy apply(含 --only runs / backup,因為整份計畫先組完才篩類別)
  就丟 KeyError 中止。容器用 git 夾具重現。v0199 的自測只單獨測證明函式,沒把它裝進 build_plan 一起跑。
本版:證明結果補回 v0198 讀的欄位(in_repo = py_in_git · ratio = py_in_git / py),
  自測用 git 夾具把新證明裝進 build_plan 組一次計畫(含 --only 篩之前的整份)、再 apply / undo 一輪。其餘照 v0199。
零網路 · 不碰 TA-Lib · 不設同意閘 · 不 import VCGC。
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
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0200"
STEM = "VDF_SystemManager"
TAG = f"VDF_SystemManager {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0199
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


V199 = PRIOR
V198 = V199.V198
_GIT_PROOF = V199.temp_proof


def temp_proof(copy: Path, code_dir: Path, tails_text: str, repo: Path | None = None) -> dict:
    r = _GIT_PROOF(copy, code_dir, tails_text, repo)
    py, got = r.get("py", 0), r.get("py_in_git", 0)
    r.setdefault("in_repo", got)
    r.setdefault("ratio", round(got / py, 3) if py else 0.0)
    return r


V198.temp_proof = temp_proof


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版 {PRIOR_PATH.name} 自測 · git 夾具 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路橋在", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    with tempfile.TemporaryDirectory(prefix="vdf_sm200_") as td:
        d = Path(td)
        repo, home = d / "repo", d / "home"
        code = repo / "via" / "functional modules" / "VDF"
        code.mkdir(parents=True)
        (code / "x.py").write_bytes(b"x = 1\n")
        gitok = subprocess.run(["git", "init", "-q", str(repo)], capture_output=True).returncode == 0
        subprocess.run(["git", "-C", str(repo), "add", "-A"], capture_output=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=fx", "-c", "user.email=fx@example.invalid", "commit", "-qm", "fx"],
                       capture_output=True)
        cp = home / "temp" / "VDF_Manager_v0104" / "setup_a"
        cp.mkdir(parents=True)
        (cp / "x.py").write_bytes(b"x = 1\r\n")
        (home / "output_hub" / "ta_factory").mkdir(parents=True)
        (home / "output_hub" / "ta_factory" / "r.json").write_text("{}", encoding="utf-8")
        os.environ["VIA_TIDY_QUARANTINE"] = str(d / "local" / "VIA_quarantine")
        try:
            err = None
            try:
                plan = V198.build_plan(home, repo / "via", code, "", "T200")
            except Exception as exc:  # noqa: BLE001 — 這就是 Codex 指的那個例外
                err, plan = f"{type(exc).__name__}: {exc}", {"items": []}
            tmp = [i for i in plan["items"] if i["cat"] == "temp"]
            chk("T2 (Codex P2)新證明裝進 build_plan:通過的副本組得出計畫 · 附註「倉裡有 1」· 不丟 KeyError",
                gitok and err is None and tmp and tmp[0]["ok"] and "倉裡有 1" in tmp[0]["note"], (err, tmp))
            ledger = d / "L.jsonl"
            r = V198.apply_plan(plan, {"runs"}, ledger)
            u = V198.undo("T200", ledger)
            chk("T3 --only runs:整份計畫先組完不崩 · 只搬 runs(temp 不動)· undo 搬回",
                err is None and [x["cat"] for x in r["moved"]] == ["runs"] and cp.is_dir() and len(u["back"]) == 1
                and (home / "output_hub" / "ta_factory" / "r.json").is_file(), (r, u))
        finally:
            os.environ.pop("VIA_TIDY_QUARANTINE", None)
    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    finally:
        V198.temp_proof = temp_proof                          # v0199 自測結束會裝回它自己的;本版的再裝上
    chk("T4 前版 v0199 自測照過(含整條前版鏈)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

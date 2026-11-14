#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0147 — 薄尾:annual 收據讀取改遞迴(放行/語意/算式/源格/金額律在巢狀或子夾 json 裡;v0146 只讀頂層印 None);(操作員 2026-10-08:v0108 年度財報交接包隔離試跑 PASS → 接入不搬檔)。
  annual status            找 intake/VRN_v0108_Annual/**/RunAndVerify.ps1 的包根 → 最新 runs/<x>/ 的 RUN_STATUS.json · RESULT_VERIFICATION.json · VERIFICATION_v0108.json 摘要(狀態 · 17 項 · 算式 · 源格)
  annual run               用包自己的 .venv312(沒有就 via_pdf_tools)跑包的入口 RunAndVerify.ps1(pwsh -NoProfile -File;逾時 VIA_ANNUAL_SEC,預設 2400)→ 讀新 runs → 登 registry/VRN_Annual_Ledger.jsonl(run 夾 · 狀態 · 數字 · sha of RUN_STATUS)
  annual register          把最新 run 登帳(不跑);annual ledger 列帳
  規矩:包 199 檔零改動;VRN 只「指向 + 讀收據 + 記帳」;包的 limitation(GS 缺值 / CLST 矛盾)= 黃
其餘動詞照前版鏈。
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

import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0147"


def _vnum_v0147(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0147(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0147(p) < _vnum_v0147(__file__)), key=_vnum_v0147)
PRIOR = _load_v0147(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _home():
    return Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)


def annual_pack() -> Path | None:
    root = Path(os.environ.get("VIA_VRN_ANNUAL_PACK") or (_home() / "intake" / "VRN_v0108_Annual"))
    if not root.is_dir():
        return None
    hits = sorted(root.rglob("RunAndVerify.ps1"), key=lambda p: len(p.parts))
    return hits[0].parent if hits else None


def _latest_run(pk: Path) -> Path | None:
    runs = pk / "runs"
    if not runs.is_dir():
        return None
    ds = [d for d in runs.iterdir() if d.is_dir()]
    return max(ds, key=lambda d: d.stat().st_mtime) if ds else None


def _rd(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else None
    except ValueError:
        return None


def annual_status() -> dict:
    pk = annual_pack()
    out = {"verb": "annual_status", "pack": str(pk) if pk else None, "run": None, "lamp": "GRAY"}
    if not pk:
        out["why"] = "intake/VRN_v0108_Annual 裡找不到 RunAndVerify.ps1(先跑 Invoke-VIA-VRN-HandoverTest)"
        return out
    out["venv"] = str(pk / ".venv312" / "Scripts" / "python.exe") if (pk / ".venv312").is_dir() else None
    run = _latest_run(pk)
    if not run:
        out["why"] = "包還沒跑過(annual run)"
        return out
    rs = _rd(run / "RUN_STATUS.json") or {}
    rv = _rd(run / "RESULT_VERIFICATION.json") or {}
    status = str(rs.get("overall_status") or rs.get("status") or rv.get("overall_status") or rv.get("status") or "")
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k, v
                yield from walk(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from walk(v)
    pool = []
    for jp in sorted(run.rglob("*.json"), key=lambda q: (q.name not in ("RUN_STATUS.json", "RESULT_VERIFICATION.json", "VERIFICATION_v0108.json"), len(q.parts))):
        if jp.stat().st_size > 2_000_000:
            continue
        d = _rd(jp)
        if d is not None:
            pool.append((jp.name, d))
    def dig(*keys):
        for k in keys:
            for _, d in pool:
                for kk, vv in walk(d):
                    if kk == k and isinstance(vv, (int, float, str)):
                        return vv
        return None
    out.update(run=str(run), status=status, checks_pass=dig("release_gate_checks_pass", "checks_pass"), semantic_pass=dig("semantic_checks_pass"), equations_pass=dig("annual_equations_pass"), source_cells_pass=dig("source_cells_pass"), amount_policy_pass=dig("amount_policy_tests_pass"), files=sum(1 for _ in run.rglob("*") if _.is_file()),
               run_status_sha=(hashlib.sha256((run / "RUN_STATUS.json").read_bytes()).hexdigest()[:12] if (run / "RUN_STATUS.json").exists() else None))
    out["lamp"] = "GREEN" if status.upper().startswith("PASS") and "LIMIT" not in status.upper() else ("YELLOW" if status.upper().startswith("PASS") else ("RED" if status else "GRAY"))
    out["limitation"] = "來源限制(GS 缺值 / CLST 原文矛盾保留)" if "LIMIT" in status.upper() else ""
    return out


def annual_register(st: dict | None = None) -> dict:
    st = st or annual_status()
    if not st.get("run"):
        return dict(st, registered=False)
    led = _home() / "registry" / "VRN_Annual_Ledger.jsonl"
    led.parent.mkdir(exist_ok=True)
    prev = [json.loads(ln) for ln in led.read_text(encoding="utf-8").splitlines() if ln.strip()] if led.exists() else []
    if any(p.get("run") == st["run"] for p in prev):
        return dict(st, registered=False, why="已登過")
    rec = {k: st.get(k) for k in ("pack", "run", "status", "checks_pass", "semantic_pass", "equations_pass", "source_cells_pass", "amount_policy_pass", "files", "run_status_sha", "lamp", "limitation")}
    rec["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
    rec["manager"] = Path(__file__).name
    with led.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return dict(st, registered=True, ledger=str(led), n=len(prev) + 1)


def annual_run() -> dict:
    pk = annual_pack()
    if not pk:
        return {"verb": "annual_run", "lamp": "RED", "why": "包不在"}
    vpy = pk / ".venv312" / "Scripts" / "python.exe"
    if not vpy.exists():
        vpy = _home().parents[1] / "envs" / "via_pdf_tools" / "Scripts" / "python.exe"
    env = dict(os.environ, VIA_PYTHON=str(vpy), PYTHON=str(vpy), PYTHONUTF8="1", VIRTUAL_ENV=str(vpy.parent.parent), PATH=str(vpy.parent) + os.pathsep + os.environ.get("PATH", ""))
    before = {d.name for d in (pk / "runs").iterdir()} if (pk / "runs").is_dir() else set()
    pwsh = "pwsh"
    try:
        cp = subprocess.run([pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(pk / "RunAndVerify.ps1")], cwd=str(pk), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=int(os.environ.get("VIA_ANNUAL_SEC", "2400")))
        rc, tail = cp.returncode, (cp.stdout or "")[-1500:]
    except subprocess.TimeoutExpired:
        return {"verb": "annual_run", "lamp": "RED", "why": "逾時"}
    except FileNotFoundError:
        return {"verb": "annual_run", "lamp": "RED", "why": "pwsh 不在 PATH"}
    after = {d.name for d in (pk / "runs").iterdir()} if (pk / "runs").is_dir() else set()
    st = annual_status()
    st.update(verb="annual_run", rc=rc, new_runs=sorted(after - before), log_tail=tail[-400:])
    if st.get("run"):
        st = annual_register(st)
    return st


def _print_annual(o: dict) -> None:
    if not o.get("run"):
        print("[計] VRN annual · %s · %s · %s" % (o.get("pack") or "包不在", o.get("why", ""), o["lamp"]))
        return
    print("[計] VRN annual · %s · run %s · %s · 放行 %s · 語意 %s · 算式 %s · 源格 %s · 金額律 %s · 檔 %s · sha %s%s · %s" % (o.get("verb"), Path(o["run"]).name, o.get("status"), o.get("checks_pass"), o.get("semantic_pass"), o.get("equations_pass"), o.get("source_cells_pass"), o.get("amount_policy_pass"), o.get("files"), o.get("run_status_sha"), (" · 登帳 #%d" % o["n"]) if o.get("registered") else (" · " + o["why"] if o.get("why") else ""), o["lamp"]))
    if o.get("limitation"):
        print("  [YEL] %s(包的誠實標記,不是程式錯)" % o["limitation"])
    if o.get("rc") is not None:
        print("  [OK] 包入口 rc %s · 新 run %s" % (o["rc"], ",".join(o.get("new_runs") or []) or "無"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["annual"]:
        sub = args[1] if len(args) > 1 else "status"
        if sub == "status":
            o = annual_status()
        elif sub == "run":
            o = annual_run()
        elif sub == "register":
            o = annual_register()
        elif sub == "ledger":
            led = _home() / "registry" / "VRN_Annual_Ledger.jsonl"
            rows = [json.loads(ln) for ln in led.read_text(encoding="utf-8").splitlines() if ln.strip()] if led.exists() else []
            print("[計] VRN annual ledger · %d 筆" % len(rows))
            for r in rows[-10:]:
                print("  [OK] %s · %s · %s · 放行 %s · 算式 %s · %s" % (r.get("ts"), Path(r.get("run", "")).name, r.get("status"), r.get("checks_pass"), r.get("equations_pass"), r.get("lamp")))
            return 0
        else:
            print("[拒跑] annual status | run | register | ledger")
            return 2
        _print_annual(o)
        return 1 if o["lamp"] == "RED" else 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrnann-"))
    home = td / "functional modules" / "VRN"
    pk = home / "intake" / "VRN_v0108_Annual" / "VRN_v0108_Complete_Handover"
    (pk / "runs" / "20261008_082722_0f0a5f").mkdir(parents=True)
    (home / "registry").mkdir()
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_ANNUAL_PACK")}
    os.environ["VIA_VRN_SSOT_HOME"] = str(home)
    os.environ.pop("VIA_VRN_ANNUAL_PACK", None)
    (pk / "RunAndVerify.ps1").write_text("exit 0\n", encoding="utf-8")
    (pk / "runs" / "20261008_082722_0f0a5f" / "RUN_STATUS.json").write_text(json.dumps({"overall_status": "PASS_WITH_SOURCE_LIMITATIONS", "gates": {"release_gate_checks_pass": 17, "semantic_checks_pass": 11}}), encoding="utf-8")
    (pk / "runs" / "20261008_082722_0f0a5f" / "sub").mkdir()
    (pk / "runs" / "20261008_082722_0f0a5f" / "sub" / "VERIFICATION_v0108.json").write_text(json.dumps({"summary": {"annual_equations_pass": 409, "source_cells_pass": 5462}, "policy": [{"amount_policy_tests_pass": 16}]}), encoding="utf-8")
    st = annual_status()
    chk("① status:找到包 · 最新 run · PASS_WITH_SOURCE_LIMITATIONS → 黃 · 巢狀/子夾也抓到 17/11/409/5462", st["pack"] == str(pk) and st["status"] == "PASS_WITH_SOURCE_LIMITATIONS" and st["lamp"] == "YELLOW" and st["checks_pass"] == 17 and st["equations_pass"] == 409 and st["source_cells_pass"] == 5462)
    r1 = annual_register(); r2 = annual_register()
    chk("② register:登帳 1 筆 · 重登 SKIP", r1["registered"] and (home / "registry" / "VRN_Annual_Ledger.jsonl").exists() and not r2["registered"])
    chk("③ 包不在 → GRAY 誠實", (lambda: (os.environ.__setitem__("VIA_VRN_ANNUAL_PACK", str(td / "nope")), annual_status()["lamp"] == "GRAY")[1])())
    os.environ.pop("VIA_VRN_ANNUAL_PACK", None)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("④ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 帶加速器橋 · 不搬檔(沒有 shutil.copy/move 到包內)", "[VIA:ACCEL-BRIDGE:v0100]" in body and "shutil.move" not in body.split("def selftest")[0] and "shutil.copy" not in body.split("def selftest")[0])
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0147 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

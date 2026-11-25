#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_LocalIntegrateLaunch v0101 — 薄尾(v0100 一字不動):先經 VCGC 檢視 / 安裝全部工具無衝突,再進 via_vdf 境跑整合

操作員 2026-11-25 桌機實跑 v0100 的 PS 一行:「[RED] 找不到 via_vdf 環境的 python」「用 VCGC 檢視安裝所有工具無衝突」。
根因:PS 只猜 miniconda3 / anaconda3 兩個路徑;正本找法是 Register-VIA-Commands 的 Get-VIAEnvPython
(覆寫 VIA_PY_VDF → 境名 via_vdf_312 · via_vdf · via_vdf_313 · via_vdf_311 · .venv-via_vdf × 根 VIA_ENV_ROOT · VIA_ENV_ROOTS ·
 ~/envs · ~/miniconda3/envs · ~/Miniconda3/envs · ~/anaconda3/envs · ~/.virtualenvs · <VIA>/Environments · <VIA>)。
本版(PS 只用 base python 啟動本檔,其餘全在這裡):
  0 同步倉        v0100 的 sync(VIA_HostBoot --dry)
  1 VCGC 健康     VCGC_CommandHub 尾版 health(= via-health:VCGC doctor 裝前檢查 → 經安裝閘 CGC_MDL056 只裝 doctor 計畫列的、
                  你輸入 YES 才開同意閘(只在子行程)→ 裝後重驗;envmgr · VDF health 並行)。rc 0 綠 · 2 黃續做 · 其他 = 紅停(前一步不過後一步不做)
  2 進 via_vdf 境 照上面正本找法(再加 conda env list);找不到 = 紅停,只印建境指令(AI 不建境、不刪境)
  3 整合          用 via_vdf 的 python 跑 v0100(並行三步盤點 → task.md → 本機 claude -p),帶 --no-sync
用法:python VDF_LocalIntegrateLaunch_v0101.py --repo <倉> [--skip-health] [--env-only] [--no-sync] [v0100 參數:--cand --db --max-turns --dry]
      python VDF_LocalIntegrateLaunch_v0101.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STEM = "VDF_LocalIntegrateLaunch"
VERSION = "v0101"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve()
ENV_NAMES = ["via_vdf_312", "via_vdf", "via_vdf_313", "via_vdf_311", ".venv-via_vdf"]   # Get-VIAEnvPython 的 vdf 別名序
ENV_SUBS = [("Scripts", "python.exe"), ("python.exe",), ("bin", "python3"), ("bin", "python")]


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
say = PRIOR.say


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- 環境
def conda_env_dirs() -> list:
    exe = shutil.which("conda") or shutil.which("conda.bat")
    if not exe:
        return []
    try:
        r = subprocess.run([exe, "env", "list", "--json"], capture_output=True, text=True, timeout=30)
        return [Path(p) for p in json.loads(r.stdout or "{}").get("envs", [])]
    except Exception as e:  # noqa: BLE001 - conda 壞掉不擋,照實印
        say(f"  conda env list 失敗({type(e).__name__}),只用固定根")
        return []


def env_roots(code_root: Path) -> list:
    home = Path.home()
    roots = [os.environ.get("VIA_ENV_ROOT", "")] + os.environ.get("VIA_ENV_ROOTS", "").split(";")
    roots += [home / "envs", home / "miniconda3" / "envs", home / "Miniconda3" / "envs", home / "anaconda3" / "envs",
              home / ".virtualenvs", code_root / "Environments", code_root]
    seen, out = set(), []
    for r in roots:
        if r and Path(r).is_dir() and str(Path(r)) not in seen:
            seen.add(str(Path(r)))
            out.append(Path(r))
    return out


def find_vdf_python(code_root: Path):
    """回 (python 路徑 | None, 找過的根)。順序照 Get-VIAEnvPython:覆寫 → 根 × 境名 × 子路徑 → conda env list。"""
    ov = os.environ.get("VIA_PY_VDF", "")
    if ov and Path(ov).is_file():
        return Path(ov), ["VIA_PY_VDF"]
    roots = env_roots(code_root)
    for r in roots:
        for n in ENV_NAMES:
            for sub in ENV_SUBS:
                p = r.joinpath(n, *sub)
                if p.is_file():
                    return p, [str(x) for x in roots]
    for d in conda_env_dirs():
        if d.name in ENV_NAMES:
            for sub in ENV_SUBS:
                p = d.joinpath(*sub)
                if p.is_file():
                    return p, [str(x) for x in roots] + ["conda env list"]
    return None, [str(x) for x in roots] + ["conda env list"]


# ---------------------------------------------------------------- VCGC 健康(via-health)
def hub_tail(code_root: Path):
    hs = sorted(code_root.glob("VCGC_CommandHub_v*.py"), key=_vnum)
    return hs[-1] if hs else None


def run_health(code_root: Path, py: str = "") -> int:
    hub = hub_tail(code_root)
    if hub is None:
        say("[RED] 找不到 VCGC_CommandHub 尾版(倉沒同步到?)")
        return 3
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", VIA_CODE_ROOT=str(code_root))
    env.setdefault("VIA_ROOT", str(code_root))   # 使用者層 VIA_ROOT 有設就照它(資料根),沒設才用程式根
    env.pop("VIA_FROM_VCGC", None)                # 交給中樞 / FastRun 自己經 VCGC 過閘
    say(f"1 VCGC 健康:{hub.name} health(doctor → 安裝閘 YES 才裝 → 重驗;全文 VIA_Reports/fastrun/)")
    return subprocess.run([py or sys.executable, str(hub), "health"], cwd=str(code_root), env=env).returncode


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    own = {"--skip-health", "--env-only", "--no-sync"}
    flags = {a for a in argv if a in own}
    rest = [a for a in argv if a not in own]
    if "--repo" not in rest:
        say("[RED] 要 --repo <倉>")
        return 1
    i = rest.index("--repo")
    repo = Path(rest[i + 1]).expanduser().resolve()
    del rest[i:i + 2]
    code_root = repo / "VeritasIntelligenceAnalytics"
    if not code_root.is_dir():
        say(f"[RED] 不是 VIA 倉:{repo}")
        return 1
    say(f"{TAG} · 倉 {repo} · base python {sys.executable} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'}")
    lamps = []
    if "--no-sync" not in flags:
        say("0 同步倉(VIA_HostBoot --dry)")
        s = PRIOR.sync(repo)
        say("0 同步 · " + s)
        lamps.append(s.split("(")[0])
    if "--skip-health" not in flags:
        rc = run_health(code_root)
        lamp = {0: "GREEN", 2: "YELLOW", 3: "YELLOW"}.get(rc, "RED")     # 3 = VCGC 中樞不在 → 退路:跳過健康檢查,VDF 照常(系統獨立)
        say(f"1 VCGC 健康 · rc {rc} · {lamp}" + (" · VCGC 不在:跳過(退路),VDF 照常" if rc == 3 else ""))
        if lamp == "RED":
            say("[停] 環境健康沒過,不進整合。照上面 doctor 列的處理(衝突境重建:via-envgov plan → 你下 via-envgov apply --approve)")
            return 1
        lamps.append(lamp)
    py, tried = find_vdf_python(code_root)
    if py is None:
        say("[RED] 找不到 via_vdf 境(找過:" + " · ".join(tried) + ")")
        say("  已有境在別處 → 設 VIA_PY_VDF=<該境 python.exe> 再跑;沒有 → via-envgov plan 看建境計畫,由你下 via-envgov apply --approve")
        return 1
    say(f"2 via_vdf 境:{py}")
    if "--env-only" in flags:
        say("--env-only:到此為止")
        return 2 if "YELLOW" in lamps else 0
    say(f"3 整合:{py.name} {PRIOR_PATH.name}")
    rc = subprocess.run([str(py), str(PRIOR_PATH), "--repo", str(repo), "--no-sync", *rest], cwd=str(repo),
                        env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", VIA_REPO=str(repo))).returncode
    if rc == 0 and "YELLOW" in lamps:
        return 2
    return rc


# ---------------------------------------------------------------- 自測(全在暫存夾造資料)
def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("前版經 glob 載入(v0100)", PRIOR_PATH.name == STEM + "_v0100.py" and callable(getattr(PRIOR, "step_a", None)))
    chk("TAILAPI 轉接前版公開名稱", __getattr__("build_task") is PRIOR.build_task)
    keep = {k: os.environ.get(k) for k in ("VIA_PY_VDF", "VIA_ENV_ROOT", "VIA_ENV_ROOTS", "PATH")}
    try:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            code = td / "repo" / "VeritasIntelligenceAnalytics"
            code.mkdir(parents=True)
            r1 = td / "envs"
            for n in ("via_vdf", "via_vdf_312"):
                (r1 / n / "Scripts").mkdir(parents=True)
                (r1 / n / "Scripts" / "python.exe").write_text("", encoding="utf-8")
            os.environ["VIA_ENV_ROOT"] = str(r1)
            os.environ.pop("VIA_PY_VDF", None)
            os.environ["PATH"] = ""                       # 沒有 conda:只走固定根
            p, _ = find_vdf_python(code)
            chk("別名序:via_vdf_312 先於 via_vdf", p == r1 / "via_vdf_312" / "Scripts" / "python.exe", str(p))
            os.environ["VIA_PY_VDF"] = str(r1 / "via_vdf" / "Scripts" / "python.exe")
            chk("VIA_PY_VDF 覆寫最優先", find_vdf_python(code)[0] == r1 / "via_vdf" / "Scripts" / "python.exe")
            os.environ.pop("VIA_PY_VDF")
            os.environ["VIA_ENV_ROOT"] = str(td / "none")
            p2, tried = find_vdf_python(code)
            chk("找不到 = None 且列出找過的根", p2 is None and "conda env list" in tried)
            chk("沒有中樞 = rc 3", run_health(code) == 3)
            os.environ["VIA_PY_VDF"] = sys.executable
            chk("沒有 VCGC 中樞 → 退路(黃)照常往下", main(["--repo", str(code.parent), "--no-sync", "--env-only"]) == 2)
            os.environ.pop("VIA_PY_VDF")
            (code / "VCGC_CommandHub_v0100.py").write_text("import sys\nsys.exit(9)\n", encoding="utf-8")
            (code / "VCGC_CommandHub_v0116.py").write_text(
                "import os, sys\nassert sys.argv[1:] == ['health'] and 'VIA_FROM_VCGC' not in os.environ\n"
                "sys.exit(int(os.environ.get('FAKE_RC', '0')))\n", encoding="utf-8")
            os.environ["VIA_FROM_VCGC"] = "YES"
            os.environ["FAKE_RC"] = "2"
            chk("健康走中樞尾版 health · 拿掉 VIA_FROM_VCGC", run_health(code) == 2)
            os.environ["FAKE_RC"] = "1"
            chk("健康紅 = 停,不進整合", main(["--repo", str(code.parent), "--no-sync"]) == 1)
            os.environ["FAKE_RC"] = "0"
            os.environ["VIA_PY_VDF"] = sys.executable
            chk("--env-only 綠", main(["--repo", str(code.parent), "--no-sync", "--env-only"]) == 0)
            cand, db = td / "cand", td / "db"
            cand.mkdir()
            db.mkdir()
            (cand / "e.py").write_text("import httpx\ndef fetch(t):\n    pass\n", encoding="utf-8")
            (code / "functional modules" / "VDF" / "engine").mkdir(parents=True)
            (code / "functional modules" / "VDF" / "VDF_SystemManager_v0191.py").write_text("'''m'''\n", encoding="utf-8")
            rc = main(["--repo", str(code.parent), "--no-sync", "--cand", str(cand), "--db", str(db), "--dry"])
            outs = sorted((code.parent / PRIOR.OUT_REL).glob("2*"))
            chk("端到端:健康 → 找境 → 前版 --dry 寫出 task.md", rc in (0, 2) and outs and (outs[-1] / "task.md").exists(), f"rc {rc}")
            os.environ.pop("VIA_FROM_VCGC", None)
            os.environ.pop("FAKE_RC", None)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

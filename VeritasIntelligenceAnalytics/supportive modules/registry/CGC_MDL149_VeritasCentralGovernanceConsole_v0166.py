#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0166 — 薄尾:`via-vcgc go` 從 VCGC 直接啟動一切

操作員 2026-09-28 R28:「直接透過 VCGC 路徑啟動一切」。
v0165 以前整條流程(流程閘 → ENV MANAGER → 註冊同步 → 換模板 → VDF 建庫 → 全景實測 → Parquet → 操作台 → 單一路徑驗證 →
布建紀錄上傳 → 簡單版 HTML)只能從倉根 `.\VIA-OperatorConsole.ps1` 進。本尾版多收一個動詞:
  via-vcgc go [-SkipSweep] [-NoOpen] [-BuildDb|-NoBuild] [-ApproveRegistrySync] [-TemplateIn <檔>] [-NoUpload]
              [-DataDir <夾>] [-SystemDir <夾>] [-Pick]            (別名 all · run-all)
→ 找 VeritasIntelligenceAnalytics 下 Invoke-VIA-OperatorConsole-v*.ps1 的**尾版**,用 PowerShell 7 跑它,參數原樣轉;
  輸出直接接到畫面(不截留),對話框(選夾 · 批准 · 換模板 · 上傳)照常跳。**編排只有那一支 PowerShell**(一把尺):
  本動詞只負責「從 VCGC 進」,不另寫第二份流程。找不到 pwsh = 照實 ABSENT(補法:裝 PowerShell 7 / 設 VIA_PWSH)。
  全程通常超過 Invoke-VIAPython 預設逾時 1800s:開跑前若 VIA_PY_TIMEOUT_SEC 小於 7200 就印一行提醒。
其餘動詞原樣轉給前一版(= 同夾同名、版號小於自己的最新一支)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
GO_VERBS = ("go", "all", "run-all")
ENTRY_GLOB = "Invoke-VIA-OperatorConsole-v*.ps1"
SWITCHES = ("SkipSweep", "NoOpen", "BuildDb", "NoBuild", "ApproveRegistrySync", "NoUpload", "Pick")
VALUED = ("TemplateIn", "DataDir", "SystemDir", "ApplyInput")


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _pvnum(path: Path) -> int:
    match = re.search(r"-v(\d+)$", path.stem)                 # PowerShell entry names use -vNNNN
    return int(match.group(1)) if match else -1


def entry_tail(via: Path = VIA) -> Path | None:
    hits = [p for p in via.glob(ENTRY_GLOB) if _pvnum(p) >= 0]
    return max(hits, key=_pvnum) if hits else None


def find_pwsh() -> str | None:
    env = os.environ.get("VIA_PWSH")
    if env and Path(env).exists():
        return env
    return shutil.which("pwsh") or shutil.which("pwsh.exe")


def map_args(args: list) -> tuple:
    """`-Name` / `--name` / `name=value` forms → the entry's own PowerShell parameters; unknown ones are reported, not guessed."""
    out, unknown, i = [], [], 0
    while i < len(args):
        tok = str(args[i])
        name, _, val = tok.lstrip("-").partition("=")
        hit = next((s for s in SWITCHES if s.lower() == name.lower()), None)
        if hit:
            out.append("-" + hit)
        else:
            hit = next((s for s in VALUED if s.lower() == name.lower()), None)
            if hit and (val or i + 1 < len(args)):
                if not val:
                    i += 1
                    val = str(args[i])
                out += ["-" + hit, val]
            else:
                unknown.append(tok)
        i += 1
    return out, unknown


def go(args: list, runner=subprocess.run) -> int:
    entry = entry_tail()
    if entry is None:
        print(json.dumps({"via": "vcgc", "verb": "go", "state": "ABSENT", "why": ENTRY_GLOB + " 不在(先 git pull)"}, ensure_ascii=False))
        return 2
    pwsh = find_pwsh()
    if pwsh is None:
        print(json.dumps({"via": "vcgc", "verb": "go", "state": "ABSENT",
                          "why": "找不到 PowerShell 7(pwsh):裝好放進 PATH,或設 VIA_PWSH=<pwsh.exe 路徑>"}, ensure_ascii=False))
        return 2
    passed, unknown = map_args(args)
    if unknown:
        print(f"  [via-vcgc go] 不認得的參數(不轉):{' '.join(unknown)}")
    try:
        t = int(os.environ.get("VIA_PY_TIMEOUT_SEC") or 1800)
    except ValueError:
        t = 1800
    if t < 7200:
        print(f"  [via-vcgc go] 提醒:全程常超過 {t}s(Invoke-VIAPython 逾時);要放寬:$env:VIA_PY_TIMEOUT_SEC=7200 後再 via-vcgc go")
    print(f"  [via-vcgc go] VCGC → {entry.name}(PowerShell {Path(pwsh).name})" + (f" · {' '.join(passed)}" if passed else ""))
    sys.stdout.flush()
    r = runner([pwsh, "-NoProfile", "-File", str(entry)] + passed, cwd=str(VIA))
    return int(getattr(r, "returncode", 1) or 0)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] and args[0] in GO_VERBS:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
            return 2
        return go(args[1:])
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    passed, unknown = map_args(["-SkipSweep", "--noopen", "-DataDir", r"D:\data", "TemplateIn=x.css", "-Bogus"])
    chk("go 參數:-X / --x / x=v 都轉成入口自己的參數;不認得的照實列出不轉",
        passed == ["-SkipSweep", "-NoOpen", "-DataDir", r"D:\data", "-TemplateIn", "x.css"] and unknown == ["-Bogus"], passed)
    e = entry_tail()
    chk("入口取尾版(Invoke-VIA-OperatorConsole-v*.ps1 版號最大者)", e is not None and _pvnum(e) == max(_pvnum(p) for p in VIA.glob(ENTRY_GLOB)),
        e.name if e else "ABSENT")
    seen = {}

    class R:
        returncode = 0

    def fake(argv, cwd=None):
        seen["argv"] = argv
        return R()

    keep = os.environ.get("VIA_PWSH")
    os.environ["VIA_PWSH"] = sys.executable                     # any existing file stands in for pwsh; the fake runner never runs it
    try:
        rc = go(["-NoOpen"], runner=fake)
    finally:
        if keep is None:
            os.environ.pop("VIA_PWSH", None)
        else:
            os.environ["VIA_PWSH"] = keep
    chk("go 只是從 VCGC 進:叫尾版入口一次,參數原樣轉(編排仍只有那一支 PowerShell)",
        rc == 0 and seen.get("argv", [None])[-1] == "-NoOpen" and str(seen["argv"][3]).endswith(".ps1") and seen["argv"][1] == "-NoProfile")
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        chk("go 不經 VCGC 就拒跑", main(["go"]) == 2)
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    body = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0].split('"""', 2)[-1]
    chk("本支沒有字串釘死任何版號檔名", not re.search(r"_v\d{4}\.(py|ps1)", body))
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(selftest() if args == ["--selftest"] else main())

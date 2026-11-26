#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL022_SafeParallelLaunch v0110 — 薄尾(v0100–v0109 一字不動):開跑前 ⓪ 暫存庫併入資料家 · 印擷取家

操作員 2026-11-26:「資料庫是否與 …\via_database\vdf_database 相同 · 若不同則整合 · 是否有增量擷取 · 有無重複擷取」
「接入排程優化加速器 · 不傷電腦不傷系統 · PS 啟動、主要功能寫在 py」。
本支本來就是 VDF 的排程啟動器(前版鏈:環境檢查 → 降壓 BELOW_NORMAL + IO LOW · 執行緒 / DuckDB 記憶體上限 → 3 道並行 + 監工
過熱減道 → 橋閘(加速器 + 網路工具)→ 增量擷取 → 矩陣)。本版只在 run 最前面加一步:
  ⓪ ① 印擷取家(VDF_MDL012_FetchGroups 尾版 home;v0113 起沒指定就寫資料家,不再落倉內暫存)
    ② VDF_MDL023_StageMerge 尾版:倉內暫存庫(上一輪落錯地方的列)只補缺併進資料家同名庫;--dry 只列計畫;--no-merge 跳過。
       子行程帶 VDF 入口旗標(本支就是 VDF 入口);合併燈併入總燈(紅留紅)。
其餘(含 --start 對範圍冊、跑完 Rich 矩陣)照 v0109。不代設同意閘;不碰 TA-Lib。
另加(PR #763 Codex):
  · run 先用前版 via_db_args 正規化參數(--via-db <根> → --data-home <根>/vdf_database)再轉絕對路徑,⓪ 與主流程用同一個資料家。
  · 新動詞 launch:開跑前檢查(找倉 · 分支 · Python · 加速器真的載到 · 網路工具 · 同意閘)+ 動畫 + 結果框都在 Python;
    PS(Start-VIA-VDF)只找到本檔、原樣轉交參數。launch 沒給 --start = 2018-01-01;--check 只做檢查;--plain 不用色彩動畫。
用法:run [--data-home <夾> | --via-db <根>] [--start 2018-01-01] [--dry] [--no-merge] … · launch [同 run] [--check] [--plain] · matrix … · --selftest
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

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0110"
TAG = f"{STEM} {VERSION}"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def worse(*rcs) -> int:                                # 0 綠 < 2 黃 < 1 紅
    rank = {0: 0, 2: 1, 1: 2}
    return max(rcs, key=lambda x: rank.get(x, 2)) if rcs else 0


def _tail(pat: str):
    hits = sorted(HERE.glob(pat), key=_vnum)
    return hits[-1] if hits else None


def norm_args(args: list) -> list:
    """前版 via_db_args(--via-db → --data-home <根>/vdf_database)+ --data-home 轉絕對路徑(子行程換工作目錄也指同一處)。"""
    a = list(PRIOR.via_db_args(list(args))) if callable(getattr(PRIOR, "via_db_args", None)) else list(args)
    if "--data-home" in a and a.index("--data-home") + 1 < len(a):
        i = a.index("--data-home") + 1
        a[i] = str(Path(a[i]).expanduser().resolve())
    return a


def stage_steps(args: list) -> list:
    """⓪ 的子行程(不跑,只組):擷取家 → 暫存併入。"""
    dh = PRIOR._opt(args, "--data-home")
    fg, sm = _tail("VDF_MDL012_FetchGroups_v*.py"), _tail("VDF_MDL023_StageMerge_v*.py")
    steps = []
    if fg:
        steps.append(("擷取家", [sys.executable, "-X", "utf8", str(fg), "home"]))
    if sm and "--no-merge" not in args:
        verb = "plan" if "--dry" in args else "apply"
        steps.append(("暫存併入資料家", [sys.executable, "-X", "utf8", str(sm), verb] + (["--home", dh] if dh else [])))
    return steps


def run_stage(args: list, runner=None) -> int:
    runner = runner or (lambda cmd, env: subprocess.run(cmd, env=env, cwd=str(HERE)).returncode)
    env = dict(os.environ, VIA_FROM_VDFSM="YES", PYTHONUTF8="1")
    dh = PRIOR._opt(args, "--data-home")
    if dh:
        env["VIA_VDF_DB_HOME"] = str(dh)               # 跟前版 run 帶給子行程的同一個資料家
    rc = 0
    for title, cmd in stage_steps(args):
        print(f"=== ⓪ {title} · {Path(cmd[3]).name} {' '.join(cmd[4:])} ===", flush=True)
        r = runner(cmd, env)
        rc = worse(rc, r if r in (0, 1, 2) else 1) if title != "擷取家" else worse(rc, 0 if r == 0 else 2)
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] == ["launch"]:
        return launch(args[1:])
    if args[:1] != ["run"]:
        return PRIOR.main(args)
    args = norm_args(args)
    rc0 = run_stage(args)
    rest = [a for a in args if a != "--no-merge"]
    rc = PRIOR.main(rest)
    out = worse(rc, rc0)
    print(f"[{TAG}] ⓪ 暫存併入 rc {rc0} · 主流程 rc {rc} → 總 rc {out}", flush=True)
    return out


# ───────── launch:開跑前檢查 + 動畫 + 結果框(PS 只轉交)─────────
ESC = "\x1b"
FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


def _rgb(text: str, rgb: tuple, vt: bool) -> str:
    return f"{ESC}[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{text}{ESC}[0m" if vt else text


def _gradient(text: str, a: tuple, b: tuple, vt: bool) -> str:
    if not vt:
        return text
    n = max(1, len(text) - 1)
    return "".join(f"{ESC}[38;2;{int(a[0] + (b[0] - a[0]) * i / n)};{int(a[1] + (b[1] - a[1]) * i / n)};{int(a[2] + (b[2] - a[2]) * i / n)}m{ch}"
                   for i, ch in enumerate(text)) + f"{ESC}[0m"


def _box(title: str, lines: list, rgb: tuple, vt: bool) -> str:
    w = 66
    out = [_rgb("╭─ " + title + " " + "─" * max(0, w - len(title) - 4) + "╮", rgb, vt)]
    out += [_rgb("│ ", rgb, vt) + ln for ln in lines]
    out.append(_rgb("╰" + "─" * (w - 1) + "╯", rgb, vt))
    return "\n".join(out)


def preflight(env=None, git_runner=None) -> list:
    """開跑前檢查(純資料,不畫):[(名稱, 狀態 ok/warn/fail, 說明)]。"""
    env = os.environ if env is None else env
    via = HERE.parents[1]
    out = [("找倉(VIA 根)", "ok" if (via / "functional modules" / "VDF").is_dir() else "fail", str(via))]
    try:
        br = (git_runner or (lambda: subprocess.run(["git", "-C", str(via), "rev-parse", "--abbrev-ref", "HEAD"],
                                                    capture_output=True, text=True, timeout=20).stdout.strip()))()
    except Exception:  # noqa: BLE001 — 沒 git 照跑
        br = ""
    if not br:
        out.append(("倉狀態(分支)", "warn", "不是 git 倉或沒 git(照跑)"))
    elif br == "HEAD":
        out.append(("倉狀態(分支)", "warn", "沒在分支上(detached;上次中斷留下的)→ git switch main 再 git pull"))
    else:
        out.append(("倉狀態(分支)", "ok", f"分支 {br}"))
    out.append(("Python", "ok" if sys.version_info >= (3, 10) else "warn", sys.version.split()[0]))
    out.append(("加速器真的載到", "ok" if VIA_ACCEL is not None else "warn", "VIA_SuperAccel_Module" if VIA_ACCEL is not None else "載不到 → 照跑、亮黃"))
    out.append(("網路工具橋", "ok" if VIA_NET_TOOL_PATH else "warn", Path(VIA_NET_TOOL_PATH).name if VIA_NET_TOOL_PATH else "不在"))
    gates = [k for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT") if env.get(k) != "YES"]
    out.append(("同意閘(只檢查,不代設)", "ok" if not gates else "warn",
                "兩道都已由你開啟" if not gates else "沒開:" + " · ".join(gates) + " → 只用庫內現有資料,不出網"))
    return out


def launch(argv: list, runner=None, git_runner=None, sleep=None) -> int:
    import time
    plain = "--plain" in argv or bool(os.environ.get("NO_COLOR"))
    vt = (not plain) and sys.stdout.isatty()
    if vt and os.name == "nt":
        os.system("")                                   # 舊主控台開 VT
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    sleep = sleep or time.sleep
    rest = [a for a in argv if a not in ("--plain", "--check")]
    if "--start" not in rest:
        rest += ["--start", "2018-01-01"]
    t0 = time.time()
    print("\n" + _gradient("  ▌ VIA · VDF  資料擷取啟動器  ·  排程加速 · 降壓保護 · 增量不重抓", (90, 160, 255), (170, 110, 255), vt))
    print(_rgb("  排程 · 降壓 · 擷取 · 併庫全在 Python(本檔);PS 只負責叫起來", (150, 150, 165), vt) + "\n")
    marks = {"ok": ("✔", (80, 220, 140)), "warn": ("!", (255, 200, 60)), "fail": ("✖", (255, 90, 90))}
    checks = preflight(git_runner=git_runner)
    for name, st, note in checks:
        if vt:
            sys.stdout.write(f"{ESC}[?25l")
            for k in range(8):
                sys.stdout.write("\r  " + _rgb(FRAMES[k % len(FRAMES)], (120, 170, 255), vt) + f" {name}")
                sys.stdout.flush()
                sleep(0.045)
            sys.stdout.write(f"\r{ESC}[2K")
        m, rgb = marks[st]
        print(f"  {_rgb(m, rgb, vt)} {name}  " + _rgb(note, (150, 150, 165), vt), flush=True)
    if vt:
        sys.stdout.write(f"{ESC}[?25h")
    if any(st == "fail" for _, st, _ in checks):
        print(_box("結果 RED", ["開跑前檢查有紅項,沒有開跑"], (255, 90, 90), vt))
        return 1
    print("\n" + _box("開跑", [f"參數 run {' '.join(rest)}",
                                "⓪ 暫存只補缺併入資料家 · ① 降壓 BELOW_NORMAL + IO LOW · ② 3 道 + 監工 · ③ 增量擷取 · 矩陣"], (120, 170, 255), vt))
    if "--check" in argv:
        rc = 0
        print(_rgb("  --check:只做開跑前檢查,沒有開跑", (255, 200, 60), vt))
    else:
        rc = (runner or main)(["run", *rest])
    lamp = {0: "GREEN", 2: "YELLOW"}.get(rc, "RED")
    rgb = {"GREEN": (80, 220, 140), "YELLOW": (255, 200, 60)}.get(lamp, (255, 90, 90))
    print("\n" + _box(f"結果 {lamp}", [f"rc {rc} · 耗時 {(time.time() - t0) / 60:.1f} 分",
                                       "收據:VIA_Reports/vdf/stage_merge · VIA_Reports/vdf/datamatrix · VIA_Reports/vdf_lake",
                                       "桌機實跑結果;收尾成功仍要輸出驗證 + 你用滑鼠走完 U/I"], rgb, vt))
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(假子行程;不跑擷取)===", flush=True)
    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 網路工具橋在位(載入不出網)", VIA_NET_TOOL_PATH is not None)
    st = stage_steps(["run", "--start", "2018-01-01"])
    chk("③ ⓪ 先印擷取家(FetchGroups home)再併暫存(StageMerge apply)", [t for t, _ in st] == ["擷取家", "暫存併入資料家"]
        and st[0][1][-1] == "home" and st[1][1][4] == "apply", st)
    chk("④ --dry → plan(唯讀)· --data-home 帶給併入 · --no-merge 只剩擷取家",
        stage_steps(["run", "--dry"])[1][1][4] == "plan" and stage_steps(["run", "--data-home", "X"])[1][1][-2:] == ["--home", "X"]
        and [t for t, _ in stage_steps(["run", "--no-merge"])] == ["擷取家"])
    seen = []
    rc = run_stage(["run", "--data-home", "D"], runner=lambda cmd, env: seen.append((cmd[4], env.get("VIA_FROM_VDFSM"), env.get("VIA_VDF_DB_HOME"))) or 1)
    chk("⑤ 子行程帶 VDF 入口旗標與資料家 · 併入紅 → ⓪ 紅(擷取家查不到只算黃)", rc == 1 and seen == [("home", "YES", "D"), ("apply", "YES", "D")], (rc, seen))
    chk("⑥ 總燈 worse:紅留紅 · 黃不蓋紅", worse(0, 2) == 2 and worse(1, 2) == 1 and worse(2, 0) == 2)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "via_database"
        root.mkdir()
        na = norm_args(["run", "--via-db", str(root), "--start", "2018-01-01"])
        st2 = stage_steps(na)
        chk("⑥b --via-db 先正規化成 --data-home <根>/vdf_database(絕對路徑)· ⓪ 併入用同一個資料家(Codex P2)",
            "--via-db" not in na and na[na.index("--data-home") + 1] == str((root / "vdf_database").resolve())
            and st2[1][1][-2:] == ["--home", str((root / "vdf_database").resolve())], (na, st2[1][1][-2:]))
        rel = norm_args(["run", "--data-home", "rel_home"])
        chk("⑥c 相對 --data-home 轉絕對(子行程換工作目錄也指同一處)", Path(rel[rel.index("--data-home") + 1]).is_absolute(), rel)
    import contextlib
    import io
    got = {}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_l = launch(["--plain"], runner=lambda a: got.setdefault("args", a) and 2, git_runner=lambda: "HEAD", sleep=lambda s: None)
        rc_c = launch(["--check", "--plain", "--start", "2020-01-01"], runner=lambda a: got.setdefault("bad", a) or 1,
                      git_runner=lambda: "main", sleep=lambda s: None)
    txt = buf.getvalue()
    chk("⑥d launch:沒給 --start = 2018-01-01 交 run · rc 照傳 · detached 黃燈提醒 · --check 不開跑 · --plain 無 ANSI",
        rc_l == 2 and got.get("args") == ["run", "--start", "2018-01-01"] and "detached" in txt and rc_c == 0 and "bad" not in got
        and "\x1b[" not in txt and "結果 YELLOW" in txt, (rc_l, got, rc_c))
    chk("⑦ 本檔沒寫同意閘(只帶入口旗標)", not re.search(r"VIA_(NET|SCRAPE)_CONSENT[\"']?\]?\s*=", Path(__file__).read_text(encoding="utf-8")))
    import contextlib
    import io
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc_p = PRIOR.selftest()
    except Exception as exc:  # noqa: BLE001
        rc_p = 1
        print(f"  [註] 前版鏈自測丟例外:{type(exc).__name__}", flush=True)
    alone = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, timeout=900).returncode
    chk("⑧ 前版鏈自測在本版下的結果 = 單獨跑 v0109 的結果(本版不讓前版變壞)", (rc_p == 0) == (alone == 0), (rc_p, alone))
    PRIOR_RC["rc"] = rc_p
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 檔面:第 3 行加速器標記 · 雙橋 · glob 取前版 · 零 TA-Lib",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:NET-BRIDGE:v0100]" in src and "HERE.glob(STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    pr = PRIOR_RC.get("rc", 0)
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}"
          + ("" if pr == 0 else " · 前版自測本來就不綠(這台缺 rich 等依賴;範圍外,照實回黃)"), flush=True)
    if not all(ok):
        return 1
    return 0 if pr == 0 else 2


PRIOR_RC = {}


if __name__ == "__main__":
    sys.exit(main())

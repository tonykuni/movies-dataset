#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_HostBoot v0106 — 薄尾(v0100–v0105 一字不動):新動詞 up(一支 PS 依序啟動 VCGC → 備份 + Graphify → VDF)

操作員 2026-11-27:「Activate vcgc vdf by insert order to ps and backup graphify the vcgc and vdf」。
順序寫在 Python(CLAUDE.md:PS 只負責叫起來);Start-VIA-v0100.ps1 只叫本檔的 up。
  ① VCGC 啟動   VCGC 主控台尾版 enter(VIA_FROM_VCGC=YES 只設在這個子行程;省 Token 卡 · 交接 · 串測)。
                非 0 = 黃,照常往下(三系統對等獨立:VCGC 的燈不擋 VDF)。
  ② 備份 + Graphify  VIA_DailyBackup 尾版 full --via <VIA> --sys VCGC,VDF(第五章六題已定案:引擎倉 · Mode C 先刷齊三冊與
                各系統 Graphify 圖 · 本機隔離區 · 5 份輪替 · Fail-Closed · 不提交)。rc 1(前置閘紅)= 停,VDF 不開跑。
                --skip-backup 跳過(照實記「略過」,不算綠)。
  ③ VDF 啟動    VDF_MDL022_SafeParallelLaunch 尾版 start(開跑前檢查 → 一次降壓 → 3 道同步 → 摘要;加速器真的載到才跑)。
                沒帶就預設 --start 2018-01-01 --slots 3;其餘參數原樣交給它。
每一步直接用這個主控台輸出(進度條照常),最後印一張步驟表(步驟 · rc · 秒),收據 <TEMP>/via_hostboot_up_<時戳>/up_RUN.json(只結構)。
同意閘一律不設:兩道閘由你在自己的視窗開(VDF 開跑前檢查會擋)。不出網(出網的是 VDF 的擷取子行程)· 不碰 TA-Lib。
用法:python VIA_HostBoot_v0106.py --repo <倉> up [--skip-backup] [VDF start 參數…]
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    import os as _sa_os
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.insert(0, _sa_Path(_sa_os.environ["VIA_REPO"]).resolve() / "VeritasIntelligenceAnalytics")
    for _sa_p in _sa_roots:
        _sa_hit = None
        while True:
            for _sa_c in (_sa_p, _sa_p / "VeritasIntelligenceAnalytics"):
                if (_sa_c / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit or _sa_p.parent == _sa_p:
                break
            _sa_p = _sa_p.parent
        if _sa_hit:
            _sa_sys.path.insert(0, str(_sa_hit / "supportive modules"))
            break
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====


import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0106"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
_T0 = time.time()
CONSOLE = ("supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole")
BACKUP = ("docs/handoff/ai", "VIA_DailyBackup")
LAUNCH = ("functional modules/VDF", "VDF_MDL022_SafeParallelLaunch")
VDF_DEFAULTS = (("--start", "2018-01-01"), ("--slots", "3"))


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
VERBS = tuple(PRIOR.VERBS) + ("up",)
VIA_NET_TOOL_PATH = getattr(PRIOR, "VIA_NET_TOOL_PATH", None)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    print(msg, flush=True)


def tail_of(via: Path, spec: tuple) -> Path | None:
    hits = [p for p in (via / spec[0]).glob(spec[1] + "_v[0-9][0-9][0-9][0-9].py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def vdf_args(extra: list) -> list:
    a = list(extra)
    for k, v in VDF_DEFAULTS:
        if k not in a and not any(x.startswith(k + "=") for x in a):
            a += [k, v]
    return a


def up_steps(via: Path, extra: list, skip_backup: bool = False, py: str = None) -> list:
    """(名稱, 指令 | None, 這一步的 env 增補, 紅燈要不要停)· 找不到尾版 → 指令 None(照實紅)。"""
    py = py or sys.executable
    con, bak, lau = tail_of(via, CONSOLE), tail_of(via, BACKUP), tail_of(via, LAUNCH)
    steps = [("① VCGC 啟動", con and [py, "-X", "utf8", str(con), "enter"], {"VIA_FROM_VCGC": "YES"}, False)]
    if not skip_backup:
        steps.append(("② 備份 + Graphify(VCGC · VDF)", bak and [py, "-X", "utf8", str(bak), "full", "--via", str(via), "--sys", "VCGC,VDF"],
                      {}, True))
    steps.append(("③ VDF 啟動", lau and [py, "-X", "utf8", str(lau), "start", *vdf_args(extra)], {}, True))
    return steps


def run_up(via: Path, extra: list, skip_backup: bool = False, runner=None, py: str = None) -> tuple:
    runner = runner or (lambda cmd, env: subprocess.run(cmd, env=env, cwd=str(via.parent)).returncode)
    rows, final = [], 0
    if skip_backup:
        rows.append({"step": "② 備份 + Graphify(VCGC · VDF)", "rc": None, "secs": 0.0, "lamp": "SKIP", "note": "--skip-backup:略過(不算綠)"})
    for name, cmd, add, stop_on_red in up_steps(via, extra, skip_backup, py):
        say(f"\n== {name} ==")
        if not cmd:
            rows.append({"step": name, "rc": None, "secs": 0.0, "lamp": "RED", "note": "找不到尾版(先 git pull)"})
            say(f"[RED] {name}:找不到尾版")
            if stop_on_red:
                final = 1
                break
            continue
        t = time.time()
        rc = runner(cmd, dict(os.environ, **add))
        lamp = "GREEN" if rc == 0 else ("YELLOW" if rc == 2 else "RED")
        note = ""
        if rc not in (0, 2) and stop_on_red and name.startswith("②"):
            note = "前置閘紅(Fail-Closed):VDF 不開跑"
        elif rc not in (0, 2) and not stop_on_red:
            note = "系統獨立:不擋後面的步驟"
        rows.append({"step": name, "rc": rc, "secs": round(time.time() - t, 1), "lamp": lamp, "note": note})
        if name.startswith("③"):
            final = rc
        elif rc not in (0, 2) and stop_on_red:
            final = 1
            break
    rows.sort(key=lambda r: r["step"])
    return final, rows


def table(rows: list) -> str:
    lines = [f"\n{'步驟':<26} {'燈':<7} {'rc':>4} {'秒':>8}  說明"]
    for r in rows:
        lines.append(f"{r['step']:<26} {r['lamp']:<7} {str(r['rc'] if r['rc'] is not None else '—'):>4} {r['secs']:>8.1f}  {r['note']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if "up" not in argv:
        return PRIOR.main(argv)
    i = argv.index("up")
    head, rest = argv[:i], argv[i + 1:]
    if "--repo" not in head:
        say("[RED] 要 --repo <倉>")
        return 1
    repo = Path(head[head.index("--repo") + 1]).expanduser().resolve()
    via = repo / BASE.VIA_REL
    if not via.is_dir():
        say(f"[RED] 不是 VIA 倉:{repo}")
        return 1
    skip = "--skip-backup" in rest
    rest = [x for x in rest if x != "--skip-backup"]
    say(f"{TAG} · up · 倉 {repo} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 順序 VCGC → 備份 + Graphify → VDF")
    rc, rows = run_up(via, rest, skip)
    say(table(rows))
    out = Path(tempfile.gettempdir()) / f"via_hostboot_up_{time.strftime('%Y%m%d_%H%M%S')}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "up_RUN.json").write_text(json.dumps({"tool": TAG, "verb": "up", "rc": rc, "secs": round(time.time() - _T0, 1), "steps": rows,
                                                 "accel": VIA_ACCEL is not None}, ensure_ascii=False, indent=1), encoding="utf-8")
    say(f"up · rc {rc} · 收據 → {out}")
    return rc


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        for folder, stem in (CONSOLE, BACKUP, LAUNCH):
            (via / folder).mkdir(parents=True, exist_ok=True)
            for v in ("v0100", "v0102"):
                (via / folder / f"{stem}_{v}.py").write_text("", encoding="utf-8")
        steps = up_steps(via, ["--dry"], py="PY")
        names = [s[0][0] for s in steps]
        c, b, l_ = (s[1] for s in steps)
        chk("① 順序 VCGC → 備份 + Graphify → VDF · 各取尾版 v0102", names == ["①", "②", "③"] and all("_v0102.py" in x[3] for x in (c, b, l_)), steps)
        chk("② VCGC enter 的入口標記只放在那一步的子行程 env(本檔不改本行程 os.environ)",
            c[-1] == "enter" and steps[0][2] == {"VIA_FROM_VCGC": "YES"} and all(s[2] == {} for s in steps[1:]), steps)
        chk("③ 備份 = DailyBackup full --via <VIA> --sys VCGC,VDF(Graphify 在 full 的 G1)", b[4:] == ["full", "--via", str(via), "--sys", "VCGC,VDF"], b)
        chk("④ VDF = MDL022 start · 預設補 --start 2018-01-01 --slots 3 · 已給的不重複", l_[4:] == ["start", "--dry", "--start", "2018-01-01", "--slots", "3"]
            and vdf_args(["--slots", "5", "--start=2020-01-01"]) == ["--slots", "5", "--start=2020-01-01"], l_)
        calls = []

        def fake(codes):
            it = iter(codes)
            return lambda cmd, env: calls.append((cmd[4], env.get("VIA_FROM_VCGC"))) or next(it)

        rc, rows = run_up(via, [], runner=fake([0, 0, 0]), py="PY")
        chk("⑤ 全綠 → 三步都跑 · rc 0 · enter 那步帶 VCGC 入口標記", rc == 0 and [c[0] for c in calls] == ["enter", "full", "start"]
            and calls[0][1] == "YES" and calls[1][1] != "YES", calls)
        calls.clear()
        rc, rows = run_up(via, [], runner=fake([1, 0, 0]), py="PY")
        chk("⑥ VCGC 紅 → 照常備份與 VDF(系統獨立)· 該步記紅", rc == 0 and len(calls) == 3 and rows[0]["lamp"] == "RED", rows)
        calls.clear()
        rc, rows = run_up(via, [], runner=fake([0, 1]), py="PY")
        chk("⑦ 備份前置閘紅 → 停 · VDF 不開跑 · rc 1", rc == 1 and [c[0] for c in calls] == ["enter", "full"] and "Fail-Closed" in rows[-1]["note"], rows)
        calls.clear()
        rc, rows = run_up(via, [], skip_backup=True, runner=fake([0, 3]), py="PY")
        chk("⑧ --skip-backup → 記「略過」(SKIP,不算綠)· rc 照 VDF", rc == 3 and [c[0] for c in calls] == ["enter", "start"]
            and any(r["lamp"] == "SKIP" for r in rows), rows)
        for p in (via / LAUNCH[0]).glob("*.py"):
            p.unlink()
        calls.clear()
        rc, rows = run_up(via, [], runner=fake([0, 0]), py="PY")
        chk("⑨ 找不到 VDF 尾版 → 紅 · rc 1(不假裝跑過)", rc == 1 and any(r["lamp"] == "RED" and "尾版" in r["note"] for r in rows), rows)
    rc_prior = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, timeout=1800).returncode
    chk("⑩ 前版 v0105 自測單獨跑照過(本版不換裝前版任何名稱)", rc_prior == 0, rc_prior)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:第 3 行加速器標記 · 橋在 · 不設同意閘 · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:ACCEL-BRIDGE:v0100]" in src
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    print(f"[selftest] {TAG} {len(ok)}/{len(ok) + len(bad)} " + ("PASS" if not bad else "FAIL · " + " · ".join(bad)), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

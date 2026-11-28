#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0124 — 薄尾(v0123 以前一字不動):容器跑的 launch 總燈最多黃(PR #773 Codex P1;AGENTS.md「容器跑出來的結果最多黃」)

v0123 在容器裡全步綠 + 加速器在 → GREEN / rc 0,寫進貼回包與只增帳。本版:
  · 總燈:容器(非 Windows,與 launch 的 host 判法同一條)全綠 → YELLOW / rc 2;紅照留紅;主機照舊可綠。
  · 貼回包多一行點名「容器最多黃」;NEXT 改指主機一行(Start-VCGC-v0102.ps1)。
  · 收據 version / 標籤寫實際跑的 v0124。
做法:掛鉤裝在「定義那個名字的那一層」(overall 在 v0123、_next / pastepack 在 v0122),v0123 的 launch 照常呼叫、行為才會變。
其餘動詞照 v0123 → v0122 → v0121 原樣轉交。只動 VCGC 自己的檔與 VIA_Reports/vcgc。
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
    VIA_ACCEL = None  # graceful:加速器缺席時照樣載得起來(v0123 的 launch 會把總燈壓到黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_SystemManager"
VERSION = "v0124"
TAG = f"{_STEM} {VERSION}"
CONTAINER_LINE = "  [YELLOW] host     容器跑的結果最多黃(AGENTS.md);收尾要主機實跑"
HOST_NEXT = "主機 PS7 跑 Start-VCGC-v0102.ps1,貼回 LAUNCH_latest.txt(容器最多黃)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


_BELOW = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
if not _BELOW:   # 放錯倉:照實停,不丟例外(同 v0122)
    print(f"[RED] {HERE} 沒有 {_STEM} 前版;這份不是主工作倉。", flush=True)
    raise SystemExit(3)
PRIOR_PATH = max(_BELOW, key=_vnum)
_spec = importlib.util.spec_from_file_location(f"cgc_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _home(name: str):
    """定義 name 的那一層(本檔之下的鏈:v0123 → v0122 → v0121 …)。"""
    m = PRIOR
    while m is not None:
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR")
    raise LookupError(name)


def is_container() -> bool:
    """與 launch 的 host 判法同一條:非 Windows = 容器。"""
    return os.name != "nt"


_OVERALL_HOME = _home("overall")
_NEXT_HOME = _home("_next")
_PACK_HOME = _home("pastepack")
_PREV_OVERALL = vars(_OVERALL_HOME)["overall"]
_PREV_NEXT = vars(_NEXT_HOME)["_next"]
_PREV_PACK = vars(_PACK_HOME)["pastepack"]


def overall(allr: list, accel_ok: bool) -> str:
    lamp = _PREV_OVERALL(allr, accel_ok)
    return "YELLOW" if (lamp == "GREEN" and is_container()) else lamp


def _next(res: dict) -> str:
    nxt = _PREV_NEXT(res)
    if res.get("host") == "容器" and nxt.startswith("via-vcgc handoff daily"):
        return HOST_NEXT
    return nxt


def pastepack(res: dict, cap: int = 300) -> list:
    out = _PREV_PACK(res, cap)
    if res.get("host") == "容器" and CONTAINER_LINE not in out:
        out.insert(1, CONTAINER_LINE)
    return out


def install() -> None:
    """掛到定義那一層;收據版本與標籤寫本版。可重複呼叫。"""
    _OVERALL_HOME.overall = overall
    _NEXT_HOME._next = _next
    _PACK_HOME.pastepack = pastepack
    PRIOR.VERSION = VERSION
    PRIOR.TAG = TAG


install()


def launch(argv: list, **kw) -> int:
    kw.setdefault("self_file", Path(__file__).resolve())
    return PRIOR.launch(argv, **kw)


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["launch"]:
        return launch(a[1:])
    return PRIOR.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    g = globals()
    chk("① 加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    below = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    chk("② 前版經 glob 載入(本檔之下最大的一版)", PRIOR_PATH == max(below, key=_vnum), PRIOR_PATH.name)
    me_mod = sys.modules[__name__]
    chk("③ TAILAPI:前版公開名稱經本檔轉接(tally · plan · run_steps · cmd_schedule · core_python)",
        all(callable(getattr(me_mod, n, None)) for n in ("tally", "plan", "run_steps", "cmd_schedule", "core_python")))
    chk("④ 掛鉤裝在定義那一層(overall @ v0123 · _next / pastepack @ v0122)",
        vars(_OVERALL_HOME)["overall"] is overall and vars(_NEXT_HOME)["_next"] is _next and vars(_PACK_HOME)["pastepack"] is pastepack,
        f"{_OVERALL_HOME.__name__} · {_NEXT_HOME.__name__}")
    green = [{"lamp": "GREEN"}, {"lamp": "GREEN"}]
    real = g["is_container"]
    try:
        g["is_container"] = lambda: True
        chk("⑤ 容器:全綠 + 加速器在 → YELLOW;有紅照紅", overall(green, True) == "YELLOW" and overall(green + [{"lamp": "RED"}], True) == "RED")
        g["is_container"] = lambda: False
        chk("⑥ 主機:全綠 + 加速器在 → GREEN;加速器缺 → YELLOW(v0123 規則照留)", overall(green, True) == "GREEN" and overall(green, False) == "YELLOW")
    finally:
        g["is_container"] = real
    saved_no_open = os.environ.pop("VIA_NO_OPEN", None)   # 自測不吃本機狀態(LL-20261128-02)
    try:
        with tempfile.TemporaryDirectory() as td:
            via = Path(td) / "repo" / "VeritasIntelligenceAnalytics"
            reg = via / "supportive modules" / "registry"
            ai = via / "docs" / "handoff" / "ai"
            reg.mkdir(parents=True)
            ai.mkdir(parents=True)
            fake = PRIOR._FAKE
            for f in (reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py", reg / "CGC_MDL158_Fake_v0100.py", ai / "VIA_ReworkGuard_v0100.py"):
                f.write_text(fake, encoding="utf-8")
            (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps(
                {"token": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_Fake_v0100.py"}}), encoding="utf-8")
            me = reg / "CGC_FakeManager_v0100.py"   # 假管理器夾具(不用本家族名)
            me.write_text(fake, encoding="utf-8")
            out = via / "VIA_Reports" / "vcgc" / "launch"
            lines, opened = [], []

            def run(container):
                g["is_container"] = (lambda: container)
                try:
                    rc = PRIOR.launch(["--timeout", "30"], via, reg, me, sys.executable, out, opened.append, lambda m, lamp=None: lines.append(m), 1, True)
                finally:
                    g["is_container"] = real
                r = json.loads((out / "LAUNCH_latest.json").read_text(encoding="utf-8"))
                return rc, r, (out / "LAUNCH_latest.txt").read_text(encoding="utf-8").splitlines()

            rc, r, pk = run(True)
            chk("⑦ 端到端(容器判定):全綠 → YELLOW · rc 2 · 收據 version v0124 · 貼回包點名容器 · NEXT 指主機一行",
                rc == 2 and r["lamp"] == "YELLOW" and r["version"] == VERSION and CONTAINER_LINE in pk and pk[-1] == "NEXT: " + HOST_NEXT,
                f"{r['lamp']} · {pk[-1][:50]}")
            rc2, r2, _pk2 = run(False)
            chk("⑧ 端到端(主機判定):全綠 → GREEN · rc 0 · 三數 應 = 已 + 略過",
                r2["counts"]["should"] == r2["counts"]["ran"] + len(r2["counts"]["skipped"])
                and (r2["lamp"] == "GREEN" and rc2 == 0), f"{r2['lamp']} · rc {rc2}")
    finally:
        if saved_no_open is not None:
            os.environ["VIA_NO_OPEN"] = saved_no_open
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1")
    env.pop("VIA_NO_OPEN", None)
    pl = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "launch", "--plan", "--plain"], capture_output=True,
                        text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
    chk("⑨ 入口:launch 走本版(真倉 --plan · rc 0 · 本版標籤 · 不寫檔)", pl.returncode == 0 and f"[{TAG}]" in pl.stdout, (pl.stdout.strip().splitlines() or ["?"])[-1][:80])
    pr = subprocess.run([sys.executable, "-X", "utf8", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", env=env, timeout=1200)
    last = (pr.stdout.strip().splitlines() or ["?"])[-1]
    chk("⑩ 直接前版自測(乾淨子行程)rc 0", pr.returncode == 0, last[:80])
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())

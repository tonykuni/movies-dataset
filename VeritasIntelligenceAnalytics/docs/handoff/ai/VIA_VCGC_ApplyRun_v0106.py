#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ApplyRun v0106 — 薄尾:A 道改走各系統的安全並行啟動器(3~6 道 · 監工過熱減道 / 暫停 · 冷卻恢復)
操作員 2026-11-20:「VRN 為了正確工具很多,由簡單但重型工具,若簡單的工具便可取得可驗證的就不必往重型移動;
  若 CPU / DRAM 承受範圍三到六個獨立步驟同步進行,不可傷害電腦及系統及指令,自動最佳化調節;這種方式通用於 VDF」。
量到的現況(只讀):
  · 由簡到重已在:VRN_ENG072_FirstPageText 尾版 extract_pdf_page1 —— 文字層(fitz → pypdf,密度閘擋浮水印)→ 原畫質 OCR
    (simple → dual → paddle → PPP,有預算)→ 只有「跑了但零字」才升高畫質 OCR(DPI 300~350);後端不在位就不升(批449 · 批493 · 批496)。
  · 3~6 道監工已在:VRN_MDL260_SafeParallelLaunch(VRN_ParamControl_SSOT 的 slots_min 3 · slots_max 6 · cpu_soft 70 ·
    cpu_hard 90 · mem_floor_gb 2)與 VDF_MDL022_SafeParallelLaunch v0104(MIN_SLOTS 3 · MAX_SLOTS 6)。
  · 缺口:v0104 / v0105 的 A 道叫的是各系統管理器的 `launch --run`(VDF → VDF_MDL013_ActivateVDF;VRN → VRN2_RoundAll),
    兩條路都**沒有**那個監工(只在起跑時量一次 CPU 決定路數,跑的中途不看壓力、不暫停)。
本版只改一件事:A 道兩步改叫各系統自己的安全並行啟動器尾版(仍是各系統自己的入口,不帶 VCGC 旗;兩步照舊依序,不疊加):
  A-VDF-activate   VDF_MDL022_SafeParallelLaunch 尾版 run --start 2021-01-01 --slots auto --no-open [--data-home <go 給的夾>]
  A-VRN-activate   VRN_MDL260_SafeParallelLaunch 尾版 run --slots auto --no-open [--source <go --vrn-source 給的夾>]
道數一律 auto(由各啟動器依這台的 CPU / DRAM 夾在 3~6,過熱自己減道 / 暫停最新子行程);本檔不設道數、不設同意閘。
啟動器尾版不在 → 照舊叫管理器 launch --run(並在註記點名退回)。
`go` 多一個旗標 `--vrn-source <夾>`:夾要真的存在才用;錯形路徑當場拒絕、零寫入(同 --data-home)。其餘全部照 v0105。
用法:python VIA_VCGC_ApplyRun_v0106.py go [--no-activate] [--data-home <夾>] [--vrn-source <夾>] [--lanes N] [--no-open] · --selftest
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_ApplyRun"
VERSION = "v0106"
TAG = "VIA_VCGC_ApplyRun " + VERSION
VDF_LAUNCHER = "VDF_MDL022_SafeParallelLaunch_v*.py"
VRN_LAUNCHER = "VRN_MDL260_SafeParallelLaunch_v*.py"
VDF_START = "2021-01-01"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def a_steps(via: Path) -> tuple:
    """(A 道兩步, 註記)。啟動器尾版在就走它;不在就退回管理器 launch --run 並點名。"""
    notes = []
    vdf_l = BASE.tail(Path(via) / "functional modules/VDF", VDF_LAUNCHER)
    vrn_l = BASE.tail(Path(via) / "functional modules/VRN", VRN_LAUNCHER)
    dh = os.environ.get("VIA_DATA_HOME") or ""
    src = os.environ.get("VIA_VRN_SOURCE") or ""
    if vdf_l is not None:
        vdf = BASE.Step("A", "A-VDF-activate", vdf_l,
                        ["run", "--start", VDF_START, "--slots", "auto", "--no-open"] + (["--data-home", dh] if dh else []), 5 * 3600, own=True)
    else:
        vdf = BASE.Step("A", "A-VDF-activate", BASE.tail(Path(via) / "functional modules/VDF", "VDF_SystemManager_v*.py"), ["launch", "--run"], 4 * 3600, own=True)
        notes.append("[A] VDF 安全並行啟動器不在 → 退回 VDF 管理器 launch --run(沒有 3~6 道監工)")
    if vrn_l is not None:
        vrn = BASE.Step("A", "A-VRN-activate", vrn_l,
                        ["run", "--slots", "auto", "--no-open"] + (["--source", src] if src else []), 7 * 3600, own=True)
    else:
        vrn = BASE.Step("A", "A-VRN-activate", BASE.tail(Path(via) / "functional modules/VRN", "VRN_SystemManager_v*.py"), ["launch", "--run"], 2 * 3600, own=True)
        notes.append("[A] VRN 安全並行啟動器不在 → 退回 VRN 管理器 launch --run(沒有 3~6 道監工)")
    notes.append("[A] 兩步依序(同一組);每一步由該系統自己的啟動器依 CPU / DRAM 夾 3~6 道、過熱減道 / 暫停最新子行程、冷卻恢復")
    return [vdf, vrn], notes


def plan(via: Path, only: list[str]):
    g, notes = _PREV_PLAN(via, only)
    if "A" in only:
        g["A"], n2 = a_steps(via)
        notes = list(notes) + n2
    return g, notes


_PREV_PLAN = BASE.plan                   # = v0104 的 plan(v0105 沒動 plan)
BASE.plan = plan


def check_source(value):
    if value is None:
        return True, ""
    p = Path(value).expanduser()
    if not p.is_dir():
        return False, "VRN 來源夾不存在或不是資料夾:%s(零寫入,沒有跑任何步)" % p
    return True, str(p.resolve())


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    if a[:1] == ["go"] and "--vrn-source" in a:
        i = a.index("--vrn-source")
        if i + 1 >= len(a) or a[i + 1].startswith("--"):
            print("[%s] --vrn-source 要給資料夾路徑" % TAG)
            return 2
        ok, msg = check_source(a[i + 1])
        if not ok:
            print("[%s] 拒跑 · %s" % (TAG, msg), flush=True)
            return 2
        os.environ["VIA_VRN_SOURCE"] = msg          # 只在本行程(A 道的計畫讀它);不寫任何檔
        a = a[:i] + a[i + 2:]
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""), flush=True)

    saved = {k: os.environ.get(k) for k in ("VIA_DATA_HOME", "VIA_VRN_SOURCE")}
    try:
        with tempfile.TemporaryDirectory(prefix="applyrun_v0106_") as td:
            via = Path(td) / "VIA"
            for rel in ("supportive modules/registry", "functional modules/VDF", "functional modules/VRN"):
                (via / rel).mkdir(parents=True)
            for rel in ("functional modules/VDF/VDF_MDL022_SafeParallelLaunch_v0104.py", "functional modules/VRN/VRN_MDL260_SafeParallelLaunch_v0102.py",
                        "functional modules/VDF/VDF_SystemManager_v0186.py", "functional modules/VRN/VRN_SystemManager_v0278.py"):
                (via / rel).write_text("x = 1\n", encoding="utf-8")
            for k in saved:
                os.environ.pop(k, None)
            steps, notes = a_steps(via)
            chk("① A 道兩步改叫各系統的安全並行啟動器尾版(不帶 VCGC 旗)· 道數 auto",
                [s.entry.name for s in steps] == ["VDF_MDL022_SafeParallelLaunch_v0104.py", "VRN_MDL260_SafeParallelLaunch_v0102.py"]
                and all(s.own for s in steps) and all(s.args[s.args.index("--slots") + 1] == "auto" for s in steps), [s.args for s in steps])
            chk("② VDF 帶 --start 2021-01-01;沒給資料家目錄就不帶 --data-home", steps[0].args[:3] == ["run", "--start", "2021-01-01"] and "--data-home" not in steps[0].args)
            os.environ["VIA_DATA_HOME"] = str(Path(td) / "home")
            os.environ["VIA_VRN_SOURCE"] = str(Path(td) / "src")
            steps, _ = a_steps(via)
            chk("③ go 給的資料家目錄 → VDF --data-home;--vrn-source → VRN --source",
                steps[0].args[-2:] == ["--data-home", str(Path(td) / "home")] and steps[1].args[-2:] == ["--source", str(Path(td) / "src")], [s.args for s in steps])
            (via / "functional modules/VRN/VRN_MDL260_SafeParallelLaunch_v0102.py").unlink()
            steps, notes = a_steps(via)
            chk("④ 啟動器不在 → 退回管理器 launch --run 並點名", steps[1].entry.name == "VRN_SystemManager_v0278.py" and steps[1].args == ["launch", "--run"]
                and any("退回 VRN" in n for n in notes))
            g, n3 = plan(via, ["A"])
            chk("⑤ 裝進 v0100 模組全域:BASE.plan 是本版 · --only A 只排 A 道兩步", BASE.plan is plan and list(g) == ["A"] and len(g["A"]) == 2, list(g))
            before = sorted(p.name for p in Path(td).rglob("*"))
            rc = main(["go", "--vrn-source", str(Path(td) / "沒有這個夾"), "--no-open"])
            chk("⑥ --vrn-source 錯形路徑 → 拒跑 rc 2 · 零寫入", rc == 2 and sorted(p.name for p in Path(td).rglob("*")) == before)
            chk("⑦ 合法來源夾 → 通過檢查且回絕對路徑", check_source(td) == (True, str(Path(td).resolve())))
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 加速器橋真的匯入 · 不碰 TA-Lib · 不設也不寫同意閘 · 不設道數 · 不含本機路徑",
        "import VIA_SuperAccel_Module as VIA_ACCEL" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("C:" + "\\Users") not in src)
    BASE.plan = _PREV_PLAN
    try:
        rc_prior = PRIOR.selftest()
    finally:
        BASE.plan = plan
    chk("⑨ 前版 %s 自測照過" % PRIOR_PATH.stem, rc_prior == 0, rc_prior)
    good = all(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if good else "FAIL", TAG, sum(ok), len(ok)))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())

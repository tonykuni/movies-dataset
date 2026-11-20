#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ApplyRun v0104 — 薄尾:新增 A 道「啟用 VDF / VRN-2 產出實冊」(在 K 道之前另外叫一次,不與 K 並行)

操作員 2026-11-20 17:51:「test vcgc debug and close out vcgc · activate vdf to get the output verify and close up vdf ·
activate and get output verify and close out · 善用vcgc節省工具去進行」。
A 道只叫各系統自己的管理器 launch --run(L123:VDF / VRN-2 走自己的入口,不帶 VCGC 旗;VCGC 不改它們的檔):
  A-VDF-activate   VDF_SystemManager launch --run → VDF_MDL013_ActivateVDF 尾版(要連網擷取;同意閘沒開 = 它自己報黃,不代開)
  A-VRN-activate   VRN_SystemManager launch --run → VRN2_RoundAll 尾版(樣本研報 → 輸出冊 + VRN2_OutBook_latest.json)
本檔不設、不寫同意閘;閘只由啟動 PS 在操作員帶 -Fetch 時、只在那一個行程裡設。其餘全部照 v0103。
用法:python VIA_VCGC_ApplyRun_v0104.py run --only A --no-open → 再 run --only G,K --no-open · --selftest
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_ApplyRun"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
VERSION = "v0104"
TAG = "VIA_VCGC_ApplyRun " + VERSION


def __getattr__(name):
    return getattr(PRIOR, name)


def plan(via: Path, only: list[str]):
    g, notes = _PREV_PLAN(via, [x for x in only if x != "A"])
    if "A" in only:
        VD = BASE.tail(via / "functional modules/VDF", "VDF_SystemManager_v*.py")
        VR = BASE.tail(via / "functional modules/VRN", "VRN_SystemManager_v*.py")
        g["A"] = [BASE.Step("A", "A-VDF-activate", VD, ["launch", "--run"], 4 * 3600, own=True),
                  BASE.Step("A", "A-VRN-activate", VR, ["launch", "--run"], 2 * 3600, own=True)]
        if [x for x in only if x != "A"]:
            notes.append("[A] A 道要在 K 道之前、分開一次叫(run --only A → run --only G,K);同一次叫會並行,K 讀不到新產出")
    return g, notes


_PREV_PLAN = BASE.plan                   # = v0103 的 plan
BASE.plan = plan
if "A" not in BASE.GROUPS:
    BASE.GROUPS = tuple(BASE.GROUPS) + ("A",)
BASE.ZH.setdefault("A", "啟用產出實冊")
BASE.VERSION, BASE.TAG = VERSION, TAG


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""))

    print("=== %s 薄尾自測(前版鏈另跑)===" % TAG)
    via = BASE.find_via(HERE)
    if via is None:
        chk("① 找不到 VIA 夾:跳過 = 黃", False)
    else:
        g, notes = BASE.plan(via, ["A"])
        a = g.get("A", [])
        chk("① A 道兩步 · 都走自己的入口(不帶 VCGC 旗)· 都是 launch --run · 入口是 VDF / VRN 管理器尾版",
            [s.name for s in a] == ["A-VDF-activate", "A-VRN-activate"] and all(s.own and s.args == ["launch", "--run"] for s in a)
            and Path(a[0].entry).name.startswith("VDF_SystemManager_v") and Path(a[1].entry).name.startswith("VRN_SystemManager_v"), [s.name for s in a])
        g2, notes2 = BASE.plan(via, ["A", "K"])
        chk("② A 與 K 同一次叫會提醒「要分開叫」· K 道照前版十步", any("分開" in n for n in notes2) and len(g2.get("K", [])) == 10)
        chk("③ --only A 認得 · 道名有中文", "A" in BASE.GROUPS and BASE.ZH.get("A") == "啟用產出實冊")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋在 · 不碰 TA-Lib · 不設也不寫同意閘 · 沒有色碼", "[VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and not re.search(r"#[0-9a-fA-F]{6}\b", src))
    BASE.plan = _PREV_PLAN
    try:
        rc_prior = PRIOR.selftest()
    finally:
        BASE.plan = plan
    chk("⑤ 前版 %s 自測照過" % PRIOR_PATH.stem, rc_prior == 0, rc_prior)
    good = all(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if good else "FAIL", TAG, sum(ok), len(ok)))
    return 0 if good else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())

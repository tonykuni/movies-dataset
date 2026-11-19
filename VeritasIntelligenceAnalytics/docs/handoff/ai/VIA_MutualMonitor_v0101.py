#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_MutualMonitor v0101 — 薄尾(v0100 一字不動):契約冊可以多一個系統節,自測不再把「正好五個系統」寫死。

實錄(2026-11-19):收據契約冊 v0105 照操作員裁示把 VDB(資料庫管理)升進 systems 之後,v0100 的自測第 ① 項就紅
  (`set(systems) == {VCGC, VDF, VRN2, VQG, VAP}`)。契約冊自己的規則是「新系統 = 本冊加一節(出新版號),不改任何系統程式」;
  寫死五個的是自測,不是功能:run 本來就照冊上有幾節就攤幾節。
本版只改自測,run 與其餘動詞一律原樣交給 v0100:
  ①' 真冊:契約冊在 · 原本的五個系統節都在(可以多,不能少)· 每個系統節是物件且有 receipts 清單 · 每張收據有 path。
  ②  前版 v0100 的自測照跑,契約冊指回它那個年代最後一版還是五個系統的冊(找得到才跑;找不到照實記「沒有可對的舊冊」算不過)。
邊界同 v0100:只讀;不跑任何系統的引擎;不改任何收據。
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

import importlib.util
import json
import re
import sys
from pathlib import Path

VERSION = "v0101"
ENGINE = "VIA_MutualMonitor " + VERSION
HERE = Path(__file__).resolve().parent
CORE5 = {"VCGC", "VDF", "VRN2", "VQG", "VAP"}
_spec = importlib.util.spec_from_file_location("VIA_MutualMonitor_v0100", HERE / "VIA_MutualMonitor_v0100.py")
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["VIA_MutualMonitor_v0100"] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
CONTRACT_GLOB = PRIOR.CONTRACT_GLOB


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def contract_shape(doc) -> list:
    """回問題清單(空 = 過):五個核心系統都在(可多不可少)· 每節是物件且 receipts 是清單 · 每張收據有 path。"""
    probs = []
    systems = doc.get("systems") if isinstance(doc, dict) else None
    if not isinstance(systems, dict):
        return ["沒有 systems"]
    lack = sorted(CORE5 - set(systems))
    if lack:
        probs.append("少了系統節 " + "、".join(lack))
    for k, sp in systems.items():
        if not isinstance(sp, dict) or not isinstance(sp.get("receipts"), list):
            probs.append("%s 沒有 receipts 清單" % k)
            continue
        probs += ["%s 的收據 %s 沒有 path" % (k, r.get("id") if isinstance(r, dict) else "?") for r in sp["receipts"] if not (isinstance(r, dict) and r.get("path"))]
    return probs


def last_five_system_book(via=None):
    """最後一版「systems 正好是原本五個」的契約冊(給 v0100 的自測對它那個年代的冊)。"""
    hits = sorted(Path(via or VIA).glob(CONTRACT_GLOB), key=_vnum, reverse=True)
    for p in hits:
        try:
            if set(json.loads(p.read_text(encoding="utf-8")).get("systems") or {}) == CORE5:
                return p
        except (OSError, ValueError):
            continue
    return None


def selftest() -> int:
    checks = []

    def chk(name, cond, note=""):
        checks.append(bool(cond))
        print("  [%s] %s%s" % ("PASS" if cond else "FAIL", name, (" · " + str(note)[:240]) if note and not cond else ""), flush=True)
    real = sorted(VIA.glob(CONTRACT_GLOB), key=_vnum)
    doc = json.loads(real[-1].read_text(encoding="utf-8")) if real else None
    probs = contract_shape(doc) if doc is not None else ["契約冊不在"]
    chk("①' 真冊:契約冊在 · 原本五個系統節都在(可多不可少)· 每節有 receipts · 每張收據有 path(現在 %d 節)" % len((doc or {}).get("systems") or {}), not probs, probs)
    ok5 = {k: {"receipts": [{"id": "a", "path": "x.json"}]} for k in CORE5}
    chk("② 規則:多一節 → 過;少一節 → 不過並點名;收據沒有 path → 不過;節不是物件 → 不過",
        contract_shape({"systems": dict(ok5, VDB={"receipts": []})}) == [] and contract_shape({"systems": {k: v for k, v in ok5.items() if k != "VAP"}}) == ["少了系統節 VAP"]
        and contract_shape({"systems": dict(ok5, VDB={"receipts": [{"id": "p"}]})}) == ["VDB 的收據 p 沒有 path"] and contract_shape({"systems": dict(ok5, VDB="x")}) == ["VDB 沒有 receipts 清單"]
        and contract_shape({}) == ["沒有 systems"])
    old = last_five_system_book()
    if old is None:
        chk("③ 前版 v0100 自測:對它那個年代的冊(最後一版五系統)9/9", False, "沒有可對的舊冊")
    else:
        keep = PRIOR.CONTRACT_GLOB
        PRIOR.CONTRACT_GLOB = str(old.relative_to(VIA)).replace("\\", "/")
        try:
            rc = PRIOR.selftest()
        finally:
            PRIOR.CONTRACT_GLOB = keep
        chk("③ 前版 v0100 自測:對它那個年代的冊(%s)rc 0;跑完契約冊指回尾版" % old.name, rc == 0 and PRIOR.CONTRACT_GLOB == keep, "rc %s" % rc)
    src = Path(__file__).read_text(encoding="utf-8")
    live = src.split("def selftest")[0]
    chk("④ 本檔自己不寫檔 · 不起子行程 · 不連網 · 不寫 environ", ".write_text(" not in live and "open(" not in live and "subprocess" not in live and "environ[" not in live)
    n = sum(checks)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(checks) else "FAIL", ENGINE, n, len(checks)), flush=True)
    return 0 if n == len(checks) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["selftest"], ["--selftest"]):
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())

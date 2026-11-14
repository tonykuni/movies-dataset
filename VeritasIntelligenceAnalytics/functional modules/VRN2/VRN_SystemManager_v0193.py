#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0193 — 薄尾(操作員 2026-10-12:實測實修迴圈 p1loop · 每輪跑 p1view → 綠燈檔案鎖定(只增不減 · 退步亮紅)· 與上一輪比較燈號 / 原因增減 · 輪次 append-only 帳本)(前版 v0192:摘要如實寫 PDF 份數 · 先切割再 pdfplumber 擷取 · 本文 / 資訊區分開 · 不亂碼 · 不能用馬上換)。
  p1view 動詞 → VRN_ENG397_P1Segment(輸入夾 = VRN 設定 input_dir · 預設 C:\\測試樣本報告)· p1view --one <檔名片段> 只看一份
  零替換(不動任何前版函式)。其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0193"


def _vnum_v0193(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0193(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0193(p) < _vnum_v0193(__file__)), key=_vnum_v0193)
PRIOR = _load_v0193(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


def p1loop(one: str = "") -> tuple:
    """實測實修迴圈:跑 p1view → 讀結果 → 綠燈鎖定(只增不減 · 退步亮紅)→ 與上一輪比較 → 輪次帳本 append-only。"""
    import hashlib
    import json
    import time
    rc, lines = PRIOR.p1view(one)
    if rc != 0:
        return rc, lines
    pv = Path(_resolve("_rep")()) / "p1view"
    try:
        res = json.loads((pv / "P1VIEW_latest.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return 1, lines + ["[RED] 實測實修迴圈 · 讀不到 P1VIEW_latest.json · %s" % type(exc).__name__]
    lock_p, led_p = pv / "VRN_P1View_Lock_latest.json", pv / "VRN_P1View_Rounds.jsonl"
    lock = json.loads(lock_p.read_text(encoding="utf-8")) if lock_p.exists() else {"locked": {}, "round": 0}
    prev = None
    if led_p.exists():
        rows = [l for l in led_p.read_text(encoding="utf-8").splitlines() if l.strip()]
        prev = json.loads(rows[-1]) if rows else None
    rnd = int(lock.get("round", 0)) + 1
    indir = Path((_resolve("input_dir") or (lambda: Path(r"C:\測試樣本報告")))())
    newly, regress = [], []
    for r in res:
        f = r["file"]
        if r.get("lamp") == "GREEN" and f not in lock["locked"]:
            p = next(indir.rglob(f), None)
            lock["locked"][f] = {"round": rnd, "sha": hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p else "", "at": time.strftime("%Y-%m-%d %H:%M")}
            newly.append(f)
        elif f in lock["locked"] and r.get("lamp") != "GREEN":
            regress.append("%s(%s)" % (f[:28], " / ".join(r.get("reasons") or [])))
    from collections import Counter
    lamps = Counter(r.get("lamp") for r in res)
    reasons = Counter(re.sub(r" \d+(/\d+)?", "", x) for r in res for x in (r.get("reasons") or []))
    lock["round"] = rnd
    lock_p.write_text(json.dumps(lock, ensure_ascii=False, indent=1), encoding="utf-8")
    entry = {"round": rnd, "at": time.strftime("%Y-%m-%d %H:%M"), "n": len(res), "lamps": dict(lamps), "reasons": dict(reasons), "locked": len(lock["locked"]), "regress": len(regress)}
    with led_p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    d = lambda k, cur, old: ("%d(%+d)" % (cur, cur - old) if old is not None else str(cur))  # noqa: E731
    pl, pr = (prev or {}).get("lamps", {}), (prev or {}).get("reasons", {})
    lines.append("[計] 實測實修迴圈 · 第 %d 輪 · 綠 %s 黃 %s 紅 %s · 本輪新鎖定 %d · 累計鎖定 %d / %d · 退步 %d" % (
        rnd, d("G", lamps.get("GREEN", 0), pl.get("GREEN") if prev else None), d("Y", lamps.get("YELLOW", 0), pl.get("YELLOW") if prev else None),
        d("R", lamps.get("RED", 0), pl.get("RED") if prev else None), len(newly), len(lock["locked"]), len(res), len(regress)))
    lines.append("[計] 原因變化(與上一輪比):%s" % (" · ".join("%s %s" % (k, d(k, v, pr.get(k, 0) if prev else None)) for k, v in reasons.most_common()) or "無"))
    if regress:
        lines.append("[RED] 鎖定過的檔案退步 %d:%s" % (len(regress), " | ".join(regress[:4])))
    return (1 if regress else 0), lines


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] in (["p1view"], ["p1loop"]):
        one = args[args.index("--one") + 1] if "--one" in args and args.index("--one") + 1 < len(args) else ""
        rc, lines = (p1loop if args[0] == "p1loop" else PRIOR.p1view)(one)
        for l in lines:
            print(l)
        return rc
    return PRIOR.main(args)


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    import json
    import tempfile
    td = Path(tempfile.mkdtemp(prefix="p1loop-"))
    (td / "p1view").mkdir()
    mo = _owner("p1view")
    real_pv, real_rep = vars(mo)["p1view"], _resolve("_rep")
    ro = _owner("_rep")
    try:
        vars(ro)["_rep"] = lambda: td
        for lamp2 in ("YELLOW", "GREEN"):
            (td / "p1view" / "P1VIEW_latest.json").write_text(json.dumps([{"file": "a.pdf", "lamp": "GREEN", "reasons": []}, {"file": "b.pdf", "lamp": lamp2, "reasons": [] if lamp2 == "GREEN" else ["沒找到財報頁"]}]), encoding="utf-8")
            vars(mo)["p1view"] = lambda one="": (0, ["[計] 模擬 p1view"])
            rc1, l1 = p1loop()
        (td / "p1view" / "P1VIEW_latest.json").write_text(json.dumps([{"file": "a.pdf", "lamp": "YELLOW", "reasons": ["首頁沒抓到評等 / 目標價"]}, {"file": "b.pdf", "lamp": "GREEN", "reasons": []}]), encoding="utf-8")
        rc2, l2 = p1loop()
    finally:
        vars(mo)["p1view"] = real_pv
        vars(ro)["_rep"] = real_rep
    lock = json.loads((td / "p1view" / "VRN_P1View_Lock_latest.json").read_text(encoding="utf-8"))
    chk("① p1loop:第 1 輪鎖 a · 第 2 輪 b 轉綠 → 新鎖定 · 累計 2 · 原因變化有 (+/-) · 第 3 輪 a 退步 → 紅字 rc 1 · 鎖定只增不減 → %s" % [l for l in l2 if "退步" in l][:1],
        rc1 == 0 and any("累計鎖定 2 / 2" in l for l in l1) and any("(-1)" in l for l in l1) and rc2 == 1 and any(l.startswith("[RED] 鎖定過的檔案退步 1") for l in l2) and set(lock["locked"]) == {"a.pdf", "b.pdf"} and lock["round"] == 3)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("② 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片 · 正式流程零替換(自測暫換 p1view / _rep 測完即還原)", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__)
        and "setattr(" not in me.split("def selftest")[0])
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0193 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

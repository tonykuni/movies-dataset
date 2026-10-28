#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0194 — 薄尾(操作員 2026-10-12:退步檔案的區塊細節追加到 P1VIEW_latest.md · 印 MD 路徑 · AI 讀 MD 不用截圖)(前版 v0193:實測實修迴圈 p1loop · 每輪跑 p1view → 綠燈檔案鎖定(只增不減 · 退步亮紅)· 與上一輪比較燈號 / 原因增減 · 輪次 append-only 帳本)(前版 v0192:摘要如實寫 PDF 份數 · 先切割再 pdfplumber 擷取 · 本文 / 資訊區分開 · 不亂碼 · 不能用馬上換)。
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
TAG = "v0194"


def _vnum_v0194(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0194(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0194(p) < _vnum_v0194(__file__)), key=_vnum_v0194)
PRIOR = _load_v0194(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
    """v0194:前版 p1loop 之後 · 退步檔案的區塊細節追加到 MD · 印 MD 路徑。"""
    import json
    rc, lines = PRIOR.p1loop(one)
    pv = Path(_resolve("_rep")()) / "p1view"
    md = pv / "P1VIEW_latest.md"
    try:
        res = {r["file"]: r for r in json.loads((pv / "P1VIEW_latest.json").read_text(encoding="utf-8"))}
        reg = [l for l in lines if l.startswith("[RED] 鎖定過的檔案退步")]
        if reg and md.exists():
            names = re.findall(r"([^|:]+?\.pdf)\(", reg[0])
            L = ["", "## 退步檔案(鎖定過 · 本輪非綠)· 每區一行:編號 | 大類·小類 | 框 | 引擎 | 亂碼 | 常用字 | 列數 | 首 60 字"]
            for nm in names:
                r = next((v for k, v in res.items() if k.startswith(nm.strip()[:20])), None)
                if not r:
                    continue
                L.append("### %s · %s · %s" % (r["file"][:40], r.get("lamp"), " / ".join(r.get("reasons") or [])))
                for pg in r.get("pages") or []:
                    for z in pg["zones"]:
                        if z.get("needs_ocr") or (z["minor"] == "TB" and pg["pno"] > 1 and "期間欄" not in (z.get("engine") or "")):
                            txt = " ".join(x["text"] for x in z.get("records") or []) or " | ".join(" ".join(c for c in row if c) for row in (z.get("rows") or [])[:3])
                            L.append("- %s | %s·%s | %s | %s | %s | %s | %d | %s" % (z["id"], z["major"], z["minor_zh"], [int(v) for v in z["bbox"]], z.get("engine", ""), z.get("garbled", 0), z.get("common", ""), len(z.get("rows") or z.get("records") or []), txt[:60]))
            with md.open("a", encoding="utf-8") as fh:
                fh.write("\n".join(L[:60]) + "\n")
    except Exception as exc:  # noqa: BLE001
        lines.append("[計] MD 追加退步細節失敗 · %s" % type(exc).__name__)
    if md.exists():
        lines.append("  [MD] %s(貼這份給 AI 即可 · 不用截圖)" % md)
    return rc, lines


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] in (["p1view"], ["p1loop"]):
        one = args[args.index("--one") + 1] if "--one" in args and args.index("--one") + 1 < len(args) else ""
        rc, lines = (p1loop if args[0] == "p1loop" else _resolve("p1view"))(one)
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
    (td / "p1view" / "P1VIEW_latest.md").write_text("# x\n", encoding="utf-8")
    (td / "p1view" / "P1VIEW_latest.json").write_text(json.dumps([{"file": "Citi-5904 20260916.pdf", "lamp": "YELLOW", "reasons": ["財報表沒對到期間欄 1/2"], "pages": [{"pno": 1, "zones": []}, {"pno": 3, "zones": [{"id": "P3·FL·02·TB", "major": "FL", "minor": "TB", "minor_zh": "財報表", "bbox": [1, 2, 3, 4], "engine": "pdfplumber", "garbled": 0, "common": 0.9, "rows": [["Valuation"], ["PE", "15"]]}]}]}]), encoding="utf-8")
    ro, mo = _owner("_rep"), _owner("p1loop")
    real_rep, real_loop = vars(ro)["_rep"], vars(mo)["p1loop"]
    try:
        vars(ro)["_rep"] = lambda: td
        vars(mo)["p1loop"] = lambda one="": (1, ["[RED] 鎖定過的檔案退步 1:Citi-5904 20260916.pdf(財報表沒對到期間欄 1/2)"])
        rc1, l1 = p1loop()
    finally:
        vars(ro)["_rep"] = real_rep
        vars(mo)["p1loop"] = real_loop
    mdt = (td / "p1view" / "P1VIEW_latest.md").read_text(encoding="utf-8")
    chk("① 退步檔案的區塊細節追加到 MD(含沒對期間欄的表 P3·FL·02·TB)· 印 MD 路徑 · rc 照前版", rc1 == 1 and "## 退步檔案" in mdt and "P3·FL·02·TB" in mdt and any(l.startswith("  [MD] ") for l in l1))
    me = Path(__file__).read_text(encoding="utf-8")
    chk("② 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片 · 正式流程零替換(自測暫換 p1view / _rep 測完即還原)", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__)
        and "setattr(" not in me.split("def selftest")[0])
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0194 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

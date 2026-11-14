#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0238 — 薄尾(邊測邊修:輸出驗證找到表頭列當數據):年度數據的一列若是表頭 —— 值是期間字(凱基 2637 現金流量表「NT$百萬 Dec-23A … Dec-27F」5 筆 · JP 2330「Balance Sheet & Cash Flow Statement FY24A … FY27E」4 筆)· 科目整個是期間字(GS 6415「Jul-25 Oct-25」Jan-26 / Apr-26 2 筆)· 一整列的值都等於期間的年份 —— 整列移出年度數據 · 進剔除冊(帶理由);其餘一筆都不動。獨立驗證器 v0100 判這 11 筆對位(表頭字本來就印在期間那一欄)→ v0101 另查值的種類(HDRVAL)。
  零替換:前版函式一個都不改;前版輸出冊(v0237)整段照跑後再補(直接叫前版包裝)· vrn2 / 成功登記用同一段程式碼重新綁定 · 前版必須是 v0237 · 其餘動詞照前版鏈。
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
import types
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0238"
DISPLAY_NAME = "VRN-2 SystemManager"


def _vnum_v0238(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0238(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0238(p) < _vnum_v0238(__file__)), key=_vnum_v0238)
PRIOR = _load_v0238(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


for _k, _v in list(vars(PRIOR).items()):                                  # 前版名稱借用(唯讀 · 前版模組一個字都不改)
    if not _k.startswith("__") and _k not in globals():
        globals()[_k] = _v


def _rebind(fn):
    """同一段前版程式碼綁到本版名稱空間(程式碼不變 · 前版函式不動 · 只是查名稱時先看本版)。"""
    g = types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)
    g.__kwdefaults__, g.__doc__ = fn.__kwdefaults__, fn.__doc__
    return g


_HDR_PER = re.compile(r"(?i)^(?:(?:FY|CY)['’]?\d{2,4}[AEFPCTH]?|\d{4}(?:[AEFPH]|CT)|\d{1,2}/\d{2,4}[AEF]?|[A-Z][a-z]{2}-\d{2}[AEF]?|[1-4][QH]\d{2}[AEF]?)$")


def _hdr_per(t) -> bool:
    """期間字(Dec-23A · FY24A · 2024E · 2025CT · 12/25 · Jan-26 · 2Q26E · 1H26)· 純數字(2024)不算。"""
    return bool(_HDR_PER.match(str(t or "").strip()))


def _hdr_yr(per) -> str:
    """期間的西元年(2024E → 2024 · FY24A / Dec-24A → 2024 · 12/25 → 2025)· 沒有 → ""。"""
    t = str(per or "")
    m = re.search(r"(?:19|20)\d{2}", t)
    if m:
        return m.group(0)
    m = re.search(r"(?<!\d)(\d{2})(?:[AEFPH]|CT)?$", t)
    return "20" + m.group(1) if m else ""


def _hdr_key(x) -> tuple:
    return (x.get("FILENAME"), x.get("TABLE"), x.get("ROW") or ("S", x.get("SECTION", "")), x.get("ITEM"), x.get("SUBCOL", ""))


def _hdrrows(fin: list) -> tuple:
    """v0238 表頭列不是數據:一列的值是期間字(凱基 2637 現金流量表「NT$百萬 Dec-23A …」· JP 2330「Balance Sheet & Cash Flow Statement FY24A …」)·
    科目整個是期間字(GS 6415「Jul-25 Oct-25」Jan-26 / Apr-26)· 一整列的值都等於期間的年份(2024 2025 …)→ 整列移剔除冊(帶理由)· 其餘不動。"""
    g = defaultdict(list)
    for x in fin:
        g[_hdr_key(x)].append(x)
    why = {}
    for k, xs in g.items():
        it = str(k[3] or "").split()
        pv = [str(x.get("VALUE", "")) for x in xs if _hdr_per(x.get("VALUE"))]
        if pv:
            why[k] = "值是期間字 %s" % " / ".join(pv[:5])
        elif it and all(_hdr_per(t) for t in it):
            why[k] = "科目整個是期間字 %s" % k[3]
        elif len(xs) >= 2 and all(_hdr_yr(x.get("PERIOD")) and re.sub(r"[,\s]", "", str(x.get("VALUE", ""))) == _hdr_yr(x.get("PERIOD")) for x in xs):
            why[k] = "一整列的值都等於期間的年份"
    keep = [x for x in fin if _hdr_key(x) not in why]
    drop = [dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON="表頭列(%s · 不是數據)· 不進年度數據" % why[_hdr_key(x)])
            for x in fin if _hdr_key(x) in why]
    return keep, drop


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0238 = v0237 輸出冊 + 表頭列移出年度數據(進剔除冊 · 帶理由)。"""
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)   # 直接叫前版包裝(不 rebind 包裝 → 不遞迴)
    fin2, hdr = _hdrrows(fin)
    if hdr:
        fin = fin2
        rej = list(_XV_LAST.get("rej") or []) + hdr
        od = v2 / "output"
        made = [m_ for m_ in made if not m_.startswith(("FinancialData(", "Rejected("))]
        made = [_write_book(od, "FinancialData", fin)] + made + [_write_book(od, "Rejected", rej)]
        _XV_LAST["rej"] = rej
    it = _XV_LAST.get("item")
    if it:
        _XV_LAST["item"] = (it[0], it[1], it[2] + " · v0238 表頭列移出 %d 列(%d 筆)" % (len({_hdr_key(x) for x in hdr}), len(hdr)))
    return basic, fin, summ, gaps, made


vrn2 = _rebind(PRIOR.vrn2)                                                # 同一段 vrn2(v0231 程式碼)· 用到本版 _out_books
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0238)


def completion(*a, **k) -> dict:
    """管理器欄寫實際在跑的尾版。"""
    comp = PRIOR.completion(*a, **k)
    comp["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    return comp


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["vrn2"]:
        rc, lines = vrn2(args[1:])
        for l in lines:
            print(l)
        return rc
    return PRIOR.main(args)


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    hr = [{"FILENAME": "k.pdf", "TABLE": "P5", "ROW": 70, "SECTION": "現金流量", "ITEM": "NT$百萬", "PERIOD": p_, "VALUE": p_} for p_ in ("Dec-23A", "Dec-24A", "Dec-25A", "Dec-26F", "Dec-27F")]
    hr += [{"FILENAME": "j.pdf", "TABLE": "P20", "ROW": 20, "ITEM": "Balance Sheet & Cash Flow Statement", "PERIOD": p_, "VALUE": p_} for p_ in ("FY24A", "FY25E", "FY26E", "FY27E")]
    hr += [{"FILENAME": "g.pdf", "TABLE": "P2", "ROW": 39, "ITEM": "Jul-25 Oct-25", "PERIOD": p_, "VALUE": v_} for p_, v_ in (("12/25", "Jan-26"), ("12/27E", "Apr-26"))]
    hr += [{"FILENAME": "y.pdf", "TABLE": "P3", "ROW": 2, "ITEM": "(NT$m)", "PERIOD": p_, "VALUE": v_} for p_, v_ in (("2024A", "2024"), ("2025E", "2025"))]
    ok_rows = [{"FILENAME": "k.pdf", "TABLE": "P5", "ROW": 71, "SECTION": "", "ITEM": "營運活動之現金流量", "PERIOD": p_, "VALUE": v_} for p_, v_ in (("Dec-23A", "6,425"), ("Dec-24A", "9,120"))]
    ok_rows += [{"FILENAME": "y.pdf", "TABLE": "P3", "ROW": 3, "ITEM": "Revenue", "PERIOD": p_, "VALUE": v_} for p_, v_ in (("2024A", "2,024"), ("2025E", "2,310"))]
    ok_rows += [{"FILENAME": "y.pdf", "TABLE": "P3", "ROW": n_, "ITEM": it_, "PERIOD": "2025E", "VALUE": v_}
                for n_, it_, v_ in ((4, "Net debt", "Net cash"), (5, "Margin chg", "0.4pp"), (6, "Interest cover", "NM"), (7, "Dividend", "-"), (8, "EPS", "(4.38)"), (9, "Op cashflow growth", "nm"))]
    kp, dr = _hdrrows(hr + ok_rows)
    chk("⓪ v0238 表頭列(值是期間字 11 筆 · 科目是月份 · 整列等於年份 2 筆)→ 全部移剔除冊(帶理由)· 一般值(6,425 · 2,024 · Net cash · 0.4pp · NM · - · (4.38) · nm)全留 → 留 %d · 移 %d" % (len(kp), len(dr)),
        len(dr) == len(hr) and kp == ok_rows and all(x["BOOK"] == "FinancialData" and x["REASON"].startswith("表頭列(") for x in dr)
        and "值是期間字 Dec-23A" in dr[0]["REASON"] and "一整列的值都等於期間的年份" in dr[-1]["REASON"])
    chk("⓪ v0238 期間字:2Q26E · 1H26 · 2025CT · 12/25 · FY24A 是 · 2024 · 4.38 · (1,234) 不是 · 年份 Dec-24A → 2024 · 12/25 → 2025",
        all(_hdr_per(t) for t in ("2Q26E", "1H26", "2025CT", "12/25", "FY24A", "Jan-26")) and not any(_hdr_per(t) for t in ("2024", "4.38", "(1,234)", "Net cash"))
        and _hdr_yr("Dec-24A") == "2024" and _hdr_yr("12/25") == "2025" and _hdr_yr("2026E") == "2026")
    chk("⓪ v0238 前版必須是 v0237 → %s" % getattr(PRIOR, "TAG", "?"), getattr(PRIOR, "TAG", "") == "v0237")
    chk("⓪ v0238 零替換:vrn2 是同一段程式(重新綁定)", vrn2.__code__ is PRIOR.vrn2.__code__ and vrn2.__globals__ is globals())
    td = Path(tempfile.mkdtemp(prefix="v0238-"))
    try:
        _ob = _out_books([], [], [], td)
        _ob_err = ""
    except BaseException as e:  # noqa: BLE001 — 自測要把遞迴 / 例外當紅燈報出
        _ob, _ob_err = (), type(e).__name__
    chk("⓪ v0238 輸出冊(本版 → v0237 → … → v0232)空輸入跑完不遞迴 %s" % (_ob_err or "· 回傳 %d 項" % len(_ob)), not _ob_err and len(_ob) == 5)
    try:
        _cm = completion(0, 1, 1, True, {}, []).get("manager")
    except Exception as e:  # noqa: BLE001
        _cm = "例外 %s" % type(e).__name__
    chk("⓪ v0238 完成判定的管理器欄 = 實際尾版 → %s" % _cm, _cm == "VRN-2 SystemManager v0238")
    print("  ── 前版 v0237 自測(原樣)──")
    rc_p = PRIOR.selftest()
    chk("⓪ 前版 %s 自測 rc %d" % (PRIOR_PATH.name, rc_p), rc_p == 0)
    print("[計] %s %s(%s)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, Path(__file__).name, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

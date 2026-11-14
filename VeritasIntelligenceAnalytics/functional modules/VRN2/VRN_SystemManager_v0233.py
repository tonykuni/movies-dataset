#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0233 — 薄尾(輸出值驗證修正):⓪ 一標題四重點用摘要器快取的全文(v0231 驗收只存前 240 字 → Daiwa「2025 年 Core Diluted EPS 6.」截斷值)① 數字回原文改比數值(原文千分位「4,200.00」· 字距拆開「3 00 . 0 0」· 小數位不同 → v0232 只比字面,把對的目標價 / 現價剔除進剔除冊)② 一標題四重點:標題 / 重點整理成單行(換行 → 空白 · 中文字間斷行空白去掉 · 頭尾裝飾「- • ⚫」去掉 · 不改字)。
  零替換:前版函式一個都不改;輸出冊 / vrn2 / 成功登記都是前版同一段程式碼重新綁定到本版名稱空間 · 前版必須是 v0232 · 其餘動詞照前版鏈。
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

import copy
import importlib.util
import json
import os
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0233"
DISPLAY_NAME = "VRN-2 SystemManager"


def _vnum_v0233(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0233(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0233(p) < _vnum_v0233(__file__)), key=_vnum_v0233)
PRIOR = _load_v0233(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


def _xv_num_in(v: str, text: str) -> bool:
    """v0233 數字回原文(數值相同即可):原文千分位逗號(4,200.00)· 字距拆開(3 00 . 0 0)· 前置 +/$ 都接受;v0232 只比字面 → 把對的目標價 / 現價剔除。"""
    v = _xv_nfk(v).strip().lstrip("+").replace(",", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?%?", v):
        return v in _xv_nfk(text)
    t = re.sub(r"(?<=[\d.,])\s+(?=[\d.,])", "", _xv_nfk(text))
    t = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", t)
    pat = r"(?<![\d.])" + re.escape(v) + r"(?![\d])"
    if re.search(pat, t):
        return True
    try:                                                                  # 同值不同小數位(4200 ↔ 4200.00)
        fv = float(v.rstrip("%"))
        return any(abs(float(x) - fv) < 1e-9 for x in re.findall(r"(?<![\d.])\d+(?:\.\d+)?(?![\d.])", t))
    except ValueError:
        return False


_CJK = "一-鿿　-〿＀-￯"


def _tidy(t: str) -> str:
    """v0233 標題 / 重點文字整理(不改字):換行 → 空白 · 中文字之間的換行空白去掉(PDF 斷行造成)· 頭尾裝飾符號(- • ⚫)去掉。"""
    t = re.sub(r"\s*\n\s*", " ", t or "")
    t = re.sub(r"(?<=[%s])\s+(?=[%s])" % (_CJK, _CJK), "", t)
    t = re.sub(r"^[\s\-–—•·⚫▪■]+|[\s\-–—•·⚫▪■]+$", "", t)
    return re.sub(r" {2,}", " ", t)


def _full_points(v2: Path) -> dict:
    """摘要器自己的快取(VIA_Reports\\vrn2\\summary\\<雜湊>_<摘要器>.json)= 完整重點文字 · {檔名: [重點全文]}(同檔多份取最新)。"""
    out = {}
    sd = Path(v2) / "summary"
    for p_ in sorted(sd.glob("*.json"), key=lambda x: x.stat().st_mtime) if sd.is_dir() else []:
        try:
            d = json.loads(p_.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if d.get("filename"):
            out[d["filename"]] = [x.get("text") or "" for x in d.get("points") or [] if isinstance(x, dict)]
    return out


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0233 = v0232 同一段輸出冊程式(重新綁定:數字回原文改用本版 _xv_num_in)· 先把摘要重點補成全文(v0231 驗收只存前 240 字 → 「EPS 6.」這種截斷值)
    · 標題 / 四點整理成單行(不改字)。"""
    acc2 = copy.deepcopy(acc or [])
    full = _full_points(v2)
    for e in acc2:
        sm = e.get("summary") or {}
        if sm.get("title"):
            sm["title"] = _tidy(sm["title"])
        for p_ in sm.get("points") or []:
            if isinstance(p_, dict) and p_.get("text"):
                t_ = p_["text"]
                if len(t_) >= 240:                                          # 被截斷 → 用摘要器快取的全文(前綴相同才換)
                    t_ = next((x for x in full.get(e.get("file"), []) if len(x) > len(t_) and x.startswith(t_)), t_)
                p_["text"] = _tidy(t_)
    return _rebind(PRIOR._out_books)(res, acc2, st, v2)


vrn2 = _rebind(PRIOR.vrn2)                                                # 同一段 vrn2(v0231 程式碼)· 用到本版 _out_books
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0233)


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
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    raw = "目標價 NT$4,200.00 收盤價 1,990 前日收盤價 2 7 0 .0 0 元 目標價 3 00 . 0 0 元 上漲空間 +11.1% Price target TWD 2600"
    got = [_xv_num_in(x, raw) for x in ("4200.00", "1990", "270.00", "300.00", "11.1", "2600", "2600.00", "4300.00", "199")]
    chk("⓪ v0233 數字回原文:千分位 / 字距拆開 / 小數位不同都對得到 · 不同數字不會誤對 → %s" % got, got == [True, True, True, True, True, True, True, False, False])
    t = [_tidy(x) for x in ("What's Next? Business\nExtension to Power AI", "公司仍維 持每年營收成長30%的目標", "- AI伺服器需求強勁,明年營運可期", "Strong May-25 Sales Point\n")]
    chk("⓪ v0233 標題 / 重點整理成單行(不改字)→ %s" % t, t == ["What's Next? Business Extension to Power AI", "公司仍維持每年營收成長30%的目標", "AI伺服器需求強勁,明年營運可期", "Strong May-25 Sales Point"])
    import tempfile
    td = Path(tempfile.mkdtemp(prefix="v0233-"))
    (td / "summary").mkdir()
    longp = "X" * 230 + "；2025 年 EPS 6.145 TWD"
    (td / "summary" / "a_e.json").write_text(json.dumps({"filename": "D.pdf", "points": [{"text": longp}]}), encoding="utf-8")
    fp = _full_points(td)
    t_ = longp[:240]
    got_ = next((x for x in fp.get("D.pdf", []) if len(x) > len(t_) and x.startswith(t_)), t_)
    chk("⓪ v0233 截斷的重點(240 字 · 「EPS 6.」)用摘要器快取補回全文 → …%s" % got_[-14:], got_ == longp)
    chk("⓪ v0233 前版必須是 v0232 → %s" % getattr(PRIOR, "TAG", "?"), getattr(PRIOR, "TAG", "") == "v0232")
    chk("⓪ v0233 零替換:vrn2 / 輸出冊 / 成功登記是前版同一段程式(重新綁定)", vrn2.__code__ is PRIOR.vrn2.__code__ and vrn2.__globals__ is globals()
        and _rebind(PRIOR._out_books).__code__ is PRIOR._out_books.__code__ and _success_register.__code__ is PRIOR._success_register.__code__)
    print("  ── 前版 v0232 自測(原樣)──")
    rc_p = PRIOR.selftest()
    chk("⓪ 前版 %s 自測 rc %d" % (PRIOR_PATH.name, rc_p), rc_p == 0)
    print("[計] %s %s(%s)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, Path(__file__).name, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0111 — 薄尾:擷取後日期格式一律 YYYY / YYYY-MM / YYYY-MM-DD · 不同來源同一筆資料寫中間檔(TEMP · 標註來源)交叉對照
  (合併 main 撞號:main 的 v0108 = 他系統表分開命名 VRN-1 / VRN-2 / VCGC · 資料庫流程 db where + db_xcheck(PR #537);
   本變更在分支上原為 v0110,改出 v0111 疊在 main 的 v0108 → v0109 → v0110 之上。
   另兩處:① 體檢 / 對照 / 驗證讀的資料庫家 = 資料庫流程 db where 選的那個(流程結果 db_home;沒跑資料庫流程才照 --db-home …)
   ② 只有一個來源的那筆「一致的來源」是空的(分支舊 v0111 才修的,併進來))
(兩個以上來源相同 = 對照成功)· 心跳略過警告的原始碼行

操作員令(2026-10-20):「時間擷取後格式一律為 YYYY YYYY-MM YYYY-MM-DD;擷取的資料後不同來源擷取相同資料將有中間檔 TEMP 標註不同來源
用來交叉對照使用;相互對照兩個以上相同即算對照成功;自測實測自改自完成,剩餘的你決定」。
現況(倉內盤點):TW 日收盤 交易所(tw_trading_daily · TWSE / TPEX 官方 · 日期原樣存民國 7 碼 1150824,ENG057 又寫 ISO → 同一欄混兩種)
  × Yahoo(tw_daily_prices · 2330.TW);月營收 tw_monthly_revenue 有 source 欄(MOPS_OFFICIAL × CNYES · ym 存 YYYYMM)——
  擷取流程裡沒有任何一步拿不同來源的值互相比對(ENG063 只取官方那筆;ENG098 / ENG102 不在擷取冊)。
本版(只在本版 activate 那一輪 · 擷取 / 引擎 / 資料庫三條流程跑完之後 · 資料庫只唯讀開):
  ⑦ 日期格式體檢:VDF 資料庫家底下每個 .duckdb 的 VDF 表、每個日期欄(欄名看得出是日期;fetched_at 這類紀錄時間不算;他系統 vrn_ 表不列)→
     標準(YYYY / YYYY-MM / YYYY-MM-DD 字串或 DATE 型別)· 不標準的格式與筆數 · 同一欄混兩種以上格式(同一天可能存成兩列)。
     引擎的表照它原本的格式存、本版不改寫:各引擎 upsert 用自己的日期格式當鍵,改寫既有列 → 下一輪原格式再寫進來就成重複列。
  ⑧ 跨來源對照:不同來源抓到的同一筆(資料集 · 代號 · 日期 · 欄位)→ 本輪 temp/xsrc/<資料集>/<資料集>__<來源>.csv(source 欄標註來源 ·
     日期一律標準格式 · 原寫法另欄留)+ <資料集>__對照結果.csv;判定:兩個以上來源相同 = 成功(第三個不同記離群)· 有兩個以上來源但
     沒有任兩個相同 = 衝突 · 只有一個來源 = 沒得對照。相同:價格到 0.01 · 營收整數 · 其他數值照兩邊較粗的小數位(浮點雜訊不算不同)·
     文字全半形 / 大小寫 / 空白統一。資料集:TW 日收盤(最近 10 個交易日,VIA_XSRC_DAYS 可改)· 同一張表有 source 欄且兩個以上來源的
     (月營收等;同一來源同一期抓了好幾次用最新那次)。衝突多半是固定倍數 → 標「疑單位不同」。
  總燈:綠 + 有衝突 → 黃(資料沒對照成功;不擋、不紅)。總覽 JSON 多 datefmt / xsrc 兩節;總覽頁多一張卡;終端 ⑦ ⑧ 兩行。
  心跳:日誌最後一行另外略過「警告的下一行」(Python 印 SyntaxWarning 時下一行縮排印出那行原始碼;工作站每一步都顯示
     VDF_SystemManager_v0155.py 第 6 行那句舊說明)。
  其餘全照 v0110;本版一輪落檔標 v0111;換上的函式只在這一輪(跑完換回原樣,前版自測驗的函式身分不變)。
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境;資料庫只唯讀。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

import copy
import csv
import html
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import threading
import time
import unicodedata
import warnings
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0111(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0111(p) < _vnum_v0111(__file__)), key=_vnum_v0111)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100
_V0101 = vars(PRIOR).get("_V0101")                 # v0101 模組全域(run_step / run_flows / overall / _last_line / STOP 都在這裡查)
_V0106 = vars(PRIOR).get("_V0106")                 # v0106:本輪總覽最後經它的 _WRITE_REPORT_V0100 落檔


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- 日期統一(YYYY · YYYY-MM · YYYY-MM-DD)
_MON = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
_DATE_HINT = re.compile(r"(?i)date|period|month|year|quarter|timestamp|(^|_)(dt|day|time|ts|ym|yyyymm|yr|qtr|asof)($|_)|日期|年月|年度|年份|月份|季別|期間|期別|時間|交易日|資料日")
_TIME_TAIL = re.compile(r"^(?P<d>.+?)(?:[T ]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)$")
_YMD = re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$")
_ROC_YMD = re.compile(r"^(?:民國)?\s*(\d{2,3})[-/.](\d{1,2})[-/.](\d{1,2})$")
_CJK_YMD = re.compile(r"^(?:民國)?\s*(\d{2,4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?$")
_AB_Y = re.compile(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$")
_EN_DMY = re.compile(r"^(\d{1,2})[- ]([A-Za-z]{3})[a-z]*\.?[-, ]+(\d{4})$")
_EN_MDY = re.compile(r"^([A-Za-z]{3})[a-z]*\.?[- ](\d{1,2}),?[- ](\d{4})$")
_YM = re.compile(r"^(\d{4})[-/.](\d{1,2})$")
_ROC_YM = re.compile(r"^(?:民國)?\s*(\d{2,3})[-/.](\d{1,2})$")
_CJK_YM = re.compile(r"^(?:民國)?\s*(\d{2,4})\s*年\s*(\d{1,2})\s*月份?$")
_YMM = re.compile(r"^(\d{4})\s*M(\d{1,2})$", re.I)
_EN_MY = re.compile(r"^([A-Za-z]{3})[a-z]*\.?[-' ]+(\d{2}|\d{4})$")
_MY = re.compile(r"^(\d{1,2})[-/.](\d{4})$")
_Q = re.compile(r"^(?:(\d{4}|\d{2,3})\s*-?\s*Q([1-4])|Q([1-4])\s*[-' ]?\s*(\d{4})|(?:民國)?\s*(\d{2,4})\s*年\s*第?\s*([1-4一二三四])\s*季)$", re.I)
_H = re.compile(r"^(\d{4})\s*-?\s*H([12])$", re.I)
_Y = re.compile(r"^(?:FY|CY)?\s*(\d{4})\s*年?(?:度)?$", re.I)
_ROC_Y = re.compile(r"^(?:民國)?\s*(\d{2,3})\s*年度?$")
_CN_Q = {"一": 1, "二": 2, "三": 3, "四": 4}


def _ok_ymd(y: int, m: int, d: int) -> str | None:
    try:
        return date(y, m, d).isoformat() if 1900 <= y <= 2100 else None
    except ValueError:
        return None


def _ok_ym(y: int, m: int) -> str | None:
    return "%04d-%02d" % (y, m) if 1900 <= y <= 2100 and 1 <= m <= 12 else None


def _roc(y: int) -> int:
    return y + 1911 if y < 1000 else y


def _digits(s: str, hinted: bool) -> tuple:
    """純數字:8 碼 YYYYMMDD · 7 碼民國 YYYMMDD(交易所 1150824)· 6 碼 YYYYMM · 5 碼民國 YYYMM(11507)· 4 碼 YYYY;欄名不像日期 → 不當日期。"""
    if not hinted:
        return None, None, "純數字(欄名不是日期)"
    n = len(s)
    if n == 8:
        r = _ok_ymd(int(s[:4]), int(s[4:6]), int(s[6:]))
        return (r, "D", "YYYYMMDD") if r else (None, None, "不是日期")
    if n == 7:
        r = _ok_ymd(int(s[:3]) + 1911, int(s[3:5]), int(s[5:]))
        return (r, "D", "民國 YYYMMDD") if r else (None, None, "不是日期")
    if n == 6:
        r = _ok_ym(int(s[:4]), int(s[4:]))
        return (r, "M", "YYYYMM") if r else (None, None, "不是日期")
    if n == 5:
        r = _ok_ym(int(s[:3]) + 1911, int(s[3:]))
        return (r, "M", "民國 YYYMM") if r else (None, None, "不是日期")
    if n == 4 and 1900 <= int(s) <= 2100:
        return s, "Y", "YYYY"
    return None, None, "不是日期"


def iso_date(v, hinted: bool = True, order: str = "MDY") -> tuple:
    """一個值 → (標準字串 YYYY / YYYY-MM / YYYY-MM-DD, 粒度 Y/M/D/None, 原格式名)。認不出 → (None, None, 原因)。
    hinted = 欄名看得出是日期欄(純數字 20241001 / 202410 / 2024 才當日期);order = 'a/b/YYYY' 兩邊都 ≤ 12 時的讀法(整欄推)。
    季 → 該季最後一個月(2024Q3 → 2024-09)· 半年 → 6 / 12 月 · 有時刻的只留日期。"""
    if v is None:
        return None, None, "空"
    if isinstance(v, datetime):
        return v.date().isoformat(), "D", "datetime"
    if isinstance(v, date):
        return v.isoformat(), "D", "date"
    if isinstance(v, bool):
        return None, None, "不是日期"
    if isinstance(v, float):
        if v != v:
            return None, None, "空"
        if not v.is_integer():
            return None, None, "不是日期"
        v = int(v)
    if isinstance(v, int):
        return _digits(str(v), hinted) if v >= 0 else (None, None, "不是日期")
    s = str(v).strip()
    if not s or s.lower() in ("nan", "nat", "none", "null", "-", "--"):
        return None, None, "空"
    if re.fullmatch(r"\d+", s):
        return _digits(s, hinted)
    m = _TIME_TAIL.match(s)
    if m and re.search(r"\d", m.group("d")):
        r = iso_date(m.group("d"), hinted, order)
        return (r[0], r[1], r[2] + "+時刻") if r[0] else r
    for rx, f, name in ((_YMD, lambda g: _ok_ymd(int(g[0]), int(g[1]), int(g[2])), "Y-M-D"),
                        (_ROC_YMD, lambda g: _ok_ymd(_roc(int(g[0])), int(g[1]), int(g[2])), "民國 Y/M/D"),
                        (_CJK_YMD, lambda g: _ok_ymd(_roc(int(g[0])), int(g[1]), int(g[2])), "Y年M月D日"),
                        (_EN_DMY, lambda g: _ok_ymd(int(g[2]), _MON.get(g[1].lower(), 0), int(g[0])), "D Mon Y"),
                        (_EN_MDY, lambda g: _ok_ymd(int(g[2]), _MON.get(g[0].lower(), 0), int(g[1])), "Mon D, Y")):
        g = rx.match(s)
        if g:
            r = f(g.groups())
            return (r, "D", name) if r else (None, None, "不是日期")
    g = _AB_Y.match(s)
    if g:
        a, b, y = int(g[1]), int(g[2]), int(g[3])
        if a > 12 or (b <= 12 and order == "DMY"):
            r, name = _ok_ymd(y, b, a), "D/M/Y"
        else:
            r, name = _ok_ymd(y, a, b), "M/D/Y"
        return (r, "D", name) if r else (None, None, "不是日期")
    for rx, f, name in ((_YM, lambda g: _ok_ym(int(g[0]), int(g[1])), "Y-M"),
                        (_ROC_YM, lambda g: _ok_ym(_roc(int(g[0])), int(g[1])), "民國 Y/M"),
                        (_CJK_YM, lambda g: _ok_ym(_roc(int(g[0])), int(g[1])), "Y年M月"),
                        (_YMM, lambda g: _ok_ym(int(g[0]), int(g[1])), "YYYYMmm"),
                        (_EN_MY, lambda g: _ok_ym(int(g[1]) if len(g[1]) == 4 else 2000 + int(g[1]), _MON.get(g[0].lower(), 0)), "Mon Y"),
                        (_MY, lambda g: _ok_ym(int(g[1]), int(g[0])), "M/Y")):
        g = rx.match(s)
        if g:
            r = f(g.groups())
            return (r, "M", name) if r else (None, None, "不是日期")
    g = _Q.match(s)
    if g:
        if g[1]:
            y, q = int(g[1]), int(g[2])
        elif g[3]:
            y, q = int(g[4]), int(g[3])
        else:
            y, q = int(g[5]), _CN_Q.get(g[6]) or int(g[6])
        r = _ok_ym(_roc(y), q * 3)
        return (r, "M", "季→季末月") if r else (None, None, "不是日期")
    g = _H.match(s)
    if g:
        r = _ok_ym(int(g[1]), 6 * int(g[2]))
        return (r, "M", "半年→期末月") if r else (None, None, "不是日期")
    for rx, f, name in ((_Y, lambda g: int(g[0]), "YYYY"), (_ROC_Y, lambda g: _roc(int(g[0])), "民國年")):
        g = rx.match(s)
        if g:
            y = f(g.groups())
            return ("%04d" % y, "Y", name) if 1900 <= y <= 2100 else (None, None, "不是日期")
    return None, None, "認不出"


def date_column(name: str, values: list) -> dict | None:
    """判一欄是不是日期欄並整欄轉:欄名像日期,或(欄名不像)非空值 ≥ 95% 是有分隔的日期字串。
    回 {"values": 轉好的(認不出的照原值), "grain": 主粒度, "formats": {原格式: 筆數}, "bad": 認不出筆數, "n": 非空筆數};不是日期欄 → None。"""
    hinted = bool(_DATE_HINT.search(str(name)))
    vals = list(values)
    order = "MDY"
    for v in vals:                                 # a/b/YYYY 整欄推讀法:有一筆 a > 12 → D/M/Y
        g = _AB_Y.match(str(v).strip()) if isinstance(v, str) else None
        if g and int(g[1]) > 12:
            order = "DMY"
            break
    out, fmts, grains, bad, n = [], {}, {}, 0, 0
    for v in vals:
        r, gr, how = iso_date(v, hinted, order)
        if how == "空":
            out.append(None if v is None or (isinstance(v, float) and v != v) else v)
            continue
        n += 1
        if r is None:
            bad += 1
            out.append(v)
            continue
        fmts[how] = fmts.get(how, 0) + 1
        grains[gr] = grains.get(gr, 0) + 1
        out.append(r)
    if not n:
        return None
    good = n - bad
    if not hinted and (good < 0.95 * n or all(k in ("YYYYMMDD", "YYYYMM", "YYYY", "民國 YYYMMDD", "民國 YYYMM") for k in fmts)):
        return None
    if hinted and good < 0.5 * n:                  # 欄名像日期但多半不是(例如「日成交量」)→ 不當日期欄
        return None
    return {"values": out, "grain": max(grains, key=grains.get) if grains else None, "formats": fmts, "bad": bad, "n": n}


# ---------------------------------------------------------------- 跨來源對照(兩個以上來源相同 = 對照成功)
_NUM = re.compile(r"^\(?[-+]?[\d,]*\.?\d+(?:[eE][-+]?\d+)?\)?%?$")


def _num(v):
    """'1,234.50' / 1234.5 / '(12.3)' / '12.3%' → (數值, 小數位);整數(沒有小數點)當精確值 = 6 位;不是數 → None。"""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return float(v), 6
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return None
        r = repr(v)
        return v, (min(len(r.split(".")[1]), 6) if "." in r and "e" not in r else 6)
    s = unicodedata.normalize("NFKC", str(v)).strip().replace(" ", "")
    if not s or not _NUM.match(s):
        return None
    neg = s.startswith("(") and s.endswith(")")
    t = s.strip("()").rstrip("%").replace(",", "")
    try:
        x = float(t)
    except ValueError:
        return None
    dec = min(len(t.split(".")[1]), 6) if "." in t and "e" not in t.lower() else 6
    return (-x if neg else x), dec


def same(a, b, dec: int | None = None) -> bool:
    """兩個來源的值算不算相同:數值 → 差距在兩邊較粗的那個小數位的半格內(1045.00 = 1045.0 = 1044.9999999 · 100 ≠ 100.4);
    dec 給定(資料集規格:價格 2 位 · 營收 0 位)→ 差距在 dec 位的半格內(10.3 ≠ 10.35);
    文字 → NFKC 全半形統一、去空白、不分大小寫後相等。"""
    na, nb = _num(a), _num(b)
    if na and nb:
        d = dec if dec is not None else min(na[1], nb[1], 6)
        return abs(na[0] - nb[0]) <= 0.5 * 10 ** (-d) + 1e-12 * max(1.0, abs(na[0]), abs(nb[0]))
    if na or nb:
        return False
    ta = re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(a or ""))).casefold()
    tb = re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(b or ""))).casefold()
    return bool(ta) and ta == tb


def cross_check(rows: list) -> dict:
    """rows:[{dataset, key, date, field, value, source(, dec)}] → 每個(資料集 · 代號 · 日期 · 欄位)一筆判定:
    VERIFIED = 兩個以上來源相同(有第三個不同 → 記 outliers)· CONFLICT = 兩個以上來源但沒有任兩個相同 · SINGLE = 只有一個來源(沒得對照)。"""
    g: dict = {}
    decs: dict = {}
    for r in rows:
        k = (r["dataset"], str(r["key"]), r["date"], r["field"])
        g.setdefault(k, {}).setdefault(r["source"], r["value"])
        decs.setdefault(k, r.get("dec"))
    items, cnt = [], {"VERIFIED": 0, "CONFLICT": 0, "SINGLE": 0}
    for k, by in sorted(g.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        srcs = sorted(by)
        if len(srcs) < 2:
            st, agree, out = "SINGLE", [], []        # 只有一個來源:沒有「一致」可言(頁面不誤讀)
        else:
            best: list = []
            for i, a in enumerate(srcs):
                grp = [a] + [b for b in srcs[i + 1:] if same(by[a], by[b], decs.get(k))]
                if len(grp) > len(best):
                    best = grp
            st = "VERIFIED" if len(best) >= 2 else "CONFLICT"
            agree = best if st == "VERIFIED" else []
            out = [s for s in srcs if s not in agree] if st == "VERIFIED" else srcs
        cnt[st] += 1
        items.append({"dataset": k[0], "key": k[1], "date": k[2], "field": k[3], "status": st, "sources": srcs,
                      "agree": agree, "outliers": out if st == "VERIFIED" else [], "values": {s: by[s] for s in srcs}})
    pairs = cnt["VERIFIED"] + cnt["CONFLICT"]
    return {"counts": cnt, "comparable": pairs, "rate": (cnt["VERIFIED"] / pairs) if pairs else None, "items": items}


# ---------------------------------------------------------------- 擷取後:讀 VDF 資料庫(唯讀)
_OTHER_SYS = re.compile(r"(?i)^(vrn_|vrn2_|via_policy|cgc_|vcgc_)")      # 他系統寫進來的表:只攤開不代修(同 VDF_SystemManager v0155)
_META_COL = re.compile(r"(?i)^(fetched_at|updated_at|created_at|inserted_at|loaded_at|ingested_at|_?ts|run_ts|write_ts)$")
_KEY_COL = re.compile(r"(?i)^(code|ticker|symbol|stock_id|series|series_id|isin|代號|證券代號|股票代號)$")
_STD = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
_SPEC_DEC = {"close": 2, "open": 2, "high": 2, "low": 2, "revenue": 0}     # 價格到 0.01 · 營收整數(千元)


def _duck():
    try:
        import duckdb
        return duckdb
    except ImportError:
        return None


def _q(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _connect_ro(path: Path, tries: int = 3):
    """唯讀開庫;被別的行程鎖著 → 等一下再試;還是不行 → (None, 原因)。"""
    duckdb = _duck()
    why = ""
    for i in range(tries):
        try:
            return duckdb.connect(str(path), read_only=True), ""
        except Exception as exc:                   # noqa: BLE001 — 鎖 / 版本不合 / 壞檔都照實回原因,不中斷整輪
            why = "%s:%s" % (type(exc).__name__, str(exc).splitlines()[0][:120] if str(exc) else "")
            time.sleep(0.5 * (i + 1))
    return None, why


def db_files(opt) -> list:
    """本輪資料庫家:--db-home > VIA_VDF_DB_HOME > --fetch-home/output_hub > 本夾 output_hub;底下所有 .duckdb(去重)。"""
    roots = [getattr(opt, "db_home", None), os.environ.get("VIA_VDF_DB_HOME")]
    fh = getattr(opt, "fetch_home", None)
    if fh:
        roots.append(str(Path(fh) / "output_hub"))
    roots.append(str(HERE / "output_hub"))
    seen, out = set(), []
    for r in roots:
        if not r or not Path(r).is_dir():
            continue
        for f in sorted(Path(r).rglob("*.duckdb")):
            k = os.path.normcase(str(f.resolve()))
            if k not in seen and not f.name.endswith(".wal"):
                seen.add(k)
                out.append(f)
    return out


def _tables(con) -> list:
    rows = con.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' "
                       "AND table_schema NOT IN ('information_schema', 'pg_catalog')").fetchall()
    return [(s, t) for s, t in rows]


def _columns(con, schema: str, table: str) -> list:
    return con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = ? AND table_name = ? "
                       "ORDER BY ordinal_position", [schema, table]).fetchall()


def datefmt_audit(dbs: list, budget_s: float = 120.0) -> dict:
    """日期格式體檢(唯讀):VDF 的表裡每個日期欄 → 標準(YYYY / YYYY-MM / YYYY-MM-DD 或 DATE 型別)· 不標準的格式與筆數 ·
    同一欄混了兩種以上格式(同一天可能存成兩列)。他系統的表 · 紀錄時間戳(fetched_at …)不列。"""
    t0, cols, skipped, locked = time.time(), [], 0, []
    for f in dbs:
        if time.time() - t0 > budget_s:
            skipped += 1
            continue
        con, why = _connect_ro(f)
        if con is None:
            locked.append({"db": f.name, "why": why})
            continue
        try:
            for sch, tb in _tables(con):
                if _OTHER_SYS.match(tb):
                    continue
                for col, typ in _columns(con, sch, tb):
                    if _META_COL.match(col) or not _DATE_HINT.search(col):
                        continue
                    typ_u = str(typ).upper()
                    ref = "%s.%s" % (_q(sch), _q(tb))
                    row = {"db": f.name, "table": tb if sch == "main" else "%s.%s" % (sch, tb), "column": col, "type": typ_u}
                    try:
                        if typ_u == "DATE":
                            row.update(standard=True, formats={"DATE 型別": 1}, nonstd=0, examples=[])
                        elif typ_u.startswith("TIMESTAMP"):
                            n_t = con.execute("SELECT count(*) FROM %s WHERE %s IS NOT NULL AND CAST(%s AS TIME) <> TIME '00:00:00'"
                                              % (ref, _q(col), _q(col))).fetchone()[0]
                            row.update(standard=n_t == 0, formats={"TIMESTAMP(有時刻)" if n_t else "TIMESTAMP(都是 00:00)": 1},
                                       nonstd=int(n_t), examples=[])
                        elif any(k in typ_u for k in ("CHAR", "TEXT", "STRING", "INT")):
                            vals = [r[0] for r in con.execute("SELECT DISTINCT CAST(%s AS VARCHAR) FROM %s WHERE %s IS NOT NULL LIMIT 20000"
                                                              % (_q(col), ref, _q(col))).fetchall()]
                            fm, bad_ex, nonstd = {}, [], 0
                            for v in vals:
                                r_, gr, how = iso_date(v, True)
                                if r_ is not None and r_ == v and _STD.match(v):
                                    how = "標準"
                                elif r_ is None:
                                    how = "認不出"
                                fm[how] = fm.get(how, 0) + 1
                                if how != "標準":
                                    nonstd += 1
                                    if len(bad_ex) < 3:
                                        bad_ex.append(v)
                            if not vals or (fm.get("認不出", 0) > 0.5 * len(vals)):
                                continue                   # 欄名像日期但多半不是日期(例如 day_volume)→ 不列
                            row.update(standard=nonstd == 0, formats=fm, nonstd=nonstd, examples=bad_ex, distinct=len(vals))
                        else:
                            continue
                    except Exception as exc:       # noqa: BLE001 — 一欄讀不到不擋整張體檢
                        row.update(standard=None, formats={}, nonstd=0, examples=[], error=type(exc).__name__)
                    row["mixed"] = len([k for k in row.get("formats", {}) if k not in ("認不出",)]) > 1
                    cols.append(row)
        finally:
            con.close()
    bad = [c for c in cols if c.get("standard") is False]
    lamp = "INFO" if not cols and not dbs else ("YELLOW" if bad or locked else "GREEN")
    return {"lamp": lamp, "dbs": len(dbs), "columns": len(cols), "standard": sum(1 for c in cols if c.get("standard")),
            "nonstandard": len(bad), "mixed": sum(1 for c in bad if c.get("mixed")), "locked": locked, "skipped_budget": skipped,
            "items": cols, "secs": round(time.time() - t0, 1)}


def _find(dbs: list, table: str):
    for f in dbs:
        con, _why = _connect_ro(f, 1)
        if con is None:
            continue
        try:
            if any(t == table and s == "main" for s, t in _tables(con)):
                return f, {c.lower(): c for c, _t in _columns(con, "main", table)}
        finally:
            con.close()
    return None, {}


def _pick_dates(con, table: str, col: str, n: int, grain: str) -> dict:
    """這張表最近 n 個(標準化後)日期 → {原始字串: 標準日期};同一天不同格式都收(對照用標準日期)。"""
    raw = [r[0] for r in con.execute("SELECT DISTINCT CAST(%s AS VARCHAR) FROM %s WHERE %s IS NOT NULL" % (_q(col), _q(table), _q(col))).fetchall()]
    m = {}
    for v in raw:
        r_, gr, _how = iso_date(v, True)
        if r_ and gr == grain:
            m[v] = r_
    keep = set(sorted(set(m.values()))[-n:])
    return {k: v for k, v in m.items() if v in keep}


def extract_tw_close(dbs: list, n_days: int = 10) -> tuple:
    """TW 日收盤:交易所(tw_trading_daily · TWSE / TPEX 官方收盤)× Yahoo(tw_daily_prices)· 同代號同日同欄位。"""
    rows, notes = [], []
    fe, ce = _find(dbs, "tw_trading_daily")
    fy, cy = _find(dbs, "tw_daily_prices")
    if not fe or not fy:
        return rows, ["缺表:" + "、".join(t for t, f in (("tw_trading_daily", fe), ("tw_daily_prices", fy)) if not f)]
    fields = [k for k in ("close", "open", "high", "low") if k in ce and k in cy]
    con, why = _connect_ro(fe)
    if con is None:
        return rows, ["%s 開不了:%s" % (fe.name, why)]
    try:
        dm = _pick_dates(con, "tw_trading_daily", ce["date"], n_days, "D")
        want = sorted(set(dm.values()))
        sel = ", ".join(_q(ce[k]) for k in fields)
        for d, code, mkt, *vals in con.execute(
                "SELECT CAST(%s AS VARCHAR), CAST(%s AS VARCHAR), CAST(%s AS VARCHAR), %s FROM tw_trading_daily WHERE list_contains(?, CAST(%s AS VARCHAR))"
                % (_q(ce["date"]), _q(ce["code"]), _q(ce.get("market", "market")), sel, _q(ce["date"])), [list(dm)]).fetchall():
            for k, v in zip(fields, vals):
                if v is not None:
                    rows.append({"dataset": "tw_daily_close", "source": str(mkt or "交易所").upper(), "key": str(code).strip(), "date": dm[d],
                                 "field": k, "value": v, "date_raw": d, "origin": "%s:tw_trading_daily" % fe.name, "dec": _SPEC_DEC.get(k)})
    finally:
        con.close()
    con, why = _connect_ro(fy)
    if con is None:
        return rows, ["%s 開不了:%s" % (fy.name, why)]
    try:
        dmy = {k: v for k, v in _pick_dates(con, "tw_daily_prices", cy["date"], n_days + 5, "D").items() if v in set(want)}
        sel = ", ".join(_q(cy[k]) for k in fields)
        for d, tk, *vals in con.execute(
                "SELECT CAST(%s AS VARCHAR), CAST(%s AS VARCHAR), %s FROM tw_daily_prices WHERE list_contains(?, CAST(%s AS VARCHAR))"
                % (_q(cy["date"]), _q(cy["ticker"]), sel, _q(cy["date"])), [list(dmy)]).fetchall():
            code = str(tk).split(".")[0].strip()
            for k, v in zip(fields, vals):
                if v is not None:
                    rows.append({"dataset": "tw_daily_close", "source": "YAHOO", "key": code, "date": dmy[d], "field": k, "value": v,
                                 "date_raw": d, "origin": "%s:tw_daily_prices" % fy.name, "dec": _SPEC_DEC.get(k)})
    finally:
        con.close()
    notes.append("最近 %d 個交易日(%s → %s)· 欄位 %s" % (len(want), want[0] if want else "—", want[-1] if want else "—", "/".join(fields)))
    return rows, notes


def extract_source_tables(dbs: list, n_periods: dict | None = None) -> tuple:
    """同一張表裡有 source 欄、兩個以上來源(例如月營收 MOPS_OFFICIAL × CNYES)→ 同代號同期別的數值欄逐欄對照;
    同一來源同一期抓了好幾次 → 用最新那次(fetched_at)。"""
    n_periods = n_periods or {"D": 10, "M": 3, "Y": 2}
    rows, notes = [], []
    for f in dbs:
        con, why = _connect_ro(f)
        if con is None:
            continue
        try:
            for sch, tb in _tables(con):
                if sch != "main" or _OTHER_SYS.match(tb):
                    continue
                cols = _columns(con, sch, tb)
                names = {c.lower(): c for c, _t in cols}
                if "source" not in names:
                    continue
                keys = [c for c, _t in cols if _KEY_COL.match(c)]
                dcol = next((c for c, _t in cols if _DATE_HINT.search(c) and not _META_COL.match(c)), None)
                nums = [c for c, t in cols if any(x in str(t).upper() for x in ("INT", "DOUBLE", "DECIMAL", "FLOAT", "REAL", "NUMERIC"))
                        and c not in keys and c != dcol and not _META_COL.match(c)]
                if not keys or not dcol or not nums:
                    continue
                nsrc = con.execute("SELECT count(DISTINCT source) FROM %s" % _q(tb)).fetchone()[0]
                if nsrc < 2:
                    continue
                gr = "M" if re.search(r"(?i)ym|month|年月|月份", dcol) else ("Y" if re.search(r"(?i)year|年度|年份", dcol) else "D")
                dm = _pick_dates(con, tb, dcol, n_periods.get(gr, 3), gr)
                if not dm:
                    continue
                order = ("ORDER BY %s DESC" % _q(names["fetched_at"])) if "fetched_at" in names else ""
                kexpr = " || '|' || ".join("CAST(%s AS VARCHAR)" % _q(k) for k in keys)
                q = ("SELECT CAST(%s AS VARCHAR) AS d, %s AS k, CAST(source AS VARCHAR) AS s, %s FROM %s WHERE list_contains(?, CAST(%s AS VARCHAR)) "
                     "QUALIFY row_number() OVER (PARTITION BY CAST(%s AS VARCHAR), %s, source %s) = 1"
                     % (_q(dcol), kexpr, ", ".join(_q(c) for c in nums), _q(tb), _q(dcol), _q(dcol), kexpr, order))
                n0 = len(rows)
                for d, k, src, *vals in con.execute(q, [list(dm)]).fetchall():
                    for c, v in zip(nums, vals):
                        if v is not None:
                            rows.append({"dataset": tb, "source": str(src), "key": k, "date": dm[d], "field": c, "value": v, "date_raw": d,
                                         "origin": "%s:%s" % (f.name, tb), "dec": _SPEC_DEC.get(c.lower())})
                notes.append("%s:來源 %d 個 · 最近 %d 期 · %d 筆" % (tb, nsrc, len(set(dm.values())), len(rows) - n0))
        finally:
            con.close()
    return rows, notes


def write_temp(xdir: Path, rows: list, result: dict) -> dict:
    """中間檔(本輪 temp):每個資料集每個來源一檔(標註來源)+ 一份對照結果;日期一律 YYYY / YYYY-MM / YYYY-MM-DD。"""
    files = []
    by: dict = {}
    for r in rows:
        by.setdefault((r["dataset"], r["source"]), []).append(r)
    for (ds, src), rs in sorted(by.items()):
        d = xdir / re.sub(r"[^\w.-]+", "_", ds)
        d.mkdir(parents=True, exist_ok=True)
        p = d / ("%s__%s.csv" % (re.sub(r"[^\w.-]+", "_", ds), re.sub(r"[^\w.-]+", "_", src)))
        with open(p, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["dataset", "source", "key", "date", "field", "value", "date_raw", "origin"])
            for r in sorted(rs, key=lambda x: (x["key"], x["date"], x["field"])):
                w.writerow([r["dataset"], r["source"], r["key"], r["date"], r["field"], r["value"], r["date_raw"], r["origin"]])
        files.append(str(p))
    for ds in sorted({i["dataset"] for i in result["items"]}):
        d = xdir / re.sub(r"[^\w.-]+", "_", ds)
        d.mkdir(parents=True, exist_ok=True)
        p = d / ("%s__對照結果.csv" % re.sub(r"[^\w.-]+", "_", ds))
        with open(p, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["dataset", "key", "date", "field", "status", "sources", "agree", "outliers", "values"])
            for i in result["items"]:
                if i["dataset"] == ds:
                    w.writerow([i["dataset"], i["key"], i["date"], i["field"], i["status"], "/".join(i["sources"]), "/".join(i["agree"]),
                                "/".join(i["outliers"]), json.dumps(i["values"], ensure_ascii=False, default=str)])
        files.append(str(p))
    return {"dir": str(xdir), "files": files}


def _unit_hint(items: list) -> str:
    """衝突多半是固定倍數(×1000 / ÷1000)→ 疑單位不同(千元 ↔ 元)。"""
    rs = []
    for i in items:
        v = [x for x in (_num(i["values"][s]) for s in i["sources"]) if x]
        if len(v) == 2 and v[0][0]:
            rs.append(v[1][0] / v[0][0])
    if len(rs) < 5:
        return ""
    rs.sort()
    med = rs[len(rs) // 2]
    for f in (1000.0, 0.001, 100.0, 0.01):
        if abs(med / f - 1) < 0.01:
            return "衝突多半差 ×%g(疑單位不同,不是抓錯)" % f
    return ""


def post_fetch(opt, res: dict) -> dict:
    """擷取流程跑完後:① 日期格式體檢 ② 跨來源對照(中間檔 → 本輪 temp/xsrc)。全程唯讀資料庫;任何一段出錯照實記,不擋整輪。"""
    t0 = time.time()
    out = {"datefmt": None, "xsrc": None}
    if _duck() is None:
        msg = "這支 python 沒有 duckdb(不代裝)· 不體檢、不對照"
        out["datefmt"] = {"lamp": "INFO", "note": msg, "items": []}
        out["xsrc"] = {"lamp": "INFO", "note": msg, "datasets": {}, "items": []}
        return out
    dbs = db_files(opt)
    try:
        out["datefmt"] = datefmt_audit(dbs, float(os.environ.get("VIA_XSRC_BUDGET_S", "120")))
    except Exception as exc:                       # noqa: BLE001
        out["datefmt"] = {"lamp": "YELLOW", "note": "體檢出錯:%s" % type(exc).__name__, "items": []}
    rows, notes = [], []
    for fn in (lambda: extract_tw_close(dbs, int(os.environ.get("VIA_XSRC_DAYS", "10"))), lambda: extract_source_tables(dbs)):
        try:
            r_, n_ = fn()
            rows += r_
            notes += n_
        except Exception as exc:                   # noqa: BLE001
            notes.append("讀取出錯:%s %s" % (type(exc).__name__, str(exc)[:120]))
    result = cross_check(rows)
    xdir = Path(res["temp_run"]) / "xsrc"
    files = write_temp(xdir, rows, result) if rows else {"dir": str(xdir), "files": []}
    per = {}
    for i in result["items"]:
        c = per.setdefault(i["dataset"], {"VERIFIED": 0, "CONFLICT": 0, "SINGLE": 0, "sources": set()})
        c[i["status"]] += 1
        c["sources"].update(i["sources"])
    for ds, c in per.items():
        c["sources"] = sorted(c["sources"])
        cmp_ = c["VERIFIED"] + c["CONFLICT"]
        c["rate"] = round(c["VERIFIED"] / cmp_, 4) if cmp_ else None
        c["hint"] = _unit_hint([i for i in result["items"] if i["dataset"] == ds and i["status"] == "CONFLICT"])
    cnt = result["counts"]
    lamp = "INFO" if not result["comparable"] else ("YELLOW" if cnt["CONFLICT"] else "GREEN")
    conflicts = [i for i in result["items"] if i["status"] == "CONFLICT"]
    out["xsrc"] = {"lamp": lamp, "counts": cnt, "comparable": result["comparable"], "rate": result["rate"], "datasets": per, "notes": notes,
                   "temp": files, "dbs": [f.name for f in dbs], "conflicts_top": conflicts[:30], "secs": round(time.time() - t0, 1)}
    return out


# ---------------------------------------------------------------- 心跳:警告的下一行(縮排印出的那行原始碼)也略過
_WARN_HEAD = re.compile(r"(^|\s)(\S.*?\.py|<unknown>|<string>):\d+: \w*Warning\b|SyntaxWarning|DeprecationWarning")


def _last_line(log: Path) -> str:
    """同 v0102 _last_line(日誌最後一行,最多 110 字 · 略過編譯警告),另外略過警告「下一行」那行被印出來的原始碼
    (工作站:VDF_SystemManager_v0155.py:6 的 SyntaxWarning 後面跟著它說明文字那一行 → 每一步的心跳都顯示同一句舊說明)。"""
    try:
        with open(log, "rb") as fh:
            fh.seek(0, 2)
            n = fh.tell()
            fh.seek(max(0, n - 8192))
            tail = fh.read().decode("utf-8", "replace")
    except OSError:
        return ""
    keep, skip_next = [], False
    for ln in tail.splitlines():
        if skip_next:
            skip_next = False
            if ln[:1] in (" ", "\t"):
                continue
        st = ln.strip()
        if not st:
            continue
        if _WARN_HEAD.search(st):
            skip_next = True
            continue
        keep.append(st)
    return keep[-1][:110] if keep else ""


# ---------------------------------------------------------------- 本輪:流程跑完 → 體檢 + 對照;總燈 / 總覽 / 頁面
_POST: dict = {}
_LOCK10 = threading.Lock()


def _home_from_flows(flows) -> str | None:
    """main v0108 的資料庫流程先問 db where,選到的家記在流程結果 db_home;體檢 / 對照 / 驗證用同一個家(PR #537 Codex P1 同理)。"""
    for f in flows or []:
        h = (f or {}).get("db_home")
        if h:
            return str(h)
    return None


def _with_home(opt, flows):
    h = _home_from_flows(flows)
    if not h or h == getattr(opt, "db_home", None):
        return opt
    o = copy.copy(opt)
    o.db_home = h
    return o


def _run_flows_layer(prev):
    def run_flows(opt, res, gate, log_dir, lists, manager=None, py=None):
        flows = prev(opt, res, gate, log_dir, lists, manager, py)
        if _V0101["STOP"].is_set():
            return flows
        print("  ⑦ 擷取後:日期格式體檢 + 跨來源對照(唯讀資料庫 · 中間檔寫本輪 temp)…", flush=True)
        opt2 = _with_home(opt, flows)
        if getattr(opt2, "db_home", None):
            print("     · 資料庫家 %s%s" % (opt2.db_home, "(資料庫流程 db where 選的)" if opt2 is not opt else ""), flush=True)
        try:
            post = post_fetch(opt2, res)
        except Exception as exc:                   # noqa: BLE001 — 這一段出錯不擋整輪,照實寫進總覽
            post = {"datefmt": {"lamp": "YELLOW", "note": "出錯:%s" % type(exc).__name__, "items": []},
                    "xsrc": {"lamp": "YELLOW", "note": "出錯:%s %s" % (type(exc).__name__, str(exc)[:160]), "datasets": {}, "items": []}}
        with _LOCK10:
            _POST.update(post)
        for line in summary_lines(post):
            print(line, flush=True)
        return flows
    return run_flows


def summary_lines(post: dict) -> list:
    df, xs = post.get("datefmt") or {}, post.get("xsrc") or {}
    out = []
    if df.get("note"):
        out.append("  ⑦ 日期格式 %s:%s" % (df.get("lamp"), df["note"]))
    else:
        bad = [c for c in df.get("items", []) if c.get("standard") is False]
        ex = ";".join("%s.%s %s" % (c["table"], c["column"], "/".join("%s×%s" % kv for kv in c["formats"].items() if kv[0] != "標準"))
                      for c in bad[:3])
        out.append("  ⑦ 日期格式 %s:資料庫 %s 個 · 日期欄 %s · 標準 %s · 不標準 %s(混兩種以上格式 %s)%s%s" % (
            df.get("lamp"), df.get("dbs"), df.get("columns"), df.get("standard"), df.get("nonstandard"), df.get("mixed"),
            (" · " + ex) if ex else "", (" · 鎖住 %d 個庫" % len(df["locked"])) if df.get("locked") else ""))
    if xs.get("note"):
        out.append("  ⑧ 跨來源對照 %s:%s" % (xs.get("lamp"), xs["note"]))
    else:
        c = xs.get("counts") or {}
        out.append("  ⑧ 跨來源對照 %s:可對照 %s 筆 · 成功(兩個以上來源相同)%s · 衝突 %s · 只有一個來源 %s · 成功率 %s" % (
            xs.get("lamp"), xs.get("comparable"), c.get("VERIFIED"), c.get("CONFLICT"), c.get("SINGLE"),
            ("%.2f%%" % (100 * xs["rate"])) if xs.get("rate") is not None else "—"))
        for ds, d in (xs.get("datasets") or {}).items():
            out.append("     · %s(%s):成功 %d · 衝突 %d · 單一來源 %d%s" % (ds, "/".join(d["sources"]), d["VERIFIED"], d["CONFLICT"], d["SINGLE"],
                                                                     (" · " + d["hint"]) if d.get("hint") else ""))
        for n in xs.get("notes") or []:
            out.append("     · " + n)
        if (xs.get("temp") or {}).get("files"):
            out.append("     · 中間檔(依來源分檔 + 對照結果)→ %s" % xs["temp"]["dir"])
    return out


def _overall_layer(prev):
    def overall(lists, flows):
        lamp = prev(lists, flows)
        with _LOCK10:
            xs = _POST.get("xsrc") or {}
        if lamp == "GREEN" and xs.get("lamp") == "YELLOW":
            return "YELLOW"                        # 有來源對不上(衝突)= 資料沒對照成功 → 黃(不擋、不紅)
        return lamp
    return overall


def _stamp_layer(prev):
    """總覽落檔最內層:標 v0111 + 放進體檢 / 對照兩節(總覽落檔函式本身不換 → v0109 ㊶ · v0110 ㊼ 照驗)。"""
    def _stamp_then_write(c, u=None):
        c["schema"], c["tag"] = "VDF_ActivateVDF_v0111", TAG
        with _LOCK10:
            if _POST:
                c["datefmt"] = _POST.get("datefmt")
                c["xsrc"] = {k: (sorted(v) if isinstance(v, set) else v) for k, v in (_POST.get("xsrc") or {}).items()}
        return prev(c, u) if u is not None else prev(c)
    return _stamp_then_write


def xsrc_card(card: dict) -> str:
    """總覽頁「擷取後:日期格式 · 跨來源對照」卡(本輪有跑才有)。"""
    df, xs = card.get("datefmt"), card.get("xsrc")
    if not df and not xs:
        return ""
    e = html.escape
    color = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "INFO": "#57606a"}
    parts = ['<section id="xsrc" class="card" style="margin:12px 0"><b>擷取後:跨來源對照</b> '
             f'<span class="lamp" style="background:{color.get((xs or {}).get("lamp"), "#cf222e")}">{e(str((xs or {}).get("lamp")))}</span>']
    if xs and xs.get("note"):
        parts.append(f"<br>{e(xs['note'])}")
    elif xs:
        c = xs.get("counts") or {}
        rate = ("%.2f%%" % (100 * xs["rate"])) if xs.get("rate") is not None else "—"
        parts.append(f"<br>可對照 {e(str(xs.get('comparable')))} 筆 · <b>成功 {e(str(c.get('VERIFIED')))}</b>(兩個以上來源相同)· "
                     f"衝突 {e(str(c.get('CONFLICT')))} · 只有一個來源 {e(str(c.get('SINGLE')))} · 成功率 {e(rate)}")
        rows = "".join(f"<tr><td>{e(ds)}</td><td>{e('/'.join(d['sources']))}</td><td>{d['VERIFIED']}</td><td>{d['CONFLICT']}</td>"
                       f"<td>{d['SINGLE']}</td><td>{e(d.get('hint') or '')}</td></tr>" for ds, d in (xs.get("datasets") or {}).items())
        if rows:
            parts.append('<div class="wrap" style="overflow-x:auto"><table><tr><th>資料集</th><th>來源</th><th>成功</th><th>衝突</th>'
                         f'<th>單一來源</th><th>備註</th></tr>{rows}</table></div>')
        cf = xs.get("conflicts_top") or []
        if cf:
            li = "".join(f"<li>{e(i['dataset'])} · {e(i['key'])} · {e(i['date'])} · {e(i['field'])}:"
                         f"{e(' / '.join('%s %s' % (s, i['values'][s]) for s in i['sources']))}</li>" for i in cf[:15])
            parts.append(f"<details><summary>衝突前 {min(15, len(cf))} 筆</summary><ul>{li}</ul></details>")
        if (xs.get("temp") or {}).get("dir"):
            parts.append(f'<br><span class="mut">中間檔(本輪 temp · 依來源分檔、日期一律 YYYY / YYYY-MM / YYYY-MM-DD):{e(xs["temp"]["dir"])}</span>')
    if df:
        parts.append(f'<br><b>日期格式體檢</b> <span class="lamp" style="background:{color.get(df.get("lamp"), "#cf222e")}">{e(str(df.get("lamp")))}</span> ')
        if df.get("note"):
            parts.append(e(df["note"]))
        else:
            parts.append(f"日期欄 {e(str(df.get('columns')))} · 標準 {e(str(df.get('standard')))} · 不標準 {e(str(df.get('nonstandard')))}"
                         f"(混兩種以上格式 {e(str(df.get('mixed')))})")
            bad = [c for c in df.get("items", []) if c.get("standard") is False]
            if bad:
                li = "".join(f"<li>{e(c['db'])} · {e(c['table'])}.{e(c['column'])}({e(c['type'])}):"
                             f"{e(', '.join('%s ×%s' % kv for kv in c['formats'].items()))}"
                             f"{(' · 例 ' + e(' / '.join(map(str, c.get('examples') or [])))) if c.get('examples') else ''}</li>" for c in bad[:20])
                parts.append(f"<details><summary>不標準的欄 {len(bad)} 個</summary><ul>{li}</ul></details>")
            parts.append('<br><span class="mut">引擎的表照它原本的格式存(它們的 upsert 用這個格式當鍵,改了下一輪會重複列);'
                         '標準格式寫在對照中間檔與結果裡,這裡列出還不是標準的欄</span>')
    parts.append("</section>")
    return "".join(parts)


def _render_layer(prev):
    def render_html(card: dict, ui_dir: Path) -> str:
        h = prev(card, ui_dir)
        sec = xsrc_card(card)
        if not sec:
            return h
        for key in ('<section id="db-inventory"', '<div class="wrap"><table>'):
            i = h.find(key)
            if i >= 0:
                return h[:i] + sec + h[i:]
        return h.replace("</body>", sec + "</body>")
    return render_html


_ACTIVATE_PRIOR = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0110 activate;這一輪:流程跑完 → 日期格式體檢 + 跨來源對照(⑦ ⑧;資料庫家同 db where)· 心跳略過警告的原始碼行 · 版號與落檔標 v0111。
    換上的東西只在這一輪(跑完全部換回原樣,前版自測驗的函式身分不變)。"""
    keep_tag = PRIOR.TAG
    PRIOR.TAG = TAG
    with _LOCK10:
        _POST.clear()
    saved = {k: _V0101[k] for k in ("run_flows", "overall", "_last_line")}
    keep_render = V0100.render_html
    prev_w = vars(_V0106).get("_WRITE_REPORT_V0100") if _V0106 is not None else None
    _V0101["run_flows"] = _run_flows_layer(saved["run_flows"])
    _V0101["overall"] = _overall_layer(saved["overall"])
    _V0101["_last_line"] = _last_line
    V0100.render_html = _render_layer(keep_render)
    if prev_w is not None:
        _V0106._WRITE_REPORT_V0100 = _stamp_layer(prev_w)
    try:
        return _ACTIVATE_PRIOR(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep_tag
        _V0101.update(saved)
        V0100.render_html = keep_render
        if prev_w is not None:
            _V0106._WRITE_REPORT_V0100 = prev_w


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------------------------------------------------------------- 自測
def make_fixture(root: Path) -> Path:
    """測試用資料庫家(工作站同名表 · 同欄位):交易所民國日期混 ISO · Yahoo 浮點雜訊 · 月營收兩來源(同一來源抓兩次取新)· 他系統表 · 整數日期欄。"""
    duckdb = _duck()
    (root / "mega").mkdir(parents=True, exist_ok=True)
    (root / "tw_index").mkdir(parents=True, exist_ok=True)
    c = duckdb.connect(str(root / "mega" / "vdf_tw_market.duckdb"))
    c.execute("CREATE TABLE tw_trading_daily(date VARCHAR, code VARCHAR, market VARCHAR, volume DOUBLE, close DOUBLE)")
    c.execute("INSERT INTO tw_trading_daily VALUES ('1150824','2330','TWSE',1,1045.0),('2026-08-25','2330','TWSE',1,1050.0),"
              "('1150824','2317','TWSE',1,200.0),('1150824','5347','TPEX',1,30.35),('1150824','0050','TWSE',1,190.0),('1150701','2330','TWSE',1,900.0)")
    c.execute("CREATE TABLE tw_daily_prices(date DATE, ticker VARCHAR, close DOUBLE, adj_close DOUBLE)")
    c.execute("INSERT INTO tw_daily_prices VALUES ('2026-08-24','2330.TW',1044.9999389648438,1.0),('2026-08-25','2330.TW',1050.0,1.0),"
              "('2026-08-24','2317.TW',201.0,1.0),('2026-08-24','5347.TWO',30.35,1.0)")
    c.execute("CREATE TABLE tw_monthly_revenue(code VARCHAR, ym VARCHAR, revenue BIGINT, source VARCHAR, fetched_at TIMESTAMP)")
    c.execute("INSERT INTO tw_monthly_revenue VALUES ('2330','202607',100,'MOPS_OFFICIAL','2026-08-10 09:00'),('2330','202607',100,'CNYES','2026-08-10 09:00'),"
              "('2317','202607',500,'MOPS_OFFICIAL','2026-08-10 09:00'),('2317','202607',400,'CNYES','2026-08-09 09:00'),"
              "('2317','202607',500,'CNYES','2026-08-11 09:00'),('6488','202607',77,'MOPS_OFFICIAL','2026-08-10 09:00')")
    c.execute("CREATE TABLE vrn_report_x(report_date VARCHAR, v DOUBLE)")
    c.execute("INSERT INTO vrn_report_x VALUES ('亂寫', 1)")
    c.close()
    c = duckdb.connect(str(root / "tw_index" / "VDF_TWIndex_Daily.duckdb"))
    c.execute("CREATE TABLE twii(trade_date INTEGER, close DOUBLE)")
    c.execute("INSERT INTO twii VALUES (20260824, 23000.5), (20260825, 23100.0)")
    c.close()
    return root


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note != "" else ""), flush=True)
    print(f"=== {TAG} · 薄尾自測(擷取後日期格式體檢 + 跨來源對照 + 心跳略過警告原始碼行;沙盒 · 零網路)===", flush=True)
    cases = [("2024-10-01", "2024-10-01"), ("20241001", "2024-10-01"), ("1150824", "2026-08-24"), ("113/10/01", "2024-10-01"),
             ("114年09月12日", "2025-09-12"), ("2024/9/5", "2024-09-05"), ("2024-10-01 13:30:00", "2024-10-01"), ("Oct 1, 2024", "2024-10-01"),
             ("202410", "2024-10"), ("11507", "2026-07"), ("113/10", "2024-10"), ("2024Q3", "2024-09"), ("113年第3季", "2024-09"),
             ("2024", "2024"), ("FY2024", "2024"), ("113年度", "2024"), (datetime(2024, 10, 1, 9, 30), "2024-10-01"),
             ("2024-02-30", None), ("1151399", None), ("abc", None), ("1,234", None), (12.5, None)]
    got = [(v, iso_date(v)[0], w) for v, w in cases]
    chk("Ⓐ 日期一律 YYYY / YYYY-MM / YYYY-MM-DD:西元 · 8 碼 · 民國 7 碼(交易所)· 民國斜線 · 中文年月日 · 帶時刻 · 英文月份 · YYYYMM · 民國 5 碼 · "
        "季 → 季末月 · 年度;不存在的日期 / 非日期 → 不轉", all(g == w for _v, g, w in got), [x for x in got if x[1] != x[2]] or f"{len(cases)} 種")
    c1 = date_column("trade_date", [20241001, 20241002, None])
    chk("Ⓑ 整欄判斷:欄名像日期的整數欄才當日期(成交量 20241001 不轉)· 民國年月欄 → YYYY-MM · a/b/YYYY 整欄推讀法",
        date_column("volume", [20241001, 20241002]) is None and c1 and c1["values"] == ["2024-10-01", "2024-10-02", None]
        and date_column("年月", ["113/09", "113/10"])["values"] == ["2024-09", "2024-10"]
        and date_column("x", ["01/02/2024", "13/02/2024"])["values"] == ["2024-02-01", "2024-02-13"])
    r = cross_check([{"dataset": "d", "key": "2330", "date": "2026-08-24", "field": "close", "value": v, "source": s, "dec": 2}
                     for s, v in (("TWSE", 1045.0), ("YAHOO", 1044.9999389648438), ("X", 1050.0))]
                    + [{"dataset": "d", "key": "2317", "date": "2026-08-24", "field": "close", "value": v, "source": s, "dec": 2}
                       for s, v in (("TWSE", 10.3), ("YAHOO", 10.35))]
                    + [{"dataset": "d", "key": "0050", "date": "2026-08-24", "field": "close", "value": 190, "source": "TWSE", "dec": 2}])
    v = next(i for i in r["items"] if i["key"] == "2330")
    chk("Ⓒ 對照規則:兩個以上來源相同 = 成功(第三個不同記離群)· 沒有任兩個相同 = 衝突(10.30 ≠ 10.35)· 只有一個來源 = 單一 · 浮點雜訊 1044.99994 = 1045.00",
        r["counts"] == {"VERIFIED": 1, "CONFLICT": 1, "SINGLE": 1} and v["agree"] == ["TWSE", "YAHOO"] and v["outliers"] == ["X"]
        and next(i for i in r["items"] if i["key"] == "0050")["agree"] == []
        and same("1,045.00", 1045) and not same(100, "100.4") and same("ＡＢＣ", "abc"), r["counts"])
    with tempfile.TemporaryDirectory(prefix="activatevdf110_") as td:
        lg = Path(td) / "step.log"
        lg.write_text("[步] 第 2 段 抓 2330\nC:\\x\\VDF\\VDF_SystemManager_v0155.py:6: SyntaxWarning: invalid escape sequence '\\o'\n"
                      "  工作站 ActivateVDF 真跑:db_check RED。容器同一支 db check 實看(VDF\\output_hub)\n", encoding="utf-8")
        a = _last_line(lg)
        lg.write_text("[步] 第 2 段\n  [進行中] 縮排的真進度行\n", encoding="utf-8")
        b = _last_line(lg)
    chk("Ⓓ 心跳最後一行:略過 SyntaxWarning 與它下一行被印出來的原始碼(工作站每步都顯示同一句舊說明);一般縮排的進度行照顯示",
        a == "[步] 第 2 段 抓 2330" and b == "[進行中] 縮排的真進度行", (a, b))
    have = _duck() is not None
    if not have:
        chk("Ⓔ duckdb 不在本境 → 資料庫段不驗(不代裝);擷取後那一步照實寫「沒有 duckdb」", "沒有 duckdb" in post_fetch(
            type("O", (), {"db_home": None, "fetch_home": None})(), {"temp_run": tempfile.gettempdir()})["xsrc"]["note"])
    else:
        with tempfile.TemporaryDirectory(prefix="activatevdf110_db_") as td:
            t = Path(td)
            home = make_fixture(t / "output_hub")
            opt = type("O", (), {"db_home": str(home), "fetch_home": None})()
            keep_days = os.environ.get("VIA_XSRC_DAYS")
            os.environ["VIA_XSRC_DAYS"] = "2"              # 最近 2 個交易日:2330 的 07-01(只有交易所有)要被窗口排除
            try:
                post = post_fetch(opt, {"temp_run": str(t / "run")})
            finally:
                if keep_days is None:
                    os.environ.pop("VIA_XSRC_DAYS", None)
                else:
                    os.environ["VIA_XSRC_DAYS"] = keep_days
            xs, df = post["xsrc"], post["datefmt"]
            ds = xs["datasets"]
            tw, rv = ds.get("tw_daily_close", {}), ds.get("tw_monthly_revenue", {})
            files = [Path(f).name for f in xs["temp"]["files"]]
            yh = (t / "run" / "xsrc" / "tw_daily_close" / "tw_daily_close__YAHOO.csv")
            yrows = list(csv.DictReader(open(yh, encoding="utf-8-sig"))) if yh.is_file() else []
            chk("Ⓔ 跨來源對照(測試庫 · 最近 2 個交易日):TW 日收盤 交易所 × Yahoo → 成功 3(民國 1150824 與 ISO 同一天對得上)· 衝突 1(2317 200 ≠ 201)· 單一 1(0050)· 窗口外的 07-01 不列;"
                "月營收 MOPS × CNYES → 成功 2(同來源抓兩次取最新)· 單一 1;他系統表不讀",
                (tw.get("VERIFIED"), tw.get("CONFLICT"), tw.get("SINGLE")) == (3, 1, 1) and (rv.get("VERIFIED"), rv.get("CONFLICT"), rv.get("SINGLE")) == (2, 0, 1)
                and xs["lamp"] == "YELLOW" and tw.get("sources") == ["TPEX", "TWSE", "YAHOO"]
                and not any(i.get("date") == "2026-07-01" for i in xs["conflicts_top"]) and "2026-08-24 → 2026-08-25" in " ".join(xs["notes"]),
                {k: (d["VERIFIED"], d["CONFLICT"], d["SINGLE"]) for k, d in ds.items()})
            chk("Ⓕ 中間檔(本輪 temp/xsrc):每個資料集每個來源一檔(source 欄標註來源)+ 對照結果;日期欄一律標準格式、原始寫法另欄留",
                {"tw_daily_close__TWSE.csv", "tw_daily_close__TPEX.csv", "tw_daily_close__YAHOO.csv", "tw_daily_close__對照結果.csv",
                 "tw_monthly_revenue__MOPS_OFFICIAL.csv", "tw_monthly_revenue__CNYES.csv", "tw_monthly_revenue__對照結果.csv"} <= set(files)
                and yrows and all(r_["source"] == "YAHOO" and _STD.match(r_["date"]) for r_ in yrows)
                and all(_STD.match(r_["date"]) for f in xs["temp"]["files"] for r_ in csv.DictReader(open(f, encoding="utf-8-sig"))), files)
            bad = {(c["table"], c["column"]): c for c in df["items"] if c.get("standard") is False}
            std = {(c["table"], c["column"]) for c in df["items"] if c.get("standard")}
            chk("Ⓖ 日期格式體檢:交易所 date 民國 7 碼混 ISO(標混用)· 月營收 ym YYYYMM · 指數 trade_date 整數 YYYYMMDD → 不標準;DATE 型別 = 標準;"
                "fetched_at(紀錄時間)與他系統表(vrn_)不列",
                ("tw_trading_daily", "date") in bad and bad[("tw_trading_daily", "date")]["mixed"] and ("tw_monthly_revenue", "ym") in bad
                and ("twii", "trade_date") in bad and ("tw_daily_prices", "date") in std
                and not any(k[1] == "fetched_at" or k[0].startswith("vrn_") for k in list(bad) + list(std)) and df["lamp"] == "YELLOW",
                sorted("%s.%s" % k for k in bad))
            page = xsrc_card({"xsrc": dict(xs, conflicts_top=[dict(xs["conflicts_top"][0], key="<b>")]) if xs["conflicts_top"] else xs, "datefmt": df})
            chk("Ⓗ 總覽頁卡:對照計數 · 每資料集一列 · 衝突明細(跳脫)· 中間檔位置 · 日期不標準的欄;沒有結果 → 不出卡",
                'id="xsrc"' in page and "&lt;b&gt;" in page and "<b>2330" not in page and "tw_trading_daily" in page and xsrc_card({}) == "")
    saved = {k: _V0101[k] for k in ("run_flows", "overall", "_last_line")}
    keep_r, keep_w = V0100.render_html, (vars(_V0106).get("_WRITE_REPORT_V0100") if _V0106 is not None else None)
    lay = _overall_layer(lambda lists, flows: lists)
    with _LOCK10:
        _POST.clear()
        _POST["xsrc"] = {"lamp": "YELLOW"}
    l1, l2 = lay("GREEN", []), lay("RED", [])
    with _LOCK10:
        _POST["xsrc"] = {"lamp": "GREEN"}
    l3 = lay("GREEN", [])
    with _LOCK10:
        _POST.clear()
    seen = []
    _stamp_layer(lambda c, u=None: seen.append(dict(c)) or c)({"lamp": "GREEN", "schema": "VDF_ActivateVDF_v0110"})
    chk("Ⓘ 總燈:綠 + 對照有衝突 → 黃(不擋、不紅)· 紅照紅 · 沒衝突照綠;落檔最內層標 v0111;本輪換上的函式不在一輪裡時都是原樣(前版自測驗的身分不變)",
        (l1, l2, l3) == ("YELLOW", "RED", "GREEN") and seen and seen[0]["schema"] == "VDF_ActivateVDF_v0111" and seen[0]["tag"] == TAG
        and V0100.render_html is keep_r and V0100.write_report is PRIOR.write_report and saved["_last_line"] is not _last_line
        and (keep_w is None or vars(_V0106).get("_WRITE_REPORT_V0100") is keep_w))
    o0 = type("O", (), {"db_home": "repo/output_hub", "fetch_home": None})()
    o1 = _with_home(o0, [{"flow": "fetch"}, {"flow": "db", "db_home": "C:/via_database/vdf_database"}])
    chk("Ⓣ 資料庫家 = 資料庫流程 db where 選的(流程結果 db_home)· 沒選 / 同一個 → 照原本 · 原 opt 不改",
        o1.db_home == "C:/via_database/vdf_database" and o0.db_home == "repo/output_hub" and _with_home(o0, [{"flow": "db"}]) is o0
        and _with_home(o0, [{"db_home": "repo/output_hub"}]) is o0)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("Ⓙ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫;資料庫只唯讀開(read_only=True · 沒有寫入語句)",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and "def _via_net" in src
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VCGC", "via_duck_temp"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src)
        and "read_only=True" in src and not re.search(r"\b(INSERT\s+INTO|UPDATE\s+\S+\s+SET|DELETE\s+FROM|ALTER\s+TABLE|DROP\s+TABLE|CREATE\s+TABLE)\b",
                                                       src.split("def make_fixture", 1)[0]))
    n_ok = sum(ok)
    print(f"  [計] {TAG} 本版 {n_ok}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    if not all(ok):
        return 1
    rc1 = PRIOR.selftest()
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0102 / v0107 … v0110)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())

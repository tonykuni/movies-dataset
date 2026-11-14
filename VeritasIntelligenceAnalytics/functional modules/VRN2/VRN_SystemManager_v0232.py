#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0232 — 薄尾(輸出值驗證 + U/I 備援指令接加速器):① 年度財報數據冊逐值驗證:第二讀取器 pypdfium2 字元框 · 數值須在該頁、同列有科目、落在期間表頭那一欄(並排表各自對欄)· 一格多值 / 科目混進數值欄 / 非數據列 / 錯欄 → 不進主冊 · 寫 output/VRN2_Rejected_latest(帶理由 · 不消失)② 基本資料冊逐欄原文回查(pdfplumber + pypdfium2 聯集)· TEL 寫原文號碼(兩條讀法都讀到才輸出;v0231 誤寫成比對說明「2/2 一致」)· Email 只收原文詞界內的帳號(頁尾頁碼「- 1-」不再接到帳號前)· 分析師優先取 Email 前緊鄰的中文姓名 · 推算值標推算 ③ 完成判定加「輸出值驗證」一項(黃提醒 · 主冊只含驗證過的值)④ U/I 左側面板:按下顯示送出狀態 · 還原封存先確認 · 「這次不上船」同步到備援指令 · 備援指令第一步 CPU 閒時升「高於標準」+ 接 PS 加速器 VIA_PS_Accel_Module + 用啟動器實際路徑 · 剪貼簿失敗改選取 / 對話框 · 記住上次分頁。
  零替換:前版函式一個都不改;vrn2 / 成功登記用 v0231 同一段程式碼重新綁定到本版名稱空間(才會用到本版的輸出冊 / 面板 / 完成判定)· 其餘動詞照前版鏈。
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

import csv
import html
import importlib.util
import json
import os
import re
import sys
import types
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0232"
DISPLAY_NAME = "VRN-2 SystemManager"


def _vnum_v0232(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0232(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0232(p) < _vnum_v0232(__file__)), key=_vnum_v0232)
PRIOR = _load_v0232(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


# ===== ① 第二讀取器:pypdfium2 字元框 =====
_XV_NIL = re.compile(r"(?i)^(?:[-–—]+|n\.?a\.?|n/a|nm|n\.m\.|nil|neg\.?|ns|net\s*cash|淨現金)$")
_XV_PER = re.compile(r"^(?:FY)?\d{2,4}[AEFP]?$|^\d{1,2}/\d{2}[AEFPe]?$|^[A-Z][a-z]{2}-\d{2}[AEFP]$|^(?:19|20)\d{2}\([AEFP]\)$|^[1-4]Q\d{2}[AEFP]?$", re.I)


def _xv_nfk(t: str) -> str:
    return unicodedata.normalize("NFKC", t or "")


def _xv_sq(t: str) -> str:
    return re.sub(r"\s+", "", _xv_nfk(t)).lower()


def _xv_lines(pdf: Path, pno: int, cache: dict) -> list:
    """一頁 → [(y, [(x0, x1, 字詞)])](由上而下)· 字元框用字型高度(loose)· 同列 = 垂直中心差 < 0.5 字高 · 字距 ≤ 0.25 字高接成一詞。讀不到 → []。"""
    key = (str(pdf), pno)
    if key in cache:
        return cache[key]
    out = []
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(pdf))
        if 1 <= pno <= len(doc):
            tp = doc[pno - 1].get_textpage()
            rows = []
            for i in range(tp.count_chars()):
                ch = tp.get_text_range(i, 1)
                if ch in ("\r", "\n"):
                    continue
                l, b, r, t = tp.get_charbox(i, loose=True)
                if r <= l:
                    continue
                yc, h = (b + t) / 2, max(t - b, 1.0)
                row = next((rw for rw in rows if abs(rw[0] - yc) < 0.5 * max(h, rw[1])), None)
                if row is None:
                    row = [yc, h, []]
                    rows.append(row)
                row[2].append((l, r, ch, h))
            for yc, h, cs in rows:
                cs.sort(key=lambda x: x[0])
                toks, cur = [], None
                for l, r, ch, hh in cs:
                    if ch.isspace():
                        cur = None
                        continue
                    if cur is not None and l - cur[1] <= 0.25 * hh:
                        cur[1], cur[2] = r, cur[2] + ch
                    else:
                        cur = [l, r, ch]
                        toks.append(cur)
                out.append((yc, [(a, b_, _xv_nfk(s)) for a, b_, s in toks]))
            out.sort(key=lambda x: -x[0])
        doc.close()
    except Exception:  # noqa: BLE001
        out = []
    cache[key] = out
    return out


def _xv_cell(lines: list, item: str, per: str, val: str) -> tuple:
    """一筆年度數據對原文:ALIGNED 數值在科目那一列且落在期間表頭那一欄 · MISALIGNED 在該列但在別欄(並排表錯位)·
    UNLOCATED 該頁有這個值但科目列 / 表頭沒定位 · ABSENT 該頁沒有這個值。並排表各自有表頭 → 每個同名表頭都試,取最近。"""
    sv = _xv_sq(val)
    ptxt = "\n".join(" ".join(t for _, _, t in tk) for _, tk in lines)
    if not lines:
        return "UNLOCATED", "第二讀取器讀不到本頁"
    if sv not in _xv_sq(ptxt) and sv.replace(",", "") not in _xv_sq(ptxt):
        return "ABSENT", "該頁原文沒有 %s" % val
    si = _xv_sq(item)
    keys = [k for k in {si[:14], si[-12:] if len(si) > 18 else ""} if k]
    best = None
    for k, (y, tk) in enumerate(lines):
        lt = _xv_sq("".join(t for _, _, t in tk))
        if not any(key in lt for key in keys):
            continue
        row = [tt for kk in (k, k + 1) if kk < len(lines) and abs(lines[kk][0] - y) < 14 for tt in lines[kk][1]]
        hits = [(a + b) / 2 for a, b, t in row if _xv_sq(t) in (sv, sv.replace(",", ""))]
        if not hits:
            continue
        for yy, htk in lines:
            if not (y - 1 < yy < y + 520):
                continue
            for a, b, t in htk:
                if t != per:
                    continue
                hx = (a + b) / 2
                colw = min([abs((aa + bb) / 2 - hx) for aa, bb, tt in htk if tt != per and _XV_PER.match(tt)] + [60])
                for vx in hits:
                    dx = abs(vx - hx)
                    if best is None or dx < best[0]:
                        best = (dx, colw, hx, vx, b - a)
    if not best:
        return "UNLOCATED", "該頁有值 · 科目列或期間表頭沒定位"
    dx, colw, hx, vx, hw = best
    if dx <= max(0.55 * colw, 0.9 * hw, 12):
        return "ALIGNED", "對欄 dx %.1f" % dx
    return "MISALIGNED", "數值 x %.0f 不在 %s 欄(x %.0f)· 並排表錯位" % (vx, per, hx)


def _xv_item(lines: list, item: str) -> str:
    """科目照原文:整個科目在本頁原文找不到(前面黏了浮水印 / 章節名 · 「,凱基 應收帳款周轉天數」「Ratios Adj. tax rate」)→ 由前往後去掉雜字,
    剩下的在某一列開頭找得到才換;科目本身找得到(含並排表右半)一律不動。"""
    if not lines:
        return item
    rows = [_xv_sq("".join(t for _, _, t in tk)) for _, tk in lines]
    page = "".join(rows)
    if _xv_sq(item) in page:
        return item
    toks = item.split()
    for i in range(len(toks)):
        c = re.sub(r"^[\s,，.;:;、·]+", "", " ".join(toks[i:]))
        sc = _xv_sq(c)
        if len(sc) >= 4 and any(r_.startswith(sc) for r_ in rows):
            return c
    return item


def _xv_raw(pdf: Path, pages=(1, 2, 3)) -> str:
    """原文(兩個讀取器聯集:pdfplumber + pypdfium2)· 去字母間字型雜訊 %(To%mmy → Tommy)· 只做安全正規化。"""
    t = []
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf)) as d:
            t += [(d.pages[p - 1].extract_text() or "") for p in pages if p <= len(d.pages)]
    except Exception:  # noqa: BLE001
        pass
    t += list(_acc_pdfium_text(Path(pdf), list(pages)).values())
    t = _xv_nfk("\n".join(t)).replace("\r\n", "\n").replace("\r", "\n")                  # pypdfium2 換行是 \r\n
    return re.sub(r"(?<=[A-Za-z一-鿿])%(?=[A-Za-z一-鿿])", "", t)


def _bi_norm2(t: str) -> str:
    """v0232 = _bi_norm,但跨行接回只接「字母開頭的片段-⏎」(daiwacm-⏎cathay)· 頁尾頁碼「- 1-⏎10863@」不再接到帳號前。"""
    t = re.sub(r"(?<=[A-Za-z])%(?=[a-z])", "", t or "")
    t = re.sub(r"([A-Za-z][\w.]*)-\s*\n\s*(?=[\w.])", r"\1-", t)
    t = re.sub(r"@\s*\n\s*", "@", t)
    t = re.sub(r"(?<=[\w])\.\s*\n\s*(?=(?:com|tw|hk|co|jp|net)\b)", ".", t)
    t = re.sub(r"(?i)exclusive use of\s+\S+@\S+", " ", t)
    return re.sub(r"\b([A-Z][a-z]?) ([a-z]{2,}[\w.]*@)", r"\1\2", t)


def _xv_num_in(v: str, text: str) -> bool:
    v = _xv_nfk(v).strip().lstrip("+")
    pat = r"(?<![\d.,])" + re.escape(v) + r"(?![\d])"
    return bool(re.search(pat, text) or re.search(pat, re.sub(r"(?<=\d)\s+(?=[\d,.])", "", text)))


def _out_pdf(f: str, v2: Path) -> Path:
    for d in (v2 / "scope_in", Path(str((_resolve("input_dir") or (lambda: ""))() or "."))):
        if (d / f).exists():
            return d / f
    return v2 / "scope_in" / f


def _an_name(em_: str, raw: str, p1n: str) -> tuple:
    """分析師姓名(照原文印):原文 Email 前 ① 上一行只有 2~4 個中文字 ②「研究員 / 分析師 姓名」③ 同一行緊鄰在前(空白分開)· 再看首頁區塊的 v0231 規則
    (/ · CFA · 分析師 · 電話 · 換行)· 帳號拆字的英文名在原文 → 原文 · 都沒有 → 帳號推算(標推算)。回 (姓名, 狀態)。"""
    acct = em_.split("@")[0]
    bad = lambda x: x in _OUT_NOTNAME or re.search(r"研究|中心|產業|分析|投資|部門|團隊|報告|說明|設計|設備|封裝|法說|服務|市場|業務|系統|領域|信箱|電話|郵件|傳真|地址|網址|聯絡|日期|評等|目標|收盤", x)  # noqa: E731
    rn = raw.replace("\r\n", "\n").replace("\r", "\n")
    for mm in re.finditer(re.escape(acct), rn, re.I):
        ls = rn[:mm.start()].split("\n")
        cur, prev = ls[-1], ls[-3:-1]
        cands = []
        if prev and re.fullmatch(r"[ \t]*([一-鿿]{2,4})[ \t]*", prev[-1]):           # ① 上一行只有姓名
            cands.append(prev[-1].strip())
        for l_ in reversed(prev + [cur]):                                   # ②「研究員 / 分析師 姓名」
            m2 = re.search(r"(?:研究員|分析師)[ \t:：]*([一-鿿]{2,4})(?![一-鿿])", l_)
            if m2:
                cands.append(m2.group(1))
        m3 = re.search(r"(?:^|[^一-鿿])([一-鿿]{2,4})[ \t]+$", cur)      # ③ 同一行緊鄰在前(空白分開)
        if m3:
            cands.append(m3.group(1))
        cands = [x for x in cands if not bad(x)]
        if cands:
            return cands[0], "原文"
    k_ = p1n.lower().find(acct[-6:].lower())
    pre = p1n[max(0, k_ - 90):k_] if k_ >= 0 else ""
    cj = (re.findall(r"([\u4e00-\u9fff]{2,4})(?=\s*[/／])", pre) or re.findall(r"([\u4e00-\u9fff]{2,4})(?=\s*[,，]\s*(?:CPA|CFA|FRM|PhD|MBA|CMA))", pre)
          or re.findall(r"([\u4e00-\u9fff]{2,4})(?=\s*分析師|\s*研究員|\s*\+?886|\s*\n)", pre))
    cj = [x for x in cj if not bad(x)]
    if cj:
        return cj[-1], "原文"
    guess = " ".join(w.capitalize() for w in re.split(r"[._]", acct) if w.isalpha())
    return guess, ("原文" if guess and _xv_sq(guess) in _xv_sq(raw) else "推算(Email 帳號 · 原文未印此名)")


_XV_LAST = {}


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0232 三本輸出冊(範圍:個股報告)· 只輸出驗證過的值:
    基本資料逐欄原文回查(兩個讀取器聯集)· TEL 寫原文號碼(兩條讀法都讀到)· Email 只收原文詞界內的帳號 · 分析師取 Email 前緊鄰的中文姓名 · 推算值標推算;
    年度數據逐值第二讀取器對欄 · 一格多值 / 科目混進數值欄 / 非數據列 / 錯欄 → 剔除冊(帶理由 · 不消失)。"""
    byf = {r.get("file"): r for r in res}
    ac = {e.get("file"): e for e in acc or []}
    basic, fin, summ, gaps, rej = [], [], [], [], []
    xstat = Counter()
    cache = {}
    for s_ in st or []:
        f = s_.get("file")
        r, e = byf.get(f) or {}, ac.get(f) or {}
        if not s_.get("stock", True) or not r:
            continue
        pdf = _out_pdf(f, v2)
        raw = _xv_raw(pdf) if pdf.exists() else ""
        rawsq = _xv_sq(raw)
        tk = s_.get("ticker", "")
        p1 = _out_p1(r)
        yf = re.search(r"\b(%s)\.(TWO|TW)\b" % re.escape(tk), p1) if tk else None
        bb = re.search(r"\b(%s)\s+TT\b" % re.escape(tk), p1) if tk else None
        en = re.search(r"([A-Z][A-Za-z&.,'\- ]{2,48}?)\s*\(\s*%s\.TWO?" % re.escape(tk), p1) if tk else None
        zh = re.search(r"(?<!\d)%s[\s_\-]*([一-鿿][一-鿿]{0,8}(?:-KY)?)" % re.escape(tk), f) if tk else None
        zh = zh or (re.search(r"([一-鿿]{2,8}(?:-KY)?)[\s_\(（]*%s" % re.escape(tk), f) if tk else None)
        rt, rts = _out_rating(r)
        bi = e.get("basic") or {}
        mt = e.get("metrics") or {}
        zs = [z for pg in r.get("pages") or [] if pg.get("pno") == 1 for z in pg.get("zones", [])]
        ta = "\n".join([x.get("text", "") for z in zs for x in (z.get("records") or []) if isinstance(x, dict)] + [" ".join(c for c in row if c) for z in zs for row in (z.get("rows") or [])])
        tb = _acc_pdfium_text(pdf, [1]).get(1, "") if pdf.exists() else ""
        raw_em = {x.lower().rstrip(".") for x in _BI_EMAIL.findall(_bi_norm2(raw))}          # 原文詞界內的帳號
        em_a = sorted({x.lower().rstrip(".") for x in _BI_EMAIL.findall(_bi_norm2(ta))})
        emails = [x for x in em_a if x in raw_em] or sorted(x for x in {y.lower().rstrip(".") for y in _BI_EMAIL.findall(_bi_norm2(tb))} if x in raw_em)
        emails = [x for x in emails if not any(y != x and y.endswith(x) and len(y.split("@")[0]) > len(x.split("@")[0]) for y in emails)]   # 截斷的(mmy.lai)讓完整的(tommy.lai)
        ta2 = _bi_norm2(ta)
        tel_a = [((("(" if m.start() and ta2[m.start() - 1] == "(" else "") + m.group(0)).strip(), re.sub(r"\D", "", m.group(0))[-8:])
                 for m in _BI_TEL.finditer(ta2) if len(re.sub(r"\D", "", m.group(0))) >= 8]   # 照原文:開頭括號也留(「(886-2) 2725-9868」)
        tel_b = {re.sub(r"\D", "", x)[-8:] for x in _BI_TEL.findall(_bi_norm2(tb)) if len(re.sub(r"\D", "", x)) >= 8}
        tels = list(dict.fromkeys(s for s, d in tel_a if d in tel_b))
        names_, nst = [], []
        p1n = _bi_norm2(p1)
        for em_ in emails:                                                 # 分析師:原文中 Email 前的中文姓名優先 · 再找原文英文名 · 最後才用帳號推算(標推算)
            nm_, ns_ = _an_name(em_, raw, p1n)
            names_.append(nm_)
            nst.append(ns_)
        up_, ups_ = mt.get("upside") or "", "原文"
        try:
            if not up_ and mt.get("target") and mt.get("current"):
                up_ = "%.1f" % ((float(str(mt["target"]).replace(",", "")) / float(str(mt["current"]).replace(",", "")) - 1) * 100)
                ups_ = "計算(目標價 ÷ 現價 − 1)"
        except (ValueError, ZeroDivisionError):
            pass
        row = {"REPORT_DATE": s_.get("date", ""), "FILENAME": f, "TICKER": tk,
               "YFINANCE_TICKER": ("%s.%s" % (yf.group(1), yf.group(2))) if yf else "", "BLOOMBERG_TICKER": ("%s TT" % tk) if tk else "",
               "NAME": zh.group(1) if zh else "", "ENGLISH_NAME": en.group(1).strip(" ,:-") if en else "", "BROKER": s_.get("broker", ""),
               "ANALYST": "、".join(dict.fromkeys(names_)), "EMAIL": "、".join(emails),
               "TEL": "、".join(tels), "TITLE": (e.get("summary") or {}).get("title") or "", "RATING": rt,
               "TARGET_PRICE": mt.get("target") or "", "CURRENT_PRICE_REPORT": mt.get("current") or "", "UPSIDE_PCT": up_,
               "ADJ_CLOSE": "", "ADJ_CLOSE_BEFORE_REPORT": "",
               "_STATUS": {"BLOOMBERG_TICKER": "VERIFIED" if bb else "推算(代號 + TT)", "YFINANCE_TICKER": "VERIFIED" if yf else "待 VDF 上市櫃清單(.TW / .TWO)",
                           "EMAIL": (bi.get("email") or ["—"])[0], "TEL": "VERIFIED(兩條讀法)" if tels else "%s · 不輸出(兩條讀法沒有同時讀到)" % ((bi.get("tel") or ["MISSING"])[0]),
                           "BROKER": (bi.get("broker") or ["—"])[0], "ANALYST": " / ".join(dict.fromkeys(nst)) or "—",
                           "RATING": rts or "首頁未印", "UPSIDE_PCT": ups_ if up_ else "缺目標價或現價", "NAME": "檔名" if zh else "待 VDF 上市櫃清單(不衝突即可取用)",
                           "ADJ_CLOSE": "待 VDF 股價庫(不衝突即可取用)"}}
        chk = {"TICKER": lambda v: v in f or v in raw, "YFINANCE_TICKER": lambda v: _xv_sq(v) in rawsq, "ENGLISH_NAME": lambda v: _xv_sq(v) in rawsq,
               "NAME": lambda v: v in f or v in raw, "RATING": lambda v: _xv_sq(v) in rawsq, "TITLE": lambda v: _xv_sq(v)[:40] in rawsq,
               "TARGET_PRICE": lambda v: _xv_num_in(v, raw), "CURRENT_PRICE_REPORT": lambda v: _xv_num_in(v, raw),
               "EMAIL": lambda v: all(x in raw_em for x in v.split("、")), "TEL": lambda v: all(re.sub(r"\D", "", x)[-8:] in re.sub(r"\D", "", raw) for x in v.split("、")),
               "ANALYST": lambda v: all(_xv_sq(x) in rawsq or st_.startswith("推算") for x, st_ in zip(v.split("、"), nst or ["推算"] * 9)),
               "UPSIDE_PCT": lambda v: (ups_.startswith("計算") or _xv_num_in(v, raw))}
        for k_, fn_ in chk.items():
            v_ = str(row.get(k_) or "")
            if not v_:
                continue
            xstat["基本資料欄"] += 1
            if raw and not fn_(v_):
                rej.append({"BOOK": "BasicInfo", "FILENAME": f, "FIELD": k_, "VALUE": v_, "REASON": "原文找不到此值 · 不輸出"})
                row[k_] = ""
                row["_STATUS"][k_] = "原文找不到 · 不輸出(見剔除冊)"
                xstat["基本資料剔除"] += 1
        basic.append(row)
        nrow = 0
        for pg in r.get("pages") or []:
            pno = pg.get("pno")
            for z in pg.get("zones") or []:
                rows = z.get("rows") or []
                if z.get("minor") != "TB" or not rows:
                    continue                                              # v0229 改用表頭判斷(與個股四項同口徑)
                hdr = next(((i, rw) for i, rw in enumerate(rows[:4]) if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2), None)
                if not hdr:
                    continue
                hi, hrow = hdr
                for rw in rows[hi + 1:]:
                    item = ((rw[0] if rw else "") or "").strip()
                    if not re.search(r"[A-Za-z一-鿿]{2,}", item) or re.fullmatch(r"[\d\s,.%()\-+]+", item) or re.search(r"\d{4}\.TWO?\(", item):
                        continue                                          # v0229 圖表座標 / 數字當科目 / 股價圖軸不收
                    cells = [(j, ((hrow[j] if j < len(hrow) else "") or "").strip(), (c or "").strip()) for j, c in enumerate(rw[1:], 1)]
                    cells = [(j, per, c) for j, per, c in cells if c and _SK_ANNUAL.match(per)]
                    if not cells:
                        continue
                    base = {"REPORT_DATE": row["REPORT_DATE"], "FILENAME": f, "TICKER": tk, "BROKER": row["BROKER"], "PAGE": pno, "TABLE": z.get("id"), "ITEM": item}
                    if not any(re.search(r"\d", c) or _XV_NIL.match(c) for _, _, c in cells):
                        for _, per, c in cells:
                            rej.append(dict(base, BOOK="FinancialData", PERIOD=per, VALUE=c, REASON="非數據列(表頭 / 子表頭 / 分隔線)"))
                        xstat["年度剔除"] += len(cells)
                        continue
                    lines = _xv_lines(pdf, int(pno or 1), cache) if pdf.exists() else []
                    item_c = _xv_item(lines, item)
                    if item_c != item:
                        base = dict(base, ITEM=item_c, ITEM_RAW=item)              # 前綴雜字(浮水印 / 章節名)去掉 · 原字串留 ITEM_RAW
                        xstat["科目清理"] += 1
                    for j, per, c in cells:
                        xstat["年度數據"] += 1
                        ntok = [t for t in c.split() if re.search(r"\d", t) or _XV_NIL.match(t)]
                        why = ""
                        if len(ntok) >= 2:
                            why = "一格多值(%d 個值 · 子欄位未拆)" % len(ntok)
                        elif not re.search(r"\d", c) and not _XV_NIL.match(c):
                            why = "科目 / 文字混進數值欄"
                        if not why and re.search(r"\d", c):
                            vd, note = _xv_cell(lines, item_c, per, c)
                            if vd in ("MISALIGNED", "ABSENT"):
                                why = note
                            else:
                                xstat["對欄" if vd == "ALIGNED" else "未定位"] += 1
                        elif not why:
                            vd, note = "NIL", "空值記號(照原文)"
                            xstat["空值記號"] += 1
                        if why:
                            rej.append(dict(base, BOOK="FinancialData", PERIOD=per, VALUE=c, REASON=why))
                            xstat["年度剔除"] += 1
                            continue
                        fin.append(dict(base, PERIOD=per, VALUE=c, VERIFY={"ALIGNED": "對欄(pypdfium2)", "UNLOCATED": "原文該頁有值 · 欄位未定位", "NIL": "空值記號(照原文)"}.get(vd, vd)))
                        nrow += 1
        sm = e.get("summary") or {}
        pts = sm.get("points") or []
        summ.append({"REPORT_DATE": row["REPORT_DATE"], "FILENAME": f, "TICKER": tk, "BROKER": row["BROKER"], "TITLE": sm.get("title") or "",
                     **{"POINT_%d" % (i + 1): ((pts[i].get("text") or "") if i < len(pts) else "") for i in range(4)},
                     "POINTS_OK": sum(1 for p in pts if p.get("text"))})
        miss = [k for k in ("REPORT_DATE", "TICKER", "BROKER", "TITLE") if not row[k]]
        quick = (s_.get("parts") or {}).get("年度財報", ("", ""))[0] == "GRAY"
        if not nrow and not quick:
            miss.append("年度數據")
        if summ[-1]["POINTS_OK"] < 4:
            miss.append("四重點 %d/4" % summ[-1]["POINTS_OK"])
        if miss:
            gaps.append("%s:%s" % (f[:28], "、".join(miss)))
    od = v2 / "output"
    od.mkdir(parents=True, exist_ok=True)
    made = []
    for name, rows_ in (("BasicInfo", basic), ("FinancialData", fin), ("Summary", summ), ("Rejected", rej)):
        (od / ("VRN2_%s_latest.json" % name)).write_text(json.dumps(rows_, ensure_ascii=False, indent=1), encoding="utf-8")
        flat = [{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in x.items()} for x in rows_]
        keys = list(dict.fromkeys(k for x in flat for k in x))
        with (od / ("VRN2_%s_latest.csv" % name)).open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys or ["EMPTY"])
            w.writeheader()
            w.writerows(flat)
        try:
            import pandas as pd  # noqa: WPS433
            pd.DataFrame(flat).to_parquet(od / ("VRN2_%s_latest.parquet" % name), index=False)
            made.append("%s(%d 列 · JSON / CSV / Parquet)" % (name, len(rows_)))
        except Exception:  # noqa: BLE001
            made.append("%s(%d 列 · JSON / CSV)" % (name, len(rows_)))
    rf = Counter(x["REASON"].split("(")[0].split(" ·")[0][:14] for x in rej if x["BOOK"] == "FinancialData")
    lamp = "GREEN" if not rej and not xstat["未定位"] else "YELLOW"
    _XV_LAST["item"] = ("輸出值驗證(第二讀取器逐值回查 · 年度數據對欄)", lamp,
                        "基本資料 欄 %d · 剔除 %d | 年度數據 輸出 %d(對欄 %d · 未定位 %d · 空值記號 %d)· 剔除 %d%s → output/VRN2_Rejected_latest(帶理由)" % (
                            xstat["基本資料欄"], xstat["基本資料剔除"], len(fin), xstat["對欄"], xstat["未定位"], xstat["空值記號"], xstat["年度剔除"],
                            ("(" + " · ".join("%s %d" % kv for kv in rf.most_common(4)) + ")") if rf else ""))
    _XV_LAST["rej"] = rej
    return basic, fin, summ, gaps, made


def _out_html(basic: list, fin: list, summ: list) -> str:
    """v0231 的三本冊頁 + 剔除冊(每筆帶理由)。"""
    rej = _XV_LAST.get("rej") or []
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % tuple(html.escape(str(x.get(k, ""))[:90]) for k in ("FILENAME", "BOOK", "FIELD" if x.get("BOOK") == "BasicInfo" else "ITEM", "PERIOD", "VALUE", "REASON")) for x in rej[:400])
    return PRIOR._out_html(basic, fin, summ) + ("<h2 style='margin-top:14px'>剔除冊(未通過輸出值驗證 · %d 筆 · 不進主冊)</h2><table><tr><th>檔案</th><th>冊</th><th>欄 / 科目</th><th>期間</th><th>值</th><th>理由</th></tr>%s</table>" % (len(rej), rows))


def completion(*a, **k) -> dict:
    """v0231 完成判定 + 「輸出值驗證」一項(黃提醒 · 主冊只含驗證過的值 · 剔除進剔除冊)。"""
    comp = _rebind(PRIOR.completion)(*a, **k)
    it = _XV_LAST.get("item")
    if it:
        comp["items"].append({"name": it[0], "lamp": it[1], "detail": it[2]})
        comp["red"] = sum(1 for x in comp["items"] if x["lamp"] == "RED")
        comp["yellow"] = sum(1 for x in comp["items"] if x["lamp"] == "YELLOW")
        comp["verdict"] = "未完成" if comp["red"] else "完成"
    return comp


def _completion_html(comp: dict) -> str:
    """v0231 完成判定面板 · 燈號欄不斷行(GREE / N → GREEN)。"""
    return re.sub(r"<tr><td( class='bl')?><i ", lambda m: "<tr><td%s style='white-space:nowrap'><i " % (m.group(1) or ""), PRIOR._completion_html(comp))


# ===== ④ U/I 操作面板 =====
def _ui_cmd(nopush: bool) -> str:
    """PS 備援指令:第一步 CPU 閒(<60%)時本視窗升「高於標準」(子行程繼承)+ GC · 接 PS 加速器(VIA_PS_Accel_Module · 找不到不影響)· 用啟動器實際路徑。"""
    try:
        cfg = json.loads((HERE / "VRN2_UIAction_Config.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        cfg = {}
    la = cfg.get("launcher") or "$env:USERPROFILE\\Downloads\\ActivateVRN-2.py"
    py = cfg.get("python") or ""
    root = str(HERE.parent.parent)
    q = lambda s: "'" + str(s).replace("'", "''") + "'"  # noqa: E731
    return ("& { try { $c = (Get-CimInstance Win32_Processor -ErrorAction Stop | Measure-Object LoadPercentage -Average).Average; if ($c -lt 60) { (Get-Process -Id $PID).PriorityClass = 'AboveNormal' } } catch { }; [GC]::Collect(); "
            "$m = Join-Path %s 'supportive modules\\VIA_PS_Accel_Module.ps1'; if (Test-Path -LiteralPath $m) { . $m }; "
            "$A = %s; $py = %s; if (-not $py -or -not (Test-Path -LiteralPath $py)) { $py = (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source }; "
            "%s& $py $A }" % (q(root), ('"%s"' % la) if la.startswith("$env:") else q(la), q(py) if py else "''",
                              "$env:VIA_VRN2_NO_PUSH = '1'; " if nopush else "Remove-Item Env:\\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue; "))


def _ui_panel_html(v2: Path) -> str:
    """v0232 U/I 左側操作面板(政策 L118)+ 右側分頁 · 動作走 vrn2://(不碰 via://)· 按下顯示送出狀態 · 還原封存先確認 ·
    備援「⧉ 複製執行指令」= 第一步提高 CPU 優先權 + PS 加速器 + 實際啟動器路徑 · 「這次不上船」同步到指令 · 剪貼簿失敗改選取 / 對話框 · 記住上次分頁。"""
    def uri(p):
        return p.as_uri() if p.exists() else ""
    links = [("📂 輸出冊", uri(v2 / "output")), ("🔍 切割檢視", uri(v2 / "p1view" / "P1VIEW_latest.html")), ("📁 個股範圍夾", uri(v2 / "scope_in")), ("🗂 備份夾", uri(v2 / "backup"))]
    b = "display:block;width:100%;box-sizing:border-box;margin:0 0 6px;padding:6px 8px;border:1px solid #d1d5db;border-radius:6px;background:#fff;color:#111;text-decoration:none;cursor:pointer;font:12px system-ui,'Microsoft JhengHei';text-align:left"
    acts = [("▶ 完整重跑", "run", "#16a34a"), ("▶ 重跑(不上船)", "run?nopush=1", ""), ("↻ 清快取後重跑", "run-clean", ""), ("↩ 還原封存舊版", "restore-archive", "")]
    h = ["<div id='vrn2panel' role='region' aria-label='VRN-2 操作' style='position:fixed;left:0;top:0;bottom:0;width:190px;overflow:auto;background:#f9fafb;border-right:1px solid #e5e7eb;padding:10px 8px;box-sizing:border-box;z-index:20'>",
         "<div style='font-weight:700;margin-bottom:8px'>VRN-2 操作</div>"]
    for lab, a, col in acts:
        st_ = b + (";background:%s;color:#fff;border-color:%s" % (col, col) if col else "")
        h.append("<a class='vact' data-a='%s' style=\"%s\" href='vrn2://%s'>%s</a>" % (a, st_, a, lab))
    h.append("<label style='display:block;margin:4px 0 6px;font-size:12px'><input type='checkbox' id='vnopush'> 這次不上船 GitHub</label>")
    h.append("<div id='vstat' role='status' aria-live='polite' style='font-size:11px;color:#1d4ed8;margin:0 0 8px;min-height:14px'></div>")
    h.append("<div style='font-weight:700;margin:8px 0 6px'>開啟</div>")
    for lab, u in links:
        if u:
            h.append("<a style=\"%s\" href='%s' target='_blank'>%s</a>" % (b, u, lab))
    h.append("<div style='font-weight:700;margin:8px 0 6px'>備援</div><button id='vcopy' type='button' style=\"%s\" data-c0=\"%s\" data-c1=\"%s\">⧉ 複製執行指令</button>" % (
        b, html.escape(_ui_cmd(False), quote=True), html.escape(_ui_cmd(True), quote=True)))
    h.append("<div style='color:#6b7280;font-size:11px;margin-top:8px'>按鈕走 vrn2:// 協定(啟動器自動註冊到目前使用者)· 第一次瀏覽器會問是否開啟 pythonw → 允許 · 沒反應請用「複製執行指令」貼到 PowerShell(指令第一步提高 CPU 優先權並接 PS 加速器)</div></div>")
    js = r"""<script>(function(){function $(i){return document.getElementById(i);}
function stat(t){var s=$('vstat');if(s){s.textContent=t;}}
function sync(){var np=$('vnopush');document.querySelectorAll('a.vact').forEach(function(a){var x=a.dataset.a;if(x.indexOf('run')===0){var u='vrn2://'+x;if(np&&np.checked&&u.indexOf('nopush')<0){u+=(u.indexOf('?')<0?'?':'&')+'nopush=1';}a.href=u;}});}
function copy(t,btn){function ok(){btn.textContent='✓ 已複製';stat('已複製執行指令 · 貼到 PowerShell 按 Enter');}
function fb(){try{var ta=document.createElement('textarea');ta.value=t;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.left='-9999px';document.body.appendChild(ta);ta.select();var r=document.execCommand('copy');document.body.removeChild(ta);if(r){ok();return;}}catch(e){}window.prompt('按 Ctrl+C 複製這行指令,再貼到 PowerShell:',t);stat('剪貼簿不可用 · 已用對話框顯示指令');}
try{if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(ok,fb);}else{fb();}}catch(e){fb();}}
function init(){var b=document.body;b.style.marginLeft='200px';var np=$('vnopush');if(np){np.addEventListener('change',sync);}sync();
document.querySelectorAll('a.vact').forEach(function(a){a.addEventListener('click',function(ev){if(a.dataset.a==='restore-archive'&&!window.confirm('還原 ⑩ 封存的舊版(依 ARCHIVE_MANIFEST 全部移回原位 · 原位已有同名檔則略過)?')){ev.preventDefault();stat('已取消還原');return;}
var d=new Date();stat('已送出 '+a.getAttribute('href')+' · '+d.toLocaleTimeString()+' · 若 5 秒內沒有新的主控台視窗:協定未註冊 → 按「⧉ 複製執行指令」');});});
var cb=$('vcopy');if(cb){cb.addEventListener('click',function(){copy((np&&np.checked)?cb.dataset.c1:cb.dataset.c0,cb);});}
var all=[].slice.call(document.querySelectorAll('h2,h3')).filter(function(h){return !h.closest('#vrn2panel');});if(all.length<2)return;var par=all[0].parentNode;var hs=all.filter(function(h){return h.parentNode===par;});if(hs.length<2)return;var hset=new Set(hs);
var bar=document.createElement('div');bar.id='vrn2tabs';bar.setAttribute('role','tablist');bar.style.cssText='position:sticky;top:0;z-index:15;background:#fff;border-bottom:1px solid #e5e7eb;padding:4px 0;margin:6px 0 8px;display:flex;flex-wrap:wrap;gap:4px';
hs[0].parentNode.insertBefore(bar,hs[0]);var pages=[];
function show(i){pages.forEach(function(p,j){p.style.display=j===i?'':'none';});[].forEach.call(bar.children,function(c,j){c.style.background=j===i?'#e0f2fe':'#fff';c.setAttribute('aria-selected',j===i?'true':'false');});try{localStorage.setItem('vrn2tab',String(i));}catch(e){}}
hs.forEach(function(h,i){var pg=document.createElement('div');pg.className='vtab';pg.setAttribute('role','tabpanel');h.parentNode.insertBefore(pg,h);var n=h;while(n&&!(n!==h&&hset.has(n))){var nx=n.nextSibling;pg.appendChild(n);n=nx;}pages.push(pg);
var t=document.createElement('button');t.type='button';t.setAttribute('role','tab');t.textContent=(h.textContent||'').split('(')[0].split('(')[0].slice(0,18);t.title=(h.textContent||'').slice(0,120);t.style.cssText='padding:3px 9px;border:1px solid #d1d5db;border-radius:12px;background:#fff;cursor:pointer;font:12px system-ui';
t.addEventListener('click',function(){show(i);});bar.appendChild(t);});
var k=0;try{k=parseInt(localStorage.getItem('vrn2tab')||'0',10)||0;}catch(e){}show(k<pages.length?k:0);}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init);}else{init();}
window.addEventListener('pageshow',sync);})();</script>"""
    return "".join(h) + js


vrn2 = _rebind(PRIOR.vrn2)                                                # v0231 同一段 vrn2 · 用到本版 _out_books / _out_html / _ui_panel_html / completion
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0232)


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
    t1 = _bi_norm2("年度EPS預估 - 1-\n10863@entrust.com.tw\nhelen.chien@daiwacm-\ncathay.com.tw To%mmy.Lai@kgi.com S haron.Shih@morganstanley.com")
    ems = sorted(x.lower() for x in _BI_EMAIL.findall(t1))
    chk("⓪ v0232 Email:頁尾頁碼不接到帳號前 → %s" % ems, ems == ["10863@entrust.com.tw", "helen.chien@daiwacm-cathay.com.tw", "sharon.shih@morganstanley.com", "tommy.lai@kgi.com"])
    chk("⓪ v0232 年度數據分類:一格多值 / 科目混入 / 空值記號 · %s" % [bool(_XV_NIL.match(x)) for x in ("Net cash", "--", "n.a.", "COGS", "____")],
        [bool(_XV_NIL.match(x)) for x in ("Net cash", "--", "n.a.", "COGS", "____")] == [True, True, True, False, False])
    ln0 = [(700, [(60, 120, "應收帳款周轉天數"), (170, 180, "3.2")]), (690, [(60, 90, "Adj."), (92, 100, "tax"), (102, 115, "rate"), (170, 190, "16.6%")]), (680, [(300, 340, "Cash"), (400, 420, "300")])]
    its = [_xv_item(ln0, x) for x in (",凱基 應收帳款周轉天數", "Ratios Adj. tax rate", "Cash", "Total liabilities")]
    chk("⓪ v0232 科目照原文:前綴雜字去掉 · 本來就在原文的不動 · 原文沒有的不亂改 → %s" % its, its == ["應收帳款周轉天數", "Adj. tax rate", "Cash", "Total liabilities"])
    td = Path(tempfile.mkdtemp(prefix="v0232-"))
    pdf = td / "XV-2330 20260101.pdf"
    ok_pdf = False
    try:
        from reportlab.pdfgen import canvas as _cv
        cv = _cv.Canvas(str(pdf), pagesize=(595, 842))
        cv.setFont("Helvetica", 9)
        for x, t in ((60, "Income (NT$m)"), (170, "2024"), (220, "2025E"), (320, "Balance (NT$m)"), (430, "2024"), (480, "2025E")):
            cv.drawString(x, 700, t)
        for x, t in ((60, "Revenue"), (170, "1,200"), (220, "1,500"), (320, "Cash"), (430, "300"), (480, "350")):
            cv.drawString(x, 686, t)
        cv.drawString(60, 640, "Analyst Ann Lee +886 2 2345 6789 ann.lee@xv.com")
        cv.save()
        ok_pdf = True
    except Exception:  # noqa: BLE001
        pass
    if ok_pdf:
        ln = _xv_lines(pdf, 1, {})
        r1, r2, r3 = _xv_cell(ln, "Revenue", "2025E", "1,500"), _xv_cell(ln, "Cash", "2024", "300"), _xv_cell(ln, "Revenue", "2024", "1,500")
        chk("⓪ v0232 對欄(並排兩表各自表頭):Revenue 2025E 1,500 → %s · Cash 2024 300 → %s · Revenue 2024 填成 1,500 → %s" % (r1[0], r2[0], r3[0]),
            r1[0] == "ALIGNED" and r2[0] == "ALIGNED" and r3[0] == "MISALIGNED")
        res = [{"file": pdf.name, "lamp": "GREEN", "pages": [{"pno": 1, "zones": [
            {"id": "P1·M·01·TX", "major": "M", "minor": "TX", "records": [{"text": "Analyst Ann Lee +886 2 2345 6789 ann.lee@xv.com"}], "rows": []},
            {"id": "P1·F·02·TB", "major": "F", "minor": "TB", "records": [], "rows": [["Income (NT$m)", "2024", "2025E"], ["Old New", "Old New", "Old New"], ["Revenue", "1,200", "1,500"], ["Cost", "COGS", "1,000 900"]]}]}]}]
        acc = [{"file": pdf.name, "basic": {"tel": ("VERIFIED", "1/1 一致"), "email": ("VERIFIED", "1/1 一致"), "email_a": ["ann.lee@xv.com"]}, "metrics": {}, "summary": {}}]
        st = [{"file": pdf.name, "stock": True, "ticker": "2330", "date": "2026-01-01", "broker": "XV", "parts": {}}]
        v2 = td / "vrn2"
        (v2 / "scope_in").mkdir(parents=True)
        import shutil
        shutil.copy2(str(pdf), str(v2 / "scope_in" / pdf.name))
        bk, fd, sm, gp, md = _out_books(res, acc, st, v2)
        rj = json.loads((v2 / "output" / "VRN2_Rejected_latest.json").read_text(encoding="utf-8"))
        chk("⓪ v0232 輸出冊:TEL 寫原文號碼 %r(不是比對說明)· 年度數據只留對欄 %s · 剔除 %s" % (bk[0]["TEL"], [(x["PERIOD"], x["VALUE"], x["VERIFY"]) for x in fd], sorted(x["REASON"][:8] for x in rj)),
            bk[0]["TEL"] == "+886 2 2345 6789" and [(x["PERIOD"], x["VALUE"]) for x in fd] == [("2024", "1,200"), ("2025E", "1,500")] and all(x["VERIFY"].startswith("對欄") for x in fd)
            and sorted(x["REASON"][:4] for x in rj) == ["一格多值", "科目 /", "非數據列", "非數據列"] and _XV_LAST["item"][1] == "YELLOW")
    else:
        chk("⓪ v0232 對欄 / 輸出冊(需 reportlab 產生測試 PDF)", False)
    nm1 = _an_name("lily.tsai@ctbcsis.com", "攻藍海 NGS建庫市場\n蔡欣妤\nLily.tsai@ctbcsis.com\n一、營運", "建庫市場蔡欣妤 Lily.tsai@ctbcsis.com")
    nm2 = _an_name("sharon.shih@morganstanley.com", "Sharon Shih\nEquity Analyst\nSharon.Shih@morganstanley.com", "Sharon Shih Equity Analyst")
    nm3 = _an_name("lily.tsai@ctbcsis.com", "Lily.tsai@ctbcsis.com", "Lily.tsai@ctbcsis.com")
    nm4 = _an_name("10863@entrust.com.tw", "::研究員聯絡方式::\r\n研究員 許願\r\n電子信箱 10863@entrust.com.tw", "電子信箱 10863@entrust.com.tw")
    nm5 = _an_name("lily.tsai@ctbcsis.com", "前 日 收 盤 價 1 9 .2 0 元\r\n蔡欣妤\r\nLily.tsai@ctbcsis.com", "")
    chk("⓪ v0232 分析師照原文:%s · %s · %s · %s · %s" % (nm1, nm2, nm3, nm4, nm5), nm1 == ("蔡欣妤", "原文") and nm2 == ("Sharon Shih", "原文") and nm3[1].startswith("推算")
        and nm4 == ("許願", "原文") and nm5 == ("蔡欣妤", "原文"))
    ph = _ui_panel_html(Path(tempfile.mkdtemp()))
    c0 = _ui_cmd(False)
    chk("⓪ v0232 U/I:vrn2:// 動作 4 · 不上船同步 · 送出狀態 · 還原確認 · 備援指令第一步升優先權 + PS 加速器 · 無 via://",
        ph.count("href='vrn2://") == 4 and "vnopush" in ph and "vstat" in ph and "window.confirm" in ph and "via://" not in ph
        and c0.index("PriorityClass") < c0.index("VIA_PS_Accel_Module") < c0.index("& $py $A") and "VIA_VRN2_NO_PUSH = '1'" in _ui_cmd(True))
    chk("⓪ v0232 零替換:vrn2 / 成功登記是 v0231 同一段程式(重新綁定)· 前版函式未動", vrn2.__code__ is PRIOR.vrn2.__code__ and vrn2.__globals__ is globals() and PRIOR.vrn2.__globals__ is vars(PRIOR)
        and _success_register.__code__ is PRIOR._success_register.__code__)
    c = completion(0, 1, 1, True, {}, [], ("GREEN", "x"), ("GREEN", "y"), ("GREEN", "z"))
    chk("⓪ v0232 完成判定多一項「輸出值驗證」· 黃不擋完成 → %s" % c["items"][-1]["name"][:8], c["items"][-1]["name"].startswith("輸出值驗證"))
    chk("⓪ v0232 前版必須是 v0231(本版借用 v0231 的 vrn2 / 輸出冊名稱 · 前版不對 → 自測擋下 · 啟動器搬隔離改用前一版)→ %s" % getattr(PRIOR, "TAG", "?"), getattr(PRIOR, "TAG", "") == "v0231")
    print("  ── 前版 v0231 自測(原樣)──")
    rc_p = PRIOR.selftest()
    chk("⓪ 前版 %s 自測 rc %d" % (PRIOR_PATH.name, rc_p), rc_p == 0)
    print("[計] %s %s(%s)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, Path(__file__).name, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

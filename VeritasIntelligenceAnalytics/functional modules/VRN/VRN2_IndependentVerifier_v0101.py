#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_IndependentVerifier_v0101 — VRN-2 輸出值獨立驗證(v0100 + 表頭列檢查 HDRVAL · 由 tools/verify_outputs v3 升版 · 啟動器 v0128 內嵌 · ⑦ 之後背景跑 · 只讀)。
  不 import 任何 VRN-2 程式 · 讀法與擷取不同(年度數據 pypdfium2 字元框 · 子欄 / 轉置表 PyMuPDF · 擷取用 pdfplumber)。

用法:python VRN2_IndependentVerifier_v0101.py <output 夾> <PDF 夾> <報告 .json> [--ui <VRN2_UI_latest.html>]
      python VRN2_IndependentVerifier_v0101.py --selftest
  基本資料:每欄值必須在 PDF 原文找得到(或可由原文重算)· 推算值要標推算
  年度數據:每筆 VALUE 必須在該頁 · 同列有 ITEM · 數值落在 PERIOD 表頭那一欄(x 對齊)
  子欄(SUBCOL):PyMuPDF 字詞框另查 · 轉置表(VERIFY 有「轉置」)另查 · DUPKEY 一致性(同檔 · 表 · 列 · 科目 · 期間 · 子欄只能一個值)
  v0100:① 每筆帶冊內序號(_I)· 報告多 fin_rows(每筆判決)與冊指紋(fp)· --ui 把判決寫回 U/I「驗證過的輸出」分頁(指紋不同 → U/I 不套用)
        ② 值列與科目列上下錯開(值比科目高半行:凱基首頁 EV/EBITDA · 淨負債比率)→ 只在本列找不到值時看上下鄰列(互為最近 · 鄰列科目欄沒有別的字)
        ③ 兩個字詞的值(Net cash)整組比對
  v0101:HDRVAL(跟讀法無關):值是期間字(Dec-23A · FY24A · 2024E · 12/25 · Jan-26 …)· 科目整個是期間字 · 一整列的值都等於期間的年份 → 這一列是表頭不是數據(整列都標)
        (v0100 漏抓:表頭字本來就印在期間那一欄 → 對位 ALIGNED · 凱基 2637 現金流量表表頭 · JP 2330 資產負債 / 現金流量表表頭 · GS 6415 月份列)
  依檔分片平行(子行程 · 路數依 CPU / RAM · VRN2_VERIFY_PAR)· 另寫 <報告>.digest.txt(≤150 行 · 貼給 AI 用)
"""
VERSION = "VRN2_IndependentVerifier_v0101"


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


import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pypdfium2 as pdfium


def nfk(t):
    return unicodedata.normalize("NFKC", t or "")


_QD = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201b": "'", "\u2032": "'", "\u201c": '"', "\u201d": '"', "\u2033": '"',
                     "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2015": "-", "\u2212": "-", "\ufe63": "-"})


def squash(t):
    return re.sub(r"\s+", "", nfk(t).translate(_QD)).lower()


_PAGES = {}


def page_lines(pdf, pno):
    """回 [(y, [(x0, x1, token)])] · 依字元框分列分詞(列 = 字元垂直中心差 < 0.5 字高)。"""
    key = (str(pdf), pno)
    if key in _PAGES:
        return _PAGES[key]
    doc = pdfium.PdfDocument(str(pdf))
    out = []
    if 1 <= pno <= len(doc):
        tp = doc[pno - 1].get_textpage()
        chars = []
        for i in range(tp.count_chars()):
            ch = tp.get_text_range(i, 1)
            l, b, r, t = tp.get_charbox(i, loose=True)
            if ch in ("\r", "\n") or r <= l:
                chars.append(None)
                continue
            chars.append((ch, l, b, r, t))
        rows = []
        for c in chars:
            if c is None:
                continue
            ch, l, b, r, t = c
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
            out.append((yc, [(a, b_, nfk(s)) for a, b_, s in toks]))
        out.sort(key=lambda x: -x[0])
    doc.close()
    _PAGES[key] = out
    return out


def page_text(pdf, pno):
    return "\n".join(" ".join(t for _, _, t in toks) for _, toks in page_lines(pdf, pno))


_IMG = {}


def is_image(pdf, pno=1):
    """這頁沒有文字層(影像 PDF · 要 OCR):兩個讀取器都 < 40 個非空白字。"""
    key = (str(pdf), pno)
    if key not in _IMG:
        n = len(re.sub(r"\s+", "", page_text(pdf, pno)))
        if n < 40:
            try:
                import pdfplumber
                with pdfplumber.open(str(pdf)) as d:
                    n = max(n, len(re.sub(r"\s+", "", (d.pages[pno - 1].extract_text() or "") if pno <= len(d.pages) else "")))
            except Exception:  # noqa: BLE001
                pass
        _IMG[key] = n < 40
    return _IMG[key]


def all_text(pdf, pages=(1, 2, 3, 4, 5, 6, 7, 8)):
    """兩個讀取器聯集(pypdfium2 字元框 + pdfplumber 文字層)· 去掉字母間的字型雜訊 %(To%mmy → Tommy)。"""
    import pdfplumber
    t = [page_text(pdf, p) for p in pages]
    try:
        with pdfplumber.open(str(pdf)) as d:
            t += [(d.pages[p - 1].extract_text() or "") for p in pages if p <= len(d.pages)]
    except Exception:  # noqa: BLE001
        pass
    return re.sub(r"(?<=[A-Za-z\u4e00-\u9fff])%(?=[A-Za-z\u4e00-\u9fff])", "", nfk("\n".join(t)))


def num_in(v, text):
    """數值回原文:字面 · 字距拆開 · 千分位 · 小數位不同(4200 = 4,200.00)都算同值。"""
    v = nfk(v).strip().lstrip("+")
    if not v:
        return True
    pat = r"(?<![\d,])(?<!\d\.)" + re.escape(v) + r"(?![\d])"
    if re.search(pat, text):
        return True
    t = re.sub(r"(?<=[\d.,])\s+(?=[\d.,])", "", nfk(text))
    if re.search(pat, t):
        return True
    vv = v.replace(",", "").rstrip("%")
    try:
        fv = float(vv)
    except ValueError:
        return False
    for tt in (nfk(text), t):                                            # 原樣 + 字距接回 兩種都比(接回會把換行兩邊的數字黏住)
        t2 = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", tt)
        if any(abs(float(x) - fv) < 1e-9 for x in re.findall(r"(?<![\d.])\d+(?:\.\d+)?(?![\d.])", t2)):
            return True
    return False


RATING_ONLY = re.compile(r"(?i)^(?:中立|買進|買入|賣出|持有|增加持股|減碼|區間操作|未評等|neutral|buy|sell|hold|outperform|underperform|overweight|underweight|equal[- ]?weight|not rated|nr)(?:\s*[(（][^)）]{1,14}[)）])?$")


def src_score(v, raw_sq):
    """原文覆蓋率:值壓縮後每 6 字一窗(步距 3)有幾成在原文(兩讀取器聯集)· 跨欄交錯的標題也量得到。"""
    sv = squash(v)
    if len(sv) <= 6:
        return 1.0 if sv in raw_sq else 0.0
    wins = [sv[i:i + 6] for i in range(0, len(sv) - 5, 3)]
    return sum(1 for w in wins if w in raw_sq) / len(wins)


def _hits(tk, sv, xmin=-1e9, xmax=1e9):
    """一列字詞裡等於值的 [(中心 x, x0, x1, 字)](xmin < x0 < xmax)· v0100 相鄰兩個字詞(字距 < 4)合起來等於值也算(Net cash)。"""
    tk = sorted(tk)
    out = [((a + b) / 2, a, b, t) for a, b, t in tk if xmin < a < xmax and (squash(t) == sv or squash(t) == sv.replace(",", ""))]
    for (a1, b1, t1), (a2, b2, t2) in zip(tk, tk[1:]):
        if xmin < a1 < xmax and 0 <= a2 - b1 < 4 and squash(t1 + t2) == sv:
            out.append(((a1 + b2) / 2, a1, b2, t1 + " " + t2))
    return out


_MONI = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"))}


def _mi(t):
    """「月-年」期間(Dec-27F)→ 月序號 · 不是 → None。"""
    m = re.match(r"^([A-Za-z]{3})-(\d{2})[AEFP]?$", t)
    return int(m.group(2)) * 12 + _MONI[m.group(1).lower()] if m and m.group(1).lower() in _MONI else None


def _qtr_x(tk):
    """v0100 表頭一列裡相鄰兩個「月-年」期間差 3 個月 = 季度欄 → 回這些字的 x0(差 12 個月 = 年度欄)。"""
    ms = [(a, _mi(t)) for a, b, t in sorted(tk) if _mi(t) is not None]
    q = set()
    for (a1, m1), (a2, m2) in zip(ms, ms[1:]):
        if m2 - m1 == 3:
            q.update((a1, a2))
    return q


def _align(lines, y, per, hits, best=None):
    """每個在上方、同期間字樣的表頭都試 · 取 x 最近(並排表各自的表頭)· 回 (dx, 欄寬, 表頭 x, 值 x, 表頭寬, 表頭 y, 是否季度欄)。
    v0100 同一列表頭同一個期間印兩次(季度段 Dec-27F · 年度段 Dec-27F)→ 只用年度那個(年度數據冊)。"""
    for yy, tk in lines:
        if not (y - 1 < yy < y + 520):
            continue
        qx = _qtr_x(tk)
        dup = sum(1 for a, b, t in tk if t == per) >= 2 and any(a not in qx for a, b, t in tk if t == per)
        for a, b, t in tk:
            if t != per or (dup and a in qx):
                continue
            hx = (a + b) / 2
            colw = min([abs((aa + bb) / 2 - hx) for aa, bb, tt in tk if tt != per and re.match(r"^(?:FY)?\d{2,4}[AEFP]?$|^\d{1,2}/\d{2}[AEFe]?$|^[A-Z][a-z]{2}-\d{2}[AEF]$", tt)] + [60])
            oth = [(aa + bb) / 2 for aa, bb, tt in tk if (aa, tt) != (a, t) and re.match(r"^(?:FY)?\d{2,4}[AEFP]?$|^\d{1,2}/\d{2}[AEFe]?$|^[A-Z][a-z]{2}-\d{2}[AEFP]$", tt)]
            for vx, va, vb, vt in hits:
                dx = abs(vx - hx)
                if any(abs(c - vx) < dx for c in oth):              # v0100 值離別的期間表頭更近 → 不是這一欄
                    continue
                if best is None or dx < best[0]:
                    best = (dx, colw, hx, vx, b - a, yy, a in qx)
    return best


_NILT = re.compile(r"(?i)^(?:[-–—]+|n\.?a\.?|nm|n/?m|n/?a|nil|neg\.?|ns)$")


def _isval(t):
    """數值或空值記號(- · n.a. · NM …)。"""
    return bool(re.search(r"\d", t)) or bool(_NILT.match(t))


def _lab_block(tk, key):
    """這一列含科目前 14 字的那段科目字(從科目開頭起 · 左右接同一詞組的非數值字詞 · 字距 < 6)→ (x0, x1, 壓縮字) · 沒有 → None。"""
    tk = sorted(tk)
    sp = None
    for i in range(len(tk)):
        s = ""
        for j in range(i, len(tk)):
            s += squash(tk[j][2])
            if key in s:
                sp = (i, j)
                break
            if len(s) > len(key) + 40:
                break
        if sp:
            break
    if not sp:
        return None
    i, j = sp
    while i < j and key in "".join(squash(t) for _, _, t in tk[i + 1:j + 1]):   # 從科目開頭那個字起(不帶左邊別欄的字)
        i += 1
    while i > 0 and not _isval(tk[i - 1][2]) and tk[i][0] - tk[i - 1][1] < 6:    # 同一詞組的字距 ≤ 4 pt · 別欄 / 並排表 ≥ 7 pt(實測)
        i -= 1
    while j + 1 < len(tk) and not _isval(tk[j + 1][2]) and tk[j + 1][0] - tk[j][1] < 6:
        j += 1
    return tk[i][0], tk[j][1], "".join(squash(t) for _, _, t in tk[i:j + 1])


def _lab_ok(lab, isq):
    """v0100 這一列的科目字就是這個科目(不是只「含」:EPS ≠ EPS growth · Revenue ≠ Total revenue):相同 · 折行(科目開頭 · 後半在下一列)· 原文多印單位(括號)。"""
    lab, isq = re.sub(r"^[•·\-–—*]+", "", lab), re.sub(r"^[•·\-–—*]+", "", isq)   # 開頭的項目符號(- · •)兩邊都去掉
    if lab == isq:
        return "同"
    if isq.startswith(lab) and len(lab) >= min(len(isq), 6):
        return "折行"
    if lab.startswith(isq) and re.fullmatch(r"[(\[(].*[)\])]|[:：]", lab[len(isq):]):
        return "單位"
    return ""


def _seg_end(tk, lx1):
    """v0100 並排表:科目右邊的值之後又出現別的科目字(另一張表)→ 這張表到那個字之前為止。"""
    seen = False
    ts = [z for z in sorted(tk) if z[0] > lx1 + 2]
    for i, (a, b, t) in enumerate(ts):
        pair = (squash(t) == "net" and i + 1 < len(ts) and squash(ts[i + 1][2]) == "cash" and ts[i + 1][0] - b < 4) or (squash(t) == "cash" and i > 0 and squash(ts[i - 1][2]) == "net")
        if _isval(t) or pair or squash(t) in ("x", "%"):
            seen = True
        elif seen and len(squash(t)) >= 2:
            return a - 1
    return 1e9


def _wrap_ok(lines, k, lb, isq):
    """v0100 折行要真的折行:下一列(16 pt 內)科目欄的字 = 科目剩下的那段(不然 Gross profit 那列會被當成 Gross profit margin)。"""
    lab, isq = re.sub(r"^[•·\-–—*]+", "", lb[2]), re.sub(r"^[•·\-–—*]+", "", isq)
    rest = isq[len(lab):]
    j = k + 1
    if not rest or j >= len(lines) or abs(lines[j][0] - lines[k][0]) >= 16:     # 折行那段可能在兩列中間(MS ModelWare net inc (NT / $ bn) 差 14.0 pt)
        return False
    nx = "".join(squash(t) for a, b, t in sorted(lines[j][1]) if lb[0] - 3 <= a <= lb[1] + 60 and not _isval(t))
    return bool(nx) and (rest.startswith(nx) or nx.startswith(rest))


def _lab_only(tk, lx0, lx1):
    """只有科目、沒有數值的列:科目欄起點有字 · 科目右邊沒有數值。"""
    return any(abs(a - lx0) <= 3 and not _isval(t) for a, b, t in tk) and not any(_isval(t) for a, b, t in tk if a > lx1 + 2)


def _row_hits(lines, k, lb, isq, sv):
    """v0100 這個科目那一列的值(先定列 · 再找值 → 別列的值不會被當成這一列的):
    科目列右邊有數值 → 只看科目列;沒有 → 上下鄰列中最近、有數值、科目欄不是別的科目(是科目接續可以)的那一列 · 那列不能離另一個只有科目的列更近(互為最近)。
    回 (hits, dy) · 定不出列 → None。"""
    y, tk = lines[k]
    lx0, lx1 = lb[0], lb[1]
    if any(_isval(t) for a, b, t in tk if a > lx1 + 2):
        return _hits(tk, sv, lx1 + 2, _seg_end(tk, lx1)), 0.0
    nb = []
    for j in (k - 1, k + 1):
        if 0 <= j < len(lines) and abs(lines[j][0] - y) < 14:
            tj = lines[j][1]
            labj = "".join(squash(t) for a, b, t in sorted(tj) if not _isval(t) and a < lx1 and b > lx0)
            if labj and labj not in isq:
                continue
            if any(_isval(t) for a, b, t in tj if a > lx1 + 2):
                nb.append((abs(lines[j][0] - y), j))
    if not nb:
        return None
    d, j = min(nb)
    if any(abs(lines[j][0] - lines[k2][0]) < d for k2 in (j - 1, j + 1) if k2 != k and 0 <= k2 < len(lines) and _lab_only(lines[k2][1], lx0, lx1)):
        return None
    return _hits(lines[j][1], sv, lx1 + 2, _seg_end(lines[j][1], lx1)), lines[j][0] - y


def verify_fin(rows, pdfdir, allrows=None):
    res = []
    occ = defaultdict(set)                                       # v0100 同一張表同名科目出現幾次(依 ROW · allrows = 整本冊的這幾檔 · 預設 rows)
    for z in (rows if allrows is None else allrows):
        if z.get("ROW"):
            occ[(z["FILENAME"], int(z["PAGE"]), z.get("TABLE"), nfk(z["ITEM"]).strip())].add(int(z["ROW"]))
    for x in rows:
        pdf = Path(pdfdir) / x["FILENAME"]
        lines = page_lines(pdf, int(x["PAGE"]))
        item, per, val = nfk(x["ITEM"]).strip(), nfk(x["PERIOD"]).strip(), nfk(x["VALUE"]).strip()
        sv = squash(val)
        # 1) 值在該頁
        ptxt = "\n".join(" ".join(t for _, _, t in tk) for _, tk in lines)
        present = num_in(val, ptxt) or sv in squash(ptxt)
        # 2) 科目那一列(科目前 14 字壓縮比對 · 允許科目折行:取科目起點所在列與下一列)
        key = squash(item)[:14]
        cand = []
        for k, (y, tk) in enumerate(lines):
            lt = squash("".join(t for _, _, t in tk))
            if key and key in lt:
                cand.append(k)
        # 3) 表頭期間欄 x(取在科目列上方、最近的那一個表頭)
        verdict, note = ("PRESENT" if present else "FAIL"), ("值在該頁 · 驗證器對不到期間欄" if present else "值不在該頁(驗證器讀法)")
        kind = "NUM" if re.search(r"\d", val) else ("NIL" if re.fullmatch(r"(?i)[-–—]+|n\.?a\.?|nm|n/?m|n/?a|na|nil|neg\.?|ns|--", val) else "TEXT")
        best, shift, how = None, None, ""
        si_ = squash(item)
        labs = []
        for k in cand:                                           # v0100 先定「這個科目那一列」:科目字相同(或折行 / 單位)· 值只從那一列找
            lb = _lab_block(lines[k][1], key)
            how_ = _lab_ok(lb[2], si_) if lb else ""
            if how_ == "折行" and not _wrap_ok(lines, k, lb, si_):
                how_ = ""
            if how_:
                labs.append((k, lb, how_))
        rk = sorted(occ.get((x["FILENAME"], int(x["PAGE"]), x.get("TABLE"), item), ()))
        if len(rk) >= 2 and len(labs) == len(rk) and x.get("ROW") and int(x["ROW"]) in rk and max(lb[0] for _, lb, _ in labs) - min(lb[0] for _, lb, _ in labs) < 10:
            labs = [labs[rk.index(int(x["ROW"]))]]               # 同名科目印了幾次就有幾列(同一欄 · 並排表不算)→ 第 n 次出現的那一列(由上往下)才是這一列
        for k, lb, how_ in labs:
            rh = _row_hits(lines, k, lb, si_, sv)
            if rh and rh[0]:
                b2 = _align(lines, lines[k][0], per, rh[0])
                if b2 and (best is None or b2[0] < best[0]):
                    best, shift, how = b2, rh[1], how_
        if best:
            dx, colw, hx, vx, hw, hy, qq = best
            if dx <= max(0.55 * colw, hw * 0.9, 12):
                verdict, note = "ALIGNED", "dx %.1f · 欄寬 %.0f · 科目列%s%s" % (dx, colw, how, (" · 值列在科目列%s %.1f pt(鄰列 · 互為最近)" % ("上" if shift > 0 else "下", abs(shift))) if shift else "")
                if qq:
                    verdict, note = "QTRCOL", "年度數據冊的值落在季度欄(表頭相鄰期間差 3 個月)· " + note
            else:
                verdict, note = "MISALIGNED", "值 x %.0f · 表頭 %s x %.0f · dx %.1f · 欄寬 %.0f" % (vx, per, hx, dx, colw)
        if kind == "TEXT" and not re.fullmatch(r"(?i)net\s*cash|淨現金", val):
            verdict, note = "BADVALUE", "VALUE 不是數字 / 空值記號(科目或底線混進數值欄)· " + note
        elif len([t for t in val.split() if re.search(r"\d", t) or re.fullmatch(r"(?i)[-–—]+|n\.?a\.?|n/a|nm|n\.m\.|nil", t)]) >= 2:
            verdict, note = "BADVALUE", "一格多值 · %s" % note
        si = squash(item)
        rows_sq = [squash("".join(t for _, _, t in tk)) for _, tk in lines]
        wrapped = any(si[:k] in rows_sq[i] and si[k:] in "".join(rows_sq[i + 1:i + 3]) for i in range(len(rows_sq)) for k in range(6, len(si) - 2))   # 科目折行
        if verdict in ("ALIGNED", "PRESENT") and si not in squash(ptxt) and not wrapped:
            verdict, note = "BADITEM", "科目 %r 本頁原文沒有 · %s" % (item, note)
        if verdict in ("FAIL", "MISALIGNED", "BADITEM") and is_image(pdf, int(x["PAGE"])):
            verdict, note = "OCR", "影像頁(文字層沒有字)· 人工核對 · " + note
        res.append(dict(x, _V=verdict, _N=note))
    return res


_PL = {}
_VTOK = re.compile(r"(?i)^(?:\(?-?\d[\d,]*\.?\d*\)?%?|\(?-?\.\d+\)?%?|\d+(?:\.\d+)?pp|n\.?a\.?|n/a|nm|n\.m\.|[-–—]+)$")
_PERTOK = re.compile(r"(?i)^(?:FY)?(?:19|20)?\d{2}[AEFP]?$|^[1-4]Q\d{2}[AEFP]?$|^(?:19|20)\d{2}\([AEFP]\)$")


def plumber_lines(pdf, pno):
    """第三種讀法(pdfplumber 字詞框 · 跟 VRN-2 子欄拆分用的 pypdfium2 不同):回 [(top, [(x0, x1, 字)])] 由上到下。"""
    key = (str(pdf), pno)
    if key not in _PL:
        import pdfplumber
        out = []
        with pdfplumber.open(str(pdf)) as d:
            if 1 <= pno <= len(d.pages):
                ws = d.pages[pno - 1].extract_words(keep_blank_chars=False)
                rows = []
                for w in sorted(ws, key=lambda w: w["top"]):
                    rw = next((r for r in rows if abs(r[0] - w["top"]) < 3.0), None)
                    if rw is None:
                        rw = [w["top"], []]
                        rows.append(rw)
                    rw[1].append((w["x0"], w["x1"], nfk(w["text"])))
                out = [(t, sorted(tk)) for t, tk in sorted(rows, key=lambda r: r[0])]
        _PL[key] = out
    return _PL[key]


_MU = {}


def mupdf_lines(pdf, pno):
    """第四種讀法(PyMuPDF 字詞框 · VRN-2 v0235 的閘用 pdfplumber · 拆分用 pypdfium2 → 驗證器用別的):回 [(top, [(x0, x1, 字)])] 由上到下 · 沒有 PyMuPDF → pdfplumber。"""
    key = (str(pdf), pno)
    if key not in _MU:
        try:
            import pymupdf as fitz  # noqa: WPS433
        except Exception:  # noqa: BLE001
            try:
                import fitz  # noqa: WPS433
            except Exception:  # noqa: BLE001
                _MU[key] = plumber_lines(pdf, pno)
                return _MU[key]
        out = []
        with fitz.open(str(pdf)) as d:
            if 1 <= pno <= len(d):
                rows = []
                for w in sorted(d[pno - 1].get_text("words"), key=lambda w: w[1]):
                    rw = next((r for r in rows if abs(r[0] - w[1]) < 3.0), None)
                    if rw is None:
                        rw = [w[1], []]
                        rows.append(rw)
                    rw[1].append((w[0], w[2], nfk(w[4])))
                out = [(t, sorted(tk)) for t, tk in sorted(rows, key=lambda r: r[0])]
        _MU[key] = out
    return _MU[key]


def _sub_lab(lines, k, x0, isq):
    """v0100 子欄那一列(值從 x0 起)左邊的科目字 = 這個科目(相同 / 折行兩列接起來 / 原文多印單位)· 值那一列沒有科目字 → 上下 14 pt 內只有科目的列。回 (是否相同, 讀到的科目)。"""
    def run(tk):
        ts = [(a, b, t) for a, b, t in sorted(tk) if b <= x0 + 1 and (not _isval(t) or squash(t) == isq)]   # 科目本身是 NM(淨利率)也算科目字
        if not ts:
            return ""
        r = [ts[-1]]
        for a, b, t in reversed(ts[:-1]):
            if r[0][0] - b < 6:
                r.insert(0, (a, b, t))
            else:
                break
        return "".join(squash(t) for _, _, t in r)
    lab = run(lines[k][1])
    if lab and _lab_ok(lab, isq) in ("同", "單位"):
        return True, lab
    for j in (k - 1, k + 1):
        if 0 <= j < len(lines) and abs(lines[j][0] - lines[k][0]) < 14 and not any(_isval(t) for a, b, t in lines[j][1] if a > x0 - 2):
            lj = run(lines[j][1])
            if lj and ((lab and _lab_ok(lj + lab if j < k else lab + lj, isq) in ("同", "單位")) or (not lab and _lab_ok(lj, isq) in ("同", "單位"))):
                return True, (lj + lab if j < k else lab + lj)
    return False, lab


def verify_subcol(rows, pdfdir):
    """子欄(一格多值拆開)逐列查 · PyMuPDF 字詞框(沒有 → pdfplumber):
    ① 整列數值序列 = 原文那一列(不漏 · 不多 · 順序同)② 期間 = 數據列上方最近的期間表頭
    ③ 同一期間內子欄標籤不重複 ④ 期間表頭的 x 落在該期間那組值的範圍內 ⑤ 子欄標籤 = 子表頭裡離這個值最近的那個字。"""
    grp = defaultdict(list)
    for x in rows:
        grp[(x["FILENAME"], x["TABLE"], int(x["PAGE"]), x["ITEM"])].append(x)
    res = []
    for (fn, tb, pno, item), xs in grp.items():
        lines = mupdf_lines(Path(pdfdir) / fn, pno)
        vals = [squash(x["VALUE"]) for x in xs]
        pers = list(dict.fromkeys(x["PERIOD"] for x in xs))
        bad = []
        cand = []
        for k, (top, tk) in enumerate(lines):
            vt = [(a, b, t) for a, b, t in tk if _VTOK.match(t) and squash(t) != squash(item)]   # 科目「NM」(淨利率)不是空值記號
            sq = [squash(t) for _, _, t in vt]
            for i in range(0, len(sq) - len(vals) + 1):
                if sq[i:i + len(vals)] == vals:
                    cand.append((k, vt[i:i + len(vals)], len(sq) == len(vals)))
        hit, hdr_ok, labs_ = None, False, []
        for k, vt, full in cand:                                         # 上方最近的期間表頭要含全部期間
            hk = next((kk for kk in range(k - 1, -1, -1) if sum(bool(_PERTOK.match(t)) for _, _, t in lines[kk][1]) >= 2), None)
            if hk is not None and all(any(t == p for _, _, t in lines[hk][1]) for p in pers):
                hdr_ok = True
                okl, lab_ = _sub_lab(lines, k, min(a for a, _, _ in vt), squash(item))   # v0100 ⑥ 那一列的科目 = 這個科目
                labs_.append(lab_)
                if okl:
                    hit = (k, vt, full, hk)
                    break
        if not hit:
            why = ("⑥ 同序列那一列的科目是 %s · 不是 %r(值是別列的)" % (" / ".join(repr(l_) for l_ in labs_[:3]) or "(沒有科目字)", item)) if hdr_ok else ("① ② " + ("原文找不到同序列的一列" if not cand else "數據列上方最近的期間表頭不是 %s" % "/".join(pers)))
            res += [dict(x, _V="SUBFAIL", _N=why) for x in xs]
            continue
        k, vt, full, hk = hit
        if not full:
            bad.append("① 原文那一列還有別的值(拆分不完整)")
        hdr = lines[hk][1]
        hx = {p: next(((a + b) / 2 for a, b, t in hdr if t == p)) for p in pers}
        x0_all = min(a for a, _, _ in vt)
        labw = [(a, b, t) for kk in range(hk + 1, k) for a, b, t in lines[kk][1]
                if not re.fullmatch(r"\(?%\)?", t) and not _VTOK.match(t) and (a + b) / 2 > x0_all - 25]
        by_p = defaultdict(list)
        for x, (a, b, t) in zip(xs, vt):
            by_p[x["PERIOD"]].append((x, a, b))
        for p, g in by_p.items():
            labs = [squash(x["SUBCOL"]) for x, _, _ in g]
            if len(set(labs)) != len(labs) or any(re.search(r"#\d+$", x["SUBCOL"]) for x, _, _ in g):
                bad.append("③ %s 子欄標籤重複 %s" % (p, [x["SUBCOL"] for x, _, _ in g]))
            ga, gb = min(a for _, a, _ in g), max(b for _, _, b in g)
            if not (ga - 14 <= hx[p] <= gb + 14):
                bad.append("④ %s 表頭 x %.0f 不在值的範圍 %.0f–%.0f" % (p, hx[p], ga, gb))
            for x, a, b in g:
                if not labw:
                    bad.append("⑤ 找不到子表頭")
                    break
                vx = (a + b) / 2
                nb = min(labw, key=lambda w: abs((w[0] + w[1]) / 2 - vx))
                first = squash(re.sub(r"\s*\(%\)$|\s*#\d+$", "", x["SUBCOL"]).split()[0] if x["SUBCOL"].split() else x["SUBCOL"])
                if squash(re.sub(r"\(%\)$", "", nb[2])) != re.sub(r"\(%\)$", "", first):
                    bad.append("⑤ %s %s 值 %s 最近的子表頭字是 %r" % (p, x["SUBCOL"], x["VALUE"], nb[2]))
        v = "SUBFAIL" if bad else "SUBALIGNED"
        res += [dict(x, _V=v, _N=" | ".join(bad[:3]) if bad else "PyMuPDF 子欄對位 · 表頭 %s" % "/".join(pers)) for x in xs]
    return res


_CJ = "\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"


def verify_trans(rows, pdfdir):
    """轉置表(年份在第一欄 · 科目在表頭)· PyMuPDF 字詞框另查:每個年份一行(年份後面緊接著同序列的值)· 各年份欄位置一致 ·
    欄界內的表頭字(數據上方相連 · 間距 ≤ 行距 + 2pt · 空行不算)接起來 = 科目。"""
    grp = defaultdict(list)
    for x in rows:
        grp[(x["FILENAME"], x["TABLE"], int(x["PAGE"]))].append(x)
    res = []
    for (fn, tb, pno), xs in grp.items():
        lines = mupdf_lines(Path(pdfdir) / fn, pno)
        pers = list(dict.fromkeys(x["PERIOD"] for x in xs))
        items = list(dict.fromkeys(x["ITEM"] for x in xs))
        val = {(x["PERIOD"], x["ITEM"]): x["VALUE"] for x in xs}
        why, hit = "", []
        for pe in pers:
            want = [squash(val.get((pe, it), "")) for it in items]
            found = []
            for k, (top, tk) in enumerate(lines):
                for i, (a, b, t) in enumerate(tk):
                    nxt = tk[i + 1:i + 1 + len(want)]
                    if squash(t) == squash(pe) and len(nxt) == len(want) and [squash(tt) for _, _, tt in nxt] == want:
                        found.append((k, (a + b) / 2, [(aa + bb) / 2 for aa, bb, _ in nxt]))
            if len(found) != 1:
                why = "%s 這一年原文找不到唯一一行同序列的值(%d)" % (pe, len(found))
                break
            hit.append(found[0])
        if not why:
            n = len(items)
            cx = [sorted(h[2][j] for h in hit)[len(hit) // 2] for j in range(n)]
            if any(abs(h[2][j] - cx[j]) > 10 for h in hit for j in range(n)):
                why = "各年份欄位置不一致"
        if not why:
            yx = hit[0][1]
            sp = (cx[-1] - cx[0]) / max(1, n - 1) if n > 1 else 40.0
            edges = [(yx + cx[0]) / 2] + [(cx[j] + cx[j + 1]) / 2 for j in range(n - 1)] + [cx[-1] + sp / 2]
            ks = sorted(h[0] for h in hit)
            gaps = sorted(abs(lines[ks[i + 1]][0] - lines[ks[i]][0]) for i in range(len(ks) - 1)) or [14]
            lim = min(gaps[len(gaps) // 2] + 2, 24)
            hdr, k, py = [], ks[0] - 1, lines[ks[0]][0]
            while k >= 0 and len(hdr) < 6:
                top, tk = lines[k]
                inr = [(a, b, t) for a, b, t in tk if edges[0] <= (a + b) / 2 < edges[-1]]
                if not inr:
                    k -= 1
                    continue
                if abs(py - top) > lim or any(re.search(r"\d", t) and _VTOK.match(t) for _, _, t in inr) or any("::" in t or re.match(r"(?i)^(?:單位|units?\b)", t) for _, _, t in tk):
                    break
                hdr.insert(0, inr)
                py, k = top, k - 1
            labs = [re.sub(r"(?<=[%s])\s+|\s+(?=[%s])" % (_CJ, _CJ), "", " ".join(t for r in hdr for a, b, t in sorted(r) if edges[j] <= (a + b) / 2 < edges[j + 1])).strip() for j in range(n)]
            if [squash(l_) for l_ in labs] != [squash(it) for it in items]:
                why = "表頭接出 %s ≠ 科目" % " / ".join(labs)
        res += [dict(x, _V="TRANSFAIL" if why else "TRANSALIGNED", _N=why or "PyMuPDF 轉置表對位 · %d 年 × %d 科目" % (len(pers), len(items))) for x in xs]
    return res


_BROKER = [(r"(?i)^CLST|clsa|cl-sec", "CLSA"), (r"(?i)^Citi|citi\.com", "Citi"), (r"(?i)^Daiwa|daiwa", "Daiwa"), (r"(?i)^GS-|gs\.com", "Goldman Sachs"),
           (r"(?i)^JP-|jpmorgan", "J.P. Morgan"), (r"(?i)^MQ-|macquarie", "Macquarie"), (r"(?i)^MS-|morganstanley", "Morgan Stanley"),
           (r"凱基|KGI", "凱基"), (r"中信|CTBC", "中信"), (r"華南", "華南"), (r"兆豐", "兆豐"), (r"台新", "台新")]


_MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def date_in(d, fname, t1):
    """REPORT_DATE(YYYY-MM-DD)在檔名或首頁:西元 / 民國 · 8 碼 / 6 碼 · / . - 年月日 · 英文月份(全名 / 縮寫 · 日月 / 月日)· 壓縮比對。"""
    try:
        y, m, dd = (int(z) for z in d.split("-"))
    except ValueError:
        return False
    roc = y - 1911
    fq = squash(fname)
    if any(s in fq for s in ("%04d%02d%02d" % (y, m, dd), "%03d%02d%02d" % (roc, m, dd), "%02d%02d%02d" % (y % 100, m, dd))):
        return True
    mn, ma = _MON[m - 1], _MON[m - 1][:3]
    cands = ["%04d-%02d-%02d" % (y, m, dd)]
    for yy in ("%04d" % y, "%d" % roc):
        for mm, de in (("%02d" % m, "%02d" % dd), ("%d" % m, "%d" % dd)):
            cands += [yy + sep + mm + sep + de for sep in ("/", ".", "-")] + ["%s年%s月%s日" % (yy, mm, de)]
    cands += ["%s %d, %d" % (mn, dd, y), "%s %d, %d" % (ma, dd, y), "%s. %d, %d" % (ma, dd, y), "%d %s %d" % (dd, mn, y), "%d %s %d" % (dd, ma, y),
              "%02d-%s-%02d" % (dd, ma, y % 100), "%d-%s-%d" % (dd, ma, y), "%02d %s %d" % (dd, ma, y)]
    tq = squash(t1)
    return any(squash(c) in tq for c in cands)


_LABRX = re.compile(r"(?i)(target\s*price|price\s*target|(?<![a-z])tp(?![a-z])|(?<![a-z])pt(?![a-z])|目標價|目標股價)"
                    r"|(share\s*price|shr\s*price|(?<![a-z])price(?![a-z])|(?<![a-z])close(?![a-z])|收盤價|股價|現價)"
                    r"|(up/downside(?:\s*to\s*price\s*target)?|upside(?:\s*to\s*(?:price\s*)?target)?|潛在漲幅|上漲空間|隱含漲幅|漲幅)")   # Up/downside to price target (%) 是上漲空間
_KIND = {"TARGET_PRICE": 1, "CURRENT_PRICE_REPORT": 2, "UPSIDE_PCT": 3}


def _numv(t):
    try:
        return float(t.replace(",", ""))
    except ValueError:
        return None


def near_label(pdf, v, field, pages=(1, 2)):
    """v0100 數值要在自己的標籤旁:同一列值左邊最近的標籤是這一種 · 同一列左邊沒有標籤 → 上下兩列內(30 pt · 標籤 x 與值相距 < 160)最近的標籤是這一種。
    標籤三種:目標價(Target price / Price target / TP / PT / 目標價)· 股價(Share price / Price / Close / 收盤價)· 上漲空間(Upside / 潛在漲幅)。回 (是否, 說明)。"""
    fv = _numv(re.sub(r"[^\d.,]", "", str(v)).strip(".,"))
    if fv is None:
        return False, "不是數字"
    want, seen = _KIND[field], []
    for pg in pages:
        L = page_lines(pdf, pg)
        info = []
        for y, tk in L:
            s_, xs = "", []
            for a, b, t in sorted(tk):
                xs.append((len(s_), a, b))
                s_ += t + " "
            def xat(off, xs=xs):
                return next((a for o, a, b in reversed(xs) if o <= off), xs[0][1] if xs else 0)
            labs = [(m.start(), m.end(), 1 if m.group(1) else (2 if m.group(2) else 3), xat(m.start())) for m in _LABRX.finditer(s_)]
            info.append((y, s_, labs, xat))
        for i, (y, s_, labs, xat) in enumerate(info):
            for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", s_):
                if _numv(m.group()) != fv:
                    continue
                vx = xat(m.start())
                bef = [l_ for l_ in labs if l_[1] <= m.start()]
                if bef:
                    kind = max(bef, key=lambda l_: l_[1])[2]
                else:
                    near = [(abs(info[j][0] - y), abs(l_[3] - vx), l_[2]) for j in range(max(0, i - 2), min(len(info), i + 3)) if j != i and abs(info[j][0] - y) < 30
                            for l_ in info[j][2] if abs(l_[3] - vx) < 160]
                    kind = min(near)[2] if near else 0
                seen.append(kind)
                if kind == want:
                    return True, "第 %d 頁 · 標籤旁(%s)" % (pg, s_[max(0, m.start() - 40):m.end()].strip()[-60:])
    names = {0: "沒有標籤", 1: "目標價標籤", 2: "股價標籤", 3: "上漲空間標籤"}
    return False, ("前兩頁沒有這個數" if not seen else "前兩頁有這個數 · 但旁邊是%s" % "、".join(sorted({names[k] for k in seen})))


def verify_basic(rows, pdfdir):
    out = []
    for x in rows:
        pdf = Path(pdfdir) / x["FILENAME"]
        t1 = all_text(pdf, (1,))
        ta = all_text(pdf)
        st = x.get("_STATUS") or {}
        chk = {}
        def put(k, ok, why=""):
            chk[k] = ("PASS" if ok else "FAIL") + ((" · " + why) if why else "")
        f = x["FILENAME"]
        tk = x.get("TICKER", "")
        put("TICKER", bool(tk) and (tk in f or tk in t1), "檔名或首頁")
        d = x.get("REPORT_DATE", "")
        if d:
            put("REPORT_DATE", date_in(d, f, t1), "檔名 / 首頁(多種日期寫法)")
        tt = x.get("TITLE", "")
        if tt:
            sc = src_score(tt, squash(ta))
            put("TITLE", sc >= 0.8 and not RATING_ONLY.match(nfk(tt).strip()), "原文覆蓋 %.0f%% · 不是只有評等" % (100 * sc))
        for k in ("YFINANCE_TICKER", "ENGLISH_NAME"):
            v = nfk(x.get(k, "")).strip()
            if v:
                put(k, squash(v) in squash(t1) or squash(v) in squash(ta), "原文")
        v = nfk(x.get("RATING", "")).strip()
        if v:                                                    # v0100 評等在前兩頁(後面的評等定義頁每種評等都有)
            put("RATING", squash(v) in squash(all_text(pdf, (1, 2))), "前兩頁原文")
        v = x.get("BLOOMBERG_TICKER", "")
        if v:
            put("BLOOMBERG_TICKER", squash(v) in squash(ta) or st.get("BLOOMBERG_TICKER", "").startswith("推算"), "原文或標推算")
        if x.get("NAME"):
            put("NAME", x["NAME"] in f or x["NAME"] in ta, "檔名 / 原文")
        for e in [e for e in (x.get("EMAIL") or "").split("、") if e]:
            put("EMAIL:" + e, e.lower() in re.sub(r"\s+", "", nfk(ta)).lower(), "原文")
        tel = x.get("TEL", "")
        if tel:
            digits = re.sub(r"\D", "", tel)
            put("TEL", len(digits) >= 8 and digits[-8:] in re.sub(r"\D", "", ta), "原文數字")
        accts = [" ".join(w.capitalize() for w in re.split(r"[._]", e.split("@")[0]) if w.isalpha()) for e in (x.get("EMAIL") or "").split("、") if e]
        for nm in [a for a in (x.get("ANALYST") or "").split("、") if a]:
            okn = squash(nm) in squash(ta) and not re.search(r"信箱|電話|郵件|傳真|地址|研究員|分析師|聯絡|日期", nm)
            if not okn and nm in accts and "推算" in (st.get("ANALYST") or ""):
                chk["ANALYST:" + nm] = "EST · 推算(已標示 · Email 帳號 · 原文沒印這個寫法)"
                continue
            put("ANALYST:" + nm, okn, "原文(姓名照原文印 · 不是欄位標籤)")
        b = x.get("BROKER", "")
        if b:
            exp = next((name for rx, name in _BROKER if re.search(rx, f) or re.search(rx, x.get("EMAIL", ""))), None)
            put("BROKER", exp is None or squash(exp)[:4] in squash(b) or squash(b)[:4] in squash(exp), "檔名 / 網域 → %s" % exp)
        for k in ("TARGET_PRICE", "CURRENT_PRICE_REPORT"):
            v = x.get(k, "")
            if v:                                                # v0100 要在自己的標籤旁(目標價 / 股價對調會被抓到)
                okl, why = near_label(pdf, v, k)
                put(k, okl, why)
        up = x.get("UPSIDE_PCT", "")
        if up:
            if (st.get("UPSIDE_PCT") or "").startswith("計算"):
                try:
                    calc = (float(x["TARGET_PRICE"].replace(",", "")) / float(x["CURRENT_PRICE_REPORT"].replace(",", "")) - 1) * 100
                    put("UPSIDE_PCT", abs(calc - float(up)) < 0.06, "重算 %.2f" % calc)
                except (ValueError, ZeroDivisionError, KeyError):
                    put("UPSIDE_PCT", False, "無法重算")
            else:
                okl, why = near_label(pdf, up.lstrip("+"), "UPSIDE_PCT")
                put("UPSIDE_PCT", okl, why)
        if is_image(pdf, 1):
            chk = {k: ("OCR · 影像頁(文字層沒有字)· 人工核對" if v.startswith("FAIL") else v) for k, v in chk.items()}
        out.append({"FILENAME": f, "checks": chk})
    return out


def _nums_raw(text):
    """原文數字(兩種讀法聯集:原樣 · 字距拆開接回)· 千分位去掉。原樣那份不接空白(表格相鄰數字不會黏在一起)。"""
    out = []
    for t in (nfk(text), re.sub(r"(?<=[\d.,])\s+(?=[\d.,])", "", nfk(text))):
        t = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", t)
        out += [float(x) for x in re.findall(r"(?<![\d.])\d+(?:\.\d+)?(?![\d.])", t)]
    return out


_PREV = re.compile(r"(?i)target|(?<![a-z])tp(?![a-z])|(?<![a-z])pt(?![a-z])|目標價|from|prior|previous|原|前次|上調|調升|下修|調降|raise|lift|cut|lower")
_EPSL = re.compile(r"(?i)eps|每股盈餘|每股純益|稅後eps")


def _line_with(pdf, val, rx, pages=(1, 2, 3)):
    """v0100 這個數在前幾頁某一列 · 而且那一列有 rx 的字(原目標價要在「目標價 / from / 原 / 前次 …」那一列)。"""
    fv = _numv(str(val).strip(".,"))
    for pg in pages:
        for y, tk in page_lines(pdf, pg):
            s_ = " ".join(t for _, _, t in sorted(tk))
            if rx.search(s_) and any(_numv(m) == fv for m in re.findall(r"\d[\d,]*(?:\.\d+)?", s_)):
                return True
    return False


def _eps_ok(val, year, pdf, fin):
    """v0100 EPS 序列:年度數據冊同檔 EPS 科目、同年度期間有這個值(年度數據每筆另外驗過)· 冊裡沒有 → 原文有 EPS 字樣的那一列有這個數。"""
    fv = _numv(str(val))
    yy = str(year)
    eps_rows = [r for r in fin or () if _EPSL.search(str(r.get("ITEM", "")))]
    for r in eps_rows:
        if _EPSL.search(str(r.get("ITEM", ""))) and (yy in str(r.get("PERIOD", "")) or re.search(r"(?<!\d)%s(?!\d)" % yy[2:], str(r.get("PERIOD", "")))) and _numv(re.sub(r"[^\d.,-]", "", str(r.get("VALUE", "")))) == fv:
            return True, "年度數據 %s %s" % (r.get("ITEM"), r.get("PERIOD"))
    if eps_rows:                                                 # 年度數據有 EPS → 一定要同年度那一格(別年的 EPS 也在原文 EPS 那一列 · 不能用來過)
        return False, ""
    return (True, "原文 EPS 列") if _line_with(pdf, val, _EPSL, pages=tuple(range(1, 9))) else (False, "")


def verify_point(v, text, rsq, pdf=None, basic=None, fin=None):
    """一個重點 → 逐段檢查:原文句(覆蓋 ≥85% · 數字在原文)· 摘要器組句(評價句 / EPS 序列:輸入數字在原文 · 「計算」的值重算對得上)。回 (PASS/FAIL, 說明)。
    v0100(pdf 有給):目標價 = 基本資料目標價 · 原目標價在「目標價 / from / 原 / 前次」那一列 · 倍數原文印成「16x / 16 倍」· 報告上漲空間在上漲空間標籤旁 · EPS = 年度數據同年度 EPS(或原文 EPS 那一列)。"""
    v = nfk(v)
    segs = [x.strip(" ,，。") for x in re.split(r"[；;⚫•]", v) if x.strip(" ,，。")]
    nums = None
    bad, notes, eps = [], [], []
    for sg in segs:
        m = re.match(r"^(\d{4}) 年 .*?EPS.*?\s([\-\d.,]+)(?: TWD)?(?:\s*[（(]計算 YoY ([\-\d.]+)%[）)])?$", sg)
        if m:
            eps.append((int(m.group(1)), float(m.group(2).replace(",", "")), float(m.group(3)) if m.group(3) else None))
            if not num_in(m.group(2), text):
                bad.append("EPS %s 不在原文" % m.group(2))
            elif pdf is not None:
                ok_e, why_e = _eps_ok(m.group(2), m.group(1), pdf, fin)
                if not ok_e:
                    bad.append("%s 年 EPS %s 不是年度數據 / 原文 EPS 那一列的值" % (m.group(1), m.group(2)))
            continue
        if sg.startswith("目標價 ") or "上漲空間" in sg or sg.startswith(("原目標價", "目標價依據", "報告潛在")):
            for k_, val in re.findall(r"(目標價|原目標價|倍)\s*([\d.,]+)", sg) + [("倍", x) for x in re.findall(r"([\d.]+)\s*倍", sg)]:
                if not num_in(val, text):
                    bad.append("%s %s 不在原文" % (k_, val))
                elif pdf is None:
                    continue
                elif k_ == "目標價" and basic and basic.get("TARGET_PRICE") and _numv(val.strip(".,")) != _numv(re.sub(r"[^\d.,]", "", basic["TARGET_PRICE"]).strip(".,")):
                    bad.append("目標價 %s 與基本資料目標價 %s 不同" % (val, basic["TARGET_PRICE"]))
                elif k_ == "原目標價" and not _line_with(pdf, val, _PREV):
                    bad.append("原目標價 %s 不在原文「目標價 / from / 原 / 前次」那一列" % val)
                elif k_ == "倍" and not re.search(r"(?<![\d.])%s(?:\.0+)?\s*(?:x|X|倍|times)" % re.escape(val.strip(".,").rstrip("0").rstrip(".") if "." in val else val.strip(".,")), nfk(text)):
                    bad.append("倍數 %s 原文沒有印成「%sx / %s 倍」" % (val, val, val))
            mu = re.search(r"上漲空間\s*(-?[\d.]+)%", sg)
            if mu:
                if "計算" in sg:
                    tp = re.search(r"目標價\s*([\d.,]+)", v)
                    nums = nums if nums is not None else _nums_raw(text)
                    z = float(mu.group(1))
                    okz = tp is not None and any(n > 0 and abs((float(tp.group(1).replace(",", "")) / n - 1) * 100 - z) <= 0.06 for n in nums)
                    notes.append("上漲空間重算%s" % ("對" if okz else "對不上"))
                    if not okz:
                        bad.append("上漲空間 %s%% 重算對不上" % mu.group(1))
                elif not num_in(mu.group(1), text):
                    bad.append("上漲空間 %s%% 不在原文" % mu.group(1))
                elif pdf is not None and not near_label(pdf, mu.group(1), "UPSIDE_PCT")[0]:
                    bad.append("報告上漲空間 %s%% 不在原文上漲空間標籤旁" % mu.group(1))
            continue
        sc = src_score(sg, rsq)
        if sc < 0.85:                                                    # 標題 + 句子黏在一起(原文中間隔著圖表字)→ 兩段各自在原文也算
            q = squash(sg)
            if any(q[:k] in rsq and src_score(q[k:], rsq) >= 0.9 for k in range(4, min(len(q) - 4, 24))):
                sc = 0.9
        nb = [n for n in re.findall(r"\d[\d,]*\.?\d*", sg) if len(n.strip(",.")) >= 2 and not num_in(n.strip(",."), text)]
        if sc < 0.85 or nb:
            bad.append("原文句覆蓋 %.0f%%%s「%s」" % (100 * sc, (" · 數字不在原文 " + "、".join(nb[:3])) if nb else "", sg[:30]))
    for i, (y, x, yoy) in enumerate(eps):
        if yoy is None:
            continue
        prev = eps[i - 1][1] if i and eps[i - 1][0] == y - 1 else None
        if prev is not None:
            ok_ = prev and abs((x / prev - 1) * 100 - yoy) <= 0.06
        else:
            nums = nums if nums is not None else _nums_raw(text)
            ok_ = any(n and abs((x / n - 1) * 100 - yoy) <= 0.06 for n in nums)
        notes.append("%d YoY 重算%s" % (y, "對" if ok_ else "對不上"))
        if not ok_:
            bad.append("%d YoY %.1f%% 重算對不上" % (y, yoy))
    return ("FAIL" if bad else "PASS"), " · ".join(bad or notes)[:200]


def verify_summary(rows, pdfdir, basic=None, fin=None):
    out = []
    bmap = {b["FILENAME"]: b for b in (basic or [])}
    fmap = defaultdict(list)
    for r in fin or ():
        fmap[r["FILENAME"]].append(r)
    for x in rows:
        pdf = Path(pdfdir) / x["FILENAME"]
        text = all_text(pdf)
        rsq = squash(text)
        chk = {}
        if x.get("TITLE"):
            sc = src_score(x["TITLE"], rsq)
            chk["TITLE"] = ("PASS" if sc >= 0.8 and len(squash(x["TITLE"])) >= 4 and not RATING_ONLY.match(nfk(x["TITLE"]).strip()) else "FAIL") + " · 原文覆蓋 %.0f%%%s" % (100 * sc, "" if len(squash(x["TITLE"])) >= 4 else " · 太短")   # v0100 一兩個字的覆蓋率沒有意義
        for i in range(1, 5):
            v = x.get("POINT_%d" % i) or ""
            if v:
                r_, n_ = verify_point(v, text, rsq, pdf, bmap.get(x["FILENAME"]), fmap.get(x["FILENAME"]))
                if len(squash(v)) < 8:                           # v0100 太短的重點不算
                    r_, n_ = "FAIL", "太短(%d 字)" % len(squash(v))
                chk["POINT_%d" % i] = r_ + " · " + n_
        if is_image(pdf, 1):
            chk = {k: ("OCR · 影像頁(文字層沒有字)· 人工核對" if v.startswith("FAIL") else v) for k, v in chk.items()}
        out.append({"FILENAME": x["FILENAME"], "checks": chk, "points_ok": x.get("POINTS_OK")})
    return out


BADV = ("FAIL", "MISALIGNED", "BADVALUE", "BADITEM", "SUBFAIL", "TRANSFAIL", "DUPKEY", "QTRCOL", "DUPROW", "HDRVAL")   # v0100 + 季度欄 · 完全重複 · v0101 表頭列


def dupkey(vf):
    """一致性(跟讀法無關):同檔 · 同表 · 同一列(ROW · 沒有就用段落)· 同科目 · 同期間 · 同子欄 只能有一個值 → 兩個以上不同的值 = DUPKEY(兩種讀法一致地讀錯欄也抓得到)。"""
    g = defaultdict(set)
    k_ = lambda r: (r["FILENAME"], r.get("TABLE"), r.get("ROW") or ("S", r.get("SECTION", "")), r.get("ITEM"), r.get("PERIOD"), r.get("SUBCOL", ""))   # noqa: E731
    cnt = Counter()
    for r in vf:
        g[k_(r)].add(squash(r.get("VALUE", "")))
        cnt[k_(r)] += 1
    out = []
    for r in vf:
        vs = g[k_(r)]
        if len(vs) > 1:
            r = dict(r, _V="DUPKEY", _N="同一列同科目同期間有 %d 個不同的值:%s" % (len(vs), " / ".join(sorted(vs))[:80]))
        elif cnt[k_(r)] > 1:
            r = dict(r, _V="DUPROW", _N="同一列同科目同期間同值出現 %d 次(年度數據冊同一格只能一筆 · 多半是季度段同期間字的那一格)" % cnt[k_(r)])
        out.append(r)
    return out


_PERV = re.compile(r"(?i)^(?:(?:FY|CY)['’]?\d{2,4}[AEFPCTH]?|\d{4}(?:[AEFPH]|CT)|\d{1,2}/\d{2,4}[AEF]?|[A-Z][a-z]{2}-\d{2}[AEF]?|[1-4][QH]\d{2}[AEF]?)$")


def _perv(t):
    """期間字(Dec-23A · FY24A · 2024E · 2025CT · 12/25 · Jan-26 · 2Q26E · 1H26)· 純數字(2024)不算。"""
    return bool(_PERV.match(nfk(str(t or "")).strip()))


def _peryr(per):
    """期間的西元年(2024E → 2024 · FY24A / Dec-24A → 2024 · 12/25 → 2025)· 沒有 → ""。"""
    t = nfk(str(per or ""))
    m = re.search(r"(?:19|20)\d{2}", t)
    if m:
        return m.group(0)
    m = re.search(r"(?<!\d)(\d{2})(?:[AEFPH]|CT)?$", t)
    return "20" + m.group(1) if m else ""


def hdrval(vf):
    """v0101 一致性(跟讀法無關):年度數據的一列若是表頭(值是期間字 · 科目整個是期間字 · 一整列的值都等於期間的年份)→ 整列 HDRVAL。
    表頭字本來就印在期間那一欄 → 位置檢查會判對位(v0100 漏抓 11 筆)· 所以另查值的種類。"""
    k_ = lambda r: (r["FILENAME"], r.get("TABLE"), r.get("ROW") or ("S", r.get("SECTION", "")), r.get("ITEM"), r.get("SUBCOL", ""))   # noqa: E731
    g = defaultdict(list)
    for r in vf:
        g[k_(r)].append(r)
    why = {}
    for k, rs in g.items():
        it = nfk(str(k[3] or "")).split()
        pv = [str(r.get("VALUE", "")) for r in rs if _perv(r.get("VALUE"))]
        if pv:
            why[k] = "值是期間字 %s(這一列是表頭 · 不是數據)" % " / ".join(pv[:5])
        elif it and all(_perv(t) for t in it):
            why[k] = "科目整個是期間字 %s(這一列是表頭 · 不是數據)" % k[3]
        elif len(rs) >= 2 and all(_peryr(r.get("PERIOD")) and re.sub(r"[,\s]", "", str(r.get("VALUE", ""))) == _peryr(r.get("PERIOD")) for r in rs):
            why[k] = "一整列的值都等於期間的年份(這一列是表頭 · 不是數據)"
    return [dict(r, _V="HDRVAL", _N=why[k_(r)]) if k_(r) in why else r for r in vf]


def run_files(od, pdfdir, files):
    """指定的檔(None = 全部)→ (基本資料, 年度數據, 一標題四重點) 驗證結果。"""
    od = Path(od)
    pick = (lambda r: True) if files is None else (lambda r, fs=set(files): r["FILENAME"] in fs)
    basic = [r for r in json.loads((od / "VRN2_BasicInfo_latest.json").read_text(encoding="utf-8")) if pick(r)]
    fin = [dict(r, _I=i) for i, r in enumerate(json.loads((od / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))) if pick(r)]   # v0100 冊內序號
    sp = od / "VRN2_Summary_latest.json"
    summ = [r for r in json.loads(sp.read_text(encoding="utf-8")) if pick(r)] if sp.exists() else []
    vb = verify_basic(basic, pdfdir)
    tr = lambda x: "轉置" in str(x.get("VERIFY", ""))                       # noqa: E731
    vf = (verify_fin([x for x in fin if not x.get("SUBCOL") and not tr(x)], pdfdir) + verify_subcol([x for x in fin if x.get("SUBCOL")], pdfdir)
          + verify_trans([x for x in fin if tr(x)], pdfdir))
    vs = verify_summary(summ, pdfdir, basic, fin)                     # v0100 組句數字對基本資料 / 年度數據(兩本冊各自另外驗過)
    return vb, vf, vs


def _workers(n_files):
    """平行路數:CPU − 1(上限 6)· 可用 RAM < 2 GB → 2 · VRN2_VERIFY_PAR=1 序跑 / 數字 = 手動。"""
    import os
    env = os.environ.get("VRN2_VERIFY_PAR", "")
    if env.isdigit():
        return max(1, min(int(env), n_files))
    w = max(1, min(6, (os.cpu_count() or 2) - 1, n_files))
    try:
        import psutil
        if psutil.virtual_memory().available < 2 * 1024 ** 3:
            w = min(w, 2)
    except Exception:  # noqa: BLE001
        pass
    return w


def run_parallel(od, pdfdir):
    """依檔分片 · 子行程平行(每路自己的快取 · 依年度數據筆數 LPT 分配)· 子行程先接加速器(VRN2_ACCEL_WRAP + VRN2_VIA_ROOT 有給就經包裝執行)。"""
    import os
    import subprocess
    import tempfile
    from collections import Counter as _C
    od = Path(od)
    fin = json.loads((od / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))
    basic = json.loads((od / "VRN2_BasicInfo_latest.json").read_text(encoding="utf-8"))
    load = _C(r["FILENAME"] for r in fin)
    files = sorted({r["FILENAME"] for r in basic} | set(load), key=lambda f_: -load.get(f_, 0))
    w = _workers(len(files))
    if w <= 1:
        return run_files(od, pdfdir, None) + (1,)
    shards = [[] for _ in range(w)]
    tot = [0] * w
    for f_ in files:
        i = tot.index(min(tot))
        shards[i].append(f_)
        tot[i] += load.get(f_, 0) + 30
    td = Path(tempfile.mkdtemp(prefix="vrn2_verify_"))
    head = [sys.executable]
    if os.environ.get("VRN2_ACCEL_WRAP") and os.environ.get("VRN2_VIA_ROOT"):
        head += [os.environ["VRN2_ACCEL_WRAP"], os.environ["VRN2_VIA_ROOT"]]
    procs = []
    for i, sh in enumerate(shards):
        (td / ("in_%d.json" % i)).write_text(json.dumps(sh, ensure_ascii=False), encoding="utf-8")
        procs.append(subprocess.Popen(head + [str(Path(__file__).resolve()), "--shard", str(od), str(pdfdir), str(td / ("in_%d.json" % i)), str(td / ("out_%d.json" % i))],
                                      stdout=subprocess.DEVNULL, stderr=open(td / ("err_%d.txt" % i), "w", encoding="utf-8")))
    vb, vf, vs = [], [], []
    for i, pr in enumerate(procs):
        pr.wait()
        op = td / ("out_%d.json" % i)
        if pr.returncode != 0 or not op.exists():
            raise RuntimeError("驗證分片 %d 失敗:%s" % (i, (td / ("err_%d.txt" % i)).read_text(encoding="utf-8")[-600:]))
        d = json.loads(op.read_text(encoding="utf-8"))
        vb += d["basic"]
        vf += d["fin"]
        vs += d["summary"]
    return vb, vf, vs, w


def write_digest(path, vb, vf, vs, w):
    """貼給 AI 的摘要(≤150 行):各冊計數 · 不過的類別與理由 · 每類最多 12 筆例子(檔 · 表 · 科目 · 期間 · 子欄 · 值 · 理由)。"""
    from collections import Counter as _C
    L = ["[驗證摘要] %s · 平行 %d 路" % (VERSION, w)]
    bc = _C(v.split(" ·")[0] for r in vb for v in r["checks"].values())
    sc = _C(v.split(" ·")[0] for r in vs for v in r["checks"].values())
    fc = _C(r["_V"] for r in vf)
    L += ["基本資料 %d 份 %s" % (len(vb), dict(bc)), "一標題四重點 %d 份 %s" % (len(vs), dict(sc)), "年度數據 %d 筆 %s" % (len(vf), dict(fc))]
    for nm, rs in (("基本資料", vb), ("一標題四重點", vs)):
        bad = [(r["FILENAME"], k, v) for r in rs for k, v in r["checks"].items() if not v.startswith("PASS")]
        for f_, k, v in bad[:25]:
            L.append("  %s %s · %s · %s" % (nm, f_[:44], k, v[:110]))
    for cat in BADV + ("OCR", "PRESENT"):
        xs = [r for r in vf if r["_V"] == cat]
        if not xs:
            continue
        why = _C(re.sub(r"[\d.,]+", "#", r["_N"])[:40] for r in xs)
        L.append("年度數據 %s %d 筆 · 理由前 3:%s" % (cat, len(xs), " | ".join("%s ×%d" % kv for kv in why.most_common(3))))
        byf = _C(r["FILENAME"] for r in xs)
        L.append("  檔:%s" % " · ".join("%s ×%d" % (f_[:30], n) for f_, n in byf.most_common(6)))
        for r in xs[:12 if cat in BADV else 4]:
            L.append("  %s | %s | %s | %s | %s | %s | %s" % (r["FILENAME"][:30], r.get("TABLE", ""), str(r.get("ITEM", ""))[:22], r.get("PERIOD", ""), r.get("SUBCOL", ""), r.get("VALUE", ""), r["_N"][:90]))
    Path(path).write_text("\n".join(L[:150]) + "\n", encoding="utf-8")
    return L[:150]


FP_KEYS = ("FILENAME", "PAGE", "TABLE", "ITEM", "PERIOD", "SUBCOL", "VALUE")


def book_fp(rows):
    """年度數據冊指紋(與 VRN-2 SystemManager v0237 U/I 同一算法 · 各自實作 · 不 import):逐筆 7 欄串接 → SHA-256 前 16 碼。"""
    h = hashlib.sha256()
    for r in rows:
        h.update(("\x1f".join(str(r.get(k, "")) for k in FP_KEYS) + "\x1e").encode("utf-8"))
    return h.hexdigest()[:16]


def ui_payload(vb, vf, vs, fp, n, w, ok, ts):
    """寫回 U/I 的判決(每筆年度數據依冊內序號 · 基本資料 / 一標題四重點依檔)。"""
    fin = [None] * n
    for r in vf:
        i = r.get("_I")
        if isinstance(i, int) and 0 <= i < n:
            fin[i] = [r["_V"], r["_N"][:120]]
    return {"ver": VERSION, "ts": ts, "fp": fp, "n": n, "w": w, "ok": ok,
            "counts": {"basic": dict(Counter(v.split(" ·")[0] for r in vb for v in r["checks"].values())),
                       "summary": dict(Counter(v.split(" ·")[0] for r in vs for v in r["checks"].values())),
                       "fin": dict(Counter(r["_V"] for r in vf))},
            "basic": {r["FILENAME"]: r["checks"] for r in vb}, "summary": {r["FILENAME"]: r["checks"] for r in vs}, "fin": fin}


_IV_RE = re.compile(r'<script id="vrn2-iv">window\.VRN2_IV=.*?;</script>', re.S)


def inject_ui(html_path, payload):
    """把判決寫進 U/I 的 <script id="vrn2-iv"> 佔位(先寫暫存檔再換 · 「<」一律跳脫 → 值裡的 </script> 不會截斷頁面)。回 (成功, 說明)。"""
    p = Path(html_path)
    if not p.is_file():
        return False, "找不到 U/I %s" % p
    page = p.read_text(encoding="utf-8")
    if not _IV_RE.search(page):
        return False, "U/I 沒有驗證佔位(不是 v0237 以後的管理器產生的頁)"
    js = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    page = _IV_RE.sub(lambda m: '<script id="vrn2-iv">window.VRN2_IV=%s;</script>' % js, page, count=1)
    tmp = p.with_name(p.name + ".iv.tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(p)
    return True, "已寫回 U/I %s(指紋 %s · %d 筆)" % (p, payload["fp"], payload["n"])


def main(od, pdfdir, rep, ui=None):
    import datetime
    vb, vf, vs, w = run_parallel(od, pdfdir)
    vf = hdrval(dupkey(vf))                                              # v0101 表頭列(跟讀法無關)
    sc_ = Counter(v.split(" ·")[0] for r in vs for v in r["checks"].values())
    bc = Counter(v.split(" ·")[0] for r in vb for v in r["checks"].values())
    fc = Counter(r["_V"] for r in vf)
    per_file = defaultdict(Counter)
    for r in vf:
        per_file[r["FILENAME"]][r["_V"]] += 1
    book = json.loads((Path(od) / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))
    fp = book_fp(book)
    rc = 0 if not any(v.startswith("FAIL") for r in vb + vs for v in r["checks"].values()) and not any(fc.get(k) for k in BADV) else 1
    Path(rep).write_text(json.dumps({"version": VERSION, "fp": fp, "n": len(book), "basic": vb, "summary": vs, "summary_counts": dict(sc_), "fin_counts": dict(fc), "fin_per_file": {k: dict(v) for k, v in per_file.items()},
                                     "fin_bad": [r for r in vf if r["_V"] in BADV], "fin_ocr": [r for r in vf if r["_V"] == "OCR"],
                                     "fin_rows": sorted([r.get("_I"), r["_V"], r["_N"]] for r in vf if isinstance(r.get("_I"), int))}, ensure_ascii=False, indent=1), encoding="utf-8")
    write_digest(str(rep) + ".digest.txt", vb, vf, vs, w)
    print("[驗證] 基本資料 %d 份 · 欄位檢查 %s" % (len(vb), dict(bc)))
    for r in vb:
        bad = {k: v for k, v in r["checks"].items() if v.startswith("FAIL")}
        if bad:
            print("  [FAIL] %s · %s" % (r["FILENAME"][:40], " | ".join("%s %s" % kv for kv in bad.items())[:300]))
    print("[驗證] 一標題四重點 %d 份 · 欄位檢查 %s" % (len(vs), dict(sc_)))
    for r in vs:
        bad = {k: v for k, v in r["checks"].items() if v.startswith("FAIL")}
        if bad:
            print("  [FAIL] %s · %s" % (r["FILENAME"][:40], " | ".join("%s %s" % kv for kv in bad.items())[:300]))
    print("[驗證] 年度數據 %d 筆 · %s" % (len(vf), dict(fc)))
    for f, c in sorted(per_file.items()):
        print("  %-46s %s" % (f[:46], dict(c)))
    print("[驗證] 摘要 %s.digest.txt(貼給 AI 用)· 平行 %d 路 · 冊指紋 %s · 每筆判決 %d / %d" % (rep, w, fp, sum(1 for r in vf if isinstance(r.get("_I"), int)), len(book)))
    if ui:
        ok_, msg = inject_ui(ui, ui_payload(vb, vf, vs, fp, len(book), w, rc == 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        print("[驗證] U/I %s · %s" % ("寫回" if ok_ else "未寫回", msg))
    return rc


def selftest():
    """不需 PDF:指紋 · 寫回 U/I(跳脫 · 重寫)· DUPKEY · v0101 HDRVAL · 兩個字詞的值 · 先定列再找值(鄰列互為最近)· 科目字相同。"""
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        p, f = (p + 1, f) if cond else (p, f + 1)
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    rows = [{"FILENAME": "a.pdf", "PAGE": 1, "TABLE": "T", "ITEM": "Revenue", "PERIOD": "2026E", "VALUE": "100"},
            {"FILENAME": "a.pdf", "PAGE": 1, "TABLE": "T", "ITEM": "Revenue", "PERIOD": "2027E", "VALUE": "</script>"}]
    fp1, fp2 = book_fp(rows), book_fp([rows[1], rows[0]])
    chk("指紋:16 碼 · 次序不同 → 指紋不同 · 同內容 → 相同", len(fp1) == 16 and fp1 != fp2 and fp1 == book_fp([dict(r) for r in rows]))
    chk("指紋算法固定(與管理器 v0237 同一組欄位與分隔字元)", FP_KEYS == ("FILENAME", "PAGE", "TABLE", "ITEM", "PERIOD", "SUBCOL", "VALUE") and
        book_fp([{"FILENAME": "x", "VALUE": "1"}]) == hashlib.sha256("x\x1f\x1f\x1f\x1f\x1f\x1f1\x1e".encode()).hexdigest()[:16])
    td = Path(tempfile.mkdtemp(prefix="vrn2iv-"))
    hp = td / "VRN2_UI_latest.html"
    hp.write_text('<html><body><h2>x</h2><script id="vrn2-iv">window.VRN2_IV=null;</script><p>tail</p></body></html>', encoding="utf-8")
    vf = [dict(rows[0], _I=0, _V="ALIGNED", _N="dx 1"), dict(rows[1], _I=1, _V="BADVALUE", _N="</script><b>")]
    pl = ui_payload([], vf, [], fp1, 2, 1, False, "t")
    ok1, _ = inject_ui(hp, pl)
    t1 = hp.read_text(encoding="utf-8")
    seg = t1.split('<script id="vrn2-iv">window.VRN2_IV=', 1)[1].split(";</script>", 1)[0]
    chk("寫回 U/I:佔位換成判決 · 值裡的 </script> 已跳脫 · 頁尾還在", ok1 and "</script><b>" not in seg and t1.endswith("<p>tail</p></body></html>") and json.loads(seg)["fin"][1][0] == "BADVALUE")
    ok2, _ = inject_ui(hp, dict(pl, ts="t2"))
    t2 = hp.read_text(encoding="utf-8")
    chk("再寫一次 → 取代上一次(只留一份)", ok2 and t2.count('id="vrn2-iv"') == 1 and '"ts":"t2"' in t2)
    hp2 = td / "old.html"
    hp2.write_text("<html><body>舊版頁</body></html>", encoding="utf-8")
    chk("沒有佔位的舊頁 → 不寫(回說明)", inject_ui(hp2, pl)[0] is False and hp2.read_text(encoding="utf-8") == "<html><body>舊版頁</body></html>")
    d = dupkey([dict(rows[0], _V="ALIGNED", _N=""), dict(rows[0], VALUE="101", _V="ALIGNED", _N="")])
    chk("DUPKEY:同列同科目同期間兩個值 → 兩筆都標", [r["_V"] for r in d] == ["DUPKEY", "DUPKEY"])
    d2 = dupkey([dict(rows[0], _V="ALIGNED", _N=""), dict(rows[0], _V="ALIGNED", _N=""), dict(rows[1], _V="ALIGNED", _N="")])
    chk("DUPROW:同列同科目同期間同值兩筆 → 兩筆都標 · 別的期間不動", [r["_V"] for r in d2] == ["DUPROW", "DUPROW", "ALIGNED"])
    hr = [{"FILENAME": "k.pdf", "TABLE": "P5", "ROW": 70, "ITEM": "NT$百萬", "PERIOD": p_, "VALUE": p_, "_V": "ALIGNED", "_N": ""} for p_ in ("Dec-23A", "Dec-24A", "Dec-25A")]
    hr += [{"FILENAME": "j.pdf", "TABLE": "P20", "ROW": 20, "ITEM": "Balance Sheet & Cash Flow Statement", "PERIOD": p_, "VALUE": p_, "_V": "ALIGNED", "_N": ""} for p_ in ("FY24A", "FY25E")]
    hr += [{"FILENAME": "g.pdf", "TABLE": "P2", "ROW": 39, "ITEM": "Jul-25 Oct-25", "PERIOD": p_, "VALUE": v_, "_V": "ALIGNED", "_N": ""} for p_, v_ in (("12/25", "Jan-26"), ("12/27E", "Apr-26"))]
    hr += [{"FILENAME": "y.pdf", "TABLE": "P3", "ROW": 2, "ITEM": "(NT$m)", "PERIOD": p_, "VALUE": v_, "_V": "ALIGNED", "_N": ""} for p_, v_ in (("2024A", "2024"), ("2025E", "2025"))]
    ok_rows = [{"FILENAME": "y.pdf", "TABLE": "P3", "ROW": 3, "ITEM": "Revenue", "PERIOD": p_, "VALUE": v_, "_V": "ALIGNED", "_N": ""} for p_, v_ in (("2024A", "2,024"), ("2025E", "2,310"))]
    ok_rows += [{"FILENAME": "y.pdf", "TABLE": "P3", "ROW": n_, "ITEM": it_, "PERIOD": "2025E", "VALUE": v_, "_V": "ALIGNED", "_N": ""}
                for n_, it_, v_ in ((4, "Net debt", "Net cash"), (5, "Margin chg", "0.4pp"), (6, "Interest cover", "NM"), (7, "Dividend", "-"), (8, "EPS", "(4.38)"))]
    hv_ = hdrval(hr + ok_rows)
    chk("v0101 HDRVAL:表頭列(值是期間字 7 · 科目是月份 2 · 整列等於年份 2)→ 全標 · 一般值(2,024 · Net cash · 0.4pp · NM · - · (4.38))不動 → %s" % dict(Counter(r["_V"] for r in hv_)),
        [r["_V"] for r in hv_[:len(hr)]] == ["HDRVAL"] * len(hr) and all(r["_V"] == "ALIGNED" for r in hv_[len(hr):]) and "HDRVAL" in BADV
        and _perv("2Q26E") and _perv("1H26") and _perv("2025CT") and not _perv("2024") and not _perv("4.38") and _peryr("Dec-24A") == "2024" and _peryr("12/25") == "2025")
    chk("兩個字詞的值:Net + cash(字距 < 4)= Net cash · 字距太大不算", len(_hits([(345, 358, "Net"), (360, 376, "cash")], "netcash")) == 1 and not _hits([(345, 358, "Net"), (380, 396, "cash")], "netcash"))
    L = [(122.0, [(232, 280, "每股盈餘成長率"), (358, 370, "76.9")]), (101.7, [(232, 260, "股價淨值比"), (280, 288, "(x)"), (358, 370, "10.4")]),
         (95.3, [(358, 370, "38.0"), (401, 413, "25.1")]), (90.7, [(232, 271, "EV/EBITDA"), (275, 288, "(x)")]),
         (84.7, [(345, 358, "Net"), (360, 376, "cash"), (406, 417, "4.5")]), (79.7, [(232, 275, "淨負債比率"), (280, 292, "(%)")]), (74.6, [])]
    def rh(k, item, v):
        lb = _lab_block(L[k][1], squash(item)[:14])
        return _row_hits(L, k, lb, squash(item), v) if lb and _lab_ok(lb[2], squash(item)) else None
    a, b_ = rh(3, "EV/EBITDA (x)", "38.0"), rh(5, "淨負債比率 (%)", "4.5")
    chk("先定列再找值:EV/EBITDA 的值在上一列(+4.6)· 淨負債比率的值在上一列(+5.0)", bool(a and a[0]) and round(a[1], 1) == 4.6 and bool(b_ and b_[0]) and round(b_[1], 1) == 5.0)
    chk("別列的值不算:淨負債比率拿 EV/EBITDA 的 38.0 · EV/EBITDA 拿淨負債比率的 4.5 · 股價淨值比拿下一列 38.0 → 都找不到",
        not (rh(5, "淨負債比率 (%)", "38.0") or (None,))[0] and not (rh(3, "EV/EBITDA (x)", "4.5") or (None,))[0] and not (rh(1, "股價淨值比 (x)", "38.0") or (None,))[0])
    chk("科目字要相同(不是只含):EPS ≠ EPS growth · Revenue ≠ Total revenue · 折行 / 原文多印單位可以",
        not _lab_ok("epsgrowth", "eps") and not _lab_ok("totalrevenue", "revenue") and _lab_ok("salesgrowthof", "salesgrowthofambusiness(%)") == "折行" and _lab_ok("revenue(nt$m)", "revenue") == "單位" and _lab_ok("revenue", "revenue") == "同")
    hq = [(175, 200, "Sep-27F"), (416, 440, "Dec-27F"), (450, 474, "Dec-26F"), (487, 511, "Dec-27F"), (524, 548, "Dec-28F")]
    a1 = _align([(700.0, hq)], 690.0, "Dec-27F", [(500.0, 495, 505, "(40)")])
    chk("季度 / 年度表頭同一個期間印兩次 → 只對年度那個 · 值在季度那欄 → 不算 · 只有季度欄 → 標季度", _qtr_x(hq) == {175, 416} and bool(a1) and a1[2] == 499.0 and
        _align([(700.0, hq)], 690.0, "Dec-27F", [(430.0, 425, 435, "-")]) is None and (_align([(700.0, hq[:2])], 690.0, "Dec-27F", [(428.0, 425, 431, "1")]) or [0] * 7)[6] is True)
    chk("值離別的期間表頭更近 → 不是這一欄(期間錯一欄)", _align([(700.0, [(400, 424, "2025A"), (440, 464, "2026E")])], 690.0, "2025A", [(445.0, 440, 450, "9")]) is None)
    W = [(500.0, [(50, 110, "Gross"), (113, 140, "profit"), (200, 220, "1,000")]), (490.0, [(50, 110, "Gross"), (113, 140, "profit"), (143, 170, "margin"), (200, 220, "33.0")]),
         (480.0, [(50, 90, "Sales"), (93, 120, "growth"), (123, 130, "of"), (200, 220, "5.0")]), (470.0, [(50, 80, "AM"), (83, 130, "business"), (133, 150, "(%)")])]
    chk("折行要真的折行:Gross profit 那列不當 Gross profit margin · Sales growth of + 下一列 AM business (%) 才算",
        not _wrap_ok(W, 0, _lab_block(W[0][1], "grossprofit"), "grossprofitmargin") and _wrap_ok(W, 2, _lab_block(W[2][1], "salesgrowthof"), "salesgrowthofambusiness(%)"))
    chk("子欄科目:Net profit 的 Net 不當值 · 科目就叫 NM 也認得 · 單列只認相同 / 單位(Gross profit ≠ Gross profit margin)",
        _sub_lab([(1.0, [(10, 20, "Net"), (22, 40, "profit"), (60, 70, "1")])], 0, 60, "netprofit")[0] and _sub_lab([(1.0, [(10, 20, "NM"), (60, 70, "1")])], 0, 60, "nm")[0]
        and not _sub_lab([(1.0, [(10, 30, "Gross"), (32, 50, "profit"), (60, 70, "1")])], 0, 60, "grossprofitmargin")[0])
    sbs = [(43, 60, "Income"), (67, 80, "tax"), (171, 190, "1,362"), (208, 225, "1,137"), (319, 340, "Change"), (344, 350, "of"), (441, 460, "1,748"), (491, 497, "0")]
    chk("並排表:科目列右邊另一張表(Change of …)的值不算這一列 · Net cash 不當成別的科目", not _hits(sbs, "0", 82, _seg_end(sbs, 80)) and len(_hits(sbs, "1,137", 82, _seg_end(sbs, 80))) == 1
        and _seg_end([(345, 358, "Net"), (360, 376, "cash"), (406, 417, "4.5"), (429, 441, "Net"), (444, 460, "cash")], 292) == 1e9)
    print("[計] %s 自測 %d/%d · %s" % (VERSION, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["--shard"]:
        _od, _pd, _in, _out = sys.argv[2:6]
        _vb, _vf, _vs = run_files(_od, _pd, json.loads(Path(_in).read_text(encoding="utf-8")))
        Path(_out).write_text(json.dumps({"basic": _vb, "fin": _vf, "summary": _vs}, ensure_ascii=False), encoding="utf-8")
        sys.exit(0)
    if sys.argv[1:2] == ["--selftest"]:
        sys.exit(selftest())
    _a = sys.argv[1:]
    _ui = _a[_a.index("--ui") + 1] if "--ui" in _a and _a.index("--ui") + 1 < len(_a) else None
    _pos = [x for i, x in enumerate(_a) if x != "--ui" and not (i > 0 and _a[i - 1] == "--ui")]
    sys.exit(main(*_pos[:3], ui=_ui))

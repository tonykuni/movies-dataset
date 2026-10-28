#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0236 — 薄尾(使用者機器第 39 輪 · 年度數據缺口):年度數據補兩種版型 ① 轉置表(年份在第一欄、科目在表頭:華南「年度 營收 毛利率(%) … 稅後 EPS」· Citi「Earnings Summary」)→ pypdfium2 每個年份一行對得上 · 各年份欄位置一致 · 表頭多行依欄界接成科目(稅前 + 純益 → 稅前純益)· 月份 / 季度表不收 ② 表頭在表外(擷取把「Year to 31 December 2023A …」切到別區:CLST · MS 右欄現金流量表)→ 往上找最近的期間表頭 · 中間的數據行要對得上同一個表頭的欄 · 每個值取 x 最近的表頭字 · 是期間且在半欄寬內才收((% YoY) 欄不收)· 兩種都要第三讀法(pdfplumber)再驗 · 不過的移剔除冊(帶理由)。
  零替換:前版函式一個都不改;前版輸出冊(v0235)整段照跑後再補(直接叫前版包裝)· vrn2 / 成功登記用同一段程式碼重新綁定 · 前版必須是 v0235 · 其餘動詞照前版鏈。
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
import importlib.util
import json
import os
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0236"
DISPLAY_NAME = "VRN-2 SystemManager"


def _vnum_v0236(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0236(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0236(p) < _vnum_v0236(__file__)), key=_vnum_v0236)
PRIOR = _load_v0236(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


# ===== 年度數據補兩種版型:A 表頭在表外(擷取把表頭切到別區)· B 轉置表(年份在第一欄 · 科目在表頭)=====
_TP_CJK = "一-鿿　-〿＀-￯"
_TP_MQ = re.compile(r"(?i)^(?:[一二三四五六七八九十]{1,3}|[1-4]Q|Q[1-4]|(?:1[0-2]|[1-9])月|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\.?$")


def _tp_join(toks: list) -> str:
    """表頭字詞接成科目名:中文 / 全形旁邊不加空白(毛利率 + (%) → 毛利率(%) · 稅前 + 純益 → 稅前純益 · Net Profit + (NT$M) → Net Profit (NT$M))。"""
    s = " ".join(t for t in toks if t)
    return re.sub(r"(?<=[%s])\s+|\s+(?=[%s])" % (_TP_CJK, _TP_CJK), "", s).strip()


def _tp_rng(tk: list, x0: float, x1: float) -> list:
    return [(a, b, t) for a, b, t in tk if x0 - 6 <= (a + b) / 2 <= x1 + 6]


def _tp_layout(lines: list, years: list, valss: list, x0: float, x1: float) -> tuple:
    """在一頁的行(由上而下)找轉置表:每個年份一行(行首 = 年份 · 後面的數值序列 = 擷取的值)· 回 (欄 x, 欄名, 第一行索引) 或 None。
    行要由上而下(pypdfium2 / pdfplumber 都是)。欄名 = 第一個數據行上方相連(間距 ≤ 數據列行距 + 2pt · 沒有數值)的表頭行 · 依欄界收字。"""
    idx = []
    for yr, vals in zip(years, valss):
        hit = []
        for k, (y, tk) in enumerate(lines):
            r = _tp_rng(tk, x0, x1)
            if r and _xv_sq(r[0][2]) == _xv_sq(yr) and [_xv_sq(t) for _, _, t in r[1:] if _SV_TOK.match(t)] == [_xv_sq(v) for v in vals]:
                hit.append(k)
        if len(hit) != 1:
            return None
        idx.append(hit[0])
    if idx != sorted(idx) or len(set(idx)) != len(idx):
        return None
    cols = []
    for k in idx:
        r = _tp_rng(lines[k][1], x0, x1)
        cols.append([(a + b) / 2 for a, b, t in r[1:] if _SV_TOK.match(t)])
    n = len(cols[0])
    if n < 1 or any(len(c) != n for c in cols):
        return None
    cx = [sorted(c[j] for c in cols)[len(cols) // 2] for j in range(n)]
    if any(abs(c[j] - cx[j]) > 10 for c in cols for j in range(n)):
        return None                                                        # 各年份的欄位置不一致 → 不收
    r0 = _tp_rng(lines[idx[0]][1], x0, x1)
    yx = (r0[0][0] + r0[0][1]) / 2
    sp = (cx[-1] - cx[0]) / max(1, n - 1) if n > 1 else 40.0
    edges = [(yx + cx[0]) / 2] + [(cx[j] + cx[j + 1]) / 2 for j in range(n - 1)] + [cx[-1] + sp / 2]
    gaps = sorted(abs(lines[idx[i + 1]][0] - lines[idx[i]][0]) for i in range(len(idx) - 1))
    lim = min(gaps[len(gaps) // 2] + 2, 24)                                # 表頭行間距上限 = 數據列行距 + 2pt(標題行離得較遠 → 不收)
    hdr, k, prev_y = [], idx[0] - 1, lines[idx[0]][0]
    while k >= 0 and len(hdr) < 6:
        y, tk = lines[k]
        r = _tp_rng(tk, x0, x1)
        if not r:                                                          # 本表範圍內沒有字的空行不算(不把間距接起來)
            k -= 1
            continue
        inner = [t for a, b, t in r if edges[0] <= (a + b) / 2 < edges[-1]]          # 年份欄的「31 Dec」不算數據
        if abs(prev_y - y) > lim or any(_SV_TOK.match(t) and re.search(r"\d", t) for t in inner) or any("::" in t or re.match(r"(?i)^(?:單位|units?\b)", t) for _, _, t in r):   # 標題 / 單位註記不是表頭
            break
        hdr.insert(0, r)
        prev_y, k = y, k - 1
    labels = [_tp_join([t for r in hdr for a, b, t in sorted(r) if edges[j] <= (a + b) / 2 < edges[j + 1]]) for j in range(n)]
    if not all(labels) or len(set(_xv_sq(l_) for l_ in labels)) != n or sum(bool(_TP_MQ.match(l_)) for l_ in labels) * 2 >= n:
        return None                                                        # 欄名缺 / 重複 / 月份季度表 → 不收
    return cx, labels, idx[0]


def _tp_table(z: dict, lines: list) -> list:
    """B 轉置表 → [(期間, 科目, 值)]:≥2 列年份開頭且有數值 · 第二讀取器(pypdfium2)每個年份一行對得上 · 欄名由表頭依欄界接出。"""
    rows = z.get("rows") or []
    yr = [rw for rw in rows if rw and _SK_ANNUAL.match((rw[0] or "").strip()) and sum(bool(_SV_TOK.match(t)) for c in rw[1:] for t in (c or "").split()) >= 2]
    if len(yr) < 2 or not z.get("bbox"):
        return []
    x0, x1 = z["bbox"][0], z["bbox"][2]
    years = [rw[0].strip() for rw in yr]
    valss = [[t for c in rw[1:] for t in (c or "").split() if _SV_TOK.match(t)] for rw in yr]
    lay = _tp_layout(lines, years, valss, x0, x1)
    if not lay:
        return []
    cx, labels, _k = lay
    rix = [rows.index(rw) + 1 for rw in yr]
    return [(yrs, labels[j], v, rn) for yrs, vals, rn in zip(years, valss, rix) for j, v in enumerate(vals)]


def _ct_table(z: dict, lines: list) -> list:
    """A 表頭在表外 → [(科目, 期間, 值)]:區內沒有期間表頭列 · 每列的數值序列在第二讀取器只有一行對得上(行首 = 科目)·
    往上找最近一行有 ≥2 個期間字樣的表頭(只看本區 x 範圍 · 600pt 內 · 中間的數據行都對得上這個表頭的欄)· 每個值取 x 最近的表頭字 · 是期間且在半欄寬內才收。"""
    rows = z.get("rows") or []
    if not z.get("bbox") or any(sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2 for rw in rows[:4]):
        return []
    if sum(bool(rw and _SK_ANNUAL.match((rw[0] or "").strip())) for rw in rows) >= 2:
        return []
    x0, x1 = z["bbox"][0], z["bbox"][2]
    out = []
    for rw in rows:
        lab = ((rw[0] if rw else "") or "").strip()
        vals = [t for c in rw[1:] for t in (c or "").split() if _SV_TOK.match(t)]
        if not lab or len(vals) < 2:
            continue
        key = _xv_sq(lab)[:8]
        want = [_xv_sq(v) for v in vals]
        hit = []
        for k, (y, tk) in enumerate(lines):
            r = _tp_rng(tk, x0, x1)
            vt = [(a, b, t) for a, b, t in r if _SV_TOK.match(t)]
            if [_xv_sq(t) for _, _, t in vt][-len(want):] == want and len(vt) == len(want) and _xv_sq("".join(t for _, _, t in r)).startswith(key):
                hit.append((k, vt))
        if len(hit) != 1:
            continue
        k, vt = hit[0]
        h = None
        for kk in range(k - 1, -1, -1):
            if abs(lines[kk][0] - lines[k][0]) > 600:
                break
            r = _tp_rng(lines[kk][1], x0, x1)
            if sum(bool(_SK_ANNUAL.match(t)) for _, _, t in r) >= 2:
                h = kk
                break
        if h is None:
            continue
        ht = _tp_rng(lines[h][1], x0, x1)
        hx = sorted(((a + b) / 2, t) for a, b, t in ht)
        ann = [x for x, t in hx if _SK_ANNUAL.match(t)]
        sp = min([ann[i + 1] - ann[i] for i in range(len(ann) - 1)] or [60])
        ok_mid = True
        for kk in range(h + 1, k):                                         # 表頭到這列之間的數據行要對得上同一個表頭的欄(不是別張表)
            mid = [(a + b) / 2 for a, b, t in _tp_rng(lines[kk][1], x0, x1) if _SV_TOK.match(t) and re.search(r"\d", t)]
            if len(mid) >= 2 and any(min(abs(m - x) for x, _ in hx) > 0.5 * sp for m in mid):
                ok_mid = False
                break
        if not ok_mid:
            continue
        got = []
        for (a, b, t), v in zip(vt, vals):
            vx = (a + b) / 2
            nx, nt = min(hx, key=lambda p_: abs(p_[0] - vx))
            if _SK_ANNUAL.match(nt) and abs(nx - vx) <= 0.5 * sp:
                got.append((lab, nt, v, rows.index(rw) + 1))
        if len({g_[1] for g_ in got}) != len(got):
            continue                                                       # 同一列兩個值落在同一期間 = 期間下有子欄(銷售金額 / 占比)→ 整列不收
        out += got
    return out


def _g3_trans(xs: list, pg, x0: float, x1: float) -> str:
    """B 轉置表過第三讀法(pdfplumber):同一張表每個年份一行對得上 · 欄名重新依欄界接出要和科目相同。回 '' = 過 · 否則理由。"""
    if not xs:
        return "空"
    per = list(dict.fromkeys(x["PERIOD"] for x in xs))
    labs = list(dict.fromkeys(x["ITEM"] for x in xs))
    vals = [[next((x["VALUE"] for x in xs if x["PERIOD"] == p and x["ITEM"] == l_), None) for l_ in labs] for p in per]
    if any(v is None for vv in vals for v in vv):
        return "表不完整"
    lay = _tp_layout(pg[0], per, vals, x0, x1)
    if not lay:
        return "pdfplumber 每個年份一行對不上 / 欄名接不出"
    if [_xv_sq(l_) for l_ in lay[1]] != [_xv_sq(l_) for l_ in labs]:
        return "欄名不同:pdfplumber 接出 %s" % " / ".join(lay[1])
    return ""


def _sec(rows: list, ri: int) -> str:
    """第 ri 列(0 起)往上找最近的段落標題列(有科目 · 其他格全空 · 不是期間表頭)· 遇到期間表頭就停。"""
    for k in range(ri - 1, -1, -1):
        rw = rows[k] or []
        if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2:
            return ""
        if rw and (rw[0] or "").strip() and len(rw) > 1 and not any((c or "").strip() for c in rw[1:]):
            return _tidy(rw[0])
    return ""


def _row_mark(res: list, fin: list) -> tuple:
    """既有年度數據每列標 ROW(表內第幾列 · 1 起)與 SECTION(段落標題:P&L / YoY (%) / 年成長率 …)· 值與科目不變。
    對法:同表 · 該列科目壓縮後前 8 字相同 · 該列在「期間」那一欄(最近的上方期間表頭)的格含此值。唯一才標。回 (標到, 標不到)。"""
    zs = {}
    for r in res:
        for pg in r.get("pages") or []:
            for z in pg.get("zones") or []:
                zs[(r.get("file"), z.get("id"))] = z.get("rows") or []
    ok = miss = 0
    hdr_cache = {}
    for x in fin:
        if x.get("ROW"):
            ok += 1
            continue
        rows = zs.get((x["FILENAME"], x.get("TABLE")))
        if not rows:
            miss += 1
            continue
        key = (x["FILENAME"], x.get("TABLE"))
        if key not in hdr_cache:
            hdr, cur = [], None
            for rw in rows:
                if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2:
                    cur = [(c or "").strip() for c in rw]
                hdr.append(cur)
            hdr_cache[key] = hdr
        hdr = hdr_cache[key]
        k8 = _xv_sq(x.get("ITEM_RAW") or x.get("ITEM", ""))[:8]
        sv = _xv_sq(x.get("VALUE", ""))
        cand = []
        for ri, rw in enumerate(rows):
            h = hdr[ri]
            if not h or not rw or not k8 or k8 not in _xv_sq(rw[0] or "") and _xv_sq(rw[0] or "")[:8] not in _xv_sq(x.get("ITEM", "")):
                continue
            for j, c in enumerate(rw[1:], 1):
                if j < len(h) and h[j] == x.get("PERIOD") and sv in [_xv_sq(t) for t in (c or "").split()] + [_xv_sq(c or "")]:
                    cand.append(ri)
                    break
        cand = sorted(set(cand))
        if len(cand) > 1:                                                  # 「稅前純益」/「稅前純益率」前 8 字相同 → 取科目完全相同的那一列
            ex = [ri for ri in cand if _xv_sq(rows[ri][0] or "") == _xv_sq(x.get("ITEM_RAW") or x.get("ITEM", ""))]
            cand = ex if len(ex) == 1 else cand
        if len(cand) == 1:
            x["ROW"], x["SECTION"] = cand[0] + 1, _sec(rows, cand[0])
            ok += 1
        else:
            miss += 1
    return ok, miss


_QM = re.compile(r"(?i)^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2})[AEFP]?$")
_QMN = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def _qtr_cols(hdr: list) -> set:
    """表頭裡「月-年」期間(Mar-26A …)· 相鄰兩欄差 3 個月連成一段 = 季度欄(回欄號)· 差 12 個月(Dec-25A → Dec-26F)= 年度欄 · 九月制年度(Sep-24A → Sep-25E)也是年度。"""
    pos = []
    for j, c in enumerate(hdr or []):
        m = _QM.match((c or "").strip())
        if m:
            pos.append((j, int(m.group(2)) * 12 + _QMN[m.group(1).lower()]))
    q = set()
    for (j1, m1), (j2, m2) in zip(pos, pos[1:]):
        if m2 - m1 == 3:
            q.update((j1, j2))
    return q


def _drop_qtr(res: list, fin: list) -> tuple:
    """年度數據裡的季度值(表頭月份每 3 個月一欄)→ 移剔除冊。看該列(ROW)在哪一欄找到這個值:找到的欄全是季度欄才剔(年度欄也找得到就留)。回 (留下, 剔除)。"""
    zs = {}
    for r in res:
        for pg in r.get("pages") or []:
            for z in pg.get("zones") or []:
                zs[(r.get("file"), z.get("id"))] = z.get("rows") or []
    keep, rej = [], []
    for x in fin:
        if not _QM.match(str(x.get("PERIOD", ""))) or x.get("SUBCOL"):
            keep.append(x)
            continue
        rows = zs.get((x["FILENAME"], x.get("TABLE"))) or []
        if not x.get("ROW"):                                               # 沒標到列:這個期間在本表所有表頭只出現在季度欄 → 季度
            hs = [rw for rw in rows if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2]
            at = [(j in _qtr_cols(h)) for h in hs for j, c in enumerate(h) if j and (c or "").strip() == x["PERIOD"]]
            if at and all(at):
                rej.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON="季度欄(表頭月份每 3 個月一欄 · 不是年度)· 不進年度數據"))
            else:
                keep.append(x)
            continue
        ri = int(x["ROW"]) - 1
        hdr = next((rows[k] for k in range(min(ri, len(rows) - 1), -1, -1) if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rows[k][1:]) >= 2), None)
        if not hdr or ri >= len(rows):
            keep.append(x)
            continue
        q = _qtr_cols(hdr)
        sv = _xv_sq(x.get("VALUE", ""))
        js = [j for j, c in enumerate(rows[ri]) if j and j < len(hdr) and (hdr[j] or "").strip() == x["PERIOD"] and sv in [_xv_sq(t) for t in (c or "").split()] + [_xv_sq(c or "")]]
        if js and all(j in q for j in js):
            rej.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON="季度欄(表頭月份每 3 個月一欄 · 不是年度)· 不進年度數據"))
        else:
            keep.append(x)
    return keep, rej


def _more_fin(res: list, basic: list, fin: list, v2: Path) -> tuple:
    """A + B 兩種版型補年度數據(第二讀取器 pypdfium2 對欄 → 第三讀法 pdfplumber 再驗)· 已有的(同檔 · 表 · 科目 · 期間)不重複。回 (留下, 剔除, 統計)。"""
    from collections import Counter
    have = {(x["FILENAME"], x.get("TABLE"), x.get("ITEM"), x.get("PERIOD")) for x in fin}
    bmeta = {b["FILENAME"]: b for b in basic}
    keep, rej, stat, cache = [], [], Counter(), {}
    for r in res:
        f = r.get("file")
        if f not in bmeta:
            continue
        pdf = _out_pdf(f, v2)
        if not pdf.exists():
            continue
        base0 = {k_: bmeta[f].get(k_, "") for k_ in ("REPORT_DATE", "FILENAME", "TICKER", "BROKER")}
        for pg in r.get("pages") or []:
            pno = int(pg.get("pno") or 0)
            for z in pg.get("zones") or []:
                if z.get("minor") != "TB":
                    continue
                lines = None
                tp = []
                if sum(bool(rw and _SK_ANNUAL.match((rw[0] or "").strip())) for rw in z.get("rows") or []) >= 2:
                    lines = _xv_lines(pdf, pno, cache)
                    tp = _tp_table(z, lines)
                if tp:
                    xs = [dict(base0, PAGE=pno, TABLE=z.get("id"), ITEM=_tidy(it), PERIOD=pe, VALUE=v, ROW=rn, SECTION="", VERIFY="年度列表(轉置 · pypdfium2 對欄)") for pe, it, v, rn in tp]
                    xs = [x for x in xs if (x["FILENAME"], x["TABLE"], x["ITEM"], x["PERIOD"]) not in have]
                    g = _g3_page(pdf, pno)
                    why = "閘不可用" if g is None else _g3_trans(xs, g, z["bbox"][0], z["bbox"][2])
                    for x in xs:
                        if why:
                            rej.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON="轉置表第三讀法(pdfplumber)對不上 · " + why))
                        else:
                            keep.append(dict(x, VERIFY=x["VERIFY"] + " · pdfplumber 再驗"))
                    stat["轉置過" if not why else "轉置剔除"] += len(xs)
                    continue
                if "財報" not in str(z.get("minor_zh", "")):
                    continue
                lines = lines or _xv_lines(pdf, pno, cache)
                ct = _ct_table(z, lines)
                if not ct:
                    continue
                g = _g3_page(pdf, pno)
                for it, pe, v, rn in ct:
                    x = dict(base0, PAGE=pno, TABLE=z.get("id"), ITEM=_tidy(it), PERIOD=pe, VALUE=v, ROW=rn, SECTION=_sec(z.get("rows") or [], rn - 1), VERIFY="對欄(pypdfium2 · 表頭在表外)")
                    if (x["FILENAME"], x["TABLE"], x["ITEM"], x["PERIOD"]) in have:
                        continue
                    vd = "閘不可用" if g is None else ("ALIGNED" if _g3_item_ok(x["ITEM"], g) and _g3_aligned(x, g) == "ALIGNED" else "不對")
                    if vd == "ALIGNED":
                        keep.append(dict(x, VERIFY=x["VERIFY"] + " · pdfplumber 再驗"))
                        stat["表頭在表外過"] += 1
                    else:
                        rej.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON="表頭在表外 · 第三讀法(pdfplumber)對不到期間欄 / 科目"))
                        stat["表頭在表外剔除"] += 1
    return keep, rej, stat


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0236 = v0235 輸出冊 + 年度數據兩種版型(A 表頭在表外 · B 轉置表)· 兩個讀取器都對得上才進主冊 · 不過的進剔除冊(帶理由)。"""
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)   # 直接叫前版包裝(不 rebind 包裝 → 不遞迴)
    n_ok, n_miss = _row_mark(res, fin)
    fin, rq = _drop_qtr(res, fin)
    add, rj, stat = _more_fin(res, basic, fin, v2)
    if True:                                                               # 本版一律重寫(ROW / SECTION 欄)
        fin = fin + add
        rej = list(_XV_LAST.get("rej") or []) + rq + rj
        od = v2 / "output"
        made = [m_ for m_ in made if not m_.startswith(("FinancialData(", "Rejected("))]
        made = [_write_book(od, "FinancialData", fin)] + made + [_write_book(od, "Rejected", rej)]
        _XV_LAST["rej"] = rej
        nf = {x["FILENAME"] for x in fin}
        g2 = []
        for g_ in gaps:                                                    # 缺項「年度數據」補到了 → 拿掉這一項(其他缺項照留)
            nm, _, its = g_.partition(":")
            its_ = [i_ for i_ in its.split("、") if i_ and not (i_ == "年度數據" and any(f_.startswith(nm) for f_ in nf))]
            if its_:
                g2.append("%s:%s" % (nm, "、".join(its_)))
        gaps = g2
    it = _XV_LAST.get("item")
    if it:
        _XV_LAST["item"] = (it[0], it[1], it[2] + " · v0236 年度數據補版型:轉置表 過 %d / 剔除 %d · 表頭在表外 過 %d / 剔除 %d · 季度欄移出年度數據 %d · 表內列號 / 段落標到 %d / 標不到 %d" % (stat["轉置過"], stat["轉置剔除"], stat["表頭在表外過"], stat["表頭在表外剔除"], len(rq), n_ok, n_miss))
    st_ = _stale_parquet(v2 / "output")
    if st_:
        made = made + ["Parquet 舊檔 %d 個移到 output/_stale(本輪沒寫 Parquet · 避免讀到舊值)" % len(st_)]
    return basic, fin, summ, gaps, made


vrn2 = _rebind(PRIOR.vrn2)                                                # 同一段 vrn2(v0231 程式碼)· 用到本版 _out_books
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0236)


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
    td = Path(tempfile.mkdtemp(prefix="v0236-"))
    (td / "scope_in").mkdir()
    pdf = td / "scope_in" / "TP-3231 20260101.pdf"
    ok_pdf = False
    try:
        from reportlab.pdfgen import canvas as _cv
        cv = _cv.Canvas(str(pdf), pagesize=(595, 842))
        cv.setFont("Helvetica", 9)
        put = lambda x, y, t: cv.drawString(x, y, t)                       # noqa: E731
        for x, t in ((50, "Year to"), (110, "Net Profit"), (200, "Diluted EPS"), (305, "P/E")):
            put(x, 720, t)
        for x, t in ((50, "31 Dec"), (115, "(NT$M)"), (210, "(NT$)"), (308, "(x)")):
            put(x, 708, t)
        for y, row in ((694, ("2023A", "11,472", "4.09", "27.9")), (680, ("2024A", "17,446", "6.12", "18.6")), (666, ("2025E", "24,878", "8.72", "13.1"))):
            for x, t in zip((50, 118, 215, 308), row):
                put(x, y, t)
        for x, t in ((50, "Year"), (120, "Jan"), (160, "Feb"), (200, "Mar")):
            put(x, 610, t)
        for y, row in ((596, ("2025", "68.0", "80.2", "85.1")), (582, ("2026", "157.0", "159.0", "160.7"))):
            for x, t in zip((50, 120, 160, 200), row):
                put(x, y, t)
        for x, t in ((50, "Year to 31 December"), (200, "2024A"), (260, "2025E"), (318, "(% YoY)"), (380, "2026E")):
            put(x, 520, t)
        put(50, 506, "Profit & Loss (NT$m)")
        for y, row in ((492, ("Revenue", "100", "200", "50.0", "300")), (478, ("Net profit", "10", "20", "100.0", "30"))):
            for x, t in zip((50, 205, 265, 325, 385), row):
                put(x, y, t)
        put(50, 420, "Year")
        put(200, 420, "2023")
        put(330, 420, "2024")
        for x, t in ((50, "Region"), (180, "Sales"), (225, "Share"), (310, "Sales"), (355, "Share")):
            put(x, 408, t)
        for x, t in ((50, "Asia"), (180, "514.4"), (225, "86.9%"), (310, "621.4"), (355, "86.6%")):
            put(x, 394, t)
        cv.save()
        ok_pdf = True
    except Exception as e:  # noqa: BLE001
        print("  [計] 自測 PDF 產生不了(%s)→ 版型自測判紅" % type(e).__name__)
    if ok_pdf:
        zt = {"id": "P1·M·06·TB", "minor": "TB", "minor_zh": "表格", "bbox": [45, 842 - 728, 360, 842 - 660],
              "rows": [["Year to", "Net Profit", "Diluted EPS", "P/E"], ["31 Dec", "(NT$M)", "(NT$)", "(x)"], ["2023A", "11,472", "4.09", "27.9"],
                       ["2024A", "17,446", "6.12", "18.6"], ["2025E", "24,878", "8.72", "13.1"]]}
        zm = {"id": "P1·M·07·TB", "minor": "TB", "minor_zh": "財報表", "bbox": [45, 842 - 618, 240, 842 - 578],
              "rows": [["Year", "Jan", "Feb", "Mar"], ["2025", "68.0", "80.2", "85.1"], ["2026", "157.0", "159.0", "160.7"]]}
        zc = {"id": "P1·F·03·TB", "minor": "TB", "minor_zh": "財報表", "bbox": [45, 842 - 512, 420, 842 - 472],
              "rows": [["Profit & Loss (NT$m)"], ["Revenue", "100", "200", "50.0", "300"], ["Net profit", "10", "20", "100.0", "30"]]}
        zs = {"id": "P1·F·05·TB", "minor": "TB", "minor_zh": "財報表", "bbox": [45, 842 - 400, 400, 842 - 390], "rows": [["Asia", "514.4", "86.9%", "621.4", "86.6%"]]}
        res = [{"file": pdf.name, "pages": [{"pno": 1, "zones": [zt, zm, zc, zs]}]}]
        basic = [{"FILENAME": pdf.name, "REPORT_DATE": "2026-01-01", "TICKER": "3231", "BROKER": "T"}]
        kp, rj, stt = _more_fin(res, basic, [], td)
        tv = sorted((x["ITEM"], x["PERIOD"], x["VALUE"]) for x in kp if x["TABLE"] == "P1·M·06·TB")
        chk("⓪ v0236 轉置表:年份在第一欄 · 兩行表頭接成科目 → %d 筆 · %s" % (len(tv), sorted({i for i, _, _ in tv})),
            len(tv) == 9 and ("Net Profit (NT$M)", "2024A", "17,446") in tv and ("Diluted EPS (NT$)", "2025E", "8.72") in tv and ("P/E (x)", "2023A", "27.9") in tv
            and all("轉置" in x["VERIFY"] and "pdfplumber 再驗" in x["VERIFY"] for x in kp if x["TABLE"] == "P1·M·06·TB"))
        chk("⓪ v0236 月份表(Jan / Feb / Mar · 年份在第一欄)不當年度數據", not [x for x in kp + rj if x["TABLE"] == "P1·M·07·TB"])
        cv_ = sorted((x["ITEM"], x["PERIOD"], x["VALUE"]) for x in kp if x["TABLE"] == "P1·F·03·TB")
        chk("⓪ v0236 表頭在表外:往上找期間表頭 · (%% YoY) 欄不收 → %s" % cv_,
            cv_ == sorted([("Revenue", "2024A", "100"), ("Revenue", "2025E", "200"), ("Revenue", "2026E", "300"),
                           ("Net profit", "2024A", "10"), ("Net profit", "2025E", "20"), ("Net profit", "2026E", "30")]) and stt["表頭在表外剔除"] == 0)
        chk("⓪ v0236 期間下有子欄(Sales / Share)· 同一列兩個值落在同一期間 → 整列不收", not [x for x in kp + rj if x["TABLE"] == "P1·F·05·TB"])
        zr = {"id": "T9", "rows": [["", "2026E", "2027E"], ["P&L", "", ""], ["Revenue", "100", "200"], ["YoY (%)", "", ""], ["Revenue", "10%", "20%"]]}
        fr = [{"FILENAME": "a.pdf", "TABLE": "T9", "ITEM": "Revenue", "PERIOD": "2026E", "VALUE": "100"}, {"FILENAME": "a.pdf", "TABLE": "T9", "ITEM": "Revenue", "PERIOD": "2026E", "VALUE": "10%"}]
        rm = _row_mark([{"file": "a.pdf", "pages": [{"pno": 1, "zones": [zr]}]}], fr)
        chk("⓪ v0236 同一張表同名科目分在不同段落 → 標 ROW / SECTION(值與科目不變)→ %s" % [(x.get("ROW"), x.get("SECTION")) for x in fr],
            rm == (2, 0) and [(x["ROW"], x["SECTION"]) for x in fr] == [(3, "P&L"), (5, "YoY (%)")] and [x["ITEM"] for x in fr] == ["Revenue", "Revenue"])
        hq = ["", "Mar-25A", "Jun-25A", "Sep-25A", "Dec-25A", "Mar-26A", "Jun-26A", "Sep-26F", "Dec-26F", "Dec-25A", "Dec-26F", "Dec-27F"]
        chk("⓪ v0236 季度欄判定:每 3 個月一欄 → 季度 %s · 每 12 個月 → 年度 · 九月制年度(Sep-24A → Sep-25E)→ 年度" % sorted(_qtr_cols(hq)),
            sorted(_qtr_cols(hq)) == list(range(1, 9)) and not _qtr_cols(["", "Sep-24A", "Sep-25E", "Sep-26E"]))
        zq = {"id": "TQ", "rows": [hq, ["營業收入", "1", "2", "3", "4", "5", "6", "7", "6,106", "16,896", "22,021", "25,000"]]}
        fq = [{"FILENAME": "a.pdf", "TABLE": "TQ", "ITEM": "營業收入", "PERIOD": "Dec-26F", "VALUE": "6,106", "ROW": 2},
              {"FILENAME": "a.pdf", "TABLE": "TQ", "ITEM": "營業收入", "PERIOD": "Dec-26F", "VALUE": "22,021", "ROW": 2},
              {"FILENAME": "a.pdf", "TABLE": "TQ", "ITEM": "營業收入", "PERIOD": "Mar-26A", "VALUE": "5", "ROW": 2}]
        kq, rq_ = _drop_qtr([{"file": "a.pdf", "pages": [{"pno": 1, "zones": [zq]}]}], fq)
        chk("⓪ v0236 季度值(Dec-26F 季 6,106 · Mar-26A 5)移出年度數據 · 年度 Dec-26F 22,021 留下", [x["VALUE"] for x in kq] == ["22,021"] and sorted(x["VALUE"] for x in rq_) == ["5", "6,106"])
        g = _g3_page(pdf, 1)
        bad = [dict(x, ITEM=("EPS (NT$)" if x["ITEM"] == "Diluted EPS (NT$)" else x["ITEM"])) for x in kp if x["TABLE"] == "P1·M·06·TB"]
        why = _g3_trans(bad, g, 45, 360)
        chk("⓪ v0236 轉置表科目被改(Diluted EPS → EPS)→ 第三讀法擋下:%s" % why[:40], bool(why) and not _g3_trans([x for x in kp if x["TABLE"] == "P1·M·06·TB"], g, 45, 360))
    else:
        chk("⓪ v0236 版型自測(需 reportlab 產生測試 PDF)", False)
    chk("⓪ v0236 前版必須是 v0235 → %s" % getattr(PRIOR, "TAG", "?"), getattr(PRIOR, "TAG", "") == "v0235")
    chk("⓪ v0236 零替換:vrn2 是同一段程式(重新綁定)", vrn2.__code__ is PRIOR.vrn2.__code__ and vrn2.__globals__ is globals())
    try:
        _ob = _out_books([], [], [], td)
        _ob_err = ""
    except BaseException as e:  # noqa: BLE001 — 自測要把遞迴 / 例外當紅燈報出
        _ob, _ob_err = (), type(e).__name__
    chk("⓪ v0236 輸出冊(本版 → v0235 → … → v0232)空輸入跑完不遞迴 %s" % (_ob_err or "· 回傳 %d 項" % len(_ob)), not _ob_err and len(_ob) == 5)
    try:
        _cm = completion(0, 1, 1, True, {}, []).get("manager")
    except Exception as e:  # noqa: BLE001
        _cm = "例外 %s" % type(e).__name__
    chk("⓪ v0236 完成判定的管理器欄 = 實際尾版 → %s" % _cm, _cm == "VRN-2 SystemManager v0236")
    print("  ── 前版 v0235 自測(原樣)──")
    rc_p = PRIOR.selftest()
    chk("⓪ 前版 %s 自測 rc %d" % (PRIOR_PATH.name, rc_p), rc_p == 0)
    print("[計] %s %s(%s)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, Path(__file__).name, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

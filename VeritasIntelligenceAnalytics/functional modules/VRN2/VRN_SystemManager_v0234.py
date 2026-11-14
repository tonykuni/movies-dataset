#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0234 — 薄尾(補回剔除冊裡能驗證的值):① 一格多值(修正前 / 後 / 差異 · GS Old/New/Diff · 共識比較 · 季度)→ 依第二讀取器 pypdfium2 的 x 位置拆成「期間 + 子欄(SUBCOL)」;條件全過才拆:有子表頭列 · 表頭期間字樣兩條讀法相同 · 該列整列數值序列兩條讀法相同(第二讀取器整段只有一列對得上)· 每個值一對一對到最近的子欄標籤 · 期間分組:季度依年份 / 其他依子表頭切組(組內標籤不重複 · 期間表頭落在組內 · 置中且唯一)· 遇到下一個表頭就停 · 擷取引擎把值分錯期間時整列每格都是多值才依子表頭更正(VERIFY 標「擷取分組更正」)· 不合的照舊留剔除冊 ② 電話第三讀取器:首頁區塊讀法對不上時,pypdfium2 與 PyMuPDF 兩個獨立讀取器讀到同一支 → 輸出(另收「(886) 2 …」「886.2.…」寫法 · 沒有 PyMuPDF 規則不變)③ 寫不出 Parquet 時上一輪的 Parquet 移到 output/_stale(不冒充本輪)④ U/I 子欄拆分總表 ⑤ 完成判定的管理器欄寫實際尾版。
  零替換:前版函式一個都不改;前版輸出冊(v0233)整段照跑後再補(直接叫前版包裝 · 不再 rebind 包裝 → 不遞迴)· vrn2 / 成功登記用同一段程式碼重新綁定 · 前版必須是 v0233 · 其餘動詞照前版鏈。
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
TAG = "v0234"
DISPLAY_NAME = "VRN-2 SystemManager"


def _vnum_v0234(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0234(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0234(p) < _vnum_v0234(__file__)), key=_vnum_v0234)
PRIOR = _load_v0234(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


# ===== ① 一格多值 → 子欄拆分(第二讀取器依 x 位置對位 · 兩條讀法數值序列相同才拆)=====
_SV_TOK = re.compile(r"(?i)^(?:\(?-?\d[\d,]*\.?\d*\)?%?|\(?-?\.\d+\)?%?|\d+(?:\.\d+)?pp|n\.?a\.?|n/a|nm|n\.m\.|[-–—]+)$")


def _sv_find(lines: list, start: int, pred, stop: int = None) -> int:
    for k in range(start, min(len(lines), stop if stop is not None else len(lines))):
        if pred(lines[k]):
            return k
    return -1


def _sv_year(t: str):
    m = re.search(r"(?:FY|^|[-/])(?:19|20)?(\d{2})(?:[AEFPe]|\([AEFP]\))?$", t.strip()) or re.match(r"^[1-4]Q(\d{2})", t.strip())
    return int(m.group(1)) if m else None


_SV_REGROUP = set()                                                       # (id(表), 列號, 欄號):擷取引擎把值分錯期間 · 依子表頭更正過的格


def _sv_partition(st_all: list, hx: list):
    """子表頭標籤(依 x)切成 len(hx) 段連續的組:每組不可有重複標籤 · 期間表頭中心要落在組的範圍內 · 取組中心離表頭最近的切法;
    第二好的切法差不到 4pt(分不出來)→ None(不拆)。回 [組號 for 每個標籤]。"""
    n, m = len(hx), len(st_all)
    if n < 1 or m < n:
        return None
    best = []
    from itertools import combinations
    for cuts in combinations(range(1, m), n - 1):
        ed = (0,) + cuts + (m,)
        cost, ok = 0.0, True
        for k in range(n):
            g = st_all[ed[k]:ed[k + 1]]
            names = [_xv_sq(t) for _, _, t in g]
            x0, x1 = g[0][0], g[-1][1]
            if len(set(names)) != len(names) or not (x0 - 2 <= hx[k] <= x1 + 2):
                ok = False
                break
            cost += abs((x0 + x1) / 2 - hx[k])
        if ok:
            best.append((cost, ed))
    if not best:
        return None
    best.sort()
    if len(best) > 1 and best[1][0] - best[0][0] < 4.0:
        return None
    ed = best[0][1]
    return [k for k in range(n) for _ in range(ed[k], ed[k + 1])]


def _sv_split_table(z: dict, lines: list) -> dict:
    """一張表:{(列號, 欄號): [(子欄標籤, 值), …]}。條件全過才拆:有子表頭列 · 第二讀取器找得到表頭列(期間字樣完全相同)·
    該列兩條讀法數值序列相同(第二讀取器整頁只有一列對得上)· 每個值對到最近的子欄標籤(一對一)·
    期間分組:子欄是季度 → 依季度年份;其他 → 子表頭切組(_sv_partition:組內不重複標籤 · 表頭落在組內 · 置中且唯一)。
    依子表頭的分組 ≠ 擷取引擎的格時:該列每個期間格都要是一格多值才改(更正記在 _SV_REGROUP),否則不拆。"""
    rows = z.get("rows") or []
    hdr = next(((i, rw) for i, rw in enumerate(rows[:4]) if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2), None)
    if not hdr or not lines or hdr[0] + 1 >= len(rows):
        return {}
    hi, hrow = hdr
    sub = rows[hi + 1]
    if any(re.search(r"\d", c or "") and not all(_XV_PER.match(t) for t in (c or "").split()) for c in sub[1:]):
        return {}                                                          # 沒有子表頭列(數據列)→ 不拆
    pers = [(j, (c or "").strip()) for j, c in enumerate(hrow) if j and _SK_ANNUAL.match((c or "").strip())]
    want = [p for _, p in pers]
    hl = _sv_find(lines, 0, lambda L: [t for _, _, t in L[1] if _SK_ANNUAL.match(t)] == want)
    if hl < 0:
        return {}
    hx = [next((a + b) / 2 for a, b, t in lines[hl][1] if t == p) for p in want]
    if any(hx[i] >= hx[i + 1] for i in range(len(hx) - 1)):
        return {}
    gap = (hx[-1] - hx[0]) / max(1, len(hx) - 1) if len(hx) > 1 else 80.0
    lo, hi_x = hx[0] - gap, hx[-1] + gap
    subq = "|".join(_xv_sq(c) for c in sub[1:] if c)                    # 擷取引擎的子表頭(中文常黏在一起:「修正後修正前調幅 (%)」→ 用子字串比)
    sl = _sv_find(lines, hl + 1, lambda L: sum(len(_xv_sq(t)) >= 2 and _xv_sq(t) in subq for _, _, t in L[1]) >= 2, hl + 4)
    st_all = []
    for a, b, t in (lines[sl][1] if sl >= 0 else []):
        if not (lo <= (a + b) / 2 < hi_x) or _xv_sq(t) not in subq:
            continue                                                       # 只收子表頭欄的字(科目欄的「百萬元」不算子欄)
        if st_all and re.fullmatch(r"\(?%\)?|\(\s*%\s*\)|\)", t):
            pa, pb, pt = st_all[-1]
            st_all[-1] = (pa, b, pt + " " + t)
        else:
            st_all.append((a, b, t))
    if not st_all:
        return {}
    quarterly = all(_XV_PER.match(t) and re.match(r"^[1-4]Q", t) for _, _, t in st_all)
    yrs = [_sv_year(p) for p in want]
    if quarterly:
        lab_g = [next((k for k, y in enumerate(yrs) if y is not None and y == _sv_year(t)), None) for _, _, t in st_all]
        if None in lab_g:
            return {}
    else:
        lab_g = _sv_partition(st_all, hx)
        if lab_g is None:
            return {}
    lcx = [(a + b) / 2 for a, b, _ in st_all]
    seqs = [[(a, b, t) for a, b, t in L[1] if lo <= (a + b) / 2 < hi_x and _SV_TOK.match(t)] for L in lines]
    k0 = max(hl, sl) + 1
    k1 = next((k for k in range(k0, len(lines)) if len(lines[k][1]) >= 2 and all(_XV_PER.match(t) for _, _, t in lines[k][1])), len(lines))
    out = {}
    for ri in range(hi + 2, len(rows)):
        rw = rows[ri]
        item = ((rw[0] if rw else "") or "").strip()
        if not item and sum(bool(_XV_PER.match((c or "").strip())) for c in rw[1:]) >= 2:
            break                                                          # 下一個表頭(同一張表下半段換期間:2Q26E …)→ 停
        cells = {j: (rw[j] if j < len(rw) else "") or "" for j, _ in pers}
        ctok = {j: [t for t in c.split() if _SV_TOK.match(t)] for j, c in cells.items()}
        multi = [j for j in ctok if len(ctok[j]) >= 2]
        if not item or not multi:
            continue
        want_seq = [_xv_sq(t) for j, _ in pers for t in ctok[j]]
        cand = [k for k in range(k0, k1) if [_xv_sq(t) for _, _, t in seqs[k]] == want_seq]
        if len(cand) != 1:
            continue                                                       # 兩條讀法數值序列對不上 / 整頁有兩列一樣(分不出)→ 不拆
        toks = seqs[cand[0]]
        li = [min(range(len(st_all)), key=lambda i_: abs(lcx[i_] - (a + b) / 2)) for a, b, _ in toks]
        if len(set(li)) != len(li) or li != sorted(li):
            continue                                                       # 兩個值搶同一個子欄 / 順序亂 → 不拆
        groups = {gi: [] for gi in range(len(pers))}
        for (a, b, t), i_ in zip(toks, li):
            groups[lab_g[i_]].append((st_all[i_][2], t))
        moved = any([_xv_sq(t) for _, t in groups[gi]] != [_xv_sq(t) for t in ctok[j]] for gi, (j, _) in enumerate(pers))
        if moved and (any(len(ctok[j]) < 2 for j, _ in pers) or any(not groups[gi] for gi in range(len(pers)))):
            continue                                                       # 要更正分組但有格不是一格多值(已單獨輸出)→ 不拆
        for gi, (j, p) in enumerate(pers):
            if j not in multi or not groups[gi]:
                continue
            out[(ri, j)] = list(groups[gi])
            if moved:
                _SV_REGROUP.add((id(z), ri, j))
    return out


def _write_book(od: Path, name: str, rows_: list) -> str:
    """與 v0231 同格式寫一本冊(JSON + CSV + Parquet 若有 pyarrow)。"""
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
        return "%s(%d 列 · JSON / CSV / Parquet)" % (name, len(rows_))
    except Exception:  # noqa: BLE001
        return "%s(%d 列 · JSON / CSV)" % (name, len(rows_))


_TEL3 = re.compile(_BI_TEL.pattern + r"|\(886\)\s?\d{1,2}\s\d{4}\s\d{4}(?!\d)|(?<![\d.])886\.\d{1,2}\.\d{4}\.\d{4}(?![\d.])")
# 第三讀取器另收兩種國際寫法:Daiwa「(886) 2 8758 6254」· 凱基「886.2.2181.8729」(v0231 首頁規則不動)


def _tel_third(pdf: Path) -> list:
    """② 電話第三讀取器:pypdfium2 與 PyMuPDF 兩個獨立讀取器都讀到同一支號碼 → 照 pypdfium2 原樣輸出(沒有 PyMuPDF → 空 · 規則不變)。"""
    try:
        import fitz  # noqa: WPS433
        with fitz.open(str(pdf)) as d:
            tc = d[0].get_text() if len(d) else ""
    except Exception:  # noqa: BLE001
        return []
    tb = _acc_pdfium_text(Path(pdf), [1]).get(1, "")
    def tels(t):
        t = _bi_norm2(t.replace("\r\n", "\n"))
        return [(m.group(0).strip(), re.sub(r"\D", "", m.group(0))[-8:]) for m in _TEL3.finditer(t) if len(re.sub(r"\D", "", m.group(0))) >= 8]
    c = {d_ for _, d_ in tels(tc)}
    return list(dict.fromkeys(s for s, d_ in tels(tb) if d_ in c))


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0234 = v0233 輸出冊 + 補強(都要第二讀取器對位 / 兩個獨立讀取器一致才收):
    ① 一格多值(修正前 / 後 / 差異 · 季度)→ 依 pypdfium2 x 位置拆成「期間 + 子欄」· 兩條讀法數值序列相同才拆 · 不同的照舊留剔除冊;
    ② TEL:首頁區塊讀法對不上時,pypdfium2 + PyMuPDF 兩個獨立讀取器都讀到 → 輸出。"""
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)   # 直接叫前版(v0233 包裝自己會再叫 v0232 · 不可再 rebind → 遞迴)
    rej = list(_XV_LAST.get("rej") or [])
    byf = {r.get("file"): r for r in res}
    cache, split_n, used = {}, 0, set()
    multi = [x for x in rej if x.get("BOOK") == "FinancialData" and str(x.get("REASON", "")).startswith("一格多值")]
    for f, tid in sorted({(x["FILENAME"], x["TABLE"]) for x in multi}):
        r = byf.get(f) or {}
        z, pno = next(((z_, pg.get("pno")) for pg in r.get("pages") or [] for z_ in pg.get("zones") or [] if z_.get("id") == tid), (None, None))
        pdf = _out_pdf(f, v2)
        if not z or not pdf.exists():
            continue
        sp = _sv_split_table(z, _xv_lines(pdf, int(pno or 1), cache))
        if not sp:
            continue
        rows = z.get("rows") or []
        hrow = next(rw for rw in rows[:4] if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2)
        for (ri, j), pairs in sorted(sp.items()):
            item = ((rows[ri][0] if rows[ri] else "") or "").strip()
            per = (hrow[j] or "").strip()
            hit = [x for x in multi if x["FILENAME"] == f and x["TABLE"] == tid and x["PERIOD"] == per and (x.get("ITEM_RAW") or x.get("ITEM")) == item]
            if not hit or any(id(x) in used for x in hit):
                continue                                                   # 沒有對應的剔除列 / 同一格已拆過(同名科目兩列)→ 不重複輸出
            base = {k_: v_ for k_, v_ in hit[0].items() if k_ not in ("BOOK", "REASON", "VALUE", "PERIOD")}
            fix = " · 擷取分組更正(依子表頭)" if (id(z), ri, j) in _SV_REGROUP else ""
            for lab, val in pairs:
                fin.append(dict(base, PERIOD=per, SUBCOL=lab, VALUE=val, VERIFY="子欄對位(pypdfium2 · 兩條讀法數值序列相同)" + fix + (" · 空值記號" if _XV_NIL.match(val) else "")))
                split_n += 1
            used.update(id(x) for x in hit)
    rej2 = [x for x in rej if id(x) not in used]
    tel_n = 0
    for row in basic:
        if row.get("TEL"):
            continue
        pdf = _out_pdf(row["FILENAME"], v2)
        t3 = _tel_third(pdf) if pdf.exists() else []
        if t3:
            row["TEL"] = "、".join(t3)
            row["_STATUS"]["TEL"] = "VERIFIED(pypdfium2 + PyMuPDF 兩個獨立讀取器)"
            tel_n += 1
    if split_n or tel_n:
        od = v2 / "output"
        made = [m_ for m_ in made if not m_.startswith(("FinancialData(", "Rejected(", "BasicInfo("))]
        made = [_write_book(od, "BasicInfo", basic), _write_book(od, "FinancialData", fin)] + made + [_write_book(od, "Rejected", rej2)]
        _XV_LAST["rej"] = rej2
        it = _XV_LAST.get("item")
        if it:
            lamp = "GREEN" if not rej2 else "YELLOW"
            _XV_LAST["item"] = (it[0], lamp, it[2] + " · v0234 子欄拆分 %d 筆(對位驗證 · 剔除剩 %d)· 電話第三讀取器補 %d 份" % (split_n, len(rej2), tel_n))
    st_ = _stale_parquet(v2 / "output")
    if st_:
        made = made + ["Parquet 舊檔 %d 個移到 output/_stale(本輪沒寫 Parquet · 避免讀到舊值)" % len(st_)]
    return basic, fin, summ, gaps, made


def _stale_parquet(od: Path) -> list:
    """③ 本輪寫不出 Parquet(缺 pandas / pyarrow)時,上一輪的 Parquet 還在 = 讀到舊值 → 比本輪 JSON 舊的 Parquet 移到 output/_stale(不刪)。回移走的檔名。"""
    import shutil
    import time as _t
    moved = []
    for js in sorted(Path(od).glob("VRN2_*_latest.json")):
        pq = js.with_suffix(".parquet")
        if pq.exists() and pq.stat().st_mtime < js.stat().st_mtime - 1:
            dst = Path(od) / "_stale" / ("%s_%s.parquet" % (pq.stem, _t.strftime("%Y%m%d_%H%M%S", _t.localtime(pq.stat().st_mtime))))
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(pq), str(dst))
            moved.append(pq.name)
    return moved


def _out_html(basic: list, fin: list, summ: list) -> str:
    """v0232 三本冊頁 + 剔除冊 + v0234 子欄拆分總表(每張表:期間 · 子欄 · 筆數 · 是否依子表頭更正分組)。"""
    import html as _h
    from collections import OrderedDict
    g = OrderedDict()
    for x in fin:
        if x.get("SUBCOL"):
            k = (x["FILENAME"], x["TABLE"])
            e = g.setdefault(k, {"per": [], "lab": [], "n": 0, "fix": 0})
            e["n"] += 1
            e["fix"] += "更正" in (x.get("VERIFY") or "")
            if x["PERIOD"] not in e["per"]:
                e["per"].append(x["PERIOD"])
            if x["SUBCOL"] not in e["lab"]:
                e["lab"].append(x["SUBCOL"])
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>" % (
        _h.escape(f[:40]), _h.escape(t), _h.escape(" / ".join(e["per"])), _h.escape(" · ".join(e["lab"])), e["n"], ("依子表頭更正 %d 筆" % e["fix"]) if e["fix"] else "—")
        for (f, t), e in g.items())
    sec = ("<h2 style='margin-top:14px'>子欄拆分(一格多值 → 期間 + 子欄 · %d 筆 · pypdfium2 對位 · 兩條讀法數值序列相同)</h2>"
           "<table><tr><th>檔案</th><th>表</th><th>期間</th><th>子欄</th><th>筆數</th><th>擷取分組</th></tr>%s</table>" % (sum(e["n"] for e in g.values()), rows)) if g else ""
    return PRIOR._out_html(basic, fin, summ) + sec


def completion(*a, **k) -> dict:
    """完成判定(v0231 本體 + v0232 輸出值驗證項)· 管理器欄寫實際在跑的尾版(前版包裝寫的是它自己的版號 v0232)。"""
    comp = PRIOR.completion(*a, **k)
    comp["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    return comp


vrn2 = _rebind(PRIOR.vrn2)                                                # 同一段 vrn2(v0231 程式碼)· 用到本版 _out_books
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0234)


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
    td = Path(tempfile.mkdtemp(prefix="v0234-"))
    pdf = td / "SV-6415 20260101.pdf"
    ok_pdf = False
    try:
        from reportlab.pdfgen import canvas as _cv
        cv = _cv.Canvas(str(pdf), pagesize=(595, 842))
        cv.setFont("Helvetica", 9)
        for x, t in ((200, "2026E"), (380, "2027E")):
            cv.drawString(x, 700, t)
        for x0 in (150, 330):
            for k, t in enumerate(("Old", "New", "Diff (%)")):
                cv.drawString(x0 + 55 * k, 688, t)
        cv.drawString(40, 700, "(NT$mn)")
        cv.drawString(40, 676, "Revenue")
        for x0, vals in ((150, ("22,682", "23,551", "3.8%")), (330, ("n.a.", "39,865", "n.a."))):
            for k, t in enumerate(vals):
                cv.drawString(x0 + 55 * k, 676, t)
        cv.drawString(40, 664, "EPS")
        for x0, vals in ((150, ("8.51", "11.48", "34.8%")), (330, ("13.49", "21.66", "60.5%"))):
            for k, t in enumerate(vals):
                cv.drawString(x0 + 55 * k, 664, t)
        cv.save()
        ok_pdf = True
    except Exception as e:  # noqa: BLE001
        print("  [計] 自測 PDF 產生不了(%s)→ 子欄拆分自測判紅" % type(e).__name__)
    if ok_pdf:
        ln = _xv_lines(pdf, 1, {})
        z = {"id": "P1·F·01·TB", "minor": "TB", "rows": [["", "2026E", "2027E"], ["(NT$mn)", "Old New Diff (%)", "Old New Diff (%)"],
                                                         ["Revenue", "22,682 23,551 3.8%", "n.a. 39,865 n.a."], ["EPS", "8.51 11.48 34.8% 13.49", "21.66 60.5%"],
                                                         ["EPS", "8.51 11.48 34.8%", "13.49 21.66 60.5%"]]}
        sp = _sv_split_table(z, ln)
        chk("⓪ v0234 子欄拆分:Revenue 2026E → %s · 2027E → %s" % (sp.get((2, 1)), sp.get((2, 2))),
            sp.get((2, 1)) == [("Old", "22,682"), ("New", "23,551"), ("Diff (%)", "3.8%")] and sp.get((2, 2)) == [("Old", "n.a."), ("New", "39,865"), ("Diff (%)", "n.a.")])
        chk("⓪ v0234 擷取把 13.49 分錯期間 → 依子表頭更正 %s · 分對的同一列照拆 %s" % (sp.get((3, 2)), sp.get((4, 2))),
            sp.get((3, 1)) == [("Old", "8.51"), ("New", "11.48"), ("Diff (%)", "34.8%")] and sp.get((3, 2)) == [("Old", "13.49"), ("New", "21.66"), ("Diff (%)", "60.5%")]
            and (id(z), 3, 2) in _SV_REGROUP and (id(z), 4, 2) not in _SV_REGROUP and sp.get((4, 2)) == sp.get((3, 2)))
        z2 = {"id": "x", "minor": "TB", "rows": [["", "2026E", "2027E"], ["(NT$mn)", "Old New Diff (%)", "Old New Diff (%)"], ["Revenue", "22,682 23,999 3.8%", "n.a. 39,865 n.a."]]}
        chk("⓪ v0234 兩條讀法數值不同(23,999 ≠ 23,551)→ 不拆 · 留剔除冊", _sv_split_table(z2, ln) == {})
        z3 = {"id": "y", "minor": "TB", "rows": z["rows"][:3] + [["", "2Q26E", "3Q26E"], ["(NT$mn)", "Old New Diff (%)", "Old New Diff (%)"], ["Revenue", "22,682 23,551 3.8%", "n.a. 39,865 n.a."]]}
        sp3 = _sv_split_table(z3, ln)
        chk("⓪ v0234 同一張表下半段換期間(2Q26E …)→ 停在新表頭 · 不把季度值標成年度 %s" % sorted(sp3), sorted(sp3) == [(2, 1), (2, 2)])
    else:
        chk("⓪ v0234 子欄拆分(需 reportlab 產生測試 PDF)", False)
    lab16 = [(x - 12, x + 12, t) for x, t in zip((99, 127, 155, 185, 213, 244, 273, 302, 329, 358, 390, 421, 447, 478, 507, 538),
                                                    ("修正後", "修正前", "調幅 (%)", "YoY (%)", "市場共識", "差異(%)") * 2 + ("凱基預估", "YoY (%)", "市場共識", "差異(%)"))]
    pg = _sv_partition(lab16, [169, 344, 491])
    chk("⓪ v0234 子表頭切組(表頭不在中點:6 / 6 / 4 欄)→ %s" % pg, pg == [0] * 6 + [1] * 6 + [2] * 4)
    chk("⓪ v0234 子表頭切組分不出來(兩種切法一樣置中)→ 不拆", _sv_partition([(0, 10, "X"), (20, 30, "Y"), (40, 50, "Z")], [12, 38]) is None
        and _sv_partition([(0, 10, "Old"), (20, 30, "Old")], [15]) is None)
    t3 = [m.group(0) for m in _TEL3.finditer("Helen Chien\n(886) 2 8758 6254\n李承泰\n886.2.2181.8729\n分機 1234\n886 2 2181 8710\n2026.10.18")]
    chk("⓪ v0234 第三讀取器電話寫法 → %s" % t3, t3 == ["(886) 2 8758 6254", "886.2.2181.8729", "886 2 2181 8710"])
    import time as _t
    od_ = td / "out"
    od_.mkdir()
    (od_ / "VRN2_FinancialData_latest.parquet").write_bytes(b"old")
    (od_ / "VRN2_BasicInfo_latest.parquet").write_bytes(b"new")
    _old = _t.time() - 600
    os.utime(od_ / "VRN2_FinancialData_latest.parquet", (_old, _old))
    (od_ / "VRN2_FinancialData_latest.json").write_text("[]", encoding="utf-8")
    (od_ / "VRN2_BasicInfo_latest.json").write_text("[]", encoding="utf-8")
    mv = _stale_parquet(od_)
    chk("⓪ v0234 Parquet 比本輪 JSON 舊 → 移到 _stale(不刪)%s · 本輪寫的留著" % mv, mv == ["VRN2_FinancialData_latest.parquet"] and (od_ / "VRN2_BasicInfo_latest.parquet").exists()
        and len(list((od_ / "_stale").glob("*.parquet"))) == 1)
    uh = _out_html([], [{"FILENAME": "a.pdf", "TABLE": "T", "PERIOD": "2026F", "SUBCOL": "修正後", "VALUE": "1", "VERIFY": "x · 擷取分組更正(依子表頭)"}], [])
    chk("⓪ v0234 U/I 子欄拆分總表(帶更正筆數)", "子欄拆分" in uh and "依子表頭更正 1 筆" in uh and "剔除冊" in uh)
    try:
        _cm = completion(0, 1, 1, True, {}, []).get("manager")
    except Exception as e:  # noqa: BLE001
        _cm = "例外 %s" % type(e).__name__
    chk("⓪ v0234 完成判定的管理器欄 = 實際尾版 → %s" % _cm, _cm == "VRN-2 SystemManager v0234")
    chk("⓪ v0234 前版必須是 v0233 → %s" % getattr(PRIOR, "TAG", "?"), getattr(PRIOR, "TAG", "") == "v0233")
    chk("⓪ v0234 零替換:vrn2 / 前版輸出冊是同一段程式(重新綁定)", vrn2.__code__ is PRIOR.vrn2.__code__ and vrn2.__globals__ is globals())
    try:
        _ob = _out_books([], [], [], td)
        _ob_err = ""
    except BaseException as e:  # noqa: BLE001 — 自測要把遞迴 / 例外當紅燈報出
        _ob, _ob_err = (), type(e).__name__
    chk("⓪ v0234 輸出冊(本版 → v0233 → v0232)空輸入跑完不遞迴 %s" % (_ob_err or "· 回傳 %d 項" % len(_ob)), not _ob_err and len(_ob) == 5)
    print("  ── 前版 v0233 自測(原樣)──")
    rc_p = PRIOR.selftest()
    chk("⓪ 前版 %s 自測 rc %d" % (PRIOR_PATH.name, rc_p), rc_p == 0)
    print("[計] %s %s(%s)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, Path(__file__).name, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

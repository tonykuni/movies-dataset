#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0235 — 薄尾(使用者機器 52 份實跑 + 獨立驗證回報的一輪修正):① 第三讀法閘(pdfplumber 字詞框 · 跟擷取的表格切法、v0232 / v0234 的 pypdfium2 字元框都不同):子欄(一格多值拆開的)整列序列 / 最近期間表頭 / 組內標籤不重複 / 表頭在組內 / 標籤 = 最近子表頭字 · v0232「欄位未定位」的值要對到期間欄 · 科目要在該頁原文(兩個讀取器聯集 · 允許折行)· 不過的移剔除冊(帶理由 · 不消失)② 分析師:Email 帳號推算的英文名(Allen K Chang)原文沒印 → 改用原文同一行印的寫法(Allen Chang / Allen K. Chang / Angela HC Hsu)· 找不到照舊標推算。
  零替換:前版函式一個都不改;前版輸出冊(v0234)整段照跑後再補(直接叫前版包裝 · 不 rebind 包裝 → 不遞迴)· vrn2 / 成功登記用同一段程式碼重新綁定 · 前版必須是 v0234 · 其餘動詞照前版鏈。
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
TAG = "v0235"
DISPLAY_NAME = "VRN-2 SystemManager"


def _vnum_v0235(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0235(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0235(p) < _vnum_v0235(__file__)), key=_vnum_v0235)
PRIOR = _load_v0235(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


# ===== ① 第三讀法閘(pdfplumber 字詞框 · 跟擷取的表格切法 / v0232 · v0234 的 pypdfium2 字元框都不同的讀法)=====
_G3 = {}
_G3_VTOK = re.compile(r"(?i)^(?:\(?-?\d[\d,]*\.?\d*\)?%?|\(?-?\.\d+\)?%?|\d+(?:\.\d+)?pp|n\.?a\.?|n/a|nm|n\.m\.|[-–—]+)$")
_G3_PER = re.compile(r"(?i)^(?:FY)?(?:19|20)?\d{2}[AEFP]?$|^[1-4]Q\d{2}[AEFP]?$|^(?:19|20)\d{2}\([AEFP]\)$")


def _g3_page(pdf: Path, pno: int):
    """一頁 → (行 [(top, [(x0, x1, 字)])] 由上而下, 該頁原文壓縮字串(pdfplumber + pypdfium2 聯集))· pdfplumber 讀不到 → None(閘不判)。"""
    key = (str(pdf), pno)
    if key not in _G3:
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf)) as d:
                if not 1 <= pno <= len(d.pages):
                    _G3[key] = None
                    return None
                pg = d.pages[pno - 1]
                rows = []
                for w in sorted(pg.extract_words(keep_blank_chars=False), key=lambda w: w["top"]):
                    rw = next((r for r in rows if abs(r[0] - w["top"]) < 3.0), None)
                    if rw is None:
                        rw = [w["top"], []]
                        rows.append(rw)
                    rw[1].append((w["x0"], w["x1"], _xv_nfk(w["text"])))
                lines = [(t, sorted(tk)) for t, tk in sorted(rows, key=lambda r: r[0])]
                txt = (pg.extract_text() or "") + "\n" + (_acc_pdfium_text(Path(pdf), [pno]).get(pno, "") or "")
            _G3[key] = (lines, _xv_sq(txt), [_xv_sq("".join(t for _, _, t in tk)) for _, tk in lines])
        except Exception:  # noqa: BLE001
            _G3[key] = None
    return _G3[key]


def _g3_item_ok(item: str, pg) -> bool:
    """科目在該頁原文(兩個讀取器聯集)· 允許科目折兩行。"""
    si = _xv_sq(item)
    if not si or si in pg[1]:
        return True
    rows = pg[2]
    return any(si[:k] in rows[i] and si[k:] in "".join(rows[i + 1:i + 3]) for i in range(len(rows)) for k in range(4, max(5, len(si) - 2)))


def _g3_aligned(x: dict, pg) -> str:
    """一般格:值在科目那一列(含下一列 14pt 內)· 上方同期間字樣的表頭取 x 最近 · 落在欄寬內 → 'ALIGNED';值在頁上但對不到欄 → 'PRESENT';頁上沒有 → 'ABSENT'。"""
    lines = pg[0]
    val, per = _xv_nfk(x.get("VALUE", "")).strip(), _xv_nfk(x.get("PERIOD", "")).strip()
    sv = _xv_sq(val)
    key = _xv_sq(x.get("ITEM", ""))[:14]
    best, present = None, any(_xv_sq(t) in (sv, sv.replace(",", "")) for _, tk in lines for _, _, t in tk)
    for k, (y, tk) in enumerate(lines):
        if not key or key not in pg[2][k]:
            continue
        row_toks = [tt for kk in (k, k + 1) if kk < len(lines) and abs(lines[kk][0] - y) < 14 for tt in lines[kk][1]]
        hits = [((a + b) / 2, b - a) for a, b, t in row_toks if _xv_sq(t) in (sv, sv.replace(",", ""))]
        if not hits:
            continue
        for yy, htk in lines:
            if not (y - 520 < yy < y + 1):
                continue
            for a, b, t in htk:
                if t != per:
                    continue
                hx = (a + b) / 2
                colw = min([abs((aa + bb) / 2 - hx) for aa, bb, tt in htk if tt != per and _XV_PER.match(tt)] + [60])
                for vx, _w in hits:
                    dx = abs(vx - hx)
                    if best is None or dx < best[0]:
                        best = (dx, colw, b - a)
    if best and best[0] <= max(0.55 * best[1], best[2] * 0.9, 12):
        return "ALIGNED"
    return "PRESENT" if present else "ABSENT"


def _g3_subcol(xs: list, pg) -> str:
    """同一列子欄(同檔 · 表 · 頁 · 科目)· 回 '' = 過 · 否則不過的理由:① 整列序列 = 原文那一列 ② 期間 = 上方最近的期間表頭 ③ 同期間標籤不重複
    ④ 期間表頭落在該組值的範圍 ⑤ 子欄標籤 = 離值最近的子表頭字。"""
    lines = pg[0]
    item = xs[0].get("ITEM", "")
    vals = [_xv_sq(x["VALUE"]) for x in xs]
    pers = list(dict.fromkeys(x["PERIOD"] for x in xs))
    hit = None
    for k, (top, tk) in enumerate(lines):
        vt = [(a, b, t) for a, b, t in tk if _G3_VTOK.match(t) and _xv_sq(t) != _xv_sq(item)]
        sq = [_xv_sq(t) for _, _, t in vt]
        for i in range(0, len(sq) - len(vals) + 1):
            if sq[i:i + len(vals)] == vals:
                hk = next((kk for kk in range(k - 1, -1, -1) if sum(bool(_G3_PER.match(t)) for _, _, t in lines[kk][1]) >= 2), None)
                if hk is not None and all(any(t == p for _, _, t in lines[hk][1]) for p in pers):
                    hit = (k, vt[i:i + len(vals)], len(sq) == len(vals), hk)
                    break
        if hit:
            break
    if not hit:
        return "①② 原文沒有同序列的一列 / 上方最近的期間表頭不是 %s" % "/".join(pers)
    k, vt, full, hk = hit
    if not full:
        return "① 原文那一列還有別的值(拆分不完整)"
    hx = {p: next((a + b) / 2 for a, b, t in lines[hk][1] if t == p) for p in pers}
    x0 = min(a for a, _, _ in vt)
    labw = [(a, b, t) for kk in range(hk + 1, k) for a, b, t in lines[kk][1] if not re.fullmatch(r"\(?%\)?", t) and not _G3_VTOK.match(t) and (a + b) / 2 > x0 - 25]
    by_p = {}
    for x, (a, b, t) in zip(xs, vt):
        by_p.setdefault(x["PERIOD"], []).append((x, a, b))
    for p, g in by_p.items():
        labs = [_xv_sq(x["SUBCOL"]) for x, _, _ in g]
        if len(set(labs)) != len(labs) or any(re.search(r"#\d+$", x["SUBCOL"]) for x, _, _ in g):
            return "③ %s 子欄標籤重複" % p
        if not (min(a for _, a, _ in g) - 14 <= hx[p] <= max(b for _, _, b in g) + 14):
            return "④ %s 期間表頭不在這組值的範圍" % p
        for x, a, b in g:
            if not labw:
                return "⑤ 找不到子表頭"
            nb = min(labw, key=lambda w: abs((w[0] + w[1]) / 2 - (a + b) / 2))
            sc = x["SUBCOL"].split()
            first = _xv_sq(re.sub(r"\s*\(%\)$|\s*#\d+$", "", x["SUBCOL"]).split()[0] if sc else x["SUBCOL"])
            if _xv_sq(re.sub(r"\(%\)$", "", nb[2])) != re.sub(r"\(%\)$", "", first):
                return "⑤ %s %s 值 %s 最近的子表頭字是「%s」" % (p, x["SUBCOL"], x["VALUE"], nb[2])
    return ""


def _gate3(fin: list, v2: Path) -> tuple:
    """主冊年度數據過第三讀法閘:子欄 → _g3_subcol · v0232 欄位未定位 → 要 _g3_aligned 對欄 · 科目 → 該頁原文要有。
    v0232 / v0234 已用 pypdfium2 對欄的一般格不因 pdfplumber 切字不同而剔除(只查科目)。不過的移剔除冊(帶理由 · 不消失)。回 (留下, 剔除, 統計)。"""
    from collections import Counter
    keep, rej, stat = [], [], Counter()
    sub = {}
    for x in fin:
        if x.get("SUBCOL"):
            sub.setdefault((x["FILENAME"], x.get("TABLE"), int(x.get("PAGE") or 0), x.get("ITEM")), []).append(x)
    bad_sub = {}
    for (f, tb, pno, it), xs in sub.items():
        pg = _g3_page(_out_pdf(f, v2), pno)
        if pg is None:
            stat["閘不可用"] += len(xs)
            continue
        why = _g3_subcol(xs, pg)
        stat["子欄過" if not why else "子欄剔除"] += len(xs)
        for x in xs if why else []:
            bad_sub[id(x)] = why
    for x in fin:
        if id(x) in bad_sub:
            rej.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON="子欄第三讀法(pdfplumber)對不上 · " + bad_sub[id(x)]))
            continue
        if x.get("SUBCOL"):
            keep.append(x)
            continue
        pg = _g3_page(_out_pdf(x["FILENAME"], v2), int(x.get("PAGE") or 0))
        if pg is None:
            stat["閘不可用"] += 1
            keep.append(x)
            continue
        if not _g3_item_ok(x.get("ITEM", ""), pg):
            stat["科目剔除"] += 1
            rej.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON="科目該頁原文沒有(pdfplumber + pypdfium2 都讀不到「%s」)" % x.get("ITEM", "")))
            continue
        if str(x.get("VERIFY", "")).startswith("原文該頁有值"):
            vd = _g3_aligned(x, pg)
            if vd == "ALIGNED":
                stat["未定位補對欄"] += 1
                keep.append(dict(x, VERIFY="對欄(pdfplumber · 第三讀法)"))
            else:
                stat["未定位剔除"] += 1
                rej.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData",
                                REASON="欄位未定位(pypdfium2 / pdfplumber 都對不到期間欄 · %s)" % ("值在該頁" if vd == "PRESENT" else "pdfplumber 讀不到此值")))
            continue
        keep.append(x)
    return keep, rej, stat


# ===== ② 分析師姓名照原文印(Email 帳號推算的英文名 → 原文印的那個寫法)=====
def _an_printed(em_: str, raw: str) -> str:
    """Email 帳號(allen.k.chang)→ 原文同一行裡「名 [中間名 / 縮寫] 姓」的印法(Allen Chang · Allen K. Chang · Angela HC Hsu)· 找不到 → ''。"""
    toks = [w for w in re.split(r"[._\-]", em_.split("@")[0]) if w.isalpha()]
    if len(toks) < 2:
        return ""
    pat = re.compile(r"(?<![A-Za-z])(%s(?:[ \t]+(?:[A-Za-z]{1,3}\.?|[A-Z][a-z]+))?[ \t]+%s)(?![A-Za-z])" % (re.escape(toks[0]), re.escape(toks[-1])), re.I)
    for m in pat.finditer(raw or ""):
        s = re.sub(r"[ \t]+", " ", m.group(1)).strip()
        if s[:1].isupper() and s.split()[-1][:1].isupper():
            return s
    return ""


def _an_fix(basic: list, v2: Path) -> int:
    """基本資料:分析師是 Email 帳號推算、原文沒印的那個寫法 → 換成原文印的寫法(狀態改「原文」)· 找不到照舊標推算。回換了幾個。"""
    n = 0
    for row in basic:
        names = [a for a in (row.get("ANALYST") or "").split("、") if a]
        ems = [e for e in (row.get("EMAIL") or "").split("、") if e]
        if not names or not ems:
            continue
        pdf = _out_pdf(row["FILENAME"], v2)
        raw = _xv_raw(pdf, (1, 2, 3)) if pdf.exists() else ""
        rsq = _xv_sq(raw)
        new, sts = [], []
        for nm in names:
            out_ = nm
            if _xv_sq(nm) not in rsq:
                for em_ in ems:
                    guess = " ".join(w.capitalize() for w in re.split(r"[._]", em_.split("@")[0]) if w.isalpha())
                    if guess == nm:
                        pr = _an_printed(em_, raw)
                        if pr:
                            out_, n = pr, n + 1
                        break
            new.append(out_)
            sts.append("原文" if _xv_sq(out_) in rsq else "推算(Email 帳號 · 原文未印此名)")
        row["ANALYST"] = "、".join(dict.fromkeys(new))
        row.setdefault("_STATUS", {})["ANALYST"] = " / ".join(dict.fromkeys(sts)) or "—"
    return n


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0235 = v0234 輸出冊 + ① 第三讀法閘(pdfplumber 字詞框):子欄 / 未定位 / 科目 不過的移剔除冊(帶理由)② 分析師照原文印的寫法。"""
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)   # 直接叫前版包裝(不 rebind 包裝 → 不遞迴)
    n_an = _an_fix(basic, v2)
    keep, rj, stat = _gate3(fin, v2)
    rej = list(_XV_LAST.get("rej") or []) + rj
    od = v2 / "output"
    made = [m_ for m_ in made if not m_.startswith(("FinancialData(", "Rejected(", "BasicInfo("))]
    made = [_write_book(od, "BasicInfo", basic), _write_book(od, "FinancialData", keep)] + made + [_write_book(od, "Rejected", rej)]
    _XV_LAST["rej"] = rej
    it = _XV_LAST.get("item")
    if it:
        lamp = "GREEN" if not rej else "YELLOW"
        _XV_LAST["item"] = (it[0], lamp, it[2] + " · v0235 第三讀法閘(pdfplumber):子欄 過 %d / 剔除 %d · 未定位 補對欄 %d / 剔除 %d · 科目原文沒有 剔除 %d%s · 分析師改原文寫法 %d · 剔除冊共 %d" % (
            stat["子欄過"], stat["子欄剔除"], stat["未定位補對欄"], stat["未定位剔除"], stat["科目剔除"], (" · 閘不可用 %d" % stat["閘不可用"]) if stat["閘不可用"] else "", n_an, len(rej)))
    st_ = _stale_parquet(od)
    if st_:
        made = made + ["Parquet 舊檔 %d 個移到 output/_stale(本輪沒寫 Parquet · 避免讀到舊值)" % len(st_)]
    return basic, keep, summ, gaps, made


vrn2 = _rebind(PRIOR.vrn2)                                                # 同一段 vrn2(v0231 程式碼)· 用到本版 _out_books
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0235)


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
    td = Path(tempfile.mkdtemp(prefix="v0235-"))
    a1 = _an_printed("allen.k.chang@gs.com", "Taiwan Technology\nAllen Chang\n+886(2)2730-4185\nallen.k.chang@gs.com")
    a2 = _an_printed("allen.k.chang@gs.com", "Allen K. Chang, CFA +886 2 2730 4185")
    a3 = _an_printed("angela.hc.hsu@citi.com", "Angela HC Hsu\nangela.hc.hsu@citi.com")
    a4 = _an_printed("allen.k.chang@gs.com", "Allen\nChang")
    chk("⓪ v0235 分析師照原文印:%s · %s · %s · 跨行不算 %r" % (a1, a2, a3, a4), (a1, a2, a3, a4) == ("Allen Chang", "Allen K. Chang", "Angela HC Hsu", ""))
    (td / "scope_in").mkdir()
    pdf = td / "scope_in" / "G3-6415 20260101.pdf"
    ok_pdf = False
    try:
        from reportlab.pdfgen import canvas as _cv
        cv = _cv.Canvas(str(pdf), pagesize=(595, 842))
        cv.setFont("Helvetica", 9)
        cv.drawString(40, 720, "(NT$mn)")
        for x, t in ((200, "2026E"), (300, "2027E")):
            cv.drawString(x, 720, t)
        cv.drawString(40, 700, "Revenue")
        for x, t in ((200, "22,682"), (300, "31,181")):
            cv.drawString(x, 700, t)
        cv.drawString(40, 660, "(NT$mn)")
        for x, t in ((200, "2026E"), (380, "2027E")):
            cv.drawString(x, 660, t)
        for x0 in (150, 330):
            for k, t in enumerate(("Old", "New", "Diff")):
                cv.drawString(x0 + 55 * k, 648, t)
        cv.drawString(40, 636, "EPS")
        for x0, vals in ((150, ("8.51", "11.48", "34.8%")), (330, ("13.49", "21.66", "60.5%"))):
            for k, t in enumerate(vals):
                cv.drawString(x0 + 55 * k, 636, t)
        cv.save()
        ok_pdf = True
    except Exception as e:  # noqa: BLE001
        print("  [計] 自測 PDF 產生不了(%s)→ 第三讀法閘自測判紅" % type(e).__name__)
    if ok_pdf:
        base = {"FILENAME": pdf.name, "TABLE": "T", "PAGE": 1}
        rows = [dict(base, ITEM="Revenue", PERIOD="2026E", VALUE="22,682", VERIFY="對欄(pypdfium2)"),
                dict(base, ITEM="Revenue", PERIOD="2027E", VALUE="31,181", VERIFY="原文該頁有值 · 欄位未定位"),
                dict(base, ITEM="Revenue", PERIOD="2027E", VALUE="22,682", VERIFY="原文該頁有值 · 欄位未定位"),
                dict(base, ITEM="Operating income", PERIOD="2026E", VALUE="22,682", VERIFY="對欄(pypdfium2)")]
        good = [("2026E", "Old", "8.51"), ("2026E", "New", "11.48"), ("2026E", "Diff", "34.8%"), ("2027E", "Old", "13.49"), ("2027E", "New", "21.66"), ("2027E", "Diff", "60.5%")]
        rows += [dict(base, TABLE="S", ITEM="EPS", PERIOD=pp, SUBCOL=lb, VALUE=vv, VERIFY="子欄對位") for pp, lb, vv in good]
        swap = [("2026E", "New", "8.51"), ("2026E", "Old", "11.48")] + good[2:]
        rows += [dict(base, TABLE="S2", ITEM="EPS", PERIOD=pp, SUBCOL=lb, VALUE=vv, VERIFY="子欄對位") for pp, lb, vv in swap]
        kp, rj, stt = _gate3(rows, td)
        kv = [(x["TABLE"], x["ITEM"], x["PERIOD"], x.get("SUBCOL", ""), x["VALUE"], x["VERIFY"][:6]) for x in kp]
        chk("⓪ v0235 第三讀法閘:對欄留 · 未定位對得上 → 補對欄 · 未定位對不上 / 科目原文沒有 / 子欄標籤對調 → 剔除冊 · 統計 %s" % dict(stt),
            ("T", "Revenue", "2026E", "", "22,682", "對欄(pyp") in kv and ("T", "Revenue", "2027E", "", "31,181", "對欄(pdf") in kv
            and len([x for x in kp if x["TABLE"] == "S"]) == 6 and not [x for x in kp if x["TABLE"] == "S2"] and len(kp) == 8
            and sorted(r["REASON"][:6] for r in rj) == sorted(["欄位未定位(", "科目該頁原文"] + ["子欄第三讀法"] * 6)
            and stt["子欄過"] == 6 and stt["子欄剔除"] == 6 and stt["未定位補對欄"] == 1 and stt["未定位剔除"] == 1 and stt["科目剔除"] == 1)
    else:
        chk("⓪ v0235 第三讀法閘(需 reportlab 產生測試 PDF)", False)
    chk("⓪ v0235 前版必須是 v0234 → %s" % getattr(PRIOR, "TAG", "?"), getattr(PRIOR, "TAG", "") == "v0234")
    chk("⓪ v0235 零替換:vrn2 是同一段程式(重新綁定)", vrn2.__code__ is PRIOR.vrn2.__code__ and vrn2.__globals__ is globals())
    try:
        _ob = _out_books([], [], [], td)
        _ob_err = ""
    except BaseException as e:  # noqa: BLE001 — 自測要把遞迴 / 例外當紅燈報出
        _ob, _ob_err = (), type(e).__name__
    chk("⓪ v0235 輸出冊(本版 → v0234 → v0233 → v0232)空輸入跑完不遞迴 %s" % (_ob_err or "· 回傳 %d 項" % len(_ob)), not _ob_err and len(_ob) == 5)
    try:
        _cm = completion(0, 1, 1, True, {}, []).get("manager")
    except Exception as e:  # noqa: BLE001
        _cm = "例外 %s" % type(e).__name__
    chk("⓪ v0235 完成判定的管理器欄 = 實際尾版 → %s" % _cm, _cm == "VRN-2 SystemManager v0235")
    print("  ── 前版 v0234 自測(原樣)──")
    rc_p = PRIOR.selftest()
    chk("⓪ 前版 %s 自測 rc %d" % (PRIOR_PATH.name, rc_p), rc_p == 0)
    print("[計] %s %s(%s)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, Path(__file__).name, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

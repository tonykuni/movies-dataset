#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0239 — 薄尾(邊測邊修:段落標題 SECTION 跨到並排的另一張表):凱基 2637 第 5 頁左「財務比率」右「投資回報率」兩張表並排 · 左表 流動比率 / 速動比率 / 淨負債 拿到右表的公式項「1 - 營業成本/營業收入」· 右表 1 / (營業運用資金 … = 稅後 ROIC 拿到左表的「每股資料分析」/「資產運用狀況」(共 13 列 65 筆)· 第三讀法(pdfplumber 字詞框)找科目那一列 → 上方同一個科目欄找這個 SECTION 字 → 找不到或是公式項(1 - … · = … · x …)→ 改成同一欄最近的段落標題(到期間表頭為止 · 沒有 → 空白);值一個都不動。獨立驗證器 v0102 另查(pypdfium2 · SECFAIL)。
  零替換:前版函式一個都不改;前版輸出冊(v0238)整段照跑後再補(直接叫前版包裝)· vrn2 / 成功登記用同一段程式碼重新綁定 · 前版必須是 v0238 · 其餘動詞照前版鏈。
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
TAG = "v0239"
DISPLAY_NAME = "VRN-2 SystemManager"


def _vnum_v0239(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0239(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0239(p) < _vnum_v0239(__file__)), key=_vnum_v0239)
PRIOR = _load_v0239(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


_SEC_FORM = re.compile(r"^\s*(?:[-+=×xX÷/]\s|\d+\s*[-+/×xX÷]\s)")
_SEC_PER = re.compile(r"(?i)^(?:(?:FY|CY)'?\d{2,4}[AEFPCTH]?|(?:19|20)\d{2}(?:[AEFPH]|CT|\([AEF]\))?|\d{2}[AEF]|\d{1,2}/\d{2,4}[AEFe]?|[A-Z][a-z]{2}-\d{2}[AEF]?|[1-4][QH]\d{2}[AEF]?)$")
_SEC_NIL = re.compile(r"(?i)^(?:[-–—]+|n\.?a\.?|nm|n/?m|n/?a|nil|neg\.?)$")


def _sec_isval(t) -> bool:
    return bool(re.search(r"\d", str(t))) or bool(_SEC_NIL.match(str(t)))


def _sec_span(tk: list, target: str) -> list:
    """一列字詞裡連續幾個字詞壓縮後 = target 的起點 x0(可能好幾處)· 起點前 6 pt 內不能緊接別的字(「= 營業利益率」不算「營業利益率」)。"""
    out = []
    for i in range(len(tk)):
        if i and tk[i][0] - tk[i - 1][1] < 6:
            continue
        s = ""
        for j in range(i, len(tk)):
            s += _xv_sq(tk[j][2])
            if s == target:
                out.append(tk[i][0])
                break
            if len(s) >= len(target) or not target.startswith(s):
                break
    return out


def _sec_col(tk: list, cx: float):
    """這一列在科目欄(起點 cx ± 40)的字 → (字, 後面有沒有數值) · 沒有字 → None。
    科目字 = 從欄起點起字距 < 6 的一串字(公式項的「1 -」「=」「x」也連在一起 → 才認得出公式項)· 整串都是數值 → 當數據列。"""
    st = [i for i, z in enumerate(tk) if cx - 40 <= z[0] <= cx + 40]
    if not st:
        return None
    i = j = st[0]
    while j + 1 < len(tk) and tk[j + 1][0] - tk[j][1] < 6:
        j += 1
    lab = " ".join(z[2] for z in tk[i:j + 1])
    if all(_sec_isval(z[2]) for z in tk[i:j + 1]):
        return lab, True
    vals = [z for z in tk[j + 1:] if z[0] - tk[j][1] < 400 and _sec_isval(z[2])]
    nxt = tk[j + 1] if j + 1 < len(tk) else None
    other = nxt is not None and not _sec_isval(nxt[2])                    # 右邊緊接的是別張表的字 → 這一列在本欄沒有數值
    return lab, bool(vals) and not other


def _sec_near(lines: list, k: int, cx: float) -> str:
    """科目上方、同一個科目欄裡最近的段落標題(只有標題字 · 右邊沒有數值 · 不是公式項 1 - … / = … / x …)· 遇到本欄的期間表頭就停 → ""。"""
    for j in range(k - 1, -1, -1):
        if lines[k][0] - lines[j][0] > 600:
            break
        tk = lines[j][1]
        if sum(1 for z in tk if cx + 40 < z[0] < cx + 420 and _SEC_PER.match(z[2])) >= 2:
            return ""
        cl = _sec_col(tk, cx)
        if cl and not cl[1] and not _SEC_FORM.match(cl[0]) and not re.fullmatch(r"\(.*\)", cl[0].strip()):
            return _tidy(cl[0])
    return ""


def _secfix(fin: list, v2: Path, zbb=None) -> tuple:
    """v0239 段落標題(SECTION)要在同一個科目欄:並排的兩張表(凱基 2637 第 5 頁 財務比率 ∥ 投資回報率)以前互相拿對方的段落標題
    (流動比率 → 「1 - 營業成本/營業收入」· = 稅後 ROIC → 「資產運用狀況」)· 公式項(1 - 營業成本/營業收入)也不是段落標題。
    第三讀法(pdfplumber 字詞框)找科目那一列(只在這張表的上下範圍 zbb · 起點前沒有緊接的字 · 有這一列的值的那一行優先 · 同一欄才依 ROW 排序)
    → 上方同一個科目欄找這個 SECTION 字 → 找不到或是公式項 → 改成同一欄最近的段落標題(到期間表頭為止 · 沒有 → 空白 · 候選列不一致 → 空白)· 沒有表的範圍 → 不改。
    回 (改了幾列, 幾筆, 例子)。"""
    grp = defaultdict(list)
    for x in fin:
        if x.get("SECTION") and not x.get("SUBCOL") and "轉置" not in str(x.get("VERIFY", "")) and x.get("PAGE"):
            grp[(x["FILENAME"], int(x["PAGE"]), x.get("TABLE"))].append(x)
    nrow, nrec, ex = 0, 0, []
    for (f, pno, tb), xs in grp.items():
        pdf = _out_pdf(f, v2)
        g = _g3_page(pdf, pno) if pdf.exists() else None
        if not g:
            continue
        bb = (zbb or {}).get((f, tb))
        if not (bb and len(bb) == 4):                                      # 沒有這張表的範圍 → 不改(同一頁別張表的同名科目會混進來)
            continue
        lines = g[0]
        band = lambda t, bb=bb: bb[1] - 12 <= t <= bb[3] + 12             # noqa: E731
        byrow = defaultdict(list)
        for x in xs:
            byrow[(x.get("ROW"), x["ITEM"], x["SECTION"])].append(x)
        allrows = defaultdict(set)
        for z in fin:
            if z["FILENAME"] == f and str(z.get("PAGE")) == str(pno) and z.get("TABLE") == tb and z.get("ROW") and not z.get("SUBCOL"):
                allrows[z["ITEM"]].add(int(z["ROW"]))
        for (row, item, sec), rs in byrow.items():
            si, ss = _xv_sq(item), _xv_sq(sec)
            labs = [(k, x0) for k, (t, tk) in enumerate(lines) if band(t) for x0 in _sec_span(tk, si)]
            if not labs:
                continue
            vs = {_xv_sq(x.get("VALUE", "")) for x in rs} - {""}
            sc = [sum(1 for v in vs if any(_xv_sq(w) == v for _, _, w in lines[k][1])) for k, _ in labs]
            if max(sc) > 0:
                labs = [l_ for l_, c_ in zip(labs, sc) if c_ == max(sc)]
            rk = sorted(allrows.get(item, ()))
            if row and len(labs) > 1 and len(labs) == len(rk) and int(row) in rk and max(x0 for _, x0 in labs) - min(x0 for _, x0 in labs) < 10:
                labs = [labs[rk.index(int(row))]]
            ok = False
            for k, cx in labs:
                for j in range(k - 1, -1, -1):
                    if lines[k][0] - lines[j][0] > 600:
                        break
                    if any(abs(sx - cx) <= 40 for sx in _sec_span(lines[j][1], ss)):
                        ok = True
                        break
                if ok:
                    break
            if ok and not _SEC_FORM.match(sec):
                continue
            cand = {_sec_near(lines, k, cx) for k, cx in labs}
            new = cand.pop() if len(cand) == 1 else ""
            if new == sec:
                continue
            for x in rs:
                x["SECTION"] = new
            nrow, nrec = nrow + 1, nrec + len(rs)
            if len(ex) < 6:
                ex.append("%s p%d %s 「%s」%r → %r" % (f[:16], pno, tb, item[:16], sec[:16], new[:16]))
    return nrow, nrec, ex


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0239 = v0238 輸出冊 + 段落標題(SECTION)改回同一個科目欄的標題。"""
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)   # 直接叫前版包裝(不 rebind 包裝 → 不遞迴)
    zbb = {(r.get("file"), z.get("id")): z.get("bbox") for r in res or [] for pg in r.get("pages") or [] for z in pg.get("zones") or []}
    nrow, nrec, ex = _secfix(fin, v2, zbb)
    if nrec:
        od = v2 / "output"
        made = [m_ for m_ in made if not m_.startswith("FinancialData(")]
        made = [_write_book(od, "FinancialData", fin)] + made
    it = _XV_LAST.get("item")
    if it:
        _XV_LAST["item"] = (it[0], it[1], it[2] + " · v0239 段落標題改回同一欄 %d 列(%d 筆)%s" % (nrow, nrec, (":" + " | ".join(ex[:3])) if ex else ""))
    return basic, fin, summ, gaps, made


vrn2 = _rebind(PRIOR.vrn2)                                                # 同一段 vrn2(v0231 程式碼)· 用到本版 _out_books
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0239)


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
    td = Path(tempfile.mkdtemp(prefix="v0239-"))
    (td / "scope_in").mkdir()
    pdf = td / "scope_in" / "SB-2637 20260101.pdf"
    ok_pdf = False
    try:
        from reportlab.pdfgen import canvas as _cv
        cv = _cv.Canvas(str(pdf), pagesize=(595, 842))
        cv.setFont("Helvetica", 8)                                         # 測試 PDF 用英文字(版面同凱基 2637 第 5 頁)
        put = lambda x, y, t: cv.drawString(x, y, t)                       # noqa: E731
        for x, t in ((150, "Dec-23A"), (190, "Dec-24A")):
            put(x, 760, t)                                                 # 左表表頭
        put(50, 748, "Stability")                                            # 左表段落標題
        for y, lab, vs in ((736, "Interest cover (x)", ("2.5", "4.1")), (724, "Cash Flow Coverage (x)", ("3.0", "4.6"))):
            put(50, y, lab)
            for x, v in zip((155, 195), vs):
                put(x, y, v)
        for x, t in ((420, "Dec-23A"), (460, "Dec-24A")):
            put(x, 716, t)                                                 # 右表表頭(在左表中間的高度)
        put(320, 708, "1 - COGS/Revenue")                               # 右表公式項(沒有數值 · 不是段落標題)
        rows_ = ((704, "L", "Current ratio (x)", ("0.6", "0.8")), (696, "R", "- SG&A/Revenue", ("1.0%", "0.9%")),
                 (688, "L", "Quick ratio (x)", ("0.6", "0.8")), (680, "R", "= Operating margin", ("20.5%", "33.3%")),
                 (668, "L", "Per share data", ()), (660, "R", "x Capital turnover", ("0.2", "0.3")), (656, "L", "EPS (NT$)", ("4.38", "8.08")),
                 (640, "R", "Others", ()), (632, "R", "ROAE (%)", ("14%", "13%")))
        for y, side, lab, vs in rows_:
            x0, xs_ = (50, (155, 195)) if side == "L" else (320, (425, 465))
            put(x0, y, lab)
            for x, v in zip(xs_, vs):
                put(x, y, v)
        cv.save()
        ok_pdf = True
    except Exception as e:  # noqa: BLE001
        print("  [計] 自測 PDF 產生不了(%s)→ 段落標題自測判紅" % type(e).__name__)
    if ok_pdf and _g3_page(pdf, 1):
        def rec(row, item, sec):
            return {"FILENAME": pdf.name, "PAGE": 1, "TABLE": "P1·F·02·TB", "ROW": row, "ITEM": item, "PERIOD": "Dec-23A", "VALUE": "1", "SECTION": sec}
        fin = [rec(5, "Current ratio (x)", "1 - COGS/Revenue"), rec(6, "- SG&A/Revenue", "1 - COGS/Revenue"), rec(7, "Quick ratio (x)", "1 - COGS/Revenue"),
               rec(8, "= Operating margin", "1 - COGS/Revenue"), rec(10, "x Capital turnover", "Per share data"), rec(11, "EPS (NT$)", "Per share data"),
               rec(13, "ROAE (%)", "Others"), rec(2, "Interest cover (x)", "Stability")]
        zb = {(pdf.name, "P1·F·02·TB"): [45, 60, 560, 220]}
        chk("⓪ v0239 沒有這張表的範圍(bbox)→ 一筆都不改", _secfix([dict(x) for x in fin], td) == (0, 0, []))
        nr, nn, ex = _secfix(fin, td, zb)
        got = {x["ITEM"]: x["SECTION"] for x in fin}
        chk("⓪ v0239 並排表段落標題(版面同凱基 2637 第 5 頁):左表 Current / Quick ratio 拿右表的公式項 → 空白 · 右表 SG&A / Operating margin(公式項)→ 空白 · 右表 x Capital turnover 拿左表「Per share data」→ 空白 · 改 %d 列" % nr,
            nr == 5 and nn == 5 and got["Current ratio (x)"] == "" and got["Quick ratio (x)"] == "" and got["- SG&A/Revenue"] == "" and got["= Operating margin"] == "" and got["x Capital turnover"] == "")
        chk("⓪ v0239 同一欄的段落標題不動:左表 EPS → Per share data · 右表 ROAE → Others · 左表 Interest cover → Stability → %s" % [got["EPS (NT$)"], got["ROAE (%)"], got["Interest cover (x)"]],
            got["EPS (NT$)"] == "Per share data" and got["ROAE (%)"] == "Others" and got["Interest cover (x)"] == "Stability")
        fin2 = [rec(13, "ROAE (%)", "Per share data")]
        _secfix(fin2, td, zb)
        chk("⓪ v0239 右表 ROAE 拿左表的「Per share data」→ 改成同一欄最近的標題 Others → %r" % fin2[0]["SECTION"], fin2[0]["SECTION"] == "Others")
    else:
        chk("⓪ v0239 段落標題自測(需 reportlab + pdfplumber 產生 / 讀測試 PDF)", False)
    chk("⓪ v0239 公式項:1 - … · - … · = … · x … 是 · 1. Income / Others / 每股資料分析 不是",
        all(_SEC_FORM.match(t) for t in ("1 - 營業成本/營業收入", "- 銷管費用", "= 營業利益率", "x 資本周轉率", "+ 淨固定資產")) and not any(_SEC_FORM.match(t) for t in ("1. Income", "Others", "每股資料分析", "YoY growth (%)")))
    chk("⓪ v0239 前版必須是 v0238 → %s" % getattr(PRIOR, "TAG", "?"), getattr(PRIOR, "TAG", "") == "v0238")
    chk("⓪ v0239 零替換:vrn2 是同一段程式(重新綁定)", vrn2.__code__ is PRIOR.vrn2.__code__ and vrn2.__globals__ is globals())
    try:
        _ob = _out_books([], [], [], td)
        _ob_err = ""
    except BaseException as e:  # noqa: BLE001 — 自測要把遞迴 / 例外當紅燈報出
        _ob, _ob_err = (), type(e).__name__
    chk("⓪ v0239 輸出冊(本版 → v0238 → … → v0232)空輸入跑完不遞迴 %s" % (_ob_err or "· 回傳 %d 項" % len(_ob)), not _ob_err and len(_ob) == 5)
    try:
        _cm = completion(0, 1, 1, True, {}, []).get("manager")
    except Exception as e:  # noqa: BLE001
        _cm = "例外 %s" % type(e).__name__
    chk("⓪ v0239 完成判定的管理器欄 = 實際尾版 → %s" % _cm, _cm == "VRN-2 SystemManager v0239")
    print("  ── 前版 v0238 自測(原樣)──")
    rc_p = PRIOR.selftest()
    chk("⓪ 前版 %s 自測 rc %d" % (PRIOR_PATH.name, rc_p), rc_p == 0)
    print("[計] %s %s(%s)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, Path(__file__).name, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

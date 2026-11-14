#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0237 — 薄尾(授權完成測試修正 + U/I 顯示驗證過的輸出):① U/I 新分頁「驗證過的輸出」(第一個分頁):全部檔案總表 · 選一份 → 基本資料(值 · VRN-2 狀態 · 獨立驗證)· 一標題四重點 · 年度數據(每張表一個格子:列 = 段落 · 科目 · 列號 · 欄 = 期間 · 子欄 · 每格值 + 驗證徽章 · 滑鼠看細節)· 搜尋 · 只看待核對 · 下載本檔 CSV · 資料內嵌 JSON(「<」跳脫)· 獨立驗證佔位 window.VRN2_IV(啟動器 v0127 在背景跑 VRN2_IndependentVerifier 後寫回 · 冊指紋相同才套用)② 一格整列拆開(擷取把「科目 值 值 值」整列塞進第一格:凱基財務比率表 流動比率 / 每股盈餘 / 每股淨值 …)→ pypdfium2 與 pdfplumber 各自找到這一列(科目整個相同 · 值序列一個不多一個不少)· 各自往上找值範圍內的表頭對欄 · 兩邊 {期間: 值} 完全相同才進主冊 · 不過的進剔除冊 ③ 整列數據誤當段落標題 → 既有列的 SECTION 改回 ④ 完全重複的列(季度段與年度段同一個期間字、兩格同值)只留一筆 · 其餘移剔除冊。
  零替換:前版函式一個都不改;前版輸出冊(v0236)整段照跑後再補(直接叫前版包裝)· vrn2 / 成功登記用同一段程式碼重新綁定 · 前版必須是 v0236 · 其餘動詞照前版鏈。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0237"
DISPLAY_NAME = "VRN-2 SystemManager"


def _vnum_v0237(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0237(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0237(p) < _vnum_v0237(__file__)), key=_vnum_v0237)
PRIOR = _load_v0237(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


# ===== A 一格整列(擷取把「科目 值 值 值」整列塞進第一格 · 其他格空白:凱基財務比率表 流動比率 / 每股盈餘 …)→ 拆開 · 兩個讀取器各自定列、定表頭、對欄 =====
def _mg_split(c0: str):
    """第一格 = 科目 + 結尾 ≥2 個數值字詞 → (科目, [值]) · 不是 → None(科目要有字母或中文)。"""
    tk = (c0 or "").split()
    n = 0
    while n < len(tk) and _SV_TOK.match(tk[-1 - n]):
        n += 1
    lab = " ".join(tk[:len(tk) - n]).strip()
    if n < 2 or not re.search(r"[A-Za-z%s]" % _CJK, lab):
        return None
    return lab, tk[len(tk) - n:]


def _mg_row(lines: list, lab: str, vals: list) -> list:
    """一個讀取器的行(由上而下)裡找這一列:連續字詞接起來 = 科目(整個)· 緊接著的值字詞 = 這組值(一個不多 · 一個不少)→ [(行號, [(x0, x1, 字)])]。"""
    sl, want = _xv_sq(lab), [_xv_sq(v) for v in vals]
    out = []
    for k, (_y, tk) in enumerate(lines):
        tk = sorted(tk)
        for i in range(len(tk)):
            s, j = "", i
            while j < len(tk) and len(s) < len(sl):
                s += _xv_sq(tk[j][2])
                j += 1
            if s != sl:
                continue
            vt = tk[j:j + len(want)]
            nxt = tk[j + len(want)] if j + len(want) < len(tk) else None
            if [_xv_sq(t) for _, _, t in vt] == want and all(_SV_TOK.match(t) for _, _, t in vt) and not (nxt and _SV_TOK.match(nxt[2])):
                out.append((k, vt))
                break
    return out


_MGH = {}


def _mg_band(pdf: Path, pno: int, z: dict, lines: list, hits: list, top_based: bool) -> list:
    """同一頁可能有兩張表印著同一列(凱基第 5 頁上表 / 下表都有「每股盈餘 (NT$) 4.38 …」)→ 只留在這個區(bbox 上下 ±12pt)裡的那一列。
    bbox = [x0, top, x1, bottom](由上量)· pypdfium2 的 y 由下量 → 用頁高換算 · 沒有 bbox / 量不到頁高 → 不篩。"""
    bb = z.get("bbox")
    if not bb or len(hits) <= 1:
        return hits
    if not top_based:
        key = (str(pdf), pno)
        if key not in _MGH:
            try:
                import pypdfium2 as pdfium
                d = pdfium.PdfDocument(str(pdf))
                _MGH[key] = d[pno - 1].get_height()
                d.close()
            except Exception:  # noqa: BLE001
                _MGH[key] = None
        if not _MGH[key]:
            return hits
    out = []
    for k, vt in hits:
        top = lines[k][0] if top_based else _MGH[(str(pdf), pno)] - lines[k][0]
        if bb[1] - 12 <= top <= bb[3] + 12:
            out.append((k, vt))
    return out


def _mg_map(lines: list, k: int, vt: list) -> dict:
    """往上找最近一行在這組值的 x 範圍內有 ≥2 個年度期間字的表頭(600pt 內)· 中間的數據行要對得上這個表頭的欄 · 每個值取 x 最近的期間(半欄寬內 · 不重複)→ {期間: 值} · 對不上 → {}。"""
    vx0, vx1 = min(a for a, _, _ in vt) - 40, max(b for _, b, _ in vt) + 40
    h = None
    for kk in range(k - 1, -1, -1):
        if abs(lines[kk][0] - lines[k][0]) > 600:
            break
        if sum(1 for a, b, t in lines[kk][1] if vx0 <= a and b <= vx1 and _SK_ANNUAL.match(t)) >= 2:
            h = kk
            break
    if h is None:
        return {}
    hx = sorted(((a + b) / 2, t) for a, b, t in lines[h][1] if vx0 <= a and b <= vx1 and _SK_ANNUAL.match(t))
    sp = min([hx[i + 1][0] - hx[i][0] for i in range(len(hx) - 1)] or [60])
    for kk in range(h + 1, k):                                             # 表頭到這列之間的數據行要對得上同一個表頭的欄(不是別張表)
        mid = [(a + b) / 2 for a, b, t in lines[kk][1] if vx0 <= a and b <= vx1 and _SV_TOK.match(t) and re.search(r"\d", t)]
        if len(mid) >= 2 and any(min(abs(m - x) for x, _ in hx) > 0.5 * sp for m in mid):
            return {}
    got = {}
    for a, b, t in vt:
        vx = (a + b) / 2
        nx, nt = min(hx, key=lambda p_: abs(p_[0] - vx))
        if abs(nx - vx) > 0.5 * sp or nt in got:
            return {}
        got[nt] = t
    return got


def _sec2(rows: list, ri: int) -> str:
    """v0237 段落標題:同 v0236 _sec(往上找有科目、其他格全空的列 · 遇到期間表頭就停)· 但「一格整列」(科目 + 一串數值)是數據列 · 不是段落標題。"""
    for k in range(ri - 1, -1, -1):
        rw = rows[k] or []
        if sum(bool(_SK_ANNUAL.match((c or "").strip())) for c in rw[1:]) >= 2:
            return ""
        if rw and (rw[0] or "").strip() and len(rw) > 1 and not any((c or "").strip() for c in rw[1:]) and not _mg_split(rw[0]):
            return _tidy(rw[0])
    return ""


def _mg_fin(res: list, basic: list, fin: list, v2: Path) -> tuple:
    """A 一格整列拆開:第二讀取器(pypdfium2)與第三讀法(pdfplumber)各自找到這一列(科目整個相同 · 值序列相同)· 各自往上找表頭對欄 · 兩邊對出來的 {期間: 值} 完全相同才進主冊;
    任何一邊對不上 → 剔除冊(帶理由)· 已有的(同檔 · 表 · 列 · 期間)不重複 · 同時把被誤當段落標題的整列從既有列的 SECTION 改回(_sec2)。回 (留下, 剔除, 段落改正數)。"""
    have = {(x["FILENAME"], x.get("TABLE"), x.get("ROW"), x.get("PERIOD")) for x in fin}
    bmeta = {b["FILENAME"]: b for b in basic}
    keep, rej, cache, nsec = [], [], {}, 0
    zidx = {}
    for r in res:
        f = r.get("file")
        if f not in bmeta:
            continue
        pdf = _out_pdf(f, v2)
        base0 = {k_: bmeta[f].get(k_, "") for k_ in ("REPORT_DATE", "FILENAME", "TICKER", "BROKER")}
        for pg in r.get("pages") or []:
            pno = int(pg.get("pno") or 0)
            for z in pg.get("zones") or []:
                if z.get("minor") != "TB":
                    continue
                rows = z.get("rows") or []
                zidx[(f, z.get("id"))] = rows
                mg = [(i, _mg_split(rw[0] if rw else "")) for i, rw in enumerate(rows) if rw and not any((c or "").strip() for c in rw[1:])]
                mg = [(i, s) for i, s in mg if s]
                if not mg or "財報" not in str(z.get("minor_zh", "")) or not pdf.exists():
                    continue
                lines = _xv_lines(pdf, pno, cache)
                g = _g3_page(pdf, pno)
                for i, (lab, vals) in mg:
                    item = _tidy(lab)
                    h2 = _mg_band(pdf, pno, z, lines, _mg_row(lines, lab, vals), False)
                    m2 = _mg_map(lines, h2[0][0], h2[0][1]) if len(h2) == 1 else {}
                    h3 = _mg_band(pdf, pno, z, g[0], _mg_row(g[0], lab, vals), True) if g else []
                    m3 = _mg_map(g[0], h3[0][0], h3[0][1]) if len(h3) == 1 else {}
                    why = ("第二讀取器(pypdfium2)找不到唯一一列「%s + %d 個值」" % (item, len(vals)) if len(h2) != 1 else
                           "第二讀取器對不到表頭期間欄" if len(m2) != len(vals) else
                           "第三讀法不可用" if g is None else
                           "第三讀法(pdfplumber)找不到唯一一列" if len(h3) != 1 else
                           "第三讀法對出來的期間不同 %s ≠ %s" % (sorted(m3), sorted(m2)) if m3 != m2 else "")
                    for pe, v in (m2.items() if m2 else [("", v_) for v_ in vals]):
                        x = dict(base0, PAGE=pno, TABLE=z.get("id"), ITEM=item, PERIOD=pe, VALUE=v, ROW=i + 1, SECTION=_sec2(rows, i))
                        if (x["FILENAME"], x["TABLE"], x["ROW"], x["PERIOD"]) in have:
                            continue
                        if why:
                            rej.append(dict(x, BOOK="FinancialData", REASON="一格整列拆開 · " + why))
                        else:
                            keep.append(dict(x, VERIFY="對欄(pypdfium2 · 一格整列拆開) · pdfplumber 再驗(同列同表頭同期間)"))
    for x in fin:                                                          # 既有列的段落:整列數據誤當段落標題 → 改回
        rows = zidx.get((x.get("FILENAME"), x.get("TABLE")))
        if rows and x.get("ROW") and x.get("SECTION") and _mg_split(x["SECTION"]):
            x["SECTION"] = _sec2(rows, int(x["ROW"]) - 1)
            nsec += 1
    return keep, rej, nsec


def _dedupe(fin: list) -> tuple:
    """v0237 同檔 · 表 · 列 · 段落 · 科目 · 期間 · 子欄 · 值完全相同的兩筆(季度段與年度段同一個期間字 · 兩格同值「-」/「(1)」→ v0236 分不出哪一格是季度)→ 留第一筆 · 其餘移剔除冊。"""
    seen, keep, drop = set(), [], []
    for x in fin:
        k = (x.get("FILENAME"), x.get("TABLE"), x.get("ROW"), x.get("SECTION", ""), x.get("ITEM"), x.get("PERIOD"), x.get("SUBCOL", ""), x.get("VALUE"))
        if k in seen:
            drop.append(dict({k_: v_ for k_, v_ in x.items() if k_ != "VERIFY"}, BOOK="FinancialData", REASON="重複(同一列同期間同值出現兩次 · 季度段與年度段同一個期間字 · 留一筆)"))
            continue
        seen.add(k)
        keep.append(x)
    return keep, drop


def _out_books(res: list, acc: list, st: list, v2: Path) -> tuple:
    """v0237 = v0236 輸出冊 + 一格整列拆開(兩個讀取器都對得上才進主冊 · 不過的進剔除冊)+ 段落標題改正 + 完全重複的列只留一筆。"""
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)   # 直接叫前版包裝(不 rebind 包裝 → 不遞迴)
    add, rj, nsec = _mg_fin(res, basic, fin, v2)
    fin2, dup = _dedupe(fin + add)
    if add or rj or nsec or dup:
        fin = fin2
        rej = list(_XV_LAST.get("rej") or []) + rj + dup
        od = v2 / "output"
        made = [m_ for m_ in made if not m_.startswith(("FinancialData(", "Rejected("))]
        made = [_write_book(od, "FinancialData", fin)] + made + [_write_book(od, "Rejected", rej)]
        _XV_LAST["rej"] = rej
    it = _XV_LAST.get("item")
    if it:
        _XV_LAST["item"] = (it[0], it[1], it[2] + " · v0237 一格整列拆開 過 %d / 剔除 %d · 段落標題改正 %d · 完全重複只留一筆(移出 %d)" % (len(add), len(rj), nsec, len(dup)))
    return basic, fin, summ, gaps, made


# ===== B U/I「驗證過的輸出」分頁:每份個股的基本資料 / 一標題四重點 / 年度數據(每格值 + 驗證徽章)· 獨立驗證器寫回 window.VRN2_IV(指紋對才套用)=====
_VO_KEYS = ("FILENAME", "PAGE", "TABLE", "ITEM", "PERIOD", "SUBCOL", "VALUE")


def _vo_fp(fin: list) -> str:
    """年度數據冊指紋(獨立驗證器各自實作同一算法 · 不 import):逐筆 7 欄串接 → SHA-256 前 16 碼。"""
    import hashlib
    h = hashlib.sha256()
    for r in fin:
        h.update(("\x1f".join(str(r.get(k, "")) for k in _VO_KEYS) + "\x1e").encode("utf-8"))
    return h.hexdigest()[:16]


def _vo_data(basic: list, fin: list, summ: list) -> dict:
    """嵌入頁面的資料(字串表去重):每份檔 {f, b: [[欄, 值, VRN-2 狀態]], s: [[欄, 文字]], r: [[冊內序號, 頁, 表, 列, 段落, 科目, 期間, 子欄, 值, VRN-2 驗證]]}。"""
    S, si = [], {}

    def sx(t):
        t = "" if t is None else str(t)
        if t not in si:
            si[t] = len(S)
            S.append(t)
        return si[t]
    files, order = {}, []
    for b in basic:
        f = b["FILENAME"]
        st = b.get("_STATUS") or {}
        files[f] = {"f": f, "b": [[k, "" if v is None else str(v), str(st.get(k, ""))] for k, v in b.items() if k not in ("FILENAME", "_STATUS")], "s": [], "r": []}
        order.append(f)
    for s in summ:
        e = files.setdefault(s["FILENAME"], {"f": s["FILENAME"], "b": [], "s": [], "r": []})
        if s["FILENAME"] not in order:
            order.append(s["FILENAME"])
        e["s"] = [[k, "" if s.get(k) is None else str(s.get(k))] for k in ("TITLE", "POINT_1", "POINT_2", "POINT_3", "POINT_4", "POINTS_OK") if k in s]
    for i, x in enumerate(fin):
        e = files.setdefault(x["FILENAME"], {"f": x["FILENAME"], "b": [], "s": [], "r": []})
        if x["FILENAME"] not in order:
            order.append(x["FILENAME"])
        e["r"].append([i, x.get("PAGE", ""), sx(x.get("TABLE")), x.get("ROW") or 0, sx(x.get("SECTION")), sx(x.get("ITEM")), sx(x.get("PERIOD")), sx(x.get("SUBCOL")), str(x.get("VALUE", "")), sx(x.get("VERIFY"))])
    return {"tag": TAG, "fp": _vo_fp(fin), "n": len(fin), "S": S, "F": [files[f] for f in order]}


_VO_CSS = ("#vrn2vo .vo-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:6px 0}#vrn2vo select,#vrn2vo input[type=search]{font:12px system-ui;padding:3px 6px;border:1px solid #d1d5db;border-radius:6px}"
           "#vrn2vo button{font:12px system-ui;padding:3px 9px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer}#vrn2vo .vo-iv{padding:4px 8px;border-radius:6px;margin:4px 0}"
           "#vrn2vo .ivg{background:#dcfce7}#vrn2vo .ivy{background:#fef9c3}#vrn2vo .ivr{background:#fee2e2}#vrn2vo .ivu{background:#f3f4f6}"
           "#vrn2vo td.g{background:#dcfce7}#vrn2vo td.y{background:#fef9c3}#vrn2vo td.r{background:#fecaca}#vrn2vo td.u{background:#eff6ff}"
           "#vrn2vo .vo-grid td,#vrn2vo .vo-grid th{white-space:nowrap;word-break:normal}#vrn2vo .vo-grid td.it{white-space:normal;min-width:160px}#vrn2vo .vo-sec td{background:#f9fafb;font-weight:600}"
           "#vrn2vo .bd{font-size:10px;margin-left:3px}#vrn2vo .vo-tb{margin:10px 0 2px;font-weight:700}#vrn2vo .vo-wrap{overflow-x:auto}#vrn2vo .vo-ov tr{cursor:pointer}#vrn2vo .vo-ov tr.sel td{background:#e0f2fe}"
           "#vrn2vo .vo-lg span{display:inline-block;padding:1px 6px;border-radius:4px;margin-right:6px}")

_VO_JS = r"""<script>(function(){
var h=document.getElementById('vrn2vo-h'),box=document.getElementById('vrn2vo');
var first=[].slice.call(document.querySelectorAll('h2,h3')).filter(function(x){return x.parentNode===h.parentNode&&x!==h;})[0];
if(first){var a=h.compareDocumentPosition(first);if(a&Node.DOCUMENT_POSITION_PRECEDING){first.parentNode.insertBefore(h,first);first.parentNode.insertBefore(box,first);}}
var D=JSON.parse(document.getElementById('vrn2-vo-data').textContent),S=D.S;
var IV=window.VRN2_IV||null,ivOk=!!(IV&&IV.fp===D.fp&&IV.n===D.n&&IV.fin&&IV.fin.length===D.n);
var GOOD={ALIGNED:1,SUBALIGNED:1,TRANSALIGNED:1},WARN={PRESENT:1,OCR:1};
function e(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function fv(i){return ivOk?IV.fin[i]:null;}
function cl(i){if(!ivOk)return 'u';var v=fv(i);if(!v)return 'r';return GOOD[v[0]]?'g':(WARN[v[0]]?'y':'r');}
function bdg(c){return {g:'✓✓',y:'◐',r:'✗',u:'✓'}[c];}
function bstat(v){if(!v)return 'u';return v.indexOf('PASS')===0?'g':(v.indexOf('EST')===0||v.indexOf('OCR')===0?'y':'r');}
function bchk(f,k){if(!ivOk||!IV.basic||!IV.basic[f])return null;var c=IV.basic[f],o=[];for(var x in c){if(x===k||x.indexOf(k+':')===0)o.push(c[x]);}if(!o.length)return null;var bad=o.filter(function(z){return z.indexOf('PASS')!==0;});return bad.length?bad[0]:o[0];}
function schk(f,k){if(!ivOk||!IV.summary||!IV.summary[f])return null;return IV.summary[f][k]||null;}
function cnt(F){var c={g:0,y:0,r:0,u:0};F.r.forEach(function(r){c[cl(r[0])]++;});return c;}
var bar=document.getElementById('vo-ivbar');
if(ivOk){var fc=IV.counts&&IV.counts.fin||{},tot=0,good=0,warn=0;for(var k in fc){tot+=fc[k];if(GOOD[k])good+=fc[k];else if(WARN[k])warn+=fc[k];}
 var bc=IV.counts.basic||{},sc=IV.counts.summary||{};
 bar.className='vo-iv '+(tot-good-warn?'ivr':(warn?'ivy':'ivg'));
 bar.textContent='獨立驗證 '+IV.ver+' · '+IV.ts+' · 冊指紋 '+IV.fp+' 與本頁相同(驗的就是這一頁的值)· 年度數據 '+tot+' 筆:✓✓ 對位 '+good+' · ◐ 人工核對 '+warn+' · ✗ 不過 '+(tot-good-warn)+' · 基本資料 PASS '+(bc.PASS||0)+' / '+Object.keys(bc).reduce(function(s,k){return s+bc[k];},0)+' · 一標題四重點 PASS '+(sc.PASS||0)+' / '+Object.keys(sc).reduce(function(s,k){return s+sc[k];},0);}
else if(IV){bar.className='vo-iv ivr';bar.textContent='獨立驗證結果是別一輪的(指紋 '+IV.fp+' ≠ 本頁 '+D.fp+')· 不套用 · 請重跑啟動器';}
else{bar.className='vo-iv ivu';bar.textContent='獨立驗證尚未寫入本頁(啟動器 ⑦ 之後在背景跑 · 跑完寫回並開啟)· 目前顯示 VRN-2 主冊的值(每筆都過 VRN-2 兩個讀取器對欄 · 徽章 ✓)';}
var ov=document.getElementById('vo-ov'),sel=document.getElementById('vo-file'),q=document.getElementById('vo-q'),only=document.getElementById('vo-bad'),one=document.getElementById('vo-one');
var cur=0;try{var sv=localStorage.getItem('vrn2vo-file');D.F.forEach(function(F,i){if(F.f===sv)cur=i;});}catch(x){}
function ovr(){var h='<table class="vo-ov"><tr><th>檔案</th><th>日期</th><th>代號</th><th>券商</th><th>基本資料</th><th>四重點</th><th>年度數據</th><th>✓✓</th><th>◐</th><th>✗</th><th>✓ 未獨立驗</th></tr>';
 D.F.forEach(function(F,i){var b={};F.b.forEach(function(x){b[x[0]]=x[1];});var c=cnt(F),bp=0,bt=0,sp=0,st=0;
  if(ivOk&&IV.basic[F.f]){for(var k in IV.basic[F.f]){bt++;if(IV.basic[F.f][k].indexOf('PASS')===0)bp++;}}
  if(ivOk&&IV.summary[F.f]){for(var k2 in IV.summary[F.f]){st++;if(IV.summary[F.f][k2].indexOf('PASS')===0)sp++;}}
  h+='<tr data-i="'+i+'"'+(i===cur?' class="sel"':'')+'><td>'+e(F.f)+'</td><td>'+e(b.REPORT_DATE)+'</td><td>'+e(b.TICKER)+'</td><td>'+e(b.BROKER)+'</td><td>'+(ivOk?bp+' / '+bt:'—')+'</td><td>'+(ivOk?sp+' / '+st:'—')+'</td><td>'+F.r.length+'</td><td>'+c.g+'</td><td>'+c.y+'</td><td'+(c.r?' style="color:#b91c1c;font-weight:700"':'')+'>'+c.r+'</td><td>'+c.u+'</td></tr>';});
 ov.innerHTML=h+'</table>';[].forEach.call(ov.querySelectorAll('tr[data-i]'),function(tr){tr.addEventListener('click',function(){pick(+tr.dataset.i,true);});});}
function grid(F){var qq=(q.value||'').toLowerCase(),ob=only.checked,tabs=[],tb={};
 F.r.forEach(function(r){var t=S[r[2]];if(!tb[t]){tb[t]={t:t,pg:r[1],rows:[],rk:{},cols:[]};tabs.push(tb[t]);}var T=tb[t],key=(r[3]||0)+'|'+S[r[4]]+'|'+S[r[5]];
  if(!T.rk[key]){T.rk[key]={row:r[3],sec:S[r[4]],it:S[r[5]],cells:{},order:[]};T.rows.push(T.rk[key]);}var R=T.rk[key],ck=S[r[6]]+(S[r[7]]?' · '+S[r[7]]:'');
  if(!R.cells[ck]){R.cells[ck]=[];R.order.push(ck);}R.cells[ck].push(r);});
 var h='';tabs.forEach(function(T){T.rows.sort(function(a,b){return (a.row||0)-(b.row||0);});
  T.rows.forEach(function(R){var prev=-1;R.order.forEach(function(ck){var ix=T.cols.indexOf(ck);if(ix<0){T.cols.splice(prev+1,0,ck);ix=prev+1;}prev=ix;});});
  var body='',lastSec=null,shown=0;
  T.rows.forEach(function(R){var cs=[],any=false;T.cols.forEach(function(ck){var rs=R.cells[ck];if(!rs){cs.push('<td></td>');return;}
    var c=rs.length>1?'r':cl(rs[0][0]);rs.forEach(function(r){if(cl(r[0])!=='g')any=true;});
    var tip=rs.map(function(r){var v=fv(r[0]);return '值 '+r[8]+'\n第 '+r[1]+' 頁 · 表 '+S[r[2]]+(r[3]?' · 第 '+r[3]+' 列':'')+'\nVRN-2:'+S[r[9]]+'\n獨立驗證:'+(v?v[0]+' · '+v[1]:(ivOk?'沒有判決':'尚未寫入'));}).join('\n——\n');
    cs.push('<td class="'+c+'" title="'+e(tip)+'">'+e(rs.map(function(r){return r[8];}).join(' / '))+'<span class="bd">'+bdg(c)+'</span></td>');});
   var hit=!qq||R.it.toLowerCase().indexOf(qq)>=0||R.sec.toLowerCase().indexOf(qq)>=0||cs.join('').toLowerCase().indexOf(qq)>=0;
   if(!hit||(ob&&!any))return;shown++;
   if(R.sec&&R.sec!==lastSec){body+='<tr class="vo-sec"><td colspan="'+(T.cols.length+1)+'">'+e(R.sec)+'</td></tr>';}lastSec=R.sec;
   body+='<tr><td class="it">'+e(R.it)+(R.row?' <span style="color:#9ca3af">#'+R.row+'</span>':'')+'</td>'+cs.join('')+'</tr>';});
  if(shown){h+='<div class="vo-tb">表 '+e(T.t)+' · 第 '+e(T.pg)+' 頁 · '+shown+' 列</div><div class="vo-wrap"><table class="vo-grid"><tr><th>科目</th>'+T.cols.map(function(c){return '<th>'+e(c)+'</th>';}).join('')+'</tr>'+body+'</table></div>';}});
 return h||'<div style="color:#6b7280">'+(F.r.length?'沒有符合條件的列':'這份沒有年度數據')+'</div>';}
function pick(i,scroll){cur=i;sel.value=String(i);try{localStorage.setItem('vrn2vo-file',D.F[i].f);}catch(x){}
 [].forEach.call(ov.querySelectorAll('tr[data-i]'),function(tr){tr.className=(+tr.dataset.i===i)?'sel':'';});
 var F=D.F[i],h='<div class="vo-tb">基本資料</div><table><tr><th>欄位</th><th>值</th><th>VRN-2</th><th>獨立驗證</th></tr>';
 F.b.forEach(function(x){var v=bchk(F.f,x[0]),c=x[1]?(ivOk?bstat(v):'u'):'';h+='<tr><td>'+e(x[0])+'</td><td'+(c?' class="'+c+'"':'')+'>'+e(x[1]||'—')+(c?'<span class="bd">'+bdg(c)+'</span>':'')+'</td><td>'+e(x[2])+'</td><td>'+e(v||(x[1]?(ivOk?'沒有這一欄的檢查':'尚未寫入'):''))+'</td></tr>';});
 h+='</table><div class="vo-tb">一標題四重點</div><table><tr><th>欄位</th><th>內容</th><th>獨立驗證</th></tr>';
 F.s.forEach(function(x){var v=schk(F.f,x[0]),c=(x[1]&&x[0]!=='POINTS_OK')?(ivOk?bstat(v):'u'):'';h+='<tr><td>'+e(x[0])+'</td><td'+(c?' class="'+c+'"':'')+' style="white-space:normal">'+e(x[1]||'—')+(c?'<span class="bd">'+bdg(c)+'</span>':'')+'</td><td>'+e(v||'')+'</td></tr>';});
 one.innerHTML=h+'</table><div class="vo-tb">年度數據('+F.r.length+' 筆)</div>'+grid(F);if(scroll){one.scrollIntoView({block:'start'});}}
D.F.forEach(function(F,i){var o=document.createElement('option');o.value=String(i);o.textContent=F.f;sel.appendChild(o);});
sel.addEventListener('change',function(){pick(+sel.value,false);});q.addEventListener('input',function(){pick(cur,false);});only.addEventListener('change',function(){pick(cur,false);});
document.getElementById('vo-csv').addEventListener('click',function(){var F=D.F[cur],L=[['FILENAME','PAGE','TABLE','ROW','SECTION','ITEM','PERIOD','SUBCOL','VALUE','VRN2_VERIFY','IV_VERDICT','IV_NOTE']];
 F.r.forEach(function(r){var v=fv(r[0])||['',''];L.push([F.f,r[1],S[r[2]],r[3]||'',S[r[4]],S[r[5]],S[r[6]],S[r[7]],r[8],S[r[9]],v[0],v[1]]);});
 var csv='﻿'+L.map(function(a){return a.map(function(x){x=String(x==null?'':x);return /[",\n]/.test(x)?'"'+x.replace(/"/g,'""')+'"':x;}).join(',');}).join('\r\n');
 var u=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=u;a.download='VRN2_Verified_'+F.f.replace(/\.pdf$/i,'')+'.csv';document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(u);a.remove();},500);
 document.getElementById('vo-st').textContent='已下載 '+a.download;});
ovr();pick(cur<D.F.length?cur:0,false);window.VRN2_VO={data:D,ivOk:ivOk,pick:pick};
})();</script>"""


def _vo_html(basic: list, fin: list, summ: list) -> str:
    """v0237 U/I 分頁「驗證過的輸出」(放在第一個分頁)· 資料 JSON 內嵌(「<」跳脫)· 獨立驗證佔位 <script id="vrn2-iv">(啟動器跑完獨立驗證後寫回)。"""
    data = json.dumps(_vo_data(basic, fin, summ), ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return ("<h2 id='vrn2vo-h' style='margin-top:14px'>驗證過的輸出(每格值 + 驗證徽章 · ✓✓ = VRN-2 兩讀取器 + 獨立驗證都對位 · ◐ 人工核對 · ✗ 不過 · ✓ 只有 VRN-2 驗證)</h2>"
            "<div id='vrn2vo'><style>%s</style><div id='vo-ivbar' class='vo-iv ivu'></div>"
            "<div class='vo-lg' style='font-size:11px;color:#374151'><span class='g' style='background:#dcfce7'>✓✓ 兩層都過</span><span style='background:#eff6ff'>✓ VRN-2 驗證(獨立驗證未寫入)</span>"
            "<span style='background:#fef9c3'>◐ 值在原文 · 欄位人工核對</span><span style='background:#fecaca'>✗ 獨立驗證不過(先看原文)</span> 滑鼠停在格子上看驗證細節</div>"
            "<div id='vo-ov'></div><div class='vo-bar'><label>檔案 <select id='vo-file'></select></label><input type='search' id='vo-q' placeholder='搜尋科目 / 值 / 段落'>"
            "<label><input type='checkbox' id='vo-bad'> 只看待核對(非 ✓✓)</label><button type='button' id='vo-csv'>⤓ 下載本檔 CSV(值 + 驗證)</button><span id='vo-st' style='color:#1d4ed8'></span></div>"
            "<div id='vo-one'></div></div>"
            "<script type='application/json' id='vrn2-vo-data'>%s</script><script id=\"vrn2-iv\">window.VRN2_IV=null;</script>%s") % (_VO_CSS, data, _VO_JS)


def _out_html(basic: list, fin: list, summ: list) -> str:
    """v0236 頁面段落 + v0237「驗證過的輸出」分頁。"""
    return PRIOR._out_html(basic, fin, summ) + _vo_html(basic, fin, summ)


vrn2 = _rebind(PRIOR.vrn2)                                                # 同一段 vrn2(v0231 程式碼)· 用到本版 _out_books / _out_html
_success_register = _rebind(PRIOR._success_register)                      # 登記本版(__file__ = v0237)


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
    import hashlib
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    td = Path(tempfile.mkdtemp(prefix="v0237-"))
    (td / "scope_in").mkdir()
    pdf = td / "scope_in" / "TP-2637 20260101.pdf"
    ok_pdf = False
    try:
        from reportlab.pdfgen import canvas as _cv
        cv = _cv.Canvas(str(pdf), pagesize=(595, 842))
        cv.setFont("Helvetica", 9)
        put = lambda x, y, t: cv.drawString(x, y, t)                       # noqa: E731
        for x, t in ((150, "Dec-23A"), (190, "Dec-24A"), (230, "Dec-25A"), (420, "Dec-23A"), (460, "Dec-24A"), (500, "Dec-25A")):
            put(x, 700, t)                                                 # 左右兩張並排表各自的表頭
        for y, lab, vs, lab2, vs2 in ((686, "Current ratio (x)", ("0.6", "0.8", "1.0"), "Gross margin", ("20.5%", "33.3%", "23.9%")),
                                      (672, "EPS (NT$)", ("4.38", "8.08", "5.27"), "Asset turnover", ("0.2", "0.3", "0.2"))):
            put(50, y, lab)
            for x, v in zip((155, 195, 235), vs):
                put(x, y, v)
            put(320, y, lab2)
            for x, v in zip((425, 465, 505), vs2):
                put(x, y, v)
        put(50, 500, "EPS (NT$)")                                          # 同一頁別張表也印著同一列(區外)→ 只取區內那一列
        for x, v in zip((155, 195, 235), ("4.38", "8.08", "5.27")):
            put(x, 500, v)
        cv.save()
        ok_pdf = True
    except Exception as e:  # noqa: BLE001
        print("  [計] 自測 PDF 產生不了(%s)→ 一格整列自測判紅" % type(e).__name__)
    if ok_pdf:
        rows = [["", "Dec-23A", "Dec-24A", "Dec-25A"], ["Current ratio (x) 0.6 0.8 1.0", "", "", ""], ["Gross margin", "20.5%", "33.3%", "23.9%"],
                ["EPS (NT$) 4.38 8.08 5.27", "", "", ""], ["Asset turnover", "0.2", "0.3", "0.2"], ["Quick ratio (x) 0.6 0.9 1.0", "", "", ""]]
        z = {"id": "P1·F·02·TB", "minor": "TB", "minor_zh": "財報表", "bbox": [45, 842 - 710, 560, 842 - 660], "rows": rows}
        res = [{"file": pdf.name, "pages": [{"pno": 1, "zones": [z]}]}]
        basic = [{"FILENAME": pdf.name, "REPORT_DATE": "2026-01-01", "TICKER": "2637", "BROKER": "T"}]
        fin0 = [{"FILENAME": pdf.name, "TABLE": "P1·F·02·TB", "ITEM": "Asset turnover", "PERIOD": "Dec-23A", "VALUE": "0.2", "ROW": 5, "SECTION": "EPS (NT$) 4.38 8.08 5.27"}]
        kp, rj, ns = _mg_fin(res, basic, fin0, td)
        got = sorted((x["ITEM"], x["PERIOD"], x["VALUE"]) for x in kp)
        chk("⓪ v0237 一格整列拆開:Current ratio / EPS 各 3 期 · 兩個讀取器都對到左表表頭(右邊並排表同期間字不混 · 區外同一列不算重複)→ %s" % got,
            got == sorted([("Current ratio (x)", "Dec-23A", "0.6"), ("Current ratio (x)", "Dec-24A", "0.8"), ("Current ratio (x)", "Dec-25A", "1.0"),
                           ("EPS (NT$)", "Dec-23A", "4.38"), ("EPS (NT$)", "Dec-24A", "8.08"), ("EPS (NT$)", "Dec-25A", "5.27")])
            and all("pdfplumber 再驗" in x["VERIFY"] and x["ROW"] in (2, 4) for x in kp))
        chk("⓪ v0237 擷取的值跟原文那一列不同(Quick ratio 0.9 · 原文沒有這一列)→ 剔除冊 3 筆(帶理由)· 不進主冊",
            len(rj) == 3 and all(x["ITEM"] == "Quick ratio (x)" and "一格整列" in x["REASON"] for x in rj) and not [x for x in kp if x["ITEM"].startswith("Quick")])
        chk("⓪ v0237 整列數據誤當段落標題 → 既有列的 SECTION 改回(%r)· 改正 %d" % (fin0[0]["SECTION"], ns), ns == 1 and fin0[0]["SECTION"] == "")
        dd_k, dd_d = _dedupe([{"FILENAME": "a", "TABLE": "T", "ROW": 3, "ITEM": "攤提", "PERIOD": "Dec-26F", "VALUE": "(1)"}] * 2 + [{"FILENAME": "a", "TABLE": "T", "ROW": 3, "ITEM": "攤提", "PERIOD": "Dec-27F", "VALUE": "(1)"}])
        chk("⓪ v0237 同一列同期間同值兩筆 → 留一筆 · 一筆進剔除冊(帶理由)· 別的期間同值不動", len(dd_k) == 2 and len(dd_d) == 1 and "重複" in dd_d[0]["REASON"])
        chk("⓪ v0237 _mg_split:科目結尾是括號也拆得開 · 只有數字 / 只有一個值不拆",
            _mg_split("流動比率 (x) 0.6 0.8 1.0") == ("流動比率 (x)", ["0.6", "0.8", "1.0"]) and _mg_split("2023 2024") is None and _mg_split("EPS 4.38") is None)
    else:
        chk("⓪ v0237 一格整列自測(需 reportlab 產生測試 PDF)", False)
    bs = [{"FILENAME": "a.pdf", "TICKER": "1", "TARGET_PRICE": "100", "_STATUS": {"TARGET_PRICE": "原文"}}]
    fs = [{"FILENAME": "a.pdf", "PAGE": 1, "TABLE": "T", "ITEM": "Revenue", "PERIOD": "2026E", "VALUE": "</script><b>1"}, {"FILENAME": "a.pdf", "PAGE": 1, "TABLE": "T", "ITEM": "Revenue", "PERIOD": "2027E", "VALUE": "2"}]
    hv = _vo_html(bs, fs, [{"FILENAME": "a.pdf", "TITLE": "T", "POINT_1": "p"}])
    js = hv.split("<script type='application/json' id='vrn2-vo-data'>", 1)[1].split("</script>", 1)[0]
    dd = json.loads(js)
    chk("⓪ v0237 驗證過的輸出分頁:h2 · 資料 JSON 可解析 · 值裡的 </script> 已跳脫 · 獨立驗證佔位在", "<h2 id='vrn2vo-h'" in hv and dd["n"] == 2 and dd["F"][0]["r"][0][8] == "</script><b>1"
        and '<script id="vrn2-iv">window.VRN2_IV=null;</script>' in hv and "</script><b>" not in js)
    fp_ = hashlib.sha256(("".join("\x1f".join(str(r.get(k, "")) for k in _VO_KEYS) + "\x1e" for r in fs)).encode("utf-8")).hexdigest()[:16]
    chk("⓪ v0237 冊指紋 = 7 欄 \\x1f 串接 · \\x1e 分筆 · SHA-256 前 16 碼(與獨立驗證器同一算法)", dd["fp"] == fp_ == _vo_fp(fs))
    chk("⓪ v0237 前版必須是 v0236 → %s" % getattr(PRIOR, "TAG", "?"), getattr(PRIOR, "TAG", "") == "v0236")
    chk("⓪ v0237 零替換:vrn2 是同一段程式(重新綁定)", vrn2.__code__ is PRIOR.vrn2.__code__ and vrn2.__globals__ is globals())
    try:
        _ob = _out_books([], [], [], td)
        _ob_err = ""
    except BaseException as e:  # noqa: BLE001 — 自測要把遞迴 / 例外當紅燈報出
        _ob, _ob_err = (), type(e).__name__
    chk("⓪ v0237 輸出冊(本版 → v0236 → … → v0232)空輸入跑完不遞迴 %s" % (_ob_err or "· 回傳 %d 項" % len(_ob)), not _ob_err and len(_ob) == 5)
    try:
        _cm = completion(0, 1, 1, True, {}, []).get("manager")
    except Exception as e:  # noqa: BLE001
        _cm = "例外 %s" % type(e).__name__
    chk("⓪ v0237 完成判定的管理器欄 = 實際尾版 → %s" % _cm, _cm == "VRN-2 SystemManager v0237")
    print("  ── 前版 v0236 自測(原樣)──")
    rc_p = PRIOR.selftest()
    chk("⓪ 前版 %s 自測 rc %d" % (PRIOR_PATH.name, rc_p), rc_p == 0)
    print("[計] %s %s(%s)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, Path(__file__).name, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

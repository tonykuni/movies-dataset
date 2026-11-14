#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0270 — 薄尾:extract 表格解析三修(左右並排表拆開 · 多層表頭合欄 · 期間表頭把關)。

操作員令(2026-11-14):「修 VRN-2 表格解析,開 PR 並盯著」;「VRN-2 為主,若功能不足 VRN-1 為輔,整合後統稱 VRN」(L128)。
實測(容器 13 份 + 操作員工作站 C:\測試樣本報告 97 份 · ERROR 0):數字都抓得到,但兩種版面把數字掛錯期間,而且照樣報 READ:
  · 左右並排兩張表(例 晶心科 6533 第 5 頁:左資產負債表 2021–3Q25、右損益表 2023–2027F)被當成一張 11 期的表
    → 「流動資產 2023 = 1」這種錯值(其實是右表的營業成本)。
  · 兩層表頭(例 同檔第 3 頁:上層 3Q25 / 4Q25(F),下層 實際數 · 預估 · 差異 · 市場共識)→ 期間表頭找不到,
    前版的期間規則把兩位數 76 · 29 當成年份,資料列被選成表頭 → 期間變成 (24) · 76 · - · 29。
本版(前版一字不動;只在 extract 的行程裡換三個函式):
  ① 抓表後先拆:表中間出現第二條「列標欄」(多數是文字),而且左右兩邊表頭各有 ≥2 個真期間 → 拆成兩張表(各自重建)。
     證據要兩樣都齊才拆(評等表中間的 Buy / Hold 文字欄不會被拆)。
  ② 多層表頭:第一列是期間群組(橫跨多欄)、第二列是子欄(實際數 / 預估 / 差異 …)→ 欄名 =「3Q25 實際數」這種合欄,不再把資料列當表頭。
     合欄後照鏈上同一套算術驗(v0128 _arith_28:毛利 = 營收 − 成本 · 三率),只驗值欄、差異 / % 欄不驗;不符記 issue 改待審。
  ③ 期間把關:重建後期間欄出現數字殘片(76 · (24) · - · -12.2%)或同一期間重複 → 記 issue「期間表頭可疑」,這張表改待審,
     不冒充 READ。QoQ / YoY / 差異 這類比較欄、連續兩位數年(22 · 23 · 24F · 23 · 24F,預估年一起算)照常放行。
號:VRN-2 私有 runtime 線(桌機)已用到 v0269,本版取下一個空號 v0270。
extract 一律在本行程跑 v0262 那條鏈(桌機上前版是 v0269 單檔、extract 走子行程轉交,改在本行程跑才吃得到這三修);
其餘動詞照前版(glob 取比本版小的最大版號)。零網路 · 不碰 TA-Lib · 不讀寫同意閘。
自測:python VRN_SystemManager_v0270.py --selftest(本版 9 項 + v0262 鏈自測)。
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

import importlib.util
import os
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0270"
DISPLAY_NAME = "VRN-2 SystemManager"
FAMILY = "VRN_SystemManager"
HOST_NAME = "VRN_SystemManager_v0262.py"              # extract 鏈的主(v0127 擷取本體 + v0128–v0132 修 + v0133… 其餘)
P27_NAME = "VRN_SystemManager_v0127.py"
SAMPLE_PDF = HERE / "intake/VRN_v0108_Annual/VRN_v0108_Complete_Handover/pack/engine/fixtures/REAL_TEST_INPUT/晶心科(6533,N,中立)-CTBC251208.pdf"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vrn_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


_HOST = {"mod": None, "p27": None, "orig": None, "arith": None}


def host():
    """extract 鏈的主(v0262 模組;main 上就是前版)。"""
    if _HOST["mod"] is None:
        _HOST["mod"] = PRIOR if PRIOR_PATH.name == HOST_NAME else _load(HERE / HOST_NAME, "vrn_extract_host_for_" + TAG)
    return _HOST["mod"]


def p27():
    """沿 extract 鏈往回找 v0127(擷取本體:_rebuild_table · _tables_* · extract_one 都掛在它模組全域)。"""
    if _HOST["p27"] is None:
        cur, seen = host(), set()
        while cur is not None and id(cur) not in seen:
            seen.add(id(cur))
            if Path(getattr(cur, "__file__", "") or "").name == P27_NAME:
                _HOST["p27"] = cur
                break
            cur = vars(cur).get("PRIOR")
        if _HOST["p27"] is None:
            raise RuntimeError("extract 本體 %s 沿鏈找不到" % P27_NAME)
    return _HOST["p27"]


# ────────────────── 期間 ──────────────────
_STRICT_RX = re.compile(
    r"^(?:FY)?(?:19|20)\d{2}(?:[AEFPR]|\([AEFP]\))?$"            # 2024 · 2025F · 2026(F) · FY2024
    r"|^(?:FY)?\d{2}[AEF]$|^FY\d{2}$"                            # 25F · FY24
    r"|^[1-4]Q(?:FY)?\d{2,4}(?:[AEF]|\([AEF]\))?$"               # 3Q25 · 4Q25(F)
    r"|^(?:[12]H|H[12])(?:FY)?\d{2,4}(?:[AEF]|\([AEF]\))?$"      # 1H25 · H2FY24
    r"|^1[01]\d年(?:度|[1-4]季)?$|^(?:19|20)\d{2}年(?:度|[1-4]季|上半年|下半年)?$"
    r"|^(?:19|20)\d{2}[/.\-](?:0?[1-9]|1[0-2])$", re.I)
_CMP_RX = re.compile(r"^(?:QoQ|YoY|MoM|HoH|CAGR|y/y|q/q|Δ|chg|change|diff|差異|變動|增減|年增率?|季增率?|月增率?|成長率|年成長率|季成長率)", re.I)


def _cl(s) -> str:
    return p27()._clean_cell(s)


def strict_period(s) -> bool:
    return bool(_STRICT_RX.match(_cl(s).replace(" ", "")))


_YY_RX = re.compile(r"(\d{2})(?:[AEF]|\([AEF]\))?", re.I)


def _two_digit_years(tokens: list) -> bool:
    """連續遞增的兩位數年(22 · 23 · 24F · 25(F))= 期間;其他兩位數(76 · 29)不是。"""
    ys = []
    for t in tokens:
        m = _YY_RX.fullmatch(t.replace(" ", ""))
        if not m:
            return False
        ys.append(int(m.group(1)))
    return len(ys) >= 2 and all(b - a == 1 for a, b in zip(ys, ys[1:]))


# ────────────────── ① 左右並排拆表 ──────────────────
def _texty(c: str) -> bool:
    return bool(c) and p27()._to_num(c) is None and not strict_period(c) and bool(re.search(r"[A-Za-z\u4e00-\u9fff]", c))


def split_side_by_side(tbl: dict, depth: int = 0) -> list:
    rows = [[_cl(c) for c in r] for r in tbl.get("rows") or []]
    if not rows or depth > 2:
        return [tbl]
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    body = [r for r in rows if any(r)]
    if w < 5 or len(body) < 4:
        return [tbl]
    head = body[:3]
    for j in range(2, w - 1):
        if max(sum(1 for c in r[1:j] if strict_period(c)) for r in head) < 2:
            continue
        if max(sum(1 for c in r[j + 1:] if strict_period(c)) for r in head) < 2:
            continue
        col = [r[j] for r in body[1:] if r[j]]
        if len(col) < 3 or sum(1 for c in col if _texty(c)) < 0.6 * len(col):
            continue
        left, right = [r[:j] for r in rows], [r[j:] for r in rows]
        if not any(p27()._to_num(c) is not None for r in left for c in r[1:]) or not any(p27()._to_num(c) is not None for r in right for c in r[1:]):
            continue
        bb = tbl.get("bbox")
        cut = (bb[0] + (bb[2] - bb[0]) * j / w) if bb and len(bb) == 4 else None

        def part(rs, side):
            b = None if cut is None else ([bb[0], bb[1], round(cut, 1), bb[3]] if side == "L" else [round(cut, 1), bb[1], bb[2], bb[3]])
            return dict(tbl, rows=[r for r in rs if any(r)], bbox=b or bb, layout_split="%s@%d/%d" % (side, j, w))
        return [part(left, "L")] + split_side_by_side(part(right, "R"), depth + 1)
    return [tbl]


def _wrap_tables(fn):
    def tables(*a, **kw):
        out = []
        for t in fn(*a, **kw) or []:
            out.extend(split_side_by_side(t))
        return out
    tables.__name__ = getattr(fn, "__name__", "tables") + "_v0270"
    tables._v0270_inner = fn
    return tables


# ────────────────── ② 多層表頭 ──────────────────
def composite_header(rows: list):
    """第一列 = 期間群組(橫跨多欄)、第二列 = 子欄(非期間 · 非數字)→ [合欄名] · 資料列 · 表題;不是這種版面回 None。"""
    rows = [[_cl(c) for c in r] for r in rows if any(_cl(c) for c in r)]
    if len(rows) < 3:
        return None
    w = max(len(r) for r in rows)
    r0, r1 = rows[0] + [""] * (w - len(rows[0])), rows[1] + [""] * (w - len(rows[1]))
    groups = [c for c in r0[1:] if c]
    subs = [c for c in r1[1:] if c]
    if not groups or not all(strict_period(g) for g in groups) or len(subs) < 2 or len(groups) >= len(subs):
        return None
    if any(strict_period(s) or p27()._to_num(s) is not None for s in subs):
        return None
    grp, cur = [], ""
    for j in range(1, w):
        cur = r0[j] or cur
        grp.append(cur)
    lab = []
    for k, j in enumerate(range(1, w)):
        sub = r1[j]
        same = [r1[i + 1] for i in range(len(grp)) if grp[i] == grp[k]]
        if sub and same.count(sub) > 1 and k > 0 and r1[j - 1] and grp[k - 1] == grp[k]:
            sub = "%s(%s)" % (sub, r1[j - 1])                    # 同群重複的子欄(差異 · 差異)→ 標它比的是哪一欄
        lab.append((grp[k] + " " + sub).strip() if sub else grp[k])
    if len(set(lab)) < len(lab):
        return None
    return lab, rows[2:], (r0[0] or r1[0])


_DIFF_SUB_RX = re.compile(r"差異|變動|增減|差額|%|率|YoY|QoQ|MoM|HoH|y/y|q/q|Δ|chg|change|diff|vs\.?", re.I)


def _value_col(label: str) -> bool:
    """合欄名的子欄是「值」(實際數 · 預估數 · 財測)才進算術;差異 / 變動 / 年增率 / % 那幾欄不是同一個量,不拿來驗。"""
    sub = label.split(" ", 1)[1] if " " in label else ""
    return not (sub and _DIFF_SUB_RX.search(sub))


def chain_arith():
    """鏈上現行的算術核:v0128 的 _arith_28(毛利率 0.4 / 40 都收)優先,沒有就用 v0127 的 _arith。"""
    if _HOST["arith"] is None:
        cur, seen, fn = host(), set(), None
        while cur is not None and id(cur) not in seen and fn is None:
            seen.add(id(cur))
            fn = vars(cur).get("_arith_28")
            cur = vars(cur).get("PRIOR")
        _HOST["arith"] = fn or p27()._arith
    return _HOST["arith"]


def composite_arith(matrix: dict) -> list:
    """多層表頭表照鏈上同一套算術驗(毛利 = 營收 − 成本 · 三率),只驗值欄(PR 638 · Codex P1)。"""
    g = {k: {per: v for per, v in d.items() if _value_col(per)} for k, d in matrix.items()}
    return list(chain_arith()({k: d for k, d in g.items() if d}))


def rebuild_composite(lab: list, body: list, title: str, lex: list) -> dict:
    P = p27()
    out_rows, matrix = [], defaultdict(dict)
    for r in body:
        label = _cl(r[0]) if r else ""
        if not label:
            continue
        cat, std = P._std_label(label, lex)
        vals = {}
        for j, c in enumerate(r[1:]):
            if j >= len(lab):
                break
            v = P._to_num(c)
            if v is not None:
                vals[lab[j]] = v
                if std:
                    matrix[std][lab[j]] = v
        out_rows.append({"label_raw": label, "label_std": std, "cat": cat, "values": vals,
                         "periods_est": any(re.search(r"[EF]\)?$", k.split(" ")[0], re.I) for k in vals)})
    cat, conf = P._classify_table(out_rows)
    issues = composite_arith(matrix) if cat in ("IS", "FORECAST") else []
    return {"category": cat, "confidence": conf, "periods": lab, "rows": out_rows, "matrix": dict(matrix), "issues": issues,
            "notes": [title] if title else [], "layout_note": "多層表頭(上層期間 × 下層子欄)",
            "unmatched_labels": [r["label_raw"] for r in out_rows if not r["label_std"] and r["values"]][:30]}


# ────────────────── ③ 期間把關 ──────────────────
def period_issue(periods: list) -> str:
    pers = [p for p in (periods or []) if p and not re.fullmatch(r"c\d+", p)]
    junk = [p for p in pers if not strict_period(p) and not _CMP_RX.match(p.replace(" ", ""))
            and (p27()._to_num(p) is not None or p.strip() in ("-", "—", "–"))]
    if junk:                                                       # 22 · 23 · 24F:整串兩位數年連同預估年一起看(PR 638 · Codex P2)
        yy = [p for p in pers if _YY_RX.fullmatch(p.replace(" ", ""))]
        if _two_digit_years(yy) and set(junk) <= set(yy):
            junk = []
    dup = sorted({p for p in pers if strict_period(p) and pers.count(p) > 1})
    if not junk and not dup:
        return ""
    return "期間表頭可疑:" + ("數字殘片 %s" % junk[:4] if junk else "") + (" · " if junk and dup else "") + ("期間重複 %s" % dup[:3] if dup else "")


def _wrap_rebuild(fn):
    def rebuild(tbl: dict, lex: list) -> dict:
        comp = composite_header(tbl.get("rows") or [])
        rb = rebuild_composite(*comp, lex) if comp else fn(tbl, lex)
        if tbl.get("layout_split"):
            rb["layout_note"] = (str(rb.get("layout_note") or "") + ";左右並排拆出 " + tbl["layout_split"]).strip(";")
        if rb.get("category") not in ("TEXT_BLOCK", "INFO", "OTHER") and not comp:
            why = period_issue(rb.get("periods"))
            if why:
                rb["issues"] = list(rb.get("issues") or []) + [why]
        return rb
    rebuild.__name__ = "_rebuild_table_v0270"
    rebuild._v0270_inner = fn
    return rebuild


def install() -> dict:
    """把三修掛上 extract 本體(冪等);回原函式以便自測還原。"""
    P = p27()
    if _HOST["orig"] is None:
        _HOST["orig"] = {n: getattr(P, n) for n in ("_tables_pdfplumber", "_tables_camelot", "_tables_tabula", "_rebuild_table")}
    o = _HOST["orig"]
    P._tables_pdfplumber, P._tables_camelot, P._tables_tabula = (_wrap_tables(o["_tables_pdfplumber"]), _wrap_tables(o["_tables_camelot"]),
                                                                 _wrap_tables(o["_tables_tabula"]))
    P._rebuild_table = _wrap_rebuild(o["_rebuild_table"])
    return o


def uninstall() -> None:
    if _HOST["orig"]:
        for n, f in _HOST["orig"].items():
            setattr(p27(), n, f)


# ────────────────── 動詞 ──────────────────
def collect() -> dict:
    """VCGC 子系統對接口(照前版 · 只讀)· served_by 記本版。"""
    out = host().collect()
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = FAMILY + "_" + TAG
        out["served_by"] = sb
    return out


def provenance(args: list) -> int:
    """同 v0262:直送 ENG114 尾版;`--selftest` 之後再跑本版自測,回傳碼取大。"""
    h = host()
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    rc = int(h._load_engine(h.provenance_engine_path()).main(list(args)) or 0)
    if "--selftest" in args:
        print("  ── 來源回歸之後:本版管理器自測 ──", flush=True)
        rc = max(rc, int(selftest() or 0))
    return rc


def extract(args: list) -> int:
    """extract 在本行程跑 v0262 鏈(掛上三修)。"""
    install()
    return int(host().main(["extract", *args]) or 0)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["provenance"]:
        return provenance(args[1:])
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    if args[:1] == ["extract"]:
        return extract(args[1:])
    return PRIOR.main(args)


def selftest() -> int:
    print("[計] %s %s 自測開始(本版 9 項 · 再 v0262 鏈)" % (DISPLAY_NAME, TAG), flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    chk("① 真期間:2024 · 2025F · 2026(F) · 3Q25 · 4Q25(F) · 1H25 · FY24 · 25F · 113年 是;76 · (24) · -12.2% · YoY · 實際數 不是",
        all(strict_period(x) for x in ("2024", "2025F", "2026(F)", "3Q25", "4Q25(F)", "1H25", "FY24", "25F", "113年"))
        and not any(strict_period(x) for x in ("76", "(24)", "-12.2%", "YoY", "實際數")))
    p5 = {"engine": "pdfplumber", "bbox": [36.0, 100.0, 560.0, 750.0], "rows": [
        ["資產負債表", "", "", "", "", "", "損益表", "", "", "", ""],
        ["(百萬元)", "2021", "2022", "2023", "2024", "3Q25", "(百萬元)", "2023", "2024", "2025F", "2026F"],
        ["資產總計", "5,029", "5,424", "5,336", "5,301", "6,334", "營業收入淨額", "1,058", "1,382", "1,657", "2,169"],
        ["流動資產", "4,495", "4,422", "3,602", "2,767", "2,370", "營業成本", "1", "1", "1", "1"],
        ["現金及約當現金", "4,005", "4,098", "1,890", "2,083", "984", "營業毛利淨額", "1,057", "1,381", "1,656", "2,168"],
        ["應收帳款與票據", "155", "111", "200", "224", "270", "營業費用", "1,325", "1,657", "1,854", "1,873"]]}
    parts = split_side_by_side(p5)
    rate = {"engine": "pdfplumber", "bbox": None, "rows": [
        ["公司", "代號", "評等", "目標價", "2025F", "2026F"], ["台積電", "2330", "Buy", "1,500", "45.1", "52.3"],
        ["聯發科", "2454", "Hold", "1,300", "60.2", "66.0"], ["日月光", "3711", "Buy", "180", "9.1", "10.4"], ["鴻海", "2317", "Buy", "250", "12.0", "13.2"]]}
    chk("② 左右並排:拆成兩張(左 2021–3Q25 · 右 2023–2026F · bbox 按欄比例切)· 評等表中間的 Buy/Hold 文字欄不拆",
        len(parts) == 2 and parts[0]["rows"][1][1:] == ["2021", "2022", "2023", "2024", "3Q25"] and parts[1]["rows"][2][0] == "營業收入淨額"
        and parts[0]["bbox"][2] == parts[1]["bbox"][0] and len(split_side_by_side(rate)) == 1, [len(parts), parts[0]["rows"][1] if parts else None])
    P = p27()
    lex = P._FIN_STD + P._load_vrn_lexicon()
    rb_inner = _wrap_rebuild(P._rebuild_table if _HOST["orig"] is None else _HOST["orig"]["_rebuild_table"])
    left = rb_inner(parts[0], lex) if parts else {}
    ca = (left.get("matrix") or {}).get("current_assets") or {}
    vals = {r["label_raw"]: r["values"] for r in left.get("rows") or []}
    chk("③ 拆出的左表重建:流動資產 2023 = 3,602(不再是右表的 1)· 標記左右並排拆出",
        (ca.get("2023") == 3602.0 or (vals.get("流動資產") or {}).get("2023") == 3602.0) and "左右並排拆出" in str(left.get("layout_note")), (ca, vals.get("流動資產")))
    p3 = [["損益表 (單位:百萬元)", "3Q25", "", "", "", "", "4Q25(F)", "", "", "", ""],
          ["", "實際數", "中信預估", "差異", "市場共識", "差異", "調整前", "調整後", "差異", "市場共識", "差異"],
          ["營業收入", "467", "507", "-8.1%", "462", "1.1%", "596", "639", "7.3%", "660", "-3.1%"],
          ["營業利益", "(24)", "76", "-", "29", "-", "185", "163", "-12.2%", "235", "-30.7%"],
          ["EPS(元)", "0.17", "1.55", "-89.0%", "0.35", "-51.1%", "3.13", "3.00", "-4.2%", "4.04", "-25.7%"]]
    rc3 = rb_inner({"engine": "pdfplumber", "rows": p3}, lex)
    oi = next((r["values"] for r in rc3.get("rows") or [] if r["label_raw"] == "營業利益"), {})
    chk("④ 多層表頭:欄名 = 3Q25 實際數 … 4Q25(F) 市場共識 · 營業利益 3Q25 實際數 = -24 · 4Q25(F) 調整後 = 163 · 不再把資料列當表頭",
        rc3.get("periods", [])[:2] == ["3Q25 實際數", "3Q25 中信預估"] and oi.get("3Q25 實際數") == -24.0 and oi.get("4Q25(F) 調整後") == 163.0
        and "多層表頭" in str(rc3.get("layout_note")), (rc3.get("periods", [])[:3], oi))
    gp = [["損益表", "2024", "", "2025F", ""], ["", "實際數", "差異", "預估數", "差異"],
          ["營業收入", "100", "5.0%", "120", "8%"], ["營業成本", "60", "-", "70", "-"], ["營業毛利", "999", "3.1%", "50", "2%"]]
    ok_gp = [r[:] for r in gp]
    ok_gp[4][1] = "40"
    rg, rk = rb_inner({"engine": "pdfplumber", "rows": gp}, lex), rb_inner({"engine": "pdfplumber", "rows": ok_gp}, lex)
    chk("⑤ 多層表頭照鏈上算術驗:毛利 999 ≠ 100 − 60 → 記 issue(REVIEW 依據)· 改成 40 → 無 issue(差異 / % 欄不拿來驗)· 晶心科第 3 頁損益段(無比率列)無誤報",
        "多層表頭" in str(rg.get("layout_note")) and any("2024 實際數" in x and "≠" in x for x in rg.get("issues") or [])
        and "多層表頭" in str(rk.get("layout_note")) and not rk.get("issues") and not rc3.get("issues"), (rg.get("issues"), rk.get("issues"), rc3.get("issues")))
    chk("⑥ 期間把關:數字殘片 / 期間重複 → 記可疑;QoQ · YoY · 差異欄 · 連續兩位數年(22 · 23 · 24F · 23 · 24F)放行;不連續(22 · 24F)照記",
        period_issue(["(24)", "76", "-", "29"]).startswith("期間表頭可疑") and "期間重複" in period_issue(["2023", "2024", "2023", "2024"])
        and period_issue(["3Q24", "2Q25", "3Q25", "QoQ", "YoY"]) == "" and period_issue(["22", "23", "24F"]) == ""
        and period_issue(["23", "24F"]) == "" and period_issue(["23", "24(F)"]) == "" and period_issue(["22", "24F"]).startswith("期間表頭可疑")
        and period_issue(["2024", "2025F", "差異"]) == "")
    if SAMPLE_PDF.is_file() and P._engines().get("pdfplumber"):
        install()
        try:
            with tempfile.TemporaryDirectory() as td:
                rec = P.extract_one(SAMPLE_PDF, Path(td))
                import json
                fin = json.loads((Path(td) / rec["sha8"] / "financial.json").read_text(encoding="utf-8"))
        finally:
            uninstall()
        p5t = [t for t in fin["tables"] if t["page"] == 5 and "左右並排拆出" in str(t.get("layout_note"))]
        bs = next((t for t in p5t if "2021" in t.get("periods", [])), {})
        is_ = next((t for t in p5t if "2027F" in t.get("periods", [])), {})
        p3t = next((t for t in fin["tables"] if t["page"] == 3 and "多層表頭" in str(t.get("layout_note"))), {})
        cur = next((r["values"] for r in bs.get("rows") or [] if r["label_raw"] == "流動資產"), {})
        chk("⑦ 真檔(晶心科 6533):第 5 頁拆成資產負債表(2021–3Q25)+ 損益表(2023–2027F)· 流動資產 2023 = 3,602 · 第 3 頁多層表頭合欄並照算術驗(原檔 4Q25(F) 調整前 毛利率 56.5%% ≠ 595/596 → 記待審)· 狀態 %s" % rec.get("status"),
            bs and is_ and cur.get("2023") == 3602.0 and p3t and any("4Q25(F) 調整前 gross_margin" in x for x in p3t.get("issues") or [])
            and rec.get("status") in ("READ", "REVIEW"), (len(p5t), cur, bool(p3t), p3t.get("issues")))
    else:
        chk("⑦ 真檔樣本不在 / pdfplumber 不在 → NODATA 照實跳過(不冒充)", True)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔面:def main / def selftest / def collect · 第 3 行加速器標記 · __main__ provenance 守門在 --selftest 之前 · 零 TA-Lib · 不寫同意閘",
        "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and text.index('sys.argv[1:2] == ["provenance"]') < text.index('"--selftest" in sys.argv:')
        and "import " + "talib" not in text and "environ[\"VIA_NET" + "_CONSENT\"] =" not in text)
    print("  ── v0262 鏈自測(本版三修卸下;照前版原行為)──", flush=True)
    uninstall()
    h = host()
    prior_rc = int(h.selftest() or 0)
    chk("⑨ v0262 鏈自測照過(前版一字不動)", prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s %s(%s_%s.py)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, FAMILY, TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"]:     # 同 v0262:provenance 先於任何 --selftest 攔截
        sys.exit(provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 SystemManager v0254 — 薄尾(前版 = v0253)。收尾規格(操作員 2026-10-28):剔除冊二次回查 · 一格多值拆分 · SOURCE 末欄 · 合併摘要 · OCR 標準 325 DPI。

① 剔除冊二次回查(不消失 · 只回主冊):
   「該頁原文沒有 N」「原文找不到此值」→ 用 pdfplumber 文字層(第二讀取器 pypdfium2 以外的另一讀法)逐頁數值相等比對(1010.00 = 1,010 · 30,660 = 30660)→ 相等就回主冊 · VERIFY / STATUS 記「原文回查(pdfplumber 數值相等)」
   UPSIDE_PCT 推算值(目標價 ÷ 現價 − 1)重算相符 → 回主冊標「推算 · 可重算驗證」
② 一格多值拆分:同檔同頁同表同期間的表頭列(1Q23 2Q23 … / Old New Chg / 修正後 修正前 調幅 YoY 市場共識 差異 / 調整後 調整前 …)標籤數 = 值數才拆:
   季度標籤 → 季度冊 VRN2_Quarterly_latest(年度冊不混)· 年份標籤 → 年度冊 · 修正 / 共識標籤 → 年度冊 SUBCOL(修正後 / 凱基預估 / New / 調整後 = VALUE_FINAL · 其餘留 SUBCOL)· 對不上的留剔除冊
③ 三冊最後一欄 SOURCE(券商:<券商>(報告 <日期>)· TWSE/TPEX(MOPS 年度實際)· 市場:TWSE/TPEX(VDF 還原價))· STATUS 倒數第二欄 · 正式英文 CSV 40 欄(+ Source)
④ 合併摘要冊 VRN2_Combined_latest:一代號一列(報告份數 · 券商 · 各家評等 / 目標價 · 目標價平均 · 調整後平均 · 最新報告標題與四重點 · 兩個月內份數)· 每欄可回溯到基本資料冊的檔案
⑤ 調節輪標準提高:VRN2_SSOT 新版(只增不減)funnel.ocr_ladder = 325p,400p(T2 = 325 DPI + 前處理 · T3 = 400 DPI + 前處理)· 門檻 0.85 / 40 字 · 上限 T3 · 漏斗層判定依新階梯
⑥ 回填 / 拆分 / 合併各一行進貼包 · 還原帳本 output/VRN2_Restored_latest.json(帶原剔除理由 · 不消失)
不改 v0253 / 另一線任何函式 · 發布層在本版補位之後才跑。
"""
from __future__ import annotations

import csv
import hashlib
import html as _html
import importlib.util
import inspect
import json
import re
import subprocess
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0254"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0253.py"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0254 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0254", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def _rebind(fn):
    return types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)


# ===== ⑤ 調節輪(325 DPI 標準) =====
_FUNNEL = [("T0", "文字層(pdfplumber)"), ("T1", "換引擎(pypdfium2)"), ("T2", "OCR 標準(325 DPI + 前處理)"), ("T3", "OCR 高畫質(400 DPI + 前處理)"), ("T4", "待人工(OCR 佇列)")]
_FUNNEL_DEFAULT = {"order": [n for _, n in _FUNNEL], "ocr_ladder": "325p,400p", "ocr_min_conf": 0.85, "ocr_min_chars": 40, "max_tier": "T3",
                   "rule": "輕的先用 · 不夠才升一層 · 不必全部都用(漏斗)· v0254 標準 325 DPI + 前處理"}


def _funnel_tier(r: dict) -> str:
    zs = [z for pg in r.get("pages") or [] for z in pg.get("zones") or []]
    engs = " ".join(str(z.get("engine") or "") for z in zs)
    if any(z.get("needs_ocr") for z in zs) or any("首頁無文字層" in x for x in (r.get("reasons") or [])):
        return "T4"
    if "rapidocr" in engs:
        tried = (r.get("ocr") or {}).get("tried") if isinstance(r.get("ocr"), dict) else None
        return "T3" if ("400" in engs or (tried and len(tried) > 1)) else "T2"
    if "pypdfium2" in engs:
        return "T1"
    return "T0"


def ensure_ssot_funnel() -> str:
    """VRN2_SSOT 最高版的 funnel 階梯不是 325p,400p → 出新版(只增不減 · 其他鍵不動)。"""
    ssd = HERE / "SSOT"
    books = sorted(ssd.glob("VRN2_SSOT_v[0-9][0-9][0-9][0-9].json"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    if not books:
        return "SSOT 冊尚未建立(vrn2scope 會建)· 階梯由本版預設帶入"
    ss = json.loads(books[-1].read_text(encoding="utf-8"))
    fp = dict(_FUNNEL_DEFAULT, **(ss.get("funnel") or {}))
    if str(fp.get("ocr_ladder")) == "325p,400p" and fp.get("order") == _FUNNEL_DEFAULT["order"]:
        return "%s 階梯已是 325p,400p" % books[-1].name
    new = dict(ss, funnel=dict(fp, ocr_ladder="325p,400p", order=_FUNNEL_DEFAULT["order"], max_tier=fp.get("max_tier") or "T3", rule=_FUNNEL_DEFAULT["rule"]))
    nv = int(re.search(r"_v(\d{4})", books[-1].name).group(1)) + 1
    (ssd / ("VRN2_SSOT_v%04d.json" % nv)).write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    return "VRN2_SSOT_v%04d.json(階梯 %s → 325p,400p · 前版不動)" % (nv, fp.get("ocr_ladder"))


# ===== ① ② 剔除冊二次回查 =====
_NUM_TOK = re.compile(r"\(?-?\d[\d,]*(?:\.\d+)?\)?%?")
_HDR_TOK = re.compile(r"[1-4]Q\d{2}[A-Z]?|\d{1,2}M\d{2}|FY\d{2,4}[AEF]?|(?<![\d.])(?:19|20)\d{2}[AEF]?(?![\d.])|修正後|修正前|調幅|凱基預估|市場共識|差異|調整後|調整前|YoY|QoQ|Old|New|Chg|Diff|Cons\.?|GS(?![A-Za-z])|%Diff")
_PRIMARY = {"修正後", "凱基預估", "New", "調整後", "GS"}
_QTR = re.compile(r"^(?:[1-4]Q\d{2}[A-Z]?|\d{1,2}M\d{2})$")
_YEAR = re.compile(r"^(?:FY)?(?:19|20)?\d{2,4}[AEF]?$")


def _tonum(s: str):
    try:
        v, _ = _norm_num(str(s))
        return v
    except Exception:  # noqa: BLE001
        t = str(s).replace(",", "").replace("%", "").strip()
        neg = t.startswith("(") and t.endswith(")")
        t = t.strip("()")
        try:
            return -float(t) if neg else float(t)
        except ValueError:
            return None


def _page_nums(pdf: Path, pno: int, cache: dict) -> set:
    key = (str(pdf), int(pno))
    if key in cache:
        return cache[key]
    out = set()
    try:
        import pdfplumber  # noqa: WPS433
        with pdfplumber.open(str(pdf)) as doc:
            if 0 < pno <= len(doc.pages):
                txt = doc.pages[pno - 1].extract_text() or ""
                txt = re.sub(r"(?<=\d),\s+(?=\d{3})", ",", txt)              # 千分位後的折行 / 空格接回
                for m in _NUM_TOK.finditer(txt):
                    v = _tonum(m.group(0))
                    if v is not None:
                        out.add(round(v, 6))
    except Exception:  # noqa: BLE001
        pass
    cache[key] = out
    return out


def _mk_fin(base: dict, period: str, value, verify: str, subcol: str = "", note: str = "") -> dict:
    kind, std = _norm_period(str(period))
    vn, unit = _norm_num(str(value))
    row = {"REPORT_DATE": base.get("REPORT_DATE", ""), "FILENAME": base.get("FILENAME", ""), "TICKER": base.get("TICKER", ""), "BROKER": base.get("BROKER", ""), "PAGE": base.get("PAGE", ""),
           "TABLE": base.get("TABLE", ""), "ITEM": base.get("ITEM", ""), "PERIOD": period, "VALUE": value, "VERIFY": verify, "ROW": base.get("ROW", ""), "SECTION": base.get("SECTION", ""),
           "PERIOD_STD": std if kind else "", "PERIOD_KIND": kind or "", "VALUE_NUM": vn, "UNIT": unit or "", "EPS_KIND": "", "ITEM_RAW": base.get("ITEM_RAW", ""), "SUBCOL": subcol,
           "VALUE_FINAL": vn, "VALUE_SOURCE": "報告值 · 未核對(VDF 年度實際未就緒)", "STATUS": note}
    return row


def second_chance(rej: list, fin: list, basic: list, v2: Path) -> tuple:
    """回 (還原的年度列數, 基本資料回填數, 季度列數, 還原帳本, 仍剔除的清單)。"""
    cache, restored, quarterly, keep = {}, [], [], []
    have = {(r.get("FILENAME"), r.get("ITEM"), str(r.get("PERIOD")), str(r.get("VALUE")), r.get("SUBCOL", "")) for r in fin}
    bmap = {Path(str(b.get("FILENAME") or "")).name: b for b in basic}
    nb = 0
    groups = defaultdict(list)
    for r in rej:
        if str(r.get("REASON") or "").startswith("一格多值"):
            groups[(r.get("FILENAME"), str(r.get("PAGE")), str(r.get("TABLE")), str(r.get("PERIOD")))].append(r)
    # 表頭列:同群裡沒有數值 token、標籤 ≥2 的那一列
    labels = {}
    for k, rows in groups.items():
        for r in rows:
            val = str(r.get("VALUE") or "")
            toks = _HDR_TOK.findall(val)
            if len(toks) >= 2 and not _NUM_TOK.findall(_HDR_TOK.sub(" ", val)):
                seen = Counter(); lab = []
                for t in toks:
                    seen[t] += 1; lab.append(t if seen[t] == 1 else "%s(%d)" % (t, seen[t]))
                labels[k] = lab
                break
    split_ids = set()
    for k, lab in labels.items():
        for r in groups[k]:
            val = str(r.get("VALUE") or "")
            if len(_HDR_TOK.findall(val)) >= 2 and not _NUM_TOK.findall(_HDR_TOK.sub(" ", val)):
                split_ids.add(id(r)); continue                                   # 表頭列本身:拆完即不再剔除
            nums = _NUM_TOK.findall(val)
            if len(nums) != len(lab):
                continue
            pri = next((i for i, l in enumerate(lab) if l.split("(")[0] in _PRIMARY), None)
            for i, (l, v) in enumerate(zip(lab, nums)):
                base = dict(r)
                if _QTR.match(l):
                    q = _mk_fin(base, l, v, "一格多值拆分(表頭 %d 欄對 %d 值 · v0254)" % (len(lab), len(nums)), "", "QUARTERLY:自年度表格拆出 · 原剔除理由 %s" % r.get("REASON"))
                    quarterly.append(q)
                elif _YEAR.match(l) and l.split("(")[0] not in _PRIMARY:
                    row = _mk_fin(base, l, v, "一格多值拆分(表頭 %d 欄對 %d 值 · v0254)" % (len(lab), len(nums)), "", "RESTORED:一格多值拆分 · 原剔除理由 %s" % r.get("REASON"))
                    if (row["FILENAME"], row["ITEM"], row["PERIOD"], row["VALUE"], "") not in have:
                        fin.append(row); restored.append(dict(r, RESTORED_AS="FinancialData", NEW_PERIOD=l, NEW_VALUE=v)); have.add((row["FILENAME"], row["ITEM"], row["PERIOD"], row["VALUE"], ""))
                else:
                    sub = l if not (pri is not None and i == pri) else ""
                    row = _mk_fin(base, str(r.get("PERIOD")), v, "一格多值拆分(表頭 %d 欄對 %d 值 · v0254)" % (len(lab), len(nums)), sub, "RESTORED:一格多值拆分%s · 原剔除理由 %s" % (" · SUBCOL %s" % l if sub else " · 主值(%s)" % l, r.get("REASON")))
                    if (row["FILENAME"], row["ITEM"], row["PERIOD"], row["VALUE"], sub) not in have:
                        fin.append(row); restored.append(dict(r, RESTORED_AS="FinancialData", SUBCOL=sub or l, NEW_VALUE=v)); have.add((row["FILENAME"], row["ITEM"], row["PERIOD"], row["VALUE"], sub))
            split_ids.add(id(r))
    for r in rej:
        if id(r) in split_ids:
            continue
        why = str(r.get("REASON") or "")
        f = str(r.get("FILENAME") or "")
        if r.get("BOOK") == "BasicInfo" and why.startswith("原文找不到此值"):
            b = bmap.get(Path(f).name)
            fld, val = r.get("FIELD"), r.get("VALUE")
            if b is not None and fld:
                ok, how = False, ""
                if fld == "UPSIDE_PCT":
                    t, c = _tonum(b.get("TARGET_PRICE")), _tonum(b.get("CURRENT_PRICE_REPORT"))
                    v = _tonum(val)
                    if t and c and v is not None and abs((t / c - 1) * 100 - v) <= 0.2:
                        ok, how = True, "推算(目標價 ÷ 現價 − 1 · 重算相符 · 可驗證)"
                else:
                    v = _tonum(val)
                    pdf = _out_pdf(Path(f).name, v2)
                    if v is not None and pdf.exists() and any(round(v, 6) in _page_nums(pdf, p, cache) for p in (1, 2)):
                        ok, how = True, "原文回查(pdfplumber 數值相等)"
                if ok:
                    if _blank(b.get(fld)):
                        b[fld] = val
                    _status_append(b, "%s:%s" % (fld, how)); nb += 1
                    restored.append(dict(r, RESTORED_AS="BasicInfo", HOW=how)); continue
        elif r.get("BOOK") == "FinancialData" and why.startswith("該頁原文沒有"):
            v = _tonum(r.get("VALUE"))
            pdf = _out_pdf(Path(f).name, v2)
            try:
                pno = int(r.get("PAGE") or 0)
            except (TypeError, ValueError):
                pno = 0
            if v is not None and pdf.exists() and pno and round(v, 6) in _page_nums(pdf, pno, cache):
                row = _mk_fin(r, str(r.get("PERIOD")), r.get("VALUE"), "原文回查(pdfplumber 數值相等 · v0254)", "", "RESTORED:第二讀法回查通過 · 原剔除理由 %s" % why)
                if (row["FILENAME"], row["ITEM"], row["PERIOD"], row["VALUE"], "") not in have:
                    fin.append(row); have.add((row["FILENAME"], row["ITEM"], row["PERIOD"], row["VALUE"], ""))
                restored.append(dict(r, RESTORED_AS="FinancialData", HOW="pdfplumber 數值相等")); continue
        keep.append(r)
    return len([x for x in restored if x.get("RESTORED_AS") == "FinancialData"]), nb, len(quarterly), restored, keep, quarterly


# ===== ③ SOURCE 末欄 =====
def _source_last(row: dict, kind: str) -> None:
    st = row.pop("STATUS", ""); row.pop("SOURCE", None)
    br, dt = row.get("BROKER") or "", row.get("REPORT_DATE") or ""
    if kind == "fin":
        src = "TWSE/TPEX(MOPS 年度實際 · VDF)" if "實際蓋過預估" in str(row.get("VALUE_SOURCE") or "") else "券商:%s(報告 %s)" % (br, dt)
        if "核對通過" in str(row.get("VALUE_SOURCE") or ""):
            src += " · 核對 TWSE/TPEX"
    elif kind == "basic":
        src = "券商:%s(報告 %s)" % (br, dt) + (" · 市場:TWSE/TPEX(VDF 還原價)" if not _blank(row.get("ADJ_CLOSE")) else "")
    elif kind == "summ":
        src = "券商:%s(報告 %s)" % (br, dt) + (" · 上漲空間(調整後):TWSE/TPEX" if not _blank(row.get("UPSIDE_ADJ")) else "")
    else:
        src = row.get("_SRC") or "彙整"
        row.pop("_SRC", None)
    row["STATUS"] = st; row["SOURCE"] = src


def _write_formal_csv_40(od: Path, basic: list) -> int:
    hv = globals().get("HEADERS_V3") or []
    keys = [k for k, _, _ in hv] + ["SOURCE"]
    en = dict({k: e for k, e, _ in hv}, SOURCE="Source")
    if len(keys) < 2:
        return 0
    with (od / "VRN2_BasicInfo_latest_formal.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh); w.writerow([en[k] for k in keys])
        for r in basic:
            w.writerow([r.get(k, "") if not isinstance(r.get(k), (dict, list)) else json.dumps(r.get(k), ensure_ascii=False) for k in keys])
    return len(keys)


# ===== ④ 合併摘要 =====
def combine(basic: list, summ: list) -> list:
    smap = {Path(str(s.get("FILENAME") or "")).name: s for s in summ}
    by = defaultdict(list)
    for b in basic:
        if b.get("TICKER"):
            by[str(b["TICKER"])].append(b)
    out = []
    for tk, rows in sorted(by.items()):
        rows = sorted(rows, key=lambda b: str(b.get("REPORT_DATE") or ""), reverse=True)
        latest = rows[0]
        s = smap.get(Path(str(latest.get("FILENAME") or "")).name, {})
        tp = [_tonum(b.get("TARGET_PRICE")) for b in rows]; tp = [x for x in tp if x]
        ta = [_tonum(b.get("TARGET_PRICE(ADJ)")) for b in rows]; ta = [x for x in ta if x]
        up = [_tonum(b.get("UPSIDE_ADJ")) for b in rows]; up = [x for x in up if x is not None]
        rec = sum(1 for b in rows if str(b.get("RECENT_2M") or b.get("RECENT_REPORT_AND_PRE_EARNINGS_FLAG") or "").startswith("兩個月內"))
        row = {"TICKER": tk, "NAME": next((b.get("NAME") for b in rows if b.get("NAME")), ""), "YFINANCE_TICKER": next((b.get("YFINANCE_TICKER") for b in rows if b.get("YFINANCE_TICKER")), ""),
               "REPORTS": len(rows), "BROKERS": " / ".join(dict.fromkeys(str(b.get("BROKER") or "") for b in rows)),
               "LATEST_REPORT_DATE": latest.get("REPORT_DATE", ""), "LATEST_BROKER": latest.get("BROKER", ""), "LATEST_RATING": latest.get("RATING", ""),
               "RATINGS": " | ".join("%s:%s(%s)" % (b.get("BROKER"), b.get("RATING") or "—", b.get("REPORT_DATE")) for b in rows),
               "TARGET_PRICES": " | ".join("%s:%s" % (b.get("BROKER"), b.get("TARGET_PRICE") or "—") for b in rows),
               "TARGET_MEAN": round(sum(tp) / len(tp), 2) if tp else "", "TARGET_ADJ_MEAN": round(sum(ta) / len(ta), 2) if ta else "",
               "ADJ_CLOSE": latest.get("ADJ_CLOSE", ""), "ADJ_CLOSE_DATE": latest.get("ADJ_CLOSE_DATE", ""), "UPSIDE_ADJ_MEAN": round(sum(up) / len(up), 9) if up else "",
               "RECENT_2M_REPORTS": rec, "TITLE": s.get("TITLE", ""), "POINT_1": s.get("POINT_1", ""), "POINT_2": s.get("POINT_2", ""), "POINT_3": s.get("POINT_3", ""), "POINT_4": s.get("POINT_4", ""),
               "FILES": " | ".join(str(b.get("FILENAME")) for b in rows),
               "STATUS": "COMBINED:%d 份 · 目標價有值 %d · 調整後 %d · 摘要來自最新一份%s" % (len(rows), len(tp), len(ta), "" if s else "(無)"),
               "_SRC": "彙整:券商 %s · 市場 TWSE/TPEX(VDF 還原價)%s" % (" / ".join(dict.fromkeys(str(b.get("BROKER") or "") for b in rows)), "" if ta else "(未就緒)")}
        _source_last(row, "comb")
        out.append(row)
    return out


def _out_books(res, acc, st, v2):
    basic, fin, summ, gaps, made = PRIOR.PRIOR.PRIOR._out_books(res, acc, st, v2)   # v0248 以前 · 之後 v0253 補位 → 本版 → 發布
    od = Path(v2) / "output"
    try:
        market = {}
        try:
            market = json.loads((Path(v2) / "market" / "VRN2_Market_latest.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
        na = _fill_analyst(basic, acc); nf = _fin_v2_shape(fin); ns = _summ_status(summ)
        print("  [計] v0253 補位:分析師回填 %d · 年度數據 V2 欄位補 %d 列 · 摘要 STATUS %d" % (na, nf, ns), flush=True)
        rej = []
        try:
            rej = json.loads((od / "VRN2_Rejected_latest.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
        nr, nb, nq, restored, keep, quarterly = second_chance(rej, fin, basic, Path(v2))
        if rej:
            _rewrite_book(od, "Rejected", keep)
            (od / "VRN2_Restored_latest.json").write_text(json.dumps(restored, ensure_ascii=False, indent=1), encoding="utf-8")
        for q in quarterly:
            _source_last(q, "fin")
        if quarterly:
            _rewrite_book(od, "Quarterly", quarterly)
        for b in basic:
            _source_last(b, "basic")
        for r in fin:
            _source_last(r, "fin")
        for s in summ:
            _source_last(s, "summ")
        comb = combine(basic, summ)
        _rewrite_book(od, "BasicInfo", basic); _rewrite_book(od, "FinancialData", fin); _rewrite_book(od, "Summary", summ); _rewrite_book(od, "Combined", comb)
        nc = _write_formal_csv_40(od, basic)
        why = Counter(str(r.get("REASON") or "").split("(")[0][:12] for r in keep)
        print("  [計] v0254 剔除冊二次回查 · 回主冊 年度 %d 列 · 基本資料 %d 格 · 季度冊 %d 列 · 仍剔除 %d(%s)→ VRN2_Restored_latest.json" % (nr, nb, nq, len(keep), " · ".join("%s %d" % (k, v) for k, v in why.most_common(4))), flush=True)
        print("  [計] v0254 SOURCE 末欄:基本資料 %d · 年度數據 %d · 摘要 %d · 正式 CSV %d 欄 · 合併摘要 %d 代號 → VRN2_Combined_latest · 調節輪 %s" % (len(basic), len(fin), len(summ), nc, len(comb), ensure_ssot_funnel()), flush=True)
        line, _ = blank_audit(basic, fin, summ, market, od, gaps)
        print("  [計] v0254 " + line, flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] v0254 收尾未完成 %s %s" % (type(exc).__name__, str(exc)[:80]), flush=True)
    try:
        eng = _pub_engine()
        if eng:
            r = subprocess.run([sys.executable, "-W", "ignore", str(eng), "--publish", "--v2", str(v2)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800, cwd=str(HERE))
            line = next((l for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith("[計] 發布")), "")
            print("  " + (line.strip() if line else "[計] 發布未回報 rc %d" % r.returncode)[:400], flush=True)
        else:
            print("  [計] 發布引擎未落地(VRN2_Publish_v####.py)", flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] 發布未完成 %s" % type(exc).__name__, flush=True)
    return basic, fin, summ, gaps, made


def _ui_panel_html(v2):
    h = PRIOR._ui_panel_html(v2)
    try:
        od = Path(v2) / "output"
        inv = Path(v2) / "publish" / "VRN2_DB_Inventory_latest.json"
        rows = ""
        if inv.exists():
            for e in json.loads(inv.read_text(encoding="utf-8")).get("files", [])[:40]:
                rows += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (_html.escape(str(e.get("book"))), _html.escape(str(e.get("format"))), e.get("rows", ""), _html.escape(str(e.get("path"))[-60:]))
        link = ("<div style='margin:8px 0;padding:6px 8px;border:1px solid #e2e8f0;border-radius:6px;background:#fff'><b>資料庫夾(parquet 為準 · 增量)</b> · "
                "<a href='vrn2://publish-inventory'>🗂 掃描資料庫夾</a> · <a href='vrn2://publish-to-parquet'>⇄ 非 parquet 轉 parquet</a> · "
                "<a href='vrn2://publish-export?fmt=csv'>⬇ 匯出 CSV</a> · <a href='vrn2://publish-export?fmt=json'>⬇ 匯出 JSON</a> · <a href='vrn2://publish'>⬆ 發布(含 Google Sheet 若啟用)</a> · "
                "<a href='%s' target='_blank'>合併摘要</a> · <a href='%s' target='_blank'>季度冊</a> · <a href='%s' target='_blank'>還原帳本</a>"
                "<table style='font-size:11px;margin-top:4px'><tr><th>冊</th><th>格式</th><th>列</th><th>路徑</th></tr>%s</table></div>") % (
                    _html.escape((od / "VRN2_Combined_latest.csv").as_uri() if (od / "VRN2_Combined_latest.csv").exists() else "#"),
                    _html.escape((od / "VRN2_Quarterly_latest.csv").as_uri() if (od / "VRN2_Quarterly_latest.csv").exists() else "#"),
                    _html.escape((od / "VRN2_Restored_latest.json").as_uri() if (od / "VRN2_Restored_latest.json").exists() else "#"), rows or "<tr><td colspan='4'>按「掃描資料庫夾」後顯示</td></tr>")
        return (h or "") + link
    except Exception:  # noqa: BLE001
        return h


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    except Exception:  # noqa: BLE001
        pass
    return result


_MY_SIG = hashlib.sha1(inspect.getsource(second_chance).encode("utf-8")).hexdigest()[:12]
for _n in ("_base_acceptance", "_acc_parallel", "_acc_shard_main", "_acc_one", "_acc_one_core", "_acc_basic", "acceptance", "_acc_sig", "_native_vrn2", "vrn2", "_idem_check", "main", "_success_register", "_out_html", "_funnel", "_funnel_html"):
    globals()[_n] = _rebind(getattr(PRIOR, _n))


def selftest() -> int:
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    import tempfile
    v2 = Path(tempfile.mkdtemp())
    rej = [{"BOOK": "FinancialData", "FILENAME": "Daiwa-1319 20231011.pdf", "PAGE": 2, "TABLE": "P2·F·01", "ITEM": "(TWDm)", "PERIOD": "2023E", "VALUE": "1Q23 2Q23 3Q23E 4Q23E", "REASON": "一格多值(4 個值 · 子欄位未拆)", "REPORT_DATE": "2023-10-11", "TICKER": "1319", "BROKER": "Daiwa"},
           {"BOOK": "FinancialData", "FILENAME": "Daiwa-1319 20231011.pdf", "PAGE": 2, "TABLE": "P2·F·01", "ITEM": "Revenue", "PERIOD": "2023E", "VALUE": "5,598 5,551 6,154 6,289", "REASON": "一格多值(4 個值 · 子欄位未拆)", "REPORT_DATE": "2023-10-11", "TICKER": "1319", "BROKER": "Daiwa"},
           {"BOOK": "FinancialData", "FILENAME": "欣銓.pdf", "PAGE": 3, "TABLE": "P3·F·02", "ITEM": "(單位:百萬元)", "PERIOD": "2026(F)", "VALUE": "調整後調整前差異市場共識差異", "REASON": "一格多值(5 個值 · 子欄位未拆)", "REPORT_DATE": "2026-09-18", "TICKER": "3264", "BROKER": "中信"},
           {"BOOK": "FinancialData", "FILENAME": "欣銓.pdf", "PAGE": 3, "TABLE": "P3·F·02", "ITEM": "營業收入", "PERIOD": "2026(F)", "VALUE": "19,520 19,100 2.2% 19,221 1.6%", "REASON": "一格多值(5 個值 · 子欄位未拆)", "REPORT_DATE": "2026-09-18", "TICKER": "3264", "BROKER": "中信"},
           {"BOOK": "FinancialData", "FILENAME": "凱基6147.pdf", "PAGE": 4, "TABLE": "P4·F·01", "ITEM": "百萬元", "PERIOD": "2026F", "VALUE": "凱基預估 YoY (%) 市場共識差異 (%)", "REASON": "一格多值(4 個值 · 子欄位未拆)", "REPORT_DATE": "2026-05-19", "TICKER": "6147", "BROKER": "凱基"},
           {"BOOK": "FinancialData", "FILENAME": "凱基6147.pdf", "PAGE": 4, "TABLE": "P4·F·01", "ITEM": "毛利率 (%)", "PERIOD": "2026F", "VALUE": "26.7 5.3 ppts 25.5 1.2 ppts", "REASON": "一格多值(4 個值 · 子欄位未拆)", "REPORT_DATE": "2026-05-19", "TICKER": "6147", "BROKER": "凱基"},
           {"BOOK": "FinancialData", "FILENAME": "GS-2382.pdf", "PAGE": 5, "TABLE": "P5·F·01", "ITEM": "NT m", "PERIOD": "2023E", "VALUE": "Old New Chg", "REASON": "非數據列(表頭 / 子表頭 / 分隔線)", "REPORT_DATE": "2023-10-12", "TICKER": "2382", "BROKER": "GS"},
           {"BOOK": "FinancialData", "FILENAME": "GS-2382.pdf", "PAGE": 5, "TABLE": "P5·F·01", "ITEM": "NM", "PERIOD": "2023E", "VALUE": "3.2% 3.1%", "REASON": "一格多值(2 個值 · 子欄位未拆)", "REPORT_DATE": "2023-10-12", "TICKER": "2382", "BROKER": "GS"},
           {"BOOK": "BasicInfo", "FILENAME": "GS-1590 20231012.pdf", "FIELD": "UPSIDE_PCT", "VALUE": "18.8", "REASON": "原文找不到此值 · 不輸出"},
           {"BOOK": "FinancialData", "FILENAME": "MS-1590.pdf", "PAGE": 1, "TABLE": "P1·R·02", "ITEM": "Revenue, net (NT$ mn)", "PERIOD": "12/24", "VALUE": "30,660", "REASON": "該頁原文沒有 30,660", "REPORT_DATE": "2025-12-02", "TICKER": "1590", "BROKER": "MS"}]
    basic = [{"FILENAME": "GS-1590 20231012.pdf", "TICKER": "1590", "BROKER": "GS", "REPORT_DATE": "2023-10-12", "TARGET_PRICE": "1,200", "CURRENT_PRICE_REPORT": "1010.00", "UPSIDE_PCT": "", "RATING": "Buy", "ADJ_CLOSE": "", "STATUS": ""},
             {"FILENAME": "GS-1590 20251203.pdf", "TICKER": "1590", "BROKER": "GS", "REPORT_DATE": "2025-12-03", "TARGET_PRICE": "1,085", "CURRENT_PRICE_REPORT": "885", "RATING": "Buy", "TARGET_PRICE(ADJ)": 1085.0, "ADJ_CLOSE": 900.0, "UPSIDE_ADJ": 0.2055, "STATUS": "", "RECENT_2M": "兩個月內 · Q3"}]
    fin = []
    nr, nb, nq, restored, keep, quarterly = second_chance(rej, fin, basic, v2)
    qper = [q["PERIOD"] for q in quarterly]
    xz = [(r["ITEM"], r["PERIOD"], r["VALUE"], r["SUBCOL"]) for r in fin if r["FILENAME"] == "欣銓.pdf"]
    kg = [(r["VALUE"], r["SUBCOL"]) for r in fin if r["FILENAME"] == "凱基6147.pdf"]
    chk("② 一格多值拆分:季度 %s · 欣銓 %s · 凱基 %s · 仍剔除 %d(GS NM 2 值對 3 標籤不拆 · MS 無 PDF 不回)" % (qper, xz[:2], kg, len(keep)),
        qper == ["1Q23", "2Q23", "3Q23E", "4Q23E"] and [q["VALUE"] for q in quarterly] == ["5,598", "5,551", "6,154", "6,289"] and len(xz) == 5 and xz[0][3] == "" and xz[1][3] == "調整前" and xz[4][3] == "差異(2)"
        and kg == [("26.7", ""), ("5.3", "YoY"), ("25.5", "市場共識"), ("1.2", "差異")] and len(keep) == 3 and all(str(k.get("ITEM")) != "Revenue" for k in keep))
    chk("① 推算值回填 UPSIDE_PCT %s · STATUS %s" % (basic[0]["UPSIDE_PCT"], basic[0]["STATUS"][:30]), nb == 1 and basic[0]["UPSIDE_PCT"] == "18.8" and "推算" in basic[0]["STATUS"])
    for b in basic:
        _source_last(b, "basic")
    for r in fin:
        _source_last(r, "fin")
    chk("③ SOURCE 末欄 %s / %s" % (list(basic[1].keys())[-2:], basic[1]["SOURCE"]), list(basic[1].keys())[-1] == "SOURCE" and list(basic[1].keys())[-2] == "STATUS" and "TWSE/TPEX" in basic[1]["SOURCE"] and "券商:GS" in basic[1]["SOURCE"] and fin[0]["SOURCE"].startswith("券商:"))
    od = Path(tempfile.mkdtemp())
    nc = _write_formal_csv_40(od, basic)
    hdr = (od / "VRN2_BasicInfo_latest_formal.csv").read_text(encoding="utf-8-sig").splitlines()[0].split(",")
    chk("③ 正式 CSV %d 欄 · 末 %s" % (nc, hdr[-1]), nc == 40 and hdr[-1] == "Source" and hdr[-2] == "Status")
    summ = [{"FILENAME": "GS-1590 20251203.pdf", "TITLE": "亞德客(1590.TW): t", "POINT_1": "p1", "POINT_2": "p2", "POINT_3": "p3", "POINT_4": "p4", "STATUS": ""}]
    comb = combine(basic, summ)
    chk("④ 合併摘要 %d 代號 · 份數 %s · 目標價平均 %s · 最新 %s · 兩個月內 %s · 末欄 %s" % (len(comb), comb[0]["REPORTS"], comb[0]["TARGET_MEAN"], comb[0]["LATEST_REPORT_DATE"], comb[0]["RECENT_2M_REPORTS"], list(comb[0].keys())[-1]),
        len(comb) == 1 and comb[0]["REPORTS"] == 2 and comb[0]["TARGET_MEAN"] == 1142.5 and comb[0]["LATEST_REPORT_DATE"] == "2025-12-03" and comb[0]["RECENT_2M_REPORTS"] == 1 and comb[0]["POINT_4"] == "p4" and list(comb[0].keys())[-1] == "SOURCE")
    chk("⑤ 調節輪 階梯 %s · T2 標籤 %s · 400 → T3 %s" % (_FUNNEL_DEFAULT["ocr_ladder"], _FUNNEL[2][1], _funnel_tier({"pages": [{"zones": [{"engine": "rapidocr 400p"}]}]})),
        _FUNNEL_DEFAULT["ocr_ladder"] == "325p,400p" and "325" in _FUNNEL[2][1] and _funnel_tier({"pages": [{"zones": [{"engine": "rapidocr 400p"}]}]}) == "T3" and _funnel_tier({"pages": [{"zones": [{"engine": "rapidocr 325p"}]}]}) == "T2")
    chk("⓪ v0254 綁定:_out_books / _ui_panel_html / completion / _funnel 走本版", _native_vrn2.__globals__["_out_books"] is _out_books and _native_vrn2.__globals__["_ui_panel_html"] is _ui_panel_html and _native_vrn2.__globals__["completion"] is completion and _funnel.__globals__["_FUNNEL_DEFAULT"]["ocr_ladder"] == "325p,400p")
    import os
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("          ── 前版鏈(v0253)自測 ──")
        rc = PRIOR.selftest()
        chk("⑥ 前版鏈 v0253 自測 rc %s" % rc, rc == 0)
    p, f = ok
    print("[計] VRN-2 SystemManager v0254(VRN_SystemManager_v0254.py)自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_BookSource v0101 — v0100 薄尾(v0100 一字不改):⑬a 再多兩件 · 四點去開頭符號 · Combined「主題與摘要」新格式。

操作員 2026-11-03:
  「四點摘要前面出現任何標點符號如 ➢ 則刪除」
  「第一點通常為評價,採取每日更新後的 ADJ 目標價、ADJ CLOSE 來計算上漲空間」
  「標題格式 Name(YFinance Ticker, 評等) - 原文標題」
做法(v0100 的 BROKER_EN / SOURCE 兩欄照舊;其他冊照舊):
  ① Summary 冊 POINT_1 ~ POINT_4 與 TITLE:開頭的項目符號 / 標點 / 編號(➢ • ⚫ ● ■ ◆ ▶ → - * · (1) ① 1、…)與空白換行刪掉,
     內文一字不改(原文核對照樣找得到 · 只是少了開頭符號)。
  ② Combined 冊「TOPIC & SUMMARY」(本來 = 標題 · 四點)改成:
       標題 = Name(YFinance Ticker, 評等) - 原文標題 (Name 取 Combined → 基本資料 → 英文名 → 代號;沒有評等就只寫代號)
       四點 = Summary 去符號後的四點;評價那一點(目標價 / 上漲空間 / 評等 / target / upside / rating …)排第一;
       那一點的上漲空間改用每日更新的 TARGET_PRICE(ADJ) ÷ ADJ_CLOSE − 1 算,句尾接「;調整後目標價 X ÷ 調整後收盤 Y = 上漲空間 Z%」;
       四點裡沒有評價句 → 第一點補一句「評價 評等:調整後目標價 X ÷ 調整後收盤 Y = 上漲空間 Z%」(四點仍是四點);
       調整後目標價或調整後收盤缺 → 數字不動(只排序)。原文核對對的是 Summary 冊,Combined 這欄是組出來的摘要。
  ③ JSON / CSV / Parquet 三種格式同一套規則;內容沒變就不寫(冪等);收據多記去符號幾格、主題與摘要幾列、改算上漲空間幾列。
動詞同 v0100:apply [--v2] [--dry-run] · --selftest
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
DISPLAY_NAME = "VRN2_BookSource"
PRIOR_NAME = "VRN2_BookSource_v0100.py"
HERE = Path(__file__).resolve().parent
POINTS = ("POINT_1", "POINT_2", "POINT_3", "POINT_4")
TOPIC = "TOPIC & SUMMARY"


def _load_prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_booksource_prior_v0100", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V0100 = _load_prior()
for _name in dir(V0100):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(V0100, _name)
_v0100 = {k: getattr(V0100, k) for k in ("apply", "do_json", "do_csv", "do_parquet")}

# ── ① 去開頭符號 ─────────────────────────────────────────────────────────────────────────────────────
_SYM = re.compile("^[\\s\u00b7\u2022\u2023\u2027\u2043\u2219\u22c5\u25a0-\u25ff\u2600-\u27bf\u2b00-\u2bff\u2190-\u21ff\u30fb\uff0d\uff65"
                  "\\-\\*\\+>~=#\u2010-\u2015\u203b\u2023\u25cf\u2605\u2606\u2713\u2714\u2717\u2718\U0001F300-\U0001FAFF]+")
_ENUM = re.compile("^(?:[(\uff08]\\s*\\d{1,2}\\s*[)\uff09]|\\d{1,2}[\u3001\uff0e](?!\\d)|\\d{1,2}[.)\uff09](?=\\s)|[\u2460-\u2473\u2776-\u277f])\\s*")


def strip_lead(s) -> str:
    """開頭的項目符號 / 標點 / 編號與空白換行刪掉(重複到不再變);內文不動。"""
    t = "" if s is None else str(s)
    prev = None
    while prev != t:
        prev = t
        t = _SYM.sub("", t)
        t = _ENUM.sub("", t)
    return t


# ── ② 主題與摘要 ─────────────────────────────────────────────────────────────────────────────────────
_VAL = re.compile(r"目標價|上漲空間|下跌空間|潛在空間|評等|評價|投資建議|(?i:target\s*price|price\s*target|\bPT\b|\bTP\b|upside|downside|\brating\b|reiterate|overweight|underweight|"
                  r"equal-weight|outperform|underperform|\bbuy\b|\bsell\b|\bneutral\b|\bhold\b)")
_UP_CN = re.compile(r"((?:潛在)?(?:上漲|下跌)空間\s*(?:約|為|達|有|仍有)?\s*[:：]?\s*)([+-]?\d+(?:\.\d+)?)(\s*%)")
_UP_EN = re.compile(r"(?i)((?:upside|downside)(?:\s+potential)?(?:\s+of)?\s*)([+-]?\d+(?:\.\d+)?)(\s*%)|([+-]?\d+(?:\.\d+)?)(\s*%\s+(?:upside|downside))")


def _num(v):
    try:
        x = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return x if x == x else None


def _fmt(x) -> str:
    return ("%.2f" % x).rstrip("0").rstrip(".") if x is not None else ""


def title_line(comb: dict, basic: dict, summ: dict) -> str:
    name = str(comb.get("NAME") or basic.get("NAME") or basic.get("ENGLISH_NAME") or comb.get("TICKER") or basic.get("TICKER") or "").strip()
    yf = str(comb.get("YFINANCE_TICKER") or basic.get("YFINANCE_TICKER") or comb.get("TICKER") or basic.get("TICKER") or "").strip()
    rating = str(comb.get("RATING") or basic.get("RATING") or "").strip()
    title = " ".join(strip_lead(summ.get("TITLE") or basic.get("TITLE") or "").split())
    inner = ", ".join(x for x in (yf, rating) if x)
    head = ("%s(%s)" % (name, inner)) if inner else name
    return (" - ".join(x for x in (head, title) if x)).strip()


def compose(comb: dict, basic: dict, summ: dict) -> tuple:
    """(新的 TOPIC & SUMMARY, 有沒有改算上漲空間)。"""
    pts = [strip_lead(summ.get(k)) for k in POINTS]
    pts = [p.strip() for p in pts if p and p.strip()]
    k = next((i for i, p in enumerate(pts) if _VAL.search(p)), None)
    if k:
        pts.insert(0, pts.pop(k))
    tp, adj = _num(comb.get("TARGET_PRICE(ADJ)")), _num(comb.get("ADJ_CLOSE"))
    redone = False
    if tp and adj and adj > 0:
        up = "%.1f" % ((tp / adj - 1) * 100)
        basis = "調整後目標價 %s ÷ 調整後收盤 %s = 上漲空間 %s%%" % (_fmt(tp), _fmt(adj), up)
        if k is not None:
            p0 = _UP_CN.sub(lambda m: m.group(1) + up + m.group(3), pts[0])
            p0 = _UP_EN.sub(lambda m: (m.group(1) + up + m.group(3)) if m.group(1) is not None else (up + m.group(5)), p0)
            pts[0] = p0.rstrip() + "\uff1b" + basis
        else:
            rating = str(comb.get("RATING") or basic.get("RATING") or "").strip()
            pts = [("評價 %s\uff1a%s" % (rating, basis)) if rating else ("評價\uff1a" + basis)] + pts[:3]
        redone = True
    return " · ".join([title_line(comb, basic, summ)] + pts[:4]).strip(" ·"), redone


# ── ③ 三種格式 ───────────────────────────────────────────────────────────────────────────────────────
CTX: dict = {}


def _read_rows(v2: Path, book: str) -> list:
    p = Path(v2) / "output" / ("VRN2_%s_latest.json" % book)
    try:
        rows = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else []
    except (OSError, ValueError):
        rows = []
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def build_ctx(v2: Path) -> dict:
    summ = {str(r.get("FILENAME") or ""): r for r in _read_rows(v2, "Summary")}
    basic = {str(r.get("FILENAME") or ""): r for r in _read_rows(v2, "BasicInfo")}
    return {"summary": summ, "basic": basic, "stats": {"stripped": 0, "topic": 0, "upside": 0}}


def fix_row(book: str, row: dict, count: bool = False) -> dict:
    """一列(值都當字串看)→ 改好的一列(只動 Summary 的 TITLE / 四點 · Combined 的 TOPIC & SUMMARY)。"""
    st = CTX.get("stats") if count else None
    if book == "Summary":
        out = dict(row)
        for k in ("TITLE",) + POINTS:
            if k in out and isinstance(out[k], str):
                new = strip_lead(out[k])
                if new != out[k]:
                    out[k] = new
                    if st is not None:
                        st["stripped"] += 1
        return out
    if book == "Combined" and TOPIC in row:
        fn = str(row.get("FILENAME") or "")
        summ = CTX.get("summary", {}).get(fn, {})
        basic = CTX.get("basic", {}).get(fn, {})
        if not (summ or basic):
            return row
        text, redone = compose(row, basic, summ)
        out = dict(row)
        out[TOPIC] = text
        if st is not None:
            st["topic"] += int(text != row.get(TOPIC))
            st["upside"] += int(redone)
        return out
    return row


def do_json(book, path, dry, unmapped):
    if book not in ("Summary", "Combined"):
        return _v0100["do_json"](book, path, dry, unmapped)
    text = path.read_text(encoding="utf-8")
    rows = json.loads(text)
    if not isinstance(rows, list):
        return {"state": "不是列清單 · 不動", "rows": 0}
    ind, exact = V0100._indent_of(text, rows)
    fixed = [fix_row(book, r, count=True) if isinstance(r, dict) else r for r in rows]
    new = V0100._with_cols(book, fixed, unmapped)
    if new == rows and all(list(r)[-2:] == list(COLS) for r in rows if isinstance(r, dict)):
        return {"state": "不變", "rows": len(rows)}
    if not dry:
        V0100._atomic(path, json.dumps(new, ensure_ascii=False, indent=ind).encode("utf-8"))
    return {"state": "改寫" if exact else "改寫(原縮排認不出 · 用 1)", "rows": len(rows)}


def do_csv(book, path, dry, unmapped):
    if book not in ("Summary", "Combined"):
        return _v0100["do_csv"](book, path, dry, unmapped)
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    if not text.strip():
        return {"state": "空檔 · 不動", "rows": 0}
    term = "\r\n" if "\r\n" in text else "\n"
    grid = list(csv.reader(io.StringIO(text, newline="")))
    head, body = grid[0], grid[1:]
    keep = [h for h in head if h not in COLS]
    out = [keep + list(COLS)]
    for row in body:
        d = dict(zip(head, row + [""] * (len(head) - len(row))))
        f = fix_row(book, d)
        out.append([f.get(h, "") for h in keep] + list(V0100.derive(book, f, unmapped)))
    buf = io.StringIO()
    csv.writer(buf, lineterminator=term).writerows(out)
    new = buf.getvalue()
    if new == text:
        return {"state": "不變", "rows": len(body)}
    if not dry:
        V0100._atomic(path, (b"\xef\xbb\xbf" if bom else b"") + new.encode("utf-8"))
    return {"state": "改寫", "rows": len(body)}


def do_parquet(book, path, dry, unmapped):
    if book not in ("Summary", "Combined"):
        return _v0100["do_parquet"](book, path, dry, unmapped)
    try:
        import pyarrow as pa  # noqa: WPS433
        import pyarrow.parquet as pq  # noqa: WPS433
    except Exception as error:  # noqa: BLE001
        return {"state": "沒寫:%s(這支 Python 的 pyarrow 載不起來)" % type(error).__name__, "rows": 0, "skip": True}
    table = pq.read_table(str(path))
    names = table.column_names
    fields = [c for c in (("TITLE",) + POINTS if book == "Summary" else (TOPIC,)) if c in names]
    if fields:
        need = sorted(set(fields) | {c for c in ("FILENAME", "NAME", "YFINANCE_TICKER", "TICKER", "RATING", "TARGET_PRICE(ADJ)", "ADJ_CLOSE") if c in names})
        cols = {c: table.column(c).to_pylist() for c in need}
        n = table.num_rows
        newcols = {c: [] for c in fields}
        for i in range(n):
            d = {c: ("" if cols[c][i] is None else str(cols[c][i])) for c in need}
            f = fix_row(book, d)
            for c in fields:
                newcols[c].append(f.get(c, d.get(c)))
        changed = any(newcols[c] != [("" if v is None else str(v)) for v in cols[c]] for c in fields)
        if changed:
            for c in fields:
                table = table.set_column(names.index(c), c, pa.array(newcols[c], type=pa.string()))
            if not dry:
                fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
                os.close(fd)
                pq.write_table(table, tmp)
                os.replace(tmp, str(path))
    return _v0100["do_parquet"](book, path, dry, unmapped)


def apply(v2, dry: bool = False) -> dict:
    global CTX
    CTX = build_ctx(Path(v2))
    rec = _v0100["apply"](v2, dry)
    st = CTX.get("stats") or {}
    rec["module"] = "%s %s" % (DISPLAY_NAME, VERSION)
    rec["summary_cleanup"] = {"stripped_cells": st.get("stripped", 0), "topic_rows": st.get("topic", 0), "upside_rows": st.get("upside", 0),
                              "rule": "四點 / 標題去開頭符號 · 主題與摘要 = Name(YFinance Ticker, 評等) - 原文標題 · 評價點排第一 · 上漲空間 = 調整後目標價 ÷ 調整後收盤 − 1"}
    if rec.get("lamp") in ("GREEN", "YELLOW") and (st.get("stripped") or st.get("topic")):
        rec["why"] = "%s · 四點去符號 %d 格 · 主題與摘要 %d 列(改算上漲空間 %d)" % (rec.get("why", ""), st.get("stripped", 0), st.get("topic", 0), st.get("upside", 0))
    if not dry:
        try:
            (Path(v2) / RECEIPT).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    return rec


V0100.do_json, V0100.do_csv, V0100.do_parquet = do_json, do_csv, do_parquet


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    V0100.do_json, V0100.do_csv, V0100.do_parquet = _v0100["do_json"], _v0100["do_csv"], _v0100["do_parquet"]
    buf = io.StringIO()
    so = sys.stdout
    sys.stdout = buf
    try:
        rc = V0100.selftest()
    finally:
        sys.stdout = so
        V0100.do_json, V0100.do_csv, V0100.do_parquet = do_json, do_csv, do_parquet
    chk("⓪ v0100 自測照過(前版自己的接線)· %s" % (buf.getvalue().strip().splitlines() or ["—"])[-1][:60], rc == 0)
    cases = {"➢ 國內外業務雙管齊下": "國內外業務雙管齊下", "• Data center": "Data center", "⚫ 營收": "營收", "- 世足賽": "世足賽", "➢ \n25Q4 預估營收": "25Q4 預估營收",
             "(1) 25Q3 單季營收": "25Q3 單季營收", "① 產能": "產能", "1、毛利率": "毛利率", "1.5 倍成長": "1.5 倍成長", "「逢低買進」評等": "「逢低買進」評等",
             "2026 年 EPS 13 元": "2026 年 EPS 13 元", "We keep": "We keep", "▶▶ 重點": "重點", "※ 註": "註", "": ""}
    chk("① 去開頭符號:➢ • ⚫ - ▶ ※ (1) ① 1、 都刪 · 1.5 倍 / 「 」/ 年份 / 英文不動 · 內文不改", all(strip_lead(a) == b for a, b in cases.items()))
    comb = {"FILENAME": "a.pdf", "NAME": "泓德能源", "YFINANCE_TICKER": "6873.TW", "RATING": "逢低買進", "TARGET_PRICE(ADJ)": "200.31", "ADJ_CLOSE": "169.00", TOPIC: "x"}
    summ = {"TITLE": "- 國內案場進度低預期,擴展海外擺脫依賴",
            "POINT_1": "➢ 泓德能源公告 25Q2 財報:營收 18.89 億元", "POINT_2": "➢ 同步下修目標價至208 元(16X 25(F)PER),潛在上漲空間22.7%,投資評等調降至「逢低買進」。",
            "POINT_3": "➢ 太陽能進度落後", "POINT_4": ""}
    text, redone = compose(comb, {}, summ)
    parts = text.split(" · ")
    chk("② 標題 = Name(YFinance Ticker, 評等) - 原文標題(去開頭符號)", parts[0] == "泓德能源(6873.TW, 逢低買進) - 國內案場進度低預期,擴展海外擺脫依賴")
    chk("③ 評價那一點排第一 · 上漲空間改用 200.31 ÷ 169 − 1 = 18.5% · 後附算法 · 其他點去符號照順序 · 空點略",
        redone and parts[1].startswith("同步下修目標價至208 元") and "潛在上漲空間18.5%" in parts[1] and parts[1].endswith("\uff1b調整後目標價 200.31 ÷ 調整後收盤 169 = 上漲空間 18.5%")
        and parts[2] == "泓德能源公告 25Q2 財報:營收 18.89 億元" and parts[3] == "太陽能進度落後" and len(parts) == 4)
    t2, r2 = compose(dict(comb, RATING=""), {}, {"TITLE": "標題", "POINT_1": "• 營收成長", "POINT_2": "• 毛利率", "POINT_3": "• 費用", "POINT_4": "• 庫存"})
    p2 = t2.split(" · ")
    chk("④ 四點沒有評價句 → 第一點補「評價 · 調整後目標價 ÷ 調整後收盤 · 上漲空間」· 仍是四點 · 沒有評等 → 標題只寫代號",
        r2 and p2[0] == "泓德能源(6873.TW) - 標題" and p2[1] == "評價\uff1a調整後目標價 200.31 ÷ 調整後收盤 169 = 上漲空間 18.5%" and p2[2:] == ["營收成長", "毛利率", "費用"])
    t3, r3 = compose(dict(comb, ADJ_CLOSE=""), {}, summ)
    chk("⑤ 調整後收盤缺 → 數字不動(只排序 · 去符號)", not r3 and "潛在上漲空間22.7%" in t3 and "調整後目標價" not in t3)
    t4, _r4 = compose({"FILENAME": "b.pdf", "NAME": "", "YFINANCE_TICKER": "", "TICKER": "3231", "RATING": "Buy", "TARGET_PRICE(ADJ)": "160", "ADJ_CLOSE": "128"},
                      {"ENGLISH_NAME": "Wistron", "YFINANCE_TICKER": "3231.TW"}, {"TITLE": "Strong sales", "POINT_1": "Reiterate Buy with TP NT$165, 25% upside", "POINT_2": "GB200 ramp"})
    chk("⑥ 英文報告:Name 用英文名 · Yahoo 代號用基本資料 · 「25% upside」改成 25.0%(160 ÷ 128)",
        t4 == "Wistron(3231.TW, Buy) - Strong sales · Reiterate Buy with TP NT$165, 25.0% upside\uff1b調整後目標價 160 ÷ 調整後收盤 128 = 上漲空間 25.0% · GB200 ramp")
    try:
        import pyarrow as pa  # noqa: WPS433
        import pyarrow.parquet as pq  # noqa: WPS433
        pa_ok = True
    except Exception:  # noqa: BLE001
        pa_ok = False
        print("[SKIP] 這支 Python 的 pyarrow 用不了 · Parquet 那段不驗", flush=True)
    with tempfile.TemporaryDirectory(prefix="vrn2-booksource101-") as td:
        v2 = Path(td) / "VIA_Reports" / "vrn2"
        out = v2 / "output"
        out.mkdir(parents=True)
        basic = [{"REPORT_DATE": "2025-08-19", "FILENAME": "a.pdf", "TICKER": "6873", "NAME": "泓德能源", "BROKER": "兆豐", "RATING": "逢低買進", "TITLE": "國內案場進度低預期"}]
        sm = [{"REPORT_DATE": "2025-08-19", "FILENAME": "a.pdf", "TICKER": "6873", "BROKER": "兆豐", "TITLE": "國內案場進度低預期", "POINT_1": "➢ 營收成長", "POINT_2": "➢ 潛在上漲空間22.7%", "POINT_3": "", "POINT_4": "", "POINTS_OK": "3"}]
        cb = [{"REPORT_DATE": "2025-08-19", "FILENAME": "a.pdf", "TICKER": "6873", "YFINANCE_TICKER": "6873.TW", "NAME": "泓德能源", "BROKER": "兆豐", "RATING": "逢低買進",
               "TARGET_PRICE(ADJ)": "200.31", "ADJ_CLOSE": "169.00", TOPIC: "國內案場進度低預期 · ➢ 營收成長 · ➢ 潛在上漲空間22.7%", "STATUS": "s"}]
        for name, rows, ind in (("BasicInfo", basic, 1), ("Summary", sm, 1), ("Combined", cb, 1)):
            (out / ("VRN2_%s_latest.json" % name)).write_text(json.dumps(rows, ensure_ascii=False, indent=ind), encoding="utf-8")
            b = io.StringIO()
            w = csv.DictWriter(b, fieldnames=list(rows[0]), lineterminator="\r\n")
            w.writeheader()
            w.writerows(rows)
            (out / ("VRN2_%s_latest.csv" % name)).write_bytes(b"\xef\xbb\xbf" + b.getvalue().encode("utf-8"))
        if pa_ok:
            pq.write_table(pa.table({k: [str(v)] for k, v in cb[0].items()}), str(out / "VRN2_Combined_latest.parquet"))
        rec = apply(v2)
        sj = json.loads((out / "VRN2_Summary_latest.json").read_text(encoding="utf-8"))[0]
        cj = json.loads((out / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))[0]
        want = "泓德能源(6873.TW, 逢低買進) - 國內案場進度低預期 · 潛在上漲空間18.5%\uff1b調整後目標價 200.31 ÷ 調整後收盤 169 = 上漲空間 18.5% · 營收成長"
        chk("⑦ JSON:Summary 四點去符號 · Combined 主題與摘要新格式 · 其他欄不動 · 最後兩欄 BROKER_EN / SOURCE · 收據記筆數",
            sj["POINT_1"] == "營收成長" and sj["POINT_2"] == "潛在上漲空間22.7%" and sj["POINTS_OK"] == "3" and cj[TOPIC] == want and cj["STATUS"] == "s"
            and list(sj)[-2:] == ["BROKER_EN", "SOURCE"] and list(cj)[-2:] == ["BROKER_EN", "SOURCE"] and cj["BROKER_EN"] == "Mega"
            and rec["summary_cleanup"]["stripped_cells"] == 2 and rec["summary_cleanup"]["topic_rows"] == 1 and rec["summary_cleanup"]["upside_rows"] == 1 and rec["module"].endswith("v0101"))
        sc = list(csv.DictReader(io.StringIO((out / "VRN2_Summary_latest.csv").read_bytes().decode("utf-8-sig"))))[0]
        cc = list(csv.DictReader(io.StringIO((out / "VRN2_Combined_latest.csv").read_bytes().decode("utf-8-sig"))))[0]
        chk("⑧ CSV 同一套:四點去符號 · 主題與摘要新格式 · BROKER_EN / SOURCE 最後", sc["POINT_1"] == "營收成長" and cc[TOPIC] == want and list(cc)[-2:] == ["BROKER_EN", "SOURCE"])
        if pa_ok:
            t = pq.read_table(str(out / "VRN2_Combined_latest.parquet"))
            chk("⑨ Parquet 同一套:主題與摘要新格式 · 最後兩欄 BROKER_EN / SOURCE", t.column(TOPIC).to_pylist() == [want] and t.column_names[-2:] == ["BROKER_EN", "SOURCE"])
        snap = {p.name: p.read_bytes() for p in out.iterdir()}
        rec2 = apply(v2)
        chk("⑩ 再跑:全部不變(冪等)· 去符號 0 · 主題與摘要 0", {p.name: p.read_bytes() for p in out.iterdir()} == snap and rec2["summary_cleanup"]["stripped_cells"] == 0
            and rec2["summary_cleanup"]["topic_rows"] == 0)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 第 3 行 ACCEL-BRIDGE 標記 · 不連外 · 前版接線(do_json / do_csv / do_parquet 指本版)",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M)
        and V0100.do_json is do_json and V0100.do_csv is do_csv and V0100.do_parquet is do_parquet)
    print("[%s] %s %s --selftest · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest()
    if not argv or argv[0] != "apply":
        print("用法:python %s apply [--v2 <VIA_Reports\\vrn2>] [--dry-run] · --selftest" % Path(__file__).name, flush=True)
        return 2
    v2 = Path(opt("--v2") or (Path(os.environ["VIA_ROOT"]) / "VIA_Reports" / "vrn2" if os.environ.get("VIA_ROOT") else HERE.parent.parent / "VIA_Reports" / "vrn2"))
    rec = apply(v2, dry="--dry-run" in argv)
    print("[計] 輸出冊 Source / Broker 欄 · 四點 / 主題與摘要 · %s · %s" % (rec["lamp"], rec["why"]), flush=True)
    print("[%s] %s %s · %s" % (rec["lamp"], DISPLAY_NAME, VERSION, rec["why"][:240]), flush=True)
    return 0 if rec["lamp"] in ("GREEN", "YELLOW", "GRAY") else 1


if __name__ == "__main__":
    sys.exit(main())

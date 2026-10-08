#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG394_LayoutRestore v0100 — 版面還原:資訊區 / 本文區 / 圖 / 排除區 · 扁平文字裡的表格還原 · 合併儲存格 · 表格驗算

操作員 R36(2026-10-01):「資料區可能在上左右甚至下 … 都稱資訊區」「不管資訊區或是本文區 擷取下來都有出現類似表格的樣子 把他提出去到
資訊區並還原表格」「本文區還原原本的樣子但一句一資料(有據點)有字體大小粗細識別 有類別(文表圖) 也有次類別(大中小標題/本文/字體小且無關的頁尾)」
「財報頁有時候為左右垂直表格 先左右拆 在上下拆 然後擷取表格 首頁也應該這樣」「堆疊數表也拆」「經準抓到小字體部相關頁尾及小字體部相關的報告後方
附錄之類的跟他的標題部擷取」「所有的表用垂直線當間隔 內部文字去空格且TRIM過」「合併儲存格的解決問題」「驗證表格正確性問題」;
另附 OCR 扁平文字四段(兆豐晨會指數表 · Citi 3231 Earnings Summary · GS Mitac / Hon Hai Exhibit 1):「表格分為 表號: 說明 / 表頭 / 表 /
資料來源: 第一個跟最後一個未必有 … 如何識別如何還原」。規則冊 VIA_VRN_LayoutRestore_SSOT_v*.json(本支照冊讀,不另寫第二份)。

一、扁平文字表格還原(text 模式;PDF 每個葉區也走同一把):
  ① 值 token = 千分位數 · 小數 · 百分比 · 帶正負號 · 括號負數 · 獨立「-」(空值)。年度 2024A / 2025E、「S&P 500」「日經225」的整數不是值。
  ② 列 = 一段非值文字(列名)+ 緊接的一串值;連續 ≥3 列、列名 ≤60 字、值數取眾數 k → 一張表(值數不同的列照列出 → 形狀紅)。
  ③ 第一列前面那段:表頭 = 冊上表頭詞的最長連鎖(「股市指數名稱收盤指數漲跌漲跌幅」連寫也拆得開);詞數 = n×(k+1) 且重複 → 並排 n 張;
     單位列「(NT$M) (NT$) (%)…」個數 = k → 掛到各值欄;剩下的「31 Dec」併回首欄表頭(Year to 31 Dec);
     說明 = 表頭前最後一句(去掉目錄點線項)→ 表號(Exhibit 1 / 圖表 3 / 表 2,可無)+ 標題。資料來源 = 表後 Source: / 資料來源:(可無)。
  ④ 列名內的「收盤指數最近更新日: 20251204」= 表註(移出列名);列名前綴的分組詞(美國 / 亞洲 / 歐洲 / 新興)= 分組,文字模式不知它管哪幾列
     → 誠實標 GROUP_UNPLACED(不猜)。目錄點線項 → 目錄表(章節 | 頁次)。免責句 → 排除區。
  ⑤ 圖不是表:Exhibit / Figure / 圖 說明後面若是一串等差數(座標軸刻度 350,000 → 50,000 · 120% → -40%)夾著零星數(資料標籤)、
     X 軸標籤(2024 / 2025E / Jul-14)、圖例、Source → 判 FIGURE。柱高只在影像 / 向量圖裡,文字層沒有 → **不造表**,只列刻度 / 標籤 / 圖例。
二、PDF 版面(page 模式):fitz get_text("dict") 每行字級 / 粗體(flags & 16)· find_tables 畫線表(合併格:表頭 None 向右延、首欄 None 向下延;
  整欄全空 → 左右拆;整列全空或數字列後出現新表頭 → 上下拆)· 表 / 影像當成不可切的整塊 → ENG392 遞迴 XY 切(**先左右、再上下**)。
  葉區分類:EXCLUDED(小字 < 本文×0.85 且在頁底帶 / 有免責字 · 附錄標題及其後的小字,標題一併不擷取)· FIGURE(影像)·
  INFO(上 / 下頁緣帶 · 左 / 右窄側欄 · 鍵值密集 · 一切表)· BODY(其餘)。本文葉區裡抽出的扁平表 → 移到資訊區。
  本文一句一列:據點 = p頁 · 區路徑 · 行號 · bbox;字級 · 粗體;次類別 H1 ≥1.5× · H2 ≥1.25× · H3 ≥1.1× 或粗體短行 · BODY · SMALL。
三、驗算(每張表都做,判 GREEN / YELLOW / RED):形狀(每列值數一致)· 欄型一致(百分比欄 / 數字欄)· 表頭欄數 ·
  漲跌幅 ≈ 漲跌 ÷ (收盤 − 漲跌) · 成長率 ≈ 本期 ÷ 上期 − 1(±0.6pp)· 隱含常數(兩欄相乘 / 相除各列幾乎相同:P/E × EPS ≈ 股價、
  淨利 ÷ EPS ≈ 股數)· 已確立的式子個別列不合 → 標疑似 OCR 誤值。
輸出:VIA_Reports/vrn/layout_restore/<檔>.layout.md(所有表垂直線分隔 · 格內 CJK 字間空白去掉、英數詞間壓成一格、TRIM)· <檔>.layout.json ·
      LAYOUT_latest.json / .html。只讀來源,不改來源。零網路;不用 TA-Lib;正本唯讀。只收 VCGC 呼叫(VIA_FROM_VCGC=YES;--selftest 例外)。
CLI:restore --in <pdf|夾> [--pages 1|all|1-3] · text --in <txt> · --selftest
結束碼:0 全綠 · 1 有紅 · 2 沒有輸入 / 拒絕 · 3 有黃無紅
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

import html as _html
import importlib.util
import json
import os
import re
import statistics
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
OUT = VIA / "VIA_Reports" / "vrn" / "layout_restore"
ENGINE = Path(__file__).stem
SSOT_GLOB = "VIA_VRN_LayoutRestore_SSOT_v*.json"
CJK = "㐀-鿿豈-﫿　-〿＀-￯"
ZONE_ZH = {"INFO": "資訊區", "BODY": "本文區", "FIGURE": "圖", "EXCLUDED": "排除區"}
CAT_ZH = {"text": "文", "table": "表", "figure": "圖"}
ORDER = {"RED": 0, "YELLOW": 1, "GREEN": 2}

# 值 token:千分位 · 小數 · 百分比 · 帶號 · 括號負數 · 獨立「-」;前後緊貼英數 / 小數點 / 逗號的不算(3231.TW · Jul-14 · G4826Z5)
VAL_RX = re.compile(r"(?<![A-Za-z0-9.,])(?:\(\d[\d,]*(?:\.\d+)?\)"
                    r"|[+\-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?%?"
                    r"|[+\-]?\d+\.\d+%?"
                    r"|[+\-]?\d+%"
                    r"|[+\-]\d+"
                    r"|-(?=\s|$))(?![A-Za-z0-9])")
NUMTOK_RX = re.compile(r"(?<![A-Za-z0-9.,])(?:[+\-]?\d[\d,]*(?:\.\d+)?%?|-(?=\s))(?![A-Za-z0-9])")
YEAR_KEY_RX = re.compile(r"^(?:(?:19|20)\d{2}[AEFP]?|[1-4]Q\d{2}[AEF]?|[12]H\d{2}[AEF]?|FY\d{2,4}[AEF]?)$")
UNIT_RX = re.compile(r"\(([^()]{1,10})\)")
SENT_RX = re.compile(r"(?<=[。！？!?；;])(?![”」』)）\"])|(?<=\.)\s+(?=[A-Z\"“(一-鿿])|\s+(?=[•●■▪◆]\s)")
TOC_HEAD_RX = re.compile(r"目\s*錄(?:\s*頁\s*次)?")
KV_LINE_RX = re.compile(r"^\s*([^:：]{1,24}?)\s*(?<!\d)[:：]\s*(\S.*)$")   # 1:51 這種時間不拆


# ---------------------------------------------------------------- rule book

_SSOT_CACHE: dict | None = None


def ssot() -> dict:
    global _SSOT_CACHE
    if _SSOT_CACHE is None:
        hits = sorted(REG.glob(SSOT_GLOB))
        if not hits:
            raise FileNotFoundError("規則冊 " + SSOT_GLOB + " 不在 registry(本支不另寫第二份)")
        _SSOT_CACHE = json.loads(hits[-1].read_text(encoding="utf-8"))
        _SSOT_CACHE["_path"] = hits[-1].name
    return _SSOT_CACHE


def _rx(key: str) -> re.Pattern:
    return re.compile(ssot()[key])


def _hdr_rx() -> re.Pattern:
    terms = sorted(set(ssot()["header_vocab"]), key=len, reverse=True)
    alt = "|".join(re.escape(t) + (r"(?![A-Za-z])" if re.search(r"[A-Za-z]$", t) else "") for t in terms)
    return re.compile(f"(?:{alt})")


# ---------------------------------------------------------------- text primitives

def tidy(s) -> str:
    """格內整理:空白壓成一格 · CJK 與任何字之間的空白去掉 · TRIM。"""
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    s = re.sub(rf"(?<=[{CJK}]) (?=\S)|(?<=\S) (?=[{CJK}])", "", s)
    return s


def md_cell(s) -> str:
    return tidy(s).replace("|", "\\|")


def md_table(columns: list, rows: list) -> str:
    cols = [md_cell(c) for c in columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        cells = [md_cell(c) for c in list(r) + [""] * (len(cols) - len(r))]
        out.append("| " + " | ".join(cells[:len(cols)]) + " |")
    return "\n".join(out)


def parse_num(v):
    """'1,234.5' → 1234.5 · '-0.1%' → -0.1 · '(12)' → -12 · '-' / 文字 → None"""
    t = tidy(v).replace(",", "").replace("+", "")
    if not t or t in ("-", "—", "–", "n.a.", "NA", "N/A", "na"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").rstrip("%").replace("−", "-")
    try:
        x = float(t)
    except ValueError:
        return None
    return -x if neg else x


def _fmt(x: float) -> str:
    return f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.4g}"


def _decimals(v) -> int:
    m = re.search(r"\.(\d+)", str(v))
    return len(m.group(1)) if m else 0


def sentences(text: str, base: int = 0, blocked: list | None = None) -> list:
    """[(start, end, sentence)] — 擋掉的區段(表 / 圖 / 目錄)不切進句子。"""
    blocked = sorted(blocked or [])
    pieces, cur = [], 0
    for a, b in blocked:
        a, b = a - base, b - base
        if a > cur:
            pieces.append((cur, a))
        cur = max(cur, b)
    if cur < len(text):
        pieces.append((cur, len(text)))
    out = []
    for a, b in pieces:
        seg = text[a:b]
        pos = 0
        for m in list(SENT_RX.finditer(seg)) + [None]:
            end = m.start() if m else len(seg)
            chunk = seg[pos:end]
            if tidy(chunk):
                lead = len(chunk) - len(chunk.lstrip())
                out.append((base + a + pos + lead, base + a + end, tidy(chunk)))
            pos = m.end() if m else len(seg)
    return out


# ---------------------------------------------------------------- flattened tables

def _rows(s: str) -> list:
    rows, pos, cur = [], 0, None
    for m in VAL_RX.finditer(s):
        gap = s[pos:m.start()]
        if cur is not None and not gap.strip():
            cur["vals"].append(m)
        else:
            cur = {"gap": gap, "g0": pos, "vals": [m]}
            rows.append(cur)
        pos = m.end()
    return rows


def _runs(rows: list) -> list:
    R = ssot()["tables"]
    runs, i = [], 0
    while i < len(rows):
        if len(rows[i]["vals"]) < R["min_values"]:
            i += 1
            continue
        j = i + 1
        while (j < len(rows) and len(rows[j]["vals"]) >= R["min_values"] and rows[j]["gap"].strip()
               and len(tidy(rows[j]["gap"])) <= R["max_label_chars"]):
            j += 1
        if j - i >= R["min_rows"]:
            runs.append((i, j))
        i = max(j, i + 1)
    return runs


def _strip_groups(label: str) -> tuple:
    groups, changed = [], True
    while changed:
        changed = False
        for g in ssot()["group_labels"]:
            if label.startswith(g) and len(label) > len(g):
                groups.append(g)
                label = label[len(g):].lstrip()
                changed = True
    return label, groups


def _notes_out(label: str) -> tuple:
    notes = [tidy(m.group(0)) for m in _rx("note_kv_rx").finditer(label)]
    return tidy(_rx("note_kv_rx").sub(" ", label)), notes


def _caption(pre_text: str) -> str:
    t = pre_text
    last = None
    for m in _rx("toc_rx").finditer(t):
        last = m
    if last is not None:
        t = t[last.end():]
    t = t.rstrip()
    cut = max((m.end() for m in re.finditer(r"[。！？!?;；\n]|\.\s", t)), default=0)
    cap = tidy(t[cut:])
    return cap if 0 < len(cap) <= ssot()["tables"].get("caption_max_chars", 120) else ""


def _split_caption(cap: str) -> tuple:
    m = _rx("caption_rx").match(cap or "")
    if not m:
        return "", cap
    return tidy(m.group("no") or ""), tidy(m.group("title") or "")


def _source_after(s: str, pos: int) -> tuple:
    """(source text, start, end) — 表後 40 字內的 Source: / 資料來源:;沒有就 ("", pos, pos)。"""
    R = ssot()
    win = s[pos:pos + 40 + R["source_max_chars"]]
    m = _rx("source_rx").search(win)
    if not m or m.start() > 40:
        return "", pos, pos
    rest = win[m.start():]
    stop = len(rest)
    for k in R["source_stop"]:
        i = rest.find(k)
        if 0 < i < stop:
            stop = i
    e = re.search(r"。|\.\s|\n", rest)
    if e and e.start() < stop:
        stop = e.end()
    stop = min(stop, R["source_max_chars"])
    return tidy(rest[:stop]), pos + m.start(), pos + m.start() + stop


def text_tables(s: str) -> list:
    R = ssot()
    hdr_rx = _hdr_rx()
    rows = _rows(s)
    out = []
    for i, j in _runs(rows):
        run = rows[i:j]
        counts = Counter(len(r["vals"]) for r in run)
        k = counts.most_common(1)[0][0]
        pre, g0 = run[0]["gap"], run[0]["g0"]
        chains = [m for m in re.finditer(f"{hdr_rx.pattern}(?:\\s*{hdr_rx.pattern})+", pre)]
        chain = chains[-1] if chains and len(pre) - chains[-1].end() <= 90 else None
        notes, issues, units = [], [], []
        col0_extra = ""
        if chain:
            terms = [tidy(t) for t in hdr_rx.findall(chain.group(0))]
            mid = pre[chain.end():]
            cap_text = pre[:chain.start()]
            start_abs = g0 + chain.start()
        else:
            terms = []
            mid = pre
            cap_text = ""
            start_abs = None
        # 單位列
        um = UNIT_RX.findall(mid)
        if len(um) == k:
            units = [tidy(u) for u in um]
            mid = UNIT_RX.sub(" ", mid)
        # 其餘列的列名
        labels = []
        for r in run[1:]:
            lab, ns = _notes_out(r["gap"])
            notes += ns
            labels.append(lab)
        yearish = labels and all(YEAR_KEY_RX.match(x) for x in labels)
        mid_t, ns = _notes_out(mid)
        notes += ns
        if yearish:
            toks = mid_t.split()
            lab0 = toks[-1] if toks and YEAR_KEY_RX.match(toks[-1]) else ""
            if not lab0:
                issues.append("首列列名找不到年度鍵")
            col0_extra = tidy(" ".join(toks[:-1])) if lab0 else ""
        elif chain:
            lab0 = mid_t
        else:
            tail = re.split(r"[。！？!?;；:：]|\.\s", mid_t)[-1]
            lab0 = tidy(tail)[-R["tables"]["max_label_chars"]:]
        if start_abs is None:
            idx0 = pre.rfind(lab0) if lab0 else len(pre)
            start_abs = g0 + max(0, idx0)
            cap_text = pre[:max(0, idx0)]
        caption = _caption(cap_text)
        if caption:
            start_abs = g0 + cap_text.rfind(caption[:4]) if caption[:4] in cap_text else start_abs
        tno, title = _split_caption(caption)
        cap_src = re.search(r"[(（]\s*((?:" + ssot()["source_rx"] + r").*?)[)）]", title)
        if cap_src:                                          # 「(Source: FactSet)」寫在說明裡 → 資料來源
            title = tidy(title[:cap_src.start()] + title[cap_src.end():])
        # 表頭欄數 vs 值數
        side = 1
        if terms:
            if len(terms) == k + 1:
                cols = terms
            elif len(terms) % (k + 1) == 0 and len(terms) > k + 1:
                n = len(terms) // (k + 1)
                parts = [terms[x * (k + 1):(x + 1) * (k + 1)] for x in range(n)]
                if all(p == parts[0] for p in parts):
                    side, cols = n, parts[0]
                else:
                    cols = terms[:k + 1]
                    issues.append(f"表頭 {len(terms)} 詞不是 {k + 1} 的重複")
            elif len(terms) == k:
                cols = [""] + terms
            else:
                cols = ([""] * (k + 1 - len(terms)) + terms)[-(k + 1):]
                issues.append(f"表頭 {len(terms)} 詞 ≠ 值欄 {k} + 列名欄")
        else:
            cols = [""] + [f"欄{x}" for x in range(1, k + 1)]
            issues.append("沒有表頭(冊上表頭詞沒對到)")
        if col0_extra:
            cols = [tidy(cols[0] + " " + col0_extra)] + cols[1:]
        if units:
            cols = [cols[0]] + [f"{c}({u})" if c else f"({u})" for c, u in zip(cols[1:], units)]
        all_labels = [lab0] + labels
        groups = []
        clean = []
        for ri, lab in enumerate(all_labels):
            lab2, gs = _strip_groups(tidy(lab))
            for g in gs:
                groups.append({"group": g, "row": ri + 1, "label": lab2})
            clean.append(lab2)
        body = [[clean[ri]] + [tidy(m.group(0)) for m in r["vals"]] for ri, r in enumerate(run)]
        end_abs = run[-1]["vals"][-1].end()
        src, _s0, s1 = _source_after(s, end_abs)
        if src:
            end_abs = s1
        elif cap_src:
            src = tidy(cap_src.group(1))
        if side > 1:
            issues.append(f"並排 {side} 張(表頭重複 {side} 次);文字模式列序照 OCR 讀序,左右歸屬要 PDF 座標才定")
        if groups:
            issues.append("GROUP_UNPLACED:分組詞 " + "、".join(dict.fromkeys(g["group"] for g in groups))
                          + " 混在列名前(文字模式不知各管哪幾列,已移出列名,不猜歸屬)")
        t = {"origin": "text", "zone": "INFO", "category": "table", "table_no": tno, "title": title, "caption": caption,
             "columns": cols, "rows": body, "units": units, "source": src, "notes": list(dict.fromkeys(notes)),
             "groups": groups, "side_by_side": side, "k": k, "shape": dict(counts), "span": [start_abs, end_abs], "issues": issues}
        t.update(validate(t))
        out.append(t)
    return out


# ---------------------------------------------------------------- figures in text

def _ap(vals: list, tol: float) -> list:
    best = []
    n = len(vals)
    for a in range(n):
        for b in range(a + 1, n):
            d = vals[b][1] - vals[a][1]
            if d == 0:
                continue
            seq, nxt = [vals[a], vals[b]], vals[b][1] + d
            for c in range(b + 1, n):
                if abs(vals[c][1] - nxt) <= abs(d) * tol:
                    seq.append(vals[c])
                    nxt += d
            if len(seq) > len(best):
                best = seq
    return best


def text_figures(s: str, blocked: list) -> list:
    R = ssot()
    F = R["figure"]
    xrx = re.compile(F["x_label_rx"])
    out = []
    for m in _rx("figure_caption_rx").finditer(s):
        if any(a <= m.start() < b for a, b in blocked):
            continue
        sm = _rx("source_rx").search(s, m.end(), m.end() + 1500)
        w_end = sm.start() if sm else min(len(s), m.end() + 700)
        win = s[m.end():w_end]
        toks = []
        for t in NUMTOK_RX.finditer(win):
            raw = t.group(0)
            if re.fullmatch(r"(?:19|20)\d{2}", raw):
                continue
            v = 0.0 if raw == "-" else parse_num(raw)
            if v is not None:
                toks.append((t.start(), v, raw.endswith("%"), raw))
        best, kind = [], ""
        for pct in (False, True):
            group = [(p, v, r) for p, v, isp, r in toks if isp == pct or r == "-"]
            ap = _ap([(p, v) for p, v, _r in group], F["tick_rel_tol"])
            if len(ap) > len(best):
                best, kind = ap, ("pct" if pct else "num")
        src, _a, s1 = _source_after(s, w_end) if sm else ("", w_end, w_end)
        cap_no = tidy(m.group(0)).rstrip(":：")
        if len(best) < F["min_ticks"]:
            continue
        tick_pos = {p for p, _v in best}
        first = min(tick_pos)
        title = tidy(win[:first])
        words = tidy(win[max(tick_pos):]).split(" ")
        xl = [w for w in words if xrx.match(w)]
        x_at = win.find(xl[0], max(tick_pos)) if xl else len(win)
        labels = [r for p, v, isp, r in toks if p not in tick_pos and first < p < x_at and r != "-"]
        last_x = max((win.rfind(x) for x in xl), default=-1)
        legend = tidy(win[last_x + len(xl[-1]):]) if xl else ""
        unit = ""
        srt = sorted(best)
        if len(srt) > 1:
            between = tidy(win[srt[0][0]:srt[1][0]])
            um = re.search(r"[A-Za-z$][A-Za-z$ ]{0,8}$", re.sub(r"[\d,.%+\-]", " ", between).strip())
            unit = tidy(um.group(0)) if um else ""
        out.append({"origin": "text", "zone": "FIGURE", "category": "figure", "table_no": cap_no, "title": title,
                    "axis": {"kind": kind, "ticks": [v for _p, v in best], "count": len(best),
                             "step": round(best[1][1] - best[0][1], 6) if len(best) > 1 else None, "unit": unit},
                    "data_labels": labels, "x_labels": xl, "legend": legend[:240], "source": src,
                    "span": [m.start(), s1 if src else w_end],
                    "verdict": "FIGURE", "note": "座標軸刻度為等差數列 → 這是圖,不是表;柱高 / 線值只在影像或向量圖裡,文字層取不到 → 不造表"})
    return out


# ---------------------------------------------------------------- TOC

def text_toc(s: str) -> list:
    rx = _rx("toc_rx")
    ms = list(rx.finditer(s))
    if len(ms) < 2:
        return []
    groups, cur = [], [ms[0]]
    for a, b in zip(ms, ms[1:]):
        if b.start() - a.end() <= 3:
            cur.append(b)
        else:
            groups.append(cur)
            cur = [b]
    groups.append(cur)
    out = []
    for g in groups:
        if len(g) < 2:
            continue
        rows = []
        for m in g:
            mm = re.match(r"(.*?)\s*\.{5,}\s*(\d+)$", m.group(0))
            rows.append([tidy(mm.group(1)), mm.group(2)] if mm else [tidy(m.group(0)), ""])
        a = g[0].start()
        hd = None
        for hm in TOC_HEAD_RX.finditer(s, max(0, a - 12), a + 1):
            hd = hm
        if hd:
            a = hd.start()
            rows[0][0] = tidy(TOC_HEAD_RX.sub("", rows[0][0])) or rows[0][0]
        rows[0][0] = re.sub(r"^次(?=[一二三四五六七八九十])", "", rows[0][0])
        out.append({"origin": "text", "zone": "INFO", "category": "table", "subcategory": "TOC", "table_no": "", "title": "目錄",
                    "columns": ["章節", "頁次"], "rows": rows, "span": [a, g[-1].end()], "verdict": "GREEN", "checks": [f"目錄 {len(rows)} 項"],
                    "issues": [], "source": "", "notes": []})
    return out


# ---------------------------------------------------------------- validation

def validate(t: dict) -> dict:
    V = ssot()["validation"]
    cols, rows = t["columns"], t["rows"]
    k = len(cols) - 1
    checks, issues, idents = [], list(t.get("issues") or []), []
    lamp = "GREEN"
    shape = Counter(len(r) - 1 for r in rows)
    if len(shape) > 1:
        issues.append("形狀不一致:每列值數 " + " · ".join(f"{a}值×{b}列" for a, b in sorted(shape.items())))
        lamp = "RED"
    else:
        checks.append(f"形狀 {len(rows)} 列 × {k} 值欄 一致")
    raw = [[r[c] if c < len(r) else "" for r in rows] for c in range(1, k + 1)]
    num = [[parse_num(v) for v in col] for col in raw]
    kinds = []
    for c, col in enumerate(raw):
        filled = [v for v in col if tidy(v) not in ("", "-", "—", "–")]
        pct = sum(1 for v in filled if tidy(v).endswith("%"))
        nums = sum(1 for v in filled if parse_num(v) is not None)
        if not filled:
            kinds.append("empty")
        elif pct == len(filled):
            kinds.append("pct")
        elif nums == len(filled):
            kinds.append("num")
        elif nums == 0:
            kinds.append("text")
        else:
            kinds.append("mixed")
            issues.append(f"欄「{cols[c + 1]}」數字 / 文字混雜")
            if lamp == "GREEN":
                lamp = "YELLOW"
    checks.append("欄型 " + " · ".join(f"{cols[c + 1] or c + 1}:{kd}" for c, kd in enumerate(kinds)))
    n = len(rows)

    def name(c):
        return cols[c + 1] or f"欄{c + 1}"

    # 漲跌幅 ≈ 漲跌 ÷ (收盤 − 漲跌)
    for p, kd in enumerate(kinds):
        if kd != "pct":
            continue
        best = None
        for a in range(k):
            for b in range(k):
                if a == b or kinds[a] != "num" or kinds[b] != "num":
                    continue
                ok, tot, bad = 0, 0, []
                for r in range(n):
                    lv, ch, pv = num[a][r], num[b][r], num[p][r]
                    if None in (lv, ch, pv) or lv - ch == 0:
                        continue
                    tot += 1
                    tol = 0.5 * 10 ** -_decimals(raw[p][r]) + V["pct_tol_extra"]
                    if abs(ch / (lv - ch) * 100 - pv) <= tol:
                        ok += 1
                    else:
                        bad.append(r + 1)
                if tot >= 3 and ok / tot >= V["identity_share"] and (best is None or ok > best[0]):
                    best = (ok, tot, a, b, bad)
        if best:
            ok, tot, a, b, bad = best
            idents.append(f"{name(p)} ≈ {name(b)} ÷ ({name(a)} − {name(b)}) × 100:{ok}/{tot} 列成立")
            if bad:
                issues.append(f"列 {bad} 不合「{name(p)}」驗算(疑 OCR 誤值)")
    # 成長率 ≈ 本期 ÷ 上期 − 1(年度鍵的表)
    if n >= 3 and all(YEAR_KEY_RX.match(tidy(r[0])) for r in rows):
        for g in range(k):
            if kinds[g] not in ("num", "pct"):
                continue
            for x in range(k):
                if x == g or kinds[x] != "num":
                    continue
                ok, tot, bad = 0, 0, []
                for r in range(1, n):
                    cur, prv, gv = num[x][r], num[x][r - 1], num[g][r]
                    if None in (cur, prv, gv) or prv == 0:
                        continue
                    tot += 1
                    if abs((cur / prv - 1) * 100 - gv) <= V["growth_tol_pp"]:
                        ok += 1
                    else:
                        bad.append(r + 1)
                if tot >= 2 and ok / tot >= V["identity_share"]:
                    idents.append(f"{name(g)} ≈ {name(x)} 本期 ÷ 上期 − 1:{ok}/{tot} 列成立")
                    if bad:
                        issues.append(f"列 {bad} 不合「{name(g)}」成長率驗算(疑 OCR 誤值)")
    # 隱含常數:兩欄相乘 / 相除各列幾乎相同
    consts = []
    for a in range(k):
        for b in range(a + 1, k):
            if kinds[a] not in ("num", "pct") or kinds[b] not in ("num", "pct"):
                continue
            pairs = [(num[a][r], num[b][r]) for r in range(n) if num[a][r] not in (None, 0) and num[b][r] not in (None, 0)]
            if len(pairs) < 3:
                continue

            def cv(xs):
                m = statistics.mean(xs)
                return abs(statistics.pstdev(xs) / m) if m else 9.0
            if cv([x for x, _ in pairs]) < V["constant_cv_max"] or cv([y for _, y in pairs]) < V["constant_cv_max"]:
                continue
            ratio = [x / y for x, y in pairs]
            flip = abs(statistics.mean(ratio)) < 1                # 只報一個方向(商 ≥ 1)
            for op, xs in (("×", [x * y for x, y in pairs]), ("÷", [1 / q for q in ratio] if flip else ratio)):
                c = cv(xs)
                if c <= V["constant_cv_max"]:
                    lhs = f"{name(a)} × {name(b)}" if op == "×" else (f"{name(b)} ÷ {name(a)}" if flip else f"{name(a)} ÷ {name(b)}")
                    consts.append((c, f"{lhs} ≈ {_fmt(statistics.mean(xs))}(各列變異 {c * 100:.1f}%)"))
    # 差額恆等式:甲 − 乙 = 丙(含 甲 = 乙 + 丙)
    seen = set()
    for a in range(k):
        for b in range(k):
            for c in range(k):
                if len({a, b, c}) < 3 or "num" != kinds[a] or "num" != kinds[b] or "num" != kinds[c] or (a, frozenset((b, c))) in seen:
                    continue
                ok, tot, bad = 0, 0, []
                for r in range(n):
                    va, vb, vc = num[a][r], num[b][r], num[c][r]
                    if None in (va, vb, vc):
                        continue
                    tot += 1
                    tol = 0.5 * 10 ** -min(_decimals(raw[a][r]), _decimals(raw[b][r]), _decimals(raw[c][r])) + 1e-9
                    if abs(va - vb - vc) <= tol:
                        ok += 1
                    else:
                        bad.append(r + 1)
                if tot >= 3 and ok / tot >= V["identity_share"]:
                    seen.add((a, frozenset((b, c))))
                    idents.append(f"{name(a)} − {name(b)} = {name(c)}:{ok}/{tot} 列成立")
                    if bad:
                        issues.append(f"列 {bad} 不合「{name(a)} − {name(b)} = {name(c)}」(疑 OCR 誤值)")
    consts.sort()
    for _c, txt in consts[:4]:
        idents.append("隱含常數 " + txt)
    if not idents:
        checks.append("驗算式 0(本表沒有可自證的算式;只核形狀與欄型)")
    if lamp == "GREEN" and issues:
        lamp = "YELLOW"
    return {"verdict": lamp, "checks": checks, "identities": idents, "issues": issues, "kinds": kinds}


# ---------------------------------------------------------------- text mode

def text_restore(text: str) -> dict:
    s = str(text or "")
    R = ssot()
    tables = text_tables(s)
    toc = text_toc(s)
    blocked = [tuple(t["span"]) for t in tables + toc]
    figures = text_figures(s, blocked)
    blocked += [tuple(f["span"]) for f in figures]
    sents = sentences(s, 0, blocked)
    keys = [k.lower() for k in R["disclaimer_keys"]]
    flags = [any(k in x.lower() for k in keys) for _a, _b, x in sents]
    first = next((i for i, f in enumerate(flags) if f), None)
    if first is not None and sum(flags[first:]) * 2 >= len(flags) - first:
        flags = flags[:first] + [True] * (len(flags) - first)       # 免責段之後整段排除(截斷的尾句也算)
    body, excluded = [], []
    for (a, b, x), f in zip(sents, flags):
        row = {"anchor": f"c{a}-{b}", "category": "text", "subcategory": "FOOTER" if f else "BODY", "text": x, "size": None, "bold": None}
        (excluded if f else body).append(row)
    info = sorted(tables + toc, key=lambda t: t["span"][0])
    return {"mode": "text", "info": info, "figures": figures, "body": body, "excluded": excluded,
            "verdict": _worst([t["verdict"] for t in info]) if info else "GREEN"}


def _worst(lamps: list) -> str:
    return min(lamps, key=lambda x: ORDER.get(x, 0)) if lamps else "GREEN"


# ---------------------------------------------------------------- PDF mode

def _eng392():
    hits = sorted(HERE.glob("VRN_ENG392_TextCompleteness_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("eng392_for_" + ENGINE, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def _inside(b, box, slack=1.0) -> bool:
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return box[0] - slack <= cx <= box[2] + slack and box[1] - slack <= cy <= box[3] + slack


def _wmedian(pairs: list) -> float:
    """[(value, weight)] 加權中位數"""
    pairs = sorted(p for p in pairs if p[1] > 0)
    if not pairs:
        return 0.0
    tot, acc = sum(w for _v, w in pairs), 0
    for v, w in pairs:
        acc += w
        if acc * 2 >= tot:
            return v
    return pairs[-1][0]


def fix_table(rows: list) -> list:
    """find_tables 的 extract() → 合併格補值 · 左右(整欄全空)· 上下(整列全空 / 新表頭)拆 → [{columns, rows, merged}]"""
    rows = [[c for c in r] for r in rows if r is not None]
    if not rows:
        return []
    w = max(len(r) for r in rows)
    rows = [r + [None] * (w - len(r)) for r in rows]
    # 左右拆:整欄全空
    empty_cols = [c for c in range(w) if all(not tidy(r[c] or "") and r[c] is not None or r[c] == "" for r in rows)
                  and all((r[c] or "") == "" for r in rows)]
    blocks, cur = [], []
    for c in range(w):
        if c in empty_cols:
            if cur:
                blocks.append(cur)
            cur = []
        else:
            cur.append(c)
    if cur:
        blocks.append(cur)
    out = []
    for cols in blocks:
        sub = [[r[c] for c in cols] for r in rows]
        # 上下拆:整列全空 · 數字列之後出現全文字列(新表頭)
        parts, cur2, seen_num = [], [], False
        for r in sub:
            vals = [tidy(x or "") for x in r]
            if not any(vals):
                if cur2:
                    parts.append(cur2)
                cur2, seen_num = [], False
                continue
            is_num = sum(1 for v in vals[1:] if parse_num(v) is not None) >= 1
            is_hdr = not is_num and sum(1 for v in vals if v) >= 2
            if seen_num and is_hdr and cur2:
                parts.append(cur2)
                cur2, seen_num = [], False
            cur2.append(r)
            seen_num = seen_num or is_num
        if cur2:
            parts.append(cur2)
        for p in parts:
            out.append(_merge_cells(p))
    return out


def _merge_cells(rows: list) -> dict:
    merged = []
    nh = 0
    for r in rows:
        if any(parse_num(x or "") is not None for x in r[1:]):
            break
        nh += 1
    nh = min(nh, max(0, len(rows) - 1)) if len(rows) > 1 else 0
    grid = [list(r) for r in rows]
    for i in range(nh):                                       # 表頭:None → 向右延(同一合併格)
        for c in range(len(grid[i])):
            if grid[i][c] is None and c > 0:
                grid[i][c] = grid[i][c - 1]
                merged.append(f"r{i + 1}c{c + 1}←左")
    for i in range(nh, len(grid)):                            # 首欄:None → 向下延(分組列);其餘 None → 空
        for c in range(len(grid[i])):
            if grid[i][c] is None:
                if c == 0 and i > nh:
                    grid[i][c] = grid[i - 1][c]
                    merged.append(f"r{i + 1}c1←上")
                else:
                    grid[i][c] = ""
                    merged.append(f"r{i + 1}c{c + 1}=空")
    if nh:
        cols = []
        for c in range(len(grid[0])):
            parts = []
            for i in range(nh):
                v = tidy(grid[i][c] or "")
                if v and (not parts or parts[-1] != v):
                    parts.append(v)
            cols.append("/".join(parts))
        body = grid[nh:]
    else:
        cols = [""] + [f"欄{c}" for c in range(1, len(grid[0]))]
        body = grid
    return {"columns": cols, "rows": [[tidy(x or "") for x in r] for r in body], "merged": merged, "header_rows": nh}


def _subcat(size: float, bold: bool, body: float, nchar: int, text: str = "x") -> str:
    F = ssot()["font"]
    if not body:
        return "BODY"
    r = size / body
    short = nchar <= F["heading_max_chars"] and bool(re.search(f"[A-Za-z{CJK}]", text))   # 純數字行不是標題
    if short and r >= F["h1"]:
        return "H1"
    if short and r >= F["h2"]:
        return "H2"
    if short and (r >= F["h3"] or (bold and r >= 0.95)):
        return "H3"
    if r < F["small"]:
        return "SMALL"
    return "BODY"


def _order_lines(lns: list) -> list:
    """讀序:同一條水平帶(垂直中心重疊)的行算同一列,列內由左而右;表格行不會被粗體 / 基線差打亂。"""
    rows = []
    for ln in sorted(lns, key=lambda x: ((x["bbox"][1] + x["bbox"][3]) / 2, x["bbox"][0])):
        cy, h = (ln["bbox"][1] + ln["bbox"][3]) / 2, ln["bbox"][3] - ln["bbox"][1]
        if rows and abs(cy - rows[-1][0]) <= 0.5 * min(h, rows[-1][1]):
            rows[-1][2].append(ln)
        else:
            rows.append([cy, h, [ln]])
    return [ln for _cy, _h, r in rows for ln in sorted(r, key=lambda x: x["bbox"][0])]


def _lines_toc(lns: list) -> list | None:
    """目錄:「標題 … 頁碼」/「標題 頁碼」/ 標題行下一行是頁碼;≥3 項、涵蓋 ≥60% 行、頁碼大致遞增 → [[章節, 頁次]]"""
    heads = [h.lower() for h in ssot().get("toc_heads", [])]
    rows, used, i = [], 0, 0
    while i < len(lns):
        t = tidy(lns[i]["text"])
        m = re.match(r"^(.*?[A-Za-z一-鿿].*?)\s*(?:\.{3,}|…+)?\s+(\d{1,3})$", t)
        if t.lower() in heads:
            used += 1
        elif m:
            rows.append([tidy(m.group(1)), m.group(2)])
            used += 1
        elif i + 1 < len(lns) and re.search(f"[A-Za-z{CJK}]", t) and re.fullmatch(r"\d{1,3}", tidy(lns[i + 1]["text"])):
            rows.append([t, tidy(lns[i + 1]["text"])])
            used += 2
            i += 1
        i += 1
    pg = [int(r[1]) for r in rows]
    if len(rows) >= 3 and used >= 0.6 * len(lns) and sum(1 for a, b in zip(pg, pg[1:]) if b >= a) >= 0.8 * (len(pg) - 1):
        return rows
    return None


def _page_lines(page) -> list:
    F = ssot()["font"]
    d = page.get_text("dict")
    lines = []
    for bi, b in enumerate(d.get("blocks", [])):
        if b.get("type") != 0:
            continue
        for ln in b.get("lines", []):
            spans = [sp for sp in ln.get("spans", []) if sp.get("text", "").strip()]
            if not spans:
                continue
            txt = "".join(sp["text"] for sp in ln["spans"])
            nch = sum(len(sp["text"].strip()) for sp in spans)
            size = _wmedian([(round(sp["size"], 1), len(sp["text"].strip())) for sp in spans])
            bold_ch = sum(len(sp["text"].strip()) for sp in spans if sp.get("flags", 0) & F["bold_flag"] or "Bold" in sp.get("font", ""))
            lines.append({"block": bi, "bbox": tuple(round(x, 1) for x in ln["bbox"]), "text": txt, "size": size,
                          "bold": bold_ch * 2 >= nch, "nch": nch})
    return lines


def page_layout(page, pno: int, state: dict) -> dict:
    R = ssot()
    L, F = R["layout"], R["font"]
    W, H = page.rect.width or 1, page.rect.height or 1
    lines = _page_lines(page)
    tables = []
    try:
        for t in page.find_tables().tables:
            tables.append({"bbox": tuple(round(x, 1) for x in t.bbox), "raw": t.extract()})
    except Exception as ex:                                   # find_tables 不在(舊版 PyMuPDF)→ 誠實記下,只走扁平文字法
        state.setdefault("notes", []).append(f"find_tables 不可用:{ex.__class__.__name__}")
    images = []
    for info in page.get_image_info():
        bb = tuple(round(x, 1) for x in info.get("bbox", (0, 0, 0, 0)))
        if (bb[2] - bb[0]) * (bb[3] - bb[1]) >= W * H * 0.01:
            images.append(bb)
    free = [ln for ln in lines if not any(_inside(ln["bbox"], t["bbox"]) for t in tables)]
    prose = [ln for ln in free if len(VAL_RX.findall(ln["text"])) < 2]          # 本文字級基準:不含表格格子 / 數字列
    if sum(ln["nch"] for ln in prose) >= L.get("min_prose_chars", 300) or not state.get("doc_body"):
        body_size = _wmedian([(ln["size"], ln["nch"]) for ln in (prose or lines)]) or 10.0
    else:
        body_size = state["doc_body"]                         # 圖表頁本文太少 → 用整份文件的本文字級
    blocks = []
    for bi in dict.fromkeys(ln["block"] for ln in free):
        bl = [ln for ln in free if ln["block"] == bi]
        blocks.append((min(x["bbox"][0] for x in bl), min(x["bbox"][1] for x in bl), max(x["bbox"][2] for x in bl),
                       max(x["bbox"][3] for x in bl), "text", bi))
    blocks += [(*t["bbox"], "table", i) for i, t in enumerate(tables)]
    blocks += [(*bb, "image", i) for i, bb in enumerate(images) if not any(_inside(bb, t["bbox"]) for t in tables)]
    e392 = state.get("eng392")
    leaves = e392.xy_cut(blocks, (0, 0, W, H), L["min_gap_pt"]) if e392 and blocks else [("0", (0, 0, W, H), blocks)]
    keys = [k.lower() for k in R["disclaimer_keys"]]
    heads = R["appendix_heads"]
    out = {"page": pno, "size": [round(W, 1), round(H, 1)], "body_size": body_size, "leaves": [], "info": [], "figures": [],
           "body": [], "excluded": []}
    after_head = appx_pending = False
    for path, _box, bl in leaves:
        if appx_pending:
            state["appendix"] = True                          # 第 2 頁起出現附錄標題 → 之後的區(含後面各頁)都是附錄段
        bb = (min(b[0] for b in bl), min(b[1] for b in bl), max(b[2] for b in bl), max(b[3] for b in bl)) if bl else _box
        bb = tuple(round(x, 1) for x in bb)
        anchor = f"p{pno}·{path}"
        tbs = [b for b in bl if b[4] == "table"]
        ims = [b for b in bl if b[4] == "image"]
        lns = [ln for b in bl if b[4] == "text" for ln in free if ln["block"] == b[5]]
        lns = _order_lines(lns)
        for b in tbs:
            for pi, part in enumerate(fix_table(tables[b[5]]["raw"]), 1):
                t = {"origin": "pdf_grid", "zone": "INFO", "category": "table", "table_no": "", "title": "", "caption": "",
                     "anchor": f"{anchor}·T{b[5] + 1}" + (f".{pi}" if pi > 1 else ""), "bbox": tables[b[5]]["bbox"],
                     "columns": part["columns"], "rows": part["rows"], "merged": part["merged"], "source": "", "notes": [],
                     "issues": [f"合併格補值 {len(part['merged'])} 處:" + " ".join(part["merged"][:8])] if part["merged"] else []}
                t.update(validate(t))
                if part["merged"] and t["verdict"] == "YELLOW" and len(t["issues"]) == 1:
                    t["verdict"] = "GREEN"                    # 合併格已補值只是註記,不是錯
                out["info"].append(t)
            out["leaves"].append({"path": path, "zone": "INFO", "where": "表", "category": "table", "bbox": bb})
        for b in ims:
            out["figures"].append({"origin": "pdf_image", "zone": "FIGURE", "category": "figure", "anchor": anchor, "bbox": b[:4],
                                   "verdict": "FIGURE", "note": "影像區:文字不在文字層(要 OCR 才核得到;本支不造表)"})
            out["leaves"].append({"path": path, "zone": "FIGURE", "where": "影像", "category": "figure", "bbox": bb})
        appx_now = False
        foot = [ln for ln in lns if ln["bbox"][1] >= H * L["bottom_band"] and ln["size"] < body_size * F["small"]]
        if foot and len(foot) < len(lns):                      # 區內混到頁底小字(整頁一區時)→ 逐行剔出
            fb = (min(x["bbox"][0] for x in foot), min(x["bbox"][1] for x in foot), max(x["bbox"][2] for x in foot),
                  max(x["bbox"][3] for x in foot))
            out["excluded"].append({"anchor": f"{anchor}·頁底", "bbox": fb, "reason": "小字頁尾(逐行)", "head": tidy(foot[0]["text"])[:40],
                                    "size": _wmedian([(x["size"], x["nch"]) for x in foot]), "lines": len(foot)})
            lns = [ln for ln in lns if ln not in foot]
        hi = next((i for i, ln in enumerate(lns) if ln["nch"] <= F["heading_max_chars"] and (ln["bold"] or ln["size"] >= body_size * 1.05)
                   and any(tidy(ln["text"]).startswith(h) for h in heads)), None)
        if hi is not None and not state.get("appendix"):       # 附錄 / 聲明標題那一行起到本區尾:標題連內容一併不擷取
            post = lns[hi:]
            pb = (min(x["bbox"][0] for x in post), min(x["bbox"][1] for x in post), max(x["bbox"][2] for x in post),
                  max(x["bbox"][3] for x in post))
            why = f"附錄 / 聲明標題「{tidy(post[0]['text'])[:24]}」及其內容"
            out["excluded"].append({"anchor": f"{anchor}·L{hi + 1}", "bbox": pb, "reason": why,
                                    "size": _wmedian([(x["size"], x["nch"]) for x in post]), "head": tidy(post[0]["text"])[:40], "lines": len(post)})
            out["leaves"].append({"path": path, "zone": "EXCLUDED", "where": why, "category": "text", "bbox": pb,
                                  "size": post[0]["size"]})
            lns = lns[:hi]
            after_head = True
            appx_now = pno >= 2
        appx_pending = appx_pending or appx_now
        if not lns:
            continue
        txt = "\n".join(ln["text"] for ln in lns)
        low = txt.lower()
        msize = _wmedian([(ln["size"], ln["nch"]) for ln in lns])
        small = msize < body_size * F["small"]
        disc = sum(1 for k in keys if k in low)
        first = tidy(lns[0]["text"])
        lx0, ly0 = min(ln["bbox"][0] for ln in lns), min(ln["bbox"][1] for ln in lns)      # 位置看文字自己的框(葉區可能含影像)
        lx1, ly1 = max(ln["bbox"][2] for ln in lns), max(ln["bbox"][3] for ln in lns)
        rw = _box[2] - _box[0]                                # 寬度看 XY 切給的區框(欄寬),不看內容框(短行)
        zone, where, why = "BODY", "本文", ""
        if state.get("appendix"):
            zone, why = "EXCLUDED", "報告後方附錄段(附錄標題之後)"
        elif after_head and small:
            zone, why = "EXCLUDED", "附錄 / 聲明標題下的小字"
        elif small and (ly0 >= H * L["bottom_band"] or disc):
            zone, why = "EXCLUDED", "小字頁尾" if not disc else "小字免責 / 聲明"
        elif disc >= 2:
            zone, why = "EXCLUDED", "免責 / 聲明(關鍵字 ≥2)"
        elif small:
            zone, where = "INFO", "小字資訊(作者 / 聯絡 / 註)"
        elif _lines_toc(lns):
            zone, where = "INFO", "目錄"
        else:
            subs = [_subcat(ln["size"], ln["bold"], body_size, ln["nch"], ln["text"]) for ln in lns]
            has_title = any(s in ("H1", "H2") for s in subs)
            kv = sum(1 for ln in lns if KV_LINE_RX.match(ln["text"]) or len(VAL_RX.findall(ln["text"])) >= 2)
            band = rw >= W * L.get("band_min_width", 0.6)       # 頁緣帶要夠寬(欄內靠上的卡片不算頁首)
            if band and ly1 <= H * L["top_band"] and not has_title:
                zone, where = "INFO", "上"
            elif band and ly0 >= H * L["bottom_band"]:
                zone, where = "INFO", "下"
            elif rw <= W * L["side_max_width"] and lx0 >= W * (1 - L["side_edge"]):
                zone, where = "INFO", "右"
            elif rw <= W * L["side_max_width"] and lx1 <= W * L["side_edge"]:
                zone, where = "INFO", "左"
            elif kv / len(lns) >= L["kv_dense"] and kv >= L.get("kv_min_lines", 3):
                zone, where = "INFO", "內(鍵值密集)"
        out["leaves"].append({"path": path, "zone": zone, "where": where if zone == "INFO" else ("" if zone == "BODY" else why),
                              "category": "text", "bbox": bb, "size": msize})
        if zone == "EXCLUDED":
            out["excluded"].append({"anchor": anchor, "bbox": bb, "reason": why, "size": msize, "head": first[:40], "lines": len(lns)})
            continue
        # 葉區文字:扁平表 → 資訊區;圖 → 圖;其餘按區輸出
        offs, pos = [], 0
        for ln in lns:
            offs.append((pos, pos + len(ln["text"])))
            pos += len(ln["text"]) + 1
        tt = text_tables(txt)
        for t in tt:
            t.update({"origin": "pdf_text", "anchor": f"{anchor}·扁平表", "bbox": bb, "moved_from": ZONE_ZH[zone]})
            out["info"].append(t)
        blocked = [tuple(t["span"]) for t in tt]
        for f in text_figures(txt, blocked):
            f.update({"origin": "pdf_text", "anchor": anchor, "bbox": bb})
            out["figures"].append(f)
            blocked.append(tuple(f["span"]))
        rest = [(i, ln) for i, ln in enumerate(lns) if not any(a <= offs[i][0] and offs[i][1] <= b + 1 for a, b in blocked)]
        if zone == "INFO" and where == "目錄":
            out["info"].append({"origin": "pdf_toc", "zone": "INFO", "category": "table", "subcategory": "TOC", "table_no": "",
                                "title": "目錄", "anchor": anchor, "bbox": bb, "columns": ["章節", "頁次"], "rows": _lines_toc(lns),
                                "verdict": "GREEN", "checks": [f"目錄 {len(_lines_toc(lns))} 項 · 頁碼遞增"], "issues": [], "source": "",
                                "notes": []})
            continue
        if zone == "INFO":
            kvrows = []
            for i, ln in rest:
                m = KV_LINE_RX.match(ln["text"])
                kvrows.append([tidy(m.group(1)), tidy(m.group(2))] if m else ["", tidy(ln["text"])])
            if kvrows:
                t = {"origin": "pdf_info", "zone": "INFO", "category": "table", "subcategory": "KV", "table_no": "",
                     "title": f"資訊區({where})", "anchor": anchor, "bbox": bb, "columns": ["項目", "內容"], "rows": kvrows,
                     "verdict": "GREEN", "checks": [f"鍵值 {sum(1 for r in kvrows if r[0])} · 其他 {sum(1 for r in kvrows if not r[0])}"],
                     "issues": [], "source": "", "notes": []}
                out["info"].append(t)
            continue
        # 本文:標題行自成一列;其餘行合段 → 一句一列
        para = []

        def flush():
            if not para:
                return
            ptxt, poffs, p = "", [], 0
            for _i, ln in para:
                sep = "" if (ptxt and re.search(f"[{CJK}]$", ptxt) and re.match(f"[{CJK}]", ln["text"].lstrip())) else (" " if ptxt else "")
                ptxt += sep
                poffs.append((len(ptxt), len(ptxt) + len(ln["text"]), ln))
                ptxt += ln["text"]
            for a, b, x in sentences(ptxt):
                cov = [ln for (s0, s1, ln) in poffs if s0 < b and s1 > a]
                sz = _wmedian([(ln["size"], ln["nch"]) for ln in cov])
                bold = sum(ln["nch"] for ln in cov if ln["bold"]) * 2 >= sum(ln["nch"] for ln in cov)
                bx = (min(ln["bbox"][0] for ln in cov), min(ln["bbox"][1] for ln in cov),
                      max(ln["bbox"][2] for ln in cov), max(ln["bbox"][3] for ln in cov))
                li = lns.index(cov[0]) + 1
                out["body"].append({"anchor": f"{anchor}·L{li}", "bbox": bx, "category": "text",
                                    "subcategory": "SMALL" if sz < body_size * F["small"] else "BODY",
                                    "size": sz, "bold": bold, "text": x})
            para.clear()
        for i, ln in rest:
            sc = _subcat(ln["size"], ln["bold"], body_size, ln["nch"], ln["text"])
            if sc in ("H1", "H2", "H3"):
                flush()
                out["body"].append({"anchor": f"{anchor}·L{i + 1}", "bbox": ln["bbox"], "category": "text", "subcategory": sc,
                                    "size": ln["size"], "bold": ln["bold"], "text": tidy(ln["text"])})
            else:
                para.append((i, ln))
        flush()
    if appx_pending:
        state["appendix"] = True
    return out


def _pages_sel(spec: str, n: int) -> list:
    spec = (spec or "1").strip().lower()
    if spec == "all":
        return list(range(1, n + 1))
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", spec)
    if not m:
        return [1]
    a = int(m.group(1))
    b = int(m.group(2) or a)
    return [p for p in range(a, b + 1) if 1 <= p <= n]


def restore_pdf(path: Path, pages: str = "1") -> dict:
    import fitz
    state = {"eng392": _eng392(), "notes": []}
    res = {"name": Path(path).name, "mode": "pdf", "pages": []}
    with fitz.open(str(path)) as doc:
        sel = _pages_sel(pages, doc.page_count)
        allp = [(ln["size"], ln["nch"]) for pno in (sel if len(sel) > 1 else range(1, min(doc.page_count, 3) + 1))
                for ln in _page_lines(doc[pno - 1]) if len(VAL_RX.findall(ln["text"])) < 2]
        state["doc_body"] = _wmedian(allp) or None           # 整份文件的本文字級(圖表頁本文太少時用)
        for pno in sel:
            res["pages"].append(page_layout(doc[pno - 1], pno, state))
    if state["eng392"] is None:
        state["notes"].append("ENG392 不在 → 不做 XY 切(整頁一區)")
    res["notes"] = state["notes"]
    lamps = [t["verdict"] for p in res["pages"] for t in p["info"]]
    res["verdict"] = _worst(lamps) if lamps else "GREEN"
    return res


# ---------------------------------------------------------------- output

def _table_md(t: dict, n: int) -> str:
    head = f"### 表 {n}"
    if t.get("table_no"):
        head += f" · {t['table_no']}"
    if t.get("title"):
        head += f" · {tidy(t['title'])}"
    where = " · ".join(x for x in (t.get("anchor") or "", ("自" + t["moved_from"] + "移入") if t.get("moved_from") else "",
                                    t.get("subcategory") or "") if x)
    lines = [head + f"  〔{t.get('verdict', '')}{(' · ' + where) if where else ''}〕", "", md_table(t["columns"], t["rows"])]
    if t.get("source"):
        lines.append(f"\n資料來源:{tidy(t['source'])}")
    for x in t.get("notes") or []:
        lines.append(f"\n表註:{x}")
    for x in (t.get("checks") or []) + (t.get("identities") or []):
        lines.append(f"- 驗:{x}")
    for x in t.get("issues") or []:
        lines.append(f"- 注意:{x}")
    return "\n".join(lines)


def _fig_md(f: dict, n: int) -> str:
    head = f"### 圖 {n}" + (f" · {f['table_no']}" if f.get("table_no") else "") + (f" · {tidy(f['title'])}" if f.get("title") else "")
    rows = [["判定", f.get("verdict", "FIGURE")], ["說明", f.get("note", "")]]
    ax = f.get("axis")
    if ax:
        rows += [["座標軸刻度", f"{ax['count']} 個 · {ax['kind']} · 步距 {ax['step']}" + (f" · 單位 {ax['unit']}" if ax.get("unit") else "")],
                 ["資料標籤", " ".join(f.get("data_labels") or []) or "—"], ["X 軸", " ".join(f.get("x_labels") or []) or "—"],
                 ["圖例 / 註", f.get("legend") or "—"]]
    if f.get("source"):
        rows.append(["資料來源", f["source"]])
    if f.get("bbox"):
        rows.append(["據點", f"{f.get('anchor', '')} {list(f['bbox'])}"])
    return head + "\n\n" + md_table(["項目", "內容"], rows)


def _body_md(body: list) -> str:
    rows = [[i, b["anchor"], CAT_ZH[b["category"]], b["subcategory"], "" if b.get("size") is None else b["size"],
             "" if b.get("bold") is None else ("粗" if b["bold"] else ""), b["text"]] for i, b in enumerate(body, 1)]
    return md_table(["#", "據點", "類別", "次類別", "字級", "粗", "內容"], rows)


def to_markdown(res: dict) -> str:
    out = [f"# 版面還原 · {res['name']}", "",
           f"總判 {res['verdict']} · 規則冊 {ssot().get('_path', '')} · 引擎 {ENGINE}", ""]
    pages = res["pages"] if res.get("mode") == "pdf" else [dict(res, page=1)]
    tn = fn = 0
    for p in pages:
        if res.get("mode") == "pdf":
            out += [f"## 第 {p['page']} 頁 · 本文字級 {p['body_size']}", "", "### 版面樹(先左右、再上下)", "",
                    md_table(["區路徑", "區", "位置 / 理由", "類別", "bbox", "字級"],
                             [[lf["path"], ZONE_ZH[lf["zone"]], lf.get("where", ""), CAT_ZH[lf["category"]], list(lf["bbox"]),
                               lf.get("size", "")] for lf in p["leaves"]]), ""]
        out += ["## 資訊區(上 / 左 / 右 / 下 · 一切表)", ""]
        for t in p["info"]:
            tn += 1
            out += [_table_md(t, tn), ""]
        if p["figures"]:
            out += ["## 圖", ""]
            for f in p["figures"]:
                fn += 1
                out += [_fig_md(f, fn), ""]
        out += ["## 本文區(一句一列 · 有據點)", "", _body_md(p["body"]) if p["body"] else "(無)", ""]
        if p["excluded"]:
            out += ["## 排除區(不擷取:小字頁尾 / 免責 / 附錄及其標題)", ""]
            if res.get("mode") == "pdf":
                out.append(md_table(["據點", "理由", "字級", "行", "開頭"],
                                    [[e["anchor"], e["reason"], e["size"], e["lines"], e["head"]] for e in p["excluded"]]))
            else:
                out.append(md_table(["據點", "理由", "開頭"], [[e["anchor"], "免責 / 聲明", e["text"][:40]] for e in p["excluded"]]))
            out.append("")
    for n in res.get("notes") or []:
        out.append(f"- 註:{n}")
    return "\n".join(out).rstrip() + "\n"


def _kit():
    hits = sorted(REG.glob("CGC_MDL241_TemplateAdapter_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("mdl241_for_" + ENGINE, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    try:
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def page_html(docs: list) -> str:
    e = _html.escape
    kit = _kit()
    lamp = (kit.lamp if kit else (lambda s, t: f"<b>{e(t)}</b>"))

    def tbl(cols, rows):
        return ("<table class='via'><tr>" + "".join(f"<th>{e(tidy(c))}</th>" for c in cols) + "</tr>"
                + "".join("<tr>" + "".join(f"<td>{e(tidy(x))}</td>" for x in r) + "</tr>" for r in rows) + "</table>")
    summ = []
    parts = []
    for d in docs:
        pages = d["pages"] if d.get("mode") == "pdf" else [d]
        nt = sum(len(p["info"]) for p in pages)
        nf = sum(len(p["figures"]) for p in pages)
        nb = sum(len(p["body"]) for p in pages)
        nx = sum(len(p["excluded"]) for p in pages)
        summ.append([d["verdict"], d["name"], nt, nf, nb, nx])
        sec = [f"<h3>{e(d['name'])} · {lamp(d['verdict'], d['verdict'])}</h3>"]
        for p in pages:
            for t in p["info"]:
                sec.append(f"<div class='via-note'>{lamp(t.get('verdict', ''), t.get('verdict', ''))} {e(t.get('table_no') or '')} "
                           f"{e(tidy(t.get('title') or ''))} {e(t.get('anchor') or '')}</div>" + tbl(t["columns"], t["rows"])
                           + "".join(f"<div class='via-note'>{e(x)}</div>" for x in (t.get("identities") or []) + (t.get("issues") or [])))
            for f in p["figures"]:
                sec.append(f"<div class='via-note'>圖 {e(f.get('table_no') or '')} {e(tidy(f.get('title') or ''))} — {e(f.get('note', ''))}</div>")
            if p["body"]:
                sec.append(tbl(["據點", "次類別", "字級", "內容"], [[b["anchor"], b["subcategory"], b.get("size") or "", b["text"]]
                                                               for b in p["body"][:60]]))
        parts.append("".join(sec))
    body = ("<h3>紅黃綠矩陣 · 版面還原</h3>"
            + tbl(["燈", "文件", "表", "圖", "本文句", "排除"], summ) + "".join(parts)
            + "<div class='via-note'>表一律在資訊區;本文一句一列帶據點;圖只列刻度 / 標籤 / 圖例,不造表;排除區只記位置與理由。</div>")
    tally = Counter(d["verdict"] for d in docs)
    side = (f"<div class='via-card'>{lamp(_worst([d['verdict'] for d in docs]), '總判 ' + _worst([d['verdict'] for d in docs]))}</div>"
            f"<div class='via-note'>{len(docs)} 件 · " + " · ".join(f"{k} {v}" for k, v in sorted(tally.items())) + "</div>")
    if kit:
        return kit.page("VRN 版面還原", body, side, module={"id": "vrn-layout-restore", "name": "版面還原"})
    return f"<!doctype html><meta charset='utf-8'><title>VRN 版面還原</title>{side}{body}"


def write_outputs(docs: list, out: Path = OUT) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for d in docs:
        stem = Path(d["name"]).stem
        (out / f"{stem}.layout.md").write_text(to_markdown(d), encoding="utf-8")
        (out / f"{stem}.layout.json").write_text(json.dumps(d, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    slim = {"engine": ENGINE, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ssot": ssot().get("_path"),
            "verdict": _worst([d["verdict"] for d in docs]) if docs else "NODATA",
            "docs": [{"name": d["name"], "verdict": d["verdict"], "mode": d.get("mode"),
                      "tables": sum(len(p["info"]) for p in (d["pages"] if d.get("mode") == "pdf" else [d])),
                      "figures": sum(len(p["figures"]) for p in (d["pages"] if d.get("mode") == "pdf" else [d]))} for d in docs]}
    (out / "LAYOUT_latest.json").write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "LAYOUT_latest.html").write_text(page_html(docs), encoding="utf-8")


def collect(given: list) -> tuple:
    files, notes = [], []
    for g in given:
        p = Path(g)
        if p.is_dir():
            files += sorted(x for x in p.rglob("*.pdf"))
        elif p.is_file():
            files.append(p)
        else:
            notes.append(f"不在:{g}")
    if not given:
        e = _eng392()
        if e is not None:
            fs, ns = e.collect_inputs([], None)
            files += [f for f in fs if Path(f).suffix.lower() == ".pdf"]
            notes += ns
    return files, notes


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    given = [args[i + 1] for i, a in enumerate(args) if a in ("--in", "--dir") and i + 1 < len(args)]
    pages = args[args.index("--pages") + 1] if "--pages" in args and args.index("--pages") + 1 < len(args) else "1"
    docs = []
    if args[:1] == ["text"]:
        for g in given:
            r = text_restore(Path(g).read_text(encoding="utf-8", errors="replace"))
            r["name"] = Path(g).name
            docs.append(r)
        notes = []
    else:
        files, notes = collect(given)
        for f in files:
            try:
                docs.append(restore_pdf(f, pages))
            except Exception as ex:
                notes.append(f"{Path(f).name}:{ex.__class__.__name__}: {ex}")
    for n in notes:
        print(f"  [輸入] {n}")
    if not docs:
        print("[版面還原] 沒有輸入(--in <pdf|夾> 或樣本夾)")
        return 2
    write_outputs(docs)
    for d in docs:
        pages_ = d["pages"] if d.get("mode") == "pdf" else [d]
        print(f"  {d['verdict']:<6} {d['name']} · 表 {sum(len(p['info']) for p in pages_)} · 圖 {sum(len(p['figures']) for p in pages_)} · "
              f"本文句 {sum(len(p['body']) for p in pages_)} · 排除 {sum(len(p['excluded']) for p in pages_)}")
    v = _worst([d["verdict"] for d in docs])
    print(f"[版面還原] 總判 {v} · {len(docs)} 件 · 頁 {OUT / 'LAYOUT_latest.html'}")
    return 0 if v == "GREEN" else (1 if v == "RED" else 3)


# ---------------------------------------------------------------- selftest
# 夾具只留表格 / 圖的片段與數字(取自操作員 R36 貼上的 OCR 扁平文字);前後句是本支自寫的中性句,不存報告正文。

FX_INDEX = ("2025. 12 . 5 星期五目 錄頁 次一、總經重要訊息評論 .................................................................... 2"
            "二、市場重要訊息評論 .................................................................... 2三、產業重要訊息評論 "
            ".................................................................... 4國際股市收盤行情股市指數名稱收盤指數漲跌漲跌幅股市指數名稱收盤指數漲跌漲跌幅"
            "Dow Jones Index 47,850.94 -31.96 -0.1% NASDAQ 23,505.14 +51.05 +0.2% 上証綜合3,875.79 -2.21 -0.1% 美國S&P 500 6,857.12 +7.40 +0.1% "
            "香港恆生25,935.90 +175.17 +0.7% 亞洲費城半導體SOX 7,215.97 -64.54 -0.9% 日經255 51,028.42 +1163.74 +2.3% 英國金融時報9,710.87 +18.80 +0.2% "
            "韓國綜合4,028.51 -7.79 -0.2% 法國CAC 8,122.03 +34.61 +0.4% 歐洲新興德國DAX 23,882.03 +188.32 +0.8% 俄羅斯RTS 1,087.43 +15.86 +1.5% "
            "收盤指數最近更新日： 20251204印度BSE 85,265.32 +158.51 +0.2% 本刊內容僅供參考，投資人需自行考量風險，本公司恕不負擔任何法律責任。")
FX_CITI = ("Sales beat expectations on a smoother ramp. Earnings Summary Year to Net Profit Diluted EPS EPS growth P/E P/B ROE Yield "
           "31 Dec (NT$M) (NT$) (%) (x) (x) (%) (%) 2023A 11,472 4.09 1.9 27.9 3.2 11.4 2.1 2024A 17,446 6.12 49.8 18.6 2.5 14.7 3.3 "
           "2025E 24,878 8.72 42.4 13.1 2.0 16.8 4.5 2026E 29,415 10.31 18.2 11.1 1.7 16.6 5.4 2027E 34,081 11.94 15.9 9.5 1.5 16.4 6.2 "
           "Source: Powered by dataCentral See Appendix A-1 for Analyst Certification. Investors should be aware of a conflict of interest.")
FX_MITAC = ("Margins should improve next year. Exhibit 1: Mitac revenues by product 350,000 NT m 35% 300,000 28% 250,000 16% 200,000 "
            "150,000 2% 100,000 1% 50,000 - 2024 2025E 2026E 2027E 2028E General server AI server - high power AI server - inferencing "
            "AI server - rack-level Storage Switch Auto electronics Others The % in chart is AI servers revenues contribution "
            "Source: Company data, Goldman Sachs Global Investment Research We maintain our view.")
FX_HONHAI = ("Revenue trends stay firm. Exhibit 1: Hon Hai’s Nov revenues +26% YoY, or -6% MoM 120% 100% 80% 60% 40% 20% 0% -20% -40% "
             "Jul-14 Jul-21 Jan-11 Aug-11 Mar-12 Oct-12 May-13 Dec-13 Feb-15 Sep-15 Apr-16 Nov-16 Jun-17 Jan-18 Aug-18 Mar-19 Oct-19 "
             "May-20 Dec-20 Feb-22 Sep-22 Nov-23 Jun-24 Jan-25 Aug-25 Apr-23 Source: Company data We expect growth ahead.")


def make_pdf(path: Path) -> Path:
    """合成首頁:H1 標題 · 本文兩段 · 右側資訊欄(鍵值)· 畫線表(表頭合併格)與並排第二張表 · 本文裡的扁平表 · 頁底小字免責。"""
    import fitz
    doc = fitz.open()
    pg = doc.new_page(width=595, height=842)
    ins = lambda x, y, t, s=10, f="china-t": pg.insert_text((x, y), t, fontname=f, fontsize=s)  # noqa: E731
    ins(40, 60, "Wistron Strong Sales Ramp", 20, "hebo")
    ins(40, 92, "Key Points", 12.5, "hebo")
    body = ["本季營收優於預期，主因伺服器出貨放量，", "且新客戶專案陸續導入。管理層維持全年成長", "看法。客戶拓展持續進行中。",
            "We expect margins to improve next year as the new", "platform ramps. The ramp seems on track and the",
            "order visibility extends into the second half."]
    for i, t in enumerate(body):
        ins(40, 112 + i * 14, t, 10, "china-t" if re.search(f"[{CJK}]", t) else "helv")
    ins(40, 215, "Earnings Summary", 11, "hebo")
    flat = ["Year to Net Profit Diluted EPS P/E", "31 Dec (NT$M) (NT$) (x)", "2023A 11,472 4.09 27.9", "2024A 17,446 6.12 18.6",
            "2025E 24,878 8.72 13.1", "Source: Powered by dataCentral"]
    for i, t in enumerate(flat):
        ins(40, 232 + i * 13, t, 9, "helv")
    tail = ["風險包括零組件供應與匯率波動，需持續追蹤。", "We keep our estimates unchanged for now."]
    for i, t in enumerate(tail):
        ins(40, 470 + i * 14, t, 10, "china-t" if re.search(f"[{CJK}]", t) else "helv")
    for i, t in enumerate(["評等：買進", "目標價：150", "收盤價：114", "產業：電子代工", "市值：NT$326bn"]):
        ins(450, 112 + i * 16, t, 8.5)

    def grid(x0, y0, cw, rh, cells, open_top=()):
        nr, nc = len(cells), len(cells[0])
        for r in range(nr + 1):
            pg.draw_line((x0, y0 + r * rh), (x0 + cw * nc, y0 + r * rh))
        for c in range(nc + 1):
            pg.draw_line((x0 + c * cw, y0 + (rh if c in open_top else 0)), (x0 + c * cw, y0 + nr * rh))
        for r, row in enumerate(cells):
            for c, t in enumerate(row):
                if t:
                    pg.insert_text((x0 + c * cw + 3, y0 + r * rh + 12), t, fontname="china-t", fontsize=9)
    grid(40, 345, 60, 18, [["年度", "營收", None], ["", "Q1", "Q2"], ["2024", "1,200", "1,350"], ["2025", "1,500", "1,640"]], open_top={2})
    grid(260, 345, 60, 18, [["項目", "數值"], ["EPS", "4.09"], ["P/E", "27.9"]])
    ins(40, 800, "免責聲明：本報告僅供參考，投資人需自行判斷，本公司不負任何法律責任。", 6)
    ins(40, 810, "Analyst Certification and Important Disclosures appear in the Appendix.", 6, "helv")
    doc.save(str(path))
    doc.close()
    return path


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    R = ssot()
    chk("規則冊在 registry 且本支照冊讀", R.get("ssot") == "VIA_VRN_LayoutRestore_SSOT" and R.get("owner_engine") == "VRN_ENG394_LayoutRestore")
    chk("TRIM:CJK 字間空白去掉 · 英數詞間壓一格", tidy("  上 証  綜合  Dow   Jones ") == "上証綜合Dow Jones", tidy("  上 証  綜合  Dow   Jones "))
    chk("值 token:3231.TW / Jul-14 / 2025E / S&P 500 不算值", not VAL_RX.findall("(3231.TW) Jul-14 2025E S&P 500 G4826Z5"),
        VAL_RX.findall("(3231.TW) Jul-14 2025E S&P 500 G4826Z5"))
    # ---- 兆豐指數表
    r = text_restore(FX_INDEX)
    tabs = [t for t in r["info"] if t.get("subcategory") != "TOC"]
    toc = [t for t in r["info"] if t.get("subcategory") == "TOC"]
    t = tabs[0] if tabs else {}
    chk("兆豐:找出 1 張指數表 13 列 × 4 欄", len(tabs) == 1 and len(t.get("rows", [])) == 13 and len(t.get("columns", [])) == 4,
        (len(tabs), len(t.get("rows", [])), t.get("columns")))
    chk("兆豐:連寫表頭拆開 + 重複 2 次 = 並排 2 張", t.get("columns") == ["股市指數名稱", "收盤指數", "漲跌", "漲跌幅"] and t.get("side_by_side") == 2,
        (t.get("columns"), t.get("side_by_side")))
    chk("兆豐:說明 = 國際股市收盤行情(目錄點線項不混入)", t.get("title") == "國際股市收盤行情", t.get("title"))
    chk("兆豐:漲跌幅驗算 13/13 列成立", any("13/13" in x and "漲跌幅" in x for x in t.get("identities", [])), t.get("identities"))
    chk("兆豐:表註移出列名 · 印度BSE 列名乾淨", "收盤指數最近更新日：20251204" in t.get("notes", []) and t["rows"][-1][0] == "印度BSE",
        (t.get("notes"), t.get("rows", [[""]])[-1]))
    chk("兆豐:分組詞(美國/亞洲/歐洲/新興)移出列名 · 誠實標 GROUP_UNPLACED → YELLOW",
        [x[0] for x in t["rows"]][3] == "S&P 500" and t["rows"][10][0] == "德國DAX" and t.get("verdict") == "YELLOW"
        and any("GROUP_UNPLACED" in x for x in t.get("issues", [])), (t["rows"][3][0], t["rows"][10][0], t.get("verdict")))
    chk("兆豐:目錄 3 項 → 目錄表(章節 | 頁次)", toc and len(toc[0]["rows"]) == 3 and toc[0]["rows"][0] == ["一、總經重要訊息評論", "2"],
        toc[0]["rows"] if toc else None)
    chk("兆豐:免責句進排除區 · 不進本文", r["excluded"] and all("法律責任" not in b["text"] for b in r["body"]))
    # ---- Citi
    r = text_restore(FX_CITI)
    t = r["info"][0] if r["info"] else {}
    chk("Citi:1 張 5 列 × 8 欄", len(r["info"]) == 1 and len(t.get("rows", [])) == 5 and len(t.get("columns", [])) == 8,
        (len(r["info"]), t.get("columns")))
    chk("Citi:說明 Earnings Summary · 首欄 Year to 31 Dec · 單位掛欄", t.get("title") == "Earnings Summary" and t["columns"][0] == "Year to 31 Dec"
        and t["columns"][1] == "Net Profit(NT$M)" and t["columns"][4] == "P/E(x)", t.get("columns"))
    chk("Citi:資料來源 = Source: Powered by dataCentral", t.get("source") == "Source: Powered by dataCentral", t.get("source"))
    chk("Citi:列名 = 年度鍵", [x[0] for x in t.get("rows", [])] == ["2023A", "2024A", "2025E", "2026E", "2027E"])
    chk("Citi:EPS 成長率驗算成立", any("EPS growth" in x and "本期" in x for x in t.get("identities", [])), t.get("identities"))
    chk("Citi:隱含常數 P/E × EPS ≈ 114(報告現價)", any("P/E" in x and "Diluted EPS" in x and "≈ 114" in x for x in t.get("identities", [])),
        t.get("identities"))
    chk("Citi:淨利 ÷ EPS ≈ 股數(隱含常數)", any("Net Profit" in x and "÷" in x for x in t.get("identities", [])), t.get("identities"))
    chk("Citi:GREEN", t.get("verdict") == "GREEN", (t.get("verdict"), t.get("issues")))
    chk("Citi:分析師聲明 / 利益衝突句進排除區", len(r["excluded"]) >= 2 and len(r["body"]) == 1, (len(r["excluded"]), len(r["body"])))
    # ---- 圖不是表
    for nm, fx, kind, cnt in (("Mitac", FX_MITAC, "num", 8), ("Hon Hai", FX_HONHAI, "pct", 9)):
        r = text_restore(fx)
        f = r["figures"][0] if r["figures"] else {}
        chk(f"{nm}:判圖 FIGURE · 不造表(0 表)", not r["info"] and f.get("verdict") == "FIGURE", (len(r["info"]), len(r["figures"])))
        chk(f"{nm}:座標軸等差 {cnt} 刻度({kind})· X 軸標籤 · 資料來源",
            (f.get("axis") or {}).get("count") == cnt and (f.get("axis") or {}).get("kind") == kind and f.get("x_labels")
            and f.get("source", "").startswith("Source: Company data"), (f.get("axis"), f.get("x_labels", [])[:3], f.get("source")))
    r = text_restore(FX_MITAC)
    f = r["figures"][0]
    chk("Mitac:資料標籤 35% 28% 16% 2% 1% 分出(不是刻度)· 單位 NT m", f["data_labels"] == ["35%", "28%", "16%", "2%", "1%"]
        and f["axis"]["unit"] == "NT m", (f["data_labels"], f["axis"]["unit"]))
    chk("Hon Hai:標題保留 +26% / -6%(不當刻度)", "+26%" in r["figures"][0]["title"] or "+26%" in text_restore(FX_HONHAI)["figures"][0]["title"])
    # ---- 驗算抓錯
    bad = FX_INDEX.replace("+1163.74 +2.3%", "+1163.74 +9.3%")
    t = [x for x in text_restore(bad)["info"] if x.get("subcategory") != "TOC"][0]
    chk("驗算抓錯:改一格漲跌幅 → 列 7 標疑 OCR 誤值", any("[7]" in x for x in t["issues"]), t["issues"])
    t = text_tables("A 1.0 2.0 3.0 B 4.0 5.0 6.0 C 7.0 8.0 D 1.0 2.0 3.0")
    chk("形狀不一致(某列少一值)→ RED", t and t[0]["verdict"] == "RED", t[0]["verdict"] if t else None)
    # ---- 合併格 · 上下拆 · 左右拆
    parts = fix_table([["年度", "營收", None], ["", "Q1", "Q2"], ["2024", "1,200", "1,350"], [None, "1,300", "1,400"]])
    chk("合併格:表頭 None 向右延 → 營收/Q1 · 營收/Q2;首欄 None 向下延", parts and parts[0]["columns"] == ["年度", "營收/Q1", "營收/Q2"]
        and parts[0]["rows"][1][0] == "2024", parts[0] if parts else None)
    parts = fix_table([["項目", "數值"], ["EPS", "4.09"], ["", ""], ["項目", "數值"], ["P/E", "27.9"]])
    chk("堆疊表:整列全空 → 上下拆 2 張", len(parts) == 2, len(parts))
    parts = fix_table([["項目", "數值"], ["EPS", "4.09"], ["P/E", "27.9"], ["指標", "比率"], ["ROE", "11.4"]])
    chk("堆疊表:數字列後出現新表頭 → 上下拆 2 張", len(parts) == 2, len(parts))
    parts = fix_table([["項目", "數值", "", "指標", "比率"], ["EPS", "4.09", "", "ROE", "11.4"]])
    chk("並排表:整欄全空 → 左右拆 2 張", len(parts) == 2 and parts[1]["columns"] == ["指標", "比率"], parts)
    # ---- PDF 版面
    try:
        import fitz  # noqa: F401
        has_fitz = True
    except Exception:
        has_fitz = False
    if has_fitz:
        with tempfile.TemporaryDirectory() as td:
            pdf = make_pdf(Path(td) / "synthetic_firstpage.pdf")
            res = restore_pdf(pdf, "1")
            p = res["pages"][0]
            zones = Counter(lf["zone"] for lf in p["leaves"])
            chk("PDF:葉區四類都在(資訊 / 本文 / 排除;表在資訊區)", zones["INFO"] >= 3 and zones["BODY"] >= 1 and zones["EXCLUDED"] >= 1, dict(zones))
            chk("PDF:右側欄 → 資訊區(右)· 鍵值表 評等=買進", any(t.get("subcategory") == "KV" and ["評等", "買進"] in t["rows"] for t in p["info"]),
                [t.get("title") for t in p["info"]])
            grids = [t for t in p["info"] if t["origin"] == "pdf_grid"]
            chk("PDF:畫線表 2 張(並排)· 合併格補值 營收/Q1", len(grids) == 2 and any(t["columns"] == ["年度", "營收/Q1", "營收/Q2"] for t in grids),
                [t["columns"] for t in grids])
            flat = [t for t in p["info"] if t["origin"] == "pdf_text"]
            chk("PDF:本文裡的扁平表抽到資訊區(單位掛欄 · 資料來源)", flat and flat[0]["columns"][1] == "Net Profit(NT$M)"
                and flat[0]["source"].startswith("Source:") and flat[0].get("moved_from") == "本文區", [t["columns"] for t in flat])
            subs = Counter(b["subcategory"] for b in p["body"])
            chk("PDF:本文一句一列 · H1 標題 · H2/H3 小標 · 本文句 ≥5", subs["H1"] == 1 and (subs["H2"] + subs["H3"]) >= 1 and subs["BODY"] >= 5, dict(subs))
            chk("PDF:本文句帶據點(p1·區路徑·L行)與字級", all(re.match(r"p1·\w+·L\d+", b["anchor"]) and b["size"] for b in p["body"]),
                [b["anchor"] for b in p["body"]][:3])
            chk("PDF:扁平表的列不進本文", not any("11,472" in b["text"] for b in p["body"]))
            chk("PDF:頁底小字免責 + 其英文聲明 → 排除區(不擷取)", len(p["excluded"]) >= 1 and not any("法律責任" in b["text"] for b in p["body"])
                and not any("Analyst Certification" in b["text"] for b in p["body"]), p["excluded"])
            md = to_markdown(res)
            chk("輸出:所有表用垂直線 · 本文架構表 · 排除區表", "| 年度 | 營收/Q1 | 營收/Q2 |" in md and "| # | 據點 | 類別 | 次類別 | 字級 | 粗 | 內容 |" in md
                and "## 排除區" in md)
            outd = Path(td) / "out"
            write_outputs([res, dict(text_restore(FX_CITI), name="citi.txt")], outd)
            chk("輸出:.layout.md / .layout.json / LAYOUT_latest.json / .html", all((outd / n).exists() for n in
                ("synthetic_firstpage.layout.md", "synthetic_firstpage.layout.json", "LAYOUT_latest.json", "LAYOUT_latest.html", "citi.layout.md")))
        real = VIA / "supportive modules" / "specs" / "EarningsInsight_062626.pdf"      # 倉內真實報告(31 頁)當回歸樣本
        if real.exists():
            res = restore_pdf(real, "all")
            pg = {p["page"]: p for p in res["pages"]}
            p4 = [t for t in pg[4]["info"] if t["origin"] == "pdf_text"]
            chk("真實 PDF p4:兩張堆疊扁平表 Top 10 / Bottom 10 各 10 列 · 表頭 5 欄 · 來源從說明裡取出",
                len(p4) == 2 and all(len(t["rows"]) == 10 and t["columns"][0] == "Company" and t["source"] == "Source: FactSet" for t in p4),
                [(len(t["rows"]), t["columns"], t["source"]) for t in p4])
            chk("真實 PDF p4:Target − Closing = Diff ($) 與 Diff (%) 驗算 10/10 · GREEN",
                all(any("Target − Closing = Diff ($):10/10" in x for x in t["identities"]) and t["verdict"] == "GREEN" for t in p4),
                [t["identities"] for t in p4])
            chk("真實 PDF p2:分行目錄(標題 / 頁碼)→ 目錄表", any(t.get("subcategory") == "TOC" and len(t["rows"]) >= 8 for t in pg[2]["info"]))
            chk("真實 PDF p31:Important Notice 標題連內容排除 · 本文只剩頁眉", any("Important Notice" in e["reason"] for e in pg[31]["excluded"])
                and [b["text"] for b in pg[31]["body"]] == ["EARNINGS INSIGHT"], [b["text"][:20] for b in pg[31]["body"]])
            chk("真實 PDF:每頁小字頁尾(版權 / 頁碼)都進排除區", all(any("頁尾" in e["reason"] or "附錄" in e["reason"] for e in p["excluded"])
                                                     for p in res["pages"]))
        else:
            print("  [—] 倉內真實樣本 EarningsInsight_062626.pdf 不在 → 真實回歸略過(誠實記缺件)")
    else:
        chk("PDF:PyMuPDF 不在 → 版面測試跳過(誠實記缺件,不算過)", False)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 閘 · 不匯入 TA-Lib · 不碰網路", "[VIA:ACCEL-BRIDGE" in body and 'os.environ.get("VIA_FROM_VCGC") != "YES"' in body
        and not re.search(r"^\s*(import|from)\s+(" + "ta" + r"lib|requests|urllib)\b", body, re.M))
    print(f"[VRN_ENG394 v0100 版面還原] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())


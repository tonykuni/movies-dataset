#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG397_P1Segment v0113 — 第一頁 + 財報頁切割擷取(v0113 擷取後修復層(對照 repo 既有工具 ENG392 / ENG398 / ENG085 · 補它們沒有的):① 數字被字距拆開接回(1 20,843 → 120,843 · 1 ,154 → 1,154 · 8 .0 → 8.0 · ( 457) → (457))② 英文字母被拉開接回(E li t e M a t e r i a l → Elite Material · 債券 E T F → 債券 ETF)③ 字型對錯中文字錯字表(漲輻 → 漲幅 · 中國僖託 → 中國信託 · 團泰期賃 → 國泰期貨)④ 欄位整齊的表格(數字列格數 ≈ 期間欄數)不再判「沒對到期間欄」· 原文留 JSON raw · 每區記 repairs)(v0112 第 20 輪實證修兩項:常用字判定加 Big5 常用字(A440–C67E)與 GB2312 一級字 · 繁體短文字(封裝 / 測試 / 台灣 / 人名)不再誤送 OCR · 首頁沒有文字層(影像 PDF)→ 整頁切 PNG 進 OCR 排隊並亮紅「首頁無文字層 → OCR 排隊」)(v0111 第 12 輪 97 份實證修五項:並排兩表(資產負債表｜現金流量表)同列兩段相同期間序列 → 以第二段起點切左右各自對齊 · 黏在一起的期間表頭格(25Q3(F) 25Q4(F) 2025(F))逐 token 拆欄 · 圖的座標軸刻度(沒科目欄 · ≥70% 列只有數字)不算財報表歸 FG · 短亂碼(` 夾在中文裡 · 擴充 A 區字)判錯碼換引擎 · 底部含 ≥2 個數字的列不算頁尾(表格不被切碎))(v0110 第 10 輪實證:行首私用區字元(Wingdings 項目符號)不算錯碼 · 表頭承接(沒自己期間表頭的表 → 用同一半上方最近的期間表頭對齊))(v0109 第 7 輪退步實證修正:圖說 / 座標軸文字(Figure · Chart · 圖 N · Source)不算財報表 · 期間表頭補 月-年(Dec-24)+ 輔助欄(YoY · QoQ · % chg · 年增)· 亂碼評估逐行(項目符號行首規則才生效)· 英文字間留空格)(v0108 契約自動寫出 contract/VRN_P1VIEW_RECORDS_CONTRACT_latest.json + .md · OCR 排隊改持久位置 VIA_Reports/vrn/p1view/ocr_queue(同一輸入不清 · 直到轉綠)· TEMP 排隊夾放 .via_keep)(v0107 第 2 輪退步修正:表名切出的區塊沒自己的期間表頭 → 是上一張表的分節 · 併回;行首 (cid:N) = 項目符號不算錯碼;新輸出 P1VIEW_records_latest.csv 扁平擷取列(檔 / 頁 / 區 / 大小類 / 框 / 列欄 / 文字)+ P1VIEW_latest.md(≤300 行 · AI 直接讀)(v0106 依真實 HTML 圖修四項:排除旋轉文字(直排浮水印不當側欄)· 整頁背景圖(>40%)忽略不擋字 · 頁首頁尾先依 x 空隙分欄再分塊(標題與評等不混)· 財報表名錨點認長表名 + 補 P&L / Ratios / Valuation 等 · 左右空隙 6pt + 右欄起頭 70% 科目)(v0105 依 97 份真實原因統計修三項:財報頁偵測放寬(關鍵字 + 數字 18% + 期間表頭列 ≥2 就算)· 期間表頭補民國年 / 兩位數年 / FY / 半年 / 季 / 月年 · 評等目標價關鍵字擴充;表格內空白行不切表(延續合併))(v0104 燈號依擷取品質:紅 = 錯碼送 OCR · 黃 = 列出原因(沒財報頁 / 財報頁沒切出表 / 財報表沒對到期間欄 / 首頁沒抓到評等目標價)· 綠 = 都沒有 · 版型改成資訊欄(側欄左 / 右 · 頁首資訊型 · 單欄型)不決定燈號 · HTML 上方原因統計)(v0103 真實 97 份回饋:綠 21→18 倒退修正 · 找側欄空隙只看中段主體(底部正常字級的全幅行不再填掉空隙)· 跨分界線的字另成全幅區 · 一字不漏)(v0102 整合優化:吸收 VRN_Unified_Repair 表頭期間欄 x 對齊(缺格留空不位移)· Grok 切割器 表名錨點切左右 / 上下 + 頁尾 = 底部且小字(本文不誤切)· 仍只用 pdfplumber 幾何 + pypdfium2 解碼)(v0101 操作員:Word / TXT 暫不處理 · 只做 PDF · 第一頁資訊區的圖 / 文再切開 · 財報頁先左右對切 · 每半再依上下不同表切 · 只用 pdfplumber 版面幾何 + pypdfium2 解碼 · 不疊複雜工具)(操作員 2026-10-11:先切割再擷取 · 本文 / 上左右下資訊區分開 · 資訊區依類別再細切 · 頁區序號 + 大類小類 ·
   文表圖不混 · 不亂碼 · 斷句銜接不接標題 · 句號一句一筆 · 標題一行一筆 · 表格儲存格 TRIM · HTML U/I 看效果 · 先第一頁 · NON-OCR pdfplumber 為主 · 不能用馬上換)。
  PDF → pdfplumber(字詞 / 表格 / 圖)切區:頁首 T · 頁尾 B · 左 L / 右 R 資訊欄(依 x 方向最大空隙)· 本文 M(再分段落 / 表格 / 圖)· 資訊區依關鍵字細分小類
  擷取:每區用 pdfplumber 裁切擷取 · 亂碼(私用區 / 替代字元)超過門檻 → 換 pymupdf · NFKC 只套全形英數 / 相容漢字 · 中文字間去空格
  Word / TXT / 圖片 → 首頁 + 財報頁轉 OCR 好讀的 PNG 到 TEMP 排隊(Word / TXT 同時直接擷取文字)
  [VIA:AST-CLASS] 類別 = 引擎(第一頁切割擷取)· 入口 = VRN_SystemManager p1view 動詞
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

import html
import json
import os
import re
from collections import Counter
import sys
import tempfile
import time
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_ID, ENGINE_NAME = "VRN_ENG397", "P1Segment(第一頁切割擷取檢視)"
EXT = {".pdf": "PDF", ".docx": "WORD", ".doc": "WORD(舊)", ".txt": "TXT", ".png": "IMG", ".jpg": "IMG", ".jpeg": "IMG", ".tif": "IMG", ".tiff": "IMG", ".bmp": "IMG"}
MAJOR = {"T": "頁首", "B": "頁尾", "L": "左資訊區", "R": "右資訊區", "M": "本文", "F": "財報全幅", "FL": "財報左半", "FR": "財報右半"}
_NUM = re.compile(r"^[\(\-−–]?[\d,]+(?:\.\d+)?%?\)?[xX倍]?$")
_STMT = re.compile(r"^(?:合併)?(?:綜合)?(?:損益表|資產負債表|現金流量表|財務預測|主要財務數據|財務比率|每股數據|評價|Income Statement|Balance Sheet|Cash ?Flows?(?: Statement)?|Key Financials|Financial Summary|Profit (?:and|&) Loss|P&L|Ratio Analysis|Key Ratios|Ratios|Valuation|Per[- ]share data|Key metrics)", re.I)
_HDR_AUX = re.compile(r"^(?:YoY|QoQ|HoH|MoM|%\s?chg\.?|chg\.?|Δ|年增|季增|月增|增減|成長|growth|%|\(%\)|change)$", re.I)
_FIGCAP = re.compile(r"^\s*(?:Figure|Fig\.?|Chart|Exhibit|Graph|Source|Sources|資料來源|圖表?\s?\d|圖)", re.I)
_PERIOD = re.compile(r"^\d{2}Q[1-4](?:\([AEFP]\))?$|^(?:19|20)\d{2}\([AEFP]\)$|^[1-4]Q\d{2}\([AEFP]\)$|^(?:FY)?(?:19|20)\d{2}(?:年度?)?[AEFP]?$|^FY\d{2}[AEFP]?$|^\d{2}[AEFP]$|^\d{3}[AEFP]$|^\d{2,3}年[AEFP]?$|^[1-4]Q\d{2}[AEFP]?$|^Q[1-4]\s?\d{2}$|^[12]H\d{2}[AEFP]?$|^(?:19|20)\d{2}[/.\-]\d{1,2}$|^\d{1,2}[/.\-](?:19|20)\d{2}$|^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[-/ ]?\d{2,4}[AEFP]?$|^\d{2,4}[-/ ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[AEFP]?$", re.I)
_FINPAGE = re.compile(r"損益表|資產負債表|現金流量表|財務預測|財務摘要|財務報表|財務資料|財務數據|財務預估|財務比率|主要財務|獲利能力|損益|資產負債|現金流|Income Statement|Balance Sheet|Cash ?Flow|Financial Summary|Key Financials|Financial Statements|Financials|P&L|Profit (?:and|&) Loss|Key Ratios|Ratios", re.I)
MINOR = [("RT", "評等 / 目標價", r"(?i)評等|rating|目標價|target\s*price|price\s*target|\bPT\b|\bTP\b|合理價|合理股價|投資建議|建議|買進|\bbuy\b|overweight|underweight|中立|neutral|持有|\bhold\b|outperform|underperform|增加持股|增持|加碼|減碼|區間操作|賣出|\bsell\b|accumulate|trading buy|\badd\b|\breduce\b"),
         ("AN", "分析師", r"(?i)@|tel\b|電話|analyst|分析師|研究員"),
         ("SD", "股價資料", r"(?i)股價|price|市值|market cap|52|成交|volume|股本|shares|流通|free float|外資|beta|收盤|close"),
         ("DS", "免責 / 揭露", r"(?i)免責|disclaimer|請參閱|important|僅供參考|版權|disclosure|certification"),
         ("DT", "日期 / 報告資訊", r"(?:19|20)\d{2}[/.\-年]\s?\d{1,2}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)")]
COLOR = {"T": (37, 99, 235), "B": (107, 114, 128), "L": (217, 119, 6), "R": (217, 119, 6), "M": (22, 163, 74), "F": (22, 163, 74), "FL": (217, 119, 6), "FR": (37, 99, 235),
         "TB": (220, 38, 38), "IMG": (124, 58, 237), "FG": (124, 58, 237)}
_END = re.compile(r"[。！？!?]$|(?<![A-Z])\.$")
_BULLET = re.compile(r"^\s*(?:[•●■◆▪‧\-–—]|\(?\d{1,2}[).、]|[一二三四五六七八九十]+、)")
_FIN = re.compile(r"(?i)損益表|資產負債表|現金流量表|財務預測|財務摘要|income statement|balance sheet|cash flow|financial summary|eps|營收|revenue")


COMMON = set("請參閱聲明頁之免責揭露其及與等並於的一是不了人我在有他這中大來上國個到說們為子和你地出道也時年得就那要下以生會自著去之過家學對可她裡後小麼心多天而能好都然沒日於起還發成事只作當想看文無開手十用主行方又如前所本見經頭面公同三已老從動兩長知民樣現分將外但身些與高意進把法此實回二理美點月明其種聲全工己話兒者向情部正名定女問力機給等幾很業最間新什打便位因重被走電四第門相次東政海口使教西再平真聽世氣信北少關並內加化由卻代軍產入先山五太水萬市眼體別處總才場師書比住員九笑性通目華報立馬命張活難神數件安表原車白應路期叫死常提感金何更反合放做系計或司利受光王果親界及今京務制解各任至清物臺特程品認持營收毛淨稅益資負債權股價標評買賣出持增減季度預估元億百仟千息配率盈虧損費用銷售額利潤現金流量投融籌備率週轉存貨帳款應付收入支出成本營業外非控制母子合併財報表重點展望需求擴大提升優於年增率市值分析研究員電話證券投顧評等目標中立買進賣出持有增加減少逢低強勁液冷健策晶片半導體電子科技伺服器光通訊散熱零組件材料設備廠客戶訂單產能出貨毛利率營益率淨利率每股盈餘殖利率本益比淨值比報酬權益資產負債總計流動非流動長期短期借款折舊攤銷資本支出自由現金流第一二三四季上下半年度預估實際月週日元角萬億兆台灣美國中國日本韓國歐洲亞洲全球集團公司股份有限")


def garbled(s: str) -> float:
    if not s:
        return 0.0
    s2 = re.sub(r"(?m)^\s*(?:\(cid:\d+\)|[\ue000-\uf8ff])\s*", "", s)   # v0107 / v0110:行首 (cid:N) 或私用區字元(Wingdings 項目符號)= 項目符號 · 不算錯碼
    cid = sum(len(m) for m in re.findall(r"\(cid:\d+\)", s2))
    bad = cid + sum(1 for c in s2 if c == "\ufffd" or 0xE000 <= ord(c) <= 0xF8FF or unicodedata.category(c) == "Co")
    bad += 3 * len(re.findall(r"[\u3400-\u4dbf]|\S*[\u3400-\u9fff]\S*[`´ˋ]\S*|\S*[`´ˋ]\S*[\u3400-\u9fff]\S*", s2))   # v0111:短亂碼(堢n,`U):擴充 A 區字 · ` 或 , 夾在中文裡 = 字型編碼錯
    return bad / len(s)


def _common2(c: str) -> bool:
    """v0112:Big5 常用字(首位元組 A4–C6)或 GB2312 一級字(B0–D7)= 常用。"""
    if c in COMMON:
        return True
    for enc, lo, hi in (("cp950", 0xA4, 0xC6), ("gb2312", 0xB0, 0xD7)):
        try:
            b = c.encode(enc)
        except (UnicodeEncodeError, LookupError):
            continue
        if len(b) == 2 and lo <= b[0] <= hi:
            return True
    return False


def quality(s: str, min_cjk: int = 2, wide: bool = False) -> tuple:
    """(分數, 常用字比例, 亂碼比例):合法但錯的字(字型編碼錯)用常用字比例判斷 · 中文 ≥min_cjk 字才判。"""
    cjk = [c for c in s if "\u3400" <= c <= "\u9fff"]
    ok = _common2 if wide else (lambda c: c in COMMON)                # v0112:wide 只用在「送不送 OCR」· 換引擎仍用嚴格常用字表(字型對錯的亂字也可能是常用字)
    ratio = (sum(1 for c in cjk if ok(c)) / len(cjk)) if len(cjk) >= min_cjk else 1.0
    g = garbled(s)
    return ratio - 5 * g, ratio, g


def clean(s: str) -> str:
    """不亂碼:去私用區 / 替代字元 · 全形英數 / 相容漢字 / 部首 → NFKC · 中文字間去空格 · TRIM。"""
    out = []
    for c in re.sub(r"\(cid:\d+\)", "", s or ""):
        o = ord(c)
        if c == "\ufffd" or 0xE000 <= o <= 0xF8FF:
            continue
        if 0xFF01 <= o <= 0xFF5E or 0xF900 <= o <= 0xFAFF or 0x2E80 <= o <= 0x2FDF:
            c = unicodedata.normalize("NFKC", c)
        out.append(c)
    t = re.sub(r"[ \t\u3000]+", " ", "".join(out))
    t = re.sub(r"(?<=[\u3400-\u9fff\u3000-\u303f\uff00-\uffef]) (?=[\u3400-\u9fff\u3000-\u303f\uff00-\uffef])", "", t)
    return t.strip()


def records(lines: list, body_size: float = 0.0, mode: str = "body") -> list:
    """本文:標題(字大 / 短且不含逗號頓號冒號 %)一行一筆 · 句子到句號一句一筆 · 不接到標題 · 項目符號開新筆。資訊區(mode=info):一行一筆(標籤:值 不串句)。"""
    if mode == "info":
        return [{"kind": "資訊", "text": t} for t in (clean(x) for x, _ in lines) if t]
    out, buf = [], ""
    sizes = [z for _, z in lines if z]
    body_size = body_size or (sorted(sizes)[len(sizes) // 2] if sizes else 0)

    def flush(final=False):
        nonlocal buf
        parts = re.split(r"(?<=[。！？!?])|(?<=[^A-Z]\.)\s+(?=[A-Z])", buf)
        keep = []
        for p in parts:
            p = clean(p)
            if p and (_END.search(p) or final):
                out.append({"kind": "句", "text": p})
            elif p:
                keep.append(p)
        buf = " ".join(keep) if not final else ""
    for i, (raw, size) in enumerate(lines):
        t = clean(raw)
        if not t:
            continue
        t2 = _BULLET.sub("", t).strip() or t                 # v0107:先去行首項目符號再判標題(「■ 投資重點」是標題)
        is_head = not _END.search(t2) and (bool(size and body_size and size >= body_size * 1.15)
                                           or (len(t2) <= 18 and i + 1 < len(lines) and not re.search(r"[，,、；;：:%]", t2) and (not buf or _BULLET.match(t))))
        if is_head:
            flush(final=True)
            out.append({"kind": "標題", "text": t2})
            continue
        if _BULLET.match(t) and buf:
            flush(final=True)
        sep = "" if (buf and re.search(r"[\u3400-\u9fff，、]$", buf) and re.match(r"[\u3400-\u9fff]", t)) else " "
        buf = (buf + sep + t).strip() if buf else t
        flush()
    flush(final=True)
    return out


def _lines(words: list) -> list:
    rows = []
    for w in sorted(words, key=lambda w: (round(w["top"] / 3), w["x0"])):
        if rows and abs(rows[-1]["top"] - w["top"]) <= 3:
            rows[-1]["ws"].append(w)
            rows[-1]["bottom"] = max(rows[-1]["bottom"], w["bottom"])
        else:
            rows.append({"top": w["top"], "bottom": w["bottom"], "ws": [w]})
    out = []
    for r in rows:
        ws = sorted(r["ws"], key=lambda w: w["x0"])
        txt = ""
        for a, b in zip([None] + ws[:-1], ws):
            cjk = a is not None and re.search(r"[\u3400-\u9fff]$", a["text"]) and re.match(r"[\u3400-\u9fff]", b["text"])
            txt += ("" if a is None else ("" if (cjk and b["x0"] - a["x1"] < 1.5) else " ")) + b["text"]   # v0109:英文字間一律留空格
        out.append({"text": txt, "size": max(float(w.get("size") or 0) for w in ws), "top": r["top"], "bottom": r["bottom"], "x0": ws[0]["x0"], "x1": max(w["x1"] for w in ws), "ws": ws})
    return out


def _blocks(lines: list, gap_k: float = 1.6) -> list:
    if not lines:
        return []
    hs = sorted(l["bottom"] - l["top"] for l in lines)
    lh = hs[len(hs) // 2] or 8
    blocks, cur = [], [lines[0]]
    for a, b in zip(lines, lines[1:]):
        if b["top"] - a["bottom"] > gap_k * lh:
            blocks.append(cur)
            cur = []
        cur.append(b)
    blocks.append(cur)
    return blocks


def _minor(text: str) -> tuple:
    for code, zh, rx in MINOR:
        if re.search(rx, text or ""):
            return code, zh
    return "TX", "文字"


def _inside(b, box, pad=1.0):
    return b[0] >= box[0] - pad and b[1] >= box[1] - pad and b[2] <= box[2] + pad and b[3] <= box[3] + pad


def _no_num_lines(ws: list) -> list:
    """v0111:底部候選字詞中 · 同一列(top 相近)有 ≥2 個數字的列不算頁尾 → 留給本文 / 表。"""
    byl = {}
    for w in ws:
        byl.setdefault(round(w["top"] / 3), []).append(w)
    keep = []
    for ls in byl.values():
        if sum(1 for w in ls if _NUM.match(w["text"])) < 2:
            keep.extend(ls)
    return keep


def _words(page) -> list:
    """字詞(v0106):排除非直立(旋轉 / 直排浮水印)的字 · 不參與切割。"""
    try:
        ws = page.extract_words(x_tolerance=1.5, y_tolerance=3, keep_blank_chars=False, extra_attrs=["size", "upright"])
    except Exception:  # noqa: BLE001
        ws = page.extract_words(x_tolerance=1.5, y_tolerance=3, keep_blank_chars=False, extra_attrs=["size"])
    return [w for w in ws if w.get("upright", True)]


def _xcols(words: list, gap: float = 24.0) -> list:
    """依 x 方向大空隙分欄(v0106 頁首 / 頁尾用):回傳每欄的字詞清單(由左到右)。"""
    segs = []
    for x0, x1 in sorted((w["x0"], w["x1"]) for w in words):
        if segs and x0 <= segs[-1][1] + gap:
            segs[-1][1] = max(segs[-1][1], x1)
        else:
            segs.append([x0, x1])
    return [[w for w in words if a <= w["x0"] <= b] for a, b in segs]


def _wb(w):
    return (w["x0"], w["top"], w["x1"], w["bottom"])


def _overlap(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    ar = max((a[2] - a[0]) * (a[3] - a[1]), 1e-6)
    return ix * iy / ar


def figures(page, words, exclude=()) -> list:
    """向量圖(線 / 矩形 / 曲線聚成一群)→ 圖框;排除整頁外框 · 排除與表格重疊 · 排除裡面幾乎全是數字的格線表。"""
    W, H = float(page.width), float(page.height)
    objs = [(float(o["x0"]), float(o["top"]), float(o["x1"]), float(o["bottom"])) for o in list(page.curves) + list(page.rects) + list(page.lines)]
    objs = [b for b in objs if (b[2] - b[0]) * (b[3] - b[1]) < 0.5 * W * H]
    cl = []
    for b in objs:
        hit = None
        for c in cl:
            if b[0] <= c["b"][2] + 4 and b[2] >= c["b"][0] - 4 and b[1] <= c["b"][3] + 4 and b[3] >= c["b"][1] - 4:
                hit = c
                break
        if hit:
            hit["b"] = (min(hit["b"][0], b[0]), min(hit["b"][1], b[1]), max(hit["b"][2], b[2]), max(hit["b"][3], b[3]))
            hit["n"] += 1
        else:
            cl.append({"b": b, "n": 1})
    out = []
    for c in cl:
        b = c["b"]
        if c["n"] < 3 or (b[2] - b[0]) * (b[3] - b[1]) < 0.01 * W * H or any(_overlap(b, e) > 0.5 or _overlap(e, b) > 0.5 for e in exclude):
            continue
        inner = [w["text"] for w in words if _inside(_wb(w), b, 1)]
        if len(inner) >= 10 and sum(1 for t in inner if _NUM.match(t)) / len(inner) >= 0.4:
            continue                                       # 格線表(裡面幾乎全是數字)不是圖
        out.append(b)
    return out


def segment(page, pno: int = 1) -> dict:
    """pdfplumber 頁物件 → 區塊清單(頁首 / 頁尾 / 左右資訊欄 / 本文 · 表格 / 圖 · 小類)。"""
    W, H = float(page.width), float(page.height)
    words = _words(page)
    tables = [t.bbox for t in page.find_tables()]
    images = [(float(i["x0"]), float(i["top"]), float(i["x1"]), float(i["bottom"])) for i in page.images if 0.01 * W * H < (i["x1"] - i["x0"]) * (i["bottom"] - i["top"]) < 0.4 * W * H]   # v0106:>40% 的是整頁背景圖 → 忽略
    sizes = sorted(float(w.get("size") or 0) for w in words) or [0]
    body_size = sizes[len(sizes) // 2]
    big = max(sizes)
    top_cut, bot_cut = 0.11 * H, 0.88 * H
    small = max(8.5, body_size * 0.85)
    foot = _no_num_lines([w for w in words if w["top"] >= bot_cut and float(w.get("size") or 0) <= small])   # 頁尾 = 底部且小字 · v0111:含 ≥2 個數字的列不算頁尾(表不切碎)
    title_ws = [w for w in words if float(w.get("size") or 0) >= max(body_size * 1.5, big * 0.9) and w["top"] < 0.35 * H]
    if title_ws:
        top_cut = max(top_cut, max(w["bottom"] for w in title_ws) + 2)
    mid = [w for w in words if w["top"] >= top_cut and not any(w is f for f in foot)]
    segs = []
    core = [w for w in mid if w["bottom"] <= bot_cut]          # 找空隙只看中段主體(v0103)
    for x0, x1 in sorted((w["x0"], w["x1"]) for w in core):
        if segs and x0 <= segs[-1][1] + 2:
            segs[-1][1] = max(segs[-1][1], x1)
        else:
            segs.append([x0, x1])
    split, side = None, None
    best = 0
    for a, b in zip(segs, segs[1:]):
        g = b[0] - a[1]
        left_w, right_w = a[1] - segs[0][0], segs[-1][1] - b[0]
        nl = sum(1 for w in core if w["x1"] <= a[1] + 1)
        nr = sum(1 for w in core if w["x0"] >= b[0] - 1)
        if g >= 6 and g > best and min(left_w, right_w) >= 0.06 * W and min(nl, nr) >= 3:
            best, split = g, (a[1] + b[0]) / 2
            side = "L" if left_w < right_w else "R"
    zones = []

    def add(major, bbox, kind, minor_code, minor_zh, ws=None, table=None):
        zones.append({"major": major, "bbox": [round(v, 1) for v in bbox], "kind": kind, "minor": minor_code, "minor_zh": minor_zh, "words": ws or [], "table": table})
    for major, ws in (("T", [w for w in words if w["bottom"] <= top_cut]), ("B", foot)):
        for col in _xcols(ws):                                  # v0106:先依 x 空隙分欄(標題與右側評等不混)
            for blk in _blocks(_lines(col)):
                txt = " ".join(l["text"] for l in blk)
                code, zh = ("TT", "標題") if major == "T" and any(l["size"] >= big * 0.9 for l in blk) else _minor(txt)
                add(major, (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", code, zh, [w for l in blk for w in l["ws"]])
    bot_m = max([w["bottom"] for w in mid] or [bot_cut]) + 1
    body_box = (split if side == "L" else 0, top_cut, split if side == "R" else W, bot_m) if split else (0, top_cut, W, bot_m)
    side_box = ((0, top_cut, split, bot_m) if side == "L" else (split, top_cut, W, bot_m)) if split else None
    for tb in tables:
        major = "M" if _inside(tb, body_box, 6) or not side_box else side
        add(major, tb, "表", "TB", "表格", table=tb)
    for im in images:
        add("M" if _inside(im, body_box, 6) or not side_box else side, im, "圖", "IMG", "圖")
    figs = figures(page, words, tables + images)
    for fb in figs:
        add("M" if _inside(fb, body_box, 6) or not side_box else side, fb, "圖", "FG", "圖表(向量)")
    blocked = tables + images + figs
    free = [w for w in mid if not any(_inside((w["x0"], w["top"], w["x1"], w["bottom"]), b, 1) for b in blocked)]
    if side_box:
        sw = [w for w in free if _inside((w["x0"], w["top"], w["x1"], w["bottom"]), side_box, 2)]
        for blk in _blocks(_lines(sw), 1.3):
            txt = " ".join(l["text"] for l in blk)
            code, zh = _minor(txt)
            add(side, (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", code, zh,
                [w for w in sw if blk[0]["top"] - 1 <= w["top"] <= blk[-1]["bottom"] + 1])
    bw = [w for w in free if _inside((w["x0"], w["top"], w["x1"], w["bottom"]), body_box, 2)]
    left = [w for w in free if w not in bw and not (side_box and _inside(_wb(w), side_box, 2))]
    for blk in _blocks(_lines(left), 2.2):                    # 跨分界線的字(全幅行)另成一區 · 一字不漏(v0103)
        add("M", (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", "TX", "本文(全幅)", [w for l in blk for w in l["ws"]])
    for blk in _blocks(_lines(bw), 2.2):
        add("M", (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", "TX", "本文段落",
            [w for w in bw if blk[0]["top"] - 1 <= w["top"] <= blk[-1]["bottom"] + 1])
    order = {"T": 0, "L": 1, "R": 2, "M": 3, "B": 4}
    zones.sort(key=lambda z: (order[z["major"]], z["bbox"][1], z["bbox"][0]))
    seq = Counter()
    for z in zones:
        seq[z["major"]] += 1
        z["id"] = "P%d·%s·%02d·%s" % (pno, z["major"], seq[z["major"]], z["minor"])
    return {"W": W, "H": H, "zones": zones, "split": split, "side": side, "body_size": body_size}


def fin_pages(pdf, pdoc, limit: int = 4) -> list:
    """財報頁:pypdfium2 文字(解碼準)含財報關鍵字 + pdfplumber 數字密度 ≥0.25(第一頁不算)。"""
    out = []
    for i in range(1, len(pdf.pages)):
        try:
            t = pdoc[i].get_textpage().get_text_range() if pdoc is not None else pdf.pages[i].extract_text() or ""
        except Exception:  # noqa: BLE001
            t = ""
        toks = re.findall(r"\S+", t)
        nr = (sum(1 for x in toks if _NUM.match(x)) / len(toks)) if toks else 0
        hdr = sum(1 for ln in t.splitlines() if (lambda ws: len(ws) >= 2 and sum(1 for x in ws if _PERIOD.match(x)) >= 2 and sum(1 for x in ws if _PERIOD.match(x) or _HDR_AUX.match(x)) / len(ws) >= 0.6)(ln.split()))
        if (_FINPAGE.search(t) and nr >= 0.18) or (hdr >= 2 and nr >= 0.12):      # v0105:關鍵字 + 數字 18% · 或 期間表頭列 ≥2
            out.append(i)
        if len(out) >= limit:
            break
    return out


def _decoded(l, tp, H) -> str:
    t = l["text"]
    if tp is not None and quality(t)[1] < 0.6:
        t = _pdfium(tp, (l["x0"] - 0.5, l["top"] - 0.5, l["x1"] + 0.5, l["bottom"] + 0.5), H) or t
    return clean(t)


def segment_fin(page, pno: int, tp=None) -> dict:
    """財報頁:頁首 / 頁尾 → 中段先左右對切(中線附近最大空隙 · 右半起頭是科目文字才算)→ 每半依上下空隙切不同表 · 向量圖另切。"""
    W, H = float(page.width), float(page.height)
    words = _words(page)
    top_cut, bot_cut = 0.07 * H, 0.90 * H
    sizes = sorted(float(w.get("size") or 0) for w in words) or [0]
    small = max(8.5, sizes[len(sizes) // 2] * 0.85)
    foot = _no_num_lines([w for w in words if w["top"] >= bot_cut and float(w.get("size") or 0) <= small])   # v0111 同上
    mid = [w for w in words if w["top"] >= top_cut and not any(w is f for f in foot)]
    def _stmt_lines(ws):                                            # v0109:先依 x 分欄再逐欄找表名(左右半同高度的行不再黏成一行)
        return [l for col in _xcols(ws, 20) for l in _lines(col) if (l["x1"] - l["x0"]) < 0.5 * W and _STMT.match(_decoded(l, tp, H))]
    stmts = _stmt_lines(mid)
    segs = []
    core = [w for w in mid if w["bottom"] <= bot_cut]          # 找空隙只看中段主體(v0103)
    for x0, x1 in sorted((w["x0"], w["x1"]) for w in core):
        if segs and x0 <= segs[-1][1] + 2:
            segs[-1][1] = max(segs[-1][1], x1)
        else:
            segs.append([x0, x1])
    split, best = None, 0
    for a, b in zip(segs, segs[1:]):
        g, c = b[0] - a[1], (a[1] + b[0]) / 2
        lead = [w["text"] for w in core if b[0] - 1 <= w["x0"] <= b[0] + 12]
        if g >= 6 and 0.3 * W <= c <= 0.7 * W and g > best and lead and sum(1 for t in lead if not _NUM.match(t)) / len(lead) >= 0.7:
            best, split = g, c
    lefts, rights = [l for l in stmts if l["x0"] < W / 2], [l for l in stmts if l["x0"] >= W / 2]
    if lefts and rights:                                   # 表名錨點(Grok 切割器):左右兩欄都有表名 → 切在右欄表名左緣
        split = min(l["x0"] for l in rights) - 3
    elif stmts and split and any(l["x0"] < split < l["x1"] for l in stmts):
        split = None                                       # 表名跨過空隙 = 全頁寬表 → 不從中線切裂
    halves = [("FL", (0, top_cut, split, H)), ("FR", (split, top_cut, W, H))] if split else [("F", (0, top_cut, W, H))]
    stmt_tops = {round(l["top"], 1) for l in stmts}             # 全頁(左右判斷用);每半另算自己的
    zones = []

    def add(major, bbox, kind, code, zh, ws=None):
        zones.append({"major": major, "bbox": [round(v, 1) for v in bbox], "kind": kind, "minor": code, "minor_zh": zh, "words": ws or [], "table": None})
    for major, ws in (("T", [w for w in words if w["bottom"] <= top_cut]), ("B", foot)):
        for col in _xcols(ws):
            for blk in _blocks(_lines(col)):
                add(major, (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", "TX", "文字", [w for l in blk for w in l["ws"]])
    figs = figures(page, words)
    for major, box in halves:
        for fb in figs:
            if _inside(fb, box, 6):
                add(major, fb, "圖", "FG", "圖表(向量)")
        hw = [w for w in mid if _inside(_wb(w), box, 2) and not any(_inside(_wb(w), fb, 1) for fb in figs)]
        figtops = {round(l["top"], 1) for col in _xcols(hw, 20) for l in _lines(col) if _FIGCAP.match(_decoded(l, tp, H))}
        stmt_tops = {round(l["top"], 1) for l in _stmt_lines(hw)} | figtops   # v0109:每半各自的表名位置 · 圖說行也是切割錨點
        blks = []
        for blk in _blocks(_lines(hw), 1.8):                # 上下:空隙切 + 表名錨點切(緊貼的兩張表也分得開)
            cur = []
            for l in blk:
                if cur and round(l["top"], 1) in stmt_tops:
                    blks.append(cur)
                    cur = []
                cur.append(l)
            blks.append(cur)
        blks = [b for b in blks if b]
        hs = sorted(l["bottom"] - l["top"] for l in _lines(hw)) or [8]
        lh = hs[len(hs) // 2] or 8
        toks_of = lambda b: [w["text"] for l in b if round(l["top"], 1) not in stmt_tops for w in l["ws"]]  # noqa: E731   v0106:排除表名行
        numr = lambda b: (lambda t: sum(1 for x in t if _NUM.match(x) or _PERIOD.match(x)) / max(len(t), 1))(toks_of(b))  # noqa: E731   期間表頭算數字類
        hashdr = lambda b: any((lambda ws: len(ws) >= 2 and sum(1 for w in ws if _PERIOD.match(w["text"])) >= 1 and sum(1 for w in ws if _PERIOD.match(w["text"]) or _HDR_AUX.match(w["text"])) >= 2 and sum(1 for w in ws if _PERIOD.match(w["text"]) or _HDR_AUX.match(w["text"])) / len(ws) >= 0.6)(l["ws"]) for l in b)  # noqa: E731
        merged = []
        for b in blks:                                      # v0105:表格內空白行不切表 → 沒表名 · 沒新期間表頭 · 仍是數字列 · 空隙 ≤4 行高 → 併回上一張
            if merged and numr(merged[-1]) >= 0.3 and numr(b) >= 0.3 and not hashdr(b) and hashdr(merged[-1]) and round(b[0]["top"], 1) not in figtops and b[0]["top"] - merged[-1][-1]["bottom"] <= 4 * lh:   # v0107:分節標題(Valuation / Ratios…)沒自己的期間表頭 → 併回上一張表
                merged[-1].extend(b)
            else:
                merged.append(b)
        hdr_lines = [l for l in _lines(hw) if (lambda ws: len(ws) >= 2 and sum(1 for w in ws if _PERIOD.match(w["text"])) >= 1 and sum(1 for w in ws if _PERIOD.match(w["text"]) or _HDR_AUX.match(w["text"])) >= 2 and sum(1 for w in ws if _PERIOD.match(w["text"]) or _HDR_AUX.match(w["text"])) / len(ws) >= 0.6)(l["ws"])]
        for blk in merged:
            toks = toks_of(blk) or [w["text"] for l in blk for w in l["ws"]]
            nr = numr(blk)
            first = _decoded(blk[0], tp, H)
            if _FIGCAP.match(first) and not hashdr(blk):            # v0109:圖說 / 座標軸文字不是財報表
                code, zh, kind = "FG", "圖(文字 · 圖說 / 座標軸)", "文"
            else:
                code, zh, kind = ("TB", "財報表", "表文") if len(blk) >= 3 and nr >= 0.3 else (("TT", "表名 / 標題", "文") if len(blk) <= 2 and nr < 0.2 else ("TX", "文字", "文"))
            add(major, (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), kind, code, zh, [w for l in blk for w in l["ws"]])
            if code == "TB" and not hashdr(blk):                     # v0110:表頭承接 · 同一半上方最近的期間表頭
                above = [l for l in hdr_lines if l["bottom"] <= blk[0]["top"] + 1 and l["x1"] > min(x["x0"] for x in blk) and l["x0"] < max(x["x1"] for x in blk)]
                if above:
                    zones[-1]["hdr_inherit"] = max(above, key=lambda l: l["top"])
    inbox = lambda w: any(_inside(_wb(w), bx, 2) for _, bx in halves) or any(_inside(_wb(w), fb, 1) for fb in figs)  # noqa: E731
    for blk in _blocks(_lines([w for w in mid if not inbox(w)]), 1.8):      # 跨左右分界線的字 → 財報全幅區(v0103)
        add("F", (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", "TX", "全幅文字", [w for l in blk for w in l["ws"]])
    order = {"T": 0, "F": 1, "FL": 1, "FR": 2, "B": 4}
    zones.sort(key=lambda z: (order[z["major"]], z["bbox"][1], z["bbox"][0]))
    seq = Counter()
    for z in zones:
        seq[z["major"]] += 1
        z["id"] = "P%d·%s·%02d·%s" % (pno, z["major"], seq[z["major"]], z["minor"])
    return {"W": W, "H": H, "zones": zones, "split": split, "side": "LR" if split else None, "body_size": 0}


def _join(ws: list) -> str:
    """字詞合併:中文字之間不留空 · 其餘留空格(v0109)。"""
    out = ""
    for a, b in zip([None] + list(ws[:-1]), ws):
        cjk = a is not None and re.search(r"[\u3400-\u9fff]$", a["text"]) and re.match(r"[\u3400-\u9fff]", b["text"])
        out += ("" if a is None or cjk else " ") + b["text"]
    return out


def _split_fused(lines: list) -> list:
    """v0111:黏在一起的期間表頭格(「25Q3(F) 25Q4(F) 2025(F)」是一個字詞)→ 逐 token 拆成多個字詞 · x 依字數比例分。"""
    out = []
    for l in lines:
        ws = []
        for w in l["ws"]:
            toks = w["text"].split()
            if len(toks) >= 2 and all(_PERIOD.match(t) or _HDR_AUX.match(t) for t in toks):
                n = sum(len(t) for t in toks) + len(toks) - 1
                x, wd = w["x0"], (w["x1"] - w["x0"]) / max(n, 1)
                for t in toks:
                    ws.append(dict(w, text=t, x0=x, x1=x + wd * len(t)))
                    x += wd * (len(t) + 1)
            else:
                ws.append(w)
        out.append(dict(l, ws=ws))
    return out


def _period_rows(lines: list, inherit=None, _depth: int = 0):
    """表頭期間欄 x 對齊(VRN_Unified_Repair 精華):找期間表頭列(≥2 個期間且佔該列 ≥60%)→ 數字依右緣 / 中心對到最近的期間欄 · 缺格留空不位移 · 表頭前的列(表名)單格保留。
    v0111:表頭列出現兩段相同期間序列(資產負債表｜現金流量表並排)→ 以第二段起點切左右 · 各自對齊 · 右表列接在左表後(標記〔右表〕)。"""
    lines = _split_fused(lines)
    hi = None
    for i, l in enumerate(lines):
        per = [w for w in l["ws"] if _PERIOD.match(w["text"])]
        aux = [w for w in l["ws"] if _HDR_AUX.match(w["text"])]
        if len(per) >= 1 and len(per) + len(aux) >= 2 and (len(per) + len(aux)) / len(l["ws"]) >= 0.6:   # v0109:1 期間 + 輔助欄也算表頭
            hi = (i, sorted(per + aux, key=lambda w: w["x0"]))   # v0109:YoY / QoQ 等輔助欄也是欄
            break
    if hi is None and inherit is not None:
        per = [w for w in inherit["ws"] if _PERIOD.match(w["text"]) or _HDR_AUX.match(w["text"])]
        if len(per) >= 2:
            hi = (-1, sorted(per, key=lambda w: w["x0"]))          # v0110:承接上方表頭(表頭列不在本區 · 以 -1 表示)
    if hi is None:
        return None
    i0, per = hi
    if _depth < 2 and len(per) >= 4:
        tx = [w["text"] for w in per]
        for k in range(2, len(per) // 2 + 1):
            if tx[k:2 * k] == tx[:k]:
                bd = per[k - 1]["x1"] + 2                       # 左表最後一欄右緣之後都算右表(含右表科目)
                lf = [dict(l, ws=[w for w in l["ws"] if w["x1"] <= bd]) for l in lines]
                rt = [dict(l, ws=[w for w in l["ws"] if w["x0"] >= bd]) for l in lines]
                lrows = _period_rows([l for l in lf if l["ws"]], None, _depth + 1) or []
                rrows = _period_rows([l for l in rt if l["ws"]], None, _depth + 1) or []
                return lrows + [[("〔右表〕", None)]] + rrows
    cs = [(w["x0"] + w["x1"]) / 2 for w in per]
    gap = (cs[-1] - cs[0]) / max(len(cs) - 1, 1) if len(cs) > 1 else 30
    edge = per[0]["x0"] - 0.45 * gap
    box = lambda ws: (min(w["x0"] for w in ws), min(w["top"] for w in ws), max(w["x1"] for w in ws), max(w["bottom"] for w in ws))  # noqa: E731
    rows = []
    for l in lines[:max(i0, 0)]:
        rows.append([(" ".join(w["text"] for w in l["ws"]), box(l["ws"]))])
    rows.append([("", None)] + [(w["text"], _wb(w)) for w in per])
    for l in lines[i0 + 1:]:
        lab = [w for w in l["ws"] if w["x1"] <= edge]
        cells = [[] for _ in per]
        for w in l["ws"]:
            if w["x1"] > edge:
                k = min(range(len(per)), key=lambda j: min(abs((w["x0"] + w["x1"]) / 2 - cs[j]), abs(w["x1"] - per[j]["x1"])))
                cells[k].append(w)
        rows.append([(_join(lab), box(lab) if lab else None)] + [(" ".join(w["text"] for w in c), box(c) if c else None) for c in cells])
    return rows


def text_table(z: dict, tp, H) -> dict:
    """無格線財報表:先試表頭期間欄 x 對齊(缺格留空)→ 沒表頭才依字距 >5pt 切格 · 錯碼 → pypdfium2 逐格重抽 · 每格 TRIM。"""
    lines = _lines(z["words"])
    rows = _period_rows(lines, z.get("hdr_inherit"))
    if rows is not None:
        q = quality("".join(t for r in rows for t, _ in r))
        eng = "pdfplumber(期間欄對齊%s)" % (" · 承接上方表頭" if z.get("hdr_inherit") and not any(_PERIOD.match(w["text"]) for l in lines for w in l["ws"]) else "")
        if (q[2] > 0.01 or q[1] < 0.6) and tp is not None:
            rows = [[((_pdfium(tp, (b[0] - 0.5, b[1] - 0.5, b[2] + 0.5, b[3] + 0.5), H) or t) if b else t, b) for t, b in r] for r in rows]
            q, eng = quality("".join(t for r in rows for t, _ in r)), "pypdfium2(期間欄對齊 · 逐格換)"
        out = [[clean(t) for t, _ in r] for r in rows]
        txt = "".join("".join(r) for r in out)
        return {"engine": eng, "rows": out, "records": [], "garbled": round(q[2], 4), "common": round(q[1], 3), "chart_like": _chart_like(out), "needs_ocr": garbled(txt) > 0.01 or quality(txt, 6, True)[1] < 0.4}
    rows = []
    for l in lines:
        cells, cur = [], [l["ws"][0]]
        for a, b in zip(l["ws"], l["ws"][1:]):
            if b["x0"] - a["x1"] > 5:
                cells.append(cur)
                cur = [b]
            else:
                cur.append(b)
        cells.append(cur)
        rows.append([(_join(c), (min(w["x0"] for w in c), min(w["top"] for w in c), max(w["x1"] for w in c), max(w["bottom"] for w in c))) for c in cells])
    q = quality("".join(t for r in rows for t, _ in r))
    eng = "pdfplumber"
    if (q[2] > 0.01 or q[1] < 0.6) and tp is not None:
        rows = [[(_pdfium(tp, (b[0] - 0.5, b[1] - 0.5, b[2] + 0.5, b[3] + 0.5), H) or t, b) for t, b in r] for r in rows]
        q, eng = quality("".join(t for r in rows for t, _ in r)), "pypdfium2(逐格換)"
    out = [[clean(t) for t, _ in r] for r in rows]
    txt = "".join("".join(r) for r in out)
    return {"engine": eng, "rows": out, "records": [], "garbled": round(q[2], 4), "common": round(q[1], 3), "chart_like": _chart_like(out), "needs_ocr": garbled(txt) > 0.01 or quality(txt, 6, True)[1] < 0.4}


def _chart_like(out: list) -> bool:
    """v0111:圖的座標軸刻度被當表:≥4 列 · 有科目(≥2 個中英字)的列 <30% · 不是財報表。"""
    rows = [r for r in out if any(c for c in r)]
    if len(rows) < 4:
        return False
    lab = sum(1 for r in rows if re.search(r"[A-Za-z\u3400-\u9fff]{2,}", r[0] if r else ""))
    return lab / len(rows) < 0.3


def _pdfium(tp, bbox, H) -> str:
    x0, top, x1, bottom = bbox
    return tp.get_text_bounded(left=x0, bottom=H - bottom, right=x1, top=H - top) if tp is not None else ""


def extract_zone(page, z: dict, fz=None, tp=None) -> dict:
    """每區分開擷取:pdfplumber → 錯碼 / 常用字比例低 → pypdfium2(同框重抽)→ pymupdf → 都不行 → OCR 排隊。"""
    if z["kind"] == "圖":
        return {"engine": "—", "records": [], "rows": [], "garbled": 0.0, "needs_ocr": False}
    H = float(page.height)
    if z["kind"] == "表文":
        r = text_table(z, tp, H)
        if r.get("chart_like"):                                      # v0111:刻度不是表 → 歸圖(FG)
            z["kind"], z["minor"], z["minor_zh"] = "圖", "FG", "圖(座標軸刻度)"
            z["id"] = re.sub(r"·[A-Z]+$", "·FG", z["id"])
            return {"engine": "—(刻度)", "records": [], "rows": r["rows"], "garbled": 0.0, "needs_ocr": False}
        return r
    bad = lambda q: q[2] > 0.01 or q[1] < 0.6  # noqa: E731     觸發換引擎(中文 ≥2 字就判)
    ocr = lambda txt: garbled(txt) > 0.01 or quality(txt, 6, True)[1] < 0.4  # noqa: E731     送 OCR 要更嚴(中文 ≥6 字 · 常用字 <0.4 才送 · 常用字表有限不誤送)
    if z["kind"] == "表":
        crop = page.crop(z["bbox"], strict=False)
        try:
            ts = crop.find_tables()
            t = ts[0] if ts else None
            rows = t.extract() if t else (crop.extract_table() or [])
        except Exception:  # noqa: BLE001
            t, rows = None, []
        q = quality("".join("".join(c or "" for c in r) for r in rows))
        eng = "pdfplumber"
        if bad(q) and t is not None and tp is not None:
            rows = [[(_pdfium(tp, c, H) if c else "") for c in r.cells] for r in t.rows]
            q, eng = quality("".join("".join(r) for r in rows)), "pypdfium2(逐格換)"
        rows = [[clean(c or "") for c in r] for r in rows]
        return {"engine": eng, "rows": rows, "records": [], "garbled": round(q[2], 4), "common": round(q[1], 3), "needs_ocr": ocr("".join("".join(r) for r in rows))}
    lines = _lines(z["words"])
    cands = [("pdfplumber", [(l["text"], l["size"]) for l in lines])]
    q0 = quality("\n".join(l["text"] for l in lines))                # v0109:逐行評估(行首項目符號規則才生效)
    if bad(q0):
        if tp is not None:
            cands.append(("pypdfium2(換)", [(t, 0) for t in re.split(r"\r?\n", _pdfium(tp, z["bbox"], H))]))
        if fz is not None:
            try:
                import fitz  # noqa: WPS433
                cands.append(("pymupdf(換)", [(t, 0) for t in fz.get_text("text", clip=fitz.Rect(*z["bbox"])).splitlines()]))
            except Exception:  # noqa: BLE001
                pass
    scored = [(quality("\n".join(t for t, _ in ls)), e, ls) for e, ls in cands]
    q, eng, ls = max(scored, key=lambda x: x[0][0])
    need = ocr("\n".join(t for t, _ in ls))
    return {"engine": eng if not need else eng + " · 仍錯碼 → OCR 排隊", "records": records(ls, mode="body" if z["major"] == "M" else "info"), "rows": [], "garbled": round(q[2], 4),
            "common": round(q[1], 3), "needs_ocr": need}


# ===== v0113 擷取後修復層(不刪字 · 原文留 raw · 每區記 repairs)=====
TYPO_FIX = [("中國僖託", "中國信託"), ("團泰期賃", "國泰期貨"), ("團泰期貨", "國泰期貨"), ("團泰證", "國泰證"), ("漲跌輻", "漲跌幅"), ("漲輻", "漲幅"), ("跌輻", "跌幅"), ("僖託", "信託"), ("期賃", "期貨")]
_NUMCELL = re.compile(r"^[\s\d,.()%\-+−]+$")
_SPACED = re.compile(r"(?<![A-Za-z])(?:[A-Za-z]{1,2} ){3,}[A-Za-z]{1,2}(?![A-Za-z])")
_SPACED_CAPS = re.compile(r"(?<=[\u4e00-\u9fff] )((?:[A-Z] ){1,}[A-Z])(?= ?[\u4e00-\u9fff]|$)")
_NUMTOK = re.compile(r"^[(\-−]?[\d,]+(?:\.\d+)?%?\)?$|^n\.?a\.?$|^-+$|^NM$", re.I)


def fix_num(c: str, cell: bool = True) -> str:
    """數字被字距拆開接回:( 457)→(457) · 1 ,154 / 3 .2 → 1,154 / 3.2 · 1, 650 → 1,650 · (只在表格格)1 20,843 → 120,843。"""
    if not c or not re.search(r"\d", c):
        return c
    if cell and not _NUMCELL.match(c):
        return c
    s = re.sub(r"\(\s+(?=[\d\-])", "(", c)
    s = re.sub(r"(?<=\d)\s+\)", ")", s)
    s = re.sub(r"(\d)\s+([,.])\s*(\d)", r"\1\2\3", s)
    s = re.sub(r"(\d)([,.])\s+(\d{3})(?!\d)", r"\1\2\3", s)
    if cell:
        s = re.sub(r"(?<![\d,.])(\d)\s+(\d{1,2}(?:,\d{3})+(?:\.\d+)?)(?![\d,])", r"\1\2", s)
    return s


def fix_spaced(t: str) -> str:
    """英文字母被拉開接回(≥4 段且多半是單字母 · 小寫接大寫處補空格)· 中文旁的 E T F → ETF · 2 0 2 6 → 2026。"""
    if not t or " " not in t:
        return t

    def j(m):
        toks = m.group(0).split(" ")
        if sum(1 for x in toks if len(x) == 1) / len(toks) < 0.6:
            return m.group(0)
        return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", "".join(toks))
    t = _SPACED.sub(j, t)
    t = _SPACED_CAPS.sub(lambda m: m.group(1).replace(" ", ""), t)
    t = re.sub(r"(?<!\d)(\d{4}) ?\. ?T ?W ?(O?)(?![A-Za-z])", r"\1.TW\2", t)                     # 2383 . T W → 2383.TW
    return re.sub(r"(?<!\d)([12]) (\d) (\d) (\d)(?!\d)", lambda m: "".join(m.groups()) if re.match(r"(?:19|20)\d\d$", "".join(m.groups())) else m.group(0), t)


def fix_typo(t: str) -> str:
    for a, b in TYPO_FIX:
        if a in t:
            t = t.replace(a, b)
    return t


def period_count(rows: list) -> int:
    rows = [[(c or "").strip() for c in r] for r in rows or []]
    hdr = next((r for r in rows if sum(1 for c in r if c and _PERIOD.match(c)) >= 2), None)
    return sum(1 for c in hdr if c and _PERIOD.match(c)) if hdr else 0


def tidy_period(rows: list, inherit: int = 0) -> bool:
    """欄位整齊:有一列 ≥2 個期間欄(或承接上表表頭 inherit 欄),且 ≥3 列數字列的數字格數 ≈ 期間欄數(±1)占 ≥70%。"""
    rows = [[(c or "").strip() for c in r] for r in rows or []]
    na = period_count(rows) or inherit
    if na < 2:
        return False
    nr = [k for k in (sum(1 for c in r if c and _NUMTOK.match(c)) for r in rows) if k >= 2]
    return len(nr) >= 3 and sum(1 for k in nr if na - 1 <= k <= na + 1) / len(nr) >= 0.7


def inherit_tidy(zones: list) -> None:
    """同頁:沒有自己期間表頭的表 · 上一張(同欄位區)有期間表頭且欄數相同 → 欄位整齊(承接上表表頭)。"""
    last = {}
    for z in zones:
        if z.get("minor") != "TB" or not z.get("rows"):
            continue
        col = z.get("major")
        pc = period_count(z["rows"])
        eng = z.get("engine") or ""
        if pc:
            last[col] = pc
            continue
        if "期間欄" not in eng and "欄位整齊" not in eng and last.get(col) and tidy_period(z["rows"], last[col]):
            z["engine"] = eng + " · 欄位整齊(承接上表表頭)"
            z.setdefault("repairs", {})["欄位整齊"] = z.get("repairs", {}).get("欄位整齊", 0) + 1


def repair_zone(z: dict) -> dict:
    """擷取後修復:表格格 → 數字接回 · 字母間距 · 錯字;文字記錄 → 同上(數字只接安全的兩種)· 欄位整齊標記。原文留 z['raw'],次數留 z['repairs']。"""
    n, raw = Counter(), {}
    for i, r in enumerate(z.get("rows") or []):
        for j, c in enumerate(r):
            if not c:
                continue
            a = fix_num(c, True)
            b = fix_spaced(a)
            d = fix_typo(b)
            if d != c:
                raw["%d,%d" % (i, j)] = c
                r[j] = d
                n["數字接回"] += a != c
                n["字母間距"] += b != a
                n["錯字"] += d != b
    for k, x in enumerate(z.get("records") or []):
        t = x.get("text", "") if isinstance(x, dict) else ""
        if not t:
            continue
        a = fix_num(t, False)
        b = fix_spaced(a)
        d = fix_typo(b)
        if d != t:
            raw["r%d" % k] = t
            x["text"] = d
            n["數字接回"] += a != t
            n["字母間距"] += b != a
            n["錯字"] += d != b
    if z.get("minor") == "TB" and z.get("rows") and "期間欄" not in (z.get("engine") or "") and tidy_period(z["rows"]):
        z["engine"] = (z.get("engine") or "") + " · 欄位整齊"
        n["欄位整齊"] += 1
    n = {k: v for k, v in n.items() if v}
    if n:
        z["repairs"] = n
        z["raw"] = raw
    return z


def recategorize(z: dict):
    if z["kind"] == "文" and z["major"] in ("L", "R", "T", "B") and z["minor"] != "TT" and z["id"].startswith("P1·"):
        z["minor"], z["minor_zh"] = _minor(" ".join(x["text"] for x in z.get("records") or []))
        z["id"] = re.sub(r"·[A-Z]+$", "·" + z["minor"], z["id"])


_FONTS = [r"C:\Windows\Fonts\msjh.ttc", r"C:\Windows\Fonts\mingliu.ttc", r"C:\Windows\Fonts\msyh.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]


def _font(size=22):
    from PIL import ImageFont
    for f in _FONTS:
        if Path(f).exists():
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                continue
    return ImageFont.load_default()


def text_png(lines: list, dst: Path, width=1700, size=26) -> Path:
    """文字 → OCR 好讀的 PNG(白底黑字 · 大字級 · 中文字型)。"""
    from PIL import Image, ImageDraw
    f = _font(size)
    h = max(400, 60 + len(lines) * int(size * 1.6))
    im = Image.new("RGB", (width, h), "white")
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((40, 30 + i * int(size * 1.6)), l[:90], fill="black", font=f)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return dst


def read_txt(p: Path) -> tuple:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "gb18030", "utf-16"):
        try:
            t = raw.decode(enc)
            if garbled(t) < 0.001:
                return t, enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8(替代)"


def read_docx(p: Path) -> tuple:
    try:
        import docx  # noqa: WPS433
        d = docx.Document(str(p))
        paras = [x.text for x in d.paragraphs]
        for t in d.tables:
            for r in t.rows:
                paras.append(" | ".join(clean(c.text) for c in r.cells))
        return "\n".join(paras), "python-docx"
    except Exception:  # noqa: BLE001
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        paras = [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)]
        return "\n".join(html.unescape(x) for x in paras), "zip XML(換)"


def queue_dir() -> Path:
    return Path(os.environ.get("VIA_SPILL_DIR") or tempfile.gettempdir()) / "vrn_ocr_queue"


def non_pdf(p: Path, kind: str) -> dict:
    """Word / TXT / 圖片 → 首頁 + 財報頁 PNG 到 TEMP 排隊(Word / TXT 同時直接擷取 · 記錄)。"""
    q = queue_dir() / re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", p.stem)[:60]
    out = {"kind": kind, "queue": str(q), "pngs": [], "records": [], "engine": "", "garbled": 0.0}
    if kind == "IMG":
        from PIL import Image
        im = Image.open(p).convert("RGB")
        if im.width < 1800:
            k = 1800 / im.width
            im = im.resize((1800, int(im.height * k)))
        q.mkdir(parents=True, exist_ok=True)
        im.save(q / "p1.png")
        out.update(pngs=[str(q / "p1.png")], engine="PIL")
        return out
    if kind == "WORD(舊)":
        out["engine"] = "需要 Word 轉 .docx(舊 .doc 無法直讀)"
        return out
    text, eng = read_txt(p) if kind == "TXT" else read_docx(p)
    lines = [clean(l) for l in text.splitlines() if clean(l)]
    out.update(engine=eng, garbled=round(garbled(text), 4), records=records([(l, 0) for l in lines[:60]]))
    out["pngs"].append(str(text_png(lines[:48], q / "p1.png")))
    starts, last = [], -10 ** 6
    for i, l in enumerate(lines):
        if _FIN.search(l) and i >= last + 40:                 # 財報段落起點 · 每 40 行一張(不重複輸出同一段)
            starts.append(i)
            last = i
    for n, i in enumerate(starts[:3]):
        out["pngs"].append(str(text_png(lines[i:i + 40], q / ("fin%d.png" % (n + 1)))))
    return out


def render(page, seg: dict, dst: Path, res=110) -> Path:
    from PIL import ImageDraw
    im = page.to_image(resolution=res).original.convert("RGB")
    k = res / 72.0
    d = ImageDraw.Draw(im)
    f = _font(14)
    for z in seg["zones"]:
        c = COLOR.get(z["minor"]) or COLOR[z["major"]]
        b = [v * k for v in z["bbox"]]
        d.rectangle(b, outline=c, width=2)
        d.text((b[0] + 2, max(b[1] - 15, 0)), z["id"], fill=c, font=f)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return dst


def judge(rec: dict) -> dict:
    """燈號依擷取品質(v0104):紅 = 錯碼區送 OCR · 黃 = 列出原因 · 綠 = 沒有原因;版型只當資訊。"""
    pages = rec.get("pages") or []
    p1 = pages[0] if pages else {"zones": [], "side": None}
    zs = [z for pg in pages for z in pg["zones"]]
    rt_rx = MINOR[0][2]
    p1txt = lambda z: " ".join(x["text"] for x in z.get("records") or []) + " ".join(" ".join(r) for r in z.get("rows") or [])  # noqa: E731
    rt = any(z["minor"] == "RT" or re.search(rt_rx, p1txt(z)) for z in p1["zones"])
    rt_top = any(z["major"] == "T" and re.search(rt_rx, p1txt(z)) for z in p1["zones"])
    layout = {"L": "側欄型(左)", "R": "側欄型(右)"}.get(p1.get("side")) or ("頁首資訊型" if rt_top else "單欄型")
    fin_tb = [z for pg in pages[1:] for z in pg["zones"] if z["minor"] == "TB"]
    unal = [z for z in fin_tb if "期間欄" not in (z.get("engine") or "") and "欄位整齊" not in (z.get("engine") or "")]
    ocr = [z for z in zs if z.get("needs_ocr")]
    reasons = []
    notext = bool(pages) and not p1["zones"]
    if notext:
        reasons.append("首頁無文字層 → OCR 排隊")
    if ocr:
        reasons.append("錯碼區 %d → OCR 排隊" % len(ocr))
    if not pages[1:]:
        reasons.append("沒找到財報頁")
    elif not fin_tb:
        reasons.append("財報頁沒切出財報表")
    elif unal:
        reasons.append("財報表沒對到期間欄 %d/%d" % (len(unal), len(fin_tb)))
    if not rt:
        reasons.append("首頁沒抓到評等 / 目標價")
    return {"layout": layout, "reasons": reasons, "lamp": "RED" if (ocr or notext) else ("YELLOW" if reasons else "GREEN")}


CONTRACT = json.loads('{"schema": "VIA.VRN.P1ViewRecordsContract.v1", "version": "v0100", "producer": "VRN_ENG397_P1Segment (v0108+ 每次執行自動寫出) via VRN_SystemManager p1view / p1loop", "files": {"records_csv": "VIA_Reports/vrn/p1view/P1VIEW_records_latest.csv (UTF-8 with BOM · 每列一筆記錄 · 扁平)", "json": "VIA_Reports/vrn/p1view/P1VIEW_latest.json (每份 PDF 一物件:pages → zones → records / rows)", "md": "VIA_Reports/vrn/p1view/P1VIEW_latest.md (≤300 行 · 原因統計 · 每份一行 · 紅燈 / 未對期間欄 / 退步 的區塊細節)", "lock": "VIA_Reports/vrn/p1view/VRN_P1View_Lock_latest.json (綠燈檔案鎖定 · 只增不減)", "rounds": "VIA_Reports/vrn/p1view/VRN_P1View_Rounds.jsonl (每輪 append-only)", "ocr_queue": "VIA_Reports/vrn/p1view/ocr_queue/<檔名>/<區編號>.png (持久 · 不在 TEMP 滾動清理內 · 直到該檔轉綠或更換測試內容)"}, "scope": {"input": "C:\\\\測試樣本報告 (VRN input_dir)", "pages": "每份 PDF:第 1 頁 + 年度財報頁(≤4 頁 · 關鍵字 + 數字比例 ≥18% 或 期間表頭列 ≥2)", "skipped": "Word / TXT / 圖片 暫不處理(只計數)"}, "coordinates": {"origin": "頁面左上角", "unit": "pt(PDF 點 · pdfplumber 座標)", "fields": "X0 / TOP / X1 / BOTTOM 為區塊外框;表格儲存格座標在 JSON 的 rows 不保留 · 以區塊框 + ROW/COL 定位"}, "columns": [{"name": "FILE", "type": "str", "desc": "PDF 檔名"}, {"name": "PAGE", "type": "int", "desc": "頁碼(1 起算)"}, {"name": "ZONE", "type": "str", "desc": "區編號 P{頁}·{大類}·{序號 2 位}·{小類} · 例 P2·FL·03·TB"}, {"name": "MAJOR", "type": "enum", "values": {"頁首": "T", "頁尾": "B", "左資訊區": "L", "右資訊區": "R", "本文": "M", "財報全幅": "F", "財報左半": "FL", "財報右半": "FR"}}, {"name": "MINOR", "type": "enum", "values": {"標題": "TT", "文字": "TX", "本文段落": "TX", "本文(全幅)": "TX", "全幅文字": "TX", "表格": "TB(有格線)", "財報表": "TB(無格線 · 逐格)", "表名 / 標題": "TT", "評等 / 目標價": "RT", "股價資料": "SD", "分析師": "AN", "免責 / 揭露": "DS", "日期 / 報告資訊": "DT", "圖": "IMG(點陣)", "圖表(向量)": "FG"}}, {"name": "KIND", "type": "enum", "values": ["文", "表", "表文", "圖"]}, {"name": "X0", "type": "float"}, {"name": "TOP", "type": "float"}, {"name": "X1", "type": "float"}, {"name": "BOTTOM", "type": "float"}, {"name": "ROW", "type": "int", "desc": "表格:列序(0 起);文字:記錄序"}, {"name": "COL", "type": "int|empty", "desc": "表格:欄序(0 = 科目 · 1.. = 期間欄);文字:空"}, {"name": "REC_KIND", "type": "enum", "values": {"標題": "無句號一行一筆(行首項目符號已去)", "句": "到句號一句一筆(跨行已接 · 不接到標題)", "資訊": "資訊區一行一筆(標籤:值 · 不串句)", "格": "表格儲存格"}}, {"name": "TEXT", "type": "str", "desc": "已 TRIM · 中文字間無空格 · 全形英數轉半形 · 私用區 / (cid:N) 已去 · 不含亂碼修復以外的改寫 · v0113 起含擷取後修復(數字接回 · 字母間距 · 錯字表)· 原文留 JSON raw"}, {"name": "ENGINE", "type": "str", "desc": "pdfplumber | pdfplumber(期間欄對齊) | pypdfium2(換) | pypdfium2(逐格換) | pypdfium2(期間欄對齊 · 逐格換) | pymupdf(換) | ... · 仍錯碼 → OCR 排隊"}, {"name": "GARBLED", "type": "float", "desc": "亂碼比例(0~1):私用區 / 替代字元 / 非行首 (cid:N);常用字比例另見 JSON common"}], "table_rows": {"header_row": "COL=0 為空、COL≥1 為期間(2024A / 2025F / FY25 / 1H25 / 112年 / 113F …)的那一列 = 期間表頭;其後每列 COL=0 科目 · COL≥1 數值文字(原樣 · 含千分位 / 括號 / 負號)", "missing_cell": "缺格留空(不位移)", "section_rows": "只有 COL=0 的列 = 表名或分節標題(如 Valuation)", "blank_rows": "表內空白行已併回同一張表"}, "lamp": {"RED": "任一區 needs_ocr(錯碼 · 已切 PNG 排 OCR)", "YELLOW": "原因之一:沒找到財報頁 | 財報頁沒切出財報表 | 財報表沒對到期間欄 n/m | 首頁沒抓到評等 / 目標價", "GREEN": "以上皆無", "layout_info_only": "側欄型(左) / 側欄型(右) / 頁首資訊型 / 單欄型 不影響燈號"}, "consumer_contract_for_G06": {"use": "VRN_Main G06 改吃 records_csv:KIND in (\'表\',\'表文\') 的列即財報列;依 ZONE 聚合成表 · 以 ROW=header_row 的期間欄對齊", "do_not": "不要重算座標;不要去 TEXT 的括號 / 負號(保留給驗算);不要把 TT / 分節列當科目"}, "stability": "欄位只增不減 · 新欄位加在最後 · 版本改變時 schema 版號 +1 並留舊欄位"}')


def write_contract(home: Path, od: Path):
    """v0108:契約正本 JSON + 可讀 MD 自動寫出(和程式同步 · 只增不減)。"""
    cd = home / "contract"
    cd.mkdir(parents=True, exist_ok=True)
    c = dict(CONTRACT)
    c["files"] = dict(c["files"], **{"records_csv": str(od / "P1VIEW_records_latest.csv"), "json": str(od / "P1VIEW_latest.json"), "md": str(od / "P1VIEW_latest.md"), "ocr_queue": str(od / "ocr_queue")})
    (cd / "VRN_P1VIEW_RECORDS_CONTRACT_latest.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# VRN P1VIEW 擷取列契約 · %s · %s" % (c["version"], c["schema"]), "產生者:%s" % c["producer"], "", "## 檔案"] + ["- **%s**:%s" % kv for kv in c["files"].items()] + ["", "## 範圍"] + ["- %s:%s" % kv for kv in c["scope"].items()] + ["", "## 座標"] + ["- %s:%s" % kv for kv in c["coordinates"].items()] + ["", "## 欄位(records_csv)", "| 欄 | 型別 | 說明 |", "|---|---|---|"]
    for col in c["columns"]:
        d = col.get("desc", "") or (" · ".join("%s=%s" % kv for kv in col["values"].items()) if isinstance(col.get("values"), dict) else " / ".join(col.get("values", [])))
        L.append("| %s | %s | %s |" % (col["name"], col["type"], d))
    L += ["", "## 表格列規則"] + ["- %s:%s" % kv for kv in c["table_rows"].items()] + ["", "## 燈號"] + ["- %s:%s" % kv for kv in c["lamp"].items()] + ["", "## 給 VRN_Main G06 的用法"] + ["- %s:%s" % kv for kv in c["consumer_contract_for_G06"].items()] + ["", "## 穩定性", "- %s" % c["stability"]]
    (cd / "VRN_P1VIEW_RECORDS_CONTRACT_latest.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return cd


def write_records(res: list, od: Path):
    """v0107:扁平擷取列 CSV(給 ETL / 表格修復引擎)+ MD 摘要(≤300 行 · AI 直接讀 · 不用截圖)。"""
    import csv
    with (od / "P1VIEW_records_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["FILE", "PAGE", "ZONE", "MAJOR", "MINOR", "KIND", "X0", "TOP", "X1", "BOTTOM", "ROW", "COL", "REC_KIND", "TEXT", "ENGINE", "GARBLED"])
        for r in res:
            for pg in r.get("pages") or []:
                for z in pg["zones"]:
                    b = z["bbox"]
                    base = [r["file"], pg["pno"], z["id"], MAJOR.get(z["major"], z["major"]), z["minor_zh"], z["kind"], b[0], b[1], b[2], b[3]]
                    if z.get("rows"):
                        for ri, row in enumerate(z["rows"]):
                            for ci, c in enumerate(row):
                                if c:
                                    w.writerow(base + [ri, ci, "格", c, z.get("engine", ""), z.get("garbled", 0)])
                    else:
                        for ri, x in enumerate(z.get("records") or []):
                            w.writerow(base + [ri, "", x["kind"], x["text"], z.get("engine", ""), z.get("garbled", 0)])
    L = ["# P1VIEW 切割擷取摘要 · %s · PDF %d 份 · 燈 %s" % (time.strftime("%Y-%m-%d %H:%M"), len(res), dict(Counter(r.get("lamp") for r in res)))]
    rc = Counter(re.sub(r" \d+(/\d+)?", "", x) for r in res for x in (r.get("reasons") or []))
    L.append("## 原因統計:" + (" · ".join("%s %d" % kv for kv in rc.most_common()) or "無"))
    L.append("## 版型:" + " · ".join("%s %d" % kv for kv in Counter(r.get("layout") or "—" for r in res).most_common()))
    L.append("## 每份一行(燈 | 檔 | 版型 | 財報頁 | 區 | 原因)")
    for r in res:
        L.append("- %s | %s | %s | %d | %d | %s" % (r.get("lamp"), r["file"][:40], r.get("layout") or "—", r.get("fin_n", 0), r.get("zones_n", 0), " / ".join(r.get("reasons") or []) or "—"))
    L.append("## 細節(紅燈 · 沒對到期間欄的表 · 沒抓到評等的首頁;每區一行:編號 | 大類·小類 | 框 | 引擎 | 亂碼 | 常用字 | 列數 | 首 60 字)")
    n = 0
    for r in res:
        if n >= 150:
            break
        flag = [z for pg in (r.get("pages") or []) for z in pg["zones"] if z.get("needs_ocr") or (z["minor"] == "TB" and pg["pno"] > 1 and "期間欄" not in (z.get("engine") or "") and "欄位整齊" not in (z.get("engine") or ""))]
        if "首頁沒抓到評等 / 目標價" in (r.get("reasons") or []) and r.get("pages"):
            flag += [z for z in r["pages"][0]["zones"] if z["major"] in ("T", "L", "R") and z["kind"] == "文"][:4]
        if not flag:
            continue
        L.append("### %s · %s" % (r["file"][:40], r.get("lamp")))
        for z in flag[:12]:
            txt = " ".join(x["text"] for x in z.get("records") or []) or " | ".join(" ".join(c for c in row if c) for row in (z.get("rows") or [])[:3])
            L.append("- %s | %s·%s | %s | %s | %s | %s | %d | %s" % (z["id"], MAJOR.get(z["major"], z["major"]), z["minor_zh"], [int(v) for v in z["bbox"]], z.get("engine", ""), z.get("garbled", 0), z.get("common", ""), len(z.get("rows") or z.get("records") or []), txt[:60]))
            n += 1
    (od / "P1VIEW_latest.md").write_text("\n".join(L[:300]) + "\n", encoding="utf-8")


def run(indir: Path, rep: Path, one: str = "") -> dict:
    """只做 PDF(Word / TXT 暫不處理 · 只計數)· 每份:第一頁 + 財報頁(≤3)· 先切割再擷取 · HTML U/I。"""
    import pdfplumber  # noqa: WPS433
    indir, rep = Path(indir), Path(rep)
    od = rep / "p1view"
    (od / "img").mkdir(parents=True, exist_ok=True)
    allf = sorted(p for p in indir.rglob("*") if p.is_file() and p.suffix.lower() in EXT and (not one or one in p.name))
    items = [p for p in allf if p.suffix.lower() == ".pdf"]
    skipped = Counter(EXT[p.suffix.lower()] for p in allf if p.suffix.lower() != ".pdf")
    res = []
    for n, p in enumerate(items, 1):
        rec = {"n": n, "file": p.name, "kind": "PDF", "pages": []}
        try:
            fzd = pdoc = None
            try:
                import fitz  # noqa: WPS433
                fzd = fitz.open(str(p))
            except Exception:  # noqa: BLE001
                fzd = None
            try:
                import pypdfium2 as pdfium  # noqa: WPS433
                pdoc = pdfium.PdfDocument(str(p))
            except Exception:  # noqa: BLE001
                pdoc = None
            with pdfplumber.open(str(p)) as pdf:
                for idx in [0] + fin_pages(pdf, pdoc):
                    page = pdf.pages[idx]
                    tp = pdoc[idx].get_textpage() if pdoc is not None else None
                    seg = segment(page, 1) if idx == 0 else segment_fin(page, idx + 1, tp)
                    fz = fzd[idx] if fzd is not None else None
                    q = od / "ocr_queue" / re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", p.stem)[:60]   # v0108:持久位置 · 同一輸入不清
                    for z in seg["zones"]:
                        z.update(extract_zone(page, z, fz, tp))
                        recategorize(z)
                        repair_zone(z)                                         # v0113 擷取後修復層
                        z.pop("words", None)
                        z.pop("hdr_inherit", None)
                        if z.get("needs_ocr"):
                            q.mkdir(parents=True, exist_ok=True)
                            page.crop(z["bbox"], strict=False).to_image(resolution=300).original.save(q / (z["id"].replace("·", "_") + ".png"))
                    inherit_tidy(seg["zones"])                                 # v0113 承接上表表頭
                    if idx == 0 and not seg["zones"]:                        # v0112:首頁無文字層 → 整頁進 OCR 排隊
                        q.mkdir(parents=True, exist_ok=True)
                        page.to_image(resolution=300).original.save(q / "P1_page.png")
                    render(page, seg, od / "img" / ("%03d_p%d.png" % (n, idx + 1)))
                    rec["pages"].append({"pno": idx + 1, "fin": idx > 0, "img": "img/%03d_p%d.png" % (n, idx + 1), "zones": seg["zones"], "side": seg["side"]})
            zs = [z for pg in rec["pages"] for z in pg["zones"]]
            g = max([z["garbled"] for z in zs] or [0])
            p1 = rec["pages"][0]
            rec.update(garbled=g, zones_n=len(zs), fin_n=len(rec["pages"]) - 1)
            rec.update(judge(rec))
        except Exception as exc:  # noqa: BLE001
            rec.update(lamp="RED", err="%s: %s" % (type(exc).__name__, str(exc)[:120]))
        res.append(rec)
        print("  [切] %d/%d · %s · %s" % (n, len(items), p.name[:40], rec.get("err") or "第一頁 + 財報頁 %d · %d 區" % (rec.get("fin_n", 0), rec.get("zones_n", 0))), flush=True)
    (od / "P1VIEW_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    write_records(res, od)
    write_contract(HERE, od)
    try:
        qd = queue_dir()
        qd.mkdir(parents=True, exist_ok=True)
        (qd / ".via_keep").write_text("VRN p1view OCR queue · 保留", encoding="utf-8")   # TEMP 排隊夾標記不清
    except OSError:
        pass
    lampc = {"GREEN": "#16a34a", "YELLOW": "#eab308", "RED": "#dc2626", "GRAY": "#9ca3af"}
    nav = "".join("<a href='#f%d' title='%s'><i style='background:%s'></i>%s</a>" % (r["n"], html.escape(" / ".join(r.get("reasons") or []) or "綠"), lampc[r["lamp"]], html.escape(r["file"][:34])) for r in res)
    rc = Counter(re.sub(r" \d+(/\d+)?", "", x) for r in res for x in (r.get("reasons") or []))
    lc = Counter(r.get("layout") or "—" for r in res)
    stats = "<p>燈號原因統計(一份可有多個原因):%s<br>版型:%s</p>" % (" · ".join("%s %d 份" % kv for kv in rc.most_common()) or "無", " · ".join("%s %d" % kv for kv in lc.most_common()))
    secs = []
    for r in res:
        pg_html = ""
        for pg in r.get("pages") or []:
            zrows = ""
            for z in pg["zones"]:
                body = ""
                if z.get("rows"):
                    body = "<table class=t>" + "".join("<tr>" + "".join("<td>%s</td>" % html.escape(c) for c in row) + "</tr>" for row in z["rows"]) + "</table>"
                elif z.get("records"):
                    body = "".join("<div class='%s'>%s</div>" % ("h" if x["kind"] == "標題" else "s", html.escape(x["text"])) for x in z["records"])
                zrows += "<tr><td><b>%s</b></td><td>%s · %s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                    z["id"], MAJOR.get(z["major"], z["major"]), z["minor_zh"], z.get("engine", ""), ("%.1f%%" % (100 * z.get("garbled", 0))) if z.get("garbled") else "0", body)
            pg_html += "<h4>第 %d 頁 · %s</h4><div class=g><div class=pi><img src='%s'></div><div><table class=z><tr><th>編號</th><th>大類 · 小類</th><th>引擎</th><th>亂碼</th><th>擷取還原</th></tr>%s</table></div></div>" % (
                pg["pno"], "財報頁" if pg["fin"] else "首頁", pg["img"], zrows)
        why = (" · <b>" + html.escape(" / ".join(r.get("reasons") or [])) + "</b>") if r.get("reasons") else ""
        secs.append("<section id='f%d'><h3><i style='background:%s'></i>%s · %s%s%s</h3>%s</section>" % (
            r["n"], lampc[r["lamp"]], html.escape(r["file"]), html.escape(r.get("layout") or "—"), why, (" · " + html.escape(r["err"])) if r.get("err") else "", pg_html))
    css = ("body{margin:0;font:13px system-ui,-apple-system,'Microsoft JhengHei',sans-serif;display:flex}nav{width:240px;height:100vh;overflow:auto;position:sticky;top:0;border-right:1px solid #e5e7eb;padding:6px}"
           "nav a{display:block;padding:3px 4px;color:#111;text-decoration:none;font-size:12px}i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}"
           "main{flex:1;padding:8px;overflow:auto}.g{display:grid;grid-template-columns:minmax(300px,46%) 1fr;gap:8px}.pi img{width:100%;border:1px solid #e5e7eb}"
           "table.z{border-collapse:collapse;width:100%}table.z td,table.z th{border:1px solid #e5e7eb;padding:3px;vertical-align:top;font-size:12px}.t td{border:1px solid #d1d5db;padding:1px 3px}"
           ".h{font-weight:700;color:#1d4ed8;margin:2px 0}.s{margin:1px 0}@media(max-width:900px){.g{grid-template-columns:1fr}nav{display:none}}")
    (od / "P1VIEW_latest.html").write_text("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>第一頁 + 財報頁切割擷取</title><style>%s</style><nav>%s</nav><main>"
                                           "<h2>第一頁 + 財報頁切割擷取 · %s · 框色:藍 頁首 · 橘 資訊欄 / 財報左半 · 綠 本文 · 紅 表格 · 紫 圖 · 灰 頁尾</h2>%s</main>" % (css, nav, ENGINE_ID, stats + "".join(secs)), encoding="utf-8")
    print("[計] 燈號原因(%s · 一份可多個):%s · 版型 %s" % (ENGINE_ID, " · ".join("%s %d" % kv for kv in rc.most_common()) or "無", dict(lc)), flush=True)
    return {"n": len(res), "kinds": {"PDF": len(items)}, "skipped": dict(skipped), "lamps": dict(Counter(r["lamp"] for r in res)),
            "zones": sum(r.get("zones_n", 0) for r in res), "fin_pages": sum(r.get("fin_n", 0) for r in res), "queued": 0, "html": str(od / "P1VIEW_latest.html"),
            "errs": [r for r in res if r.get("err")][:4], "queue": str(od / "ocr_queue"), "reasons": dict(rc), "layouts": dict(lc), "contract": str(HERE / "contract" / "VRN_P1VIEW_RECORDS_CONTRACT_latest.json")}


def _fixture_pdf(path: Path):
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
    c = canvas.Canvas(str(path), pagesize=(595, 842))
    from PIL import Image as _Im
    bg = str(Path(tempfile.gettempdir()) / "vrn_eng397_bg.png")
    _Im.new("RGB", (60, 85), (250, 250, 250)).save(bg)
    c.drawImage(bg, 0, 0, width=595, height=842)                       # 整頁背景圖(v0106:要忽略 · 不擋字)
    c.saveState()
    c.translate(18, 300)
    c.rotate(90)
    c.setFont("Helvetica", 8)
    c.drawString(0, 0, "KGI Securities Asia Equity Research Watermark")  # 直排浮水印(v0106:要排除)
    c.restoreState()
    c.setFont("MSung-Light", 20)
    c.drawString(40, 800, "健策 3653 TT 液冷成長動能強勁")
    c.setFont("MSung-Light", 12)
    c.drawString(470, 800, "Overweight")                                   # 標題同列右側評等(v0106:要分開)
    c.setFont("MSung-Light", 9)
    for i, t in enumerate(["評等:買進", "目標價:NT$650", "", "股價(10/1):520", "市值:NT$65bn", "", "分析師 王小明", "wang@kgi.com"]):
        if t:
            c.drawString(40, 700 - i * 14, t)
    c.setFont("ZapfDingbats", 9)
    c.drawString(205, 700, "\u00e0")                                        # 項目符號(符號字型 → (cid:N) · v0107 不算錯碼)
    c.setFont("MSung-Light", 10)
    y = 700
    for t in ["投資重點", "公司第三季營收年增 25%,優於", "預期。毛利率提升至 38%。", "", "", "展望", "明年液冷需求持續擴大。"]:
        if t == "展望":
            c.setFont("ZapfDingbats", 9)
            c.drawString(205, y, "\u00e0")                                # 第二個項目符號(不在區塊第一行 · v0109 逐行評估)
            c.setFont("MSung-Light", 10)
        if t:
            c.drawString(220, y, t)
        y -= 15
    xs, ys = [220, 320, 420, 520], [520, 500, 480, 460]
    for x in xs:
        c.line(x, ys[0], x, ys[-1])
    for yy in ys:
        c.line(xs[0], yy, xs[-1], yy)
    for r, row in enumerate([["年度", "2024A", "2025F"], ["營收", " 1,200 ", "1,500"], ["EPS", "10.5", "12.3"]]):
        for k, v in enumerate(row):
            c.drawString(xs[k] + 4, ys[r] - 14, v)
    c.rect(40, 520, 110, 70)
    c.lines([(45, 530, 70, 560), (70, 560, 95, 545), (95, 545, 120, 580), (120, 580, 145, 570)])
    c.setFont("Helvetica", 6)
    c.drawString(42, 583, "600")
    c.drawString(42, 523, "500")
    c.setFont("MSung-Light", 10)
    c.drawString(220, 80, "結論:維持買進評等。")
    c.setFont("MSung-Light", 9.5)
    c.drawString(40, 62, "資料來源:公司資料、凱基預估;本報告內容僅供參考,投資人應審慎評估風險與報酬,不得作為投資決策之唯一依據。")
    c.setFont("MSung-Light", 7)
    c.drawString(40, 40, "請參閱最後一頁之免責聲明")
    c.showPage()
    c.setFont("MSung-Light", 14)
    c.drawString(40, 800, "財務預測")
    c.setFont("MSung-Light", 9)
    for x0, blocks in ((40, [["Income Statement (NT$ mn), year end Dec", ("", "2024A", "2025F"), ("營收", "1,200", "1,500"), ("營業費用", "", "120"), ("__blank__", "", ""), ("毛利", "400", "520"), ("淨利", "150", "200")],
                             ["Valuation", ("本益比(x)", "15.2", "12.8"), ("本淨比(x)", "2.1", "1.9")],
                             ["資產負債表", ("", "2024A", "2025F"), ("總資產", "3,000", "3,400"), ("總負債", "1,000", "1,100"), ("股東權益", "2,000", "2,300")]]),
                       (320, [["現金流量表", ("", "2024A", "2025F"), ("營業現金流", "300", "350"), ("資本支出", "-100", "-120"), ("自由現金流", "200", "230")],
                              ["P&L Summary", ("", "Dec-24", "YoY"), ("Net sales", "186,189", "10%"), ("EBIT", "12,300", "18%"), ("Net profit", "9,800", "22%")],
                              ["Balance Sheet Summary", ("__gap__", "", ""), ("Total assets", "300,100", "8%"), ("Total debt", "90,500", "-2%"), ("Equity", "150,200", "5%")],
                              ["Figure 2. Poya: Monthly SSSG Trend", ("2024 Jan", "5%", "3%"), ("2024 Feb", "4%", "2%"), ("2024 Mar", "6%", "1%")]])):
        y = 740
        for blk in blocks:
            c.drawString(x0, y, blk[0])
            y -= 14
            for lab, a, b in blk[1:]:
                if lab == "__gap__":
                    y -= 50                                            # 與上一張表隔開 > 4 行高(不併回 · 要靠承接)
                    continue
                for xx, v in ((x0, lab), (x0 + 130, a), (x0 + 190, b)):
                    if v and lab != "__blank__":
                        c.drawString(xx, y, v)
                y -= 14
    c.save()


def selftest() -> int:
    import shutil
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="eng397-"))
    saved = os.environ.get("VIA_SPILL_DIR")
    try:
        os.environ["VIA_SPILL_DIR"] = str(td / "spill")
        indir = td / "測試樣本報告"
        indir.mkdir()
        _fixture_pdf(indir / "KGI_3653 健策_20260915.pdf")
        import pdfplumber
        with pdfplumber.open(str(indir / "KGI_3653 健策_20260915.pdf")) as pdf:
            page = pdf.pages[0]
            seg = segment(page)
            import pypdfium2 as pdfium
            tp = pdfium.PdfDocument(str(indir / "KGI_3653 健策_20260915.pdf"))[0].get_textpage()
            for z in seg["zones"]:
                z.update(extract_zone(page, z, None, tp))
                recategorize(z)
                repair_zone(z)
        maj = Counter(z["major"] for z in seg["zones"])
        minors = {z["minor"] for z in seg["zones"] if z["major"] == "L"}
        chk("① 切割:頁首 T · 左資訊欄 L(依 x 最大空隙)· 本文 M · 頁尾 B · 共 %d 區 · %s" % (len(seg["zones"]), dict(maj)), seg["side"] == "L" and all(maj[k] for k in "TLMB"))
        info = [x["text"] for z in seg["zones"] if z["major"] == "L" for x in z["records"]]
        chk("② 資訊區依類別細切:評等 / 目標價 RT · 股價資料 SD · 分析師 AN → %s · 一行一筆(不串句)%s" % (sorted(minors), info[:3]),
            {"RT", "SD", "AN"} <= minors and "評等:買進" in info and "目標價:NT$650" in info)
        body = [x for z in seg["zones"] if z["major"] == "M" and z["kind"] == "文" for x in z["records"]]
        txt = [(x["kind"], x["text"]) for x in body]
        chk("③ 斷句銜接:標題「投資重點」「展望」各一筆 · 跨行句子接起來到句號 · 一句一筆 · 不接到標題 → %s" % txt[:4],
            ("標題", "投資重點") in txt and ("標題", "展望") in txt and any(k == "句" and t.startswith("公司第三季營收年增") and t.endswith("優於預期。") for k, t in txt)
            and ("句", "毛利率提升至 38%。") in txt and not any(k == "標題" and "。" in t for k, t in txt))
        tb = next((z for z in seg["zones"] if z["kind"] == "表"), None)
        chk("④ 表格獨立一區 · 儲存格 TRIM → %s" % (tb["rows"][:2] if tb else None), tb is not None and tb["rows"][0] == ["年度", "2024A", "2025F"] and tb["rows"][1] == ["營收", "1,200", "1,500"])
        engs = {z.get("engine", "") for z in seg["zones"]}
        chk("⑤ 不亂碼:私用區 / (cid:N) 剔除 · 全形轉半形 · 中文字間去空格 · 字型編碼錯(合法但錯的字)用常用字比例抓到 → 換 pypdfium2 · 本頁引擎 %s" % sorted(engs),
            clean("營\ue000收 １２３ 億 元(cid:98)") == "營收 123 億元" and garbled("營(cid:98)") > 0.5 and quality("兟岱貥砦煙菪緯崌")[1] < 0.6 and quality("公司第三季營收年增")[1] >= 0.9
            and any("pypdfium2" in e for e in engs))
        figz = [z for z in seg["zones"] if z["minor"] == "FG"]
        ltxt = " ".join(x["text"] for z in seg["zones"] if z["major"] == "L" for x in z.get("records") or [])
        chk("⑥ 資訊區多圖多文再切:側欄股價走勢圖(向量)獨立一區 %s · 圖內座標字(500 / 600)不混進文字區" % [z["id"] for z in figz],
            any(z["major"] == "L" for z in figz) and "600" not in ltxt and "500" not in ltxt)
        (indir / "6488_note.txt").write_bytes("環球晶 6488\n".encode("cp950"))
        (indir / "6488_note.docx").write_bytes(b"PK")
        o = run(indir, td / "rep")
        js = json.loads((td / "rep" / "p1view" / "P1VIEW_latest.json").read_text(encoding="utf-8"))[0]
        fin = [pg for pg in js["pages"] if pg["fin"]]
        fz = fin[0]["zones"] if fin else []
        tbs = [(z["major"], z["rows"]) for z in fz if z["minor"] == "TB"]
        allrows = [r for _, rows in tbs for r in rows]
        chk("⑦ Word / TXT 暫不處理(略過 %s)· 財報頁偵測到第 %s 頁 · 先左右對切(%s)· 每半再依上下切不同表 · 財報表 %d 張(左 %d / 右 %d)" % (
            o["skipped"], [pg["pno"] for pg in fin], fin[0]["side"] if fin else None, len(tbs), sum(1 for m, _ in tbs if m == "FL"), sum(1 for m, _ in tbs if m == "FR")),
            o["skipped"] == {"TXT": 1, "WORD": 1} and o["n"] == 1 and [pg["pno"] for pg in fin] == [2] and fin[0]["side"] == "LR"
            and sum(1 for m, _ in tbs if m == "FL") == 2 and sum(1 for m, _ in tbs if m == "FR") == 3)
        chk("⑧ 表頭期間欄 x 對齊 · 缺格留空不位移(營業費用只有 2025F)· 緊貼兩表靠表名錨點切開 · 錯碼逐格換 pypdfium2 → %s" % allrows[:4],
            ["營收", "1,200", "1,500"] in allrows and ["營業費用", "", "120"] in allrows and ["資本支出", "-100", "-120"] in allrows and ["股東權益", "2,000", "2,300"] in allrows
            and ["", "2024A", "2025F"] in allrows)
        p1z = js["pages"][0]["zones"]
        btxt = " ".join(x["text"] for z in p1z if z["major"] == "M" for x in z.get("records") or [])
        ftxt = " ".join(x["text"] for z in p1z if z["major"] == "B" for x in z.get("records") or [])
        p1side = js["pages"][0]["side"]
        alltxt = " ".join(x["text"] for z in p1z for x in z.get("records") or [])
        chk("⑫ 底部有橫跨全頁的正常字級行(9.5pt)→ 側欄照樣找到(%s)· 這行另成全幅區不漏字" % p1side, p1side == "L" and "資料來源" in alltxt and any(z["minor_zh"] == "本文(全幅)" for z in p1z))
        nd = td / "nofin"
        nd.mkdir()
        from reportlab.pdfgen import canvas as _cv
        from reportlab.pdfbase import pdfmetrics as _pm
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont as _UF
        _pm.registerFont(_UF("MSung-Light"))
        cv = _cv.Canvas(str(nd / "2330_memo.pdf"), pagesize=(595, 842))
        cv.setFont("MSung-Light", 10)
        cv.drawString(60, 700, "公司第三季營收年增,優於預期。")
        cv.save()
        o2 = run(nd, td / "rep2")
        j2 = json.loads((td / "rep2" / "p1view" / "P1VIEW_latest.json").read_text(encoding="utf-8"))[0]
        chk("⑬ 燈號依擷取品質:模擬報告(側欄 + 評等 + 財報表對齊)= %s · %s · 只有本文的報告 = %s · 原因 %s · 版型 %s" % (js["lamp"], js["layout"], j2["lamp"], j2["reasons"], j2["layout"]),
            js["lamp"] == "GREEN" and js["layout"] == "側欄型(左)" and not js["reasons"] and j2["lamp"] == "YELLOW"
            and "沒找到財報頁" in j2["reasons"] and "首頁沒抓到評等 / 目標價" in j2["reasons"] and j2["layout"] == "單欄型" and o2["reasons"].get("沒找到財報頁") == 1)
        ltb = [z for z in fz if z["minor"] == "TB" and z["major"] == "FL"]
        chk("⑭ 表格內空白行不切表:損益表中間空一行 → 左半仍是 2 張表 · 毛利 / 淨利在同一張 · 期間欄對齊保留 → %s" % [len(z["rows"]) for z in ltb],
            len(ltb) == 2 and any(["營收", "1,200", "1,500"] in z["rows"] and ["淨利", "150", "200"] in z["rows"] for z in ltb))
        per_ok = all(_PERIOD.match(x) for x in ("112年", "113F", "25F", "26E", "FY2025E", "FY25", "2025年", "1H25", "2H26", "1Q25", "Q1 25", "12/2025", "2025/12")) and not any(_PERIOD.match(x) for x in ("1,500", "1500", "12.5", "NT$"))
        rt_rx = MINOR[0][2]
        rt_ok = all(re.search(rt_rx, x) for x in ("投資建議:增持", "Target Price NT$650", "PT 120", "區間操作", "合理股價 88", "Outperform", "加碼")) and not re.search(rt_rx, "營收年增 25%")
        chk("⑮ 期間表頭補民國年 / 兩位數年 / FY / 半年 / 季 / 月年(數字不誤判)· 評等目標價關鍵字擴充(一般句子不誤判)", per_ok and rt_ok)
        tz = [z for z in p1z if z["major"] == "T"]
        ttl = " ".join(x["text"] for z in tz if z["minor"] == "TT" for x in z.get("records") or [])
        chk("⑯ 真實圖回饋:直排浮水印不當側欄(側欄仍 L · 浮水印字不出現)· 整頁背景圖忽略(本文仍在)· 標題與同列右側 Overweight 分成兩區(RT %s)· 長英文表名仍切左右(%s)" % (
            any(z["minor"] == "RT" for z in tz), fin[0]["side"] if fin else None),
            p1side == "L" and "Watermark" not in alltxt and "投資重點" in btxt and not any(z["minor"] == "IMG" and (z["bbox"][2] - z["bbox"][0]) * (z["bbox"][3] - z["bbox"][1]) > 0.4 * 595 * 842 for z in p1z)
            and "Overweight" not in ttl and any(z["minor"] == "RT" and "Overweight" in " ".join(x["text"] for x in z.get("records") or []) for z in tz) and fin and fin[0]["side"] == "LR")
        ltb2 = [z for z in fz if z["minor"] == "TB" and z["major"] == "FL"]
        chk("⑰ 第 2 輪退步修正:Valuation 分節(沒自己的期間表頭)併回損益表 → 左半仍 2 張表且本益比列在損益表裡(期間欄對齊 %s)· 符號字型項目符號不算錯碼(錯碼區 %d)· CSV %d 列 · MD %d 行" % (
            all("期間欄" in z.get("engine", "") for z in ltb2), sum(1 for z in p1z if z.get("needs_ocr")), sum(1 for _ in (td / "rep" / "p1view" / "P1VIEW_records_latest.csv").open(encoding="utf-8-sig")) - 1,
            len((td / "rep" / "p1view" / "P1VIEW_latest.md").read_text(encoding="utf-8").splitlines())),
            len(ltb2) == 2 and any(["本益比(x)", "15.2", "12.8"] in z["rows"] and ["營收", "1,200", "1,500"] in z["rows"] for z in ltb2) and all("期間欄" in z.get("engine", "") for z in ltb2)
            and not any(z.get("needs_ocr") for z in p1z) and (td / "rep" / "p1view" / "P1VIEW_latest.md").exists() and "## 每份一行" in (td / "rep" / "p1view" / "P1VIEW_latest.md").read_text(encoding="utf-8"))
        cj = Path(__file__).resolve().parent / "contract" / "VRN_P1VIEW_RECORDS_CONTRACT_latest.json"
        chk("⑱ 契約自動寫出(JSON + MD · 欄位 %d)· OCR 排隊在持久位置 %s" % (len(json.loads(cj.read_text(encoding="utf-8"))["columns"]) if cj.exists() else 0, o["queue"].endswith("ocr_queue")),
            cj.exists() and cj.with_suffix(".md").exists() and o["queue"].endswith("ocr_queue") and len(json.loads(cj.read_text(encoding="utf-8"))["columns"]) == 16)
        fr = [z for z in fz if z["major"] == "FR"]
        pl = next((z for z in fr if z["minor"] == "TB" and any("Net sales" in r for r in z["rows"])), None)
        chk("⑲ 第 7 輪實證修正:圖說 / 座標軸區塊(Figure 2…)歸圖不算表(%s)· Dec-24 + YoY 表頭對齊(%s)· 第二行項目符號不算錯碼(錯碼區 %d)· 英文字留空格(Net sales)" % (
            any(z["minor"] == "FG" and "Figure" in " ".join(x["text"] for x in z.get("records") or []) for z in fr), bool(pl and "期間欄" in pl.get("engine", "")), sum(1 for z in p1z if z.get("needs_ocr"))),
            any(z["minor"] == "FG" and "Figure" in " ".join(x["text"] for x in z.get("records") or []) for z in fr) and not any(z["minor"] == "TB" and any("Figure" in c for r in z["rows"] for c in r) for z in fr)
            and pl is not None and "期間欄" in pl.get("engine", "") and ["Net sales", "186,189", "10%"] in pl["rows"] and not any(z.get("needs_ocr") for z in p1z))
        bs = next((z for z in fr if z["minor"] == "TB" and any("Total assets" in r for r in z["rows"])), None)
        chk("⑳ 第 10 輪實證:行首私用區字元(Wingdings 項目符號)不算錯碼(%.3f)· 沒自己表頭的 Balance Sheet Summary 承接上方 Dec-24 / YoY 表頭對齊(%s)" % (
            garbled("\uf0d8 Order outlook remains robust\n\uf0d8 Reaffirming our Buy"), (bs or {}).get("engine")),
            garbled("\uf0d8 Order outlook remains robust\n\uf0d8 Reaffirming our Buy") == 0 and bs is not None and "承接上方表頭" in bs.get("engine", "") and ["Total assets", "300,100", "8%"] in bs["rows"])
        W = lambda t, x0, x1, top=0, size=8: {"text": t, "x0": x0, "x1": x1, "top": top, "bottom": top + 8, "size": size}  # noqa: E731
        hdr = [W("2024", 100, 120), W("2025F", 140, 165), W("2026F", 180, 205), W("2024", 320, 340), W("2025F", 360, 385), W("2026F", 400, 425)]
        row = [W("現金", 20, 40, 12), W("7,907", 100, 122, 12), W("8,132", 140, 162, 12), W("8,739", 180, 202, 12), W("折舊", 230, 250, 12), W("673", 320, 335, 12), W("781", 360, 375, 12), W("889", 400, 415, 12)]
        pr = _period_rows([{"ws": hdr, "text": "", "size": 8}, {"ws": row, "text": "", "size": 8}])
        ptxt = [[c for c, _ in r] for r in pr]
        chk("⑫ 並排兩表拆開:同列兩段 2024/2025F/2026F → 左表 現金 7,907…·〔右表〕· 折舊 673… → %s" % ptxt, ["現金", "7,907", "8,132", "8,739"] in ptxt and ["〔右表〕"] in ptxt and ["折舊", "673", "781", "889"] in ptxt)
        sf = _split_fused([{"ws": [W("25Q3(F) 25Q4(F) 2025(F)", 300, 390)], "text": "", "size": 8}])[0]["ws"]
        chk("⑬ 黏在一起的期間表頭格拆成 3 欄 · x 依字數分 → %s" % [w["text"] for w in sf], [w["text"] for w in sf] == ["25Q3(F)", "25Q4(F)", "2025(F)"] and sf[0]["x1"] < sf[1]["x0"] < sf[2]["x0"])
        chk("⑭ 短亂碼「堢n,`U」判錯碼(>0)· 正常「國泰期貨」不判 · 刻度表(列只有數字)= 圖 · 有科目的表不是圖", garbled("堢n,`U") > 0 and garbled("國泰期貨國泰證券子公司") == 0 and _chart_like([["23.0x", "200"], ["21.0x"], ["19.0x", "150"], ["17.0x"], ["100", "13.0x"]]) and not _chart_like([["營業收入", "1"], ["營業成本", "2"], ["毛利", "3"], ["費用", "4"]]))
        nf = _no_num_lines([W("稅後盈餘成長率", 20, 60, 700, 7), W("27.92", 100, 120, 700, 7), W("0.34", 140, 160, 700, 7), W("本資料僅供參考", 20, 80, 712, 7)])
        chk("⑮ 底部含 ≥2 個數字的列不算頁尾(留給表)· 免責文字仍是頁尾 → %s" % [w["text"] for w in nf], [w["text"] for w in nf] == ["本資料僅供參考"])
        chk("㉑ 第 20 輪實證:繁體短文字不誤送 OCR(IC 封裝/測試 ‧ 台灣 · 呂旻旂/紡織、製鞋、伺服器 · 訪談報告 慧洋-KY 俄烏停火有助散裝業復甦)· 罕用字串仍判低(龘靐齉爩鱻麤 常用比 %.2f)· 換引擎仍用嚴格表(笙東 / 痦費 照樣觸發換碼)" % quality("龘靐齉爩鱻麤", 6, True)[1],
            quality("IC 封裝/測試 ‧ 台灣 半導體封裝測試廠", 6, True)[1] >= 0.4 and quality("呂旻旂/紡織、製鞋、伺服器", 6, True)[1] >= 0.4 and quality("訪談報告 慧洋-KY 俄烏停火有助散裝業復甦", 6, True)[1] >= 0.4 and quality("龘靐齉爩鱻麤", 6, True)[1] < 0.4)
        jt = judge({"pages": [{"zones": [], "side": None}]})
        chk("㉒ 首頁無文字層(影像 PDF · 0 區)→ 紅 · 原因「首頁無文字層 → OCR 排隊」→ %s %s" % (jt["lamp"], jt["reasons"]), jt["lamp"] == "RED" and jt["reasons"][0] == "首頁無文字層 → OCR 排隊")
        jp = [["NT$ in millions", "FY24A", "FY25E", "FY26E", "FY27E"], ["Revenue", "2,894,308", "3,618,960", "4,118,088", "4,634,792"], ["Adj. EBIT", "1,322,053", "1,710,940", "1,942,311", "2,175,018"], ["Adj. EPS", "45.24", "58.44", "65.11", "73.35"]]
        cl = [["Revenue", "241,901", "360,541", "879,897", "144", "1,055,970"], ["Taxation", "(3,400)", "(6,054)", "(12,586)", "(13,299)", "(14,830)"], ["Net profit", "12,044", "22,776", "45,316", "99", "49,730"]]
        zr = {"minor": "TB", "engine": "pdfplumber", "rows": [["Total Equity", "1 20,843", "1 40,813"], ["Residual Income", "( 457)", "1 ,154"], ["P/B (x)", "4 .2", "8 .0 24.0"], ["Units", "20,843 22,995", ""]], "records": []}
        repair_zone(zr)
        zt = {"minor": "TX", "rows": [], "records": [{"text": "E li t e M a t e r i a l ( 2383 . T W )"}, {"text": "債券 E T F 周報"}, {"text": "預期未來六個月股價漲輻超過+30%"}, {"text": "中國僖託證券投顧"}, {"text": "to be in a good shape"}, {"text": "2 0 2 6 / 9 / 7"}]}
        repair_zone(zt)
        tx = [x["text"] for x in zt["records"]]
        chk("㉓ v0113 擷取後修復:數字接回 %s · 字母間距 %s · 錯字 %s · 一般英文不動 · 原文留 raw · JP 年度表欄位整齊 %s · CLST 無表頭不算 %s" % (zr["rows"][0][1:], tx[:2], tx[2][-8:], tidy_period(jp), tidy_period(cl)),
            zr["rows"][0][1:] == ["120,843", "140,813"] and zr["rows"][1][1:] == ["(457)", "1,154"] and zr["rows"][2][1:] == ["4.2", "8.0 24.0"] and zr["rows"][3][1] == "20,843 22,995"
            and zr["raw"]["0,1"] == "1 20,843" and "Elite Material" in tx[0] and "2383.TW" in tx[0] and tx[1] == "債券 ETF 周報" and "漲幅" in tx[2] and tx[3] == "中國信託證券投顧"
            and tx[4] == "to be in a good shape" and tx[5].startswith("2026") and tidy_period(jp) and not tidy_period(cl) and tidy_period(cl, 5))
        chk("⑪ 頁尾 = 底部且小字:底部正常字級的本文「結論:維持買進評等。」留在本文 · 7pt 免責才是頁尾", "結論:維持買進評等。" in btxt and "免責" in ftxt and "結論" not in ftxt)
        htm = (td / "rep" / "p1view" / "P1VIEW_latest.html").read_text(encoding="utf-8")
        chk("⑨ HTML U/I:每份第一頁 + 財報頁各一張切割圖 · 各區擷取還原 · %d 檔 · %d 區" % (o["n"], o["zones"]), "img/001_p1.png" in htm and "img/001_p2.png" in htm and "P2·FL·" in htm and "P1·L·" in htm)
    finally:
        if saved is None:
            os.environ.pop("VIA_SPILL_DIR", None)
        else:
            os.environ["VIA_SPILL_DIR"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111]", "[VIA:ACCEL-BRIDGE:v0111]" in me)
    print("[計] %s v0113 自測 %d/%d · %s" % (ENGINE_ID, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:2]:
        raise SystemExit(selftest())
    print(json.dumps(run(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\測試樣本報告"), HERE / "_p1view_out"), ensure_ascii=False, default=str)[:1500])

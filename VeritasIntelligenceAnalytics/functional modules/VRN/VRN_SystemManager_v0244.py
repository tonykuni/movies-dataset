#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 SystemManager v0244 — 兩線合併薄尾(v0243 的兄弟版 · 前版 = 另一線 v0242;共同祖先 v0231)。

v0244 相對 v0243(第 49 輪實證):① _acc_parallel 也重新綁定 → 分片子行程真的跑本版(v0243 漏綁 → 子行程跑 v0231 的雙讀 · 命中舊快取 · 慧洋 ⑦ 假退步)② ⑦ 退步訊息附細節與快取旗標 ③ 冪等閘:另一線版本 PermissionError 時退回 v0231 版 ④ 輸出冊退步只算既有類別(年度數據 / 四重點 / TITLE / 基本欄)· 另一線新規則「四點原文證據未齊」列為口徑變嚴不算退步 ⑤ 完成判定管理器名稱寫回本版。


本線(ActivateVRN-2 v0123 線)相對 v0231 的淨增量,以另一線的薄尾機制接回,不遮蔽另一線 v0232~v0242 的任何函式:
① 標準化層:期間去前後綴(年 YYYY · 月 YYYY-MM · 日 YYYY-MM-DD · 季 YYYY-Qn)· 數值化(VALUE_NUM / UNIT)· EPS_KIND(兩列取低者為稀釋)→ 年度數據冊 (_out_books 包裝 · 先呼叫另一線的 _out_books 再加欄 · 三本冊重寫)
② ⑦ 基本資料雙讀修正:Email 跨行接回 · 字型插字(88)6 / To%mmy)· 完整電話(tel_a / tel_b)· 分析師非姓名停用詞 · 網域 Daiwa / CLSA / 中信 (_acc_basic / _bi_read / _bi_norm · 驗收與分片重新綁定到本版)
③ 基本資料冊 TEL 填號碼並統一格式 +國碼-區碼-號碼(原誤填狀態說明)
④ VRN2_Regex 冊 · 擷取還原風險目錄 55 項 (vrn2scope 寫入)· 補裝帳本網路錯誤 7 天不重試 (envcheck)
⑤ 本線 v0232 / v0240 已成功的治理項全部接回:⑦ 基本資料雙讀只准變好(上輪綠 → 本輪非綠 = 驗收退步 · 擋完成)· 輸出冊逐份完整度只准變好(VRN2_OutBook_latest.json · 退步印紅)· 驗收後各階段先印階段名
本版跳過本線的 v0232(全文)~v0240(全文)· 那些檔保留不刪 · 血緣登記 registry/VRN2_Lineage_Register.json。
"""
from __future__ import annotations

# ===== 1. Parameters =====
TAG = "v0244"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0242.py"

import csv
import hashlib
import importlib.util
import itertools
import json
import os
import re
import sys
import types
from pathlib import Path

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0244", Path(__file__).with_name(PRIOR_NAME))
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in list(vars(PRIOR).items()):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


def _rebind(function):
    result = types.FunctionType(function.__code__, globals(), function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__, result.__doc__ = function.__kwdefaults__, function.__doc__
    return result


# ===== 2. 本線淨增量(另一線沒碰的定義 · 原樣搬入) =====
_MON = {m: i + 1 for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"))}


_RX_DEFAULT = {
    "book": "VRN2_Regex", "owner": "VRN-2", "rule": "向其他子系統取用(VRN TW_TICKER_REGEX v2 等)· 不衝突則只增不減 · 本冊為 VRN-2 現役",
    "TW_TICKER": r"(?<!\d)([1-9]\d{3})(?!\d)",
    "TW_YFINANCE": r"(?<!\d)([1-9]\d{3})\.(TW|TWO)\b",
    "TW_BLOOMBERG": r"(?<!\d)([1-9]\d{3})\s+TT\b",
    "YEAR": r"^(?:FY|CY|年度)?[\s\-]?(?:(19|20)?(\d{2}))\s*(?:年度?)?\s*[\(（]?(?:[AEFPaefp]|實際|預估|Act|Est|F)?[\)）]?$|^(?:1[0-2])/(\d{2})[AEFPaefp]?$|^(1[01]\d)\s*年[AEFP]?$",
    "MONTH": r"^(?:(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-/']?(\d{2,4}))$|^(\d{4})[\-/\.](\d{1,2})$|^(\d{2,4})\s*年\s*(\d{1,2})\s*月$",
    "QUARTER": r"^([1-4])Q[\s\-]?(\d{2,4})\s*[\(（]?[AEFPaefp]?[\)）]?$|^(\d{2,4})Q([1-4])\s*[\(（]?[AEFPaefp]?[\)）]?$|^Q([1-4])[\s\-']?(\d{2,4})$|^(\d{2,4})\s*年?\s*第?([1-4])\s*季$",
    "DATE": r"^(\d{4})[\-/\.](\d{1,2})[\-/\.](\d{1,2})$|^(\d{4})(\d{2})(\d{2})$|^(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})$|^(1[01]\d)[\-/\.](\d{1,2})[\-/\.](\d{1,2})$|^(\d{2,4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日$",
    "NUMBER": r"^[\(（]?[\-−+]?[\d,]+(?:\.\d+)?[\)）]?\s*(%|x|倍|bps|ppts?)?$",
}


_RISK_CATALOG = [
    # (編號, 因素, 識別方法, 修復 / 處理方案, 狀態)
    (1, "文字層亂碼(字型 CMap 錯 · 合法但錯的字)", "常用字比例低於嚴格表 · 已知錯碼字對(笙東 / 痦費)", "整頁換 pypdfium2 → 逐格換 → 仍錯則切 PNG 進 OCR 佇列", "已實作 v0105+"),
    (2, "私用區字元 / (cid:N) / Wingdings 項目符號", "Unicode 私用區 · (cid:\\d+) regex · 行首符號", "剔除;行首項目符號不算錯碼", "已實作"),
    (3, "全形 / 半形混用", "全形數字 / 標點", "一律轉半形;數值化層再轉一次", "已實作"),
    (4, "中文字間多餘空格", "CJK 字間 \\s", "去空格;英文字保留空格", "已實作"),
    (5, "英文字母間距被拆(E l i t e)", "連續單字母序列", "併回單字;專有名詞保護", "已實作 v0113"),
    (6, "數字斷裂跨格(「1,021,435 1」+「,163,923」)", "右格以逗號開頭 · 左格尾端孤立 1~3 位數", "搬回右格 + 同列量級檢查(0.2x~5x)不過不接", "已實作 v0118 · v0128 加合理性"),
    (7, "數字碎片同格(「4 11,810」)", "格內「數字 空格 千分位數」", "首尾相接且合千分位才併", "已實作 v0119"),
    (8, "字詞層碎片(x 座標相接但不同字詞)", "字詞框首尾相接", "字詞層接合", "已實作 v0119"),
    (9, "負數以括號表示 (1,234)", "括號包數字", "數值化層轉負數", "已實作 v0240"),
    (10, "百分比 / 倍數 / 基點後綴(% x 倍 bps ppts)", "數字後綴", "數值化層拆成 VALUE_NUM + UNIT", "已實作 v0240"),
    (11, "字型在字中插雜字(To%mmy · 88)6 · 賴%偉中)", "字母 / 數字間夾 % )", "去除後再比對(⑦ 雙讀 · 摘要器)", "已實作 v0232 / v0110"),
    (12, "期間表頭格黏在一起(25Q3(F)25Q4(F))", "一格含多個期間", "依字數拆欄", "已實作"),
    (13, "期間表頭格式多樣(FY23 / FY-23 / 12/23 / 2023A / 112年)", "YEAR regex", "標準化 YYYY(無前後綴)", "已實作 v0240"),
    (14, "月份格式多樣(Apr-12 / 2024/04 / 113年4月)", "MONTH regex", "標準化 YYYY-MM", "已實作 v0240"),
    (15, "日期格式多樣(2025/8/19 · 19 May 2026 · 114/12/02 · 20250819)", "DATE regex", "標準化 YYYY-MM-DD", "已實作 v0240"),
    (16, "季度格式多樣(1Q25A · 25Q3(F) · Q1 2025 · 2025 年第 1 季)", "QUARTER regex", "標準化 YYYY-Qn", "已實作 v0240"),
    (17, "表格左上角空格", "表頭 row[0] 空", "補「ITEM」", "已實作 v0128"),
    (18, "並排兩表黏成一張(年度 + 季度)", "表頭中段出現非期間文字", "從該欄切開 · 各自對齊", "已實作 v0122"),
    (19, "接續表沒有自己的表頭(Balance Sheet Summary / 現金流量)", "無期間表頭 · 欄數 = 上方表", "承接上方表頭", "已實作 v0113 / v0122"),
    (20, "表內空白列被當成分表", "空白列夾在同表", "不切表", "已實作"),
    (21, "兩張表緊貼無間距", "表名錨點", "以表名切開", "已實作"),
    (22, "缺格造成欄位位移(只有一年有值)", "x 座標對齊", "缺格留空不位移", "已實作"),
    (23, "圖內座標字混入文字區", "圖區判定 · 刻度數字", "不收進文字 · 補擷取只收區外字", "已實作 v0116"),
    (24, "只有數字列的刻度表被當表", "列全為數字", "判為圖", "已實作"),
    (25, "頁面外框被當成一張表(JP-2330 首頁)", "整頁大框只抽出少數格", "不當表", "已實作 v0115"),
    (26, "頁尾免責混入本文", "小字級 + 底部", "歸頁尾 / DS", "已實作"),
    (27, "底部正常字級列被當頁尾", "字級 ≥ 本文", "留在本文;≥2 個數字的列留給表", "已實作"),
    (28, "直排浮水印 / 整頁背景圖干擾版型", "旋轉字 · 整頁圖", "忽略;側欄照常判定", "已實作 v0116"),
    (29, "側欄填色資訊框被當成圖(GS Forecast)", "向量框 · 無點陣圖 · 線條 ≤1 · 含期間表或評等", "文字救回 + 表格重建", "已實作 v0123"),
    (30, "影像 PDF 無文字層", "首頁 0 區", "OCR 階梯 200 → 325 DPI(隔離環境)", "已實作 v0119"),
    (31, "OCR 信心不足 / 字數太少", "信心 <0.85 或 <40 字", "升 325 DPI + 前處理;仍不足進佇列", "已實作"),
    (32, "OCR 英文空格遺失", "字元框間距", "行高正規化間距 + 字典斷詞", "已實作 橋 v0100"),
    (33, "OCR 數字誤讀(0→o · 1→l · 8→3)", "表內算術(成長率 = 前後年相除 · PE × EPS 各年一致)", "交叉驗證不過判黃;自動修正待實檔", "驗證已實作 v0225 · 自動修正規劃"),
    (34, "OCR 表格欄位錯位", "數字右緣 vs 期間欄右緣", "右緣對齊重建", "已實作 v0120"),
    (35, "OCR 科目符號錯((96)→(%) · {TWD]→(TWD))", "符號對照表", "科目修正表", "已實作"),
    (36, "多欄版面本文順序錯亂", "版型判定(頁首 / 側欄 / 本文 / 頁尾)", "依 x 最大空隙切欄", "已實作"),
    (37, "斷句跨行 / 跨欄", "行尾無句號", "接到句號 · 不接到標題", "已實作"),
    (38, "標題被券商橫幅取代(Sachs I Research)", "橫幅樣式", "排除 + 往下找粗體大字", "已實作 v0107 / v0108"),
    (39, "標題跨兩行只取半句", "同區塊同字級相鄰行", "接續", "已實作 v0109"),
    (40, "標題含股票代號被排除", "代號後接冒號", "允許", "已實作 v0111"),
    (41, "免責 / 圖例 / 表格列被當成重點", "免責樣式 · (左軸)(右軸) · 數字佔比 ≥45%", "過濾;重點只從前段選", "已實作 v0110 / v0112"),
    (42, "逐行 PDF 區塊太短無候選句(凱基)", "原路徑候選句 <4", "接回段落後援", "已實作 v0110"),
    (43, "Email 跨行 / 截斷 / 授權浮水印", "daiwacm-⏎cathay · mmy.lai ⊂ tommy.lai · exclusive use of", "接回 / 截斷判一致 / 排除", "已實作 v0226 ~ v0229"),
    (44, "電話誤判(圖表日期軸 04 25-07)", "嚴格格式(國碼 / 區碼)", "只收合格式", "已實作 v0226"),
    (45, "分析師誤抓(法說 / 封裝 / 研究中心)", "停用詞 · 斜線 / 逗號證照前", "優先姓名位置", "已實作 v0229"),
    (46, "目標價候選衝突(12-month TSR 的 12 · 圖例 240)", "多個不同值", "數字後接 -month 不算 · 優先帶幣別", "已實作 v0113"),
    (47, "目標價不在首頁(GS 第 4 頁資訊框)", "首頁無候選", "其他頁結構化資訊框後援", "已實作 v0111"),
    (48, "EPS 基本 / 稀釋混淆", "同表兩列 EPS", "兩列取低者為稀釋 · 單列視為稀釋(標註 EPS_KIND)", "已實作 v0240(標註)· 對照歷史待 VDF"),
    (49, "單位混用(百萬 / 千 / 元 / 美元)", "表頭 / 表名單位字", "解析單位寫入 UNIT 欄", "規劃(需實檔驗證)"),
    (50, "同一科目跨表數值不一致(報告本身)", "損益表 vs 比率表重算", "判黃「原文跨表不一致」· 人工確認", "已實作 v0216"),
    (51, "年份被誤判為股票代號(2026 / 2330)", "TW_TICKER 不排除年份 · 另以 .TW / TT / 年字消歧", "消歧層", "已實作"),
    (52, "資產 ≠ 負債 + 權益(少數股權 / 口徑)", "恆等式 + 合理性(負值 / 權益 <1%)", "判黃 · 含少數股權也算平", "已實作 v0226 / v0229"),
    (53, "檔名含括號 / 全形 / 多重代號", "檔名切連續中英數段", "代號 · 日期 · 券商 · 公司名分段比對", "已實作"),
    (54, "同檔內容被 OneDrive / 編輯器改動(雜湊不同)", "落地時雜湊比對", "不覆蓋 · 出新版 · 回報", "已實作 ②"),
    (55, "非個股報告混入個股流程", "範圍冊 + 檔名排除", "只擷取個股報告", "已實作 v0227"),
]


def _yy(y: str) -> str:
    y = str(y)
    if len(y) == 4:
        return y
    if len(y) == 3:                                                        # 民國 112 → 2023
        return str(int(y) + 1911)
    return ("20" if int(y) < 70 else "19") + y


def _norm_period(s: str) -> tuple:
    """v0240 期間標準化:回 (kind, std) · 年 YYYY · 月 YYYY-MM · 日 YYYY-MM-DD · 季 YYYY-Qn · 其他 (None, 原字串)。無前後綴(FY / A / E / F / 括號 / 年)。"""
    t = (s or "").strip().replace("／", "/").replace("－", "-").replace("　", " ")
    t = re.sub(r"\s+", " ", t)
    if not t:
        return None, s
    m = re.match(_RX_DEFAULT["DATE"], t, re.I)
    if m:
        g = [x for x in m.groups() if x]
        if m.group(1):
            return "date", "%s-%02d-%02d" % (g[0], int(g[1]), int(g[2]))
        if m.group(4):
            return "date", "%s-%s-%s" % (g[0], g[1], g[2])
        if m.group(7):
            return "date", "%s-%02d-%02d" % (g[2], _MON[g[1][:3].lower()], int(g[0]))
        if m.group(10):
            return "date", "%s-%02d-%02d" % (_yy(g[0]), int(g[1]), int(g[2]))
        return "date", "%s-%02d-%02d" % (_yy(g[0]), int(g[1]), int(g[2]))
    m = re.match(_RX_DEFAULT["QUARTER"], t, re.I)
    if m:
        g = m.groups()
        if g[0]:
            q, y = g[0], g[1]
        elif g[2]:
            y, q = g[2], g[3]
        elif g[4]:
            q, y = g[4], g[5]
        else:
            y, q = g[6], g[7]
        return "quarter", "%s-Q%s" % (_yy(y), q)
    m = re.match(_RX_DEFAULT["MONTH"], t, re.I)
    if m:
        g = m.groups()
        if g[0]:
            if _MON[g[0][:3].lower()] == 12:                                  # Dec-24 = 會計年度(同 12/24)→ 年
                return "year", _yy(g[1])
            return "month", "%s-%02d" % (_yy(g[1]), _MON[g[0][:3].lower()])
        if g[2]:
            return "month", "%s-%02d" % (g[2], int(g[3]))
        return "month", "%s-%02d" % (_yy(g[4]), int(g[5]))
    m = re.match(_RX_DEFAULT["YEAR"], t, re.I)
    if m:
        g = m.groups()                                                     # (世紀, 兩位年, 12/yy 的 yy, 民國年)
        if g[2]:                                                           # 12/23 → 2023(會計年度末)
            return "year", _yy(g[2])
        if g[3]:                                                           # 112年 → 2023
            return "year", _yy(g[3])
        if g[1]:
            return "year", (g[0] + g[1]) if g[0] else _yy(g[1])
    return None, s


def _norm_num(s: str) -> tuple:
    """v0240 數值化:回 (value: float|None, unit: str)。去空格 / 千分位 / 全形 · 括號負數 · −號 · % x 倍 bps ppts 為單位 · n.m. / - / — → None。"""
    t = (s or "").strip().translate(str.maketrans("０１２３４５６７８９，．（）－", "0123456789,.()-"))
    t = t.replace("−", "-").replace("–", "-").replace(" ", "")
    if not t or re.fullmatch(r"(?i)-+|—|n\.?[am]\.?|na|nm|n/a", t):
        return None, ""
    m = re.fullmatch(r"(\()?([\-+]?)([\d,]+(?:\.\d+)?)(\))?(%|x|倍|bps|ppts?)?", t, re.I)
    if not m:
        return None, ""
    neg = bool(m.group(1) and m.group(4)) or m.group(2) == "-"
    try:
        v = float(m.group(3).replace(",", ""))
    except ValueError:
        return None, ""
    return (-v if neg else v), (m.group(5) or "")


def _out_tel(x: str) -> str:
    """v0232 電話統一格式 +國碼-區碼-號碼(台灣 886 / 香港 852 / 日本 81 / 新加坡 65 / 中國 86;其他照原數字)。"""
    d = re.sub(r"\D", "", x or "")
    for cc, area in (("886", 1), ("852", 0), ("81", 1), ("65", 0), ("86", 2)):
        if d.startswith(cc) and len(d) - len(cc) >= 8:
            r_ = d[len(cc):]
            if cc == "886" and r_.startswith("9"):
                return "+886-%s-%s-%s" % (r_[:3], r_[3:6], r_[6:])
            a_, n_ = r_[:area], r_[area:]
            body = "%s-%s" % (n_[:-4], n_[-4:]) if len(n_) >= 7 else n_
            return "+%s-%s%s" % (cc, (a_ + "-") if a_ else "", body)
    return ("+" + d) if d else x


def _write_books_if_missing(ssd: Path, L: list) -> None:
    """v0240 Regex 冊 / 風險目錄:不存在才寫(只增不減)。"""
    rx = ssd / "VRN2_Regex_v0100.json"
    if not rx.exists():
        rx.write_text(json.dumps(_RX_DEFAULT, ensure_ascii=False, indent=1), encoding="utf-8")
        L.append("[計] VRN-2 Regex 冊 → SSOT/VRN2_Regex_v0100.json(TW_TICKER / YFINANCE / BLOOMBERG · YEAR / MONTH / QUARTER / DATE / NUMBER · 去前後綴)")
    rc = ssd / "VRN2_RestoreRiskCatalog_v0100.json"
    if not rc.exists():
        rows = [{"id": i, "factor": f, "detect": d, "fix": x, "status": st} for i, f, d, x, st in _RISK_CATALOG]
        rc.write_text(json.dumps({"book": "VRN2_RestoreRiskCatalog", "owner": "VRN-2", "count": len(rows), "items": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
        L.append("[計] VRN-2 擷取還原風險目錄 → SSOT/VRN2_RestoreRiskCatalog_v0100.json(%d 項 · 已實作 %d · 規劃 %d)" % (len(rows), sum(1 for r in rows if r["status"].startswith("已")), sum(1 for r in rows if not r["status"].startswith("已"))))


def _bi_norm(t: str) -> str:
    """v0226 字距拆斷修復:「D errick.Yang@」「To mmy.Lai@」→ 接回(只接 1~2 個字母的大寫開頭碎片)· 字母間怪字元 % 去掉 · 授權使用者浮水印(For the exclusive use of x@y)不算。"""
    t = re.sub(r"(?<=[A-Za-z])%(?=[a-z])", "", t or "")
    t = re.sub(r"(?<=\d)[)%](?=\d)", "", t)                                   # v0232 數字間字型插字(88)6 → 886)
    t = re.sub(r"(?<=[\w.@])-\s*\n\s*(?=[\w.])", "-", t)                     # v0229 Email 跨行(daiwacm-⏎cathay)接回
    t = re.sub(r"@\s*\n\s*", "@", t)
    t = re.sub(r"(?<=[\w])\.\s*\n\s*(?=(?:com|tw|hk|co|jp|net)\b)", ".", t)
    t = re.sub(r"(?i)exclusive use of\s+\S+@\S+", " ", t)
    return re.sub(r"\b([A-Z][a-z]?) ([a-z]{2,}[\w.]*@)", r"\1\2", t)


def _bi_read(text: str) -> dict:
    t = _bi_norm(text)
    em = sorted({e.lower().rstrip(".") for e in _BI_EMAIL.findall(t)})
    tel = sorted({re.sub(r"\D", "", x)[-8:] for x in _BI_TEL.findall(t) if len(re.sub(r"\D", "", x)) >= 8})
    full = sorted({re.sub(r"\s+", " ", x).strip() for x in _BI_TEL.findall(t) if len(re.sub(r"\D", "", x)) >= 8})   # v0232 完整號碼(輸出冊用)
    return {"email": em, "tel": tel, "tel_full": full}


def _acc_basic(r: dict, pdf) -> tuple:
    """v0226 ⑦ 基本資料雙讀(學 VRN-1 的雙讀法 · VRN-2 自己實作):讀法 A = ENG397 首頁區塊 · 讀法 B = pypdfium2 獨立讀首頁原文 ·
    Email / 電話逐欄 VERIFIED / CONFLICT / SINGLE / MISSING · 券商由 Email 網域反查並與檔名比對 · 最多黃(提醒)。"""
    zs = [z for pg in r.get("pages") or [] if pg.get("pno") == 1 for z in pg.get("zones", [])]
    ta = "\n".join([x.get("text", "") for z in zs for x in (z.get("records") or []) if isinstance(x, dict)] + [" ".join(c for c in row if c) for z in zs for row in (z.get("rows") or [])])
    tb = _acc_pdfium_text(Path(pdf), [1]).get(1, "")
    A, B = _bi_read(ta), _bi_read(tb)
    em = _bi_cmp(A["email"], B["email"])
    tel = _bi_cmp(A["tel"], B["tel"])
    fb = next((b for rx, b in _BI_FILE if re.search(rx, r.get("file", ""), re.I)), None)
    dom = sorted({_BI_DOMAIN.get(e.split("@")[1]) for e in (A["email"] or B["email"]) if _BI_DOMAIN.get(e.split("@")[1])})
    if dom and fb:
        br = ("VERIFIED", "%s(網域 = 檔名)" % dom[0]) if fb in dom else ("CONFLICT", "網域 %s ≠ 檔名 %s" % ("、".join(dom), fb))
    else:
        br = ("SINGLE", "只有%s" % ("網域 " + "、".join(dom) if dom else "檔名 " + (fb or "—")))
    names = [" ".join(w.capitalize() for w in re.split(r"[._]", e.split("@")[0]) if w.isalpha()) for e in (A["email"] or B["email"])][:3]
    st = {"email": em, "tel": tel, "broker": br, "analysts": names, "email_a": A["email"], "email_b": B["email"], "tel_a": A["tel_full"], "tel_b": B["tel_full"]}
    if em[0] == "MISSING" and tel[0] == "MISSING":                       # 首頁沒印分析師聯絡資料(兆豐 / MQ)= 不適用(VRN-1 的 NOT_PRINTED)
        return ("GRAY", "首頁未印分析師聯絡資料 · 券商 %s %s" % (br[0], br[1])), dict(email=em, tel=tel, broker=br, analysts=[], email_a=A["email"], email_b=B["email"])
    rank = {"VERIFIED": 0, "MISSING": 0, "SINGLE": 1, "CONFLICT": 2}
    worst = max((em[0], tel[0], br[0] if br[0] != "SINGLE" else "VERIFIED"), key=lambda x: rank[x])
    lamp = "GREEN" if worst == "VERIFIED" or worst == "MISSING" else "YELLOW"
    note = "Email %s %s · 電話 %s %s · 券商 %s %s%s" % (em[0], em[1], tel[0], tel[1], br[0], br[1], (" · 分析師 " + "、".join(names)) if names else "")
    return (lamp, note), st


def envcheck(install: bool = False) -> tuple:
    """AST 掃 import(加速器 + 網路工具 = 必裝;VRN 尾版:頂層必裝 · try 內選裝)→ 缺的用本環境 pip 補(numpy 釘 >=1.24,<2.0 · 隔離套件不裝只列灰)。"""
    import ast
    import importlib.util
    import subprocess
    import sys
    import tempfile
    sup = next((p / "supportive modules" for p in [HERE] + list(HERE.parents) if (p / "supportive modules").is_dir()), None)
    must_files, opt_files = [], []
    if sup:
        acc = sorted(list(sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")), key=lambda x: int(re.search(r"_v(\d{4})", x.name).group(1)))
        must_files += acc[-1:] + list(sup.glob("VeritasAegisNexus_v1652.py"))[:1] + list(sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]
    fams = {}
    for p in HERE.rglob("*.py"):
        if _AF_SKIP.search(str(p)):
            continue
        m = re.search(r"^(.*)_v(\d{3,4})$", p.stem)
        if m and ((str(p.parent), m.group(1)) not in fams or int(m.group(2)) > fams[(str(p.parent), m.group(1))][1]):
            fams[(str(p.parent), m.group(1))] = (p, int(m.group(2)))
    opt_files = [p for p, _ in fams.values()]
    local = {p.stem for p in HERE.rglob("*.py")} | ({p.stem for p in sup.rglob("*.py")} if sup else set()) | {p.name for p in HERE.iterdir() if p.is_dir()}
    std = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    need = {}

    def scan(f, must):
        try:
            t = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError, ValueError):
            return
        tries = {id(n) for x in ast.walk(t) if isinstance(x, ast.Try) for b in x.body for n in ast.walk(b)}
        for n in ast.walk(t):
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module] if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module else [])
            for nm in names:
                top = nm.split(".")[0]
                if not top or top in std or top in local or top.startswith(("_", "VRN_", "VIA_", "Veritas", "CGC_", "VDF_", "VCGC")):
                    continue
                hard = must or id(n) not in tries
                d = need.setdefault(top, {"must": False, "hard": False, "by": set()})
                d["must"] |= must
                d["hard"] |= hard
                d["by"].add(f.name)
    for f in must_files:
        scan(f, True)
    for f in opt_files:
        scan(f, False)
    rows = []
    for top, d in sorted(need.items()):
        ok = importlib.util.find_spec(top) is not None
        pip = _PIPNAME.get(top, top.replace("_", "-"))
        lamp = "GREEN" if ok else ("GRAY" if _ISOLATED.match(top) else ("RED" if d["must"] or d["hard"] else "YELLOW"))
        rows.append({"module": top, "pip": pip, "lamp": lamp, "must": d["must"], "hard": d["hard"], "by": sorted(d["by"])[:3], "installed": ok, "action": ""})
    todo = [r for r in rows if r["lamp"] in ("RED", "YELLOW")]
    L = ["[計] 環境檢查(envcheck · %s)· 掃 加速器 / 網路工具 %d 檔 + VRN-2 尾版 %d 檔 · 第三方套件 %d · 已裝 %d · 缺(必裝)%d · 缺(選裝)%d · 隔離不裝 %d" % (
        sys.executable, len(must_files), len(opt_files), len(rows), sum(1 for r in rows if r["installed"]), sum(1 for r in rows if r["lamp"] == "RED"),
        sum(1 for r in rows if r["lamp"] == "YELLOW"), sum(1 for r in rows if r["lamp"] == "GRAY"))]
    if install and todo:
        cf = Path(tempfile.mkdtemp(prefix="pipc-")) / "constraints.txt"
        cf.write_text("numpy>=1.24,<2.0\n", encoding="utf-8")
        import time as _time
        lp = HERE / "registry" / "VRN_PipLedger.json"                         # v0231 補裝帳本(不重試必敗的套件)
        try:
            led = json.loads(lp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            led = {}
        for r in todo:
            x = led.get(r["pip"]) or {}
            if x.get("kind") == "no_dist":
                r["action"] = "不補裝 · PyPI 上沒有此套件(VIA 內部模組或名稱不同 · 首次判定 %s)" % x.get("day", "")
                if r["lamp"] == "YELLOW":
                    r["lamp"] = "GRAY"
                L.append("[計] 略過 %s(%s)· %s" % (r["pip"], "必裝" if r["lamp"] == "RED" else "選裝", r["action"]))
                continue
            if x.get("kind") == "network" and _time.time() - float(x.get("ts", 0)) < 7 * 86400 and os.environ.get("VIA_VRN2_PIP_RETRY") != "1":
                r["action"] = "不補裝 · 上次網路錯誤(7 天內不重試 · VIA_VRN2_PIP_RETRY=1 可強制)"
                L.append("[計] 略過 %s · %s" % (r["pip"], r["action"]))
                continue
            try:
                p = subprocess.run([sys.executable, "-m", "pip", "install", "--no-input", "--disable-pip-version-check", "-c", str(cf), r["pip"]], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
                importlib.invalidate_caches()
                r["installed"] = importlib.util.find_spec(r["module"]) is not None
                err = (p.stderr or "") + (p.stdout or "")
                r["action"] = "已補裝" if r["installed"] else "補裝失敗 rc %d · %s" % (p.returncode, ((p.stderr or "").strip().splitlines() or [""])[-1][:90])
                if r["installed"]:
                    led.pop(r["pip"], None)
                elif re.search(r"No matching distribution|Could not find a version", err):
                    led[r["pip"]] = {"kind": "no_dist", "ts": _time.time(), "day": _time.strftime("%Y-%m-%d")}
                elif re.search(r"IncompleteRead|Connection|Timeout|timed out|SSL|Temporary failure|Max retries", err, re.I):
                    led[r["pip"]] = {"kind": "network", "ts": _time.time(), "day": _time.strftime("%Y-%m-%d")}
            except Exception as exc:  # noqa: BLE001
                r["action"] = "補裝失敗 · %s" % type(exc).__name__
            if r["installed"]:
                r["lamp"] = "GREEN"
            try:
                lp.parent.mkdir(parents=True, exist_ok=True)
                lp.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
            except OSError:
                pass
            L.append("[計] 補裝 %s(%s)· %s" % (r["pip"], "必裝" if r["must"] else ("頂層" if r["hard"] else "選裝"), r["action"]))
    for r in rows:
        if r["lamp"] in ("RED", "YELLOW") and not (install and r["action"]):
            L.append("[計] 缺 %s %s(pip %s · 用於 %s)" % ("必裝" if r["lamp"] == "RED" else "選裝", r["module"], r["pip"], " · ".join(r["by"])))
        elif r["lamp"] == "GRAY":
            L.append("[計] 隔離套件 %s 不裝進本環境(LL#21–24 · 經橋呼叫)" % r["module"])
    try:
        rep = Path(_resolve("_rep")()).parent / "vrn2"
        rep.mkdir(parents=True, exist_ok=True)
        (rep / "VRN2_Env_latest.json").write_text(json.dumps({"python": sys.executable, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    bad = [r for r in rows if r["lamp"] == "RED"]
    return (1 if bad else 0), L


def vrn2scope(args: list) -> tuple:
    """v0227 VRN-2 獨立設定冊 + 範圍聚焦:VRN2_SSOT(來源夾 · 範圍 = 個股報告 · 交付項)· 來源夾的 PDF 扣掉上輪判定非個股 / 檔名明確非個股 → 同步到 VIA_Reports\\vrn2\\scope_in · 設定冊 input_dir 指向它(只增不減:出新版)。"""
    import shutil
    L = []
    ssd = HERE / "SSOT"
    ssd.mkdir(parents=True, exist_ok=True)
    v2 = Path(_resolve("_rep")()).parent / "vrn2"
    scope_dir = v2 / "scope_in"
    cur_in = Path(_resolve("input_dir")())
    books = sorted(ssd.glob("VRN2_SSOT_v[0-9][0-9][0-9][0-9].json"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    ss = json.loads(books[-1].read_text(encoding="utf-8")) if books else {}
    src = Path(ss.get("source_dir") or (str(cur_in) if cur_in.resolve() != scope_dir.resolve() else r"C:\測試樣本報告"))
    new = dict(ss, system="VRN-2", owner="VRN-2 SystemManager", independent=True, source_dir=str(src), scope="stock_only", scope_dir=str(scope_dir),
               deliverables=["FILENAME", "首頁(本文 / 資訊區)", "年度財報頁(年度財報及數據分解)", "100% 還原", "一標題四重點", "輸出驗證", "HTML U/I"],
               borrow_rule="參數可向其他系統取用(VDF 上市櫃清單 / 股價庫等)· 不衝突即可 · 不照抄程式",
               funnel=dict(_FUNNEL_DEFAULT, **(ss.get("funnel") or {})))
    if new != ss:
        nv = (int(re.search(r"_v(\d{4})", books[-1].name).group(1)) + 1) if books else 100
        (ssd / ("VRN2_SSOT_v%04d.json" % nv)).write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        L.append("[計] VRN-2 獨立設定冊 → SSOT/VRN2_SSOT_v%04d.json(來源 %s · 範圍 個股報告)" % (nv, src))
    _write_books_if_missing(ssd, L)                                         # v0240 Regex 冊 / 風險目錄
    prev = {}
    try:
        prev = json.loads((v2 / "VRN2_Scope_latest.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    nons = set(prev.get("non_stock") or [])
    if not src.is_dir():
        return 1, L + ["[RED] VRN-2 範圍 · 來源夾不在 %s" % src]
    allf = sorted([p for p in src.rglob("*") if p.is_file()], key=lambda p: p.name)
    pdfs = [p for p in allf if p.suffix.lower() == ".pdf"]
    keep = [p for p in pdfs if p.name not in nons and not _SK_EXCL.search(p.name)]
    scope_dir.mkdir(parents=True, exist_ok=True)
    names = {p.name for p in keep}
    cp = 0
    for p in keep:
        d = scope_dir / p.name
        if not d.exists() or d.stat().st_size != p.stat().st_size or int(d.stat().st_mtime) != int(p.stat().st_mtime):
            shutil.copy2(str(p), str(d))
            cp += 1
    rm = 0
    for d in scope_dir.iterdir():
        if d.is_file() and d.name not in names:
            d.unlink()
            rm += 1
    cfgs = sorted(ssd.glob("VRN_Config_v[0-9][0-9][0-9][0-9].json"), key=lambda p: int(re.search(r"_v(\d{4})", p.name).group(1)))
    cfg = json.loads(cfgs[-1].read_text(encoding="utf-8")) if cfgs else {}
    if Path(cfg.get("input_dir") or "").resolve() != scope_dir.resolve() if cfg.get("input_dir") else True:
        nv = (int(re.search(r"_v(\d{4})", cfgs[-1].name).group(1)) + 1) if cfgs else 1000
        (ssd / ("VRN_Config_v%04d.json" % nv)).write_text(json.dumps(dict(cfg, input_dir=str(scope_dir), vrn2_scope="stock_only", vrn2_source_dir=str(src)), ensure_ascii=False, indent=1), encoding="utf-8")
        L.append("[計] VRN-2 設定冊 → SSOT/VRN_Config_v%04d.json(input_dir = 個股範圍夾)" % nv)
    L.append("[計] VRN-2 範圍(只擷取個股報告)· 來源 %s · 檔 %d(PDF %d · 非 PDF %d 不在範圍)· 個股範圍 %d · 排除非個股 %d(上輪判定 %d · 檔名 %d)· 同步 新增 / 更新 %d · 移除 %d" % (
        src, len(allf), len(pdfs), len(allf) - len(pdfs), len(keep), len(pdfs) - len(keep), len([p for p in pdfs if p.name in nons]),
        len([p for p in pdfs if p.name not in nons and _SK_EXCL.search(p.name)]), cp, rm))
    return 0, L


_OUT_NOTNAME = {"法說", "封裝", "研究中心", "研究部", "伺服器", "半導體", "電子", "金融", "傳產", "航運"}


_OUT_RATING = re.compile(r"(?i)\b(Overweight|Underweight|Equal-?weight|Outperform|Underperform|Market Perform|Neutral|Buy|Sell|Hold|Reduce|Accumulate)\b|(強力買進|逢低買進|增加持股|降低持股|區間操作|逢高賣出|買進|持有|中立|賣出|未評等)")


# ===== 3. 驗收重新綁定(分片子行程跑本檔 → _acc_basic / _bi_* 用本版) =====
_acc_shard_main = _rebind(PRIOR._acc_shard_main)
_acc_parallel = _rebind(PRIOR._acc_parallel)                               # v0244 分片由此啟動 → 子行程 = 本檔
_acc_one = _rebind(PRIOR._acc_one)
_acc_one_core = _rebind(PRIOR._acc_one_core)
_base_acceptance = _rebind(PRIOR.PRIOR.acceptance if hasattr(PRIOR, "PRIOR") else PRIOR.acceptance)   # v0231 層的 acceptance(非另一線包裝)→ 分片以本檔啟動
_MY_SIG = hashlib.sha1("|".join(x for x in (
    __import__("inspect").getsource(_acc_basic), __import__("inspect").getsource(_bi_read), __import__("inspect").getsource(_bi_norm))).encode("utf-8")).hexdigest()[:16]


def _acc_sig() -> str:
    """v0243 驗收指紋 = 前鏈指紋 + 本版雙讀修正指紋(改到任一邊都讓驗收快取失效)。"""
    return hashlib.sha1((PRIOR._acc_sig() + _MY_SIG).encode("utf-8")).hexdigest()[:16]


def acceptance(res, indir, v2, *args, **kwargs):
    """v0243:以本版綁定的基底 acceptance 跑(分片 = 本檔)· 再套另一線 v0242 的「原文逐字摘要還原」· 再加 ⑦ 雙讀只准變好(本線 v0232)。"""
    try:
        prev7 = {x["file"]: (x.get("c7") or ["GRAY"])[0] for x in json.loads((Path(v2) / "VRN2_Acceptance_latest.json").read_text(encoding="utf-8")).get("files", [])}
    except Exception:  # noqa: BLE001
        prev7 = {}
    result = _base_acceptance(res, indir, v2, *args, **kwargs)
    try:
        out, reg, lines = result[0], result[1], result[2]
        for e in out:
            now = (e.get("c7") or ["GRAY"])[0]
            if prev7.get(e.get("file")) == "GREEN" and now in ("YELLOW", "RED"):
                reg.append(e.get("file"))
                lines.append("[RED] 驗收退步 · %s · ⑦ 基本資料雙讀(上輪綠 → %s)· %s%s" % (str(e.get("file"))[:40], now, str((e.get("c7") or ["", ""])[1])[:160], " · 來自快取" if e.get("_cache") else " · 本輪重算"))
    except Exception:  # noqa: BLE001
        pass
    try:
        _, engine_name = _acc_eng062()
        for entry in result[0]:
            pdf = Path(indir) / entry["file"]
            if not pdf.is_file():
                continue
            digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
            cache = Path(v2) / "summary" / (digest[:12] + "_" + engine_name.replace(".py", "") + ".json")
            if cache.is_file():
                summary = json.loads(cache.read_text(encoding="utf-8"))
                if summary.get("summary_mode") == "SOURCE_VERBATIM" and summary.get("source_pdf_sha256") == digest:
                    entry["summary"] = summary
    except Exception:  # noqa: BLE001
        pass
    return result


# ===== 4. 輸出冊包裝(另一線的 _out_books 之後加標準化欄位 · TEL 修正 · 三本冊重寫) =====
def _rewrite_book(od: Path, name: str, rows: list) -> None:
    (od / ("VRN2_%s_latest.json" % name)).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    flat = [{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in x.items()} for x in rows]
    keys = list(dict.fromkeys(k for x in flat for k in x))
    with (od / ("VRN2_%s_latest.csv" % name)).open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys or ["EMPTY"])
        w.writeheader()
        w.writerows(flat)
    try:
        import pandas as pd  # noqa: WPS433
        pd.DataFrame(flat).to_parquet(od / ("VRN2_%s_latest.parquet" % name), index=False)
    except Exception:  # noqa: BLE001
        pass


def _out_books(res, acc, st, v2):
    print("  [計] 階段 · 輸出冊(基本資料 / 年度數據 / 一標題四重點)", flush=True)
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)
    try:                                                                   # 本線 v0232 輸出冊逐份完整度只准變好
        _MINE = ("年度數據", "四重點", "TITLE", "REPORT_DATE", "TICKER", "BROKER")
        def _mine(g):
            return any(k in str(g).split(":", 1)[-1] for k in _MINE)
        gapf = {str(g).split(":", 1)[0] for g in gaps if _mine(g)}            # v0244 只算既有類別
        newcat = [str(g) for g in gaps if not _mine(g)]
        if newcat:
            print("  [計] 輸出冊口徑變嚴(另一線規則 · 不算退步)· %d 份 · 例 %s" % (len(newcat), newcat[0][:70]), flush=True)
        prevob = {}
        try:
            prevob = json.loads((Path(v2) / "VRN2_OutBook_latest.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
        obreg = sorted(f for f in (prevob.get("complete") or []) if f[:28] in gapf)
        (Path(v2) / "VRN2_OutBook_latest.json").write_text(json.dumps({"complete": sorted(b["FILENAME"] for b in basic if b.get("FILENAME", "")[:28] not in gapf), "gaps": [str(g) for g in gaps]}, ensure_ascii=False, indent=1), encoding="utf-8")
        for f in obreg:
            print("[RED] 輸出冊退步 · %s · 上輪齊全 → 本輪 %s" % (f[:40], next((str(g) for g in gaps if str(g).startswith(f[:28])), "缺項")), flush=True)
    except Exception:  # noqa: BLE001
        pass
    by_file = {e.get("file"): e for e in acc or []}
    for row in basic:
        bi = (by_file.get(row.get("FILENAME")) or {}).get("basic") or {}
        tels = bi.get("tel_a") or bi.get("tel_b") or []
        if tels or "一致" in str(row.get("TEL", "")) or str(row.get("TEL", "")).startswith(("MISSING", "只有")):
            row["TEL"] = "、".join(dict.fromkeys(_out_tel(x) for x in tels))   # v0232 TEL 填號碼(原誤填狀態說明)· 統一格式
    for x in fin:
        if not isinstance(x, dict):
            continue
        pk, ps = _norm_period(str(x.get("PERIOD", "") or ""))
        vn, un = _norm_num(str(x.get("VALUE", "") or ""))
        x.setdefault("PERIOD_STD", ps if pk else "")
        x.setdefault("PERIOD_KIND", pk or "")
        x.setdefault("VALUE_NUM", vn)
        x.setdefault("UNIT", un)
    eps = [x for x in fin if isinstance(x, dict) and re.search(r"(?i)^EPS\b|每股盈餘|每股稅後", str(x.get("ITEM", "")))]
    key = lambda x: (x.get("FILENAME", ""), x.get("TABLE", ""), x.get("PERIOD_STD") or x.get("PERIOD", ""))
    for _k, grp in itertools.groupby(sorted(eps, key=key), key=key):
        grp = [g for g in grp if g.get("VALUE_NUM") is not None]
        if not grp:
            continue
        lo = min(grp, key=lambda g: g["VALUE_NUM"])
        for g in grp:
            g["EPS_KIND"] = "diluted" if (g is lo or len(grp) == 1 or re.search(r"(?i)dilut|稀釋", g["ITEM"])) and not re.search(r"(?i)basic|基本", g["ITEM"]) else "basic"
    od = Path(v2) / "output"
    od.mkdir(parents=True, exist_ok=True)
    for name, rows in (("BasicInfo", basic), ("FinancialData", fin), ("Summary", summ)):
        try:
            _rewrite_book(od, name, rows)
        except Exception:  # noqa: BLE001
            pass
    return basic, fin, summ, gaps, made


_idem_base = _rebind(PRIOR.PRIOR._idem_check if hasattr(PRIOR, "PRIOR") else PRIOR._idem_check)   # v0231 版(使用者機器已成功)


def _idem_check(*args, **kwargs):
    print("  [計] 階段 · 冪等閘(重跑 3 份 · 不吃快取)", flush=True)
    try:
        r = PRIOR._idem_check(*args, **kwargs)
        if isinstance(r, tuple) and r and r[0] == "YELLOW" and "Error" in str(r[1:]):
            raise RuntimeError(str(r[1:])[:80])
        return r
    except Exception as exc:  # noqa: BLE001
        print("  [計] 冪等閘(另一線版)%s → 退回本線版重跑" % type(exc).__name__, flush=True)
        return _idem_base(*args, **kwargs)


def completion(*args, **kwargs):
    print("  [計] 階段 · 完成判定 → 鎖定 / 備份 → U/I", flush=True)
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    except Exception:  # noqa: BLE001
        pass
    return result


# ===== 5. 主流程綁定(另一線 v0242 的 vrn2 包裝 + 原生流程都重綁到本版 · 內部呼叫 _out_books / acceptance 走本版) =====
_native_vrn2 = _rebind(PRIOR._native_vrn2)
vrn2 = _rebind(PRIOR.vrn2)
_success_register = _rebind(PRIOR._success_register)


# ===== 6. 自測 =====
def selftest() -> int:
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    np_ = [_norm_period(x)[1] for x in ("12/23", "FY-23", "FY23", "2023A", "112年", "Apr-12", "1Q25A", "25Q3(F)", "2025/8/19", "19 May 2026", "Dec-24", "Revenue")]
    chk("⓪ v0244 標準化 %s" % np_, np_ == ["2023", "2023", "2023", "2023", "2023", "2012-04", "2025-Q1", "2025-Q3", "2025-08-19", "2026-05-19", "2024", "Revenue"])
    nn = [_norm_num(x) for x in ("1,163,923", "(1,234)", "-0.5%", "12.5x", "n.m.")]
    chk("⓪ v0244 數值化 %s" % nn, nn == [(1163923.0, ""), (-1234.0, ""), (-0.5, "%"), (12.5, "x"), (None, "")])
    kp = _bi_read("賴偉中\n88)6 2 2181 8710\nTo%mmy.Lai@kgi.com")
    chk("⓪ v0244 凱基插字 電話 %s · Email %s · 完整 %s" % (kp["tel"], kp["email"], kp.get("tel_full")), kp["tel"] == ["21818710"] and kp["email"] == ["tommy.lai@kgi.com"] and bool(kp.get("tel_full")))
    chk("⓪ v0244 電話格式 %s" % _out_tel("886-2) 2725-9618"), _out_tel("886-2) 2725-9618") == "+886-2-2725-9618")
    chk("⓪ v0244 綁定:acceptance / _acc_parallel / _acc_shard_main / _acc_one 全綁本版 %s · 指紋含本版 %s · 分片腳本 = 本檔 %s" % (
        all(f.__globals__ is globals() for f in (_base_acceptance, _acc_parallel, _acc_shard_main, _acc_one, _acc_one_core)), _acc_sig() != PRIOR._acc_sig(), _acc_parallel.__globals__.get("__file__") == __file__),
        all(f.__globals__ is globals() for f in (_base_acceptance, _acc_parallel, _acc_shard_main, _acc_one, _acc_one_core)) and _acc_sig() != PRIOR._acc_sig() and _acc_parallel.__globals__.get("__file__") == __file__)
    chk("⓪ v0244 vrn2 內部 _out_books / acceptance 走本版 %s %s" % (_native_vrn2.__globals__["_out_books"] is _out_books, _native_vrn2.__globals__["acceptance"] is acceptance),
        _native_vrn2.__globals__["_out_books"] is _out_books and _native_vrn2.__globals__["acceptance"] is acceptance)
    chk("⓪ v0244 風險目錄 %d 項 · Regex 冊 %d 鍵" % (len(_RISK_CATALOG), len(_RX_DEFAULT)), len(_RISK_CATALOG) >= 50 and "TW_TICKER" in _RX_DEFAULT)
    chk("⓪ v0244 接回本線治理項:vrn2 內部 _idem_check / completion 走本版(階段列印)%s %s · acceptance 包含 ⑦ 退步鎖 %s" % (
        _native_vrn2.__globals__["_idem_check"] is _idem_check, _native_vrn2.__globals__["completion"] is completion, "prev7" in __import__("inspect").getsource(acceptance)),
        _native_vrn2.__globals__["_idem_check"] is _idem_check and _native_vrn2.__globals__["completion"] is completion and "prev7" in __import__("inspect").getsource(acceptance))
    print("      ── 前版鏈(另一線 v0242)自測 ──")
    rc = 0
    try:
        rc = int(PRIOR.selftest() or 0)
    except Exception as exc:  # noqa: BLE001
        print("  [FAIL] 前版鏈自測 %s %s" % (type(exc).__name__, str(exc)[:120]))
        rc = 1
    chk("③ 前版鏈 %s 自測 rc %d" % (PRIOR_NAME.replace(".py", ""), rc), rc == 0)
    print("[計] VRN-2 SystemManager v0244(VRN_SystemManager_v0244.py)自測 %d/%d · %s" % (ok[0], ok[0] + ok[1], "PASS" if not ok[1] else "FAIL"))
    return 0 if not ok[1] else 1


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments[:1] == ["vrn2scope"]:
        rc_, ln_ = vrn2scope(arguments[1:])
        for x in ln_:
            print(x, flush=True)
        return rc_
    if arguments[:1] == ["envcheck"]:
        rc_, ln_ = envcheck("--install" in arguments)
        for x in ln_:
            print(x)
        return rc_
    if arguments[:1] == ["acc-shard"] and "--shard" in arguments:
        return _acc_shard_main(arguments[arguments.index("--shard") + 1])
    if arguments == ["--selftest"]:
        return selftest()
    if arguments[:1] == ["vrn2"]:
        code, lines = vrn2(arguments[1:])
        for line in lines:
            print(line, flush=True)
        return code
    return PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())

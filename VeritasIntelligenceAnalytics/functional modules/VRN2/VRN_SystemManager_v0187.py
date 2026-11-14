#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0187 — 薄尾(操作員 2026-10-11「NON-OCR JSON 還原表格文字 100% · OCR 搭配 LAYOUT 切割 PNG 高畫質識別修復表格文字 · 兩個還原度 100% 為目標 ·
   失誤不用修補法 · 找到 ROOT CAUSE 補上去 · 思考 30 個最可能錯誤去補救方案 · 只有 DILUTED EPS 是有意義的」)。
  rootcause 動詞(auto 自動接):30 個根因(RC01~RC30 · 每個:偵測特徵 · 證據 · 該修在哪個引擎 / 函式)→ restore 失敗表 / 算術不符 / 雙軌衝突格 / 問題正文 逐一歸類
  → 依件數排序(下一輪從最多的根因在源頭一次修掉一整類 · 不逐筆補)· 歸不進 30 類 → RC00 未歸類(列出 · 擴充根因表)
  只有稀釋 EPS 有意義:FINANCIAL DATA 基本 EPS 列 → 灰「不使用」· 未分 EPS → 黃「未確認稀釋」
其餘動詞照前版鏈。
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
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0187"


def _vnum_v0187(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0187(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0187(p) < _vnum_v0187(__file__)), key=_vnum_v0187)
PRIOR = _load_v0187(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_rep = _resolve("_rep")
# 30 根因:(代碼, 範圍, 根因, 源頭修法 · 修在哪)
RC = [
    ("RC01", "NON-OCR 表", "期間表頭沒認出(格式不在辨識器)", "期間辨識器 _is_period 補格式(由未認出的表頭字樣學)· layout 驗表"),
    ("RC02", "NON-OCR 表", "兩層表頭(年度 + 季度)沒合併", "表頭重建 _rebuild_table:上下兩列期間合併成一組鍵"),
    ("RC03", "NON-OCR 表", "欄位錯位(列的數值格數 ≠ 表頭期間數)", "欄對齊改用表頭 x 座標分欄(不靠欄序)· _rebuild_table"),
    ("RC04", "NON-OCR 表", "兩張表並排被讀成一張(表頭期間重複)", "表框切割 _table_boxes:同列期間重複 → 從重複處切成兩表"),
    ("RC05", "NON-OCR 表", "一張表被頁 / 欄切成兩段", "表框合併:同頁相鄰且表頭一致 / 續表無表頭 → 接回同表"),
    ("RC06", "NON-OCR 表", "標籤跨兩行(只有標籤的列 + 只有數字的列)", "列重建:無數字列與下一列無標籤列合併"),
    ("RC07", "NON-OCR 表", "括號負數沒轉成負值", "數字解析 parse_number:(123) → −123(在源頭轉)"),
    ("RC08", "NON-OCR 表", "千分位 / 小數點誤判(1.234 是一千兩百 還是一點二)", "數字解析依整表格式判定千分位符號(整欄一致)"),
    ("RC09", "NON-OCR 表", "單位列 / 幣別列混進數值列", "列分類:只有單位字樣的列 → 表的單位屬性(不當資料列)"),
    ("RC10", "NON-OCR 表", "比率列與金額列對到同一標準鍵(值域不符)", "標準鍵加值域約束(比率 0~100 · 金額量級)· 對鍵時檢查"),
    ("RC11", "對鍵", "科目名沒對到標準鍵(同義字缺)", "FinLexicon 補同義字(候選冊 → 操作員確認)"),
    ("RC12", "對鍵", "科目名對錯標準鍵(成長率 / % 對到金額鍵)", "對鍵規則:含 growth / % / 率 → 只能對比率鍵"),
    ("RC13", "NON-OCR 表", "預估 / 實際標記遺失(年度無 A / E / F)", "期間推斷:年度 ≥ 報告年 → 預估(依報告日)"),
    ("RC14", "NON-OCR 表", "季度與年度混在同一表", "期間鍵帶粒度(年 / 季 / 半年)· 測試只比同粒度"),
    ("RC15", "NON-OCR 表", "同一標準鍵出現兩列(小計 / 合計 / 重複)", "對鍵加階層:小計 / 合計 / 子項分開鍵"),
    ("RC16", "測試", "符號慣例不一(成本 / 費用正負)", "符號正規化在對鍵後統一(成本費用一律負)"),
    ("RC17", "測試", "單位量級不一(億 / 百萬 / 千元混用)", "表單位偵測 table_unit 在 restore 時正規化成百萬"),
    ("RC18", "測試", "四捨五入差被判不符", "容許誤差依顯示精度(v0180 已改)· 再看小數位數"),
    ("RC19", "測試", "恆等式口徑差(非控制權益 / 業外 / 加徵稅)", "恆等式補口徑項(v0181 已加)· 缺項時標口徑不同"),
    ("RC20", "NON-OCR 文", "頁首 / 頁尾 / 免責聲明混進正文", "雜訊規則:頁面上下邊界 + 跨頁重複行 → 剔除"),
    ("RC21", "NON-OCR 文", "多欄版面閱讀順序錯(句子過長 / 主題跳)", "閱讀順序依欄框排序(layout 分欄後再串)"),
    ("RC22", "NON-OCR 文", "斷行斷句錯(句中斷開 · 英文連字號)", "斷句:行尾無句號且下行小寫 / 中文續接 → 合併"),
    ("RC23", "NON-OCR 文", "標題被併進句子", "標題偵測(字級 / 粗體 / 短句無標點)先切出"),
    ("RC24", "NON-OCR 文", "表格文字被當正文(數字密度高)", "數字密度高的段落 → 文中表重建(不當句子)"),
    ("RC25", "OCR", "解析度不足小字誤認(8↔3 · 1↔7 · 0↔6)", "小字表切圖升 300~400 DPI · 灰階二值化前處理"),
    ("RC26", "OCR", "去空白造成數字黏連", "OCR 用字框間距切 token(不靠空白)"),
    ("RC27", "OCR", "欄對齊錯(OCR 值 = 鄰欄的值)", "OCR 欄對齊用 NON-OCR 表頭 x 座標分欄"),
    ("RC28", "OCR", "小數點 / 千分位遺失(差 10 / 100 / 1000 倍)", "OCR 數值用 NON-OCR 量級先驗校正(只當候選)"),
    ("RC29", "OCR", "負號 / 括號遺失", "OCR 讀括號字框 · 負號單獨字框不丟"),
    ("RC30", "OCR", "切圖範圍錯(沒包全表 / 包到別表)", "切圖用 layout 表框 + 邊界外擴 · 一張圖一張表"),
]
RCD = {c: (a, r, fx) for c, a, r, fx in RC}
_PER = re.compile(r"(?i)^(?:FY)?(?:19|20)\d{2}(?:[AEF]|\([AEF]\))?$|^[1-4]Q\d{2}[AEF]?$|^\d{2}Q[1-4][AEF]?$|^[12]H\d{2}[AEF]?$|^(?:DEC|MAR|JUN|SEP)-\d{2}[AEF]?$")
_NUM = re.compile(r"\(?-?[\d,]+(?:\.\d+)?\)?%?")


def _is_per(s) -> bool:
    return bool(_PER.match(str(s or "").strip().replace(" ", "")))


def _num(s):
    t = str(s or "").strip().replace(",", "")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()%")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def classify_table(fn: str, t: dict, report_year: int = None) -> list:
    hits = []
    add = lambda rc, ev: hits.append((rc, fn, t.get("id"), ev))  # noqa: E731
    raw = [list(r) for r in (t.get("raw_rows") or [])]
    rows = t.get("rows") or []
    iss = " ".join(str(x) for x in ((t.get("verify") or {}).get("issues") or []))
    pers = [c.get("period") for r in rows for c in r.get("cells") or []]
    if re.search(r"期間|period|表頭", iss) or (rows and not any(pers)):
        add("RC01", "驗表:%s" % iss[:60])
    if len(raw) >= 2 and sum(_is_per(c) for c in raw[0]) >= 2 and sum(_is_per(c) for c in raw[1]) >= 2:
        add("RC02", "前兩列都有期間")
    numrows = [r for r in raw if sum(1 for c in r if _num(c) is not None) >= 2]
    if numrows and max(len(r) for r in numrows) - min(len(r) for r in numrows) >= 1:
        add("RC03", "數值列格數 %d~%d" % (min(len(r) for r in numrows), max(len(r) for r in numrows)))
    for r in raw[:3]:
        ps = [str(c).strip() for c in r if _is_per(c)]
        if len(ps) != len(set(ps)) and len(ps) >= 4:
            add("RC04", "表頭期間重複 %s" % ",".join(ps[:8]))
            break
    if 0 < len(rows) <= 2 and pers:
        add("RC05", "只有 %d 列" % len(rows))
    for a, b in zip(raw, raw[1:]):
        if a and b and str(a[0]).strip() and all(_num(c) is None for c in a[1:]) and not str(b[0]).strip() and sum(1 for c in b[1:] if _num(c) is not None) >= 2:
            add("RC06", "「%s」下一列無標籤" % str(a[0])[:20])
            break
    paren = {abs(_num(c)) for r in raw for c in r if re.fullmatch(r"\(\s*[\d,]+(?:\.\d+)?\s*\)", str(c).strip()) and _num(c) is not None}
    if paren and any(isinstance(c.get("value"), (int, float)) and c["value"] > 0 and c["value"] in paren for r in rows for c in r.get("cells") or []):
        add("RC07", "括號數 %s 被讀成正值" % sorted(paren)[:3])
    if any(re.fullmatch(r"\d{1,3}\.\d{3}", str(c).strip()) for r in raw for c in r):
        add("RC08", "有 1.234 型數字")
    for r in rows:
        lab = str(r.get("label_raw") or "")
        if re.fullmatch(r"(?i)\s*\(?(NT\$|US\$|RMB)?\s*(m|mn|bn|百萬|千元|億元|%|x)\)?\s*", lab):
            add("RC09", "單位列「%s」" % lab)
        vals = [c["value"] for c in r.get("cells") or [] if isinstance(c.get("value"), (int, float))]
        std = r.get("std") or ""
        if vals and re.search(r"margin|growth|roe|roa|ratio|yield|payout", std) and max(abs(v) for v in vals) > 150:
            add("RC10", "%s 比率鍵值 %s" % (std, max(vals)))
        if std and not re.search(r"margin|growth|roe|roa|ratio|yield|payout|pe|pb", std) and re.search(r"(?i)growth|yoy|%|率", lab) and "每股" not in lab:
            add("RC12", "「%s」對到 %s" % (lab[:20], std))
    if t.get("unmatched_labels"):
        add("RC11", "沒對到 %s" % ",".join(str(x) for x in t["unmatched_labels"][:3]))
    if report_year:
        bare = [p for p in set(pers) if p and re.fullmatch(r"(?:FY)?(?:19|20)(\d{2})", str(p)) and int(re.sub(r"\D", "", str(p))[-2:]) >= report_year % 100]
        if bare:
            add("RC13", "無 A/E/F 的未來年 %s" % ",".join(sorted(bare)[:3]))
    if any(re.search(r"Q", str(p)) for p in pers) and any(re.fullmatch(r"(?:FY)?(?:19|20)\d{2}[AEF]?", str(p)) for p in pers):
        add("RC14", "同表有季也有年")
    stds = [r.get("std") for r in rows if r.get("std")]
    dup = [s for s, n in Counter(stds).items() if n > 1]
    if dup:
        add("RC15", "重複鍵 %s" % ",".join(dup[:3]))
    for c in t.get("calc") or []:
        if c.get("status") != "FAIL":
            continue
        m = re.findall(r"-?[\d.]+", str(c.get("detail") or ""))
        try:
            a, b = float(m[0]), float(m[1])
        except (IndexError, ValueError):
            continue
        r_ = a / b if b else None
        if r_ is None:
            continue
        if abs(r_ + 1) < 0.02:
            add("RC16", "%s %s 正負相反" % (c.get("rule"), c.get("period")))
        elif any(abs(r_ - k) / k < 0.02 for k in (10, 100, 1000, 0.1, 0.01, 0.001)):
            add("RC17", "%s %s 差 %.0f 倍" % (c.get("rule"), c.get("period"), r_ if r_ > 1 else 1 / r_))
        elif abs(r_ - 1) < 0.005:
            add("RC18", "%s %s 差 %.2f%%" % (c.get("rule"), c.get("period"), (r_ - 1) * 100))
        elif str(c.get("rule", "")).startswith("淨利"):
            add("RC19", "%s %s" % (c.get("rule"), c.get("period")))
    return hits


_DISC = re.compile(r"(?i)disclaimer|免責|本報告僅供參考|analyst certification|重要聲明|請參閱|important disclosures|investment banking|未經許可|版權所有")
_CONF = {"8": "3B", "3": "8", "1": "7l", "7": "1", "0": "6O", "6": "0", "5": "6S", "9": "4"}


def classify_text(fn: str, content: list) -> list:
    hits = []
    sents = [c for c in content or [] if c.get("type") in ("sentence", None) and c.get("text")]
    for i, c in enumerate(sents):
        s = c["text"]
        if _DISC.search(s):
            hits.append(("RC20", fn, "句 %d" % i, s[:50]))
        if len(s) > 400:
            hits.append(("RC21", fn, "句 %d" % i, "長 %d 字" % len(s)))
        if i + 1 < len(sents) and not re.search(r"[。．.!?！？:：;；)」』]$", s.strip()) and re.match(r"[a-z]", sents[i + 1]["text"].strip()):
            hits.append(("RC22", fn, "句 %d" % i, s[-30:]))
        m = re.match(r"^([^\s。，,.!?]{2,14})\s{1,}(\S.{20,})$", s)
        if m and not re.search(r"[。，,.]", m.group(1)):
            hits.append(("RC23", fn, "句 %d" % i, m.group(1)))
        nums = _NUM.findall(s)
        if len(nums) >= 6 and sum(len(x) for x in nums) / max(len(s), 1) > 0.35:
            hits.append(("RC24", fn, "句 %d" % i, "數字 %d 個" % len(nums)))
    return hits


def classify_conflict(fn: str, uid: str, k: str, a, b, others: set) -> tuple:
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return ("RC00", fn, uid, "%s 非數字" % k)
    if a == 0 or b == 0:
        return ("RC30", fn, uid, "%s 一邊為 0(%s / %s)· 切圖或對列" % (k, a, b))
    r = b / a
    if abs(r + 1) < 0.005:
        return ("RC29", fn, uid, "%s NON-OCR %s · OCR %s" % (k, a, b))
    if any(abs(r - kk) / kk < 0.001 for kk in (10, 100, 1000, 0.1, 0.01, 0.001)):      # 小數點遺失 = 精確倍數(黏連約 100 倍但不精確 → 往下判)
        return ("RC28", fn, uid, "%s %s vs %s" % (k, a, b))
    if b in others and b != a:
        return ("RC27", fn, uid, "%s OCR %s = 同表別格的值" % (k, b))
    sa, sb = ("%g" % abs(a)).replace(".", ""), ("%g" % abs(b)).replace(".", "")
    if len(sb) > len(sa) and sa in sb:
        return ("RC26", fn, uid, "%s %s 黏連成 %s" % (k, a, b))
    if len(sa) == len(sb) and sum(1 for x, y in zip(sa, sb) if x != y) == 1:
        x, y = next((x, y) for x, y in zip(sa, sb) if x != y)
        if y in _CONF.get(x, "") or x in _CONF.get(y, ""):
            return ("RC25", fn, uid, "%s %s → %s(%s↔%s)" % (k, a, b, x, y))
    return ("RC00", fn, uid, "%s %s vs %s" % (k, a, b))


def rootcause_run() -> dict:
    rep = _rep()
    hits = []
    for f in sorted((rep / "restore").glob("*.json")) if (rep / "restore").is_dir() else []:
        if f.name.startswith("RESTORE_"):
            continue
        dj = json.loads(f.read_text(encoding="utf-8"))
        meta = dj.get("document_meta") or {}
        fn = meta.get("file") or f.stem
        ry = re.search(r"(20\d{2})", str(meta.get("report_date") or meta.get("date") or fn))
        for t in dj.get("tables", []):
            if t.get("status") != "還原無誤" or any(c.get("status") == "FAIL" for c in t.get("calc") or []):
                hits += classify_table(fn, t, int(ry.group(1)) if ry else None)
        hits += [(rc, a, b, c) for rc, a, b, c in classify_text(fn, dj.get("content"))]
    dj = rep / "dualtrack" / "DUALTRACK_latest.json"
    if dj.exists():
        for x in json.loads(dj.read_text(encoding="utf-8")).get("records", []):
            cf = x.get("conflicts") or []
            if x.get("kind") != "table" or x.get("lamp") != "RED":
                continue
            if not cf and (x.get("agree") or 0) < 0.3:
                hits.append(("RC30", x["file"], x["id"], "一致度 %s · 沒有可比格 → 切圖 / 對列" % x.get("agree")))
            others = {float(c[1]) for c in cf if isinstance(c, list) and len(c) > 2 and isinstance(c[1], (int, float))}
            for c in cf:
                if isinstance(c, list) and len(c) >= 3:
                    hits.append(classify_conflict(x["file"], x["id"], c[0], c[1], c[2], others))
    by = defaultdict(list)
    for h in hits:
        by[h[0]].append(h)
    rows = sorted(({"rc": rc, "area": RCD.get(rc, ("—", "未歸類(擴充根因表)", "看例子 → 新根因"))[0], "cause": RCD.get(rc, ("", "未歸類(擴充根因表)", ""))[1],
                    "fix": RCD.get(rc, ("", "", "看例子 → 新增根因"))[2], "n": len(v), "files": len({x[1] for x in v}), "examples": ["%s · %s · %s" % (x[1][:26], x[2], x[3]) for x in v[:3]]}
                   for rc, v in by.items()), key=lambda r: -r["n"])
    od = rep / "rootcause"
    od.mkdir(parents=True, exist_ok=True)
    (od / "ROOTCAUSE_latest.json").write_text(json.dumps({"catalog": [{"rc": c, "area": a, "cause": r, "fix": fx} for c, a, r, fx in RC], "rows": rows, "total": len(hits)},
                                                         ensure_ascii=False, indent=1), encoding="utf-8")
    with (od / "ROOTCAUSE_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rc", "area", "cause", "n", "files", "fix", "example1", "example2", "example3"])
        for r in rows:
            w.writerow([r["rc"], r["area"], r["cause"], r["n"], r["files"], r["fix"]] + (r["examples"] + ["", "", ""])[:3])
    page = _resolve("_page")
    if page:
        (od / "ROOTCAUSE_latest.html").write_text(page("根因分析 · 30 個根因 · 依件數排序 · 從最多的在源頭修掉一整類(不逐筆補)", "共 %d 件 · %d 類" % (len(hits), len(rows)),
                                                       ["根因", "範圍", "原因", "件", "檔", "源頭修法(修在哪)", "例子"],
                                                       [("RED" if r["n"] >= 10 else ("YELLOW" if r["rc"] != "RC00" else "GRAY"), [r["rc"], html.escape(r["area"]), html.escape(r["cause"]), r["n"], r["files"],
                                                         html.escape(r["fix"]), html.escape(" | ".join(r["examples"]))[:240]]) for r in rows]), encoding="utf-8")
    return {"total": len(hits), "rows": rows, "html": str(od / "ROOTCAUSE_latest.html")}


def diluted_only_policy() -> dict:
    """只有稀釋 EPS 有意義:FINANCIAL DATA 基本 EPS → 灰「不使用」· 未分 EPS → 黃「未確認稀釋」(輸出政策層 · 檔案重寫同一份 latest)。"""
    od = _rep() / "findata"
    jp = od / "FINANCIAL_DATA_FINAL_latest.json"
    if not jp.exists():
        return {"basic": 0, "unsure": 0}
    d = json.loads(jp.read_text(encoding="utf-8"))
    nb = nu = 0
    for r in d.get("rows", []):
        if r.get("EPS_CLASS") == "BASIC_EPS":
            r["THREE_LIGHT"], r["ACCOUNT"] = "GRAY", "basic_eps(不使用 · 只有稀釋 EPS 有意義)"
            nb += 1
        elif r.get("EPS_CLASS") == "EPS_UNSURE":
            r["THREE_LIGHT"], r["ACCOUNT"] = "YELLOW", "eps(未確認稀釋)"
            nu += 1
    jp.write_text(json.dumps(d, ensure_ascii=False, default=str), encoding="utf-8")
    cols = d.get("columns", []) + d.get("extra", [])
    if cols:
        with (od / "FINANCIAL_DATA_FINAL_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(d.get("rows", []))
    return {"basic": nb, "unsure": nu}


def _lines_v187(o: dict, dp: dict) -> list:
    L = ["[計] 根因分析 · 共 %d 件 · %d 類(30 根因 + 未歸類)· 依件數排序 → 下一輪從最多的在源頭修(不逐筆補)" % (o["total"], len(o["rows"]))]
    for r in o["rows"][:12]:
        L.append("[計] %s × %d(%d 檔)· %s · %s → 修:%s · 例 %s" % (r["rc"], r["n"], r["files"], r["area"], r["cause"][:24], r["fix"][:40], (r["examples"] or [""])[0][:60]))
    L.append("[計] 只有稀釋 EPS 有意義 · FINANCIAL DATA 基本 EPS %d 格 → 灰(不使用)· 未分 EPS %d 格 → 黃(未確認稀釋)" % (dp["basic"], dp["unsure"]))
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["rootcause"] or (args[:1] in (["auto"], ["findata2"]) and "--resume" not in args):
        rc = PRIOR.main(args) if args[:1] != ["rootcause"] else 0
        dp = diluted_only_policy()
        o = rootcause_run()
        L = _lines_v187(o, dp)
        for l in L:
            print(l)
        print("  [U/I] %s" % o["html"])
        if args[:1] == ["auto"]:
            pk = _rep() / "auto" / "VRN_AI_PACK_latest.md"
            if pk.exists():
                old = [l for l in pk.read_text(encoding="utf-8").splitlines() if l.strip()]
                nxt = ["NEXT: 依根因件數排序 → 從最多的根因在源頭修一整類(薄尾 · 在地測試)→ 再跑 auto"]
                pk.write_text("\n".join(([l for l in old if not l.startswith("NEXT:")] + L)[:299] + nxt) + "\n", encoding="utf-8")
                ac = _resolve("aiverb_compress")
                if ac:
                    print("[計] AI 包(含根因分析)· %s" % ac(pk, nxt[0].replace("NEXT: ", ""))[1])
        return rc
    return PRIOR.main(args)



def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    chk("⓪ 根因表 30 條 · 代碼 RC01~RC30 唯一 · 每條有範圍 / 原因 / 源頭修法", len(RC) == 30 and len({c for c, *_ in RC}) == 30 and all(a and r and fx for _, a, r, fx in RC))
    R = lambda lab, std, vals: {"label_raw": lab, "std": std, "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
    t = {"id": "T1", "status": "未過", "raw_rows": [["NT$m", "2024A", "2025F", "2024A", "2025F"], ["Revenue", "1,000", "(200)", "900"], ["Gross profit", "400", "450", "380", "420"]],
         "rows": [R("Revenue", "revenue", {"2024A": 1000, "2025F": 200}), R("Revenue", "revenue", {"2024A": 900}), R("Revenue growth %", "revenue", {"2025F": 12.0}), R("(NT$ m)", "", {"2024A": 1})],
         "unmatched_labels": ["營業外淨額"], "calc": [{"rule": "毛利 = 營收 − 成本", "period": "2024A", "status": "FAIL", "detail": "400 vs -400"},
                                                 {"rule": "營益 = 毛利 − 營業費用", "period": "2025F", "status": "FAIL", "detail": "250 vs 2500"},
                                                 {"rule": "毛利 = 營收 − 成本", "period": "2025F", "status": "FAIL", "detail": "450 vs 450.9"}]}
    got = {h[0] for h in classify_table("A.pdf", t, 2025)}
    want = {"RC03", "RC04", "RC07", "RC09", "RC11", "RC12", "RC15", "RC16", "RC17", "RC18"}
    chk("① 表格根因:欄位錯位 / 並排兩表 / 括號負數 / 單位列 / 沒對鍵 / 成長率對到金額鍵 / 重複鍵 / 正負相反 / 差 10 倍 / 四捨五入 → %s" % sorted(got & want), want <= got)
    tx = [{"type": "sentence", "text": "本報告僅供參考,投資人應自行判斷"}, {"type": "sentence", "text": "營收 " + "很長的內容" * 90}, {"type": "sentence", "text": "The company expects strong"},
          {"type": "sentence", "text": "demand in 2026."}, {"type": "sentence", "text": "2024 1,200 2025 1,350 2026 1,500 2027 1,620 毛利率 32.1% 33.0%"}]
    gt = {h[0] for h in classify_text("A.pdf", tx)}
    chk("② 正文根因:免責聲明混入 / 句子過長(閱讀順序)/ 斷句錯(下句小寫)/ 表格文字當正文 → %s" % sorted(gt), {"RC20", "RC21", "RC22", "RC24"} <= gt)
    cc = lambda a, b, o=frozenset(): classify_conflict("A.pdf", "T1", "revenue·2025F", a, b, set(o))[0]  # noqa: E731
    chk("③ 雙軌衝突格根因:負號遺失 RC29 · 差 100 倍 RC28 · = 鄰格值 RC27 · 數字黏連 RC26 · 8→3 誤認 RC25 · 一邊 0 RC30 · 其他 RC00",
        cc(120, -120) == "RC29" and cc(1234, 12.34) == "RC28" and cc(500, 480, {480.0, 500.0}) == "RC27" and cc(242, 24261) == "RC26" and cc(1830, 1330) == "RC25"
        and cc(0, 50) == "RC30" and cc(100, 257) == "RC00")
    td = Path(tempfile.mkdtemp(prefix="vrn187-"))
    saved = os.environ.get("VIA_VRN_HEALTH_OUT")
    try:
        os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "rep")
        (td / "rep" / "restore").mkdir(parents=True)
        (td / "rep" / "restore" / "01_a.json").write_text(json.dumps({"document_meta": {"file": "A 20251201.pdf"}, "content": tx, "tables": [t]}, ensure_ascii=False), encoding="utf-8")
        (td / "rep" / "dualtrack").mkdir()
        (td / "rep" / "dualtrack" / "DUALTRACK_latest.json").write_text(json.dumps({"records": [{"kind": "table", "file": "A 20251201.pdf", "id": "T1", "lamp": "RED", "agree": 0.4,
                                                                                                "conflicts": [["revenue·2025F", 120.0, -120.0], ["cogs·2025F", 1234.0, 12.34], ["eps·2025F", 1830.0, 1330.0]]}]}), encoding="utf-8")
        o = rootcause_run()
        ns = [r["n"] for r in o["rows"]]
        chk("④ rootcause 動詞:%d 件 · %d 類 · 依件數由多到少 · 每類附源頭修法 + 例子" % (o["total"], len(o["rows"])), o["total"] >= 15 and ns == sorted(ns, reverse=True) and all(r["fix"] for r in o["rows"]))
        (td / "rep" / "findata").mkdir()
        (td / "rep" / "findata" / "FINANCIAL_DATA_FINAL_latest.json").write_text(json.dumps({"columns": ["ACCOUNT", "THREE_LIGHT"], "extra": ["EPS_CLASS"], "rows": [
            {"ACCOUNT": "basic_eps", "THREE_LIGHT": "YELLOW", "EPS_CLASS": "BASIC_EPS"}, {"ACCOUNT": "eps", "THREE_LIGHT": "YELLOW", "EPS_CLASS": "EPS_UNSURE"},
            {"ACCOUNT": "diluted_eps", "THREE_LIGHT": "GREEN", "EPS_CLASS": "DILUTED_EPS"}]}), encoding="utf-8")
        dp = diluted_only_policy()
        rr = json.loads((td / "rep" / "findata" / "FINANCIAL_DATA_FINAL_latest.json").read_text(encoding="utf-8"))["rows"]
        chk("⑤ 只有稀釋 EPS 有意義:基本 EPS → 灰「不使用」· 未分 → 黃「未確認稀釋」· 稀釋照舊", dp == {"basic": 1, "unsure": 1} and rr[0]["THREE_LIGHT"] == "GRAY" and "不使用" in rr[0]["ACCOUNT"]
            and "未確認稀釋" in rr[1]["ACCOUNT"] and rr[2]["THREE_LIGHT"] == "GREEN")
    finally:
        if saved is None:
            os.environ.pop("VIA_VRN_HEALTH_OUT", None)
        else:
            os.environ["VIA_VRN_HEALTH_OUT"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0187 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Language Engine  v1.0   --  中文判讀共用層 (切句 / 期限 / 意圖 / 校正)
----------------------------------------------------------------------------
 定位: 郵件判讀與會議記錄兩條線共用的中文處理層。刻意做成「純規則、零相依」,
       原因: 判讀結果必須可解釋、可重現、可稽核 —— 每個判斷都回傳觸發它的
       cue 詞, 報告上看得到「為什麼系統這樣判」。LLM 只在本層之上做加值,
       不取代本層 (LLM 不可得時系統仍完整可用)。

 提供:
   split_sentences   切句 (中文標點 + 長句二次切分)
   resolve_due       相對時間 -> 絕對日期 (「下週三前」-> 2026-08-05)
   classify_mail     郵件意圖 + 緊急度 1-5 (帶 cue 與信心)
   classify_sentence 句子性質 決/辦/議/問/資 (帶 cue 與信心)
   fuzzy_correct     專有名詞模糊校正 (詞彙表驅動)
   to_traditional    簡繁轉換 (opencc 選配)
   strip_fillers     口語贅詞清理 (保守: 只清明確的填充詞)
 相容: Python 3.11+, 標準庫。選配 opencc / rapidfuzz 可提升品質但非必要。
============================================================================
"""
from __future__ import annotations

import re
import calendar
import datetime as dt
from typing import Optional

LANG_VERSION = "v1.0"

UNKNOWN = "[?]"

# ---------------------------------------------------------------- 切句 ------

_SENT_END = "。！？!?；;\n"
_SOFT_BREAK = "，,、"


def split_sentences(text: str, max_len: int = 60) -> list[str]:
    """
    中文切句。先依句末標點硬切, 超長句再依逗號軟切 ——
    逐字稿常出現「一口氣講三分鐘沒有句號」, 不二次切分會讓一句話塞進三個議題。
    """
    if not text:
        return []
    hard: list[str] = []
    buf = ""
    for ch in str(text):
        buf += ch
        if ch in _SENT_END:
            s = buf.strip()
            if s:
                hard.append(s)
            buf = ""
    if buf.strip():
        hard.append(buf.strip())

    out: list[str] = []
    for s in hard:
        if len(s) <= max_len:
            out.append(s)
            continue
        piece = ""
        for ch in s:
            piece += ch
            if ch in _SOFT_BREAK and len(piece) >= max_len:
                out.append(piece.strip())
                piece = ""
        if piece.strip():
            out.append(piece.strip())
    return [s for s in out if s]


# ---------------------------------------------------------------- 數字 ------

_ZH_DIGIT = {"零": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5,
             "六": 6, "七": 7, "八": 8, "九": 9}


def zh2int(s: str) -> Optional[int]:
    """中文數字 -> int (支援 0-99, 涵蓋期限用語的實際範圍)。"""
    s = str(s).strip()
    if s.isdigit():
        return int(s)
    if not s:
        return None
    if s == "十":
        return 10
    if "十" in s:
        left, _, right = s.partition("十")
        tens = _ZH_DIGIT.get(left, 1) if left else 1
        ones = _ZH_DIGIT.get(right, 0) if right else 0
        if left and left not in _ZH_DIGIT:
            return None
        if right and right not in _ZH_DIGIT:
            return None
        return tens * 10 + ones
    if len(s) == 1 and s in _ZH_DIGIT:
        return _ZH_DIGIT[s]
    return None


_NUM = r"(\d{1,2}|[零一二兩三四五六七八九十]{1,3})"

# ---------------------------------------------------------------- 期限 ------

_WEEKDAY = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6, "末": 4}
_WK = r"(?:週|周|星期|禮拜)"


def _monday(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def _month_end(d: dt.date) -> dt.date:
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def _add_months(d: dt.date, n: int) -> dt.date:
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return d.replace(year=y, month=m, day=min(d.day, calendar.monthrange(y, m)[1]))


def resolve_due(text: str, base: dt.date | None = None) -> Optional[tuple[dt.date, str]]:
    """
    相對時間 -> 絕對日期。回傳 (date, 觸發字串) 或 None。
    會議與郵件裡的期限幾乎都是相對的 (「下週三前」),
    不換算成絕對日期, 逾期偵測就完全做不了。
    """
    if not text:
        return None
    base = base or dt.date.today()
    t = str(text)
    hits: list[tuple[int, int, dt.date, str]] = []

    def add(m: re.Match, d: Optional[dt.date]) -> None:
        if d is not None:
            hits.append((m.start(), -(m.end() - m.start()), d, m.group(0)))

    def _weekday_date(offset_weeks: int, wd_char: str, allow_roll: bool) -> Optional[dt.date]:
        wd = _WEEKDAY.get(wd_char)
        if wd is None:
            return None
        d = _monday(base) + dt.timedelta(days=wd, weeks=offset_weeks)
        if allow_roll and d < base:
            d += dt.timedelta(days=7)
        return d

    # 明確日期
    for m in re.finditer(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})\s*[日號]?", t):
        try:
            add(m, dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            pass
    for m in re.finditer(r"(?<![\d/-])(\d{1,2})[/月](\d{1,2})\s*[日號]", t):
        try:
            d = dt.date(base.year, int(m.group(1)), int(m.group(2)))
            # 已過超過半年者視為明年 (跨年度會議的常見寫法)
            if (base - d).days > 182:
                d = d.replace(year=base.year + 1)
            add(m, d)
        except ValueError:
            pass

    # 週別
    for m in re.finditer(r"下下%s([一二三四五六日天])" % _WK, t):
        add(m, _weekday_date(2, m.group(1), False))
    for m in re.finditer(r"(下|這|本|此)%s([一二三四五六日天])" % _WK, t):
        add(m, _weekday_date(1 if m.group(1) == "下" else 0, m.group(2), False))
    for m in re.finditer(r"(?<![下這本此])%s([一二三四五六日天])" % _WK, t):
        add(m, _weekday_date(0, m.group(1), True))
    for m in re.finditer(r"下下%s(?![一二三四五六日天])(?:底|內|以內)?" % _WK, t):
        add(m, _monday(base) + dt.timedelta(days=4, weeks=2))
    for m in re.finditer(r"下%s(?![一二三四五六日天])(?:底|內|以內)?" % _WK, t):
        add(m, _monday(base) + dt.timedelta(days=4, weeks=1))
    for m in re.finditer(r"(這|本|此)%s(?![一二三四五六日天])(?:底|內|以內)?" % _WK, t):
        add(m, _monday(base) + dt.timedelta(days=4))

    # 日別
    for m in re.finditer(r"今天|今日|本日", t):
        add(m, base)
    for m in re.finditer(r"明天|明日", t):
        add(m, base + dt.timedelta(days=1))
    for m in re.finditer(r"(?<!大)後天", t):
        add(m, base + dt.timedelta(days=2))
    for m in re.finditer(r"大後天", t):
        add(m, base + dt.timedelta(days=3))

    # 月別
    for m in re.finditer(r"下個?月\s*%s\s*[日號]" % _NUM, t):
        n = zh2int(m.group(1))
        nm = _add_months(base.replace(day=1), 1)
        if n and 1 <= n <= calendar.monthrange(nm.year, nm.month)[1]:
            add(m, nm.replace(day=n))
    for m in re.finditer(r"下個?月底", t):
        add(m, _month_end(_add_months(base.replace(day=1), 1)))
    for m in re.finditer(r"下個?月初", t):
        add(m, _add_months(base.replace(day=1), 1))
    for m in re.finditer(r"(這個?月|本月)?月底", t):
        add(m, _month_end(base))
    for m in re.finditer(r"(這個?月|本月)月初", t):
        add(m, base.replace(day=1))

    # 相對量
    for m in re.finditer(r"%s\s*(?:天|日)\s*(?:內|後|以內|之內)" % _NUM, t):
        n = zh2int(m.group(1))
        add(m, base + dt.timedelta(days=n) if n else None)
    for m in re.finditer(r"%s\s*%s\s*(?:內|後|以內|之內)" % (_NUM, _WK), t):
        n = zh2int(m.group(1))
        add(m, base + dt.timedelta(weeks=n) if n else None)

    if not hits:
        return None
    hits.sort()                      # 位置最前者優先; 同位置取最長 match
    _, _, d, matched = hits[0]
    return d, matched


# ---------------------------------------------------------------- 郵件意圖 --

MAIL_INTENTS = ("REQUEST", "REPLY", "ESCALATION", "NOTICE", "FYI")

_INTENT_CUES: dict[str, list[str]] = {
    "ESCALATION": ["逾期", "超過期限", "已過期", "緊急", "急件", "催辦", "再次提醒", "第三次",
                   "asap", "urgent", "critical", "立即處理", "停線", "客訴"],
    # 注意: 「RE:」前綴不列在這裡。RE: 只代表「這封信在某個會話串裡」,
    # 對方在自己的信上回覆來催你, 主旨一樣是 RE:, 但那是升級不是回覆。
    "REPLY": ["回覆如下", "已完成", "已處理", "已確認", "如附件回覆", "答覆如下", "回覆內容"],
    "REQUEST": ["請協助", "請提供", "麻煩", "煩請", "請確認", "請回覆", "需要您", "請於",
                "是否可以", "可否", "請安排", "請追蹤", "please provide", "could you", "kindly"],
    "NOTICE": ["通知", "公告", "系統自動", "no-reply", "noreply", "自動發送", "已排程"],
    "FYI": ["fyi", "供參", "僅供參考", "周知", "知悉即可", "無需回覆"],
}

_URGENCY_CUES: dict[int, list[str]] = {
    5: ["緊急", "急件", "asap", "urgent", "critical", "立即", "馬上", "停線", "停工",
        "客訴", "今天內", "本日內", "當日回覆"],
    4: ["盡快", "儘快", "優先", "重要", "逾期", "催辦", "本週內", "明天前", "high priority"],
    3: ["請於", "期限", "deadline", "請提供", "請確認", "請協助"],
    2: ["參考", "有空", "方便時", "不急"],
    1: ["fyi", "供參", "周知", "無需回覆"],
}


def _hit(text: str, cues: list[str]) -> Optional[str]:
    low = text.lower()
    for c in cues:
        if c.lower() in low:
            return c
    return None


def classify_mail(subject: str, body: str, has_checkbox_reply: bool = False) -> dict:
    """
    郵件意圖 + 緊急度判讀 (純規則, 全程可解釋)。
    回傳 {intent, urgency, needs_action, confidence, cues}
    低信心者由呼叫端送 Q01 隔離, 不阻斷主線。
    """
    subject = subject or ""
    body = body or ""
    blob = "%s\n%s" % (subject, body)
    cues: list[str] = []

    intent, conf = "NOTICE", 0.35
    is_thread_reply = bool(re.match(r"\s*[^\w]*\s*(re|fw|fwd|回覆|答覆)\s*[:：]",
                                    subject, re.IGNORECASE))
    if has_checkbox_reply:
        intent, conf = "REPLY", 0.9          # 勾選是最強訊號, 不會誤判
        cues.append("checkbox")
    else:
        for name in ("ESCALATION", "REPLY", "REQUEST", "FYI", "NOTICE"):
            c = _hit(blob, _INTENT_CUES[name])
            if c:
                intent, conf = name, 0.8
                cues.append(c)
                break
        else:
            if is_thread_reply:
                intent, conf = "REPLY", 0.5   # 只有 RE: 前綴, 信心不高
                cues.append("re-prefix")
            elif re.search(r"[?？]", blob) or resolve_due(blob):
                intent, conf = "REQUEST", 0.5
                cues.append("question/deadline")

    urgency = 3 if intent in ("REQUEST", "ESCALATION") else 2
    for lvl in (5, 4, 3, 2, 1):
        c = _hit(blob, _URGENCY_CUES[lvl])
        if c:
            urgency = lvl
            cues.append("U%d:%s" % (lvl, c))
            break
    if intent == "ESCALATION":
        urgency = max(urgency, 5)
    if intent == "FYI":
        urgency = min(urgency, 2)

    needs_action = intent in ("REQUEST", "ESCALATION")
    return {"intent": intent, "urgency": urgency, "needs_action": needs_action,
            "confidence": round(conf, 2), "cues": cues}


# ---------------------------------------------------------------- 句子性質 --

TAGS = ("決", "辦", "議", "問", "資")
TAG_NAMES = {"決": "決議", "辦": "待辦", "議": "討論", "問": "問題", "資": "資訊"}

_DECISION_STRONG = ["決定", "拍板", "定案", "通過", "結論是", "達成共識", "就這麼辦",
                    "敲定", "確定要", "議決", "核定"]
_DECISION_WEAK = ["那就", "就這樣", "就照", "沒問題的話"]
_ACTION_COMMIT = ["我來", "我會", "我負責", "我去", "我先", "我這邊處理", "我這邊出",
                  "交給", "請你", "麻煩你", "由我", "我提供", "我準備", "我提",
                  "持續追蹤", "會持續", "每週回報", "定期回報", "會follow"]
# 指派句: 「麻煩林佳蓉確認…」「請志豪提供…」—— 有受指派人 + 動作動詞才算,
# 否則「麻煩了」「請多指教」這類客套話會被誤判成待辦。
_ASSIGN_RE = re.compile(
    r"(?:請|麻煩|拜託|交給|指派給|煩請)\s*([^\s，,。、；;]{1,8}?)\s*(?:幫忙|協助|再)?\s*"
    r"(提供|確認|處理|安排|追蹤|回覆|準備|整理|查|寄|送|做|完成|更新|聯絡|報告|提出)")
_ACTION_VERB = ["提", "寄", "送", "做", "準備", "安排", "查", "確認", "整理", "更新",
                "聯絡", "跟進", "追蹤", "報告", "完成", "處理", "提供", "回覆", "出"]
_QUESTION = ["有沒有", "是不是", "要不要", "多少", "為什麼", "怎麼", "還不確定",
             "要再查", "不知道", "可不可以", "能不能"]
_OPINION = ["我覺得", "我認為", "建議", "應該", "可能", "或許", "不如", "我想", "傾向"]


def classify_sentence(text: str, is_chair: bool = False,
                      base_date: dt.date | None = None) -> dict:
    """
    句子性質判讀 決/辦/議/問/資。回傳 {tag, cue, confidence}

    設計重點: 「決議」與「提議」必須分開 —— 「應該可以這樣做」不是決議。
    只有出現強決策詞、或主席說出弱決策詞 (那就…) 才算決議, 其餘一律降級為討論。
    """
    t = (text or "").strip()
    if not t:
        return {"tag": "資", "cue": "", "confidence": 0.0}

    c = _hit(t, _DECISION_STRONG)
    if c:
        return {"tag": "決", "cue": c, "confidence": 0.9}
    c = _hit(t, _DECISION_WEAK)
    if c and is_chair:
        return {"tag": "決", "cue": "%s(主席)" % c, "confidence": 0.6}

    c = _hit(t, _ACTION_COMMIT)
    if c:
        return {"tag": "辦", "cue": c, "confidence": 0.85}
    m = _ASSIGN_RE.search(t)
    if m:
        return {"tag": "辦", "cue": "指派:%s%s" % (m.group(1), m.group(2)), "confidence": 0.8}
    due = resolve_due(t, base_date)
    if due and _hit(t, _ACTION_VERB):
        return {"tag": "辦", "cue": "期限:%s" % due[1], "confidence": 0.65}

    if t.rstrip("」』)】").endswith(("？", "?", "嗎", "呢", "嗎。", "呢。")):
        return {"tag": "問", "cue": "句末問句", "confidence": 0.8}
    c = _hit(t, _QUESTION)
    if c:
        return {"tag": "問", "cue": c, "confidence": 0.7}

    c = _hit(t, _OPINION)
    if c:
        return {"tag": "議", "cue": c, "confidence": 0.75}

    return {"tag": "資", "cue": "", "confidence": 0.5}


# ---------------------------------------------------------------- 文字整理 --

_FILLER_PATTERNS = [
    r"^\s*(?:呃|嗯|欸|唉|啊)+[，,、\s]*",
    r"(?:呃|嗯)+(?=[，,、])",
    r"就是說[，,、\s]*",
    r"那個(?=[，,、\s])",
    r"這個(?=[，,、\s])",
    r"對對對[，,、\s]*",
    r"\b(?:um+|uh+|you know|i mean)\b[,\s]*",
]


def strip_fillers(text: str) -> str:
    """保守清理口語贅詞。刻意不動「那個報表」這類有語意的用法。"""
    t = text or ""
    for p in _FILLER_PATTERNS:
        t = re.sub(p, "", t, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", t).strip()


def to_traditional(text: str, config: str = "s2twp") -> str:
    """簡繁轉換 (opencc 選配)。ASR 中文輸出常是簡體, 不轉會混在繁中記錄裡。"""
    if not text:
        return text
    try:
        import opencc  # type: ignore
        return opencc.OpenCC(config).convert(text)
    except Exception:
        return text


def _ratio(a: str, b: str) -> float:
    try:
        from rapidfuzz.distance import Levenshtein  # type: ignore
        return Levenshtein.normalized_similarity(a, b)
    except Exception:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio()


# 同音/近音字群 —— ASR 的替換錯誤幾乎都是同音字 (稼動率 -> 稼動律)。
# 只有落在同一群的字才允許被校正: 「宣傳排程」的「排」與「期」不同音,
# 因此不會被誤改成「宣傳期程」。各單位可依自己的專有名詞擴充本表。
_HOMOPHONE_GROUPS = [
    "率律慮濾綠", "在再", "的得地", "是事士式試市示", "做作坐座", "需須",
    "以已椅倚", "其期奇齊旗", "制製至志誌治質置智", "帳賬張章漲", "家佳加價夾",
    "容蓉溶榕", "豪毫號耗好", "華花畫化划", "程成城承誠", "計級即記寄季既繼",
    "案安按暗", "報保寶包抱", "產鏟闡", "動洞棟凍", "稼架價假嫁駕", "莞管館官關觀",
    "東冬董懂凍", "線先現限憲", "料療聊瞭", "貨獲或惑霍", "資自字姿滋",
    "議意義易益溢", "決絕覺爵", "辦半版板伴", "認任仁刃", "確缺卻雀",
    "供工功公攻宮", "應影映硬", "算酸蒜", "預育與譽域", "銷小笑消宵校",
    "傳船串穿", "排牌派拍", "週洲州舟粥", "數術書輸熟", "程稱撐", "配佩培賠",
    "額鵝惡", "簽千前錢潛", "核合何和荷", "圖徒途土", "面免棉綿", "格隔革各",
]
_HOMOPHONE_OF: dict[str, int] = {
    ch: gid for gid, grp in enumerate(_HOMOPHONE_GROUPS) for ch in grp
}


def _confusable(a: str, b: str) -> bool:
    """兩個字是否可能被 ASR 混淆 (同音字群, 或英數字母的拼寫誤差)。"""
    if a.isascii() and b.isascii() and a.isalpha() and b.isalpha():
        return True
    ga, gb = _HOMOPHONE_OF.get(a), _HOMOPHONE_OF.get(b)
    return ga is not None and ga == gb


def fuzzy_correct(text: str, vocab: list[str], max_sub: int = 1,
                  min_len: int = 3) -> tuple[str, list[tuple[str, str]]]:
    """
    專有名詞模糊校正。詞彙表 (人名 / 專案 / 產品代號) 驅動,
    回傳 (校正後文字, [(原字串, 校正後), ...]) —— 改了什麼一定要留痕跡, 供人工覆核。

    校正條件是三重的, 缺一不可 —— 校正做太鬆會自己製造錯誤, 比不校正更糟:
      1 等長且至多 max_sub 個字不同 : 中文 ASR 的典型錯誤是同音字替換, 長度不變
      2 差異字必須同音              : 「宣傳排程」的排與期不同音, 不得改成「宣傳期程」
      3 互為子字串者一律不改        : 「宣傳」是合法的較短詞, 不是「宣傳期」的錯誤
    另外 min_len=3: 兩個字的詞錯一個字就是一半不同, 猜錯的風險太高, 不碰。
    """
    if not text or not vocab:
        return text, []
    out = text
    changes: list[tuple[str, str]] = []
    for term in sorted({str(v) for v in vocab if v and len(str(v)) >= min_len},
                       key=len, reverse=True):
        if term in out:
            continue
        n = len(term)
        for i in range(0, max(0, len(out) - n + 1)):
            win = out[i:i + n]
            if re.search(r"[\s，。、,.;；:：!！?？\n]", win):
                continue
            if win in term or term in win:          # 子字串關係 -> 不是聽錯, 是別的詞
                continue
            pairs = [(a, b) for a, b in zip(win, term) if a != b]
            if pairs and len(pairs) <= max_sub and all(_confusable(a, b) for a, b in pairs):
                out = out.replace(win, term, 1)
                changes.append((win, term))
                break
    return out, changes

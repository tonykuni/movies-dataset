#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG085_MarkdownRestore v0100 — 本文還原與分類標註(批636)

操作員令(批636):
  「擷取本文用非OCR / MARKDOWN / OCR 多種擷取法,有時會本文及表格同步擷取;
   用 LAYOUT 引擎標註類別、次類別、頁數;先把還原,再把本文修好,斷行間隔修好,
   一句一行、一標題一行、表格一列一行等還原原貌;表格資料庫;
   文字修正好並標示是標題、表、本文還是其他;
   這是一個**不刪除**修正好本文輸出;再根據修正好的輸出進行 SUMMARIZE。」

【零九頭龍:三道擷取與 LAYOUT 標註都不重做】
  VRN_ENG072 已經落下 sidecar,裡面就有:
      header / right / body / footer   四區(周邊資訊區與本文已分開)
      heads      GenericLayoutEngine 標的 {text, size, level:H1/H2/H3}
      tables     逐表逐列
      compare    **方法之間逐區對照**({ratio, verdict: AGREE/DIVERGE/BOTH_EMPTY})
      triage     DIGITAL / 稀薄 / backend(非OCR 還是 OCR 走的哪一道)
  所以本器**讀 sidecar**,不重抽一次。重抽的那一份跟原本那一份遲早會不一樣。

【要修的病(實測,不是假設)】
  `VRN_Meeting_Minutes` 這一份:
      tables[0] 只撈到表頭 `[['#','行動','負責人','期限']]` —— **一列**,
      而資料列全部漏進 body,變成
          「1 Action Items 行動項目#行動負責人期限1 ControlCenter 的即時狀態燈號…」
  這就是操作員說的「有時會本文及表格同步擷取」。
  本器的 A 道就是把**已經黏進本文的表格片段**找回來、標成表,
  而不是把它刪掉——刪掉就違反「不刪除」。

【不刪除是硬規矩】
  輸出是**新的一層**:原件零觸碰、sidecar 零改寫。
  而且**字元保全率**要現場量:來源(四區+表)的非空白字元,
  一個都不可以在輸出裡消失。㊀ 那一檢就是釘這件事——
  「修好」如果是靠丟掉修不動的那幾段換來的,那不是修好。

【類別 / 次類別】
  標題 H1/H2/H3 · 表 表頭/表列 · 本文 句 · 其他 頁首/右欄/頁尾
  判不出來的標 `未分類`,**不硬塞本文**(硬塞的那一段 SUMMARIZE 會當句子讀)。

【頁數】
  sidecar 是首頁層級,所以預設 page=1;頁尾寫得出「第 N 頁」就用它。
  兩者都沒有就 **page=None 並說出來**,不編一個號碼。

【紀律】
  · 零網路 · 原件零觸碰 · 預設**不寫庫**(表格入庫要 `--apply`)
  · 零九頭龍:擷取、LAYOUT、SUMMARIZE 都呼叫既有正主

用法:
  … run --in "<sidecar 夾>"            還原全部(只讀;出 .md 與 manifest)
  … one --file "<sidecar.json>"        單份
  … run --in <夾> --apply              表格另外入庫(vrn_md_tables)
  … --selftest
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
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
SIDECARS = VIA / "VIA_Reports" / "first_page_text"
OUT = VIA / "VIA_Reports" / "vrn" / "markdown"

# 類別冊。**這一份是分類的唯一出處**——頁上/庫裡/MD 裡的標籤都從這裡長出來。
KINDS = {
    "標題": {"subs": ["H1", "H2", "H3", "H4"], "md": "#",
             "why": "LAYOUT 引擎給的層級;沒給就用字級×粗體推(LEVELS 冊)"},
    "表":   {"subs": ["表頭", "表列", "表格殘片"], "md": "|", "why": "來自 tables,或從本文裡找回來的殘片"},
    "本文": {"subs": ["句"], "md": "", "why": "一句一行"},
    "其他": {"subs": ["頁首", "右欄", "頁尾"], "md": ">", "why": "周邊資訊區"},
    "未分類": {"subs": ["未分類"], "md": "", "why": "判不出來就說判不出來,不硬塞本文"},
    "剔除": {"subs": ["小字體頁尾", "附錄與其標題"], "md": "",
             "why": "批637 操作員令要刪的兩類。**移出本文主體不進 SUMMARIZE**,"
                    "但留在檔尾剔除區並寫出理由——剔除不是消失(批636 保全率照樣 100%)"},
}

# ── 層級門檻冊(批637 操作員令「根據字體大小粗體 可分大中小標題 本文」)──
#   門檻是**相對 body_font 的倍率**,不是絕對字級——每一家研報的內文字級都不一樣
#   (實測樣本 body_font=10.0,而標題有 25.0 / 14.0 / 10.5 三層)。
#   寫絕對值的話換一家券商就全錯。
LEVELS = [
    {"id": "H1", "zh": "大標題", "min_ratio": 1.8, "need_bold": True,
     "why": "字級 ≥ 內文 1.8 倍且粗體。操作員:**大標題是帶著股票名稱與代碼的那一句**"
            "——所以命中股票代號的那一個優先當 H1"},
    {"id": "H2", "zh": "中標題", "min_ratio": 1.25, "need_bold": True,
     "why": "字級 ≥ 內文 1.25 倍且粗體"},
    {"id": "H3", "zh": "小標題", "min_ratio": 1.0, "need_bold": True,
     "why": "粗體、字級不小於內文"},
]
#   剔除冊(批637 操作員令「小字體不相關的頁尾(刪除)」「小字體不相關的後面附錄及它的標題(刪除)」)
#   **剔除不是消失**:移出本文主體、不進 SUMMARIZE,但留在檔尾剔除區並寫出理由,
#   保全率改成「留用 + 剔除 = 100%」。批636 立的「不刪除」與這一單兩條令都成立。
DROP_RULES = [
    {"id": "DROP-FOOT", "zh": "小字體頁尾",
     "max_ratio": 0.9, "zones": ("BL", "BC", "BR"),
     "why": "字級 < 內文 0.9 倍且落在版面下緣三區——頁碼、機密標記、免責一行字"},
    {"id": "DROP-APPX", "zh": "附錄與其標題",
     "max_ratio": 1.0, "after_cue": True,
     "why": "附錄起點之後、字級不大於內文的段落。起點詞見 APPENDIX_CUES"},
]
APPENDIX_CUES = ("附錄", "附件", "Appendix", "APPENDIX", "免責", "重要聲明", "Disclaimer",
                 "DISCLAIMER", "Disclosure", "法律聲明", "風險預告", "本報告僅供")

_ZW = "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0xFEFF, 0x00AD))
_SENT_END = "。．.!?!?;;"
#: 光禿禿的編號:`1.` `2)` `①` `(3)`——它是下一句的號碼,不是一句話。
_BARE_NUM = re.compile(r"[(（]?\s*(?:\d{1,3}|[①-⑳]|[a-zA-Z])\s*[.)）、]?\s*")


def norm(s: str) -> str:
    """比對用的正規化:去零寬、全形→半形、壓空白。**只用於比對,不用於輸出**。"""
    s = str(s or "")
    s = s.translate({ord(c): None for c in _ZW})
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", "", s)


MIN_WRAP_CHARS = 12          #: 折行的左行至少這麼長;短行後面是真的換行不是折行


def repair_text(s: str, head_texts=None) -> tuple:
    """修斷行與間隔。回 `(修好的字串, {動了幾處})`。

    **不刪字**:只做四件——去零寬、全形空白換半形、把 CJK 中間被硬斷的行接回、
    壓連續空白。每一種都記次數,因為「修了什麼」要說得出來。
    """
    n = {"zw": 0, "fullwidth_space": 0, "joins": 0, "spaces": 0}
    for c in _ZW:
        n["zw"] += s.count(c)
    s = s.translate({ord(c): None for c in _ZW})
    n["fullwidth_space"] = s.count("　")
    s = s.replace("　", " ")
    # CJK 被硬斷:三道護欄,缺一個就會把**真的換行**也接掉。
    #   ① 兩側都是 CJK(英數不接——`Q2\n2025` 接了會變 `Q22025`)
    #   ② **左邊那一行要夠長**(≥ MIN_WRAP_CHARS)。折行只發生在行寬用完的時候,
    #      而標題、欄位標籤、短句本來就短——短行後面是真的換行。
    #      自測 ⑳ 當場抓到:`投資論點\n先進製程需求強勁。` 被接成一行,標題就消失了,
    #      而畫面上只看得出「少了一行」。
    #   ③ 左行已經有句末標點、或下一行是已知標題,都不接。
    heads_n = {norm(h) for h in (head_texts or []) if h}
    _ls = s.split("\n")
    _out = _ls[:1]
    for _nx in _ls[1:]:
        _pv = _out[-1]
        _pc, _nc = _pv.rstrip()[-1:], _nx.lstrip()[:1]
        _long = len(re.sub(r"\s", "", _pv)) >= MIN_WRAP_CHARS
        _nh = norm(_nx) in heads_n or any(norm(_nx).startswith(h) for h in heads_n if h)
        if (_pc and _nc and "\u4e00" <= _pc <= "\u9fa5" and "\u4e00" <= _nc <= "\u9fa5"
                and _long and not _nh and _pc not in _SENT_END):
            n["joins"] += 1
            _out[-1] = _pv.rstrip() + _nx.lstrip()
        else:
            _out.append(_nx)
    s = "\n".join(_out)
    before = len(s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    n["spaces"] = before - len(s)
    return s, n


def split_sentences(s: str) -> list:
    """一句一行。**只在句末標點斷**,而且表格與標題不走這裡。

    為什麼不順便拿換行當句界:研報的換行多半是版面折行不是句界,
    拿它斷會把一句話切成三行(而 SUMMARIZE 會把三行讀成三件事)。
    """
    out, buf = [], ""
    for ch in str(s or ""):
        buf += ch
        if ch in _SENT_END:
            t = buf.strip()
            if t:
                out.append(t)
            buf = ""
    t = buf.strip()
    if t:
        out.append(t)
    # **光禿禿的編號不是一句**。`1.` / `2.` / `①` 被句末的 `.` 切成獨立一行之後,
    #   「一句一行」就變成「一個號碼也一行」——而 SUMMARIZE 會把它讀成一件事。
    #   編號黏回它後面那一句(實測:VRN_Meeting_Minutes 一份就生了 5 行這種)。
    merged = []
    for x in out:
        if merged and _BARE_NUM.fullmatch(merged[-1]):
            merged[-1] = merged[-1] + " " + x
        else:
            merged.append(x)
    return merged


def table_fragments(tables: list) -> dict:
    """本文裡用來找回表格殘片的鑰匙。回 `{"row": [...], "cell": [...]}`。

    **以「列」為單位拼起來**,不是逐格比——自測 ⑧ 當場抓到:
    病灶是整列被黏進本文(`…行動項目#行動負責人期限1 燈號要補…`),
    而逐格比的話 `#` 太短被濾掉、`行動` 又不在行首,於是一個都對不上,
    那一行就被判成本文(而 SUMMARIZE 會把表頭當句子讀)。
    列鑰匙要 ≥2 格且 ≥4 字才算數,不然 `['1','2']` 這種會亂咬。
    """
    rows, cells = [], []
    for t in tables or []:
        for row in (t or []):
            cs = row if isinstance(row, (list, tuple)) else [row]
            ks = [norm(c) for c in cs]
            joined = "".join(ks)
            if len([k for k in ks if k]) >= 2 and len(joined) >= 4:
                rows.append(joined)
            for k in ks:
                if len(k) >= 4:
                    cells.append(k)
    return {"row": sorted(set(rows), key=len, reverse=True),
            "cell": sorted(set(cells), key=len, reverse=True)}


_HUB = None


def hub():
    """規則樞紐 SUP_MDL749(找股票代號用)。缺席回 None——**不自己寫一條代號正則**。"""
    global _HUB
    if _HUB is not None:
        return _HUB or None
    import importlib.util
    d = VIA / "supportive modules" / "70_VRN_Rules"
    hits = sorted(d.glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))
    if not hits:
        _HUB = False
        return None
    try:
        spec = importlib.util.spec_from_file_location("SUP_MDL749_hub85", hits[-1])
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _HUB = m
    except Exception:
        _HUB = False
    return _HUB or None


def has_ticker(text: str) -> str:
    """這一行有沒有台股代號。回命中的代號;沒有或樞紐缺席回空字串。"""
    h = hub()
    if not h:
        return ""
    for tok in re.findall(r"[0-9A-Za-z.]{4,12}", str(text or "")):
        r = h.ticker_platform(tok)
        if r and not r.get("ambiguous_year"):
            return r["canonical"]
    return ""


def gle_index(sc: dict) -> tuple:
    """`gle.elements` → `(依正規化 head 可查的表, body_font)`。

    `head` 是被截過的(實測約 30 字),所以查法是**前綴比對**不是相等。
    `gle` 缺席回 `({}, None)`——**沒有版面資料就不要假裝判得出字級**。
    """
    g = sc.get("gle") or {}
    els = g.get("elements")
    if not isinstance(els, list):
        return {}, None
    try:
        bf = float(g.get("body_font") or 0) or None
    except (TypeError, ValueError):
        bf = None
    out = []
    for e in els:
        if not isinstance(e, dict):
            continue
        k = norm(e.get("head") or "")
        if not k:
            continue
        try:
            sz = float(e.get("size") or 0)
        except (TypeError, ValueError):
            sz = 0.0
        out.append({"key": k, "size": sz,
                    "bold": str(e.get("bold")).lower() == "true" or e.get("bold") is True,
                    "zone": str(e.get("zone") or ""), "head": str(e.get("head") or "")})
    out.sort(key=lambda x: -len(x["key"]))
    return {"rows": out}, bf


def gle_of(line_key: str, idx: dict) -> dict:
    """一行對到哪一個版面元素。前綴比對,長的先試。"""
    for e in idx.get("rows", []):
        if line_key.startswith(e["key"]) or e["key"].startswith(line_key):
            return e
    return {}


def level_of(el: dict, body_font: float) -> str:
    """字級 × 粗體 → 大/中/小標題。判不出來回空字串(**不硬塞標題**)。"""
    if not el or not body_font:
        return ""
    r = (el.get("size") or 0) / body_font
    for L in LEVELS:
        if r >= L["min_ratio"] and (el.get("bold") if L["need_bold"] else True):
            return L["id"]
    return ""


def drop_of(el: dict, body_font: float, in_appendix: bool) -> dict:
    """要不要剔除。回命中的規則;不剔除回空 dict。"""
    if not body_font:
        return {}
    r = (el.get("size") or 0) / body_font if el else 1.0
    for rule in DROP_RULES:
        if rule.get("zones"):
            if el and r < rule["max_ratio"] and el.get("zone", "") in rule["zones"]:
                return rule
        elif rule.get("after_cue"):
            if in_appendix and el and r <= rule["max_ratio"]:
                return rule
    return {}


def is_appendix_cue(text: str) -> str:
    """這一行是不是附錄起點。回命中的詞;不是回空字串。"""
    t = str(text or "")
    return next((c for c in APPENDIX_CUES if c in t), "")


def page_of(sc: dict) -> tuple:
    """頁數。頁尾寫得出「第 N 頁」就用它;否則 sidecar 是首頁層級 → 1;
    真的判不出來回 `(None, 理由)`——**不編號碼**。"""
    foot = str(sc.get("footer") or "")
    m = re.search(r"第\s*(\d{1,4})\s*頁", foot) or re.search(r"[Pp]age\s*(\d{1,4})", foot)
    if m:
        return int(m.group(1)), "頁尾寫出來的"
    if any(str(sc.get(k) or "").strip() for k in ("header", "right", "body", "footer")):
        return 1, "sidecar 是首頁層級(ENG072 只抽第一頁),所以是 1"
    return None, "頁尾沒寫、四區也全空——判不出來就不編號碼"


def restore(sc: dict, name: str = "") -> dict:
    """一份 sidecar → 分類標註過的行串 + 保全率。"""
    page, page_why = page_of(sc)
    idx, body_font = gle_index(sc)
    frs = table_fragments(sc.get("tables") or [])
    heads = []
    for h in (sc.get("heads") or []):
        if isinstance(h, dict) and str(h.get("text") or "").strip():
            heads.append({"key": norm(h["text"]), "text": str(h["text"]).strip(),
                          "level": str(h.get("level") or "H3").upper(),
                          "size": h.get("size")})
    head_keys = {h["key"]: h for h in heads}

    rows = []

    def add(kind, sub, text, why, extra=None):
        t = str(text or "").strip()
        if not t:
            return
        rows.append(dict({"kind": kind, "sub": sub, "text": t, "page": page, "why": why},
                         **(extra or {})))

    # ① 其他:周邊資訊區(頁首 / 右欄 / 頁尾)
    for key, sub in (("header", "頁首"), ("right", "右欄"), ("footer", "頁尾")):
        raw = str(sc.get(key) or "")
        if not raw.strip():
            continue
        fixed, _ = repair_text(raw)
        el = gle_of(norm(fixed), idx)
        d = drop_of(el, body_font, False) if key == "footer" else {}
        if d:
            add("剔除", d["zh"], fixed,
                f"{d['id']}:{d['why']}(字級 {el.get('size')} / 內文 {body_font} · "
                f"區 {el.get('zone')})——**移出本文不進 SUMMARIZE,但留在剔除區**")
        else:
            add("其他", sub, fixed, f"ENG072 的 {key} 區")

    # ② 標題 + 本文:走 body,先把標題整行切出來,剩下的才斷句
    body, rep = repair_text(str(sc.get("body") or ""), [h["text"] for h in heads])
    in_appendix = ""
    for line in [x for x in re.split(r"\n+", body) if x.strip()]:
        k = norm(line)
        el = gle_of(k, idx)
        # 附錄起點:命中起點詞之後,小字體的東西一律剔除(操作員令)
        cue = is_appendix_cue(line)
        if cue and not in_appendix:
            in_appendix = cue
        d = drop_of(el, body_font, bool(in_appendix))
        if d:
            add("剔除", d["zh"], line,
                f"{d['id']}:{d['why']}"
                + (f";附錄起點「{in_appendix}」" if d["id"] == "DROP-APPX" else "")
                + f"(字級 {el.get('size')} / 內文 {body_font})"
                  "——**移出本文不進 SUMMARIZE,但留在剔除區**")
            continue
        if k in head_keys:
            h = head_keys[k]
            add("標題", h["level"], line, f"LAYOUT 引擎標的 {h['level']}(字級 {h['size']})")
            continue
        # LAYOUT 沒標,但字級×粗體推得出層級(操作員令「根據字體大小粗體分大中小標題」)
        lv = level_of(el, body_font)
        if lv and not line.rstrip()[-1:] in _SENT_END:
            # **標題沒有句號**——操作員點名的訊號。有句號的粗體大字多半是強調句不是標題。
            add("標題", lv, line,
                f"字級 {el.get('size')} / 內文 {body_font} = "
                f"{(el.get('size') or 0) / body_font:.2f} 倍 · "
                f"{'粗體' if el.get('bold') else '非粗體'} · **句末沒有句號**"
                + (f" · 帶股票代號 {has_ticker(line)}" if lv == "H1" and has_ticker(line) else ""))
            continue
        # 標題被黏在行首**或行中**。
        #   實測:`M E E T I N G M I N U T E S · 會議紀錄VRN Fetch v4 — 設計審查會議日期…`
        #   裡面那個 H1 `VRN Fetch v4 — 設計審查會議` 卡在中間,只比行首是抓不到的
        #   ——跟表格殘片同一種病:黏在哪裡都要找得回來。
        pre = next((h for h in heads
                    if h["key"] and h["key"] in k and len(h["key"]) < len(k)), None)
        if pre:
            i = line.find(pre["text"])
            # **字面找不到就不切。**我第一版在 find 回 -1 的時候還是從 0 砍掉
            #   `len(標題)` 個字——那等於砍掉沒對上的內容,保全率當場從 100%
            #   掉到 96.97%(㊀ 在真資料上抓到,夾具太小沒照出來)。
            #   正規化對得上、字面對不上,代表原字裡夾著零寬或全形——
            #   那種情況**寧可不切**,留一行完整的比切壞一行好。
            if i < 0:
                pre = None
            else:
                head_txt = pre["text"]
        if pre:
            before, after = line[:i], line[i + len(head_txt):]
            if before.strip():
                for _s in split_sentences(before):
                    add("本文", "句", _s, "標題前面那一段(標題原本黏在行中)")
            add("標題", pre["level"], head_txt,
                f"LAYOUT 標的 {pre['level']},原本黏在{'行首' if i == 0 else '行中'},切出來")
            line = after
            k = norm(line)
            if not k:
                continue
        # 表格殘片:整行被表吃掉,或行首黏著表的格子
        # 列鑰匙用 `in`(整列被黏在句子中間也要抓到);格鑰匙才用相等/開頭。
        hit = next((f for f in frs["row"] if f and f in k), "") or \
              next((f for f in frs["cell"] if f and (k == f or k.startswith(f))), "")
        if hit:
            add("表", "表格殘片", line,
                f"這一行在 tables 裡有對得上的格子({hit[:18]}…)——"
                f"擷取時本文與表格黏在一起了,標成表**但不刪**")
            continue
        for s in split_sentences(line):
            add("本文", "句", s, "一句一行(只在句末標點斷)")

    # ③ 表:逐表逐列,一列一行
    for ti, t in enumerate(sc.get("tables") or []):
        for ri, row in enumerate(t or []):
            cells = [str(c) for c in (row if isinstance(row, (list, tuple)) else [row])]
            add("表", "表頭" if ri == 0 else "表列", " | ".join(cells),
                f"tables[{ti}] 第 {ri} 列", {"table": ti, "row": ri, "cells": cells})

    # ④ 大標題只能有一個,而且**是帶股票名稱與代碼的那一句**(操作員批637 指名)。
    #   多個 H1 候選時,命中代號的留 H1,其餘降 H2——不是誰字大誰贏。
    h1s = [r for r in rows if r["kind"] == "標題" and r["sub"] == "H1"]
    if len(h1s) > 1:
        withtk = [r for r in h1s if has_ticker(r["text"])]
        keep = withtk[0] if withtk else h1s[0]
        for r in h1s:
            if r is not keep:
                r["sub"] = "H2"
                r["why"] += ";**降 H2**——大標題只留帶股票代號的那一句(批637)"
        if withtk:
            keep["why"] += f";**留 H1**——帶股票代號 {has_ticker(keep['text'])}"
        else:
            keep["why"] += ";留 H1——沒有一個帶代號,取字級最大的第一個(**這是退路,說出來**)"

    # ⑤ 保全率:來源非空白字元,一個都不可以不見
    src = "".join(str(sc.get(k) or "") for k in ("header", "right", "body", "footer"))
    src += "".join("".join(str(c) for c in (r if isinstance(r, (list, tuple)) else [r]))
                   for t in (sc.get("tables") or []) for r in (t or []))
    src_chars = norm(src)
    out_chars = norm("".join(r["text"] for r in rows))
    kept = sum(1 for i, ch in enumerate(src_chars) if ch in out_chars) if src_chars else 0
    from collections import Counter
    cs, co = Counter(src_chars), Counter(out_chars)
    lost = {c: n - co.get(c, 0) for c, n in cs.items() if n > co.get(c, 0)}
    keep_rate = (1 - sum(lost.values()) / len(src_chars)) * 100.0 if src_chars else None

    return {
        "name": name, "page": page, "page_why": page_why,
        "rows": rows, "repair": rep,
        "n_rows": len(rows),
        "by_kind": {k: sum(1 for r in rows if r["kind"] == k) for k in KINDS},
        "keep": {"src_chars": len(src_chars), "out_chars": len(out_chars),
                 "lost_chars": sum(lost.values()),
                 "lost_sample": sorted(lost.items(), key=lambda x: -x[1])[:6],
                 "rate": keep_rate},
        "method": (sc.get("logic") or {}).get("method", ""),
        "triage": (sc.get("triage") or {}).get("state", ""),
        "compare": sc.get("compare") or {},
    }


def to_markdown(r: dict) -> str:
    """分類標註 → Markdown。**每一行都帶著它是什麼**(HTML 註解,人看不到 AI 看得到)。"""
    L = [f"<!-- VRN_ENG085 v{VERSION} · 還原層(不刪除;原件零觸碰)-->",
         f"<!-- 來源 {r['name']} · 頁 {r['page'] if r['page'] is not None else '判不出來'}"
         f"({r['page_why']})· 擷取法 {r['method'] or '未標'} · 版面 {r['triage'] or '未標'} -->",
         f"<!-- 保全率 {('%.2f%%' % r['keep']['rate']) if r['keep']['rate'] is not None else '—'}"
         f" · 來源字 {r['keep']['src_chars']} · 掉 {r['keep']['lost_chars']} -->", ""]
    last = None
    dropped = [x for x in r["rows"] if x["kind"] == "剔除"]
    for row in [x for x in r["rows"] if x["kind"] != "剔除"]:
        k, sub, t = row["kind"], row["sub"], row["text"]
        if k != last:
            L.append("")
            last = k
        tag = f"<!-- {k}/{sub} p{row['page'] if row['page'] is not None else '?'} -->"
        if k == "標題":
            lv = {"H1": 1, "H2": 2, "H3": 3, "H4": 4}.get(sub, 3)
            L.append(f"{'#' * lv} {t} {tag}")
        elif k == "表":
            if sub == "表頭":
                # **表頭後面要補 `|---|` 分隔列**,不然它不是合法 Markdown 表格,
                #   第二把尺會判成 paragraph(實測 1 塊就是這樣對不上的)。
                cells = [c.strip() for c in t.split("|")]
                L.append("| " + " | ".join(cells) + f" | {tag}")
                L.append("| " + " | ".join(["---"] * len(cells)) + " |")
            elif sub == "表列":
                L.append("| " + " | ".join(c.strip() for c in t.split("|")) + f" | {tag}")
            else:
                L.append(f"{t} {tag}")
        elif k == "其他":
            # **每一行都要加 `>`**。周邊資訊區的原文帶著換行(頁首/右欄常常是多行),
            #   只在第一行加引用符號的話,後面幾行會脫離引用區,
            #   被 Markdown 判成標題或清單——實測 23 塊對不上全是這一種。
            _ls = [x for x in t.split("\n") if x.strip()]
            L.append("> " + f" {tag}\n> ".join(_ls) if len(_ls) > 1 else f"> {t} {tag}")
        else:
            L.append(f"{t} {tag}")
    if dropped:
        L += ["", "---", "",
              f"<!-- 剔除區 {len(dropped)} 段(批637 操作員令要刪的兩類)。",
              "     **移出本文主體、不進 SUMMARIZE**,但留在這裡並寫出理由",
              "     ——剔除不是消失,保全率仍是「留用 + 剔除 = 100%」 -->",
              "", "## 剔除區(不進 SUMMARIZE)"]
        for x in dropped:
            L.append(f"- ~~{x['text']}~~ <!-- 剔除/{x['sub']} p"
                     f"{x['page'] if x['page'] is not None else '?'} · {x['why']} -->")
    return "\n".join(L) + "\n"


# ── 第二把尺:MarkdownLayoutAnalyzer(批639)────────────────────────────
#   操作員上傳 `layout_analysis.py` 要我導入。量完的結論有兩層:
#   ① 上傳那份與樹上 NLP v1.8.0 的副本**換行正規化後 byte 完全相同**
#      (上傳是 CRLF、樹上是 LF)——跟 MDL002 一樣,沒有帶來新東西。
#   ② 它**不是 ENG085 行型判定的替代品**:`_line_type` 判的是 **Markdown 語法**
#      (`#`、`-`、`|`、``` ),而 ENG085 的輸入是 PDF 抽出來的純文字,沒有這些符號。
#      拿它當抽取器會全判成 paragraph。
#   所以它真正的位置是**驗 ENG085 的輸出**:ENG085 說這一行是標題,
#   它獨立再讀一次產出的 .md,說這一塊是不是 heading。
#   兩把尺對不上就具名報出來——**判定器不自判**(LL133)。
#   而且走既有的 SUP_MDL744 NLP 橋,不另開一條 import 路(Zero-Hydra)。
_NLPHUB = None

#: ENG085 的類別 ↔ MarkdownLayoutAnalyzer 的 block_type
#   對照表第一版太窄,實測 149 塊「對不上」裡 **142 塊是我的尺錯不是 ENG085 錯**:
#     · 138 塊 本文/句 vs ordered_list —— `1. 為什麼…` 這種句子**既是本文也是編號清單**,
#       兩把尺都對。Markdown 的 block_type 是**語法層**,ENG085 的 kind 是**語意層**,
#       一個語意可以對到多個語法。窄對照 = 把「兩個都對」判成「對不上」,
#       那是假紅,而假紅跟假綠一樣傷。
#     · 2 塊 表/表格殘片 vs paragraph —— 殘片本來就混在散文裡,分析器說得對。
KIND_TO_BLOCK = {
    "標題": {"heading"},
    # 表列/表頭要是合法 Markdown 表格(有 `|---|` 分隔列)才會被判 table;
    # 殘片是混在散文裡的,paragraph 是對的。
    "表": {"table", "paragraph"},
    "本文": {"paragraph", "ordered_list", "unordered_list", "task_list", "blockquote"},
    "其他": {"blockquote", "paragraph"},
}


def nlp_hub():
    """NLP 應用系統橋(SUP_MDL744)。缺席回 None——**不自己再造一個版面分析器**。"""
    global _NLPHUB
    if _NLPHUB is not None:
        return _NLPHUB or None
    import importlib.util
    d = VIA / "supportive modules" / "70_VRN_Rules"
    hits = sorted(d.glob("SUP_MDL744_NLPApplicationHub_v*.py"))
    if not hits:
        _NLPHUB = False
        return None
    try:
        spec = importlib.util.spec_from_file_location("SUP_MDL744_hub85", hits[-1])
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _NLPHUB = m
    except Exception:
        _NLPHUB = False
    return _NLPHUB or None


def layout_crosscheck(r: dict, md: str) -> dict:
    """拿 MarkdownLayoutAnalyzer 再讀一次 ENG085 產出的 .md,兩把尺對照。

    回 `{"state", "agree", "disagree", "rate", "why", "rows"}`。
    橋缺席或回空 → `state="ABSENT"` 並說出來,**不當成一致**
    (「沒量到」和「量過了一致」是兩件事)。
    """
    h = nlp_hub()
    if h is None or not hasattr(h, "layout"):
        return {"state": "ABSENT", "agree": 0, "disagree": 0, "rate": None, "rows": [],
                "why": "SUP_MDL744 NLP 橋缺席——**沒量到,不是一致**"}
    try:
        la = h.layout(md)
    except Exception as exc:
        return {"state": "FAIL", "agree": 0, "disagree": 0, "rate": None, "rows": [],
                "why": f"{type(exc).__name__}: {exc}"}
    blocks = (la or {}).get("blocks") or []
    if not blocks:
        return {"state": "NODATA", "agree": 0, "disagree": 0, "rate": None, "rows": [],
                "why": "橋回了空 blocks——橋在但是啞的,要查為什麼,不是『沒有版面』"}
    # 逐塊找回它是 ENG085 的哪一行。**用位移對齊,不用「包含」比字**——
    #   實測抓到:`MDL010 到 MDL014 已全部接上 BRIDGE…` 這一段在文件裡出現兩次
    #   (一次是本文、一次在表格列裡),用包含比會挑到第一個,
    #   於是本文那一行被對到表格那一塊,報成「對不上」。
    #   **那不是 ENG085 判錯,是我的比對法不精確。**
    #   改法:按輸出順序用移動游標在 md 裡找每一行的起點,重複的文字自然各歸各位。
    idx, _cur = [], 0
    for x in r["rows"]:
        if x["kind"] == "剔除":
            continue
        _i = md.find(x["text"], _cur)
        if _i < 0:
            _i = md.find(x["text"])          # 找不到就全域找一次(理論上不會)
        if _i >= 0:
            idx.append((_i, _i + len(x["text"]), x))
            _cur = _i + len(x["text"])
    agree, dis = 0, []
    for b in blocks:
        bt = b.get("block_type")
        if bt in ("blank", "thematic_break", "html_block", "source_record_marker"):
            continue
        bk = norm(b.get("source_text") or "")
        if not bk:
            continue
        _bs, _be = int(b["source_span"]["start"]), int(b["source_span"]["end"])
        # 落在這一塊 span 裡、而且重疊最多的那一行
        _cand = [(min(_be, e) - max(_bs, st), row) for st, e, row in idx
                 if min(_be, e) > max(_bs, st)]
        hit = max(_cand, key=lambda z: z[0])[1] if _cand else None
        if hit is None:
            continue
        want = KIND_TO_BLOCK.get(hit["kind"], set())
        if bt in want:
            agree += 1
        else:
            dis.append({"text": hit["text"][:40], "eng085": f"{hit['kind']}/{hit['sub']}",
                        "analyzer": f"{bt}/{(b.get('block_label') or {}).get('zh', '')}"})
    tot = agree + len(dis)
    return {"state": "OK" if tot else "NODATA",
            "agree": agree, "disagree": len(dis),
            "rate": (agree / tot * 100.0) if tot else None,
            "completeness": (la or {}).get("completeness"),
            "rows": dis[:20],
            "why": ("兩把尺全對" if not dis else
                    f"{len(dis)} 塊對不上,具名列出(**不挑一把用**)")}


def disagree_pairs(rows: list, top: int = 8) -> list:
    """兩把尺對不上的**成對統計**。回 `[(eng085, analyzer, 次數, 例子), …]`。

    為什麼要有:工作站實跑 105 份報「對不上 30 塊」,而那 30 塊長什麼樣子
    只有操作員的機器上有。叫他去 grep manifest,等於把診斷丟回給他
    ——**哨兵抓到就要給得出下一步**(L92)。
    """
    from collections import Counter
    c, eg = Counter(), {}
    for r in rows or []:
        for d in (r.get("xcheck") or {}).get("rows") or []:
            k = (d.get("eng085", "?"), d.get("analyzer", "?"))
            c[k] += 1
            eg.setdefault(k, d.get("text", ""))
    return [(a, b, n, eg[(a, b)]) for (a, b), n in c.most_common(top)]


def summarize_input(r: dict) -> str:
    """餵給 SUMMARIZE 的那一份:**剔除區不在裡面**,而且表與標題各自成行。

    不在這裡寫摘要器——摘要走既有的 VRN_ENG080(Zero-Hydra)。
    """
    return "\n".join(x["text"] for x in r["rows"] if x["kind"] != "剔除")


def render_run(res: dict) -> list[str]:
    """把 `run()` 的結果**渲染成逐行字串**。抽出來的唯一理由:那個分歧分支跑不到。

    批650 操作員實機實錄:
        NameError: name 'ok' is not defined   ← VRN_ENG085 v0103 main() 第 1040 行
    `ok` 是 `run()` 的區域變數,`main()` 裡根本沒有這個名字。
    這一行只有在**二尺對不上**的時候才會執行:容器的料一致 380/380 = 100%,
    所以它從寫下來那天起就沒被執行過一次;操作員的機器一致 1093/1123 = 97.3%,
    第一次真的走進這個分支,當場炸掉。

    更難看的是:批640 我**已經**把 `disagree_pairs` 抽成函式、還寫了檢 ㉛ 拿假資料測它,
    檢裡甚至自己寫著「容器零分歧,所以這一段在容器裡走不到,抽成函式才驗得了」——
    **測了那支函式,沒測呼叫它的那一行。**(LL286)
    治法:整段畫面變成純函式,自測直接餵一個「有分歧」的 res 進來走完全程。
    """
    x = res.get("xcheck") or {}
    tot = x.get("agree", 0) + x.get("disagree", 0)
    out = [f"[VRN_ENG085 v{VERSION}] run · OK · {res['n']} 份(OK {res['ok']} · FAIL {res['fail']})",
           (f"  [保全] 最低 {res['keep_min']:.2f}%" if res.get("keep_min") is not None else "  [保全] 無分母"),
           f"         全部 100%:{'是' if res.get('keep_all_100') else '**否——有份數掉字,逐份看 manifest**'}",
           ("  [二尺] MarkdownLayoutAnalyzer 對照 · "
            f"量到 {x.get('measured', 0)} 份 · 沒量到 {x.get('absent', 0)} 份(橋缺席=**沒量到不是一致**)· "
            + (f"一致 {x.get('agree', 0)}/{tot} = {x.get('agree', 0) / tot * 100:.1f}%" if tot else "零塊可比"))]
    if x.get("disagree"):
        # 批640:**不要叫人去翻 JSON**。工作站實跑 105 份報「對不上 30 塊」,
        #   那 30 塊長什麼樣子只有操作員的機器上有——叫他去 grep manifest,
        #   等於把診斷丟回給他。哨兵抓到就要給得出下一步(L92)。
        out.append(f"         **對不上 {x['disagree']} 塊**,成對統計(看一眼就知道是尺錯還是輸出錯):")
        for a, b, n, t in disagree_pairs(res.get("rows") or []):
            out.append(f"           {n:>4} 次 · ENG085={a:14} vs 分析器={b:20} 例:{t[:40]!r}")
    db = res.get("db") or {}
    out.append(f"  [表格] {res.get('tables_rows', 0)} 列 · 入庫 {db.get('state', 'SKIPPED')}"
               + (" · " + db["why"] if db.get("why") else ""))
    out.append(f"  [出] {res.get('out', '')}")
    return out


def run(indir: str = "", apply_db: bool = False) -> dict:
    d = Path(indir) if indir else SIDECARS
    if not d.exists():
        return {"state": "ABSENT", "why": f"sidecar 夾不在:{d}。先跑 ENG072(via-firstpage)"}
    files = sorted(d.glob("*.json"))
    if not files:
        return {"state": "NODATA", "why": f"夾子在但沒有 sidecar:{d}"}
    OUT.mkdir(parents=True, exist_ok=True)
    rows, tables_out = [], []
    for f in files:
        try:
            sc = json.loads(f.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            rows.append({"name": f.name, "state": "FAIL", "why": f"{type(exc).__name__}: {exc}"})
            continue
        r = restore(sc, f.stem)
        (OUT / f"{f.stem}.md").write_text(to_markdown(r), encoding="utf-8")
        for x in r["rows"]:
            if x["kind"] == "表" and "cells" in x:
                tables_out.append({"report": f.stem, "page": x["page"], "table": x["table"],
                                   "row": x["row"], "sub": x["sub"], "cells": x["cells"]})
        r["xcheck"] = layout_crosscheck(r, to_markdown(r))
        r["state"] = "OK"
        rows.append({k: v for k, v in r.items() if k != "rows"})
    ok = [r for r in rows if r.get("state") == "OK"]
    rates = [r["keep"]["rate"] for r in ok if r.get("keep", {}).get("rate") is not None]
    res = {"state": "OK", "dir": str(d), "out": str(OUT), "n": len(files),
           "ok": len(ok), "fail": len(files) - len(ok),
           "tables_rows": len(tables_out),
           "keep_min": min(rates) if rates else None,
           "xcheck": {
               "measured": sum(1 for r in ok if (r.get("xcheck") or {}).get("state") == "OK"),
               "absent": sum(1 for r in ok if (r.get("xcheck") or {}).get("state") == "ABSENT"),
               "agree": sum((r.get("xcheck") or {}).get("agree", 0) for r in ok),
               "disagree": sum((r.get("xcheck") or {}).get("disagree", 0) for r in ok),
           },
           "keep_all_100": all(abs(x - 100.0) < 1e-9 for x in rates) if rates else None,
           "rows": rows}
    (OUT / "VRN_MD_RESTORE_manifest.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    if apply_db:
        res["db"] = _write_tables(tables_out)
    else:
        res["db"] = {"state": "SKIPPED",
                     "why": f"預設不寫庫;要把 {len(tables_out)} 列表格入庫請加 --apply"}
    return res


def _write_tables(rows: list) -> dict:
    """表格入庫(操作員令「表格資料庫」)。**只增不減**:同報告同表先刪同鍵再寫。"""
    if not rows:
        return {"state": "NODATA", "why": "沒有表格列可入庫"}
    try:
        import duckdb
    except Exception:
        return {"state": "ABSENT", "why": "本境沒有 duckdb(不代裝;在工作站跑)"}
    db = VIA / "functional modules" / "VRN" / "output" / "vrn_reports.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS vrn_md_tables(
            report VARCHAR, page INTEGER, tbl INTEGER, row_no INTEGER,
            sub VARCHAR, cells VARCHAR, extracted_at VARCHAR)""")
        reps = sorted({r["report"] for r in rows})
        con.execute("DELETE FROM vrn_md_tables WHERE report IN ("
                    + ",".join("?" * len(reps)) + ")", reps)
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        con.executemany(
            "INSERT INTO vrn_md_tables(report,page,tbl,row_no,sub,cells,extracted_at) "
            "VALUES (?,?,?,?,?,?,?)",
            [(r["report"], r["page"], r["table"], r["row"], r["sub"],
              json.dumps(r["cells"], ensure_ascii=False), ts) for r in rows])
        n = con.execute("SELECT count(*) FROM vrn_md_tables").fetchone()[0]
    finally:
        con.close()
    return {"state": "OK", "db": str(db), "table": "vrn_md_tables",
            "written": len(rows), "total": n}


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== VRN_ENG085 本文還原與分類標註 v{VERSION} · 自測(零網路;零寫庫)===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路", not any(k in code for k in ("import requests", "import httpx", "import urllib")))
    chk("② 預設不寫庫:`--apply` 才入庫,平跑只讀",
        "apply_db: bool = False" in code and '"state": "SKIPPED"' in code)
    chk("③ 零九頭龍:三道擷取與 LAYOUT 標註都**讀 ENG072 的 sidecar**,不重抽",
        "first_page_text" in code and "heads" in code and "compare" in code
        and "pdfplumber" not in code and "fitz" not in code)

    sc = {"header": "兆豐證券", "right": "目標價 1000", "footer": "第 7 頁",
          "body": "本次會議共 10 段。\n1 Action Items 行動項目#行動負責人期限1 燈號要補重試計數。\n"
                  "我們決定維持 PDF 流程。",
          "heads": [{"text": "1 Action Items 行動項目", "size": 14.0, "level": "H3"}],
          "tables": [[["#", "行動", "負責人", "期限"]]],
          "logic": {"method": "DUAL_ZONES"}, "triage": {"state": "DIGITAL"}}
    r = restore(sc, "夾具")
    kinds = {x["kind"] for x in r["rows"]}
    chk("④ 四類都標得出來(標題/表/本文/其他)",
        {"標題", "表", "本文", "其他"} <= kinds, str(sorted(kinds)))
    chk("⑤ 頁數讀頁尾的「第 N 頁」,不是猜的",
        r["page"] == 7 and "頁尾" in r["page_why"], f"(p{r['page']} · {r['page_why']})")
    chk("⑥ 判不出頁數要**說判不出來**,不編號碼",
        page_of({})[0] is None and "不編" in page_of({})[1])
    _h = [x for x in r["rows"] if x["kind"] == "標題"]
    chk("⑦ 黏在行首的標題要切出來,而且層級用 LAYOUT 給的(不是自己猜)",
        len(_h) == 1 and _h[0]["sub"] == "H3" and _h[0]["text"] == "1 Action Items 行動項目",
        str([(x["sub"], x["text"][:20]) for x in _h]))
    _t = [x for x in r["rows"] if x["kind"] == "表"]
    chk("⑧ **本文與表格黏在一起的那一段要標成表**(操作員點名的病):"
        "`#行動負責人期限…` 在 tables 裡對得上格子,標成表格殘片——**但不刪**",
        any(x["sub"] == "表格殘片" for x in _t) and any(x["sub"] == "表頭" for x in _t),
        str([x["sub"] for x in _t]))
    _b = [x for x in r["rows"] if x["kind"] == "本文"]
    chk("⑨ 一句一行:句末標點才斷,換行不斷"
        "(研報的換行多半是版面折行;拿它斷會把一句切三行,SUMMARIZE 就讀成三件事)",
        all(x["text"][-1] in _SENT_END for x in _b) and len(_b) >= 2,
        str([x["text"][:16] for x in _b]))
    chk("㊀ **不刪除**:來源非空白字元保全率 100%。"
        "「修好」如果是靠丟掉修不動的那幾段換來的,那不是修好",
        r["keep"]["rate"] is not None and abs(r["keep"]["rate"] - 100.0) < 1e-9,
        f"(保全 {r['keep']['rate']:.2f}% · 來源 {r['keep']['src_chars']} 字 · "
        f"掉 {r['keep']['lost_chars']}{' · ' + str(r['keep']['lost_sample']) if r['keep']['lost_chars'] else ''})")
    # 夾具左行要**夠長**才會觸發折行接回——批637 加了長度護欄之後,
    #   `中`+換行 本來就不該接(短行後面是真的換行)。夾具跟著契約走。
    fixed, rep = repair_text("這是一行被行寬切斷的長句子中\n文  斷行​與　間隔")
    chk("⑪ 修斷行與間隔:去零寬 · 全形空白換半形 · CJK 硬斷接回 · 壓連續空白,"
        "**而且每一種都記次數**(修了什麼要說得出來)",
        rep["zw"] == 1 and rep["fullwidth_space"] == 1 and rep["joins"] == 1
        and "中文" in fixed and "​" not in fixed, f"{rep}")
    chk("⑫ 英數中間的硬斷**不接**(接了會黏成錯字:`Q2\\n2025` → `Q22025`)",
        repair_text("Q2\n2025")[1]["joins"] == 0)
    md = to_markdown(r)
    chk("⑬ MD 每一行都帶著它是什麼(類別/次類別/頁),AI 讀得出來",
        md.count("<!-- 標題/H3") == 1 and "<!-- 表/表頭" in md and "<!-- 本文/句" in md
        and "保全率 100.00%" in md, f"({len(md)} 字)")
    chk("⑭ 類別冊是分類的唯一出處:每一個用到的類別都在 KINDS 裡,"
        "次類別也在它的 subs 裡(加一類沒進冊,它就只活在程式裡——LL207 同族)",
        all(x["kind"] in KINDS and x["sub"] in KINDS[x["kind"]]["subs"] for x in r["rows"]),
        str([(x["kind"], x["sub"]) for x in r["rows"] if x["kind"] not in KINDS
             or x["sub"] not in KINDS.get(x["kind"], {}).get("subs", [])] or "全在冊"))
    _n = split_sentences("決議1.\nMDL010 已接上。\n2.\n維持 PDF 流程。")
    chk("⑰ **光禿禿的編號不是一句**:`1.` `2.` 被句末的 `.` 切成獨立一行之後,"
        "「一句一行」就變成「一個號碼也一行」,而 SUMMARIZE 會把它讀成一件事。"
        "編號要黏回它後面那一句(實測 VRN_Meeting_Minutes 一份就生了 5 行這種)",
        # 斷言是 3 不是 2——我第一版寫 2,而正確結果是
        #   `決議1.` / `MDL010 已接上。` / `2. 維持 PDF 流程。`。
        #   **檢寫錯的時候先懷疑檢**:這裡碼是對的,錯的是我算錯句數。
        not any(_BARE_NUM.fullmatch(x) for x in _n) and len(_n) == 3
        and _n[-1].startswith("2. "),
        str(_n))
    _mid = restore({"body": "前言一段。標題在中間後面還有話。",
                    "heads": [{"text": "標題在中間", "size": 20.0, "level": "H1"}]}, "行中")
    _mk = [(x["kind"], x["sub"], x["text"]) for x in _mid["rows"]]
    chk("⑱ 標題黏在**行中**也要切出來(不只行首)。實測:"
        "`…會議紀錄VRN Fetch v4 — 設計審查會議日期…` 裡那個 H1 卡在中間,只比行首抓不到"
        "——跟表格殘片同一種病:黏在哪裡都要找得回來。而且**前面那一段不可以丟**",
        any(k == "標題" and t == "標題在中間" for k, _, t in _mk)
        and any(k == "本文" and "前言一段" in t for k, _, t in _mk)
        and abs(_mid["keep"]["rate"] - 100.0) < 1e-9,
        str(_mk))
    # ⑲ 夾具要**造得出那個坑**:標題在 heads 裡是乾淨的,body 裡卻夾著零寬——
    #   正規化對得上、字面對不上。我第一版在這種情況照 len(標題) 硬切,
    #   保全率在真資料上從 100% 掉到 96.97%,而**夾具太小沒照出來**。
    _zwv = restore({"body": "前面一段話。標\u200b題\u200b在中間後面還有話。",
                    "heads": [{"text": "標題在中間", "size": 20.0, "level": "H1"}]}, "零寬")
    chk("⑲ 正規化對得上、**字面對不上就不切**:原字裡夾著零寬的時候,"
        "照 `len(標題)` 硬切會砍掉沒對上的字。留一行完整的,比切壞一行好"
        "——保全率仍須 100%",
        abs(_zwv["keep"]["rate"] - 100.0) < 1e-9 and _zwv["keep"]["lost_chars"] == 0,
        f"(保全 {_zwv['keep']['rate']:.2f}% · 掉 {_zwv['keep']['lost_chars']})")
    # ══ 批637 補六檢:字級×粗體判級 · 剔除區 · 大標題帶代號 ══
    _g = {"gle": {"body_font": 10.0, "elements": [
              {"zone": "TC", "bold": "True", "size": "25.0", "head": "台積電 2330 買進 目標價 1200"},
              {"zone": "TL", "bold": "True", "size": "14.0", "head": "投資論點"},
              {"zone": "ML", "bold": "False", "size": "10.0", "head": "先進製程需求強勁。"},
              {"zone": "BC", "bold": "False", "size": "8.0", "head": "本報告僅供參考 第 3 頁"},
              {"zone": "ML", "bold": "True", "size": "20.0", "head": "另一個大字標題"}]},
          "footer": "本報告僅供參考 第 3 頁",
          "body": "台積電 2330 買進 目標價 1200\n投資論點\n先進製程需求強勁。\n另一個大字標題"}
    _r = restore(_g, "字級夾具")
    _lv = [(x["sub"], x["text"][:12]) for x in _r["rows"] if x["kind"] == "標題"]
    chk("⑳ 字級 × 粗體判大中小標題(門檻是**相對 body_font 的倍率**不是絕對字級"
        "——每一家研報內文字級都不一樣,寫絕對值換一家就全錯)",
        # 斷言用 startswith,不寫死切片長度——我第一版把 12 字切片算錯,
        #   碼是對的、檢是錯的(**檢紅的時候先懷疑檢**)。
        any(a == "H1" and b.startswith("台積電") for a, b in _lv)
        and any(a == "H2" and "投資論點" in b for a, b in _lv),
        str(_lv))
    chk("㉑ **標題沒有句號**(操作員點名的訊號):`先進製程需求強勁。` 字級等於內文又帶句號,"
        "是本文不是標題",
        any(x["kind"] == "本文" and "先進製程" in x["text"] for x in _r["rows"]),
        str([(x["kind"], x["text"][:10]) for x in _r["rows"] if "先進" in x["text"]]))
    chk("㉒ **大標題只留帶股票代號的那一句**(批637 指名):兩個大字候選,"
        "`台積電 2330…` 帶代號留 H1,`另一個大字標題` 降 H2——不是誰字大誰贏",
        sum(1 for a, _ in _lv if a == "H1") == 1
        and any(a == "H2" and "另一個大字" in b for a, b in _lv),
        str(_lv))
    _dr = [x for x in _r["rows"] if x["kind"] == "剔除"]
    chk("㉓ 小字體 + 版面下緣 = 頁尾,剔除(操作員令);"
        "`本報告僅供參考` 同時是附錄起點詞,兩條規則都指向剔除",
        any("頁尾" in x["sub"] or "附錄" in x["sub"] for x in _dr),
        str([(x["sub"], x["text"][:14]) for x in _dr]))
    chk("㉔ **剔除不是消失**:剔除段不進本文主體、不進 SUMMARIZE,"
        "但留在檔尾剔除區並寫出理由;保全率仍是「留用 + 剔除 = 100%」"
        "(批636 的不刪除與批637 的刪除,兩條令都成立)",
        abs(_r["keep"]["rate"] - 100.0) < 1e-9
        and "## 剔除區(不進 SUMMARIZE)" in to_markdown(_r)
        and all(x["text"] not in summarize_input(_r) for x in _dr),
        f"(保全 {_r['keep']['rate']:.2f}% · 剔除 {len(_dr)} 段)")
    chk("㉕ 沒有 gle 就**不假裝判得出字級**:body_font 缺席時不推層級、不剔除"
        "(判不出來要說判不出來,不是給一個看起來很確定的答案)",
        gle_index({})[1] is None and level_of({"size": 99, "bold": True}, None) == ""
        and drop_of({"size": 1, "zone": "BC"}, None, True) == {})
    # ══ 批639 補五檢:第二把尺 ══════════════════════════════════════
    _h = nlp_hub()
    import ast as _ast_mod
    _imp = set()
    for _n in _ast_mod.walk(_ast_mod.parse(Path(__file__).read_text(encoding="utf-8"))):
        if isinstance(_n, _ast_mod.Import):
            _imp |= {a.name.split(".")[0] for a in _n.names}
        elif isinstance(_n, _ast_mod.ImportFrom):
            _imp.add((_n.module or "").split(".")[0])
    chk("㉖ 第二把尺走**既有的 SUP_MDL744 NLP 橋**,不另開 import 路,"
        "也不自己再造一個版面分析器(Zero-Hydra)。"
        "**判準用 AST 查真的 import,不用字串找詞**——第一版用字串,"
        "而我自己那段說明註解裡就有這個詞,第五次檢比到自己"
        "(而且是在我剛寫完 LL257 之後)。字串分不出「程式在 import 它」"
        "和「註解在講它」,AST 分得出來",
        "SUP_MDL744" in code and "layout_analysis" not in _imp,
        f"(橋 {'在' if _h else '缺席'} · import 數 {len([x for x in _imp if x])})")
    _md = to_markdown(_r)
    _xc = layout_crosscheck(_r, _md)
    chk("㉗ 橋缺席要回 **ABSENT 並說出來**——「沒量到」和「量過了一致」是兩件事",
        _xc["state"] in ("OK", "ABSENT", "NODATA")
        and (_xc["state"] != "ABSENT" or "沒量到" in _xc["why"]),
        f"({_xc['state']} · {_xc['why'][:30]})")
    chk("㉘ 對照表不可以太窄:`1. 某某句子` 這種**既是本文也是編號清單**,"
        "兩把尺都對。窄對照會把「兩個都對」判成「對不上」——那是假紅,"
        "而假紅跟假綠一樣傷(實測 149 塊對不上裡 142 塊是我的尺錯)",
        {"ordered_list", "unordered_list"} <= KIND_TO_BLOCK["本文"]
        and "paragraph" in KIND_TO_BLOCK["表"])
    chk("㉙ 表頭後面要補 `|---|` 分隔列,不然**不是合法 Markdown 表格**,"
        "第二把尺會判成 paragraph",
        any(set(x.strip()) <= {"-", "|", " "} and "-" in x
            for x in _md.split("\n")) or not any(
            x["sub"] == "表頭" for x in _r["rows"]),
        "表頭有就要有分隔列")
    _multi = restore({"header": "第一行\n第二行\n第三行", "body": "一句話。"}, "多行頁首")
    _mm = to_markdown(_multi)
    chk("㉚ 周邊資訊區**每一行都要加 `>`**:原文帶換行時只引第一行,"
        "後面幾行會脫離引用區被判成標題或清單(實測 23 塊對不上全是這一種)",
        all(x.startswith(">") for x in _mm.split("\n")
            if x.strip() and ("第二行" in x or "第三行" in x)),
        str([x[:14] for x in _mm.split("\n") if "第" in x]))
    _fakerows = [{"xcheck": {"rows": [
        {"eng085": "本文/句", "analyzer": "table/表格", "text": "某一句話"},
        {"eng085": "本文/句", "analyzer": "table/表格", "text": "另一句"},
        {"eng085": "表/表頭", "analyzer": "paragraph/段落", "text": "A | B"}]}}]
    _pp = disagree_pairs(_fakerows)
    chk("㉛ 對不上的要**當場印成對統計**,不是叫人去 grep manifest。"
        "工作站實跑 105 份報「對不上 30 塊」,而那 30 塊只有他的機器上有"
        "——哨兵抓到就要給得出下一步(L92)。"
        "(容器零分歧,所以這一段在容器裡走不到,抽成函式才驗得了 L83)",
        len(_pp) == 2 and _pp[0][2] == 2 and _pp[0][0] == "本文/句"
        and _pp[0][3] == "某一句話" and disagree_pairs([]) == [],
        str([(a, b, n) for a, b, n, _ in _pp]))
    # ㉜ 批650:**測了那支函式,沒測呼叫它的那一行**。
    #   檢 ㉛ 拿假資料驗過 disagree_pairs,而 v0103 的 main() 餵給它的是 `ok`
    #   —— 那是 run() 的區域變數,main() 裡根本不存在。這一行只有「二尺對不上」時才跑,
    #   容器一致 380/380 永遠走不到,操作員的機器 1093/1123 第一次走到就 NameError。
    #   所以這一檢不測函式,測**整段畫面**:餵一個有分歧的 res 走完全程。
    _res_dis = {"n": 3, "ok": 3, "fail": 0, "keep_min": 100.0, "keep_all_100": True,
                "tables_rows": 0, "out": "/tmp/x", "db": {"state": "SKIPPED"},
                "xcheck": {"measured": 3, "absent": 0, "agree": 7, "disagree": 3},
                "rows": _fakerows}
    try:
        _lines = render_run(_res_dis)
        _crash = ""
    except Exception as _e:                                   # noqa: BLE001
        _lines, _crash = [], f"{type(_e).__name__}: {_e}"
    _res_ag = dict(_res_dis, xcheck={"measured": 3, "absent": 0, "agree": 10, "disagree": 0})
    _lines_ag = render_run(_res_ag)
    chk("㉜ **有分歧時的那一段畫面要真的被跑過**(v0103 在這裡 NameError,"
        "因為容器零分歧、那一行從沒執行過;檢 ㉛ 測了函式,沒測呼叫它的那一行)"
        "+ 負控:零分歧時不得印成對統計",
        not _crash
        and any("成對統計" in x for x in _lines)
        and any("本文/句" in x for x in _lines)
        and not any("成對統計" in x for x in _lines_ag),
        _crash or f"(分歧 {len(_lines)} 行 · 零分歧 {len(_lines_ag)} 行)")
    chk("⑮ 夾不在=ABSENT 且講得出下一句(去跑 ENG072)· 空夾=NODATA",
        run("/no/such/dir")["state"] == "ABSENT" and "ENG072" in run("/no/such/dir")["why"])
    _e = restore({}, "空")
    chk("⑯ 空 sidecar:零行、保全率不給數字(沒有分母就不給比率),不當成 100%",
        _e["n_rows"] == 0 and _e["keep"]["rate"] is None,
        f"(rate={_e['keep']['rate']})")
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}(檢數現場計)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VRN_ENG085_MarkdownRestore",
                                 description="本文還原與分類標註(零網路;預設不寫庫)")
    ap.add_argument("verb", nargs="?", default="run", choices=["run", "one"])
    ap.add_argument("--in", dest="indir", default="", help="sidecar 夾(預設 VIA_Reports/first_page_text)")
    ap.add_argument("--file", default="", help="單一 sidecar.json")
    ap.add_argument("--apply", action="store_true", help="表格入庫(預設不寫)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.verb == "one":
        if not a.file:
            print("  [絕] one 要給檔:--file <sidecar.json>")
            return 1
        p = Path(a.file)
        if not p.exists():
            print(f"[VRN_ENG085 v{VERSION}] one · ABSENT · 檔不在:{p}")
            return 3
        r = restore(json.loads(p.read_text(encoding="utf-8-sig")), p.stem)
        OUT.mkdir(parents=True, exist_ok=True)
        q = OUT / f"{p.stem}.md"
        q.write_text(to_markdown(r), encoding="utf-8")
        print(json.dumps({k: v for k, v in r.items() if k != "rows"}, ensure_ascii=False)
              if a.json else
              f"[VRN_ENG085 v{VERSION}] one · {p.stem} · 行 {r['n_rows']} · "
              f"{r['by_kind']} · 保全 {r['keep']['rate']:.2f}% · 頁 {r['page']} → {q}")
        return 0
    res = run(a.indir, a.apply)
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res["state"] == "OK" else {"NODATA": 2, "ABSENT": 3}.get(res["state"], 1)
    if res["state"] != "OK":
        print(f"[VRN_ENG085 v{VERSION}] run · {res['state']} · {res['why']}")
        return {"NODATA": 2, "ABSENT": 3}.get(res["state"], 1)
    for _ln in render_run(res):
        print(_ln)
    return 0 if res["keep_all_100"] is not False else 1


if __name__ == "__main__":
    sys.exit(main())

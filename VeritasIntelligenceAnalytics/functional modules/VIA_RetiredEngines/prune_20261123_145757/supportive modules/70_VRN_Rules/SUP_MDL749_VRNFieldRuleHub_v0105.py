#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
v0104→v0105(批563 操作員「同意」接收容冊的 MOPS 判定規則)
  收容冊 `VRN_AnnualExtract_SSOT_v0100.json` 的 `note` 裡有四條**判定規則**(不是詞):
      「MOPS 認明『合計』;應收/存貨取『淨額』;權益與 ROE/BVPS 以
        『歸屬於母公司業主之權益』為準;稀釋 EPS 為主」
  這四條的價值可能比所有詞表加起來大——因為它們修的不是「抓不到」,是**抓錯一個看起來對的數字**。
  量出來的缺口:ENG074 的 `parse_data_row` 把「淨額/合計/總額/總計」當**雜訊字尾剝掉**去對正典名
  (對映本身沒錯),但下游 `rows.append` **沒有去重也沒有優先序**——
  同一份財報頁同時有「權益總計」與「歸屬於母公司業主之權益總計」時,兩列都進去,
  誰先誰後決定了 ROE 與 BVPS 的分母。**那是一個不會報錯、只會安靜算錯的位置。**
  本樞紐提供 `mops_rank(raw_label, canonical)`:回 (名次, 為什麼),名次高者為準。
  實作放這裡不放引擎裡(Zero-Hydra),而且**只排名不刪列**(只增不減)——
  輸給別人的那一列照樣留著,只是帶著名次與理由,由呼叫端取 max。
v0103→v0104(批562 操作員裁示「SSOT 只增不減除非衝突」+ 上傳 VRN_Rating_Dict 等 19 件收容冊)
  評等詞彙從兩源變**三源**:收容件字典 ∪ 本土尺度 ∪ **操作員收容冊**(VRN_Rating_Dict)。
  量出來的事實:冊 38 詞 vs 正本 38 詞,**交集只有 19**——不是重複是互補。
  冊補的是「未評等」整族(未評等/未評級/無評等/暫無評等/NR/N/A/No Rating/Not Rated)
  與「強力賣出/Strong Sell」(正本有強力買進卻沒有對稱的賣出端);
  正本補的是批538 在 64 份真研報打出來的本土尺度。聯集 57 詞。
  **衝突只有 2 個**(量的,不是猜的):`Accumulate` / `Add`——冊判 BUY,正本判 ADD,
  同一別名對到兩個正典名 → 依操作員裁示「除非衝突」**排除這 2 個,正本的 ADD 保留**。
  「只增不減」不等於「照單全收就開判」:冊裡的 `賣超`(籌碼用語,外資賣超≠SELL)、
  `Long`(部位方向)、`推薦`、`平衡`、`觀望`、`避免` 都**收進詞表**,
  但要命中必須過**線索詞閘**(評等/評級/建議/Rating/…)或整行等於,再過上下文否決。
  詞進 SSOT 是一回事,判不判是另一回事——批540/554/558 已經量過三次:
  光補詞彙不補守衛就是製造假評等。
v0102→v0103(批558 操作員令「加入同義字 第一頁周圍訊息區塊及中間本文標題區修復後尋找」)
  同義字補齊之後,下一個問題是**在哪裡找**。操作員點名兩個區:
    ① **第一頁周圍訊息區塊** = 頁首帶 / 右資訊區 / **頁尾**。
       量出來的事實:ENG073 的 `text_all` 從批237 起就只 join `header+right+body`,
       **`footer` 這一區從來沒有被搜過**——目標價、評等、代碼全都看不到頁尾。
       這不是設計取捨,是一個 join 漏了一個鍵,而且六百多行外的另一處 join 是有 footer 的。
    ② **中間本文標題區** = 本文裡的章節標題行(【】■◆● 一、 1. 第N節 …、短行不收句尾標點)。
       研報常把「評等:增加持股」「目標價 250 元」寫在段落標題上,而不是資訊欄裡。
  兩區都**修復後尋找**(斷行修復:標籤與值被換行切開時先接回來,批239b 的做法)。
  實作放這裡不放各引擎裡:`repair` / `headings` / `info_block` 三個公用件,
  之後接 首頁全能 與 TW02 時拿同一份(Zero-Hydra;四支各寫一份標題偵測=四個會漂的真相)。
v0101→v0102(批554 操作員令「目標價 目標 target price price target target」+「評等以同義字為主」)
  ① **目標價同義字的正本在哪**——量出來的答案是:不在我這本規則冊裡。
     機構 SSOT(VIA_Financial_Institution_SSOT #registries.research_fields.TARGET_PRICE.aliases)
     有 **16 條**(Target Price/Price Target/TP/PT/Target/Tgt/Fair Value/FV/Valuation/
     目標價/目標股價/目標/合理價/合理股價/預期價/目標區間),ENG073 早就在讀它;
     而正本實作 ENG086 與本冊只認 **5 條**(目標價/Target Price/Price Target/TP/PT)。
     操作員點名的「目標 / target」正好落在那 11 條差裡。
     修法不是把 16 條抄進規則冊(第二顆頭),是**本樞紐直接讀機構 SSOT 那一本**——
     同義字一個出處(L30),`tp_terms()` 就是那個唯一讀冊口。
  ② `tp_of` 加**第二道**:正本實作(5 條強線索)判不出時,才用加寬的 11 條試,
     且守衛不自己寫——轉交 ENG086 的 `_is_upside_context`(LL64 幅度不是價格)
     與 `_plausible_tp`,並額外要求加寬詞**貼著數字**。回傳的 how 說明走了哪一道,
     弱道就寫明是弱道(不冒充強線索)。
  ③ `drift` 加目標價維度:誰認得 16 條裡的幾條,當場量給你看(評等那一半的對稱物)。
v0100→v0101(批541 操作員令「去衝突 SSOT 同義字 · 邊實測邊更新同義字」)
  +`conflicts` —— 去衝突量尺:合併後同一別名對到多個正典名 = 衝突(下游一 join 就散),必須是 0。
  +`harvest`  —— **邊實測邊長同義字**的那一半:拿真語料跑一輪,把「該有卻沒命中」的欄位旁邊的
                 候選詞撈出來,附檔名與證據行,標 PENDING_OPERATOR。
                 **只提候選,絕不自己寫進正本冊**(不代設;正本要長,是你點頭那一刻才長)。
SUP_MDL749_VRNFieldRuleHub v0100 — VRN 研報六欄規則正本樞紐(批540)

操作員令:「有相同邏輯 相同規則 整合去重 · 有錯誤一起討論 · 類似引擎邏輯整合後只增不減 ·
任何邏輯不影響現在功能為主 · 不要傷害系統 不要九頭龍風險」

為什麼要有這一支
  研報六欄(券商 / 評等 / 目標價 / 財報 / email / 電話)的規則今天散在四支**現役**引擎裡,各有各的版本:
      ENG086 第一頁橋 v0102   評等詞 35  ← 64 份真研報上打出來的,批537/538 逐條驗過
      ENG073 報告結構庫 v0127  評等詞 29  ← 少「增加持股/減少持股/優於大盤系列」
      TW02 報告解析器 v0101    評等詞 24  ← 再少「區間操作/逢低/持有評等」
      首頁全能引擎 v0125       評等詞 13  ← **英文評等全缺**(Buy / Neutral / Outperform / Sell…)
  同一件事四套規則,就是四個會各自漂移的真相。凱基寫「增加持股」時 ENG086 讀得到、ENG073 讀不到;
  外資寫「Buy」時首頁全能引擎讀不到——這不是假設,是本檔 `drift` 動詞當場量給你看的。

這一支怎麼做(關鍵:**不改任何現役引擎**)
  ① 正本冊 VRN_FieldRules_SSOT_v0100.json:把**已驗過的那一套**(ENG086 v0102)立為正本並鎖住。
  ② 本樞紐 = 唯一讀冊口(L30 一功能一主):要規則的人跟這裡拿,不要再各自抄一份。
  ③ `drift` 動詞:掃現役引擎,逐條列出「正本有、它沒有」的規則——**先看得見,再由你決定誰改**。
  ④ 本批**零改線**:engines 照舊跑、行為一位元都沒變(只增不減 · 不影響現有功能 · 零九頭龍)。
     整合的第一步是把真相收斂到一處,不是急著動刀。

律:L30 一功能一主 · L57 誠實分母 · L59 已修複驗 · 只增不減 · 正本零觸碰 · 零網路

用法:python3 SUP_MDL749_VRNFieldRuleHub_v0100.py [rules|drift|status] [--json] | --selftest
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
except Exception:
    pass
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SSOT = VIA / "supportive modules" / "registry" / "VRN_FieldRules_SSOT_v0100.json"

# 現役研報欄位擷取引擎(尾版 glob;不釘版號 L54)
# fields = 這支**真的在抽**哪些欄位——不抽評等的引擎拿評等去量它,就是替它點一盞判錯的紅燈(L57)。
CONSUMERS = (
    ("ENG086 第一頁邏輯橋", "functional modules/VRN", "VRN_ENG086_FirstPageLogicBridge_v*.py", True,  ("rating", "target_price", "broker", "date")),
    ("ENG073 報告結構庫", "functional modules/VRN", "VRN_ENG073_ReportStructuredDB_v*.py", False, ("rating", "target_price", "broker")),
    ("TW02 報告解析器", "functional modules/VRN", "VRN_TW02_ReportParser_v*.py", False, ("rating", "target_price", "broker")),
    ("首頁全能引擎", "functional modules/VRN", "VIA_VRN_FirstPageEngine_v*.py", False, ("rating", "target_price", "broker", "date")),
    ("ENG080 四點文摘", "functional modules/VRN", "VRN_ENG080_FourPointDigest_v*.py", False, ("target_price",)),
)
HUB_MARK = "SUP_MDL749_VRNFieldRuleHub"      # 批554:委由本樞紐=整套規則連守衛一起繼承(不必也不該再抄詞表)
#: 批554:目標價同義字冊的印記。**要兩個印記同時在**才算真的讀了那本冊——
#: 我第一版只認 "TARGET_PRICE",結果 TW02 印出目標價 16/16:它那個字串是自己的變數名
#: `TARGET_PRICE_SYNONYMS`(寫死 4 條),根本沒讀冊。一個字面印記就能給出假綠,
#: 這已經是同一家族的第三次(LL85 我的尺子錯了)——所以印記要釘在**冊名**上,不是釘在欄位名上。
TP_DICT_MARK = ("VIA_Financial_Institution_SSOT", "TARGET_PRICE")
DICT_MARK = "BrokerRatingDict"      # 載入收容件評等字典的印記:有它就自動擁有 canon_map 那 24 個詞


def _newest(rel_dir: str, glob: str) -> Path | None:
    hits = sorted((VIA / rel_dir).glob(glob))
    return hits[-1] if hits else None


def rules() -> dict:
    """正本規則冊。冊不在=誠實 ABSENT(不編)。"""
    if not SSOT.is_file():
        return {"state": "ABSENT", "why": f"規則正本冊不在:{SSOT.name}", "rules": {}}
    try:
        d = json.loads(SSOT.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"state": "RED", "why": f"規則冊讀不動:{type(exc).__name__}", "rules": {}}
    d["state"] = "OK"
    return d


#: 批562:操作員收容冊(尾版 glob;缺=不編,三源退兩源)
INTAKE_RATING_GLOB = "functional modules/VRN/references/intake/**/VRN_Rating_Dict_v*.json"
#: 冊的分組名 → 正典名
_GRP2KEY = {"strong_buy": "BUY", "buy": "BUY", "hold": "HOLD",
            "sell": "SELL", "strong_sell": "SELL", "not_rated": "NOT_RATED"}


def _intake_map() -> dict:
    """收容冊那一半(批562)。回 {別名: 正典名};冊缺=誠實空 dict(不編)。"""
    import json as _json
    hits = sorted(VIA.glob(INTAKE_RATING_GLOB))
    if not hits:
        return {}
    try:
        d = _json.loads(hits[-1].read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for g, ws in (d.get("keyword_sets") or {}).items():
        k = _GRP2KEY.get(g)
        if not k or not isinstance(ws, list):
            continue
        for w in ws:
            w = str(w).strip()
            if w:
                out[w] = k
    return out


def _canon_of_alias() -> dict:
    """正本那兩源的 {別名小寫: {正典名}}(拿來驗衝突)。"""
    r = rules().get("rules", {}).get("rating", {}) or {}
    a2k = {}
    for k, al in (r.get("canon_map") or {}).items():
        for a in al:
            a2k.setdefault(str(a).lower(), set()).add(k)
    for a, k in (r.get("local_scale") or {}).items():
        a2k.setdefault(str(a).lower(), set()).add(k)
    return a2k


def intake_conflicts() -> dict:
    """批562:收容冊 × 正本的**撞名**——同一別名對到不同正典名。
    操作員裁示「SSOT 只增不減**除非衝突**」,所以撞名的那幾個是唯一該被排除的。
    實測本冊撞名 2 個:Accumulate / Add(冊 BUY vs 正本 ADD)。"""
    a2k, out = _canon_of_alias(), {}
    for w, k in _intake_map().items():
        ex = a2k.get(w.lower())
        if ex and k not in ex:
            out[w] = {"intake": k, "canon": sorted(ex)}
    return out


def intake_words() -> dict:
    """收容冊裡**沒有衝突**的那些(可以進 SSOT 的);撞名者依裁示排除。"""
    bad = set(intake_conflicts())
    return {w: k for w, k in _intake_map().items() if w not in bad}


def rating_words() -> list:
    """正本評等詞彙 = 收容件 canon_map ∪ 本土尺度 ∪ **操作員收容冊**(批562 三源)。
    只增不減:三源聯集;除非衝突:撞名者(Accumulate/Add)排除,正本的判定保留。"""
    return sorted(set(_dict_words()) | set(_local_words()) | set(intake_words()))


def _dict_words() -> list:
    """收容件字典那一半(載入 BrokerRatingDict 就自動有,不必寫在自己檔裡)。"""
    r = rules().get("rules", {}).get("rating", {}) or {}
    out = set()
    for v in (r.get("canon_map") or {}).values():
        out.update(v)
    return sorted(out)


def _local_words() -> list:
    """本土尺度那一半(批538 在 64 份真研報上打出來的;要寫在自己檔裡才算有)。"""
    return sorted((rules().get("rules", {}).get("rating", {}) or {}).get("local_scale") or {})


def tp_cues() -> list:
    return list((rules().get("rules", {}).get("target_price", {}) or {}).get("cue_rx") or [])


#: 正本實作 ENG086 認得的 5 條強線索(拿來算「加寬的是哪幾條」,不是拿來判定)
TP_STRONG = ("目標價", "Target Price", "Price Target", "TP", "PT")


def tp_terms() -> tuple:
    """目標價同義字的**唯一讀冊口**(批554)。

    冊在 `supportive modules/ssot/VIA_Financial_Institution_SSOT_v*.json`
    的 `registries.research_fields.TARGET_PRICE.aliases`——ENG073 v0121 起就在讀它,
    本樞紐與正本實作 ENG086 卻各自只認 5 條。**同義字有中央冊、引擎各讀各的**,
    就是這一家族所有漂移的同一個病。這裡不抄那 16 條,直接讀那一本。
    回 (詞表, 出處說明);冊缺=誠實退回 5 條強線索並講明走了退路(不假裝綁了冊)。
    """
    import json as _json
    d = VIA / "supportive modules" / "ssot"
    try:
        hits = sorted(d.glob("VIA_Financial_Institution_SSOT_v*.json"))
        if not hits:
            return TP_STRONG, "機構 SSOT 冊缺=退 5 條強線索"
        reg = _json.loads(hits[-1].read_text(encoding="utf-8")).get("registries") or {}
        al = ((reg.get("research_fields") or {}).get("TARGET_PRICE") or {}).get("aliases")
        if not al:
            return TP_STRONG, f"冊在但無 TARGET_PRICE 別名({hits[-1].name})=退 5 條強線索"
        terms = tuple(sorted({str(x).strip() for x in al if str(x).strip()},
                             key=len, reverse=True))      # 長詞先試:目標股價 不可被 目標 先吃掉
        return terms, f"機構 SSOT {hits[-1].name} · {len(terms)} 條"
    except Exception as exc:
        return TP_STRONG, f"讀冊失敗 {type(exc).__name__}=退 5 條強線索"


def tp_wide_terms() -> list:
    """加寬的那幾條(16 − 5);操作員點名的「目標 / target」就在這裡。"""
    terms, _ = tp_terms()
    low = {t.lower() for t in TP_STRONG}
    return [t for t in terms if t.lower() not in low]


#: 加寬詞與數字之間**允許**出現的中文(只有這幾個字才算連接詞;
#: 「目標市場規模 2026」的『市場規模』不在其中=那個 `目標` 不是價格標籤)
_TP_GAP_OK = "約為上看估預區間至到目標價位"
#: 數字後面**緊接**這些=不是價格:百分比、倍數、折數、年份標記
_TP_NOT_PRICE_AFTER = "%％xX倍折年"


def _tp_wide_rx():
    """加寬詞的正則。加寬詞本來就弱,守衛要比強線索**更緊**,不是更鬆:
      · 拉丁短詞加詞界(Target 不吃 Targeted);中文不加(中文沒詞界,加了反而不匹配)
      · 詞與數字之間最多 6 個字元,且不得夾雜白名單以外的中文
      · 數字後面(容一個空白)接 % ／ 倍 ／ x ／ 年 = 不是價格——
        空白那一格是量出來的:少了它,「target 2026 年營收成長」照樣判 2026;
        而只補空白還不夠——正則會回溯成「202」再看見『6』就過關,所以還要 `(?![\\d.,])`
        把數字吃乾淨。兩次都是負向對照當場抓到的,不是我想出來的
    這三條全是**量出來的**:第一版只寫「最多 20 個非數字字元」,負向對照當場抓到四筆誤抓——
    「目標市場規模 2026 年上看 100 億」判 2026、「Valuation is undemanding at 15x」判 15、
    「target 2026 年營收成長」判 2026、「毛利率目標 45%」判 45。
    加寬同義字如果不配上加緊的守衛,補進來的不是命中率,是假目標價(批540 在評等那邊量過同一件事)。
    """
    import re as _re
    ws = tp_wide_terms()
    if not ws:
        return None
    alt = "|".join((r"\b" + _re.escape(t) + r"\b") if _re.fullmatch(r"[A-Za-z][A-Za-z .]*", t)
                   else _re.escape(t).replace(r"\ ", r"\s*") for t in ws)
    gap = r"(?:[^\d\u4e00-\u9fff]|[" + _TP_GAP_OK + r"]){0,6}"
    return _re.compile(r"(?:" + alt + r")" + gap + r"(?:NT\$|新台幣)?\s*"
                       r"([\d,]+(?:\.\d+)?)(?![\d.,])(?!\s*[" + _TP_NOT_PRICE_AFTER + r"])", _re.I)


def broker_tiers() -> list:
    return list((rules().get("rules", {}).get("broker", {}) or {}).get("evidence_tiers") or [])


# ===== 批558:找欄位要在**哪裡找**(周圍訊息區塊 · 中間本文標題區 · 都修復後再找)=====
import re as _re

#: 標題行的起首記號(研報常見)。中文序號「一、」「(一)」也算。
_HEAD_MARK = _re.compile(
    r"^\s*(?:[【\[（(]|[■◆●▲◎※☆★◇□〓▎▌]|"
    r"[一二三四五六七八九十]+\s*[、.·]|第\s*[一二三四五六七八九十\d]+\s*[章節部篇]|"
    r"\d+\s*[、.)）]|\(\d+\)|[IVX]+\s*[.、])")
#: 句尾標點——一行以它結束,多半是敘述句不是標題
_SENT_END = "。．!?!?;;…～~"


def repair(text: str) -> str:
    """斷行修復(批239b 操作員令「文字修復後可抓」;批558 收斂到一處)。
    標籤與值被換行切開——`Target↵price↵NT$165`、`評等↵增加持股`——接回來才找得到。
    只動換行與其周邊空白,不動內容(一個字都不新增)。"""
    return _re.sub(r"\s*\n\s*", " ", text or "")


def headings(text: str, max_len: int = 40, limit: int = 120) -> str:
    """**中間本文標題區**:把本文裡「看起來是標題」的行挑出來,接成一塊給欄位擷取用。

    為什麼要這一區:研報常把「評等:增加持股」「目標價 250 元」寫在段落標題上,
    不在右邊那個資訊欄裡。只掃資訊欄會漏;而整段本文亂掃會撿到敘述句裡的假評等(LL68)。
    標題區是這兩者中間那個剛好的粒度。

    判準(逐條都能反駁,所以逐條寫明):
      · 短 —— strip 後長度 ≤ max_len(標題不會是一整段)
      · 非空、且不是純數字/純標點(那是頁碼與分隔線)
      · 而且滿足其一:有起首記號(【■◆● 一、 1. 第N節 …)、或以「:」「:」結尾、
        或**不以句尾標點結束**(敘述句幾乎都以。結束)
    守衛不在這裡 —— 這裡只負責**縮小範圍**,要不要算評等/目標價仍由 rating_of / tp_of
    的線索詞與守衛決定(L30:範圍歸範圍,判定歸判定,不要在這裡偷做判定)。
    """
    out, n = [], 0
    for ln in (text or "").splitlines():
        t = ln.strip()
        if not t or len(t) > max_len:
            continue
        if not _re.search(r"[\w\u4e00-\u9fff]", t):       # 純標點/分隔線
            continue
        if _re.fullmatch(r"[\d\s.,\-–—/]+", t):            # 純數字=頁碼/日期列
            continue
        if _HEAD_MARK.search(t) or t.endswith((":", "：")) or t[-1] not in _SENT_END:
            out.append(t)
            n += 1
            if n >= limit:
                break
    return repair("\n".join(out))


def info_block(zones: dict) -> str:
    """**第一頁周圍訊息區塊** = 頁首帶 + 右資訊區 + **頁尾**(修復後)。

    `footer` 這一鍵是批558 才補上的:ENG073 的主 join 從批237 起就漏了它,
    於是頁尾的目標價/評等/代碼一直是**看不見**的。缺鍵不會報錯,只會安靜地少一區——
    這種漏最難發現,因為它長得跟「那裡本來就沒東西」一模一樣。
    """
    return repair("\n".join(str((zones or {}).get(k, "") or "")
                            for k in ("header", "right", "footer")))


_M = {"mod": None, "why": ""}


def matchers() -> tuple:
    """**惰性**取回已驗過的那一套判定函式本體(不是只給詞表,是給實作)。

    整合去重的重點在這裡:與其讓每支引擎各自抄一份詞表 + 各自寫一套判法,
    不如讓大家跟這裡拿**同一個實作**——ENG086 v0102 在 64 份真研報上打出來的那一套,
    連它踩過的坑一起繼承:
      · rating_local_scale(text, lines=40) —— 只看前段。內文的「外資持有」「增持庫藏股」不是評等(LL68),
        光補詞表不補這條守衛,補進去就是製造假評等。
      · _is_upside_context() —— 目標價 ≠ 潛在上漲空間(LL64)。
      · safe_broker_ev() —— 券商證據分級:文內(去電郵/網址)> 檔名 > 電郵網域(弱)(LL66/LL67)。
    惰性載入:import 這支樞紐時**不會**碰任何引擎;真的要用才載(缺=誠實 ABSENT)。
    """
    if _M["mod"] is None:
        eng = _newest("functional modules/VRN", "VRN_ENG086_FirstPageLogicBridge_v*.py")
        if eng is None:
            _M["why"] = "正本實作缺:VRN_ENG086_FirstPageLogicBridge_v*.py"
            return None, _M["why"]
        try:
            import importlib.util as _il
            sp = _il.spec_from_file_location("_vrn_rule_impl", eng)
            mod = _il.module_from_spec(sp)
            sp.loader.exec_module(mod)
            _M["mod"], _M["why"] = mod, f"正本實作 {eng.name}"
        except Exception as exc:
            _M["why"] = f"正本實作載不動:{type(exc).__name__}: {str(exc)[:60]}"
            return None, _M["why"]
    return _M["mod"], _M["why"]


#: 批558:本土尺度命中之後的**上下文否決**。位置守衛(只看前 N 行)在**文件比窗短**時等於沒有,
#: 而短文件正是研報最常見的形狀——本批的負向對照當場打穿:
#: 「公司宣布增持庫藏股 5000 張」整份不到 40 行,`增持` 落在窗內 → 判 BUY。
#: 這正是 LL68 點名的那一型,只是批554 的負控把它放在第 47 行,**靠位置僥倖過關**(LL106 同型)。
#: 否決詞釘在「這個字後面/前面接了什麼就不是評等」,不動正本實作 ENG086 一個位元。
_RATING_VETO_AFTER = _re.compile(r"^\s*(?:庫藏股|比重|比率|比例|率|張|股|股數|部位|水位|成本|天數|日數)")
_RATING_VETO_BEFORE = _re.compile(r"(?:外資|投信|自營|法人|董監|大股東|公司|本公司|集團)\s*$")


def _veto_local(text: str, hit: dict) -> bool:
    """本土尺度命中是不是被上下文否決(是=不算評等)。"""
    w = (hit or {}).get("raw") or ""
    if not w:
        return False
    i = (text or "").find(w)
    if i < 0:
        return False
    return bool(_RATING_VETO_AFTER.match((text or "")[i + len(w): i + len(w) + 6])
                or _RATING_VETO_BEFORE.search((text or "")[max(0, i - 6): i]))


# ===== 批563:MOPS 列優先序(規則出處=收容冊 VRN_AnnualExtract_SSOT 的 note)=====
INTAKE_ANNUAL_GLOB = "functional modules/VRN/references/intake/**/VRN_AnnualExtract_SSOT_v*.json"
#: 規則原文的指紋——冊若被換掉而這段話不在了,`mops_rules()` 要誠實說 ABSENT,不是繼續照舊排。
_MOPS_FINGERPRINT = ("合計", "淨額", "歸屬於母公司業主之權益", "稀釋")


def mops_rules() -> dict:
    """回收容冊裡那四條判定規則的原文與在位狀態(冊缺/話不在=誠實 ABSENT,不編)。"""
    import json as _json
    hits = sorted(VIA.glob(INTAKE_ANNUAL_GLOB))
    if not hits:
        return {"state": "ABSENT", "why": "收容冊缺:VRN_AnnualExtract_SSOT_v*.json", "note": ""}
    try:
        note = str(_json.loads(hits[-1].read_text(encoding="utf-8")).get("note") or "")
    except Exception as exc:
        return {"state": "RED", "why": f"冊讀不動:{type(exc).__name__}", "note": ""}
    miss = [k for k in _MOPS_FINGERPRINT if k not in note]
    if miss:
        return {"state": "ABSENT", "why": f"冊在但規則原文缺 {miss}", "note": note, "file": hits[-1].name}
    return {"state": "OK", "note": note, "file": hits[-1].name}


#: (名次, 規則名, 樣式)——名次高者為準。**只排名,不刪列。**
_MOPS_RANKS = (
    (40, "權益以歸屬母公司為準", _re.compile(r"歸屬於母公司(業主)?之權益")),
    (30, "取淨額", _re.compile(r"淨額$")),
    (25, "稀釋 EPS 為主", _re.compile(r"^稀釋每股(盈餘|收益)")),
    (20, "認明合計", _re.compile(r"(合計|總計|總額)$")),
)


def mops_rank(raw_label: str, canonical: str = "") -> tuple:
    """批563:同一個正典名有多列在搶時,誰說了算。

    回 `(名次, 為什麼)`;沒有任何規則命中=`(0, "")`(裸標,名次最低)。
    規則出處是收容冊 `VRN_AnnualExtract_SSOT` 的 note,**冊不在就沒有名次**
    ——不是退回一套我自己編的預設(那就變成第二顆頭)。

    為什麼「權益」排最高:ROE = 淨利 ÷ 權益、BVPS = 權益 ÷ 股數。
    拿「權益總額」(含非控制權益)當分母,算出來的 ROE 會**偏低而且看起來完全正常**。
    這種錯不會有紅燈,只會有一個錯的結論。
    """
    lbl = (raw_label or "").strip(" :‧·")
    if not lbl or mops_rules().get("state") != "OK":
        return 0, ""
    for n, why, rx in _MOPS_RANKS:
        if rx.search(lbl):
            return n, why
    return 0, ""


def mops_pick(rows: list, key=lambda r: (r.get("canonical"), r.get("period"))) -> dict:
    """同鍵多列時依名次挑一列;回 {鍵: (勝列, 敗列們)}。**敗列原樣回傳,不丟**。"""
    by = {}
    for r in rows:
        by.setdefault(key(r), []).append(r)
    out = {}
    for k, rs in by.items():
        if len(rs) < 2:
            continue
        rs2 = sorted(rs, key=lambda r: -mops_rank(r.get("raw_label", ""), r.get("canonical", ""))[0])
        if mops_rank(rs2[0].get("raw_label", ""))[0] > mops_rank(rs2[1].get("raw_label", ""))[0]:
            out[k] = (rs2[0], rs2[1:])
    return out


def rating_of(text: str, head_lines: int = 40):
    """評等(正本實作;本土尺度只看前段=連守衛一起繼承)。缺實作=誠實 None。"""
    mod, why = matchers()
    if mod is None:
        return None
    hit = mod.rating_local_scale(text, lines=head_lines)
    if hit and not _veto_local(text, hit):          # 批558:加一道上下文否決(見上)
        return hit
    for fn in (mod.rating_quoted, mod.rating_from_title, mod.safe_rating):
        r = fn(text)
        if r and r.get("canonical"):
            return r
    hit5 = _intake_rating(text)                     # 批562:收容冊那一源(閘最嚴,排最後)
    if hit5:
        return hit5
    return None        # 批541:沒判出評等就回 None,不回一個 canonical=None 的殼(呼叫端會誤以為有結果)


#: 批562:收容冊詞要命中,必須先有線索詞(與冊的 `policy` 同律,也與 ENG086 safe_rating 同律)
_INTAKE_CUE = _re.compile(r"(投資評等|評等|評級|評價|建議|Rating|Recommendation|Rec\.|"
                          r"維持|重申|調升為|調降為|給予|給與)", _re.I)
#: 收容冊裡**風險詞**的專屬否決:這幾個字在研報裡最常見的用法根本不是評等。
#: 操作員裁示「只增不減」——所以它們**留在 SSOT 裡**,只是要命中得過這一關。
#: 詞在不在冊,跟這一次出現算不算評等,是兩件事。
_INTAKE_RISK = {
    "賣超": r"(?:外資|投信|自營|法人|三大法人|融資|融券)|[\d,]+\s*(?:張|股|億|萬|口)",
    "買超": r"(?:外資|投信|自營|法人|三大法人|融資|融券)|[\d,]+\s*(?:張|股|億|萬|口)",
    "Long": r"(?i)(?:long[\s\-]?(?:term|position|only|short)|做多部位|多空)",
    "推薦": r"(?:推薦(?:閱讀|文章|報告|標的清單|名單))",
    "平衡": r"(?:平衡(?:型|配置|基金|報表|計分卡))",
    "觀望": r"(?:市場觀望|買盤觀望|投資人觀望|觀望氣氛|觀望情緒)",
    "避免": r"(?:避免(?:風險|重複|誤判|過度|使用))",
}


def _intake_rating(text: str):
    """批562 第五道:收容冊那一源。**閘最嚴,所以排最後。**

    規則(每一條都是為了讓「只增不減」不等於「製造假評等」):
      ① 命中詞的前 14 字內要有線索詞(投資評等/評等/建議/Rating/維持/重申/給予…),
        **或者**整行去尾標點後剛好等於那個詞(研報的評等欄常是獨立一行)。
      ② 風險詞(賣超/買超/Long/推薦/平衡/觀望/避免)另過專屬否決:
        「外資賣超 3,000 張」是籌碼、「long-term」是期間、「推薦閱讀」是導引——都不是評等。
      ③ 長詞先試(強力賣出 勝過 賣出)。
    回 {raw, canonical, in_dict, how} 或 None(與其他四道同形)。
    """
    m = intake_words()
    if not m or not (text or ""):
        return None
    lines = (text or "").splitlines()
    for w in sorted(m, key=len, reverse=True):
        rx = _re.compile((r"(?<![A-Za-z])" + _re.escape(w) + r"(?![A-Za-z])")
                         if _re.fullmatch(r"[A-Za-z][A-Za-z /.\-]*", w) else _re.escape(w), _re.I)
        for mo in rx.finditer(text):
            i = mo.start()
            seg = text[max(0, i - 14): i]
            ln = next((l for l in lines if w.lower() in l.lower()), "")
            standalone = ln.strip().strip(":：。.、,,;;()()【】").lower() == w.lower()
            if not (_INTAKE_CUE.search(seg) or standalone):
                continue
            veto = _INTAKE_RISK.get(w)
            if veto and _re.search(veto, text[max(0, i - 24): i + len(w) + 24]):
                continue
            return {"raw": mo.group(0), "canonical": m[w], "in_dict": False,
                    "how": f"收容冊(線索詞)" if not standalone else "收容冊(整行等於)"}
    return None


def tp_of(text: str, exclude_code: str | None = None):
    """目標價。缺實作=誠實 (None, 原因)。

    第一道:正本實作(5 條強線索 + LL64 幅度守衛 + 代碼排除)——原封不動。
    第二道(批554):強線索判不出時,才用機構 SSOT 加寬的 11 條試一次
    (目標/Target/合理價/Fair Value/Valuation/預期價/目標股價/合理股價/Tgt/FV/目標區間)。
    守衛**不自己寫**:轉交正本實作的 `_is_upside_context` 與 `_plausible_tp`
    (L30 一個出處;自己另寫一套就是第二顆頭,而且會漂)。
    回傳的 how 一律寫明走了哪一道——弱道不冒充強線索(操作員要能一眼看出這個值多硬)。
    """
    mod, why = matchers()
    if mod is None:
        return None, why
    v, how = mod.safe_target_price(text, exclude_code=exclude_code)
    if v is not None:
        return v, how
    rx = _tp_wide_rx()
    if rx is None or not (text or ""):
        return None, how
    ex = {str(exclude_code)} if exclude_code else set()
    for m in rx.finditer(text):
        if mod._is_upside_context(text, m.end(1)):            # 幅度不是價格(LL64)
            continue
        if not mod._plausible_tp(m.group(1)):                 # 個位數多半是頁碼/序號
            continue
        try:
            fv = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if fv == float(int(fv)) and str(int(fv)) in ex:       # 不得是本檔代碼
            continue
        return fv, f"加寬線索(弱)·{m.group(0)[:18]}"
    return None, how


def broker_of(text: str, filename: str = "", ticker: str | None = None):
    """券商(正本實作;證據分級 + 標的公司名否決)。回 (canon|None, how)。"""
    mod, why = matchers()
    if mod is None:
        return None, why
    veto = mod.subject_names(text, filename, ticker) if ticker else set()
    canon, how = mod.safe_broker_ev(text, veto=veto)
    if not canon and filename:
        canon, how = (mod.safe_broker(filename), "檔名") if mod.safe_broker(filename) else (None, "無")
    return canon, how


def drift(do_print: bool = True) -> dict:
    """逐支現役引擎比對正本規則:**正本有、它沒有**的逐條列出。
    兩段量(這一段是我自己先量錯過才改對的):
      ① 字典那一半——ENG086 與首頁全能引擎是**載入收容件 BrokerRatingDict** 拿到英文評等的,
         不是寫死在檔裡;用「字面有沒有」去量會冤枉它們,那就是我造的判錯紅燈。
      ② 本土尺度那一半——批538 在 64 份真研報上打出來的(增加持股/減少持股/優於大盤…),
         這一半必須寫在自己檔裡才算有。
    而且只量它**真的在抽**的欄位:ENG080 只抽目標價,拿評等去量它是無中生有。"""
    dict_w, local_w = _dict_words(), _local_words()
    intake_w = sorted(intake_words())          # 批562 第三源(撞名已排除)
    all_w = rating_words()                     # 分母的**唯一出處**:與 rating_words 同源
    tp_all, tp_src = tp_terms()
    rep = {"schema": "VIA.VRNFieldRules.drift.v4", "canon_dict_n": len(dict_w),
           "canon_local_n": len(local_w), "canon_intake_n": len(intake_w),
           "canon_all_n": len(all_w), "canon_tp_n": len(tp_all), "tp_src": tp_src,
           "rows": [], "state": "OK"}
    if not (dict_w or local_w or intake_w):
        rep.update(state="ABSENT", why="正本冊缺或無評等詞,無從比對")
        if do_print:
            print(f"[VRN 規則樞紐] {rep['state']} · {rep['why']}")
        return rep
    for zh, d, g, is_canon, fields in CONSUMERS:
        p = _newest(d, g)
        if p is None:
            rep["rows"].append({"engine": zh, "file": None, "state": "ABSENT", "fields": list(fields)})
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        row = {"engine": zh, "file": p.name, "canon": is_canon, "fields": list(fields)}
        if "rating" not in fields:
            row.update(state="N/A", why="這支不抽評等(只抽 " + "、".join(fields) + "),評等落差對它無意義")
        else:
            # 批554 第三種來源:**委由樞紐**。ENG073 v0128 沒有把 38 個詞抄進去(那是第二顆頭),
            # 它呼叫本樞紐拿實作。用「字面有沒有那 38 個詞」去量它,量到的是 17/38——
            # 那是**我的尺子錯了**,不是它缺規則(LL85 同型:我第一版的尺就錯過一次)。
            row["hub_delegate"] = HUB_MARK in t
            row["dict_source"] = DICT_MARK in t
            if row["hub_delegate"]:
                row["local_missing"], row["dict_missing"] = [], []
                row["n"] = len(all_w)          # 批562:委樞=整套有,分母用三源聯集
                row["state"] = "CANON" if is_canon else "HUB"
                row["why"] = "委由樞紐(規則與守衛整套繼承;沒抄第二份詞表=對的做法)"
            else:
                row["local_missing"] = [w for w in local_w if w not in t]
                row["dict_missing"] = [] if row["dict_source"] else [w for w in dict_w if w not in t]
                # 批562 第三源:收容冊的詞沒有「載了就自動有」的印記,一律字面量
                row["intake_missing"] = [w for w in intake_w if w.lower() not in t.lower()]
                # 批562 誠實兩欄:**本體字面有幾個** / **經樞紐拿到幾個**。
                # 收容冊那一源是樞紐第五道(`_intake_rating`)供應的,而所有人都經 `rating_of`
                # 拿實作——「本體沒有這幾個字」與「它判不出這幾個」不是同一件事。
                # 混成一個數字就是我在批554 被打過的那把錯尺(LL85)。
                miss = row["dict_missing"] + row["local_missing"] + row["intake_missing"]
                row["n_self"] = len(all_w) - len({w.lower() for w in miss} & {w.lower() for w in all_w})
                # **只有真的經樞紐拿實作的那幾支**才配有「經樞紐」這一欄:
                # 正本 ENG086 是樞紐轉交的那一支,委樞的引擎呼叫樞紐——這兩種才算。
                # TW02 與首頁全能兩支既沒委樞也不是正本,替它們印一個「經樞紐 40/66」
                # 就是我自己造的假綠:它們根本沒有那條路。
                _via_hub = bool(is_canon or row.get("hub_delegate"))
                row["intake_by_hub"] = len(row["intake_missing"]) if _via_hub else 0
                row["n_hub"] = row["n_self"] + row["intake_by_hub"] if _via_hub else None
                row["n"] = row["n_self"]
                # 正本那一支的判準只看**字典那兩源**:收容冊本來就該由樞紐供應,
                # 拿它去量 ENG086 的本體,量到的是「它沒抄第三本冊」——那正是對的做法(Zero-Hydra)。
                row["state"] = ("CANON" if is_canon and not (row["dict_missing"] + row["local_missing"])
                                else ("OK" if not miss else "DRIFT"))
        # 批554 目標價維度(評等那一半的對稱物):機構 SSOT 16 條同義字,誰認得幾條。
        if "target_price" in fields:
            row["tp_source"] = all(k in t for k in TP_DICT_MARK) or row.get("hub_delegate", False)
            row["tp_missing"] = [] if row["tp_source"] else [w for w in tp_all if w.lower() not in t.lower()]
            row["tp_n"] = len(tp_all) - len(row["tp_missing"])
        rep["rows"].append(row)
    rep["drift_n"] = sum(1 for r in rep["rows"] if r["state"] == "DRIFT")
    if do_print:
        tot = len(all_w)
        print(f"=== VRN 研報欄位規則 · 正本評等 {tot} 詞(三源聯集)"
              f"(收容件字典 {len(dict_w)} + 本土尺度 {len(local_w)} + 操作員收容冊 {len(intake_w)};"
              f"撞名 {len(intake_conflicts())} 個依「只增不減除非衝突」排除)===")
        for r in rep["rows"]:
            tag = {"CANON": "正本", "HUB": "委樞", "OK": "齊", "DRIFT": "落差",
                   "ABSENT": "缺", "N/A": "不適用"}[r["state"]]
            n = f"{r.get('n', 0)}/{tot}" if r["state"] not in ("N/A", "ABSENT") else "—"
            if r.get("intake_by_hub"):
                n += f" 本體 · {r.get('n_hub')}/{tot} 經樞紐"
            tpn = f" · 目標價 {r['tp_n']}/{len(tp_all)}" if "tp_n" in r else ""
            print(f"  [{tag:<4}] {r['engine']:<18} {r.get('file') or '-':<44} {n}{tpn}")
            if r["state"] in ("N/A", "HUB"):
                print(f"           {r['why']}")
            if r.get("tp_missing"):
                print(f"           目標價同義字缺 {len(r['tp_missing'])} 條:{'、'.join(r['tp_missing'])}")
            if r["state"] == "DRIFT":
                if not r.get("dict_source"):
                    print(f"           沒載收容件字典(自己寫死一份)→ 英文評等缺 {len(r['dict_missing'])} 個:"
                          f"{'、'.join(r['dict_missing'][:8])}{'…' if len(r['dict_missing']) > 8 else ''}")
                if r["local_missing"]:
                    print(f"           本土尺度缺 {len(r['local_missing'])} 個:{'、'.join(r['local_missing'])}")
                if r.get("intake_missing"):
                    print(f"           收容冊缺 {len(r['intake_missing'])} 個:"
                          f"{'、'.join(r['intake_missing'][:8])}{'…' if len(r['intake_missing']) > 8 else ''}")
        print(f"  [目標價] 正本 {len(tp_all)} 條同義字 · 來源 {tp_src}"
              f"(操作員點名的「目標 / target」在加寬的 {len(tp_wide_terms())} 條裡)")
        print(f"  [結] 落差引擎 {rep['drift_n']} 支 · 本批零改線(規則先收斂到一處,動不動刀是你的決定)")
    return rep


def conflicts(do_print: bool = True) -> dict:
    """批541 去衝突:同一別名對到多個正典名 = 衝突。轉交正本實作的量尺(L30 一個出處)。"""
    mod, why = matchers()
    if mod is None:
        rep = {"state": "ABSENT", "why": why, "n": None}
    else:
        c = mod.broker_conflicts()
        rep = {"state": "OK" if c["n"] == 0 else "RED", "n": c["n"], "rows": c["rows"],
               "brokers": len(mod.broker_tables())}
    if do_print:
        print(f"[去衝突] {rep['state']} · 券商別名撞名 {rep.get('n')} 個 · 合併後 {rep.get('brokers')} 家")
        for r in (rep.get("rows") or [])[:10]:
            print(f"   '{r['alias']}' → {r['canons']}")
    return rep


_CAND_RX = None


def _alias_in_name(name_l: str, known) -> str:
    """批541:檔名裡是不是**已經**出現在冊的別名?有的話這份就認得出券商,生不出「新」別名。

    中文別名 2 字就算數(「兆豐」很專指);拉丁別名要 3 字以上而且卡邊界
    ——`jp` 兩個字母會誤咬 `..._jpn_...`,咬錯就等於把真候選也一起埋掉。
    """
    import re as _re
    for k in known:
        if not k:
            continue
        if any("\u4e00" <= ch <= "\u9fff" for ch in k):
            if len(k) >= 2 and k in name_l:
                return k
        elif len(k) >= 3 and _re.search(r"(?<![a-z0-9])" + _re.escape(k) + r"(?![a-z0-9])", name_l):
            return k
    return ""


def harvest(limit: int = 0, do_print: bool = True, rows: list | None = None) -> dict:
    """批541 邊實測邊更新同義字:拿真語料跑一輪,把**該有卻沒命中**的欄位旁邊的候選詞撈出來。

    只做三件很克制的事:
      ① 券商——證據只有「檔名」的那幾份(文內沒認出來),把檔名開頭那段機構字樣列為候選別名;
      ② 評等——個股報告、文中有評等字樣卻沒命中的,把線索詞後面那一小段列為候選;
      ③ 一律標 PENDING_OPERATOR,附檔名與證據,**絕不自己寫進正本冊**(不代設)。
    正本要長,是你點頭那一刻才長;這支只負責把「下一批該補什麼」端到你面前。
    """
    import json as _j
    import re as _re
    mod, why = matchers()
    if mod is None:
        rep = {"state": "ABSENT", "why": why, "candidates": []}
        if do_print:
            print(f"[候選同義字] ABSENT · {why}")
        return rep
    if rows is not None:
        # 負控用的合成列(檢⑩):閘門必須擋得住假候選、**也必須放得出真候選**。
        # 一個永遠回 0 的濾網跟一盞假綠燈沒有兩樣(LL77),所以這條路要留著給自測走。
        out, d = Path("(合成列)"), {"rows": list(rows)}
    else:
        out = VIA / "VIA_Reports" / "first_page_logic" / "CORPUS_latest.json"
        if not out.is_file():
            rep = {"state": "NODATA", "why": f"還沒有實測結果:{out.name}(先跑 via-fplogic corpus)", "candidates": []}
            if do_print:
                print(f"[候選同義字] NODATA · {rep['why']}")
            return rep
        d = _j.loads(out.read_text(encoding="utf-8"))
    ssot_alias = {a.lower() for v in mod.ssot_brokers()[0].values() for a in v}
    extra_alias = {a.lower() for v in mod.EXTRA_BROKER.values() for a in v}
    known = ssot_alias | extra_alias
    cands, seen = [], set()
    for r in d.get("rows", [])[: (limit or None)]:
        f = r.get("file") or ""
        if r.get("broker_how") == "檔名":
            # 批541 第一道閘:檔名裡任何一處已經有在冊的別名 → 這份檔名本來就認得出券商,
            # 撈出來的只會是報告段名(公司訪談摘要)或產品類別(PCB),不是新機構。
            hit = _alias_in_name(f.lower(), known)
            if hit:
                continue
            # 檔名開頭那段機構字樣(中文 2~6 字 或 拉丁 2~12 字),沒在冊上的才算候選
            # 批541:檔名有兩種擺法——`<券商><日期>-<標的>` 與 `<標的>(代碼,評等)-<券商><日期>`。
            # 只掃開頭會把第二種的標的公司名(晶心科/瑞基)當成券商=假候選。改成頭尾都看,並且:
            #   · 後面緊跟 `(四碼` 的是標的公司名,跳過
            #   · 已知別名是它的一部分就不是新詞(「凱基日股分析」裡的「凱基」早就在冊上)
            #   · 場次序號(第一場/第二場)不是機構
            head = _re.match(r"^([\u4e00-\u9fff]{2,6}|[A-Za-z][A-Za-z.\- ]{1,11})", f)
            tail = _re.search(r"[-_]([A-Za-z]{2,12}|[\u4e00-\u9fff]{2,6})\s*\d{0,8}\.(?:pdf|docx?)$", f, _re.I)
            subj = bool(_re.match(r"^[\u4e00-\u9fff A-Za-z\-]{2,10}[((]\s*\d{4}", f))
            for g, tok in (("頭", head.group(1) if head else None), ("尾", tail.group(1) if tail else None)):
                if not tok:
                    continue
                if g == "頭" and subj:
                    continue
                t = tok.strip().strip("-_. ").lower()
                if not t or t in known or any(k in t for k in known if len(k) >= 2):
                    continue
                if _re.match(r"^第[一二三四五六七八九十]場$", t) or ("broker", t) in seen:
                    continue
                seen.add(("broker", t))
                cands.append({"field": "broker", "candidate": tok.strip(), "canon_guess": r.get("broker"),
                              "evidence": f, "pos": g,
                              "why": f"文內認不出券商,只靠檔名;檔名{g}段這串機構字樣不在冊上",
                              "disposition": "PENDING_OPERATOR"})
                # 一份檔名只端一個候選:兩種擺法是互斥的——`<券商><日期>-<標的>` 券商在頭,
                # `<標的>(代碼)-<券商><日期>` 券商在尾。頭已經端出東西了還去撈尾,撈到的是標的公司名。
                break
        if r.get("rating_state") == "MISS" and ("rating", f) not in seen:
            seen.add(("rating", f))
            cands.append({"field": "rating", "candidate": "(待人工看原文)", "evidence": f,
                          "why": "個股報告、文中有評等字樣卻沒命中=正本詞彙可能缺這家的寫法",
                          "disposition": "PENDING_OPERATOR"})
    rep = {"schema": "VIA.VRNFieldRules.harvest.v1", "state": "OK", "source": str(out),
           "n_docs": len(d.get("rows", [])), "candidates": cands,
           "note": "只提候選,絕不自己寫進正本冊(不代設);要入冊請逐條裁後我再改冊"}
    if do_print:
        print(f"=== 候選同義字(實測 {rep['n_docs']} 份;PENDING_OPERATOR {len(cands)} 條)===")
        for c in cands[:20]:
            print(f"  [{c['field']:<7}] {str(c['candidate'])[:18]:<20} ← {c['evidence'][:44]}")
            print(f"            {c['why']}")
        if not cands:
            print("  (這一輪沒有新候選:該命中的都命中了)")
        print("  [守則] 只提候選,不自己寫進正本冊——正本要長,是你點頭那一刻才長")
    return rep


def status(do_print: bool = True) -> dict:
    r = rules()
    rep = {"state": r.get("state"), "ssot": str(SSOT), "owner": r.get("owner"),
           "rating_words": len(rating_words()), "tp_cues": len(tp_cues()),
           "broker_tiers": broker_tiers(), "consumers": len(CONSUMERS)}
    if do_print:
        print(f"[VRN 規則樞紐] {rep['state']} · 冊 {SSOT.name} · 評等詞 {rep['rating_words']}"
              f" · 目標價線索 {rep['tp_cues']} · 券商證據分級 {'>'.join(rep['broker_tiers'])}"
              f" · 讀冊者 {rep['consumers']} 支")
    return rep


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    r = rules()
    chk("① 規則正本冊在位且讀得動(冊不在=誠實 ABSENT,不編)", r.get("state") == "OK", f"({SSOT.name})")
    words = rating_words()
    chk("② 評等正本詞彙 = 收容件 canon_map ∪ 本土尺度;含批538 打出來的本土尺度(增加持股/減少持股)",
        len(words) >= 30 and "增加持股" in words and "減少持股" in words, f"({len(words)} 詞)")
    chk("③ 目標價線索與券商證據分級都在冊(不是各引擎各抄一份)",
        len(tp_cues()) >= 2 and broker_tiers() and "電郵網域(弱)" in broker_tiers()[-1],
        f"(線索 {len(tp_cues())} 條 · 分級 {broker_tiers()})")
    d = drift(do_print=False)
    canon = [x for x in d["rows"] if x.get("canon")]
    chk("④ 正本那一支自己零落差(ENG086 v0102 是冊的來源,它若有落差就是冊寫錯了——"
        "量法要兩段:載收容件字典算有英文評等,本土尺度要寫在自己檔裡)",
        len(canon) == 1 and canon[0]["state"] == "CANON" and canon[0].get("dict_source")
        and not canon[0]["local_missing"] and canon[0].get("n_hub") == len(rating_words()),
        f"({canon[0]['file'] if canon else '缺'} {canon[0].get('state') if canon else ''} · 本體 "
        f"{canon[0].get('n_self') if canon else '-'}/{len(rating_words())} · 經樞紐 "
        f"{canon[0].get('n_hub') if canon else '-'}/{len(rating_words())})")
    na = [x for x in d["rows"] if x["state"] == "N/A"]
    chk("⑤ 落差看得見、且只量它真的在抽的欄位(ENG080 只抽目標價,拿評等去量它是無中生有=判錯的紅燈)",
        d["state"] == "OK" and len(d["rows"]) == len(CONSUMERS) and d["drift_n"] >= 1 and len(na) == 1,
        f"(落差 {d['drift_n']}/{len(CONSUMERS)} 支 · 不適用 {len(na)} 支)")
    src = Path(__file__).read_text(encoding="utf-8").split("\ndef selftest()")[0]
    chk("⑥ 零改線宣告:本樞紐只讀冊、只報落差、只轉交正本實作,**不改寫任何現役引擎**;"
        "正本實作惰性載入(import 本樞紐時不碰任何引擎)· 零網路 · 不落檔(不影響現有功能 · 零九頭龍)",
        "零改線" in src and "惰性" in src
        and all(("import " + k) not in src for k in ("requests", "httpx", "urllib"))
        and ".write_text(" not in src and _M["mod"] is None)
    mod, why = matchers()
    r1 = rating_of("重申貿聯「增加持股」評等") if mod else None
    r2 = rating_of("\n".join(["x"] * 60) + "\n外資持有比重上升") if mod else None
    tp1, _ = tp_of("目標價:NT$1,250 元")
    tp2, _ = tp_of("潛在上漲空間 23%")
    b1, h1 = broker_of("Jentech (3653 TT)\nhelen.chien@daiwacm-cathay.com.tw\nSource: FactSet, Daiwa forecasts")
    chk("⑦ 轉交的是**實作**不是詞表:本土尺度只看前段(內文「外資持有」不當評等 LL68)· 幅度不是價格(LL64)"
        "· 券商證據分級挖掉電郵網域(LL66)——這三條守衛跟著一起繼承",
        mod is not None and (r1 or {}).get("canonical") == "BUY" and r2 is None
        and tp1 == 1250.0 and tp2 is None and b1 is not None and b1 != "CATHAY" and h1 == "文內",
        f"({why} · 評等 {(r1 or {}).get('canonical')} · 內文誤判 {r2} · 目標價 {tp1}/{tp2} · 券商 {b1}/{h1})")
    cf = conflicts(do_print=False)
    chk("⑧ 批541 去衝突:合併後同一別名不得對到多個正典名(下游一 join 就散)——必須是 0",
        cf.get("state") == "OK" and cf.get("n") == 0, f"(撞名 {cf.get('n')} · 合併後 {cf.get('brokers')} 家)")
    hv = harvest(do_print=False)
    chk("⑨ 批541 邊實測邊長同義字:候選一律 PENDING_OPERATOR,**絕不自己寫進正本冊**(不代設);"
        "沒有實測結果就誠實 NODATA 並指路,不編",
        hv.get("state") in ("OK", "NODATA")
        and all(c.get("disposition") == "PENDING_OPERATOR" for c in hv.get("candidates", []))
        and "絕不自己寫進正本冊" in Path(__file__).read_text(encoding="utf-8"),
        f"({hv.get('state')} · 候選 {len(hv.get('candidates', []))} 條)")
    FAKE = "20251205兆豐晨會報告(二)-公司訪談摘要.pdf"      # 檔名早就有「兆豐」→ 生不出新券商
    REAL = "寰宇投顧20251210-台積電.pdf"                     # 全名都不在冊 → 這才是該端上來的新候選
    hv2 = harvest(do_print=False, rows=[{"file": FAKE, "broker_how": "檔名", "broker": "MEGA"},
                                        {"file": REAL, "broker_how": "檔名", "broker": None}])
    got = {c["candidate"] for c in hv2.get("candidates", []) if c["field"] == "broker"}
    chk("⑩ 批541 候選閘門負控:擋得住假候選(報告段名/產品類別——檔名裡已經有在冊別名就生不出新券商),"
        "**也放得出真候選**(全新機構名),而且一份檔名只端一個(不把標的公司名一起撈進來)",
        got == {"寰宇投顧"}, f"(合成兩列 → 端出 {sorted(got)})")
    # ⑪⑫⑬ 批554 目標價同義字(操作員令「目標價 目標 target price price target target」)
    _t, _src = tp_terms()
    chk("⑪ 目標價同義字**讀機構 SSOT 那一本**,不在本冊另抄一份(操作員點名的「目標 / target」"
        "就在加寬的 11 條裡;同義字一個出處=L30)",
        len(_t) >= 16 and "目標" in _t and any(x.lower() == "target" for x in _t)
        and "機構 SSOT" in _src, f"({len(_t)} 條 · {_src})")
    _pos = [("目標價 250 元", 250.0), ("Target Price: NT$1,250.00", 1250.0),
            ("目標 285 元", 285.0), ("Target NT$312.5", 312.5), ("合理價 98 元", 98.0),
            ("Fair Value 44.8", 44.8), ("目標股價 1,080 元", 1080.0), ("預期價 66 元", 66.0),
            ("合理股價約為 156 元", 156.0), ("Tgt: 41.2", 41.2), ("目標區間 90~110", 90.0)]
    _miss = [x for x, want in _pos if (tp_of(x)[0] != want)]
    chk("⑫ 加寬同義字真的抓得到(強線索判不出時才走第二道;前四條走正本實作,"
        "後七條是批554 新增的加寬道)", not _miss,
        f"(正向 {len(_pos)} 筆 · 沒抓到 {len(_miss)} 筆{('=' + '、'.join(_miss)) if _miss else ''})")
    # ⑬ 負向對照:這一檢是 ⑫ 的保命符。加寬詞彙不配加緊守衛,補進來的不是命中率,是假目標價。
    #    下面十一條**全是實測抓到過的誤抓**(四條是我第一版真的判錯的:2026 / 15 / 2026 / 45),
    #    不是我事後編的假想例。
    _neg = ["潛在上漲空間 23%", "上漲空間達 35%", "目標市場規模 2026 年上看 100 億元",
            "Valuation is undemanding at 15x 2026 PE", "公司將 target 2026 年營收成長 20%",
            "本報告無目標價", "毛利率目標 45%", "目標客群為高階手機 5G 用戶",
            "營收目標 3 年翻倍", "FV 假設 2027 年折現", "目標價位帶尚未給出"]
    _fire = [(x[:16], tp_of(x)[0]) for x in _neg if tp_of(x)[0] is not None]
    chk("⑬ 加寬道負向對照:幅度不是價格(LL64)、年份不是價格、倍數不是價格、"
        "「目標市場/目標客群/營收目標」的『目標』不是價格標籤——一條都不准抓到值",
        not _fire, f"(負向 {len(_neg)} 筆 · 誤抓 {len(_fire)} 筆"
                   + (f":{_fire}" if _fire else "") + ")")
    # ⑭ 尺子本身要對:委由樞紐 ≠ 缺規則,而「欄位名撞變數名」不算讀了冊。
    _rows = {x["engine"]: x for x in d["rows"]}
    _e73 = _rows.get("ENG073 報告結構庫", {})
    _tw02 = _rows.get("TW02 報告解析器", {})
    chk("⑭ 量尺負控(批554,LL85 同型第三次):① 委由樞紐的引擎算**整套有**,不是 17/38——"
        "它沒抄詞表正是對的做法,用字面去量會替它點一盞判錯的紅燈;"
        "② 目標價的印記釘在**冊名**上,不是欄位名——只認 TARGET_PRICE 時 TW02 印 16/16,"
        "而它那個字串是自己的變數名 TARGET_PRICE_SYNONYMS(寫死 11 條),根本沒讀冊",
        _e73.get("hub_delegate") and _e73.get("n") == len(words)
        and not _tw02.get("tp_source") and _tw02.get("tp_n", 99) < len(_t),
        f"(ENG073 {_e73.get('state')} {_e73.get('n')}/{len(words)} 目標價 {_e73.get('tp_n')}/{len(_t)}"
        f" · TW02 目標價 {_tw02.get('tp_n')}/{len(_t)} 讀冊={_tw02.get('tp_source')})")
    # ⑮⑯ 批558:找欄位要在**哪裡找**(操作員令「第一頁周圍訊息區塊及中間本文標題區修復後尋找」)
    _Z = {"header": "凱基投顧 研究部", "right": "投資\n評等\n增加持股",
          "body": ("公司近況說明如下,本季營收表現穩健。\n"
                   "【投資評等】維持增加持股\n"
                   "本公司預期明年毛利率將持續改善,主要受惠於產品組合優化。\n"
                   "二、目標價 1250 元\n"
                   "外資持有比重上升至 23%,投信同步調節。\n"
                   "- - - - -\n12\n"),
          "footer": "風險聲明 · 目標價 1250 元"}
    _i, _h = info_block(_Z), headings(_Z["body"])
    chk("⑮ 三個公用件(批558):`repair` 斷行修復 · `info_block` 第一頁周圍訊息區塊"
        "(頁首帶/右/**頁尾**)· `headings` 中間本文標題區。實作放這裡不放各引擎裡——"
        "四支各寫一份標題偵測就是四個會漂的真相(Zero-Hydra)",
        repair("Target\nprice\nNT$165") == "Target price NT$165"
        and "投資 評等 增加持股" in _i and "風險聲明" in _i          # 頁尾真的在
        and "【投資評等】維持增加持股" in _h and "目標價 1250 元" in _h
        and "外資持有比重" not in _h and "毛利率將持續改善" not in _h  # 敘述句不收
        and "- - - - -" not in _h and "\n12" not in _h,              # 分隔線/頁碼不收
        f"(周圍訊息 {len(_i)} 字 · 標題區 {len(_h)} 字:{_h[:32]}…)")
    # ⑯ 負向:位置守衛在「文件比窗短」時等於沒有——這一檢就是在量那個洞補了沒有。
    _short = "某某投顧 法說會紀要\n公司宣布增持庫藏股 5000 張。\n外資持有比重上升至 23%。\n"
    _long = "某某投顧 法說會紀要\n" + ("內文段落。\n" * 45) + "公司宣布增持庫藏股 5000 張。\n"
    _real = "凱基投顧 2330\n投資評等 增加持股\n目標價 1250 元\n"
    chk("⑯ 本土尺度的**上下文否決**(批558 負控):正本實作只用位置守衛(前 40 行),"
        "文件比窗短時等於沒守——「公司宣布增持庫藏股 5000 張」整份三行,`增持` 落在窗內就判 BUY。"
        "批554 的負控把假朋友放在第 47 行,**是靠位置僥倖過關的**(LL106 同型:沒走到那一步冒充通過)。"
        "加否決詞(庫藏股/比重/張/…在後,外資/投信/法人/公司…在前)後,短文件也擋得住,"
        "而真的評等照樣判得出來——擋得住**且**放得過,兩邊都要量",
        rating_of(_short) is None and rating_of(_long) is None
        and (rating_of(_real) or {}).get("canonical") == "BUY",
        f"(短文件={'擋住' if rating_of(_short) is None else '漏了'} · "
        f"長文件={'擋住' if rating_of(_long) is None else '漏了'} · "
        f"真評等={(rating_of(_real) or {}).get('canonical') or '沒判出來'})")
    # ⑰⑱ 批562 操作員裁示「SSOT 只增不減除非衝突」+ 收容冊 VRN_Rating_Dict
    _im, _ic = _intake_map(), intake_conflicts()
    _all = rating_words()
    chk("⑰ 評等詞彙三源聯集(批562:收容件字典 ∪ 本土尺度 ∪ **操作員收容冊**)。"
        "**只增不減**=三源全收;**除非衝突**=撞名者排除。"
        "撞名是量出來的不是猜的:`Accumulate`/`Add` 冊判 BUY、正本判 ADD,"
        "同一別名對到兩個正典名 → 排除這 2 個,正本的 ADD 保留",
        len(_im) >= 30 and set(_ic) == {"Accumulate", "Add"}
        and len(_all) > len(set(_dict_words()) | set(_local_words()))
        and "未評等" in _all and "強力賣出" in _all
        and "Accumulate" not in intake_words(),
        f"(冊 {len(_im)} 詞 · 撞名 {sorted(_ic)} · 三源聯集 {len(_all)} 詞 · "
        f"兩源 {len(set(_dict_words()) | set(_local_words()))} 詞)")

    # ⑱ 「只增不減」不等於「照單全收就開判」——這一檢就是那條界線。
    _pos = [("投資評等 未評等", "NOT_RATED"), ("評等:強力賣出", "SELL"),
            ("Rating: Not Rated", "NOT_RATED"), ("建議 積極買進", "BUY"),
            ("投資評等\n觀望\n目標價 -", "HOLD"), ("評等 NR", "NOT_RATED")]
    _neg = ["外資賣超 3,000 張,投信買超 500 張。", "long-term growth remains intact",
            "推薦閱讀:本公司年報第 12 頁", "平衡型基金配置建議", "市場觀望氣氛濃厚",
            "為避免重複計算,已扣除關係人交易", "公司宣布增持庫藏股 5000 張。"]
    _miss = [t.replace("\n", "⏎") for t, w in _pos if (rating_of(t) or {}).get("canonical") != w]
    _fire = [(t[:18], (rating_of(t) or {}).get("canonical")) for t in _neg if rating_of(t)]
    chk("⑱ 收容冊那一道的閘(批562):詞進 SSOT 是一回事,**這一次出現算不算評等是另一回事**。"
        "冊裡的 `賣超`/`Long`/`推薦`/`平衡`/`觀望`/`避免` 依裁示**留在詞表裡**,"
        "但要命中得先有線索詞或整行等於,再過專屬否決——"
        "「外資賣超 3,000 張」是籌碼、「long-term」是期間、「推薦閱讀」是導引,一個都不准判成評等。"
        "批540/554/558 已經量過三次:光補詞彙不補守衛就是製造假評等",
        not _miss and not _fire,
        f"(正向 {len(_pos)} 筆漏 {len(_miss)}{('=' + '、'.join(_miss)) if _miss else ''} · "
        f"負向 {len(_neg)} 筆誤判 {len(_fire)}{('=' + str(_fire)) if _fire else ''})")
    # ⑲⑳ 批563:收容冊的 MOPS **判定規則**(不是詞)
    _mr = mops_rules()
    chk("⑲ MOPS 四條判定規則讀自收容冊(批563:認明「合計」· 應收/存貨取「淨額」· "
        "權益與 ROE/BVPS 以「歸屬於母公司業主之權益」為準 · 稀釋 EPS 為主)。"
        "**規則不在冊裡就沒有名次**——不退回一套我自己編的預設(那就是第二顆頭)",
        _mr.get("state") == "OK" and all(k in _mr.get("note", "") for k in _MOPS_FINGERPRINT)
        and mops_rank("歸屬於母公司業主之權益總計")[0] == 40
        and mops_rank("應收帳款淨額")[0] == 30
        and mops_rank("稀釋每股盈餘")[0] == 25
        and mops_rank("營業收入合計")[0] == 20
        and mops_rank("營業收入")[0] == 0,
        f"({_mr.get('file')} · 權益 40 · 淨額 30 · 稀釋 25 · 合計 20 · 裸標 0)")
    # ⑳ 這一檢量的是**那個會安靜算錯的位置**:兩列搶同一個正典名時誰贏,以及輸的有沒有被丟掉。
    _rows = [{"canonical": "equity", "period": "2025", "raw_label": "權益總計", "value": 3200000},
             {"canonical": "equity", "period": "2025", "raw_label": "歸屬於母公司業主之權益總計", "value": 3050000},
             {"canonical": "receivables", "period": "2025", "raw_label": "應收帳款", "value": 250},
             {"canonical": "receivables", "period": "2025", "raw_label": "應收帳款淨額", "value": 243},
             {"canonical": "revenue", "period": "2025", "raw_label": "營業收入合計", "value": 9000}]
    _pick = mops_pick(_rows)
    _eq = _pick.get(("equity", "2025"))
    _ar = _pick.get(("receivables", "2025"))
    chk("⑳ 同鍵多列的優先序(批563):ROE = 淨利 ÷ 權益、BVPS = 權益 ÷ 股數——"
        "拿含非控制權益的「權益總額」當分母,算出來的 ROE 會**偏低而且看起來完全正常**,"
        "不會有紅燈只會有錯結論。這一檢要求:① 歸屬母公司那列贏 ② 淨額那列贏 "
        "③ **輸的那列原樣留著不丟**(只增不減)④ 只有一列的鍵不進 pick(沒在搶就沒有輸贏)",
        _eq and _eq[0]["value"] == 3050000 and _eq[1][0]["value"] == 3200000
        and _ar and _ar[0]["value"] == 243 and _ar[1][0]["value"] == 250
        and ("revenue", "2025") not in _pick,
        f"(權益 勝 {_eq[0]['raw_label'] if _eq else '-'} · 敗留 {len(_eq[1]) if _eq else 0} 列 · "
        f"應收 勝 {_ar[0]['raw_label'] if _ar else '-'} · 單列鍵不進 pick={('revenue','2025') not in _pick})")
    print(f"  [計] 二十檢 OK {20 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="VRN 研報六欄規則正本樞紐")
    ap.add_argument("verb", nargs="?", choices=("status", "rules", "drift", "conflicts", "harvest", "selftest"), default="status")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", dest="as_json", action="store_true")
    argv = [("selftest" if a == "--selftest" else a) for a in sys.argv[1:]]
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        print("=== VRN 研報欄位規則正本樞紐(SUP_MDL749)· 二十檢自測(零網路;零改線)===")
        return selftest()
    if args.verb == "rules":
        print(json.dumps(rules(), ensure_ascii=False, indent=1))
        return 0
    if args.verb == "conflicts":
        c = conflicts(do_print=not args.as_json)
        if args.as_json:
            print(json.dumps(c, ensure_ascii=False, indent=1))
        return 0 if c.get("state") == "OK" else 1
    if args.verb == "harvest":
        h = harvest(limit=args.limit, do_print=not args.as_json)
        if args.as_json:
            print(json.dumps(h, ensure_ascii=False, indent=1))
        return 0 if h.get("state") in ("OK", "NODATA") else 2
    if args.verb == "drift":
        d = drift(do_print=not args.as_json)
        if args.as_json:
            print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0
    s = status(do_print=not args.as_json)
    if args.as_json:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    return 0 if s.get("state") == "OK" else 2


if __name__ == "__main__":
    sys.exit(main())

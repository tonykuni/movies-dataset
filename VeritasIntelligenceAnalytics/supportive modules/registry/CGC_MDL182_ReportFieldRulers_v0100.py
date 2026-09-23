#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL182_ReportFieldRulers v0100 — 研報欄位補尺(批713)

操作員 2026-09-23 指名四件。**先量,量出來才知道哪一件是哪一種問題**(LL400):

| 項 | 實測 | 是哪一種 |
|---|---|---|
| 評等抽取 | 詞在冊上 4 個檔名、抽取器只抓到 1 個 | **詞表齊,抽取器沒抓到** |
| 台北/香港電話 | 正本 `contact.corrected` **早就有而且更強** | 我差點長出第二顆頭 |
| 研究員職稱表 | 樹上**沒有這張表** | 缺表 |
| 券商網域 | `@ctbcsecurities.com` 回空、`@kgi.com` 正確 | 冊缺一條 |
| 中英姓名 / `@` 前互證 / 鄰域 | 冊上**有規則、沒有人跑** | 缺實作 |

**批713 自糾(操作員令「檢查前兩次成功經驗他們的 ssot regex 同意字級標準」)**:
本支首版自帶五條電話式子。拿兩本成功冊的十四條標準一量就穿幫 ——
正本 `VRN_FieldRules_SSOT_v0100.json#rules.contact.corrected` 那兩條**收得到香港裸號
`2971 6686`,我自帶那五條收不到**。式子全部撤掉改成指向正本(檢 ⑧ 釘住),
只留一條量得出來的加寬(`#2101` 分機標記)。

**但正本那兩條單獨用會咬錯**(實測):台灣號碼的後八碼同時被判成香港號碼、
日期 `2025 1231` 與 ETF 代號 `00878 2025` 都被當成電話。正本自己對中文姓名下過
「不可以單獨用」的鄰域鎖,電話這條漏了 —— 本支補的是**那道鎖**(檢 ⑩),
不是第二份式子。

**批713 第二道令(操作員 2026-09-23 逐字給定五式 + 錨點回溯法)**:
職稱中英字典、中英文姓名、台北/香港電話、Email 具名拆解(eng_name / broker_domain / tld)、
以及最重要的**逐 Email 各自開窗**。原文一字不改留在冊 `contact_block.as_given`,
實測打破的逐條寫在 `corrected`:

| 原文 | 哪一個探針打破它 | 怎麼改 |
|---|---|---|
| 台灣式區碼寫死 `2` | `(03) 578-1234`(新竹)抓不到 | 放寬 `\d{1,2}`,其餘一字不動 |
| 英文姓名尾巴 `*` | `Senior Analyst` / `Tel Fax` 整個被當成姓名 | 用操作員那張職稱表當擋板扣掉 |
| 中文姓名錨點式 | `分析師的看法是這樣` 抽出 `的看法是`;操作員自己舉的 `職稱 / Senior Analyst\n林大衛` 反而抓不到 | 錨點開窗 + 職稱/機構/虛詞三道擋板;原文那式留作強線索 |
| 80 字元視窗 | 三位分析師,**第三位拿到第二位的電話** | 視窗起點卡在前一個錨點之後(檢 ⑬) |
| 香港式首碼 `[23]` | 比舊正本 `[2-9]` 嚴,但漏掉 5/6/9 開頭的手機 | 新式當正主,舊式留著只產 WEAK(只增不減) |

**為什麼另立一支而不改正本**:評等的正本實作是 `VRN_ENG086`(現 v0113),
而 **PR #75 已經佔著 v0114/v0115 與 RuleHub v0113**。在它還沒併之前去開同樣的號,
就是批708/711 那兩次撞號再來一遍。本支只**補新尺**,一個字都不動正本。

規則全部從 `VIA_VRN_ReportFieldRules_SSOT_v0100.json` 讀(規格是冊不是碼)。

律:唯讀 · 零網路 · 不動正本 · **不抄第二份**(電話/姓名只指向正本)· 不硬塞評等(槽位取得出來但詞不在冊上 = UNRATED_SLOT)。
用法:python3 CGC_MDL182_ReportFieldRulers_v0100.py [檔名…] | --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import re
import sys
from pathlib import Path

ENGINE_ID = "CGC_MDL182_ReportFieldRulers"
VERSION = "v0100"
BATCH = "批713"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RULES = HERE / "VIA_VRN_ReportFieldRules_SSOT_v0100.json"
CANON = HERE / "VRN_FieldRules_SSOT_v0100.json"   # 正本:電話/姓名的式子只從這裡來


def rules(path: Path | None = None) -> dict:
    """規則從**冊**來。讀不到就回空 —— 不自己內建一份(內建的那份沒有人裁定過)。"""
    try:
        return json.loads((path or RULES).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _rating_dict() -> tuple[list, str]:
    """評等詞表**委派給 RuleHub**(L30 單一出處),不自己抄一份。問不到就誠實回空。"""
    try:
        import importlib.util as ilu
        h = sorted((VIA / "supportive modules/70_VRN_Rules")
                   .glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))
        if not h:
            return [], "RuleHub 缺席"
        sp = ilu.spec_from_file_location("_mdl182_hub", h[-1])
        m = ilu.module_from_spec(sp)
        sys.modules["_mdl182_hub"] = m
        sp.loader.exec_module(m)
        return list(m.rating_words()), h[-1].name
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def rating_from_filename(stem: str, words=None, R: dict | None = None) -> dict:
    """檔名**括號位置式**評等:`瑞基(4171,NR_未評等)` / `欣銓(3264,B_買進)`。

    正本 `safe_rating` 要**線索詞**(「評等」)才判,所以這種寫法整個沒進掃描面。
    這裡用的是**位置**:括號內、代號之後、逗號之隔 —— 那一格就是評等槽。
    位置比線索詞強,也比掃全文安全(掃全文會把內文的「中立」當評等,批419g 實錄)。

    槽位裡的詞**不在評等冊上就不硬塞**:回 `UNRATED_SLOT` + 原文。
    `(7728,Note)` 的 `Note` 是**報告類型**不是評等,把它講成評等
    等於憑空造一個沒有人裁定過的評等。
    """
    R = R if R is not None else rules()
    cfg = (R.get("filename_rating_slot") or {})
    rx = cfg.get("rx")
    if not rx:
        return {"state": "NODATA", "why": "規則冊缺 filename_rating_slot"}
    m = re.search(rx, stem)
    if not m:
        return {"state": "NO_SLOT", "why": "檔名沒有 (代號,評等) 這種括號槽"}
    raw = (m.group("slot") or "").strip()
    parts = [p for p in re.split(cfg.get("slot_split_rx") or "[_]", raw) if p.strip()]
    if words is None:
        words, _ = _rating_dict()
    wl = {w.lower(): w for w in words if w}
    for p in parts + [raw]:
        q = p.strip()
        if q.lower() in wl:
            return {"state": "GREEN", "code": m.group("code"), "raw": raw,
                    "word": wl[q.lower()], "how": "檔名括號槽位式"}
    return {"state": cfg.get("not_in_dict", "UNRATED_SLOT"), "code": m.group("code"),
            "raw": raw, "word": "", "how": "槽位取得出來,但詞不在評等冊上——不硬塞"}


def canon(path: Path | None = None) -> dict:
    """正本冊(批628/634;canonical = ENG086 v0102,64 份真研報上驗過)。
    電話與姓名的式子**只從這裡來** —— 抄一份過來就是第二顆會漂移的頭(正本自己寫的那句話)。"""
    try:
        return json.loads((path or CANON).read_text(encoding="utf-8"))
    except Exception:
        return {}


def contact_rules(C: dict | None = None) -> dict:
    """正本 rules.contact.corrected(email / name_en / name_cn / phone_tw / phone_hk)。"""
    C = C if C is not None else canon()
    return ((C.get("rules") or {}).get("contact") or {}).get("corrected") or {}


def _dig(book: dict, dotted: str):
    """`contact_block.corrected.tpe_phone` 這種路徑取值。冊上沒有就回空字串(不內建)。"""
    cur = book
    for k in dotted.split("."):
        cur = (cur or {}).get(k) if isinstance(cur, dict) else None
    return cur or ""


def _pat(spec: dict, R: dict, C: dict) -> str:
    """式子從哪一本來:`from` 帶檔名就去正本拿,不帶就在本冊裡取。"""
    src = spec.get("from", "")
    if "#" in src:
        return _dig(canon() if C is None else C, src.split("#", 1)[1].split("rules.", 1)[-1]
                    ) or _dig({"rules": (canon() if C is None else C).get("rules", {})},
                              src.split("#", 1)[1])
    return _dig(R, src)


def phones_of(text: str, R: dict | None = None, C: dict | None = None) -> list:
    """台北 / 香港 / 分機 —— **式子是操作員 2026-09-23 逐字給定的那兩條**(冊 contact_block)。

    守衛三步(冊 phone.guard):先台後港並遮掉已命中區間 → 同行要有電話字樣或號碼自帶 `+`/`(`/`-`
    → 都沒有就記 WEAK(**不丟掉也不當命中**)。`HK_MOBILE` 是舊正本那一式,只能產 WEAK:
    操作員新式首碼 `[23]` 只收固網,舊式多收 5/6/9 開頭的手機 —— 只增不減,但不搶判定權。
    """
    R = R if R is not None else rules()
    cc = contact_rules(C)
    P = (R.get("phone") or {})
    G = (P.get("guard") or {})
    cue = re.compile(G.get("cue_rx") or r"(?!x)x")
    lines, out, taken = text.splitlines() or [text], [], []

    def _line_of(i: int) -> str:
        n = 0
        for ln in lines:
            if n <= i <= n + len(ln):
                return ln
            n += len(ln) + 1
        return ""

    def _scan(pid: str, rx: str, weak_only: bool) -> None:
        if not rx:
            return
        for m in re.finditer(rx, text):
            a, b = m.span()
            if any(a < y and x < b for x, y in taken):
                continue                      # 已被前一式吃掉的區間:同一支電話不判兩個地點
            hit = m.group(0)
            ok = any(ch in hit for ch in "+()-") or bool(cue.search(_line_of(a)))
            if weak_only or not ok:
                out.append({"id": pid, "hit": hit, "state": "WEAK",
                            "why": ("舊正本那一式只補手機號段,不搶判定權" if weak_only else
                                    "式子中了但同行沒有電話字樣、號碼也沒有 +/(/- 記號")})
                continue
            taken.append((a, b))
            out.append({"id": pid, "hit": hit, "state": "HIT"})

    for spec in (P.get("use") or []):
        rx = _pat(spec, R, C if C is not None else canon())
        if not rx and spec.get("id") == "HK_MOBILE":
            rx = cc.get("phone_hk") or ""
        _scan(spec["id"], rx, spec.get("grade") == "WEAK_ONLY")
    return out


def contacts_of(text: str, R: dict | None = None, C: dict | None = None) -> list:
    """**錨點回溯法**(操作員 2026-09-23 逐字給定):逐個 Email 各自開一個視窗,窗內才抽姓名/職稱/電話。

    「逐個」是這條規則的全部重點 —— 併成一塊抽,一份報告三位分析師就會**串位**
    (A 的電話配到 B 的名字)。視窗 = Email 往前 80 字元(操作員給定)到 Email 結尾。
    """
    R = R if R is not None else rules()
    cc = contact_rules(C)
    B = (R.get("contact_block") or {})
    ag, co = (B.get("as_given") or {}), (B.get("corrected") or {})
    win = int(ag.get("window_chars") or 80)
    email_rx = ag.get("email") or cc.get("email") or r"(?!x)x"
    name_en_rx = cc.get("name_en") or ag.get("en_name") or r"(?!x)x"
    cn_rx = cc.get("name_cn") or r"[\u4e00-\u9fa5]{2,4}"
    stop = ((R.get("name") or {}).get("stop") or {}).get("rx") or r"(?!x)x"
    stop2 = co.get("tw_name_stop_add") or r"(?!x)x"
    strong = ag.get("tw_name") or ""
    out, prev_end = [], 0
    for m in re.finditer(email_rx, text):
        # 視窗起點不只看 80 字元,還要**卡在前一個錨點之後** ——
        # 不卡就會把上一位分析師的電話捲進來(實測:三人區塊,第三人拿到第二人的電話)
        blk = text[max(0, m.start() - win, prev_end): m.end()]
        prev_end = m.end()
        addr = m.group(0)
        titles = titles_in(blk, R)
        ph = [p for p in phones_of(blk, R, C) if p["state"] == "HIT"]
        en = [x for x in dict.fromkeys(re.findall(name_en_rx, blk) if "(" not in name_en_rx
                                       else [g.group(0) for g in re.finditer(name_en_rx, blk)])
              if x not in titles and not any(t.lower() == x.lower() for t in titles)]
        raw_cn = list(dict.fromkeys(re.findall(cn_rx, blk)))
        cn = [w for w in raw_cn
              if not re.search(stop, w) and w not in titles and not re.search(stop2, w)]
        sm = re.search(strong, blk) if strong else None
        if sm and sm.group("tw_name") and not re.search(stop2, sm.group("tw_name")):
            cn = [sm.group("tw_name")] + [w for w in cn if w != sm.group("tw_name")]
        local, dom = addr.split("@", 1)
        at_left = re.sub(r"[._]+", " ", local).title()   # 操作員令:`.` 換空白,`-` 留著(Da-Ming Wang)
        toks = {t.lower() for t in re.split(r"[ ._-]+", local) if len(t) > 1}
        agree = [n for n in en if {w.lower() for w in re.split(r"[ .-]+", n) if w} & toks]
        st = ("GREEN" if agree else "YELLOW" if en else
              "UNVERIFIABLE" if cn else "NODATA")
        out.append({"email": addr, "at_left": at_left,
                    "broker": broker_of_domain(addr, R) or dom.split(".")[0].upper(),
                    "broker_src": "冊" if broker_of_domain(addr, R) else "網域字面(**未對冊,不是裁定**)",
                    "name_en": en[:3], "name_cn": cn[:3], "title": titles[:3],
                    "phone": [p["hit"] for p in ph], "state": st,
                    "window_chars": len(blk)})
    return out


def analyst_of(text: str, R: dict | None = None, C: dict | None = None) -> dict:
    """姓名。**規則正本早就寫好了,樹上沒有人跑它** —— 本函式只是把那三條合起來跑。

    正本 contact.proximity:中文姓名只在電郵 / 電話 / 職稱字樣**往後 2 行、往前 1 行**內取。
    正本 contact.cross_check.at_left:`@` 前通常是分析師英文姓名(first.last / firstlast / flast)
    —— 所以 `@` 前是最硬的那一條,姓名對得上就互證。
    """
    R = R if R is not None else rules()
    cc = contact_rules(C)
    lines = text.splitlines() or [text]
    titles = set(titles_in(text, R))
    email_rx = cc.get("email") or ""
    anchors = set()
    for i, ln in enumerate(lines):
        if (email_rx and re.search(email_rx, ln)) \
           or any(d["state"] == "HIT" for d in phones_of(ln, R, C)) \
           or any(t.lower() in ln.lower() for t in titles):
            anchors.add(i)
    lo_hi = [(max(0, i - 1), min(len(lines), i + 3)) for i in sorted(anchors)]   # 前 1 後 2
    near = "\n".join("\n".join(lines[a:b]) for a, b in lo_hi)
    stop = ((R.get("name") or {}).get("stop") or {}).get("rx") or r"(?!x)x"
    raw_cn = re.findall(cc.get("name_cn") or r"(?!x)x", near) if lo_hi else []
    raw_cn = list(dict.fromkeys(raw_cn))
    drop = [w for w in raw_cn if re.search(stop, w) or w in titles]
    cn = [w for w in raw_cn if w not in drop]          # 擋掉的不消失,原文回在 name_cn_dropped
    en = [m.group(0) for m in re.finditer(cc.get("name_en") or r"(?!x)x", near)] if lo_hi else []
    en = list(dict.fromkeys(en))
    mails = re.findall(email_rx, text) if email_rx else []
    left = [str(m).split("@")[0].lower() for m in mails]
    toks = {t for lp in left for t in re.split(r"[._-]+", lp) if len(t) > 1}
    agree = [n for n in en if {w.lower() for w in re.split(r"[ .-]+", n) if w} & toks]
    st = ("NODATA" if not (cn or en or mails) else
          "GREEN" if agree else
          "YELLOW" if (en and mails) else
          "UNVERIFIABLE")
    return {"state": st, "name_cn": cn[:4], "name_cn_dropped": drop[:6],
            "name_en": en[:4], "emails": mails[:4],
            "at_left": left[:4], "agree": agree[:4], "titles": sorted(titles),
            "anchors": len(anchors),
            "why": {"GREEN": "姓名與 @ 前對得上(正本說這一條最硬)",
                    "YELLOW": "有英文姓名也有電郵,但 @ 前對不上(具名衝突,不挑一個用)",
                    "UNVERIFIABLE": "有姓名沒有電郵 —— 驗不了,不是判錯",
                    "NODATA": "鄰域裡什麼都沒有"}[st]}


def titles_in(text: str, R: dict | None = None) -> list:
    """命中的研究員職稱(中英)。**姓名在職稱/電話/電郵的上方**,所以先認職稱。"""
    R = R if R is not None else rules()
    t = (R.get("analyst_titles") or {})
    low = text.lower()
    hits = [w for w in t.get("zh", []) if w in text]
    hits += [w for w in t.get("en", []) if w.lower() in low]
    return sorted(set(hits), key=lambda x: -len(x))


def broker_of_domain(addr: str, R: dict | None = None) -> str:
    """電郵網域 → 券商(**只補冊上量到缺的那幾條**;正本查不到時才用,只增不減)。"""
    R = R if R is not None else rules()
    dom = addr.split("@")[-1].strip().lower()
    mp = ((R.get("broker_domains_addendum") or {}).get("map") or {})
    for k, v in mp.items():
        if dom == k or dom.endswith("." + k):
            return v
    return ""


def selftest() -> int:
    """語料=操作員 2026-09-23 給的真檔名與逐字規格;**每條檢都帶正控或負控**。

    十四檢裡有七檢是**釘住這一批自己犯過的錯**:⑧ 自帶第二份式子、⑨ 冊缺席偷偷退回內建、
    ⑩ 正本式子裸用咬日期與代號、⑫ 三段式槽位對不上冊、⑬ 三位分析師串位、
    ⑭ 操作員原文三處被探針打破。錯過一次就要有一盞會紅的燈站在那裡。
    """
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    R = rules()
    words, src = _rating_dict()
    print(f"=== 研報欄位補尺 {VERSION}({BATCH})· 自測(沙盒 · 零網路 · 唯讀)===")
    print(f"  規則冊 {RULES.name} · 評等詞表委派 {src}({len(words)} 詞)")

    # ① 括號槽位式:三個實測檔名(正控)
    hit = [rating_from_filename(s, words, R) for s in
           ("瑞基(4171,NR_未評等)-CTBC251208", "欣銓(3264,B_買進)-CTBC260918",
            "南亞(1303,B_買進)-CTBC260918")]
    chk("① **檔名括號槽位式**:`(代號,評等)` 那一格就是評等槽 —— 位置本身是證據,"
        "不必等線索詞。**正控**=操作員語料裡那三個正本抓不到的檔名,這裡必須全中",
        all(h["state"] == "GREEN" for h in hit) and [h["code"] for h in hit] == ["4171", "3264", "1303"],
        "(" + " · ".join(f"{h['code']}→{h.get('word') or h['state']}" for h in hit) + ")")

    # ② 不硬塞 + 沒有槽就說沒有槽
    note = rating_from_filename("光焱(7728,Note)-CTBC260918", words, R)
    noslot = rating_from_filename("GS-1590 20251203", words, R)
    chk("② **槽位取得出來但詞不在冊上,不准硬塞**:`(7728,Note)` 的 `Note` 是**報告類型**不是評等,"
        "回 UNRATED_SLOT + 原文。把報告類型講成評等 = 憑空造一個沒有人裁定過的評等。"
        "**負控**:沒有括號槽的檔名要回 NO_SLOT,不可以生出一個評等",
        note["state"] == "UNRATED_SLOT" and note.get("code") == "7728"
        and noslot["state"] == "NO_SLOT",
        f"(Note→{note['state']} raw={note.get('raw')!r} · 無槽→{noslot['state']})")

    # ③ 電話 + 負控
    ph = phones_of("Tel: (02) 2181-8888 ext. 2101 / HK +852 2971 6686 / 02-2181-8888")
    ids = {p["id"] for p in ph if p["state"] == "HIT"}
    has_ext = any("2101" in p["hit"] for p in ph if p["state"] == "HIT")
    neg = [p for p in phones_of("華南投顧-2606-裕民-1141202 報告日 20251202 代號 3014TT")
           if p["state"] == "HIT"]
    chk("③ 台北市話(括號式/連字號式)· 香港 +852 · 分機都要認得;"
        "**負控**:民國日期 `1141202`、西元日期 `20251202`、代號 `3014TT` 這種數字串"
        "**一個都不准**被當成電話(一把會把日期當電話的尺,抓出來的名片全是假的)",
        {"TPE", "HK"} <= ids and has_ext and not neg,
        f"(命中 {sorted(ids)} · 分機併進台灣式 {has_ext} · 負控誤判 {len(neg)})")

    # ④ 職稱 + 負控
    tt = titles_in("凱基投顧 研究員 劉昃恩 / Research Analyst, Vice President")
    bad = titles_in("這份報告的內容與結論都很清楚")
    chk("④ 研究員職稱表(中英):姓名出現在職稱/電話/電郵的**上方**,所以要先認得出職稱才框得出姓名。"
        "**負控**:一段沒有職稱的普通句子,一個都不准命中",
        {"研究員"} <= set(tt) and any(x.lower().startswith("research analyst") for x in tt) and not bad,
        f"(命中 {tt[:4]} · 負控 {bad})")

    # ⑤ 網域補遺 + 負控
    chk("⑤ 網域補遺只補**量到缺的那幾條**:`@ctbcsecurities.com` → CTBC(實測正本回空)。"
        "**負控**:不認識的網域要回空**不猜** —— 猜出來的券商,下游看不出來那是猜的",
        broker_of_domain("a@ctbcsecurities.com") == "CTBC"
        and broker_of_domain("b@megabank.com.tw") == "MEGA"
        and broker_of_domain("c@unknown-broker.example") == "",
        f"(ctbc→{broker_of_domain('a@ctbcsecurities.com')} · "
        f"未知→{broker_of_domain('c@unknown-broker.example')!r})")

    # ⑥ 規則從冊來
    empty = rating_from_filename("瑞基(4171,NR_未評等)", words, {})
    chk("⑥ 規則從**冊**讀,不內建一份(內建的那份沒有人裁定過)。"
        "**負控**:餵一本空冊,必須誠實 NODATA 並說冊缺了什麼,不可以退回一份寫死的式子照跑",
        empty["state"] == "NODATA" and "filename_rating_slot" in empty["why"],
        f"(空冊→{empty['state']})")

    # ⑦ 唯讀零網路
    src_txt = Path(__file__).read_text(encoding="utf-8")
    code = "\n".join(l for l in src_txt.split("\n") if not l.lstrip().startswith("#"))
    # 自審(批713):`urlopen` 我沒拆,這條檢當場咬到自己 —— **同一個星期第三次**
    #   (MDL180 · MDL181 · 本支)。禁用字面一律拆開寫,這已經是慣犯了。
    banned = [b for b in ("requests." + "get", "url" + "open",
                          "write_" + "text", "http" + "s://api")
              if b in code]
    # ⑧ 不抄第二份:式子只准**指名出處**,不准在用它的地方再抄一份
    own_key = "phone" + "_rx"
    uses = ((R.get("phone") or {}).get("use") or [])
    sup = ((R.get("phone") or {}).get("supersedes") or {})
    chk("⑧ **不抄第二份**:`phone.use` 每一條只准寫**出處路徑**(`from`),不准內嵌式子;"
        "換掉正本哪一條要在 `supersedes` 指名。"
        "(批713 首版自帶五條電話式子被這一檢抓出來 —— 正本那一條還更強。"
        "這一版是操作員 2026-09-23 逐字給定的新式子當正主,舊正本的港式留著只產 WEAK:只增不減)",
        own_key not in R and bool(uses)
        and all(("from" in u and "rx" not in u) for u in uses)
        and CANON.name in (sup.get("book") or "")
        and any(u.get("grade") == "WEAK_ONLY" for u in uses),
        f"(use {[u['id'] for u in uses]} · 內嵌式子 {[u['id'] for u in uses if 'rx' in u]} · "
        f"supersedes→{(sup.get('book') or '')[-34:]!r})")

    # ⑨ 冊缺席:誠實少那幾把尺,不准偷偷退回內建
    gone = phones_of("Tel: (02) 2181-8888", {})
    chk("⑨ **冊讀不到就誠實少那幾條**:餵一本空冊,台/港式必須整個消失。"
        "**負控**:不准退回一份寫死的內建式子照跑(退得回去就表示樹上其實有兩份)",
        not gone,
        f"(空冊→{[p['id'] for p in gone]})")

    # ⑩ 守衛:正本式子單獨用會咬錯,三個假陽性逐個釘住
    fp = {t: [p["state"] for p in phones_of(t)]
          for t in ("(02) 2181-8888", "報告日 2025 1231", "00878 2025", "電話 2971 6686")}
    chk("⑩ **電話鄰域守衛**(批713 補的那道鎖):正本兩條式子單獨用會把"
        "『台灣號碼的後八碼』判成香港號碼、把日期 `2025 1231`、把 ETF 代號 `00878 2025` 當電話。"
        "守衛之後這三個都降成 WEAK(**不丟掉也不當命中**),而同行有『電話』字樣的裸港號照樣 HIT",
        fp["(02) 2181-8888"] == ["HIT"]                       # 台號只算一支,不再兼判香港
        and "HIT" not in fp["報告日 2025 1231"]
        and "HIT" not in fp["00878 2025"]
        and "HIT" in fp["電話 2971 6686"],
        f"({ {k[:12]: v for k, v in fp.items()} })")

    # ⑪ 姓名:正本寫了規則卻沒有人跑,本支只是把三條合起來
    a1 = analyst_of("凱基投顧 研究報告\n研究員 劉昃恩 Vincent Liu\n"
                    "Tel: (02) 2181-8888 ext. 2101\nvincent.liu@kgi.com\n")
    a2 = analyst_of("凱基投顧\n研究員 劉昃恩\nTel: (02) 2181-8888\n")
    a3 = analyst_of("這份報告的內容與結論都很清楚,沒有任何聯絡資訊。\n")
    chk("⑪ 姓名四態(正本 cross_check:`@` 前是最硬的那一條):"
        "姓名與 `@` 前對得上=GREEN · 有姓名沒有電郵=**UNVERIFIABLE(驗不了,不是判錯)** · 什麼都沒有=NODATA。"
        "**負控**:鄰域裡的 `凱基投顧` `研究報告` `研究員` 都中『兩到四個漢字』,一個都不准當成姓名",
        a1["state"] == "GREEN" and a1["name_cn"] == ["劉昃恩"]
        and "凱基投顧" in a1["name_cn_dropped"]
        and a2["state"] == "UNVERIFIABLE" and a3["state"] == "NODATA",
        f"({a1['state']}/{a1['name_cn']} · {a2['state']} · {a3['state']})")

    # ⑫ 三段式槽位:`(代號,短碼,評等)` —— 逐 token 試,命中即取
    tri = rating_from_filename("晶心科(6533,N,中立)-CTBC251208", words, R)
    chk("⑫ **三段式槽位**`(6533,N,中立)`:槽位裡是`短碼,評等`兩段,只切 `_` 會整段變成 `N,中立` 對不上冊。"
        "加切逗號後逐 token 試、命中即取。括號槽是**受限命名空間**,`N`/`B`/`NR` 這種一兩碼在這裡才認得"
        "(批678 短碼律管的是內文,內文一律不收)。**負控**:`Note` 三段切完仍然全不中 → 照樣 UNRATED_SLOT",
        tri["state"] == "GREEN"
        and rating_from_filename("南亞科(7728,Note)", words, R)["state"] == "UNRATED_SLOT",
        f"({tri['state']} · raw={tri.get('raw')!r})")

    # ⑬ 錨點回溯法:逐 Email 各自開窗,**不得串位**
    THREE = ("本報告純屬研究參考。\n林大衛 David Lin\n資深產業分析師 / Senior Analyst\n"
             "(02)2345-6789 ext 123\ndavid.lin@ctbcsec.com\n\n"
             "王大明 Da-Ming Wang\n策略分析師 / Strategist\n(02)8888-1234\n"
             "da-ming.wang@citi.com\n\n"
             "John Doe\nHead of Research\n+852 2971 6686\njohn.doe@morganstanley.com\n")
    cs = contacts_of(THREE)
    chk("⑬ **錨點回溯法**(操作員 2026-09-23 逐字給定):逐個 Email 各自開一個視窗,窗內才抽姓名/職稱/電話。"
        "**負控 —— 這一檢的全部重點**:三位分析師,第三位**不准**拿到第二位的電話 `(02)8888-1234`"
        "(實測就是這樣串過位:80 字元視窗往回伸會伸進上一個人的區塊,所以視窗起點要卡在前一個錨點之後)。"
        "`da-ming.wang` 的 `-` 要留著 → `Da-Ming Wang`(操作員給的預期輸出)",
        len(cs) == 3
        and [c["at_left"] for c in cs] == ["David Lin", "Da-Ming Wang", "John Doe"]
        and [c["broker"] for c in cs] == ["CTBC", "CITI", "MORGAN STANLEY"]
        and cs[2]["phone"] == ["+852 2971 6686"]
        and cs[0]["name_cn"] == ["林大衛"] and cs[1]["name_cn"] == ["王大明"],
        f"({len(cs)} 位 · 第三位電話 {cs[2]['phone'] if len(cs) > 2 else '—'})")

    # ⑭ 操作員原文逐條實測:對的照收,打破的寫明是哪一個探針打破的
    tpe3 = [p for p in phones_of("研究部 (03) 578-1234") if p["state"] == "HIT"]
    en_bad = contacts_of("Senior Analyst\nTel Fax\na@kgi.com")
    cn_bad = contacts_of("分析師的看法是這樣\nb@kgi.com")
    chk("⑭ **操作員原文逐條實測**(as_given 一字不改留冊上,corrected 寫明誰打破它):"
        "① 原文台灣式把區碼寫死 `2`,`(03) 578-1234` 抓不到 → 放寬 `\\d{1,2}` 後要收得到;"
        "② 原文英文姓名式尾巴是 `*`,`Senior Analyst` / `Tel Fax` **整個被當成姓名** → 用職稱表當擋板扣掉;"
        "③ 原文中文姓名錨點式在 `分析師的看法是這樣` 抓出 `的看法是` → 虛詞擋板擋掉",
        bool(tpe3)
        and not any(n.lower().endswith("analyst") for c in en_bad for n in c["name_en"])
        and not any("的看法" in w or w in ("看法是", "的看法是") for c in cn_bad for w in c["name_cn"]),
        f"((03)→{[p['hit'] for p in tpe3]} · 職稱當姓名 {[n for c in en_bad for n in c['name_en']]} · "
        f"虛詞當姓名 {[w for c in cn_bad for w in c['name_cn']]})")

    chk("⑦ 唯讀零網路:本支只讀冊、只比對字串,不出網、不寫檔",
        not banned, f"(違禁 {banned or '無'})")

    print("  [計] %d 檢 OK %d · FAIL %d" % (len(ran), len(ran) - len(fails), len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a or "--self-test" in a:
        return selftest()
    R = rules()
    words, _ = _rating_dict()
    for s in a or []:
        stem = Path(s).stem
        print(f"{stem[:46]:48s} {rating_from_filename(stem, words, R)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

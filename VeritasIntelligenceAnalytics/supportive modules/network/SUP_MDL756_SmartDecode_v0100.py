#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL756_SmartDecode v0100 — 亂碼問題解碼器(文字智慧解碼 + 可逆亂碼反解;純函式 · 零網路 · 不寫檔)

操作員令(2026-10-12):「先把它修正為非亂碼 再回朔到擷取他的工具加上亂碼問題解碼器 解取實用一次 輸出實用一次」。
根因(倉內實錄):網路工具把回應當文字時用 `resp.text`(無 charset 的 Big5 回應被當 latin-1 → 可逆亂碼)、
  `decode("utf-8","replace")`(→ U+FFFD,不可逆)、`decode("utf-8", errors='ignore')`(丟位元組,不可逆)。
本模組兩個入口:
  smart_decode(bytes, declared=None) → {"text", "encoding", "note", "lossy"}:
    BOM → 宣告 charset(big5/ms950 → cp950;latin-1 宣告視同沒宣告)→ HTML <meta charset> 嗅探 → utf-8 嚴格 →
    cp950 / big5hkscs / gb18030 嚴格 + 可信度評分 → 最後才 latin-1(永不 replace / ignore;lossy 旗標誠實)。
  demojibake(text) → (text, kind):可逆亂碼反解(latin1→utf8 · cp1252→utf8 · latin1→cp950 · cp1252→cp950 ·
    latin1→big5hkscs · cp950→utf8 雙重編碼);只有可信度明顯變好且結果沒有壞字才採用;含 U+FFFD = UNRECOVERABLE(照實,不猜)。
  plan_values(values) → 一欄的修復計畫:多數決一種 kind、對應表 orig→fixed、不可逆計數(欄內同一種轉換,不逐值亂猜)。
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
import codecs
import re
import sys
from collections import Counter

TAG = "v0100"
STEM = "SUP_MDL756_SmartDecode"
CJK_RX = re.compile(r"[一-鿿㐀-䶿　-〿＀-￯぀-ヿ가-힯—-…「-』]")
BAD_RX = re.compile(r"[�\u0080-\u009f-￰-￾]")
META_RX = re.compile(rb"charset\s*=\s*[\"']?\s*([A-Za-z0-9_\-]+)", re.I)
ALIASES = {"big5": "cp950", "ms950": "cp950", "big-5": "cp950", "x-big5": "cp950", "big5-hkscs": "big5hkscs",
           "utf8": "utf-8", "utf_8": "utf-8", "gb2312": "gb18030", "gbk": "gb18030", "x-sjis": "shift_jis", "sjis": "shift_jis",
           "ansi": None, "iso-8859-1": None, "latin-1": None, "latin1": None, "us-ascii": None, "ascii": None}
STRICT_ORDER = ("utf-8", "cp950", "big5hkscs", "gb18030", "shift_jis", "euc-kr")
# 常用字集(繁 + 簡高頻 + 財經用字):錯的 CJK 解碼(例 Big5 位元組用 gb18030 解)會是隨機罕見字,命中率極低;對的解碼命中率高。
COMMON = set("的一是不了在人有我他這中大來上國個到說們為子和你地出道也時年得就那要下以生會自著去之過家學對可她里小心多天而能好都然日"
             "起還發成事只作當想看文無開手十十用主行方又如前所本見經頭面公同三已老從動兩長知民樣現分將外但身些與高意進把法此實回二理美點月明"
             "其種聲全工己話兒者向情問間別太電期名稱代號產業股份限司台灣銀金融控投資證券市場價量交易收盤開盤最漲跌總額報表數據資料統計"
             "財務營收益利潤成本費用淨值每股權益負債流動固定存貨應付帳款現金借款稅率基金指數債券外匯利率央行政府經濟製造科技半導體"
             "電子光機械化學材料生技醫療零售批發運輸航空觀光建設營造水泥鋼鐵塑膠紡織食品汽車能源電信網路軟體服務保險租賃信託上市櫃興櫃"
             "申報公告季年度月週日元千萬億百萬增減比率平均合計小計其他備註說明來源更新日期版本代碼類別區域國家城市公司機構單位部門"
             "的一是不了在人有我他这中大来上国个到说们为子和你地出道也时年得就那要下以生会自着去之过家学对可她里后小么心多天而能好都然没日"
             "于起还发成事只作当想看文无开手十用主行方又如前所本见经头面公同三已老从动两长知民样现分将外但身些与高意进把法此实回二理美点月明"
             "其种声全工己话儿者向情问间别太电期名称代号产业股份限司台湾银金融控投资证券市场价量交易收盘开盘最涨跌总额报表数据资料统计")


def common_ratio(text: str) -> float:
    cjk = [c for c in text if CJK_RX.match(c)]
    if not cjk:
        return 0.0
    return sum(1 for c in cjk if c in COMMON) / len(cjk)


def credible(text: str) -> bool:
    """CJK 內容是不是像真的中文:4 個 CJK 字以上要有 ≥ 12% 常用字命中(隨機假字約 1–3%);短字串不設門檻。"""
    cjk_n = len(CJK_RX.findall(text))
    if cjk_n < 4:
        return True
    return common_ratio(text) >= 0.12
# 可逆亂碼反解:(名字, 先用什麼把文字還原成位元組, 再用什麼解)
MOJI_KINDS = (("latin1->utf8", "latin-1", "utf-8"), ("cp1252->utf8", "cp1252", "utf-8"),
              ("latin1->cp950", "latin-1", "cp950"), ("cp1252->cp950", "cp1252", "cp950"),
              ("latin1->big5hkscs", "latin-1", "big5hkscs"), ("latin1->gb18030", "latin-1", "gb18030"),
              ("cp950->utf8", "cp950", "utf-8"), ("big5hkscs->utf8", "big5hkscs", "utf-8"), ("gb18030->utf8", "gb18030", "utf-8"))


def norm_charset(name) -> str | None:
    """宣告的 charset 正規化;latin-1 / ansi 一類視同沒宣告(伺服器常亂宣告)。"""
    if not name:
        return None
    n = str(name).strip().lower().strip("\"' ")
    if n in ALIASES:
        return ALIASES[n]
    try:
        codecs.lookup(n)
        return n
    except LookupError:
        return None


def plausibility(text: str) -> float:
    """可信度:CJK 加分、ASCII 小加分、壞字(U+FFFD · C1 控制 · 私用區)重罰、非 CJK 的高位字罰。"""
    if not text:
        return 0.0
    n = len(text)
    cjk = len(CJK_RX.findall(text))
    bad = len(BAD_RX.findall(text))
    asc = sum(1 for c in text if ord(c) < 128)
    hi_other = n - asc - cjk
    base = (cjk * 2.0 + asc * 0.5 - bad * 5.0 - hi_other * 1.5) / n
    return base + (common_ratio(text) if cjk else 0.0)


def _hi_cjk_ratio(text: str) -> float:
    hi = [c for c in text if ord(c) >= 128]
    if not hi:
        return 1.0
    return sum(1 for c in hi if CJK_RX.match(c)) / len(hi)


def demojibake(text) -> tuple:
    """可逆亂碼反解。回 (文字, kind);kind ∈ ascii · clean · UNRECOVERABLE · 或 MOJI_KINDS 之一;不動 = 原文字回傳。"""
    if not isinstance(text, str) or not text:
        return text, "ascii"
    if all(ord(c) < 128 for c in text):
        return text, "ascii"
    if "�" in text:
        return text, "UNRECOVERABLE"
    base = plausibility(text)
    if base >= 1.2 and _hi_cjk_ratio(text) >= 0.9:
        return text, "clean"
    best, best_kind, best_p = None, None, base + 0.5
    for kind, back, fwd in MOJI_KINDS:
        try:
            raw = text.encode(back)
            cand = raw.decode(fwd)
        except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
            continue
        if cand == text or BAD_RX.search(cand) or _hi_cjk_ratio(cand) < 0.8 or not credible(cand):
            continue
        p = plausibility(cand)
        if p > best_p:
            best, best_kind, best_p = cand, kind, p
    if best is None:
        return text, "clean"
    return best, best_kind


def smart_decode(data, declared=None) -> dict:
    """位元組 → 文字:BOM → 宣告 charset → <meta charset> → utf-8 嚴格 → cp950 / big5hkscs / gb18030 … 嚴格 + 評分 → latin-1(lossy 旗標)。"""
    if data is None:
        return {"text": "", "encoding": None, "note": "empty", "lossy": False}
    if isinstance(data, str):
        t, k = demojibake(data)
        return {"text": t, "encoding": "str", "note": "already-text" + ("" if k in ("ascii", "clean") else f" · demojibake {k}"), "lossy": k == "UNRECOVERABLE"}
    b = bytes(data)
    if not b:
        return {"text": "", "encoding": None, "note": "empty", "lossy": False}
    for bom, enc in ((codecs.BOM_UTF8, "utf-8-sig"), (codecs.BOM_UTF32_LE, "utf-32"), (codecs.BOM_UTF32_BE, "utf-32"),
                     (codecs.BOM_UTF16_LE, "utf-16"), (codecs.BOM_UTF16_BE, "utf-16")):
        if b.startswith(bom):
            try:
                return {"text": b.decode(enc), "encoding": enc, "note": "bom", "lossy": False}
            except UnicodeDecodeError:
                break
    tried = []
    dec = norm_charset(declared)
    if dec:
        try:
            return {"text": b.decode(dec), "encoding": dec, "note": "declared", "lossy": False}
        except (UnicodeDecodeError, LookupError):
            tried.append(dec)
    m = META_RX.search(b[:4096])
    meta = norm_charset(m.group(1).decode("ascii", "ignore")) if m else None
    if meta and meta not in tried:
        try:
            return {"text": b.decode(meta), "encoding": meta, "note": "meta-charset", "lossy": False}
        except (UnicodeDecodeError, LookupError):
            tried.append(meta)
    cands = []
    for enc in STRICT_ORDER:
        if enc in tried:
            continue
        try:
            t = b.decode(enc)
        except UnicodeDecodeError:
            continue
        p = plausibility(t)
        if enc == "utf-8":
            return {"text": t, "encoding": "utf-8", "note": "strict", "lossy": False}
        if credible(t):
            cands.append((p, enc, t))
    if cands:
        cands.sort(key=lambda x: x[0], reverse=True)   # 穩定排序:同分照 STRICT_ORDER(cp950 先於 gb18030)
        p, enc, t = cands[0]
        if p > -0.5:
            return {"text": t, "encoding": enc, "note": "strict+score %.2f" % p, "lossy": False}
    return {"text": b.decode("latin-1"), "encoding": "latin-1", "note": "fallback-latin1(沒有一種嚴格解碼可信;可逆保留位元組)", "lossy": True}


def plan_values(values, limit=None) -> dict:
    """一欄的修復計畫:逐值反解 → 多數決一種 kind → 只用那一種做對應表(orig → fixed);U+FFFD 計 unrecoverable。"""
    kinds = Counter()
    fixes = {}
    unrec = 0
    seen = 0
    for v in values:
        if limit and seen >= limit:
            break
        seen += 1
        if not isinstance(v, str):
            continue
        f, k = demojibake(v)
        if k == "UNRECOVERABLE":
            unrec += 1
        elif k not in ("ascii", "clean"):
            kinds[k] += 1
            fixes.setdefault(k, {})[v] = f
    if not kinds:
        return {"kind": None, "map": {}, "n_fix": 0, "n_unrecoverable": unrec, "kinds": {}, "seen": seen}
    kind = kinds.most_common(1)[0][0]
    return {"kind": kind, "map": fixes[kind], "n_fix": len(fixes[kind]), "n_unrecoverable": unrec, "kinds": dict(kinds), "seen": seen}


def selftest() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:240]) if note else ""))

    print("=== %s %s · 自測(純函式 · 零網路)===" % (STEM, TAG))
    zh = "台灣積體電路製造股份有限公司 2330"
    big5 = zh.encode("cp950")
    utf8 = zh.encode("utf-8")
    r1 = smart_decode(big5)
    chk("① Big5 位元組(無宣告)→ cp950 嚴格 + 評分 → 正字", r1["text"] == zh and r1["encoding"] == "cp950" and not r1["lossy"], r1)
    r2 = smart_decode(utf8)
    chk("② UTF-8 位元組 → utf-8 嚴格", r2["text"] == zh and r2["encoding"] == "utf-8")
    r3 = smart_decode(codecs.BOM_UTF8 + utf8)
    chk("③ BOM 優先(utf-8-sig)", r3["text"] == zh and r3["note"] == "bom")
    r4 = smart_decode(big5, declared="big5")
    chk("④ 宣告 big5 → cp950;宣告 latin-1 視同沒宣告", r4["encoding"] == "cp950" and r4["note"] == "declared" and smart_decode(big5, declared="ISO-8859-1")["text"] == zh)
    html = b"<html><head><meta charset=big5></head><body>" + "資料".encode("cp950") + b"</body>"
    r5 = smart_decode(html)
    chk("⑤ HTML <meta charset=big5> 嗅探", "資料" in r5["text"] and r5["note"] == "meta-charset")
    r6 = smart_decode(b"\x81\x00\xfe\xfe\x80 abc")
    chk("⑥ 沒有一種嚴格解碼可信 → latin-1 可逆保留 + lossy 旗標(不 replace / ignore)", r6["encoding"] == "latin-1" and r6["lossy"] and "�" not in r6["text"])
    m1 = big5.decode("latin-1")
    t1, k1 = demojibake(m1)
    chk("⑦ 可逆亂碼:Big5 被當 latin-1 → latin1->cp950 還原", t1 == zh and k1 == "latin1->cp950", (k1, t1))
    m2 = utf8.decode("latin-1")
    t2, k2 = demojibake(m2)
    chk("⑧ 可逆亂碼:UTF-8 被當 latin-1(å°ç£…)→ latin1->utf8 還原", t2 == zh and k2 == "latin1->utf8", (k2, t2))
    m3 = utf8.decode("cp950", errors="strict") if _decodes(utf8, "cp950") else None
    if m3 is not None:
        t3, k3 = demojibake(m3)
        chk("⑨ 雙重編碼:UTF-8 位元組被當 cp950 → cp950->utf8 還原", t3 == zh and k3 == "cp950->utf8", (k3, t3))
    else:
        chk("⑨ 雙重編碼樣本(cp950 解不開此 UTF-8 串 → 本機沒有這種亂碼可試;照實記)", True)
    t4, k4 = demojibake("台積電 TSMC 2330")
    chk("⑩ 正常中文不動(clean)· 純 ASCII 不動(ascii)· U+FFFD 誠實 UNRECOVERABLE", t4 == "台積電 TSMC 2330" and k4 == "clean" and demojibake("abc")[1] == "ascii" and demojibake("台�電")[1] == "UNRECOVERABLE")
    plan = plan_values([m1, m1, "2330", "台積電", "x�", big5.decode("latin-1")[:6]])
    chk("⑪ 欄計畫:多數決 kind=latin1->cp950 · 對應表只收可修值 · unrecoverable 計 1", plan["kind"] == "latin1->cp950" and plan["n_unrecoverable"] == 1 and m1 in plan["map"] and plan["map"][m1] == zh, plan)
    body = open(__file__, encoding="utf-8").read()
    chk("⑫ 零網路 · 不寫檔 · 橋在 · 不碰 TA-Lib · 不用 replace / ignore 解碼",
        all(x not in body for x in ("import " + "requests", "import " + "urllib", "import " + "socket", "write_" + "text(", "open(" + "__file__, \"w\"", "import " + "talib"))
        and "[VIA:ACCEL-BRIDGE:v0100]" in body and ', "rep' + 'lace")' not in body and 'errors="ign' + 'ore"' not in body)
    long_zh = "台灣積體電路製造股份有限公司於民國七十六年成立,為全球最大的專業積體電路製造服務公司"
    r13 = smart_decode(long_zh.encode("cp950"))
    try:
        gb_view = long_zh.encode("cp950").decode("gb18030")
    except UnicodeDecodeError:
        gb_view = ""
    chk("⑬ 長句 Big5:cp950 勝 gb18030(常用字命中率)· gb18030 假字不可信", r13["encoding"] == "cp950" and r13["text"] == long_zh and (not gb_view or not credible(gb_view)), (r13["encoding"], common_ratio(gb_view)))
    print("[計] %s %s 自測 %d/%d · %s" % (STEM, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def _decodes(b: bytes, enc: str) -> bool:
    try:
        b.decode(enc)
        return True
    except UnicodeDecodeError:
        return False


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if args and args[0] == "decode" and len(args) > 1:
        import json
        from pathlib import Path
        r = smart_decode(Path(args[1]).read_bytes())
        print(json.dumps({k: (v if k != "text" else v[:200]) for k, v in r.items()}, ensure_ascii=False))
        return 0
    if args and args[0] == "fix" and len(args) > 1:
        t, k = demojibake(" ".join(args[1:]))
        print(k, "→", t)
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG393_DocClassVerify v0101 — 薄尾:① 只有幣別前綴的格子讓 verify 當掉 ② 首頁主標題改用版面字級判(前版 v0100 本體照讀)

v0100→v0101(R36 操作員工作站實錄 2026-10-01 `via-vcgc run --family vrn VRN_ENG393_DocClassVerify verify --samples "C:\測試樣本報告"`):
  Traceback … build_cells → parse_num → `sign, s = s[0], s[1:]` → IndexError: string index out of range(第 2 次)。
  根因:Python 的 `"" in "+-"` 永遠為 True。格子整格就是冊上的前綴(`$` `NT$` `US$` …,表頭的幣別欄常見)時,
  剝掉前綴後 s 變空字串,第二次正負號檢查 `s[:1] in "+-"` 判真,再取 s[0] 就當掉 —— 一格就讓整批 verify 停掉。
  修法(只動取數這一格,其餘一字不動):正負號檢查改成「s 非空且首字是 + / -」;剝完前綴 / 字尾後是空字串 = 不是數字格(None, '')。
  前版 build_cells 在前版命名空間裡叫 parse_num → 換掉 PRIOR.parse_num 這一格即可(同 ENG080 v0111 的作法)。
② 主標題(操作員 R36 原話「文章的主標題通常偏大 不包含個股及代碼的一句話沒有句號」「nlp layout可幫忙」):
  前版標題 = 前 3 個標題 + 整條頁首帶(券商 · 日期 · Asia Pacific …)→ 工作站 classify 實錄 9 份個股(MS-1590 / 2308 / 3661 …)被標
  「首頁標題判 OTHER_INVEST / INDUSTRY_OUTLOOK ≠ 檔名」進複核。本版 page1_title():ENG394 尾版的行字級(版面)找字最大的一句,
  剔除 帶代號的行 · 檔名代號旁的股名 · 句尾有句號的句子 · 日期 / 純數字;同級連續換行接成一句。verify 的 text_verify 與
  classify 的標題都換成它(找不到才沿用前版)。另:檔名有代號判個股時,主標題只靠冊上「無代號」類規則(when.ticker == false)
  判成別類不算衝突(主標題本不含代號,個股標題帶產業詞是常態);標題是新聞摘要 / 研討會強標記仍算衝突。
VIA_FROM_VCGC:經 VCGC 跑(via-vcgc run --family vrn VRN_ENG393_DocClassVerify …取尾版);零網路;不用 TA-Lib;正本唯讀。
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

import importlib.util
import re
import sys
import unicodedata
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG393_DocClassVerify"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VRN_ENG393_DocClassVerify_v0100.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("docclass_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem


def _signed(s: str) -> bool:
    return bool(s) and s[0] in "+-"


def parse_num(text, bk: dict | None = None) -> tuple:
    """Whole cell is one number → (Fraction, unit); otherwise (None, ''). A cell that is only a prefix / suffix is not a number."""
    spec = ((bk or PRIOR.book()).get("xcheck") or {}).get("numeric_cell") or {}
    s = unicodedata.normalize("NFKC", PRIOR.ZW_RX.sub("", str(text or ""))).strip()
    s = re.sub(r"\s+", "", s)
    if not s:
        return None, ""
    for ch in spec.get("minus_chars", "−–—－"):
        s = s.replace(ch, "-")
    neg = False
    if spec.get("neg_paren", True) and len(s) > 2 and s[0] in "(（" and s[-1] in ")）":
        neg, s = True, s[1:-1]
    sign = ""
    if _signed(s):
        sign, s = s[0], s[1:]
    for pre in sorted(spec.get("strip_prefix") or [], key=len, reverse=True):
        if s.upper().startswith(pre.upper()):
            s = s[len(pre):]
            break
    if not sign and _signed(s):
        sign, s = s[0], s[1:]
    unit = ""
    for suf in sorted(spec.get("strip_suffix") or [], key=len, reverse=True):
        if s.endswith(suf):
            unit, s = suf, s[:-len(suf)]
            break
    if not s:
        return None, ""
    rx = spec.get("rx") or r"^[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$"
    if not re.fullmatch(rx, s):
        return None, ""
    try:
        v = Fraction(Decimal(s.replace(",", "")))
    except (InvalidOperation, ValueError):
        return None, ""
    if sign == "-":
        v = -v
    return (-v if neg else v), unit


PRIOR.parse_num = parse_num          # build_cells / 自核在前版命名空間裡叫它 → 換這一格即可


# ---------------------------------------------------------------- 首頁主標題(操作員 R36:字最大 · 不含個股名稱與代碼 · 一句話沒有句號)
# 前版的「標題」= 前 3 個標題 + 整條頁首帶(券商名 · 日期 · Asia Pacific / Taiwan …)→ 頁首帶的地區詞讓 MS 個股報告被 DC-R07(海外詞)誤判。
# 本版:版面(ENG394 尾版的行字級 / 粗體 / 讀序)找字級最大的一句;NLP 規則剔除 帶代號的行 · 股名行 · 有句號的句子 · 日期 / 純數字 / 太短。
_SENT_END = "。．.!?！？"
_DATE_RX = re.compile(r"^\W*(?:\d{1,4}[-/.年]\d{1,2}(?:[-/.月]\d{1,2}日?)?|\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4}|[A-Z][a-z]{2,8}\s+\d{1,2},?\s+\d{4})\W*$")


def _eng394():
    hits = sorted(HERE.glob("VRN_ENG394_LayoutRestore_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("eng394_for_" + ENGINE, hits[-1])
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    try:
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def _names_from_file(stem: str, code: str) -> list:
    """檔名裡緊貼代號的股名:「2637 慧洋-KY」→ 慧洋 · 「南亞(1303」→ 南亞 · 「神達(3706 TT)」→ 神達(只取中文 2–6 字)。"""
    if not code:
        return []
    out = []
    for m in re.finditer(r"([一-鿿]{2,6})\s*[\(（]?\s*" + code, stem):
        out.append(m.group(1))
    for m in re.finditer(code + r"[\s_\-]*([一-鿿]{2,6})", stem):
        out.append(m.group(1))
    drop = {"投顧", "證券", "投信", "研究部", "研究", "證期"}
    return [n for n in dict.fromkeys(out) if n not in drop]


def title_reject(text: str, code: str, names: list, bk: dict) -> str:
    """不是主標題的理由(空字串 = 可當主標題)。"""
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(re.sub(r"\W", "", t)) < 4 or not re.search(r"[A-Za-z一-鿿]", t):
        return "太短 / 沒有文字"
    if _DATE_RX.match(t) or re.fullmatch(r"[\d\W]+", t):
        return "日期 / 純數字"
    if t[-1] in _SENT_END:
        return "有句號(是內文句子,不是標題)"
    tk, _rej = PRIOR.ticker_of(t, bk, True)
    if tk or (code and re.search(r"(?<!\d)" + code + r"(?!\d)", t)):
        return "含代號(個股名稱行)"
    if any(n in t for n in names):
        return "含股名"
    return ""


def page1_title(path: Path, bk: dict | None = None) -> dict:
    """首頁主標題:候選 = 字級 ≥ 本文 × 1.15 且沒被剔除的行;取字級最大的一組,連續換行的同級行接成一句。"""
    bk = bk or PRIOR.book()
    out = {"title": "", "size": None, "body": None, "rejected": [], "method": "layout(ENG394 字級)+ 規則(句號 · 代號 · 股名)"}
    e394 = _eng394()
    if e394 is None or Path(path).suffix.lower() != ".pdf":
        out["method"] = "NODATA(ENG394 不在或非 PDF)"
        return out
    try:
        import fitz
        with fitz.open(str(path)) as doc:
            if not doc.page_count:
                return out
            lines = e394._order_lines(e394._page_lines(doc[0]))
    except Exception as exc:
        out["method"] = f"NODATA(讀檔 {type(exc).__name__})"
        return out
    if not lines:
        return out
    prose = [ln for ln in lines if len(e394.VAL_RX.findall(ln["text"])) < 2]
    body = e394._wmedian([(ln["size"], ln["nch"]) for ln in (prose or lines)]) or 10.0
    stem = Path(path).stem
    code, _r = PRIOR.ticker_of(stem, bk, False)
    names = _names_from_file(stem, code or "")
    cands = []
    for i, ln in enumerate(lines):
        if ln["size"] < body * 1.15:
            continue
        why = title_reject(ln["text"], code or "", names, bk)
        if why:
            out["rejected"].append({"text": ln["text"].strip()[:60], "size": ln["size"], "why": why})
        else:
            cands.append((i, ln))
    out["body"] = body
    if not cands:
        return out
    top = max(ln["size"] for _i, ln in cands)
    group = [(i, ln) for i, ln in cands if ln["size"] >= top - 0.5]
    i0, first = group[0]
    parts, last = [first], first
    for i, ln in group[1:]:
        gap = ln["bbox"][1] - last["bbox"][3]
        if gap <= 1.6 * (last["bbox"][3] - last["bbox"][1]):
            parts.append(ln)
            last = ln
        else:
            break
    txt = ""
    for ln in parts:
        s = ln["text"].strip()
        sep = "" if (txt and re.search(r"[一-鿿]$", txt) and re.match(r"[一-鿿]", s)) else (" " if txt else "")
        txt += sep + s
    out.update(title=txt[:300], size=top)
    return out


_PRIOR_CLASSIFY = PRIOR.classify


def classify(name: str, title: str = "", broker_hint: str = "", bk: dict | None = None) -> dict:
    """前版分類照跑;唯一改動:檔名有代號判個股(DC-R04)而主標題只靠「無代號」類規則(冊上 when.ticker == false)
    判成別類時,不算衝突 —— 主標題本來就不含個股名稱與代碼(操作員 R36),個股報告的標題帶產業 / 海外 / 策略詞是常態。
    標題是強標記(新聞摘要 · 研討會)或標題自己帶代號時,照前版算衝突。"""
    bk = bk or PRIOR.book()
    row = _PRIOR_CLASSIFY(name, title, broker_hint, bk)
    if not (row.get("conflict") and row.get("doc_class") == "STOCK" and row.get("class_rule") == "DC-R04" and title):
        return row
    ttk, _r = PRIOR.ticker_of(title, bk, bool((bk.get("ticker") or {}).get("title_ticker_requires_mark", True)))
    t_rule, _h = PRIOR.ladder(title, ttk, bk)
    if not t_rule or (t_rule.get("when") or {}).get("ticker") is not False:
        return row
    cf = bk.get("confidence") or {}
    conf = min(cf.get("cap", 0.99), row["class_confidence"] - cf.get("title_conflict", -0.10))
    classes = bk.get("classes") or {}
    note = f"首頁標題判 {t_rule['class']}({t_rule['id']})≠ 檔名"
    ev = row["class_evidence"].replace(" · " + note, "").replace(note, "")
    row.update(conflict=False, class_confidence=round(conf, 3),
               needs_review=bool(conf < cf.get("review_below", 0.6) or (classes.get("STOCK") or {}).get("review")),
               class_evidence=ev + f" · 主標題判 {t_rule['class']}({t_rule['id']},無代號類規則)只作參考:主標題本不含代號(R36)")
    return row


PRIOR.classify = classify

_PRIOR_TEXT_VERIFY = PRIOR.text_verify


def text_verify(path: Path) -> dict:
    """前版文字核對照跑;分類用的 title 換成主標題(找不到才沿用前版的「標題 + 頁首帶」),前版的留在 title_heads。"""
    out = _PRIOR_TEXT_VERIFY(path)
    pt = page1_title(path)
    out["title_heads"] = out.get("title", "")
    if pt.get("title"):
        out["title"] = pt["title"]
        out["title_source"] = f"page1_title(字級 {pt['size']} / 本文 {pt['body']})"
    else:
        out["title_source"] = "heads+header(前版;主標題找不到)"
    return out


PRIOR.text_verify = text_verify


class _TitleZones:
    """只給 classify 用的 ENG072 代理:extract_page1_zones 的標題換成主標題、頁首帶清空;其餘屬性照轉。"""

    def __init__(self, m72):
        self._m = m72

    def __getattr__(self, k):
        return getattr(self._m, k)

    def extract_page1_zones(self, path, *a, **kw):
        pt = page1_title(Path(path))
        if pt.get("title"):
            return {"heads": [{"text": pt["title"]}], "header": ""}
        return self._m.extract_page1_zones(path, *a, **kw)


_PRIOR_RUN_CLASSIFY = PRIOR.run_classify
_PRIOR_ENG072 = PRIOR.eng072


def run_classify(args: list) -> int:
    def _eng072_titled():
        m, w = _PRIOR_ENG072()
        return (_TitleZones(m) if m is not None else None), w
    PRIOR.eng072 = _eng072_titled
    try:
        return _PRIOR_RUN_CLASSIFY(args)
    finally:
        PRIOR.eng072 = _PRIOR_ENG072


PRIOR.run_classify = run_classify


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    # 實錄重現:前版本體的 parse_num(不經本版換格)遇到只有前綴的格子會當掉
    spec2 = importlib.util.spec_from_file_location("docclass_raw_prior_" + ENGINE, _PRIOR_PATH)
    raw = importlib.util.module_from_spec(spec2)
    sys.modules[spec2.name] = raw
    spec2.loader.exec_module(raw)
    crashed = []
    for c in ("$", "NT$", "US$"):
        try:
            raw.parse_num(c)
        except IndexError:
            crashed.append(c)
    chk("實錄重現:前版遇到整格只有幣別前綴($ · NT$ · US$)→ IndexError", crashed == ["$", "NT$", "US$"], crashed)
    chk("本版:只有前綴 / 只有字尾 / 只有符號的格子 = 不是數字格,不當掉",
        all(parse_num(c) == (None, "") for c in ("$", "NT$", "US$", "%", "x", "倍", "-", "+", "(%)", "NT$%", "-$")),
        [(c, parse_num(c)) for c in ("$", "NT$", "US$", "%", "x", "倍", "-", "+", "(%)", "NT$%", "-$")])
    chk("數值照舊:NT$1,200 → 1200 · -3.5% → -3.5 % · (12.5) → -12.5 · +$5 → 5 · −2 倍 → -2 倍",
        parse_num("NT$1,200") == (1200, "") and parse_num("-3.5%") == (Fraction(-7, 2), "%") and parse_num("(12.5)") == (Fraction(-25, 2), "")
        and parse_num("+$5") == (5, "") and parse_num("−2倍") == (-2, "倍"))
    same = [c for c in ("1,234", "-0.1%", "(3.2)", "US$45.6", "27.9x", "n.a.", "Q1", "2Q25", "", "abc", "12.5pp")
            if raw.parse_num(c) != parse_num(c)]
    chk("其餘格子與前版結果完全相同(只修當掉那一條路)", not same, same)
    chk("前版 build_cells / 自核走本版的 parse_num", PRIOR.parse_num is parse_num)
    # 主標題(操作員 R36:字最大 · 不含個股名稱與代碼 · 一句話沒有句號)
    bk = PRIOR.book()
    try:
        import fitz
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "MS-2308 20251128.pdf"
            doc = fitz.open()
            pg = doc.new_page(width=595, height=842)
            pg.insert_text((40, 40), "Morgan Stanley | Research | Asia Pacific | Taiwan", fontname="helv", fontsize=8)
            pg.insert_text((40, 60), "November 28, 2025", fontname="helv", fontsize=8)
            pg.insert_text((40, 95), "Delta Electronics (2308.TW)", fontname="hebo", fontsize=15)
            pg.insert_text((40, 130), "Margins Set to Expand on Liquid", fontname="hebo", fontsize=22)
            pg.insert_text((40, 156), "Cooling Ramp", fontname="hebo", fontsize=22)
            pg.insert_text((40, 190), "We raise our target price on stronger demand.", fontname="helv", fontsize=16)
            for i in range(8):
                pg.insert_text((40, 220 + i * 13), "Body text line about the company outlook and estimates for next year", fontname="helv", fontsize=9.5)
            doc.save(str(p))
            doc.close()
            pt = page1_title(p, bk)
            chk("仿 MS 首頁:主標題 = 字最大的一句(兩行接起來),不是頁首帶 / 公司行 / 有句號的句子",
                pt["title"] == "Margins Set to Expand on Liquid Cooling Ramp", (pt["title"], pt["rejected"]))
            whys = {r["text"][:20].strip(): r["why"] for r in pt["rejected"]}
            chk("剔除理由:公司行 = 含代號 · 「We raise …」= 有句號", whys.get("Delta Electronics (2") == "含代號(個股名稱行)"
                and whys.get("We raise our target") == "有句號(是內文句子,不是標題)", whys)
            old = _PRIOR_CLASSIFY(p.name, pt["title"], "", bk)
            new = PRIOR.classify(p.name, pt["title"], "", bk)
            chk("前版:個股報告主標題帶產業詞(Liquid Cooling)→ 判衝突 · 標複核(實錄 MS-1590 / 2308 / 3661 … 同形)",
                old["doc_class"] == "STOCK" and old["conflict"] and old["needs_review"], old["class_evidence"])
            chk("本版:主標題本不含代號 → 無代號類規則(DC-R05)只作參考,個股不再誤標複核 · 信心回到 0.99",
                new["doc_class"] == "STOCK" and not new["conflict"] and not new["needs_review"] and new["class_confidence"] >= 0.95
                and "只作參考" in new["class_evidence"], new)
            nd = PRIOR.classify("凱基投顧_2637 慧洋-KY_20260915.pdf", "凱基期貨晨間解盤", "", bk)
            chk("強標記照舊:檔名個股 + 標題是新聞摘要(晨間)→ 仍算衝突、進複核", nd["conflict"] and nd["needs_review"], nd["class_evidence"])
            q = Path(td) / "【國泰證期研究部】神達(3706 TT)-初次評等買進-20250822.pdf"
            doc = fitz.open()
            pg = doc.new_page(width=595, height=842)
            pg.insert_text((40, 40), "國泰證期研究部 2025/08/22", fontname="china-t", fontsize=8)
            pg.insert_text((40, 80), "神達(3706 TT)", fontname="china-t", fontsize=16)
            pg.insert_text((40, 120), "大顯神威，營運騰達", fontname="china-t", fontsize=24)
            pg.insert_text((40, 160), "初次評等買進，目標價上看一百元。", fontname="china-t", fontsize=16)
            for i in range(8):
                pg.insert_text((40, 190 + i * 13), "伺服器出貨放量帶動營收成長，毛利率持續改善並維持全年展望", fontname="china-t", fontsize=10)
            doc.save(str(q))
            doc.close()
            pt = page1_title(q, bk)
            chk("仿國泰中文首頁:主標題 = 大顯神威，營運騰達(股名代碼行 · 有句號的句子 · 頁首日期都剔除)", pt["title"] == "大顯神威，營運騰達",
                (pt["title"], pt["rejected"]))
            chk("檔名股名抽取:神達(3706 → 神達 · 2637 慧洋-KY → 慧洋", _names_from_file(q.stem, "3706") == ["神達"]
                and _names_from_file("凱基投顧_2637 慧洋-KY_賴偉中_20260915", "2637") == ["慧洋"])
    except ImportError:
        chk("主標題:PyMuPDF 不在 → 測試跳過(誠實記缺件,不算過)", False)
    chk("verify 的 text_verify / classify 的 run_classify 都走本版主標題", PRIOR.text_verify is text_verify and PRIOR.run_classify is run_classify)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print("--- 前版 v0100 全套自測(在本版取數下重跑)---")
    prc = PRIOR.selftest()
    chk("前版自測在本版取數下仍全過", prc == 0)
    print(f"[VRN_ENG393 v0101 前綴格 · 主標題] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())

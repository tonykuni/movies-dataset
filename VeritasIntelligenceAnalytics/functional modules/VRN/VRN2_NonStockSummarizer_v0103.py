#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_NonStockSummarizer v0103 — 薄尾(v0100 · v0101 · v0102 一字不動):核心接口補回先前核心取主張時的排除與去重(PR #722 Codex P2 ×3)

Codex P2:換成 v0400 核心後,v0310 的摘要選句照舊,但先前核心(VRN-2 暫代核心)在取主張時的排除不見了:
  「台積電(2330) EPS 2024 2025 2026 10 20 30 40。」以前不成主張,現在變成 POINT_3 而且報告標 PASS;
  讀檔層標成 TABLE 的 PDF / DOCX 表格區塊也不再排除。
  同一輪另兩項:免責聲明(v0400 的區塊判型不會給 DISCLAIMER)成了 POINT_3;同一句重複四次成了四個一樣的重點
  (v0310 選句認主張號不認字)。
本版在接口(核心 def_extract_claims 外面)補回暫代核心取主張時的全部排除與去重,規則逐字照暫代核心
(不載入暫代核心本身,v0101 ③ 照樣成立):
  ① 區塊:型別是 DISCLAIMER / URL / EMPTY / TABLE、區塊文字命中免責聲明、或區塊本身數字密
     (≥ 6 個數字且數字長度 × 4 ≥ 去空白長度 / 3)→ 整塊不取主張。
  ② 句子:整句是網址、去掉符號數字後不到 4 個字、命中免責聲明、是表格列(≥ 4 個數字,數字位數 ≥ 中英文字數 × 0.6,
     或 ≥ 6 個數字且沒有句讀)、是表單 / 欄位頭(沒有句讀、≥ 16 字、空白分隔 ≥ 5 段、中文過半)→ 不當主張。
  ③ 去重:跟最近 80 句的相似度 ≥ 0.92(去空白後 difflib 比)→ 只留第一次出現的那句。
v0400 / v0310 原檔不動(只包這一次載入的核心物件上的函式);原文照舊留在來源,只是不拿來當摘要句。
零網路 · 不用 TA-Lib · 不 import VCGC · 加速器橋在。用法同 v0102。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import contextlib
import difflib
import importlib.util
import io
import json
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN2_NonStockSummarizer"
ENGINE = "VRN2_NonStockSummarizer v0103"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.PRIOR                                        # load_engine 的本體(v0101 已把它換進 v0100)
V0100 = V0101.PRIOR
_LOAD_V0101 = V0101.load_engine

# ── 規則逐字照 VRN2_NonStockCore_v0100(暫代核心)的 NUMBER_RE / _CJK / def_guess_block_type 的 TABLE / is_table_line / is_form_line ──
NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?\s*%?")
URL_RE = re.compile(r"https?://[^\s<>\"'\uff09)]+")
DISCLAIMER_RE = re.compile(r"\u672c\u520a\u6240\u520a\u8f09\u4e4b\u5167\u5bb9\u50c5\u505a\u70ba\u53c3\u8003|\u50c5\u4f9b\u5167\u90e8\u53c3\u8003|\u50c5\u4f9b\u5167\u90e8\u4f7f\u7528|\u8acb\u52ff\u5916\u50b3|\u514d\u8cac\u8072\u660e|\u6295\u8cc7\u4eba\u61c9\u81ea\u884c|Disclaimer|not an offer", re.I)
_CJK = re.compile(r"[\u4e00-\u9fff]")
SIM_DEDUP = 0.92
SKIP_BLOCK_TYPES = frozenset({"DISCLAIMER", "URL", "EMPTY", "TABLE"})
TABLE_BLOCK_TYPES = SKIP_BLOCK_TYPES                      # \u820a\u540d\u7559\u6bbc


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def is_table_block(text: str) -> bool:
    t = (text or "").strip()
    nums = len(NUMBER_RE.findall(t))
    return nums >= 6 and nums * 4 >= len(re.sub(r"\s", "", t)) / 3


def is_table_line(line: str) -> bool:
    """表格列(數字密、句讀少):不拿來當摘要句,只留在原文。"""
    t = (line or "").strip()
    nums = NUMBER_RE.findall(t)
    if len(nums) < 4:
        return False
    digits = sum(len(re.sub(r"\D", "", n)) for n in nums)
    letters = len(_CJK.findall(t)) + len(re.findall(r"[A-Za-z]", t))
    return digits >= letters * 0.6 or (len(nums) >= 6 and not re.search(r"[，。,；;]", t))


def is_form_line(line: str) -> bool:
    """表單 / 欄位頭:中文為主、空白分隔 ≥ 5 段、沒有句讀。"""
    t = (line or "").strip()
    if re.search(r"[，。；,;！？]", t) or len(t) < 16:
        return False
    toks = t.split()
    cjk = len(_CJK.findall(t))
    return len(toks) >= 5 and cjk >= len(re.sub(r"\s", "", t)) * 0.5


def similarity(a: str, b: str) -> float:
    """同暫代核心的 def_similarity:去空白後 difflib 比(快篩 < 0.5 直接 0)。"""
    a, b = re.sub(r"\s+", "", a or ""), re.sub(r"\s+", "", b or "")
    if not a or not b:
        return 0.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sm.ratio() if sm.real_quick_ratio() >= 0.5 else 0.0


def skip_block(block) -> bool:
    t = block.text or ""
    return block.block_type in SKIP_BLOCK_TYPES or bool(DISCLAIMER_RE.search(t)) or is_table_block(t)


def skip_sentence(s: str) -> bool:
    s = s or ""
    return (bool(URL_RE.fullmatch(s)) or len(re.sub(r"[\W\d_]", "", s)) < 4 or is_table_line(s) or is_form_line(s)
            or bool(DISCLAIMER_RE.search(s)))


def table_filtered(extract):
    """包住核心的 def_extract_claims:照暫代核心排除區塊與句子,再去掉重複句(只留第一次)。"""
    if getattr(extract, "_vrn2_table_filter", False):
        return extract

    def def_extract_claims(blocks):
        out, seen = [], []
        for c in extract([b for b in blocks if not skip_block(b)]):
            if skip_sentence(c.text) or any(similarity(c.text, x) >= SIM_DEDUP for x in seen[-80:]):
                continue
            seen.append(c.text)
            out.append(c)
        return out
    def_extract_claims._vrn2_table_filter = True
    def_extract_claims.__wrapped__ = extract
    return def_extract_claims


def without_disclaimers(text: str) -> str:
    """去掉命中免責聲明的句子(逐行、逐句;句界 。！？!?;;)。"""
    keep = []
    for line in (text or "").split("\n"):
        parts = re.split(r"(?<=[。！？!?；;])", line)
        keep.append("".join(p for p in parts if not DISCLAIMER_RE.search(p)))
    return "\n".join(keep)


def company_map_filtered(company_map):
    """包住 v0310 的 def_company_map:免責聲明句不拿來找「涉及公司」(否則會變成 POINT_3)。"""
    if getattr(company_map, "_vrn2_disclaimer_filter", False):
        return company_map

    def def_company_map(text, *a, **kw):
        return company_map(without_disclaimers(text), *a, **kw)
    def_company_map._vrn2_disclaimer_filter = True
    def_company_map.__wrapped__ = company_map
    return def_company_map


def load_engine():
    eng, st = _LOAD_V0101()
    eng.CORE.def_extract_claims = table_filtered(eng.CORE.def_extract_claims)   # 只改這一次載入的核心物件,不寫檔
    eng.def_company_map = company_map_filtered(eng.def_company_map)              # 這一次載入的 v0310 物件;v0310 原檔不動
    st["table_filter"] = ENGINE
    return eng, st


def _install() -> None:
    V0101.load_engine = load_engine                        # v0101 的 doctor / selftest 叫它模組裡的 load_engine
    V0100.load_engine = load_engine                        # v0100 的 run / analyze 叫它模組裡的 load_engine


def _uninstall() -> None:
    V0101.load_engine = V0100.load_engine = _LOAD_V0101
    eng = V0101._ENGINE_CACHE.get("e")
    if eng is not None and getattr(eng.CORE.def_extract_claims, "_vrn2_table_filter", False):
        eng.CORE.def_extract_claims = eng.CORE.def_extract_claims.__wrapped__
    if eng is not None and getattr(eng.def_company_map, "_vrn2_disclaimer_filter", False):
        eng.def_company_map = eng.def_company_map.__wrapped__


_install()


def run(inputs: list, out: Path, include_stock: bool = False) -> dict:
    return PRIOR.run(inputs, out, include_stock)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(v0100–v0102 / v0310 / v0400 不改;零網路)===" % ENGINE, flush=True)
    eng, _st = load_engine()
    C = eng.CORE
    raw = C.def_extract_claims.__wrapped__
    row = "台積電(2330) EPS 2024 2025 2026 10 20 30 40。"
    prose = "由於 AI 伺服器需求成長,南亞科(2408)2026年獲利可望轉佳,HBM 報價上漲 15%。"
    form = "公司名稱 來億-KY(6890) 報告種類 個股報告評 等 逢低買進"
    tbl = "營收 100 200 300 400 毛利率 40% 41% 42%"
    disc = "免責聲明：本公司及關係企業可能持有台積電(2330)股票，投資人應自行評估風險。"
    rpt = "由於AI伺服器需求成長，台積電(2330)先進製程產能供不應求，預期明年營收將持續上升。"
    blocks = [C.SourceBlock("S1", "x.txt", 1, 1, "PARAGRAPH", row), C.SourceBlock("S2", "x.txt", 1, 2, "TABLE", tbl),
              C.SourceBlock("S3", "x.txt", 1, 3, "PARAGRAPH", prose), C.SourceBlock("S4", "x.txt", 1, 4, "PARAGRAPH", form),
              C.SourceBlock("S5", "x.txt", 1, 5, "PARAGRAPH", disc), C.SourceBlock("S6", "x.txt", 1, 6, "PARAGRAPH", rpt * 4)]
    nf = lambda x: unicodedata.normalize("NFKC", x)                        # noqa: E731  核心會把全形標點轉半形
    row, tbl, prose, form, disc, rpt = map(nf, (row, tbl, prose, form, disc, rpt))
    before = [nf(c.text) for c in raw(blocks)]
    after = [nf(c.text) for c in C.def_extract_claims(blocks)]
    chk("① Codex 重現(三項):未包時表格列 · TABLE 區塊 · 免責聲明都成了主張,重複句成了 4 個主張",
        row in before and tbl in before and disc in before and before.count(rpt) == 4, before)
    chk("② 包上後:表格列 · TABLE 區塊 · 表單列 · 免責聲明都不成主張;重複句只留 1 個;一般敘述句照留",
        prose in after and after.count(rpt) == 1 and not ({row, tbl, form, disc} & set(after)), after)
    with tempfile.TemporaryDirectory(prefix="vrn2_ns103_") as td:
        d = Path(td) / "in"
        d.mkdir()
        (d / "產業專題_晶圓代工.txt").write_text("晶圓代工產業專題\n\n結論:先進製程需求強勁,台積電(2330)2026年營收可望成長 20%。\n\n"
                                           + row + "\n\n若終端需求不如預期,下半年稼動率可能下修。\n\n" + rpt * 4 + "\n\n" + disc + "\n",
                                           encoding="utf-8")
        out = Path(td) / "out"
        with contextlib.redirect_stdout(io.StringIO()):
            run([str(d)], out)
        blob = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in out.rglob("*") if p.is_file() and p.suffix in (".json", ".csv", ".md", ".html"))
        rows = json.loads((out / "RESULTS.json").read_text(encoding="utf-8")).get("report_summary") or []
        points = [str(v) for r in rows for k, v in r.items() if k.startswith("POINT") and v]
        cases = {}
        for name, body in (("disc", "晶圓代工產業專題\n\n先進製程需求強勁,台積電(2330)明年資本支出可望上調。\n\n"
                                    "由於 AI 伺服器需求成長,CoWoS 產能持續吃緊,封測廠訂單能見度拉長。\n\n" + disc + "\n"),
                           ("rpt", "晶圓代工產業專題\n\n" + rpt * 4 + "\n")):
            d2, o2 = Path(td) / ("in_" + name), Path(td) / ("out_" + name)
            d2.mkdir()
            (d2 / "產業專題_晶圓代工.txt").write_text(body, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                run([str(d2)], o2)
            cases[name] = [str(v) for r in json.loads((o2 / "RESULTS.json").read_text(encoding="utf-8")).get("report_summary") or []
                           for k, v in r.items() if k.startswith("POINT") and v]
    chk("③ 端到端:輸出沒有那一列表格;摘要重點裡沒有免責聲明、重複句最多出現一次;正文重點照留",
        "2024 2025 2026 10 20 30 40" not in blob and "營收可望成長" in blob and bool(points) and not any("可能持有台積電" in p for p in points)
        and sum("供不應求" in p for p in points) <= 1, points)
    chk("③b Codex 兩個情境端到端:兩段正文 + 免責聲明 → 重點裡沒有免責聲明(含「涉及公司」那一行);同一句重複四次 → 重點裡只出現一次",
        bool(cases["disc"]) and not any("可能持有" in p or "投資人應自行" in p for p in cases["disc"])
        and sum("供不應求" in p for p in cases["rpt"]) == 1, cases)
    loaded = [n for n, m in list(sys.modules.items()) if Path(str(getattr(m, "__file__", "") or "")).name == V0101.STANDIN_NAME]
    chk("④ 規則逐字照暫代核心,但沒有載入暫代核心(v0101 ③ 照樣成立)", not loaded, loaded)
    buf = io.StringIO()
    _uninstall()
    try:
        with contextlib.redirect_stdout(buf):
            rc_prior = PRIOR.selftest()
    finally:
        _install()
    chk("⑤ 前版 %s 自測整個照過(本版的包裝先拿掉再跑)" % PRIOR_PATH.name, rc_prior == 0, buf.getvalue()[-300:])
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑥ 零網路 · 不用 TA-Lib · 不 import VCGC · 加速器橋在 · 不寫檔",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|http|CGC_)", body, re.M) and "[VIA:ACCEL-BRIDGE:v0100]" in src
        and ".write_text(" not in body and ".write_bytes(" not in body)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑦ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), "%d 支" % len(pub))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[:1] in (["selftest"], ["--selftest"]) or "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())

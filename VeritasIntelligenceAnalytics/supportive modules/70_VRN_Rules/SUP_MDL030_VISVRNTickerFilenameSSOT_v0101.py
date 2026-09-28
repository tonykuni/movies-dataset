#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL030_VISVRNTickerFilenameSSOT v0101 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
自測項:前版本體語法樹可讀、可載入;十個公開定義(正則三式、斷詞器、候選擷取、年份判別、三碼交叉)都在且可呼叫;
並以合成檔名實測:台股四碼正則三式、全形/中英混排斷詞、2021–2030 年份帶判別五種判決、三碼交叉 PASS/FAIL。
本體 __main__ 以 runpy 原樣重跑一次,輸出須與前版一致。純函式、零寫檔、零網路。
前版原封不動留作版史(L04);本檔以 glob 取前版(不釘版號),以 PEP 562 __getattr__ 轉接舊公開面。
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
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "SUP_MDL030_VISVRNTickerFilenameSSOT"
PRIOR_PATH = [p for p in sorted(HERE.glob(STEM + "_v*.py")) if p.name < Path(__file__).name][-1]

_BODY = None


def _body():
    """惰性載入前版本體(本體頂層只有正則/常數/函式定義,載入零副作用)。"""
    global _BODY
    if _BODY is None:
        spec = importlib.util.spec_from_file_location("_" + STEM + "_body", PRIOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _BODY = mod
    return _BODY


def __getattr__(name):
    """PEP 562:舊公開面(TW_TICKER_REGEX / tokenize_filename / cross_check_tricode …)一律轉接前版本體。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_body(), name)


def selftest() -> int:
    import ast
    import contextlib
    import io

    ver = Path(__file__).stem.rsplit("_", 1)[-1]
    res: list[bool] = []

    def chk(label: str, cond, detail: str = "") -> None:
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {label}{(' · ' + detail) if detail else ''}", flush=True)

    print(f"=== {STEM} {ver} 自測(前版本體 {PRIOR_PATH.name})===")
    try:
        ast.parse(PRIOR_PATH.read_text(encoding="utf-8"))
        chk("前版本體語法樹可讀", True, PRIOR_PATH.name)
    except SyntaxError as exc:
        chk("前版本體語法樹可讀", False, f"{type(exc).__name__}: {exc}")
        return _tally(ver, res)
    try:
        b = _body()
        chk("前版本體可載入", True)
    except Exception as exc:
        chk("前版本體可載入", False, f"{type(exc).__name__}: {exc}")
        return _tally(ver, res)

    funcs = ("is_year_band", "tokenize_filename", "extract_filename_ticker_candidates",
             "disambiguate_year_vs_ticker", "core4", "cross_check_tricode")
    regs = ("TW_TICKER_REGEX", "TW_YFINANCE_TICKER_REGEX", "TW_BLOOMBERG_TICKER_REGEX")
    lost = [n for n in funcs if not callable(getattr(b, n, None))] + \
           [n for n in regs if not hasattr(getattr(b, n, None), "fullmatch")]
    chk("公開函式與正則三式俱在且可呼叫", not lost, ("缺:" + ",".join(lost)) if lost else f"{len(funcs)} 函式 + {len(regs)} 正則")
    here_mod = sys.modules.get(__name__)
    chk("PEP 562 轉接:本尾版可直接取舊公開面",
        here_mod is not None and getattr(here_mod, "tokenize_filename", None) is b.tokenize_filename)

    # 正則三式(4 碼、首碼非 0;年份不再烤進正則)
    t = b.TW_TICKER_REGEX
    got = (t.search("abc2330x").group(1), t.search("0050") is None, t.search("12345") is None,
           bool(t.fullmatch("2027")),
           bool(b.TW_YFINANCE_TICKER_REGEX.fullmatch("2330.TW")), bool(b.TW_YFINANCE_TICKER_REGEX.fullmatch("6488.two")),
           bool(b.TW_BLOOMBERG_TICKER_REGEX.fullmatch("2330 TT")), b.TW_BLOOMBERG_TICKER_REGEX.fullmatch("2330TT") is None)
    chk("台股正則三式(2330 抓得到 · 0050/12345 不收 · 2027 不被年份誤殺 · .TW/.two/ TT)",
        got == ("2330", True, True, True, True, True, True, True), repr(got))

    # 斷詞器:標點→分隔、全形→半形、中英數混排切段、副檔名剝除
    tk1 = b.tokenize_filename("台積電2330_法說會.pdf")
    chk("斷詞:台積電2330_法說會.pdf → CJK/DIGIT/CJK 三段",
        tk1 == [("台積電", "CJK"), ("2330", "DIGIT"), ("法說會", "CJK")], repr(tk1))
    tk2 = b.tokenize_filename("２３３０台積電Q3.PDF")
    chk("斷詞:全形數字 NFKC 歸半形 + 大寫副檔名剝除",
        tk2 == [("2330", "DIGIT"), ("台積電", "CJK"), ("Q", "LATIN"), ("3", "DIGIT")], repr(tk2))
    cands, _toks = b.extract_filename_ticker_candidates("2024年報_2330_台積電.pdf")
    chk("候選擷取:2024年報_2330_台積電.pdf → ['2024','2330']", cands == ["2024", "2330"], repr(cands))

    # 年份帶 2021–2030 判別
    d = b.disambiguate_year_vs_ticker
    verdicts = (d("2330")[0], d("2031")[0], d("2027", firstpage_ticker="2027")[:2],
                d("2024", official_set={"2024"})[:2], d("2024", neighbor_text="2024年報")[:2],
                d("2027")[:2], d("2026")[:2])
    want = ("TICKER", "TICKER", ("TICKER", 0.97), ("TICKER", 0.9), ("YEAR", 0.9),
            ("AMBIGUOUS", 0.5), ("AMBIGUOUS", 0.4))
    chk("年份帶判別(帶外=TICKER · 首頁同碼 0.97 · 官方表 0.9 · 年字=YEAR · 無佐證=AMBIGUOUS)",
        verdicts == want, repr(verdicts))

    # 三碼交叉
    ok = b.cross_check_tricode("2330", raw_code="2330", yf_code="2330.TW", bbg_code="2330 TT")
    bad = b.cross_check_tricode("2330", raw_code="2330", yf_code="2317.TW")
    chk("三碼交叉:三碼同 2330 → PASS(3 格)· yfinance 2317.TW → FAIL",
        ok["verdict"] == "PASS" and len(ok["checks"]) == 3 and bad["verdict"] == "FAIL"
        and [c["ok"] for c in bad["checks"]] == [True, False],
        f"{ok['verdict']}/{bad['verdict']}")
    chk("core4:2330.TWO → 2330 · 空值 → None", b.core4("2330.TWO") == "2330" and b.core4("") is None)

    # 本體 __main__ 原樣重跑(正常執行路徑=runpy 前版)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runpy.run_path(str(PRIOR_PATH), run_name="__main__")
    chk("正常執行路徑:runpy 前版 __main__ 輸出一致", buf.getvalue().strip() == "module self-import OK",
        repr(buf.getvalue().strip()))
    return _tally(ver, res)


def _tally(ver: str, res: list) -> int:
    k, n = sum(res), len(res)
    passed = bool(res) and all(res)
    print(f"  [計] {STEM} {ver} 自測 {k}/{n} · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    runpy.run_path(str(PRIOR_PATH), run_name="__main__")

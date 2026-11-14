#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG062_SummarizerV1 v0103 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
前版 argparse 只認 --status/--test/--ticker,本尾在任何本體程式碼跑之前先攔 --selftest。
自測查:本體(同夾前一版,newest-glob 找)可載入、公開類別與 main/summarize_report 等在位;
純函式實測 ReportCodeGenerator/ValuationMethodDetector/KeywordExtractor 詞頻退路/
CategorySentenceExtractor 五點分類/AdjCloseFetcher 代碼轉換與零網路閘(VIA_SELFTEST=1 必 GATED);
再以合成報告文字跑 VRN_Summarizer.process() 端到端比對一標題五點。前版原檔留作歷史不動(L04)。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import sys
from pathlib import Path

STEM = "VRN_ENG062_SummarizerV1"
TAIL_VER = "v0103"
HERE = Path(__file__).resolve().parent
# 尾版律:前一版用 newest-glob 找(比本檔名小的最後一支),不釘版號
PRIOR_PATH = [p for p in sorted(HERE.glob(STEM + "_v*.py")) if p.name < Path(__file__).name][-1]

_BODY = None


def _load_body(fresh: bool = False):
    """惰性載入前版本體為模組。
    本體頂層會試載一串選配重庫(transformers/sentence_transformers/…)並改全域 warnings 過濾,
    故不在本檔 import 時載入,只在 main()/屬性轉接/自測時才載。"""
    global _BODY
    if _BODY is not None and not fresh:
        return _BODY
    name = "_" + STEM + "_body" + ("_selftest" if fresh else "")
    spec = importlib.util.spec_from_file_location(name, PRIOR_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass 需在 sys.modules 找得到本模組
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    if not fresh:
        _BODY = mod
    return mod


def __getattr__(name: str):
    """PEP 562:匯入端照舊看得到前版整面(VRN_Summarizer/summarize_report/LIBS/…)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_load_body(), name)


def selftest() -> int:
    import os

    os.environ["VIA_SELFTEST"] = "1"   # 本體 AdjCloseFetcher.fetch 見此必 GATED:自測零網路
    results: list[bool] = []
    missing: list[str] = []

    def check(label: str, fn) -> None:
        try:
            good, detail = fn()
        except ModuleNotFoundError as exc:
            print(f"  {type(exc).__name__}: {exc}")
            print(f"  NODATA 缺件 {exc.name}(缺件≠壞掉 L16)· 此檢略過:{label}")
            missing.append(str(exc.name))
            return
        except Exception as exc:
            good, detail = False, f"{type(exc).__name__}: {str(exc)[:120]}"
        results.append(bool(good))
        print(f"  [{'OK' if good else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))

    print(f"=== {STEM} {TAIL_VER} 自測(沙盒零網路;本體={PRIOR_PATH.name})===")
    holder: dict = {}

    def _c_load():
        holder["m"] = _load_body(fresh=True)
        return True, PRIOR_PATH.name

    check("本體載入(前版 newest-glob 定位;選配重庫缺席走本體自帶退路)", _c_load)
    b = holder.get("m")
    if b is not None:
        def _c_surface():
            need = ("VRN_Summarizer", "ReportSummary", "AdjCloseFetcher", "KeywordExtractor",
                    "ExtractiveSummarizer", "CategorySentenceExtractor", "ValuationMethodDetector",
                    "ReportCodeGenerator", "summarize_report", "get_version", "get_libs_status", "main")
            miss = [n for n in need if not callable(getattr(b, n, None))]
            ok = not miss and b.get_version() == "1.0.0" and isinstance(b.get_libs_status(), dict)
            return ok, ("缺 " + ",".join(miss)) if miss else f"{len(need)} 項可呼叫 · 版本 {b.get_version()}"
        check("公開面:八個類別與 main/summarize_report/get_version/get_libs_status 在位", _c_surface)

        def _c_code():
            g = b.ReportCodeGenerator()
            x = g.generate("元大", "2330", "台積電", "2025-01-19")
            y = g.generate("Foo", "TW3661", "世芯-KY", "2025/02/03")
            return x == "YT-2330-台積電-20250119" and y == "FOO-3661-世芯-20250203", f"{x} · {y}"
        check("ReportCodeGenerator:券商縮寫/代碼/中文名/日期正規化", _c_code)

        def _c_val():
            d = b.ValuationMethodDetector()
            x = d.detect("採用 DCF 現金流折現模型推算目標價。其他說明")
            y = d.detect("無關文字")
            return x == ("DCF", "採用 DCF 現金流折現模型推算目標價") and y == ("PE", ""), f"{x} · {y}"
        check("ValuationMethodDetector:認出 DCF 並取評價句;無線索預設 PE", _c_val)

        def _c_kw():
            got = b.KeywordExtractor(method="simple").extract("AI AI 需求", top_n=2)
            return got == [("AI", 2 / 3), ("需求", 1 / 3)], str([(w, round(s, 3)) for w, s in got])
        check("KeywordExtractor 詞頻退路:中英詞切分與頻率", _c_kw)

        s_risk = "風險因子需留意地緣政治風險與匯率波動"
        s_grow = "AI 伺服器需求強勁帶動營收年增三成"

        def _c_cat():
            ce = b.CategorySentenceExtractor()
            got = ce.extract(f"短句。{s_risk}。{s_grow}。")
            want = {"conclusion": [], "growth": [s_grow], "valuation": [], "peers": [], "risk": [s_risk]}
            return got == want and ce.get_best_sentence([]) == "", "growth/risk 各一句 · 短句剔除"
        check("CategorySentenceExtractor:五點分類與短句剔除", _c_cat)

        def _c_fetch():
            f = b.AdjCloseFetcher()
            t1, t2 = f._to_yf_ticker("3661", "TPEX"), f._to_yf_ticker("2330.TW")
            r = f.fetch("2330")
            gated = "error" in r and (r.get("gated") is True or not b.LIBS.get("yfinance"))
            return t1 == "3661.TWO" and t2 == "2330.TW" and gated, f"{t1} · {t2} · fetch→{str(r.get('error'))[:24]}"
        check("AdjCloseFetcher:代碼轉 .TW/.TWO;VIA_SELFTEST=1 下 fetch 必不出網", _c_fetch)

        def _c_process():
            kw = dict(broker="元大", report_date="2025-01-19", target_price=1200, rating="買進", eps_current=45)
            fp, rest = "台積電 投資報告\n", f"{s_risk}。{s_grow}。"
            r = b.VRN_Summarizer(keyword_method="simple").process("TW2330", fp, rest, **kw)
            ok = (r.ticker == "2330" and r.yfinance_ticker == "2330.TW" and r.bloomberg_ticker == "2330 TT"
                  and r.broker_abbr == "YT" and r.adj_close is None and r.upside_pct is None
                  and r.topic == "台積電 投資報告" and r.headline == "2330(2330.TW): 台積電 投資報告"
                  and r.point_1_conclusion == "買進，目標價 1200 元。"
                  and r.point_2_growth == s_grow
                  and r.point_3_valuation == "預估 EPS 45 元，目標價 1200 元。"
                  and r.point_4_peers == "同業中具競爭優勢。"
                  and r.point_5_risk == s_risk
                  and r.valuation_method == "PE" and r.report_code == "YT-2330--20250119"
                  and r.to_markdown().splitlines()[0] == "**2330(2330.TW): 台積電 投資報告**"
                  and r.to_one_line_csv().startswith('"YT-2330--20250119","2025-01-19","元大"')
                  and b.summarize_report("TW2330", fp, rest, **kw).to_dict() == r.to_dict())
            return ok, f"{r.report_code} · 一標題五點比對{'全對' if ok else '有差'}"
        check("VRN_Summarizer.process() 端到端:合成報告 → 一標題五點/報告碼/Markdown/CSV", _c_process)

    n, k = len(results), sum(results)
    if n and k == n and missing:
        print(f"  [計] {STEM} {TAIL_VER} 自測 {k}/{n} · NODATA(缺件 {','.join(missing)};已跑之檢全過,不假綠)")
        return 2
    verdict = "PASS" if n and k == n else "FAIL"
    print(f"  [計] {STEM} {TAIL_VER} 自測 {k}/{n} · {verdict}")
    return 0 if verdict == "PASS" else 1


def main():
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _load_body().main()


if __name__ == "__main__":
    sys.exit(main())

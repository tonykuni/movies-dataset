#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG243_TWFin5Y v0102 — 薄尾(v0100 / v0101 一字不動):公積發放現金兩欄分開時要加總

PR #749 審查(Codex P2,讀碼屬實):v0101 parse_dividend_periods 用 next() 只取第一個對得上的公積欄。
股利表把「法定盈餘公積發放之現金」與「資本公積發放之現金」分成兩欄時,盈餘現金 1 · 法定公積現金 2 · 資本公積現金 3
被讀成 DPS 3(該是 6)→ 寫進 fin5y_div_period,再往下算年度 DPS 與配發率,全都偏低。
本版:有「法定盈餘公積、資本公積發放之現金」合併欄 → 只用它(不重複加);沒有合併欄 → 分開的公積現金欄全部加總。
其餘(期別判定 · 只收四碼代號 · 空值當沒有)照 v0101。資料不離開本機;不用 TA-Lib;不設同意閘;本檔零外呼。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

STEM = "VDF_ENG243_TWFin5Y"
VERSION = "v0102"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
COMBINED = "法定盈餘公積、資本公積發放之現金(元/股)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
norm, num, period_of = PRIOR.norm, PRIOR.num, PRIOR.period_of


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def parse_dividend_periods(html: str, items: dict) -> list:
    """股利分派彙總頁 → [(代號, 所屬年, 期別, DPS = 盈餘現金 + 公積現金, 原字樣)]。
    公積現金:有合併欄只用合併欄;沒有就把分開的公積現金欄全部加總(v0101 只取第一欄 → 偏低)。"""
    p = PRIOR.P._Tables()
    p.feed(html)
    want_e, want_r, want_p = ({norm(x) for x in items[k]} for k in ("cash_dps", "cash_dps_reserve", "dividend_period"))
    comb = norm(COMBINED)
    out = []
    for t in p.tables:
        for hi, head in enumerate(t[:6]):
            hn = [norm(h) for h in head]
            ci = next((j for j, h in enumerate(hn) if "代號" in h), None)
            ei = next((j for j, h in enumerate(hn) if h in want_e), None)
            ris = [j for j, h in enumerate(hn) if h in want_r]
            if any(hn[j] == comb for j in ris):
                ris = [j for j in ris if hn[j] == comb]
            pi = next((j for j, h in enumerate(hn) if h in want_p or ("所屬" in h and ("年" in h or "期" in h))), None)
            if ci is None or ei is None or pi is None:
                continue
            for r in t[hi + 1:]:
                if len(r) <= max(ci, ei, pi):
                    continue
                code = r[ci][:4]
                per = period_of(r[pi])
                e = num(r[ei])
                rvs = [num(r[j]) for j in ris if j < len(r)]
                rvs = [v for v in rvs if v is not None]
                if re.fullmatch(r"\d{4}", code) and per and (e is not None or rvs):
                    out.append((code, per[0], per[1], (e or 0.0) + sum(rvs), r[pi]))
            break
    return out


_ORIG = PRIOR.parse_dividend_periods


def _install():
    PRIOR.parse_dividend_periods = parse_dividend_periods
    PRIOR.TAG = TAG


def _uninstall():
    PRIOR.parse_dividend_periods = _ORIG
    PRIOR.TAG = f"{STEM} v{_vnum(PRIOR_PATH):04d}"


_install()


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main()


SPLIT = """<table><tr><th>公司代號名稱</th><th>股利所屬年(季)度</th><th>盈餘分配之現金股利(元/股)</th>
<th>法定盈餘公積發放之現金(元/股)</th><th>資本公積發放之現金(元/股)</th></tr>
<tr><td>2330 台積電</td><td>113年年度</td><td>1.00</td><td>2.00</td><td>3.00</td></tr>
<tr><td>1101 台泥</td><td>113年上半年</td><td>1.00</td><td></td><td>0.50</td></tr>
<tr><td>2317 鴻海</td><td>113年年度</td><td></td><td></td><td>0.70</td></tr></table>"""
BOTH = """<table><tr><th>公司代號名稱</th><th>股利所屬年(季)度</th><th>盈餘分配之現金股利(元/股)</th>
<th>法定盈餘公積、資本公積發放之現金(元/股)</th><th>法定盈餘公積發放之現金(元/股)</th><th>資本公積發放之現金(元/股)</th></tr>
<tr><td>2330 台積電</td><td>113年年度</td><td>1.00</td><td>5.00</td><td>2.00</td><td>3.00</td></tr></table>"""


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    items = PRIOR.DEFAULTS["fin5y.items"]
    got = {(c, fy, per): v for c, fy, per, v, _ in parse_dividend_periods(SPLIT, items)}
    old = {(c, fy, per): v for c, fy, per, v, _ in _ORIG(SPLIT, items)}
    chk("公積兩欄分開:盈餘 1 + 法定 2 + 資本 3 = 6(v0101 讀成 3,Codex P2 重現)",
        abs(got.get(("2330", 2024, "FY"), 0) - 6.0) < 1e-9 and abs(old.get(("2330", 2024, "FY"), 0) - 3.0) < 1e-9, (got, old))
    chk("空格當沒有:台泥 1 + 0.5 = 1.5 · 只有資本公積的鴻海 = 0.7(盈餘空也收)",
        abs(got.get(("1101", 2024, "H1"), 0) - 1.5) < 1e-9 and abs(got.get(("2317", 2024, "FY"), 0) - 0.7) < 1e-9, got)
    both = {(c, fy, per): v for c, fy, per, v, _ in parse_dividend_periods(BOTH, items)}
    chk("有合併欄又有分開欄 → 只用合併欄(1 + 5 = 6,不重複加成 11)", abs(both.get(("2330", 2024, "FY"), 0) - 6.0) < 1e-9, both)
    comb = {(c, fy, per): v for c, fy, per, v, _ in parse_dividend_periods(PRIOR.DIVQ, items)}
    chk("舊版合併欄版面照舊:台積電 113Q4 = 4.5 + 0.5 = 5.0", abs(comb.get(("2330", 2024, "Q4"), 0) - 5.0) < 1e-9, comb)
    chk("已裝進 v0101 模組全域(fetch 叫的是本版)· 橫幅寫本版", PRIOR.parse_dividend_periods is parse_dividend_periods and PRIOR.TAG == TAG)
    _uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0101 自測(本版換裝卸下)照過", rc == 0, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:雙橋在 · 零 TA-Lib · 不設同意閘",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

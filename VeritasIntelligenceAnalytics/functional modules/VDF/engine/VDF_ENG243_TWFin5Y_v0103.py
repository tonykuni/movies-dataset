#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG243_TWFin5Y v0103 — 薄尾(v0100–v0102 一字不動):fetch 的燈號 / rc 算進股利與季報兩段

PR #749 Codex 審查(P2,讀碼屬實):v0101 main 的 fetch 只看年報那一段的 st 決定燈號與 rc;
fetch_dividends 不計失敗、遇到 BLOCKED 也照抓下一年;fetch_quarters 遇 BLOCKED 會停但不回報。
→ 季報全失敗({'codes': 1, 'ok': 0, 'fail': 1})仍 GREEN rc 0,期別配發率需要的輸入缺了也看不出來。
本版:
  · 股利段 / 季報段各自計 fail 與 blocked;BLOCKED 一出現就停該段後面的請求。
  · 兩段的 fail / blocked 併回 main 讀的同一份 st(年報段 P.fetch 回的那個 dict):fail 加總、任一段 blocked → st["blocked"] = True。
    main 原本的判式(blocked = RED · 有 fail = YELLOW · 都沒有 = GREEN)就涵蓋三段;股利段被擋 → 季報段照 main 原規則不再跑。
  · st 另記 fail_dividend / fail_quarters / blocked_at,收據看得出是哪一段。
其餘照 v0102。資料不離開本機;本檔零外呼(擷取走前版 get_html,出網照前版的同意閘規則);不用 TA-Lib。
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
import time
from datetime import datetime, timezone
from pathlib import Path

STEM = "VDF_ENG243_TWFin5Y"
VERSION = "v0103"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V101 = PRIOR.PRIOR                                  # v0101:main · fetch_dividends · fetch_quarters 的所在
P = V101.P                                          # v0100 本體:fetch · get_html · mops_url · req_years · parse_statement
norm = V101.norm
_CUR = {}


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _fold(out: dict, phase: str) -> None:
    """把這一段的 fail / blocked 併回 main 讀的那份年報 st。"""
    st = _CUR.get("st")
    if st is None:
        return
    st["fail"] = int(st.get("fail") or 0) + int(out.get("fail") or 0)
    st[f"fail_{phase}"] = int(out.get("fail") or 0)
    if out.get("blocked"):
        st["blocked"] = True
        st.setdefault("blocked_at", phase)


def fetch(con, codes, prm, max_req=None):
    st = _ORIG_FETCH(con, codes, prm, max_req=max_req)
    _CUR["st"] = st
    return st


def fetch_dividends(con, prm: dict, getter=None, sleep=time.sleep, base=None) -> dict:
    """同 v0101,另計 fail / blocked;BLOCKED 就停。"""
    years = P.req_years(prm)
    fys = sorted({y - k for y in years for k in (0, 1)})
    qyears = sorted(set(fys) | {max(fys) + 1})
    have = {r[0] for r in con.execute("SELECT src_year FROM fin5y_log WHERE statement = 'dividend_period' AND state = 'OK'").fetchall()}
    base = base or prm["fin5y.bases"][0]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"queries": 0, "rows": 0, "revised": 0, "fail": 0, "blocked": False}
    for y in [y for y in qyears if y not in have]:
        st, body = P.get_html(P.mops_url(base, prm["fin5y.endpoints"]["dividend"], "", y - 1911, "dividend"), getter)
        got = V101.parse_dividend_periods(body, prm["fin5y.items"]) if st == "OK" else []
        for code, fy, per, dps, label in got:
            old = con.execute("SELECT cash_dps FROM fin5y_div_period WHERE code=? AND fy=? AND period=?", [code, fy, per]).fetchone()
            if old is None:
                con.execute("INSERT INTO fin5y_div_period VALUES (?,?,?,?,?,?,?)", [code, fy, per, dps, label, y, now])
                out["rows"] += 1
            elif abs((old[0] or 0) - dps) > 1e-9:
                con.execute("INSERT INTO fin5y_div_revised VALUES (?,?,?,?,?,?,?)", [code, fy, per, old[0], dps, label, now])
                out["revised"] += 1
        state = st if (st != "OK" or got) else "UNPARSED"
        con.execute("INSERT INTO fin5y_log VALUES (?,?,?,?,?,?,?)", ["*", y, "dividend_period", state, len(got), "" if got else str(body)[:200], now])
        out["queries"] += 1
        if state != "OK":
            out["fail"] += 1
        if st == "BLOCKED":
            out["blocked"] = True
            break
        sleep(float(prm["fin5y.rate_s"]))
    _fold(out, "dividend")
    return out


def fetch_quarters(con, codes: list, prm: dict, getter=None, sleep=time.sleep, base=None) -> dict:
    """同 v0101(只對季配 / 半年配的公司抓第 1–3 季),另回 blocked;結果併回年報 st。"""
    out = _ORIG_FQ(con, codes, prm, getter=getter, sleep=sleep, base=base)
    last = con.execute("SELECT state FROM fin5y_log WHERE statement LIKE 'income_q%' ORDER BY fetched_at DESC, rowid DESC LIMIT 1").fetchone() \
        if out.get("fail") else None
    out = dict(out, blocked=bool(last and last[0] == "BLOCKED"))
    _fold(out, "quarters")
    return out


_ORIG_FETCH = P.fetch
_ORIG_FD = V101.fetch_dividends
_ORIG_FQ = V101.fetch_quarters


def _install():
    P.fetch = fetch
    V101.fetch_dividends, V101.fetch_quarters = fetch_dividends, fetch_quarters
    V101.TAG = TAG


def _uninstall():
    P.fetch = _ORIG_FETCH
    V101.fetch_dividends, V101.fetch_quarters = _ORIG_FD, _ORIG_FQ
    V101.TAG = PRIOR.TAG


_install()


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    _CUR.clear()
    return PRIOR.main()


def _lamp(st: dict) -> str:
    """與 v0101 main fetch 分支同一個判式(本版不改判式,改的是 st 裡有什麼)。"""
    return "RED" if st["blocked"] else ("GREEN" if not st["fail"] else "YELLOW")


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("已裝進 v0101 / v0100(main 叫的 fetch · fetch_dividends · fetch_quarters 是本版)",
        P.fetch is fetch and V101.fetch_dividends is fetch_dividends and V101.fetch_quarters is fetch_quarters)
    duckdb = P._duck()
    con = duckdb.connect()
    for ddl in list(getattr(P, "DDL", [])) + list(getattr(V101, "DDL2", [])):
        con.execute(ddl)
    prm = dict(V101.DEFAULTS)
    prm["fin5y.rate_s"] = 0
    calls = []

    def blocked_getter(url):
        calls.append(url)
        return "BLOCKED", "429"
    _CUR.clear()
    _CUR["st"] = {"fail": 0, "blocked": False}
    keep = P.get_html
    P.get_html = lambda url, getter=None: getter(url)
    try:
        sd = fetch_dividends(con, prm, getter=blocked_getter, sleep=lambda s: None)
        chk("股利段遇 BLOCKED → 只送 1 個請求就停 · 回 blocked · fail 1", sd["blocked"] and sd["queries"] == 1 and len(calls) == 1 and sd["fail"] == 1, sd)
        st = _CUR["st"]
        chk("併回年報 st:blocked → main 的判式 = RED(原本年報 OK 就 GREEN)· blocked_at = dividend",
            _lamp(st) == "RED" and st["blocked_at"] == "dividend" and st["fail_dividend"] == 1, st)
        _CUR["st"] = {"fail": 0, "blocked": False}
        con.execute("INSERT INTO fin5y_div_period VALUES ('2330', 2024, 'Q1', 4.0, '113年第1季', 2025, 'x')")
        codes = ["2330"]
        sq = fetch_quarters(con, codes, prm, getter=lambda url: ("ERROR", "500"), sleep=lambda s: None)
        st2 = _CUR["st"]
        chk("季報段全失敗({'ok': 0, 'fail': N})→ 併回 st → main 判式 = YELLOW(Codex P2 案例,原本 GREEN rc 0)",
            sq["fail"] >= 1 and sq["ok"] == 0 and not sq["blocked"] and _lamp(st2) == "YELLOW" and st2["fail_quarters"] == sq["fail"], (sq, st2))
        _CUR["st"] = {"fail": 0, "blocked": False}
        con.execute("DELETE FROM fin5y_log")
        sq2 = fetch_quarters(con, codes, prm, getter=lambda url: ("BLOCKED", "429"), sleep=lambda s: None)
        chk("季報段遇 BLOCKED → 回 blocked · main 判式 = RED", sq2["blocked"] and _lamp(_CUR["st"]) == "RED", (sq2, _CUR["st"]))
        _CUR["st"] = {"fail": 0, "blocked": False}
        con.execute("DELETE FROM fin5y_log")
        ok_html = ("<table><tr><th>公司代號名稱</th><th>股利所屬年(季)度</th><th>盈餘分配之現金股利(元/股)</th></tr>"
                   "<tr><td>2330 台積電</td><td>113年年度</td><td>4.0</td></tr></table>")
        sd3 = fetch_dividends(con, prm, getter=lambda url: ("OK", ok_html), sleep=lambda s: None)
        chk("全部 OK → fail 0 · 不擋 · 判式照舊 GREEN", sd3["fail"] == 0 and not sd3["blocked"] and _lamp(_CUR["st"]) == "GREEN", (sd3, _CUR["st"]))
    finally:
        P.get_html = keep
        _CUR.clear()
        con.close()
    _uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0102 自測(本版換裝卸下)照過", rc == 0, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:雙橋在 · 零 TA-Lib · 不設同意閘",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

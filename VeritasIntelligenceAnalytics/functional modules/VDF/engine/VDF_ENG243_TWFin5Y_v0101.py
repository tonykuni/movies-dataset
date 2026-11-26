#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG243_TWFin5Y v0101 — 薄尾(v0100 一字不動):股利依「歸屬期間」· 配發頻率 · 配息率 = 該期 DPS ÷ 同一期稀釋每股盈餘

操作員 2026-11-25:「Diluted EPS 的標準中文是『稀釋每股盈餘』· ROE 是前兩期平均值 · DPS 看歸屬哪個時期的 diluted EPS 則為它的 payout ratio ·
注意它的配息頻率及歸屬」(參考頁 cnyes 2330 股利:表由 JavaScript 載入,靜態頁只有「年股利 · 近四季 EPS」彙總 → 逐期歸屬取 MOPS 股利分派)。
v0100 只取股利的「年」,季配公司的四期會擠成一年(錯)。本版:
  股利   MOPS 股利分派彙總逐列取「股利所屬年(季)度」→ (所屬年度, 期別 FY · H1 · H2 · Q1–Q4);DPS = 盈餘分配之現金股利 + 法定盈餘公積 / 資本公積發放之現金
         (元/股;兩欄都依參數冊 fin5y.items 找)。同一期出現不同數字 = 先到的留著、另列(只增不減)。查詢年度 = 窗內每年與次年(年配多半次年分派)。
  頻率   每家每年:有 Q = 季配 · 有 H = 半年配 · 只有 FY = 年配(混合照列)。
  季 EPS 只對「季配 / 半年配」的公司另抓損益表第 1–3 季(每份季報的第一個金額欄 = 當季,第二個 = 去年同季 → 一樣只抓 Y · Y−2 · Y−4)。
  逐期配息率(新表 fin5y_payout_period):FY 用全年稀釋 EPS;Q1–Q3 用季報當季稀釋 EPS;Q4 = 全年 − (Q1 + Q2 + Q3);
         H1 = Q1 + Q2;H2 = 全年 − H1。EPS ≤ 0 或缺 = 不算(寫原因)。
  年度   dps = 歸屬該年度各期加總;期數不齊(季配 < 4 · 半年配 < 2)= 空值 + 「只到 Qn」(不拿不完整的數去算);payout_ratio = 年度 dps ÷ 全年稀釋 EPS。
  ROE    = 歸屬母公司淨利 ÷ 前兩期(期初 + 期末)歸屬母公司權益平均(定義照 v0100,寫進表的 roe_basis 欄)。
其餘(plan · probe · 三大報表抓法 · 只增 · 安全頁停 · 原子換新 · 不補 0)照 v0100。參數新增鍵以只增方式併進 VDF 正本(params-init;既有值不改)。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(操作員 2026-11-25「網路工具也要強制加入」;從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    import os as _nb_os
    from pathlib import Path as _nb_Path
    _nb_roots = [_nb_Path(__file__).resolve(), _nb_Path.cwd().resolve()]
    if _nb_os.environ.get("VIA_REPO"):
        _nb_roots.append(_nb_Path(_nb_os.environ["VIA_REPO"]).resolve())
    for _nb_r in _nb_roots:
        for _nb_q in (_nb_r, *_nb_r.parents):
            for _nb_dir in (_nb_q / "supportive modules" / "network", _nb_q / "VeritasIntelligenceAnalytics" / "supportive modules" / "network"):
                _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py")) if _nb_dir.is_dir() else []
                if _nb_hits:
                    VIA_NET_TOOL_PATH = str(_nb_hits[-1])
                    break
            if VIA_NET_TOOL_PATH:
                break
        if VIA_NET_TOOL_PATH:
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT:載入不出網,真的連線才看閘);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

STEM = "VDF_ENG243_TWFin5Y"
VERSION = "v0101"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)
VDF, VIA, DB_PATH = P.VDF, P.VIA, P.DB_PATH
norm, num, say = P.norm, P.num, P.say
DEFAULTS = json.loads(json.dumps(P.DEFAULTS))
DEFAULTS["fin5y.items"]["cash_dps_reserve"] = ["法定盈餘公積、資本公積發放之現金(元/股)", "法定盈餘公積發放之現金(元/股)", "資本公積發放之現金(元/股)"]
DEFAULTS["fin5y.items"]["dividend_period"] = ["股利所屬年(季)度", "股利所屬期間", "股利所屬年度"]
EXPECT = {"Q": 4, "H": 2, "FY": 1}
FREQ_ZH = {"Q": "季配", "H": "半年配", "FY": "年配"}
DDL2 = [
    "CREATE TABLE IF NOT EXISTS fin5y_div_period(code VARCHAR, fy INTEGER, period VARCHAR, cash_dps DOUBLE, label VARCHAR, src_year INTEGER, fetched_at VARCHAR, PRIMARY KEY(code, fy, period))",
    "CREATE TABLE IF NOT EXISTS fin5y_div_revised(code VARCHAR, fy INTEGER, period VARCHAR, old_dps DOUBLE, new_dps DOUBLE, label VARCHAR, seen_at VARCHAR)",
    "CREATE TABLE IF NOT EXISTS fin5y_qeps(code VARCHAR, fy INTEGER, quarter INTEGER, diluted_eps DOUBLE, src_year INTEGER, fetched_at VARCHAR, PRIMARY KEY(code, fy, quarter))",
]


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(P, name)


def params(vdf: Path = VDF) -> dict:
    out, src = json.loads(json.dumps(DEFAULTS)), {k: "DEFAULT" for k in DEFAULTS}
    mt = P.newest(vdf, "VDF_ParamControl_SSOT_v*.json")
    if mt:
        for e in json.loads(mt.read_text(encoding="utf-8")).get("params", []):
            k = str(e.get("path", ""))
            if k.startswith("fin5y."):
                v = e.get("value")
                if isinstance(v, dict) and isinstance(out.get(k), dict):
                    out[k] = {**out[k], **v}                             # 正本的值優先;正本還沒有的新鍵用本版預設
                    src[k] = e.get("id") if set(out[k]) == set(v) else f"{e.get('id')}+新鍵待登"
                else:
                    out[k], src[k] = v, e.get("id")
    out["_src"], out["_master"] = src, (mt.name if mt else None)
    return out


def open_db(path: Path = DB_PATH):
    con = P.open_db(path)
    for d in DDL2:
        con.execute(d)
    return con


# ---------------------------------------------------------------- 歸屬期間
_ZH_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "1": 1, "2": 2, "3": 3, "4": 4}


def period_of(label: str):
    """股利所屬期間字樣 → (西元年, 期別)。113年第3季 · 113年第三季 · 2024Q3 · 113年上半年 · 113年下半年 · 113年年度 · 113年度 · 113年。認不出 = None。"""
    t = norm(label).upper()
    m = re.search(r"(\d{2,4})", t)
    if not m:
        return None
    y = int(m.group(1))
    y = y + 1911 if y < 1911 else y
    q = re.search(r"Q([1-4])|第([一二三四1-4])季", t)
    if q:
        return y, f"Q{_ZH_NUM[q.group(1) or q.group(2)]}"
    if "上半" in t or "H1" in t:
        return y, "H1"
    if "下半" in t or "H2" in t:
        return y, "H2"
    return y, "FY"


def parse_dividend_periods(html: str, items: dict) -> list:
    """股利分派彙總頁 → [(代號, 所屬年, 期別, DPS = 盈餘現金 + 公積現金, 原字樣)]。依表頭找欄(代號 · 所屬期間 · 兩種現金),不寫死位置。"""
    p = P._Tables()
    p.feed(html)
    want_e, want_r, want_p = ({norm(x) for x in items[k]} for k in ("cash_dps", "cash_dps_reserve", "dividend_period"))
    out = []
    for t in p.tables:
        for hi, head in enumerate(t[:6]):
            hn = [norm(h) for h in head]
            ci = next((j for j, h in enumerate(hn) if "代號" in h), None)
            ei = next((j for j, h in enumerate(hn) if h in want_e), None)
            ri = next((j for j, h in enumerate(hn) if h in want_r), None)
            pi = next((j for j, h in enumerate(hn) if h in want_p or ("所屬" in h and ("年" in h or "期" in h))), None)
            if ci is None or ei is None or pi is None:
                continue
            for r in t[hi + 1:]:
                if len(r) <= max(ci, ei, pi):
                    continue
                code = r[ci][:4]
                per = period_of(r[pi])
                e = num(r[ei])
                rv = num(r[ri]) if ri is not None and ri < len(r) else None
                if re.fullmatch(r"\d{4}", code) and per and (e is not None or rv is not None):
                    out.append((code, per[0], per[1], (e or 0.0) + (rv or 0.0), r[pi]))
            break
    return out


def quarter_url(base: str, ep: str, code: str, roc_year: int, season: int) -> str:
    q = {"encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "queryName": "co_id", "inpuType": "co_id", "TYPEK": "all",
         "isnew": "false", "co_id": code, "year": roc_year, "season": f"{season:02d}"}
    return f"{base.rstrip('/')}/{ep}?{urlencode(q)}"


def fetch_dividends(con, prm: dict, getter=None, sleep=time.sleep, base=None) -> dict:
    years = P.req_years(prm)
    fys = sorted({y - k for y in years for k in (0, 1)})
    qyears = sorted(set(fys) | {max(fys) + 1})                          # 窗內每年 + 次年(年配多半次年分派)
    have = {r[0] for r in con.execute("SELECT src_year FROM fin5y_log WHERE statement = 'dividend_period' AND state = 'OK'").fetchall()}
    base = base or prm["fin5y.bases"][0]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    st_all = {"queries": 0, "rows": 0, "revised": 0}
    for y in [y for y in qyears if y not in have]:
        st, body = P.get_html(P.mops_url(base, prm["fin5y.endpoints"]["dividend"], "", y - 1911, "dividend"), getter)
        got = parse_dividend_periods(body, prm["fin5y.items"]) if st == "OK" else []
        for code, fy, per, dps, label in got:
            old = con.execute("SELECT cash_dps FROM fin5y_div_period WHERE code=? AND fy=? AND period=?", [code, fy, per]).fetchone()
            if old is None:
                con.execute("INSERT INTO fin5y_div_period VALUES (?,?,?,?,?,?,?)", [code, fy, per, dps, label, y, now])
                st_all["rows"] += 1
            elif abs((old[0] or 0) - dps) > 1e-9:
                con.execute("INSERT INTO fin5y_div_revised VALUES (?,?,?,?,?,?,?)", [code, fy, per, old[0], dps, label, now])
                st_all["revised"] += 1
        state = st if (st != "OK" or got) else "UNPARSED"
        con.execute("INSERT INTO fin5y_log VALUES (?,?,?,?,?,?,?)", ["*", y, "dividend_period", state, len(got), "" if got else str(body)[:200], now])
        st_all["queries"] += 1
        sleep(float(prm["fin5y.rate_s"]))
    return st_all


def fetch_quarters(con, codes: list, prm: dict, getter=None, sleep=time.sleep, base=None) -> dict:
    """只對季配 / 半年配的公司抓損益表第 1–3 季 → 當季稀釋每股盈餘(第一個金額欄 = 當季,第二個 = 去年同季)。"""
    need = sorted({c for (c,) in con.execute("SELECT DISTINCT code FROM fin5y_div_period WHERE period <> 'FY'").fetchall()} & set(codes))
    done = {(c, y, s) for c, y, s in con.execute("SELECT code, src_year, statement FROM fin5y_log WHERE state = 'OK'").fetchall()}
    base = base or prm["fin5y.bases"][0]
    names = prm["fin5y.items"]["diluted_eps"]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stx = {"codes": len(need), "ok": 0, "fail": 0}
    for c in need:
        for y in P.req_years(prm):
            for s in (1, 2, 3):
                tag = f"income_q{s}"
                if (c, y, tag) in done:
                    continue
                st, body = P.get_html(quarter_url(base, prm["fin5y.endpoints"]["income"], c, y - 1911, s), getter)
                rows = P.parse_statement(body) if st == "OK" else []
                hit = next(((cur, pri) for item, cur, pri in rows if norm(item) in {norm(n) for n in names}), None)
                if st == "OK" and hit is None:
                    st, body = "UNPARSED", "季報認不出稀釋每股盈餘"
                if hit:
                    for fy, v in ((y, hit[0]), (y - 1, hit[1])):
                        if v is not None:
                            con.execute("INSERT INTO fin5y_qeps VALUES (?,?,?,?,?,?) ON CONFLICT DO NOTHING", [c, fy, s, v, y, now])
                con.execute("INSERT INTO fin5y_log VALUES (?,?,?,?,?,?,?)", [c, y, tag, st, len(rows), "" if st == "OK" else str(body)[:200], now])
                stx["ok" if st == "OK" else "fail"] += 1
                if st == "BLOCKED":
                    return stx
                sleep(float(prm["fin5y.rate_s"]))
    return stx


# ---------------------------------------------------------------- 計算
def period_eps(fy_eps, q: dict, per: str):
    """該期稀釋每股盈餘:FY = 全年;Q1–Q3 = 季報當季;Q4 = 全年 − (Q1 + Q2 + Q3);H1 = Q1 + Q2;H2 = 全年 − H1。缺 = (None, 原因)。"""
    if per == "FY":
        return (fy_eps, "") if fy_eps is not None else (None, "缺全年稀釋每股盈餘")
    q1, q2, q3 = q.get(1), q.get(2), q.get(3)
    if per in ("Q1", "Q2", "Q3"):
        v = q.get(int(per[1]))
        return (v, "") if v is not None else (None, f"缺 {per} 季報稀釋每股盈餘")
    if per == "Q4":
        return (fy_eps - q1 - q2 - q3, "") if None not in (fy_eps, q1, q2, q3) else (None, "Q4 = 全年 − 前三季:缺項")
    if per == "H1":
        return (q1 + q2, "") if None not in (q1, q2) else (None, "H1 = Q1 + Q2:缺項")
    if per == "H2":
        return (fy_eps - q1 - q2, "") if None not in (fy_eps, q1, q2) else (None, "H2 = 全年 − H1:缺項")
    return None, f"認不出期別 {per}"


def compute(con, prm: dict) -> tuple:
    base_rows = P.compute(con, prm)                                     # v0100 的七項(EPS · BVPS · 實付股利 · ROE · EBITDA/股 · 年增率)照用
    divs, qeps = {}, {}
    for c, fy, per, dps in con.execute("SELECT code, fy, period, cash_dps FROM fin5y_div_period").fetchall():
        divs.setdefault((c, fy), {})[per] = dps
    for c, fy, qn, v in con.execute("SELECT code, fy, quarter, diluted_eps FROM fin5y_qeps").fetchall():
        qeps.setdefault((c, fy), {})[qn] = v
    annual, per_rows = [], []
    for r in base_rows:
        c, fy = r["code"], r["fy"]
        d = divs.get((c, fy), {})
        kinds = {("Q" if p.startswith("Q") else "H" if p.startswith("H") else "FY") for p in d}
        freq = "/".join(FREQ_ZH[k] for k in ("Q", "H", "FY") if k in kinds) or "無配息資料"
        miss = [m for m in r["missing"].split(";") if m and not m.startswith(("dps:", "payout_ratio:"))]
        dps = None
        if len(kinds) == 1:
            k = next(iter(kinds))
            if len(d) >= EXPECT[k]:
                dps = sum(d.values())
            else:
                have = sorted(d)
                miss.append(f"dps:{FREQ_ZH[k]}只到 {have[-1]}(共 {len(d)}/{EXPECT[k]} 期)")
        elif kinds:
            miss.append(f"dps:配發頻率混合 {freq}(逐期表照列,年度不加總)")
        else:
            miss.append("dps:股利分派")
        payout = dps / r["diluted_eps"] if dps is not None and r["diluted_eps"] and r["diluted_eps"] > 0 else None
        if dps is not None and payout is None:
            miss.append("payout_ratio:全年稀釋每股盈餘 ≤ 0 或缺")
        annual.append({**r, "dps": dps, "payout_ratio": payout, "dividend_frequency": freq, "dps_periods": ",".join(sorted(d)),
                       "roe_basis": "歸屬母公司淨利 ÷ (期初 + 期末歸屬母公司權益) / 2", "missing": ";".join(miss)})
        for per, pd in sorted(d.items()):
            eps_p, why = period_eps(r["diluted_eps"], qeps.get((c, fy), {}), per)
            po = pd / eps_p if eps_p is not None and eps_p > 0 else None
            per_rows.append({"code": c, "fy": fy, "period": per, "frequency": FREQ_ZH["Q" if per.startswith("Q") else "H" if per.startswith("H") else "FY"],
                             "cash_dps": pd, "diluted_eps_period": eps_p, "payout_ratio": po,
                             "note": why or ("" if po is not None else "該期稀釋每股盈餘 ≤ 0")})
    return annual, per_rows


def save_all(con, annual: list, per_rows: list, lake: Path) -> dict:
    cols = ["code", "fy", "diluted_eps", "bvps", "dps", "dividends_paid", "payout_ratio", "roe", "ebitda_ps", "diluted_eps_growth",
            "dividend_frequency", "dps_periods", "roe_basis", "missing"]
    types = {"code": "VARCHAR", "fy": "INTEGER", "dividend_frequency": "VARCHAR", "dps_periods": "VARCHAR", "roe_basis": "VARCHAR", "missing": "VARCHAR"}
    con.execute("CREATE OR REPLACE TABLE fin5y_metrics(" + ", ".join(f"{c} {types.get(c, 'DOUBLE')}" for c in cols) + ", PRIMARY KEY(code, fy))")
    con.executemany(f"INSERT INTO fin5y_metrics VALUES ({','.join('?' * len(cols))})", [[r.get(c) for c in cols] for r in annual])
    pc = ["code", "fy", "period", "frequency", "cash_dps", "diluted_eps_period", "payout_ratio", "note"]
    con.execute("CREATE OR REPLACE TABLE fin5y_payout_period(code VARCHAR, fy INTEGER, period VARCHAR, frequency VARCHAR, cash_dps DOUBLE, "
                "diluted_eps_period DOUBLE, payout_ratio DOUBLE, note VARCHAR, PRIMARY KEY(code, fy, period))")
    con.executemany(f"INSERT INTO fin5y_payout_period VALUES ({','.join('?' * len(pc))})", [[r.get(c) for c in pc] for r in per_rows])
    out = {}
    for name, tb in (("tw_fin5y_metrics", "fin5y_metrics"), ("tw_fin5y_payout_period", "fin5y_payout_period")):
        dest = lake / "_metrics" / f"{name}.parquet"
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + f".{os.getpid()}.sdd_tmp")
        con.execute(f"COPY (SELECT * FROM {tb} ORDER BY ALL) TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        os.replace(tmp, dest)                                           # 整份原子換新 = 不重複輸出
        out[name] = str(dest)
    dup = con.execute("SELECT (SELECT count(*) - count(DISTINCT (code, fy)) FROM fin5y_metrics) + "
                      "(SELECT count(*) - count(DISTINCT (code, fy, period)) FROM fin5y_payout_period)").fetchone()[0]
    full = sum(1 for r in annual if not r["missing"])
    return {"rows": len(annual), "period_rows": len(per_rows), "dup": dup, "complete_rows": full, "parquet": out}


# ---------------------------------------------------------------- 主
def main() -> int:
    a = sys.argv[1:]
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    verb = a[0] if a else "plan"
    if verb in ("plan", "probe"):
        return P.main()
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d  # noqa: E731
    prm = params()
    say(f"{TAG} {verb} · 正本 {prm['_master']} · 年度 {P.req_years(prm)} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在'}")
    pend = [k for k, v in prm["_src"].items() if v == "DEFAULT" or "新鍵待登" in str(v)]
    if pend and verb != "params-init":
        say(f"[YELLOW] {len(pend)} 個參數(或新鍵)還沒登進 VDF 正本:先 params-init --apply")
    if verb == "params-init":
        e53p = P.newest(HERE, "VDF_ENG053_ParamEngineMap_v*.py")
        sp = importlib.util.spec_from_file_location(f"{STEM}_e53_{VERSION}", e53p)
        e53 = importlib.util.module_from_spec(sp)
        sys.modules[sp.name] = e53
        sp.loader.exec_module(e53)
        mt, ut = e53.tail_of(VDF, e53.MASTER), e53.tail_of(VDF, e53.UNIFIED)
        m = json.loads(mt.read_text(encoding="utf-8"))
        by = {e["path"]: e for e in m["params"]}
        at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        changes = []
        for k, v in DEFAULTS.items():
            e = by.get(k)
            if e is None:
                changes.append((k, "ADD", v))
            elif isinstance(v, dict) and isinstance(e.get("value"), dict):
                newk = {kk: vv for kk, vv in v.items() if kk not in e["value"]}   # 只增:補新鍵,既有鍵的值不改
                if newk:
                    changes.append((k, "MERGE_KEYS", newk))
        res = {"rows": [{"path": k, "state": s, "keys": list(v) if isinstance(v, dict) else None} for k, s, v in changes],
               "lamp": "GREEN" if not changes else "YELLOW", "counts": {"changes": len(changes)}}
        if changes and "--apply" in a:
            nums = [int(x["id"].rsplit("-", 1)[1]) for x in m["params"] if re.fullmatch(r"VDF-PAR-\d+", str(x.get("id")))]
            n = max(nums or [0])
            for k, s, v in changes:
                if s == "ADD":
                    n += 1
                    m["params"].append({"name": f"五年財報 · {k.split('.', 1)[1]}", "book": ut.name, "path": k, "value": v, "class": "規則", "mutable": True,
                                        "why": f"{TAG} params-init", "id": f"VDF-PAR-{n:03d}", "version": "v0100", "registered_at": at, "derive_pending": at})
                else:
                    e = by[k]
                    e.setdefault("history", []).append({"at": at, "added_keys": sorted(v), "reason": f"{TAG}:股利歸屬期間 · 公積現金(只增,既有鍵不改)"})
                    e["value"] = {**e["value"], **v}
                    e["updated_at"], e["derive_pending"] = at, at
            res["written"] = e53.write_next(mt, m, f"{TAG} params-init:{', '.join(f'{k}({s})' for k, s, _ in changes)}").name
            d = subprocess.run([sys.executable, str(e53p), "derive", "--apply"], cwd=str(HERE), capture_output=True, text=True)
            res["derive_rc"] = d.returncode
            res["lamp"] = "GREEN" if d.returncode in (0, 2) else "RED"
    elif verb == "fetch":
        if "--live" not in a:
            res = {"rows": [], "lamp": "YELLOW", "note": "fetch 會出網:加 --live", "counts": {}}
        else:
            os.environ.setdefault("VIA_NET_CONSENT", "YES")
            os.environ.setdefault("VIA_SCRAPE_CONSENT", "YES")
            only = [x for x in re.split(r"[,\s]+", opt("--only", "") or "") if x] or None
            mdb = P.market_db()
            mc = P._duck().connect(str(mdb), read_only=True) if mdb else None
            codes = P.universe(mc, prm, only)
            if mc:
                mc.close()
            con = open_db()
            st = P.fetch(con, codes, prm, max_req=int(opt("--max")) if opt("--max") else None)
            sd = fetch_dividends(con, prm) if not st["blocked"] else {}
            sq = fetch_quarters(con, codes, prm) if not st["blocked"] else {}
            con.close()
            res = {"rows": [], "counts": {**st, "dividend": sd, "quarters": sq}, "lamp": "RED" if st["blocked"] else ("GREEN" if not st["fail"] else "YELLOW")}
    elif verb == "compute":
        if not DB_PATH.is_file():
            res = {"rows": [], "lamp": "YELLOW", "note": f"庫不在:{DB_PATH}(先 fetch --live)", "counts": {}}
        else:
            con = open_db()
            annual, per_rows = compute(con, prm)
            info = save_all(con, annual, per_rows, VIA / "VIA_Reports" / "vdf_lake")
            con.close()
            res = {"rows": annual, "counts": info, "lamp": "RED" if info["dup"] else ("GREEN" if annual and info["complete_rows"] == info["rows"] else "YELLOW")}
    else:
        say(f"[RED] 未知動詞 {verb}")
        return 1
    od = P.save(verb, res)
    say(f"{verb} · {res['lamp']} · " + " · ".join(f"{k} {v}" for k, v in (res.get("counts") or {}).items()) + (f" · 寫 {res['written']}" if res.get("written") else "")
        + (f" · {res['note']}" if res.get("note") else ""))
    say(f"DataFrame → {od}")
    return {"GREEN": 0, "YELLOW": 2}.get(res["lamp"], 1)


# ---------------------------------------------------------------- 自測(零網路假頁)
DIVQ = """<table><tr><th>公司代號名稱</th><th>股利所屬年(季)度</th><th>盈餘分配之現金股利(元/股)</th><th>法定盈餘公積、資本公積發放之現金(元/股)</th></tr>
<tr><td>2330 台積電</td><td>113年第1季</td><td>4.00</td><td>0</td></tr><tr><td>2330 台積電</td><td>113年第2季</td><td>4.50</td><td>0</td></tr>
<tr><td>2330 台積電</td><td>113年第3季</td><td>5.00</td><td>0</td></tr><tr><td>2330 台積電</td><td>113年第4季</td><td>4.50</td><td>0.5</td></tr>
<tr><td>2317 鴻海</td><td>113年年度</td><td>5.20</td><td></td></tr><tr><td>1101 台泥</td><td>113年上半年</td><td>1.00</td><td>0</td></tr></table>"""
QINC = {1: ("10.00", "8.00"), 2: ("11.00", "9.00"), 3: ("12.00", "10.00")}


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, str(VIA_NET_TOOL_PATH))
    chk("前版經 glob 載入(v0100)", PRIOR_PATH.name == STEM + "_v0100.py")
    chk("歸屬期間:季 · 中文季 · 西元季 · 上下半年 · 年度", [period_of(x) for x in ("113年第3季", "113年第三季", "2024Q4", "113年上半年", "113年下半年", "113年年度", "113年度")]
        == [(2024, "Q3"), (2024, "Q3"), (2024, "Q4"), (2024, "H1"), (2024, "H2"), (2024, "FY"), (2024, "FY")])
    got = parse_dividend_periods(DIVQ, DEFAULTS["fin5y.items"])
    chk("股利逐期:代號 · 歸屬期 · 盈餘現金 + 公積現金", ("2330", 2024, "Q4", 5.0, "113年第4季") in got and ("2317", 2024, "FY", 5.2, "113年年度") in got and len(got) == 6, str(got[:3]))
    with tempfile.TemporaryDirectory() as td:
        con = open_db(Path(td) / "f.duckdb")
        y = P.latest_fy()

        def getter(url):
            if "t05st09" in url:
                return "OK", DIVQ.replace("113年", f"{y - 1911}年")
            s = int(re.search(r"season=(\d+)", url).group(1))
            ep = re.search(r"/(ajax_\w+)\?", url).group(1)
            if ep == "ajax_t164sb04" and s in QINC:
                cur, pri = QINC[s]
                return "OK", f"<table><tr><th>會計項目</th><th>當季</th><th>%</th><th>去年同季</th><th>%</th></tr><tr><td>稀釋每股盈餘</td><td>{cur}</td><td></td><td>{pri}</td><td></td></tr></table>"
            pages = {"ajax_t164sb04": P.INC.replace("8.95", "45.00"), "ajax_t164sb03": P.BAL, "ajax_t164sb05": P.CF}
            return "OK", pages[ep]
        prm = json.loads(json.dumps(DEFAULTS))
        prm["fin5y.years"] = 1
        noop = lambda s: None  # noqa: E731
        st = P.fetch(con, ["2330", "2317", "1101"], prm, getter=getter, sleep=noop)
        sd = fetch_dividends(con, prm, getter=getter, sleep=noop)
        sq = fetch_quarters(con, ["2330", "2317", "1101"], prm, getter=getter, sleep=noop)
        chk("季配 / 半年配才抓季報(2330 · 1101;年配 2317 不抓)", sq["codes"] == 2 and sq["ok"] == 6, str(sq))
        sd2 = fetch_dividends(con, prm, getter=getter, sleep=noop)
        chk("股利已抓過的年度不重抓 · 同期同值不重複", sd2["queries"] == 0 and con.execute("SELECT count(*) FROM fin5y_div_period").fetchone()[0] == 6, str((sd, sd2)))
        prm["fin5y.years"] = 1
        annual, per = compute(con, prm)
        a = {(r["code"], r["fy"]): r for r in annual}
        t = a[("2330", y)]
        chk("季配:年度 DPS = 四季加總 · 頻率 = 季配 · 年度配息率 = DPS ÷ 全年稀釋每股盈餘",
            t["dps"] == 18.5 and t["dividend_frequency"] == "季配" and abs(t["payout_ratio"] - 18.5 / 45.0) < 1e-9, str({k: t[k] for k in ("dps", "dividend_frequency", "payout_ratio", "missing")}))
        pp = {(r["code"], r["period"]): r for r in per if r["fy"] == y}
        chk("逐期配息率:Q1–Q3 用當季 · Q4 = 全年 − 前三季", abs(pp[("2330", "Q1")]["payout_ratio"] - 4.0 / 10.0) < 1e-9
            and abs(pp[("2330", "Q4")]["diluted_eps_period"] - (45.0 - 33.0)) < 1e-9 and abs(pp[("2330", "Q4")]["payout_ratio"] - 5.0 / 12.0) < 1e-9)
        t2 = a[("2317", y)]
        chk("年配:DPS = 年度那一筆 · 配息率用全年", t2["dps"] == 5.2 and t2["dividend_frequency"] == "年配" and pp[("2317", "FY")]["diluted_eps_period"] == 45.0)
        t3 = a[("1101", y)]
        chk("半年配只到 H1:年度 DPS 空值 + 寫「只到 H1」· 逐期 H1 = Q1 + Q2", t3["dps"] is None and "只到 H1" in t3["missing"]
            and abs(pp[("1101", "H1")]["diluted_eps_period"] - 21.0) < 1e-9)
        chk("ROE 定義寫進表(前兩期平均權益)", "期初 + 期末" in t["roe_basis"])
        info = save_all(con, annual, per, Path(td) / "lake")
        info2 = save_all(con, annual, per, Path(td) / "lake")
        chk("輸出:年度表 + 逐期表 · DuckDB + Parquet 原子換新 · 零重複", info["dup"] == 0 and info2["period_rows"] == info["period_rows"] == len(per)
            and len(list((Path(td) / "lake" / "_metrics").glob("*.parquet"))) == 2)
        con.execute("UPDATE fin5y_log SET state='X' WHERE statement='dividend_period'")
        bad_html = DIVQ.replace("4.50</td><td>0.5", "4.80</td><td>0.5").replace("113年", f"{y - 1911}年")
        sd3 = fetch_dividends(con, prm, getter=lambda u: ("OK", bad_html) if "t05st09" in u else getter(u), sleep=noop)
        chk("同期不同值 = 更正:留舊值 · 另列", sd3["revised"] >= 1 and con.execute("SELECT cash_dps FROM fin5y_div_period WHERE code='2330' AND period='Q4' AND fy=?", [y]).fetchone()[0] == 5.0)
        con.close()
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

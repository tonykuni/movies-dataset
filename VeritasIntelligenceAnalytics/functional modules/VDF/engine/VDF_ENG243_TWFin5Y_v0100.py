#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG243_TWFin5Y v0100 — 全部台股 × 近 5 年度財報(MOPS 歷年)→ 8 個指標(稀釋 EPS · BVPS · DPS · 發放現金股利 · 配息率 · ROE · EBITDA/股 · 稀釋 EPS 年增率)

操作員 2026-11-25:「用全部台股清單的代碼去擷取能算出最近 5 年度數值所需的財報資料:diluted eps / bvps / dps / dividend paid /
payout ratio / roe / ebitda per share / diluted eps growth」。逐題定案:來源 = MOPS 歷年財報 · 範圍 = 全部上市上櫃普通股(四碼首位非 0)·
實抓只在桌機 · 指標定義照預設(growth = 稀釋 EPS 年增率)。範圍改的是 VDF 正本參數(fin5y.*),不改既有擷取引擎(ENG082 照舊)。
動詞:
  plan                名單(MDL009 寫進庫的 tw_listings,四碼首位非 0)× 年度 → 要抓的請求數;先看庫:已 OK 的不重抓(斷點續跑)
  probe [--live]      兩個 MOPS 網址前綴 × 損益 / 資產負債 / 現金流量 / 股利各打一次(2330 最近年度)→ 哪個前綴能用 · 表頭長什麼樣
  fetch --live [--only 2330,2317] [--max N]
                      每家抓年度 Y · Y−2 · Y−4 的三大報表(每份年報同時有本期 / 前期 → 6 年,第 6 年給年增率與 ROE 平均權益)
                      + 股利分派(依年度);網路一律經 VDF 網路橋(via_net_unified → AegisNexus;同意閘只在子行程,已裁定 1);
                      請求間隔 fin5y.rate_s;交易所安全頁 = BLOCKED 停下;寫入只增(同鍵不同值 = 交易所更正,留舊值、另列)
  compute             由原始科目算 8 個指標 → DuckDB 表 fin5y_metrics(整表換新)+ <湖>/_metrics/tw_fin5y_metrics.parquet(原子換新;不重複)
                      缺輸入 = 空值 + missing 欄寫缺什麼(不補 0 · FAIL_CLOSED)
  params-init [--apply] 把 fin5y.* 參數登進 VDF 正本(經 ENG053 出新版號再 derive 寫回統一參數冊)
定義(參數冊 fin5y.items 管科目名;比對前 NFKC 半形 · 去空白):
  diluted_eps = 稀釋每股盈餘 · bvps = 歸屬母公司權益 ÷ (普通股股本 ÷ 面額) · dps = 該年度盈餘所配現金股利(元/股,依所屬年度)
  dividends_paid = 現金流量表發放現金股利(當年實付,取絕對值)· payout = dps ÷ diluted_eps(EPS ≤ 0 不算)
  roe = 歸屬母公司淨利 ÷ 平均歸屬母公司權益(期初 + 期末)/ 2 · ebitda_ps = (營業利益 + 折舊 + 攤銷) ÷ 加權平均股數(= 歸屬母公司淨利 ÷ 基本 EPS)
  diluted_eps_growth = 本年 ÷ 前一年 − 1(前一年 ≤ 0 不算)。金額單位:MOPS 仟元 → ×fin5y.amount_scale 成元;每股類不換。
輸出:<VDF>/output_hub/fin5y/vdf_tw_fin5y.duckdb(fin5y_raw · fin5y_div · fin5y_log · fin5y_revised · fin5y_metrics;ENG239 會把它收進湖)
      + VIA_Reports/vdf_fin5y/<UTC>/ 的 DataFrame + SUMMARY.json;運作帳只增。不用 TA-Lib · 不 import 他系統。
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
import unicodedata
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

STEM = "VDF_ENG243_TWFin5Y"
VERSION = "v0100"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
_T0 = time.time()
DB_PATH = VDF / "output_hub" / "fin5y" / "vdf_tw_fin5y.duckdb"
DEFAULTS = {
    "fin5y.years": 5,
    "fin5y.universe_regex": r"^[1-9]\d{3}$",
    "fin5y.rate_s": 3.0,
    "fin5y.amount_scale": 1000,
    "fin5y.face_value": 10,
    "fin5y.face_value_overrides": {},
    "fin5y.bases": ["https://mopsov.twse.com.tw/mops/web", "https://mops.twse.com.tw/mops/web"],
    "fin5y.endpoints": {"income": "ajax_t164sb04", "balance": "ajax_t164sb03", "cashflow": "ajax_t164sb05", "dividend": "ajax_t05st09_2"},
    "fin5y.items": {
        "diluted_eps": ["稀釋每股盈餘", "稀釋每股盈餘(元)", "稀釋每股盈餘合計"],
        "basic_eps": ["基本每股盈餘", "基本每股盈餘(元)", "基本每股盈餘合計"],
        "ni_parent": ["本期淨利(淨損)歸屬於母公司業主", "母公司業主(淨利/損)", "淨利(淨損)歸屬於母公司業主", "歸屬於母公司業主之本期淨利(淨損)"],
        "equity_parent": ["歸屬於母公司業主之權益合計", "歸屬於母公司業主之權益"],
        "share_capital": ["普通股股本", "普通股"],
        "operating_income": ["營業利益(損失)", "營業利益", "營業淨利(淨損)"],
        "depreciation": ["折舊費用", "折舊費用合計"],
        "amortization": ["攤銷費用", "攤銷費用合計"],
        "dividends_paid": ["發放現金股利", "發放現金股利合計"],
        "cash_dps": ["盈餘分配之現金股利(元/股)", "現金股利", "股東配發-盈餘分配之現金股利(元/股)", "盈餘分配之股東現金股利(元/股)"],
    },
}
STATEMENTS = ("income", "balance", "cashflow")


def say(msg: str) -> None:
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


def newest(d: Path, pat: str):
    c = [p for p in d.glob(pat) if _vnum(p) >= 0] if d.is_dir() else []
    return max(c, key=_vnum) if c else None


def norm(s) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(s or "")))


def params(vdf: Path = VDF) -> dict:
    out, src = json.loads(json.dumps(DEFAULTS)), {k: "DEFAULT" for k in DEFAULTS}
    mt = newest(vdf, "VDF_ParamControl_SSOT_v*.json")
    if mt:
        for e in json.loads(mt.read_text(encoding="utf-8")).get("params", []):
            if str(e.get("path", "")).startswith("fin5y."):
                out[e["path"]], src[e["path"]] = e.get("value"), e.get("id")
    out["_src"], out["_master"] = src, (mt.name if mt else None)
    return out


def latest_fy(today: date | None = None) -> int:
    """法定年報期限 3/31:今天過了 3/31 → 去年度齊;否則前年度。"""
    t = today or date.today()
    return t.year - 1 if (t.month, t.day) > (3, 31) else t.year - 2


def req_years(prm: dict, today: date | None = None) -> list:
    y = latest_fy(today)
    n = int(prm["fin5y.years"])
    return [y - k for k in range(0, n + 1, 2)][: (n + 2) // 2]        # 5 年 → Y · Y−2 · Y−4(每份同時有本期 / 前期 → 6 年)


# ---------------------------------------------------------------- HTML 解析
class _Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self._row, self._cell, self._in = [], None, None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tables.append([])
            self._in += 1
        elif tag == "tr" and self._in:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(norm("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row and self.tables:
                self.tables[-1].append(self._row)
            self._row = None
        elif tag == "table":
            self._in = max(0, self._in - 1)

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def num(s):
    t = norm(s).replace(",", "")
    if t in ("", "-", "--", "—", "N/A"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def parse_statement(html: str) -> list:
    """MOPS 單一公司報表頁 → [(科目, 本期值, 前期值)]。依表頭找「會計項目」那張表;表頭含 % 的欄跳過(不寫死欄位位置)。"""
    p = _Tables()
    p.feed(html)
    out = []
    for t in p.tables:
        hi = next((i for i, r in enumerate(t) if r and "會計項目" in r[0]), None)
        if hi is None:
            continue
        head = t[hi]
        keep = [j for j in range(1, len(head)) if "%" not in head[j]]
        for r in t[hi + 1:]:
            if not r or not r[0] or len(r) < 2:
                continue
            vals = [num(r[j]) if j < len(r) else None for j in keep]
            if any(v is not None for v in vals):
                out.append((r[0], vals[0] if vals else None, vals[1] if len(vals) > 1 else None))
    return out


def parse_dividend(html: str, items: list) -> list:
    """股利彙總頁 → [(公司代號, 所屬年度(西元), 現金股利元/股)]。依表頭找代號欄 · 所屬年度欄 · 現金股利欄(科目名照參數冊)。"""
    p = _Tables()
    p.feed(html)
    want = {norm(x) for x in items}
    out = []
    for t in p.tables:
        for hi, head in enumerate(t[:5]):
            ci = next((j for j, h in enumerate(head) if "代號" in h), None)
            di = next((j for j, h in enumerate(head) if norm(h) in want), None)
            yi = next((j for j, h in enumerate(head) if "所屬" in h and "年" in h), None)
            if ci is None or di is None:
                continue
            for r in t[hi + 1:]:
                if len(r) <= max(ci, di):
                    continue
                code = r[ci][:4]
                fy = None
                if yi is not None and yi < len(r):
                    m = re.search(r"(\d{2,4})", r[yi])
                    if m:
                        y = int(m.group(1))
                        fy = y + 1911 if y < 1911 else y
                v = num(r[di])
                if re.fullmatch(r"\d{4}", code) and v is not None:
                    out.append((code, fy, v))
            break
    return out


# ---------------------------------------------------------------- 網路(經 VDF 網路橋)
def mops_url(base: str, ep: str, code: str, roc_year: int, kind: str) -> str:
    if kind == "dividend":
        q = {"encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "TYPEK": "all", "year": roc_year}
    else:
        q = {"encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1, "queryName": "co_id", "inpuType": "co_id",
             "TYPEK": "all", "isnew": "false", "co_id": code, "year": roc_year, "season": "04"}
    return f"{base.rstrip('/')}/{ep}?{urlencode(q)}"


def get_html(url: str, getter=None) -> tuple:
    if getter is not None:
        return getter(url)
    n = _via_net()
    if n is None or not hasattr(n, "http_text"):
        return "ABSENT", "網路工具不在"
    r = n.http_text(url, timeout=60)
    st = str(r.get("state") or "")
    if st == "DENY":
        return "DENY", str(r.get("note") or "閘未開")
    if st != "OK":
        return "FAIL", str(r.get("note") or r.get("why") or st)[:120]
    body = r.get("data")
    txt = body.decode("utf-8", "replace") if isinstance(body, (bytes, bytearray)) else str(body or "")
    if "SECURITY" in txt[:3000].upper() or "安全性" in txt[:3000] or "查詢過於頻繁" in txt:
        return "BLOCKED", "交易所安全頁 / 查詢過於頻繁(停下,換時段或調大 fin5y.rate_s)"
    return "OK", txt


# ---------------------------------------------------------------- 庫
def _duck():
    import duckdb
    return duckdb


DDL = [
    "CREATE TABLE IF NOT EXISTS fin5y_raw(code VARCHAR, fy INTEGER, statement VARCHAR, item VARCHAR, item_norm VARCHAR, value DOUBLE, src_year INTEGER, col VARCHAR, fetched_at VARCHAR, PRIMARY KEY(code, fy, statement, item_norm))",
    "CREATE TABLE IF NOT EXISTS fin5y_div(code VARCHAR, fy INTEGER, cash_dps DOUBLE, src_year INTEGER, fetched_at VARCHAR, PRIMARY KEY(code, fy))",
    "CREATE TABLE IF NOT EXISTS fin5y_log(code VARCHAR, src_year INTEGER, statement VARCHAR, state VARCHAR, n_items INTEGER, note VARCHAR, fetched_at VARCHAR)",
    "CREATE TABLE IF NOT EXISTS fin5y_revised(code VARCHAR, fy INTEGER, statement VARCHAR, item_norm VARCHAR, old_value DOUBLE, new_value DOUBLE, seen_at VARCHAR)",
]


def open_db(path: Path = DB_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    con = _duck().connect(str(path))
    for d in DDL:
        con.execute(d)
    return con


def done_set(con) -> set:
    return {(c, y, s) for c, y, s in con.execute("SELECT code, src_year, statement FROM fin5y_log WHERE state = 'OK'").fetchall()}


def write_items(con, code: str, src_year: int, statement: str, rows: list, now: str) -> tuple:
    new = rev = 0
    for item, cur, prior in rows:
        for fy, col, v in ((src_year, "current", cur), (src_year - 1, "prior", prior)):
            if v is None:
                continue
            k = norm(item)
            old = con.execute("SELECT value FROM fin5y_raw WHERE code=? AND fy=? AND statement=? AND item_norm=?", [code, fy, statement, k]).fetchone()
            if old is None:
                con.execute("INSERT INTO fin5y_raw VALUES (?,?,?,?,?,?,?,?,?)", [code, fy, statement, item, k, v, src_year, col, now])
                new += 1
            elif abs((old[0] or 0) - v) > 1e-9:
                con.execute("INSERT INTO fin5y_revised VALUES (?,?,?,?,?,?,?)", [code, fy, statement, k, old[0], v, now])  # 只增:留舊值
                rev += 1
    return new, rev


def universe(con_market, prm: dict, only=None) -> list:
    rx = re.compile(prm["fin5y.universe_regex"])
    if only:
        return [c for c in only if rx.match(c)]
    try:
        codes = [str(r[0]) for r in con_market.execute("SELECT DISTINCT code FROM tw_listings WHERE code IS NOT NULL ORDER BY code").fetchall()]
    except Exception:  # noqa: BLE001 - 名單表不在 = 空(照實)
        return []
    return [c for c in codes if rx.match(c)]


def market_db():
    for p in (os.environ.get("VIA_DB_VDF_TW_MARKET"),):
        if p and Path(p).is_file():
            return Path(p)
    hits = sorted((VDF / "output_hub").rglob("vdf_tw_market.duckdb")) + sorted((VIA / "VIA_Reports" / "vdf_fetch").rglob("vdf_tw_market.duckdb"))
    return hits[0] if hits else None


# ---------------------------------------------------------------- 主要流程
def fetch(con, codes: list, prm: dict, getter=None, max_req: int | None = None, sleep=time.sleep) -> dict:
    eps = prm["fin5y.endpoints"]
    bases = list(prm["fin5y.bases"])
    years = req_years(prm)
    done = done_set(con)
    todo = [(c, y, s) for c in codes for y in years for s in STATEMENTS if (c, y, s) not in done]
    stats = {"todo": len(todo), "ok": 0, "fail": 0, "blocked": 0, "new_items": 0, "revised": 0, "skipped_done": len(codes) * len(years) * 3 - len(todo)}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    base = bases[0]
    for i, (c, y, s) in enumerate(todo):
        if max_req is not None and i >= max_req:
            break
        st, body = get_html(mops_url(base, eps[s], c, y - 1911, s), getter)
        if st != "OK" and len(bases) > 1:
            for b in bases[1:]:
                st2, body2 = get_html(mops_url(b, eps[s], c, y - 1911, s), getter)
                if st2 == "OK":
                    base, st, body = b, st2, body2
                    break
        rows = parse_statement(body) if st == "OK" else []
        if st == "OK" and not rows:
            st, body = "UNPARSED", "回應有內容但認不出會計項目表(表頭變了?)"
        n, r = write_items(con, c, y, s, rows, now) if rows else (0, 0)
        con.execute("INSERT INTO fin5y_log VALUES (?,?,?,?,?,?,?)", [c, y, s, st, len(rows), "" if st == "OK" else str(body)[:200], now])
        stats["new_items"] += n
        stats["revised"] += r
        stats["ok" if st == "OK" else ("blocked" if st in ("BLOCKED", "DENY") else "fail")] += 1
        if st == "BLOCKED":
            say(f"[停] {c} {y} {s}:{body}")
            break
        if (i + 1) % 50 == 0:
            say(f"  進度 {i + 1}/{len(todo)} · OK {stats['ok']} · 失敗 {stats['fail']}")
        sleep(float(prm["fin5y.rate_s"]))
    div_years = sorted({y - k for y in years for k in (0, 1)})
    have_div = {r[0] for r in con.execute("SELECT DISTINCT src_year FROM fin5y_div").fetchall()}
    for y in [y for y in div_years if y not in have_div]:
        st, body = get_html(mops_url(base, eps["dividend"], "", y - 1911 + 1, "dividend"), getter)   # 股利多半次年分派:查 y+1 的分派彙總
        got = parse_dividend(body, prm["fin5y.items"]["cash_dps"]) if st == "OK" else []
        for code, fy, v in got:
            con.execute("INSERT INTO fin5y_div VALUES (?,?,?,?,?) ON CONFLICT DO NOTHING", [code, fy or y, v, y, now])
        con.execute("INSERT INTO fin5y_log VALUES (?,?,?,?,?,?,?)", ["*", y, "dividend", st if (st != "OK" or got) else "UNPARSED", len(got), "" if got else str(body)[:200], now])
        sleep(float(prm["fin5y.rate_s"]))
    return stats


def pick(rows: dict, names: list):
    for n in names:
        v = rows.get(norm(n))
        if v is not None:
            return v
    return None


def compute(con, prm: dict, codes=None) -> list:
    it = prm["fin5y.items"]
    scale = float(prm["fin5y.amount_scale"])
    raw = {}
    for code, fy, stt, k, v in con.execute("SELECT code, fy, statement, item_norm, value FROM fin5y_raw").fetchall():
        raw.setdefault((code, fy), {})[k] = v
    divs = {(c, y): v for c, y, v in con.execute("SELECT code, fy, cash_dps FROM fin5y_div").fetchall()}
    years = sorted({fy for _, fy in raw})
    last5 = years[-int(prm["fin5y.years"]):] if years else []
    out = []
    for code in sorted({c for c, _ in raw} if codes is None else codes):
        for fy in last5:
            r, rp = raw.get((code, fy), {}), raw.get((code, fy - 1), {})
            g = {k: pick(r, v) for k, v in it.items() if k != "cash_dps"}
            gp = {k: pick(rp, it[k]) for k in ("diluted_eps", "equity_parent")}
            miss = []
            fv = float((prm["fin5y.face_value_overrides"] or {}).get(code, prm["fin5y.face_value"]))
            shares = g["share_capital"] * scale / fv if g["share_capital"] else None
            bvps = g["equity_parent"] * scale / shares if g["equity_parent"] is not None and shares else None
            roe = (g["ni_parent"] / ((g["equity_parent"] + gp["equity_parent"]) / 2)
                   if None not in (g["ni_parent"], g["equity_parent"], gp["equity_parent"]) and (g["equity_parent"] + gp["equity_parent"]) else None)
            wavg = g["ni_parent"] * scale / g["basic_eps"] if g["ni_parent"] is not None and g["basic_eps"] else None
            ebitda = (g["operating_income"] + g["depreciation"] + g["amortization"]) if None not in (g["operating_income"], g["depreciation"], g["amortization"]) else None
            ebitda_ps = ebitda * scale / wavg if ebitda is not None and wavg else None
            dps = divs.get((code, fy))
            payout = dps / g["diluted_eps"] if dps is not None and g["diluted_eps"] and g["diluted_eps"] > 0 else None
            growth = g["diluted_eps"] / gp["diluted_eps"] - 1 if g["diluted_eps"] is not None and gp["diluted_eps"] and gp["diluted_eps"] > 0 else None
            paid = abs(g["dividends_paid"]) * scale if g["dividends_paid"] is not None else None
            for name, val, why in (("diluted_eps", g["diluted_eps"], "稀釋每股盈餘"), ("bvps", bvps, "權益或股本"), ("dps", dps, "股利分派"),
                                   ("dividends_paid", paid, "發放現金股利"), ("payout_ratio", payout, "DPS 或 EPS≤0"), ("roe", roe, "淨利或期初 / 期末權益"),
                                   ("ebitda_ps", ebitda_ps, "營業利益 / 折舊 / 攤銷 / 加權股數"), ("diluted_eps_growth", growth, "前一年 EPS 或 ≤0")):
                if val is None:
                    miss.append(f"{name}:{why}")
            out.append({"code": code, "fy": fy, "diluted_eps": g["diluted_eps"], "bvps": bvps, "dps": dps, "dividends_paid": paid,
                         "payout_ratio": payout, "roe": roe, "ebitda_ps": ebitda_ps, "diluted_eps_growth": growth, "missing": ";".join(miss)})
    return out


def save_metrics(con, rows: list, lake: Path) -> dict:
    con.execute("CREATE OR REPLACE TABLE fin5y_metrics(code VARCHAR, fy INTEGER, diluted_eps DOUBLE, bvps DOUBLE, dps DOUBLE, dividends_paid DOUBLE, payout_ratio DOUBLE, roe DOUBLE, ebitda_ps DOUBLE, diluted_eps_growth DOUBLE, missing VARCHAR, PRIMARY KEY(code, fy))")
    cols = ["code", "fy", "diluted_eps", "bvps", "dps", "dividends_paid", "payout_ratio", "roe", "ebitda_ps", "diluted_eps_growth", "missing"]
    con.executemany(f"INSERT INTO fin5y_metrics VALUES ({','.join('?' * len(cols))})", [[r[c] for c in cols] for r in rows])
    out = lake / "_metrics" / "tw_fin5y_metrics.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + f".{os.getpid()}.sdd_tmp")
    con.execute(f"COPY (SELECT * FROM fin5y_metrics ORDER BY code, fy) TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    os.replace(tmp, out)                                                # 整份原子換新 = 不重複輸出
    dup = con.execute("SELECT count(*) - count(DISTINCT (code, fy)) FROM fin5y_metrics").fetchone()[0]
    full = con.execute("SELECT count(*) FILTER (WHERE missing = '') FROM fin5y_metrics").fetchone()[0]
    return {"rows": len(rows), "dup": dup, "complete_rows": full, "parquet": str(out)}


# ---------------------------------------------------------------- DataFrame · 收據
def frame(rows: list):
    cols = sorted({k for r in rows for k in r}) or ["state"]
    try:
        import polars as pl
        return pl.DataFrame([{c: r.get(c) for c in cols} for r in rows], infer_schema_length=None) if rows else pl.DataFrame(schema={c: pl.Utf8 for c in cols})
    except ImportError:
        try:
            import pandas as pd
            return pd.DataFrame([{c: r.get(c) for c in cols} for r in rows], columns=cols)
        except ImportError:
            return None


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pre = ""
    if path.is_file() and path.stat().st_size:
        with path.open("rb") as f:
            f.seek(-1, 2)
            pre = "" if f.read(1) == b"\n" else "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(pre + line + "\n")


def save(verb: str, res: dict) -> Path:
    base = VIA / "VIA_Reports" / "vdf_fin5y"
    od = base / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    od.mkdir(parents=True, exist_ok=True)
    df = frame(res.get("rows", []))
    if df is not None and len(res.get("rows", [])):
        try:
            df.write_parquet(od / f"{verb}.parquet", compression="zstd") if hasattr(df, "write_parquet") else df.to_parquet(od / f"{verb}.parquet", compression="zstd", index=False)
        except Exception:  # noqa: BLE001 - 沒有 parquet 寫手 → jsonl 退路
            (od / f"{verb}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in res["rows"]), encoding="utf-8")
    summ = {k: v for k, v in res.items() if k != "rows"}
    summ.update(tool=TAG, verb=verb, utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), accel=VIA_ACCEL is not None, net=VIA_NET_TOOL_PATH is not None)
    (od / "SUMMARY.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    append_line(base / "RUN_LEDGER.jsonl", json.dumps({"verb": verb, "utc": summ["utc"], "lamp": res.get("lamp"), "secs": round(time.time() - _T0, 2),
                                                       "counts": res.get("counts")}, ensure_ascii=False, default=str))
    return od


def main() -> int:
    a = sys.argv[1:]
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    verb = a[0] if a else "plan"
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d  # noqa: E731
    prm = params()
    only = [x for x in re.split(r"[,\s]+", opt("--only", "") or "") if x] or None
    say(f"{TAG} {verb} · 正本 {prm['_master']} · 年度 {req_years(prm)} → 近 {prm['fin5y.years']} 年 · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在'}")
    unreg = [k for k, v in prm["_src"].items() if v == "DEFAULT"]
    if unreg and verb != "params-init":
        say(f"[YELLOW] {len(unreg)} 個參數還沒登進 VDF 正本(用預設):先 params-init --apply")
    if verb == "params-init":
        e53p = newest(HERE, "VDF_ENG053_ParamEngineMap_v*.py")
        sp = importlib.util.spec_from_file_location(f"{STEM}_e53", e53p)
        e53 = importlib.util.module_from_spec(sp)
        sys.modules[sp.name] = e53
        sp.loader.exec_module(e53)
        mt, ut = e53.tail_of(VDF, e53.MASTER), e53.tail_of(VDF, e53.UNIFIED)
        m = json.loads(mt.read_text(encoding="utf-8"))
        have = {e["path"] for e in m["params"]}
        add = [(k, v) for k, v in DEFAULTS.items() if k not in have]
        res = {"rows": [{"path": k, "state": "ADD"} for k, _ in add], "lamp": "GREEN" if not add else "YELLOW", "counts": {"add": len(add)}}
        if add and "--apply" in a:
            nums = [int(x["id"].rsplit("-", 1)[1]) for x in m["params"] if re.fullmatch(r"VDF-PAR-\d+", str(x.get("id")))]
            n, at = max(nums or [0]), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            for k, v in add:
                n += 1
                cls = "輸入參數" if k in ("fin5y.universe_regex", "fin5y.bases", "fin5y.endpoints", "fin5y.rate_s") else ("時間範圍" if k == "fin5y.years" else "規則")
                m["params"].append({"name": f"五年財報 · {k.split('.', 1)[1]}", "book": ut.name, "path": k, "value": v, "class": cls, "mutable": True,
                                    "why": f"{TAG} params-init(操作員 2026-11-25:全部上市上櫃普通股 · 近 5 年度 · MOPS)", "id": f"VDF-PAR-{n:03d}",
                                    "version": "v0100", "registered_at": at, "derive_pending": at})
            res["written"] = e53.write_next(mt, m, f"{TAG} params-init:補登 {len(add)} 個五年財報參數(範圍 = 全部上市上櫃普通股)").name
            d = subprocess.run([sys.executable, str(e53p), "derive", "--apply"], cwd=str(HERE), capture_output=True, text=True)
            res["derive_rc"] = d.returncode
            res["lamp"] = "GREEN" if d.returncode in (0, 2) else "RED"
    elif verb == "plan":
        mdb = market_db()
        codes = []
        if mdb:
            c = _duck().connect(str(mdb), read_only=True)
            codes = universe(c, prm, only)
            c.close()
        elif only:
            codes = universe(None, prm, only)
        done = 0
        if DB_PATH.is_file():
            c = _duck().connect(str(DB_PATH), read_only=True)
            try:
                ds = done_set(c)
                done = sum(1 for x in codes for y in req_years(prm) for s in STATEMENTS if (x, y, s) in ds)
            except Exception:  # noqa: BLE001 - 舊庫沒有表 = 0
                done = 0
            c.close()
        total = len(codes) * len(req_years(prm)) * 3
        est = (total - done) * float(prm["fin5y.rate_s"])
        res = {"rows": [{"code": x} for x in codes[:5000]], "lamp": "GREEN" if codes else "YELLOW",
               "counts": {"universe": len(codes), "requests": total, "already_ok": done, "todo": total - done, "est_hours": round(est / 3600, 1),
                          "market_db": str(mdb) if mdb else None}}
        if not codes:
            res["note"] = "名單是空的:先跑 MDL009(台股清單)或用 --only 指定代碼"
    elif verb == "probe":
        if "--live" not in a:
            res = {"rows": [], "lamp": "YELLOW", "note": "probe 會出網:加 --live(同意閘只在本行程)", "counts": {}}
        else:
            os.environ.setdefault("VIA_NET_CONSENT", "YES")
            os.environ.setdefault("VIA_SCRAPE_CONSENT", "YES")
            rows, y = [], latest_fy()
            for b in prm["fin5y.bases"]:
                for kind, ep in prm["fin5y.endpoints"].items():
                    st, body = get_html(mops_url(b, ep, "2330", y - 1911 + (1 if kind == "dividend" else 0), kind))
                    n = len(parse_statement(body)) if st == "OK" and kind != "dividend" else (len(parse_dividend(body, prm["fin5y.items"]["cash_dps"])) if st == "OK" else 0)
                    rows.append({"base": b, "kind": kind, "state": st, "parsed": n, "bytes": len(body) if st == "OK" else 0, "note": "" if st == "OK" else str(body)[:120]})
                    time.sleep(float(prm["fin5y.rate_s"]))
            okb = [b for b in prm["fin5y.bases"] if all(r["state"] == "OK" and r["parsed"] for r in rows if r["base"] == b)]
            res = {"rows": rows, "lamp": "GREEN" if okb else "RED", "counts": {"bases_ok": okb}}
    elif verb == "fetch":
        if "--live" not in a:
            res = {"rows": [], "lamp": "YELLOW", "note": "fetch 會出網:加 --live", "counts": {}}
        else:
            os.environ.setdefault("VIA_NET_CONSENT", "YES")
            os.environ.setdefault("VIA_SCRAPE_CONSENT", "YES")
            mdb = market_db()
            mc = _duck().connect(str(mdb), read_only=True) if mdb else None
            codes = universe(mc, prm, only)
            if mc:
                mc.close()
            con = open_db()
            st = fetch(con, codes, prm, max_req=int(opt("--max")) if opt("--max") else None)
            con.close()
            res = {"rows": [], "counts": st, "lamp": "RED" if st["blocked"] else ("GREEN" if not st["fail"] else "YELLOW")}
    elif verb == "compute":
        if not DB_PATH.is_file():
            res = {"rows": [], "lamp": "YELLOW", "note": f"庫不在:{DB_PATH}(先 fetch --live)", "counts": {}}
        else:
            con = open_db()
            rows = compute(con, prm)
            info = save_metrics(con, rows, VIA / "VIA_Reports" / "vdf_lake")
            con.close()
            res = {"rows": rows, "counts": info, "lamp": "RED" if info["dup"] else ("GREEN" if info["complete_rows"] == info["rows"] and rows else "YELLOW")}
    else:
        say(f"[RED] 未知動詞 {verb}")
        return 1
    od = save(verb, res)
    say(f"{verb} · {res['lamp']} · " + " · ".join(f"{k} {v}" for k, v in (res.get("counts") or {}).items()) + (f" · 寫 {res['written']}" if res.get("written") else "")
        + (f" · {res['note']}" if res.get("note") else ""))
    say(f"DataFrame → {od}")
    return {"GREEN": 0, "YELLOW": 2}.get(res["lamp"], 1)


# ---------------------------------------------------------------- 自測(全在暫存夾造資料;零網路)
INC = """<table><tr><th>會計項目</th><th>2024年度 金額</th><th>%</th><th>2023年度 金額</th><th>%</th></tr>
<tr><td>營業利益（損失）</td><td>1,000,000</td><td>40</td><td>800,000</td><td>38</td></tr>
<tr><td>本期淨利（淨損）歸屬於母公司業主</td><td>900,000</td><td>36</td><td>700,000</td><td>33</td></tr>
<tr><td>基 本 每 股 盈 餘</td><td>9.00</td><td></td><td>7.00</td><td></td></tr>
<tr><td>稀釋每股盈餘</td><td>8.95</td><td></td><td>6.98</td><td></td></tr></table>"""
BAL = """<table><tr><th>會計項目</th><th>2024年12月31日 金額</th><th>%</th><th>2023年12月31日 金額</th><th>%</th></tr>
<tr><td>普通股股本</td><td>1,000,000</td><td>10</td><td>1,000,000</td><td>11</td></tr>
<tr><td>歸屬於母公司業主之權益合計</td><td>5,000,000</td><td>60</td><td>4,000,000</td><td>58</td></tr></table>"""
CF = """<table><tr><th>會計項目</th><th>2024年度</th><th>2023年度</th></tr>
<tr><td>折舊費用</td><td>300,000</td><td>250,000</td></tr><tr><td>攤銷費用</td><td>20,000</td><td>15,000</td></tr>
<tr><td>發放現金股利</td><td>(400,000)</td><td>(350,000)</td></tr></table>"""
DIV = """<table><tr><th>公司代號名稱</th><th>股利所屬年(季)度</th><th>盈餘分配之現金股利(元/股)</th></tr>
<tr><td>2330 台積電</td><td>113年</td><td>4.50</td></tr><tr><td>2317 鴻海</td><td>113年</td><td>5.20</td></tr></table>"""


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, str(VIA_NET_TOOL_PATH))
    chk("年報期限:11/25 → 去年度 · 3/1 → 前年度", latest_fy(date(2026, 11, 25)) == 2025 and latest_fy(date(2026, 3, 1)) == 2024)
    chk("5 年 → 抓 Y · Y−2 · Y−4(每份含前期 → 6 年)", req_years(DEFAULTS, date(2026, 11, 25)) == [2025, 2023, 2021])
    inc = parse_statement(INC)
    chk("損益表解析:表頭 % 欄跳過 · 全形括號 / 空白正規化", ("稀釋每股盈餘", 8.95, 6.98) in inc and ("基本每股盈餘", 9.0, 7.0) in inc, str(inc))
    chk("現金流量:括號 = 負數", ("發放現金股利", -400000.0, -350000.0) in parse_statement(CF))
    chk("股利彙總:代號 · 民國年 → 西元 · 現金股利欄依參數冊", parse_dividend(DIV, DEFAULTS["fin5y.items"]["cash_dps"]) == [("2330", 2024, 4.5), ("2317", 2024, 5.2)])
    chk("名單只留四碼首位非 0", universe(None, DEFAULTS, ["2330", "0050", "00981A", "2317", "1101B"]) == ["2330", "2317"])
    u = mops_url(DEFAULTS["fin5y.bases"][0], "ajax_t164sb04", "2330", 113, "income")
    chk("MOPS 網址:co_id · 民國年 · 第四季(年報)", "co_id=2330" in u and "year=113" in u and "season=04" in u)
    try:
        _duck()
    except ImportError:
        chk("duckdb 可用(缺 = 黃)", False, "duckdb 沒裝")
        print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}", flush=True)
        return 1
    with tempfile.TemporaryDirectory() as td:
        con = open_db(Path(td) / "f.duckdb")
        pages = {"ajax_t164sb04": INC, "ajax_t164sb03": BAL, "ajax_t164sb05": CF, "ajax_t05st09_2": DIV}
        calls = []

        def getter(url):
            calls.append(url)
            if "mopsov" in url:
                return "FAIL", "舊站關了"                                  # 第一個前缀失敗 → 換下一個
            ep = re.search(r"/(ajax_\w+)\?", url).group(1)
            return "OK", pages[ep]
        prm = json.loads(json.dumps(DEFAULTS))
        prm["fin5y.years"] = 1                                          # 自測:只抓 1 個請求年(= 2 年)
        st = fetch(con, ["2330"], prm, getter=getter, sleep=lambda s: None)
        chk("fetch:前綴失敗換下一個 · 三表各一次 · 寫入", st["ok"] == 3 and st["fail"] == 0 and any("mops.twse" in c for c in calls), str(st))
        st2 = fetch(con, ["2330"], prm, getter=getter, sleep=lambda s: None)
        chk("先看庫:已 OK 的不重抓(斷點續跑)", st2["todo"] == 0 and st2["skipped_done"] == 3)
        y = latest_fy()
        pages["ajax_t164sb04"] = INC.replace("8.95", "9.10")
        con.execute("DELETE FROM fin5y_log WHERE statement = 'income'")
        st3 = fetch(con, ["2330"], prm, getter=getter, sleep=lambda s: None)
        chk("同鍵不同值 = 交易所更正:留舊值 · 另列", st3["revised"] == 1 and con.execute("SELECT value FROM fin5y_raw WHERE item_norm='稀釋每股盈餘' AND fy=?", [y]).fetchone()[0] == 8.95)
        con.execute("UPDATE fin5y_div SET fy = ?", [y])                 # 自測的股利年對到本期
        prm["fin5y.years"] = 2
        rows = compute(con, prm)
        r = next(x for x in rows if x["fy"] == y)
        chk("8 指標:EPS · BVPS · DPS · 實付股利 · 配息率 · ROE · EBITDA/股 · EPS 年增率",
            r["diluted_eps"] == 8.95 and abs(r["bvps"] - 50.0) < 1e-9 and r["dps"] == 4.5 and r["dividends_paid"] == 400000000.0
            and abs(r["payout_ratio"] - 4.5 / 8.95) < 1e-9 and abs(r["roe"] - 900000 / 4500000) < 1e-9
            and abs(r["ebitda_ps"] - 1320000 * 1000 / (900000 * 1000 / 9.0)) < 1e-9 and abs(r["diluted_eps_growth"] - (8.95 / 6.98 - 1)) < 1e-9, str(r))
        r0 = next(x for x in rows if x["fy"] == y - 1)
        chk("缺輸入 = 空值 + missing 寫缺什麼(不補 0)", r0["roe"] is None and "roe" in r0["missing"] and r0["diluted_eps_growth"] is None)
        info = save_metrics(con, rows, Path(td) / "lake")
        info2 = save_metrics(con, rows, Path(td) / "lake")
        chk("輸出:DuckDB 表 + Parquet 原子換新 · 零重複", info["dup"] == 0 and info2["rows"] == info["rows"] and len(list((Path(td) / "lake" / "_metrics").glob("*.parquet"))) == 1)
        chk("輸出 DataFrame", frame(rows) is not None)
        con.close()
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

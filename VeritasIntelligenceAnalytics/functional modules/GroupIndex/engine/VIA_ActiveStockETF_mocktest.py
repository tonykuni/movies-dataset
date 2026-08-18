#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_ActiveStockETF_mocktest.py
==============================
End-to-end integration harness for VIA_ActiveStockETF.py.

Stands up a local HTTP server that speaks the *real* TWSE / ISIN / TPEx response
shapes, then drives the actual pipeline against it via the --base-* overrides.
Nothing in the engine is stubbed: discovery, registry merge, history walk,
return math, rendering and exports all run for real.

  python VIA_ActiveStockETF_mocktest.py            run every scenario
  python VIA_ActiveStockETF_mocktest.py --keep     keep the output folder

Scenarios covered
  1. cold start        - empty registry, full discovery, HTML/JSON/CSV emitted
  2. new listing       - a freshly approved ETF appears with no edit to the code
  3. delisting         - a code vanishes from every feed -> DORMANT, never deleted
  4. degraded sources  - NAV endpoint 500s, fund master 500s -> PENDING, no crash
  5. cache/offline     - second run served from cache with the network shut off
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

import argparse
import csv
import datetime as _dt
import http.server
import importlib.util
import io
import json
import re
import shutil
import socketserver
import sys
import tempfile
import threading
import traceback
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("via_etf", HERE / "VIA_ActiveStockETF.py")
ENG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENG)


# --------------------------------------------------------------------------- #
# Mock data
# --------------------------------------------------------------------------- #

def iso_to_roc(iso: str) -> str:
    y, m, d = iso.split("-")
    return "%d/%s/%s" % (int(y) - 1911, m, d)


def trading_days(n: int, end: _dt.date) -> list[_dt.date]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= _dt.timedelta(days=1)
    return list(reversed(out))


class MockMarket:
    """Deterministic synthetic market used ONLY to exercise the engine's plumbing."""

    def __init__(self, today: _dt.date):
        self.today = today
        # code -> (name, pm, listed, units, days_of_history, base_price, drift)
        self.funds = {
            "00980A": ("主動野村臺灣優選", "陳柏宇", "2025-05-05", 1.20e9, 320, 25.0, 0.045),
            "00981A": ("主動統一台股增長", "林哲緯", "2025-05-05", 2.85e9, 320, 30.0, 0.070),
            "00982A": ("主動群益台灣強棒", "黃詩涵", "2025-06-10", 1.56e9, 300, 22.0, 0.030),
            "00999A": ("主動凱基台灣高息", "張凱程", "2025-11-20", 0.44e9, 180, 15.0, -0.010),
            "00982D": ("主動群益投資級債", "吳承翰", "2025-09-01", 0.30e9, 220, 10.0, 0.005),
        }
        # decoys that must never enter the universe
        self.decoys = {
            "0050": ("元大台灣50", 190.0), "00878": ("國泰永續高股息", 24.0),
            "00679B": ("元大美債20年", 28.0), "2330": ("台積電", 1200.0),
            "00670L": ("富邦NASDAQ正2", 90.0),
        }
        self.hidden_from_quotes = {"00982A"}   # in fund master only -> tests the union
        self.dropped: set[str] = set()         # simulates a delisting
        self.fail_nav = False
        self.fail_fund_master = False

    # -- price series --------------------------------------------------------- #
    def series(self, code: str) -> list[tuple[_dt.date, float, int]]:
        if code in self.funds:
            _, _, _, _, days, base, drift = self.funds[code]
        elif code in self.decoys:
            base, days, drift = self.decoys[code][1], 320, 0.02
        else:
            return []
        out = []
        seed = sum(ord(c) for c in code)
        for i, d in enumerate(trading_days(days, self.today)):
            wobble = ((seed * (i + 7) * 1103515245 + 12345) % 1000) / 1000.0 - 0.5
            px = base * (1 + drift * i / 100.0) * (1 + wobble * 0.012)
            vol = 1000 * (500 + ((seed + i) % 4000))
            out.append((d, round(px, 2), vol))
        return out

    def last_quote(self, code: str):
        s = self.series(code)
        if len(s) < 2:
            return None
        return s[-1][0], s[-2][1], s[-1][1], s[-1][2]

    # -- payloads ------------------------------------------------------------- #
    def fund_master(self) -> list[dict]:
        rows = []
        for code, (name, pm, listed, units, *_rest) in self.funds.items():
            if code in self.dropped:
                continue
            rows.append({
                "出表日期": iso_to_roc(self.today.isoformat()),
                "基金代號": code, "基金簡稱": name,
                "基金類型": "指數股票型" + ("(債券)" if code.endswith("D") else ""),
                "基金中文名稱": name + ("主動式證券投資信託基金" if code.endswith("A") else "基金"),
                "基金英文名稱": "Active TW ETF " + code,
                "成立日期": iso_to_roc(listed), "上市日期": iso_to_roc(listed),
                "基金經理人": pm,
                "發行單位數/轉換數": "{:,.0f}".format(units),
                "保管機構": "台北富邦銀行",
            })
        # non-ETF funds that must be filtered out
        rows.append({"基金代號": "1234", "基金簡稱": "某某平衡基金", "基金經理人": "王某",
                     "上市日期": "", "發行單位數/轉換數": "0"})
        return rows

    def stock_day_all(self) -> list[dict]:
        rows = []
        codes = [c for c in self.funds if c not in self.hidden_from_quotes] + list(self.decoys)
        for code in codes:
            if code in self.dropped:
                continue
            q = self.last_quote(code)
            if not q:
                continue
            d, prev, close, vol = q
            name = (self.funds[code][0] if code in self.funds else self.decoys[code][0])
            rows.append({
                "Date": "%d%02d%02d" % (d.year - 1911, d.month, d.day),
                "Code": code, "Name": name,
                "TradeVolume": "{:,}".format(vol),
                "TradeValue": "{:,}".format(int(vol * close)),
                "OpeningPrice": "%.2f" % prev, "HighestPrice": "%.2f" % max(prev, close),
                "LowestPrice": "%.2f" % min(prev, close), "ClosingPrice": "%.2f" % close,
                "Change": "%.2f" % (close - prev), "Transaction": "12,345",
            })
        return rows

    def stock_day(self, code: str, yyyymm: str) -> dict:
        rows = []
        for d, px, vol in self.series(code):
            if d.strftime("%Y%m") != yyyymm:
                continue
            rows.append(["%d/%02d/%02d" % (d.year - 1911, d.month, d.day),
                         "{:,}".format(vol), "{:,}".format(int(vol * px)),
                         "%.2f" % px, "%.2f" % (px * 1.004), "%.2f" % (px * 0.996),
                         "%.2f" % px, "+0.10", "3,456"])
        if not rows:
            return {"stat": "很抱歉，沒有符合條件的資料!", "date": yyyymm + "01"}
        return {"stat": "OK", "date": yyyymm + "01", "title": "%s 各日成交資訊" % code,
                "fields": ["日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價",
                           "收盤價", "漲跌價差", "成交筆數"],
                "data": rows, "notes": []}

    def isin_html(self, mode: int) -> str:
        head = ("<html><head><meta http-equiv='Content-Type' content='text/html; charset=Big5'>"
                "</head><body><table class='h4'>")
        rows = ["<tr><td colspan='7' align='center'>%s指數股票型基金(ETF)</td></tr>"
                % ("上市" if mode == 2 else "上櫃")]
        pool = ({**{c: v[0] for c, v in self.funds.items()},
                 **{c: v[0] for c, v in self.decoys.items()}} if mode == 2 else {})
        for code, name in pool.items():
            if code in self.dropped:
                continue
            listed = self.funds[code][2] if code in self.funds else "2003-06-25"
            rows.append(
                "<tr><td bgcolor=#FAFAD2>%s\u3000%s</td><td bgcolor=#FAFAD2>TW%s09</td>"
                "<td bgcolor=#FAFAD2>%s</td><td bgcolor=#FAFAD2>%s</td>"
                "<td bgcolor=#FAFAD2>ETF</td><td bgcolor=#FAFAD2>CEOGEU</td>"
                "<td bgcolor=#FAFAD2>&nbsp;</td></tr>"
                % (code, name, code.ljust(10, "0"), iso_to_roc(listed),
                   "上市" if mode == 2 else "上櫃"))
        return head + "".join(rows) + "</table></body></html>"

    def etf_nav(self) -> list[dict]:
        rows = []
        for code in self.funds:
            if code in self.dropped:
                continue
            q = self.last_quote(code)
            if not q:
                continue
            rows.append({"日期": "%d%02d%02d" % (q[0].year - 1911, q[0].month, q[0].day),
                         "基金代號": code, "基金名稱": self.funds[code][0],
                         "每受益權單位淨值": "%.4f" % (q[2] * 1.001),
                         "前一營業日淨值": "%.4f" % (q[1] * 1.001),
                         "折溢價%": "-0.10"})
        return rows

    def tpex(self) -> list[dict]:
        return [{"Date": self.today.strftime("%Y%m%d"), "SecuritiesCompanyCode": "6488",
                 "CompanyName": "環球晶", "Close": "500.0"}]


# --------------------------------------------------------------------------- #
# Mock HTTP server
# --------------------------------------------------------------------------- #

class MockServer:
    def __init__(self, market: MockMarket):
        self.market = market
        self.hits: dict[str, int] = {}
        m = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def _send(self, body: bytes, ctype="application/json; charset=utf-8", code=200):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):                                    # noqa: N802
                u = urllib.parse.urlparse(self.path)
                q = urllib.parse.parse_qs(u.query)
                m.hits[u.path] = m.hits.get(u.path, 0) + 1
                mk = m.market

                if u.path.endswith("/opendata/t187ap47_L"):
                    if mk.fail_fund_master:
                        return self._send(b'{"error":"boom"}', code=500)
                    return self._send(json.dumps(mk.fund_master(), ensure_ascii=False).encode())

                if u.path.endswith("/exchangeReport/STOCK_DAY_ALL"):
                    return self._send(json.dumps(mk.stock_day_all(), ensure_ascii=False).encode())

                if "STOCK_DAY" in u.path:
                    code = (q.get("stockNo") or [""])[0]
                    date = (q.get("date") or ["20260101"])[0]
                    doc = mk.stock_day(code, date[:6])
                    return self._send(json.dumps(doc, ensure_ascii=False).encode())

                if "C_public.jsp" in u.path:
                    mode = int((q.get("strMode") or ["2"])[0])
                    # the real registrar serves Big5 - exercise the decoder
                    return self._send(mk.isin_html(mode).encode("cp950", errors="replace"),
                                      ctype="text/html; charset=Big5")

                if "etfNav" in u.path:
                    if mk.fail_nav:
                        return self._send(b"<html>service unavailable</html>",
                                          ctype="text/html", code=503)
                    return self._send(json.dumps({"stat": "OK", "data": mk.etf_nav()},
                                                 ensure_ascii=False).encode())

                if "tpex_mainboard_daily_close_quotes" in u.path:
                    return self._send(json.dumps(mk.tpex(), ensure_ascii=False).encode())

                return self._send(b'{"error":"not found"}', code=404)

            def log_message(self, *a):                           # silence
                return

        self.httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def base(self) -> str:
        return "http://127.0.0.1:%d" % self.port


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond, detail: str = "") -> None:
    RESULTS.append((name, bool(cond), detail))
    sys.stdout.write("    %s %s%s\n" % ("\u2713" if cond else "\u2717", name,
                                        "" if cond else "   <-- " + detail))
    sys.stdout.flush()


def run_engine(server: MockServer, out: Path, extra=None) -> int:
    argv = ["--out", str(out), "--quiet", "--months", "14", "--workers", "4",
            "--base-openapi", server.base + "/v1",
            "--base-twse", server.base,
            "--base-isin", server.base,
            "--base-tpex", server.base]
    argv += extra or []
    return ENG.main(argv)


def load_out(out: Path):
    doc = json.loads((out / "etf_matrix.json").read_text(encoding="utf-8"))
    reg = json.loads((out / "active_etf_registry.json").read_text(encoding="utf-8"))
    html = sorted(out.glob("VIA_ActiveStockETF_2*.html"))[-1].read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.open(out / "etf_matrix.csv", encoding="utf-8")))
    return doc, reg, html, rows


def scenario_cold_start(out: Path, today: _dt.date) -> MockMarket:
    print("\n[1] cold start - discovery, history, render, export")
    mk = MockMarket(today)
    with MockServer(mk) as srv:
        rc = run_engine(srv, out)
    check("exit code 0", rc == 0, "rc=%s" % rc)
    doc, reg, html, rows = load_out(out)

    codes = [e["code"] for e in doc["etfs"]]
    check("universe = the 4 equity active ETFs",
          codes == ["00980A", "00981A", "00982A", "00999A"], str(codes))
    check("bond suffix D excluded by default", "00982D" not in codes)
    check("passive decoys excluded",
          not any(c in codes for c in ("0050", "00878", "00679B", "00670L", "2330")))
    check("fund-master-only code still found (feed union)", "00982A" in codes)

    by = {e["code"]: e for e in doc["etfs"]}
    check("PM pulled from official field",
          by["00981A"]["pm"]["value"] == "\u6797\u54f2\u7def"
          and by["00981A"]["pm"]["evidence"] == "V", str(by["00981A"]["pm"]))
    check("trust derived from name",
          by["00981A"]["trust"]["value"] == "\u7d71\u4e00\u6295\u4fe1"
          and by["00981A"]["trust"]["evidence"] == "Der", str(by["00981A"]["trust"]))
    check("style derived", by["00981A"]["style"]["value"] == "\u6210\u9577",
          str(by["00981A"]["style"]))
    check("NAV official from feed", by["00981A"]["nav"]["evidence"] == "V",
          str(by["00981A"]["nav"]))
    check("AUM = units x NAV", by["00981A"]["aum"]["value"] and by["00981A"]["aum"]["value"] > 0,
          str(by["00981A"]["aum"]))

    r = by["00981A"]["ret"]
    check("240D return computed on deep history", r["horizons"]["240"]["value"] is not None,
          str(r["horizons"]))
    check("YTD computed", r["ytd"]["value"] is not None, str(r["ytd"]))
    check("short-history fund has no 240D",
          by["00999A"]["ret"]["horizons"]["240"]["value"] is None,
          str(by["00999A"]["ret"]["horizons"]["240"]))
    check("unresolved fee stays PENDING",
          by["00981A"]["fee"]["value"] is None and by["00981A"]["fee"]["evidence"] == "P")
    check("first-run flow is PENDING not zero", by["00981A"]["flow_ytd"]["value"] is None,
          str(by["00981A"]["flow_ytd"]))

    check("registry seeded", len(reg["entries"]) == 4, str(list(reg["entries"])))
    check("snapshots recorded", len(reg["snapshots"]) == 4)
    check("HTML has no unsubstituted placeholder", "${" not in html)
    check("HTML lists every code", all(c in html for c in codes))
    check("CSV row count matches", len(rows) == 4, str(len(rows)))
    check("CSV blanks missing horizon rather than zeroing",
          [x for x in rows if x["code"] == "00999A"][0]["ret_240D"] == "")
    return mk


def scenario_new_listing(out: Path, today: _dt.date) -> None:
    print("\n[2] new listing - appears with zero code changes")
    mk = MockMarket(today)
    listed = today - _dt.timedelta(days=9)
    mk.funds["00404A"] = ("主動元大台股動能", "李宛蓉", listed.isoformat(), 0.18e9, 7, 12.0, 0.02)
    with MockServer(mk) as srv:
        rc = run_engine(srv, out)
    check("exit code 0", rc == 0, "rc=%s" % rc)
    doc, reg, html, _ = load_out(out)
    by = {e["code"]: e for e in doc["etfs"]}
    check("new code discovered automatically", "00404A" in by, str(list(by)))
    check("flagged NEW", by.get("00404A", {}).get("is_new") is True)
    check("NEW badge rendered", 'class="new">NEW' in html)
    check("registry recorded it", "00404A" in reg["entries"])
    check("registry marks first_seen",
          reg["entries"]["00404A"]["first_seen"] == ENG.today_tw().isoformat())
    check("thin history -> long horizons PENDING",
          by["00404A"]["ret"]["horizons"]["60"]["value"] is None)
    check("thin history -> since-listing still computed",
          by["00404A"]["ret"]["since"]["value"] is not None)


def scenario_delisting(out: Path, today: _dt.date) -> None:
    print("\n[3] delisting - only-increase-never-decrease holds")
    mk = MockMarket(today)
    mk.funds["00404A"] = ("主動元大台股動能", "李宛蓉",
                          (today - _dt.timedelta(days=9)).isoformat(), 0.18e9, 7, 12.0, 0.02)
    mk.dropped = {"00980A"}
    with MockServer(mk) as srv:
        rc = run_engine(srv, out)
    check("exit code 0", rc == 0, "rc=%s" % rc)
    doc, reg, html, _ = load_out(out)
    codes = [e["code"] for e in doc["etfs"]]
    check("dropped code leaves the live table", "00980A" not in codes, str(codes))
    check("registry entry survives", "00980A" in reg["entries"])
    check("status -> DORMANT", reg["entries"]["00980A"]["status"] == "DORMANT")
    check("name history retained", reg["entries"]["00980A"]["name"] != "")
    check("dormant event logged",
          any(h["event"] == "WENT_DORMANT" for h in reg["entries"]["00980A"]["history"]))
    check("HTML surfaces the dormant block", "DORMANT" in html)
    check("previous-generation registry kept",
          (out / "active_etf_registry_prev.json").exists())


def scenario_degraded(out: Path, today: _dt.date) -> None:
    print("\n[4] degraded sources - PENDING, never invented, never a crash")
    mk = MockMarket(today)
    mk.fail_nav = True
    with MockServer(mk) as srv:
        rc = run_engine(srv, out, extra=["--no-cache"])
    check("exit code 0 despite dead NAV endpoint", rc == 0, "rc=%s" % rc)
    doc, _reg, html, _ = load_out(out)
    by = {e["code"]: e for e in doc["etfs"]}
    check("NAV falls back to close, tagged Est not V",
          by["00981A"]["nav"]["evidence"] == "Est", str(by["00981A"]["nav"]))
    check("AUM inherits the Est tag", by["00981A"]["aum"]["evidence"] == "Est",
          str(by["00981A"]["aum"]))
    check("Est badge visible to the reader", ">Est<" in html)

    print("    ... now killing the fund master too")
    mk2 = MockMarket(today)
    mk2.fail_fund_master = True
    with MockServer(mk2) as srv:
        rc = run_engine(srv, out, extra=["--no-cache"])
    check("exit code 0 with fund master down", rc == 0, "rc=%s" % rc)
    doc2, _r2, html2, _ = load_out(out)
    codes2 = sorted(e["code"] for e in doc2["etfs"])
    check("universe still recovered from quotes + ISIN",
          "00981A" in codes2 and "00980A" in codes2, str(codes2))
    by2 = {e["code"]: e for e in doc2["etfs"]}
    check("PM now PENDING rather than guessed",
          by2["00981A"]["pm"]["value"] is None and by2["00981A"]["pm"]["evidence"] == "P")
    check("AUM PENDING without units", by2["00981A"]["aum"]["value"] is None)
    check("HTML still renders", "${" not in html2 and "<!DOCTYPE html>" in html2)


def scenario_cache_offline(out: Path, today: _dt.date) -> None:
    print("\n[5] cache + offline - second run with the network gone")
    mk = MockMarket(today)
    with MockServer(mk) as srv:
        base = srv.base
        rc = run_engine(srv, out)
        check("warm run ok", rc == 0, "rc=%s" % rc)
        hits_after_warm = sum(srv.hits.values())
    # The server is now shut down.  Same base URL (so cache keys match) but the
    # host is dead, so anything returned had to come off disk.
    rc = ENG.main(["--out", str(out), "--quiet", "--offline", "--months", "14",
                   "--base-openapi", base + "/v1", "--base-twse", base,
                   "--base-isin", base, "--base-tpex", base])
    check("offline run exits 0", rc == 0, "rc=%s" % rc)
    doc, _reg, html, _ = load_out(out)
    check("offline run still produced the full universe", len(doc["etfs"]) == 4,
          str(len(doc["etfs"])))
    check("offline HTML intact", "<!DOCTYPE html>" in html and "${" not in html)
    check("http stats show cache served it", doc["meta"]["http"]["cache"] > 0,
          str(doc["meta"]["http"]))
    check("mock actually got exercised", hits_after_warm > 0, str(hits_after_warm))

    # cold cache + offline = nothing knowable.  That must be loud, not a silent 0.
    cold = out.parent / "cold_offline"
    rc = ENG.main(["--out", str(cold), "--quiet", "--offline", "--months", "3",
                   "--base-openapi", base + "/v1", "--base-twse", base,
                   "--base-isin", base, "--base-tpex", base])
    check("empty universe exits non-zero", rc == 3, "rc=%s" % rc)
    check("empty run still wrote outputs for diagnosis",
          (cold / "etf_matrix.json").exists())


def scenario_flow_accumulation(out: Path, today: _dt.date) -> None:
    print("\n[6] flow accrual - PENDING until the engine owns two snapshots")
    reg_path = out / "active_etf_registry.json"
    reg = ENG.Registry(reg_path)
    yesterday = (today - _dt.timedelta(days=1)).isoformat()
    for code in ("00980A", "00981A", "00982A", "00999A"):
        cur = reg.data["snapshots"].get(code, [])
        if cur:
            reg.add_snapshot(code, yesterday, cur[0].get("nav"),
                             (cur[0].get("units") or 0) * 0.90)
    reg.save(today.isoformat())

    mk = MockMarket(today)
    with MockServer(mk) as srv:
        rc = run_engine(srv, out)
    check("exit code 0", rc == 0, "rc=%s" % rc)
    doc, _reg, html, _ = load_out(out)
    by = {e["code"]: e for e in doc["etfs"]}
    f = by["00981A"]["flow_ytd"]
    check("flow now computes from observed unit deltas", f["value"] is not None, str(f))
    check("flow tagged Der not V", f["evidence"] == "Der", str(f))
    check("flow sign is positive for a growing fund", (f["value"] or 0) > 0, str(f))
    check("HTML renders the flow", "${" not in html)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    today = ENG.today_tw()
    tmp = Path(tempfile.mkdtemp(prefix="via_etf_it_"))
    print("=" * 74)
    print("  VIA ActiveStockETF - INTEGRATION TEST (mock TWSE/ISIN/TPEx)")
    print("  workspace %s" % tmp)
    print("=" * 74)

    try:
        scenario_cold_start(tmp / "s1", today)
        scenario_new_listing(tmp / "s1", today)
        scenario_delisting(tmp / "s1", today)
        scenario_degraded(tmp / "s4", today)
        scenario_cache_offline(tmp / "s5", today)
        scenario_flow_accumulation(tmp / "s5", today)
    except Exception:                                          # noqa: BLE001
        traceback.print_exc()
        RESULTS.append(("harness crashed", False, "exception"))

    ok = sum(1 for _n, c, _d in RESULTS if c)
    print("\n" + "=" * 74)
    print("  %d/%d CHECKS PASS" % (ok, len(RESULTS)))
    for n, c, d in RESULTS:
        if not c:
            print("   FAIL  %s   %s" % (n, d))
    print("=" * 74)

    if args.keep:
        print("  workspace kept: %s" % tmp)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())

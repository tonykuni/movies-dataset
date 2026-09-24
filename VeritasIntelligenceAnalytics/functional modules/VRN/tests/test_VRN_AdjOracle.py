"""ADJ correctness against an independent source (批730; operator 2026-09-24 "結果也要實測正確性").

The exchange's own daily close (tw_trading_daily) is the price that actually traded; Yahoo's close in tw_daily_prices is
re-adjusted afterwards for stock dividends and splits.  The L99 conversion must keep the report-time ratio
    target_price_adj / adj_close(day before) == target_price / exchange_close(day before)
because both sides describe the same moment in two share bases.  This test samples the real market database (skipped
when none is found), checks that invariant and the upside against a separately written oracle, and counts how many
samples the v0137 formula (Yahoo close as the denominator) would have got wrong.

Same batch, second round (the first v0138 took a five-day median of the whole factor and got these wrong):
  * a cash ex-dividend date that falls on the day before the report must be used as it is (the new level persists);
  * a one-day stale price on either side must not move the factor (it must equal the previous report day's factor);
  * '6147.TWO' and '6147' must give the same answer;
  * ENG080 (four-point digest) must give the same factor as ENG073 for the same report date, and refuse the same events."""

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
import sys
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"
TP_MULT = 1.2           # a synthetic target 20% above the traded close of the day before the report
N_RETRO, N_PLAIN = 60, 60
N_STRATUM = 40


def def_load(name, filename):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ENGINE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(importlib.util.find_spec("duckdb"), "duckdb absent")
class AdjOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import duckdb
        cls.C = def_load("vrn_evidence_core_adj_oracle", "VRN_Evidence_Core.py")
        mod, why = cls.C.adj_engine()
        if mod is None or not hasattr(mod, "_prev_basis"):
            raise unittest.SkipTest("no ENG073 v0138+ in this tree: " + str(why))
        path, why = cls.C.adj_db()
        if not path:
            raise unittest.SkipTest("no market database: " + str(why))
        cls.db = path
        con = duckdb.connect(path, read_only=True)
        tables = {r[0] for r in con.execute("SELECT table_name FROM information_schema.tables").fetchall()}
        if not {"tw_daily_prices", "tw_trading_daily"} <= tables:
            con.close()
            raise unittest.SkipTest("market database lacks tw_daily_prices / tw_trading_daily")
        base = """
            WITH j AS (
              SELECT p.ticker, CAST(p.date AS VARCHAR) AS d, p.close AS yc, p.adj_close AS ya, t.close AS rc,
                     lead(CAST(p.date AS VARCHAR)) OVER (PARTITION BY p.ticker ORDER BY p.date) AS nd
              FROM tw_daily_prices p
              LEFT JOIN tw_trading_daily t
                ON t.code = regexp_replace(p.ticker, '\\.TWO?$', '') AND CAST(t.date AS VARCHAR) = CAST(p.date AS VARCHAR)
              WHERE p.close > 0 AND p.adj_close > 0)
            SELECT ticker, d, nd, yc, ya, rc FROM j
            WHERE rc > 0 AND nd IS NOT NULL AND {cond}
            ORDER BY hash(ticker || d) LIMIT {n}"""
        cls.retro = con.execute(base.format(cond="abs(yc / rc - 1) > 0.005", n=N_RETRO)).fetchall()
        cls.plain = con.execute(base.format(cond="abs(yc / rc - 1) <= 0.005", n=N_PLAIN)).fetchall()
        # day-level strata: c = Yahoo adj / Yahoo close (cash part), x = Yahoo close / exchange close (stock part);
        # nd = the report date (next trading day), pd = the day before d, both exchange days as well
        strata = """
            WITH j AS (
              SELECT p.ticker, CAST(p.date AS VARCHAR) AS d, p.close AS yc, p.adj_close AS ya, t.close AS rc
              FROM tw_daily_prices p JOIN tw_trading_daily t
                ON t.code = regexp_replace(p.ticker, '\\.TWO?$', '') AND CAST(t.date AS VARCHAR) = CAST(p.date AS VARCHAR)
              WHERE p.close > 0 AND p.adj_close > 0 AND t.close > 0),
            w AS (SELECT *, ya / yc AS c, yc / rc AS x, lag(ya / yc) OVER k AS cb, lead(ya / yc) OVER k AS ca,
                         lag(yc / rc) OVER k AS xb, lag(yc / rc, 2) OVER k AS xbb, lead(yc / rc) OVER k AS xa,
                         lag(d) OVER k AS db, lead(d) OVER k AS da
                  FROM j WINDOW k AS (PARTITION BY ticker ORDER BY d)),
            nx AS (SELECT ticker, CAST(date AS VARCHAR) AS d,
                          lead(CAST(date AS VARCHAR)) OVER (PARTITION BY ticker ORDER BY date) AS nd,
                          lag(CAST(date AS VARCHAR)) OVER (PARTITION BY ticker ORDER BY date) AS pd FROM tw_daily_prices)
            SELECT w.ticker, w.d, nx.nd, w.ya, w.rc, w.c, w.xb FROM w JOIN nx USING (ticker, d)
            WHERE nx.nd = w.da AND nx.pd = w.db AND w.cb IS NOT NULL AND w.ca IS NOT NULL AND w.xbb IS NOT NULL
              AND w.xa IS NOT NULL AND {cond}
            ORDER BY hash(w.ticker || w.d) LIMIT {n}"""
        cls.exdate = con.execute(strata.format(
            cond="abs(c / cb - 1) > 1e-3 AND abs(ca / c - 1) <= 1e-4 AND abs(x / xb - 1) <= 5e-4 AND abs(x / xa - 1) <= 5e-4",
            n=N_STRATUM)).fetchall()
        cls.blip = con.execute(strata.format(
            cond="abs(c / cb - 1) <= 1e-4 AND abs(ca / c - 1) <= 1e-4 AND abs(x / xb - 1) > 5e-4 AND abs(x / xa - 1) > 5e-4 "
                 "AND abs(xa / xb - 1) <= 5e-4 AND abs(xb / xbb - 1) <= 5e-4", n=N_STRATUM)).fetchall()
        tickers = sorted({r[0] for r in cls.retro + cls.plain})
        cls.latest = {}
        for tk in tickers:
            r = con.execute("SELECT CAST(date AS VARCHAR), adj_close, close FROM tw_daily_prices WHERE ticker=? "
                            "AND adj_close IS NOT NULL ORDER BY date DESC LIMIT 1", [tk]).fetchone()
            raw = con.execute("SELECT close FROM tw_trading_daily WHERE code=? AND CAST(date AS VARCHAR)=?",
                              [tk.split(".")[0], r[0]]).fetchone() if r else None
            cls.latest[tk] = (float(r[1]), r[0], float(raw[0]) if raw and raw[0] else None) if r else None
        con.close()

    def quote(self, row):
        tk, d, nd, yc, ya, rc = row
        tp = round(rc * TP_MULT, 2)
        return tp, self.C.adj_basis(tk.split(".")[0], nd, tp, db=self.db)

    def test_the_report_time_ratio_survives_the_adj_conversion(self):
        checked, events = 0, 0
        for row in self.retro + self.plain:
            tk, d, nd, yc, ya, rc = row
            tp, q = self.quote(row)
            st = str(q.get("state") or "")
            if st.startswith("ADJ_EVENT_UNADJUSTED"):
                events += 1
                self.assertTrue(q.get("adj_event"), (tk, nd, q.get("adj_event")))
                continue
            if not st.startswith("ADJ_OK") or q.get("adj_factor_basis") != "RAW_EXCHANGE":
                continue                 # ADJ_ABSURD (a far latest price) or a smoothed one-day glitch
            self.assertEqual((q["price_prev_date"], q["price_prev_raw"]), (d, rc), (tk, nd))
            # the invariant: same moment, two share bases
            self.assertAlmostEqual(q["target_price_adj"] / q["price_prev_adj"], tp / rc, delta=2e-4 * tp / rc,
                                   msg=(tk, nd, q["target_price_adj"], q["price_prev_adj"], tp, rc))
            checked += 1
        self.assertGreater(checked, 0.5 * (len(self.retro) + len(self.plain)), (checked, events))

    def test_upside_matches_a_separately_written_oracle(self):
        mismatches, v0137_off, n = [], [], 0
        for row in self.retro + self.plain:
            tk, d, nd, yc, ya, rc = row
            tp, q = self.quote(row)
            lat = self.latest.get(tk)
            if not lat or not str(q.get("state") or "").startswith("ADJ_OK") or q.get("adj_factor_basis") != "RAW_EXCHANGE":
                continue
            oracle = round((round(tp * ya / rc, 4) / lat[0] - 1) * 100, 1)
            old = round((round(tp * ya / yc, 4) / lat[0] - 1) * 100, 1)
            n += 1
            if q["upside_adj"] != oracle:
                mismatches.append((tk, nd, q["upside_adj"], oracle))
            if abs(old - oracle) > 0.5:
                v0137_off.append((tk, nd, old, oracle))
        print(f"\n[ADJ oracle] samples {n} · v0138 vs oracle mismatches {len(mismatches)} · "
              f"v0137 off by >0.5pt {len(v0137_off)}" + (f" (e.g. {v0137_off[0]})" if v0137_off else ""))
        self.assertEqual(mismatches, [])
        self.assertGreater(n, 0)
        if self.retro:
            self.assertGreater(len(v0137_off), 0, "Yahoo re-adjusted closes were sampled, so v0137 must disagree somewhere")

    def engine(self):
        mod, why = self.C.adj_engine()
        self.assertIsNotNone(mod, why)
        return mod

    def test_an_ex_dividend_on_the_factor_day_is_used_as_it_is(self):
        import duckdb
        mod = self.engine()
        con = duckdb.connect(self.db, read_only=True)
        wrong = []
        for tk, d, nd, ya, rc, c, xb in self.exdate:
            q = mod.adj_quote(con, tk.split(".")[0], nd, round(rc * TP_MULT, 2))
            if q["adj_factor"] is None or abs(q["adj_factor"] / (ya / rc) - 1) > 1e-9 or q["adj_factor_basis"] != "RAW_EXCHANGE":
                wrong.append((tk, d, q["adj_factor"], ya / rc, q["adj_factor_basis"]))
        con.close()
        print(f"\n[ADJ ex-date on the factor day] samples {len(self.exdate)} · wrong {len(wrong)}")
        self.assertEqual(wrong, [])
        self.assertGreater(len(self.exdate), 0)

    def test_a_one_day_stale_price_does_not_move_the_factor(self):
        import duckdb
        mod = self.engine()
        con = duckdb.connect(self.db, read_only=True)
        moved = []
        for tk, d, nd, ya, rc, c, xb in self.blip:
            code = tk.split(".")[0]
            today, yesterday = mod.adj_quote(con, code, nd, 100.0), mod.adj_quote(con, code, d, 100.0)
            # the cash part did not change (c == cb), so the report the day before must see the same factor
            if (today["adj_factor"] is None or yesterday["adj_factor"] is None
                    or abs(today["adj_factor"] / yesterday["adj_factor"] - 1) > 2e-4
                    or abs(today["adj_factor"] / (c * xb) - 1) > 1e-9):
                moved.append((tk, d, today["adj_factor"], yesterday["adj_factor"], c * xb))
        con.close()
        print(f"\n[ADJ one-day stale price] samples {len(self.blip)} · factor moved {len(moved)}")
        self.assertEqual(moved, [])
        self.assertGreater(len(self.blip), 0)

    def test_a_suffixed_ticker_gives_the_same_answer(self):
        import duckdb
        mod = self.engine()
        con = duckdb.connect(self.db, read_only=True)
        diff = []
        for tk, d, nd, yc, ya, rc in (self.retro + self.plain)[:30]:
            bare, suffixed = mod.adj_quote(con, tk.split(".")[0], nd, 100.0), mod.adj_quote(con, tk, nd, 100.0)
            if bare != suffixed or mod._prior_close(con, tk, nd) != mod._prior_close(con, tk.split(".")[0], nd):
                diff.append((tk, nd, bare.get("adj_factor_basis"), suffixed.get("adj_factor_basis")))
        con.close()
        self.assertEqual(diff, [])

    def test_the_four_point_digest_uses_the_same_factor(self):
        import duckdb
        hits = sorted(ENGINE.parent.glob("VRN_ENG080_FourPointDigest_v*.py"))
        if not hits:
            self.skipTest("no ENG080 in this tree")
        e80 = def_load("vrn_eng080_adj_oracle", "../" + hits[-1].name)
        if not hasattr(e80, "_eng073"):
            self.skipTest(hits[-1].name + " predates the ENG073 delegation")
        mod = self.engine()
        con = duckdb.connect(self.db, read_only=True)
        diff, n = [], 0
        for tk, d, nd, *_rest in self.retro + self.plain + self.exdate + self.blip:
            code = tk.split(".")[0]
            q, px = mod.adj_quote(con, code, nd, 100.0), e80.price_context(con, code, nd)
            st = str(q.get("upside_adj_state") or "")
            if st.startswith("ADJ_EVENT_UNADJUSTED"):
                if px.get("adjust_method") != "EVENT_UNADJUSTED":
                    diff.append((tk, nd, st, px.get("adjust_method")))
                continue
            if q["adj_factor"] is None or not px.get("adjust_factor") or not px.get("factor_latest"):
                continue
            n += 1
            # ENG080 converts raw-to-latest (factor / latest factor) and rounds a factor within RETRO_SAME of 1 to 1
            if abs(px["adjust_factor"] * px["factor_latest"] / q["adj_factor"] - 1) > 6e-4:
                diff.append((tk, nd, q["adj_factor"], px["adjust_factor"], px.get("factor_basis")))
        for rd in ("2025-10-20", "2025-10-31"):          # 4950: capital reduction on 2025-11-03 that Yahoo left unadjusted
            q, px = mod.adj_quote(con, "4950", rd, 12.0), e80.price_context(con, "4950", rd)
            if q.get("upside_adj_state") and str(q["upside_adj_state"]).startswith("ADJ_EVENT_UNADJUSTED"):
                self.assertEqual((px.get("adjust_method"), px.get("adjust_factor")), ("EVENT_UNADJUSTED", None), rd)
        con.close()
        print(f"\n[ENG080 vs ENG073] samples {n} · disagree {len(diff)}")
        self.assertEqual(diff, [])
        self.assertGreater(n, 0)

    def test_the_latest_adj_close_is_the_traded_price(self):
        both = [(tk, v) for tk, v in self.latest.items() if v and v[2]]
        off = [(tk, v) for tk, v in both if abs(v[0] / v[2] - 1) > 0.005]
        self.assertEqual(off, [], "the upside divides by the latest adj close; it must equal today's traded close")
        self.assertGreater(len(both), 0)


if __name__ == "__main__":
    unittest.main()

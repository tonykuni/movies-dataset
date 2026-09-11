import assert from "node:assert/strict";
import { test } from "node:test";
import {
  classifyTwAll,
  classifyTwRx,
  completeEtfSuffix,
  deriveTw,
  inActiveEquityRange,
  isActiveDomesticEquityEtf,
  runTwRxSelftest,
  rxHits,
  TW_RX_REGISTRY,
  TW_TICKER,
  TW_TICKER_DORMANT,
  twRxQc,
} from "./tw-ticker-all.ts";

test("stock three forms stay first-digit-nonzero four digits", () => {
  const a = classifyTwAll("2330");
  const b = classifyTwAll("2330.TW");
  const c = classifyTwAll("2330 TT");
  assert.equal(a?.kind, "Stock");
  assert.equal(b?.yfinance, "2330.TW");
  assert.equal(c?.bloomberg, "2330 TT");
  assert.equal(classifyTwAll("0330"), null);
  assert.equal(TW_TICKER.Stock.test("0050"), false);
});

test("ETF suffix families and 00980 completes to 00980A in active range", () => {
  assert.equal(classifyTwAll("00980A")?.kind, "ActiveEquityETF");
  assert.equal(classifyTwAll("00982D")?.kind, "ActiveBondETF");
  assert.equal(classifyTwAll("00878")?.kind, "PassiveEquityETF");
  assert.equal(classifyTwAll("0050")?.kind, "PassiveEquityETF4");
  assert.equal(classifyTwAll("00631L")?.kind, "LeverageETF");
  const p = completeEtfSuffix("00980");
  assert.equal(p.completed, "00980A");
  assert.equal(p.kind, "ActiveEquityETF");
  assert.ok(p.candidates.includes("00980B"));
  assert.equal(completeEtfSuffix("00878").completed, null);
});

test("active domestic equity ETF needs A plus 00400A-00499A or 00980A-00999A", () => {
  assert.equal(inActiveEquityRange("00980A"), true);
  assert.equal(inActiveEquityRange("00403A"), true);
  assert.equal(inActiveEquityRange("00950A"), false);
  assert.equal(isActiveDomesticEquityEtf("00980A"), true);
  assert.equal(isActiveDomesticEquityEtf("00980A", { region: "Foreign" }), false);
  assert.equal(isActiveDomesticEquityEtf("00982D"), false);
  assert.equal(classifyTwAll("00980A.TW")?.yfinance, "00980A.TW");
  assert.equal(classifyTwAll("00980A TT")?.bloomberg, "00980A TT");
});

test("v0100 registry: preferred, FX suffix, 6-digit passive, dormant 5-code", () => {
  assert.equal(TW_RX_REGISTRY.length, 13);
  assert.equal(classifyTwRx("2881A")?.cls, "PREFERRED");
  assert.equal(classifyTwRx("2882B.TW")?.venue, "TW");
  assert.equal(classifyTwRx("00679C")?.cls, "ETF_BOND_FX");
  assert.equal(classifyTwRx("00663M")?.cls, "ETF_LEVERAGE_FX");
  assert.equal(classifyTwRx("00664S")?.cls, "ETF_REVERSE_FX");
  assert.equal(classifyTwRx("00643K")?.cls, "ETF_PASSIVE_FX");
  assert.equal(classifyTwRx("0050")?.cls, "ETF_PASSIVE");
  assert.equal(classifyTwRx("006208")?.cls, "ETF_PASSIVE");
  assert.equal(classifyTwRx("009800")?.cls, "ETF_PASSIVE");
  assert.equal(classifyTwRx("004001")?.cls, "ETF_PASSIVE");
  assert.equal(classifyTwRx("009800 TT")?.fmt, "BBG");
  assert.equal(classifyTwAll("009800")?.kind, "PassiveEquityETFv2");
  assert.equal(classifyTwAll("006208.TW")?.yfinance, "006208.TW");
  assert.equal(TW_TICKER_DORMANT.PassiveEquityETF.test("0050"), false);
  assert.equal(TW_TICKER_DORMANT.PassiveEquityETF.test("006208"), false);
  assert.equal(TW_TICKER_DORMANT.PassiveEquityETF.test("00878"), true);
  assert.equal(classifyTwRx("00981a"), null);
  assert.equal(classifyTwRx("2330TT"), null);
  assert.equal(classifyTwRx("00980X"), null);
  assert.equal(rxHits("00981A").join(","), "ETF_ACTIVE");
  const d = deriveTw("6488", "TWO");
  assert.equal(classifyTwRx(d.yfinance)?.venue, "TWO");
});

test("attachment selftest 75/75 and QC lights", () => {
  const st = runTwRxSelftest();
  assert.equal(st.all, 75);
  assert.equal(st.pass, 75);
  assert.equal(st.ok, true);
  const fail = st.rows.filter((r) => !r.pass);
  assert.deepEqual(fail, []);
  const qc = twRxQc();
  assert.equal(qc.filter((r) => r.light === "bad").length, 0);
  assert.equal(completeEtfSuffix("009800").kind, "PassiveEquityETFv2");
  assert.ok(completeEtfSuffix("00980").candidates.includes("00980C"));
});

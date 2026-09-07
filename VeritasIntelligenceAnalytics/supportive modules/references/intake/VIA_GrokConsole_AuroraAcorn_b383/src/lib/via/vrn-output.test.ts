import assert from "node:assert/strict";
import { test } from "node:test";
import { FOLDER_SEEDS } from "./catalog.ts";
import { completeVrn, vrnReady } from "./complete-vrn.ts";
import { MOTHER_INCOMING } from "./incoming-roster.ts";
import { incomingText } from "./incoming.ts";
import { extractFacts } from "./nlp-extract.ts";
import { packBasic, packFinance, packSummary, parseFilename, validationRisk } from "./vrn.ts";
import { runVrnToEnd } from "./vrn-end.ts";

test("VRN output values: 2330 facts, 2637 date, R11, no seal without tests", () => {
  const facts = extractFacts(incomingText("GS-2330 台積電_20251130.pdf"));
  const rev = facts.find((f) => f.dataName === "revenue");
  assert.equal(rev?.value, 2894.3);
  assert.equal(facts.find((f) => f.dataName === "eps")?.value, 45.25);
  assert.equal(facts.find((f) => f.dataName === "ocf")?.value, 1820.4);

  const gs = parseFilename("GS-2330 台積電_20251130.pdf");
  assert.equal(gs.ticker, "2330");
  assert.equal(gs.yfinance, "2330.TW");
  assert.equal(gs.reportDate, "2025-11-30");

  const hy = parseFilename("華南投顧-2637-慧洋-KY-1141202.pdf");
  assert.equal(hy.ticker, "2637");
  assert.equal(hy.reportDate, "2025-12-02");
  assert.equal(packFinance({ id: "h", name: hy.ticker + ".pdf", ext: "pdf", size: 1, lastModified: 0, origin: "folder", skipDup: false, fingerprint: "x", status: "ok", stuckStep: null, stuckDetail: null, steps: {} }, hy, "ok").length, 0);

  const gsFile = FOLDER_SEEDS.find((f) => f.name.startsWith("GS-2330"))!;
  const sums = packSummary(gsFile, parseFilename(gsFile.name));
  const by = Object.fromEntries(sums.map((s) => [s.slot, s]));
  assert.equal(by.headline?.grounded, true);
  assert.equal(by.K1?.grounded, true);
  assert.match(by.K1?.bullet ?? "", /20\.8%/);
  assert.match(by.K1?.bullet ?? "", /1450/);
  assert.match(by.K1?.bullet ?? "", /1200/);
  assert.equal(by.K2?.grounded, true);
  assert.match(by.K2?.bullet ?? "", /2024 45.25/);
  assert.match(by.K2?.bullet ?? "", /2027 70/);
  assert.equal(by.K3?.grounded, true);
  assert.equal(by.K4?.grounded, true);
  assert.equal(by.K5?.grounded, false);
  const ghost = packSummary(
    { ...gsFile, name: "華南投顧-2637-慧洋-KY-1141202.pdf", text: undefined },
    hy,
  );
  const g1 = ghost.find((s) => s.slot === "K1");
  assert.equal(g1?.grounded, true);
  assert.match(g1?.bullet ?? "", /7\.7%/);
  assert.match(g1?.bullet ?? "", /VRN_SSOT/);
  assert.equal(ghost.filter((s) => s.slot !== "K1").every((s) => s.grounded === false), true);

  let g = 0;
  for (const name of MOTHER_INCOMING) {
    const ext = name.split(".").pop() ?? "";
    if (validationRisk({ status: "ok", name, ext, size: 80_000 }, parseFilename(name)) === "GREEN") g += 1;
  }
  assert.equal(g, 41);

  const files = FOLDER_SEEDS.map((f) => ({
    ...f,
    status: f.size === 0 ? ("bad" as const) : ("ok" as const),
    stuckStep: f.size === 0 ? "S04" : null,
  }));
  const pass = files.filter((f) => f.status !== "bad" && !(f.skipDup && f.dupOf));
  const basics = pass.map((f) => packBasic(f, parseFilename(f.name), "ok"));
  const summaries = pass.flatMap((f) => packSummary(f, parseFilename(f.name)));
  const finances = pass.flatMap((f) => packFinance(f, parseFilename(f.name), "ok"));
  const ended = runVrnToEnd({ files, basics, summaries, finances, confirmNlp: false });
  assert.equal(ended.fail, 0);
  assert.match(ended.steps.find((s) => s.id === "R11")?.out ?? "", /進件實測通過/);
  assert.equal(ended.steps.find((s) => s.id === "R09")?.result, "SKIP");
  assert.ok(finances.some((r) => r.dataName === "revenue" && r.value === 2894.3));
  assert.ok(!finances.some((r) => r.fileName.includes("2637")));

  assert.equal(vrnReady(false).ok, true);
  assert.equal(completeVrn({ testsPass: false }).seal.light, "warn");
  assert.equal(completeVrn({ testsPass: true }).seal.light, "ok");
});

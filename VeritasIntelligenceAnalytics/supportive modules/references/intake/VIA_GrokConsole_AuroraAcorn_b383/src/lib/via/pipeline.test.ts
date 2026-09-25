import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { decideStep, fingerprint, guessTicker, guessType, statusFromSteps } from "./pipeline.ts";

describe("fingerprint", () => {
  it("matches format + size", () => {
    assert.equal(fingerprint("csv", 128440), fingerprint("csv", 128440));
    assert.notEqual(fingerprint("csv", 128440), fingerprint("pdf", 128440));
  });
});

describe("decideStep", () => {
  const base = { name: "a.pdf", ext: "pdf", size: 100, skipDup: false as const };

  it("skips remaining after dup gate", () => {
    const hit = decideStep({ ...base, ext: "csv", skipDup: true, dupOf: "orig.csv" }, "S03", false);
    assert.equal(hit.light, "warn");
    assert.equal(hit.skipRest, true);
    const later = decideStep(base, "S07", true);
    assert.equal(later.light, "idle");
  });

  it("rejects empty and unknown ext at S04", () => {
    const empty = decideStep({ ...base, ext: "tmp", size: 0 }, "S04", false);
    assert.equal(empty.aborted, true);
    const bad = decideStep({ ...base, ext: "tmp", size: 12 }, "S04", false);
    assert.equal(bad.aborted, true);
    const okMd = decideStep({ ...base, ext: "md", name: "note.md" }, "S04", false);
    assert.equal(okMd.light, "ok");
    const okPptx = decideStep({ ...base, ext: "pptx", name: "deck.pptx" }, "S04", false);
    assert.equal(okPptx.light, "ok");
  });

  it("warns scan at OCR route", () => {
    const d = decideStep({ ...base, name: "broker_scan_note.pdf" }, "S06", false);
    assert.equal(d.light, "warn");
    assert.equal(d.aborted, false);
  });
});

describe("statusFromSteps", () => {
  it("keeps warn after later ok steps", () => {
    const steps = { S01: "ok", S06: "warn", S07: "ok" } as const;
    assert.equal(statusFromSteps(steps, false, false, false), "warn");
    assert.equal(statusFromSteps(steps, true, false, false), "bad");
  });
});

describe("guessers", () => {
  it("maps TSMC and holdings", () => {
    assert.equal(guessTicker("台積電_2024Q4.pdf"), "2330.TW");
    assert.equal(guessType("0050_holdings.csv", "csv"), "holdings");
  });
});

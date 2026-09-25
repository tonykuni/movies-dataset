import assert from "node:assert/strict";
import { test } from "node:test";
import { KNOWLEDGE_SOURCES, YEAR_SUSPECT, classifyRating, matchBroker } from "./knowledge.ts";
import { parseFilename } from "./vrn.ts";

test("twelve mother knowledge files registered", () => {
  assert.equal(KNOWLEDGE_SOURCES.length, 12);
});

test("GS-2330 uses broker dict + year not ticker", () => {
  const hit = matchBroker("GS-2330 台積電_20251130.pdf");
  assert.equal(hit?.abbr, "GS");
  const p = parseFilename("GS-2330 台積電_20251130.pdf");
  assert.equal(p.broker, "Goldman Sachs");
  assert.equal(p.ticker, "2330");
  assert.equal(YEAR_SUSPECT.test("2025"), true);
  assert.equal(parseFilename("review_2024_notes.pdf").ticker, "");
});

test("rating dict maps 買進", () => {
  const r = classifyRating("買進 台積電");
  assert.equal(r?.cat, "buy");
});

test("mainland brokers not matched; TW 中信 kept", () => {
  assert.equal(matchBroker("廣發證券-2330.pdf"), null);
  assert.equal(matchBroker("中信證券_2330.pdf"), null);
  assert.equal(matchBroker("國泰君安_2330.pdf"), null);
  assert.equal(matchBroker("中信投顧_2330.pdf")?.abbr, "CTBC");
});

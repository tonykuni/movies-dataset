import assert from "node:assert/strict";
import { test } from "node:test";
import { periodKey, resampleLast } from "./freq.ts";

test("resample takes last of month, does not interpolate", () => {
  const out = resampleLast(
    [
      { date: "2024-01-15", value: 1 },
      { date: "2024-01-31", value: 2 },
      { date: "2024-02-10", value: 3 },
    ],
    "M",
  );
  assert.equal(out.length, 2);
  assert.equal(out[0]?.value, 2);
  assert.equal(out[1]?.value, 3);
  assert.equal(periodKey("2024-05-20", "Q"), "2024-Q2");
  assert.equal(periodKey("2024-12-01", "A"), "2024");
});

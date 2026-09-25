import assert from "node:assert/strict";
import test from "node:test";
import { MOTHER_STATUS_ROWS, motherStatusLight, motherStatusOpen, motherStatusSummary } from "./mother-status.ts";

test("母倉狀況列:id 唯一且欄位齊", () => {
  const ids = MOTHER_STATUS_ROWS.map((r) => r.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const r of MOTHER_STATUS_ROWS) {
    assert.ok(r.batch.startsWith("批"));
    assert.ok(r.title.length > 0 && r.note.length > 0 && r.metric.length > 0);
  }
});

test("總燈不取巧:有未了結就不能是 ok", () => {
  assert.equal(motherStatusLight(), "warn");
  assert.equal(motherStatusLight([{ ...MOTHER_STATUS_ROWS[0]!, light: "ok" }]), "ok");
  assert.equal(motherStatusLight([{ ...MOTHER_STATUS_ROWS[0]!, light: "bad" }]), "bad");
});

test("未了結列列得出來(ETF 覆蓋 3/23 與 VRN 缺真報告)", () => {
  const open = motherStatusOpen().map((r) => r.id);
  assert.ok(open.includes("ETF_COVER"));
  assert.ok(open.includes("VRN_INPUT"));
  const s = motherStatusSummary();
  assert.equal(s.total, MOTHER_STATUS_ROWS.length);
  assert.equal(s.ok + s.open, s.total);
});

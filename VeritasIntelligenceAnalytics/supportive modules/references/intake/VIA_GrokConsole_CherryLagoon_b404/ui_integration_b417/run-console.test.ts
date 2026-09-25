import assert from "node:assert/strict";
import test from "node:test";
import {
  canRunAll,
  familyLight,
  overallLight,
  readiness,
  resultRows,
  verdictText,
  worstLight,
  type RunCounts,
} from "./run-console.ts";

const INPUT = { startYear: 2015, confirmNet: false, fredKey: "", etfPicked: [], vrnFiles: 0 };
const ZERO: RunCounts = {
  fredRows: 0, laneResults: 0, laneLive: 0, etfRows: 0, etfPicked: 0,
  vrnFiles: 0, vrnBasics: 0, vrnSummaries: 0, vrnFinances: 0, vrnBad: 0,
};
const IDLE = { vdf: false, vrn: false };

test("最壞燈:空=pending;bad 壓過一切;全 ok 才 ok", () => {
  assert.equal(worstLight([]), "pending");
  assert.equal(worstLight(["ok", "bad", "warn"]), "bad");
  assert.equal(worstLight(["ok", "run", "warn"]), "run");
  assert.equal(worstLight(["ok", "warn", "pending"]), "warn");
  assert.equal(worstLight(["ok", "idle"]), "pending");
  assert.equal(worstLight(["ok", "ok"]), "ok");
});

test("整備:VRN 沒檔案就是不能跑,且說得出差什麼", () => {
  const r = readiness(INPUT);
  assert.equal(r.length, 3);
  const vrn = r.find((x) => x.family === "VRN")!;
  assert.equal(vrn.ready, false);
  assert.match(vrn.why, /尚無報告檔/);
  assert.equal(canRunAll(INPUT), false);
  assert.equal(canRunAll({ ...INPUT, vrnFiles: 2 }), true);
});

test("整備:網閘三態各自講白,不含糊", () => {
  const off = readiness(INPUT).find((x) => x.family === "VDF")!.why;
  const noKey = readiness({ ...INPUT, confirmNet: true }).find((x) => x.family === "VDF")!.why;
  const live = readiness({ ...INPUT, confirmNet: true, fredKey: "k" }).find((x) => x.family === "VDF")!.why;
  assert.match(off, /零外呼/);
  assert.match(noKey, /KEY 空/);
  assert.match(live, /可 LIVE/);
});

test("沒跑過一律 pending,總燈不得是 ok", () => {
  const rows = resultRows(ZERO, IDLE);
  assert.ok(rows.length >= 6);
  assert.ok(rows.every((r) => r.light === "pending"));
  assert.equal(overallLight(rows), "pending");
  assert.match(verdictText(rows), /尚未跑/);
});

test("跑完但零列=warn,不當成功", () => {
  const ran: RunCounts = { ...ZERO, laneResults: 4, laneLive: 0, fredRows: 0, vrnFiles: 1 };
  const rows = resultRows(ran, IDLE);
  assert.equal(familyLight(rows, "VDF"), "warn");
  assert.equal(overallLight(rows), "warn");
  assert.match(verdictText(rows), /零列/);
});

test("三族都有料才是 ok;有卡住的件即 bad 且列得出來", () => {
  const good: RunCounts = {
    fredRows: 12, laneResults: 4, laneLive: 4, etfRows: 9, etfPicked: 2,
    vrnFiles: 2, vrnBasics: 2, vrnSummaries: 8, vrnFinances: 6, vrnBad: 0,
  };
  const rows = resultRows(good, IDLE);
  assert.equal(overallLight(rows), "ok");
  assert.match(verdictText(rows), /全數有料/);
  const stuck = resultRows({ ...good, vrnBad: 1 }, IDLE);
  assert.equal(overallLight(stuck), "bad");
  assert.ok(stuck.some((r) => r.key === "卡住的件"));
});

test("busy 期間一律 run(不讓上一輪的數字冒充本輪)", () => {
  const rows = resultRows({ ...ZERO, fredRows: 5, laneResults: 2, laneLive: 2 }, { vdf: true, vrn: false });
  assert.ok(rows.filter((r) => r.family === "VDF").every((r) => r.light === "run"));
  assert.equal(overallLight(rows), "run");
  assert.equal(verdictText(rows), "跑動中");
});

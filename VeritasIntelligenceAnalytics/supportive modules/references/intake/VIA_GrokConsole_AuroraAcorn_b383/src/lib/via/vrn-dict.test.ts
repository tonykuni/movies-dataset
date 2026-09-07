import assert from "node:assert/strict";
import { test } from "node:test";
import { VRN_ANN_N } from "./vrn-annual-cache.ts";
import { VRN_BROKER_N } from "./vrn-broker-cache.ts";
import {
  vrnAbbrCollisions,
  vrnAnnByBlock,
  vrnBrokerLookup,
  vrnDictNote,
  vrnDictQc,
  vrnDropped,
  vrnExtTw,
  vrnFcfNote,
} from "./vrn-dict.ts";

test("broker split: GS=高盛, DH=大華, MS/大摩, JPM/小摩, 摩根 dropped", () => {
  assert.equal(VRN_BROKER_N, 29);
  assert.equal(vrnBrokerLookup("Yuanta")?.abbr, "YT");
  assert.equal(vrnBrokerLookup("GS")?.zh, "高盛");
  assert.equal(vrnBrokerLookup("大華")?.abbr, "DH");
  assert.equal(vrnBrokerLookup("大摩")?.abbr, "MS");
  assert.equal(vrnBrokerLookup("小摩")?.abbr, "JPM");
  assert.equal(vrnBrokerLookup("摩根士丹利")?.abbr, "MS");
  assert.equal(vrnBrokerLookup("摩根大通")?.abbr, "JPM");
  assert.equal(vrnBrokerLookup("摩根"), null);
  assert.equal(vrnDropped("摩根"), true);
  assert.equal(vrnAbbrCollisions().length, 0);
  assert.ok(vrnExtTw().includes("元大證券"));
});

test("mainland brokers dropped; TW 中信/國泰 kept", () => {
  assert.equal(vrnBrokerLookup("中信")?.abbr, "CTBC");
  assert.equal(vrnBrokerLookup("中信證券"), null);
  assert.equal(vrnBrokerLookup("國泰")?.abbr, "CT");
  assert.equal(vrnBrokerLookup("國泰君安"), null);
  assert.equal(vrnBrokerLookup("廣發"), null);
  assert.equal(vrnBrokerLookup("中金"), null);
  assert.equal(vrnBrokerLookup("海通"), null);
});

test("annual 79, FCF uses CFO+CapEx, BVPS parent equity", () => {
  assert.equal(VRN_ANN_N, 79);
  const b = vrnAnnByBlock();
  assert.equal(b.IS, 9);
  assert.match(vrnFcfNote(), /CFO/);
  const q = vrnDictQc();
  assert.equal(q.filter((r) => r.light === "bad").length, 0);
  assert.equal(q.find((r) => r.id === "D_GS")?.light, "ok");
  assert.equal(q.find((r) => r.id === "D_MS")?.light, "ok");
  assert.equal(q.find((r) => r.id === "D_JPM")?.light, "ok");
  assert.equal(q.find((r) => r.id === "D_MAN")?.light, "warn");
  assert.match(vrnDictNote(), /摩根已刪/);
});

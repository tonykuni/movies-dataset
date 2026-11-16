import type { Reading } from "./engine";
import type { VqgDef } from "./registry";
import type { SignalDef } from "./signals";
import type { TestRow } from "./test-engine";

export type VersionNote = {
  id: string;
  name: string;
  version: number;
  status: "新增" | "沿用" | "衝突";
  detail: string;
};

export type VqgPayload = {
  asOf: string;
  barCount: number;
  flowDays: number;
  policy: string[];
  files: { indicators: string; bars: string; readings: string; signals: string; tests: string; versions: string };
  themes: Array<{ theme: string; indicators: number; filled: number; summary: string }>;
  registry: VqgDef[];
  readings: Reading[];
  counts: Array<{ theme: string; indicators: number; filled: number }>;
  signals: SignalDef[];
  tests: TestRow[];
  versions: VersionNote[];
};
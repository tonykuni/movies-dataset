import definition from "../../../data/via/parameter-definition.json" with { type: "json" };

export type SignalDef = {
  id: string;
  indicatorId: string;
  name: string;
  meaning: string;
  testQuestion: string;
  evidenceRule: string;
  noiseRule: string;
  saturationRule: string;
};

export const SIGNALS = definition.signals as SignalDef[];

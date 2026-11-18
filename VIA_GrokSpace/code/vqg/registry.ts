import definition from "../../../data/via/parameter-definition.json" with { type: "json" };

export type SolutionDef = {
  id: string;
  unit: string;
  method: string;
  blank: string;
};

export type VqgDef = {
  id: string;
  category: string;
  theme: string;
  name: string;
  naming: "正式" | "自訂";
  version: number;
  changeNote: string;
  formula: string;
  params: Record<string, number>;
  windows: number[];
  inputs: string[];
  solutions: SolutionDef[];
  evidence: string;
  purpose: string;
  advantage: string;
  disadvantage: string;
  upgrade: string;
  signalRule: string;
  tvRef: string;
  updatedOn: string;
};

export const PARAMETER_ID = definition.id;
export const ENGINE_ID = definition.engine;
export const VQG = definition.indicators as VqgDef[];
export const THEMES = ["趨勢", "動能", "波動", "成交與法人", "風險", "結構", "可比"] as const;

export type TopicDef = {
  id: string;
  name: string;
  question: string;
  reads: string[];
  rule: string;
  version: number;
};

export type LibDef = {
  id: string;
  package: string;
  license: string;
  role: string;
  expands: string;
};

export const TOPICS = definition.topics as TopicDef[];
export const LIBRARIES = definition.libraries as LibDef[];
export const FRESH_IDS = [
  "VIA-VQG-TA-TRD006",
  "VIA-VQG-TA-TRD007",
  "VIA-VQG-TA-TRD008",
  "VIA-VQG-TA-TRD009",
  "VIA-VQG-TA-TRD010",
  "VIA-VQG-TA-MOM008",
  "VIA-VQG-TA-MOM009",
  "VIA-VQG-TA-MOM010",
  "VIA-VQG-TA-MOM011",
  "VIA-VQG-TA-MOM012",
  "VIA-VQG-TA-VOL007",
  "VIA-VQG-TA-VOL008",
  "VIA-VQG-TA-VOL009",
  "VIA-VQG-TA-VOL010",
  "VIA-VQG-TA-RSK009",
  "VIA-VQG-TA-RSK010",
  "VIA-VQG-TA-RSK011",
  "VIA-VQG-TA-STA006",
  "VIA-VQG-TA-STA007",
  "VIA-VQG-TA-STA008",
] as const;

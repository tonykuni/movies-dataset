import definition from "../../../data/via/parameter-definition.json" with { type: "json" };

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
export const THEMES = ["趨勢", "動能", "波動", "成交與法人", "風險", "可比"] as const;

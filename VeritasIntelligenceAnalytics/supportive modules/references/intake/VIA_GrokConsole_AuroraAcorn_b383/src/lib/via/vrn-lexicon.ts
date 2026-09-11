/** Lexicon fill 候審。只填空 en，不改 id/zh。操作員 --merge 才生效。 */
export const VRN_LEX_MERGE = false;

export type LexFill = { node: string; zh: string; en: string };

/** K6 產業族群空英欄 · 專業財經對譯 */
export const VRN_LEX_FILLS: LexFill[] = [
  { node: "K6.1", zh: "記憶體", en: "Memory" },
  { node: "K6.2", zh: "CPO", en: "Co-Packaged Optics" },
  { node: "K6.3", zh: "金融", en: "Financials" },
  { node: "K6.4", zh: "半導體", en: "Semiconductors" },
  { node: "K6.5", zh: "AI 伺服器", en: "AI Servers" },
  { node: "K6.6", zh: "散熱", en: "Thermal Management" },
  { node: "K6.7", zh: "軍工", en: "Defense" },
  { node: "K6.8", zh: "散裝航運", en: "Dry Bulk Shipping" },
  { node: "K6.9", zh: "PCB", en: "PCB" },
  { node: "K6.10", zh: "航太", en: "Aerospace" },
  { node: "K6.11", zh: "無人機", en: "UAV" },
  { node: "K6.12", zh: "觀光", en: "Tourism" },
  { node: "K6.13", zh: "能源", en: "Energy" },
  { node: "K6.14", zh: "電動車", en: "Electric Vehicles" },
];

export const VRN_EBIT_ZH_CANDIDATE = { id: "ebit", zh: "稅前息前盈餘", en: "EBIT" };

export function lexFillOk(): boolean {
  return VRN_LEX_FILLS.length === 14 && VRN_LEX_FILLS.every((r) => r.zh && r.en && r.node.startsWith("K6."));
}

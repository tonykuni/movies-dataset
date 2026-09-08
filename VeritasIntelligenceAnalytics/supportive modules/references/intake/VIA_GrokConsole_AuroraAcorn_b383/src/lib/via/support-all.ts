/** 三套支援引擎：Markdown 編輯、語意插件、全格式。本台無 Downloads 原件，契約＋CACHE。NLP 閘關不外呼。 */
export const SUPPORT_LIVE = false;

export const MDE = {
  id: "VRN_ENG_MDE",
  name: "MarkdownEditingEngine",
  version: "v1.2.0",
  path: "C:\\Users\\tonyk\\Downloads\\MarkdownEditingEngine_v1.2.0_FINAL",
  ext: ["md", "markdown", "mdx", "txt", "rst"],
} as const;

export const USIP = {
  id: "VRN_ENG_USIP",
  name: "Universal Semantic Intelligence Plugin",
  version: "v0100",
  path: "C:\\Users\\tonyk\\Downloads\\Veritas_Universal_Semantic_Intelligence_Plugin_Engine_v0100_FINAL\\Veritas_Universal_Semantic_Intelligence_Plugin_Engine_v0100",
} as const;

export const OFIE = {
  id: "VRN_ENG_OFIE",
  name: "OmniFormat Intelligence Engine",
  version: "v0140",
  path: "C:\\Users\\tonyk\\Downloads\\Veritas_OmniFormat_Intelligence_Engine_v0140_FINAL (1)\\Veritas_OmniFormat_Intelligence_Engine_v0140",
  ext: [
    "pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "html", "htm",
    "md", "txt", "csv", "json", "xml", "rtf", "odt", "ods", "odp", "epub",
  ],
} as const;

const REJECT = new Set(["tmp", "exe", "dll", "bat", "ps1", "lnk"]);

export function ofieAccepts(ext: string): boolean {
  const e = ext.toLowerCase().replace(/^\./, "");
  if (REJECT.has(e)) return false;
  return (OFIE.ext as readonly string[]).includes(e);
}

export function mdeAccepts(ext: string): boolean {
  const e = ext.toLowerCase().replace(/^\./, "");
  return (MDE.ext as readonly string[]).includes(e);
}

export function supportStack(ext: string): { ofie: boolean; mde: boolean; usip: boolean; note: string } {
  const ofie = ofieAccepts(ext);
  const mde = mdeAccepts(ext);
  const usip = ofie;
  const note = !ofie
    ? `OFIE 拒 ${ext}`
    : SUPPORT_LIVE
      ? `OFIE ${OFIE.version}${mde ? " · MDE" : ""} · USIP`
      : `CACHE 契約 · OFIE/MDE/USIP 未讀 Downloads 原件 · 閘關`;
  return { ofie, mde, usip, note };
}

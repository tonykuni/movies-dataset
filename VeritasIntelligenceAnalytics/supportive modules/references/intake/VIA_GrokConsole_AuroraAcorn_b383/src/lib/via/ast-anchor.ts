/** Precision vs elastic AST anchors. DCT01–20 stay sealed. No writes into L/C/V lakes. */
import type { Light } from "./types.ts";

export type SourceKind = "py" | "ts" | "ps1" | "html" | "json" | "md";
export type AstMode = "precision" | "elastic";
export type FixKind = "parallel" | "sequence";

export const DCT_SEALED = true;

export function astMode(kind: SourceKind): AstMode {
  return kind === "py" || kind === "ts" ? "precision" : "elastic";
}

export const AST_ANCHORS = [
  { mode: "precision" as const, tool: "ast.parse + lineno/col", kinds: "py/ts", sees: "節點座標／Call／Name ctx", misses: "編碼、動態 getattr" },
  { mode: "elastic" as const, tool: "regex + 語意錨", kinds: "ps1/html/json", sees: "指令區塊／函式名", misses: "完整 scope" },
] as const;

export function classifyFix(deps: string[]): FixKind {
  return deps.length ? "sequence" : "parallel";
}

export function astCloseNote(): { light: Light; note: string } {
  const prec = AST_ANCHORS.filter((a) => a.mode === "precision").length;
  const elas = AST_ANCHORS.filter((a) => a.mode === "elastic").length;
  return {
    light: DCT_SEALED && prec === 1 && elas === 1 ? "ok" : "bad",
    note: `精準 ${prec} · 彈性 ${elas} · DCT ${DCT_SEALED ? "封印不重做" : "未封"}`,
  };
}

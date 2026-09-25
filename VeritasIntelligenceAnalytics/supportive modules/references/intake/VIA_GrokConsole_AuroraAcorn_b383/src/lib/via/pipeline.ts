import { ofieAccepts } from "./support-all.ts";
import type { IntakeFile, Light } from "./types.ts";
import { extractTicker, guessType as vrnGuessType } from "./vrn.ts";

export const ALLOWED_EXT = new Set(["pdf", "xlsx", "xls", "csv", "docx", "md", "pptx", "html", "txt"]);

export function fingerprint(ext: string, size: number): string {
  return `${ext}:${size}`;
}

export function guessTicker(name: string): string {
  const t = extractTicker(name);
  return t ? `${t}.TW` : "—";
}

export function guessType(name: string, ext: string): string {
  return vrnGuessType(name, ext);
}

export type StepDecision = {
  light: Light;
  skipRest: boolean;
  aborted: boolean;
  stuck: string | null;
  detail: string | null;
};

export function decideStep(
  file: Pick<IntakeFile, "name" | "ext" | "size" | "skipDup" | "dupOf">,
  stepId: string,
  skipRest: boolean,
): StepDecision {
  if (skipRest) {
    return { light: "idle", skipRest: true, aborted: false, stuck: null, detail: null };
  }
  if (file.skipDup && file.dupOf && stepId === "S03") {
    return {
      light: "warn",
      skipRest: true,
      aborted: false,
      stuck: stepId,
      detail: `去重命中 · 格式 ${file.ext} 大小 ${file.size} 與 ${file.dupOf} 相同`,
    };
  }
  if (file.size === 0 && stepId === "S04") {
    return {
      light: "bad",
      skipRest: false,
      aborted: true,
      stuck: stepId,
      detail: "零位元組 · 格式分類拒絕",
    };
  }
  if (!ofieAccepts(file.ext) && stepId === "S04") {
    return {
      light: "bad",
      skipRest: false,
      aborted: true,
      stuck: stepId,
      detail: `副檔名 .${file.ext} 不在允許清單`,
    };
  }
  if (file.name.includes("scan") && stepId === "S06") {
    return { light: "warn", skipRest: false, aborted: false, stuck: null, detail: null };
  }
  return { light: "ok", skipRest: false, aborted: false, stuck: null, detail: null };
}

export function statusFromSteps(
  steps: Record<string, Light>,
  aborted: boolean,
  skipRest: boolean,
  running: boolean,
): Light {
  if (aborted) return "bad";
  if (skipRest) return "warn";
  const lights = Object.values(steps);
  if (lights.includes("bad")) return "bad";
  if (lights.includes("warn")) return "warn";
  if (running) return "run";
  const known = Object.keys(steps);
  if (known.length && known.every((k) => steps[k] === "ok" || steps[k] === "warn" || steps[k] === "idle")) {
    if (Object.values(steps).some((v) => v === "ok" || v === "warn") && !Object.values(steps).includes("idle")) return "ok";
  }
  return "idle";
}

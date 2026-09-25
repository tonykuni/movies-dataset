import { ACCEL_TOOLS, GOV_TOOLS, NET_TOOLS, NLP_TOOLS } from "./catalog";
import type { Light, MountedTool, ToolKind } from "./types";

export const TOOL_BUS: MountedTool[] = [...ACCEL_TOOLS, ...NET_TOOLS, ...NLP_TOOLS, ...GOV_TOOLS];

export function patchTools(
  tools: MountedTool[],
  match: (t: MountedTool) => boolean,
  status: Light,
): MountedTool[] {
  return tools.map((t) => (match(t) ? { ...t, status } : t));
}

export function byKinds(kinds: ToolKind[]) {
  return (t: MountedTool) => kinds.includes(t.kind);
}

export function countOk(tools: MountedTool[], kind: ToolKind): number {
  return tools.filter((t) => t.kind === kind && t.status === "ok").length;
}

export function countKind(tools: MountedTool[], kind: ToolKind): number {
  return tools.filter((t) => t.kind === kind).length;
}

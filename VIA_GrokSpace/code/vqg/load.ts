import { createServerFn } from "@tanstack/react-start";
import type { VqgPayload } from "./types";

export type { VqgPayload } from "./types";

export const loadVqg = createServerFn({ method: "GET" }).handler(async (): Promise<VqgPayload> => {
  const { buildVqg } = await import("./build.server");
  return buildVqg();
});

/** VAP Router：總管路由 VIA／VDF／VRN，不寫資料湖、不開 LIVE、不重做 DCT。 */
import { REGISTERED_ENGINES } from "./catalog.ts";
import { applySsot, liveEngines } from "./inventory.ts";
import type { Light } from "./types.ts";
import type { Seal } from "./seal.ts";

export const VAP_ID = "VAP_MDL001";
export const VAP_WRITE = "vap-route";

const ROUTES = [
  { to: "VIA_CGC", job: "CONSOLE" },
  { to: "VDF_FETCH", job: "VDF" },
  { to: "VRN_REP", job: "VRN" },
] as const;

export function vapHydraOk(writes: string[] = []): boolean {
  return !writes.includes(VAP_WRITE);
}

export function vapReady(): { ok: boolean; light: Light; note: string } {
  const live = liveEngines(applySsot(REGISTERED_ENGINES));
  const self = live.find((e) => e.id === VAP_ID);
  const missing = ROUTES.filter((r) => !live.some((e) => e.id === r.to)).map((r) => r.to);
  if (!self || self.status === "bad" || !self.ssot || !self.hash) {
    return { ok: false, light: "bad", note: "VAP 未登錄或 SSOT 未完" };
  }
  if (missing.length) return { ok: false, light: "bad", note: `路由缺 ${missing.join(",")}` };
  return {
    ok: true,
    light: "ok",
    note: `VAR 過 · 路由 ${ROUTES.map((r) => r.to).join("/")} · 寫 ${VAP_WRITE} · 不寫湖`,
  };
}

export function sealVap(): Seal {
  const r = vapReady();
  return { id: "VAP", name: "VAP Router", light: r.light, note: r.note };
}

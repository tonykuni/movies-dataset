/** EIA Open Data v2 · KEY 為參數。LIVE 預設關，以後再測。勿與 FRED KEY 混填。 */
export const DEFAULT_EIA_API = "https://api.eia.gov/v2";

/** 未開測：即使 NET＋KEY 齊也零外呼。改 true 才走雙閘 LIVE。 */
export const EIA_LIVE_ENABLED = false;

export function sanitizeEiaApi(raw: string): { ok: true; url: string } | { ok: false; reason: string } {
  const trimmed = (raw || "").trim() || DEFAULT_EIA_API;
  let u: URL;
  try {
    u = new URL(trimmed);
  } catch {
    return { ok: false, reason: "EIA API 非合法 URL" };
  }
  if (u.protocol !== "https:") return { ok: false, reason: "EIA API 僅允許 https" };
  if (u.hostname !== "api.eia.gov") return { ok: false, reason: "EIA API 僅允許 api.eia.gov" };
  if (u.username || u.password) return { ok: false, reason: "EIA API 禁止內嵌帳密" };
  u.hash = "";
  u.search = "";
  return { ok: true, url: u.toString().replace(/\/$/, "") };
}

export function eiaKeyFormat(raw: string): boolean {
  const k = raw.trim();
  return /^[A-Za-z0-9]{16,64}$/.test(k);
}

/** 三閘：LIVE 旗 × NET × KEY × https。現況 EIA_LIVE_ENABLED=false → 永遠 CACHE。 */
export function canFetchEia(input: {
  confirmNet: boolean;
  apiKey: string;
  apiUrl: string;
}): { ok: true; url: string } | { ok: false; mode: "CACHE" | "DENIED"; reason: string } {
  const held = input.apiKey.trim() ? "KEY 已收" : "KEY 空";
  if (!EIA_LIVE_ENABLED) {
    return { ok: false, mode: "CACHE", reason: `EIA LIVE 未啟用 · ${held} · 以後再測 · 零外呼` };
  }
  if (!input.confirmNet) return { ok: false, mode: "CACHE", reason: "NET 閘未確認 · EIA 零外呼" };
  if (!input.apiKey.trim()) return { ok: false, mode: "CACHE", reason: "EIA KEY 未填 · 參數位保留" };
  if (!eiaKeyFormat(input.apiKey)) return { ok: false, mode: "DENIED", reason: "EIA KEY 格式不符 · 非 FRED 32 hex" };
  const api = sanitizeEiaApi(input.apiUrl);
  if (!api.ok) return { ok: false, mode: "DENIED", reason: `${api.reason} · 不外呼` };
  return { ok: true, url: api.url };
}

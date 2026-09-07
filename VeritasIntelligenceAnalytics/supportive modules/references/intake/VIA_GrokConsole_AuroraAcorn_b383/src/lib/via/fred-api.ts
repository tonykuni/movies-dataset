/** MDL003 PARAM-10 · FRED endpoint 為參數，預設官方觀測 API。 */
export const DEFAULT_FRED_API = "https://api.stlouisfed.org/fred/series/observations";

export function sanitizeFredApi(raw: string): { ok: true; url: string } | { ok: false; reason: string } {
  const trimmed = (raw || "").trim() || DEFAULT_FRED_API;
  let u: URL;
  try {
    u = new URL(trimmed);
  } catch {
    return { ok: false, reason: "FRED API 非合法 URL" };
  }
  if (u.protocol !== "https:") return { ok: false, reason: "FRED API 僅允許 https" };
  if (u.username || u.password) return { ok: false, reason: "FRED API 禁止內嵌帳密" };
  u.hash = "";
  return { ok: true, url: u.toString().replace(/\/$/, "") };
}

export function buildFredObsUrl(api: string, seriesId: string, key: string, start: string, limit = 8): string {
  const u = new URL(api);
  u.searchParams.set("series_id", seriesId);
  u.searchParams.set("api_key", key);
  u.searchParams.set("file_type", "json");
  u.searchParams.set("observation_start", start);
  u.searchParams.set("sort_order", "desc");
  u.searchParams.set("limit", String(Math.min(Math.max(1, limit | 0), 100000)));
  return u.toString();
}

/** 雙閘 AND：政策閘 × KEY × https。任一假則禁止 fetch。 */
export function canFetchFred(input: { confirmNet: boolean; apiKey: string; apiUrl: string }): { ok: true; url: string } | { ok: false; mode: "CACHE" | "DENIED"; reason: string } {
  if (!input.confirmNet) return { ok: false, mode: "CACHE", reason: "NET 閘未確認 · 零外呼" };
  if (!/^[a-f0-9]{32}$/i.test(input.apiKey.trim())) {
    return { ok: false, mode: input.apiKey.trim() ? "DENIED" : "CACHE", reason: input.apiKey.trim() ? "KEY 格式非 32 hex · 快取盤保留" : "FRED KEY 未填 · 列式湖走 VDF 快取盤" };
  }
  const api = sanitizeFredApi(input.apiUrl);
  if (!api.ok) return { ok: false, mode: "DENIED", reason: `${api.reason} · 快取盤保留` };
  return { ok: true, url: api.url };
}
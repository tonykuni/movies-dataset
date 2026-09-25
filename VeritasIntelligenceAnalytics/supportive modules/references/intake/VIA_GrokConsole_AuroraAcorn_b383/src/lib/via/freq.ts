/** FRED 頻率轉換：只取期末，不插值、不發明。 */
export type Freq = "D" | "W" | "M" | "Q" | "A";

export type Pt = { date: string; value: number | null };

export function periodKey(iso: string, freq: Freq): string {
  const y = iso.slice(0, 4);
  const mo = Number(iso.slice(5, 7) || "1");
  if (freq === "A") return y;
  if (freq === "Q") return `${y}-Q${Math.ceil(mo / 3) || 1}`;
  if (freq === "M") return iso.slice(0, 7);
  if (freq === "W") {
    const t = Date.parse(iso);
    if (!Number.isFinite(t)) return iso.slice(0, 10);
    const d = new Date(t);
    const day = (d.getUTCDay() + 6) % 7;
    const thu = new Date(t + (3 - day) * 86400000);
    return thu.toISOString().slice(0, 10);
  }
  return iso.slice(0, 10);
}

/** Last observation in each period. Nulls do not fill. */
export function resampleLast(points: Pt[], freq: Freq): Pt[] {
  const g = new Map<string, Pt>();
  for (const p of points) {
    if (!p.date) continue;
    const k = periodKey(p.date, freq);
    const prev = g.get(k);
    if (!prev || p.date >= prev.date) g.set(k, p);
  }
  return [...g.values()].sort((a, b) => a.date.localeCompare(b.date));
}

export function freqCover(list: Array<{ frequency: string }>): Record<string, number> {
  const out: Record<string, number> = { D: 0, W: 0, M: 0, Q: 0, A: 0, other: 0 };
  for (const r of list) {
    const f = (r.frequency || "").toUpperCase();
    if (f in out && f !== "other") out[f] = (out[f] ?? 0) + 1;
    else out.other = (out.other ?? 0) + 1;
  }
  return out;
}
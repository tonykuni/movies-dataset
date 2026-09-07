/** NumPy 套餐 SSOT。衝突只隔離 via_iso_*，不刪 base，不 conda create 除非同意。 */
import type { Light } from "./types.ts";

export type NpyMeal = {
  id: string;
  meal: string;
  py: string;
  numpy: string;
  tools: string;
  slot: string;
  spawn: "LKGC" | "ISO" | "PLAN" | "NEVER";
  light: Light;
  note: string;
};

/** 對號入座。母機 CPython 3.13 無 1.26 wheel → 1.x 必須獨立 py3.11 槽。 */
export const NPY_MEALS: NpyMeal[] = [
  {
    id: "NPY_VDF",
    meal: "VDF 湖／DuckDB",
    py: "3.11–3.13",
    numpy: "2.1.1",
    tools: "polars 1.9 · duckdb · pyarrow 17 · pandas 新",
    slot: "via_vdf / .venv-via_vdf",
    spawn: "LKGC",
    light: "ok",
    note: "LKGC · 進 PATH",
  },
  {
    id: "NPY_ISO",
    meal: "1.x 黃金過渡",
    py: "3.11",
    numpy: "1.26.4",
    tools: "pandas 2.1 · scipy 1.12 · sklearn 1.4 · torch 2.0–2.2 · TF 2.12–2.15",
    slot: "via_iso_numpy",
    spawn: "ISO",
    light: "ok",
    note: "不進 PATH · 與 2.x ABI 不相容",
  },
  {
    id: "NPY_BASE",
    meal: "base 精簡",
    py: "3.12",
    numpy: "1.26.4",
    tools: "pandas 2.2 · 不裝 TF/torch",
    slot: "base",
    spawn: "LKGC",
    light: "ok",
    note: "base 不混 2.x",
  },
  {
    id: "NPY_LEGACY",
    meal: "2022 前論文／舊 GitHub",
    py: "3.9",
    numpy: "1.23.5",
    tools: "pandas 1.5 · scipy 1.9 · sklearn 1.2 · TF 2.4–2.11",
    slot: "via_iso_numpy_legacy",
    spawn: "PLAN",
    light: "warn",
    note: "未同意不 create",
  },
  {
    id: "NPY_FRONT",
    meal: "最新前沿",
    py: "3.12–3.13",
    numpy: "2.1+",
    tools: "pandas 2.2+ · scipy 1.13+ · sklearn 1.5+ · TF 2.16+ · torch 2.3+",
    slot: "via_vdf",
    spawn: "LKGC",
    light: "ok",
    note: "舊 cython 套件會 ABI mismatch → 改走 ISO 1.x",
  },
  {
    id: "NPY_MUSEUM",
    meal: "NumPy ≤1.6 博物館",
    py: "2.7 / 3.2",
    numpy: "≤1.6",
    tools: "SciPy 0.9 · Pandas 0.7–0.10 · sklearn 0.10 · ArcGIS 10.1 · LabVIEW 舊節點 · Python(x,y)",
    slot: "none",
    spawn: "NEVER",
    light: "ok",
    note: "2026 不裝 · 不編譯 · 改寫或放棄",
  },
];

export function npySlotOf(py: string, need1x: boolean): NpyMeal {
  if (need1x) return NPY_MEALS.find((m) => m.id === "NPY_ISO")!;
  if (/3\.13/.test(py)) return NPY_MEALS.find((m) => m.id === "NPY_VDF")!;
  return NPY_MEALS.find((m) => m.id === "NPY_ISO")!;
}

export function npyPlanNote(): string {
  return "NumPy 1.26.4↔2.1.1 分槽 via_iso_numpy · <1.6 NEVER · 未同意不 conda create";
}

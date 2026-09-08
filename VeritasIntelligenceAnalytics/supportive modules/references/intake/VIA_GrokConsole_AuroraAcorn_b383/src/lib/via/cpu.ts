export type Isa = "scalar" | "avx2" | "avx512";

export type CpuProfile = {
  isa: Isa;
  model: string;
  flags: string[];
  f64Width: number;
  i32Width: number;
  align: number;
  vector: number;
  batch: number;
  kernel: string;
  downclock: boolean;
  note: string;
};

export const DUCKDB_VECTOR = 2048;
export const ARROW_BATCH = 65536;

const ISA: Record<Isa, Pick<CpuProfile, "f64Width" | "i32Width" | "align" | "kernel" | "downclock">> = {
  scalar: { f64Width: 1, i32Width: 1, align: 8, kernel: "remainder", downclock: false },
  avx2: { f64Width: 4, i32Width: 8, align: 32, kernel: "avx2-shape", downclock: false },
  avx512: { f64Width: 8, i32Width: 16, align: 64, kernel: "avx512-shape", downclock: true },
};

export function parseFlags(flagsLine: string): string[] {
  return flagsLine.toLowerCase().split(/\s+/).filter(Boolean);
}

export function isaFromFlags(flags: string[]): Isa {
  const has = (f: string) => flags.includes(f);
  if (has("avx512f") || has("avx512")) return "avx512";
  if (has("avx2")) return "avx2";
  return "scalar";
}

export function profileFromFlags(flagsLine: string, model = "unknown"): CpuProfile {
  const flags = parseFlags(flagsLine);
  const isa = isaFromFlags(flags);
  const spec = ISA[isa];
  const downclock = isa === "avx512" && /xeon|skylake|cascade|broadwell/i.test(model) && !/ice lake|sapphire|emerald|granite|zen [45]/i.test(model);
  return {
    isa,
    model: model.trim() || "unknown",
    flags: flags.filter((f) => f.startsWith("avx") || f.startsWith("sse") || f === "fma"),
    f64Width: spec.f64Width,
    i32Width: spec.i32Width,
    align: spec.align,
    vector: DUCKDB_VECTOR,
    batch: ARROW_BATCH,
    kernel: spec.kernel,
    downclock,
    note: downclock
      ? `${isa} · f64×${spec.f64Width} · 對齊 ${spec.align}B · 舊 Xeon 可能降頻，執行期可退 AVX2`
      : `${isa} · f64×${spec.f64Width} · i32×${spec.i32Width} · 對齊 ${spec.align}B · DuckDB vector ${DUCKDB_VECTOR}`,
  };
}

export function simdBoost(isa: Isa): number {
  if (isa === "avx512") return 1.3;
  if (isa === "avx2") return 1.15;
  return 1;
}

export function alignUp(n: number, width: number): number {
  if (width <= 1) return n;
  const r = n % width;
  return r === 0 ? n : n + (width - r);
}

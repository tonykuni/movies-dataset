import { LLVM_LAB } from "@/lib/llvm-practice";

export function LlvmBay() {
  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">LLVM · ANC-35</p>
            <h2 className="mt-1 text-lg font-medium tracking-display">Numba 的 LLVM 後端</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              LLVM {LLVM_LAB.llvm} · numba {LLVM_LAB.numba} · x86_64 · 2 核 · n=
              {LLVM_LAB.n.toLocaleString()}。向量化要看組語裡的 ymm / vfmadd，不看裝飾器名字。
            </p>
          </div>
          <div className="min-w-28">
            <p className="font-mono text-[10px] tracking-widest text-muted">有差</p>
            <p className="font-mono text-3xl tabular-nums">
              {LLVM_LAB.wins}/{LLVM_LAB.total}
            </p>
            <p className="mt-1 font-mono text-[10px] text-muted">遞推無法向量化</p>
          </div>
        </div>
      </section>

      <section className="overflow-x-auto rounded-[var(--radius-xl)] border border-border">
        <h3 className="border-b border-border bg-bg-elevated px-3 py-2 text-sm font-medium">
          fastmath 一次打開的 LLVM 旗標
        </h3>
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="bg-bg-elevated font-mono text-[10px] tracking-widest text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">旗標</th>
              <th className="px-3 py-2 font-medium">假設</th>
              <th className="px-3 py-2 font-medium">後端能做什麼</th>
            </tr>
          </thead>
          <tbody>
            {LLVM_LAB.flags.map((f) => (
              <tr key={f.id} className="border-t border-border">
                <td className="px-3 py-2 font-mono text-xs text-ok">{f.id}</td>
                <td className="px-3 py-2">{f.means}</td>
                <td className="px-3 py-2 text-xs text-muted">{f.effect}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="overflow-x-auto rounded-[var(--radius-xl)] border border-border">
        <h3 className="border-b border-border bg-bg-elevated px-3 py-2 text-sm font-medium">實測 · 組語對照</h3>
        <table className="w-full min-w-[860px] text-left text-sm">
          <thead className="bg-bg-elevated font-mono text-[10px] tracking-widest text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">項目</th>
              <th className="px-3 py-2 font-medium">反模式</th>
              <th className="px-3 py-2 font-medium">ms</th>
              <th className="px-3 py-2 font-medium">守則</th>
              <th className="px-3 py-2 font-medium">ms</th>
              <th className="px-3 py-2 font-medium">倍率</th>
            </tr>
          </thead>
          <tbody>
            {LLVM_LAB.cases.map((c) => (
              <tr key={c.id} className="border-t border-border align-top">
                <td className="px-3 py-2">
                  <span className="block">{c.title}</span>
                  <span className="block text-xs text-muted">{c.note}</span>
                  <span className="mt-1 block font-mono text-[10px] text-muted">{c.evidence}</span>
                </td>
                <td className="px-3 py-2 font-mono text-xs text-muted">{c.anti}</td>
                <td className="px-3 py-2 font-mono text-xs tabular-nums">
                  {c.id === "rec" ? "—" : c.antiMs.toFixed(3)}
                </td>
                <td className="px-3 py-2 font-mono text-xs text-muted">{c.practice}</td>
                <td className="px-3 py-2 font-mono text-xs tabular-nums">
                  {c.id === "rec" ? "純量" : c.practiceMs.toFixed(3)}
                </td>
                <td className="px-3 py-2 font-mono text-xs text-ok tabular-nums">
                  {c.id === "rec" ? "不可向量化" : `${c.speedup.toFixed(1)}×`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

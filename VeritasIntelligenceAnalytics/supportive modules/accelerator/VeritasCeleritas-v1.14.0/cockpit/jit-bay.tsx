import { JIT_AUDIT_SAMPLE, JIT_LAB } from "@/lib/jit-practice";
import { cn } from "@/lib/utils";

export function JitBay() {
  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">JIT · ANC-34</p>
            <h2 className="mt-1 text-lg font-medium tracking-display">Numba JIT 守則</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              numba {JIT_LAB.numba} · n={JIT_LAB.n.toLocaleString()} · 2 核。只在 nopython
              編譯迴圈依賴與融合核。簡單 ufunc 與小陣列交給 numpy。財務核不開 fastmath。
            </p>
          </div>
          <div className="min-w-28">
            <p className="font-mono text-[10px] tracking-widest text-muted">守則勝</p>
            <p className="font-mono text-3xl tabular-nums">
              {JIT_LAB.wins}/{JIT_LAB.total}
            </p>
            <p className="mt-1 font-mono text-[10px] text-muted">其餘為持平，不是輸</p>
          </div>
        </div>
      </section>

      <section className="overflow-x-auto rounded-[var(--radius-xl)] border border-border">
        <h3 className="border-b border-border bg-bg-elevated px-3 py-2 text-sm font-medium">做 / 不要做</h3>
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="bg-bg-elevated font-mono text-[10px] tracking-widest text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">做</th>
              <th className="px-3 py-2 font-medium">不要做</th>
              <th className="px-3 py-2 font-medium">原因</th>
            </tr>
          </thead>
          <tbody>
            {JIT_LAB.rules.map((r) => (
              <tr key={r.id} className="border-t border-border">
                <td className="px-3 py-2 text-ok">{r.do}</td>
                <td className="px-3 py-2 text-warn">{r.dont}</td>
                <td className="px-3 py-2 text-xs text-muted">{r.why}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="overflow-x-auto rounded-[var(--radius-xl)] border border-border">
        <h3 className="border-b border-border bg-bg-elevated px-3 py-2 text-sm font-medium">實測 · 含首次編譯稅</h3>
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="bg-bg-elevated font-mono text-[10px] tracking-widest text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">項目</th>
              <th className="px-3 py-2 font-medium">反模式</th>
              <th className="px-3 py-2 font-medium">ms</th>
              <th className="px-3 py-2 font-medium">守則</th>
              <th className="px-3 py-2 font-medium">ms</th>
              <th className="px-3 py-2 font-medium">倍率</th>
              <th className="px-3 py-2 font-medium">編譯</th>
            </tr>
          </thead>
          <tbody>
            {JIT_LAB.cases.map((c) => (
              <tr key={c.id} className="border-t border-border">
                <td className="px-3 py-2">
                  <span className="block">{c.title}</span>
                  <span className="block text-xs text-muted">{c.rule}</span>
                </td>
                <td className="px-3 py-2 font-mono text-xs text-muted">{c.anti}</td>
                <td className="px-3 py-2 font-mono text-xs tabular-nums">{c.antiMs.toFixed(3)}</td>
                <td className="px-3 py-2 font-mono text-xs text-muted">{c.practice}</td>
                <td className="px-3 py-2 font-mono text-xs tabular-nums">{c.practiceMs.toFixed(3)}</td>
                <td className="px-3 py-2 font-mono text-xs text-ok tabular-nums">{c.speedup.toFixed(1)}×</td>
                <td className="px-3 py-2 font-mono text-xs tabular-nums text-muted">
                  {c.compileMs == null ? "—" : `${c.compileMs.toFixed(0)} ms`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4">
        <h3 className="text-sm font-medium">AST 抽樣 · @jit 會被擋</h3>
        <pre className="mt-2 overflow-x-auto font-mono text-[11px] leading-5 text-muted">{JIT_AUDIT_SAMPLE.src}</pre>
        <ul className="mt-3 space-y-1">
          {JIT_AUDIT_SAMPLE.findings.map((f) => (
            <li key={f.id + f.line} className="flex flex-wrap gap-2 font-mono text-[11px]">
              <span
                className={cn(
                  "tracking-widest",
                  f.sev === "block" ? "text-danger" : f.sev === "warn" ? "text-warn" : "text-muted",
                )}
              >
                {f.sev.toUpperCase()}
              </span>
              <span className="text-muted">L{f.line}</span>
              <span>{f.msg}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

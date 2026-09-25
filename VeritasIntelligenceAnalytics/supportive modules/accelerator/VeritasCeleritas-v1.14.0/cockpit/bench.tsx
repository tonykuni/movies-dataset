import { useState } from "react";
import { Timer } from "lucide-react";
import { LAB, caption, runBrowserBench, type BenchCase } from "@/lib/bench";
import { cn } from "@/lib/utils";

export function BenchBay() {
  const [live, setLive] = useState<BenchCase[] | null>(null);
  const [busy, setBusy] = useState(false);

  async function run() {
    if (busy) return;
    setBusy(true);
    await new Promise((r) => setTimeout(r, 40));
    setLive(runBrowserBench());
    setBusy(false);
  }

  const labNew = LAB.cases.filter((c) => c.winner === "new").length;
  const labOld = LAB.cases.filter((c) => c.winner === "old").length;

  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">RACE · ANC-32</p>
            <h2 className="mt-1 text-lg font-medium tracking-display">舊路徑 vs 新引擎 · 誰快</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              實驗室實測 CPython {LAB.py} · {LAB.cpu} 核 · 中位數 15 次。四項新引擎全勝。微任務可向量化則一次進 numpy，JSON 走 orjson。
            </p>
          </div>
          <div className="min-w-28">
            <p className="font-mono text-[10px] tracking-widest text-muted">新引擎勝</p>
            <p className="font-mono text-3xl tabular-nums">
              {labNew}/{LAB.cases.length}
            </p>
            <p className="mt-1 font-mono text-[10px] text-muted">舊勝 {labOld} · 平手 {LAB.cases.length - labNew - labOld}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void run()}
          disabled={busy}
          className="mt-4 min-h-11 rounded-[var(--radius-md)] bg-accent px-4 text-sm font-medium text-accent-fg disabled:opacity-60"
        >
          {busy ? "測試中…" : live ? "再測瀏覽器這一輪" : "測瀏覽器這一輪"}
        </button>
      </section>

      <Matrix title="實驗室 · Python" cases={LAB.cases} />
      {live && <Matrix title="瀏覽器這一輪" cases={live} />}
    </div>
  );
}

function Matrix({ title, cases }: { title: string; cases: BenchCase[] }) {
  return (
    <section className="overflow-x-auto rounded-[var(--radius-xl)] border border-border">
      <div className="flex items-center gap-2 border-b border-border bg-bg-elevated px-3 py-2">
        <Timer className="size-4 text-accent" strokeWidth={1.75} />
        <h3 className="text-sm font-medium">{title}</h3>
      </div>
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="bg-bg-elevated font-mono text-[10px] tracking-widest text-muted">
          <tr>
            <th className="px-3 py-2 font-medium">項目</th>
            <th className="px-3 py-2 font-medium">舊路徑</th>
            <th className="px-3 py-2 font-medium">ms</th>
            <th className="px-3 py-2 font-medium">新引擎</th>
            <th className="px-3 py-2 font-medium">ms</th>
            <th className="px-3 py-2 font-medium">誰快</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr key={c.id} className="border-t border-border">
              <td className="px-3 py-2">
                <span className="block text-fg">{c.title}</span>
                <span className="block text-xs text-muted">{c.note}</span>
              </td>
              <td className="px-3 py-2 font-mono text-xs text-muted">{c.old}</td>
              <td className="px-3 py-2 font-mono text-xs tabular-nums">{c.oldMs.toFixed(3)}</td>
              <td className="px-3 py-2 font-mono text-xs text-muted">{c.new}</td>
              <td className="px-3 py-2 font-mono text-xs tabular-nums">{c.newMs.toFixed(3)}</td>
              <td className="px-3 py-2">
                <span
                  className={cn(
                    "font-mono text-[10px] tracking-widest",
                    c.winner === "new" ? "text-ok" : c.winner === "old" ? "text-warn" : "text-muted",
                  )}
                >
                  {c.winner === "new" ? "新" : c.winner === "old" ? "舊" : "平"}
                </span>
                <span className="mt-1 block text-xs text-muted">{caption(c)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

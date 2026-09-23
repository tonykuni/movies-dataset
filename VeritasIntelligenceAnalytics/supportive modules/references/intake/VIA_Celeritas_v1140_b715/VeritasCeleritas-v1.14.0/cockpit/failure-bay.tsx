import { FAIL_LAB } from "@/lib/failure-matrix";
import { cn } from "@/lib/utils";

const ARMED: Record<string, string> = {
  S1: "主解",
  S2: "備援",
  S3: "最後",
};

export function FailureBay() {
  const high = FAIL_LAB.rows.filter((r) => r.blast === "high").length;
  return (
    <div className="space-y-4">
      <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[10px] tracking-[0.18em] text-muted">FAILSAFE · ANC-36</p>
            <h2 className="mt-1 text-lg font-medium tracking-display">25 個最可能失效點</h2>
            <p className="mt-1 max-w-2xl text-sm text-muted">
              每個點三條解法：主解、備援、最後手段。現況是這台機器上 `xroute` 選到的那條。探針沒過會改走最後手段。
            </p>
          </div>
          <div className="min-w-28">
            <p className="font-mono text-[10px] tracking-widest text-muted">主解接上</p>
            <p className="font-mono text-3xl tabular-nums">
              {FAIL_LAB.armedS1}/{FAIL_LAB.n}
            </p>
            <p className="mt-1 font-mono text-[10px] text-muted">
              高風險 {high} · 未解 {FAIL_LAB.open}
            </p>
          </div>
        </div>
      </section>

      <section className="overflow-x-auto rounded-[var(--radius-xl)] border border-border">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="bg-bg-elevated font-mono text-[10px] tracking-widest text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">點</th>
              <th className="px-3 py-2 font-medium">主解</th>
              <th className="px-3 py-2 font-medium">備援</th>
              <th className="px-3 py-2 font-medium">最後</th>
              <th className="px-3 py-2 font-medium">現況</th>
            </tr>
          </thead>
          <tbody>
            {FAIL_LAB.rows.map((r) => (
              <tr key={r.id} className="border-t border-border align-top">
                <td className="px-3 py-2">
                  <span className="font-mono text-[10px] text-muted">{r.id}</span>
                  <span className="mt-0.5 block">{r.title}</span>
                  <span className="mt-0.5 block text-xs text-muted">{r.symptom}</span>
                  <span
                    className={cn(
                      "mt-1 inline-block font-mono text-[10px] tracking-widest",
                      r.blast === "high" ? "text-danger" : "text-muted",
                    )}
                  >
                    {r.blast === "high" ? "HIGH" : "MED"}
                  </span>
                </td>
                <td className={cn("px-3 py-2 text-xs", r.armed === "S1" ? "text-ok" : "text-muted")}>{r.s1}</td>
                <td className={cn("px-3 py-2 text-xs", r.armed === "S2" ? "text-ok" : "text-muted")}>{r.s2}</td>
                <td className={cn("px-3 py-2 text-xs", r.armed === "S3" ? "text-ok" : "text-muted")}>{r.s3}</td>
                <td className="px-3 py-2">
                  <span className="font-mono text-[10px] tracking-widest text-ok">
                    {r.armed} {ARMED[r.armed]}
                  </span>
                  <span className="mt-1 block font-mono text-[10px] text-muted">
                    {r.probe === "pass" ? "探針過" : r.probe === "fail" ? "探針失敗" : "策略"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

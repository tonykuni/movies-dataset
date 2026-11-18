import { useServerFn } from "@tanstack/react-start";
import { useEffect, useState } from "react";
import { loadVqg } from "@/lib/vqg/load";
import { FRESH_IDS, VQG } from "@/lib/vqg/registry";
import type { VqgPayload } from "@/lib/vqg/types";

const VAP_IDS = [
  "VIA-VQG-TA-VOL003",
  "VIA-VQG-TA-FLW005",
  "VIA-VQG-TA-FLW006",
  "VIA-VQG-TA-RSK003",
  "VIA-VQG-TA-CMP012",
] as const;

function fmt(value: number | null, unit: string, signal = ""): string {
  if (value == null) return signal.includes("留空") ? "留空" : "樣本不足";
  const digits = Math.abs(value) >= 100 ? 1 : 2;
  return `${value.toFixed(digits)} ${unit}`;
}

function taipeiStamp(iso: string | null): string {
  if (!iso) return "尚未更新";
  return new Intl.DateTimeFormat("zh-TW", {
    timeZone: "Asia/Taipei",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).format(new Date(iso));
}

export function VqgBoard({
  initial,
  embedded = false,
  tick = 0,
}: {
  initial: VqgPayload | null;
  embedded?: boolean;
  tick?: number;
}) {
  const refresh = useServerFn(loadVqg);
  const [data, setData] = useState(initial);
  const [busy, setBusy] = useState(initial == null);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(initial ? new Date().toISOString() : null);
  const [theme, setTheme] = useState("全部");
  const [pick, setPick] = useState<"全部" | "新登錄">("全部");
  const [selected, setSelected] = useState(initial?.registry[0]?.id ?? "");

  async function pull() {
    setBusy(true);
    try {
      const next = await refresh();
      setData(next);
      setUpdatedAt(new Date().toISOString());
      setError(null);
      setSelected((current) => current || next.registry[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失敗");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    let cancel = false;
    if (!initial) void pull();
    const id = window.setInterval(() => {
      if (!cancel && document.visibilityState === "visible") void pull();
    }, 5 * 60 * 1000);
    return () => {
      cancel = true;
      window.clearInterval(id);
    };
    // The first load and the five-minute refresh are owned here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (tick > 0) void pull();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick]);

  if (!data) {
    return (
      <section id={embedded ? undefined : "vqg"} className="bg-paper px-4 py-6 text-ink">
        <h2 className="text-sm font-semibold">指標、訊號、回放</h2>
        <p className="mt-2 text-sm">{error ?? "正在取數並重算。定義有調整時，這次更新會一併寫回。"}</p>
      </section>
    );
  }

  const view = data;
  const themes = ["全部", ...view.counts.map((row) => row.theme)];
  const fresh = new Set<string>(FRESH_IDS);
  const visible = view.registry.filter((row) => {
    if (pick === "新登錄" && !fresh.has(row.id)) return false;
    return theme === "全部" || row.theme === theme;
  });
  const detail = view.registry.find((row) => row.id === selected) ?? visible[0];
  const spec = VQG.find((row) => row.id === detail?.id);
  const detailReadings = view.readings.filter((row) => row.id === detail?.id);
  const linked = view.tests.filter((row) => row.indicatorId === detail?.id);

  return (
    <div className={embedded ? "" : "min-h-screen bg-bg text-accent-fg"}>
      <header className={embedded ? "bg-paper px-4 py-4 text-ink" : "mx-auto w-full max-w-7xl px-5 pt-8 pb-4"}>
        <p className="text-xs tracking-widest text-accent">VIA-ENG-001 · VIA-PAR-001</p>
        <div className="mt-1 flex flex-wrap items-end justify-between gap-3">
          <h1 className={embedded ? "text-lg font-semibold" : "text-3xl font-semibold"}>指標、訊號、回放</h1>
          <div className="flex items-center gap-3">
            <p className="font-mono text-xs text-muted" suppressHydrationWarning>
              {busy ? "更新中" : taipeiStamp(updatedAt)}
            </p>
            <button type="button" onClick={() => void pull()} disabled={busy} className="min-h-11 border border-line px-3 text-sm text-ink disabled:opacity-60">
              {busy ? "更新中" : "立即重算"}
            </button>
          </div>
        </div>
        <p className="mt-2 text-sm">
          資料截止 {view.asOf || "—"}。價格 {view.barCount} 日，扣當沖成交 {view.flowDays} 日。參數只有 VIA-PAR-001。每 5 分鐘重算一次。
        </p>
        {view.versions.some((row) => row.status === "衝突") ? (
          <p className="mt-2 text-sm font-medium">有指標版本衝突。舊內容沒有覆蓋，請先把版本加一。</p>
        ) : null}
        {error ? <p className="mt-2 text-sm font-medium">{error}</p> : null}
      </header>

      <main className="mx-auto grid w-full max-w-7xl gap-6 px-5 pb-16">
        <section className="grid gap-px bg-line md:grid-cols-3">
          {[
            ["訊號庫", `${view.signals.length} 條跡象。只寫定義、核對規則、噪音和鈍化怎麼記。不算數字，也不下買賣結論。`],
            ["計算引擎", `${view.barCount} 個交易日的調整後收盤。${view.registry.length} 個編號都走同一個入口。這次新接 20 個。不使用 TA-LIB，也不把價格交給其他套件重算。缺欄留空。`],
            ["測試及回測引擎", `${view.tests.length} 條逐日回放。只計看得到、看不到、樣本不足，以及噪音和鈍化。不回測淨利、勝率、獲利因子或盈虧比。`],
          ].map(([title, body]) => (
            <article key={title} className="bg-paper px-4 py-4 text-ink">
              <h2 className="text-sm font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-relaxed">{body}</p>
            </article>
          ))}
        </section>

        <section className="bg-paper px-4 py-4 text-ink">
          <h2 className="text-sm font-semibold">選標</h2>
          <p className="mt-1 text-sm leading-relaxed">
            從已登錄的指標裡選，不在畫面上另寫公式。新的 20 項已經建在 VIA-PAR-001，版本從 1 起算。舊編號的公式沒有改。
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(["全部", "新登錄"] as const).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setPick(item)}
                className={`min-h-11 px-3 text-sm ${pick === item ? "bg-ink text-paper" : "border border-line"}`}
              >
                {item === "全部" ? `全部 ${view.registry.length}` : "新登錄 20"}
              </button>
            ))}
          </div>
        </section>

        <section className="bg-paper text-ink">
          <div className="px-4 pt-4">
            <h2 className="text-sm font-semibold">專題分析</h2>
            <p className="mt-1 text-sm">只讀已經算出的讀數。看得到是這條規則目前成立，不是上漲，也不是之後會怎樣。</p>
          </div>
          <div className="mt-3 grid gap-px bg-line sm:grid-cols-2">
            { (view.topics ?? []).map((row) => (
              <article key={row.id} className="bg-paper px-4 py-3">
                <div className="flex items-baseline justify-between gap-3">
                  <h3 className="text-sm font-medium">{row.name}</h3>
                  <p className={`shrink-0 text-xs ${row.status === "看得到" ? "text-ink" : "text-muted"}`}>{row.status}</p>
                </div>
                <p className="mt-2 text-sm leading-relaxed">{row.question}</p>
                <p className="mt-1 font-mono text-xs text-muted">{row.detail}</p>
                <p className="mt-1 text-xs text-muted">
                  版本 {row.version} · {row.rule}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="bg-paper px-4 py-4 text-ink">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="text-sm font-semibold">VAP 呈現</h2>
            <p className="font-mono text-xs text-muted">只讀 VIA-ENG-001</p>
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed">
            這一塊只把已經算出的結果和留空原因攤開。不另算一次，也不用賺賠或勝率來排。沒有成交股數、利率、同市場基準或台積電序列的解，維持空白。
          </p>
          <div className="mt-4 grid gap-px bg-line md:grid-cols-2">
            {VAP_IDS.map((id) => {
              const rows = view.readings.filter((row) => row.id === id);
              const head = rows[0];
              if (!head) return null;
              return (
                <article key={id} className="bg-paper px-4 py-4">
                  <button type="button" onClick={() => setSelected(id)} className="min-h-11 text-left">
                    <p className="font-mono text-xs text-muted">{id}</p>
                    <h3 className="mt-1 text-sm font-semibold">{head.name}</h3>
                  </button>
                  <ul className="mt-3 space-y-3">
                    {rows.map((row) => (
                      <li key={`${row.id}-${row.label}`}>
                        <div className="flex items-baseline justify-between gap-3">
                          <p className="text-sm">{row.label.trim() || row.name}</p>
                          <p className="font-mono text-sm">{fmt(row.value, row.unit, row.signal)}</p>
                        </div>
                        <p className="mt-1 text-sm leading-relaxed text-muted">{row.signal}</p>
                      </li>
                    ))}
                  </ul>
                </article>
              );
            })}
          </div>
        </section>

        <section className="bg-paper text-ink">
          <div className="px-4 pt-4">
            <h2 className="text-sm font-semibold">訊號庫</h2>
            <p className="mt-1 text-sm">看得到只代表這一筆符合定義。它不是上漲，也不是勝率。</p>
          </div>
          <div className="mt-3 grid gap-px bg-line sm:grid-cols-2 xl:grid-cols-3">
            {view.tests.map((row) => (
              <button
                key={row.id}
                type="button"
                onClick={() => setSelected(row.indicatorId)}
                className={`bg-paper px-4 py-3 text-left ${row.indicatorId === detail?.id ? "outline outline-1 outline-ink" : ""}`}
              >
                <div className="flex items-baseline justify-between gap-3">
                  <p className="text-sm font-medium">{row.name}</p>
                  <p className={`shrink-0 text-xs ${row.latestStatus === "看得到" ? "text-ink" : "text-muted"}`}>{row.latestStatus}</p>
                </div>
                <p className="mt-2 font-mono text-xs">{row.latestDetail}</p>
                <p className="mt-2 text-xs text-muted">
                  回放 {row.present} 看得到 · {row.absent} 看不到 · 不足 {row.insufficient}
                </p>
                <p className="mt-1 text-xs text-muted">
                  噪音 {row.noiseCount} · 鈍化 {row.saturationCount}
                  {row.saturationNow.startsWith("不適用") ? "" : ` · ${row.saturationNow}`}
                </p>
              </button>
            ))}
          </div>
        </section>

        <section className="bg-paper px-4 py-4 text-ink">
          <h2 className="text-sm font-semibold">怎麼讓數字比得起來</h2>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm leading-relaxed">
            <li>價格只用調整後收盤。要比，比漲跌幅，不比點數。</li>
            <li>金額先除以扣掉當沖的成交值，變成占比。占比才能跨日比。</li>
            <li>漲跌和占比再看自己過去的位置。同一把尺，才能跨群比強弱。</li>
            <li>當沖和台積電會把成交灌大。分母拿掉它們，其餘變化才不會被蓋住。還沒接到的數字留空。</li>
            <li>回放只核對跡象到目前這一筆。不回測淨利、勝率或盈虧比。</li>
          </ol>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          {view.themes.map((row) => (
            <article key={row.theme} className="bg-paper px-4 py-4 text-ink">
              <div className="flex items-baseline justify-between gap-3">
                <h2 className="text-sm font-semibold">{row.theme}</h2>
                <p className="font-mono text-xs text-muted">
                  {row.indicators} 項 · {row.filled} 個有值
                </p>
              </div>
              <p className="mt-2 text-sm leading-relaxed">{row.summary}</p>
            </article>
          ))}
        </section>

        <section className="bg-paper text-ink">
          <div className="px-4 pt-4">
            <h2 className="text-sm font-semibold">本機免費函式庫</h2>
            <p className="mt-1 text-sm">只登記已經安裝的免費套件、它做的事，和目前版本。價格仍由 VIA-ENG-001 算，不交給這些套件重算。</p>
          </div>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-muted">
                <tr>
                  <th className="px-4 py-2 font-medium">編號</th>
                  <th className="px-4 py-2 font-medium">套件</th>
                  <th className="px-4 py-2 font-medium">版本</th>
                  <th className="px-4 py-2 font-medium">授權</th>
                  <th className="px-4 py-2 font-medium">展開的功能</th>
                </tr>
              </thead>
              <tbody>
                {(view.libraries ?? []).map((row) => (
                  <tr key={row.id}>
                    <td className="px-4 py-2 font-mono text-xs">{row.id}</td>
                    <td className="px-4 py-2">{row.package}</td>
                    <td className="px-4 py-2 font-mono text-xs">{row.version}</td>
                    <td className="px-4 py-2 text-xs">{row.license}</td>
                    <td className="px-4 py-2">{row.expands}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="bg-paper text-ink">
          <p className="px-4 pt-4 text-sm">有正式英文名稱的，用英文，每個字的首字母大寫。自己的指標用白話名稱。</p>
          <p className="px-4 pt-2 text-sm">編號不變。公式、參數或天數變了才加版本。只改說明不加版本。舊版本留在資料庫，不覆蓋。</p>
          <div className="flex flex-wrap gap-2 px-4 pt-4">
            {themes.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setTheme(item)}
                className={`min-h-11 px-3 text-sm ${theme === item ? "bg-ink text-paper" : "border border-line"}`}
              >
                {item}
              </button>
            ))}
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-muted">
                <tr>
                  <th className="px-4 py-2 font-medium">編號</th>
                  <th className="px-4 py-2 font-medium">名稱</th>
                  <th className="px-4 py-2 font-medium">版本</th>
                  <th className="px-4 py-2 font-medium">主題</th>
                  <th className="px-4 py-2 font-medium">天數</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((row) => (
                  <tr key={row.id} className={row.id === detail?.id ? "bg-line/60" : ""}>
                    <td className="px-4 py-2">
                      <button type="button" className="min-h-11 text-left font-mono text-xs" onClick={() => setSelected(row.id)}>
                        {row.id}
                      </button>
                    </td>
                    <td className="px-4 py-2">{row.name}</td>
                    <td className="px-4 py-2 font-mono text-xs">{row.version}</td>
                    <td className="px-4 py-2">{row.theme}</td>
                    <td className="px-4 py-2 font-mono text-xs">{row.windows.join(" / ") || "固定參數"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {detail ? (
          <section className="bg-paper px-4 py-4 text-ink">
            <p className="font-mono text-xs text-muted">{detail.id}</p>
            <h2 className="mt-1 text-lg font-semibold">{detail.name}</h2>
            <p className="mt-1 text-xs text-muted">
              {detail.naming === "正式" ? "正式英文名稱" : "自訂名稱"} · 版本 {detail.version} · {detail.changeNote}
              {view.versions.find((row) => row.id === detail.id)?.status === "衝突" ? " · 版本衝突，舊內容未覆蓋" : ""}
            </p>
            <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs text-muted">公式</dt>
                <dd className="mt-1 leading-relaxed">{spec?.formula ?? detail.formula}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted">要用到的欄</dt>
                <dd className="mt-1 leading-relaxed">{spec?.inputs.join("、") || "—"}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-xs text-muted">解</dt>
                <dd className="mt-1 space-y-2 leading-relaxed">
                  {spec?.solutions.map((row) => (
                    <p key={row.id}>
                      <span className="font-medium">{row.id}</span>
                      <span className="text-muted"> · {row.unit}</span>
                      。{row.method}
                      {row.blank}
                    </p>
                  )) ?? <p>{detail.formula}</p>}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted">參數</dt>
                <dd className="mt-1 font-mono">
                  {detail.windows.length ? `天數 ${detail.windows.join(" / ")}` : "沒有天數窗口"}
                  {Object.keys(detail.params).length ? ` · ${JSON.stringify(detail.params)}` : ""}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted">目的</dt>
                <dd className="mt-1 leading-relaxed">{detail.purpose}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted">優勢</dt>
                <dd className="mt-1 leading-relaxed">{detail.advantage}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted">劣勢</dt>
                <dd className="mt-1 leading-relaxed">{detail.disadvantage}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted">往後升級</dt>
                <dd className="mt-1 leading-relaxed">{detail.upgrade}</dd>
              </div>
            </dl>
            <p className="mt-3 text-sm leading-relaxed">{spec?.evidence ?? ""}</p>
            <p className="mt-2 text-sm leading-relaxed">{detail.signalRule}</p>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted">
                  <tr>
                    <th className="py-2 pr-3 font-medium">讀數</th>
                    <th className="py-2 pr-3 font-medium">數值</th>
                    <th className="py-2 pr-3 font-medium">分位</th>
                    <th className="py-2 font-medium">目前位置</th>
                  </tr>
                </thead>
                <tbody>
                  {detailReadings.map((row) => (
                    <tr key={`${row.id}-${row.label}`}>
                      <td className="py-2 pr-3">{row.label.trim() || row.name}</td>
                      <td className="py-2 pr-3 font-mono">{fmt(row.value, row.unit, row.signal)}</td>
                      <td className="py-2 pr-3 font-mono">{row.percentile == null ? "—" : row.percentile.toFixed(0)}</td>
                      <td className="py-2">{row.signal}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <h3 className="mt-4 text-sm font-semibold">對上的跡象</h3>
            {linked.length === 0 ? (
              <p className="mt-2 text-sm">這個指標目前沒有掛跡象。換指標時，這裡會跟著換。</p>
            ) : (
              <ul className="mt-2 space-y-3 text-sm">
                {linked.map((row) => (
                  <li key={row.id}>
                    <p className="font-medium">
                      {row.name} · {row.latestStatus}
                    </p>
                    <p className="mt-1">{row.meaning}</p>
                    <p className="mt-1 text-xs text-muted">
                      {row.latestDetail} 看得到 {row.present} 天，看不到 {row.absent} 天。噪音 {row.noiseCount} 次，鈍化 {row.saturationCount} 次。
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ) : null}
      </main>
    </div>
  );
}

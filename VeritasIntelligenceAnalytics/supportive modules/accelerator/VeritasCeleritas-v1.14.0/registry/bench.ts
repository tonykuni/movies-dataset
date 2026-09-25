export type BenchWinner = "old" | "new" | "tie";

export type BenchCase = {
  id: string;
  title: string;
  old: string;
  new: string;
  oldMs: number;
  newMs: number;
  winner: BenchWinner;
  speedup: number;
  note: string;
};

/** Lab run: CPython 3.10 · 2 核 · median of 9. */
export const LAB: {
  cpu: number;
  py: string;
  cases: BenchCase[];
} = {
  cpu: 2,
  py: "3.10.21",
  cases: [
    {
      id: "num",
      title: "40萬平方和",
      old: "純 Python 迴圈",
      new: "numpy 向量",
      oldMs: 17.06,
      newMs: 0.483,
      winner: "new",
      speedup: 35.32,
      note: "數值熱路徑走 numpy",
    },
    {
      id: "str",
      title: "3萬段字串",
      old: "s += 片段",
      new: '"".join',
      oldMs: 1.351,
      newMs: 0.155,
      winner: "new",
      speedup: 8.72,
      note: "字串禁 +=",
    },
    {
      id: "micro",
      title: "2萬次平方",
      old: "逐筆 fn(x)",
      new: "xmap numpy",
      oldMs: 1.157,
      newMs: 0.658,
      winner: "new",
      speedup: 1.76,
      note: "可向量化 λ 一次進 numpy。已從 361ms 降到 0.66ms。",
    },
    {
      id: "json",
      title: "1.2萬筆 dumps",
      old: "json.dumps",
      new: "orjson json_dumps",
      oldMs: 5.424,
      newMs: 0.4,
      winner: "new",
      speedup: 13.56,
      note: "略過 stub，走真實 orjson",
    },
  ],
};

export function caption(c: BenchCase): string {
  if (c.winner === "new") return `新引擎快 ${c.speedup.toFixed(1)}×`;
  if (c.winner === "old") {
    const slow = c.newMs / Math.max(c.oldMs, 1e-9);
    if (slow < 5) return `略慢 ${slow.toFixed(1)}×（Python 呼叫；已避開執行緒池）`;
    return `新路徑慢 ${slow.toFixed(0)}× · 勿對微任務開平行`;
  }
  return "平手";
}

function now() {
  return performance.now();
}

function median(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)]!;
}

function timeFn(fn: () => void, rounds = 7): number {
  fn();
  const xs: number[] = [];
  for (let i = 0; i < rounds; i++) {
    const t0 = now();
    fn();
    xs.push(now() - t0);
  }
  return median(xs);
}

export function runBrowserBench(): BenchCase[] {
  const n = 250_000;
  const py: number[] = [];
  for (let i = 0; i < n; i++) py.push(i);
  const ta = new Float64Array(n);
  for (let i = 0; i < n; i++) ta[i] = i;

  const parts: string[] = [];
  for (let i = 0; i < 20_000; i++) parts.push(String(i));

  const numOld = timeFn(() => {
    let s = 0;
    for (let i = 0; i < py.length; i++) s += py[i]! * py[i]!;
    return s;
  });
  const numNew = timeFn(() => {
    let s = 0;
    for (let i = 0; i < ta.length; i++) s += ta[i]! * ta[i]!;
    return s;
  });

  const strOld = timeFn(() => {
    let s = "";
    for (let i = 0; i < parts.length; i++) s += parts[i];
    return s;
  });
  const strNew = timeFn(() => parts.join(""));

  function pack(id: string, title: string, old: string, neu: string, oldMs: number, newMs: number, note: string): BenchCase {
    const winner: BenchWinner =
      newMs < oldMs * 0.97 ? "new" : oldMs < newMs * 0.97 ? "old" : "tie";
    return {
      id,
      title,
      old,
      new: neu,
      oldMs: Math.round(oldMs * 1000) / 1000,
      newMs: Math.round(newMs * 1000) / 1000,
      winner,
      speedup: newMs > 0 ? Math.round((oldMs / newMs) * 100) / 100 : 0,
      note,
    };
  }

  return [
    pack("num", "25萬平方和", "JS 數字陣列", "Float64Array", numOld, numNew, "瀏覽器這一輪"),
    pack("str", "2萬段字串", "s += 片段", "Array.join", strOld, strNew, "瀏覽器這一輪"),
  ];
}

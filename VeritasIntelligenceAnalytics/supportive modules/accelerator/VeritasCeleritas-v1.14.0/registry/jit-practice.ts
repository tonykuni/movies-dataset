export type JitCase = {
  id: string;
  title: string;
  anti: string;
  practice: string;
  antiMs: number;
  practiceMs: number;
  speedup: number;
  rule: string;
  compileMs: number | null;
};

export type JitRule = { id: string; do: string; dont: string; why: string };

/** Lab: CPython 3.10 · numba 0.67 · n=200_000 · 2 核 */
export const JIT_LAB: {
  n: number;
  numba: string;
  wins: number;
  total: number;
  cases: JitCase[];
  rules: JitRule[];
} = {
  n: 200_000,
  numba: "0.67.0",
  wins: 5,
  total: 7,
  rules: [
    { id: "nopython", do: "njit / nopython=True", dont: "@jit 預設 object mode", why: "object mode 幾乎不加速" },
    { id: "ufunc", do: "簡單運算交給 numpy ufunc", dont: "為 a*a 付編譯稅", why: "一次性呼叫會更慢" },
    { id: "rec", do: "迴圈依賴用 njit", dont: "Python 逐筆遞推", why: "這是 Numba 主場" },
    { id: "fuse", do: "分支核融合進一層迴圈", dont: "先遮罩再 ufunc 兩次掃描", why: "減少記憶體來回" },
    { id: "cache", do: "cache=True 跨行程", dont: "每次重編", why: "編譯常是百毫秒級" },
    { id: "par", do: "大 n 才 parallel/prange", dont: "64 筆就開平行", why: "編譯更貴、2 核不一定贏" },
    { id: "tiny", do: "小陣列走 numpy", dont: "對 64 筆 dispatch JIT", why: "呼叫開銷大於運算" },
    { id: "fastmath", do: "財務核勿亂開 fastmath", dont: "預設 fastmath=True", why: "會重排浮點、破 IEEE" },
  ],
  cases: [
    { id: "ufunc", title: "平方", anti: "Python 迴圈寫 ndarray", practice: "numpy ufunc a*a", antiMs: 38.419, practiceMs: 0.116, speedup: 331, rule: "簡單運算不要 JIT", compileMs: null },
    { id: "hot", title: "平方熱路徑", anti: "numpy ufunc", practice: "njit 迴圈（已編譯）", antiMs: 0.11, practiceMs: 0.107, speedup: 1.03, rule: "編譯後僅微贏，第一次 309ms", compileMs: 309.28 },
    { id: "fuse", title: "sin·exp 分支核", anti: "numpy 遮罩兩次掃描", practice: "njit 單迴圈融合", antiMs: 4.51, practiceMs: 2.829, speedup: 1.59, rule: "分支核融合", compileMs: 80.79 },
    { id: "pykern", title: "sin·exp 分支核", anti: "純 Python", practice: "njit", antiMs: 55.425, practiceMs: 2.931, speedup: 18.9, rule: "相對 Python", compileMs: null },
    { id: "rec", title: "指數平滑遞推", anti: "Python 逐筆", practice: "njit 迴圈依賴", antiMs: 51.905, practiceMs: 0.504, speedup: 103, rule: "Numba 主場", compileMs: 102.55 },
    { id: "tiny", title: "64 筆平方", anti: "njit dispatch", practice: "numpy ufunc", antiMs: 0.001, practiceMs: 0.001, speedup: 1, rule: "小陣列不要 JIT", compileMs: null },
    { id: "compile", title: "首次平方編譯", anti: "每次重編", practice: "記住已編譯函式", antiMs: 309.28, practiceMs: 0.107, speedup: 2890, rule: "編譯稅要攤提", compileMs: 309.28 },
  ],
};

export const JIT_AUDIT_SAMPLE = {
  src: `from numba import jit, njit

@jit
def f(x):
    return x * x

@njit(fastmath=True, parallel=True)
def g(x):
    return x
`,
  findings: [
    { id: "bare-jit", line: 3, sev: "block" as const, msg: "@jit 改 @njit 或 @xjit" },
    { id: "fastmath", line: 7, sev: "warn" as const, msg: "fastmath 會破 IEEE，財務核不要開" },
    { id: "parallel", line: 7, sev: "info" as const, msg: "parallel 編譯更貴，確認 n 夠大" },
  ],
};

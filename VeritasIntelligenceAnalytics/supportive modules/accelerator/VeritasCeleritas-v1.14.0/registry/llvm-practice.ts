export type LlvmCase = {
  id: string;
  title: string;
  anti: string;
  practice: string;
  antiMs: number;
  practiceMs: number;
  speedup: number;
  evidence: string;
  note: string;
};

export type LlvmFlag = { id: string; means: string; effect: string };

/** Lab: numba 0.67 · LLVM 22.1 · x86_64 · 2 cores · n=2e6 float64 reduction */
export const LLVM_LAB = {
  llvm: "22.1",
  numba: "0.67.0",
  n: 2_000_000,
  wins: 4,
  total: 5,
  flags: [
    { id: "nnan", means: "假設沒有 NaN", effect: "比較與邊界分支可刪" },
    { id: "ninf", means: "假設沒有 Inf", effect: "無限大分支可刪" },
    { id: "nsz", means: "−0 視為 +0", effect: "符號零可丟" },
    { id: "arcp", means: "允許倒數近似", effect: "除法可改乘法" },
    { id: "contract", means: "允許 FMA 收縮", effect: "mul+add → vfmadd" },
    { id: "reassoc", means: "允許重結合", effect: "浮點約簡才能向量化" },
    { id: "afn", means: "近似 libm", effect: "sin/exp 可換快速版" },
  ] satisfies LlvmFlag[],
  cases: [
    {
      id: "opt",
      title: "優化等級",
      anti: "NUMBA_OPT=0",
      practice: "NUMBA_OPT=3",
      antiMs: 29.126,
      practiceMs: 1.517,
      speedup: 19.2,
      evidence: "OPT 0：ymm=0。OPT 3：仍是純量，但其他 pass 打開。",
      note: "0 關掉循環向量化與多數 LLVM pass",
    },
    {
      id: "fm",
      title: "浮點約簡",
      anti: "fastmath 關（addsd）",
      practice: "fastmath 開（vfmadd）",
      antiMs: 1.43,
      practiceMs: 0.592,
      speedup: 2.42,
      evidence: "ymm 50 · vaddpd 10 · vfmadd 6。誤差約 8e-11。",
      note: "reassoc 才能把約簡向量化。財務核不開。",
    },
    {
      id: "np",
      title: "暫存陣列",
      anti: "numpy x*x+0.5*x",
      practice: "njit 單迴圈 + fastmath",
      antiMs: 10.389,
      practiceMs: 0.592,
      speedup: 17.6,
      evidence: "numpy 物化中間陣列。LLVM 把乘加收成 FMA。",
      note: "融合核才值得付編譯稅",
    },
    {
      id: "bc",
      title: "邊界檢查",
      anti: "boundscheck=True 編譯",
      practice: "boundscheck=False 編譯",
      antiMs: 247.9,
      practiceMs: 73.7,
      speedup: 3.36,
      evidence: "熱路徑 1.41 vs 1.43 ms，幾乎持平。",
      note: "主要省的是編譯，不是執行。除錯要開。",
    },
    {
      id: "rec",
      title: "迴圈依賴",
      anti: "以為能向量化",
      practice: "接受純量 mulsd",
      antiMs: 0,
      practiceMs: 0,
      speedup: 1,
      evidence: "遞推組語是 mulsd / vmulsd，沒有 vaddpd。",
      note: "LLVM 切不開 y[i] 依賴 y[i-1]。Numba 仍該編，但是純量。",
    },
  ] satisfies LlvmCase[],
};

export type VecCase = {
  id: string;
  title: string;
  anti: string;
  practice: string;
  antiMs: number;
  practiceMs: number;
  speedup: number;
  rule: string;
};

export type VecRule = {
  id: string;
  do: string;
  dont: string;
  why: string;
};

/** Lab: CPython 3.10 · numpy · n=80_000 · median 5. */
export const VEC_LAB: {
  n: number;
  wins: number;
  cases: VecCase[];
  rules: VecRule[];
} = {
  n: 80_000,
  wins: 8,
  rules: [
    { id: "ufunc", do: "ufunc / 廣播", dont: "np.vectorize", why: "vectorize 是 Python 迴圈偽裝" },
    { id: "keep", do: "熱路徑保留 ndarray", dont: "每步 .tolist()", why: "轉換成本常大於運算" },
    { id: "dtype", do: "int64 / float64", dont: "dtype=object", why: "object 沒有 SIMD" },
    { id: "mask", do: "布林遮罩", dont: "Python if 過濾", why: "遮罩走 C 層" },
    { id: "alloc", do: "預先配置", dont: "list.append 再轉陣列", why: "已知長度不要長列表" },
    { id: "bcast", do: "廣播對齊", dont: "zip 雙層迴圈", why: "對齊維度交給 numpy" },
    { id: "stride", do: "量過再 copy", dont: "盲目 ascontiguousarray", why: "步幅運算有時更快" },
    { id: "fromiter", do: "fromiter + 明確 dtype", dont: "逐筆 fn(x)", why: "同質純量一次進陣列" },
  ],
  cases: [
    { id: "ufunc", title: "平方", anti: "np.vectorize", practice: "ufunc a*a", antiMs: 8.878, practiceMs: 0.033, speedup: 269, rule: "禁止 vectorize" },
    { id: "keep", title: "熱路徑輸出", anti: "每次 .tolist()", practice: "保留 ndarray", antiMs: 1.671, practiceMs: 0.03, speedup: 55.7, rule: "邊界才轉 list" },
    { id: "dtype", title: "元素相乘", anti: "dtype=object", practice: "int64 ufunc", antiMs: 1.682, practiceMs: 0.028, speedup: 60.1, rule: "禁止 object" },
    { id: "mask", title: "取偶數", anti: "Python if", practice: "布林遮罩", antiMs: 2.328, practiceMs: 0.582, speedup: 4.0, rule: "遮罩走 C" },
    { id: "alloc", title: "寫入結果", anti: "list.append", practice: "預先配置", antiMs: 4.027, practiceMs: 0.067, speedup: 60.1, rule: "已知長度預配置" },
    { id: "bcast", title: "對齊相加", anti: "zip 迴圈", practice: "廣播", antiMs: 16.149, practiceMs: 0.094, speedup: 171.8, rule: "對齊交給廣播" },
    { id: "stride", title: "隔筆平方", anti: "先 copy 連續", practice: "直接步幅 ufunc", antiMs: 0.057, practiceMs: 0.025, speedup: 2.28, rule: "量過再 copy" },
    { id: "fromiter", title: "list→陣列平方", anti: "逐筆 fn(x)", practice: "fromiter + ufunc", antiMs: 4.799, practiceMs: 1.687, speedup: 2.84, rule: "同質純量 fromiter" },
  ],
};

export const VEC_AUDIT_SAMPLE = {
  src: `import numpy as np
np.vectorize(lambda x: x * x)
for x in a:
    y = x.tolist()
np.array(v, dtype="object")
`,
  findings: [
    { id: "vectorize", line: 2, sev: "block", msg: "np.vectorize 不是向量化，改 ufunc / 廣播" },
    { id: "py-loop", line: 3, sev: "info", msg: "Python for：確認是否可改遮罩 / ufunc" },
    { id: "tolist", line: 4, sev: "info", msg: "熱路徑避免 .tolist()，交給邊界再轉" },
    { id: "object-dtype", line: 5, sev: "warn", msg: "dtype=object 沒有 SIMD" },
  ],
};

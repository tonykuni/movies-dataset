export type FailRow = {
  id: string;
  blast: "high" | "med";
  title: string;
  symptom: string;
  s1: string;
  s2: string;
  s3: string;
  armed: "S1" | "S2" | "S3";
  probe: "pass" | "fail" | "skip";
};

export const FAIL_LAB: {
  engine: string;
  n: number;
  armedS1: number;
  open: number;
  ok: boolean;
  rows: FailRow[];
} = {
  "engine": "1.13.0",
  "n": 25,
  "armedS1": 22,
  "open": 0,
  "ok": true,
  "rows": [
    {
      "id": "F01",
      "blast": "high",
      "title": "缺 Numba",
      "symptom": "JIT 匯入失敗，核退回純 Python",
      "s1": "裝 numba，走 @xjit nopython",
      "s2": "改 xvec / numpy ufunc",
      "s3": "純 Python，標明未加速",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F02",
      "blast": "high",
      "title": "JIT 型別推斷失敗",
      "symptom": "njit 吃到 _LazyModule 直接 TypingError",
      "s1": "核內 import 真實 numpy，禁止惰性模組",
      "s2": "去掉 parallel 重編一次",
      "s3": "放棄 JIT，改 numpy",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F03",
      "blast": "high",
      "title": "fastmath 改寫財務結果",
      "symptom": "reassoc / FMA 讓加總漂移",
      "s1": "xjit 預設 fastmath=False",
      "s2": "雙跑比對，誤差超過 1e-9 退回",
      "s3": "財務路徑永久禁用 fastmath",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F04",
      "blast": "med",
      "title": "NUMBA_OPT=0",
      "symptom": "LLVM 向量化 pass 沒開，ymm=0",
      "s1": "維持 OPT=3",
      "s2": "偵測到 0 則改走 numpy",
      "s3": "照跑但報告標成未向量化",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F05",
      "blast": "high",
      "title": "boundscheck 關掉後越界",
      "symptom": "錯誤索引變未定義行為",
      "s1": "除錯與預設保持 boundscheck",
      "s2": "只在探針通過後才關",
      "s3": "IndexError 則立刻退回",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F06",
      "blast": "high",
      "title": "微任務開 ThreadPool",
      "symptom": "2 萬次平方曾慢 631×",
      "s1": "低於 80µs/筆不開池",
      "s2": "可向量化改 fromiter",
      "s3": "其餘走 listcomp",
      "armed": "S2",
      "probe": "pass"
    },
    {
      "id": "F07",
      "blast": "high",
      "title": "orjson stub 雙重編碼",
      "symptom": "假 orjson 比 stdlib 更慢",
      "s1": "略過 *Stub，活體重匯入",
      "s2": "改 msgspec",
      "s3": "stdlib json",
      "armed": "S1",
      "probe": "pass"
    },
    {
      "id": "F08",
      "blast": "med",
      "title": "JSON 不可序列化",
      "symptom": "set / 路徑物件讓 dumps 爆炸",
      "s1": "default=str",
      "s2": "先轉純量再 dumps",
      "s3": "回傳錯誤路徑，不吞例外",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F09",
      "blast": "high",
      "title": "把 np.vectorize 當加速",
      "symptom": "它是 Python 迴圈偽裝",
      "s1": "AST 直接擋 vectorize",
      "s2": "改寫成 ufunc",
      "s3": "fromiter + 明確 dtype",
      "armed": "S1",
      "probe": "pass"
    },
    {
      "id": "F10",
      "blast": "med",
      "title": "dtype=object",
      "symptom": "沒有 SIMD",
      "s1": "稽核警告 object",
      "s2": "純量串改 int64/float64",
      "s3": "拒絕宣稱已向量化",
      "armed": "S2",
      "probe": "skip"
    },
    {
      "id": "F11",
      "blast": "med",
      "title": "熱路徑 .tolist()",
      "symptom": "轉換比運算貴",
      "s1": "xvec keep_array=True",
      "s2": "只在邊界轉 list",
      "s3": "xmap 相容層才 tolist",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F12",
      "blast": "med",
      "title": "遞推被誤判成向量化",
      "symptom": "y[i] 依賴 y[i-1]，LLVM 切不開",
      "s1": "組語看到 mulsd 就標純量",
      "s2": "仍用 njit，但不許報 vaddpd",
      "s3": "資料量小改 Python",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F13",
      "blast": "med",
      "title": "小陣列還去 JIT",
      "symptom": "64 筆 dispatch 比 ufunc 貴",
      "s1": "n<256 走 numpy",
      "s2": "用已編譯快取，不重編",
      "s3": "低於門檻直接 listcomp",
      "armed": "S2",
      "probe": "skip"
    },
    {
      "id": "F14",
      "blast": "high",
      "title": "首次編譯稅",
      "symptom": "平方核第一次可到 300ms",
      "s1": "cache=True",
      "s2": "行程啟動暖機一次",
      "s3": "只跑一次的工作不要 JIT",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F15",
      "blast": "high",
      "title": "記憶體壓力",
      "symptom": "平行配置把機器打滿",
      "s1": "壓力超過門檻改循序",
      "s2": "縮小 chunk",
      "s3": "仍超過則中止這批",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F16",
      "blast": "high",
      "title": "PS 未接入模板",
      "symptom": "AI 產出裸腳本沒有還原",
      "s1": "xps_join 包進模板",
      "s2": "稽核不過就 block",
      "s3": "拒絕執行未接入檔",
      "armed": "S1",
      "probe": "pass"
    },
    {
      "id": "F17",
      "blast": "high",
      "title": "PS 禁令",
      "symptom": "IEX、EmptyWorkingSet、High、32767 執行緒",
      "s1": "去註解後再掃",
      "s2": "命中即 block",
      "s3": "改寫成安全等價寫法",
      "armed": "S1",
      "probe": "pass"
    },
    {
      "id": "F18",
      "blast": "high",
      "title": "離開未還原",
      "symptom": "優先權或親和性留在行程上",
      "s1": "finally / 退出還原",
      "s2": "稽核要求 restore",
      "s3": "只改本行程，不動別人",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F19",
      "blast": "med",
      "title": "預覽框擋下載",
      "symptom": "iframe 吃掉 a[download]",
      "s1": "另開 download.html",
      "s2": "頁內 base64 自行存檔",
      "s3": "直連 zip 備援",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F20",
      "blast": "med",
      "title": "引擎與畫面版本漂移",
      "symptom": "駕駛艙寫 1.6、引擎已 1.13",
      "s1": "單一 __version__",
      "s2": "打包時寫進 SHA256",
      "s3": "啟動比對不一致就標紅",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F21",
      "blast": "high",
      "title": "缺 numpy",
      "symptom": "xvec / 約簡全部失效",
      "s1": "先探針再呼叫",
      "s2": "退回 listcomp",
      "s3": "缺庫時失敗要講人話",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F22",
      "blast": "med",
      "title": "fromiter 混型",
      "symptom": "int 串裡夾 float 會爆",
      "s1": "看頭一個元素選 dtype",
      "s2": "失敗加寬成 float64",
      "s3": "再失敗就放棄向量路徑",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F23",
      "blast": "med",
      "title": "執行緒池沒關",
      "symptom": "每次 xmap 新建池",
      "s1": "微任務根本不建池",
      "s2": "with 包住 Executor",
      "s3": "atexit 再清一次",
      "armed": "S1",
      "probe": "skip"
    },
    {
      "id": "F24",
      "blast": "high",
      "title": "AST 注入沒蓋滿",
      "symptom": "覆蓋率低於 100% 還當成功",
      "s1": "inventory 對 injected",
      "s2": "未滿 100 視為失敗",
      "s3": "漏的節點重掃一次",
      "armed": "S1",
      "probe": "pass"
    },
    {
      "id": "F25",
      "blast": "med",
      "title": "少核平行反慢",
      "symptom": "2 核上 parallel 編譯更貴",
      "s1": "實體核少於 4 不開 parallel",
      "s2": "n 不夠大不 prange",
      "s3": "先量再決定",
      "armed": "S1",
      "probe": "skip"
    }
  ]
};

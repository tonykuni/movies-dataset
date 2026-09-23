export type AccelLayer = "pre" | "cpu" | "mem" | "parse" | "io" | "cross";

export type AccelItem = {
  id: number;
  code: string;
  layer: AccelLayer;
  title: string;
  effect: string;
  stack: string;
  restore: boolean;
};

export const PS_STACK_VERSION = "1.0.1";
export const PS_STACK_FILE = "/VeritasCeleritas.PS7.ps1";

export const PRE_DEPRESS: AccelItem[] = [
  {
    id: 0,
    code: "P1",
    layer: "pre",
    title: "快照本行程",
    effect: "優先權、親和性、GC、執行緒池、Preference 全部先記下",
    stack: "還原契約",
    restore: true,
  },
  {
    id: 0,
    code: "P2",
    layer: "pre",
    title: "關掉本視窗進度條",
    effect: "ProgressPreference = SilentlyContinue，迴圈不再重繪",
    stack: "I/O 減壓",
    restore: true,
  },
  {
    id: 0,
    code: "P3",
    layer: "pre",
    title: "Gen0 輕回收",
    effect: "只收本行程第 0 代，不 Forced Gen2、不掃全機",
    stack: "記憶體起跑",
    restore: false,
  },
  {
    id: 0,
    code: "P4",
    layer: "pre",
    title: "不碰其他進程",
    effect: "不降 Chrome / Explorer、不 EmptyWorkingSet 別人",
    stack: "安全門",
    restore: false,
  },
  {
    id: 0,
    code: "P5",
    layer: "pre",
    title: "註冊退出還原",
    effect: "PowerShell.Exiting 把所有設定寫回快照",
    stack: "關閉即還原",
    restore: true,
  },
];

export const ACCEL_30: AccelItem[] = [
  { id: 1, code: "A01", layer: "cpu", title: "PS7 閘門", effect: "#Requires -Version 7；5.1 直接拒絕", stack: "版本", restore: false },
  { id: 2, code: "A02", layer: "cpu", title: "AboveNormal", effect: "只抬本 PID，不用 High / Realtime", stack: "排程", restore: true },
  { id: 3, code: "A03", layer: "cpu", title: "安全親和性", effect: "UInt64 遮罩；≥64 核則交給 OS", stack: "核心", restore: true },
  { id: 4, code: "A04", layer: "cpu", title: "執行緒池下限", effect: "MinThreads = ProcessorCount", stack: "池", restore: true },
  { id: 5, code: "A05", layer: "cpu", title: "執行緒池上限", effect: "MaxThreads = cores×2，封頂 64，禁止 32767", stack: "池", restore: true },
  { id: 6, code: "A06", layer: "cpu", title: "JIT 設定檔", effect: "ProfileOptimization 寫入 TEMP，不寫工作目錄", stack: "JIT", restore: false },
  { id: 7, code: "A07", layer: "mem", title: "低延遲 GC", effect: "SustainedLowLatency，結束還原", stack: "GC", restore: true },
  { id: 8, code: "A08", layer: "mem", title: "泛型 List", effect: "List[object](4096) 取代 +=", stack: "集合", restore: false },
  { id: 9, code: "A09", layer: "mem", title: "泛型 Dictionary", effect: "O(1) 查找緩衝", stack: "集合", restore: false },
  { id: 10, code: "A10", layer: "mem", title: "ConcurrentDictionary", effect: "給 -Parallel 共用快取", stack: "平行", restore: false },
  { id: 11, code: "A11", layer: "mem", title: "OFS 清空", effect: "陣列展開少一次字串接合", stack: "字串", restore: true },
  { id: 12, code: "A12", layer: "mem", title: "PSStyle 靜音", effect: "PS7 進度視圖改 Minimal", stack: "主控台", restore: true },
  { id: 13, code: "A13", layer: "parse", title: "關閉偵錯掃描", effect: "DebuggerDebugMode.None", stack: "解析", restore: true },
  { id: 14, code: "A14", layer: "parse", title: "SIMD 探測", effect: "Vector.IsHardwareAccelerated", stack: "指令集", restore: false },
  { id: 15, code: "A15", layer: "parse", title: "Regex 編譯快取", effect: "RegexOptions.Compiled 共用表", stack: "正則", restore: false },
  { id: 16, code: "A16", layer: "parse", title: "Stopwatch", effect: "高解析計時給報告矩陣", stack: "量測", restore: false },
  { id: 17, code: "A17", layer: "parse", title: "原生參數傳遞", effect: "PSNativeCommandArgumentPassing = Standard", stack: "外部", restore: true },
  { id: 18, code: "A18", layer: "parse", title: "資訊流靜音", effect: "InformationPreference 關閉；Error 保持 Continue", stack: "管線", restore: true },
  { id: 19, code: "A19", layer: "io", title: "進度條關閉", effect: "迴圈加速的主因，可達數十百分比", stack: "I/O", restore: true },
  { id: 20, code: "A20", layer: "io", title: "Verbose 關閉", effect: "少字串拋送", stack: "I/O", restore: true },
  { id: 21, code: "A21", layer: "io", title: "Error 不吞", effect: "ErrorAction 維持 Continue，不藏錯", stack: "安全", restore: false },
  { id: 22, code: "A22", layer: "io", title: "InvariantCulture", effect: "字串/日期比較走固定文化", stack: "文化", restore: true },
  { id: 23, code: "A23", layer: "io", title: "UTF-8", effect: "OutputEncoding 無 BOM", stack: "編碼", restore: true },
  { id: 24, code: "A24", layer: "io", title: "主控台 UTF-8", effect: "Console.OutputEncoding 對齊", stack: "編碼", restore: true },
  { id: 25, code: "A25", layer: "cross", title: "Http 連線上限", effect: "MaxConnectionsPerServer = cores×4", stack: "網路", restore: false },
  { id: 26, code: "A26", layer: "cross", title: "64KB I/O", effect: "FileStream 緩衝給大檔", stack: "磁碟", restore: false },
  { id: 27, code: "A27", layer: "cross", title: "RunspacePool", effect: "池大小 = 實體核", stack: "平行", restore: true },
  { id: 28, code: "A28", layer: "cross", title: "ForEach -Parallel", effect: "ThrottleLimit = workers", stack: "PS7", restore: false },
  { id: 29, code: "A29", layer: "cross", title: "交叉鎖", effect: "同行程不重套，可巢狀呼叫", stack: "堆疊", restore: true },
  { id: 30, code: "A30", layer: "cross", title: "退出還原", effect: "優先權/GC/池/Preference 全部還原", stack: "安全", restore: true },
];

export const REFUSED = [
  { bad: "EmptyWorkingSet 掃全機進程", why: "會把別的軟體工作集踢到磁碟，桌面變慢" },
  { bad: "把其他進程改成 BelowNormal / Idle", why: "不是無損，瀏覽器與 Explorer 會被餓死" },
  { bad: "SetMaxThreads(32767, 32767)", why: "執行緒爆炸，記憶體與排程一起壞" },
  { bad: "PriorityClass = High / Realtime", why: "搶過滑鼠與磁碟，系統會卡" },
  { bad: "ErrorAction SilentlyContinue", why: "把失敗藏起來，不是加速" },
  { bad: "PSModuleAutoLoadingPreference = None", why: "後面指令找不到模組" },
  { bad: "1 -shl ProcessorCount（32 位）", why: "超過 31 核溢位，親和性設錯" },
  { bad: "起跑 Forced Gen2 Collect", why: "一開始就停世界，變慢不是變快" },
];

export const LAYERS: { id: AccelLayer; label: string; blurb: string }[] = [
  { id: "pre", label: "減壓", blurb: "只清本行程" },
  { id: "cpu", label: "CPU", blurb: "排程 / 池 / JIT" },
  { id: "mem", label: "記憶體", blurb: "GC / 集合" },
  { id: "parse", label: "解析", blurb: "偵錯 / SIMD / Regex" },
  { id: "io", label: "I/O", blurb: "進度條與編碼" },
  { id: "cross", label: "交叉", blurb: "平行與還原" },
];

export const CPU_POLICY_PS = {
  architecture: "CPU-only · PowerShell 7+",
  priority: "AboveNormal（本 PID）",
  pool: "min=cores · max=min(cores×2, 64)",
  parallel: "ForEach-Object -Parallel",
  gpu: "disabled",
  restore: "Exiting 100% 還原",
};

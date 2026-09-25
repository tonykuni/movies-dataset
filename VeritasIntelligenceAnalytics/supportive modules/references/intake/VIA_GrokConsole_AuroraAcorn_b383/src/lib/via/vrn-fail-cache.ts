/** Extract failure playbook v0100 compact. 不抄引擎全文。 */
export type VrnFail = { id: number; name: string; st: string };
export const VRN_FAIL_N = 15;
export const VRN_FAILS: VrnFail[] = [
  { id: 1, name: "隱形表", st: "IMPLEMENTED" },
  { id: 2, name: "亂碼/Mojibake", st: "IMPLEMENTED" },
  { id: 3, name: "巨型 xlsx OOM", st: "IMPLEMENTED" },
  { id: 4, name: "合併格錯位", st: "IMPLEMENTED" },
  { id: 5, name: "多欄橫讀混行", st: "IMPLEMENTED" },
  { id: 6, name: "頁首頁尾盲區", st: "IMPLEMENTED" },
  { id: 7, name: "原生 binary 依賴", st: "IMPLEMENTED_VARIANT" },
  { id: 8, name: "SharedStrings 膨脹", st: "REGISTERED" },
  { id: 9, name: "格內多行斷列", st: "IMPLEMENTED" },
  { id: 10, name: "巢狀表遞迴", st: "REGISTERED" },
  { id: 11, name: "掃描件歪斜", st: "PARTIAL" },
  { id: 12, name: "zip 炸彈", st: "IMPLEMENTED" },
  { id: 13, name: "加密檔掛死", st: "IMPLEMENTED" },
  { id: 14, name: "浮動圖形文字框", st: "REGISTERED" },
  { id: 15, name: "批次記憶體洩漏", st: "IMPLEMENTED" },
];

/** 旗艦 Mega-Prompt 原文已封。未來動作走綁定，不把「拔除」讀成刪除。DCT 不動。 */
import { AST_ANCHORS } from "./ast-anchor.ts";
import { GOV_ACCEL, GOV_PIPELINES, GOV_ROUNDS, GOV_ZONES } from "./gov-spec.ts";
import type { Light } from "./types.ts";

export const GOV_MEGA_ID = "VIA_MEGA_PROMPT";
export const GOV_MEGA_TITLE = "VIA Central Governance Console：終極旗艦整合版 Mega-Prompt";
export const GOV_MEGA_TITLE_EN =
  "Ultimate Mega-Prompt: SSOT Registry, AST Dual-Mode Anchoring, 20 Accelerators & 6 Unrestricted Pipelines";
export const GOV_MEGA_SEALED = true;
export const GOV_MEGA_WHEN = "2026-09-06";

/** 使用者交存的中文核心大腦指令。執行時 overlay GOV_MEGA_BIND，勿直接「刪 base」。 */
export const GOV_MEGA_PROMPT_ZH = `請啟動「VIA Central Governance Console：全自動沙盒治理與環境修復引擎」，啟用全部 20 個加速器，掛載「中央 SSOT 規範庫、同義字/Regex 治理中心」，對 Base 環境及所有已註冊與動態擴充之子系統（via_core / VRN / VDF / VAP / 新增 via_* 環境）執行標準化部署與穩定化流程。

【核心治理原則與無限制推進指令】
1. 全景式分析與診斷先行：優先啟動全景式分析，調用各類指令與語法識別工具（如 Ruff, PSScriptAnalyzer, Language.Parser 等），對全系統代碼、環境與相依性進行掃描與錯誤分類。
2. AST 雙模錨點定位：針對識別出的問題，動態切換「精準 AST 錨點（精確節點/行號）」或「彈性 AST 錨點（語意特徵簽名）」進行定界鎖定。
3. 六獨立流程無限制推進與錯誤收斂：
  * 後續的「六個獨立流程」若無任何限制，必須在「不損害系統健康、不產生九頭龍連鎖風險（Zero-Hydra Risk）」的絕對前提下，全力同步向前推進到底。
  * 若推進過程中偵測到指令有錯或系統異常，即刻觸發「三輪全景式分析」進行錯誤識別。
  * 識別後，能同步解決的問題（Parallel-Fixable）一口氣全數同時解決；不可同步的問題（Sequence-Dependent）嚴格依賴拓撲順序逐步解決，全程以不影響系統健康、零九頭龍風險為最高依歸。

一、VIA EnvManager 環境治理與 SSOT 中央規範
1. SSOT 規範與同義字 Regex 治理：集中管理跨子系統（VRN/VDF/VAP）命名實體、資料契約、同義字庫與 Regex 規則集（VIA_SSOT_Unified），消除跨模組語意歧義。
2. uv 極速解析與多鏡像源調度：全面調用 uv 解析器與 Local-Free Libs 快篩矩陣。整合清華 (Tsinghua)、阿里 (Aliyun) 及 PyPI 官方鏡像源，即時監測環境健康度。
3. 衝突立拔與動態隔離環境 (via_*)：發現衝突風險立即重建環境並拔除風險因子。高風險函式庫、特定工具鏈或多版本需求（如 Plotly 多版本、C++ 擴展、CUDA 引擎），自動分流建立專屬獨立環境（如 via_lib_plotly_v5, via_engine_cuda12），確保 Base 環境極致精簡最佳化。
4. 非阻塞 PowerShell 啟動器：全流程整合成一支 launch.ps1，背景非同步派工（不關閉、不阻塞、不卡斷）。

二、三輪全景式分析與錯誤識別（異常觸發時執行）
1. 全景式分析 (Panoramic Analysis)：無死角掃描全系統代碼、配置與跨模組呼叫。
2. 全錯誤識別 (Error Identification)：運用各類語法診斷工具進行語法、語意、類型與正則匹配標記。
3. 優化點定位 (Optimization Points)：資源洩漏、複雜度過高與冗餘路徑定位。
4. AST 結構分析 (AST Structural Analysis)：精準與彈性錨點定界。
5. SSOT 對齊檢查 (SSOT Alignment)：驗證中央資料字典一致性。
6. 九頭龍風險偵測 (Hydra Risk Detection)：鎖定高耦合共用依賴節點。
7. 錯誤分類 (Error Classification)：
  * Parallel-Fixable（可同時修正）
  * Sequence-Dependent（需順序修正）
8. 多子系統同步檢視 (Multi-Subsystem Sync)：跨業務模組即時狀態同步。

三、六個獨立流程無限制同步推進 (Six Independent Pipelines)
若無異常，以下六大流程全力同步推進到底：
* Pipeline 1: 代碼層 AST 重構與指令語法修復流程
* Pipeline 2: 中央 SSOT 與同義字 Regex 校準流程
* Pipeline 3: 子系統解耦與動態模組插槽註冊流程
* Pipeline 4: uv 依賴解析、衝突立拔與多環境隔離流程
* Pipeline 5: 沙盒多重驗證、性能優化與回歸測試流程
* Pipeline 6: 自適應 HTML UI Matrix 渲染與非阻塞部署監控流程

四、三輪精準修正策略（嚴格限制最多三輪）
* 第 1 輪：全面性修正（Comprehensive Fix）
  * 針對所有 Parallel-Fixable 問題，一口氣同時並行解決。嚴格隔離高 Hydra 節點。
* 第 2 輪：順序性修正（Sequential Fix）
  * 針對 Sequence-Dependent 問題，依賴拓撲排序逐步沙盒驗證修正。高風險節點僅給予建議。
* 第 3 輪：收尾性修正（Final Polishing）
  * 微調、格式化、刪除死碼、性能極致優化，確保系統穩定乾淨。

五、沙盒驗證與持續穩定循環
每次修正後執行驗證循環：
test → debug → upgrade → test → debug → optimize → test → debug → consolidate → test → debug → user-test → debug
系統正式啟動（Activation）後持續驗證：
activate system → test → debug → until perfect

六、啟用全部 20 個加速器（Accelerators）
1. AST 精準解析加速器
2. 多語言語意模型加速器
3. 九頭龍風險預測加速器
4. 依賴拓撲排序加速器
5. 沙盒隔離執行加速器
6. 自動修正建議生成加速器
7. 三輪全景式分析加速器
8. SSOT 對齊加速器
9. 視覺化矩陣生成加速器
10. 錯誤分類與分群加速器
11. 性能與複雜度分析加速器
12. 多子系統同步檢視加速器
13. 版本差異與回滾加速器
14. 覆蓋率與回歸檢查加速器
15. 修正順序最佳化加速器
16. 動態進度條加速器 (Dynamic Progress Bar)
17. 動態說明加速器 (Dynamic Status Narration)
18. 非阻塞 PowerShell 執行加速器 (Non-Blocking PowerShell)
19. 多引擎整合加速器 (Python + PowerShell + UI)
20. 自動部署與環境初始化加速器 (Auto-Deploy & Init)

七、自動跳出 HTML UI Matrix 報告
* 設計規範：採用略小字體（small font），表格高度與寬度具備自動最佳化（Auto-Optimized Layout），儲存格文字過長時強制自動換行（Auto-Wrap）。
* 四大分區：MODULE / ENGINE / FUNCTION-LIB / OTHERS。
* 矩陣內容：錯誤矩陣、優化矩陣、Hydra 風險矩陣、依賴拓撲矩陣、修正順序矩陣、數量校驗矩陣、SSOT 對照矩陣。包含紅黃綠燈（RYG）健康度指標、動態進度條與動態說明。`;

export type MegaBind = {
  id: string;
  from: string;
  to: string;
  light: Light;
  note: string;
};

/** 原文用語 → 現行契約。未來動作只走 to 欄。 */
export const GOV_MEGA_BIND: MegaBind[] = [
  {
    id: "B_PULL",
    from: "衝突立拔／拔除風險因子／立即重建環境",
    to: "via_iso_* 隔離不刪",
    light: "ok",
    note: "新建隔離槽 · 禁止 conda remove／pip uninstall／刪 base",
  },
  {
    id: "B_PLOTLY",
    from: "via_lib_plotly_v5",
    to: "via_iso_plotly",
    light: "ok",
    note: "已關帳槽 · plotly 5.24.1 只在 iso · 不重做",
  },
  {
    id: "B_CUDA",
    from: "via_engine_cuda12",
    to: "via_iso_cuda（若出現再立槽）",
    light: "warn",
    note: "尚未 pin · 出現衝突才建槽 · 不刪 base",
  },
  {
    id: "B_SIX",
    from: "六獨立流程無限制推進",
    to: "G1–G6 寫區互斥 · Zero-Hydra",
    light: "ok",
    note: "全力同步但 job／winner／write／layer 不互踩",
  },
  {
    id: "B_GA",
    from: "全部 20 個加速器",
    to: "GA-01–20 治理 · PS-01–20 資料分冊",
    light: "ok",
    note: "不混 ID",
  },
  {
    id: "B_AST",
    from: "AST 雙模錨點",
    to: "精準節點／行號 · 彈性語意簽名",
    light: "ok",
    note: "py/ts 精準 · ps1/html/json 彈性 · DCT 不重做",
  },
  {
    id: "B_ROUND",
    from: "三輪精準修正",
    to: "Parallel-Fixable → Sequence-Dependent → Harden",
    light: "ok",
    note: "最多三輪 · 高 Hydra 只隔離建議",
  },
  {
    id: "B_DCT",
    from: "全系統代碼修復到底",
    to: "DCT01–20 已 FIXED · 本輪不重做",
    light: "ok",
    note: "分析 RED 不綁架收官",
  },
  {
    id: "B_LIVE",
    from: "標準化部署與穩定化",
    to: "CACHE 收官 · LIVE 雙閘",
    light: "ok",
    note: "本台不 spawn conda／uv · 閘1 NET 關則零外呼",
  },
  {
    id: "B_UI",
    from: "HTML UI Matrix 四大分區",
    to: GOV_ZONES.join("／"),
    light: "ok",
    note: "小字 · 自動換行 · 紅黃綠 · 唯一 Console",
  },
  {
    id: "B_DEAD",
    from: "第3輪刪除死碼／清理臨時環境",
    to: "不刪檔 · Harden 只鎖 lockfile",
    light: "ok",
    note: "死碼／風險件進 via_iso_* · 功能只增不減",
  },
  {
    id: "B_SLOT",
    from: "via_isolated_*／via_lib_plotly_v*",
    to: "via_iso_*",
    light: "ok",
    note: "槽名正名 · plotly 已在 via_iso_plotly",
  },
  {
    id: "B_UV8",
    from: "uv 極速解析與多鏡像源調度",
    to: "三鏡競向＋UVT-01–08",
    light: "ok",
    note: "清華冠 LKGC 2026-09-06 · 未同意不切鏡",
  },
  {
    id: "B_LOG",
    from: "PREVIOUS LOGS AS LESSON LEARN",
    to: "GOV_LESSONS → 計畫只從 LKGC 擴張",
    light: "ok",
    note: "成功失敗皆入 logs/env_governance.log",
  },
  {
    id: "B_ENVPY",
    from: "VIA_EnvManager.py",
    to: "檢查＋產指令 · 本台不 spawn",
    light: "ok",
    note: "Local-Free · 同意後母機 launch.ps1",
  },
];

export type MegaPipe = {
  id: string;
  pipeline: number;
  long: string;
  write: string;
  winner: string;
};

export const GOV_MEGA_PIPES: MegaPipe[] = [
  { id: "G1", pipeline: 1, long: "代碼層 AST 重構與指令語法修復", write: "ast-src", winner: "VIS-ENV-000001" },
  { id: "G2", pipeline: 2, long: "中央 SSOT 與同義字 Regex 校準", write: "ssot-regex", winner: "VRN_SYN" },
  { id: "G3", pipeline: 3, long: "子系統解耦與動態模組插槽註冊", write: "plug-sub", winner: "VAP_MDL001" },
  { id: "G4", pipeline: 4, long: "uv 依賴解析、衝突立拔與多環境隔離", write: "uv-iso", winner: "SUP_MDL737" },
  { id: "G5", pipeline: 5, long: "沙盒多重驗證、性能優化與回歸測試", write: "sandbox-reg", winner: "VRN_AUDITU" },
  { id: "G6", pipeline: 6, long: "自適應 HTML UI Matrix 渲染與非阻塞部署監控", write: "ui-matrix", winner: "VIA_CGC" },
];

export function megaHydraOk(): boolean {
  const n = GOV_MEGA_PIPES.length;
  const spec = GOV_PIPELINES.length === n;
  const writes = new Set(GOV_MEGA_PIPES.map((p) => p.write)).size === n;
  const ids = GOV_MEGA_PIPES.every((p, i) => p.id === GOV_PIPELINES[i]?.id && p.write === GOV_PIPELINES[i]?.write);
  return spec && writes && ids;
}

export function megaAccelOk(): boolean {
  return GOV_ACCEL.length === 20 && GOV_MEGA_PROMPT_ZH.includes("20. 自動部署與環境初始化加速器");
}

export function megaAstOk(): boolean {
  return AST_ANCHORS.length === 2 && /精準 AST 錨點/.test(GOV_MEGA_PROMPT_ZH) && /彈性 AST 錨點/.test(GOV_MEGA_PROMPT_ZH);
}

export function megaBoundText(): string {
  const binds = GOV_MEGA_BIND.map((b) => `${b.from} → ${b.to} · ${b.note}`).join("\n");
  const pipes = GOV_MEGA_PIPES.map((p) => `${p.id} P${p.pipeline} ${p.long} write=${p.write}`).join("\n");
  const rounds = GOV_ROUNDS.map((r) => `R${r.id} ${r.name}`).join(" → ");
  return [
    `未來動作規範 · ${GOV_MEGA_TITLE} · 已封 ${GOV_MEGA_WHEN}`,
    GOV_MEGA_TITLE_EN,
    "執行 overlay：拔除＝隔離不刪 · 槽名 via_iso_* · DCT 不動 · LIVE 雙閘 · 本台不 spawn · 日誌當教訓 · R3 不刪死碼",
    `綁定：\n${binds}`,
    `六程：\n${pipes}`,
    `三輪：${rounds}`,
    `AST 雙模：${AST_ANCHORS.map((a) => `${a.mode} ${a.tool}`).join(" · ")}`,
    `GA ${GOV_ACCEL.length}/20 · 四分區 ${GOV_ZONES.join("／")}`,
  ].join("\n\n");
}

export function megaSeal(): { id: string; name: string; light: Light; note: string } {
  const ok = GOV_MEGA_SEALED && megaHydraOk() && megaAccelOk() && megaAstOk();
  return {
    id: "MEGA",
    name: GOV_MEGA_TITLE,
    light: ok ? "ok" : "bad",
    note: ok
      ? "已封為未來動作規範 · 拔除＝via_iso_* 不刪 · G1–G6／GA20／AST 雙模對齊 · DCT 不動"
      : "Mega-Prompt 未對齊契約",
  };
}

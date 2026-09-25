/** Mother incoming + NLP OneEngine 1.5.0. Sandbox has no C: drive; fixtures stand in for empty git incoming. */

export const VRN_INCOMING_PATH = "C:\\incoming";
export const VRN_INCOMING_PATHS = [
  "C:\\incoming",
  "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics\\functional modules\\VRN\\input\\incoming",
];
export const VRN_NLP_ENGINE_PATH =
  "C:\\Users\\tonyk\\OneDrive\\Documents\\VIA Super HTML Parser\\VIA_NLP_OneEngine_v1.5.0";
export const VRN_NLP_ENGINE_REF =
  "functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0";

export const INCOMING_TEXT: Record<string, string> = {
  "GS-2330 台積電_20251130.pdf": `標題: 台積電(2330.TW) 維持買進
券商: Goldman Sachs
日期: 2025-11-30
目標價: 1450元
評價方式: PE
基於: 3nm／CoWoS 產能滿載假設
2024 稀釋每股盈餘 45.25
2025 稀釋每股盈餘 52.0
2026 稀釋每股盈餘 61.0
2027 稀釋每股盈餘 70.0
主要原因: AI 相關需求與先進封裝擴產
投資結論: 買進 · 目標價上修，不另發明評等。
成長動能: 3nm / CoWoS 產能滿載。
財務: 見損益／資負／現金流表。
同業: 對照三星／英特爾先進製程。
風險: 地緣與資本支出節奏。
先進製程市占與資本支出節奏仍是首頁敘事核心，本點不另發明數字。
客戶庫存與海外建廠時程構成第二段正文，僅引用原句。
| 科目 | 2024 |
| --- | --- |
| 營業收入合計 | 2894.3 |
| 營業利益 | 1350.6 |
| 本期淨利 | 1173.3 |
| 稀釋每股盈餘 | 45.25 |
| 現金及約當現金 | 2120.0 |
| 資產總額 | 6690.0 |
| 權益總額 | 4260.0 |
| 營業活動現金流 | 1820.4 |
| 自由現金流量 | 980.2 |
`,
  "台積電_2024Q4_法人說明會.pdf": `標題: 台積電 2024Q4 法說
日期: 2024-12-31
投資結論: 公司展望未在檔名評等 · 不發明。
成長動能: AI 相關需求延續。
財務: 季報口徑對 AnnualExtract。
同業: 未給正式同業表 · 不發明。
風險: 指引區間。
營業收入合計: 868.5
營業利益: 406.2
本期淨利: 374.7
`,
  "2330_FY2024_annual_report.pdf": `標題: 台積電 2024 年報
日期: 2024-12-31
投資結論: 年報無券商評等 · 不發明。
成長動能: 年報經營層討論。
財務: 完整三表。
同業: 不發明。
風險: 年報風險章節。
| 科目 | FY2024 |
| --- | --- |
| 營業收入合計 | 2894.3 |
| 營業利益 | 1350.6 |
| 本期淨利 | 1173.3 |
| 現金及約當現金 | 2120.0 |
| 資產總額 | 6690.0 |
| 權益總額 | 4260.0 |
| 營業活動現金流 | 1820.4 |
| 自由現金流量 | 980.2 |
`,
  "income_2330_fy2024.xlsx": `科目,FY2024
營業收入合計,2894.3
營業利益,1350.6
本期淨利,1173.3
稀釋每股盈餘,45.25
`,
  "cashflow_2330_fy2024.xlsx": `科目,FY2024
營業活動現金流,1820.4
自由現金流量,980.2
`,
  "0050_holdings_20260331.csv": `ticker,name,weight
2330,台積電,47.2
2317,鴻海,4.1
2454,聯發科,3.8
`,
};

export function incomingText(name: string): string {
  return INCOMING_TEXT[name] ?? "";
}

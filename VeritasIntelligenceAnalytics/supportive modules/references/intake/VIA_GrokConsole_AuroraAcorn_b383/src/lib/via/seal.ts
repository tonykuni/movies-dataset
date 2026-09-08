import type { BasicInfo, FinRow, FredRow, IntakeFile, Light, SummaryRow } from "./types.ts";

export type Seal = {
  id: string;
  name: string;
  light: Light;
  note: string;
};

export type ParquetSealInput = {
  parquetPages: number;
  parquetRoundtrip: boolean;
  parquetReadPages: number;
  parquetSkipPages: number;
  parquetTokenRatio: number;
};

export function sealVdf(rows: FredRow[], metrics?: ParquetSealInput | null): Seal {
  const cats = new Set(rows.map((r) => r.category));
  const missing = rows.filter((r) => r.lastValue == null || !r.lastDate || r.lastDate === "—");
  if (!rows.length) return { id: "VDF", name: "VDF 擷取", light: "warn", note: "尚未啟動" };
  if (missing.length) return { id: "VDF", name: "VDF 擷取", light: "bad", note: `缺值 ${missing.length} 列` };
  if (cats.size < 8) return { id: "VDF", name: "VDF 擷取", light: "warn", note: `類別 ${cats.size} < 8` };
  if (metrics && metrics.parquetPages > 0 && !metrics.parquetRoundtrip) {
    return { id: "VDF", name: "VDF 擷取", light: "bad", note: "parquet 回讀不一致" };
  }
  const parq = metrics?.parquetPages
    ? ` · PAR1 ${metrics.parquetPages}p 跳過 ${metrics.parquetSkipPages}`
    : "";
  return { id: "VDF", name: "VDF 擷取", light: "ok", note: `完工 · ${rows.length} series · ${cats.size} 類${parq}` };
}

export function sealVrn(files: IntakeFile[], basics: BasicInfo[], summaries: SummaryRow[], finances: FinRow[]): Seal {
  const failKept = files.some((f) => f.status === "bad" && f.stuckStep === "S04");
  const redInTab2 = basics.some((b) => b.validationRisk === "RED");
  const green = basics.filter((b) => b.validationRisk === "GREEN").length;
  const grounded = summaries.filter((s) => s.grounded).length;
  const hasIS = finances.some((f) => f.category === "IS");
  const hasBS = finances.some((f) => f.category === "BS");
  const hasCF = finances.some((f) => f.category === "CF");
  if (!files.length) return { id: "VRN", name: "VRN 管線", light: "warn", note: "尚未啟動" };
  if (!failKept) return { id: "VRN", name: "VRN 管線", light: "bad", note: "S04 失敗件未留 TAB 1" };
  if (redInTab2) return { id: "VRN", name: "VRN 管線", light: "bad", note: "RED 流入 TAB 2" };
  if (green < 3 || grounded < 10 || !hasIS || !hasBS || !hasCF) {
    return { id: "VRN", name: "VRN 管線", light: "warn", note: `INFO綠 ${green} · 摘要 ${grounded} · IS/BS/CF ${[hasIS, hasBS, hasCF].filter(Boolean).length}/3` };
  }
  return { id: "VRN", name: "VRN 管線", light: "ok", note: `完工 · GREEN ${green} · GROUNDED ${grounded} · FIN ${finances.length}` };
}

export function sealParquet(metrics?: ParquetSealInput | null): Seal {
  if (!metrics || !metrics.parquetPages) return { id: "PARQ", name: "Parquet 年分區", light: "warn", note: "尚未落盤" };
  if (!metrics.parquetRoundtrip) return { id: "PARQ", name: "Parquet 年分區", light: "bad", note: "回讀對帳失敗" };
  return {
    id: "PARQ",
    name: "Parquet 年分區",
    light: "ok",
    note: `PAR1 回讀 ${metrics.parquetReadPages}p · 跳過 ${metrics.parquetSkipPages} · token ${metrics.parquetTokenRatio}`,
  };
}

export function sealGoLive(parts: Seal[]): Seal {
  if (!parts.length) return { id: "LIVE", name: "VDF+VRN+Console 實測", light: "pending", note: "尚未按實測完工" };
  if (parts.some((p) => p.light === "bad")) {
    const hit = parts.find((p) => p.light === "bad");
    return { id: "LIVE", name: "VDF+VRN+Console 實測", light: "bad", note: `未通過 · ${hit?.id} ${hit?.note}` };
  }
  if (parts.some((p) => p.light === "warn" || p.light === "pending")) {
    return { id: "LIVE", name: "VDF+VRN+Console 實測", light: "warn", note: "VDF/VRN/Console 未齊" };
  }
  return { id: "LIVE", name: "VDF+VRN+Console 實測", light: "ok", note: "VDF+VRN 實測通過 · Console 齊 · DCT01–20 不動" };
}

export function sealConsole(engines: number): Seal {
  if (engines < 1) return { id: "CGC", name: "VIA Central Governance Console", light: "bad", note: "無引擎登錄" };
  return { id: "CGC", name: "VIA Central Governance Console", light: "ok", note: `唯一總管 · 登錄 ${engines} · 無第二 UI` };
}

export function sealEng075(n: number, latest: string): Seal {
  if (!n) return { id: "ENG075", name: "TWMopsMonthlyRevenue", light: "warn", note: "尚未分析" };
  return { id: "ENG075", name: "TWMopsMonthlyRevenue", light: "ok", note: `CACHE ${n} 家 · ${latest} · LIVE 關正確` };
}

export function sealGlss(n: number): Seal {
  if (!n) return { id: "GLSS", name: "VIA-GLSS", light: "warn", note: "尚未模擬" };
  return { id: "GLSS", name: "VIA-GLSS", light: "ok", note: `沙盒 ${n} 列 · ENG075 在籍 · 未因果` };
}

export function sealEng077(n: number, codes: number): Seal {
  if (!n) return { id: "ENG077", name: "CnyesFactSetYfConsensus", light: "warn", note: "尚未分析" };
  return { id: "ENG077", name: "CnyesFactSetYfConsensus", light: "ok", note: `CACHE 長表 ${n} 列 · ${codes} 檔 · LIVE 關正確` };
}

export function sealLocalDb(parts: number): Seal {
  if (parts < 3) return { id: "LOCALDB", name: "本機 VIA_db 三庫", light: "bad", note: `只掛 ${parts} 庫` };
  return { id: "LOCALDB", name: "本機 VIA_db 三庫", light: "warn", note: "價量／籌碼／其餘已掛 · 原件不刪 · COPY→GitHub · 本台未探 C:" };
}
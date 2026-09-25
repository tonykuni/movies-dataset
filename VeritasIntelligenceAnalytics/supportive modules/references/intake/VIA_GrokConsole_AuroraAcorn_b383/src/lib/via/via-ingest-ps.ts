/** 母機已在 PS 專案根。scripts\ 檔不在磁碟 → 貼 VIA-CmdMatrix.ps1。 */
export const INGEST_PS_REL = "scripts/VIA-Ingest-2023.ps1";
export const INGEST_PS_CMD = "scripts\\VIA-Ingest-2023.cmd";
export const ENTER_PS_REL = "scripts/VIA-Enter-Root.ps1";
export const ENTER_PS_CMD = "scripts\\VIA-Enter-Root.cmd";
export const MATRIX_PS_REL = "scripts/VIA-CmdMatrix.ps1";

export function ingestCmdOneLiner(): string {
  return [
    "cd /d %USERPROFILE%\\movies-dataset\\VeritasIntelligenceAnalytics",
    "pwsh -NoLogo -NoExit",
  ].join("\n");
}

export function ingestRunCommand(): string {
  return [
    "# 已在 PS 母目錄。scripts\\VIA-Enter-Root.ps1 不在磁碟。",
    "# 貼 scripts/VIA-CmdMatrix.ps1 整段，或：",
    "via-enter",
    "via-matrix",
    "via-ingest",
    "# 矩陣上方鎖定短指令 · 視窗自動長寬 · 禁網 · COPY_ONLY",
  ].join("\n");
}

export function ingestRunNote(): string {
  return "PS 專案內貼 VIA-CmdMatrix · 短指令上方鎖定 · 自動長寬";
}

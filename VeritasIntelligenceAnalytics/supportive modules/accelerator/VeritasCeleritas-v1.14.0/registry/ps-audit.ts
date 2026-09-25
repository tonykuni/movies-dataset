export type FindingSev = "must" | "forbid" | "ok";

export type PsFinding = {
  id: string;
  sev: FindingSev;
  rule: string;
  detail: string;
  hit: boolean;
};

export type PsFileKind = "origin" | "template" | "ai-raw" | "joined";

export type PsFile = {
  id: string;
  name: string;
  kind: PsFileKind;
  intent: string;
  source: string;
};

export type PsAudit = {
  file: PsFile;
  joined: boolean;
  restore: boolean;
  requires7: boolean;
  forbidden: number;
  score: number;
  verdict: "pass" | "join" | "block";
  findings: PsFinding[];
  functions: string[];
};

const MARKER = "CELERITAS-TEMPLATE-JOIN";

const MUST: { id: string; re: RegExp; rule: string; detail: string }[] = [
  { id: "requires", re: /#Requires\s+-Version\s+7/i, rule: "PS7 閘門", detail: "#Requires -Version 7.0" },
  { id: "restore", re: /Restore-CeleritasPS7|Register-EngineEvent[\s\S]{0,80}Exiting|Invoke-CeleritasGenerated/i, rule: "關閉即還原", detail: "Restore-CeleritasPS7 或 Exiting 事件" },
  { id: "join", re: /CELERITAS-TEMPLATE-JOIN|VeritasCeleritas\.PS7(\.Template)?\.ps1|Start-CeleritasPS7/i, rule: "接入模板", detail: "點來源模板或本棧" },
];

const FORBID: { id: string; re: RegExp; rule: string; detail: string }[] = [
  { id: "ews", re: /::EmptyWorkingSet|EmptyWorkingSet\s*\(/i, rule: "禁掃全機", detail: "EmptyWorkingSet()" },
  { id: "hi", re: /PriorityClass\s*=\s*['\"]?(High|Realtime)/i, rule: "禁超高優先權", detail: "High / Realtime" },
  { id: "pool", re: /SetMaxThreads\([^)]*32767/i, rule: "禁無上限執行緒池", detail: "32767" },
  { id: "iex", re: /\bIEX\b|Invoke-Expression/i, rule: "禁動態執行", detail: "IEX / Invoke-Expression" },
  { id: "dl", re: /DownloadString|Net\.WebClient/i, rule: "禁遠端下載執行", detail: "DownloadString" },
  { id: "hklm", re: /HKLM:\\|Set-ItemProperty[^\n]*HKLM/i, rule: "禁改登錄檔", detail: "HKLM" },
  { id: "stop", re: /Stop-Process\s+(?!-Id\s*\$PID)/i, rule: "禁殺其他進程", detail: "Stop-Process" },
];

export const PS_FILES: PsFile[] = [
  {
    id: "origin",
    name: "VeritasCeleritas.PS7.ps1",
    kind: "origin",
    intent: "本棧源頭",
    source: `#Requires -Version 7.0
function Restore-CeleritasPS7 { }
function Start-CeleritasPS7 { }
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Restore-CeleritasPS7 }
[void](Start-CeleritasPS7)`,
  },
  {
    id: "template",
    name: "VeritasCeleritas.PS7.Template.ps1",
    kind: "template",
    intent: "生成接入模板",
    source: `# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
. (Join-Path $PSScriptRoot 'VeritasCeleritas.PS7.ps1')
if (-not $script:CeleritasPS7.Applied) { [void](Start-CeleritasPS7) }
function Invoke-CeleritasGenerated { param([scriptblock]$Body) try { & $Body } finally { Restore-CeleritasPS7 } }`,
  },
  {
    id: "raw-quotes",
    name: "Fetch-Quotes.ps1",
    kind: "ai-raw",
    intent: "AI 裸生成 · 價量",
    source: `param($Tickers)
$raw = Invoke-WebRequest https://example/quotes
$raw.Content | ConvertFrom-Json
IEX $raw.Headers.Hint`,
  },
  {
    id: "raw-mem",
    name: "Sweep-Memory.ps1",
    kind: "ai-raw",
    intent: "AI 裸生成 · 記憶體",
    source: `#Requires -Version 5.1
Get-Process | ForEach-Object { $_.PriorityClass = 'BelowNormal' }
[void][Kernel32]::EmptyWorkingSet($_.Handle)
$p = Get-Process -Id $PID; $p.PriorityClass = 'High'`,
  },
  {
    id: "raw-reg",
    name: "Tune-Machine.ps1",
    kind: "ai-raw",
    intent: "AI 裸生成 · 系統",
    source: `Set-ItemProperty HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager -Name Celeritas -Value 1
Stop-Process -Name explorer
[void][System.Threading.ThreadPool]::SetMaxThreads(32767, 32767)`,
  },
  {
    id: "joined-report",
    name: "Write-DailyMatrix.ps1",
    kind: "joined",
    intent: "已接入 · 日報矩陣",
    source: `# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
. (Join-Path $PSScriptRoot 'VeritasCeleritas.PS7.Template.ps1')
Invoke-CeleritasGenerated -Body {
  $rows = 1..30 | ForEach-Object -Parallel { $_ * $_ }
  Write-CeleritasReport
}`,
  },
];

export function joinTemplate(name: string, body: string): string {
  const inner = body
    .split("\n")
    .map((l) => (l.length ? `    ${l}` : l))
    .join("\n");
  return [
    `# CELERITAS-TEMPLATE-JOIN v1`,
    `#Requires -Version 7.0`,
    `# generated: ${name}`,
    `# AI 產出必須接入模板。只動 $PID，關閉即還原。`,
    `. (Join-Path $PSScriptRoot 'VeritasCeleritas.PS7.Template.ps1')`,
    ``,
    `Invoke-CeleritasGenerated -Body {`,
    inner,
    `}`,
  ].join("\n");
}

export function auditPs(file: PsFile): PsAudit {
  const src = file.source;
  const code = src
    .split("\n")
    .filter((l) => !l.trim().startsWith("#"))
    .join("\n");
  const findings: PsFinding[] = [];

  for (const r of MUST) {
    const hit = r.re.test(src);
    findings.push({ id: r.id, sev: "must", rule: r.rule, detail: r.detail, hit });
  }
  for (const r of FORBID) {
    const hit = r.re.test(code);
    findings.push({ id: r.id, sev: "forbid", rule: r.rule, detail: r.detail, hit });
  }

  const functions = Array.from(src.matchAll(/function\s+([\w-]+)/gi)).map((m) => m[1]!);
  const requires7 = findings.some((f) => f.id === "requires" && f.hit);
  const restore = findings.some((f) => f.id === "restore" && f.hit);
  const joined =
    file.kind === "origin" ||
    file.kind === "template" ||
    src.includes(MARKER) ||
    /VeritasCeleritas\.PS7(\.Template)?\.ps1|Start-CeleritasPS7/i.test(src);
  const forbidden = findings.filter((f) => f.sev === "forbid" && f.hit).length;
  const missing = findings.filter((f) => f.sev === "must" && !f.hit).length;
  let score = 100 - missing * 22 - forbidden * 28;
  if (score < 0) score = 0;
  if (joined && forbidden === 0 && missing === 0) score = 100;

  let verdict: PsAudit["verdict"] = "pass";
  if (forbidden > 0) verdict = "block";
  else if (!joined || missing > 0) verdict = "join";

  return { file, joined, restore, requires7, forbidden, score, verdict, findings, functions };
}

export function generateJoined(file: PsFile): PsFile {
  const stripped = file.source
    .replace(/\bIEX\b[^\n]*/gi, "# shielded: IEX")
    .replace(/Invoke-Expression[^\n]*/gi, "# shielded: Invoke-Expression")
    .replace(/EmptyWorkingSet[^\n]*/gi, "# shielded: EmptyWorkingSet")
    .replace(/PriorityClass\s*=\s*['\"]?(High|Realtime)['\"]?/gi, "PriorityClass = 'AboveNormal'")
    .replace(/SetMaxThreads\([^)]*32767[^)]*\)/gi, "SetMaxThreads(64, 64)")
    .replace(/Set-ItemProperty[^\n]*HKLM[^\n]*/gi, "# shielded: HKLM")
    .replace(/Stop-Process\s+-Name[^\n]*/gi, "# shielded: Stop-Process")
    .replace(/#Requires\s+-Version\s+5\.1/gi, "#Requires -Version 7.0");
  return {
    ...file,
    id: `${file.id}-joined`,
    kind: "joined",
    intent: `已接入 · ${file.intent.replace(/^AI 裸生成 · /, "")}`,
    name: file.name.replace(/\.ps1$/i, ".Joined.ps1"),
    source: joinTemplate(file.name, stripped),
  };
}

export const TEMPLATE_FILE = "/VeritasCeleritas.PS7.Template.ps1";

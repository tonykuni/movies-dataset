#requires -Version 7.0
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
<#
================================================================================
 Invoke-VIA-SSOT-Manager-v0100.ps1
 VERITAS INTELLIGENCE ANALYTICS  ·  VIA VisualDesignOps / VDF / VRN  SSOT Manager
--------------------------------------------------------------------------------
 Single tool to validate, bridge-check, export, version-bump and visually
 maintain SSOT_VIA_VisualDesignOps_20260617.json.

 Safety policy (aligned with VeritasNexusCore):
   def no exit / no Stop-Process / no destructive delete
   def copy-only freeze, SHA256 verification, report generation
   def edits write to the SSOT registry, never to source code or frozen engines
   def supportive modules are bridged read-heavy / dry-run, never executed here
   def PowerShell session remains open

 Actions:
   Launch    Build the VisualMaintainer HTML (SSOT injected) and open it. [default]
   Validate  L0/L1 schema + integrity (SHA256) + row counts -> JSON/CSV/HTML.
   Bridge    Existence + size + sha12 of supportive modules (dry-run).
   Export    CSV + HTML summaries of every matrix (read-only).
   Bump      Bump content_version, rewrite PS-native integrity, archive old copy.
   Matrix    Print the safe-action matrix.

 Example:
   pwsh -NoProfile -ExecutionPolicy Bypass -File "Invoke-VIA-SSOT-Manager-v0100.ps1" -Action Launch -OpenReport
================================================================================
#>
param(
    [ValidateSet("Launch","Validate","Bridge","Export","Bump","Matrix")]
    [string]$Action = "Launch",

    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",

    [string]$SsotPath = "",

    [string]$OutDir = "",

    [ValidateSet("major","minor","patch")]
    [string]$BumpPart = "patch",

    [switch]$OpenReport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def PARAMS
# =============================================================================
$def_STAMP   = Get-Date -Format "yyyyMMdd_HHmmss"
$def_SCRIPT_DIR = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }

if ([string]::IsNullOrWhiteSpace($OutDir)) {
    $OutDir = Join-Path $BaseDir ("_ssot_runs\RUN_" + $def_STAMP)
}
$def_LOG_DIR    = Join-Path $OutDir "_logs"
$def_REPORT_DIR = Join-Path $OutDir "_reports"
$def_REGISTRY_DIR = Join-Path $OutDir "_ssot_registry"
$def_ARCHIVE_DIR  = Join-Path $OutDir "_archive"
$def_LOG = Join-Path $def_LOG_DIR "SSOT_MANAGER.log"

$def_REQUIRED_KEYS = @(
    "meta","authority_tiers","input_parameters","ticker_rules","vdf_contracts",
    "macro_contracts","global_comparable_macro","vrn_contracts","validation_contract",
    "visual_lock","component_taxonomy","template_library","html_ui_spec","supportive_bridge"
)

# =============================================================================
# def UTIL
# =============================================================================
function def_WriteLine {
    param([string]$Level,[string]$Message)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$ts] [$Level] $Message"
    $color = "Gray"
    if ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "FAIL") { $color = "Red" }
    elseif ($Level -eq "RUN") { $color = "Cyan" }
    Write-Host $line -ForegroundColor $color
    if (Test-Path -LiteralPath $def_LOG_DIR) {
        Add-Content -LiteralPath $def_LOG -Value $line -Encoding UTF8
    }
}
function def_EnsureDir { param([string]$Path) if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }
function def_EnsureDirs {
    foreach ($d in @($OutDir,$def_LOG_DIR,$def_REPORT_DIR,$def_REGISTRY_DIR,$def_ARCHIVE_DIR)) { def_EnsureDir -Path $d }
}
function def_WriteText { param([string]$Path,[string]$Text) [System.IO.File]::WriteAllText($Path,$Text,[System.Text.UTF8Encoding]::new($false)) }
function def_WriteJson { param([string]$Path,[object]$Obj) def_WriteText -Path $Path -Text ($Obj | ConvertTo-Json -Depth 100) }
function def_Html { param([AllowNull()][string]$Text) if ($null -eq $Text) { return "" } return [System.Net.WebUtility]::HtmlEncode($Text) }
function def_Hash {
    param([string]$Path)
    try { if (-not [System.IO.File]::Exists($Path)) { return "" } return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLower() }
    catch { return "HASH_ERROR" }
}
function def_Sha12 { param([string]$Path) $h = def_Hash $Path; if ($h.Length -ge 12) { return $h.Substring(0,12) } else { return $h } }
function def_Csv { param([object]$Value) $s = if ($null -eq $Value) { "" } else { [string]$Value }; if ($s -match '[",\r\n]') { '"' + $s.Replace('"','""') + '"' } else { $s } }

function def_ResolveSsot {
    if ($SsotPath -and (Test-Path -LiteralPath $SsotPath)) { return (Resolve-Path -LiteralPath $SsotPath).Path }
    $candidates = @(
        (Join-Path $def_SCRIPT_DIR "SSOT_VIA_VisualDesignOps_20260617.json"),
        (Join-Path $BaseDir "supportive modules\SSOT_VIA_VisualDesignOps_20260617.json"),
        (Join-Path $BaseDir "SSOT_VIA_VisualDesignOps_20260617.json")
    )
    foreach ($c in $candidates) { if (Test-Path -LiteralPath $c) { return $c } }
    # latest dated SSOT next to script
    $glob = Get-ChildItem -LiteralPath $def_SCRIPT_DIR -Filter "SSOT_VIA_VisualDesignOps_*.json" -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | Select-Object -First 1
    if ($glob) { return $glob.FullName }
    return ""
}
function def_LoadSsotText { param([string]$Path) return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8) }
function def_LoadSsotObj  { param([string]$Path) return (def_LoadSsotText $Path | ConvertFrom-Json) }

# PS-native canonical integrity: mask integrity hash, ConvertTo-Json -Compress, SHA256 of UTF8 bytes.
function def_PsIntegrity {
    param([string]$Path)
    $o = def_LoadSsotObj $Path
    if ($o.PSObject.Properties.Name -contains "meta" -and $o.meta.PSObject.Properties.Name -contains "integrity") {
        $o.meta.integrity.sha256_of_body = ""
    }
    $canon = $o | ConvertTo-Json -Depth 100 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($canon)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hash = ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
    return $hash
}

function def_ReportHtml {
    param([string]$Title,[string]$Subtitle,[array]$Sections,[string]$OutPath)
    # Sections: array of @{ name=...; rows=[pscustomobject] }
    $sb = [System.Text.StringBuilder]::new()
    foreach ($sec in $Sections) {
        [void]$sb.Append("<div class='card'><div class='ct'>" + (def_Html $sec.name) + "</div>")
        if ($sec.rows -and $sec.rows.Count -gt 0) {
            $cols = $sec.rows[0].PSObject.Properties.Name
            [void]$sb.Append("<table><thead><tr>")
            foreach ($c in $cols) { [void]$sb.Append("<th>" + (def_Html $c) + "</th>") }
            [void]$sb.Append("</tr></thead><tbody>")
            foreach ($r in $sec.rows) {
                [void]$sb.Append("<tr>")
                foreach ($c in $cols) {
                    $val = [string]$r.$c
                    $cls = ""
                    if ($val -match '^(OK|PASS|GREEN|READY|LOW|ACTIVATE|CLEAN)$') { $cls = "g" }
                    elseif ($val -match '^(WARN|YELLOW|REVIEW|MEDIUM)$') { $cls = "y" }
                    elseif ($val -match '^(FAIL|RED|HIGH|ERROR|MISSING|BLOCK)$') { $cls = "r" }
                    if ($cls) { [void]$sb.Append("<td><span class='b $cls'>" + (def_Html $val) + "</span></td>") }
                    else { [void]$sb.Append("<td>" + (def_Html $val) + "</td>") }
                }
                [void]$sb.Append("</tr>")
            }
            [void]$sb.Append("</tbody></table>")
        }
        [void]$sb.Append("</div>")
    }
    $html = @"
<!doctype html><html><head><meta charset="utf-8"><title>$Title</title>
<style>
body{font-family:"DM Sans",Segoe UI,system-ui,sans-serif;background:#0e1519;color:#eef3f5;margin:0;padding:26px}
h1{font-family:"Syne",sans-serif;font-size:22px;margin:0 0 2px}
.sub{font-family:"DM Mono",monospace;color:#7f939d;font-size:11px;letter-spacing:.08em;margin-bottom:18px}
.card{background:#18232b;border:1px solid #2a3b46;border-radius:13px;margin:0 0 18px;overflow:hidden}
.ct{font-family:"DM Mono",monospace;font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;color:#aebdc4;padding:12px 14px;border-bottom:1px solid #223139}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{font-family:"DM Mono",monospace;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:#7f939d;text-align:left;padding:8px 12px;border-bottom:1px solid #2a3b46}
td{padding:8px 12px;border-bottom:1px solid #223139;vertical-align:top}
.b{font-family:"DM Mono",monospace;font-size:10px;padding:2px 8px;border-radius:999px;border:1px solid #2a3b46}
.b.g{color:#8fe3bd;border-color:rgba(46,158,107,.5);background:rgba(46,158,107,.12)}
.b.y{color:#ecd57d;border-color:rgba(201,162,39,.5);background:rgba(201,162,39,.12)}
.b.r{color:#f0a9a4;border-color:rgba(207,91,84,.5);background:rgba(207,91,84,.12)}
</style></head><body>
<h1>$Title</h1><div class="sub">$Subtitle</div>
$($sb.ToString())
</body></html>
"@
    def_WriteText -Path $OutPath -Text $html
}

# =============================================================================
# def EMBEDDED MAINTAINER TEMPLATE  (single-quoted here-string, literal)
# =============================================================================
$def_TEMPLATE = @'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA SSOT VisualMaintainer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  /* VisualLock tokens — SSOT-locked, do not edit */
  --lock-primary:#4c78a8;
  --lock-neutral:#9c9890;
  --lock-accent:#439a9a;
  /* console ground */
  --ground:#0e1519;
  --ground-2:#131c22;
  --surface:#18232b;
  --surface-2:#1e2c35;
  --line:#2a3b46;
  --line-soft:#223139;
  --ink:#eef3f5;
  --ink-dim:#aebdc4;
  --ink-faint:#7f939d;
  --g:#2e9e6b; --y:#c9a227; --r:#cf5b54; --lock:#9c9890;
  --mono:"DM Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --sans:"DM Sans",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  --disp:"Syne",var(--sans);
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{
  background:
    radial-gradient(1100px 540px at 88% -8%, rgba(67,154,154,.10), transparent 60%),
    radial-gradient(900px 520px at -6% 4%, rgba(76,120,168,.12), transparent 55%),
    var(--ground);
  color:var(--ink);font-family:var(--sans);font-size:14px;line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.app{display:grid;grid-template-columns:248px 1fr;grid-template-rows:auto 1fr;min-height:100vh}

/* masthead */
header.mast{
  grid-column:1/3;display:flex;align-items:center;gap:20px;flex-wrap:wrap;
  padding:14px 22px;border-bottom:1px solid var(--line);
  background:linear-gradient(180deg,var(--ground-2),rgba(19,28,34,.55));
  position:sticky;top:0;z-index:30;backdrop-filter:blur(6px);
}
.brand{display:flex;align-items:center;gap:13px;min-width:max-content}
.seal{width:34px;height:34px;border-radius:9px;flex:0 0 auto;
  background:conic-gradient(from 210deg,var(--lock-primary),var(--lock-accent),var(--lock-neutral),var(--lock-primary));
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.12), 0 2px 14px rgba(67,154,154,.25);
  position:relative}
.seal::after{content:"";position:absolute;inset:8px;border-radius:4px;background:var(--ground);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.10)}
.brand h1{font-family:var(--disp);font-weight:800;font-size:15px;letter-spacing:.04em;margin:0;line-height:1.05}
.brand .sub{font-family:var(--mono);font-size:10.5px;color:var(--ink-faint);letter-spacing:.08em;text-transform:uppercase}
.mast .stats{display:flex;gap:16px;flex-wrap:wrap;margin-left:6px}
.stat{display:flex;flex-direction:column;gap:1px}
.stat .k{font-family:var(--mono);font-size:9.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-faint)}
.stat .v{font-family:var(--mono);font-size:12.5px;color:var(--ink)}
.mast .spacer{flex:1 1 auto}
.tier-pick{display:flex;align-items:center;gap:8px}
.tier-pick label{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-faint)}
select,.btn{font-family:var(--mono);font-size:12px}
select{background:var(--surface);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 9px}
.btn{background:var(--surface-2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 13px;cursor:pointer;transition:.15s}
.btn:hover{border-color:var(--lock-accent);color:#fff}
.btn.primary{background:linear-gradient(180deg,var(--lock-primary),#3f6692);border-color:transparent;color:#fff}
.btn.primary:hover{filter:brightness(1.08)}
.btn.ghost{background:transparent}

/* nav rail */
nav.rail{border-right:1px solid var(--line);background:var(--ground-2);padding:14px 10px;overflow:auto}
nav .grp{font-family:var(--mono);font-size:9.5px;letter-spacing:.15em;text-transform:uppercase;color:var(--ink-faint);padding:14px 12px 6px}
nav a{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:9px;color:var(--ink-dim);
  text-decoration:none;cursor:pointer;font-size:13px;border:1px solid transparent;transition:.13s}
nav a .idx{font-family:var(--mono);font-size:10px;color:var(--ink-faint);width:18px;text-align:right}
nav a:hover{background:var(--surface);color:var(--ink)}
nav a.active{background:var(--surface-2);border-color:var(--line);color:#fff}
nav a.active .idx{color:var(--lock-accent)}

/* main */
main{padding:24px 28px 60px;overflow:auto}
.view{display:none;animation:fade .25s ease}
.view.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.view-head{display:flex;align-items:baseline;gap:14px;margin:0 0 4px}
.view-head h2{font-family:var(--disp);font-weight:700;font-size:21px;letter-spacing:.01em;margin:0}
.view-head .eyebrow{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--lock-accent)}
.view-sub{color:var(--ink-faint);font-size:12.5px;margin:0 0 20px;max-width:70ch}

.card{background:linear-gradient(180deg,var(--surface),var(--ground-2));border:1px solid var(--line);
  border-radius:14px;padding:4px;margin:0 0 22px;overflow:hidden}
.card > .card-title{font-family:var(--mono);font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;
  color:var(--ink-dim);padding:13px 14px 9px;display:flex;align-items:center;gap:9px}
.card > .card-title .count{margin-left:auto;color:var(--ink-faint)}

table{width:100%;border-collapse:collapse;font-size:12.5px}
th{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-faint);
  text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--ground-2);z-index:1}
td{padding:9px 12px;border-bottom:1px solid var(--line-soft);vertical-align:top}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(76,120,168,.06)}
td.key{font-family:var(--mono);color:var(--ink);white-space:nowrap}
td.note{color:var(--ink-faint);font-size:11.5px}
td.mono,.mono{font-family:var(--mono)}
.val-input{font-family:var(--mono);font-size:12px;width:100%;min-width:90px;background:var(--ground);color:var(--ink);
  border:1px solid var(--line);border-radius:7px;padding:6px 8px}
.val-input:focus{outline:none;border-color:var(--lock-accent)}
.val-input:disabled{opacity:.55;cursor:not-allowed;background:var(--ground-2)}
tr.dirty td:first-child{box-shadow:inset 3px 0 0 var(--lock-accent)}

.badge{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);font-size:10px;letter-spacing:.05em;
  padding:3px 8px;border-radius:999px;border:1px solid var(--line);color:var(--ink-dim);white-space:nowrap}
.badge.g{color:#8fe3bd;border-color:rgba(46,158,107,.5);background:rgba(46,158,107,.12)}
.badge.y{color:#ecd57d;border-color:rgba(201,162,39,.5);background:rgba(201,162,39,.12)}
.badge.r{color:#f0a9a4;border-color:rgba(207,91,84,.5);background:rgba(207,91,84,.12)}
.badge.lock{color:#d6cfc6;border-color:rgba(156,152,144,.55);background:rgba(156,152,144,.14)}
.badge.tier{color:#bcd2ec;border-color:rgba(76,120,168,.5);background:rgba(76,120,168,.12)}
.badge.acc{color:#a3e0e0;border-color:rgba(67,154,154,.5);background:rgba(67,154,154,.12)}

/* lock toggle */
.lk{display:inline-flex;align-items:center;gap:7px;cursor:pointer;user-select:none}
.lk .dot{width:30px;height:17px;border-radius:999px;background:var(--ground);border:1px solid var(--line);position:relative;transition:.15s}
.lk .dot::after{content:"";position:absolute;top:1.5px;left:2px;width:12px;height:12px;border-radius:50%;
  background:var(--ink-faint);transition:.15s}
.lk.on .dot{background:rgba(156,152,144,.3);border-color:var(--lock)}
.lk.on .dot::after{left:14px;background:var(--lock)}
.lk .txt{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-faint)}
.shield{color:var(--y)}

/* overview kpis */
.kpis{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin:0 0 22px}
.kpi{background:linear-gradient(180deg,var(--surface),var(--ground-2));border:1px solid var(--line);border-radius:13px;padding:14px}
.kpi .n{font-family:var(--disp);font-weight:700;font-size:26px;line-height:1}
.kpi .l{font-family:var(--mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint);margin-top:7px}

/* validation ladder (signature) */
.ladder{display:flex;flex-direction:column;gap:0;padding:8px 6px 14px}
.rung{display:grid;grid-template-columns:62px 1fr;gap:14px;position:relative;padding:11px 10px}
.rung::before{content:"";position:absolute;left:31px;top:0;bottom:0;width:2px;background:var(--line)}
.rung:first-child::before{top:50%}
.rung:last-child::before{bottom:50%}
.rung .lv{position:relative;z-index:1;justify-self:center;align-self:start;font-family:var(--mono);font-weight:500;
  width:46px;height:46px;border-radius:12px;display:grid;place-items:center;font-size:13px;
  background:var(--surface-2);border:1px solid var(--line);color:var(--ink)}
.rung[data-gate="hard"] .lv{border-color:var(--lock-primary);box-shadow:0 0 0 3px rgba(76,120,168,.14)}
.rung[data-gate="review"] .lv{border-color:var(--y);box-shadow:0 0 0 3px rgba(201,162,39,.12)}
.rung[data-gate="activate"] .lv{border-color:var(--lock-accent);box-shadow:0 0 0 3px rgba(67,154,154,.16)}
.rung .body{padding-top:2px}
.rung .name{font-weight:600;font-size:14px}
.rung .pair{display:flex;gap:22px;flex-wrap:wrap;margin-top:5px;font-size:12px;color:var(--ink-dim)}
.rung .pair b{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-faint);font-weight:500;margin-right:6px}

/* tokens */
.swatches{display:flex;gap:14px;flex-wrap:wrap;padding:14px}
.sw{border:1px solid var(--line);border-radius:12px;overflow:hidden;width:150px}
.sw .chip{height:64px}
.sw .meta{padding:9px 11px;font-family:var(--mono);font-size:11px}
.sw .meta .nm{color:var(--ink);text-transform:uppercase;letter-spacing:.08em;font-size:9.5px;color:var(--ink-faint)}
.sw .meta .hex{color:var(--ink)}
.fontrow{display:flex;gap:14px;flex-wrap:wrap;padding:0 14px 14px}
.fontcard{border:1px solid var(--line);border-radius:12px;padding:14px 16px;flex:1 1 180px}
.fontcard .role{font-family:var(--mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-faint)}
.fontcard .samp{font-size:24px;margin-top:6px}
.chips{display:flex;gap:8px;flex-wrap:wrap;padding:0 14px 14px}

/* region cards */
.regions{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;padding:14px}
.region{border:1px solid var(--line);border-radius:12px;padding:13px 14px;background:var(--ground-2)}
.region h4{margin:0 0 8px;font-family:var(--disp);font-weight:700;font-size:15px;display:flex;align-items:center;gap:8px}
.region .field{display:flex;justify-content:space-between;gap:10px;font-size:11.5px;padding:3px 0;border-bottom:1px dashed var(--line-soft)}
.region .field b{font-family:var(--mono);font-size:10px;color:var(--ink-faint);font-weight:500}
.region .field span{font-family:var(--mono);color:var(--ink-dim);text-align:right}
.region .special{margin-top:8px;font-size:11px;color:var(--ink-faint)}

/* bridge */
.bridge-item{border:1px solid var(--line);border-radius:12px;padding:13px 14px;margin:10px 14px;background:var(--ground-2)}
.bridge-item .role{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--lock-accent)}
.bridge-item .path{font-family:var(--mono);font-size:11.5px;color:var(--ink-dim);word-break:break-all;margin:5px 0}
.cmd{display:flex;gap:8px;align-items:center;margin-top:7px}
.cmd code{flex:1;font-family:var(--mono);font-size:11px;background:var(--ground);border:1px solid var(--line);
  border-radius:7px;padding:7px 9px;color:var(--ink-dim);word-break:break-all}

/* toolbar */
.toolbar{position:sticky;bottom:0;grid-column:1/3;display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  padding:12px 22px;border-top:1px solid var(--line);background:rgba(14,21,25,.92);backdrop-filter:blur(6px);z-index:25}
.toolbar .status{font-family:var(--mono);font-size:11px;color:var(--ink-faint)}
.toolbar .spacer{flex:1}
.dirtycount{color:var(--lock-accent)}

/* modal */
.scrim{position:fixed;inset:0;background:rgba(6,10,12,.66);display:none;place-items:center;z-index:60}
.scrim.on{display:grid}
.modal{width:min(440px,92vw);background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px 22px;
  box-shadow:0 22px 60px rgba(0,0,0,.5)}
.modal h3{margin:0 0 4px;font-family:var(--disp);font-weight:700}
.modal p{color:var(--ink-dim);font-size:13px;margin:0 0 14px}
.modal .field{font-family:var(--mono);font-size:11px;color:var(--y);margin-bottom:6px}
.modal input[type=text]{width:100%;font-family:var(--mono);font-size:13px;background:var(--ground);color:var(--ink);
  border:1px solid var(--line);border-radius:8px;padding:9px 10px;margin-bottom:14px}
.modal .row{display:flex;gap:10px;justify-content:flex-end}
.hidden{display:none!important}
::-webkit-scrollbar{width:11px;height:11px}::-webkit-scrollbar-thumb{background:var(--line);border-radius:99px;border:3px solid var(--ground-2)}
</style>
</head>
<body>
<div class="app">
  <header class="mast">
    <div class="brand">
      <div class="seal"></div>
      <div>
        <h1>SSOT VisualMaintainer</h1>
        <div class="sub" id="m-ssotid">SSOT</div>
      </div>
    </div>
    <div class="stats">
      <div class="stat"><span class="k">Schema</span><span class="v" id="m-schema">–</span></div>
      <div class="stat"><span class="k">Content</span><span class="v" id="m-content">–</span></div>
      <div class="stat"><span class="k">Integrity</span><span class="v" id="m-sha">–</span></div>
      <div class="stat"><span class="k">Run Mode</span><span class="v" id="m-runmode">–</span></div>
      <div class="stat"><span class="k">Rounds</span><span class="v" id="m-rounds">–</span></div>
    </div>
    <div class="spacer"></div>
    <div class="tier-pick">
      <label for="tier">Acting as</label>
      <select id="tier">
        <option value="Operator">Operator</option>
        <option value="Maintainer">Maintainer</option>
        <option value="Architect">Architect</option>
      </select>
    </div>
  </header>

  <nav class="rail" id="rail"></nav>
  <main id="main"></main>

  <div class="toolbar">
    <span class="status" id="status">Loaded.</span>
    <span class="status">Dirty edits: <span class="dirtycount" id="dirty">0</span></span>
    <span class="spacer"></span>
    <label class="btn ghost" for="loadfile">Load SSOT JSON…</label>
    <input id="loadfile" type="file" accept=".json,application/json" class="hidden">
    <button class="btn" id="copycmd">Copy launch command</button>
    <button class="btn primary" id="export">Export updated SSOT JSON</button>
  </div>
</div>

<div class="scrim" id="scrim">
  <div class="modal">
    <h3 id="mod-title">Confirm protected change</h3>
    <p id="mod-body">This toggle is high-risk and requires dual confirmation.</p>
    <div class="field" id="mod-field"></div>
    <input type="text" id="mod-input" placeholder="Type CONFIRM to proceed" autocomplete="off">
    <div class="row">
      <button class="btn ghost" id="mod-cancel">Cancel</button>
      <button class="btn primary" id="mod-ok">Proceed</button>
    </div>
  </div>
</div>

<script id="ssot-data" type="application/json">"__SSOT_DATA__"</script>
<script>
"use strict";

/* ----- load SSOT (injected by PowerShell launcher, or via file picker) ----- */
let SSOT = null;
try {
  const raw = document.getElementById("ssot-data").textContent;
  const parsed = JSON.parse(raw);
  SSOT = (parsed && parsed.meta) ? parsed : null;
} catch(e){ SSOT = null; }

const dirty = new Set();
const TIERRANK = {Operator:1, Maintainer:2, Architect:3};
let actingTier = "Operator";

const el = (t,c,txt)=>{const n=document.createElement(t); if(c)n.className=c; if(txt!=null)n.textContent=txt; return n;};
const badge = (txt,cls)=>{const b=el("span","badge "+(cls||""),txt); return b;};
const riskClass = v => ({LOW:"g",MEDIUM:"y",HIGH:"r"}[String(v).toUpperCase()]||"");
const resultClass = v => {const s=String(v).toUpperCase(); if(/GREEN|PASS|ACTIVATE/.test(s))return"g"; if(/YELLOW|REVIEW/.test(s))return"y"; if(/RED|FAIL|HOLD/.test(s))return"r"; return"";};

/* ----- tabs ----- */
const TABS = (SSOT && SSOT.html_ui_spec && SSOT.html_ui_spec.tabs) ? SSOT.html_ui_spec.tabs : [];
function buildRail(){
  const rail = document.getElementById("rail");
  rail.innerHTML="";
  rail.appendChild(el("div","grp","Governance Console"));
  TABS.forEach((t,i)=>{
    const a = el("a"); a.dataset.tab=t.id;
    a.appendChild(el("span","idx", String(i).padStart(2,"0")));
    a.appendChild(el("span",null,t.title));
    a.onclick=()=>activate(t.id);
    rail.appendChild(a);
  });
}
function activate(id){
  document.querySelectorAll("nav a").forEach(a=>a.classList.toggle("active",a.dataset.tab===id));
  document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.id==="view-"+id));
  document.getElementById("main").scrollTop=0;
}

/* ----- generic renderers ----- */
function viewShell(id,title,eyebrow,sub){
  const v = el("section","view"); v.id="view-"+id;
  const h = el("div","view-head");
  h.appendChild(el("span","eyebrow",eyebrow||""));
  h.appendChild(el("h2",null,title));
  v.appendChild(h);
  if(sub){ v.appendChild(el("p","view-sub",sub)); }
  return v;
}
function card(title,count){
  const c = el("div","card");
  if(title){
    const t = el("div","card-title"); t.appendChild(el("span",null,title));
    if(count!=null) t.appendChild(el("span","count",count+" rows"));
    c.appendChild(t);
  }
  return c;
}
function tableFrom(rows, cols){
  const tbl = el("table");
  const thead = el("thead"); const htr = el("tr");
  cols.forEach(c=>htr.appendChild(el("th",null,c.h))); thead.appendChild(htr); tbl.appendChild(thead);
  const tb = el("tbody");
  rows.forEach(r=>{
    const tr = el("tr");
    cols.forEach(c=>{ tr.appendChild(c.render(r)); });
    tb.appendChild(tr);
  });
  tbl.appendChild(tb);
  return tbl;
}
function txtCell(val,cls){ const td=el("td",cls); td.textContent=(val==null?"":String(val)); return td; }
function badgeCell(val,cls){ const td=el("td"); if(val!=null&&val!=="") td.appendChild(badge(String(val),cls)); return td; }

/* ----- editable parameter rows ----- */
function paramTable(groupKey, rows){
  const cols = [
    {h:"Parameter", render:r=>txtCell(r.key,"key")},
    {h:"Value", render:r=>{
        const td = el("td");
        const locked = !!r.locked;
        const allowed = TIERRANK[actingTier] >= TIERRANK[r.authority];
        if(typeof r.default === "boolean"){
          const sel = el("select"); ["true","false"].forEach(o=>{const op=el("option",null,o);op.value=o;sel.appendChild(op);});
          sel.value = String(r.value);
          sel.disabled = locked || !allowed;
          sel.onchange = ()=>commit(groupKey,r,sel.value==="true", td);
          td.appendChild(sel);
        } else if(Array.isArray(r.options)){
          const sel = el("select"); r.options.forEach(o=>{const op=el("option",null,o);op.value=o;sel.appendChild(op);});
          sel.value = String(r.value); sel.disabled = locked || !allowed;
          sel.onchange = ()=>commit(groupKey,r,sel.value,td);
          td.appendChild(sel);
        } else {
          const inp = el("input","val-input"); inp.value = String(r.value);
          inp.disabled = locked || !allowed;
          inp.onchange = ()=>{ let v=inp.value; if(typeof r.default==="number"){const n=Number(v); v=isNaN(n)?r.value:n; inp.value=v;} commit(groupKey,r,v,td); };
          td.appendChild(inp);
        }
        if(!allowed && !locked){ const b=badge(r.authority+"+","tier"); b.style.marginLeft="8px"; td.appendChild(b); }
        return td;
    }},
    {h:"Authority", render:r=>badgeCell(r.authority,"tier")},
    {h:"Lock", render:r=>{
        const td = el("td");
        const wrap = el("span","lk"+(r.locked?" on":""));
        wrap.appendChild(el("span","dot"));
        wrap.appendChild(el("span","txt", r.protected?"protected":"lock"));
        if(r.protected){ const s=el("span","shield"," ⬡"); wrap.insertBefore(s,wrap.firstChild); }
        wrap.onclick = ()=>toggleLock(groupKey,r,wrap,td);
        td.appendChild(wrap);
        return td;
    }},
    {h:"Note", render:r=>txtCell(r.note,"note")},
  ];
  return tableFrom(rows,cols);
}
function rowEl(td){ return td.closest("tr"); }
function markDirty(groupKey,r,td){ const id=groupKey+":"+r.key; dirty.add(id); const tr=rowEl(td); if(tr)tr.classList.add("dirty"); document.getElementById("dirty").textContent=dirty.size; }
function commit(groupKey,r,v,td){ r.value=v; markDirty(groupKey,r,td); setStatus("Edited "+r.key+" → "+v); }
function toggleLock(groupKey,r,wrap,td){
  const turningOn = !r.locked;
  const apply = ()=>{ r.locked=turningOn; wrap.classList.toggle("on",turningOn); markDirty(groupKey,r,td); reRenderParams(); setStatus((turningOn?"Locked ":"Unlocked ")+r.key); };
  if(r.protected){
    confirmModal("Protected lock: "+r.key,
      "This parameter is high-risk ("+r.note+"). Enabling/locking requires dual confirmation.",
      r.key, apply);
  } else { apply(); }
}

/* ----- protected confirm modal ----- */
let _modalAction=null;
function confirmModal(title,body,field,onok){
  document.getElementById("mod-title").textContent=title;
  document.getElementById("mod-body").textContent=body;
  document.getElementById("mod-field").textContent=field?("Target: "+field):"";
  const inp=document.getElementById("mod-input"); inp.value="";
  _modalAction=onok;
  document.getElementById("scrim").classList.add("on"); inp.focus();
}
function closeModal(){ document.getElementById("scrim").classList.remove("on"); _modalAction=null; }

/* ----- build all views ----- */
function buildViews(){
  const main = document.getElementById("main"); main.innerHTML="";
  TABS.forEach(t=>{ const fn = VIEWS[t.id]; main.appendChild(fn ? fn(t) : viewShell(t.id,t.title,t.id,t.use)); });
  if(TABS[0]) activate(TABS[0].id);
}
function reRenderParams(){ /* rebuild only the input_parameters view to reflect lock/disable state */
  const old=document.getElementById("view-input_parameters"); if(!old)return;
  const fresh=VIEWS.input_parameters({title:"Input Parameters",use:""});
  fresh.classList.add("active"); old.replaceWith(fresh);
}

const VIEWS = {
  overview(t){
    const v = viewShell("overview","System Overview","SSOT · "+SSOT.meta.ssot_id,
      "Single source of truth for VIA VisualDesignOps, VDF / VRN dataset contracts, ticker rules, validation, and VisualLock. Edits stay in this registry — never written back to source.");
    const counts = {
      "Input parameters": Object.values(SSOT.input_parameters).reduce((a,b)=>a+b.length,0),
      "VDF contract rows": Object.values(SSOT.vdf_contracts).reduce((a,b)=>a+b.length,0),
      "Macro rows": Object.values(SSOT.macro_contracts).reduce((a,b)=>a+b.length,0),
      "VRN rows": Object.values(SSOT.vrn_contracts).reduce((a,b)=>a+b.length,0),
      "Validation levels": SSOT.validation_contract.length,
      "Templates": SSOT.template_library.length,
    };
    const kp = el("div","kpis");
    Object.entries(counts).forEach(([l,n])=>{ const k=el("div","kpi"); k.appendChild(el("div","n",String(n))); k.appendChild(el("div","l",l)); kp.appendChild(k); });
    v.appendChild(kp);

    const pc = card("Run Policy");
    const ptbl = el("table"); const tb=el("tbody");
    Object.entries(SSOT.meta.policy).forEach(([k,val])=>{
      if(typeof val==="object") return;
      const tr=el("tr"); tr.appendChild(txtCell(k,"key")); tr.appendChild(txtCell(val,"mono")); tb.appendChild(tr);
    });
    ptbl.appendChild(tb); pc.appendChild(ptbl); v.appendChild(pc);

    const ac = card("Authority Tiers", SSOT.authority_tiers.length);
    ac.appendChild(tableFrom(SSOT.authority_tiers,[
      {h:"Tier",render:r=>badgeCell(r.tier,"tier")},
      {h:"Rank",render:r=>txtCell(r.rank,"mono")},
      {h:"Can edit",render:r=>txtCell((r.can_edit||[]).join(", "),"note")},
      {h:"Note",render:r=>txtCell(r.note,"note")},
    ]));
    v.appendChild(ac);
    return v;
  },
  input_parameters(t){
    const v = viewShell("input_parameters","Input Parameters","Parameter Registry",
      SSOT.html_ui_spec.principles[0]+" Edit rights follow the acting tier; protected toggles require dual confirmation.");
    const labels = {paths:"Paths", run_mode:"Run Mode", vdf_params:"VDF Parameters", vrn_params:"VRN Parameters"};
    Object.entries(SSOT.input_parameters).forEach(([gk,rows])=>{
      const c = card(labels[gk]||gk, rows.length);
      c.appendChild(paramTable(gk,rows));
      v.appendChild(c);
    });
    return v;
  },
  vdf_contracts(t){
    const v = viewShell("vdf_contracts","VDF Dataset Contract","Market Facts · Verifiable",
      "Market fact data. P1 source wins; fallback only fills gaps. VDF never overwrites VRN broker views.");
    const labels={tw_stock_daily:"TW Stock Daily",tw_chips:"TW Chips",tw_index:"TW Index / Breadth",etf_universe:"ETF Universe",etf_daily:"ETF Daily / NAV / Flow"};
    Object.entries(SSOT.vdf_contracts).forEach(([gk,rows])=>{
      const c=card(labels[gk]||gk,rows.length);
      c.appendChild(tableFrom(rows,[
        {h:"Category",render:r=>badgeCell(r.category,"acc")},
        {h:"Item",render:r=>txtCell(r.item,"key")},
        {h:"Scope",render:r=>txtCell(r.scope,"note")},
        {h:"P1 Source",render:r=>txtCell(r.p1_source,"mono")},
        {h:"Fallback",render:r=>txtCell(r.fallback,"note")},
        {h:"Freq",render:r=>txtCell(r.frequency,"mono")},
        {h:"Table",render:r=>txtCell(r.table,"mono")},
        {h:"Validation",render:r=>txtCell(r.validation,"note")},
      ]));
      v.appendChild(c);
    });
    return v;
  },
  vrn_contracts(t){
    const v = viewShell("vrn_contracts","VRN Dataset Contract","Broker Reports · Views",
      "Broker PDF report views. Rating and Target Price are never overwritten by external data. Forecasts stay separate from VDF actuals.");
    const bc=card("BasicInfo",SSOT.vrn_contracts.basic_info.length);
    bc.appendChild(tableFrom(SSOT.vrn_contracts.basic_info,[
      {h:"Field",render:r=>txtCell(r.field,"key")},
      {h:"P1 Source",render:r=>txtCell(r.p1_source,"mono")},
      {h:"Validation Source",render:r=>txtCell(r.validation_source,"note")},
      {h:"Rule",render:r=>txtCell(r.rule,"note")},
    ]));
    v.appendChild(bc);
    const fc=card("FinancialData",SSOT.vrn_contracts.financial_data.length);
    fc.appendChild(tableFrom(SSOT.vrn_contracts.financial_data,[
      {h:"Section",render:r=>badgeCell(r.section,"tier")},
      {h:"Item",render:r=>txtCell(r.item,"key")},
      {h:"P1",render:r=>txtCell(r.p1,"mono")},
      {h:"Validation",render:r=>txtCell(r.validation,"note")},
      {h:"Rule",render:r=>txtCell(r.rule,"note")},
    ]));
    v.appendChild(fc);
    return v;
  },
  ticker_rules(t){
    const v = viewShell("ticker_rules","Ticker Rules","Normalization SSOT",
      "TW ticker, yfinance, Bloomberg and filename parsing. These rules gate VDF, VRN and ETF identity resolution.");
    const tw=SSOT.ticker_rules.tw_ticker;
    const c=card("TW_TICKER");
    const tbl=el("table"); const tb=el("tbody");
    const rowKV=(k,val)=>{const tr=el("tr"); tr.appendChild(txtCell(k,"key")); const td=el("td","mono"); td.textContent=typeof val==="object"?JSON.stringify(val):String(val); tr.appendChild(td); tb.appendChild(tr);};
    Object.entries(tw).forEach(([k,val])=>rowKV(k,val));
    tbl.appendChild(tb); c.appendChild(tbl); v.appendChild(c);
    const fc=card("Filename Tokens",SSOT.ticker_rules.filename_tokens.length);
    fc.appendChild(tableFrom(SSOT.ticker_rules.filename_tokens,[
      {h:"Type",render:r=>badgeCell(r.type,"acc")},
      {h:"Rule",render:r=>txtCell(r.rule,"mono")},
      {h:"Priority",render:r=>txtCell(r.priority,"mono")},
      {h:"Note",render:r=>txtCell(r.note,"note")},
    ]));
    v.appendChild(fc);
    return v;
  },
  macro_contracts(t){
    const v = viewShell("macro_contracts","Macro & Global","US Core + Global Comparable",
      "US is the most complete core; other regions capture comparable fields plus region-specific signals.");
    const labels={us_leading:"US Leading Indicators",us_inflation:"US Inflation (CPI/PCE/PPI)",us_employment:"US Employment",us_fiscal_rates:"US Fiscal / Rates / Fed"};
    Object.entries(SSOT.macro_contracts).forEach(([gk,rows])=>{
      const c=card(labels[gk]||gk,rows.length);
      c.appendChild(tableFrom(rows,[
        {h:"Layer",render:r=>txtCell(r.layer,"mono")},
        {h:"Category",render:r=>badgeCell(r.category,"acc")},
        {h:"Item",render:r=>txtCell(r.item,"key")},
        {h:"Sources",render:r=>txtCell(r.sources,"mono")},
        {h:"Freq",render:r=>txtCell(r.frequency,"mono")},
        {h:"Use",render:r=>txtCell(r.use,"note")},
      ]));
      v.appendChild(c);
    });
    const gc=card("Global Comparable Regions");
    gc.appendChild((()=>{ const wrap=el("div","chips");
      SSOT.global_comparable_macro.core_fields.forEach(f=>wrap.appendChild(badge(f,"")));
      return wrap; })());
    const reg=el("div","regions");
    Object.entries(SSOT.global_comparable_macro.regions).forEach(([name,info])=>{
      const r=el("div","region"); r.appendChild(el("h4",null,name));
      ["policy","10y","fx","equity"].forEach(f=>{ if(info[f]!=null){ const fr=el("div","field"); fr.appendChild(el("b",null,f)); fr.appendChild(el("span",null,info[f])); r.appendChild(fr);} });
      if(info.special){ const s=el("div","special"); s.textContent="special: "+info.special.join(", "); r.appendChild(s); }
      reg.appendChild(r);
    });
    gc.appendChild(reg); v.appendChild(gc);
    return v;
  },
  validation(t){
    const v = viewShell("validation","Validation Matrix","L0 → L9 Activation Ladder",
      "Each level gates the next. Hard gates (L0/L1) must pass; review gates raise flags; activation requires zero high-risk.");
    const c=card("Validation Ladder");
    const ladder=el("div","ladder");
    SSOT.validation_contract.forEach(lvl=>{
      const gate = /L0|L1/.test(lvl.level)?"hard": /L8|L9/.test(lvl.level)?"activate":"review";
      const rung=el("div","rung"); rung.dataset.gate=gate;
      rung.appendChild(el("div","lv",lvl.level));
      const body=el("div","body");
      const nm=el("div","name"); nm.appendChild(document.createTextNode(lvl.name+"  "));
      nm.appendChild(badge(lvl.result, resultClass(lvl.result))); body.appendChild(nm);
      const pair=el("div","pair");
      const vdf=el("span"); vdf.appendChild(el("b",null,"VDF")); vdf.appendChild(document.createTextNode(lvl.vdf)); pair.appendChild(vdf);
      const vrn=el("span"); vrn.appendChild(el("b",null,"VRN")); vrn.appendChild(document.createTextNode(lvl.vrn)); pair.appendChild(vrn);
      body.appendChild(pair); rung.appendChild(body); ladder.appendChild(rung);
    });
    c.appendChild(ladder); v.appendChild(c);
    return v;
  },
  visual_lock(t){
    const v = viewShell("visual_lock","VisualLock","Locked Tokens · Templates",
      "Color and type tokens locked across the platform. Components and templates extend, never break the core.");
    const tc=card("Locked Tokens");
    const sw=el("div","swatches");
    Object.entries(SSOT.visual_lock.tokens.color).forEach(([nm,hex])=>{
      const s=el("div","sw"); const chip=el("div","chip"); chip.style.background=hex; s.appendChild(chip);
      const m=el("div","meta"); m.appendChild(el("div","nm",nm)); m.appendChild(el("div","hex",hex)); s.appendChild(m); sw.appendChild(s);
    });
    tc.appendChild(sw);
    const fr=el("div","fontrow");
    const fmap={mono:'"DM Mono",monospace',sans:'"DM Sans",sans-serif',display:'"Syne",sans-serif'};
    Object.entries(SSOT.visual_lock.tokens.font).forEach(([role,fam])=>{
      const f=el("div","fontcard"); f.appendChild(el("div","role",role)); const s=el("div","samp",fam); s.style.fontFamily=fmap[role]||"inherit"; f.appendChild(s);
      const lbl=el("div","note"); lbl.style.fontFamily="var(--mono)"; lbl.style.fontSize="11px"; lbl.style.marginTop="6px"; lbl.textContent="Aa Bb Cc 0123"; lbl.style.fontFamily=fmap[role]; f.appendChild(lbl);
      fr.appendChild(f);
    });
    tc.appendChild(fr); v.appendChild(tc);

    const mc=card("Lock Markers");
    const ch=el("div","chips"); SSOT.visual_lock.lock_markers.forEach(m=>ch.appendChild(badge(m,"lock"))); mc.appendChild(ch);
    mc.appendChild(tableFrom(SSOT.visual_lock.lock_layers,[
      {h:"Layer",render:r=>badgeCell(r.layer,"lock")},
      {h:"Scope",render:r=>txtCell(r.scope,"note")},
    ]));
    v.appendChild(mc);

    const lc=card("Component Taxonomy",SSOT.component_taxonomy.length);
    lc.appendChild(tableFrom(SSOT.component_taxonomy,[
      {h:"Class",render:r=>badgeCell(r.class,"acc")},
      {h:"Use",render:r=>txtCell(r.use,"note")},
    ]));
    v.appendChild(lc);

    const pc=card("Template Library",SSOT.template_library.length);
    pc.appendChild(tableFrom(SSOT.template_library,[
      {h:"Template",render:r=>txtCell(r.id,"key")},
      {h:"Required Specs",render:r=>{ const td=el("td"); r.required.forEach(s=>{const b=badge(s,"");b.style.margin="2px 4px 2px 0";td.appendChild(b);}); return td; }},
    ]));
    v.appendChild(pc);
    return v;
  },
  bridge(t){
    const v = viewShell("bridge","Supportive Bridge","Read-heavy · Dry-run",
      "NexusCore, PolyglotCheck and README are bridged for existence + hash checks only. The maintainer never executes them or writes back to frozen engines.");
    const c=card("Bridged Modules ("+SSOT.supportive_bridge.mode+")");
    SSOT.supportive_bridge.modules.forEach(m=>{
      const it=el("div","bridge-item");
      it.appendChild(el("div","role",m.role));
      it.appendChild(el("div","path",m.path));
      if(m.suggested_command){
        const cmd=el("div","cmd"); const code=el("code",null,m.suggested_command.replace("<path>",m.path));
        const b=el("button","btn ghost","Copy"); b.onclick=()=>copy(code.textContent,b);
        cmd.appendChild(code); cmd.appendChild(b); it.appendChild(cmd);
      }
      c.appendChild(it);
    });
    v.appendChild(c);
    const rc=card("Bridge Rules");
    const ul=el("div"); ul.style.padding="6px 14px 14px";
    SSOT.supportive_bridge.rules.forEach(r=>{ const p=el("div","note"); p.style.padding="4px 0"; p.textContent="• "+r; ul.appendChild(p); });
    rc.appendChild(ul); v.appendChild(rc);
    return v;
  },
  activation(t){
    const v = viewShell("activation","Activation Gate","User-test → Activate",
      "Final readiness summary. Activation is a record of intent in this SSOT; it triggers no execution here.");
    const c=card("Readiness");
    const tbl=el("table"); const tb=el("tbody");
    const rm = findParam("run_mode","RUN_MODE");
    const rows=[
      ["Run mode", rm?rm.value:"—"],
      ["Source patch", SSOT.meta.policy.source_patch],
      ["DB write", SSOT.meta.policy.db_write],
      ["High-risk protected toggles enabled", String(countProtectedOn())],
      ["Dirty edits pending export", String(dirty.size)],
    ];
    rows.forEach(([k,val])=>{ const tr=el("tr"); tr.appendChild(txtCell(k,"key")); const td=el("td"); td.appendChild(badge(String(val), /0|dry_run|DISABLED|FORBIDDEN|user_test/.test(String(val))?"g":"y")); tr.appendChild(td); tb.appendChild(tr); });
    tbl.appendChild(tb); c.appendChild(tbl);
    const note=el("div","note"); note.style.padding="12px 14px"; note.textContent="Activation principle: high-risk count must be 0 and edits exported before promoting RUN_MODE to execute.";
    c.appendChild(note); v.appendChild(c);
    return v;
  },
};

function findParam(group,key){ const g=SSOT.input_parameters[group]; return g?g.find(r=>r.key===key):null; }
function countProtectedOn(){ let n=0; Object.values(SSOT.input_parameters).forEach(g=>g.forEach(r=>{ if(r.protected && (r.value===true)) n++; })); return n; }

/* ----- masthead ----- */
function fillMast(){
  const m=SSOT.meta;
  document.getElementById("m-ssotid").textContent=m.ssot_id;
  document.getElementById("m-schema").textContent=m.schema_version;
  document.getElementById("m-content").textContent=m.content_version;
  document.getElementById("m-sha").textContent=(m.integrity.sha256_of_body||"").slice(0,12)||"–";
  const rm=findParam("run_mode","RUN_MODE"); document.getElementById("m-runmode").textContent=rm?rm.value:"–";
  document.getElementById("m-rounds").textContent=String(m.rounds);
}

/* ----- canonical hash (mirrors py sort_keys + compact) ----- */
function sortValue(x){
  if(Array.isArray(x)) return x.map(sortValue);
  if(x && typeof x==="object"){ const o={}; Object.keys(x).sort().forEach(k=>o[k]=sortValue(x[k])); return o; }
  return x;
}
async function recomputeIntegrity(obj){
  const body={}; Object.keys(obj).forEach(k=>{ if(k!=="meta") body[k]=obj[k]; });
  const canon=JSON.stringify(sortValue(body));
  const buf=new TextEncoder().encode(canon);
  const dig=await crypto.subtle.digest("SHA-256",buf);
  return Array.from(new Uint8Array(dig)).map(b=>b.toString(16).padStart(2,"0")).join("");
}

/* ----- export ----- */
async function exportSSOT(){
  const out=JSON.parse(JSON.stringify(SSOT));
  // bump content version patch
  const parts=(out.meta.content_version||"0.0.0").split(".").map(n=>parseInt(n,10)||0);
  parts[2]=(parts[2]||0)+1; out.meta.content_version=parts.join(".");
  out.meta.generated=new Date().toISOString();
  out.meta.integrity.canonical="js_json_sorted_compact";
  out.meta.integrity.note="Rewritten by VisualMaintainer export. JS canonical sorted-compact SHA-256 over body.";
  try{ out.meta.integrity.sha256_of_body=await recomputeIntegrity(out); }catch(e){ out.meta.integrity.sha256_of_body="HASH_UNAVAILABLE_OFFLINE"; }
  const stamp=new Date().toISOString().replace(/[-:T]/g,"").slice(0,15);
  const name="SSOT_VIA_VisualDesignOps_"+stamp+"_v"+out.meta.content_version.replace(/\./g,"")+".json";
  const blob=new Blob([JSON.stringify(out,null,2)],{type:"application/json"});
  const a=el("a"); a.href=URL.createObjectURL(blob); a.download=name; a.click();
  URL.revokeObjectURL(a.href);
  dirty.clear(); document.getElementById("dirty").textContent="0";
  document.querySelectorAll("tr.dirty").forEach(tr=>tr.classList.remove("dirty"));
  SSOT.meta.content_version=out.meta.content_version; SSOT.meta.integrity=out.meta.integrity; fillMast();
  setStatus("Exported "+name+" (content v"+out.meta.content_version+")");
}

/* ----- misc ----- */
function setStatus(s){ document.getElementById("status").textContent=s; }
function copy(text,btn){ navigator.clipboard?.writeText(text).then(()=>{ const o=btn.textContent; btn.textContent="Copied"; setTimeout(()=>btn.textContent=o,1100); }).catch(()=>{}); }

function wire(){
  document.getElementById("tier").onchange=(e)=>{ actingTier=e.target.value; reRenderParams(); setStatus("Acting as "+actingTier); };
  document.getElementById("export").onclick=exportSSOT;
  document.getElementById("copycmd").onclick=(e)=>copy('pwsh -NoProfile -ExecutionPolicy Bypass -File "Invoke-VIA-SSOT-Manager-v0100.ps1" -Action Launch -OpenReport', e.target);
  document.getElementById("mod-cancel").onclick=closeModal;
  document.getElementById("mod-ok").onclick=()=>{ const v=document.getElementById("mod-input").value.trim().toUpperCase(); if(v==="CONFIRM"){ const a=_modalAction; closeModal(); if(a)a(); } else { document.getElementById("mod-input").style.borderColor="var(--r)"; } };
  document.getElementById("scrim").onclick=(e)=>{ if(e.target.id==="scrim") closeModal(); };
  document.getElementById("loadfile").onchange=(e)=>{
    const f=e.target.files[0]; if(!f)return; const rd=new FileReader();
    rd.onload=()=>{ try{ const j=JSON.parse(rd.result); if(!j.meta) throw new Error("not an SSOT"); SSOT=j; boot(); setStatus("Loaded "+f.name); }catch(err){ setStatus("Load failed: "+err.message); } };
    rd.readAsText(f);
  };
}

function boot(){ buildRail(); buildViews(); fillMast(); }

if(SSOT){ wire(); boot(); }
else {
  document.getElementById("main").innerHTML='<section class="view active"><div class="view-head"><span class="eyebrow">No data</span><h2>Load an SSOT JSON</h2></div><p class="view-sub">No SSOT was injected. Use “Load SSOT JSON…” in the toolbar to open SSOT_VIA_VisualDesignOps_20260617.json.</p></section>';
  wire();
}
</script>
</body>
</html>

'@

# =============================================================================
# def ACTIONS
# =============================================================================
function def_Action_Matrix {
    $rows = @(
        [pscustomobject]@{ Action="Launch";   Safe=$true;  Writes="HTML maintainer"; Risk="LOW"; Rule="Injects SSOT, opens UI." }
        [pscustomobject]@{ Action="Validate"; Safe=$true;  Writes="reports";         Risk="LOW"; Rule="Schema + integrity only." }
        [pscustomobject]@{ Action="Bridge";   Safe=$true;  Writes="reports";         Risk="LOW"; Rule="Existence + sha12 dry-run." }
        [pscustomobject]@{ Action="Export";   Safe=$true;  Writes="csv/html";        Risk="LOW"; Rule="Read-only matrices." }
        [pscustomobject]@{ Action="Bump";     Safe=$true;  Writes="new SSOT + archive"; Risk="LOW"; Rule="Copy-only, no overwrite of source." }
        [pscustomobject]@{ Action="Matrix";   Safe=$true;  Writes="reports";         Risk="LOW"; Rule="This table." }
    )
    $out = Join-Path $def_REPORT_DIR "SSOT_ACTION_MATRIX.html"
    def_ReportHtml -Title "VIA SSOT Manager · Action Matrix" -Subtitle "Generated $def_STAMP · all actions safe" -Sections @(@{ name="Safe Actions"; rows=$rows }) -OutPath $out
    def_WriteJson -Path (Join-Path $def_REPORT_DIR "SSOT_ACTION_MATRIX.json") -Obj $rows
    return $out
}

function def_Action_Validate {
    param([string]$Ssot)
    $rows = New-Object System.Collections.Generic.List[object]
    $add = { param($check,$detail,$status,$risk) $rows.Add([pscustomobject]@{ Check=$check; Detail=$detail; Status=$status; Risk=$risk }) | Out-Null }

    $exists = (Test-Path -LiteralPath $Ssot)
    & $add "L0:FileExists" $Ssot ($(if($exists){"PASS"}else{"FAIL"})) ($(if($exists){"LOW"}else{"HIGH"}))
    if (-not $exists) { return (def_FinishValidate $rows $null) }

    $size = (Get-Item -LiteralPath $Ssot).Length
    & $add "L0:NonEmpty" "$size bytes" ($(if($size -gt 10){"PASS"}else{"FAIL"})) ($(if($size -gt 10){"LOW"}else{"HIGH"}))

    $obj = $null
    try { $obj = def_LoadSsotObj $Ssot; & $add "L1:JsonParse" "ConvertFrom-Json ok" "PASS" "LOW" }
    catch { & $add "L1:JsonParse" $_.Exception.Message "FAIL" "HIGH"; return (def_FinishValidate $rows $null) }

    $present = $obj.PSObject.Properties.Name
    foreach ($k in $def_REQUIRED_KEYS) {
        $ok = ($present -contains $k)
        & $add "L1:Key:$k" ($(if($ok){"present"}else{"MISSING"})) ($(if($ok){"PASS"}else{"FAIL"})) ($(if($ok){"LOW"}else{"HIGH"}))
    }

    # counts
    $pc = 0; foreach ($g in $obj.input_parameters.PSObject.Properties) { $pc += @($g.Value).Count }
    $vc = 0; foreach ($g in $obj.vdf_contracts.PSObject.Properties) { $vc += @($g.Value).Count }
    $mc = 0; foreach ($g in $obj.macro_contracts.PSObject.Properties) { $mc += @($g.Value).Count }
    & $add "Count:InputParameters" "$pc rows" "OK" "LOW"
    & $add "Count:VDFContracts" "$vc rows" "OK" "LOW"
    & $add "Count:MacroRows" "$mc rows" "OK" "LOW"
    & $add "Count:ValidationLevels" ("" + @($obj.validation_contract).Count) "OK" "LOW"

    # integrity
    $stored = $obj.meta.integrity.sha256_of_body
    $canon  = $obj.meta.integrity.canonical
    & $add "Integrity:Canonical" $canon "OK" "LOW"
    & $add "Integrity:Stored" ($stored.Substring(0,[Math]::Min(16,$stored.Length)) + "...") "OK" "LOW"
    if ($canon -eq "ps_file_raw_masked") {
        $psh = def_PsIntegrity $Ssot
        $match = ($psh -eq $stored)
        & $add "Integrity:PSRecompute" ($psh.Substring(0,16) + "...") ($(if($match){"PASS"}else{"FAIL"})) ($(if($match){"LOW"}else{"HIGH"}))
    } else {
        $psh = def_PsIntegrity $Ssot
        & $add "Integrity:PSObserved" ($psh.Substring(0,16) + "... (canonical=$canon, external; record only)") "OK" "LOW"
    }

    return (def_FinishValidate $rows $obj)
}
function def_FinishValidate {
    param([System.Collections.Generic.List[object]]$Rows,[object]$Obj)
    $fail = @($Rows | Where-Object { $_.Status -eq "FAIL" }).Count
    $grade = if ($fail -eq 0) { "GREEN" } else { "RED" }
    $summary = [pscustomobject]@{ Status=$grade; Fails=$fail; Checks=$Rows.Count; Stamp=$def_STAMP }
    def_WriteJson -Path (Join-Path $def_REPORT_DIR "SSOT_VALIDATE.json") -Obj @{ summary=$summary; rows=$Rows }
    $out = Join-Path $def_REPORT_DIR "SSOT_VALIDATE.html"
    def_ReportHtml -Title "VIA SSOT · Validate" -Subtitle "Status $grade · $($Rows.Count) checks · $def_STAMP" -Sections @(@{ name="Validation"; rows=$Rows }) -OutPath $out
    def_WriteLine ($(if($fail -eq 0){"OK"}else{"FAIL"})) "Validate grade: $grade ($fail fails)"
    return $out
}

function def_Action_Bridge {
    param([object]$Obj)
    $rows = New-Object System.Collections.Generic.List[object]
    $items = @()
    if ($Obj) {
        $items += [pscustomobject]@{ role="first_layer"; path=$Obj.supportive_bridge.first_layer_interface }
        foreach ($m in $Obj.supportive_bridge.modules) { $items += [pscustomobject]@{ role=$m.role; path=$m.path } }
    }
    foreach ($it in $items) {
        $exists = Test-Path -LiteralPath $it.path
        $size = if ($exists) { (Get-Item -LiteralPath $it.path).Length } else { 0 }
        $sha12 = if ($exists) { def_Sha12 $it.path } else { "" }
        $rows.Add([pscustomobject]@{
            Role=$it.role; Path=$it.path
            Status=$(if($exists){"FOUND"}else{"MISSING"})
            Size=$size; Sha12=$sha12
            Risk=$(if($exists){"LOW"}else{"HIGH"})
            Mode="read_heavy_dry_run"
        }) | Out-Null
    }
    def_WriteJson -Path (Join-Path $def_REPORT_DIR "SSOT_BRIDGE.json") -Obj $rows
    $out = Join-Path $def_REPORT_DIR "SSOT_BRIDGE.html"
    def_ReportHtml -Title "VIA SSOT · Supportive Bridge" -Subtitle "Read-heavy / dry-run · not executed · $def_STAMP" -Sections @(@{ name="Bridged Modules"; rows=$rows }) -OutPath $out
    return $out
}

function def_Action_Export {
    param([object]$Obj)
    if (-not $Obj) { throw "Export requires a valid SSOT." }
    $sections = @()

    # input parameters
    $pr = New-Object System.Collections.Generic.List[object]
    foreach ($g in $Obj.input_parameters.PSObject.Properties) {
        foreach ($p in $g.Value) {
            $pr.Add([pscustomobject]@{ Group=$g.Name; Key=$p.key; Value=$p.value; Authority=$p.authority; Locked=$p.locked; Note=$p.note }) | Out-Null
        }
    }
    $sections += @{ name="Input Parameters"; rows=($pr.ToArray()) }
    def_ExportCsv (Join-Path $def_REPORT_DIR "SSOT_input_parameters.csv") $pr.ToArray()

    # vdf
    $vr = New-Object System.Collections.Generic.List[object]
    foreach ($g in $Obj.vdf_contracts.PSObject.Properties) {
        foreach ($d in $g.Value) {
            $vr.Add([pscustomobject]@{ Set=$g.Name; Category=$d.category; Item=$d.item; P1=$d.p1_source; Fallback=$d.fallback; Freq=$d.frequency; Table=$d.table; Validation=$d.validation }) | Out-Null
        }
    }
    $sections += @{ name="VDF Contracts"; rows=($vr.ToArray()) }
    def_ExportCsv (Join-Path $def_REPORT_DIR "SSOT_vdf_contracts.csv") $vr.ToArray()

    # validation
    $valRows = @($Obj.validation_contract | ForEach-Object { [pscustomobject]@{ Level=$_.level; Name=$_.name; VDF=$_.vdf; VRN=$_.vrn; Result=$_.result } })
    $sections += @{ name="Validation L0-L9"; rows=$valRows }
    def_ExportCsv (Join-Path $def_REPORT_DIR "SSOT_validation.csv") $valRows

    $out = Join-Path $def_REPORT_DIR "SSOT_EXPORT.html"
    def_ReportHtml -Title "VIA SSOT · Export" -Subtitle "Read-only matrix export · $def_STAMP" -Sections $sections -OutPath $out
    return $out
}
function def_ExportCsv {
    param([string]$Path,[array]$Rows)
    if (-not $Rows -or $Rows.Count -eq 0) { return }
    $cols = $Rows[0].PSObject.Properties.Name
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine(($cols | ForEach-Object { def_Csv $_ }) -join ",")
    foreach ($r in $Rows) { [void]$sb.AppendLine(($cols | ForEach-Object { def_Csv ($r.$_) }) -join ",") }
    def_WriteText -Path $Path -Text $sb.ToString()
}

function def_Action_Bump {
    param([string]$Ssot,[object]$Obj)
    if (-not $Obj) { throw "Bump requires a valid SSOT." }
    # archive original (copy-only, no delete)
    $arch = Join-Path $def_ARCHIVE_DIR ((Split-Path $Ssot -Leaf) + "." + $def_STAMP + ".bak")
    Copy-Item -LiteralPath $Ssot -Destination $arch -Force
    def_WriteLine "OK" "Archived original -> $arch"

    $cur = "$($Obj.meta.content_version)"
    $parts = $cur.Split(".")
    [int]$maj = $parts[0]; [int]$min = $parts[1]; [int]$pat = $parts[2]
    switch ($BumpPart) {
        "major" { $maj++; $min=0; $pat=0 }
        "minor" { $min++; $pat=0 }
        default { $pat++ }
    }
    $newVer = "$maj.$min.$pat"
    $Obj.meta.content_version = $newVer
    $Obj.meta.generated = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    $Obj.meta.integrity.canonical = "ps_file_raw_masked"
    $Obj.meta.integrity.note = "Rewritten by PowerShell Bump. PS-native masked-compact SHA256; re-verifiable by -Action Validate."
    $Obj.meta.integrity.sha256_of_body = ""

    # write to registry with hash blank, then recompute over the written file, then rewrite with hash
    $newName = "SSOT_VIA_VisualDesignOps_" + (Get-Date -Format "yyyyMMdd") + "_v" + ($newVer.Replace(".","")) + ".json"
    $newPath = Join-Path $def_REGISTRY_DIR $newName
    def_WriteText -Path $newPath -Text ($Obj | ConvertTo-Json -Depth 100)
    $psh = def_PsIntegrity $newPath
    $Obj.meta.integrity.sha256_of_body = $psh
    def_WriteText -Path $newPath -Text ($Obj | ConvertTo-Json -Depth 100)

    def_WriteLine "OK" "Bumped content_version $cur -> $newVer"
    def_WriteLine "OK" "New SSOT -> $newPath"

    $rows = @(
        [pscustomobject]@{ Field="content_version"; Old=$cur; New=$newVer; Status="OK"; Risk="LOW" }
        [pscustomobject]@{ Field="integrity.canonical"; Old="(external)"; New="ps_file_raw_masked"; Status="OK"; Risk="LOW" }
        [pscustomobject]@{ Field="sha256_of_body"; Old=""; New=($psh.Substring(0,16)+"..."); Status="OK"; Risk="LOW" }
        [pscustomobject]@{ Field="archive"; Old=$Ssot; New=$arch; Status="OK"; Risk="LOW" }
        [pscustomobject]@{ Field="newPath"; Old=""; New=$newPath; Status="OK"; Risk="LOW" }
    )
    $out = Join-Path $def_REPORT_DIR "SSOT_BUMP.html"
    def_ReportHtml -Title "VIA SSOT · Version Bump" -Subtitle "Copy-only · original archived · $def_STAMP" -Sections @(@{ name="Bump"; rows=$rows }) -OutPath $out
    return $out
}

function def_Action_Launch {
    param([string]$Ssot)
    if ([string]::IsNullOrWhiteSpace($def_TEMPLATE) -or $def_TEMPLATE.Trim() -eq "#__TEMPLATE_CONTENT__#") {
        throw "Embedded maintainer template missing."
    }
    $ssotText = if ($Ssot -and (Test-Path -LiteralPath $Ssot)) { def_LoadSsotText $Ssot } else { '"__SSOT_DATA__"' }
    # literal replace (no regex): swap the JSON-string placeholder for the raw object text
    $html = $def_TEMPLATE.Replace('"__SSOT_DATA__"', $ssotText)
    $out = Join-Path $def_REPORT_DIR "VIA_SSOT_VisualMaintainer.html"
    def_WriteText -Path $out -Text $html
    def_WriteLine "OK" ("Maintainer built (" + $html.Length + " bytes) -> " + $out)
    return $out
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA SSOT MANAGER  ·  VisualDesignOps / VDF / VRN" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    def_EnsureDirs
    $ssot = def_ResolveSsot
    def_WriteLine "RUN" "Action : $Action"
    def_WriteLine "RUN" "SSOT   : $(if($ssot){''+$ssot}else{'NOT FOUND'})"
    def_WriteLine "RUN" "OutDir : $OutDir"

    $obj = $null
    if ($ssot -and (Test-Path -LiteralPath $ssot)) {
        try { $obj = def_LoadSsotObj $ssot } catch { def_WriteLine "WARN" "SSOT parse failed: $($_.Exception.Message)" }
    } else {
        def_WriteLine "WARN" "SSOT JSON not found. Place SSOT_VIA_VisualDesignOps_20260617.json next to this script or pass -SsotPath."
    }

    $report = ""
    switch ($Action) {
        "Matrix"   { $report = def_Action_Matrix }
        "Validate" { $report = def_Action_Validate -Ssot $ssot }
        "Bridge"   { $report = def_Action_Bridge -Obj $obj }
        "Export"   { $report = def_Action_Export -Obj $obj }
        "Bump"     { $report = def_Action_Bump -Ssot $ssot -Obj $obj }
        "Launch"   { $report = def_Action_Launch -Ssot $ssot }
        default    { throw "Unknown action: $Action" }
    }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def SSOT MANAGER COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status : SSOT_MANAGER_COMPLETE"
    Write-Host "Action : $Action"
    Write-Host "Risk   : LOW"
    Write-Host "Report : $report"
    Write-Host "Log    : $def_LOG"

    if (($OpenReport -or $Action -eq "Launch") -and $report -and (Test-Path -LiteralPath $report)) {
        try { Start-Process $report } catch { def_WriteLine "WARN" "Could not auto-open report." }
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

<#
.SYNOPSIS
  VIA 桌機邊跑邊驗 v0100(2026-11-13)— 啟動 VDF → 補持股率 → 啟動 VRN-2 → 唯讀驗證 → 總表 + 貼回摘要(剪貼簿)。

.DESCRIPTION
  操作員 2026-11-13:「啟動 VDF VRN 邊跑邊修結果驗證」。桌機唯讀驗證(v0101 全包)黃兩項:
    V3 持股率最新日 2026-09-21(上游三大法人庫 tw_chip_inst 沒更新)· V4 VRN-2 收據最新 2026-11-04(VRN-2 這週沒跑)。
  本支依序跑(每步照實記燈 · 一步失敗不擋下一步):
    ① 找倉 + 取這輪檔(只取有改的路徑;本機有改動的檔 → 不覆蓋、列出來)
    ② 同意閘只讀顯示(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是操作員的手:本支不設、不讀值以外的事;閘關 = 擷取 GATED,不是壞)
    ③ VDF:ActivateVDF 尾版 run --mode live(閘關時它自己只跑離線步並照實黃)
    ④ VDF:ENG238 尾版 run(三大法人持股率 · 讀擷取後的庫 · 只增)
    ⑤ VRN-2:RoundAll v0135(-VrnMode auto:上一輪輸出冊在 → repair,不在 → full;full 約 40 分鐘)
    ⑥ 唯讀驗證 VIA_DesktopValidate v0100(V1–V6)
    ⑦ 總表 + 每步最後幾行 → 貼回摘要(剪貼簿)· 貼回給 AI 就能接著修
  不碰 TA-Lib · 不裝套件 · 不推 · 不改 VRN-1 遠端 · 不設同意閘。

.EXAMPLE
  Set-Location "$env:USERPROFILE\OneDrive\Documents\movies-dataset"
  git fetch origin claude/optimistic-goodall-yhalc5
  git checkout origin/claude/optimistic-goodall-yhalc5 -- "VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DesktopRunVerify_v0100.ps1"
  pwsh -NoProfile -ExecutionPolicy Bypass -File "VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DesktopRunVerify_v0100.ps1"
#>
[CmdletBinding()]
param(
    [string]$Repo = '',
    [string]$Branch = 'claude/optimistic-goodall-yhalc5',
    [ValidateSet('auto', 'full', 'repair', 'verify', 'report')][string]$VrnMode = 'auto',
    [switch]$SkipFetch,
    [switch]$SkipVDF,
    [switch]$SkipVRN,
    [switch]$NoValidate
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$Stamp = Get-Date -Format 'yyyyMMdd_HHmm'
$Log   = Join-Path $env:TEMP "VIA_DesktopRunVerify_v0100_$Stamp.log"
$Paste = Join-Path $env:TEMP "VIA_DesktopRunVerify_v0100_${Stamp}_paste.txt"
$Rows  = [System.Collections.Generic.List[object]]::new()
$Tails = [ordered]@{}
$T0 = Get-Date

function Say([string]$m, [string]$c = 'Gray') { Write-Host $m -ForegroundColor $c; Add-Content -Path $Log -Value $m -Encoding utf8 }
function Note([string]$step, [string]$lamp, [string]$key) { $Rows.Add([pscustomobject]@{ Step = $step; Lamp = $lamp; Key = $key }) }
function Lamp-Of([int]$rc) { switch ($rc) { 0 { 'GREEN' } 2 { 'YELLOW' } 3 { 'ABSENT' } 4 { 'GATED' } default { 'RED' } } }

# ── ① 找倉 ─────────────────────────────────────────────────────────
function Find-Repo {
    $cands = @()
    if ($Repo) { $cands += $Repo }
    if ($PSScriptRoot) { $cands += (git -C $PSScriptRoot rev-parse --show-toplevel 2>$null) }
    $cands += (git rev-parse --show-toplevel 2>$null)
    $cands += @((Join-Path $env:USERPROFILE 'OneDrive\Documents\movies-dataset'), (Join-Path $env:USERPROFILE 'Documents\movies-dataset'), (Join-Path $env:USERPROFILE 'movies-dataset'))
    foreach ($c in $cands) { if ($c -and (Test-Path (Join-Path $c '.git')) -and (Test-Path (Join-Path $c 'VeritasIntelligenceAnalytics'))) { return (Resolve-Path $c).Path } }
    return $null
}
$RepoPath = Find-Repo
if (-not $RepoPath) { Say '[RED] 找不到 movies-dataset 倉 · 用 -Repo "<倉路徑>" 指定' 'Red'; exit 1 }
Set-Location $RepoPath
$VIA = Join-Path $RepoPath 'VeritasIntelligenceAnalytics'
Say "[GREEN] ① 倉:$RepoPath" 'Green'
Note '找倉' 'GREEN' $RepoPath

$py = $env:VIA_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source
if (-not $py) { Say '[RED] 找不到 python(不要用 WindowsApps 的假 python · 或先設 $env:VIA_PY)' 'Red'; exit 1 }
Say "[GREEN]   python $("$(& $py --version 2>&1)".Trim()) · $py" 'Green'

# ── ① 取這輪檔(本機有改動的路徑不覆蓋)──────────────────────────────────────
if (-not $SkipFetch) {
    $paths = @('VeritasIntelligenceAnalytics/functional modules/VDF', 'VeritasIntelligenceAnalytics/functional modules/VRN',
               'VeritasIntelligenceAnalytics/supportive modules/registry', 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0179',
               'VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DesktopValidate_v0100.py', 'VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DesktopRunVerify_v0100.ps1')
    git fetch origin $Branch 2>&1 | ForEach-Object { Add-Content -Path $Log -Value "  $_" -Encoding utf8 }
    $took = @(); $kept = @()
    foreach ($p in $paths) {
        $dirty = @(git diff --name-only -- $p 2>$null | Where-Object { $_ })
        if ($dirty.Count) { $kept += $dirty; continue }
        git checkout "origin/$Branch" -- $p 2>&1 | ForEach-Object { Add-Content -Path $Log -Value "  $_" -Encoding utf8 }
        if ($LASTEXITCODE -eq 0) { $took += $p }
    }
    if ($kept.Count) { Say "[YELLOW] ① 本機有改動、沒覆蓋的檔 $($kept.Count) 支(前 5):$(($kept | Select-Object -First 5) -join ' · ')" 'Yellow' }
    Note '取這輪檔' ($(if ($kept.Count) { 'YELLOW' } else { 'GREEN' })) "$($took.Count)/$($paths.Count) 路徑$(if ($kept.Count) { " · 本機改動未覆蓋 $($kept.Count) 支" })"
} else { Note '取這輪檔' 'SKIP' '-SkipFetch' }

# ── ② 同意閘(只讀)─────────────────────────────────────────────────
$g1 = "$env:VIA_NET_CONSENT"; $g2 = "$env:VIA_SCRAPE_CONSENT"
$gate = ($g1 -ceq 'YES') -and ($g2 -cin 'YES', 'I_ACCEPT_RESPONSIBLE_SCRAPING')
if ($gate) { Say "[GREEN] ② 同意閘開(操作員設的)· VDF 會實抓 · VRN-2 ⑥f 共識會重抓" 'Green'; Note '同意閘' 'OPEN' '操作員設 · 只讀' }
else {
    Say "[YELLOW] ② 同意閘未開(VIA_NET_CONSENT=$(($g1) ? $g1 : '(未設)') · VIA_SCRAPE_CONSENT=$(($g2) ? $g2 : '(未設)'))→ VDF 只跑離線步(持股率不會更新到最新)· 本支不代設" 'Yellow'
    Say "    要實抓:同一個視窗先貼 `$env:VIA_NET_CONSENT = 'YES'; `$env:VIA_SCRAPE_CONSENT = 'YES' 再跑本支(操作員決定)" 'DarkGray'
    Note '同意閘' 'GATED' '未開 · VDF 擷取 GATED(不是壞)'
}

function Run-Py([string]$name, [string]$file, [string[]]$pyArgs, [int]$keep = 8) {
    if (-not (Test-Path -LiteralPath $file)) { Note $name 'ABSENT' "檔不在 $file"; return }
    Say "▶ $name · $(Split-Path $file -Leaf) $($pyArgs -join ' ')" 'Cyan'
    $t = Get-Date
    $env:PYTHONUNBUFFERED = '1'; $env:PYTHONIOENCODING = 'utf-8'
    $out = & $py $file @pyArgs 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -Path $Log -Value $l -Encoding utf8; $l }
    $rc = $LASTEXITCODE
    $last = @($out | Where-Object { "$_".Trim() } | Select-Object -Last $keep)
    $Tails[$name] = $last
    $head = "$(@($last | Where-Object { $_ -match '^\[(GREEN|YELLOW|RED|PASS|FAIL|GATED|NODATA)' } | Select-Object -Last 1))"
    if (-not $head) { $head = "$($last | Select-Object -Last 1)" }
    Note $name (Lamp-Of $rc) ("rc $rc · $([int]((Get-Date) - $t).TotalSeconds) 秒 · " + $head.Substring(0, [Math]::Min(150, $head.Length)))
}
function Tail-File([string]$dir, [string]$stem) {
    $hits = @(Get-ChildItem -LiteralPath $dir -Filter "$($stem)_v*.py" -ErrorAction SilentlyContinue | Where-Object Name -Match '_v\d{4}\.py$' | Sort-Object Name)
    if ($hits.Count) { return $hits[-1].FullName } else { return $null }
}

# ── ③ VDF 啟動 · ④ 持股率 ────────────────────────────────────────────
if (-not $SkipVDF) {
    $vdf = Join-Path $VIA 'functional modules\VDF'
    $act = Tail-File $vdf 'VDF_MDL013_ActivateVDF'
    Run-Py 'VDF 啟動(ActivateVDF)' $act @('run', '--mode', 'live') 10
    $e238 = Tail-File (Join-Path $vdf 'engine') 'VDF_ENG238_InstHoldingPct'
    Run-Py 'VDF 持股率(ENG238)' $e238 @('run') 6
} else { Note 'VDF' 'SKIP' '-SkipVDF' }

# ── ⑤ VRN-2 整輪 / 修 ───────────────────────────────────────────────
if (-not $SkipVRN) {
    $ra = Join-Path $VIA 'docs\handoff\ai\vrn2_release_v0179\VRN2_RoundAll_v0135.py'
    $mode = $VrnMode
    if ($mode -eq 'auto') { $mode = $(if (Test-Path -LiteralPath (Join-Path $VIA 'VIA_Reports\vrn2\output\VRN2_FinancialData_latest.json')) { 'repair' } else { 'full' }) }
    $rargs = @('--root', $VIA, '--no-open') + @(switch ($mode) {
        'repair' { '--only'; 'package,fix,report,closeout,pasteback' }
        'verify' { '--only'; 'package,verify,report,closeout,pasteback' }
        'report' { '--only'; 'report,closeout,pasteback' } })
    Say "[計] ⑤ VRN-2 模式 $mode$(if ($VrnMode -eq 'auto') { '(自動:上一輪輸出冊' + $(if ($mode -eq 'repair') { '在 → 只修' } else { '不在 → 整輪 · 約 40 分鐘' }) + ')' })" 'DarkGray'
    Run-Py "VRN-2 RoundAll($mode)" $ra $rargs 12
    $cj = Join-Path $VIA 'VIA_Reports\vrn2\VRN2_CloseoutUI_latest.json'
    if ((Test-Path -LiteralPath $cj) -and (Get-Item -LiteralPath $cj).LastWriteTime -ge $T0) {
        $c = Get-Content -LiteralPath $cj -Raw -Encoding utf8 | ConvertFrom-Json
        Note 'VRN-2 收尾' "$($c.state)" "$($c.state_label) · $($c.state_text)"
    } else { Note 'VRN-2 收尾' 'NODATA' '這輪沒寫出收尾頁(看 RoundAll 最後幾行)' }
} else { Note 'VRN-2' 'SKIP' '-SkipVRN' }

# ── ⑥ 唯讀驗證 ─────────────────────────────────────────────────────
if (-not $NoValidate) {
    Run-Py '唯讀驗證(V1–V6)' (Join-Path $VIA 'docs\handoff\ai\VIA_DesktopValidate_v0100.py') @('--root', $RepoPath) 10
} else { Note '唯讀驗證' 'SKIP' '-NoValidate' }

# ── ⑦ 總表 + 貼回摘要 ───────────────────────────────────────────────
$Rows | Format-Table -AutoSize -Wrap | Out-String -Width 220 | ForEach-Object { Write-Host $_; Add-Content -Path $Log -Value $_ -Encoding utf8 }
$out = @("VIA_DesktopRunVerify v0100 · $Stamp · $([int]((Get-Date) - $T0).TotalMinutes) 分 · 倉 $RepoPath · 同意閘 $(if ($gate) { '開' } else { '未開' })")
$out += ($Rows | ForEach-Object { "{0} | {1} | {2}" -f $_.Step, $_.Lamp, $_.Key })
foreach ($k in $Tails.Keys) { $out += "── $k(最後幾行)──"; $out += $Tails[$k] }
$out | Set-Content -Path $Paste -Encoding utf8
try { $out -join "`n" | Set-Clipboard; $clip = '(已複製到剪貼簿)' } catch { $clip = '' }
Say "日誌:$Log"
Say "貼回摘要:$Paste $clip"

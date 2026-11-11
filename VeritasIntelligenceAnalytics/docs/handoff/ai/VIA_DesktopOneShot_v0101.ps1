<#
.SYNOPSIS
  VIA 桌機一支跑完 v0101(2026-11-11)— 三管理器 · VDF ENG238 持股率 · VRN-1 clone 快轉 + PeerBridge prove · VQG 指標冊。

.DESCRIPTION
  只取本分支這輪的檔(git checkout origin/<分支> -- 檔),不動其他本機改動;每步失敗不擋後面;
  v0101(桌機 08:18 / 08:40 貼回):① 每支薄尾的前版鏈缺哪支就從分支補哪支(桌機缺 VQG v0110 → v0111 RED);
  ② 加 VDF_MDL008_FetchSystem v0109(子行程也用新版 → MDL009 v0103 才真的跑 → 清單帶股數)。
  最後一張表(步驟 · RC · 重點行),貼回摘要另存一檔並放進剪貼簿。
  不設同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 由操作員自己設)· 不裝套件 · 不碰 TA-Lib · VRN-1 只更新本機 clone(不推)。

  ENG238 為什麼要找檔:MDL009 把 tw_stock_list_latest.parquet 和 vdf_master_lists.duckdb 寫在同一個輸出根;
  ENG238 只在它拿到的 master 庫旁邊找 parquet。本支先找「有股數」的最新 parquet,再把它旁邊的 master 庫交給 ENG238。

.EXAMPLE
  在倉根:
    git fetch origin claude/optimistic-goodall-yhalc5
    git checkout origin/claude/optimistic-goodall-yhalc5 -- "VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DesktopOneShot_v0101.ps1"
    pwsh -NoProfile -ExecutionPolicy Bypass -File "VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_DesktopOneShot_v0101.ps1"
#>
[CmdletBinding()]
param(
    [string]$Branch = 'claude/optimistic-goodall-yhalc5',
    [string]$Python = 'python',
    [string]$Vrn1Root = (Join-Path $env:USERPROFILE 'via-vdf-vrn'),
    [switch]$SkipMdl009,
    [switch]$SkipVrn1Pull
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = 'utf-8'

$Root = (git -C $PSScriptRoot rev-parse --show-toplevel 2>$null)
if (-not $Root) { Write-Host '[RED] 找不到倉根(本檔要放在 movies-dataset 倉裡)'; exit 1 }
Set-Location $Root
$V  = 'VeritasIntelligenceAnalytics'
$RG = "$V/supportive modules/registry"
$VD = "$V/functional modules/VDF"
$VR = "$V/functional modules/VRN"
$VQ = "$V/functional modules/VQG"
$Stamp = Get-Date -Format 'yyyyMMdd_HHmm'
$Log   = Join-Path $env:TEMP "VIA_DesktopOneShot_v0101_$Stamp.log"
$Paste = Join-Path $env:TEMP "VIA_DesktopOneShot_v0101_${Stamp}_paste.txt"
$Rows  = [System.Collections.Generic.List[object]]::new()
$KeyRx = '\b(GREEN|YELLOW|RED|PASS|FAIL|ABSENT|GATED)\b|^\s*\[計\]|清單來源|^\[prove|HEAD |狀態 MATCH|^\S+\s+\S+\s+(GREEN|YELLOW|RED)\s'

function Add-Row {
    param([string]$Name, [int]$Rc, [string[]]$Lines)
    $key = @($Lines | Where-Object { $_ -match $KeyRx } | Select-Object -Last 4)
    $Rows.Add([pscustomobject]@{ Step = $Name; RC = $Rc; Key = ($key -join ' ‖ ') })
}

function Invoke-Py {
    param([string]$Name, [string[]]$PyArgs)
    "▶ $Name" | Tee-Object -FilePath $Log -Append | Write-Host -ForegroundColor Cyan
    $buf = [System.Collections.Generic.List[string]]::new()
    & $Python @PyArgs 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -Path $Log -Value $l -Encoding utf8; $buf.Add($l) }
    $rc = $LASTEXITCODE
    Add-Row -Name $Name -Rc $rc -Lines $buf
    return , $buf
}

function Invoke-Git {
    param([string]$Name, [string[]]$GitArgs)
    "▶ $Name" | Tee-Object -FilePath $Log -Append | Write-Host -ForegroundColor Cyan
    $buf = [System.Collections.Generic.List[string]]::new()
    & git @GitArgs 2>&1 | ForEach-Object { $l = "$_"; Write-Host $l; Add-Content -Path $Log -Value $l -Encoding utf8; $buf.Add($l) }
    $rc = $LASTEXITCODE
    $Rows.Add([pscustomobject]@{ Step = $Name; RC = $rc; Key = (@($buf | Select-Object -Last 2) -join ' ‖ ') })
    return , $buf
}

# ── ① 取這輪的檔(只取這些 · 其他本機改動不動)──────────────────────────────
$null = Invoke-Git '取分支' @('fetch', 'origin', $Branch)
$Files = @(
    "$RG/CGC_MDL149_VeritasCentralGovernanceConsole_v0193.py",
    "$RG/CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py",
    "$RG/CGC_MDL149_VeritasCentralGovernanceConsole_v0195.py",
    "$RG/VIA_RegistrationReceipts_v0100.jsonl",
    "$V/docs/handoff/ai/VIA_SystemManager_Standard_v0100.json",
    "$VD/VDF_SystemManager_v0169.py",
    "$VD/VDF_MDL008_FetchSystem_v0108.py",
    "$VD/VDF_MDL008_FetchSystem_v0109.py",
    "$VD/VDF_MDL009_TWStockList_v0103.py",
    "$VD/VDF_FetchSystem_SSOT_v0108.json",
    "$VD/engine/VDF_ENG238_InstHoldingPct_v0101.py",
    "$VD/engine/VDF_ENG238_InstHoldingPct_v0102.py",
    "$VR/VRN_SystemManager_v0263.py",
    "$VR/VRN2_PeerBridge_v0102.py",
    "$VQ/VQG_AllInOne_v0111.py",
    "$VQ/VQG_IndicatorRegister_SSOT_v0100.json",
    "$V/supportive modules/VIA_ParquetLake_v0101.py"
)
$have = @($Files | Where-Object { git cat-file -e "origin/${Branch}:$_" 2>$null; $LASTEXITCODE -eq 0 })
$miss = @($Files | Where-Object { $have -notcontains $_ })
if ($miss.Count) { Write-Host "[YELLOW] 分支上沒有:$($miss -join ' · ')" }
if ($have.Count) { $null = Invoke-Git "取檔 $($have.Count) 支" (@('checkout', "origin/$Branch", '--') + $have) }

# 前版鏈補齊:每支薄尾(<家族>_vNNNN.py)在分支上比它舊的同家族檔,本機缺哪支就補哪支(只補缺的 · 不覆蓋已在的)
$chainMiss = [System.Collections.Generic.List[string]]::new()
foreach ($f in $have) {
    if ($f -notmatch '^(?<dir>.+)/(?<fam>[^/]+)_v(?<ver>\d{4})\.py$') { continue }
    $dir = $Matches.dir; $fam = $Matches.fam; $ver = [int]$Matches.ver
    $onBranch = @(git ls-tree --name-only "origin/$Branch" -- "$dir/" 2>$null)
    foreach ($p in $onBranch) {
        if ($p -match ('^' + [regex]::Escape("$dir/$fam") + '_v(\d{4})\.py$') -and [int]$Matches[1] -lt $ver -and -not (Test-Path -LiteralPath $p)) {
            if (-not $chainMiss.Contains($p)) { $chainMiss.Add($p) }
        }
    }
}
if ($chainMiss.Count) {
    Write-Host "[INFO] 前版鏈本機缺 $($chainMiss.Count) 支 → 從分支補:$((@($chainMiss) | ForEach-Object { Split-Path $_ -Leaf }) -join ' · ')"
    $null = Invoke-Git "補前版鏈 $($chainMiss.Count) 支" (@('checkout', "origin/$Branch", '--') + @($chainMiss))
} else {
    $Rows.Add([pscustomobject]@{ Step = '補前版鏈'; RC = 0; Key = '本機前版鏈齊全 · 不用補' })
}

# ── ② 三個 System Manager(對等 · 只讀)──────────────────────────────────
$null = Invoke-Py 'VCGC 主控台 v0195 health' @("$RG/CGC_MDL149_VeritasCentralGovernanceConsole_v0195.py", 'health')
$null = Invoke-Py 'VDF 管理器 v0169 conform' @("$VD/VDF_SystemManager_v0169.py", 'conform')
$null = Invoke-Py 'VRN 管理器 v0263 peers' @("$VR/VRN_SystemManager_v0263.py", 'peers')

# ── ③ VDF:ENG238 持股率(找有股數的 latest.parquet → 用它旁邊的 master 庫)──────────
$null = Invoke-Py 'ENG238 v0102 自測' @("$VD/engine/VDF_ENG238_InstHoldingPct_v0102.py", '--selftest')

$Probe = Join-Path $env:TEMP 'via_oneshot_probe_v0101.py'
@'
import json, sys
from pathlib import Path
import duckdb
out = []
for root in sys.argv[1:]:
    r = Path(root)
    if not r.is_dir():
        continue
    for p in r.rglob("tw_stock_list_latest.parquet"):
        rec = {"parquet": str(p), "mtime": p.stat().st_mtime, "rows": 0, "shares": -1, "db": None}
        q = "read_parquet('" + str(p).replace("'", "''") + "')"
        try:
            con = duckdb.connect()
            cols = [d[0] for d in con.execute("DESCRIBE SELECT * FROM " + q).fetchall()]
            rec["rows"] = con.execute("SELECT count(*) FROM " + q).fetchone()[0]
            if "shares_issued" in cols:
                rec["shares"] = con.execute("SELECT count(shares_issued) FROM " + q).fetchone()[0]
            con.close()
        except Exception as e:  # noqa: BLE001
            rec["error"] = str(e)[:160]
        for base in (p.parent.parent, p.parent.parent.parent):   # ENG238 v0102 只在 db.parent / db.parent.parent 找 0-1-TWStockList
            db = base / "vdf_master_lists.duckdb"
            if db.is_file():
                rec["db"] = str(db)
                break
        out.append(rec)
out.sort(key=lambda x: (x["shares"] > 0, x["db"] is not None, x["mtime"]), reverse=True)
print(json.dumps(out, ensure_ascii=False))
'@ | Set-Content -Path $Probe -Encoding utf8

function Find-StockList {
    $raw = & $Python $Probe "$V/VIA_Reports" "$VD" 2>&1 | Select-Object -Last 1
    try { $obj = $raw | ConvertFrom-Json; return @($obj | ForEach-Object { $_ }) } catch { Write-Host "[YELLOW] 找清單檔失敗:$raw"; return @() }
}

$cands = Find-StockList
$best = $cands | Where-Object { $_.shares -gt 0 -and $_.db } | Select-Object -First 1
if (-not $best -and -not $SkipMdl009) {
    Write-Host '[INFO] 沒有「有股數且旁邊有 master 庫」的清單 → 經 VDF 管理器跑 MDL009(v0169 轉交前版 · 同意閘照你現在的設定)'
    $null = Invoke-Py 'MDL009 實跑(經 VDF 管理器)' @("$VD/VDF_SystemManager_v0169.py", 'fetch', 'run', 'MDL009', '--apply')
    $cands = Find-StockList
    $best = $cands | Where-Object { $_.shares -gt 0 -and $_.db } | Select-Object -First 1
}
"── 找到的清單檔(前 5)──" | Tee-Object -FilePath $Log -Append | Write-Host
$cands | Select-Object -First 5 | ForEach-Object {
    $l = "  股數 $($_.shares) / 列 $($_.rows) · master 庫 $(if ($_.db) { $_.db } else { '（旁邊沒有）' }) · $($_.parquet)"
    Write-Host $l; Add-Content -Path $Log -Value $l -Encoding utf8
}
if ($best) {
    $null = Invoke-Py 'ENG238 v0102 實跑(補持股率)' @("$VD/engine/VDF_ENG238_InstHoldingPct_v0102.py", 'run', '--stock-db', $best.db)
} else {
    $why = if ($cands | Where-Object { $_.shares -gt 0 }) { '有股數的 parquet 旁邊沒有 vdf_master_lists.duckdb' } else { '找不到有股數的 tw_stock_list_latest.parquet' }
    Write-Host "[YELLOW] ENG238 這輪不跑 · $why(上面清單照實列出,貼回給 AI)"
    $Rows.Add([pscustomobject]@{ Step = 'ENG238 v0102 實跑(補持股率)'; RC = 2; Key = "YELLOW · $why" })
}

# ── ④ VRN-1 clone 快轉(只更新本機 clone · 不推)+ PeerBridge prove ─────────────
if ($env:VIA_VRN1_ROOT -and $env:VIA_VRN1_ROOT -match '請換成') { Remove-Item Env:VIA_VRN1_ROOT -ErrorAction SilentlyContinue }
if (Test-Path (Join-Path $Vrn1Root '.git')) {
    if (-not $SkipVrn1Pull) {
        $null = Invoke-Git 'VRN-1 fetch' @('-C', $Vrn1Root, 'fetch', 'origin')
        $dirty = @(git -C $Vrn1Root status --porcelain --untracked-files=no 2>$null)
        if ($dirty.Count) {
            Write-Host "[YELLOW] VRN-1 有已追蹤檔的本機改動 $($dirty.Count) 個 → 不 pull(先自己看 git -C `"$Vrn1Root`" status)"
            $Rows.Add([pscustomobject]@{ Step = 'VRN-1 pull --ff-only'; RC = 2; Key = "YELLOW · 本機改動 $($dirty.Count) 個 · 未 pull" })
        } else {
            $null = Invoke-Git 'VRN-1 pull --ff-only' @('-C', $Vrn1Root, 'pull', '--ff-only')
        }
    }
    $null = Invoke-Git 'VRN-1 HEAD' @('-C', $Vrn1Root, 'log', '--oneline', '-1')
} else {
    Write-Host "[YELLOW] 找不到 VRN-1 clone:$Vrn1Root(用 -Vrn1Root 指定)"
    $Rows.Add([pscustomobject]@{ Step = 'VRN-1 clone'; RC = 3; Key = "ABSENT · $Vrn1Root" })
}
$null = Invoke-Py 'PeerBridge v0102 prove' @("$VR/VRN2_PeerBridge_v0102.py", 'prove')

# ── ⑤ VQG 指標登記冊 ─────────────────────────────────────────────────
$null = Invoke-Py 'VQG v0111 指標冊對帳' @("$VQ/VQG_AllInOne_v0111.py", 'indicators', '--check')
$null = Invoke-Py 'VQG v0111 指標冊匯出' @("$VQ/VQG_AllInOne_v0111.py", 'indicators', '--export')

# ── 收尾:表 + 貼回摘要 ───────────────────────────────────────────────
$Rows | Format-Table -AutoSize -Wrap | Out-String -Width 220 | Tee-Object -FilePath $Log -Append | Write-Host
$sum = @("VIA_DesktopOneShot v0101 · $Stamp · 分支 $Branch") + ($Rows | ForEach-Object { "{0} | rc {1} | {2}" -f $_.Step, $_.RC, $_.Key })
$sum | Set-Content -Path $Paste -Encoding utf8
try { $sum -join "`n" | Set-Clipboard; $clip = '(已複製到剪貼簿)' } catch { $clip = '' }
Write-Host "日誌:$Log"
Write-Host "貼回摘要:$Paste $clip"

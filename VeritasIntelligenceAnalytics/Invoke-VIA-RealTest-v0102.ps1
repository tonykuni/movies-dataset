# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-RealTest-v0102.ps1 — 短指令 via-realtest(R44 · 一支 PS 全包:拉齊 → 實測 → 樣本驗證 → 交接紀錄 → 同步 GitHub)
#   操作員(R44 2026-10-02):「integrate into one ps code to handle all and log the handover report sync all to github」
#   工作站實錄:`git pull` 被兩種東西擋住 ——
#     (a) 本機帳本有只增寫的新列(VIA_Lessons_Ledger · VIA_ToolCoverage_Ledger)→「local changes would be overwritten」;
#     (b) 先前從分支單拉的檔(Invoke-VIA-RealTest-v0100 · Register-v0265 · 鏈跑器 v0105 / v0108)成了未追蹤檔,內容和遠端一樣
#         →「untracked working tree files would be overwritten」。
#   本版只加頭尾,實測本體照 v0101(呼叫它,不複製):
#   ① 拉齊(-NoSync 跳過):未完成合併先 abort;擋路的未追蹤檔**和遠端一模一樣**才搬到 %TEMP%\VIA_presync_<時間>(搬,不刪;
#      內容不同就不碰、列紅字);只增寫帳本(*_Ledger_v####.json/.jsonl)先在本機提交;已知的副作用檔
#      (VIA_Engine_Consolidation_Register:鏈跑會寫 candidates)還原;其餘本機改動**不碰**,照實列出;
#      然後交給既有拉齊醫生 CGC_MDL143_MergeMedic sync --apply(分叉 merge --no-ff · 帳本聯集 · 零 force / reset / 刪除)。
#   ② 實測:呼叫 Invoke-VIA-RealTest-v0101(25 加速器 · VDF ∥ VRN ∥ 覆蓋 ∥ 衝突 · ENV 等鏈跑完 · 全景 + 三合一 · 紅字 / 黃字)。
#   ③ 樣本驗證:VRN_ENG392_TextCompleteness run --dir <-Samples,預設 C:\測試樣本報告>(經 VCGC)。
#   ④ 交接:VCGC handoff check(只判,不寫 checkpoint;checkpoint 要綠才准,由 AI 端在 PR 上做)。
#   ⑤ 交接紀錄:docs\handoff\workstation\WS_HANDOVER_<時間>.md + WS_HANDOVER_latest.md(結果總表 · 紅字 · 黃字全文 · 樣本 · 交接 · 拉齊動作)。
#   ⑥ 同步 GitHub(-NoPush 跳過):只提交「只增寫帳本 + docs\handoff\」;VIA_Reports 永不提交(.gitignore 也擋);
#      push 被拒(遠端又動了)→ 再拉齊一次 → 再 push 一次;還不行就照實記紅,不 force。
#   不代開網路同意閘;不用 TA-Lib;不刪檔;不 force;不 reset --hard;不 stash drop。
# 用法:via-realtest [-NoSync] [-NoPush] [-Samples <夾>] [-Resume] [-FixEnv] [-NoOpen] [-StrictGate] [-StallSec 240] [-MaxMin 60]
# 結束碼:同 v0101(0 全綠 · 2 有發現 · 1 有紅 · 124 有一條超時);拉齊或推送失敗另算紅(1)。
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$NoSync,
    [switch]$NoPush,
    [string]$Samples = "C:\測試樣本報告",
    [switch]$Resume,
    [switch]$FixEnv,
    [switch]$NoOpen,
    [switch]$StrictGate,
    [int]$StallSec = 240,
    [int]$MaxMin = 60
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$VIA = $PSScriptRoot
$Repo = Split-Path $VIA -Parent
$Reg = Join-Path $VIA "supportive modules\registry"
$Rep = Join-Path $VIA "VIA_Reports"
$LogDir = Join-Path $Rep "realtest"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Red = New-Object System.Collections.Generic.List[string]
$Notes = New-Object System.Collections.Generic.List[string]
$SideEffect = @("VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Engine_Consolidation_Register_v0100.json")
$LedgerRx = '_Ledger_v\d{3,4}\.jsonl?$'
$HandoffRx = '^VeritasIntelligenceAnalytics/docs/handoff/'
$keepFromVcgc = $env:VIA_FROM_VCGC; $keepPush = $env:VIA_VCGC_PUSH

function Get-Py {
    foreach ($c in @($env:VIA_PY, "python", "python3", "py")) {
        if (-not $c) { continue }
        $cmd = Get-Command $c -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
    }
    return $null
}
function Get-Newest([string]$Dir, [string]$Filter) {
    Get-ChildItem -LiteralPath $Dir -Filter $Filter -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
}
function G { & git -C $Repo @args 2>&1 | ForEach-Object { "" + $_ } }
function Unquote([string]$p) { $p = $p.Trim(); if ($p.StartsWith('"') -and $p.EndsWith('"')) { $p = $p.Substring(1, $p.Length - 2) -replace '\\"', '"' }; return $p }
function Get-Porcelain {
    # 回 @{ code; path }(-z 不好在 PS 拆;用 core.quotepath=false 讓中文路徑原樣)
    @(& git -C $Repo -c core.quotepath=false status --porcelain -uall 2>$null | ForEach-Object {
        $l = "" + $_
        if ($l.Length -ge 4) { [pscustomobject]@{ code = $l.Substring(0, 2); path = (Unquote ($l.Substring(3) -replace '^.* -> ', '')) } }
    })
}
function Invoke-MergeMedic([string]$py, [string]$V) {
    $out = @(& $py $V run --family core CGC_MDL143_MergeMedic sync --apply 2>&1 | ForEach-Object { "" + $_ })
    return @{ rc = $LASTEXITCODE; out = $out }
}

$py = Get-Py
$V = Get-Newest $Reg "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
if (-not $py -or -not $V) { Write-Host "  [via-realtest v0102] 找不到 python 或 VCGC 主控台尾版" -ForegroundColor Red; exit 1 }
$env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"
$headBefore = (G rev-parse --short HEAD | Select-Object -Last 1)
$branch = (G rev-parse --abbrev-ref HEAD | Select-Object -Last 1)

Write-Host ""
Write-Host "  ╔════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  via-realtest v0102 · 拉齊 → 實測 → 樣本驗證 → 交接紀錄 → 同步 GitHub    ║" -ForegroundColor Cyan
Write-Host "  ╚════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# ① 拉齊 ---------------------------------------------------------------------------------
$syncLine = "跳過(-NoSync)"
if (-not $NoSync) {
    Write-Progress -Id 0 -Activity "via-realtest v0102" -Status "① 拉齊 GitHub…" -PercentComplete 1
    if (Test-Path -LiteralPath (Join-Path $Repo ".git\MERGE_HEAD")) {
        $null = G merge --abort
        $Notes.Add("未完成的合併已 abort(合併前的本機狀態原樣回來)")
    }
    $null = G fetch -q origin $branch
    # 已知副作用檔還原(鏈跑會在冊上寫 candidates;不提交)
    foreach ($s in $SideEffect) {
        if (@(Get-Porcelain | Where-Object { $_.path -eq $s -and $_.code -match 'M' }).Count) { $null = G checkout -- $s; $Notes.Add("副作用檔還原:" + (Split-Path $s -Leaf)) }
    }
    # 擋路的未追蹤檔:遠端有同路徑 → 內容一樣才搬走(搬到 %TEMP%,不刪)
    $bk = Join-Path ([IO.Path]::GetTempPath()) ("VIA_presync_" + $stamp)
    foreach ($u in @(Get-Porcelain | Where-Object { $_.code -eq '??' })) {
        $rel = $u.path
        if ($rel.EndsWith("/")) { continue }
        $remoteBlob = (& git -C $Repo rev-parse --verify -q ("origin/" + $branch + ":" + $rel) 2>$null)
        if (-not $remoteBlob) { continue }
        $localBlob = (& git -C $Repo hash-object -- (Join-Path $Repo $rel) 2>$null)
        if ($localBlob -eq $remoteBlob) {
            $dest = Join-Path $bk $rel
            New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
            Move-Item -LiteralPath (Join-Path $Repo $rel) -Destination $dest -Force
            $Notes.Add("未追蹤檔與遠端一模一樣 → 搬到 " + $dest + "(拉下來的就是同一份)")
        } else {
            $Red.Add("拉齊:未追蹤檔 " + $rel + " 和遠端不同 → 不碰;請你決定留哪份(另存新版號或移開)後再跑")
        }
    }
    # 只增寫帳本先在本機提交(拉齊醫生合併時做聯集,不丟列)
    $led = @(Get-Porcelain | Where-Object { $_.code -match 'M' -and $_.path -match $LedgerRx } | ForEach-Object { $_.path })
    if ($led.Count) {
        $null = G add -- @led
        $null = G commit -q -m ("workstation: append-only ledgers before sync (" + $stamp + ")") -- @led
        $Notes.Add("只增寫帳本先在本機提交 " + $led.Count + " 支:" + (($led | ForEach-Object { Split-Path $_ -Leaf }) -join "、"))
    }
    $other = @(Get-Porcelain | Where-Object { $_.code -ne '??' })
    if ($other.Count) { $Notes.Add("其餘本機改動不碰(" + $other.Count + " 檔):" + (($other | Select-Object -First 8 | ForEach-Object { $_.path }) -join "、")) }
    $mm = Invoke-MergeMedic $py $V.FullName
    $mmLine = @($mm.out | Where-Object { $_ -match '拉齊|MergeMedic|ff|merge|分叉|DIVERGED|BEHIND|UP_TO_DATE|AHEAD|衝突|聯集' } | Select-Object -Last 3) -join " | "
    $headAfter = (G rev-parse --short HEAD | Select-Object -Last 1)
    $ab = (G rev-list --left-right --count ("origin/" + $branch + "...HEAD") | Select-Object -Last 1)
    $syncLine = "HEAD " + $headBefore + " → " + $headAfter + " · 落後/領先 " + ($ab -replace "\s+", "/") + " · MergeMedic rc " + $mm.rc + $(if ($mmLine) { " · " + $mmLine } else { "" })
    if ($mm.rc -notin 0, 2) { $Red.Add("拉齊:MergeMedic rc " + $mm.rc + " · " + (($mm.out | Select-Object -Last 4) -join " | ")) }
    if (Test-Path -LiteralPath (Join-Path $Repo ".git\MERGE_HEAD")) { $Red.Add("拉齊:合併有人工衝突沒解(git status 看 UU 檔);實測照跑,推送跳過") }
    Write-Host ("  ① 拉齊 · " + $syncLine) -ForegroundColor $(if ($Red.Count) { "Red" } else { "Green" })
    $Notes | ForEach-Object { Write-Host ("     · " + $_) -ForegroundColor DarkGray }
}

# ② 實測(v0101 本體) ---------------------------------------------------------------------
$rt = Join-Path $VIA "Invoke-VIA-RealTest-v0101.ps1"
$rtRc = -1
if (Test-Path -LiteralPath $rt) {
    $rtArgs = @{ StallSec = $StallSec; MaxMin = $MaxMin }
    if ($Resume) { $rtArgs.Resume = $true }; if ($FixEnv) { $rtArgs.FixEnv = $true }
    if ($NoOpen) { $rtArgs.NoOpen = $true }; if ($StrictGate) { $rtArgs.StrictGate = $true }
    & $rt @rtArgs
    $rtRc = $LASTEXITCODE
} else { $Red.Add("實測:找不到 Invoke-VIA-RealTest-v0101.ps1(拉齊沒成功?)") }
$env:VIA_FROM_VCGC = "YES"; $env:VIA_VCGC_PUSH = "NO"      # v0101 跑完會還原環境變數,這裡再設回來

# ③ 樣本驗證 -----------------------------------------------------------------------------
Write-Progress -Id 0 -Activity "via-realtest v0102" -Status "③ 樣本驗證 $Samples…" -PercentComplete 92
$smpLines = @(); $smpRc = -1
if (Test-Path -LiteralPath $Samples) {
    $nPdf = @(Get-ChildItem -LiteralPath $Samples -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in ".pdf", ".docx", ".txt" }).Count
    $smpLines = @(& $py $V.FullName run --family vrn VRN_ENG392_TextCompleteness run --dir $Samples 2>&1 | ForEach-Object { "" + $_ })
    $smpRc = $LASTEXITCODE
    $smpSum = @($smpLines | Where-Object { $_ -match '\[計\]|總判|verdict|完整度|COMPLETE|檔' } | Select-Object -Last 3)
    Write-Host ("  ③ 樣本驗證 · " + $Samples + " · 檔 " + $nPdf + " · rc " + $smpRc + " · " + ($smpSum -join " | ")) -ForegroundColor $(if ($smpRc -eq 0) { "Green" } elseif ($smpRc -in 2, 3, 4) { "Yellow" } else { "Red" })
    if ($smpRc -eq 1) { $Red.Add("樣本驗證 rc 1:" + ($smpSum -join " | ")) }
} else {
    $Notes.Add("樣本夾不在:" + $Samples + "(-Samples <夾> 指定)")
    Write-Host ("  ③ 樣本驗證 · 夾不在 " + $Samples) -ForegroundColor Yellow
}

# ④ 交接檢查 -----------------------------------------------------------------------------
Write-Progress -Id 0 -Activity "via-realtest v0102" -Status "④ 交接檢查…" -PercentComplete 95
$hc = @(& $py $V.FullName handoff check 2>&1 | ForEach-Object { "" + $_ })
$hcRc = $LASTEXITCODE
$hcLine = @($hc | Where-Object { $_ -match '交接防遺漏' } | Select-Object -Last 1)
$hcFind = @($hc | Where-Object { $_ -match '^\[(RED|YELLOW)\]' } | Select-Object -First 12)
Write-Host ("  ④ 交接 · rc " + $hcRc + " · " + ($hcLine -join "")) -ForegroundColor $(if ($hcRc -eq 0) { "Green" } elseif ($hcRc -eq 2) { "Yellow" } else { "Red" })

# ⑤ 交接紀錄 -----------------------------------------------------------------------------
$wsDir = Join-Path $VIA "docs\handoff\workstation"
New-Item -ItemType Directory -Force -Path $wsDir | Out-Null
$paste = Join-Path $LogDir "PASTE_TO_AI_latest.txt"
$pasteText = if ((Test-Path -LiteralPath $paste) -and (Get-Item -LiteralPath $paste).LastWriteTime -ge (Get-Date).AddHours(-3)) { Get-Content -LiteralPath $paste -Raw -Encoding UTF8 } else { "(本輪沒有 PASTE_TO_AI_latest.txt)" }
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# 工作站交接紀錄 · via-realtest v0102 · " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
$md.Add("")
$md.Add("- 分支 " + $branch + " · HEAD(開始)" + $headBefore + " · (拉齊後)" + (G rev-parse --short HEAD | Select-Object -Last 1))
$md.Add("- ① 拉齊:" + $syncLine)
foreach ($n in $Notes) { $md.Add("  - " + $n) }
$md.Add("- ② 實測 v0101 結束碼:" + $rtRc + "(0 全綠 · 2 有發現 · 1 有紅 · 124 超時)")
$md.Add("- ③ 樣本驗證 " + $Samples + ":rc " + $smpRc)
foreach ($l in @($smpLines | Select-Object -Last 12)) { $md.Add("    " + $l) }
$md.Add("- ④ 交接檢查:rc " + $hcRc + " · " + ($hcLine -join ""))
foreach ($l in $hcFind) { $md.Add("    " + $l) }
$md.Add("")
$md.Add("## 紅字(本支)")
if ($Red.Count) { foreach ($r in $Red) { $md.Add("- " + $r) } } else { $md.Add("- 無") }
$md.Add("")
$md.Add("## 實測全文(v0101 的「貼給 AI」整段)")
$md.Add("")
$md.Add('```')
$md.Add($pasteText.TrimEnd())
$md.Add('```')
$wsFile = Join-Path $wsDir ("WS_HANDOVER_" + $stamp + ".md")
$md -join "`n" | Set-Content -LiteralPath $wsFile -Encoding UTF8
Copy-Item -LiteralPath $wsFile -Destination (Join-Path $wsDir "WS_HANDOVER_latest.md") -Force
Write-Host ("  ⑤ 交接紀錄 · " + $wsFile) -ForegroundColor Cyan

# ⑥ 同步 GitHub ---------------------------------------------------------------------------
$pushLine = "跳過(-NoPush)"
if (-not $NoPush) {
    Write-Progress -Id 0 -Activity "via-realtest v0102" -Status "⑥ 同步 GitHub…" -PercentComplete 98
    if (Test-Path -LiteralPath (Join-Path $Repo ".git\MERGE_HEAD")) {
        $pushLine = "跳過:合併衝突沒解"
    } else {
        foreach ($s in $SideEffect) { if (@(Get-Porcelain | Where-Object { $_.path -eq $s -and $_.code -match 'M' }).Count) { $null = G checkout -- $s } }
        $take = @(Get-Porcelain | Where-Object { ($_.path -match $LedgerRx -or $_.path -match $HandoffRx) -and $_.path -notmatch '/VIA_Reports/' } | ForEach-Object { $_.path })
        if ($take.Count) {
            $null = G add -- @take
            $null = G commit -q -m ("workstation handover " + $stamp + ": realtest rc " + $rtRc + " · samples rc " + $smpRc + " · handoff rc " + $hcRc + " (ledgers append-only + docs/handoff)") -- @take
        }
        $p = @(G push origin ("HEAD:" + $branch))
        if ($LASTEXITCODE -ne 0) {
            $Notes.Add("push 被拒(遠端又動了)→ 再拉齊一次")
            $null = G fetch -q origin $branch
            $mm2 = Invoke-MergeMedic $py $V.FullName
            $p = @(G push origin ("HEAD:" + $branch))
        }
        if ($LASTEXITCODE -eq 0) { $pushLine = "已推 " + $branch + " · 提交 " + $take.Count + " 檔(帳本 + docs/handoff)· HEAD " + (G rev-parse --short HEAD | Select-Object -Last 1) }
        else { $pushLine = "推送失敗:" + (($p | Select-Object -Last 3) -join " | "); $Red.Add($pushLine) }
    }
    Write-Host ("  ⑥ 同步 GitHub · " + $pushLine) -ForegroundColor $(if ($pushLine -like "已推*") { "Green" } else { "Red" })
}
Write-Progress -Id 0 -Activity "via-realtest v0102" -Completed

# 收尾 ------------------------------------------------------------------------------------
Write-Host ""
if ($Red.Count) {
    Write-Host "  ═══════════ 紅字(拉齊 / 樣本 / 推送)═══════════" -ForegroundColor Red
    $Red | ForEach-Object { Write-Host ("  ✖ " + $_) -ForegroundColor Red }
}
$tail = @("", "[v0102] 拉齊:" + $syncLine, "[v0102] 樣本驗證 " + $Samples + ":rc " + $smpRc + " · " + (@($smpLines | Select-Object -Last 3) -join " | "),
          "[v0102] 交接:rc " + $hcRc + " · " + ($hcLine -join ""), "[v0102] 同步:" + $pushLine, "[v0102] 交接紀錄:" + $wsFile)
if (Test-Path -LiteralPath $paste) { Add-Content -LiteralPath $paste -Value $tail -Encoding UTF8 }
if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { try { ($pasteText.TrimEnd() + [Environment]::NewLine + ($tail -join [Environment]::NewLine)) | Set-Clipboard } catch { } }
Write-Host "  黃字整段 + v0102 四行已放進剪貼簿(Ctrl+V 貼給 AI)· 交接紀錄已寫進 docs\handoff\workstation 並同步 GitHub" -ForegroundColor Yellow
$env:VIA_FROM_VCGC = $keepFromVcgc; $env:VIA_VCGC_PUSH = $keepPush
$final = if ($Red.Count -and $rtRc -ne 124) { 1 } else { $rtRc }
exit $final

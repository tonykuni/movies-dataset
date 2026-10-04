# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0270.ps1 — 2026-10-05:+via-activate-vcgc(別名 via_activate_vcgc · 啟動中控)
#   操作員令「advise a short code via_activate_vcgc to make ready for others」(VCGC-REQ165)= L70 這一次的許可:只加這一件;v0269 以前一字不動。
#   接手的人 / AI 一行就把 VCGC 帶到可交接狀態(照 CLAUDE.md 入場順序),最後一張總表照實列:
#     ① 同步   git fetch + pull --ff-only(只快轉;有本機改動或分岔 = 停在這步,不強推、不 stash)· 印分支 · 最新鎖版 tag
#     ② token  via-vcgc token(省 Token 工具卡;紅 = VCGC 本身停)
#     ③ enter  via-vcgc enter --card --no-pull(工具版本卡 + test --quick 串測)
#     ④ 交接   via-vcgc handoff check(pending · 相依變更;綠只代表交接資料完整,不是驗收)
#     ⑤ 必用卡 via-vcgc functions(AI 必用功能卡)
#     ⑥ TEMP   via-vcgc run CGC_MDL262_DuckTempHook status(DuckDB TEMP 鉤境覆蓋)
#   via-activate-vcgc [-NoPull] [-StopOnRed]
#   不安裝、不寫冊、不觸網(除了 git fetch / pull);每步包 Invoke-VIACeleritasScoped(PS 25 加速器;只動本行程)。
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
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0269.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:Invoke-VIAActivateStep {
    param([string]$Name, [scriptblock]$Body)
    Write-Host ""
    Write-Host ("  ===== [via-activate-vcgc] " + $Name + " =====") -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    try {
        if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Invoke-VIACeleritasScoped $Body } else { & $Body }
        $rc = [int]$global:LASTEXITCODE
    } catch {
        Write-Host ("  [" + $Name + "] 例外:" + $_.Exception.Message) -ForegroundColor Red
        $rc = 99
    }
    return [pscustomobject]@{ Step = $Name; Rc = $rc }
}

function global:via-activate-vcgc {
    param([switch]$NoPull, [switch]$StopOnRed)
    $vroot = Split-Path -Parent $global:VIARegisterPath
    $repo = Split-Path -Parent $vroot
    $rows = @()
    $steps = [ordered]@{}
    if (-not $NoPull) {
        $steps['① 同步'] = {
            git -C $repo fetch --quiet origin
            if ($LASTEXITCODE -ne 0) { Write-Host "  git fetch 失敗(網路 / 權限)" -ForegroundColor Red; return }
            $dirty = git -C $repo status --porcelain --untracked-files=no
            if ($dirty) { Write-Host "  本機有未提交改動 → 不 pull(先自己提交或另存;本指令不 stash)" -ForegroundColor Yellow; $global:LASTEXITCODE = 1; return }
            git -C $repo pull --ff-only --quiet
            if ($LASTEXITCODE -ne 0) { Write-Host "  不能快轉(本機與遠端分岔)→ 停,不強推" -ForegroundColor Red; return }
            $br = git -C $repo rev-parse --abbrev-ref HEAD
            $head = git -C $repo log -1 --format="%h %s"
            $lock = git -C $repo tag --list "lock-vcgc-vdf/*" --sort=-creatordate | Select-Object -First 1
            Write-Host ("  分支 " + $br + " · " + $head) -ForegroundColor Gray
            Write-Host ("  最新鎖版 " + $(if ($lock) { $lock } else { "(本機沒有 lock-vcgc-vdf/* tag;git fetch --tags)" })) -ForegroundColor Gray
            $global:LASTEXITCODE = 0
        }.GetNewClosure()
    }
    $steps['② token'] = { via-vcgc token }
    $steps['③ enter'] = { via-vcgc enter --card --no-pull }
    $steps['④ 交接'] = { via-vcgc handoff check }
    $steps['⑤ 必用卡'] = { via-vcgc functions }
    $steps['⑥ TEMP'] = { via-vcgc run CGC_MDL262_DuckTempHook status }
    foreach ($k in $steps.Keys) {
        $r = Invoke-VIAActivateStep $k $steps[$k]
        $rows += $r
        if ($StopOnRed -and $r.Rc -ne 0) { Write-Host ("  -StopOnRed:" + $k + " rc " + $r.Rc + " → 停") -ForegroundColor Red; break }
    }
    Write-Host ""
    Write-Host "  ===== [via-activate-vcgc] 總表(照實:rc 0 = 綠;交接綠只代表資料完整,驗收看 closeout_lamp) =====" -ForegroundColor Cyan
    foreach ($r in $rows) {
        $lamp = if ($r.Rc -eq 0) { 'GREEN' } elseif ($r.Step -like '④*') { 'YELLOW' } else { 'RED' }
        $color = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red' }[$lamp]
        Write-Host ("    {0,-8} {1,-7} rc {2}" -f $r.Step, $lamp, $r.Rc) -ForegroundColor $color
    }
    $hard = @($rows | Where-Object { $_.Rc -ne 0 -and $_.Step -notlike '④*' })
    $ready = ($hard.Count -eq 0) -and ($rows.Count -eq $steps.Count)
    if ($ready) {
        Write-Host "  [READY] VCGC 已就緒可交接(④ 交接若黃 = 有 pending,照卡上 owner / next 接手)" -ForegroundColor Green
        $global:LASTEXITCODE = 0
    } else {
        Write-Host ("  [NOT READY] 紅:" + (($hard | ForEach-Object { $_.Step }) -join ' · ') + "(先處理再交接)") -ForegroundColor Red
        $global:LASTEXITCODE = 1
    }
}
Set-Alias -Name via_activate_vcgc -Value via-activate-vcgc -Scope Global -Force
Set-Alias -Name 啟動中控 -Value via-activate-vcgc -Scope Global -Force

<#
.SYNOPSIS
    VIA 同步解卡引導(穩定檔名;永遠不改名、不加版本後綴)

.DESCRIPTION
    批605。這一支存在的理由是一個設計錯誤:

      批604 我把「解決同步卡住」的工具(Invoke-VIA-AllInOne-v0104.ps1)
      放進倉裡,然後叫操作員去跑它 —— 可是他正**因為同步卡住**才沒有那個檔。
      pwsh 回:「引數 '...Invoke-VIA-AllInOne-v0104.ps1' 無法辨識為指令碼檔案名稱」。
      **用來解除卡住的工具,不能放在被卡住的那一側。**

    所以這一支:
      · **檔名固定**,不帶版本尾碼 —— 一旦落地就永遠是同一個路徑,不會因為升版而失聯
      · 只做一件事:把工作樹安全地快轉到 origin/<目前分支>
      · 真的沒有這個檔的時候,對應的貼上版在 docs/VIA_B604_AllInOneSync.md

    紅線(和 v0104 第 0 段同律):
      · 只 stash **追蹤檔**(git stash 不帶 -u)→ 未追蹤件一根不碰
      · stash 前先**整包複製**到 VIA_Reports\presync_<ts>(stash 之外的第二條退路)
      · 只做 --ff-only;分岔就誠實停,不自動 merge / 不 rebase / 不 force
      · 不裝任何東西、不刪任何檔、不設任何同意閘
      · 撞到的未追蹤件**移開保存**(VIA_Reports\presync_<ts>\_untracked_collisions),不刪;
        沒撞到的未追蹤件一根不碰

    尾版律的例外(刻意):這一支**就地改版、永遠不改檔名**。
    版本尾碼是給「引擎換代要能並存」用的;而這一支的價值正好相反——
    它必須是一個**永遠不變的路徑**,不然下次升版又會變成「你手上那一版沒有那個檔」。
    改了什麼看 git log 與下面的沿革。

    沿革:
      批605 v0100 生;批606 +未追蹤件撞名清理(工作站實錄:追蹤檔清乾淨後仍被
      `_patches\` 的未追蹤件擋住 merge)。
#>
[CmdletBinding()]
param(
    [string]$RepoRoot,
    [switch]$Onboard,      # 批608「上船母資料夾」:清點母資料夾裡沒進 git 的東西(唯讀)
    [switch]$Commit,       # 與 -Onboard 併用才會真的 git add + commit(你的手)
    [switch]$Push          # 與 -Commit 併用才 push
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

# ── 上船分類(批608)────────────────────────────────────────────────────────
#   「上船母資料夾」= 母資料夾裡**已經在那、但沒進 git** 的東西要進倉。
#   這跟 via-intake 不是同一件事:那支是把**外面的檔**(預設掃 Downloads)收編進來給 URN;
#   這裡的檔早就在它該在的位置,缺的只是 git。
#   分三類,而且**每一類都印出來讓你看**——不是我替你決定:
#     再生物  引擎跑一次就重生(VIA_Reports\、ui_support 的頁、被引擎覆寫的註冊表)→ 不上船
#     暫存    *.bak_*、*.tmp、__pycache__、一次性補丁夾 _patches\        → 不上船
#     該上船  其餘(引擎新版、docs、launchers、手維護的冊)                 → 上船
#   預設**只清點不動**;-Commit 才 git add + commit;-Push 才推。
$script:RegenPat = '(^VeritasIntelligenceAnalytics/VIA_Reports/|/ui_support/VIA_UI_.*\.html$|/registry/VIA_(Engine_|Schema_|Unified_Register|IndustryUnifiedMap|SSOT_RegexDict|ProjectCompletion|ParallelLanes|VDFArchitecture))'
$script:TempPat  = '(\.bak_|\.tmp$|__pycache__|~$|/_patches/|\.orig$|\.rej$)'

function Get-OnboardClass([string]$Rel) {
    if ($Rel -match $script:TempPat)  { return '暫存' }
    if ($Rel -match $script:RegenPat) { return '再生物' }
    return '該上船'
}

$ErrorActionPreference = 'Continue'
$PSNativeCommandUseErrorActionPreference = $false

function Unquote([string]$p) {
    $p = $p.Trim()
    if ($p.StartsWith('"') -and $p.EndsWith('"')) { $p = $p.Substring(1, $p.Length - 2) }
    $p
}

if (-not $RepoRoot) {
    # launchers\ 的上兩層 = 倉根(…\movies-dataset)
    $RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
}
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
    Write-Host "  [FAIL] 倉根不存在:$RepoRoot" -ForegroundColor Red
} else {
    Set-Location -LiteralPath $RepoRoot
    $top = (git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $top) {
        Write-Host "  [FAIL] 這裡不是 git 工作樹(或 git 不在 PATH):$RepoRoot" -ForegroundColor Red
    } elseif ($Onboard) {
        # ── 批608「上船母資料夾」──────────────────────────────────────────
        $B = (git rev-parse --abbrev-ref HEAD).Trim()
        Write-Host "=== 上船母資料夾 · 分支 $B ===" -ForegroundColor Cyan
        $rows = @()
        foreach ($r in @(git ls-files --others --exclude-standard | ForEach-Object { Unquote $_ } | Where-Object { $_ })) {
            $rows += [pscustomobject]@{ 狀態 = '未追蹤'; 類 = (Get-OnboardClass $r); 路徑 = $r }
        }
        foreach ($d in @(git status --porcelain --untracked-files=no | Where-Object { $_ -and $_.Length -gt 3 })) {
            $r = Unquote $d.Substring(3)
            if ($r -match ' -> ') { $r = ($r -split ' -> ')[-1] }
            $rows += [pscustomobject]@{ 狀態 = '已改'; 類 = (Get-OnboardClass $r); 路徑 = $r }
        }
        if (-not $rows.Count) {
            Write-Host "  母資料夾與 git 一致,沒有東西要上船" -ForegroundColor Green
        } else {
            foreach ($g in ('該上船', '再生物', '暫存')) {
                $sel = @($rows | Where-Object { $_.類 -eq $g })
                if (-not $sel.Count) { continue }
                $col = if ($g -eq '該上船') { 'Yellow' } else { 'DarkGray' }
                Write-Host ("  [{0}] {1} 件" -f $g, $sel.Count) -ForegroundColor $col
                foreach ($x in $sel) { Write-Host ("     {0}  {1}" -f $x.狀態, $x.路徑) -ForegroundColor $col }
            }
            $take = @($rows | Where-Object { $_.類 -eq '該上船' })
            Write-Host ("  ---- 該上船 {0} 件 · 再生物 {1} 件(不上船)· 暫存 {2} 件(不上船)" -f `
                    $take.Count, @($rows | Where-Object { $_.類 -eq '再生物' }).Count,
                @($rows | Where-Object { $_.類 -eq '暫存' }).Count) -ForegroundColor Cyan
            if (-not $Commit) {
                Write-Host "  [唯讀] 只清點沒動。要真的上船:加 -Commit(再加 -Push 才推)" -ForegroundColor DarkGray
            } elseif (-not $take.Count) {
                Write-Host "  [停] 沒有「該上船」的件,不做 commit" -ForegroundColor Yellow
            } else {
                foreach ($x in $take) { git add -- "$($x.路徑)" }
                $msg = "上船母資料夾(Sync-VIA-Bootstrap -Onboard -Commit):$($take.Count) 件"
                $body = ($take | ForEach-Object { "- $($_.狀態) $($_.路徑)" }) -join "`n"
                git commit -m $msg -m $body
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  [OK] 已 commit $($take.Count) 件" -ForegroundColor Green
                    git log --oneline -1
                    if ($Push) { git push -u origin $B }
                    else { Write-Host "  推是你的手:git push -u origin $B" -ForegroundColor DarkGray }
                } else {
                    Write-Host "  [停] commit 失敗,工作樹沒有被推上去" -ForegroundColor Red
                }
            }
        }
    } else {
        $B = (git rev-parse --abbrev-ref HEAD).Trim()
        Write-Host "=== VIA 同步解卡 · 分支 $B ===" -ForegroundColor Cyan
        git fetch origin $B

        $counts = (git rev-list --left-right --count "HEAD...origin/$B" 2>$null)
        $ahead = 0; $behind = 0
        if ($counts) {
            $parts = @($counts -split '\s+' | Where-Object { $_ -ne '' })
            if ($parts.Count -ge 2) { $ahead = [int]$parts[0]; $behind = [int]$parts[1] }
        }
        Write-Host ("  本地領先 {0} · 落後 {1}" -f $ahead, $behind)

        if ($ahead -gt 0) {
            Write-Host "  [停] 本地領先 $ahead 個 commit;自動合併會動到你的歷史,這一步交給你決定" -ForegroundColor Yellow
            Write-Host "       看差異:git log --oneline origin/$B..HEAD" -ForegroundColor Yellow
        } elseif ($behind -eq 0) {
            Write-Host "  已是最新,不需要動工作樹" -ForegroundColor Green
        } else {
            $ts = Get-Date -Format yyyyMMdd_HHmmss
            $bk = Join-Path $RepoRoot "VeritasIntelligenceAnalytics\VIA_Reports\presync_$ts"
            $dirty = @(git status --porcelain --untracked-files=no | Where-Object { $_ -and $_.Length -gt 3 })
            foreach ($d in $dirty) {
                $rel = $d.Substring(3).Trim('"')
                if ($rel -match ' -> ') { $rel = ($rel -split ' -> ')[-1] }
                $src = Join-Path $RepoRoot $rel
                if (Test-Path -LiteralPath $src -PathType Leaf) {
                    $dst = Join-Path $bk $rel
                    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
                    Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction SilentlyContinue
                }
            }
            if ($dirty.Count) {
                Write-Host "  備份 $($dirty.Count) 個追蹤檔 -> $bk" -ForegroundColor Yellow
                git stash push -m "VIA-presync-$ts"
            }
            # 批606 工作站實錄:追蹤檔清乾淨之後還是擋住 ——
            #   「error: The following untracked working tree files would be overwritten by merge」。
            #   PR #41 把 `_patches\` 那幾個檔 **commit 進分支**了,而操作員本機同路徑是**未追蹤**的。
            #   v0100 只處理追蹤檔的髒、刻意不碰未追蹤件 → 方向對但**不完整**。
            #   正解:把**撞到的那幾個**移開保存(不是刪、也不是整夾清掉),其餘未追蹤件一根不碰。
            $incoming  = @(git diff --name-only --diff-filter=A HEAD "origin/$B" | ForEach-Object { Unquote $_ } | Where-Object { $_ })
            $untracked = @(git ls-files --others --exclude-standard | ForEach-Object { Unquote $_ } | Where-Object { $_ })
            $hit = @($untracked | Where-Object { $incoming -contains $_ })
            if ($hit.Count) {
                $same = 0
                foreach ($rel in $hit) {
                    $src = Join-Path $RepoRoot ($rel -replace '/', '\')
                    if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { continue }
                    $ls = (git hash-object -- "$rel" 2>$null)
                    $rs = (git rev-parse "origin/${B}:$rel" 2>$null)
                    if ($ls -and $rs -and $ls.Trim() -eq $rs.Trim()) { $same++ }
                    $dst = Join-Path (Join-Path $bk '_untracked_collisions') ($rel -replace '/', '\')
                    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
                    Move-Item -LiteralPath $src -Destination $dst -Force
                }
                Write-Host ("  撞到 {0} 個未追蹤件(位元組相同 {1} · 不同 {2})→ 移開保存到 {3}\_untracked_collisions" -f `
                        $hit.Count, $same, ($hit.Count - $same), $bk) -ForegroundColor Yellow
            }
            git merge --ff-only "origin/$B"
            if ($LASTEXITCODE -eq 0) {
                git log --oneline -1
                $newest = Get-ChildItem ".\VeritasIntelligenceAnalytics\supportive modules\registry\CGC_MDL135_EnvGovernance_v*.py" -ErrorAction SilentlyContinue |
                    Sort-Object Name | Select-Object -ExpandProperty Name | Select-Object -Last 1
                Write-Host "  MDL135 尾版 : $newest" -ForegroundColor Green
                # 尾版律:指到**現有最新**那一支,不寫死版號(寫死了升版就又變成「你那一版沒有那個檔」)
                $launcher = Get-ChildItem '.\VeritasIntelligenceAnalytics\launchers\Invoke-VIA-AllInOne-v*.ps1' -ErrorAction SilentlyContinue |
                    Sort-Object Name | Select-Object -ExpandProperty FullName | Select-Object -Last 1
                if ($launcher) {
                    Write-Host "  ALL-IN-ONE  : $(Split-Path $launcher -Leaf)" -ForegroundColor Green
                } else {
                    Write-Host "  ALL-IN-ONE  : **找不到**(launchers\Invoke-VIA-AllInOne-v*.ps1)" -ForegroundColor Yellow
                }
                if ($dirty.Count) {
                    Write-Host "  要拿回再生物:git stash pop(多半不必,引擎再跑一次就重生)" -ForegroundColor DarkGray
                }
                if ($launcher) {
                    Write-Host "  下一步:pwsh -NoProfile -ExecutionPolicy Bypass -File `"$launcher`"" -ForegroundColor Cyan
                }
            } else {
                Write-Host "  [停] ff-only 失敗 → 不自動 merge。先看 git status" -ForegroundColor Red
            }
        }
    }
}

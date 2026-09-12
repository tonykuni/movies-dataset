#Requires -Version 5.1
param(
    [string]$Root = "",
    [int]$MaxRounds = 6,
    [switch]$NoEnter,
    [switch]$DryRun
)
# =============================================================================
# Invoke-VIA-Unstick-v0100.ps1 — 倉庫解卡啟動器(批394 續章;操作員不在電腦前亦可一鍵)
# =============================================================================
# 為何需要本件(雲端腳手架端到端實測所得,非推測):
#   操作員副本卡在「合併進行中 + 兩件連字號版號族 Register 衝突」。其拉齊醫生尾版為 v0101,
#   只認底線版號,連字號族一律判 MANUAL 而停 → 要解倉庫才拿得到新醫生,但新醫生就在那個
#   解不開的倉庫裡 = bootstrap 死結。
#   更深一層:操作員那輪 merge 起於「舊的 origin commit」,解完後醫生會再 merge 今天的新
#   commit,同兩件 Register 第二輪又衝突 → v0101 醫生再次 MANUAL。故「解一次」不夠,
#   必須迴圈直到 UP_TO_DATE。
# 本件的立場:不依賴該副本醫生的版本。
#   · 醫生尾版 >= v0102(已認連字號族)→ 直接委派醫生 sync --apply(零重造)
#   · 否則走最小迴圈:台帳交給醫生的 ledger_union 做聯集(append-only 律,零重造),
#     其餘衝突取遠端版(先發先得律,與醫生 VERSIONED_TWIN 裁決同義),完成合併後再拉,
#     迴圈至 UP_TO_DATE 或輪數用盡(不卡斷)。
# 紀律:零 force、零刪除、台帳只增不減、髒檔與未追蹤件不得遺失、誠實三態。
# 用法:& .\Invoke-VIA-Unstick-v0100.ps1            自找根,解到底,最後點源尾版短令冊
#       & .\Invoke-VIA-Unstick-v0100.ps1 -DryRun    只診斷不動手
#       & .\Invoke-VIA-Unstick-v0100.ps1 -NoEnter   解完不點源
# =============================================================================
$ErrorActionPreference = "Continue"
$env:GIT_EDITOR = "true"
$env:GIT_MERGE_AUTOEDIT = "no"
$env:VIA_NO_OPEN = "1"

function Write-Step([string]$State, [string]$Msg) {
    Write-Host ("  [" + $State + "] " + $Msg)
}

# ---- ① 自找倉庫根與 VIA 夾(零寫死路徑) ----
if (-not $Root -or -not (Test-Path -LiteralPath $Root)) {
    $probe = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
    while ($probe) {
        if (Test-Path -LiteralPath (Join-Path $probe ".git")) { $Root = $probe; break }
        $parent = Split-Path $probe -Parent
        if (-not $parent -or $parent -eq $probe) { break }
        $probe = $parent
    }
}
if (-not $Root -or -not (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
    Write-Step "FAIL" "找不到 git 工作樹根(可用 -Root 指定)"
    if ($MyInvocation.InvocationName -eq ".") { return } else { exit 2 }
}
$via = Join-Path $Root "VeritasIntelligenceAnalytics"
if (-not (Test-Path -LiteralPath $via)) { $via = $Root }
$ledRel = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_AutoCode_Registry_v0100.json"

function Get-Tail([string]$Dir, [string]$Pat) {
    $g = @(Get-ChildItem -LiteralPath $Dir -Filter $Pat -File -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($g.Count -ge 1) { return $g[-1].FullName }
    return ""
}
$regDir = Join-Path $via "supportive modules\registry"
$medic = Get-Tail $regDir "CGC_MDL143_MergeMedic_v*.py"
$medicVer = 0
if ($medic -and ($medic -match "_v(\d{3,4})\.py$")) { $medicVer = [int]$Matches[1] }
$branch = (& git -C $Root rev-parse --abbrev-ref HEAD 2>$null)
if (-not $branch) { $branch = "main" }
$head0 = (& git -C $Root rev-parse --short HEAD 2>$null)

Write-Host ""
Write-Host "=== VIA 倉庫解卡(Invoke-VIA-Unstick v0100)==="
Write-Step "OK" ("根 " + $Root + " · 分支 " + $branch + " · HEAD " + $head0)
Write-Step "OK" ("本副本拉齊醫生 " + $(if ($medic) { Split-Path $medic -Leaf } else { "(缺)" }))

$u0 = @(& git -C $Root diff --name-only --diff-filter=U 2>$null) | Where-Object { $_ }
$inMerge = Test-Path -LiteralPath (Join-Path $Root ".git\MERGE_HEAD")
Write-Step "OK" ("合併進行中 " + $inMerge + " · 未合併 " + $u0.Count + " 件")
if ($DryRun) {
    Write-Step "PLAN" "唯讀診斷結束(去掉 -DryRun 才動手)"
    if ($MyInvocation.InvocationName -eq ".") { return } else { exit 0 }
}

# ---- ② 醫生夠新即委派(零重造) ----
if ($medicVer -ge 102) {
    Write-Step "RUN" ("醫生 v" + $medicVer + " 已認連字號版號族=直接委派 sync --apply")
    & python $medic sync --apply --root $Root
} else {
    Write-Step "RUN" ("醫生 v" + $medicVer + " 只認底線版號(bootstrap 死結)=走最小迴圈,最多 " + $MaxRounds + " 輪")
    for ($i = 1; $i -le $MaxRounds; $i++) {
        $u = @(& git -C $Root diff --name-only --diff-filter=U 2>$null) | Where-Object { $_ }
        if ($u.Count -gt 0) {
            $led = @($u | Where-Object { $_ -eq $ledRel })
            $oth = @($u | Where-Object { $_ -ne $ledRel })
            foreach ($f in $oth) {
                & git -C $Root checkout --theirs -- $f 2>$null | Out-Null
                & git -C $Root add -- $f 2>$null | Out-Null
            }
            if ($oth.Count) { Write-Step "OK" ("R" + $i + " 取遠端版 " + $oth.Count + " 件(先發先得律)") }
            if ($led.Count -and $medic) {
                # 台帳只增不減:用該副本醫生的 ledger_union(零重造),絕不取單邊
                $py = @'
import importlib.util, sys
from pathlib import Path
med, root, rel = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
spec = importlib.util.spec_from_file_location("med", med)
m = importlib.util.module_from_spec(spec); sys.modules["med"] = m; spec.loader.exec_module(m)
ours, theirs = m._stage_blob(root, 2, rel), m._stage_blob(root, 3, rel)
data, info = m.ledger_union(ours, theirs)
if info.get("ok") and data is not None:
    (root / rel).write_bytes(data)
    print("LEDGER_UNION_OK|" + str(info.get("total")))
else:
    print("LEDGER_UNION_FAIL|" + str(info.get("why")))
'@
                $tmpPy = Join-Path ([System.IO.Path]::GetTempPath()) ("via_led_" + [guid]::NewGuid().ToString("N") + ".py")
                Set-Content -LiteralPath $tmpPy -Value $py -Encoding UTF8
                $res = (& python $tmpPy $medic $Root $ledRel 2>&1 | Out-String).Trim()
                Remove-Item -LiteralPath $tmpPy -ErrorAction SilentlyContinue
                if ($res -match "LEDGER_UNION_OK\|(\d+)") {
                    & git -C $Root add -- $ledRel 2>$null | Out-Null
                    Write-Step "OK" ("R" + $i + " 台帳聯集 " + $Matches[1] + " 筆(append-only;零取單邊)")
                } else {
                    Write-Step "FAIL" ("R" + $i + " 台帳聯集敗=停手不硬合(誠實):" + $res)
                    break
                }
            }
        }
        if (Test-Path -LiteralPath (Join-Path $Root ".git\MERGE_HEAD")) {
            & git -C $Root -c user.name="tonykuni" -c user.email="tonyhuang0122@gmail.com" commit -q --no-edit 2>$null | Out-Null
            Write-Step "OK" ("R" + $i + " 完成合併提交")
        }
        & git -C $Root fetch -q origin $branch 2>$null | Out-Null
        $behind = (& git -C $Root rev-list --count ("HEAD..origin/" + $branch) 2>$null)
        if (-not $behind) { $behind = "0" }
        if ([int]$behind -eq 0) {
            Write-Step "OK" ("R" + $i + " 已與 origin/" + $branch + " 齊平=收斂")
            break
        }
        Write-Step "RUN" ("R" + $i + " 遠端獨有 " + $behind + " 提交 → merge --no-ff")
        $mo = (& git -C $Root merge --no-ff --no-edit ("origin/" + $branch) 2>&1 | Out-String)
        if ($mo -match "local changes|overwritten by merge") {
            & git -C $Root stash push -u -q -m "via-unstick" 2>$null | Out-Null
            Write-Step "OK" ("R" + $i + " 髒樹擋 merge → 已 stash(合併後還原)")
            $mo = (& git -C $Root merge --no-ff --no-edit ("origin/" + $branch) 2>&1 | Out-String)
        }
    }
    # 殘留 stash 還原(衝突時台帳聯集、其餘取合併後版;絕不留衝突標記)
    $stashes = @(& git -C $Root stash list 2>$null) | Where-Object { $_ -match "via-unstick" }
    if ($stashes.Count -and $medic) {
        $pop = (& git -C $Root stash pop 2>&1 | Out-String)
        if ($pop -match "CONFLICT|conflict") {
            Write-Step "RUN" "stash 還原起衝突 → 委派醫生裁決(台帳聯集;零衝突標記)"
            & python $medic resolve --apply --root $Root 2>$null | Out-Null
            & git -C $Root -c user.name="tonykuni" -c user.email="tonyhuang0122@gmail.com" commit -q -m "via-unstick:stash 還原衝突按律裁決" 2>$null | Out-Null
        }
        Write-Step "OK" "stash 已還原"
    }
}

# ---- ③ 驗收 ----
$u1 = @(& git -C $Root diff --name-only --diff-filter=U 2>$null) | Where-Object { $_ }
$head1 = (& git -C $Root rev-parse --short HEAD 2>$null)
$behind1 = (& git -C $Root rev-list --count ("HEAD..origin/" + $branch) 2>$null)
if (-not $behind1) { $behind1 = "0" }
$regTail = Get-Tail $via "Register-VIA-Commands-v*.ps1"
$medTail = Get-Tail $regDir "CGC_MDL143_MergeMedic_v*.py"
Write-Host ""
Write-Host "=== 驗收 ==="
Write-Step $(if ($u1.Count) { "FAIL" } else { "OK" }) ("未合併殘留 " + $(if ($u1.Count) { ($u1 -join ", ") } else { "零" }))
Write-Step $(if ([int]$behind1 -eq 0) { "OK" } else { "WARN" }) ("HEAD " + $head0 + " → " + $head1 + " · 落後遠端 " + $behind1 + " 提交")
Write-Step "OK" ("尾版短令冊 " + $(if ($regTail) { Split-Path $regTail -Leaf } else { "(缺)" }))
Write-Step "OK" ("尾版拉齊醫生 " + $(if ($medTail) { Split-Path $medTail -Leaf } else { "(缺)" }))

$rc = if ($u1.Count -or [int]$behind1 -ne 0) { 1 } else { 0 }
if (-not $NoEnter -and $regTail -and $rc -eq 0) {
    Write-Host ""
    Write-Step "RUN" "點源尾版短令冊"
    . $regTail
}
if ($rc -ne 0) {
    Write-Host ""
    Write-Step "WARN" "未完全收斂。現場已保留(零 force 零刪除);把上面整段畫面貼回對話即可續解。"
}
if ($MyInvocation.InvocationName -eq ".") { $global:LASTEXITCODE = $rc; return } else { exit $rc }

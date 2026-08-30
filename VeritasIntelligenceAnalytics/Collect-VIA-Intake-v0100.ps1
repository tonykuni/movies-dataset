# =====================================================================
# Collect-VIA-Intake-v0100.ps1 — Downloads 收容器(批245;操作員令)
# =====================================================================
# 操作員令:「引擎功能化 系統整合引擎 如先前——類似工具整合優化進去」。
# 八件名冊自 Downloads 收容入 references/intake 收容區:
#   hash 定生死((1)(2) 重複件同 hash=去重;異 hash=取最新,舊列 superseded)
#   只增不減(Downloads 原件零觸碰;既有收容夾不覆寫,異 hash 另開 _r 夾)
#   每夾 _INTAKE_MANIFEST.json 存證(來源/sha256/時戳/讓位清單)
#   收畢自動 git add+commit+雙推(main+作業分支)→雲端接手引擎化整合
# 用法:pwsh -File .\Collect-VIA-Intake-v0100.ps1 [-DryRun]
# =====================================================================
param([switch]$DryRun)
$ErrorActionPreference = "Stop"
$VIA = Split-Path -Parent $MyInvocation.MyCommand.Path
$DL = Join-Path $env:USERPROFILE "Downloads"
$BRANCH = "claude/via-system-followup-tz7k9t"

$Roster = @(
    @{ Pattern = "VAP_Chart_Library*.json";                     Target = "functional modules\VAP\references\intake";  Kind = "file" },
    @{ Pattern = "VIA_Toolchain_Bundle_*.zip";                  Target = "supportive modules\references\intake";      Kind = "zip"  },
    @{ Pattern = "PDFRegressionEvidence_v*.zip";                Target = "functional modules\VRN\references\intake";  Kind = "zip"  },
    @{ Pattern = "AttachmentFixedOutput_v*.zip";                Target = "functional modules\VRN\references\intake";  Kind = "zip"  },
    @{ Pattern = "GenericLayoutEngine_AllEngines_v*.zip";       Target = "functional modules\VRN\references\intake";  Kind = "zip"  },
    @{ Pattern = "Veritas_OmniFormat_Intelligence_Engine_v*.zip"; Target = "functional modules\VRN\references\intake"; Kind = "zip" },
    @{ Pattern = "VIA_Hybrid_TW_Flow_Engine_v*.zip";            Target = "functional modules\VDF\references\intake";  Kind = "zip"  }
)

function Get-CleanStem([string]$Name) {
    # 去 " (1)" 重複尾綴+副檔名 → 收容夾名 <stem>_b245
    $stem = [IO.Path]::GetFileNameWithoutExtension($Name) -replace "\s*\(\d+\)\s*$", ""
    return ($stem.Trim() + "_b245")
}

$log = @(); $newDirs = @()
Write-Host "=== VIA Downloads 收容器 v0100(批245)· hash 定生死 · 只增不減 ===" -ForegroundColor Cyan
foreach ($r in $Roster) {
    $hits = @(Get-ChildItem -Path $DL -Filter $r.Pattern -File -ErrorAction SilentlyContinue)
    if (-not $hits) {
        Write-Host ("  [SKIP] " + $r.Pattern + " · Downloads 未尋獲(誠實)") -ForegroundColor Yellow
        $log += @{ pattern = $r.Pattern; status = "SKIP_NOT_FOUND" }; continue
    }
    # hash 定生死:同 hash 去重;異 hash 取最新,其餘列 superseded
    $byHash = @{}
    foreach ($h in $hits) {
        $sha = (Get-FileHash -Algorithm SHA256 -Path $h.FullName).Hash
        if (-not $byHash.ContainsKey($sha)) { $byHash[$sha] = $h }
    }
    $pick = $byHash.Values | Sort-Object LastWriteTime | Select-Object -Last 1
    $pickSha = ($byHash.GetEnumerator() | Where-Object { $_.Value.FullName -eq $pick.FullName }).Key
    $superseded = @($byHash.GetEnumerator() | Where-Object { $_.Value.FullName -ne $pick.FullName } |
        ForEach-Object { @{ file = $_.Value.Name; sha256 = $_.Key } })

    $destRoot = Join-Path $VIA $r.Target
    $destName = Get-CleanStem $pick.Name
    $dest = Join-Path $destRoot $destName
    $mf = Join-Path $dest "_INTAKE_MANIFEST.json"
    if (Test-Path $mf) {
        $old = Get-Content $mf -Raw | ConvertFrom-Json
        if ($old.sha256 -eq $pickSha) {
            Write-Host ("  [SKIP] " + $pick.Name + " · 同 hash 已收容(冪等)") -ForegroundColor DarkGray
            $log += @{ pattern = $r.Pattern; status = "SKIP_SAME_HASH"; dir = $destName }; continue
        }
        $destName = $destName + "_r" + (Get-Date -Format "yyyyMMddHHmm")   # 異 hash=另開夾不覆寫
        $dest = Join-Path $destRoot $destName
        $mf = Join-Path $dest "_INTAKE_MANIFEST.json"
    }
    if ($DryRun) {
        Write-Host ("  [DRY ] " + $pick.Name + " → " + $r.Target + "\" + $destName) -ForegroundColor Cyan
        $log += @{ pattern = $r.Pattern; status = "DRY_RUN"; dir = $destName }; continue
    }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    if ($r.Kind -eq "zip") {
        Expand-Archive -Path $pick.FullName -DestinationPath $dest -Force
    } else {
        Copy-Item -Path $pick.FullName -Destination $dest -Force
    }
    $manifest = @{
        source = $pick.Name; source_path = $pick.FullName; sha256 = $pickSha
        collected_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        batch = "b245"; superseded = $superseded
        note = "hash 定生死去重;Downloads 原件零觸碰;異 hash 另開 _r 夾(只增不減)"
    }
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $mf -Encoding UTF8
    $n = @(Get-ChildItem -Path $dest -Recurse -File).Count
    Write-Host ("  [OK  ] " + $pick.Name + " → " + $destName + "(" + $n + " 檔;讓位 " + $superseded.Count + ")") -ForegroundColor Green
    $log += @{ pattern = $r.Pattern; status = "OK"; dir = $destName; files = $n }
    $newDirs += (Join-Path $r.Target $destName)
}

$ok = @($log | Where-Object { $_.status -eq "OK" }).Count
$sk = @($log | Where-Object { $_.status -like "SKIP*" }).Count
Write-Host ("  [計] OK " + $ok + " · SKIP " + $sk + " · 名冊 " + $Roster.Count + "(誠實三態)") -ForegroundColor Cyan

if ($DryRun -or $newDirs.Count -eq 0) {
    Write-Host "  [git] 無新收容或 DryRun=不提交(誠實)" -ForegroundColor Yellow
    exit 0
}
# 自動提交雙推(僅新收容夾;含 commit trailers)
foreach ($d in $newDirs) { git -C $VIA add -- "$d" }
$msgFile = Join-Path $env:TEMP ("via_intake_" + (Get-Date -Format "HHmmss") + ".txt")
@(
    "批245 收容:Downloads 八件名冊入 intake(工作站收容器 v0100)"
    ""
    ("收容 " + $ok + " 夾:" + (($newDirs | ForEach-Object { Split-Path $_ -Leaf }) -join "、"))
    "hash 定生死去重;只增不減;每夾 _INTAKE_MANIFEST.json 存證。"
    "候雲端接手:引擎功能化整合(操作員令=類似功能整併優化)。"
    ""
    "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
    "Claude-Session: https://claude.ai/code/session_01R2d69oa1AGvnPVwjSUdSv5"
) | Set-Content -Path $msgFile -Encoding UTF8
git -C $VIA commit -F $msgFile
git -C $VIA push origin HEAD:main
git -C $VIA push -u origin ("HEAD:" + $BRANCH)
Write-Host "  [git] 收容已雙推(main+作業分支)→回雲端貼實錄即續整合" -ForegroundColor Green

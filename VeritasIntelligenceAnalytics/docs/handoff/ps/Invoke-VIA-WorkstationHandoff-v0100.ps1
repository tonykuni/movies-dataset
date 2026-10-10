# CELERITAS-TEMPLATE-JOIN v1
# Invoke-VIA-WorkstationHandoff-v0100.ps1 — 工作站補跑交接收據(容器缺 polars / akshare / pwsh / reportlab 的案)
# 操作員裁定 2026-10-10(PR #518):這幾案在雲端容器跑不了(缺套件、不裝;或要工作站的 66 份真 sidecar 庫),改在工作站經 VCGC 唯一入口跑。
#   ① 逐案 `handoff test <case>`(經 VCGC;不 pip install、不改環境)
#   ② 收據 rc 0 且驗收標記出現 → 交接冊對應待辦 PENDING → VERIFIED(帶 verified_at / verified_on);沒過照舊 PENDING,不假綠
#   ③ `handoff check`:綠才跑 `handoff checkpoint`;紅就照印判決行停下
#   ④ 不自動提交、不推送:最後印出要提交的檔與指令,由操作員確認
# VRN 真失敗(SUP_MDL749 v0116 正則範例兩條 → vrn_ssot_consistency)等操作員裁定,不在本腳本。
[CmdletBinding()]
param(
    [string]$Via = '',
    [string]$PythonExe = 'python',
    [string[]]$Cases = @('qg_onebridge', 'vdf_akshare_v0101', 'vdf_akshare_v0102', 'via_unified', 'vdfvrn_readiness', 'vrn_layout', 'cov_vrn_firstpage_engine'),
    [switch]$NoCheckpoint
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try { $VIAPSAccelProbe = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics' }
  while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) { $m = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"; if (Test-Path $m) { . $m; break }; $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent } } catch { }
# ===== [VIA:PS-ACCEL:END] =====
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $Via) {
    $probe = $PSScriptRoot
    while ($probe -and -not (Test-Path (Join-Path $probe 'supportive modules\registry'))) { $probe = Split-Path $probe -Parent }
    $Via = $probe
}
if (-not $Via -or -not (Test-Path (Join-Path $Via 'supportive modules\registry'))) { Write-Host '[停] 找不到 VeritasIntelligenceAnalytics 根(用 -Via 指定)'; exit 1 }
$registry = Join-Path $Via 'supportive modules\registry'
$vcgc = (Get-ChildItem $registry -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' -File |
    Sort-Object { [int]([regex]::Match($_.BaseName, '_v(\d+)$').Groups[1].Value) } | Select-Object -Last 1).FullName
if (-not $vcgc) { Write-Host '[停] VCGC 入口不在'; exit 1 }
$env:VIA_FROM_VCGC = 'YES'
$env:VIA_VCGC_PUSH = 'NO'

Push-Location $Via
try {
    $rows = @()
    foreach ($case in $Cases) {
        Write-Host ("[跑] handoff test " + $case)
        $out = & $PythonExe $vcgc handoff test $case 2>&1 | Out-String
        $rc = $LASTEXITCODE
        $receipt = Join-Path $Via ("docs\handoff\evidence\" + $case + ".json")
        $ok = $false
        if (Test-Path $receipt) {
            $j = Get-Content $receipt -Raw -Encoding utf8 | ConvertFrom-Json
            $ok = ($j.rc -eq 0) -and [bool]$j.target_marker_seen
        }
        $rows += [pscustomobject]@{ Case = $case; Rc = $rc; Pass = $ok }
        Write-Host ("  → rc {0} · 標記 {1}" -f $rc, $(if ($ok) { '對上' } else { '沒對上(照舊 PENDING)' }))
    }

    # ② 只把「這次真的過了」的案,從 PENDING 轉 VERIFIED(冊用 Python 寫,保留原格式 indent=2)
    $passed = @($rows | Where-Object { $_.Pass } | ForEach-Object { $_.Case })
    if ($passed.Count -gt 0) {
        $flip = @'
import json, sys, datetime, pathlib
p = pathlib.Path("supportive modules/registry/VIA_Handoff_Continuity_SSOT_v0100.json")
raw = p.read_text(encoding="utf-8"); d = json.loads(raw)
now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
cases = set(sys.argv[1:]); n = 0
for w in d["work_items"]:
    if w.get("case") in cases and w.get("state") == "PENDING":
        w["state"] = "VERIFIED"; w["verified_at"] = now; w["verified_on"] = "workstation"
        w["receipt"] = "docs/handoff/evidence/" + w["case"] + ".json"
        for k in ("owner", "reason", "next"):
            w.pop(k, None)
        n += 1
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
print("[轉態] PENDING → VERIFIED " + str(n) + " 項 · " + now)
'@
        $flip | & $PythonExe - @passed
    }

    # ③ 冊改過 → 依賴冊的收據(numbering 等)要重跑;再看交接閘
    if ($passed.Count -gt 0) {
        foreach ($dep in @('numbering')) { & $PythonExe $vcgc handoff test $dep | Out-Null }
    }
    $check = & $PythonExe $vcgc handoff check 2>&1 | Out-String
    $head = ($check -split "`n" | Where-Object { $_ -match '^\[交接防遺漏\]' } | Select-Object -Last 1)
    Write-Host $head
    $check -split "`n" | Where-Object { $_ -match '^\[RED\]' } | ForEach-Object { Write-Host ("  " + $_) }
    if ($LASTEXITCODE -eq 0 -and -not $NoCheckpoint) {
        & $PythonExe $vcgc handoff checkpoint
    } elseif ($LASTEXITCODE -ne 0) {
        Write-Host '[停] 交接閘還沒綠:不寫 checkpoint(上面紅行就是還缺的;VRN 兩件等裁定)'
    }

    Write-Host ''
    Write-Host '== 結果 =='
    $rows | Format-Table -AutoSize | Out-String | Write-Host
    Write-Host '要提交的檔(確認後再執行):'
    Write-Host '  git add "docs/handoff/evidence" "supportive modules/registry/VIA_Handoff_Continuity_SSOT_v0100.json" "docs/handoff/HANDOFF_latest.json"'
    Write-Host '  git commit -m "Workstation handoff receipts (qg / akshare / pwsh / reportlab cases)"'
    Write-Host '  git push'
}
finally {
    Pop-Location
}

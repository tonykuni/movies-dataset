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
Test-VIA-TheoryAudit.ps1 — 今日五引擎「理論正確性」獨立稽核(ONE PS CODE)
===========================================================================
與各引擎 selftest 的差異:selftest 是引擎自證;本稽核是 PowerShell 端的
**獨立甲骨文** — 自算期望值、自讀 SSOT、自算 SHA256、從原始產物重新導出
結論,再與引擎輸出對質。同一 bug 藏在實作與自測裡也會被抓出來。

14 項理論斷言:
  A 工作流引擎:A1 DAG 環必拒 · A2 Cron 手算真值對照
  B VAP 繪圖:  B1 視覺鎖 α≡SSOT(PS 自讀 spec 對 HTML)· B2 雙軸同格數+刻度倍數律
  C ChipWar:   C1 洩漏必虛胖(leaky IC>clean)· C2 CCF 回收嵌入 lag(負控制)
               C3 FOMO 四閘門 PS 重導出 · C4 Walk-Forward 誠實缺口≥0
  D MultiFactor:D1 SHA256 manifest 獨立重算 · D2 投影不得 Confirmed
               D3 模型准入規則(allow ⇒ 領先+增量+樣本外)
  E TALib:     E1 SMA 甲骨文(PS 自算均值對質)· E2 Adj 鐵律雙態(adj/raw)
               E3 BBANDS 恆等式(mid=SMA20 · upper=mid+2σ)

用法:  .\Test-VIA-TheoryAudit.ps1        (或經啟動器:.\VIA_WorkflowEngine.ps1 theory)
#>
$ErrorActionPreference = 'Stop'
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

# ── python 偵測(啟動器 -Python 經 VIA_PYTHON 透傳;否則 py -3 → python → python3)──
$PyExe = ''
$PyPre = @()
if ($env:VIA_PYTHON -and (Get-Command $env:VIA_PYTHON -ErrorAction SilentlyContinue)) {
    $PyExe = $env:VIA_PYTHON
}
foreach ($cand in @(@('py', @('-3')), @('python', @()), @('python3', @()))) {
    if ($PyExe -ne '') { break }
    if (Get-Command $cand[0] -ErrorAction SilentlyContinue) {
        $probe = @($cand[1]) + @('--version')
        $v = (& $cand[0] $probe 2>&1 | Out-String)
        if (($LASTEXITCODE -eq 0) -and ($v -match 'Python 3')) {
            $PyExe = $cand[0]
            $PyPre = @($cand[1])
            break
        }
    }
}
if ($PyExe -eq '') { Write-Host '誠實 FAIL:找不到 Python 3'; exit 1 }

$Root = $PSScriptRoot
$WF   = Join-Path $Root 'VIA_WorkflowEngine.py'
$VAP  = Join-Path $Root 'functional modules\VAP\engine\VAP_ENG003_AutoplotSeabornPlotly_v0100.py'
$SPEC = Join-Path $Root 'functional modules\VAP\spec\ssot\vap_spec.json'
$CW   = Join-Path $Root 'functional modules\ChipWar'
$MF   = Join-Path $Root 'functional modules\MultiFactor'
$TA   = Join-Path $Root 'functional modules\TALib\VIA_ENG003_TALibEngine.py'
$Tmp  = Join-Path ([System.IO.Path]::GetTempPath()) ("via_theory_" + (Get-Date -Format 'HHmmss'))
New-Item -ItemType Directory -Path $Tmp -Force | Out-Null

$Results = New-Object System.Collections.Generic.List[object]
function Check {
    param([string]$Id, [string]$Name, [scriptblock]$Body)
    try {
        & $Body
        [void]$Results.Add(@{ id = $Id; name = $Name; st = 'PASS'; note = '' })
    } catch {
        $st = if ($_.Exception.Message -like 'SKIP:*') { 'SKIP' } else { 'FAIL' }
        [void]$Results.Add(@{ id = $Id; name = $Name; st = $st
                              note = ($_.Exception.Message -replace "`n", ' ').Substring(0, [Math]::Min(88, $_.Exception.Message.Length)) })
    }
}
function Invoke-Py {
    param([string[]]$A)
    $full = @($PyPre) + $A
    $out = & $PyExe $full 2>&1 | Out-String
    return @{ code = $LASTEXITCODE; out = $out }
}
function Assert {
    param([bool]$Cond, [string]$Msg)
    if (-not $Cond) { throw $Msg }
}

# ═══ A 工作流引擎 ═══════════════════════════════════════════════════════════
Check 'A1' 'DAG 環必拒(雙層:JSON 前置閘 + Kahn 環偵測)' {
    # 第一層:環流程檔必被 CLI 拒絕(定義序參照完整性先攔 — 防禦縱深第一閘)
    $cyc = Join-Path $Tmp 'cyclic.json'
    '{"name":"cyc","steps":[{"name":"a","command":"echo a","depends_on":["b"]},{"name":"b","command":"echo b","depends_on":["a"]}]}' |
        Set-Content -Path $cyc -Encoding UTF8
    $r = Invoke-Py @($WF, 'run', $cyc)
    Assert ($r.code -ne 0) 'A→B→A 環流程檔竟被接受執行'
    # 第二層:直接構圖繞過前置閘(加點後改 depends_on),Kahn 環分支必須點名環
    $probe = Join-Path $Tmp 'cycle_probe.py'
    @(
        'import sys',
        "sys.path.insert(0, r'$Root')",
        'from VIA_WorkflowEngine import WorkflowSpec',
        "wf = WorkflowSpec('cyc')",
        "wf.task('a', command='echo a')",
        "wf.task('b', command='echo b', depends_on=['a'])",
        "wf.tasks['a'].depends_on.append('b')   # a->b->a",
        'try:',
        '    wf.validate()',
        'except ValueError as e:',
        "    print('REJECTED:', e)",
        '    sys.exit(0)',
        "print('ACCEPTED')",
        'sys.exit(3)'
    ) -join "`n" | Set-Content -Path $probe -Encoding UTF8
    $r2 = Invoke-Py @($probe)
    Assert (($r2.code -eq 0) -and ($r2.out -match 'REJECTED')) ('直接構環未被 validate 拒絕:' + $r2.out.Substring(0, [Math]::Min(80, $r2.out.Length)))
    Assert (($r2.out -match '環') -or ($r2.out -match 'cycle')) '拒絕原因未點名環(cycle)'
}

Check 'A2' 'Cron 手算真值對照(0 1 * * * 與工作日 */15)' {
    $code = "import sys; sys.path.insert(0, r'$Root'); " +
            "from VIA_WorkflowEngine import Cron; from datetime import datetime; " +
            "print(Cron('0 1 * * *').next_after(datetime(2026, 8, 10, 0, 30))); " +
            "print(Cron('*/15 9-17 * * 1-5').matches(datetime(2026, 8, 10, 9, 45)))"
    $r = Invoke-Py @('-c', $code)
    Assert ($r.code -eq 0) ("Cron 執行失敗:" + $r.out)
    Assert ($r.out -match '2026-08-10 01:00:00') ("next_after 期望 2026-08-10 01:00,得到:" + $r.out)
    Assert ($r.out -match 'True') '2026-08-10(週一)09:45 應命中 */15 9-17 * * 1-5'
}

# ═══ B VAP 繪圖 ═════════════════════════════════════════════════════════════
Check 'B1' '視覺鎖 α≡SSOT(PS 自讀 spec 對 plotly HTML)' {
    $spec = Get-Content -Raw $SPEC | ConvertFrom-Json
    $alpha = [double]$spec.fill.areaUnderLine
    $out = Join-Path $Tmp 'vap_area'
    $r = Invoke-Py @($VAP, 'render', '--chart', 'area', '--backend', 'plotly',
                     '--out', $out, '--plotlyjs', 'directory')
    Assert ($r.code -eq 0) ("area 渲染失敗:" + $r.out)
    $html = Get-Content -Raw (Join-Path $out 'vap_ch_02_plotly.html')
    $pat = 'rgba\(\d+,\d+,\d+,' + [regex]::Escape($alpha.ToString([System.Globalization.CultureInfo]::InvariantCulture)) + '\)'
    Assert ($html -match $pat) ("HTML 填色透明度未見 SSOT 值 " + $alpha)
    Assert (-not ($html -match 'rgba\(\d+,\d+,\d+,0\.4\)')) '出現 0.4 視覺鎖回歸值!'
}

Check 'B2' '雙軸同格數 + 刻度倍數律(2/2.5/5/10)' {
    $code = "import importlib.util, json; " +
            "s = importlib.util.spec_from_file_location('v', r'$VAP'); " +
            "v = importlib.util.module_from_spec(s); s.loader.exec_module(v); " +
            "sp = v.Spec(v.find_ssot_dir(None)); " +
            "l, r = v.dual_ticks(0, 97.3, -2.7, 3.1, sp); " +
            "print(json.dumps({'l': l, 'r': r}))"
    $r = Invoke-Py @('-c', $code)
    Assert ($r.code -eq 0) ("dual_ticks 失敗:" + $r.out)
    $t = ($r.out.Trim() -split "`n")[-1] | ConvertFrom-Json
    Assert ($t.l.Count -eq $t.r.Count) ("左右刻度數不等:{0} vs {1}" -f $t.l.Count, $t.r.Count)
    foreach ($ticks in @($t.l, $t.r)) {
        $step = [double]($ticks[1] - $ticks[0])
        $norm = $step / [math]::Pow(10, [math]::Floor([math]::Log10($step)))
        $ok = @(1.0, 2.0, 2.5, 5.0) | Where-Object { [math]::Abs($norm - $_) -lt 1e-9 }
        Assert ($ok.Count -eq 1) ("步距 {0} 正規化 {1} 不在 2/2.5/5/10 倍數律" -f $step, $norm)
    }
}

# ═══ C ChipWar(讀 staging 原始產物;缺件先跑全鏈)═══════════════════════════
$Stag = Join-Path $CW '_generated\staging'
if (-not (Test-Path (Join-Path $Stag 'chipwar_run.json'))) {
    Write-Host '  [前置] ChipWar staging 缺件 → 先跑全鏈…'
    $null = Invoke-Py @($WF, 'master', (Join-Path $CW 'chipwar_params.json'))
}

Check 'C1' '洩漏必虛胖(leaky IC 均值 > clean;lookahead 理論)' {
    $d = Get-Content -Raw (Join-Path $Stag 'chipwar_run.json') | ConvertFrom-Json
    $clean = ($d.ic_groups | Where-Object { $_.mode -eq 'clean' } | Measure-Object -Property spearman_ic -Average).Average
    $leaky = ($d.ic_groups | Where-Object { $_.mode -eq 'leaky' } | Measure-Object -Property spearman_ic -Average).Average
    Assert ($leaky -gt $clean) ("leaky({0:n3}) 應 > clean({1:n3}) — 洩漏隔離失效" -f $leaky, $clean)
}

Check 'C2' 'CCF 回收嵌入 lag(負控制設計)' {
    $g = (Get-Content -Raw (Join-Path $Stag 'social_run.json') | ConvertFrom-Json).gate
    $true_lag = [int]$g.embedded_true_lag_bd
    $best = [int]$g.ccf_best_lag
    Assert ([math]::Abs($best - (-$true_lag)) -le 2) ("嵌入 −{0} 但 CCF 峰值 {1}(容差±2)" -f $true_lag, $best)
}

Check 'C3' 'FOMO 四閘門 PS 重導出(不信 pass 欄)' {
    $d = Get-Content -Raw (Join-Path $Stag 'fomo_index_run.json') | ConvertFrom-Json
    $g = $d.gates
    $ic_ok = ([double]$g.G_ic.value) -lt -0.05
    $diffs = 0
    for ($i = 1; $i -lt $g.G_mono.value.Count; $i++) {
        if ([double]$g.G_mono.value[$i] -gt [double]$g.G_mono.value[$i - 1]) { $diffs++ }
    }
    $mono_ok = $diffs -le 1
    $null_ok = ([double]$g.G_null.value) -lt 0.05
    $oos_ok = ([math]::Sign([double]$g.G_oos.value[0]) -eq [math]::Sign([double]$g.G_oos.value[1]))
    foreach ($pair in @(@('G_ic', $ic_ok), @('G_mono', $mono_ok), @('G_null', $null_ok), @('G_oos', $oos_ok))) {
        $stored = [bool]$g.($pair[0]).pass
        Assert ($stored -eq $pair[1]) ("{0}:引擎 pass={1} 但 PS 重導出={2}" -f $pair[0], $stored, $pair[1])
    }
    $expect = if ($ic_ok -and $mono_ok -and $null_ok -and $oos_ok) { 'PROVED_VALID' } else { 'FAILED_GATES' }
    Assert ($d.gate.verdict -eq $expect) ("verdict {0} 與重導出 {1} 不符" -f $d.gate.verdict, $expect)
}

Check 'C4' 'Walk-Forward 誠實缺口 ≥ 0(過擬合理論:樣本內≥樣本外)' {
    $wf = (Get-Content -Raw (Join-Path $Stag 'xmkt_run.json') | ConvertFrom-Json).wf_summary
    $anyPos = $false
    foreach ($row in $wf) {
        $gap = [double]$row.insample_ic_mean - [double]$row.oos_ic_mean
        Assert ([math]::Abs($gap - [double]$row.honesty_gap) -lt 1e-6) ("honesty_gap 欄與 PS 重算不符({0})" -f $row.criteria)
        if ($gap -gt 0) { $anyPos = $true }
    }
    Assert $anyPos '無任何正缺口 — 優化器聲稱樣本外優於樣本內,理論可疑'
}

# ═══ D MultiFactor ══════════════════════════════════════════════════════════
Check 'D1' 'SHA256 manifest PS 獨立重算' {
    $man = Get-Content -Raw (Join-Path $MF 'engines\VIA_MF_ENGINE_SHA256_MANIFEST_v0100.json') | ConvertFrom-Json
    foreach ($entry in $man) {
        $local = Join-Path $MF ('engines\' + $entry.name)
        if (-not (Test-Path $local)) { continue }   # manifest 可含未歸檔項
        $h = (Get-FileHash -Algorithm SHA256 -Path $local).Hash
        Assert ($h -eq $entry.sha256.ToUpper()) ("{0} 雜湊不符!repo={1} manifest={2}" -f $entry.name, $h.Substring(0, 8), $entry.sha256.Substring(0, 8))
    }
}

Check 'D2' '投影不得 Confirmed(治理鐵律掃 ledger)' {
    $csv = Import-Csv (Join-Path $MF 'runs\RUN_20260807_105152_VIA_MF_TEST_VALIDATE_SIM_v0100\factor_relation_ledger.csv')
    foreach ($row in $csv) {
        Assert ($row.evidence_status -ne 'Confirmed') ("{0} 的 evidence_status=Confirmed 違反投影治理" -f $row.factor_id)
    }
    $sim = Import-Csv (Join-Path $MF 'runs\RUN_20260807_105152_VIA_MF_TEST_VALIDATE_SIM_v0100\simulation_ledger.csv')
    foreach ($row in $sim) {
        Assert ($row.evidence_status -like '*NotConfirmed*') ("模擬 {0} 未標 NotConfirmed" -f $row.scenario_id)
    }
}

Check 'D3' '模型准入規則(allow ⇒ 領先+增量+樣本外顯著)' {
    $csv = Import-Csv (Join-Path $MF 'runs\RUN_20260807_105152_VIA_MF_TEST_VALIDATE_SIM_v0100\factor_relation_ledger.csv')
    $allowN = 0
    foreach ($row in $csv) {
        if ($row.model_permission -eq 'allow') {
            $allowN++
            Assert ($row.lead_label -eq 'leading') ("{0} allow 但非 leading" -f $row.factor_id)
            Assert ($row.impact_label -eq 'incremental_impact_detected') ("{0} allow 但無增量影響" -f $row.factor_id)
            Assert ([double]$row.oos_binom_p_value -lt 0.05) ("{0} allow 但 OOS p={1} 不顯著" -f $row.factor_id, $row.oos_binom_p_value)
            Assert ($row.causal_status -eq 'supported') ("{0} allow 但 causal_status={1}" -f $row.factor_id, $row.causal_status)
        }
    }
    Assert ($allowN -ge 1) 'ledger 無任何 allow 列可稽核'
}

# ═══ E TALib(PS 甲骨文自算)═══════════════════════════════════════════════
Check 'E1' 'SMA 甲骨文(PS 自算 3 期均值對質)' {
    $src = Join-Path $Tmp 'tiny.csv'
    "date,close`nD1,1`nD2,2`nD3,3`nD4,4`nD5,5`nD6,6" | Set-Content -Path $src -Encoding UTF8
    $out = Join-Path $Tmp 'tiny_sma.csv'
    $r = Invoke-Py @($TA, 'compute', '--file', $src, '--indicators', 'sma', '--period', '3', '--out', $out)
    Assert ($r.code -eq 0) ("compute 失敗:" + $r.out)
    $rows = Import-Csv $out
    for ($i = 2; $i -lt $rows.Count; $i++) {
        $expect = ([double]$rows[$i - 2].close + [double]$rows[$i - 1].close + [double]$rows[$i].close) / 3.0
        Assert ([math]::Abs([double]$rows[$i].sma - $expect) -lt 1e-9) ("第 {0} 列 SMA {1} ≠ PS 自算 {2}" -f $i, $rows[$i].sma, $expect)
    }
}

Check 'E2' 'Adj 鐵律雙態(有 adj 全轉 adj;缺則 raw)' {
    $adj = Join-Path $Tmp 'adj.csv'
    "date,close,adj_close`nD1,10,5`nD2,10,5`nD3,10,5" | Set-Content -Path $adj -Encoding UTF8
    $o1 = Join-Path $Tmp 'adj_out.csv'
    $r1 = Invoke-Py @($TA, 'compute', '--file', $adj, '--indicators', 'sma', '--period', '2', '--out', $o1)
    Assert ($r1.out -match 'price_basis=adj') ('adj 欄在位卻未走 adj:' + $r1.out)
    $row = (Import-Csv $o1)[0]
    Assert ([math]::Abs([double]$row.close - 5.0) -lt 1e-9) ("close 應=adj(5),得到 " + $row.close)
    $raw = Join-Path $Tmp 'raw.csv'
    "date,close`nD1,10`nD2,10`nD3,10" | Set-Content -Path $raw -Encoding UTF8
    $r2 = Invoke-Py @($TA, 'compute', '--file', $raw, '--indicators', 'sma', '--period', '2', '--out', (Join-Path $Tmp 'raw_out.csv'))
    Assert ($r2.out -match 'price_basis=raw') ('無 adj 欄應誠實 raw:' + $r2.out)
}

Check 'E3' 'BBANDS 恆等式(mid≡SMA20 · upper≡mid+2σ)' {
    $s = Join-Path $Tmp 'ohlcv.csv'
    $null = Invoke-Py @($TA, 'sample', '-o', $s)
    $out = Join-Path $Tmp 'bb.csv'
    $r = Invoke-Py @($TA, 'compute', '--file', $s, '--indicators', 'sma,stddev,bbands', '--period', '20', '--out', $out)
    Assert ($r.code -eq 0) ("compute 失敗:" + $r.out)
    $rows = Import-Csv $out
    $checked = 0
    foreach ($row in $rows) {
        if (($row.sma -ne '') -and ($row.bb_mid -ne '') -and ($row.stddev -ne '')) {
            Assert ([math]::Abs([double]$row.bb_mid - [double]$row.sma) -lt 1e-4) '中軌≠SMA20'
            $up = [double]$row.sma + 2.0 * [double]$row.stddev
            Assert ([math]::Abs([double]$row.bb_upper - $up) -lt 1e-3) ("上軌 {0} ≠ SMA+2σ {1}" -f $row.bb_upper, $up)
            $checked++
        }
    }
    Assert ($checked -gt 100) ("有效檢核列僅 " + $checked)
}

# ═══ 總結 ═══════════════════════════════════════════════════════════════════
Write-Host ''
Write-Host '════════════════════════════════════════════════════════════════'
Write-Host ' VIA 今日五引擎理論稽核(PowerShell 獨立甲骨文)'
Write-Host '════════════════════════════════════════════════════════════════'
$fails = 0
foreach ($r in $Results) {
    if ($r.st -eq 'FAIL') { $fails++ }
    $note = if ($r.note) { '  ← ' + $r.note } else { '' }
    Write-Host ('  [{0}] {1,-3} {2}{3}' -f $r.st, $r.id, $r.name, $note)
}
$pass = @($Results | Where-Object { $_.st -eq 'PASS' }).Count
$skip = @($Results | Where-Object { $_.st -eq 'SKIP' }).Count
Write-Host '────────────────────────────────────────────────────────────────'
Write-Host ('  合計:{0} PASS / {1} SKIP / {2} FAIL(共 {3} 項理論斷言)' -f $pass, $skip, $fails, $Results.Count)
if ($fails -eq 0) {
    Write-Host '  [OK  ] 全部理論斷言由 PS 獨立驗證通過 — 非引擎自證。'
} else {
    Write-Host '  [FAIL] 有理論斷言被獨立稽核推翻 — 逐條檢視上表。'
}
Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
exit $(if ($fails -eq 0) { 0 } else { 1 })

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

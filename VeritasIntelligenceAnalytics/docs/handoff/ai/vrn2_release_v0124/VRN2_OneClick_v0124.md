# VRN-2 v0124 一鍵 PowerShell(整合全流程)

貼進 PowerShell(Windows PowerShell 5.1 或 PowerShell 7)直接執行;或存成 `Run-VRN2-v0124.ps1`(UTF-8 含 BOM)後 `powershell -ExecutionPolicy Bypass -File Run-VRN2-v0124.ps1`。

| 步驟 | 做什麼 |
|---|---|
| ① | 第一步提高 CPU / DRAM:CPU 閒(<60%)時本視窗升「高於標準」(子行程繼承 · 結束還原)· 釋放記憶體 |
| ② | 接 PS 加速器 `supportive modules\VIA_PS_Accel_Module.ps1`(找不到不影響)· 之後每個 python 指令都先接正本加速器 VeritasCeleritas |
| ③ | 取得 v0124:本機那份不是 v0124 → `git fetch` 分支 `claude/optimistic-goodall-yhalc5` + `git archive` 讀發行夾(不切換分支)→ SHA-256 必須是 `1c90b731a914ae6a3775bbeadcfde62dd8f06f9cd7b696172c8b3a5087b46814` 才換 · 舊啟動器改名 `.bak` 備份(不刪) |
| ④ | 執行啟動器(①~⑩:落地 v0231→v0234 · 補裝 · 平行段 · vrn2 --run · ⑧ 完成判定 · ⑨ 上船 VRN-2 船包 · ⑩ 封存 · U/I 自動跳出) |
| ⑤ | 摘要(完成判定 · 輸出冊筆數 · 子欄 · 剔除冊 · Parquet · 上船狀態)與**獨立驗證**(另寫的驗證器 · 只讀)**同時跑** · 報告寫 `VIA_Reports\vrn2\verify_independent\` |

開關:檔頭 `$NoPush = $true` 只實測不上船 · `$Verify = $false` 不跑獨立驗證。

容器實測(PowerShell 7.4 · 測試樹 · 19 份 PDF):舊版 v0123 → 備份 + 換 v0124 → ⑧ 完成 紅 0 → 獨立驗證錯值 0(約 2 分 20 秒)· 再跑(已是 v0124)約 1 分 20 秒 · 離線且本機是舊版 → ③ 紅燈停(不動啟動器)。Windows 專屬部分(CPU / RAM 量測、優先權)在容器量不到 → 照實顯示「量不到」。

程式碼 SHA-256(本文):`1dbb2e874349`

```powershell
& {
  # ===== VRN-2 v0124 一鍵全流程:① CPU / DRAM → ② PS 加速器 → ③ 取得 v0124(GitHub 分支 · SHA-256 驗證 · 舊版留備份)→ ④ 執行(啟動器 ①~⑩ · 完成後自動上船)→ ⑤ 摘要 ∥ 獨立驗證(同時跑 · 只讀)→ NEXT =====
  # 只增不減:不刪任何檔(舊啟動器改名備份)· 不動別的系統(VCGC / VDF)的檔 · 驗證只讀 · 報告寫在 VIA_Reports\vrn2\verify_independent
  $R      = if ($env:VRN2_ROOT)  { $env:VRN2_ROOT }  else { "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics" }   # VIA 根
  $A      = if ($env:VRN2_LAUNCHER) { $env:VRN2_LAUNCHER } else { Join-Path $env:USERPROFILE 'Downloads\ActivateVRN-2.py' }                   # 啟動器位置
  $Br     = 'claude/optimistic-goodall-yhalc5'                                    # v0124 發行所在的 GitHub 分支(只讀取 · 不切換分支)
  $RelP   = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0124'     # 發行夾(repo 根起算)
  $Want   = '1c90b731a914ae6a3775bbeadcfde62dd8f06f9cd7b696172c8b3a5087b46814'   # ActivateVRN-2 v0124 SHA-256
  $NoPush = $false        # $true = 只實測不上船
  $Verify = $true         # 跑完後獨立驗證(只讀)
  $LArgs  = @(); if ($env:VRN2_LAUNCHER_ARGS) { $LArgs = $env:VRN2_LAUNCHER_ARGS -split ' ' }   # 例:--no-install
  $ErrorActionPreference = 'Continue'
  try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
  $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
  $t0 = Get-Date; $tmp = Join-Path ([IO.Path]::GetTempPath()) ("vrn2_v0124_" + $t0.ToString('yyyyMMdd_HHmmss')); New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  function Say($lamp, $msg) { $c = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red'; GRAY = 'DarkGray' }[$lamp]; Write-Host ("[{0}] {1}" -f $lamp, $msg) -ForegroundColor $c }
  $me = Get-Process -Id $PID; $prio0 = $me.PriorityClass
  try {
    # ① 第一步:CPU / DRAM(CPU 閒 <60% → 本視窗升「高於標準」· 子行程繼承 · 結束還原)+ 釋放記憶體
    $cpu = $null; $ram = $null
    try { $cpu = [int](Get-CimInstance Win32_Processor -ErrorAction Stop | Measure-Object LoadPercentage -Average).Average } catch { }
    try { $ram = [math]::Round((Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).FreePhysicalMemory / 1MB, 1) } catch { }
    if ($cpu -ne $null -and $cpu -lt 60) { try { $me.PriorityClass = 'AboveNormal' } catch { } }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    Say GREEN ("① CPU / DRAM · CPU {0} · 可用 RAM {1} · 優先權 {2} → {3}" -f $(if ($cpu -ne $null) { "$cpu%" } else { '量不到' }), $(if ($ram -ne $null) { "$ram GB" } else { '量不到' }), $prio0, (Get-Process -Id $PID).PriorityClass)
    # ② PS 加速器(找不到不影響)
    $m = [IO.Path]::Combine($R, 'supportive modules', 'VIA_PS_Accel_Module.ps1')
    if (Test-Path -LiteralPath $m) { . $m; Say GREEN "② PS 加速器已接 · $m" } else { Say GRAY "② 找不到 VIA_PS_Accel_Module.ps1(不影響)" }
    if (-not (Test-Path -LiteralPath $R)) { Say RED "找不到 VIA 根 $R"; return }
    $py = if ($env:VRN2_PY) { $env:VRN2_PY } else { (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source }
    if (-not $py) { Say RED "找不到 python(不要用 WindowsApps 的假 python)"; return }
    # 每個 python 指令都先接正本加速器(VeritasCeleritas 最新版號 · 找不到 = 不改行為)
    $wrap = Join-Path $tmp 'vrn2_accel_run.py'
    [IO.File]::WriteAllText($wrap, @'
# [VIA:ACCEL-BRIDGE:v0111] 先接正本加速器(找不到 = 不改行為)再執行目標 .py
import re, runpy, sys
from pathlib import Path
root, target = Path(sys.argv[1]), sys.argv[2]
sys.argv = [target] + sys.argv[3:]
sup = root / "supportive modules"
c = sorted(list(sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")), key=lambda x: int(re.search(r"_v(\d{4})", x.name).group(1)))
try:
    if c:
        sys.path.insert(0, str(c[-1].parent))
        __import__(c[-1].stem)
except Exception:  # noqa: BLE001
    pass
sys.path.insert(0, str(Path(target).resolve().parent))
runpy.run_path(target, run_name="__main__")
'@, (New-Object Text.UTF8Encoding $false))
    function Q($s) { '"' + $s + '"' }
    # ③ 取得 v0124:先看本機那份 · 不是 → 從 GitHub 分支讀發行夾(git fetch + git archive · 不切換分支)· 雜湊對才換 · 舊版改名備份
    $have = if (Test-Path -LiteralPath $A) { (Get-FileHash -LiteralPath $A -Algorithm SHA256).Hash.ToLower() } else { '' }
    $rel = $null
    $top = $null; if (Get-Command git -ErrorAction SilentlyContinue) { $top = (git -C $R rev-parse --show-toplevel 2>$null) }; if ($top) { $top = "$top".Trim() }
    if ($top) {
      $ok = $false
      foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $Br 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }
      if ($ok) {
        $z = Join-Path $tmp 'vrn2_release_v0124.zip'
        git -C $top archive --format=zip -o $z "origin/${Br}:$RelP" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $rel = Join-Path $tmp 'rel'; Expand-Archive -LiteralPath $z -DestinationPath $rel -Force }
      }
    }
    if ($have -ne $Want) {
      if (-not $rel) { Say RED "③ 本機啟動器不是 v0124,且讀不到 GitHub 分支 $Br(網路 / git)· 請手動下載 ActivateVRN-2.py v0124 到 $A"; return }
      Expand-Archive -LiteralPath (Join-Path $rel 'ActivateVRN-2_v0124.zip') -DestinationPath (Join-Path $tmp 'l') -Force
      $new = [IO.Path]::Combine($tmp, 'l', 'ActivateVRN-2.py')
      $man = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $rel 'VRN2_Release_v0124.json') | ConvertFrom-Json
      $got = (Get-FileHash -LiteralPath $new -Algorithm SHA256).Hash.ToLower()
      if ($got -ne $Want -or $man.launcher.sha256 -ne $Want) { Say RED "③ 下載的啟動器雜湊不對($got)· 不使用"; return }
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $A) | Out-Null
      if (Test-Path -LiteralPath $A) {
        $ov = Select-String -LiteralPath $A -Pattern 'VERSION = "ActivateVRN-2 v(\d{4})"' -List
        $bak = Join-Path (Split-Path -Parent $A) ("ActivateVRN-2_v{0}_{1}.py.bak" -f $(if ($ov) { $ov.Matches[0].Groups[1].Value } else { 'old' }), $t0.ToString('yyyyMMdd_HHmmss'))
        Copy-Item -LiteralPath $A -Destination $bak; Say GREEN "③ 舊啟動器已備份 → $bak"
      }
      Copy-Item -LiteralPath $new -Destination $A -Force
      Say GREEN "③ 啟動器 v0124 就位(SHA-256 $($Want.Substring(0,12)) · 來源 GitHub $Br)→ $A"
    } else { Say GREEN "③ 本機已是 v0124(SHA-256 $($Want.Substring(0,12)))" }
    # ④ 執行(啟動器自己做 ①~⑩:CPU/DRAM · 定位 · 船包補回 · 落地 v0231→v0234 · 補裝 · 加速器 · 平行段 · 登記 · 測試 · vrn2 --run · 完成判定 · 上船 · 封存 · U/I)
    if ($NoPush) { $env:VIA_VRN2_NO_PUSH = '1' } else { Remove-Item Env:\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue }
    Write-Host ("[計] VRN-2 · ActivateVRN-2 v0124 · {0}" -f $(if ($NoPush) { '只實測不上船' } else { '完成後自動上船(VRN-2 船包)' })) -ForegroundColor Yellow
    & $py $A @LArgs
    $rcL = $LASTEXITCODE
    # ⑤ 摘要 ∥ 獨立驗證(兩件互不相連 · 都只讀 → 同時跑)
    $v2 = [IO.Path]::Combine($R, 'VIA_Reports', 'vrn2'); $od = Join-Path $v2 'output'
    $vp = $null; $vd = Join-Path $v2 'verify_independent'
    if ($Verify -and $rel -and (Test-Path -LiteralPath (Join-Path $od 'VRN2_FinancialData_latest.json'))) {
      Expand-Archive -LiteralPath (Join-Path $rel 'vrn2_test_tools_v0124.zip') -DestinationPath (Join-Path $tmp 'tt') -Force
      New-Item -ItemType Directory -Force -Path $vd | Out-Null
      $vr = Join-Path $vd ("VRN2_IndependentVerify_{0}.json" -f $t0.ToString('yyyyMMdd_HHmmss'))
      $vlog = $vr -replace '\.json$', '.txt'
      $vp = Start-Process -FilePath $py -ArgumentList @((Q $wrap), (Q $R), (Q ([IO.Path]::Combine($tmp, 'tt', 'tools', 'verify_outputs.py'))), (Q $od), (Q (Join-Path $v2 'scope_in')), (Q $vr)) -NoNewWindow -PassThru -RedirectStandardOutput $vlog -RedirectStandardError ($vlog + '.err')
    }
    $sum = Join-Path $tmp 'vrn2_sum.py'
    [IO.File]::WriteAllText($sum, @'
import json, sys, datetime
from collections import Counter
from pathlib import Path
v2, t0 = Path(sys.argv[1]), datetime.datetime.fromisoformat(sys.argv[2])
def j(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
c = j(v2 / "VRN2_Completion_latest.json") or {}
fresh = bool(c.get("ts")) and datetime.datetime.fromisoformat(c["ts"]) >= t0 - datetime.timedelta(seconds=5)
lamp = "GREEN" if fresh and c.get("verdict") == "完成" and not c.get("red") else "RED"
print("%s|⑧ 完成判定 · %s · 紅 %s · 黃 %s · %s · %s" % (lamp, c.get("verdict", "?"), c.get("red", "?"), c.get("yellow", "?"), c.get("manager", "?"), "本輪" if fresh else "不是本輪寫的(⑦ 沒跑完)"))
for it in c.get("items") or []:
    if it.get("lamp") in ("RED", "YELLOW"):
        print("%s|   %s · %s" % (it["lamp"], it["name"][:24], it["detail"][:150]))
od = v2 / "output"
b, f, s, r = (j(od / ("VRN2_%s_latest.json" % n)) or [] for n in ("BasicInfo", "FinancialData", "Summary", "Rejected"))
sub = [x for x in f if x.get("SUBCOL")]
rc = Counter(str(x.get("REASON", "")).split("(")[0][:10] for x in r)
pq = sorted(p.name for p in od.glob("VRN2_*_latest.parquet"))
st = list((od / "_stale").glob("*.parquet")) if (od / "_stale").is_dir() else []
print("GREEN|輸出冊 · 基本資料 %d · 年度數據 %d 筆(子欄 %d · 依子表頭更正 %d)· 一標題四重點 %d · 剔除冊 %d(%s)" % (len(b), len(f), len(sub), sum("更正" in (x.get("VERIFY") or "") for x in sub), len(s), len(r), " · ".join("%s %d" % kv for kv in rc.most_common(4))))
print("%s|Parquet %d / 4%s" % ("GREEN" if len(pq) == 4 else "YELLOW", len(pq), (" · 舊檔移到 output\\_stale %d 個(本輪沒寫 Parquet · 缺 pandas / pyarrow)" % len(st)) if st else ""))
print("GREEN|U/I %s" % (v2 / "VRN2_UI_latest.html"))
'@, (New-Object Text.UTF8Encoding $false))
    $sumOut = & $py $wrap $R $sum $v2 $t0.ToString('yyyy-MM-ddTHH:mm:ss') 2>&1
    foreach ($ln in $sumOut) { $p = "$ln" -split '\|', 2; if ($p.Count -eq 2) { Say $p[0] $p[1] } else { Write-Host $ln } }
    # 上船狀態(VRN-2 自己的位置 docs\handoff\ai\vrn2_ship)
    if ($top) {
      $last = git -C $R log -1 --format='%h %cd %s' --date=format:'%m-%d %H:%M' -- docs/handoff/ai/vrn2_ship 2>$null
      $ahead = git -C $R rev-list --count '@{u}..HEAD' 2>$null
      $pushed = if ("$ahead" -eq '0') { '已推到 GitHub' } elseif ("$ahead" -match '^\d+$') { "還有 $ahead 個提交沒推上去" } else { '沒有上游分支(看不出是否已推)' }
      if ($NoPush) { Say GRAY "⑨ 這次不上船" } elseif ($last) { Say $(if ("$ahead" -eq '0') { 'GREEN' } else { 'YELLOW' }) ("⑨ 船包最近提交 {0} · {1}" -f $last, $pushed) } else { Say YELLOW "⑨ 還沒有 VRN-2 船包提交(⑧ 沒完成就不上船)" }
    }
    if ($vp) {
      if (-not $vp.WaitForExit(1800000)) { try { $vp.Kill() } catch { }; Say YELLOW "獨立驗證超過 30 分鐘 · 已停(不影響輸出)" }
      else {
        $vt = if (Test-Path -LiteralPath $vlog) { Get-Content -Encoding UTF8 -LiteralPath $vlog } else { @() }
        $ve = if (Test-Path -LiteralPath ($vlog + '.err')) { Get-Content -Encoding UTF8 -LiteralPath ($vlog + '.err') | Where-Object { $_ -notmatch 'FontBBox' } } else { @() }
        if (($ve -join ' ') -match 'ModuleNotFoundError') { Say GRAY "獨立驗證跳過 · 缺 pdfplumber / pypdfium2(不補裝)" }
        else {
          foreach ($ln in ($vt | Where-Object { $_ -match '^\[驗證\]' })) { Say $(if ($vp.ExitCode -eq 0) { 'GREEN' } else { 'YELLOW' }) "獨立驗證 $ln" }
          foreach ($ln in ($vt | Where-Object { $_ -match '^\s+\[FAIL\]' } | Select-Object -First 8)) { Say YELLOW $ln.Trim() }
          Say $(if ($vp.ExitCode -eq 0) { 'GREEN' } else { 'YELLOW' }) ("獨立驗證 {0} · 報告 {1}{2}" -f $(if ($vp.ExitCode -eq 0) { '錯值 0' } else { '有 FAIL → 先看原文再判(驗證器也要被驗)' }), $vr, $(if ($vp.ExitCode -ne 0) { " · 明細 $vlog" } else { '' }))
        }
      }
    } elseif ($Verify) { Say GRAY "獨立驗證跳過 · 讀不到 GitHub 發行夾的驗證工具或沒有輸出冊" }
    $d = [int]((Get-Date) - $t0).TotalSeconds
    Write-Host ("NEXT: {0} · 交接報告 {1} · 啟動器 rc {2} · {3} 秒" -f $(if ($rcL -eq 0) { 'VRN-2 v0124 跑完 · 把上面 [RED]/[YELLOW] 行與貼包結尾 NEXT 貼回' } else { 'VRN-2 有紅燈 · 把貼包(≤300 行 · 結尾 NEXT)貼回' }), ([IO.Path]::Combine($R, 'docs', 'handoff', 'ai', 'VRN2_Handover_latest.md')), $rcL, $d) -ForegroundColor Cyan
  } finally {
    try { (Get-Process -Id $PID).PriorityClass = $prio0 } catch { }
  }
}
```

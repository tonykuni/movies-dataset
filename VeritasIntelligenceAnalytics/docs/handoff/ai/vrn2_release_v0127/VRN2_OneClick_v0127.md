# VRN-2 v0127 一鍵 PowerShell(整合全流程 · U/I 顯示驗證過的輸出)

貼進 PowerShell(Windows PowerShell 5.1 或 PowerShell 7)直接執行;或存成 `Run-VRN2-v0127.ps1`(UTF-8 含 BOM)後 `powershell -ExecutionPolicy Bypass -File Run-VRN2-v0127.ps1`。

| 步驟 | 做什麼 |
|---|---|
| ① | 第一步提高 CPU / DRAM:CPU 閒(<60%)時本視窗升「高於標準」(子行程繼承 · 結束還原)· 釋放記憶體 |
| ② | 接 PS 加速器 `supportive modules\VIA_PS_Accel_Module.ps1`(找不到不影響)· 之後每個 python 指令都先接正本加速器 VeritasCeleritas |
| ③ | 取得 v0127:本機那份不是 v0127 → `git fetch` 分支 `claude/optimistic-goodall-yhalc5` + `git archive` 讀發行夾(不切換分支)→ SHA-256 必須是 `333e906e78e7852a30413b913044493b9d2d0c3bbc7dd0f1082edd17c5518552` 且與發行清單相同才換 · 舊啟動器改名備份 |
| ④ | 執行啟動器 ①~⑪:落地 v0231 → **v0237** + **獨立驗證器 v0100** · ⑦ 擷取 → **⑪ 背景獨立驗證開始**(與 ⑧⑨⑩ 同時跑 · 只讀)· ⑧ 完成判定 · ⑨ **只送 VRN-2 船包**(疊在遠端最新提交上 fast-forward · 本機別的提交不代推)· ⑩ 封存 · ⑪ 驗證判決寫回 U/I → **開 U/I(第一個分頁「驗證過的輸出」)** |
| ⑤ | 摘要(完成判定 · 輸出冊 · 剔除冊 · Parquet · **U/I 驗證判決是否已寫回且冊指紋相同** · GitHub 上的船包是否與本機相同)· 印啟動器 ⑪ 的驗證結果與**驗證摘要**(≤40 行)· 啟動器沒驗到時 PS 用落地的驗證器自己驗 |

開關:檔頭 `$NoPush = $true` 只實測不上船 · `$Verify = $false` 啟動器沒驗到時 PS 也不補驗 · `$env:VIA_VRN2_NO_VERIFY = '1'` 啟動器不跑 ⑪ · `$env:VRN2_VERIFY_PAR = '2'` 驗證平行路數 · `$env:VIA_VRN2_VERIFY_WAIT = '3600'` ⑪ 等待上限(秒)。

U/I 怎麼看:左上分頁「驗證過的輸出」→ 狀態列寫「冊指紋 … 與本頁相同」= 判決就是這一頁的值 → 總表點一份 → 基本資料 / 一標題四重點 / 年度數據格子 · **✓✓ 綠 = VRN-2 兩個讀取器 + 獨立驗證都對位** · ◐ 黃 = 值在原文、欄位人工核對 · ✗ 紅 = 獨立驗證不過(滑鼠停在格子上看理由與原文頁)· 「只看待核對」只留非 ✓✓ · 「⤓ 下載本檔 CSV」帶每筆判決。

容器實測(PowerShell 7.4 · 情境 = 使用者機器:先跑過 v0126 · 遠端被別台推了新提交 · 本機有別的系統的提交):見 `VRN2_Verification_v0127.md`。

程式碼 SHA-256(本文):`ea6e15796389`

```powershell
& {
  # ===== VRN-2 v0127 一鍵全流程(U/I「驗證過的輸出」· 啟動器 ⑪ 背景獨立驗證寫回 U/I · 一格整列拆開 · 重複列只留一筆 · 驗證器 v0100):① CPU / DRAM → ② PS 加速器 → ③ 取得 v0127(GitHub 分支 · SHA-256 驗證 · 舊版留備份)→ ④ 執行(啟動器 ①~⑪ · 完成後自動上船 · 驗證寫回後開 U/I)→ ⑤ 摘要 · 印驗證摘要(啟動器沒驗到才自己驗)→ NEXT =====
  # 只增不減:不刪任何檔(舊啟動器改名備份)· 不動別的系統(VCGC / VDF)的檔 · 驗證只讀 · 報告寫在 VIA_Reports\vrn2\verify_independent
  $R      = if ($env:VRN2_ROOT)  { $env:VRN2_ROOT }  else { "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics" }   # VIA 根
  $A      = if ($env:VRN2_LAUNCHER) { $env:VRN2_LAUNCHER } else { Join-Path $env:USERPROFILE 'Downloads\ActivateVRN-2.py' }                   # 啟動器位置
  $Br     = 'claude/optimistic-goodall-yhalc5'                                    # v0127 發行所在的 GitHub 分支(只讀取 · 不切換分支)
  $RelP   = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0127'     # 發行夾(repo 根起算)
  $Want   = '333e906e78e7852a30413b913044493b9d2d0c3bbc7dd0f1082edd17c5518552'   # ActivateVRN-2 v0127 SHA-256
  $NoPush = $false        # $true = 只實測不上船
  $Verify = $true         # 啟動器 ⑪ 沒驗到(例:舊版 / 中斷)時 PS 自己用落地的驗證器驗(只讀)
  $LArgs  = @(); if ($env:VRN2_LAUNCHER_ARGS) { $LArgs = $env:VRN2_LAUNCHER_ARGS -split ' ' }   # 例:--no-install
  $ErrorActionPreference = 'Continue'
  try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
  $env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
  $t0 = Get-Date; $tmp = Join-Path ([IO.Path]::GetTempPath()) ("vrn2_v0127_" + $t0.ToString('yyyyMMdd_HHmmss')); New-Item -ItemType Directory -Force -Path $tmp | Out-Null
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
    # ③ 取得 v0127:先看本機那份 · 不是 → 從 GitHub 分支讀發行夾(git fetch + git archive · 不切換分支)· 雜湊對才換 · 舊版改名備份
    $have = if (Test-Path -LiteralPath $A) { (Get-FileHash -LiteralPath $A -Algorithm SHA256).Hash.ToLower() } else { '' }
    $rel = $null
    $top = $null; if (Get-Command git -ErrorAction SilentlyContinue) { $top = (git -C $R rev-parse --show-toplevel 2>$null) }; if ($top) { $top = "$top".Trim() }
    if ($top) {
      $ok = $false
      foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $Br 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }
      if ($ok) {
        $z = Join-Path $tmp 'vrn2_release_v0127.zip'
        git -C $top archive --format=zip -o $z "origin/${Br}:$RelP" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $rel = Join-Path $tmp 'rel'; Expand-Archive -LiteralPath $z -DestinationPath $rel -Force }
      }
    }
    if ($have -ne $Want) {
      if (-not $rel) { Say RED "③ 本機啟動器不是 v0127,且讀不到 GitHub 分支 $Br(網路 / git)· 請手動下載 ActivateVRN-2.py v0127 到 $A"; return }
      Expand-Archive -LiteralPath (Join-Path $rel 'ActivateVRN-2_v0127.zip') -DestinationPath (Join-Path $tmp 'l') -Force
      $new = [IO.Path]::Combine($tmp, 'l', 'ActivateVRN-2.py')
      $man = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $rel 'VRN2_Release_v0127.json') | ConvertFrom-Json
      $got = (Get-FileHash -LiteralPath $new -Algorithm SHA256).Hash.ToLower()
      if ($got -ne $Want -or $man.launcher.sha256 -ne $Want) { Say RED "③ 下載的啟動器雜湊不對($got)· 不使用"; return }
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $A) | Out-Null
      if (Test-Path -LiteralPath $A) {
        $ov = Select-String -LiteralPath $A -Pattern 'VERSION = "ActivateVRN-2 v(\d{4})"' -List
        $bak = Join-Path (Split-Path -Parent $A) ("ActivateVRN-2_v{0}_{1}.py.bak" -f $(if ($ov) { $ov.Matches[0].Groups[1].Value } else { 'old' }), $t0.ToString('yyyyMMdd_HHmmss'))
        Copy-Item -LiteralPath $A -Destination $bak; Say GREEN "③ 舊啟動器已備份 → $bak"
      }
      Copy-Item -LiteralPath $new -Destination $A -Force
      Say GREEN "③ 啟動器 v0127 就位(SHA-256 $($Want.Substring(0,12)) · 來源 GitHub $Br)→ $A"
    } else { Say GREEN "③ 本機已是 v0127(SHA-256 $($Want.Substring(0,12)))" }
    # ④ 執行(啟動器自己做 ①~⑪:CPU/DRAM · 定位 · 船包補回 · 落地 v0231→v0237 + 獨立驗證器 · 補裝 · 加速器 · 平行段 · 登記 · 測試 · vrn2 --run · ⑪ 背景驗證 ∥ 完成判定 · 上船 · 封存 · 驗證寫回 U/I → 開 U/I)
    if ($NoPush) { $env:VIA_VRN2_NO_PUSH = '1' } else { Remove-Item Env:\VIA_VRN2_NO_PUSH -ErrorAction SilentlyContinue }
    Write-Host ("[計] VRN-2 · ActivateVRN-2 v0127 · {0}" -f $(if ($NoPush) { '只實測不上船' } else { '完成後自動上船(VRN-2 船包)' })) -ForegroundColor Yellow
    & $py $A @LArgs
    $rcL = $LASTEXITCODE
    # ⑤ 摘要 · 獨立驗證:啟動器 ⑪ 本輪已驗(報告時間 ≥ 開始)→ 直接用;沒有 → PS 用落地的驗證器自己驗(與摘要同時跑 · 只讀 · 判決也寫回 U/I)
    $v2 = [IO.Path]::Combine($R, 'VIA_Reports', 'vrn2'); $od = Join-Path $v2 'output'
    $vp = $null; $vd = Join-Path $v2 'verify_independent'; $vr = $null; $vlog = $null
    $lv = if (Test-Path -LiteralPath $vd) { Get-ChildItem -LiteralPath $vd -Filter 'VRN2_IndependentVerify_*.json' | Where-Object { $_.LastWriteTime -ge $t0.AddSeconds(-5) } | Sort-Object LastWriteTime | Select-Object -Last 1 } else { $null }
    if ($lv) { $vr = $lv.FullName; $vlog = $vr -replace '\.json$', '.txt' }
    elseif ($Verify -and (Test-Path -LiteralPath (Join-Path $od 'VRN2_FinancialData_latest.json'))) {
      $ver = Get-ChildItem -LiteralPath ([IO.Path]::Combine($R, 'functional modules', 'VRN')) -Filter 'VRN2_IndependentVerifier_v*.py' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
      if ($ver) {
        New-Item -ItemType Directory -Force -Path $vd | Out-Null
        $vr = Join-Path $vd ("VRN2_IndependentVerify_{0}.json" -f $t0.ToString('yyyyMMdd_HHmmss'))
        $vlog = $vr -replace '\.json$', '.txt'
        $vp = Start-Process -FilePath $py -ArgumentList @((Q $wrap), (Q $R), (Q $ver.FullName), (Q $od), (Q (Join-Path $v2 'scope_in')), (Q $vr), '--ui', (Q (Join-Path $v2 'VRN2_UI_latest.html'))) -NoNewWindow -PassThru -RedirectStandardOutput $vlog -RedirectStandardError ($vlog + '.err')
        Say GRAY "啟動器本輪沒有驗證報告 → PS 用 $($ver.Name) 自己驗(只讀 · 判決寫回 U/I)"
      }
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
import hashlib, re as _re
up = v2 / "VRN2_UI_latest.html"
pg = up.read_text(encoding="utf-8") if up.exists() else ""
h = hashlib.sha256()
for x in f:
    h.update(("\x1f".join(str(x.get(k, "")) for k in ("FILENAME", "PAGE", "TABLE", "ITEM", "PERIOD", "SUBCOL", "VALUE")) + "\x1e").encode("utf-8"))
m = _re.search(r'window\.VRN2_IV=\{"ver":"[^"]*","ts":"([^"]*)","fp":"([0-9a-f]{16})"', pg)
tab = "id='vrn2vo-h'" in pg
if not tab:
    print("YELLOW|U/I %s · 沒有「驗證過的輸出」分頁(管理器不是 v0237 以後)" % up)
elif m and m.group(2) == h.hexdigest()[:16]:
    print("GREEN|U/I %s · 「驗證過的輸出」分頁 · 獨立驗證判決已寫回(%s · 冊指紋 %s 相同)" % (up, m.group(1), m.group(2)))
else:
    print("YELLOW|U/I %s · 「驗證過的輸出」分頁 · 獨立驗證%s" % (up, "結果是別一輪的(指紋不同)" if m else "尚未寫回"))
'@, (New-Object Text.UTF8Encoding $false))
    $sumOut = & $py $wrap $R $sum $v2 $t0.ToString('yyyy-MM-ddTHH:mm:ss') 2>&1
    foreach ($ln in $sumOut) { $p = "$ln" -split '\|', 2; if ($p.Count -eq 2) { Say $p[0] $p[1] } else { Write-Host $ln } }
    # 上船狀態:GitHub 上的 VRN-2 船包是否和本機相同(v0125 起只送 VRN-2 船包 · 本機別的提交不代推)
    if ($top) {
      $u = git -C $R rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
      if ($NoPush) { Say GRAY "⑨ 這次不上船" }
      elseif (-not $u) { Say YELLOW "⑨ 目前分支沒有上游(看不出 GitHub 上的船包)" }
      else {
        $ub = "$u" -split '/', 2; git -C $R fetch -q $ub[0] $ub[1] 2>&1 | Out-Null
        git -C $R diff --quiet $u HEAD -- docs/handoff/ai/vrn2_ship docs/handoff/ai/VRN2_Handover_latest.md 2>$null
        $same = ($LASTEXITCODE -eq 0)
        $ahead = git -C $R rev-list --count "$u..HEAD" -- . ':(exclude)docs/handoff/ai/vrn2_ship' ':(exclude)docs/handoff/ai/VRN2_Handover_latest.md' ':(exclude)docs/handoff/ai/VRN2_Handover_v0127.md' 2>$null
        Say $(if ($same) { 'GREEN' } else { 'YELLOW' }) ("⑨ GitHub {0} 上的 VRN-2 船包 {1}" -f $u, $(if ($same) { '與本機相同(已上船)' } else { '與本機不同(沒推上去 · 看上面 ⑨ 那行的原因)' }))
        if ("$ahead" -match '^\d+$' -and [int]$ahead -gt 0) { Say GRAY ("本機另有 {0} 個動到別的檔的提交沒推到 {1}(不是 VRN-2 的 · VRN-2 不代推)" -f $ahead, $u) }
      }
    }
    $vok = $null
    if ($vp) {
      if (-not $vp.WaitForExit(1800000)) { try { $vp.Kill() } catch { }; Say YELLOW "獨立驗證超過 30 分鐘 · 已停(不影響輸出)"; $vr = $null }
      else { $vok = ($vp.ExitCode -eq 0) }
    } elseif ($vr) { $vok = -not ((Get-Content -Encoding UTF8 -LiteralPath $vlog -ErrorAction SilentlyContinue) -match '^\[驗證\] 年度數據 .*(FAIL|MISALIGNED|BADVALUE|BADITEM|SUBFAIL|TRANSFAIL|DUPKEY|QTRCOL|DUPROW)') }
    if ($vr -and (Test-Path -LiteralPath $vlog)) {
      $vt = Get-Content -Encoding UTF8 -LiteralPath $vlog
      $ve = if (Test-Path -LiteralPath ($vlog + '.err')) { Get-Content -Encoding UTF8 -LiteralPath ($vlog + '.err') | Where-Object { $_ -notmatch 'FontBBox' } } else { @() }
      if (($ve -join ' ') -match 'ModuleNotFoundError') { Say GRAY "獨立驗證跳過 · 缺 pdfplumber / pypdfium2(不補裝)" }
      else {
        foreach ($ln in ($vt | Where-Object { $_ -match '^\[驗證\]' })) { Say $(if ($vok) { 'GREEN' } else { 'YELLOW' }) "獨立驗證 $ln" }
        foreach ($ln in ($vt | Where-Object { $_ -match '^\s+\[FAIL\]' } | Select-Object -First 8)) { Say YELLOW $ln.Trim() }
        Say $(if ($vok) { 'GREEN' } else { 'YELLOW' }) ("獨立驗證({0}){1} · 報告 {2}" -f $(if ($lv) { '啟動器 ⑪' } else { 'PS 自己驗' }), $(if ($vok) { ' 錯值 0' } else { ' 有待核對 → U/I「驗證過的輸出」看 ✗ 格(先看原文再判 · 驗證器也要被驗)' }), $vr)
        $dg = "$vr.digest.txt"
        if (Test-Path -LiteralPath $dg) {
          Write-Host "──── 驗證摘要(貼給 AI 只要這份 · 完整在 $dg)────" -ForegroundColor Cyan
          Get-Content -Encoding UTF8 -LiteralPath $dg | Select-Object -First 40 | ForEach-Object { Write-Host $_ }
        }
      }
    } elseif ($Verify) { Say GRAY "獨立驗證跳過 · 啟動器沒驗、也找不到落地的驗證器或輸出冊" }
    $d = [int]((Get-Date) - $t0).TotalSeconds
    Write-Host ("NEXT: {0} · 交接報告 {1} · 啟動器 rc {2} · {3} 秒" -f $(if ($rcL -eq 0) { 'VRN-2 v0127 跑完 · U/I 已開在「驗證過的輸出」· 把上面 [RED]/[YELLOW] 行 + ⑨ / ⑪ 兩行 + 驗證摘要貼回' } else { 'VRN-2 有紅燈 · 把貼包(≤300 行 · 結尾 NEXT)貼回' }), ([IO.Path]::Combine($R, 'docs', 'handoff', 'ai', 'VRN2_Handover_latest.md')), $rcL, $d) -ForegroundColor Cyan
  } finally {
    try { (Get-Process -Id $PID).PriorityClass = $prio0 } catch { }
  }
}
```

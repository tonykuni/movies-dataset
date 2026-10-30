# VRN-2 一支 Python · VRN2_RoundAll_v0112.py(套件 v0156 · 共識經 VIA 網路工具 + 加速器出網)

`VRN2_RoundAll_v0112.py`(只用 Python 標準庫 · SHA-256 `5f032bc73f2f`)= v0111 + 套件 `vrn2_release_v0156/VRN2_Closeout_v0156.zip`(SHA-256 `182bc1486bb4`,本檔內已釘死):

| 改了什麼 | 說明 |
|---|---|
| 套件 v0156 | 啟動器 v0156 · runtime v0156 = v0154 的 190 個成員不動 + 共識引擎 v0122(經 `SUP_MDL740_NetUnified` 最高版號 + 加速器橋)+ ConsensusJoin v0104 |
| ⑤ 自動修 `consensus_refresh` | 共識收據不是經網路工具的引擎抓的 + 同意閘開(操作員設的 `VIA_NET_CONSENT=YES` · `VIA_SCRAPE_CONSENT=YES` / `I_ACCEPT_RESPONSIBLE_SCRAPING`)→ 補放 ConsensusJoin 鏈 + 引擎 → `VIA_VRN2_CONSENSUS_REFRESH=1` 重跑 ⑥f → 重組 Combined;閘關 → 不重抓 |
| 收尾頁負責方 | ⑥f 收據有 `net_deny`:同意閘未開 → **人工**(操作員決定 · 不代設)· 合規 DENY → **VCGC**;Combined 的「VIA 網路工具 DENY」空格同樣分;MOPS 規則不再吃掉 ⑥f / Combined 的 DENY 列 |
| 除錯報告 | 「⑥f 經 VIA 網路工具」(綠 · 網路工具版號 · 閘 · 加速器)/「⑥f VIA 網路工具 DENY」/「⑥f 共識還沒經 VIA 網路工具」(閘關 · 人工) |

自測 55 項(v0111 的 51 項 + 52 ~ 55)。**最省事:`VRN2_HandleAll_v0104.md` 最上面那一行**。前版 v0111 的說明見 `vrn2_release_v0155/VRN2_RoundAll_v0111.md`。

## 在 PowerShell 7 視窗直接貼(約 2,300 字元)

```powershell
& { $ErrorActionPreference = 'Continue'; $ProgressPreference = 'SilentlyContinue'; if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這一行要 PowerShell 7 以上(pwsh)' -ForegroundColor Red; return }; $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0156'; $F = 'VRN2_RoundAll_v0112.py'; $H = '5f032bc73f2f8bc7608754107dcd4dcede05be4a349f38599a12d0e5bfe18fff'; $top = git -C $R rev-parse --show-toplevel 2>$null; if (-not $top) { Write-Host "[RED] $R 不是 git 倉或找不到 git(先設 `$env:VRN2_ROOT)" -ForegroundColor Red; return }; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_roundall_$(Get-Date -Format yyyyMMdd_HHmmss)"; New-Item -ItemType Directory -Force -Path $t | Out-Null; $z = Join-Path $t 'roundall.zip'; $src = $null; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/${b}:$P" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }; if (-not $src) { Write-Host "[RED] 讀不到 GitHub 分支或 main 的 $F(網路 / git)" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $bytes = [Text.UTF8Encoding]::new($false).GetBytes($code); $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant(); if ($sha -ne $H) { Write-Host "[RED] $F SHA-256 不對($sha)· 不執行" -ForegroundColor Red; return }; $dst = Join-Path $env:USERPROFILE "Downloads\$F"; [IO.File]::WriteAllBytes($dst, $bytes); $py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source; if (-not $py) { Write-Host '[RED] 找不到 python(不要用 WindowsApps 的假 python)' -ForegroundColor Red; return }; Write-Host "[GREEN] $F SHA-256 $($H.Substring(0, 12)) 相符(GitHub $src)→ $dst · 用 $py 執行" -ForegroundColor Green; & $py $dst --root $R @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ }); Write-Host "[計] RoundAll 結束碼 $LASTEXITCODE(視窗不會關)" }
```

## 已經有這個檔時

```bat
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0112.py" --only package,fix,report,closeout,pasteback
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0112.py" --only report,closeout,pasteback
```

第 1 行 = 只修(同意閘開 → ⑥f 經網路工具重抓)+ 收尾頁 · 第 2 行 = 只重做報告 + 收尾頁。PowerShell 把 `%USERPROFILE%` 換成 `$env:USERPROFILE`。

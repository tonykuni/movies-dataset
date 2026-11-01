# VRN-2 一支 Python · VRN2_RoundAll_v0113.py(套件 v0157 · ③ 改經 VCGC 安裝)

`VRN2_RoundAll_v0113.py`(只用 Python 標準庫 · SHA-256 `891df58a576e`)= v0112 + 套件 `vrn2_release_v0157/VRN2_Closeout_v0157.zip`(SHA-256 `7ff4e9626abf`,本檔內已釘死):

| 改了什麼 | 說明 |
|---|---|
| 套件 v0157 | 啟動器 v0157(③ 只檢查 · 缺的一個一個交 VCGC 安裝閘 `CGC_MDL056_InstallGate` 最高版號 · 裝完再檢查 · 裝不起來 24 小時不重試)· runtime v0156 原樣 |
| ② 提示 | 必裝缺 → 「啟動器 v0157 ③ 只檢查 · 缺的經 VCGC 安裝閘裝 · 仍缺 → via-install」(不再印 pip 指令) |
| 除錯報告 | 「③ 環境檢查 · VCGC 安裝閘沒裝起來」:必裝 = 黃(收尾頁 VCGC)· 選裝 = 灰 |
| 貼回包 | 多帶 `VRN2_VCGCInstall_latest.json` 與 `VRN2_Env_latest.json` |

自測 57 項(v0112 的 55 項 + 56 · 57)。**最省事:`VRN2_HandleAll_v0105.md` 最上面那一行**。前版 v0112 的說明見 `vrn2_release_v0156/VRN2_RoundAll_v0112.md`。

## 在 PowerShell 7 視窗直接貼(約 2,300 字元)

```powershell
& { $ErrorActionPreference = 'Continue'; $ProgressPreference = 'SilentlyContinue'; if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這一行要 PowerShell 7 以上(pwsh)' -ForegroundColor Red; return }; $R = $env:VRN2_ROOT ?? 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0157'; $F = 'VRN2_RoundAll_v0113.py'; $H = '891df58a576e42260e856f053387ac1c5aa4fc772fe58d9d407b3de8aedd4df9'; $top = git -C $R rev-parse --show-toplevel 2>$null; if (-not $top) { Write-Host "[RED] $R 不是 git 倉或找不到 git(先設 `$env:VRN2_ROOT)" -ForegroundColor Red; return }; $t = Join-Path ([IO.Path]::GetTempPath()) "vrn2_roundall_$(Get-Date -Format yyyyMMdd_HHmmss)"; New-Item -ItemType Directory -Force -Path $t | Out-Null; $z = Join-Path $t 'roundall.zip'; $src = $null; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 2, 4, 8, 16) { if ($w) { Start-Sleep -Seconds $w }; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/${b}:$P" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $z)) { $src = $b; break } }; if (-not $src) { Write-Host "[RED] 讀不到 GitHub 分支或 main 的 $F(網路 / git)" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $code = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $bytes = [Text.UTF8Encoding]::new($false).GetBytes($code); $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant(); if ($sha -ne $H) { Write-Host "[RED] $F SHA-256 不對($sha)· 不執行" -ForegroundColor Red; return }; $dst = Join-Path $env:USERPROFILE "Downloads\$F"; [IO.File]::WriteAllBytes($dst, $bytes); $py = $env:VRN2_PY ?? (Get-Command python, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source; if (-not $py) { Write-Host '[RED] 找不到 python(不要用 WindowsApps 的假 python)' -ForegroundColor Red; return }; Write-Host "[GREEN] $F SHA-256 $($H.Substring(0, 12)) 相符(GitHub $src)→ $dst · 用 $py 執行" -ForegroundColor Green; & $py $dst --root $R @(($env:VRN2_ROUNDALL_ARGS ?? '') -split '\s+' | Where-Object { $_ }); Write-Host "[計] RoundAll 結束碼 $LASTEXITCODE(視窗不會關)" }
```

## 已經有這個檔時

```bat
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0113.py" --only package,fix,report,closeout,pasteback
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0113.py"
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0113.py" --launcher-args "--no-install"
```

第 1 行 = 只修 + 收尾頁 · 第 2 行 = 整輪(③ 缺的經 VCGC 安裝閘)· 第 3 行 = 整輪但 ③ 只檢查、不裝。PowerShell 把 `%USERPROFILE%` 換成 `$env:USERPROFILE`。

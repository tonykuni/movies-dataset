# VIA · SettleAll v0118 一支 PS 開機行(整合桌機全部收尾 · 雙橋 100% · 五系統憲法矩陣 · 外部工具)

操作員 2026-11-09:「integrate all into one ps code 遵守 ps/py 注入 ast 加速器覆蓋率 100% · 對外擷取資料的引擎 / VDF 注入網路工具 100% ·
VCGC 所有工具網路加速器遇到多個有差異:全景式檢是注入 AST 分類編號修正 標準化 合併 優化簡化 整合去重不遺漏最佳化處理」。

一行做的事:從 GitHub 取 `VIA_SettleAll_v0117.py` + `VIA_SettleAll_v0118.py`(先試分支 `claude/optimistic-goodall-yhalc5`,再 `main`)到暫存夾 → 核 v0118 的 SHA-256
`3781e00abb67b4cb3d15707134e7242c270c7d8d98b77ed9664af3d87dec691b` 才跑 → `python VIA_SettleAll_v0118.py --root <倉根> --apply-bridges`。

| 步 | 做什麼 | 寫到哪 |
|---|---|---|
| ⓪…⑰(v0117 原樣) | 全景 · 同步(合併分支 · 不 push)· VDF ui · VRN-2 狀態 · VCGC 串測 / 交接閘 · Graphify · VQG · Agent OS · VAP · 政策 · VDF 全引擎自測 · 模組矩陣 · 衝突偵測 · 系統矩陣 · 報告 | VIA_Reports/settle |
| ⑲ 雙橋覆蓋 | CGC_MDL124 BridgeSweeper 尾版:PY 加速器橋(四系 + 根層)· PS 加速器橋 · VDF 擷取引擎網路橋;`--apply-bridges` 真注入,否則只算覆蓋率 | 工作樹(注入時)· VIA_Reports/bridge_sweep |
| ㉑ 治理核心矩陣 | VIA_GovCoreChain 尾版 `run`(dry-run:它的 json / md / UI 是帶版號的已發布冊,就地重生會被編號稽核判 IMMUT;重生要出新版號):六家族副本 · 分岔 · 載入者 · 改動權 | 只讀 |
| ㉒ 編號稽核 | VCGC `run CGC_MDL237_NumberingSystem audit`:遺失 / 改身分 / 重號 都 0 才不紅 | 只讀 |
| ⑱ 五系統憲法矩陣 | VIA_FiveSystemConstitution 尾版 `run --apply`(L125):五系統各自 --selftest · 號 · 憲法性 · 進度帳只增 | docs/handoff/ai/VIA_FiveSystem* |
| ⑳ 外部工具 | Graphify 隔離環境 · Ponytail 外掛 · OmniRoute · Node:只偵測,缺的印安裝指令,不代裝 | 只讀 |

**注入後**:工作樹裡被注橋的檔 = 你桌機自己的改動;本檔不 commit、不 push。看 `git -C <倉> status`,要留就 commit 走 PR;不要就 `git checkout -- <檔>`。
**同意閘**:Graphify 第一次安裝要下載,請自己設 `$env:VIA_NET_CONSENT = 'YES'`;本檔與一行都不代設。
**不做**:發號(L125 ③)· 裁正本 · 安裝外部工具 · rebase / 強推。

## PowerShell 7 視窗(貼這一行)

```powershell
& { $r = $env:VIA_ROOT ?? (Join-Path $HOME 'OneDrive\Documents\movies-dataset'); if (-not (Test-Path (Join-Path $r '.git'))) { Write-Host "[RED] boot: $r 不是 git 倉(設 `$env:VIA_ROOT = 倉根)" -ForegroundColor Red; return }; $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai'; $t = Join-Path ([IO.Path]::GetTempPath()) "via_settle118_$(Get-Date -Format yyyyMMddHHmmss)"; New-Item -ItemType Directory -Force -Path $t | Out-Null; $ok = $false; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { git -C $r fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -ne 0) { continue }; git -C $r archive --format=zip -o "$t\s.zip" "origin/$($b):$($P)" VIA_SettleAll_v0117.py VIA_SettleAll_v0118.py 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }; if (-not $ok) { Write-Host '[RED] boot: GitHub 取不到 VIA_SettleAll v0117 / v0118' -ForegroundColor Red; return }; Expand-Archive -LiteralPath "$t\s.zip" -DestinationPath $t -Force; $c = [IO.File]::ReadAllText("$t\VIA_SettleAll_v0118.py", [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $s = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.UTF8Encoding]::new($false).GetBytes($c))) -replace '-', '').ToLowerInvariant(); if ($s -ne '3781e00abb67b4cb3d15707134e7242c270c7d8d98b77ed9664af3d87dec691b') { Write-Host "[RED] boot: SHA-256 $s 不是 3781e00abb67… - 不跑" -ForegroundColor Red; return }; Write-Host "[GREEN] boot: VIA_SettleAll v0118 SHA-256 OK ($b)" -ForegroundColor Green; python "$t\VIA_SettleAll_v0118.py" --root $r --apply-bridges @args }
```

後面可以接 v0117 的任何參數,例如只跑新五步:`… --no-sync --only scan,bridges,govcore,numaudit,fivesys,exttools,matrix,report`;不想真注入就在一行尾端加 `--only` 之外再加不了旗標 —— 改貼下面「不注入」版。

不注入(只算覆蓋率)版:把上面那行最後的 `--apply-bridges @args` 改成 `@args` 即可。

## cmd 視窗(cmd.exe 貼這一行;需要 PowerShell 7 = `pwsh`,沒有就 `winget install Microsoft.PowerShell`)

```bat
pwsh -NoProfile -ExecutionPolicy Bypass -EncodedCommand JgAgAHsAIAAkAHIAIAA9ACAAJABlAG4AdgA6AFYASQBBAF8AUgBPAE8AVAAgAD8APwAgACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAEgATwBNAEUAIAAnAE8AbgBlAEQAcgBpAHYAZQBcAEQAbwBjAHUAbQBlAG4AdABzAFwAbQBvAHYAaQBlAHMALQBkAGEAdABhAHMAZQB0ACcAKQA7ACAAaQBmACAAKAAtAG4AbwB0ACAAKABUAGUAcwB0AC0AUABhAHQAaAAgACgASgBvAGkAbgAtAFAAYQB0AGgAIAAkAHIAIAAnAC4AZwBpAHQAJwApACkAKQAgAHsAIABXAHIAaQB0AGUALQBIAG8AcwB0ACAAIgBbAFIARQBEAF0AIABiAG8AbwB0ADoAIAAkAHIAIAANTi9mIABnAGkAdAAgAAlQKAAtiiAAYAAkAGUAbgB2ADoAVgBJAEEAXwBSAE8ATwBUACAAPQAgAAlQOWgpACIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAHIAZQB0AHUAcgBuACAAfQA7ACAAJABQACAAPQAgACcAVgBlAHIAaQB0AGEAcwBJAG4AdABlAGwAbABpAGcAZQBuAGMAZQBBAG4AYQBsAHkAdABpAGMAcwAvAGQAbwBjAHMALwBoAGEAbgBkAG8AZgBmAC8AYQBpACcAOwAgACQAdAAgAD0AIABKAG8AaQBuAC0AUABhAHQAaAAgACgAWwBJAE8ALgBQAGEAdABoAF0AOgA6AEcAZQB0AFQAZQBtAHAAUABhAHQAaAAoACkAKQAgACIAdgBpAGEAXwBzAGUAdAB0AGwAZQAxADEAOABfACQAKABHAGUAdAAtAEQAYQB0AGUAIAAtAEYAbwByAG0AYQB0ACAAeQB5AHkAeQBNAE0AZABkAEgASABtAG0AcwBzACkAIgA7ACAATgBlAHcALQBJAHQAZQBtACAALQBJAHQAZQBtAFQAeQBwAGUAIABEAGkAcgBlAGMAdABvAHIAeQAgAC0ARgBvAHIAYwBlACAALQBQAGEAdABoACAAJAB0ACAAfAAgAE8AdQB0AC0ATgB1AGwAbAA7ACAAJABvAGsAIAA9ACAAJABmAGEAbABzAGUAOwAgAGYAbwByAGUAYQBjAGgAIAAoACQAYgAgAGkAbgAgACcAYwBsAGEAdQBkAGUALwBvAHAAdABpAG0AaQBzAHQAaQBjAC0AZwBvAG8AZABhAGwAbAAtAHkAaABhAGwAYwA1ACcALAAgACcAbQBhAGkAbgAnACkAIAB7ACAAZwBpAHQAIAAtAEMAIAAkAHIAIABmAGUAdABjAGgAIAAtAHEAIABvAHIAaQBnAGkAbgAgACQAYgAgADIAPgAmADEAIAB8ACAATwB1AHQALQBOAHUAbABsADsAIABpAGYAIAAoACQATABBAFMAVABFAFgASQBUAEMATwBEAEUAIAAtAG4AZQAgADAAKQAgAHsAIABjAG8AbgB0AGkAbgB1AGUAIAB9ADsAIABnAGkAdAAgAC0AQwAgACQAcgAgAGEAcgBjAGgAaQB2AGUAIAAtAC0AZgBvAHIAbQBhAHQAPQB6AGkAcAAgAC0AbwAgACIAJAB0AFwAcwAuAHoAaQBwACIAIAAiAG8AcgBpAGcAaQBuAC8AJAAoACQAYgApADoAJAAoACQAUAApACIAIABWAEkAQQBfAFMAZQB0AHQAbABlAEEAbABsAF8AdgAwADEAMQA3AC4AcAB5ACAAVgBJAEEAXwBTAGUAdAB0AGwAZQBBAGwAbABfAHYAMAAxADEAOAAuAHAAeQAgADIAPgAmADEAIAB8ACAATwB1AHQALQBOAHUAbABsADsAIABpAGYAIAAoACQATABBAFMAVABFAFgASQBUAEMATwBEAEUAIAAtAGUAcQAgADAAKQAgAHsAIAAkAG8AawAgAD0AIAAkAHQAcgB1AGUAOwAgAGIAcgBlAGEAawAgAH0AIAB9ADsAIABpAGYAIAAoAC0AbgBvAHQAIAAkAG8AawApACAAewAgAFcAcgBpAHQAZQAtAEgAbwBzAHQAIAAnAFsAUgBFAEQAXQAgAGIAbwBvAHQAOgAgAEcAaQB0AEgAdQBiACAA1lMNTjBSIABWAEkAQQBfAFMAZQB0AHQAbABlAEEAbABsACAAdgAwADEAMQA3ACAALwAgAHYAMAAxADEAOAAnACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAFIAZQBkADsAIAByAGUAdAB1AHIAbgAgAH0AOwAgAEUAeABwAGEAbgBkAC0AQQByAGMAaABpAHYAZQAgAC0ATABpAHQAZQByAGEAbABQAGEAdABoACAAIgAkAHQAXABzAC4AegBpAHAAIgAgAC0ARABlAHMAdABpAG4AYQB0AGkAbwBuAFAAYQB0AGgAIAAkAHQAIAAtAEYAbwByAGMAZQA7ACAAJABjACAAPQAgAFsASQBPAC4ARgBpAGwAZQBdADoAOgBSAGUAYQBkAEEAbABsAFQAZQB4AHQAKAAiACQAdABcAFYASQBBAF8AUwBlAHQAdABsAGUAQQBsAGwAXwB2ADAAMQAxADgALgBwAHkAIgAsACAAWwBUAGUAeAB0AC4ARQBuAGMAbwBkAGkAbgBnAF0AOgA6AFUAVABGADgAKQAgAC0AcgBlAHAAbABhAGMAZQAgACIAYAByAGAAbgAiACwAIAAiAGAAbgAiADsAIAAkAHMAIAA9ACAAKABbAEIAaQB0AEMAbwBuAHYAZQByAHQAZQByAF0AOgA6AFQAbwBTAHQAcgBpAG4AZwAoAFsAUwBlAGMAdQByAGkAdAB5AC4AQwByAHkAcAB0AG8AZwByAGEAcABoAHkALgBTAEgAQQAyADUANgBdADoAOgBDAHIAZQBhAHQAZQAoACkALgBDAG8AbQBwAHUAdABlAEgAYQBzAGgAKABbAFQAZQB4AHQALgBVAFQARgA4AEUAbgBjAG8AZABpAG4AZwBdADoAOgBuAGUAdwAoACQAZgBhAGwAcwBlACkALgBHAGUAdABCAHkAdABlAHMAKAAkAGMAKQApACkAIAAtAHIAZQBwAGwAYQBjAGUAIAAnAC0AJwAsACAAJwAnACkALgBUAG8ATABvAHcAZQByAEkAbgB2AGEAcgBpAGEAbgB0ACgAKQA7ACAAaQBmACAAKAAkAHMAIAAtAG4AZQAgACcAMwA3ADgAMQBlADAAMABhAGIAYgA2ADcAYgA0AGMAYgAzAGQAMQA1ADcAMAA3ADEAMwA0AGUANwAyADQAMgBjADIANwAwAGMANwBkADgAZAA5ADgAYgA3ADcAZQBkADkANgA2ADQAYQBmADMAZAA4ADcAZABlAGMANgA5ADEAYgAnACkAIAB7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBSAEUARABdACAAYgBvAG8AdAA6ACAAUwBIAEEALQAyADUANgAgACQAcwAgAA1OL2YgADMANwA4ADEAZQAwADAAYQBiAGIANgA3ACYgIAAtACAADU7RjSIAIAAtAEYAbwByAGUAZwByAG8AdQBuAGQAQwBvAGwAbwByACAAUgBlAGQAOwAgAHIAZQB0AHUAcgBuACAAfQA7ACAAVwByAGkAdABlAC0ASABvAHMAdAAgACIAWwBHAFIARQBFAE4AXQAgAGIAbwBvAHQAOgAgAFYASQBBAF8AUwBlAHQAdABsAGUAQQBsAGwAIAB2ADAAMQAxADgAIABTAEgAQQAtADIANQA2ACAATwBLACAAKAAkAGIAKQAiACAALQBGAG8AcgBlAGcAcgBvAHUAbgBkAEMAbwBsAG8AcgAgAEcAcgBlAGUAbgA7ACAAcAB5AHQAaABvAG4AIAAiACQAdABcAFYASQBBAF8AUwBlAHQAdABsAGUAQQBsAGwAXwB2ADAAMQAxADgALgBwAHkAIgAgAC0ALQByAG8AbwB0ACAAJAByACAALQAtAGEAcABwAGwAeQAtAGIAcgBpAGQAZwBlAHMAIABAAGEAcgBnAHMAIAB9AA==
```

第一行應是 `[GREEN] boot: VIA_SettleAll v0118 SHA-256 OK (claude/optimistic-goodall-yhalc5)`;開機行 SHA-256 `3fcac682e184`。
跑完把最後一段(⑫ 系統矩陣那行到 ⑩ 報告)貼回來。

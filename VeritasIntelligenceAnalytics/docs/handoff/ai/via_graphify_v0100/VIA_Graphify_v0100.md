# VIA · Graphify v0100(程式碼知識圖譜 · 一個系統一張圖 · 全離線)

[Graphify](https://github.com/Graphify-Labs/graphify)(Apache-2.0 · PyPI `graphifyy`)用 tree-sitter AST 把程式碼解析成可查詢的知識圖譜(`graph.html` / `GRAPH_REPORT.md` / `graph.json`)。
本段**只解析程式碼**(`--code-only`)、`GRAPHIFY_BACKEND=none` 關掉所有 LLM 後端 —— **不送任何內容出去**;VIA 夾裡的券商報告 / PDF / 文件一律不讀。

| 項目 | 做法 |
|---|---|
| 版本 | graphifyy **0.9.100**(容器實測同一版)· 裝前核對 wheel SHA-256 `64c5ed6f2dcc…` · 不符就不裝 |
| 安裝位置 | **隔離環境** `%USERPROFILE%\envs\via_graphify`;VRN / VDF / VCGC 的 Python 與環境都不碰(裝前裝後比對主 Python 套件清單)|
| 為什麼不走 VCGC InstallGate | InstallGate 只能 `pip --user` 裝進主 Python(`C:\Python313` = VRN / VDF 擷取用的那支);Graphify 會帶 numpy + 約 30 個 tree-sitter 套件,可能撞引擎環境 |
| 網路 | 只有第一次安裝要下載(PyPI)→ 要 `VIA_NET_CONSENT=YES`(操作員設 · 本段不代設);之後不連網 |
| 範圍 | 一個系統一張圖(由小到大):VRN(`functional modules\VRN2`)· VRN_Shared(`functional modules\VRN`)· VDF(`functional modules\VDF`)· VCGC(`supportive modules\registry`)· 排除 `references/` `intake/` `*quarantine*/` `VIA_RetiredEngines/` `backup*/` `archive*/` 副本 |
| 為什麼不一張大圖 | 容器實測:整個 VIA 樹 12,944 支程式檔一張圖 → 建圖時記憶體爆掉(15 GB 機器被 OOM)|
| 記憶體 | 容器實測峰值:VRN 共用夾 3.4 GB · VCGC registry 5.5 GB;跑每個系統前查可用記憶體,不夠就**跳過並說明**(`$env:VIA_GRAPHIFY_FORCE = '1'` 硬跑)|
| 輸出 | `<VIA 根>\VIA_Reports\graphify\<系統>\graphify-out\`(git 已忽略)· 收據 `VIA_Reports\graphify\VIA_Graphify_latest.json` · 跑完開第一張 graph.html |
| 目標夾 | 先用 `…\Documents\VeritasIntelligenceAnalytics`(操作員給的)· 不存在 → `…\Documents\movies-dataset\VeritasIntelligenceAnalytics` · `$env:VIA_GRAPHIFY_DIR` 可改 · `$env:VIA_GRAPHIFY_ONLY = 'VRN,VDF'` 只跑指定系統 |

容器實測(本倉 VIA 樹 · 排除副本):VRN 共用夾 1,086 支 → **31,579 節點 · 67,999 連線 · 1,334 群** · 121 秒 · 峰值 3.4 GB · **沒有 import 循環** · VDF 921 支 → **15,797 節點 · 35,623 連線 · 607 群** · 65 秒(重跑走快取 30 秒)· VCGC registry 1,600 支 → **47,381 節點 · 116,165 連線 · 1,912 群** · 峰值 5.5 GB(單 worker 一樣 5.5 GB:瓶頸在建圖不在 worker)· VIA 樹 0 個檔被改

## PowerShell 7 視窗(441 字元)

第一次(要下載 · 同意閘是操作員決定):

```powershell
$env:VIA_NET_CONSENT = 'YES'
```

再貼:

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/via_graphify_v0100/VIA_Graphify_v0100_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'2265ff22975f5fc2e8f5d8235e5a5f95f315df4736071998c561b92c44947f8f'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
```

第一行應是 `[GREEN] boot: VIA Graphify v0100 SHA-256 OK`(開機檔 SHA-256 `2265ff22975f` · 主段 `34bf1574d5e0`)。

## cmd 視窗(1232 字元)

```bat
pwsh -NoProfile -ExecutionPolicy Bypass -EncodedCommand JAByAD0AIgAkAEgATwBNAEUAXABPAG4AZQBEAHIAaQB2AGUAXABEAG8AYwB1AG0AZQBuAHQAcwBcAG0AbwB2AGkAZQBzAC0AZABhAHQAYQBzAGUAdAAiADsAZwBpAHQAIAAtAEMAIAAkAHIAIABmAGUAdABjAGgAIAAtAHEAIABvAHIAaQBnAGkAbgAgAGMAbABhAHUAZABlAC8AbwBwAHQAaQBtAGkAcwB0AGkAYwAtAGcAbwBvAGQAYQBsAGwALQB5AGgAYQBsAGMANQA7ACQAYwA9ACgAZwBpAHQAIAAtAEMAIAAkAHIAIABzAGgAbwB3ACAAIgBGAEUAVABDAEgAXwBIAEUAQQBEADoAVgBlAHIAaQB0AGEAcwBJAG4AdABlAGwAbABpAGcAZQBuAGMAZQBBAG4AYQBsAHkAdABpAGMAcwAvAGQAbwBjAHMALwBoAGEAbgBkAG8AZgBmAC8AYQBpAC8AdgBpAGEAXwBnAHIAYQBwAGgAaQBmAHkAXwB2ADAAMQAwADAALwBWAEkAQQBfAEcAcgBhAHAAaABpAGYAeQBfAHYAMAAxADAAMABfAGIAbwBvAHQALgB0AHgAdAAiACkALQBqAG8AaQBuACIAYABuACIAOwBpAGYAKAAoAEcAZQB0AC0ARgBpAGwAZQBIAGEAcwBoACAALQBJAG4AcAB1AHQAUwB0AHIAZQBhAG0AIAAoAFsASQBPAC4ATQBlAG0AbwByAHkAUwB0AHIAZQBhAG0AXQA6ADoAbgBlAHcAKABbAGIAeQB0AGUAWwBdAF0AWwBjAGgAYQByAFsAXQBdACQAYwApACkAKQAuAEgAYQBzAGgALQBlAHEAJwAyADIANgA1AGYAZgAyADIAOQA3ADUAZgA1AGYAYwAyAGUAOABmADUAZAA4ADIAMwA1AGUANQBhADUAZgA5ADUAZgAzADEANQBkAGYANAA3ADMANgAwADcAMQA5ADkAOABjADUANgAxAGIAOQAyAGMANAA0ADkANAA3AGYAOABmACcAKQB7AGkAZQB4ACAAJABjAH0AZQBsAHMAZQB7ACcAWwBSAEUARABdACAAYgBvAG8AdAAgAFMASABBAC0AMgA1ADYAIABtAGkAcwBtAGEAdABjAGgAIAAtACAAbgBvAHQAIAByAHUAbgAnAH0A
```

## 查詢(不重讀檔)

```powershell
& "$env:USERPROFILE\envs\via_graphify\Scripts\graphify.exe" query "共識引擎怎麼連到 Combined 冊?" --graph "<VIA 根>\VIA_Reports\graphify\VRN\graphify-out\graph.json"
& "$env:USERPROFILE\envs\via_graphify\Scripts\graphify.exe" path "ConsensusJoin" "Workbench" --graph "<…>\graph.json"
& "$env:USERPROFILE\envs\via_graphify\Scripts\graphify.exe" god-nodes --graph "<…>\graph.json"
```

本機 Claude Code 想直接打 `/graphify`:`graphify.exe install --platform windows` 會註冊技能;**注意**技能版會把文件 / PDF 交給助理模型做語意那段,VIA 夾有券商報告 —— 建議照本段只解析程式碼。

## 開機行(1,727 字元)

```powershell
& { $R = $env:VRN2_ROOT ?? (Join-Path $HOME 'OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'); $P = 'VeritasIntelligenceAnalytics/docs/handoff/ai/via_graphify_v0100'; $F = 'VIA_Graphify_v0100.md'; $H = '34bf1574d5e041a876827f9d3a4042aba10d8d84a732ff4b1c64ca6f1c672624'; $top = "$(git -C $R rev-parse --show-toplevel 2>$null)".Trim(); if (-not $top) { Write-Host "[RED] boot: $R is not a git repo (set `$env:VRN2_ROOT)" -ForegroundColor Red; return }; $t = Join-Path ([IO.Path]::GetTempPath()) "via_graphify_boot_$(Get-Date -Format yyyyMMddHHmmss)"; $z = Join-Path $t 'g.zip'; New-Item -ItemType Directory -Force -Path $t | Out-Null; $ok = $false; foreach ($b in 'claude/optimistic-goodall-yhalc5', 'main') { foreach ($w in 0, 3, 9) { Start-Sleep -Seconds $w; git -C $top fetch -q origin $b 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { break } }; git -C $top archive --format=zip -o $z "origin/$($b):$($P)" $F 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } }; if (-not $ok) { Write-Host "[RED] boot: cannot read $F from GitHub" -ForegroundColor Red; return }; Expand-Archive -LiteralPath $z -DestinationPath $t -Force; $md = [IO.File]::ReadAllText((Join-Path $t $F), [Text.Encoding]::UTF8) -replace "`r`n", "`n"; $c = [regex]::Match($md, '(?s)<!-- graphify line -->\n```powershell\n(.*?)\n```').Groups[1].Value; $s = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.UTF8Encoding]::new($false).GetBytes($c))) -replace '-', '').ToLowerInvariant(); if ($s -ne $H) { Write-Host "[RED] boot: SHA-256 $s is not $H - not run" -ForegroundColor Red; return }; Write-Host "[GREEN] boot: VIA Graphify v0100 SHA-256 OK ($b)" -ForegroundColor Green; Invoke-Expression $c }
```

## 主段那一行(開機行從 GitHub 取這段、核對 SHA-256 才執行 · 不用貼它)

<!-- graphify line -->
```powershell
& { $ErrorActionPreference = 'Continue'; if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh)' -ForegroundColor Red; return }; try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }; $T0 = Get-Date; $VER = '0.9.100'; $WHL = '64c5ed6f2dcc8c28b6a96c87023851c1644c16f55a87f45dbc9127119eb6e769'; Write-Host "[VIA] Graphify v0100 · graphifyy $($VER)(Graphify-Labs/graphify · Apache-2.0)· 只解析程式碼 · 全離線 · 不送任何內容出去 · 一個系統一張圖" -ForegroundColor Yellow; $want = $env:VIA_GRAPHIFY_DIR ?? (Join-Path $HOME 'OneDrive\Documents\VeritasIntelligenceAnalytics'); $alt = Join-Path $HOME 'OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'; $Root = (Test-Path -LiteralPath $want -PathType Container) ? $want : ((Test-Path -LiteralPath $alt -PathType Container) ? $alt : $null); if (-not $Root) { Write-Host "[RED] ① VIA 根不在:$($want) · 也不在 $($alt)(先貼 `$env:VIA_GRAPHIFY_DIR = '<VIA 根>')" -ForegroundColor Red; return }; Write-Host "[GREEN] ① VIA 根 $($Root)$(($Root -ne $want) ? "(你給的 $($want) 不在 → 用這一份)" : '')" -ForegroundColor Green; $Out = $env:VIA_GRAPHIFY_OUT ?? (Join-Path $Root 'VIA_Reports' 'graphify'); New-Item -ItemType Directory -Force -Path $Out | Out-Null; $py = $env:VIA_GRAPHIFY_PY ?? (Get-Command python, python3, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source; if (-not $py) { Write-Host '[RED] ② 找不到 python(或先設 $env:VIA_GRAPHIFY_PY)' -ForegroundColor Red; return }; $pv = "$(& $py -c "import sys;print('%d.%d' % sys.version_info[:2])" 2>$null)".Trim(); if (-not $pv -or [version]$pv -lt [version]'3.10') { Write-Host "[RED] ② $($py) 版本 $($pv) · Graphify 要 3.10 以上" -ForegroundColor Red; return }; Write-Host "[GREEN] ② Python $($pv) · $($py)(只用來建隔離環境)" -ForegroundColor Green; $venv = $env:VIA_GRAPHIFY_VENV ?? (Join-Path ($env:USERPROFILE ?? $HOME) 'envs' 'via_graphify'); $vpy = $IsWindows ? (Join-Path $venv 'Scripts\python.exe') : (Join-Path $venv 'bin/python'); $gx = $IsWindows ? (Join-Path $venv 'Scripts\graphify.exe') : (Join-Path $venv 'bin/graphify'); $have = (Test-Path -LiteralPath $gx) ? "$(& $gx --version 2>$null)".Trim() : ''; if ($have -match [regex]::Escape($VER)) { Write-Host "[GREEN] ③ 隔離環境已有 graphify $($VER) · $($venv)(這次不安裝 · 不連網)" -ForegroundColor Green } else { $g1 = "$env:VIA_NET_CONSENT"; if ($g1 -cne 'YES') { Write-Host "[YELLOW] ③ 第一次要從 PyPI 下載 graphifyy $($VER)(網路)· VIA 網路同意閘未開(VIA_NET_CONSENT=$(($g1) ? $g1 : '(未設)'))· 操作員決定 · 本段不代設" -ForegroundColor Yellow; Write-Host "    同一個視窗先貼:`$env:VIA_NET_CONSENT = 'YES'  再貼同一行(cmd 視窗:set VIA_NET_CONSENT=YES)" -ForegroundColor Cyan; return }; $frz0 = ((& $py -m pip freeze 2>$null) -join "`n"); if (-not (Test-Path -LiteralPath $vpy)) { & $py -m venv $venv; if ($LASTEXITCODE -or -not (Test-Path -LiteralPath $vpy)) { Write-Host "[RED] ③ 建不了隔離環境 $($venv)" -ForegroundColor Red; return } }; $dl = Join-Path ([IO.Path]::GetTempPath()) "via_graphify_$(Get-Date -Format yyyyMMddHHmmss)"; New-Item -ItemType Directory -Force -Path $dl | Out-Null; & $vpy -m pip download --disable-pip-version-check --no-deps -q -d $dl "graphifyy==$($VER)"; $w = Get-ChildItem -LiteralPath $dl -Filter "graphifyy-$($VER)-*.whl" | Select-Object -First 1; if (-not $w) { Write-Host "[RED] ③ 下載不到 graphifyy $($VER)(網路 / PyPI)" -ForegroundColor Red; return }; $ws = (Get-FileHash -LiteralPath $w.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); if ($ws -ne $WHL) { Write-Host "[RED] ③ wheel SHA-256 $($ws) 不是容器實測那一份 $($WHL) · 不安裝" -ForegroundColor Red; return }; Write-Host "[GREEN] ③ wheel SHA-256 $($WHL.Substring(0, 12)) 相符 → 裝進隔離環境(相依套件也只進這個環境)" -ForegroundColor Green; & $vpy -m pip install --disable-pip-version-check -q $w.FullName; if ($LASTEXITCODE -or -not (Test-Path -LiteralPath $gx)) { Write-Host "[RED] ③ 安裝失敗(上面 pip 的訊息)" -ForegroundColor Red; return }; $frz1 = ((& $py -m pip freeze 2>$null) -join "`n"); if ($frz0 -ceq $frz1) { Write-Host "[GREEN] ③ 主 Python $($py) 的套件清單前後一致(沒有被動到)" -ForegroundColor Green } else { Write-Host "[YELLOW] ③ 主 Python 套件清單前後不同 · 不是本段造成的就是別的程式剛好在裝 · 請貼回給 AI" -ForegroundColor Yellow } }; $sys = @(@{ n = 'VRN'; d = 'functional modules\VRN2'; gb = 3 }, @{ n = 'VRN_Shared'; d = 'functional modules\VRN'; gb = 4 }, @{ n = 'VDF'; d = 'functional modules\VDF'; gb = 4 }, @{ n = 'VCGC'; d = 'supportive modules\registry'; gb = 6 }); $only = @("$env:VIA_GRAPHIFY_ONLY" -split '[,; ]+' | Where-Object { $_ }); $ex = @('references/', 'intake/', '_quarantine*/', '*quarantine*/', 'VIA_RetiredEngines/', 'backup*/', 'archive*/'); $exa = @($ex | ForEach-Object { '--exclude'; $_ }); $e0 = @{ B = $env:GRAPHIFY_BACKEND; Q = $env:GRAPHIFY_QUERY_LOG_DISABLE }; $env:GRAPHIFY_BACKEND = 'none'; $env:GRAPHIFY_QUERY_LOG_DISABLE = '1'; $res = @(); foreach ($s in $sys) { if ($only -and $s.n -notin $only) { continue }; $src = Join-Path $Root ($s.d -replace '\\', [IO.Path]::DirectorySeparatorChar); if (-not (Test-Path -LiteralPath $src -PathType Container)) { Write-Host "[GRAY] ④ $($s.n) · $($s.d) 不在 · 跳過" -ForegroundColor DarkGray; $res += [pscustomobject]@{ system = $s.n; lamp = 'GRAY'; why = 'folder missing' }; continue }; $free = -1; try { if ($IsWindows) { $free = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1) } else { $free = [math]::Round(([long]((Get-Content /proc/meminfo | Select-String '^MemAvailable').Line -replace '\D', '')) / 1MB, 1) } } catch { }; if ($free -ge 0 -and $free -lt $s.gb -and "$env:VIA_GRAPHIFY_FORCE" -ne '1') { Write-Host "[YELLOW] ④ $($s.n) · 可用記憶體 $($free) GB < 需要約 $($s.gb) GB · 跳過(關掉別的程式再貼一次 · 或先貼 `$env:VIA_GRAPHIFY_FORCE = '1' 硬跑)" -ForegroundColor Yellow; $res += [pscustomobject]@{ system = $s.n; lamp = 'YELLOW'; why = "free RAM $($free) GB < $($s.gb) GB" }; continue }; $o = Join-Path $Out $s.n; New-Item -ItemType Directory -Force -Path $o | Out-Null; $t1 = Get-Date; Write-Host "[計] ④ $($s.n) · $($src) · 可用記憶體 $($free) GB · 抽取中(進度照 graphify 自己印的)" -ForegroundColor Cyan; & $gx extract $src --code-only --max-workers 2 --out $o @exa; $rc = $LASTEXITCODE; if (-not $rc) { & $gx cluster-only $o --no-label; $rc = $LASTEXITCODE }; $gj = Join-Path $o 'graphify-out' 'graph.json'; if ($rc -or -not (Test-Path -LiteralPath $gj)) { Write-Host "[RED] ④ $($s.n) · rc $($rc) · 沒有圖(上面 graphify 的訊息貼回給 AI)" -ForegroundColor Red; $res += [pscustomobject]@{ system = $s.n; lamp = 'RED'; rc = $rc }; continue }; $cnt = "$(& $vpy -c "import json,sys;g=json.load(open(sys.argv[1],encoding='utf-8'));print(len(g.get('nodes') or []), len(g.get('links') or g.get('edges') or []))" $gj 2>$null)".Trim() -split '\s+'; $nn = [int]($cnt[0] ?? 0); $ne = [int]($cnt[1] ?? 0); if ($nn -le 0) { Write-Host "[RED] ④ $($s.n) · graph.json 讀不出節點(0)· 貼回給 AI" -ForegroundColor Red; $res += [pscustomobject]@{ system = $s.n; lamp = 'RED'; why = 'graph.json has 0 nodes' }; continue }; Write-Host "[GREEN] ④ $($s.n) · 節點 $($nn) · 連線 $($ne) · $([int]((Get-Date) - $t1).TotalSeconds) 秒 · $(Join-Path $o 'graphify-out' 'graph.html')" -ForegroundColor Green; $res += [pscustomobject]@{ system = $s.n; lamp = 'GREEN'; nodes = $nn; edges = $ne; seconds = [int]((Get-Date) - $t1).TotalSeconds; html = (Join-Path $o 'graphify-out' 'graph.html'); report = (Join-Path $o 'graphify-out' 'GRAPH_REPORT.md'); graph = $gj } }; $env:GRAPHIFY_BACKEND = $e0.B; $env:GRAPHIFY_QUERY_LOG_DISABLE = $e0.Q; @{ tool = 'graphifyy'; version = $VER; wheel_sha256 = $WHL; root = $Root; mode = 'code-only · GRAPHIFY_BACKEND=none · offline · one graph per system'; excludes = $ex; systems = $res; seconds = [int]((Get-Date) - $T0).TotalSeconds; at = (Get-Date -Format s) } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Out 'VIA_Graphify_latest.json') -Encoding utf8; $ok = @($res | Where-Object lamp -EQ 'GREEN'); Write-Host "===== Graphify · 綠 $($ok.Count) · 黃 $(@($res | Where-Object lamp -EQ 'YELLOW').Count) · 紅 $(@($res | Where-Object lamp -EQ 'RED').Count) · $([int]((Get-Date) - $T0).TotalSeconds) 秒 · 收據 $(Join-Path $Out 'VIA_Graphify_latest.json')" -ForegroundColor (($res | Where-Object lamp -EQ 'RED') ? 'Red' : 'Green'); if ($ok) { Write-Host "[計] ⑤ 查詢(不重讀檔):& '$($gx)' query `"<問題>`" --graph '$($ok[0].graph)'  ·  path `"A`" `"B`"  ·  explain `"X`"  ·  god-nodes --graph <graph.json>" -ForegroundColor DarkGray }; Write-Host "[計] ⑤ 本機 Claude Code 想打 /graphify:& '$($gx)' install --platform windows(該指令會把文件 / PDF 交給助理模型做語意那段 · VIA 夾有券商報告 · 建議照這裡只解析程式碼)" -ForegroundColor DarkGray; if ($ok -and $IsWindows -and "$env:VIA_NO_OPEN" -ne '1') { try { Start-Process -FilePath $ok[0].html -ErrorAction Stop; Write-Host "[GREEN] ⑥ 已開 $($ok[0].system) 的 graph.html(其他系統的在同一個 graphify 夾)" -ForegroundColor Green } catch { Write-Host '[YELLOW] ⑥ graph.html 沒開成 · 自己開上面的檔' -ForegroundColor Yellow } } }
```

## 可讀版 · 主段

```powershell
& {
$ErrorActionPreference = 'Continue'
if ($PSVersionTable.PSVersion.Major -lt 7) { Write-Host '[RED] 這段要 PowerShell 7 以上(pwsh)' -ForegroundColor Red; return }
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$T0 = Get-Date
$VER = '0.9.100'
$WHL = '64c5ed6f2dcc8c28b6a96c87023851c1644c16f55a87f45dbc9127119eb6e769'
Write-Host "[VIA] Graphify v0100 · graphifyy $($VER)(Graphify-Labs/graphify · Apache-2.0)· 只解析程式碼 · 全離線 · 不送任何內容出去 · 一個系統一張圖" -ForegroundColor Yellow
# ① VIA 根:先用操作員給的路徑 · 不存在 → 退到 movies-dataset 那份
$want = $env:VIA_GRAPHIFY_DIR ?? (Join-Path $HOME 'OneDrive\Documents\VeritasIntelligenceAnalytics')
$alt = Join-Path $HOME 'OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$Root = (Test-Path -LiteralPath $want -PathType Container) ? $want : ((Test-Path -LiteralPath $alt -PathType Container) ? $alt : $null)
if (-not $Root) { Write-Host "[RED] ① VIA 根不在:$($want) · 也不在 $($alt)(先貼 `$env:VIA_GRAPHIFY_DIR = '<VIA 根>')" -ForegroundColor Red; return }
Write-Host "[GREEN] ① VIA 根 $($Root)$(($Root -ne $want) ? "(你給的 $($want) 不在 → 用這一份)" : '')" -ForegroundColor Green
$Out = $env:VIA_GRAPHIFY_OUT ?? (Join-Path $Root 'VIA_Reports' 'graphify')
New-Item -ItemType Directory -Force -Path $Out | Out-Null
# ② Python 3.10+(只拿來建隔離環境 · 不在它身上裝任何東西)
$py = $env:VIA_GRAPHIFY_PY ?? (Get-Command python, python3, py -ErrorAction SilentlyContinue | Where-Object Source -NotMatch 'WindowsApps' | Select-Object -First 1).Source
if (-not $py) { Write-Host '[RED] ② 找不到 python(或先設 $env:VIA_GRAPHIFY_PY)' -ForegroundColor Red; return }
$pv = "$(& $py -c "import sys;print('%d.%d' % sys.version_info[:2])" 2>$null)".Trim()
if (-not $pv -or [version]$pv -lt [version]'3.10') { Write-Host "[RED] ② $($py) 版本 $($pv) · Graphify 要 3.10 以上" -ForegroundColor Red; return }
Write-Host "[GREEN] ② Python $($pv) · $($py)(只用來建隔離環境)" -ForegroundColor Green
# ③ 隔離環境(VRN / VDF / VCGC 的 Python 與 env 都不碰)
$venv = $env:VIA_GRAPHIFY_VENV ?? (Join-Path ($env:USERPROFILE ?? $HOME) 'envs' 'via_graphify')
$vpy = $IsWindows ? (Join-Path $venv 'Scripts\python.exe') : (Join-Path $venv 'bin/python')
$gx = $IsWindows ? (Join-Path $venv 'Scripts\graphify.exe') : (Join-Path $venv 'bin/graphify')
$have = (Test-Path -LiteralPath $gx) ? "$(& $gx --version 2>$null)".Trim() : ''
if ($have -match [regex]::Escape($VER)) { Write-Host "[GREEN] ③ 隔離環境已有 graphify $($VER) · $($venv)(這次不安裝 · 不連網)" -ForegroundColor Green } else {
$g1 = "$env:VIA_NET_CONSENT"
if ($g1 -cne 'YES') { Write-Host "[YELLOW] ③ 第一次要從 PyPI 下載 graphifyy $($VER)(網路)· VIA 網路同意閘未開(VIA_NET_CONSENT=$(($g1) ? $g1 : '(未設)'))· 操作員決定 · 本段不代設" -ForegroundColor Yellow; Write-Host "    同一個視窗先貼:`$env:VIA_NET_CONSENT = 'YES'  再貼同一行(cmd 視窗:set VIA_NET_CONSENT=YES)" -ForegroundColor Cyan; return }
$frz0 = ((& $py -m pip freeze 2>$null) -join "`n")
if (-not (Test-Path -LiteralPath $vpy)) { & $py -m venv $venv; if ($LASTEXITCODE -or -not (Test-Path -LiteralPath $vpy)) { Write-Host "[RED] ③ 建不了隔離環境 $($venv)" -ForegroundColor Red; return } }
$dl = Join-Path ([IO.Path]::GetTempPath()) "via_graphify_$(Get-Date -Format yyyyMMddHHmmss)"
New-Item -ItemType Directory -Force -Path $dl | Out-Null
& $vpy -m pip download --disable-pip-version-check --no-deps -q -d $dl "graphifyy==$($VER)"
$w = Get-ChildItem -LiteralPath $dl -Filter "graphifyy-$($VER)-*.whl" | Select-Object -First 1
if (-not $w) { Write-Host "[RED] ③ 下載不到 graphifyy $($VER)(網路 / PyPI)" -ForegroundColor Red; return }
$ws = (Get-FileHash -LiteralPath $w.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ws -ne $WHL) { Write-Host "[RED] ③ wheel SHA-256 $($ws) 不是容器實測那一份 $($WHL) · 不安裝" -ForegroundColor Red; return }
Write-Host "[GREEN] ③ wheel SHA-256 $($WHL.Substring(0, 12)) 相符 → 裝進隔離環境(相依套件也只進這個環境)" -ForegroundColor Green
& $vpy -m pip install --disable-pip-version-check -q $w.FullName
if ($LASTEXITCODE -or -not (Test-Path -LiteralPath $gx)) { Write-Host "[RED] ③ 安裝失敗(上面 pip 的訊息)" -ForegroundColor Red; return }
$frz1 = ((& $py -m pip freeze 2>$null) -join "`n")
if ($frz0 -ceq $frz1) { Write-Host "[GREEN] ③ 主 Python $($py) 的套件清單前後一致(沒有被動到)" -ForegroundColor Green } else { Write-Host "[YELLOW] ③ 主 Python 套件清單前後不同 · 不是本段造成的就是別的程式剛好在裝 · 請貼回給 AI" -ForegroundColor Yellow }
}
# ④ 一個系統一張圖(由小到大)· 排除副本夾 · 記憶體不夠就跳過(容器實測峰值:VRN 共用夾 3.4 GB · VCGC registry 5.5 GB)
$sys = @(@{ n = 'VRN'; d = 'functional modules\VRN2'; gb = 3 }, @{ n = 'VRN_Shared'; d = 'functional modules\VRN'; gb = 4 }, @{ n = 'VDF'; d = 'functional modules\VDF'; gb = 4 }, @{ n = 'VCGC'; d = 'supportive modules\registry'; gb = 6 })
$only = @("$env:VIA_GRAPHIFY_ONLY" -split '[,; ]+' | Where-Object { $_ })
$ex = @('references/', 'intake/', '_quarantine*/', '*quarantine*/', 'VIA_RetiredEngines/', 'backup*/', 'archive*/')
$exa = @($ex | ForEach-Object { '--exclude'; $_ })
$e0 = @{ B = $env:GRAPHIFY_BACKEND; Q = $env:GRAPHIFY_QUERY_LOG_DISABLE }
$env:GRAPHIFY_BACKEND = 'none'; $env:GRAPHIFY_QUERY_LOG_DISABLE = '1'
$res = @()
foreach ($s in $sys) {
if ($only -and $s.n -notin $only) { continue }
$src = Join-Path $Root ($s.d -replace '\\', [IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath $src -PathType Container)) { Write-Host "[GRAY] ④ $($s.n) · $($s.d) 不在 · 跳過" -ForegroundColor DarkGray; $res += [pscustomobject]@{ system = $s.n; lamp = 'GRAY'; why = 'folder missing' }; continue }
$free = -1
try { if ($IsWindows) { $free = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1) } else { $free = [math]::Round(([long]((Get-Content /proc/meminfo | Select-String '^MemAvailable').Line -replace '\D', '')) / 1MB, 1) } } catch { }
if ($free -ge 0 -and $free -lt $s.gb -and "$env:VIA_GRAPHIFY_FORCE" -ne '1') { Write-Host "[YELLOW] ④ $($s.n) · 可用記憶體 $($free) GB < 需要約 $($s.gb) GB · 跳過(關掉別的程式再貼一次 · 或先貼 `$env:VIA_GRAPHIFY_FORCE = '1' 硬跑)" -ForegroundColor Yellow; $res += [pscustomobject]@{ system = $s.n; lamp = 'YELLOW'; why = "free RAM $($free) GB < $($s.gb) GB" }; continue }
$o = Join-Path $Out $s.n
New-Item -ItemType Directory -Force -Path $o | Out-Null
$t1 = Get-Date
Write-Host "[計] ④ $($s.n) · $($src) · 可用記憶體 $($free) GB · 抽取中(進度照 graphify 自己印的)" -ForegroundColor Cyan
& $gx extract $src --code-only --max-workers 2 --out $o @exa
$rc = $LASTEXITCODE
if (-not $rc) { & $gx cluster-only $o --no-label; $rc = $LASTEXITCODE }
$gj = Join-Path $o 'graphify-out' 'graph.json'
if ($rc -or -not (Test-Path -LiteralPath $gj)) { Write-Host "[RED] ④ $($s.n) · rc $($rc) · 沒有圖(上面 graphify 的訊息貼回給 AI)" -ForegroundColor Red; $res += [pscustomobject]@{ system = $s.n; lamp = 'RED'; rc = $rc }; continue }
$cnt = "$(& $vpy -c "import json,sys;g=json.load(open(sys.argv[1],encoding='utf-8'));print(len(g.get('nodes') or []), len(g.get('links') or g.get('edges') or []))" $gj 2>$null)".Trim() -split '\s+'
$nn = [int]($cnt[0] ?? 0); $ne = [int]($cnt[1] ?? 0)
if ($nn -le 0) { Write-Host "[RED] ④ $($s.n) · graph.json 讀不出節點(0)· 貼回給 AI" -ForegroundColor Red; $res += [pscustomobject]@{ system = $s.n; lamp = 'RED'; why = 'graph.json has 0 nodes' }; continue }
Write-Host "[GREEN] ④ $($s.n) · 節點 $($nn) · 連線 $($ne) · $([int]((Get-Date) - $t1).TotalSeconds) 秒 · $(Join-Path $o 'graphify-out' 'graph.html')" -ForegroundColor Green
$res += [pscustomobject]@{ system = $s.n; lamp = 'GREEN'; nodes = $nn; edges = $ne; seconds = [int]((Get-Date) - $t1).TotalSeconds; html = (Join-Path $o 'graphify-out' 'graph.html'); report = (Join-Path $o 'graphify-out' 'GRAPH_REPORT.md'); graph = $gj }
}
$env:GRAPHIFY_BACKEND = $e0.B; $env:GRAPHIFY_QUERY_LOG_DISABLE = $e0.Q
# ⑤ 收據(在 VIA_Reports\graphify · git 不收)
@{ tool = 'graphifyy'; version = $VER; wheel_sha256 = $WHL; root = $Root; mode = 'code-only · GRAPHIFY_BACKEND=none · offline · one graph per system'; excludes = $ex; systems = $res; seconds = [int]((Get-Date) - $T0).TotalSeconds; at = (Get-Date -Format s) } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Out 'VIA_Graphify_latest.json') -Encoding utf8
$ok = @($res | Where-Object lamp -EQ 'GREEN')
Write-Host "===== Graphify · 綠 $($ok.Count) · 黃 $(@($res | Where-Object lamp -EQ 'YELLOW').Count) · 紅 $(@($res | Where-Object lamp -EQ 'RED').Count) · $([int]((Get-Date) - $T0).TotalSeconds) 秒 · 收據 $(Join-Path $Out 'VIA_Graphify_latest.json')" -ForegroundColor (($res | Where-Object lamp -EQ 'RED') ? 'Red' : 'Green')
if ($ok) { Write-Host "[計] ⑤ 查詢(不重讀檔):& '$($gx)' query `"<問題>`" --graph '$($ok[0].graph)'  ·  path `"A`" `"B`"  ·  explain `"X`"  ·  god-nodes --graph <graph.json>" -ForegroundColor DarkGray }
Write-Host "[計] ⑤ 本機 Claude Code 想打 /graphify:& '$($gx)' install --platform windows(該指令會把文件 / PDF 交給助理模型做語意那段 · VIA 夾有券商報告 · 建議照這裡只解析程式碼)" -ForegroundColor DarkGray
if ($ok -and $IsWindows -and "$env:VIA_NO_OPEN" -ne '1') { try { Start-Process -FilePath $ok[0].html -ErrorAction Stop; Write-Host "[GREEN] ⑥ 已開 $($ok[0].system) 的 graph.html(其他系統的在同一個 graphify 夾)" -ForegroundColor Green } catch { Write-Host '[YELLOW] ⑥ graph.html 沒開成 · 自己開上面的檔' -ForegroundColor Yellow } }
}
```

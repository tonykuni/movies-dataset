# VIA Agent OS v0100(操作員 2026-11-04 交付 · 整合 + 啟動)

`VeritasIntelligenceAnalytics/supportive modules/agent_os/VIA_AgentOS_v0100.py`(SHA-256 `7424eacfd2ea`)= 操作員上傳的 `via_agent_os.py` 原檔 + 第 3 行加速器標記 `# [VIA:ACCEL-BRIDGE:v0111]`(其他一字不改)。
單檔 · 只用 Python 標準庫 · 本機優先 · 預設唯讀 / 乾跑。

| 項目 | 內容 |
|---|---|
| 八個 Skill | planner · architect · decision-log · factor-builder · factor-validator · strategy-builder · code-review · memory-manager(決定性 · 單層呼叫 · 不遞迴)|
| 安全邊界(原檔契約)| 不連網 · 不開子行程 / shell · 不動態匯入被掃的程式 · 不裝套件 · AST 只讀不改原始碼 · SSOT 寫入要 `--apply` 且先備份 · 指標只記數字不記內容 |
| SSOT | `<VIA 根>\.via\ssot.json`(只合併自己的 `via-agent-os` 命名空間 · 既有欄位保留)· **不進倉**:每次桌機 bootstrap 都會改它,進倉會擋 git pull(教訓帳本 RC-21 同型)|
| VCGC 連線 | 原檔自己標 `UNVERIFIED_NOT_CONNECTED`(沒有審過的 mount / adapter 前不算接上)· 本輪 VCGC 只做元件登記(registry-sync · 編號)|
| 四系統 | 不屬於 VRN-1 / VRN-2 / VDF / VCGC 任一系統;放 VIA 共用 `supportive modules`,只讀掃描,不改任何系統的檔 |

## 容器實測(2026-11-04)

| 項目 | 結果 |
|---|---|
| `selftest` | ok · 15 個測試 · 失敗 0 · 錯誤 0(`VIA_AgentOS_Selftest_v0100.json`)|
| `skills test` | PASS · 8 個 Skill · 23 / 23 案例(`VIA_AgentOS_SkillTest_v0100.json` · 與操作員附的報告一致)|
| `bootstrap --root <VIA>`(乾跑)| DRY_RUN · AST 索引 1,500 支(上限)· 新增 Skill 8 · 衝突 0 · 64 秒 · 沒寫任何檔(`VIA_AgentOS_BootstrapDryRun_v0100.json`)|
| `dashboard` | 單檔 HTML 47 KB(`VIA_AgentOS_Dashboard_v0100.html`)· Chromium 1,440 / 390 寬:外連 0 · 錯誤 0 · 橫向溢出 0 |
| 編譯 | `-W error::SyntaxWarning` 乾淨 |

## 桌機啟動(PowerShell 7 · 一行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/via_agent_os_v0100/VIA_AgentOS_v0100_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'06dc25e1dd0b7e4bff6d94cf27df2ea6719d094e7543abeba604c1d46c43f77d'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
```

它做的事(開機檔 `VIA_AgentOS_v0100_boot.txt` · SHA-256 `06dc25e1dd0b`):從分支取模組 → 核對 SHA-256 → 找 VIA 根(`$env:VIA_AGENTOS_ROOT` → `Documents\VeritasIntelligenceAnalytics`(要有系統夾才算)→ `Documents\movies-dataset\VeritasIntelligenceAnalytics`)→ `selftest` 過了才 `bootstrap --apply` → `dashboard` → 開儀表板。
操作員 2026-11-04 給的 `C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics`:Graphify v0100 的收據顯示那個夾沒有任何系統夾(四系統全灰),所以會落到 `movies-dataset\VeritasIntelligenceAnalytics`;要指定就先貼 `$env:VIA_AGENTOS_ROOT = '<路徑>'`。

## 可讀版

```powershell
$r = "$HOME\OneDrive\Documents\movies-dataset"
git -C $r fetch -q origin claude/optimistic-goodall-yhalc5
$t = Join-Path ([IO.Path]::GetTempPath()) "via_aos_$(Get-Random)"
New-Item -ItemType Directory -Force -Path $t | Out-Null
git -C $r archive --format=zip -o "$t\a.zip" FETCH_HEAD "VeritasIntelligenceAnalytics/supportive modules/agent_os/VIA_AgentOS_v0100.py"
Expand-Archive -LiteralPath "$t\a.zip" -DestinationPath $t -Force
$f = "$HOME\Downloads\VIA_AgentOS_v0100.py"
Copy-Item -LiteralPath "$t\VeritasIntelligenceAnalytics\supportive modules\agent_os\VIA_AgentOS_v0100.py" -Destination $f -Force
if ((Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash -ne '7424eacfd2ea5375e0702b15aed9bee06f6595522d2b488d92afcbca364ac968') { Write-Host '[RED] VIA Agent OS SHA-256 mismatch - not run' -ForegroundColor Red }
else {
$V = @($env:VIA_AGENTOS_ROOT, "$HOME\OneDrive\Documents\VeritasIntelligenceAnalytics", "$r\VeritasIntelligenceAnalytics") | Where-Object { $_ -and ((Test-Path -LiteralPath "$_\supportive modules\registry") -or (Test-Path -LiteralPath "$_\functional modules")) } | Select-Object -First 1
if (-not $V) { Write-Host '[RED] no VIA root with system folders (set $env:VIA_AGENTOS_ROOT)' -ForegroundColor Red }
else {
Write-Host "[GREEN] VIA Agent OS v0100 SHA-256 OK - root $V" -ForegroundColor Green
python $f selftest | Out-Null; if ($LASTEXITCODE) { Write-Host '[RED] selftest failed - SSOT not written' -ForegroundColor Red }
else {
python $f bootstrap --root $V --apply
New-Item -ItemType Directory -Force -Path "$V\VIA_Reports\agent_os" | Out-Null
python $f dashboard --root $V --out "$V\VIA_Reports\agent_os\VIA_AgentOS_Dashboard.html" --overwrite
Start-Process "$V\VIA_Reports\agent_os\VIA_AgentOS_Dashboard.html"
}
}
}
```

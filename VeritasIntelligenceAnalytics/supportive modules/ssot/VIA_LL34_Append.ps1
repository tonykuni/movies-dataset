#requires -Version 7.0
<#
================================================================================
 VIA_LL34_Append.ps1
 ASSET_ID    : AST-PS-MOD-LL-APPEND-034
 DISPLAY     : SYS_VIA.LL.APPEND-034
 VERSION     : 1.0.0       STATUS : ready
 PURPOSE     : 把 LL#34（Patcher 三大教訓）追加到 PS7 Lesson Learned 手冊
 STRATEGY    :
   1. 偵測手冊檔（依優先順序）：
      a. -ManualPath 顯式指定
      b. 同目錄 LL34_entry.md / *Lesson*Learn*.md / *LL*.md
      c. OneDrive\VeritasIntelligenceAnalytics\docs\*.md
      d. 都找不到 → 在 -OutDir 寫獨立 LL34_entry.md
   2. 重複加入保護：偵測「LL#34」已存在 → SKIP
   3. DryRun 預覽差異
================================================================================
#>

param(
    [string]$ManualPath = '',
    [string]$OutDir     = '',
    [switch]$DryRun,
    [switch]$Force
)
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

[System.Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3.0

$script:SW  = [System.Diagnostics.Stopwatch]::StartNew()

function Write-Stage {
    param([string]$Tag, [string]$Msg, [ConsoleColor]$Color = 'Cyan')
    Write-Host ('[{0,6:N2}s] [{1}] {2}' -f $script:SW.Elapsed.TotalSeconds, $Tag, $Msg) -ForegroundColor $Color
}

# ── LL#34 條目本體（embedded） ────────────────────────────
$LL34_BODY = @'

---

# LL#34 — Patcher 三大教訓（AST 計數 / 污染清理 / PSObject 安全取值）

**Source case**: VIA_SSOT_PanoramicAugmenter v1 → v2
**Date logged**: 2026-05-09
**Tags**: `python-ast`, `powershell`, `code-patching`, `pollution-cleanup`

---

## LL#34a — AST-level def 計數，不要用 `^def` regex

### Trap

寫補丁工具時想知道「`def normalize` 在檔案裡有幾次」，直覺寫法是：

```python
count = len(re.findall(r'^def\s+normalize\s*\(', src, re.MULTILINE))
```

這在「乾淨檔案」上正確，但**只要源碼內含 docstring 或字串包裹的 def 定義**（例如 quarantine 後的 `_VIA_QUARANTINED = '''def normalize(...)...'''`），regex 會把字串裡的內容也算進去，計數變得毫無意義。

### Fix

用 `ast.parse` + 只走 `tree.body`（module-level）：

```python
import ast
tree = ast.parse(src)
counts = {}
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        counts[node.name] = counts.get(node.name, 0) + 1
```

`tree.body` 只看 module-level 的 def，不會深入 docstring，也不會誤抓 class methods。
若要連 class methods 也算，改用 `ast.walk(tree)`（但通常不該這樣計算重複定義）。

### Verification

對同一檔案：regex 抓到 4 個（含 docstring 內 2 個），AST `tree.body` 抓到 2 個 ✓ 正確。

---

## LL#34b — 只增不減清理污染：Quarantine docstring + Module-level Rebind

### Trap

當源碼有「歷史補丁污染」（例如外部 patch 在檔尾追加 `def normalize(value): return value` 把正規 SSOT-backed 的 `normalize` 覆寫掉），按「只增不減」原則不能直接刪除污染區，但保留它又會繼續污染。

### Fix

雙重策略：

**1. Quarantine：把污染區包成 docstring**

```python
sentinel_open  = "_VIA_QUARANTINED_VIA_FINAL_PATCH = '''\n"
sentinel_close = "\n'''  # end VIA_QUARANTINED_VIA_FINAL_PATCH\n"
src = src[:start] + sentinel_open + pollution_block + sentinel_close + src[end:]
```

代碼仍在檔案內（保留歷史證據、可一鍵還原），但 Python parser 把它當字串賦值，不再執行。

**邊角處理**：若 pollution_block 內含 `'''`，改用 `"""` 包並對內部 `"""` 做 `\"\"\"` 轉義；反之亦然。先掃描再選 quote 字符。

**2. Rebind：在 quarantine 後立刻重建 module-level 函數**

```python
_VIA_SSOT_INSTANCE = None
def get_ssot():
    global _VIA_SSOT_INSTANCE
    if _VIA_SSOT_INSTANCE is None:
        _VIA_SSOT_INSTANCE = SSOT()
    return _VIA_SSOT_INSTANCE

def normalize(raw):
    return get_ssot().normalize(raw)
# ... extract / extract_all / contains / canonical / all_canonicals
```

確保外部 `from module import normalize` 拿到的是 SSOT-backed 版本而非污染版。

### Idempotent 檢查

第二次執行偵測 `_VIA_QUARANTINED_VIA_FINAL_PATCH` 標記存在 → 直接 SKIP，不重複包裹。

### Verification

驗證的「核心測試」是 `from module import normalize; normalize('營收') == 'Revenue'`，不能只測 SSOT class API（污染只影響 module-level，不影響 class）。

---

## LL#34c — `PSObject.Properties[name]` 不能用 `| ForEach { $_.Value }` 取值

### Trap

PowerShell 7 處理 `ConvertFrom-Json` 拿到的 PSCustomObject 時，常見錯誤寫法：

```powershell
# WRONG — 屬性不存在時會炸 'The property Value cannot be found'
$cases = $t.PSObject.Properties['cases'] | ForEach-Object { $_.Value }
```

`PSObject.Properties[name]` 在屬性不存在時返回 `$null`，pipe 進 ForEach 嘗試對 `$null` 取 `.Value`，在 StrictMode 下立即 throw。

### Fix

先用 `Properties.Name -contains` 檢查存在性：

```powershell
$cases = if ($t.PSObject.Properties.Name -contains 'cases') { $t.cases } else { $null }
```

或用 `Get-Member`（較囉嗦但更正式）：

```powershell
$cases = if ($t | Get-Member -Name 'cases' -MemberType NoteProperty -EA 0) { $t.cases } else { $null }
```

### Why

`Properties.Name` 是字串陣列，`-contains` 是純查表 O(n) 但永不丟錯。`Properties[name]` 看似 indexer 實為查找，找不到就回 `$null`。

### Real bug record

VIA_SSOT_PanoramicAugmenter_v1.ps1:728 在 Phase 4 收集測試結果時掛掉，第一輪實機跑卡在這。v2 已內建修正。

---

## 三條教訓的組合應用情境

寫**任何 Python 源碼補丁工具**（PS 編排 + Python 子程序）時：

- **PS 端**收集 Python 子程序回傳的 JSON → 用 LL#34c 的 `Properties.Name -contains` 安全取值
- **Python 端**做污染偵測與計數 → 用 LL#34a 的 AST-level，不要用 regex 線性掃描
- **Python 端**遇到「不能刪只能停用」的污染區 → 用 LL#34b 的 quarantine + rebind

整套配合「只增不減」原則 + idempotent 檢查 = 任意次數重複執行都安全。
'@

# ── 偵測手冊位置 ──────────────────────────────────────────
Write-Stage 'PHASE0' '偵測 PS7 Lesson Learned 手冊位置' Yellow

$found = $null
$reason = ''

if ($ManualPath) {
    if (Test-Path -LiteralPath $ManualPath) {
        $found = (Resolve-Path -LiteralPath $ManualPath).Path
        $reason = '使用者顯式指定'
    } else {
        Write-Stage 'PHASE0' ('  ⚠ -ManualPath 指定的檔案不存在: {0}' -f $ManualPath) Red
        throw "ManualPath 不存在"
    }
}

if (-not $found) {
    # 在 OneDrive\VeritasIntelligenceAnalytics 內搜尋常見手冊命名
    $searchRoots = @(
        'C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\docs',
        'C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\OneDrive\Desktop\新增資料夾',
        $PSScriptRoot,
        (Get-Location).Path
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

    $patterns = @(
        '*Lesson*Learn*.md',
        '*LessonsLearned*.md',
        '*PS7*Handbook*.md',
        '*PS7*LL*.md',
        '*VIA*LL*.md',
        'LL_*.md',
        'LL.md'
    )

    foreach ($root in $searchRoots) {
        foreach ($pat in $patterns) {
            $hits = Get-ChildItem -LiteralPath $root -Filter $pat -File -ErrorAction SilentlyContinue
            if ($hits) {
                $found = $hits[0].FullName
                $reason = ('自動偵測命中於 {0} (pattern: {1})' -f $root, $pat)
                break
            }
        }
        if ($found) { break }
    }
}

if (-not $OutDir) {
    if ($found) {
        $OutDir = Split-Path $found -Parent
    } else {
        $OutDir = (Get-Location).Path
    }
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if ($found) {
    Write-Stage 'PHASE0' ('  ✓ 找到手冊: {0}' -f $found) Green
    Write-Stage 'PHASE0' ('    Reason: {0}' -f $reason) DarkGray
} else {
    Write-Stage 'PHASE0' '  ℹ 未找到既有手冊 — 將寫獨立 LL34 條目檔' Yellow
}

# ── 模式 A：找到手冊 → append ─────────────────────────────
if ($found) {
    $manualText = Get-Content -LiteralPath $found -Raw -Encoding UTF8

    # 重複加入保護
    if ($manualText -match 'LL\s*#\s*34' -and -not $Force) {
        Write-Stage 'PHASE1' '  ⚠ 手冊已含 "LL#34" — 跳過 (使用 -Force 可強制重新追加)' Yellow
        Write-Stage 'DONE'   ('  Manual 路徑: {0}' -f $found) DarkGray
        Write-Stage 'DONE'   ('  Total elapsed: {0:N2}s' -f $script:SW.Elapsed.TotalSeconds) Yellow
        return
    }

    # 備份
    $backup = Join-Path $OutDir ('{0}.backup_{1}.md' -f `
        [System.IO.Path]::GetFileNameWithoutExtension($found), `
        (Get-Date -Format 'yyyyMMdd_HHmmss'))
    Copy-Item -LiteralPath $found -Destination $backup -Force
    Write-Stage 'PHASE1' ('  ✓ 備份: {0}' -f $backup) Cyan

    # 顯示 diff 預覽
    Write-Stage 'PHASE2' '  Diff 預覽（前 8 行）:' Cyan
    $LL34_BODY -split "`n" | Select-Object -First 8 | ForEach-Object {
        Write-Host ('     | ' + $_) -ForegroundColor DarkGray
    }
    Write-Host '     | ...' -ForegroundColor DarkGray

    if ($DryRun) {
        Write-Stage 'PHASE2' '  ⚠ DryRun — 不實際寫入手冊' Yellow
        $previewFile = Join-Path $OutDir 'LL34_dryrun_preview.md'
        Set-Content -LiteralPath $previewFile -Value ($manualText + $LL34_BODY) -Encoding UTF8
        Write-Stage 'PHASE2' ('  預覽檔: {0}' -f $previewFile) Cyan
    } else {
        $newText = $manualText.TrimEnd("`r","`n") + "`n`n" + $LL34_BODY.TrimStart("`r","`n") + "`n"
        Set-Content -LiteralPath $found -Value $newText -Encoding UTF8 -NoNewline
        Write-Stage 'PHASE2' ('  ✓ LL#34 已追加到手冊（+{0:N0} bytes）' -f ($newText.Length - $manualText.Length)) Green
    }
}
# ── 模式 B：未找到手冊 → 寫獨立檔 ────────────────────────
else {
    $standalone = Join-Path $OutDir 'LL34_entry.md'
    if ((Test-Path $standalone) -and -not $Force) {
        Write-Stage 'PHASE1' ('  ⚠ {0} 已存在 — 跳過 (使用 -Force 可覆寫)' -f $standalone) Yellow
    } else {
        if ($DryRun) {
            Write-Stage 'PHASE1' ('  ⚠ DryRun — 將會建立: {0}' -f $standalone) Yellow
        } else {
            Set-Content -LiteralPath $standalone -Value $LL34_BODY.TrimStart("`r","`n") -Encoding UTF8
            Write-Stage 'PHASE1' ('  ✓ 獨立 LL34 條目寫入: {0}' -f $standalone) Green
        }
    }
}

Write-Stage 'DONE' '─────────────────────────────────────' Yellow
Write-Stage 'DONE' ('Total elapsed: {0:N2}s' -f $script:SW.Elapsed.TotalSeconds) Yellow


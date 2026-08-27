#Requires -Version 5.1
<#
================================================================================
  VDF_Consolidator.ps1  ·  v1.0  ·  PS5.1+ / PS7
================================================================================
  ROLE
    一鍵收斂 VDF 編號生態 22 個檔案到統一目標資料夾.
    1. 掃 3 個來源 (Downloads, OneDrive Desktop, target itself)
    2. 依「檔案大小 (主) + 修改時間 (副)」選同名最新版
    3. 自動剝除 Windows 重複後綴: " (1)", " (2)", " - Copy", "_1"
    4. 自動 rename legacy 舊命名 → 編號版 (VDF_RegistryLoader.py → VDF_MDL104_*)
    5. 移動到目標, 重複版本歸檔到 _archive/
    6. 對照 22 模組 ecosystem 列缺漏 + 額外檔案 + 個人工具

  ONE-PASTE USAGE
    1. Win+X → "Terminal" 或 "PowerShell"
    2. 整段複製 (此檔案全選) → 貼到 PowerShell (Ctrl+V) → Enter
    3. 自動執行,結束後印 Summary Matrix
================================================================================
#>

function Invoke-VDFConsolidator {

    # ─── 來源資料夾 ─────────────────────────────────────────────────────────
    $SearchRoots = @(
        'C:\Users\tonyk\Downloads',
        'C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vdf',
        'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF'
    )

    # ─── 目標資料夾 ─────────────────────────────────────────────────────────
    $TargetDir = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF'

    # ─── 執行模式 ───────────────────────────────────────────────────────────
    $Execute = $true   # $true = 真實搬移 + 歸檔 ; $false = 預覽

    # ─── 22 個 canonical 模組 ───────────────────────────────────────────────
    $Expected22 = @(
        'VDF_MDL000_README.md',
        'VDF_MDL001_TWUniverseVerify.py',
        'VDF_MDL002_YFinanceFetchingEngine.py',
        'VDF_MDL003_SentimentMacroEngine.py',
        'VDF_ENG006_MDL004TWFullMarketEngine.py',
        'VDF_MDL005_TWStockFilter.py',
        'VDF_MDL006_FinancialModel.py',
        'VDF_MDL007_SSOTResolver.py',
        'VDF_MDL101_OutputManager.py',
        'VDF_ENG011_MDL102FormatUpgrader.py',
        'VDF_MDL103_MasterRegistry.py',
        'VDF_MDL104_RegistryLoader.py',
        'VDF_MDL105_CrossValidator.py',
        'VDF_MDL201_GenerateFullRegistry.py',
        'VDF_MDL301_SystemTest.py',
        'VDF_ENG017_MDL302FinalActivation.py',
        'VDF_MDL303_RegistryActivation.py',
        'VDF_MDL401_RegistrySchema.json',
        'VDF_MDL402_RegistrySample.json',
        'VDF_MDL403_RegistryFull.json',
        'VDF_MDL404_CoverageReport.json',
        'VDF_MDL501_DataModuleController.html'
    )

    # ─── Legacy 舊命名 → 編號版對應 ────────────────────────────────────────
    $LegacyMap = @{
        'VDF_OutputManager.py'                  = 'VDF_MDL101_OutputManager.py'
        'VDF_FormatUpgrader.py'                 = 'VDF_ENG011_MDL102FormatUpgrader.py'
        'VDF_MasterRegistry.py'                 = 'VDF_MDL103_MasterRegistry.py'
        'VDF_RegistryLoader.py'                 = 'VDF_MDL104_RegistryLoader.py'
        'VDF_CrossValidator.py'                 = 'VDF_MDL105_CrossValidator.py'
        'generate_full_registry.py'             = 'VDF_MDL201_GenerateFullRegistry.py'
        'VDF_SystemTestSuite.py'                = 'VDF_MDL301_SystemTest.py'
        'VDF_FinalActivationTest.py'            = 'VDF_ENG017_MDL302FinalActivation.py'
        'VDF_RegistryActivationTest.py'         = 'VDF_MDL303_RegistryActivation.py'
        'vdf_registry_schema.json'              = 'VDF_MDL401_RegistrySchema.json'
        'vdf_extraction_registry.sample.json'   = 'VDF_MDL402_RegistrySample.json'
        'vdf_extraction_registry.full.json'     = 'VDF_MDL403_RegistryFull.json'
        'vdf_registry_coverage_report.json'     = 'VDF_MDL404_CoverageReport.json'
        'VIA_DataModule_Controller_v2.html'     = 'VDF_MDL501_DataModuleController.html'
        'VIA_DataModule_Controller.html'        = 'VDF_MDL501_DataModuleController.html'
        'VDF_ENG031_MDL001TWUniverseVerify.py'       = 'VDF_MDL001_TWUniverseVerify.py'
    }

    # ─── Helper Functions ──────────────────────────────────────────────────
    function Resolve-CanonicalName {
        param([string]$FileName, [hashtable]$Map)
        if ($Map.ContainsKey($FileName)) { return $Map[$FileName] }
        $clean = $FileName -replace '\s*\(\d+\)(\.[^.]+)$', '$1'
        $clean = $clean -replace '\s*-\s*Copy(\s*\(\d+\))?(\.[^.]+)$', '$2'
        if ($clean -notmatch 'MDL\d{3,4}_') {
            $clean = $clean -replace '_(\d+)(\.[^.]+)$', '$2'
        }
        if ($Map.ContainsKey($clean)) { return $Map[$clean] }
        return $clean
    }
    function Format-FileSize {
        param([int64]$Bytes)
        if ($Bytes -gt 1MB) { return ('{0:N1} MB' -f ($Bytes / 1MB)) }
        if ($Bytes -gt 1KB) { return ('{0:N1} KB' -f ($Bytes / 1KB)) }
        return ('{0} B' -f $Bytes)
    }
    function Write-Section {
        param([string]$Title, [string]$Color = 'Cyan')
        $bar = ('=' * 78)
        Write-Host ''
        Write-Host $bar -ForegroundColor $Color
        Write-Host "  $Title" -ForegroundColor $Color
        Write-Host $bar -ForegroundColor $Color
    }

    # ═══════════════════════════════════════════════════════════════════════
    # Main Pipeline
    # ═══════════════════════════════════════════════════════════════════════
    $startTime = Get-Date

    Write-Section 'VDF Consolidator v1.0 . 編號生態收斂器' 'Magenta'
    $modeText = if ($Execute) { 'EXECUTE (will move files)' } else { 'DRY-RUN (preview only)' }
    $modeColor = if ($Execute) { 'Yellow' } else { 'Gray' }
    Write-Host "  Mode    : $modeText" -ForegroundColor $modeColor
    Write-Host "  Target  : $TargetDir"
    Write-Host '  Sources :'
    foreach ($r in $SearchRoots) { Write-Host "    . $r" }

    # ─── Phase 1: Scan ─────────────────────────────────────────────────────
    Write-Section 'Phase 1: 掃描所有來源' 'Cyan'
    $allFiles = New-Object System.Collections.ArrayList
    foreach ($root in $SearchRoots) {
        if (-not (Test-Path -LiteralPath $root)) {
            Write-Host "  [WARN] Skip (not exist): $root" -ForegroundColor Yellow
            continue
        }
        $hits = @(Get-ChildItem -LiteralPath $root -File -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -match '^(VDF_|generate_|vdf_|VIA_DataModule)' -and
                $_.Extension -match '^\.(py|json|html|md)$' -and
                $_.Name -notlike '*.crdownload'
            })
        Write-Host ("  . {0,-60} {1,4} files" -f $root, $hits.Count)
        foreach ($h in $hits) { [void]$allFiles.Add($h) }
    }
    Write-Host ("  ----------------------------------------------- Total: {0} candidates" -f $allFiles.Count) -ForegroundColor Green

    if ($allFiles.Count -eq 0) {
        Write-Host '[ERROR] No files found, abort.' -ForegroundColor Red
        return
    }

    # ─── Phase 2: Group + pick largest ─────────────────────────────────────
    Write-Section 'Phase 2: 解析 canonical name + 選最大版' 'Cyan'
    $groups = @{}
    foreach ($f in $allFiles) {
        $canon = Resolve-CanonicalName -FileName $f.Name -Map $LegacyMap
        if (-not $groups.ContainsKey($canon)) { $groups[$canon] = @() }
        $groups[$canon] += $f
    }
    $selected   = @{}
    $duplicates = New-Object System.Collections.ArrayList
    foreach ($canon in ($groups.Keys | Sort-Object)) {
        $candidates = @($groups[$canon] | Sort-Object Length, LastWriteTime -Descending)
        $winner = $candidates[0]
        $selected[$canon] = $winner
        if ($candidates.Count -gt 1) {
            foreach ($l in ($candidates | Select-Object -Skip 1)) {
                [void]$duplicates.Add(@{ Winner = $winner; Loser = $l; Canonical = $canon })
            }
            Write-Host ("  . {0,-44} [{1} candidates, kept {2}]" -f $canon, $candidates.Count, (Format-FileSize $winner.Length)) -ForegroundColor Yellow
            foreach ($c in $candidates) {
                $marker = if ($c.FullName -eq $winner.FullName) { '   [KEEP]' } else { '    [DUP]' }
                $sizeStr = Format-FileSize $c.Length
                Write-Host ("{0} {1,8} . {2:yyyy-MM-dd HH:mm} . {3}" -f $marker, $sizeStr, $c.LastWriteTime, $c.FullName) -ForegroundColor Gray
            }
        } else {
            Write-Host ("  . {0,-44} {1}" -f $canon, (Format-FileSize $winner.Length)) -ForegroundColor Green
        }
    }
    Write-Host ("  ----------------------------------------------- {0} unique, {1} dups to archive" -f $selected.Count, $duplicates.Count) -ForegroundColor Green

    # ─── Phase 3: Target + archive dirs ────────────────────────────────────
    Write-Section 'Phase 3: 確保目標 + 歸檔夾' 'Cyan'
    if (-not (Test-Path -LiteralPath $TargetDir)) {
        if ($Execute) {
            New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
            Write-Host "  [OK] Created target: $TargetDir" -ForegroundColor Green
        } else {
            Write-Host "  [DRY-RUN] Would create: $TargetDir" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [OK] Target exists: $TargetDir" -ForegroundColor Green
    }
    $ArchiveDir = Join-Path $TargetDir '_archive'
    if ($Execute -and -not (Test-Path -LiteralPath $ArchiveDir)) {
        New-Item -ItemType Directory -Path $ArchiveDir -Force | Out-Null
    }

    # ─── Phase 4: Copy winners + archive losers ────────────────────────────
    Write-Section 'Phase 4: 搬移最新版 + 歸檔重複' 'Cyan'
    $movedCount    = 0
    $skippedCount  = 0
    $archivedCount = 0
    $failedCount   = 0

    foreach ($canon in ($selected.Keys | Sort-Object)) {
        $src = $selected[$canon]
        $dst = Join-Path $TargetDir $canon
        if ($src.FullName -ieq $dst) {
            Write-Host ("  [SKIP] Already in place: {0}" -f $canon) -ForegroundColor DarkGray
            $skippedCount++
            continue
        }
        if ($Execute) {
            try {
                Copy-Item -LiteralPath $src.FullName -Destination $dst -Force -ErrorAction Stop
                Write-Host ("  [OK]   {0,-44} <- {1}" -f $canon, $src.Directory.Name) -ForegroundColor Green
                $movedCount++
            } catch {
                Write-Host ("  [FAIL] {0}: {1}" -f $canon, $_.Exception.Message) -ForegroundColor Red
                $failedCount++
            }
        } else {
            Write-Host ("  [DRY]  {0,-44} <- {1} ({2})" -f $canon, $src.FullName, (Format-FileSize $src.Length)) -ForegroundColor Yellow
            $movedCount++
        }
    }

    # Archive duplicates
    foreach ($d in $duplicates) {
        $loser = $d.Loser
        $winnerPath = Join-Path $TargetDir $d.Canonical
        if ($loser.FullName -ieq $winnerPath) { continue }
        if (-not (Test-Path -LiteralPath $loser.FullName)) { continue }
        $stamp    = $loser.LastWriteTime.ToString('yyyyMMdd_HHmmss')
        $archName = "$stamp" + '_' + $loser.Name
        $archPath = Join-Path $ArchiveDir $archName

        if ($Execute) {
            try {
                Move-Item -LiteralPath $loser.FullName -Destination $archPath -Force -ErrorAction Stop
                Write-Host ("  [ARC]  {0} -> _archive\{1}" -f $loser.Name, $archName) -ForegroundColor DarkYellow
                $archivedCount++
            } catch {
                Write-Host ("  [WARN] Archive fail {0}: {1}" -f $loser.Name, $_.Exception.Message) -ForegroundColor Yellow
            }
        } else {
            Write-Host ("  [DRY]  Would archive: {0}" -f $loser.FullName) -ForegroundColor DarkYellow
        }
    }

    # ─── Phase 5: Compare with Expected22 ──────────────────────────────────
    Write-Section 'Phase 5: 22 模組 Ecosystem 比對' 'Cyan'

    $inTarget = @()
    if (Test-Path -LiteralPath $TargetDir) {
        $inTarget = @(Get-ChildItem -LiteralPath $TargetDir -File |
                      Select-Object -ExpandProperty Name)
    }

    $present  = @($Expected22 | Where-Object { $_ -in $inTarget })
    $missing  = @($Expected22 | Where-Object { $_ -notin $inTarget })
    $extra    = @($inTarget | Where-Object {
        $_ -notin $Expected22 -and
        ($_ -match '^(VDF_|generate_|vdf_)')
    })
    $personal = @($inTarget | Where-Object {
        $_ -notmatch '^(VDF_|generate_|vdf_)' -and
        $_ -notlike '_archive*'
    })

    Write-Host ('  [+] Present : {0,2} / 22' -f $present.Count) -ForegroundColor Green
    $missingColor = if ($missing.Count -eq 0) { 'Green' } else { 'Red' }
    Write-Host ('  [-] Missing : {0,2}' -f $missing.Count) -ForegroundColor $missingColor
    $extraColor = if ($extra.Count -eq 0) { 'Green' } else { 'Yellow' }
    Write-Host ('  [!] Extra   : {0,2}  (VDF prefix but not in canonical 22)' -f $extra.Count) -ForegroundColor $extraColor
    Write-Host ('  [#] Personal: {0,2}  (your own non-VDF files)' -f $personal.Count) -ForegroundColor Cyan

    if ($missing.Count -gt 0) {
        Write-Host ''
        Write-Host '  MISSING (需補):' -ForegroundColor Red
        $missing | ForEach-Object { Write-Host "     . $_" -ForegroundColor Red }
    }
    if ($extra.Count -gt 0) {
        Write-Host ''
        Write-Host '  EXTRA (legacy 殘留, 建議手動清除):' -ForegroundColor Yellow
        $extra | ForEach-Object { Write-Host "     . $_" -ForegroundColor Yellow }
    }
    if ($personal.Count -gt 0) {
        Write-Host ''
        Write-Host '  PERSONAL (你的工具檔, 保留):' -ForegroundColor Cyan
        $personal | ForEach-Object { Write-Host "     . $_" -ForegroundColor Cyan }
    }

    # ─── Final Summary ─────────────────────────────────────────────────────
    $elapsed = (Get-Date) - $startTime
    Write-Section '最終總覽' 'Magenta'
    Write-Host ('  Sources scanned : {0}' -f $SearchRoots.Count)
    Write-Host ('  Files found     : {0}' -f $allFiles.Count)
    Write-Host ('  Unique modules  : {0}' -f $selected.Count)
    Write-Host ('  Moved to target : {0} (skipped {1} already-in-place, failed {2})' -f $movedCount, $skippedCount, $failedCount)
    Write-Host ('  Archived dups   : {0}' -f $archivedCount)
    Write-Host ('  Elapsed         : {0:N2}s' -f $elapsed.TotalSeconds)
    Write-Host ''

    if ($missing.Count -eq 0 -and $extra.Count -eq 0) {
        Write-Host '  [SUCCESS] VDF 編號生態 22 個檔案完整無誤' -ForegroundColor Green
    } elseif ($missing.Count -gt 0) {
        Write-Host ('  [WARN] 尚缺 {0} 個檔案, 請從 Claude 對話下載補上' -f $missing.Count) -ForegroundColor Yellow
    } else {
        Write-Host '  [INFO] 有 extra/legacy 檔案需手動檢視' -ForegroundColor Yellow
    }
    Write-Host ''
}

# ═══════════════════════════════════════════════════════════════════════════
# Auto-run on paste/execute
# ═══════════════════════════════════════════════════════════════════════════
Invoke-VDFConsolidator

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

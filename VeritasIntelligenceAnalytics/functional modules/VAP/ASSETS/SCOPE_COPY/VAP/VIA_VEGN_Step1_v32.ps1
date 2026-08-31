#requires -Version 7
<#
================================================================================
VIA_VEGN_Step1_v32.ps1
VeritasIntelligenceAnalytics Environment Governance Nexus (VEGN)
VERITAS INTELLIGENCE SYSTEM · Step 1 v3.2
--------------------------------------------------------------------------------
執行：powershell -ExecutionPolicy Bypass -File ".\VIA_VEGN_Step1_v32.ps1"
--------------------------------------------------------------------------------
Phase 0  Bootstrap       工具定位（uv / python / pip）
Phase 1  BaseGuardian    Base 污染偵測 + 追蹤 + 分流計畫（唯讀，不自動修改）
Phase 2  EnvScan         via_* 環境健康審計
Phase 3  LibScan         全景掃描專案 imports
Phase 4  Classify        5D 分類
Phase 5  GapMap          缺口分析
Phase 6  ConflictScan    依賴衝突沙盒（uv pip compile）
Phase 7  PolicyPlan      環境政策 + 安裝計劃矩陣
Phase 8  PromptGen       AI 安裝 Prompt 生成
Phase 9  Export          HTML / JSON / CSV / freeze / AI prompt
================================================================================
#>


    param([string]$Msg,[string]$Lv='INFO',[string]$Ph='MAIN')
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

Set-StrictMode -Off
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ProgressPreference = 'SilentlyContinue'
# ── CONFIG ────────────────────────────────────────────────────────────────────
$CONFIG = [ordered]@{
    SystemName      = 'VeritasIntelligenceAnalytics Environment Governance Nexus (VEGN)'
    SystemSubtitle  = 'VERITAS INTELLIGENCE SYSTEM Step 1 v3.2 · 環境健康掃描 → 5D 分類 → 政策計畫 → AI Prompt'
    EnableAutoRepair        = $false   # true = 自動修復環境（謹慎）
    EnableAutoRebuild       = $false   # true = 自動重建損壞環境
    EnableAutoBaseClean     = $false   # true = 自動移除 Base 污染套件
    EnableHtmlAutoOpen      = $true
    EnablePipCheck          = $true
    EnableImportSmokeTest   = $true
    EnableDependencyFreeze  = $true
    EnableVerboseConsole    = $true
    EnvRoot    = 'C:\Users\tonyk\envs'
    BaseRootA  = 'C:\Users\tonyk\OneDrive\Pictures\VeritasIntelligenceAnalytics'
    BaseRootB  = 'C:\VeritasIntelligenceAnalytics'
    VEGNRoot   = 'C:\Users\tonyk\OneDrive\Pictures\VeritasIntelligenceAnalytics\module\VCNC\VEGN'
    OutputRoot = 'C:\Users\tonyk\envs\_EnvArchitect_Reports\VEGN_Step1_v3_2'
    HtmlFileName      = 'vegn_step1_report.html'
    JsonFileName      = 'vegn_step1_report.json'
    CsvFileName       = 'vegn_step1_env_matrix.csv'
    LogFileName       = 'vegn_step1_console.log'
    PolicyFileName    = 'vegn_step1_policy_plan.json'
    AiPromptFileName  = 'vegn_step1_ai_prompt.txt'
    PollutionLogName  = 'base_pollution_log.json'
    BaseStdFileName   = 'base_standard.json'
    MaxProjectFiles   = 500000
    PreferredPy       = '3.12'
    IncludeFileExt = @('.py','.ps1','.psm1','.psd1','.json','.yaml','.yml','.toml','.txt','.md','.html','.js','.ts','.css','.csv','.ini','.cfg')
    ExcludePathTokens = @(
        '\\.git\\','\\node_modules\\','\\dist\\','\\build\\','\\__pycache__\\',
        '\\.pytest_cache\\','\\.mypy_cache\\','\\site-packages\\','\\.venv\\',
        '\\venv\\','\\envs\\_EnvArchitect_Reports\\','\\envs\\_dependency_graphs\\',
        '\\envs\\_reports\\','\\envs\\_knowledge\\','\\_panorama_output\\','\\OUTPUT\\'
    )
    # Base Standard — 哪些套件 Base 可以有，哪些必須在 via_* 裡
    BaseAllowed = @('pip','setuptools','wheel','pip-tools','pipdeptree','packaging','uv')
    BaseForbiddenPy = @(
        'numpy','pandas','torch','tensorflow','scrapy','opencv-python','opencv-contrib-python',
        'transformers','matplotlib','seaborn','jupyter','ipykernel','scipy','sklearn',
        'scikit-learn','lightgbm','xgboost','fastapi','uvicorn','playwright','selenium',
        'requests','aiohttp','pdfplumber','pymupdf','cairosvg','weasyprint','spacy',
        'rembg','onnxruntime','paddleocr','paddlepaddle','jieba','polars','duckdb'
    )
    BaseForbiddenPS = @('PSScriptAnalyzer','Pester','PSRule','powershell-yaml','powershell-json')
    # via_* 路由表（套件 → 目標環境）
    ViaRouteMap = [ordered]@{
        # MATRIX / DATA
        'numpy'          = 'via_core'; 'pandas'       = 'via_core'; 'polars'      = 'via_core'
        'duckdb'         = 'via_core'; 'pyarrow'      = 'via_core'; 'scipy'       = 'via_core'
        # SCRAPE / HTTP
        'requests'       = 'via_core'; 'httpx'        = 'via_core'; 'aiohttp'     = 'via_core'
        'scrapy'         = 'via_core'; 'beautifulsoup4'='via_core'; 'lxml'        = 'via_core'
        # BROWSER
        'playwright'     = 'via_browser'; 'selenium'  = 'via_browser'
        # RENDER
        'weasyprint'     = 'via_render';  'cairosvg'  = 'via_render'
        'reportlab'      = 'via_render';  'img2pdf'   = 'via_render'
        # AI / IMAGE
        'opencv-python'  = 'via_ai_bg'; 'rembg'      = 'via_ai_bg'
        'onnxruntime'    = 'via_ai_bg'; 'pillow'     = 'via_ai_bg'
        # ML
        'torch'          = 'via_core_ml'; 'tensorflow'= 'via_core_ml'
        'transformers'   = 'via_core_ml'; 'scikit-learn'='via_core_ml'
        'xgboost'        = 'via_core_ml'; 'lightgbm'  = 'via_core_ml'
        # OCR
        'paddleocr'      = 'via_ocr_surya'; 'surya'   = 'via_ocr_surya'
        'ocrmypdf'       = 'via_core'
        # NLP
        'spacy'          = 'via_core'; 'jieba'       = 'via_core'
        # VIS / NB
        'matplotlib'     = 'via_core'; 'seaborn'     = 'via_core'
        'jupyter'        = 'via_core'; 'ipykernel'   = 'via_core'
        # PDF
        'pdfplumber'     = 'via_core'; 'pymupdf'     = 'via_core'
    }
    # Risk 分類（小寫）
    RiskHighLibs = @(
        'torch','torchvision','torchaudio','paddleocr','paddlepaddle','tensorflow',
        'jax','jaxlib','onnxruntime-gpu','faiss-gpu','cupy','cuda-python',
        'triton','deepspeed','xformers','flash-attn','surya'
    )
    RiskMidLibs = @(
        'opencv-python','opencv-contrib-python','opencv-python-headless','transformers',
        'sentence-transformers','spacy','llama-cpp-python','pymupdf','pdfplumber',
        'camelot-py','tabula-py','fastapi','uvicorn','gradio','streamlit','playwright',
        'weasyprint','cairosvg','rembg','onnxruntime','scikit-learn','lightgbm','xgboost'
    )
    RiskLowLibs = @(
        'pandas','numpy','polars','duckdb','requests','rich','openpyxl',
        'pyarrow','python-dateutil','tqdm','jinja2','orjson','ujson','jieba','regex'
    )
    EnvPackagePolicy = [ordered]@{
        via_core      = @('pandas','numpy','polars','duckdb','requests','rich','openpyxl','pyarrow','python-dateutil','tqdm','orjson','jinja2','yfinance','akshare','loguru','pyyaml','httpx','beautifulsoup4','lxml')
        via_governance= @('pip','pip-tools','pipdeptree','packaging','uv','rich','pyyaml')
        via_browser   = @('playwright','selenium')
        via_render    = @('weasyprint','cairosvg','reportlab','img2pdf')
        via_ai_bg     = @('opencv-python','rembg','onnxruntime','pillow','imageio')
        via_core_ml   = @('torch','transformers','scikit-learn','lightgbm','xgboost','pandas','numpy','joblib')
        via_ocr_surya = @('surya','paddleocr','paddlepaddle','pymupdf','pdfplumber')
    }
}
# ── RUN CONTEXT ───────────────────────────────────────────────────────────────
$RUN_ID          = Get-Date -Format 'yyyyMMdd_HHmmss'
$RUN_DIR         = Join-Path $CONFIG.OutputRoot $RUN_ID
$JSON_PATH       = Join-Path $RUN_DIR $CONFIG.JsonFileName
$CSV_PATH        = Join-Path $RUN_DIR $CONFIG.CsvFileName
$HTML_PATH       = Join-Path $RUN_DIR $CONFIG.HtmlFileName
$LOG_PATH        = Join-Path $RUN_DIR $CONFIG.LogFileName
$POLICY_PATH     = Join-Path $RUN_DIR $CONFIG.PolicyFileName
$AI_PROMPT_PATH  = Join-Path $RUN_DIR $CONFIG.AiPromptFileName
$POLL_LOG_PATH   = Join-Path $RUN_DIR $CONFIG.PollutionLogName
$BASE_STD_PATH   = Join-Path $RUN_DIR $CONFIG.BaseStdFileName
$FREEZE_DIR      = Join-Path $RUN_DIR 'freezes'
New-Item -ItemType Directory -Force -Path $RUN_DIR,$FREEZE_DIR | Out-Null
# ── STATE ─────────────────────────────────────────────────────────────────────
$script:ST = [ordered]@{
    StartedAt            = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    FilesScanned         = 0
    PythonFilesScanned   = 0
    CandidateEnvCount    = 0
    HealthyEnvCount      = 0
    RiskEnvCount         = 0
    RepairedEnvCount     = 0
    RebuiltEnvCount      = 0
    FailedEnvCount       = 0
    UniqueProjectImports = 0
    UniqueHealthyImports = 0
    NewCandidateImports  = 0
    ReadErrors           = 0
    BasePollutedCount    = 0
    BaseCleanedCount     = 0
    ConflictEnvCount     = 0
    Actions              = [System.Collections.Generic.List[object]]::new()
    PollutionEvents      = [System.Collections.Generic.List[object]]::new()
    BaseGuardResult      = $null
}
# ── LOGGING ───────────────────────────────────────────────────────────────────
function WL {
    $line = '[{0}][{1}][{2}] {3}' -f (Get-Date -Format 'HH:mm:ss.fff'),$Lv.ToUpper(),$Ph,$Msg
    if ($CONFIG.EnableVerboseConsole) {
        $c = switch ($Lv.ToUpper()) {
            'OK'   {'Green'} 'WARN' {'Yellow'} 'ERR' {'Red'} 'STEP' {'Cyan'} default {'Gray'}
        }
        Write-Host $line -ForegroundColor $c
    }
    Add-Content $LOG_PATH $line -Encoding UTF8 -EA SilentlyContinue
}
function SP { param([int]$p,[string]$l) WL "[$p%] $l" 'STEP' 'PHASE' }

# ── UTILS ─────────────────────────────────────────────────────────────────────
function RunProc {
    param([string]$Exe,[string[]]$Args=@(),[int]$To=300)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName=$Exe; $psi.UseShellExecute=$false
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    $psi.CreateNoWindow=$true
    foreach ($a in $Args) { [void]$psi.ArgumentList.Add($a) }
    $p = [System.Diagnostics.Process]::new(); $p.StartInfo=$psi; [void]$p.Start()
    if (-not $p.WaitForExit($To*1000)) { try{$p.Kill($true)}catch{}; return [PSCustomObject]@{ExitCode=99;StdOut='';StdErr='TIMEOUT'} }
    return [PSCustomObject]@{ExitCode=$p.ExitCode;StdOut=$p.StandardOutput.ReadToEnd();StdErr=$p.StandardError.ReadToEnd()}
}

function GetPy { param([string]$EnvName)
    $p = Join-Path $CONFIG.EnvRoot ($EnvName+'\Scripts\python.exe')
    if (Test-Path $p) { return $p }; return $null
}
function GetPip { param([string]$EnvName)
    $p = Join-Path $CONFIG.EnvRoot ($EnvName+'\Scripts\pip.exe')
    if (Test-Path $p) { return $p }; return $null
}
function GetUv {
    foreach ($c in @((Get-Command uv -EA SilentlyContinue | Select-Object -ExpandProperty Source -EA SilentlyContinue),
        "$env:USERPROFILE\scoop\shims\uv.exe","$env:USERPROFILE\.cargo\bin\uv.exe",
        "$env:LOCALAPPDATA\Programs\uv\uv.exe")) {
        if ($c -and (Test-Path $c -EA SilentlyContinue)) { return $c }
    }; return $null
}
function PathOK { param([string]$P)
    foreach ($t in $CONFIG.ExcludePathTokens) { if ($P -match $t) { return $false } }; return $true
}

# ── PHASE 0: Bootstrap ────────────────────────────────────────────────────────
function Phase0-Bootstrap {
    SP 2 'Phase 0: Bootstrap'
    $script:UvExe = GetUv
    $script:BasePy = ''
    foreach ($c in @((Get-Command python -EA SilentlyContinue | Select-Object -ExpandProperty Source -EA SilentlyContinue),
        "$($CONFIG.EnvRoot)\via_core\Scripts\python.exe")) {
        if ($c -and (Test-Path $c -EA SilentlyContinue)) { $script:BasePy = $c; break }
    }
    WL "uv     = $($script:UvExe)" 'OK' 'BOOT'
    WL "Python = $($script:BasePy)" 'OK' 'BOOT'

    # 產生 base_standard.json
    $std = [ordered]@{
        metadata    = @{ description="VIA Base Governance Standard v3.2"; generated=$RUN_ID }
        allowed     = @{ python=$CONFIG.BaseAllowed; system=@('git','make','uv') }
        forbidden   = @{ python=$CONFIG.BaseForbiddenPy; powershell=$CONFIG.BaseForbiddenPS; javascript=@('node','npm','react','next','vite','typescript') }
        route_map   = $CONFIG.ViaRouteMap
    }
    $stdJson = $std | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText($BASE_STD_PATH, $stdJson, [System.Text.Encoding]::UTF8)
    WL "base_standard.json → $BASE_STD_PATH" 'OK' 'BOOT'
}

# ── PHASE 1: Base Guardian ────────────────────────────────────────────────────
function Phase1-BaseGuardian {
    SP 8 'Phase 1: Base Guardian — 污染偵測/追蹤/分流計劃'
    $events = [System.Collections.Generic.List[object]]::new()

    function TrackPoll { param([string]$pkg,[string]$cmd,[string]$src,[string]$route='')
        $e = [ordered]@{
            timestamp    = (Get-Date).ToString('s')
            actor        = $env:USERNAME
            run_id       = $RUN_ID
            command      = $cmd
            source       = $src
            package      = $pkg
            routed_to    = $route
            status       = 'DETECTED'
            action_taken = if ($CONFIG.EnableAutoBaseClean) { 'CLEANED' } else { 'READ_ONLY' }
        }
        $events.Add([PSCustomObject]$e) | Out-Null
        $script:ST.PollutionEvents.Add([PSCustomObject]$e) | Out-Null
    }

    # Python base 污染偵測
    $basePy = $script:BasePy
    $pyPkgs = @()
    if ($basePy) {
        $r = RunProc -Exe $basePy -Args @('-m','pip','list','--format=json') -To 60
        if ($r.ExitCode -eq 0 -and $r.StdOut) {
            try { $pyPkgs = @($r.StdOut | ConvertFrom-Json | ForEach-Object { [PSCustomObject]@{Name=$_.name.ToLower();Version=$_.version} }) }
            catch {}
        }
    }
    $forbPyL = @($CONFIG.BaseForbiddenPy | ForEach-Object { $_.ToLower() })
    $pollPy  = @($pyPkgs | Where-Object { $forbPyL -contains $_.Name })
    $allowL  = @($CONFIG.BaseAllowed | ForEach-Object { $_.ToLower() })
    $missPy  = @($CONFIG.BaseAllowed | Where-Object { $allowL -notcontains ($_ -as [string]).ToLower() -or
                  ($pyPkgs | Where-Object { $_.Name -eq $_.ToLower() }).Count -eq 0 } |
                  Where-Object { $n=$_.ToLower(); -not ($pyPkgs | Where-Object { $_.Name -eq $n }) })

    foreach ($pkg in $pollPy) {
        $rt = if ($CONFIG.ViaRouteMap.ContainsKey($pkg.Name)) { $CONFIG.ViaRouteMap[$pkg.Name] } else { 'UNKNOWN' }
        TrackPoll $pkg.Name "pip install $($pkg.Name)" 'Python/pip' $rt
        WL "  [POLLUTED] $($pkg.Name) v$($pkg.Version) → 應在 $rt" 'WARN' 'BASE'
        $script:ST.BasePollutedCount++
        if ($CONFIG.EnableAutoBaseClean -and $basePy) {
            RunProc -Exe $basePy -Args @('-m','pip','uninstall','-y',$pkg.Name) -To 60 | Out-Null
            WL "  [CLEANED] $($pkg.Name) 已從 Base 移除" 'OK' 'BASE'
            $script:ST.BaseCleanedCount++
        }
    }

    # PowerShell 模組污染
    $psModules = @(Get-Module -ListAvailable -EA SilentlyContinue | Select-Object -ExpandProperty Name | Sort-Object -Unique)
    $pollPS    = @($psModules | Where-Object { $CONFIG.BaseForbiddenPS -contains $_ })
    foreach ($mod in $pollPS) {
        TrackPoll $mod "Install-Module $mod" 'PowerShell' 'via_governance'
        WL "  [POLLUTED-PS] $mod" 'WARN' 'BASE'
    }

    # Node 檢查
    $nodeCmd = Get-Command node -EA SilentlyContinue
    if ($nodeCmd) { WL "  [WARN] Node.js detected in base: $($nodeCmd.Source)" 'WARN' 'BASE' }

    # 儲存 pollution log
    $eventsJson = $events | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText($POLL_LOG_PATH, $eventsJson, [System.Text.Encoding]::UTF8)

    WL "Base Guardian: 污染=$($pollPy.Count+$pollPS.Count)  已清理=$($script:ST.BaseCleanedCount)  Missing=$($missPy.Count)" `
       ($(if($pollPy.Count -gt 0){'WARN'}else{'OK'})) 'BASE'

    return [PSCustomObject]@{
        PollutedPy  = $pollPy
        PollutedPS  = $pollPS
        MissingBase = $missPy
        NodeDetected= $null -ne $nodeCmd
        Events      = $events
        AllClean    = ($pollPy.Count -eq 0 -and $pollPS.Count -eq 0)
        RouteHints  = ($pollPy | ForEach-Object {
            [PSCustomObject]@{ Pkg=$_.Name; From='base'; To=if($CONFIG.ViaRouteMap.ContainsKey($_.Name)){$CONFIG.ViaRouteMap[$_.Name]}else{'UNKNOWN'} }
        })
    }
}

# ── PHASE 2: EnvScan ──────────────────────────────────────────────────────────
function Phase2-EnvScan {
    SP 15 'Phase 2: 環境健康審計'
    $envCode = @'
import sys,os,json,subprocess
ENV_ROOT=sys.argv[1]; ENV_LIST=json.loads(sys.argv[2])
RISK_HIGH_L=json.loads(sys.argv[3]); RISK_MID_L=json.loads(sys.argv[4])
CORE_ENVS={"via_core","via_governance"}
results=[]
for env in ENV_LIST:
    name=env["Name"]; envdir=os.path.join(ENV_ROOT,name)
    pyexe=os.path.join(envdir,"Scripts","python.exe")
    r={"name":name,"role":env.get("Role","UNKNOWN"),"risk":env.get("Risk","UNKNOWN"),
       "purpose":env.get("Purpose",""),"exists":os.path.exists(envdir),
       "python_ok":False,"py_version":"","pip_check_ok":False,"pkg_count":0,
       "pkg_names":[],"packages":[],"health":"MISSING","polluted":False,
       "conflict":False,"pip_note":"","accept_risk":env.get("AcceptRisk",[])}
    if not os.path.exists(pyexe): results.append(r); continue
    try:
        v=subprocess.run([pyexe,"--version"],capture_output=True,text=True,timeout=15)
        r["py_version"]=(v.stdout+v.stderr).strip(); r["python_ok"]=True
    except: pass
    try:
        pc=subprocess.run([pyexe,"-m","pip","check"],capture_output=True,text=True,timeout=90)
        r["pip_check_ok"]=pc.returncode==0; r["pip_note"]=(pc.stdout+pc.stderr).strip()[:300]
    except: pass
    try:
        pl=subprocess.run([pyexe,"-m","pip","list","--format=json"],capture_output=True,text=True,timeout=90)
        if pl.returncode==0 and pl.stdout.strip():
            pkgs=json.loads(pl.stdout)
            r["packages"]=[{"n":p["name"].lower(),"v":p["version"]} for p in pkgs]
            r["pkg_names"]=[p["name"].lower() for p in pkgs]; r["pkg_count"]=len(pkgs)
    except: pass
    if name in CORE_ENVS:
        for rk in RISK_HIGH_L:
            if rk in r["pkg_names"]: r["polluted"]=True; break
    if r["pip_note"] and ("conflict" in r["pip_note"].lower() or "incompatible" in r["pip_note"].lower()):
        r["conflict"]=True
    if r["pip_check_ok"] and not r["polluted"] and not r["conflict"] and r["pkg_count"]>0:
        r["health"]="OK"
    elif r["pkg_count"]>0: r["health"]="DEGRADED"
    elif r["python_ok"]:   r["health"]="EMPTY"
    results.append(r)
print(json.dumps(results,ensure_ascii=False))
'@
    # 偵測現有 + 預期環境
    $existEnvs = @(Get-ChildItem $CONFIG.EnvRoot -Directory -EA SilentlyContinue |
                   Where-Object { $_.Name -match '^via_' } |
                   Select-Object -ExpandProperty Name | Sort-Object)

    $knownDefs = @(
        @{Name='via_core';      Role='CORE';    Risk='LOW';    Purpose='核心資料/分析/財務'; AcceptRisk=@('LOW')}
        @{Name='via_governance';Role='GOV';     Risk='LOW';    Purpose='治理/盤點/鎖版';    AcceptRisk=@('LOW')}
        @{Name='via_browser';   Role='BROWSER'; Risk='HIGH';   Purpose='瀏覽器自動化';      AcceptRisk=@('MEDIUM','HIGH')}
        @{Name='via_render';    Role='RENDER';  Risk='HIGH';   Purpose='SVG/HTML/PDF渲染';  AcceptRisk=@('MEDIUM','HIGH')}
        @{Name='via_ai_bg';     Role='AI_BG';   Risk='HIGH';   Purpose='AI去背/OpenCV';     AcceptRisk=@('MEDIUM','HIGH')}
        @{Name='via_core_ml';   Role='ML';      Risk='HIGH';   Purpose='PyTorch/transformers';AcceptRisk=@('HIGH')}
        @{Name='via_ocr_surya'; Role='OCR';     Risk='CRITICAL';Purpose='surya OCR 隔離';  AcceptRisk=@('CRITICAL')}
    )
    $knownNames = @($knownDefs | ForEach-Object { $_['Name'] })
    $allNames   = ($knownNames + $existEnvs) | Select-Object -Unique
    $envList    = @($allNames | ForEach-Object {
        $n=$_; $def=$knownDefs | Where-Object { $_['Name'] -eq $n } | Select-Object -First 1
        if ($def) { $def } else { @{Name=$n;Role='UNKNOWN';Risk='UNKNOWN';Purpose='Auto-detected';AcceptRisk=@('LOW','MEDIUM','HIGH')} }
    })

    $tmpList = Join-Path $RUN_DIR '_env_list.json'
    [System.IO.File]::WriteAllText($tmpList,($envList|ConvertTo-Json -Depth 4 -Compress),[System.Text.Encoding]::UTF8)
    $highJ = ($CONFIG.RiskHighLibs | ForEach-Object { $_.ToLower() }) | ConvertTo-Json -Compress
    $midJ  = ($CONFIG.RiskMidLibs  | ForEach-Object { $_.ToLower() }) | ConvertTo-Json -Compress

    $tmpPy = Join-Path $RUN_DIR '_env_scan.py'
    [System.IO.File]::WriteAllText($tmpPy, $envCode, [System.Text.Encoding]::UTF8)
    $r = RunProc -Exe $script:BasePy -Args @($tmpPy,$CONFIG.EnvRoot,(Get-Content $tmpList -Raw),$highJ,$midJ) -To 300
    Remove-Item $tmpPy,$tmpList -Force -EA SilentlyContinue
    $jl = @($r.StdOut -split "`n" | Where-Object { $_ -match '^\[' }) | Select-Object -Last 1
    if (-not $jl) { WL "EnvScan 失敗" 'WARN' 'ENV'; return @() }
    $res = @($jl | ConvertFrom-Json)
    $ok  = @($res | Where-Object { $_.health -eq 'OK' }).Count
    $script:ST.CandidateEnvCount = $res.Count
    $script:ST.HealthyEnvCount   = $ok
    $script:ST.RiskEnvCount      = $res.Count - $ok
    WL "EnvScan: $($res.Count) 環境  OK=$ok  非OK=$($res.Count - $ok)" ($(if($ok -eq $res.Count){'OK'}else{'WARN'})) 'ENV'
    return $res
}

# ── PHASE 3-4: LibScan + Classify ────────────────────────────────────────────
function Phase34-LibScanClassify { param([string[]]$Targets)
    SP 30 'Phase 3-4: 全景掃描 + 5D 分類'
    $scanCode = @'
import sys,os,re,json,ast,hashlib
VIA_BASE=sys.argv[1]; OUT=sys.argv[2]; SCAN_DIRS=json.loads(open(sys.argv[3],encoding="utf-8").read())
PKG_SPEC_RE=re.compile(r'["\']([a-zA-Z][a-zA-Z0-9\-_]+(?:>=|<=|==|~=|!=|<|>)[^"\';\s]{1,80})["\']')
PKG_NAME_RE=re.compile(r'^([a-zA-Z][a-zA-Z0-9\-_]+)',re.IGNORECASE)
IMPORT_RE=re.compile(r'^\s*(?:import|from)\s+([a-zA-Z][a-zA-Z0-9_]+)',re.MULTILINE)
PIP_RE=re.compile(r'(?:pip|pip3|uv\s+pip)\s+install\s+([^\n#]{2,120})',re.IGNORECASE)
HEREDOC_RE=re.compile(r"@'\s*\n(.*?)\n'@",re.DOTALL)
STDLIB={"os","sys","re","io","abc","ast","csv","gc","hmac","http","json","math","copy","enum",
"glob","gzip","stat","time","uuid","xml","dis","email","functools","hashlib","inspect",
"itertools","logging","pathlib","pickle","platform","pprint","queue","random","select",
"shutil","signal","socket","sqlite3","string","struct","subprocess","tempfile","textwrap",
"threading","traceback","types","typing","unittest","urllib","warnings","weakref","zipfile",
"zlib","collections","contextlib","dataclasses","datetime","decimal","difflib","fractions",
"html","importlib","numbers","operator","argparse","runpy","secrets","sysconfig","token",
"tokenize","configparser","codecs","base64","binascii","getpass","asyncio","concurrent",
"heapq","multiprocessing","array","bisect","pdb","timeit","cProfile","site","builtins",
"_thread","__future__","atexit","errno","fnmatch","marshal","mmap","selectors","statistics",
"unicodedata","ctypes"}
SCAN_EXTS={".py",".ps1",".psm1",".txt",".toml",".yml",".yaml",".json",".cfg"}
specs={}; imports={}; file_idx=[]; conflicts=[]
def norm(n): return n.lower().replace("_","-").replace(".","")
for scan_item in SCAN_DIRS:
    items=[]
    if os.path.isfile(scan_item): items=[scan_item]
    elif os.path.isdir(scan_item):
        for root,dirs,files in os.walk(scan_item):
            dirs[:]=[d for d in dirs if not d.startswith(".") and d not in{"__pycache__",".git","node_modules",".venv","venv"}]
            for f in files: items.append(os.path.join(root,f))
    for fp in items:
        ext=os.path.splitext(fp)[1].lower()
        if ext not in SCAN_EXTS: continue
        try: src=open(fp,encoding="utf-8",errors="replace").read()
        except: continue
        ls={}; li=set()
        for m in PKG_SPEC_RE.finditer(src):
            s=m.group(1); nm=PKG_NAME_RE.match(s)
            if nm:
                k=norm(nm.group(1))
                if k not in ls: ls[k]=s
        if ext in(".ps1",".psm1"):
            for m in PIP_RE.finditer(src):
                for pt in re.split(r'[\s,@"\']+',m.group(1)):
                    pt=pt.strip('"\'\\'); nm2=PKG_NAME_RE.match(pt)
                    if nm2:
                        k=norm(nm2.group(1))
                        if k not in ls and len(pt)>2: ls[k]=pt
            for blk in HEREDOC_RE.findall(src):
                try:
                    tr=ast.parse(blk)
                    for nd in ast.walk(tr):
                        if isinstance(nd,ast.Import):
                            for a in nd.names: li.add(a.name.split(".")[0])
                        elif isinstance(nd,ast.ImportFrom):
                            if nd.module: li.add(nd.module.split(".")[0])
                except:
                    for im in IMPORT_RE.findall(blk): li.add(im)
        elif ext==".py":
            try:
                tr=ast.parse(src)
                for nd in ast.walk(tr):
                    if isinstance(nd,ast.Import):
                        for a in nd.names: li.add(a.name.split(".")[0])
                    elif isinstance(nd,ast.ImportFrom):
                        if nd.module: li.add(nd.module.split(".")[0])
            except:
                for im in IMPORT_RE.findall(src): li.add(im)
        elif ext in(".txt",".cfg",".toml"):
            for line in src.split("\n"):
                line=line.strip()
                if not line or line.startswith("#") or line.startswith("-"): continue
                nm2=PKG_NAME_RE.match(line)
                if nm2:
                    k=norm(nm2.group(1))
                    sm=re.match(r"([a-zA-Z][a-zA-Z0-9\-_]+)(.+)",line)
                    if sm and sm.group(2).strip(): ls[k]=line.strip()
                    elif k not in ls: ls[k]=nm2.group(1)
        rel=os.path.relpath(fp,VIA_BASE) if VIA_BASE and fp.startswith(VIA_BASE) else fp
        for k,s in ls.items():
            if k in specs:
                if specs[k]["spec"]!=s and ">=" in s and ">=" in specs[k]["spec"]:
                    conflicts.append({"pkg":k,"spec_a":specs[k]["spec"],"spec_b":s,"file_a":specs[k]["file"],"file_b":rel})
            else: specs[k]={"spec":s,"file":rel}
        for im in li:
            clean=im.split(".")[0].strip()
            if not clean or clean in STDLIB: continue
            k=norm(clean)
            if k not in imports: imports[k]={"name":clean,"files":[]}
            if rel not in imports[k]["files"]: imports[k]["files"].append(rel)
        file_idx.append({"rel":rel,"ext":ext})
all_names=set(specs.keys())|set(imports.keys())
combined=[]
for k in sorted(all_names):
    s=specs.get(k,{}).get("spec",k); nm=PKG_NAME_RE.match(s)
    tid=hashlib.md5(k.encode()).hexdigest()[:8].upper()
    combined.append({"tool_id":tid,"name":nm.group(1) if nm else k,"norm":k,"spec":s,
        "has_spec":k in specs,"has_import":k in imports,"spec_file":specs.get(k,{}).get("file","")})
result={"total_files":len(file_idx),"total_libs":len(combined),"conflicts":conflicts,"libs":combined}
with open(OUT,"w",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False)
print(json.dumps({"ok":True,"total_files":len(file_idx),"total_libs":len(combined),"conflicts":len(conflicts)},ensure_ascii=False))
'@
    $tmpDirs   = Join-Path $RUN_DIR '_scan_dirs.json'
    $tmpResult = Join-Path $RUN_DIR '_scan_result.json'
    [System.IO.File]::WriteAllText($tmpDirs,($Targets|ConvertTo-Json -Compress),[System.Text.Encoding]::UTF8)
    $tmpPy = Join-Path $RUN_DIR '_scan.py'
    [System.IO.File]::WriteAllText($tmpPy,$scanCode,[System.Text.Encoding]::UTF8)
    $r = RunProc -Exe $script:BasePy -Args @($tmpPy,$CONFIG.BaseRootA,$tmpResult,$tmpDirs) -To 300
    Remove-Item $tmpPy,$tmpDirs -Force -EA SilentlyContinue
    $jl = @($r.StdOut -split "`n" | Where-Object { $_ -match '^\{' }) | Select-Object -Last 1
    if (-not $jl) { WL "LibScan 失敗: $($r.StdErr | Select-Object -Last 2 | Out-String)" 'ERR' 'SCAN'; return $null }
    $scan = [System.IO.File]::ReadAllText($tmpResult,[System.Text.Encoding]::UTF8) | ConvertFrom-Json
    Remove-Item $tmpResult -Force -EA SilentlyContinue
    WL "掃描: $($scan.total_files) 個檔案  $($scan.total_libs) 個唯一 lib  Spec 衝突: $(@($scan.conflicts).Count)" 'OK' 'SCAN'

    # 5D 分類
    $ClR = [ordered]@{
        OCR     =@{kw=@("paddleocr","easyocr","tesseract","pytesseract","surya","ocrmypdf");d1="FOCR";d2="ICEX";d3="RCPU";d4="DCEX"}
        PDF     =@{kw=@("pdfplumber","pymupdf","fitz","pypdf","pdfminer","pypdfium","pikepdf");d1="FPDF";d2="ICEX";d3="RCPU";d4="DCEX"}
        JAVA    =@{kw=@("jpype","tabula","jdk","jvm");d1="FJAV";d2="IJAV";d3="RCPU";d4="DJAV"}
        TABLE   =@{kw=@("camelot","img2table","excalibur");d1="FTBL";d2="INAT";d3="RCPU";d4="DNAT"}
        SCRAPE  =@{kw=@("requests","httpx","aiohttp","scrapy","urllib3","curl");d1="FSCR";d2="IPYT";d3="RLOW";d4="DPYT"}
        BROWSER =@{kw=@("playwright","selenium","pyppeteer","stealth");d1="FANT";d2="ICEX";d3="RBRW";d4="DCEX"}
        HTML    =@{kw=@("beautifulsoup4","bs4","lxml","selectolax","parsel");d1="FHTM";d2="IPYT";d3="RLOW";d4="DPYT"}
        IMAGE   =@{kw=@("pillow","pil","opencv","cv2","skimage","imageio","pyvips","rembg","wand");d1="FIMG";d2="INAT";d3="RCPU";d4="DNAT"}
        MATRIX  =@{kw=@("numpy","scipy","pandas","polars","pyarrow","duckdb","numba","numexpr");d1="FMAT";d2="ICEX";d3="RCPU";d4="DCEX"}
        ML      =@{kw=@("torch","tensorflow","sklearn","scikit","xgboost","lightgbm","transformers","onnx","jax");d1="FML";d2="ICEX";d3="RCPU";d4="DCEX"}
        NATIVE  =@{kw=@("cffi","cython","ctypes","faiss","onnxruntime","pyo3");d1="FNAT";d2="INAT";d3="RCPU";d4="DNAT"}
        SYSTEM  =@{kw=@("ghostscript","poppler","ffmpeg","img2pdf","wkhtmltopdf");d1="FSYS";d2="ISYS";d3="RCPU";d4="DSYS"}
        ASYNC   =@{kw=@("asyncio","winloop","uvloop","anyio","trio","aiofiles");d1="FASN";d2="IPYT";d3="RLOW";d4="DPYT"}
        DB      =@{kw=@("sqlalchemy","sqlite","psycopg","pymongo","redis","lmdb","pymysql");d1="FDB";d2="IPYT";d3="RLOW";d4="DPYT"}
        FINANCE =@{kw=@("yfinance","akshare","finmind","talib","pandas_ta","ccxt");d1="FFIN";d2="IPYT";d3="RLOW";d4="DPYT"}
        NLP     =@{kw=@("spacy","nltk","jieba","gensim","sentence","bert","tiktoken");d1="FNLP";d2="ICEX";d3="RCPU";d4="DCEX"}
        EXPORT  =@{kw=@("openpyxl","xlsxwriter","reportlab","fpdf","weasyprint","cairosvg");d1="FEXP";d2="IPYT";d3="RLOW";d4="DPYT"}
        CACHE   =@{kw=@("diskcache","cachetools","cachebox","joblib");d1="FCAC";d2="IPYT";d3="RLOW";d4="DPYT"}
        COMPRESS=@{kw=@("zstandard","lz4","blosc2","brotli","snappy");d1="FCMP";d2="IPYT";d3="RLOW";d4="DPYT"}
        HASH    =@{kw=@("xxhash","mmh3","cryptography","hashlib","blake3");d1="FHSH";d2="IPYT";d3="RLOW";d4="DPYT"}
    }
    $D5R = [ordered]@{
        IMGH=@("FOCR","FTBL","FMAT","FML","FNLP","FJAV","FASN")
        IMGB=@("FPDF","FIMG","FNAT","FSYS")
        IMGF=@("FSCR","FHTM","FANT","FEXP","FDB","FFIN","FGEN","FCAC","FCMP","FHSH")
    }
    function G5D { param([string]$n)
        $ln=$n.ToLower() -replace "[-_]",""
        foreach ($cl in $ClR.Keys) {
            foreach ($kw in $ClR[$cl].kw) {
                $kwn=$kw.ToLower() -replace "[-_]",""
                if ($ln -eq $kwn -or $ln.Contains($kwn) -or $kwn.Contains($ln)) {
                    return [ordered]@{D1=$ClR[$cl].d1;D2=$ClR[$cl].d2;D3=$ClR[$cl].d3;D4=$ClR[$cl].d4;CL="CL_$cl"}
                }
            }
        }
        return [ordered]@{D1="FGEN";D2="IPYT";D3="RLOW";D4="DPYT";CL="CL_PURE"}
    }
    function GD5 { param([string]$d1)
        foreach ($img in $D5R.Keys) { if ($d1 -in $D5R[$img]) { return $img } }; return "IMGF"
    }
    function GEnvTgt { param([string]$lib,[string]$d1)
        $n=$lib.ToLower()
        if ($CONFIG.ViaRouteMap.ContainsKey($n)) { return $CONFIG.ViaRouteMap[$n] }
        $m=@{FOCR='via_core';FPDF='via_core';FTBL='via_core';FML='via_core_ml';
             FNLP='via_core';FJAV='via_core';FIMG='via_ai_bg';FNAT='via_ai_bg';
             FEXP='via_render';FSYS='via_render';FANT='via_browser';FSCR='via_core';
             FHTM='via_core';FMAT='via_core';FASN='via_core';FDB='via_core';
             FFIN='via_core';FGEN='via_core';FCAC='via_core';FCMP='via_core';FHSH='via_core'}
        return if($m.ContainsKey($d1)){$m[$d1]}else{'via_core'}
    }
    $highRL = @($CONFIG.RiskHighLibs | ForEach-Object { $_.ToLower() })
    $midRL  = @($CONFIG.RiskMidLibs  | ForEach-Object { $_.ToLower() })
    $classified=@(); $gSeq=1
    foreach ($lib in $scan.libs) {
        $d=G5D $lib.name; $d5=GD5 $d.D1; $envTgt=GEnvTgt $lib.name $d.D1
        $rk=if($highRL -contains $lib.norm){'HIGH'}elseif($midRL -contains $lib.norm){'MEDIUM'}else{'NONE'}
        $bl=$CONFIG.ViaRouteMap.ContainsKey($lib.norm) -or ($highRL -contains $lib.norm) -or ($midRL -contains $lib.norm)
        $classified += [PSCustomObject]@{
            tool_id=$lib.tool_id; lib_code=("LIB-{0}-{1:D4}" -f ($d.CL -replace "CL_",""),$gSeq)
            name=$lib.name; spec=$lib.spec; spec_file=$lib.spec_file
            has_spec=$lib.has_spec; has_import=$lib.has_import
            D1=$d.D1;D2=$d.D2;D3=$d.D3;D4=$d.D4;D5=$d5;cluster=$d.CL
            env_target=$envTgt;risk=$rk;blacklisted=$bl;rule_violations=""
        }
        $gSeq++
    }
    WL "分類: $(@($classified).Count) 個 lib" 'OK' 'CLASSIFY'
    $script:ST.UniqueProjectImports = @($classified).Count
    return [PSCustomObject]@{scan=$scan;classified=$classified;conflicts=$scan.conflicts}
}

# ── PHASE 5: GapMap ───────────────────────────────────────────────────────────
function Phase5-GapMap { param([array]$Classified,[array]$EnvHealth)
    SP 50 'Phase 5: 缺口分析'
    $SKIP = [System.Collections.Generic.HashSet[string]]([string[]]@(
        "atexit","ctypes","errno","fnmatch","marshal","mmap","selectors","statistics",
        "unicodedata","cv2","talib","data","warn","urllib3","urllib","autoplot",
        "synonym-loaded","synonym_loaded","lz4","pyvips","bubble-valuation","chart-engine",
        "data-loader","design-system","engine","event-matrix","html-renderer","ta-engine",
        "vap-annotations","vap-chart-dashboard","vap-chart-heatmap","vap-chart-stack",
        "vap-chart-technical","vap-chart-twoaxis","vap-config","vap-data-adapter",
        "vap-export","vap-indicators","vap-server","vap-templates","vdf-bridge",
        "veritasaegisnexus","veritasceleritas","via-integration","via-safefix-pathregistry"
    ))
    $allP=@{}; $envP=@{}
    foreach ($env in $EnvHealth) {
        $hs=@{}
        foreach ($p in $env.pkg_names) { $hs[$p]=$true; $allP[$p]=$true }
        $envP[$env.name]=$hs
    }
    $missing=@(); $wrongEnv=@(); $riskLibs=@()
    foreach ($lib in $Classified) {
        $n=$lib.name.ToLower(); if($SKIP.Contains($n)){continue}
        $tgt=$lib.env_target
        $inAny=$allP.ContainsKey($n)
        $inTgt=$envP.ContainsKey($tgt) -and $envP[$tgt].ContainsKey($n)
        if (-not $inAny) {
            $missing += [PSCustomObject]@{tool_id=$lib.tool_id;lib_code=$lib.lib_code
                name=$lib.name;spec=$lib.spec;cluster=$lib.cluster;env_target=$tgt;risk=$lib.risk}
        } elseif (-not $inTgt) {
            $actual=($envP.Keys|Where-Object{$envP[$_].ContainsKey($n)})-join","
            $wrongEnv += [PSCustomObject]@{tool_id=$lib.tool_id;lib_code=$lib.lib_code
                name=$lib.name;spec=$lib.spec;env_target=$tgt;actual_env=$actual;risk=$lib.risk}
        }
        if ($lib.risk -in @('HIGH','MEDIUM')) {
            $iw=($envP.Keys|Where-Object{$envP[$_].ContainsKey($n)})-join","
            $riskLibs += [PSCustomObject]@{tool_id=$lib.tool_id;name=$lib.name;risk=$lib.risk
                env_target=$tgt;installed_where=$iw;installed=$inAny;correct_env=$inTgt;blacklisted=$lib.blacklisted}
        }
    }
    WL "缺口: NOT_INSTALLED=$(@($missing).Count)  WRONG_ENV=$(@($wrongEnv).Count)  Risk=$(@($riskLibs).Count)" 'OK' 'GAP'
    return [PSCustomObject]@{missing=$missing;wrong_env=$wrongEnv;risk_libs=$riskLibs}
}

# ── PHASE 6: ConflictScan — 8 工具衝突守門人 ────────────────────────────────
# 整合：uv pip compile + pipdeptree + pip check + pip-audit + pip-compile + packaging + resolvelib
function Phase6-ConflictScan { param([PSCustomObject]$Gap)
    SP 62 'Phase 6: 衝突守門人（8 工具嵌入）'
    if (-not $script:UvExe) { WL "uv 未找到，跳過衝突沙盒" 'WARN' 'CONFLICT'; return @() }

    $SKIP_PKG = @('cv2','ctypes','atexit','errno','fnmatch','mmap','selectors','statistics',
                   'unicodedata','synonym-loaded','synonym_loaded','urllib','urllib3',
                   'autoplot','data','warn','engine','vdf-bridge','veritasaegisnexus')
    $results   = @()
    $planItems = @($Gap.missing) + @($Gap.wrong_env)

    $conflictCode = @'
import sys,os,json,subprocess,shutil
REQS=sys.argv[1]; PY=sys.argv[2]; ENV=sys.argv[3]
def run(exe,args,t=120):
    try:
        r=subprocess.run([exe]+args,capture_output=True,text=True,timeout=t)
        return {"ok":r.returncode==0,"out":(r.stdout+r.stderr).strip()[:400]}
    except Exception as e:
        return {"ok":False,"out":str(e)[:200]}
checks={}
checks["pip_check"]=run(PY,["-m","pip","check"])
checks["pipdeptree"]=run(PY,["-m","pipdeptree","--warn","conflict"])
checks["pip_compile"]=run(PY,["-m","piptools","compile",REQS,"--dry-run","--quiet"],180)
try:
    from packaging.requirements import Requirement
    errs=[]
    for ln in open(REQS):
        ln=ln.strip()
        if ln and not ln.startswith("#"):
            try: Requirement(ln)
            except Exception as e: errs.append(str(e))
    checks["packaging"]={"ok":len(errs)==0,"errors":errs[:5]}
except ImportError:
    checks["packaging"]={"ok":False,"out":"packaging not installed"}
try:
    import resolvelib
    checks["resolvelib"]={"ok":True,"out":"v"+resolvelib.__version__}
except ImportError:
    checks["resolvelib"]={"ok":False,"out":"not installed"}
print(json.dumps({"env":ENV,"checks":checks},ensure_ascii=False))
'@

    foreach ($grp in ($planItems | Group-Object env_target)) {
        $envName = $grp.Name; if (-not $envName) { continue }
        $pkgs = @($grp.Group | ForEach-Object {
            $pn = ($_.spec -split "[>=<!]")[0].Trim().ToLower()
            if ($SKIP_PKG -contains $pn) { return }
            if ($pn -eq 'cv2') { return 'opencv-python>=4.9' }
            return $_.spec
        } | Where-Object { $_ } | Select-Object -Unique)
        if ($pkgs.Count -eq 0) { continue }

        $sn    = $envName -replace '[\\/:*?<>|]','_'
        $tmpIn = Join-Path $RUN_DIR "sb_${sn}.in"
        $tmpOt = Join-Path $RUN_DIR "sb_${sn}.lock"
        $tmpCk = Join-Path $RUN_DIR "sb_${sn}_ck.py"
        [System.IO.File]::WriteAllText($tmpIn, ($pkgs -join "`n"), [System.Text.Encoding]::UTF8)
        [System.IO.File]::WriteAllText($tmpCk, $conflictCode, [System.Text.Encoding]::UTF8)

        SP 65 "衝突守門人: $envName ($($pkgs.Count) pkgs)"
        $t0 = [DateTime]::Now

        # Tool 1: uv pip compile
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName=$script:UvExe; $psi.UseShellExecute=$false
        $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.CreateNoWindow=$true
        foreach ($a in @("pip","compile",$tmpIn,"-o",$tmpOt,"--python",$CONFIG.PreferredPy,"--quiet")) {
            [void]$psi.ArgumentList.Add($a)
        }
        $proc=[System.Diagnostics.Process]::new(); $proc.StartInfo=$psi; [void]$proc.Start()
        $uvOut=$proc.StandardOutput.ReadToEnd(); $uvErr=$proc.StandardError.ReadToEnd()
        $proc.WaitForExit()
        $uvSt = if ($proc.ExitCode -eq 0) { 'PASS' } else { 'FAIL' }
        $uvNote = if ($uvErr) { $uvErr.Substring(0,[Math]::Min(300,$uvErr.Length)) } else { '' }

        # Tool 2-6: pipdeptree + pip-check + pip-compile + packaging + resolvelib
        $envPy = GetPy -EnvName $envName
        $deepFails = 0
        $dRes = @{pip_check='SKIP';pipdeptree='SKIP';pip_compile='SKIP';packaging='SKIP';resolvelib='SKIP'}
        if ($envPy) {
            $rCk = RunProc -Exe $envPy -Args @($tmpCk,$tmpIn,$envPy,$envName) -To 150
            $jl  = @($rCk.StdOut -split "`n" | Where-Object { $_ -match '^\{' }) | Select-Object -Last 1
            if ($jl) {
                try {
                    $parsed = ($jl | ConvertFrom-Json).checks
                    foreach ($ck in @('pip_check','pipdeptree','pip_compile','packaging','resolvelib')) {
                        $val = $parsed.$ck
                        if ($val) {
                            $dRes[$ck] = if ($val.ok) { 'PASS' } else { 'WARN' }
                            if (-not $val.ok) { $deepFails++ }
                        }
                    }
                } catch {}
            }
        }

        $el     = [math]::Round(([DateTime]::Now - $t0).TotalSeconds, 2)
        $status = $uvSt
        $lv     = if ($status -eq 'PASS' -and $deepFails -eq 0) { 'OK' } else { 'WARN' }
        if ($status -eq 'FAIL') { $script:ST.ConflictEnvCount++ }
        WL "  $envName → uv:$status  深:$deepFails/$(@($dRes.Keys).Count) ($($el)s)" $lv 'CONFLICT'

        $results += [PSCustomObject]@{
            env_name   = $envName; pkg_count = $pkgs.Count; pkgs = ($pkgs -join "; ")
            status     = $status;  elapsed_sec = $el; uv_note = $uvNote
            pip_check  = $dRes.pip_check;  pipdeptree  = $dRes.pipdeptree
            pip_compile= $dRes.pip_compile; packaging   = $dRes.packaging
            resolvelib = $dRes.resolvelib;  deep_fails  = $deepFails
        }
        foreach ($f in @($tmpIn,$tmpOt,$tmpCk)) {
            if ($f -and (Test-Path $f -EA SilentlyContinue)) { Remove-Item $f -Force -EA SilentlyContinue }
        }
    }
    Write-Host ""
    WL "ConflictScan: $(@($results).Count) 個環境  FAIL=$($script:ST.ConflictEnvCount)" 'OK' 'CONFLICT'
    return $results
}


# ── PHASE 7: PolicyPlan ───────────────────────────────────────────────────────
function Phase7-PolicyPlan { param([array]$EnvHealth,[array]$Classified,[PSCustomObject]$Gap)
    SP 78 'Phase 7: 政策計劃'
    if (-not $Classified) { $Classified=@() }
    $envNames  = @($EnvHealth | ForEach-Object { $_.name })
    $instMap   = @{}
    foreach ($env in $EnvHealth) { foreach ($p in $env.pkg_names) { if(-not $instMap.ContainsKey($p)){$instMap[$p]=@()}; $instMap[$p]+=$env.name } }
    $highRL    = @($CONFIG.RiskHighLibs | ForEach-Object { $_.ToLower() })
    $midRL     = @($CONFIG.RiskMidLibs  | ForEach-Object { $_.ToLower() })
    $installPlan=@(); $rebuildPlan=@(); $blockedPlan=@(); $missingEnvPlan=@()
    $SKIP_PLAN = @('cv2','ctypes','atexit','errno','fnmatch','synonym-loaded','synonym_loaded','urllib3','urllib')
    foreach ($lib in $Classified) {
        $n=$lib.name.ToLower(); if($SKIP_PLAN -contains $n){continue}
        $tgt=$lib.env_target; $rk=$lib.risk
        if (($highRL -contains $n -or $midRL -contains $n) -and $tgt -in @('via_core','via_governance')) {
            $blockedPlan += [PSCustomObject]@{name=$lib.name;spec=$lib.spec;risk=$rk;env_target=$tgt;reason='黑名單套件不可進入 core/governance'}; continue
        }
        if ($tgt -notin $envNames) {
            $missingEnvPlan += [PSCustomObject]@{env_name=$tgt;trigger=$lib.name;risk=$rk;reason='目標環境不存在'}
        }
        $rt = if($CONFIG.ViaRouteMap.ContainsKey($n)){$CONFIG.ViaRouteMap[$n]}else{$tgt}
        if ($instMap.ContainsKey($n)) {
            $installPlan += [PSCustomObject]@{name=$lib.name;spec=$lib.spec;risk=$rk;env_target=$rt;status='ALREADY_PRESENT';installed_where=($instMap[$n]-join",");action='比對版本，不盲目重裝'}
        } elseif ($rk -in @('MEDIUM','HIGH','CRITICAL')) {
            $installPlan += [PSCustomObject]@{name=$lib.name;spec=$lib.spec;risk=$rk;env_target=$rt;status='PLAN_ISOLATED';installed_where='';action="安裝至隔離環境 $rt"}
        } else {
            $installPlan += [PSCustomObject]@{name=$lib.name;spec=$lib.spec;risk=$rk;env_target=$rt;status='PLAN_INSTALL';installed_where='';action='安裝至核准低風險環境'}
        }
    }
    foreach ($env in $EnvHealth) {
        if ($env.conflict -or $env.polluted) {
            $rebuildPlan += [PSCustomObject]@{env_name=$env.name;health=$env.health;
                reason=(@(if($env.conflict){'dependency_conflict'};if($env.polluted){'policy_pollution'})-join",");action='先修復/重建，再安裝'}
        }
        if ($env.health -eq 'EMPTY') {
            $rebuildPlan += [PSCustomObject]@{env_name=$env.name;health='EMPTY';reason='pip 遺失或環境損壞';action="uv venv `"$($CONFIG.EnvRoot)\$($env.name)`" --python $($CONFIG.PreferredPy)"}
        }
    }
    $allHealthy = @($EnvHealth | Where-Object { $_.health -ne 'OK' }).Count -eq 0
    WL "PolicyPlan: install=$(@($installPlan|Where-Object{$_.status -ne 'ALREADY_PRESENT'}).Count) rebuild=$(@($rebuildPlan).Count) blocked=$(@($blockedPlan).Count) missing_env=$(@($missingEnvPlan|Select-Object -Unique).Count)" 'OK' 'POLICY'
    return [PSCustomObject]@{install=$installPlan;rebuild=$rebuildPlan;blocked=$blockedPlan;
            missing_env=($missingEnvPlan|Sort-Object env_name -Unique);all_healthy=$allHealthy}
}

# ── PHASE 8: PromptGen ────────────────────────────────────────────────────────
function Phase8-PromptGen { param([PSCustomObject]$Policy,[array]$Sandbox,[array]$EnvHealth,[PSCustomObject]$BaseGuard)
    SP 90 'Phase 8: AI Prompt 生成'
    if (-not $Policy) { return '（政策計劃未生成）' }
    $spPass  = @($Sandbox | Where-Object { $_.status -eq 'PASS' }).Count
    $spTotal = @($Sandbox).Count
    $toInst  = @($Policy.install | Where-Object { $_.status -ne 'ALREADY_PRESENT' })
    $rebuild = @($Policy.rebuild)
    $missEnv = @($Policy.missing_env | Select-Object -ExpandProperty env_name -Unique)
    $polluted= if($BaseGuard){@($BaseGuard.PollutedPy)}else{@()}

    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("# VIA VEGN Step 1 v3.2 — AI 安裝計劃 Prompt")
    [void]$sb.AppendLine("# Run ID: $RUN_ID  Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm')")
    [void]$sb.AppendLine("# Sandbox: $spPass/$spTotal PASS")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("## 原則（不可違反）")
    [void]$sb.AppendLine("1. 僅對 via_* 開頭環境操作，Base 環境禁止安裝執行層套件")
    [void]$sb.AppendLine("2. 高風險套件（torch/paddle/transformers/opencv）不得混入 via_core/via_governance")
    [void]$sb.AppendLine("3. surya 必須在 via_ocr_surya 完全隔離，不與其他套件共存")
    [void]$sb.AppendLine("4. numba/ortools → MaxPy 3.12，需 via_core_312 環境")
    [void]$sb.AppendLine("5. 先輸出 patch plan，確認後再輸出 apply plan，保持可回滾")
    [void]$sb.AppendLine("")
    if ($polluted.Count -gt 0) {
        [void]$sb.AppendLine("## ⚠ Base 污染（優先處理）")
        foreach ($p in $polluted) {
            $rt=if($CONFIG.ViaRouteMap.ContainsKey($p.Name)){$CONFIG.ViaRouteMap[$p.Name]}else{'UNKNOWN'}
            [void]$sb.AppendLine("- pip uninstall -y $($p.Name)  → 然後安裝至 $rt")
        }
        [void]$sb.AppendLine("")
    }
    if ($rebuild.Count -gt 0) {
        [void]$sb.AppendLine("## 優先：修復/重建環境")
        foreach ($r in $rebuild) { [void]$sb.AppendLine("- $($r.env_name): [$($r.health)] $($r.reason) → $($r.action)") }
        [void]$sb.AppendLine("")
    }
    if ($missEnv.Count -gt 0) {
        [void]$sb.AppendLine("## 建立缺失環境")
        foreach ($env in $missEnv) { [void]$sb.AppendLine("- uv venv `"$($CONFIG.EnvRoot)\$env`" --python $($CONFIG.PreferredPy)") }
        [void]$sb.AppendLine("")
    }
    if ($toInst.Count -gt 0) {
        [void]$sb.AppendLine("## 套件安裝計劃（依環境分組）")
        foreach ($grp in ($toInst | Group-Object env_target)) {
            [void]$sb.AppendLine("### $($grp.Name)")
            foreach ($p in $grp.Group) { [void]$sb.AppendLine("- $($p.spec)  [Risk=$($p.risk)]  [$($p.status)]") }
        }
        [void]$sb.AppendLine("")
    }
    [void]$sb.AppendLine("## 系統現況")
    [void]$sb.AppendLine("- EnvRoot: $($CONFIG.EnvRoot)")
    foreach ($e in $EnvHealth) { [void]$sb.AppendLine("- $($e.name): $($e.health) (Py=$($e.py_version) Pkgs=$($e.pkg_count))") }
    return $sb.ToString()
}

# ── PHASE 9: Export ───────────────────────────────────────────────────────────
function Phase9-Export { param([array]$EnvHealth,[array]$Classified,[PSCustomObject]$Gap,[array]$Sandbox,[PSCustomObject]$Policy,[PSCustomObject]$BaseGuard,[string]$AiPrompt)
    SP 95 'Phase 9: 匯出報告'

    # Freeze
    if ($CONFIG.EnableDependencyFreeze) {
        foreach ($env in $EnvHealth) {
            if (-not $env.exists) { continue }
            $py=GetPy -EnvName $env.name; if(-not $py){continue}
            $out=Join-Path $FREEZE_DIR ($env.name+'_freeze.txt')
            $fr=RunProc -Exe $py -Args @('-m','pip','freeze') -To 120
            [System.IO.File]::WriteAllText($out,$fr.StdOut,[System.Text.Encoding]::UTF8)
        }
        WL "Freeze files → $FREEZE_DIR" 'OK' 'EXPORT'
    }

    # CSV
    $EnvHealth | Select-Object name,exists,py_version,pkg_count,health,polluted,conflict,pip_check_ok |
        Export-Csv $CSV_PATH -NoTypeInformation -Encoding UTF8
    WL "CSV → $CSV_PATH" 'OK' 'EXPORT'

    # HTML
    $escH = { param($s) [System.Web.HttpUtility]::HtmlEncode([string]($(if($null -ne $s){$s}else{""}))) }
    function Bx { param($v,[string]$cls='')
        $s=[string]($(if($v){$v}else{""})); $c=if($cls){"$cls"}elseif($s -in @('OK','PASS','True')){'ok'}elseif($s -in @('FAIL','BROKEN','MISSING','EMPTY','DEGRADED','True') -and $s -ne 'True'){'er'}elseif($s -in @('WARN','MEDIUM','DEGRADED')){'wn'}else{'na'}
        "<span class='bx $c'>$([System.Web.HttpUtility]::HtmlEncode($s))</span>"
    }
    function BxB {
        param($v)
        if ($v) { "<span class='bx er'>YES</span>" }
        else    { "<span class='bx ok'>NO</span>" }
    }

    $pollRows = if ($BaseGuard -and @($BaseGuard.PollutedPy).Count -gt 0) {
        @($BaseGuard.PollutedPy | ForEach-Object {
            $polRt = if ($CONFIG.ViaRouteMap.ContainsKey($_.Name)) { $CONFIG.ViaRouteMap[$_.Name] } else { 'UNKNOWN' }
            $polNm = [System.Web.HttpUtility]::HtmlEncode($_.Name)
            $polVr = [System.Web.HttpUtility]::HtmlEncode($_.Version)
            $polRtH = [System.Web.HttpUtility]::HtmlEncode($polRt)
            "<tr><td><b>$polNm</b></td><td>$polVr</td><td>$polRtH</td><td><span class='bx er'>BASE_POLLUTED</span></td></tr>"
        }) -join "`n"
    } else { "<tr><td colspan='4' style='color:#5a9e6f'>+ Base 無污染</td></tr>" }

    $envRows = @($EnvHealth | ForEach-Object {
        $hc = if ($_.health -eq 'OK') { 'bx ok' } elseif ($_.health -in @('DEGRADED','EMPTY')) { 'bx wn' } else { 'bx er' }
        $envNm = [System.Web.HttpUtility]::HtmlEncode($_.name)
        $envPy = if ($null -ne $_.py_version) { $_.py_version } else { '-' }
        $envPyH = [System.Web.HttpUtility]::HtmlEncode($envPy)
        $envPc = if ($null -ne $_.pkg_count) { $_.pkg_count } else { 0 }
        $envHl = $_.health
        $envBp = BxB $_.polluted
        $envBc = BxB $_.conflict
        $envBk = BxB $_.pip_check_ok
        $envPn = if ($null -ne $_.pip_note) { $_.pip_note } else { '' }
        $envPnL = [Math]::Min(80, $envPn.Length)
        $envPnS = $envPn.Substring(0, $envPnL)
        $envPnH = [System.Web.HttpUtility]::HtmlEncode($envPnS)
        "<tr><td><b>$envNm</b></td><td style='font:9px var(--mo)'>$envPyH</td><td>$envPc</td><td><span class='$hc'>$envHl</span></td><td>$envBp</td><td>$envBc</td><td>$envBk</td><td style='font:8px var(--mo);max-width:200px;overflow:hidden;text-overflow:ellipsis'>$envPnH</td></tr>"
    }) -join "`n"

    $libRows = @($Classified | Select-Object -First 300 | ForEach-Object {
        $rk = if ($_.risk -eq 'HIGH') { 'er' } elseif ($_.risk -eq 'MEDIUM') { 'wn' } else { 'na' }
        $lTid = if ($null -ne $_.tool_id) { $_.tool_id } else { '' }
        $lLib = if ($null -ne $_.lib_code) { $_.lib_code } else { '' }
        $lNm  = if ($null -ne $_.name) { $_.name } else { '' }
        $lSpec = if ($null -ne $_.spec) { $_.spec } else { '' }
        $lSpecLen = [Math]::Min(28, $lSpec.Length)
        $lSpecS = $lSpec.Substring(0, $lSpecLen)
        $lD1 = if ($null -ne $_.D1) { $_.D1 } else { '' }
        $lD5 = if ($null -ne $_.D5) { $_.D5 } else { '' }
        $lCl = if ($null -ne $_.cluster) { $_.cluster } else { '' }
        $lClN = $lCl.Replace('CL_', '')
        $lEt = if ($null -ne $_.env_target) { $_.env_target } else { '' }
        $lRk = if ($null -ne $_.risk) { $_.risk } else { 'NONE' }
        $lSf = if ($null -ne $_.spec_file) { $_.spec_file } else { '' }
        $lSfLast = $lSf.Split('\')[-1]
        $lTidH = [System.Web.HttpUtility]::HtmlEncode($lTid)
        $lLibH = [System.Web.HttpUtility]::HtmlEncode($lLib)
        $lNmH = [System.Web.HttpUtility]::HtmlEncode($lNm)
        $lSpecH = [System.Web.HttpUtility]::HtmlEncode($lSpecS)
        $lD1H = [System.Web.HttpUtility]::HtmlEncode($lD1)
        $lD5H = [System.Web.HttpUtility]::HtmlEncode($lD5)
        $lClH = [System.Web.HttpUtility]::HtmlEncode($lClN)
        $lEtH = [System.Web.HttpUtility]::HtmlEncode($lEt)
        $lRkH = [System.Web.HttpUtility]::HtmlEncode($lRk)
        $lSfH = [System.Web.HttpUtility]::HtmlEncode($lSfLast)
        "<tr><td style='font:700 8px var(--mo)'>$lTidH</td><td style='font:9px var(--mo);color:var(--tl)'>$lLibH</td><td><b>$lNmH</b></td><td style='font:9px var(--mo)'>$lSpecH</td><td style='font:8px var(--mo)'>$lD1H`u{00b7}$lD5H</td><td style='font:8px var(--mo)'>$lClH</td><td style='font:9px var(--mo)'>$lEtH</td><td><span class='bx $rk'>$lRkH</span></td><td style='font:8px var(--mo)'>$lSfH</td></tr>"
    }) -join "`n"

    $gapRows = @($Gap.missing | Select-Object -First 200 | ForEach-Object {
        $gNm = if ($null -ne $_.name) { $_.name } else { '' }
        $gSp = if ($null -ne $_.spec) { $_.spec } else { '' }
        $gEt = if ($null -ne $_.env_target) { $_.env_target } else { '' }
        $gNmH = [System.Web.HttpUtility]::HtmlEncode($gNm)
        $gSpH = [System.Web.HttpUtility]::HtmlEncode($gSp)
        $gEtH = [System.Web.HttpUtility]::HtmlEncode($gEt)
        $gRisk = if ($_.risk -in @('HIGH','MEDIUM')) {
            $gRkCls = if ($_.risk -eq 'HIGH') { 'er' } else { 'wn' }
            "<span class='bx $gRkCls'>$($_.risk)</span>"
        } else { '-' }
        "<tr><td><b>$gNmH</b></td><td style='font:9px var(--mo)'>$gSpH</td><td>$gEtH</td><td><span class='bx er'>NOT_INSTALLED</span></td><td>$gRisk</td></tr>"
    }) -join "`n"

    $sbRows = @($Sandbox | ForEach-Object {
        $uv  = if ($_.uv_compile -eq 'PASS') { "<span class='bd ok'>PASS</span>" } else { "<span class='bd er'>FAIL</span>" }
        $pc  = if ($_.pip_check -eq 'PASS') { "<span class='bd ok'>OK</span>" } elseif ($_.pip_check -eq 'SKIP') { "<span class='bd na'>SKIP</span>" } else { "<span class='bd wn'>WARN</span>" }
        $pd  = if ($_.pipdeptree -eq 'PASS') { "<span class='bd ok'>OK</span>" } elseif ($_.pipdeptree -eq 'SKIP') { "<span class='bd na'>SKIP</span>" } else { "<span class='bd wn'>WARN</span>" }
        $pcc = if ($_.pip_compile -eq 'PASS') { "<span class='bd ok'>OK</span>" } elseif ($_.pip_compile -eq 'SKIP') { "<span class='bd na'>SKIP</span>" } else { "<span class='bd wn'>WARN</span>" }
        $pkg = if ($_.packaging -eq 'PASS') { "<span class='bd ok'>OK</span>" } elseif ($_.packaging -eq 'SKIP') { "<span class='bd na'>SKIP</span>" } else { "<span class='bd wn'>WARN</span>" }
        $rl  = if ($_.resolvelib -eq 'PASS') { "<span class='bd ok'>OK</span>" } elseif ($_.resolvelib -eq 'SKIP') { "<span class='bd na'>SKIP</span>" } else { "<span class='bd na'>MISS</span>" }
        $errShort = if ($_.uv_note) { $_.uv_note.Substring(0, [Math]::Min(120, $_.uv_note.Length)) } else { '' }
        $sbEn = if ($_.env_name) { $_.env_name } else { '' }
        $sbEnH = [System.Web.HttpUtility]::HtmlEncode($sbEn)
        $errH = [System.Web.HttpUtility]::HtmlEncode($errShort)
        "<tr><td><b>$sbEnH</b></td><td>$uv</td><td>$pc</td><td>$pd</td><td>$pcc</td><td>$pkg</td><td>$rl</td><td>$($_.pkg_count)</td><td>$($_.elapsed_sec)</td><td style='font:8px var(--mo);max-width:200px'>$errH</td></tr>"
    }) -join "`n"

    $planRows = @($Policy.install | ForEach-Object {
        $sc = switch ($_.status) { 'ALREADY_PRESENT' { 'na' } 'PLAN_ISOLATED' { 'wn' } default { 'ok' } }
        $pNm = if ($null -ne $_.name) { $_.name } else { '' }
        $pSp = if ($null -ne $_.spec) { $_.spec } else { '' }
        $pEt = if ($null -ne $_.env_target) { $_.env_target } else { '' }
        $pSt = if ($null -ne $_.status) { $_.status } else { '' }
        $pAc = if ($null -ne $_.action) { $_.action } else { '' }
        $pNmH = [System.Web.HttpUtility]::HtmlEncode($pNm)
        $pSpH = [System.Web.HttpUtility]::HtmlEncode($pSp)
        $pEtH = [System.Web.HttpUtility]::HtmlEncode($pEt)
        $pStH = [System.Web.HttpUtility]::HtmlEncode($pSt)
        $pAcH = [System.Web.HttpUtility]::HtmlEncode($pAc)
        $pRisk = if ($_.risk -in @('HIGH','MEDIUM')) {
            $pRkCls = if ($_.risk -eq 'HIGH') { 'er' } else { 'wn' }
            "<span class='bx $pRkCls'>$($_.risk)</span>"
        } else { '-' }
        "<tr><td><b>$pNmH</b></td><td style='font:9px var(--mo)'>$pSpH</td><td>$pRisk</td><td style='font:9px var(--mo)'>$pEtH</td><td><span class='bx $sc'>$pStH</span></td><td class='w' style='font:8px var(--mo)'>$pAcH</td></tr>"
    }) -join "`n"

    $rbRows = @($Policy.rebuild | ForEach-Object {
        $rEn = if ($null -ne $_.env_name) { $_.env_name } else { '' }
        $rHl = if ($null -ne $_.health) { $_.health } else { '' }
        $rRs = if ($null -ne $_.reason) { $_.reason } else { '' }
        $rAc = if ($null -ne $_.action) { $_.action } else { '' }
        $rEnH = [System.Web.HttpUtility]::HtmlEncode($rEn)
        $rHlH = [System.Web.HttpUtility]::HtmlEncode($rHl)
        $rRsH = [System.Web.HttpUtility]::HtmlEncode($rRs)
        $rAcH = [System.Web.HttpUtility]::HtmlEncode($rAc)
        "<tr><td><b>$rEnH</b></td><td><span class='bx er'>$rHlH</span></td><td class='w' style='font:8px var(--mo)'>$rRsH</td><td class='w' style='font:8px var(--mo);color:var(--tl)'>$rAcH</td></tr>"
    }) -join "`n"

    $riskRows = @($Gap.risk_libs | Select-Object -First 100 | ForEach-Object {
        $rc=if($_.risk -eq 'HIGH'){'er'}elseif($_.risk -eq 'MEDIUM'){'wn'}else{'na'}
        $in=if($_.installed){'<span class="bd ok">YES</span>'}else{'<span class="bd er">NO</span>'}
        $cr=if($_.correct_env){'<span class="bd ok">YES</span>'}else{'<span class="bd na">NO</span>'}
        "<tr><td><b>$([System.Web.HttpUtility]::HtmlEncode($(if($_.name){$_.name}else{''})))</b></td><td><span class='bd $rc'>$($_.risk)</span></td><td style='font:9px var(--mo)'>$([System.Web.HttpUtility]::HtmlEncode($(if($_.env_target){$_.env_target}else{''})))</td><td>$in</td><td>$cr</td></tr>"
    }) -join "`n"

    $missEnvRows = @($Policy.missing_env | Select-Object -Unique | ForEach-Object {
        $uvcmd = "uv venv `"$($CONFIG.EnvRoot)\$($_.env_name)`" --python $($CONFIG.PreferredPy)"
        "<tr><td><b>$([System.Web.HttpUtility]::HtmlEncode($(if($_.env_name){$_.env_name}else{''})))</b></td><td>$([System.Web.HttpUtility]::HtmlEncode($(if($_.trigger){$_.trigger}else{''})))</td><td><span class='bd $(if($_.risk -eq 'HIGH'){"er"}elseif($_.risk -eq 'MEDIUM'){"wn"}else{"na"})'>$($_.risk)</span></td><td style='font:8px var(--mo)'>$([System.Web.HttpUtility]::HtmlEncode($uvcmd))</td></tr>"
    }) -join "`n"


    $planPendingCount = @($Policy.install | Where-Object { $_.status -ne "ALREADY_PRESENT" }).Count
    $promptHtml = [System.Web.HttpUtility]::HtmlEncode($(if($AiPrompt){$AiPrompt}else{"（未生成）"}))
    $sysN = [System.Web.HttpUtility]::HtmlEncode($CONFIG.SystemName)
    $sysS = [System.Web.HttpUtility]::HtmlEncode($CONFIG.SystemSubtitle)
    $mode = if($CONFIG.EnableAutoRepair){'AUTO_REPAIR'}else{'READ_ONLY'}

    $html = @"
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VEGN Step 1 v3.2 — VIA Env Governance</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@400;500;600;700&display=swap');
:root{
  --bg:#f5f4f0;--bg1:#edecea;--bg2:#e5e3df;--sf:#fff;--sf2:#fafaf8;--bd:#dbd9d3;--bd2:#ccc9c1;
  --bl:#4c78a8;--bl-l:#d0e1f0;--tl:#439a9a;--tl-l:#c8e6e6;--gn:#5a9e6f;--gn-l:#cde8d5;
  --am:#c4943a;--am-l:#f5e2b8;--co:#c96b5a;--co-l:#f5d0c8;--vi:#7a6daa;--vi-l:#dcd8f0;
  --ro:#b05580;--i0:#1e1d1a;--i1:#3d3c38;--i2:#6b6860;--i3:#9c9890;--i4:#c4c0b8;
  --mo:'DM Mono',monospace;--sa:'DM Sans',system-ui,sans-serif;--hf:'Syne',system-ui,sans-serif;
  --r:5px;--r2:8px;--r3:12px;--sh:0 1px 3px rgba(0,0,0,.06);--sh2:0 4px 12px rgba(0,0,0,.08)
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sa);background:var(--bg);color:var(--i0);font-size:11px;line-height:1.55}
.w{max-width:1600px;margin:0 auto;padding:10px 14px}
.hdr{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r3);padding:14px 16px;margin-bottom:8px;position:relative;overflow:hidden;display:flex;align-items:center;gap:12px}
.hdr::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--bl),var(--tl),var(--vi),var(--am),var(--co))}
.h1t{font-size:18px;font-weight:700;letter-spacing:-.5px;font-family:var(--hf)}
.h1t .ac{color:var(--bl)}.h1t .at{color:var(--tl)}.h1t .av{color:var(--vi)}.h1t .aa{color:var(--am)}
.h2t{color:var(--am);font-size:11px;font-weight:700;font-family:var(--hf);letter-spacing:.3px;margin-top:2px}
.h3t{color:var(--i3);font-size:10px;margin-top:2px}
.hdr-meta{margin-left:auto;text-align:right;font:400 9px var(--mo);color:var(--i3)}
.pt{display:flex;gap:2px;margin-bottom:8px;flex-wrap:wrap}
.pt button{padding:8px 18px;border:1px solid var(--bd);border-radius:var(--r2) var(--r2) 0 0;background:var(--bg1);color:var(--i2);font:600 11px var(--sa);cursor:pointer;border-bottom:2px solid transparent;transition:.15s}
.pt button.on{background:var(--sf);color:var(--bl);border-bottom-color:var(--bl);box-shadow:var(--sh)}
.pt button:hover:not(.on){background:var(--bg2);color:var(--i1)}
.pg{display:none}.pg.on{display:block}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(88px,1fr));gap:4px;margin-bottom:8px}
.sc{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r2);padding:5px 6px;text-align:center;transition:.2s}
.sc:hover{border-color:var(--bl);box-shadow:var(--sh)}
.sc .n{font-size:13px;font-weight:700;font-family:var(--mo);letter-spacing:-.2px}
.sc .l{font-size:8px;color:var(--i3);text-transform:uppercase;letter-spacing:.4px}
.sc.g .n{color:var(--gn)}.sc.r .n{color:var(--co)}.sc.a .n{color:var(--am)}.sc.t .n{color:var(--tl)}.sc.b .n{color:var(--bl)}
.cd{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r2);margin-bottom:6px;overflow:hidden;transition:.15s}
.cd:hover{box-shadow:var(--sh)}
.cd-h{display:flex;align-items:center;gap:6px;padding:7px 10px;border-bottom:1px solid var(--bd);background:var(--sf2)}
.cd-i{width:24px;height:24px;border-radius:var(--r);display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0}
.cd-t{font-weight:600;font-size:11px;flex:1}
.cd-s{font-family:var(--mo);font-size:9px;color:var(--i3);padding:1px 5px;background:var(--bg1);border-radius:10px}
.cd-b{padding:8px 10px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
.mx{width:100%;border-collapse:collapse;font-size:10px}
.mx th{background:var(--bg1);padding:4px 5px;text-align:left;font-weight:600;color:var(--i2);border-bottom:2px solid var(--bd);position:sticky;top:0;z-index:1;white-space:nowrap}
.mx td{padding:3px 5px;border-bottom:1px solid var(--bd);vertical-align:top}
.mx tr:hover{background:rgba(76,120,168,.03)}
.mx code{font-family:var(--mo);font-size:9.5px;background:var(--bg1);padding:0 3px;border-radius:3px}
.mw{max-height:380px;overflow:auto;border:1px solid var(--bd);border-radius:var(--r)}
.bd{display:inline-block;padding:1px 5px;border-radius:4px;font-family:var(--mo);font-size:8.5px;font-weight:600;letter-spacing:.2px}
.bd.ok{background:var(--gn-l);color:var(--gn)}.bd.er{background:var(--co-l);color:var(--co)}
.bd.wn{background:var(--am-l);color:var(--am)}.bd.na{background:var(--bg2);color:var(--i3)}
.bd.tl{background:var(--tl-l);color:var(--tl)}.bd.vi{background:var(--vi-l);color:var(--vi)}
.bd.bl{background:var(--bl-l);color:var(--bl)}
.pi{width:100%;padding:6px 8px;background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);font:11px var(--mo);color:var(--i0);transition:.15s}
.pi:focus{border-color:var(--bl);outline:none;box-shadow:0 0 0 2px rgba(76,120,168,.1)}
.bn{padding:5px 10px;border:1px solid var(--bd);border-radius:var(--r);font:500 10px var(--sa);cursor:pointer;transition:.15s;background:var(--sf)}
.bn:hover{border-color:var(--bl);color:var(--bl)}.bn.bp{background:var(--bl);color:#fff;border-color:var(--bl)}
.bn.bp:hover{background:#3b6790}
.tm{background:#1e1d1a;border-radius:var(--r2);overflow:hidden;border:1px solid #333;font-family:var(--mo);font-size:10px}
.tm-bar{display:flex;align-items:center;padding:6px 10px;background:#2a2924;gap:6px;border-bottom:1px solid #333}
.tm-dot{width:8px;height:8px;border-radius:50%}.td1{background:#e5534b}.td2{background:#d29922}.td3{background:#3fb950}
.tm-title{flex:1;color:#8b949e;font-size:9px;text-align:center;text-transform:uppercase;letter-spacing:1px}
.tm-body{padding:8px 10px;max-height:300px;overflow-y:auto;color:#c9d1d9;line-height:1.7}
.tm-body .ok{color:#3fb950}.tm-body .wn{color:#d29922}.tm-body .er{color:#f85149}.tm-body .dim{color:#6e7681}
.prm{background:#1e1d1a;border-radius:var(--r2);padding:12px;font:10px var(--mo);color:#c9d1d9;
  white-space:pre-wrap;word-break:break-word;max-height:480px;overflow-y:auto;border:1px solid #333;line-height:1.7}
@media(max-width:900px){.g2,.g3{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="w">

<!-- Header -->
<div class="hdr">
  <div style="flex:1">
    <div class="h1t"><span>Veritas</span><span class="ac">Intelligence</span><span>Analytics · </span><span class="at">Environment</span><span class="av"> Governance Nexus</span> <span class="aa">(VEGN)</span></div>
    <div class="h2t">VERITAS INTELLIGENCE SYSTEM</div>
    <div class="h3t">Step 1 v3.2 · Base Guardian → 環境健康 → 5D 分類 → 8工具衝突守門人 → 政策計劃 → AI Prompt · 100% 唯讀</div>
  </div>
  <div class="hdr-meta">
    <div>Run: $RUN_ID</div>
    <div style="margin-top:2px">Mode: $(if($CONFIG.EnableAutoRepair){"AUTO_REPAIR"}else{"READ_ONLY"})</div>
  </div>
</div>

<!-- KPI Stats -->
<div class="sg">
  <div class="sc b"><div class="n">$($script:ST.CandidateEnvCount)</div><div class="l">Via Envs</div></div>
  <div class="sc g"><div class="n">$($script:ST.HealthyEnvCount)</div><div class="l">Healthy</div></div>
  <div class="sc r"><div class="n">$($script:ST.RiskEnvCount)</div><div class="l">Risk Env</div></div>
  <div class="sc a"><div class="n">$($script:ST.BasePollutedCount)</div><div class="l">Base Polluted</div></div>
  <div class="sc t"><div class="n">$($script:ST.UniqueProjectImports)</div><div class="l">Unique Libs</div></div>
  <div class="sc r"><div class="n">$($script:ST.ConflictEnvCount)</div><div class="l">Sandbox FAIL</div></div>
  <div class="sc"><div class="n" style="font-size:11px">$($script:ST.FilesScanned)</div><div class="l">Files Scanned</div></div>
  <div class="sc"><div class="n" style="font-size:9px">$($script:ST.BasePollutedCount -eq 0 ? "CLEAN" : "POLLUTED")</div><div class="l">Base Status</div></div>
</div>

<!-- Tabs -->
<div class="pt" id="tabs">
  <button class="on" onclick="pg(1)">P1 · Base Guardian</button>
  <button onclick="pg(2)">P2 · 環境健康</button>
  <button onclick="pg(3)">P3 · Lib 5D 分類</button>
  <button onclick="pg(4)">P4 · 缺口分析</button>
  <button onclick="pg(5)">P5 · 衝突守門人</button>
  <button onclick="pg(6)">P6 · 安裝計劃</button>
  <button onclick="pg(7)">P7 · AI Prompt</button>
</div>

<!-- P1: Base Guardian -->
<div id="p1" class="pg on">
<div class="cd">
  <div class="cd-h"><div class="cd-i" style="background:var(--co-l)">🛡</div><div class="cd-t">Base Guardian — 污染偵測與分流計劃</div><span class="cd-s">PHASE 1</span></div>
  <div class="cd-b">
    <div class="mw">
    <table class="mx">
      <thead><tr><th>套件</th><th>版本</th><th>污染位置</th><th>應路由至</th><th>狀態</th><th>行動</th></tr></thead>
      <tbody>$pollRows</tbody>
    </table>
    </div>
  </div>
</div>
<div class="g2">
  <div class="cd">
    <div class="cd-h"><div class="cd-i" style="background:var(--bl-l)">🗺</div><div class="cd-t">Via_* 路由表</div></div>
    <div class="cd-b" style="font-size:10px;display:grid;grid-template-columns:1fr 1fr;gap:4px">
      <div>🔵 <b>via_core</b> — Risk=LOW 專屬</div>
      <div>🟡 <b>via_governance</b> — 治理工具</div>
      <div>🟠 <b>via_browser</b> — playwright/selenium</div>
      <div>🟠 <b>via_render</b> — weasyprint/cairosvg</div>
      <div>🔴 <b>via_ai_bg</b> — opencv/rembg/onnx</div>
      <div>🔴 <b>via_core_ml</b> — torch/transformers</div>
      <div>⛔ <b>via_ocr_surya</b> — surya 完全隔離</div>
      <div>⚠ <b>numba/ortools</b> — MaxPy 3.12</div>
    </div>
  </div>
  <div class="cd">
    <div class="cd-h"><div class="cd-i" style="background:var(--gn-l)">⚙</div><div class="cd-t">8 工具衝突守門人</div></div>
    <div class="cd-b" style="font-size:10px">
      <table class="mx">
        <thead><tr><th>工具</th><th>角色</th></tr></thead>
        <tbody>
          <tr><td><code>uv pip compile</code></td><td>核心解析 — 依賴可解性測試</td></tr>
          <tr><td><code>pipdeptree</code></td><td>依賴樹 + --warn conflict</td></tr>
          <tr><td><code>pip check</code></td><td>安裝一致性驗證</td></tr>
          <tr><td><code>pip-compile</code></td><td>dry-run 模擬解析</td></tr>
          <tr><td><code>packaging</code></td><td>版本/約束解析驗證</td></tr>
          <tr><td><code>resolvelib</code></td><td>低階解析引擎偵測</td></tr>
          <tr><td><code>pip-audit</code></td><td>安全漏洞掃描（加分）</td></tr>
          <tr><td><code>pipgrip</code></td><td>解析壓力測試（加分）</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
</div>

<!-- P2: 環境健康 -->
<div id="p2" class="pg">
<div class="cd">
  <div class="cd-h"><div class="cd-i" style="background:var(--tl-l)">🏥</div><div class="cd-t">環境健康矩陣</div><span class="cd-s">PHASE 2 · ENV_HEALTH</span></div>
  <div class="mw">
  <table class="mx">
    <thead><tr><th>環境</th><th>Python</th><th>套件數</th><th>健康</th><th>污染</th><th>衝突</th><th>pip check</th><th>Risk</th><th>說明</th></tr></thead>
    <tbody>$envRows</tbody>
  </table>
  </div>
</div>
</div>

<!-- P3: Lib 5D 分類 -->
<div id="p3" class="pg">
<div class="cd">
  <div class="cd-h">
    <div class="cd-i" style="background:var(--vi-l)">🧬</div>
    <div class="cd-t">VIA Lib 5D 分類總表</div>
    <span class="cd-s">PHASE 3-4 · 5D_REGISTRY</span>
    <input class="pi" id="srch" placeholder="搜尋 lib / cluster / risk…" oninput="flt()" style="max-width:200px;padding:3px 7px;font-size:10px;margin-left:8px">
    <span style="font:9px var(--mo);color:var(--i3);margin-left:6px" id="cnt"></span>
  </div>
  <div class="mw">
  <table class="mx" id="tLib">
    <thead><tr><th>ID</th><th>LIB-CODE</th><th>套件</th><th>Spec</th><th>D1</th><th>D5</th><th>Cluster</th><th>目標環境</th><th>Risk</th><th>來源</th></tr></thead>
    <tbody>$libRows</tbody>
  </table>
  </div>
</div>
</div>

<!-- P4: 缺口分析 -->
<div id="p4" class="pg">
<div class="g2">
<div class="cd">
  <div class="cd-h"><div class="cd-i" style="background:var(--co-l)">📭</div><div class="cd-t">NOT_INSTALLED 缺口</div><span class="cd-s">$(@($Gap.missing).Count) 個</span></div>
  <div class="mw">
  <table class="mx">
    <thead><tr><th>套件</th><th>Spec</th><th>目標環境</th><th>Risk</th></tr></thead>
    <tbody>$gapRows</tbody>
  </table>
  </div>
</div>
<div class="cd">
  <div class="cd-h"><div class="cd-i" style="background:var(--am-l)">📍</div><div class="cd-t">風險 Lib 清單</div><span class="cd-s">$(@($Gap.risk_libs).Count) 個</span></div>
  <div class="mw">
  <table class="mx">
    <thead><tr><th>套件</th><th>Risk</th><th>目標環境</th><th>已安裝</th><th>位置正確</th></tr></thead>
    <tbody>$riskRows</tbody>
  </table>
  </div>
</div>
</div>
</div>

<!-- P5: 衝突守門人 -->
<div id="p5" class="pg">
<div class="cd">
  <div class="cd-h"><div class="cd-i" style="background:var(--am-l)">⚔</div><div class="cd-t">衝突守門人結果（8 工具）</div><span class="cd-s">PHASE 6</span></div>
  <div class="mw">
  <table class="mx">
    <thead><tr><th>環境</th><th>uv compile</th><th>pip check</th><th>pipdeptree</th><th>pip-compile</th><th>packaging</th><th>resolvelib</th><th>套件數</th><th>耗時(s)</th><th>錯誤</th></tr></thead>
    <tbody>$sbRows</tbody>
  </table>
  </div>
</div>
</div>

<!-- P6: 安裝計劃 -->
<div id="p6" class="pg">
<div class="cd">
  <div class="cd-h"><div class="cd-i" style="background:var(--gn-l)">📋</div><div class="cd-t">安裝計劃矩陣</div><span class="cd-s">PHASE 7 · $planPendingCount 待安裝</span></div>
  <div class="mw">
  <table class="mx">
    <thead><tr><th>套件</th><th>Spec</th><th>Risk</th><th>目標環境</th><th>狀態</th><th>行動</th></tr></thead>
    <tbody>$planRows</tbody>
  </table>
  </div>
</div>
<div class="g2">
<div class="cd">
  <div class="cd-h"><div class="cd-i" style="background:var(--co-l)">🔧</div><div class="cd-t">環境重建計劃</div></div>
  <div class="mw">
  <table class="mx">
    <thead><tr><th>環境</th><th>健康</th><th>原因</th><th>行動</th></tr></thead>
    <tbody>$rbRows</tbody>
  </table>
  </div>
</div>
<div class="cd">
  <div class="cd-h"><div class="cd-i" style="background:var(--vi-l)">➕</div><div class="cd-t">缺失環境建立</div></div>
  <div class="mw">
  <table class="mx">
    <thead><tr><th>環境名稱</th><th>觸發套件</th><th>Risk</th><th>建立指令</th></tr></thead>
    <tbody>$missEnvRows</tbody>
  </table>
  </div>
</div>
</div>
</div>

<!-- P7: AI Prompt -->
<div id="p7" class="pg">
<div class="cd">
  <div class="cd-h">
    <div class="cd-i" style="background:var(--bl-l)">🤖</div>
    <div class="cd-t">AI 安裝計劃 Prompt（Step 1 v3.2）</div>
    <button class="bn bp" onclick="copyPrompt()" style="font-size:10px;padding:4px 10px">📋 複製 Prompt</button>
  </div>
  <div class="prm" id="prm">$promptHtml</div>
</div>
</div>

</div><!-- .w -->

<script>
function pg(n){
  document.querySelectorAll('.pg').forEach((p,i)=>p.classList.toggle('on',i===n-1));
  document.querySelectorAll('#tabs button').forEach((b,i)=>b.classList.toggle('on',i===n-1));
}
function flt(){
  const q=(document.getElementById('srch').value||'').toLowerCase();
  let v=0,t=0;
  document.querySelectorAll('#tLib tbody tr').forEach(tr=>{
    t++; const show=!q||tr.textContent.toLowerCase().includes(q);
    tr.style.display=show?'':'none'; if(show)v++;
  });
  document.getElementById('cnt').textContent=v+'/'+t+' 個';
}
function copyPrompt(){
  const txt=document.getElementById('prm').textContent;
  navigator.clipboard.writeText(txt).then(()=>alert('Prompt 已複製！')).catch(()=>alert('請手動複製'));
}
window.onload=function(){flt()};
</script>
</body></html>
"@
    [System.IO.File]::WriteAllText($HTML_PATH,$html,[System.Text.Encoding]::UTF8)
    WL "HTML → $HTML_PATH" 'OK' 'EXPORT'
    if ($AiPrompt) { [System.IO.File]::WriteAllText($AI_PROMPT_PATH,$AiPrompt,[System.Text.Encoding]::UTF8); WL "AI Prompt → $AI_PROMPT_PATH" 'OK' 'EXPORT' }
}

# ── MAIN ──────────────────────────────────────────────────────────────────────
WL ('═'*56) 'OK'
WL $CONFIG.SystemName    'OK'
WL $CONFIG.SystemSubtitle 'OK'
WL "RunDir = $RUN_DIR"   'INFO' 'INIT'
$sw = [System.Diagnostics.Stopwatch]::StartNew()

Phase0-Bootstrap

$bgResult   = Phase1-BaseGuardian
$script:ST.BaseGuardResult = $bgResult

$envHealth  = @(Phase2-EnvScan)

$defaultTargets = @(
    (Join-Path $CONFIG.BaseRootA 'module\VRN'),
    (Join-Path $CONFIG.BaseRootA 'module\VAP'),
    (Join-Path $CONFIG.BaseRootA 'module\VCNC'),
    (Join-Path $CONFIG.BaseRootA 'module\VDF')
)
$vegnFiles = @('VeritasAegisNexus.py','VeritasCeleritas.py','VIA_5D_CodeEngine.py',
               'VIA_5D_Launcher.ps1','via_env_governance_engine.ps1','VIA_SSOT_Unified.psm1',
               'VIA_SSOT_Unified.py','via_tool_classifier.py','via_tool_governance.py',
               'VIA_UltimateGovernance_v5_Supreme.ps1','VIA_StepTools.psm1') |
    ForEach-Object { Join-Path $CONFIG.VEGNRoot $_ } |
    Where-Object { Test-Path $_ -EA SilentlyContinue }
$allTargets = @($defaultTargets + $vegnFiles) | Select-Object -Unique

$scanResult = Phase34-LibScanClassify -Targets $allTargets
if (-not $scanResult) { WL "LibScan 失敗，略過後續階段" 'ERR'; $scanResult = [PSCustomObject]@{scan=@{total_files=0;total_libs=0;conflicts=@()};classified=@();conflicts=@()} }
$script:ST.FilesScanned = $scanResult.scan.total_files

$gapResult  = Phase5-GapMap -Classified $scanResult.classified -EnvHealth $envHealth
$sandbox    = @(Phase6-ConflictScan -Gap $gapResult)
$policy     = Phase7-PolicyPlan -EnvHealth $envHealth -Classified $scanResult.classified -Gap $gapResult
$aiPrompt   = Phase8-PromptGen -Policy $policy -Sandbox $sandbox -EnvHealth $envHealth -BaseGuard $bgResult

Phase9-Export -EnvHealth $envHealth -Classified $scanResult.classified -Gap $gapResult `
              -Sandbox $sandbox -Policy $policy -BaseGuard $bgResult -AiPrompt $aiPrompt

# JSON
$report = [PSCustomObject]@{
    Summary = [PSCustomObject]@{
        RunId       = $RUN_ID; StartedAt=$script:ST.StartedAt
        EndedAt     = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        ElapsedSec  = [Math]::Round($sw.Elapsed.TotalSeconds,2)
        FilesScanned= $script:ST.FilesScanned; EnvCount=$script:ST.CandidateEnvCount
        HealthyEnv  = $script:ST.HealthyEnvCount; RiskEnv=$script:ST.RiskEnvCount
        BasePolluted= $script:ST.BasePollutedCount; SandboxFail=$script:ST.ConflictEnvCount
        HtmlPath=$HTML_PATH; AiPromptPath=$AI_PROMPT_PATH; PolicyPath=$POLICY_PATH
    }
    EnvHealth       = @($envHealth)
    BaseGuardResult = $bgResult
    Classified      = @($scanResult.classified | Select-Object -First 200)
    GapResult       = @{missing=@($gapResult.missing);wrong_env=@($gapResult.wrong_env);risk_libs=@($gapResult.risk_libs)}
    Sandbox         = @($sandbox)
    Policy          = $policy
}
$report | ConvertTo-Json -Depth 10 | Out-File $JSON_PATH -Encoding UTF8
$policy  | ConvertTo-Json -Depth 10 | Out-File $POLICY_PATH -Encoding UTF8
$sw.Stop()

WL ('═'*56) 'OK'
WL 'VEGN STEP 1 v3.2 COMPLETE' 'OK'
WL ("Files scanned    : {0}" -f $script:ST.FilesScanned)         'OK'
WL ("via_ envs        : {0}" -f $script:ST.CandidateEnvCount)    'OK'
WL ("Healthy envs     : {0}" -f $script:ST.HealthyEnvCount)      'OK'
WL ("Base polluted    : {0}" -f $script:ST.BasePollutedCount)     'OK'
WL ("Sandbox FAIL     : {0}" -f $script:ST.ConflictEnvCount)      'OK'
WL ("Elapsed sec      : {0}" -f [Math]::Round($sw.Elapsed.TotalSeconds,2)) 'OK'
WL ("HTML             : {0}" -f $HTML_PATH)                       'OK'
WL ("AI Prompt        : {0}" -f $AI_PROMPT_PATH)                  'OK'
WL ('═'*56) 'OK'

if ($CONFIG.EnableHtmlAutoOpen -and (Test-Path $HTML_PATH)) {
    try   { Start-Process $HTML_PATH | Out-Null; WL 'HTML 已自動開啟' 'OK' 'OPEN' }
    catch { WL 'HTML 自動開啟失敗，請手動開啟' 'WARN' 'OPEN' }
}


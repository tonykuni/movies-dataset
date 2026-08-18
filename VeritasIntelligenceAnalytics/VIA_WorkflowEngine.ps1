<#
VIA_WorkflowEngine.ps1 — Windows 一鍵啟動器（ONE POWERSHELL TO HANDLE ALL）
===========================================================================
包辦 Windows 上執行 VIA_WorkflowEngine.py 的全部前置：
  1. Python 偵測：py -3 → python → python3（需 3.8+；自動擋 Microsoft Store 假棒）
  2. UTF-8 主控台（中文輸出不亂碼）+ PYTHONUTF8/PYTHONIOENCODING
  3. 引擎路徑解析（以本檔所在目錄定位 — 任何 cwd 都能跑）
  4. 參數原樣透傳引擎全部動詞，外加三個 wrapper 動詞

WRAPPER 動詞
  doctor     環境診斷（interpreter / 各引擎在位 / PyYAML / 繪圖庫 / SSOT / 模組）
  setup      安裝選配依賴 PyYAML（--user）；十庫安裝指令僅列印、絕不代裝
  setup vap  安裝繪圖後端 seaborn+plotly+pandas（--user；您明示才裝）
  setup chipwar  安裝 ChipWar/MultiFactor 依賴 duckdb+scipy+scikit-learn+statsmodels
  all        backends → 工作流 selftest → VAP 繪圖 selftest 一鍵全驗證
  vap …      透傳 VAP seaborn+plotly 繪圖引擎（probe|list|spec|render|demo|selftest|columns）
  talib …    透傳 TALib 指標引擎（probe|list|sample|compute|signals|chart|selftest;adj 鐵律）
  theory     今日五引擎理論稽核 — PS 獨立甲骨文 14 斷言（自算期望值對質,非引擎自證）
  chipwar    跑 ChipWar 13 階段全鏈（籌碼戰五 lane + 報告 + harness + VAP 儀表板；可加 --dry-run）
  mf         跑 MultiFactor 共振引擎（= multifactor；可加 --dry-run）
  dashboard  只重生 ChipWar × VAP 儀表板並印 index 路徑
  flowsystem FlowSystem v2 一鍵（引擎未上傳時誠實回報待傳清單）
  status     全模組在位/缺席全景
  everything 一支到底：all + chipwar + mf + theory（本 session 全部建設一次驗完）

引擎動詞（透傳）
  backends | demo [...] | sample | master [params.json] [--dry-run]
  run <file> [--backend ...] [--param k=v] | resume <file> <run_id>
  export <file> --format <fmt> [--out 檔案] | scaffold <target> | runs | selftest

USAGE
  .\VIA_WorkflowEngine.ps1 all
  .\VIA_WorkflowEngine.ps1 sample                                    # 先產生範例流程檔
  .\VIA_WorkflowEngine.ps1 run via_sample_flow.yaml
  .\VIA_WorkflowEngine.ps1 master --dry-run                          # VMT 九階段預覽
  .\VIA_WorkflowEngine.ps1 vap probe                                 # 繪圖後端探測
  .\VIA_WorkflowEngine.ps1 vap demo --out vap_demo                   # 28 圖型全渲染
  .\VIA_WorkflowEngine.ps1 vap render --chart candle --backend both --out out
  .\VIA_WorkflowEngine.ps1 -Python C:\Python312\python.exe selftest   # 指定直譯器

  被 ExecutionPolicy 擋時：
  powershell -ExecutionPolicy Bypass -File .\VIA_WorkflowEngine.ps1 all
#>
$ErrorActionPreference = 'Stop'
$BranchHint = 'claude/workflow-engine-libs-integration-pxsyv3'

# 不宣告 param 塊 — 一切進 $args，手動抽出 -Python，其餘原樣透傳引擎。
# （宣告式 param 會把第一個位置參數吃進 $Python，動詞就消失；advanced param
#   又會讓 -o 與 -OutVariable 前綴撞名。手動掃描是兩全做法。）
$Python = ''
$EngineArgs = New-Object System.Collections.Generic.List[string]
$RawArgs = @($args)
# 互動式 PowerShell 會把未加引號的 a,b,c 解析成陣列(單一 $args 元素)—
# 先攤平成逐一參數,否則 [string] 轉換會黏成一個含空格的 token。
$Flat = New-Object System.Collections.Generic.List[object]
foreach ($item in $RawArgs) {
    if (($item -is [System.Array]) -and ($item -isnot [string])) {
        foreach ($e in $item) { [void]$Flat.Add($e) }
    } else {
        [void]$Flat.Add($item)
    }
}
$RawArgs = @($Flat.ToArray())
$i = 0
while ($i -lt $RawArgs.Count) {
    $tok = [string]$RawArgs[$i]
    if (($tok -ieq '-Python') -or ($tok -ieq '--python')) {
        if (($i + 1) -lt $RawArgs.Count) {
            $Python = [string]$RawArgs[$i + 1]
            $i += 2
            continue
        }
        Write-Host '誠實 FAIL：-Python 後面需要直譯器路徑（例：-Python C:\Python312\python.exe）'
        exit 1
    }
    [void]$EngineArgs.Add($tok)
    $i++
}
$EngineArgs = @($EngineArgs.ToArray())

# ── UTF-8 主控台（先於任何中文輸出）────────────────────────────────────────
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

function Write-Tag {
    param([string]$Tag, [string]$Msg)
    Write-Host ("  [{0}] {1}" -f $Tag, $Msg)
}

# ── Python 偵測 ────────────────────────────────────────────────────────────
function Test-PythonCandidate {
    param([string]$Exe, [string[]]$Pre = @())
    if (-not (Get-Command $Exe -ErrorAction SilentlyContinue)) { return $null }
    $out = ''
    try {
        $probe = @($Pre) + @('--version')
        $out = (& $Exe $probe 2>&1 | Out-String).Trim()
    } catch { return $null }
    if ($LASTEXITCODE -ne 0) { return $null }   # Store 假棒 / 壞安裝在此被擋
    if ($out -match 'Python (\d+)\.(\d+)') {
        $maj = [int]$Matches[1]
        $min = [int]$Matches[2]
        if (($maj -eq 3 -and $min -ge 8) -or ($maj -gt 3)) {
            return @{ Exe = $Exe; Pre = @($Pre); Ver = ('{0}.{1}' -f $maj, $min) }
        }
    }
    return $null
}

function Find-Python {
    $c = Test-PythonCandidate -Exe 'py' -Pre @('-3')
    if ($null -ne $c) { return $c }
    $c = Test-PythonCandidate -Exe 'python'
    if ($null -ne $c) { return $c }
    return (Test-PythonCandidate -Exe 'python3')
}

if ($Python -ne '') {
    # 使用者明講的直譯器不可用 = 誠實 FAIL，絕不默默換別支
    $Py = Test-PythonCandidate -Exe $Python
    if ($null -eq $Py) {
        Write-Host ('VIA_WorkflowEngine 啟動器 — 誠實 FAIL：指定的 -Python 不可用：{0}' -f $Python)
        Write-Tag 'FIX' '確認路徑正確且為 Python 3.8+；或拿掉 -Python 改用自動偵測'
        exit 1
    }
} else {
    $Py = Find-Python
}
if ($null -eq $Py) {
    Write-Host 'VIA_WorkflowEngine 啟動器 — 誠實 FAIL：找不到可用的 Python 3.8+'
    Write-Tag 'FIX' '安裝其一後重試：'
    Write-Host '        winget install -e --id Python.Python.3.12'
    Write-Host '        或 https://www.python.org/downloads/（勾選 Add python.exe to PATH）'
    exit 1
}
$PyExe = [string]$Py.Exe
$PyPre = @($Py.Pre)

# ── 引擎路徑解析（本檔同目錄優先；備援：cwd 向下搜尋）──────────────────────
$EnginePath = Join-Path $PSScriptRoot 'VIA_WorkflowEngine.py'
if (-not (Test-Path -LiteralPath $EnginePath)) {
    $hit = Get-ChildItem -Path (Get-Location).Path -Filter 'VIA_WorkflowEngine.py' `
        -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $hit) { $EnginePath = $hit.FullName }
}
if (-not (Test-Path -LiteralPath $EnginePath)) {
    Write-Host 'VIA_WorkflowEngine 啟動器 — 誠實 FAIL：找不到 VIA_WorkflowEngine.py'
    Write-Tag 'FIX' ('請確認已取回分支：git fetch origin; git checkout ' + $BranchHint)
    exit 1
}

function Invoke-EngineHost {
    # doctor/all 用：輸出直入主控台（不進管線）；回傳 exit code
    param([string[]]$A)
    $full = @($PyPre) + @($EnginePath) + @($A)
    & $PyExe $full 2>&1 | Out-Host
    return $LASTEXITCODE
}

# ── VAP seaborn+plotly 繪圖引擎（新平行引擎線;動態解析鐵律:取最新版,嚴禁寫死版號）──
$VapEngineDir = Join-Path $PSScriptRoot 'functional modules\VAP\engine'
$VapEngine = Get-ChildItem -LiteralPath $VapEngineDir -Filter 'VAP_ENG003_AutoplotSeabornPlotly_v0*.py' -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1 -ExpandProperty FullName
if (-not $VapEngine) { $VapEngine = Join-Path $VapEngineDir 'VAP_ENG003_AutoplotSeabornPlotly_v0100.py' }

# ── 本 session 各模組定位 ──────────────────────────────────────────────────
$ChipWarParams = Join-Path $PSScriptRoot 'functional modules\ChipWar\chipwar_params.json'
$ChipWarDash   = Join-Path $PSScriptRoot 'functional modules\ChipWar\engines\CHW_ENG016_ChipwarVapDashboard.py'
$ChipWarIndex  = Join-Path $PSScriptRoot 'functional modules\ChipWar\_generated\reports\vap_dashboard\index.html'
$MFParams      = Join-Path $PSScriptRoot 'functional modules\MultiFactor\mf_params.json'
$MFManifest    = Join-Path $PSScriptRoot 'functional modules\MultiFactor\engines\VIA_MF_ENGINE_SHA256_MANIFEST_v0100.json'
$FlowV2Dir     = Join-Path $PSScriptRoot 'supportive modules\VIA_FlowSystem\FlowSystem_v2'
$FlowV2Launch  = Join-Path $FlowV2Dir 'Activate-VIAFlowSystem.ps1'
$TALibEngine   = Join-Path $PSScriptRoot 'functional modules\TALib\VIA_ENG003_TALibEngine.py'
$TheoryAudit   = Join-Path $PSScriptRoot 'Test-VIA-TheoryAudit.ps1'

function Invoke-VapHost {
    param([string[]]$A)
    if (-not (Test-Path -LiteralPath $VapEngine)) {
        Write-Tag 'FAIL' ('找不到 VAP 繪圖引擎：{0}（git pull 取回分支最新版）' -f $VapEngine)
        return 1
    }
    $full = @($PyPre) + @($VapEngine) + @($A)
    & $PyExe $full 2>&1 | Out-Host
    return $LASTEXITCODE
}

function Test-PyModule {
    param([string]$ModuleName)
    & $PyExe (@($PyPre) + @('-c', ('import ' + $ModuleName))) 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

$Verb = ''
if ($EngineArgs.Count -gt 0) { $Verb = ([string]$EngineArgs[0]).ToLowerInvariant() }

# ── wrapper 動詞 ───────────────────────────────────────────────────────────
if ($Verb -eq 'doctor') {
    Write-Host '════════════════════════════════════════════════════════'
    Write-Host ' VIA_WorkflowEngine doctor — 環境診斷'
    Write-Host '════════════════════════════════════════════════════════'
    Write-Tag 'OK  ' ('Python {0}  （{1} {2}）' -f $Py.Ver, $PyExe, ($PyPre -join ' '))
    Write-Tag 'OK  ' ('引擎  {0}' -f $EnginePath)
    if (Test-PyModule 'yaml') {
        Write-Tag 'OK  ' 'PyYAML 在位（YAML DSL 已啟用）'
    } else {
        Write-Tag 'INFO' 'PyYAML 缺席 — JSON DSL 照常全功能；要 YAML 就跑：.\VIA_WorkflowEngine.ps1 setup'
    }
    if (Test-Path -LiteralPath $VapEngine) {
        Write-Tag 'OK  ' ('VAP 繪圖引擎  {0}' -f $VapEngine)
        foreach ($mod in @('seaborn', 'plotly', 'pandas')) {
            if (Test-PyModule $mod) {
                Write-Tag 'OK  ' ('繪圖庫 {0} 在位' -f $mod)
            } else {
                Write-Tag 'INFO' ('繪圖庫 {0} 缺席 — 安裝：.\VIA_WorkflowEngine.ps1 setup vap' -f $mod)
            }
        }
    } else {
        Write-Tag 'INFO' 'VAP 繪圖引擎未在位（git pull 取回分支最新版）'
    }
    foreach ($pair in @(@('ChipWar 13 階段', $ChipWarParams), @('MultiFactor 引擎', $MFParams),
                        @('FlowSystem v2 啟動器', $FlowV2Launch))) {
        if (Test-Path -LiteralPath $pair[1]) {
            Write-Tag 'OK  ' ('{0} 在位' -f $pair[0])
        } else {
            Write-Tag 'INFO' ('{0} 缺席（git pull 或待上傳）' -f $pair[0])
        }
    }
    Write-Host ''
    $code = Invoke-EngineHost @('backends')
    if (Test-Path -LiteralPath $VapEngine) {
        Write-Host ''
        $null = Invoke-VapHost @('probe')
    }
    exit $code
}

if ($Verb -eq 'setup' -and $EngineArgs.Count -ge 2 -and
    ([string]$EngineArgs[1]).ToLowerInvariant() -eq 'chipwar') {
    Write-Host '安裝 ChipWar/MultiFactor 依賴 duckdb + scipy + scikit-learn + statsmodels（--user）…'
    & $PyExe (@($PyPre) + @('-m', 'pip', 'install', '--user', 'duckdb', 'scipy', 'scikit-learn', 'statsmodels')) 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) {
        Write-Tag 'OK  ' '依賴安裝完成。試試：.\VIA_WorkflowEngine.ps1 chipwar --dry-run'
        exit 0
    }
    Write-Tag 'FAIL' ('pip 回傳 exit={0}' -f $LASTEXITCODE)
    exit 1
}

if ($Verb -eq 'setup' -and $EngineArgs.Count -ge 2 -and
    ([string]$EngineArgs[1]).ToLowerInvariant() -eq 'vap') {
    Write-Host '安裝 VAP 繪圖後端 seaborn + plotly + pandas（--user；您明示才裝）…'
    & $PyExe (@($PyPre) + @('-m', 'pip', 'install', '--user', 'seaborn', 'plotly', 'pandas')) 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) {
        Write-Tag 'OK  ' '繪圖後端安裝完成。試試：.\VIA_WorkflowEngine.ps1 vap selftest'
        exit 0
    }
    Write-Tag 'FAIL' ('pip 回傳 exit={0} — 請檢查網路 / pip 環境' -f $LASTEXITCODE)
    exit 1
}

if ($Verb -eq 'setup') {
    Write-Host '安裝選配依賴 PyYAML（--user，僅此一項）…'
    & $PyExe (@($PyPre) + @('-m', 'pip', 'install', '--user', 'pyyaml')) 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) {
        Write-Tag 'OK  ' 'PyYAML 安裝完成'
    } else {
        Write-Tag 'FAIL' ('pip 回傳 exit={0} — 請檢查網路 / pip 環境' -f $LASTEXITCODE)
    }
    Write-Host ''
    Write-Host '十庫為選配、本啟動器絕不代裝；需要哪個自行執行（缺席時引擎自動回退原生）：'
    Write-Host '  pip install prefect            # 現代資料管線'
    Write-Host '  pip install transitions        # 輕量狀態機'
    Write-Host '  pip install SpiffWorkflow      # BPMN 2.0'
    Write-Host '  pip install langgraph          # AI 循環圖'
    Write-Host '  pip install crewai             # 多智能體（需 LLM 金鑰）'
    Write-Host '  pip install llama-index-core   # 事件驅動 AI 流程'
    Write-Host '  pip install temporalio         # 耐用執行（另需 scaffold temporal 起 server）'
    Write-Host '  pip install django viewflow    # 網頁審批流程'
    Write-Host '  # Apache Airflow 官方不支援原生 Windows — 請用 WSL2 或 Docker'
    Write-Host '  # Kestra 為 Java 伺服器型 — 用 .\VIA_WorkflowEngine.ps1 scaffold kestra'
    exit 0
}

if ($Verb -eq 'all') {
    Write-Host '── [1/3] backends 十庫在位探測 ──────────────────────────'
    $c1 = Invoke-EngineHost @('backends')
    Write-Host ''
    Write-Host '── [2/3] 工作流引擎 selftest ────────────────────────────'
    $c2 = Invoke-EngineHost @('selftest')
    Write-Host ''
    Write-Host '── [3/3] VAP 繪圖引擎 selftest（seaborn+plotly）─────────'
    $c3 = 0
    if (Test-Path -LiteralPath $VapEngine) {
        if ((Test-PyModule 'seaborn') -or (Test-PyModule 'plotly')) {
            $c3 = Invoke-VapHost @('selftest')
        } else {
            Write-Tag 'SKIP' '繪圖庫全缺席 — 誠實跳過（安裝：.\VIA_WorkflowEngine.ps1 setup vap）'
        }
    } else {
        Write-Tag 'SKIP' 'VAP 繪圖引擎未在位（git pull 取回分支最新版）'
    }
    Write-Host ''
    if (($c1 -eq 0) -and ($c2 -eq 0) -and ($c3 -eq 0)) {
        Write-Tag 'OK  ' 'ALL 綠燈。下一步範例：'
        Write-Host '        .\VIA_WorkflowEngine.ps1 sample                  # 產生範例流程檔'
        Write-Host '        .\VIA_WorkflowEngine.ps1 run via_sample_flow.yaml'
        Write-Host '        .\VIA_WorkflowEngine.ps1 master --dry-run        # VMT 九階段預覽'
        Write-Host '        .\VIA_WorkflowEngine.ps1 vap demo --out vap_demo # 28 圖型全渲染'
        exit 0
    }
    Write-Tag 'FAIL' ('backends={0}, workflow selftest={1}, vap selftest={2}' -f $c1, $c2, $c3)
    if ($c2 -ne 0) { exit $c2 } elseif ($c3 -ne 0) { exit $c3 } else { exit $c1 }
}

if ($Verb -eq 'vap') {
    $rest = @()
    if ($EngineArgs.Count -gt 1) { $rest = @($EngineArgs[1..($EngineArgs.Count - 1)]) }
    exit (Invoke-VapHost $rest)
}

function Get-RestArgs {
    if ($EngineArgs.Count -gt 1) { return @($EngineArgs[1..($EngineArgs.Count - 1)]) }
    return @()
}

if ($Verb -eq 'talib') {
    if (-not (Test-Path -LiteralPath $TALibEngine)) {
        Write-Tag 'FAIL' 'TALib 引擎缺席（git pull 取回分支最新版）'
        exit 1
    }
    $full = @($PyPre) + @($TALibEngine) + @(Get-RestArgs)
    & $PyExe $full
    exit $LASTEXITCODE
}

if ($Verb -eq 'theory') {
    if (-not (Test-Path -LiteralPath $TheoryAudit)) {
        Write-Tag 'FAIL' '理論稽核腳本缺席:Test-VIA-TheoryAudit.ps1（git pull 取回分支最新版）'
        exit 1
    }
    if ($Python -ne '') { $env:VIA_PYTHON = $Python }
    & $TheoryAudit
    exit $LASTEXITCODE
}

if ($Verb -eq 'chipwar') {
    if (-not (Test-Path -LiteralPath $ChipWarParams)) {
        Write-Tag 'FAIL' ('找不到 ChipWar 參數檔:{0}（git pull 取回分支最新版）' -f $ChipWarParams)
        exit 1
    }
    exit (Invoke-EngineHost (@('master', $ChipWarParams) + (Get-RestArgs)))
}

if (($Verb -eq 'mf') -or ($Verb -eq 'multifactor')) {
    if (-not (Test-Path -LiteralPath $MFParams)) {
        Write-Tag 'FAIL' ('找不到 MultiFactor 參數檔:{0}（git pull 取回分支最新版）' -f $MFParams)
        exit 1
    }
    exit (Invoke-EngineHost (@('master', $MFParams) + (Get-RestArgs)))
}

if ($Verb -eq 'dashboard') {
    if (-not (Test-Path -LiteralPath $ChipWarDash)) {
        Write-Tag 'FAIL' '找不到 ChipWar 儀表板引擎（git pull 取回分支最新版）'
        exit 1
    }
    & $PyExe (@($PyPre) + @($ChipWarDash)) 2>&1 | Out-Host
    $code = $LASTEXITCODE
    if (($code -eq 0) -and (Test-Path -LiteralPath $ChipWarIndex)) {
        Write-Tag 'OK  ' ('儀表板:{0}' -f $ChipWarIndex)
    } elseif ($code -ne 0) {
        Write-Tag 'INFO' '若 staging 缺件,先跑:.\VIA_WorkflowEngine.ps1 chipwar'
    }
    exit $code
}

if ($Verb -eq 'flowsystem') {
    $engDir = Join-Path $FlowV2Dir 'engines'
    $n = 0
    if (Test-Path -LiteralPath $engDir) {
        $n = @(Get-ChildItem -LiteralPath $engDir -Filter 'flow_*.py' -File -ErrorAction SilentlyContinue).Count
    }
    if ($n -lt 5) {
        Write-Tag 'FAIL' ('FlowSystem v2 引擎未到位（flow_*.py 在位 {0}/16）— README 與啟動器已歸檔,' -f $n)
        Write-Host '        請把 VIA_FlowSystem (2) 的 engines/config/data 檔案上傳(拖檔案或整包 zip),'
        Write-Host '        到位後本動詞會自動委派 Activate-VIAFlowSystem.ps1 跑 synth→calibrate→run→ui。'
        exit 1
    }
    Write-Tag 'OK  ' ('flow_*.py 在位 {0} 支 — 委派 Activate-VIAFlowSystem.ps1' -f $n)
    & $FlowV2Launch @(Get-RestArgs)
    exit $LASTEXITCODE
}

if ($Verb -eq 'status') {
    Write-Host '════════════════════════════════════════════════════════'
    Write-Host ' VIA 全模組在位/缺席全景（本 session 建設）'
    Write-Host '════════════════════════════════════════════════════════'
    $rows = @(
        @{ n = '工作流引擎 VIA_WorkflowEngine.py';  p = $EnginePath },
        @{ n = 'VAP seaborn+plotly 引擎(28型)';    p = $VapEngine },
        @{ n = 'ChipWar 13 階段參數檔';            p = $ChipWarParams },
        @{ n = 'ChipWar × VAP 儀表板引擎';         p = $ChipWarDash },
        @{ n = 'ChipWar 儀表板產物 index';         p = $ChipWarIndex },
        @{ n = 'MultiFactor 參數檔';               p = $MFParams },
        @{ n = 'MultiFactor SHA256 manifest';      p = $MFManifest },
        @{ n = 'FlowSystem v2 啟動器';             p = $FlowV2Launch },
        @{ n = 'TALib 指標引擎(adj 鐵律)';          p = $TALibEngine },
        @{ n = '理論稽核 Test-VIA-TheoryAudit.ps1'; p = $TheoryAudit }
    )
    foreach ($r in $rows) {
        $mark = if (Test-Path -LiteralPath $r.p) { '在位' } else { '缺席' }
        Write-Host ('  [{0}] {1}' -f $mark, $r.n)
    }
    $engDir = Join-Path $FlowV2Dir 'engines'
    $n = 0
    if (Test-Path -LiteralPath $engDir) {
        $n = @(Get-ChildItem -LiteralPath $engDir -Filter 'flow_*.py' -File -ErrorAction SilentlyContinue).Count
    }
    Write-Host ('  [{0}] FlowSystem v2 引擎 flow_*.py（{1}/16;缺=待上傳）' -f ($(if ($n -ge 16) { '在位' } else { '缺席' })), $n)
    foreach ($mod in @('yaml', 'seaborn', 'plotly', 'duckdb', 'scipy', 'sklearn')) {
        $mark = if (Test-PyModule $mod) { '在位' } else { '缺席' }
        Write-Host ('  [{0}] python 依賴 {1}' -f $mark, $mod)
    }
    exit 0
}

if ($Verb -eq 'everything') {
    Write-Host '━━ EVERYTHING:本 session 全部建設一支到底 ━━━━━━━━━━━━'
    $steps = @()
    Write-Host '── [1/6] backends 十庫探測 ──'
    $steps += @{ n = 'backends'; c = (Invoke-EngineHost @('backends')) }
    Write-Host '── [2/6] 工作流 selftest ──'
    $steps += @{ n = 'workflow selftest'; c = (Invoke-EngineHost @('selftest')) }
    Write-Host '── [3/6] VAP 繪圖 selftest ──'
    if ((Test-Path -LiteralPath $VapEngine) -and ((Test-PyModule 'seaborn') -or (Test-PyModule 'plotly'))) {
        $steps += @{ n = 'vap selftest'; c = (Invoke-VapHost @('selftest')) }
    } else {
        Write-Tag 'SKIP' 'VAP 引擎或繪圖庫缺席'
        $steps += @{ n = 'vap selftest'; c = -1 }
    }
    Write-Host '── [4/6] ChipWar 13 階段全鏈 ──'
    if ((Test-Path -LiteralPath $ChipWarParams) -and (Test-PyModule 'duckdb')) {
        $steps += @{ n = 'chipwar chain'; c = (Invoke-EngineHost @('master', $ChipWarParams)) }
    } else {
        Write-Tag 'SKIP' 'ChipWar 參數檔或 duckdb 缺席（setup chipwar 可裝依賴）'
        $steps += @{ n = 'chipwar chain'; c = -1 }
    }
    Write-Host '── [5/6] MultiFactor 引擎 ──'
    if ((Test-Path -LiteralPath $MFParams) -and (Test-PyModule 'scipy')) {
        $steps += @{ n = 'multifactor'; c = (Invoke-EngineHost @('master', $MFParams)) }
    } else {
        Write-Tag 'SKIP' 'MultiFactor 參數檔或 scipy 缺席'
        $steps += @{ n = 'multifactor'; c = -1 }
    }
    Write-Host '── [6/6] 理論稽核（PS 獨立甲骨文 14 斷言）──'
    if (Test-Path -LiteralPath $TheoryAudit) {
        if ($Python -ne '') { $env:VIA_PYTHON = $Python }
        & $TheoryAudit
        $steps += @{ n = 'theory audit'; c = $LASTEXITCODE }
    } else {
        Write-Tag 'SKIP' '理論稽核腳本缺席（git pull 取回分支最新版）'
        $steps += @{ n = 'theory audit'; c = -1 }
    }
    Write-Host ''
    Write-Host '━━ EVERYTHING 總結 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
    $bad = 0
    foreach ($s in $steps) {
        $mark = if ($s.c -eq 0) { 'PASS' } elseif ($s.c -eq -1) { 'SKIP' } else { $bad++; 'FAIL' }
        Write-Host ('  [{0}] {1}' -f $mark, $s.n)
    }
    if (Test-Path -LiteralPath $ChipWarIndex) {
        Write-Host ('  儀表板:{0}' -f $ChipWarIndex)
    }
    if ($bad -eq 0) {
        Write-Tag 'OK  ' 'EVERYTHING 綠燈(SKIP 為誠實缺席,非失敗)'
        exit 0
    }
    Write-Tag 'FAIL' ('{0} 步失敗' -f $bad)
    exit 1
}

if ($Verb -eq '') {
    Write-Host '════════════════════════════════════════════════════════'
    Write-Host (' VIA_WorkflowEngine 啟動器（Python {0} @ {1}）' -f $Py.Ver, $PyExe)
    Write-Host ' wrapper：doctor|setup [vap|chipwar]|all|vap …|talib …|theory|chipwar|mf|dashboard|flowsystem|status|everything'
    Write-Host '════════════════════════════════════════════════════════'
    $code = Invoke-EngineHost @()
    exit $code
}

# ── 預設：原樣透傳（stdout 保持可管線，例如 run 的 JSON | ConvertFrom-Json）──
$Full = @($PyPre) + @($EnginePath) + @($EngineArgs)
& $PyExe $Full
exit $LASTEXITCODE

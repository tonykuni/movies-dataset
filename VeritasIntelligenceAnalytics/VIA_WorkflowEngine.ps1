<#
VIA_WorkflowEngine.ps1 — Windows 一鍵啟動器（ONE POWERSHELL TO HANDLE ALL）
===========================================================================
包辦 Windows 上執行 VIA_WorkflowEngine.py 的全部前置：
  1. Python 偵測：py -3 → python → python3（需 3.8+；自動擋 Microsoft Store 假棒）
  2. UTF-8 主控台（中文輸出不亂碼）+ PYTHONUTF8/PYTHONIOENCODING
  3. 引擎路徑解析（以本檔所在目錄定位 — 任何 cwd 都能跑）
  4. 參數原樣透傳引擎全部動詞，外加三個 wrapper 動詞

WRAPPER 動詞
  doctor   環境診斷（interpreter / 引擎在位 / PyYAML / backends 探測）
  setup    安裝選配依賴 PyYAML（--user）；十庫安裝指令僅列印、絕不代裝
  all      backends → selftest 一鍵全驗證

引擎動詞（透傳）
  backends | demo [all|dag|saga|resume|fsm|graph|events|crew|decorators|cron|dsl|export]
  run <file> [--backend ...] [--param k=v] | resume <file> <run_id>
  export <file> --format <fmt> [--out 檔案] | scaffold <target> | runs | selftest

USAGE
  .\VIA_WorkflowEngine.ps1 all
  .\VIA_WorkflowEngine.ps1 demo all
  .\VIA_WorkflowEngine.ps1 run flow.yaml --backend native
  .\VIA_WorkflowEngine.ps1 export flow.yaml --format dagu --out flow_dagu.yaml
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

$Verb = ''
if ($EngineArgs.Count -gt 0) { $Verb = ([string]$EngineArgs[0]).ToLowerInvariant() }

# ── wrapper 動詞 ───────────────────────────────────────────────────────────
if ($Verb -eq 'doctor') {
    Write-Host '════════════════════════════════════════════════════════'
    Write-Host ' VIA_WorkflowEngine doctor — 環境診斷'
    Write-Host '════════════════════════════════════════════════════════'
    Write-Tag 'OK  ' ('Python {0}  （{1} {2}）' -f $Py.Ver, $PyExe, ($PyPre -join ' '))
    Write-Tag 'OK  ' ('引擎  {0}' -f $EnginePath)
    & $PyExe (@($PyPre) + @('-c', 'import yaml')) 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Tag 'OK  ' 'PyYAML 在位（YAML DSL 已啟用）'
    } else {
        Write-Tag 'INFO' 'PyYAML 缺席 — JSON DSL 照常全功能；要 YAML 就跑：.\VIA_WorkflowEngine.ps1 setup'
    }
    Write-Host ''
    $code = Invoke-EngineHost @('backends')
    exit $code
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
    Write-Host '── [1/2] backends 十庫在位探測 ──────────────────────────'
    $c1 = Invoke-EngineHost @('backends')
    Write-Host ''
    Write-Host '── [2/2] selftest 全功能自我驗證 ────────────────────────'
    $c2 = Invoke-EngineHost @('selftest')
    Write-Host ''
    if (($c1 -eq 0) -and ($c2 -eq 0)) {
        Write-Tag 'OK  ' 'ALL 綠燈。下一步範例：'
        Write-Host '        .\VIA_WorkflowEngine.ps1 demo all'
        Write-Host '        .\VIA_WorkflowEngine.ps1 run flow.yaml'
        Write-Host '        .\VIA_WorkflowEngine.ps1 export flow.yaml --format reactflow'
        exit 0
    }
    Write-Tag 'FAIL' ('backends exit={0}, selftest exit={1}' -f $c1, $c2)
    if ($c2 -ne 0) { exit $c2 } else { exit $c1 }
}

if ($Verb -eq '') {
    Write-Host '════════════════════════════════════════════════════════'
    Write-Host (' VIA_WorkflowEngine 啟動器（Python {0} @ {1}）' -f $Py.Ver, $PyExe)
    Write-Host ' wrapper 動詞：doctor | setup | all    其餘動詞透傳引擎 ↓'
    Write-Host '════════════════════════════════════════════════════════'
    $code = Invoke-EngineHost @()
    exit $code
}

# ── 預設：原樣透傳（stdout 保持可管線，例如 run 的 JSON | ConvertFrom-Json）──
$Full = @($PyPre) + @($EnginePath) + @($EngineArgs)
& $PyExe $Full
exit $LASTEXITCODE

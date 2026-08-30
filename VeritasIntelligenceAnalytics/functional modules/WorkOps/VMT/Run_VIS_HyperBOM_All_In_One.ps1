param(
    [string]$BaseDir = (Get-Location).Path,
    [string]$InputCsvFolder = "",
    [string]$RootPartNumber = "ASM-SVR-001",
    [double]$BuildQty = 100,
    [int]$MaxScanFiles = 500,
    [int]$ChildTimeoutSec = 180,
    [bool]$OpenHtml = $true,
    [bool]$KeepPowerShellOpen = $true
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

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function def_NewUtf8NoBomEncoding {
    return [System.Text.UTF8Encoding]::new($false)
}

function def_WriteText {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Text
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Text, (def_NewUtf8NoBomEncoding))
}

function def_WriteJson {
    param(
        [Parameter(Mandatory=$true)]$Data,
        [Parameter(Mandatory=$true)][string]$Path,
        [int]$Depth = 80
    )
    $json = $Data | ConvertTo-Json -Depth $Depth
    def_WriteText -Path $Path -Text $json
}

function def_WriteBanner {
    param([string]$Title)
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def $Title" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
}

function def_WriteStep {
    param(
        [int]$Percent,
        [string]$Activity,
        [string]$Status,
        [string]$Color = "White"
    )
    if ($Percent -lt 0) { $Percent = 0 }
    if ($Percent -gt 100) { $Percent = 100 }
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $Percent
    Write-Host ("[{0,3}%] {1}" -f $Percent, $Status) -ForegroundColor $Color
}

function def_GetRyg {
    param([string]$Status)
    $s = ($Status + "").Trim().ToUpperInvariant()
    if ($s -in @("PASS","OK","GREEN","FOUND","READY","LOW")) { return "GREEN" }
    if ($s -in @("WARN","WARNING","YELLOW","SKIP","MISSING_OPTIONAL","MEDIUM")) { return "YELLOW" }
    if ($s -in @("FAIL","ERROR","RED","MISSING","BLOCK","HIGH","CRITICAL","TIMEOUT")) { return "RED" }
    return "YELLOW"
}

function def_AddRow {
    param(
        [System.Collections.ArrayList]$Rows,
        [string]$Matrix,
        [string]$Name,
        [string]$Status,
        [string]$Risk,
        [string]$Message,
        [string]$Path = "",
        [int]$Expected = 0,
        [int]$Actual = 0
    )
    $row = [ordered]@{
        matrix   = $Matrix
        name     = $Name
        status   = $Status
        ryg      = def_GetRyg $Status
        risk     = $Risk
        expected = $Expected
        actual   = $Actual
        message  = $Message
        path     = $Path
    }
    [void]$Rows.Add([pscustomobject]$row)
}

function def_FindFirstFile {
    param(
        [string]$Root,
        [string[]]$Names
    )
    foreach ($n in $Names) {
        $direct = Join-Path $Root $n
        if (Test-Path -LiteralPath $direct) { return (Resolve-Path -LiteralPath $direct).Path }
    }
    foreach ($n in $Names) {
        $found = Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq $n } |
            Select-Object -First 1
        if ($null -ne $found) { return $found.FullName }
    }
    return ""
}

function def_FindPython {
    $candidates = @("python", "py")
    foreach ($c in $candidates) {
        try {
            $cmd = Get-Command $c -ErrorAction Stop
            return $cmd.Source
        } catch {
        }
    }
    return ""
}

function def_InvokeChild {
    param(
        [Parameter(Mandatory=$true)][string]$FileName,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [Parameter(Mandatory=$true)][string]$WorkDir,
        [Parameter(Mandatory=$true)][string]$LogPrefix,
        [int]$TimeoutSec = 180
    )
    $result = [ordered]@{
        file       = $FileName
        arguments  = $Arguments
        work_dir   = $WorkDir
        exit_code  = $null
        timed_out  = $false
        status     = "UNKNOWN"
        stdout_log = "$LogPrefix.stdout.txt"
        stderr_log = "$LogPrefix.stderr.txt"
        message    = ""
    }

    $stdoutBuilder = [System.Text.StringBuilder]::new()
    $stderrBuilder = [System.Text.StringBuilder]::new()
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FileName
    foreach ($a in $Arguments) { [void]$psi.ArgumentList.Add($a) }
    $psi.WorkingDirectory = $WorkDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi

    $outHandler = [System.Diagnostics.DataReceivedEventHandler]{
        param($sender, $eventArgs)
        if ($null -ne $eventArgs.Data) { [void]$stdoutBuilder.AppendLine($eventArgs.Data) }
    }
    $errHandler = [System.Diagnostics.DataReceivedEventHandler]{
        param($sender, $eventArgs)
        if ($null -ne $eventArgs.Data) { [void]$stderrBuilder.AppendLine($eventArgs.Data) }
    }
    $proc.add_OutputDataReceived($outHandler)
    $proc.add_ErrorDataReceived($errHandler)

    try {
        [void]$proc.Start()
        $proc.BeginOutputReadLine()
        $proc.BeginErrorReadLine()
        $ok = $proc.WaitForExit($TimeoutSec * 1000)
        if (-not $ok) {
            $result.timed_out = $true
            try { $proc.Kill($true) } catch { try { $proc.Kill() } catch {} }
            $result.status = "TIMEOUT"
            $result.message = "Child process timeout; only this child process was stopped."
        } else {
            $proc.WaitForExit()
            $result.exit_code = $proc.ExitCode
            if ($proc.ExitCode -eq 0) {
                $result.status = "PASS"
                $result.message = "Completed."
            } else {
                $result.status = "FAIL"
                $result.message = "Non-zero exit code: $($proc.ExitCode)"
            }
        }
    } catch {
        $result.status = "ERROR"
        $result.message = $_.Exception.Message
    } finally {
        $proc.remove_OutputDataReceived($outHandler)
        $proc.remove_ErrorDataReceived($errHandler)
        $proc.Dispose()
    }

    def_WriteText -Path $result.stdout_log -Text $stdoutBuilder.ToString()
    def_WriteText -Path $result.stderr_log -Text $stderrBuilder.ToString()
    return [pscustomobject]$result
}

function def_GetToolRegistry {
    $registry = [ordered]@{
        version = "1.0.0"
        name = "Decision Studio Panoramic Analyzer Tool Registry"
        policy = "local-free-offline-first; registry only; no auto-install"
        languages = @("python", "javascript", "powershell")
        expected_tool_count = 270
        functions = [ordered]@{
            panoramic_analysis = [ordered]@{
                python = @("pylint","flake8","mypy","bandit","radon","vulture","prospector","pyright","rope","jedi")
                javascript = @("eslint","typescript","sonarjs-local","dependency-cruiser","madge","webpack-bundle-analyzer","plato","eslint-plugin-import","jscodeshift","ts-morph")
                powershell = @("psscriptanalyzer","psrule","pester","scriptanalyzerrules","psdepend","psprofiler","psframework","psgraph","plaster","custom-ast-analyzer")
            }
            error_identification = [ordered]@{
                python = @("pylint","pyflakes","flake8","mypy","pyright","pytest","unittest","coverage","nose2","bandit")
                javascript = @("eslint","typescript","jest","mocha","ava","eslint-plugin-node","eslint-plugin-promise","node-trace-warnings","c8","nyc")
                powershell = @("psscriptanalyzer","pester","psframework-logging","psrule","invoke-scriptanalyzer","pslogging","psprofiler","transcript-logging","custom-ast-rules","psreadline-diagnostics")
            }
            sandbox_testing = [ordered]@{
                python = @("venv","virtualenv","tox","nox","pytest-fixtures","unittest-mock","subprocess-sandbox","pyenv","docker-local","hypothesis")
                javascript = @("node-vm","jest-sandbox","mocha-isolated","ts-node-isolated","docker-local","nvm","playwright-local","sinon","proxyquire","pnpm-workspaces")
                powershell = @("pssession-isolation","start-job","runspacepool","pester-isolated","temp-psmodulepath","jea","constrained-language-mode","windows-sandbox","docker-windows","sandbox-wrapper")
            }
            ast_analysis = [ordered]@{
                python = @("ast","astroid","libcst","parso","redbaron","typed-ast","jedi","rope","bowler","pylsp")
                javascript = @("babel-parser","esprima","acorn","recast","jscodeshift","ts-morph","typescript-compiler-api","eslint-parser","meriyah","swc-parser")
                powershell = @("powershell-ast","psscriptanalyzer-ast","psparser","scriptanalyzerrules","custom-ast-visitors","psgraph-ast","psframework-ast","pester-ast-checks","dotnet-ast-reflection","custom-ast-refactor")
            }
            interface_contract_detection = [ordered]@{
                python = @("mypy-protocols","pydantic","dataclasses","jsonschema","marshmallow","attrs","inspect","pyi-stubs","fastapi-schema-local","drf-schema-local")
                javascript = @("typescript-interfaces","ts-json-schema-generator","ajv-local","io-ts","zod","jsdoc-tsserver","swagger-jsdoc-local","quicktype-cli","eslint-plugin-jsdoc","openapi-generator-local")
                powershell = @("param-type-blocks","powershell-classes","test-json","psscriptanalyzer-param-rules","dsc-schema","module-manifest-schema","psrule-contracts","pester-contract-tests","import-powershelldatafile","comment-help-schema")
            }
            syntax_compile = [ordered]@{
                python = @("py_compile","compileall","pylint","flake8","pyflakes","mypy","pyright","black","isort","bandit")
                javascript = @("typescript-compiler","babel-cli","eslint","flow","swc","esbuild","webpack","rollup","parcel","node-check")
                powershell = @("psscriptanalyzer-syntax","scriptblock-create","test-modulemanifest","import-module-verbose","pester-syntax-tests","psparser","scriptanalyzerrules","psreadline-syntax","powershellget-testinstall","ast-parse-only")
            }
            hydra_risk_detection = [ordered]@{
                python = @("pylint-cyclic-import","pydeps","snakefood","pipdeptree","radon","vulture","mypy-cross-module","bandit-security-chains","networkx-dep-graph","rope-refactor-graph")
                javascript = @("madge","dependency-cruiser","eslint-import-rules","webpack-analyzer","ts-morph-graph","typescript-project-refs","sonarjs-local","plato","depcheck","jscodeshift")
                powershell = @("psscriptanalyzer-deps","ast-import-graph","psdepend","psmodulepath-analyzer","psgraph-dep-map","pester-dep-tests","dsc-dep-graph","scriptanalyzerrules","module-manifest-analysis","dotnet-reflection-deps")
            }
            anchor_point_detection = [ordered]@{
                python = @("ast-lineno","libcst-loc","parso-loc","jedi-symbol","rope-refactor","bowler-patterns","ripgrep","tree-sitter-python","pylsp","redbaron")
                javascript = @("babel-ast-loc","ts-morph-loc","eslint-sourcecode","recast","jscodeshift","tree-sitter-js","vscode-tsserver-local","ripgrep","source-map","prettier-stable")
                powershell = @("ast-extent","psparser-tokens","psscriptanalyzer-context","custom-ast-visitors","vscode-powershell-api","pester-line-assert","transcript-line-ref","psreadline-markers","region-tags","anchor-comments")
            }
            integration_scheduling = [ordered]@{
                python = @("tox","nox","invoke","doit","make","airflow-local","prefect-local","celery-local","cron-venv","fabric")
                javascript = @("npm-scripts","yarn","pnpm","gulp","grunt","nx","lerna","turbo","node-cron","pm2-local")
                powershell = @("psake","invoke-build","scheduledtasks","register-scheduledjob","pester-pipelines","gha-local-runner","azure-devops-agent","start-job","runspacepool","dsc-scheduled-configs")
            }
        }
    }
    return $registry
}

function def_CountRegistryTools {
    param($Registry)
    $count = 0
    foreach ($fn in $Registry.functions.Keys) {
        foreach ($lang in $Registry.functions[$fn].Keys) {
            $count += @($Registry.functions[$fn][$lang]).Count
        }
    }
    return $count
}

function def_GetInventory {
    param([string]$Root, [int]$Limit)
    $files = Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "\\_vis_hyperbom_runs\\" } |
        Select-Object -First $Limit
    $rows = New-Object System.Collections.ArrayList
    foreach ($f in $files) {
        $ext = if ($f.Extension) { $f.Extension.ToLowerInvariant() } else { "[no_ext]" }
        [void]$rows.Add([pscustomobject]@{
            name = $f.Name
            extension = $ext
            size_bytes = $f.Length
            last_write = $f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            path = $f.FullName
        })
    }
    return $rows
}

function def_SummarizeInventory {
    param([System.Collections.ArrayList]$Inventory)
    $groups = $Inventory | Group-Object extension | Sort-Object Name
    $rows = New-Object System.Collections.ArrayList
    foreach ($g in $groups) {
        [void]$rows.Add([pscustomobject]@{
            extension = $g.Name
            count = $g.Count
            status = if ($g.Count -gt 0) { "PASS" } else { "WARN" }
        })
    }
    return $rows
}

function def_ParsePowerShellAst {
    param([string[]]$Paths)
    $rows = New-Object System.Collections.ArrayList
    foreach ($p in $Paths) {
        try {
            $tokens = $null
            $errors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$tokens, [ref]$errors)
            $fnCount = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)).Count
            [void]$rows.Add([pscustomobject]@{
                file = Split-Path -Leaf $p
                status = if (@($errors).Count -eq 0) { "PASS" } else { "FAIL" }
                errors = @($errors).Count
                functions = $fnCount
                path = $p
            })
        } catch {
            [void]$rows.Add([pscustomobject]@{
                file = Split-Path -Leaf $p
                status = "ERROR"
                errors = 1
                functions = 0
                path = $p
            })
        }
    }
    return $rows
}

function def_GetHtmlTable {
    param($Rows, [string]$Title)
    $arr = @($Rows)
    if ($arr.Count -eq 0) { return "<section class='card'><h2>$Title</h2><p>No rows.</p></section>" }
    $props = $arr[0].PSObject.Properties.Name
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("<section class='card'><h2>$Title</h2><table><thead><tr>")
    foreach ($p in $props) { [void]$sb.AppendLine("<th>$([System.Web.HttpUtility]::HtmlEncode($p))</th>") }
    [void]$sb.AppendLine("</tr></thead><tbody>")
    foreach ($r in $arr) {
        $cls = ""
        if ($r.PSObject.Properties.Name -contains "status") { $cls = def_GetRyg ($r.status + "") }
        elseif ($r.PSObject.Properties.Name -contains "ryg") { $cls = $r.ryg }
        [void]$sb.AppendLine("<tr class='$cls'>")
        foreach ($p in $props) {
            $v = $r.$p
            [void]$sb.AppendLine("<td>$([System.Web.HttpUtility]::HtmlEncode(($v | Out-String).Trim()))</td>")
        }
        [void]$sb.AppendLine("</tr>")
    }
    [void]$sb.AppendLine("</tbody></table></section>")
    return $sb.ToString()
}

function def_BuildGovernanceHtml {
    param(
        [string]$Path,
        $Summary,
        $MatrixRows,
        $InventorySummary,
        $AstRows,
        $ProcessRows,
        $RegistryFlatRows
    )
    Add-Type -AssemblyName System.Web
    $css = @'
body{font-family:Inter,"Noto Sans TC",Arial,sans-serif;background:#F9F9F6;color:#1F2933;margin:24px}h1{font-size:24px;margin-bottom:6px}h2{font-size:18px}.grid{display:grid;grid-template-columns:repeat(4,minmax(160px,1fr));gap:12px}.kpi{background:#fff;border:1px solid #DFECEA;border-radius:14px;padding:14px}.kpi b{font-size:24px}.card{background:#fff;border:1px solid #DFECEA;border-radius:14px;padding:16px;margin:14px 0;box-shadow:0 2px 9px rgba(31,41,51,.06)}table{border-collapse:collapse;width:100%;font-size:12px}th{background:#0F766E;color:white;text-align:left}td,th{border:1px solid #D1D5DB;padding:6px;vertical-align:top}.GREEN td{background:#DCFCE7}.YELLOW td{background:#FEF3C7}.RED td{background:#FEE2E2}.muted{color:#6B7C78}.mono{font-family:"Cascadia Mono",Consolas,monospace;font-size:12px}.banner{border-left:6px solid #0F766E;padding-left:12px}.warn{border-left-color:#B7791F}.fail{border-left-color:#B91C1C}
'@
    $body = [System.Text.StringBuilder]::new()
    [void]$body.AppendLine("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIS HyperBOM All-In-One Governance Matrix</title><style>$css</style></head><body>")
    [void]$body.AppendLine("<h1>VIS HyperBOM Matrix · All-In-One Governance Matrix</h1>")
    [void]$body.AppendLine("<p class='muted'>append-only · run-local · no canonical mutation · no SAP/PLM write-back · recommendation-only</p>")
    [void]$body.AppendLine("<section class='grid'>")
    [void]$body.AppendLine("<div class='kpi'><span>Gate</span><br><b>$($Summary.gate)</b></div>")
    [void]$body.AppendLine("<div class='kpi'><span>Files Scanned</span><br><b>$($Summary.files_scanned)</b></div>")
    [void]$body.AppendLine("<div class='kpi'><span>Registry Tools</span><br><b>$($Summary.registry_tools_actual)/$($Summary.registry_tools_expected)</b></div>")
    [void]$body.AppendLine("<div class='kpi'><span>Run Dir</span><br><span class='mono'>$([System.Web.HttpUtility]::HtmlEncode($Summary.run_dir))</span></div>")
    [void]$body.AppendLine("</section>")
    [void]$body.AppendLine((def_GetHtmlTable -Rows $MatrixRows -Title "RYG Master Matrix"))
    [void]$body.AppendLine((def_GetHtmlTable -Rows $ProcessRows -Title "Execution / Sandbox Test Matrix"))
    [void]$body.AppendLine((def_GetHtmlTable -Rows $InventorySummary -Title "Quantity Validation by File Type"))
    [void]$body.AppendLine((def_GetHtmlTable -Rows $AstRows -Title "PowerShell AST / Syntax Matrix"))
    [void]$body.AppendLine((def_GetHtmlTable -Rows $RegistryFlatRows -Title "Decision Studio Tool Registry Matrix"))
    [void]$body.AppendLine("</body></html>")
    def_WriteText -Path $Path -Text $body.ToString()
}

function def_FlattenRegistry {
    param($Registry)
    $rows = New-Object System.Collections.ArrayList
    foreach ($fn in $Registry.functions.Keys) {
        foreach ($lang in $Registry.functions[$fn].Keys) {
            foreach ($tool in @($Registry.functions[$fn][$lang])) {
                [void]$rows.Add([pscustomobject]@{
                    function = $fn
                    language = $lang
                    tool = $tool
                    local_free_offline = "YES"
                    status = "REGISTRY"
                })
            }
        }
    }
    return $rows
}

try {
    def_WriteBanner -Title "VIS HyperBOM Matrix · ALL-IN-ONE SAFE RUNNER"
    def_WriteStep -Percent 3 -Activity "VIS HyperBOM All-In-One" -Status "Boot: safety policy loaded" -Color Cyan

    $BaseDir = (Resolve-Path -LiteralPath $BaseDir).Path
    $runId = "RUN_" + (Get-Date -Format "yyyyMMdd_HHmmss") + "_VIS_HYPERBOM_ALL_IN_ONE"
    $runRoot = Join-Path $BaseDir "_vis_hyperbom_runs"
    $runDir = Join-Path $runRoot $runId
    $logDir = Join-Path $runDir "logs"
    $registryDir = Join-Path $runDir "registry"
    $matrixDir = Join-Path $runDir "matrix"
    $sandboxDir = Join-Path $runDir "sandbox"
    foreach ($d in @($runDir,$logDir,$registryDir,$matrixDir,$sandboxDir)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }

    $matrixRows = New-Object System.Collections.ArrayList
    $processRows = New-Object System.Collections.ArrayList

    def_WriteStep -Percent 8 -Activity "VIS HyperBOM All-In-One" -Status "Run-local folder created: $runDir" -Color Green
    def_AddRow -Rows $matrixRows -Matrix "Safety" -Name "Append-only run folder" -Status "PASS" -Risk "LOW" -Message "All outputs are written under this run folder only." -Path $runDir
    def_AddRow -Rows $matrixRows -Matrix "Safety" -Name "SAP/PLM write-back" -Status "PASS" -Risk "LOW" -Message "No SAP/PLM/MS Project write-back is executed; recommendation-only." -Path ""

    $zipPath = def_FindFirstFile -Root $BaseDir -Names @("VIS_HyperBOM_Matrix_Package.zip")
    $extractDir = Join-Path $sandboxDir "package_extract"
    if ($zipPath) {
        def_WriteStep -Percent 12 -Activity "VIS HyperBOM All-In-One" -Status "Package zip found; extracting read-only copy" -Color Cyan
        Expand-Archive -LiteralPath $zipPath -DestinationPath $extractDir -Force
        def_AddRow -Rows $matrixRows -Matrix "Input" -Name "Package zip" -Status "PASS" -Risk "LOW" -Message "Extracted to run-local sandbox copy." -Path $zipPath
    } else {
        def_AddRow -Rows $matrixRows -Matrix "Input" -Name "Package zip" -Status "WARN" -Risk "LOW" -Message "No package zip found. Will search BaseDir directly." -Path $BaseDir
    }

    $searchRoots = @($BaseDir)
    if (Test-Path -LiteralPath $extractDir) { $searchRoots = @($extractDir, $BaseDir) }
    $enginePath = ""
    $schemaPath = ""
    $templatePath = ""
    $promptPath = ""
    foreach ($sr in $searchRoots) {
        if (-not $enginePath) { $enginePath = def_FindFirstFile -Root $sr -Names @("vis_hyperbom_matrix_engine.py") }
        if (-not $schemaPath) { $schemaPath = def_FindFirstFile -Root $sr -Names @("VIS_HyperBOM_Schema_Spec.json") }
        if (-not $templatePath) { $templatePath = def_FindFirstFile -Root $sr -Names @("VIS_HyperBOM_Matrix_Template.xlsx") }
        if (-not $promptPath) { $promptPath = def_FindFirstFile -Root $sr -Names @("VIS_HyperBOM_AI_Prompt_Pack.md") }
    }

    $expectedFiles = @(
        @{name="Python Engine"; path=$enginePath; required=$true},
        @{name="Schema Spec"; path=$schemaPath; required=$false},
        @{name="Excel Template"; path=$templatePath; required=$false},
        @{name="AI Prompt Pack"; path=$promptPath; required=$false}
    )
    foreach ($ef in $expectedFiles) {
        $status = if ($ef.path) { "PASS" } elseif ($ef.required) { "FAIL" } else { "WARN" }
        $risk = if ($status -eq "FAIL") { "HIGH" } else { "LOW" }
        def_AddRow -Rows $matrixRows -Matrix "File Presence" -Name $ef.name -Status $status -Risk $risk -Message "File lookup result." -Path ($ef.path + "") -Expected 1 -Actual $(if ($ef.path) {1} else {0})
    }

    def_WriteStep -Percent 18 -Activity "VIS HyperBOM All-In-One" -Status "Generating Decision Studio Tool Registry" -Color Cyan
    $registry = def_GetToolRegistry
    $registryActual = def_CountRegistryTools -Registry $registry
    $registryPath = Join-Path $registryDir "decision_studio_tool_registry.json"
    def_WriteJson -Data $registry -Path $registryPath
    $registryFlatRows = def_FlattenRegistry -Registry $registry
    $registryStatus = if ($registryActual -eq 270) { "PASS" } else { "WARN" }
    def_AddRow -Rows $matrixRows -Matrix "Tool Registry" -Name "270 local/free/offline tools" -Status $registryStatus -Risk "LOW" -Message "Generated Decision Studio registry." -Path $registryPath -Expected 270 -Actual $registryActual

    $agentProfile = [ordered]@{
        version = "1.0.0"
        name = "VIS HyperBOM Decision Studio Agent Profile"
        stages = @(
            @{stage="panoramic_analysis"; tools=@("python-ast","powershell-ast","file-inventory","registry-scan")},
            @{stage="sandbox_testing"; tools=@("python-self-test","py_compile","run-local-output")},
            @{stage="hydra_detection"; tools=@("duplicate-basename","multi-writer-risk","reference-check")},
            @{stage="visual_matrix"; tools=@("html-matrix","ryg-indicators","quantity-validation")}
        )
        policy = [ordered]@{
            canonical_mutation = $false
            sap_writeback = $false
            plm_writeback = $false
            delete_files = $false
            append_only = $true
            human_approval = $true
        }
    }
    $agentProfilePath = Join-Path $registryDir "decision_studio_agent_profile.json"
    def_WriteJson -Data $agentProfile -Path $agentProfilePath
    def_AddRow -Rows $matrixRows -Matrix "Agent Profile" -Name "AI Agent Tool Profile" -Status "PASS" -Risk "LOW" -Message "Generated safe agent profile." -Path $agentProfilePath

    def_WriteStep -Percent 26 -Activity "VIS HyperBOM All-In-One" -Status "Scanning files and quantities" -Color Cyan
    $inventory = def_GetInventory -Root $BaseDir -Limit $MaxScanFiles
    $inventorySummary = def_SummarizeInventory -Inventory $inventory
    $inventoryPath = Join-Path $matrixDir "file_inventory.json"
    def_WriteJson -Data $inventory -Path $inventoryPath
    def_AddRow -Rows $matrixRows -Matrix "Inventory" -Name "File inventory" -Status "PASS" -Risk "LOW" -Message "Scanned files within limit." -Path $inventoryPath -Expected $MaxScanFiles -Actual $inventory.Count

    $psFiles = @($inventory | Where-Object { $_.extension -eq ".ps1" } | Select-Object -ExpandProperty path)
    $astRows = New-Object System.Collections.ArrayList
    if ($psFiles.Count -gt 0) {
        def_WriteStep -Percent 34 -Activity "VIS HyperBOM All-In-One" -Status "PowerShell AST parsing" -Color Cyan
        $astRows = def_ParsePowerShellAst -Paths $psFiles
        $astFail = @($astRows | Where-Object { $_.status -ne "PASS" }).Count
        def_AddRow -Rows $matrixRows -Matrix "AST" -Name "PowerShell AST parse" -Status $(if ($astFail -eq 0) {"PASS"} else {"FAIL"}) -Risk $(if ($astFail -eq 0) {"LOW"} else {"HIGH"}) -Message "AST errors: $astFail" -Path "" -Expected $psFiles.Count -Actual ($psFiles.Count - $astFail)
    } else {
        def_AddRow -Rows $matrixRows -Matrix "AST" -Name "PowerShell AST parse" -Status "WARN" -Risk "LOW" -Message "No .ps1 files found in scan scope." -Path ""
    }

    $pythonExe = def_FindPython
    if ($pythonExe) {
        def_AddRow -Rows $matrixRows -Matrix "Runtime" -Name "Python executable" -Status "PASS" -Risk "LOW" -Message "Python found." -Path $pythonExe
    } else {
        def_AddRow -Rows $matrixRows -Matrix "Runtime" -Name "Python executable" -Status "FAIL" -Risk "HIGH" -Message "Python not found; HyperBOM engine cannot run." -Path ""
    }

    if ($enginePath -and $pythonExe) {
        def_WriteStep -Percent 42 -Activity "VIS HyperBOM All-In-One" -Status "Python syntax compile for HyperBOM engine" -Color Cyan
        $compilePrefix = Join-Path $logDir "python_compile_engine"
        $compileResult = def_InvokeChild -FileName $pythonExe -Arguments @("-m","py_compile",$enginePath) -WorkDir (Split-Path -Parent $enginePath) -LogPrefix $compilePrefix -TimeoutSec $ChildTimeoutSec
        [void]$processRows.Add($compileResult)
        def_AddRow -Rows $matrixRows -Matrix "Syntax" -Name "python -m py_compile" -Status $compileResult.status -Risk $(if ($compileResult.status -eq "PASS") {"LOW"} else {"HIGH"}) -Message $compileResult.message -Path $enginePath

        def_WriteStep -Percent 52 -Activity "VIS HyperBOM All-In-One" -Status "Generating HyperBOM CSV template" -Color Cyan
        $templateOut = Join-Path $runDir "generated_template_csv"
        $templatePrefix = Join-Path $logDir "engine_make_template"
        $templateResult = def_InvokeChild -FileName $pythonExe -Arguments @($enginePath,"--make-template","--out",$templateOut) -WorkDir (Split-Path -Parent $enginePath) -LogPrefix $templatePrefix -TimeoutSec $ChildTimeoutSec
        [void]$processRows.Add($templateResult)
        def_AddRow -Rows $matrixRows -Matrix "HyperBOM" -Name "Generate CSV template" -Status $templateResult.status -Risk $(if ($templateResult.status -eq "PASS") {"LOW"} else {"HIGH"}) -Message $templateResult.message -Path $templateOut

        def_WriteStep -Percent 62 -Activity "VIS HyperBOM All-In-One" -Status "Generating sample data" -Color Cyan
        $sampleOut = Join-Path $runDir "sample_input_csv"
        $samplePrefix = Join-Path $logDir "engine_write_sample"
        $sampleResult = def_InvokeChild -FileName $pythonExe -Arguments @($enginePath,"--write-sample","--out",$sampleOut) -WorkDir (Split-Path -Parent $enginePath) -LogPrefix $samplePrefix -TimeoutSec $ChildTimeoutSec
        [void]$processRows.Add($sampleResult)
        def_AddRow -Rows $matrixRows -Matrix "HyperBOM" -Name "Generate sample input" -Status $sampleResult.status -Risk $(if ($sampleResult.status -eq "PASS") {"LOW"} else {"HIGH"}) -Message $sampleResult.message -Path $sampleOut

        def_WriteStep -Percent 72 -Activity "VIS HyperBOM All-In-One" -Status "Running HyperBOM self-test" -Color Cyan
        $selfTestOut = Join-Path $runDir "self_test_output"
        $selfTestPrefix = Join-Path $logDir "engine_self_test"
        $selfResult = def_InvokeChild -FileName $pythonExe -Arguments @($enginePath,"--self-test","--out",$selfTestOut,"--qty",([string]$BuildQty)) -WorkDir (Split-Path -Parent $enginePath) -LogPrefix $selfTestPrefix -TimeoutSec $ChildTimeoutSec
        [void]$processRows.Add($selfResult)
        def_AddRow -Rows $matrixRows -Matrix "HyperBOM" -Name "Self-test validation" -Status $selfResult.status -Risk $(if ($selfResult.status -eq "PASS") {"LOW"} else {"HIGH"}) -Message $selfResult.message -Path $selfTestOut

        if ($InputCsvFolder -and (Test-Path -LiteralPath $InputCsvFolder)) {
            def_WriteStep -Percent 82 -Activity "VIS HyperBOM All-In-One" -Status "Running real input folder" -Color Cyan
            $realOut = Join-Path $runDir "real_input_output"
            $realPrefix = Join-Path $logDir "engine_real_input"
            $realResult = def_InvokeChild -FileName $pythonExe -Arguments @($enginePath,"--input",(Resolve-Path -LiteralPath $InputCsvFolder).Path,"--out",$realOut,"--root",$RootPartNumber,"--qty",([string]$BuildQty)) -WorkDir (Split-Path -Parent $enginePath) -LogPrefix $realPrefix -TimeoutSec $ChildTimeoutSec
            [void]$processRows.Add($realResult)
            def_AddRow -Rows $matrixRows -Matrix "HyperBOM" -Name "Real input run" -Status $realResult.status -Risk $(if ($realResult.status -eq "PASS") {"LOW"} else {"HIGH"}) -Message $realResult.message -Path $realOut
        } else {
            def_AddRow -Rows $matrixRows -Matrix "HyperBOM" -Name "Real input run" -Status "WARN" -Risk "LOW" -Message "InputCsvFolder not provided or not found; skipped real data run." -Path ($InputCsvFolder + "")
        }
    } else {
        def_AddRow -Rows $matrixRows -Matrix "HyperBOM" -Name "Engine execution" -Status "FAIL" -Risk "HIGH" -Message "Missing engine or Python runtime." -Path $enginePath
    }

    def_WriteStep -Percent 90 -Activity "VIS HyperBOM All-In-One" -Status "Hydra risk and quantity finalization" -Color Cyan
    $duplicateBasenames = $inventory | Group-Object name | Where-Object { $_.Count -gt 1 }
    $hydraStatus = if (@($duplicateBasenames).Count -eq 0) { "PASS" } else { "WARN" }
    def_AddRow -Rows $matrixRows -Matrix "Hydra Risk" -Name "Duplicate basename risk" -Status $hydraStatus -Risk $(if ($hydraStatus -eq "PASS") {"LOW"} else {"MEDIUM"}) -Message "Duplicate basenames found: $(@($duplicateBasenames).Count). Review before canonical merge." -Path "" -Expected 0 -Actual @($duplicateBasenames).Count

    $failCount = @($matrixRows | Where-Object { $_.ryg -eq "RED" }).Count
    $warnCount = @($matrixRows | Where-Object { $_.ryg -eq "YELLOW" }).Count
    $gate = if ($failCount -eq 0) { "PASS" } else { "REVIEW_REQUIRED" }
    $summary = [ordered]@{
        gate = $gate
        generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        base_dir = $BaseDir
        run_dir = $runDir
        files_scanned = $inventory.Count
        registry_tools_expected = 270
        registry_tools_actual = $registryActual
        red_count = $failCount
        yellow_count = $warnCount
        policy = "append-only; run-local; no delete; no canonical mutation; no SAP/PLM write-back"
    }
    $summaryPath = Join-Path $runDir "VIS_HyperBOM_AllInOne_RunSummary.json"
    $matrixJsonPath = Join-Path $matrixDir "VIS_HyperBOM_Master_Matrix.json"
    def_WriteJson -Data $summary -Path $summaryPath
    def_WriteJson -Data $matrixRows -Path $matrixJsonPath

    def_WriteStep -Percent 96 -Activity "VIS HyperBOM All-In-One" -Status "Generating HTML UI Matrix" -Color Cyan
    $htmlPath = Join-Path $runDir "VIS_HyperBOM_AllInOne_Governance_Matrix.html"
    def_BuildGovernanceHtml -Path $htmlPath -Summary $summary -MatrixRows $matrixRows -InventorySummary $inventorySummary -AstRows $astRows -ProcessRows $processRows -RegistryFlatRows $registryFlatRows

    Write-Progress -Activity "VIS HyperBOM All-In-One" -Completed
    def_WriteBanner -Title "VIS HyperBOM Matrix · ALL-IN-ONE RESULT"
    Write-Host "Gate        : $gate" -ForegroundColor $(if ($gate -eq "PASS") {"Green"} else {"Yellow"})
    Write-Host "RunDir      : $runDir" -ForegroundColor Cyan
    Write-Host "HTML Matrix : $htmlPath" -ForegroundColor Cyan
    Write-Host "Summary     : $summaryPath" -ForegroundColor Cyan
    Write-Host "Registry    : $registryPath" -ForegroundColor Cyan
    Write-Host "Red         : $failCount" -ForegroundColor $(if ($failCount -eq 0) {"Green"} else {"Red"})
    Write-Host "Yellow      : $warnCount" -ForegroundColor Yellow

    if ($OpenHtml -and (Test-Path -LiteralPath $htmlPath)) {
        Start-Process -FilePath $htmlPath | Out-Null
    }
} catch {
    Write-Host "" -ForegroundColor Red
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
} finally {
    Write-Progress -Activity "VIS HyperBOM All-In-One" -Completed
    if ($KeepPowerShellOpen) {
        Write-Host "" -ForegroundColor Cyan
        Write-Host "PowerShell remains open. No destructive action was executed." -ForegroundColor Cyan
        Read-Host "Press Enter to return to prompt"
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

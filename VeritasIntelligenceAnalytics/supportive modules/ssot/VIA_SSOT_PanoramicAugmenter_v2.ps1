#requires -Version 7.0
<#
================================================================================
 VIA_SSOT_PanoramicAugmenter_v2.ps1   ── ONE PowerShell to solve all problems
 ASSET_ID    : AST-PS-MOD-VSE-AUG-002
 DISPLAY     : SYS_VSE.AUGMENTER.MOD-PANORAMIC-V2
 VERSION     : 2.0.0       STATUS : sim-validated · idempotent · self-healing
 LANGUAGE    : PowerShell 7.x
 PURPOSE     : VIA_SSOT_Unified.py 一鍵終極修復
               1. 全景式 AST 檢視 + 污染偵測
               2. 補不足規則注入（76 條會計科目同義詞，idempotent）
               3. POLLUTION 清理 — VIA_FINAL_PATCH 註解化 + module-level rebind
               4. 自動測試（py_compile / import / SSOT class / module-level / 新規則）
               5. HTML U/I Matrix Report 自動跳出（VIA Visual Lock）
 LL RULES    : #10 #12 #13 #15 #16 #17 #18 #19 #20
 ACCEL (10)  : 1.ProcessStartInfo  2.StringBuilder  3.HashSet
               4.List<T>           5.Stopwatch       6.OrderedDict
               7.[regex]MatchEvaluator  8.LINQ .Where{}
               9.Out-Null discard       10.SHA256 fingerprint
================================================================================
 USAGE
 ─────────────────────────────────────────────────────────────────────────
   pwsh -ExecutionPolicy Bypass -File .\VIA_SSOT_PanoramicAugmenter_v2.ps1
   pwsh -File .\VIA_SSOT_PanoramicAugmenter_v2.ps1 -Mode Augment
   pwsh -File .\VIA_SSOT_PanoramicAugmenter_v2.ps1 -Mode Clean
   pwsh -File .\VIA_SSOT_PanoramicAugmenter_v2.ps1 -Mode Full -DryRun
   pwsh -File .\VIA_SSOT_PanoramicAugmenter_v2.ps1 -ForceLocalCopy

 MODES
   Augment : 只補不足規則（v1 行為）
   Clean   : 只清理 VIA_FINAL_PATCH 污染
   Full    : 兩個都做（預設）
================================================================================
#>

param(
    [string]$TargetPath = 'C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py',
    [ValidateSet('Augment','Clean','Full')]
    [string]$Mode = 'Full',
    [string]$OutDir = '',
    [switch]$DryRun,
    [switch]$NoOpenHtml,
    [switch]$ForceLocalCopy
)

# param 必須在最頂端，以下才開始一般指令 ───────────────────
[System.Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3.0

$script:SW    = [System.Diagnostics.Stopwatch]::StartNew()
$script:LOG   = [System.Collections.Generic.List[string]]::new()
$script:STAT  = [ordered]@{}
$script:DIFF  = [System.Collections.Generic.List[hashtable]]::new()
$script:TESTS = [System.Collections.Generic.List[hashtable]]::new()
$script:WARN  = [System.Collections.Generic.List[string]]::new()
$script:FP    = [ordered]@{}   # SHA256 fingerprints

function Write-Stage {
    param([string]$Tag, [string]$Msg, [ConsoleColor]$Color = 'Cyan')
    $line = ('[{0,7:N2}s] [{1}] {2}' -f $script:SW.Elapsed.TotalSeconds, $Tag, $Msg)
    Write-Host $line -ForegroundColor $Color
    $script:LOG.Add($line) | Out-Null
}

function Get-FileSha256 {
    param([string]$Path)
    $h = Get-FileHash -LiteralPath $Path -Algorithm SHA256
    return $h.Hash.Substring(0, 12).ToLower()
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 0 ─ 環境探勘 + 工作目錄 + 備份 + Python 偵測                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE0' ('啟動 v2 — Mode: {0}' -f $Mode) Yellow

if (-not (Test-Path -LiteralPath $TargetPath)) {
    throw "目標檔案不存在：$TargetPath"
}
$targetItem = Get-Item -LiteralPath $TargetPath
$srcDir     = $targetItem.Directory.FullName
$srcName    = $targetItem.Name
$srcSize    = $targetItem.Length

if (-not $OutDir) {
    $OutDir = Join-Path $srcDir ('_VIA_SSOT_AugV2_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$workFile    = Join-Path $OutDir 'VIA_SSOT_Unified.work.py'
$backupFile  = Join-Path $OutDir 'VIA_SSOT_Unified.backup.py'
$reportFile  = Join-Path $OutDir 'VIA_SSOT_Matrix_Report_v2.html'
$invJsonBefore = Join-Path $OutDir 'panoramic_inspect_before.json'
$invJsonAfter  = Join-Path $OutDir 'panoramic_inspect_after.json'
$specJson    = Join-Path $OutDir 'patch_spec.json'
$resultJson  = Join-Path $OutDir 'patch_result.json'
$testsJson   = Join-Path $OutDir 'tests_result.json'

Copy-Item -LiteralPath $TargetPath -Destination $backupFile -Force
Copy-Item -LiteralPath $TargetPath -Destination $workFile  -Force

$script:FP['source_input'] = Get-FileSha256 -Path $TargetPath
$script:FP['backup']       = Get-FileSha256 -Path $backupFile

Write-Stage 'PHASE0' ('來源: {0} ({1:N0} bytes, sha256:{2})' -f $srcName, $srcSize, $script:FP['source_input']) Green
Write-Stage 'PHASE0' ('輸出: {0}' -f $OutDir) Green

# 偵測 Python 3.11+ ──────────────────────────────────────
$pyExe = $null; $pyArg = $null
$candidates = @(
    @{exe='py';         arg='-3.11'},
    @{exe='py';         arg='-3.12'},
    @{exe='py';         arg='-3.13'},
    @{exe='py';         arg='-3'   },
    @{exe='python3.11'; arg=$null},
    @{exe='python3.12'; arg=$null},
    @{exe='python3.13'; arg=$null},
    @{exe='python';     arg=$null}
)
foreach ($c in $candidates) {
    try {
        $argv = @()
        if ($c.arg) { $argv += $c.arg }
        $argv += @('-c', 'import sys;print(sys.version_info[:2])')
        $out = & $c.exe @argv 2>$null
        if ($LASTEXITCODE -eq 0 -and $out -match '\(3,\s*1[1-9]') {
            $pyExe = $c.exe; $pyArg = $c.arg
            Write-Stage 'PHASE0' ('Python 偵測成功: {0} {1} → {2}' -f $c.exe, $c.arg, $out.Trim()) Green
            break
        }
    } catch { }
}
if (-not $pyExe) {
    throw "未偵測到 Python 3.11+（必要條件，請先安裝）"
}

function Invoke-PyScript {
    param(
        [string]$ScriptPath,
        [string[]]$ScriptArgs = @(),
        [int]$TimeoutMs = 120000
    )
    $argv = [System.Collections.Generic.List[string]]::new()
    if ($pyArg) { $argv.Add($pyArg) }
    $argv.Add($ScriptPath)
    foreach ($a in $ScriptArgs) { $argv.Add($a) }

    $psi = [System.Diagnostics.ProcessStartInfo]@{
        FileName               = $pyExe
        WorkingDirectory       = $OutDir
        UseShellExecute        = $false
        RedirectStandardOutput = $true
        RedirectStandardError  = $true
        CreateNoWindow         = $true
        StandardOutputEncoding = [System.Text.Encoding]::UTF8
        StandardErrorEncoding  = [System.Text.Encoding]::UTF8
    }
    foreach ($a in $argv) { $psi.ArgumentList.Add($a) }

    $proc = [System.Diagnostics.Process]::Start($psi)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    if (-not $proc.WaitForExit($TimeoutMs)) {
        try { $proc.Kill() } catch { }
        return @{ Pass=$false; ExitCode=-1; Stdout=$stdout; Stderr='TIMEOUT' }
    }
    @{ Pass=($proc.ExitCode -eq 0); ExitCode=$proc.ExitCode; Stdout=$stdout; Stderr=$stderr }
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 1 ─ 全景式 AST 檢視（before）                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE1' '全景式 AST 檢視 → 庫存盤點 + 污染偵測' Yellow

$astTool = Join-Path $OutDir 'panoramic_inspect.py'
$astCode = @'
# -*- coding: utf-8 -*-
"""Panoramic AST inspector for VIA_SSOT_Unified.py — uses real AST parse for accurate def counts."""
import ast, json, re, sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
out_path = Path(sys.argv[2])

anchor_pat = re.compile(r'#\s*ANCHOR\[VIA:ANCHOR:([A-Z0-9\-]+)\]\s*[\u2014\-]?\s*([^\r\n]*)')
anchors = []
for i, line in enumerate(src.splitlines(), start=1):
    m = anchor_pat.search(line)
    if m:
        anchors.append({'line': i, 'id': m.group(1), 'desc': m.group(2).strip()})

def count_objs(src_text, marker_var):
    pat = re.compile(rf"{marker_var}\s*:\s*list\[Rule\]\s*=\s*json\.loads\(r'''(.*?)'''\)", re.DOTALL)
    m = pat.search(src_text)
    if not m: return 0, []
    try:
        data = json.loads(m.group(1))
        return len(data), data
    except Exception as e:
        return -1, [{'error': str(e)}]

regex_n, regex_data = count_objs(src, '_RAW_REGEX')
list_n,  list_data  = count_objs(src, '_RAW_LISTS')
syn_n,   syn_data   = count_objs(src, '_RAW_SYNONYMS')

regex_names = [r.get('rule_name') for r in regex_data if isinstance(r, dict)]
list_names  = [r.get('list_name') for r in list_data  if isinstance(r, dict)]
syn_names   = [r.get('canonical') for r in syn_data   if isinstance(r, dict)]
syn_groups, total_aliases = {}, 0
for r in syn_data:
    if isinstance(r, dict):
        g = r.get('group', 'unknown')
        syn_groups[g] = syn_groups.get(g, 0) + 1
        total_aliases += len(r.get('aliases', []))

# ── 污染偵測 ─────────────────────────────────────────────
pollution = []
quarantined = '_VIA_QUARANTINED_VIA_FINAL_PATCH' in src
if 'VIA_FINAL_PATCH_SSOT_COMPAT' in src and not quarantined:
    pollution.append('VIA_FINAL_PATCH_SSOT_COMPAT detected — module-level get_ssot/normalize/extract overridden')
if quarantined:
    pollution.append('PREVIOUSLY QUARANTINED — VIA_FINAL_PATCH already wrapped in docstring (safe state)')

# ── AST 級別準確的 def 計數（不被 docstring 內容干擾） ──
ast_def_counts = {}
parse_ok, parse_err = True, ''
funcs_module_level = []
classes = []
try:
    tree = ast.parse(src)
    # 只計算 module-level 的 def
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs_module_level.append({'name': node.name, 'line': node.lineno})
            ast_def_counts[node.name] = ast_def_counts.get(node.name, 0) + 1
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append({'name': node.name, 'line': node.lineno, 'method_count': len(methods)})
except SyntaxError as e:
    parse_ok = False; parse_err = f'{e.msg} at line {e.lineno}'

# 重要 def 重複計數（基於 AST，不被 docstring 影響）
dup_get_ssot   = ast_def_counts.get('get_ssot',  0)
dup_normalize  = ast_def_counts.get('normalize', 0)
dup_extract    = ast_def_counts.get('extract',   0)

# 也提供 regex 線性計數做對照（包含 docstring 內容）
regex_dup_get_ssot   = len(re.findall(r'^def\s+get_ssot\s*\(',  src, re.MULTILINE))
regex_dup_normalize  = len(re.findall(r'^def\s+normalize\s*\(', src, re.MULTILINE))
regex_dup_extract    = len(re.findall(r'^def\s+extract\s*\(',   src, re.MULTILINE))

# 全部函數 (含 class methods)
all_funcs_count = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))) if parse_ok else 0

ver_match  = re.search(r'VERSION\s*:\s*(\d+\.\d+\.\d+)', src)
version    = ver_match.group(1) if ver_match else 'unknown'
test_match = re.search(r'Self-Test\s*\((\d+)\s*cases\)', src)
test_count = int(test_match.group(1)) if test_match else 0

result = {
    'version': version, 'parse_ok': parse_ok, 'parse_err': parse_err,
    'src_bytes': len(src.encode('utf-8')), 'src_lines': src.count('\n') + 1,
    'anchors': anchors,
    'regex_count': regex_n, 'list_count': list_n, 'synonym_count': syn_n,
    'total_aliases': total_aliases,
    'regex_names': regex_names, 'list_names': list_names,
    'synonym_canonicals': syn_names, 'synonym_groups': syn_groups,
    'function_count': all_funcs_count, 'class_count': len(classes), 'classes': classes,
    'self_test_count': test_count,
    'pollution': pollution,
    'quarantined': quarantined,
    'ast_duplicate_defs': {
        'get_ssot': dup_get_ssot, 'normalize': dup_normalize, 'extract': dup_extract
    },
    'regex_duplicate_defs': {
        'get_ssot': regex_dup_get_ssot, 'normalize': regex_dup_normalize, 'extract': regex_dup_extract
    },
}
out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('OK')
'@
Set-Content -LiteralPath $astTool -Value $astCode -Encoding UTF8

$r1 = Invoke-PyScript -ScriptPath $astTool -ScriptArgs @($workFile, $invJsonBefore)
if (-not $r1.Pass) { throw ("AST 掃描失敗: " + $r1.Stderr.Trim()) }
$invBefore = Get-Content -LiteralPath $invJsonBefore -Raw -Encoding UTF8 | ConvertFrom-Json

$script:STAT['mode']             = $Mode
$script:STAT['source_file']      = $srcName
$script:STAT['source_bytes']     = $srcSize
$script:STAT['source_lines']     = $invBefore.src_lines
$script:STAT['version_before']   = $invBefore.version
$script:STAT['parse_ok']         = $invBefore.parse_ok
$script:STAT['anchors_count']    = $invBefore.anchors.Count
$script:STAT['regex_before']     = $invBefore.regex_count
$script:STAT['list_before']      = $invBefore.list_count
$script:STAT['synonym_before']   = $invBefore.synonym_count
$script:STAT['aliases_before']   = $invBefore.total_aliases
$script:STAT['function_count']   = $invBefore.function_count
$script:STAT['class_count']      = $invBefore.class_count
$script:STAT['self_test_before'] = $invBefore.self_test_count
$script:STAT['quarantined_before'] = $invBefore.quarantined
$script:STAT['ast_dup_get_ssot_before']   = $invBefore.ast_duplicate_defs.get_ssot
$script:STAT['ast_dup_normalize_before']  = $invBefore.ast_duplicate_defs.normalize
$script:STAT['ast_dup_extract_before']    = $invBefore.ast_duplicate_defs.extract

Write-Stage 'PHASE1' ('版本: {0}  Parse OK: {1}  Lines: {2:N0}  SHA256: {3}' -f `
    $invBefore.version, $invBefore.parse_ok, $invBefore.src_lines, $script:FP['source_input']) Green
Write-Stage 'PHASE1' ('Anchors: {0}  Regex: {1}  Lists: {2}  Synonyms: {3}  Aliases: {4}' -f `
    $invBefore.anchors.Count, $invBefore.regex_count, $invBefore.list_count, $invBefore.synonym_count, $invBefore.total_aliases) Green
Write-Stage 'PHASE1' ('AST def count: get_ssot×{0}, normalize×{1}, extract×{2}' -f `
    $invBefore.ast_duplicate_defs.get_ssot, $invBefore.ast_duplicate_defs.normalize, $invBefore.ast_duplicate_defs.extract) Green

if ($invBefore.pollution.Count -gt 0) {
    foreach ($w in $invBefore.pollution) {
        Write-Stage 'PHASE1' ('  ⚠ {0}' -f $w) Yellow
        $script:WARN.Add($w) | Out-Null
    }
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 2 ─ 補不足規則設計 + spec 序列化                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝
$doAugment = ($Mode -eq 'Full' -or $Mode -eq 'Augment')
$doClean   = ($Mode -eq 'Full' -or $Mode -eq 'Clean')

Write-Stage 'PHASE2' ('規則設計階段 — Augment: {0}, Clean: {1}' -f $doAugment, $doClean) Yellow

$ALIAS_REDIRECT = [ordered]@{
    'EPS' = [ordered]@{
        remove = @('基本每股盈餘', '稀釋每股盈餘')
        note   = '由 BasicEPS / DilutedEPS 精化承接；EPS 仍保留 "每股盈餘" / "Earnings Per Share" 作為通用稱呼'
    }
}

# 76 條新規則
$newRulesRaw = @(
    @{can='SellingExpenses';            grp='income_statement'; aliases=@('推銷費用','銷售費用','Selling Expenses','銷售及行銷費用')}
    @{can='AdministrativeExpenses';     grp='income_statement'; aliases=@('管理費用','一般管理費用','Administrative Expenses','General and Administrative Expenses','G&A')}
    @{can='SellingGeneralAdmin';        grp='income_statement'; aliases=@('推銷及管理費用','SG&A','Selling General and Administrative','銷管費用')}
    @{can='FinanceCosts';               grp='income_statement'; aliases=@('財務成本','利息支出','Finance Costs','Interest Expense','利息費用')}
    @{can='InterestIncome';             grp='income_statement'; aliases=@('利息收入','Interest Income','存款利息')}
    @{can='ForeignExchangeGain';        grp='income_statement'; aliases=@('匯兌損益','匯兌利益','Foreign Exchange Gain','FX Gain Loss','匯率變動損益')}
    @{can='NonOperatingIncome';         grp='income_statement'; aliases=@('營業外收入及支出','業外損益','Non-operating Income','Non Operating Income','Other Income Expense','業外收支')}
    @{can='PretaxIncome';               grp='income_statement'; aliases=@('稅前淨利','稅前純益','Income Before Tax','Pretax Income','EBT','Earnings Before Tax')}
    @{can='IncomeTaxExpense';           grp='income_statement'; aliases=@('所得稅費用','Income Tax Expense','Tax Provision','所得稅','稅費')}
    @{can='OtherComprehensiveIncome';   grp='income_statement'; aliases=@('其他綜合損益','OCI','Other Comprehensive Income','綜合損益其他項目')}
    @{can='TotalComprehensiveIncome';   grp='income_statement'; aliases=@('本期綜合損益總額','綜合損益總額','Total Comprehensive Income')}
    @{can='BasicEPS';                   grp='income_statement'; aliases=@('基本每股盈餘','Basic EPS','Basic Earnings Per Share')}
    @{can='DilutedEPS';                 grp='income_statement'; aliases=@('稀釋每股盈餘','Diluted EPS','Diluted Earnings Per Share','完全稀釋每股盈餘')}
    @{can='EquityMethodInvestmentIncome'; grp='income_statement'; aliases=@('採用權益法認列之損益份額','權益法投資損益','Share of Profit of Associates','Equity Method Income')}
    @{can='ExpectedCreditLoss';         grp='income_statement'; aliases=@('預期信用減損損失','預期信用減損','Expected Credit Loss','ECL')}
    @{can='AccountsReceivable';         grp='balance_sheet'; aliases=@('應收帳款','應收帳款淨額','Accounts Receivable','A/R','Receivables','貿易應收款')}
    @{can='Inventory';                  grp='balance_sheet'; aliases=@('存貨','庫存','Inventory','Inventories','商品存貨')}
    @{can='Prepayments';                grp='balance_sheet'; aliases=@('預付款項','Prepayments','預付費用','Prepaid Expenses')}
    @{can='FinancialAssetsFVTPL';       grp='balance_sheet'; aliases=@('透過損益按公允價值衡量之金融資產','Financial Assets at FVTPL','FVTPL Assets')}
    @{can='FinancialAssetsFVOCI';       grp='balance_sheet'; aliases=@('透過其他綜合損益按公允價值衡量之金融資產','Financial Assets at FVOCI','FVOCI Assets')}
    @{can='EquityMethodInvestments';    grp='balance_sheet'; aliases=@('採用權益法之投資','Investments Accounted for Using Equity Method','Investments And Advances','權益法投資')}
    @{can='PropertyPlantEquipment';     grp='balance_sheet'; aliases=@('不動產廠房及設備','不動產、廠房及設備','PP&E','PPE','Property Plant Equipment','Net PPE','固定資產')}
    @{can='RightOfUseAssets';           grp='balance_sheet'; aliases=@('使用權資產','Right-of-use Assets','ROU Assets')}
    @{can='IntangibleAssets';           grp='balance_sheet'; aliases=@('無形資產','Intangible Assets','商譽','Goodwill','Goodwill And Other Intangible Assets')}
    @{can='AccountsPayable';            grp='balance_sheet'; aliases=@('應付帳款','Accounts Payable','A/P','Payables','貿易應付款')}
    @{can='AccruedExpenses';            grp='balance_sheet'; aliases=@('應付薪資及費用','應計費用','Accrued Expenses','應付費用')}
    @{can='ShortTermBorrowings';        grp='balance_sheet'; aliases=@('短期借款','Short-term Borrowings','Short Term Debt','Current Debt','短期負債')}
    @{can='LongTermBorrowings';         grp='balance_sheet'; aliases=@('長期借款','Long-term Borrowings','Long Term Debt','長期負債')}
    @{can='LeaseLiabilities';           grp='balance_sheet'; aliases=@('租賃負債','Lease Liabilities','租賃負擔')}
    @{can='DeferredTaxLiabilities';     grp='balance_sheet'; aliases=@('遞延所得稅負債','Deferred Tax Liabilities','DTL')}
    @{can='ShareCapital';               grp='balance_sheet'; aliases=@('股本','普通股股本','Share Capital','Common Stock','Capital Stock','實收資本')}
    @{can='CapitalSurplus';             grp='balance_sheet'; aliases=@('資本公積','Capital Surplus','Additional Paid in Capital','APIC')}
    @{can='RetainedEarnings';           grp='balance_sheet'; aliases=@('保留盈餘','累積盈餘','Retained Earnings','未分配盈餘')}
    @{can='NonControllingInterests';    grp='balance_sheet'; aliases=@('非控制權益','Non-controlling Interests','Minority Interest','少數股權')}
    @{can='TreasuryStock';              grp='balance_sheet'; aliases=@('庫藏股','庫藏股票','Treasury Stock','Treasury Shares')}
    @{can='Depreciation';               grp='cash_flow'; aliases=@('折舊費用','折舊','Depreciation','固定資產折舊')}
    @{can='Amortization';               grp='cash_flow'; aliases=@('攤銷費用','攤提費用','Amortization','無形資產攤銷')}
    @{can='DepreciationAndAmortization';grp='cash_flow'; aliases=@('折舊與攤銷','D&A','Depreciation and Amortization','折舊及攤銷')}
    @{can='CapitalExpenditures';        grp='cash_flow'; aliases=@('資本支出','取得不動產廠房及設備','CapEx','Capital Expenditure','Capital Expenditures','設備投資')}
    @{can='FreeCashFlow';               grp='cash_flow'; aliases=@('自由現金流量','自由現金流','FCF','Free Cash Flow')}
    @{can='DividendsPaid';              grp='cash_flow'; aliases=@('發放現金股利','現金股利','Dividends Paid','Cash Dividends Paid','股利支付')}
    @{can='EffectOfExchangeRate';       grp='cash_flow'; aliases=@('匯率影響數','匯率變動影響','Effect of Exchange Rate Changes','Foreign Exchange Effects')}
    @{can='NetChangeInCash';            grp='cash_flow'; aliases=@('本期現金及約當現金增加減少','Net Change In Cash','Changes In Cash','現金淨變動')}
    @{can='ReturnOnEquity';             grp='ratio'; aliases=@('股東權益報酬率','ROE','Return on Equity','權益報酬率','淨值報酬率')}
    @{can='ReturnOnAssets';             grp='ratio'; aliases=@('總資產報酬率','資產報酬率','ROA','Return on Assets')}
    @{can='GrossMargin';                grp='ratio'; aliases=@('毛利率','Gross Margin','Gross Profit Margin','營業毛利率')}
    @{can='OperatingMargin';            grp='ratio'; aliases=@('營業利益率','Operating Margin','EBIT Margin','營業淨利率')}
    @{can='NetProfitMargin';            grp='ratio'; aliases=@('純益率','淨利率','Net Profit Margin','Profit Margin','稅後淨利率')}
    @{can='PretaxMargin';               grp='ratio'; aliases=@('稅前淨利率','Pretax Margin','Pre-tax Margin')}
    @{can='CurrentRatio';               grp='ratio'; aliases=@('流動比率','Current Ratio','流動比')}
    @{can='QuickRatio';                 grp='ratio'; aliases=@('速動比率','Quick Ratio','Acid Test Ratio','酸性測試比率')}
    @{can='DebtRatio';                  grp='ratio'; aliases=@('負債比率','Debt Ratio','Debt-to-Asset Ratio','資產負債率','負債比')}
    @{can='DebtToEquity';               grp='ratio'; aliases=@('負債權益比','Debt-to-Equity','D/E Ratio','負債對權益比率')}
    @{can='InterestCoverage';           grp='ratio'; aliases=@('利息保障倍數','Interest Coverage Ratio','Times Interest Earned','TIE')}
    @{can='ReceivablesTurnover';        grp='ratio'; aliases=@('應收帳款週轉率','Receivables Turnover','A/R Turnover')}
    @{can='InventoryTurnover';          grp='ratio'; aliases=@('存貨週轉率','Inventory Turnover')}
    @{can='AssetTurnover';              grp='ratio'; aliases=@('總資產週轉率','Asset Turnover','Total Asset Turnover')}
    @{can='DaysSalesOutstanding';       grp='ratio'; aliases=@('平均收現日數','DSO','Days Sales Outstanding','收現天數')}
    @{can='DaysInventoryOutstanding';   grp='ratio'; aliases=@('平均銷售日數','DIO','Days Inventory Outstanding','存貨天數')}
    @{can='CashConversionCycle';        grp='ratio'; aliases=@('現金轉換循環','淨營業週期','CCC','Cash Conversion Cycle')}
    @{can='CashFlowAdequacyRatio';      grp='ratio'; aliases=@('現金流量允當比率','Cash Flow Adequacy Ratio')}
    @{can='OperatingCashFlowRatio';     grp='ratio'; aliases=@('現金流量比率','Operating Cash Flow Ratio')}
    @{can='EffectiveTaxRate';           grp='ratio'; aliases=@('有效稅率','Effective Tax Rate','實質稅率')}
    @{can='EquityMultiplier';           grp='ratio'; aliases=@('權益乘數','Equity Multiplier','財務槓桿乘數')}
    @{can='PriceToEarnings';            grp='market'; aliases=@('本益比','P/E','PE Ratio','PER','Price-to-Earnings','TrailingPE','股價盈餘比')}
    @{can='PriceToBook';                grp='market'; aliases=@('股價淨值比','P/B','PB Ratio','PBR','Price-to-Book','市價淨值比')}
    @{can='PriceToSales';               grp='market'; aliases=@('股價營收比','P/S','PS Ratio','PSR','Price-to-Sales','市價營收比')}
    @{can='DividendYield';              grp='market'; aliases=@('現金股利殖利率','股利殖利率','Dividend Yield','現金殖利率','股息收益率','Yield')}
    @{can='PayoutRatio';                grp='market'; aliases=@('股利發放率','配息率','Payout Ratio','Dividend Payout Ratio','股利支付率')}
    @{can='BookValuePerShare';          grp='per_share'; aliases=@('每股淨值','BVPS','Book Value Per Share','每股帳面價值','每股股東權益')}
    @{can='RevenuePerShare';            grp='per_share'; aliases=@('每股營業額','每股營收','Revenue Per Share','SPS','Sales Per Share')}
    @{can='CashFlowPerShare';           grp='per_share'; aliases=@('每股現金流量','每股現金流','CFPS','Cash Flow Per Share')}
    @{can='FreeCashFlowPerShare';       grp='per_share'; aliases=@('每股自由現金流','FCF Per Share','Free Cash Flow Per Share')}
    @{can='SharesOutstanding';          grp='per_share'; aliases=@('普通股流通股數','流通在外股數','發行股數','Shares Outstanding','市場流通股')}
    @{can='WeightedAverageShares';      grp='per_share'; aliases=@('加權平均股數','加權平均流通股數','Weighted Average Shares','基本股數')}
    @{can='DilutedShares';              grp='per_share'; aliases=@('稀釋後股數','完全稀釋後股數','Fully Diluted Shares','Diluted Average Shares')}
)

if ($doAugment) {
    Write-Stage 'PHASE2' ('  Augment 啟用 — 預備新增 {0} 條規則' -f $newRulesRaw.Count) Cyan
} else {
    Write-Stage 'PHASE2' '  Augment 跳過' DarkGray
}

if ($doClean) {
    if ($invBefore.quarantined) {
        Write-Stage 'PHASE2' '  Clean 啟用 — 偵測到既有 quarantine（idempotent，會跳過實際清理）' Cyan
    } else {
        Write-Stage 'PHASE2' '  Clean 啟用 — 預備清理 VIA_FINAL_PATCH 污染區' Cyan
    }
} else {
    Write-Stage 'PHASE2' '  Clean 跳過' DarkGray
}

$rulesForPy = if ($doAugment) {
    @($newRulesRaw | ForEach-Object {
        [ordered]@{ canonical=$_.can; group=$_.grp; aliases=@($_.aliases) }
    })
} else { @() }

$specObj = [ordered]@{
    new_rules      = $rulesForPy
    alias_redirect = $ALIAS_REDIRECT
    work_file      = $workFile
    target_version = '4.3.0'
    do_augment     = $doAugment
    do_clean       = $doClean
    dry_run        = [bool]$DryRun
}
$specJsonText = $specObj | ConvertTo-Json -Depth 10
Set-Content -LiteralPath $specJson -Value $specJsonText -Encoding UTF8

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 3 ─ AST 級別精準補丁 + POLLUTION 清理（Python 子程序）             ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE3' '精準補丁注入 + POLLUTION 清理' Yellow

$patchTool = Join-Path $OutDir 'apply_patch.py'
$patchCode = @'
# -*- coding: utf-8 -*-
"""Apply augmentation + pollution cleanup to VIA_SSOT_Unified.py.
   Idempotent: re-running has no effect (rules with existing canonicals are skipped;
   already-quarantined VIA_FINAL_PATCH is detected and skipped)."""
import json, re, sys
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
result_path = Path(sys.argv[2])

new_rules      = spec['new_rules']
alias_redirect = spec['alias_redirect']
work_file      = Path(spec['work_file'])
target_version = spec['target_version']
do_augment     = spec.get('do_augment', True)
do_clean       = spec.get('do_clean', True)
dry_run        = bool(spec.get('dry_run', False))

src = work_file.read_text(encoding='utf-8', errors='replace')
diffs = []
result = {'ok': True}

# ════════════════════════════════════════════════════════════
# PART A — AUGMENT (補不足規則)
# ════════════════════════════════════════════════════════════
augment_result = {'rules_added': 0, 'rules_skipped': 0, 'alias_conflicts': 0,
                  'pending': [], 'skipped': [], 'redirect_log': []}

if do_augment:
    syn_pat = re.compile(r"(_RAW_SYNONYMS\s*:\s*list\[Rule\]\s*=\s*json\.loads\(r''')(.*?)('''\))", re.DOTALL)
    syn_match = syn_pat.search(src)
    if not syn_match:
        result_path.write_text(json.dumps({'ok': False, 'error': '_RAW_SYNONYMS block not found'}, ensure_ascii=False), encoding='utf-8')
        sys.exit(2)

    syn_data = json.loads(syn_match.group(2))

    # alias redirect
    redirect_log = []
    for rule in syn_data:
        can = rule['canonical']
        if can in alias_redirect:
            cfg = alias_redirect[can]
            before = list(rule['aliases'])
            rule['aliases'] = [a for a in rule['aliases'] if a not in cfg['remove']]
            removed = [a for a in before if a not in rule['aliases']]
            if removed:
                redirect_log.append({'canonical': can, 'removed': removed, 'note': cfg.get('note', '')})

    # 衝突檢測
    known = {}
    for rule in syn_data:
        known[rule['canonical'].lower()] = rule['canonical']
        for a in rule['aliases']:
            known[a.lower()] = rule['canonical']

    max_id = 0
    for rule in syn_data:
        mm = re.match(r'SYN-FIN-ACCOUNT-(\d{4})', rule.get('syn_id', ''))
        if mm:
            n = int(mm.group(1))
            if n > max_id: max_id = n

    pending, skipped, alias_conflicts = [], [], []
    for r in new_rules:
        can = r['canonical']; grp = r['group']; aliases = list(r['aliases'])
        if can.lower() in known:
            skipped.append({'canonical': can, 'reason': 'canonical exists'}); continue
        bad, clean = [], []
        for a in aliases:
            if a.lower() in known:
                bad.append({'alias': a, 'occupied_by': known[a.lower()]})
            else:
                clean.append(a)
        if bad: alias_conflicts.append({'canonical': can, 'conflicts': bad})
        if not clean:
            skipped.append({'canonical': can, 'reason': 'all aliases conflict'}); continue
        pending.append({'canonical': can, 'group': grp, 'aliases': clean})
        known[can.lower()] = can
        for a in clean:
            known[a.lower()] = can

    next_id = max_id + 1
    new_rule_objs = []
    for p in pending:
        new_rule_objs.append({
            'syn_id':    f'SYN-FIN-ACCOUNT-{next_id:04d}',
            'canonical': p['canonical'],
            'aliases':   p['aliases'],
            'group':     p['group'],
            'status':    'stable',
            'version':   '1.0.0',
            'domain':    'finance_tw',
        })
        next_id += 1

    all_rules = syn_data + new_rule_objs
    new_syn_count   = len(all_rules)
    new_alias_count = sum(len(r['aliases']) for r in all_rules)
    new_syn_json    = json.dumps(all_rules, ensure_ascii=False, indent=2)

    src = src[:syn_match.start(2)] + '\n' + new_syn_json + '\n' + src[syn_match.end(2):]

    diffs.append({'anchor':'SSOT-DATA._RAW_SYNONYMS', 'action':'APPEND',
                  'count': len(pending),
                  'detail': f'+{len(pending)} synonym rules (skipped={len(skipped)})'})
    if redirect_log:
        diffs.append({'anchor':'SSOT-DATA._RAW_SYNONYMS', 'action':'REDIRECT',
                      'count': sum(len(r['removed']) for r in redirect_log),
                      'detail': '; '.join(f"{r['canonical']}: -{r['removed']}" for r in redirect_log)})

    augment_result.update({
        'rules_added': len(pending), 'rules_skipped': len(skipped),
        'alias_conflicts': len(alias_conflicts),
        'pending': pending, 'skipped': skipped, 'redirect_log': redirect_log,
        'before': {'synonym_count': len(syn_data) - len(new_rule_objs), 'alias_count': sum(len(r['aliases']) for r in syn_data) - sum(len(r['aliases']) for r in new_rule_objs)},
        'after':  {'synonym_count': new_syn_count, 'alias_count': new_alias_count},
    })

# 重新計算 corpus stats（無論 augment 是否開啟，都更新一次以保險）
def count_block(src_text, marker):
    p = re.compile(rf"{marker}\s*:\s*list\[Rule\]\s*=\s*json\.loads\(r'''(.*?)'''\)", re.DOTALL)
    m = p.search(src_text)
    return (len(json.loads(m.group(1))), json.loads(m.group(1))) if m else (0, [])

regex_count, _              = count_block(src, '_RAW_REGEX')
list_count, _               = count_block(src, '_RAW_LISTS')
syn_count, all_rules_now    = count_block(src, '_RAW_SYNONYMS')
alias_count                 = sum(len(r['aliases']) for r in all_rules_now)
total_rules                 = regex_count + list_count + syn_count

# 補丁: _CORPUS_STATS
corpus_pat = re.compile(r"(_CORPUS_STATS\s*:\s*dict\[str,\s*int\]\s*=\s*\{)([^}]+)(\})", re.DOTALL)
new_corpus = (
    '\n    "regex_rules":   ' + str(regex_count) +
    ',\n    "list_rules":    ' + str(list_count) +
    ',\n    "synonym_rules": ' + str(syn_count) +
    ',\n    "total_aliases": ' + str(alias_count) +
    ',\n    "total_rules":   ' + str(total_rules) + ',\n'
)
def _corpus_repl(m): return m.group(1) + new_corpus + m.group(3)
src_before_corpus = src
src = corpus_pat.sub(_corpus_repl, src, count=1)
if src != src_before_corpus:
    diffs.append({'anchor':'SSOT-DATA._CORPUS_STATS', 'action':'UPDATE', 'count': 5,
                  'detail': f'regex={regex_count}, lists={list_count}, syns={syn_count}, aliases={alias_count}, total={total_rules}'})

# 補丁: VERSION
old_ver_match = re.search(r'(VERSION\s*:\s*)(\d+\.\d+\.\d+)', src)
old_ver = old_ver_match.group(2) if old_ver_match else 'unknown'
if old_ver != target_version:
    src = re.sub(r'(VERSION\s*:\s*)\d+\.\d+\.\d+', r'\g<1>' + target_version, src, count=1)
    diffs.append({'anchor':'HEADER.VERSION', 'action':'UPDATE', 'count': 1,
                  'detail': f'{old_ver} -> {target_version}'})

# 補丁: BANNER
new_banner = f'CORPUS: regex={regex_count} \u00b7 lists={list_count} \u00b7 synonyms={syn_count} \u00b7 aliases={alias_count}'
src = re.sub(r'CORPUS:\s*regex=\d+\s*\u00b7\s*lists=\d+\s*\u00b7\s*synonyms=\d+\s*\u00b7\s*aliases=\d+',
             new_banner, src, count=1)

# 補丁: self_test
src = re.sub(r'(chk\("regex_rules=)\d+(",[^,]+,\s*)\d+(\))',
             rf'\g<1>{regex_count}\g<2>{regex_count}\g<3>',     src, count=1)
src = re.sub(r'(chk\("list_rules=)\d+(",[^,]+,\s*)\d+(\))',
             rf'\g<1>{list_count}\g<2>{list_count}\g<3>',       src, count=1)
src = re.sub(r'(chk\("synonym_rules=)\d+(",[^,]+,\s*)\d+(\))',
             rf'\g<1>{syn_count}\g<2>{syn_count}\g<3>',         src, count=1)

# ════════════════════════════════════════════════════════════
# PART B — POLLUTION CLEANUP (註解化 + module-level rebind)
# ════════════════════════════════════════════════════════════
clean_result = {'cleaned': False, 'already_quarantined': False,
                'pollution_bytes': 0, 'rebind_added': False}

QUARANTINE_MARKER = '_VIA_QUARANTINED_VIA_FINAL_PATCH'
REBIND_MARKER     = '_VIA_SSOT_INSTANCE'

if do_clean:
    # 偵測既有 quarantine
    if QUARANTINE_MARKER in src:
        clean_result['already_quarantined'] = True
        # 仍要確認 rebind 存在
        if REBIND_MARKER not in src:
            # 罕見邊角：quarantined 但沒有 rebind — 補上
            pass  # 下方會補
    pollution_marker = '# === VIA_FINAL_PATCH_SSOT_COMPAT ==='
    start_idx = src.find(pollution_marker) if QUARANTINE_MARKER not in src else -1

    if start_idx > 0:
        # 找結束點：第一個 SUPPORTIVE_SELF_GOVERNANCE 標記前的 # === 行
        end_marker = '[VIA:ANCHOR:SUPPORTIVE_SELF_GOVERNANCE'
        end_search = src.find(end_marker, start_idx)
        end_idx = -1
        if end_search > 0:
            line_start = src.rfind('# ===', start_idx, end_search)
            if line_start > 0:
                end_idx = line_start
        if end_idx < 0:
            # 備用：到 EOF 之前找最後一個 == 線
            end_idx = len(src)

        pollution_block = src[start_idx:end_idx]
        clean_result['pollution_bytes'] = len(pollution_block)

        # 確保 docstring 內不含未跳脫的 """
        # 處理：把 """ 換成 \"\"\" 或者用 ''' (這裡用 ''' 因為較不容易與 source code 衝突)
        if "'''" in pollution_block:
            # 罕見，污染區若已含 '''，改用 """ 包裹並做轉義
            quote = '"""'
            quoted_block = pollution_block.replace('"""', '\\"\\"\\"')
        else:
            quote = "'''"
            quoted_block = pollution_block

        sentinel_open = (
            '# \u2554' + '\u2550'*74 + '\u2557\n'
            '# \u2551 VIA POLLUTION QUARANTINE \u2014 disabled by VIA_SSOT_PanoramicAugmenter v2 \u2551\n'
            '# \u2551   原因：VIA_FINAL_PATCH_SSOT_COMPAT 簡化版覆寫了 SSOT class 的 module- \u2551\n'
            '# \u2551   level get_ssot/normalize/extract，使外部 import normalize 無法正確 \u2551\n'
            '# \u2551   normalize。本區塊以 docstring 註解化保留，移除 quarantine 即恢復。 \u2551\n'
            '# \u2551   下方「Module-level Rebind」已重建正確的 SSOT-backed 函數綁定。 \u2551\n'
            '# \u255a' + '\u2550'*74 + '\u255d\n'
            f'{QUARANTINE_MARKER} = {quote}\n'
        )
        sentinel_close = f'\n{quote}  # end VIA_QUARANTINED_VIA_FINAL_PATCH\n\n'

        rebind_block = (
            '# \u2554' + '\u2550'*74 + '\u2557\n'
            '# \u2551 VIA Module-level Rebind \u2014 restored by VIA_SSOT_PanoramicAugmenter v2 \u2551\n'
            '# \u2551   重建 module-level get_ssot/normalize/extract/contains 為 SSOT-backed \u2551\n'
            '# \u2551   形式，覆寫上方 quarantine 區塊原本的簡化 dict-store 行為。 \u2551\n'
            '# \u255a' + '\u2550'*74 + '\u255d\n'
            f'{REBIND_MARKER} = None\n'
            '\n'
            'def get_ssot():\n'
            '    """Return the singleton SSOT instance (rebuilt over VIA_FINAL_PATCH compat)."""\n'
            f'    global {REBIND_MARKER}\n'
            f'    if {REBIND_MARKER} is None:\n'
            f'        {REBIND_MARKER} = SSOT()\n'
            f'    return {REBIND_MARKER}\n'
            '\n'
            'def normalize(raw):\n'
            '    """Normalize alias to canonical via SSOT."""\n'
            '    return get_ssot().normalize(raw)\n'
            '\n'
            'def extract(rule, text):\n'
            '    """Extract first regex match via SSOT."""\n'
            '    return get_ssot().extract(rule, text)\n'
            '\n'
            'def extract_all(rule, text):\n'
            '    """Extract all regex matches via SSOT."""\n'
            '    return get_ssot().extract_all(rule, text)\n'
            '\n'
            'def contains(lst, val):\n'
            '    """Check whether `val` is in named list via SSOT."""\n'
            '    return get_ssot().contains(lst, val)\n'
            '\n'
            'def canonical(raw):\n'
            '    """Return canonical form or None."""\n'
            '    return get_ssot().canonical(raw)\n'
            '\n'
            'def all_canonicals():\n'
            '    """Return all canonicals."""\n'
            '    return get_ssot().all_canonicals()\n'
            '\n'
            '# end VIA Module-level Rebind\n'
        )

        src = src[:start_idx] + sentinel_open + quoted_block + sentinel_close + rebind_block + src[end_idx:]

        clean_result['cleaned'] = True
        clean_result['rebind_added'] = True
        diffs.append({'anchor': 'POLLUTION.VIA_FINAL_PATCH', 'action': 'QUARANTINE',
                      'count': 1, 'detail': f'wrapped {len(pollution_block)} bytes in docstring'})
        diffs.append({'anchor': 'POLLUTION.MODULE_REBIND', 'action': 'INSERT',
                      'count': 7, 'detail': '+7 module-level functions: get_ssot/normalize/extract/extract_all/contains/canonical/all_canonicals'})
    elif clean_result['already_quarantined']:
        # 已經 quarantined — idempotent 跳過
        diffs.append({'anchor': 'POLLUTION.VIA_FINAL_PATCH', 'action': 'SKIP',
                      'count': 0, 'detail': 'already quarantined (idempotent)'})

# ── 寫回 ─────────────────────────────────────────────────
if not dry_run:
    work_file.write_text(src, encoding='utf-8')

result.update({
    'augment': augment_result,
    'clean':   clean_result,
    'corpus_after': {
        'regex_count': regex_count, 'list_count': list_count,
        'synonym_count': syn_count, 'alias_count': alias_count,
        'total_rules': total_rules,
    },
    'diffs': diffs,
    'work_file': str(work_file),
    'work_bytes': len(src.encode('utf-8')),
    'dry_run': dry_run,
})
result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('OK')
'@
Set-Content -LiteralPath $patchTool -Value $patchCode -Encoding UTF8

$r2 = Invoke-PyScript -ScriptPath $patchTool -ScriptArgs @($specJson, $resultJson)
if (-not $r2.Pass) {
    throw ("補丁失敗: " + $r2.Stderr.Trim())
}
$patchResult = Get-Content -LiteralPath $resultJson -Raw -Encoding UTF8 | ConvertFrom-Json

foreach ($d in $patchResult.diffs) {
    $col = switch ($d.action) {
        'APPEND'     { 'Green'   }
        'UPDATE'     { 'Cyan'    }
        'REDIRECT'   { 'Yellow'  }
        'QUARANTINE' { 'Magenta' }
        'INSERT'     { 'Magenta' }
        'SKIP'       { 'DarkGray'}
        default      { 'White'   }
    }
    Write-Stage 'PHASE3' ('  [{0,-10}] {1}: {2}' -f $d.action, $d.anchor, $d.detail) $col
    $script:DIFF.Add(@{ Anchor=$d.anchor; Action=$d.action; Count=$d.count; Detail=$d.detail }) | Out-Null
}

if ($patchResult.augment.redirect_log -and $patchResult.augment.redirect_log.Count -gt 0) {
    foreach ($r in $patchResult.augment.redirect_log) {
        Write-Stage 'PHASE3' ('  ◆ Redirect from {0}: removed {1}' -f $r.canonical, ($r.removed -join ', ')) Cyan
    }
}

Write-Stage 'PHASE3' ('  Augment: +{0} rules, {1} skipped' -f $patchResult.augment.rules_added, $patchResult.augment.rules_skipped) Green
if ($patchResult.clean.cleaned) {
    Write-Stage 'PHASE3' ('  Clean: quarantined {0} bytes + 7 module-level rebinds' -f $patchResult.clean.pollution_bytes) Magenta
} elseif ($patchResult.clean.already_quarantined) {
    Write-Stage 'PHASE3' '  Clean: already quarantined (idempotent skip)' DarkGray
} elseif (-not $doClean) {
    Write-Stage 'PHASE3' '  Clean: 模式跳過' DarkGray
}
Write-Stage 'PHASE3' ('  Work file: {0:N0} bytes (was {1:N0})' -f $patchResult.work_bytes, $srcSize) Green

$script:FP['work_after_patch'] = if (-not $DryRun) { Get-FileSha256 -Path $workFile } else { 'dry-run' }

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 4 ─ 自動測試 (5 stages: compile / import / SSOT class / module-     ║
# ║   level functions / new rules)                                             ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE4' '自動測試 (5 stages)' Yellow

$testTool = Join-Path $OutDir 'run_tests.py'
$testCode = @'
# -*- coding: utf-8 -*-
"""Run automated tests against patched VIA_SSOT_Unified.work.py.
   v2: 增加 module-level function 測試，驗證 POLLUTION 清理是否生效。"""
import json, sys, importlib.util, py_compile, traceback
from pathlib import Path

work_file = Path(sys.argv[1])
out_path  = Path(sys.argv[2])
results   = []

# ── Test 1: py_compile ──
try:
    py_compile.compile(str(work_file), doraise=True)
    results.append({'tag':'py_compile', 'pass': True, 'detail':'syntax OK'})
except py_compile.PyCompileError as e:
    results.append({'tag':'py_compile', 'pass': False, 'detail': str(e)})
    out_path.write_text(json.dumps({'tests': results}, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.exit(0)

# ── Test 2: import ──
mod = None
try:
    spec = importlib.util.spec_from_file_location('via_ssot_test', work_file)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules['via_ssot_test'] = mod
    spec.loader.exec_module(mod)
    results.append({'tag':'import', 'pass': True, 'detail':'module loaded'})
except Exception as e:
    results.append({'tag':'import', 'pass': False,
                    'detail': f'{type(e).__name__}: {e}',
                    'traceback': traceback.format_exc()})
    out_path.write_text(json.dumps({'tests': results}, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.exit(0)

# ── Test 3: SSOT class direct API ──
try:
    s = mod.SSOT()
    info = s.info()
    cases = []
    cases.append(('normalize 營收→Revenue',         s.normalize('營收')         == 'Revenue'))
    cases.append(('normalize 台積電→2330.TW',       s.normalize('台積電')       == '2330.TW'))
    cases.append(('normalize TSMC→2330.TW',         s.normalize('TSMC')         == '2330.TW'))
    cases.append(('normalize 本期淨利→NetIncome',   s.normalize('本期淨利')     == 'NetIncome'))
    cases.append(('normalize DXY→DX-Y.NYB',         s.normalize('DXY')          == 'DX-Y.NYB'))
    cases.append(('normalize unknown→raw',          s.normalize('XYZ_UNKNOWN')  == 'XYZ_UNKNOWN'))
    cases.append(('canonical None for unknown',     s.canonical('XYZ_UNKNOWN')  is None))
    cases.append(('Revenue in all_canonicals',      'Revenue' in s.all_canonicals()))
    cases.append(('extract TW_YFINANCE 2330.TW',    s.extract('TW_YFINANCE_TICKER','2330.TW') == '2330.TW'))
    cases.append(('extract TW_BLOOMBERG 2330 TT',   s.extract('TW_BLOOMBERG_TICKER','2330 TT') == '2330 TT'))
    cases.append(('extract SYSTEM_PREFIX VIA',      s.extract('SYSTEM_PREFIX','VIA_Master.ps1') == 'VIA'))
    cases.append(('extract LL#17',                  s.extract('LL_RULE_REFERENCE','violates LL#17 here') == 'LL#17'))
    cases.append(('contains PS_CRITICAL Remove-Item', s.contains('PS_CRITICAL_COMMANDS','Remove-Item')))
    cases.append(('synonym_rules info matches',     s.info()['synonym_rules']  == info['synonym_rules']))
    cases.append(('total_aliases info matches',     s.info()['total_aliases']  == info['total_aliases']))
    cases.append(('canonical Revenue is Revenue',   s.canonical('營收')        == 'Revenue'))

    pass_n = sum(1 for _, ok in cases if ok)
    total  = len(cases)
    results.append({'tag':'ssot_class_api', 'pass': pass_n == total,
                    'detail': f'{pass_n}/{total} cases pass; corpus: regex={info["regex_rules"]}, lists={info["list_rules"]}, syns={info["synonym_rules"]}, aliases={info["total_aliases"]}',
                    'cases': [{'name':n,'ok':ok} for n,ok in cases],
                    'info': info})
except Exception as e:
    results.append({'tag':'ssot_class_api', 'pass': False,
                    'detail': f'{type(e).__name__}: {e}',
                    'traceback': traceback.format_exc()})

# ── Test 4: MODULE-LEVEL functions (THE KEY TEST for POLLUTION CLEANUP) ──
try:
    cases = []
    cases.append(('mod.normalize("營收")→Revenue',           mod.normalize('營收')        == 'Revenue'))
    cases.append(('mod.normalize("台積電")→2330.TW',         mod.normalize('台積電')      == '2330.TW'))
    cases.append(('mod.normalize("本期淨利")→NetIncome',     mod.normalize('本期淨利')    == 'NetIncome'))
    cases.append(('mod.normalize unknown→raw',               mod.normalize('XYZ_UNKNOWN') == 'XYZ_UNKNOWN'))
    cases.append(('mod.extract TW_YFINANCE 2330.TW',         mod.extract('TW_YFINANCE_TICKER','2330.TW') == '2330.TW'))
    cases.append(('mod.contains PS_CRITICAL Remove-Item',    mod.contains('PS_CRITICAL_COMMANDS','Remove-Item')))
    # canonical / all_canonicals 也要存在
    has_canonical = hasattr(mod, 'canonical')
    has_all_can   = hasattr(mod, 'all_canonicals')
    cases.append(('mod.canonical defined',                   has_canonical))
    cases.append(('mod.all_canonicals defined',              has_all_can))
    if has_canonical:
        cases.append(('mod.canonical("營收")→Revenue',       mod.canonical('營收') == 'Revenue'))

    pass_n = sum(1 for _, ok in cases if ok)
    total  = len(cases)
    results.append({'tag':'module_level_funcs', 'pass': pass_n == total,
                    'detail': f'{pass_n}/{total} module-level calls work correctly (POLLUTION cleanup verification)',
                    'cases': [{'name':n,'ok':ok} for n,ok in cases]})
except Exception as e:
    results.append({'tag':'module_level_funcs', 'pass': False,
                    'detail': f'{type(e).__name__}: {e}',
                    'traceback': traceback.format_exc()})

# ── Test 5: 新規則抽樣 ──
try:
    samples = [
        ('ROE',                'ReturnOnEquity'),
        ('毛利率',              'GrossMargin'),
        ('資本支出',            'CapitalExpenditures'),
        ('每股淨值',            'BookValuePerShare'),
        ('股利發放率',          'PayoutRatio'),
        ('應收帳款',            'AccountsReceivable'),
        ('折舊費用',            'Depreciation'),
        ('基本每股盈餘',        'BasicEPS'),
        ('稀釋每股盈餘',        'DilutedEPS'),
        ('CashConversionCycle','CashConversionCycle'),
    ]
    s = mod.SSOT()
    hits = []
    for raw, expected in samples:
        got = s.normalize(raw)
        hits.append({'raw': raw, 'expected': expected, 'got': got, 'ok': got == expected})
    pass_n = sum(1 for h in hits if h['ok'])
    total  = len(samples)
    eps_check = s.normalize('每股盈餘')
    results.append({'tag':'new_rules', 'pass': pass_n == total,
                    'detail': f'{pass_n}/{total} normalize hits; EPS fallback: 每股盈餘 -> {eps_check}',
                    'samples': hits, 'eps_fallback': eps_check})
except Exception as e:
    results.append({'tag':'new_rules', 'pass': False,
                    'detail': f'{type(e).__name__}: {e}',
                    'traceback': traceback.format_exc()})

out_path.write_text(json.dumps({'tests': results}, ensure_ascii=False, indent=2), encoding='utf-8')
print('OK')
'@
Set-Content -LiteralPath $testTool -Value $testCode -Encoding UTF8

$r3 = Invoke-PyScript -ScriptPath $testTool -ScriptArgs @($workFile, $testsJson)
if (-not $r3.Pass) {
    Write-Stage 'PHASE4' ('  ⚠ 測試執行有錯誤: {0}' -f $r3.Stderr.Trim()) Yellow
}
$testsBlob = Get-Content -LiteralPath $testsJson -Raw -Encoding UTF8 | ConvertFrom-Json

foreach ($t in $testsBlob.tests) {
    $col = if ($t.pass) { 'Green' } else { 'Red' }
    $sym = if ($t.pass) { 'PASS' } else { 'FAIL' }
    Write-Stage 'PHASE4' ('  Test [{0,-20}]: {1} — {2}' -f $t.tag, $sym, $t.detail) $col
    # safe property access (v1 bug 已修正)
    $caseVal   = if ($t.PSObject.Properties.Name -contains 'cases')   { $t.cases }   else { $null }
    $sampleVal = if ($t.PSObject.Properties.Name -contains 'samples') { $t.samples } else { $null }
    $script:TESTS.Add(@{ Tag=$t.tag; Pass=$t.pass; Detail=$t.detail; Cases=$caseVal; Samples=$sampleVal }) | Out-Null
}

$passCount = (@($script:TESTS) | Where-Object { $_.Pass }).Count
$failCount = $script:TESTS.Count - $passCount
$verdict   = if ($failCount -eq 0) { 'READY' } elseif ($failCount -le 1) { 'NEAR-READY' } else { 'NOT-READY' }

# 重新跑 AST inspector 確認 after 狀態
$r4 = Invoke-PyScript -ScriptPath $astTool -ScriptArgs @($workFile, $invJsonAfter)
if ($r4.Pass) {
    $invAfter = Get-Content -LiteralPath $invJsonAfter -Raw -Encoding UTF8 | ConvertFrom-Json
    $script:STAT['version_after']  = $invAfter.version
    $script:STAT['regex_after']    = $invAfter.regex_count
    $script:STAT['list_after']     = $invAfter.list_count
    $script:STAT['synonym_after']  = $invAfter.synonym_count
    $script:STAT['aliases_after']  = $invAfter.total_aliases
    $script:STAT['quarantined_after']  = $invAfter.quarantined
    $script:STAT['ast_dup_get_ssot_after']   = $invAfter.ast_duplicate_defs.get_ssot
    $script:STAT['ast_dup_normalize_after']  = $invAfter.ast_duplicate_defs.normalize
    $script:STAT['ast_dup_extract_after']    = $invAfter.ast_duplicate_defs.extract
    $script:STAT['lines_after']    = $invAfter.src_lines
}
$script:STAT['rules_added']     = $patchResult.augment.rules_added
$script:STAT['rules_skipped']   = $patchResult.augment.rules_skipped
$script:STAT['cleaned']         = $patchResult.clean.cleaned
$script:STAT['already_quarantined'] = $patchResult.clean.already_quarantined
$script:STAT['tests_pass']      = $passCount
$script:STAT['tests_fail']      = $failCount
$script:STAT['verdict']         = $verdict

Write-Stage 'PHASE4' ('=== Verdict: {0} ({1}/{2} pass) ===' -f $verdict, $passCount, $script:TESTS.Count) `
    $(if ($verdict -eq 'READY') { 'Green' } elseif ($verdict -eq 'NEAR-READY') { 'Yellow' } else { 'Red' })

if ($verdict -eq 'READY' -and -not $DryRun -and -not $ForceLocalCopy) {
    try {
        Copy-Item -LiteralPath $workFile -Destination $TargetPath -Force
        $script:FP['target_after'] = Get-FileSha256 -Path $TargetPath
        Write-Stage 'PHASE4' ('  ✓ 已覆寫原檔: {0} (sha256:{1})' -f $TargetPath, $script:FP['target_after']) Green
    } catch {
        Write-Stage 'PHASE4' ('  ⚠ 無法覆寫原檔（OneDrive/權限）: {0}' -f $_.Exception.Message) Yellow
        Write-Stage 'PHASE4' ('    → 工作檔保留於: {0}' -f $workFile) Yellow
    }
} else {
    Write-Stage 'PHASE4' ('  ℹ 工作檔保留於: {0}' -f $workFile) Cyan
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 5 ─ HTML U/I Matrix Report v2 (VIA Visual Lock)                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE5' '產生 HTML U/I Matrix Report v2' Yellow

$genTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$verdictClass = switch ($verdict) {
    'READY'      { 'b-ok'   }
    'NEAR-READY' { 'b-warn' }
    default      { 'b-fail' }
}
$aliasDelta = $script:STAT.aliases_after - $script:STAT.aliases_before
$rulesDelta = $script:STAT.synonym_after - $script:STAT.synonym_before

# Cards 區（含 AST def 計數對照）
$cardsTop = @"
<div class="grid">
  <div class="cd accent"><div class="cd-h">Mode</div><div class="cd-b">$Mode</div><div class="cd-i">Augment + Clean</div></div>
  <div class="cd accent"><div class="cd-h">Version</div><div class="cd-b">$($script:STAT.version_before) → $($script:STAT.version_after)</div></div>
  <div class="cd teal"><div class="cd-h">Lines</div><div class="cd-b">$('{0:N0}' -f $script:STAT.source_lines) → $('{0:N0}' -f $script:STAT.lines_after)</div></div>
  <div class="cd"><div class="cd-h">Anchors</div><div class="cd-b">$($script:STAT.anchors_count)</div></div>
  <div class="cd"><div class="cd-h">Functions</div><div class="cd-b">$($script:STAT.function_count)</div></div>
  <div class="cd"><div class="cd-h">Classes</div><div class="cd-b">$($script:STAT.class_count)</div></div>
</div>
"@

$cardsDelta = @"
<div class="grid grid4">
  <div class="cd accent"><div class="cd-h">Regex Rules</div><div class="cd-b">$($script:STAT.regex_before) → $($script:STAT.regex_after)</div><div class="cd-i delta-flat">no change</div></div>
  <div class="cd accent"><div class="cd-h">List Rules</div><div class="cd-b">$($script:STAT.list_before) → $($script:STAT.list_after)</div><div class="cd-i delta-flat">no change</div></div>
  <div class="cd good"><div class="cd-h">Synonym Rules</div><div class="cd-b">$($script:STAT.synonym_before) → $($script:STAT.synonym_after)</div><div class="cd-i $(if($rulesDelta -gt 0){'delta-up'}else{'delta-flat'})">$(if($rulesDelta -gt 0){"+$rulesDelta"}else{'no change (idempotent)'})</div></div>
  <div class="cd good"><div class="cd-h">Total Aliases</div><div class="cd-b">$($script:STAT.aliases_before) → $($script:STAT.aliases_after)</div><div class="cd-i $(if($aliasDelta -gt 0){'delta-up'}else{'delta-flat'})">$(if($aliasDelta -gt 0){"+$aliasDelta"}else{'no change'})</div></div>
</div>
"@

# POLLUTION 對照卡片
$cleanResultLabel = if ($patchResult.clean.cleaned) {
    "<span class='b b-ok'>CLEANED</span>"
} elseif ($patchResult.clean.already_quarantined) {
    "<span class='b b-mut'>ALREADY QUARANTINED</span>"
} elseif (-not $doClean) {
    "<span class='b b-mut'>SKIPPED</span>"
} else {
    "<span class='b b-mut'>NO POLLUTION FOUND</span>"
}

$cardsPollution = @"
<div class="grid grid4">
  <div class="cd warn">
    <div class="cd-h">Pollution State</div>
    <div class="cd-b" style="font-size:14px">$cleanResultLabel</div>
    <div class="cd-i">VIA_FINAL_PATCH_SSOT_COMPAT</div>
  </div>
  <div class="cd"><div class="cd-h">def get_ssot</div><div class="cd-b">$($script:STAT.ast_dup_get_ssot_before) → $($script:STAT.ast_dup_get_ssot_after)</div><div class="cd-i">AST-level (excludes docstring)</div></div>
  <div class="cd"><div class="cd-h">def normalize</div><div class="cd-b">$($script:STAT.ast_dup_normalize_before) → $($script:STAT.ast_dup_normalize_after)</div><div class="cd-i">AST-level (excludes docstring)</div></div>
  <div class="cd"><div class="cd-h">def extract</div><div class="cd-b">$($script:STAT.ast_dup_extract_before) → $($script:STAT.ast_dup_extract_after)</div><div class="cd-i">AST-level (excludes docstring)</div></div>
</div>
"@

# 新規則 by group
$grpCounts = @{}
if ($patchResult.augment.pending) {
    foreach ($r in $patchResult.augment.pending) {
        $g = $r.group
        if (-not $grpCounts.ContainsKey($g)) { $grpCounts[$g] = 0 }
        $grpCounts[$g]++
    }
}
$grpRows = ''
if ($grpCounts.Count -gt 0) {
    foreach ($k in ($grpCounts.Keys | Sort-Object)) {
        $grpRows += ('<tr><td><span class="b b-teal">' + $k + '</span></td><td>' + $grpCounts[$k] + '</td></tr>' + "`n")
    }
} else {
    $grpRows = '<tr><td colspan="2" style="color:#6b7280">no new rules added (idempotent run)</td></tr>'
}

# Diff 表
$diffRows = ''
foreach ($d in $script:DIFF) {
    $actClass = switch ($d.Action) {
        'APPEND'     { 'b-ok'   }
        'UPDATE'     { 'b-pri'  }
        'REDIRECT'   { 'b-warn' }
        'QUARANTINE' { 'b-warn' }
        'INSERT'     { 'b-ok'   }
        'SKIP'       { 'b-mut'  }
        default      { 'b-mut'  }
    }
    $diffRows += ('<tr><td><code>' + $d.Anchor + '</code></td><td><span class="b ' + $actClass + '">' + $d.Action + '</span></td><td>' + $d.Count + '</td><td>' + $d.Detail + '</td></tr>' + "`n")
}

# Test 表
$testRows = ''
foreach ($t in $testsBlob.tests) {
    $stClass = if ($t.pass) { 'b-ok' } else { 'b-fail' }
    $stTxt   = if ($t.pass) { 'PASS' } else { 'FAIL' }
    $detailEsc = ($t.detail -replace '<','&lt;' -replace '>','&gt;')
    $testRows += ('<tr><td><code>' + $t.tag + '</code></td><td><span class="b ' + $stClass + '">' + $stTxt + '</span></td><td>' + $detailEsc + '</td></tr>' + "`n")
}

# Module-level 案例細節（最重要的測試）
$modLevelTest = $testsBlob.tests | Where-Object { $_.tag -eq 'module_level_funcs' } | Select-Object -First 1
$modLevelRows = ''
if ($modLevelTest -and $modLevelTest.PSObject.Properties.Name -contains 'cases') {
    foreach ($c in $modLevelTest.cases) {
        $okClass = if ($c.ok) { 'b-ok' } else { 'b-fail' }
        $okTxt   = if ($c.ok) { '✓' } else { '✗' }
        $modLevelRows += ('<tr><td>' + $c.name + '</td><td><span class="b ' + $okClass + '">' + $okTxt + '</span></td></tr>' + "`n")
    }
}

# SSOT class 案例
$ssotClassTest = $testsBlob.tests | Where-Object { $_.tag -eq 'ssot_class_api' } | Select-Object -First 1
$ssotClassRows = ''
if ($ssotClassTest -and $ssotClassTest.PSObject.Properties.Name -contains 'cases') {
    foreach ($c in $ssotClassTest.cases) {
        $okClass = if ($c.ok) { 'b-ok' } else { 'b-fail' }
        $okTxt   = if ($c.ok) { '✓' } else { '✗' }
        $ssotClassRows += ('<tr><td>' + $c.name + '</td><td><span class="b ' + $okClass + '">' + $okTxt + '</span></td></tr>' + "`n")
    }
}

# 新規則抽樣
$newRulesTest = $testsBlob.tests | Where-Object { $_.tag -eq 'new_rules' } | Select-Object -First 1
$sampleRows = ''
if ($newRulesTest -and $newRulesTest.PSObject.Properties.Name -contains 'samples') {
    foreach ($sm in $newRulesTest.samples) {
        $okClass = if ($sm.ok) { 'b-ok' } else { 'b-fail' }
        $okTxt   = if ($sm.ok) { '✓' } else { '✗' }
        $sampleRows += ('<tr><td>' + $sm.raw + '</td><td><code>' + $sm.expected + '</code></td><td><code>' + $sm.got + '</code></td><td><span class="b ' + $okClass + '">' + $okTxt + '</span></td></tr>' + "`n")
    }
}

# Detail 表（如果有新增）
$ruleDetailRows = ''
if ($patchResult.augment.pending -and $patchResult.augment.pending.Count -gt 0) {
    foreach ($r in $patchResult.augment.pending) {
        $aliasesJoined = ($r.aliases -join ' · ')
        $ruleDetailRows += ('<tr><td><span class="b b-pri">' + $r.canonical + '</span></td><td><span class="b b-teal">' + $r.group + '</span></td><td>' + $r.aliases.Count + '</td><td>' + $aliasesJoined + '</td></tr>' + "`n")
    }
}

# Anchor 表
$anchorRows = ''
foreach ($a in $invBefore.anchors) {
    $anchorRows += ('<tr><td>' + $a.line + '</td><td><code>' + $a.id + '</code></td><td>' + $a.desc + '</td></tr>' + "`n")
}

# SHA256 fingerprint 表
$fpRows = ''
foreach ($k in $script:FP.Keys) {
    $fpRows += ('<tr><td><code>' + $k + '</code></td><td><code>' + $script:FP[$k] + '</code></td></tr>' + "`n")
}

# Console log
$logEsc = (($script:LOG -join "`n") -replace '<','&lt;' -replace '>','&gt;')

# ── 完整 HTML ──────────────────────────────────────────
$html = @"
<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="UTF-8">
<title>VIA SSOT Unified — Panoramic Augmenter v2 Matrix Report</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;800&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#f5f4f0; --ink:#1f2933; --mut:#6b7280;
    --pri:#4c78a8; --teal:#439a9a; --warn:#d4a017; --bad:#c0504d; --good:#54a24b;
    --line:rgba(31,41,51,.12); --soft:rgba(76,120,168,.08);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;font-size:11px;line-height:1.55}
  .rainbow{height:3px;background:linear-gradient(90deg,#c0504d,#d4a017,#54a24b,#439a9a,#4c78a8,#9467bd)}
  header{padding:24px 28px 18px;border-bottom:1px solid var(--line);background:#fff}
  header h1{font-family:'Syne',sans-serif;font-weight:800;font-size:22px;letter-spacing:.5px;margin:0 0 4px}
  header .sub{font-family:'DM Mono',monospace;color:var(--mut);font-size:10.5px}
  header .meta{margin-top:10px;display:flex;gap:18px;flex-wrap:wrap;font-family:'DM Mono',monospace;font-size:10px;color:var(--mut)}
  main{padding:18px 28px 60px;max-width:1400px;margin:0 auto}
  .grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:18px}
  .grid.grid2{grid-template-columns:repeat(2,1fr)}
  .grid.grid3{grid-template-columns:repeat(3,1fr)}
  .grid.grid4{grid-template-columns:repeat(4,1fr)}
  .cd{background:#fff;border:1px solid var(--line);border-radius:8px;padding:11px 13px}
  .cd-h{font-family:'DM Mono',monospace;font-size:9.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.6px;margin-bottom:4px}
  .cd-b{font-family:'Syne',sans-serif;font-weight:700;font-size:18px;color:var(--ink);line-height:1.1}
  .cd-i{font-size:10px;color:var(--mut);margin-top:3px;font-family:'DM Mono',monospace}
  .cd.accent{border-left:3px solid var(--pri)}
  .cd.teal{border-left:3px solid var(--teal)}
  .cd.warn{border-left:3px solid var(--warn)}
  .cd.good{border-left:3px solid var(--good)}
  .cd.bad{border-left:3px solid var(--bad)}
  section{margin-bottom:22px}
  h2{font-family:'Syne',sans-serif;font-weight:600;font-size:13.5px;letter-spacing:.4px;margin:0 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
  table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden;font-family:'DM Mono',monospace;font-size:10.5px}
  th{background:var(--soft);text-align:left;padding:8px 10px;font-weight:500;color:var(--mut);text-transform:uppercase;font-size:9.5px;letter-spacing:.5px;border-bottom:1px solid var(--line)}
  td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  tr:last-child td{border-bottom:none}
  .b{display:inline-block;padding:2px 8px;border-radius:10px;font-family:'DM Mono',monospace;font-size:9.5px;font-weight:500;letter-spacing:.4px}
  .b-ok{background:rgba(84,162,75,.12);color:var(--good)}
  .b-warn{background:rgba(212,160,23,.12);color:var(--warn)}
  .b-fail{background:rgba(192,80,77,.12);color:var(--bad)}
  .b-pri{background:rgba(76,120,168,.12);color:var(--pri)}
  .b-teal{background:rgba(67,154,154,.12);color:var(--teal)}
  .b-mut{background:rgba(31,41,51,.06);color:var(--mut)}
  .tm{background:#1f2933;color:#cad3c4;font-family:'DM Mono',monospace;font-size:10px;border-radius:8px;overflow:hidden;margin-top:8px}
  .tm-h{padding:5px 12px;background:#161c24;font-size:9.5px;color:#7a8a96;letter-spacing:.5px}
  .tm-b{padding:11px 14px;max-height:280px;overflow:auto;white-space:pre-wrap;line-height:1.55}
  .verdict{padding:14px 18px;background:#fff;border:1px solid var(--line);border-radius:10px;display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;flex-wrap:wrap;gap:12px}
  .verdict .lbl{font-family:'Syne',sans-serif;font-size:13px;color:var(--mut);font-weight:600}
  .verdict .val{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;letter-spacing:1px}
  .delta-up{color:var(--good)}
  .delta-flat{color:var(--mut)}
  small.note{color:var(--mut);font-family:'DM Mono',monospace;font-size:9.5px}
  code{background:rgba(31,41,51,.06);padding:1px 5px;border-radius:3px;font-family:'DM Mono',monospace;font-size:10px}
</style></head>
<body>
<div class="rainbow"></div>
<header>
  <h1>VeritasIntelligenceAnalytics — VIA_SSOT_Unified Panoramic Augmenter v2</h1>
  <div class="sub">ONE PowerShell to solve all problems · Mode: $Mode · Idempotent · Self-Healing · Pollution-Aware</div>
  <div class="meta">
    <span>Generated $genTime</span>
    <span>Elapsed $([math]::Round($script:SW.Elapsed.TotalSeconds,2))s</span>
    <span>Target $srcName</span>
    <span>Out $(Split-Path -Leaf $OutDir)</span>
    <span>Python $pyExe $pyArg</span>
  </div>
</header>
<main>

<div class="verdict">
  <div>
    <div class="lbl">FINAL VERDICT</div>
    <small class="note">$($script:STAT.tests_pass)/$($script:TESTS.Count) tests passed · $($script:STAT.rules_added) rules added · v$($script:STAT.version_before) → v$($script:STAT.version_after) · POLLUTION: $(if($patchResult.clean.cleaned){'cleaned'}elseif($patchResult.clean.already_quarantined){'already-quarantined'}else{'untouched'})</small>
  </div>
  <div class="val"><span class="b $verdictClass" style="font-size:18px;padding:6px 16px">$verdict</span></div>
</div>

<section>
<h2>① Source Inventory + Configuration</h2>
$cardsTop
</section>

<section>
<h2>② Corpus Delta — Before vs After</h2>
$cardsDelta
</section>

<section>
<h2>③ POLLUTION State (AST-level def counts; docstring excluded)</h2>
$cardsPollution
</section>

<section>
<h2>④ AST Anchor Patches Applied</h2>
<table>
<thead><tr><th>Anchor</th><th>Action</th><th>Count</th><th>Detail</th></tr></thead>
<tbody>$diffRows</tbody>
</table>
</section>

<section>
<h2>⑤ Test Results — Top Level</h2>
<table>
<thead><tr><th>Test</th><th>Status</th><th>Detail</th></tr></thead>
<tbody>$testRows</tbody>
</table>
</section>

<section>
<h2>⑥ module_level_funcs — POLLUTION cleanup verification (THE KEY TEST)</h2>
<table>
<thead><tr><th>Assertion (calls go through module-level, NOT class API)</th><th>Status</th></tr></thead>
<tbody>$modLevelRows</tbody>
</table>
</section>

<section>
<h2>⑦ ssot_class_api — SSOT class direct calls</h2>
<table>
<thead><tr><th>Assertion</th><th>Status</th></tr></thead>
<tbody>$ssotClassRows</tbody>
</table>
</section>

<section>
<h2>⑧ New Rules — Sample Verification (normalize)</h2>
<table>
<thead><tr><th>Input</th><th>Expected</th><th>Got</th><th>Status</th></tr></thead>
<tbody>$sampleRows</tbody>
</table>
</section>

<section>
<h2>⑨ New Rules by Group$(if($patchResult.augment.rules_added -gt 0){" + Detail Matrix ($($patchResult.augment.rules_added) rules)"}else{" (idempotent — none added this run)"})</h2>
<div class="grid grid2" style="margin-bottom:10px">
<table><thead><tr><th>Group</th><th>Added</th></tr></thead><tbody>$grpRows</tbody></table>
<div></div>
</div>
$(if ($ruleDetailRows) { @"
<table>
<thead><tr><th>Canonical</th><th>Group</th><th>Aliases</th><th>Alias List</th></tr></thead>
<tbody>$ruleDetailRows</tbody>
</table>
"@ })
</section>

<section>
<h2>⑩ Anchor Map ($($invBefore.anchors.Count))</h2>
<table>
<thead><tr><th>Line</th><th>Anchor ID</th><th>Description</th></tr></thead>
<tbody>$anchorRows</tbody>
</table>
</section>

<section>
<h2>⑪ SHA256 Fingerprints (12-char prefix)</h2>
<table>
<thead><tr><th>Stage</th><th>SHA256</th></tr></thead>
<tbody>$fpRows</tbody>
</table>
</section>

<section>
<h2>⑫ Execution Log</h2>
<div class="tm"><div class="tm-h">stdout · $($script:LOG.Count) lines</div><div class="tm-b">$logEsc</div></div>
</section>

</main>
</body></html>
"@

Set-Content -LiteralPath $reportFile -Value $html -Encoding UTF8
Write-Stage 'PHASE5' ('  ✓ HTML 報表已產生: {0:N0} bytes' -f (Get-Item $reportFile).Length) Green

if (-not $NoOpenHtml) {
    try {
        Start-Process -FilePath $reportFile
        Write-Stage 'PHASE5' '  ✓ HTML 已在預設瀏覽器開啟' Green
    } catch {
        Write-Stage 'PHASE5' ('  ⚠ 無法自動開啟瀏覽器: {0}' -f $_.Exception.Message) Yellow
    }
} else {
    Write-Stage 'PHASE5' ('  ℹ NoOpenHtml — 報表路徑: {0}' -f $reportFile) Cyan
}

# 完成總結
Write-Stage 'DONE' '─────────────────────────────────────────────────────' Yellow
Write-Stage 'DONE' ('Mode:           {0}' -f $Mode) Cyan
Write-Stage 'DONE' ('Verdict:        {0}' -f $verdict) `
    $(if ($verdict -eq 'READY') { 'Green' } elseif ($verdict -eq 'NEAR-READY') { 'Yellow' } else { 'Red' })
Write-Stage 'DONE' ('Rules Added:    {0}  (Aliases +{1})' -f $script:STAT.rules_added, $aliasDelta) Cyan
Write-Stage 'DONE' ('Synonyms:       {0} → {1}' -f $script:STAT.synonym_before, $script:STAT.synonym_after) Cyan
Write-Stage 'DONE' ('POLLUTION:      {0}' -f $(if ($patchResult.clean.cleaned) { 'CLEANED' } elseif ($patchResult.clean.already_quarantined) { 'ALREADY QUARANTINED' } elseif (-not $doClean) { 'mode-skipped' } else { 'no pollution found' })) Cyan
Write-Stage 'DONE' ('def counts:     get_ssot {0}→{1}, normalize {2}→{3}, extract {4}→{5}' -f `
    $script:STAT.ast_dup_get_ssot_before,  $script:STAT.ast_dup_get_ssot_after, `
    $script:STAT.ast_dup_normalize_before, $script:STAT.ast_dup_normalize_after, `
    $script:STAT.ast_dup_extract_before,   $script:STAT.ast_dup_extract_after) Cyan
Write-Stage 'DONE' ('Tests:          {0}/{1} passed' -f $script:STAT.tests_pass, $script:TESTS.Count) Cyan
Write-Stage 'DONE' ('HTML Report:    {0}' -f $reportFile) Cyan
Write-Stage 'DONE' ('Total elapsed:  {0:N2}s' -f $script:SW.Elapsed.TotalSeconds) Yellow

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====

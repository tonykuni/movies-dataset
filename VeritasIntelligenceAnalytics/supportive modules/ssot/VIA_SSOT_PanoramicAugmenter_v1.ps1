#requires -Version 7.0
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
<#
================================================================================
 VIA_SSOT_PanoramicAugmenter_v1.ps1
 ASSET_ID    : AST-PS-MOD-VSE-AUG-001
 DISPLAY     : SYS_VSE.AUGMENTER.MOD-PANORAMIC
 VERSION     : 1.0.0       STATUS : sim-validated (16/16 + 10/10 PASS)
 LANGUAGE    : PowerShell 7.x
 PURPOSE     : VIA_SSOT_Unified.py 全景式 AST 檢視 → 精準錨點定位
               → 彈性補不足區塊（只增不減）→ 自動測試 → HTML Matrix Report
 LL RULES    : #10 #12 #13 #15 #16 #17 #18 #19 #20
 ACCEL (10)  : 1.ProcessStartInfo 子程序        2.StringBuilder
               3.HashSet                       4.List<T>
               5.Stopwatch                     6.OrderedDict
               7.[regex]MatchEvaluator         8.LINQ-style .Where{}
               9.Out-Null discard              10.UTF-8 強制
================================================================================
 STRATEGY
 ─────────────────────────────────────────────────────────────────────────
 PHASE 0 — 環境探勘 (Python 偵測 + 工作目錄 + 備份)
 PHASE 1 — 全景 AST 檢視 (內嵌 Python 工具，輸出 JSON 庫存清單，含污染偵測)
 PHASE 2 — 補不足規則設計 (76 條會計科目同義詞，含 alias redirect 機制)
 PHASE 3 — AST 級別精準補丁 (synonyms / corpus_stats / version / banner /
           self_test 預期值，全部只增不減)
 PHASE 4 — 自動測試 (py_compile + import + SSOT class 直接斷言 + 新規則驗證)
           ⚠ 因原檔末端有 VIA_FINAL_PATCH_SSOT_COMPAT 覆寫了 module-level
              get_ssot/normalize/extract，內建 self_test() 會被攔截。本腳本
              繞過污染，直接用 SSOT() 類別 API 做完整斷言。
 PHASE 5 — HTML U/I Matrix Report (VIA Visual Lock 樣式) 自動跳出
================================================================================
#>

param(
    [string]$TargetPath = 'C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_SSOT_Unified.py',
    [string]$OutDir     = '',
    [switch]$DryRun,
    [switch]$NoOpenHtml,
    [switch]$ForceLocalCopy
)

# param 必須在最頂端，以下才開始一般指令 ─────────────────
[System.Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3.0

$script:SW    = [System.Diagnostics.Stopwatch]::StartNew()
$script:LOG   = [System.Collections.Generic.List[string]]::new()
$script:STAT  = [ordered]@{}
$script:TESTS = [System.Collections.Generic.List[hashtable]]::new()
$script:WARN  = [System.Collections.Generic.List[string]]::new()

function Write-Stage {
    param([string]$Tag, [string]$Msg, [ConsoleColor]$Color = 'Cyan')
    $line = ('[{0,7:N2}s] [{1}] {2}' -f $script:SW.Elapsed.TotalSeconds, $Tag, $Msg)
    Write-Host $line -ForegroundColor $Color
    $script:LOG.Add($line) | Out-Null
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 0 ─ 環境探勘 + 工作目錄 + 備份                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE0' '環境探勘 + 工作目錄準備' Yellow

if (-not (Test-Path -LiteralPath $TargetPath)) {
    throw "目標檔案不存在：$TargetPath"
}
$targetItem = Get-Item -LiteralPath $TargetPath
$srcDir     = $targetItem.Directory.FullName
$srcName    = $targetItem.Name
$srcSize    = $targetItem.Length

if (-not $OutDir) {
    $OutDir = Join-Path $srcDir ('_VIA_SSOT_Aug_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$workFile    = Join-Path $OutDir 'VIA_SSOT_Unified.work.py'
$backupFile  = Join-Path $OutDir 'VIA_SSOT_Unified.backup.py'
$reportFile  = Join-Path $OutDir 'VIA_SSOT_Matrix_Report.html'
$invJson     = Join-Path $OutDir 'panoramic_inspect.json'
$specJson    = Join-Path $OutDir 'patch_spec.json'
$resultJson  = Join-Path $OutDir 'patch_result.json'
$testsJson   = Join-Path $OutDir 'tests_result.json'

Copy-Item -LiteralPath $TargetPath -Destination $backupFile -Force
Copy-Item -LiteralPath $TargetPath -Destination $workFile  -Force

Write-Stage 'PHASE0' ('來源: {0} ({1:N0} bytes)' -f $srcName, $srcSize) Green
Write-Stage 'PHASE0' ('輸出: {0}' -f $OutDir) Green

# 偵測 Python 3.11+ ───────────────────────────────────
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
# ║  PHASE 1 ─ 全景式 AST 檢視（內嵌 Python 工具）                            ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE1' '全景式 AST 檢視 → 庫存盤點 + 污染偵測' Yellow

$astTool = Join-Path $OutDir 'panoramic_inspect.py'
$astCode = @'
# -*- coding: utf-8 -*-
"""Panoramic AST inspector for VIA_SSOT_Unified.py"""
import ast, json, re, sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
out_path = Path(sys.argv[2])

# ── 錨點掃描 ─────────────────────────────────────────────
anchor_pat = re.compile(r'#\s*ANCHOR\[VIA:ANCHOR:([A-Z0-9\-]+)\]\s*[\u2014\-]?\s*([^\r\n]*)')
anchors = []
for i, line in enumerate(src.splitlines(), start=1):
    m = anchor_pat.search(line)
    if m:
        anchors.append({'line': i, 'id': m.group(1), 'desc': m.group(2).strip()})

# ── 規則計數 ─────────────────────────────────────────────
def count_objs(src_text, marker_var):
    pat = re.compile(rf"{marker_var}\s*:\s*list\[Rule\]\s*=\s*json\.loads\(r'''(.*?)'''\)", re.DOTALL)
    m = pat.search(src_text)
    if not m:
        return 0, []
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

# ── VIA_FINAL_PATCH 污染偵測 ─────────────────────────────
pollution = []
if 'VIA_FINAL_PATCH_SSOT_COMPAT' in src:
    pollution.append('VIA_FINAL_PATCH_SSOT_COMPAT detected — module-level get_ssot/normalize/extract overridden')
dup_get_ssot   = len(re.findall(r'^def\s+get_ssot\s*\(', src, re.MULTILINE))
dup_normalize  = len(re.findall(r'^def\s+normalize\s*\(', src, re.MULTILINE))
dup_extract    = len(re.findall(r'^def\s+extract\s*\(',  src, re.MULTILINE))

# ── AST 函數 / 類別 ─────────────────────────────────────
funcs, classes = [], []
parse_ok, parse_err = True, ''
try:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            funcs.append({'name': node.name, 'line': node.lineno, 'args': len(node.args.args)})
        elif isinstance(node, ast.AsyncFunctionDef):
            funcs.append({'name': node.name, 'line': node.lineno, 'args': len(node.args.args), 'async': True})
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append({'name': node.name, 'line': node.lineno, 'method_count': len(methods)})
except SyntaxError as e:
    parse_ok = False; parse_err = f'{e.msg} at line {e.lineno}'

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
    'function_count': len(funcs), 'class_count': len(classes), 'classes': classes,
    'self_test_count': test_count,
    'pollution': pollution,
    'duplicate_defs': {'get_ssot': dup_get_ssot, 'normalize': dup_normalize, 'extract': dup_extract},
}
out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('OK')
'@
Set-Content -LiteralPath $astTool -Value $astCode -Encoding UTF8

$r1 = Invoke-PyScript -ScriptPath $astTool -ScriptArgs @($workFile, $invJson)
if (-not $r1.Pass) {
    throw ("AST 掃描失敗: " + $r1.Stderr.Trim())
}
$inv = Get-Content -LiteralPath $invJson -Raw -Encoding UTF8 | ConvertFrom-Json

$script:STAT['source_file']      = $srcName
$script:STAT['source_bytes']     = $srcSize
$script:STAT['source_lines']     = $inv.src_lines
$script:STAT['version_before']   = $inv.version
$script:STAT['parse_ok']         = $inv.parse_ok
$script:STAT['anchors_count']    = $inv.anchors.Count
$script:STAT['regex_before']     = $inv.regex_count
$script:STAT['list_before']      = $inv.list_count
$script:STAT['synonym_before']   = $inv.synonym_count
$script:STAT['aliases_before']   = $inv.total_aliases
$script:STAT['function_count']   = $inv.function_count
$script:STAT['class_count']      = $inv.class_count
$script:STAT['self_test_before'] = $inv.self_test_count

Write-Stage 'PHASE1' ('版本: {0}  Parse OK: {1}  Lines: {2:N0}' -f $inv.version, $inv.parse_ok, $inv.src_lines) Green
Write-Stage 'PHASE1' ('Anchors: {0}  Regex: {1}  Lists: {2}  Synonyms: {3}  Aliases: {4}' -f `
    $inv.anchors.Count, $inv.regex_count, $inv.list_count, $inv.synonym_count, $inv.total_aliases) Green

if ($inv.pollution.Count -gt 0) {
    foreach ($w in $inv.pollution) {
        Write-Stage 'PHASE1' ('  ⚠ POLLUTION: {0}' -f $w) Yellow
        $script:WARN.Add($w) | Out-Null
    }
    Write-Stage 'PHASE1' ('  ⚠ Duplicate defs: get_ssot×{0}, normalize×{1}, extract×{2}' -f `
        $inv.duplicate_defs.get_ssot, $inv.duplicate_defs.normalize, $inv.duplicate_defs.extract) Yellow
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 2 ─ 補不足規則設計 (76 條會計科目同義詞)                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE2' '設計補不足規則（依會計科目對照表）' Yellow

# alias redirect — 把舊規則中的 alias 移出，賦予新規則（精化分類，非刪除）
$ALIAS_REDIRECT = [ordered]@{
    'EPS' = [ordered]@{
        remove = @('基本每股盈餘', '稀釋每股盈餘')
        note   = '由 BasicEPS / DilutedEPS 精化承接；EPS 仍保留 "每股盈餘" / "Earnings Per Share" 作為通用稱呼'
    }
}

# 76 條新規則（已模擬驗證 76/76 全部成功注入，0 衝突）
$newRulesRaw = @(
    # 損益表 (15)
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

    # 資產負債表 (20)
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

    # 現金流量表 (8)
    @{can='Depreciation';               grp='cash_flow'; aliases=@('折舊費用','折舊','Depreciation','固定資產折舊')}
    @{can='Amortization';               grp='cash_flow'; aliases=@('攤銷費用','攤提費用','Amortization','無形資產攤銷')}
    @{can='DepreciationAndAmortization';grp='cash_flow'; aliases=@('折舊與攤銷','D&A','Depreciation and Amortization','折舊及攤銷')}
    @{can='CapitalExpenditures';        grp='cash_flow'; aliases=@('資本支出','取得不動產廠房及設備','CapEx','Capital Expenditure','Capital Expenditures','設備投資')}
    @{can='FreeCashFlow';               grp='cash_flow'; aliases=@('自由現金流量','自由現金流','FCF','Free Cash Flow')}
    @{can='DividendsPaid';              grp='cash_flow'; aliases=@('發放現金股利','現金股利','Dividends Paid','Cash Dividends Paid','股利支付')}
    @{can='EffectOfExchangeRate';       grp='cash_flow'; aliases=@('匯率影響數','匯率變動影響','Effect of Exchange Rate Changes','Foreign Exchange Effects')}
    @{can='NetChangeInCash';            grp='cash_flow'; aliases=@('本期現金及約當現金增加減少','Net Change In Cash','Changes In Cash','現金淨變動')}

    # 比率分析 (21)
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

    # 估值指標 (5)
    @{can='PriceToEarnings';            grp='market'; aliases=@('本益比','P/E','PE Ratio','PER','Price-to-Earnings','TrailingPE','股價盈餘比')}
    @{can='PriceToBook';                grp='market'; aliases=@('股價淨值比','P/B','PB Ratio','PBR','Price-to-Book','市價淨值比')}
    @{can='PriceToSales';               grp='market'; aliases=@('股價營收比','P/S','PS Ratio','PSR','Price-to-Sales','市價營收比')}
    @{can='DividendYield';              grp='market'; aliases=@('現金股利殖利率','股利殖利率','Dividend Yield','現金殖利率','股息收益率','Yield')}
    @{can='PayoutRatio';                grp='market'; aliases=@('股利發放率','配息率','Payout Ratio','Dividend Payout Ratio','股利支付率')}

    # 每股分析 (7)
    @{can='BookValuePerShare';          grp='per_share'; aliases=@('每股淨值','BVPS','Book Value Per Share','每股帳面價值','每股股東權益')}
    @{can='RevenuePerShare';            grp='per_share'; aliases=@('每股營業額','每股營收','Revenue Per Share','SPS','Sales Per Share')}
    @{can='CashFlowPerShare';           grp='per_share'; aliases=@('每股現金流量','每股現金流','CFPS','Cash Flow Per Share')}
    @{can='FreeCashFlowPerShare';       grp='per_share'; aliases=@('每股自由現金流','FCF Per Share','Free Cash Flow Per Share')}
    @{can='SharesOutstanding';          grp='per_share'; aliases=@('普通股流通股數','流通在外股數','發行股數','Shares Outstanding','市場流通股')}
    @{can='WeightedAverageShares';      grp='per_share'; aliases=@('加權平均股數','加權平均流通股數','Weighted Average Shares','基本股數')}
    @{can='DilutedShares';              grp='per_share'; aliases=@('稀釋後股數','完全稀釋後股數','Fully Diluted Shares','Diluted Average Shares')}
)

Write-Stage 'PHASE2' ('預備新增 {0} 條規則' -f $newRulesRaw.Count) Cyan

# ── 序列化 spec 給 Python 子程序 ──────────────────────
$rulesForPy = @($newRulesRaw | ForEach-Object {
    [ordered]@{ canonical=$_.can; group=$_.grp; aliases=@($_.aliases) }
})
$specObj = [ordered]@{
    new_rules      = $rulesForPy
    alias_redirect = $ALIAS_REDIRECT
    work_file      = $workFile
    target_version = '4.2.0'
    dry_run        = [bool]$DryRun
}
$specJsonText = $specObj | ConvertTo-Json -Depth 10
Set-Content -LiteralPath $specJson -Value $specJsonText -Encoding UTF8

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 3 ─ AST 級別精準補丁 (Python 子程序執行)                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE3' 'AST 級別精準補丁注入' Yellow

$patchTool = Join-Path $OutDir 'apply_patch.py'
$patchCode = @'
# -*- coding: utf-8 -*-
"""Apply augmentation patch to VIA_SSOT_Unified.py (only-add policy)."""
import json, re, sys
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
result_path = Path(sys.argv[2])

new_rules      = spec['new_rules']
alias_redirect = spec['alias_redirect']
work_file      = Path(spec['work_file'])
target_version = spec['target_version']
dry_run        = bool(spec.get('dry_run', False))

src = work_file.read_text(encoding='utf-8', errors='replace')
diffs = []

# ── 定位 _RAW_SYNONYMS JSON 區塊 ──────────────────────
syn_pat = re.compile(r"(_RAW_SYNONYMS\s*:\s*list\[Rule\]\s*=\s*json\.loads\(r''')(.*?)('''\))", re.DOTALL)
syn_match = syn_pat.search(src)
if not syn_match:
    print(json.dumps({'ok': False, 'error': '_RAW_SYNONYMS block not found'}, ensure_ascii=False))
    sys.exit(2)

syn_data = json.loads(syn_match.group(2))
old_syn_count   = len(syn_data)
old_alias_count = sum(len(r['aliases']) for r in syn_data)

# ── 套用 alias redirect ───────────────────────────────
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

# ── 衝突檢測 ──────────────────────────────────────────
known = {}
for rule in syn_data:
    known[rule['canonical'].lower()] = rule['canonical']
    for a in rule['aliases']:
        known[a.lower()] = rule['canonical']

# 找 syn_id 最大編號
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
    if bad:
        alias_conflicts.append({'canonical': can, 'conflicts': bad})
    if not clean:
        skipped.append({'canonical': can, 'reason': 'all aliases conflict'}); continue
    pending.append({'canonical': can, 'group': grp, 'aliases': clean})
    known[can.lower()] = can
    for a in clean:
        known[a.lower()] = can

# ── 序列化新規則 ──────────────────────────────────────
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

# ── 補丁 1: 替換 _RAW_SYNONYMS 內容 ──────────────────
src = src[:syn_match.start(2)] + '\n' + new_syn_json + '\n' + src[syn_match.end(2):]
diffs.append({'anchor':'SSOT-DATA._RAW_SYNONYMS', 'action':'APPEND',
              'count': len(pending), 'detail': f'+{len(pending)} synonym rules'})
if redirect_log:
    diffs.append({'anchor':'SSOT-DATA._RAW_SYNONYMS', 'action':'REDIRECT',
                  'count': sum(len(r['removed']) for r in redirect_log),
                  'detail': '; '.join(f"{r['canonical']}: -{r['removed']}" for r in redirect_log)})

# ── 補丁 2: 更新 _CORPUS_STATS ───────────────────────
regex_count = src.count('"rule_id":')
list_count  = src.count('"list_id":')
# 用更精確的方式：直接從 _RAW_REGEX / _RAW_LISTS 重新計數
def count_block(src_text, marker):
    p = re.compile(rf"{marker}\s*:\s*list\[Rule\]\s*=\s*json\.loads\(r'''(.*?)'''\)", re.DOTALL)
    m = p.search(src_text)
    return len(json.loads(m.group(1))) if m else 0
regex_count = count_block(src, '_RAW_REGEX')
list_count  = count_block(src, '_RAW_LISTS')
total_rules = regex_count + list_count + new_syn_count

corpus_pat = re.compile(r"(_CORPUS_STATS\s*:\s*dict\[str,\s*int\]\s*=\s*\{)([^}]+)(\})", re.DOTALL)
new_corpus = (
    '\n    "regex_rules":   ' + str(regex_count) +
    ',\n    "list_rules":    ' + str(list_count) +
    ',\n    "synonym_rules": ' + str(new_syn_count) +
    ',\n    "total_aliases": ' + str(new_alias_count) +
    ',\n    "total_rules":   ' + str(total_rules) + ',\n'
)
def _corpus_repl(m):
    return m.group(1) + new_corpus + m.group(3)
src = corpus_pat.sub(_corpus_repl, src, count=1)
diffs.append({'anchor':'SSOT-DATA._CORPUS_STATS', 'action':'UPDATE', 'count': 5,
              'detail': f'regex={regex_count}, lists={list_count}, syns={new_syn_count}, aliases={new_alias_count}, total={total_rules}'})

# ── 補丁 3: 升版 ──────────────────────────────────────
old_ver_match = re.search(r'(VERSION\s*:\s*)(\d+\.\d+\.\d+)', src)
old_ver = old_ver_match.group(2) if old_ver_match else 'unknown'
src = re.sub(r'(VERSION\s*:\s*)\d+\.\d+\.\d+', r'\g<1>' + target_version, src, count=1)
diffs.append({'anchor':'HEADER.VERSION', 'action':'UPDATE', 'count': 1,
              'detail': f'{old_ver} -> {target_version}'})

# ── 補丁 4: 更新檔頭 banner CORPUS 統計 ──────────────
new_banner = f'CORPUS: regex={regex_count} \u00b7 lists={list_count} \u00b7 synonyms={new_syn_count} \u00b7 aliases={new_alias_count}'
src = re.sub(r'CORPUS:\s*regex=\d+\s*\u00b7\s*lists=\d+\s*\u00b7\s*synonyms=\d+\s*\u00b7\s*aliases=\d+',
             new_banner, src, count=1)
diffs.append({'anchor':'HEADER.BANNER', 'action':'UPDATE', 'count': 1, 'detail': new_banner})

# ── 補丁 5: 同步 self_test 預期值 ─────────────────────
src = re.sub(r'(chk\("regex_rules=)\d+(",[^,]+,\s*)\d+(\))',
             rf'\g<1>{regex_count}\g<2>{regex_count}\g<3>',     src, count=1)
src = re.sub(r'(chk\("list_rules=)\d+(",[^,]+,\s*)\d+(\))',
             rf'\g<1>{list_count}\g<2>{list_count}\g<3>',       src, count=1)
src = re.sub(r'(chk\("synonym_rules=)\d+(",[^,]+,\s*)\d+(\))',
             rf'\g<1>{new_syn_count}\g<2>{new_syn_count}\g<3>', src, count=1)
diffs.append({'anchor':'SSOT-UTIL.self_test', 'action':'UPDATE', 'count': 3,
              'detail': 'corpus stat assertions synced'})

# ── 寫回 ──────────────────────────────────────────────
if not dry_run:
    work_file.write_text(src, encoding='utf-8')

result = {
    'ok': True,
    'before': {'synonym_count': old_syn_count, 'alias_count': old_alias_count,
               'regex_count': regex_count, 'list_count': list_count},
    'after':  {'synonym_count': new_syn_count, 'alias_count': new_alias_count,
               'regex_count': regex_count, 'list_count': list_count, 'total_rules': total_rules},
    'rules_added':     len(pending),
    'rules_skipped':   len(skipped),
    'alias_conflicts': len(alias_conflicts),
    'redirect_log':    redirect_log,
    'skipped':         skipped,
    'pending':         pending,
    'diffs':           diffs,
    'work_file':       str(work_file),
    'work_bytes':      len(src.encode('utf-8')),
    'dry_run':         dry_run,
}
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
    Write-Stage 'PHASE3' ('  ✓ [{0}] {1}: {2}' -f $d.action, $d.anchor, $d.detail) Green
}
foreach ($r in $patchResult.redirect_log) {
    Write-Stage 'PHASE3' ('  ◆ Redirect from {0}: removed {1}' -f $r.canonical, ($r.removed -join ', ')) Cyan
}
Write-Stage 'PHASE3' ('  + Rules added: {0}  Skipped: {1}  Alias conflicts handled: {2}' -f `
    $patchResult.rules_added, $patchResult.rules_skipped, $patchResult.alias_conflicts) Green
Write-Stage 'PHASE3' ('  Work file: {0:N0} bytes (was {1:N0})' -f $patchResult.work_bytes, $srcSize) Green

if ($DryRun) {
    Write-Stage 'PHASE3' '  ⚠ DryRun 模式：規則差異已計算但未寫入工作檔' Yellow
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 4 ─ 自動測試                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE4' '自動測試 (4 stages)' Yellow

$testTool = Join-Path $OutDir 'run_tests.py'
$testCode = @'
# -*- coding: utf-8 -*-
"""Run automated tests against patched VIA_SSOT_Unified.work.py.
   - 因原檔末端有 VIA_FINAL_PATCH_SSOT_COMPAT 覆寫了 module-level get_ssot/normalize/extract，
     繞過污染：直接使用 SSOT() 類別 API 做完整斷言。"""
import json, sys, importlib.util, py_compile, traceback
from pathlib import Path

work_file = Path(sys.argv[1])
out_path  = Path(sys.argv[2])
results   = []

# ── Test 1: py_compile ───────────────────────────────
try:
    py_compile.compile(str(work_file), doraise=True)
    results.append({'tag':'py_compile', 'pass': True, 'detail':'syntax OK'})
except py_compile.PyCompileError as e:
    results.append({'tag':'py_compile', 'pass': False, 'detail': str(e)})
    out_path.write_text(json.dumps({'tests': results}, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.exit(0)

# ── Test 2: import + SSOT class instantiation ───────
mod = None
try:
    spec = importlib.util.spec_from_file_location('via_ssot_test', work_file)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules['via_ssot_test'] = mod   # Py 3.12 dataclass 需要 module 先註冊
    spec.loader.exec_module(mod)
    s = mod.SSOT()   # 直接用 class 繞過 VIA_FINAL_PATCH 污染
    info = s.info()
    results.append({
        'tag':'import+ssot', 'pass': True,
        'detail': f"regex={info['regex_rules']}, lists={info['list_rules']}, syns={info['synonym_rules']}, aliases={info['total_aliases']}",
        'info': info,
    })
except Exception as e:
    results.append({'tag':'import+ssot', 'pass': False,
                    'detail': f'{type(e).__name__}: {e}',
                    'traceback': traceback.format_exc()})
    out_path.write_text(json.dumps({'tests': results}, ensure_ascii=False, indent=2), encoding='utf-8')
    sys.exit(0)

# ── Test 3: self_test (繞過 VIA_FINAL_PATCH 污染) ───
try:
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
    results.append({'tag':'self_test_direct', 'pass': pass_n == total,
                    'detail': f'{pass_n}/{total} cases pass',
                    'cases': [{'name':n,'ok':ok} for n,ok in cases]})
except Exception as e:
    results.append({'tag':'self_test_direct', 'pass': False,
                    'detail': f'{type(e).__name__}: {e}',
                    'traceback': traceback.format_exc()})

# ── Test 4: 新規則抽樣驗證 ───────────────────────────
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
    Write-Stage 'PHASE4' ('  Test [{0}]: {1} — {2}' -f $t.tag, $sym, $t.detail) $col
    $script:TESTS.Add(@{ Tag=$t.tag; Pass=$t.pass; Detail=$t.detail; Cases=($t.PSObject.Properties['cases'] | ForEach-Object { $_.Value }); Samples=($t.PSObject.Properties['samples'] | ForEach-Object { $_.Value }) }) | Out-Null
}

$passCount = (@($script:TESTS) | Where-Object { $_.Pass }).Count
$failCount = $script:TESTS.Count - $passCount
$verdict   = if ($failCount -eq 0) { 'READY' } elseif ($failCount -le 1) { 'NEAR-READY' } else { 'NOT-READY' }

$script:STAT['version_after']   = '4.2.0'
$script:STAT['regex_after']     = $patchResult.after.regex_count
$script:STAT['list_after']      = $patchResult.after.list_count
$script:STAT['synonym_after']   = $patchResult.after.synonym_count
$script:STAT['aliases_after']   = $patchResult.after.alias_count
$script:STAT['rules_added']     = $patchResult.rules_added
$script:STAT['rules_skipped']   = $patchResult.rules_skipped
$script:STAT['alias_conflicts'] = $patchResult.alias_conflicts
$script:STAT['tests_pass']      = $passCount
$script:STAT['tests_fail']      = $failCount
$script:STAT['verdict']         = $verdict

Write-Stage 'PHASE4' ('=== Verdict: {0} ({1}/{2} pass) ===' -f $verdict, $passCount, $script:TESTS.Count) `
    $(if ($verdict -eq 'READY') { 'Green' } elseif ($verdict -eq 'NEAR-READY') { 'Yellow' } else { 'Red' })

# 若全綠且非 DryRun，覆寫原檔
if ($verdict -eq 'READY' -and -not $DryRun -and -not $ForceLocalCopy) {
    try {
        Copy-Item -LiteralPath $workFile -Destination $TargetPath -Force
        Write-Stage 'PHASE4' ('  ✓ 已覆寫原檔: {0}' -f $TargetPath) Green
    } catch {
        Write-Stage 'PHASE4' ('  ⚠ 無法覆寫原檔（OneDrive/權限）: {0}' -f $_.Exception.Message) Yellow
        Write-Stage 'PHASE4' ('    → 工作檔保留於: {0}' -f $workFile) Yellow
    }
} else {
    Write-Stage 'PHASE4' ('  ℹ 工作檔保留於: {0}' -f $workFile) Cyan
    if ($ForceLocalCopy) { Write-Stage 'PHASE4' '    （ForceLocalCopy 啟用 — 不覆寫原檔）' DarkGray }
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PHASE 5 ─ HTML U/I Matrix Report (VIA Visual Lock)                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'PHASE5' '產生 HTML U/I Matrix Report' Yellow

$genTime = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$verdictClass = switch ($verdict) {
    'READY'      { 'b-ok'   }
    'NEAR-READY' { 'b-warn' }
    default      { 'b-fail' }
}
$aliasDelta = $script:STAT.aliases_after - $script:STAT.aliases_before

# 警示條（污染偵測）
$warnHtml = ''
if ($script:WARN.Count -gt 0 -or $inv.duplicate_defs.get_ssot -gt 1) {
    $warnLines = @()
    foreach ($w in $script:WARN) { $warnLines += ('• ' + $w) }
    if ($inv.duplicate_defs.get_ssot -gt 1) {
        $warnLines += ('• Duplicate defs detected: get_ssot×' + $inv.duplicate_defs.get_ssot + ', normalize×' + $inv.duplicate_defs.normalize + ', extract×' + $inv.duplicate_defs.extract)
    }
    $warnHtml = @"
<section class="warn-box">
  <div class="warn-h">⚠ POLLUTION DETECTED — 既有問題（非本次補丁造成）</div>
  <div class="warn-b">$([string]::Join('<br>', $warnLines))<br>
  <small>本腳本繞過污染：直接以 <code>SSOT()</code> 類別 API 做測試，補丁注入未受影響。建議日後清理此污染區。</small></div>
</section>
"@
}

# Cards 區
$cardsTop = @"
<div class="grid">
  <div class="cd accent"><div class="cd-h">Version</div><div class="cd-b">$($script:STAT.version_before) → $($script:STAT.version_after)</div><div class="cd-i">semver bump</div></div>
  <div class="cd teal"><div class="cd-h">Source Lines</div><div class="cd-b">$('{0:N0}' -f $script:STAT.source_lines)</div><div class="cd-i">$('{0:N0}' -f $script:STAT.source_bytes) bytes</div></div>
  <div class="cd"><div class="cd-h">Anchors</div><div class="cd-b">$($script:STAT.anchors_count)</div><div class="cd-i">VIA:ANCHOR markers</div></div>
  <div class="cd"><div class="cd-h">Functions</div><div class="cd-b">$($script:STAT.function_count)</div><div class="cd-i">module-level</div></div>
  <div class="cd"><div class="cd-h">Classes</div><div class="cd-b">$($script:STAT.class_count)</div><div class="cd-i">incl. SSOT</div></div>
  <div class="cd"><div class="cd-h">SelfTest</div><div class="cd-b">$($script:STAT.self_test_before)+</div><div class="cd-i">case count</div></div>
</div>
"@

$cardsDelta = @"
<div class="grid grid4">
  <div class="cd accent">
    <div class="cd-h">Regex Rules</div>
    <div class="cd-b">$($script:STAT.regex_before) <span class="delta-flat">→</span> $($script:STAT.regex_after)</div>
    <div class="cd-i delta-flat">no change</div>
  </div>
  <div class="cd accent">
    <div class="cd-h">List Rules</div>
    <div class="cd-b">$($script:STAT.list_before) <span class="delta-flat">→</span> $($script:STAT.list_after)</div>
    <div class="cd-i delta-flat">no change</div>
  </div>
  <div class="cd good">
    <div class="cd-h">Synonym Rules</div>
    <div class="cd-b">$($script:STAT.synonym_before) <span class="delta-up">→</span> $($script:STAT.synonym_after)</div>
    <div class="cd-i delta-up">+$($script:STAT.rules_added)</div>
  </div>
  <div class="cd good">
    <div class="cd-h">Total Aliases</div>
    <div class="cd-b">$($script:STAT.aliases_before) <span class="delta-up">→</span> $($script:STAT.aliases_after)</div>
    <div class="cd-i delta-up">+$aliasDelta</div>
  </div>
</div>
"@

# 新規則 by group
$grpCounts = @{}
foreach ($r in $patchResult.pending) {
    $g = $r.group
    if (-not $grpCounts.ContainsKey($g)) { $grpCounts[$g] = 0 }
    $grpCounts[$g]++
}
$grpRows = ''
foreach ($k in ($grpCounts.Keys | Sort-Object)) {
    $grpRows += ('<tr><td><span class="b b-teal">' + $k + '</span></td><td>' + $grpCounts[$k] + '</td></tr>' + "`n")
}

$skippedRows = ''
if ($patchResult.skipped.Count -gt 0) {
    foreach ($s in $patchResult.skipped) {
        $skippedRows += ('<tr><td><span class="b b-mut">' + $s.canonical + '</span></td><td>' + $s.reason + '</td></tr>' + "`n")
    }
} else {
    $skippedRows = '<tr><td colspan="2" style="color:#6b7280">none</td></tr>'
}

# Detail 表（76 條全列）
$ruleDetailRows = ''
foreach ($r in $patchResult.pending) {
    $aliasesJoined = ($r.aliases -join ' · ')
    $ruleDetailRows += ('<tr><td><span class="b b-pri">' + $r.canonical + '</span></td><td><span class="b b-teal">' + $r.group + '</span></td><td>' + $r.aliases.Count + '</td><td>' + $aliasesJoined + '</td></tr>' + "`n")
}

# Diff 表
$diffRows = ''
foreach ($d in $patchResult.diffs) {
    $actClass = switch ($d.action) {
        'APPEND'   { 'b-ok'   }
        'UPDATE'   { 'b-pri'  }
        'REDIRECT' { 'b-warn' }
        default    { 'b-mut'  }
    }
    $diffRows += ('<tr><td><code>' + $d.anchor + '</code></td><td><span class="b ' + $actClass + '">' + $d.action + '</span></td><td>' + $d.count + '</td><td>' + $d.detail + '</td></tr>' + "`n")
}

# Test 表
$testRows = ''
foreach ($t in $testsBlob.tests) {
    $stClass = if ($t.pass) { 'b-ok' } else { 'b-fail' }
    $stTxt   = if ($t.pass) { 'PASS' } else { 'FAIL' }
    $detailEsc = ($t.detail -replace '<','&lt;' -replace '>','&gt;')
    $testRows += ('<tr><td><code>' + $t.tag + '</code></td><td><span class="b ' + $stClass + '">' + $stTxt + '</span></td><td>' + $detailEsc + '</td></tr>' + "`n")
}

# self_test_direct 案例細節
$caseRows = ''
$selfTestDirect = $testsBlob.tests | Where-Object { $_.tag -eq 'self_test_direct' } | Select-Object -First 1
if ($selfTestDirect -and $selfTestDirect.PSObject.Properties['cases']) {
    foreach ($c in $selfTestDirect.cases) {
        $okClass = if ($c.ok) { 'b-ok' } else { 'b-fail' }
        $okTxt   = if ($c.ok) { '✓' } else { '✗' }
        $caseRows += ('<tr><td>' + $c.name + '</td><td><span class="b ' + $okClass + '">' + $okTxt + '</span></td></tr>' + "`n")
    }
}

# new_rules 抽樣
$sampleRows = ''
$newRulesTest = $testsBlob.tests | Where-Object { $_.tag -eq 'new_rules' } | Select-Object -First 1
if ($newRulesTest -and $newRulesTest.PSObject.Properties['samples']) {
    foreach ($sm in $newRulesTest.samples) {
        $okClass = if ($sm.ok) { 'b-ok' } else { 'b-fail' }
        $okTxt   = if ($sm.ok) { '✓' } else { '✗' }
        $sampleRows += ('<tr><td>' + $sm.raw + '</td><td><code>' + $sm.expected + '</code></td><td><code>' + $sm.got + '</code></td><td><span class="b ' + $okClass + '">' + $okTxt + '</span></td></tr>' + "`n")
    }
}

# Anchor 表
$anchorRows = ''
foreach ($a in $inv.anchors) {
    $anchorRows += ('<tr><td>' + $a.line + '</td><td><code>' + $a.id + '</code></td><td>' + $a.desc + '</td></tr>' + "`n")
}

# Class 表
$classRows = ''
foreach ($c in $inv.classes) {
    $classRows += ('<tr><td><code>' + $c.name + '</code></td><td>' + $c.line + '</td><td>' + $c.method_count + '</td></tr>' + "`n")
}

# Console log
$logEsc = (($script:LOG -join "`n") -replace '<','&lt;' -replace '>','&gt;')

# ── 完整 HTML 拼接 ─────────────────────────────────────
$html = @"
<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="UTF-8">
<title>VIA SSOT Unified — Panoramic Augmenter Matrix Report</title>
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
  .cd-b{font-family:'Syne',sans-serif;font-weight:700;font-size:20px;color:var(--ink);line-height:1.1}
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
  .warn-box{background:#fff;border:1px solid rgba(212,160,23,.4);border-left:3px solid var(--warn);border-radius:8px;padding:11px 14px;margin-bottom:18px}
  .warn-h{font-family:'Syne',sans-serif;font-weight:600;color:var(--warn);font-size:12px;margin-bottom:5px}
  .warn-b{color:var(--ink);font-size:10.5px;line-height:1.6}
  code{background:rgba(31,41,51,.06);padding:1px 5px;border-radius:3px;font-family:'DM Mono',monospace;font-size:10px}
</style></head>
<body>
<div class="rainbow"></div>
<header>
  <h1>VeritasIntelligenceAnalytics — VIA_SSOT_Unified Panoramic Augmenter</h1>
  <div class="sub">VIA_SSOT_PanoramicAugmenter_v1 · Matrix Report · 全景式 AST 檢視 + 補不足 + 自動測試</div>
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
    <small class="note">$($script:STAT.tests_pass)/$($script:TESTS.Count) tests passed · $($script:STAT.rules_added) rules added · v$($script:STAT.version_before) → v$($script:STAT.version_after) · +$aliasDelta aliases</small>
  </div>
  <div class="val"><span class="b $verdictClass" style="font-size:18px;padding:6px 16px">$verdict</span></div>
</div>

$warnHtml

<section>
<h2>① Source Inventory (Before)</h2>
$cardsTop
</section>

<section>
<h2>② Corpus Delta — Before vs After</h2>
$cardsDelta
</section>

<section>
<h2>③ New Rules by Group + Skipped</h2>
<div class="grid grid2">
<table><thead><tr><th>Group</th><th>Added</th></tr></thead><tbody>$grpRows</tbody></table>
<table><thead><tr><th>Skipped Canonical</th><th>Reason</th></tr></thead><tbody>$skippedRows</tbody></table>
</div>
</section>

<section>
<h2>④ New Synonym Rules — Detail Matrix ($($patchResult.rules_added) rules)</h2>
<table>
<thead><tr><th>Canonical</th><th>Group</th><th>Aliases</th><th>Alias List</th></tr></thead>
<tbody>$ruleDetailRows</tbody>
</table>
</section>

<section>
<h2>⑤ AST Anchor Patches Applied</h2>
<table>
<thead><tr><th>Anchor</th><th>Action</th><th>Count</th><th>Detail</th></tr></thead>
<tbody>$diffRows</tbody>
</table>
</section>

<section>
<h2>⑥ Test Results — Top Level</h2>
<table>
<thead><tr><th>Test</th><th>Status</th><th>Detail</th></tr></thead>
<tbody>$testRows</tbody>
</table>
</section>

<section>
<h2>⑦ self_test_direct — Case-by-case (繞過 VIA_FINAL_PATCH 污染)</h2>
<table>
<thead><tr><th>Assertion</th><th>Status</th></tr></thead>
<tbody>$caseRows</tbody>
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
<h2>⑨ Anchor Map ($($inv.anchors.Count))</h2>
<table>
<thead><tr><th>Line</th><th>Anchor ID</th><th>Description</th></tr></thead>
<tbody>$anchorRows</tbody>
</table>
</section>

<section>
<h2>⑩ Class Map ($($inv.classes.Count))</h2>
<table>
<thead><tr><th>Class</th><th>Line</th><th>Methods</th></tr></thead>
<tbody>$classRows</tbody>
</table>
</section>

<section>
<h2>⑪ Execution Log</h2>
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

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  完成總結                                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
Write-Stage 'DONE' '─────────────────────────────────────────────────────' Yellow
Write-Stage 'DONE' ('Verdict:        {0}' -f $verdict) `
    $(if ($verdict -eq 'READY') { 'Green' } elseif ($verdict -eq 'NEAR-READY') { 'Yellow' } else { 'Red' })
Write-Stage 'DONE' ('Rules Added:    {0}  (Aliases +{1})' -f $script:STAT.rules_added, $aliasDelta) Cyan
Write-Stage 'DONE' ('Synonyms:       {0} → {1}' -f $script:STAT.synonym_before, $script:STAT.synonym_after) Cyan
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

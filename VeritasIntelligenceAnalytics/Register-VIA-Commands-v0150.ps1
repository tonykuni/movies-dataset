# =====================================================================
# Register-VIA-Commands-v0150.ps1 — VIA 短指令唯一定義處(批383 操作員令「將 river-beam-aurora-acorn 裡面的檔案接回做為整合為一入口」+「單一入口與這個(SYSTEM MANAGER MATRIX v0700)整合;vap 補充;vdf vrn 要弄到實際能跑;vdf 要將資料庫存入;之前有的資料庫整理好抓過的不必再抓」→ +via-entry(唯一入口燈板/plan/roster;--scan/--open/--console)+via-env(→via-envgov 正本)+via-grok(Grok 短令冊;matrix 右側板)+via-webconsole(Grok 網頁主控台 8080;同意閘)+via-vapone(VAP ONE 72 檢)+via-vdfdb(本機三庫整併 DuckDB;抓過不再抓)+via-envpy/Get-VIAEnvPython(家族境 python 解析;功能件住 via_ 境=啟動器指對 python)+載入即接 Grok CmdMatrix(去尾段自動執行;撞名母倉先發先得)+via-open 別名 矩陣/入口;批381 操作員令「依照已成功地建構布局向上新增;最壞還原成原本規劃;base 只放該有的工具;其他放在 via_core 及 via_ 開頭的環境」→ +via-envgov(CGC_MDL135 環境治理統一引擎:全景式分析 base/via_core/via_* → uv 毫秒快篩 → base 該有冊閉包 → 衝突立拔家族路由 → Zero-Hydra 分流拓撲三輪 → LKGC/rollback → 四分區 UI Matrix;預設 run --offline 唯讀;apply --approve 才動;base 移除另 --approve-remove)+via-envgov-auto(Invoke-VIA-EnvGovernance 單一 PowerShell 一貼即用;-Background 非阻塞);批380 操作員令「用一個 PowerShell 完成所有動作 不影響系統健康 不可造成九頭龍風險 20 的加速器 不卡斷」→ via-autorun 四閘版:①20 加速器點亮 ②Hydra 哨兵 H1–H6 先行(H3/H5 阻擋=誠實停) ③全程零跳出零 TTY 等待 ④逾時 kill 不卡斷;批379 操作員在電腦前「自動完成所有動作 不要打開 VS Code 我不知道要怎麼辦」→ +via-autorun 一鍵全自動(雙擊 via-autorun.cmd 即可;結束停窗)+git 永不開編輯器 env;批378 操作員令「不要一直開啟 VS Code,全自動完成一切」→ 載入即全域 VIA_NO_OPEN=1(所有短令零跳出;看頁只走 via-open 瀏覽器道;VIA_OPEN_PAGES=1 可解);批377 +via-lanes 十道並行安全編排(MDL134;Hydra 哨兵)+via-mobile --lanes;批376 +via-productgate 產品資格閘九閘(MDL133);via-mobile 末段 +productgate digest;批375 +via-etfhist 每日持股史深;批374 +via-etfuniv 主動 ETF 宇宙日更;批373 +via-etfrev 主動 ETF×月營收合流;批371 via-ves→MDL132 橋(尾版鏡像+安全種子+雙跑;--raw 直通原件);批370 +via-ves 唯讀 E3 標準化掃描;批368 +via-projects 四專案完工矩陣;+via-revfill 月營收史深;批367 via-reload 同名雙物大寫原件復位;批366 via-mobile 零跳出 VIA_NO_OPEN=1;批362 via-fred 無動詞=run;批360/361 +via-fred/via-vdfarch;批254 立;批260 +via-all;批316 +via-pipeline;批323 +via-accel/via-accel-check;批325 +via-rotation/via-repo-optimize;批327 +via-vapstack;批328 +via-reload;批330 +via-plotlaw;批331 via-reload 先拉齊;批332 +via-system/via-api;批333 +via-master;批335 +via-complete;批336 +via-intake-roster;批337 via-reload 拉齊誠實+產出頁自動讓位;批338 可編輯模板排除;批339 短令清單動態;批340 +via-datahome/via-complete 分離啟動器;批342 +via-six 六流程 Zero-Hydra 編排;批344 via-complete watch/stop;批345 +via-bridge-sweep)
# =====================================================================
# 批254 摩擦修:舊制=Register-Profile 把函式全文塞 $PROFILE(要跑 via
# +開新視窗+每加一指令就 v010x 重貼)。新制=點源架構:
#   ①本檔=十指令唯一定義處(global 域;git pull 即最新)
#   ②$PROFILE 只留一行點源(VIA.ps1 自動補;舊 v010x 段無害,點源
#     在後=後定義勝)
#   ③當場生效:. "<本檔路徑>"(不用新視窗不用 via)
# =====================================================================
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
$VIA = Split-Path -Parent $MyInvocation.MyCommand.Path
$global:VIARegisterPath = $MyInvocation.MyCommand.Path   # 批383:撞名守衛掃描本冊用

# 批378:全域零跳出律——.html 預設程式=VS Code,任何 --open 皆會彈 VS Code(批366 只管 via-mobile 不夠)。載入短令冊即設 VIA_NO_OPEN=1:
# py 側 SUP_MDL737 閘(webbrowser/os.startfile 頁面目標 no-op)+PS 側 PS-ACCEL 閘(Start-Process/Invoke-Item)全樹生效;頁面只落檔。
# 想看頁:via-open <頁名片段>(只走瀏覽器 exe,永不經 .html 預設程式);想恢復舊行為:$env:VIA_OPEN_PAGES="1" 後 via-reload。
if ($env:VIA_OPEN_PAGES -ne "1") { $env:VIA_NO_OPEN = "1" }
# 批379:git 永不開編輯器(core.editor=code --wait 會彈 VS Code 等你關窗=卡住);GIT_EDITOR=true 接受預設訊息;不問密碼提示
$env:GIT_EDITOR = "true"; $env:GIT_MERGE_AUTOEDIT = "no"; $env:GIT_SEQUENCE_EDITOR = "true"; $env:GIT_TERMINAL_PROMPT = "0"
function global:Get-VIANewest([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}
# 批383:家族境 python 解析(操作員令「vdf vrn 要弄到實際能跑」:功能件住 via_ 境(Baseline 冊 docs→via_vrn_312/data_fetch→via_vdf_312/plot_ui→via_vap_312),啟動器須指對境 python;base 只放共用工具)
# 序:$env:VIA_PY_<FAMILY> 覆寫 > 境根(VIA_ENV_ROOT/VIA_ENV_ROOTS/~\envs/C:\Users\tonyk\envs/conda envs/$VIA\Environments/$VIA\.venv-via_<f>)×候選名(Baseline 別名 via_<f>_312/via_<f>/…)> "python"(base 退路;via-envpy 誠實印黃);規則正本+自測=CGC_MDL136 EntryBridge envpy
function global:Get-VIAEnvPython([string]$Family) {
    $f = ("" + $Family).ToLower(); if (-not $f) { return "python" }
    $ov = [Environment]::GetEnvironmentVariable("VIA_PY_" + $f.ToUpper()); if ($ov -and (Test-Path -LiteralPath $ov)) { return $ov }
    $alias = @{ "vdf" = @("via_vdf_312", "via_vdf", "via_vdf_313"); "vrn" = @("via_vrn_312", "via_vrn", "via_extract_312", "via_vrn4"); "vap" = @("via_vap_312", "via_vap", "via_vap_313"); "core" = @("via_core_312", "via_core", "venv_core"); "ocr" = @("via_paddle_311", "via_paddle_312", "via_ocr", "paddle_312", "paddle_311"); "table" = @("via_camelot_311", "camelot_311"); "html" = @("via_html_312"); "nlp" = @("via_nlp"); "ml" = @("via_ml"); "tools" = @("via_tools_312") }
    $names = @(); if ($alias.ContainsKey($f)) { $names += $alias[$f] }; $names += @(("via_" + $f + "_312"), ("via_" + $f), ("via_" + $f + "_313"), ("via_" + $f + "_311"), (".venv-via_" + $f))
    $roots = @($env:VIA_ENV_ROOT) + @(("" + $env:VIA_ENV_ROOTS).Split(";")) + @("$env:USERPROFILE\envs", "C:\Users\tonyk\envs", "$env:USERPROFILE\miniconda3\envs", "$env:USERPROFILE\Miniconda3\envs", "$env:USERPROFILE\anaconda3\envs", "$env:USERPROFILE\.virtualenvs", "$VIA\Environments", $VIA) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
    foreach ($r in $roots) { foreach ($n in $names) { foreach ($sub in @("Scripts\python.exe", "python.exe", "bin\python3", "bin\python")) { $p = Join-Path (Join-Path $r $n) $sub; if (Test-Path -LiteralPath $p) { return $p } } } }
    return "python"
}
function global:via-envpy { $f = if ($args.Count -gt 0) { "" + $args[0] } else { "vdf" }; $p = Get-VIAEnvPython $f; if ($p -eq "python") { Write-Host ("  [envpy] " + $f + " 境未見 → base 退路 python(建境:via-envgov apply --approve(ENSURE_ENV);或設 `$env:VIA_PY_" + $f.ToUpper() + ")") -ForegroundColor Yellow } else { Write-Host ("  [envpy] " + $f + " → " + $p) -ForegroundColor Green }; $p }
# 批383:Grok 主控台短令矩陣接回(收容包 b383 scripts/VIA-CmdMatrix.ps1;原件零觸碰;操作員令「將裡面的檔案接回做為整合為一入口」)
# ①去尾段自動執行(欄 0:via-enter 進母根/via-matrix WPF 板/LOAD 燈=違批378 零跳出律)②撞名守衛:母倉先發先得(via-entry/via-env 母倉正本;Grok 同名改 -grok 尾綴;內部呼叫鏈同步改指)
# ③Grok 非 global 助手(Lamp/Get-VIAZh/…)升 global(函式域點源後仍可用);規則正本+驗證=CGC_MDL136 EntryBridge(cmdmatrix-clean);$env:VIA_GROK_MATRIX="0" 可不載
function global:Import-VIAGrokMatrix {
    $cm = "$VIA\supportive modules\references\intake\VIA_GrokConsole_AuroraAcorn_b383\scripts\VIA-CmdMatrix.ps1"
    if (-not (Test-Path -LiteralPath $cm)) { return @() }
    try {
        $t = Get-Content -LiteralPath $cm -Raw -Encoding UTF8
        $t = [regex]::Replace($t, "(?m)^via-enter \| Out-Null[ \t]*$", "")
        $t = [regex]::Replace($t, "(?m)^try \{ via-matrix \}.*$", "")
        $t = [regex]::Replace($t, "(?m)^Lamp 'GREEN' 'LOAD'.*$", "")
        $mine = @("via-entry", "via-env") + @([regex]::Matches((Get-Content -LiteralPath $global:VIARegisterPath -Raw -Encoding UTF8), "function global:(via[\w-]*)") | ForEach-Object { $_.Groups[1].Value })
        $ren = @()
        foreach ($m in @([regex]::Matches($t, "function global:(via[\w-]*)") | ForEach-Object { $_.Groups[1].Value })) {
            if ($mine -contains $m) {
                $t = $t.Replace(("function global:" + $m + " {"), ("function global:" + $m + "-grok {"))
                $t = [regex]::Replace($t, ("(?m)^(\s*)" + [regex]::Escape($m) + "\s*$"), ('$1' + $m + "-grok"))
                $ren += ($m + "→" + $m + "-grok")
            }
        }
        $t = [regex]::Replace($t, "(?m)^function (?!global:)([\w-]+)", 'function global:$1')
        . ([scriptblock]::Create($t))
        $verbs = @([regex]::Matches($t, "function global:(via[\w-]*)") | ForEach-Object { $_.Groups[1].Value })
        Write-Host ("  [Grok 矩陣] " + $verbs.Count + " 令已載(" + ($ren -join " ") + ";尾段自動執行已去;via-grok 看冊;via-matrix 開右側板)") -ForegroundColor DarkCyan
        return $verbs
    } catch { Write-Host ("  [Grok 矩陣] 載入失敗(不影響母倉短令):" + $_.Exception.Message) -ForegroundColor Yellow; return @() }
}
$VIAGrokVerbs = @(); if ($env:VIA_GROK_MATRIX -ne "0") { $VIAGrokVerbs = @(Import-VIAGrokMatrix) }

function global:regen-all { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL096_SyncStatus_v*.py") --regen-all }
function global:via { powershell -NoProfile -ExecutionPolicy Bypass -File "$VIA\VIA.ps1" }
function global:via-status { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL096_SyncStatus_v*.py") --open }
function global:via-selftest { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL064_SelftestGrid_v*.py") @args }
function global:selftest { via-selftest @args }
function global:via-intake { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Collect-VIA-Intake-v*.ps1") @args }
function global:via-help { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL102_CommandRoster_v*.py") --print }
function global:via-md { python (Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG075_DocToMarkdown_v*.py") run @args }
function global:via-prompt { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL109_PromptManager_v*.py") @args }
function global:via-analysis { python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG068_ETFConsensusAnalysis_v*.py") run; python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG069_RevenueConsensusAnalysis_v*.py") run }
function global:via-manager { python (Get-VIANewest "$VIA" "VIA_SYSTEM_MANAGER_v*.py") @args }
function global:via-rootcheck { & cmd /c "$VIA\VIA-ROOTCHECK.cmd" }
function global:via-tower-reset { & cmd /c "$VIA\VIA-TOWER-RESET.cmd" }
function global:via-ssot { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL115_SSOTRegexDict_v*.py") @args }
function global:via-register { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL113_UnifiedRegistry_v*.py") @args }
function global:via-health { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL114_CommandCenterBridge_v*.py") run }
function global:via-tpn { python (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG011_TemplateRegistry_v*.py") @args }
function global:via-psrepair { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-PSRepair-v*.ps1") @args }
function global:via-all { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-All-v*.ps1") @args }
# 批323:加速器啟動報告(SUP_MDL737 尾版 --activate/--libs)+覆蓋×啟動稽核(CGC_MDL117)
function global:via-accel { python (Get-VIANewest "$VIA\supportive modules" "SUP_MDL737_SuperAccelModule_v*.py") $(if ($args) { $args } else { "--activate" }) }
function global:via-accel-check { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL117_AccelCoverage_v*.py") run }
# 批325:故事族群輪動橋接(ENG072 尾版;run 預設,可帶 export/preflight/--pkgtest)+repo 衛生一鍵(只宜工作站)
function global:via-rotation { python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG072_StoryRotationBridge_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-repo-optimize { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-RepoOptimizer-v*.ps1") @args }
# 批327:VAP Seaborn 垂直圖組橋接(ENG015 尾版;預設 stock 2330;可帶 stock <代碼> | heatmap | --selftest)
function global:via-vapstack { python (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG015_SeabornStackBridge_v*.py") $(if ($args) { $args } else { @("stock", "2330") }) }
# 批328 實錄:拉齊後既開視窗仍是舊短令冊(profile 只在開窗時點源)→via-reload=本窗重點源尾版冊,免開新視窗
# 批331 實錄:via-reload 只重載磁碟冊,未拉齊=仍舊版→先 fetch+ff-only 再重載(分流不動;VIA-ALL 才對齊)
# 批337 實錄:工作站 pull 被本地再生頁(VIA_UI_Portal)差異擋下,而 via-reload 靜默 2>$null=假拉齊(HEAD 不動仍印「已拉齊」)。
# 改:①fetch ②ui_support 產出頁本地差異=再生物→自動還原讓位(git checkout;誠實印件數)③ff-only 失敗=印 git 原話+阻擋檔清單(不 reset 不 stash 其他檔)④重載尾版冊+印 HEAD 前後
function global:via-reload {
    $root = Split-Path $VIA -Parent
    $before = git -C $root rev-parse --short HEAD
    git -C $root fetch -q origin main 2>$null
    # 批348 再生物冊:引擎每次自測/再生會回寫的追蹤檔=產物非正本→拉齊前自動還原讓位(誠實印件數);台帳 VIA_AutoCode_Registry 永不還原(append-only)
    $regen = "^VeritasIntelligenceAnalytics/(supportive modules/ui_support/.*\.html|supportive modules/registry/VIA_(Engine_Consolidation_Register|Engine_Contract|SSOT_RegexDict|Schema_Registry|Tool_Escalation_Ladder|Unified_Register|IndustryUnifiedMap|Problem_Ledger|NetModules_Integration_Register|AccelModules_Integration_Register|VDFArchitecture|ProjectCompletion|ProductGate|ParallelLanes)_v\d+\.json|VIA-TOWER-RESET\.cmd|functional modules/VAP/references/intake/VAP_v025_Complete_Package/(output|spec)/.*\.json)$"
    $gen = @(git -C $root status --porcelain 2>$null | Where-Object { $_.Substring(0,2) -match "M" } | ForEach-Object { $_.Substring(3).Trim('"') } | Where-Object { $_ -match $regen -and $_ -notmatch "EditableTemplate" -and $_ -notmatch "VIA_AutoCode_Registry" })  # 批338:可編輯模板=操作員手改件,永不還原
    if ($gen.Count -gt 0) { git -C $root checkout -q -- $gen 2>$null; Write-Host ("  [VIA] 產出頁本地差異 " + $gen.Count + " 件=再生物,已還原讓位(誠實):" + ($gen -join ", ")) -ForegroundColor DarkYellow }
    $out = (git -C $root merge --ff-only origin/main 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        # 批347:阻擋檔=本地未提交→自動 stash(含未追蹤;記名)→ff-only→pop(VIA.ps1 Sync-Repo 同律;pop 衝突=stash 留存誠實印)
        $blk = @(git -C $root status --porcelain 2>$null)
        if ($blk.Count -gt 0 -and $out -match "overwritten|local changes|Not possible to fast-forward|Diverging") {
            $stMsg = "via-reload " + (Get-Date -Format "yyyyMMdd_HHmmss")
            git -C $root stash push --include-untracked -q -m $stMsg 2>$null
            Write-Host ("  [VIA] 阻擋檔 " + $blk.Count + " 件已 stash(" + $stMsg + "),拉齊後自動還原") -ForegroundColor DarkYellow
            $out = (git -C $root merge --ff-only origin/main 2>&1 | Out-String).Trim()
            $ffrc = $LASTEXITCODE
            $pop = (git -C $root stash pop 2>&1 | Out-String).Trim()
            if ($LASTEXITCODE -ne 0) { Write-Host ("  [VIA] stash 還原衝突(誠實;stash 留存,手動 git stash pop):" + $pop) -ForegroundColor Yellow } else { Write-Host "  [VIA] 阻擋檔已原樣還原" -ForegroundColor DarkYellow }
            if ($ffrc -ne 0) { Write-Host ("  [VIA] 拉齊仍失敗(誠實;非阻擋檔問題=分歧,見 git 原話):" + $out) -ForegroundColor Yellow }
            $global:LASTEXITCODE = $ffrc
        } else {
            Write-Host ("  [VIA] 拉齊失敗(誠實):" + $out) -ForegroundColor Yellow
            if ($blk.Count -gt 0) { Write-Host ("  [VIA] 阻擋檔:`n    " + ($blk -join "`n    ")) -ForegroundColor Yellow }
        }
    }
    # 批367 同名雙物讓位後復位:小寫梭 via-all/via-rootcheck/via-tower-reset.cmd 已 git mv 入收容冊;Windows 大小寫不分=git 刪小寫可能連帶刪掉大寫原件實體→缺即自 HEAD 復位(唯讀 checkout;誠實印)
    $caseOrig = @("VIA-ALL.cmd", "VIA-ROOTCHECK.cmd", "VIA-TOWER-RESET.cmd") | Where-Object { -not (Test-Path -LiteralPath (Join-Path $VIA $_)) -and (git -C $root ls-files --error-unmatch ("VeritasIntelligenceAnalytics/" + $_) 2>$null) }
    if ($caseOrig.Count -gt 0) { foreach ($c in $caseOrig) { git -C $root checkout -q -- ("VeritasIntelligenceAnalytics/" + $c) 2>$null }; Write-Host ("  [VIA] 同名雙物讓位後大寫原件復位 " + $caseOrig.Count + " 件:" + ($caseOrig -join ", ")) -ForegroundColor DarkYellow }
    $r = Get-VIANewest $VIA "Register-VIA-Commands-v*.ps1"; . $r
    $after = git -C $root rev-parse --short HEAD
    Write-Host ("  [VIA] 短令冊重載:" + (Split-Path $r -Leaf) + " · HEAD " + $before + " → " + $after + $(if ($before -eq $after -and $LASTEXITCODE -ne 0) { "(未拉齊)" } else { "" })) -ForegroundColor Green
}
# 批330:繪圖/TA 資料律稽核(價=還原 量=扣當沖;CGC_MDL118 尾版 --audit)
function global:via-plotlaw { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL118_PlotDataLaw_v*.py") $(if ($args) { $args } else { "--audit" }) }
# 批332:系統總台=六主體標準 U/I(VIA 首頁所有擷取資料/VDF/VAP/主動 ETF 分類/族群輪動/月營收);via-system 再生頁並開啟(樞紐在線=LIVE;否則 SNAPSHOT 誠實);via-api <主體> 印後端 JSON
function global:via-system { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL120_SystemUI_v*.py") $(if ($args) { $args } else { "--open" }) }
function global:via-api { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL119_SystemAPI_v*.py") $(if ($args) { $args } else { "subjects" }) }
# 批333:總控台=Codex 設計正本(VIA_SYSTEM_MANAGER 尾版 ui 再生)由樞紐同源 /master 供應(CSRF 權杖注入;file:// 唯讀預覽自動導同源);via-master=再生頁+開 /master(樞紐未起先打 via)
function global:via-master { python (Get-VIANewest "$VIA" "VIA_SYSTEM_MANAGER_v*.py") ui --no-open; Start-Process "http://127.0.0.1:8765/master" }
# 批335:一鍵完工=未完工作冊(via-complete 印冊)+完工鏈 16 步依序跑(via-complete run;--only a,b 子集;--skip-net 離線試跑);閘(批212/P08/P09/P18)零自動解除
# 批336:上船件冊=references/intake 全收容包 × 整合鏈(引擎/頁/短令/任務)頁;via-intake-roster --open
function global:via-intake-roster { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL122_IntakeRoster_v*.py") $(if ($args) { $args } else { "--open" }) }
# 批340:一鍵完工=分離工人+直播尾讀(Invoke-VIA-Complete 啟動器;PS-ACCEL;關窗不斷;Ctrl-C 只離開觀看);無參數=印未完工作冊
# 批344:via-complete watch=重接最新 LAUNCH log 直播(Ctrl-C 只離開);via-complete stop=依最新 RUN_*/PROGRESS.json 停 MDL121 本體+當前步子程序(工人 Ctrl-C 免疫後唯一停止法)
function global:via-complete { if ($args.Count -gt 0 -and $args[0] -eq "watch") { $lg = Get-ChildItem "$VIA\VIA_Reports\completion" -Filter "LAUNCH_*.log" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1; if ($lg) { Write-Host ("  [watch] " + $lg.FullName + "(Ctrl-C 只離開)") -ForegroundColor Cyan; Get-Content -Path $lg.FullName -Wait -Tail 20 -Encoding UTF8 } else { Write-Host "  [watch] 無 LAUNCH log" -ForegroundColor Yellow }; return }
    if ($args.Count -gt 0 -and $args[0] -eq "stop") { $pj = Get-ChildItem "$VIA\VIA_Reports\completion" -Filter "PROGRESS.json" -File -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1; if (-not $pj) { Write-Host "  [stop] 無 PROGRESS.json(無在跑工人)" -ForegroundColor Yellow; return }; $j = Get-Content $pj.FullName -Raw -Encoding UTF8 | ConvertFrom-Json; foreach ($id in @($j.pid, $j.self_pid)) { if ($id) { $pr = Get-Process -Id $id -ErrorAction SilentlyContinue; if ($pr) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue; Write-Host ("  [stop] 已停 PID " + $id + "(" + $pr.ProcessName + ")") -ForegroundColor Yellow } else { Write-Host ("  [stop] PID " + $id + " 不在(已結束)") -ForegroundColor DarkGray } } }; Write-Host ("  [stop] 步 " + $j.step + "/" + $j.total + " " + $j.id + " · " + $pj.FullName) -ForegroundColor DarkGray; return }
    if ($args.Count -gt 0 -and $args[0] -eq "run") { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-Complete-v*.ps1") @($args | Select-Object -Skip 1) } else { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL121_CompletionAutomator_v*.py") @args } }
# 批340:資料本機家=接點律(倉內 output_hub→本機資料家 Junction;145 引擎零改;增量更新經接點寫入本機);via-datahome=status;via-datahome link/find/unlink
function global:via-datahome { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL123_DataHome_v*.py") $(if ($args) { $args } else { "status" }) }
# 批350:紅站一鍵補齊鏈(MDL125:datahome 接點→OpenCC 輔助安裝→global 全球擷取→consensus/revenue_consensus→--refail 複驗;NET 步雙同意閘;誠實三態;心跳進度條);via-fixall=印步冊;via-fixall run [--only a,b] [--dry]
function global:via-fixall { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL125_FixAll_v*.py") @args }
# 批358:手機一鍵改名 via-mobile(工作站實錄:PATH 上已有操作員之 via-go=「VIA AllGreen 一鍵統包 v0100」;同名=九頭龍→讓位);=拉齊→六流程 dry-run→紅站補齊鏈(含時段實測)→digest
# 批366:操作員令「不要一直跳出 VS Code,自動到底完成所有動作」→ via-mobile 全程 VIA_NO_OPEN=1(SUP_MDL737 v0104 py 閘+PS-ACCEL 模組 PS 閘;所有頁面只落檔不跳出;結束後 via-open 可看);--open 覆寫
function global:via-mobile { $o = ($args -contains "--open"); $a = @($args | Where-Object { $_ -ne "--open" }); $env:VIA_NO_OPEN = $(if ($o) { "0" } else { "1" }); via-reload; Write-Host "--- [via-mobile] 六流程 dry-run(零跳出 VIA_NO_OPEN=$env:VIA_NO_OPEN)---" -ForegroundColor Cyan; via-six --no-open; Write-Host "--- [via-mobile] 紅站補齊鏈 ---" -ForegroundColor Cyan; if ($a -contains "--lanes") { $a = @($a | Where-Object { $_ -ne "--lanes" }); via-lanes run @a } else { via-fixall run @a }; Write-Host "--- [via-mobile] 四專案完工矩陣 ---" -ForegroundColor Cyan; via-projects digest; Write-Host "--- [via-mobile] 產品資格閘(九閘)---" -ForegroundColor Cyan; via-productgate digest; $env:VIA_NO_OPEN = $(if ($env:VIA_OPEN_PAGES -eq "1") { "0" } else { "1" }); Write-Host "--- [via-mobile] 完成;頁面已落檔未跳出;看頁:via-open 產品 / via-open 竣工 / via-open 架構 ---" -ForegroundColor Cyan }
# 批353:網路車道時段基準(操作員令「先測一些時段」;chart/chart×N(accel_map)/yf 三車道同標的同時段實測秒數與成功率;零入庫;親跑=同意);via-netbench [--tickers 2330,2317] [--days 60] [--workers 4] [--pause 0.35]
function global:via-netbench { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL126_NetBench_v*.py") run @args }
# 批360/361:FRED 宏觀 SSOT 擷取(ENG074;macro_ssot 190 series 從新往舊;checkpoint;accel_map+節流;parquet+DuckDB us_macro+polars 鏡;落 output_hub/mega=接點→本機資料家;鑰缺=當場輸入;親跑=同意);via-fred [run|status|lamps] [--since 1990-01-01] [--workers 4] [--rpm 100] [--only CPIAUCSL,UNRATE] [--fred-key <key>]
function global:via-fred { $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"; $a = @($args); if (-not ($a | Where-Object { $_ -in @("run", "status", "lamps", "help") })) { $a = @("run") + $a }; python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG074_FredMacroSSOT_v*.py") @a }
# 批368:月營收全市場史深回補(ENG075;MOPS t21sc03 上市/上櫃 國內/KY 月檔 2023-01→ 從新往舊;Big5;只增 anti-join;checkpoint;親跑=同意);via-revfill [run] [--since 2023-01] [--workers 3] [--max-months N] | status;(名 via-rev 讓位另線工作站別名=先發先得)
function global:via-revfill { $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"; python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG075_MonthlyRevenueBackfill_v*.py") $(if ($args) { $args } else { "run" }) }
# 批371:VES 橋(MDL132)=尾版鏡像(史版不當多頭)→第 1 跑→安全種子決策(VIA 動詞冊/橋塊 REJECT/selftest 群 REJECT;append-only)→第 2 跑確定性套用;唯讀;--apply 永不經短令;via-ves [--root <相對子樹>] [--no-seed] [--single];via-ves --raw <VES 原生參數…>(直通收容原件,如 --slice <碼>)
function global:via-ves { if ($args -contains "--apply") { Write-Host "  [via-ves] --apply 不經短令(操作員親打 python <VES> --apply --token <hint>;Zero-Hydra 律)" -ForegroundColor Yellow; return }; if ($args -contains "--raw") { $ves = Get-VIANewest "$VIA\supportive modules\references\intake\VIA_VES_EngineStandardizer_b*" "via_engine_standardizer.py"; $a = @($args | Where-Object { $_ -ne "--raw" }); if (-not ($a -contains "--root")) { $a = @("--root", "$VIA\VIA_Reports\ves\tails_tree") + $a }; if (-not ($a -contains "--out")) { $a = @("--out", "$VIA\VIA_Reports\ves\out") + $a }; python $ves --no-ml-probe @a; return }; python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL132_VesBridge_v*.py") run @args }
# 批375:主動 ETF 每日持股史深覆蓋+缺口回補(ENG078;IPO 起應有交易日 vs 快照;車道冊 VIA_ActiveETF_HistoryLanes VERIFIED 才呼;缺源=NO_SOURCE 誠實;親跑=同意);via-etfhist [daily [--offline] [--max-days N] | backfill | status]
function global:via-etfhist { $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"; python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG078_ActiveETFHoldingsHistory_v*.py") $(if ($args) { $args } else { "daily" }) }
# 批374:主動 ETF 宇宙日更(ENG077;A 碼律 ^\d{5}A$ + 國內成分揭露律;TWSE 官方冊→etf_book 後備→既有聯集只增;寫 ENG051 SSOT csv;親跑=同意);via-etfuniv [run [--offline] | status]
function global:via-etfuniv { $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"; python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG077_ActiveETFUniverse_v*.py") $(if ($args) { $args } else { "run" }) }
# 批373:主動 ETF 持股×月營收動能(ENG076;兩專案合流層;零網路;加權 yoy/重疊榜;頁 VIA_UI_ETFRevenueMomentum);via-etfrev [run|status]
function global:via-etfrev { python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG076_ETFRevenueMomentum_v*.py") $(if ($args) { $args } else { "run" }) }
# 批379/380:via-autorun=一鍵全自動四閘版:①via-accel --activate(20 加速器)②via-lanes plan(Hydra 哨兵 H1–H6;H3/H5 FAIL=誠實停)③via-mobile --lanes(拉齊→六流程→十道並行→矩陣→產品閘)④lanes digest;零跳出、零 TTY 等待(VIA_FRED_PROMPT=0)、逾時 kill 不卡斷;雙擊 via-autorun.cmd 同效且結束停窗
function global:via-autorun { $env:VIA_NO_OPEN = "1"; $env:VIA_FRED_PROMPT = "0"; $env:GIT_EDITOR = "true"; $env:PYTHONUTF8 = "1"
    Write-Host "=== [via-autorun] 一鍵全自動(單一 PowerShell;零跳出;不卡斷;約 20–60 分鐘)===" -ForegroundColor Cyan
    Write-Host "--- ① 20 加速器點亮(SUP_MDL737 --activate;缺席=誠實 SKIP 零影響)---" -ForegroundColor Cyan; try { via-accel --activate } catch { Write-Host ("  [加速器] " + $_.Exception.Message) -ForegroundColor Yellow }
    Write-Host "--- ② 九頭龍哨兵 H1–H6(唯讀;H3 進程雙頭/H5 尾版律 FAIL=誠實停,不跑)---" -ForegroundColor Cyan; $plan = (via-lanes plan 2>&1 | Out-String); Write-Host $plan
    if ($plan -match "H3 FAIL|H5 FAIL") { Write-Host "=== [via-autorun] 九頭龍風險(見上 H3/H5)=停;請先關閉另一條在跑的補齊鏈或修尾版後重試 ===" -ForegroundColor Red; return }
    Write-Host "--- ③ 全自動主鏈(拉齊→六流程 dry-run→十道並行補齊→四專案矩陣→產品閘)---" -ForegroundColor Cyan; via-mobile --lanes
    Write-Host "--- ④ 十道並行存證 ---" -ForegroundColor Cyan; via-lanes digest
    Write-Host "=== [via-autorun] 畢;看頁:via-open 產品 ===" -ForegroundColor Cyan }
# 批378:via-open <片段|路徑>=只走瀏覽器可執行檔(Edge/Chrome/Firefox 依序),永不經 .html 預設程式(VS Code);缺瀏覽器=印路徑。別名:產品→ProductGate 竣工→ProjectCompletion 架構→VDFArchitecture 道→ParallelLanes 總控→MasterControl
function global:via-open { $alias = @{ "產品" = "VIA_UI_ProductGate"; "竣工" = "VIA_UI_ProjectCompletion"; "架構" = "VIA_UI_VDFArchitecture"; "道" = "VIA_UI_ParallelLanes"; "總控" = "VIA_UI_MasterControl"; "整" = "VIA_UI_Consolidated"; "系統" = "VIA_UI_SystemConsole"; "矩陣" = "VIA_MasterControl_Matrix"; "入口" = ("" + $VIA + "\VIA_Reports\entry\ENTRY_latest.html") }; $q = if ($args.Count -gt 0) { "" + $args[0] } else { "VIA_UI_ProductGate" }; if ($alias.ContainsKey($q)) { $q = $alias[$q] }; $ui = Join-Path $VIA "supportive modules\ui_support"; $f = if (Test-Path -LiteralPath $q) { Get-Item -LiteralPath $q } else { Get-ChildItem -LiteralPath $ui -Filter "*.html" | Where-Object { $_.Name -like ("*" + $q + "*") } | Sort-Object Name | Select-Object -Last 1 }; if (-not $f) { Write-Host ("  [via-open] 找不到頁:" + $q + "(ui_support 內 *.html 片段或完整路徑)") -ForegroundColor Yellow; return }; $bx = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe", "$env:ProgramFiles\Mozilla Firefox\firefox.exe") | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1; if ($bx) { Start-Process -FilePath $bx -ArgumentList ("`"" + $f.FullName + "`""); Write-Host ("  [via-open] " + (Split-Path $bx -Leaf) + " ← " + $f.Name) -ForegroundColor Green } else { Write-Host ("  [via-open] 未找到瀏覽器 exe;請手動以瀏覽器開:" + $f.FullName) -ForegroundColor Yellow } }
# 批377:十道並行安全編排(MDL134;FixAll 步冊→資源鏈 DAG:同庫序跑/鏈間並行≤10;Hydra 哨兵 H1 同名/H2 同版/H3 進程雙頭(鎖)/H4 單寫者/H5 尾版;離線 net 步 SKIP;零 force);via-lanes [plan | run [--workers N] [--only a,b] [--dry] | digest];via-mobile --lanes=補齊鏈改並行
function global:via-lanes { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL134_ParallelLanes_v*.py") $(if ($args) { $args } else { "plan" }) }
# 批376:產品資格閘(MDL133;九閘 G1 矩陣存證/G2 短令↔梭/G3 樞紐任務/G4 頁衛生/G5 再生物讓位/G6 鑰匙守衛/G7 引擎尾版/G8 短令在位/G9 用法;QUALIFIED/CONDITIONAL/NOT_QUALIFIED 永不假綠);via-productgate [build --open | digest | --json]
function global:via-productgate { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL133_ProductGate_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批368:四專案完工矩陣(MDL131;VDF/VRN/主動 ETF/月營收 × grid 存證 × DuckDB 深度 × 任務/頁/令;RYG+下一指令;八段循環證據);via-projects [build --open | digest]
function global:via-projects { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL131_ProjectCompletion_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批360:VDF 資料架構(ENG073;SSOT 12 類→現役表/引擎/車道對映;DuckDB 盤點;--optimize dry-run 只增不減;--go 才寫;頁 VIA_UI_VDFArchitecture);via-vdfarch [build --open | --optimize [--go]]
function global:via-vdfarch { python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG073_DataArchitecture_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批352:VIA SuperHtml Parser(HTML content+UI component+JS/CSS logic+backend→Markdown;bs4/lxml/esprima/tinycss2/markitdown;NLP OneEngine v1.5.0 語意橋;自建根 C:\VIA\VeritasSuperHtmlParser);via-superhtml <路徑...> [-NoOpen] [-NlpSource <zip|夾>];需 pwsh 7
function global:via-superhtml { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; $t = @($args | Where-Object { $_ -notmatch "^-" }); $o = @($args | Where-Object { $_ -match "^-" }); if ($t.Count -gt 0) { & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-SuperHtmlParser-v*.ps1") -Targets $t @o } else { & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-SuperHtmlParser-v*.ps1") @o } }
# 批345:橋塊掃描/注入(ACCEL-BRIDGE 全樹/NET-BRIDGE VDF;預設 dry-run;--apply 才寫;排除冊=獨立工具不可動/凍結群/收容原件/退役);via-bridge-sweep [--net] [--accel] [--root <rel>] [--apply]
function global:via-bridge-sweep { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL124_BridgeSweeper_v*.py") @args }
# 批342:六流程 Zero-Hydra 編排(Invoke-VIA-SixStreams 尾版;九流分離子進程/獨立 log/硬逾時/文字進度條;PS-ACCEL;缺件=誠實 SKIP;tally 逐字取各工具 [計] 行);via-six [-GoToken GO_v1] [-NoOpen] [-StreamTimeoutS 900];需 pwsh 7
# 批354:via-six 正主=CGC_MDL127_SixStreams(py;九子行程並行;A01–A20 加速器燈;dry-run 預設;--go 只放行 S1);via-six --ps=退 Invoke-VIA-SixStreams ps1 後備
function global:via-six { if ($args -contains "--ps") { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-SixStreams-v*.ps1") @($args | Where-Object { $_ -ne "--ps" }) } else { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL127_SixStreams_v*.py") run @args } }
# 批354:系統結構總冊(MDL128;七域+治理核;--probe --days 2 兩日試鏈)/生命週期 RACI(MDL129;via-loop=≤25 行 digest)/UI 橋接整合台(MDL130;spec+template→VIA_UI_Consolidated;VHUIRE 品質閘)
function global:via-charter { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL128_SystemCharter_v*.py") $(if ($args) { $args } else { "--open" }) }
function global:via-loop { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL129_LifecycleRACI_v*.py") $(if ($args) { $args } else { "digest" }) }
function global:via-ui { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL130_UIBridge_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批316:族群分類一鍵管線(補料→ENG070 自測+run→ENG071 自測+run→開頁;pwsh 缺退 powershell)
function global:via-pipeline { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-GroupPipeline-v*.ps1") @args }

# 批381:環境治理統一引擎(MDL135):①全景式分析 base+via_core*+via_*/paddle*/camelot*(平行探針硬逾時不卡斷)②uv pip check 毫秒快篩(退 pip)③base 該有冊(Baseline 冊:工具鏈+引擎核心+LOW)+相依閉包=該有;閉包外=拉出候選 ④衝突要求者家族整包路由(via_core 白名單→家族 target_env(如 OCR→paddle_312 contrib 錨)→purpose hints→5D→黑環境)⑤H1–H6 九頭龍分流:Parallel-Fixable 並行/Sequence-Dependent 拓撲序 ⑥三輪 R1/R2/R3 ⑦uv pip compile 多輪沙盒模擬(同意閘)⑧apply --approve 只跑 GREEN 非破壞段;base 移除 --approve-remove 且目標境 VERIFY 綠後 ⑨LKGC 晉升律+rollback(LKGC lock 逐境 sync;無=原本規劃重建)⑩logs/env_governance.log JSONL+四分區矩陣;批382 +rename 命名律(非 via_ 境換名重建:uv venv 同 Python+lock sync+check;--approve-remove 退役舊境)+base 共用冊/功能件家族(docs/html_parse/data_fetch/nlp/dev_tools/plot_ui→既有 via_ 境)+專屬境覆寫;via-envgov [run|panorama|plan|apply|lkgc|rollback|rename|matrix|digest] [--offline] [--approve] [--approve-remove] [--only S02,S03] [--env-root P] [--base-python EXE]
function global:via-envgov { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL135_EnvGovernance_v*.py") $(if ($args) { $args } else { @("run", "--offline") }) }
# 批381:單一 PowerShell 一貼即用(Invoke-VIA-EnvGovernance 尾版):①20 加速器點亮 ②全景+計畫(唯讀)③-Approve 執行 GREEN 段(-ApproveRemove 破壞段)④矩陣落檔零跳出;-Online 開同意閘;-Background 背景 Job 不阻塞(-Watch 直播 log);-Open 只走瀏覽器 exe
function global:via-envgov-auto { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-EnvGovernance-v*.ps1") @args }

# 批383:單一入口(操作員令「單一入口與這個(SYSTEM MANAGER MATRIX v0700)整合」):via-entry=母倉唯一入口燈板(GitHub/Mother/Data/Env/PATH/EnvGov/VDF-DB/VAP/Matrix/Console/Grok;零網路;落 VIA_Reports/entry)
# via-entry plan=一貼即用 11 步;via-entry roster=短令冊(母倉∪Grok 撞名冊);--scan 加跑 via-envgov 全景;--open 開矩陣頁(瀏覽器道零跳出);--console 帶起 Grok 網頁主控台(背景)
function global:via-entry { $a = @($args); if ($a.Count -gt 0 -and ($a[0] -in @("plan", "roster", "status", "envpy"))) { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL136_EntryBridge_v*.py") @a; return }
    Set-Location -LiteralPath $VIA; $env:VIA_ROOT = $VIA; $env:PYTHONNOUSERSITE = "1"; $env:PYTHONUTF8 = "1"; if (-not $env:VIA_NET) { $env:VIA_NET = "0" }
    Write-Host ("=== [via-entry] VIA 唯一入口(母倉 " + $VIA + ";Grok 主控台=via-webconsole 子入口;LIVE 預設關 VIA_NET=" + $env:VIA_NET + ";零跳出 VIA_NO_OPEN=" + $env:VIA_NO_OPEN + ")===") -ForegroundColor Cyan
    foreach ($f in @("vdf", "vrn", "vap")) { $p = Get-VIAEnvPython $f; Write-Host ("  [境] " + $f + " → " + $p + $(if ($p -eq "python") { "(base 退路;功能件境未見)" } else { "" })) -ForegroundColor $(if ($p -eq "python") { "Yellow" } else { "Green" }) }
    python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL136_EntryBridge_v*.py") status
    if ($a -contains "--scan") { Write-Host "--- [via-entry] 環境治理全景(唯讀)---" -ForegroundColor Cyan; via-envgov run --offline }
    if ($a -contains "--open") { via-open 矩陣 }
    if ($a -contains "--console") { via-webconsole --background }
    Write-Host "  [via-entry] 次序:via-entry plan(11 步)· via-envgov · via-envgov apply --approve --only-kind REPAIR_BASE · via-vdfdb scan · via-vapone · via-open 矩陣 · via-webconsole" -ForegroundColor Cyan }
# 批383:via-env=環境治理正本(MDL135 via-envgov;Grok 版 39 行樁改名 via-env-grok 留冊);via-grok=Grok 短令冊(load 重載;matrix 開 WPF 右側板)
function global:via-env { via-envgov @args }
function global:via-grok { if ($args -contains "load") { $global:VIAGrokVerbs = @(Import-VIAGrokMatrix) }; if ($args -contains "matrix") { if (Get-Command via-matrix -ErrorAction SilentlyContinue) { via-matrix } else { Write-Host "  [via-grok] via-matrix 未載(收容包缺或 VIA_GROK_MATRIX=0;via-grok load)" -ForegroundColor Yellow }; return }; python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL136_EntryBridge_v*.py") roster }
# 批383:via-webconsole=Grok 網頁主控台(收容包 b383;TanStack/Vite;npm run dev 0.0.0.0:8080):node_modules 缺=須 npm install 觸網→ --install 或 $env:VIA_NET_CONSENT="YES" 同意閘;--background 另窗最小化(關窗即停;不 Stop-Process)
function global:via-webconsole { $dir = "$VIA\supportive modules\references\intake\VIA_GrokConsole_AuroraAcorn_b383"; if (-not (Test-Path -LiteralPath "$dir\package.json")) { Write-Host ("  [via-webconsole] 收容包缺 " + $dir) -ForegroundColor Yellow; return }
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Host "  [via-webconsole] 未見 npm(Node 22);裝 Node 後再試;離線總控矩陣頁:via-open 矩陣" -ForegroundColor Yellow; return }
    if (-not (Test-Path -LiteralPath "$dir\node_modules")) { if (($args -contains "--install") -or ($env:VIA_NET_CONSENT -eq "YES")) { Write-Host "  [via-webconsole] npm install(觸網;同意閘已過)…" -ForegroundColor Cyan; Push-Location -LiteralPath $dir; try { npm install --no-audit --no-fund } finally { Pop-Location } } else { Write-Host "  [via-webconsole] node_modules 缺=需 npm install(觸網);同意:via-webconsole --install(或 `$env:VIA_NET_CONSENT='YES')" -ForegroundColor Yellow; return } }
    if (-not (Test-Path -LiteralPath "$dir\node_modules")) { Write-Host "  [via-webconsole] node_modules 仍缺(npm install 失敗?)=誠實停" -ForegroundColor Red; return }
    Write-Host "  [via-webconsole] http://localhost:8080(Grok 主控台;LIVE 預設關 VIA_NET=0;KEY 永不入檔)" -ForegroundColor Green
    if ($args -contains "--background") { Start-Process -FilePath $env:ComSpec -ArgumentList "/k npm run dev" -WorkingDirectory $dir -WindowStyle Minimized; Write-Host "  [via-webconsole] 已於最小化視窗帶起(關該窗即停)" -ForegroundColor Green } else { Push-Location -LiteralPath $dir; try { npm run dev } finally { Pop-Location } } }
# 批383:via-vapone=VAP ONE 單檔整合引擎(VAP_ENG016;圖規 SSOT 40/圖規鎖/批330 資料律/零依賴 SVG+Plotly+Matplotlib 車道;無參數=--selftest;via_vap_312 python 優先=全車道)
function global:via-vapone { $py = Get-VIAEnvPython "vap"; & $py (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG016_AutoplotOne_v*.py") $(if ($args) { $args } else { "--selftest" }) }
# 批383:via-vdfdb=本機三庫整併入正典 DuckDB(VDF_ENG079;C:\新增資料夾\新增資料夾\VIA_db_part1_prices/part2_chips/part3_rest;COPY_ONLY anti-join 只補缺鍵;檔冊 sha 已入=跳過;ckpt=ENG064 checkpoint 重建=抓過不再抓;need=缺口清單);無參數=scan 唯讀;run --apply 才寫
function global:via-vdfdb { $py = Get-VIAEnvPython "vdf"; & $py (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG079_LocalDbConsolidate_v*.py") $(if ($args) { $args } else { "scan" }) }
# --- 自註冊:$PROFILE 補一行點源(冪等;標記 v0200) -------------------
try {
    # 批260:profile 行改尾版 glob(v0200 曾寫死 v0100 路徑=新版不自動吃)
    $mark = "# [VIA:PROFILE:v0201] 點源尾版(pull 即最新;永久免重貼)"
    if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Force $PROFILE | Out-Null }
    if (-not (Select-String -Path $PROFILE -Pattern "VIA:PROFILE:v0201" -Quiet -ErrorAction SilentlyContinue)) {
        $dir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $line = '. (Get-ChildItem "' + $dir + '\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName'
        @("", $mark, $line) | Add-Content -Path $PROFILE -Encoding UTF8
        Write-Host "  [註冊] profile 點源一行已入(以後 pull 即自動最新)" -ForegroundColor Green
    }
} catch { }
# 批339:短令清單改動態自本檔實掃(實錄:靜態字串停在 v0112,新令 via-master/via-complete/via-intake-roster 未列)
$viaCmds = (Select-String -LiteralPath $MyInvocation.MyCommand.Path -Pattern '^function global:([\w-]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Where-Object { $_ -notin @("Get-VIANewest", "Get-VIAEnvPython", "Import-VIAGrokMatrix") }) -join "/"
Write-Host ("  [VIA] 短指令已生效於本視窗(" + (Split-Path $MyInvocation.MyCommand.Path -Leaf) + "):" + $viaCmds) -ForegroundColor Cyan
if ($VIAGrokVerbs.Count -gt 0) { Write-Host ("  [VIA] +Grok 矩陣 " + $VIAGrokVerbs.Count + " 令(母倉撞名者 -grok):" + ($VIAGrokVerbs -join "/") + " · 唯一入口:via-entry") -ForegroundColor DarkCyan }

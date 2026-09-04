# =====================================================================
# Register-VIA-Commands-v0133.ps1 — VIA 短指令唯一定義處(批360/361 +via-fred/via-vdfarch;批254 立;批260 +via-all;批316 +via-pipeline;批323 +via-accel/via-accel-check;批325 +via-rotation/via-repo-optimize;批327 +via-vapstack;批328 +via-reload;批330 +via-plotlaw;批331 via-reload 先拉齊;批332 +via-system/via-api;批333 +via-master;批335 +via-complete;批336 +via-intake-roster;批337 via-reload 拉齊誠實+產出頁自動讓位;批338 可編輯模板排除;批339 短令清單動態;批340 +via-datahome/via-complete 分離啟動器;批342 +via-six 六流程 Zero-Hydra 編排;批344 via-complete watch/stop;批345 +via-bridge-sweep)
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

function global:Get-VIANewest([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}

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
    $regen = "^VeritasIntelligenceAnalytics/(supportive modules/ui_support/.*\.html|supportive modules/registry/VIA_(Engine_Consolidation_Register|Engine_Contract|SSOT_RegexDict|Schema_Registry|Tool_Escalation_Ladder|Unified_Register|IndustryUnifiedMap|Problem_Ledger|NetModules_Integration_Register|AccelModules_Integration_Register|VDFArchitecture)_v\d+\.json|VIA-TOWER-RESET\.cmd|functional modules/VAP/references/intake/VAP_v025_Complete_Package/(output|spec)/.*\.json)$"
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
function global:via-mobile { via-reload; Write-Host "--- [via-mobile] 六流程 dry-run ---" -ForegroundColor Cyan; via-six --no-open; Write-Host "--- [via-mobile] 紅站補齊鏈 ---" -ForegroundColor Cyan; via-fixall run @args }
# 批353:網路車道時段基準(操作員令「先測一些時段」;chart/chart×N(accel_map)/yf 三車道同標的同時段實測秒數與成功率;零入庫;親跑=同意);via-netbench [--tickers 2330,2317] [--days 60] [--workers 4] [--pause 0.35]
function global:via-netbench { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL126_NetBench_v*.py") run @args }
# 批360/361:FRED 宏觀 SSOT 擷取(ENG074;macro_ssot 190 series 從新往舊;checkpoint;accel_map+節流;parquet+DuckDB us_macro+polars 鏡;落 output_hub/mega=接點→本機資料家;鑰缺=當場輸入;親跑=同意);via-fred [run|status|lamps] [--since 1990-01-01] [--workers 4] [--rpm 100] [--only CPIAUCSL,UNRATE] [--fred-key <key>]
function global:via-fred { $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"; python (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG074_FredMacroSSOT_v*.py") $(if ($args) { $args } else { "run" }) }
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
$viaCmds = (Select-String -LiteralPath $MyInvocation.MyCommand.Path -Pattern '^function global:([\w-]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Where-Object { $_ -ne "Get-VIANewest" }) -join "/"
Write-Host ("  [VIA] 短指令已生效於本視窗(" + (Split-Path $MyInvocation.MyCommand.Path -Leaf) + "):" + $viaCmds) -ForegroundColor Cyan

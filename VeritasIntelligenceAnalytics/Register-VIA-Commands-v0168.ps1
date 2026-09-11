# =====================================================================
# Register-VIA-Commands-v0168.ps1 — VIA 短指令唯一定義處(批381→合流:+via-vdffetch [年份](預設 2023;單一指令:年份旗標→20 加速器→Hydra 哨兵→十一步資料鏈十道並行→存證;零跳出零互動不卡斷);批423 操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」:+via-allgreen(尾版律起 Invoke-VIA-AllGreen-v*.ps1;別名 統包)。工作站實錄 via-go 停在「── ① TEST(自測矩陣)──」不動=看起來死機,根因兩條皆在 AllGreen v0100:①`$out = & `$PY @Argv 2>&1 | Out-String` 把子行程輸出緩衝到結束才吐(200 站期間畫面全白)②`$StageTimeoutSec` 宣告了但**全檔從未使用**=任一站真卡住就永遠等。v0101 改 Start-Process+邊跑邊 tail、逾時 Kill 記 TIMEOUT、Write-Progress 進度列、開跑點 20 加速器名;格子 v0262 補動態進度條/SELFTEST_PROGRESS.json 心跳/Ctrl+C 安全落檔(rc=130)。via-go 是操作員自己 PATH 上的檔(批358 讓位律),短令冊不佔該名,改登錄 via-allgreen;批421 操作員令「REGISTER AND IMPLEMENT THESE TWO SYSTEMS AS SUPPORTIVE MODULES TO SUPPORT VRN」:+via-gle(SUP_MDL743 GLE 全後端統轄橋;status|probe|route;別名 版面橋)+via-nlp(SUP_MDL744 NLP 應用系統統轄橋;status|roster|delta|demo;別名 語意橋)。GLE v2.1.0 上傳包對在庫 b245 逐檔比對 16/18 位元相同,installer 唯一差異是 ${ExitCode}: 改成 $ExitCode:(PowerShell 會把冒號誤讀成限定符=上傳版反而是回歸,不採),另一枚 dist whl 是原始碼建置產物=**不重複收容**,改把在庫收容件升格為全樹可用支援服務;NLP 確為新版,VIA_NLP_Application_System v1.8.0 68 檔入收容夾。兩橋修同一個真缺口:ENG072 v0106/ENG073 v0113 把 NLP 收容夾**寫死** VIA_NLP_OneEngine_v1.1.0(18 模組),v1.5.0/v1.8.0(39 模組,含 table_ops/layout_analysis/content_roles)收容了也永遠掛不上=尾版律破口;現由橋統一解析,橋缺席則原樣退回直掛=零回歸;批408 同意閘不覆蓋律:六個短令(via-fred/via-revfill/via-etfhist/via-etfuniv/via-chip/via-price)自 批360/368/374/375/394 起每次呼叫都寫死 $env:VIA_NET_CONSENT="YES";$env:VIA_SCRAPE_CONSENT="YES"——覆寫式;但閘二的包內法遵 def_validate_consent 只認 I_ACCEPT_RESPONSIBLE_SCRAPING,字串 "YES" 永遠 BLOCK,且因為每呼必覆寫,操作員就算自己設了正確 token 也會被短令蓋掉=爬蟲道永遠不可達(批407 掛上的 scrape 道等於死路);改法=Set-VIAGateDefaults:只在「該閘未設」時才補預設值,已設者一律尊重(不移除既有預設行為=既有六令零行為變更;亦不代操作員設任何新意圖);批400 八流程並進:via-entry 動詞白名單 +deadends(MDL136 短令死路掃描器)+ via-deadends 別名;收尾閘登錄樞紐任務 closeout(Deck v0134/Manager v0121);批398 操作員令「將 VRN VAL 收個尾吧」:+via-closeout [vrn|vap|all] [--run] [--dir 夾](MDL141 收尾閘:VRN 驗證逐份五段鏈+核對態 DONE|FAIL|PENDING;VAP 逐圖驗;CLOSEOUT_latest.md)+ via-vrnval/via-vapval 別名;批397 雙副本律:工作站實錄 新視窗 profile 點源 Github 母副本(main c14d428c;v0148)→ via-reload 分支感知拉 origin/main=拉不到 PR #30 未併的批381–396 → via-famui/via-console 不認;b381 副本(claude/… v0161)只在該夾啟動的視窗生效 → +via-pin(把 profile 點源行換成本窗副本;--show 只看;只改 profile 一行,兩副本檔案零觸碰)+ via-reload 雙副本提示;批396 工作站實錄修:+via-rebuild(MDL050 多環境隔離重建/旁建零破壞;via-envgov digest「下一指令」指路的 via-rebuild --env 在冊內從未登錄=死路;無參數=--offline 唯讀計畫);via-entry 次序文字 15 步→16 步含 console/handover;批394 工作站實錄修:+via-chip(ENG056 籌碼增量)/via-price(ENG054 價格增量;別名 via-tw-backfill)——ENG081/ENG056 docstring 指路的 via-chip 從未登錄=死路;籌碼止 08-25 根因=日更鏈 ③ 跑時價表尚無 08-26 後交易日(ENG064 回補在後才補齊),現在重跑即補;批393 工作站實錄修:+via-bg 背景引擎進程唯讀一覽(誰持 DuckDB 單寫者鎖一看便知;絕不 Stop-Process;實錄:[FAIL] 庫忙曾指路 via-status 但那是同步頁不是進程表);via-align 基準日律/持鎖者解析在引擎側 ENG081;批392 操作員令「參數最小化;台股除財報外抓全部;國際資訊勾選放右面板;啟動跑一切;VRN TAB2/3/4;起始統一 2023-01-01;VAP 規格與圖;VIA Central Console=超詳細系統狀態如 handover reports 一頁堆疊矩陣可轉 MD 接棒」→ +via-handover(MDL140 接棒狀態台:build|status|md;--open;別名 接棒/接棒LIVE);via-console 頁改 批392 版(整類起始日遮罩輸入/國際資訊右面板勾選/VRN 單鍵啟動/TAB BASIC INFO·SUMMARY·FINANCIAL DATA 核對 VDF 為主/VAP 規格與圖/跑成功?);批391 工作站實錄「start http://127.0.0.1:8765/console 被 VIA_NO_OPEN 抑制;via-align update --apply 撞單寫者鎖 traceback」→ via-open 認 http(s):// URL(只走瀏覽器 exe;別名 LIVE/主控台LIVE=樞紐 /console)+via-console --open 樞紐在線=開 LIVE 網址、離線=開快照頁;ENG081 讓庫律;批390 操作員令「左面板輸入/右面板矩陣;VDF 查詢標的分類細項(總體經濟 PMI/通膨/就業;台股 TWSE/TPEX 可新增代碼);起始日個別可改;財報當季/累計/年度年起迄;DEFAULT 最新;庫狀況;日交易×籌碼數量對齊更新清單;parquet 增量 DuckDB;右側矩陣篩選/大到小;Windows U/I 下拉/勾選/全選/全不選;VRN 資料夾拖曳/啟動/動畫/整體跑況 BASIC INFO/SUMMARY/FINANCIAL DATA;VAP 簡輸入」→ +via-console(MDL139 輸入主控台:build 頁|status|set k=v|argv|run --item;--open 走 via-open 主控台;樞紐在線 http://127.0.0.1:8765/console 可啟動)+via-align(VDF_ENG081 台股日交易×籌碼數量對齊 check|update --apply|status;vdf 境 python)+via-open 別名 主控台/輸入;批388 操作員令「若能跑 vdf vrn 的 u/i」→ via-famui vdf|vrn|vap|all [--open](MDL138 家族 U/I 再生閘:家族境 python 真跑頁面產生器→頁新鮮/零 CDN 判準→FAMILY_UI 索引頁;via-vdfui/via-vrnui 別名;via-open 別名 VDF/VRN/四點/家族);批387 工作站實錄「Windows autocrlf 工作副本 CRLF → Grok CmdMatrix 尾段 via-enter | Out-Null 未去除,載入即 cd 到主 clone」→ 去尾段 regex 容 \r;via-rungate --family vrn 誤判動詞/via_vrn_312 無 duckdb → MDL137 動詞白名單+--approve-install 補庫;批386 Grok 主控台 VRN 契約接回母倉:via-vrn4=一題四點文摘(VRN_ENG080;潛在上漲空間=目標價除權息調整後 vs 最新 adj close;K2 稀釋 EPS n～n+3 YoY;K3/K4 首頁其餘;K5 風險可空;quote-or-abstain 不發明不平均;via_vrn_312 python);批385 工作站實錄「via-reload 在 b381 worktree(claude/… 分支)固定拉 origin/main → ff 失敗 HEAD 8be0780 不動 → via-entry/via-vdfdb/via-vapone/via-rungate 永遠 not recognized;舊版 MDL135 不識 --only-kind 卻靜默照跑全段」→ via-reload 分支感知(當前分支≠main 即拉 origin/<分支>;印分支與 HEAD 前後)+MDL135 旗標白名單誠實停+via-envgov conflicts 衝突明細;批384 操作員令「以此為中央控管將 session_01R2d69oa1AGvnPVwjSUdSv5(VIA系統後續工作;claude/via-system-followup-tz7k9t@c14d428=main=本分支基底)整合完畢;vdf vrn 能跑」→ VDF/VRN/VAP 引擎短令一律以家族境 python 啟動(Get-VIAEnvPython vdf|vrn|vap;境缺=base 退路)+via-rungate(MDL137 能跑閘:家族境 python 真跑引擎自測;--fast/--all;status)+via-py <family> <script> 通用家族啟動器;批383 操作員令「將 river-beam-aurora-acorn 裡面的檔案接回做為整合為一入口」+「單一入口與這個(SYSTEM MANAGER MATRIX v0700)整合;vap 補充;vdf vrn 要弄到實際能跑;vdf 要將資料庫存入;之前有的資料庫整理好抓過的不必再抓」→ +via-entry(唯一入口燈板/plan/roster;--scan/--open/--console)+via-env(→via-envgov 正本)+via-grok(Grok 短令冊;matrix 右側板)+via-webconsole(Grok 網頁主控台 8080;同意閘)+via-vapone(VAP ONE 72 檢)+via-vdfdb(本機三庫整併 DuckDB;抓過不再抓)+via-envpy/Get-VIAEnvPython(家族境 python 解析;功能件住 via_ 境=啟動器指對 python)+載入即接 Grok CmdMatrix(去尾段自動執行;撞名母倉先發先得)+via-open 別名 矩陣/入口;批381 操作員令「依照已成功地建構布局向上新增;最壞還原成原本規劃;base 只放該有的工具;其他放在 via_core 及 via_ 開頭的環境」→ +via-envgov(CGC_MDL135 環境治理統一引擎:全景式分析 base/via_core/via_* → uv 毫秒快篩 → base 該有冊閉包 → 衝突立拔家族路由 → Zero-Hydra 分流拓撲三輪 → LKGC/rollback → 四分區 UI Matrix;預設 run --offline 唯讀;apply --approve 才動;base 移除另 --approve-remove)+via-envgov-auto(Invoke-VIA-EnvGovernance 單一 PowerShell 一貼即用;-Background 非阻塞);批380 操作員令「用一個 PowerShell 完成所有動作 不影響系統健康 不可造成九頭龍風險 20 的加速器 不卡斷」→ via-autorun 四閘版:①20 加速器點亮 ②Hydra 哨兵 H1–H6 先行(H3/H5 阻擋=誠實停) ③全程零跳出零 TTY 等待 ④逾時 kill 不卡斷;批379 操作員在電腦前「自動完成所有動作 不要打開 VS Code 我不知道要怎麼辦」→ +via-autorun 一鍵全自動(雙擊 via-autorun.cmd 即可;結束停窗)+git 永不開編輯器 env;批378 操作員令「不要一直開啟 VS Code,全自動完成一切」→ 載入即全域 VIA_NO_OPEN=1(所有短令零跳出;看頁只走 via-open 瀏覽器道;VIA_OPEN_PAGES=1 可解);批377 +via-lanes 十道並行安全編排(MDL134;Hydra 哨兵)+via-mobile --lanes;批376 +via-productgate 產品資格閘九閘(MDL133);via-mobile 末段 +productgate digest;批375 +via-etfhist 每日持股史深;批374 +via-etfuniv 主動 ETF 宇宙日更;批373 +via-etfrev 主動 ETF×月營收合流;批371 via-ves→MDL132 橋(尾版鏡像+安全種子+雙跑;--raw 直通原件);批370 +via-ves 唯讀 E3 標準化掃描;批368 +via-projects 四專案完工矩陣;+via-revfill 月營收史深;批367 via-reload 同名雙物大寫原件復位;批366 via-mobile 零跳出 VIA_NO_OPEN=1;批362 via-fred 無動詞=run;批360/361 +via-fred/via-vdfarch;批254 立;批260 +via-all;批316 +via-pipeline;批323 +via-accel/via-accel-check;批325 +via-rotation/via-repo-optimize;批327 +via-vapstack;批328 +via-reload;批330 +via-plotlaw;批331 via-reload 先拉齊;批332 +via-system/via-api;批333 +via-master;批335 +via-complete;批336 +via-intake-roster;批337 via-reload 拉齊誠實+產出頁自動讓位;批338 可編輯模板排除;批339 短令清單動態;批340 +via-datahome/via-complete 分離啟動器;批342 +via-six 六流程 Zero-Hydra 編排;批344 via-complete watch/stop;批345 +via-bridge-sweep)
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
# 批408:同意閘不覆蓋律。舊寫法 `$env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"`
# 每次呼叫都覆寫,操作員自設的值永遠被蓋掉;閘二包內法遵只認 I_ACCEPT_RESPONSIBLE_SCRAPING
# (見 functional modules/VRN/webscraping_dualengine_*/VIA_WebScraping_Compliance_SSOT.json 的
# required_consent_token),"YES" 過不了 def_validate_consent → check_url 一律 DENY → 爬蟲道不可達。
# 本函式只在「未設」時補預設值(既有六令行為零變更),已設者尊重;仍不代操作員設任何新意圖。
function global:Set-VIAGateDefaults {
    if (-not $env:VIA_NET_CONSENT)    { $env:VIA_NET_CONSENT = "YES" }
    if (-not $env:VIA_SCRAPE_CONSENT) { $env:VIA_SCRAPE_CONSENT = "YES" }
}
# 批408:閘態一覽(唯讀;絕不印原值,只報是否等於期望 token)
function global:via-gates {
    $g1 = $env:VIA_NET_CONSENT; $g2 = $env:VIA_SCRAPE_CONSENT
    $tok = "I_ACCEPT_RESPONSIBLE_SCRAPING"
    $s1 = if ($g1 -eq "YES") { "OPEN" } elseif ($g1) { "SET(非 YES)" } else { "未設" }
    $s2 = if ($g2 -eq $tok) { "OPEN(期望 token)" } elseif ($g2) { "SET 但非期望值(過不了包內法遵)" } else { "未設" }
    Write-Host ("  [閘一 VIA_NET_CONSENT   ] " + $s1) -ForegroundColor $(if ($g1 -eq "YES") { "Green" } else { "Yellow" })
    Write-Host ("  [閘二 VIA_SCRAPE_CONSENT] " + $s2) -ForegroundColor $(if ($g2 -eq $tok) { "Green" } else { "Yellow" })
    Write-Host ("  [說明] http/headers 兩道只需閘一;scrape 道另需閘二=期望 token。要開爬蟲道請自行親設:") -ForegroundColor DarkGray
    Write-Host ('         $env:VIA_SCRAPE_CONSENT = "' + $tok + '"') -ForegroundColor DarkGray
    Write-Host ("  [律] 本系統永不代操作員設任何同意閘;短令只在該閘未設時補預設,已設者尊重。") -ForegroundColor DarkGray
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
        $t = [regex]::Replace($t, "(?m)^via-enter \| Out-Null[ \t\r]*$", "")   # 批387:CRLF 工作副本容 \r(否則載入即執行 via-enter → cd 主 clone)
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
function global:via-md { & (Get-VIAEnvPython "vrn") (Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG075_DocToMarkdown_v*.py") run @args }
# 批421:兩收容系統升格為 VRN 支援模組(操作員令 REGISTER AND IMPLEMENT ...)。
# via-gle=GenericLayoutEngine v2.1.0 全後端統轄橋(SUP_MDL743;status|probe|route)
#   ——收容件早在庫,但只有 ENG072 私掛且只用一支,30 後端矩陣與多引擎路由全樹無人呼叫。
function global:via-gle { & (Get-VIAEnvPython "vrn") (Get-VIANewest "$VIA\supportive modules\70_VRN_Rules" "SUP_MDL743_GenericLayoutHub_v*.py") @args }
# via-nlp=VIA_NLP_Application_System v1.8.0 統轄橋(SUP_MDL744;status|roster|delta|demo)
#   ——修尾版律破口:ENG072/ENG073 舊版把收容夾寫死 v1.1.0(18 模組),
#     v1.5.0/v1.8.0(39 模組:table_ops/layout_analysis/content_roles…)收容了也掛不上。
function global:via-nlp { & (Get-VIAEnvPython "vrn") (Get-VIANewest "$VIA\supportive modules\70_VRN_Rules" "SUP_MDL744_NLPApplicationHub_v*.py") @args }
# 批423(操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」):via-allgreen=統包全流程尾版啟動器。
# 為什麼要新登錄一個名:工作站的 via-go 是**操作員自己放在 PATH 上的檔**(批358 已記
# 「同名=九頭龍→讓位」,所以短令冊永遠不定義 via-go),而它指的是寫死的
# Invoke-VIA-AllGreen-v0100.ps1——也就是說 v0101 的卡斷修**傳不到操作員手上**。
# 倉庫這邊改用尾版律 glob 起 Invoke-VIA-AllGreen-v*.ps1,新版一落地就自動生效。
# v0101 修的兩條:①子行程輸出不再被 Out-String 吞(邊跑邊轉播)
#                 ②$StageTimeoutSec 真正接線(v0100 宣告了卻整檔沒用過=永遠等下去)
function global:via-allgreen { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest "$VIA\supportive modules\registry" "Invoke-VIA-AllGreen-v*.ps1") @args }
Set-Alias -Name 統包 -Value via-allgreen -Scope Global -Force
Set-Alias -Name 版面橋 -Value via-gle -Scope Global -Force
Set-Alias -Name 語意橋 -Value via-nlp -Scope Global -Force
function global:via-prompt { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL109_PromptManager_v*.py") @args }
function global:via-analysis { & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG068_ETFConsensusAnalysis_v*.py") run; & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG069_RevenueConsensusAnalysis_v*.py") run }
function global:via-manager { python (Get-VIANewest "$VIA" "VIA_SYSTEM_MANAGER_v*.py") @args }
function global:via-rootcheck { & cmd /c "$VIA\VIA-ROOTCHECK.cmd" }
function global:via-tower-reset { & cmd /c "$VIA\VIA-TOWER-RESET.cmd" }
function global:via-ssot { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL115_SSOTRegexDict_v*.py") @args }
function global:via-register { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL113_UnifiedRegistry_v*.py") @args }
function global:via-health { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL114_CommandCenterBridge_v*.py") run }
function global:via-tpn { & (Get-VIAEnvPython "vap") (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG011_TemplateRegistry_v*.py") @args }
function global:via-psrepair { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-PSRepair-v*.ps1") @args }
function global:via-all { pwsh -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-All-v*.ps1") @args }
# 批323:加速器啟動報告(SUP_MDL737 尾版 --activate/--libs)+覆蓋×啟動稽核(CGC_MDL117)
function global:via-accel { python (Get-VIANewest "$VIA\supportive modules" "SUP_MDL737_SuperAccelModule_v*.py") $(if ($args) { $args } else { "--activate" }) }
function global:via-accel-check { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL117_AccelCoverage_v*.py") run }
# 批325:故事族群輪動橋接(ENG072 尾版;run 預設,可帶 export/preflight/--pkgtest)+repo 衛生一鍵(只宜工作站)
function global:via-rotation { & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG072_StoryRotationBridge_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-repo-optimize { $ps = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }; & $ps -NoProfile -ExecutionPolicy Bypass -File (Get-VIANewest $VIA "Invoke-VIA-RepoOptimizer-v*.ps1") @args }
# 批327:VAP Seaborn 垂直圖組橋接(ENG015 尾版;預設 stock 2330;可帶 stock <代碼> | heatmap | --selftest)
function global:via-vapstack { & (Get-VIAEnvPython "vap") (Get-VIANewest "$VIA\functional modules\VAP\engine" "VAP_ENG015_SeabornStackBridge_v*.py") $(if ($args) { $args } else { @("stock", "2330") }) }
# 批328 實錄:拉齊後既開視窗仍是舊短令冊(profile 只在開窗時點源)→via-reload=本窗重點源尾版冊,免開新視窗
# 批331 實錄:via-reload 只重載磁碟冊,未拉齊=仍舊版→先 fetch+ff-only 再重載(分流不動;VIA-ALL 才對齊)
# 批337 實錄:工作站 pull 被本地再生頁(VIA_UI_Portal)差異擋下,而 via-reload 靜默 2>$null=假拉齊(HEAD 不動仍印「已拉齊」)。
# 改:①fetch ②ui_support 產出頁本地差異=再生物→自動還原讓位(git checkout;誠實印件數)③ff-only 失敗=印 git 原話+阻擋檔清單(不 reset 不 stash 其他檔)④重載尾版冊+印 HEAD 前後
function global:via-reload {
    $root = Split-Path $VIA -Parent
    $before = git -C $root rev-parse --short HEAD
    # 批385:分支感知拉齊——當前分支=main 拉 origin/main;否則(worktree 在 claude/… 等分支)拉 origin/<當前分支>;detached=main
    $branch = (git -C $root rev-parse --abbrev-ref HEAD 2>$null); if (-not $branch -or $branch -eq "HEAD") { $branch = "main" }
    $target = "origin/" + $branch
    git -C $root fetch -q origin $branch 2>$null
    # 批348 再生物冊:引擎每次自測/再生會回寫的追蹤檔=產物非正本→拉齊前自動還原讓位(誠實印件數);台帳 VIA_AutoCode_Registry 永不還原(append-only)
    $regen = "^VeritasIntelligenceAnalytics/(supportive modules/ui_support/.*\.html|supportive modules/registry/VIA_(Engine_Consolidation_Register|Engine_Contract|SSOT_RegexDict|Schema_Registry|Tool_Escalation_Ladder|Unified_Register|IndustryUnifiedMap|Problem_Ledger|NetModules_Integration_Register|AccelModules_Integration_Register|VDFArchitecture|ProjectCompletion|ProductGate|ParallelLanes)_v\d+\.json|VIA-TOWER-RESET\.cmd|functional modules/VAP/references/intake/VAP_v025_Complete_Package/(output|spec)/.*\.json)$"
    $gen = @(git -C $root status --porcelain 2>$null | Where-Object { $_.Substring(0,2) -match "M" } | ForEach-Object { $_.Substring(3).Trim('"') } | Where-Object { $_ -match $regen -and $_ -notmatch "EditableTemplate" -and $_ -notmatch "VIA_AutoCode_Registry" })  # 批338:可編輯模板=操作員手改件,永不還原
    if ($gen.Count -gt 0) { git -C $root checkout -q -- $gen 2>$null; Write-Host ("  [VIA] 產出頁本地差異 " + $gen.Count + " 件=再生物,已還原讓位(誠實):" + ($gen -join ", ")) -ForegroundColor DarkYellow }
    $out = (git -C $root merge --ff-only $target 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        # 批347:阻擋檔=本地未提交→自動 stash(含未追蹤;記名)→ff-only→pop(VIA.ps1 Sync-Repo 同律;pop 衝突=stash 留存誠實印)
        $blk = @(git -C $root status --porcelain 2>$null)
        if ($blk.Count -gt 0 -and $out -match "overwritten|local changes|Not possible to fast-forward|Diverging") {
            $stMsg = "via-reload " + (Get-Date -Format "yyyyMMdd_HHmmss")
            git -C $root stash push --include-untracked -q -m $stMsg 2>$null
            Write-Host ("  [VIA] 阻擋檔 " + $blk.Count + " 件已 stash(" + $stMsg + "),拉齊後自動還原") -ForegroundColor DarkYellow
            $out = (git -C $root merge --ff-only $target 2>&1 | Out-String).Trim()
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
    Write-Host ("  [VIA] 短令冊重載:" + (Split-Path $r -Leaf) + " · 分支 " + $branch + "(拉 " + $target + ")· HEAD " + $before + " → " + $after + $(if ($before -eq $after -and $LASTEXITCODE -ne 0) { "(未拉齊;看上方 git 原話)" } else { "" })) -ForegroundColor Green
    $pinDir = Get-VIAPinnedDir; if ($pinDir -and ($pinDir -ne $VIA)) { Write-Host ("  [VIA] 雙副本:新視窗預設(profile)=" + $pinDir + " ≠ 本窗 " + $VIA + " → 要讓新視窗也用本副本:via-pin(批397;只改 profile 一行)") -ForegroundColor DarkYellow }
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
function global:via-fred { Set-VIAGateDefaults; $a = @($args); if (-not ($a | Where-Object { $_ -in @("run", "status", "lamps", "help") })) { $a = @("run") + $a }; & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG074_FredMacroSSOT_v*.py") @a }
# 批368:月營收全市場史深回補(ENG075;MOPS t21sc03 上市/上櫃 國內/KY 月檔 2023-01→ 從新往舊;Big5;只增 anti-join;checkpoint;親跑=同意);via-revfill [run] [--since 2023-01] [--workers 3] [--max-months N] | status;(名 via-rev 讓位另線工作站別名=先發先得)
function global:via-revfill { Set-VIAGateDefaults; & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG075_MonthlyRevenueBackfill_v*.py") $(if ($args) { $args } else { "run" }) }
# 批371:VES 橋(MDL132)=尾版鏡像(史版不當多頭)→第 1 跑→安全種子決策(VIA 動詞冊/橋塊 REJECT/selftest 群 REJECT;append-only)→第 2 跑確定性套用;唯讀;--apply 永不經短令;via-ves [--root <相對子樹>] [--no-seed] [--single];via-ves --raw <VES 原生參數…>(直通收容原件,如 --slice <碼>)
function global:via-ves { if ($args -contains "--apply") { Write-Host "  [via-ves] --apply 不經短令(操作員親打 python <VES> --apply --token <hint>;Zero-Hydra 律)" -ForegroundColor Yellow; return }; if ($args -contains "--raw") { $ves = Get-VIANewest "$VIA\supportive modules\references\intake\VIA_VES_EngineStandardizer_b*" "via_engine_standardizer.py"; $a = @($args | Where-Object { $_ -ne "--raw" }); if (-not ($a -contains "--root")) { $a = @("--root", "$VIA\VIA_Reports\ves\tails_tree") + $a }; if (-not ($a -contains "--out")) { $a = @("--out", "$VIA\VIA_Reports\ves\out") + $a }; python $ves --no-ml-probe @a; return }; python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL132_VesBridge_v*.py") run @args }
# 批375:主動 ETF 每日持股史深覆蓋+缺口回補(ENG078;IPO 起應有交易日 vs 快照;車道冊 VIA_ActiveETF_HistoryLanes VERIFIED 才呼;缺源=NO_SOURCE 誠實;親跑=同意);via-etfhist [daily [--offline] [--max-days N] | backfill | status]
function global:via-etfhist { Set-VIAGateDefaults; & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG078_ActiveETFHoldingsHistory_v*.py") $(if ($args) { $args } else { "daily" }) }
# 批374:主動 ETF 宇宙日更(ENG077;A 碼律 ^\d{5}A$ + 國內成分揭露律;TWSE 官方冊→etf_book 後備→既有聯集只增;寫 ENG051 SSOT csv;親跑=同意);via-etfuniv [run [--offline] | status]
function global:via-etfuniv { Set-VIAGateDefaults; & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG077_ActiveETFUniverse_v*.py") $(if ($args) { $args } else { "run" }) }
# 批373:主動 ETF 持股×月營收動能(ENG076;兩專案合流層;零網路;加權 yoy/重疊榜;頁 VIA_UI_ETFRevenueMomentum);via-etfrev [run|status]
function global:via-etfrev { & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG076_ETFRevenueMomentum_v*.py") $(if ($args) { $args } else { "run" }) }
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
function global:via-open { $alias = @{ "產品" = "VIA_UI_ProductGate"; "竣工" = "VIA_UI_ProjectCompletion"; "架構" = "VIA_UI_VDFArchitecture"; "道" = "VIA_UI_ParallelLanes"; "總控" = "VIA_UI_MasterControl"; "整" = "VIA_UI_Consolidated"; "系統" = "VIA_UI_SystemConsole"; "矩陣" = "VIA_MasterControl_Matrix"; "入口" = ("" + $VIA + "\VIA_Reports\entry\ENTRY_latest.html"); "VDF" = "VIA_UI_VDFArchitecture"; "VRN" = "VIA_UI_VRNControlTower"; "四點" = ("" + $VIA + "\VIA_Reports\vrn\four_point\DIGEST_latest.html"); "家族" = ("" + $VIA + "\VIA_Reports\ui\FAMILY_UI_latest.html"); "主控台" = "VIA_UI_InputConsole"; "輸入" = "VIA_UI_InputConsole"; "LIVE" = "http://127.0.0.1:8765/console"; "主控台LIVE" = "http://127.0.0.1:8765/console"; "總控LIVE" = "http://127.0.0.1:8765/master"; "接棒" = "VIA_UI_Handover"; "接棒LIVE" = "http://127.0.0.1:8765/handover" }; $q = if ($args.Count -gt 0) { "" + $args[0] } else { "VIA_UI_ProductGate" }; if ($alias.ContainsKey($q)) { $q = $alias[$q] }; if ($q -match '^https?://') { $bx0 = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe", "$env:ProgramFiles\Mozilla Firefox\firefox.exe") | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1; if ($bx0) { Start-Process -FilePath $bx0 -ArgumentList $q; Write-Host ("  [via-open] " + (Split-Path $bx0 -Leaf) + " ← " + $q + "(樞紐 LIVE 道;批391)") -ForegroundColor Green } else { Write-Host ("  [via-open] 未找到瀏覽器 exe;請手動以瀏覽器開:" + $q) -ForegroundColor Yellow }; return }; $ui = Join-Path $VIA "supportive modules\ui_support"; $f = if (Test-Path -LiteralPath $q) { Get-Item -LiteralPath $q } else { Get-ChildItem -LiteralPath $ui -Filter "*.html" | Where-Object { $_.Name -like ("*" + $q + "*") } | Sort-Object Name | Select-Object -Last 1 }; if (-not $f) { Write-Host ("  [via-open] 找不到頁:" + $q + "(ui_support 內 *.html 片段或完整路徑)") -ForegroundColor Yellow; return }; $bx = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe", "$env:ProgramFiles\Mozilla Firefox\firefox.exe") | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1; if ($bx) { Start-Process -FilePath $bx -ArgumentList ("`"" + $f.FullName + "`""); Write-Host ("  [via-open] " + (Split-Path $bx -Leaf) + " ← " + $f.Name) -ForegroundColor Green } else { Write-Host ("  [via-open] 未找到瀏覽器 exe;請手動以瀏覽器開:" + $f.FullName) -ForegroundColor Yellow } }
# 批377:十道並行安全編排(MDL134;FixAll 步冊→資源鏈 DAG:同庫序跑/鏈間並行≤10;Hydra 哨兵 H1 同名/H2 同版/H3 進程雙頭(鎖)/H4 單寫者/H5 尾版;離線 net 步 SKIP;零 force);via-lanes [plan | run [--workers N] [--only a,b] [--dry] | digest];via-mobile --lanes=補齊鏈改並行
# 批381:via-vdffetch [年份]=單一指令抓該年以後全部 VDF 資料(預設 2023)。四段:①年份旗標 VIA_HIST_SINCE=<年>-01-01 + VIA_REV_SINCE=<年>-01(MDL125 尾版步冊 hist_2023/revenue_backfill 直讀)
#   ②20 加速器點亮 ③Hydra 哨兵 H1–H6(via-lanes plan;H3 進程雙頭/H5 尾版律 FAIL=誠實停不跑)④十一步資料鏈十道並行(同庫序跑=單寫者律;net 步雙同意閘;逾時 kill 不卡斷;零跳出;FRED 鑰缺=SKIP 印指令)→ lanes digest + projects digest
#   用法:via-vdffetch(=2023 起)/ via-vdffetch 2020 / via-vdffetch 2023 --dry(只印不抓)
function global:via-vdffetch {
    $y = if ($args.Count -gt 0 -and ("" + $args[0]) -match "^\d{4}$") { "" + $args[0] } else { "2023" }
    $rest = @($args | Where-Object { ("" + $_) -ne $y })
    $env:VIA_HIST_SINCE = "$y-01-01"; $env:VIA_REV_SINCE = "$y-01"
    $env:VIA_NO_OPEN = "1"; $env:VIA_FRED_PROMPT = "0"; $env:GIT_EDITOR = "true"; $env:PYTHONUTF8 = "1"
    $env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"   # 操作員親打本令=同意閘開(紅線:不代設於他處)
    Write-Host ("=== [via-vdffetch] VDF 史深全抓 " + $y + "-01-01 → 今(單一 PowerShell;零跳出;不卡斷)===") -ForegroundColor Cyan
    Write-Host "--- (1) 20 加速器點亮 ---" -ForegroundColor Cyan; try { via-accel --activate } catch { Write-Host ("  [加速器] " + $_.Exception.Message) -ForegroundColor Yellow }
    Write-Host "--- (2) 九頭龍哨兵 H1-H6(唯讀)---" -ForegroundColor Cyan; $plan = (via-lanes plan 2>&1 | Out-String); Write-Host $plan
    if ($plan -match "H3 FAIL|H5 FAIL") { Write-Host "=== [via-vdffetch] 九頭龍風險(見上 H3/H5)=誠實停;關閉另一條在跑的鏈或修尾版後重試 ===" -ForegroundColor Red; return }
    Write-Host ("--- (3) 資料鏈十道並行(hist_2023 " + $y + "→今 / global / fred / 月營收 / 主動 ETF / 共識 / 合流)---") -ForegroundColor Cyan
    via-lanes run --only datahome,hist_2023,global,fred,revenue_backfill,etf_universe,etf_fetch,etf_history,consensus,revenue_consensus,etf_revenue @rest
    Write-Host "--- (4) 存證 ---" -ForegroundColor Cyan; via-lanes digest; via-projects digest
    Write-Host "=== [via-vdffetch] 畢;看頁:via-open 架構 / via-open 竣工 ===" -ForegroundColor Cyan }
function global:via-lanes { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL134_ParallelLanes_v*.py") $(if ($args) { $args } else { "plan" }) }
# 批376:產品資格閘(MDL133;九閘 G1 矩陣存證/G2 短令↔梭/G3 樞紐任務/G4 頁衛生/G5 再生物讓位/G6 鑰匙守衛/G7 引擎尾版/G8 短令在位/G9 用法;QUALIFIED/CONDITIONAL/NOT_QUALIFIED 永不假綠);via-productgate [build --open | digest | --json]
function global:via-productgate { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL133_ProductGate_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批368:四專案完工矩陣(MDL131;VDF/VRN/主動 ETF/月營收 × grid 存證 × DuckDB 深度 × 任務/頁/令;RYG+下一指令;八段循環證據);via-projects [build --open | digest]
function global:via-projects { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL131_ProjectCompletion_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
# 批360:VDF 資料架構(ENG073;SSOT 12 類→現役表/引擎/車道對映;DuckDB 盤點;--optimize dry-run 只增不減;--go 才寫;頁 VIA_UI_VDFArchitecture);via-vdfarch [build --open | --optimize [--go]]
function global:via-vdfarch { & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG073_DataArchitecture_v*.py") $(if ($args) { $args } else { @("build", "--open") }) }
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
function global:via-entry { $a = @($args); if ($a.Count -gt 0 -and ($a[0] -in @("plan", "roster", "status", "envpy", "deadends"))) { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL136_EntryBridge_v*.py") @a; return }
    Set-Location -LiteralPath $VIA; $env:VIA_ROOT = $VIA; $env:PYTHONNOUSERSITE = "1"; $env:PYTHONUTF8 = "1"; if (-not $env:VIA_NET) { $env:VIA_NET = "0" }
    Write-Host ("=== [via-entry] VIA 唯一入口(母倉 " + $VIA + ";Grok 主控台=via-webconsole 子入口;LIVE 預設關 VIA_NET=" + $env:VIA_NET + ";零跳出 VIA_NO_OPEN=" + $env:VIA_NO_OPEN + ")===") -ForegroundColor Cyan
    foreach ($f in @("vdf", "vrn", "vap")) { $p = Get-VIAEnvPython $f; Write-Host ("  [境] " + $f + " → " + $p + $(if ($p -eq "python") { "(base 退路;功能件境未見)" } else { "" })) -ForegroundColor $(if ($p -eq "python") { "Yellow" } else { "Green" }) }
    python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL136_EntryBridge_v*.py") status
    if ($a -contains "--scan") { Write-Host "--- [via-entry] 環境治理全景(唯讀)---" -ForegroundColor Cyan; via-envgov run --offline }
    if ($a -contains "--open") { via-open 矩陣 }
    if ($a -contains "--console") { via-webconsole --background }
    Write-Host "  [via-entry] 次序:via-entry plan(16 步)· via-envgov · via-envgov apply --approve --only-kind REPAIR_BASE · via-rungate(能跑閘)· via-console --open(輸入主控台)· via-handover --open(接棒台)· via-famui vdf,vrn --open(家族 U/I)· via-vdfdb scan · via-vapone · via-open 矩陣 · via-webconsole" -ForegroundColor Cyan }
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
# 批384:via-rungate=VDF/VRN/VAP 能跑閘(MDL137):家族境 python 逐庫 import + SelftestGrid 家族站真跑(--fast 每族 3 站;預設 8;--all 全站;--family vdf,vrn,vap;status 看上次);via-py <family> <script.py> [args]=通用家族啟動器
function global:via-rungate { python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL137_RunGate_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-py { if ($args.Count -lt 2) { Write-Host "  用法:via-py <vdf|vrn|vap|core|ocr|table> <script.py> [args](家族境 python 啟動;境缺=base 退路)" -ForegroundColor Yellow; return }; $py = Get-VIAEnvPython ("" + $args[0]); Write-Host ("  [via-py] " + $args[0] + " → " + $py) -ForegroundColor DarkCyan; & $py @($args | Select-Object -Skip 1) }
# 批386:via-vrn4=研報一題四點文摘+潛在上漲空間(VRN_ENG080;目標價除權息同口徑後向因子鏈;最新 adj close;quote-or-abstain);無參數=run;show <ticker|report_file>;--ticker/--limit
function global:via-vrn4 { $py = Get-VIAEnvPython "vrn"; & $py (Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG080_FourPointDigest_v*.py") $(if ($args) { $args } else { "run" }) }
# 批388:via-famui=家族 U/I 再生閘(MDL138):以家族境 python 真跑 VDF/VRN/VAP 頁面產生器→頁新鮮/零 CDN 判準→索引 FAMILY_UI_latest.html;--open 只走 via-open 瀏覽器道;--no-build 只驗頁;via-vdfui/via-vrnui 別名
function global:via-famui { $a = @($args); $o = ($a -contains "--open"); $rest = @($a | Where-Object { $_ -ne "--open" -and $_ -notin @("vdf", "vrn", "vap", "all") }); $fam = @($a | Where-Object { $_ -in @("vdf", "vrn", "vap", "all") } | Select-Object -First 1); $fam = if ($fam) { "" + $fam } else { "all" }; python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL138_FamilyUI_v*.py") run --family $fam @rest; if ($o) { via-open 家族 } }
function global:via-vdfui { via-famui vdf @args }
function global:via-vrnui { via-famui vrn @args }
# 批390:via-console=輸入主控台(MDL139 左輸入/右矩陣;零 CDN):無參數=build 頁;status [--json];set k=v…(tw-add=2330:TWSE start=<item>:YYYY-MM-DD|latest days=<item>:N macro-cats=Business,Prices fin-period=累計 fin-from=2022 vrn-dir=<夾> vap-code=2330…);argv --item <id> k=v;run --item <id> k=v [--dry];--open=via-open 主控台(樞紐在線時開 http://127.0.0.1:8765/console 才可按啟動;file:// 頁=SNAPSHOT 只看並印等價短令)
function global:via-console { $a = @($args); $o = ($a -contains "--open"); $rest = @($a | Where-Object { $_ -ne "--open" }); python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL139_InputConsole_v*.py") @rest; if ($o) { $live = $false; try { $tc = New-Object System.Net.Sockets.TcpClient; $ar = $tc.BeginConnect("127.0.0.1", 8765, $null, $null); $live = $ar.AsyncWaitHandle.WaitOne(400) -and $tc.Connected; $tc.Close() } catch { $live = $false }; if ($live) { via-open LIVE } else { Write-Host "  [via-console] 樞紐 8765 未在線=開快照頁(只看;要按啟動:先 via 帶起樞紐,再 via-console --open 或 via-open LIVE)" -ForegroundColor Yellow; via-open 主控台 } } }
# 批390:via-align=台股每日交易資訊×籌碼 數量對齊與股票清單更新(VDF_ENG081;vdf 境 python):check [--days N](逐日核對 ALIGNED/PARTIAL/MISALIGNED;差集清單)| update [--apply](最新日 價∪籌碼 ∩ 冊 → tw_universe anti-join 只增 + parquet 增量)| status
# 批392:via-handover=接棒狀態台(MDL140):超詳細系統狀態分門別類堆疊矩陣一頁(git/PR/環境治理/能跑閘/家族 U/I/樞紐任務/庫狀況/對齊/本機三庫/VRN 跑況/VAP 產出/日更鏈/候操作員/次步)+ HANDOVER_latest.md(可轉 MD 接棒);無參數=build;status|md;--open=樞紐在線開 LIVE /handover 否則快照頁
function global:via-handover { $a = @($args); $o = ($a -contains "--open"); $rest = @($a | Where-Object { $_ -ne "--open" }); python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL140_HandoverConsole_v*.py") @rest; if ($o) { $live = $false; try { $tc = New-Object System.Net.Sockets.TcpClient; $ar = $tc.BeginConnect("127.0.0.1", 8765, $null, $null); $live = $ar.AsyncWaitHandle.WaitOne(400) -and $tc.Connected; $tc.Close() } catch { $live = $false }; if ($live) { via-open 接棒LIVE } else { via-open 接棒 } } }
function global:via-align { & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG081_UniverseAlign_v*.py") $(if ($args) { $args } else { "check" }) }
# 批393:via-bg=背景引擎進程一覽(唯讀;工作站實錄:via-align 撞 DuckDB 單寫者鎖時 [FAIL] 句指路「via-status」,但 via-status 開的是同步頁不是進程表)。
#   Get-CimInstance Win32_Process 篩 python/pwsh/powershell 命令列含 VIA 引擎/boot 鏈/樞紐 → 列 PID/已跑分鐘/引擎+動詞;絕不 Stop-Process(只看;等其跑完再 via-align)。
function global:via-bg {
    $rx = 'VeritasIntelligenceAnalytics|via_boot_update|VDF_ENG|VRN_ENG|VAP_ENG|CGC_MDL|SUP_MDL|VIA_SYSTEM_MANAGER|VIA\.ps1'
    $eng = '((?:VDF|VRN|VAP|CGC|SUP)_(?:ENG|MDL)\d{3}_[A-Za-z0-9]+(?:_v\d{4})?\.py|via_boot_update\.(?:ps1|sh)|VIA\.ps1|VIA_SYSTEM_MANAGER_v\d{4}\.py)'
    $rows = @()
    try {
        Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -and ($_.Name -match '^(python|pwsh|powershell)') -and ($_.CommandLine -match $rx) } | ForEach-Object {
            $cl = $_.CommandLine
            $lab = $cl.Substring(0, [Math]::Min(70, $cl.Length))
            if ($cl -match $eng) {
                $m = $Matches[1]
                $tail = @(($cl.Substring($cl.IndexOf($m) + $m.Length)).Trim().Trim('"').Split(' ') | Where-Object { $_ })
                if ($tail.Count -gt 0 -and -not $tail[0].StartsWith('-')) { $lab = "$m $($tail[0])" } else { $lab = $m }
            }
            $min = if ($_.CreationDate) { [int]((Get-Date) - $_.CreationDate).TotalMinutes } else { -1 }
            $rows += [pscustomobject]@{ PID = $_.ProcessId; 分鐘 = $min; 程式 = $_.Name; 引擎 = $lab }
        }
    } catch { Write-Host ("  [via-bg] 無法列進程:" + $_.Exception.Message) -ForegroundColor Yellow; return }
    if ($rows.Count -eq 0) { Write-Host "  [via-bg] 無 VIA 背景引擎進程(DuckDB 單寫者鎖應已釋放;可 via-align check / via-align update --apply)" -ForegroundColor Green; return }
    Write-Host ("  [via-bg] VIA 背景引擎進程 " + $rows.Count + " 個(唯讀一覽;持 DuckDB 單寫者鎖者多為 ENG064 回補/boot 日更鏈;等其跑完再 via-align;絕不 Stop-Process)") -ForegroundColor Cyan
    $rows | Sort-Object 分鐘 -Descending | Format-Table -AutoSize | Out-String -Width 160 | Write-Host
}
# 批394:via-chip=籌碼增量(VDF_ENG056:run [--days N] | --derive | --status);via-price=價格增量(VDF_ENG054 v0101 增量律:依各標的 MAX(date) 只抓缺口;run [--limit N] [--full] | --status);
#   via-tw-backfill=ENG054 docstring 原名別名。同意閘同 via-fred(VIA_NET_CONSENT/VIA_SCRAPE_CONSENT=YES);以 via_vdf_312 python 啟動;撞單寫者鎖=引擎自身庫鎖律誠實停。
function global:via-chip { Set-VIAGateDefaults; & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG056_ChipBackfill_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-price { Set-VIAGateDefaults; & (Get-VIAEnvPython "vdf") (Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG054_TWDailyBackfill_v*.py") $(if ($args) { $args } else { "run" }) }
function global:via-tw-backfill { via-price @args }
# 批398:via-closeout=收尾閘 MDL141(VRN 驗證收尾 VAL:報告夾每一份 收件→首頁→入庫→財報頁→四點 + TAB2/TAB4 核對態 → DONE|FAIL|PENDING;VAP 產出收尾:逐圖驗 SVG/PNG/HTML/PDF+零 CDN+台帳)
#   [vrn|vap|all] [--run](先經 MDL139 run --item 跑鏈再收尾)[--dir 報告夾] [--json];落 VIA_Reports/closeout/CLOSEOUT_latest.md/.json(接棒台讀);以 via_vrn_312 python 啟動(duckdb 在);--open=以瀏覽器開 MD 所在夾外之 Handover(接棒台含收尾矩陣)。
function global:via-closeout { $a = @($args); $o = ($a -contains "--open"); $rest = @($a | Where-Object { $_ -ne "--open" }); & (Get-VIAEnvPython "vrn") (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL141_ClosingGate_v*.py") @rest; if ($o) { via-handover --open } }
function global:via-vrnval { via-closeout vrn @args }
function global:via-vapval { via-closeout vap @args }
# 批400:via-deadends=短令死路掃描器(MDL136 deadends):掃引擎 docstring/[FAIL] 句/docs/README 內 via-* 令,對照短令冊+梭;未登錄=死路(批394 via-chip/批396 via-rebuild 同類);落 VIA_Reports/entry/DEADENDS_latest.json;--json/--quiet
function global:via-deadends { via-entry deadends @args }
# 批397 雙副本律:via-pin=把 $PROFILE 的 VIA 點源行換成「本窗副本」($VIA=本檔所在 VeritasIntelligenceAnalytics 夾),讓以後每個新視窗預設載本副本尾版短令冊;
#   --show 只看(本窗副本 vs profile 預設副本,各印分支/HEAD);只改 profile 一行,兩副本檔案零觸碰;換回=到另一副本的視窗再 via-pin。pwsh 與 Windows PowerShell 各有 $PROFILE,各自 via-pin 一次。
function global:Get-VIAPinnedDir { try { if (Test-Path -LiteralPath $PROFILE) { $m = Select-String -LiteralPath $PROFILE -Pattern '\. \(Get-ChildItem "([^"]+)\\Register-VIA-Commands-v\*\.ps1"' | Select-Object -First 1; if ($m) { return $m.Matches[0].Groups[1].Value } } } catch { }; return "" }
function global:via-pin {
    $pinned = Get-VIAPinnedDir
    $rootH = Split-Path $VIA -Parent
    $bH = (git -C $rootH rev-parse --abbrev-ref HEAD 2>$null); $hH = (git -C $rootH rev-parse --short HEAD 2>$null)
    Write-Host ("  [via-pin] 本窗副本:" + $VIA + "(" + $bH + " " + $hH + ";" + (Split-Path $global:VIARegisterPath -Leaf) + ")")
    if ($pinned) { $rootP = Split-Path $pinned -Parent; $bP = (git -C $rootP rev-parse --abbrev-ref HEAD 2>$null); $hP = (git -C $rootP rev-parse --short HEAD 2>$null); Write-Host ("  [via-pin] 新視窗預設(profile " + $PROFILE + "):" + $pinned + "(" + $bP + " " + $hP + ")") } else { Write-Host ("  [via-pin] 新視窗預設(profile " + $PROFILE + "):(無 VIA 點源行)") }
    if ($args -contains "--show") { return }
    if ($pinned -eq $VIA) { Write-Host "  [via-pin] 已是本副本;無事" -ForegroundColor Green; return }
    $line = '. (Get-ChildItem "' + $VIA + '\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName'
    try {
        if (!(Test-Path -LiteralPath $PROFILE)) { New-Item -ItemType File -Force $PROFILE | Out-Null }
        if ($pinned) {
            $rx = '^\. \(Get-ChildItem "[^"]+\\Register-VIA-Commands-v\*\.ps1"'
            $new = @(Get-Content -LiteralPath $PROFILE | ForEach-Object { if ($_ -match $rx) { $line } else { $_ } })
            Set-Content -LiteralPath $PROFILE -Value $new -Encoding UTF8
        } else {
            @("", "# [VIA:PROFILE:v0201] 點源尾版(pull 即最新;永久免重貼)", $line) | Add-Content -Path $PROFILE -Encoding UTF8
        }
        Write-Host ("  [via-pin] 新視窗預設已換 → " + $VIA + "(舊:" + $(if ($pinned) { $pinned } else { "無" }) + ";只改 profile 一行;兩副本檔案零觸碰;換回=到另一副本的視窗 via-pin)") -ForegroundColor Green
    } catch { Write-Host ("  [via-pin] profile 寫入失敗(誠實):" + $_.Exception.Message) -ForegroundColor Yellow }
}
# 批396:via-rebuild=多環境隔離重建計畫引擎 MDL050(via-envgov digest「下一指令」指路的 via-rebuild --env/--split;旁建零破壞=原境不動,驗綠後切換候裁)。
#   無參數=--offline(只 ①~④+⑦ 唯讀計畫;零網路);via-rebuild --env <境>=只治理單一環境(② 起需網路;無網路段誠實 NOT_RUN);--selftest 十四檢。base python(MDL050 自管 uv)。
#   MDL050 尾版旗標只認 --env/--roots/--rounds/--offline/--selftest;MDL135 提案的 --split <境>(拆分)尚無=改以 --env <境> --offline 唯讀計畫並印明(不讓引擎靜默跑全境)。
function global:via-rebuild { $a = @($args); if ($a -contains "--split") { $i = [Array]::IndexOf($a, "--split"); $e0 = if ($i -ge 0 -and $i + 1 -lt $a.Count) { "" + $a[$i + 1] } else { "" }; Write-Host ("  [via-rebuild] MDL050 尾版尚無 --split(拆分候裁;MDL135 提案)→ 改以 --env " + $e0 + " --offline 唯讀計畫(原境不動)") -ForegroundColor Yellow; $a = @("--env", $e0, "--offline") }; python (Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL050_EnvRebuild_v*.py") $(if ($a) { $a } else { @("--offline") }) }
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

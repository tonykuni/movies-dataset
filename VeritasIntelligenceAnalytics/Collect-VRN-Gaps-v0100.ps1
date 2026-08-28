# Collect-VRN-Gaps-v0100.ps1 — 券商報告缺件搜集器(批232;操作員令
# 「解決所有問題 缺件在 C:\Users\tonyk\Downloads 搜尋看看」)
# 機制:對帳 NO_EXTRACTION 64 件名冊(嵌入)→ Downloads 遞迴搜尋
#   (精確名優先;正規化模糊後備:去空白括號比對)→ 複製入
#   input_reports(.gitignore 紅線:原件永不入 git;僅本機)
# 誠實三態:FOUND(複製)/ALREADY(已在)/MISSING(誠實列缺)
param([string]$SearchRoot = "$env:USERPROFILE\Downloads")
$dest = Join-Path $PSScriptRoot "functional modules\VRN\input_reports"
New-Item -ItemType Directory -Force $dest | Out-Null
$GAPS = @(
  "MS-Memory 20251204.pdf",
  "晶心科(6533,N,中立)-CTBC251208.pdf",
  "JP-3653 20251003.pdf",
  "MS-3665 20251202.pdf",
  "華南投顧-2606-裕民-1141202.pdf",
  "凱基期貨晨間解盤20251205.pdf",
  "凱基投顧_6147 頎邦_劉宇程_20260519.pdf",
  "凱基投顧_鋼鐵產業_劉昃恩_20260518.pdf",
  "MS-ABF 20260518.pdf",
  "MS-3661 20251203.pdf",
  "20251128兆豐訪談速報-神達(3706).pdf",
  "Citi-3231 20250604.pdf",
  "6933_AMAX-KY_個股介紹報告.pdf",
  "GS-2383 20260519.pdf",
  "20251204兆豐個股報告-志強-KY(6768).pdf",
  "GS-3706 20251130.pdf",
  "瑞基(4171,NR_未評等)-CTBC251208.pdf",
  "20260519兆豐個股報告-望隼(4771).pdf",
  "凱基美股分析20251205-Meta大砍元宇宙預算，標普、那指續漲.pdf",
  "凱基日股分析20251205-軍工股及機器人股上漲推升日股收漲.pdf",
  "JP-2330 20250718.pdf",
  "MS-8210 20251007.pdf",
  "Daiwa-6278 20260521.pdf",
  "Daiwa-3653 20251002.pdf",
  "凱基港股分析20251205-機器人概念受資金追捧，港股收漲.pdf",
  "20251205兆豐晨會報告(二)-公司訪談摘要.pdf",
  "Daiwa-1319 20231011.pdf",
  "MS-Thermal Solutions 20251007.pdf",
  "MS-2308 20251128.pdf",
  "GS-1590 20231012.pdf",
  "【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf",
  "凱基投顧_3665 貿聯-KY_李承泰_20260519.pdf",
  "華南投顧-6143-振曜-1141128.pdf",
  "第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf",
  "MS-1590 20251202.pdf",
  "GS-1590 20251203.pdf",
  "MS-Thermal Solutions 20251208.pdf",
  "GF-Thoughts on TPU Competition with GPU 20251126.pdf",
  "MS-Automation 20251126.pdf",
  "凱基投顧_1476 儒鴻_劉昃恩_20260519.pdf",
  "統一投顧-20251209投資早報.pdf",
  "20251205兆豐晨會報告(一)-當日新聞與重要訊息評論.pdf",
  "Daiwa-PCB 20251204.pdf",
  "3014TT-20231005.pdf",
  "UBS-Asia Hardware Insights 20251205.pdf",
  "MS-6669 20251007.pdf",
  "GS-2382 20231012.pdf",
  "投資早報251209.pdf",
  "第二場 2026海外投資展望 - 華南永昌海外商品部.pdf",
  "20251208_台新台股盤勢分析.pdf",
  "GS-6415 20260517.pdf",
  "CLST-6669 20251001.pdf",
  "凱基投顧_2891 中信金_施志鴻_20260519.pdf",
  "GS-2317 20251205.pdf",
  "20250819兆豐個股報告-泓德能源(6873).pdf",
  "華南投顧-3017-奇鋐-1141202.pdf",
  "第三場 AI潮流下展望2026半導體產業趨勢 - 陳子昂.pdf",
  "華南投顧-2637-慧洋-KY-1141202.pdf",
  "GS-AI PCB CCL 20251204.pdf",
  "MQ-1560 20260520.pdf",
  "華南投顧-4153-鈺緯-Memo-20251208.docx",
  "華南投顧-3038-全台-Memo-20251209.docx",
  "華南投顧-3675-德微-Memo-20260518.docx",
  "華南投顧-2762-世界健身-KY-Memo-20251209.docx"
)
function Norm([string]$s) { ($s -replace "[\s()\uFF08\uFF09-]", "").ToLower() }
Write-Host "[搜集] 名冊 $($GAPS.Count) 件 · 根 $SearchRoot(遞迴;含子夾)" -ForegroundColor Cyan
$all = Get-ChildItem $SearchRoot -Recurse -File -Include *.pdf,*.docx -ErrorAction SilentlyContinue
$idx = @{}
foreach ($f in $all) { $idx[(Norm $f.Name)] = $f.FullName }
$found = 0; $already = 0; $missing = @()
foreach ($g in $GAPS) {
    $tgt = Join-Path $dest $g
    if (Test-Path $tgt) { $already++; continue }
    $hit = $idx[(Norm $g)]
    if ($hit) {
        Copy-Item $hit $tgt -Force
        Write-Host "  [FOUND] $g" -ForegroundColor Green
        $found++
    } else { $missing += $g }
}
Write-Host ""
Write-Host "[計] FOUND $found · ALREADY $already · MISSING $($missing.Count)(誠實)" -ForegroundColor Yellow
if ($missing.Count) {
    Write-Host "--- 誠實列缺(Downloads 無此件;候他處)---" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  [缺] $_" }
}
Write-Host "[次步] 搜到件後跑 digest 擷取:python (Get-ChildItem '.\functional modules\VRN\vrn_report_digest_v*.py' | Sort-Object Name | Select-Object -Last 1).FullName" -ForegroundColor Cyan

# 批694 · 動態進度條的真百分比 + 不卡斷 + 25 加速器在燈上 · 2026-09-21

> 操作員三令(批683 · 批692B · 本輪「卡斷 25個加速器 動態進度條及百分比」):**L70 逐次許可就是這三道令本身**——改的三支都只為這件事,
> 且各自可回退(模組就地改=git 一行還原;啟動器/跑器都是新版號檔,刪檔即回退)。
> 先認一件事:上一則我叫你 `via-vrnrun 2>&1 | Tee-Object … | Out-Null`,`Out-Null` 把畫面全吞了——那個「卡斷」有一半是我的指令造成的,
> 這一批把它做成不需要濾管也看得見進度的樣子。

## 一 · 改了什麼(三支,一條協定)

| 件 | 改法 | 驗 |
|----|------|----|
| `supportive modules/VIA_PS_PyProgress_Module.ps1`(無版號冊,就地改)| `Invoke-VIAPython` 轉播 stdout 時認三種行:引擎的 `[進度] n/N …`、格子的 `n/N xx% ·`、啟動器的 `[Vk] i/n` → **真百分比**(狀態列印「n/N xx% · 經過 · 剩約」);引擎沒報進度才退回 30 秒脈動,而且狀態列寫明「脈動(引擎未報進度)」不假裝;**心跳**:30 秒無輸出印「無輸出 Ns(仍在跑;逾時 Ts 才停)」;結束把最後進度放 `$global:VIA_PYPROG_LAST`。stdout 一行不少、rc 照真、逾時 Kill 整樹全保留 | `VIA_PS_PyProgress_Selftest_v0101.ps1`(via-pyprog):七檢(8 項)**8/8**——+⑦ `[進度] 1..4/4` → pct 100;⑦b 沒報進度 pct=-1;容器 pwsh 7.4 實跑 |
| `Invoke-VIA-VRN-v0102.ps1`(via-vrnrun 的啟動器,新版號)| 起跑印 `[加速器] N/25 冊在位`(讀 $global:VIA_ACCEL25,缺席講缺席);五步走 Write-Progress Id 11 真百分比(0/20/40/60/80%),每步印 `[進度] k/5 [Vk] …` 與耗時秒;收尾一行五步總表(rc · 秒)。其餘一字不動 | pwsh ParseFile OK;via-vrnrun 用 Get-VIANewest 自動取 v0102 |
| `CGC_MDL172_VRNChainRunner_v0103.py`(V2 六層鏈跑器,新版號)| run 模式每個節點跑完印 `[進度] k/44 <層> <節點> <態> <秒>`(層內並行,計數上鎖)——最長的那一步不再是黑箱;plan/--only 不印;rc/存證/頁不動 | 廿四檢 24/24;容器 `run --fast` 實印 1/44…;PS 語法閘棘輪不變 |

協定只有一句:**誰有可數的迴圈,誰就印 `[進度] n/N`**——VDF/VAP/中央引擎本線逐支接,VRN 家族交 VRN 線;啟動器一處解析(L05)。

## 二 · 沒動的

`VIA_PS_Accel_Module.ps1`(25 冊本體)一字未動——「25 個加速器」本來就在,現在是燈上看得見(`[加速器] 25/25 冊在位`)。Z76 794 支註解仍候「統一」。

## 三 · 全格子 v0446(容器;PATH 帶 /opt/pwsh)

OK 278 · FAIL 0 · SKIP 8 · TIMEOUT 0(236s;GRID_20260921_183342;rc=0)。PS 語法閘棘輪 5 支/53 筆不變;MDL172 v0103 站(newest)綠。

## 四 · 實錄讀出(工作站 `via-vrnrun` 2026-09-21;跑在拉 批694 **之前**的樹)

橫幅「VRN 六層鏈 · 批671 · v0102」、沒有 `[加速器]` 與 `[進度] k/5` 行——所以這一輪還看不到批694 的進度條;V1/V3/V4/V5 rc=0,**V2 rc=1**:GREEN 30 · RED 2 · NODATA 14。

| 讀出 | 容器對照(main 576aba61,PR #73 已併) | 判 |
|------|------------------------------------------|----|
| `SUP_MDL746_PDFPlumberPlusHub RED 語法樹讀不出來(line 15)` | v0101 在 python3.11 / 3.12 / 3.13 `ast.parse` 全 OK;用 MDL172 `selftest_door` 同一讀法(utf-8 · errors=replace)也 OK;無 BOM 無 CRLF;line 15 在模組 docstring 裡 | **紅的不是 git 上的內容**。MDL172 `resolve_tail` 敲的是樹上同 stem 最新 `_vNNNN.py`,讀出又沒有「【冊落後】」註 → 剩三種可能:① 工作站該路徑的檔跟 git 不同(OneDrive 半寫/佔位/衝突標記;前一輪有 unmerged files 史)② 工作站有未追蹤的更高版號同名檔(L25 側枝那類)③ 工作站直譯器 via_vrn_312 真的不吃某一行。**三種要工作站自己量**(文末 PS 診斷塊),貼回定案;VRN 家族歸 VRN 線(已轉交 2026-09-21 18:52Z)。掉球 **Z118** |
| `CGC_MDL141_ClosingGate RED 語法樹讀不出來(line 13)` | v0111 同上三直譯器全 OK;line 13 在 docstring 裡 | 同上 |
| `VRN_ENG072_FirstPageText NODATA 逾時 180.4s` | — | 沒跑完=沒有結論,不是紅(批616 律);ENG072 逾時歸 VRN 線 |
| V4 格子 735 · GREEN 461 · YELLOW 11 · NODATA 215 · NA 48;判對率 100%(461/461)· 可判率 62.7% / 扣不適用 67.1% | — | 兩個都印,可判率離 100% 是缺料(215 NODATA)不是判錯 |
| `[第二顆頭] 另有 1 本庫也有 vrn_report_basic` | — | Z88 仍候操作員封存舊庫 |

診斷塊(工作站貼回三樣:python 版本、兩支同 stem 版號檔與 git 是否同 blob、工作站 python 直接 `ast.parse` 的錯誤訊息與那一行):

```powershell
& { $py = (Get-ChildItem "$env:VIA_ENV_ROOT\via_vrn_*\Scripts\python.exe" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName; if (-not $py) { $py = 'python' }
  & $py -c "import sys; print('[py]', sys.version.split()[0], sys.executable)"
  foreach ($stem in @('supportive modules\70_VRN_Rules\SUP_MDL746_PDFPlumberPlusHub', 'supportive modules\registry\CGC_MDL141_ClosingGate')) {
    $sibs = Get-ChildItem "${stem}_v[0-9][0-9][0-9][0-9].py" | Sort-Object Name
    $f = $sibs[-1].FullName; $rel = ($f.Substring((Get-Location).Path.Length + 1)) -replace '\\', '/'
    "[樹尾版] " + ($sibs | ForEach-Object { $_.Name + '(' + $_.Length + 'B)' }) -join ' · '
    "[git]    工作樹 blob " + (git hash-object $f) + " · HEAD blob " + (git rev-parse "HEAD:VeritasIntelligenceAnalytics/$rel" 2>$null) + " · status " + ((git status --short -- $f) -join ' ')
    & $py -c "import ast,sys,pathlib; p=pathlib.Path(sys.argv[1]); t=p.read_text(encoding='utf-8',errors='replace')
try:
    ast.parse(t); print('[ast]    OK', p.name)
except SyntaxError as e:
    ls=t.splitlines(); print('[ast]    FAIL', p.name, 'line', e.lineno, e.msg); print('[那一行]', repr(ls[e.lineno-1][:160]) if e.lineno and e.lineno<=len(ls) else '(超出檔尾)')" $f
  } }
```

> **批695 補**:三種可能不必工作站量了——根因已在容器重現(側線 86a72a0e 同名檔加/加衝突,標記留在工作站樹裡),見 `VIA_B695_TheLampMustSayWhoIsRed.md`;MDL172 v0104 起燈自己會講。

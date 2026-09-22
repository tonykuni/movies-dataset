# 批695 · 紅燈要自己講是誰紅——工作站兩盞「語法樹讀不出來」的根因 · 2026-09-21

> 操作員令(沿用):「"C:\測試樣本報告" 實測實修正直到成功」。工作站兩次貼回 `via-vrnrun`,V2 同兩盞紅:
> `SUP_MDL746_PDFPlumberPlusHub RED 語法樹讀不出來(line 15)` · `CGC_MDL141_ClosingGate RED 語法樹讀不出來(line 13)`。
> 批694 文四我開了一段 PS 診斷塊請操作員貼——操作員貼回來的還是 `via-vrnrun`。**燈自己該講的,不該叫人另外量**(L16 紅燈指路)。這一批兩件事:把根因在容器重現,把燈改成會講。

## 一 · 根因(容器重現,行號一模一樣)

| 步 | 量到什麼 |
|----|---------|
| main 576aba61 上的兩支 | `SUP_MDL746_PDFPlumberPlusHub_v0101.py`(blob acab3b45)· `CGC_MDL141_ClosingGate_v0111.py`(blob 16edbb45):python3.11 / 3.12 / 3.13 `ast.parse` 全 OK;line 15 / line 13 都在模組 docstring 裡。**git 上的內容不會在那裡炸** |
| 誰還加過同名檔 | `git log --all --diff-filter=A`:側線分支 `claude/via-envmanager-governance-7cls8h` 未併的 **86a72a0e**「批692:兩盞紅燈,兩支尺——工作站照出來的,容器看不到」也加了**同名的兩支**(blob 76231cc5 / 81986f86,內容不同)——它也在修 Z84,跟 VRN 線 08684854 撞號(LL334),沒併進 main |
| 工作站的樹怎麼來的 | 先有 main(08684854 版),後來拉了那條側線 → 兩支同名新檔**加/加衝突**(操作員前一輪貼過 `git pull` error「unmerged files」)。衝突標記留在檔裡、被 commit 進本地樹——之後 `git pull` 都正常,燈卻一直紅 |
| 容器重做這個衝突 | `git merge-file`(ours=08684854 · theirs=86a72a0e)再 `ast.parse`:SUP_MDL746 **line 15** `invalid character '·' (U+00B7)`、CGC_MDL141 **line 13** `invalid character '→' (U+2192)`——**與工作站讀出的行號完全相同**(反向 ours/theirs 則是 13/18,不合;所以工作站是「先 main 後側線」) |
| 側線還動了什麼 | 三本 SSOT JSON(Component_Inventory / SSOT_RegexDict / VRN_LogicArchitecture)與總控頁——都是再生物,工作站跑工具時自癒;**只有版號引擎檔不會自癒**,所以剩這兩盞 |

## 二 · 改了什麼

| 件 | 改法 | 驗 |
|----|------|----|
| `CGC_MDL172_VRNChainRunner_v0104.py`(新版號) | `selftest_door` 抓到 SyntaxError 時燈自述:detail(表格 ≤150 字)講 line · 檔名 · 大小 · **衝突標記 有/NUL/blob 對 HEAD 與上游** · 讀它的 python · 錯訊;stdout 另印一行 `[語法樹] …` 全文(該行 repr、HEAD/上游 blob、修法),`Select-String 語法樹` 就抓得到;fix 欄=修法本身。上游=`@{u}` → `origin/<本地分支>` → `origin/main`(工作站是 `git pull origin <分支>` 拉的,@{u} 常沒設)。blob 算法=git 的(`blob <len>\0`+內容 sha1),CRLF 先正規化再算(Windows autocrlf 也對得上)。判決順序:衝突標記 > NUL > =上游(問直譯器)> =HEAD≠上游(本地 commit 不同)> ≠HEAD(工作樹被改)> 不在 HEAD(未追蹤版號) | 廿五檢 **27/27**(+㉕ 沙盒壞檔講齊六樣、+沙盒衝突標記檔說「衝突標記 有」並指「取上游版」、+blob 算法對得上 git);三直譯器 ast OK;**容器用 worktree 重建工作站的樹(標記檔已 commit)實跑 run_node**:兩支都 RED,detail `語法樹讀不出來(line 15)· … · 衝突標記 有`,修法 `git checkout origin/main -- "<檔>"` |
| `CGC_MDL064_SelftestGrid_v0447.py`(新版號) | 一站改名「VRN 六層鏈廿四檢」→「廿五檢」;期望 rc0 不變,站數不變 | 全格子見文六 |

## 三 · 沒動的

`SUP_MDL746_PDFPlumberPlusHub_v0101.py` 與 `CGC_MDL141_ClosingGate_v0111.py` **一字未動**——內容沒錯,錯的是工作站樹裡夾著標記的那份;VRN 線已告知不必改(改了反而讓工作站再撞一次)。側線那筆 86a72a0e 沒併也沒刪(不是母線的分支;登 Z119 候操作員裁)。

## 四 · 工作站的手(一貼即用)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git pull origin claude/awesome-bardeen-h0wm5v
git log --oneline -1
git grep -l '^<<<<<<< ' -- .
git checkout origin/claude/awesome-bardeen-h0wm5v -- "supportive modules/70_VRN_Rules/SUP_MDL746_PDFPlumberPlusHub_v0101.py" "supportive modules/registry/CGC_MDL141_ClosingGate_v0111.py"
git commit -m "工作站:兩支帶衝突標記的檔取上游版(SUP_MDL746 v0101 · CGC_MDL141 v0111)" -- "supportive modules/70_VRN_Rules/SUP_MDL746_PDFPlumberPlusHub_v0101.py" "supportive modules/registry/CGC_MDL141_ClosingGate_v0111.py"
git grep -l '^<<<<<<< ' -- .
via-vrnrun 2>&1 | Tee-Object -FilePath "$env:TEMP\vrnrun_b695.txt"
Select-String -Path "$env:TEMP\vrnrun_b695.txt" -Pattern '\[加速器\]|\[進度\] \d+/5|\[V[1-5]\]|語法樹|RED|\[FAIL\]|\[計\]|判對率|可判率|rc=' | ForEach-Object { $_.Line }
```

第一次 `git grep` 列出**所有**夾著標記的檔(預期就那兩支;多的貼回來,母線逐檔給取法);第二次應該是空的。之後 V2 那兩格應轉綠或露出下一層真相(燈現在會講)。

## 五 · 給側線與撞號律(LL334)的一筆

同一個 Z84 被兩條線各修一次、各用同一個新版號:VRN 線 08684854 先併進 main,側線 86a72a0e 留在分支上沒併——**分支上沒併的同名檔,不是不存在,它會在任何一台拉過那條分支的機器上變成加/加衝突**。登 Z119:操作員裁那條側線分支是關掉,還是由該線照 LL334 往上疊號重貼。

## 六 · 全格子 v0447(容器;PATH 帶 /opt/pwsh)

OK 278 · FAIL 0 · SKIP 8 · TIMEOUT 0(244s;GRID_20260921_200105;rc=0)。registry-sync 活 6176 · 新 5 · 變更 46;六層冊未變;總控契約 OK;VCGC v0123 廿九檢 29/29。

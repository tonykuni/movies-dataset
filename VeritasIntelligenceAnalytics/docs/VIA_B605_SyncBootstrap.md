# 批605 — 解卡的工具不能放在被卡住的那一側

```
PS> pwsh -NoProfile -ExecutionPolicy Bypass -File ".\VeritasIntelligenceAnalytics\launchers\Invoke-VIA-AllInOne-v0104.ps1"
引數 '...Invoke-VIA-AllInOne-v0104.ps1' 無法辨識為指令碼檔案名稱。
```

這是**我的設計錯誤**,不是操作員操作錯。`v0104` 是批604 推上去的,
而他的 `HEAD` 還停在 `946132b0`(批600)、`[behind 3]` ——
**那支檔正好在他拿不到的那幾個 commit 裡**。

> 用來解除「同步卡住」的工具,不能只存在於倉裡。 → 新律 **L85**

---

## 一、先貼這段(零檔案相依,貼上就跑)

```powershell
cd "C:\Users\tonyk\OneDrive\Documents\movies-dataset"
$R = (Get-Location).Path
$B = (git rev-parse --abbrev-ref HEAD).Trim()
git fetch origin $B
$ts = Get-Date -Format yyyyMMdd_HHmmss
$bk = Join-Path $R "VeritasIntelligenceAnalytics\VIA_Reports\presync_$ts"
$dirty = @(git status --porcelain --untracked-files=no | Where-Object { $_ -and $_.Length -gt 3 })
foreach ($d in $dirty) {
  $rel = $d.Substring(3).Trim('"'); if ($rel -match ' -> ') { $rel = ($rel -split ' -> ')[-1] }
  $src = Join-Path $R $rel
  if (Test-Path -LiteralPath $src -PathType Leaf) {
    $dst = Join-Path $bk $rel
    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
  }
}
Write-Host "備份 $($dirty.Count) 個追蹤檔 -> $bk" -ForegroundColor Yellow
if ($dirty.Count) { git stash push -m "VIA-presync-$ts" }
git merge --ff-only "origin/$B"
if ($LASTEXITCODE -eq 0) {
  git log --oneline -1
  Get-ChildItem ".\VeritasIntelligenceAnalytics\supportive modules\registry\CGC_MDL135_EnvGovernance_v*.py" |
    Sort-Object Name | Select-Object -ExpandProperty Name | Select-Object -Last 1
  "ALL-IN-ONE 在不在: " + (Test-Path ".\VeritasIntelligenceAnalytics\launchers\Invoke-VIA-AllInOne-v0104.ps1")
} else {
  Write-Host "[停] ff-only 失敗 -> 不自動 merge。先看 git status" -ForegroundColor Red
}
```

它**不會**碰你的未追蹤件(`CGC_MDL148_EngineBus_v0128.py`、`_patches\`、`*.bak_b600_*`):
`git stash` 沒帶 `-u`。而且 stash 之前先把那 41 個追蹤檔**整包複製**到
`VIA_Reports\presync_<ts>` —— 一份在 stash、一份是看得見的檔案,兩條退路。

## 二、跑完之後

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\VeritasIntelligenceAnalytics\launchers\Invoke-VIA-AllInOne-v0104.ps1"
```

以後不必再貼:倉裡多了一支**固定檔名**的
`launchers\Sync-VIA-Bootstrap-v0100.ps1` —— 不帶版本尾碼,一旦落地就永遠是同一個路徑,
不會因為升版而失聯。

## 三、這兩支都是**真跑過**才交的

容器有 `pwsh 7.4.6`,所以造了一個**和工作站同形狀**的 scratch 倉:

```
落後 4 · 一個被改過的追蹤檔(遠端也改過同一支)· 兩個未追蹤件
```

跑的是**倉裡那一支的實際位元組**,逐件量:

| # | 量什麼 | 結果 |
|---|---|---|
| ① | 未追蹤件內容有沒有變 | `EngineBus v0128` 一字不差 · `_patches/` 在 |
| ② | stash 能不能還原 | `stash@{0}: VIA-presync-…` |
| ③ | 看得見的備份 | 裡面是**操作員那份**內容 |
| ④ | 分支狀態 | `## br...origin/br`(無落後) |
| ⑤ | 尾版解析 | 印得出 `CGC_MDL135_EnvGovernance_v0113.py` |

順手修掉貼上版的兩個坑:

- `Select-Object -Last 1 Name` 會被綁成 `-Property Name` → **印不出尾版名**(第一版就中了)
- 頂層 `return` 貼進互動式終端機會出事 → 改成 `if/else`

## 四、我連錯三回合,而證據每一則都貼在我眼前(LL162)

他貼的 `git status -sb` 第一行從頭到尾寫著 `[behind 3]`、`git log` 第一行寫著 `946132b0 批600`。

- 第一則:我看懂了「沒 pull」,**卻沒再往前問一步**「為什麼 pull 不進去」(41 個被改過的追蹤檔擋著)
- 第二則:我把答案寫成一支 `.ps1` 推上去 —— **而那支檔在他拿不到的 commit 裡**
- 第三則:才真的把整張圖讀完

「叫他跑 X」之前要先確定**他手上有 X**。這跟 L71(在 Linux 產、在 Windows 貼)同一族:
**我所在的環境不是他所在的環境**,我看得到的檔他不一定看得到。
